import os
from dotenv import load_dotenv
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.db_client import get_db_client
from shared.roi_engine import adjust_salary_for_course_type

load_dotenv()

db = get_db_client()


SENIORITY_COLUMNS = {
    "Junior": "salary_junior",
    "Mid": "salary_average",
    "Senior": "salary_senior",
}

def run_taxonomy_roi_audit():
    print("🚀 Iniciando Auditoría de Coherencia Taxonómica y Financiera...")
    
    # 1. Obtener datos de referencia (Salarios de Mercado)
    salaries_data = db.select_all('market_salaries', columns='*')
    market_map = {s['category_id']: s for s in salaries_data}

    # 2. Obtener todos los cursos activos
    courses = db.select_all(
        'courses',
        filters='is_active=eq.true',
        columns='id,name,category,category_id,expected_monthly_salary,roi_months,seniority_level,price_pen,course_type',
    )
    
    issues = []
    
    if not courses:
        print("ℹ️ No hay cursos activos para auditar en este momento.")
        return

    total_courses = len(courses)
    print(f"📊 Auditando {total_courses} cursos...")
    
    for c in courses:
        error = []
        # A. Validación de Categoría (ID vs Texto)
        expected_cat_name = market_map.get(c['category_id'], {}).get('category_name')
        if expected_cat_name and c['category'] != expected_cat_name:
            error.append(f"Desconexión de nombre: ID pertenece a '{expected_cat_name}' pero texto dice '{c['category']}'")
            
        # B. Validación de Salario vs Mercado
        market_data = market_map.get(c['category_id'])
        if market_data:
            seniority = c.get('seniority_level') or 'Mid'
            column = SENIORITY_COLUMNS.get(seniority, 'salary_average')
            salary_base = market_data.get(column, market_data['salary_average'])
            expected_salary = adjust_salary_for_course_type(salary_base, c.get('course_type'))

            current_salary = round(float(c['expected_monthly_salary'] or 0), 2)
            if expected_salary is not None and current_salary != float(expected_salary):
                error.append(f"Salario inconsistente: Tiene S/ {c['expected_monthly_salary']} pero debería ser S/ {expected_salary} ({seniority} ajustado por tipo)")

        # C. Detección de ROI Incoherente
        if c.get('roi_months') and float(c['roi_months']) > 48: # Más de 4 años para recuperar inversión en un curso es alerta
            error.append(f"ROI Atípico: {c['roi_months']} meses")

        if error:
            issues.append({
                "name": c['name'],
                "category": c['category'],
                "seniority": c.get('seniority_level'),
                "errors": error
            })

    # 3. Generar Reporte de Coherencia
    report_path = "docs/qa-engineer/reporte_coherencia_taxonomica_v1.md"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Auditoría de Coherencia Taxonómica y Financiera\n\n")
        f.write(f"- **Total Cursos Auditados:** {len(courses)}\n")
        f.write(f"- **Conflictos Detectados:** {len(issues)}\n\n")
        f.write("## Hallazgos por Curso\n\n")
        for issue in issues:
            f.write(f"### {issue['name']}\n")
            f.write(f"- **Categoría Actual:** {issue['category']} ({issue['seniority']})\n")
            for e in issue['errors']:
                f.write(f"- ❌ {e}\n")
            f.write("\n")

    print(f"✅ Auditoría completada. Reporte generado en: {report_path}")
    print(f"⚠️ Se encontraron {len(issues)} inconsistencias.")

if __name__ == "__main__":
    run_taxonomy_roi_audit()
