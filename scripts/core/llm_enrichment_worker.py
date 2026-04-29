import os
import json
import time
import re
import sys
import argparse
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.db_client import get_db_client
from shared.utils import setup_lima_logging

logger = setup_lima_logging("LLMEnrichmentWorker")

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_MODELS_TOKEN")
GH_MODELS_TOKEN = os.getenv("GH_MODELS_TOKEN") or os.getenv("GITHUB_MODELS_TOKEN")
CF_API_TOKEN = os.getenv("CF_API_TOKEN") or os.getenv("CLOUDFLARE_API_TOKEN")
CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID") or os.getenv("CLOUDFLARE_ACCOUNT_ID")

db = get_db_client()

DB_CHECK_KEYS = ["SUPABASE_URL", "SUPABASE_KEY"]
DB_MISSING = [k for k in DB_CHECK_KEYS if not os.getenv(k)]
if DB_MISSING:
    logger.error(f"Credenciales faltantes: {', '.join(DB_MISSING)}")
    exit(1)


def get_enriched_to_fill(limit: int = 50):
    records = db.select(
        'enriched_programs',
        filters="or=(objectives.is.null,target_audience.is.null,syllabus.is.null)",
        columns="id,official_name,ai_summary,institution_id",
        limit=limit
    )
    if not records:
        return []
    return records


def call_github_models(prompt: str):
    if not GH_MODELS_TOKEN:
        return None
    import requests
    try:
        url = "https://models.inference.ai.azure.com/chat/completions"
        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "model": "gpt-4o",
            "temperature": 0.5,
            "max_tokens": 1000
        }
        res = requests.post(url, headers={"Authorization": f"Bearer {GH_MODELS_TOKEN}"}, json=payload, timeout=30)
        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logger.warning(f"GH Models Error: {e}")
    return None


def call_gemini(prompt: str):
    if not GEMINI_API_KEY:
        return None
    import google.generativeai as genai
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.warning(f"Gemini Error: {e}")
    return None


def call_cloudflare(prompt: str):
    if not CF_API_TOKEN or not CF_ACCOUNT_ID:
        return None
    import requests
    try:
        model = "@cf/meta/llama-3-8b-instruct"
        url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/{model}"
        headers = {"Authorization": f"Bearer {CF_API_TOKEN}", "Content-Type": "application/json"}
        res = requests.post(url, headers=headers, json={
            "messages": [
                {"role": "system", "content": "Eres un analista experto en educacion tecnica y ROI."},
                {"role": "user", "content": prompt}
            ]
        }, timeout=30)
        if res.status_code == 200:
            return res.json()["result"]["response"]
    except Exception as e:
        logger.warning(f"Cloudflare Error: {e}")
    return None


def enrich_program(record: dict, provider: str = "auto"):
    record_id = record.get("id")
    name = record.get("official_name", "")
    description = (record.get("ai_summary") or "")[:1200]

    prompt = f"""Analiza este programa educativo para StudIAMatch:
Nombre: {name}
Descripcion: {description}

Tareas:
1. Generar Objetivos, Perfil del Estudiante y Syllabus.
2. Inferir el Nivel de Seniority (Junior, Mid, Senior).
3. Estimar la Duracion en semanas/meses.

Responde UNICAMENTE con un JSON valido y minificado:
{{
  "objectives": "2 oraciones de impacto.",
  "target_audience": "Perfil tecnico requerido.",
  "syllabus": "Temario clave (max 6 modulos).",
  "seniority": "Junior|Mid|Senior",
  "duration_value": "Numero (ej: 4)",
  "duration_unit": "Semanas|Meses"
}}"""

    providers_queue = []
    if provider == "auto":
        providers_queue = [
            ("cloudflare", call_cloudflare),
            ("github", call_github_models),
            ("gemini", call_gemini)
        ]
    elif provider == "github":
        providers_queue = [("github", call_github_models)]
    elif provider == "cloudflare":
        providers_queue = [("cloudflare", call_cloudflare)]
    elif provider == "gemini":
        providers_queue = [("gemini", call_gemini)]

    for p_name, p_func in providers_queue:
        try:
            response_text = p_func(prompt)
            if not response_text:
                continue

            json_match = re.search(r"(\{.*\})", response_text, re.DOTALL)
            if json_match:
                try:
                    raw_json = json_match.group(1)
                    clean_json = re.sub(r',\s*\}', '}', raw_json)
                    data = json.loads(clean_json)

                    def clean_field(val):
                        if isinstance(val, list):
                            return "\n".join([f"- {str(i).strip()}" for i in val])
                        return str(val).strip()

                    duration_val = data.get("duration_value", "")
                    duration_unit = data.get("duration_unit", "Semanas")
                    full_duration = f"{duration_val} {duration_unit}".strip() if duration_val else None

                    time.sleep(1)

                    updates = {
                        "objectives": clean_field(data.get("objectives", "")),
                        "target_audience": clean_field(data.get("target_audience", "")),
                        "syllabus": clean_field(data.get("syllabus", "")),
                        "seniority_level": data.get("seniority", "Junior"),
                        "duration": full_duration
                    }
                    return updates
                except Exception as e:
                    logger.warning(f"Parse Error en {p_name}: {e}")
        except Exception as e:
            logger.warning(f"Provider Error {p_name}: {e}")
            continue
    return None


def update_enriched_metadata(record_id: str, updates: dict):
    try:
        result = db.patch('enriched_programs', filters=f"id=eq.{record_id}", data=updates)
        return result is not None
    except Exception as e:
        logger.error(f"Error actualizando enriched_programs {record_id}: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--provider", type=str, default="auto",
                        choices=["auto", "github", "gemini", "cloudflare"])
    args = parser.parse_args()

    logger.info(f"Iniciando LLM Worker (Provider: {args.provider})")
    records = get_enriched_to_fill(limit=args.limit)
    logger.info(f"  -> {len(records)} registros encontrados en enriched_programs.")

    success, error, skipped = 0, 0, 0
    for record in records:
        desc = record.get("ai_summary", "")
        if not desc or len(desc) < 150:
            logger.info(f"  Saltando: Descripcion muy corta ({len(desc) if desc else 0} chars)")
            skipped += 1
            continue

        name = record.get("official_name", "")[:40]
        logger.info(f"  -> Procesando ({success+error+skipped+1}/{len(records)}): {name}...")
        enriched = enrich_program(record, args.provider)

        if enriched and update_enriched_metadata(record["id"], enriched):
            logger.info(f"    OK")
            success += 1
        else:
            logger.info(f"    Error")
            error += 1

        time.sleep(1.5)

    logger.info(f"Finalizado. Exitos: {success} | Errores: {error} | Saltados: {skipped}")
