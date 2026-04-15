import os
import requests
import json
import time
import re
import argparse
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Configuración de Proveedores
SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GH_MODELS_TOKEN = os.getenv("GH_MODELS_TOKEN")
CF_API_TOKEN = os.getenv("CF_API_TOKEN") or os.getenv("CLOUDFLARE_API_TOKEN")
CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID") or os.getenv("CLOUDFLARE_ACCOUNT_ID")

if not SUPABASE_URL or not SUPABASE_KEY:
    print(f"Error: No se encontraron las credenciales de Supabase. URL: {bool(SUPABASE_URL)}, KEY: {bool(SUPABASE_KEY)}")
    exit(1)

# Headers para Supabase
headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def get_courses_to_enrich(limit: int = 50):
    """Obtiene cursos con metadata incompleta."""
    url = (
        f"{SUPABASE_URL}/rest/v1/courses"
        f"?is_active=eq.true"
        f"&or=(syllabus.is.null,objectives.is.null,target_audience.is.null)"
        f"&select=id,name,category,course_type,institution_id,description_long"
        f"&limit={limit}"
    )
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        return res.json()
    return []

def call_github_models(prompt: str) -> str | None:
    """Usa GitHub Models (OpenAI compatible)."""
    if not GH_MODELS_TOKEN: return None
    try:
        url = "https://models.inference.ai.azure.com/chat/completions"
        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "model": "gpt-4o", # O "Llama-3.1-70B-Instruct"
            "temperature": 0.5,
            "max_tokens": 1000
        }
        res = requests.post(url, headers={"Authorization": f"Bearer {GH_MODELS_TOKEN}"}, json=payload)
        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"  [GH Models Error]: {e}")
    return None

def call_gemini(prompt: str) -> str | None:
    """Usa Google Gemini."""
    if not GEMINI_API_KEY: return None
    import google.generativeai as genai
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"  [Gemini Error]: {e}")
    return None

def call_cloudflare(prompt: str) -> str | None:
    """Usa Cloudflare Workers AI."""
    if not CF_API_TOKEN or not CF_ACCOUNT_ID: return None
    try:
        # Usamos Llama-3-8b-instruct que es gratuito en el tier de Workers AI
        model = "@cf/meta/llama-3-8b-instruct"
        url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/{model}"
        headers = {"Authorization": f"Bearer {CF_API_TOKEN}", "Content-Type": "application/json"}
        res = requests.post(url, headers=headers, json={
            "messages": [
                {"role": "system", "content": "Eres un analista experto en educación técnica y ROI."},
                {"role": "user", "content": prompt}
            ]
        })
        if res.status_code == 200:
            return res.json()["result"]["response"]
    except Exception as e:
        print(f"  [Cloudflare Error]: {e}")
    return None

def enrich_course(course: dict, provider: str = "auto") -> dict | None:
    """Orquestador de enriquecimiento con auditoría de 14 pilares."""
    name = course.get("name", "")
    category = course.get("category", "Tecnología")
    course_type = course.get("course_type", "Curso")
    description = course.get("description_long", "")[:1200]

    prompt = f"""Analiza este programa educativo para la plataforma StudIAMatch:
Nombre: {name} | Categoría: {category} | Tipo: {course_type}
Descripción: {description}

Tareas:
1. Generar Objetivos, Perfil del Estudiante y Syllabus.
2. Inferir el Nivel de Seniority (Junior, Mid, Senior).
3. Estimar la Duración en semanas/meses.

Responde ÚNICAMENTE con un JSON válido y minificado:
{{
  "objectives": "2 oraciones de impacto.",
  "target_audience": "Perfil técnico requerido.",
  "syllabus": "Temario clave (máx 6 módulos).",
  "seniority": "Junior|Mid|Senior",
  "duration_value": "Número (ej: 4)",
  "duration_unit": "Semanas|Meses"
}}"""

    # Orden de prioridad para el Golden Pipeline gratuito/bajo costo
    providers_queue = []
    if provider == "auto":
        providers_queue = [
            ("github", call_github_models),
            ("cloudflare", call_cloudflare),
            ("gemini", call_gemini)
        ]
    elif provider == "github": providers_queue = [("github", call_github_models)]
    elif provider == "cloudflare": providers_queue = [("cloudflare", call_cloudflare)]
    elif provider == "gemini": providers_queue = [("gemini", call_gemini)]

    for p_name, p_func in providers_queue:
        try:
            response_text = p_func(prompt)
            if response_text:
                text = re.sub(r"```json|```", "", response_text).strip()
                data = json.loads(text)
                return {
                    "objectives": data.get("objectives", ""),
                    "target_audience": data.get("target_audience", ""),
                    "syllabus": data.get("syllabus", ""),
                    "seniority": data.get("seniority", "Junior"),
                    "duration_value": data.get("duration_value", ""),
                    "duration_unit": data.get("duration_unit", "Semanas")
                }
        except:
            continue
    return None

def update_course_metadata(course_id: str, updates: dict) -> bool:
    url = f"{SUPABASE_URL}/rest/v1/courses?id=eq.{course_id}"
    res = requests.patch(url, headers=headers, json=updates)
    return res.status_code in [200, 204]

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--provider", type=str, default="auto", choices=["auto", "github", "gemini", "cloudflare"])
    args = parser.parse_args()

    print(f"[{datetime.now().isoformat()}] 🚀 Iniciando LLM Worker (Provider: {args.provider})...")
    courses = get_courses_to_enrich(limit=args.limit)
    print(f"  → {len(courses)} cursos encontrados.")

    success, error = 0, 0
    for course in courses:
        print(f"  → Procesando: {course['name'][:40]}...")
        enriched = enrich_course(course, args.provider)
        if enriched and update_course_metadata(course["id"], enriched):
            print(f"    ✅ OK")
            success += 1
        else:
            print(f"    ❌ Error/Skip")
            error += 1
        time.sleep(2) # Throttle suave

    print(f"\n[{datetime.now().isoformat()}] ✅ Finalizado. Éxitos: {success} | Errores: {error}")
