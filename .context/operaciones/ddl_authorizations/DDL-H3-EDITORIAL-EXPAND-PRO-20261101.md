# DDL-H3-EDITORIAL-EXPAND-PRO-20261101

Status: APPROVED_FOR_PRODUCTION_DDL

**Alcance de la aprobación de contenido.** Esta marca se limita a los bytes exactos de esta versión, su manifest y la tupla indicada. No autoriza commit, push, PR, review, merge, workflow dispatch, SQL, configuración, secretos, backup/restore ni deploy. Report, Apply y Verify conservan JIT y gates Production independientes.

## Identidad y campos que valida el workflow

- Proyecto: Supabase Pro `xwhtiqmboljkshrtviyw`.
- Workflow: `.github/workflows/db-sync-to-pro.yml`, manifest H3 permitido solo desde `main`.
- ID/path exigido por el workflow: `DDL-H3-EDITORIAL-EXPAND-PRO-20261101` / `.context/operaciones/ddl_authorizations/DDL-H3-EDITORIAL-EXPAND-PRO-20261101.md`.
- `auth_base` es el corte real de Desarrollo antes de preparar la evidencia; no es main ni afirma cubrir todo el historial desde main.
- El candidato final `M` es el SHA real de main después de las promociones protegidas; todavía no existe para esta tupla y no se anticipa.

Authorized manifest: h3-editorial-expand
Authorized payload SHA: 9a79f4096a8af617e961d3494e2ec46ca050c997
Authorized base SHA: 5523c6e7606a9c006020c263b43cf63aa05778f1
Authorized non-auth digest SHA256: sha256:7d5d69873d842f5d309480d70072ef3ac9a582476d565664c3c10c08b253bbe8
H2 expected eligible count: 224
H2 expected cohort digest: sha256:c217dbffc9d50cca0e1f111fcddf1268db9a34e8671a409f3663dcfff1d735e9
Backup/PITR gate: BACKUP_PITR_RUNTIME_GATE_REQUIRED
Pro apply gate: APPLY_REQUIRES_WORKFLOW_DISPATCH_PRODUCTION_ENVIRONMENT_APPROVAL_AND_RUNTIME_BACKUP_PITR

## Identidad del payload y cálculo del digest

P=`9a79f4096a8af617e961d3494e2ec46ca050c997`, árbol `246bd33e890e6e8ea929139acb67911bc106ace4`; `auth_base`=`5523c6e7606a9c006020c263b43cf63aa05778f1` es su padre directo y ancestro. El digest fue calculado en Docker con la misma secuencia del workflow: `git diff --name-status -z --find-renames --find-copies auth_base P`, metadatos de blob/modo del árbol P, SHA-256 por blob y JSON canónico con `sort_keys=true` y separadores `(',', ':')`. El resultado es `sha256:7d5d69873d842f5d309480d70072ef3ac9a582476d565664c3c10c08b253bbe8`. El diferencial auth_base→P consta solo de seis documentos/registro bajo `.context`; el digest cubre ese delta no-auth y no pretende resumir todo lo heredado desde main. El SHA P y el manifest cerrado fijan por separado el payload completo y los 32 bytes SQL.

El H2 candidate verificado `C` es `7e6c1c1a288706afcfac405df1bb6eabaa9a64e5`. No se exige `C` ancestro de P. El flujo protegido debe preservar P y C como ancestros del `M` final; el workflow exige `auth_base`→P, P→M, C→M, el filtro post-C y que `diff(P,M)` contenga exclusivamente este archivo. No se usa squash ni rebase. El DDL actual en el padre P tiene una aprobación histórica para otra tupla; esa aprobación no se transfiere. Esta nueva versión en la misma ruta exacta sustituye la tupla anterior solo después de decisión humana sobre estos bytes.

## Evidencia H2 autenticada — no acredita H3

DB Sync to Production [run #96](https://github.com/romelhc95/studiamatch/actions/runs/41749790054), attempt 1, fue `workflow_dispatch`, ref `certificacion`, candidate/payload `7e6c1c1a288706afcfac405df1bb6eabaa9a64e5`, manifest `h2-expand-compat`, conclusión `SUCCESS`. Report fue dry-run con cero pendientes H2; Apply finalizó `SUCCESS` como NO-OP y `Apply migrations to Pro` quedó `SKIPPED`; `Verify target schema` terminó `SUCCESS`. La cohorte verificada fue 224 con digest `sha256:c217dbffc9d50cca0e1f111fcddf1268db9a34e8671a409f3663dcfff1d735e9` y los advisors se marcaron revisados, sin nuevos HIGH/CRITICAL/ERROR según el JSON auténtico.

Artefacto GitHub `13286019927`, ZIP SHA-256 `8f24ba5adaefd627f60ebdcaadf424c37cfe6a1ed5a405f6803d96b886fd4a8a`. El miembro `h2-production-expand-verify-evidence.json` y el archivo canónico se compararon byte por byte; SHA-256 `c30895c94edd054fd2500293c417021c643f906558de184a1a49021e2cd2a59c`. El esquema histórico conserva `operation=apply`; el evento y jobs reales prueban que el dispatch fue `verify`, Apply NO-OP y Verify SUCCESS. Esta evidencia verifica H2 en C, no el ledger, instalación ni runtime H3 Pro.

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

## Alcance, exclusiones y secuencia

El único payload elegible es `h3-editorial-expand`, las 32 migraciones de la tabla. `db_migrate.py --env pro --manifest h3-editorial-expand` aplica solo entradas pendientes tras un Report nuevo; no se reaplican ni reparan manualmente entradas existentes. La lectura histórica de H3 (22/32 al 2026-11-03 14:24 Lima) no es resultado vigente ni fija el próximo Apply.

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

Ante drift de candidate/payload/base/digest, manifest/hash, C/ancestry, pendientes, cohort, permisos o archivo de autorización: no iniciar Apply. Ante error parcial de Apply, detener todo reintento, conservar schema, ledger, auditoría y snapshots, obtener lecturas autorizadas y preparar corrección forward-only con nuevo JIT. No borrar historial ni ejecutar rollback destructivo de DB. Si Verify falla, mantener el código compatible y Admin cerrado; recuperar la aplicación mediante el flujo protegido si es necesario. La aprobación de este contenido no acepta ni verifica un backup ni autoriza restaurarlo.

## Decisiones que permanecen separadas

- Publicar el paquete y aprobar/mergear sus PRs protegidos.
- H3 Report-only desde main y sus gates Production.
- H3 Apply/SQL, DDL ID y su gate Production, con backup vigente.
- Verify si ocurre en un run distinto, y sus gates Production.
- Configuración de gateway, Edge, Auth/primer Admin, Pages/BFF/cuotas y apertura de Admin.
- Smoke Pro, recuperación y posterior contract.
