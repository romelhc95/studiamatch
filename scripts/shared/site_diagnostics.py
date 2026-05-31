#!/usr/bin/env python3
"""Fase 121: Modulo compartido de diagnostico de sitios.

Extrae la logica de deteccion de diagnose_institution.py para que
pueda ser usada tanto por el script de diagnostico como por el
universal_harvester.py en modo auto-deteccion.

Uso:
    from shared.site_diagnostics import diagnose_site, assign_template
"""

import json
import re
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}

NON_HTML_EXTENSIONS = re.compile(
    r"\.(pdf|xlsx?|docx?|pptx?|zip|rar|png|jpe?g|gif|svg|mp4|webm|css|js)$", re.I
)

PRICE_REGEX_PATTERNS = [
    (re.compile(r"S/\s*([\d,]+\.?\d*)", re.I), "PEN"),
    (re.compile(r"\$\s*([\d,]+\.?\d*)"), "USD"),
    (re.compile(r"USD\s*([\d,]+\.?\d*)", re.I), "USD"),
    (re.compile(r"€\s*([\d,]+\.?\d*)"), "EUR"),
]

DATE_KEYWORDS = [
    "inicio", "inicia", "comienza", "fecha de inicio",
    "start date", "duracion", "duración", "duration",
]

NOISE_PATH_PATTERNS = [
    "/blog/", "/noticias/", "/contacto/", "/nosotros/",
    "/sobre-nosotros/", "/author/", "/category/", "/tag/",
    "/eventos/", "/admision/", "/biblioteca/", "/investigacion/",
    "/login/", "/register/", "/politica/", "/terminos/",
    "/checkout/", "/cart/", "/carrito/", "/mi-cuenta/",
]

CATALOG_PATH_PATTERNS = [
    "/cursos/", "/curso/", "/programas/", "/programa/",
    "/carreras/", "/carrera/", "/diplomados/", "/especializaciones/",
    "/producto/", "/maestrias/", "/posgrado/",
]


def _get(url: str, timeout: int = 10):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        return r.status_code, r.text, r.url
    except Exception:
        return None, "", url


def detect_cms(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    cms = "html_puro"
    signals = []

    meta_gen = soup.find("meta", attrs={"name": "generator"})
    if meta_gen:
        gen = (meta_gen.get("content", "") or "").lower()
        if "wordpress" in gen:
            cms = "wordpress"
            signals.append("meta_generator:wordpress")
        elif "joomla" in gen:
            cms = "joomla"
            signals.append("meta_generator:joomla")
        elif "hubspot" in gen:
            cms = "hubspot"
            signals.append("meta_generator:hubspot")

    if "/wp-content/" in html or "wp-json" in html:
        cms = "wordpress"
        signals.append("wp_content_paths")

    if "woocommerce" in html.lower() or "woocommerce-LoopProduct-link" in html:
        cms = "woocommerce"
        signals.append("woocommerce_markers")

    if "hs-scripts.com" in html or "hubspot" in html.lower():
        if cms == "html_puro":
            cms = "hubspot"
        signals.append("hubspot_scripts")

    scripts_srcs = [s.get("src", "") for s in soup.find_all("script", src=True)]
    for src in scripts_srcs:
        lsrc = src.lower()
        if "react" in lsrc and "react" not in signals:
            signals.append("react_script")
            if cms == "html_puro":
                cms = "react"
        if "vue" in lsrc and "vue" not in signals:
            signals.append("vue_script")
            if cms == "html_puro":
                cms = "vue"
        if "angular" in lsrc and "angular" not in signals:
            signals.append("angular_script")
            if cms == "html_puro":
                cms = "angular"

    return {"cms": cms, "signals": signals}


def detect_sitemap(base_url: str) -> dict:
    parsed = urlparse(base_url)
    root = f"{parsed.scheme}://{parsed.netloc}"
    candidates = [
        f"{root}/sitemap.xml",
        f"{root}/sitemap_index.xml",
        f"{root}/post-sitemap.xml",
        f"{root}/page-sitemap.xml",
    ]
    found = []
    for url in candidates:
        status, _, _ = _get(url, timeout=5)
        if status == 200:
            found.append(url)
    return {"found": len(found) > 0, "urls": found}


def detect_json_ld(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    result = {}
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            if isinstance(data, dict):
                at_type = data.get("@type", "")
                result[at_type.lower()] = data
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        at_type = item.get("@type", "")
                        result[at_type.lower()] = item
        except (json.JSONDecodeError, TypeError):
            pass
    return result


def detect_price_patterns(html: str) -> dict:
    text = BeautifulSoup(html, "html.parser").get_text()
    for pattern, currency in PRICE_REGEX_PATTERNS:
        matches = pattern.findall(text)
        if matches:
            prices = []
            for m in matches:
                try:
                    p = float(m.replace(",", ""))
                    if 10 < p < 1000000:
                        prices.append(p)
                except ValueError:
                    pass
            if prices:
                return {
                    "currency": currency,
                    "prices_found": prices[:5],
                    "regex": pattern.pattern,
                }
    return {}


def detect_date_texts(html: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    results = []
    text = soup.get_text()
    for kw in DATE_KEYWORDS:
        idx = text.lower().find(kw)
        if idx >= 0:
            snippet = text[max(0, idx - 5):idx + len(kw) + 60].strip()
            results.append(snippet[:100])
    return results[:10]


def detect_section_headings(html: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    headings = []
    for tag in soup.find_all(["h1", "h2", "h3", "h4"]):
        text = tag.get_text(strip=True).lower()
        headings.append(text[:100])
    return headings


def detect_catalog_links(html: str, base_url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    catalog_urls = []
    noise_urls = []

    for a in soup.find_all("a", href=True):
        href = a["href"]
        full_url = urljoin(base_url, href)
        if NON_HTML_EXTENSIONS.search(full_url):
            continue
        path = urlparse(full_url).path.lower()
        if any(pattern in path for pattern in CATALOG_PATH_PATTERNS):
            catalog_urls.append(full_url)
        if any(pattern in path for pattern in NOISE_PATH_PATTERNS):
            noise_urls.append(full_url)

    return {
        "catalog_urls": list(set(catalog_urls))[:20],
        "noise_urls_detected": list(set(noise_urls))[:10],
    }


def detect_js_required(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    body_text = soup.body.get_text(strip=True) if soup.body else ""
    needs_js = len(body_text) < 500
    return {"needs_js": needs_js, "body_text_length": len(body_text)}


def detect_institution_metadata(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.string.strip() if soup.title else ""
    og_site = soup.find("meta", property="og:site_name")
    site_name = og_site["content"].strip() if og_site else ""
    parsed = urlparse(url)
    domain = parsed.netloc.replace("www.", "")
    slug_candidate = domain.split(".")[0].lower()

    return {
        "title_tag": title[:200],
        "og_site_name": site_name,
        "domain": domain,
        "suggested_slug": slug_candidate,
    }


def suggest_site_type(cms_result: dict, js_result: dict) -> str:
    cms = cms_result.get("cms", "html_puro")
    if cms == "woocommerce":
        return "ecommerce"
    if cms == "hubspot":
        return "traditional_ssr"
    if js_result.get("needs_js"):
        return "spa_js_heavy"
    return "traditional_ssr"


def suggest_discovery_mode(sitemap_result: dict, catalog_result: dict) -> str:
    if catalog_result.get("catalog_urls"):
        return "catalog_link_extraction"
    if sitemap_result.get("found"):
        return "sitemap_bfs"
    return "hardcoded_urls"


def build_section_keywords(headings: list) -> dict:
    mapping = {}
    for h in headings:
        hl = h.lower()
        if any(w in hl for w in ["inversión", "inversion", "precio", "costo"]):
            mapping.setdefault("total_cost_est", h)
        elif any(w in hl for w in ["inicio", "fecha", "comienza"]):
            mapping.setdefault("start_date", h)
        elif any(w in hl for w in ["duración", "duracion", "duration"]):
            mapping.setdefault("duration_text", h)
        elif any(w in hl for w in ["modalidad", "presencial", "remoto", "virtual"]):
            mapping.setdefault("modality", h)
        elif any(w in hl for w in ["dirigido a", "requisitos", "prerrequisitos"]):
            mapping.setdefault("requirements", h)
        elif any(w in hl for w in ["certificación", "certificacion", "diploma"]):
            mapping.setdefault("certifications", h)
        elif any(w in hl for w in ["malla", "plan de estudios", "temario", "contenido"]):
            mapping.setdefault("curriculum_summary", h)
        elif any(w in hl for w in ["perfil del egresado", "perfil del graduado", "objetivos"]):
            mapping.setdefault("graduate_profile", h)
    return mapping


def build_exclusion_patterns(base_url: str, catalog_result: dict) -> list:
    patterns = list(catalog_result.get("noise_urls_detected", []))
    parsed = urlparse(base_url)
    domain = parsed.netloc
    patterns.append(f"re:{domain}/?$")
    patterns.extend([
        "/blog/", "/contacto/", "/nosotros/", "/noticias/",
        "/eventos/", "/login/", "/politica/",
    ])
    return list(set(patterns))[:30]


def assign_template(diagnosis: dict) -> dict:
    """Asigna una plantilla base segun el tipo de sitio detectado."""
    cms = diagnosis.get("cms", {}).get("cms", "html_puro")
    js = diagnosis.get("js", {})

    if cms == "woocommerce":
        return {
            "site_type": "ecommerce",
            "discovery_mode": "catalog_link_extraction",
            "catalog_link_selector": "a.woocommerce-LoopProduct-link",
            "requires_stealth": False,
            "requires_cloudflare_bypass": False,
            "catalog_scroll_iterations": 15,
            "detail_wait_ms": 5000,
            "pipeline_ready": False,
        }
    if cms == "hubspot":
        return {
            "site_type": "traditional_ssr",
            "discovery_mode": "hardcoded_urls",
            "requires_stealth": False,
            "requires_cloudflare_bypass": False,
            "pipeline_enabled": False,
            "pipeline_ready": False,
            "detail_wait_ms": 2000,
        }
    if js.get("needs_js") and cms in ("react", "vue", "angular"):
        return {
            "site_type": "spa_js_heavy",
            "discovery_mode": "sitemap_bfs",
            "requires_stealth": True,
            "requires_cloudflare_bypass": True,
            "detail_wait_ms": 3000,
            "pipeline_ready": False,
        }

    return {
        "site_type": "traditional_ssr",
        "discovery_mode": "sitemap_bfs",
        "requires_stealth": False,
        "requires_cloudflare_bypass": False,
        "detail_wait_ms": 2000,
        "pipeline_ready": False,
    }


def diagnose_site(url: str, logger=None) -> dict:
    """Ejecuta diagnostico completo de un sitio web.
    Retorna un dict con perfil sugerido + confidence levels.
    """
    def _log(msg):
        if logger:
            logger.info(msg)

    _log(f"Diagnosticando {url} ...")
    t0 = time.time()

    status, html, final_url = url, "", url
    try:
        r = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        status = r.status_code
        html = r.text
        final_url = r.url
    except Exception as e:
        return {"error": str(e), "url": url}

    if not html:
        return {"error": f"No se pudo obtener la pagina (status={status})", "url": url}

    _log(f"HTTP {status} ({len(html)} bytes, {time.time() - t0:.1f}s)")

    cms = detect_cms(html)
    sitemap = detect_sitemap(final_url)
    ld = detect_json_ld(html)
    price = detect_price_patterns(html)
    dates = detect_date_texts(html)
    headings = detect_section_headings(html)
    catalog = detect_catalog_links(html, final_url)
    js = detect_js_required(html)
    meta = detect_institution_metadata(html, final_url)

    template = assign_template({"cms": cms, "js": js})
    site_type = suggest_site_type(cms, js)
    discovery_mode = suggest_discovery_mode(sitemap, catalog)
    section_kw = build_section_keywords(headings)
    exclusion = build_exclusion_patterns(final_url, catalog)

    profile = {
        "site_type": site_type,
        "discovery_mode": discovery_mode,
        "seed_urls": catalog.get("catalog_urls", [])[:5] or [final_url],
        "section_keywords": section_kw,
        "price_regex": price.get("regex", ""),
        "duration_regex": "",
        "exclusion_patterns": exclusion,
        "allowed_url_patterns": [],
        "field_defaults": {},
        "requires_stealth": template.get("requires_stealth", False),
        "requires_cloudflare_bypass": template.get("requires_cloudflare_bypass", False),
        "catalog_link_selector": template.get("catalog_link_selector"),
        "catalog_scroll_iterations": template.get("catalog_scroll_iterations"),
        "detail_wait_ms": template.get("detail_wait_ms", 2000),
        "pipeline_ready": False,
        "auto_generated": True,
    }

    confidence = {
        "site_type": "high" if cms["cms"] != "html_puro" else "medium",
        "discovery_mode": "high" if sitemap["found"] else "medium",
        "price_present": bool(price),
        "sitemap_found": sitemap["found"],
        "js_required": js["needs_js"],
        "template_match": cms["cms"],
        "needs_manual_review": [],
    }

    if not price and cms["cms"] not in ("woocommerce",):
        confidence["needs_manual_review"].append("price_regex")
    if discovery_mode == "hardcoded_urls":
        confidence["needs_manual_review"].append("discovery_mode")
    if cms["cms"] == "html_puro":
        confidence["needs_manual_review"].append("site_type")

    return {
        "institution_metadata": meta,
        "institution_site_profile": profile,
        "raw_diagnostics": {
            "cms": cms,
            "sitemap": sitemap,
            "json_ld_keys": list(ld.keys()),
            "price": price,
            "dates": dates,
            "headings_count": len(headings),
            "catalog_count": len(catalog.get("catalog_urls", [])),
            "js_required": js,
        },
        "_confidence": confidence,
    }
