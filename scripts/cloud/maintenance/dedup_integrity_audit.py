import os
import requests
import json
from dotenv import load_dotenv
from urllib.parse import quote

load_dotenv()

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
BASE_URL = "http://localhost:3000"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}"
}

def clean_slug(slug_or_url, url=None):
    if url:
        try:
            from urllib.parse import urlparse
            path = urlparse(url).path
            segments = [s for s in path.split('/') if s]
            if segments:
                last = segments[-1]
                if len(last) > 2:
                    import re
                    # Simple normalization for the script
                    res = last.lower()
                    res = re.sub(r'[^a-z0-9-]', '-', res)
                    res = re.sub(r'-+', '-', res)
                    return res.strip('-')
        except:
            pass
    
    import re
    res = slug_or_url.lower()
    res = re.sub(r'[^a-z0-9-]', '-', res)
    res = re.sub(r'-+', '-', res)
    return res.strip('-')

def run_audit():
    print("Iniciando Auditoria de Unicidad e Integridad de URLs...")
    
    # 1. Fetch courses and institutions
    payload = "select=id,name,slug,url,institution_id,course_type,institutions(slug)&is_active=eq.true"
    res = requests.get(f"{SUPABASE_URL}/rest/v1/courses?{payload}", headers=headers)
    
    if res.status_code != 200:
        print(f"Error: {res.status_code}")
        return

    courses = res.json()
    total = len(courses)
    
    # 2. De-duplication check (Logic same as frontend)
    unique_map = {}
    duplicates = []
    
    for c in courses:
        inst_slug = c.get("institutions", {}).get("slug") if c.get("institutions") else "general"
        # We use institution_id and url or slug as key
        key = f"{c['institution_id']}-{c.get('url') or c['slug']}"
        
        if key in unique_map:
            existing = unique_map[key]
            # Prefer Programa
            if c['course_type'] == 'Programa' and existing['course_type'] != 'Programa':
                duplicates.append(existing)
                unique_map[key] = c
            else:
                duplicates.append(c)
        else:
            unique_map[key] = c

    unique_courses = list(unique_map.values())
    
    # 3. Integrity Check (Sample testing)
    print(f"Unicidad: {len(unique_courses)} cursos unicos detectados de {total} totales.")
    
    test_results = []
    # Test top 10 unique courses to ensure no "Lo sentimos"
    to_test = unique_courses[:15]
    
    print(f"Probando integridad de {len(to_test)} URLs aleatorias...")
    for c in to_test:
        inst_slug = c.get("institutions", {}).get("slug") if c.get("institutions") else "general"
        slug = clean_slug(c['slug'], c.get('url'))
        local_url = f"{BASE_URL}/courses/{inst_slug}/{slug}"
        
        try:
            r = requests.get(local_url, timeout=5)
            # Check if "Lo sentimos" is in the text
            is_dead = "Lo sentimos" in r.text or r.status_code != 200
            test_results.append({
                "name": c['name'],
                "url": local_url,
                "status": "ALIVE" if not is_dead else "DEAD",
                "code": r.status_code
            })
        except Exception as e:
            test_results.append({
                "name": c['name'],
                "url": local_url,
                "status": "ERROR",
                "code": 0
            })

    # ... rest of the logic ...
    print(f"Reporte generado.")

    # 4. Generate Formal Report
    os.makedirs("docs/qa-engineer", exist_ok=True)
    report_path = "docs/qa-engineer/reporte_duplicidad_integridad.md"
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Informe de Unicidad e Integridad - Phase 29\n\n")
        f.write("## 1. Análisis de Unicidad (Caminos de Ruta)\n")
        f.write(f"- **Total de registros en DB:** {total}\n")
        f.write(f"- **Cursos únicos renderizados:** {len(unique_courses)}\n")
        f.write(f"- **Registros filtrados (Duplicados técnicos):** {len(duplicates)}\n")
        f.write("- **Criterio de De-duplicación:** `(institution_id, source_url)`. Se prioriza 'Programa' sobre 'Curso'.\n\n")
        
        if duplicates:
            f.write("### Ejemplos de Duplicados Identificados y Filtrados\n")
            for d in duplicates[:5]:
                f.write(f"- `{d['name']}` ({d['course_type']}) - URL: {d.get('url', 'N/A')}\n")
            f.write("\n")

        f.write("## 2. Auditoría de Integridad (URLs Vivas)\n")
        f.write("Se ha verificado la navegación dinámica hacia el detalle de los cursos para asegurar que el ruteo `/[institution]/[slug]` resuelve correctamente.\n\n")
        
        f.write("| Curso | URL Local | Estado |\n")
        f.write("| :--- | :--- | :--- |\n")
        for r in test_results:
            status_icon = "✅" if r['status'] == "ALIVE" else "❌"
            f.write(f"| {r['name']} | [{r['url']}]({r['url']}) | {status_icon} {r['status']} |\n")
            
        f.write("\n\n---\n*Reporte generado automáticamente por Antigravity QA Engine.*")

    print(f"📊 Reporte generado en: {report_path}")

if __name__ == "__main__":
    run_audit()
