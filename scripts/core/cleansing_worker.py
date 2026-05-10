import os
import json
import logging
import re
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Generator

from bs4 import BeautifulSoup
import html
from dotenv import load_dotenv

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.utils import (
    clean_course_name,
    slugify,
    standardize_mode,
    setup_lima_logging,
    normalize_url,
    TimeGuard,
    parse_start_date,
)
from shared.db_client import get_db_client, DatabaseClient

# Setup logging
load_dotenv()
logger = setup_lima_logging("CleansingWorker")

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


def aggressive_html_clean(raw_html: str) -> str:
    if not raw_html: return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    for tag in soup(["head", "header", "footer", "nav", "aside", "script", "style", "noscript", "iframe", "svg"]):
        tag.decompose()
    
    noise_patterns = re.compile(r'header|footer|nav|menu|topbar|sidebar|social|copyright|breadcrumb|banner', re.I)
    for element in soup.find_all(True, {"class": noise_patterns}): element.decompose()
    for element in soup.find_all(True, {"id": noise_patterns}): element.decompose()

    text = soup.get_text(separator="\n", strip=True)
    text = html.unescape(text)
    text = re.sub(r'\n\s*\n+', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()

def detect_locations(text: str) -> List[str]:
    cities = ["Lima", "Arequipa", "Trujillo", "Chiclayo", "Piura", "Iquitos", "Cusco", "Chimbote", "Huancayo", "Tacna", "Ica", "Juliaca", "Ayacucho", "Cajamarca", "Pucallpa", "Sullana", "Huanuco", "Huánuco", "Chincha", "Tarapoto", "Puno", "Tumbes", "Talara", "Huaraz", "Cerro de Pasco", "Abancay", "Moquegua", "Ilo", "Puerto Maldonado"]
    found = []
    campus_matches = re.findall(r'(?:campus|sede|filial|local|ubicaci[óo]n)\s+([A-Z][a-zñáéíóú]+(?:\s+[A-Z][a-zñáéíóú]+)*)', text, re.IGNORECASE)
    if campus_matches:
        for match in campus_matches:
            c = match.strip()
            if c and c not in found: found.append(c)
    for city in cities:
        if re.search(r'\b' + city + r'\b', text, re.IGNORECASE):
            if city not in found: found.append(city)
    return found if found else ["Nacional/No especificado"]

def is_soft_404(text: str) -> bool:
    patterns = [r"p[áa]gina no encontrada", r"error 404", r"no existe la p[áa]gina", r"lo sentimos.*?p[áa]gina.*?no existe", r"404 - ", r"page not found"]
    return any(re.search(p, text.lower()) for p in patterns)

def detect_obsolete_dates(text: str, url: str = "", name: str = "") -> Optional[str]:
    today = datetime.now()
    current_year = today.year
    
    # 1. Buscar cualquier año de 4 dígitos (2000-2029) en URL o Nombre
    # Si el año es menor al actual, es obsoleto de inmediato (Hard Exclusion)
    year_match = re.findall(r'\b(20[0-2][0-9])\b', f"{url} {name}")
    if year_match:
        for y in year_match:
            if int(y) < current_year:
                return f"hard_obsolete_year:{y}"
    
    # 2. Buscar menciones de años pasados en el cuerpo del texto con contexto de fechas
    for year in [str(y) for y in range(2000, current_year)]:
        if re.search(r'(?:inicio|clases|admisi[óo]n|fecha|ciclo|semestre|vencimiento).*?\b' + year + r'\b', text, re.IGNORECASE | re.DOTALL):
            return f"obsolete_year_context:{year}"
            
    return None

def extract_price(text: str) -> Tuple[Optional[float], str]:
    price_match = re.search(r'S/\.?\s*([\d,.]+)', text, re.IGNORECASE)
    if price_match:
        try:
            p = float(price_match.group(1).replace(",", ""))
            if 10 < p < 1000000: return p, "publicado"
        except Exception:
            pass
    return None, "consultar"


def detect_expired_start_date(text: str) -> Optional[str]:
    """Fase 73: Busca menciones de fecha de inicio en el texto y verifica si expiraron (>90d)."""
    patterns = [
        r'(?:inicio|inicia|comienza|fecha de inicio|start date)[:\s]+([A-Za-záéíóúñ]+\s+\d{4})',
        r'(?:inicio|inicia|comienza|fecha de inicio|start date)[:\s]+(\d{1,2}\s+(?:de\s+)?[A-Za-záéíóúñ]+(?:\s+(?:de\s+)?\d{4})?)',
    ]
    for pat in patterns:
        match = re.search(pat, text, re.IGNORECASE)
        if match:
            parsed_date, is_expired = parse_start_date(match.group(1))
            if is_expired:
                return f"expired_start_date:{match.group(1)}"
    return None

class CleansingWorker:
    def __init__(self, db_client: Optional[DatabaseClient] = None) -> None:
        self.db = db_client or get_db_client()
        self.profiles = self._load_profiles()
        self.exclusions = self._load_exclusions()
        # Fase 75: Exclusion Gate — solo procesar instituciones con pipeline_ready=true
        self.ready_inst_ids = {
            str(p['institution_id']) for p in self.profiles
            if isinstance(p, dict) and p.get('pipeline_ready')
        }
        # Fase 79C: Noise patterns cargados desde DB con fallback hardcodeado
        self.default_noise_name_patterns = [
            r'agradecimiento',
            r'thank.?\s*you',
            r'gracias',
            r'matr[ií]culas?\s+abiert',
            r'inscr[ií]bete',
            r'^facultad\s+de\b',
            r'^universidad.+?\|',
        ]
        # NOTA: noise_name_patterns NO se carga globalmente. Se obtiene por institución
        # vía _get_noise_patterns_for_inst() para evitar que patrones de una institución
        # afecten a otras. Ver Fase 79C reapertura.

        # Páginas que son solo contenedores y no cursos reales
        # Fase 72: hub_patterns diferencian landing page vs subpáginas vía /?$ (regex)
        # /idiomas/?$ bloquea /idiomas pero NO /idiomas/english-media
        self.hub_patterns = [
            r'ulima\.edu\.pe/?$',
            r'up\.edu\.pe/?$',
            r'/programas-de-especializacion/?$',
            r'/pregrado/?$',
            r'/posgrado/?$',
            r'/maestrias/?$',
            r'/idiomas/?$',
            r'/educacion-ejecutiva/?$',
            r'/educacion-ejecutiva/cursos-talleres/?$',
            r'/educacion-ejecutiva/certificacion/?$',
        ]

    def is_hub_page(self, url: str) -> bool:
        return any(re.search(p, url.lower()) for p in self.hub_patterns)

    def _load_exclusions(self) -> List[Dict[str, Any]]:
        try:
            if self.profiles:
                raw_patterns = []
                for p in self.profiles:
                    ep = p.get('exclusion_patterns', [])
                    if ep:
                        if isinstance(ep, str):
                            try:
                                parsed = json.loads(ep)
                                if isinstance(parsed, list):
                                    raw_patterns.extend(parsed)
                            except (json.JSONDecodeError, TypeError):
                                pass
                        else:
                            raw_patterns.extend(ep)
                if raw_patterns:
                    compiled = []
                    for exc in set(raw_patterns):
                        if isinstance(exc, str):
                            if exc.startswith('re:'):
                                pat = exc[3:]
                                if len(pat) > 200:
                                    logger.warning(f"Regex pattern too long, skipping: {pat[:50]}...")
                                    continue
                                if re.search(r'(\([^)]*[*+][^)]*\))+[*+]', pat):
                                    logger.warning(f"ReDoS-risk pattern rejected: {pat}")
                                    continue
                                try:
                                    compiled.append(re.compile(pat, re.IGNORECASE))
                                except re.error as e:
                                    logger.warning(f"Invalid regex pattern '{pat}': {e}")
                                    continue
                            else:
                                compiled.append(exc.lower())
                    return compiled
            return []
        except Exception as e:
            logger.warning(f"Error loading exclusions: {e}")
            return []

    def _load_profiles(self) -> List[Dict[str, Any]]:
        try:
            return self.db.select_pipeline('institution_site_profiles') or []
        except Exception as e:
            logger.warning(f"Error loading site profiles: {e}")
            return []

    # Fase 62C: Perfil-driven cleansing helpers
    def _get_profile_for_inst(self, inst_id) -> Dict[str, Any]:
        if not inst_id:
            return {}
        for p in self.profiles or []:
            if isinstance(p, dict) and str(p.get('institution_id', '')) == str(inst_id):
                return p
        return {}

    def _apply_title_cleansing(self, raw_name: str, profile: Dict[str, Any]) -> str:
        if not raw_name:
            return raw_name
        name = raw_name.strip()
        # Remove prefixes
        for prefix in profile.get('title_prefix_removals') or []:
            if name.lower().startswith(prefix.lower()):
                name = name[len(prefix):].strip()
        # Split on separators and take first meaningful part
        for sep in profile.get('title_split_separators') or []:
            if sep in name:
                parts = [p.strip() for p in name.split(sep) if p.strip()]
                if parts:
                    name = parts[0]
        return name

    def _get_noise_patterns_for_inst(self, inst_id) -> List[str]:
        """
        Retorna noise patterns de la institución específica.
        Si la institución no tiene patrones, usa fallback hardcodeado.
        Esto evita que patrones de una institución afecten a otras.
        Genérico: funciona para cualquier institución.
        """
        profile = self._get_profile_for_inst(inst_id) if inst_id else {}
        patterns = profile.get('noise_patterns', []) if isinstance(profile, dict) else []
        if isinstance(patterns, list) and len(patterns) > 0:
            validated = []
            for pat in patterns:
                if not isinstance(pat, str):
                    continue
                if len(pat) > 200:
                    logger.warning(f"Noise pattern too long, skipping: {pat[:50]}...")
                    continue
                if re.search(r'(\([^)]*[*+][^)]*\))+[*+]', pat):
                    logger.warning(f"ReDoS-risk noise pattern rejected: {pat}")
                    continue
                try:
                    re.compile(pat, re.IGNORECASE)
                except re.error as e:
                    logger.warning(f"Invalid noise regex '{pat}': {e}")
                    continue
                validated.append(pat)
            if validated:
                return sorted(validated)
        return list(self.default_noise_name_patterns)

    def _extract_price_with_regex(self, text: str, profile: Dict[str, Any]):
        profile_regex = profile.get('price_regex')
        if profile_regex:
            match = re.search(profile_regex, text, re.IGNORECASE)
            if match:
                try:
                    price_str = match.group(1) if match.lastindex else match.group(0)
                    price_str = price_str.replace(',', '').replace('S/', '').replace('s/', '').strip()
                    price = float(price_str)
                    if 10 < price < 1000000:
                        return price, "publicado"
                except (ValueError, IndexError):
                    pass
        return extract_price(text)

    def _get_base_url(self, url: str) -> str:
        suffixes = ['presentacion/', 'presentacion', 'beneficios/', 'beneficios', 'plana-docente/', 'plana-docente', 'malla-curricular/', 'malla-curricular', 'admision/', 'admision', 'objetivos/', 'objetivos', 'certificacion/', 'certificacion', 'requisitos/', 'requirements/', 'Paginas/curso-actualizacion.aspx', 'sustentacion-tesis/', 'sustentacion-tesis', 'ranking-eduniversal/', 'ranking-eduniversal', 'contactenos/', 'contactenos']
        clean_url = url.rstrip('/') + '/'
        for s in suffixes:
            pattern = re.escape(s.rstrip('/')) + r'/?$'
            if re.search(pattern, clean_url, re.IGNORECASE): return re.sub(pattern, '', clean_url, flags=re.IGNORECASE).rstrip('/') + '/'
        return clean_url

    def stream_pending_staging(self, batch_size: int = 100, max_iterations: int = 10000) -> Generator[Dict[str, Any], None, None]:
        """Streams pending staging records using lock RPC if available, falls back to simple select."""
        seen_ids: set = set()
        iterations = 0
        rpc_failures = 0
        rpc_fallback = False
        while True:
            iterations += 1
            if iterations > max_iterations:
                logger.warning(f"Max iterations ({max_iterations}) reached. Breaking loop.")
                break
            try:
                # Try atomic lock via RPC first (PG17-safe, UPDATE+RETURNING atomico)
                if not rpc_fallback:
                    locked = self.db.rpc('lock_staging_records', {"inst_id": None, "batch_size": batch_size})
                    if locked and len(locked) > 0:
                        rpc_failures = 0
                        current_ids = {r['id'] for r in locked if isinstance(r, dict)}
                        if current_ids.issubset(seen_ids):
                            logger.warning("Detected repeated IDs from lock_staging_records. Breaking to prevent infinite loop.")
                            break
                        seen_ids.update(current_ids)
                        for record in locked:
                            if isinstance(record, dict):
                                yield record
                        continue
                    if locked is not None:
                        break
                    rpc_failures += 1
                    if rpc_failures >= 3:
                        logger.warning(f"RPC lock_staging_records failed {rpc_failures} consecutive times. Switching to fallback-only mode.")
                        rpc_fallback = True
                # Fallback: simple select (no lock)
                batch = self.db.select_pipeline('staging_raw', filters="status=eq.pending", limit=batch_size)
                if not batch: break
                for record in batch: yield record
            except Exception as e:
                logger.error(f"Error streaming pending staging: {e}")
                break

    def is_invalid_course(self, name: str, description: str, url: str, clean_text: str = "", institution_id: str = "") -> Optional[str]:
        if name is None: name = ""
        if description is None: description = ""
        if url is None: url = ""
        
        low_url, low_name = url.lower(), name.lower()
        for exc in self.exclusions:
            if isinstance(exc, re.Pattern):
                if exc.search(low_url):
                    return f"hard_db_exclusion:regex:{exc.pattern}"
            elif isinstance(exc, str):
                if exc in low_url:
                    return f"hard_db_exclusion:{exc}"

        # Fase 79C: Noise name patterns por institución (no global)
        noise_patterns = self._get_noise_patterns_for_inst(institution_id)
        for pat in noise_patterns:
            try:
                if re.search(pat, low_name, re.IGNORECASE):
                    return f"noise_name_pattern:{pat}"
            except re.error:
                continue
        if is_soft_404(f"{name} {clean_text}"): return "soft_404_detected"
        if not name or len(name) < 3: return "name_too_short"
        if not description or len(description) < 20: return "description_too_short"
        return None

    def process_batch(self, batch: List[Dict[str, Any]]) -> int:
        groups: Dict[str, List[Dict[str, Any]]] = {}
        for raw in batch:
            identity = normalize_url(raw.get('canonical_url') or raw.get('effective_url') or raw['url'])
            base = self._get_base_url(identity)
            if base not in groups: groups[base] = []
            groups[base].append(raw)

        cleansed_batch, staging_updates, processed_count = [], [], 0
        for base_url, members in groups.items():
            combined_html, combined_desc = "", ""
            best_raw_name = None
            
            # Find the best name among siblings
            for m in members:
                m_url = m['url'].lower()
                m_name = m.get('raw_name')
                if m_name and len(m_name) > 5:
                    # Preference for presentation pages or shorter names that don't look like URLs
                    if '/presentacion' in m_url:
                        best_raw_name = m_name
                        break
                    if not best_raw_name or len(m_name) < len(best_raw_name):
                        best_raw_name = m_name

            for m in members:
                combined_html += f"\n--- URL: {m['url']} ---\n" + (m.get('raw_html') or "")
                combined_desc += f" {m.get('raw_description') or ''}"
            
            main_raw = members[0]
            for m in members:
                if normalize_url(m['url']) == normalize_url(base_url):
                    main_raw = m
                    break
            
            # Use the best name found if main_raw has none
            final_raw_name = best_raw_name or main_raw.get('raw_name', '')
            
            inst_id, clean_text_context = main_raw['institution_id'], aggressive_html_clean(combined_html)
            
            # Filtros de Calidad y Hubs
            discard_reason = self.is_invalid_course(final_raw_name, combined_desc, base_url, clean_text_context, institution_id=inst_id)
            if not discard_reason and self.is_hub_page(base_url): discard_reason = "is_hub_page"
            if not discard_reason: discard_reason = detect_obsolete_dates(clean_text_context, base_url, final_raw_name)
            if not discard_reason: discard_reason = detect_expired_start_date(clean_text_context)
            
            if discard_reason:
                for m in members: staging_updates.append({"id": m['id'], "status": "discarded", "metadata": {"discard_reason": discard_reason}})
                continue
                
            clean_name = clean_course_name(final_raw_name)
            # Fase 62C: Perfil-driven title cleansing (prefix removal, separator splitting)
            profile = self._get_profile_for_inst(inst_id)
            clean_name = self._apply_title_cleansing(clean_name, profile)
            combined_full_text = f"{clean_name}\n{combined_desc}\n{clean_text_context}"
            mode, locations = standardize_mode(combined_full_text), detect_locations(combined_full_text)
            # Fase 62C: Perfil-driven price extraction with profile regex
            price, p_status = self._extract_price_with_regex(combined_full_text, profile)
            
            cleansed_batch.append({
                "staging_id": main_raw['id'], "institution_id": inst_id, "url": base_url,
                "effective_url": main_raw.get('effective_url'), "canonical_url": main_raw.get('canonical_url'),
                "clean_name": clean_name, "clean_description": combined_full_text[:15000],
                "modality": mode, "location": ", ".join(locations), "base_price": price, "currency": "PEN", "status": "pending",
                "metadata": {"raw_name": final_raw_name, "price_status": p_status, "cleansed_at": datetime.now().isoformat(), "locations_list": locations, "sibling_urls": [m['url'] for m in members]}
            })
            for m in members: staging_updates.append({"id": m['id'], "status": "processed"})
            processed_count += len(members)

        if cleansed_batch:
            try:
                # Try atomic RPC promotion first
                staging_ids = [u['id'] for u in staging_updates if u['status'] == 'processed']
                rpc_result = self.db.rpc('atomic_cleansing_promote', {
                    "p_staging_ids": staging_ids,
                    "p_cleansed_data": cleansed_batch
                })
                if rpc_result:
                    logger.info(f"Promoted {len(cleansed_batch)} courses via RPC (Consolidated {processed_count} URLs).")
                else:
                    # Fallback: traditional upsert + patch
                    self.db.upsert('cleansed_programs', cleansed_batch, on_conflict="url")
                    logger.info(f"Promoted {len(cleansed_batch)} courses (Consolidated {processed_count} URLs).")
                    for update in staging_updates:
                        try:
                            self.db.patch('staging_raw', filters=f"id=eq.{update['id']}", data={"status": update['status'], "metadata": update.get('metadata', {})})
                        except Exception as e:
                            logger.warning(f"Failed to update staging_raw status for {update['id']}: {e}")
            except Exception as e:
                logger.error(f"Failed bulk upsert: {e}")
        else:
            # No cleansed batch, just update staging_raw statuses
            for update in staging_updates:
                try:
                    self.db.patch('staging_raw', filters=f"id=eq.{update['id']}", data={"status": update['status'], "metadata": update.get('metadata', {})})
                except Exception as e:
                    logger.warning(f"Failed to update staging_raw status for {update['id']}: {e}")
        return processed_count

if __name__ == "__main__":
    worker = CleansingWorker()
    guard = TimeGuard(max_seconds=1800, logger=logger)
    logger.info("--- Starting Station 1.5: High Fidelity Smart Sync ---")
    total_processed, batch_accumulator = 0, []
    for record in worker.stream_pending_staging(batch_size=200):
        if guard.should_exit:
            logger.warning(f"⚠️ [TIME_GUARD] Shutdown durante cleansing. Procesados: {total_processed}")
            break
        # Fase 75: Exclusion Gate — saltar registros de instituciones no listas
        inst_id = record.get('institution_id')
        if inst_id and str(inst_id) not in worker.ready_inst_ids:
            worker.db.patch('staging_raw', filters=f"id=eq.{record['id']}", data={'status': 'skipped', 'processing_error': 'pipeline_ready=false'})
            continue
        batch_accumulator.append(record)
        if len(batch_accumulator) >= 100:
            total_processed += worker.process_batch(batch_accumulator)
            batch_accumulator = []
            guard.tick(every=10)
    if batch_accumulator and not guard.should_exit:
        total_processed += worker.process_batch(batch_accumulator)
    logger.info(f"Session finished. Total staging URLs processed: {total_processed} | Time: {guard.elapsed_hours:.2f}h")
