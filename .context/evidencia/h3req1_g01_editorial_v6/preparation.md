# G01 editorial PG17 V6 — preparación y alcance

Fecha: 2026-10-10. Candidato local en `feat/h3req1-sync-20261002`, HEAD
baseline `4eb4d877a50b012bb630a129bd0c74482c33be9c`; antes de esta nota: 55
archivos rastreados modificados, 659 no rastreados y 0 staged.

## Motivo de renovación

V5 ejecutó y reportó PASS de los harnesses editorial, cuota y gateway firmado,
pero su manifiesto de 36 entradas no fijaba `tests/sql/h3_admin_quota_harness.sql`
ni `tests/sql/h3_admin_rpc_signed_gateway_harness.sql`, y el resultado no registró
el SHA del runner. Se conserva V5 como resultado histórico observado, no como
atribución criptográfica completa de esos dos inputs. V6 mantiene las mismas tres
pruebas y fija los 36 inputs anteriores más ambos harnesses realmente ejecutados.

La ruta firmada compara ahora la fila completa `course_editorial_state` como
`to_jsonb(es)` y el conteo de auditoría antes/después del payload autenticado con
`p_version: null`. El harness PG17 directo ya hacía comparación completa de fila.
La migración rechaza NULL/versión stale después de los gates de editor activo y AAL2,
antes del DML. No cambia permisos ni el contrato de RPC.

## Ficha de impacto

- Criterio cliente: edición Admin conserva procedencia, conflicto de versión y
  auditoría atómica con actor/fecha/antes/después.
- Archivos: migración `20261001_h3_course_editorial_audit_availability.sql`,
  harnesses PG17/cuota/gateway firmado y runner V6.
- Consumidores: Admin BFF allowlist → RPC editorial; pruebas PG17 local, cuotas y
  firma/gateway. Checkout original, servicios y datos cloud no se usan.
- Comportamiento preservado: BFF HttpOnly, gateway firmado, cuotas, roles y MFA/AAL2.
- Evidencia preservada: V4 FAIL y V5 PASS observado, sin reescribir archivos.
- Evidencia renovada: V6 manifest 38/38 y tres harnesses en PostgreSQL 17.11
  temporal; V5 no sustituye V6 para los dos harnesses antes omitidos.
- Transición: expand/compatibilidad conserva columnas y RPC legado; la guardia de
  versión rechaza ausencia/stale antes de mutation; rollback es restaurar solo los
  cambios locales de candidato, nunca aplicar rollback a DB remota.
- Permiso: ejecución local PG17 desechable y SQL sintético cubiertos por la
  autorización humana local H3REQ1 del 2026-10-10. Sin acceso remoto ni secretos.
- Gate: G01 cierra solo si los tres harnesses reportan exit 0 y marcadores exactos,
  el cleanup del contenedor fijado pasa y la revisión posterior no deja bloqueantes.

## Inputs y ejecución fijada

- Manifiesto: `inputs-v6.sha256`, 38 entradas, SHA-256
  `71aab76f4dae5c881151f024f830fb79769b9ac7d4868dd7797d71e0a4ed76a3`.
- Runner: `tests/h3req1_c03_atomicity_pg17/run_editorial_atomicity_v6_once.sh`,
  SHA-256 `68e3b323a426023a03b079fddfaf6fa26044a813f9bb843df4eca99d45058e34`.
- Imagen existente: `postgres@sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f`,
  local ID confirmado `sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f`.
- Runtime local: Docker Desktop/WSL, contexto `default` sobre
  `unix:///var/run/docker.sock`, Linux server 29.8.2.
- Un contenedor temporal único, `--pull=never --network=none`, 2 CPU, 2 GiB,
  PGDATA/`/tmp` en tmpfs, `POSTGRES_HOST_AUTH_METHOD=trust` solo para fixtures
  sintéticos. SQL, migraciones y seed montados read-only. No recibe `.env*`,
  secretos, cuenta, sesión ni datos operativos.
- Cada harness tiene timeout 180 s; listo PG17 con hasta 60 consultas espaciadas
  0.5 s. Stop-on-failure y cero retries. El trap valida identidad/labels y retira
  únicamente el contenedor creado por la invocación; la salida registra fase,
  código y exit, sin volcar stdout/stderr crudo del SQL.
- Comando local: `bash tests/h3req1_c03_atomicity_pg17/run_editorial_atomicity_v6_once.sh`.

## Revisión previa

Sintaxis Bash (`bash -n`) PASS; manifiesto SHA coincide y `sha256sum --check
--strict` confirma 38/38. La comparación de rutas muestra exactamente las dos
entradas agregadas sobre V5. El diff V5→V6 del runner se limita a rutas/identidad
V6, pin del manifiesto y conteo 38. El comando real y su exit se registrarán en el
log `pg17-editorial-and-signed-gateway-v6.txt`; esta nota no declara runtime PASS.
