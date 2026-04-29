import os
import sys
import json
from urllib.parse import urlparse
from collections import defaultdict
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.db_client import get_db_client

db = get_db_client()

KNOWN_SAFE_PREFIXES = [
    "pregrado", "posgrado", "cursos", "programas", "carreras",
    "maestria", "diplomados", "especializaciones", "cursos-cortos",
    "educacion-continua", "formacion-continua", "programa", "curso",
    "facultad", "escuela", "departamento", "admision", "estudios"
]

NOISE_INDICATORS = [
    "tag", "tags", "noticia", "noticias", "evento", "eventos",
    "blog", "articulo", "publicacion", "publicaciones", "node",
    "author", "category", "archive", "page", "pagina",
    "promocion", "promociones", "login", "register", "search",
    "carrito", "cart", "checkout", "add-to-cart", "api",
    "ventana", "indiscreta", "taxonomy", "agenda", "mooc",
    "agradecimiento", "clonado", "filtro", "popup", "banner",
    "wp-content", "wp-json", "feed", "rss", "sitemap",
    "politica", "terminos", "privacidad", "faq", "preguntas",
    "pdf", "doc", "img", "assets", "static", "media",
    "contacto", "contact", "nosotros", "acerca", "about",
    "admision", "transparencia", "biblioteca", "laboratorio"
]


def tokenize_paths(urls):
    tokens_l1 = defaultdict(int)
    tokens_l2 = defaultdict(int)
    tokens_l3 = defaultdict(list)

    seen_paths = set()
    for u in urls:
        path = urlparse(u).path
        path = path.rstrip('/')
        if not path or path in seen_paths:
            continue
        seen_paths.add(path)

        segments = [s.lower() for s in path.split('/') if s]
        if not segments:
            continue

        tokens_l1[f"/{segments[0]}/"] += 1

        if len(segments) >= 2:
            tokens_l2[f"/{segments[0]}/{segments[1]}/"] += 1

        if len(segments) >= 1:
            tokens_l3[f"/{segments[0]}/"].append(u)

    for k in tokens_l3:
        tokens_l3[k] = tokens_l3[k][:3]

    return tokens_l1, tokens_l2, tokens_l3


def is_noise_candidate(pattern):
    clean = pattern.strip('/').split('/')[0].lower()
    return clean in NOISE_INDICATORS


def score_confidence(count, total_staging, pattern, has_course_match):
    if has_course_match:
        return None

    ratio = count / max(total_staging, 1) * 100

    if count >= 50 or ratio > 5:
        return "HIGH"
    elif count >= 20 or ratio > 2:
        return "MEDIUM"
    elif count >= 10:
        return "LOW"
    return None


def build_exclusion_pattern(pattern):
    clean = pattern.strip('/')
    segments = clean.split('/')
    if len(segments) == 1:
        return f"/{segments[0]}/"
    return f"/{segments[0]}/{segments[1]}"


def analyze_institution(inst_id, inst_name):
    staging = db.select_all('staging_raw',
                            filters=f"institution_id=eq.{inst_id}",
                            columns="url")
    staging_urls = [r['url'] for r in staging]
    staging_set = set(staging_urls)

    courses = db.select_all('courses',
                            filters=f"institution_id=eq.{inst_id}",
                            columns="url")
    course_urls = [r['url'] for r in courses]
    course_set = set(course_urls)

    if not staging_urls:
        return None

    l1, l2, l3 = tokenize_paths(staging_urls)
    suggestions = []

    all_tokens = {**l1, **l2}
    for pattern, count in sorted(all_tokens.items(), key=lambda x: x[1], reverse=True):
        clean_key = pattern.strip('/').split('/')[0].lower()
        if clean_key in KNOWN_SAFE_PREFIXES:
            if count < 100:
                continue

        has_match = any(pattern in cu for cu in course_urls)
        level = score_confidence(count, len(staging_urls), pattern, has_match)

        if level is None:
            continue

        is_explicit_noise = is_noise_candidate(pattern)

        suggestions.append({
            "pattern": pattern,
            "exclusion": build_exclusion_pattern(pattern),
            "frequency": count,
            "confidence": level,
            "is_noise_indicator": is_explicit_noise,
            "has_course_conversion": has_match,
            "sample_urls": l3.get(pattern, [])[:3]
        })

    if suggestions:
        total_staging = len(staging_urls)
        total_courses = len(course_urls)
        high = sum(1 for s in suggestions if s['confidence'] == 'HIGH')
        med = sum(1 for s in suggestions if s['confidence'] == 'MEDIUM')
        low = sum(1 for s in suggestions if s['confidence'] == 'LOW')

        return {
            "institution_id": inst_id,
            "institution_name": inst_name,
            "staging_count": total_staging,
            "courses_count": total_courses,
            "conversion_rate_pct": round(total_courses / max(total_staging, 1) * 100, 1),
            "suggestions_count": {"HIGH": high, "MEDIUM": med, "LOW": low},
            "suggestions": suggestions
        }
    return None


def generate_report(results):
    ts = datetime.now()
    timestamp = ts.strftime('%Y%m%d_%H%M%S')
    lines = []
    lines.append(f"# Reporte Noise AI-Sentinel")
    lines.append(f"**Fecha:** {ts.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("Motor proactivo de deteccion de ruido en `staging_raw`. Identifica patrones de URL recurrentes sin conversion a cursos reales.")
    lines.append("")

    total_total = 0
    for r in results:
        s = r['suggestions_count']
        inst_total = s['HIGH'] + s['MEDIUM'] + s['LOW']
        total_total += inst_total

        lines.append(f"## {r['institution_name']}")
        lines.append(f"**URLs en staging:** {r['staging_count']} | **Cursos:** {r['courses_count']} | **Conversion:** {r['conversion_rate_pct']}%")
        lines.append(f"**Sugerencias:** HIGH={s['HIGH']}, MEDIUM={s['MEDIUM']}, LOW={s['LOW']}")
        lines.append("")

        if r['suggestions']:
            lines.append("| Patron | Frecuencia | Confianza | Indicador Ruido | Conversion |")
            lines.append("| :--- | :--- | :--- | :--- | :--- |")
            for sug in r['suggestions']:
                noise_flag = "SI" if sug['is_noise_indicator'] else "No"
                conv_flag = "SI" if sug['has_course_conversion'] else "NO"
                lines.append(f"| `{sug['pattern']}` | {sug['frequency']} | {sug['confidence']} | {noise_flag} | {conv_flag} |")
            lines.append("")
            lines.append("<details><summary>URLs de muestra</summary>")
            lines.append("")
            for sug in r['suggestions'][:10]:
                if sug['sample_urls']:
                    for su in sug['sample_urls']:
                        lines.append(f"- {su}")
                    lines.append("")
            lines.append("</details>")
            lines.append("")
        lines.append("---")
        lines.append("")

    if total_total == 0:
        lines.append("## Ningun patron de ruido detectado")
        lines.append("Todos los directorios en staging_raw tienen conversion a cursos o estan por debajo del umbral minimo.")

    lines.append("")
    lines.append("*Reporte generado por Noise AI-Sentinel (Fase 50)*")

    report_path = f"docs/data-analyst/reporte_sugerencias_exclusion_{timestamp}.md"
    os.makedirs("docs/data-analyst", exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    json_path = f"docs/data-analyst/noise_suggestions_{timestamp}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    return report_path, json_path, total_total


def run_discovery():
    print("Analizando instituciones...")
    institutions = db.select_all('institutions', columns="id,name", order="name.asc")
    print(f"  -> {len(institutions)} instituciones encontradas.")

    results = []
    for inst in institutions:
        inst_id = inst['id']
        inst_name = inst['name']
        print(f"  Analizando: {inst_name}...")
        result = analyze_institution(inst_id, inst_name)
        if result:
            results.append(result)
            s = result['suggestions_count']
            print(f"    Sugerencias: HIGH={s['HIGH']}, MEDIUM={s['MEDIUM']}, LOW={s['LOW']}")
        else:
            print(f"    Sin sugerencias.")

    report_path, json_path, total = generate_report(results)
    print(f"\nReporte: {report_path}")
    print(f"JSON: {json_path}")
    print(f"Total sugerencias: {total}")


if __name__ == "__main__":
    run_discovery()
