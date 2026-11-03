# H3REQ1 — fallo del clasificador socket V1 y corrección V2 preparada

Fecha: 2026-10-09. Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`. WIP actual:
54 rutas tracked modificadas, 188 untracked, 0 staged. El checkout original conserva 39
tracked, 39 untracked y 0 staged; no fue modificado.

## Ciclo ejecutado

| Paso | Evidencia | Estado |
|---|---|---|
| Analizar | El JIT V1 produjo `socket-probe-synthetic-tests/OK` y luego un error genérico del clasificador | PASS parcial; el socket real no se alcanzó |
| Corregir | El wrapper usaba `projection.EXPECTED_ENDPOINT`, atributo inexistente en `diagnostic_once.py`; el endpoint fijo sí existe en el módulo probe fijado | Defecto determinista localizado |
| Validar | `git diff --check` y `bash -n` del runner V2 pasaron; la V1 original conserva su SHA | Validación estática PASS; no se ejecutó Python ni Docker aparte del JIT consumido |
| Revisar | V2 obtiene el valor del probe allowlisted y conserva el endpoint `unix:///var/run/docker.sock`; no accede a metadata dinámica | Revisión estática PASS |
| Revalidar | Nuevo JIT agrupado incluye sintéticos, socket, F1 y r9 bajo condiciones exactas | Pendiente de autorización y ejecución única |

## Resultado del JIT V1 consumido

El usuario aprobó una invocación de
`H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-SOCKET-CLASSIFIER-V1-AND-R9-ONCE-20261009-V1`, SHA-256
`da21f8c7853769f7f5cefe5155b45bcb3c192e228244a756d415205f4733cd2e`. Runner combinado:
`546946238013267a1ce8f74ddda39f3c74336d3dbf2b1040ce185e751455c0a5`. Se ejecutó una sola vez
como `romel` en Ubuntu WSL interactiva, sin sudo.

```text
phase=socket-probe-synthetic-tests|error_code=OK
phase=f1-classification-v2|error_code=F1_CLASSIFICATION_FAILED
exit=1
```

El clasificador genérico es el único error sanitizado disponible. La revisión estática
demuestra el predicado que falló: el objeto `projection` cargado desde
`tests/h3req1_docker_peer_substep_diag/diagnostic_once.py` no define `EXPECTED_ENDPOINT`; el
wrapper intentó leer ese atributo después de imprimir el PASS sintético. El acceso lanza
`AttributeError`, que el helper V2 traduce a `F1_CLASSIFICATION_FAILED`. El módulo de socket
probe fijado sí define la ruta allowlisted.

La invocación se detuvo antes de `lstat`/socket/connect, respuesta HTTP, identidad del Engine,
lectura de la imagen o contenedor F1, sintéticos Docker y r9. No demuestra un fallo de Docker.
No hubo retry, Docker repair, pull/build, instalación ni interacción con `studiamatch-dev`.

## Corrección y paquete siguiente

Se conserva sin cambios la V1 consumida:

- `f1_read_failure_classification_socket_v1_once.py`: SHA-256
  `ae69a8f221026d518dfa96205baf09208eaa919f7f5065875dbcef49a8dee72a`.
- `run_wsl_f1_socket_classifier_v1_then_r9_once.sh`: SHA-256
  `546946238013267a1ce8f74ddda39f3c74336d3dbf2b1040ce185e751455c0a5`.

V2 se preparó en archivos nuevos; el cambio de código es usar `probe.EXPECTED_ENDPOINT`,
tomado del módulo probe con SHA-256
`fb8ee1b3afb4496e4c00d827cec57793c449957193fae7c4924485db758dcbbf`. El nuevo runner fija
el helper V2, mantiene el candidato/HEAD y revalida los pins del paquete r9. `bash -n` pasó;
`git diff --check` pasó. No se ejecutó Python en el host ni se probaron los cambios en Docker.

El [JIT socket classifier V2 + F1/r9 condicional](../operaciones/jit_h3req1_docker_desktop_wsl_f1_socket_classifier_v2_and_r9_once_2026-10-09.md),
ID `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-SOCKET-CLASSIFIER-V2-AND-R9-ONCE-20261009-V1`, SHA-256
`edecb9534187fc522cd7b97851fe1cfaa6ab0473e7d975585aeff3f12074476a`, está preparado y espera
aprobación específica de una sola invocación. Si pasa el diagnóstico de socket, contiene los
sintéticos V3, F1 y r9 en orden; todo error detiene el resto sin reintentos. No autoriza copia,
arranque Pages/workerd, C03 integrado, UAT final, publicación, PR, merge, Settings o despliegue.

## Frentes y gates

- Bootstrap CI Protected Workflow Integrity V3 conserva SHA `4f5c7a946886d1df9cb866bdc057276db9eb5aa47e997be403b092ba6f704d1b`. `git apply --check`, aplicación temporal desde HEAD y `git diff --check` pasaron; no se aplicó al checkout compartido, ni se instaló o publicó. Checks de runtime, status requerido y enforcement siguen pendientes.
- La matriz vigente de los cuatro ajustes está en [la evidencia del corte anterior](h3req1_c03_engine_unavailable_and_socket_classifier_prep_2026-10-09.md). Los PASS históricos permanecen separados y no se reutilizan como aceptación del WIP.
- Parciales previos, sin incremento: SQL C03 41/41; pytest focal r4 20/20; scanner r7 PASS; UAT BFF r2 60 checks/10 casos de cuota; UAT anterior 144/144; onboarding anterior 10/10; C02 70/72.
- G01=10/10, G02=10/10, G03–G10=0/10; total **20%**, delta 0. D01–D14=0/14. No hay `GO_LOCAL_PR` ni `GO_DEVELOPMENT_REAL`.
- Se preservan BFF/HttpOnly, MFA, roles, gateway, cuotas, cuenta existente, WIP y evidencia histórica. No se interpreta el informe sessionStorage histórico como ataque ni HIGH actual.
