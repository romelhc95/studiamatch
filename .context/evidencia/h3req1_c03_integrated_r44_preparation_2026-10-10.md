# H3REQ1 G07 — preparación R44 tras corregir la ruta del probe

## Ficha de impacto

- **Componente:** probe read-only del harness de replay C03.
- **Consumidores:** runtime integrado, PostgREST local directo y contratos R43/R44.
- **Contrato funcional preservado:** replay Edge debe devolver 200 para la misma invitación y no hacer una segunda llamada Auth; Pages/BFF, Edge, SQL y comportamiento de producto no cambian.
- **Pruebas preservadas:** cobertura C03 SQL/R42/R43 que mantenga inputs; se conservaron resultado, log y manifiesto histórico R43.
- **Pruebas renovadas:** contratos R43/R44, snapshot del nuevo manifiesto y drill integrado R44 por el probe corregido.
- **Recuperación:** redes internas por run; PGDATA tmpfs; credenciales solo sintéticas; snapshots/logs sanitizados. En fallo, runner para solo servicios propios; inventario exacto previo a retirada. En PASS, solo IDs/redes del run se retiran, volúmenes snapshot/TLS quedan.

## Causa y cambio mínimo

R43 llegó al replay: Edge devolvió 409 `INVITE_EARLY_RECONCILIATION_REQUIRED`. El probe no alcanzó la tabla: su GET a `http://h3req1-c03-postgrest:3000/rest/v1/admin_invitations` recibió 404 `PGRST125`. PostgREST 13 documenta PGRST125 como ruta inválida: [PostgREST 13 — Errors](https://docs.postgrest.org/en/v13/references/errors.html#postgrest-error-codes). El contenedor habla directamente PostgREST en el puerto 3000, no el gateway Supabase que añade `/rest/v1`; el path correcto para esta llamada directa es `/admin_invitations`.

Se cambió una sola ruta del harness de `/rest/v1/admin_invitations` a `/admin_invitations`. El probe mantiene GET, destino fijo, request ID sintético, proyección allowlisted, máximo dos filas, timeout 5 s, respuesta acotada a 8 KiB y salida de clases/booleanos. No registra correo, UUID, metadata cruda ni errores sin clasificar. El replay sigue esperando 200; no se rebajaron asserts ni se añadieron retries.

## Ciclo test-first y revisión

1. Contrato R44 esperaba el path del endpoint PostgREST directo; antes de cambiar runtime falló ese único subtest, con 33/34 PASS. La salida identificó solo el path discrepante.
2. Después del cambio, contratos R43 y R44 pasan **68/68** en `studiamatch-dev`.
3. `node --check` del runtime/helper, `bash -n` del runner R44, ShellCheck 0.11.0 en contenedor local `network=none`/read-only y `git diff --check`: PASS.
4. Revisión del diff: solo ruta de diagnóstico y contratos, runner versionado con nombres/log/recurso R44; no hay cambios funcionales de producto, cambios de permisos, exposición de datos o ampliación de respuesta. El helper mantiene sanitización y límites.

## Candidato e inputs

- Rama/HEAD: `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- Manifiesto R43 histórico preservado: 120 filas, SHA-256 `acc4b2b733998bd6f5e5be1010c7e7c9e8cc72d26f598d5bcc5c93f21443b096`.
- Manifiesto R44 activo: 122 entradas, SHA-256 `e25f62b86bd99d2e20cc07e3da09f172d7b3e3dee8f9ba740135b0f3356790c6`; `sha256sum -c` 122/122 PASS. Incluye el source allowlisted histórico más runner/contrato R44. El manifiesto no se incluye a sí mismo.
- Runner R44 SHA-256: `63ee41945b3c4083da4b94a87fb055fb6982a0a282d9249f3d179b099b8540c7`.
- Runtime SHA-256: `7c672ab9634f6caa9b9edfb37024a677a13ff8b8c26a60b4664e1807cd1402b8`.
- Helper de clasificación SHA-256: `2bf5d1be10c92356978b9f07ff4b8e6057c2157f7916de92b7cc69f656aabead`.
- Contrato R44 SHA-256: `49fd4ecaa534189e4ee8acf61f01e9a39af50bf35dfc22d31e1620eeffc86f3d`.
- Caches locales R4 verificados: digests deno-cache, edge-node-modules, miniflare-node-modules y pages-node-modules coinciden con lo archivado.
- WIP antes de preparar esta nota: 658 entradas (55 tracked modificados, 603 untracked); preservar todos.

## Resultado R44 y siguiente diagnóstico

R44 se ejecutó una vez con el comando fijado arriba; timeout 2400 s, exit `1` en
`edge-first-pages-last-recovery-smoke`. Log sanitizado SHA-256
`fe609c318eb06fc28502a581896282315f481a0964d2a79414976e7fc7d95a7f`; manifiesto archivado
sin cambios. Snapshot/caches, PG17.11, bootstrap, PostgREST readiness, Pages/workerd AAL2,
reserva, suspensión, denegaciones, finalizador único, safe-resume y assertions SQL pasaron.
Replay Edge 409 `INVITE_EARLY_RECONCILIATION_REQUIRED`; probe HTTP 200 y `rowCountClass=ZERO`
filtrando por metadata request ID.

La assertion SQL anterior comprobó la fila por actor, correo y request ID; por tanto el probe
HTTP ya no tiene un error de ruta, pero su resultado vacío no distingue el filtro JSON de la
visibilidad. No se toca el producto. R44 e inventario/retirada exacta documentados en
[resultado R44](h3req1_c03_r44_result_inventory_2026-10-10.md); se retiraron siete contenedores
y dos redes por ID/etiquetas después de preservar evidencia; snapshot/TLS y caches quedan.

R45 cambiará solo el filtro diagnóstico a la dirección sintética fija `email=eq.TARGET_EMAIL`
con el límite de dos filas. Mantiene request ID como campo comparado y no registrado. Esto
separa filtro JSON de falta de visibilidad y permite ver las clases de estado de la única fila.
El replay conserva HTTP 200 requerido y cero retries. R45 usará log/recursos nuevos, el mismo
contrato funcional, imágenes y límites.

El comando usado en R44 fue:

```bash
/usr/bin/timeout --foreground --signal=TERM --kill-after=3s 2400s \
  /bin/bash tests/h3req1_c03_integrated_drill_r44.sh \
  --jit H3-CLOSE-03-INTEGRATED-2026-10-10-R44 \
  --manifest-sha256 e25f62b86bd99d2e20cc07e3da09f172d7b3e3dee8f9ba740135b0f3356790c6
```

Usa las imágenes locales fijadas de PG17.11, PostgREST 13, Node y Edge Runtime; no hace pull/build ni descarga dependencias. Runtimes en redes Docker internas, recursos por servicio limitados, datos sintéticos locales y credenciales de fixture no operativas. PGDATA es tmpfs. No lee `.env*`, no toca checkout original ni servicios remotos. Timeout 2400 s, stop-on-failure, cero retries. Ante cualquier error, G07 sigue parcial; preservar el log y clasificar el primer predicado antes de otro cambio.

## Criterio de G07

R45 debe orientar el diagnóstico y las siguientes etapas deben acreditar estado persistido matching, replay HTTP 200 de la misma invitación, cero correo/Auth adicional, login AAL2, rol admin y smoke final, además de las assertions de suspensión/recovery ya integradas. Un resultado del probe sin `rowCountClass=ONE` o con mismatch orienta el diagnóstico; no cierra el gate. La métrica se mantiene en histórico 60% y local 6/9 hasta completar todos los criterios.
