import os
import json
import logging
import sys
import re
import html
import time
import requests
from datetime import datetime
from dotenv import load_dotenv

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.utils import (
    infer_course_type,
    standardize_mode,
    standardize_category,
    setup_lima_logging,
    TimeGuard,
    LLMProvider,
    ProviderOrchestrator,
)
from shared.db_client import get_db_client

# Setup logging
load_dotenv()
logger = setup_lima_logging("EnrichmentWorker")

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# API Keys & Credits (Multicloud Policy)
CF_API_TOKEN = os.getenv("CF_API_TOKEN") 
CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GH_MODELS_TOKEN = os.getenv("GH_MODELS_TOKEN")
NVCF_API_KEY = os.getenv("NVCF_API_KEY")

class EnrichmentWorker:
    def __init__(self):
        self.db = get_db_client()
        self.profiles = self._load_profiles()
        # Fase 75: Exclusion Gate
        self.ready_inst_ids = {
            str(p['institution_id']) for p in self.profiles
            if isinstance(p, dict) and p.get('pipeline_ready')
        }
        cf_provider = LLMProvider("Cloudflare", self._call_cloudflare)
        gh_provider = LLMProvider("GitHub", self._call_github)
        nv_provider = LLMProvider("NVIDIA", self._call_nvidia)
        gemini_provider = LLMProvider("Gemini", self._call_gemini)
        self.orchestrator = ProviderOrchestrator(
            providers=[cf_provider, gh_provider, nv_provider, gemini_provider],
            logger=logger,
        )

    def _load_profiles(self):
        try:
            return self.db.select('institution_site_profiles') or []
        except Exception as e:
            logger.warning(f"Error loading site profiles: {e}")
            return []

    def _get_profile(self, institution_id):
        for p in self.profiles:
            if p.get('institution_id') == institution_id:
                return p
        return {}

    def get_pending_cleansed(self, limit=None):
        """Obtiene registros de cleansed_programs para IA."""
        try:
            res = self.db.select('cleansed_programs', filters="status=eq.pending", limit=limit)
            if res and len(res) > 0:
                return res
        except Exception as e:
            logger.warning(f"Error obteniendo cleansed_programs: {e}")

        logger.info("No hay registros pendientes en cleansed_programs.")
        return []

    def _call_cloudflare(self, prompt):
        if not CF_API_TOKEN or not CF_ACCOUNT_ID: return None
        try:
            model = "@cf/meta/llama-3.1-8b-instruct"
            url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/{model}"
            res = requests.post(url, headers={"Authorization": f"Bearer {CF_API_TOKEN}"}, json={
                "messages": [
                    {"role": "system", "content": "Eres un analista educativo experto. Responde solo JSON."},
                    {"role": "user", "content": prompt}
                ]
            }, timeout=30)
            if res.status_code == 200: return res.json()["result"]["response"]
        except Exception as e:
            logger.warning(f"Cloudflare error: {e}")
            return None
        return None

    def _call_github(self, prompt):
        if not GH_MODELS_TOKEN: return None
        try:
            url = "https://models.inference.ai.azure.com/chat/completions"
            payload = {
                "messages": [{"role": "user", "content": prompt}],
                "model": "gpt-4o",
                "temperature": 0.3
            }
            res = requests.post(url, headers={"Authorization": f"Bearer {GH_MODELS_TOKEN}"}, json=payload, timeout=30)
            if res.status_code == 200: return res.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning(f"GitHub Models error: {e}")
            return None
        return None

    def _call_gemini(self, prompt):
        if not GEMINI_API_KEY: return None
        try:
            url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
            headers_gemini = {"x-goog-api-key": GEMINI_API_KEY, "Content-Type": "application/json"}
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            res = requests.post(url, headers=headers_gemini, json=payload, timeout=30)
            if res.status_code == 200: return res.json()['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            logger.warning(f"Gemini error: {e}")
            return None
        return None

    def _call_nvidia(self, prompt):
        if not NVCF_API_KEY: return None
        try:
            url = "https://integrate.api.nvidia.com/v1/chat/completions"
            payload = {
                "model": "meta/llama-3.1-70b-instruct",
                "messages": [
                    {"role": "system", "content": "Eres un analista educativo experto. Responde solo JSON."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 1024
            }
            headers = {
                "Authorization": f"Bearer {NVCF_API_KEY}",
                "Content-Type": "application/json"
            }
            res = requests.post(url, headers=headers, json=payload, timeout=30)
            if res.status_code == 200:
                return res.json()["choices"][0]["message"]["content"]
            else:
                logger.warning(f"NVIDIA error: HTTP {res.status_code} - {res.text[:200]}")
                return None
        except Exception as e:
            logger.warning(f"NVIDIA error: {e}")
            return None
        return None

    def _clean_json_response(self, text):
        if not text: return None
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if not match: return None
        json_str = match.group()
        json_str = re.sub(r',\s*\}', '}', json_str)
        json_str = re.sub(r',\s*\]', ']', json_str)
        return json_str

    def _sanitize_for_prompt(self, text: str, max_len: int = 1200) -> str:
        if not text:
            return ""
        text = html.unescape(text)
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
        return text[:max_len]

    def _call_llm_for_pillars(self, name, description, inst_id=None):
        profile = self._get_profile(inst_id) if inst_id else {}
        section_keywords = profile.get('section_keywords', {})
        section_keywords = profile.get('section_keywords', {})
        field_defaults = profile.get('field_defaults', {})

        hints = ""
        if section_keywords:
            hints = "\nHINTS DE EXTRACCION POR SECCION:\n"
            for section_label, field_name in section_keywords.items():
                hints += f'- Si encuentras "{section_label}" en el HTML, extrae su contenido como {field_name}\n'
        if field_defaults:
            hints += "\nDEFAULTS (usar si no puedes inferir):\n"
            for key, val in field_defaults.items():
                hints += f"- {key}: {val}\n"

        prompt = f"""Extrae 14 pilares de este curso para studiamatch. Responde SOLO JSON puro.
[SYS] Nombre: {self._sanitize_for_prompt(name, 200)}
[SYS] Descripción: {self._sanitize_for_prompt(description, 1200)}
{hints}

REGLAS CRÍTICAS:
- Si NO puedes inferir un campo con confianza, responde null (NO uses el string "None" ni cadenas vacías).
- Para total_cost_est: extrae el valor numérico en soles (S/). Ej: "S/ 1,500" → 1500.0. Si no hay precio, responde null.
- Para modality: debe ser exactamente "Presencial", "Remoto" o "Híbrido".
- Para start_date: si hay fecha de inicio, extraerla. Ej: "Abril 2026" o "15 de mayo". Si no hay info, responder null.
- Para official_name: usar el nombre completo y formal del programa, nunca abreviaciones.
- REGLA ABSOLUTA: Si la página es un agradecimiento/thank-you, página de inicio (homepage), confirmation page, listado de facultades sin programa individual, o sede/campus sin programa → responde null en TODOS los campos. NO inventes datos de un programa que no existe.

Esquema: {{"official_name": "", "duration_text": "", "duration_months": 0, "total_cost_est": null, "requirements": [], "graduate_profile": "", "curriculum_summary": {{"pilares": []}}, "modality": "Presencial|Remoto|Híbrido", "primary_campus": "", "degree_type": "Maestría|Especialización|Diplomado|Curso|Taller|Bootcamp", "start_date": null, "categories": [], "difficulty_level": "", "ai_summary": ""}}"""

        result, provider_name = self.orchestrator.call_with_fallback(prompt, self._clean_json_response)
        if result is not None:
            return result, provider_name
        return self._generate_smart_mock(name, description), None

    def enrich_record(self, cleansed):
        c_id, name, desc = cleansed['id'], cleansed['clean_name'], cleansed['clean_description']
        inst_id = cleansed.get('institution_id')
        logger.info(f"--- Procesando: {name} ---")
        try:
            enriched, provider_name = self._call_llm_for_pillars(name, desc, inst_id)
            is_mock = provider_name is None

            # Validate official_name: fallback to clean_name if LLM returned None, "None", or empty
            official_name = enriched.get("official_name")
            if not official_name or str(official_name).strip().lower() in ('none', 'null', 'nan', '') or len(str(official_name).strip()) < 3:
                logger.warning(f"LLM returned invalid official_name '{official_name}', falling back to clean_name '{name}'")
                enriched["official_name"] = name

            # Validate modality: normalize to allowed values
            modality_raw = enriched.get("modality")
            modality_norm = str(modality_raw).strip() if modality_raw else ""
            modality_map = {"presencial": "Presencial", "remoto": "Remoto", "virtual": "Remoto",
                            "online": "Remoto", "hibrido": "Híbrido", "híbrido": "Híbrido",
                            "semipresencial": "Híbrido", "blend": "Híbrido"}
            if modality_norm.lower() in modality_map:
                enriched["modality"] = modality_map[modality_norm.lower()]
            elif modality_norm and modality_norm not in ("Presencial", "Remoto", "Híbrido"):
                logger.warning(f"Unknown modality '{modality_norm}', defaulting to Presencial")
                enriched["modality"] = "Presencial"
            elif not modality_norm or modality_norm.lower() in ('none', 'null', 'nan', ''):
                enriched["modality"] = "Presencial"

            # Parse total_cost_est: extract number from strings like "S/ 1,500" or "1500 soles"
            cost_raw = enriched.get("total_cost_est")
            if cost_raw is not None and str(cost_raw).strip().lower() not in ('none', 'null', 'nan', ''):
                try:
                    cost_str = str(cost_raw).replace("S/", "").replace("s/", "").replace("PEN", "").replace("pen", "")
                    cost_str = cost_str.replace("soles", "").replace("Soles", "").replace(",", "").strip()
                    enriched["total_cost_est"] = float(cost_str)
                except (ValueError, TypeError):
                    logger.warning(f"Could not parse total_cost_est '{cost_raw}', setting to None")
                    enriched["total_cost_est"] = None
            else:
                enriched["total_cost_est"] = None

            # Validate start_date: reject string "None"/"null"
            start_date_raw = enriched.get("start_date")
            if start_date_raw and str(start_date_raw).strip().lower() in ('none', 'null', 'nan', ''):
                enriched["start_date"] = None
            
            def normalize(val):
                if isinstance(val, (list, dict)):
                    return json.dumps(val) if isinstance(val, dict) else ", ".join([str(v) for v in val if v])
                return str(val) if val is not None else ""

            # 🛠️ Mapeo Inteligente de Categoría para el Frontend
            cat_id = None
            suggested_cats = enriched.get("categories", [])
            if suggested_cats:
                # Buscar el ID de la primera categoría válida
                cat_name = suggested_cats[0] if isinstance(suggested_cats, list) else suggested_cats
                safe_cat = re.sub(r'[^a-zA-ZáéíóúñÁÉÍÓÚÑ\s]', '', cat_name[:5]).strip()
                res_cat = self.db.select('categories', filters=f"name=ilike.*{safe_cat}*") if safe_cat else None
                if res_cat: cat_id = res_cat[0]['id']

            # Sanitize duration_months: LLM may return 3.5 (float) but DB column is INT
            duration_months_raw = enriched.get("duration_months")
            duration_months_val = 0
            if duration_months_raw is not None:
                try:
                    duration_months_val = int(float(duration_months_raw))
                except (ValueError, TypeError):
                    duration_months_val = 0

            save_data = {
                "cleansed_id": c_id,
                "institution_id": cleansed['institution_id'],
                "url": cleansed['url'],
                "official_name": enriched.get("official_name"),
                "duration_text": enriched.get("duration_text"),
                "duration_months": duration_months_val,
                "total_cost_est": enriched.get("total_cost_est"),
                "requirements": normalize(enriched.get("requirements")),
                "graduate_profile": enriched.get("graduate_profile"),
                "curriculum_summary": normalize(enriched.get("curriculum_summary")),
                "modality": enriched.get("modality"),
                "primary_campus": enriched.get("primary_campus"),
                "degree_type": enriched.get("degree_type"),
                "start_date": enriched.get("start_date"),
                "categories": normalize(enriched.get("categories")),
                "difficulty_level": enriched.get("difficulty_level"),
                "ai_summary": enriched.get("ai_summary"),
                "status": "pending",
                "provider_used": provider_name or "mock",
                "is_mock_data": is_mock
            }

            # 🛡️ Guardar en enriched_programs con toda la metadata de 14 pilares
            try:
                # Try atomic RPC promotion first
                rpc_data = [{
                    "cleansed_id": str(c_id),
                    "institution_id": str(cleansed['institution_id']),
                    "url": cleansed['url'],
                    "official_name": save_data.get("official_name"),
                    "duration_text": save_data.get("duration_text"),
                    "duration_months": save_data.get("duration_months"),
                    "total_cost_est": save_data.get("total_cost_est"),
                    "requirements": save_data.get("requirements"),
                    "graduate_profile": save_data.get("graduate_profile"),
                    "curriculum_summary": save_data.get("curriculum_summary"),
                    "modality": save_data.get("modality"),
                    "primary_campus": save_data.get("primary_campus"),
                    "degree_type": save_data.get("degree_type"),
                    "start_date": save_data.get("start_date"),
                    "categories": save_data.get("categories"),
                    "difficulty_level": save_data.get("difficulty_level"),
                    "ai_summary": save_data.get("ai_summary"),
                    "provider_used": save_data.get("provider_used", "mock"),
                    "is_mock_data": save_data.get("is_mock_data", True)
                }]
                rpc_result = self.db.rpc('atomic_enrichment_promote', {
                    "p_enriched_data": rpc_data,
                    "p_cleansed_id": str(c_id)
                })
                if not rpc_result:
                    # Fallback: traditional upsert + patch
                    self.db.upsert('enriched_programs', save_data, on_conflict="url")
                    self.db.patch('cleansed_programs', filters=f"id=eq.{c_id}", data={"status": "enriched"})
            except Exception as e:
                logger.warning(f"No se pudo guardar en enriched_programs ({e}). El registro quedará pendiente para reintento.")
        except Exception as e:
            logger.error(f"Error en enriquecimiento: {e}")

    def _generate_smart_mock(self, name, description):
        return {
            "official_name": name,
            "duration_text": "Consultar",
            "duration_months": 0,
            "total_cost_est": None,
            "requirements": [],
            "graduate_profile": "",
            "curriculum_summary": {},
            "modality": "Presencial",
            "primary_campus": "",
            "degree_type": "Curso",
            "start_date": None,
            "categories": [],
            "difficulty_level": "",
            "ai_summary": ""
        }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run AI Enrichment Worker")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of records to process")
    args = parser.parse_args()

    worker = EnrichmentWorker()
    guard = TimeGuard(max_seconds=20400, logger=logger)

    worker.orchestrator.run_health_checks()

    total_processed = 0
    batch_size = 10

    logger.info(f"🚀 Iniciando Enriquecimiento Masivo (Límite: {args.limit or 'Sin Límite'})")

    while not guard.should_exit:
        fetch_limit = batch_size
        if args.limit:
            remaining = args.limit - total_processed
            if remaining <= 0: break
            fetch_limit = min(batch_size, remaining)

        records = worker.get_pending_cleansed(limit=fetch_limit)

        if not records or len(records) == 0:
            logger.info("✅ No hay más registros pendientes por enriquecer.")
            break

        logger.info(f"📦 Procesando lote de {len(records)} registros...")
        for r in records:
                if guard.should_exit:
                    logger.warning(f"⚠️ [TIME_GUARD] Shutdown durante lote. Registros procesados: {total_processed}")
                    break
                if r and isinstance(r, dict):
                    # Fase 75: Exclusion Gate — saltar institucion no lista
                    inst_id = r.get('institution_id')
                    if inst_id and str(inst_id) not in worker.ready_inst_ids:
                        logger.warning(f"⏭️ SKIP {r.get('clean_name', '?')}: institution {inst_id} pipeline_ready=false")
                        worker.db.patch('cleansed_programs', filters=f"id=eq.{r['id']}", data={'status': 'skipped'})
                        continue
                    worker.enrich_record(r)
                    total_processed += 1
                    guard.tick(every=50)
                    time.sleep(1.5)

        if len(records) < fetch_limit:
            logger.info("✅ Cola de enriquecimiento vaciada exitosamente.")
            break

    logger.info(f"🏁 Sesión finalizada. Total registros enriquecidos: {total_processed} | Tiempo: {guard.elapsed_hours:.2f}h | Providers: {worker.orchestrator.summary()}")
