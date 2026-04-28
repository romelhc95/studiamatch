import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
headers = {'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}'}

def export_data():
    print("-- DEBUG: Exportando datos...")
    
    # Categorías
    r = requests.get(f'{SUPABASE_URL}/rest/v1/categories?select=name,description', headers=headers)
    cats = r.json()
    if not isinstance(cats, list):
        print(f"-- ERROR Categorías: {json.dumps(cats)}")
        return

    # Salarios
    r = requests.get(f'{SUPABASE_URL}/rest/v1/market_salaries?select=category_name,salary_junior,salary_average,salary_senior', headers=headers)
    salaries = r.json()
    if not isinstance(salaries, list):
        print(f"-- ERROR Salarios: {json.dumps(salaries)}")
        return

    # Si todo bien, imprimir SQL
    print("-- CATEGORIAS")
    cat_list = [f"('{c['name']}', '{c['description'] or ''}')" for c in cats]
    print("INSERT INTO public.categories (name, description) VALUES " + ",\n".join(cat_list) + " ON CONFLICT (name) DO NOTHING;")
    
    print("\n-- SALARIOS")
    print("INSERT INTO public.market_salaries (category_id, category_name, salary_junior, salary_average, salary_senior)")
    print("SELECT c.id, s.cat_name, s.sj, s.sa, s.ss FROM ( VALUES ")
    sal_list = [f"('{s['category_name']}', {s['salary_junior']}, {s['salary_average']}, {s['salary_senior']})" for s in salaries]
    print(",\n".join(sal_list))
    print(") as s(cat_name, sj, sa, ss) JOIN public.categories c ON c.name = s.cat_name ON CONFLICT (category_name) DO NOTHING;")

if __name__ == "__main__":
    import json
    export_data()
