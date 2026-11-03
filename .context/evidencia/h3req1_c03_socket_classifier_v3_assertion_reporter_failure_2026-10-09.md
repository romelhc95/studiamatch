# H3REQ1 — endpoint acreditado; clasificador sintético ambiguo corregido

Fecha: 2026-10-09. Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Tareas y gates

| Tarea | Resultado verificable | Gate |
|---|---|---|
| Ejecutar una vez JIT V3 escalado aprobado | Socket path/create/connect, lectura HTTP e identidad Linux `OK`; sintéticos fallaron; exit 1 | F1 y r9 no alcanzados; G03/G04 abiertos |
| Aislar la discrepancia del clasificador | El runner usaba búsqueda de subcadena en el traceback completo; el código emitido no identifica necesariamente el assert fallido | Corregido en V4 por nombre de caso allowlisted |
| Mantener aceptación funcional de los cuatro ajustes | Matriz abajo; no se reejecutaron suites funcionales | G08/G09 abiertos |
| Preparar CI independiente | Patch Protected Workflow Integrity V3 permanece aislado y sin instalación | G10 abierto |

## Preservación y candidato

| Checkout | Rama / HEAD | Modificados | Untracked | Staged |
|---|---|---:|---:|---:|
| Candidato | `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c` | 54 | 190 | 0 |
| Original `/home/romel/src/studiamatch` | `feat/h3req1-development-remote-tests` / `7650093b05a820e8e6faf9ec711e12fab8b50398` | 39 | 39 | 0 |

Los conteos usan `git status --porcelain --untracked-files=normal`. No se usaron reset, checkout,
clean, stage, secrets, `.env*` ni modificaciones al checkout original. `git apply --check` del
patch CI sobre el WIP compartido no aplica porque sus cuatro rutas se solapan con cambios
locales ya existentes; no se aplicó. El patch sí tiene evidencia preservable de aplicación y
`git diff --check` en una copia aislada limpia del baseline, descrita en el paquete CI.

## Resultado exacto del JIT V3 consumido

El usuario aprobó una invocación de
`H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-SOCKET-CLASSIFIER-V3-ESCALATED-AND-R9-ONCE-20261009-V1`,
JIT SHA-256 `aac075df511b0982b12e5414db75dcfb792c46d022a6bdf8ba0c3b6c8afad994`. Se ejecutó una
vez como usuario no-root en Ubuntu WSL, con acceso elevado del entorno, sin `sudo`.

```text
phase=desktop-wsl-socket-path|error_code=OK
phase=desktop-wsl-socket-create|error_code=OK
phase=desktop-wsl-socket-connect|error_code=OK
phase=desktop-wsl-engine-response-read|error_code=OK
phase=desktop-wsl-engine-identity|error_code=OK
phase=desktop-wsl-endpoint-attested|error_code=OK
phase=classifier-synthetic-image-read|error_code=OK
phase=classifier-synthetic-tests|error_code=V2_MAIN_EXIT_ASSERT_FAILED
exit=1
```

La identidad del endpoint Docker Desktop WSL quedó acreditada por respuesta HTTP/Engine Linux.
También se leyó el digest allowlisted de la imagen sintética. El contenedor sintético reportó
`V2_MAIN_EXIT_ASSERT_FAILED`; stop-on-failure detuvo la ejecución antes de F1 y r9. No se
reintentó ni se consultó/reconstruyó/reinició `studiamatch-dev`; no hubo pull, instalación ni
cambio de Docker. El resultado no cierra G03/G04.

## Predicado discrepante y corrección mínima

La prueba sintética agrupa retorno, salida exacta y ausencia de un marcador privado en un solo
test. El reporter V3 inspeccionaba `report.longreprtext` completo y escogía el primer marker
encontrado por subcadena. La línea de contexto de otra aserción puede aparecer en esa
representación; por eso el código recibido no basta para atribuir la falla al retorno
`main() != 1`. No se conserva ni expone el traceback crudo y no se afirma que el clasificador
funcional F1 esté mal.

La corrección acotada del harness separa el caso en tres tests allowlisted: retorno no-cero,
secuencia de fases/códigos y ausencia del sentinel privado. El runner nuevo clasifica fallos
solo por el nombre de test fijado, nunca por traceback o salida; un test desconocido falla
cerrado. Esto ofrece una siguiente observación inequívoca sin registrar valores de retorno,
líneas de código, metadata ni texto privado. El candidato funcional no se modificó.

La API de pytest documenta `longreprtext` como representación textual completa de `longrepr`,
lo que respalda no usarla para encontrar tokens de aserción por subcadena: [pytest API Reference](https://docs.pytest.org/en/latest/reference/reference.html).

## Matriz de aceptación: cuatro ajustes

| Ajuste / inputs | Evidencia previa preservable | Cobertura afectada | Resultado de este corte | Siguiente acción |
|---|---|---|---|---|
| Edición Admin con procedencia: campos permitidos, valor de pipeline y override, recarga, dos saves concurrentes y conflicto | `h3_course_editorial_local_cycle_2026-10-01.md`; histórica, no se invalida | `tests/sql/h3_pg17_harness.sql`, `tests/h3_local_uat.mjs`; el UAT conserva el override anterior y espera RPC con `Promise.allSettled` antes del cleanup | Implementación existente; ningún defecto funcional demostrado; asserts de WIP no ejecutados | Renovar solo con fixture PG17 desechable después de tooling/startup; no reescribir la implementación |
| Auditoría actor/fecha/antes/después: identidad real, timestamp, old/new, coherencia del evento y edición autorizada | Evidencia SQL/editorial histórica y C03 SQL 41/41 del candidato previo, preservadas separadamente | Harness PG17 + casos de auditoría del UAT | Assertions presentes; sin runtime del WIP actual ni defecto demostrado | Validar atomicidad y rechazo de edición/borrado por rol no autorizado, sin repetir suites intactas |
| Disponibilidad: evidencia ausente/inválida, día 90 inclusivo, >90, calidad y coexistencia legacy | C03 SQL 41/41 del input previo, solo preservable para sus hashes | `tests/sql/h3_pg17_harness.sql` y publicación UAT | Límite cubierto en harness anterior; no revalidado para WIP actual | Renovar solo inputs delta sobre PG17 limpio; no fabricar datos operativos para PASS |
| Email autenticado en encabezado: Admin/User, fallback, MFA/rol/sesión, viewport móvil/escritorio | Ciclo de header de 11 checks y UAT histórico 144/144, separados del WIP actual | `tests/h3_local_uat.mjs` (48 casos × 3 viewports), regresiones MFA/roles/invitación/publicación | Cobertura preparada; no ejecutada para este WIP | Revalidar 144 sin retries tras tooling; onboarding separado 10/10; conservar cuenta/MFA existente |

La decisión BFF sigue vigente. Se preservan BFF/HttpOnly, roles, MFA, gateway y cuotas. El
hallazgo sessionStorage/localStorage permanece histórico: no se declara XSS ni HIGH actual a
partir de ese informe, y no se vuelve a tokens de sesión accesibles desde JavaScript. Los
parciales anteriores se conservan como tales, sin sumar a la aceptación actual.

## CI y gatekeeping

Protected Workflow Integrity V3 permanece como patch aislado SHA-256
`4f5c7a946886d1df9cb866bdc057276db9eb5aa47e997be403b092ba6f704d1b`; su aplicación y
`git diff --check` en copia limpia del baseline son parciales preservables. No se aplicó al
WIP, no se ejecutaron `actionlint`/pytest en Docker y no hay run, required status ni enforcement
remoto. GitHub exige actualmente `security-audit`; no se repiten las capturas administrativas.
Production Pages `main`, watch `*` y el riesgo de rollout siguen en el paquete CI. No se abre
PR, no se publica y no se cambian Settings.

## Próxima ejecución acotada

Se prepara un nuevo JIT V4 de una sola invocación. Reusa la atestación endpoint/identidad
capturada arriba —no repite socket/HTTP—, prueba el reporter por nombres de casos en un
contenedor sintético offline, y solo si pasa lee F1 una vez y ejecuta r9 una vez. Cualquier
FAIL/timeout detiene el resto; no se cambia Docker ni el producto. La autorización V3 quedó
consumida, por lo que el nuevo bloque requerirá aprobación específica. Los JIT no autorizan
por sí mismos publicación, PR, merge, configuración remota ni despliegue.

## Gates y parciales

| Gate | Estado | Evidencia / pendiente |
|---|---:|---|
| G01 | 10/10 | SQL/wire anterior preservado para sus inputs |
| G02 | 10/10 | C03 SQL anterior 41/41; integración real pendiente |
| G03 | 0/10 | r9 no alcanzado; sintético V3 falló antes |
| G04 | 0/10 | Endpoint acreditado; lectura de F1 y controles íntegros aún pendientes |
| G05 | 0/10 | Copia completa aislada pendiente |
| G06 | 0/10 | Pages/workerd healthz pendiente |
| G07 | 0/10 | Edge/PG17/PostgREST integrado y C03 real pendiente |
| G08 | 0/10 | BFF actual 60 checks/10 cuotas histórico; deltas pendientes |
| G09 | 0/10 | UAT vigente 144, onboarding separado 10/10 y revisión independiente pendientes |
| G10 | 0/10 | Bootstrap CI aislado; checks/runtime y enforcement pendientes |
| **Total** | **20%** | G01/G02 completos; delta 0. Documentación y lectura de identidad no suman puntos. |

D01–D14 continúan 0/14. No hay `GO_LOCAL_PR` ni `GO_DEVELOPMENT_REAL`. No se declara GO.
