import os
import requests
from dotenv import load_dotenv

load_dotenv(".env.local")
url = os.getenv("SUPABASE_URL", os.getenv("SUPABASE_URL"))
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not key:
    print("❌ ERROR: SUPABASE_SERVICE_ROLE_KEY no encontrada.")
    exit(1)

headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

ulima_id = "ccd04100-1bde-427b-b94f-ab24ae233a2a"

print("--- 1. Reseteando registros 'discovered' a 'pending' ---")
res_discovered = requests.get(f"{url}/rest/v1/staging_raw?institution_id=eq.{ulima_id}&status=eq.discovered&select=id", headers=headers)
if res_discovered.status_code == 200:
    records = res_discovered.json()
    count = 0
    for r in records:
        patch_res = requests.patch(f"{url}/rest/v1/staging_raw?id=eq.{r['id']}", headers=headers, json={"status": "pending"})
        if patch_res.status_code in [200, 204]:
            count += 1
    print(f"✅ Se resetearon {count} registros a 'pending'.")
else:
    print(f"❌ Error al obtener registros discovered: {res_discovered.status_code} - {res_discovered.text}")

print("\n--- 2. Inyectando Lista Maestra de 102 URLs ---")
urls_to_inject = [
    "https://www.ulima.edu.pe/pregrado/administracion",
    "https://www.ulima.edu.pe/pregrado/comunicacion",
    "https://www.ulima.edu.pe/pregrado/derecho",
    "https://www.ulima.edu.pe/pregrado/ingenieria-ambiental",
    "https://www.ulima.edu.pe/pregrado/ingenieria-industrial",
    "https://www.ulima.edu.pe/pregrado/ingenieria-de-sistemas",
    "https://www.ulima.edu.pe/pregrado/arquitectura",
    "https://www.ulima.edu.pe/pregrado/contabilidad-y-finanzas",
    "https://www.ulima.edu.pe/pregrado/economia",
    "https://www.ulima.edu.pe/pregrado/ingenieria-civil",
    "https://www.ulima.edu.pe/pregrado/ingenieria-mecatronica",
    "https://www.ulima.edu.pe/pregrado/marketing",
    "https://www.ulima.edu.pe/posgrado/maestria/macp",
    "https://www.ulima.edu.pe/posgrado/maestria/mbf",
    "https://www.ulima.edu.pe/posgrado/maestria/mcdn",
    "https://www.ulima.edu.pe/posgrado/maestria/mcgc",
    "https://www.ulima.edu.pe/posgrado/maestria/mde",
    "https://www.ulima.edu.pe/posgrado/maestria/mdop",
    "https://www.ulima.edu.pe/posgrado/maestria/mdie",
    "https://www.ulima.edu.pe/posgrado/maestria/mgi",
    "https://www.ulima.edu.pe/posgrado/maestria/mgc",
    "https://www.ulima.edu.pe/posgrado/maestria/mid",
    "https://www.ulima.edu.pe/posgrado/maestria/mlp",
    "https://www.ulima.edu.pe/posgrado/maestria/mmgc",
    "https://www.ulima.edu.pe/posgrado/maestria/mtpf",
    "https://www.ulima.edu.pe/posgrado/maestria/mba",
    "https://www.ulima.edu.pe/posgrado/doctorado/da",
    "https://www.ulima.edu.pe/posgrado/doctorado/dc",
    "https://www.ulima.edu.pe/posgrado/doctorado/dge",
    "https://www.ulima.edu.pe/idiomas/programa-integral-ingles",
    "https://www.ulima.edu.pe/idiomas/english-business",
    "https://www.ulima.edu.pe/idiomas/english-media",
    "https://www.ulima.edu.pe/idiomas/english-engineering",
    "https://www.ulima.edu.pe/idiomas/extension-workshops",
    "https://www.ulima.edu.pe/idiomas/intensive-graduation",
    "https://www.ulima.edu.pe/idiomas/b2-first",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-comunicacion-marketing-politico",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-cultura-organizacional",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/vir-presentaciones-alto-impacto",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-alto-impacto-presentaciones",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-arbitraje",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-app",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-corporate-compliance",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-legaltech-ia-abogados",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-ley-contrataciones-estado",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/vir-obras-impuesto",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-obras-publicas",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/vir-resolucion-conflictos",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-gestion-compensacion-total",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-people-analytics",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-domina-tiempo",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-expresate-lidera",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-power-skills",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-soft-skills",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-liderazgo-alto-desempeno",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-analisis-fundamental",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-analisis-tecnico",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-elaboracion-presupuestos",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-finanzas-no-especialistas",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-gestion-tesoreria",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-gestion-riesgo-compliance",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-impuesto-renta",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-control-interno",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-niif",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-inversion-bolsa",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-python-aplicado-finanzas",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-fraude-auditoria-forense",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-bloomberg",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-construccion",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-marca-ia",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-growth-hacking",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-ia-marketing-digital",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-kam",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-negociacion-comercial",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/vir-marketing-digital",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-retail-category-management",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-social-media",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-ia-creadores-contenido",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-metodologias-agiles",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-direccion-supply-chain",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-gestion-proyectos",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/vir-mejora-rediseno-procesos",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-planeamiento-estrategico",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/vir-seguridad-salud-trabajo",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-future-thinking",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-arquitectura-soluciones-digitales",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-business-analytics",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-data-analytics",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-visualizacion-datos-power-bi",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-power-bi",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-excel",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-gobierno-datos",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-ia-generativa-negocios",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-modernizacion-aplicaciones",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-power-bi-desde-cero",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-transformacion-digital",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-fundamentos-power-bi",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-ia-contenido-textual",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-talent-shift",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-transformacion-digital",
    "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-sql-decisiones-negocio"
]

count_injected = 0
for u in urls_to_inject:
    payload = {"url": u, "institution_id": ulima_id, "status": "pending"}
    res = requests.post(f"{url}/rest/v1/staging_raw", headers={**headers, "Prefer": "resolution=merge-duplicates"}, json=payload)
    if res.status_code in [200, 201]:
        count_injected += 1
    else:
        # If it already exists and merge-duplicates fails, force patch to pending
        res_patch = requests.patch(f"{url}/rest/v1/staging_raw?url=eq.{u}", headers=headers, json={"status": "pending"})
        if res_patch.status_code in [200, 204]: 
            count_injected += 1

print(f"✅ Se inyectaron/actualizaron {count_injected} URLs maestras con estado 'pending'.")

print("\n--- 3. Verificando estado final ---")
res_check = requests.get(f"{url}/rest/v1/staging_raw?institution_id=eq.{ulima_id}&status=eq.pending&select=count", headers={'apikey': key, 'Authorization': f'Bearer {key}', 'Prefer': 'count=exact'})
print(f"Registros en pending para U. Lima: {res_check.json()}")
