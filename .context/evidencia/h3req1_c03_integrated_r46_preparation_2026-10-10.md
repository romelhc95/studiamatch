# H3REQ1 G07 — preparación R46, role RLS del fixture alineado

## Ficha de impacto

- **Componente:** rol sintético de servicio y lectura de la reserva C03.
- **Consumidores:** fixture PG17 aislado, PostgREST local, Edge Runtime y Pages/workerd.
- **Contratos:** Edge replay exige HTTP 200 e idempotencia; no se modifica la aplicación ni las migraciones funcionales. El fixture modela `service_role` administrado por Supabase con `BYPASSRLS`.
- **Evidencia preservada:** logs, manifiestos e inventarios R43/R44/R45; PGDATA de cada run fue tmpfs.
- **Cobertura renovada:** contrato R46, setup SQL integrado, manifiesto 126/126 y drill integrado completo; otros checks se renuevan solo por impacto.
- **Recuperación:** servicios en dos redes internas, credenciales sintéticas, caches R4 read-only; timeout 2400 s, cero retries, stop-on-failure. Logs en el checkout; retirada posterior solo por identidad exacta. Snapshot/TLS/caches/imágenes se preservan.

## Causa demostrada y corrección acotada

R45 terminó exit 1 en el replay Edge con 409 `INVITE_EARLY_RECONCILIATION_REQUIRED`; el probe directo filtrado por correo sintético respondió HTTP 200 y `ZERO`. La assertion SQL anterior encontró la fila con el mismo request ID, correo, actor y `delivery_state=completed`.

El bootstrap crea `service_role NOLOGIN`, cuyo `rolbypassrls` queda falso por defecto. La migración de invitaciones habilita RLS, revoca acceso público, concede SELECT a `service_role` y no crea policy. El JWT del probe usa ese rol; así PostgREST puede devolver cero filas mientras `postgres` ve la reserva. Es un desacuerdo del fixture PG17 con el rol administrado de Supabase, no evidencia de defecto remoto/productivo.

Se cambió solo `tests/sql/h3req1_c03_integrated_extension_setup_r13.sql`: `ALTER ROLE service_role BYPASSRLS` y una aserción `pg_roles.rolbypassrls` que falla cerrado si no quedó aplicado. Es configuración exclusiva del PG17 desechable, no una migration de producto ni un cambio remoto. El contrato R46 nuevo se ejecutó primero en rojo (34/35; solo la aserción nueva falló) y luego verde (35/35) tras la corrección.

## Identidad, validación y ejecución

- Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama `feat/h3req1-sync-20261002`, HEAD baseline `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- WIP al preparar R46: 55 tracked modified y 616 untracked (671 entradas); todo preservado.
- Manifiesto R46: 126 entradas, `sha256sum -c` 126/126 PASS, SHA-256 `1b4047f29e75fca65935b4984b0c9c3023e1944c3f2f8b1f2abe363aeeb23445`.
- Runner R46 SHA-256 `073950df2ff3e0a6744cf53e0024b0cb31b711decd6a3bc2f8cbc22cf867825e`.
- Contrato R46 SHA-256 `5f5b975db0c665eb12b4af42d0e6da46c49b2131f785ee468b3b7d3edfd0f7b7`.
- Setup SQL fixture SHA-256 `2157f16d793613aa4d8bafe6fe2a7d3601c5c11a049752d0641458afaa0f5459`.
- Contrato dentro de `studiamatch-dev`: 35/35 PASS. Bash/Node syntax, `git diff --check`, ShellCheck 0.11.0 sobre el runner en contenedor `network none` y read-only: PASS.
- Docker Desktop: contexto `default`, engine `fc2115b2-c3c4-440e-89c6-26899eb7cb04`, versión 29.8.2. `studiamatch-dev` healthy con `studiamatch-h3req1:20261009-v3` y este candidato en `/app`.
- Imágenes locales fijadas: PostgreSQL 17.11, PostgREST 13, Node y `supabase/edge-runtime:v1.74.3_amd64`; sin pull/build/egress.
- El log R46 debe estar ausente antes de ejecutar; todos los recursos usan sufijo único `r46`.

Comando local autorizado por el alcance humano vigente:

```bash
/usr/bin/timeout --foreground --signal=TERM --kill-after=3s 2400s \
  /bin/bash tests/h3req1_c03_integrated_drill_r46.sh \
  --jit H3-CLOSE-03-INTEGRATED-2026-10-10-R46 \
  --manifest-sha256 1b4047f29e75fca65935b4984b0c9c3023e1944c3f2f8b1f2abe363aeeb23445
```

Al preparar R46, G07 seguía parcial a la espera del replay, sesión/rol y smoke; la ejecución PASS se registra a continuación.

## Ejecución R46 — PASS local

R46 se ejecutó una vez con timeout externo 2400 s y cero retries. El runner emitió el registro final `C03 integrated drill: PASS` y completó las aserciones y retirada exacta. Log sanitizado SHA-256 `0fefdb22984226124a2847c8f9f4a01923a2396569b01309db8239f30b4f1a00`; véase [resultado/inventario R46](h3req1_c03_r46_result_inventory_2026-10-10.md). El manifiesto R46 se archivó en [126 inputs](h3req1_c03_integrated_manifest_r46.sha256).

La lectura de PostgREST devolvió una fila: `requestIdMatches`, actor, correo, rol y user ID coinciden; estado `PENDING`, `reconciliationRequired=false`, entrega `COMPLETED`. Edge replay pasó con la misma invitación, sin segundo Auth email; sesión `aal2`, rol `admin`. También pasaron suspensión persistente, denegaciones Pages/Edge/dispatcher con nonce preservado, finalizador in-flight una sola vez, auditoría/cuota, resume persistente por conexión nueva y assertions finales SQL. El smoke completó. Los recursos de ejecución se retiraron por el propio runner tras PASS; snapshot/TLS/caches quedaron preservados.

G07 se cierra con evidencia del candidato integrado. Métrica actualizada: tablero histórico G01–G10 70%; cierre local G01–G09 7/9 = 77.78%. G08 y G09 siguen abiertos; G10 conserva su requisito remoto/humano.
