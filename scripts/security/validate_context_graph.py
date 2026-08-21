#!/usr/bin/env python3
"""Validate the minimum semantic contract of the StudIAMatch Context Graph."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTEXT = ROOT / ".context"
PRIVATE_SOURCE_NAMES = {
    "Studiamatch_MVP_Requerimientos_v5.docx",
    "studiamatch_home.html",
    "studiamatch_resultados.html",
}
PRIVATE_SOURCE_EXTENSIONS = (".docx", ".pdf", ".zip", ".tar", ".tar.gz", ".html")
REQUIRED_INDEX_LINKS = (
    "estado_del_proyecto.md",
    "operaciones/plan_maestro_sprint1_h2_h5.md",
    "operaciones/context_graph_semantico.md",
    "seguimiento/seguimiento_sprint_1_h2_h5.md",
    "seguimiento/plantilla_tracker_reutilizable.md",
    "seguimiento/retrospectiva_hito_001.md",
    "decisiones/ADR-0028_context_graph_semantico_y_autorizacion_r0_r3.md",
    "work_packages/WP-H2-001.json",
    "work_packages/WP-H3-001.json",
    "work_packages/WP-H4-001.json",
    "work_packages/WP-H5-001.json",
)
TRACKER_SECTIONS = (
    "## Verificacion",
    "## Porcentaje De Avance",
    "## Porcentaje De Desviacion",
    "## Cumplimiento De Criterios",
    "## Hallazgos Y Backlog",
    "## Avances",
    "## Siguientes Pasos",
    "## Fecha",
    "## Proximo Prompt Cavernicola",
)


def read(relative: str) -> str:
    return (CONTEXT / relative).read_text(encoding="utf-8")


def fail(message: str, errors: list[str]) -> None:
    errors.append(message)


def main() -> int:
    errors: list[str] = []
    state = read("estado_del_proyecto.md")
    plan = read("operaciones/plan_maestro_sprint1_h2_h5.md")
    tracker = read("seguimiento/seguimiento_sprint_1_h2_h5.md")
    index = read("00_INDICE.md")
    adr = read("decisiones/ADR-0028_context_graph_semantico_y_autorizacion_r0_r3.md")

    for needle in ("F10.11", "COMPLETED_HOMOLOGATED", "Work package activo: `NONE`", "HUMAN_APPROVAL_WP_H2_001_BY_DIGEST"):
        if needle not in state:
            fail(f"estado_del_proyecto.md missing semantic marker: {needle}", errors)
    for pattern in (
        r"\| O3 `certificacion -> main` \| `COMPLETED` \|",
        r"\| O4 `main -> certificacion` \| `COMPLETED` \|",
        r"\| O5 `certificacion -> desarrollo` \| `COMPLETED` \|",
    ):
        if not re.search(pattern, state):
            fail(f"estado_del_proyecto.md missing completed homologation row: {pattern}", errors)

    for needle in ("H2-H5 = NOT_AUTHORIZED", "O3 = COMPLETED", "O4 = COMPLETED", "O5 = COMPLETED", "WP-H2-001"):
        if needle not in plan:
            fail(f"plan_maestro_sprint1_h2_h5.md missing semantic marker: {needle}", errors)

    for forbidden in ("O3 | `BLOCKED`", "O4 | `PENDING`", "O5 | `PENDING`", "COMPLETED_LOCAL_VERIFIED"):
        if forbidden in plan:
            fail(f"plan_maestro_sprint1_h2_h5.md retains stale marker: {forbidden}", errors)

    for section in TRACKER_SECTIONS:
        if section not in tracker:
            fail(f"seguimiento_sprint_1_h2_h5.md missing section: {section}", errors)
    for needle in ("Alcance exclusivo", "Allowlist", "Denylist", "Stop conditions", "Proximo gate unico"):
        if needle not in tracker:
            fail(f"tracker prompt missing field: {needle}", errors)

    for link in REQUIRED_INDEX_LINKS:
        if link not in index:
            fail(f"00_INDICE.md missing canonical link: {link}", errors)

    for level in ("`R0`", "`R1`", "`R2`", "`R3`", "`R3+`"):
        if level not in adr:
            fail(f"ADR-0028 missing authorization level: {level}", errors)

    for manifest_path in sorted((CONTEXT / "work_packages").glob("WP-H*-001.json")):
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        if data.get("status") != "PROPOSED":
            fail(f"{manifest_path.name} must remain PROPOSED before human digest approval", errors)
        if "approval_digest" in data:
            fail(f"{manifest_path.name} must not contain approval_digest while PROPOSED", errors)

    if re.search(r"\| O[345][^\n]*\| `(BLOCKED|PENDING)[^`]*` \|", state):
        fail("estado_del_proyecto.md retains stale O3/O4/O5 blocked or pending status", errors)
    if re.search(r"\| O[345][^\n]*\| `(BLOCKED|PENDING)[^`]*` \|", plan):
        fail("plan_maestro_sprint1_h2_h5.md retains stale O3/O4/O5 blocked or pending status", errors)

    forbidden_status = re.compile(r"H[2-5].*`(ACTIVE|IMPLEMENTED|ACCEPTED|ACCEPTED_WITH_WAIVER|CERTIFIED|VERIFIED_DEVELOPMENT)`")
    if forbidden_status.search(tracker):
        fail("tracker appears to activate or accept H2-H5 before authorization", errors)

    try:
        tracked = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).splitlines()
    except subprocess.CalledProcessError:
        tracked = []
        ignored_dirs = {".git", "node_modules", ".next", "out", ".pytest_cache", "test-results"}
        for dirpath, dirnames, filenames in os.walk(ROOT):
            dirnames[:] = [dirname for dirname in dirnames if dirname not in ignored_dirs]
            for filename in filenames:
                tracked.append(str((Path(dirpath) / filename).relative_to(ROOT)).replace("\\", "/"))
    allowed_env_templates = {".env.example"}
    tracked_env = [
        path
        for path in tracked
        if (Path(path).name.startswith(".env") or path.endswith(".env")) and Path(path).name not in allowed_env_templates
    ]
    if tracked_env:
        fail(f"env-like file present in repository tree: {tracked_env}", errors)

    tracked_sources = [
        path
        for path in tracked
        if Path(path).name in PRIVATE_SOURCE_NAMES or path.lower().endswith(PRIVATE_SOURCE_EXTENSIONS)
    ]
    if tracked_sources:
        fail(f"private source artifact present in repository tree: {tracked_sources}", errors)

    if errors:
        for error in errors:
            print(error)
        return 1
    print("context graph semantic validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
