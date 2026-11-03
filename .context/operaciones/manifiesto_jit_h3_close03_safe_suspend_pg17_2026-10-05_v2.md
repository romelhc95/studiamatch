# Continuación JIT v2 — safe-suspend PG17 — 2026-10-05

**Estado vigente:** `JIT_V2_SQL_SUBGATE_PASS_NO_GO_REMAINS`. La aprobación fue local y
se consumió para ejecutar únicamente el harness safe-suspend; no autoriza repetición,
integración, servicios remotos ni cleanup.
**Este documento reemplaza solo la autorización pendiente de la etapa final** del
[manifiesto inicial](manifiesto_jit_h3_close03_safe_suspend_pg17_2026-10-05.md); no
autoriza reiniciar los harnesses ya ejecutados ni cambia su resultado.

## Estado exacto de la ejecución parcial

La aprobación inicial cubrió la secuencia local H2→H3, cuota, gateway firmado y
safe-suspend. Preflight inicial: manifiesto padre SHA-256
`0f6a1b598a4a81b8bda51e3dea8112a6effae60eab4fdda8b62b1f4da3be239d`; **40/40 inputs**
transitivos, 0 includes ausentes y 0 hashes diferentes; rama `feat/h3req1-sync-20261002`,
`HEAD=origin/desarrollo=merge-base=4eb4d877a50b012bb630a129bd0c74482c33be9c`, 0 staged.
El preflight actual repitió las 40 comparaciones sin discrepancias.

| Etapa | Resultado observado |
|---|---|
| `h3_from_h2_pro_pg17_harness.sql` | PASS: `h3_from_h2_pro_pg17_harness_ok` |
| `h3_admin_quota_harness.sql` | PASS: `h3_admin_quota_harness_ok` |
| `h3_admin_rpc_signed_gateway_harness.sql` | PASS: `h3_admin_rpc_signed_gateway_harness_ok`; la salida automática mostró filas `set_config` con firmas HMAC sintéticas de test. No se copian los valores aquí; no eran credenciales, claves ni JWT de producto. |
| `h3_safe_suspend_harness.sql` | PASS bajo JIT v2 con stdout redirigido a `/dev/null`; exit code 0 y sin filas de firmas emitidas. |

Antes de la cadena, `pg_isready` respondió accepting connections. Una consulta opcional de
versión falló únicamente por quoting incorrecto en el wrapper PowerShell; no alteró datos.
La versión se verificó después, en modo no SQL, con `pg_config`: PostgreSQL **17.11**.
La cadena SQL completada hasta gateway terminó sin error de harness.

## Recurso parcial preservado

| Propiedad | Estado read-only verificado |
|---|---|
| Contenedor | `h3req1-c03-safe-suspend-pg17-20261005`, ID `88aa68bc11372f5efad73e114be1e5fea822754bf525907d180a8ba46b643d2d`, `running` |
| Imagen | `postgres@sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f` |
| Red / puertos | `network=none`; sin port bindings |
| Datos | `/var/lib/postgresql/data` en tmpfs 1 GiB; sin volumen persistente |
| Montajes | `/candidate/tests/sql`, `/candidate/db/migrations`, `/candidate/db/rollback`; todos `RW=false` |
| Base parcial | `h3_c03_chain`; secuencia válida completada hasta el gateway firmado |

No se detuvo, eliminó ni limpió el recurso. El identificador del contenedor y su DB parcial
son precondición de esta continuación; si el contenedor cambia, no está running o el
preflight difiere, detenerse y solicitar un JIT distinto. No recrear DB ni reejecutar
baseline bajo este manifiesto.

## Paso único aprobado y ejecutado

Antes de ejecutar se recibió aprobación humana explícita para este manifiesto y SHA-256
`c72134417fc9560f1b58d23a2aac3d11042442f2030d6088da7709b89464e581`. Se revalidaron el
hash del manifiesto padre, las 40 entradas transitivas, el ID/estado del contenedor,
imagen, `network=none`, mounts `RW=false`, tmpfs y DB parcial. Todo coincidió; se ejecutó
únicamente dentro del contenedor existente:

```text
psql -X -q -U postgres -d h3_c03_chain -v ON_ERROR_STOP=1 \
  -o /dev/null -f /candidate/tests/sql/h3_safe_suspend_harness.sql
```

El harness emite por consultas sus headers de prueba; por eso `-q -o /dev/null` se vuelve
gate obligatorio para no mostrar ni persistir firmas. El resultado se registra solo como
exit code de `psql`: `0` con `ON_ERROR_STOP=1` significa que se alcanzó el final del archivo
y pasaron todas sus aserciones; cualquier código distinto de `0`, error en stderr o duda
sobre la redirección detiene la operación. No ejecutar manualmente una segunda versión,
no quitar la redirección para buscar el marcador y no repetir el harness.

El único resultado aceptable es que el script compruebe, en esta misma DB efímera: ACL de
`admin_signed_rpc` y funciones iniciadoras revocadas durante la suspensión; pre-request
válido seguido de denegación por privilegios de la llamada `authenticated`; nonce no
consumido; finalizadores service-role para complete/fail/reconcile; fingerprints y
auditoría preservados por la suspensión; y restauración TEST-only de permisos efectivos
originales. Este es un **subgate SQL**, no una prueba HTTP ni un PASS integrado.

Ante cualquier error/noise que contenga firmas, detenerse y preservar el contenedor sin
cleanup; no incluir valores en evidencia. No ejecutar Edge, Auth/correo, PostgREST, Pages,
workerd, otro SQL, Supabase remoto, Git remoto ni cleanup. La salida de los tres harnesses
anteriores no se vuelve a imprimir ni se añade a evidencia.

## Desviación y límites restantes

La primera ejecución, bajo el JIT inicial, mostró en stdout filas `set_config` que
contenían firmas sintéticas de test; por precaución se detuvo antes del safe-suspend.
Luego el JIT v2 fue aprobado y ejecutó únicamente ese harness con `-q -o /dev/null`,
exit code 0 y sin emitir filas. No se copiaron los valores a evidencia; no eran claves,
JWTs ni credenciales de producto. La desviación de logging no invalida los tres PASS
anteriores ni requiere rotación de secretos.

Incluso con exit code 0, H3-CLOSE-03 sigue **NO-GO**: el SQL harness no coordina Pages/
workerd, Edge y PG17; los UAT de componentes permanecen separados; no existe recovery
operativo persistente aprobado. El test usa snapshot de ACL temporal y no es receta de
resume remoto. Se preservan el contenedor y sus datos; cleanup y toda operación remota
requieren JIT independiente.

## Resultado de ejecución JIT v2 — 2026-10-05

- Aprobación humana recibida para este subgate, con SHA previo a ejecución
  `c72134417fc9560f1b58d23a2aac3d11042442f2030d6088da7709b89464e581`.
- Preflight exacto: manifiesto v2 y padre coincidentes; 40/40 hashes transitivos, 0
  includes ausentes y 0 discrepancias; rama/HEAD sin drift; contenedor e imagen fijados,
  PG17 17.11, `network=none`, sin puertos, tmpfs y mounts read-only exactos.
- Ejecución de `h3_safe_suspend_harness.sql` con `psql -X -q -U postgres -d h3_c03_chain
  -v ON_ERROR_STOP=1 -o /dev/null -f ...`: **exit code 0**, sin stdout ni error. Dado
  `ON_ERROR_STOP=1`, se completó el archivo y pasaron las aserciones del harness. No se
  emitieron ni copiaron firmas de prueba.
- Inspección Docker posterior: mismo contenedor ID
  `88aa68bc11372f5efad73e114be1e5fea822754bf525907d180a8ba46b643d2d`, running, digest,
  red, puertos y tmpfs sin cambios. Sin cleanup.
- Resultado: **PASS del subgate SQL safe-suspend**; H3-CLOSE-03 integrado permanece
  **NO-GO** por falta de runner workerd+Edge+PG17 y recuperación operativa persistente.
  El JIT v2 se consumió y no autoriza ningún gate o repetición adicional.
