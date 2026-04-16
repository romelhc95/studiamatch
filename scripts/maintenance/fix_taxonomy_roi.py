import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

def fix_taxonomy_roi():
    print("🧹 Iniciando proceso de curación de datos para Certificación...")
    
    # 1. Obtener datos de referencia (Salarios de Mercado)
    res_salaries = requests.get(f"{SUPABASE_URL}/rest/v1/market_salaries?select=*", headers=headers)
    market_map = {s['category_id']: s for s in res_salaries.json()}
    
    # 2. Obtener cursos con inconsistencias
    res_courses = requests.get(f"{SUPABASE_URL}/rest/v1/courses?is_active=eq.true&select=id,name,category,category_id,expected_monthly_salary,seniority_level,price_pen", headers=headers)
    courses = res_courses.json()
    
    fixed_count = 0
    
    for c in courses:
        market_data = market_map.get(c['category_id'])
        if not market_data:
            continue
            
        seniority = c.get('seniority_level', 'Mid')
        expected_cat_name = market_data['category_name']
        expected_salary = market_data.get(f'salary_{seniority.lower()}', market_data['salary_average'])
        
        needs_fix = False
        update_payload = {}

        # Validar Nombre de Categoría
        if c['category'] != expected_cat_name:
            update_payload['category'] = expected_cat_name
            needs_fix = True
            
        # Validar Salario
        if float(c['expected_monthly_salary'] or 0) != float(expected_salary):
            update_payload['expected_monthly_salary'] = float(expected_salary)
            needs_fix = True

        # Si hubo cambios, recalcular ROI
        if needs_fix:
            investment = c['price_pen'] or 0
            # Usamos el nuevo salario para el ROI
            new_salary = update_payload.get('expected_monthly_salary', c['expected_monthly_salary'])
            if new_salary and new_salary > 0:
                update_payload['roi_months'] = round(investment / new_salary, 2)
            
            # Aplicar actualización
            patch_res = requests.patch(
                f"{SUPABASE_URL}/rest/v1/courses?id=eq.{c['id']}",
                json=update_payload,
                headers=headers
            )
            
            if patch_res.status_code in [200, 201, 204]:
                fixed_count += 1
                print(f"✅ Corregido: {c['name']} -> {expected_cat_name} (Salario: S/ {expected_salary})")
            else:
                print(f"❌ Error corrigiendo {c['name']}: {patch_res.text}")

    print(f"\n✨ Proceso de curación finalizado. Registros actualizados: {fixed_count}")

if __name__ == "__main__":
    fix_taxonomy_roi()
