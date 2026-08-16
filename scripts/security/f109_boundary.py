#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import json
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
F1010_M3_PUBLIC_ACL_PREFLIGHT_POST_MERGE_BASE = "6068f2ac9ef623e06dcc23d9828980641e396c39"
F1010_M3_PUBLIC_ACL_PREFLIGHT_POST_MERGE_BASE_TREE = "6a7ebe58b0acdc79bafe8362239c797e7256e31f"
F1010_M3_PUBLIC_ACL_PREFLIGHT_POST_MERGE_HEAD_REF = (
    "docs/f10-10-m3-public-acl-preflight-post-merge"
)
F1010_M3_PUBLIC_ACL_PRIVATE_PREFLIGHT_V2_PAYLOAD_BASE = "f78713087813bea950e320bc37c55cdd36c95a70"
F1010_M3_PUBLIC_ACL_PRIVATE_PREFLIGHT_V2_PAYLOAD_BASE_TREE = "65fb4d4a54df4e4bf32955dfce0847bf03b10cc2"
F1010_M3_PUBLIC_ACL_PRIVATE_PREFLIGHT_V2_PAYLOAD_HEAD_REF = (
    "docs/f10-10-m3-public-acl-private-preflight-v2-payload"
)
F1010_M3_PUBLIC_ACL_POST_MERGE_HARNESS_BASE = "b2956820295d0476ebb0580e2363fccd3bbbfae8"
F1010_M3_PUBLIC_ACL_POST_MERGE_HARNESS_BASE_TREE = "921e6f23c522ab4d75c816040e6cf15e4c8934bb"
F1010_M3_PUBLIC_ACL_POST_MERGE_HARNESS_HEAD_REF = (
    "fix/f10-10-m3-public-acl-postmerge-harness"
)
F1010_M3_PUBLIC_ACL_V2_EVIDENCE_BASE = "89cbeda226c6e04c6c1b6e091e6b94fc36273645"
F1010_M3_PUBLIC_ACL_V2_EVIDENCE_BASE_TREE = "da92dfa4baf89cc04bc2a67c97f678f3273e152b"
F1010_M3_PUBLIC_ACL_V2_EVIDENCE_HEAD_REF = (
    "docs/f10-10-m3-public-acl-v2-post-merge-evidence"
)
F1010_M3_PUBLIC_ACL_FINAL_READINESS_BASE = "51dac8f4906725aeb9d11172e674eafb5df87b8b"
F1010_M3_PUBLIC_ACL_FINAL_READINESS_BASE_TREE = "0382efc31ea3540ac8efa82046210520cd7da1a4"
F1010_M3_PUBLIC_ACL_FINAL_READINESS_HEAD_REF = (
    "fix/f10-10-m3-public-acl-final-readiness"
)
F1010_H1_CA1_REBASELINE_BASE = "d8859a52254135561be996a706590f9a005fc7da"
F1010_H1_CA1_REBASELINE_BASE_TREE = "25a05352b0a3f1319328927539a4f32bb9af827f"
F1010_H1_CA1_REBASELINE_HEAD_REF = "docs/f10-10-h1-ca1-rebaseline"
G5_PRODUCTION_READONLY_BASE = "2c9d2438c5fc309d3692d1a1de1233e0fcc95afc"
G5_PRODUCTION_READONLY_BASE_TREE = "161a8df69bf5e527c4ba863891504551ec5f7aa7"
G5_PRODUCTION_READONLY_HEAD_REF = "feat/f10-9-g5-production-readonly"
G5_V2_ATTRIBUTION_BASE = "30f77b88778372de112c6a8fb51a1344155db025"
G5_V2_ATTRIBUTION_BASE_TREE = "b25fca6fc4e37db5b1e2c0e048748ee0ec3d839c"
G5_V2_ATTRIBUTION_HEAD_REF = "feat/f10-9-g5-v2-attribution"
G5_V2_POST_MERGE_BASE = "4bb7f6d93a269879a3d73f39a5c71919ac2ea7d5"
G5_V2_POST_MERGE_BASE_TREE = "1daedcbe9651667201214eb4388e00024fa59bf3"
G5_V2_POST_MERGE_PREVIOUS_BASE = G5_V2_ATTRIBUTION_BASE
G5_V2_POST_MERGE_CANDIDATE = "2c211cf58ed0917e3e5e1255c189dcd6ca8ef976"
G5_V2_POST_MERGE_HEAD_REF = "docs/f10-9-g5-v2-post-merge"
G5_GET_ONLY_ADAPTER_BASE = "74defb6326d8432bf790cb84b4aa549fefc425be"
G5_GET_ONLY_ADAPTER_BASE_TREE = "b9b4cc8a6f8279f898b2b8bf2a900c56a741b528"
G5_GET_ONLY_ADAPTER_PREVIOUS_BASE = "191539de71cbff95552c476463305e8d6f3e4b73"
# PR #386 is the protected base's second parent. Deployment-ready PR D is one commit.
G5_GET_ONLY_ADAPTER_CANDIDATE = "d6e4eaae058b52aacf5099c763204a1343a6eebf"
G5_GET_ONLY_ADAPTER_HEAD_REF = "feat/f10-9-g5-workflow-pr-d"
G5_GET_ONLY_ADAPTER_STATUS = "DEPLOYMENT_READY_DISABLED_NOT_CONFIGURED"
G5_GET_ONLY_ADAPTER_PREVIOUS_RESULT = (
    "MERGED_POST_MERGE_VERIFIED"
)
G5_OPERATIONAL_RUNBOOK_BASE = "bd0d82864c26755435e551b835d145b864383810"
G5_OPERATIONAL_RUNBOOK_BASE_TREE = "135af5a95237a1d4d6e1b977e8bb9ab82ac95e16"
G5_OPERATIONAL_RUNBOOK_HEAD_REF = "feat/f10-9-pr-e-reconcile-g5-runbook"
G5_OPERATIONAL_RUNBOOK_STATUS = "MERGED_POST_MERGE_VERIFIED_WITH_INFRA_RETRY"
G5_E1_HARDENING_BASE = "71d6640b990b934fa02401518650ec38dca6cae4"
G5_E1_HARDENING_BASE_TREE = "815a2316c8de67047567d89a9928576869f43c4f"
G5_E1_HARDENING_HEAD_REF = "feat/f10-9-pr-f-e1-hardening"
G5_E1_HARDENING_STATUS = "MERGED_POST_MERGE_VERIFIED"
G5_E1_READINESS_STATUS = "E1_ACCOUNT_READINESS_GO"
G5_E1_DEPLOYMENT_STOP = "E1_DEPLOYMENT_STOP_REPOSITORY_HARDENING_REQUIRED"
G5_E1_WRANGLER_COMPAT_BASE = "4bdc698cd9a8569e4e8290257effa6bc3aa3bb15"
G5_E1_WRANGLER_COMPAT_BASE_TREE = "874ccffa3db9871189ca351d88cc84e120251e95"
G5_E1_WRANGLER_COMPAT_HEAD_REF = "feat/f10-9-pr-g-wrangler-compat"
G5_E1_WRANGLER_COMPAT_STATUS = "MERGED_POST_MERGE_VERIFIED"
G5_E1_WRANGLER_STOP = "E1_DEPLOYMENT_STOP_WRANGLER_FLAG_INCOMPATIBLE"
G5_E1_WRANGLER_VERSION = "4.44.0"
G5_TRUST_LIVE_REMEDIATION_BASE = "9811b19e1527b39366e43907990c4b77d1394f75"
G5_TRUST_LIVE_REMEDIATION_BASE_TREE = "edb7c827621fce1089d636b50494405115d348a6"
G5_TRUST_LIVE_REMEDIATION_HEAD_REF = "feat/f10-9-pr-h-trust-live-remediation"
G5_TRUST_LIVE_REMEDIATION_STATUS = "MERGED_POST_MERGE_VERIFIED"
G5_E1_DEPLOYMENT_STATUS = "E1_DEPLOYMENT_PASS"
G5_E1_CREDENTIAL_ATTESTATION = "E1_CREDENTIAL_REVOKED_AND_LOCAL_REMOVED"
G5_TRUST_RUNTIME_POLICY_NAMES = (
    "G5_ALLOWED_CANDIDATE_SHA",
    "G5_ALLOWED_CANDIDATE_TREE",
    "G5_ALLOWED_WORKFLOW_BLOB_SHA",
    "G5_GITHUB_APP_INSTALLATION_ID",
    "G5_TRUST_RUNTIME_ENABLED",
)

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

F1010_M3_PUBLIC_ACL_PREFLIGHT_POST_MERGE_ALLOWED_STATUSES = {
    ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
    ".context/estado_del_proyecto.md": "M",
    ".context/operaciones/flujo_release_minimo.md": "M",
    ".context/operaciones/m3_f10_10_scope_por_ambiente_target.md": "M",
    ".context/operaciones/m3_public_db_acl_private_preflight_post_merge_evidence_2026_08_13.md": "A",
    ".context/operaciones/m3_reader_f10_10_rebaseline.md": "M",
    ".context/operaciones/plan_cierre_hito1_ca1_only.md": "M",
    ".context/operaciones/plan_remediacion_metadata_f10_10.md": "M",
    "scripts/security/f109_boundary.py": "M",
    "tests/test_fase10_9_branch_reconciliation.py": "M",
}

F1010_M3_PUBLIC_ACL_PREFLIGHT_POST_MERGE_ALLOWED_MODES = {
    path: "100644"
    for path in F1010_M3_PUBLIC_ACL_PREFLIGHT_POST_MERGE_ALLOWED_STATUSES
}
F1010_M3_PUBLIC_ACL_PREFLIGHT_POST_MERGE_TRIGGER_PATHS = {
    ".context/operaciones/m3_public_db_acl_private_preflight_post_merge_evidence_2026_08_13.md"
}

F1010_M3_PUBLIC_ACL_PRIVATE_PREFLIGHT_V2_PAYLOAD_ALLOWED_STATUSES = {
    ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
    ".context/estado_del_proyecto.md": "M",
    ".context/operaciones/flujo_release_minimo.md": "M",
    ".context/operaciones/m3_f10_10_scope_por_ambiente_target.md": "M",
    ".context/operaciones/m3_public_db_acl_private_preflight_free_v2_payload_2026_08_13.json": "A",
    ".context/operaciones/m3_reader_f10_10_rebaseline.md": "M",
    ".context/operaciones/plan_cierre_hito1_ca1_only.md": "M",
    ".context/operaciones/plan_remediacion_metadata_f10_10.md": "M",
    "scripts/security/f109_boundary.py": "M",
    "tests/test_fase10_9_branch_reconciliation.py": "M",
}
F1010_M3_PUBLIC_ACL_PRIVATE_PREFLIGHT_V2_PAYLOAD_ALLOWED_MODES = {
    path: "100644"
    for path in F1010_M3_PUBLIC_ACL_PRIVATE_PREFLIGHT_V2_PAYLOAD_ALLOWED_STATUSES
}
F1010_M3_PUBLIC_ACL_PRIVATE_PREFLIGHT_V2_PAYLOAD_TRIGGER_PATHS = {
    ".context/operaciones/m3_public_db_acl_private_preflight_free_v2_payload_2026_08_13.json"
}

F1010_M3_PUBLIC_ACL_POST_MERGE_HARNESS_ALLOWED_STATUSES = {
    ".github/workflows/f9-7-contract.yml": "M",
    "scripts/security/f109_boundary.py": "M",
    "tests/sql/run_f10_10_m3_public_db_acl_preflight_postgres17.sh": "M",
    "tests/test_f10_10_m3_public_db_acl_preflight.py": "M",
    "tests/test_f10_10_m3_reader_package.py": "M",
    "tests/test_fase10_9_branch_reconciliation.py": "M",
}
F1010_M3_PUBLIC_ACL_POST_MERGE_HARNESS_ALLOWED_MODES = {
    path: "100644" for path in F1010_M3_PUBLIC_ACL_POST_MERGE_HARNESS_ALLOWED_STATUSES
}
F1010_M3_PUBLIC_ACL_POST_MERGE_HARNESS_TRIGGER_PATHS = {
    ".github/workflows/f9-7-contract.yml",
    "tests/sql/run_f10_10_m3_public_db_acl_preflight_postgres17.sh",
}

F1010_M3_PUBLIC_ACL_V2_EVIDENCE_ALLOWED_STATUSES = {
    ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
    ".context/estado_del_proyecto.md": "M",
    ".context/operaciones/flujo_release_minimo.md": "M",
    ".context/operaciones/m3_f10_10_scope_por_ambiente_target.md": "M",
    ".context/operaciones/m3_public_db_acl_private_preflight_v2_payload_post_merge_evidence_2026_08_13.md": "A",
    ".context/operaciones/m3_reader_f10_10_rebaseline.md": "M",
    ".context/operaciones/plan_cierre_hito1_ca1_only.md": "M",
    ".context/operaciones/plan_remediacion_metadata_f10_10.md": "M",
    "scripts/security/f109_boundary.py": "M",
    "tests/test_fase10_9_branch_reconciliation.py": "M",
}
F1010_M3_PUBLIC_ACL_V2_EVIDENCE_ALLOWED_MODES = {
    path: "100644" for path in F1010_M3_PUBLIC_ACL_V2_EVIDENCE_ALLOWED_STATUSES
}
F1010_M3_PUBLIC_ACL_V2_EVIDENCE_TRIGGER_PATHS = {
    ".context/operaciones/m3_public_db_acl_private_preflight_v2_payload_post_merge_evidence_2026_08_13.md"
}

F1010_M3_PUBLIC_ACL_FINAL_READINESS_ALLOWED_STATUSES = {
    ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
    ".context/estado_del_proyecto.md": "M",
    ".context/operaciones/m3_public_db_acl_postgres_final_readiness_incident_2026_08_13.md": "A",
    "scripts/security/f109_boundary.py": "M",
    "tests/sql/f10_10_m3_postgres_final_readiness.sh": "A",
    "tests/sql/run_f10_10_m3_public_db_acl_preflight_postgres17.sh": "M",
    "tests/test_f10_10_m3_public_db_acl_preflight.py": "M",
    "tests/test_fase10_9_branch_reconciliation.py": "M",
}
F1010_M3_PUBLIC_ACL_FINAL_READINESS_ALLOWED_MODES = {
    path: "100644" for path in F1010_M3_PUBLIC_ACL_FINAL_READINESS_ALLOWED_STATUSES
}
F1010_M3_PUBLIC_ACL_FINAL_READINESS_TRIGGER_PATHS = {
    ".context/operaciones/m3_public_db_acl_postgres_final_readiness_incident_2026_08_13.md"
}

F1010_H1_CA1_REBASELINE_ALLOWED_STATUSES = {
    ".context/00_INDICE.md": "M",
    ".context/backlog_tareas/req_est_001_sprint_1/_index.md": "M",
    ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
    ".context/backlog_tareas/req_est_001_sprint_1/tarea_002_hito_2.md": "A",
    ".context/decisiones/ADR-0010_rebaseline_f10_10_metadata_remediation.md": "M",
    ".context/decisiones/ADR-0011_rebaseline_superior_hito1_ca1_f10_10_a_h2.md": "A",
    ".context/estado_del_proyecto.md": "M",
    ".context/evidencias_cliente/sprint_1/paquete_hito_001.md": "M",
    ".context/evidencias_cliente/sprint_1/registro_observacion_production_f10_9_2026-08-09.md": "M",
    ".context/hitos/hito_001.md": "M",
    ".context/hitos/hito_002.md": "A",
    ".context/operaciones/flujo_release_minimo.md": "M",
    ".context/operaciones/incidente_f10_9_fg2_fg3_2026-08-09.md": "M",
    ".context/operaciones/plan_cierre_hito1_ca1_only.md": "M",
    ".context/operaciones/plan_remediacion_f10_9_fg2_fg3.md": "M",
    ".context/operaciones/plan_remediacion_metadata_f10_10.md": "M",
    ".context/operaciones/rebaseline_f10_10_h1_h2_ca2_2026_08_13.md": "A",
    "scripts/security/f109_boundary.py": "M",
    "tests/test_fase10_9_branch_reconciliation.py": "M",
}
F1010_H1_CA1_REBASELINE_ALLOWED_MODES = {
    path: "100644" for path in F1010_H1_CA1_REBASELINE_ALLOWED_STATUSES
}

G5_PRODUCTION_READONLY_ALLOWED_STATUSES = {
    ".gitignore": "M",
    ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
    ".context/estado_del_proyecto.md": "M",
    ".context/operaciones/g5_production_readonly_candidate_2026_08_14.md": "A",
    ".context/operaciones/plan_remediacion_f10_9_fg2_fg3.md": "M",
    "scripts/security/f109_boundary.py": "M",
    "scripts/shared/f10_9_g5_readonly_collector.py": "A",
    "tests/test_fase10_9_branch_reconciliation.py": "M",
    "tests/test_fase10_9_g5_production_readonly.py": "A",
}
G5_PRODUCTION_READONLY_ALLOWED_MODES = {
    path: "100644" for path in G5_PRODUCTION_READONLY_ALLOWED_STATUSES
}

G5_V2_ATTRIBUTION_ALLOWED_STATUSES = {
    ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
    ".context/estado_del_proyecto.md": "M",
    ".context/operaciones/g5_production_readonly_candidate_2026_08_14.md": "M",
    ".context/operaciones/g5_v2_repository_only_candidate_2026_08_14.md": "A",
    ".context/operaciones/plan_remediacion_f10_9_fg2_fg3.md": "M",
    "scripts/security/f109_boundary.py": "M",
    "scripts/shared/f10_9_g5_readonly_collector.py": "M",
    "tests/test_fase10_9_branch_reconciliation.py": "M",
    "tests/test_fase10_9_g5_production_readonly.py": "M",
}
G5_V2_ATTRIBUTION_ALLOWED_MODES = {
    path: "100644" for path in G5_V2_ATTRIBUTION_ALLOWED_STATUSES
}
G5_V2_POST_MERGE_ALLOWED_STATUSES = {
    ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
    ".context/estado_del_proyecto.md": "M",
    ".context/operaciones/g5_v2_repository_only_candidate_2026_08_14.md": "M",
    ".context/operaciones/plan_remediacion_f10_9_fg2_fg3.md": "M",
    "scripts/security/f109_boundary.py": "M",
    "tests/test_fase10_9_branch_reconciliation.py": "M",
}
G5_V2_POST_MERGE_ALLOWED_MODES = {
    path: "100644" for path in G5_V2_POST_MERGE_ALLOWED_STATUSES
}
G5_GET_ONLY_ADAPTER_ALLOWED_STATUSES = {
    ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
    ".context/decisiones/ADR-0015_g5_deployment_ready_disabled.md": "A",
    ".context/estado_del_proyecto.md": "M",
    ".context/operaciones/g5_get_only_adapter_contract_2026_08_14.md": "M",
    ".context/operaciones/plan_remediacion_f10_9_fg2_fg3.md": "M",
    ".github/workflows/f9-7-contract.yml": "M",
    ".github/workflows/g5-manual-trust-gate.yml": "M",
    "scripts/security/f109_boundary.py": "M",
    "scripts/shared/f10_9_g5_get_only_adapter_contract.py": "M",
    "scripts/shared/f10_9_g5_readonly_collector.py": "M",
    "tests/test_fase10_9_branch_reconciliation.py": "M",
    "tests/test_fase10_9_g5_get_only_adapter_contract.py": "M",
    "tests/test_fase10_9_g5_production_readonly.py": "M",
    "workers/g5-trust-broker/src/index.mjs": "M",
    "workers/g5-trust-broker/test/trust-broker.test.mjs": "M",
}
G5_GET_ONLY_ADAPTER_ALLOWED_MODES = {
    path: "100644" for path in G5_GET_ONLY_ADAPTER_ALLOWED_STATUSES
}

G5_OPERATIONAL_RUNBOOK_ALLOWED_STATUSES = {
    ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
    ".context/decisiones/ADR-0016_g5_operational_activation_gates.md": "A",
    ".context/estado_del_proyecto.md": "M",
    ".context/operaciones/g5_get_only_adapter_contract_2026_08_14.md": "M",
    ".context/operaciones/g5_operational_activation_manifest_2026_08_15.json": "A",
    ".context/operaciones/g5_operational_activation_runbook_2026_08_15.md": "A",
    ".context/operaciones/plan_remediacion_f10_9_fg2_fg3.md": "M",
    ".github/workflows/f9-7-contract.yml": "M",
    "scripts/security/f109_boundary.py": "M",
    "scripts/shared/f10_9_g5_operational_activation_preflight.py": "A",
    "tests/test_fase10_9_branch_reconciliation.py": "M",
    "tests/test_fase10_9_g5_operational_activation_preflight.py": "A",
}
G5_OPERATIONAL_RUNBOOK_ALLOWED_MODES = {
    path: "100644" for path in G5_OPERATIONAL_RUNBOOK_ALLOWED_STATUSES
}

G5_E1_HARDENING_ALLOWED_STATUSES = {
    ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
    ".context/decisiones/ADR-0016_g5_operational_activation_gates.md": "M",
    ".context/decisiones/ADR-0017_g5_e1_cloudflare_deployment_hardening.md": "A",
    ".context/estado_del_proyecto.md": "M",
    ".context/operaciones/g5_operational_activation_manifest_2026_08_15.json": "M",
    ".context/operaciones/g5_operational_activation_runbook_2026_08_15.md": "M",
    ".context/operaciones/plan_remediacion_f10_9_fg2_fg3.md": "M",
    ".github/workflows/f9-7-contract.yml": "M",
    "scripts/security/f109_boundary.py": "M",
    "scripts/shared/f10_9_g5_operational_activation_preflight.py": "M",
    "tests/test_fase10_9_branch_reconciliation.py": "M",
    "tests/test_fase10_9_g5_e1_hardening.py": "A",
    "tests/test_fase10_9_g5_operational_activation_preflight.py": "M",
    "workers/g5-trust-broker/package-lock.json": "A",
    "workers/g5-trust-broker/package.json": "A",
    "workers/g5-trust-broker/wrangler.repository-only.jsonc": "M",
}
G5_E1_HARDENING_ALLOWED_MODES = {
    path: "100644" for path in G5_E1_HARDENING_ALLOWED_STATUSES
}

G5_E1_WRANGLER_COMPAT_ALLOWED_STATUSES = {
    ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
    ".context/decisiones/ADR-0016_g5_operational_activation_gates.md": "M",
    ".context/decisiones/ADR-0017_g5_e1_cloudflare_deployment_hardening.md": "M",
    ".context/estado_del_proyecto.md": "M",
    ".context/operaciones/g5_operational_activation_manifest_2026_08_15.json": "M",
    ".context/operaciones/g5_operational_activation_runbook_2026_08_15.md": "M",
    ".context/operaciones/plan_remediacion_f10_9_fg2_fg3.md": "M",
    ".github/workflows/f9-7-contract.yml": "M",
    "scripts/security/f109_boundary.py": "M",
    "scripts/shared/f10_9_g5_operational_activation_preflight.py": "M",
    "tests/test_fase10_9_branch_reconciliation.py": "M",
    "tests/test_fase10_9_g5_e1_hardening.py": "M",
    "tests/test_fase10_9_g5_operational_activation_preflight.py": "M",
    "workers/g5-trust-broker/package-lock.json": "M",
    "workers/g5-trust-broker/package.json": "M",
    "workers/g5-trust-broker/test/block-egress.mjs": "A",
}
G5_E1_WRANGLER_COMPAT_ALLOWED_MODES = {
    path: "100644" for path in G5_E1_WRANGLER_COMPAT_ALLOWED_STATUSES
}

G5_TRUST_LIVE_REMEDIATION_ALLOWED_STATUSES = {
    ".context/00_INDICE.md": "M",
    ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
    ".context/decisiones/ADR-0016_g5_operational_activation_gates.md": "M",
    ".context/decisiones/ADR-0018_g5_trust_live_remediation_repository_only.md": "A",
    ".context/estado_del_proyecto.md": "M",
    ".context/operaciones/g5_get_only_adapter_contract_2026_08_14.md": "M",
    ".context/operaciones/g5_operational_activation_manifest_2026_08_15.json": "M",
    ".context/operaciones/g5_operational_activation_runbook_2026_08_15.md": "M",
    ".context/operaciones/plan_remediacion_f10_9_fg2_fg3.md": "M",
    ".github/workflows/f9-7-contract.yml": "M",
    ".github/workflows/g5-manual-trust-gate.yml": "M",
    "scripts/security/f109_boundary.py": "M",
    "scripts/shared/f10_9_g5_get_only_adapter_contract.py": "M",
    "scripts/shared/f10_9_g5_operational_activation_preflight.py": "M",
    "tests/test_fase10_9_branch_reconciliation.py": "M",
    "tests/test_fase10_9_g5_e1_hardening.py": "M",
    "tests/test_fase10_9_g5_get_only_adapter_contract.py": "M",
    "tests/test_fase10_9_g5_operational_activation_preflight.py": "M",
    "workers/g5-trust-broker/src/index.mjs": "M",
    "workers/g5-trust-broker/test/trust-broker.test.mjs": "M",
}
G5_TRUST_LIVE_REMEDIATION_ALLOWED_MODES = {
    path: "100644" for path in G5_TRUST_LIVE_REMEDIATION_ALLOWED_STATUSES
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


def validate_f1010_m3_public_acl_preflight_post_merge(
    repo: Path, base: str, head: str, event: str,
) -> None:
    require(
        base == F1010_M3_PUBLIC_ACL_PREFLIGHT_POST_MERGE_BASE,
        "unexpected M3 PUBLIC ACL preflight post-merge baseline",
    )
    require_sha(repo, "F1010_M3_PUBLIC_ACL_PREFLIGHT_POST_MERGE_BASE", base)
    require_sha(repo, "head", head)
    require(
        commit_tree(repo, base) == F1010_M3_PUBLIC_ACL_PREFLIGHT_POST_MERGE_BASE_TREE,
        "M3 PUBLIC ACL preflight post-merge base tree drift",
    )
    require(is_ancestor(repo, base, head), "M3 PUBLIC ACL preflight post-merge base is not ancestor")
    candidate_head = head
    if event == "push":
        parents = commit_parents(repo, head)
        require(
            len(parents) == 2 and parents[0] == base,
            "M3 PUBLIC ACL preflight post-merge push must be a protected merge",
        )
        candidate_head = parents[1]
        require(
            commit_tree(repo, head) == commit_tree(repo, candidate_head),
            "M3 PUBLIC ACL preflight post-merge push tree drift",
        )
    require(
        commit_parents(repo, candidate_head) == [base],
        "M3 PUBLIC ACL preflight post-merge candidate must contain one direct commit",
    )
    require_exact_delta(
        repo,
        base,
        candidate_head,
        F1010_M3_PUBLIC_ACL_PREFLIGHT_POST_MERGE_ALLOWED_STATUSES,
        F1010_M3_PUBLIC_ACL_PREFLIGHT_POST_MERGE_ALLOWED_MODES,
    )
    validate_context_graph(repo, 58, 377)


def validate_f1010_m3_public_acl_private_preflight_v2_payload(
    repo: Path, base: str, head: str, event: str,
) -> None:
    require(
        base == F1010_M3_PUBLIC_ACL_PRIVATE_PREFLIGHT_V2_PAYLOAD_BASE,
        "unexpected M3 PUBLIC ACL private preflight v2 payload baseline",
    )
    require_sha(repo, "F1010_M3_PUBLIC_ACL_PRIVATE_PREFLIGHT_V2_PAYLOAD_BASE", base)
    require_sha(repo, "head", head)
    require(
        commit_tree(repo, base) == F1010_M3_PUBLIC_ACL_PRIVATE_PREFLIGHT_V2_PAYLOAD_BASE_TREE,
        "M3 PUBLIC ACL private preflight v2 payload base tree drift",
    )
    require(is_ancestor(repo, base, head), "M3 PUBLIC ACL private preflight v2 payload ancestry drift")
    candidate_head = head
    if event == "push":
        parents = commit_parents(repo, head)
        require(
            len(parents) == 2 and parents[0] == base,
            "M3 PUBLIC ACL private preflight v2 payload push must be a protected merge",
        )
        candidate_head = parents[1]
        require(
            commit_tree(repo, head) == commit_tree(repo, candidate_head),
            "M3 PUBLIC ACL private preflight v2 payload merge tree drift",
        )
    require(
        commit_parents(repo, candidate_head) == [base],
        "M3 PUBLIC ACL private preflight v2 payload must contain one direct commit",
    )
    require_exact_delta(
        repo,
        base,
        candidate_head,
        F1010_M3_PUBLIC_ACL_PRIVATE_PREFLIGHT_V2_PAYLOAD_ALLOWED_STATUSES,
        F1010_M3_PUBLIC_ACL_PRIVATE_PREFLIGHT_V2_PAYLOAD_ALLOWED_MODES,
    )
    payload_path = (
        repo
        / ".context/operaciones/m3_public_db_acl_private_preflight_free_v2_payload_2026_08_13.json"
    )
    raw = payload_path.read_bytes()
    payload = json.loads(raw)
    require(
        set(payload) == {
            "application_rows_allowed", "authority_commit", "authority_head_commit",
            "authority_parent", "authority_pr", "authority_tree", "automatic_continuation",
            "automatic_retry", "candidate_merge_commit", "candidate_tree",
            "collector_result_schema", "collector_sql_digest", "database_classes",
            "ddl_allowed", "dml_allowed", "expected_rows", "gate",
            "managed_dependency_attestation_schema", "max_calls",
            "observed_transport_schema", "password_allowed", "post_merge_checks",
            "postgres_major_required", "private_artifact_schema",
            "private_dependency_attestation_path", "private_env_path",
            "private_result_path", "private_target_binding_path", "pro_allowed",
            "q0_allowed", "reader_required", "remediation_allowed", "remote_read_scope",
            "rpc_allowed", "sanitized_manifest_schema", "schema", "status",
            "target_alias", "target_binding_schema", "transaction",
        },
        "M3 PUBLIC ACL private preflight v2 payload shape drift",
    )
    require(
        raw
        == json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        ).encode("ascii")
        + b"\n",
        "M3 PUBLIC ACL private preflight v2 payload is not canonical JSON",
    )
    require(
        payload.get("schema") == "f10.10-m3-public-db-acl-private-preflight-payload-v2"
        and payload.get("gate")
        == "APPROVE_F10_10_M3_PUBLIC_DB_ACL_PRIVATE_PREFLIGHT_FREE_V2"
        and payload.get("authority_commit") == base
        and payload.get("authority_tree")
        == F1010_M3_PUBLIC_ACL_PRIVATE_PREFLIGHT_V2_PAYLOAD_BASE_TREE
        and payload.get("authority_pr") == 370
        and payload.get("authority_head_commit")
        == "f6e34a7211ac7bd54c7242d65e9ed2d721d544a3"
        and payload.get("authority_parent")
        == "6068f2ac9ef623e06dcc23d9828980641e396c39"
        and payload.get("candidate_merge_commit") is None
        and payload.get("candidate_tree") is None,
        "M3 PUBLIC ACL private preflight v2 payload authority drift",
    )
    require(
        payload.get("collector_sql_digest")
        == "sha256:c109752ce46d3528920527ea034c929ff4e4e6b477576c1fa7514b3fe26f3d35"
        and payload.get("target_binding_schema") == "f10.10-m3-target-binding-v2"
        and payload.get("observed_transport_schema")
        == "f10.10-m3-observed-transport-v2"
        and payload.get("collector_result_schema")
        == "f10.10-m3-public-db-acl-private-result-v1"
        and payload.get("managed_dependency_attestation_schema")
        == "f10.10-m3-managed-dependency-attestation-v1"
        and payload.get("private_artifact_schema")
        == "f10.10-m3-public-db-acl-private-artifact-v1"
        and payload.get("sanitized_manifest_schema")
        == "f10.10-m3-public-db-acl-sanitized-manifest-v1"
        and payload.get("private_env_path") == "local/f10_10/m3/preflight.env"
        and payload.get("private_target_binding_path")
        == "local/f10_10/m3/public-db-acl-target-binding-v2.json"
        and payload.get("private_dependency_attestation_path")
        == "local/f10_10/m3/public-db-acl-managed-dependency-attestation-v1.json"
        and payload.get("private_result_path")
        == "local/f10_10/m3/public-db-acl-private-result-v1.json"
        and payload.get("transaction") == "REPEATABLE_READ_READ_ONLY"
        and payload.get("target_alias") == "FREE_DB"
        and payload.get("max_calls") == 1
        and payload.get("expected_rows") == 1,
        "M3 PUBLIC ACL private preflight v2 payload contract drift",
    )
    require(
        payload.get("application_rows_allowed") == 0
        and payload.get("postgres_major_required") == 17
        and payload.get("database_classes")
        == ["TARGET", "OTHER_CONNECTABLE", "NON_CONNECTABLE"]
        and payload.get("post_merge_checks")
        == [
            {"conclusion": "success", "name": "Security Audit Gate", "run_id": 31707738912},
            {
                "conclusion": "success",
                "name": "F9.7 Public Access, Trigger Retirement, and Security Hold PostgreSQL 17 Contract",
                "run_id": 31707738896,
            },
        ]
        and payload.get("status")
        == "PENDING_CANONICAL_TARGET_AND_OBSERVED_TRANSPORT_BINDING_HUMAN_APPROVAL_NOT_EXECUTED",
        "M3 PUBLIC ACL private preflight v2 payload evidence drift",
    )
    for field in (
        "automatic_continuation", "automatic_retry", "ddl_allowed", "dml_allowed",
        "password_allowed", "pro_allowed", "q0_allowed", "reader_required",
        "remediation_allowed", "rpc_allowed",
    ):
        require(payload.get(field) is False, f"M3 PUBLIC ACL private preflight v2 enables {field}")
    validate_context_graph(repo, 58, 377)


def validate_f1010_m3_public_acl_post_merge_harness(
    repo: Path, base: str, head: str, event: str,
) -> None:
    require(
        base == F1010_M3_PUBLIC_ACL_POST_MERGE_HARNESS_BASE,
        "unexpected M3 PUBLIC ACL post-merge harness baseline",
    )
    require_sha(repo, "F1010_M3_PUBLIC_ACL_POST_MERGE_HARNESS_BASE", base)
    require_sha(repo, "head", head)
    require(
        commit_tree(repo, base) == F1010_M3_PUBLIC_ACL_POST_MERGE_HARNESS_BASE_TREE,
        "M3 PUBLIC ACL post-merge harness base tree drift",
    )
    require(is_ancestor(repo, base, head), "M3 PUBLIC ACL post-merge harness ancestry drift")
    candidate_head = head
    if event == "push":
        parents = commit_parents(repo, head)
        require(
            len(parents) == 2 and parents[0] == base,
            "M3 PUBLIC ACL post-merge harness push must be a protected merge",
        )
        candidate_head = parents[1]
        require(
            commit_tree(repo, head) == commit_tree(repo, candidate_head),
            "M3 PUBLIC ACL post-merge harness merge tree drift",
        )
    require(
        commit_parents(repo, candidate_head) == [base],
        "M3 PUBLIC ACL post-merge harness must contain one direct commit",
    )
    require_exact_delta(
        repo,
        base,
        candidate_head,
        F1010_M3_PUBLIC_ACL_POST_MERGE_HARNESS_ALLOWED_STATUSES,
        F1010_M3_PUBLIC_ACL_POST_MERGE_HARNESS_ALLOWED_MODES,
    )


def validate_f1010_m3_public_acl_v2_evidence(
    repo: Path, base: str, head: str, event: str,
) -> None:
    require(base == F1010_M3_PUBLIC_ACL_V2_EVIDENCE_BASE, "unexpected M3 PUBLIC ACL v2 evidence baseline")
    require_sha(repo, "F1010_M3_PUBLIC_ACL_V2_EVIDENCE_BASE", base)
    require_sha(repo, "head", head)
    require(
        commit_tree(repo, base) == F1010_M3_PUBLIC_ACL_V2_EVIDENCE_BASE_TREE,
        "M3 PUBLIC ACL v2 evidence base tree drift",
    )
    require(is_ancestor(repo, base, head), "M3 PUBLIC ACL v2 evidence ancestry drift")
    candidate_head = head
    if event == "push":
        parents = commit_parents(repo, head)
        require(
            len(parents) == 2 and parents[0] == base,
            "M3 PUBLIC ACL v2 evidence push must be a protected merge",
        )
        candidate_head = parents[1]
        require(
            commit_tree(repo, head) == commit_tree(repo, candidate_head),
            "M3 PUBLIC ACL v2 evidence merge tree drift",
        )
    require(
        commit_parents(repo, candidate_head) == [base],
        "M3 PUBLIC ACL v2 evidence must contain one direct commit",
    )
    require_exact_delta(
        repo, base, candidate_head,
        F1010_M3_PUBLIC_ACL_V2_EVIDENCE_ALLOWED_STATUSES,
        F1010_M3_PUBLIC_ACL_V2_EVIDENCE_ALLOWED_MODES,
    )
    evidence = (
        repo
        / ".context/operaciones/m3_public_db_acl_private_preflight_v2_payload_post_merge_evidence_2026_08_13.md"
    ).read_text(encoding="utf-8")
    for required in (
        "M3_PUBLIC_DB_ACL_PRIVATE_PREFLIGHT_FREE_V2_PAYLOAD_POST_MERGE_VERIFIED_CONSUMER_BINDING_REQUIRED",
        "payload_merge = b2956820295d0476ebb0580e2363fccd3bbbfae8",
        "payload_post_merge_f9_7 = 31716674957:FAIL_CLOSED",
        "harness_merge = 89cbeda226c6e04c6c1b6e091e6b94fc36273645",
        "harness_merge_tree = da92dfa4baf89cc04bc2a67c97f678f3273e152b",
        "harness_post_merge_security_audit = 31720301586:PASS",
        "harness_post_merge_f9_7 = 31720301577:PASS",
        "CONSUMER_BINDING = REQUIRED_NOT_IMPLEMENTED",
        "PROPOSED_NOT_CREATED_NOT_APPROVED_NOT_CONSUMED",
        "M4_M10 = NOT_AUTHORIZED",
    ):
        require(required in evidence, "M3 PUBLIC ACL v2 evidence contract drift")
    validate_context_graph(repo, 59, 378)


def validate_f1010_m3_public_acl_final_readiness(
    repo: Path, base: str, head: str, event: str,
) -> None:
    require(base == F1010_M3_PUBLIC_ACL_FINAL_READINESS_BASE, "unexpected M3 PUBLIC ACL final readiness baseline")
    require_sha(repo, "F1010_M3_PUBLIC_ACL_FINAL_READINESS_BASE", base)
    require_sha(repo, "head", head)
    require(
        commit_tree(repo, base) == F1010_M3_PUBLIC_ACL_FINAL_READINESS_BASE_TREE,
        "M3 PUBLIC ACL final readiness base tree drift",
    )
    require(is_ancestor(repo, base, head), "M3 PUBLIC ACL final readiness ancestry drift")
    candidate_head = head
    if event == "push":
        parents = commit_parents(repo, head)
        require(
            len(parents) == 2 and parents[0] == base,
            "M3 PUBLIC ACL final readiness push must be a protected merge",
        )
        candidate_head = parents[1]
        require(
            commit_tree(repo, head) == commit_tree(repo, candidate_head),
            "M3 PUBLIC ACL final readiness merge tree drift",
        )
    require(
        commit_parents(repo, candidate_head) == [base],
        "M3 PUBLIC ACL final readiness must contain one direct commit",
    )
    require_exact_delta(
        repo, base, candidate_head,
        F1010_M3_PUBLIC_ACL_FINAL_READINESS_ALLOWED_STATUSES,
        F1010_M3_PUBLIC_ACL_FINAL_READINESS_ALLOWED_MODES,
    )
    incident = (
        repo / ".context/operaciones/m3_public_db_acl_postgres_final_readiness_incident_2026_08_13.md"
    ).read_text(encoding="utf-8")
    helper = (repo / "tests/sql/f10_10_m3_postgres_final_readiness.sh").read_text(encoding="utf-8")
    for required in (
        "31724004476", "FAIL_CLOSED_LOCAL_POSTGRES_INIT_RACE", "34_PASS",
        "REQUIRED_NOT_IMPLEMENTED", "NOT_CREATED_NOT_APPROVED_NOT_CONSUMED",
    ):
        require(required in incident, "M3 PUBLIC ACL final readiness incident drift")
    for required in (
        "PostgreSQL init process complete; ready for start up.",
        "/var/run/postgresql/.s.PGSQL.5432", "stable_probes=0",
        "stable_probes=$((stable_probes + 1))", 'if [ "$stable_probes" -eq 3 ]',
    ):
        require(required in helper, "M3 PUBLIC ACL final readiness helper drift")
    validate_context_graph(repo, 60, 378)


def validate_f1010_h1_ca1_rebaseline(
    repo: Path, base: str, head: str, event: str,
) -> None:
    require(
        base == F1010_H1_CA1_REBASELINE_BASE,
        "unexpected F10.10 Hito 1 CA1 rebaseline base",
    )
    require_sha(repo, "F1010_H1_CA1_REBASELINE_BASE", base)
    require_sha(repo, "head", head)
    require(
        commit_tree(repo, base) == F1010_H1_CA1_REBASELINE_BASE_TREE,
        "F10.10 Hito 1 CA1 rebaseline base tree drift",
    )
    candidate_head = head
    if event == "push":
        parents = commit_parents(repo, head)
        require(
            len(parents) == 2 and parents[0] == base,
            "F10.10 Hito 1 CA1 rebaseline push must be a protected merge",
        )
        candidate_head = parents[1]
        require(
            commit_tree(repo, head) == commit_tree(repo, candidate_head),
            "F10.10 Hito 1 CA1 rebaseline merge tree drift",
        )
    require(
        is_ancestor(repo, base, candidate_head),
        "F10.10 Hito 1 CA1 rebaseline base is not an ancestor of head",
    )
    require_exact_delta(
        repo,
        base,
        candidate_head,
        F1010_H1_CA1_REBASELINE_ALLOWED_STATUSES,
        F1010_H1_CA1_REBASELINE_ALLOWED_MODES,
    )
    validate_context_graph(repo, 64, 391)


def validate_g5_production_readonly(
    repo: Path, base: str, head: str, event: str,
) -> None:
    require(
        base == G5_PRODUCTION_READONLY_BASE,
        "unexpected G5 Production read-only base",
    )
    require_sha(repo, "G5_PRODUCTION_READONLY_BASE", base)
    require_sha(repo, "head", head)
    require(
        commit_tree(repo, base) == G5_PRODUCTION_READONLY_BASE_TREE,
        "G5 Production read-only base tree drift",
    )
    candidate_head = head
    if event == "push":
        parents = commit_parents(repo, head)
        require(
            len(parents) == 2 and parents[0] == base,
            "G5 Production read-only push must be a protected merge",
        )
        candidate_head = parents[1]
        require(
            commit_tree(repo, head) == commit_tree(repo, candidate_head),
            "G5 Production read-only merge tree drift",
        )
    else:
        require(
            commit_parents(repo, head) == [base],
            "G5 Production read-only candidate must be one direct commit",
        )
    require(
        is_ancestor(repo, base, candidate_head),
        "G5 Production read-only base is not an ancestor of head",
    )
    require_exact_delta(
        repo,
        base,
        candidate_head,
        G5_PRODUCTION_READONLY_ALLOWED_STATUSES,
        G5_PRODUCTION_READONLY_ALLOWED_MODES,
    )
    collector = (
        repo / "scripts/shared/f10_9_g5_readonly_collector.py"
    ).read_text(encoding="utf-8")
    evidence = (
        repo / ".context/operaciones/g5_production_readonly_candidate_2026_08_14.md"
    ).read_text(encoding="utf-8")
    for forbidden in (
        "f10_9_metadata_planner",
        "select_all_service",
        "select_all_pipeline",
        "patch_exact_one_raise",
    ):
        require(forbidden not in collector, "G5 collector capability drift")
    for required in (
        "APPROVE_F10_9_G5_PRODUCTION_READONLY_DIAGNOSTIC_V1",
        "NOT_CREATED_NOT_APPROVED_NOT_CONSUMED",
        "BLOCKED_BEFORE_NETWORK",
        "STOP_G5_SNAPSHOT_DRIFT",
        "31768101859=PASS",
        "31768101887=PASS",
    ):
        require(required in evidence, "G5 repository-only evidence drift")
    validate_context_graph(repo, 65, 400)


def validate_g5_v2_attribution(
    repo: Path, base: str, head: str, event: str,
) -> None:
    require(base == G5_V2_ATTRIBUTION_BASE, "unexpected G5 v2 attribution base")
    require_sha(repo, "G5_V2_ATTRIBUTION_BASE", base)
    require_sha(repo, "head", head)
    require(
        commit_tree(repo, base) == G5_V2_ATTRIBUTION_BASE_TREE,
        "G5 v2 attribution base tree drift",
    )
    candidate_head = head
    if event == "push":
        parents = commit_parents(repo, head)
        require(
            len(parents) == 2 and parents[0] == base,
            "G5 v2 attribution push must be a protected merge",
        )
        candidate_head = parents[1]
        require(
            commit_tree(repo, head) == commit_tree(repo, candidate_head),
            "G5 v2 attribution merge tree drift",
        )
    else:
        require(
            commit_parents(repo, head) == [base],
            "G5 v2 attribution candidate must be one direct commit",
        )
    require(
        is_ancestor(repo, base, candidate_head),
        "G5 v2 attribution base is not an ancestor of head",
    )
    require_exact_delta(
        repo,
        base,
        candidate_head,
        G5_V2_ATTRIBUTION_ALLOWED_STATUSES,
        G5_V2_ATTRIBUTION_ALLOWED_MODES,
    )
    collector = (
        repo / "scripts/shared/f10_9_g5_readonly_collector.py"
    ).read_text(encoding="utf-8")
    evidence = (
        repo / ".context/operaciones/g5_v2_repository_only_candidate_2026_08_14.md"
    ).read_text(encoding="utf-8")
    for forbidden in (
        "f10_9_metadata_planner",
        "select_all_service",
        "select_all_pipeline",
        "patch_exact_one_raise",
        "db_client",
        "safe_http",
        "import requests",
        "import httpx",
        "import socket",
        "import urllib",
        "import subprocess",
        "import supabase",
        "import importlib",
        "eval(",
        "exec(",
    ):
        require(forbidden not in collector, "G5 v2 collector capability drift")
    for required in (
        "f10.9-g5-production-readonly-projection.v2",
        "STOP_G5_CONNECTED_MODE_NOT_IMPLEMENTED",
        "NOT_CREATED_NOT_APPROVED_NOT_CONSUMED",
        "30f77b88778372de112c6a8fb51a1344155db025",
        "31771823387=PASS",
        "31771823386=PASS",
    ):
        require(required in evidence, "G5 v2 repository-only evidence drift")
    validate_context_graph(repo, 66, 403)


def validate_g5_v2_post_merge(
    repo: Path, base: str, head: str, event: str,
) -> None:
    require(base == G5_V2_POST_MERGE_BASE, "unexpected G5 v2 post-merge base")
    require_sha(repo, "G5_V2_POST_MERGE_BASE", base)
    require_sha(repo, "G5_V2_POST_MERGE_CANDIDATE", G5_V2_POST_MERGE_CANDIDATE)
    require_sha(repo, "head", head)
    require(
        commit_tree(repo, base) == G5_V2_POST_MERGE_BASE_TREE,
        "G5 v2 post-merge base tree drift",
    )
    require(
        commit_parents(repo, base)
        == [G5_V2_POST_MERGE_PREVIOUS_BASE, G5_V2_POST_MERGE_CANDIDATE],
        "G5 v2 protected merge parents drift",
    )
    require(
        commit_tree(repo, G5_V2_POST_MERGE_CANDIDATE)
        == G5_V2_POST_MERGE_BASE_TREE,
        "G5 v2 candidate and merge tree drift",
    )
    candidate_head = head
    if event == "push":
        parents = commit_parents(repo, head)
        require(
            len(parents) == 2 and parents[0] == base,
            "G5 v2 post-merge attestation push must be a protected merge",
        )
        candidate_head = parents[1]
        require(
            commit_tree(repo, head) == commit_tree(repo, candidate_head),
            "G5 v2 post-merge attestation merge tree drift",
        )
    else:
        require(
            commit_parents(repo, head) == [base],
            "G5 v2 post-merge attestation must be one direct commit",
        )
    require_exact_delta(
        repo,
        base,
        candidate_head,
        G5_V2_POST_MERGE_ALLOWED_STATUSES,
        G5_V2_POST_MERGE_ALLOWED_MODES,
    )
    collector = (
        repo / "scripts/shared/f10_9_g5_readonly_collector.py"
    ).read_text(encoding="utf-8")
    evidence = (
        repo / ".context/operaciones/g5_v2_repository_only_candidate_2026_08_14.md"
    ).read_text(encoding="utf-8")
    for required in (
        "COMPLETED_POST_MERGE_VERIFIED",
        G5_V2_POST_MERGE_BASE,
        G5_V2_POST_MERGE_BASE_TREE,
        G5_V2_POST_MERGE_CANDIDATE,
        "31820665170=PASS",
        "31820665257=PASS",
        "NOT_CREATED_NOT_APPROVED_NOT_CONSUMED",
        "STOP_G5_CONNECTED_MODE_NOT_IMPLEMENTED",
    ):
        require(required in evidence, "G5 v2 post-merge evidence drift")
    require(
        "STOP_G5_CONNECTED_MODE_NOT_IMPLEMENTED" in collector
        or "IMPLEMENTED_DISABLED_NOT_CONFIGURED" in collector,
        "G5 v2 connected-mode STOP drift",
    )
    validate_context_graph(repo, 66, 403)


def validate_g5_get_only_adapter(
    repo: Path, base: str, head: str, event: str,
) -> None:
    require(base == G5_GET_ONLY_ADAPTER_BASE, "unexpected G5 adapter contract base")
    require_sha(repo, "G5_GET_ONLY_ADAPTER_BASE", base)
    require_sha(repo, "G5_GET_ONLY_ADAPTER_CANDIDATE", G5_GET_ONLY_ADAPTER_CANDIDATE)
    require_sha(repo, "head", head)
    require(
        commit_tree(repo, base) == G5_GET_ONLY_ADAPTER_BASE_TREE,
        "G5 adapter contract base tree drift",
    )
    require(
        commit_parents(repo, base)
        == [G5_GET_ONLY_ADAPTER_PREVIOUS_BASE, G5_GET_ONLY_ADAPTER_CANDIDATE],
        "G5 adapter protected source parents drift",
    )
    require(
        commit_tree(repo, G5_GET_ONLY_ADAPTER_CANDIDATE)
        == G5_GET_ONLY_ADAPTER_BASE_TREE,
        "G5 adapter source candidate and merge tree drift",
    )
    candidate_head = head
    if event == "push":
        parents = commit_parents(repo, head)
        require(
            len(parents) == 2 and parents[0] == base,
            "G5 adapter contract push must be a protected merge",
        )
        candidate_head = parents[1]
        require(
            commit_tree(repo, head) == commit_tree(repo, candidate_head),
            "G5 adapter contract merge tree drift",
        )
    else:
        require(
            commit_parents(repo, head) == [base],
            "G5 adapter contract candidate must be one direct commit",
        )
    require_exact_delta(
        repo,
        base,
        candidate_head,
        G5_GET_ONLY_ADAPTER_ALLOWED_STATUSES,
        G5_GET_ONLY_ADAPTER_ALLOWED_MODES,
    )
    contract = (
        repo / "scripts/shared/f10_9_g5_get_only_adapter_contract.py"
    ).read_text(encoding="utf-8")
    collector = (
        repo / "scripts/shared/f10_9_g5_readonly_collector.py"
    ).read_text(encoding="utf-8")
    evidence = (
        repo / ".context/operaciones/g5_get_only_adapter_contract_2026_08_14.md"
    ).read_text(encoding="utf-8")
    workflow = (repo / ".github/workflows/f9-7-contract.yml").read_text(
        encoding="utf-8"
    )
    manual_workflow = (repo / ".github/workflows/g5-manual-trust-gate.yml").read_text(
        encoding="utf-8"
    )
    broker = (repo / "workers/g5-trust-broker/src/index.mjs").read_text(
        encoding="utf-8"
    )
    broker_tests = (
        repo / "workers/g5-trust-broker/test/trust-broker.test.mjs"
    ).read_text(encoding="utf-8")
    broker_config = (
        repo / "workers/g5-trust-broker/wrangler.repository-only.jsonc"
    ).read_text(encoding="utf-8")
    adr = (
        repo / ".context/decisiones/ADR-0013_trust_broker_durable_object_ledger.md"
    ).read_text(encoding="utf-8")
    adr14 = (
        repo / ".context/decisiones/ADR-0014_g5_manual_workflow_connected_adapter_disabled.md"
    ).read_text(encoding="utf-8")
    adr15 = (
        repo / ".context/decisiones/ADR-0015_g5_deployment_ready_disabled.md"
    ).read_text(encoding="utf-8")
    for forbidden in (
        "import supabase",
        "import requests",
        "import httpx",
        "import urllib",
        "import socket",
        "import subprocess",
        "db_client",
        "import psycopg",
        "import sqlalchemy",
        "os.environ",
        "getenv(",
        "create_client(",
    ):
        require(forbidden not in contract, "G5 adapter offline capability drift")
    contract_tree = ast.parse(contract)
    imported_roots: set[str] = set()
    called_names: set[str] = set()
    referenced_names: set[str] = set()
    for node in ast.walk(contract_tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called_names.add(node.func.attr)
        elif isinstance(node, ast.Name):
            referenced_names.add(node.id)
    require(
        imported_roots
        <= {
            "__future__",
            "hashlib",
            "ipaddress",
            "json",
            "re",
            "dataclasses",
            "datetime",
            "types",
            "typing",
            "urllib",
            "url_identity",
        },
        "G5 adapter import allowlist drift",
    )
    require(
        not imported_roots
        & {
            "supabase",
            "requests",
            "httpx",
            "socket",
            "subprocess",
            "psycopg",
            "sqlalchemy",
            "boto3",
            "importlib",
            "os",
        },
        "G5 adapter forbidden import capability",
    )
    require(
        not called_names
        & {
            "__import__",
            "import_module",
            "getenv",
            "open",
            "urlopen",
            "connect",
            "create_client",
            "Popen",
            "run",
            "check_call",
            "check_output",
            "eval",
            "exec",
        },
        "G5 adapter forbidden runtime capability",
    )
    require(
        not referenced_names
        & {
            "__import__",
            "import_module",
            "getattr",
            "globals",
            "locals",
            "open",
            "compile",
            "eval",
            "exec",
        },
        "G5 adapter forbidden indirect capability",
    )
    for forbidden in (
        "class GateAttestation",
        "class CredentialAvailabilityAttestation",
        "class HistoricalFG3AnchorProvider",
        "class SourceObservationProvider",
        "Protocol",
        "runtime_checkable",
        "obtain_independent_historical_anchor",
        "asdict",
        "row: Mapping",
        "SourceAttemptTiming",
    ):
        require(forbidden not in contract, "G5 adapter v1 trust surface returned")
    for required in (
        "f10.9-g5-get-only-adapter-contract.v2.3",
        "f10.9-g5-get-only-adapter-schema.v2.3",
        "f10.9-g5-get-only-adapter-v2.3",
        "ManifestBuilderEvidenceReceipt",
        "AnchorProviderEvidenceReceipt",
        "class FrozenRow",
        "class LifecycleEvidence",
        "class StaticSourceTarget",
        "class EffectiveProfileRouting",
        "class SourceAttemptResult",
        "class FG3PriorMutationEvidence",
        "SOURCE_ATTEMPT_BUDGET_NS = 15_000_000_000",
        "MAX_SOURCES_PER_PROFILE = 64",
        "MAX_PROFILE_SOURCE_PAIRS = 50_000",
        "MAX_FG3_HISTORICAL_OBSERVATIONS = 50_000",
        "SOURCE_ATTEMPT_GRAMMAR",
        'SOURCE_ROLE_PROBE_TARGET = "PROBE_TARGET"',
        'SOURCE_ROLE_TEMPLATE = "TEMPLATE"',
        'SOURCE_ROLE_FILTER = "FILTER"',
        "from .url_identity import build_url_identity",
        "import ipaddress",
        "identity = build_url_identity(value)",
        "address = ipaddress.ip_address(host)",
        "address is not None and not address.is_global",
        "return identity.canonical_url",
        "def _is_safe_profile_regex",
        "Deliberately linear subset",
        'if character in "()|*+?{}":',
        "len(pattern) > 200",
        "regex_url_text = lowered[:2000]",
        "circuit_effective_open",
        "circuit_auto_closed",
        "observed_at - parsed_circuit_opened_at < timedelta(hours=24)",
        'REDIRECT_EVIDENCE_POLICY = "NO_REDIRECT_WITHOUT_DERIVATION_EVIDENCE"',
        "expected_historical_count = 27 + max(0, len(required_inactive) - 1)",
        "len(evidence.historical_observations) != expected_historical_count",
        "any(len(items) != 1 for items in mutations_by_course.values())",
        "count > MAX_FG3_HISTORICAL_OBSERVATIONS",
        "len(manifest.category_counts) != 3",
        "_enforce_fg3_collection_limit(len(evidence.courses))",
        "_enforce_fg3_collection_limit(len(evidence.prior_mutations))",
        "len(evidence.historical_observations)",
        "if len(target_values) > MAX_SOURCES_PER_PROFILE:\n"
        "        _raise(STOP_TARGET_BINDING_INVALID)",
        "if type(count) is not int or count < 0 or count > MAX_PROFILE_SOURCE_PAIRS:\n"
        "        _raise(STOP_TARGET_BINDING_INVALID)",
        "utc_first = min(first_attempts, key=lambda item: item[1].started_at_utc)",
        "monotonic_first = min(",
        "if utc_first[0] != monotonic_first[0]",
        "routing_observed_at = utc_first[1].started_at_utc",
        "_require_complete",
        "historical_observation_fingerprint",
        "prior_mutation_fingerprint",
        "profile_source_fingerprints",
        "validate_source_coverage",
        "source_terminal_reason",
        "validate_lifecycle_evidence",
        "_STALE_AFTER = timedelta(hours=24)",
        "STOP_G5_SOURCE_BLOCKERS_PRESENT",
        "STOP_G5_LIFECYCLE_BLOCKERS_PRESENT",
        "STOP_G5_TRUST_VERIFICATION_NOT_IMPLEMENTED",
        "REPOSITORY_ONLY_TRUST_PLANE_PR_A_STOP",
        "MERGED_POST_MERGE_VERIFIED",
        "DEPLOYMENT_READY_DISABLED_NOT_CONFIGURED",
        "class GateIntent",
        "class GitHubOidcClaims",
        "class WorkflowRunEvidence",
        "class EnvironmentEvidence",
        "class ApprovalEvidence",
        "class DeploymentEvidence",
        "class GateConsumptionReceipt",
        "STOP_G5_AUTHORITY_INVALID",
        "STOP_G5_APPROVAL_INVALID",
        "STOP_G5_BINDING_DRIFT",
        "STOP_G5_REPLAY_DETECTED",
        "STOP_G5_GATE_EXPIRED",
        "STOP_G5_CONSUMPTION_AMBIGUOUS",
        "STOP_G5_ATOMIC_LEDGER_REQUIRED",
        "STOP_G5_PROOF_INVALID",
        "G5_ATOMIC_LEDGER_INTERFACE",
        "READY",
        "CONSUMED",
        "STOP_G5_SNAPSHOT_CONTENT_DRIFT",
        "CLOCK_DURATION_TOLERANCE_NS = 250_000_000",
        "MAX_IMMUTABLE_DEPTH = 8",
        "MAX_IMMUTABLE_NODES = 256",
        "MAX_IMMUTABLE_STRING_BYTES = 8_192",
        "MAX_IMMUTABLE_INTEGER_ABS = 2**63 - 1",
        "IMPLEMENTED_DISABLED_NOT_CONFIGURED",
        "NOT_CREATED_NOT_APPROVED_NOT_CONSUMED",
        G5_GET_ONLY_ADAPTER_BASE,
        G5_GET_ONLY_ADAPTER_BASE_TREE,
    ):
        require(required in contract, "G5 adapter contract drift")
    for forbidden in (
        "account_id",
        'workers_dev": true',
        "api.github.com",
        "token.actions.githubusercontent.com/.well-known",
        "postgres",
        "Authorization: Bearer",
    ):
        if forbidden in {"api.github.com", "token.actions.githubusercontent.com/.well-known"}:
            guarded_live = all(
                marker in broker
                for marker in (
                    "RUNTIME_POLICY_BINDING_NAMES",
                    "G5_TRUST_RUNTIME_ENABLED",
                    "G5ConnectedGithubAppAdapter",
                    "LEGACY_POLICY_DENYLIST",
                )
            )
            if guarded_live:
                continue
        require(
            forbidden not in broker and forbidden not in broker_config,
            "G5 trust broker remote capability drift",
        )
    for forbidden in (
        "wrangler",
        "curl ",
        "api.github.com",
    ):
        require(forbidden not in manual_workflow, "G5 manual workflow disabled boundary drift")
    for required in (
        'const VERSION = "f10.9-g5-trust-broker.v2"',
        'const CONNECTED_DISABLED = "IMPLEMENTED_DISABLED_NOT_CONFIGURED"',
        'const TRUST_STOP = "STOP_G5_TRUST_VERIFICATION_NOT_IMPLEMENTED"',
        "const MAX_TOKEN_LIFETIME_SECONDS = 600",
        "const MAX_LEDGER_RECORDS = 10_000",
        "const STRICT_TIMEOUT_MS = 15_000",
        "const MAX_RESPONSE_BYTES = 32_000_000",
        "export async function verifyGithubOidc",
        'header.alg !== "RS256"',
        "export class GithubAppReadOnlyAdapter",
        "export class G5ConnectedGithubAppAdapter",
        "export class G5GithubActionsOidcClient",
        "export class G5TrustBrokerHttpClient",
        "export class G5ConnectedSupabaseCollector",
        "export class G5SingleUseReceiptSession",
        "export async function validateTrustBrokerReceipt",
        "export function createDisabledConnectedGithubAppAdapter",
        "export function g5WorkflowGuard",
        "export class G5AtomicLedgerDurableObject extends DurableObjectBase",
        "export class G5TrustBroker",
        'env.G5_ATOMIC_LEDGER.getByName("g5-atomic-ledger-v1")',
        'state: "READY"',
        'state: "CONSUMED"',
        'state: "EXPIRED"',
        "binding.repositoryId, binding.runId, binding.runAttempt, binding.checkRunId",
        "binding.environmentId, binding.deploymentId",
        "authorizationComplete: false",
        "transportCreated: false",
        "IMPLEMENTED_DISABLED_NOT_CONFIGURED",
        "NEXT_SUPABASE_PUBLISHABLE_KEY",
        "apikey: key",
        "stop(CONNECTED_STOP)",
    ):
        require(required in broker, "G5 trust broker contract drift")
    for required in (
        "two concurrent consumes serialize and only one succeeds",
        "nonce and jti replay are rejected even with a different signed JWT",
        "nonce and jti indexes reject replay independently across gate identities",
        "timeout or diagnostic failure after CAS preserves CONSUMED and receipt",
        "expiry is re-evaluated after authoritative queries and before CAS",
        "expired gate cleanup creates a non-resurrectable tombstone",
        "cleanup transitions persisted READY to EXPIRED without resurrection",
        "broker emits no logs or sensitive token material",
        "Worker handler constructs broker from repository-only bindings",
        "runtime policy comes from bindings and legacy protected source is rejected",
        "GitHub-like not-before before issued-at is accepted",
        "OIDC numeric identity claims require canonical decimal strings",
        "authoritative evidence must declare a complete result set",
        "concurrent cross-identity nonce replay permits only one consume",
        "ledger rejects malformed RPC bindings and non-ABSENT persisted states",
        "receipt retrieval verifies persisted receipt integrity",
        "ledger capacity is exact, atomic, and rejects malformed counters",
        "falsy persisted replay markers still reject consumption",
        "broker preserves allowlisted reasons reconstructed across Durable Object RPC",
        "cleanup and receipt reject falsy corrupted gate records",
        "connected GitHub App adapter remains implemented but disabled by default",
        "manual workflow policy is deployment-ready but disabled without operational var",
        "OIDC client fetches a sanitized token with fixed audience",
        "trust broker HTTP client requires future config and validates one receipt",
        "trust broker HTTP client rejects unsafe endpoints before transport",
        "connected Supabase collector is GET-only, publishable-only, paginated, and stable",
        "connected Supabase collector rejects forged receipts and incomplete counts",
        "connected Supabase collector derives required source targets from enabled profiles",
        "connected Supabase collector remains disabled when config is absent or secret",
        "connected diagnostic CLI reports disabled instead of silently no-op",
    ):
        require(required in broker_tests, "G5 trust broker test coverage drift")
    for required in (
        '"workers_dev": false',
        '"G5_ATOMIC_LEDGER"',
        '"G5AtomicLedgerDurableObject"',
        '"repository-only-v1"',
    ):
        require(required in broker_config, "G5 repository-only config drift")
    for required in (
        "Cloudflare Worker + Durable Object",
        "ABSENT -> READY -> CONSUMED",
        "Supabase, SQL, DDL, RPC, grants",
        "todo write prohibido",
        "NOT_CREATED_NOT_APPROVED_NOT_CONSUMED",
        "STOP_G5_TRUST_VERIFICATION_NOT_IMPLEMENTED",
        "STOP_G5_CONNECTED_MODE_NOT_IMPLEMENTED",
    ):
        require(required in adr, "ADR-0013 trust broker drift")
    for required in (
        "workflow_dispatch",
        "permissions: {}",
        "vars.G5_TRUST_RUNTIME_ENABLED == 'true'",
        "environment: Production",
        "id-token: write",
        "G5_TRUST_BROKER_ENDPOINT",
        "NEXT_PUBLIC_SUPABASE_URL",
        "NEXT_SUPABASE_PUBLISHABLE_KEY",
    ):
        require(required in manual_workflow, "G5 manual workflow disabled marker drift")
    for required in (
        "ADR-0014",
        "REPOSITORY_ONLY_WORKFLOW_CONNECTED_PR_C_LOCAL_CANDIDATE",
        "NOT_EXECUTED_DISABLED_PLACEHOLDER",
        "STOP_G5_CONNECTED_MODE_NOT_IMPLEMENTED",
        "191539de71cbff95552c476463305e8d6f3e4b73",
        "7fe13bb907053f4dea51ac593b5df0de78cb40d6",
        "4b3dfb155081f9c3c9b638373b6e5aa2a06cca65",
    ):
        require(required in adr14, "ADR-0014 workflow connected drift")
    for required in (
        G5_GET_ONLY_ADAPTER_PREVIOUS_RESULT,
        G5_GET_ONLY_ADAPTER_BASE,
        G5_GET_ONLY_ADAPTER_BASE_TREE,
        G5_GET_ONLY_ADAPTER_CANDIDATE,
        "d6e4eaae058b52aacf5099c763204a1343a6eebf",
        "31905626274=success",
        "31905626285=success",
        "95062812645=F10.9 G5 Workflow PR C Repository-Only success",
        "95062903177=F9.7 Release Gate Contract success",
        "ADR-0013",
        "ADR-0014",
        "ADR-0015",
        "DEPLOYMENT_READY_DISABLED_NOT_CONFIGURED",
        "STOP_G5_ATOMIC_LEDGER_REQUIRED",
        "STOP_G5_REPLAY_DETECTED",
        "NOT_CREATED_NOT_APPROVED_NOT_CONSUMED",
        "STOP_G5_SOURCE_BLOCKERS_PRESENT",
        "STOP_G5_LIFECYCLE_BLOCKERS_PRESENT",
        "STOP_G5_TRUST_VERIFICATION_NOT_IMPLEMENTED",
        "IMPLEMENTED_DISABLED_NOT_CONFIGURED",
        "ZERO_OPERATIONAL",
    ):
        require(required in evidence, "G5 adapter evidence drift")
    require(
        "del authorization, facade_factory, observations, binding, page_size"
        in collector
        and "raise G5Error(CONNECTED_MODE_STATUS)" in collector,
        "G5 connected-mode disabled config drift",
    )
    for required in (
        "ADR-0015",
        "DEPLOYMENT_READY_DISABLED_NOT_CONFIGURED",
        "IMPLEMENTED_DISABLED_NOT_CONFIGURED",
        "G5_TRUST_OPERATIONAL_ENABLED",
        "G5_TRUST_BROKER_ENDPOINT",
        "GET-only",
        "sin workflow ejecutado",
    ):
        require(required in adr15, "ADR-0015 deployment-ready disabled drift")
    for required in (
        "F10.9 G5 Workflow PR D Deployment-Ready Disabled",
        "tests/test_fase10_9_g5_get_only_adapter_contract.py",
        "Run repository-only G5 trust broker and Durable Object contract",
        "workers/g5-trust-broker/test/trust-broker.test.mjs",
        ".github/workflows/g5-manual-trust-gate.yml",
        "needs: [g5-get-only-v2-3, f1010-m3-zero-write]",
        "Block G5 trust-plane external egress",
        "--bounding-set=-all",
        "env -i HOME=/tmp CI=true",
        "Restore G5 trust-plane external egress",
    ):
        require(required in workflow, "G5 v2.3 focused CI drift")
    require(
        workflow.index("Run repository-only G5 trust-plane focused contract")
        < workflow.index("git checkout --detach \"$F97_CANDIDATE_COMMIT\""),
        "G5 v2.3 focused CI must precede historical F9.7 checkout",
    )
    validate_context_graph(repo, 71, 408)


def validate_g5_operational_runbook(
    repo: Path, base: str, head: str, event: str,
) -> None:
    require(base == G5_OPERATIONAL_RUNBOOK_BASE, "unexpected G5 operational runbook base")
    require_sha(repo, "G5_OPERATIONAL_RUNBOOK_BASE", base)
    require_sha(repo, "head", head)
    require(
        commit_tree(repo, base) == G5_OPERATIONAL_RUNBOOK_BASE_TREE,
        "G5 operational runbook base tree drift",
    )
    candidate_head = head
    if event == "push":
        parents = commit_parents(repo, head)
        require(
            len(parents) == 2 and parents[0] == base,
            "G5 operational runbook push must be a protected merge",
        )
        candidate_head = parents[1]
        require(
            commit_tree(repo, head) == commit_tree(repo, candidate_head),
            "G5 operational runbook merge tree drift",
        )
    else:
        require(
            commit_parents(repo, head) == [base],
            "G5 operational runbook candidate must be one direct commit",
        )
    require_exact_delta(
        repo,
        base,
        candidate_head,
        G5_OPERATIONAL_RUNBOOK_ALLOWED_STATUSES,
        G5_OPERATIONAL_RUNBOOK_ALLOWED_MODES,
    )
    state = (repo / ".context/estado_del_proyecto.md").read_text(encoding="utf-8")
    task = (
        repo / ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md"
    ).read_text(encoding="utf-8")
    plan = (
        repo / ".context/operaciones/plan_remediacion_f10_9_fg2_fg3.md"
    ).read_text(encoding="utf-8")
    evidence = (
        repo / ".context/operaciones/g5_get_only_adapter_contract_2026_08_14.md"
    ).read_text(encoding="utf-8")
    runbook = (
        repo / ".context/operaciones/g5_operational_activation_runbook_2026_08_15.md"
    ).read_text(encoding="utf-8")
    adr16 = (
        repo / ".context/decisiones/ADR-0016_g5_operational_activation_gates.md"
    ).read_text(encoding="utf-8")
    manifest = (
        repo / ".context/operaciones/g5_operational_activation_manifest_2026_08_15.json"
    ).read_text(encoding="utf-8")
    preflight = (
        repo / "scripts/shared/f10_9_g5_operational_activation_preflight.py"
    ).read_text(encoding="utf-8")
    preflight_tests = (
        repo / "tests/test_fase10_9_g5_operational_activation_preflight.py"
    ).read_text(encoding="utf-8")
    workflow = (repo / ".github/workflows/f9-7-contract.yml").read_text(
        encoding="utf-8"
    )
    combined = "\n".join((state, task, plan, evidence, runbook, adr16, manifest))
    for required in (
        G5_OPERATIONAL_RUNBOOK_STATUS,
        "d62c8969e7d229bb8d2a9e1f8c6db6a1c4ef4d1d",
        G5_OPERATIONAL_RUNBOOK_BASE,
        G5_OPERATIONAL_RUNBOOK_BASE_TREE,
        "31912540519=PASS",
        "95079685172=PASS",
        "95079685191=PASS",
        "31912540528",
        "95079764790=CANCELLED",
        "CI_INFRA_TIMEOUT_PLAYWRIGHT_APT",
        "95084155346=PASS",
        "CI_RETRY_PASS",
        "run_attempt=2",
        "run_attempt=1",
        "NOT_CREATED_NOT_APPROVED_NOT_CONSUMED",
        "STOP_G5_TRUST_VERIFICATION_NOT_IMPLEMENTED",
        "IMPLEMENTED_DISABLED_NOT_CONFIGURED",
        "G5 end-to-end = `50%`",
        "G5 `5/10` dominios end-to-end",
        "connected collector deployment-ready",
    ):
        require(required in combined, "G5 PR E reconciliation evidence drift")
    for required in ("E1", "E2", "E3", "E4", "E5", "E6"):
        require(required in runbook, "G5 PR E runbook gate drift")
    for required in (
        "STOP",
        "No se puede combinar",
        "Un gate PASS no concede el siguiente",
    ):
        require(required in runbook or required in adr16, "G5 PR E runbook gate drift")
    for required in (
        "G5_GITHUB_APP_PRIVATE_KEY",
        "G5_GITHUB_APP_ID",
        "G5_OIDC_AUDIENCE",
        "G5_TRUST_BROKER_ENDPOINT",
        "G5_TRUST_RUNTIME_ENABLED",
        "ABSENT_NOT_CONFIGURED",
        "REPOSITORY_ONLY_NAME_ONLY_NO_VALUES",
        "PREPARED_NOT_CONFIGURED",
        '"actions": "read"',
        '"checks": "read"',
        '"contents": "read"',
        '"deployments": "read"',
        '"metadata": "read"',
        '"id-token": "write"',
    ):
        require(required in manifest, "G5 PR E manifest drift")
    for forbidden in (
        "https://",
        "http://",
        "sb_secret_",
        "sb_publishable_",
        "eyJhbG",
        "-----BEGIN",
        "installation_id",
        "project_ref",
        "account_id",
        '"value"',
        '"token"',
        '"private_key"',
    ):
        require(forbidden not in manifest, "G5 PR E manifest contains sensitive value")
    preflight_tree = ast.parse(preflight)
    imported_roots: set[str] = set()
    called_names: set[str] = set()
    referenced_names: set[str] = set()
    for node in ast.walk(preflight_tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called_names.add(node.func.attr)
        elif isinstance(node, ast.Name):
            referenced_names.add(node.id)
    require(
        imported_roots
        <= {"__future__", "argparse", "dataclasses", "json", "pathlib", "re", "types", "typing"},
        "G5 PR E preflight import drift",
    )
    require(
        not imported_roots
        & {"os", "socket", "subprocess", "requests", "httpx", "urllib", "supabase"},
        "G5 PR E preflight remote capability",
    )
    require(
        not called_names & {"getenv", "urlopen", "connect", "request", "run", "check_output"},
        "G5 PR E preflight runtime capability",
    )
    require(
        not referenced_names & {"environ", "workflow_dispatch", "wrangler"},
        "G5 PR E preflight indirect capability",
    )
    for required in (
        "test_pr387_attempts_are_preserved_and_retry_is_ci_only",
        "test_manifest_contains_no_configuration_values_or_remote_identifiers",
        "test_preflight_is_completely_offline",
        "test_gates_e1_to_e6_are_reordered_and_non_executing",
        "test_permissions_are_exact_and_write_permissions_are_minimal",
        "test_runbook_and_adr_preserve_operational_run_attempt_one",
    ):
        require(required in preflight_tests, "G5 PR E test coverage drift")
    for required in (
        "tests/test_fase10_9_g5_operational_activation_preflight.py",
        ".context/operaciones/g5_operational_activation_manifest_2026_08_15.json",
        ".context/operaciones/g5_operational_activation_runbook_2026_08_15.md",
        ".context/decisiones/ADR-0016_g5_operational_activation_gates.md",
    ):
        require(required in workflow, "G5 PR E focused CI drift")
    validate_context_graph(repo, 73, 416)


def validate_g5_e1_hardening(repo: Path, base: str, head: str, event: str) -> None:
    require(base == G5_E1_HARDENING_BASE, "unexpected G5 E1 hardening base")
    require_sha(repo, "G5_E1_HARDENING_BASE", base)
    require_sha(repo, "head", head)
    require(
        commit_tree(repo, base) == G5_E1_HARDENING_BASE_TREE,
        "G5 E1 hardening base tree drift",
    )
    candidate_head = head
    if event == "push":
        parents = commit_parents(repo, head)
        require(
            len(parents) == 2 and parents[0] == base,
            "G5 E1 hardening push must be a protected merge",
        )
        candidate_head = parents[1]
        require(
            commit_tree(repo, head) == commit_tree(repo, candidate_head),
            "G5 E1 hardening merge tree drift",
        )
    else:
        require(
            commit_parents(repo, head) == [base],
            "G5 E1 hardening candidate must be one direct commit",
        )
    require_exact_delta(
        repo,
        base,
        candidate_head,
        G5_E1_HARDENING_ALLOWED_STATUSES,
        G5_E1_HARDENING_ALLOWED_MODES,
    )
    state = (repo / ".context/estado_del_proyecto.md").read_text(encoding="utf-8")
    task = (
        repo / ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md"
    ).read_text(encoding="utf-8")
    plan = (repo / ".context/operaciones/plan_remediacion_f10_9_fg2_fg3.md").read_text(
        encoding="utf-8"
    )
    runbook = (
        repo / ".context/operaciones/g5_operational_activation_runbook_2026_08_15.md"
    ).read_text(encoding="utf-8")
    adr16 = (repo / ".context/decisiones/ADR-0016_g5_operational_activation_gates.md").read_text(
        encoding="utf-8"
    )
    adr17 = (
        repo / ".context/decisiones/ADR-0017_g5_e1_cloudflare_deployment_hardening.md"
    ).read_text(encoding="utf-8")
    manifest_text = (
        repo / ".context/operaciones/g5_operational_activation_manifest_2026_08_15.json"
    ).read_text(encoding="utf-8")
    preflight_tests = (
        repo / "tests/test_fase10_9_g5_operational_activation_preflight.py"
    ).read_text(encoding="utf-8")
    e1_tests = (repo / "tests/test_fase10_9_g5_e1_hardening.py").read_text(
        encoding="utf-8"
    )
    workflow = (repo / ".github/workflows/f9-7-contract.yml").read_text(encoding="utf-8")
    wrangler_config = json.loads(
        (repo / "workers/g5-trust-broker/wrangler.repository-only.jsonc").read_text(
            encoding="utf-8"
        )
    )
    package_json = json.loads(
        (repo / "workers/g5-trust-broker/package.json").read_text(encoding="utf-8")
    )
    package_lock = json.loads(
        (repo / "workers/g5-trust-broker/package-lock.json").read_text(encoding="utf-8")
    )
    manifest = json.loads(manifest_text)
    combined = "\n".join((state, task, plan, runbook, adr16, adr17, manifest_text))
    for required in (
        G5_E1_HARDENING_STATUS,
        G5_E1_HARDENING_BASE,
        G5_E1_HARDENING_BASE_TREE,
        "eb052c2755937a2bf239cd778bc814274fbc846f",
        "31917838025=PASS",
        "31917838011=PASS",
        "95092629457=PASS",
        "95092706912=PASS",
        "run_attempt=1",
        G5_E1_READINESS_STATUS,
        "Workers existentes `0`",
        "NOT_EXECUTED",
        G5_E1_DEPLOYMENT_STOP,
        "Hito 1 `60%`",
        "F10.9 `38%`",
        "G5 `50%`",
        "NOT_CREATED_NOT_APPROVED_NOT_CONSUMED",
        "STOP_G5_TRUST_VERIFICATION_NOT_IMPLEMENTED",
        "IMPLEMENTED_DISABLED_NOT_CONFIGURED",
        "G5_TRUST_OPERATIONAL_ENABLED` permanece `ABSENT_NOT_CONFIGURED`",
    ):
        require(required in combined, "G5 E1 hardening evidence drift")
    for required in (
        "preview_urls:false",
        "workers_dev:false",
        "wrangler deploy --strict --config wrangler.repository-only.jsonc",
        "--dry-run --outdir /tmp/studiamatch-g5-e1-dry-run",
        "CLOUDFLARE_API_TOKEN",
        "CLOUDFLARE_ACCOUNT_ID",
        "CF_API_TOKEN",
        "CF_ACCOUNT_ID",
        "E3A",
        "DEFINED_NOT_EXECUTED",
        "E4 queda bloqueado",
        "Este PR no selecciona ni habilita endpoint",
    ):
        require(required in combined, "G5 E1 hardening runbook drift")
    require(wrangler_config.get("name") == "g5-trust-broker-repository-only", "G5 E1 worker name drift")
    require(wrangler_config.get("main") == "src/index.mjs", "G5 E1 worker main drift")
    require(wrangler_config.get("compatibility_date") == "2026-08-15", "G5 E1 compatibility drift")
    require(wrangler_config.get("workers_dev") is False, "G5 E1 workers_dev drift")
    require(wrangler_config.get("preview_urls") is False, "G5 E1 preview_urls drift")
    for forbidden_key in ("route", "routes", "domain", "domains", "custom_domain", "custom_domains", "triggers"):
        require(forbidden_key not in wrangler_config, "G5 E1 public exposure config drift")
    require(
        wrangler_config.get("durable_objects") == {
            "bindings": [
                {"name": "G5_ATOMIC_LEDGER", "class_name": "G5AtomicLedgerDurableObject"}
            ]
        },
        "G5 E1 durable binding drift",
    )
    require(
        wrangler_config.get("migrations") == [
            {"tag": "repository-only-v1", "new_sqlite_classes": ["G5AtomicLedgerDurableObject"]}
        ],
        "G5 E1 durable migration drift",
    )
    scripts = package_json.get("scripts", {})
    require(package_json.get("devDependencies") == {"wrangler": "4.30.0"}, "G5 E1 wrangler pin drift")
    require(package_lock.get("lockfileVersion") == 3, "G5 E1 lockfile drift")
    require(
        package_lock.get("packages", {}).get("node_modules/wrangler", {}).get("version") == "4.30.0",
        "G5 E1 lockfile wrangler drift",
    )
    require(
        list(scripts) == ["e1:dry-run", "e1:deploy"],
        "G5 E1 script order drift",
    )
    require(
        scripts.get("e1:dry-run")
        == "wrangler deploy --strict --config wrangler.repository-only.jsonc --dry-run --outdir /tmp/studiamatch-g5-e1-dry-run",
        "G5 E1 dry-run command drift",
    )
    require(
        scripts.get("e1:deploy") == "wrangler deploy --strict --config wrangler.repository-only.jsonc",
        "G5 E1 deploy command drift",
    )
    for command in scripts.values():
        for forbidden in ("--temporary", "--route", "--routes", "--domain", "--triggers", "--schedule", "--schedules", "--env-file", "--secrets-file", "--keep-vars"):
            require(forbidden not in command, "G5 E1 forbidden deploy flag drift")
    require([gate.get("id") for gate in manifest.get("gates", [])] == ["E1", "E2", "E3", "E3A", "E4", "E5", "E6"], "G5 E1 manifest gate drift")
    for required in (
        "test_wrangler_version_is_exact_and_lockfile_is_versioned",
        "test_wrangler_config_is_isolated_and_explicitly_non_public",
        "test_package_scripts_require_dry_run_before_exact_deploy_command",
        "test_cloudflare_credential_names_are_standard_for_e1_only",
        "test_e3a_endpoint_gate_is_separate_and_blocks_e4",
        "test_e1_hardening_docs_preserve_stops_and_no_sensitive_values",
    ):
        require(required in e1_tests, "G5 E1 test coverage drift")
    require(
        "test_gates_e1_to_e6_and_e3a_are_separate_and_non_executing" in preflight_tests,
        "G5 E1 preflight test coverage drift",
    )
    for required in (
        "tests/test_fase10_9_g5_e1_hardening.py",
        "tests/test_fase10_9_g5_operational_activation_preflight.py",
    ):
        require(required in workflow, "G5 E1 focused CI drift")
    validate_context_graph(repo, 74, 418)


def validate_g5_e1_wrangler_compat(repo: Path, base: str, head: str, event: str) -> None:
    require(base == G5_E1_WRANGLER_COMPAT_BASE, "unexpected G5 E1 Wrangler compat base")
    require_sha(repo, "G5_E1_WRANGLER_COMPAT_BASE", base)
    require_sha(repo, "head", head)
    require(
        commit_tree(repo, base) == G5_E1_WRANGLER_COMPAT_BASE_TREE,
        "G5 E1 Wrangler compat base tree drift",
    )
    candidate_head = head
    if event == "push":
        parents = commit_parents(repo, head)
        require(
            len(parents) == 2 and parents[0] == base,
            "G5 E1 Wrangler compat push must be a protected merge",
        )
        candidate_head = parents[1]
        require(
            commit_tree(repo, head) == commit_tree(repo, candidate_head),
            "G5 E1 Wrangler compat merge tree drift",
        )
    else:
        require(
            commit_parents(repo, head) == [base],
            "G5 E1 Wrangler compat candidate must be one direct commit",
        )
    require_exact_delta(
        repo,
        base,
        candidate_head,
        G5_E1_WRANGLER_COMPAT_ALLOWED_STATUSES,
        G5_E1_WRANGLER_COMPAT_ALLOWED_MODES,
    )
    state = (repo / ".context/estado_del_proyecto.md").read_text(encoding="utf-8")
    task = (
        repo / ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md"
    ).read_text(encoding="utf-8")
    plan = (repo / ".context/operaciones/plan_remediacion_f10_9_fg2_fg3.md").read_text(
        encoding="utf-8"
    )
    runbook = (
        repo / ".context/operaciones/g5_operational_activation_runbook_2026_08_15.md"
    ).read_text(encoding="utf-8")
    adr16 = (repo / ".context/decisiones/ADR-0016_g5_operational_activation_gates.md").read_text(
        encoding="utf-8"
    )
    adr17 = (
        repo / ".context/decisiones/ADR-0017_g5_e1_cloudflare_deployment_hardening.md"
    ).read_text(encoding="utf-8")
    manifest_text = (
        repo / ".context/operaciones/g5_operational_activation_manifest_2026_08_15.json"
    ).read_text(encoding="utf-8")
    preflight_source = (
        repo / "scripts/shared/f10_9_g5_operational_activation_preflight.py"
    ).read_text(encoding="utf-8")
    e1_tests = (repo / "tests/test_fase10_9_g5_e1_hardening.py").read_text(
        encoding="utf-8"
    )
    preflight_tests = (
        repo / "tests/test_fase10_9_g5_operational_activation_preflight.py"
    ).read_text(encoding="utf-8")
    workflow = (repo / ".github/workflows/f9-7-contract.yml").read_text(encoding="utf-8")
    guard = (repo / "workers/g5-trust-broker/test/block-egress.mjs").read_text(
        encoding="utf-8"
    )
    wrangler_config = json.loads(
        (repo / "workers/g5-trust-broker/wrangler.repository-only.jsonc").read_text(
            encoding="utf-8"
        )
    )
    package_json = json.loads(
        (repo / "workers/g5-trust-broker/package.json").read_text(encoding="utf-8")
    )
    package_lock = json.loads(
        (repo / "workers/g5-trust-broker/package-lock.json").read_text(encoding="utf-8")
    )
    manifest = json.loads(manifest_text)
    combined = "\n".join((state, task, plan, runbook, adr16, adr17, manifest_text))
    for required in (
        G5_E1_WRANGLER_COMPAT_STATUS,
        G5_E1_WRANGLER_COMPAT_BASE,
        G5_E1_WRANGLER_COMPAT_BASE_TREE,
        "f48d0f25154970531744815e1d3769a20731717a",
        "31921056993=PASS",
        "31921056963=PASS",
        "95100885045=PASS",
        "95100958336=PASS",
        "run_attempt=1",
        G5_E1_READINESS_STATUS,
        G5_E1_DEPLOYMENT_STOP,
        G5_E1_WRANGLER_STOP,
        "Wrangler `4.30.0`",
        f"Wrangler exacto `{G5_E1_WRANGLER_VERSION}`",
        "Hito 1 `60%`",
        "F10.9 `38%`",
        "G5 `50%`",
        "NOT_EXECUTED",
        "NOT_CREATED_NOT_APPROVED_NOT_CONSUMED",
        "STOP_G5_TRUST_VERIFICATION_NOT_IMPLEMENTED",
        "IMPLEMENTED_DISABLED_NOT_CONFIGURED",
    ):
        require(required in combined, "G5 E1 Wrangler compat evidence drift")
    for required in (
        "wrangler deploy --strict --config wrangler.repository-only.jsonc",
        "--dry-run --outdir /tmp/studiamatch-g5-e1-dry-run",
        "CLOUDFLARE_API_TOKEN",
        "CLOUDFLARE_ACCOUNT_ID",
        "dry-run offline",
        "E3A",
        "DEFINED_NOT_EXECUTED",
        "E4 permanece bloqueado por E3A",
    ):
        require(required in combined, "G5 E1 Wrangler compat runbook drift")
    require(wrangler_config.get("name") == "g5-trust-broker-repository-only", "G5 E1 worker name drift")
    require(wrangler_config.get("main") == "src/index.mjs", "G5 E1 worker main drift")
    require(wrangler_config.get("workers_dev") is False, "G5 E1 workers_dev drift")
    require(wrangler_config.get("preview_urls") is False, "G5 E1 preview_urls drift")
    for forbidden_key in ("route", "routes", "domain", "domains", "custom_domain", "custom_domains", "triggers"):
        require(forbidden_key not in wrangler_config, "G5 E1 public exposure config drift")
    require(
        wrangler_config.get("durable_objects") == {
            "bindings": [
                {"name": "G5_ATOMIC_LEDGER", "class_name": "G5AtomicLedgerDurableObject"}
            ]
        },
        "G5 E1 durable binding drift",
    )
    require(
        wrangler_config.get("migrations") == [
            {"tag": "repository-only-v1", "new_sqlite_classes": ["G5AtomicLedgerDurableObject"]}
        ],
        "G5 E1 durable migration drift",
    )
    scripts = package_json.get("scripts", {})
    require(package_json.get("devDependencies") == {"wrangler": G5_E1_WRANGLER_VERSION}, "G5 E1 Wrangler pin drift")
    require(package_lock.get("lockfileVersion") == 3, "G5 E1 lockfile drift")
    require(
        package_lock.get("packages", {}).get("", {}).get("devDependencies")
        == {"wrangler": G5_E1_WRANGLER_VERSION},
        "G5 E1 root lockfile Wrangler drift",
    )
    require(
        package_lock.get("packages", {}).get("node_modules/wrangler", {}).get("version")
        == G5_E1_WRANGLER_VERSION,
        "G5 E1 lockfile Wrangler drift",
    )
    require(scripts.get("e1:deploy") == "wrangler deploy --strict --config wrangler.repository-only.jsonc", "G5 E1 deploy command drift")
    require(
        scripts.get("e1:dry-run")
        == "wrangler deploy --strict --config wrangler.repository-only.jsonc --dry-run --outdir /tmp/studiamatch-g5-e1-dry-run",
        "G5 E1 dry-run command drift",
    )
    require(manifest.get("frozen_versions", {}).get("wrangler") == G5_E1_WRANGLER_VERSION, "G5 E1 manifest Wrangler drift")
    require(f'"wrangler": "{G5_E1_WRANGLER_VERSION}"' in preflight_source, "G5 E1 preflight Wrangler drift")
    for required in (
        "test_wrangler_cli_version_and_strict_support_are_executable",
        "test_e1_dry_run_executes_without_cloudflare_credentials_or_external_egress",
        "NODE_OPTIONS",
        "NETWORK_EGRESS_BLOCKED",
        "CLOUDFLARE_API_TOKEN",
        "CLOUDFLARE_ACCOUNT_ID",
        "WRANGLER_VERSION = \"4.44.0\"",
    ):
        require(required in e1_tests + guard, "G5 E1 Wrangler compat test coverage drift")
    require("npm ci --ignore-scripts --audit=false --fund=false --prefix workers/g5-trust-broker" in workflow, "G5 E1 CI npm install drift")
    require("tests/test_fase10_9_g5_e1_hardening.py" in workflow, "G5 E1 focused CI drift")
    require('"wrangler"] == "4.44.0"' in preflight_tests, "G5 E1 preflight test Wrangler drift")
    validate_context_graph(repo, 74, 418)


def validate_g5_trust_live_remediation(repo: Path, base: str, head: str, event: str) -> None:
    require(base == G5_TRUST_LIVE_REMEDIATION_BASE, "unexpected G5 trust live remediation base")
    require_sha(repo, "G5_TRUST_LIVE_REMEDIATION_BASE", base)
    require_sha(repo, "head", head)
    require(
        commit_tree(repo, base) == G5_TRUST_LIVE_REMEDIATION_BASE_TREE,
        "G5 trust live remediation base tree drift",
    )
    candidate_head = head
    if event == "push":
        parents = commit_parents(repo, head)
        require(
            len(parents) == 2 and parents[0] == base,
            "G5 trust live remediation push must be a protected merge",
        )
        candidate_head = parents[1]
        require(
            commit_tree(repo, head) == commit_tree(repo, candidate_head),
            "G5 trust live remediation merge tree drift",
        )
    else:
        require(
            commit_parents(repo, head) == [base],
            "G5 trust live remediation candidate must be one direct commit",
        )
    require_exact_delta(
        repo,
        base,
        candidate_head,
        G5_TRUST_LIVE_REMEDIATION_ALLOWED_STATUSES,
        G5_TRUST_LIVE_REMEDIATION_ALLOWED_MODES,
    )
    state = (repo / ".context/estado_del_proyecto.md").read_text(encoding="utf-8")
    task = (
        repo / ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md"
    ).read_text(encoding="utf-8")
    plan = (repo / ".context/operaciones/plan_remediacion_f10_9_fg2_fg3.md").read_text(
        encoding="utf-8"
    )
    adapter_doc = (
        repo / ".context/operaciones/g5_get_only_adapter_contract_2026_08_14.md"
    ).read_text(encoding="utf-8")
    runbook = (
        repo / ".context/operaciones/g5_operational_activation_runbook_2026_08_15.md"
    ).read_text(encoding="utf-8")
    adr16 = (repo / ".context/decisiones/ADR-0016_g5_operational_activation_gates.md").read_text(
        encoding="utf-8"
    )
    adr18 = (
        repo / ".context/decisiones/ADR-0018_g5_trust_live_remediation_repository_only.md"
    ).read_text(encoding="utf-8")
    manifest_text = (
        repo / ".context/operaciones/g5_operational_activation_manifest_2026_08_15.json"
    ).read_text(encoding="utf-8")
    preflight_source = (
        repo / "scripts/shared/f10_9_g5_operational_activation_preflight.py"
    ).read_text(encoding="utf-8")
    preflight_tests = (
        repo / "tests/test_fase10_9_g5_operational_activation_preflight.py"
    ).read_text(encoding="utf-8")
    get_only_source = (
        repo / "scripts/shared/f10_9_g5_get_only_adapter_contract.py"
    ).read_text(encoding="utf-8")
    get_only_tests = (
        repo / "tests/test_fase10_9_g5_get_only_adapter_contract.py"
    ).read_text(encoding="utf-8")
    f97_workflow = (repo / ".github/workflows/f9-7-contract.yml").read_text(encoding="utf-8")
    g5_workflow = (repo / ".github/workflows/g5-manual-trust-gate.yml").read_text(encoding="utf-8")
    worker_source = (repo / "workers/g5-trust-broker/src/index.mjs").read_text(encoding="utf-8")
    worker_tests = (repo / "workers/g5-trust-broker/test/trust-broker.test.mjs").read_text(
        encoding="utf-8"
    )
    manifest = json.loads(manifest_text)
    combined = "\n".join((state, task, plan, adapter_doc, runbook, adr16, adr18, manifest_text))
    for required in (
        G5_TRUST_LIVE_REMEDIATION_STATUS,
        "c36cc9b6efb166f2f840615759793b7917142f38",
        G5_TRUST_LIVE_REMEDIATION_BASE,
        G5_TRUST_LIVE_REMEDIATION_BASE_TREE,
        "31926378062=PASS",
        "31926378069=PASS",
        "95114516929=PASS",
        "95114603279=PASS",
        "run_attempt=1",
        G5_E1_DEPLOYMENT_STATUS,
        G5_E1_CREDENTIAL_ATTESTATION,
        "f10.9-g5-trust-broker.v2",
        "G5_ATOMIC_LEDGER",
        "G5AtomicLedgerDurableObject",
        "repository-only-v1",
        "routes/domains/schedules/vars/secrets `0`",
        "E4_BEFORE_E5_SUPERSEDED_NOT_EXECUTABLE",
        "NOT_CREATED_NOT_APPROVED_NOT_CONSUMED",
        "STOP_G5_TRUST_VERIFICATION_NOT_IMPLEMENTED",
        "IMPLEMENTED_DISABLED_NOT_CONFIGURED",
        "Hito 1 `60%`",
        "F10.9 `38%`",
        "G5 `50%`",
    ):
        require(required in combined, "G5 trust live remediation evidence drift")
    for required in G5_TRUST_RUNTIME_POLICY_NAMES:
        require(required in combined, "G5 trust runtime policy name drift")
    require(manifest.get("superseded_sequence") == "E4_BEFORE_E5_SUPERSEDED_NOT_EXECUTABLE", "G5 trust sequence drift")
    require(
        [gate.get("id") for gate in manifest.get("gates", [])]
        == ["E1", "E2", "E3", "E4", "E4A", "E4B", "E5", "E6"],
        "G5 trust gate order drift",
    )
    require(manifest.get("e1_deployment_reconciliation", {}).get("status") == G5_E1_DEPLOYMENT_STATUS, "G5 E1 status drift")
    require(
        manifest.get("e1_deployment_reconciliation", {}).get("credential_state")
        == G5_E1_CREDENTIAL_ATTESTATION,
        "G5 E1 credential attestation drift",
    )
    require(
        all(item.get("state") == "ABSENT_NOT_CONFIGURED" for item in manifest.get("required_configuration_names", [])),
        "G5 trust runtime policy must remain name-only",
    )
    for forbidden in (
        "https://",
        "http://",
        "sb_secret_",
        "sb_publishable_",
        "eyJhbG",
        "-----BEGIN",
        "project_ref",
        "account_id",
        "worker_id",
        "deployment_id",
        '"value"',
        '"token"',
        '"current_value"',
    ):
        require(forbidden not in manifest_text, "G5 PR H manifest contains sensitive value")
    require("vars.G5_TRUST_RUNTIME_ENABLED == 'true'" in g5_workflow, "G5 workflow runtime guard drift")
    require("G5_TRUST_OPERATIONAL_ENABLED" not in g5_workflow, "G5 workflow legacy guard drift")
    require(".context/decisiones/ADR-0018_g5_trust_live_remediation_repository_only.md" in f97_workflow, "G5 PR H focused CI path drift")
    for required in (
        "RUNTIME_POLICY_BINDING_NAMES",
        "LEGACY_POLICY_DENYLIST",
        "_valid_runtime_policy_triplet",
    ):
        require(required in get_only_source, "G5 GET-only runtime policy drift")
    for forbidden in (
        "PROTECTED_SOURCE_SHA =",
        "PROTECTED_SOURCE_TREE =",
        "EXPECTED_WORKFLOW_SHA =",
        "EXPECTED_WORKFLOW_BLOB_SHA =",
    ):
        require(forbidden not in get_only_source, "G5 GET-only hardcoded authority drift")
    require(
        "test_legacy_pr_c_sha_tree_blob_are_denylist_not_authority" in get_only_tests,
        "G5 GET-only denylist test drift",
    )
    for required in (
        "RUNTIME_POLICY_BINDING_NAMES",
        "G5ConnectedGithubAppAdapter",
        "G5GithubJwksClient",
        "createGithubAppJwt",
        "LEGACY_POLICY_DENYLIST",
        "G5_GITHUB_APP_INSTALLATION_ID",
        "G5_TRUST_RUNTIME_ENABLED",
    ):
        require(required in worker_source + worker_tests, "G5 broker live remediation drift")
    require("G5_TRUST_OPERATIONAL_ENABLED" not in worker_source + worker_tests, "G5 broker legacy guard drift")
    for required in (
        "test_pr390_and_e1_deployment_are_sanitized_and_reconciled",
        "test_gates_e1_to_e6_are_reordered_and_non_executing",
        "G5_TRUST_RUNTIME_ENABLED",
    ):
        require(required in preflight_tests, "G5 PR H preflight test coverage drift")
    preflight_tree = ast.parse(preflight_source)
    imported_roots: set[str] = set()
    called_names: set[str] = set()
    referenced_names: set[str] = set()
    for node in ast.walk(preflight_tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called_names.add(node.func.attr)
        elif isinstance(node, ast.Name):
            referenced_names.add(node.id)
    require(
        imported_roots
        <= {"__future__", "argparse", "dataclasses", "json", "pathlib", "re", "types", "typing"},
        "G5 PR H preflight import drift",
    )
    require(
        not imported_roots
        & {"os", "socket", "subprocess", "requests", "httpx", "urllib", "supabase"},
        "G5 PR H preflight remote capability",
    )
    require(
        not called_names & {"getenv", "urlopen", "connect", "request", "run", "check_output"},
        "G5 PR H preflight runtime capability",
    )
    require(
        not referenced_names & {"environ", "workflow_dispatch"},
        "G5 PR H preflight indirect capability",
    )
    validate_context_graph(repo, 75, 426)


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
    if (
        base_ref == "desarrollo"
        and base == F1010_M3_PUBLIC_ACL_PREFLIGHT_POST_MERGE_BASE
        and (
            event == "push"
            or head_ref == F1010_M3_PUBLIC_ACL_PREFLIGHT_POST_MERGE_HEAD_REF
        )
    ):
        return "f1010_m3_public_acl_preflight_post_merge"
    if (
        base_ref == "desarrollo"
        and base == F1010_M3_PUBLIC_ACL_PRIVATE_PREFLIGHT_V2_PAYLOAD_BASE
        and (
            event == "push"
            or head_ref == F1010_M3_PUBLIC_ACL_PRIVATE_PREFLIGHT_V2_PAYLOAD_HEAD_REF
        )
    ):
        return "f1010_m3_public_acl_private_preflight_v2_payload"
    if (
        base_ref == "desarrollo"
        and base == F1010_M3_PUBLIC_ACL_POST_MERGE_HARNESS_BASE
        and (
            event == "push"
            or head_ref == F1010_M3_PUBLIC_ACL_POST_MERGE_HARNESS_HEAD_REF
        )
    ):
        return "f1010_m3_public_acl_post_merge_harness"
    if (
        base_ref == "desarrollo"
        and base == F1010_M3_PUBLIC_ACL_V2_EVIDENCE_BASE
        and (event == "push" or head_ref == F1010_M3_PUBLIC_ACL_V2_EVIDENCE_HEAD_REF)
    ):
        return "f1010_m3_public_acl_v2_evidence"
    if (
        base_ref == "desarrollo"
        and base == F1010_H1_CA1_REBASELINE_BASE
        and (event == "push" or head_ref == F1010_H1_CA1_REBASELINE_HEAD_REF)
    ):
        return "f1010_h1_ca1_rebaseline"
    if (
        base_ref == "desarrollo"
        and base == G5_PRODUCTION_READONLY_BASE
        and (event == "push" or head_ref == G5_PRODUCTION_READONLY_HEAD_REF)
    ):
        return "g5_production_readonly"
    if (
        base_ref == "desarrollo"
        and base == G5_V2_ATTRIBUTION_BASE
        and (event == "push" or head_ref == G5_V2_ATTRIBUTION_HEAD_REF)
    ):
        return "g5_v2_attribution"
    if (
        base_ref == "desarrollo"
        and base == G5_V2_POST_MERGE_BASE
        and (event == "push" or head_ref == G5_V2_POST_MERGE_HEAD_REF)
    ):
        return "g5_v2_post_merge"
    if (
        base_ref == "desarrollo"
        and base == G5_GET_ONLY_ADAPTER_BASE
        and (event == "push" or head_ref == G5_GET_ONLY_ADAPTER_HEAD_REF)
    ):
        return "g5_get_only_adapter"
    if (
        base_ref == "desarrollo"
        and base == G5_OPERATIONAL_RUNBOOK_BASE
        and (event == "push" or head_ref == G5_OPERATIONAL_RUNBOOK_HEAD_REF)
    ):
        return "g5_operational_runbook"
    if (
        base_ref == "desarrollo"
        and base == G5_E1_HARDENING_BASE
        and (event == "push" or head_ref == G5_E1_HARDENING_HEAD_REF)
    ):
        return "g5_e1_hardening"
    if (
        base_ref == "desarrollo"
        and base == G5_E1_WRANGLER_COMPAT_BASE
        and (event == "push" or head_ref == G5_E1_WRANGLER_COMPAT_HEAD_REF)
    ):
        return "g5_e1_wrangler_compat"
    if (
        base_ref == "desarrollo"
        and base == G5_TRUST_LIVE_REMEDIATION_BASE
        and (event == "push" or head_ref == G5_TRUST_LIVE_REMEDIATION_HEAD_REF)
    ):
        return "g5_trust_live_remediation"
    if (
        base_ref == "desarrollo"
        and base == F1010_M3_PUBLIC_ACL_FINAL_READINESS_BASE
        and (event == "push" or head_ref == F1010_M3_PUBLIC_ACL_FINAL_READINESS_HEAD_REF)
    ):
        return "f1010_m3_public_acl_final_readiness"
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
            if (
                args.event == "pull_request"
                and args.head_ref == F1010_H1_CA1_REBASELINE_HEAD_REF
            ):
                raise BoundaryError(
                    "F10.10 Hito 1 CA1 rebaseline branch requires its frozen baseline"
                )
            if (
                args.event == "pull_request"
                and args.head_ref == G5_PRODUCTION_READONLY_HEAD_REF
            ):
                raise BoundaryError(
                    "G5 Production read-only branch requires its frozen baseline"
                )
            if (
                args.event == "pull_request"
                and args.head_ref == G5_V2_ATTRIBUTION_HEAD_REF
            ):
                raise BoundaryError(
                    "G5 v2 attribution branch requires its frozen baseline"
                )
            if (
                args.event == "pull_request"
                and args.head_ref == G5_V2_POST_MERGE_HEAD_REF
            ):
                raise BoundaryError(
                    "G5 v2 post-merge branch requires its frozen baseline"
                )
            if (
                args.event == "pull_request"
                and args.head_ref == G5_GET_ONLY_ADAPTER_HEAD_REF
            ):
                raise BoundaryError(
                    "G5 GET-only adapter contract branch requires its frozen baseline"
                )
            if (
                args.event == "pull_request"
                and args.head_ref == G5_OPERATIONAL_RUNBOOK_HEAD_REF
            ):
                raise BoundaryError(
                    "G5 PR E runbook branch requires the frozen PR #387 merge baseline"
                )
            if args.event == "pull_request" and args.head_ref == G5_E1_HARDENING_HEAD_REF:
                raise BoundaryError(
                    "G5 PR F E1 hardening branch requires the frozen PR #388 merge baseline"
                )
            if args.event == "pull_request" and args.head_ref == G5_E1_WRANGLER_COMPAT_HEAD_REF:
                raise BoundaryError(
                    "G5 PR G Wrangler compat branch requires the frozen PR #389 merge baseline"
                )
            if args.event == "pull_request" and args.head_ref == G5_TRUST_LIVE_REMEDIATION_HEAD_REF:
                raise BoundaryError(
                    "G5 PR H trust live remediation branch requires the frozen PR #390 merge baseline"
                )
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
            if (
                args.event == "pull_request"
                and args.head_ref == F1010_M3_PUBLIC_ACL_PREFLIGHT_POST_MERGE_HEAD_REF
            ):
                raise BoundaryError(
                    "F10.10 M3 PUBLIC ACL preflight post-merge branch requires its frozen protected desarrollo baseline"
                )
            if (
                args.event == "pull_request"
                and args.head_ref == F1010_M3_PUBLIC_ACL_PRIVATE_PREFLIGHT_V2_PAYLOAD_HEAD_REF
            ):
                raise BoundaryError(
                    "F10.10 M3 PUBLIC ACL private preflight v2 payload branch requires its frozen protected desarrollo baseline"
                )
            if (
                args.event == "pull_request"
                and args.head_ref == F1010_M3_PUBLIC_ACL_POST_MERGE_HARNESS_HEAD_REF
            ):
                raise BoundaryError(
                    "F10.10 M3 PUBLIC ACL post-merge harness branch requires its frozen protected desarrollo baseline"
                )
            if (
                args.event == "pull_request"
                and args.head_ref == F1010_M3_PUBLIC_ACL_V2_EVIDENCE_HEAD_REF
            ):
                raise BoundaryError(
                    "F10.10 M3 PUBLIC ACL v2 evidence branch requires its frozen protected desarrollo baseline"
                )
            if (
                args.event == "pull_request"
                and args.head_ref == F1010_M3_PUBLIC_ACL_FINAL_READINESS_HEAD_REF
            ):
                raise BoundaryError(
                    "F10.10 M3 PUBLIC ACL final readiness branch requires its frozen protected desarrollo baseline"
                )
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
            touched_f1010_m3_public_acl_preflight_post_merge = set(actual).intersection(
                F1010_M3_PUBLIC_ACL_PREFLIGHT_POST_MERGE_TRIGGER_PATHS
            )
            touched_f1010_m3_public_acl_private_preflight_v2_payload = set(actual).intersection(
                F1010_M3_PUBLIC_ACL_PRIVATE_PREFLIGHT_V2_PAYLOAD_TRIGGER_PATHS
            )
            touched_f1010_m3_public_acl_post_merge_harness = set(actual).intersection(
                F1010_M3_PUBLIC_ACL_POST_MERGE_HARNESS_TRIGGER_PATHS
            )
            touched_f1010_m3_public_acl_v2_evidence = set(actual).intersection(
                F1010_M3_PUBLIC_ACL_V2_EVIDENCE_TRIGGER_PATHS
            )
            touched_f1010_m3_public_acl_final_readiness = set(actual).intersection(
                F1010_M3_PUBLIC_ACL_FINAL_READINESS_TRIGGER_PATHS
            )
            touched_g5_trust_live_remediation = set(actual).intersection(
                G5_TRUST_LIVE_REMEDIATION_ALLOWED_STATUSES
            )
            if touched_f1010_m3_public_acl_final_readiness:
                touched_f1010_m3_public_acl_preflight = set()
            if touched_f1010_m3_public_acl_v2_evidence:
                touched_f1010_m3_public_acl_preflight = set()
            if (
                touched_f1010_m3_public_acl_post_merge_harness
                and args.base_sha == F1010_M3_PUBLIC_ACL_POST_MERGE_HARNESS_BASE
            ):
                touched_f1010_m3_public_acl_preflight = set()
            else:
                touched_f1010_m3_public_acl_post_merge_harness = set()
            if touched_f1010_m3_public_acl_private_preflight_v2_payload:
                touched_f1010_m3_public_acl_preflight = set()
                touched_f1010_m3_public_acl_preflight_post_merge = set()
            if touched_f1010_m3_public_acl_preflight_post_merge:
                touched_f1010_m3_public_acl_preflight = set()
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
                        touched_f1010_m3_public_acl_preflight_post_merge,
                        touched_f1010_m3_public_acl_private_preflight_v2_payload,
                        touched_f1010_m3_public_acl_post_merge_harness,
                        touched_f1010_m3_public_acl_v2_evidence,
                        touched_f1010_m3_public_acl_final_readiness,
                        touched_g5_trust_live_remediation,
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
            elif touched_f1010_m3_public_acl_preflight_post_merge:
                require(
                    args.head_ref == F1010_M3_PUBLIC_ACL_PREFLIGHT_POST_MERGE_HEAD_REF
                    or args.event == "push",
                    "F10.10 M3 PUBLIC ACL preflight post-merge paths require the protected post-merge branch",
                )
                require(
                    actual
                    == F1010_M3_PUBLIC_ACL_PREFLIGHT_POST_MERGE_ALLOWED_STATUSES,
                    "partial or expanded F10.10 M3 PUBLIC ACL preflight post-merge delta is forbidden",
                )
                mode = "f1010_m3_public_acl_preflight_post_merge"
            elif touched_f1010_m3_public_acl_private_preflight_v2_payload:
                require(
                    args.head_ref == F1010_M3_PUBLIC_ACL_PRIVATE_PREFLIGHT_V2_PAYLOAD_HEAD_REF
                    or args.event == "push",
                    "F10.10 M3 PUBLIC ACL private preflight v2 payload paths require the protected payload branch",
                )
                require(
                    actual == F1010_M3_PUBLIC_ACL_PRIVATE_PREFLIGHT_V2_PAYLOAD_ALLOWED_STATUSES,
                    "partial or expanded F10.10 M3 PUBLIC ACL private preflight v2 payload delta is forbidden",
                )
                mode = "f1010_m3_public_acl_private_preflight_v2_payload"
            elif touched_f1010_m3_public_acl_post_merge_harness:
                require(
                    args.head_ref == F1010_M3_PUBLIC_ACL_POST_MERGE_HARNESS_HEAD_REF
                    or args.event == "push",
                    "F10.10 M3 PUBLIC ACL post-merge harness paths require the protected harness branch",
                )
                require(
                    actual == F1010_M3_PUBLIC_ACL_POST_MERGE_HARNESS_ALLOWED_STATUSES,
                    "partial or expanded F10.10 M3 PUBLIC ACL post-merge harness delta is forbidden",
                )
                mode = "f1010_m3_public_acl_post_merge_harness"
            elif touched_f1010_m3_public_acl_v2_evidence:
                require(
                    args.head_ref == F1010_M3_PUBLIC_ACL_V2_EVIDENCE_HEAD_REF
                    or args.event == "push",
                    "F10.10 M3 PUBLIC ACL v2 evidence paths require the protected evidence branch",
                )
                require(
                    actual == F1010_M3_PUBLIC_ACL_V2_EVIDENCE_ALLOWED_STATUSES,
                    "partial or expanded F10.10 M3 PUBLIC ACL v2 evidence delta is forbidden",
                )
                mode = "f1010_m3_public_acl_v2_evidence"
            elif touched_f1010_m3_public_acl_final_readiness:
                require(
                    args.head_ref == F1010_M3_PUBLIC_ACL_FINAL_READINESS_HEAD_REF
                    or args.event == "push",
                    "F10.10 M3 PUBLIC ACL final readiness paths require the protected readiness branch",
                )
                require(
                    actual == F1010_M3_PUBLIC_ACL_FINAL_READINESS_ALLOWED_STATUSES,
                    "partial or expanded F10.10 M3 PUBLIC ACL final readiness delta is forbidden",
                )
                mode = "f1010_m3_public_acl_final_readiness"
            elif touched_g5_trust_live_remediation:
                require(
                    args.head_ref == G5_TRUST_LIVE_REMEDIATION_HEAD_REF
                    or args.event == "push",
                    "G5 PR H paths require the protected trust live remediation branch",
                )
                require(
                    actual == G5_TRUST_LIVE_REMEDIATION_ALLOWED_STATUSES,
                    "partial or expanded G5 PR H delta is forbidden",
                )
                mode = "g5_trust_live_remediation"
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
        elif mode == "f1010_m3_public_acl_preflight_post_merge":
            validate_f1010_m3_public_acl_preflight_post_merge(
                args.repo, args.base_sha, args.head_sha, args.event
            )
        elif mode == "f1010_m3_public_acl_private_preflight_v2_payload":
            validate_f1010_m3_public_acl_private_preflight_v2_payload(
                args.repo, args.base_sha, args.head_sha, args.event
            )
        elif mode == "f1010_m3_public_acl_post_merge_harness":
            validate_f1010_m3_public_acl_post_merge_harness(
                args.repo, args.base_sha, args.head_sha, args.event
            )
        elif mode == "f1010_m3_public_acl_v2_evidence":
            validate_f1010_m3_public_acl_v2_evidence(
                args.repo, args.base_sha, args.head_sha, args.event
            )
        elif mode == "f1010_m3_public_acl_final_readiness":
            validate_f1010_m3_public_acl_final_readiness(
                args.repo, args.base_sha, args.head_sha, args.event
            )
        elif mode == "f1010_h1_ca1_rebaseline":
            validate_f1010_h1_ca1_rebaseline(
                args.repo, args.base_sha, args.head_sha, args.event
            )
        elif mode == "g5_production_readonly":
            validate_g5_production_readonly(
                args.repo, args.base_sha, args.head_sha, args.event
            )
        elif mode == "g5_v2_attribution":
            validate_g5_v2_attribution(
                args.repo, args.base_sha, args.head_sha, args.event
            )
        elif mode == "g5_v2_post_merge":
            validate_g5_v2_post_merge(
                args.repo, args.base_sha, args.head_sha, args.event
            )
        elif mode == "g5_get_only_adapter":
            validate_g5_get_only_adapter(
                args.repo, args.base_sha, args.head_sha, args.event
            )
        elif mode == "g5_operational_runbook":
            validate_g5_operational_runbook(
                args.repo, args.base_sha, args.head_sha, args.event
            )
        elif mode == "g5_e1_hardening":
            validate_g5_e1_hardening(
                args.repo, args.base_sha, args.head_sha, args.event
            )
        elif mode == "g5_e1_wrangler_compat":
            validate_g5_e1_wrangler_compat(
                args.repo, args.base_sha, args.head_sha, args.event
            )
        elif mode == "g5_trust_live_remediation":
            validate_g5_trust_live_remediation(
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
