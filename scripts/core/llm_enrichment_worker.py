import os
import requests
import json
import time
import re
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# Configuración de Supabase
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: No se encontraron las credenciales de Supabase en .env")
    exit(1)

if not GEMINI_API_KEY:
    print("Error: No se encontró GEMINI_API_KEY en .env")
    exit(1)

# Configurar Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def get_courses_to_enrich(limit: int = 50):
    """Obtiene cursos con metadata incompleta (sin syllabus u objetivos)."""
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
    else:
        print(f"Error obteniendo cursos: {res.status_code} - {res.text}")
        return []

def enrich_with_gemini(course: dict) -> dict | None:
    """Llama a Gemini para enriquecer los metadatos del curso."""
    name = course.get("name", "")
    category = course.get("category", "Tecnología")
    course_type = course.get("course_type", "Curso")
    description = course.get("description_long", "")[:500]  # Limitar contexto

    prompt = f"""Eres un experto en educación técnica en Perú. Dado el siguiente curso, genera metadata adicional en español:

Nombre del curso: {name}
Categoría: {category}
Tipo: {course_type}
Descripción disponible: {description}

Responde ÚNICAMENTE con un JSON válido (sin markdown) con estos 3 campos:
{{
  "objectives": "2-3 oraciones describiendo qué aprenderá el estudiante.",
  "target_audience": "Quiénes deberían tomar este curso (perfil del participante).",
  "syllabus": "Temario resumido con 4-6 módulos o temas principales, separados por salto de línea."
}}"""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()

        # Limpiar posibles bloques de markdown
        text = re.sub(r"```json|```", "", text).strip()

        data = json.loads(text)
        return {
            "objectives": data.get("objectives", ""),
            "target_audience": data.get("target_audience", ""),
            "syllabus": data.get("syllabus", ""),
        }
    except Exception as e:
        print(f"  [Gemini Error] para '{name}': {e}")
        return None

def update_course_metadata(course_id: str, updates: dict) -> bool:
    """Actualiza los campos enriquecidos en Supabase via PATCH."""
    url = f"{SUPABASE_URL}/rest/v1/courses?id=eq.{course_id}"
    res = requests.patch(url, headers=headers, json=updates)
    return res.status_code in [200, 204]

if __name__ == "__main__":
    print(f"[{datetime.now().isoformat()}] 🚀 Iniciando LLM Enrichment Worker...")
    courses = get_courses_to_enrich(limit=50)
    print(f"  → {len(courses)} cursos pendientes de enriquecimiento encontrados.")

    success_count = 0
    error_count = 0

    for course in courses:
        name = course.get("name", "N/A")
        print(f"  → Enriqueciendo: {name}...")

        enriched = enrich_with_gemini(course)
        if enriched:
            ok = update_course_metadata(course["id"], enriched)
            if ok:
                print(f"    ✅ OK: {name}")
                success_count += 1
            else:
                print(f"    ❌ Error guardando: {name}")
                error_count += 1
        else:
            print(f"    ⚠️ Skipped (Gemini no respondió): {name}")
            error_count += 1

        # Respetar límite de la API: ~10 RPM en tier gratuito
        time.sleep(6)

    print(f"\n[{datetime.now().isoformat()}] ✅ Completado. Éxitos: {success_count} | Errores: {error_count}")
