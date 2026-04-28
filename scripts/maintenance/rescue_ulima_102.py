import requests
import os
from dotenv import load_dotenv

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json"
}

ulima_id = "ccd04100-1bde-427b-b94f-ab24ae233a2a"

urls_to_rescue = [
    "https://www.ulima.edu.pe/pregrado/administracion", "https://www.ulima.edu.pe/pregrado/comunicacion",
    "https://www.ulima.edu.pe/pregrado/derecho", "https://www.ulima.edu.pe/pregrado/ingenieria-ambiental",
    "https://www.ulima.edu.pe/pregrado/ingenieria-industrial", "https://www.ulima.edu.pe/pregrado/ingenieria-de-sistemas",
    "https://www.ulima.edu.pe/pregrado/arquitectura", "https://www.ulima.edu.pe/pregrado/contabilidad-y-finanzas",
    "https://www.ulima.edu.pe/pregrado/economia", "https://www.ulima.edu.pe/pregrado/ingenieria-civil",
    "https://www.ulima.edu.pe/pregrado/ingenieria-mecatronica", "https://www.ulima.edu.pe/pregrado/marketing",
    "https://www.ulima.edu.pe/posgrado/maestria/macp", "https://www.ulima.edu.pe/posgrado/maestria/mbf",
    "https://www.ulima.edu.pe/posgrado/maestria/mcdn", "https://www.ulima.edu.pe/posgrado/maestria/mcgc",
    "https://www.ulima.edu.pe/posgrado/maestria/mde", "https://www.ulima.edu.pe/posgrado/maestria/mdop",
    "https://www.ulima.edu.pe/posgrado/maestria/mdie", "https://www.ulima.edu.pe/posgrado/maestria/mgi",
    "https://www.ulima.edu.pe/posgrado/maestria/mgc", "https://www.ulima.edu.pe/posgrado/maestria/mid",
    "https://www.ulima.edu.pe/posgrado/maestria/mlp", "https://www.ulima.edu.pe/posgrado/maestria/mmgc",
    "https://www.ulima.edu.pe/posgrado/maestria/mtpf", "https://www.ulima.edu.pe/posgrado/maestria/mba",
    "https://www.ulima.edu.pe/posgrado/doctorado/da", "https://www.ulima.edu.pe/posgrado/doctorado/dc",
    "https://www.ulima.edu.pe/posgrado/doctorado/dge", "https://www.ulima.edu.pe/idiomas/programa-integral-ingles",
    "https://www.ulima.edu.pe/idiomas/english-business", "https://www.ulima.edu.pe/idiomas/english-media",
    "https://www.ulima.edu.pe/idiomas/english-engineering", "https://www.ulima.edu.pe/idiomas/extension-workshops",
    "https://www.ulima.edu.pe/idiomas/intensive-graduation", "https://www.ulima.edu.pe/idiomas/b2-first",
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

print(f"--- Iniciando Rescate de {len(urls_to_rescue)} URLs de U. Lima ---")
rescued_count = 0
for u in urls_to_rescue:
    # Bypassear normalización local intentando con / y sin /
    for variant in [u, u.rstrip('/') + '/']:
        res = requests.patch(f"{url}/rest/v1/staging_raw?institution_id=eq.{ulima_id}&url=eq.{variant}", 
                             headers=headers, 
                             json={"status": "pending", "metadata": {"manual_rescue": "Phase 49.2"}})
        if res.status_code in [200, 204]:
            rescued_count += 1
            break # Si rescatamos una variante, pasamos a la siguiente URL

print(f"✅ Se han reseteado {rescued_count} programas a estado 'pending'.")
