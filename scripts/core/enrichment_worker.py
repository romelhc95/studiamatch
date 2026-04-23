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

# DB connection is now handled by DBClient

# API Keys & Credits (Multicloud Policy)
CF_API_TOKEN = os.getenv("CF_API_TOKEN") 
CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GH_MODELS_TOKEN = os.getenv("GH_MODELS_TOKEN")

class EnrichmentWorker:
    def __init__(self):
        self.db = get_db_client()

    def get_pending_cleansed(self, limit=None):
        """Obtiene registros de cleansed_programs listos para IA."""
        return self.db.select('cleansed_programs', filters="status=eq.pending", limit=limit)

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
        """Clean and repair common LLM JSON errors."""
        if not text: return None
        
        # 1. Remove markdown code blocks
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        
        # 2. Extract only the content between the first { and the last }
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if not match: return None
        json_str = match.group()
        
        # 3. Basic syntax repairs
        # Remove trailing commas before a closing brace or bracket
        json_str = re.sub(r',\s*\}', '}', json_str)
        json_str = re.sub(r',\s*\]', ']', json_str)
        
        return json_str

    def _call_llm_for_pillars(self, name, description):
        """Multicloud Cascade: CF -> GitHub -> Gemini"""
        prompt = f"""Extrae 14 pilares de este curso para studiamatch. Responde SOLO JSON puro. No incluyas explicaciones ni markdown.
        Nombre: {name}
        Descripción: {description[:1200]}

        Esquema Requerido:
        {{
            "official_name": "Nombre formal del programa",
            "duration_text": "Ej: 6 meses, 24 horas",
            "duration_months": 0,
            "total_cost_est": 0.0,
            "requirements": ["Requisito 1", "Requisito 2"],
            "graduate_profile": "Perfil del egresado",
            "curriculum_summary": {{"modulo1": "descripcion", "modulo2": "descripcion"}},
            "modality": "Presencial|Remoto|Híbrido",
            "primary_campus": "Sede o Ciudad",
            "degree_type": "Maestría|Diplomado|Curso|Taller",
            "start_date": "YYYY-MM-DD",
            "categories": ["Categoría 1", "Categoría 2"],
            "difficulty_level": "Básico|Intermedio|Avanzado",
            "ai_summary": "Resumen ejecutivo de 3 líneas"
        }}"""

        providers = [
            ("Cloudflare", self._call_cloudflare),
            ("GitHub", self._call_github),
            ("Gemini", self._call_gemini)
        ]

        for p_name, p_func in providers:
            try:
                logger.info(f"Intentando con Provider: {p_name}")
                raw_response = p_func(prompt)
                if not raw_response:
                    continue
                
                clean_json = self._clean_json_response(raw_response)
                if clean_json:
                    try:
                        data = json.loads(clean_json)
                        logger.info(f"✅ Éxito con {p_name}")
                        return data
                    except json.JSONDecodeError as je:
                        logger.warning(f"⚠️ {p_name} devolvió JSON inválido: {je}. Raw: {raw_response[:200]}...")
                else:
                    logger.warning(f"⚠️ {p_name} no devolvió un bloque JSON válido.")
            except Exception as e:
                logger.warning(f"⚠️ Error inesperado con {p_name}: {e}")
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
            
            # 🛡️ Data Type Normalization for DB
            def normalize_field(val):
                if isinstance(val, (list, dict)):
                    return json.dumps(val) if isinstance(val, dict) else ", ".join([str(v) for v in val if v])
                return str(val) if val is not None else ""

            save_data = {
                "cleansed_id": c_id,
                "institution_id": inst_id,
                "url": url,
                "official_name": enriched_data.get("official_name"),
                "duration_text": enriched_data.get("duration_text"),
                "duration_months": enriched_data.get("duration_months"),
                "total_cost_est": enriched_data.get("total_cost_est"),
                "requirements": normalize_field(enriched_data.get("requirements")),
                "graduate_profile": enriched_data.get("graduate_profile"),
                "curriculum_summary": normalize_field(enriched_data.get("curriculum_summary")),
                "modality": enriched_data.get("modality"),
                "primary_campus": enriched_data.get("primary_campus"),
                "degree_type": enriched_data.get("degree_type"),
                "start_date": enriched_data.get("start_date"),
                "categories": normalize_field(enriched_data.get("categories")),
                "difficulty_level": enriched_data.get("difficulty_level"),
                "ai_summary": enriched_data.get("ai_summary"),
                "status": "pending"
            }

            res = self.db.upsert('enriched_programs', save_data, on_conflict="url")

            if res:
                logger.info(f"Record guardado en enriched_programs.")
                self.update_cleansed_status(c_id, "enriched")
            else:
                logger.error(f"Error al guardar en enriched_programs")
        except Exception as e:
            logger.error(f"Error en enriquecimiento: {e}")

    def update_cleansed_status(self, c_id, status):
        self.db.patch('cleansed_programs', filters=f"id=eq.{c_id}", data={"status": status})

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
    records = worker.get_pending_cleansed() # Sin límite para procesar todo el shard
    logger.info(f"🚀 Iniciando procesamiento de {len(records)} registros pendientes.")
    for r in records:
        worker.enrich_record(r)
