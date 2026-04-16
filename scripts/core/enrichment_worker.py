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
    standardize_category
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [MULTICLOUD-ENRICHER] - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("EnrichmentWorker")

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("❌ CRITICAL ERROR: SUPABASE_URL or SUPABASE_KEY is not set.")
    sys.exit(1)

# API Keys & Credits (Multicloud Policy)
CF_API_TOKEN = os.getenv("CF_API_TOKEN") 
CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GH_MODELS_TOKEN = os.getenv("GH_MODELS_TOKEN")

class EnrichmentWorker:
    def __init__(self):
        self.api_url = f"{SUPABASE_URL}/rest/v1"
        self.headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

    def get_pending_cleansed(self, limit=10):
        """Obtiene registros de cleansed_programs listos para IA."""
        url = f"{self.api_url}/cleansed_programs?status=eq.pending&limit={limit}"
        res = requests.get(url, headers=self.headers)
        if res.status_code == 200: return res.json()
        return []

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

    def _call_llm_for_pillars(self, name, description):
        """Multicloud Cascade: CF -> GitHub -> Gemini"""
        prompt = f"""Extrae 14 pilares de este curso para studiamatch. Responde SOLO JSON minificado. No incluyas markdown.
        Nombre: {name} | Desc: {description[:1000]}
        Esquema: {{
            "official_name": "string", "duration_text": "string", "duration_months": int,
            "total_cost_est": float, "requirements": [], "graduate_profile": "string",
            "curriculum_summary": {{}}, "modality": "Presencial|Remoto|Híbrido",
            "primary_campus": "string", "degree_type": "string", "start_date": "ISO",
            "categories": [], "difficulty_level": "Básico|Intermedio|Avanzado",
            "ai_summary": "string"
        }}"""

        providers = [
            ("Cloudflare", self._call_cloudflare),
            ("GitHub", self._call_github),
            ("Gemini", self._call_gemini)
        ]

        for p_name, p_func in providers:
            try:
                logger.info(f"Intentando con Provider: {p_name}")
                response = p_func(prompt)
                if response:
                    match = re.search(r'\{.*\}', response, re.DOTALL)
                    if match: 
                        data = json.loads(match.group())
                        logger.info(f"✅ Éxito con {p_name}")
                        return data
            except Exception as e:
                logger.warning(f"⚠️ Provider {p_name} falló: {e}")
                continue
        
        logger.warning("❌ Todos los providers fallaron. Generando Smart Mock preventivo.")
        return self._generate_smart_mock(name, description)

    def enrich_record(self, cleansed):
        c_id = cleansed['id']
        name = cleansed['clean_name']
        desc = cleansed['clean_description']
        inst_id = cleansed['institution_id']
        url = cleansed['url']

        logger.info(f"--- Procesando: {name} ---")
        try:
            enriched_data = self._call_llm_for_pillars(name, desc)
            
            save_data = {
                "cleansed_id": c_id,
                "institution_id": inst_id,
                "url": url,
                **enriched_data,
                "status": "pending"
            }

            res = requests.post(
                f"{self.api_url}/enriched_programs?on_conflict=url",
                headers=self.headers,
                json=save_data
            )

            if res.status_code in [200, 201, 204]:
                logger.info(f"Record guardado en enriched_programs.")
                self.update_cleansed_status(c_id, "enriched")
            else:
                logger.error(f"Error al guardar: {res.text}")
        except Exception as e:
            logger.error(f"Error en enriquecimiento: {e}")

    def update_cleansed_status(self, c_id, status):
        requests.patch(
            f"{self.api_url}/cleansed_programs?id=eq.{c_id}",
            headers=self.headers,
            json={"status": status}
        )

    def _generate_smart_mock(self, name, description):
        inferred_type = infer_course_type(name)
        return {
            "official_name": name,
            "duration_text": "Pendiente",
            "duration_months": 0,
            "total_cost_est": 0.0,
            "requirements": [],
            "graduate_profile": "Perfil por definir",
            "curriculum_summary": {},
            "modality": standardize_mode(description),
            "primary_campus": "Sede Central",
            "degree_type": inferred_type,
            "start_date": None,
            "categories": [standardize_category(name)],
            "difficulty_level": "Intermedio",
            "ai_summary": f"Programa especializado en {name}."
        }

if __name__ == "__main__":
    worker = EnrichmentWorker()
    records = worker.get_pending_cleansed(limit=5)
    for r in records:
        worker.enrich_record(r)
