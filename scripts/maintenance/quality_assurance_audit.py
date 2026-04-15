import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}"
}

# Definición de los 14 Pilares para Auditoría
PILLARS = [
    "name", "mode", "address", "price_pen", "description", 
    "duration", "start_date_text", "target_audience", "syllabus", 
    "brochure_url", "objectives", "requirements", "certification", "benefits"
]

def run_audit():
    print("🚀 Iniciando Auditoría de Coherencia y Calidad (Fase 26)...")
    # Fetch courses with their institution slugs
    url = f"{SUPABASE_URL}/rest/v1/courses?select=*,institutions(slug)&is_active=eq.true"
    res = requests.get(url, headers=headers)
    
    if res.status_code != 200:
        print(f"❌ Error al conectar con Supabase: {res.status_code}")
        return

    courses = res.json()
    total_courses = len(courses)
    flagged_courses = []

    for course in courses:
        issues = []
        # 1. Check de vacíos
        missing_pillars = [p for p in PILLARS if not course.get(p) or str(course.get(p)).strip() == ""]
        
        # 2. Check de Coherencia (Data demasiado larga)
        if course.get("description") and len(course.get("description")) > 1500:
            issues.append("Resumen Ejecutivo excesivamente largo")
            
        # 3. Check de Alucinación/Falta de Data
        if len(missing_pillars) > 6:
            issues.append(f"Faltan {len(missing_pillars)} pilares críticos")

        # 4. Check de Slugs e Institución
        inst_slug = course.get("institutions", {}).get("slug") if course.get("institutions") else "general"
        
        if issues:
            flagged_courses.append({
                "name": course["name"],
                "slug": course["slug"],
                "institution_slug": inst_slug,
                "issues": issues,
                "missing": missing_pillars
            })

    # Generar Reporte
    report_path = "docs/qa_coherence_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# Reporte de Coherencia y Calidad V2 (Rutas Dinámicas)\n\n")
        f.write(f"- **Total Cursos Auditados:** {total_courses}\n")
        f.write(f"- **Cursos con Observaciones:** {len(flagged_courses)}\n")
        f.write(f"- **Salud del Catálogo:** {((total_courses - len(flagged_courses)) / total_courses) * 100:.2f}%\n\n")
        f.write("## Hallazgos de Navegación y Datos\n\n")
        for c in flagged_courses:
            # New URL format: /courses/[institution]/[slug]
            url_link = f"https://studiamatch.com/courses/{c['institution_slug']}/{c['slug']}"
            f.write(f"### [{c['name']}]({url_link})\n")
            f.write(f"- **Alertas:** {', '.join(c['issues'])}\n")
            f.write(f"- **Campos Vacíos:** {', '.join(c['missing'])}\n\n")

    print(f"✅ Auditoría completada. Reporte generado en: {report_path}")

if __name__ == "__main__":
    run_audit()
