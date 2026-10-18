# H3REQ1 G07 — resultado e inventario R45

## Identidad y resultado

- Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`.
- Rama/HEAD: `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- R45 se ejecutó una vez, timeout 2400 s, y terminó **exit 1** en `edge-first-pages-last-recovery-smoke`.
- Manifiesto R45: 124 filas, SHA-256 `791c36132ba4fd7e8acf9c0fff332a637a382333433f379ff428aa8f09f9a0b4`, archivado en [manifiesto R45](h3req1_c03_integrated_manifest_r45.sha256).
- Runner SHA-256 `6fdf1c2fde7eadfea6b189d4bfd0fe559b5efdd827fd6fa528f02017b80ac4b9`.
- Log sanitizado [R45](h3req1_c03_integrated_run_2026-10-10_r45.txt), SHA-256 `7cf304b4ac961b184d96e239870e3bd52b2fabfa530d28a69b879d2314bfcebc`.
- Una tentativa de despacho anterior terminó exit 77 (`invalid manifest SHA-256`) antes de ejecutar Docker; se comparó el pin extraído del documento con el archivo y luego el runner inició una vez. No creó recursos.

## Resultado técnico

Pasaron la copia/fuente 124/124, verificación de caches R4, PostgreSQL 17.11, bootstrap H2→H3, setup de cuota/gateway, fixture sintético, readiness de PostgREST, login Pages/workerd AAL2, reserva antes de Auth, suspensión persistente, denegaciones Pages/Edge/dispatcher, finalizador in-flight exactamente una vez, safe-resume y assertions SQL recuperadas.

El replay Edge respondió HTTP 409 `INVITE_EARLY_RECONCILIATION_REQUIRED`. El probe PostgREST directo respondió HTTP 200 y `rowCountClass=ZERO`, incluso filtrando por el correo sintético allowlisted. La assertion SQL inmediatamente anterior había confirmado la fila finalizada mediante `request_id`, correo y actor, con `delivery_state=completed`. R45 descarta que el filtro JSON original fuera la única explicación; el replay sigue siendo FAIL y G07 no se cierra.

La inspección del contrato local demuestra una causa del fixture: el bootstrap crea `service_role NOLOGIN` sin `BYPASSRLS`; la migración habilita RLS en `admin_invitations`, revoca sus grants públicos y da SELECT solo a `service_role`, sin policy para ese rol. El probe firma como `service_role`. En ese estado PostgreSQL devuelve una colección vacía bajo RLS aunque una assertion como `postgres` vea la fila. Esto explica el `ZERO` del PostgREST de la prueba; no demuestra un defecto del servicio remoto ni del producto en Supabase, donde `service_role` es un rol administrado. Se corregirá solamente la configuración del rol sintético en el setup integrado aislado y se comprobará la propiedad en PG17 más el replay completo.

## Fases logradas y pendiente

| Fase | Resultado |
|---|---|
| Snapshot, hashes y caches | PASS, 124 inputs; caches con digests fijados |
| PostgreSQL/bootstrap/setup | PASS; PG 17.11 |
| Pages/workerd health, auth | PASS; sesión AAL2 sintética, cookies observadas |
| Suspensión, rechazos y finalización | PASS; finalizador ejecutado una vez |
| Resume/SQL recuperado | PASS |
| Replay Edge | FAIL; 409 `INVITE_EARLY_RECONCILIATION_REQUIRED` |
| Probe PostgREST | HTTP 200, `ZERO`; clasificación local indica RLS del rol de fixture |
| Sesión/rol tras replay y smoke final | No alcanzados |

## Recursos R45

`run_nonce=1777468-1791658546557267929-25635-20692`; todos los recursos enumerados llevan JIT, manifiesto y nonce coincidentes. No se leyó ni guardó `Env`.

| Recurso | ID | Imagen / estado y límite |
|---|---|---|
| `h3req1-c03-source-snapshot-20261010-r45` | `7b5a200fd5436916695cfb6e92c66a899b66318f9d3b3ae96802fc0cabd19873` | Node fijado; exited 0; 512 MiB / 1 CPU |
| `h3req1-c03-dependency-cache-verify-20261010-r45` | `83e40bb7fa9d14d9ad6b70a29de2975737b2e2256892abed3b05116004c579a0` | Node fijado; exited 0; 512 MiB / 1 CPU |
| `h3req1-c03-integrated-runtime-20261010-r45` | `f10e68c6470ca09716efffa7e9168e57c9210db17a19d8c8f44d91b6e79e30db` | Node fijado; exited 143 al detener servicios; 4 GiB / 2 CPU |
| `h3req1-c03-integrated-pg17-20261010-r45` | `92a14897eb0f7e320c93d0f156855f73c13d2dbbf7abe7287717dcb80d067d8a` | PostgreSQL fijado; exited 0; 2 GiB / 2 CPU; PGDATA solo tmpfs |
| `h3req1-c03-integrated-postgrest-20261010-r45` | `3f6dfcec2d1c42c308191d8680f2fe5a4e9bdf5711621e595b22c74b7fd3cfb0` | PostgREST fijado; exited 255; 512 MiB / 1 CPU |
| `h3req1-c03-integrated-edge-active-20261010-r45` | `2820b0a21b9297bdfa56dd75eff5297446c3529e5ac3811290d37734c5016079` | Edge Runtime fijado; exited 15; 1 GiB / 1 CPU |
| `h3req1-c03-integrated-edge-suspended-20261010-r45` | `4316bb757930adea454432a895796461d6500727969adf6f170e0de9c7f9b04d` | Edge Runtime fijado; exited 15; 1 GiB / 1 CPU |
| Red `h3req1-c03-integrated-edge-20261010-r45` | `9df8ba68cf73e4a137043e33a0811f6ca70347168e62281667223c02ba8196bf` | interna, cero adjuntos |
| Red `h3req1-c03-integrated-data-20261010-r45` | `3a0dbc73f53f516b1d78d250a38ebe28c7f9762894c65ea138adb4d1facf3e4c` | interna, cero adjuntos |

Se preservan los volúmenes `h3req1-c03-integrated-source-snapshot-20261010-r45` y `h3req1-c03-integrated-tls-20261010-r45`, más los cuatro caches R4 read-only, imágenes y `studiamatch-dev`. No se borró ningún volumen. Tras archivar este inventario, la retirada verificó manifiesto, nonce, IDs completos y estado: se quitaron los siete contenedores detenidos y dos redes internas vacías, sin `-v`; los dos volúmenes R45 siguen presentes y `studiamatch-dev` siguió healthy. Dos preflights de retirada no mutaron recursos: el primero usó un pin tipeado incorrecto; el segundo comparó IDs completos con la salida abreviada de Docker. El tercero enumeró con `--no-trunc`, pasó y retiró exclusivamente los IDs documentados.

## Estado del gate

G07 sigue parcial. Métricas sin cambio: G01–G10 histórico 60%; G01–G09 local 6/9 = 66.67%. El siguiente cambio es limitado al rol sintético `service_role` del setup integrado: debe activar BYPASSRLS como en el entorno administrado y comprobar ese atributo antes de PostgREST. No se modifican migrations funcionales, policies remotas, queries de negocio ni el checkout original.
