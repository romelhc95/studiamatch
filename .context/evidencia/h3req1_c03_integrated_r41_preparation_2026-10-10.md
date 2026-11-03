# G07 C03 integrado R41 — clasificación allowlisted de conflicto Edge

R40 alcanzó la recuperación tras PASS de snapshot, PG17 17.11, PostgREST, login
Pages/workerd, suspensión persistente, dispatcher 403/42501, finalización de Auth
una vez y safe-resume con assertions SQL PASS. Falló el replay Edge con HTTP 409;
R40 solo pudo clasificar `INVITE_EARLY_HTTP_409` porque no permitía aún todos los
códigos de conflicto definidos en el handler.

R41 no cambia producto, SQL, status esperado ni reglas de reintento. Añade a la
clasificación local los códigos Edge existentes para HTTP 409 (`duplicate_ready`,
`duplicate_pending`, `resend_cooldown`, `membership_blocked`,
`onboarding_in_progress`, `role_mismatch`, `reconciliation_required`) y registra
solo clase de código (`ALLOWLISTED`, `UNRECOGNIZED`, `ABSENT` o `STATUS_INVALID`),
status numérico e identificador de clasificación. El cuerpo y el código crudo no
se emiten.

## Inputs y revisión

- Candidato: rama `feat/h3req1-sync-20261002`, baseline HEAD
  `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- Único delta de código sobre el manifiesto R40: `tests/h3req1_c03_login_result.mjs`.
  Runner/contrato R41 tienen nombres, JIT, log y recursos propios; R40 no se reescribe.
- Se archivó el manifiesto R40 exacto, 113 entradas, SHA-256
  `7233b21cc615ff6427e043fdae11cd97b61ebffe8c39a92f11f769c28fbb4799`.
- Contrato R41: 31/31 PASS en `studiamatch-dev`, incluyendo clase conocida
  `duplicate_pending`, códigos desconocidos, código ausente y status inválido.
- `bash -n`: PASS. ShellCheck 0.11.0 local, `--network=none`, read-only: PASS.
- `git diff --check`: PASS. Manifiesto R41 115/115 PASS, SHA-256
  `c8d2f656b7cfb726ea907d336ca92dd55bef602fcda4245304b56c700fbcf4a4`.
- R40 fue inventariado y sus siete contenedores/dos redes internos vacíos se
  retiraron por identidad exacta. Volúmenes, imágenes y caches se conservaron.

## Invocación R41

Una ejecución, timeout 2400 s, stop-on-failure:

```bash
/usr/bin/timeout --foreground --signal=TERM --kill-after=3s 2400s \
  /bin/bash tests/h3req1_c03_integrated_drill_r41.sh \
  --jit H3-CLOSE-03-INTEGRATED-2026-10-10-R41 \
  --manifest-sha256 c8d2f656b7cfb726ea907d336ca92dd55bef602fcda4245304b56c700fbcf4a4
```

El run usa los pines locales R4/R5/R39 y crea recursos R41 aislados. PostgreSQL
17.11 usa PGDATA tmpfs; sus credenciales/usuarios son sintéticos. No lee `.env*`
ni Env de Docker, no usa servicios/cuentas/correo reales y no cambia el checkout
original, `studiamatch-dev`, engine, servicios remotos, imágenes ni configuraciones
globales. Un fallo detiene fases dependientes y preserva log y recursos exactos.

## Resultado ejecutado R41

R41 consumido una vez, exit 1 en `/control/recovery`, status Edge 409,
`errorCodeClass=ABSENT`, clasificación `INVITE_EARLY_HTTP_409`. La evidencia
estática identifica la causa de la ausencia diagnóstica: el handler de
`supabase/functions/admin-invite/index.ts` construye errores como objeto de raíz
`{ error, code, request_id }`; el runtime de prueba R41 leyó
`payload?.error?.code`, estructura anidada que ese endpoint no emite. Esto explica
el campo ausente, no determina todavía el código de conflicto ni por qué el Edge
respondió 409. El siguiente runner lee únicamente `payload?.code` y mantiene la
clasificación cerrada; no lee `error` ni modifica el status esperado.

Antes del fallo pasaron snapshot, cache verifier, PG17 17.11, PostgREST, Pages/login,
suspensión, dispatcher 403/42501, finalización Auth una vez, safe-resume y assertions
SQL. Log sanitizado SHA-256
`eaa8e006c497401d77c9f2f0fb814e565fc347c6e7a5a47086adefdadc1479c7`:
[R41](h3req1_c03_integrated_run_2026-10-10_r41.txt). Inventario y retirada exacta:
[recursos R41](h3req1_c03_r41_resource_inventory_2026-10-10.md).
