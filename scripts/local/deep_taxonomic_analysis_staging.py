import subprocess
import json
import os
import sys

def run_query(query):
    command = [
        "docker", "exec", "studiamatch-db-predesa",
        "psql", "-U", "postgres", "-d", "studiamatch_predesa", "-t", "-c", query
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running query: {result.stderr}", file=sys.stderr)
        return None
    return result.stdout.strip()

def main():
    report = []
    report.append("# Reporte de Análisis Taxonómico Profundo de URLs - UNVERSO COMPLETO (staging_raw)")
    report.append("\n## 1. Resumen Ejecutivo")
    
    total = run_query("SELECT COUNT(*) FROM public.staging_raw;")
    report.append(f"- **Universo total de URLs analizadas:** {total}")
    
    # 2. Distribución por Dominio
    query_domains = """
    SELECT split_part(regexp_replace(url, '^https?://', ''), '/', 1) as domain, COUNT(*) as count
    FROM public.staging_raw
    GROUP BY domain ORDER BY count DESC;
    """
    domains = run_query(query_domains)
    report.append("\n## 2. Huella de Instituciones (Dominios)")
    report.append("```\n" + (domains if domains else "Sin datos") + "\n```")

    # 3. Descomposición por Niveles
    report.append("\n## 3. Estructura de Rutas por Niveles")
    report.append("Análisis de la arquitectura de información de los sitios capturados.")

    max_level_query = "SELECT max(cardinality(string_to_array(trim(both '/' from regexp_replace(url, '^https?://[^/]+', '')), '/'))) FROM public.staging_raw;"
    max_level = int(run_query(max_level_query) or 0)
    
    for level in range(1, max_level + 1):
        query_level = f"""
        WITH path_extraction AS (
            SELECT regexp_replace(url, '^https?://[^/]+', '') as path
            FROM public.staging_raw
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
        LIMIT 20;
        """
        res = run_query(query_level)
        if res:
            report.append(f"\n### Nivel {level} - Top 20 Segmentos")
            report.append("```\n" + res + "\n```")

    # 4. Detección de Patrones: Valor vs Ruido
    report.append("\n## 4. Análisis de Calidad de Contenido (Basado en Patrones)")
    
    patterns = {
        "VALOR: Programas / Cursos / Maestrías": ["curso", "maestria", "posgrado", "postgrado", "magister", "diplomado", "especializacion", "carrera", "grado", "producto", "p-", "certificacion", "certification", "programs", "academicos"],
        "RUIDO: Noticias / Blogs / Eventos": ["noticia", "evento", "prensa", "blog", "comunicado", "news", "articles", "actualidad", "agenda", "galeria", "category", "tag"],
        "RUIDO: Administrativo / Legal": ["contacto", "nosotros", "mision", "vision", "terminos", "privacidad", "legal", "cookies", "login", "admin", "wp-content", "wp-includes"]
    }

    report.append("| Categoría | Cantidad URLs | Porcentaje |")
    report.append("|-----------|---------------|------------|")
    
    for cat, keywords in patterns.items():
        conditions = " OR ".join([f"url ~* '{kw}'" for kw in keywords])
        count = int(run_query(f"SELECT COUNT(*) FROM public.staging_raw WHERE {conditions};") or 0)
        percentage = round((count / int(total)) * 100, 2) if int(total) > 0 else 0
        report.append(f"| {cat} | {count} | {percentage}% |")

    # 5. Segmentos Globales (Mapa de Calor)
    report.append("\n## 5. Mapa de Calor Global (Top 50 Segmentos)")
    report.append("Frecuencia absoluta de términos en cualquier posición de la URL.")
    
    query_global = """
    WITH segments AS (
        SELECT unnest(string_to_array(trim(both '/' from regexp_replace(url, '^https?://[^/]+', '')), '/')) as segment
        FROM public.staging_raw
    )
    SELECT segment, COUNT(*) as freq
    FROM segments
    WHERE segment <> ''
    GROUP BY segment
    ORDER BY freq DESC
    LIMIT 50;
    """
    global_segments = run_query(query_global)
    report.append("```\n" + (global_segments if global_segments else "Sin datos") + "\n```")

    # 6. Conclusiones para Revisión Manual
    report.append("\n## 6. Conclusiones y Recomendaciones para Limpieza")
    
    # Logic to identify messy institutions
    report.append("### Hallazgos Clave:")
    
    # Check if we have many news
    news_count = int(run_query("SELECT COUNT(*) FROM public.staging_raw WHERE url ~* 'noticia|noticias|news|prensa';") or 0)
    if news_count > 100:
        report.append(f"- **Alerta de Ruido Informativo:** Se detectaron {news_count} URLs relacionadas con noticias. Se recomienda filtrar el segmento `/noticias/` y `/prensa/` antes de la ingesta final.")
    
    # Check for duplicate-like patterns or generic paths
    p_count = int(run_query("SELECT COUNT(*) FROM public.staging_raw WHERE url ~* '/p/';") or 0)
    if p_count > 0:
        report.append(f"- **Identificadores de Producto:** `{p_count}` URLs utilizan el patrón `/p/` (común en VTEX o plataformas E-commerce), que suelen ser páginas de producto final de alto valor.")

    report.append("\n### Acciones Sugeridas:")
    report.append("1. **Blacklist Sugerida:** Eliminar URLs que contengan `wp-json`, `wp-content`, `/category/`, `/tag/`, `/author/`.")
    report.append("2. **Filtro de Profundidad:** Las URLs con nivel > 4 suelen ser muy específicas o basura técnica.")
    report.append("3. **Priorización:** Enfocarse en dominios con mayor densidad de palabras clave de 'VALOR' identificadas en la sección 4.")

    output_path = "docs/data-analyst/reporte_analisis_taxonomico_staging.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report))
    
    print(f"Reporte generado exitosamente en: {output_path}")

if __name__ == "__main__":
    if not os.path.exists("docs/data-analyst"):
        os.makedirs("docs/data-analyst")
    main()
