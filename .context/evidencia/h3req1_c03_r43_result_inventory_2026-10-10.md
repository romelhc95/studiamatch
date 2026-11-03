# H3REQ1 G07 — resultado e inventario R43

## Identidad y resultado

- Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`.
- Rama/HEAD: `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- JIT local: `H3-CLOSE-03-INTEGRATED-2026-10-10-R43`; manifiesto R43: 120 entradas, SHA-256 `acc4b2b733998bd6f5e5be1010c7e7c9e8cc72d26f598d5bcc5c93f21443b096`.
- Comando ejecutado: `/usr/bin/timeout --foreground --signal=TERM --kill-after=3s 2400s /bin/bash tests/h3req1_c03_integrated_drill_r43.sh --jit H3-CLOSE-03-INTEGRATED-2026-10-10-R43 --manifest-sha256 acc4b2b733998bd6f5e5be1010c7e7c9e8cc72d26f598d5bcc5c93f21443b096`.
- Exit: `1`; fase: `edge-first-pages-last-recovery-smoke`; no hubo retry.
- Log sanitizado: [R43](h3req1_c03_integrated_run_2026-10-10_r43.txt), SHA-256 `ec5d23bd171733a98de51bc86f5ba83698a01affe93843f3d903cb9d66b81`.
- Manifiesto R43 archivado sin cambios: [120 inputs](h3req1_c03_integrated_manifest_r43.sha256), SHA-256 `acc4b2b733998bd6f5e5be1010c7e7c9e8cc72d26f598d5bcc5c93f21443b096`.

## Resultado técnico

La fase integrada pasó snapshot íntegro, verificación de caches R4, PG17 17.11, bootstrap H2→H3, esquema auxiliar, fixture sintético, readiness PostgREST, Pages/workerd AAL2, reserva previa a Auth, suspensión persistente, rechazos Pages/Edge/dispatcher, finalizador in-flight exactamente una vez, safe-resume y assertions de recuperación SQL.

El replay directo Edge volvió a responder 409 `INVITE_EARLY_RECONCILIATION_REQUIRED`. El probe read-only de R43 respondió 404 `PGRST125`, por lo que no leyó filas (`rowCountClass=NOT_READ`). La documentación oficial de PostgREST 13 clasifica PGRST125 como ruta inválida en la URL: [PostgREST 13 — Errors](https://docs.postgrest.org/en/v13/references/errors.html#postgrest-error-codes).

La causa demostrada es del **probe del harness**: construyó `/rest/v1/admin_invitations` contra un contenedor PostgREST directo en `http://h3req1-c03-postgrest:3000/`. Ese endpoint no tiene el prefijo del gateway Supabase; PostgREST recibe la ruta con prefijo y devuelve PGRST125 antes de consultar la tabla. No se atribuye el 409 al producto ni se conoce todavía cuál estado persistido exige reconciliación.

Corrección mínima siguiente: fijar el probe read-only a `/admin_invitations`, actualizar su contrato sintético para distinguir endpoint directo PostgREST del gateway, renovar el manifiesto y ejecutar un nuevo drill integrado. No se cambia Edge, Pages/BFF, SQL, los criterios del replay, ni la cantidad de retries. Si la lectura devuelve 200, sus valores se reducen a clases cerradas/booleanos antes de registrarse.

## Recursos R43 inventariados

Todos los recursos propios del run están detenidos, tienen etiqueta de ejecución R43 y no contienen credenciales operativas. El log no usa driver de logs y solo contiene datos sanitizados.

| Contenedor | ID | Imagen fijada | Estado/exit | Límite memoria/CPU |
|---|---|---|---:|---:|
| `h3req1-c03-source-snapshot-20261010-r43` | `e5385c62b15ae0aa1235b1ae7b6d5d1f19214f816c5fac0c0272bfe88330391b` | `node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844` | exited / 0 | 512 MiB / 1 CPU |
| `h3req1-c03-dependency-cache-verify-20261010-r43` | `ae873fc0c1f2785622799060a47724cf5d9ce5a2ce0c9ab81545499dd7fc8867` | `node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844` | exited / 0 | 512 MiB / 1 CPU |
| `h3req1-c03-integrated-runtime-20261010-r43` | `dfcde6ed0d315de76521b74277e230238e660bb70ebfe74eeb1575b68d773487` | `node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844` | exited / 143 (failure stop) | 4 GiB / 2 CPU |
| `h3req1-c03-integrated-pg17-20261010-r43` | `287b6dbc3e6f20974eee0d481206e9af4fc0faf08400fbe1a6ec5fb3bf29db2d` | `postgres@sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f` | exited / 0 | 2 GiB / 2 CPU; PGDATA tmpfs |
| `h3req1-c03-integrated-postgrest-20261010-r43` | `569dd2c7c7a36f9abf53a324594069049b8e053a2f2c391c2640e18a5336a27d` | `postgrest/postgrest@sha256:0a46780309a604cdc8b56c776c6e5e15788ce58174d709e40459ab5a2d44d228` | exited / 255 (failure stop) | 512 MiB / 1 CPU |
| `h3req1-c03-integrated-edge-active-20261010-r43` | `ada9eaa5e0d7fadd9cb508015760d36fc1a6e4bf74981db50f4712dac92d8bd9` | `supabase/edge-runtime:v1.74.3_amd64@sha256:cc355c3d0e9c063a351cad56d1c4c52a3c4d85aff4e1fad9d91688e75f9aad09` | exited / 15 (failure stop) | 1 GiB / 1 CPU |
| `h3req1-c03-integrated-edge-suspended-20261010-r43` | `f3e51bbd39b5059cf031a19d9dc58a13fe5655e68f2d5b7d0cef97dc1c30eb36` | `supabase/edge-runtime:v1.74.3_amd64@sha256:cc355c3d0e9c063a351cad56d1c4c52a3c4d85aff4e1fad9d91688e75f9aad09` | exited / 15 (failure stop) | 1 GiB / 1 CPU |

| Recurso | ID | Decisión |
|---|---|---|
| Red Edge | `4826069afa08345f8dad7f76cc6c625dba0d8f19a6ce7e89df56698babe1d271` | internal=true, 0 adjuntos; preservar hasta registrar y luego retirar selectivamente |
| Red de datos | `036466a9173031af2854375bdfaf9525d9e3a4b5b6f7af25f5d1c65aad903af7` | internal=true, 0 adjuntos; preservar hasta registrar y luego retirar selectivamente |
| Volumen snapshot `h3req1-c03-integrated-source-snapshot-20261010-r43` | etiqueta R43, digest de manifiesto fijado | preservar como evidencia del candidato R43 |
| Volumen TLS sintético `h3req1-c03-integrated-tls-20261010-r43` | etiqueta R43, digest de manifiesto fijado | preservar como fixture de prueba |
| Caches de dependencias R4 | cuatro volúmenes read-only, hashes esperados | conservar; no fueron creados por R43 |
| `studiamatch-dev` | `500931b0f086d29ec9e751e1fd652f9b7ccd357f3eb64daa8751344776162049` | running/healthy, imagen `studiamatch-h3req1:20261009-v3`; conservar |

Todos los contenedores R43 estaban `exited`; las dos redes eran internas con cero contenedores adjuntos. PGDATA fue tmpfs y no dejó datos persistentes. Tras archivar este inventario se retiraron por ID exacto los siete contenedores y las dos redes R43, sin `-v`; se conservaron los dos volúmenes R43, caches, imágenes, `studiamatch-dev` y recursos de otros runs. Verificación de limpieza: `containers=7 networks=2 volumes_preserved=2 images_preserved=true studiamatch-dev_preserved=true`.

## Gate y siguiente paso

G07 sigue **parcial**: suspensión, protección de datos, finalización in-flight y reanudación SQL pasaron; replay idempotente, sesión/rol posteriores y smoke final no se acreditaron. No aumenta la métrica. El siguiente paso es corregir el path del probe, renovar el manifiesto, revisar el diff y ejecutar el drill corregido una vez bajo la autorización local vigente.
