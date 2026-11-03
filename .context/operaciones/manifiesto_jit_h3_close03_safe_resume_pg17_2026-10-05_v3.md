# Propuesta JIT v3 — safe-suspend/resume persistente en PG17 — 2026-10-05

**Estado:** `PREPARADO_NO_APROBADO`; no autoriza crear contenedores ni ejecutar SQL.
Alcance: reevaluar el subgate SQL H3-CLOSE-03 sobre un PostgreSQL 17 desechable nuevo,
con captura ACL persistente, recuperación fail-closed y reconexión real entre sesiones.
No es el drill integrado Pages/workerd + Edge + PG17 y no cierra H3-CLOSE-03.

## Cambio de candidato y vigencia de evidencia

Rama `feat/h3req1-sync-20261002`; baseline `HEAD=4eb4d877a50b012bb630a129bd0c74482c33be9c`.
La autoría local se autorizó solo para `db/rollback/h3req1_safe_suspend.sql`, el nuevo
`db/rollback/h3req1_safe_resume.sql` y `tests/sql/h3_safe_suspend_harness.sql`.
No se ha ejecutado SQL ni se ha conectado al PG17 preservado.

- Se conserva **H3-CLOSE-02/JIT v4 PASS**: sus 72 inputs no pertenecientes a C03 no
  cambiaron. No se repiten esos gates.
- El PASS histórico del **safe-suspend/JIT v2** permanece en su manifiesto para los
  bytes que probó, pero deja de ser evidencia del candidato actual: cambiaron sus dos
  fuentes y se agregó `safe_resume`. El cierre transitivo actual es 41 inputs: 2 cambiados,
  1 agregado, 0 removidos y 0 includes ausentes.
- El nuevo harness re-ejecuta en el PG17 limpio los tres harnesses de bootstrap H2/H3,
  cuotas y gateway porque sus migraciones/fixtures son prerrequisito del test C03. Es una
  repetición de preparación en otro contenedor, **no** se presentará como nuevo PASS de
  H3-CLOSE-02 ni de esos gates. Si no se autoriza esa preparación completa, detenerse:
  el PG17 parcial previo está preservado y no se reutiliza.

## Cambios revisados estáticamente

- `safe_suspend.sql` limita la transición a las diez firmas exactas y ACL explícitas
  autenticadas/service_role del baseline; rechaza overloads, PUBLIC/anon, roles/grantors
  no allowlisted, drift de propietario o ACL. Captura el snapshot privado persistente en
  la misma transacción que revoca los iniciadores y el dispatcher firmado.
- Captura huella SHA-256 del DB, usuario, instante UTC, roles/firmas, ACL original y estado
  suspendido; verifica tabla, ACL privada, índice de snapshot único y estado activo antes
  de tratar un reintento como idempotente.
- `safe_resume.sql` acepta únicamente la captura del mismo DB/usuario, verifica la ACL
  suspendida exacta y el contrato allowlisted, restaura grants explícitos y deja la base
  sin cambios si cualquier comprobación falla. No altera bindings/flags Pages ni Edge.
- El inventario deja ejecutables los finalizadores service-only de invitación para
  completar/fallar/reconciliar trabajo in-flight. También sigue ejecutable
  `admin_invitation_request_admit`, que registra solo eventos de cuota y se llama antes
  del guard `ADMIN_INVITE_SAFE_SUSPEND`; no puede reservar invitación ni invocar Auth.
  El futuro drill integrado debe comprobar ese límite y cuantificar esos eventos. Si el
  contrato exige cero escrituras de cuota durante suspensión, detenerse y pedir un diseño
  y autorización Edge aparte antes de cerrar C03.
- Las huellas SHA-256 son checks de consistencia, no HMAC: no protegen contra compromiso
  del propietario/superusuario de la DB, que podría cambiar ACL directamente. El threat
  model del subgate cubre drift accidental y roles API sin privilegio de escritura; no
  promete defensa frente a un operador DB privilegiado.
- El harness conserva los checks de no pérdida, no bypass, nonce sin consumir y
  finalizadores in-flight; reconecta con `\connect`, altera una ACL de forma sintética,
  exige que el resume real falle con SQLSTATE específico `H3D01`, revierte esa alteración
  fixture y ejecuta el resume persistente dos veces para comprobar idempotencia. La última
  aserción compara la captura reanudada y los permisos.
- Revisión estática: ambos mapas de ACL tienen diez entradas idénticas; cierre `\ir`
  recursivo **41/41 archivos**, 0 ausentes; dollar quotes `$$` balanceados y newline final en
  los tres archivos editados. Esto no demuestra sintaxis/ejecución SQL.

## Cierre transitivo del candidato — SHA-256

Recalcular las 41 rutas antes de cualquier ejecución. Cualquier diferencia, ruta ausente,
cambio de rama/HEAD inesperado o contenedor preexistente con el nombre propuesto detiene
la operación y requiere otro manifiesto/aprobación. Los hashes identifican los bytes de
SQL; no congelan el WIP completo ni autorizan su ejecución.

| Ruta | SHA-256 |
|---|---|
| `db/migrations/20260827_h2_pro_backfill_editorial_state.sql` | `0118a17cf1e9fbfa001f67d07e92770f5a8787a14722e1dee992592f3bcee3c3` |
| `db/migrations/20260827_h2_pro_capture_legacy_cohort.sql` | `4212a94e59df8a0702176265848f16746486299852ab94267247f26f50e393f9` |
| `db/migrations/20260827_h2_pro_contract_legacy_cohort.sql` | `62db91e741ab448ec057cc7cea41bb813535f26b762d38ef66a120210fc20c28` |
| `db/migrations/20260827_h2_pro_contract_public_reader.sql` | `86ce2998bdfb2e0a91ebc9f7ec50f88b285de60ed8dbe538ead21611df132da3` |
| `db/migrations/20260827_h2_pro_expand_schema_compat.sql` | `e3b8665e0ceafc590a41390d3c206fc1e9846332ddd5cf9385f0a704ffabb577` |
| `db/migrations/20260827_h2_pro_rollback_public_reader_contract.sql` | `b0ad29f6bf092b723936589d5902ee1081499a1278d054320f35933fe2a46f40` |
| `db/migrations/20260827_h2_pro_seed_editorial_field_definitions.sql` | `ecf46e71b6b261fdba8a8fee0cab76a3d4d57eefb1b097f4496bac9c717f2d17` |
| `db/migrations/20260828_h3_admin_auth.sql` | `9a962d01cb3969f6442cac44e3947e7591e93015c4383d245fb3d1f9a1beb314` |
| `db/migrations/20260828_h3_admin_course_queue_view.sql` | `96f2ffffdbae1ea3f85ff32ade1a2987821c9e837dd771e1a188165cf377caf9` |
| `db/migrations/20260828_h3_admin_editorial_reader_rpc.sql` | `2783ad358c035db03456b8934e2fa598a4af8272d3715404a8d3c00189e3b63b` |
| `db/migrations/20260828_h3_admin_editorial_rpc.sql` | `ee8d5b1458da1291ec8b1e4f943728af82cd3cef42a5aee36d490ef8cbda9726` |
| `db/migrations/20260828_h3_admin_queue_rpc.sql` | `e4fd2ff6733667520916d136eb5d657778c27e5f291e74613a02a595c4bbfb0c` |
| `db/migrations/20260829_h3_rbac_users.sql` | `b1f96c366f506d52ce11fcf6ef64759ba543af63304da124af0dc10b21fd24c7` |
| `db/migrations/20260830_h3_expanded_contract.sql` | `387c6247976e92dcbaeff3b53ffa59a9f3f989dd8a50ded1ff61df4721769e27` |
| `db/migrations/20260902_h3_pr_contract.sql` | `6c22319a66c10e323a6fa4ed1fdbd612a609f8057c6e952a8601cb17c46a4e74` |
| `db/migrations/20260903_h3_rbac_contract_fix.sql` | `4274e114882fae1deb3039036c612bdc682d59921833c297ed691e87c0440797` |
| `db/migrations/20260918_h3_invitation_flow_persistence.sql` | `0837d448d8552feb62bb3ab63701123e2449a00ffdcc84dc776849e879030f77` |
| `db/migrations/20260919_h3_invitation_auth_token_delta.sql` | `701f5c74ff923765fb39efa1605600cb58c93c8caa820b7d49a17fba73e8275d` |
| `db/migrations/20260920_h3_invitation_edge_runtime.sql` | `46f7d24ac9c8af033ebd84b9ede44c27241382b9cba3fe179ec745b9a25f9188` |
| `db/migrations/20260921_h3_invitation_onboarding_rpc.sql` | `138e2d3690ec880c51f3834e42fa33ebce0080c6ad9e08b5fe34b8df76de84f2` |
| `db/migrations/20260924_h3_onboarding_rbac_hardening.sql` | `e466bf1f7968d71ce715724779cc4bd37818f6462021724d01ad48a9bfb1a857` |
| `db/migrations/20260924_h3_onboarding_rbac_hardening_fix.sql` | `9a5c5d46bca6b4dec438bc6ae63036641423fee95b73e188237ef8ba230b2978` |
| `db/migrations/20260925_h3_admin_members_onboarding_reader.sql` | `0a9a0b5b694b9caef66da5f6e0d5a45d77bff9029e31b0ede54a5026c14a9d0d` |
| `db/migrations/20260925_h3_legacy_member_creation_guard.sql` | `bf7b240d76452105753883523428f6cfa4448bdb96c880b2f4aca467db0fe678` |
| `db/migrations/20260927_h3_admin_queue_facets_filter.sql` | `efabbb35e5fc8b9dc28ce3159ed3ed2328f20c74e4d8e02d2a1a222e8351600b` |
| `db/migrations/20260927_h3_publication_visibility_contract.sql` | `2b02df3f9ab5736da292d5b8653ca567111cd82705ada182b5baa8085b21e1aa` |
| `db/migrations/20260928_h3_invitation_accept_email_regex_fix.sql` | `a1b9eaa799d7cc760c84e1df2f66b362ebf1b0556a9f446222f2f9cbea99cd44` |
| `db/migrations/20261001_h3_course_editorial_audit_availability.sql` | `590d4c6e177ded33384b746f187a3476af663db6aef8d5c789d4d7bcad093717` |
| `db/migrations/20261001_h3_invitation_reservation_compensation.sql` | `1001c059b951eaa907016e31be08bef9f3e0a7835f30ea2cac5227a123927270` |
| `db/migrations/20261002_h3_admin_quota_expand.sql` | `d839f7f760bdb12025297a24e09b547cf4f0b5989d3c0142835978083be9bb67` |
| `db/migrations/20261002_h3_admin_quotas.sql` | `7ea746ca73f2acee31956e59d490083c4fbfcaebf51941d4c6cb52618c906619` |
| `db/migrations/20261004_h3_admin_queue_first_null_guard.sql` | `012f994af8b44353e385e68b22dc1b15535e31f47f8f990716cbd726f1908711` |
| `db/migrations/20261004_h3_admin_rpc_signed_gateway_expand.sql` | `e80e236348c2eefe79035c6f6ea5e22bc5dea194555d07a1f1b5a8b41a02876c` |
| `db/migrations/20261004_h3_admin_rpc_signed_gateway_payload_bound_wrapper.sql` | `c8a69e06e2d1d3a7f5e2245f6fb68ac6220deac3fd0b273edb5bcedafdba81a5` |
| `db/rollback/h3req1_safe_resume.sql` | `d47579a8e7c4fbf005b8bcca4b2261aa09a311b2606f167a7ee099b5b3339cd8` |
| `db/rollback/h3req1_safe_suspend.sql` | `5236371a8bb2beec5434b49f60bf56e46509b58408a81ea471e6297b41769b2d` |
| `tests/sql/h2_pro_pg17_harness.sql` | `676a149546d8f3ff045d7d4332eedeefe343a8ef25375cd72e906ed6d1f26bfe` |
| `tests/sql/h3_admin_quota_harness.sql` | `890464e81ae5bbbce9c3440d7318460c32970e8e5b89dc9693ef7aa30af7ca90` |
| `tests/sql/h3_admin_rpc_signed_gateway_harness.sql` | `376bd1cba0c557b5a62fe0b7f175bd7ef7493de5c9d98a4f78d4ddc48346812f` |
| `tests/sql/h3_from_h2_pro_pg17_harness.sql` | `c5f45bd65427497050832b9c0f7c517e687ea9e1961fcdc0e8653f2932b8d379` |
| `tests/sql/h3_safe_suspend_harness.sql` | `821167b000ce20e18f1c4a2504bfe57fbcf4e92f33145c1290bd7c9c81bd04f6` |

## Procedimiento exacto propuesto — requiere JIT humano separado

1. Revalidar rama/HEAD, los 41 hashes anteriores, el nombre libre
   `h3req1-c03-safe-resume-pg17-20261005`, y que la imagen local coincide con
   `postgres@sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f`.
   Si falta/difiere la imagen, detenerse: no hacer pull.
2. Crear **un contenedor PG17 nuevo** con ese nombre, `--network none`, sin puertos,
   `/var/lib/postgresql/data` en tmpfs de 1 GiB, `POSTGRES_HOST_AUTH_METHOD=trust` solo
   en ese contenedor aislado, y mounts read-only de `/candidate/tests/sql`,
   `/candidate/db/migrations` y `/candidate/db/rollback` desde el worktree exacto.
   No montar `.env*`, home, otros repositorios ni volúmenes persistentes. No tocar,
   conectar, detener ni limpiar `h3req1-c03-safe-suspend-pg17-20261005`.
3. Esperar `pg_isready`, crear `h3_c03_chain` y ejecutar en orden los cuatro roots
   siguientes dentro del contenedor nuevo, sin workflow ni servicios externos:
   `h3_from_h2_pro_pg17_harness.sql` → `h3_admin_quota_harness.sql` →
   `h3_admin_rpc_signed_gateway_harness.sql` → `h3_safe_suspend_harness.sql`.
   Para cada `psql`, usar `-X -q -U postgres -d h3_c03_chain -v ON_ERROR_STOP=1
   -o /dev/null -f /candidate/tests/sql/<root>`; preservar solo el exit code y errores
   sanitizados. La redirección evita emitir filas con HMACs sintéticos.
4. El único criterio nuevo de aceptación C03 es el safe-suspend actualizado: contrato
   exacto de diez firmas/ACL, idempotencia de captura; todas las aserciones previas de
   datos/auditoría, nonce, dispatcher y finalizadores in-flight; reconexión; rechazo
   fail-closed tras drift ACL; restauración persistente, coincidencia de fingerprint e
   idempotencia del resume completado.
   El resultado aceptable es exit code 0 de los cuatro `psql`; no se reivindican nuevos
   PASS de gates previos.
5. Ante hash, bootstrap, SQL, conexión o assertion distinta de PASS: detenerse y conservar
   el contenedor/datos; no reintentar, reparar grants ni ejecutar resume manual. No
   ejecutar Edge/Auth/correo, PostgREST, Pages/workerd, Supabase remoto, Git remoto ni
   cleanup. La destrucción/limpieza requiere otra aprobación.

Este manifiesto no aprueba JIT, grants, rollback/resume ni creación de recursos. La
atestación cliente vigente limita este ciclo a trabajo local; el drill integrado y todo
acceso remoto requieren permisos independientes. El PASS SQL, si se obtiene, no cierra
H3-CLOSE-03.

Referencias: [preflight C03](../evidencia/h3req1_h3_close03_integrated_preflight_2026-10-05.md),
[JIT safe-suspend v2 histórico](manifiesto_jit_h3_close03_safe_suspend_pg17_2026-10-05_v2.md),
[JIT v4 H3-CLOSE-02](manifiesto_jit_pg17_postgrest_h3req1_2026-10-05_v4.md),
[plan de cierre](plan_cierre_integral_h3req1_2026-10-04.md) y
[atestación cliente](../evidencias_cliente/sprint_1/atestado_aceptacion_plan_ingesta_editorial_auditoria_2026-10-01.md).
