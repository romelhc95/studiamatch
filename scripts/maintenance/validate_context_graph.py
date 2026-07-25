#!/usr/bin/env python3
"""Validate required files and local links in the minimal context graph."""

from __future__ import annotations

import posixpath
import re
import sys
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[2] / ".context"
ENTRYPOINT = "00_INDICE.md"
REQUIRED = (
    "00_INDICE.md",
    "prompts/system_prompt_base.md",
    "sistema_db_supabase.md",
    "arquitectura_pipeline.md",
    "estructura_frontend.md",
    "estado_del_proyecto.md",
    "backlog_tareas/req_est_001_sprint_1/_index.md",
    "backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md",
    "estimaciones/est_001.md",
    "operaciones/flujo_release_minimo.md",
    "operaciones/matriz_adopcion_db.md",
    "changelog/2026-07-24.md",
)

WIKILINK_RE = re.compile(r"(?<!!)\[\[([^\[\]\n]+)\]\]")
MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^\]\n]*\]\(([^)\n]+)\)")
FENCED_CODE_RE = re.compile(r"```.*?```|~~~.*?~~~", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
WINDOWS_ABSOLUTE_RE = re.compile(r"^[A-Za-z]:[/\\]")
ALLOWED_EXTERNAL_SCHEMES = {"http", "https", "mailto"}


def without_code(text: str) -> str:
    return INLINE_CODE_RE.sub("", FENCED_CODE_RE.sub("", text))


def normalize_local(source: str, target: str) -> tuple[str | None, str | None]:
    target = unquote(target.strip()).replace("\\", "/")
    if target.startswith(("/", "//")) or WINDOWS_ABSOLUTE_RE.match(target):
        return None, "absolute path"

    base = PurePosixPath(source).parent.as_posix()
    joined = posixpath.normpath(posixpath.join(base, target))
    if joined == ".." or joined.startswith("../"):
        return None, "path escapes .context"
    return joined.removeprefix("./"), None


def case_hint(target: str, files: set[str]) -> str:
    matches = sorted(path for path in files if path.casefold() == target.casefold())
    return f"; case-sensitive match: {', '.join(matches)}" if matches else ""


def resolve_markdown_link(
    source: str, raw: str, files: set[str]
) -> tuple[set[str], str | None]:
    destination = raw.strip()
    if destination.startswith("<") and ">" in destination:
        destination = destination[1 : destination.index(">")]
    else:
        destination = destination.split(maxsplit=1)[0] if destination else ""

    if not destination or destination.startswith("#"):
        return set(), None

    local_form = unquote(destination).replace("\\", "/")
    if local_form.startswith(("/", "//")) or WINDOWS_ABSOLUTE_RE.match(local_form):
        return set(), f"{source}: absolute Markdown link is not allowed: {destination}"

    parsed = urlsplit(destination)
    if parsed.scheme or parsed.netloc:
        if parsed.scheme.lower() not in ALLOWED_EXTERNAL_SCHEMES:
            return set(), f"{source}: unsupported URL scheme: {destination}"
        return set(), None

    path = parsed.path
    if not path:
        return set(), None
    target, error = normalize_local(source, path)
    if error:
        return set(), f"{source}: {error}: {destination}"
    if not path.lower().endswith(".md"):
        return set(), None

    if target not in files:
        return set(), f"{source}: missing target: {target}{case_hint(target, files)}"
    return {target}, None


def resolve_wikilink(
    source: str, raw: str, files: set[str]
) -> tuple[set[str], str | None]:
    destination = raw.split("|", 1)[0].split("#", 1)[0].strip()
    if not destination:
        return set(), None

    destination = unquote(destination).replace("\\", "/")
    if destination.startswith(("/", "//")) or WINDOWS_ABSOLUTE_RE.match(destination):
        return set(), f"{source}: absolute wikilink is not allowed: {destination}"
    if not destination.lower().endswith(".md"):
        destination += ".md"

    if "/" not in destination:
        candidates = sorted(path for path in files if PurePosixPath(path).name == destination)
        if not candidates:
            folded = sorted(
                path
                for path in files
                if PurePosixPath(path).name.casefold() == destination.casefold()
            )
            hint = f"; case-sensitive match: {', '.join(folded)}" if folded else ""
            return set(), f"{source}: missing wikilink target: {destination}{hint}"
    else:
        relative, error = normalize_local(source, destination)
        if error:
            return set(), f"{source}: {error}: {destination}"
        root_relative = posixpath.normpath(destination).removeprefix("./")
        if root_relative == ".." or root_relative.startswith("../"):
            root_relative = ""
        candidates = sorted(
            candidate
            for candidate in {relative, root_relative}
            if candidate and candidate in files
        )
        if not candidates:
            hint = case_hint(relative, files)
            return set(), f"{source}: missing wikilink target: {destination}{hint}"

    if len(candidates) > 1:
        return set(), f"{source}: ambiguous wikilink {destination}: {', '.join(candidates)}"
    return {candidates[0]}, None


def main() -> int:
    issues: set[str] = set()
    if not ROOT.is_dir():
        print("CONTEXT_GRAPH: FAIL")
        print(f"- missing root: {ROOT}")
        return 1

    files: set[str] = set()
    root_resolved = ROOT.resolve()
    for path in sorted(ROOT.rglob("*.md")):
        relative = path.relative_to(ROOT).as_posix()
        if path.is_symlink():
            issues.add(f"symlink note is not allowed: {relative}")
            continue
        if not path.is_file():
            continue
        try:
            path.resolve().relative_to(root_resolved)
        except ValueError:
            issues.add(f"note resolves outside .context: {relative}")
            continue
        files.add(relative)
    for required in REQUIRED:
        if required not in files:
            issues.add(f"missing required file: {required}")

    graph: dict[str, set[str]] = {path: set() for path in files}
    link_count = 0
    for source in sorted(files):
        text = without_code((ROOT / PurePosixPath(source)).read_text(encoding="utf-8"))
        for raw in WIKILINK_RE.findall(text):
            targets, error = resolve_wikilink(source, raw, files)
            if error:
                issues.add(error)
            graph[source].update(targets)
            link_count += 1
        for raw in MARKDOWN_LINK_RE.findall(text):
            targets, error = resolve_markdown_link(source, raw, files)
            if error:
                issues.add(error)
            graph[source].update(targets)
            link_count += 1

    reachable: set[str] = set()
    pending = [ENTRYPOINT] if ENTRYPOINT in files else []
    while pending:
        current = pending.pop()
        if current in reachable:
            continue
        reachable.add(current)
        pending.extend(sorted(graph[current] - reachable, reverse=True))

    for path in sorted(files - reachable):
        issues.add(f"unreachable from {ENTRYPOINT}: {path}")

    if issues:
        print("CONTEXT_GRAPH: FAIL")
        for issue in sorted(issues):
            print(f"- {issue}")
        return 1

    print(f"CONTEXT_GRAPH: PASS ({len(files)} files, {link_count} links)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
