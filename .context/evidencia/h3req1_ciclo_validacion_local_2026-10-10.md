# H3REQ1 — ciclo de validación local autorizado — 2026-10-10

## Alcance humano

El usuario autorizó en esta sesión el ciclo local H3REQ1 completo para el checkout
`/home/romel/src/studiamatch-h3req1-sync-20261002`, incluyendo correcciones locales dentro de
los contratos H3 aprobados, runners y pruebas, snapshots, fixtures Docker aislados y PG17
desechable. Esta excepción sustituye solicitudes documentales de JIT solo para operaciones
locales incluidas en ese ciclo; no cambia AGENTS ni concede permiso remoto.

Quedan excluidos commit, push, PR, merge, ramas protegidas, CI remoto, workflow_dispatch,
deploy, configuración o acceso a servicios remotos, datos operativos cloud, cuentas/sesiones/correo
reales, secretos, cambios del checkout original `/home/romel/src/studiamatch`, limpieza global,
Docker engine y cambios fuera de H3REQ1. Los runtimes de prueba usan fixtures sintéticos y egress
restringido después del bootstrap.

## Candidato y punto de partida

- Rama: `feat/h3req1-sync-20261002`.
- HEAD baseline: `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- WIP observado al iniciar el ciclo: 55 tracked / 287 untracked / 0 staged; se preserva íntegro.
- Checkout original preservado y fuera de las operaciones.
- Métricas iniciales: tablero G01–G10 = 10%; cierre local G01–G09 = 1/9 (G02), 11.11%.

## Inventario Docker relevante (metadata solamente)

- `studiamatch-dev`, ID `500931b0f086`, imagen local
  `studiamatch-h3req1:20261009-v3` (digest `sha256:5a1c95a7…`), running/healthy, puerto
  `127.0.0.1:3000`; volumen `studiamatch_h3req1_node_modules` montado en solo lectura para
  el runner aislado. No se usó `docker exec` sobre el servicio habitual y no se leyeron Env.
- Imágenes/runtimes históricos y contenedores detenidos se preservan; no se ejecutó limpieza.
- Las pruebas G03 se ejecutan en un contenedor efímero dedicado, con `network=none`, rootfs
  read-only, snapshot/dependencias read-only, 4 GiB de memoria, 2 CPU, sin `.env*` ni credenciales.

## G03 — diagnóstico y ejecución en curso

Evidencia anterior: actionlint, ShellCheck, Next typegen y ESLint PASS sobre inputs identificados;
TypeScript falló con `NODE_HEAP_LIMIT`, exit 134, dentro de un contenedor limitado a 512 MiB.
No hay evidencia de defecto en `tsconfig`; las tres suites protegidas/workflow, scanner y scope
guard no se alcanzaron. Los manifiestos r6 actuales verifican 77 filas de paquete y 68 archivos
fuente presentes; los hashes coinciden con el candidato y no incluyen paths `.env*`. Los tres
workflow inputs reutilizables para actionlint mantienen sus hashes exactos.

Runner para la continuación focalizada:

- Host: `tests/h3req1_docker_peer_substep_diag/run-r9-tsc-heap-continuation-host-v1.sh`.
- Inner: `tests/h3req1_docker_peer_substep_diag/run-r9-tsc-heap-continuation-inner-v1.sh`.
- TSC: `NODE_OPTIONS=--max-old-space-size=3072`; contenedor limitado a 4 GiB y 2 CPU.
- Orden stop-on-failure: manifests/dependencias/versiones → Next typegen requerido por scratch
  efímero → TSC → protected-workflow review → credential scanner → protected-path guard.
- No repite ShellCheck/ESLint/actionlint con inputs intactos; no accede al servicio dev, F1,
  bases remotas, SQL remoto o secretos.
- Los runners pasaron `bash -n` y ShellCheck en Docker aislado; revisión independiente actual:
  sin hallazgos pendientes. El host runner abre evidencia con creación exclusiva, compara el
  exit de Docker con `.State.ExitCode`, y solo marca cleanup PASS tras verificar ID, digest,
  labels y retirada. Señales durante cleanup se registran como diferidas.
- Aprobación humana local ya registrada; no se solicita un JIT adicional para este ciclo.

### Intentos G03 y correcciones — 2026-10-10

Los dos intentos se conservaron por separado en
`h3req1_g03_r9_tsc_heap_and_pending_suites_2026-10-10.txt` y su variante `_v2.txt`.
Ambos verificaron rama/HEAD, snapshot r6, 68 fuentes, actionlint reusable, dependencias y
versiones; ambos limpiaron el fixture exacto con `phase=r9-fixture-cleanup|error_code=OK`.

- V1: exit 1 en `next typegen`; TSC y las tres suites no comenzaron. Se encontró un defecto
  concreto del runner: invocaba Next desde la raíz aunque los manifests/configuración están en
  `web/`. La salida de V1 pegó `exit` y cleanup por pérdida de newline en command substitution.
- V2: tras ejecutar typegen y TSC desde `web/`, typegen siguió en FAIL exit 1 y clasificó
  `DEPENDENCY_MISSING`. Esto descarta que cambiar el cwd fuera suficiente; la causa del mensaje
  interno todavía no está identificada y no se atribuye a Docker ni al producto. Next/TS/node
  principales están presentes, pero una prueba de `require.resolve` al subpath no acredita el
  grafo completo. No se reinstalaron dependencias.
- Corrección actual del clasificador: si typegen falla, emite una clase cerrada y un nombre de
  módulo solo si pasa un allowlist estricto; stdout/stderr crudos nunca salen del contenedor.
  TSC también corre en `web/`, con heap 3072 MiB dentro del límite de 4 GiB. Evidencia v3 aún
  no ejecutada; V3 está pendiente solo de la nueva invocación de la secuencia G03 local ya
  autorizada.

No se declara G03 completo: TSC y las tres suites siguen pendientes. El runner no modifica
fuentes funcionales; ShellCheck y revisión independiente del runner pasan para los pines actuales.

## Siguientes gates

G01 conserva C02 aplicable y requiere renovar únicamente SQL/editorial afectado, incluida la
captura de exit del harness. G02 conserva C03 SQL aislado v3 41/41 mientras sus inputs sigan
coincidiendo. G04 requiere corregir el parser/verificador F1 según reducción mínima acreditada;
G05 snapshot completo; G06 Pages/workerd hasta healthz; G07 C03 integrado con Edge/PG17/
PostgREST; G08 checks finales del candidato; G09 aceptación local, UAT 144/cero retries,
onboarding 10/10, seis pilares y revisión sin bloqueantes. G10 CI remoto permanece fuera de esta
autorización. Ninguna etapa remota está autorizada ni ejecutada.

## Resultado de esta sesión

Se completará después de cada gate con candidato/inputs, fases y exits sanitizados, cambios
propios, recursos activos y siguiente acción. No se declara GO por plan, código o pruebas parciales.

## Corrección de privacidad del clasificador G03 — 2026-10-10

La revisión independiente halló que el primer clasificador podía aceptar una ruta absoluta en el
campo `module`. La reproducción mínima aislada dio `synthetic_absolute_path_accepted=true`.
Se extrajo el parser a `tests/h3req1_docker_peer_substep_diag/r9_typegen_classifier_v1.py` y se
añadieron sintéticos para rutas Unix/Windows, relativas, traversal, paquetes no declarados y
subpaths válidos. El filtro conserva solo la raíz de paquetes declarados; las entradas no válidas
se convierten en `UNCLASSIFIED`.

Prueba sintética en contenedor local sin red: PASS, exit 0. Python compile, `bash -n`, ShellCheck
0.11.0 desde bundle cacheado y `git diff --check`: PASS. No se usó egress ni se leyó `Env`.
Hallazgo del producto/Next aún no determinado. Los dos intentos previos permanecen como evidencia
separada; no se repitió typegen ni se ejecutaron TSC/suites. Revisión independiente del nuevo pin
pendiente antes de reanudar el runner G03. G03 permanece 0/10 y G01–G09 local 1/9; no hay nuevo
gate completo.

## G03 — continuación completada tras corregir el intérprete pytest — 2026-10-10

### Candidato e inputs

- Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
  `feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- Snapshot r6: `r4-package.sha256=d10cc19b87adfff36f8092c97b59dc8fb4a247166c0dcbf8f0653dd9f2db6186`,
  `inputs.sha256=c53e3321190646a2449e28b935711fc6f7b8425d1b19289f2374f4488eaff4c8`; 68 fuentes
  coincidentes, 77 filas de paquete y ningún `.env*`.
- Imagen: digest local `sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63`.
- La secuencia V5 corrió en un contenedor efímero `--network=none`, rootfs read-only, mounts
  read-only, 4 GiB, 2 CPU y heap Node 3072 MiB. Fixture `e16ce8a6c95e6d4dd7b10c3c6c23847935445fd32991b84b6081de96ad550e79`;
  exit de Docker, contenedor y gate 0. Cleanup del ID exacto PASS.

### Fallo, causa y corrección

V4 preservó el fallo real: `next typegen` y TypeScript pasaron; la suite de workflow protegido
terminó exit 1 y el clasificador reportó `failed=UNKNOWN`. La salida correspondía a la invocación
`python3 -m pytest`, que no llegó a ejecutar casos. Una lectura mínima, read-only, de la imagen
fijada demostró `system_python_pytest=missing` y `/opt/venv/bin/python` con pytest `9.1.1`.
`Dockerfile` instala requisitos pinneados en `/opt/venv`; por tanto, el defecto estaba en el
intérprete invocado por el runner, no en el código del test ni en el producto.

Corrección mínima: el runner ahora exige `/opt/venv/bin/python`, comprueba `import pytest` y
ejecuta con ese intérprete. El host usa una ruta de evidencia V5 exclusiva y preserva V4. El pin
del inner runner coincide con el host. `bash -n`, ShellCheck 0.11.0 en Docker aislado y revisión
independiente de los cambios: PASS / sin hallazgos.

### Revalidación V5

Evidencia durable:
[V4 diagnóstico de intérprete](h3req1_g03_r9_tsc_heap_and_pending_suites_2026-10-10_v4.txt) y
[V5 resultado completo](h3req1_g03_r9_tsc_heap_and_pending_suites_2026-10-10_v5.txt).

```text
phase=g03-candidate-source|error_code=68_INPUTS_MATCH
phase=g03-actionlint-reuse|error_code=INPUT_HASHES_MATCH
phase=r9-container-preflight|error_code=OK
phase=r9-candidate-copy|error_code=OK
phase=r9-npm-dependency-manifest|error_code=OK
phase=r9-node-and-typescript-versions|error_code=OK
phase=r9-typegen-classifier-synthetics|error_code=OK
phase=r9-next-typegen|error_code=OK
phase=r9-typescript|error_code=OK
phase=r9-protected-workflow-tests|error_code=OK
phase=r9-credential-scan|error_code=OK
phase=r9-protected-path-guard|error_code=OK
phase=r9-summary|error_code=ALL_PENDING_CHECKS_OK
phase=r9-fixture-cleanup|error_code=OK
exit=0
```

ShellCheck and ESLint PASS from the prior r9 V7 run remain applicable: it used the same r6
package, all 68 current candidate sources match that manifest, and the web manifests/configs and
workflow hashes are unchanged. The current runner confirmed workflow hashes before reusing
actionlint. G03 is complete (10/10). Historical G01–G10 total is now 20% (G02 + G03); local
G01–G09 is 2/9 = 22.22%. No other gate was advanced by this result.

### Estado y recuperación

Al cierre de esta fase el checkout candidato conserva rama y HEAD base; WIP medido con
`git status --porcelain --untracked-files=normal`: 55 entradas tracked, 294 entradas untracked y
0 staged. El checkout original no fue tocado. No se leyeron secrets/Env, no hubo egress, pull,
build, install, DB/SQL, F1 ni operaciones remotas. El siguiente gate es G01: conciliar los
inputs actuales con el cierre transitivo C03 v3 y renovar únicamente la cobertura editorial
afectada. Mantener G02 histórico sujeto a los mismos inputs. Después proceder G04→G09 sin saltos
tras FAIL.

## Actualización G01 — 2026-10-10

Se comprobó nuevamente el cierre transitivo C03 SQL v3: 41/41 hashes actuales, sin ausentes ni
deltas; no se volvió a ejecutar ese harness. El manifiesto editorial vigente fijó 36 inputs y
pasó 36/36. Su ejecución PG17.11 aislada terminó exit 0, confirmó el marcador y verificó la
retirada del contenedor exacto. Evidencia sanitaria: `h3req1_editorial_atomicity_pg17_v3_once_2026-10-10.txt`,
SHA-256 `e85fcbfcf983c3bd2bf96417632259a872094bc956985336ba98c399fa0e630a`.

C02 permanece en 69/72, no 72/72: el harness editorial afectado queda renovado; los deltas
BFF/workflow corresponden a cobertura G08/G10. G01 pasa a 10/10. El tablero histórico es 30%
(20% inicial, delta +10 puntos); cierre local 3/9 = 33.33% (2/9 inicial, delta +11.11 pp).
G04 es el siguiente gate. Esta ejecución no tocó recursos persistentes ni ambientes remotos.

## G04/G05 — proyección F1 y snapshot completo PASS — 2026-10-10

Candidato: rama feat/h3req1-sync-20261002, HEAD base
4eb4d877a50b012bb630a129bd0c74482c33be9c, WIP antes del runner 55 tracked / 300 untracked /
0 staged. Se conservó todo el WIP y el checkout original.

La reproducción sintética mínima que redujo V14 a una interacción de expresiones se resolvió
separando los 21 campos no conflictivos y leyendo cuatro expresiones en invocaciones individuales:
NanoCpus, Tmpfs["/snapshot"], len(Tmpfs) y Mounts. Se recompone el orden y formato de los
25 campos originales. No se eliminó ningún predicado de seguridad. El límite de timeout se fijó
como regex cerrada 1–15 para evitar aritmética Bash con cadenas arbitrariamente largas.

Prueba en Docker node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844,
network=none, rootfs read-only, usuario 1001, 256 MiB, 0.5 CPU y /tmp tmpfs 16 MiB:

- bash -n: PASS.
- Suite de proyección: PASS, composition=25, mapas present-absent, cuatro lecturas aisladas,
  negative-cases=11; exit 0. Cada lectura simuló el LF terminal de Docker. Los timeouts 16 y
  entero largo se rechazaron antes de llamar a Docker; los fallos parciales vacían resultados.
- ShellCheck 0.11.0 en contenedor aislado: PASS.
- git diff --check: PASS.
- Revisión independiente estática de helper/test/runner/sidecar: PASS sin hallazgos. El revisor
  confirmó que Bash command substitution remueve el único LF final permitido y que LF interno,
  repetido, CR y NUL se rechazan.

Un primer arranque del test sintético en rootfs read-only falló en setup (mktemp, exit 1) por
no disponer de /tmp; no alcanzó la función bajo prueba ni Docker. Se cambió únicamente el
entorno de prueba, agregando /tmp tmpfs acotado 16 MiB, y la única revalidación pasó.

El runner tests/h3req1_c03_source_snapshot_f1_v2.sh se ejecutó una vez como usuario no-root,
con launcher hash-bound, timeout externo e interno de 180 s, usando imagen local fijada y sin
pull/retry. Resultado durable:
evidencia/h3req1_c03_source_snapshot_2026-10-10_v2.md:

    container-create-status=0
    container-controls=PASS|state=created|exit=0|oom=false|network=none|rootfs=read-only|user=1001:1001|cap-drop=ALL|memory=128m|cpus=0.5|pids=64|snapshot-tmpfs=96m|shm=16m|persistent-mounts=none|logs=none
    source-snapshot=PASS|files=14|source-manifest=13/13|no-same-owner=true
    source-tar-producer-status=0|tar-bound-status=0|docker-start-status=0|output-filter-status=0
    container-controls=PASS|state=exited|exit=0|oom=false|network=none|rootfs=read-only|user=1001:1001|cap-drop=ALL|memory=128m|cpus=0.5|pids=64|snapshot-tmpfs=96m|shm=16m|persistent-mounts=none|logs=none
    source-snapshot-result=PASS
    source-snapshot-exit=0|phase=complete

WIP tras crear evidencia y el cidfile: 55 tracked / 302 untracked / 0 staged. La imagen y el
contenedor terminado h3req1-c03-source-snapshot-f1-v2-20261010 se conservan para inspección
acotada/recuperación; no se hizo limpieza. G04 y G05 pasan. Tablero G01–G10: 30% → 50% (+20 pp).
Cierre local G01–G09: 3/9 → 5/9 = 55.56% (+22.22 pp). Siguiente gate G06: arranque real
Pages/workerd y healthz; G07 solo procede tras PASS.

## Revalidación de fuente F1 V3 y preparación G06 — 2026-10-10

El cambio acotado de `tests/h3req1_c03_integrated_runtime.mjs` selecciona el manifiesto de
fuentes V3 en `startupOnly` y mantiene el manifiesto integrado original fuera de ese modo. Esto
invalidó la vigencia del snapshot V2, que queda preservado como histórico. Se revalidó solo la
captura afectada con `tests/h3req1_c03_source_snapshot_f1_v3.sh`.

F1 V3: runner SHA-256
`9b9d010787836c9c317fe3e451ff63d17b94b48ba154421306bff6c305f64211`, sidecar SHA-256
`6377c544113c302cef3ee91be821e83675e794c62b5e1e132f16ff2c755ad3c9`, source manifest SHA-256
`4b6e99fb6feb85eb8b4ea8e899e69c2d3c497657b507b03004d45981b97417c8`, helper SHA-256
`7be1caec879e7e22db6da8c10a0623f254ec329e101ed675b7928803cba005f6`. Se ejecutó una vez como
usuario no-root; el launcher verificó pins y el runner revalidó rama, HEAD, socket, contexto y
daemon. Candidato `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
Resultado en [evidencia F1 V3](h3req1_c03_source_snapshot_2026-10-10_v3.md): productor tar,
receptor Docker, filtro/verificador exit 0; 14 archivos/540831 bytes, 13/13 hashes, sin symlinks,
`--no-same-owner`; contenedor `032d29993a847f5737dc68970de2a13573f786c51f17e2308884ded198f86fef`
exited 0, `network=none`, rootfs readonly, user 1001, 128 MiB, 0.5 CPU, sin mounts persistentes,
logs ni puertos. Recurso y cidfile se conservan. G04 y G05 permanecen completos; no se incrementa
el porcentaje por esta revalidación.

La revisión independiente encontró inicialmente (MEDIUM) que el smoke aceptaba cualquier socket
Unix local y (LOW) que S2 no fijaba el path del checkout. Se corrigieron ambos runners para exigir
el checkout S2 canónico, contexto `default`, endpoint `unix:///var/run/docker.sock` e identidad
Docker Desktop `fc2115b2-c3c4-440e-89c6-26899eb7cb04|docker-desktop|Docker Desktop`. La segunda
revisión estática cerró esos findings sin hallazgos concretos. `studiamatch-dev` se observó
healthy en `studiamatch-h3req1:20261009-v3`, mount del candidato `/app`, y puerto loopback
3000; no se leyó Env ni se ejecutaron pruebas en ese servicio.

Preflight S2 al corte: runner SHA-256
`67f108ee253e8c7540f5f6bd3fc8533576b1ceaf264fe8f5c1a70525b8e3daae`, manifest SHA-256
`18cda74992361c971d355159c6454477111d86216af30e11089e3ced3575dc62`. `sha256sum -c` para los
manifiestos S2/fuente/F1, `bash -n`, `node --check`, ShellCheck 0.11.0 con severity warning y
`git diff --check` pasaron. El primer preflight combinado falló antes de tests porque
`studiamatch-dev` no tiene ShellCheck; un default ShellCheck independiente devolvió solo mensajes
`info` SC2016/SC2015/SC1091. Se descargó la imagen oficial `koalaman/shellcheck:v0.11.0`, digest
`sha256:61862eba1fcf09a484ebcc6feea46f1782532571a34ed51fedf90dd25f925a8d`, y se usó en contenedor
efímero sin red con mounts readonly. Ningún cambio en dependencias del proyecto.

S2 se ejecutó una vez. `create-new-source-snapshot` falló: receptor `docker run` exit 2, runner
exit 1. El tar productor y entrada quedaron fijados; en reproducción mínima dentro de la imagen
Node pinned, con `network=none`, rootfs read-only y `cap-drop=ALL`, `tar -xf` intentó restaurar
UID/GID y devolvió `OWNER_RESTORE_DENIED` (exit 2). El fixture de un archivo con
`tar --no-same-owner -xf` terminó exit 0. No se alcanzaron bootstrap npm, red interna, Pages,
workerd ni healthz. Los recursos S2 siguen preservados; no hubo cleanup. Detalle en
`h3req1_c03_startup_smoke_2026-10-10_s2_diagnosis.md`.

La corrección está aislada en S3: `tests/h3req1_c03_startup_smoke_s3.sh` usa
`tar --no-same-owner`, pins y recursos nuevos, sin modificar S2. Runner SHA-256
`4077a9c6e14a0588fb972f77c4b27385cc223306a63bbaea553b239c87af1689`; manifest SHA-256
`351c6590c24c466fe8af531f1d9661ef7a6fcc1f7170c617f223fefc70bdc018`. Bash syntax, ShellCheck
0.11.0 warning-level, `git diff --check` y revisión independiente estática: PASS sin hallazgos.
## G06 — continuación del startup smoke S3 detenida y recuperación focal — 2026-10-10

S3 corrigió el snapshot (exit 0, 14 archivos, cero symlinks, hashes vigentes) y completó ambos
bootstrap `npm ci` en contenedores temporales (`tools` y `pages`, exit 0). Se detuvo en
`create-new-egress-blocked-internal-network`, exit 1, antes de Pages/workerd/healthz.

Causa demostrada: el runner comparó stdout de `docker network create` con el nombre de red; la
salida de éxito del Docker CLI es el ID. Inspección read-only del recurso comprobó el nombre S3
exacto, ID de formato Docker, bridge internal, etiquetas JIT/manifiesto coincidentes y run label
presente. El predicado del runner falló aunque la red estuviera correctamente creada. No se
atribuye a Docker Engine ni al producto. Evidencia detallada:
`h3req1_c03_startup_smoke_2026-10-10_s3_diagnosis.md`; resultado crudo del runner permanece
sanitizado en `h3req1_c03_startup_smoke_2026-10-10_s3.md`.

S2 y S3 se conservan. S3 mantiene snapshot/tools/pages containers con exit 0, holder activo, tres
volúmenes tmpfs identificados y una red internal. No se hizo cleanup. Se evita repetir los dos
bootstraps: el siguiente runner verificará artefactos y labels de S3, resolverá la red por
metadata estructurada, montará los volúmenes read-only y ejecutará solo el runtime dentro de esa
red sin egress. G06 permanece 0/10 y G07 bloqueado hasta healthz PASS. G01–G05: 50% histórico y
5/9 = 55.56% local, delta 0 en esta fase.

## G06 S4 — runtime FAIL; verificador de red post-exit corregible — 2026-10-10

Antes de ejecutar, el runner actualizado pasó `bash -n` en `studiamatch-dev`, ShellCheck
0.11.0 warning-level en la imagen oficial, `git diff --check`, todas las entradas del manifiesto
S4 y revisión independiente. La revisión cerró el LOW de carrera de red: cero endpoints antes de
arrancar, `docker run --network` con el ID validado y verificación posterior del `NetworkID`.

Ejecución S4 única: `bash tests/h3req1_c03_startup_smoke_s3_resume_s4.sh --jit
H3-CLOSE-03-WORKERD-STARTUP-SMOKE-2026-10-10-S4-RESUME-S3 --runner-sha256
c4659f16889a41987c6512d7167ffe397d6a31edf58b645a77bc888d627eca7c --manifest-sha256
1cb90249466e65ccf59fc6ae3d2d7088f8c658917d91ece5f55c66bfd9268f29`; exit 1 en
`one-shot-pages-workerd-runtime-healthz`. El runtime preservado terminó exit 1 y sin OOM;
healthz observó `ECONNREFUSED`, luego `runtime-exited-before-ready`. La última etapa conocida es
`dependency-roots-present`; no hubo marcador `runtime-ready`. El output stderr no clasificado se
suprimió. No está demostrada la causa interna entre TLS/Miniflare/listeners; no se atribuye a
Docker ni al producto.

Fallo secundario del runner demostrado por metadata estructurada: tras detenerse el runtime, el
contenedor conserva `HostConfig.NetworkMode` igual al ID S3 y Networks muestra la clave/nombre y
`NetworkID` exactos; `EndpointID` queda vacío post-exit. La exigencia de EndpointID causó el
`NO-GO` del verificador, no evidencia de conexión a otra red. Corrección siguiente: no exigir
EndpointID después del exit y añadir captura segura del tipo/etapa de error del proceso antes de
runtime-ready. No se repite S4 intacto.

Evidencia: resultado sanitario S4 SHA-256
`4136061965cde82eb926c450ac2efaafcd3832551097fd7767de0393398fea87` y
[diagnóstico S4](h3req1_c03_startup_smoke_2026-10-10_s4_diagnosis.md), SHA-256
`581b7230713344142911357f63d890408705f6bde0c7124de3414df941517fc4`. Contenedor S4, S2/S3,
holder, volúmenes y red permanecen; no hubo limpieza. WIP actual: 55 tracked modificados /
319 untracked / 0 staged. Checkout original intacto. No hubo egress, credenciales, SQL, Edge,
servicios remotos, publicación ni deploy. G06 incompleto; G07 detenido; G01–G05 siguen 50%
histórico y 5/9 = 55.56% local.

## G06 S5 — Pages/workerd runtime exit 1; diagnóstico aún no clasifica la excepción — 2026-10-10

El preflight S5 pasó la verificación de manifiesto y sintéticos; la revisión independiente cerró
el LOW de symlink en `.context/evidencia` y no encontró riesgos nuevos. Bash syntax, ShellCheck
0.11.0 warning-level y `git diff --check` pasaron antes de ejecutar. Runner SHA-256
`6e886754cde2c4a3feb998adaea6d8d5ecde03558eae15841e4cdb2c60347fdf`, manifiesto SHA-256
`08a428daf847d690f4f72fdad03379eab4faeeba64362b78762c28e6f9e4ab03`.

Ejecución S5 única: exit 1 en `one-shot-pages-workerd-runtime-healthz`. S3 resources y red-ID
PASS; sintéticos del probe PASS; `dependency-roots-present`; el único marco capturado fue
`runtime.mjs:800:3`; healthz NO-GO después de 3 intentos; proceso exit 1 sin OOM. Esto ubica el
fallo en la inicialización esperada de Miniflare/workerd, pero no determina el subpaso exacto. El
runner preservó el contenedor `h3req1-c03-startup-runtime-20261010-s5`, los recursos S3 y la red.
No hubo retries, egress, DB/Edge/SQL, secretos, recursos persistentes ajenos o remotos.

Evidencia sanitizada S5 SHA-256
`c7d32cbe20929e5db473fa6331d5a34117a30a7ad24776ebb412d88e06b45f3b`; diagnóstico
[`S5`](h3req1_c03_startup_smoke_2026-10-10_s5_diagnosis.md). No se repite S5 intacto: el probe
actualizará la clasificación de la excepción y emitirá hasta ocho marcos numéricos permitidos,
sin mensajes ni stack crudo; luego será revisado antes de una continuación S6 corregida.
G06 sigue 0/10; G07 no inicia. Métricas: G01–G10 50%, cierre local 5/9 = 55.56%, delta 0.

## G06 S6 — MiniflareCoreError clasificado; subfase exacta pendiente — 2026-10-10

S6 corrigió el filtro para aceptar los dos tipos Miniflare emitidos por la sonda y luego cerró
`error.code`/spawn code con listas finitas. Se agregaron sintéticos para `ERR_WORKER_INIT`,
`ENOENT`, `API_SECRET_ABC` y `SUPABASE_SECRET_KEY`; los códigos tipo secreto se convierten en
`UNCLASSIFIED`/línea suprimida. Node syntax y sintéticos, Bash syntax, ShellCheck oficial v0.11.0,
manifiesto y `git diff --check` pasaron. La revisión independiente inicial detectó el LOW del
código abierto; se corrigió y la segunda revisión quedó sin findings.

La ejecución S6 única terminó exit 1 en `one-shot-pages-workerd-runtime-healthz`. Evidencia:
`dependency-roots-present`, `runtime-error-class=MINIFLARECOREERROR`,
`runtime-project-frame=line:800:column:3`, healthz NO-GO tras 4 intentos y exit 1 sin OOM.
Contenedor S6 preservado: ID
`e7dcb0e20e47fd8d1c26ab6e5ce6674b10fb480bcc67dabcaf24cbe2e7cf1f36`, estado exited, red interna
S3. Resultado sanitizado S6 SHA-256
`38f5ff8c466886ae405db19bc26ad498accacf14e9de95218d1f7816bcde9b74` y
[diagnóstico S6](h3req1_c03_startup_smoke_2026-10-10_s6_diagnosis.md). La clase indica la ruta
Miniflare/workerd, pero el marco apunta solo al `await runServer`; no distingue directorios/TLS,
bundles, constructor ni `getWorker`. No se atribuye causa al producto/engine. G06 sigue 0/10, G07
detenido y las métricas no cambian: tablero 50%, cierre local 5/9 = 55.56%.

La continuación autorizada prepara instrumentación de fase alrededor de esas fronteras con códigos
cerrados y salida sanitizada. Se conservan snapshot/volúmenes S3 y contenedores S4/S5/S6; no hubo
cleanup, Edge, DB/SQL, egress ni operaciones remotas.
