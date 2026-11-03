# Propuesta JIT H3-CLOSE-03 — safe-suspend SQL en PG17 — 2026-10-05

**Estado:** `PREPARADO_NO_APROBADO_SQL_SUBGATE`; no concede permiso de ejecución.
**Alcance de esta propuesta:** validar en un PG17 desechable el nuevo bloqueo SQL del
dispatcher firmado y los finalizadores in-flight. Este subgate no es el drill integrado
workerd+Edge+PG17 ni cierra H3-CLOSE-03.

## Motivo y límites

La revisión estática posterior al JIT v4 encontró que `db/rollback/h3req1_safe_suspend.sql`
revocaba las funciones mutadoras internas, pero no `public.admin_signed_rpc(text,jsonb,text)`,
que es `SECURITY DEFINER` y permanece ejecutable por `authenticated`. Por ello, revocar
solo las funciones internas no demostraba el bloqueo de una llamada firmada a través del
dispatcher. El rollback local ahora incluye el dispatcher y
`tests/sql/h3_safe_suspend_harness.sql` verifica una llamada con prueba payload-bound
válida, el rechazo por ACL, nonce sin consumir y restauración TEST-only de permisos.

El JIT v4 está consumido y no cubre estos bytes. No se ejecutaron SQL, PG17, PostgREST,
Docker ni servicios durante la preparación. La atestación sanitizada H3-CA4/H3 local se
revisó: el cambio es de seguridad/transición, no amplía criterios de negocio ni autoriza
operaciones remotas.

## Cierre transitivo SQL

Se recorrieron recursivamente todos los `\ir` —incluidas ramas condicionales— desde estas
cuatro raíces: `tests/sql/h3_from_h2_pro_pg17_harness.sql`,
`tests/sql/h3_admin_quota_harness.sql`,
`tests/sql/h3_admin_rpc_signed_gateway_harness.sql` y
`tests/sql/h3_safe_suspend_harness.sql`. Resultado de preflight local de archivos:
**40 inputs encontrados, 0 includes ausentes**. El listado incluye la migración de
payload-bound, ambas funciones de cuota, los baselines H2 Pro/H3, migraciones condicionales
del baseline y el rollback/harness actualizados.

Los SHA-256 fueron calculados sobre las rutas de este worktree. Recalcular los 40 antes
de cualquier ejecución; una diferencia no enumerada detiene el JIT y exige manifiesto
nuevo. Estos hashes identifican archivos fuente, no congelan el WIP ni autorizan SQL.

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
| `db/rollback/h3req1_safe_suspend.sql` | `5b02ce69e5aa9083dd69c92670d138d93ca589b1260f57ac77deed33a19cb522` |
| `tests/sql/h2_pro_pg17_harness.sql` | `676a149546d8f3ff045d7d4332eedeefe343a8ef25375cd72e906ed6d1f26bfe` |
| `tests/sql/h3_admin_quota_harness.sql` | `890464e81ae5bbbce9c3440d7318460c32970e8e5b89dc9693ef7aa30af7ca90` |
| `tests/sql/h3_admin_rpc_signed_gateway_harness.sql` | `376bd1cba0c557b5a62fe0b7f175bd7ef7493de5c9d98a4f78d4ddc48346812f` |
| `tests/sql/h3_from_h2_pro_pg17_harness.sql` | `c5f45bd65427497050832b9c0f7c517e687ea9e1961fcdc0e8653f2932b8d379` |
| `tests/sql/h3_safe_suspend_harness.sql` | `9526b2d21d7b89ba068c5f6a90105ac30365de1fc9b5d1a49bbccc214771dff3` |

## Procedimiento exacto propuesto para este subgate

**Solo tras aprobación JIT independiente**, y con preflight idéntico a la tabla anterior:

1. Revalidar la rama/WIP sin modificarlo; comprobar que el nombre
   `h3req1-c03-safe-suspend-pg17-20261005` está libre y que la imagen Postgres local
   coincide con `sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f`.
   No hacer pull si falta o difiere la imagen.
2. Crear únicamente ese contenedor PG17 nuevo, sin puertos publicados, red `none`,
   almacenamiento de datos en tmpfs y montajes read-only de `tests/sql`, `db/migrations`
   y `db/rollback`. No montar `.env*`, home, otros repositorios ni volúmenes persistentes.
   Usar solo las credenciales sintéticas efímeras del harness local.
3. Crear la base desechable `h3_c03_chain` y ejecutar, en este orden, dentro del
   contenedor, con `ON_ERROR_STOP=1`:
   `h3_from_h2_pro_pg17_harness.sql` → `h3_admin_quota_harness.sql` →
   `h3_admin_rpc_signed_gateway_harness.sql` → `h3_safe_suspend_harness.sql`.
   No ejecutar el workflow GitHub, no conectar PostgREST ni continuar ante FAIL.
4. Exigir los cuatro marcadores PASS y, en safe-suspend, que: las ACL capturadas de
   todos los iniciadores y del dispatcher queden denegadas a roles API; un proof firmado
   válido pase el pre-request pero la llamada `authenticated` a `admin_signed_rpc` falle
   por privilegios y no consuma nonce; `service_role` pueda completar/fallar/reconciliar
   las tres reservas previas con auditoría; el snapshot de datos/auditoría/cohorte no
   cambie por la suspensión; y la restauración TEST-only coincida con las ACL efectivas
   originales, incluido `admin_signed_rpc`.
5. Si cualquier hash, imagen, mount o resultado difiere, detenerse y conservar evidencia
   sanitizada. No corregir ni reintentar bajo la misma aprobación. No eliminar ni limpiar
   el contenedor/datos al terminar; cleanup requiere JIT separado.

La imagen/digest anterior se toma del JIT v4 histórico; no se inspeccionó Docker al
preparar esta propuesta. Debe confirmarse localmente antes de pedir o consumir el JIT.
El SHA-256 final de este manifiesto y el preflight de los 40 inputs se deben registrar
inmediatamente antes de solicitar aprobación; ninguna aprobación queda concedida aquí.

## Recuperación y límites de aceptación

El harness conserva permisos efectivos en una tabla temporal de su sesión, revoca y
restaura al final exactamente las ejecuciones que estaban habilitadas. Si el proceso se
interrumpe, el DB efímero puede quedar suspendido; no improvisar grants ni reusar la base.
La tabla temporal desaparece al cerrar la sesión y no constituye procedimiento operativo
ni remoto de recuperación.

Para un futuro drill integrado, mantener Pages y Edge en safe-suspend mientras se
restauran ACL desde una captura persistente y aprobada; verificar primero esa captura,
finalizadores, datos y auditoría; habilitar Edge y luego Pages solo tras smoke controlado.
Pages limpia cookies, por lo que la recuperación incluye reautenticación normal sin
reset/re-enrolamiento ni repetir el PASS histórico Auth+MFA. Si la restauración es
ambigua, mantener ambos flags activos y detenerse. No se define SLA ni se inventa un
plazo de recuperación.

**Bloqueadores para H3-CLOSE-03 completo:** no existe todavía un runner que una los bytes
reales de Pages/workerd, Edge y esta DB PG17; los UAT actuales de workerd, Edge y SQL son
fixtures separados. Tampoco existe un procedimiento operativo de recuperación persistente
aprobado. Debe diseñarse/validarse esa integración en un ciclo autorizado antes de
presentar un GO de rollback integrado. Este subgate SQL, aunque pase, no lo sustituye.

## Aprobaciones no concedidas

- SQL/PG17 local: JIT nuevo para el procedimiento exacto anterior, después de hash final,
  preflight y verificación del digest/mounts.
- Docker/workerd/Edge integrados: requiere un runner integrado aún inexistente y un ciclo
  local posterior con alcance y validaciones propios.
- Supabase, Auth/correo, Cloudflare, secretos, Git/CI remoto, push/PR/merge/deploy,
  promoción, Certification/Production y cleanup: fuera de alcance y con permisos separados.
