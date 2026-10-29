# H3REQ1 G07 — resultado e inventario R44

## Identidad y resultado

- Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`.
- Rama/HEAD: `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- Runner R44 SHA-256: `63ee41945b3c4083da4b94a87fb055fb6982a0a282d9249f3d179b099b8540c7`.
- Manifiesto R44 archivado: 122 filas, SHA-256 `e25f62b86bd99d2e20cc07e3da09f172d7b3e3dee8f9ba740135b0f3356790c6`.
- Comando: `/usr/bin/timeout --foreground --signal=TERM --kill-after=3s 2400s /bin/bash tests/h3req1_c03_integrated_drill_r44.sh --jit H3-CLOSE-03-INTEGRATED-2026-10-10-R44 --manifest-sha256 e25f62b86bd99d2e20cc07e3da09f172d7b3e3dee8f9ba740135b0f3356790c6`.
- Exit `1`, fase `edge-first-pages-last-recovery-smoke`, sin retry.
- Log sanitizado [R44](h3req1_c03_integrated_run_2026-10-10_r44.txt), SHA-256 `fe609c318eb06fc28502a581896282315f481a0964d2a79414976e7fc7d95a7f`.
- [Manifiesto R44 archivado](h3req1_c03_integrated_manifest_r44.sha256).

## Resultado técnico

Pasaron snapshot 122/122, caches de dependencias, PG17 17.11, bootstrap H2→H3, setup sintético, readiness PostgREST, login Pages/workerd AAL2, reserva previa a Auth, suspensión persistente, rechazos Pages/Edge/dispatcher, finalizador in-flight exactamente una vez, safe-resume y assertions SQL recuperadas.

El replay Edge respondió 409 `INVITE_EARLY_RECONCILIATION_REQUIRED`. El probe directo corrigió el path y respondió HTTP 200, pero su filtro por `metadata->>request_id` devolvió `rowCountClass=ZERO`. No se expuso ningún valor de fila. La assertion SQL previa, ejecutada antes de suspender, confirmó una reserva para el mismo actor, correo sintético y request ID; por ello el resultado del probe no identifica todavía cuál campo o visibilidad produjo el 409.

No se modifica aún el producto ni se atribuye la diferencia a RLS, parser o persistencia. El siguiente diagnóstico leerá, solo en la base nueva desechable, como máximo dos filas por el correo sintético fijo `c03-inflight@local.test`. El clasificador comparará actor/request ID/correo/rol y devolverá solo cardinalidad, clases y booleanos; el replay seguirá exigiendo 200. Así se distingue si falla el filtro JSON, la visibilidad de filas o un predicado del estado.

## Recursos R44 inventariados

Los siete contenedores del run están detenidos y llevan etiquetas R44 con manifiesto y nonce coincidentes. No hay variables `Env` ni metadata cruda en este inventario.

| Contenedor | ID | Imagen | Estado/exit | Límite |
|---|---|---|---:|---:|
| `h3req1-c03-source-snapshot-20261010-r44` | `9323b1709ecd54fa55e1f78d926f7ca16187e84e1d135b449191c0a27006e662` | `node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844` | exited / 0 | 512 MiB / 1 CPU |
| `h3req1-c03-dependency-cache-verify-20261010-r44` | `0ef68d1f1cbc2077ac3f670818dabd48e9ff48268fd2874aa6e4f4d8ce5c5e18` | `node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844` | exited / 0 | 512 MiB / 1 CPU |
| `h3req1-c03-integrated-runtime-20261010-r44` | `db4a1cd45e28292d79361694c7cc7dc3177e003bd763ff3c2aae01a3b93b1569` | `node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844` | exited / 143 | 4 GiB / 2 CPU |
| `h3req1-c03-integrated-pg17-20261010-r44` | `6fde4eb4cab9167f9690efb3a6747e9bbd680290fb405325989543995f3c3ec6` | `postgres@sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f` | exited / 0 | 2 GiB / 2 CPU; PGDATA tmpfs |
| `h3req1-c03-integrated-postgrest-20261010-r44` | `049d47a3c0469aa250c6f34ddbdfabbe60cd9f20559db57afbb74e2119399c2d` | `postgrest/postgrest@sha256:0a46780309a604cdc8b56c776c6e5e15788ce58174d709e40459ab5a2d44d228` | exited / 255 | 512 MiB / 1 CPU |
| `h3req1-c03-integrated-edge-active-20261010-r44` | `6be6aa7c85ad00f9789746fef88e394ece910f7fce198b42ef06ba9128eaef63` | `supabase/edge-runtime:v1.74.3_amd64@sha256:cc355c3d0e9c063a351cad56d1c4c52a3c4d85aff4e1fad9d91688e75f9aad09` | exited / 15 | 1 GiB / 1 CPU |
| `h3req1-c03-integrated-edge-suspended-20261010-r44` | `29e2bc7fbc19bc6d850d8f68bbb30b5e746086ae2a9744d66fc0e56416a4e0cb` | `supabase/edge-runtime:v1.74.3_amd64@sha256:cc355c3d0e9c063a351cad56d1c4c52a3c4d85aff4e1fad9d91688e75f9aad09` | exited / 15 | 1 GiB / 1 CPU |

Las redes internas R44 `30c4591e79e8b59c173c7504281bb0f6a56789ef6b24492146662fccd1315dde` y `feb93e9aebfc6e599ce2ba57882d73d1e8d71da9fed19a3fceabc58a2a8ba958` tenían cero contenedores adjuntos. Los volúmenes `h3req1-c03-integrated-source-snapshot-20261010-r44` y `h3req1-c03-integrated-tls-20261010-r44` se conservan; PGDATA solo fue tmpfs. También se conservan caches R4, imágenes, `studiamatch-dev` y todos los recursos de otros runs. Tras archivar este inventario se retiraron los siete contenedores y dos redes R44 por ID/etiquetas exactos, sin `-v`; verificación: `containers=7 networks=2 volumes_preserved=2 images_preserved=true studiamatch-dev_preserved=true`.

## Estado del gate

G07 sigue parcial. R44 demuestra que la ruta directa está corregida, pero no identifica el estado persistido ni alcanza replay 200, sesión/rol posterior o smoke final. Métrica sin cambio. La retirada selectiva de los siete contenedores y dos redes R44 se completó sin `-v` después de preservar el inventario.
