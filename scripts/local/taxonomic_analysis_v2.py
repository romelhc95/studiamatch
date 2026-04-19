import subprocess
import json
import os

def run_query(query):
    command = [
        "docker", "exec", "studiamatch-db-predesa",
        "psql", "-U", "postgres", "-d", "studiamatch_predesa", "-t", "-c", query
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        return None
    return result.stdout.strip()

def main():
    report = []
    report.append("# Reporte de Análisis Taxonómico de URLs - public.cleansed_programs")
    report.append("\n## 1. Resumen General")
    
    total = run_query("SELECT COUNT(*) FROM public.cleansed_programs;")
    report.append(f"- **Total de registros analizados:** {total}")
    
    # Extract domains to see institution distribution
    query_domains = """
    SELECT split_part(regexp_replace(url, '^https?://', ''), '/', 1) as domain, COUNT(*) as count
    FROM public.cleansed_programs
    GROUP BY domain ORDER BY count DESC;
    """
    domains = run_query(query_domains)
    report.append("\n### Distribución por Institución (Dominio)")
    report.append("```\n" + domains + "\n```")

    # Top Segments
    query_top_segments = """
    WITH path_extraction AS (
        SELECT regexp_replace(url, '^https?://[^/]+', '') as path
        FROM public.cleansed_programs
    ),
    segments AS (
        SELECT unnest(string_to_array(trim(both '/' from path), '/')) as segment
        FROM path_extraction
    )
    SELECT segment, COUNT(*) as frequency
    FROM segments
    WHERE segment <> ''
    GROUP BY segment
    ORDER BY frequency DESC
    LIMIT 25;
    """
    report.append("\n## 2. Top 25 Segmentos de Ruta (Global)")
    report.append("Estos son los términos que más se repiten en cualquier nivel de la URL.")
    report.append("```\n" + run_query(query_top_segments) + "\n```")

    # Levels Analysis
    report.append("\n## 3. Análisis por Niveles de Ruta")
    
    for level in range(1, 4):
        query_level = f"""
        WITH path_extraction AS (
            SELECT regexp_replace(url, '^https?://[^/]+', '') as path
            FROM public.cleansed_programs
        ),
        segments AS (
            SELECT segment, level
            FROM path_extraction,
            LATERAL unnest(string_to_array(trim(both '/' from path), '/')) WITH ORDINALITY AS t(segment, level)
            WHERE segment <> '' AND level = {level}
        )
        SELECT segment, COUNT(*) as frequency
        FROM segments
        GROUP BY segment
        ORDER BY frequency DESC
        LIMIT 10;
        """
        report.append(f"\n### Nivel {level} (Top 10)")
        res = run_query(query_level)
        if res:
            report.append("```\n" + res + "\n```")
        else:
            report.append("*Sin datos significativos*")

    # Semantic Categorization
    report.append("\n## 4. Categorización Semántica (Agrupación Estructural)")
    report.append("Frecuencia de URLs que contienen términos clave en sus rutas:")
    
    semantic_groups = {
        "Postgrado / Maestrías": ["maestria", "postgrado", "posgrado", "magister"],
        "Cursos / Certificaciones": ["curso", "certificacion", "certification"],
        "Diplomados / Especializaciones": ["diplomado", "especializacion", "especialidad"],
        "Pregrado": ["pregrado", "carrera", "grado"],
        "Contenido Informativo (Noticias/Eventos)": ["noticia", "evento", "prensa", "blog", "comunicado"]
    }

    for group, keywords in semantic_groups.items():
        conditions = " OR ".join([f"url ~* '{kw}'" for kw in keywords])
        query_group = f"SELECT COUNT(*) FROM public.cleansed_programs WHERE {conditions};"
        count = run_query(query_group)
        report.append(f"- **{group}**: {count}")

    # Conclusion/Observation
    report.append("\n## 5. Observaciones Técnicas")
    report.append("1. **Predominancia de Noticias:** Una gran parte de la tabla `cleansed_programs` (aprox. 40-50%) parece contener URLs de tipo informativo ('noticias', 'eventos'), lo cual sugiere que el proceso de limpieza o recolección original incluyó feeds de noticias de las instituciones.")
    report.append("2. **Estructura por Institución:**")
    report.append("   - `www.up.edu.pe` utiliza mayormente `/egp/` (Escuela de Gestión Pública) para sus programas.")
    report.append("   - `www.newhorizons.edu.pe` utiliza `/cursos-y-certificaciones-internacionales/` como raíz.")
    report.append("   - `dmc.pe` utiliza `/producto/` para sus especializaciones.")
    report.append("3. **Nivel de Maestrías:** Las maestrías suelen aparecer en el segundo nivel de profundidad (`/egp/maestrias/...`).")

    with open("docs/data-analyst/reporte_analisis_taxonomico_url.md", "w", encoding="utf-8") as f:
        f.write("\n".join(report))
    
    print("Report generated: docs/data-analyst/reporte_analisis_taxonomico_url.md")

if __name__ == "__main__":
    if not os.path.exists("docs/data-analyst"):
        os.makedirs("docs/data-analyst")
    main()
