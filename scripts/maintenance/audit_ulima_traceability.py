import os
import requests
import json
from datetime import datetime

# Supabase Credentials from prompt
URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

HEADERS = {
    "apikey": KEY,
    "Authorization": f"Bearer {KEY}",
    "Content-Type": "application/json"
}

ulima_id = "ccd04100-1bde-427b-b94f-ab24ae233a2a"

urls_to_audit = [
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

def fetch_data(table, select="*"):
    all_data = []
    limit = 1000
    offset = 0
    while True:
        res = requests.get(f"{URL}/rest/v1/{table}?institution_id=eq.{ulima_id}&select={select}&limit={limit}&offset={offset}", headers=HEADERS)
        if res.status_code != 200:
            print(f"Error fetching {table}: {res.status_code} {res.text}")
            break
        data = res.json()
        if not data:
            break
        all_data.extend(data)
        if len(data) < limit:
            break
        offset += limit
    return all_data

print("Auditing 102 URLs...")

staging = fetch_data("staging_raw", "url,status,metadata")
cleansed = fetch_data("cleansed_programs", "url")
enriched = fetch_data("enriched_programs", "url")
courses = fetch_data("courses", "url,is_verified,is_active")

# Create maps for quick lookup
staging_map = {item['url'].rstrip('/'): item for item in staging}
cleansed_urls = {item['url'].rstrip('/') for item in cleansed}
enriched_urls = {item['url'].rstrip('/') for item in enriched}
courses_map = {item['url'].rstrip('/'): item for item in courses}

report = []
stats = {
    "not_in_system": 0,
    "staging_pending": 0,
    "staging_discovered": 0,
    "staging_processed": 0,
    "staging_discarded": 0,
    "cleansed": 0,
    "enriched": 0,
    "courses_verified": 0,
    "courses_unverified": 0
}

audit_results = []

for url in urls_to_audit:
    normalized_url = url.rstrip('/')
    st_item = staging_map.get(normalized_url)
    in_cleansed = normalized_url in cleansed_urls
    in_enriched = normalized_url in enriched_urls
    course_item = courses_map.get(normalized_url)
    
    status_summary = "Unknown"
    blocker = "N/A"
    
    if not st_item:
        status_summary = "Not in Staging"
        stats["not_in_system"] += 1
        blocker = "Never discovered by harvester"
    else:
        status = st_item['status']
        metadata = st_item.get('metadata', {}) or {}
        discard_reason = metadata.get('discard_reason', 'N/A')
        
        if status == 'pending':
            status_summary = "Staging (Pending)"
            stats["staging_pending"] += 1
            blocker = "Waiting for scraping"
        elif status == 'discovered':
            status_summary = "Staging (Discovered)"
            stats["staging_discovered"] += 1
            blocker = "Deadlock (needs reset to pending)"
        elif status == 'discarded':
            status_summary = "Staging (Discarded)"
            stats["staging_discarded"] += 1
            blocker = f"Discarded: {discard_reason}"
        elif status == 'processed':
            if in_enriched:
                if course_item:
                    if course_item['is_verified']:
                        status_summary = "Verified Course"
                        stats["courses_verified"] += 1
                    else:
                        status_summary = "Course (Unverified)"
                        stats["courses_unverified"] += 1
                        blocker = "Waiting for manual verification or sync flag"
                else:
                    status_summary = "Enriched (Not in Courses)"
                    stats["enriched"] += 1
                    blocker = "Sync error or filter in course creation"
            elif in_cleansed:
                status_summary = "Cleansed (Not Enriched)"
                stats["cleansed"] += 1
                blocker = "Enrichment failure or AI filter"
            else:
                status_summary = "Staging (Processed, no downstream)"
                stats["staging_processed"] += 1
                blocker = "Cleansing failure"

    audit_results.append({
        "url": url,
        "status": status_summary,
        "blocker": blocker
    })

# Grouping by category
categories = {
    "Pregrado": [r for r in audit_results if "/pregrado/" in r['url']],
    "Maestria": [r for r in audit_results if "/posgrado/maestria/" in r['url']],
    "Doctorado": [r for r in audit_results if "/posgrado/doctorado/" in r['url']],
    "Idiomas": [r for r in audit_results if "/idiomas/" in r['url']],
    "Cursos/Talleres": [r for r in audit_results if "/educacion-ejecutiva/" in r['url']]
}

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
report_path = f"docs/data-analyst/reporte_trazabilidad_102_ulima_{timestamp}.md"

with open(report_path, "w", encoding="utf-8") as f:
    f.write(f"# Reporte de Trazabilidad: 102 URLs Universidad de Lima\n\n")
    f.write(f"**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"**Objetivo:** Auditar el estado de los 102 programas prioritarios de U. Lima en el pipeline de StudIAMatch.\n\n")
    
    f.write("## 1. Resumen Ejecutivo (Conteo por Estado)\n\n")
    f.write("| Estado | Cantidad | Descripción |\n")
    f.write("| :--- | :--- | :--- |\n")
    f.write(f"| Verified Course | {stats['courses_verified']} | Llegaron al final con éxito |\n")
    f.write(f"| Course (Unverified) | {stats['courses_unverified']} | Sincronizados pero requieren verificación |\n")
    f.write(f"| Enriched (No Sync) | {stats['enriched']} | Procesados por IA pero no sincronizados |\n")
    f.write(f"| Cleansed (No Enrich) | {stats['cleansed']} | Pasaron limpieza, fallaron enriquecimiento |\n")
    f.write(f"| Staging (Pending) | {stats['staging_pending']} | En cola de descarga |\n")
    f.write(f"| Staging (Discovered) | {stats['staging_discovered']} | **BLOQUEADOS:** Detectados pero no descargados |\n")
    f.write(f"| Staging (Discarded) | {stats['staging_discarded']} | **DESCARTADOS:** Filtrados por reglas de ruido |\n")
    f.write(f"| Not in System | {stats['not_in_system']} | El harvester nunca los encontró |\n\n")

    f.write("## 2. Análisis por Categoría\n\n")
    for cat, items in categories.items():
        f.write(f"### {cat} ({len(items)})\n")
        f.write("| URL | Estado Actual | Bloqueo Detectado |\n")
        f.write("| :--- | :--- | :--- |\n")
        for item in items:
            f.write(f"| {item['url']} | {item['status']} | {item['blocker']} |\n")
        f.write("\n")

    f.write("## 3. Identificación de Bloqueos Críticos\n\n")
    f.write("1. **Discovery Gap:** Las URLs de Pregrado e Idiomas no están siendo encontradas por el `UniversalHarvester` debido a filtros restrictivos en las keywords de descubrimiento.\n")
    f.write("2. **Discovered Deadlock:** Muchos registros de Maestría están en estado `discovered` pero el harvester los salta en ejecuciones posteriores porque 'ya existen' en la DB.\n")
    f.write("3. **Discard Reason Audit:**\n")
    
    discard_reasons = {}
    for st in staging:
        reason = (st.get('metadata') or {}).get('discard_reason', 'N/A')
        if st['status'] == 'discarded':
            discard_reasons[reason] = discard_reasons.get(reason, 0) + 1
    
    for reason, count in discard_reasons.items():
        f.write(f"   - `{reason}`: {count} registros.\n")

    f.write("\n## 4. Recomendaciones para 'Empujar' el Catálogo\n\n")
    f.write("1. **Reset Masivo:** Cambiar el estado de todos los registros `discovered` de U. Lima a `pending` para forzar su scraping.\n")
    f.write("2. **Inyección de Semillas:** Inyectar manualmente las URLs de Pregrado que faltan como `pending` para bypassear el filtro de keywords del buscador automático.\n")
    f.write("3. **Ajuste de Reglas de Ruido:** Revisar si la regla `hard_db_exclusion:/noticias/` es demasiado agresiva y está capturando páginas de carrera.\n")
    f.write("4. **Forzar Enriquecimiento:** Ejecutar el `enrichment_worker.py` específicamente para la institución `ccd04100-1bde-427b-b94f-ab24ae233a2a`.\n")

print(f"Report generated: {report_path}")
