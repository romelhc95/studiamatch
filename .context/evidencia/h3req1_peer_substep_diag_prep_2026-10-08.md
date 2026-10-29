# H3REQ1 — preparación del diagnóstico peer por subpasos

Fecha: 2026-10-08. Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
Autoridad: encabezado vigente de [estado](../estado_del_proyecto.md), [AGENTS](../../AGENTS.md),
[protocolo constructor](../trazabilidad/protocolo_constructor.md), paquete consolidado
[H3REQ1-CLOSE-LOCAL-ITERATIVE-20261008-V1](../operaciones/h3req1_paquete_consolidado_cierre_local_luna_2026-10-08.md)
y [revisión de bloqueos](h3req1_revision_sesion_01a11de1_bloqueos_2026-10-08.md).

## Ficha de impacto

- **Objetivo:** distinguir el subpaso que falla al probar la identidad del peer Docker y leer
  F1 solo tras superar ese gate. No cambiar runtime ni declarar G04 cerrado por código o docs.
- **Archivos nuevos y aislados:**
  `tests/h3req1_docker_peer_substep_diag/diagnostic_once.py`,
  `tests/h3req1_docker_peer_substep_diag/test_diagnostic_once.py`,
  `tests/h3req1_docker_peer_substep_diag/run_host_admin_once.sh`, este informe y el JIT
  [preparado](../operaciones/jit_h3req1_peer_substep_diag_once_2026-10-08.md). No se editaron
  el helper/test consumidos, estado, índice, CI ni otros WIP.
- **Contrato/impacto:** tooling local de K14 (socket/peer Linux), QA y DOC. No cambia K01–K13,
  SQL/DB, API/producto, BFF/Edge, UI, workflow ni recursos Docker. Consumidores condicionados:
  F1 read, r9, copia completa, arranque Pages/workerd y C03 integrado; el runner no los inicia.
- **Comportamiento preservado:** los accesos a metadata de proceso son los necesarios para el
  predicado de identidad ya revisado. Se rechazan overrides Docker y endpoint no Unix. No hay
  bytes de aplicación. F1 es solo lectura y queda detrás del resultado de identidad positiva.
- **Transición y rollback:** `expand -> compatibilidad -> deploy -> contract` no aplica; no hay
  cambio funcional/de runtime. Rollback es retirar estos archivos nuevos y sus dos notas,
  preservando toda la evidencia y los runners históricos.
- **Pilares:** funcionalidad/escalabilidad/rendimiento del producto no se afectan ni miden.
  La revisión estática independiente no conserva hallazgos abiertos. Las pruebas sintéticas
  siguen sin ejecutar y la invocación autorizada en el host está pendiente.

## Por qué hace falta un nuevo diagnóstico

El helper anterior, con JIT aprobado y consumido, devolvió una única línea
`phase=peer-identity|error_code=EACCES`. Su inspección muestra que, luego de socket, conexión,
`SO_PEERCRED` y decode, este `EACCES` podía venir de lecturas distintas de `/proc` o de volver
a leer la identidad del socket. No especificó causa. El nuevo helper no reusa el F2d ni la
invocación elevada de fase anterior. La única corrida elevada del diagnóstico anterior está
consumida y no se repite.

El runner preparado es para terminal Linux del host Docker con UID efectivo 0. La aprobación
`require_escalated` de Codex **no garantiza** ese UID: el launcher lo comprueba y se detiene
antes de socket/F1 si no lo tiene. El script no ejecuta `sudo` automáticamente. Si el entorno
de Codex no es el host administrador, el comando exacto se entrega para ejecución manual en
terminal del host tras la aprobación JIT; no se presenta el sandbox como equivalente. Incluso
root puede recibir `EACCES` por restricciones de procfs/capabilities; el resultado discrimina
esa fase y no justifica reinstalar/cambiar Docker.

## Fases realmente cubiertas

El auxiliar no usa `os.access()` para inferir permisos. Hace el `open/readlink/stat` real bajo
el contexto que ejecuta la invocación, transforma `OSError` a nombre errno y descarta mensaje,
ruta y valor. Solo emite fases/códigos fijos.

1. Preflight de host root efectivo y checkout/branch/HEAD.
2. `docker context show` e `inspect --format` para configuración local únicamente, con stderr
   descartado; no son llamadas a la API del daemon.
3. Canonicalización y `stat` iniciales del socket seleccionado/canónico, cada una separada.
4. `socket-create`, `socket-configure`, `socket-connect`, `peercred-read` y `peercred-decode`.
5. `/proc/<peer>/stat` antes y después, `/proc/<peer>/comm`, `readlink /proc/<peer>/exe`,
   `stat /proc/<peer>/exe`, `/proc/<peer>/status` (solo parsea `Uid`), namespace PID del peer
   y namespace PID local: cada lectura tiene fase propia.
6. Revalidación por separado del socket canónico y seleccionado después de leer el peer.
7. Solo si lo anterior cumple la regla conocida de identidad, emite
   `peer-identity-verified|OK` y habilita la etapa F1.

No se leen namespaces mnt/net ni otra metadata que no usaba el predicado F2d. No hay hash o
firma del ejecutable; por eso la prueba de identidad es del peer/kernel + metadata existente,
no atestación criptográfica frente a un root comprometido.

## Revalidaciones de socket antes de F1

Además de la revalidación después de leer los metadatos del peer, el helper vuelve a comprobar
el socket canónico y el seleccionado antes de cada consulta F1. Sus cuatro fases diferenciadas
son socket-revalidate-f1-image-canonical, socket-revalidate-f1-image-selected,
socket-revalidate-f1-container-canonical y socket-revalidate-f1-container-selected.
Si alguna falla, la consulta Docker correspondiente no se ejecuta; el resultado conserva solo
fase y código sanitizado.

## Lectura F1 condicional

El mismo JIT de objetivo único incorpora la lectura A autorizada, con condición técnica dentro
del runner: **ninguna Docker API antes de `peer-identity-verified|OK`**. Luego hace, en orden:

1. `docker image inspect --format '{{json .Config.Volumes}}'` para la imagen Node fijada, no
   pull. Acepta solo vacío/`null`/`{}` y stdout queda acotado a 4 KiB.
2. Revalida de nuevo el socket local y hace una sola consulta `docker inspect --type
   container --format` al ID F1 literal ya aprobado. Su proyección contiene exactamente los
   campos allowlisted por el JIT F2 histórico: identidad/estado/OOM/labels; red y rootfs; user,
   capabilities/security options; memoria/swap/CPU/PIDs/restart; tmpfs/count; logging/puertos/
   shm; Binds y Mounts.

Se compara en memoria contra el contrato pre-start; salida posible: `OK`,
`F1_POLICY_MISMATCH` o error de lectura/parser, sin nombre de campo, valores, rutas, Env,
command, `.State.Error`, logs, filesystem, ID/nombre del recurso, stdout crudo ni evidencia en
archivo. Cada lectura tiene timeout 10 s y cap de salida. La consulta de contenedor se omite si
la imagen falla; ambas se omiten si falla cualquier fase anterior.

Los dos riesgos MEDIUM de A permanecen explícitos: el CLI recibe/procesa transientemente el
objeto completo antes del formato; y el mismo usuario puede operar Docker por fuera del
runner. La aprobación consolidada previa aceptó ambos para el objetivo A. La nueva aprobación
es requerida por la nueva invocación/JIT, no por cada campo/hash. El F1 create/start original
está consumido y no se reusa; la lectura de este recurso no crea, arranca, detiene ni limpia
nada.

## Pruebas sintéticas y revisión

`test_diagnostic_once.py` define 32 casos sintéticos previstos sobre socket, credenciales,
falso `/proc`, errores `EACCES`, identidad, revalidación y F1. Incluye errores en cada lectura
de metadata y en ambos lados de la revalidación; éxito de peer que habilita F1; parada de F1 al
fallar imagen/identidad; destino ID/formato exactos; salida sanitizada con un marcador de datos
privados; y un control estático de que el comando JIT verifica el hash fijado del runner antes
de su única invocación. Los fixtures simulan `docker context` y las llamadas Docker: no hablan
con daemon ni leen `/proc` real.

Estado de pruebas: **escritas, no ejecutadas**. AGENTS exige pruebas Python dentro de Docker y
la identidad del peer sigue sin acreditarse. No se corrieron pytest, Docker, helpers, linters ni
checks de runtime. No se declara PASS sintético ni sintaxis ejecutada.

Revisión estática propia del paquete:

- F1 queda después del único punto de identidad validada y va en orden imagen → ID F1.
- Los subpasos de `/proc`, ejecutable y socket post-proc tienen rutas de fallo separadas; solo
  capturan errores para convertirlos a código, nunca imprimen excepciones.
- Subprocesos Docker usan argumentos fijos, contexto/endpoint local, stderr descartado, timeout
  y stdout acotado; no existe acción mutante ni retry en el código.
- El bloque JIT verifica el pin exacto del launcher antes de invocarlo; el launcher exige UID 0,
  branch/HEAD y pin del auxiliar antes de ejecutar el helper una vez. No se autoeleva. Los
  preflights Git usan `-c safe.directory=<checkout>` por proceso para la ruta propiedad de
  `romel`, sin cambiar config global/local.
- Sin hallazgo que amplíe el scope en la revisión manual; la revisión no sustituye al auditor
  independiente o a las pruebas sintéticas ejecutadas.

## Revisión estática independiente — hallazgo LOW resuelto en documentos

La revisión independiente final confirmó el pin del runner antes de una sola invocación y
el conteo de 32 casos sintéticos escritos/no ejecutados. Encontró que la evidencia/JIT no
enumeraban las cuatro revalidaciones locales de socket que preceden a las lecturas F1.
Se incorporaron arriba; son operaciones stat read-only con códigos sanitizados. La revisión
no ejecutó pruebas ni Docker. No identificó otros hallazgos en el alcance revisado.

## Formato de salida

La salida real del helper es exclusivamente registros phase/error_code. Si completa el
recorrido, emite tres registros: peer-identity-verified|OK, f1-image-read|OK y
f1-container-read|OK. Si cualquier fase falla, emite solo la fase y código de ese primer
fallo y termina; el launcher tampoco imprime stderr del helper.

## Autorizaciones, resultado y gates

La solicitud es [nueva y estática](../operaciones/jit_h3req1_peer_substep_diag_once_2026-10-08.md).
Su SHA-256 es `e474440a425e376b238858af820698ec3ea88fb5ef20002de6852eef10e27173`.
El ID anterior `H3REQ1-C03-PEER-PHASE-DIAGNOSTIC-ONCE-20261008-V1` y su SHA
`70764727e392ebb612ca44d9ffadc0bec4b1bb2ef38158d20489b99200c396df` permanecen consumidos.
El JIT F2d y el JIT F1 create/start también permanecen consumidos; el JIT histórico F2 para
leer metadata F1 no se hereda. El nuevo JIT concentra el subdiagnóstico y la lectura F1
condicionada en una aprobación/objetivo. No se ejecutó ninguna acción en este corte.

| Archivo nuevo | SHA-256 |
|---|---|
| `tests/h3req1_docker_peer_substep_diag/diagnostic_once.py` | `794b49ce5560c8cacebbd403c05b4cdbe78fd0c0062d30b6690b901838831463` |
| `tests/h3req1_docker_peer_substep_diag/test_diagnostic_once.py` | `b4c68a3fa9ed2cfe09dc9e6b036a7db9ecec85b55e2dd63625cefb5486e46d81` |
| `tests/h3req1_docker_peer_substep_diag/run_host_admin_once.sh` | `01222bf1c142651e267253313aa6a9d555d69699bda3f025e94b1e307ead8cb6` |
| `.context/operaciones/jit_h3req1_peer_substep_diag_once_2026-10-08.md` | `e474440a425e376b238858af820698ec3ea88fb5ef20002de6852eef10e27173` |

| Gate | Estado que conserva este corte |
|---|---:|
| G01–G02 | 10/10 cada uno; PASS parciales históricos sin cambios. |
| G03 | 0/10; parciales existentes, sin pruebas nuevas ejecutadas. |
| G04 | 0/10; identidad aún no acreditada; nuevo JIT preparado. |
| G05–G10 | 0/10 cada uno; bloqueos existentes sin cambios. |
| Total | **20%**, sin incremento por preparación, hashes ni revisión estática. No GO. |

No se modificó Docker/motor, producto, DB, secrets, GitHub, workflow, reglas, estado o índice;
no se leyó F1 ni se ejecutó r9/copia/startup/C03.

## Addendum vigente — Docker Desktop con WSL integration — 2026-10-08

El usuario aclaró que usa Docker Desktop de Windows con WSL integration. Docker documenta
que el Engine se ejecuta dentro de su distro `docker-desktop`, aislada de Ubuntu; la
integración da acceso al CLI/socket y no convierte `sudo` de Ubuntu en root del proceso
Engine. Por eso el runner peer-substep que exige ver el `/proc` del daemon no acredita el
proceso desde `studiamatch-dev`, otro contenedor ni Ubuntu WSL. El usuario lo ejecutó una vez
en Ubuntu WSL como root; el runner fijado terminó `phase=peer-identity|error_code=IDENTITY_MISMATCH`.
Esa invocación está consumida, no se reintenta y no leyó F1.
Fuentes: [Docker Desktop WSL](https://docs.docker.com/desktop/features/wsl/) y
[networking](https://docs.docker.com/desktop/features/networking/).

Se preparó una alternativa separada, no equivalente a prueba de identidad PID-level:
[JIT Docker Desktop WSL](../operaciones/jit_h3req1_docker_desktop_wsl_attestation_once_2026-10-08.md)
y [paquete consolidado de dependencias](../operaciones/h3req1_cierre_dependencias_wsl_y_ci_2026-10-08.md).
La alternativa fija contexto `default` a `unix:///var/run/docker.sock`, verifica `.Server.Os`
igual a `linux` y solo entonces consulta la imagen fijada y F1 con el proyector previamente
revisado. El usuario aprobó una invocación y aceptó el residual MEDIUM: no identifica PID/UID,
ejecutable ni namespace del peer; depende del endpoint WSL y de la identidad de Docker Desktop
declarada por el usuario. El usuario informó que ejecutó el bloque; la ventana se cerró y las
líneas de resultado aún no se han recuperado. La invocación queda consumida; no repetir.

El código alternativo y sus siete funciones de prueba (12 casos al expandir parámetros)
quedaron preparados. No se
ejecutaron tests, helper ni Docker. Revisión estática propia: un endpoint distinto falla
cerrado; solo context inspect, version `.Server.Os`, image inspect y F1 inspect exacto pueden
llamarse; imagen es anterior a contenedor; fallos de helper se transforman a fase/código fijo;
stderr se descarta, stdout se limita y no hay operación mutante ni retry. Esta revisión no
acredita runtime, seguridad frente a root local ni identidad del proceso del daemon.

| Artefacto alternativo | SHA-256 |
|---|---|
| `desktop_wsl_attestation_once.py` | `c25aa3d3d91bb0cadc160b090c49c4bc61362baefaf3415d046ce7a9cabea4cb` |
| `test_desktop_wsl_attestation_once.py` | `063e05162bb432d7b9c48871da62fae21ff57ac00ffe975a8cfe1795fd4d32b3` |
| `run_wsl_desktop_attestation_once.sh` | `39cebc3e0dbf1e290c11ff6fce0f7a98586209bd94a8af2acf0e6d43cad88f87` |

G04 sigue en 0/10 y el total en 20% hasta que la alternativa aprobada produzca salida runtime
válida con disposición F1. No se cambió Docker, permisos del host, WSL, settings ni el código
de producto.

## Actualización de resultado — peer-substep consumido en Ubuntu WSL — 2026-10-08

El usuario ejecutó una sola vez el bloque fijado por el JIT peer-substep, SHA-256
`e474440a425e376b238858af820698ec3ea88fb5ef20002de6852eef10e27173`. El hash del runner
`run_host_admin_once.sh` coincide con el pin
`01222bf1c142651e267253313aa6a9d555d69699bda3f025e94b1e307ead8cb6`. Salida recibida:
`phase=peer-identity|error_code=IDENTITY_MISMATCH`. La salida sanitizada de `uname` confirma
que la terminal era WSL2. Esta invocación queda consumida; no se repite.

La fase `peer-identity` se emite después de SO_PEERCRED, las lecturas allowlisted del peer y
la revalidación del socket. El predicado final de identidad no pasó; el código no identifica
cuál condición difirió. Conforme al gate del runner, no se consultó Docker API/F1 después del
fallo. No demuestra que Docker esté mal ni justifica rebuild, reinstalación o limpieza.

El JIT alternativo Docker Desktop WSL, SHA-256
`9327c0ea163e47aa35c798442fec4230341b97fda1c19dfa811c492e3416fe4d`, se informó ejecutado
una vez. La ventana se cerró antes de que las líneas sanitizadas llegaran al chat; el runner no
persiste resultado en archivos, así que endpoint/Linux y F1 quedan desconocidos y r9 no se
habilita. No repetir. Si se recuperan las tres líneas PASS, habilita r9 según el alcance A/B ya
aprobado. No se hicieron rebuild/pull, cleanup ni tests desde Codex. G04=0/10, total 20%, sin GO.

## Addendum vigente — captura del resultado perdida — 2026-10-08

El usuario confirmó que no puede recuperar scrollback ni salida. La invocación V1 sigue
consumida y su resultado es desconocido. Se preparó un JIT V2 nuevo, pendiente de aprobación,
que no modifica los runners fijados, guarda stdout solo en memoria, filtra fase/código y pausa
en la TTY para que la salida pueda copiarse antes de cerrar:
[JIT output-capture](../operaciones/jit_h3req1_docker_desktop_wsl_output_capture_once_2026-10-08.md),
SHA-256 `bbaa2242bf026f252864b4e476a60e9de2a8e327c0456d2b343b612402c61c92`. Si se aprueba,
autoriza una sola repetición read-only de endpoint/Linux y F1; solo tres PASS habilitan r9 bajo
los límites existentes. No hubo ejecución ni cambio de gates: G04=0/10, total 20%.
