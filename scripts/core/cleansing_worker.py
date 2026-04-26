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
    setup_lima_logging
)
from shared.db_client import get_db_client, DatabaseClient

# Setup logging
load_dotenv()
logger = setup_lima_logging("CleansingWorker")

def normalize_url(url: str) -> str:
    """Removes query strings, fragments, and trailing slashes for clean mapping."""
    if not url: return ""
    try:
        parsed = urlparse(url)
        path = parsed.path.rstrip('/')
        return f"{parsed.scheme}://{parsed.netloc.lower()}{path}"
    except:
        return url.rstrip('/')

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
        except: pass
    return None, "consultar"

class CleansingWorker:
    def __init__(self, db_client: Optional[DatabaseClient] = None) -> None:
        self.db = db_client or get_db_client()
        self.exclusions = self._load_exclusions()
        # Páginas que son solo contenedores y no cursos reales
        self.hub_patterns = [
            r'ulima\.edu\.pe/?$', 
            r'up\.edu\.pe/?$',
            r'/programas-de-especializacion/?$',
            r'/pregrado/?$',
            r'/posgrado/?$',
            r'/maestrias/?$'
        ]

    def is_hub_page(self, url: str) -> bool:
        return any(re.search(p, url.lower()) for p in self.hub_patterns)

    def _load_exclusions(self) -> List[Dict[str, Any]]:
        try: return self.db.select('crawler_exclusions', filters="is_active=eq.true")
        except: return []

    def _get_base_url(self, url: str) -> str:
        suffixes = ['presentacion/', 'presentacion', 'beneficios/', 'beneficios', 'plana-docente/', 'plana-docente', 'malla-curricular/', 'malla-curricular', 'admision/', 'admision', 'objetivos/', 'objetivos', 'certificacion/', 'certificacion', 'requisitos/', 'requirements/', 'Paginas/curso-actualizacion.aspx', 'sustentacion-tesis/', 'sustentacion-tesis', 'ranking-eduniversal/', 'ranking-eduniversal', 'contactenos/', 'contactenos']
        clean_url = url.rstrip('/') + '/'
        for s in suffixes:
            pattern = re.escape(s.rstrip('/')) + r'/?$'
            if re.search(pattern, clean_url, re.IGNORECASE): return re.sub(pattern, '', clean_url, flags=re.IGNORECASE).rstrip('/') + '/'
        return clean_url

    def stream_pending_staging(self, batch_size: int = 100) -> Generator[Dict[str, Any], None, None]:
        while True:
            try:
                batch = self.db.select('staging_raw', filters="status=eq.pending", limit=batch_size)
                if not batch: break
                for record in batch: yield record
            except: break

    def is_invalid_course(self, name: str, description: str, url: str, inst_id: str, clean_text: str = "") -> Optional[str]:
        if name is None: name = ""
        if description is None: description = ""
        if url is None: url = ""
        
        low_url, low_name = url.lower(), name.lower()
        for exc in self.exclusions:
            if exc.get('institution_id') and exc['institution_id'] != inst_id: continue
            if exc['pattern'].lower() in low_url: return f"hard_db_exclusion:{exc['pattern']}"
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
            discard_reason = self.is_invalid_course(final_raw_name, combined_desc, base_url, inst_id, clean_text_context)
            if not discard_reason and self.is_hub_page(base_url): discard_reason = "is_hub_page"
            if not discard_reason: discard_reason = detect_obsolete_dates(clean_text_context, base_url, final_raw_name)
            
            if discard_reason:
                for m in members: staging_updates.append({"id": m['id'], "status": "discarded", "metadata": {"discard_reason": discard_reason}})
                continue
                
            clean_name = clean_course_name(final_raw_name)
            combined_full_text = f"{clean_name}\n{combined_desc}\n{clean_text_context}"
            mode, locations, (price, p_status) = standardize_mode(combined_full_text), detect_locations(combined_full_text), extract_price(combined_full_text)
            
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
                self.db.upsert('cleansed_programs', cleansed_batch, on_conflict="url")
                logger.info(f"Promoted {len(cleansed_batch)} courses (Consolidated {processed_count} URLs).")
            except Exception as e: logger.error(f"Failed bulk upsert: {e}")
        for update in staging_updates:
            try: self.db.patch('staging_raw', filters=f"id=eq.{update['id']}", data={"status": update['status'], "metadata": update.get('metadata', {})})
            except: pass
        return processed_count

if __name__ == "__main__":
    worker = CleansingWorker()
    logger.info("--- Starting Station 1.5: High Fidelity Smart Sync ---")
    total_processed, batch_accumulator = 0, []
    for record in worker.stream_pending_staging(batch_size=200):
        batch_accumulator.append(record)
        if len(batch_accumulator) >= 100:
            total_processed += worker.process_batch(batch_accumulator)
            batch_accumulator = []
    if batch_accumulator: total_processed += worker.process_batch(batch_accumulator)
    logger.info(f"Session finished. Total staging URLs processed: {total_processed}")
