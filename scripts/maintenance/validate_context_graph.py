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
    "backlog_tareas/_README.md",
    "backlog_tareas/_plantilla_tarea.md",
    "backlog_tareas/intake/INTAKE-002.md",
    "backlog_tareas/req_est_001_sprint_1/_index.md",
    "backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md",
    "hitos/hito_001.md",
    "decisiones/_index.md",
    "decisiones/_plantilla_adr.md",
    "decisiones/ADR-0001_autoridad_fuentes_context_graph.md",
    "decisiones/ADR-0002_ciclo_requerimientos_privados.md",
    "estimaciones/est_001.md",
    "operaciones/flujo_requerimientos.md",
    "operaciones/flujo_release_minimo.md",
    "operaciones/matriz_adopcion_db.md",
    "operaciones/reconciliacion_db_as_code_f6.md",
    "changelog/_plantilla_changelog.md",
    "changelog/2026-07-24.md",
    "changelog/2026-07-25.md",
)

WIKILINK_RE = re.compile(r"(?<!!)\[\[([^\[\]\n]+)\]\]")
MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^\]\n]*\]\(([^)\n]+)\)")
FENCED_CODE_RE = re.compile(r"```.*?```|~~~.*?~~~", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
WINDOWS_ABSOLUTE_RE = re.compile(r"^[A-Za-z]:[/\\]")
ALLOWED_EXTERNAL_SCHEMES = {"http", "https", "mailto"}
CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
MAX_FILES = 250
MAX_FILE_BYTES = 1_000_000
MAX_TOTAL_BYTES = 5_000_000
IGNORED_PREFIXES = (".obsidian/", "attachments/private/", "artifacts/private/")


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


def safe_label(value: str) -> str:
    return CONTROL_RE.sub("?", value)[:200]


def case_hint(target: str, files: set[str]) -> str:
    has_match = any(path.casefold() == target.casefold() for path in files)
    return "; case-sensitive candidate exists" if has_match else ""


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
        return set(), f"{safe_label(source)}: absolute Markdown link is not allowed"

    parsed = urlsplit(destination)
    if parsed.scheme or parsed.netloc:
        if parsed.scheme.lower() not in ALLOWED_EXTERNAL_SCHEMES:
            return set(), f"{safe_label(source)}: unsupported URL scheme"
        return set(), None

    path = parsed.path
    if not path:
        return set(), None
    target, error = normalize_local(source, path)
    if error:
        return set(), f"{safe_label(source)}: {error}"
    if not path.lower().endswith(".md"):
        return set(), None

    if target not in files:
        return set(), f"{safe_label(source)}: missing Markdown target{case_hint(target, files)}"
    return {target}, None


def resolve_wikilink(
    source: str, raw: str, files: set[str]
) -> tuple[set[str], str | None]:
    destination = raw.split("|", 1)[0].split("#", 1)[0].strip()
    if not destination:
        return set(), None

    destination = unquote(destination).replace("\\", "/")
    if destination.startswith(("/", "//")) or WINDOWS_ABSOLUTE_RE.match(destination):
        return set(), f"{safe_label(source)}: absolute wikilink is not allowed"
    if not destination.lower().endswith(".md"):
        destination += ".md"

    if "/" not in destination:
        candidates = sorted(path for path in files if PurePosixPath(path).name == destination)
        if not candidates:
            has_folded = any(
                PurePosixPath(path).name.casefold() == destination.casefold()
                for path in files
            )
            hint = "; case-sensitive candidate exists" if has_folded else ""
            return set(), f"{safe_label(source)}: missing wikilink target{hint}"
    else:
        relative, error = normalize_local(source, destination)
        if error:
            return set(), f"{safe_label(source)}: {error}"
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
            return set(), f"{safe_label(source)}: missing wikilink target{hint}"

    if len(candidates) > 1:
        return set(), f"{safe_label(source)}: ambiguous wikilink"
    return {candidates[0]}, None


def main() -> int:
    issues: set[str] = set()
    if not ROOT.is_dir():
        print("CONTEXT_GRAPH: FAIL")
        print("- missing context root")
        return 1

    files: set[str] = set()
    root_resolved = ROOT.resolve()
    try:
        discovered_paths = sorted(ROOT.rglob("*.md"))
    except OSError:
        print("CONTEXT_GRAPH: FAIL")
        print("- unable to enumerate context notes")
        return 1

    markdown_paths = [
        path
        for path in discovered_paths
        if not path.relative_to(ROOT).as_posix().startswith(IGNORED_PREFIXES)
    ]

    if len(markdown_paths) > MAX_FILES:
        print("CONTEXT_GRAPH: FAIL")
        print(f"- too many Markdown notes: limit is {MAX_FILES}")
        return 1

    for path in markdown_paths:
        relative = path.relative_to(ROOT).as_posix()
        if path.is_symlink():
            issues.add(f"{safe_label(relative)}: symlink note is not allowed")
            continue
        if not path.is_file():
            continue
        try:
            path.resolve().relative_to(root_resolved)
        except (OSError, RuntimeError, ValueError):
            issues.add(f"{safe_label(relative)}: note path is invalid")
            continue
        files.add(relative)
    for required in REQUIRED:
        if required not in files:
            issues.add(f"missing required file: {required}")

    graph: dict[str, set[str]] = {path: set() for path in files}
    link_count = 0
    total_bytes = 0
    for source in sorted(files):
        source_path = ROOT / PurePosixPath(source)
        try:
            file_bytes = source_path.stat().st_size
        except OSError:
            issues.add(f"{safe_label(source)}: unable to stat note")
            continue
        if file_bytes > MAX_FILE_BYTES:
            issues.add(f"{safe_label(source)}: note exceeds size limit")
            continue
        total_bytes += file_bytes
        if total_bytes > MAX_TOTAL_BYTES:
            issues.add("context notes exceed total size limit")
            continue
        try:
            text = without_code(source_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError):
            issues.add(f"{safe_label(source)}: unable to read UTF-8 note")
            continue
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
        issues.add(f"{safe_label(path)}: unreachable from {ENTRYPOINT}")

    if issues:
        print("CONTEXT_GRAPH: FAIL")
        for issue in sorted(issues):
            print(f"- {issue}")
        return 1

    print(f"CONTEXT_GRAPH: PASS ({len(files)} files, {link_count} links)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
