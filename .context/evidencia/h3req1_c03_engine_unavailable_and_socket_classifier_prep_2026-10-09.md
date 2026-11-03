# H3REQ1 — Docker Engine no respondió en el endpoint WSL; clasificador por subpasos preparado

Fecha: 2026-10-09. Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Tareas y gates de este corte

| Tarea | Resultado verificable | Gate |
|---|---|---|
| Ejecutar una vez el JIT V3 aprobado | `desktop-wsl-engine/DOCKER_ENGINE_UNAVAILABLE`, exit 1; detuvo F1 y r9 | G03/G04 siguen abiertos |
| Afinar diagnóstico sin repetir consultas Docker CLI | Socket path/create/connect/HTTP read/decode separados; pruebas sintéticas in-memory preparadas y revisión manual | Un nuevo JIT exacto queda pendiente |
| Revisar bootstrap CI en base limpia | Patch V3 aplicó en copia aislada de HEAD y `git diff --check` pasó | G10 sin runtime ni promoción |
| Mantener aceptación de producto | Cuatro criterios y regresiones no revalidados en este candidato | G08/G09 abiertos |

## Candidato y preservación

Rama y HEAD coinciden con el baseline esperado. Al cierre de esta nota hay 54 rutas tracked con
cambios, 186 untracked y cero staged. No se usó reset/checkout, no se aplicó el patch CI al
checkout compartido, no se leyó `.env*` ni se tocaron secretos. El checkout original
`/home/romel/src/studiamatch` conserva 39 tracked y 39 untracked con cero staged; no fue
modificado.

## Resultado de la invocación V3

El usuario aprobó una invocación de
`H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-CLASSIFIER-V3-ASSERTIONS-AND-R9-ONCE-20261009-V1`, JIT SHA-256
`1aa957146fbe98b6bec2e04c9d9cbc67414cbb4a9dbe3af138d53b592f8af178`. El JIT y su runner
combinado (`09755cd55d874bbae2b07afeaead9747abbb86f6d6126f3bee3ca71c9c9147c7`) se verificaron
antes de ejecutarlo. Se lanzó como usuario no root, con TTY, en el contexto WSL disponible; no
se elevó.

Salida sanitizada:

```text
phase=desktop-wsl-engine|error_code=DOCKER_ENGINE_UNAVAILABLE
exit=1
```

Por el orden y los códigos del runner, `docker context inspect` llegó a devolver el endpoint
allowlisted y el proceso Docker CLI para `docker version --format '{{.Server.Os}}'` terminó con
estado no cero. El helper descartó stderr, así que el resultado no distingue socket ausente,
conexión rechazada, permiso del socket u otra respuesta del Engine. No prueba que Docker
Desktop globalmente esté mal. No se alcanzaron digest sintético, los nueve casos sintéticos V3,
F1, ni r9. El JIT quedó consumido; no hay retry.

No se hizo pull, build, instalación, cleanup, cambio de Docker ni interacción con
`studiamatch-dev`. El runner del JIT no escribió resultados crudos. El exit de la invocación fue
1 y la pausa final se cerró con Enter.

## Corrección diagnóstica concreta y revisión

El clasificador del runner V3 transforma cualquier status no cero de `docker version` en el
mismo código. Esa pérdida de información está demostrada por el código ejecutado y la fase
recibida; no se demuestra un defecto del Engine ni del producto.

Se preparó un diagnóstico nuevo, sin repetir `docker context inspect` ni `docker version`:

- el helper compara el path fijo `/var/run/docker.sock`, sin imprimir metadata del filesystem;
- emite fases distintas para creación del socket y `connect()`, con códigos errno de una lista
  cerrada;
- hace una sola solicitud HTTP `GET /version`, con timeout de 5 s y cuerpo máximo de 8192
  bytes; solo acepta status 200, JSON decodificable y `Os=linux`;
- no imprime ni persiste respuesta, headers, endpoint dinámico, error crudo o datos de proceso;
- doce aserciones in-memory cubren errno, fases create/connect, HTTP, tamaño, JSON, identidad y
  OS antes de tocar el socket;
- solo tras identidad exacta, ejecuta los sintéticos V3 fijados en contenedor offline, lee F1
  una vez y ejecuta r9 una vez si los predicados previos pasan.

Revisión manual del flujo y límites estáticos: sin retries; sin `/proc`; sin pulls/rebuilds ni
`studiamatch-dev`; el fallo impide todas las etapas siguientes. La sintaxis Bash del runner
combinado pasó `bash -n`. No se ejecutó Python de desarrollo en host, no se conectó a Docker y
no se ejecutaron pruebas funcionales; la prueba sintética del clasificador y los casos V3 quedan
condicionados al próximo JIT. El residual de identidad se limita a respuesta Linux por el
socket WSL fijado; no verifica PID/UID/ejecutable del daemon.

El [JIT socket classifier V1 + F1/r9 condicional](../operaciones/jit_h3req1_docker_desktop_wsl_f1_socket_classifier_v1_and_r9_once_2026-10-09.md),
ID `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-SOCKET-CLASSIFIER-V1-AND-R9-ONCE-20261009-V1`, SHA-256
`da21f8c7853769f7f5cefe5155b45bcb3c192e228244a756d415205f4733cd2e`, agrupa la siguiente
invocación completa. Está preparado; aún no aprobado ni ejecutado.

## Bootstrap CI aislado

El patch Protected Workflow Integrity V3 conserva SHA-256
`4f5c7a946886d1df9cb866bdc057276db9eb5aa47e997be403b092ba6f704d1b`. `git apply --check`
contra el checkout WIP compartido falla porque tres rutas nuevas ya existen localmente y el
hunk del `security-audit.yml` no coincide con su WIP. No se aplicó nada a ese checkout. En una
copia temporal limpia de `4eb4d877a50b012bb630a129bd0c74482c33be9c`, `git apply --check`, la
aplicación en `/tmp` y `git diff --check` pasaron (`ci-patch-isolated-apply/OK`); la copia
temporal se eliminó. Esto prueba aplicabilidad al baseline, no lint/runtime ni instalación CI.

El patch sigue con cuatro rutas exactas, no aplicado ni publicado. Las reglas administrativas
ya compartidas no se vuelven a pedir. Production Pages `main` con include `*` y exclude vacío
sigue siendo una dependencia de rollout; no hubo promoción ni build. Policy event real,
emisión del check, asociación al SHA vigente, bloqueo efectivo, Settings, merge queue y
aislamiento Pages siguen pendientes. No solicitar aquí publicación, integración ni cambios de
Settings; requieren instrucción separada después de cerrar prerrequisitos locales.

## Matriz de aceptación de los cuatro ajustes

| Criterio | Inputs/casos | Evidencia previa preservable | Cobertura afectada | Resultado actual | Siguiente acción |
|---|---|---|---|---|---|
| Edición Admin con procedencia | Campos permitidos; valor de pipeline y override; guardado, recarga, dos saves con misma versión y conflicto | Ciclo editorial 2026-10-01 y checks anteriores se conservan como históricos | `tests/sql/h3_pg17_harness.sql`, `tests/h3_local_uat.mjs`; los asserts añadidos siguen sin ejecutar | Implementación existente; no hay defecto funcional demostrado ni PASS del WIP actual. La revisión estática mostró que el UAT podía limpiar un override previo y saltar cleanup si un fetch rechazaba | El UAT ahora restaura el override previo y espera ambos RPC con `Promise.allSettled` antes del cleanup. Validar en fixture PG17 desechable; runner aún no ejecutado |
| Auditoría actor/fecha/antes/después | Actor autenticado; timestamp; valores previos/nuevos; limpiar override; coherencia evento/modificación | Evidencia SQL/editorial histórica preservable, no se eleva a aceptación actual | Harness SQL y casos de auditoría del UAT | Assertions presentes en el WIP, sin ejecución actual | Validar integridad de evento y rechazo de edición/borrado por rol no autorizado |
| Disponibilidad con evidencia válida ≤90 días | Evidencia ausente/inválida; día 90 inclusivo; más de 90 días; calidad y legacy concurrentes | C03 SQL v3 41/41 inputs, solo para sus hashes/candidato anteriores | `tests/sql/h3_pg17_harness.sql`, publicación UAT | El límite está expresado en el harness; no revalidado en este WIP | Mantener SQL/wire sin cambios; renovar únicamente inputs delta en fixture limpia |
| Correo autenticado en header | Admin/User autenticados, fallback, sesión/MFA/rol, ancho móvil y escritorio | 11 checks de encabezado y UAT previo 144/144 se conservan como evidencia histórica; no se atribuyen al WIP | `tests/h3_local_uat.mjs` mantiene 48 casos × 3 viewports y cero retries; MFA/roles/invitación/publicación requieren regresión delta | Cobertura ampliada preparada, no ejecutada para este WIP | Revalidar UAT vigente 144 sin retries tras Docker/r9; no reinvitar ni resetear cuenta |

Históricos adicionales separados: 122 tests Python, TypeScript/lint/static smoke editorial; 11
tests de header; C03 SQL 41/41; C02 70/72 por deltas BFF/workflow; UAT BFF r2 60 checks/10
casos de cuota; UAT 144/144 y onboarding 10/10 de candidato anterior. No suman aceptación
actual. Se conserva BFF/HttpOnly, MFA, roles, gateway, cuotas y la compatibilidad vigente; el
informe de sessionStorage sigue histórico y no se declara HIGH actual.

## G01–G10 y parciales

| Gate | Estado | Evidencia/pendiente |
|---|---:|---|
| G01 | 10/10 | Gate SQL/wire previo; inputs sin delta demostrada conservados. |
| G02 | 10/10 | C03 SQL v3 previo 41/41; integración real todavía pendiente. |
| G03 | 0/10 | Parciales r4 20/20, scanner r7 PASS y otros focales conservados; r9 y revisión final pendientes. |
| G04 | 0/10 | V3 consumido con `DOCKER_ENGINE_UNAVAILABLE`; F1 no leído en esa invocación. |
| G05 | 0/10 | Copia íntegra aislada pendiente. |
| G06 | 0/10 | Pages/workerd healthz pendiente. |
| G07 | 0/10 | Edge/PG17/PostgREST integrado y C03 real pendiente. |
| G08 | 0/10 | BFF r2 60/10 parcial histórico; deltas actuales pendientes. |
| G09 | 0/10 | UAT actual 144, onboarding 10/10 separado y revisión independiente pendientes. |
| G10 | 0/10 | Patch aislado aplicable; checks/runtime, check remoto, required status y enforcement pendientes. |
| **Total** | **20%** | Solo G01/G02 completos; no suma por documentación, patch, revisión estática o hash. |

D01–D14 permanecen 0/14. No hay `GO_LOCAL_PR`, `GO_DEVELOPMENT_REAL` ni GO. El siguiente
resultado debe venir del JIT V1 aprobado antes de habilitar r9 y etapas posteriores.
