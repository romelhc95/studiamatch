#!/usr/bin/env python3
"""Validar que los cursos en Pro coincidan con el artifact dmc.txt."""
import sys
sys.path.insert(0, '/app')
from scripts.shared.db_client import DatabaseClient
from scripts.shared.supabase_credentials import get_environment_credentials

# Leer URLs del artifact
with open('/app/artifacts/urls_interes/dmc.txt', 'r') as f:
    artifact_urls = set()
    for line in f:
        line = line.strip()
        if line.startswith('http'):
            # Normalizar URL
            url = line.replace('http://', 'https://').rstrip('/')
            artifact_urls.add(url)

print(f"URLs de interés en artifact: {len(artifact_urls)}")

# Obtener cursos DMC de Pro
PRO = get_environment_credentials("PRO")
db = DatabaseClient(PRO.url, PRO.secret_key)
try:
    courses = db.select_service('courses',
                       filters="is_active=eq.true&is_verified=eq.true",
                       columns='id,name,slug,url,institution_id')
    
    # Obtener institution_id de DMC
    dmc = db.select_service('institutions', filters="slug=eq.dmc", columns='id')
    dmc_id = dmc[0]['id'] if dmc else None
    
    dmc_courses = [c for c in courses if c.get('institution_id') == dmc_id]
    
    print(f"Cursos DMC en Pro: {len(dmc_courses)}")
    
    # Comparar URLs
    course_urls = set()
    matched = []
    unmatched = []
    
    for c in dmc_courses:
        url = (c.get('url') or '').replace('http://', 'https://').rstrip('/')
        if url:
            course_urls.add(url)
            if url in artifact_urls:
                matched.append((c['name'], url))
            else:
                unmatched.append((c['name'], url))
    
    # URLs en artifact que no están en Pro
    missing = artifact_urls - course_urls
    
    print(f"\n✅ Coinciden: {len(matched)}")
    print(f"⚠️ En Pro pero no en artifact: {len(unmatched)}")
    print(f"❌ En artifact pero no en Pro: {len(missing)}")
    
    if missing:
        print("\nURLs faltantes en Pro:")
        for url in sorted(missing)[:10]:
            print(f"  - {url}")
    
    if unmatched:
        print("\nProgramas extra en Pro (no en artifact):")
        for name, url in sorted(unmatched)[:5]:
            print(f"  - {name}: {url}")
    
    # Cobertura
    coverage = len(matched) / len(artifact_urls) * 100 if artifact_urls else 0
    print(f"\n📊 Cobertura: {coverage:.1f}% ({len(matched)}/{len(artifact_urls)})")
    
    if coverage >= 95:
        print("✅ VALIDACIÓN EXITOSA: Más del 95% de los programas de interés están en Pro.")
    elif coverage >= 80:
        print("⚠️ VALIDACIÓN PARCIAL: Entre 80-95% de cobertura.")
    else:
        print("❌ VALIDACIÓN FALLIDA: Menos del 80% de cobertura.")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
