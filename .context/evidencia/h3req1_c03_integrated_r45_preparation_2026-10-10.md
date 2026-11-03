# H3REQ1 G07 — preparación R45 con filtro diagnóstico por destinatario sintético

## Ficha de impacto

- **Componente:** diagnóstico read-only de la fila de invitación durante el recovery C03.
- **Consumidores:** runtime integrado y PostgREST local directo.
- **Contrato funcional:** replay Edge sigue requiriendo HTTP 200 para la misma invitación; cero llamadas Auth adicionales; no cambia producto, Edge, Pages/BFF, SQL ni reglas de recuperación.
- **Pruebas preservadas:** C03 SQL/R42 y los resultados históricos R43/R44; sus manifiestos se archivaron antes de cambiar inputs.
- **Pruebas renovadas:** contratos R43/R44/R45 (102/102), manifiesto R45 y drill integrado completo con solo el filtro diagnóstico ampliado.
- **Recuperación:** servicios aislados en redes internas, credenciales sintéticas, PGDATA tmpfs; logs sanitizados. El runner para solo sus servicios al fallar. Inventario antes de retirar IDs/redes exactos; volúmenes de snapshot/TLS y caches se preservan.

## Evidencia y cambio

R43 probó que `/rest/v1/admin_invitations` era ruta inválida en el PostgREST directo. R44 corrigió a `/admin_invitations`; el GET pasó a HTTP 200, pero el filtro `metadata->>request_id` no devolvió filas (`rowCountClass=ZERO`). Antes de ese probe, las assertions SQL confirmaron la reserva sintética por actor/correo/request ID. R44 no permite concluir si falla el filtro JSON, la visibilidad o un campo consultado; [resultado/inventario R44](h3req1_c03_r44_result_inventory_2026-10-10.md) preserva evidencia.

R45 cambia solamente el filtro de diagnóstico a `email=eq.c03-inflight@local.test`, destinatario fijo del fixture nuevo y aislado. Sigue leyendo máximo dos filas, con proyección acotada, timeout 5 s y límite 8 KiB. El helper compara `requestIdMatches`, actor, email, rol, status, user ID, reconciliación y entrega, y devuelve solo clases cerradas/booleanos. No registra valores crudos ni amplía el replay. No se cambia la consulta del producto ni se modifica una policy.

El contrato R45 se escribió antes del cambio y falló únicamente el subtest del filtro (33/34). Tras cambiar el path query, los contratos R43+R44+R45 pasan **102/102** en `studiamatch-dev`. `node --check`, `bash -n`, ShellCheck 0.11.0 local read-only/network-none y `git diff --check` PASS. Revisión del diff: una clave de query diagnóstica, sus contratos y runner R45 con nombres/log separados; ningún cambio a producto/SQL/roles/credenciales.

## Identidad y pins

- Candidato: rama `feat/h3req1-sync-20261002`, HEAD baseline `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- Manifiesto R44 histórico: 122 filas SHA-256 `e25f62b86bd99d2e20cc07e3da09f172d7b3e3dee8f9ba740135b0f3356790c6`, archivado antes del cambio posterior.
- Manifiesto R45: **124 inputs**, `sha256sum -c` 124/124 PASS, SHA-256 `791c36132ba4fd7e8acf9c0fff332a637a382333433f379ff428aa8f09f9a0b4`.
- Runner R45 SHA-256 `6fdf1c2fde7eadfea6b189d4bfd0fe559b5efdd827fd6fa528f02017b80ac4b9`.
- Runtime SHA-256 `4997bf97cac4e63ad1abd9debf6824a95d6e8be777b32e4e9fc533b660f4dee8`.
- Helper SHA-256 `2bf5d1be10c92356978b9f07ff4b8e6057c2157f7916de92b7cc69f656aabead`.
- Contrato R45 SHA-256 `2f806929997b02145083649fe74be7f1431a057b0c074320f340a114da91f39f`.

## Ejecución autorizada en el ciclo local vigente

```bash
/usr/bin/timeout --foreground --signal=TERM --kill-after=3s 2400s \
  /bin/bash tests/h3req1_c03_integrated_drill_r45.sh \
  --jit H3-CLOSE-03-INTEGRATED-2026-10-10-R45 \
  --manifest-sha256 791c36132ba4fd7e8acf9c0fff332a637a382333433f379ff428aa8f09f9a0b4
```

Usa imágenes locales fijadas de PG17.11, PostgREST 13, Node y Edge Runtime, sin pull/build/instalación/egress. Reutiliza caches R4 solo read-only con hashes verificados. Redes internas; PGDATA tmpfs. No lee `.env*`, no usa datos operativos ni toca el checkout original/remotos. Timeout 2400 s; stop-on-failure; cero retries. `studiamatch-dev` permanece healthy con `studiamatch-h3req1:20261009-v3`. Si el estado no es exactamente uno o hay mismatch, se conserva clasificación y se decide el cambio por predicado demostrado; no se rebaja el replay HTTP 200.

G07 permanece parcial hasta probar replay idempotente, sin segundo correo, sesión AAL2/rol y smoke final, además de la cobertura ya pasada. Métricas siguen histórico G01–G10 60% y cierre local G01–G09 6/9.

## Resultado del ciclo R45

El primer despacho terminó exit 77 antes de abrir Docker porque el hash pasado manualmente no cumplía el pin; no se creó log ni recurso. Luego el pin se extrajo mecánicamente de esta nota, se comparó con el manifiesto y R45 se ejecutó una vez.

R45 pasó snapshot/caches, PG17 17.11, bootstrap, PostgREST readiness, Pages/workerd AAL2, suspensión, rechazos, finalizador único, resume y assertions SQL. Falló exit 1 en `edge-first-pages-last-recovery-smoke`: Edge 409 `INVITE_EARLY_RECONCILIATION_REQUIRED`; probe PostgREST HTTP 200, `rowCountClass=ZERO`, filtrando por correo sintético. La assertion SQL anterior confirmó la fila finalizada por request ID, correo y actor. Véase [resultado e inventario R45](h3req1_c03_r45_result_inventory_2026-10-10.md), log SHA-256 `7cf304b4ac961b184d96e239870e3bd52b2fabfa530d28a69b879d2314bfcebc` y manifiesto archivado SHA-256 `791c36132ba4fd7e8acf9c0fff332a637a382333433f379ff428aa8f09f9a0b4`.

La cadena del harness crea `service_role NOLOGIN` sin `BYPASSRLS`; la migración habilita RLS en `admin_invitations`, revoca acceso público y concede SELECT a `service_role`, sin policy. Esto explica que PostgREST con JWT de `service_role` devuelva una colección vacía mientras `postgres` observa la fila. R46 corrige únicamente el atributo del rol sintético en el setup integrado aislado y lo aserta antes de iniciar PostgREST; no cambia producto, policies, migraciones funcionales ni configuración remota.

La retirada exacta R45 quitó siete contenedores detenidos y dos redes internas vacías tras preservar inventario/log; los dos volúmenes R45, caches R4, imágenes y `studiamatch-dev` permanecen. La revisión automática rechazó un comando que incluía `rm -f` de un temporal al regenerar el manifiesto; se detuvo antes de ejecutar y se regeneró con dos temporales retenidos en `/tmp`. El manifiesto fue 126/126 verificado. Dos preflights de retirada también se detuvieron sin mutación (pin tipeado y IDs abreviados); el tercero usó `--no-trunc` y eliminó solo los IDs inventariados.
