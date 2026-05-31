#!/usr/bin/env python3
"""Fase 119: Diagnostico pre-onboarding para instituciones nuevas.

Dada 1 URL de muestra, visita la pagina en modo read-only y genera
un borrador de institution_site_profiles listo para revision humana.

Uso:
    python3 scripts/maintenance/diagnose_institution.py https://www.ejemplo.pe/curso/data-engineer
"""

import json
import os
import sys
import time
from urllib.parse import urlparse

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.site_diagnostics import (
    _get,
    detect_cms,
    detect_sitemap,
    detect_json_ld,
    detect_price_patterns,
    detect_date_texts,
    detect_section_headings,
    detect_catalog_links,
    detect_noise_patterns,
    detect_js_required,
    detect_institution_metadata,
    suggest_site_type,
    suggest_discovery_mode,
    build_section_keywords,
    build_exclusion_patterns,
    NOISE_PATH_PATTERNS,
)


def diagnose(url: str) -> dict:
    print(f"\n  Diagnosticando {url} ...")
    t0 = time.time()

    status, html, final_url = _get(url)
    if not html:
        return {"error": f"No se pudo obtener la pagina (status={status})", "url": url}

    print(f"  HTTP {status} ({len(html)} bytes, {time.time() - t0:.1f}s)")

    cms = detect_cms(html)
    sitemap = detect_sitemap(final_url)
    ld = detect_json_ld(html)
    price = detect_price_patterns(html)
    dates = detect_date_texts(html)
    headings = detect_section_headings(html)
    catalog = detect_catalog_links(html, final_url)
    js = detect_js_required(html)
    meta = detect_institution_metadata(html, final_url)

    parsed = urlparse(final_url)
    noise = []
    path = parsed.path.lower()
    for pattern in NOISE_PATH_PATTERNS:
        if pattern in path:
            noise.append(pattern)

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
        "requires_stealth": cms["cms"] == "woocommerce",
        "requires_cloudflare_bypass": False,
        "pipeline_ready": False,
    }

    confidence = {
        "site_type": "high" if cms["cms"] != "html_puro" else "medium",
        "discovery_mode": "high" if sitemap["found"] else "medium",
        "price_present": bool(price),
        "price_format_detected": f"{price.get('currency', 'N/A')} {price.get('prices_found', [])[:3]}" if price else None,
        "start_date_present": bool(dates),
        "sitemap_found": sitemap["found"],
        "js_required": js["needs_js"],
        "template_match": cms["cms"],
        "needs_manual_review": [],
    }

    if not price and cms["cms"] not in ("woocommerce",):
        confidence["needs_manual_review"].append("price_regex (no se detecto precio)")
    if discovery_mode == "hardcoded_urls":
        confidence["needs_manual_review"].append("discovery_mode (sin sitemap ni catalogo)")
    if cms["cms"] == "html_puro":
        confidence["needs_manual_review"].append("site_type (CMS desconocido)")

    return {
        "institution": {
            "name": meta["og_site_name"] or meta["domain"],
            "slug": meta["suggested_slug"],
            "website_url": f"{parsed.scheme}://{meta['domain']}",
            "sample_url": url,
            "final_url": final_url,
        },
        "institution_site_profile": profile,
        "_confidence": confidence,
        "_elapsed_s": round(time.time() - t0, 2),
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 scripts/maintenance/diagnose_institution.py <URL>")
        sys.exit(1)

    result = diagnose(sys.argv[1])
    print(json.dumps(result, indent=2, ensure_ascii=False))
