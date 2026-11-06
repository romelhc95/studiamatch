# DDL-H3-EDITORIAL-EXPAND-PRO-20261101

Status: APPROVED_FOR_PRODUCTION_DDL

**Alcance de la aprobación de contenido.** Esta marca se limita a los bytes exactos de esta versión, su manifest y la tupla indicada. No autoriza commit, push, PR, review, merge, workflow dispatch, SQL, configuración, secretos, backup/restore ni deploy. Report, Apply y Verify conservan JIT y gates Production independientes.

## Identidad y campos que valida el workflow

- Proyecto: Supabase Pro `xwhtiqmboljkshrtviyw`.
- Workflow: `.github/workflows/db-sync-to-pro.yml`, manifest H3 permitido solo desde `main`.
- ID/path exigido por el workflow: `DDL-H3-EDITORIAL-EXPAND-PRO-20261101` / `.context/operaciones/ddl_authorizations/DDL-H3-EDITORIAL-EXPAND-PRO-20261101.md`.
- `auth_base` es el baseline explícito del digest de este payload; es un ancestro de P, no su padre directo, y no es main ni pretende cubrir todo el historial desde main.
- El candidato final `M` es el SHA real de main después de las promociones protegidas; todavía no existe para esta tupla y no se anticipa.

Authorized manifest: h3-editorial-expand
Authorized payload SHA: 286469bb45dcc0cb73b70cd25aa1ba71432da86f
Authorized base SHA: 5523c6e7606a9c006020c263b43cf63aa05778f1
Authorized non-auth digest SHA256: sha256:9b831181d423569dead630327ecfea4d7e2c2a001086fab575f10096e1c13436
H2 expected eligible count: 224
H2 expected cohort digest: sha256:c217dbffc9d50cca0e1f111fcddf1268db9a34e8671a409f3663dcfff1d735e9
Backup/PITR gate: BACKUP_PITR_RUNTIME_GATE_REQUIRED
Pro apply gate: APPLY_REQUIRES_WORKFLOW_DISPATCH_PRODUCTION_ENVIRONMENT_APPROVAL_AND_RUNTIME_BACKUP_PITR

## Identidad del payload y cálculo del digest

P=`286469bb45dcc0cb73b70cd25aa1ba71432da86f`, árbol `404a3920f7949087a0dca7ef86da09cc1343535b`; `auth_base`=`5523c6e7606a9c006020c263b43cf63aa05778f1` es ancestro de P (15 commits adelante en la comparación), pero no su padre directo. El digest se reconstruyó con las rutas y objetos GitHub del rango auth_base→P, aplicando el algoritmo literal del workflow: `git diff --name-status -z --find-renames --find-copies auth_base P`, metadatos blob/modo del árbol P, SHA-256 por blob y JSON canónico (`sort_keys=true`, separadores `(',', ':')`). No es un run CI. El valor propuesto es `sha256:9b831181d423569dead630327ecfea4d7e2c2a001086fab575f10096e1c13436`. El rango tiene 20 rutas; los 19 registros no-auth forman el digest y la ruta DDL exacta se excluye. La lista completa sigue; P y el manifest cerrado fijan por separado el payload y los 33 bytes SQL.

| Estado | Ruta |
|---|---|
| modified | `.context/componentes/admin_runtime.md` |
| modified | `.context/componentes/database_migrations.md` |
| modified | `.context/componentes/pruebas_evidencia.md` |
| modified | `.context/database.md` |
| modified | `.context/estado_del_proyecto.md` |
| added | `.context/evidencia/h3req1_first_admin_bootstrap_2026-11-05.md` |
| modified | `.context/indice.md` |
| modified, excluida del digest | `.context/operaciones/ddl_authorizations/DDL-H3-EDITORIAL-EXPAND-PRO-20261101.md` |
| modified | `.context/operaciones/h2_main_production_expand_evidence.json` |
| modified | `.context/trazabilidad/registro_fuentes_componentes.json` |
| modified | `.context/trazabilidad/registro_fuentes_componentes.md` |
| added | `db/migrations/20261105_h3_first_admin_auth_bootstrap.sql` |
| modified | `scripts/maintenance/pro_h3_migration_manifest.py` |
| modified | `scripts/security/protected_path_scope_guard.sh` |
| added | `tests/h3_first_admin_bootstrap_pg17.sh` |
| added | `tests/sql/h3_first_admin_bootstrap_harness.sql` |
| added | `tests/sql/h3_first_admin_bootstrap_pg17_harness.sql` |
| added | `tests/test_h3_first_admin_bootstrap_contract.py` |
| modified | `tests/test_h3_pro_migration_manifest.py` |
| modified | `tests/test_protected_path_scope_guard.sh` |

El candidato H2 verificado `C` es `17d2d9b57fe9e5f32430a83ec843a3c3df9baa3b`; C es ancestro de P (4 commits adelante en la comparación). El flujo protegido debe preservar P y C como ancestros del `M` final; el workflow exige `auth_base`→P, P→M, C→M, el filtro post-C y que `diff(P,M)` contenga exclusivamente este archivo. No se usa squash ni rebase. El archivo DDL que formaba parte de P registraba la aprobación anterior para un payload de 32 migraciones; esa aprobación no cubría el manifest de 33 migraciones de esta versión. Esta versión fue aprobada como contenido exacto y está incorporada en esta ruta canónica. La aprobación cubre el contenido DDL, no la ejecución: SQL, dispatch, backup/restore, configuración y deploy conservan sus autorizaciones independientes.

## Evidencia H2 autenticada — no acredita H3

DB Sync to Production [run #99](https://github.com/romelhc95/studiamatch/actions/runs/42170267471), attempt 1, fue un `workflow_dispatch` de `operation=verify` sobre `ref=certificacion`, candidate/payload `C=17d2d9b57fe9e5f32430a83ec843a3c3df9baa3b`, manifest `h2-expand-compat`, conclusión `SUCCESS`. Report registró 90 migraciones H2 presentes y 0 pendientes. Apply fue NO-OP; el step `Apply migrations to Pro` quedó `SKIPPED`. `Verify target schema` terminó `SUCCESS`. La cohorte fue 224 con digest `sha256:c217dbffc9d50cca0e1f111fcddf1268db9a34e8671a409f3663dcfff1d735e9`; `h2_advisors_reviewed=true` se respaldó con los advisors del run.

Artefacto auténtico `13481325792`; JSON canónico SHA-256 `7082bb5a19f08a10f56cfb0d1198bb38021d575d05e18c144f81e799aed252f9`. La evidencia #99 se promovió a Certificación en #546 y quedó bajo el árbol actual sin cambios de archivos desde P. Acredita H2 en C; no acredita DB33 ni runtime Admin.

## Manifest H3 cerrado, orden y hashes

El workflow y `scripts/maintenance/pro_h3_migration_manifest.py::validate_h3_manifest_tree` validan esta lista exacta y ordenada. No se incluyen migraciones H2.

| # | Migration | SHA-256 |
|---:|---|---|
| 01 | `20260828_h3_admin_auth.sql` | `9a962d01cb3969f6442cac44e3947e7591e93015c4383d245fb3d1f9a1beb314` |
| 02 | `20260828_h3_admin_course_queue_view.sql` | `96f2ffffdbae1ea3f85ff32ade1a2987821c9e837dd771e1a188165cf377caf9` |
| 03 | `20260828_h3_admin_editorial_reader_rpc.sql` | `2783ad358c035db03456b8934e2fa598a4af8272d3715404a8d3c00189e3b63b` |
| 04 | `20260828_h3_admin_editorial_rpc.sql` | `ee8d5b1458da1291ec8b1e4f943728af82cd3cef42a5aee36d490ef8cbda9726` |
| 05 | `20260828_h3_admin_queue_rpc.sql` | `e4fd2ff6733667520916d136eb5d657778c27e5f291e74613a02a595c4bbfb0c` |
| 06 | `20260829_h3_rbac_users.sql` | `b1f96c366f506d52ce11fcf6ef64759ba543af63304da124af0dc10b21fd24c7` |
| 07 | `20260830_h3_expanded_contract.sql` | `387c6247976e92dcbaeff3b53ffa59a9f3f989dd8a50ded1ff61df4721769e27` |
| 08 | `20260902_h3_pr_contract.sql` | `6c22319a66c10e323a6fa4ed1fdbd612a609f8057c6e952a8601cb17c46a4e74` |
| 09 | `20260903_h3_rbac_contract_fix.sql` | `4274e114882fae1deb3039036c612bdc682d59921833c297ed691e87c0440797` |
| 10 | `20260918_h3_invitation_flow_persistence.sql` | `0837d448d8552feb62bb3ab63701123e2449a00ffdcc84dc776849e879030f77` |
| 11 | `20260919_h3_invitation_auth_token_delta.sql` | `701f5c74ff923765fb39efa1605600cb58c93c8caa820b7d49a17fba73e8275d` |
| 12 | `20260920_h3_invitation_edge_runtime.sql` | `46f7d24ac9c8af033ebd84b9ede44c27241382b9cba3fe179ec745b9a25f9188` |
| 13 | `20260921_h3_invitation_onboarding_rpc.sql` | `138e2d3690ec880c51f3834e42fa33ebce0080c6ad9e08b5fe34b8df76de84f2` |
| 14 | `20260924_h3_onboarding_rbac_hardening.sql` | `e466bf1f7968d71ce715724779cc4bd37818f6462021724d01ad48a9bfb1a857` |
| 15 | `20260924_h3_onboarding_rbac_hardening_fix.sql` | `9a5c5d46bca6b4dec438bc6ae63036641423fee95b73e188237ef8ba230b2978` |
| 16 | `20260925_h3_admin_members_onboarding_reader.sql` | `0a9a0b5b694b9caef66da5f6e0d5a45d77bff9029e31b0ede54a5026c14a9d0d` |
| 17 | `20260925_h3_legacy_member_creation_guard.sql` | `bf7b240d76452105753883523428f6cfa4448bdb96c880b2f4aca467db0fe678` |
| 18 | `20260927_h3_admin_queue_facets_filter.sql` | `efabbb35e5fc8b9dc28ce3159ed3ed2328f20c74e4d8e02d2a1a222e8351600b` |
| 19 | `20260927_h3_publication_visibility_contract.sql` | `2b02df3f9ab5736da292d5b8653ca567111cd82705ada182b5baa8085b21e1aa` |
| 20 | `20260928_h3_invitation_accept_email_regex_fix.sql` | `a1b9eaa799d7cc760c84e1df2f66b362ebf1b0556a9f446222f2f9cbea99cd44` |
| 21 | `20261001_h3_course_editorial_audit_availability.sql` | `14e47f4ab4a50382bbea8453b84295bcb2f707e760c8c0a9ae5da4c1f71c3097` |
| 22 | `20261001_h3_invitation_reservation_compensation.sql` | `1001c059b951eaa907016e31be08bef9f3e0a7835f30ea2cac5227a123927270` |
| 23 | `20261002_h3_admin_quota_expand.sql` | `68016d250bfc9ab6fc83cd2c2123a4fcefbbad87732eb1807364b5129facbfad` |
| 24 | `20261002_h3_admin_quotas.sql` | `99cf11b5cac339f5382a5c49d4fd2a5d0439700938a4d78308f57a1a8f8f523e` |
| 25 | `20261004_h3_admin_queue_first_null_guard.sql` | `912b28d476b8bef3246c88c895ed275b85477f57ba15efa47b435c344c778175` |
| 26 | `20261004_h3_admin_rpc_signed_gateway_expand.sql` | `0d20f15140014dd9fe887b95003d4e00b153abad044d5823ec212e24d83ea16e` |
| 27 | `20261004_h3_admin_rpc_signed_gateway_payload_bound_wrapper.sql` | `d708e9de4c3c9c53a72b3f3c189aded683ba3013cb1f63dc6564a7fa6e19f8cc` |
| 28 | `20261010_h3_admin_members_service_select.sql` | `6a4d4476e5143537b51390becfe995ca5cb9340ed891c1232e7af2cb1cb9e49c` |
| 29 | `20261025_h3_admin_members_onboarding_forbidden_status.sql` | `37c14b6d5bc2ca39bbc0487c9c34fca794ab34e5ee024a94df5236e70bd70a7e` |
| 30 | `20261028_h3_editorial_publication_snapshot.sql` | `2c2bd2238f03a1b5bec2d47fb4bc8a9f0fe1650501378a8ff2dde8746b2a0fef` |
| 31 | `20261028_h3_public_price_projection_empty_price_guard.sql` | `82b8eb0655779f0e82b979cb65a051f2b244b5c4bffb199c5e13c9473132987b` |
| 32 | `20261102_h3_legacy_public_withdrawal_guard.sql` | `a719310811dd9b5a992f4a0002931b4a6c9f6a84aac2f84cdd217daead97a7b6` |
| 33 | `20261105_h3_first_admin_auth_bootstrap.sql` | `67045f02b2eb2c846295207b249b5b9014fe50610e162fe7fac4b40c8b7d62d6` |

## Alcance, exclusiones y secuencia

El único payload elegible es `h3-editorial-expand`, las 33 migraciones de la tabla. Report #97 / Apply y Verify #98 correspondieron a la tupla previa de 32 entradas; no sustituyen un Report para este payload. No se anticipa el número de pendientes de la entrada33: un Report posterior al merge real a main debe identificar los nombres actuales. `db_migrate.py --env pro --manifest h3-editorial-expand` aplica solo entradas aún pendientes, respetando las registradas; no se fuerza reaplicación ni se repara manualmente el ledger.

Quedan excluidos: volver a aplicar H2; backfill/sincronización operativa Free→Pro; seeds/fixtures; Auth/cuentas/membresía Admin; Edge; gateway y `pgrst.db_pre_request`; Pages/BFF/Access/Worker/cuotas/bindings/secrets; habilitar Admin; writers, schedules, FG1/FG2/FG3; cambios de configuración y deploy manual. Cada operación conserva autorización independiente.

1. **Contenido.** La aprobación humana aplica solo a los bytes exactos de esta versión. `Status` y cada campo deben coincidir exactamente al instalarlo en la ruta canónica.
2. **Publicación.** Tras aprobación de contenido y publicación por separado, integrar la ruta exacta mediante PR protegido feature/docs→Desarrollo→Certificación→main. Después de P, el único cambio admitido es este archivo. Los checks y reviews deben validar los SHA reales; no hay candidato M anticipado.
3. **Report H3.** Después del merge real a main, solicitar un JIT nuevo para `operation=report`, manifest H3, `candidate_sha=M` y `payload_sha=P`. El job hace preflight/dry-run y no aplica SQL. Revisar pendientes reales, drift, hashes y contrato. Detener ante diferencias; no asumir actuales las 10 faltantes históricas.
4. **Backup/Production.** Inmediatamente antes de Apply, releer el punto de recuperación y comprobar su disponibilidad/aceptación. PITR no está demostrado aquí y no se declara satisfecho. `backup_pitr_verified=true` solo puede enviarse con evidencia actual aceptada. Cada job protegido requiere la aprobación del environment Production para ese run.
5. **Apply.** Requiere un JIT distinto, DDL ID exacto, Report actual sin drift, pendientes exactas, `apply_authorized=true`, backup gate satisfecho y gates Production. El workflow vuelve a hacer Report en ese mismo run y aplica únicamente pendientes del manifest. Cualquier diferencia, fallo o Apply parcial detiene la secuencia; no se reintenta automáticamente ni se repara el ledger.
6. **Verify/compatibilidad.** Exigir `Verify target schema` SUCCESS y paridad antes de declarar H3 schema instalado. Mantener lector y aplicación compatibles; no contraer legacy por el mero Apply.
7. **Activación.** Aun con Verify SUCCESS, Admin permanece cerrado hasta JIT separados y verificación de gateway, Auth/primer Admin, Edge, BFF/Pages y cuotas. El smoke Pro con recuperación es otro gate.
8. **Contract.** Solo después de compatibilidad y aceptación del runtime, autorizar por separado la contracción legacy que corresponda. Aplicación desplegada, migración aplicada, funcionalidad habilitada y cierre son estados distintos.

## Recuperación y detención

Ante drift de candidate/payload/base/digest, manifest/hash, C/ancestry, pendientes, cohort, permisos o archivo de autorización: no iniciar Apply. Ante error parcial de Apply, detener todo reintento, conservar schema, ledger, auditoría y snapshots, obtener lecturas autorizadas y preparar corrección forward-only con nuevo JIT. No borrar historial ni ejecutar rollback destructivo de DB. Si Verify falla, mantener el código compatible y Admin cerrado; recuperar la aplicación mediante el flujo protegido si es necesario. La aprobación de este contenido no acepta ni verifica un backup ni autoriza restaurarlo. La copia física observada el 2026-11-04 00:57:02 Lima fue aceptada solo condicionada a relectura inmediata; no es evidencia vigente para un futuro Apply.

## Decisiones que permanecen separadas

- Publicar el paquete y aprobar/mergear sus PRs protegidos.
- H3 Report-only desde main y sus gates Production.
- H3 Apply/SQL, DDL ID y su gate Production, con backup vigente.
- Verify si ocurre en un run distinto, y sus gates Production.
- Configuración de gateway, Edge, Auth/primer Admin, Pages/BFF/cuotas y apertura de Admin.
- Smoke Pro, recuperación y posterior contract.
