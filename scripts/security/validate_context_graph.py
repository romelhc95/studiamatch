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
    "arquitectura_pipeline.md",
    "sistema_db_supabase.md",
    "operaciones/matriz_adopcion_db.md",
    "seguimiento/seguimiento_sprint_1_h2_h5.md",
    "seguimiento/plantilla_tracker_reutilizable.md",
    "seguimiento/retrospectiva_hito_001.md",
    "decisiones/ADR-0028_context_graph_semantico_y_autorizacion_r0_r3.md",
    "work_packages/WP-H2-001.json",
    "work_packages/WP-GOV-OBS-001.json",
    "work_packages/WP-GOV-INFRA-001.json",
    "work_packages/WP-GOV-ARCH-001.json",
    "work_packages/WP-GOV-HOM-001.json",
    "work_packages/WP-GOV-CI-001.json",
    "work_packages/WP-GOV-CI-002.json",
    "work_packages/WP-GOV-CI-003.json",
    "work_packages/WP-GOV-CI-004.json",
    "work_packages/WP-GOV-CI-005.json",
    "work_packages/WP-GOV-CI-006.json",
    "work_packages/WP-GOV-CI-007.json",
    "work_packages/WP-GOV-CI-008.json",
    "work_packages/WP-GOV-CI-009.json",
    "work_packages/WP-H3-001.json",
    "work_packages/WP-H4-001.json",
    "work_packages/WP-H5-001.json",
    "matrices/matriz_hito_002.md",
    "evidencias_cliente/req_est_001_sprint_1/evidencia_hito_002.md",
    "backlog_tareas/governance/TASK-GOV-OBS-001.md",
    "backlog_tareas/governance/TASK-GOV-INFRA-001.md",
    "backlog_tareas/governance/TASK-GOV-ARCH-001.md",
    "backlog_tareas/governance/TASK-GOV-HOM-001.md",
    "backlog_tareas/governance/TASK-GOV-CI-001.md",
    "backlog_tareas/governance/TASK-GOV-CI-002.md",
    "backlog_tareas/governance/TASK-GOV-CI-003.md",
    "backlog_tareas/governance/TASK-GOV-CI-004.md",
    "backlog_tareas/governance/TASK-GOV-CI-005.md",
    "backlog_tareas/governance/TASK-GOV-CI-006.md",
    "backlog_tareas/governance/TASK-GOV-CI-007.md",
    "backlog_tareas/governance/TASK-GOV-CI-008.md",
    "backlog_tareas/governance/TASK-GOV-CI-009.md",
    "decisiones/ADR-0029_homologacion_no_recursiva.md",
    "decisiones/ADR-0030_separacion_ci_y_review_gate.md",
    "decisiones/ADR-0031_boundary_homologacion_estructural.md",
    "decisiones/ADR-0032_grant_bootstrap_no_autorreferencial.md",
    "decisiones/ADR-0033_promotion_environment_para_o2_o5.md",
    "decisiones/ADR-0034_post_merge_promotion_push_boundary.md",
    "decisiones/ADR-0035_target_aware_promotions_y_retiro_gates_legacy.md",
    "decisiones/ADR-0036_post_merge_evidence_fail_closed.md",
    "decisiones/ADR-0037_post_merge_route_classification_fail_closed.md",
    "decisiones/ADR-0038_owner_only_protected_branch_updates.md",
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
GOV_OBS_DIGEST = "6a2adee53c4aba66ca9f344f67319b72e624ce17408f73928947b9cc404c5060"
GOV_INFRA_DIGEST = "37ab7416071d6438bfeb91c876d683360ac7a58afd8f22744584f516f2b9fe58"
GOV_OBS_BASE_COMMIT = "486bf420cb0d8ad250bc7b3cceb21545184b4dd5"
GOV_ARCH_BASE_COMMIT = "96c6e7e97a1a6c703eb3b5a3a22f6f6d21aa28e9"
GOV_HOM_BASE_COMMIT = "4cce43a743de5860c4da86eecf1782efab91d26b"
GOV_HOM_BASE_TREE = "ac16b545b74a03b149aac538062def20101187fb"
GOV_CI_BASE_COMMIT = "fddb9cea6ac44a1f7f7b31e93a7b2f2cc0eeacd1"
GOV_CI_BASE_TREE = "5e7d087ac45457264ea29dfc1aa7373efd909290"
GOV_CI2_BASE_COMMIT = "b878c5764e55cb2646b60c4777e363489fe48e8b"
GOV_CI2_BASE_TREE = "174c18efd840fff6ce27fce9fe1dc4edcd65abe8"
GOV_CI3_BASE_COMMIT = "1ac74f78fec6290e214444e9d2f18619ae3fd3b6"
GOV_CI3_BASE_TREE = "8191790192580f2e9fb1ddb48d85ab28714720f9"
GOV_CI4_BASE_COMMIT = "235c2329eb5fd8903c31785640a63466b23f0dd8"
GOV_CI4_BASE_TREE = "cc774746d21cb6649f7018da3049fc811a3f294b"
GOV_CI5_BASE_COMMIT = "32dc50c2a26f0d8cf34c5a39a4f10a821bf821aa"
GOV_CI5_BASE_TREE = "acabd0965d4aa716904917caab691b3867aa5798"
GOV_CI6_BASE_COMMIT = "9f265e41eb4724727e5bd4b1a5cf6ef5c75a4845"
GOV_CI6_BASE_TREE = "fc9ff315d20648e87d049d5fb244a09ea214bfb8"
GOV_CI7_BASE_COMMIT = "26a44af87e4e610d905763b6a5b8c14b64607954"
GOV_CI7_BASE_TREE = "3b956049f3535263b2fdbe3177dc7118005b7af1"
GOV_CI8_BASE_COMMIT = "16045d45811cbe12299ce2ba66f6afd75a93d1ee"
GOV_CI8_BASE_TREE = "29f76f029f9c1c664fd8a9fc2ebda30d75a0a4df"
GOV_CI9_BASE_COMMIT = "1bc36ae6a4381c5ceac5e30c3970c39099965bc3"
GOV_CI9_BASE_TREE = "7df05c52da47855d62c082f7cfbd12ee1e38b965"
GOV_CI9_CERT_COMMIT = "df2cde3626c75fa4733bf1624fb105d8ee08c076"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
UTC_TS = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def read(root: Path, relative: str) -> str:
    try:
        return (root / ".context" / relative).read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def read_repo(root: Path, relative: str) -> str:
    try:
        return (root / relative).read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


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
    gov_task = read(root, "backlog_tareas/governance/TASK-GOV-OBS-001.md")
    gov_infra_task = read(root, "backlog_tareas/governance/TASK-GOV-INFRA-001.md")
    gov_arch_task = read(root, "backlog_tareas/governance/TASK-GOV-ARCH-001.md")
    gov_hom_task = read(root, "backlog_tareas/governance/TASK-GOV-HOM-001.md")
    gov_ci_task = read(root, "backlog_tareas/governance/TASK-GOV-CI-001.md")
    gov_ci2_task = read(root, "backlog_tareas/governance/TASK-GOV-CI-002.md")
    gov_ci3_task = read(root, "backlog_tareas/governance/TASK-GOV-CI-003.md")
    gov_ci4_task = read(root, "backlog_tareas/governance/TASK-GOV-CI-004.md")
    gov_ci5_task = read(root, "backlog_tareas/governance/TASK-GOV-CI-005.md")
    gov_ci6_task = read(root, "backlog_tareas/governance/TASK-GOV-CI-006.md")
    gov_ci7_task = read(root, "backlog_tareas/governance/TASK-GOV-CI-007.md")
    gov_ci8_task = read(root, "backlog_tareas/governance/TASK-GOV-CI-008.md")
    gov_ci9_task = read(root, "backlog_tareas/governance/TASK-GOV-CI-009.md")
    architecture = read(root, "arquitectura_pipeline.md")
    db_system = read(root, "sistema_db_supabase.md")
    db_matrix = read(root, "operaciones/matriz_adopcion_db.md")
    wp = json.loads((root / ".context" / "work_packages" / "WP-H2-001.json").read_text(encoding="utf-8"))
    gov_wp = json.loads((root / ".context" / "work_packages" / "WP-GOV-OBS-001.json").read_text(encoding="utf-8"))
    gov_infra_wp = json.loads((root / ".context" / "work_packages" / "WP-GOV-INFRA-001.json").read_text(encoding="utf-8"))
    gov_arch_wp = json.loads((root / ".context" / "work_packages" / "WP-GOV-ARCH-001.json").read_text(encoding="utf-8"))
    gov_hom_wp = json.loads((root / ".context" / "work_packages" / "WP-GOV-HOM-001.json").read_text(encoding="utf-8"))
    gov_ci_wp = json.loads((root / ".context" / "work_packages" / "WP-GOV-CI-001.json").read_text(encoding="utf-8"))
    gov_ci2_wp = json.loads((root / ".context" / "work_packages" / "WP-GOV-CI-002.json").read_text(encoding="utf-8"))
    gov_ci3_wp = json.loads((root / ".context" / "work_packages" / "WP-GOV-CI-003.json").read_text(encoding="utf-8"))
    gov_ci4_wp = json.loads((root / ".context" / "work_packages" / "WP-GOV-CI-004.json").read_text(encoding="utf-8"))
    gov_ci5_wp = json.loads((root / ".context" / "work_packages" / "WP-GOV-CI-005.json").read_text(encoding="utf-8"))
    gov_ci6_wp = json.loads((root / ".context" / "work_packages" / "WP-GOV-CI-006.json").read_text(encoding="utf-8"))
    gov_ci7_wp = json.loads((root / ".context" / "work_packages" / "WP-GOV-CI-007.json").read_text(encoding="utf-8"))
    gov_ci8_wp = json.loads((root / ".context" / "work_packages" / "WP-GOV-CI-008.json").read_text(encoding="utf-8"))
    gov_ci9_wp = json.loads((root / ".context" / "work_packages" / "WP-GOV-CI-009.json").read_text(encoding="utf-8"))

    if linked_id(bullet_value(state, "Hito")) != "HITO-002":
        errors.append("GRAPH_ID_MISMATCH:state active hito must be HITO-002")
    if linked_id(bullet_value(state, "Tarea")) != "TASK-H2-001":
        errors.append("GRAPH_ID_MISMATCH:state active task must be TASK-H2-001")
    if "WP-H2-001=ACTIVE_R1" not in state:
        errors.append("GRAPH_ID_MISMATCH:state must reference WP-H2-001 as active R1")
    if "Subfase tecnica activa: `F10.11`" not in state:
        errors.append("EXECUTION_PHASE_MISMATCH:state must remain F10.11 until Obsidian reaches main")
    if "`F12.1` | `BLOCKED_PENDING_HOMOLOGATION_AND_REBASE`" not in state or "`F12.2` | `BLOCKED_BY_F12_1_CA2`" not in state:
        errors.append("EXECUTION_PHASE_MISMATCH:F12 taxonomy missing")
    if wp.get("id") != "WP-H2-001" or wp.get("task_id") != "TASK-H2-001" or wp.get("hito") != "HITO-002":
        errors.append("GRAPH_ID_MISMATCH:WP-H2-001 IDs")

    expected = {
        "Lifecycle stage": "ACTIVE",
        "Gate status": "APPROVED_R1",
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
    if "BLOCKED_PENDING_HOMOLOGATION_AND_REBASE" not in state + plan + tracker + evidence:
        errors.append("LIFECYCLE_MISMATCH:homologation/rebase blocker missing")
    if table_value(hito, "Implementation status") != "BLOCKED_PENDING_OBSIDIAN_MAIN" or table_value(task, "Implementation status") != "BLOCKED_PENDING_OBSIDIAN_MAIN":
        errors.append("LIFECYCLE_MISMATCH:hito/task implementation status must remain not-started pre-rebase")
    if wp.get("lifecycle_stage") != "ACTIVE" or wp.get("implementation_status") != "BLOCKED_PENDING_OBSIDIAN_MAIN":
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
    if "COMPLETE_WP_GOV_CI_009_R1_LOCAL_VALIDATION" not in state or "COMPLETE_WP_GOV_CI_009_R1_LOCAL_VALIDATION" not in plan or "COMPLETE_WP_GOV_CI_009_R1_LOCAL_VALIDATION" not in tracker:
        errors.append("NEXT_GATE_MISMATCH:GOV CI9 R1 local validation gate must be next")
    if "COMPLETE_WP_GOV_CI_008_R1_LOCAL_VALIDATION" in state + plan + tracker or "PREPARE_WP_GOV_CI_007_R2_APPROVAL" in state + plan + tracker:
        errors.append("NEXT_GATE_MISMATCH:stale GOV CI7/CI8 gate")
    if "PREPARE_WP_GOV_CI_006_R2_APPROVAL" in state + plan + tracker:
        errors.append("NEXT_GATE_MISMATCH:stale GOV CI6 R2 gate")
    if "PREPARE_WP_GOV_CI_005_R2_APPROVAL" in state + plan + tracker:
        errors.append("NEXT_GATE_MISMATCH:stale GOV CI5 R2 gate")
    if "PREPARE_WP_GOV_CI_004_R2_APPROVAL" in state + plan + tracker:
        errors.append("NEXT_GATE_MISMATCH:stale GOV CI4 R2 gate")
    if "PREPARE_WP_GOV_CI_003_R2_APPROVAL" in state + plan + tracker:
        errors.append("NEXT_GATE_MISMATCH:stale GOV CI3 R2 gate")
    if "PREPARE_WP_GOV_CI_002_R2_APPROVAL" in state + plan + tracker:
        errors.append("NEXT_GATE_MISMATCH:stale GOV CI2 R2 gate")
    if "PREPARE_WP_GOV_CI_001_R2_APPROVAL" in state + plan + tracker:
        errors.append("NEXT_GATE_MISMATCH:stale GOV CI1 R2 gate")
    if "PREPARE_WP_GOV_HOM_R2_APPROVAL" in state + plan + tracker:
        errors.append("NEXT_GATE_MISMATCH:stale GOV HOM R2 gate")
    if "PREPARE_WP_GOV_ARCH_R2_APPROVAL" in state + plan + tracker + evidence + read(root, "operaciones/context_graph_semantico.md"):
        errors.append("NEXT_GATE_MISMATCH:stale GOV ARCH R2 gate")
    if "PREPARE_WP_GOV_OBS_INFRA_R2_APPROVAL" in state + plan + tracker:
        errors.append("NEXT_GATE_MISMATCH:stale GOV OBS/INFRA R2 gate")
    if "PREPARE_WP_GOV_OBS_R2_APPROVAL" in state + plan + tracker + evidence + read(root, "operaciones/context_graph_semantico.md"):
        errors.append("NEXT_GATE_MISMATCH:stale OBS-only R2 gate")
    if "WP-GOV-INFRA-001" not in state or "WP-GOV-INFRA-001" not in plan:
        errors.append("GOV_INFRA_WP_INVALID:missing from canonical authority")
    if "WP-GOV-CI-003" not in state or "WP-GOV-CI-003" not in plan or "TASK-GOV-CI-003" not in gov_ci3_task:
        errors.append("GOV_CI3_WP_INVALID:missing from canonical authority")
    if "WP-GOV-CI-004" not in state or "WP-GOV-CI-004" not in plan or "TASK-GOV-CI-004" not in gov_ci4_task:
        errors.append("GOV_CI4_WP_INVALID:missing from canonical authority")
    if "WP-GOV-CI-005" not in state or "WP-GOV-CI-005" not in plan or "TASK-GOV-CI-005" not in gov_ci5_task:
        errors.append("GOV_CI5_WP_INVALID:missing from canonical authority")
    if "WP-GOV-CI-006" not in state or "WP-GOV-CI-006" not in plan or "TASK-GOV-CI-006" not in gov_ci6_task:
        errors.append("GOV_CI6_WP_INVALID:missing from canonical authority")
    if "WP-GOV-CI-007" not in state or "WP-GOV-CI-007" not in plan or "TASK-GOV-CI-007" not in gov_ci7_task:
        errors.append("GOV_CI7_WP_INVALID:missing from canonical authority")
    if "WP-GOV-CI-008" not in state or "WP-GOV-CI-008" not in plan or "TASK-GOV-CI-008" not in gov_ci8_task:
        errors.append("GOV_CI8_WP_INVALID:missing from canonical authority")
    if "WP-GOV-CI-009" not in state or "WP-GOV-CI-009" not in plan or "TASK-GOV-CI-009" not in gov_ci9_task:
        errors.append("GOV_CI9_WP_INVALID:missing from canonical authority")
    if "EXECUTE_F12_1_LOCAL_CA2_R1" in state + plan + tracker:
        errors.append("NEXT_GATE_MISMATCH:F12.1 must remain blocked pending main")
    if "Pendiente de aprobacion humana por digest" in plan:
        errors.append("NEXT_GATE_MISMATCH:plan still points to digest approval")
    if "proximo gate de aprobacion humana por digest" in adr + plan + tracker + read(root, "operaciones/context_graph_semantico.md"):
        errors.append("NEXT_GATE_MISMATCH:stale digest approval gate text")
    if "WP-H2-001` es la excepcion vigente" not in read(root, "operaciones/context_graph_semantico.md"):
        errors.append("NEXT_GATE_MISMATCH:approved H2 exception must be documented")
    prompt_match = re.search(r"## Proximo Prompt Cavernicola\s+```text\n([\s\S]*?)\n```", tracker)
    prompt = prompt_match.group(1) if prompt_match else ""
    if re.search(r"WP-H2-001[\s\S]{0,160}(R1/R2|hasta R2|grant R2|concede R2)", prompt):
        errors.append("NEXT_GATE_MISMATCH:H2 prompt must not grant R2")
    if "Supabase Free" not in prompt or "Supabase Pro" not in prompt:
        errors.append("NEXT_GATE_MISMATCH:first H2 prompt must deny Supabase Free and Pro")
    if "Ejecuta las tareas pendientes de la Fase" in prompt:
        errors.append("LEGACY_PHASE_PROMPT_AUTHORITY_DRIFT")
    if "Apruebo WP-GOV-CI-009 de TASK-GOV-CI-009 segun manifest sha256:<D_CI9>" not in prompt:
        errors.append("NEXT_GATE_MISMATCH:GOV CI9 approval prompt missing digest placeholder")
    if "hasta R2" not in prompt or "no Certification, no Main y no R3" not in prompt:
        errors.append("NEXT_GATE_MISMATCH:GOV HOM prompt must be R2 only")

    if "DESARROLLO_MERGED_PENDING_HOMOLOGATION" not in state + plan + tracker + evidence:
        errors.append("OBSIDIAN_STAGE_MISMATCH:pending homologation status missing")
    if "COMPLETED_OBSIDIAN_CONTEXT_GRAPH" in state + plan + tracker + evidence and "MAIN_HOMOLOGATED_CONSUMED" not in state + plan + tracker + evidence:
        errors.append("OBSIDIAN_STAGE_MISMATCH:cannot complete before main homologation consumption")
    if "SUPERSEDED_TOMBSTONE" not in adr0003:
        errors.append("TAXONOMY_TOMBSTONE_MISSING:ADR-0003")
    if "SUPERSEDED_HISTORY" not in release_flow or "F10.9, F11.1, schedules" not in release_flow:
        errors.append("LEGACY_RELEASE_FLOW_AUTHORITY_DRIFT")
    if "SUPERSEDED_TOMBSTONE" not in legacy_evidence or "req_est_001_sprint_1/evidencia_hito_002.md" not in legacy_evidence:
        errors.append("EVIDENCE_NAMESPACE_MISMATCH:legacy tombstone")
    if "Estado: `TEMPLATE_ONLY`. No acredita PASS funcional." not in evidence:
        errors.append("EVIDENCE_STATUS_MISMATCH:H2 evidence must remain template only")
    if gov_wp.get("id") != "WP-GOV-OBS-001" or gov_wp.get("task_id") != "TASK-GOV-OBS-001" or gov_wp.get("status") != "PROPOSED":
        errors.append("GOV_OBS_WP_INVALID:identity/status")
    if gov_wp.get("candidate_digest") != GOV_OBS_DIGEST or gov_wp.get("target_level") != "R2":
        errors.append("GOV_OBS_WP_INVALID:digest/target")
    if gov_wp.get("baseline", {}).get("candidate_commit") != GOV_OBS_BASE_COMMIT:
        errors.append("GOV_OBS_WP_INVALID:baseline")
    if "PROPOSED_R2_PENDING_DIGEST_APPROVAL" not in gov_task:
        errors.append("GOV_OBS_TASK_INVALID:status")
    if gov_infra_wp.get("id") != "WP-GOV-INFRA-001" or gov_infra_wp.get("task_id") != "TASK-GOV-INFRA-001" or gov_infra_wp.get("status") != "PROPOSED":
        errors.append("GOV_INFRA_WP_INVALID:identity/status")
    if gov_infra_wp.get("candidate_digest") != GOV_INFRA_DIGEST or gov_infra_wp.get("target_level") != "R2":
        errors.append("GOV_INFRA_WP_INVALID:digest/target")
    if gov_infra_wp.get("allowed_paths") != [".github/workflows/security-audit.yml", "docker-compose.h2-test.yml", "scripts/security/run_h2_r1_tests.sh"]:
        errors.append("GOV_INFRA_WP_INVALID:allowlist")
    if "PROPOSED_R2_PENDING_DIGEST_APPROVAL" not in gov_infra_task:
        errors.append("GOV_INFRA_TASK_INVALID:status")
    if gov_arch_wp.get("id") != "WP-GOV-ARCH-001" or gov_arch_wp.get("task_id") != "TASK-GOV-ARCH-001" or gov_arch_wp.get("status") != "PROPOSED":
        errors.append("GOV_ARCH_WP_INVALID:identity/status")
    if gov_arch_wp.get("target_level") != "R2":
        errors.append("GOV_ARCH_WP_INVALID:target")
    if gov_arch_wp.get("baseline", {}).get("candidate_commit") != GOV_ARCH_BASE_COMMIT:
        errors.append("GOV_ARCH_WP_INVALID:baseline")
    if "COMPLETED_EXTERNALLY_BY_PR_425" not in gov_arch_task:
        errors.append("GOV_ARCH_TASK_INVALID:status")
    if gov_hom_wp.get("id") != "WP-GOV-HOM-001" or gov_hom_wp.get("task_id") != "TASK-GOV-HOM-001" or gov_hom_wp.get("status") != "PROPOSED":
        errors.append("GOV_HOM_WP_INVALID:identity/status")
    if gov_hom_wp.get("target_level") != "R2":
        errors.append("GOV_HOM_WP_INVALID:target")
    if gov_hom_wp.get("baseline", {}).get("candidate_commit") != GOV_HOM_BASE_COMMIT or gov_hom_wp.get("baseline", {}).get("candidate_tree") != GOV_HOM_BASE_TREE:
        errors.append("GOV_HOM_WP_INVALID:baseline")
    grants = gov_hom_wp.get("homologation_grants", [])
    if not isinstance(grants, list) or len(grants) != 4 or any(grant.get("status") != "TEMPLATE_ONLY_NOT_GRANTED" for grant in grants if isinstance(grant, dict)):
        errors.append("GOV_HOM_GRANTS_INVALID:templates")
    if "tree(main) == tree(certificacion) == tree(desarrollo) == T_HOM" not in "\n".join(str(item) for item in gov_hom_wp.get("closure_predicate", [])):
        errors.append("GOV_HOM_CLOSURE_PREDICATE_REQUIRED")
    if "PROPOSED_R2_PENDING_DIGEST_APPROVAL" not in gov_hom_task:
        errors.append("GOV_HOM_TASK_INVALID:status")
    if gov_ci_wp.get("id") != "WP-GOV-CI-001" or gov_ci_wp.get("task_id") != "TASK-GOV-CI-001" or gov_ci_wp.get("status") != "PROPOSED":
        errors.append("GOV_CI_WP_INVALID:identity/status")
    if gov_ci_wp.get("target_level") != "R2":
        errors.append("GOV_CI_WP_INVALID:target")
    if gov_ci_wp.get("baseline", {}).get("candidate_commit") != GOV_CI_BASE_COMMIT or gov_ci_wp.get("baseline", {}).get("candidate_tree") != GOV_CI_BASE_TREE:
        errors.append("GOV_CI_WP_INVALID:baseline")
    decoupling = gov_ci_wp.get("ci_review_decoupling", {})
    if decoupling.get("reviews_trigger_ci") is not False or decoupling.get("reviews_api_used") is not False or decoupling.get("manual_rerun_required_for_review") is not False:
        errors.append("GOV_CI_DECOUPLING_INVALID")
    if "PROPOSED_R2_PENDING_DIGEST_APPROVAL" not in gov_ci_task:
        errors.append("GOV_CI_TASK_INVALID:status")
    if gov_ci2_wp.get("id") != "WP-GOV-CI-002" or gov_ci2_wp.get("task_id") != "TASK-GOV-CI-002" or gov_ci2_wp.get("status") != "PROPOSED":
        errors.append("GOV_CI2_WP_INVALID:identity/status")
    if gov_ci2_wp.get("target_level") != "R2":
        errors.append("GOV_CI2_WP_INVALID:target")
    if gov_ci2_wp.get("baseline", {}).get("candidate_commit") != GOV_CI2_BASE_COMMIT or gov_ci2_wp.get("baseline", {}).get("candidate_tree") != GOV_CI2_BASE_TREE:
        errors.append("GOV_CI2_WP_INVALID:baseline")
    promotion_boundary = gov_ci2_wp.get("promotion_boundary", {})
    if promotion_boundary.get("incremental_boundary_preserved") is not True or len(promotion_boundary.get("structural_pairs", [])) != 4:
        errors.append("GOV_CI2_PROMOTION_BOUNDARY_INVALID")
    if "PROPOSED_R2_PENDING_DIGEST_APPROVAL" not in gov_ci2_task:
        errors.append("GOV_CI2_TASK_INVALID:status")
    if gov_ci3_wp.get("id") != "WP-GOV-CI-003" or gov_ci3_wp.get("task_id") != "TASK-GOV-CI-003" or gov_ci3_wp.get("status") != "PROPOSED":
        errors.append("GOV_CI3_WP_INVALID:identity/status")
    if gov_ci3_wp.get("target_level") != "R2":
        errors.append("GOV_CI3_WP_INVALID:target")
    if gov_ci3_wp.get("baseline", {}).get("candidate_commit") != GOV_CI3_BASE_COMMIT or gov_ci3_wp.get("baseline", {}).get("candidate_tree") != GOV_CI3_BASE_TREE:
        errors.append("GOV_CI3_WP_INVALID:baseline")
    bootstrap = gov_ci3_wp.get("promotion_request_bootstrap", {})
    if bootstrap.get("static_request_status") != "REQUESTED_JIT_SINGLE_USE" or bootstrap.get("final_wp") != "WP-GOV-CI-003" or len(bootstrap.get("grant_request_ids", [])) != 4:
        errors.append("GOV_CI3_BOOTSTRAP_INVALID")
    if "CANDIDATE_R1_LOCAL" not in gov_ci3_task:
        errors.append("GOV_CI3_TASK_INVALID:status")
    if gov_ci4_wp.get("id") != "WP-GOV-CI-004" or gov_ci4_wp.get("task_id") != "TASK-GOV-CI-004" or gov_ci4_wp.get("status") != "PROPOSED":
        errors.append("GOV_CI4_WP_INVALID:identity/status")
    if gov_ci4_wp.get("target_level") != "R2":
        errors.append("GOV_CI4_WP_INVALID:target")
    if gov_ci4_wp.get("baseline", {}).get("candidate_commit") != GOV_CI4_BASE_COMMIT or gov_ci4_wp.get("baseline", {}).get("candidate_tree") != GOV_CI4_BASE_TREE:
        errors.append("GOV_CI4_WP_INVALID:baseline")
    remediation = gov_ci4_wp.get("promotion_environment_remediation", {})
    if remediation.get("environment") != "Promotion" or remediation.get("failed_pr") != 431 or remediation.get("consumed_grant") != "R3-GOV-HOM-003-O2-REQ1":
        errors.append("GOV_CI4_PROMOTION_ENVIRONMENT_INVALID")
    if "CANDIDATE_R1_LOCAL" not in gov_ci4_task:
        errors.append("GOV_CI4_TASK_INVALID:status")
    if gov_ci5_wp.get("id") != "WP-GOV-CI-005" or gov_ci5_wp.get("task_id") != "TASK-GOV-CI-005" or gov_ci5_wp.get("status") != "PROPOSED":
        errors.append("GOV_CI5_WP_INVALID:identity/status")
    if gov_ci5_wp.get("target_level") != "R2":
        errors.append("GOV_CI5_WP_INVALID:target")
    if gov_ci5_wp.get("baseline", {}).get("candidate_commit") != GOV_CI5_BASE_COMMIT or gov_ci5_wp.get("baseline", {}).get("candidate_tree") != GOV_CI5_BASE_TREE:
        errors.append("GOV_CI5_WP_INVALID:baseline")
    post_merge = gov_ci5_wp.get("post_merge_promotion_push_boundary", {})
    required_evidence = post_merge.get("required_evidence", [])
    if post_merge.get("failed_run") != 32615044699 or post_merge.get("fallback") != "incremental_boundary" or "associated_pr_by_api" not in required_evidence:
        errors.append("GOV_CI5_POST_MERGE_BOUNDARY_INVALID")
    bootstrap5 = gov_ci5_wp.get("promotion_request_bootstrap", {})
    if bootstrap5.get("static_request_status") != "REQUESTED_JIT_SINGLE_USE" or bootstrap5.get("final_wp") != "WP-GOV-CI-005" or len(bootstrap5.get("grant_request_ids", [])) != 4:
        errors.append("GOV_CI5_BOOTSTRAP_INVALID")
    if "CANDIDATE_R1_LOCAL" not in gov_ci5_task:
        errors.append("GOV_CI5_TASK_INVALID:status")
    if gov_ci6_wp.get("id") != "WP-GOV-CI-006" or gov_ci6_wp.get("task_id") != "TASK-GOV-CI-006" or gov_ci6_wp.get("status") != "PROPOSED":
        errors.append("GOV_CI6_WP_INVALID:identity/status")
    if gov_ci6_wp.get("target_level") != "R2":
        errors.append("GOV_CI6_WP_INVALID:target")
    if gov_ci6_wp.get("baseline", {}).get("candidate_commit") != GOV_CI6_BASE_COMMIT or gov_ci6_wp.get("baseline", {}).get("candidate_tree") != GOV_CI6_BASE_TREE:
        errors.append("GOV_CI6_WP_INVALID:baseline")
    target_aware = gov_ci6_wp.get("target_aware_promotion_model", {})
    if target_aware.get("static_request_status") != "REQUESTED_JIT_SINGLE_USE" or target_aware.get("final_wp") != "WP-GOV-CI-006" or len(target_aware.get("grant_request_ids", [])) != 4:
        errors.append("GOV_CI6_TARGET_AWARE_INVALID")
    legacy_retirement = gov_ci6_wp.get("legacy_gate_retirement", {})
    if legacy_retirement.get("mode") != "MANUAL_FROZEN_ONLY" or legacy_retirement.get("workflow") != ".github/workflows/f9-7-contract.yml":
        errors.append("GOV_CI6_LEGACY_RETIREMENT_INVALID")
    if "CANDIDATE_R1_LOCAL" not in gov_ci6_task:
        errors.append("GOV_CI6_TASK_INVALID:status")
    if gov_ci7_wp.get("id") != "WP-GOV-CI-007" or gov_ci7_wp.get("task_id") != "TASK-GOV-CI-007" or gov_ci7_wp.get("status") != "PROPOSED":
        errors.append("GOV_CI7_WP_INVALID:identity/status")
    if gov_ci7_wp.get("target_level") != "R2":
        errors.append("GOV_CI7_WP_INVALID:target")
    if gov_ci7_wp.get("baseline", {}).get("candidate_commit") != GOV_CI7_BASE_COMMIT or gov_ci7_wp.get("baseline", {}).get("candidate_tree") != GOV_CI7_BASE_TREE:
        errors.append("GOV_CI7_WP_INVALID:baseline")
    fail_closed = gov_ci7_wp.get("post_merge_evidence_fail_closed", {})
    if fail_closed.get("tri_state") != ["VERIFIED_PROMOTION", "NOT_APPLICABLE", "BLOCKED"] or fail_closed.get("failed_pr") != 437 or fail_closed.get("failed_run") != 32650341464:
        errors.append("GOV_CI7_FAIL_CLOSED_INVALID")
    bootstrap7 = gov_ci7_wp.get("promotion_request_bootstrap", {})
    if bootstrap7.get("static_request_status") != "REQUESTED_JIT_SINGLE_USE" or bootstrap7.get("final_wp") != "WP-GOV-CI-007" or len(bootstrap7.get("grant_request_ids", [])) != 4:
        errors.append("GOV_CI7_BOOTSTRAP_INVALID")
    if "CANDIDATE_R1_LOCAL" not in gov_ci7_task:
        errors.append("GOV_CI7_TASK_INVALID:status")
    if gov_ci8_wp.get("id") != "WP-GOV-CI-008" or gov_ci8_wp.get("task_id") != "TASK-GOV-CI-008" or gov_ci8_wp.get("status") != "PROPOSED":
        errors.append("GOV_CI8_WP_INVALID:identity/status")
    if gov_ci8_wp.get("target_level") != "R2":
        errors.append("GOV_CI8_WP_INVALID:target")
    if gov_ci8_wp.get("baseline", {}).get("candidate_commit") != GOV_CI8_BASE_COMMIT or gov_ci8_wp.get("baseline", {}).get("candidate_tree") != GOV_CI8_BASE_TREE:
        errors.append("GOV_CI8_WP_INVALID:baseline")
    route_classification = gov_ci8_wp.get("route_classification_fail_closed", {})
    if route_classification.get("tri_state") != ["VERIFIED_PROMOTION", "NOT_APPLICABLE", "BLOCKED"] or route_classification.get("failed_pr") != 438 or route_classification.get("failed_run") != 32655520324:
        errors.append("GOV_CI8_ROUTE_CLASSIFICATION_INVALID")
    bootstrap8 = gov_ci8_wp.get("promotion_request_bootstrap", {})
    if bootstrap8.get("static_request_status") != "REQUESTED_JIT_SINGLE_USE" or bootstrap8.get("final_wp") != "WP-GOV-CI-008" or len(bootstrap8.get("grant_request_ids", [])) != 4:
        errors.append("GOV_CI8_BOOTSTRAP_INVALID")
    if "CANDIDATE_R1_LOCAL" not in gov_ci8_task:
        errors.append("GOV_CI8_TASK_INVALID:status")
    if gov_ci9_wp.get("id") != "WP-GOV-CI-009" or gov_ci9_wp.get("task_id") != "TASK-GOV-CI-009" or gov_ci9_wp.get("status") != "PROPOSED":
        errors.append("GOV_CI9_WP_INVALID:identity/status")
    if gov_ci9_wp.get("target_level") != "R2":
        errors.append("GOV_CI9_WP_INVALID:target")
    if gov_ci9_wp.get("baseline", {}).get("candidate_commit") != GOV_CI9_BASE_COMMIT or gov_ci9_wp.get("baseline", {}).get("candidate_tree") != GOV_CI9_BASE_TREE:
        errors.append("GOV_CI9_WP_INVALID:baseline")
    owner_only = gov_ci9_wp.get("owner_only_protected_branch_updates", {})
    if owner_only.get("name") != "owner-only-protected-branch-updates" or owner_only.get("refs") != ["refs/heads/desarrollo", "refs/heads/certificacion", "refs/heads/main"]:
        errors.append("GOV_CI9_OWNER_ONLY_INVALID")
    if owner_only.get("bypass_user") != "romelhc95" or owner_only.get("bypass_user_id") != 18040405 or owner_only.get("excluded_user") != "romelhc95-approver" or owner_only.get("excluded_user_id") != 306979205:
        errors.append("GOV_CI9_OWNER_ONLY_ACTORS_INVALID")
    failure9 = gov_ci9_wp.get("post_merge_merger_identity_failure", {})
    if failure9.get("failed_pr") != 440 or failure9.get("failed_run") != 32662084712 or failure9.get("primary_failure") != "POST_MERGE_MERGER_INVALID":
        errors.append("GOV_CI9_FAILURE_INVALID")
    if failure9.get("reviewer") != "romelhc95-approver" or failure9.get("observed_merger") != "romelhc95-approver" or failure9.get("required_merger") != "romelhc95":
        errors.append("GOV_CI9_IDENTITY_INVALID")
    bootstrap9 = gov_ci9_wp.get("promotion_request_bootstrap", {})
    if bootstrap9.get("static_request_status") != "REQUESTED_JIT_SINGLE_USE" or bootstrap9.get("final_wp") != "WP-GOV-CI-009" or len(bootstrap9.get("grant_request_ids", [])) != 4:
        errors.append("GOV_CI9_BOOTSTRAP_INVALID")
    if "CANDIDATE_R1_LOCAL" not in gov_ci9_task:
        errors.append("GOV_CI9_TASK_INVALID:status")
    if "PR #424" not in state or "MERGED_TO_DESARROLLO" not in state or "96c6e7e97a1a6c703eb3b5a3a22f6f6d21aa28e9" not in state + tracker + plan:
        errors.append("GOV_OBS_INFRA_R2_HISTORY_MISSING:PR424")
    if "PR #425" not in state or GOV_HOM_BASE_COMMIT not in state + tracker + plan or GOV_HOM_BASE_TREE not in state + tracker + plan:
        errors.append("GOV_HOM_R2_HISTORY_MISSING:PR425")
    if "PR #426" not in state or GOV_CI_BASE_COMMIT not in state + tracker + plan or GOV_CI_BASE_TREE not in state + tracker + plan:
        errors.append("GOV_CI_R2_HISTORY_MISSING:PR426")
    if "PR #427" not in state or GOV_CI2_BASE_COMMIT not in state + tracker + plan or GOV_CI2_BASE_TREE not in state + tracker + plan:
        errors.append("GOV_CI2_R2_HISTORY_MISSING:PR427")
    if "PR #429" not in state or GOV_CI3_BASE_COMMIT not in state + tracker + plan or GOV_CI3_BASE_TREE not in state + tracker + plan:
        errors.append("GOV_CI3_R2_HISTORY_MISSING:PR429")
    if "PR #428" not in state + tracker + plan or "O2_CONSUMED_BY_FAILURE" not in state + tracker + plan:
        errors.append("GOV_CI2_FAILURE_HISTORY_MISSING:PR428")
    if "PR #430" not in state or GOV_CI4_BASE_COMMIT not in state + tracker + plan or GOV_CI4_BASE_TREE not in state + tracker + plan:
        errors.append("GOV_CI4_R2_HISTORY_MISSING:PR430")
    if "PR #431" not in state + tracker + plan or "R3-GOV-HOM-003-O2-REQ1" not in state + tracker + plan:
        errors.append("GOV_CI4_FAILURE_HISTORY_MISSING:PR431")
    if "PR #432" not in state or GOV_CI5_BASE_COMMIT not in state + tracker + plan or GOV_CI5_BASE_TREE not in state + tracker + plan:
        errors.append("GOV_CI5_R2_HISTORY_MISSING:PR432")
    if "PR #433" not in state + tracker + plan or "R3-GOV-HOM-004-O2-REQ1" not in state + tracker + plan or "32615044699" not in state + tracker + plan:
        errors.append("GOV_CI5_FAILURE_HISTORY_MISSING:PR433")
    if "PR #434" not in state or GOV_CI6_BASE_COMMIT not in state + tracker + plan or GOV_CI6_BASE_TREE not in state + tracker + plan:
        errors.append("GOV_CI6_R2_HISTORY_MISSING:PR434")
    if "PR #435" not in state + tracker + plan or "R3-GOV-HOM-005-O2-REQ1" not in state + tracker + plan or "32619372008" not in state + tracker + plan:
        errors.append("GOV_CI6_FAILURE_HISTORY_MISSING:PR435")
    if "PR #436" not in state or GOV_CI7_BASE_COMMIT not in state + tracker + plan or GOV_CI7_BASE_TREE not in state + tracker + plan:
        errors.append("GOV_CI7_R2_HISTORY_MISSING:PR436")
    if "PR #437" not in state + tracker + plan or "R3-GOV-HOM-006-O2-REQ1" not in state + tracker + plan or "32650341464" not in state + tracker + plan or "merged_by=romelhc95-approver" not in state + tracker + plan:
        errors.append("GOV_CI7_FAILURE_HISTORY_MISSING:PR437")
    if "PR #438" not in state + tracker + plan or GOV_CI8_BASE_COMMIT not in state + tracker + plan or GOV_CI8_BASE_TREE not in state + tracker + plan or "32655520324" not in state + tracker + plan:
        errors.append("GOV_CI8_FAILURE_HISTORY_MISSING:PR438")
    if "PR #439" not in state + tracker + plan or GOV_CI9_BASE_COMMIT not in state + tracker + plan or GOV_CI9_BASE_TREE not in state + tracker + plan or "32659464257" not in state + tracker + plan:
        errors.append("GOV_CI8_R2_HISTORY_MISSING:PR439")
    if "PR #440" not in state + tracker + plan or GOV_CI9_CERT_COMMIT not in state + tracker + plan or "32662084712" not in state + tracker + plan or "POST_MERGE_MERGER_INVALID" not in state + tracker + plan:
        errors.append("GOV_CI9_FAILURE_HISTORY_MISSING:PR440")
    if "owner-only-protected-branch-updates" not in state + plan + tracker + architecture + release_flow or "romelhc95-approver" not in state + plan + tracker + architecture + release_flow or "actor_id=18040405" not in state + plan + tracker + architecture + release_flow:
        errors.append("GOV_CI9_OWNER_ONLY_HISTORY_MISSING")
    canonical_docs = (
        ("ARCHITECTURE_CANONICAL_MISSING:arquitectura_pipeline", architecture),
        ("ARCHITECTURE_CANONICAL_MISSING:sistema_db_supabase", db_system),
        ("ARCHITECTURE_CANONICAL_MISSING:matriz_adopcion_db", db_matrix),
    )
    for prefix, text in canonical_docs:
        if "Fuente canonica" not in text or "Snapshot de investigacion" not in text:
            errors.append(prefix)
    if "staging_raw" not in architecture + db_system or "cleansed_programs" not in architecture + db_system or "enriched_programs" not in architecture + db_system or "courses" not in architecture + db_system:
        errors.append("ARCHITECTURE_CANONICAL_MISSING:pipeline lineage")
    production_arch = read_repo(root, "docs/orquestador-sdlc/PRODUCTION_ARCHITECTURE.md")
    workflow_arch = read_repo(root, "docs/architecture/Documento_Detallado_workflow.md")
    if production_arch and "SUPERSEDED_HISTORY" not in production_arch:
        errors.append("ARCHITECTURE_LEGACY_SOURCE_DRIFT:production architecture")
    if workflow_arch and "SUPERSEDED_HISTORY" not in workflow_arch:
        errors.append("ARCHITECTURE_LEGACY_SOURCE_DRIFT:workflow document")

    for name, text in (("hito", hito), ("task", task), ("matrix", matrix), ("plan", plan), ("tracker", tracker)):
        if not H2_CRITERIA <= criteria_from_text(text):
            errors.append(f"CRITERIA_SET_MISMATCH:{name}")
    if wp.get("criteria_status") != {"H2-CA2": "NOT_STARTED", "H2-CA3": "NOT_STARTED"}:
        errors.append("CRITERIA_SET_MISMATCH:wp")
    if re.search(r"H2-CA[23].*`(ACTIVE|IMPLEMENTED|PASS|ACCEPTED|CERTIFIED|COMPLETED)`", tracker + matrix + evidence, re.IGNORECASE):
        errors.append("PREMATURE_ACCEPTANCE:H2 criteria marked accepted before approval")
    if "H2-CA2 | `ACTIVE`" in tracker + plan or "H2-CA2 | `IMPLEMENTED`" in tracker + plan:
        errors.append("PREMATURE_ACCEPTANCE:H2 started before homologation/rebase")

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
    if "fase decimal queda como trazabilidad" not in adr:
        errors.append("APPROVAL_BINDING_MISSING:ADR-0028 decimal trace rule")

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
