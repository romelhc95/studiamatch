# G07 C03 integrado R40 — clasificar replay Edge tras reanudación

## Cambio focal y preservación

R39 pasó el snapshot, PG17 17.11, bootstrap H2→H3, PostgREST, login Pages/workerd
AAL2, reserva, suspensión, dispatcher rechazado con HTTP 403/SQLSTATE 42501,
finalización Auth exactamente una vez durante la suspensión, safe-resume y sus
assertions SQL. Falló únicamente el status del replay Edge posterior; R39 no
capturó status ni código Edge, así que no se atribuye causa al producto.

El cambio de R40 no altera Edge/SQL ni relaja el predicado 200. Clasifica el status
HTTP dentro de 100–599 y usa únicamente `classifyInviteEarlyResult`, que mapea
códigos Edge cerrados y cae al status numérico para valores desconocidos. Status
inválido se reporta como `INVALID`/`INVITE_EARLY_HTTP_INVALID`. No se serializan
cuerpo, mensaje, headers, tokens, PII ni código desconocido. Las otras aserciones de
recovery quedan intactas.

Archivos fuente modificados: `tests/h3req1_c03_integrated_runtime.mjs` y
`tests/h3req1_c03_login_result.mjs`. Se clonó el runner R39 y su contrato como R40,
con IDs/nombres/log/JIT propios; no se reescribieron los R39 consumidos.

## Revisión y preflight R40

- Candidato: `feat/h3req1-sync-20261002`, HEAD baseline
  `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- Se archivó intacto el manifiesto R39, 111 entradas, SHA-256
  `703129159e15e1a3f0ea92e2594c9fa33420946944c06c2b9ec47200196b1763`.
  Solo difieren respecto de él los dos archivos de código fuente declarados arriba;
  R40 agrega su runner y contrato. Manifiesto R40: 113 entradas, SHA-256
  `7233b21cc615ff6427e043fdae11cd97b61ebffe8c39a92f11f769c28fbb4799`.
- Contrato R40: 31/31 PASS en `studiamatch-dev`, incluyendo códigos sintéticos
  conocidos/desconocidos e input inválido; no se filtra el código crudo.
- Bash syntax: PASS. ShellCheck 0.11.0 fijado en imagen local, contenedor read-only
  y network none: PASS. El contenedor de desarrollo no incluye ShellCheck; no se
  instaló nada.
- `git diff --check`: PASS. `sha256sum -c` del manifiesto R40: 113/113 PASS.
- `studiamatch-dev`: healthy, imagen `studiamatch-h3req1:20261009-v3`. Se preservan
  los inputs y caches R4/R5. No se leen `.env*` ni Env de Docker.

Iteraciones preflight: (1) una ejecución inicial del contrato obtuvo 30/31; el
caso de status inválido reveló precedencia ambigua entre un status no numérico y un
código conocido sintético. Se corrigió el helper para devolver
`INVALID`/`INVITE_EARLY_HTTP_INVALID`. (2) una aserción estática apuntaba a la
implementación antes de extraer el clasificador; se actualizó para comprobar el
call-site y la función pura por separado. Ambas correcciones quedaron cubiertas por
el 31/31 PASS final. (3) ShellCheck no está instalado en `studiamatch-dev`; se usó
la imagen local fijada en un contenedor efímero aislado, sin instalar paquetes.
Una primera reconciliación del manifiesto se detuvo por un error en el propio
guard que comparaba rutas; la lectura posterior mostró únicamente los dos deltas
fuente declarados. No se publicó ni usó el manifiesto fallido; el guard corregido
validó 111/111 inputs históricos con exactamente esos dos deltas y generó 113/113.

R39 se inventarió antes de retirarlo: siete contenedores detenidos y dos redes
internas vacías retirados por identidad exacta; volúmenes, imágenes y evidencia se
conservaron. Ver [inventario R39](h3req1_c03_r39_resource_inventory_2026-10-10.md).

## Ejecución R40

Una invocación con timeout 2400 s y stop-on-failure:

```bash
/usr/bin/timeout --foreground --signal=TERM --kill-after=3s 2400s \
  /bin/bash tests/h3req1_c03_integrated_drill_r40.sh \
  --jit H3-CLOSE-03-INTEGRATED-2026-10-10-R40 \
  --manifest-sha256 7233b21cc615ff6427e043fdae11cd97b61ebffe8c39a92f11f769c28fbb4799
```

El runner reutiliza versiones e imágenes fijadas de R39, el snapshot completo y los
caches verificados, pero crea snapshot/PG17 17.11/PostgREST/Pages/Edge/networks
aislados con nuevos nombres y nonce. PostgreSQL es tmpfs; credenciales son
sintéticas. No modifica `studiamatch-dev`, el checkout original, servicios
remotos, secretos ni infraestructura global. En FAIL para antes de la fase
dependiente y deja log sanitizado y recursos exactos etiquetados; en PASS ejecuta
cleanup propio de contenedores/redes, preservando imágenes, caches y volúmenes de
evidencia.

## Resultado ejecutado R40

R40 consumido una vez, exit 1, en `edge-first-pages-last-recovery-smoke` al
consultar `/control/recovery`. El predicado mantenido fue
`RECOVERY_EDGE_REPLAY_STATUS`; diagnóstico allowlisted: `status=409`,
`classification=INVITE_EARLY_HTTP_409`. No se expuso código Edge crudo. En el
handler actual, HTTP 409 corresponde a códigos de conflicto cerrados como
`duplicate_pending`, `duplicate_ready`, `resend_cooldown`, `membership_blocked`,
`onboarding_in_progress`, `role_mismatch` o `reconciliation_required`. La evidencia
disponible no identifica cuál, por lo que no hay aún una causa confirmada ni un
defecto de producto demostrado. La siguiente ejecución añade únicamente esas
clases conocidas a la allowlist diagnóstica y conserva la expectativa de status
200 para replay completo.

Antes del fallo pasaron los mismos gates previos que R39, incluidos suspensión,
403/42501 con nonce preservado, finalización Auth una vez, safe-resume y assertions
SQL recuperadas. Log sanitizado SHA-256
`76f9b2a975cff439d69893c71c7c3c85482ad378558edb8cb58e83d68a03871a`:
[R40](h3req1_c03_integrated_run_2026-10-10_r40.txt). Inventario y retirada
selectiva: [recursos R40](h3req1_c03_r40_resource_inventory_2026-10-10.md).
