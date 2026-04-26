import os
import json
import logging
import sys
import requests
import re
from datetime import datetime
from dotenv import load_dotenv

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.utils import (
    infer_course_type,
    standardize_mode,
    standardize_category,
    setup_lima_logging
)
from shared.db_client import get_db_client

# Setup logging
load_dotenv()
logger = setup_lima_logging("EnrichmentWorker")

# API Keys & Credits (Multicloud Policy)
CF_API_TOKEN = os.getenv("CF_API_TOKEN") 
CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GH_MODELS_TOKEN = os.getenv("GH_MODELS_TOKEN")

class EnrichmentWorker:
    def __init__(self):
        self.db = get_db_client()

    def get_pending_cleansed(self, limit=None):
        """Obtiene registros de cleansed_programs o directamente de courses para IA."""
        try:
            res = self.db.select('cleansed_programs', filters="status=eq.pending", limit=limit)
            if res and len(res) > 0:
                return res
        except:
            pass
            
        logger.info("No hay registros en cleansed_programs, intentando con tabla courses...")
        # Filtrar cursos que no tengan tipo o duración (indicador de falta de enriquecimiento)
        res = self.db.select('courses', filters="course_type=eq.", limit=limit)
        normalized = []
        for r in res:
            normalized.append({
                "id": r['id'],
                "clean_name": r['name'],
                "clean_description": r.get('description_long') or r['name'],
                "institution_id": r['institution_id'],
                "url": r['url']
            })
        return normalized

    def _call_cloudflare(self, prompt):
        if not CF_API_TOKEN or not CF_ACCOUNT_ID: return None
        try:
            model = "@cf/meta/llama-3-8b-instruct"
            url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/{model}"
            res = requests.post(url, headers={"Authorization": f"Bearer {CF_API_TOKEN}"}, json={
                "messages": [
                    {"role": "system", "content": "Eres un analista educativo experto. Responde solo JSON."},
                    {"role": "user", "content": prompt}
                ]
            }, timeout=30)
            if res.status_code == 200: return res.json()["result"]["response"]
        except: return None
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
        except: return None
        return None

    def _call_gemini(self, prompt):
        if not GEMINI_API_KEY: return None
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            res = requests.post(url, json=payload, timeout=30)
            if res.status_code == 200: return res.json()['candidates'][0]['content']['parts'][0]['text']
        except: return None
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

    def _call_llm_for_pillars(self, name, description):
        prompt = f"""Extrae 14 pilares de este curso para studiamatch. Responde SOLO JSON puro.
        Nombre: {name}
        Descripción: {description[:1200]}
        Esquema: {{"official_name": "", "duration_text": "", "duration_months": 0, "total_cost_est": 0.0, "requirements": [], "graduate_profile": "", "curriculum_summary": {{}}, "modality": "Presencial|Remoto", "primary_campus": "", "degree_type": "Maestría|Diplomado|Curso", "start_date": "", "categories": [], "difficulty_level": "", "ai_summary": ""}}"""

        for p_name, p_func in [("Cloudflare", self._call_cloudflare), ("GitHub", self._call_github), ("Gemini", self._call_gemini)]:
            try:
                raw = p_func(prompt)
                clean = self._clean_json_response(raw)
                if clean:
                    logger.info(f"✅ Éxito con {p_name}")
                    return json.loads(clean)
            except: continue
        return self._generate_smart_mock(name, description)

    def enrich_record(self, cleansed):
        c_id, name, desc = cleansed['id'], cleansed['clean_name'], cleansed['clean_description']
        logger.info(f"--- Procesando: {name} ---")
        try:
            enriched = self._call_llm_for_pillars(name, desc)
            
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
                res_cat = self.db.select('categories', filters=f"name=ilike.*{cat_name[:5]}*")
                if res_cat: cat_id = res_cat[0]['id']

            save_data = {
                "cleansed_id": c_id,
                "institution_id": cleansed['institution_id'],
                "url": cleansed['url'],
                "official_name": enriched.get("official_name"),
                "duration_text": enriched.get("duration_text"),
                "duration_months": enriched.get("duration_months"),
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
                "status": "pending"
            }

            # 🛡️ Intentar guardar en enriched_programs pero no bloquear el flujo si falla RLS
            try:
                self.db.upsert('enriched_programs', save_data, on_conflict="url") 
            except:
                logger.warning("Fallo guardado en enriched_programs por RLS. Continuando con sincronización directa a courses...")

            self.sync_to_courses(c_id, enriched, cat_id)
            logger.info(f"Sincronización a tabla courses exitosa.")
        except Exception as e:
            logger.error(f"Error en enriquecimiento: {e}")

    def sync_to_courses(self, course_id, data, cat_id=None):
        update_data = {
            "course_type": data.get("degree_type", "Curso"),
            "duration": data.get("duration_text", "Consultar"),
            "mode": data.get("modality", "Presencial"),
            "category_id": cat_id,
            "description_long": data.get("ai_summary", "")
        }
        self.db.patch('courses', filters=f"id=eq.{course_id}", data=update_data)

    def _generate_smart_mock(self, name, description):
        return {"official_name": name, "duration_text": "Consultar", "degree_type": "Curso", "modality": "Presencial"}

if __name__ == "__main__":
    worker = EnrichmentWorker()
    records = worker.get_pending_cleansed(limit=5)
    logger.info(f"🚀 Procesando {len(records)} registros.")
    for r in records:
        if r and isinstance(r, dict): worker.enrich_record(r)
