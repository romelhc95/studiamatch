#!/usr/bin/env python3
"""Offline helper to inspect temporary URL interest artifacts.

This script only prints candidate patterns. Persist reviewed configuration through
versioned SQL migrations in `db/migrations/`; workers must not depend on these
artifact files at runtime.
"""

from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = ROOT / "artifacts" / "urls_interes"

NOISE_SEGMENTS = {
    "blog",
    "blogs",
    "cart",
    "categoria-producto",
    "categoria-termino-y-condicion",
    "checkout",
    "egresado",
    "etiqueta-producto",
    "facultad",
    "facultades",
    "legales",
    "mi-cuenta",
    "noticias",
    "profesores",
    "termino-y-condicion",
}


def load_urls(slug: str) -> list[str]:
    if not re.fullmatch(r"[a-z0-9_-]+", slug):
        raise ValueError("Slug invalido. Usa solo minusculas, numeros, guion y guion bajo.")

    path = ARTIFACT_DIR / f"{slug}.txt"
    resolved = path.resolve()
    if ARTIFACT_DIR.resolve() not in resolved.parents:
        raise ValueError("Ruta fuera de artifacts/urls_interes")
    if not resolved.exists():
        raise FileNotFoundError(f"No existe {path}")
    if resolved.stat().st_size > 1_000_000:
        raise ValueError("Archivo demasiado grande para analisis offline")

    urls: list[str] = []
    for line in resolved.read_text(encoding="utf-8").splitlines():
        value = line.strip()
        parsed = urlparse(value)
        if parsed.scheme in {"http", "https"} and parsed.netloc:
            urls.append(value)
    return urls


def path_family(url: str) -> str:
    parsed = urlparse(url)
    segments = [segment for segment in parsed.path.strip("/").split("/") if segment]
    if not segments:
        return "/"
    if len(segments) == 1:
        return f"/{segments[0]}/<slug>"
    return "/" + "/".join(segments[:-1]) + "/<slug>"


def is_noise_family(family: str) -> bool:
    normalized = family.lower()
    return any(segment in normalized for segment in NOISE_SEGMENTS)


def regex_for_family(family: str) -> str:
    if family == "/":
        return r"re:^/$"
    escaped = re.escape(family).replace(re.escape("<slug>"), r"[^\/]+")
    return f"re:^https?://[^/]+{escaped}/?$"


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze artifacts/urls_interes/<slug>.txt offline")
    parser.add_argument("slug", help="Institution slug, e.g. dmc, ulima, idat")
    args = parser.parse_args()

    urls = load_urls(args.slug)
    families = Counter(path_family(url) for url in urls)
    allowed = [family for family, _ in families.most_common() if not is_noise_family(family)]
    excluded = [family for family, _ in families.most_common() if is_noise_family(family)]

    print(f"URLs: {len(urls)}")
    print("\nFamilias detectadas:")
    for family, count in families.most_common():
        label = "exclude" if is_noise_family(family) else "review"
        print(f"- {family} ({count}) [{label}]")

    print("\nCandidatos allowed_url_patterns:")
    for family in allowed:
        print(f"- {regex_for_family(family)}")

    print("\nCandidatos exclusion_patterns:")
    for family in excluded:
        print(f"- {regex_for_family(family)}")

    print("\nSiguiente paso: revisar manualmente y persistir en db/migrations/*.sql")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
