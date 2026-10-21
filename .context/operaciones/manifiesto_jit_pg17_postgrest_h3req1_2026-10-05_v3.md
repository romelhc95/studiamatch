# Manifiesto JIT v3 — PG17/PostgREST local H3REQ1 — 2026-10-05

**Estado:** `JIT_SQL_FAILED_STOPPED` — aprobado y ejecutado; el signed-gateway harness falló en el caso de replay; no se ejecutó PostgREST/wire ni SQL posterior.
**Alcance solicitado:** repetir la secuencia completa PG17/PostgREST local con la corrección `v_key_id`, en un PostgreSQL nuevo y una red interna nueva. No cubre servicios del producto ni operaciones remotas.
**JIT v2:** [ejecución detenida](manifiesto_jit_pg17_postgrest_h3req1_2026-10-05_v2.md). El signed-gateway harness falló por ambigüedad PL/pgSQL `key_id`; no repetir con su hash ni con sus bases parciales.

## Corrección local y gates previos

Con aprobación humana acotada, en `db/migrations/20261004_h3_admin_rpc_signed_gateway_payload_bound_wrapper.sql` se renombró la variable local `key_id` a `v_key_id` dentro de `private.h3_admin_rpc_gateway_verify_payload`. Se conservó `gateway_key.key_id`, la firma de función y el resto de la lógica.

| Gate | Evidencia |
|---|---|
| Atestación/aceptación cliente | La atestación sanitizada exige conservar identidad de usuario, RLS, `auth.uid()`, RBAC y MFA; prohíbe sustituir identidad por `service_role`. El cambio solo desambigua el identificador PL/pgSQL; no altera esos contratos. |
| Revisión `security-auditor` | 0 hallazgos de vulnerabilidad en lectura estática. Limitación informativa: el archivo es untracked, por lo que Git no ofrece diff contra una versión base. La herramienta de patch realizó únicamente el rename aprobado. |
| Contrato estático en Docker | PASS: `v_key_id` declarado y usado en validación/consulta/payload canónico; columna `gateway_key.key_id` conservada; sin predicado `gateway_key.key_id = key_id`; `auth.uid()` y verificación payload siguen presentes. |
| Runtime de esta corrección | **NO EJECUTADO**. Ningún SQL/PG17/PostgREST desde el FAIL v2. Solo un manifiesto JIT nuevo y aprobado puede autorizar la revalidación. |

## Baseline y cierre criptográfico de inputs

| Campo | Valor |
|---|---|
| Worktree | `/home/romel/src/studiamatch-h3req1-sync-20261002` |
| Rama / `HEAD` / `origin/desarrollo` | `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c` / `4eb4d877a50b012bb630a129bd0c74482c33be9c`; merge-base igual, divergencia `0/0`. |
| WIP tras agregar este manifiesto | 103 entradas: 0 staged, 48 tracked modificadas, 55 untracked. Preservar íntegramente. El conteo previo a crear v3 era 102/48/54. |
| Manifiesto hash base | v1 SHA-256 `45654420e7e3ce00a362b7e91a3877f129789a655ccf6ce45ccc1e087434de12`, contiene 74 rutas/ hashes (57 SQL/harness). |
| Sustitución permitida en el set de 74 | `db/migrations/20261004_h3_admin_rpc_signed_gateway_payload_bound_wrapper.sql`: hash v1 `f1b4dce0dc0634585b5448514877b200924448c7e2dcc06441f1c3f66af78d0f`; hash corregido `c8a69e06e2d1d3a7f5e2245f6fb68ac6220deac3fd0b273edb5bcedafdba81a5`. Las otras 73 rutas deben conservar exactamente los hashes del manifiesto v1. |
| Preflight de inputs | 74 rutas presentes; exactamente 1 hash distinto, el archivo corregido; 73/73 restantes coinciden. Recalcular de nuevo antes de ejecutar. |

Antes del JIT, verificar SHA del manifiesto v1, rama/HEAD/ref local, WIP, mounts y todos los 74 hashes. Cualquier diferencia invalida v3; detenerse y emitir otro manifiesto. No stagear ni editar fuentes durante la operación aprobada.

## Recursos y secuencia cuya autorización se solicita

### Red y runner sin egress

1. Crear la red Docker bridge interna nueva `h3req1-jit-internal-v3-20261005` con `--internal`; no conectarla a bridges con egress.
2. Reutilizar el runner existente `h3req1-node22-jit-v2-20261005` (imagen Node 22 digest `sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844`, mounts read-only ya fijados en v2). Revalidar estado, image digest, los cuatro mounts, `node --version` `v22.*`, `npm ls @supabase/supabase-js` `2.109.0` y los hashes exactos de `web/package.json`/lock/vendor. Reutiliza el `node_modules` instalado por el `npm ci` PASS del v2; **no ejecutar npm ni habilitar egress**.
3. Con autorización v3, conectar ese runner a la red interna v3 y desconectarlo de la red interna v2 `h3req1-jit-internal-20261005`. El runner v1 sigue idle en `bridge`; no ejecutar, detener, desconectar ni eliminar runner v1 bajo esta solicitud. El runner v2 solo se moverá entre esas dos redes internas según este paso, no se detendrá ni eliminará. Tras moverlo, debe estar solo en la red interna v3.

### PostgreSQL y PostgREST nuevos

- Crear `h3req1-pg17-jit-v3-20261005` desde `postgres@sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f`, red interna v3 únicamente, sin puertos publicados, `/var/lib/postgresql/data` tmpfs, sin volumen persistente. Montar read-only únicamente `tests/sql`, `db/migrations`, `db/rollback` y `db/seeds`. Usar el password sintético local `postgres` sin imprimirlo ni persistirlo.
- Crear `h3req1-postgrest-jit-20261005` desde `postgrest/postgrest:v13.0.7@sha256:0a46780309a604cdc8b56c776c6e5e15788ce58174d709e40459ab5a2d44d228`, red interna v3 únicamente, sin puertos publicados, listener `0.0.0.0` interno, puerto `3233`, schema `public`, anon role `anon`, DB `h3_pro_chain_gate`, pre-request `public.h3_admin_rpc_signed_gateway_pre_request`. El nombre/puerto son exactos para la allowlist del driver. No hacer pull de imágenes; comprobar digests locales.
- Revalidar después de crear que solo runner v2, PG v3 y PostgREST estén en la red v3; no exista binding de puertos ni volumen persistente y los mounts PG sean exclusivamente los cuatro read-only declarados.

### Secuencia SQL/wire íntegra en el PG v3 limpio

Ejecutar `psql`/`createdb` dentro de `h3req1-pg17-jit-v3-20261005`, `ON_ERROR_STOP=1`, deteniéndose ante cualquier error:

1. DB `postgres`: `tests/sql/h2_pg17_harness.sql`, luego `tests/sql/h2_pro_pg17_harness.sql`.
2. DB `h3_gate`: `tests/sql/h3_pg17_harness.sql` con defaults.
3. DB `h3_pro_gate`: `h3_pg17_harness.sql` con `h3_pro_baseline=1`.
4. DB `h3_pro_chain_gate`: `h3_from_h2_pro_pg17_harness.sql`, `h3_admin_quota_harness.sql`, `h3_admin_rpc_signed_gateway_harness.sql`, `h3_safe_suspend_harness.sql`, en ese orden.
5. DB `h3_future_contract_gate`: repetir cadena con `h3_contracted_baseline=1` solo para `h3_from_h2_pro_pg17_harness.sql`.
6. En `h3_pro_chain_gate`, `h3_quota_postgrest_fixture.sql`; después reaplicar `db/migrations/20261004_h3_admin_rpc_signed_gateway_payload_bound_wrapper.sql`. Arrancar PostgREST; desde runner v2 ejecutar `tests/h3_admin_quota_postgrest.mjs` solo contra `http://h3req1-postgrest-jit-20261005:3233` con secretos/fixtures sintéticos efímeros; luego `h3_quota_postgrest_assert.sql`.
7. Ejecutar `tests/sql/h3_invitation_reservation_concurrency.sh` solo contra `h3_gate` con identidades/correos sintéticos.

No guardar JWT, firmas ni secretos sintéticos en logs/evidencias. La migración fuente permanece read-only dentro de PostgreSQL. La salida no acredita `db_pre_request` remoto, CI, deploy, rollback Pages/Edge/BFF ni GO Development.

## Riesgo, aprobación y límites

Esta ejecución reutiliza paquetes ya instalados bajo la aceptación v2, verificados contra el mismo lockfile/hash y auditados sin vulnerabilidades. No solicita ni necesita egress nuevo. El permiso de edición local ya se consumió; no cubre esta nueva ejecución PG/wire.

**Aprobación humana v3 recibida** el 2026-10-05 mediante “Aprobar v3 local”. Cubrió exclusivamente crear la red interna v3, mover el runner v2 a ella, crear PostgreSQL v3 con los digests/mounts/aislamiento aquí descritos y ejecutar la secuencia local. No autorizó PostgREST si falla un harness previo ni cleanup. No hubo egress nuevo.

No autoriza SQL Supabase remoto, Auth, secretos de producto, Cloudflare, Git/CI remoto, push/PR/merge, deploy, Certification/Production, cambios adicionales de fuente, rollback ni cleanup. Preservar runner v1/v2, PG v2 parcial, red v1 y todos los recursos v3 al terminar; eliminarlos requiere JIT separado. Ante fallo, detenerse, conservar resultado sanitizado, no reintentar con este manifiesto y mantener NO-GO.

## Resultado de ejecución JIT v3 — 2026-10-05

- Aprobación v3 explícita recibida. SHA-256 del manifiesto v3 aprobado antes de ejecutar: `f6905fe2b5e93e4bd9db3defa33870b9273ce75cf2ddd30b9ca5ca892b87facd`.
- Preflight: rama/HEAD/`origin/desarrollo`, WIP, los 74 inputs (una sustitución de hash), manifests y mounts coincidieron. Runner Node v2 con Node `v22.23.2`, SDK `2.109.0` y mounts read-only; se movió de la red interna v2 a v3 sin bridge/egress. No se ejecutó npm.
- Se creó la red interna v3 con ID `da6a40654b6cc5af86a38b9df73fe873814a0b249f1ded6d03ed5426ca4ddbe7` y PostgreSQL v3 ID `51b1967bc60a37747671f161c091bf07d225447d2b0f5f564d8de9fbeae73f9a`, digest fijado, sin puertos publicados, datos tmpfs y cuatro mounts SQL read-only. `pg_isready` PASS.
- PASS antes del fallo: H2; H2 Pro (incluido el rechazo esperado del rollback guard); H3 default; H3 Pro baseline; cadena H2 Pro→H3; harness de cuotas.
- **FAIL bloqueante:** `tests/sql/h3_admin_rpc_signed_gateway_harness.sql:247`. El caso de replay esperaba `rpc_replay_rejected`/409, pero recibió `rpc_signature_invalid`/403 en `admin_signed_rpc`. Revisión estática posterior identificó que, luego del escenario non-editor, el harness restauraba los JWT claims del admin pero dejaba `request.headers` con actor/RPC/nonce/firmas del non-editor. La petición resultaba inválida antes del control de nonce. La expiración de 60 segundos planteada inicialmente no se confirmó y queda supersedida por este hallazgo concreto.
- Parada: no se ejecutaron `h3_safe_suspend_harness.sql`, la cadena `h3_future_contract_gate`, PostgREST, wire, assert ni concurrency harness. No hubo cambios de código tras el manifiesto v3, rollback, cleanup, SQL remoto ni acciones remotas.
- Se conservan runner v1 idle en bridge, runner v2 y PG v2 en la red v2, y red v3/runner v2/PG v3 con bases parciales. Resultado **NO-GO**; el manifiesto v3 queda consumido y no se repetirá. Cualquier ajuste del harness requiere aprobación separada, hashes nuevos y otro JIT para runtime.

## Revisión estática posterior y preparación del siguiente ciclo

Con autorización humana separada para editar solo el harness, el check de consumo del
nonce y el replay exacto se movieron inmediatamente después de la primera llamada positiva,
antes del escenario non-editor. La prueba conserva el nonce, headers, claims, timestamp y
firmas originales y requiere 409; no se recalculan ni relajan firmas. La revisión
`security-auditor` no encontró hallazgos en el contenido actual; ejecución SQL/runtime de
esta edición **NO REALIZADA**. El set de inputs tiene ahora dos hashes distintos del v1:
la migración con `v_key_id` y el harness actualizado. El manifiesto v4 con hashes nuevos
fue aprobado y ejecutado en PG17 limpio; el resultado PASS de su alcance está en su
sección de resultado.
