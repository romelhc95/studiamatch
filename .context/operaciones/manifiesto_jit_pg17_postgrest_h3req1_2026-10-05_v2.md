# Manifiesto JIT v2 — PG17/PostgREST local H3REQ1 — 2026-10-05

**Estado:** `JIT_SQL_FAILED_STOPPED` — aprobado y ejecutado localmente; el signed-gateway SQL harness falló; no se ejecutaron más SQL ni wire.
**Alcance:** únicamente bootstrap aislado y gate SQL/wire local PG17/PostgREST; sigue excluyendo servicios del producto y operaciones remotas.
**Manifiesto anterior:** [intento detenido](manifiesto_jit_pg17_postgrest_h3req1_2026-10-05.md), SHA-256 `45654420e7e3ce00a362b7e91a3877f129789a655ccf6ce45ccc1e087434de12`. Su intento falló antes de npm config resolution. Su autorización expiró y **no se reutiliza**.

## Motivo de la nueva solicitud

El JIT anterior fue aprobado, pero el comando npm especificó `/dev/null` para `userconfig` y `globalconfig`; npm abortó al detectar la misma ruta cargada dos veces. No comenzó instalación ni descarga. Por regla de parada no se reintentó y no se ejecutó SQL.

Este manifiesto corrige únicamente esa ambigüedad usando dos archivos npm vacíos, separados y efímeros dentro del runner. Conserva la resolución por lockfile, registry fijado, `--omit=dev` y `--ignore-scripts`. La aceptación de riesgo de egress del manifiesto v1 expiró con el fallo; esta solicitud requiere **nueva aprobación explícita**, incluida aceptación del mismo riesgo MEDIUM.

## Baseline actual y cierre de inputs

| Campo | Valor de preparación (solo lectura) |
|---|---|
| Worktree | `/home/romel/src/studiamatch-h3req1-sync-20261002` |
| Rama / HEAD / `origin/desarrollo` | `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c` / `4eb4d877a50b012bb630a129bd0c74482c33be9c`; merge-base coincide, divergencia `0/0`. |
| Estado WIP | 102 entradas: 0 staged, 48 tracked modificadas, 54 untracked. Preservar íntegramente; no stagear ni editar fuentes. |
| Mount de candidato | `/candidate` → worktree exacto, `RW=false`. |
| Inputs transitivos | El manifiesto v1 fijado arriba contiene **74 SHA-256** (57 SQL/harness); recalcularlos todos y exigir 74/74 antes de ejecutar. El manifiesto v1 debe conservar el SHA indicado. |
| Red interna existente | `h3req1-jit-internal-20261005`, Docker ID `f54379669c125d32f02120b0c0f74d07b56cf3df8c973a3ae6c869e0cf8646b9`, `internal=true`, vacía en este preflight. Revalidar identidad/estado antes de usar; no recrear ni limpiar. |
| Runner v1 existente | `h3req1-node22-jit-20261005`, Node `v22.23.2`, imagen digest `sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844`; sigue running en `bridge` con solo los cuatro mounts read-only aprobados. No reutilizar para npm v2 y no detener/desconectar/eliminar sin JIT de cleanup. |

La lista completa de hashes de archivos se hereda solo por referencia criptográfica al manifiesto v1. Antes de ejecutar, verificar su SHA-256 exacto, reparsear las 74 filas y recalcularlas desde el mismo mount read-only. Cualquier diferencia de hash, rama, HEAD, estado baseline, mount, digest o estado/ID de la red invalida esta solicitud: detenerse y presentar otro manifiesto.

## Recursos y secuencia cuya autorización se solicita

No crear recursos antes de aprobar y repetir el preflight. No leer `.env*` ni montar el checkout completo.

### Bootstrap del runner (único egress autorizado)

1. Crear el contenedor `h3req1-node22-jit-v2-20261005` desde `node:22@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844`, inicialmente solo en el bridge existente. Montar read-only únicamente `tests/` → `/candidate/tests`, `web/package.json`, `web/package-lock.json` y `web/vendor/` desde el worktree indicado. No montar `.env*`, `web/node_modules` ni el resto del repositorio. `HOME=/tmp/h3req1-node-home`.
2. Antes de instalar, verificar `node --version` (`v22.*`) y crear dentro del filesystem efímero del runner dos archivos distintos y vacíos: `/tmp/h3req1-node-user.npmrc` y `/tmp/h3req1-node-global.npmrc`. No incluir credenciales ni otras opciones npm.
3. Ejecutar exactamente una vez:

   ```sh
   npm ci --prefix /candidate/web --omit=dev --ignore-scripts \
     --userconfig=/tmp/h3req1-node-user.npmrc \
     --globalconfig=/tmp/h3req1-node-global.npmrc \
     --cache=/tmp/h3req1-node-cache \
     --registry=https://registry.npmjs.org
   ```

   Única salida de red autorizada: esta instalación bloqueada por `package-lock.json` y el registry indicado. Docker bridge no aplica filtro FQDN. No usar scripts, dependencias dev, credenciales, configuración npm preexistente ni otro destino. Si falla, detenerse sin reintentar ni iniciar PG/SQL.
4. Verificar de nuevo Node `v22.*` y `@supabase/supabase-js` `2.109.0`. Solo tras ambos PASS, conectar el runner v2 a `h3req1-jit-internal-20261005` y desconectarlo del bridge. Ningún runner tendrá egress durante SQL/wire.

### PG17/PostgREST y bases efímeras

- Crear `h3req1-pg17-jit-20261005` con la imagen local `postgres:17`, digest `sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f`; revalidar el digest local, no hacer pull. Red interna únicamente, sin puertos publicados ni volumen persistente; montar `/var/lib/postgresql/data` como tmpfs. Montar read-only solo `tests/sql`, `db/migrations`, `db/rollback` y `db/seeds`. Usar password sintético local `postgres`; no imprimir ni persistir secretos de prueba.
- Crear `h3req1-postgrest-jit-20261005` con `postgrest/postgrest:v13.0.7@sha256:0a46780309a604cdc8b56c776c6e5e15788ce58174d709e40459ab5a2d44d228`; revalidar el digest local, no hacer pull. Únicamente en la red interna, sin puertos publicados; escuchar en `0.0.0.0` dentro de esa red. Database `h3_pro_chain_gate`, schema `public`, anon role `anon`, puerto interno `3233` y pre-request `public.h3_admin_rpc_signed_gateway_pre_request`. No habilitar otros hosts/rutas.
- En PostgreSQL ejecutar, con `ON_ERROR_STOP`, esta secuencia exacta; `psql`/`createdb` corren dentro del contenedor PG:
  1. Base `postgres`: `tests/sql/h2_pg17_harness.sql`, luego `tests/sql/h2_pro_pg17_harness.sql`.
  2. `h3_gate`: `tests/sql/h3_pg17_harness.sql` con defaults.
  3. `h3_pro_gate`: el mismo `h3_pg17_harness.sql` con `h3_pro_baseline=1`.
  4. `h3_pro_chain_gate`: `h3_from_h2_pro_pg17_harness.sql`, `h3_admin_quota_harness.sql`, `h3_admin_rpc_signed_gateway_harness.sql`, `h3_safe_suspend_harness.sql`, en ese orden.
  5. `h3_future_contract_gate`: repetir los cuatro harnesses de la cadena con `h3_contracted_baseline=1` solo en `h3_from_h2_pro_pg17_harness.sql`.
  6. En `h3_pro_chain_gate`, ejecutar `h3_quota_postgrest_fixture.sql`; después reaplicar `db/migrations/20261004_h3_admin_rpc_signed_gateway_payload_bound_wrapper.sql`. Arrancar PostgREST en la red interna. Desde runner v2, ejecutar `tests/h3_admin_quota_postgrest.mjs` exclusivamente contra `http://h3req1-postgrest-jit-20261005:3233` con fixtures efímeras; luego `h3_quota_postgrest_assert.sql` en esa base.
  7. Ejecutar `tests/sql/h3_invitation_reservation_concurrency.sh` solo contra `h3_gate`, con identidades/correos sintéticos.

Los fixtures/JWT/firmas/secretos de PostgREST son locales, sintéticos y efímeros; no se guardan en logs/evidencias. La lista de archivos SQL/harness permitidos es exactamente la fijada por las 74 filas del manifiesto v1. No ejecutar GitHub Actions ni ningún workflow remoto.

## Riesgo MEDIUM y aceptación nueva requerida

| Campo | Registro |
|---|---|
| Causa | El bridge Docker no filtra destinos por hostname; `npm ci` descarga paquetes durante un único bootstrap. |
| Mitigación | Contenedor fijado por digest; solo manifests/tests/vendor read-only; dos configs npm vacíos y distintos; lockfile/tarball con hash; `--omit=dev --ignore-scripts`; HOME/cache efímeros; sin secretos; desconexión de bridge antes de SQL/wire; test URL fijada a hostname/puerto exactos. |
| Riesgo residual | Durante el único `npm ci`, una dependencia/registry comprometido podría solicitar otro destino externo. No existe filtro técnico FQDN en bridge. |
| Owner / vencimiento | Romel. La aceptación nueva aplica solo a este bootstrap, expira al éxito/fallo de `npm ci` o a las 2026-10-06 23:59 UTC, lo que ocurra primero. |
| Aceptación humana | Aprobada expresamente el 2026-10-05: “apruebo la V2 y riesgo local”. Alcance limitado a este manifiesto; aceptación del riesgo MEDIUM solo hasta que `npm ci` terminara. El bootstrap terminó correctamente; esta aceptación de egress expiró entonces. |

## Límites y parada

El JIT solicitado no autoriza Supabase Free/Pro, SQL remoto, Auth/reset/correo/factores, secretos de producto, Cloudflare, Git remoto, CI, push/PR/merge, deploy, Certification/Production ni GO Development. No se autoriza cleanup: conservar red, runner v1/v2, contenedores, bases y datos al terminar. Su eliminación, detenerlos o cambiarles networking requiere JIT independiente. Ante fallo, preservar logs sanitizados, no reintentar, no hacer rollback remoto y mantener NO-GO.

## Aprobación y resultado de ejecución JIT v2 — 2026-10-05

- Aprobación recibida en respuesta humana explícita: “apruebo la V2 y riesgo local”. SHA-256 del manifiesto v2 aprobado antes de ejecutar: `148f45c14a1b4e0bf9e930cde51ac0b8e410554599dacdc0eeae0ebc66439af7`.
- Preflight: rama/HEAD/`origin/desarrollo` y WIP coincidentes con la tabla; manifiesto v1 con SHA esperado y **74/74 inputs** coincidentes; mount read-only exacto; digests locales correctos; red interna existente con ID esperado y vacía; nombres v2/PostgreSQL/PostgREST libres.
- Runner `h3req1-node22-jit-v2-20261005`: imagen fijada y mounts read-only exactos. Node `v22.23.2`. Los dos `.npmrc` temporales eran distintos y vacíos. `npm ci --omit=dev --ignore-scripts` PASS: 90 paquetes añadidos, 91 auditados, 0 vulnerabilidades. `npm ls` confirma `@supabase/supabase-js@2.109.0`. Runner desconectado de `bridge` y conectado solo a la red interna.
- PostgreSQL `h3req1-pg17-jit-20261005`: digest fijado, solo red interna, sin puerto publicado, datos en tmpfs y los cuatro directorios autorizados read-only. `pg_isready` PASS.
- SQL completado antes del fallo: `h2_pg17_harness.sql`; `h2_pro_pg17_harness.sql` (incluyó el rechazo esperado del rollback guard); `h3_pg17_harness.sql` en `h3_gate` y `h3_pro_gate`; cadena `h3_from_h2_pro_pg17_harness.sql` y `h3_admin_quota_harness.sql` en `h3_pro_chain_gate` PASS.
- **FAIL bloqueante:** `tests/sql/h3_admin_rpc_signed_gateway_harness.sql:70` devolvió `column reference "key_id" is ambiguous` dentro de `private.h3_admin_rpc_gateway_verify_payload(text,jsonb,text)`, línea 117. La consulta `gateway_key.key_id = key_id` es ambigua entre columna y variable PL/pgSQL. No se reintentó.
- Parada: no se ejecutó `h3_safe_suspend_harness.sql`, no se creó `h3_future_contract_gate`, no se ejecutaron PostgREST, wire, assert ni concurrency harness. No se modificó código, no se aplicó rollback y no se hizo cleanup. Se conservan runner v1 en bridge, runner v2 y PostgreSQL en la red interna, y las bases/datos parciales en tmpfs.
- Resultado: **NO-GO H3-CLOSE-02/03**. El JIT v2 quedó consumido por el fallo; cualquier corrección de fuente cambia hashes y exige revisión, manifiesto nuevo y aprobación JIT nueva antes de repetir o continuar SQL/wire. No hubo operaciones remotas.
