#!/usr/bin/env python3
"""Validate Sprint 1 work package manifests and changed path scope."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
import zipfile
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

try:
    from scripts.security.attestation_parser import parse_attestation_section
except ModuleNotFoundError:
    from attestation_parser import parse_attestation_section


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_DIR = ROOT / ".context" / "work_packages"
VALID_STATUS = {"PROPOSED", "APPROVED", "ACTIVE", "COMPLETED", "REVOKED", "EXPIRED"}
REQUIRED = {
    "id",
    "status",
    "hito",
    "risk_level",
    "baseline",
    "environment_scope",
    "allowed_paths",
    "denied_without_jit",
    "dependencies",
    "r3_operations",
    "expires_at",
    "candidate_digest",
    "approval_digest_source",
    "approver_required",
    "invalidated_by",
    "exit_criteria",
}
FORBIDDEN_PROPOSED_KEYS = {"approved_by", "approved_at", "approval_digest", "activated_at", "approval_reference", "approved_level", "approved_candidate_commit", "approval_evidence_sha256"}
APPROVAL_KEYS = {"approval_digest", "approved_by", "approved_at", "approval_reference", "approved_level", "approved_candidate_commit", "approval_evidence_sha256"}
ACTIVE_KEYS = APPROVAL_KEYS | {"activated_at"}
REQUIRED_DENY_TERMS = {"production", "writers", "schedules", "lead_capture", "egress"}
H2_REQUIRED_DENY_TERMS = REQUIRED_DENY_TERMS | {
    "certification",
    "main",
    "supabase-free",
    "supabase-pro",
    "ddl-execution",
    "dml-execution",
    "backfill-execution",
    "rls-grants-remote",
    "workflow_dispatch",
    "deploys",
    "secrets",
}
DIGEST_FIELD = "candidate_digest"
DIGEST_EXCLUDED_FIELDS = {
    DIGEST_FIELD,
    "status",
    "approval_digest",
    "approved_by",
    "approved_at",
    "approval_reference",
    "approved_level",
    "activated_at",
}
H2_DIGEST_SCHEMA = "h2-approval-target-v1"
H2_APPROVED_CANDIDATE_COMMIT = "c8e4596b153c10721ed335369863a07154eb2b43"
H2_ACTIVATION_BASE_COMMIT = "6ad2690239db361bf913fc9f14c22146d11e69a6"
H2_OBSIDIAN_BASE_COMMIT = "56c517140ede7bce6a0580035a456016da8571a5"
GOV_OBS_BASE_COMMIT = "486bf420cb0d8ad250bc7b3cceb21545184b4dd5"
PR424_BASE_COMMIT = "974f9d4bde6d79230afde5c5a86ba7a3894233c6"
GOV_ARCH_BASE_COMMIT = "96c6e7e97a1a6c703eb3b5a3a22f6f6d21aa28e9"
GOV_HOM_BASE_COMMIT = "4cce43a743de5860c4da86eecf1782efab91d26b"
GOV_CI_BASE_COMMIT = "fddb9cea6ac44a1f7f7b31e93a7b2f2cc0eeacd1"
GOV_CI2_BASE_COMMIT = "b878c5764e55cb2646b60c4777e363489fe48e8b"
GOV_CI3_BASE_COMMIT = "1ac74f78fec6290e214444e9d2f18619ae3fd3b6"
GOV_CI4_BASE_COMMIT = "235c2329eb5fd8903c31785640a63466b23f0dd8"
GOV_CI5_BASE_COMMIT = "32dc50c2a26f0d8cf34c5a39a4f10a821bf821aa"
GOV_CI6_BASE_COMMIT = "9f265e41eb4724727e5bd4b1a5cf6ef5c75a4845"
GOV_CI7_BASE_COMMIT = "26a44af87e4e610d905763b6a5b8c14b64607954"
GOV_CI8_BASE_COMMIT = "16045d45811cbe12299ce2ba66f6afd75a93d1ee"
GOV_CI9_BASE_COMMIT = "1bc36ae6a4381c5ceac5e30c3970c39099965bc3"
GOV_CI10_BASE_COMMIT = "17d383291a5f2877074b54b66f2a0ff48a643667"
GOV_CI11_BASE_COMMIT = "cbdfe9dab373a2b427df4864b14427f3b2358789"
GOV_CI12_BASE_COMMIT = "793a2fb5aabc9e23bba2e3d36b47d6826444c5d4"
GOV_OBS_TARGET_LEVEL = "R2"
H2_SIGNED_FIELDS = {
    "digest_schema",
    "id",
    "task_id",
    "hito",
    "phase_trace",
    "risk_level",
    "baseline",
    "environment_scope",
    "allowed_paths",
    "allowed_actions",
    "denied_operations",
    "denied_without_jit",
    "dependencies",
    "r3_operations",
    "approval_contract",
    "approval_target_lifecycle_stage",
    "approval_target_gate_status",
    "approval_target_level",
    "criteria_contract",
    "source_artifacts",
    "expires_at",
    "supersedes_digest",
    "approval_digest_source",
    "approver_required",
    "invalidated_by",
    "exit_criteria",
}
H2_MUTABLE_FIELDS = {
    "candidate_digest",
    "status",
    "lifecycle_stage",
    "gate_status",
    "implementation_status",
    "criteria_status",
    "acceptance_status",
    "metrics",
    "approval_digest",
    "approved_by",
    "approved_at",
    "approval_reference",
    "approved_level",
    "approved_candidate_commit",
    "approval_evidence_sha256",
    "activated_at",
}
H2_ALLOWED_FIELDS = H2_SIGNED_FIELDS | H2_MUTABLE_FIELDS
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
UTC_TS = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
GOVERNANCE_ALLOWLIST = (
    "AGENTS.md",
    ".context/estado_del_proyecto.md",
    ".context/operaciones/plan_maestro_sprint1_h2_h5.md",
    ".context/operaciones/context_graph_semantico.md",
    ".context/seguimiento/seguimiento_sprint_1_h2_h5.md",
    ".context/hitos/hito_002.md",
    ".context/backlog_tareas/req_est_001_sprint_1/_index.md",
    ".context/backlog_tareas/req_est_001_sprint_1/tarea_002_hito_2.md",
    ".context/matrices/matriz_hito_002.md",
    ".context/work_packages/WP-H2-001.json",
    ".context/decisiones/ADR-0027_work_packages_y_convergencia.md",
    ".context/decisiones/ADR-0028_context_graph_semantico_y_autorizacion_r0_r3.md",
    ".github/workflows/security-audit.yml",
    "scripts/security/validate_context_graph.py",
    "scripts/security/validate_work_package.py",
    "scripts/security/run_h2_r1_tests.sh",
    "tests/test_work_package_manifest.py",
    "tests/test_context_graph_semantics.py",
    "docker-compose.h2-test.yml",
    "README.md",
    ".context/00_INDICE.md",
    ".context/arquitectura_pipeline.md",
    ".context/sistema_db_supabase.md",
    ".context/operaciones/matriz_adopcion_db.md",
    ".context/backlog_tareas/governance/TASK-GOV-ARCH-001.md",
    ".context/work_packages/WP-GOV-ARCH-001.json",
    "docs/architecture/Documento_Detallado_workflow.md",
    "docs/architecture/core_data_flow.md",
    "docs/orquestador-sdlc/PRODUCTION_ARCHITECTURE.md",
)
ABSOLUTE_DENY = (
    ".env*",
    "**/.env*",
    "*.env",
    "**/*.env",
    "supabase/**",
)
GOVERNANCE_DENY = ABSOLUTE_DENY + (
    "web/**",
    "db/**",
    "scripts/core/**",
    "scripts/maintenance/**",
    "workers/**",
)
H2_ACTIVATION_TRANSITION_ALLOWLIST = (
    ".context/estado_del_proyecto.md",
    ".context/operaciones/plan_maestro_sprint1_h2_h5.md",
    ".context/operaciones/context_graph_semantico.md",
    ".context/seguimiento/seguimiento_sprint_1_h2_h5.md",
    ".context/hitos/hito_002.md",
    ".context/backlog_tareas/req_est_001_sprint_1/tarea_002_hito_2.md",
    ".context/matrices/matriz_hito_002.md",
    ".context/work_packages/WP-H2-001.json",
    "scripts/security/validate_context_graph.py",
    "scripts/security/validate_work_package.py",
    "tests/test_work_package_manifest.py",
    "tests/test_context_graph_semantics.py",
)
H2_ACTIVATION_TRANSITION_DENY = ABSOLUTE_DENY + (
    "web/**",
    "db/**",
    "scripts/core/**",
    "scripts/maintenance/**",
    "supabase/**",
    "workers/**",
)
H2_OBSIDIAN_TRANSITION_ALLOWLIST = (
    "AGENTS.md",
    ".context/**",
    "scripts/security/validate_context_graph.py",
    "scripts/security/validate_work_package.py",
    "tests/test_context_graph_semantics.py",
    "tests/test_work_package_manifest.py",
)
H2_OBSIDIAN_TRANSITION_DENY = ABSOLUTE_DENY + (
    "web/**",
    "db/**",
    "supabase/**",
    "scripts/core/**",
    "scripts/maintenance/**",
    "workers/**",
    ".github/workflows/**",
)
GOV_OBS_TRANSITION_ALLOWLIST = (
    "AGENTS.md",
    ".context/**",
    "scripts/security/validate_context_graph.py",
    "scripts/security/validate_work_package.py",
    "tests/test_context_graph_semantics.py",
    "tests/test_work_package_manifest.py",
)
GOV_INFRA_TRANSITION_ALLOWLIST = (
    ".github/workflows/security-audit.yml",
    "docker-compose.h2-test.yml",
    "scripts/security/run_h2_r1_tests.sh",
)
GOV_RELEASE_TRANSITION_ALLOWLIST = tuple(sorted(set(GOV_OBS_TRANSITION_ALLOWLIST + GOV_INFRA_TRANSITION_ALLOWLIST)))
GOV_ARCH_TRANSITION_ALLOWLIST = (
    "AGENTS.md",
    "README.md",
    ".github/pull_request_template.md",
    ".github/workflows/security-audit.yml",
    ".context/00_INDICE.md",
    ".context/estado_del_proyecto.md",
    ".context/arquitectura_pipeline.md",
    ".context/sistema_db_supabase.md",
    ".context/operaciones/context_graph_semantico.md",
    ".context/operaciones/matriz_adopcion_db.md",
    ".context/operaciones/plan_maestro_sprint1_h2_h5.md",
    ".context/seguimiento/seguimiento_sprint_1_h2_h5.md",
    ".context/backlog_tareas/governance/TASK-GOV-ARCH-001.md",
    ".context/work_packages/WP-GOV-ARCH-001.json",
    "docs/architecture/Documento_Detallado_workflow.md",
    "docs/architecture/core_data_flow.md",
    "docs/orquestador-sdlc/PRODUCTION_ARCHITECTURE.md",
    "scripts/security/validate_change_governance.py",
    "scripts/security/validate_context_graph.py",
    "scripts/security/validate_work_package.py",
    "tests/test_change_governance.py",
    "tests/test_context_graph_semantics.py",
    "tests/test_work_package_manifest.py",
)
GOV_HOM_TRANSITION_ALLOWLIST = (
    ".context/00_INDICE.md",
    ".context/estado_del_proyecto.md",
    ".context/arquitectura_pipeline.md",
    ".context/operaciones/context_graph_semantico.md",
    ".context/operaciones/plan_maestro_sprint1_h2_h5.md",
    ".context/operaciones/flujo_release_minimo.md",
    ".context/seguimiento/seguimiento_sprint_1_h2_h5.md",
    ".context/evidencias_cliente/req_est_001_sprint_1/evidencia_hito_002.md",
    ".context/backlog_tareas/governance/TASK-GOV-ARCH-001.md",
    ".context/backlog_tareas/governance/TASK-GOV-HOM-001.md",
    ".context/work_packages/WP-GOV-HOM-001.json",
    ".context/decisiones/ADR-0029_homologacion_no_recursiva.md",
    "scripts/security/validate_context_graph.py",
    "scripts/security/validate_work_package.py",
    "tests/test_context_graph_semantics.py",
    "tests/test_work_package_manifest.py",
)
GOV_CI_TRANSITION_ALLOWLIST = (
    ".github/workflows/security-audit.yml",
    ".github/pull_request_template.md",
    "scripts/security/validate_change_governance.py",
    "scripts/security/validate_work_package.py",
    "scripts/security/validate_context_graph.py",
    "tests/test_change_governance.py",
    "tests/test_work_package_manifest.py",
    "tests/test_context_graph_semantics.py",
    ".context/00_INDICE.md",
    ".context/estado_del_proyecto.md",
    ".context/arquitectura_pipeline.md",
    ".context/operaciones/context_graph_semantico.md",
    ".context/operaciones/plan_maestro_sprint1_h2_h5.md",
    ".context/operaciones/flujo_release_minimo.md",
    ".context/operaciones/matriz_adopcion_db.md",
    ".context/seguimiento/seguimiento_sprint_1_h2_h5.md",
    ".context/backlog_tareas/governance/TASK-GOV-CI-001.md",
    ".context/work_packages/WP-GOV-CI-001.json",
    ".context/decisiones/ADR-0030_separacion_ci_y_review_gate.md",
)
GOV_CI2_TRANSITION_ALLOWLIST = (
    ".github/workflows/security-audit.yml",
    ".github/pull_request_template.md",
    "scripts/security/validate_work_package.py",
    "scripts/security/validate_context_graph.py",
    "tests/test_change_governance.py",
    "tests/test_work_package_manifest.py",
    "tests/test_context_graph_semantics.py",
    ".context/00_INDICE.md",
    ".context/estado_del_proyecto.md",
    ".context/arquitectura_pipeline.md",
    ".context/operaciones/context_graph_semantico.md",
    ".context/operaciones/plan_maestro_sprint1_h2_h5.md",
    ".context/operaciones/flujo_release_minimo.md",
    ".context/operaciones/matriz_adopcion_db.md",
    ".context/seguimiento/seguimiento_sprint_1_h2_h5.md",
    ".context/backlog_tareas/governance/TASK-GOV-CI-002.md",
    ".context/work_packages/WP-GOV-CI-002.json",
    ".context/decisiones/ADR-0031_boundary_homologacion_estructural.md",
)
GOV_CI3_TRANSITION_ALLOWLIST = (
    ".github/workflows/security-audit.yml",
    ".github/pull_request_template.md",
    "scripts/security/validate_work_package.py",
    "scripts/security/validate_context_graph.py",
    "tests/test_change_governance.py",
    "tests/test_work_package_manifest.py",
    "tests/test_context_graph_semantics.py",
    ".context/00_INDICE.md",
    ".context/estado_del_proyecto.md",
    ".context/arquitectura_pipeline.md",
    ".context/operaciones/context_graph_semantico.md",
    ".context/operaciones/plan_maestro_sprint1_h2_h5.md",
    ".context/operaciones/flujo_release_minimo.md",
    ".context/operaciones/matriz_adopcion_db.md",
    ".context/seguimiento/seguimiento_sprint_1_h2_h5.md",
    ".context/backlog_tareas/governance/TASK-GOV-CI-003.md",
    ".context/work_packages/WP-GOV-CI-003.json",
    ".context/decisiones/ADR-0032_grant_bootstrap_no_autorreferencial.md",
    ".context/r3_grants/R3-GOV-HOM-003-O2-REQ1.json",
    ".context/r3_grants/R3-GOV-HOM-003-O3-REQ1.json",
    ".context/r3_grants/R3-GOV-HOM-003-O4-REQ1.json",
    ".context/r3_grants/R3-GOV-HOM-003-O5-REQ1.json",
)
GOV_CI4_TRANSITION_ALLOWLIST = (
    ".github/workflows/security-audit.yml",
    "scripts/security/validate_work_package.py",
    "scripts/security/validate_context_graph.py",
    "tests/test_change_governance.py",
    "tests/test_work_package_manifest.py",
    "tests/test_context_graph_semantics.py",
    ".context/00_INDICE.md",
    ".context/estado_del_proyecto.md",
    ".context/arquitectura_pipeline.md",
    ".context/operaciones/context_graph_semantico.md",
    ".context/operaciones/plan_maestro_sprint1_h2_h5.md",
    ".context/operaciones/flujo_release_minimo.md",
    ".context/operaciones/matriz_adopcion_db.md",
    ".context/seguimiento/seguimiento_sprint_1_h2_h5.md",
    ".context/backlog_tareas/governance/TASK-GOV-CI-004.md",
    ".context/work_packages/WP-GOV-CI-004.json",
    ".context/decisiones/ADR-0033_promotion_environment_para_o2_o5.md",
    ".context/r3_grants/R3-GOV-HOM-004-O2-REQ1.json",
    ".context/r3_grants/R3-GOV-HOM-004-O3-REQ1.json",
    ".context/r3_grants/R3-GOV-HOM-004-O4-REQ1.json",
    ".context/r3_grants/R3-GOV-HOM-004-O5-REQ1.json",
)
GOV_CI5_TRANSITION_ALLOWLIST = (
    ".github/workflows/security-audit.yml",
    "scripts/security/validate_work_package.py",
    "scripts/security/validate_context_graph.py",
    "tests/test_change_governance.py",
    "tests/test_work_package_manifest.py",
    "tests/test_context_graph_semantics.py",
    ".context/00_INDICE.md",
    ".context/estado_del_proyecto.md",
    ".context/arquitectura_pipeline.md",
    ".context/operaciones/context_graph_semantico.md",
    ".context/operaciones/plan_maestro_sprint1_h2_h5.md",
    ".context/operaciones/flujo_release_minimo.md",
    ".context/operaciones/matriz_adopcion_db.md",
    ".context/seguimiento/seguimiento_sprint_1_h2_h5.md",
    ".context/backlog_tareas/governance/TASK-GOV-CI-005.md",
    ".context/work_packages/WP-GOV-CI-005.json",
    ".context/decisiones/ADR-0034_post_merge_promotion_push_boundary.md",
    ".context/r3_grants/R3-GOV-HOM-005-O2-REQ1.json",
    ".context/r3_grants/R3-GOV-HOM-005-O3-REQ1.json",
    ".context/r3_grants/R3-GOV-HOM-005-O4-REQ1.json",
    ".context/r3_grants/R3-GOV-HOM-005-O5-REQ1.json",
)
GOV_CI6_TRANSITION_ALLOWLIST = (
    "AGENTS.md",
    ".github/workflows/security-audit.yml",
    ".github/workflows/f9-7-contract.yml",
    ".github/pull_request_template.md",
    "scripts/security/validate_change_governance.py",
    "scripts/security/validate_work_package.py",
    "scripts/security/validate_context_graph.py",
    "tests/test_work_package_manifest.py",
    "tests/test_change_governance.py",
    "tests/test_context_graph_semantics.py",
    "tests/test_release_workflow_matrix.py",
    "tests/test_fase09_9_certification_canary.py",
    "tests/test_fase09_10_pre_main_controls.py",
    "tests/test_fase10_main_boundary.py",
    "tests/test_fase10_8_db_sync.py",
    "tests/test_fase10_production_canary.py",
    ".context/00_INDICE.md",
    ".context/estado_del_proyecto.md",
    ".context/arquitectura_pipeline.md",
    ".context/sistema_db_supabase.md",
    ".context/operaciones/context_graph_semantico.md",
    ".context/operaciones/flujo_release_minimo.md",
    ".context/operaciones/matriz_adopcion_db.md",
    ".context/operaciones/plan_maestro_sprint1_h2_h5.md",
    ".context/seguimiento/seguimiento_sprint_1_h2_h5.md",
    ".context/backlog_tareas/governance/TASK-GOV-CI-006.md",
    ".context/work_packages/WP-GOV-CI-006.json",
    ".context/decisiones/ADR-0035_target_aware_promotions_y_retiro_gates_legacy.md",
    ".context/r3_grants/R3-GOV-HOM-006-O2-REQ1.json",
    ".context/r3_grants/R3-GOV-HOM-006-O3-REQ1.json",
    ".context/r3_grants/R3-GOV-HOM-006-O4-REQ1.json",
    ".context/r3_grants/R3-GOV-HOM-006-O5-REQ1.json",
)
GOV_CI7_TRANSITION_ALLOWLIST = (
    "AGENTS.md",
    ".github/workflows/security-audit.yml",
    "scripts/security/validate_work_package.py",
    "scripts/security/validate_context_graph.py",
    "tests/test_work_package_manifest.py",
    "tests/test_context_graph_semantics.py",
    "tests/test_release_workflow_matrix.py",
    "tests/test_fase09_10_pre_main_controls.py",
    ".context/00_INDICE.md",
    ".context/estado_del_proyecto.md",
    ".context/arquitectura_pipeline.md",
    ".context/sistema_db_supabase.md",
    ".context/operaciones/context_graph_semantico.md",
    ".context/operaciones/flujo_release_minimo.md",
    ".context/operaciones/matriz_adopcion_db.md",
    ".context/operaciones/plan_maestro_sprint1_h2_h5.md",
    ".context/seguimiento/seguimiento_sprint_1_h2_h5.md",
    ".context/backlog_tareas/governance/TASK-GOV-CI-007.md",
    ".context/work_packages/WP-GOV-CI-007.json",
    ".context/decisiones/ADR-0036_post_merge_evidence_fail_closed.md",
    ".context/r3_grants/R3-GOV-HOM-007-O2-REQ1.json",
    ".context/r3_grants/R3-GOV-HOM-007-O3-REQ1.json",
    ".context/r3_grants/R3-GOV-HOM-007-O4-REQ1.json",
    ".context/r3_grants/R3-GOV-HOM-007-O5-REQ1.json",
)
GOV_CI8_TRANSITION_ALLOWLIST = (
    "AGENTS.md",
    ".github/workflows/security-audit.yml",
    "scripts/security/validate_work_package.py",
    "scripts/security/validate_context_graph.py",
    "tests/test_work_package_manifest.py",
    "tests/test_context_graph_semantics.py",
    "tests/test_release_workflow_matrix.py",
    "tests/test_fase09_10_pre_main_controls.py",
    ".context/00_INDICE.md",
    ".context/estado_del_proyecto.md",
    ".context/arquitectura_pipeline.md",
    ".context/sistema_db_supabase.md",
    ".context/operaciones/context_graph_semantico.md",
    ".context/operaciones/flujo_release_minimo.md",
    ".context/operaciones/matriz_adopcion_db.md",
    ".context/operaciones/plan_maestro_sprint1_h2_h5.md",
    ".context/seguimiento/seguimiento_sprint_1_h2_h5.md",
    ".context/backlog_tareas/governance/TASK-GOV-CI-008.md",
    ".context/work_packages/WP-GOV-CI-008.json",
    ".context/decisiones/ADR-0037_post_merge_route_classification_fail_closed.md",
    ".context/r3_grants/R3-GOV-HOM-008-O2-REQ1.json",
    ".context/r3_grants/R3-GOV-HOM-008-O3-REQ1.json",
    ".context/r3_grants/R3-GOV-HOM-008-O4-REQ1.json",
    ".context/r3_grants/R3-GOV-HOM-008-O5-REQ1.json",
)
GOV_CI9_TRANSITION_ALLOWLIST = (
    "AGENTS.md",
    ".github/pull_request_template.md",
    ".github/workflows/security-audit.yml",
    "scripts/security/validate_work_package.py",
    "scripts/security/validate_context_graph.py",
    "tests/test_work_package_manifest.py",
    "tests/test_context_graph_semantics.py",
    "tests/test_release_workflow_matrix.py",
    "tests/test_fase09_10_pre_main_controls.py",
    ".context/00_INDICE.md",
    ".context/estado_del_proyecto.md",
    ".context/arquitectura_pipeline.md",
    ".context/sistema_db_supabase.md",
    ".context/operaciones/context_graph_semantico.md",
    ".context/operaciones/flujo_release_minimo.md",
    ".context/operaciones/matriz_adopcion_db.md",
    ".context/operaciones/plan_maestro_sprint1_h2_h5.md",
    ".context/seguimiento/seguimiento_sprint_1_h2_h5.md",
    ".context/backlog_tareas/governance/TASK-GOV-CI-009.md",
    ".context/work_packages/WP-GOV-CI-009.json",
    ".context/decisiones/ADR-0038_owner_only_protected_branch_updates.md",
    ".context/r3_grants/R3-GOV-HOM-009-O2-REQ1.json",
    ".context/r3_grants/R3-GOV-HOM-009-O3-REQ1.json",
    ".context/r3_grants/R3-GOV-HOM-009-O4-REQ1.json",
    ".context/r3_grants/R3-GOV-HOM-009-O5-REQ1.json",
)
GOV_CI10_TRANSITION_ALLOWLIST = (
    "AGENTS.md",
    ".github/pull_request_template.md",
    ".github/workflows/security-audit.yml",
    "scripts/security/attestation_parser.py",
    "scripts/security/validate_change_governance.py",
    "scripts/security/validate_work_package.py",
    "scripts/security/validate_context_graph.py",
    "tests/test_attestation_parser.py",
    "tests/test_change_governance.py",
    "tests/test_work_package_manifest.py",
    "tests/test_context_graph_semantics.py",
    "tests/test_release_workflow_matrix.py",
    "tests/test_fase09_10_pre_main_controls.py",
    "tests/test_fase10_main_boundary.py",
    ".context/00_INDICE.md",
    ".context/estado_del_proyecto.md",
    ".context/arquitectura_pipeline.md",
    ".context/sistema_db_supabase.md",
    ".context/operaciones/context_graph_semantico.md",
    ".context/operaciones/flujo_release_minimo.md",
    ".context/operaciones/matriz_adopcion_db.md",
    ".context/operaciones/plan_maestro_sprint1_h2_h5.md",
    ".context/seguimiento/seguimiento_sprint_1_h2_h5.md",
    ".context/backlog_tareas/governance/TASK-GOV-CI-010.md",
    ".context/work_packages/WP-GOV-CI-010.json",
    ".context/decisiones/ADR-0039_attestation_section_aware_fail_closed.md",
    ".context/r3_grants/R3-GOV-HOM-010-O2-REQ1.json",
    ".context/r3_grants/R3-GOV-HOM-010-O3-REQ1.json",
    ".context/r3_grants/R3-GOV-HOM-010-O4-REQ1.json",
    ".context/r3_grants/R3-GOV-HOM-010-O5-REQ1.json",
)
GOV_CI11_TRANSITION_ALLOWLIST = (
    "AGENTS.md",
    ".github/pull_request_template.md",
    ".github/workflows/security-audit.yml",
    ".github/workflows/db-sync-to-pro.yml",
    "scripts/security/validate_work_package.py",
    "scripts/security/validate_context_graph.py",
    "scripts/security/validate_promotion_readiness.py",
    "tests/test_work_package_manifest.py",
    "tests/test_context_graph_semantics.py",
    "tests/test_release_workflow_matrix.py",
    "tests/test_fase09_10_pre_main_controls.py",
    "tests/test_fase10_main_boundary.py",
    "tests/test_fase10_8_db_sync.py",
    "tests/test_promotion_readiness.py",
    ".context/00_INDICE.md",
    ".context/estado_del_proyecto.md",
    ".context/arquitectura_pipeline.md",
    ".context/sistema_db_supabase.md",
    ".context/operaciones/context_graph_semantico.md",
    ".context/operaciones/flujo_release_minimo.md",
    ".context/operaciones/matriz_adopcion_db.md",
    ".context/operaciones/plan_maestro_sprint1_h2_h5.md",
    ".context/seguimiento/seguimiento_sprint_1_h2_h5.md",
    ".context/backlog_tareas/governance/TASK-GOV-CI-011.md",
    ".context/work_packages/WP-GOV-CI-011.json",
    ".context/decisiones/ADR-0040_promocion_transaccional_y_cierre_o3.md",
    ".context/r3_grants/R3-GOV-HOM-011-O2-REQ1.json",
    ".context/r3_grants/R3-GOV-HOM-011-O3-REQ1.json",
    ".context/r3_grants/R3-GOV-HOM-011-O4-REQ1.json",
    ".context/r3_grants/R3-GOV-HOM-011-O5-REQ1.json",
)
GOV_CI12_TRANSITION_ALLOWLIST = (
    "AGENTS.md",
    ".github/pull_request_template.md",
    ".github/workflows/security-audit.yml",
    ".github/workflows/db-sync-to-pro.yml",
    ".github/workflows/o3-closure.yml",
    "scripts/security/github_promotion_snapshot.py",
    "scripts/security/promotion_evidence.py",
    "scripts/security/validate_work_package.py",
    "scripts/security/validate_context_graph.py",
    "scripts/security/validate_promotion_readiness.py",
    "tests/fixtures/governance/gov-ci12/**",
    "tests/test_work_package_manifest.py",
    "tests/test_context_graph_semantics.py",
    "tests/test_release_workflow_matrix.py",
    "tests/test_fase09_10_pre_main_controls.py",
    "tests/test_fase10_main_boundary.py",
    "tests/test_fase10_8_db_sync.py",
    "tests/test_promotion_readiness.py",
    "tests/test_promotion_evidence.py",
    "tests/test_promotion_api_adapter.py",
    "tests/test_promotion_o2_o5_e2e.py",
    ".context/00_INDICE.md",
    ".context/estado_del_proyecto.md",
    ".context/arquitectura_pipeline.md",
    ".context/sistema_db_supabase.md",
    ".context/operaciones/context_graph_semantico.md",
    ".context/operaciones/flujo_release_minimo.md",
    ".context/operaciones/matriz_adopcion_db.md",
    ".context/operaciones/plan_maestro_sprint1_h2_h5.md",
    ".context/seguimiento/seguimiento_sprint_1_h2_h5.md",
    ".context/backlog_tareas/governance/TASK-GOV-CI-012.md",
    ".context/work_packages/WP-GOV-CI-012.json",
    ".context/decisiones/ADR-0041_promociones_evidencia_causal_o2_o5.md",
    ".context/r3_grants/R3-GOV-HOM-012-O2-REQ1.json",
    ".context/r3_grants/R3-GOV-HOM-012-O3-REQ1.json",
    ".context/r3_grants/R3-GOV-HOM-012-O4-REQ1.json",
    ".context/r3_grants/R3-GOV-HOM-012-O5-REQ1.json",
)
GOV_RELEASE_TRANSITION_DENY = ABSOLUTE_DENY + (
    "web/**",
    "db/**",
    "supabase/**",
    "scripts/core/**",
    "scripts/maintenance/**",
    "workers/**",
)
GOV_OBS_TRANSITION_DENY = GOV_RELEASE_TRANSITION_DENY
SOURCE_NAMES = {"Studiamatch_MVP_Requerimientos_v5.docx", "studiamatch_home.html", "studiamatch_resultados.html"}
SOURCE_EXTENSIONS = (".docx", ".pdf", ".zip", ".tar", ".tar.gz", ".html")
PROMOTION_PAIRS = {
    "O2 desarrollo -> certificacion": ("certificacion", "desarrollo"),
    "O3 certificacion -> main": ("main", "certificacion"),
    "O4 main -> certificacion": ("certificacion", "main"),
    "O5 certificacion -> desarrollo": ("desarrollo", "certificacion"),
}
PROMOTION_CANDIDATE_BRANCHES = {
    "O2 desarrollo -> certificacion": "promote/gov-hom-012-o2-req1",
    "O3 certificacion -> main": "promote/gov-hom-012-o3-req1",
    "O4 main -> certificacion": "promote/gov-hom-012-o4-req1",
    "O5 certificacion -> desarrollo": "promote/gov-hom-012-o5-req1",
}
SUPERSEDED_PROMOTION_PREFIX = "promote/gov-hom-"
PROMOTION_FIELDS = ("Operation", "Grant-ID", "Base-Ref", "Base-SHA", "Source-Ref", "Source-SHA", "Candidate-SHA", "Candidate-Tree", "Final-WP", "D_FINAL", "T_FINAL", "Approval-Level", "Approval-Reference", "Approval-Expiry")
PROMOTION_SHAPED_FIELDS = {"Operation", "Grant-ID", "Source-Ref", "Source-SHA", "Final-WP", "D_FINAL", "T_FINAL", "Candidate-Tree"}
INERT_ATTESTATION_VALUES = {"", "todo", "tbd", "n/a", "na", "none", "null", "nuevo-unico-no-consumido"}
PROTECTED_BRANCHES = {"desarrollo", "certificacion", "main"}
PROMOTION_FINAL_WP = "WP-GOV-CI-012"
GOV_CI2_PROMOTION_BLOCKED_PR_NUMBERS = {428}
GOV_CI2_PROMOTION_CONSUMED_GRANTS = {"R3-GOV-HOM-001-O2"}
PROMOTION_ALLOWED_ACTION = "opened"
PROMOTION_BLOCKED_PR_NUMBERS = {428, 431, 433, 435, 437, 440, 441, 443, 445}
PROMOTION_CONSUMED_GRANTS = {"R3-GOV-HOM-001-O2", "R3-GOV-HOM-003-O2-REQ1", "R3-GOV-HOM-004-O2-REQ1", "R3-GOV-HOM-005-O2-REQ1", "R3-GOV-HOM-006-O2-REQ1", "R3-GOV-HOM-008-O2-REQ1", "R3-GOV-HOM-010-O2-REQ1", "R3-GOV-HOM-011-O2-REQ1"}
PROMOTION_SUPERSEDED_GRANTS = {"R3-GOV-HOM-006-O3-REQ1", "R3-GOV-HOM-006-O4-REQ1", "R3-GOV-HOM-006-O5-REQ1", "R3-GOV-HOM-007-O2-REQ1", "R3-GOV-HOM-007-O3-REQ1", "R3-GOV-HOM-007-O4-REQ1", "R3-GOV-HOM-007-O5-REQ1", "R3-GOV-HOM-008-O2-REQ1", "R3-GOV-HOM-008-O3-REQ1", "R3-GOV-HOM-008-O4-REQ1", "R3-GOV-HOM-008-O5-REQ1", "R3-GOV-HOM-009-O2-REQ1", "R3-GOV-HOM-009-O3-REQ1", "R3-GOV-HOM-009-O4-REQ1", "R3-GOV-HOM-009-O5-REQ1", "R3-GOV-HOM-010-O3-REQ1", "R3-GOV-HOM-010-O4-REQ1", "R3-GOV-HOM-010-O5-REQ1", "R3-GOV-HOM-011-O3-REQ1", "R3-GOV-HOM-011-O4-REQ1", "R3-GOV-HOM-011-O5-REQ1"}
OWNER_ONLY_RULESET_REQUIRED = {
    "name": "owner-only-protected-branch-updates",
    "refs": ["refs/heads/desarrollo", "refs/heads/certificacion", "refs/heads/main"],
    "rule": "restrict_updates",
    "bypass_user": "romelhc95",
    "bypass_user_id": 18040405,
    "excluded_user": "romelhc95-approver",
    "excluded_user_id": 306979205,
}
PROMOTION_GRANT_ID_PATTERN = re.compile(r"^R3-GOV-HOM-\d{3}-O[2-5]-[A-Za-z0-9][A-Za-z0-9_.-]{3,}$")
PROMOTION_REQUEST_STATUS = "REQUESTED_JIT_SINGLE_USE"
LEGACY_PROMOTION_BINDINGS = {
    "base_sha_binding": "pull_request.base.sha",
    "candidate_sha_binding": "pull_request.head.sha",
    "t_final_binding": "tree(pull_request.head.sha)",
    "d_final_binding": "manifest.candidate_digest",
}
PROMOTION_BINDINGS = {
    "base_sha_binding": "pull_request.base.sha",
    "source_sha_binding": "promotion_attestation.Source-SHA",
    "candidate_sha_binding": "pull_request.head.sha",
    "candidate_tree_binding": "tree(pull_request.head.sha)",
    "t_final_binding": "tree(promotion_attestation.Source-SHA)",
    "d_final_binding": "manifest.candidate_digest",
}
STATIC_PROMOTION_REQUEST_KEYS = {
    "id",
    "status",
    "operation",
    "repository",
    "base_ref",
    "head_ref",
    "source_ref",
    "candidate_branch",
    "final_wp",
    "base_sha_binding",
    "source_sha_binding",
    "candidate_sha_binding",
    "candidate_tree_binding",
    "t_final_binding",
    "d_final_binding",
    "event_action",
    "run_attempt",
    "single_use",
    "external_consumption_required",
    "required_merger",
    "required_reviewer",
    "merger_reviewer_distinct",
    "cloudflare_pages_production_rebuild_expected",
    "db_sync_detect_only_required",
    "db_sync_expected_result",
    "approval_envelope_schema",
    "allowed_side_effects",
    "blocked_until_o3_closed",
}
PROMOTION_ENVELOPE_SCHEMA = "promotion-jit-envelope-v2"
PROMOTION_ENVELOPE_FIELDS = {
    "schema",
    "transaction_id",
    "approval_id",
    "grant_id",
    "repository_id",
    "repository",
    "operation",
    "pr_number",
    "pr_node_id",
    "premerge_run_id",
    "premerge_run_attempt",
    "event_name",
    "event_action",
    "base_ref",
    "base_sha",
    "source_ref",
    "source_sha",
    "candidate_ref",
    "candidate_sha",
    "candidate_tree",
    "final_wp",
    "final_digest",
    "final_tree",
    "required_reviewer",
    "required_reviewer_id",
    "required_merger",
    "required_merger_id",
    "allowed_side_effects",
    "environment",
    "environment_id",
    "ruleset_id",
    "ruleset_digest",
    "issued_at",
    "expires_at",
    "nonce",
}
GITHUB_ACTIONS_APP_ID = 15368
CLOUDFLARE_PAGES_APP_ID = 85455
CLOUDFLARE_PAGES_CHECK_NAME = "Cloudflare Pages"
DB_SYNC_DETECT_ONLY_CHECK_NAME = "DB Sync Detect Only"
DB_SYNC_DETECT_ONLY_RESULT = "NO_DB_CHANGES"
PROMOTION_APPROVAL_EVIDENCE_FILE = "promotion-approval-evidence.json"
O3_CLOSURE_EVIDENCE_FILE = "o3-closure-evidence.json"
DB_SYNC_DETECT_ONLY_EVIDENCE_FILE = "db-sync-detect-only.json"


def canonical_payload(data: dict[str, Any]) -> bytes:
    if data.get("digest_schema") == H2_DIGEST_SCHEMA:
        payload = {key: data[key] for key in sorted(H2_SIGNED_FIELDS) if key in data}
    else:
        payload = {key: value for key, value in data.items() if key not in DIGEST_EXCLUDED_FIELDS}
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")


def compute_digest(data: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_payload(data)).hexdigest()


def parse_attestation_fields(body: str) -> dict[str, str]:
    section = parse_attestation_section(body, "Promotion Attestation", PROMOTION_FIELDS)
    fields = dict(section.fields)
    if section.duplicate_section:
        fields["__DUPLICATE_SECTION__"] = "Promotion Attestation"
    if section.duplicates:
        fields["__DUPLICATE__"] = section.duplicates[0]
    return fields


def promotion_section_errors(body: str, prefix: str) -> list[str]:
    section = parse_attestation_section(body, "Promotion Attestation", PROMOTION_FIELDS)
    errors: list[str] = []
    if not section.present:
        errors.append(f"{prefix}_ATTESTATION_SECTION_MISSING")
    if section.duplicate_section:
        errors.append(f"{prefix}_ATTESTATION_SECTION_DUPLICATE")
    if section.duplicates:
        errors.append(f"{prefix}_ATTESTATION_DUPLICATE")
    return errors


def governance_section_populated(body: str) -> bool:
    governance_fields = (
        "Base-SHA", "Candidate-SHA", "Estado-Snapshot", "Requerimiento", "Hito", "TASK", "WP", "WP-Digest",
        "Approval-Level", "Approval-Expiry", "Architecture-Snapshot", "Data-Architecture-Snapshot", "Adoption-Matrix-Snapshot",
        "Architecture-Impact", "Architecture-Impact-Reason", "Data-Impact", "Data-Impact-Reason", "Security-Auditor",
    )
    section = parse_attestation_section(body, "Governance Attestation", governance_fields)
    return any(not is_inert_attestation_value(value) for value in section.nonempty_fields().values())


def is_inert_attestation_value(value: str) -> bool:
    stripped = value.strip()
    return stripped.lower() in INERT_ATTESTATION_VALUES or stripped.startswith("<")


def parse_utc(value: Any) -> datetime | None:
    if not isinstance(value, str) or not UTC_TS.match(value):
        return None
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)


def path_is_safe_pattern(pattern: str) -> bool:
    if not pattern or pattern in {"*", "**", "/", "/**"}:
        return False
    if "\\" in pattern or pattern.startswith("/"):
        return False
    parts = pattern.split("/")
    return all(part not in {"", ".", ".."} for part in parts)


def pattern_matches(patterns: tuple[str, ...] | list[str], path: str) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def validate_manifest(path: Path, *, now: datetime | None = None, root: Path | None = None) -> list[str]:
    errors: list[str] = []
    root = root or ROOT
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"WP_JSON_INVALID:{path.name}:{exc}"]
    if not isinstance(data, dict):
        return [f"WP_JSON_INVALID:{path.name}:root must be object"]

    missing = REQUIRED - data.keys()
    if missing:
        errors.append(f"WP_REQUIRED_MISSING:{path.name}:{sorted(missing)}")
    status = data.get("status")
    if status not in VALID_STATUS:
        errors.append(f"WP_STATUS_INVALID:{path.name}")
    if data.get("id") != path.stem:
        errors.append(f"WP_ID_MISMATCH:{path.name}")
    if data.get("approver_required") != "human":
        errors.append(f"WP_HUMAN_APPROVER_REQUIRED:{path.name}")
    if data.get("digest_schema") == H2_DIGEST_SCHEMA:
        unknown = set(data) - H2_ALLOWED_FIELDS
        if unknown:
            errors.append(f"WP_UNKNOWN_FIELDS:{path.name}:{sorted(unknown)}")
        missing_signed = H2_SIGNED_FIELDS - set(data)
        if missing_signed:
            errors.append(f"WP_SIGNED_FIELDS_MISSING:{path.name}:{sorted(missing_signed)}")

    for key in ("allowed_paths", "denied_without_jit", "dependencies", "r3_operations", "invalidated_by", "exit_criteria"):
        if not isinstance(data.get(key), list) or not data.get(key):
            errors.append(f"WP_LIST_REQUIRED:{path.name}:{key}")

    digest = data.get(DIGEST_FIELD)
    if not isinstance(digest, str) or not HEX64.match(digest):
        errors.append(f"WP_DIGEST_FORMAT:{path.name}")
    elif digest != compute_digest(data):
        errors.append(f"WP_DIGEST_MISMATCH:{path.name}:expected {compute_digest(data)}")

    baseline = data.get("baseline")
    required_baseline = {"main_commit", "main_tree", "desarrollo_commit", "desarrollo_tree", "certificacion_commit", "certificacion_tree"}
    if not isinstance(baseline, dict) or not required_baseline <= set(baseline):
        errors.append(f"WP_BASELINE_REQUIRED:{path.name}")
    elif any(not isinstance(baseline[key], str) or not HEX40.match(baseline[key]) for key in required_baseline):
        errors.append(f"WP_BASELINE_SHA_FORMAT:{path.name}")
    else:
        for branch in ("main", "desarrollo", "certificacion"):
            commit = baseline[f"{branch}_commit"]
            tree = baseline[f"{branch}_tree"]
            try:
                actual = subprocess.check_output(["git", "rev-parse", f"{commit}^{{tree}}"], cwd=root, text=True, stderr=subprocess.DEVNULL).strip()
            except subprocess.CalledProcessError:
                continue
            if actual != tree:
                errors.append(f"COMMIT_TREE_MISMATCH:{path.name}:{branch}")

    expires_at = data.get("expires_at")
    if not isinstance(expires_at, str):
        errors.append(f"WP_EXPIRES_REQUIRED:{path.name}")
    else:
        expiry = parse_utc(expires_at)
        if expiry is None and data.get("id") != "WP-H2-001" and re.match(r"^\d{4}-\d{2}-\d{2}$", expires_at):
            expiry = datetime.strptime(expires_at, "%Y-%m-%d").replace(tzinfo=UTC)
        if expiry is None:
            errors.append(f"WP_EXPIRES_FORMAT:{path.name}")
        elif (now or datetime.now(UTC)) >= expiry:
            errors.append(f"WP_EXPIRED:{path.name}")

    allowed = [str(item) for item in data.get("allowed_paths", [])]
    denied = [str(item) for item in data.get("denied_without_jit", [])]
    for pattern in allowed:
        if not path_is_safe_pattern(pattern):
            errors.append(f"UNSAFE_PATH_PATTERN:{path.name}:{pattern}")
    if any(pattern in {"*", "**"} for pattern in allowed):
        errors.append(f"UNBOUNDED_ALLOWLIST:{path.name}")
    unsafe_allowed = (".env", ".env*", "**/.env", "**/.env*", "*.env", "**/*.env", "supabase/**")
    if any(pattern_matches(unsafe_allowed, pattern) for pattern in allowed):
        errors.append(f"ALLOW_DENY_OVERLAP:{path.name}")

    denied_terms = {item.lower() for item in denied}
    if data.get("id") == "WP-H2-001":
        required_denies = H2_REQUIRED_DENY_TERMS
        if data.get("task_id") != "TASK-H2-001" or data.get("hito") != "HITO-002":
            errors.append(f"GRAPH_ID_MISMATCH:{path.name}")
        if data.get("digest_schema") != H2_DIGEST_SCHEMA:
            errors.append(f"WP_DIGEST_SCHEMA_INVALID:{path.name}")
        expected_lifecycle = {"PROPOSED": "AWAITING_DIGEST", "APPROVED": "APPROVED_NOT_ACTIVE", "ACTIVE": "ACTIVE"}.get(status)
        expected_gate = "READY_FOR_DIGEST_APPROVAL" if status == "PROPOSED" else "APPROVED_R1"
        if expected_lifecycle and data.get("lifecycle_stage") != expected_lifecycle:
            errors.append(f"LIFECYCLE_MISMATCH:{path.name}:expected {expected_lifecycle}")
        if expected_gate and data.get("gate_status") != expected_gate:
            errors.append(f"LIFECYCLE_MISMATCH:{path.name}:gate")
        if data.get("approval_target_lifecycle_stage") != "APPROVED_NOT_ACTIVE":
            errors.append(f"APPROVAL_TARGET_INVALID:{path.name}:lifecycle")
        if data.get("approval_target_gate_status") != "APPROVED_R1":
            errors.append(f"APPROVAL_TARGET_INVALID:{path.name}:gate")
        if data.get("approval_target_level") != "R1":
            errors.append(f"APPROVAL_TARGET_INVALID:{path.name}:level")
        if data.get("criteria_contract") != ["H2-CA2", "H2-CA3"]:
            errors.append(f"CRITERIA_SET_MISMATCH:{path.name}:contract")
        expected_implementation = "BLOCKED_PENDING_OBSIDIAN_MAIN" if status == "ACTIVE" else "PLANNED_NOT_ACTIVE"
        if data.get("implementation_status") != expected_implementation:
            errors.append(f"LIFECYCLE_MISMATCH:{path.name}:implementation")
        if data.get("acceptance_status") != "NOT_STARTED":
            errors.append(f"LIFECYCLE_MISMATCH:{path.name}:acceptance")
        if data.get("criteria_status") != {"H2-CA2": "NOT_STARTED", "H2-CA3": "NOT_STARTED"}:
            errors.append(f"CRITERIA_SET_MISMATCH:{path.name}")
        if data.get("environment_scope") != ["local", "development"]:
            errors.append(f"WP_ENV_SCOPE_INVALID:{path.name}")
        if data.get("supersedes_digest") != "7a62121f8389192f8c0bab3a06b54b554ddd5a1e8fc05822e7429d96a1229066":
            errors.append(f"WP_REJECTED_DIGEST_TRACE_REQUIRED:{path.name}")
    elif data.get("id") == "WP-GOV-OBS-001":
        required_denies = H2_REQUIRED_DENY_TERMS
        if data.get("task_id") != "TASK-GOV-OBS-001" or data.get("hito") != "GOV-OBS":
            errors.append(f"GRAPH_ID_MISMATCH:{path.name}")
        if data.get("target_level") != GOV_OBS_TARGET_LEVEL:
            errors.append(f"GOV_OBS_TARGET_INVALID:{path.name}")
        if data.get("status") != "PROPOSED":
            errors.append(f"GOV_OBS_STATUS_INVALID:{path.name}:must remain PROPOSED before R2 approval")
        baseline = data.get("baseline", {})
        if baseline.get("candidate_commit") != GOV_OBS_BASE_COMMIT:
            errors.append(f"GOV_OBS_BASELINE_INVALID:{path.name}:candidate_commit")
        if baseline.get("candidate_tree") != "bc521d7b030095fb1ef928923e333cb4721cda94":
            errors.append(f"GOV_OBS_BASELINE_INVALID:{path.name}:candidate_tree")
        if any(term not in denied_terms for term in ("certification", "main", "supabase-free", "supabase-pro", "ddl-execution", "dml-execution", "backfill-execution", "rls-grants-remote", "workflow_dispatch", "deploys", "secrets")):
            errors.append(f"GOV_OBS_R3_DENY_MISSING:{path.name}")
        if not any("certification" in str(item).lower() for item in data.get("r3_operations", [])) or not any("main" in str(item).lower() for item in data.get("r3_operations", [])):
            errors.append(f"GOV_OBS_R3_OPERATIONS_REQUIRED:{path.name}")
    elif data.get("id") == "WP-GOV-INFRA-001":
        required_denies = H2_REQUIRED_DENY_TERMS
        if data.get("task_id") != "TASK-GOV-INFRA-001" or data.get("hito") != "GOV-INFRA":
            errors.append(f"GRAPH_ID_MISMATCH:{path.name}")
        if data.get("target_level") != GOV_OBS_TARGET_LEVEL:
            errors.append(f"GOV_INFRA_TARGET_INVALID:{path.name}")
        if data.get("status") != "PROPOSED":
            errors.append(f"GOV_INFRA_STATUS_INVALID:{path.name}:must remain PROPOSED before R2 approval")
        if data.get("allowed_paths") != list(GOV_INFRA_TRANSITION_ALLOWLIST):
            errors.append(f"GOV_INFRA_ALLOWLIST_INVALID:{path.name}")
        baseline = data.get("baseline", {})
        if baseline.get("candidate_commit") != GOV_OBS_BASE_COMMIT:
            errors.append(f"GOV_INFRA_BASELINE_INVALID:{path.name}:candidate_commit")
        if baseline.get("candidate_tree") != "bc521d7b030095fb1ef928923e333cb4721cda94":
            errors.append(f"GOV_INFRA_BASELINE_INVALID:{path.name}:candidate_tree")
        if any(term not in denied_terms for term in ("certification", "main", "supabase-free", "supabase-pro", "ddl-execution", "dml-execution", "backfill-execution", "rls-grants-remote", "workflow_dispatch", "deploys", "secrets")):
            errors.append(f"GOV_INFRA_R3_DENY_MISSING:{path.name}")
    elif data.get("id") == "WP-GOV-ARCH-001":
        required_denies = H2_REQUIRED_DENY_TERMS | {"migration-execution"}
        if data.get("task_id") != "TASK-GOV-ARCH-001" or data.get("hito") != "GOV-ARCH":
            errors.append(f"GRAPH_ID_MISMATCH:{path.name}")
        if data.get("target_level") != GOV_OBS_TARGET_LEVEL:
            errors.append(f"GOV_ARCH_TARGET_INVALID:{path.name}")
        if data.get("status") != "PROPOSED":
            errors.append(f"GOV_ARCH_STATUS_INVALID:{path.name}:must remain PROPOSED before R2 approval")
        baseline = data.get("baseline", {})
        if baseline.get("candidate_commit") != GOV_ARCH_BASE_COMMIT:
            errors.append(f"GOV_ARCH_BASELINE_INVALID:{path.name}:candidate_commit")
        if baseline.get("candidate_tree") != "530b0a95dda9f81f408ebcb8c177a1ed73afe3e3":
            errors.append(f"GOV_ARCH_BASELINE_INVALID:{path.name}:candidate_tree")
        required_paths = {
            ".context/arquitectura_pipeline.md",
            ".context/sistema_db_supabase.md",
            ".context/operaciones/matriz_adopcion_db.md",
            ".context/backlog_tareas/governance/TASK-GOV-ARCH-001.md",
            ".context/work_packages/WP-GOV-ARCH-001.json",
        }
        if data.get("allowed_paths") != list(GOV_ARCH_TRANSITION_ALLOWLIST) or not required_paths <= set(data.get("allowed_paths", [])):
            errors.append(f"GOV_ARCH_ALLOWLIST_INVALID:{path.name}")
        control_paths = {".github/workflows/security-audit.yml", "scripts/security/validate_change_governance.py", "scripts/security/validate_context_graph.py", "scripts/security/validate_work_package.py"}
        if control_paths & set(data.get("allowed_paths", [])) and not data.get("governance_controls_scope"):
            errors.append(f"GOV_ARCH_CONTROLS_SCOPE_REQUIRED:{path.name}")
        if any(term not in denied_terms for term in ("certification", "main", "supabase-free", "supabase-pro", "ddl-execution", "dml-execution", "migration-execution", "backfill-execution", "rls-grants-remote", "workflow_dispatch", "deploys", "secrets")):
            errors.append(f"GOV_ARCH_R3_DENY_MISSING:{path.name}")
    elif data.get("id") == "WP-GOV-HOM-001":
        required_denies = H2_REQUIRED_DENY_TERMS | {"migration-execution"}
        if data.get("task_id") != "TASK-GOV-HOM-001" or data.get("hito") != "GOV-HOM":
            errors.append(f"GRAPH_ID_MISMATCH:{path.name}")
        if data.get("target_level") != GOV_OBS_TARGET_LEVEL:
            errors.append(f"GOV_HOM_TARGET_INVALID:{path.name}")
        if data.get("status") != "PROPOSED":
            errors.append(f"GOV_HOM_STATUS_INVALID:{path.name}:must remain PROPOSED before R2 approval")
        if data.get("allowed_paths") != list(GOV_HOM_TRANSITION_ALLOWLIST):
            errors.append(f"GOV_HOM_ALLOWLIST_INVALID:{path.name}")
        baseline = data.get("baseline", {})
        if baseline.get("candidate_commit") != GOV_HOM_BASE_COMMIT or baseline.get("desarrollo_commit") != GOV_HOM_BASE_COMMIT:
            errors.append(f"GOV_HOM_BASELINE_INVALID:{path.name}:candidate/desarrollo_commit")
        if baseline.get("candidate_tree") != "ac16b545b74a03b149aac538062def20101187fb" or baseline.get("desarrollo_tree") != "ac16b545b74a03b149aac538062def20101187fb":
            errors.append(f"GOV_HOM_BASELINE_INVALID:{path.name}:candidate/desarrollo_tree")
        grants = data.get("homologation_grants")
        if not isinstance(grants, list) or len(grants) != 4:
            errors.append(f"GOV_HOM_GRANTS_INVALID:{path.name}:expected four separate templates")
        else:
            expected_ids = {"R3-GOV-HOM-001-O2", "R3-GOV-HOM-001-O3", "R3-GOV-HOM-001-O4", "R3-GOV-HOM-001-O5"}
            actual_ids = {str(grant.get("id")) for grant in grants if isinstance(grant, dict)}
            if actual_ids != expected_ids or any(grant.get("single_use") is not True for grant in grants if isinstance(grant, dict)):
                errors.append(f"GOV_HOM_GRANTS_INVALID:{path.name}:ids/single_use")
            if any(str(grant.get("status")) != "TEMPLATE_ONLY_NOT_GRANTED" for grant in grants if isinstance(grant, dict)):
                errors.append(f"GOV_HOM_GRANTS_INVALID:{path.name}:must not grant R3")
        predicate = data.get("closure_predicate")
        if not isinstance(predicate, list) or not any("tree(main) == tree(certificacion) == tree(desarrollo) == T_HOM" in str(item) for item in predicate):
            errors.append(f"GOV_HOM_CLOSURE_PREDICATE_REQUIRED:{path.name}")
        if any(term not in denied_terms for term in ("certification", "main", "supabase-free", "supabase-pro", "ddl-execution", "dml-execution", "migration-execution", "backfill-execution", "rls-grants-remote", "workflow_dispatch", "deploys", "secrets")):
            errors.append(f"GOV_HOM_R3_DENY_MISSING:{path.name}")
    elif data.get("id") == "WP-GOV-CI-001":
        required_denies = H2_REQUIRED_DENY_TERMS | {"migration-execution"}
        if data.get("task_id") != "TASK-GOV-CI-001" or data.get("hito") != "GOV-CI":
            errors.append(f"GRAPH_ID_MISMATCH:{path.name}")
        if data.get("target_level") != GOV_OBS_TARGET_LEVEL:
            errors.append(f"GOV_CI_TARGET_INVALID:{path.name}")
        if data.get("status") != "PROPOSED":
            errors.append(f"GOV_CI_STATUS_INVALID:{path.name}:must remain PROPOSED before R2 approval")
        if data.get("allowed_paths") != list(GOV_CI_TRANSITION_ALLOWLIST):
            errors.append(f"GOV_CI_ALLOWLIST_INVALID:{path.name}")
        baseline = data.get("baseline", {})
        if baseline.get("candidate_commit") != GOV_CI_BASE_COMMIT or baseline.get("desarrollo_commit") != GOV_CI_BASE_COMMIT:
            errors.append(f"GOV_CI_BASELINE_INVALID:{path.name}:candidate/desarrollo_commit")
        if baseline.get("candidate_tree") != "5e7d087ac45457264ea29dfc1aa7373efd909290" or baseline.get("desarrollo_tree") != "5e7d087ac45457264ea29dfc1aa7373efd909290":
            errors.append(f"GOV_CI_BASELINE_INVALID:{path.name}:candidate/desarrollo_tree")
        decoupling = data.get("ci_review_decoupling")
        if not isinstance(decoupling, dict) or decoupling.get("reviews_trigger_ci") is not False or decoupling.get("reviews_api_used") is not False or decoupling.get("manual_rerun_required_for_review") is not False:
            errors.append(f"GOV_CI_DECOUPLING_INVALID:{path.name}")
        if any(term not in denied_terms for term in ("certification", "main", "supabase-free", "supabase-pro", "ddl-execution", "dml-execution", "migration-execution", "backfill-execution", "rls-grants-remote", "workflow_dispatch", "deploys", "secrets")):
            errors.append(f"GOV_CI_R3_DENY_MISSING:{path.name}")
    elif data.get("id") == "WP-GOV-CI-002":
        required_denies = H2_REQUIRED_DENY_TERMS | {"migration-execution"}
        if data.get("task_id") != "TASK-GOV-CI-002" or data.get("hito") != "GOV-CI":
            errors.append(f"GRAPH_ID_MISMATCH:{path.name}")
        if data.get("target_level") != GOV_OBS_TARGET_LEVEL:
            errors.append(f"GOV_CI2_TARGET_INVALID:{path.name}")
        if data.get("status") != "PROPOSED":
            errors.append(f"GOV_CI2_STATUS_INVALID:{path.name}:must remain PROPOSED before R2 approval")
        if data.get("allowed_paths") != list(GOV_CI2_TRANSITION_ALLOWLIST):
            errors.append(f"GOV_CI2_ALLOWLIST_INVALID:{path.name}")
        baseline = data.get("baseline", {})
        if baseline.get("candidate_commit") != GOV_CI2_BASE_COMMIT or baseline.get("desarrollo_commit") != GOV_CI2_BASE_COMMIT:
            errors.append(f"GOV_CI2_BASELINE_INVALID:{path.name}:candidate/desarrollo_commit")
        if baseline.get("candidate_tree") != "174c18efd840fff6ce27fce9fe1dc4edcd65abe8" or baseline.get("desarrollo_tree") != "174c18efd840fff6ce27fce9fe1dc4edcd65abe8":
            errors.append(f"GOV_CI2_BASELINE_INVALID:{path.name}:candidate/desarrollo_tree")
        promotion = data.get("promotion_boundary")
        if not isinstance(promotion, dict) or promotion.get("structural_pairs") != sorted(PROMOTION_PAIRS) or promotion.get("incremental_boundary_preserved") is not True:
            errors.append(f"GOV_CI2_PROMOTION_BOUNDARY_INVALID:{path.name}")
        elif promotion.get("blocked_pr_numbers") != sorted(GOV_CI2_PROMOTION_BLOCKED_PR_NUMBERS) or promotion.get("consumed_grants_blocked") != sorted(GOV_CI2_PROMOTION_CONSUMED_GRANTS) or promotion.get("accepted_event_action") != PROMOTION_ALLOWED_ACTION or promotion.get("accepted_run_attempt") != 1:
            errors.append(f"GOV_CI2_PROMOTION_REPLAY_GUARDS_INVALID:{path.name}")
        if any(term not in denied_terms for term in ("certification", "main", "supabase-free", "supabase-pro", "ddl-execution", "dml-execution", "migration-execution", "backfill-execution", "rls-grants-remote", "workflow_dispatch", "deploys", "secrets")):
            errors.append(f"GOV_CI2_R3_DENY_MISSING:{path.name}")
    elif data.get("id") == "WP-GOV-CI-003":
        required_denies = H2_REQUIRED_DENY_TERMS | {"migration-execution"}
        if data.get("task_id") != "TASK-GOV-CI-003" or data.get("hito") != "GOV-CI":
            errors.append(f"GRAPH_ID_MISMATCH:{path.name}")
        if data.get("target_level") != GOV_OBS_TARGET_LEVEL:
            errors.append(f"GOV_CI3_TARGET_INVALID:{path.name}")
        if data.get("status") != "PROPOSED":
            errors.append(f"GOV_CI3_STATUS_INVALID:{path.name}:must remain PROPOSED before R2 approval")
        if data.get("allowed_paths") != list(GOV_CI3_TRANSITION_ALLOWLIST):
            errors.append(f"GOV_CI3_ALLOWLIST_INVALID:{path.name}")
        baseline = data.get("baseline", {})
        if baseline.get("candidate_commit") != GOV_CI3_BASE_COMMIT or baseline.get("desarrollo_commit") != GOV_CI3_BASE_COMMIT:
            errors.append(f"GOV_CI3_BASELINE_INVALID:{path.name}:candidate/desarrollo_commit")
        if baseline.get("candidate_tree") != "8191790192580f2e9fb1ddb48d85ab28714720f9" or baseline.get("desarrollo_tree") != "8191790192580f2e9fb1ddb48d85ab28714720f9":
            errors.append(f"GOV_CI3_BASELINE_INVALID:{path.name}:candidate/desarrollo_tree")
        if data.get("supersedes_digest") != "30bc9a2e7b201438e7398a46f42e6a719e0e5bb41d46c95c71b02234c9091d04":
            errors.append(f"GOV_CI3_SUPERSEDES_INVALID:{path.name}")
        promotion = data.get("promotion_request_bootstrap")
        expected_grants = [
            "R3-GOV-HOM-003-O2-REQ1",
            "R3-GOV-HOM-003-O3-REQ1",
            "R3-GOV-HOM-003-O4-REQ1",
            "R3-GOV-HOM-003-O5-REQ1",
        ]
        if not isinstance(promotion, dict) or promotion.get("final_wp") != "WP-GOV-CI-003" or promotion.get("static_request_status") != PROMOTION_REQUEST_STATUS or promotion.get("symbolic_bindings") != LEGACY_PROMOTION_BINDINGS or promotion.get("grant_request_ids") != expected_grants:
            errors.append(f"GOV_CI3_PROMOTION_REQUEST_BOOTSTRAP_INVALID:{path.name}")
        if any(term not in denied_terms for term in ("certification", "main", "supabase-free", "supabase-pro", "ddl-execution", "dml-execution", "migration-execution", "backfill-execution", "rls-grants-remote", "workflow_dispatch", "deploys", "secrets")):
            errors.append(f"GOV_CI3_R3_DENY_MISSING:{path.name}")
    elif data.get("id") == "WP-GOV-CI-004":
        required_denies = H2_REQUIRED_DENY_TERMS | {"migration-execution"}
        if data.get("task_id") != "TASK-GOV-CI-004" or data.get("hito") != "GOV-CI":
            errors.append(f"GRAPH_ID_MISMATCH:{path.name}")
        if data.get("target_level") != GOV_OBS_TARGET_LEVEL:
            errors.append(f"GOV_CI4_TARGET_INVALID:{path.name}")
        if data.get("status") != "PROPOSED":
            errors.append(f"GOV_CI4_STATUS_INVALID:{path.name}:must remain PROPOSED before R2 approval")
        if data.get("allowed_paths") != list(GOV_CI4_TRANSITION_ALLOWLIST):
            errors.append(f"GOV_CI4_ALLOWLIST_INVALID:{path.name}")
        baseline = data.get("baseline", {})
        if baseline.get("candidate_commit") != GOV_CI4_BASE_COMMIT or baseline.get("desarrollo_commit") != GOV_CI4_BASE_COMMIT:
            errors.append(f"GOV_CI4_BASELINE_INVALID:{path.name}:candidate/desarrollo_commit")
        if baseline.get("candidate_tree") != "cc774746d21cb6649f7018da3049fc811a3f294b" or baseline.get("desarrollo_tree") != "cc774746d21cb6649f7018da3049fc811a3f294b":
            errors.append(f"GOV_CI4_BASELINE_INVALID:{path.name}:candidate/desarrollo_tree")
        if data.get("supersedes_digest") != "60c1fc0978208742597f17ef6f4c1fe5741f59b5de0739accbce24fa613ab9c7":
            errors.append(f"GOV_CI4_SUPERSEDES_INVALID:{path.name}")
        remediation = data.get("promotion_environment_remediation", {})
        if remediation.get("environment") != "Promotion" or remediation.get("failed_pr") != 431 or remediation.get("consumed_grant") != "R3-GOV-HOM-003-O2-REQ1":
            errors.append(f"GOV_CI4_PROMOTION_ENVIRONMENT_INVALID:{path.name}")
        promotion = data.get("promotion_request_bootstrap")
        expected_grants = [
            "R3-GOV-HOM-004-O2-REQ1",
            "R3-GOV-HOM-004-O3-REQ1",
            "R3-GOV-HOM-004-O4-REQ1",
            "R3-GOV-HOM-004-O5-REQ1",
        ]
        if not isinstance(promotion, dict) or promotion.get("final_wp") != "WP-GOV-CI-004" or promotion.get("static_request_status") != PROMOTION_REQUEST_STATUS or promotion.get("symbolic_bindings") != LEGACY_PROMOTION_BINDINGS or promotion.get("grant_request_ids") != expected_grants:
            errors.append(f"GOV_CI4_PROMOTION_REQUEST_BOOTSTRAP_INVALID:{path.name}")
        if any(term not in denied_terms for term in ("certification", "main", "supabase-free", "supabase-pro", "ddl-execution", "dml-execution", "migration-execution", "backfill-execution", "rls-grants-remote", "workflow_dispatch", "deploys", "secrets")):
            errors.append(f"GOV_CI4_R3_DENY_MISSING:{path.name}")
    elif data.get("id") == "WP-GOV-CI-005":
        required_denies = H2_REQUIRED_DENY_TERMS | {"migration-execution"}
        if data.get("task_id") != "TASK-GOV-CI-005" or data.get("hito") != "GOV-CI":
            errors.append(f"GRAPH_ID_MISMATCH:{path.name}")
        if data.get("target_level") != GOV_OBS_TARGET_LEVEL:
            errors.append(f"GOV_CI5_TARGET_INVALID:{path.name}")
        if data.get("status") != "PROPOSED":
            errors.append(f"GOV_CI5_STATUS_INVALID:{path.name}:must remain PROPOSED before R2 approval")
        if data.get("allowed_paths") != list(GOV_CI5_TRANSITION_ALLOWLIST):
            errors.append(f"GOV_CI5_ALLOWLIST_INVALID:{path.name}")
        baseline = data.get("baseline", {})
        if baseline.get("candidate_commit") != GOV_CI5_BASE_COMMIT or baseline.get("desarrollo_commit") != GOV_CI5_BASE_COMMIT:
            errors.append(f"GOV_CI5_BASELINE_INVALID:{path.name}:candidate/desarrollo_commit")
        if baseline.get("candidate_tree") != "acabd0965d4aa716904917caab691b3867aa5798" or baseline.get("desarrollo_tree") != "acabd0965d4aa716904917caab691b3867aa5798":
            errors.append(f"GOV_CI5_BASELINE_INVALID:{path.name}:candidate/desarrollo_tree")
        if data.get("supersedes_digest") != "e267fd204eb818674f382b72497be25e7a32706ff7061bb080eda4293fa40e86":
            errors.append(f"GOV_CI5_SUPERSEDES_INVALID:{path.name}")
        remediation = data.get("post_merge_promotion_push_boundary", {})
        required_checks = {"merge_commit_two_parents", "first_parent_matches_before", "associated_pr_by_api", "merge_commit_sha_matches_after", "same_repo", "exact_o2_o5_pair", "second_parent_matches_pr_head", "tree_after_matches_pr_head_tree", "promotion_attestation_matches", "promotion_boundary_success", "security_audit_success", "merger_romelhc95", "reviewer_romelhc95_approver", "merger_reviewer_distinct"}
        if not isinstance(remediation, dict) or set(remediation.get("required_evidence", [])) != required_checks or remediation.get("fallback") != "incremental_boundary" or remediation.get("failed_run") != 32615044699:
            errors.append(f"GOV_CI5_POST_MERGE_BOUNDARY_INVALID:{path.name}")
        promotion = data.get("promotion_request_bootstrap")
        expected_grants = [
            "R3-GOV-HOM-005-O2-REQ1",
            "R3-GOV-HOM-005-O3-REQ1",
            "R3-GOV-HOM-005-O4-REQ1",
            "R3-GOV-HOM-005-O5-REQ1",
        ]
        if not isinstance(promotion, dict) or promotion.get("final_wp") != "WP-GOV-CI-005" or promotion.get("static_request_status") != PROMOTION_REQUEST_STATUS or promotion.get("symbolic_bindings") != LEGACY_PROMOTION_BINDINGS or promotion.get("grant_request_ids") != expected_grants:
            errors.append(f"GOV_CI5_PROMOTION_REQUEST_BOOTSTRAP_INVALID:{path.name}")
        if any(term not in denied_terms for term in ("certification", "main", "supabase-free", "supabase-pro", "ddl-execution", "dml-execution", "migration-execution", "backfill-execution", "rls-grants-remote", "workflow_dispatch", "deploys", "secrets")):
            errors.append(f"GOV_CI5_R3_DENY_MISSING:{path.name}")
    elif data.get("id") == "WP-GOV-CI-006":
        required_denies = H2_REQUIRED_DENY_TERMS | {"migration-execution"}
        if data.get("task_id") != "TASK-GOV-CI-006" or data.get("hito") != "GOV-CI":
            errors.append(f"GRAPH_ID_MISMATCH:{path.name}")
        if data.get("target_level") != GOV_OBS_TARGET_LEVEL:
            errors.append(f"GOV_CI6_TARGET_INVALID:{path.name}")
        if data.get("status") != "PROPOSED":
            errors.append(f"GOV_CI6_STATUS_INVALID:{path.name}:must remain PROPOSED before R2 approval")
        if data.get("allowed_paths") != list(GOV_CI6_TRANSITION_ALLOWLIST):
            errors.append(f"GOV_CI6_ALLOWLIST_INVALID:{path.name}")
        baseline = data.get("baseline", {})
        if baseline.get("candidate_commit") != GOV_CI6_BASE_COMMIT or baseline.get("desarrollo_commit") != GOV_CI6_BASE_COMMIT:
            errors.append(f"GOV_CI6_BASELINE_INVALID:{path.name}:candidate/desarrollo_commit")
        if baseline.get("candidate_tree") != "fc9ff315d20648e87d049d5fb244a09ea214bfb8" or baseline.get("desarrollo_tree") != "fc9ff315d20648e87d049d5fb244a09ea214bfb8":
            errors.append(f"GOV_CI6_BASELINE_INVALID:{path.name}:candidate/desarrollo_tree")
        if data.get("supersedes_digest") != "3912d0b7798068c700facfb054360c531b768f251644fef0dbe456ce4b0567cf":
            errors.append(f"GOV_CI6_SUPERSEDES_INVALID:{path.name}")
        legacy = data.get("legacy_gate_retirement", {})
        if legacy.get("workflow") != ".github/workflows/f9-7-contract.yml" or legacy.get("mode") != "MANUAL_FROZEN_ONLY" or set(legacy.get("forbidden_automatic_triggers", [])) != {"pull_request", "push"}:
            errors.append(f"GOV_CI6_LEGACY_RETIREMENT_INVALID:{path.name}")
        contract = data.get("target_aware_promotion_contract", {})
        if contract.get("candidate_parent_1_binding") != "pull_request.base.sha" or contract.get("candidate_parent_2_binding") != "promotion_attestation.Source-SHA" or contract.get("candidate_tree_binding") != "tree(promotion_attestation.Source-SHA)":
            errors.append(f"GOV_CI6_TARGET_AWARE_CONTRACT_INVALID:{path.name}")
        promotion = data.get("promotion_request_bootstrap")
        expected_grants = [
            "R3-GOV-HOM-006-O2-REQ1",
            "R3-GOV-HOM-006-O3-REQ1",
            "R3-GOV-HOM-006-O4-REQ1",
            "R3-GOV-HOM-006-O5-REQ1",
        ]
        if not isinstance(promotion, dict) or promotion.get("final_wp") != "WP-GOV-CI-006" or promotion.get("static_request_status") != PROMOTION_REQUEST_STATUS or promotion.get("symbolic_bindings") != PROMOTION_BINDINGS or promotion.get("grant_request_ids") != expected_grants:
            errors.append(f"GOV_CI6_PROMOTION_REQUEST_BOOTSTRAP_INVALID:{path.name}")
        main_preflight = data.get("main_preflight", {})
        if main_preflight.get("required_result") != "NO_DB_CHANGES" or main_preflight.get("apply_allowed") is not False or main_preflight.get("production_writer_allowed") is not False:
            errors.append(f"GOV_CI6_MAIN_PREFLIGHT_INVALID:{path.name}")
        closure = data.get("non_recursive_closure", {})
        if closure.get("next_h2_manifest") != "WP-H2-002" or closure.get("wp_h2_001_mutation_forbidden") is not True:
            errors.append(f"GOV_CI6_CLOSURE_INVALID:{path.name}")
        if any(term not in denied_terms for term in ("certification", "main", "supabase-free", "supabase-pro", "ddl-execution", "dml-execution", "migration-execution", "backfill-execution", "rls-grants-remote", "workflow_dispatch", "deploys", "secrets")):
            errors.append(f"GOV_CI6_R3_DENY_MISSING:{path.name}")
    elif data.get("id") == "WP-GOV-CI-007":
        required_denies = H2_REQUIRED_DENY_TERMS | {"migration-execution"}
        if data.get("task_id") != "TASK-GOV-CI-007" or data.get("hito") != "GOV-CI":
            errors.append(f"GRAPH_ID_MISMATCH:{path.name}")
        if data.get("target_level") != GOV_OBS_TARGET_LEVEL:
            errors.append(f"GOV_CI7_TARGET_INVALID:{path.name}")
        if data.get("status") != "PROPOSED":
            errors.append(f"GOV_CI7_STATUS_INVALID:{path.name}:must remain PROPOSED before R2 approval")
        if data.get("allowed_paths") != list(GOV_CI7_TRANSITION_ALLOWLIST):
            errors.append(f"GOV_CI7_ALLOWLIST_INVALID:{path.name}")
        baseline = data.get("baseline", {})
        if baseline.get("candidate_commit") != GOV_CI7_BASE_COMMIT or baseline.get("desarrollo_commit") != GOV_CI7_BASE_COMMIT:
            errors.append(f"GOV_CI7_BASELINE_INVALID:{path.name}:candidate/desarrollo_commit")
        if baseline.get("candidate_tree") != "3b956049f3535263b2fdbe3177dc7118005b7af1" or baseline.get("desarrollo_tree") != "3b956049f3535263b2fdbe3177dc7118005b7af1":
            errors.append(f"GOV_CI7_BASELINE_INVALID:{path.name}:candidate/desarrollo_tree")
        if baseline.get("certificacion_commit") != "2134ebfc1af2097b7e17a31b5376bc6942cf020b" or baseline.get("main_commit") != "9b486146962bd2a092acfd649fdcf716e922de89":
            errors.append(f"GOV_CI7_BASELINE_INVALID:{path.name}:branch_commits")
        if data.get("supersedes_digest") != "8b5ac7981acd9d4fada938fe8363e4abfa43acd95cddbe35ab8a5235604a2b2d":
            errors.append(f"GOV_CI7_SUPERSEDES_INVALID:{path.name}")
        remediation = data.get("post_merge_evidence_fail_closed", {})
        if remediation.get("tri_state") != ["VERIFIED_PROMOTION", "NOT_APPLICABLE", "BLOCKED"] or remediation.get("fallback_allowed_only_for") != "NOT_APPLICABLE":
            errors.append(f"GOV_CI7_TRI_STATE_INVALID:{path.name}")
        if remediation.get("failed_pr") != 437 or remediation.get("failed_run") != 32650341464:
            errors.append(f"GOV_CI7_FAILURE_TRACE_INVALID:{path.name}")
        promotion = data.get("promotion_request_bootstrap")
        expected_grants = [
            "R3-GOV-HOM-007-O2-REQ1",
            "R3-GOV-HOM-007-O3-REQ1",
            "R3-GOV-HOM-007-O4-REQ1",
            "R3-GOV-HOM-007-O5-REQ1",
        ]
        if not isinstance(promotion, dict) or promotion.get("final_wp") != "WP-GOV-CI-007" or promotion.get("static_request_status") != PROMOTION_REQUEST_STATUS or promotion.get("symbolic_bindings") != PROMOTION_BINDINGS or promotion.get("grant_request_ids") != expected_grants:
            errors.append(f"GOV_CI7_PROMOTION_REQUEST_BOOTSTRAP_INVALID:{path.name}")
        if data.get("bootstrap_authorization", {}).get("id") != "R1-BOOTSTRAP-GOV-CI-007-REQ2":
            errors.append(f"GOV_CI7_BOOTSTRAP_AUTH_INVALID:{path.name}")
        if any(term not in denied_terms for term in ("certification", "main", "supabase-free", "supabase-pro", "ddl-execution", "dml-execution", "migration-execution", "backfill-execution", "rls-grants-remote", "workflow_dispatch", "deploys", "secrets")):
            errors.append(f"GOV_CI7_R3_DENY_MISSING:{path.name}")
    elif data.get("id") == "WP-GOV-CI-008":
        required_denies = H2_REQUIRED_DENY_TERMS | {"migration-execution"}
        if data.get("task_id") != "TASK-GOV-CI-008" or data.get("hito") != "GOV-CI":
            errors.append(f"GRAPH_ID_MISMATCH:{path.name}")
        if data.get("target_level") != GOV_OBS_TARGET_LEVEL:
            errors.append(f"GOV_CI8_TARGET_INVALID:{path.name}")
        if data.get("status") != "PROPOSED":
            errors.append(f"GOV_CI8_STATUS_INVALID:{path.name}:must remain PROPOSED before R2 approval")
        if data.get("allowed_paths") != list(GOV_CI8_TRANSITION_ALLOWLIST):
            errors.append(f"GOV_CI8_ALLOWLIST_INVALID:{path.name}")
        baseline = data.get("baseline", {})
        if baseline.get("candidate_commit") != GOV_CI8_BASE_COMMIT or baseline.get("desarrollo_commit") != GOV_CI8_BASE_COMMIT:
            errors.append(f"GOV_CI8_BASELINE_INVALID:{path.name}:candidate/desarrollo_commit")
        if baseline.get("candidate_tree") != "29f76f029f9c1c664fd8a9fc2ebda30d75a0a4df" or baseline.get("desarrollo_tree") != "29f76f029f9c1c664fd8a9fc2ebda30d75a0a4df":
            errors.append(f"GOV_CI8_BASELINE_INVALID:{path.name}:candidate/desarrollo_tree")
        if baseline.get("certificacion_commit") != "2134ebfc1af2097b7e17a31b5376bc6942cf020b" or baseline.get("certificacion_tree") != "3b956049f3535263b2fdbe3177dc7118005b7af1" or baseline.get("main_commit") != "9b486146962bd2a092acfd649fdcf716e922de89" or baseline.get("main_tree") != "fcb59095e48441bb4486ccc196aee61e2e1e0fe3":
            errors.append(f"GOV_CI8_BASELINE_INVALID:{path.name}:branch_commits")
        if data.get("supersedes_digest") != "0800d1c01bc174b228d746fa508386d4b8425fb4173ee7f477c516f978a32f41":
            errors.append(f"GOV_CI8_SUPERSEDES_INVALID:{path.name}")
        remediation = data.get("route_classification_fail_closed", {})
        if remediation.get("failed_pr") != 438 or remediation.get("failed_run") != 32655520324 or remediation.get("primary_failure") != "POST_MERGE_PAIR_INVALID":
            errors.append(f"GOV_CI8_FAILURE_TRACE_INVALID:{path.name}")
        if remediation.get("not_applicable_only_for") != "unique ordinary PR to desarrollo" or remediation.get("direct_pushes_blocked") is not True:
            errors.append(f"GOV_CI8_CLASSIFIER_INVALID:{path.name}")
        promotion = data.get("promotion_request_bootstrap")
        expected_grants = [
            "R3-GOV-HOM-008-O2-REQ1",
            "R3-GOV-HOM-008-O3-REQ1",
            "R3-GOV-HOM-008-O4-REQ1",
            "R3-GOV-HOM-008-O5-REQ1",
        ]
        if not isinstance(promotion, dict) or promotion.get("final_wp") != "WP-GOV-CI-008" or promotion.get("static_request_status") != PROMOTION_REQUEST_STATUS or promotion.get("symbolic_bindings") != PROMOTION_BINDINGS or promotion.get("grant_request_ids") != expected_grants:
            errors.append(f"GOV_CI8_PROMOTION_REQUEST_BOOTSTRAP_INVALID:{path.name}")
        if data.get("bootstrap_authorization", {}).get("id") != "R1-BOOTSTRAP-GOV-CI-008-REQ1":
            errors.append(f"GOV_CI8_BOOTSTRAP_AUTH_INVALID:{path.name}")
        if any(term not in denied_terms for term in ("certification", "main", "supabase-free", "supabase-pro", "ddl-execution", "dml-execution", "migration-execution", "backfill-execution", "rls-grants-remote", "workflow_dispatch", "deploys", "secrets")):
            errors.append(f"GOV_CI8_R3_DENY_MISSING:{path.name}")
    elif data.get("id") == "WP-GOV-CI-009":
        required_denies = H2_REQUIRED_DENY_TERMS | {"migration-execution"}
        if data.get("task_id") != "TASK-GOV-CI-009" or data.get("hito") != "GOV-CI":
            errors.append(f"GRAPH_ID_MISMATCH:{path.name}")
        if data.get("target_level") != GOV_OBS_TARGET_LEVEL:
            errors.append(f"GOV_CI9_TARGET_INVALID:{path.name}")
        if data.get("status") != "PROPOSED":
            errors.append(f"GOV_CI9_STATUS_INVALID:{path.name}:must remain PROPOSED before R2 approval")
        if data.get("allowed_paths") != list(GOV_CI9_TRANSITION_ALLOWLIST):
            errors.append(f"GOV_CI9_ALLOWLIST_INVALID:{path.name}")
        baseline = data.get("baseline", {})
        if baseline.get("candidate_commit") != GOV_CI9_BASE_COMMIT or baseline.get("desarrollo_commit") != GOV_CI9_BASE_COMMIT:
            errors.append(f"GOV_CI9_BASELINE_INVALID:{path.name}:candidate/desarrollo_commit")
        if baseline.get("candidate_tree") != "7df05c52da47855d62c082f7cfbd12ee1e38b965" or baseline.get("desarrollo_tree") != "7df05c52da47855d62c082f7cfbd12ee1e38b965":
            errors.append(f"GOV_CI9_BASELINE_INVALID:{path.name}:candidate/desarrollo_tree")
        if baseline.get("certificacion_commit") != "df2cde3626c75fa4733bf1624fb105d8ee08c076" or baseline.get("certificacion_tree") != "7df05c52da47855d62c082f7cfbd12ee1e38b965" or baseline.get("main_commit") != "9b486146962bd2a092acfd649fdcf716e922de89" or baseline.get("main_tree") != "fcb59095e48441bb4486ccc196aee61e2e1e0fe3":
            errors.append(f"GOV_CI9_BASELINE_INVALID:{path.name}:branch_commits")
        if data.get("supersedes_digest") != "8acfacaebd45177241e1d3636430de7cd26530bf9c5fb65b7c6fb8581e50052f":
            errors.append(f"GOV_CI9_SUPERSEDES_INVALID:{path.name}")
        failure = data.get("post_merge_merger_identity_failure", {})
        if failure.get("failed_pr") != 440 or failure.get("failed_run") != 32662084712 or failure.get("primary_failure") != "POST_MERGE_MERGER_INVALID":
            errors.append(f"GOV_CI9_FAILURE_TRACE_INVALID:{path.name}")
        if failure.get("reviewer") != "romelhc95-approver" or failure.get("observed_merger") != "romelhc95" + "-approver" or failure.get("required_merger") != "romelhc95":
            errors.append(f"GOV_CI9_IDENTITY_TRACE_INVALID:{path.name}")
        owner_only = data.get("owner_only_protected_branch_updates", {})
        if owner_only != OWNER_ONLY_RULESET_REQUIRED:
            errors.append(f"GOV_CI9_OWNER_ONLY_RULESET_INVALID:{path.name}")
        protection = data.get("branch_environment_hardening", {})
        if protection.get("main_require_last_push_approval") is not True or protection.get("certification_prevent_self_review") is not True or protection.get("preserve_security_audit_required") is not True:
            errors.append(f"GOV_CI9_PROTECTION_HARDENING_INVALID:{path.name}")
        promotion = data.get("promotion_request_bootstrap")
        expected_grants = [
            "R3-GOV-HOM-009-O2-REQ1",
            "R3-GOV-HOM-009-O3-REQ1",
            "R3-GOV-HOM-009-O4-REQ1",
            "R3-GOV-HOM-009-O5-REQ1",
        ]
        if not isinstance(promotion, dict) or promotion.get("final_wp") != "WP-GOV-CI-009" or promotion.get("static_request_status") != PROMOTION_REQUEST_STATUS or promotion.get("symbolic_bindings") != PROMOTION_BINDINGS or promotion.get("grant_request_ids") != expected_grants:
            errors.append(f"GOV_CI9_PROMOTION_REQUEST_BOOTSTRAP_INVALID:{path.name}")
        historical = data.get("historical_blocks", {})
        if 440 not in historical.get("blocked_pr_numbers", []) or "R3-GOV-HOM-008-O2-REQ1" not in historical.get("consumed_grants", []) or any(f"R3-GOV-HOM-008-O{n}-REQ1" not in historical.get("superseded_grants", []) for n in range(2, 6)):
            errors.append(f"GOV_CI9_HISTORICAL_BLOCKS_INVALID:{path.name}")
        if data.get("bootstrap_authorization", {}).get("id") != "R1-BOOTSTRAP-GOV-CI-009-REQ1":
            errors.append(f"GOV_CI9_BOOTSTRAP_AUTH_INVALID:{path.name}")
        if any(term not in denied_terms for term in ("certification", "main", "supabase-free", "supabase-pro", "ddl-execution", "dml-execution", "migration-execution", "backfill-execution", "rls-grants-remote", "workflow_dispatch", "deploys", "secrets")):
            errors.append(f"GOV_CI9_R3_DENY_MISSING:{path.name}")
    elif data.get("id") == "WP-GOV-CI-010":
        required_denies = H2_REQUIRED_DENY_TERMS | {"migration-execution"}
        if data.get("task_id") != "TASK-GOV-CI-010" or data.get("hito") != "GOV-CI":
            errors.append(f"GRAPH_ID_MISMATCH:{path.name}")
        if data.get("target_level") != GOV_OBS_TARGET_LEVEL:
            errors.append(f"GOV_CI10_TARGET_INVALID:{path.name}")
        if data.get("status") != "PROPOSED":
            errors.append(f"GOV_CI10_STATUS_INVALID:{path.name}:must remain PROPOSED before R2 approval")
        if data.get("allowed_paths") != list(GOV_CI10_TRANSITION_ALLOWLIST):
            errors.append(f"GOV_CI10_ALLOWLIST_INVALID:{path.name}")
        baseline = data.get("baseline", {})
        if baseline.get("candidate_commit") != GOV_CI10_BASE_COMMIT or baseline.get("desarrollo_commit") != GOV_CI10_BASE_COMMIT:
            errors.append(f"GOV_CI10_BASELINE_INVALID:{path.name}:candidate/desarrollo_commit")
        if baseline.get("candidate_tree") != "e0029083e24016b97fc8896be3be2d4285414117" or baseline.get("desarrollo_tree") != "e0029083e24016b97fc8896be3be2d4285414117":
            errors.append(f"GOV_CI10_BASELINE_INVALID:{path.name}:candidate/desarrollo_tree")
        if baseline.get("certificacion_commit") != "df2cde3626c75fa4733bf1624fb105d8ee08c076" or baseline.get("certificacion_tree") != "7df05c52da47855d62c082f7cfbd12ee1e38b965" or baseline.get("main_commit") != "9b486146962bd2a092acfd649fdcf716e922de89" or baseline.get("main_tree") != "fcb59095e48441bb4486ccc196aee61e2e1e0fe3":
            errors.append(f"GOV_CI10_BASELINE_INVALID:{path.name}:branch_commits")
        if data.get("supersedes_digest") != "6f9d309d50b90c18a2703cd6b9170af9af9048f7d80ef749a22a95e8dd8a32ef":
            errors.append(f"GOV_CI10_SUPERSEDES_INVALID:{path.name}")
        failure = data.get("post_merge_attestation_duplicate_failure", {})
        if failure.get("failed_pr") != 441 or failure.get("failed_run") != 32666126533 or failure.get("primary_failure") != "POST_MERGE_ATTESTATION_DUPLICATE":
            errors.append(f"GOV_CI10_FAILURE_TRACE_INVALID:{path.name}")
        section_contract = data.get("section_aware_attestation_contract", {})
        if section_contract.get("no_body_fallback") is not True or section_contract.get("duplicate_scope") != "within_applicable_section" or section_contract.get("ordinary_desarrollo_result") != "NOT_APPLICABLE":
            errors.append(f"GOV_CI10_SECTION_CONTRACT_INVALID:{path.name}")
        if data.get("owner_only_protected_branch_updates") != OWNER_ONLY_RULESET_REQUIRED:
            errors.append(f"GOV_CI10_OWNER_ONLY_RULESET_INVALID:{path.name}")
        promotion = data.get("promotion_request_bootstrap")
        expected_grants = [
            "R3-GOV-HOM-010-O2-REQ1",
            "R3-GOV-HOM-010-O3-REQ1",
            "R3-GOV-HOM-010-O4-REQ1",
            "R3-GOV-HOM-010-O5-REQ1",
        ]
        if not isinstance(promotion, dict) or promotion.get("final_wp") != "WP-GOV-CI-010" or promotion.get("static_request_status") != PROMOTION_REQUEST_STATUS or promotion.get("symbolic_bindings") != PROMOTION_BINDINGS or promotion.get("grant_request_ids") != expected_grants:
            errors.append(f"GOV_CI10_PROMOTION_REQUEST_BOOTSTRAP_INVALID:{path.name}")
        historical = data.get("historical_blocks", {})
        if 441 not in historical.get("blocked_pr_numbers", []) or any(f"R3-GOV-HOM-009-O{n}-REQ1" not in historical.get("superseded_grants", []) for n in range(2, 6)):
            errors.append(f"GOV_CI10_HISTORICAL_BLOCKS_INVALID:{path.name}")
        if data.get("bootstrap_authorization", {}).get("id") != "R1-BOOTSTRAP-GOV-CI-010-REQ1":
            errors.append(f"GOV_CI10_BOOTSTRAP_AUTH_INVALID:{path.name}")
        if any(term not in denied_terms for term in ("certification", "main", "supabase-free", "supabase-pro", "ddl-execution", "dml-execution", "migration-execution", "backfill-execution", "rls-grants-remote", "workflow_dispatch", "deploys", "secrets")):
            errors.append(f"GOV_CI10_R3_DENY_MISSING:{path.name}")
    elif data.get("id") == "WP-GOV-CI-011":
        required_denies = H2_REQUIRED_DENY_TERMS | {"migration-execution"}
        if data.get("task_id") != "TASK-GOV-CI-011" or data.get("hito") != "GOV-CI":
            errors.append(f"GRAPH_ID_MISMATCH:{path.name}")
        if data.get("target_level") != GOV_OBS_TARGET_LEVEL:
            errors.append(f"GOV_CI11_TARGET_INVALID:{path.name}")
        if data.get("status") != "PROPOSED":
            errors.append(f"GOV_CI11_STATUS_INVALID:{path.name}:must remain PROPOSED before R2 approval")
        if data.get("allowed_paths") != list(GOV_CI11_TRANSITION_ALLOWLIST):
            errors.append(f"GOV_CI11_ALLOWLIST_INVALID:{path.name}")
        baseline = data.get("baseline", {})
        if baseline.get("candidate_commit") != GOV_CI11_BASE_COMMIT or baseline.get("desarrollo_commit") != GOV_CI11_BASE_COMMIT:
            errors.append(f"GOV_CI11_BASELINE_INVALID:{path.name}:candidate/desarrollo_commit")
        if baseline.get("candidate_tree") != "99c1cda4f0091aaee35752caec69745051c41a3a" or baseline.get("desarrollo_tree") != "99c1cda4f0091aaee35752caec69745051c41a3a":
            errors.append(f"GOV_CI11_BASELINE_INVALID:{path.name}:candidate/desarrollo_tree")
        if baseline.get("certificacion_commit") != "df2cde3626c75fa4733bf1624fb105d8ee08c076" or baseline.get("certificacion_tree") != "7df05c52da47855d62c082f7cfbd12ee1e38b965" or baseline.get("main_commit") != "9b486146962bd2a092acfd649fdcf716e922de89" or baseline.get("main_tree") != "fcb59095e48441bb4486ccc196aee61e2e1e0fe3":
            errors.append(f"GOV_CI11_BASELINE_INVALID:{path.name}:branch_commits")
        if data.get("supersedes_digest") != "c64a12f0a3208664db4575471bf3425d38c692807debf648db0bc157e091d31c":
            errors.append(f"GOV_CI11_SUPERSEDES_INVALID:{path.name}")
        failure = data.get("hom010_o2_failure", {})
        if failure.get("failed_pr") != 443 or failure.get("status") != "FAILED_NOT_MERGED" or failure.get("consumed_grant") != "R3-GOV-HOM-010-O2-REQ1":
            errors.append(f"GOV_CI11_FAILURE_TRACE_INVALID:{path.name}")
        envelope = data.get("promotion_jit_envelope", {})
        ci11_fields = set(PROMOTION_ENVELOPE_FIELDS) - {"transaction_id", "repository_id", "pr_node_id", "premerge_run_attempt", "event_name", "required_reviewer_id", "required_merger_id", "environment", "environment_id", "ruleset_id", "ruleset_digest", "nonce"} | {"run_attempt"}
        if envelope.get("schema") != "promotion-jit-envelope-v1" or envelope.get("secret_name") != "R3_JIT_APPROVAL_ENVELOPE" or set(envelope.get("required_fields", [])) != ci11_fields:
            errors.append(f"GOV_CI11_ENVELOPE_INVALID:{path.name}")
        if envelope.get("strict_json") is not True or envelope.get("unknown_fields_allowed") is not False or envelope.get("single_active_transaction") is not True:
            errors.append(f"GOV_CI11_ENVELOPE_STRICTNESS_INVALID:{path.name}")
        desired = data.get("promotion_environment_desired_state", {})
        if desired.get("environment") != "Promotion" or desired.get("can_admins_bypass") is not False:
            errors.append(f"GOV_CI11_PROMOTION_ENVIRONMENT_INVALID:{path.name}")
        o3 = data.get("o3_closure", {})
        if o3.get("cloudflare_pages_app_id") != CLOUDFLARE_PAGES_APP_ID or o3.get("cloudflare_check_name") != CLOUDFLARE_PAGES_CHECK_NAME:
            errors.append(f"GOV_CI11_O3_CLOUDFLARE_INVALID:{path.name}")
        if o3.get("db_sync_check_name") != DB_SYNC_DETECT_ONLY_CHECK_NAME or o3.get("db_sync_expected_result") != DB_SYNC_DETECT_ONLY_RESULT or o3.get("db_apply_allowed") is not False:
            errors.append(f"GOV_CI11_O3_DB_SYNC_INVALID:{path.name}")
        if data.get("o4_gate", {}).get("blocked_until_o3_closed") is not True:
            errors.append(f"GOV_CI11_O4_GATE_INVALID:{path.name}")
        promotion = data.get("promotion_request_bootstrap")
        expected_grants = [
            "R3-GOV-HOM-011-O2-REQ1",
            "R3-GOV-HOM-011-O3-REQ1",
            "R3-GOV-HOM-011-O4-REQ1",
            "R3-GOV-HOM-011-O5-REQ1",
        ]
        if not isinstance(promotion, dict) or promotion.get("final_wp") != "WP-GOV-CI-011" or promotion.get("static_request_status") != PROMOTION_REQUEST_STATUS or promotion.get("symbolic_bindings") != PROMOTION_BINDINGS or promotion.get("grant_request_ids") != expected_grants:
            errors.append(f"GOV_CI11_PROMOTION_REQUEST_BOOTSTRAP_INVALID:{path.name}")
        historical = data.get("historical_blocks", {})
        if 443 not in historical.get("blocked_pr_numbers", []) or "R3-GOV-HOM-010-O2-REQ1" not in historical.get("consumed_grants", []) or any(f"R3-GOV-HOM-010-O{n}-REQ1" not in historical.get("superseded_grants", []) for n in range(3, 6)):
            errors.append(f"GOV_CI11_HISTORICAL_BLOCKS_INVALID:{path.name}")
        if data.get("bootstrap_authorization", {}).get("id") != "R1-BOOTSTRAP-GOV-CI-011-REQ1":
            errors.append(f"GOV_CI11_BOOTSTRAP_AUTH_INVALID:{path.name}")
        if any(term not in denied_terms for term in ("certification", "main", "supabase-free", "supabase-pro", "ddl-execution", "dml-execution", "migration-execution", "backfill-execution", "rls-grants-remote", "workflow_dispatch", "deploys", "secrets")):
            errors.append(f"GOV_CI11_R3_DENY_MISSING:{path.name}")
    elif data.get("id") == "WP-GOV-CI-012":
        required_denies = H2_REQUIRED_DENY_TERMS | {"migration-execution"}
        if data.get("task_id") != "TASK-GOV-CI-012" or data.get("hito") != "GOV-CI":
            errors.append(f"GRAPH_ID_MISMATCH:{path.name}")
        if data.get("target_level") != GOV_OBS_TARGET_LEVEL:
            errors.append(f"GOV_CI12_TARGET_INVALID:{path.name}")
        if data.get("status") != "PROPOSED":
            errors.append(f"GOV_CI12_STATUS_INVALID:{path.name}:must remain PROPOSED before R2 approval")
        if data.get("allowed_paths") != list(GOV_CI12_TRANSITION_ALLOWLIST):
            errors.append(f"GOV_CI12_ALLOWLIST_INVALID:{path.name}")
        baseline = data.get("baseline", {})
        if baseline.get("candidate_commit") != GOV_CI12_BASE_COMMIT or baseline.get("desarrollo_commit") != GOV_CI12_BASE_COMMIT:
            errors.append(f"GOV_CI12_BASELINE_INVALID:{path.name}:candidate/desarrollo_commit")
        if baseline.get("candidate_tree") != "bb3a9084961c090adac0d390aa22fdcc84670656" or baseline.get("desarrollo_tree") != "bb3a9084961c090adac0d390aa22fdcc84670656":
            errors.append(f"GOV_CI12_BASELINE_INVALID:{path.name}:candidate/desarrollo_tree")
        if baseline.get("certificacion_commit") != "df2cde3626c75fa4733bf1624fb105d8ee08c076" or baseline.get("certificacion_tree") != "7df05c52da47855d62c082f7cfbd12ee1e38b965" or baseline.get("main_commit") != "9b486146962bd2a092acfd649fdcf716e922de89" or baseline.get("main_tree") != "fcb59095e48441bb4486ccc196aee61e2e1e0fe3":
            errors.append(f"GOV_CI12_BASELINE_INVALID:{path.name}:branch_commits")
        failure = data.get("hom011_o2_failure", {})
        if failure.get("failed_pr") != 445 or failure.get("status") != "FAILED_NOT_MERGED_FROZEN" or failure.get("consumed_grant") != "R3-GOV-HOM-011-O2-REQ1":
            errors.append(f"GOV_CI12_FAILURE_TRACE_INVALID:{path.name}")
        envelope = data.get("promotion_jit_envelope", {})
        if envelope.get("schema") != PROMOTION_ENVELOPE_SCHEMA or envelope.get("secret_name") != "R3_JIT_APPROVAL_ENVELOPE" or set(envelope.get("required_fields", [])) != PROMOTION_ENVELOPE_FIELDS:
            errors.append(f"GOV_CI12_ENVELOPE_INVALID:{path.name}")
        if envelope.get("premerge_artifact_required") is not True or envelope.get("post_merge_secret_dependency") is not False:
            errors.append(f"GOV_CI12_EVIDENCE_FLOW_INVALID:{path.name}")
        desired = data.get("promotion_environment_desired_state", {})
        if desired.get("environment") != "Promotion" or desired.get("single_approval_only") is not True or desired.get("post_merge_environment") is not None:
            errors.append(f"GOV_CI12_PROMOTION_ENVIRONMENT_INVALID:{path.name}")
        o3 = data.get("o3_closure", {})
        if o3.get("cloudflare_pages_app_id") != CLOUDFLARE_PAGES_APP_ID or o3.get("db_sync_expected_result") != DB_SYNC_DETECT_ONLY_RESULT or o3.get("db_apply_allowed") is not False:
            errors.append(f"GOV_CI12_O3_INVALID:{path.name}")
        if o3.get("producer_consumer_artifact") != "o3-closure-evidence.json" or o3.get("clock_controlled_polling") is not True:
            errors.append(f"GOV_CI12_O3_EVIDENCE_INVALID:{path.name}")
        if data.get("o5_closure", {}).get("final_tree_equality_required") is not True or data.get("o5_closure", {}).get("final_ancestry_required") is not True:
            errors.append(f"GOV_CI12_O5_INVALID:{path.name}")
        promotion = data.get("promotion_request_bootstrap")
        expected_grants = [
            "R3-GOV-HOM-012-O2-REQ1",
            "R3-GOV-HOM-012-O3-REQ1",
            "R3-GOV-HOM-012-O4-REQ1",
            "R3-GOV-HOM-012-O5-REQ1",
        ]
        if not isinstance(promotion, dict) or promotion.get("final_wp") != "WP-GOV-CI-012" or promotion.get("static_request_status") != PROMOTION_REQUEST_STATUS or promotion.get("symbolic_bindings") != PROMOTION_BINDINGS or promotion.get("grant_request_ids") != expected_grants:
            errors.append(f"GOV_CI12_PROMOTION_REQUEST_BOOTSTRAP_INVALID:{path.name}")
        historical = data.get("historical_blocks", {})
        if 445 not in historical.get("blocked_pr_numbers", []) or "R3-GOV-HOM-011-O2-REQ1" not in historical.get("consumed_grants", []) or any(f"R3-GOV-HOM-011-O{n}-REQ1" not in historical.get("superseded_grants", []) for n in range(3, 6)):
            errors.append(f"GOV_CI12_HISTORICAL_BLOCKS_INVALID:{path.name}")
        if data.get("bootstrap_authorization", {}).get("id") != "R1-BOOTSTRAP-GOV-CI-012-REQ1":
            errors.append(f"GOV_CI12_BOOTSTRAP_AUTH_INVALID:{path.name}")
    else:
        required_denies = REQUIRED_DENY_TERMS
    if not required_denies <= denied_terms:
        errors.append(f"WP_DENY_TERMS_MISSING:{path.name}:{sorted(required_denies - denied_terms)}")

    if status == "PROPOSED" and any(key in data for key in FORBIDDEN_PROPOSED_KEYS):
        errors.append(f"WP_PROPOSED_APPROVAL_FIELDS:{path.name}")
    if status in {"APPROVED", "ACTIVE", "COMPLETED"}:
        missing_approval = [key for key in APPROVAL_KEYS if not data.get(key)]
        if missing_approval:
            errors.append(f"APPROVAL_METADATA_REQUIRED:{path.name}:{missing_approval}")
        if data.get("approval_digest") != digest:
            errors.append(f"APPROVAL_DIGEST_MISMATCH:{path.name}")
        if parse_utc(data.get("approved_at")) is None:
            errors.append(f"APPROVAL_TIMESTAMP_INVALID:{path.name}")
        if data.get("id") == "WP-H2-001" and data.get("approved_level") != "R1":
            errors.append(f"APPROVAL_LEVEL_INVALID:{path.name}:first H2 approval must be R1")
        if data.get("id") == "WP-H2-001":
            if not HEX40.match(str(data.get("approved_candidate_commit"))):
                errors.append(f"APPROVAL_CANDIDATE_COMMIT_INVALID:{path.name}")
            elif data.get("approved_candidate_commit") != H2_APPROVED_CANDIDATE_COMMIT:
                errors.append(f"APPROVAL_CANDIDATE_COMMIT_MISMATCH:{path.name}")
            if not HEX64.match(str(data.get("approval_evidence_sha256"))):
                errors.append(f"APPROVAL_EVIDENCE_INVALID:{path.name}")
            if status == "APPROVED" and "activated_at" in data:
                errors.append(f"ACTIVATION_PREMATURE:{path.name}:approved work package must not include activated_at")
    if status == "ACTIVE":
        if not data.get("activated_at") or parse_utc(data.get("activated_at")) is None:
            errors.append(f"ACTIVATION_METADATA_REQUIRED:{path.name}")
        approved_at = parse_utc(data.get("approved_at"))
        activated_at = parse_utc(data.get("activated_at"))
        if approved_at and activated_at and activated_at < approved_at:
            errors.append(f"ACTIVATION_TIMESTAMP_INVALID:{path.name}")

    return errors


def active_work_package_from_state(root: Path = ROOT) -> str:
    try:
        state = (root / ".context" / "estado_del_proyecto.md").read_text(encoding="utf-8")
    except FileNotFoundError:
        return "NONE"
    match = re.search(r"^- Work package activo:\s*`([^`]+)`", state, re.MULTILINE)
    return match.group(1) if match else "NONE"


def is_active_r1_manifest(manifest: dict[str, Any], *, active_work_package: str = "NONE") -> bool:
    if active_work_package != "WP-H2-001":
        return False
    if manifest.get("status") != "ACTIVE":
        return False
    if manifest.get("id") != "WP-H2-001":
        return False
    required = {
        "lifecycle_stage": "ACTIVE",
        "gate_status": "APPROVED_R1",
        "approval_target_level": "R1",
        "approved_level": "R1",
    }
    if any(manifest.get(key) != value for key, value in required.items()):
        return False
    if manifest.get("approval_digest") != manifest.get("candidate_digest"):
        return False
    if manifest.get("approved_candidate_commit") != H2_APPROVED_CANDIDATE_COMMIT:
        return False
    if not all(manifest.get(key) for key in APPROVAL_KEYS):
        return False
    if not HEX40.match(str(manifest.get("approved_candidate_commit"))):
        return False
    if not HEX64.match(str(manifest.get("approval_evidence_sha256"))):
        return False
    if parse_utc(manifest.get("approved_at")) is None or parse_utc(manifest.get("activated_at")) is None:
        return False
    if parse_utc(manifest["activated_at"]) < parse_utc(manifest["approved_at"]):
        return False
    expiry = parse_utc(manifest.get("expires_at"))
    if expiry is None or datetime.now(UTC) >= expiry:
        return False
    return compute_digest(manifest) == manifest.get("candidate_digest")


def parse_name_status(raw: bytes) -> list[tuple[str, str]]:
    fields = raw.split(b"\0")
    index = 0
    paths: list[tuple[str, str]] = []
    while index < len(fields) and fields[index]:
        status = fields[index].decode("ascii")
        index += 1
        if status.startswith(("R", "C")):
            paths.append((status, fields[index].decode("utf-8", "surrogateescape")))
            index += 1
        paths.append((status, fields[index].decode("utf-8", "surrogateescape")))
        index += 1
    return paths


def git_status_paths(root: Path = ROOT) -> list[tuple[str, str]]:
    raw = subprocess.check_output(["git", "status", "--porcelain=v1", "-uall", "-z"], cwd=root)
    fields = [field for field in raw.split(b"\0") if field]
    paths: list[tuple[str, str]] = []
    index = 0
    while index < len(fields):
        entry = fields[index].decode("utf-8", "surrogateescape")
        status = entry[:2].strip() or "M"
        path = entry[3:]
        if status.startswith(("R", "C")):
            index += 1
            if index < len(fields):
                paths.append((status, fields[index].decode("utf-8", "surrogateescape")))
        paths.append((status, path))
        index += 1
    return paths


def git_changed_paths(base: str, root: Path = ROOT) -> list[tuple[str, str]]:
    status_paths = git_status_paths(root)
    for command in (
        ["git", "diff", "--name-status", "-z", base, "--"],
        ["git", "diff", "--name-status", "-z", base, "HEAD", "--"],
    ):
        try:
            paths = parse_name_status(subprocess.check_output(command, cwd=root, stderr=subprocess.DEVNULL))
            seen = {(status, path) for status, path in paths}
            for item in status_paths:
                if item not in seen:
                    paths.append(item)
            return paths
        except subprocess.CalledProcessError:
            continue
    paths = status_paths
    try:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True, stderr=subprocess.DEVNULL).strip()
        if head != base:
            paths.extend(parse_name_status(subprocess.check_output(["git", "show", "--name-status", "--format=", "-z", "HEAD"], cwd=root, stderr=subprocess.DEVNULL)))
    except subprocess.CalledProcessError:
        pass
    return paths


def git_sha(args: list[str], root: Path = ROOT) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True, stderr=subprocess.DEVNULL).strip()


def git_is_ancestor(base: str, head: str, root: Path = ROOT) -> bool | None:
    result = subprocess.run(["git", "merge-base", "--is-ancestor", base, head], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    return None


def load_manifest_by_id(wp_id: str, root: Path = ROOT) -> dict[str, Any] | None:
    path = root / ".context" / "work_packages" / f"{wp_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def load_promotion_grant(grant_id: str, root: Path = ROOT) -> dict[str, Any] | None:
    path = root / ".context" / "r3_grants" / f"{grant_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def validate_static_promotion_request(grant: dict[str, Any], *, grant_id: str, operation: str, repo_name: str, base_ref: str, head_ref: str, final_wp_id: str, d_final: str, source_ref: str | None = None, candidate_branch: str | None = None, require_identity: bool = False) -> list[str]:
    errors: list[str] = []
    unknown_keys = set(grant) - STATIC_PROMOTION_REQUEST_KEYS
    if unknown_keys:
        errors.append(f"PROMOTION_GRANT_UNKNOWN_FIELDS:{sorted(unknown_keys)}")
    expected = {
        "id": grant_id,
        "status": PROMOTION_REQUEST_STATUS,
        "operation": operation,
        "repository": repo_name,
        "base_ref": base_ref,
        "head_ref": head_ref,
        "final_wp": final_wp_id,
        "event_action": PROMOTION_ALLOWED_ACTION,
        "run_attempt": 1,
    }
    if final_wp_id in {"WP-GOV-CI-003", "WP-GOV-CI-004", "WP-GOV-CI-005"}:
        expected.update(LEGACY_PROMOTION_BINDINGS)
    else:
        expected.update({
            "source_ref": source_ref or head_ref,
            "candidate_branch": candidate_branch or head_ref,
            **PROMOTION_BINDINGS,
        })
    for key, expected_value in expected.items():
        if grant.get(key) != expected_value:
            errors.append(f"PROMOTION_GRANT_MISMATCH:{key}")
    if require_identity:
        if grant.get("required_merger") != "romelhc95":
            errors.append("PROMOTION_GRANT_MISMATCH:required_merger")
        if grant.get("required_reviewer") != "romelhc95-approver":
            errors.append("PROMOTION_GRANT_MISMATCH:required_reviewer")
        if grant.get("merger_reviewer_distinct") is not True:
            errors.append("PROMOTION_GRANT_MISMATCH:merger_reviewer_distinct")
    if final_wp_id in {"WP-GOV-CI-011", "WP-GOV-CI-012"}:
        expected_schema = "promotion-jit-envelope-v1" if final_wp_id == "WP-GOV-CI-011" else PROMOTION_ENVELOPE_SCHEMA
        if grant.get("approval_envelope_schema") != expected_schema:
            errors.append("PROMOTION_GRANT_MISMATCH:approval_envelope_schema")
        if grant.get("allowed_side_effects") != expected_allowed_side_effects(operation):
            errors.append("PROMOTION_GRANT_MISMATCH:allowed_side_effects")
        if operation.startswith("O4") and grant.get("blocked_until_o3_closed") is not True:
            errors.append("PROMOTION_GRANT_MISMATCH:blocked_until_o3_closed")
        if operation.startswith("O3"):
            if grant.get("cloudflare_pages_production_rebuild_expected") is not True:
                errors.append("PROMOTION_GRANT_MISMATCH:cloudflare_pages_production_rebuild_expected")
            if grant.get("db_sync_detect_only_required") is not True:
                errors.append("PROMOTION_GRANT_MISMATCH:db_sync_detect_only_required")
            if grant.get("db_sync_expected_result") != DB_SYNC_DETECT_ONLY_RESULT:
                errors.append("PROMOTION_GRANT_MISMATCH:db_sync_expected_result")
    if grant.get("single_use") is not True:
        errors.append("PROMOTION_GRANT_MISMATCH:single_use")
    if grant.get("external_consumption_required") is not True:
        errors.append("PROMOTION_GRANT_MISMATCH:external_consumption_required")
    forbidden = {
        "base_sha",
        "candidate_sha",
        "d_final",
        "t_final",
        "approval_reference",
        "approval_expiry",
        "approval_level",
        "consumed",
        "Base-SHA",
        "Candidate-SHA",
        "Source-SHA",
        "Candidate-Tree",
        "D_FINAL",
        "T_FINAL",
        "Approval-Reference",
        "Approval-Expiry",
        "Approval-Level",
    }
    for key in sorted(forbidden & set(grant)):
        errors.append(f"PROMOTION_GRANT_SELF_REFERENCE:{key}")
    return errors


def validate_static_promotion_requests(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    expected: dict[str, tuple[str, str, str, str, str, bool]] = {}
    for family in ("003", "004", "005"):
        final_wp = f"WP-GOV-CI-{family}"
        for op, code, base_ref, source_ref in (
            ("O2 desarrollo -> certificacion", "O2", "certificacion", "desarrollo"),
            ("O3 certificacion -> main", "O3", "main", "certificacion"),
            ("O4 main -> certificacion", "O4", "certificacion", "main"),
            ("O5 certificacion -> desarrollo", "O5", "desarrollo", "certificacion"),
        ):
            expected[f"R3-GOV-HOM-{family}-{code}-REQ1"] = (op, base_ref, source_ref, final_wp, source_ref, False)
    for family in ("006", "007", "008", "009", "010", "011", "012"):
        final_wp = f"WP-GOV-CI-{family}"
        for op, code, base_ref, source_ref in (
            ("O2 desarrollo -> certificacion", "O2", "certificacion", "desarrollo"),
            ("O3 certificacion -> main", "O3", "main", "certificacion"),
            ("O4 main -> certificacion", "O4", "certificacion", "main"),
            ("O5 certificacion -> desarrollo", "O5", "desarrollo", "certificacion"),
        ):
            expected[f"R3-GOV-HOM-{family}-{code}-REQ1"] = (op, base_ref, f"promote/gov-hom-{family}-{code.lower()}-req1", final_wp, source_ref, family in {"007", "008", "009", "010", "011", "012"})
    for grant_id, (operation, base_ref, candidate_branch, final_wp_id, source_ref, require_identity) in expected.items():
        wp = load_manifest_by_id(final_wp_id, root=root)
        d_final = str(wp.get("candidate_digest") if isinstance(wp, dict) else "")
        grant = load_promotion_grant(grant_id, root=root)
        if grant is None:
            errors.append(f"PROMOTION_REQUEST_MISSING:{grant_id}")
            continue
        errors.extend(validate_static_promotion_request(
            grant,
            grant_id=grant_id,
            operation=operation,
            repo_name="romelhc95/studiamatch",
            base_ref=base_ref,
            head_ref=candidate_branch,
            source_ref=source_ref,
            candidate_branch=candidate_branch,
            final_wp_id=final_wp_id,
            d_final=d_final,
            require_identity=require_identity,
        ))
    return errors


def validate_promotion_event(event_path: str, *, event_name: str = "", run_attempt: str = "", now: datetime | None = None, root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    now = now or datetime.now(UTC)
    try:
        event = json.loads(Path(event_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ["PROMOTION_EVENT_INVALID"]

    pr = event.get("pull_request") or {}
    if event_name and event_name != "pull_request":
        errors.append("PROMOTION_EVENT_INVALID")
    if not pr:
        errors.append("PROMOTION_EVENT_INVALID")
        return errors
    if event.get("action") != PROMOTION_ALLOWED_ACTION:
        errors.append("PROMOTION_ACTION_INVALID")
    try:
        attempt = int(run_attempt)
    except (TypeError, ValueError):
        attempt = 0
    if attempt != 1:
        errors.append("PROMOTION_RUN_ATTEMPT_INVALID")
    try:
        pr_number = int(pr.get("number") or event.get("number") or 0)
    except (TypeError, ValueError):
        pr_number = 0
    if pr_number in PROMOTION_BLOCKED_PR_NUMBERS:
        errors.append(f"PROMOTION_PR_BLOCKED:{pr_number}")

    body = str(pr.get("body") or "")
    fields = parse_attestation_fields(body)
    errors.extend(promotion_section_errors(body, "PROMOTION"))
    if governance_section_populated(body):
        errors.append("PROMOTION_GOVERNANCE_SECTION_POPULATED")
    if "__DUPLICATE__" in fields:
        errors.append("PROMOTION_ATTESTATION_DUPLICATE")
    if "__DUPLICATE_SECTION__" in fields:
        errors.append("PROMOTION_ATTESTATION_SECTION_DUPLICATE")
    operation = fields.get("Operation", "")
    expected_pair = PROMOTION_PAIRS.get(operation)
    expected_candidate_branch = PROMOTION_CANDIDATE_BRANCHES.get(operation)
    if expected_pair is None:
        errors.append("PROMOTION_OPERATION_MISMATCH")

    base = pr.get("base") or {}
    head = pr.get("head") or {}
    repo = event.get("repository") or {}
    base_repo = base.get("repo") or {}
    head_repo = head.get("repo") or {}
    repo_name = str(repo.get("full_name") or "")
    if not repo_name or str(base_repo.get("full_name") or "") != repo_name or str(head_repo.get("full_name") or "") != repo_name:
        errors.append("PROMOTION_REPOSITORY_INVALID")
    base_ref = str(base.get("ref") or "")
    head_ref = str(head.get("ref") or "")
    base_sha = str(base.get("sha") or "")
    head_sha = str(head.get("sha") or "")
    source_ref = fields.get("Source-Ref", "")
    source_sha = fields.get("Source-SHA", "")
    if expected_pair and (base_ref, source_ref) != expected_pair:
        errors.append("PROMOTION_PAIR_INVALID")
    if expected_candidate_branch and head_ref != expected_candidate_branch:
        errors.append("PROMOTION_CANDIDATE_BRANCH_INVALID")
    grant_id = fields.get("Grant-ID", "")
    operation_code = operation.split(" ", 1)[0] if operation else ""
    if not PROMOTION_GRANT_ID_PATTERN.match(grant_id):
        errors.append("PROMOTION_GRANT_ID_INVALID")
    if grant_id in PROMOTION_CONSUMED_GRANTS:
        errors.append("PROMOTION_GRANT_CONSUMED")
    if grant_id in PROMOTION_SUPERSEDED_GRANTS:
        errors.append("PROMOTION_GRANT_SUPERSEDED")
    if not grant_id or not operation_code or f"-{operation_code}-" not in grant_id:
        errors.append("PROMOTION_GRANT_ID_MISMATCH")
    grant = load_promotion_grant(grant_id, root=root) if grant_id else None
    if grant is None:
        errors.append("PROMOTION_GRANT_NOT_FOUND")

    attested_base = fields.get("Base-SHA", "")
    if fields.get("Base-Ref", "") != base_ref:
        errors.append("PROMOTION_BASE_REF_MISMATCH")
    if not HEX40.match(base_sha) or not HEX40.match(attested_base):
        errors.append("PROMOTION_BASE_SHA_INVALID")
    elif base_sha != attested_base:
        errors.append("PROMOTION_BASE_SHA_MISMATCH")

    attested_head = fields.get("Candidate-SHA", "")
    if not HEX40.match(head_sha) or not HEX40.match(attested_head):
        errors.append("PROMOTION_CANDIDATE_SHA_INVALID")
    elif head_sha != attested_head:
        errors.append("PROMOTION_CANDIDATE_SHA_MISMATCH")

    if not HEX40.match(source_sha):
        errors.append("PROMOTION_SOURCE_SHA_INVALID")
    elif source_ref:
        try:
            remote_source = git_sha(["rev-parse", f"origin/{source_ref}"], root=root)
            if remote_source != source_sha:
                errors.append("PROMOTION_SOURCE_SHA_MISMATCH")
        except subprocess.CalledProcessError:
            errors.append("PROMOTION_SOURCE_SHA_UNRESOLVED")

    final_wp_id = fields.get("Final-WP", "")
    if final_wp_id != PROMOTION_FINAL_WP:
        errors.append("PROMOTION_FINAL_WP_INVALID")
    final_wp = load_manifest_by_id(final_wp_id, root=root)
    if final_wp is None:
        errors.append("PROMOTION_FINAL_WP_NOT_FOUND")

    d_final = fields.get("D_FINAL", "")
    if not HEX64.match(d_final):
        errors.append("PROMOTION_FINAL_DIGEST_INVALID")
    elif final_wp is not None and (final_wp.get("candidate_digest") != d_final or compute_digest(final_wp) != d_final):
        errors.append("PROMOTION_FINAL_DIGEST_MISMATCH")

    t_final = fields.get("T_FINAL", "")
    candidate_tree = fields.get("Candidate-Tree", "")
    if not HEX40.match(candidate_tree):
        errors.append("PROMOTION_CANDIDATE_TREE_INVALID")
    elif HEX40.match(head_sha):
        try:
            if git_sha(["rev-parse", f"{head_sha}^{{tree}}"], root=root) != candidate_tree:
                errors.append("PROMOTION_CANDIDATE_TREE_MISMATCH")
        except subprocess.CalledProcessError:
            errors.append("PROMOTION_CANDIDATE_TREE_MISMATCH")
    if not HEX40.match(t_final):
        errors.append("PROMOTION_FINAL_TREE_INVALID")
    elif HEX40.match(source_sha):
        try:
            if git_sha(["rev-parse", f"{source_sha}^{{tree}}"], root=root) != t_final:
                errors.append("PROMOTION_FINAL_TREE_MISMATCH")
        except subprocess.CalledProcessError:
            errors.append("PROMOTION_FINAL_TREE_MISMATCH")

    if HEX40.match(base_sha) and HEX40.match(head_sha) and git_is_ancestor(base_sha, head_sha, root=root) is not True:
        errors.append("PROMOTION_ANCESTRY_INVALID")
    if HEX40.match(base_sha) and HEX40.match(source_sha) and HEX40.match(head_sha):
        try:
            parents = git_sha(["show", "-s", "--format=%P", head_sha], root=root).split()
            if parents != [base_sha, source_sha]:
                errors.append("PROMOTION_CANDIDATE_PARENTS_INVALID")
        except subprocess.CalledProcessError:
            errors.append("PROMOTION_CANDIDATE_PARENTS_INVALID")

    if HEX40.match(head_sha):
        try:
            head_tree = git_sha(["rev-parse", f"{head_sha}^{{tree}}"], root=root)
            if git_sha(["rev-parse", "HEAD^{tree}"], root=root) != head_tree or (HEX40.match(t_final) and head_tree != t_final):
                errors.append("PROMOTION_SYNTHETIC_TREE_MISMATCH")
        except subprocess.CalledProcessError:
            errors.append("PROMOTION_SYNTHETIC_TREE_MISMATCH")

    if fields.get("Approval-Level") != "R3 JIT single-use":
        errors.append("PROMOTION_OPERATION_MISMATCH")
    approval_ref = fields.get("Approval-Reference", "")
    if not approval_ref or approval_ref in {"TODO", "N/A", "none", "<approval-reference>"}:
        errors.append("PROMOTION_APPROVAL_REFERENCE_REQUIRED")
    expiry = parse_utc(fields.get("Approval-Expiry", ""))
    if expiry is None or now >= expiry:
        errors.append("PROMOTION_APPROVAL_EXPIRED")
    envelope, envelope_errors = decode_promotion_envelope(os.environ.get("R3_JIT_APPROVAL_ENVELOPE", ""))
    errors.extend(envelope_errors)
    if envelope:
        values = envelope_values(envelope)
        if values["grant_id"] != grant_id:
            errors.append("PROMOTION_APPROVAL_GRANT_ID_MISMATCH")
        if values["reference"] != approval_ref:
            errors.append("PROMOTION_APPROVAL_REFERENCE_MISMATCH")
        if values["expiry"] != fields.get("Approval-Expiry", "") or parse_utc(values["expiry"]) != expiry:
            errors.append("PROMOTION_APPROVAL_EXPIRY_MISMATCH")
        errors.extend(validate_envelope_bindings(envelope, event=event, fields=fields, pr=pr, expected_digest=d_final, expected_tree=t_final, now=now))

    if grant is not None:
        errors.extend(validate_static_promotion_request(
            grant,
            grant_id=grant_id,
            operation=operation,
            repo_name=repo_name,
            base_ref=base_ref,
            head_ref=head_ref,
            source_ref=source_ref,
            candidate_branch=head_ref,
            final_wp_id=final_wp_id,
            d_final=d_final,
            require_identity=final_wp_id not in {"WP-GOV-CI-003", "WP-GOV-CI-004", "WP-GOV-CI-005", "WP-GOV-CI-006"},
        ))

    return errors


class GitHubEvidenceError(RuntimeError):
    pass


class GitHubSchemaError(GitHubEvidenceError):
    pass


def retry_after_seconds(value: str | None) -> float:
    if not value:
        return 0.0
    try:
        return max(0.0, min(float(value), 5.0))
    except ValueError:
        try:
            parsed = parsedate_to_datetime(value)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=UTC)
            return max(0.0, min((parsed - datetime.now(UTC)).total_seconds(), 5.0))
        except (TypeError, ValueError):
            return 0.0


def parse_link_next(link: str | None) -> str | None:
    if not link:
        return None
    for part in link.split(","):
        section = part.strip()
        if 'rel="next"' not in section:
            continue
        match = re.match(r"<([^>]+)>", section)
        if match:
            return match.group(1)
    return None


def github_api_json(path: str, *, paginate: bool = False, max_pages: int = 10, deadline: float | None = None) -> Any:
    token = os.environ.get("GITHUB_TOKEN", "")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if not token or not repo:
        raise GitHubEvidenceError("github api requires GITHUB_TOKEN and GITHUB_REPOSITORY")
    deadline = deadline or (time.monotonic() + 30.0)
    url = path if path.startswith("https://api.github.com/") else f"https://api.github.com/repos/{repo}/{path.lstrip('/')}"
    pages: list[Any] = []
    page_count = 0
    while url:
        page_count += 1
        if page_count > max_pages:
            raise GitHubEvidenceError("github api pagination limit exceeded")
        attempt = 0
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise GitHubEvidenceError("github api retry budget exhausted")
            request = urllib.request.Request(url, headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": "2022-11-28",
            })
            try:
                with urllib.request.urlopen(request, timeout=min(10.0, remaining)) as response:
                    raw = response.read().decode("utf-8")
                    try:
                        data = json.loads(raw)
                    except json.JSONDecodeError as exc:
                        raise GitHubSchemaError("github api malformed json") from exc
                    next_url = parse_link_next(response.headers.get("Link"))
                    break
            except urllib.error.HTTPError as exc:
                retryable = exc.code == 404 or exc.code == 429 or 500 <= exc.code <= 599
                rate_limited = exc.code == 403 and (exc.headers.get("X-RateLimit-Remaining") == "0" or exc.headers.get("Retry-After"))
                if exc.code in {401, 403} and not rate_limited:
                    raise GitHubEvidenceError(f"github api auth failure {exc.code}") from exc
                if not (retryable or rate_limited) or attempt >= 3:
                    raise GitHubEvidenceError(f"github api unavailable {exc.code}") from exc
                delay = retry_after_seconds(exc.headers.get("Retry-After")) or min(0.25 * (2 ** attempt), 2.0)
            except (TimeoutError, urllib.error.URLError) as exc:
                if attempt >= 3:
                    raise GitHubEvidenceError("github api network failure") from exc
                delay = min(0.25 * (2 ** attempt), 2.0)
            attempt += 1
            if time.monotonic() + delay > deadline:
                raise GitHubEvidenceError("github api retry budget exhausted")
            time.sleep(delay)
        if not paginate:
            return data
        pages.append(data)
        url = next_url
    flattened: list[Any] = []
    for page in pages:
        if isinstance(page, list):
            flattened.extend(page)
        elif isinstance(page, dict) and isinstance(page.get("check_runs"), list):
            flattened.extend(page["check_runs"])
        else:
            raise GitHubSchemaError("github api paginated schema invalid")
    return flattened


def github_api_bytes(url: str, *, deadline: float | None = None) -> bytes:
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        raise GitHubEvidenceError("github api requires GITHUB_TOKEN")
    deadline = deadline or (time.monotonic() + 30.0)
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise GitHubEvidenceError("github api retry budget exhausted")
    request = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with urllib.request.urlopen(request, timeout=min(10.0, remaining)) as response:
        return response.read()


def payload_digest_valid(payload: dict[str, Any]) -> bool:
    digest = payload.get("payload_sha256")
    if not isinstance(digest, str) or not HEX64.match(digest):
        return False
    signed = {key: value for key, value in payload.items() if key != "payload_sha256"}
    raw = json.dumps(signed, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest() == digest


def load_single_json_from_zip(raw: bytes, *, expected_member: str, max_size: int = 128_000) -> dict[str, Any]:
    if len(raw) > max_size * 4:
        raise GitHubEvidenceError("artifact archive too large")
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = [name for name in archive.namelist() if not name.endswith("/")]
        if names != [expected_member]:
            raise GitHubEvidenceError("artifact archive member mismatch")
        info = archive.getinfo(expected_member)
        if info.file_size > max_size:
            raise GitHubEvidenceError("artifact json too large")
        data = json.loads(archive.read(expected_member).decode("utf-8"))
    if not isinstance(data, dict):
        raise GitHubSchemaError("artifact json root must be object")
    return data


def load_workflow_artifact_json(run_id: int, *, artifact_name: str, expected_member: str, deadline: float | None = None) -> dict[str, Any]:
    deadline = deadline or (time.monotonic() + 30.0)
    listing = github_api_json(f"actions/runs/{run_id}/artifacts?per_page=100", deadline=deadline)
    artifacts = listing.get("artifacts") if isinstance(listing, dict) else None
    if not isinstance(artifacts, list):
        raise GitHubSchemaError("workflow artifacts schema invalid")
    matches = [item for item in artifacts if isinstance(item, dict) and item.get("name") == artifact_name and item.get("expired") is not True]
    if len(matches) != 1:
        raise GitHubEvidenceError("workflow artifact count invalid")
    raw = github_api_bytes(str(matches[0].get("archive_download_url") or ""), deadline=deadline)
    return load_single_json_from_zip(raw, expected_member=expected_member)


def approval_artifact_name(pr_number: int, run_id: int) -> str:
    return f"promotion-approval-evidence-pr-{pr_number}-run-{run_id}"


def load_promotion_approval_evidence(run_id: int, pr_number: int, *, deadline: float | None = None) -> dict[str, Any]:
    evidence = load_workflow_artifact_json(
        run_id,
        artifact_name=approval_artifact_name(pr_number, run_id),
        expected_member=PROMOTION_APPROVAL_EVIDENCE_FILE,
        deadline=deadline,
    )
    if evidence.get("schema") != "promotion-approval-evidence-v1" or evidence.get("artifact_name") != f"promotion-approval-evidence-pr-{pr_number}-run-{run_id}.json":
        raise GitHubEvidenceError("promotion approval artifact identity invalid")
    if evidence.get("premerge_run_id") != run_id or evidence.get("premerge_run_attempt") != 1:
        raise GitHubEvidenceError("promotion approval artifact run invalid")
    if not payload_digest_valid(evidence):
        raise GitHubEvidenceError("promotion approval artifact digest invalid")
    if not isinstance(evidence.get("envelope"), dict):
        raise GitHubEvidenceError("promotion approval artifact envelope invalid")
    envelope = evidence.get("envelope") or {}
    if any(key in evidence for key in ("deployment_approval_id", "deployment_approval", "approved_at", "environment_name")):
        raise GitHubEvidenceError("promotion approval legacy fields invalid")
    review = evidence.get("environment_review")
    if not isinstance(review, dict):
        raise GitHubEvidenceError("promotion approval review invalid")
    if evidence.get("environment_review_digest") != digest_json(review):
        raise GitHubEvidenceError("promotion approval review digest invalid")
    reviewer = review.get("reviewer") or {}
    environment = review.get("environment") or {}
    if reviewer.get("login") != "romelhc95-approver" or reviewer.get("id") != 306979205:
        raise GitHubEvidenceError("promotion approval reviewer invalid")
    if environment.get("name") != "Promotion" or environment.get("id") != envelope.get("environment_id"):
        raise GitHubEvidenceError("promotion approval environment invalid")
    if review.get("state") != "approved" or parse_utc(review.get("created_at")) is None:
        raise GitHubEvidenceError("promotion approval state invalid")
    if evidence.get("jit_approval_reference") != envelope.get("approval_id"):
        raise GitHubEvidenceError("promotion approval reference invalid")
    if evidence.get("promotion_boundary_job_id") in {None, "", run_id}:
        raise GitHubEvidenceError("promotion approval job invalid")
    return evidence


def load_promotion_approval_artifact(run_id: int, pr_number: int, *, deadline: float | None = None) -> dict[str, Any]:
    evidence = load_promotion_approval_evidence(run_id, pr_number, deadline=deadline)
    protected = {"envelope": evidence.get("envelope")}
    return protected


def load_repo_artifact_json(*, artifact_name: str, expected_member: str, deadline: float | None = None) -> dict[str, Any]:
    deadline = deadline or (time.monotonic() + 30.0)
    listing = github_api_json("actions/artifacts?per_page=100", deadline=deadline)
    artifacts = listing.get("artifacts") if isinstance(listing, dict) else None
    if not isinstance(artifacts, list):
        raise GitHubSchemaError("repo artifacts schema invalid")
    matches = [item for item in artifacts if isinstance(item, dict) and item.get("name") == artifact_name and item.get("expired") is not True]
    if len(matches) != 1:
        raise GitHubEvidenceError("repo artifact count invalid")
    raw = github_api_bytes(str(matches[0].get("archive_download_url") or ""), deadline=deadline)
    return load_single_json_from_zip(raw, expected_member=expected_member)


def o3_closure_artifact_name(main_sha: str) -> str:
    return f"o3-closure-evidence-{main_sha}"


def load_o3_closure_artifact(main_sha: str, *, deadline: float | None = None) -> dict[str, Any]:
    closure = load_repo_artifact_json(
        artifact_name=o3_closure_artifact_name(main_sha),
        expected_member=O3_CLOSURE_EVIDENCE_FILE,
        deadline=deadline,
    )
    if closure.get("schema") != "o3-closure-evidence-v1" or closure.get("status") != "CLOSED" or closure.get("main_merge_sha") != main_sha:
        raise GitHubEvidenceError("o3 closure artifact identity invalid")
    if closure.get("cloudflare_pages_app_id") != CLOUDFLARE_PAGES_APP_ID or closure.get("db_sync_app_id") != GITHUB_ACTIONS_APP_ID:
        raise GitHubEvidenceError("o3 closure artifact producer invalid")
    if closure.get("db_sync_result") != DB_SYNC_DETECT_ONLY_RESULT or closure.get("db_changed") is not False or closure.get("apply_executed") is not False:
        raise GitHubEvidenceError("o3 closure db contract invalid")
    if closure.get("db_sync_artifact_head_sha") != main_sha:
        raise GitHubEvidenceError("o3 closure db artifact sha invalid")
    if not payload_digest_valid(closure):
        raise GitHubEvidenceError("o3 closure artifact digest invalid")
    return closure


def github_api_json_until(path: str, predicate, *, paginate: bool = False, deadline: float | None = None) -> Any:
    deadline = deadline or (time.monotonic() + 30.0)
    attempt = 0
    while True:
        data = github_api_json(path, paginate=paginate, deadline=deadline)
        if predicate(data):
            return data
        delay = min(0.25 * (2 ** attempt), 2.0)
        attempt += 1
        if time.monotonic() + delay > deadline:
            raise GitHubEvidenceError("github api evidence remained incomplete")
        time.sleep(delay)


def load_post_merge_evidence(after_sha: str) -> dict[str, Any]:
    evidence_path = os.environ.get("PROMOTION_POST_MERGE_EVIDENCE_PATH", "")
    if evidence_path:
        data = json.loads(Path(evidence_path).read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise GitHubSchemaError("post-merge evidence root must be object")
        return data
    deadline = time.monotonic() + 30.0
    pulls = github_api_json_until(f"commits/{after_sha}/pulls?per_page=100", lambda value: isinstance(value, list) and bool(value), paginate=True, deadline=deadline)
    if len(pulls) != 1:
        return {"ambiguous_pull_requests": len(pulls)}
    pr = pulls[0]
    if not isinstance(pr, dict) or not isinstance(pr.get("number"), int):
        raise GitHubSchemaError("commit pull association schema invalid")
    number = pr.get("number")
    pr = github_api_json(f"pulls/{number}", deadline=deadline)
    if not isinstance(pr, dict):
        raise GitHubSchemaError("pull request schema invalid")
    head_sha = pr.get("head", {}).get("sha", "") if isinstance(pr.get("head"), dict) else ""
    head_checks = github_api_json_until(f"commits/{head_sha}/check-runs?per_page=100", lambda value: isinstance(value, list) and bool(value), paginate=True, deadline=deadline)
    after_checks = github_api_json(f"commits/{after_sha}/check-runs?per_page=100", paginate=True, deadline=deadline)
    if not isinstance(after_checks, list):
        raise GitHubSchemaError("merge commit check-runs schema invalid")
    checks = head_checks + after_checks
    reviews = github_api_json(f"pulls/{number}/reviews?per_page=100", paginate=True, deadline=deadline)
    timeline = github_api_json(f"issues/{number}/timeline?per_page=100", paginate=True, deadline=deadline)
    return {"pull_request": pr, "checks": checks, "reviews": reviews, "timeline": timeline}


def check_run_id(check: dict[str, Any]) -> int:
    try:
        return int(check.get("id") or 0)
    except (TypeError, ValueError):
        return 0


def workflow_run_id_from_details(details_url: Any) -> int | None:
    if not isinstance(details_url, str):
        return None
    match = re.search(r"/actions/runs/(\d+)", details_url)
    return int(match.group(1)) if match else None


def latest_check_run(checks: list[dict[str, Any]], name: str, *, head_sha: str, pr_number: int, pr_created_at: datetime, pr_merged_at: datetime, allow_empty_pull_requests: bool, app_id: int = GITHUB_ACTIONS_APP_ID) -> tuple[dict[str, Any] | None, str | None]:
    matching: list[tuple[datetime, int, dict[str, Any]]] = []
    for check in checks:
        if not isinstance(check, dict):
            return None, "POST_MERGE_CHECK_SCHEMA_INVALID"
        if check.get("name") != name:
            continue
        if check.get("head_sha") != head_sha:
            continue
        app = check.get("app") or {}
        if app.get("id") != app_id:
            continue
        pull_numbers = [item.get("number") for item in check.get("pull_requests", []) if isinstance(item, dict)]
        if pull_numbers:
            if pull_numbers != [pr_number]:
                return None, "POST_MERGE_CHECK_PR_ASSOCIATION_INVALID"
        elif not allow_empty_pull_requests:
            return None, "POST_MERGE_CHECK_PR_ASSOCIATION_MISSING"
        started_at = parse_utc(str(check.get("started_at") or ""))
        completed_at = parse_utc(str(check.get("completed_at") or ""))
        updated_at = parse_utc(str(check.get("updated_at") or ""))
        ordering_time = completed_at or updated_at
        if started_at is None or completed_at is None or updated_at is None or ordering_time is None:
            return None, "POST_MERGE_CHECK_TIMESTAMP_INVALID"
        if started_at > completed_at or completed_at > updated_at:
            return None, "POST_MERGE_CHECK_TIMESTAMP_INVALID"
        if started_at < pr_created_at or updated_at > pr_merged_at:
            return None, "POST_MERGE_CHECK_TIME_WINDOW_INVALID"
        if app_id == GITHUB_ACTIONS_APP_ID and workflow_run_id_from_details(check.get("details_url")) is None:
            return None, "POST_MERGE_WORKFLOW_RUN_MISSING"
        matching.append((ordering_time, check_run_id(check), check))
    if not matching:
        return None, "POST_MERGE_REQUIRED_CHECK_MISSING"
    latest = max(matching, key=lambda item: (item[0], item[1]))[2]
    if latest.get("status") != "completed" or latest.get("conclusion") != "success":
        return None, "POST_MERGE_REQUIRED_CHECK_MISSING"
    return latest, None


def db_sync_detect_only_result(check: dict[str, Any]) -> str:
    output = check.get("output") or {}
    text = "\n".join(str(output.get(key) or "") for key in ("title", "summary", "text"))
    if DB_SYNC_DETECT_ONLY_RESULT in text:
        return DB_SYNC_DETECT_ONLY_RESULT
    return ""


def require_workflow_run(run: dict[str, Any], *, run_id: int, head_sha: str, head_branch: str, pr_created_at: datetime, pr_merged_at: datetime) -> str | None:
    if not isinstance(run, dict) or run.get("id") != run_id:
        return "POST_MERGE_WORKFLOW_RUN_MISMATCH"
    if run.get("repository", {}).get("full_name") != "romelhc95/studiamatch":
        return "POST_MERGE_WORKFLOW_REPOSITORY_INVALID"
    if run.get("event") != "pull_request":
        return "POST_MERGE_WORKFLOW_EVENT_INVALID"
    if run.get("head_sha") != head_sha or run.get("head_branch") != head_branch:
        return "POST_MERGE_WORKFLOW_HEAD_INVALID"
    if run.get("run_attempt") != 1:
        return "POST_MERGE_WORKFLOW_ATTEMPT_INVALID"
    path = str((run.get("path") or run.get("workflow", {}).get("path") or ""))
    if path != ".github/workflows/security-audit.yml":
        return "POST_MERGE_WORKFLOW_PATH_INVALID"
    if run.get("status") != "completed" or run.get("conclusion") != "success":
        return "POST_MERGE_WORKFLOW_RESULT_INVALID"
    created_at = parse_utc(run.get("created_at"))
    updated_at = parse_utc(run.get("updated_at"))
    if created_at is None or updated_at is None:
        return "POST_MERGE_WORKFLOW_TIMESTAMP_INVALID"
    if created_at < pr_created_at or updated_at > pr_merged_at:
        return "POST_MERGE_WORKFLOW_TIME_WINDOW_INVALID"
    return None


def latest_effective_review_state(reviews: list[dict[str, Any]], login: str) -> dict[str, Any] | None:
    matching: list[tuple[datetime, int, dict[str, Any]]] = []
    for review in reviews:
        if (review.get("user") or {}).get("login") != login:
            continue
        submitted_at = parse_utc(str(review.get("submitted_at") or ""))
        if submitted_at is None:
            continue
        matching.append((submitted_at, check_run_id(review), review))
    if not matching:
        return None
    return max(matching, key=lambda item: (item[0], item[1]))[2]


def validate_reviews_schema(reviews: Any) -> str | None:
    if not isinstance(reviews, list) or any(not isinstance(review, dict) for review in reviews):
        return "POST_MERGE_REVIEW_SCHEMA_INVALID"
    return None


def approved_review_by(reviews: list[dict[str, Any]], login: str, *, commit_id: str) -> bool:
    latest = latest_effective_review_state(reviews, login)
    return bool(latest and latest.get("state") == "APPROVED" and latest.get("commit_id") == commit_id)


def decode_promotion_envelope(raw: str) -> tuple[dict[str, Any] | None, list[str]]:
    if not raw:
        return None, ["PROMOTION_APPROVAL_ENVELOPE_REQUIRED"]
    try:
        envelope = json.loads(raw)
    except json.JSONDecodeError:
        return None, ["PROMOTION_APPROVAL_ENVELOPE_JSON_INVALID"]
    if not isinstance(envelope, dict):
        return None, ["PROMOTION_APPROVAL_ENVELOPE_JSON_INVALID"]
    unknown = set(envelope) - PROMOTION_ENVELOPE_FIELDS
    missing = PROMOTION_ENVELOPE_FIELDS - set(envelope)
    errors: list[str] = []
    if unknown:
        errors.append("PROMOTION_APPROVAL_ENVELOPE_UNKNOWN_FIELDS")
    if missing:
        errors.append("PROMOTION_APPROVAL_ENVELOPE_MISSING_FIELDS")
    if envelope.get("schema") != PROMOTION_ENVELOPE_SCHEMA:
        errors.append("PROMOTION_APPROVAL_ENVELOPE_SCHEMA_INVALID")
    return envelope, errors


def envelope_values(envelope: dict[str, Any] | None) -> dict[str, str]:
    if not envelope:
        return {"grant_id": "", "reference": "", "expiry": ""}
    return {
        "grant_id": str(envelope.get("grant_id") or ""),
        "reference": str(envelope.get("approval_id") or ""),
        "expiry": str(envelope.get("expires_at") or ""),
    }


def expected_allowed_side_effects(operation: str) -> list[str]:
    if operation.startswith("O2"):
        return ["certification_branch_update"]
    if operation.startswith("O3"):
        return ["main_branch_update", "cloudflare_pages_production_rebuild", "db_sync_detect_only"]
    if operation.startswith("O4"):
        return ["certification_branch_update"]
    if operation.startswith("O5"):
        return ["development_branch_update"]
    return []


def validate_envelope_bindings(envelope: dict[str, Any], *, event: dict[str, Any], fields: dict[str, str], pr: dict[str, Any], expected_digest: str, expected_tree: str, require_premerge_run: bool = True, now: datetime | None = None) -> list[str]:
    now = now or datetime.now(UTC)
    errors: list[str] = []
    base = pr.get("base") or {}
    head = pr.get("head") or {}
    expected = {
        "repository_id": (event.get("repository") or {}).get("id"),
        "repository": (event.get("repository") or {}).get("full_name"),
        "operation": fields.get("Operation"),
        "pr_number": int(pr.get("number") or event.get("number") or 0),
        "event_name": "pull_request",
        "event_action": PROMOTION_ALLOWED_ACTION,
        "premerge_run_attempt": 1,
        "base_ref": base.get("ref"),
        "base_sha": base.get("sha"),
        "source_ref": fields.get("Source-Ref"),
        "source_sha": fields.get("Source-SHA"),
        "candidate_ref": head.get("ref"),
        "candidate_sha": head.get("sha"),
        "candidate_tree": fields.get("Candidate-Tree"),
        "final_wp": fields.get("Final-WP"),
        "final_digest": expected_digest,
        "final_tree": expected_tree,
        "required_reviewer": "romelhc95-approver",
        "required_reviewer_id": 306979205,
        "required_merger": "romelhc95",
        "required_merger_id": 18040405,
        "environment": "Promotion",
    }
    for key, expected_value in expected.items():
        if expected_value is None:
            continue
        if envelope.get(key) != expected_value:
            errors.append(f"PROMOTION_APPROVAL_ENVELOPE_MISMATCH:{key}")
    if require_premerge_run:
        try:
            run_id = int(envelope.get("premerge_run_id"))
        except (TypeError, ValueError):
            run_id = 0
        if run_id <= 0:
            errors.append("PROMOTION_APPROVAL_ENVELOPE_MISMATCH:premerge_run_id")
        current_run_id = os.environ.get("GITHUB_RUN_ID", "")
        if current_run_id and str(run_id) != current_run_id:
            errors.append("PROMOTION_APPROVAL_ENVELOPE_MISMATCH:premerge_run_id")
    if envelope.get("allowed_side_effects") != expected_allowed_side_effects(fields.get("Operation", "")):
        errors.append("PROMOTION_APPROVAL_ENVELOPE_MISMATCH:allowed_side_effects")
    ruleset_digest = str(envelope.get("ruleset_digest") or "")
    expected_ruleset_digest = os.environ.get("PROMOTION_RULESET_DIGEST", "")
    if not ruleset_digest.startswith("sha256:"):
        errors.append("PROMOTION_APPROVAL_ENVELOPE_MISMATCH:ruleset_digest")
    if expected_ruleset_digest and ruleset_digest != expected_ruleset_digest:
        errors.append("PROMOTION_APPROVAL_ENVELOPE_MISMATCH:ruleset_digest")
    for key in ("repository_id", "environment_id", "ruleset_id", "required_reviewer_id", "required_merger_id", "premerge_run_id", "pr_number"):
        if not isinstance(envelope.get(key), int) or envelope[key] <= 0:
            errors.append(f"PROMOTION_APPROVAL_ENVELOPE_MISMATCH:{key}")
    if not isinstance(envelope.get("pr_node_id"), str) or not envelope["pr_node_id"].strip():
        errors.append("PROMOTION_APPROVAL_ENVELOPE_MISMATCH:pr_node_id")
    for key in ("transaction_id", "nonce"):
        if not isinstance(envelope.get(key), str) or len(envelope[key]) < 12:
            errors.append(f"PROMOTION_APPROVAL_ENVELOPE_MISMATCH:{key}")
    issued_at = parse_utc(str(envelope.get("issued_at") or ""))
    expires_at = parse_utc(str(envelope.get("expires_at") or ""))
    if issued_at is None or expires_at is None or issued_at >= expires_at or now >= expires_at or issued_at > now:
        errors.append("PROMOTION_APPROVAL_ENVELOPE_EXPIRED")
    return errors


def protected_approval_values(evidence: dict[str, Any]) -> dict[str, str]:
    protected = evidence.get("protected_approval")
    if isinstance(protected, dict):
        envelope = protected.get("envelope")
        if isinstance(envelope, dict):
            return envelope_values(envelope)
        return {
            "grant_id": str(protected.get("grant_id") or ""),
            "reference": str(protected.get("reference") or ""),
            "expiry": str(protected.get("expiry") or ""),
        }
    return envelope_values(None)


def protected_approval_envelope(evidence: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
    protected = evidence.get("protected_approval")
    if isinstance(protected, dict) and isinstance(protected.get("envelope"), dict):
        envelope = protected["envelope"]
        unknown = set(envelope) - PROMOTION_ENVELOPE_FIELDS
        missing = PROMOTION_ENVELOPE_FIELDS - set(envelope)
        errors: list[str] = []
        if unknown:
            errors.append("PROMOTION_APPROVAL_ENVELOPE_UNKNOWN_FIELDS")
        if missing:
            errors.append("PROMOTION_APPROVAL_ENVELOPE_MISSING_FIELDS")
        if envelope.get("schema") != PROMOTION_ENVELOPE_SCHEMA:
            errors.append("PROMOTION_APPROVAL_ENVELOPE_SCHEMA_INVALID")
        return envelope, errors
    return None, ["PROMOTION_APPROVAL_ENVELOPE_REQUIRED"]


def last_attestation_mutation_at(pr: dict[str, Any], timeline: list[dict[str, Any]]) -> datetime | None:
    created = parse_utc(pr.get("created_at"))
    latest = created
    for item in timeline:
        if not isinstance(item, dict):
            continue
        event = item.get("event")
        if event not in {"edited", "renamed"}:
            continue
        changes = item.get("changes") or {}
        if event == "edited" and "body" not in changes:
            continue
        when = parse_utc(item.get("created_at"))
        if when and (latest is None or when > latest):
            latest = when
    return latest


def is_unknown_promotion_branch(branch: str) -> bool:
    return branch.startswith(SUPERSEDED_PROMOTION_PREFIX) and branch not in set(PROMOTION_CANDIDATE_BRANCHES.values())


def is_promotion_shaped(branch: str, target_branch: str, fields: dict[str, str]) -> bool:
    return branch.startswith(SUPERSEDED_PROMOTION_PREFIX) or target_branch in {"certificacion", "main"} or any(not is_inert_attestation_value(fields.get(field, "")) for field in PROMOTION_SHAPED_FIELDS)


def classify_post_merge_promotion_push(event_path: str, *, root: Path = ROOT) -> tuple[str, list[str]]:
    errors = validate_post_merge_promotion_push(event_path, root=root)
    if not errors:
        if os.environ.get("POST_MERGE_SKIP_PROTECTED_APPROVAL") == "1":
            return "STRUCTURAL_PROMOTION_CANDIDATE", []
        return "VERIFIED_PROMOTION", []
    if errors and errors[0] == "POST_MERGE_NORMAL_PR_NOT_PROMOTION":
        return "NOT_APPLICABLE", errors
    return "BLOCKED", errors


def validate_post_merge_promotion_push(event_path: str, *, root: Path = ROOT) -> list[str]:
    try:
        event = json.loads(Path(event_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ["POST_MERGE_EVENT_INVALID"]
    if not isinstance(event, dict):
        return ["POST_MERGE_EVENT_INVALID"]
    before = str(event.get("before") or "")
    after = str(event.get("after") or "")
    ref = str(event.get("ref") or "")
    if before == "0" * 40 or not HEX40.match(before) or not HEX40.match(after) or not ref.startswith("refs/heads/"):
        return ["POST_MERGE_EVENT_INVALID"]
    branch = ref.removeprefix("refs/heads/")
    if branch not in PROTECTED_BRANCHES:
        return ["POST_MERGE_TARGET_BRANCH_INVALID"]
    try:
        parents = git_sha(["show", "-s", "--format=%P", after], root=root).split()
    except subprocess.CalledProcessError:
        return ["POST_MERGE_COMMIT_INVALID"]
    if len(parents) == 2 and parents[0] != before:
        return ["POST_MERGE_FIRST_PARENT_MISMATCH"]
    try:
        evidence = load_post_merge_evidence(after)
    except (GitHubEvidenceError, RuntimeError, OSError, urllib.error.URLError, json.JSONDecodeError):
        return ["POST_MERGE_EVIDENCE_UNAVAILABLE"]
    pr = evidence.get("pull_request") or {}
    if evidence.get("ambiguous_pull_requests"):
        return ["POST_MERGE_PR_AMBIGUOUS"]
    if not isinstance(pr, dict) or not pr or pr.get("merged") is not True or pr.get("merge_commit_sha") != after:
        return ["POST_MERGE_PR_MISMATCH"]
    try:
        pr_number = int(pr.get("number") or 0)
    except (TypeError, ValueError):
        return ["POST_MERGE_PR_METADATA_INVALID"]
    if pr_number <= 0:
        return ["POST_MERGE_PR_METADATA_INVALID"]
    base = pr.get("base") or {}
    head = pr.get("head") or {}
    if not isinstance(base, dict) or not isinstance(head, dict):
        return ["POST_MERGE_PR_SCHEMA_INVALID"]
    base_repo = base.get("repo") or {}
    head_repo = head.get("repo") or {}
    repo = pr.get("base", {}).get("repo", {}).get("full_name") or os.environ.get("GITHUB_REPOSITORY", "")
    if base_repo.get("full_name") != repo or head_repo.get("full_name") != repo:
        return ["POST_MERGE_REPOSITORY_INVALID"]
    base_ref = str(base.get("ref") or "")
    head_ref = str(head.get("ref") or "")
    head_sha = str(head.get("sha") or "")
    if base_ref != branch:
        return ["POST_MERGE_PR_BASE_REF_MISMATCH"]
    pr_created_at = parse_utc(pr.get("created_at"))
    pr_merged_at = parse_utc(pr.get("merged_at"))
    if pr_created_at is None or pr_merged_at is None:
        return ["POST_MERGE_PR_TIMESTAMP_INVALID"]
    merged_user = pr.get("merged_by") or {}
    merged_by = merged_user.get("login")
    if merged_by != "romelhc95" or merged_user.get("id") != 18040405:
        return ["POST_MERGE_MERGER_INVALID"]
    body = str(pr.get("body") or "")
    fields = parse_attestation_fields(body)
    operation = fields.get("Operation", "")
    expected_pair = PROMOTION_PAIRS.get(operation)
    expected_candidate_branch = PROMOTION_CANDIDATE_BRANCHES.get(operation)
    source_ref = fields.get("Source-Ref", "")
    source_sha = fields.get("Source-SHA", "")
    if is_unknown_promotion_branch(head_ref):
        return ["POST_MERGE_PROMOTION_BRANCH_SUPERSEDED"]
    route_is_promotion = expected_pair is not None and (base_ref, source_ref) == expected_pair and head_ref == expected_candidate_branch and base_ref == branch
    if not route_is_promotion:
        if branch == "desarrollo":
            if is_promotion_shaped(head_ref, branch, fields):
                return ["POST_MERGE_PAIR_INVALID"]
            return ["POST_MERGE_NORMAL_PR_NOT_PROMOTION"]
        if not head_ref.startswith(SUPERSEDED_PROMOTION_PREFIX) and not any(field in fields for field in PROMOTION_SHAPED_FIELDS):
            return ["POST_MERGE_PROTECTED_BRANCH_NON_PROMOTION"]
        if is_promotion_shaped(head_ref, branch, fields):
            return ["POST_MERGE_PAIR_INVALID"]
        return ["POST_MERGE_PROTECTED_BRANCH_NON_PROMOTION"]
    section_errors = promotion_section_errors(body, "POST_MERGE")
    if section_errors:
        return section_errors
    if governance_section_populated(body):
        return ["POST_MERGE_GOVERNANCE_SECTION_POPULATED"]
    if "__DUPLICATE__" in fields or "__DUPLICATE_SECTION__" in fields:
        return ["POST_MERGE_ATTESTATION_DUPLICATE"]
    if len(parents) != 2:
        return ["POST_MERGE_NOT_MERGE_COMMIT"]
    if parents[0] != before:
        return ["POST_MERGE_FIRST_PARENT_MISMATCH"]
    if not expected_pair or (base_ref, source_ref) != expected_pair or head_ref != expected_candidate_branch or base_ref != branch:
        return ["POST_MERGE_PAIR_INVALID"]
    if str(base.get("sha") or "") != before:
        return ["POST_MERGE_PR_BASE_SHA_MISMATCH"]
    if parents[1] != head_sha:
        return ["POST_MERGE_SECOND_PARENT_MISMATCH"]
    try:
        after_tree = git_sha(["rev-parse", f"{after}^{{tree}}"], root=root)
        candidate_tree = git_sha(["rev-parse", f"{head_sha}^{{tree}}"], root=root)
        source_tree = git_sha(["rev-parse", f"{source_sha}^{{tree}}"], root=root) if HEX40.match(source_sha) else ""
        if after_tree != candidate_tree or candidate_tree != source_tree:
            return ["POST_MERGE_TREE_MISMATCH"]
    except subprocess.CalledProcessError:
        return ["POST_MERGE_TREE_MISMATCH"]
    if fields.get("Operation") != operation or fields.get("Base-Ref") != base_ref or fields.get("Base-SHA") != before or fields.get("Candidate-SHA") != head_sha or fields.get("Candidate-Tree") != candidate_tree or fields.get("Final-WP") != PROMOTION_FINAL_WP:
        return ["POST_MERGE_ATTESTATION_MISMATCH"]
    try:
        candidate_parents = git_sha(["show", "-s", "--format=%P", head_sha], root=root).split()
    except subprocess.CalledProcessError:
        return ["POST_MERGE_CANDIDATE_PARENTS_INVALID"]
    if candidate_parents != [before, source_sha]:
        return ["POST_MERGE_CANDIDATE_PARENTS_INVALID"]
    grant_id = fields.get("Grant-ID", "")
    if not PROMOTION_GRANT_ID_PATTERN.match(grant_id):
        return ["POST_MERGE_GRANT_ID_INVALID"]
    skip_protected_approval = os.environ.get("POST_MERGE_SKIP_PROTECTED_APPROVAL") == "1"
    if pr_number in PROMOTION_BLOCKED_PR_NUMBERS or grant_id in PROMOTION_CONSUMED_GRANTS:
        return ["POST_MERGE_GRANT_CONSUMED"]
    if grant_id in PROMOTION_SUPERSEDED_GRANTS:
        return ["POST_MERGE_GRANT_SUPERSEDED"]
    if fields.get("Approval-Level") != "R3 JIT single-use":
        return ["POST_MERGE_APPROVAL_LEVEL_INVALID"]
    approval_ref = fields.get("Approval-Reference", "")
    if not approval_ref or approval_ref in {"TODO", "N/A", "none", "<approval-reference>"}:
        return ["POST_MERGE_APPROVAL_REFERENCE_REQUIRED"]
    expiry = parse_utc(fields.get("Approval-Expiry", ""))
    if expiry is None or datetime.now(UTC) >= expiry:
        return ["POST_MERGE_APPROVAL_EXPIRED"]
    final_wp = load_manifest_by_id(fields.get("Final-WP", ""), root=root)
    d_final = fields.get("D_FINAL", "")
    if final_wp is None or final_wp.get("candidate_digest") != d_final or compute_digest(final_wp) != d_final:
        return ["POST_MERGE_DIGEST_MISMATCH"]
    grant = load_promotion_grant(grant_id, root=root)
    if grant is None:
        return ["POST_MERGE_GRANT_NOT_FOUND"]
    grant_errors = validate_static_promotion_request(
        grant,
        grant_id=grant_id,
        operation=operation,
            repo_name=repo,
            base_ref=base_ref,
            head_ref=head_ref,
            source_ref=source_ref,
            candidate_branch=head_ref,
            final_wp_id=PROMOTION_FINAL_WP,
            d_final=d_final,
            require_identity=True,
        )
    if grant_errors:
        return ["POST_MERGE_GRANT_MISMATCH"]
    try:
        if git_sha(["rev-parse", f"{source_sha}^{{tree}}"], root=root) != fields.get("T_FINAL", ""):
            return ["POST_MERGE_T_FINAL_MISMATCH"]
    except subprocess.CalledProcessError:
        return ["POST_MERGE_T_FINAL_MISMATCH"]
    checks = evidence.get("checks") or []
    if not isinstance(checks, list):
        return ["POST_MERGE_CHECK_SCHEMA_INVALID"]
    timeline = evidence.get("timeline") or []
    if not isinstance(timeline, list) or any(not isinstance(item, dict) for item in timeline):
        return ["POST_MERGE_TIMELINE_SCHEMA_INVALID"]
    allow_empty_pull_requests = True
    promotion_check, check_error = latest_check_run(checks, "Promotion Boundary", head_sha=head_sha, pr_number=pr_number, pr_created_at=pr_created_at, pr_merged_at=pr_merged_at, allow_empty_pull_requests=allow_empty_pull_requests)
    if check_error:
        return [check_error]
    audit_check, check_error = latest_check_run(checks, "security-audit", head_sha=head_sha, pr_number=pr_number, pr_created_at=pr_created_at, pr_merged_at=pr_merged_at, allow_empty_pull_requests=allow_empty_pull_requests)
    if check_error:
        return [check_error]
    if operation.startswith("O3"):
        if evidence.get("db_changed") is not False:
            try:
                if subprocess.check_output(["git", "diff", "--name-only", before, after, "--", "db"], cwd=root, text=True, stderr=subprocess.DEVNULL).strip():
                    return ["POST_MERGE_O3_DB_DELTA_INVALID"]
            except subprocess.CalledProcessError:
                return ["POST_MERGE_O3_DB_DELTA_INVALID"]
    if operation.startswith("O4"):
        try:
            o3 = load_o3_closure_artifact(source_sha)
        except (GitHubEvidenceError, GitHubSchemaError, OSError, urllib.error.URLError, json.JSONDecodeError, zipfile.BadZipFile):
            return ["POST_MERGE_O4_BLOCKED_PENDING_O3"]
        if o3.get("status") != "CLOSED" or o3.get("cloudflare_pages_app_id") != CLOUDFLARE_PAGES_APP_ID or o3.get("db_sync_result") != DB_SYNC_DETECT_ONLY_RESULT or o3.get("main_merge_sha") != source_sha or o3.get("db_changed") is not False or o3.get("apply_executed") is not False:
            return ["POST_MERGE_O4_BLOCKED_PENDING_O3"]
    if operation.startswith("O5"):
        try:
            main_tree = git_sha(["rev-parse", "origin/main^{tree}"], root=root)
            certificacion_tree = git_sha(["rev-parse", "origin/certificacion^{tree}"], root=root)
            desarrollo_tree = git_sha(["rev-parse", f"{after}^{{tree}}"], root=root)
        except subprocess.CalledProcessError:
            return ["POST_MERGE_O5_FINAL_REFS_UNAVAILABLE"]
        if len({main_tree, certificacion_tree, desarrollo_tree, fields.get("T_FINAL", "")}) != 1:
            return ["POST_MERGE_O5_FINAL_TREE_MISMATCH"]
        if git_is_ancestor("origin/main", "origin/certificacion", root=root) is not True or git_is_ancestor("origin/certificacion", after, root=root) is not True:
            return ["POST_MERGE_O5_FINAL_ANCESTRY_INVALID"]
    promotion_run_id = workflow_run_id_from_details(promotion_check.get("details_url")) if promotion_check else None
    audit_run_id = workflow_run_id_from_details(audit_check.get("details_url")) if audit_check else None
    if promotion_run_id is None or audit_run_id is None or promotion_run_id != audit_run_id:
        return ["POST_MERGE_WORKFLOW_RUN_MISMATCH"]
    if not skip_protected_approval:
        if not isinstance(evidence.get("protected_approval"), dict):
            try:
                evidence["protected_approval"] = load_promotion_approval_artifact(promotion_run_id, pr_number)
            except (GitHubEvidenceError, GitHubSchemaError, OSError, urllib.error.URLError, json.JSONDecodeError, zipfile.BadZipFile):
                return ["POST_MERGE_APPROVAL_ARTIFACT_INVALID"]
        protected = protected_approval_values(evidence)
        protected_envelope, protected_envelope_errors = protected_approval_envelope(evidence)
        if not protected["grant_id"] or not protected["reference"] or not protected["expiry"]:
            return ["POST_MERGE_APPROVAL_ENV_REQUIRED"]
        if protected_envelope_errors or protected_envelope is None:
            return ["POST_MERGE_APPROVAL_ENVELOPE_INVALID"]
        if protected["grant_id"] != grant_id:
            return ["POST_MERGE_APPROVAL_GRANT_ID_MISMATCH"]
        if protected["reference"] != approval_ref:
            return ["POST_MERGE_APPROVAL_REFERENCE_MISMATCH"]
        if protected["expiry"] != fields.get("Approval-Expiry", "") or parse_utc(protected["expiry"]) != expiry:
            return ["POST_MERGE_APPROVAL_EXPIRY_MISMATCH"]
        if protected_envelope.get("premerge_run_id") != promotion_run_id:
            return ["POST_MERGE_APPROVAL_ENVELOPE_MISMATCH"]
        pseudo_event = {"repository": {"full_name": repo}, "number": pr_number}
        envelope_errors = validate_envelope_bindings(protected_envelope, event=pseudo_event, fields=fields, pr=pr, expected_digest=d_final, expected_tree=fields.get("T_FINAL", ""), require_premerge_run=False)
        if envelope_errors:
            return ["POST_MERGE_APPROVAL_ENVELOPE_MISMATCH"]
    runs = evidence.get("workflow_runs") or {}
    run = runs.get(str(promotion_run_id)) if isinstance(runs, dict) else None
    if run is None:
        try:
            run = github_api_json(f"actions/runs/{promotion_run_id}")
        except GitHubEvidenceError:
            return ["POST_MERGE_WORKFLOW_RUN_UNAVAILABLE"]
    run_error = require_workflow_run(run, run_id=promotion_run_id, head_sha=head_sha, head_branch=head_ref, pr_created_at=pr_created_at, pr_merged_at=pr_merged_at)
    if run_error:
        return [run_error]
    latest_attestation = last_attestation_mutation_at(pr, timeline)
    run_created_at = parse_utc(run.get("created_at"))
    if latest_attestation is None or run_created_at is None or run_created_at < latest_attestation:
        return ["POST_MERGE_ATTESTATION_STALE"]
    reviews = evidence.get("reviews") or []
    review_schema_error = validate_reviews_schema(reviews)
    if review_schema_error:
        return [review_schema_error]
    latest_review = latest_effective_review_state(reviews, "romelhc95-approver")
    if latest_review is None:
        return ["POST_MERGE_REVIEW_MISSING"]
    review_user = latest_review.get("user") or {}
    if review_user.get("login") != "romelhc95-approver" or review_user.get("id") != 306979205:
        return ["POST_MERGE_REVIEWER_INVALID"]
    review_submitted_at = parse_utc(latest_review.get("submitted_at"))
    if review_submitted_at is None or review_submitted_at < pr_created_at or review_submitted_at > pr_merged_at:
        return ["POST_MERGE_REVIEW_TIME_WINDOW_INVALID"]
    if latest_attestation is None or review_submitted_at < latest_attestation:
        return ["POST_MERGE_REVIEW_STALE"]
    if latest_review.get("commit_id") != head_sha:
        return ["POST_MERGE_REVIEW_COMMIT_INVALID"]
    if latest_review.get("state") != "APPROVED":
        return ["POST_MERGE_REVIEW_STATE_INVALID"]
    if merged_by == "romelhc95-approver":
        return ["POST_MERGE_REVIEWER_MERGER_MATCH"]
    return []


def resolve_git_ref(ref: str, root: Path = ROOT) -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", ref], cwd=root, text=True, stderr=subprocess.DEVNULL).strip()
    except subprocess.CalledProcessError:
        for known_ref in (H2_ACTIVATION_BASE_COMMIT, H2_OBSIDIAN_BASE_COMMIT, GOV_OBS_BASE_COMMIT, PR424_BASE_COMMIT, GOV_ARCH_BASE_COMMIT, GOV_HOM_BASE_COMMIT, GOV_CI_BASE_COMMIT, GOV_CI2_BASE_COMMIT, GOV_CI3_BASE_COMMIT, GOV_CI4_BASE_COMMIT, GOV_CI5_BASE_COMMIT, GOV_CI6_BASE_COMMIT, GOV_CI7_BASE_COMMIT, GOV_CI8_BASE_COMMIT, GOV_CI9_BASE_COMMIT, GOV_CI10_BASE_COMMIT, GOV_CI11_BASE_COMMIT, GOV_CI12_BASE_COMMIT):
            if known_ref.startswith(ref):
                return known_ref
        return ref


def validate_changed_paths(changed: list[tuple[str, str]], manifests: list[dict[str, Any]], *, active_work_package: str = "NONE", activation_transition: bool = False, obsidian_transition: bool = False, gov_obs_transition: bool = False, gov_arch_transition: bool = False, gov_hom_transition: bool = False, gov_ci_transition: bool = False, gov_ci2_transition: bool = False, gov_ci3_transition: bool = False, gov_ci4_transition: bool = False, gov_ci5_transition: bool = False, gov_ci6_transition: bool = False, gov_ci7_transition: bool = False, gov_ci8_transition: bool = False, gov_ci9_transition: bool = False, gov_ci10_transition: bool = False, gov_ci11_transition: bool = False, gov_ci12_transition: bool = False) -> list[str]:
    errors: list[str] = []
    active = [manifest for manifest in manifests if is_active_r1_manifest(manifest, active_work_package=active_work_package)]
    if len(active) > 1:
        errors.append("MULTIPLE_ACTIVE_WORK_PACKAGES")
    if gov_ci12_transition:
        allowed = GOV_CI12_TRANSITION_ALLOWLIST
        denied = GOV_RELEASE_TRANSITION_DENY
    elif gov_ci11_transition:
        allowed = GOV_CI11_TRANSITION_ALLOWLIST
        denied = GOV_RELEASE_TRANSITION_DENY
    elif gov_ci10_transition:
        allowed = GOV_CI10_TRANSITION_ALLOWLIST
        denied = GOV_RELEASE_TRANSITION_DENY
    elif gov_ci9_transition:
        allowed = GOV_CI9_TRANSITION_ALLOWLIST
        denied = GOV_RELEASE_TRANSITION_DENY
    elif gov_ci8_transition:
        allowed = GOV_CI8_TRANSITION_ALLOWLIST
        denied = GOV_RELEASE_TRANSITION_DENY
    elif gov_ci7_transition:
        allowed = GOV_CI7_TRANSITION_ALLOWLIST
        denied = GOV_RELEASE_TRANSITION_DENY
    elif gov_ci6_transition:
        allowed = GOV_CI6_TRANSITION_ALLOWLIST
        denied = GOV_RELEASE_TRANSITION_DENY
    elif gov_ci5_transition:
        allowed = GOV_CI5_TRANSITION_ALLOWLIST
        denied = GOV_RELEASE_TRANSITION_DENY
    elif gov_ci4_transition:
        allowed = GOV_CI4_TRANSITION_ALLOWLIST
        denied = GOV_RELEASE_TRANSITION_DENY
    elif gov_ci3_transition:
        allowed = GOV_CI3_TRANSITION_ALLOWLIST
        denied = GOV_RELEASE_TRANSITION_DENY
    elif gov_ci2_transition:
        allowed = GOV_CI2_TRANSITION_ALLOWLIST
        denied = GOV_RELEASE_TRANSITION_DENY
    elif gov_ci_transition:
        allowed = GOV_CI_TRANSITION_ALLOWLIST
        denied = GOV_RELEASE_TRANSITION_DENY
    elif gov_obs_transition:
        allowed = GOV_RELEASE_TRANSITION_ALLOWLIST
        denied = GOV_RELEASE_TRANSITION_DENY
    elif gov_hom_transition:
        allowed = GOV_HOM_TRANSITION_ALLOWLIST
        denied = GOV_RELEASE_TRANSITION_DENY
    elif gov_arch_transition:
        allowed = GOV_ARCH_TRANSITION_ALLOWLIST
        denied = GOV_RELEASE_TRANSITION_DENY
    elif obsidian_transition:
        allowed = H2_OBSIDIAN_TRANSITION_ALLOWLIST
        denied = H2_OBSIDIAN_TRANSITION_DENY
    elif active_work_package == "WP-GOV-OBS-001":
        allowed = GOV_OBS_TRANSITION_ALLOWLIST
        denied = GOV_OBS_TRANSITION_DENY
    elif activation_transition:
        allowed = H2_ACTIVATION_TRANSITION_ALLOWLIST
        denied = H2_ACTIVATION_TRANSITION_DENY
    elif active:
        allowed = tuple(str(item) for item in active[0].get("allowed_paths", []))
        denied = ABSOLUTE_DENY
    else:
        allowed = GOVERNANCE_ALLOWLIST
        denied = GOVERNANCE_DENY
    for status, path in changed:
        name = path.rsplit("/", 1)[-1]
        lower = path.lower()
        if name in SOURCE_NAMES or lower.endswith(SOURCE_EXTENSIONS):
            errors.append(f"SOURCE_ARTIFACT:{status}:{path}")
        if pattern_matches(denied, path):
            errors.append(f"DENIED_PATH:{status}:{path}")
        if not pattern_matches(allowed, path):
            errors.append(f"CHANGED_PATH_NOT_ALLOWED:{status}:{path}")
    return errors


def load_manifests(root: Path = ROOT) -> list[dict[str, Any]]:
    manifests = []
    for manifest_path in sorted((root / ".context" / "work_packages").glob("WP-*.json")):
        manifests.append(json.loads(manifest_path.read_text(encoding="utf-8")))
    return manifests


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--changed-from", help="Validate changed paths from this git ref to HEAD")
    parser.add_argument("--promotion-event", help="Validate a protected branch promotion event")
    parser.add_argument("--post-merge-push-event", help="Classify push as VERIFIED_PROMOTION(0), STRUCTURAL_PROMOTION_CANDIDATE(0), BLOCKED(1), or NOT_APPLICABLE(2)")
    parser.add_argument("--event-name", default="")
    parser.add_argument("--run-attempt", default="", help="GitHub Actions run attempt for promotion replay protection")
    args = parser.parse_args(argv)
    manifests = sorted(MANIFEST_DIR.glob("WP-*.json"))
    errors: list[str] = []
    if len(manifests) != 20:
        errors.append("WP_MANIFEST_COUNT:expected four Sprint 1 manifests plus GOV OBS/INFRA/ARCH/HOM/CI/CI2/CI3/CI4/CI5/CI6/CI7/CI8/CI9/CI10/CI11/CI12 manifests")
    for manifest in manifests:
        errors.extend(validate_manifest(manifest, root=ROOT))
    errors.extend(validate_static_promotion_requests(root=ROOT))
    if args.post_merge_push_event:
        if errors:
            print("BLOCKED")
            for error in errors:
                print(error)
            return 1
        state, post_merge_errors = classify_post_merge_promotion_push(args.post_merge_push_event, root=ROOT)
        print(state)
        if state == "VERIFIED_PROMOTION":
            print("POST_MERGE_PROMOTION_STRUCTURAL_PASS")
            return 0
        if state == "STRUCTURAL_PROMOTION_CANDIDATE":
            print("POST_MERGE_PROMOTION_STRUCTURAL_PASS_APPROVAL_PENDING")
            return 0
        for error in post_merge_errors:
            print(error)
        return 2 if state == "NOT_APPLICABLE" else 1
    if args.promotion_event:
        errors.extend(validate_promotion_event(args.promotion_event, event_name=args.event_name, run_attempt=args.run_attempt, root=ROOT))
    elif args.changed_from:
        changed_from = resolve_git_ref(args.changed_from)
        errors.extend(validate_changed_paths(
            git_changed_paths(args.changed_from),
            load_manifests(),
            active_work_package=active_work_package_from_state(),
            activation_transition=changed_from == H2_ACTIVATION_BASE_COMMIT,
            obsidian_transition=changed_from == H2_OBSIDIAN_BASE_COMMIT,
            gov_obs_transition=changed_from in {GOV_OBS_BASE_COMMIT, PR424_BASE_COMMIT},
            gov_arch_transition=changed_from == GOV_ARCH_BASE_COMMIT,
            gov_hom_transition=changed_from == GOV_HOM_BASE_COMMIT,
            gov_ci_transition=changed_from == GOV_CI_BASE_COMMIT,
            gov_ci2_transition=changed_from == GOV_CI2_BASE_COMMIT,
            gov_ci3_transition=changed_from == GOV_CI3_BASE_COMMIT,
            gov_ci4_transition=changed_from == GOV_CI4_BASE_COMMIT,
            gov_ci5_transition=changed_from == GOV_CI5_BASE_COMMIT,
            gov_ci6_transition=changed_from == GOV_CI6_BASE_COMMIT,
            gov_ci7_transition=changed_from == GOV_CI7_BASE_COMMIT,
            gov_ci8_transition=changed_from == GOV_CI8_BASE_COMMIT,
            gov_ci9_transition=changed_from == GOV_CI9_BASE_COMMIT,
            gov_ci10_transition=changed_from == GOV_CI10_BASE_COMMIT,
            gov_ci11_transition=changed_from == GOV_CI11_BASE_COMMIT,
            gov_ci12_transition=changed_from == GOV_CI12_BASE_COMMIT,
        ))
    if errors:
        for error in errors:
            print(error)
        return 1
    print("work package manifests valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
