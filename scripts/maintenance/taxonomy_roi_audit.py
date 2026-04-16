import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

def run_taxonomy_roi_audit():
    print("🚀 Iniciando Auditoría de Coherencia Taxonómica y Financiera...")
    
    # 1. Obtener datos de referencia (Salarios de Mercado)
    res_salaries = requests.get(f"{SUPABASE_URL}/rest/v1/market_salaries?select=*", headers=headers)
    salaries_data = res_salaries.json()
    
    if not isinstance(salaries_data, list):
        print(f"❌ Error al obtener salarios: {json.dumps(salaries_data)}")
        return
        
    market_map = {s['category_id']: s for s in salaries_data}
    
    # 2. Obtener todos los cursos activos
    res_courses = requests.get(f"{SUPABASE_URL}/rest/v1/courses?is_active=eq.true&select=id,name,category,category_id,expected_monthly_salary,roi_months,seniority_level,price_pen", headers=headers)
    courses_data = res_courses.json()
    
    if not isinstance(courses_data, list):
        print(f"❌ Error al obtener cursos: {json.dumps(courses_data)}")
        return
        
    courses = courses_data
    
    issues = []
    
    for c in courses:
        error = []
        # A. Validación de Categoría (ID vs Texto)
        expected_cat_name = market_map.get(c['category_id'], {}).get('category_name')
        if expected_cat_name and c['category'] != expected_cat_name:
            error.append(f"Desconexión de nombre: ID pertenece a '{expected_cat_name}' pero texto dice '{c['category']}'")
            
        # B. Validación de Salario vs Mercado
        market_data = market_map.get(c['category_id'])
        if market_data:
            seniority = c.get('seniority_level', 'Mid')
            expected_salary = market_data.get(f'salary_{seniority.lower()}', market_data['salary_average'])
            
            if float(c['expected_monthly_salary'] or 0) != float(expected_salary):
                error.append(f"Salario inconsistente: Tiene S/ {c['expected_monthly_salary']} pero debería ser S/ {expected_salary} ({seniority})")

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
