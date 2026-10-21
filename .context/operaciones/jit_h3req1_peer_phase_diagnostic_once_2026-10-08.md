# JIT — diagnóstico local único de identidad Docker por fases

ID: `H3REQ1-C03-PEER-PHASE-DIAGNOSTIC-ONCE-20261008-V1`  
Estado: **SOLICITUD PREPARADA; NO APROBADA; NO EJECUTADA**.  
Autoridad de contexto: autorización consolidada
`H3REQ1-CLOSE-LOCAL-ITERATIVE-20261008-V1`, SHA-256
`4b2649342395f8bb14fb43958d660d3588f1f6ca55bce4a6516858b395cfb4f8`; F2d se consumió y
no se reutiliza.  
Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Objetivo único

Determinar una sola vez si el entorno puede crear un socket Unix, conectarse al endpoint
local seleccionado, leer `SO_PEERCRED`, decodificar sus credenciales y validar internamente
que el peer es el `dockerd` local esperado. El F2d anterior agrupó esas etapas y ocultó la
causa. Su NO-GO no demuestra que el sandbox, el daemon o el motor sean la causa.

## Código y pin de esta revisión

El permiso solicitado cubre la invocación única del diagnóstico descrito aquí. Los hashes
identifican sus bytes revisables y quedan incluidos en el SHA de esta solicitud:

| Archivo | SHA-256 |
|---|---|
| `tests/h3req1_docker_peer_phase_diag/diagnostic_once.py` | `5305d88efd4c2e5e298d22706f2aa1b6490c4da714349d55564c9618dba44b39` |
| `tests/h3req1_docker_peer_phase_diag/test_diagnostic_once.py` | `0ac95af553cb58a1f3c26197838c802ee87be28333508eca5496d086e0b434a6` |

Las pruebas son fixtures sintéticos que simulan proceso, socket y errores; no requieren
Docker ni leen `/proc` real. Quedan preparadas, pero no ejecutadas en este corte.

## Única invocación solicitada

Ejecutar **una vez**, sin retry, con esta llamada del entorno:

```json
{
  "cmd": "timeout --foreground --signal=TERM --kill-after=1s 30s python3 tests/h3req1_docker_peer_phase_diag/diagnostic_once.py",
  "workdir": "/home/romel/src/studiamatch-h3req1-sync-20261002",
  "sandbox_permissions": "require_escalated",
  "yield_time_ms": 10000,
  "max_output_tokens": 200
}
```

La llamada requiere acceso elevado del entorno solicitado explícitamente. La aprobación de
este documento no elude la revisión propia del sandbox.

## Alcance técnico y salida

- Lee el nombre y endpoint del contexto Docker mediante `docker context show` y
  `docker context inspect --format ...`; ambos comandos consultan configuración local y no
  llaman a la API del daemon.
- Rechaza variables de override Docker y cualquier endpoint que no sea Unix local.
- Prueba solo creación/configuración del socket, conexión, lectura `SO_PEERCRED`, decodificación
  y validación local de identidad. No envía bytes de aplicación.
- No ejecuta `docker info`, `docker inspect`, `ps`, `create`, `run`, `start`, `exec`, `wait`,
  `stop`, `rm`, ni consulta contenedores, imágenes, volúmenes o redes.
- No crea/modifica archivos, recursos Docker, motor, daemon, paquetes o configuración. No
  instala herramientas, cambia Docker ni prueba otro motor.
- Límite externo 30 s; dos lecturas locales de contexto con timeout máximo de 5 s cada una;
  conexión Unix con timeout de 3 s; exactamente una ejecución y cero retry.
- La única línea diagnóstica tiene forma `phase=<fase>|error_code=<código>`. Fases posibles:
  `endpoint-resolution`, `socket-create`, `socket-configure`, `connect`, `identity-read`,
  `decode`, `peer-identity` e `identity-verified`. Los errores OS se reducen a un nombre
  simbólico allowlisted o `EOTHER`; los errores de protocolo/validación son códigos fijos.
- No registra ni imprime rutas/endpoints, mensajes de excepción, PID, UID/GID, ejecutable,
  bytes de credenciales, inspect, Env, secretos ni metadata cruda. `identity-verified|OK`
  significa que las validaciones se completaron; no divulga valores del peer.

El criterio de identidad es de metadatos del proceso: credenciales del kernel, PID/UID
consistentes, `comm`/basename `dockerd`, namespace local y ejecutable regular propiedad de
root con permisos seguros. No calcula hash ni verifica firma del binario, por lo que no
atestigua integridad frente a un root comprometido. Reutiliza el predicado de identidad de
F2d; si se requiere autenticidad criptográfica del binario, este resultado no bastará para
continuar y habrá que presentar esa decisión aparte.

## Stop y continuación

Si la llamada falla, preservar solo fase, código sanitizado y exit code. No repetir F2d ni
este intento, no iniciar operaciones Docker dependientes y no cambiar de motor. Presentar la
causa concreta y la siguiente decisión requerida.

Si sale `phase=identity-verified|error_code=OK`, no se ejecutará F1 como efecto de esta
invocación. Reconciliar entonces el alcance A/B/C aún vigente del paquete aprobado, comprobar
sus prerrequisitos y continuar con r9, copia completa, arranque y C03 integrado dentro de sus
límites. Si algún objetivo exige un permiso nuevo, presentarlo agrupado por objetivo antes
de esa etapa.

La solicitud no cambia G01–G10, no ejecuta las pruebas sintéticas, no suma porcentaje y no
declara GO. Solo la respuesta que apruebe este ID y el SHA íntegro del documento habilitará
la única ejecución elevada indicada arriba.
