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
F1010_M2A_BASE = "560af8ad9ce6350fd6c219c853665e1f9c6089f3"
F1010_M2A_BASE_TREE = "bb2fce144bacac4045b028dd0246815bae209023"
F1010_M2A_HEAD_REF = "ci/f10-10-m2-boundary"
F1010_M1_HEAD_REF = "feat/f10-10-m1-offline-tooling"
F1010_M3_BASE = "ea6ef79a450d691a93195b26bec2ecde1b4dc18d"
F1010_M3_BASE_TREE = "fe5b8223e56f360bef930bd565cfa6318e37692c"
F1010_M3_HEAD_REF = "feat/f10-10-m3-readonly-collector-v2"
F1010_M3_READER_BASE = "1adfc2a8bcabfd4b58ff2bc34f73e47626f1a838"
F1010_M3_READER_BASE_TREE = "4b2e3245d2a87c7170b4241b87e1a8ae123c1bec"
F1010_M3_READER_HEAD_REF = "feat/f10-10-m3-reader-rebaseline-v2"
F1010_M3_READER_POST_MERGE_BASE = "2cf614a4a44ffabc5e06ba08dc20707807db274f"
F1010_M3_READER_POST_MERGE_BASE_TREE = "7b9e9cfd9d74749416cfab098da116ecbe239c04"
F1010_M3_READER_POST_MERGE_HEAD_REF = "docs/f10-10-m3-reader-post-merge"
F1010_M3_READER_POST_MERGE_DOCS_COMMIT = "07953e6e0759bd73cdb4ca7df1f3163fda5b53a0"
F1010_M3_ROTATION_BASE = "1749d85b52ee2634e4089d578c09b18e7731f655"
F1010_M3_ROTATION_BASE_TREE = "cdf5b43dde3d4c27503e103e679825e4fb2cb15e"
F1010_M3_ROTATION_HEAD_REF = "docs/f10-10-m3-rotation-attestation"
F1010_M3_PASSWORDLESS_BASE = "e9d881e80f9d359d4b190ed136c09f6be217f004"
F1010_M3_PASSWORDLESS_BASE_TREE = "21418de4b60f3f151eba803e2f163bba1573a040"
F1010_M3_PASSWORDLESS_HEAD_REF = "fix/f10-10-m3-passwordless-binding"
F1010_M3_PREFLIGHT_PAYLOAD_BASE = "ea3adaf6fd9847fc5cf98f4d0ed6449a41fae1a1"
F1010_M3_PREFLIGHT_PAYLOAD_BASE_TREE = "1929c3cc6dd3ab0f5b822a530ee2d08285ff9345"
F1010_M3_PREFLIGHT_PAYLOAD_HEAD_REF = "docs/f10-10-m3-preflight-payload"
F1010_M3_PREFLIGHT_EVIDENCE_BASE = "47100311a10731ea6297af5c8c1e2e64f5d100b2"
F1010_M3_PREFLIGHT_EVIDENCE_BASE_TREE = "7ebe1b429ae986fbab907814d14eddb680a72dab"
F1010_M3_PREFLIGHT_EVIDENCE_HEAD_REF = "docs/f10-10-m3-preflight-evidence"
F1010_M3_FINAL_READINESS_BASE = "68cc282f27945891b52fc3b574a14606bcb62e2c"
F1010_M3_FINAL_READINESS_BASE_TREE = "c580d12ac9c9b6f01a5f026dc59376402504419a"
F1010_M3_FINAL_READINESS_HEAD_REF = "fix/f10-10-m3-postgres-final-readiness"
F1010_M3_APPLY_PROJECTION_BASE = "b6fe593ec649d3421aa153e4049f48af3ad0c12d"
F1010_M3_APPLY_PROJECTION_BASE_TREE = "662f07b2c1fa2d592545de18bd9dfccb2219a82c"
F1010_M3_APPLY_PROJECTION_HEAD_REF = "feat/f10-10-m3-apply-projection"
F1010_M3_DDL_PAYLOAD_BASE = "ac9bda0374930339268f9e59af15ea7416fb320f"
F1010_M3_DDL_PAYLOAD_BASE_TREE = "43337b48bfe460f6305ca703a8e194b1ebd55942"
F1010_M3_DDL_PAYLOAD_HEAD_REF = "docs/f10-10-m3-ddl-free-payload"
F1010_M3_DDL_PAYLOAD_REFRESH_BASE = "49d9c0cbdc526854cb1414965ded8c2ca35ab2ad"
F1010_M3_DDL_PAYLOAD_REFRESH_BASE_TREE = "ffd726e3881893437bb482773c44e6dfa1b60a05"
F1010_M3_DDL_PAYLOAD_REFRESH_HEAD_REF = "docs/f10-10-m3-ddl-free-payload-refresh"
F1010_M3_NULLABILITY_REMEDIATION_BASE = "16265817e89e1ac00bbce498f3532e05bd0c9a55"
F1010_M3_NULLABILITY_REMEDIATION_BASE_TREE = "8d89cbc6642e44a5bb380c754df09900266ed416"
F1010_M3_NULLABILITY_REMEDIATION_HEAD_REF = "fix/f10-10-m3-is-active-nullability"
F1010_M3_DDL_V2_PAYLOAD_BASE = "bc268f119e04791bc17439aaa096e9e06c8b5e8b"
F1010_M3_DDL_V2_PAYLOAD_BASE_TREE = "fd08e8cee5cc7cc6d031fd59fbb5ed97e9f9ad68"
F1010_M3_DDL_V2_PAYLOAD_HEAD_REF = "docs/f10-10-m3-ddl-free-v2-payload"
F1010_M3_PUBLIC_ACL_REBASELINE_BASE = "d6f2570816b6a69bf5e5aad5e37a6dd004e0e0d2"
F1010_M3_PUBLIC_ACL_REBASELINE_BASE_TREE = "a54b57e361be3fbed86ccee820128a1d71303498"
F1010_M3_PUBLIC_ACL_REBASELINE_HEAD_REF = "fix/f10-10-m3-public-db-acl-rebaseline"
F1010_M3_PUBLIC_ACL_V2_PAYLOAD_BASE = "d7d1325e74561b0bf8f369475691ee1ea70b2a82"
F1010_M3_PUBLIC_ACL_V2_PAYLOAD_BASE_TREE = "a71ad6f4ee64b2b2e7eef82dd8f0835740434b44"
F1010_M3_PUBLIC_ACL_V2_PAYLOAD_HEAD_REF = "docs/f10-10-m3-public-db-acl-diagnostic-v2-payload"
F1010_M3_PUBLIC_ACL_V3_BASE = "8e6d569dcc2d91479e48172bf18f3024571b95ac"
F1010_M3_PUBLIC_ACL_V3_BASE_TREE = "09e15518f24f6b120c09962296f3d13763dd7bd7"
F1010_M3_PUBLIC_ACL_V3_HEAD_REF = "fix/f10-10-m3-public-db-acl-diagnostic-v3"
F1010_M3_PUBLIC_ACL_V3_BOUND_BASE = "daf3e5babb2f6185304973e4f7607d95d85ab130"
F1010_M3_PUBLIC_ACL_V3_BOUND_BASE_TREE = "da047276b78cea8c1a2b8bf7048a6f40c0146f2b"
F1010_M3_PUBLIC_ACL_V3_BOUND_HEAD_REF = "docs/f10-10-m3-public-db-acl-diagnostic-v3-execution-binding"
F1010_M3_PUBLIC_ACL_PREFLIGHT_BASE = "7034d93059da92b34fb77b06b870ad254f192623"
F1010_M3_PUBLIC_ACL_PREFLIGHT_BASE_TREE = "a86b31d562d3ae094afe1b46da297827eee07020"
F1010_M3_PUBLIC_ACL_PREFLIGHT_HEAD_REF = "feat/f10-10-m3-public-db-acl-private-preflight"

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

F1010_M2A_ALLOWED_STATUSES = {
    ".github/workflows/f9-7-contract.yml": "M",
    ".github/workflows/security-audit.yml": "M",
    "scripts/security/f109_boundary.py": "M",
    "tests/test_fase10_9_branch_reconciliation.py": "M",
}

F1010_M2A_ALLOWED_MODES = {
    path: "100755" if path == ".github/workflows/security-audit.yml" else "100644"
    for path in F1010_M2A_ALLOWED_STATUSES
}

F1010_M1_ALLOWED_STATUSES = {
    "scripts/shared/f10_10_metadata_remediation.py": "A",
    "tests/test_fase10_10_m1_offline_tooling.py": "A",
}

F1010_M1_ALLOWED_MODES = {path: "100644" for path in F1010_M1_ALLOWED_STATUSES}

F1010_M3_PUBLIC_ACL_PREFLIGHT_ALLOWED_STATUSES = {
    ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
    ".context/estado_del_proyecto.md": "M",
    ".context/operaciones/flujo_release_minimo.md": "M",
    ".context/operaciones/m3_f10_10_scope_por_ambiente_target.md": "M",
    ".context/operaciones/m3_public_db_acl_diagnostic_free_v3_bound_result_2026_08_12.md": "A",
    ".context/operaciones/m3_reader_f10_10_rebaseline.md": "M",
    ".context/operaciones/plan_cierre_hito1_ca1_only.md": "M",
    ".context/operaciones/plan_remediacion_metadata_f10_10.md": "M",
    ".github/workflows/f9-7-contract.yml": "M",
    "scripts/maintenance/f10_10_m3_public_db_acl_preflight.py": "A",
    "scripts/security/f109_boundary.py": "M",
    "tests/sql/f10_10_m3_public_db_acl_preflight_assert.sql": "A",
    "tests/sql/f10_10_m3_public_db_acl_preflight_fixture.sql": "A",
    "tests/sql/run_f10_10_m3_public_db_acl_preflight_postgres17.sh": "A",
    "tests/test_f10_10_m3_public_db_acl_preflight.py": "A",
    "tests/test_fase10_9_branch_reconciliation.py": "M",
}

F1010_M3_PUBLIC_ACL_PREFLIGHT_ALLOWED_MODES = {
    path: "100644" for path in F1010_M3_PUBLIC_ACL_PREFLIGHT_ALLOWED_STATUSES
}

F1010_M3_ALLOWED_STATUSES = {
    ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
    ".context/estado_del_proyecto.md": "M",
    ".context/operaciones/flujo_release_minimo.md": "M",
    ".context/operaciones/m3_f10_10_scope_por_ambiente_target.md": "M",
    ".context/operaciones/plan_cierre_hito1_ca1_only.md": "M",
    ".context/operaciones/plan_remediacion_metadata_f10_10.md": "M",
    ".github/workflows/f9-7-contract.yml": "M",
    "scripts/maintenance/f10_10_m3_readonly_collector.py": "A",
    "scripts/security/f109_boundary.py": "M",
    "tests/test_f10_10_m3_readonly_collector.py": "A",
    "tests/test_fase10_9_branch_reconciliation.py": "M",
}

F1010_M3_ALLOWED_MODES = {path: "100644" for path in F1010_M3_ALLOWED_STATUSES}

F1010_M3_READER_ALLOWED_STATUSES = {
    ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
    ".context/estado_del_proyecto.md": "M",
    ".context/operaciones/flujo_release_minimo.md": "M",
    ".context/operaciones/m3_f10_10_scope_por_ambiente_target.md": "M",
    ".context/operaciones/m3_reader_f10_10_rebaseline.md": "A",
    ".context/operaciones/plan_cierre_hito1_ca1_only.md": "M",
    ".context/operaciones/plan_remediacion_metadata_f10_10.md": "M",
    ".github/workflows/f9-7-contract.yml": "M",
    ".github/workflows/db-sync-to-pro.yml": "M",
    "db/free_only_migrations/20260811_fase10_10_m3_free_reader.sql": "A",
    "db/rollbacks/20260811_fase10_10_m3_free_reader_compensating.sql": "A",
    "scripts/maintenance/f10_10_m3_readonly_collector.py": "M",
    "scripts/security/f109_boundary.py": "M",
    "tests/sql/20260811_fase10_10_m3_free_reader_test.sql": "A",
    "tests/sql/run_fase10_10_m3_free_reader_postgres17.sh": "A",
    "tests/test_f10_10_m3_reader_package.py": "A",
    "tests/test_f10_10_m3_readonly_collector.py": "M",
    "tests/test_fase10_8_db_sync.py": "M",
    "tests/test_fase10_9_branch_reconciliation.py": "M",
}

F1010_M3_READER_ALLOWED_MODES = {
    path: "100755" if path == "tests/sql/run_fase10_10_m3_free_reader_postgres17.sh" else "100644"
    for path in F1010_M3_READER_ALLOWED_STATUSES
}

F1010_M3_READER_POST_MERGE_ALLOWED_STATUSES = {
    ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
    ".context/estado_del_proyecto.md": "M",
    ".context/operaciones/flujo_release_minimo.md": "M",
    ".context/operaciones/m3_f10_10_scope_por_ambiente_target.md": "M",
    ".context/operaciones/m3_reader_f10_10_post_merge_evidence_2026_08_11.md": "A",
    ".context/operaciones/m3_reader_f10_10_rebaseline.md": "M",
    ".context/operaciones/plan_cierre_hito1_ca1_only.md": "M",
    ".context/operaciones/plan_remediacion_metadata_f10_10.md": "M",
    "scripts/security/f109_boundary.py": "M",
    "tests/test_fase10_9_branch_reconciliation.py": "M",
}

F1010_M3_READER_POST_MERGE_ALLOWED_MODES = {
    path: "100644" for path in F1010_M3_READER_POST_MERGE_ALLOWED_STATUSES
}

F1010_M3_ROTATION_ALLOWED_STATUSES = {
    ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
    ".context/estado_del_proyecto.md": "M",
    ".context/operaciones/flujo_release_minimo.md": "M",
    ".context/operaciones/m3_f10_10_scope_por_ambiente_target.md": "M",
    ".context/operaciones/m3_reader_f10_10_post_merge_evidence_2026_08_11.md": "M",
    ".context/operaciones/m3_reader_f10_10_rebaseline.md": "M",
    ".context/operaciones/m3_reader_f10_10_rotation_attestation_2026_08_11.md": "A",
    ".context/operaciones/plan_cierre_hito1_ca1_only.md": "M",
    ".context/operaciones/plan_remediacion_metadata_f10_10.md": "M",
    "scripts/security/f109_boundary.py": "M",
    "tests/test_fase10_9_branch_reconciliation.py": "M",
}

F1010_M3_ROTATION_ALLOWED_MODES = {
    path: "100644" for path in F1010_M3_ROTATION_ALLOWED_STATUSES
}

F1010_M3_PASSWORDLESS_ALLOWED_STATUSES = {
    ".context/operaciones/m3_f10_10_scope_por_ambiente_target.md": "M",
    ".context/operaciones/m3_reader_f10_10_rebaseline.md": "M",
    "scripts/maintenance/f10_10_m3_readonly_collector.py": "M",
    "scripts/security/f109_boundary.py": "M",
    "tests/test_f10_10_m3_readonly_collector.py": "M",
    "tests/test_fase10_9_branch_reconciliation.py": "M",
}

F1010_M3_PASSWORDLESS_ALLOWED_MODES = {
    path: "100644" for path in F1010_M3_PASSWORDLESS_ALLOWED_STATUSES
}

F1010_M3_PREFLIGHT_PAYLOAD_ALLOWED_STATUSES = {
    ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
    ".context/estado_del_proyecto.md": "M",
    ".context/operaciones/flujo_release_minimo.md": "M",
    ".context/operaciones/m3_f10_10_scope_por_ambiente_target.md": "M",
    ".context/operaciones/m3_reader_f10_10_preflight_payload_2026_08_11.json": "A",
    ".context/operaciones/m3_reader_f10_10_rebaseline.md": "M",
    ".context/operaciones/m3_reader_f10_10_rotation_attestation_2026_08_11.md": "M",
    ".context/operaciones/plan_cierre_hito1_ca1_only.md": "M",
    ".context/operaciones/plan_remediacion_metadata_f10_10.md": "M",
    "scripts/security/f109_boundary.py": "M",
    "tests/test_fase10_9_branch_reconciliation.py": "M",
}

F1010_M3_PREFLIGHT_PAYLOAD_ALLOWED_MODES = {
    path: "100644" for path in F1010_M3_PREFLIGHT_PAYLOAD_ALLOWED_STATUSES
}

F1010_M3_PREFLIGHT_EVIDENCE_ALLOWED_STATUSES = {
    ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
    ".context/estado_del_proyecto.md": "M",
    ".context/operaciones/flujo_release_minimo.md": "M",
    ".context/operaciones/m3_f10_10_scope_por_ambiente_target.md": "M",
    ".context/operaciones/m3_reader_f10_10_preflight_evidence_2026_08_11.md": "A",
    ".context/operaciones/m3_reader_f10_10_preflight_result_2026_08_11.json": "A",
    ".context/operaciones/m3_reader_f10_10_rebaseline.md": "M",
    ".context/operaciones/plan_cierre_hito1_ca1_only.md": "M",
    ".context/operaciones/plan_remediacion_metadata_f10_10.md": "M",
    "scripts/security/f109_boundary.py": "M",
    "tests/test_fase10_9_branch_reconciliation.py": "M",
}

F1010_M3_PREFLIGHT_EVIDENCE_ALLOWED_MODES = {
    path: "100644" for path in F1010_M3_PREFLIGHT_EVIDENCE_ALLOWED_STATUSES
}

F1010_M3_FINAL_READINESS_ALLOWED_STATUSES = {
    ".context/operaciones/m3_reader_f10_10_preflight_evidence_2026_08_11.md": "M",
    ".context/operaciones/plan_remediacion_metadata_f10_10.md": "M",
    ".github/workflows/f9-7-contract.yml": "M",
    "scripts/security/f109_boundary.py": "M",
    "tests/test_f10_10_m3_reader_package.py": "M",
    "tests/test_fase10_9_branch_reconciliation.py": "M",
}

F1010_M3_FINAL_READINESS_ALLOWED_MODES = {
    path: "100644" for path in F1010_M3_FINAL_READINESS_ALLOWED_STATUSES
}

F1010_M3_APPLY_PROJECTION_ALLOWED_STATUSES = {
    ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
    ".context/estado_del_proyecto.md": "M",
    ".context/operaciones/m3_f10_10_scope_por_ambiente_target.md": "M",
    ".context/operaciones/m3_reader_f10_10_rebaseline.md": "M",
    ".github/workflows/f9-7-contract.yml": "M",
    "scripts/maintenance/f10_10_m3_apply_projection.py": "A",
    "scripts/security/f109_boundary.py": "M",
    "tests/sql/run_fase10_10_m3_free_reader_postgres17.sh": "M",
    "tests/test_f10_10_m3_apply_projection.py": "A",
    "tests/test_f10_10_m3_reader_package.py": "M",
    "tests/test_fase10_9_branch_reconciliation.py": "M",
}

F1010_M3_APPLY_PROJECTION_ALLOWED_MODES = {
    path: (
        "100755"
        if path == "tests/sql/run_fase10_10_m3_free_reader_postgres17.sh"
        else "100644"
    )
    for path in F1010_M3_APPLY_PROJECTION_ALLOWED_STATUSES
}

F1010_M3_DDL_PAYLOAD_ALLOWED_STATUSES = {
    ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
    ".context/estado_del_proyecto.md": "M",
    ".context/operaciones/m3_f10_10_scope_por_ambiente_target.md": "M",
    ".context/operaciones/m3_reader_f10_10_ddl_free_payload_2026_08_12.json": "A",
    ".context/operaciones/m3_reader_f10_10_rebaseline.md": "M",
    "scripts/security/f109_boundary.py": "M",
    "tests/test_fase10_9_branch_reconciliation.py": "M",
}

F1010_M3_DDL_PAYLOAD_ALLOWED_MODES = {
    path: "100644" for path in F1010_M3_DDL_PAYLOAD_ALLOWED_STATUSES
}

F1010_M3_DDL_PAYLOAD_REFRESH_ALLOWED_STATUSES = {
    ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
    ".context/estado_del_proyecto.md": "M",
    ".context/operaciones/m3_f10_10_scope_por_ambiente_target.md": "M",
    ".context/operaciones/m3_reader_f10_10_ddl_free_payload_2026_08_12.json": "M",
    ".context/operaciones/m3_reader_f10_10_rebaseline.md": "M",
    "scripts/security/f109_boundary.py": "M",
    "tests/test_fase10_9_branch_reconciliation.py": "M",
}

F1010_M3_DDL_PAYLOAD_REFRESH_ALLOWED_MODES = {
    path: "100644" for path in F1010_M3_DDL_PAYLOAD_REFRESH_ALLOWED_STATUSES
}

F1010_M3_NULLABILITY_REMEDIATION_ALLOWED_STATUSES = {
    ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
    ".context/estado_del_proyecto.md": "M",
    ".context/operaciones/flujo_release_minimo.md": "M",
    ".context/operaciones/m3_f10_10_scope_por_ambiente_target.md": "M",
    ".context/operaciones/m3_reader_f10_10_nullability_remediation_2026_08_12.json": "A",
    ".context/operaciones/m3_reader_f10_10_rebaseline.md": "M",
    ".context/operaciones/plan_cierre_hito1_ca1_only.md": "M",
    ".context/operaciones/plan_remediacion_metadata_f10_10.md": "M",
    "db/free_only_migrations/20260811_fase10_10_m3_free_reader.sql": "M",
    "scripts/maintenance/f10_10_m3_readonly_collector.py": "M",
    "scripts/security/f109_boundary.py": "M",
    "tests/sql/run_fase10_10_m3_free_reader_postgres17.sh": "M",
    "tests/test_f10_10_m3_apply_projection.py": "M",
    "tests/test_f10_10_m3_reader_package.py": "M",
    "tests/test_f10_10_m3_readonly_collector.py": "M",
    "tests/test_fase10_9_branch_reconciliation.py": "M",
}

F1010_M3_NULLABILITY_REMEDIATION_ALLOWED_MODES = {
    path: (
        "100755"
        if path == "tests/sql/run_fase10_10_m3_free_reader_postgres17.sh"
        else "100644"
    )
    for path in F1010_M3_NULLABILITY_REMEDIATION_ALLOWED_STATUSES
}

F1010_M3_DDL_V2_PAYLOAD_ALLOWED_STATUSES = {
    ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
    ".context/estado_del_proyecto.md": "M",
    ".context/operaciones/m3_f10_10_scope_por_ambiente_target.md": "M",
    ".context/operaciones/m3_reader_f10_10_ddl_free_payload_2026_08_12.json": "M",
    ".context/operaciones/m3_reader_f10_10_rebaseline.md": "M",
    "scripts/security/f109_boundary.py": "M",
    "tests/test_fase10_9_branch_reconciliation.py": "M",
}

F1010_M3_DDL_V2_PAYLOAD_ALLOWED_MODES = {
    path: "100644" for path in F1010_M3_DDL_V2_PAYLOAD_ALLOWED_STATUSES
}

F1010_M3_PUBLIC_ACL_REBASELINE_ALLOWED_STATUSES = {
    ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
    ".context/estado_del_proyecto.md": "M",
    ".context/operaciones/flujo_release_minimo.md": "M",
    ".context/operaciones/m3_f10_10_scope_por_ambiente_target.md": "M",
    ".context/operaciones/m3_public_db_acl_diagnostic_free_payload_2026_08_12.json": "A",
    ".context/operaciones/m3_reader_f10_10_ddl_free_v2_execution_evidence_2026_08_12.md": "A",
    ".context/operaciones/m3_reader_f10_10_rebaseline.md": "M",
    ".context/operaciones/plan_cierre_hito1_ca1_only.md": "M",
    ".context/operaciones/plan_remediacion_metadata_f10_10.md": "M",
    "db/free_only_migrations/20260811_fase10_10_m3_free_reader.sql": "M",
    "scripts/maintenance/f10_10_m3_public_db_acl_diagnostic.py": "A",
    "scripts/security/f109_boundary.py": "M",
    "tests/sql/run_fase10_10_m3_free_reader_postgres17.sh": "M",
    "tests/test_f10_10_m3_apply_projection.py": "M",
    "tests/test_f10_10_m3_public_db_acl_diagnostic.py": "A",
    "tests/test_f10_10_m3_reader_package.py": "M",
    "tests/test_fase10_9_branch_reconciliation.py": "M",
}

F1010_M3_PUBLIC_ACL_REBASELINE_ALLOWED_MODES = {
    path: (
        "100755"
        if path == "tests/sql/run_fase10_10_m3_free_reader_postgres17.sh"
        else "100644"
    )
    for path in F1010_M3_PUBLIC_ACL_REBASELINE_ALLOWED_STATUSES
}

F1010_M3_PUBLIC_ACL_V2_PAYLOAD_ALLOWED_STATUSES = {
    ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
    ".context/estado_del_proyecto.md": "M",
    ".context/operaciones/flujo_release_minimo.md": "M",
    ".context/operaciones/m3_f10_10_scope_por_ambiente_target.md": "M",
    ".context/operaciones/m3_public_db_acl_diagnostic_free_v2_payload_2026_08_12.json": "A",
    ".context/operaciones/m3_reader_f10_10_rebaseline.md": "M",
    ".context/operaciones/plan_cierre_hito1_ca1_only.md": "M",
    ".context/operaciones/plan_remediacion_metadata_f10_10.md": "M",
    "scripts/security/f109_boundary.py": "M",
    "tests/test_fase10_9_branch_reconciliation.py": "M",
}
F1010_M3_PUBLIC_ACL_V2_PAYLOAD_ALLOWED_MODES = {
    path: "100644" for path in F1010_M3_PUBLIC_ACL_V2_PAYLOAD_ALLOWED_STATUSES
}

F1010_M3_PUBLIC_ACL_V3_ALLOWED_STATUSES = {
    ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
    ".context/estado_del_proyecto.md": "M",
    ".context/operaciones/flujo_release_minimo.md": "M",
    ".context/operaciones/m3_f10_10_scope_por_ambiente_target.md": "M",
    ".context/operaciones/m3_public_db_acl_diagnostic_free_v3_payload_2026_08_12.json": "A",
    ".context/operaciones/m3_reader_f10_10_rebaseline.md": "M",
    ".context/operaciones/plan_cierre_hito1_ca1_only.md": "M",
    ".context/operaciones/plan_remediacion_metadata_f10_10.md": "M",
    "scripts/maintenance/f10_10_m3_public_db_acl_diagnostic.py": "M",
    "scripts/security/f109_boundary.py": "M",
    "tests/test_f10_10_m3_public_db_acl_diagnostic.py": "M",
    "tests/test_fase10_9_branch_reconciliation.py": "M",
}
F1010_M3_PUBLIC_ACL_V3_ALLOWED_MODES = {
    path: "100644" for path in F1010_M3_PUBLIC_ACL_V3_ALLOWED_STATUSES
}

F1010_M3_PUBLIC_ACL_V3_BOUND_ALLOWED_STATUSES = {
    ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
    ".context/estado_del_proyecto.md": "M",
    ".context/operaciones/flujo_release_minimo.md": "M",
    ".context/operaciones/m3_f10_10_scope_por_ambiente_target.md": "M",
    ".context/operaciones/m3_public_db_acl_diagnostic_free_v3_execution_binding_2026_08_12.json": "A",
    ".context/operaciones/m3_reader_f10_10_rebaseline.md": "M",
    ".context/operaciones/plan_cierre_hito1_ca1_only.md": "M",
    ".context/operaciones/plan_remediacion_metadata_f10_10.md": "M",
    "scripts/security/f109_boundary.py": "M",
    "tests/test_fase10_9_branch_reconciliation.py": "M",
}
F1010_M3_PUBLIC_ACL_V3_BOUND_ALLOWED_MODES = {
    path: "100644" for path in F1010_M3_PUBLIC_ACL_V3_BOUND_ALLOWED_STATUSES
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


def validate_f1010_m2a_wiring(repo: Path, base: str, head: str, event: str) -> None:
    require(base == F1010_M2A_BASE, "unexpected F10.10 M2a wiring baseline")
    require_sha(repo, "F1010_M2A_BASE", base)
    require_sha(repo, "head", head)
    require(commit_tree(repo, base) == F1010_M2A_BASE_TREE, "F10.10 M2a baseline tree drift")
    candidate_head = head
    if event == "push":
        push_parents = commit_parents(repo, head)
        require(len(push_parents) == 2, "F10.10 M2a push must be a protected merge commit")
        require(push_parents[0] == base, "F10.10 M2a push first parent drift")
        candidate_head = push_parents[1]
        require(
            commit_tree(repo, head) == commit_tree(repo, candidate_head),
            "F10.10 M2a push tree differs from PR head",
        )
    require(
        commit_parents(repo, candidate_head) == [base],
        "F10.10 M2a PR must be one direct commit",
    )
    require_exact_delta(
        repo,
        base,
        candidate_head,
        F1010_M2A_ALLOWED_STATUSES,
        F1010_M2A_ALLOWED_MODES,
    )
    validate_context_graph(
        repo,
        expected_files=48,
        expected_links=345,
        expected_blobs=CONTEXT_EXPECTED_BLOBS,
        forbidden_paths=CONTEXT_FORBIDDEN_PATHS,
    )


def validate_f1010_m1(
    repo: Path,
    base: str,
    head: str,
    f1010_m1_base: str,
    f1010_m1_base_tree: str,
    event: str,
) -> None:
    require(bool(SHA_RE.fullmatch(f1010_m1_base)), "F10.10 M1 baseline is not frozen")
    require(bool(SHA_RE.fullmatch(f1010_m1_base_tree)), "F10.10 M1 baseline tree is not frozen")
    require(base == f1010_m1_base, "F10.10 M1 must use the protected post-M2a desarrollo baseline")
    require_sha(repo, "base", base)
    require_sha(repo, "head", head)
    require(commit_tree(repo, base) == f1010_m1_base_tree, "F10.10 M1 protected base tree drift")
    require(is_ancestor(repo, base, head), "F10.10 M1 base is not an ancestor of head")
    candidate_head = head
    if event == "pull_request":
        require(
            commit_parents(repo, candidate_head) == [base],
            "F10.10 M1 PR head must be one direct commit from protected desarrollo",
        )
    else:
        push_parents = commit_parents(repo, head)
        require(len(push_parents) == 2, "F10.10 M1 push must be a protected merge commit")
        require(push_parents[0] == base, "F10.10 M1 push first parent must be protected desarrollo")
        candidate_head = push_parents[1]
        require(
            commit_parents(repo, candidate_head) == [base],
            "F10.10 M1 merged PR must contain one direct commit",
        )
        require(
            commit_tree(repo, head) == commit_tree(repo, candidate_head),
            "F10.10 M1 push tree differs from PR head",
        )
    require_exact_delta(
        repo,
        base,
        candidate_head,
        F1010_M1_ALLOWED_STATUSES,
        F1010_M1_ALLOWED_MODES,
    )


def validate_f1010_m3(repo: Path, base: str, head: str, event: str) -> None:
    require(base == F1010_M3_BASE, "unexpected F10.10 M3 protected baseline")
    require_sha(repo, "F1010_M3_BASE", base)
    require_sha(repo, "head", head)
    require(commit_tree(repo, base) == F1010_M3_BASE_TREE, "F10.10 M3 protected base tree drift")
    require(is_ancestor(repo, base, head), "F10.10 M3 base is not an ancestor of head")
    candidate_head = head
    if event == "pull_request":
        require(
            commit_parents(repo, candidate_head) == [base],
            "F10.10 M3 PR head must be one direct commit from protected desarrollo",
        )
    else:
        push_parents = commit_parents(repo, head)
        require(len(push_parents) == 2, "F10.10 M3 push must be a protected merge commit")
        require(push_parents[0] == base, "F10.10 M3 push first parent must be protected desarrollo")
        candidate_head = push_parents[1]
        require(
            commit_parents(repo, candidate_head) == [base],
            "F10.10 M3 merged PR must contain one direct commit",
        )
        require(
            commit_tree(repo, head) == commit_tree(repo, candidate_head),
            "F10.10 M3 push tree differs from PR head",
        )
    require_exact_delta(
        repo,
        base,
        candidate_head,
        F1010_M3_ALLOWED_STATUSES,
        F1010_M3_ALLOWED_MODES,
    )


def validate_f1010_m3_reader(repo: Path, base: str, head: str, event: str) -> None:
    require(base == F1010_M3_READER_BASE, "unexpected F10.10 M3 reader protected baseline")
    require_sha(repo, "F1010_M3_READER_BASE", base)
    require_sha(repo, "head", head)
    require(
        commit_tree(repo, base) == F1010_M3_READER_BASE_TREE,
        "F10.10 M3 reader protected base tree drift",
    )
    require(is_ancestor(repo, base, head), "F10.10 M3 reader base is not an ancestor of head")
    candidate_head = head
    if event == "pull_request":
        require(
            commit_parents(repo, candidate_head) == [base],
            "F10.10 M3 reader PR head must be one direct commit from protected desarrollo",
        )
    else:
        push_parents = commit_parents(repo, head)
        require(len(push_parents) == 2, "F10.10 M3 reader push must be a protected merge commit")
        require(push_parents[0] == base, "F10.10 M3 reader push first parent must be protected desarrollo")
        candidate_head = push_parents[1]
        require(
            commit_parents(repo, candidate_head) == [base],
            "F10.10 M3 reader merged PR must contain one direct commit",
        )
        require(
            commit_tree(repo, head) == commit_tree(repo, candidate_head),
            "F10.10 M3 reader push tree differs from PR head",
        )
    require_exact_delta(
        repo,
        base,
        candidate_head,
        F1010_M3_READER_ALLOWED_STATUSES,
        F1010_M3_READER_ALLOWED_MODES,
    )
    validate_context_graph(repo, 52, 363)


def validate_f1010_m3_reader_post_merge(
    repo: Path, base: str, head: str, event: str
) -> None:
    require(
        base == F1010_M3_READER_POST_MERGE_BASE,
        "unexpected F10.10 M3 reader post-merge baseline",
    )
    require_sha(repo, "F1010_M3_READER_POST_MERGE_BASE", base)
    require_sha(repo, "head", head)
    require(
        commit_tree(repo, base) == F1010_M3_READER_POST_MERGE_BASE_TREE,
        "F10.10 M3 reader post-merge base tree drift",
    )
    require(
        is_ancestor(repo, base, head),
        "F10.10 M3 reader post-merge base is not an ancestor of head",
    )
    candidate_head = head
    if event == "push":
        push_parents = commit_parents(repo, head)
        require(
            len(push_parents) == 2,
            "F10.10 M3 reader post-merge push must be a protected merge commit",
        )
        require(
            push_parents[0] == base,
            "F10.10 M3 reader post-merge push first parent drift",
        )
        candidate_head = push_parents[1]
        require(
            is_ancestor(repo, base, candidate_head),
            "F10.10 M3 reader post-merge PR head does not descend from baseline",
        )
        require(
            commit_tree(repo, head) == commit_tree(repo, candidate_head),
            "F10.10 M3 reader post-merge push tree differs from PR head",
        )
    first_parent_chain = str(
        git(repo, "rev-list", "--reverse", "--first-parent", f"{base}..{candidate_head}")
    ).split()
    require(
        first_parent_chain
        == [F1010_M3_READER_POST_MERGE_DOCS_COMMIT, candidate_head],
        "F10.10 M3 reader post-merge candidate must contain the frozen docs commit and one remediation commit",
    )
    all_commits = str(git(repo, "rev-list", f"{base}..{candidate_head}")).split()
    require(
        set(all_commits) == set(first_parent_chain),
        "F10.10 M3 reader post-merge candidate cannot contain merge or side history",
    )
    require(
        commit_parents(repo, F1010_M3_READER_POST_MERGE_DOCS_COMMIT) == [base],
        "F10.10 M3 reader post-merge docs commit parent drift",
    )
    require(
        commit_parents(repo, candidate_head)
        == [F1010_M3_READER_POST_MERGE_DOCS_COMMIT],
        "F10.10 M3 reader post-merge remediation must directly follow the docs commit",
    )
    require_exact_delta(
        repo,
        base,
        candidate_head,
        F1010_M3_READER_POST_MERGE_ALLOWED_STATUSES,
        F1010_M3_READER_POST_MERGE_ALLOWED_MODES,
    )
    validate_context_graph(repo, 53, 362)


def validate_f1010_m3_rotation(repo: Path, base: str, head: str, event: str) -> None:
    require(base == F1010_M3_ROTATION_BASE, "unexpected F10.10 M3 rotation baseline")
    require_sha(repo, "F1010_M3_ROTATION_BASE", base)
    require_sha(repo, "head", head)
    require(
        commit_tree(repo, base) == F1010_M3_ROTATION_BASE_TREE,
        "F10.10 M3 rotation base tree drift",
    )
    require(is_ancestor(repo, base, head), "F10.10 M3 rotation base is not an ancestor of head")
    candidate_head = head
    if event == "pull_request":
        require(
            commit_parents(repo, candidate_head) == [base],
            "F10.10 M3 rotation PR head must be one direct commit from protected desarrollo",
        )
    else:
        push_parents = commit_parents(repo, head)
        require(len(push_parents) == 2, "F10.10 M3 rotation push must be a protected merge commit")
        require(push_parents[0] == base, "F10.10 M3 rotation push first parent drift")
        candidate_head = push_parents[1]
        require(
            commit_parents(repo, candidate_head) == [base],
            "F10.10 M3 rotation merged PR must contain one direct commit",
        )
        require(
            commit_tree(repo, head) == commit_tree(repo, candidate_head),
            "F10.10 M3 rotation push tree differs from PR head",
        )
    require_exact_delta(
        repo,
        base,
        candidate_head,
        F1010_M3_ROTATION_ALLOWED_STATUSES,
        F1010_M3_ROTATION_ALLOWED_MODES,
    )
    validate_context_graph(repo, 54, 369)


def validate_f1010_m3_passwordless(
    repo: Path, base: str, head: str, event: str,
) -> None:
    require(
        base == F1010_M3_PASSWORDLESS_BASE,
        "unexpected F10.10 M3 passwordless binding baseline",
    )
    require_sha(repo, "F1010_M3_PASSWORDLESS_BASE", base)
    require_sha(repo, "head", head)
    require(
        commit_tree(repo, base) == F1010_M3_PASSWORDLESS_BASE_TREE,
        "F10.10 M3 passwordless binding base tree drift",
    )
    require(
        is_ancestor(repo, base, head),
        "F10.10 M3 passwordless binding base is not an ancestor of head",
    )
    candidate_head = head
    if event == "pull_request":
        require(
            commit_parents(repo, candidate_head) == [base],
            "F10.10 M3 passwordless binding PR must be one direct commit",
        )
    else:
        push_parents = commit_parents(repo, head)
        require(
            len(push_parents) == 2 and push_parents[0] == base,
            "F10.10 M3 passwordless binding push must be a protected merge",
        )
        candidate_head = push_parents[1]
        require(
            commit_parents(repo, candidate_head) == [base],
            "F10.10 M3 passwordless binding merged PR must be one direct commit",
        )
        require(
            commit_tree(repo, head) == commit_tree(repo, candidate_head),
            "F10.10 M3 passwordless binding push tree differs from PR head",
        )
    require_exact_delta(
        repo,
        base,
        candidate_head,
        F1010_M3_PASSWORDLESS_ALLOWED_STATUSES,
        F1010_M3_PASSWORDLESS_ALLOWED_MODES,
    )
    validate_context_graph(repo, 54, 369)


def validate_f1010_m3_preflight_payload(
    repo: Path, base: str, head: str, event: str,
) -> None:
    require(
        base == F1010_M3_PREFLIGHT_PAYLOAD_BASE,
        "unexpected F10.10 M3 preflight payload baseline",
    )
    require_sha(repo, "F1010_M3_PREFLIGHT_PAYLOAD_BASE", base)
    require_sha(repo, "head", head)
    require(
        commit_tree(repo, base) == F1010_M3_PREFLIGHT_PAYLOAD_BASE_TREE,
        "F10.10 M3 preflight payload base tree drift",
    )
    require(
        is_ancestor(repo, base, head),
        "F10.10 M3 preflight payload base is not an ancestor of head",
    )
    candidate_head = head
    if event == "pull_request":
        require(
            commit_parents(repo, candidate_head) == [base],
            "F10.10 M3 preflight payload PR must be one direct commit",
        )
    else:
        push_parents = commit_parents(repo, head)
        require(
            len(push_parents) == 2 and push_parents[0] == base,
            "F10.10 M3 preflight payload push must be a protected merge",
        )
        candidate_head = push_parents[1]
        require(
            commit_parents(repo, candidate_head) == [base],
            "F10.10 M3 preflight payload merged PR must be one direct commit",
        )
        require(
            commit_tree(repo, head) == commit_tree(repo, candidate_head),
            "F10.10 M3 preflight payload push tree differs from PR head",
        )
    require_exact_delta(
        repo,
        base,
        candidate_head,
        F1010_M3_PREFLIGHT_PAYLOAD_ALLOWED_STATUSES,
        F1010_M3_PREFLIGHT_PAYLOAD_ALLOWED_MODES,
    )
    validate_context_graph(repo, 54, 374)


def validate_f1010_m3_preflight_evidence(
    repo: Path, base: str, head: str, event: str,
) -> None:
    require(
        base == F1010_M3_PREFLIGHT_EVIDENCE_BASE,
        "unexpected F10.10 M3 preflight evidence baseline",
    )
    require_sha(repo, "F1010_M3_PREFLIGHT_EVIDENCE_BASE", base)
    require_sha(repo, "head", head)
    require(
        commit_tree(repo, base) == F1010_M3_PREFLIGHT_EVIDENCE_BASE_TREE,
        "F10.10 M3 preflight evidence base tree drift",
    )
    require(
        is_ancestor(repo, base, head),
        "F10.10 M3 preflight evidence base is not an ancestor of head",
    )
    candidate_head = head
    if event == "pull_request":
        require(
            commit_parents(repo, candidate_head) == [base],
            "F10.10 M3 preflight evidence PR must be one direct commit",
        )
    else:
        push_parents = commit_parents(repo, head)
        require(
            len(push_parents) == 2 and push_parents[0] == base,
            "F10.10 M3 preflight evidence push must be a protected merge",
        )
        candidate_head = push_parents[1]
        require(
            commit_parents(repo, candidate_head) == [base],
            "F10.10 M3 preflight evidence merged PR must be one direct commit",
        )
        require(
            commit_tree(repo, head) == commit_tree(repo, candidate_head),
            "F10.10 M3 preflight evidence push tree differs from PR head",
        )
    require_exact_delta(
        repo,
        base,
        candidate_head,
        F1010_M3_PREFLIGHT_EVIDENCE_ALLOWED_STATUSES,
        F1010_M3_PREFLIGHT_EVIDENCE_ALLOWED_MODES,
    )
    validate_context_graph(repo, 55, 379)


def validate_f1010_m3_final_readiness(
    repo: Path, base: str, head: str, event: str,
) -> None:
    require(
        base == F1010_M3_FINAL_READINESS_BASE,
        "unexpected F10.10 M3 final readiness baseline",
    )
    require_sha(repo, "F1010_M3_FINAL_READINESS_BASE", base)
    require_sha(repo, "head", head)
    require(
        commit_tree(repo, base) == F1010_M3_FINAL_READINESS_BASE_TREE,
        "F10.10 M3 final readiness base tree drift",
    )
    require(
        is_ancestor(repo, base, head),
        "F10.10 M3 final readiness base is not an ancestor of head",
    )
    candidate_head = head
    if event == "pull_request":
        require(
            commit_parents(repo, candidate_head) == [base],
            "F10.10 M3 final readiness PR must be one direct commit",
        )
    else:
        push_parents = commit_parents(repo, head)
        require(
            len(push_parents) == 2 and push_parents[0] == base,
            "F10.10 M3 final readiness push must be a protected merge",
        )
        candidate_head = push_parents[1]
        require(
            commit_parents(repo, candidate_head) == [base],
            "F10.10 M3 final readiness merged PR must be one direct commit",
        )
        require(
            commit_tree(repo, head) == commit_tree(repo, candidate_head),
            "F10.10 M3 final readiness push tree differs from PR head",
        )
    require_exact_delta(
        repo,
        base,
        candidate_head,
        F1010_M3_FINAL_READINESS_ALLOWED_STATUSES,
        F1010_M3_FINAL_READINESS_ALLOWED_MODES,
    )
    validate_context_graph(repo, 55, 379)


def validate_f1010_m3_apply_projection(
    repo: Path, base: str, head: str, event: str,
) -> None:
    require(
        base == F1010_M3_APPLY_PROJECTION_BASE,
        "unexpected F10.10 M3 apply projection baseline",
    )
    require_sha(repo, "F1010_M3_APPLY_PROJECTION_BASE", base)
    require_sha(repo, "head", head)
    require(
        commit_tree(repo, base) == F1010_M3_APPLY_PROJECTION_BASE_TREE,
        "F10.10 M3 apply projection base tree drift",
    )
    require(
        is_ancestor(repo, base, head),
        "F10.10 M3 apply projection base is not an ancestor of head",
    )
    candidate_head = head
    if event == "pull_request":
        require(
            commit_parents(repo, candidate_head) == [base],
            "F10.10 M3 apply projection PR must be one direct commit",
        )
    else:
        push_parents = commit_parents(repo, head)
        require(
            len(push_parents) == 2 and push_parents[0] == base,
            "F10.10 M3 apply projection push must be a protected merge",
        )
        candidate_head = push_parents[1]
        require(
            commit_parents(repo, candidate_head) == [base],
            "F10.10 M3 apply projection merged PR must be one direct commit",
        )
        require(
            commit_tree(repo, head) == commit_tree(repo, candidate_head),
            "F10.10 M3 apply projection push tree differs from PR head",
        )
    require_exact_delta(
        repo,
        base,
        candidate_head,
        F1010_M3_APPLY_PROJECTION_ALLOWED_STATUSES,
        F1010_M3_APPLY_PROJECTION_ALLOWED_MODES,
    )
    validate_context_graph(repo, 55, 379)


def validate_f1010_m3_ddl_payload(
    repo: Path, base: str, head: str, event: str,
) -> None:
    require(
        base == F1010_M3_DDL_PAYLOAD_BASE,
        "unexpected F10.10 M3 DDL payload baseline",
    )
    require_sha(repo, "F1010_M3_DDL_PAYLOAD_BASE", base)
    require_sha(repo, "head", head)
    require(
        commit_tree(repo, base) == F1010_M3_DDL_PAYLOAD_BASE_TREE,
        "F10.10 M3 DDL payload base tree drift",
    )
    require(
        is_ancestor(repo, base, head),
        "F10.10 M3 DDL payload base is not an ancestor of head",
    )
    candidate_head = head
    if event == "pull_request":
        require(
            commit_parents(repo, candidate_head) == [base],
            "F10.10 M3 DDL payload PR must be one direct commit",
        )
    else:
        push_parents = commit_parents(repo, head)
        require(
            len(push_parents) == 2 and push_parents[0] == base,
            "F10.10 M3 DDL payload push must be a protected merge",
        )
        candidate_head = push_parents[1]
        require(
            commit_parents(repo, candidate_head) == [base],
            "F10.10 M3 DDL payload merged PR must be one direct commit",
        )
        require(
            commit_tree(repo, head) == commit_tree(repo, candidate_head),
            "F10.10 M3 DDL payload push tree differs from PR head",
        )
    require_exact_delta(
        repo,
        base,
        candidate_head,
        F1010_M3_DDL_PAYLOAD_ALLOWED_STATUSES,
        F1010_M3_DDL_PAYLOAD_ALLOWED_MODES,
    )
    validate_context_graph(repo, 55, 382)


def validate_f1010_m3_ddl_payload_refresh(
    repo: Path, base: str, head: str, event: str,
) -> None:
    require(
        base == F1010_M3_DDL_PAYLOAD_REFRESH_BASE,
        "unexpected F10.10 M3 DDL payload refresh baseline",
    )
    require_sha(repo, "F1010_M3_DDL_PAYLOAD_REFRESH_BASE", base)
    require_sha(repo, "head", head)
    require(
        commit_tree(repo, base) == F1010_M3_DDL_PAYLOAD_REFRESH_BASE_TREE,
        "F10.10 M3 DDL payload refresh base tree drift",
    )
    require(
        is_ancestor(repo, base, head),
        "F10.10 M3 DDL payload refresh base is not an ancestor of head",
    )
    candidate_head = head
    if event == "pull_request":
        require(
            commit_parents(repo, candidate_head) == [base],
            "F10.10 M3 DDL payload refresh PR must be one direct commit",
        )
    else:
        push_parents = commit_parents(repo, head)
        require(
            len(push_parents) == 2 and push_parents[0] == base,
            "F10.10 M3 DDL payload refresh push must be a protected merge",
        )
        candidate_head = push_parents[1]
        require(
            commit_parents(repo, candidate_head) == [base],
            "F10.10 M3 DDL payload refresh merged PR must be one direct commit",
        )
        require(
            commit_tree(repo, head) == commit_tree(repo, candidate_head),
            "F10.10 M3 DDL payload refresh push tree differs from PR head",
        )
    require_exact_delta(
        repo,
        base,
        candidate_head,
        F1010_M3_DDL_PAYLOAD_REFRESH_ALLOWED_STATUSES,
        F1010_M3_DDL_PAYLOAD_REFRESH_ALLOWED_MODES,
    )
    validate_context_graph(repo, 55, 382)


def validate_f1010_m3_nullability_remediation(
    repo: Path, base: str, head: str, event: str,
) -> None:
    require(
        base == F1010_M3_NULLABILITY_REMEDIATION_BASE,
        "unexpected F10.10 M3 nullability remediation baseline",
    )
    require_sha(repo, "F1010_M3_NULLABILITY_REMEDIATION_BASE", base)
    require_sha(repo, "head", head)
    require(
        commit_tree(repo, base) == F1010_M3_NULLABILITY_REMEDIATION_BASE_TREE,
        "F10.10 M3 nullability remediation base tree drift",
    )
    require(is_ancestor(repo, base, head), "nullability remediation base is not ancestor")
    candidate_head = head
    if event == "pull_request":
        require(commit_parents(repo, candidate_head) == [base], "nullability PR must be one direct commit")
    else:
        push_parents = commit_parents(repo, head)
        require(
            len(push_parents) == 2 and push_parents[0] == base,
            "nullability push must be a protected merge",
        )
        candidate_head = push_parents[1]
        require(commit_parents(repo, candidate_head) == [base], "merged nullability PR must be direct")
        require(commit_tree(repo, head) == commit_tree(repo, candidate_head), "nullability push tree drift")
    require_exact_delta(
        repo,
        base,
        candidate_head,
        F1010_M3_NULLABILITY_REMEDIATION_ALLOWED_STATUSES,
        F1010_M3_NULLABILITY_REMEDIATION_ALLOWED_MODES,
    )
    validate_context_graph(repo, 55, 379)


def validate_f1010_m3_ddl_v2_payload(
    repo: Path, base: str, head: str, event: str,
) -> None:
    require(
        base == F1010_M3_DDL_V2_PAYLOAD_BASE,
        "unexpected M3 DDL v2 payload baseline",
    )
    require_sha(repo, "F1010_M3_DDL_V2_PAYLOAD_BASE", base)
    require_sha(repo, "head", head)
    require(
        commit_tree(repo, base) == F1010_M3_DDL_V2_PAYLOAD_BASE_TREE,
        "M3 DDL v2 payload base tree drift",
    )
    require(is_ancestor(repo, base, head), "M3 DDL v2 payload base is not ancestor")
    candidate_head = head
    if event == "pull_request":
        require(
            commit_parents(repo, candidate_head) == [base],
            "M3 DDL v2 PR must be one direct commit",
        )
    else:
        push_parents = commit_parents(repo, head)
        require(
            len(push_parents) == 2 and push_parents[0] == base,
            "M3 DDL v2 push must be a protected merge",
        )
        candidate_head = push_parents[1]
        require(
            commit_parents(repo, candidate_head) == [base],
            "merged M3 DDL v2 PR must be direct",
        )
        require(
            commit_tree(repo, head) == commit_tree(repo, candidate_head),
            "M3 DDL v2 push tree drift",
        )
    require_exact_delta(
        repo, base, candidate_head,
        F1010_M3_DDL_V2_PAYLOAD_ALLOWED_STATUSES,
        F1010_M3_DDL_V2_PAYLOAD_ALLOWED_MODES,
    )
    validate_context_graph(repo, 55, 376)


def validate_f1010_m3_public_acl_rebaseline(
    repo: Path, base: str, head: str, event: str,
) -> None:
    require(
        base == F1010_M3_PUBLIC_ACL_REBASELINE_BASE,
        "unexpected M3 PUBLIC ACL rebaseline baseline",
    )
    require_sha(repo, "F1010_M3_PUBLIC_ACL_REBASELINE_BASE", base)
    require_sha(repo, "head", head)
    require(
        commit_tree(repo, base) == F1010_M3_PUBLIC_ACL_REBASELINE_BASE_TREE,
        "M3 PUBLIC ACL rebaseline base tree drift",
    )
    require(is_ancestor(repo, base, head), "M3 PUBLIC ACL base is not ancestor")
    candidate_head = head
    if event == "pull_request":
        require(commit_parents(repo, candidate_head) == [base], "M3 PUBLIC ACL PR must be one direct commit")
    else:
        parents = commit_parents(repo, head)
        require(len(parents) == 2 and parents[0] == base, "M3 PUBLIC ACL push must be a protected merge")
        candidate_head = parents[1]
        require(commit_parents(repo, candidate_head) == [base], "merged M3 PUBLIC ACL PR must be direct")
        require(commit_tree(repo, head) == commit_tree(repo, candidate_head), "M3 PUBLIC ACL push tree drift")
    require_exact_delta(
        repo, base, candidate_head,
        F1010_M3_PUBLIC_ACL_REBASELINE_ALLOWED_STATUSES,
        F1010_M3_PUBLIC_ACL_REBASELINE_ALLOWED_MODES,
    )
    validate_context_graph(repo, 56, 377)


def validate_f1010_m3_public_acl_v2_payload(
    repo: Path, base: str, head: str, event: str,
) -> None:
    require(base == F1010_M3_PUBLIC_ACL_V2_PAYLOAD_BASE, "unexpected M3 PUBLIC ACL v2 payload baseline")
    require_sha(repo, "F1010_M3_PUBLIC_ACL_V2_PAYLOAD_BASE", base)
    require_sha(repo, "head", head)
    require(commit_tree(repo, base) == F1010_M3_PUBLIC_ACL_V2_PAYLOAD_BASE_TREE, "M3 PUBLIC ACL v2 payload base tree drift")
    require(is_ancestor(repo, base, head), "M3 PUBLIC ACL v2 payload base is not ancestor")
    candidate_head = head
    if event == "pull_request":
        require(commit_parents(repo, candidate_head) == [base], "M3 PUBLIC ACL v2 payload PR must be one direct commit")
    else:
        parents = commit_parents(repo, head)
        require(len(parents) == 2 and parents[0] == base, "M3 PUBLIC ACL v2 payload push must be a protected merge")
        candidate_head = parents[1]
        require(commit_parents(repo, candidate_head) == [base], "merged M3 PUBLIC ACL v2 payload PR must be direct")
        require(commit_tree(repo, head) == commit_tree(repo, candidate_head), "M3 PUBLIC ACL v2 payload push tree drift")
    require_exact_delta(repo, base, candidate_head, F1010_M3_PUBLIC_ACL_V2_PAYLOAD_ALLOWED_STATUSES, F1010_M3_PUBLIC_ACL_V2_PAYLOAD_ALLOWED_MODES)
    validate_context_graph(repo, 56, 377)


def validate_f1010_m3_public_acl_v3(
    repo: Path, base: str, head: str, event: str,
) -> None:
    require(base == F1010_M3_PUBLIC_ACL_V3_BASE, "unexpected M3 PUBLIC ACL v3 baseline")
    require_sha(repo, "F1010_M3_PUBLIC_ACL_V3_BASE", base)
    require_sha(repo, "head", head)
    require(commit_tree(repo, base) == F1010_M3_PUBLIC_ACL_V3_BASE_TREE, "M3 PUBLIC ACL v3 base tree drift")
    require(is_ancestor(repo, base, head), "M3 PUBLIC ACL v3 base is not ancestor")
    candidate_head = head
    if event == "pull_request":
        require(commit_parents(repo, candidate_head) == [base], "M3 PUBLIC ACL v3 PR must be one direct commit")
    else:
        parents = commit_parents(repo, head)
        require(len(parents) == 2 and parents[0] == base, "M3 PUBLIC ACL v3 push must be a protected merge")
        candidate_head = parents[1]
        require(commit_parents(repo, candidate_head) == [base], "merged M3 PUBLIC ACL v3 PR must be direct")
        require(commit_tree(repo, head) == commit_tree(repo, candidate_head), "M3 PUBLIC ACL v3 push tree drift")
    require_exact_delta(repo, base, candidate_head, F1010_M3_PUBLIC_ACL_V3_ALLOWED_STATUSES, F1010_M3_PUBLIC_ACL_V3_ALLOWED_MODES)
    validate_context_graph(repo, 56, 377)


def validate_f1010_m3_public_acl_v3_bound(
    repo: Path, base: str, head: str, event: str,
) -> None:
    require(base == F1010_M3_PUBLIC_ACL_V3_BOUND_BASE, "unexpected M3 PUBLIC ACL v3 bound baseline")
    require_sha(repo, "F1010_M3_PUBLIC_ACL_V3_BOUND_BASE", base)
    require_sha(repo, "head", head)
    require(commit_tree(repo, base) == F1010_M3_PUBLIC_ACL_V3_BOUND_BASE_TREE, "M3 PUBLIC ACL v3 bound base tree drift")
    require(is_ancestor(repo, base, head), "M3 PUBLIC ACL v3 bound base is not ancestor")
    candidate_head = head
    if event == "pull_request":
        require(commit_parents(repo, candidate_head) == [base], "M3 PUBLIC ACL v3 bound PR must be one direct commit")
    else:
        parents = commit_parents(repo, head)
        require(len(parents) == 2 and parents[0] == base, "M3 PUBLIC ACL v3 bound push must be a protected merge")
        candidate_head = parents[1]
        require(commit_parents(repo, candidate_head) == [base], "merged M3 PUBLIC ACL v3 bound PR must be direct")
        require(commit_tree(repo, head) == commit_tree(repo, candidate_head), "M3 PUBLIC ACL v3 bound push tree drift")
    require_exact_delta(repo, base, candidate_head, F1010_M3_PUBLIC_ACL_V3_BOUND_ALLOWED_STATUSES, F1010_M3_PUBLIC_ACL_V3_BOUND_ALLOWED_MODES)
    validate_context_graph(repo, 56, 377)


def validate_f1010_m3_public_acl_preflight(
    repo: Path, base: str, head: str, event: str,
) -> None:
    require(base == F1010_M3_PUBLIC_ACL_PREFLIGHT_BASE, "unexpected M3 PUBLIC ACL preflight baseline")
    require_sha(repo, "F1010_M3_PUBLIC_ACL_PREFLIGHT_BASE", base)
    require_sha(repo, "head", head)
    require(
        commit_tree(repo, base) == F1010_M3_PUBLIC_ACL_PREFLIGHT_BASE_TREE,
        "M3 PUBLIC ACL preflight base tree drift",
    )
    require(is_ancestor(repo, base, head), "M3 PUBLIC ACL preflight base is not ancestor")
    candidate_head = head
    if event == "pull_request":
        pass
    else:
        parents = commit_parents(repo, head)
        require(len(parents) == 2 and parents[0] == base, "M3 PUBLIC ACL preflight push must be a protected merge")
        candidate_head = parents[1]
        require(commit_tree(repo, head) == commit_tree(repo, candidate_head), "M3 PUBLIC ACL preflight push tree drift")
    linear_chain = str(
        git(repo, "rev-list", "--reverse", "--first-parent", f"{base}..{candidate_head}")
    ).split()
    require(bool(linear_chain), "M3 PUBLIC ACL preflight candidate is empty")
    previous = base
    for commit in linear_chain:
        require(
            commit_parents(repo, commit) == [previous],
            "M3 PUBLIC ACL preflight candidate must be a linear no-merge chain",
        )
        previous = commit
    require(previous == candidate_head, "M3 PUBLIC ACL preflight first-parent chain drift")
    require(
        set(str(git(repo, "rev-list", f"{base}..{candidate_head}")).split()) == set(linear_chain),
        "M3 PUBLIC ACL preflight contains side history",
    )
    require_exact_delta(
        repo, base, candidate_head,
        F1010_M3_PUBLIC_ACL_PREFLIGHT_ALLOWED_STATUSES,
        F1010_M3_PUBLIC_ACL_PREFLIGHT_ALLOWED_MODES,
    )
    validate_context_graph(repo, 57, 377)


def detect_mode(
    event: str,
    base_ref: str,
    head_ref: str,
    base: str,
    p1_base: str = "",
    p2_base: str = "",
    g2_base: str = "",
    p5_base: str = "",
    f1010_m1_base: str = "",
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
    if base_ref == "desarrollo" and base == F1010_M2A_BASE and (
        event == "push" or head_ref == F1010_M2A_HEAD_REF
    ):
        return "f1010_m2a"
    if base_ref == "desarrollo" and base == F1010_M3_BASE and (
        event == "push" or head_ref == F1010_M3_HEAD_REF
    ):
        return "f1010_m3"
    if base_ref == "desarrollo" and base == F1010_M3_READER_BASE and (
        event == "push" or head_ref == F1010_M3_READER_HEAD_REF
    ):
        return "f1010_m3_reader"
    if base_ref == "desarrollo" and base == F1010_M3_READER_POST_MERGE_BASE and (
        event == "push" or head_ref == F1010_M3_READER_POST_MERGE_HEAD_REF
    ):
        return "f1010_m3_reader_post_merge"
    if base_ref == "desarrollo" and base == F1010_M3_ROTATION_BASE and (
        event == "push" or head_ref == F1010_M3_ROTATION_HEAD_REF
    ):
        return "f1010_m3_rotation"
    if base_ref == "desarrollo" and base == F1010_M3_PASSWORDLESS_BASE and (
        event == "push" or head_ref == F1010_M3_PASSWORDLESS_HEAD_REF
    ):
        return "f1010_m3_passwordless"
    if base_ref == "desarrollo" and base == F1010_M3_PREFLIGHT_PAYLOAD_BASE and (
        event == "push" or head_ref == F1010_M3_PREFLIGHT_PAYLOAD_HEAD_REF
    ):
        return "f1010_m3_preflight_payload"
    if base_ref == "desarrollo" and base == F1010_M3_PREFLIGHT_EVIDENCE_BASE and (
        event == "push" or head_ref == F1010_M3_PREFLIGHT_EVIDENCE_HEAD_REF
    ):
        return "f1010_m3_preflight_evidence"
    if base_ref == "desarrollo" and base == F1010_M3_FINAL_READINESS_BASE and (
        event == "push" or head_ref == F1010_M3_FINAL_READINESS_HEAD_REF
    ):
        return "f1010_m3_final_readiness"
    if base_ref == "desarrollo" and base == F1010_M3_APPLY_PROJECTION_BASE and (
        event == "push" or head_ref == F1010_M3_APPLY_PROJECTION_HEAD_REF
    ):
        return "f1010_m3_apply_projection"
    if base_ref == "desarrollo" and base == F1010_M3_DDL_PAYLOAD_BASE and (
        event == "push" or head_ref == F1010_M3_DDL_PAYLOAD_HEAD_REF
    ):
        return "f1010_m3_ddl_payload"
    if base_ref == "desarrollo" and base == F1010_M3_DDL_PAYLOAD_REFRESH_BASE and (
        event == "push" or head_ref == F1010_M3_DDL_PAYLOAD_REFRESH_HEAD_REF
    ):
        return "f1010_m3_ddl_payload_refresh"
    if base_ref == "desarrollo" and base == F1010_M3_NULLABILITY_REMEDIATION_BASE and (
        event == "push" or head_ref == F1010_M3_NULLABILITY_REMEDIATION_HEAD_REF
    ):
        return "f1010_m3_nullability_remediation"
    if base_ref == "desarrollo" and base == F1010_M3_DDL_V2_PAYLOAD_BASE and (
        event == "push" or head_ref == F1010_M3_DDL_V2_PAYLOAD_HEAD_REF
    ):
        return "f1010_m3_ddl_v2_payload"
    if base_ref == "desarrollo" and base == F1010_M3_PUBLIC_ACL_REBASELINE_BASE and (
        event == "push" or head_ref == F1010_M3_PUBLIC_ACL_REBASELINE_HEAD_REF
    ):
        return "f1010_m3_public_acl_rebaseline"
    if base_ref == "desarrollo" and base == F1010_M3_PUBLIC_ACL_V2_PAYLOAD_BASE and (
        event == "push" or head_ref == F1010_M3_PUBLIC_ACL_V2_PAYLOAD_HEAD_REF
    ):
        return "f1010_m3_public_acl_v2_payload"
    if base_ref == "desarrollo" and base == F1010_M3_PUBLIC_ACL_V3_BASE and (
        event == "push" or head_ref == F1010_M3_PUBLIC_ACL_V3_HEAD_REF
    ):
        return "f1010_m3_public_acl_v3"
    if base_ref == "desarrollo" and base == F1010_M3_PUBLIC_ACL_V3_BOUND_BASE and (
        event == "push" or head_ref == F1010_M3_PUBLIC_ACL_V3_BOUND_HEAD_REF
    ):
        return "f1010_m3_public_acl_v3_bound"
    if base_ref == "desarrollo" and base == F1010_M3_PUBLIC_ACL_PREFLIGHT_BASE and (
        event == "push" or head_ref == F1010_M3_PUBLIC_ACL_PREFLIGHT_HEAD_REF
    ):
        return "f1010_m3_public_acl_preflight"
    if event == "pull_request" and base_ref == "desarrollo" and p1_base and base == p1_base and head_ref == P1_HEAD_REF:
        return "p1"
    if event == "pull_request" and base_ref == "desarrollo" and p2_base and base == p2_base and head_ref == P2_HEAD_REF:
        return "p2"
    if event == "pull_request" and base_ref == "desarrollo" and g2_base and base == g2_base and head_ref == G2_HEAD_REF:
        return "g2"
    if event == "pull_request" and base_ref == "desarrollo" and p5_base and base == p5_base and head_ref == P5_HEAD_REF:
        return "p5"
    if (
        event == "pull_request"
        and base_ref == "desarrollo"
        and f1010_m1_base
        and base == f1010_m1_base
        and head_ref == F1010_M1_HEAD_REF
    ):
        return "f1010_m1"
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
    parser.add_argument("--f1010-m1-base", default="")
    parser.add_argument("--f1010-m1-base-tree", default="")
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
            getattr(args, "f1010_m1_base", ""),
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
            if args.event == "pull_request" and args.head_ref == F1010_M2A_HEAD_REF:
                raise BoundaryError("F10.10 M2a wiring branch requires its frozen baseline")
            if args.event == "pull_request" and args.head_ref == F1010_M1_HEAD_REF:
                raise BoundaryError("F10.10 M1 branch requires the frozen protected desarrollo baseline")
            if args.event == "pull_request" and args.head_ref == F1010_M3_HEAD_REF:
                raise BoundaryError("F10.10 M3 branch requires the frozen protected desarrollo baseline")
            if args.event == "pull_request" and args.head_ref == F1010_M3_READER_HEAD_REF:
                raise BoundaryError("F10.10 M3 reader branch requires the frozen protected desarrollo baseline")
            if args.event == "pull_request" and args.head_ref == F1010_M3_READER_POST_MERGE_HEAD_REF:
                raise BoundaryError("F10.10 M3 reader post-merge branch requires its frozen protected desarrollo baseline")
            if args.event == "pull_request" and args.head_ref == F1010_M3_ROTATION_HEAD_REF:
                raise BoundaryError("F10.10 M3 rotation branch requires its frozen protected desarrollo baseline")
            if args.event == "pull_request" and args.head_ref == F1010_M3_PASSWORDLESS_HEAD_REF:
                raise BoundaryError("F10.10 M3 passwordless binding branch requires its frozen protected desarrollo baseline")
            if args.event == "pull_request" and args.head_ref == F1010_M3_PREFLIGHT_PAYLOAD_HEAD_REF:
                raise BoundaryError("F10.10 M3 preflight payload branch requires its frozen protected desarrollo baseline")
            if args.event == "pull_request" and args.head_ref == F1010_M3_PREFLIGHT_EVIDENCE_HEAD_REF:
                raise BoundaryError("F10.10 M3 preflight evidence branch requires its frozen protected desarrollo baseline")
            if args.event == "pull_request" and args.head_ref == F1010_M3_FINAL_READINESS_HEAD_REF:
                raise BoundaryError("F10.10 M3 final readiness branch requires its frozen protected desarrollo baseline")
            if args.event == "pull_request" and args.head_ref == F1010_M3_APPLY_PROJECTION_HEAD_REF:
                raise BoundaryError("F10.10 M3 apply projection branch requires its frozen protected desarrollo baseline")
            if args.event == "pull_request" and args.head_ref == F1010_M3_DDL_PAYLOAD_HEAD_REF:
                raise BoundaryError("F10.10 M3 DDL payload branch requires its frozen protected desarrollo baseline")
            if args.event == "pull_request" and args.head_ref == F1010_M3_DDL_PAYLOAD_REFRESH_HEAD_REF:
                raise BoundaryError("F10.10 M3 DDL payload refresh branch requires its frozen protected desarrollo baseline")
            if args.event == "pull_request" and args.head_ref == F1010_M3_NULLABILITY_REMEDIATION_HEAD_REF:
                raise BoundaryError("F10.10 M3 nullability remediation branch requires its frozen protected desarrollo baseline")
            if args.event == "pull_request" and args.head_ref == F1010_M3_PUBLIC_ACL_V3_BOUND_HEAD_REF:
                raise BoundaryError("F10.10 M3 PUBLIC ACL v3 bound branch requires its frozen protected desarrollo baseline")
            if args.event == "pull_request" and args.head_ref == F1010_M3_PUBLIC_ACL_PREFLIGHT_HEAD_REF:
                raise BoundaryError("F10.10 M3 PUBLIC ACL preflight branch requires its frozen protected desarrollo baseline")
            actual = changed_statuses(args.repo, args.base_sha, args.head_sha)
            touched_p1 = set(actual).intersection(P1_ALLOWED_STATUSES)
            touched_p2 = set(actual).intersection(P2_ALLOWED_STATUSES)
            touched_g2 = set(actual).intersection(G2_ALLOWED_STATUSES)
            touched_p5 = set(actual).intersection(P5_ALLOWED_STATUSES)
            touched_f1010_m1 = set(actual).intersection(F1010_M1_ALLOWED_STATUSES)
            touched_f1010_m3 = set(actual).intersection(F1010_M3_ALLOWED_STATUSES)
            touched_f1010_m3_reader = set(actual).intersection(F1010_M3_READER_ALLOWED_STATUSES)
            touched_f1010_m3_rotation = set(actual).intersection(F1010_M3_ROTATION_ALLOWED_STATUSES)
            touched_f1010_m3_preflight_payload = set(actual).intersection(
                F1010_M3_PREFLIGHT_PAYLOAD_ALLOWED_STATUSES
            )
            touched_f1010_m3_preflight_evidence = set(actual).intersection(
                F1010_M3_PREFLIGHT_EVIDENCE_ALLOWED_STATUSES
            )
            touched_f1010_m3_public_acl_v3_bound = set(actual).intersection(
                F1010_M3_PUBLIC_ACL_V3_BOUND_ALLOWED_STATUSES
            )
            touched_f1010_m3_public_acl_preflight = set(actual).intersection(
                F1010_M3_PUBLIC_ACL_PREFLIGHT_ALLOWED_STATUSES
            )
            require(
                sum(
                    bool(surface)
                    for surface in (
                        touched_p1,
                        touched_p2,
                        touched_g2,
                        touched_p5,
                        touched_f1010_m1,
                        touched_f1010_m3,
                        touched_f1010_m3_reader,
                        touched_f1010_m3_rotation,
                        touched_f1010_m3_preflight_payload,
                        touched_f1010_m3_preflight_evidence,
                        touched_f1010_m3_public_acl_v3_bound,
                        touched_f1010_m3_public_acl_preflight,
                    )
                )
                <= 1,
                "F10.9 and F10.10 protected surfaces cannot share a candidate",
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
            elif touched_f1010_m1:
                require(
                    args.head_ref == F1010_M1_HEAD_REF or args.event == "push",
                    "F10.10 M1 paths require the protected M1 branch",
                )
                require(
                    actual == F1010_M1_ALLOWED_STATUSES,
                    "partial or expanded F10.10 M1 delta is forbidden",
                )
                mode = "f1010_m1"
            elif touched_f1010_m3_rotation:
                require(
                    args.head_ref == F1010_M3_ROTATION_HEAD_REF or args.event == "push",
                    "F10.10 M3 rotation paths require the protected rotation branch",
                )
                require(
                    actual == F1010_M3_ROTATION_ALLOWED_STATUSES,
                    "partial or expanded F10.10 M3 rotation delta is forbidden",
                )
                mode = "f1010_m3_rotation"
            elif touched_f1010_m3_preflight_payload:
                require(
                    args.head_ref == F1010_M3_PREFLIGHT_PAYLOAD_HEAD_REF
                    or args.event == "push",
                    "F10.10 M3 preflight payload paths require the protected payload branch",
                )
                require(
                    actual == F1010_M3_PREFLIGHT_PAYLOAD_ALLOWED_STATUSES,
                    "partial or expanded F10.10 M3 preflight payload delta is forbidden",
                )
                mode = "f1010_m3_preflight_payload"
            elif touched_f1010_m3_preflight_evidence:
                require(
                    args.head_ref == F1010_M3_PREFLIGHT_EVIDENCE_HEAD_REF
                    or args.event == "push",
                    "F10.10 M3 preflight evidence paths require the protected evidence branch",
                )
                require(
                    actual == F1010_M3_PREFLIGHT_EVIDENCE_ALLOWED_STATUSES,
                    "partial or expanded F10.10 M3 preflight evidence delta is forbidden",
                )
                mode = "f1010_m3_preflight_evidence"
            elif touched_f1010_m3_public_acl_v3_bound:
                require(
                    args.head_ref == F1010_M3_PUBLIC_ACL_V3_BOUND_HEAD_REF
                    or args.event == "push",
                    "F10.10 M3 PUBLIC ACL v3 bound paths require the protected binding branch",
                )
                require(
                    actual == F1010_M3_PUBLIC_ACL_V3_BOUND_ALLOWED_STATUSES,
                    "partial or expanded F10.10 M3 PUBLIC ACL v3 bound delta is forbidden",
                )
                mode = "f1010_m3_public_acl_v3_bound"
            elif touched_f1010_m3_public_acl_preflight:
                require(
                    args.head_ref == F1010_M3_PUBLIC_ACL_PREFLIGHT_HEAD_REF
                    or args.event == "push",
                    "F10.10 M3 PUBLIC ACL preflight paths require the protected preflight branch",
                )
                require(
                    actual == F1010_M3_PUBLIC_ACL_PREFLIGHT_ALLOWED_STATUSES,
                    "partial or expanded F10.10 M3 PUBLIC ACL preflight delta is forbidden",
                )
                mode = "f1010_m3_public_acl_preflight"
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
        elif mode == "f1010_m2a":
            validate_f1010_m2a_wiring(args.repo, args.base_sha, args.head_sha, args.event)
        elif mode == "p5":
            validate_p5(
                args.repo,
                args.base_sha,
                args.head_sha,
                getattr(args, "p5_base", ""),
                getattr(args, "p5_base_tree", ""),
                args.event,
            )
        elif mode == "f1010_m1":
            validate_f1010_m1(
                args.repo,
                args.base_sha,
                args.head_sha,
                getattr(args, "f1010_m1_base", ""),
                getattr(args, "f1010_m1_base_tree", ""),
                args.event,
            )
        elif mode == "f1010_m3":
            validate_f1010_m3(args.repo, args.base_sha, args.head_sha, args.event)
        elif mode == "f1010_m3_reader":
            validate_f1010_m3_reader(args.repo, args.base_sha, args.head_sha, args.event)
        elif mode == "f1010_m3_reader_post_merge":
            validate_f1010_m3_reader_post_merge(
                args.repo, args.base_sha, args.head_sha, args.event
            )
        elif mode == "f1010_m3_rotation":
            validate_f1010_m3_rotation(
                args.repo, args.base_sha, args.head_sha, args.event
            )
        elif mode == "f1010_m3_passwordless":
            validate_f1010_m3_passwordless(
                args.repo, args.base_sha, args.head_sha, args.event
            )
        elif mode == "f1010_m3_preflight_payload":
            validate_f1010_m3_preflight_payload(
                args.repo, args.base_sha, args.head_sha, args.event
            )
        elif mode == "f1010_m3_preflight_evidence":
            validate_f1010_m3_preflight_evidence(
                args.repo, args.base_sha, args.head_sha, args.event
            )
        elif mode == "f1010_m3_final_readiness":
            validate_f1010_m3_final_readiness(
                args.repo, args.base_sha, args.head_sha, args.event
            )
        elif mode == "f1010_m3_apply_projection":
            validate_f1010_m3_apply_projection(
                args.repo, args.base_sha, args.head_sha, args.event
            )
        elif mode == "f1010_m3_ddl_payload":
            validate_f1010_m3_ddl_payload(
                args.repo, args.base_sha, args.head_sha, args.event
            )
        elif mode == "f1010_m3_ddl_payload_refresh":
            validate_f1010_m3_ddl_payload_refresh(
                args.repo, args.base_sha, args.head_sha, args.event
            )
        elif mode == "f1010_m3_nullability_remediation":
            validate_f1010_m3_nullability_remediation(
                args.repo, args.base_sha, args.head_sha, args.event
            )
        elif mode == "f1010_m3_ddl_v2_payload":
            validate_f1010_m3_ddl_v2_payload(
                args.repo, args.base_sha, args.head_sha, args.event
            )
        elif mode == "f1010_m3_public_acl_rebaseline":
            validate_f1010_m3_public_acl_rebaseline(
                args.repo, args.base_sha, args.head_sha, args.event
            )
        elif mode == "f1010_m3_public_acl_v2_payload":
            validate_f1010_m3_public_acl_v2_payload(
                args.repo, args.base_sha, args.head_sha, args.event
            )
        elif mode == "f1010_m3_public_acl_v3":
            validate_f1010_m3_public_acl_v3(
                args.repo, args.base_sha, args.head_sha, args.event
            )
        elif mode == "f1010_m3_public_acl_v3_bound":
            validate_f1010_m3_public_acl_v3_bound(
                args.repo, args.base_sha, args.head_sha, args.event
            )
        elif mode == "f1010_m3_public_acl_preflight":
            validate_f1010_m3_public_acl_preflight(
                args.repo, args.base_sha, args.head_sha, args.event
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
