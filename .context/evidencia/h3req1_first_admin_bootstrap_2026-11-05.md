# H3REQ1 — bootstrap del primer Admin — registro iniciado 2026-11-05

## Reconciliación posterior — 2026-11-06

Este checkpoint conserva el detalle local original y su evidencia sellada. El
estado posterior comprobado es: #542 mergeado en Desarrollo
`14d81b133258572ffa09d72e1bf74d17c221b6a2`; #543 mergeado en Certificación
`17d2d9b57fe9e5f32430a83ec843a3c3df9baa3b`; ambos con árbol
`8cd495d31b0effe4a3023eee4afedc27f5bce933`. Main sigue en
`96eb696d53a7f90279afdc4d37fadec10c2056c4` y no contiene bootstrap.

H2 #99 (`42170267471`) verificó `h2-expand-compat` sobre Certificación; Report
fue 90 aplicadas/0 pendientes, Apply NO-OP y Verify SUCCESS. Artefacto auténtico
ID `13481325792`; JSON SHA-256
`7082bb5a19f08a10f56cfb0d1198bb38021d575d05e18c144f81e799aed252f9`, copiado
byte por byte a la ruta canónica. El label `operation=apply` es histórico del
esquema; el evento real fue Verify. Este run no valida ni instala H3 migration
33.

H3 base 32 permanece instalada/verificada por #98. No consta Report/Apply/Verify
H3 para la migration 33. El archivo DDL aprobado para 32 migraciones no cubre
este delta. Pro no tiene todavía la identidad Auth `romelhc95@gmail.com` según
la última lectura del TL; no se envió correo ni se creó membresía. Pages
Production conserva el safe-suspend y el usuario vio el mensaje de mantenimiento;
esto no acredita callback, Auth, membresía, contraseña ni panel operativo.

La reconciliación de siete rutas documentales/evidencia pasó en Docker el
self-test y el selector candidate-aware; el scanner de credenciales y
`git diff --check` también pasaron. Checker integral: FAIL 348→348, listas
idénticas, cero nuevos/resueltos, SHA-256
`738e442d6b13b3f604376a3f274747b8208f389fa3c2712e535d5fa015527a92`; logs y
listas completas están en
`/tmp/h3req1-documentation-reconcile-20261106/logs/`. Los siete paths
modificados coinciden con los allowlists exactos actuales. El test completo
`tests/test_protected_path_scope_guard.sh` terminó PASS en Docker sobre el
checkout Git con el commit histórico `8ac174d81cf6ce23658bff132236a78935ace1ad`
disponible: manifest/negativos, regresiones de rutas, selector candidate-aware,
promociones y pins. Red deshabilitada y ambas fuentes montadas read-only. El
resultado local no es CI remoto; comando, imagen y stdout se conservan en
`/tmp/h3req1-documentation-reconcile-20261106-final/scope-guard-run-20261106.txt`.
Los logs no incluyen datos secretos.


## Snapshot original — alcance y estado al 2026-11-05

Paquete local aislado en `/tmp/h3req1-first-admin-bootstrap-20261105`, base
main `96eb696d53a7f90279afdc4d37fadec10c2056c4`, árbol base
`455c9364223e93f63dc16f0534877d63b3e62aa0`. La propuesta añade una migration
H3 número 33; no se ha creado commit, PR ni cambio remoto en este ciclo. SQL y
pin del manifest: SHA-256
`67045f02b2eb2c846295207b249b5b9014fe50610e162fe7fac4b40c8b7d62d6`.

La captura de Romel en `/admin/login/` muestra el mensaje “Administración
temporalmente en mantenimiento.” Es evidencia visual aportada por el usuario,
no una lectura de status HTTP, DevTools, Auth, membership ni runtime completo.
No afirma que `romelhc95@gmail.com` exista en Auth Pro, que haya recibido un
correo o que tenga una fila en `admin_members`. En este ciclo no se consultó
Auth Pro, no se envió invitación, no se hizo SQL remoto y no se activó Admin.

## Causa demostrada y opciones

El flujo normal de reserva requiere un actor Admin ready y guarda
`created_by_user_id`; el lifecycle de aceptación requiere actor Auth, invitación
pending y una membresía `invited`; la auditoría requiere un `actor_user_id`
real. La ruta de alta directa de miembros está deshabilitada. El sistema aún no
tiene un actor Admin con el que ejecutar la reserva normal.

| Opción | Resultado de revisión de contratos |
|---|---|
| A — operación excepcional usando solo el schema actual | Descartada. Para materializar la reserva necesitaría falsificar o inventar creador/actor, escribir una membresía directa o ignorar constraints; si marca ready/activa, además salta callback y contraseña. |
| B — delta DB de un solo uso bajo el callback existente | Recomendación local. Una pequeña ampliación del provenance/check permite una reserva sin creador solo para el Auth invite confirmado de la identidad exacta; la auditoría usa el UUID real de `auth.uid()`. Se conserva el callback y el lifecycle existente, con estado inactivo `password_pending`. |

La propuesta B no es una necesidad nueva del cliente ni está desplegada. Es una
brecha de instalación inicial. La migration no genera identidad ni correo,
omite OTP, establece contraseña ni activa una membresía. El usuario debe
completar el lifecycle normal.

## Cambios de implementación locales

- `20261105_h3_first_admin_auth_bootstrap.sql`: admite `created_by_user_id`
  nulo solo con metadata de origen Auth completa, email exacto,
  `invited_at`/`email_confirmed_at` válidos y `app_email_sent=false`; añade una
  acción de auditoría específica; crea un helper privado de una sola vez y
  envuelve la RPC que ya consume el callback. Para una solicitud sin ID intenta
  el bootstrap acotado y luego entra una sola vez al lifecycle/cuota firmado;
  con ID llama ese lifecycle una vez sin bootstrap. Si la aceptación falla,
  el subtransaction revierte la materialización.
- Membresía: se crea como `admin`, `invited`, inactiva, sin `invited_by`
  inventado; la RPC existente actualiza a `accepted` y luego
  `password_pending`. El RPC existente de contraseña debe completar `ready` y
  activo.
- Auditoría: fila `first_admin_bootstrap` y luego la fila normal `accept`, con
  `actor_user_id=auth.uid()`; no se atribuye el envío Auth a un Admin creador.
- Manifest: 33 entradas locales y orden explícito; el pin registrado coincide
  con SHA-256 `67045f02b2eb2c846295207b249b5b9014fe50610e162fe7fac4b40c8b7d62d6`;
  el test de manifest corrió en Docker dentro del resultado focal 9/9. Esto
  acredita orden, pin y contrato estático, no ejecución SQL en PostgreSQL.
- Scope guard: añade el path SQL exacto a la admisión del manifest y paths
  exactos para runner/harness/test/evidencia; conserva rechazos de vecinos.
- Compatibilidad: el contrato vigente permite `token_hash=NULL` también para
  una reserva ordinaria previa a la entrega Auth. El primer borrador que exigía
  hash no nulo fue corregido sin cambiar la columna; el candidato añade
  provenance estricta solo al `created_by_user_id=NULL` del bootstrap.
- Cuota/gateway: el harness actualizado alcanza el callback por el pre-request
  firmado y `admin_signed_rpc`, y compara el incremento de cuota de una
  solicitud con una unidad. No afirma dos RPC ni dos nonces por solicitud.

## Resultado por paso

| Paso | Estado | Evidencia / límite |
|---|---|---|
| E6-A, revisar opción sin schema | `COMPLETADO_LOCAL` | A descartada por los contratos de creador, membresía y actor/auditoría; no se ejecutó nada remoto. |
| E6-B, preparar y validar delta mínimo | `PASS_LOCAL_PG17` | Migration, manifest, runner y fixtures pasaron el harness PostgreSQL 17 sintético autorizado para el árbol de ejecución `20ca1593822c2d7e887877b5d1fffa103d2aceb0`/patch `bb8bb7af3fcbf94410e477bc44ee544abe374477654f51c7cc32e3b058f4a916`; no aplica a Pro. |
| Contrato estático de identidad/callback + manifest | `PASS_LOCAL_DOCKER` | `tests/test_h3_first_admin_bootstrap_contract.py` y `tests/test_h3_pro_migration_manifest.py`: repetidos después de calificar el harness, 9/9 en la imagen Docker local fijada. Pytest emitió solo warning por no poder escribir cache en source read-only. Sin PostgreSQL completo, Auth ni runtime remoto. |
| Scope guard positivo y vecinos | `PASS_LOCAL_DOCKER` | Reejecutado en Docker sobre el checkout actual: suite completa pasó, incluidos paths exactos, vecinos, selector y promotions. Log: `/tmp/h3req1-first-admin-bootstrap-20261105-checkpoint/scope-guard-r21-6-final.log`; no acredita GitHub Actions remoto. |
| PG17, replay dos veces, ACL y lifecycle | `PASS_LOCAL_PG17` | Una ejecución autorizada, una DB efímera, marcador `h3_first_admin_bootstrap_pg17 PASS`; árbol de ejecución `20ca1593822c2d7e887877b5d1fffa103d2aceb0`, patch SHA-256 `bb8bb7af3fcbf94410e477bc44ee544abe374477654f51c7cc32e3b058f4a916`. Log SHA-256 `2002c6ee56ec19ba4b2377a4b9973b1993f6a47d389e363be6f028f2f4af75c2`; limpieza comprobada. El fixture cubre reserva ordinaria token NULL, bootstrap/replay, `password_pending`, ACL y una unidad de cuota por callback. Solo evidencia sintética local; Pro/Auth/correo/CI siguen pendientes. |
| Credential scan y diff-check | `PASS_LOCAL` | Revisión actual en Docker `--network none`, fuente read-only, sobre las 18 rutas del candidato: `credential scan passed`. `git diff --cached --check HEAD` con índice temporal fuera del repo no reportó errores. Comando, imagen, huellas y límites constan en el checkpoint externo `/tmp/h3req1-first-admin-bootstrap-20261105-checkpoint/final-validation-current.md`; no valida runtime remoto. |
| Documentación integral y self-test | `FAIL_INTEGRAL_PRESERVADO` / `PASS_SELF_TEST` | Mismo checker/configuración en copias Git limpias tras el render y la reconciliación: baseline y candidato tienen 348 diagnósticos; listas idénticas, SHA-256 `738e442d6b13b3f604376a3f274747b8208f389fa3c2712e535d5fa015527a92`, cero nuevos/resueltos. El self-test y el gate acotado pasaron; el comando integral termina con exit 1 porque el FAIL permanece. Logs/listas actuales: `/tmp/h3req1-first-admin-doc-reconcile-20261105/logs/`. |
| Auth identidad, invitación/correo, callback real | `PENDIENTE_REMOTO` | El TL confirmó que `romelhc95@gmail.com` aún no tiene identidad Auth Pro; esta sesión no repitió la consulta ni creó la identidad. Invitación/email y apertura temporal del callback requieren JIT separados. |
| Pro apply de migration y Verify | `PENDIENTE_REMOTO` | Requiere manifest final, H2 C/verify para el SHA real si el guard post-C lo exige, autorización DDL nueva, Report/Apply/Verify y gates Production separados. |

## Historial de validación y gates pendientes

Docker fue recuperado tras el único reinicio global aprobado por Romel; no se
repitió. `studiamatch-dev` está healthy y la imagen local importa pytest 9.1.1.
El primer comando de pruebas fue interceptado por el entrypoint de la imagen,
que detectó manifests npm distintos y abortó antes del checker; el rerun usó
`--entrypoint` explícito y sí ejecutó los comandos. Este error de preparación no
se cuenta como fallo del producto ni como resultado de prueba. El checker
completo en árboles Git limpios terminó integral FAIL 348→348 con listas
idénticas (hash `738e442d6b13b3f604376a3f274747b8208f389fa3c2712e535d5fa015527a92`) y self-test PASS. Dos errores de conteo de proyección observados en
un corte intermedio se corrigieron antes de esta comparación, sin modificar el
checker ni su umbral.

La captura posterior de Romel muestra el guard devolviendo el texto de
mantenimiento en `/admin/login/`; es una comprobación visual del estado cerrado,
no lectura del status HTTP ni de Auth/DB. El mismo `ADMIN_BFF_SAFE_SUSPEND`
bloquea el callback y su POST; mantenerlo hasta verificar todas las dependencias.
La apertura controlada del callback deberá ocurrir bajo JIT después de
dependencias listas y antes de enviar el correo de invitación. Si callback o
lifecycle falla, volver a safe-suspend bajo JIT; no reenviar ni insertar una
membresía manualmente.

Los intentos previos se conservan como historia y no se reinterpretan como PASS: `021cb4f8…` terminó en preflight porque no estaba disponible la imagen; el candidato `eda6d9cc…` alcanzó el harness y falló por ambigüedad de `event_count`; otro fixture anterior se detuvo por configuración RLS sintética. Esos resultados no demostraron un defecto de producto. El último JIT exacto se ejecutó una sola vez para árbol `20ca1593822c2d7e887877b5d1fffa103d2aceb0` y patch `bb8bb7af3fcbf94410e477bc44ee544abe374477654f51c7cc32e3b058f4a916`: terminó PASS en PostgreSQL 17 sintético, con limpieza verificada. Log y límite constan en la fila PG17 y en el registro externo. La documentación se reconcilia con ese resultado; la migración, runner y harness probados conservan los mismos bytes.

Codex Security completó la revisión focal del diff el 2026-11-05 21:41 America/Lima: scan `5023da29-ae85-4543-8325-6e79a3a943a3`, snapshot `codex-security-snapshot/v1:sha256:3bfe97c9e49145b04b62245da745ad59598b412f974afb30e964113aa4c4182e`, 4/4 superficies previstas y cero findings reportables. El artefacto `report.md` está en `/home/romel/.codex/state/plugins/codex-security/scans/h3req1-first-admin-bootstrap-20261105/96eb696d53a7f90279afdc4d37fadec10c2056c4_20261106T022511Z_ekxzhn_l/report.md`. El scan es focal/diff-only; excluye Pro/Cloudflare runtime, Auth, correo, CI y smoke. La metadata de usage marca `rollout_unavailable`/un hilo faltante, sin invalidar el resultado focal. La revisión manual anterior señaló falta de un negativo directo de traversal; queda registrada como límite de cobertura, sin bypass ni finding reportado. Los documentos se actualizaron después del snapshot únicamente para reconciliar el resultado y el estado de identidad informado por el TL; no cambian hashes ejecutables. El checker integral se reejecutó tras esta reconciliación en Docker sobre baseline HEAD y candidato limpio. Para conservar la lista completa, solo se amplió el límite de impresión (200→10000) en copias efímeras del script; la lógica y configuración de diagnóstico no se modificaron. Resultado: FAIL 348→348, listas idénticas, cero nuevos/resueltos, SHA-256 `738e442d6b13b3f604376a3f274747b8208f389fa3c2712e535d5fa015527a92`. Logs: `/tmp/h3req1-security-reconcile-20261106/logs/baseline_full.log` (SHA-256 `d19826c25849e7ec1f451b75893c74115c4fca27627d30de17a1f6d6053127da`) y `candidate_full.log` (SHA-256 `a6d4d65e49d3dc3c005adb76b8a39a979cdba588fd42bb5f305d3b6ada34d8b5`). Siguen pendientes publicación/promociones protegidas, nuevo H2 si el gate post-C lo exige, tupla P/DDL para manifest 33 y operaciones remotas Pro bajo sus JITs.

## Recuperación y límites

- PG17 local: ejecución autorizada terminada PASS; el contenedor fue autolimpiado y `docker ps -a` no encontró residuos. No se conectó a Free/Pro.
- Si la migration queda parcialmente aplicada en un futuro Apply, detener el
  run y preservar ledger/auditoría; no ejecutar rollback destructivo ni reparar
  ledger manualmente. La corrección debe ser una migration forward revisada.
- Si el callback falla, el bootstrap y la aceptación se ejecutan en una
  transacción; no dar acceso, no insertar membresía por Dashboard y no reenviar
  automáticamente. Conservar safe-suspend y leer el error sanitizado bajo
  autorización apropiada.
- La apertura de Admin sigue condicionada a Verify de DB, gateway/hook, cuota y
  binding, Edge, Auth callback y BFF. La captura de mantenimiento no cierra E7
  ni E8. H1 continúa sin activar; H4 no inicia.
