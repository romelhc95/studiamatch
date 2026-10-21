# Manifiesto JIT — PG17/PostgREST local H3REQ1 — 2026-10-05

**Estado:** `JIT_BOOTSTRAP_FAILED_STOPPED` — aprobación humana recibida; npm abortó antes de resolver su configuración; no se inició PostgreSQL, PostgREST ni SQL.
**Operación solicitada:** únicamente el gate SQL local PG17 y wire PostgREST desechable descrito aquí.
**No consumido:** ningún JIT, grant o permiso SQL anterior. El JIT de este manifiesto se consumió en el intento de bootstrap fallido; no hubo ejecución SQL.

## Navegación y alcance de cierre

Amarre: [estado vivo](../estado_del_proyecto.md) → [plan H3-CLOSE-01–08](plan_cierre_integral_h3req1_2026-10-04.md) → [evidencia del candidato](../evidencia/h3req1_development_candidate_cycle_2026-10-04.md) → [tarea TASK-H3-001](../backlog_tareas/req_est_001_sprint_1/tarea_003_hito_3.md) → [HITO-003](../hitos/hito_003.md) → [seguimiento](../seguimiento/h3req1_traspaso_avance_y_proximo_ciclo_2026-10-04.md) → [atestación sanitizada cliente](../evidencias_cliente/sprint_1/atestado_aceptacion_plan_ingesta_editorial_auditoria_2026-10-01.md).

Este manifiesto cubre evidencia local de `H3-CLOSE-02` (migraciones, cuotas, guard NULL, firma payload-bound y wire PostgREST) y la parte SQL reproducible de `H3-CLOSE-03` (safe-suspend harness). **No** cubre CI protegido efectivo, rollback integrado Pages/Edge/BFF, UAT D01–D14, Auth remoto, integración, despliegue ni GO Development real.

## Baseline y candidato identificados

| Campo | Valor comprobado |
|---|---|
| Worktree | `/home/romel/src/studiamatch-h3req1-sync-20261002` |
| Rama | `feat/h3req1-sync-20261002` |
| `HEAD` | `4eb4d877a50b012bb630a129bd0c74482c33be9c` |
| `origin/desarrollo` | `4eb4d877a50b012bb630a129bd0c74482c33be9c` |
| Divergencia Git | `0` ahead / `0` behind; merge-base igual a `HEAD` |
| Estado | WIP amplio local, sin cambios staged; preservar todo el trabajo ajeno. `HEAD` no identifica por sí solo los bytes modificados. |
| Fuente dentro de Docker | Contenedor `h3req1-candidate-docker-20261004`, bind mount `/candidate` read-only al worktree exacto. |
| SQL/runtime anterior | **No ejecutado** sobre estos bytes; manifiestos/JIT anteriores quedan obsoletos. |

Antes de ejecutar, volver a comprobar rama, `HEAD`, estado WIP, hashes de esta tabla y mount. Cualquier diferencia invalida este manifiesto y requiere uno nuevo; no rebasar ni modificar el WIP para hacerlo coincidir.

## Ambiente exacto solicitado

| Recurso | Especificación |
|---|---|
| PostgreSQL | Contenedor nuevo `h3req1-pg17-jit-20261005`, imagen local `postgres:17`, digest comprobado `sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f`; bind mounts read-only únicamente de `tests/sql`, `db/migrations`, `db/rollback` y `db/seeds` bajo `/candidate`; sin `.env*`, resto del worktree, volumen persistente ni puertos publicados. |
| PostgREST | Contenedor `h3req1-postgrest-jit-20261005`, imagen local `postgrest/postgrest:v13.0.7@sha256:0a46780309a604cdc8b56c776c6e5e15788ce58174d709e40459ab5a2d44d228`; solo en la red interna indicada abajo, sin puertos publicados. |
| Runner wire | Contenedor nuevo `h3req1-node22-jit-20261005`, imagen local `node:22@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844`. Monta read-only solo el directorio `tests`, `web/package.json`, `web/package-lock.json` y `web/vendor`; instala dependencias productivas con `npm ci --omit=dev --ignore-scripts`, verifica `node --version` y `@supabase/supabase-js` 2.109.0, luego corre `tests/h3_admin_quota_postgrest.mjs`. El árbol actual de `web/node_modules` bajo `/candidate` está vacío; no se usará ni copiará el árbol de 733 MB del snapshot. |
| Red | Crear la red bridge Docker `h3req1-jit-internal-20261005` con `--internal`; conectar únicamente los tres contenedores nombrados. El runner arranca en el bridge preexistente solo para instalar dependencias desde el lockfile, luego se conecta a la red interna y se desconecta del bridge antes de cualquier SQL/wire. Postgres/PostgREST y el runner quedan sin egress durante pruebas. No publicar puertos, usar red host, ni configurar URLs Supabase Free/Pro. El driver contactará únicamente `http://h3req1-postgrest-jit-20261005:3233`; PostgREST contactará PostgreSQL por su nombre de contenedor. |
| Identidades/datos | Fixtures sintéticas locales ya incluidas en los harnesses. JWT, publishable key de prueba, firma y secretos de PostgREST son efímeros/locales; no leer `.env*`, imprimirlos, persistirlos ni incorporarlos a evidencia. |

Los digests de las imágenes locales Postgres, PostgREST y Node 22 fueron comprobados. La imagen Node queda fijada por digest; su versión exacta se registra antes de instalar paquetes y debe ser `v22.*`, si no, detenerse. El lockfile fija la versión SDK; el comando de instalación omite scripts y desarrollo. La red interna no tendrá egress. No se autoriza deploy, Worker remoto, Auth, correo, secretos de Cloudflare, escritura/lectura Supabase ni conexión a redes/servicios del producto.

## Secuencia SQL/wire solicitada

### Bootstrap aislado del runner (antes de SQL)

Montar read-only en el runner solo `/candidate/tests`, `/candidate/web/package.json`, `/candidate/web/package-lock.json` y `/candidate/web/vendor` desde el worktree exacto. Crear el runner Node 22 en la red Docker preexistente `bridge`, ejecutar con entorno limpio y sin npm config/credenciales (`HOME=/tmp/h3req1-node-home`, user/global config `/dev/null`, cache `/tmp/h3req1-node-cache`, registry `https://registry.npmjs.org`): `npm ci --prefix /candidate/web --omit=dev --ignore-scripts`. El lockfile declara únicamente paquetes `registry.npmjs.org` y el tarball local `web/vendor/braces-3.0.4-h3.1.tgz`. La única salida de red autorizada en esta fase es esa instalación; Docker bridge no fuerza allowlist por hostname. Inmediatamente después verificar `node --version` (`v22.*`) y SDK `2.109.0`, conectar el runner a `h3req1-jit-internal-20261005` y desconectarlo de `bridge`. No iniciar PostgreSQL/PostgREST ni ejecutar SQL si falla el bootstrap, pin de versión o comprobación de dependencias.

#### Riesgo residual MEDIUM y aceptación limitada requerida

| Campo | Registro |
|---|---|
| Causa | El bridge Docker disponible no aplica filtrado de salida por hostname; `npm ci` necesita descargar paquetes durante un único bootstrap. |
| Evidencia reproducible | El análisis del `web/package-lock.json` encontró `registry.npmjs.org` más el tarball local ya fijado por SHA-256; Docker bridge no implementa una allowlist FQDN y la red `--internal` sí bloquea egress después del bootstrap. |
| Mitigación | Runner aislado sin `.env*` ni secretos; imagen Node por digest; npm config/user/global config limpios; solo dependencias prod; `--ignore-scripts`; lockfile y tarball versionados/hash; desconexión de `bridge` antes de SQL/wire; revisión estática del driver y test URL restringida a host/puerto exactos. |
| Riesgo residual | Durante ese único `npm ci`, un componente/npm registry comprometido podría solicitar otro destino externo. No hay credenciales de producto en el runner; el filtro de hostname no es técnico en esa fase. |
| Owner / vencimiento | Romel. Solo para el bootstrap de este manifiesto; expira al éxito/fallo del comando o a las 2026-10-06 23:59 UTC, lo que ocurra primero. No es waiver de GO ni permiso de egress posterior. |
| Aceptación humana | Aceptada explícitamente el 2026-10-05 mediante la opción “Aprobar JIT y riesgo”; limitada al bootstrap de este manifiesto y al egress residual descrito. El comando npm falló antes de resolver configuración y no inició descargas; la aprobación expiró al fallar. Cualquier reintento requiere manifiesto y aprobación nuevos. |

Todo comando `psql`/`createdb` se ejecutaría **dentro del contenedor Postgres recién creado**, leyendo exclusivamente los cuatro directorios de harness/migraciones/rollback/seed montados read-only; no se montará el worktree completo ni archivos de entorno. Usará estas bases efímeras:

1. En la base de harness vacía `postgres`: `tests/sql/h2_pg17_harness.sql` y después `tests/sql/h2_pro_pg17_harness.sql`, en ese orden.
2. Crear `h3_gate` y ejecutar `tests/sql/h3_pg17_harness.sql` con defaults.
3. Crear `h3_pro_gate` y ejecutar `tests/sql/h3_pg17_harness.sql` con `h3_pro_baseline=1`.
4. Crear `h3_pro_chain_gate`; ejecutar `tests/sql/h3_from_h2_pro_pg17_harness.sql`, `h3_admin_quota_harness.sql`, `h3_admin_rpc_signed_gateway_harness.sql` y `h3_safe_suspend_harness.sql`, en ese orden. Este modo conserva la cohorte Pro actual.
5. Crear `h3_future_contract_gate`; repetir la cadena con `h3_contracted_baseline=1` solo para el fixture futuro de contracción. No representa ni modifica el estado remoto Pro.
6. En `h3_pro_chain_gate`, ejecutar `h3_quota_postgrest_fixture.sql`. Como el fixture vuelve a aplicar el hook EXPAND original, reaplicar **después** `db/migrations/20261004_h3_admin_rpc_signed_gateway_payload_bound_wrapper.sql`; arrancar PostgREST en la red interna indicada, con DB `h3_pro_chain_gate`, schema `public`, anon role `anon`, puerto interno `3233` y el `db_pre_request` del gateway; correr en el runner aislado el driver Node 22 hacia `http://h3req1-postgrest-jit-20261005:3233` con fixtures/secretos sintéticos solo en el entorno de proceso; ejecutar `h3_quota_postgrest_assert.sql`.
7. Ejecutar `tests/sql/h3_invitation_reservation_concurrency.sh` únicamente contra `h3_gate`, con sus identidades/correos sintéticos.

`security-audit.yml` contiene esta misma secuencia de DB gate y el reapply payload-bound añadido para que el wire mida los bytes actuales. No se ejecutará GitHub Actions, `workflow_dispatch` ni ningún workflow remoto; las líneas son referencia de la receta local.

### Efectos autorizables, limitados al contenedor nuevo

- Crear la red `h3req1-jit-internal-20261005` como bridge Docker `--internal`; crear y conectar a ella solo los contenedores PostgreSQL, PostgREST y Node runner nombrados. El runner podrá usar el bridge existente solo durante el bootstrap npm y deberá salir de ese bridge antes de iniciar servicios/SQL/wire.
- `CREATE EXTENSION pgcrypto`, roles locales `anon`/`authenticated`/`service_role`, schemas, tablas, índices, funciones, vistas, triggers, grants/revokes y datos sintéticos que declaran los scripts.
- Los únicos bind mounts de fuente al contenedor DB son `tests/sql`, `db/migrations`, `db/rollback` y `db/seeds`, todos read-only; `.env*`, secretos y el resto del repositorio no se exponen al contenedor.
- El runner solo recibe mounts de `tests`, los dos manifiestos package y el tarball local fijados por hash; no recibe `.env*` ni el resto del worktree. `npm ci` omite scripts y dependencias dev. Egress a registry solo durante esa instalación; el runner se desconecta de `bridge` antes del test.
- Los harnesses pueden recrear schemas `public`/`private` **solo dentro de las bases de prueba nuevas**. Ejecutan fixtures de invitación, membresía, auditoría, cuotas, nonces y estados editoriales sintéticos.
- No se conectará a instancias Supabase ni se leerá/escribirá dato operativo; no habrá reset de cuentas reales, envío de correo, cambio de factores, grant remoto o alteración de Free/Pro.
- La salida del test no demuestra activación remota de `db_pre_request`, despliegue ni GO contractual.

En falla: detenerse, conservar logs sanitizados y no intentar rollback remoto ni repetir con otro baseline. No detener/eliminar contenedores, red, bases ni datos, ni desconectar el runner de la red interna al finalizar: cleanup/destrucción requiere JIT independiente. La aprobación aquí solicitada tampoco concede PR, push, merge, deploy, cambios de secretos, Auth/reset, Certification o Production.

## Cierre transitivo de archivos SQL y harnesses

SHA-256 calculados desde el mount read-only del worktree indicado. El cierre recursivo sigue cada `\ir` de las nueve raíces de harness SQL del `db-gate`; incluye ramas condicionales del archivo aunque una rama concreta quede inactiva. Todo cambio de byte invalida la aprobación.

| Ruta | SHA-256 |
|---|---|
| `db/migrations/20260825_h2_editorial_layer.sql` | `d7c7a96f0f7ba7e867b800f262766ab7e66f595ae82c71286407405357fe69aa` |
| `db/migrations/20260825_h2_editorial_layer_allowlist_fix.sql` | `dbeef2733b741ea14809a2f29a8c3ac18dedbb166e0ce4af52baf0632ed17536` |
| `db/migrations/20260825_h2_editorial_layer_grants_fix.sql` | `0e65ca8e75f0f02f2d0fa1c169d0805762c451a85fcba99548a8980907ff5440` |
| `db/migrations/20260825_h2_editorial_layer_start_date_view_fix.sql` | `7eaf1dfdd0daaaefa23b5ed39d83cff3b6accf65b77c6eb48f0e49412322d8ca` |
| `db/migrations/20260826_h2_development_legacy_public_compat.sql` | `ee07b75d149de7146ddbbe40ba3b1fef8579cc98e923ad5f0b704b656c1890e3` |
| `db/migrations/20260826_h2_editorial_layer_forward_fix.sql` | `56b28eabc6d2f520897c73ac8b1ec58bec00601cfbf2c8014a22582a848e89a6` |
| `db/migrations/20260826_h2_public_effective_view_public_fields_fix.sql` | `2d5762012eb30f3df8476110ac1c2c554e536824d583eab7c17026c7d7bf1062` |
| `db/migrations/20260826_h2_security_advisor_remediation.sql` | `9ae179772c1361076f2bfa6444f074fc54c99bc5d6622abadbb97bf0789001bf` |
| `db/migrations/20260826_h2_seed_editorial_field_definitions.sql` | `9dc615f08a6d2dd9e6c72f5ddefa1bac7fe97611fd9c1e85bd3a12a32e4d2104` |
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
| `db/migrations/20261004_h3_admin_rpc_signed_gateway_payload_bound_wrapper.sql` | `f1b4dce0dc0634585b5448514877b200924448c7e2dcc06441f1c3f66af78d0f` |
| `db/rollback/h3req1_safe_suspend.sql` | `09fcd8f6a5b9590f2e8db20f00c0fd9244ffd6a4a8db714c3c2837f04c22369d` |
| `db/seeds/h3_admin_seed_local.sql` | `3ce5f5ae7408aadfb0a79124a32f03a893f5abad04d47a69a05118c25ae14df4` |
| `tests/sql/h2_pg17_harness.sql` | `af2de7546ce05d07042c55ce152b855b137a442b83b0a4f183deef70a810147f` |
| `tests/sql/h2_pro_pg17_harness.sql` | `676a149546d8f3ff045d7d4332eedeefe343a8ef25375cd72e906ed6d1f26bfe` |
| `tests/sql/h3_admin_quota_harness.sql` | `890464e81ae5bbbce9c3440d7318460c32970e8e5b89dc9693ef7aa30af7ca90` |
| `tests/sql/h3_admin_rpc_signed_gateway_harness.sql` | `221e9100e9353db89e3fafd7f16fad4addcd9f958d8738b4d9a262e62819af01` |
| `tests/sql/h3_from_h2_pro_pg17_harness.sql` | `c5f45bd65427497050832b9c0f7c517e687ea9e1961fcdc0e8653f2932b8d379` |
| `tests/sql/h3_invitation_edge_runtime_harness.sql` | `2233bf419c2e9c1a1367f34f915bbcb188cf7ba0e818a14abbf49cb4d44d5b5f` |
| `tests/sql/h3_invitation_onboarding_harness.sql` | `6b956e63d0860f5bb2e9aa8fef98fe07223b891060245b11186f78d9d0f8e69b` |
| `tests/sql/h3_onboarding_rbac_hardening_harness.sql` | `aa5a2510e2604cbb94bd42788adb38f31c92872a6ac0b7cc0520f7aa866b4423` |
| `tests/sql/h3_pg17_harness.sql` | `e1525daa888895619b477402b688e0a3409d2eba9d53c1e2c60f674f03aa61d3` |
| `tests/sql/h3_quota_postgrest_assert.sql` | `f0f2285b23bb4fddb7e5fdc4aa2ee409d822524fc1ed110abd42e6ff11a6aad9` |
| `tests/sql/h3_quota_postgrest_fixture.sql` | `307704d2734506902b8974beb36fb29c5dd35d36f797e70c9bd2f27070b228ed` |
| `tests/sql/h3_safe_suspend_harness.sql` | `c1dcfef828b836e6627530127eb66a157db1df1437ad923a06f6c64e2c6782f1` |

## Runners y contrato de ejecución

| Ruta | SHA-256 |
|---|---|
| `.github/workflows/security-audit.yml` | `1221ecc16a46f5f6d617deeb86d523033a2dc927985dea285c0631869b5b0b72` |
| `tests/sql/h3_invitation_reservation_concurrency.sh` | `9436045bce656db8c5caca80ab35bdad35f173dbe639b864d1a9f8a8cb9b422c` |
| `tests/h3_admin_quota_postgrest.mjs` | `e11034070050212bffe961f87467cc727b0c16053a3319515acb477f63d28e95` |
| `web/package.json` | `4567e008756097437c0ef586f1c112c97db3a198bcd521bd62e8342242f7cd8a` |
| `web/package-lock.json` | `8bd9c50605a8ce92e87b0ad81e4513fd47fc01ca328079eef792d264c2a292bc` |
| `web/vendor/braces-3.0.4-h3.1.tgz` | `a8c0b0223dc788781252f9b056207b5b053b8dd0896da861c305769b472f0819` |
| `tests/h3_admin_quota_uat.mjs` | `79e8162be08bdaf5b1c62aad87ef1cb4349394193ca6a6e4cb83b26404b2422f` |
| `tests/h3_admin_quota_runtime.mjs` | `99672bbb0ec968b6b12656821e0e45144670298db7478c89a6749df4272b13f1` |
| `tests/h3_local_runtime_server.mjs` | `52589bc937e962cb4335e7b5d854987577d0f1bc48bd6b7a0cfbd4aa8564861e` |
| `tests/h3_local_runtime_quota_fixture.mjs` | `cab8b55c8bdd3e4da1871b965ae72d3fa7c8d3e1f011fea263c2071c23c1a60a` |
| `tests/h3_supabase_sdk_headers_uat.mjs` | `a63c0febf70290a692527cb4dc56d342f2f61e3490c104030b424e5a5873a2f9` |
| `tests/test_supabase_credentials_contract.py` | `bc8bceb6ae2ab223000e0f1c413423098bb04e4142b3956ae37877e5f81936b0` |
| `web/functions/_lib/admin-bff.ts` | `1cb1ad95d723e884f58cf98dd5b2600e59fa8230aa044cb25e6ebb41f1db7ed7` |
| `web/functions/_lib/admin-quota.ts` | `738a3267d645fdca40b77b8d8fb9877c209992296031b0d670b6153c9a9134d6` |
| `web/src/lib/supabase-transport.ts` | `b115c8f1c46f7c33c80f6ace8fc9d5c2409898ca1833851e58d1361d640571b0` |
| `workers/admin-quota/index.ts` | `392d0f9ad183ac871a16d01c6f6b5e6fd18edd26c18fd3221a1d16f8bb0a869f` |
| `workers/admin-quota/wrangler.jsonc` | `f90ffabbfe79c5ebf8f98da12b6604fc6a2961fa8b8811ce48dd2a23e855bbf5` |

La captura anterior de reglas GitHub no se toma como evidencia efectiva. Este JIT local tampoco instala ni modifica checks/protecciones.

## Evidencia previa del mismo candidato (no sustituye esta operación)

- Docker `pytest tests -q`: `287 passed, 4 skipped`, una advertencia de deprecación PyPDF2.
- Cuotas: UAT aislado PASS; runtime Miniflare PASS con 25 concurrencias, persistencia tras restart y compatibilidad de payload previo; máximo 1 shard DO para 20 identidades de cuenta-IP en una IP sintética.
- SDK/BFF/Edge Auth e invitaciones: pruebas interceptadas/unitarias y typecheck PASS; TypeScript PASS; ESLint 0 errores/9 warnings preexistentes; smoke H2 web mock PASS; credential scan PASS ejecutado como root en el contenedor por restricción de escritura de `/tmp`.
- Revisión estática del código producto: 0 defectos LOW+ no mitigados. La revisión posterior del manifiesto encontró el riesgo MEDIUM de egress npm, que estaba pendiente en ese corte y fue aceptado después; el resultado del bootstrap fallido está registrado abajo. El CI fija loopback para el port mapping de Postgres y configura `server-host=127.0.0.1` para PostgREST; YAML/bash parse PASS, falta validar el workflow en CI remoto.
- Estos resultados no prueban SQL PG17, HTTP PostgREST ni grants/OIDs efectivos. El PASS remoto Auth+MFA histórico se conserva sin repetición.

## Aprobación humana solicitada — concedida; intento detenido

**Aprobación recibida el 2026-10-05.** La solicitud aprobada se limitó a crear la red interna `h3req1-jit-internal-20261005`; crear los contenedores `h3req1-pg17-jit-20261005`, `h3req1-postgrest-jit-20261005` y `h3req1-node22-jit-20261005` con las imágenes fijadas aquí; montar los directorios SQL read-only en PostgreSQL y al runner solo `tests`, `web/package.json`, `web/package-lock.json` y `web/vendor`; permitir que el runner use temporalmente el bridge existente solo para `npm ci --omit=dev --ignore-scripts` con lockfile, registry configurado y sin credenciales/scripts; reconocer que el bridge no filtra técnicamente hostnames durante ese bootstrap; desconectarlo de `bridge` antes de SQL/wire; crear las cuatro bases sintéticas declaradas; ejecutar la secuencia completa con estos hashes; y conservar red, contenedores/datos al terminar sin cleanup. Si cualquier hash, rama, mount, recurso o secuencia difiere, la ejecución debía detenerse. La aprobación incluyó aceptación limitada del riesgo residual documentado arriba. No autorizó operaciones con servicios del producto ni permisos remotos adicionales.

La aprobación de esta solicitud no incluye eliminación de contenedores/datos, grants o writes Supabase remotos, Auth/reset/correo/factores, secretos de producto, Git remoto, PR/merge, deploy, rollback/cleanup, Certification ni Production. Cada uno mantiene su autorización JIT separada.

## Resultado del intento JIT — 2026-10-05

- La aprobación humana explícita cubrió el alcance local exacto y aceptó el riesgo MEDIUM de egress temporal durante `npm ci`.
- Preflight: rama `feat/h3req1-sync-20261002`; `HEAD=4eb4d877a50b012bb630a129bd0c74482c33be9c`; 0 archivos staged; 101 entradas WIP (48 tracked modificadas y 53 untracked); mount `/candidate` read-only al worktree esperado; **74/74 hashes** coincidentes. Los tres digests de imagen coincidieron con este manifiesto.
- Se creó la red interna `h3req1-jit-internal-20261005` (Docker ID `f54379669c125d32f02120b0c0f74d07b56cf3df8c973a3ae6c869e0cf8646b9`) y el runner `h3req1-node22-jit-20261005`, con los cuatro mounts autorizados read-only. Node reportó `v22.23.2`.
- El único intento de `npm ci --omit=dev --ignore-scripts` terminó antes de resolver configuración: npm rechazó cargar `/dev/null` simultáneamente como `userconfig` y `globalconfig` (“double-loading config”). No se inició descarga de paquetes ni egress al registry.
- Por la regla de parada, no se reintentó npm, no se conectó el runner a la red interna, y no se crearon PostgreSQL/PostgREST ni bases; SQL, wire y asserts **no ejecutados**. Se conservan sin cleanup la red interna y el runner; el runner sigue en el bridge existente. No se autorizó cleanup.
- Resultado: **NO-GO** para H3-CLOSE-02/03. No repetir bajo este manifiesto: su aprobación expiró con el fallo. Preparar un manifiesto nuevo con configuración npm no ambigua y hashes/preflight vigentes, y solicitar otra aprobación antes de cualquier bootstrap o SQL.
