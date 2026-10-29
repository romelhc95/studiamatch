# JIT S1 — reproducción mínima de arranque Pages/workerd — 2026-10-06

Estado: **APROBADO y consumido una sola vez el 2026-10-07; NO-GO en source snapshot.** No reintentar ni consultar/limpiar recursos con este JIT.

## Por qué hace falta

R4 llegó a `isolated-workerd-bootstrap`: verificó 62/62 inputs y los cuatro digests de dependencias; después no obtuvo `healthz` en 60 intentos. D1 no identificó la imagen porque su comparación literal falló. D2, ejecutado una sola vez bajo su JIT independiente, verificó el runtime R4 exacto como `exited`, `exit=1`, `OOMKilled=false`, `log-driver=none`. El contenedor no conserva logs y R4 redirigió stdout/stderr del proceso a `/dev/null`; la causa del arranque sigue sin determinarse. Evidencia D2 SHA-256 `a62865e09cf409a81047999e438f45aa0c1abdb1b4e4d4b2b9c8532679c9dda6`.

El control `healthz` se vuelve listo solo después de que Miniflare/workerd cree los workers Pages activo, suspendido y quota. El smoke usa el mismo `runServer`/bootstrap hasta abrir los listeners TLS/HTTP/control, con un modo `--startup-smoke` dedicado: dependencias instaladas desde lockfiles nuevos, validación acotada de raíces, TLS sintético y la misma creación real de workers. `Auth mock=false`; los listeners gateway S1 responden solo 404 y cuentan llamadas, y `finish` exige cero solicitudes. No se lee el fixture SQL, no se ejecutan solicitudes Pages/Auth/PostgREST/Functions, no se inicia Edge Runtime y no hay base de datos. No prueba integración SQL ni reemplaza C03.

## Operación exacta aprobada y ejecutada

- JIT: `H3-CLOSE-03-WORKERD-STARTUP-SMOKE-2026-10-06-S1`.
- Manifiesto JIT de 13 inputs: `tests/h3req1-c03-startup-smoke-s1.sha256`, SHA-256 `67fdea215c289cec028dae46172ba431814c598211561c17e6846d24e1c9ca7f`.
- Runner `tests/h3req1_c03_startup_smoke_s1.sh`, SHA-256 `c5fd272fdd18ef5a84d19bd1de229c421eb7dcccef7c2f1817460bcd9cc1a0d0`.
- Supervisor `tests/h3req1_c03_startup_smoke_s1.mjs`, SHA-256 `6a5e14271ad4795ccbfff8e2e7049a702cca9c9bcdc060b24df5798a2a8e3fcd`.
- Runtime candidato actualizado, SHA-256 `637990b49e585d9772b62e8f5eeac0aa3708f082d9106228d62caf3859776e3a`.
- Manifiesto mínimo del source snapshot: `tests/h3req1-c03-startup-source-s1.sha256`, 13 inputs y SHA-256 `ae335c8e197d2c380bc877abbd53aa9f52a30f2b00e3310865bccb64ecb17c5d`. Incluye runtime, supervisor, Page middleware/BFF/quota, worker quota, paquetes y lockfiles requeridos; excluye archivos SQL, `.env*`, fixtures Auth separados y datos operativos. El runtime contiene literales/helpers sintéticos de test, pero el modo S1 no lee el fixture SQL, fija Auth mock=false y no invoca Auth. El histórico R4 conserva por separado su manifiesto original, sin editarlo.
- Gates estáticos locales pre-JIT: `bash -n` PASS; `node --check` del filtro, supervisor y runtime PASS; `git diff --check` PASS; source S1 **13/13 PASS**; manifiesto JIT **13/13 PASS**. Auditoría independiente estática final 2026-10-07: **0 hallazgos**. `shellcheck` no está instalado y no se marca PASS.
- La ejecución JIT aprobada no llegó a `npm ci`, Miniflare ni workerd; resultado y límites detallados abajo.
- Comando exacto ejecutado una sola vez:

```bash
bash tests/h3req1_c03_startup_smoke_s1.sh \
  --jit H3-CLOSE-03-WORKERD-STARTUP-SMOKE-2026-10-06-S1 \
  --runner-sha256 c5fd272fdd18ef5a84d19bd1de229c421eb7dcccef7c2f1817460bcd9cc1a0d0 \
  --manifest-sha256 67fdea215c289cec028dae46172ba431814c598211561c17e6846d24e1c9ca7f
```

## Resultado de ejecución S1 — 2026-10-07

**NO-GO.** El runner terminó en `phase=create-new-source-snapshot`, con exit `2`, antes de ambos bootstraps npm y del runtime Pages/workerd. No se obtuvo un smoke ni diagnóstico de la causa más específico: la salida Docker del snapshot se suprimió. Evidencia sanitaria `.context/evidencia/h3req1_c03_startup_smoke_2026-10-07_s1.md`, SHA-256 `46b5d62efc1a557ed4a6833ffaf62b2ae290ae15c4761b33601702524876436b`.

La evidencia reporta holder `h3req1-c03-startup-volume-holder-20261006-s1` running en `network=none` y `bounded-stop=completed` para el contenedor snapshot por ownership verificado. El runner ya había creado los volúmenes source/tools/pages antes del snapshot; no se realizó inspección posterior ni cleanup. La red runtime y los bootstraps npm no se alcanzaron por el orden del runner. Recursos y holder quedan preservados. Este JIT queda consumido; cualquier diagnóstico adicional, cambio del runner, retry o cleanup requiere alcance/JIT separado.

El runner enlaza el SHA aprobado con su entrada en el manifiesto, verifica rama `feat/h3req1-sync-20261002`, HEAD baseline `4eb4d877a50b012bb630a129bd0c74482c33be9c`, evidencia D2/R4 y source S1 antes de Docker. Rechaza symlinks/paths inseguros y colisiones. El contenedor snapshot vuelve a verificar el SHA fijado del source manifest y todos sus inputs después del tar, antes de los bootstraps npm, cerrando drift concurrente del snapshot. Comprueba Docker local por socket Unix (rechaza overrides `DOCKER_*`) y neutraliza variables proxy estándar. Para detener, exige ID de 64 hex y labels JIT/manifiesto/nonce coincidentes antes de enviar `docker stop` por ID; cualquier desacuerdo falla cerrado. Usa la imagen local fijada `node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844` (`--pull=never`). No reutiliza ni consulta caches, volúmenes, contenedores o redes R1–R4.

### Recursos nuevos autorizables

Contenedores: `h3req1-c03-startup-snapshot-20261006-s1`, `h3req1-c03-startup-tools-20261006-s1`, `h3req1-c03-startup-pages-20261006-s1`, `h3req1-c03-startup-runtime-20261006-s1` y holder offline `h3req1-c03-startup-volume-holder-20261006-s1`.

Volúmenes Docker locales nuevos, driver tmpfs y opciones verificadas: `h3req1-c03-startup-source-20261006-s1` (96 MiB), `h3req1-c03-startup-tools-20261006-s1` (768 MiB), `h3req1-c03-startup-pages-20261006-s1` (1024 MiB), máximo conjunto 1888 MiB. El holder, sin red y read-only, conserva los mounts/datos tras los bootstraps; permanecerá ejecutándose al terminar. Durante un bootstrap, la máxima capacidad tmpfs simultáneamente montada es 1888 MiB de volúmenes + 512 MiB de `/tmp` del bootstrap + 8 MiB de `/tmp` del holder = 2408 MiB (~2.35 GiB); los bootstraps son secuenciales. Snapshot (32 MiB) y runtime (hasta 280 MiB) ocurren en otras fases y tienen máximos simultáneos menores. Estas son cuotas de capacidad configurada, no estimaciones de uso real. El holder y sus volúmenes se preservan; no se paran ni eliminan, y su liberación requiere JIT de cleanup independiente. Si el daemon no soporta tmpfs o los límites exactos, se detiene sin fallback. Red única `h3req1-c03-startup-net-20261006-s1`, creada y verificada como bridge `Internal=true`; sin puertos publicados. Recursos con colisión causan parada. Todos llevan labels de JIT/manifiesto/nonce.

Los únicos pasos con egress son dos bootstraps nuevos desde lockfiles fijados: `npm ci` de Miniflare 4.20260730.0/esbuild 0.25.10/TypeScript 5.9.3 (incluye lifecycle workerd) y `npm ci --omit=dev --ignore-scripts` de dependencies Pages. Ambos fijan `--fetch-retries=0`; no se reintenta la descarga internamente ni se vuelve a ejecutar un bootstrap fallido. Usan Docker `bridge` sin allowlist FQDN (riesgo residual de egress general), variables proxy estándar vacías y sin `.env*`/credenciales de operador. El source snapshot solo contiene los 13 inputs S1 fijados; no incluye SQL, secretos externos ni datos. Cada bootstrap tiene 10 min, 2 CPU, 2 GiB RAM/swap, 256 procesos, `--cap-drop=ALL`, `no-new-privileges`, `/tmp` tmpfs 512 MiB y volumen tmpfs con cuota indicada; si falla, se detiene solo el container nuevo.

El runtime está en red interna sin egress; usa source/dependencies read-only, genera TLS sintético en tmpfs y abre solo listeners internos no publicados. No ejecuta digest recursivo en S1: los bootstraps lockfile `npm ci` deben terminar exit 0 y el runtime verifica roots `node_modules` reales; el C03 integrado mantiene su gate de digest completo. Healthz máximo 60 intentos/60 s; cierre gracioso 10 s; límite externo 180 s; 2 CPU, 2 GiB RAM/swap, 256 procesos, `--cap-drop=ALL`, `no-new-privileges`. La salida npm se lee en fragmentos de hasta 4 KiB, la clasificación se detiene después de 16 MiB de salida y el resto solo se drena. El supervisor runtime procesa streams incrementalmente y conserva como máximo 4 KiB por línea antes de clasificarla; no se conserva texto crudo. Emite clases/códigos allowlisted (máximo 200 líneas de 1 KiB); `log-driver none`. Al timeout envía SIGTERM y, tras 10 s, SIGKILL solo al child nuevo; el wrapper puede detener solo el container S1 nuevo. Snapshot/bootstraps/runtime quedan exit; holder queda running sin red. Todos los containers/volúmenes/red se preservan; no hay `rm`, cleanup ni resume.

### Aprobación incluye únicamente

1. Verificaciones Docker de contexto local, colisión, digest de imagen local y creación de snapshot, tres volúmenes tmpfs con cuotas exactas, holder y red nueva.
2. Los dos bootstraps npm nuevos con egress general Docker bridge y lifecycle workerd descritos arriba.
3. Un solo arranque del bootstrap real Pages/workerd, healthz, cero requests a gateway y shutdown gracioso; evidencia sanitaria en `.context/evidencia/h3req1_c03_startup_smoke_2026-10-07_s1.md`.
4. Límites y terminación de procesos/containers nuevos por timeout exactamente descritos; preservación de todos los recursos.

No incluye Postgres/PostgREST real, Edge Runtime, SQL/DDL/DML/grants ni lectura de fixture SQL; Auth real/mock o solicitudes Auth, correo, `.env*` o secretos del operador; llamadas remotas, Cloudflare, Supabase, datos operativos, recursos R1–R4, retries, stop del holder, cleanup, rollback/resume, cambios de código posteriores a este manifiesto, commit/push/PR/merge/deploy/workflow_dispatch/protecciones.

## Decisión del resultado

- Solo `smoke=PASS workerd-pages-healthz=true` con runtime exit 0, gateway request count cero y holder validado acredita este smoke; no cierra H3-CLOSE-03.
- Un fallo produce un NO-GO con fase, categoría/mensaje filtrado y exit/OOM del recurso nuevo. Se preserva todo y se detiene el ciclo; no hay retry implícito. La causa deberá revisarse y corregirse localmente antes de solicitar el JIT separado que cubra un smoke actualizado.
- Un smoke PASS precede, pero no autoriza, un C03 integrado nuevo. C03 requerirá runner/manifiesto y JIT propios, nuevas dependencias/recursos y la secuencia/efectos ya definidos en el plan único.

## Compatibilidad y transición

Tooling diagnóstico local solamente; no cambia el contrato o runtime del producto. `expand`: runner/supervisor y artefactos diagnósticos nuevos. `compatibilidad`: ningún cambio a producto ni a los recursos preservados. `deploy`: no aplica ni se autoriza. `contract`: no aplica al producto; conservar evidencia diagnóstica. Rollback: detener el ciclo, preservar el snapshot/containers/volúmenes/log; no borrar ni reanudar recursos.
