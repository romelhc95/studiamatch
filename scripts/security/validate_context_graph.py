#!/usr/bin/env python3
"""Validate the semantic contract of the StudIAMatch Context Graph."""

from __future__ import annotations

import json
import os
import re
import subprocess
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
    "decisiones/ADR-0003_taxonomia_macrofases_subfases.md",
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
    "matrices/matriz_hito_002.md",
    "evidencias_cliente/req_est_001_sprint_1/evidencia_hito_002.md",
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
H2_CRITERIA = {"H2-CA2", "H2-CA3"}
EXPECTED_BASELINE = {
    "main_commit": "9b486146962bd2a092acfd649fdcf716e922de89",
    "main_tree": "fcb59095e48441bb4486ccc196aee61e2e1e0fe3",
    "certificacion_commit": "fe7b27abf18c096f674948b4f30f815aea4aef08",
    "certificacion_tree": "fcb59095e48441bb4486ccc196aee61e2e1e0fe3",
    "desarrollo_commit": "974f9d4bde6d79230afde5c5a86ba7a3894233c6",
    "desarrollo_tree": "fcb59095e48441bb4486ccc196aee61e2e1e0fe3",
}
APPROVED_DIGEST = "2dc7f7864ffb766282f33b52dd5f0dc54e45c3b52a18d91f528ef1a44901a933"
APPROVED_CANDIDATE_COMMIT = "c8e4596b153c10721ed335369863a07154eb2b43"
ACTIVATION_BASE_COMMIT = "6ad2690239db361bf913fc9f14c22146d11e69a6"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
UTC_TS = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def read(root: Path, relative: str) -> str:
    return (root / ".context" / relative).read_text(encoding="utf-8")


def table_value(text: str, field: str) -> str | None:
    pattern = rf"^\|\s*{re.escape(field)}\s*\|\s*`?([^`|]+)`?\s*\|"
    match = re.search(pattern, text, re.MULTILINE)
    return match.group(1).strip() if match else None


def bullet_value(text: str, field: str) -> str | None:
    pattern = rf"^-\s*{re.escape(field)}:\s*(.+)$"
    match = re.search(pattern, text, re.MULTILINE)
    return match.group(1).strip() if match else None


def linked_id(value: str | None) -> str | None:
    if not value:
        return None
    match = re.search(r"\[([^\]]+)\]", value)
    return match.group(1) if match else value.strip("`")


def criteria_from_text(text: str) -> set[str]:
    return set(re.findall(r"H2-CA[23]", text))


def validate(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    state = read(root, "estado_del_proyecto.md")
    plan = read(root, "operaciones/plan_maestro_sprint1_h2_h5.md")
    release_flow = read(root, "operaciones/flujo_release_minimo.md")
    tracker = read(root, "seguimiento/seguimiento_sprint_1_h2_h5.md")
    hito = read(root, "hitos/hito_002.md")
    task = read(root, "backlog_tareas/req_est_001_sprint_1/tarea_002_hito_2.md")
    matrix = read(root, "matrices/matriz_hito_002.md")
    index = read(root, "00_INDICE.md")
    adr = read(root, "decisiones/ADR-0028_context_graph_semantico_y_autorizacion_r0_r3.md")
    adr0003 = read(root, "decisiones/ADR-0003_taxonomia_macrofases_subfases.md")
    evidence = read(root, "evidencias_cliente/req_est_001_sprint_1/evidencia_hito_002.md")
    legacy_evidence = read(root, "evidencias_cliente/sprint_1/evidencia_hito_002.md")
    wp = json.loads((root / ".context" / "work_packages" / "WP-H2-001.json").read_text(encoding="utf-8"))

    if linked_id(bullet_value(state, "Hito")) != "HITO-002":
        errors.append("GRAPH_ID_MISMATCH:state active hito must be HITO-002")
    if linked_id(bullet_value(state, "Tarea")) != "TASK-H2-001":
        errors.append("GRAPH_ID_MISMATCH:state active task must be TASK-H2-001")
    if "WP-H2-001=ACTIVE_R1" not in state:
        errors.append("GRAPH_ID_MISMATCH:state must reference WP-H2-001 as active R1")
    if "Subfase tecnica activa: `F12.1`" not in state:
        errors.append("EXECUTION_PHASE_MISMATCH:state must activate F12.1")
    if "`F12.1` | `READY_NOT_STARTED`" not in state or "`F12.2` | `BLOCKED_BY_F12_1_CA2`" not in state:
        errors.append("EXECUTION_PHASE_MISMATCH:F12 taxonomy missing")
    if wp.get("id") != "WP-H2-001" or wp.get("task_id") != "TASK-H2-001" or wp.get("hito") != "HITO-002":
        errors.append("GRAPH_ID_MISMATCH:WP-H2-001 IDs")

    expected = {
        "Lifecycle stage": "ACTIVE",
        "Gate status": "APPROVED_R1",
        "Implementation status": "READY_NOT_STARTED",
        "Acceptance status": "NOT_STARTED",
    }
    for field, value in expected.items():
        if table_value(hito, field) != value:
            errors.append(f"LIFECYCLE_MISMATCH:hito:{field}")
        if field in {"Lifecycle stage", "Implementation status"} and table_value(task, field) != value:
            errors.append(f"LIFECYCLE_MISMATCH:task:{field}")
        state_value = bullet_value(state, field)
        if state_value is None:
            errors.append(f"LIFECYCLE_MISMATCH:state missing {field}")
        elif value not in state_value:
            errors.append(f"LIFECYCLE_MISMATCH:state:{field}")
        if value not in tracker:
            errors.append(f"LIFECYCLE_MISMATCH:tracker missing {value}")
        if value not in plan:
            errors.append(f"LIFECYCLE_MISMATCH:plan missing {value}")
    if wp.get("lifecycle_stage") != "ACTIVE" or wp.get("implementation_status") != "READY_NOT_STARTED":
        errors.append("LIFECYCLE_MISMATCH:wp")
    if wp.get("gate_status") != "APPROVED_R1" or wp.get("acceptance_status") != "NOT_STARTED":
        errors.append("LIFECYCLE_MISMATCH:wp gate/acceptance")
    if wp.get("approval_target_lifecycle_stage") != "APPROVED_NOT_ACTIVE":
        errors.append("APPROVAL_TARGET_INVALID:wp lifecycle")
    if wp.get("approval_target_gate_status") != "APPROVED_R1":
        errors.append("APPROVAL_TARGET_INVALID:wp gate")
    if wp.get("approval_target_level") != "R1":
        errors.append("APPROVAL_TARGET_INVALID:wp level")
    for name, text in (("task", task), ("matrix", matrix), ("hito", hito), ("tracker", tracker)):
        for line in text.splitlines():
            if re.search(r"H2-CA[23]|Implementation status|Criteria status", line) and re.search(r"`(IMPLEMENTED|PASS|ACCEPTED|CERTIFIED|COMPLETED)`", line):
                errors.append(f"LIFECYCLE_MISMATCH:{name}:premature active status")
    if wp.get("status") != "ACTIVE":
        errors.append("UNAPPROVED_ACTIVE_WP:WP-H2-001 must remain ACTIVE")
    if "Work package activo: `WP-H2-001`" not in state:
        errors.append("UNAPPROVED_ACTIVE_WP:active work package must be WP-H2-001")
    if "active_work_package = WP-H2-001" not in plan:
        errors.append("UNAPPROVED_ACTIVE_WP:plan active work package must be WP-H2-001")
    required_metadata = {
        "approval_digest": APPROVED_DIGEST,
        "approved_candidate_commit": APPROVED_CANDIDATE_COMMIT,
        "approved_level": "R1",
    }
    for field, value in required_metadata.items():
        if wp.get(field) != value:
            errors.append(f"APPROVAL_METADATA_MISMATCH:wp:{field}")
    for field in ("approved_by", "approved_at", "approval_reference", "approval_evidence_sha256"):
        if not wp.get(field):
            errors.append(f"APPROVAL_METADATA_REQUIRED:wp:{field}")
    if wp.get("approved_at") and not UTC_TS.match(str(wp.get("approved_at"))):
        errors.append("APPROVAL_TIMESTAMP_INVALID:wp")
    if wp.get("approval_evidence_sha256") and not HEX64.match(str(wp.get("approval_evidence_sha256"))):
        errors.append("APPROVAL_EVIDENCE_INVALID:wp")
    if not wp.get("activated_at") or not UTC_TS.match(str(wp.get("activated_at"))):
        errors.append("ACTIVATION_METADATA_REQUIRED:wp")
    if "EXECUTE_F12_1_LOCAL_CA2_R1" not in state or "EXECUTE_F12_1_LOCAL_CA2_R1" not in plan:
        errors.append("NEXT_GATE_MISMATCH:F12.1 local CA2 gate must be next")
    if "Pendiente de aprobacion humana por digest" in plan:
        errors.append("NEXT_GATE_MISMATCH:plan still points to digest approval")
    if "proximo gate de aprobacion humana por digest" in adr + plan + tracker + read(root, "operaciones/context_graph_semantico.md"):
        errors.append("NEXT_GATE_MISMATCH:stale digest approval gate text")
    if "WP-H2-001` es la excepcion vigente" not in read(root, "operaciones/context_graph_semantico.md"):
        errors.append("NEXT_GATE_MISMATCH:approved H2 exception must be documented")
    prompt_match = re.search(r"## Proximo Prompt Cavernicola\s+```text\n([\s\S]*?)\n```", tracker)
    prompt = prompt_match.group(1) if prompt_match else ""
    if re.search(r"(R1/R2|hasta R2|grant R2|concede R2)", prompt):
        errors.append("NEXT_GATE_MISMATCH:first H2 prompt must not grant R2")
    if "Supabase Free" not in prompt or "Supabase Pro" not in prompt:
        errors.append("NEXT_GATE_MISMATCH:first H2 prompt must deny Supabase Free and Pro")
    if "Ejecuta las tareas pendientes de la Fase F12.1" not in prompt or "H2-CA2 local R1" not in prompt:
        errors.append("NEXT_GATE_MISMATCH:H2 next prompt must execute F12.1 local CA2")
    if "H2-CA3" not in prompt or "no R3" not in prompt:
        errors.append("NEXT_GATE_MISMATCH:H2 next prompt must deny CA3 and R3")

    if "COMPLETED_OBSIDIAN_CONTEXT_GRAPH" not in state + plan + tracker + evidence:
        errors.append("OBSIDIAN_STAGE_MISMATCH:closure missing")
    if "SUPERSEDED_TOMBSTONE" not in adr0003:
        errors.append("TAXONOMY_TOMBSTONE_MISSING:ADR-0003")
    if "SUPERSEDED_HISTORY" not in release_flow or "F10.9, F11.1, schedules" not in release_flow:
        errors.append("LEGACY_RELEASE_FLOW_AUTHORITY_DRIFT")
    if "SUPERSEDED_TOMBSTONE" not in legacy_evidence or "req_est_001_sprint_1/evidencia_hito_002.md" not in legacy_evidence:
        errors.append("EVIDENCE_NAMESPACE_MISMATCH:legacy tombstone")
    if "Estado: `TEMPLATE_ONLY`. No acredita PASS funcional." not in evidence:
        errors.append("EVIDENCE_STATUS_MISMATCH:H2 evidence must remain template only")

    for name, text in (("hito", hito), ("task", task), ("matrix", matrix), ("plan", plan), ("tracker", tracker)):
        if not H2_CRITERIA <= criteria_from_text(text):
            errors.append(f"CRITERIA_SET_MISMATCH:{name}")
    if wp.get("criteria_status") != {"H2-CA2": "NOT_STARTED", "H2-CA3": "NOT_STARTED"}:
        errors.append("CRITERIA_SET_MISMATCH:wp")
    if re.search(r"H2-CA[23].*`(ACTIVE|IMPLEMENTED|PASS|ACCEPTED|CERTIFIED|COMPLETED)`", tracker + matrix + evidence, re.IGNORECASE):
        errors.append("PREMATURE_ACCEPTANCE:H2 criteria marked accepted before approval")

    for branch, ref in (("Main homologado O3", EXPECTED_BASELINE["main_commit"]), ("Certificacion homologada O4", EXPECTED_BASELINE["certificacion_commit"]), ("Desarrollo homologado O5", EXPECTED_BASELINE["desarrollo_commit"])):
        if ref not in state:
            errors.append(f"BASELINE_DOCUMENT_DRIFT:state missing {branch}")
    if wp.get("baseline") != EXPECTED_BASELINE:
        errors.append("BASELINE_DOCUMENT_DRIFT:wp baseline")
    if "O3 = COMPLETED" not in plan or "O4 = COMPLETED" not in plan or "O5 = COMPLETED" not in plan:
        errors.append("HOMOLOGATION_GATE_STALE:plan")
    for token in ("O0 = COMPLETED", "O1 = COMPLETED", "O2 = COMPLETED"):
        if token not in plan:
            errors.append(f"HOMOLOGATION_GATE_STALE:plan missing {token}")
    for token in ("O0-A preflight | `COMPLETED_READ_ONLY`", "O0-B decision humana | `APPROVED`", "O1 desarrollo | `COMPLETED`", "O2 certificacion | `COMPLETED`"):
        if token not in tracker:
            errors.append(f"HOMOLOGATION_GATE_STALE:tracker missing {token}")
    if re.search(r"\| O[345][^\n]*\| `(BLOCKED|PENDING)[^`]*` \|", state + plan):
        errors.append("HOMOLOGATION_GATE_STALE:O3/O4/O5 stale")
    if "O4 = COMPLETED" not in plan and "READY_FOR_DIGEST_APPROVAL" in state:
        errors.append("GATE_PREREQUISITE_VIOLATION:O4 before H2 gate")

    for section in TRACKER_SECTIONS:
        if section not in tracker:
            errors.append(f"TRACKER_SECTION_MISSING:{section}")
    for link in REQUIRED_INDEX_LINKS:
        if link not in index:
            errors.append(f"INDEX_LINK_MISSING:{link}")
    for level in ("`R0`", "`R1`", "`R2`", "`R3`", "`R3+`"):
        if level not in adr:
            errors.append(f"ADR_AUTH_LEVEL_MISSING:{level}")
    if "contenido en candidate commit" not in adr:
        errors.append("APPROVAL_BINDING_MISSING:ADR-0028")

    try:
        tracked = subprocess.check_output(["git", "ls-files"], cwd=root, text=True, stderr=subprocess.DEVNULL).splitlines()
    except subprocess.CalledProcessError:
        tracked = []
        ignored_dirs = {".git", "node_modules", ".next", "out", ".pytest_cache", "test-results"}
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [dirname for dirname in dirnames if dirname not in ignored_dirs]
            for filename in filenames:
                tracked.append(str((Path(dirpath) / filename).relative_to(root)).replace("\\", "/"))
    tracked_env = [path for path in tracked if (Path(path).name.startswith(".env") or path.endswith(".env")) and Path(path).name != ".env.example"]
    if tracked_env:
        errors.append(f"ENV_FILE_TRACKED:{tracked_env}")
    tracked_sources = [path for path in tracked if Path(path).name in PRIVATE_SOURCE_NAMES or path.lower().endswith(PRIVATE_SOURCE_EXTENSIONS)]
    if tracked_sources:
        errors.append(f"SOURCE_ARTIFACT_TRACKED:{tracked_sources}")
    return errors


def main() -> int:
    errors = validate(ROOT)
    if errors:
        for error in errors:
            print(error)
        return 1
    print("context graph semantic validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
