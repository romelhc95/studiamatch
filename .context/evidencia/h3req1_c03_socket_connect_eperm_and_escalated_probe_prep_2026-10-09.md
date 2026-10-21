# H3REQ1 — socket connect EPERM; prueba acotada fuera del sandbox preparada

Fecha: 2026-10-09. Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`. Se conserva el
WIP y no se modifica el checkout original.

## Tareas y gates

| Tarea | Resultado | Gate |
|---|---|---|
| Ejecutar el JIT V2 aprobado una vez | Sintéticos previos `OK`; path y socket-create `OK`; connect `EPERM`; exit 1 | Socket real no conectado; G03/G04 abiertos |
| Clasificar el `EPERM` | Resultado prueba syscall denegado en este contexto; no prueba si lo impuso sandbox Codex o host/WSL | Requiere ejecución diferenciada |
| Reutilizar pruebas intactas | Se conserva el PASS de los sintéticos in-memory del probe porque su SHA no cambió | No se repiten |
| Preparar siguiente verificación | JIT V3 intenta una sola conexión bajo sandbox escalado; identidad, sintéticos Docker, F1 y r9 son condicionales | Nueva aprobación exacta pendiente |
| Continuar CI independiente | Patch aplicable en copia aislada; sin runtime ni publicación | G10 sigue abierto |

## Resultado V2 consumido

El usuario aprobó una invocación de
`H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-SOCKET-CLASSIFIER-V2-AND-R9-ONCE-20261009-V1`, JIT
SHA-256 `edecb9534187fc522cd7b97851fe1cfaa6ab0473e7d975585aeff3f12074476a`. Runner
`999d1e93b9c73b6832803225b702c13ed9bf3d686c58da4583bdbd07265fda7e`. Se ejecutó como
`romel`, Ubuntu WSL2, TTY, uid 1000, sin sudo.

```text
phase=socket-probe-synthetic-tests|error_code=OK
phase=desktop-wsl-socket-path|error_code=OK
phase=desktop-wsl-socket-create|error_code=OK
phase=desktop-wsl-socket-connect|error_code=EPERM
exit=1
```

El shell cerró su pausa final con Enter. El runner se detuvo antes de HTTP/decodificación,
sintéticos del contenedor, lectura F1 o r9. No consultó `studiamatch-dev` ni hizo pull/build,
instalación o cambios Docker. No hubo retry.

## Análisis y paquete correctivo

El predicado demostrado es el `connect()` a `/var/run/docker.sock` devolviendo `EPERM`. La fase
de path confirmó socket local; la creación AF_UNIX pasó. El syscall de conexión no se completó.
La ejecución usó el sandbox normal `workspace-write`; que este limite el syscall es una
hipótesis, no una causa acreditada. No se afirma que Docker Desktop esté mal ni se cambia el
daemon.

Se preparó un wrapper V3 nuevo sin repetir los sintéticos in-memory ya aprobados y sin reusar el
helper V2 consumido. Revalida el SHA del probe idéntico, y en una sola conexión lee `/version`
solo si connect pasa. El runner combinado conserva los gates: identidad Linux exacta → pruebas
sintéticas Docker offline ya fijadas → F1 allowlisted una vez → r9 una vez. Todo fallo detiene
fases posteriores. La ejecución solicitada es `sandbox_permissions=require_escalated`, mantiene
uid no-root y no usa sudo; si el auto-review rechaza el acceso, el runner no se ejecuta.

Revisión estática: `bash -n` del runner combinado pasó; `git diff --check` pasó; los SHA de JIT,
wrapper, runner, probe y r9 se contrastaron. No se ejecutó Python ni Docker después del fallo.

El [JIT V3 escalado con F1/r9 condicional](../operaciones/jit_h3req1_docker_desktop_wsl_f1_socket_classifier_v3_escalated_and_r9_once_2026-10-09.md),
ID `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-SOCKET-CLASSIFIER-V3-ESCALATED-AND-R9-ONCE-20261009-V1`,
SHA-256 `aac075df511b0982b12e5414db75dcfb792c46d022a6bdf8ba0c3b6c8afad994`, espera
autorización de una sola ejecución.

## Gates, parciales y dependencias

- G01=10/10, G02=10/10; G03–G10=0/10; total **20%**, delta 0; D01–D14=0/14. No hay GO.
- Parciales históricos separados: SQL C03 41/41; pytest focal r4 20/20; scanner r7 PASS;
  UAT BFF r2 60 checks/10 cuotas; UAT anterior 144/144; onboarding anterior 10/10; C02 70/72.
- La matriz de aceptación de edición con procedencia, auditoría, disponibilidad ≤90 días y email
  autenticado está en [el corte de aceptación](h3req1_c03_engine_unavailable_and_socket_classifier_prep_2026-10-09.md);
  no hay validación nueva de esos criterios.
- Bootstrap CI Protected Workflow Integrity V3 sigue aislado y sin publicar. Persisten los
  gates de actionlint/pytest en Docker, check remoto real, estado requerido, efecto Pages y
  merge queue. No se vuelven a pedir las capturas administrativas recibidas.
- BFF/HttpOnly, MFA, roles, gateway, cuotas, cuenta existente, WIP y evidencia histórica se
  preservan. No se declara ataque ni HIGH actual a partir del informe sessionStorage histórico.
