#!/usr/bin/env python3
"""Validate Obsidian wikilinks and orphan notes under .context."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


def _build_index(root: Path) -> tuple[dict[str, Path], dict[str, list[Path]]]:
    by_relative: dict[str, Path] = {}
    by_stem: dict[str, list[Path]] = {}
    for path in root.rglob("*.md"):
        if ".obsidian" in path.parts:
            continue
        relative_key = path.relative_to(root).with_suffix("").as_posix()
        by_relative[relative_key] = path
        by_stem.setdefault(path.stem, []).append(path)
    return by_relative, by_stem


def _is_inside_root(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _resolve_link(
    source: Path,
    target: str,
    root: Path,
    by_relative: dict[str, Path],
    by_stem: dict[str, list[Path]],
) -> Path | None:
    target = target.split("|", 1)[0].split("#", 1)[0].strip()
    if not target or "XXX" in target:
        return None
    if target.startswith("."):
        candidate = (source.parent / target).resolve()
        return next(
            (path for path in (candidate, candidate.with_suffix(".md")) if path.exists() and _is_inside_root(path, root)),
            None,
        )
    normalized = target[:-3] if target.endswith(".md") else target
    if normalized in by_relative:
        return by_relative[normalized]
    candidates = by_stem.get(Path(normalized).name, [])
    return candidates[0] if len(candidates) == 1 else None


def validate_context_graph(root: Path) -> tuple[list[str], list[str]]:
    root = root.resolve()
    by_relative, by_stem = _build_index(root)
    graph = {path: set() for path in by_relative.values()}
    missing: list[str] = []
    for source in sorted(by_relative.values()):
        for raw_target in WIKILINK_RE.findall(source.read_text(encoding="utf-8")):
            if "XXX" in raw_target:
                continue
            resolved = _resolve_link(source, raw_target, root, by_relative, by_stem)
            if resolved is None:
                rel_source = source.relative_to(root).as_posix()
                missing.append(f"{rel_source}: [[{raw_target}]]")
                continue
            if resolved != source:
                graph.setdefault(source, set()).add(resolved)

    root_index = root / "00_INDICE.md"
    reachable: set[Path] = set()
    pending = [root_index] if root_index.exists() else []
    while pending:
        current = pending.pop()
        if current in reachable:
            continue
        reachable.add(current)
        pending.extend(graph.get(current, set()) - reachable)

    orphans: list[str] = []
    for path in sorted(by_relative.values(), key=lambda item: item.as_posix()):
        relative = path.relative_to(root).as_posix()
        if path not in reachable and relative != "00_INDICE.md" and "_plantilla" not in relative:
            orphans.append(relative)
    return missing, orphans


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate .context Obsidian graph links")
    parser.add_argument("root", nargs="?", default=".context", help="Context vault root")
    args = parser.parse_args()
    root = Path(args.root)
    if not root.exists():
        print(f"Context root not found: {root}", file=sys.stderr)
        return 2
    missing, orphans = validate_context_graph(root)
    if missing:
        print("Missing or ambiguous wikilinks:")
        for item in missing:
            print(f"- {item}")
    if orphans:
        print("Markdown files without backlinks:")
        for item in orphans:
            print(f"- {item}")
    if missing or orphans:
        return 1
    print("Context graph validation OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
