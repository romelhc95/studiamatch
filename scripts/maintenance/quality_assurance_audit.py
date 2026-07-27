import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.db_client import get_db_client

db = get_db_client()

# Definición de los 14 Pilares para Auditoría
PILLARS = [
    "name", "mode", "address", "price_pen", "description_long", 
    "duration", "start_date_text", "target_audience", "syllabus", 
    "brochure_url", "objectives", "requirements", "certification", "benefits"
]

PUBLIC_COURSE_FILTERS = (
    "is_active=eq.true&is_verified=eq.true&publication_status=eq.publicado"
)
COURSE_COLUMNS = (
    "id,name,slug,institution_id,mode,address,price_pen,description_long,"
    "duration,start_date_text,target_audience,syllabus,brochure_url,objectives,"
    "requirements,certification,benefits,institutions(slug)"
)


def _load_public_visible_courses(database):
    profiles = database.select_all_service(
        'institution_site_profiles',
        filters='production_enabled=eq.true',
        columns='institution_id',
    )
    production_institution_ids = {
        str(profile.get('institution_id'))
        for profile in profiles
        if profile.get('institution_id')
    }
    courses = database.select_all_service(
        'courses',
        filters=PUBLIC_COURSE_FILTERS,
        columns=COURSE_COLUMNS,
    )
    return [
        course
        for course in courses
        if str(course.get('institution_id')) in production_institution_ids
    ]


def run_audit():
    print("Iniciando Auditoría de Coherencia y Calidad (Fase 26)...")
    courses = _load_public_visible_courses(db)
    total_courses = len(courses)
    flagged_courses = []

    for course in courses:
        issues = []
        # 1. Check de vacíos
        missing_pillars = [p for p in PILLARS if not course.get(p) or str(course.get(p)).strip() == ""]
        
        # 2. Check de Coherencia (Data demasiado larga)
        desc = course.get("description_long") or course.get("description") or ""
        if len(desc) > 1500:
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
        health_score = ((total_courses - len(flagged_courses)) / total_courses) * 100 if total_courses > 0 else 0
        f.write(f"- **Salud del Catálogo:** {health_score:.2f}%\n\n")
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
