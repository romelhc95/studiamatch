import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: Missing Supabase credentials in .env")
    exit(1)

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

def analyze_metadata():
    url = f"{SUPABASE_URL}/rest/v1/courses?select=id,name,url,description_long,target_audience,syllabus,institution_id"
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Error fetching data: {response.status_code} {response.text}")
        return

    courses = response.json()
    print(f"Total courses fetched: {len(courses)}")

    missing_description = []
    missing_audience = []
    missing_syllabus = []
    missing_multiple = []

    for course in courses:
        desc = course.get('description_long')
        audience = course.get('target_audience')
        syllabus = course.get('syllabus')

        has_desc = bool(desc and str(desc).strip())
        has_audience = bool(audience and str(audience).strip())
        has_syllabus = bool(syllabus and str(syllabus).strip())

        missing_count = sum([not has_desc, not has_audience, not has_syllabus])

        course_info = {
            "name": course.get('name', 'Unknown'),
            "url": course.get('url', 'Unknown')
        }

        if missing_count >= 2:
            missing_multiple.append(course_info)
        else:
            if not has_desc: missing_description.append(course_info)
            if not has_audience: missing_audience.append(course_info)
            if not has_syllabus: missing_syllabus.append(course_info)

    report_lines = [
        "# Reporte de Calidad de Metadata de Cursos\n",
        f"**Total de cursos analizados:** {len(courses)}\n",
        "## Resumen de Problemas",
        f"- Cursos con múltiples campos críticos vacíos: {len(missing_multiple)}",
        f"- Cursos sin descripción: {len(missing_description)}",
        f"- Cursos sin audiencia objetivo: {len(missing_audience)}",
        f"- Cursos sin temario/objetivos: {len(missing_syllabus)}\n",
        "## Detalle de Cursos con Múltiples Campos Vacíos"
    ]

    for c in missing_multiple:
        report_lines.append(f"- **{c['name']}**")
        report_lines.append(f"  URL: {c['url']}")

    if missing_multiple or missing_description or missing_audience or missing_syllabus:
        report_lines.append("\n## Propuesta de Re-Scraping Dirigido")
        report_lines.append("Se detectaron cursos con metadata incompleta. Se propone el siguiente proceso de re-scraping:")
        report_lines.append("1. **Identificación**: Filtrar los cursos afectados por `institution_id` para determinar qué scraper (PUCP, NewHorizons, etc.) necesita ajustes.")
        report_lines.append("2. **Actualización de Selectores**: Revisar la estructura HTML actual de las páginas de los cursos fallidos, ya que es probable que hayan cambiado los selectores de los campos `description_long`, `target_audience` o `syllabus`.")
        report_lines.append("3. **Ejecución Dirigida**: Crear un script temporal de re-scraping que tome específicamente las URLs listadas en este reporte.")
        report_lines.append("4. **Validación**: Utilizar la instrucción `on_conflict_do_update` basada en `(institution_id, slug)` para actualizar únicamente los campos faltantes, conservando el resto de la información intacta.")

    os.makedirs('docs', exist_ok=True)
    with open('docs/metadata_quality_report.md', 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    
    print("Report written to docs/metadata_quality_report.md")

if __name__ == "__main__":
    analyze_metadata()
