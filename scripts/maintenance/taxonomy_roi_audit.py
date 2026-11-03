import os
from dotenv import load_dotenv
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.db_client import get_db_client
from shared.roi_engine import adjust_salary_for_course_type

load_dotenv()


SENIORITY_COLUMNS = {
    "Junior": "salary_junior",
    "Mid": "salary_average",
    "Senior": "salary_senior",
}

REPORT_PATH = "docs/qa-engineer/reporte_coherencia_taxonomica_v1.md"
ISSUE_LABELS = {
    "category_mismatch": "Desconexiones de categoría",
    "salary_inconsistent": "Salarios inconsistentes",
    "roi_atypical": "ROI atípicos",
}


def run_taxonomy_roi_audit(database=None):
    print("🚀 Iniciando Auditoría de Coherencia Taxonómica y Financiera...")

    database = database or get_db_client()
    
    # 1. Obtener datos de referencia (Salarios de Mercado)
    salaries_data = database.select_all('market_salaries', columns='*')
    market_map = {s['category_id']: s for s in salaries_data}

    # 2. Obtener todos los cursos activos
    courses = database.select_all(
        'courses',
        filters='is_active=eq.true',
        columns='category,category_id,expected_monthly_salary,roi_months,seniority_level,course_type',
    )
    
    issue_counts = {key: 0 for key in ISSUE_LABELS}
    conflicted_courses = 0
    
    if not courses:
        print("ℹ️ No hay cursos activos para auditar en este momento.")
        return

    total_courses = len(courses)
    print(f"📊 Auditando {total_courses} cursos...")
    
    for c in courses:
        course_has_issue = False
        # A. Validación de Categoría (ID vs Texto)
        expected_cat_name = market_map.get(c['category_id'], {}).get('category_name')
        if expected_cat_name and c['category'] != expected_cat_name:
            issue_counts["category_mismatch"] += 1
            course_has_issue = True
            
        # B. Validación de Salario vs Mercado
        market_data = market_map.get(c['category_id'])
        if market_data:
            seniority = c.get('seniority_level') or 'Mid'
            column = SENIORITY_COLUMNS.get(seniority, 'salary_average')
            salary_base = market_data.get(column, market_data['salary_average'])
            expected_salary = adjust_salary_for_course_type(salary_base, c.get('course_type'))

            current_salary = round(float(c['expected_monthly_salary'] or 0), 2)
            if expected_salary is not None and current_salary != float(expected_salary):
                issue_counts["salary_inconsistent"] += 1
                course_has_issue = True

        # C. Detección de ROI Incoherente
        if c.get('roi_months') and float(c['roi_months']) > 48: # Más de 4 años para recuperar inversión en un curso es alerta
            issue_counts["roi_atypical"] += 1
            course_has_issue = True

        if course_has_issue:
            conflicted_courses += 1

    # 3. Generar Reporte de Coherencia
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("# Auditoría de Coherencia Taxonómica y Financiera\n\n")
        f.write(f"- **Total Cursos Auditados:** {len(courses)}\n")
        f.write(f"- **Conflictos Detectados:** {conflicted_courses}\n\n")
        f.write("## Hallazgos agregados por regla\n\n")
        for issue_type, label in ISSUE_LABELS.items():
            f.write(f"- **{label}:** {issue_counts[issue_type]}\n")
        f.write("\nEl reporte omite nombres, categorías y valores por curso.\n")

    print(f"✅ Auditoría completada. Reporte generado en: {REPORT_PATH}")
    print(f"⚠️ Se encontraron {conflicted_courses} cursos con inconsistencias.")

if __name__ == "__main__":
    run_taxonomy_roi_audit()
