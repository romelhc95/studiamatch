#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote


SHA_RE = re.compile(r"^[0-9a-f]{40}$")

CERT_BASE = "2a70dd001d8ded34d5ba67c19221f7f5e291d2c8"
MAIN_SOURCE = "ad89e8ab9575b37476502d6062e22c044ad6447b"
MAIN_SOURCE_TREE = "54098b3ff581cc7728979afc8e6d47c9535141b5"
CERT_ANCHOR = "f8695f2463f5f8bf2d887bdd344f7f102afc13cd"

DEV_BASE = "8f4b4b0cbd8fd8ed096a34d8fa826f39ba6ec3fc"
DEV_ARCHIVE_REF = "refs/remotes/origin/archive/f10-9-ca2-preserve-desarrollo-20260809"
DEV_ARCHIVE_TREE = "13d3926f21b65abc73d1e8ef6e4305b2d61e0c77"
DEV_EXTRACTION = "2c83cde5bc6e04f01c595a629e5694bd6de3e286"
P1_HEAD_REF = "fix/f10-9-p1-rebuilt"

CONTEXT_EXPECTED_BLOBS = {
    ".context/00_INDICE.md": "0f05d40caa1b78f62f236c6200c04b178c3fb177",
    ".context/arquitectura_pipeline.md": "88f2e44d409ccd61203147d3db50634057d6c60c",
    ".context/backlog_tareas/req_est_001_sprint_1/_index.md": "1d15276b5692e08ae6aad8edcc3800fca217a712",
    ".context/backlog_tareas/req_est_001_sprint_1/adenda_cliente_001_sanitizada.md": "c7d1d25c2dcaff656fabb46fde369f219d24bdb5",
    ".context/backlog_tareas/req_est_001_sprint_1/backlog_f9_5_known_findings.md": "f197a2e2da4afdbf283b3e35d14c5c44536f74aa",
    ".context/backlog_tareas/req_est_001_sprint_1/backlog_seguridad_leads_email.md": "e7cb201edfee6194d2062835636034dd7c5a2544",
    ".context/backlog_tareas/req_est_001_sprint_1/seguimiento_detallado_hito_1.md": "361b0e821d63c678bb4062df25dea5ce266b30ec",
    ".context/decisiones/ADR-0003_taxonomia_macrofases_subfases.md": "b8b5d49c0eb9338b6bfe9849f21f4e01546b1304",
    ".context/decisiones/ADR-0004_simplificacion_contractual_hito1.md": "4854f63e3b4a1bcb93fac61a9859fd253f4db3a2",
    ".context/decisiones/ADR-0005_corte_seguridad_funcionalidad_estabilidad_hito1.md": "26ca8bcaea61229dcce829a8f4586c4bbbfde10e",
    ".context/decisiones/ADR-0007_desviacion_canary_certification_f9_9.md": "e466a172ee761eec555259a506bdb042dafd339b",
    ".context/decisiones/ADR-0008_rebaseline_f10_7_gate_reconstruction.md": "45f60e0bd3e2ef4ec3f2ba580bdf99759011dfc5",
    ".context/decisiones/ADR-0009_reconciliacion_entrega_tecnica_post_main_f10_7.md": "bd6f0fdfcbb5b4ddfd5feb2c3e34bf77756dc628",
    ".context/estimaciones/est_001.md": "13f91a8e5d8d692342d05ec14deffac613ca391a",
    ".context/operaciones/matriz_adopcion_db.md": "d2f89c062bd08e3cf99117b3518c6a673967b06f",
    ".context/operaciones/plan_corte_seguridad_funcionalidad_estabilidad_hito1.md": "f7421172969e819912b5b89dddffbd539bd32d21",
    ".context/operaciones/plan_simplificado_hito1.md": "4549a0316f24fec55200e9b651d4fc0f9986d794",
    ".context/operaciones/pr_o_f9_7_successor_private_executor.md": "31e098b5c94daae9f2162f7ef33de8e10c333c87",
    ".context/operaciones/pr_o_f9_7_v3_hold.md": "b032f5f871a611c7229f02ea8ba84048013d6e58",
    ".context/operaciones/precertificacion_hito1_f9.md": "61cc2425daeb961837004a8344ec98e09e6067ed",
    ".context/operaciones/preflight_free_f9_4.md": "fbdcbe77349ab6e071a15ba0048e01788b8262bd",
    ".context/operaciones/preflight_free_f9_5.md": "2b209a41fc97f8c53504054229b6a8df76ef143a",
    ".context/operaciones/promocion_hito1_f10.md": "fe8167eb168e929e510300228962d2cec8b41e9c",
    ".context/operaciones/qa_desviacion_f9_9.md": "aa7f2a886818fe4ee91cde71baee136f07f35ad0",
    ".context/operaciones/qa_desviacion_f9_9_resultado.md": "c4de82a9395e04fdb00d0d75cb1cc642bdaa50c3",
    ".context/sistema_db_supabase.md": "5573d16c193d3f07e8e3a7a10088b77a4b649a3c",
}

CONTEXT_FORBIDDEN_PATHS = {
    ".context/backlog_tareas/req_est_001_sprint_1/tarea_002_hito_2.md",
    ".context/backlog_tareas/req_est_001_sprint_1/tarea_004_hito_4.md",
    ".context/evidencias_cliente/sprint_1/anexo_h1_ca2_seguridad_rls.md",
    ".context/operaciones/certificacion_hito1_f9.md",
    ".context/operaciones/cierre_definitivo_f9_7.md",
    ".context/operaciones/gate_b_f9_7.md",
    ".context/operaciones/reconciliacion_db_as_code_f6.md",
    ".context/operaciones/remediacion_gate_b_f9_7.md",
    ".context/operaciones/remediacion_trigger_f9_7.md",
}

CERT_ALLOWED_STATUSES = {
    ".context/00_INDICE.md": "A",
    ".context/arquitectura_pipeline.md": "A",
    ".context/backlog_tareas/req_est_001_sprint_1/_index.md": "A",
    ".context/backlog_tareas/req_est_001_sprint_1/adenda_cliente_001_sanitizada.md": "A",
    ".context/backlog_tareas/req_est_001_sprint_1/backlog_f9_5_known_findings.md": "A",
    ".context/backlog_tareas/req_est_001_sprint_1/backlog_seguridad_leads_email.md": "A",
    ".context/backlog_tareas/req_est_001_sprint_1/seguimiento_detallado_hito_1.md": "A",
    ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
    ".context/decisiones/ADR-0003_taxonomia_macrofases_subfases.md": "A",
    ".context/decisiones/ADR-0004_simplificacion_contractual_hito1.md": "A",
    ".context/decisiones/ADR-0005_corte_seguridad_funcionalidad_estabilidad_hito1.md": "A",
    ".context/decisiones/ADR-0007_desviacion_canary_certification_f9_9.md": "A",
    ".context/decisiones/ADR-0008_rebaseline_f10_7_gate_reconstruction.md": "A",
    ".context/decisiones/ADR-0009_reconciliacion_entrega_tecnica_post_main_f10_7.md": "A",
    ".context/estado_del_proyecto.md": "M",
    ".context/estimaciones/est_001.md": "A",
    ".context/evidencias_cliente/sprint_1/paquete_hito_001.md": "M",
    ".context/operaciones/g0_r0_reconciliacion_f10_9.md": "A",
    ".context/operaciones/matriz_adopcion_db.md": "A",
    ".context/operaciones/plan_corte_seguridad_funcionalidad_estabilidad_hito1.md": "A",
    ".context/operaciones/plan_remediacion_f10_9_fg2_fg3.md": "M",
    ".context/operaciones/plan_simplificado_hito1.md": "A",
    ".context/operaciones/pr_o_f9_7_successor_private_executor.md": "A",
    ".context/operaciones/pr_o_f9_7_v3_hold.md": "A",
    ".context/operaciones/precertificacion_hito1_f9.md": "A",
    ".context/operaciones/preflight_free_f9_4.md": "A",
    ".context/operaciones/preflight_free_f9_5.md": "A",
    ".context/operaciones/promocion_hito1_f10.md": "A",
    ".context/operaciones/qa_desviacion_f9_9.md": "A",
    ".context/operaciones/qa_desviacion_f9_9_resultado.md": "A",
    ".context/operaciones/r0_ci_boundary_manifest_2026_08_09.md": "A",
    ".context/operaciones/r0_context_graph_manifest_2026_08_09.md": "A",
    ".context/operaciones/r0_freeze_f10_9_2026_08_09.md": "A",
    ".context/sistema_db_supabase.md": "A",
    ".github/workflows/f9-7-contract.yml": "M",
    ".github/workflows/opencode.yml": "M",
    ".github/workflows/security-audit.yml": "M",
    "scripts/security/f109_boundary.py": "A",
    "tests/test_fase10_9_branch_reconciliation.py": "A",
    "tests/test_fase10_main_boundary.py": "M",
}

P1_ALLOWED_STATUSES = {
    "scripts/shared/db_client.py": "M",
    "scripts/shared/safe_http.py": "A",
    "scripts/shared/url_identity.py": "A",
    "scripts/shared/utils.py": "M",
    "tests/test_fase10_9_p1_safety_contracts.py": "A",
}


class BoundaryError(RuntimeError):
    pass


def git(repo: Path, *args: str, text: bool = True) -> str | bytes:
    return subprocess.check_output(
        ["git", "-C", str(repo), *args],
        text=text,
    )


def require(condition: bool, message: str) -> None:
    if not condition:
        raise BoundaryError(message)


def require_sha(repo: Path, name: str, value: str) -> None:
    require(bool(SHA_RE.fullmatch(value)), f"{name} must be a full SHA")
    subprocess.run(
        ["git", "-C", str(repo), "cat-file", "-e", f"{value}^{{commit}}"],
        check=True,
    )


def commit_tree(repo: Path, commit: str) -> str:
    return str(git(repo, "rev-parse", f"{commit}^{{tree}}")).strip()


def commit_parents(repo: Path, commit: str) -> list[str]:
    fields = str(git(repo, "rev-list", "--parents", "-n", "1", commit)).split()
    return fields[1:]


def is_ancestor(repo: Path, ancestor: str, descendant: str) -> bool:
    result = subprocess.run(
        ["git", "-C", str(repo), "merge-base", "--is-ancestor", ancestor, descendant],
        check=False,
    )
    return result.returncode == 0


def changed_statuses(repo: Path, base: str, head: str) -> dict[str, str]:
    raw = bytes(
        git(
            repo,
            "diff",
            "--name-status",
            "-z",
            "--no-renames",
            base,
            head,
            "--",
            text=False,
        )
    )
    fields = raw.split(b"\0")
    result: dict[str, str] = {}
    index = 0
    while index < len(fields) and fields[index]:
        status = fields[index].decode("ascii")
        path = fields[index + 1].decode("utf-8", "surrogateescape")
        require(status in {"A", "M", "D"}, f"unsupported diff status {status}:{path}")
        require(path not in result, f"duplicate diff path {path}")
        result[path] = status
        index += 2
    return result


def require_exact_delta(
    repo: Path,
    base: str,
    head: str,
    expected: dict[str, str],
) -> None:
    actual = changed_statuses(repo, base, head)
    require(actual == expected, f"delta mismatch: expected={expected!r} actual={actual!r}")
    for path, status in actual.items():
        if status == "D":
            continue
        metadata = str(git(repo, "ls-tree", head, "--", path)).strip().split(None, 3)
        require(len(metadata) == 4, f"missing tree metadata for {path}")
        mode, kind, _blob, tree_path = metadata
        require((mode, kind, tree_path) == ("100644", "blob", path), f"invalid tree entry {path}")


def validate_context_graph(
    root: Path,
    expected_files: int,
    expected_links: int,
    expected_blobs: dict[str, str] | None = None,
    forbidden_paths: set[str] | None = None,
) -> None:
    root = root.resolve()
    markdown_files = sorted((root / ".context").rglob("*.md"))
    pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    local_links = 0
    broken: list[tuple[str, str]] = []
    for path in markdown_files:
        for target in pattern.findall(path.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            clean_target = target.split("#", 1)[0]
            if not clean_target:
                continue
            local_links += 1
            resolved = (path.parent / unquote(clean_target)).resolve()
            require(resolved == root or root in resolved.parents, f"context link escapes repository: {target}")
            if not resolved.exists():
                broken.append((path.relative_to(root).as_posix(), target))
    require(len(markdown_files) == expected_files, f"unexpected markdown count {len(markdown_files)}")
    require(local_links == expected_links, f"unexpected local link count {local_links}")
    require(not broken, f"broken context links: {broken!r}")
    for relative in forbidden_paths or set():
        require(not (root / relative).exists(), f"forbidden CA2 context path present: {relative}")
    for relative, expected_blob in (expected_blobs or {}).items():
        path = root / relative
        require(path.is_file(), f"missing reconciled context path: {relative}")
        actual_blob = str(git(root, "hash-object", relative)).strip()
        require(actual_blob == expected_blob, f"reconciled context blob drift: {relative}")


def validate_cert(repo: Path, base: str, head: str, event: str) -> None:
    require(base == CERT_BASE, "unexpected certification baseline")
    require_sha(repo, "CERT_BASE", base)
    require_sha(repo, "MAIN_SOURCE", MAIN_SOURCE)
    require_sha(repo, "CERT_ANCHOR", CERT_ANCHOR)
    require_sha(repo, "head", head)
    require(commit_tree(repo, MAIN_SOURCE) == MAIN_SOURCE_TREE, "main source tree drift")
    require(commit_parents(repo, CERT_ANCHOR) == [CERT_BASE, MAIN_SOURCE], "cert anchor parents drift")
    require(commit_tree(repo, CERT_ANCHOR) == MAIN_SOURCE_TREE, "cert anchor tree drift")
    require(is_ancestor(repo, CERT_ANCHOR, head), "cert anchor is not an ancestor of head")
    if event == "push":
        require(commit_parents(repo, head)[0] == base, "certification push first parent drift")
    require_exact_delta(repo, CERT_ANCHOR, head, CERT_ALLOWED_STATUSES)
    validate_context_graph(
        repo,
        expected_files=41,
        expected_links=340,
        expected_blobs=CONTEXT_EXPECTED_BLOBS,
        forbidden_paths=CONTEXT_FORBIDDEN_PATHS,
    )


def validate_dev(repo: Path, base: str, head: str, event: str, cert_tip: str) -> None:
    require(base == DEV_BASE, "unexpected desarrollo reconciliation baseline")
    for name, value in {
        "DEV_BASE": base,
        "DEV_EXTRACTION": DEV_EXTRACTION,
        "cert_tip": cert_tip,
        "head": head,
    }.items():
        require_sha(repo, name, value)
    archive_commit = str(git(repo, "rev-parse", DEV_ARCHIVE_REF)).strip()
    require(archive_commit == DEV_BASE, "CA2 archive commit drift")
    require(commit_tree(repo, archive_commit) == DEV_ARCHIVE_TREE, "CA2 archive tree drift")
    require(commit_parents(repo, DEV_EXTRACTION) == [DEV_BASE], "extraction parent drift")
    require(commit_tree(repo, DEV_EXTRACTION) == MAIN_SOURCE_TREE, "extraction tree drift")
    require(is_ancestor(repo, DEV_EXTRACTION, head), "extraction is not an ancestor of head")
    require(is_ancestor(repo, cert_tip, head), "protected certificacion tip is not an ancestor")
    require(commit_tree(repo, head) == commit_tree(repo, cert_tip), "desarrollo tree differs from certificacion")
    first_parent_chain = str(
        git(repo, "rev-list", "--reverse", "--first-parent", f"{base}..{head}")
    ).split()
    require(first_parent_chain and first_parent_chain[0] == DEV_EXTRACTION, "unexpected first-parent extraction history")
    for commit in first_parent_chain[1:]:
        parents = commit_parents(repo, commit)
        require(len(parents) == 2, f"non-merge commit in reconciliation history: {commit}")
        require(is_ancestor(repo, parents[1], cert_tip), f"merge parent is outside certificacion: {commit}")
        require(commit_tree(repo, commit) == commit_tree(repo, parents[1]), f"merge tree differs from certificacion parent: {commit}")
    first_parent_set = set(first_parent_chain)
    all_commits = str(git(repo, "rev-list", f"{base}..{head}")).split()
    unexpected = [
        commit
        for commit in all_commits
        if commit not in first_parent_set and not is_ancestor(repo, commit, cert_tip)
    ]
    require(not unexpected, f"unexpected commits outside certificacion history: {unexpected!r}")
    if event == "push":
        require(commit_parents(repo, head)[0] == base, "desarrollo push first parent drift")


def validate_p1(repo: Path, base: str, head: str, p1_base: str, event: str) -> None:
    require(bool(SHA_RE.fullmatch(p1_base)), "P1 baseline is not frozen")
    require(base == p1_base, "P1 must use the protected post-R0 desarrollo baseline")
    require_sha(repo, "base", base)
    require_sha(repo, "head", head)
    require(is_ancestor(repo, base, head), "P1 base is not an ancestor of head")
    parents = commit_parents(repo, head)
    if event == "pull_request":
        require(parents == [base], "P1 PR head must be one direct commit from protected desarrollo")
    else:
        require(parents and parents[0] == base, "P1 push first parent must be protected desarrollo")
    require_exact_delta(repo, base, head, P1_ALLOWED_STATUSES)


def detect_mode(event: str, base_ref: str, head_ref: str, base: str, p1_base: str = "") -> str:
    if base_ref == "certificacion" and base == CERT_BASE:
        return "cert"
    if base_ref == "desarrollo" and base == DEV_BASE:
        return "dev"
    if base_ref == "desarrollo" and p1_base and base == p1_base and (
        event == "push" or head_ref == P1_HEAD_REF
    ):
        return "p1"
    return "skip"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--event", choices=("pull_request", "push"), required=True)
    parser.add_argument("--base-ref", required=True)
    parser.add_argument("--head-ref", required=True)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--base-repo", required=True)
    parser.add_argument("--head-repo", required=True)
    parser.add_argument("--cert-tip", default="")
    parser.add_argument("--p1-base", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        require(args.base_repo == args.head_repo, "F10.9 boundary requires the same repository")
        mode = detect_mode(args.event, args.base_ref, args.head_ref, args.base_sha, args.p1_base)
        require(mode != "skip", "event does not match an exact F10.9 boundary mode")
        if mode == "cert":
            validate_cert(args.repo, args.base_sha, args.head_sha, args.event)
        elif mode == "dev":
            require(bool(args.cert_tip), "cert_tip is required for desarrollo reconciliation")
            validate_dev(args.repo, args.base_sha, args.head_sha, args.event, args.cert_tip)
        else:
            validate_p1(args.repo, args.base_sha, args.head_sha, args.p1_base, args.event)
        print(f"F10.9 boundary passed: mode={mode}")
        return 0
    except (BoundaryError, subprocess.CalledProcessError) as exc:
        print(f"F10.9 boundary failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
