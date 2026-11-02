# DDL-H3-EDITORIAL-EXPAND-PRO-20261101

Status: APPROVED_FOR_PRODUCTION_DDL

## Campos del workflow (valores propuestos; inactivos mientras DRAFT)

- Ambiente: Supabase Pro `xwhtiqmboljkshrtviyw`.
- Workflow: `DB Sync to Production`, solo desde `main`.
- ID de autorización: `DDL-H3-EDITORIAL-EXPAND-PRO-20261101`.
- Candidato final M: se resolverá con el SHA real de `main` después de la integración protegida.

Authorized manifest: h3-editorial-expand
Authorized payload SHA: 15817342eb0e9a31d3c31cd9dbe84f3c47794f3a
Authorized base SHA: 60ac3ca0fb51635eabe025499865187522c2ac90
Authorized non-auth digest SHA256: sha256:b5c0056773b425a96d9d2605f2a05cca9ea1117fc2da64249f46cb37ac34a56d
H2 expected eligible count: 224
H2 expected cohort digest: sha256:c217dbffc9d50cca0e1f111fcddf1268db9a34e8671a409f3663dcfff1d735e9
Backup/PITR gate: BACKUP_PITR_RUNTIME_GATE_REQUIRED
Pro apply gate: APPLY_REQUIRES_WORKFLOW_DISPATCH_PRODUCTION_ENVIRONMENT_APPROVAL_AND_RUNTIME_BACKUP_PITR
- ID propuesto: `DDL-H3-EDITORIAL-EXPAND-PRO-20261101`.

Los campos `Authorized ...` de arriba contienen valores propuestos para satisfacer los predicados exactos del workflow. No están autorizados ni son efectivos mientras el estado permanezca `DRAFT_NOT_AUTHORIZED`. La decisión humana A debe aprobar este contenido y estos valores exactos. Si se aprueban, el único cambio de estado de este documento será `Status: APPROVED_FOR_PRODUCTION_DDL`; no se editarán otros campos después de esa decisión sin una nueva revisión y aprobación. El conteo/digest H2 proviene de #91 y requiere revalidación antes de apply. Esta aprobación de contenido no sustituye autorización de publicación, workflow_dispatch, aprobación del environment Production ni evidencia vigente de Backup/PITR. Si cambia P, auth_base, digest o alcance, detenerse y revisar el candidato con nueva autorización.

## Manifest cerrado y orden

El workflow valida el orden y SHA-256 de los 31 archivos SQL mediante `scripts/maintenance/pro_h3_migration_manifest.py::validate_h3_manifest_tree`. El inventario completo, en orden exacto y con hash SHA-256 derivado del código versionado en P, está en `manifest-h3-editorial-expand-31.tsv` del paquete externo. Es un auxiliar de revisión; el manifiesto ejecutable sigue siendo el Python integrado. No se incluyen migraciones H2 en este manifest.

## Alcance

El único payload SQL elegible es la tupla cerrada `h3-editorial-expand` de 31 migraciones, con sus bytes y orden fijados por el manifest. El workflow requiere primero el reporte dry-run del estado Pro y valida el manifest cerrado. Si se autoriza `operation=apply`, `db_migrate.py --env pro --manifest h3-editorial-expand` aplica únicamente las migraciones pendientes de esa selección; después el job Verify compara el schema Pro con el contrato H3. La cohorte H2 y su digest son precondiciones verificables, no datos a backfillear por esta autorización.

Quedan excluidos: ejecutar H2 otra vez; backfill o sincronización de datos operativos desde Free; fixtures/seeds de prueba; cuentas/Auth/membresías; Edge Functions; BFF/Pages/Access/Workers/bindings/secrets; habilitar `pgrst.db_pre_request` o crear el espejo del gateway; escritores, schedules, FG1/FG2/FG3; cambios de configuración; y cualquier deploy manual. Esas operaciones requieren sus propios paquetes y JIT.

## Secuencia y gates que siguen pendientes

1. **Decisión de contenido.** La revisión humana debe cubrir exactamente este archivo y sus valores. Mantener `DRAFT_NOT_AUTHORIZED` hasta esa decisión. La aprobación del contenido DDL no autoriza publicarlo, integrarlo, despachar un workflow ni aplicar SQL.
2. **Publicación protegida.** Con autorización de publicación separada, enviar el archivo aprobado por el flujo feature → Desarrollo → Certificación → main. El cambio posterior al payload debe limitarse a esta ruta. Conservar merge commits; no usar squash ni rebase.
3. **Validación de SHAs antes de fijar la ejecución.** Los valores propuestos son `auth_base=60ac3ca0fb51635eabe025499865187522c2ac90` y `P=15817342eb0e9a31d3c31cd9dbe84f3c47794f3a`. Antes del apply, derivar `M` del SHA real de main y validar `auth_base` ancestro de `P`, `P` ancestro de `M`, `diff(P,M)` solo esta autorización, `C=605a6ecca29e20ade8cac3874d380758d18e6a11` ancestro de `M`, y `diff(C,M)` aprobado por el filtro H2. No exigir `C` ancestro de `P`. Si algún SHA, árbol, base o digest difiere, detener y volver a revisar el contenido; estos valores aún son propuesta y no payload congelado.
4. **Report read-only.** Solo después de una integración real a main, solicitar un JIT específico para `operation=report`, manifest `h3-editorial-expand`, `candidate_sha=M` real y `payload_sha=P`. El workflow admite report únicamente desde main y usa el environment Production. El job ejecuta dry-run/lecturas; no aplica SQL. Revisar su resultado de ledger, pendientes, drift y manifest antes de decidir apply. Este reporte no autoriza apply; el propio run `operation=apply` vuelve a ejecutar el report como precondición.
5. **Preflight inmediato de apply.** Releer Pro, ledger, schema y dependencias; revalidar la cohorte H2 (224 y su digest son solo referencia de #91 hasta que se revaliden). Comprobar los controles de Production y el punto de recuperación aceptado. `backup_pitr_verified=true` solo con evidencia vigente y aceptada justo antes del apply; si falta, es insuficiente o hay drift, detenerse sin cambiar flags ni reparar el ledger.
6. **Apply separado.** Requiere JIT propio de workflow/SQL y la aprobación del environment Production para los jobs protegidos. Inputs del dispatch: `operation=apply`, manifest `h3-editorial-expand`, `candidate_sha=M`, `payload_sha=P`, ID exacto, `apply_authorized=true` y `backup_pitr_verified=true` únicamente después de sus aprobaciones/comprobaciones respectivas. En este mismo run, Report vuelve a hacer dry-run; Apply solo corre si el reporte termina sin error y `pending_count > 0`, además de superar los controles de DDL, ancestry, digest, manifest y producción. Si pendientes es cero o cualquier guard falla, el Apply queda bloqueado.
7. **Verify y activación posterior.** El job `Verify target schema` debe pasar después de Apply para acreditar paridad real. Una ejecución separada `operation=verify` requiere autorización propia; en ella Apply es NO-OP y Verify procede solo con cero pendientes. Si Apply falla parcialmente o Verify no alcanza paridad, detener reintentos y activación. Incluso tras Apply + Verify, mantener cerrado el panel Admin hasta resolver los JIT independientes de gateway, Auth/primer Admin, Edge, Pages/BFF/cuotas y el smoke Pro con recuperación.

## Recuperación y detención

Ante drift de manifest/hash, candidato, base/digest, cohorte, ancestry, diff de rutas, estado de ledger, permiso o gate de respaldo: detener sin aplicar ni reparar ledger. Ante fallo parcial del apply: detener toda repetición automática, conservar el estado y auditoría existentes, releer ledger/schema en modo autorizado y preparar un forward-fix/JIT nuevo si hace falta. No borrar snapshots, auditoría ni historial de migraciones ni revertir datos a mano. Si la migración termina pero Verify falla, mantener la aplicación en modo compatible, no abrir el panel Admin ni habilitar escritores; revisar el delta y decidir un arreglo forward-only con autorización propia. Rollback de aplicación es por código/configuración protegidos y no implica rollback destructivo de schema.

## Aprobaciones y autorizaciones que siguen separadas

- Aprobación humana del contenido exacto de esta autorización DDL; hasta entonces, mantener el estado canónico `DRAFT_NOT_AUTHORIZED`.
- Autorización de commit/push/PR protegido para publicar ese archivo a Desarrollo; no incluye review, merge ni promoción.
- Disposición documental específica si el gate integral continúa en FAIL; no se heredan las disposiciones de #524/#525.
- JIT read-only para `operation=report` desde main y su aprobación del environment Production.
- JIT de apply/SQL y aprobación del environment Production; evidencia vigente del punto de recuperación y aprobación de `apply_authorized`/`backup_pitr_verified`.
- Aprobaciones independientes para gateway, Auth/primer Admin/membresía, Edge, Pages/BFF/cuotas, habilitación del panel y smoke Pro con recuperación.

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
| 23 | `20261002_h3_admin_quota_expand.sql` | `d839f7f760bdb12025297a24e09b547cf4f0b5989d3c0142835978083be9bb67` |
| 24 | `20261002_h3_admin_quotas.sql` | `7ea746ca73f2acee31956e59d490083c4fbfcaebf51941d4c6cb52618c906619` |
| 25 | `20261004_h3_admin_queue_first_null_guard.sql` | `012f994af8b44353e385e68b22dc1b15535e31f47f8f990716cbd726f1908711` |
| 26 | `20261004_h3_admin_rpc_signed_gateway_expand.sql` | `e80e236348c2eefe79035c6f6ea5e22bc5dea194555d07a1f1b5a8b41a02876c` |
| 27 | `20261004_h3_admin_rpc_signed_gateway_payload_bound_wrapper.sql` | `c8a69e06e2d1d3a7f5e2245f6fb68ac6220deac3fd0b273edb5bcedafdba81a5` |
| 28 | `20261010_h3_admin_members_service_select.sql` | `6a4d4476e5143537b51390becfe995ca5cb9340ed891c1232e7af2cb1cb9e49c` |
| 29 | `20261025_h3_admin_members_onboarding_forbidden_status.sql` | `11c46cebb640cc6e015926ac7ab6120ca9f0180e43e451909a94ea316960502d` |
| 30 | `20261028_h3_editorial_publication_snapshot.sql` | `2c2bd2238f03a1b5bec2d47fb4bc8a9f0fe1650501378a8ff2dde8746b2a0fef` |
| 31 | `20261028_h3_public_price_projection_empty_price_guard.sql` | `82b8eb0655779f0e82b979cb65a051f2b244b5c4bffb199c5e13c9473132987b` |
