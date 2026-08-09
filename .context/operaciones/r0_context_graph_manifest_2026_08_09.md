# R0-CONTEXT-GRAPH-F10.9-2026-08-09

| Campo | Valor |
|---|---|
| Gate | [G0-R0-F10.9](./g0_r0_reconciliacion_f10_9.md) |
| Freeze | [R0-FREEZE](./r0_freeze_f10_9_2026_08_09.md) |
| Estado | `RECONCILED_LOCAL_SECURITY_REVIEW_PENDING` |
| Autoriza merge | `NO` |
| Autoriza CA2 | `NO` |

## Before Y After

```text
before_markdown_files = 11
before_local_links = 135
before_broken_references = 78
before_unique_missing_targets = 38

reconciled_content_markdown_files = 39
reconciled_content_local_links = 337
final_graph_markdown_files = 40
final_graph_local_links = 340
after_broken_references = 0
after_unknown_provenance_holds = 0
active_ca2_documents_added = 0
```

La restauracion transitiva inicial produjo `42` documentos, `500` enlaces y
`135` enlaces rotos. La reconciliacion retiro hyperlinks ausentes conservando su
texto visible:

| Pass | Links retirados | Digest SHA-256 del inventario ordenado |
|---|---:|---|
| `REMOVE_STALE_LINK-1` | `135` | `de63f9f66866017d2ec3c0a19b01c14da8915bf9e4dc04a9e7365f241f6f6290` |
| `REMOVE_STALE_LINK-2` | `18` | `ab342dc1bf02a7309d51acaaf846a93b67ce8c2a077afffdab8ce2f4eea0042e` |

## Fuentes CA1 Restauradas Bajo Revision

| Path | Source commit | Source blob |
|---|---|---|
| `.context/00_INDICE.md` | `ae0f99490146211d41dc88bff18e2137247b54f9` | `41ff16e37780790d4e4fc14027968fd69a2d84cf` |
| `.context/arquitectura_pipeline.md` | `e866ce9a2acecc95a14a1ec2f766f91a084e1566` | `f49ceebc8a7f2ab466bfef91f1059073a11b0aac` |
| `.context/backlog_tareas/req_est_001_sprint_1/_index.md` | `e866ce9a2acecc95a14a1ec2f766f91a084e1566` | `7d6facfcb1bc453934d47e61e1ff01e411ca2ab0` |
| `.context/backlog_tareas/req_est_001_sprint_1/adenda_cliente_001_sanitizada.md` | `e866ce9a2acecc95a14a1ec2f766f91a084e1566` | `99c4139ad066a1e8f8602ac0e51b6bb4aedcb513` |
| `.context/decisiones/ADR-0003_taxonomia_macrofases_subfases.md` | `e866ce9a2acecc95a14a1ec2f766f91a084e1566` | `19695eca231411b0d2b1311e935f4664be1152b4` |
| `.context/decisiones/ADR-0007_desviacion_canary_certification_f9_9.md` | `fa52ea6bdc2af5febc04b22f3d020911e3304ccd` | `6dc0e6ebace5c9ad36e8961218007f7cf8e002fe` |
| `.context/decisiones/ADR-0009_reconciliacion_entrega_tecnica_post_main_f10_7.md` | `fc1461d427010b446b7bd59e09c4f97c1d7032e0` | `bd6f0fdfcbb5b4ddfd5feb2c3e34bf77756dc628` |
| `.context/operaciones/matriz_adopcion_db.md` | `fc1461d427010b446b7bd59e09c4f97c1d7032e0` | `ad248d4d60d197ffce2b9beb43504bbc2876a146` |
| `.context/sistema_db_supabase.md` | `e866ce9a2acecc95a14a1ec2f766f91a084e1566` | `9be5cd667fb08dee874f5ef055103396de14066f` |

Las dos fuentes DB fueron tombstoneadas en el target reconciliado como
`SUPERSEDED_BY_F10_8`; sus source blobs no se presentan como estado vigente.

## Antecedentes Historicos Restaurados

Estos blobs se autoidentifican como tracking, superseded, consumed o no
ejecutables. No son autoridad viva.

| Path | Source commit | Source blob |
|---|---|---|
| `.context/backlog_tareas/req_est_001_sprint_1/backlog_f9_5_known_findings.md` | `e866ce9a2acecc95a14a1ec2f766f91a084e1566` | `f63227097f7b4ad452c625a7fe21aa533c7b2528` |
| `.context/backlog_tareas/req_est_001_sprint_1/backlog_seguridad_leads_email.md` | `e866ce9a2acecc95a14a1ec2f766f91a084e1566` | `041c75c9e4227229c3500ed6c980393616c24f41` |
| `.context/backlog_tareas/req_est_001_sprint_1/seguimiento_detallado_hito_1.md` | `e866ce9a2acecc95a14a1ec2f766f91a084e1566` | `68b00bde789093b8c55bdce0efb4c7bcf302be23` |
| `.context/decisiones/ADR-0004_simplificacion_contractual_hito1.md` | `e866ce9a2acecc95a14a1ec2f766f91a084e1566` | `a5247b0d6baac33bbbf314edf3d1b5f577bc0fa9` |
| `.context/decisiones/ADR-0005_corte_seguridad_funcionalidad_estabilidad_hito1.md` | `e866ce9a2acecc95a14a1ec2f766f91a084e1566` | `fd1a0ee8ecc3e9721704ae47033ddcbfdc6688e0` |
| `.context/decisiones/ADR-0008_rebaseline_f10_7_gate_reconstruction.md` | `fc1461d427010b446b7bd59e09c4f97c1d7032e0` | `45f60e0bd3e2ef4ec3f2ba580bdf99759011dfc5` |
| `.context/estimaciones/est_001.md` | `e866ce9a2acecc95a14a1ec2f766f91a084e1566` | `9c0cb6b384a9a4727a26738488b6c31d7837057c` |
| `.context/operaciones/plan_corte_seguridad_funcionalidad_estabilidad_hito1.md` | `e866ce9a2acecc95a14a1ec2f766f91a084e1566` | `1878ca943bd7ac29877013bbbd60799032d55999` |
| `.context/operaciones/plan_simplificado_hito1.md` | `e866ce9a2acecc95a14a1ec2f766f91a084e1566` | `8621de4e38f1f7a3f87d4b2ac391371c56a84d36` |
| `.context/operaciones/pr_o_f9_7_successor_private_executor.md` | `e866ce9a2acecc95a14a1ec2f766f91a084e1566` | `a4aeb16ed778ca34b0f3bbec66b54b108fcf2729` |
| `.context/operaciones/pr_o_f9_7_v3_hold.md` | `e866ce9a2acecc95a14a1ec2f766f91a084e1566` | `5c26a1e9a0ec88c8cee191f7b490143175f557ea` |
| `.context/operaciones/precertificacion_hito1_f9.md` | `e866ce9a2acecc95a14a1ec2f766f91a084e1566` | `01c978d3decc922bef2cd9a67ad23ff3e9141262` |
| `.context/operaciones/preflight_free_f9_4.md` | `e866ce9a2acecc95a14a1ec2f766f91a084e1566` | `7d2a8683d7f22069ec0ce6055d80f626a9dfd72a` |
| `.context/operaciones/preflight_free_f9_5.md` | `e866ce9a2acecc95a14a1ec2f766f91a084e1566` | `1d594630ecef18e070ef723fcf40cbdeef7a7fa3` |
| `.context/operaciones/promocion_hito1_f10.md` | `e866ce9a2acecc95a14a1ec2f766f91a084e1566` | `bfe96c2419cff03e39c7488b5d6885607cb14bbf` |
| `.context/operaciones/qa_desviacion_f9_9.md` | `eaf10d832fc4f0d342887f7465a82d4e60361266` | `aa7f2a886818fe4ee91cde71baee136f07f35ad0` |
| `.context/operaciones/qa_desviacion_f9_9_resultado.md` | `eaf10d832fc4f0d342887f7465a82d4e60361266` | `c4de82a9395e04fdb00d0d75cb1cc642bdaa50c3` |

Tres antecedentes inicialmente considerados fueron excluidos tras security
review porque conservaban estado operativo stale: `atestacion_origen_acl_f9_7`,
`certificacion_hito1_f8` y `cierre_h00_f9_6`.

## Target Blobs Reconciliados

Estos blobs incluyen `REMOVE_STALE_LINK` y, donde corresponde, tombstone de
autoridad obsoleta. Son los `proposed_target_blob` que el boundary debe congelar.

| Path | Reconciled blob | Accion |
|---|---|---|
| `.context/00_INDICE.md` | `0f05d40caa1b78f62f236c6200c04b178c3fb177` | `RESTORE_CA1_REVIEWED+REMOVE_STALE_LINK+REPOINT_DB_AUTHORITY` |
| `.context/arquitectura_pipeline.md` | `88f2e44d409ccd61203147d3db50634057d6c60c` | `RESTORE_CA1_REVIEWED+REMOVE_STALE_LINK` |
| `.context/backlog_tareas/req_est_001_sprint_1/_index.md` | `1d15276b5692e08ae6aad8edcc3800fca217a712` | `RESTORE_CA1_REVIEWED+REMOVE_STALE_LINK` |
| `.context/backlog_tareas/req_est_001_sprint_1/adenda_cliente_001_sanitizada.md` | `c7d1d25c2dcaff656fabb46fde369f219d24bdb5` | `RESTORE_CA1_REVIEWED+REMOVE_STALE_LINK` |
| `.context/decisiones/ADR-0003_taxonomia_macrofases_subfases.md` | `b8b5d49c0eb9338b6bfe9849f21f4e01546b1304` | `RESTORE_CA1_REVIEWED+REMOVE_STALE_LINK` |
| `.context/decisiones/ADR-0007_desviacion_canary_certification_f9_9.md` | `e466a172ee761eec555259a506bdb042dafd339b` | `RESTORE_CA1_REVIEWED+REMOVE_STALE_LINK` |
| `.context/decisiones/ADR-0009_reconciliacion_entrega_tecnica_post_main_f10_7.md` | `bd6f0fdfcbb5b4ddfd5feb2c3e34bf77756dc628` | `RESTORE_CA1_REVIEWED` |
| `.context/operaciones/matriz_adopcion_db.md` | `d2f89c062bd08e3cf99117b3518c6a673967b06f` | `RESTORE+TOMBSTONE_SUPERSEDED_F10_8+REMOVE_STALE_LINK` |
| `.context/sistema_db_supabase.md` | `5573d16c193d3f07e8e3a7a10088b77a4b649a3c` | `RESTORE+TOMBSTONE_SUPERSEDED_F10_8+REMOVE_STALE_LINK` |
| `.context/backlog_tareas/req_est_001_sprint_1/backlog_f9_5_known_findings.md` | `f197a2e2da4afdbf283b3e35d14c5c44536f74aa` | `RESTORE_HISTORICAL+REMOVE_STALE_LINK` |
| `.context/backlog_tareas/req_est_001_sprint_1/backlog_seguridad_leads_email.md` | `e7cb201edfee6194d2062835636034dd7c5a2544` | `RESTORE_HISTORICAL+REMOVE_STALE_LINK` |
| `.context/backlog_tareas/req_est_001_sprint_1/seguimiento_detallado_hito_1.md` | `361b0e821d63c678bb4062df25dea5ce266b30ec` | `RESTORE_HISTORICAL+REMOVE_STALE_LINK` |
| `.context/decisiones/ADR-0004_simplificacion_contractual_hito1.md` | `4854f63e3b4a1bcb93fac61a9859fd253f4db3a2` | `RESTORE_HISTORICAL+REMOVE_STALE_LINK` |
| `.context/decisiones/ADR-0005_corte_seguridad_funcionalidad_estabilidad_hito1.md` | `26ca8bcaea61229dcce829a8f4586c4bbbfde10e` | `RESTORE_HISTORICAL+REMOVE_STALE_LINK` |
| `.context/decisiones/ADR-0008_rebaseline_f10_7_gate_reconstruction.md` | `45f60e0bd3e2ef4ec3f2ba580bdf99759011dfc5` | `RESTORE_HISTORICAL` |
| `.context/estimaciones/est_001.md` | `13f91a8e5d8d692342d05ec14deffac613ca391a` | `RESTORE_HISTORICAL+REMOVE_STALE_LINK` |
| `.context/operaciones/plan_corte_seguridad_funcionalidad_estabilidad_hito1.md` | `f7421172969e819912b5b89dddffbd539bd32d21` | `RESTORE_HISTORICAL+REMOVE_STALE_LINK` |
| `.context/operaciones/plan_simplificado_hito1.md` | `4549a0316f24fec55200e9b651d4fc0f9986d794` | `RESTORE_HISTORICAL+REMOVE_STALE_LINK` |
| `.context/operaciones/pr_o_f9_7_successor_private_executor.md` | `31e098b5c94daae9f2162f7ef33de8e10c333c87` | `RESTORE_HISTORICAL+REMOVE_STALE_LINK` |
| `.context/operaciones/pr_o_f9_7_v3_hold.md` | `b032f5f871a611c7229f02ea8ba84048013d6e58` | `RESTORE_HISTORICAL+REMOVE_STALE_LINK` |
| `.context/operaciones/precertificacion_hito1_f9.md` | `61cc2425daeb961837004a8344ec98e09e6067ed` | `RESTORE_HISTORICAL+REMOVE_STALE_LINK` |
| `.context/operaciones/preflight_free_f9_4.md` | `fbdcbe77349ab6e071a15ba0048e01788b8262bd` | `RESTORE_HISTORICAL+REMOVE_STALE_LINK` |
| `.context/operaciones/preflight_free_f9_5.md` | `2b209a41fc97f8c53504054229b6a8df76ef143a` | `RESTORE_HISTORICAL+REMOVE_STALE_LINK` |
| `.context/operaciones/promocion_hito1_f10.md` | `fe8167eb168e929e510300228962d2cec8b41e9c` | `RESTORE_HISTORICAL+REMOVE_STALE_LINK` |
| `.context/operaciones/qa_desviacion_f9_9.md` | `aa7f2a886818fe4ee91cde71baee136f07f35ad0` | `RESTORE_HISTORICAL` |
| `.context/operaciones/qa_desviacion_f9_9_resultado.md` | `c4de82a9395e04fdb00d0d75cb1cc642bdaa50c3` | `RESTORE_HISTORICAL` |

## CA2 No Importado

Los siguientes targets permanecen fuera del candidate; sus hyperlinks ausentes
se convirtieron a texto, preservando IDs/resumen sin importar contenido activo:

```text
tarea_002_hito_2.md
tarea_004_hito_4.md
anexo_h1_ca2_seguridad_rls.md
certificacion_hito1_f9.md
cierre_definitivo_f9_7.md
gate_b_f9_7.md
reconciliacion_db_as_code_f6.md
remediacion_gate_b_f9_7.md
remediacion_trigger_f9_7.md
```

## Stop Conditions

- Cualquier enlace local roto after.
- Un antecedente restaurado presentado como autoridad viva.
- Un blob sin provenance o distinto al manifest.
- Contenido CA2 activo, secreto o identificador operativo nuevo.
- Cambio fuera de `.context` durante esta reconciliacion.

Este manifest no autoriza merge ni cambia evidencias H1.
