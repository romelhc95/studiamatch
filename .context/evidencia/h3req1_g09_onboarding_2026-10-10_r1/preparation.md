# H3REQ1 G09 — onboarding local aislado R1

Fecha: 2026-10-10. Candidato: rama `feat/h3req1-sync-20261002`, HEAD baseline
`4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Ficha de impacto

- Criterio: invitación y onboarding local, separada de cualquier cuenta existente.
- Consumidores: Admin BFF/HttpOnly, Edge `admin-invite` simulado, mock de inbox/Auth,
  gateway firmado local, SQL PG17 y páginas de callback/contraseña del build Pages.
- Contratos preservados: TOTP/MFA del administrador sintético; sesiones HttpOnly;
  permisos admin/user; tokens de invitación de un solo uso; contraseña solo al BFF Auth;
  redirect allowlist; TTL, revocación, expiración, reenvío e idempotencia.
- Prueba: runner existente `tests/h3_invitation_uat.mjs`; 10 casos `INV-013`, `008`,
  `001`, `002`, `009`, `007`, `003`, `004`, `005`, `012`; spacing mínimo declarado
  por el test, cero retries.
- Evidencia preservable: PG17 harness R46, build estático r2, dependencias fijadas,
  UAT visual R9 48/48 y 144/144 con 144 hashes. El onboarding usará PG17 tmpfs nuevo,
  credenciales sintéticas, red Docker interna y mock inbox; no `.env*`, servicios remotos,
  correo real ni identidades reales.
- Recuperación: ante fallo se preservan PG17/red y resumen sanitizado; el trap solo detiene
  el app container de la corrida por ID/label exactos. Ante PASS se conserva el resumen y
  se retiran app, PG17 tmpfs y red exactos; no hay volúmenes persistentes.
- Transición: expand/compatibilidad y rollback se conservan; deploy/contract remotos quedan
  pendientes. Esta corrida no aplica cambios a servicios remotos.

## UAT visual R9 completada

R9 PASS: 48/48 casos, 144/144 viewports, 144 capturas verificadas por SHA-256 y cero
retries. Resumen y artefactos en `../h3req1_g09_uat_2026-10-10_r1/h3-expanded-r9/`;
la matriz y el manifest del candidato viven allí. La evidencia R8 previa permanece
intacta según su manifiesto.

## Preparación del onboarding

Salida previa: rama/HEAD correctos; `studiamatch-dev` healthy con imagen
`studiamatch-h3req1:20261009-v3`; los fixtures R9 fueron retirados exactamente. El runner
de onboarding reutiliza la imagen local y volúmenes existentes, crea una base PG17 tmpfs
nueva y el app temporal sin publicar puertos. Ambos contenedores usan synthetic-only env;
la red es interna y las fuentes/dependencias se montan read-only. El test captura solo
casos y resultados; errores se reducen a fase/código sanitizado.

Runner fijado antes de la ejecución: `h3req1_g09_onboarding_local_runner_r1.sh`, SHA-256
`f930b52de6ef50a1e66958b9f0d6feaeac962d54960568c937675322eac670f3`. Los inputs UAT y
harness relevantes se fijan en `input-manifests/source-onboarding-r1.sha256` al comenzar
el runner; sus hashes previos son `tests/h3_invitation_uat.mjs`
`f006db83cd578ad6a40302ae2d43aa3cffc11574bbe7760e4ac3dc272e4caa2e`,
`tests/sql/h3_invitation_onboarding_harness.sql`
`6b956e63d0860f5bb2e9aa8fef98fe07223b891060245b11186f78d9d0f8e69b`, y
`tests/sql/h3_invitation_edge_runtime_harness.sql`
`2233bf419c2e9c1a1367f34f915bbcb188cf7ba0e818a14abbf49cb4d44d5b5f`.

Revisión previa: `bash -n` pasó; ShellCheck 0.11.0 pasó en contenedor local
`--network none --read-only`; el test enumera exactamente los diez casos fijados y exige
spacing mínimo 20,100 ms. El runner usa imagen app `sha256:5a1c95a7…ca63`, PostgreSQL
17.11 `sha256:d74eeac9…ec46f`, credenciales sintéticas generadas en memoria, mounts
read-only de código, red interna y PGDATA tmpfs. Comando a ejecutar una vez:
`bash .context/evidencia/h3req1_g09_onboarding_local_runner_r1.sh`.

## Resultado

### R1 — detenido antes de Pages/Playwright

Exit 1 en `pg17-fixture-seed-after-tmpfs-reset` con
`PG17_H3_HARNESS_RESEED_FAILED`. El log sanitizado del harness termina en
`tests/sql/h3_pg17_harness.sql:190`: el `\ir` del harness no pudo abrir
`/candidate/db/seeds/h3_admin_seed_local.sql`. Causa demostrada: el runner montaba
`tests/sql` y `db/migrations` read-only, pero omitía `db/seeds`, requerido por el
harness. Log SHA-256 `2d52a9ad8451b658d150afd425ef0577dadb683d12d850b931b186c0be2396ba`.

La etapa se detuvo antes de migraciones de cuota/gateway, Pages/workerd y los 10 casos;
no hay resultado de onboarding. El trap detuvo el app si existía (no se creó) y dejó
PG17/red para diagnóstico. PG17 temporal ID
`921572248f470d92a71b136d7a2d79c03bf3f6508dd34ee63907e8b98dc1c39b`, red interna ID
`2f8f32161b4c38e1d218da740cf7c2c8bb9d7adf557dbd61d1a8b0de780e64e8`; ambos llevan el
label exacto `h3req1-g09-onboarding-20261010-r1`. PG17 solo tiene mounts bind read-only
de migraciones y tests SQL y PGDATA tmpfs; no hay volumen persistente ni datos operativos.
La corrección R2 conserva R1 y agrega solo `db/seeds` read-only. Su ejecución aún está
pendiente.
