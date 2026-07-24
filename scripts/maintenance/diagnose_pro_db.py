#!/usr/bin/env python3
"""Diagnóstico rápido de Supabase Pro para validar estado pre-ejecución."""
import sys
sys.path.insert(0, '/app')
from scripts.shared.db_client import DatabaseClient
from scripts.shared.supabase_credentials import get_environment_credentials

PRO = get_environment_credentials("PRO")
db = DatabaseClient(PRO.url, PRO.secret_key)

print("=" * 60)
print("DIAGNÓSTICO SUPABASE PRO")
print("=" * 60)

# 1. Verificar si tablas de Fase 100 existen
print("\n1. Verificando tablas críticas...")
try:
    tables = db.select_service('information_schema.tables',
                      filters="table_schema=eq.public",
                      columns='table_name')
    table_names = [t['table_name'] for t in tables]
    
    critical_tables = ['institutions', 'institution_site_profiles', 'courses', 
                      'staging_raw', 'cleansed_programs', 'enriched_programs',
                      'categories', 'category_rules', 'market_salaries']
    
    for t in critical_tables:
        status = "✅" if t in table_names else "❌"
        print(f"  {status} {t}")
except Exception as e:
    print(f"  ❌ Error: {e}")

# 2. Verificar columnas de Fase 100 en institution_site_profiles
print("\n2. Verificando columnas Fase 100 en institution_site_profiles...")
try:
    cols = db.select_service('information_schema.columns',
                    filters="table_schema=eq.public&table_name=eq.institution_site_profiles",
                    columns='column_name')
    col_names = [c['column_name'] for c in cols]
    
    fase100_cols = ['pipeline_ready', 'discovery_enabled', 'production_enabled']
    for c in fase100_cols:
        status = "✅" if c in col_names else "❌"
        print(f"  {status} {c}")
except Exception as e:
    print(f"  ❌ Error: {e}")

# 3. Verificar estado de DMC
print("\n3. Verificando DMC en institutions...")
try:
    dmc = db.select_service('institutions', filters="slug=eq.dmc", columns='id,name,slug')
    if dmc:
        print(f"  ✅ DMC encontrado: {dmc[0]}")
    else:
        print("  ❌ DMC NO encontrado en institutions")
except Exception as e:
    print(f"  ❌ Error: {e}")

# 4. Verificar perfil de DMC
print("\n4. Verificando perfil de DMC...")
try:
    profiles = db.select_service('institution_site_profiles',
                        filters="institution_id=eq." + (dmc[0]['id'] if dmc else 'none'),
                        columns='pipeline_ready,discovery_enabled,production_enabled')
    if profiles:
        print(f"  ✅ Perfil encontrado: {profiles[0]}")
    else:
        print("  ❌ Perfil NO encontrado")
except Exception as e:
    print(f"  ❌ Error: {e}")

# 5. Conteos de tablas operativas
print("\n5. Conteos de tablas operativas...")
for table in ['staging_raw', 'cleansed_programs', 'enriched_programs', 'courses']:
    try:
        count = db.count_service(table)
        print(f"  {table}: {count} registros")
    except Exception as e:
        print(f"  {table}: Error - {e}")

# 6. Verificar cursos activos de DMC
print("\n6. Cursos activos/verificados de DMC...")
try:
    courses = db.select_service('courses',
                       filters="is_active=eq.true&is_verified=eq.true",
                       columns='id,name,slug,url')
    dmc_courses = [c for c in courses if 'dmc' in (c.get('slug', '') + c.get('url', '')).lower()]
    print(f"  Total cursos activos: {len(courses)}")
    print(f"  Cursos DMC: {len(dmc_courses)}")
    for c in dmc_courses[:5]:
        print(f"    - {c['name']} ({c['url']})")
except Exception as e:
    print(f"  ❌ Error: {e}")

print("\n" + "=" * 60)
print("DIAGNÓSTICO COMPLETADO")
print("=" * 60)
