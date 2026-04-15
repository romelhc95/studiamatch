import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

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
    print("🚀 Iniciando Auditoría de Coherencia y Calidad (Fase 16)...")
    url = f"{SUPABASE_URL}/rest/v1/courses?is_active=eq.true"
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
        
        # 2. Check de Coherencia (Data acumulada en campos segmentados)
        # Si un campo segmentado tiene más de 1000 caracteres, es sospechoso de ser un dump.
        if course.get("description") and len(course.get("description")) > 1000:
            issues.append("Resumen Ejecutivo demasiado largo (posible dump)")
            
        # 3. Check de Alucinación/Falta de Data
        if len(missing_pillars) > 5:
            issues.append(f"Faltan {len(missing_pillars)} pilares críticos")

        if issues:
            flagged_courses.append({
                "name": course["name"],
                "slug": course["slug"],
                "issues": issues,
                "missing": missing_pillars
            })

    # Generar Reporte
    report_path = "docs/qa_coherence_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# Reporte de Coherencia y Calidad V1\n\n")
        f.write(f"- **Total Cursos Auditados:** {total_courses}\n")
        f.write(f"- **Cursos con Observaciones:** {len(flagged_courses)}\n")
        f.write(f"- **Salud del Catálogo:** {((total_courses - len(flagged_courses)) / total_courses) * 100:.2f}%\n\n")
        f.write("## Cursos que requieren atención inmediata\n\n")
        for c in flagged_courses:
            f.write(f"### [{c['name']}](http://localhost:3000/courses/{c['slug']})\n")
            f.write(f"- **Alertas:** {', '.join(c['issues'])}\n")
            f.write(f"- **Campos Vacíos:** {', '.join(c['missing'])}\n\n")

    print(f"✅ Auditoría completada. Reporte generado en: {report_path}")

if __name__ == "__main__":
    run_audit()
