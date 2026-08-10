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
POST_R0_DEV_BASE = "4dcbb3fd792c25b16627f663fde31e40229718ce"
POST_R0_DEV_TREE = "cad3f1061cbdc00b2883f7812602a4f80bda0853"
WIRING_HEAD_REF = "ci/f10-9-p1-boundary"
P1_HEAD_REF = "fix/f10-9-p1-rebuilt"
POST_P1_DEV_BASE = "53921e3ec845f4a248e586a0ecd667c64f4c070d"
POST_P1_DEV_TREE = "0344c649772aea18314fe022d5f24898e3dc03d0"
P2_WIRING_HEAD_REF = "ci/f10-9-p2-boundary"
P2_HEAD_REF = "feat/f10-9-p2-readonly-planners"
POST_P2_DEV_BASE = "f3b48a177b1ac17f4cb0ac0c4b7e46acb25e32cf"
POST_P2_DEV_TREE = "672a810d7ff59e3fd4006953c2b77823529612b5"
G2_WIRING_HEAD_REF = "ci/f10-9-g2-boundary"
G2_HEAD_REF = "feat/f10-9-p3-p4-runtime-fail-closed"
POST_G2_DEV_BASE = "0f3bdafde9adb49749aed6c758c235924b0f0063"
POST_G2_DEV_TREE = "fae420228a6c5631bddb730f38e6204df1dfcc97"
P5_WIRING_HEAD_REF = "ci/f10-9-g3-boundary"
P5_HEAD_REF = "feat/f10-9-p5-metadata-readonly"

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

CERT_ALLOWED_MODES = {
    path: "100755" if path == ".github/workflows/security-audit.yml" else "100644"
    for path in CERT_ALLOWED_STATUSES
}

P1_ALLOWED_STATUSES = {
    "scripts/shared/db_client.py": "M",
    "scripts/shared/safe_http.py": "A",
    "scripts/shared/url_identity.py": "A",
    "scripts/shared/utils.py": "M",
    "tests/test_fase10_9_p1_safety_contracts.py": "A",
}

P2_ALLOWED_STATUSES = {
    "scripts/shared/f10_9_readonly_planner.py": "A",
    "scripts/maintenance/f10_9_readonly_audit.py": "A",
    "tests/fixtures/f10_9_p2_synthetic.json": "A",
    "tests/test_fase10_9_p2_readonly_planners.py": "A",
}

G2_ALLOWED_STATUSES = {
    "scripts/core/master_orchestrator.py": "M",
    "scripts/core/integrity_ping.py": "M",
    "scripts/shared/f10_9_fg2_preflight.py": "A",
    "scripts/shared/f10_9_fg3_atomic.py": "A",
    "tests/test_fase10_9_p3_fg2_preflight.py": "A",
    "tests/test_fase10_9_p4_fg3_atomicity.py": "A",
}

G2_ALLOWED_MODES = {path: "100644" for path in G2_ALLOWED_STATUSES}

P5_ALLOWED_STATUSES = {
    "scripts/shared/f10_9_metadata_planner.py": "A",
    "tests/test_fase10_9_p5_metadata_readonly.py": "A",
}

P5_ALLOWED_MODES = {path: "100644" for path in P5_ALLOWED_STATUSES}

WIRING_ALLOWED_STATUSES = {
    "AGENTS.md": "M",
    ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
    ".context/estado_del_proyecto.md": "M",
    ".context/operaciones/g0_r0_reconciliacion_f10_9.md": "M",
    ".context/operaciones/plan_remediacion_f10_9_fg2_fg3.md": "M",
    ".context/operaciones/r0_ci_boundary_manifest_2026_08_09.md": "M",
    ".context/operaciones/r0_post_merge_evidence_2026_08_09.md": "A",
    ".github/workflows/f9-7-contract.yml": "M",
    ".github/workflows/security-audit.yml": "M",
    "scripts/security/f109_boundary.py": "M",
    "tests/test_fase10_9_branch_reconciliation.py": "M",
    "tests/test_fase10_main_boundary.py": "M",
}

WIRING_ALLOWED_MODES = {
    path: "100755" if path == ".github/workflows/security-audit.yml" else "100644"
    for path in WIRING_ALLOWED_STATUSES
}

P2_WIRING_ALLOWED_STATUSES = {
    ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
    ".context/estado_del_proyecto.md": "M",
    ".context/operaciones/g0_r0_reconciliacion_f10_9.md": "M",
    ".context/operaciones/plan_remediacion_f10_9_fg2_fg3.md": "M",
    ".context/operaciones/r0_ci_boundary_manifest_2026_08_09.md": "M",
    ".context/operaciones/r0_post_merge_evidence_2026_08_09.md": "M",
    ".github/workflows/f9-7-contract.yml": "M",
    ".github/workflows/security-audit.yml": "M",
    "scripts/security/f109_boundary.py": "M",
    "tests/test_fase10_9_branch_reconciliation.py": "M",
}

P2_WIRING_ALLOWED_MODES = {
    path: "100755" if path == ".github/workflows/security-audit.yml" else "100644"
    for path in P2_WIRING_ALLOWED_STATUSES
}

G2_WIRING_ALLOWED_STATUSES = {
    ".github/workflows/f9-7-contract.yml": "M",
    ".github/workflows/security-audit.yml": "M",
    "scripts/security/f109_boundary.py": "M",
    "tests/test_fase10_9_branch_reconciliation.py": "M",
}

G2_WIRING_ALLOWED_MODES = {
    path: "100755" if path == ".github/workflows/security-audit.yml" else "100644"
    for path in G2_WIRING_ALLOWED_STATUSES
}

P5_WIRING_ALLOWED_STATUSES = {
    ".github/workflows/f9-7-contract.yml": "M",
    ".github/workflows/security-audit.yml": "M",
    "scripts/security/f109_boundary.py": "M",
    "tests/test_fase10_9_branch_reconciliation.py": "M",
}

P5_WIRING_ALLOWED_MODES = {
    path: "100755" if path == ".github/workflows/security-audit.yml" else "100644"
    for path in P5_WIRING_ALLOWED_STATUSES
}

CONTEXT_IGNORED_PREFIXES = (
    ".context/.obsidian/",
    ".context/artifacts/private/",
)

LEGACY_ALLOWED_STATUSES = {
    ".gitattributes": {"M"},
    ".github/workflows/fg1_inventory.yml": {"M"},
    ".github/workflows/db-sync-to-pro.yml": {"M"},
    "db/migrations/20260808_fase10_8_atomic_cleansing_provenance.sql": {"A"},
    "db/restore_full_schema.sql": {"M"},
    "scripts/maintenance/db_migrate.py": {"M"},
    ".github/workflows/fg3_integrity.yml": {"M"},
    ".github/workflows/production_pipeline.yml": {"M"},
    "scripts/core/certification_canary_manifest.py": {"A", "M"},
    "scripts/core/certification_canary_state.py": {"A", "M"},
    "scripts/core/production_canary_manifest.py": {"A", "M"},
    "scripts/core/production_canary_source_preflight.py": {"A", "M"},
    "scripts/core/production_canary_state.py": {"A", "M"},
    "scripts/core/cleansing_worker.py": {"M"},
    "scripts/core/discovery_institutions.py": {"M"},
    "scripts/core/enrichment_worker.py": {"M"},
    "scripts/core/integrity_ping.py": {"M"},
    "scripts/core/master_orchestrator.py": {"M"},
    "scripts/core/sync_vector_worker.py": {"M"},
    "scripts/core/universal_harvester.py": {"M"},
    "scripts/shared/db_client.py": {"M"},
}

LEGACY_PROTECTED_PATHS = {
    ".github/workflows/fg1_inventory.yml",
    ".github/workflows/production_pipeline.yml",
    ".github/workflows/fg3_integrity.yml",
    ".github/workflows/db-sync-to-pro.yml",
    "requirements-fg1.txt",
    "requirements-pipeline.txt",
    "requirements-fg3.txt",
    "requirements-db-migrate.txt",
    "db/manifests/fase09_7_free_schema_rls_v3.json",
    "db/migrations/20260724_fase06_g1b_reconciliation.sql",
    "db/migrations/20260724_fase06_hito1_editorial_contract.sql",
    "db/migrations/20260725_fase07_g1b_closure.sql",
    "db/migrations/20260725_fase08_hito1_functional_closure.sql",
    "db/migrations/20260727_fase09_7_public_access_closure.sql",
    "db/migrations/20260728_fase09_7_notify_new_lead_retirement_v3.sql",
    "scripts/maintenance/category_coverage_audit.py",
    "scripts/maintenance/quality_assurance_audit.py",
    "scripts/maintenance/taxonomy_roi_audit.py",
}

F109_CONTROL_PATHS = {
    ".github/workflows/f9-7-contract.yml",
    ".github/workflows/security-audit.yml",
    "scripts/security/f109_boundary.py",
    "tests/test_fase10_9_branch_reconciliation.py",
    "tests/test_fase10_main_boundary.py",
}

LEGACY_PROTECTED_PREFIXES = ("scripts/core/", "scripts/shared/", "config/")
LEGACY_DENIED_PREFIXES = ("db/", "supabase/", "web/", "scripts/maintenance/")


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
    expected_modes: dict[str, str] | None = None,
) -> None:
    actual = changed_statuses(repo, base, head)
    require(actual == expected, f"delta mismatch: expected={expected!r} actual={actual!r}")
    for path, status in actual.items():
        if status == "D":
            continue
        metadata = str(git(repo, "ls-tree", head, "--", path)).strip().split(None, 3)
        require(len(metadata) == 4, f"missing tree metadata for {path}")
        mode, kind, _blob, tree_path = metadata
        expected_mode = (expected_modes or {}).get(path, "100644")
        require((mode, kind, tree_path) == (expected_mode, "blob", path), f"invalid tree entry {path}")


def validate_non_p1_delta(repo: Path, head: str, actual: dict[str, str]) -> None:
    failures: list[str] = []
    for path, status in actual.items():
        if path.startswith(CONTEXT_IGNORED_PREFIXES):
            failures.append(f"private-context-tracked:{path}")
            continue
        if path in F109_CONTROL_PATHS:
            failures.append(f"f109-control-drift:{path}")
            continue
        allowed_statuses = LEGACY_ALLOWED_STATUSES.get(path)
        if path.startswith(LEGACY_DENIED_PREFIXES) and allowed_statuses is None:
            failures.append(f"legacy-denied:{path}")
            continue
        if (
            path in LEGACY_PROTECTED_PATHS or path.startswith(LEGACY_PROTECTED_PREFIXES)
        ) and allowed_statuses is None:
            failures.append(f"legacy-protected-drift:{path}")
            continue
        if allowed_statuses is not None and status not in allowed_statuses:
            failures.append(f"legacy-status:{status}:{path}")
            continue
        if allowed_statuses is not None and status != "D":
            metadata = str(git(repo, "ls-tree", head, "--", path)).strip().split(None, 3)
            if len(metadata) != 4 or (metadata[0], metadata[1], metadata[3]) != (
                "100644",
                "blob",
                path,
            ):
                failures.append(f"legacy-mode-kind:{path}")
    require(not failures, f"non-P1 delta violates legacy boundary: {failures!r}")


def validate_context_graph(
    root: Path,
    expected_files: int,
    expected_links: int,
    expected_blobs: dict[str, str] | None = None,
    forbidden_paths: set[str] | None = None,
) -> None:
    root = root.resolve()
    tracked_private = str(
        git(root, "ls-files", "--", ".context/.obsidian", ".context/artifacts/private")
    ).split()
    require(not tracked_private, f"private context paths must remain untracked: {tracked_private!r}")
    markdown_files = sorted(
        path
        for path in (root / ".context").rglob("*.md")
        if not path.relative_to(root).as_posix().startswith(CONTEXT_IGNORED_PREFIXES)
    )
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
    require_exact_delta(repo, CERT_ANCHOR, head, CERT_ALLOWED_STATUSES, CERT_ALLOWED_MODES)
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
    candidate_head = head
    if event == "push":
        push_parents = commit_parents(repo, head)
        require(len(push_parents) == 2, "desarrollo push must be a protected merge commit")
        require(push_parents[0] == base, "desarrollo push first parent drift")
        candidate_head = push_parents[1]
        require(commit_tree(repo, head) == commit_tree(repo, candidate_head), "push tree differs from PR head")
    require(is_ancestor(repo, DEV_EXTRACTION, candidate_head), "extraction is not an ancestor of PR head")
    require(is_ancestor(repo, cert_tip, candidate_head), "protected certificacion tip is not an ancestor")
    require(commit_tree(repo, candidate_head) == commit_tree(repo, cert_tip), "desarrollo tree differs from certificacion")
    first_parent_chain = str(
        git(repo, "rev-list", "--reverse", "--first-parent", f"{base}..{candidate_head}")
    ).split()
    require(first_parent_chain and first_parent_chain[0] == DEV_EXTRACTION, "unexpected first-parent extraction history")
    for commit in first_parent_chain[1:]:
        parents = commit_parents(repo, commit)
        require(len(parents) == 2, f"non-merge commit in reconciliation history: {commit}")
        require(is_ancestor(repo, parents[1], cert_tip), f"merge parent is outside certificacion: {commit}")
        require(commit_tree(repo, commit) == commit_tree(repo, parents[1]), f"merge tree differs from certificacion parent: {commit}")
    first_parent_set = set(first_parent_chain)
    all_commits = str(git(repo, "rev-list", f"{base}..{candidate_head}")).split()
    unexpected = [
        commit
        for commit in all_commits
        if commit not in first_parent_set and not is_ancestor(repo, commit, cert_tip)
    ]
    require(not unexpected, f"unexpected commits outside certificacion history: {unexpected!r}")


def validate_wiring(repo: Path, base: str, head: str, event: str) -> None:
    require(base == POST_R0_DEV_BASE, "unexpected P1 wiring baseline")
    require_sha(repo, "POST_R0_DEV_BASE", base)
    require_sha(repo, "head", head)
    require(commit_tree(repo, base) == POST_R0_DEV_TREE, "post-R0 desarrollo tree drift")
    archive_commit = str(git(repo, "rev-parse", DEV_ARCHIVE_REF)).strip()
    require(archive_commit == DEV_BASE, "CA2 archive commit drift during P1 wiring")
    require(commit_tree(repo, archive_commit) == DEV_ARCHIVE_TREE, "CA2 archive tree drift during P1 wiring")
    candidate_head = head
    if event == "push":
        push_parents = commit_parents(repo, head)
        require(len(push_parents) == 2, "P1 wiring push must be a protected merge commit")
        require(push_parents[0] == base, "P1 wiring push first parent drift")
        candidate_head = push_parents[1]
        require(commit_tree(repo, head) == commit_tree(repo, candidate_head), "P1 wiring push tree differs from PR head")
    require(commit_parents(repo, candidate_head) == [base], "P1 wiring PR must be one direct commit")
    require_exact_delta(
        repo,
        base,
        candidate_head,
        WIRING_ALLOWED_STATUSES,
        WIRING_ALLOWED_MODES,
    )
    validate_context_graph(
        repo,
        expected_files=42,
        expected_links=341,
        expected_blobs=CONTEXT_EXPECTED_BLOBS,
        forbidden_paths=CONTEXT_FORBIDDEN_PATHS,
    )


def validate_p1(
    repo: Path,
    base: str,
    head: str,
    p1_base: str,
    p1_base_tree: str,
    event: str,
) -> None:
    require(bool(SHA_RE.fullmatch(p1_base)), "P1 baseline is not frozen")
    require(bool(SHA_RE.fullmatch(p1_base_tree)), "P1 baseline tree is not frozen")
    require(base == p1_base, "P1 must use the protected post-R0 desarrollo baseline")
    require_sha(repo, "base", base)
    require_sha(repo, "head", head)
    require(commit_tree(repo, base) == p1_base_tree, "P1 protected base tree drift")
    require(is_ancestor(repo, base, head), "P1 base is not an ancestor of head")
    candidate_head = head
    if event == "pull_request":
        require(commit_parents(repo, candidate_head) == [base], "P1 PR head must be one direct commit from protected desarrollo")
    else:
        push_parents = commit_parents(repo, head)
        require(len(push_parents) == 2, "P1 push must be a protected merge commit")
        require(push_parents[0] == base, "P1 push first parent must be protected desarrollo")
        candidate_head = push_parents[1]
        require(commit_parents(repo, candidate_head) == [base], "P1 merged PR must contain one direct commit")
        require(commit_tree(repo, head) == commit_tree(repo, candidate_head), "P1 push tree differs from PR head")
    require_exact_delta(repo, base, candidate_head, P1_ALLOWED_STATUSES)


def validate_p2_wiring(repo: Path, base: str, head: str, event: str) -> None:
    require(base == POST_P1_DEV_BASE, "unexpected P2 wiring baseline")
    require_sha(repo, "POST_P1_DEV_BASE", base)
    require_sha(repo, "head", head)
    require(commit_tree(repo, base) == POST_P1_DEV_TREE, "post-P1 desarrollo tree drift")
    archive_commit = str(git(repo, "rev-parse", DEV_ARCHIVE_REF)).strip()
    require(archive_commit == DEV_BASE, "CA2 archive commit drift during P2 wiring")
    require(commit_tree(repo, archive_commit) == DEV_ARCHIVE_TREE, "CA2 archive tree drift during P2 wiring")
    candidate_head = head
    if event == "push":
        push_parents = commit_parents(repo, head)
        require(len(push_parents) == 2, "P2 wiring push must be a protected merge commit")
        require(push_parents[0] == base, "P2 wiring push first parent drift")
        candidate_head = push_parents[1]
        require(commit_tree(repo, head) == commit_tree(repo, candidate_head), "P2 wiring push tree differs from PR head")
    require(commit_parents(repo, candidate_head) == [base], "P2 wiring PR must be one direct commit")
    require_exact_delta(
        repo,
        base,
        candidate_head,
        P2_WIRING_ALLOWED_STATUSES,
        P2_WIRING_ALLOWED_MODES,
    )
    validate_context_graph(
        repo,
        expected_files=42,
        expected_links=341,
        expected_blobs=CONTEXT_EXPECTED_BLOBS,
        forbidden_paths=CONTEXT_FORBIDDEN_PATHS,
    )


def validate_p2(
    repo: Path,
    base: str,
    head: str,
    p2_base: str,
    p2_base_tree: str,
    event: str,
) -> None:
    require(bool(SHA_RE.fullmatch(p2_base)), "P2 baseline is not frozen")
    require(bool(SHA_RE.fullmatch(p2_base_tree)), "P2 baseline tree is not frozen")
    require(base == p2_base, "P2 must use the protected post-wiring desarrollo baseline")
    require_sha(repo, "base", base)
    require_sha(repo, "head", head)
    require(commit_tree(repo, base) == p2_base_tree, "P2 protected base tree drift")
    require(is_ancestor(repo, base, head), "P2 base is not an ancestor of head")
    candidate_head = head
    if event == "pull_request":
        require(commit_parents(repo, candidate_head) == [base], "P2 PR head must be one direct commit from protected desarrollo")
    else:
        push_parents = commit_parents(repo, head)
        require(len(push_parents) == 2, "P2 push must be a protected merge commit")
        require(push_parents[0] == base, "P2 push first parent must be protected desarrollo")
        candidate_head = push_parents[1]
        require(commit_parents(repo, candidate_head) == [base], "P2 merged PR must contain one direct commit")
        require(commit_tree(repo, head) == commit_tree(repo, candidate_head), "P2 push tree differs from PR head")
    require_exact_delta(repo, base, candidate_head, P2_ALLOWED_STATUSES)


def validate_g2_wiring(repo: Path, base: str, head: str, event: str) -> None:
    require(base == POST_P2_DEV_BASE, "unexpected G2 wiring baseline")
    require_sha(repo, "POST_P2_DEV_BASE", base)
    require_sha(repo, "head", head)
    require(commit_tree(repo, base) == POST_P2_DEV_TREE, "post-P2 desarrollo tree drift")
    archive_commit = str(git(repo, "rev-parse", DEV_ARCHIVE_REF)).strip()
    require(archive_commit == DEV_BASE, "CA2 archive commit drift during G2 wiring")
    require(commit_tree(repo, archive_commit) == DEV_ARCHIVE_TREE, "CA2 archive tree drift during G2 wiring")
    candidate_head = head
    if event == "push":
        push_parents = commit_parents(repo, head)
        require(len(push_parents) == 2, "G2 wiring push must be a protected merge commit")
        require(push_parents[0] == base, "G2 wiring push first parent drift")
        candidate_head = push_parents[1]
        require(commit_tree(repo, head) == commit_tree(repo, candidate_head), "G2 wiring push tree differs from PR head")
    require(commit_parents(repo, candidate_head) == [base], "G2 wiring PR must be one direct commit")
    require_exact_delta(
        repo,
        base,
        candidate_head,
        G2_WIRING_ALLOWED_STATUSES,
        G2_WIRING_ALLOWED_MODES,
    )
    validate_context_graph(
        repo,
        expected_files=43,
        expected_links=344,
        expected_blobs=CONTEXT_EXPECTED_BLOBS,
        forbidden_paths=CONTEXT_FORBIDDEN_PATHS,
    )


def validate_g2(
    repo: Path,
    base: str,
    head: str,
    g2_base: str,
    g2_base_tree: str,
    event: str,
) -> None:
    require(bool(SHA_RE.fullmatch(g2_base)), "G2 baseline is not frozen")
    require(bool(SHA_RE.fullmatch(g2_base_tree)), "G2 baseline tree is not frozen")
    require(base == g2_base, "G2 must use the protected post-wiring desarrollo baseline")
    require_sha(repo, "base", base)
    require_sha(repo, "head", head)
    require(commit_tree(repo, base) == g2_base_tree, "G2 protected base tree drift")
    require(is_ancestor(repo, base, head), "G2 base is not an ancestor of head")
    candidate_head = head
    if event == "pull_request":
        require(commit_parents(repo, candidate_head) == [base], "G2 PR head must be one direct commit from protected desarrollo")
    else:
        push_parents = commit_parents(repo, head)
        require(len(push_parents) == 2, "G2 push must be a protected merge commit")
        require(push_parents[0] == base, "G2 push first parent must be protected desarrollo")
        candidate_head = push_parents[1]
        require(commit_parents(repo, candidate_head) == [base], "G2 merged PR must contain one direct commit")
        require(commit_tree(repo, head) == commit_tree(repo, candidate_head), "G2 push tree differs from PR head")
    require_exact_delta(
        repo,
        base,
        candidate_head,
        G2_ALLOWED_STATUSES,
        G2_ALLOWED_MODES,
    )


def validate_p5_wiring(repo: Path, base: str, head: str, event: str) -> None:
    require(base == POST_G2_DEV_BASE, "unexpected P5 wiring baseline")
    require_sha(repo, "POST_G2_DEV_BASE", base)
    require_sha(repo, "head", head)
    require(commit_tree(repo, base) == POST_G2_DEV_TREE, "post-G2 desarrollo tree drift")
    archive_commit = str(git(repo, "rev-parse", DEV_ARCHIVE_REF)).strip()
    require(archive_commit == DEV_BASE, "CA2 archive commit drift during P5 wiring")
    require(commit_tree(repo, archive_commit) == DEV_ARCHIVE_TREE, "CA2 archive tree drift during P5 wiring")
    candidate_head = head
    if event == "push":
        push_parents = commit_parents(repo, head)
        require(len(push_parents) == 2, "P5 wiring push must be a protected merge commit")
        require(push_parents[0] == base, "P5 wiring push first parent drift")
        candidate_head = push_parents[1]
        require(commit_tree(repo, head) == commit_tree(repo, candidate_head), "P5 wiring push tree differs from PR head")
    require(commit_parents(repo, candidate_head) == [base], "P5 wiring PR must be one direct commit")
    require_exact_delta(
        repo,
        base,
        candidate_head,
        P5_WIRING_ALLOWED_STATUSES,
        P5_WIRING_ALLOWED_MODES,
    )
    validate_context_graph(
        repo,
        expected_files=44,
        expected_links=345,
        expected_blobs=CONTEXT_EXPECTED_BLOBS,
        forbidden_paths=CONTEXT_FORBIDDEN_PATHS,
    )


def validate_p5(
    repo: Path,
    base: str,
    head: str,
    p5_base: str,
    p5_base_tree: str,
    event: str,
) -> None:
    require(bool(SHA_RE.fullmatch(p5_base)), "P5 baseline is not frozen")
    require(bool(SHA_RE.fullmatch(p5_base_tree)), "P5 baseline tree is not frozen")
    require(base == p5_base, "P5 must use the protected post-wiring desarrollo baseline")
    require_sha(repo, "base", base)
    require_sha(repo, "head", head)
    require(commit_tree(repo, base) == p5_base_tree, "P5 protected base tree drift")
    require(is_ancestor(repo, base, head), "P5 base is not an ancestor of head")
    candidate_head = head
    if event == "pull_request":
        require(commit_parents(repo, candidate_head) == [base], "P5 PR head must be one direct commit from protected desarrollo")
    else:
        push_parents = commit_parents(repo, head)
        require(len(push_parents) == 2, "P5 push must be a protected merge commit")
        require(push_parents[0] == base, "P5 push first parent must be protected desarrollo")
        candidate_head = push_parents[1]
        require(commit_parents(repo, candidate_head) == [base], "P5 merged PR must contain one direct commit")
        require(commit_tree(repo, head) == commit_tree(repo, candidate_head), "P5 push tree differs from PR head")
    require_exact_delta(repo, base, candidate_head, P5_ALLOWED_STATUSES, P5_ALLOWED_MODES)


def detect_mode(
    event: str,
    base_ref: str,
    head_ref: str,
    base: str,
    p1_base: str = "",
    p2_base: str = "",
    g2_base: str = "",
    p5_base: str = "",
) -> str:
    if base_ref == "certificacion" and base == CERT_BASE:
        return "cert"
    if base_ref == "desarrollo" and base == DEV_BASE:
        return "dev"
    if base_ref == "desarrollo" and base == POST_R0_DEV_BASE and (
        event == "push" or head_ref == WIRING_HEAD_REF
    ):
        return "wiring"
    if base_ref == "desarrollo" and base == POST_P1_DEV_BASE and (
        event == "push" or head_ref == P2_WIRING_HEAD_REF
    ):
        return "p2_wiring"
    if base_ref == "desarrollo" and base == POST_P2_DEV_BASE and (
        event == "push" or head_ref == G2_WIRING_HEAD_REF
    ):
        return "g2_wiring"
    if base_ref == "desarrollo" and base == POST_G2_DEV_BASE and (
        event == "push" or head_ref == P5_WIRING_HEAD_REF
    ):
        return "p5_wiring"
    if event == "pull_request" and base_ref == "desarrollo" and p1_base and base == p1_base and head_ref == P1_HEAD_REF:
        return "p1"
    if event == "pull_request" and base_ref == "desarrollo" and p2_base and base == p2_base and head_ref == P2_HEAD_REF:
        return "p2"
    if event == "pull_request" and base_ref == "desarrollo" and g2_base and base == g2_base and head_ref == G2_HEAD_REF:
        return "g2"
    if event == "pull_request" and base_ref == "desarrollo" and p5_base and base == p5_base and head_ref == P5_HEAD_REF:
        return "p5"
    return "skip"


def emit_mode(mode: str, github_output: str) -> None:
    print(f"F10.9 boundary passed: mode={mode}")
    if github_output:
        with Path(github_output).open("a", encoding="utf-8") as output:
            output.write(f"mode={mode}\n")


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
    parser.add_argument("--p1-base-tree", default="")
    parser.add_argument("--p2-base", default="")
    parser.add_argument("--p2-base-tree", default="")
    parser.add_argument("--g2-base", default="")
    parser.add_argument("--g2-base-tree", default="")
    parser.add_argument("--p5-base", default="")
    parser.add_argument("--p5-base-tree", default="")
    parser.add_argument("--github-output", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        require(args.base_repo == args.head_repo, "F10.9 boundary requires the same repository")
        mode = detect_mode(
            args.event,
            args.base_ref,
            args.head_ref,
            args.base_sha,
            args.p1_base,
            args.p2_base,
            args.g2_base,
            getattr(args, "p5_base", ""),
        )
        if mode == "skip" and args.base_ref == "desarrollo":
            if args.event == "pull_request" and args.head_ref == WIRING_HEAD_REF:
                raise BoundaryError("P1 wiring branch requires the frozen post-R0 baseline")
            if args.event == "pull_request" and args.head_ref == P1_HEAD_REF:
                raise BoundaryError("P1 branch requires the frozen protected desarrollo baseline")
            if args.event == "pull_request" and args.head_ref == P2_WIRING_HEAD_REF:
                raise BoundaryError("P2 wiring branch requires the frozen post-P1 baseline")
            if args.event == "pull_request" and args.head_ref == P2_HEAD_REF:
                raise BoundaryError("P2 branch requires the frozen protected desarrollo baseline")
            if args.event == "pull_request" and args.head_ref == G2_WIRING_HEAD_REF:
                raise BoundaryError("G2 wiring branch requires the frozen post-P2 baseline")
            if args.event == "pull_request" and args.head_ref == G2_HEAD_REF:
                raise BoundaryError("G2 branch requires the frozen protected desarrollo baseline")
            if args.event == "pull_request" and args.head_ref == P5_WIRING_HEAD_REF:
                raise BoundaryError("P5 wiring branch requires the frozen post-G2 baseline")
            if args.event == "pull_request" and args.head_ref == P5_HEAD_REF:
                raise BoundaryError("P5 branch requires the frozen protected desarrollo baseline")
            actual = changed_statuses(args.repo, args.base_sha, args.head_sha)
            touched_p1 = set(actual).intersection(P1_ALLOWED_STATUSES)
            touched_p2 = set(actual).intersection(P2_ALLOWED_STATUSES)
            touched_g2 = set(actual).intersection(G2_ALLOWED_STATUSES)
            touched_p5 = set(actual).intersection(P5_ALLOWED_STATUSES)
            require(
                sum(bool(surface) for surface in (touched_p1, touched_p2, touched_g2, touched_p5)) <= 1,
                "P1, P2, G2, and P5 surfaces cannot share a candidate",
            )
            if touched_p1:
                require(args.head_ref == P1_HEAD_REF or args.event == "push", "P1 paths require the protected P1 branch")
                require(actual == P1_ALLOWED_STATUSES, "partial or expanded P1 delta is forbidden")
                mode = "p1"
            elif touched_p2:
                require(args.head_ref == P2_HEAD_REF or args.event == "push", "P2 paths require the protected P2 branch")
                require(actual == P2_ALLOWED_STATUSES, "partial or expanded P2 delta is forbidden")
                mode = "p2"
            elif touched_g2:
                require(args.head_ref == G2_HEAD_REF or args.event == "push", "G2 paths require the protected G2 branch")
                require(actual == G2_ALLOWED_STATUSES, "partial or expanded G2 delta is forbidden")
                mode = "g2"
            elif touched_p5:
                require(args.head_ref == P5_HEAD_REF or args.event == "push", "P5 paths require the protected P5 branch")
                require(actual == P5_ALLOWED_STATUSES, "partial or expanded P5 delta is forbidden")
                mode = "p5"
            else:
                validate_non_p1_delta(args.repo, args.head_sha, actual)
                emit_mode("skip_non_p1", args.github_output)
                return 0
        require(mode != "skip", "event does not match an exact F10.9 boundary mode")
        if mode == "cert":
            validate_cert(args.repo, args.base_sha, args.head_sha, args.event)
        elif mode == "dev":
            require(bool(args.cert_tip), "cert_tip is required for desarrollo reconciliation")
            validate_dev(args.repo, args.base_sha, args.head_sha, args.event, args.cert_tip)
        elif mode == "wiring":
            validate_wiring(args.repo, args.base_sha, args.head_sha, args.event)
        elif mode == "p1":
            validate_p1(
                args.repo,
                args.base_sha,
                args.head_sha,
                args.p1_base,
                args.p1_base_tree,
                args.event,
            )
        elif mode == "p2_wiring":
            validate_p2_wiring(args.repo, args.base_sha, args.head_sha, args.event)
        elif mode == "p2":
            validate_p2(
                args.repo,
                args.base_sha,
                args.head_sha,
                args.p2_base,
                args.p2_base_tree,
                args.event,
            )
        elif mode == "g2_wiring":
            validate_g2_wiring(args.repo, args.base_sha, args.head_sha, args.event)
        elif mode == "p5_wiring":
            validate_p5_wiring(args.repo, args.base_sha, args.head_sha, args.event)
        elif mode == "p5":
            validate_p5(
                args.repo,
                args.base_sha,
                args.head_sha,
                getattr(args, "p5_base", ""),
                getattr(args, "p5_base_tree", ""),
                args.event,
            )
        else:
            validate_g2(
                args.repo,
                args.base_sha,
                args.head_sha,
                args.g2_base,
                args.g2_base_tree,
                args.event,
            )
        emit_mode(mode, args.github_output)
        return 0
    except (BoundaryError, subprocess.CalledProcessError) as exc:
        print(f"F10.9 boundary failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
