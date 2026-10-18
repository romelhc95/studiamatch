# Validación aislada del helper/parser y regresiones — 2026-10-08

## Identidad y alcance

Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, baseline HEAD
`4eb4d877a50b012bb630a129bd0c74482c33be9c`. Esta evidencia registra una sola
ejecución efímera autorizada para probar fixtures sintéticos. No ejecutó F2d contra
F1 ni accedió a PostgreSQL, Supabase, Cloudflare, GitHub o servicios remotos.

El usuario autorizó el contexto Docker local y una ejecución con la imagen inmutable
`sha256:29d8fff9a799aaacd45d771696f40762511d4c3a4c1ebfe536bd2a69a2f16be0` y el paquete
de seis archivos en `/tmp/h3req1-helper-validation-29d8fff9-20261008`, cuyo
`inputs.sha256` tiene SHA-256
`35c50b4a664c68930e535d9700649f450d5cd1b64d59612f32c03d0e00c3812e`. El contexto
activo era `default` con endpoint `unix:///var/run/docker.sock`. La primera invocación
fue rechazada por permisos antes de crear un contenedor; la misma invocación se realizó
después con permiso elevado, sin ampliar el alcance. `--rm` eliminó el contenedor
efímero al terminar. No se borraron imágenes ni recursos preexistentes.

La ejecución usó `--pull=never`, `--network=none`, raíz de solo lectura, usuario
`1001:1001`, capacidades descartadas, `no-new-privileges`, límites de memoria/CPU/PID,
`/tmp` efímero y un único montaje de solo lectura del paquete. No montó `.env*`, el
socket Docker, archivos de la aplicación ni datos privados. Las pruebas usaron sockets,
procesos y metadata sintéticos; la prueba dentro del contenedor no llamó a Docker API.

## Comando y resultado

```bash
docker run --rm --pull=never --network=none --read-only --user 1001:1001 --cap-drop=ALL --security-opt=no-new-privileges --memory=512m --memory-swap=512m --cpus=1 --pids-limit=64 --tmpfs /tmp:rw,noexec,nosuid,nodev,size=16m,uid=1001,gid=1001,mode=0700 --mount type=bind,src=/tmp/h3req1-helper-validation-29d8fff9-20261008,dst=/validation,readonly --workdir /validation --env PYTHONDONTWRITEBYTECODE=1 --entrypoint bash sha256:29d8fff9a799aaacd45d771696f40762511d4c3a4c1ebfe536bd2a69a2f16be0 -euc 'sha256sum -c inputs.sha256 && python3 -m pytest -q -p no:cacheprovider tests/test_h3req1_c03_docker_daemon_identity_f2d.py tests/test_protected_workflow_review.py && bash tests/test_h3req1_c03_docker_inspect_projection.sh'
```

`sha256sum -c inputs.sha256` pasó para los seis archivos del paquete. Pytest terminó
`12 passed, 1 failed` (exit 1). El fallo fue
`test_rejects_distinct_selected_socket_before_reading_peer`: el test empaquetado
reemplazaba `socket.socket` globalmente y luego intentó crear el segundo socket del
fixture mediante esa sustitución, que no implementaba `bind`. La aserción del helper
no llegó a ejecutarse. El helper F2d del paquete coincide con el archivo actual
(`f117a1c4d6f769d161c1401daa78de166746729ad84a2e1431ca26967aa5612d`), pero el test
empaquetado no coincide con la versión actual: paquete
`40970955360a21ca30618e16a33cf498e4a42df13dcb14d4fabbc471ba68b60c`, worktree
`ffc66e809830bdcb873c8e9f37da8f09df80eb323d0817d46bb54bacb51e1498`. El worktree
conserva `REAL_SOCKET` para crear sockets reales del fixture; esa corrección aún no
está revalidada.

El proyector regresivo `tests/test_h3req1_c03_docker_inspect_projection.sh` estaba en
el paquete, pero no corrió porque pytest falló y el comando encadenado se detuvo.
Resultado global: **NO-GO de esta etapa**; no se atribuye un fallo al helper ni se
declara validado el paquete actual. La aprobación de una sola ejecución quedó
consumida. F2d no se ejecutó contra F1 y su JIT y sus dos aceptaciones MEDIUM siguen
pendientes.

## Cambios de seguridad revisados y validación pendiente

- El r3 ejecutó la regresión del scanner y falló al redactar; también se confirmó en
  revisión estática que `grep -I`, sufijos omitidos y el parser del diff no cubrían todos
  los blobs. El código ahora escanea blobs binarios de índice/commit y la regresión agrega
  NUL, `.lock`, línea `++` y contenido binario cambiado. Esa versión aún no corrió.
- El scope guard consume rutas Git delimitadas por NUL, falla cerrado ante registros
  malformados o controles y evita imprimir rutas no confiables. Su regresión pasó en r3:
  `ordinary=3|newline=1|controls=1|malformed=3`.
- El reviewer de workflows protegidos considera rutas anterior y nueva en renombres,
  falla cerrado ante registros de renombre incompletos y al límite de 3000 archivos de
  GitHub. Sus pruebas están dentro de los 19 pytest aprobados en r3; esto no prueba que el
  check independiente sea requerido en la configuración de ramas.
- `actionlint` y ShellCheck no se ejecutaron. El Dockerfile del proyecto no declara
  esas herramientas y su presencia en la imagen no se verificó; requieren una ruta de
  validación autorizada con herramientas disponibles.

## Continuación del ciclo: guardia HMAC y revisión actual — 2026-10-08

### Ficha del cambio local

- Componente: Pages Admin BFF en `web/functions/_lib/admin-bff.ts`; la entrada se enruta
  desde `_middleware.ts` y consume cuota a través de `admin-quota.ts` antes de las rutas
  Admin normales. La firma del RPC usa el secreto de gateway en la misma capa.
- Contrato afectado: `ADMIN_QUOTA_HMAC_KEY` y `ADMIN_RPC_GATEWAY_HMAC_KEY` deben ser
  distintos por ambiente. El BFF ahora devuelve un error genérico 503 si ambos valores
  están presentes y son iguales, antes de admitir cuota o invocar RPC; el logout local
  conserva su respuesta de limpieza de cookies.
- Consumidor de validación: `tests/h3_admin_bff_mock_uat.mjs` agrega una fixture sintética
  de colisión que exige 503 y cero llamadas a cuota/RPC. La UAT pasó en el paquete aislado
  BFF r2 con 60 verificaciones y 10 casos de cuota; r4 no contenía estos archivos.
- Impacto y permisos: solo cambio local de código/test bajo `continua`; no cambia SQL,
  grants, secretos ni servicios remotos. No verifica los valores ni bindings desplegados.
  El permiso de ejecución BFF r2 está consumido; la validación helper r4 mantiene aprobación
  separada pendiente.
- Atestación/pilares: se mantiene dentro de H3 `CA4` y de la aceptación local del BFF
  sanitizada el 2026-10-01 (same-origin, cookie HttpOnly, RBAC y MFA); no agrega un flujo
  de negocio ni amplía permisos. Reduce el riesgo de configurar ambas funciones con una
  misma clave, a costa de bloquear Admin con 503 si ocurre la colisión. Logout se conserva.
  La regresión sintética pasó; no hay medición de rendimiento ni evidencia de valores
  efectivos por ambiente.
- Transición `expand -> compatibilidad -> deploy -> contract`: expandir primero los
  bindings y claves independientes por ambiente; la versión previa del BFF puede operar
  con esa separación. Desplegar el guard solo con configuración distinta verificada bajo
  JIT remoto. Rollback vuelve a la versión Pages anterior manteniendo ambas claves
  separadas. El guard no retira rutas ni contrato legacy; contract queda sin eliminación
  de comportamiento, a confirmar con estabilidad. Todo esto es requisito de promoción,
  no una operación realizada ni autorizada aquí.

### Revisión estática del snapshot actual

Codex Security scan `13b4219e-4661-4e92-b4e0-1aafffc88ee3` quedó completado para el
snapshot `codex-security-snapshot/v1:sha256:e20b46145f4fed6119fe2475ec0c6571bf4206d835c6c467ea2766716298c0cb`, baseline
`4eb4d877a50b012bb630a129bd0c74482c33be9c`. Revisó 51/51 rutas del inventario; reporta
cero hallazgos confirmados, cuatro candidatos diferidos y cobertura parcial. La revisión
estática verificó el orden del nuevo guard, pero no ejecutó pruebas ni afirma runtime.
Persisten la confirmación de email/Auth, reglas y costos de CI en GitHub, el host/base
efectivos del mock y los bindings/valores HMAC desplegados. El guard de código reduce el
riesgo ante una colisión, pero no demuestra que la configuración de cada ambiente esté
correctamente ligada.

La revalidación hash más reciente encontró que C02 v4 no-C03 ahora coincide 70/72 por
el cambio previo del workflow y el nuevo guard HMAC de `admin-bff.ts`; C03 SQL v3 sigue
41/41. No se repitió ninguna suite SQL/wire. El test sintético nuevo está enlazado por
workflow en `security-audit.yml`, pero debe ejecutarse sobre estos bytes antes de cerrar.
Ver [detalle de hashes](h3req1_revalidacion_hashes_2026-10-08.md).

El reporte y SARIF canónicos están bajo
`/home/romel/.codex/state/plugins/codex-security/scans/studiamatch-h3req1-sync-20261002/4eb4d877a50b012bb630a129bd0c74482c33be9c_20261008T163856Z_13syg3_u/`.
La ejecución r4 continúa pendiente de la autorización de una sola ejecución; no se
reutilizará la aprobación consumida por r3. Se mantiene **NO-GO** para snapshot integrado,
`GO_LOCAL_PR` y `GO_DEVELOPMENT_REAL`.

## Segunda ejecución aislada — paquete r3 — 2026-10-08

El usuario aprobó una sola ejecución para el paquete
`/tmp/h3req1-helper-validation-29d8fff9-current-r3`, con manifiesto
`87389c0ee5c51052f32ce2fe63cef37d2c2a9782661bb689a40496ee207ad400`. Se verificaron las
13 entradas: todas coincidieron. La ejecución fue única, con timeout de 180 segundos,
contexto `default`, imagen inmutable anterior, `--pull=never`, `--rm`, red desactivada,
raíz de solo lectura, paquete montado solo lectura, UID 1001, capacidades descartadas,
`no-new-privileges`, límites de CPU/memoria/PID y `/tmp` efímero. Sin retry ni limpieza de
otros recursos.

Resultado: pytest **19 passed, 1 failed**; el helper devolvió
`socket-path-schema-or-canonicality` donde la regresión esperaba
`selected-and-canonical-socket-differ`. La regresión del proyector falló porque el fixture
concatenó el campo duplicado sin un salto de línea después de la sustitución de comando;
el parser no recibió dos registros separados. La regresión del scanner falló porque se
invocó `awk` con `--`, separador de opciones que no forma parte de la interfaz POSIX de
`awk`, por lo que no se imprimió el hallazgo redactado. La regresión del scope guard pasó:
`ordinary=3|newline=1|controls=1|malformed=3`. Resultado global **NO-GO**, exit 1. La
autorización r3 está consumida; no se repitió.

Comando ejecutado (el script entre comillas corrió dentro del contenedor):

```bash
timeout --foreground --signal=TERM --kill-after=5s 180s docker --context default run --rm --pull=never --network=none --read-only --user 1001:1001 --cap-drop=ALL --security-opt=no-new-privileges --memory=512m --memory-swap=512m --cpus=1 --pids-limit=64 --tmpfs /tmp:rw,noexec,nosuid,nodev,size=16m,uid=1001,gid=1001,mode=0700 --mount type=bind,src=/tmp/h3req1-helper-validation-29d8fff9-current-r3,dst=/validation,readonly --workdir /validation --env PYTHONDONTWRITEBYTECODE=1 --entrypoint bash sha256:29d8fff9a799aaacd45d771696f40762511d4c3a4c1ebfe536bd2a69a2f16be0 -euc 'sha256sum -c inputs.sha256 || exit 2; failed=0; python3 -m pytest -q -p no:cacheprovider tests/test_h3req1_c03_docker_daemon_identity_f2d.py tests/test_protected_workflow_review.py tests/test_security_flow.py::test_protected_path_guard_preserves_git_filename_boundaries tests/test_admin_invite_edge_contract.py::test_protected_h3_path_allowlist_is_narrow_and_covers_this_candidate || failed=1; bash tests/test_h3req1_c03_docker_inspect_projection.sh || failed=1; bash tests/test_scan_credentials.sh || failed=1; bash tests/test_protected_path_scope_guard.sh || failed=1; exit "$failed"'
```

## Diagnóstico y correcciones del siguiente ciclo

Se corrigió el chequeo de ruta F2d para aceptar una ruta seleccionada válida solo cuando
`realpath` coincide con la ruta canónica; una ruta distinta ahora produce el motivo de
socket diferente antes de leer metadata del peer. El test del comparador agrega el campo
duplicado como un registro separado. El scanner ya no usa `awk` para imprimir hallazgos:
escanea sin guardar la línea encontrada y emite solo una ruta sanitizada. Elimina también
las exclusiones de binarios/`.lock` y lee blobs directamente para tree/diff. Estas
correcciones son revisión estática; aún no están revalidadas en Docker.

La siguiente ejecución requerirá paquete nuevo, hashes actuales y aprobación humana nueva.
No incluye F2d contra F1, ShellCheck/actionlint, SQL/DB, recursos adicionales, limpieza,
red externa ni pruebas remotas. Incluso un PASS de helpers no acredita el snapshot completo,
smoke Pages/workerd, C03 integrado, UAT final, CI remoto, `GO_LOCAL_PR` ni
`GO_DEVELOPMENT_REAL`. F2d sobre F1 sigue sin JIT y las dos aceptaciones MEDIUM deben
recibirse de nuevo por separado.

Revisión independiente estática adicional: dos candidatos scanner MEDIUM (NUL/binary y
`++` en diff), corregidos en el worktree; y un candidato MEDIUM condicional de integridad
CI si las reglas de GitHub no requieren por separado el status `Protected Workflow
Integrity`. Las reglas activas no se inspeccionaron. La revisión BFF no halló candidato
plausible en su alcance. Al cierre inicial de esta nota, la revisión formal del diff para el snapshot
`codex-security-snapshot/v1:sha256:5429d4eeecd0cc1a5cb33f29abbfd7772b33eb07d3b249a5014bdf05b713c6e0`
estaba abierta; la actualización de cierre está en la sección siguiente.

## Revisión formal y paquete siguiente — 2026-10-08

La revisión formal terminó y quedó sellada como Codex Security scan
`de56da40-ee89-470f-ace5-b2a2b8a7f9e3`, sobre el snapshot
`codex-security-snapshot/v1:sha256:5429d4eeecd0cc1a5cb33f29abbfd7772b33eb07d3b249a5014bdf05b713c6e0`
y baseline `4eb4d877a50b012bb630a129bd0c74482c33be9c`. Revisó 51/51 elementos
del inventario y no registró hallazgos reportables confirmados. Los cuatro
candidatos quedaron diferidos, no descartados: enforcement independiente de
Protected Workflow Integrity, confirmación de email en Auth, host del PostgreSQL
del mock UAT y costo/límites de los eventos de revisión en CI. La cobertura es
parcial. El reporte no demuestra que no existan HIGH/CRITICAL fuera de los
hechos observables en ese snapshot ni resuelve las dependencias externas.

El cierre advierte que el árbol de trabajo cambió durante la revisión y que el
reporte corresponde al snapshot indicado. Por ello se conserva como evidencia
de ese snapshot; no se extiende automáticamente a ediciones posteriores.
El informe canónico y SARIF están en el directorio de la revisión bajo
`/home/romel/.codex/state/plugins/codex-security/scans/studiamatch-h3req1-sync-20261002/4eb4d877a50b012bb630a129bd0c74482c33be9c_20261008T160447Z_lhwksu8a/`.

### Paquete r4 verificado antes de su ejecución — corte histórico

Se preparó el paquete inmutable
`/tmp/h3req1-helper-validation-29d8fff9-current-r4`, cuyo manifiesto
`inputs.sha256` tiene SHA-256
`d915597d6eacb0a80e812e32c51b5c699ffb27e7c364501612cc576951404491`.
Las 13 entradas del manifiesto pasaron y sus hashes coinciden con las fuentes
actuales del candidato. Esto verifica identidad del paquete, no comportamiento.

La ejecución propuesta es una única invocación de 180 s, sin reintentos, sobre
la imagen local inmutable `sha256:29d8fff9a799aaacd45d771696f40762511d4c3a4c1ebfe536bd2a69a2f16be0`
y el contexto local `default` previamente confirmado. Dentro del contenedor:
verificar manifiesto, correr pytest de helper F2d, revisión de workflows, scope
guard y contrato de invitación; luego correr de forma independiente las
regresiones shell del proyector, scanner y scope guard aunque alguna falle.
El aislamiento propuesto usa `--pull=never`, sin red, raíz de solo lectura,
solo el paquete como montaje de solo lectura, UID 1001, capacidades descartadas,
límites de recursos y eliminación automática del contenedor. No se incluye
`.env*`, socket Docker, base de datos, F2d sobre F1 ni limpieza de recursos
existentes. En este corte histórico, la autorización r4 estaba pendiente y no había
resultado runtime. La ejecución posterior se registra al final de esta evidencia.

r4 no contiene `web/functions/_lib/admin-bff.ts` ni
`tests/h3_admin_bff_mock_uat.mjs`, por lo que su PASS no valida el nuevo cambio HMAC.
La UAT BFF se ejecutó por separado en el paquete r2 aprobado: 60 verificaciones y 10
casos de cuota PASS, exit 0. No acredita bindings remotos ni cierra G08; ver
[evidencia de acceso y ejecución BFF](h3req1_bff_validation_access_2026-10-08.md).

### Estado de gates

- La revisión estática formal está completa para su snapshot y conserva tres
  dependencias externas diferidas y cuatro candidatos de seguridad sin resolver.
- En este corte, r4 esperaba autorización nueva porque r3 ya estaba consumido; su resultado
  runtime posterior quedó registrado en la sección final.
- F2d contra el contenedor F1 exacto, lectura de metadata F1, stack local, smoke
  Pages/workerd, C03 integrado, UAT final 144/144, onboarding 10/10 y enforcement
  efectivo del CI siguen sin acreditarse en este ciclo.
- No se declara `GO_LOCAL_PR` ni habilitado el inicio de pruebas remotas
  Development. No se ejecutaron acciones remotas ni operaciones DB.

## Tercera ejecución aislada — paquete r4 — 2026-10-08

El usuario aprobó exactamente una ejecución de hasta 180 s para el paquete
`/tmp/h3req1-helper-validation-29d8fff9-current-r4`, manifiesto
`d915597d6eacb0a80e812e32c51b5c699ffb27e7c364501612cc576951404491`, e imagen local
`sha256:29d8fff9a799aaacd45d771696f40762511d4c3a4c1ebfe536bd2a69a2f16be0`. Antes de
ejecutar, se verificó el SHA del manifiesto y sus trece entradas. La única invocación usó
el contexto `default`, privilegio elevado del sandbox para el socket local, `--pull=never`,
`--network=none`, raíz de solo lectura, único montaje RO del paquete, UID 1001, capacidades
descartadas, `no-new-privileges`, 512 MiB, 1 CPU, 64 PIDs y `/tmp` efímero de 16 MiB.
No incluyó secretos, `.env*`, DB, socket dentro del contenedor, red, instalación, F2d/F1
ni limpieza de recursos existentes. El permiso r4 quedó consumido; no hubo retry. El
contenedor era `--rm`.

Comando único:

```bash
timeout --foreground --signal=TERM --kill-after=5s 180s docker --context default run --rm --pull=never --network=none --read-only --user 1001:1001 --cap-drop=ALL --security-opt=no-new-privileges --memory=512m --memory-swap=512m --cpus=1 --pids-limit=64 --tmpfs /tmp:rw,noexec,nosuid,nodev,size=16m,uid=1001,gid=1001,mode=0700 --mount type=bind,src=/tmp/h3req1-helper-validation-29d8fff9-current-r4,dst=/validation,readonly --workdir /validation --env PYTHONDONTWRITEBYTECODE=1 --entrypoint bash sha256:29d8fff9a799aaacd45d771696f40762511d4c3a4c1ebfe536bd2a69a2f16be0 -euc 'sha256sum -c inputs.sha256 || exit 2; failed=0; python3 -m pytest -q -p no:cacheprovider tests/test_h3req1_c03_docker_daemon_identity_f2d.py tests/test_protected_workflow_review.py tests/test_security_flow.py::test_protected_path_guard_preserves_git_filename_boundaries tests/test_admin_invite_edge_contract.py::test_protected_h3_path_allowlist_is_narrow_and_covers_this_candidate || failed=1; bash tests/test_h3req1_c03_docker_inspect_projection.sh || failed=1; bash tests/test_scan_credentials.sh || failed=1; bash tests/test_protected_path_scope_guard.sh || failed=1; exit "$failed"'
```

Resultado observado: manifiesto **13/13 OK**; pytest **20 passed**; proyector
`PASS|d4-tmpfs-shape=1|negative-controls=4|image-id=checked|schema=fail-closed`; scope
guard `PASS|ordinary=3|newline=1|controls=1|malformed=3`. La regresión scanner falló con
`scanner regression failed: grep I/O failure was accepted`. El proceso terminó exit 1 en
aprox. 1.2 s. Resultado de etapa **NO-GO**. No atribuir el fallo a las suites que sí
pasaron ni acreditar G03.

### Cuarta ejecución aislada — paquete scanner r5 — 2026-10-08

El permiso r5 fue distinto y posterior a r4. Se verificó el manifiesto
`cb7c08de62e03e640c8180c820011a3246d75efdd1fb13bc11b2d25675cca08f` y sus tres entradas,
y se ejecutó una vez con imagen fija, `--pull=never`, red desactivada, raíz de solo lectura,
un montaje RO, UID 1001 y límites aprobados. El contenedor se eliminó al terminar; no hubo
retry. La prueba terminó exit 1 con `scanner regression failed: grep I/O failure fixture
was not invoked`.

Esto demuestra que la inyección de fallo de la regresión no alcanzó el `grep` falso; por eso
el NO-GO r4 no acredita un defecto funcional del scanner. Se retiró el cambio de código
innecesario del scanner. La regresión ahora lo ejecuta con un entorno vacío, ruta explícita
al intérprete y PATH controlado; registra el uso del `grep` falso y exige exit 2. El paquete
r6 contiene README, scanner actual sin cambios y regresión actualizada. Su manifiesto se
verificó y tiene SHA-256
`b95a8bc84f017b48a4479121777f4e32ba620e681758c0f9f4f186aacfd18392`. r5 está consumido;
r6 aún no se ha ejecutado y necesita aprobación nueva.

La puntuación queda **20% -> 20%**, delta 0: ningún gate se cerró. G01/G02 continúan en
10 puntos cada uno; G03–G10, 0. BFF r2 permanece como evidencia parcial de G08. D01–D14
sigue 0/14. F2d/F1, la copia completa, Pages/workerd, C03 integrado, SQL, PR y remotos
continúan fuera de esta ejecución.

### Quinta ejecución aislada — scanner r6 — 2026-10-08

El usuario autorizó exactamente una ejecución de hasta 180 s del paquete
`/tmp/h3req1-helper-validation-29d8fff9-current-r6`, con manifiesto
`inputs.sha256` SHA-256
`b95a8bc84f017b48a4479121777f4e32ba620e681758c0f9f4f186aacfd18392` e imagen local
`sha256:29d8fff9a799aaacd45d771696f40762511d4c3a4c1ebfe536bd2a69a2f16be0`. Se verificó
el manifiesto 3/3 y se compararon los dos archivos de código con el candidato. La única
invocación usó `docker --context default run --rm --pull=never`, red desactivada, raíz de
solo lectura, único paquete montado en solo lectura, UID 1001, capacidades descartadas,
`no-new-privileges`, 512 MiB, 1 CPU, 64 PIDs y `/tmp` de 16 MiB montado con `noexec`.
No incluyó instalación, secretos, `.env*`, DB, servicios remotos, socket dentro del
contenedor, F2d/F1 ni limpieza de recursos externos. La autorización r6 quedó consumida;
no hubo retry.

Resultado: manifiesto **3/3 OK**; la regresión falló con
`scanner regression failed: grep I/O failure fixture was not invoked`; exit 1 en menos de
5 s. La revisión del comando y la fixture localiza la causa: el test creó el ejecutable
falso bajo `$test_root/fakebin`, donde `$test_root` vive bajo `/tmp`; el límite aprobado
monta `/tmp` con `noexec`. El kernel impide ejecutar ese archivo, Bash continúa la búsqueda
en `/usr/bin` y el marcador no se crea. Esto demuestra incompatibilidad entre la ubicación
del fixture y el aislamiento de r6; no confirma defecto del scanner.

Se corrigió únicamente la regresión para admitir un directorio de fixture ejecutable
separado, limitado a `/exec-fixture`, mientras deja marcador y scratch bajo `/tmp`. El
scanner no cambió. Se preparó el paquete r7:
`/tmp/h3req1-helper-validation-29d8fff9-current-r7`, manifiesto SHA-256
`c374f2d25a6faea9343b560bc27d400cd9ef82d2bc90e202327b54ccba1df95b`. Sus tres entradas
se verificaron y los dos archivos de código coinciden con el candidato. La única prueba
r7 propuesta requiere montar `/exec-fixture` como tmpfs ejecutable, con UID/GID 1001, y
pasar `SCANNER_TEST_EXEC_ROOT=/exec-fixture`; los demás límites siguen iguales. Esa
ejecución no está autorizada todavía. No se reutiliza r6.

El indicador permanece **20% -> 20%**, sin gate cerrado. G03 sigue abierto porque esta
regresión no obtuvo PASS y faltan linters/revisión completa; G04 también sigue abierto y
F2d no se ejecutó. D01–D14 remoto permanece 0/14.

### Séptima ejecución aislada — scanner r7 — 2026-10-08

El usuario autorizó una única ejecución de hasta 180 s, sin reintentos, del paquete
congelado `/tmp/h3req1-helper-validation-29d8fff9-current-r7`, con SHA-256 de
`inputs.sha256` `c374f2d25a6faea9343b560bc27d400cd9ef82d2bc90e202327b54ccba1df95b`.
Antes de ejecutar se confirmó el hash aprobado, los tres archivos del manifiesto y que
scanner y regresión coincidían byte a byte con el checkout. El permiso r7 quedó consumido.

La única invocación usó `docker --context default run --rm --pull=never` con imagen local
`sha256:29d8fff9a799aaacd45d771696f40762511d4c3a4c1ebfe536bd2a69a2f16be0`, red desactivada,
raíz de solo lectura, el paquete como único bind mount de solo lectura, UID/GID 1001,
capacidades retiradas, `no-new-privileges`, límites 512 MiB/1 CPU/64 PIDs, `/tmp` efímero
con `noexec` y `/exec-fixture` como tmpfs ejecutable de 1 MiB. Dentro se verificó el
manifiesto y se corrió solamente `bash tests/test_scan_credentials.sh` con
`SCANNER_TEST_EXEC_ROOT=/exec-fixture`. No hubo instalaciones, acceso a `.env*`, secretos,
DB, remotos, socket dentro del contenedor, F2d/F1 ni limpieza de recursos externos.

Resultado: las tres entradas del manifiesto **OK**; regresiones del scanner **PASS** con
`clean=1|text=1|binary=2|lockfile=1|plus-prefixed=1|newline-paths=3|io-failures=4|concurrent=2`
y `redaction=PASS`; exit 0 en menos de 5 s, sin retry. r6 queda como fallo histórico del
montaje `noexec`; r7 confirma la corrección de la fixture, no modifica el scanner.

Este ciclo sigue en **20% -> 20%**, delta 0: G03 vale 0 hasta completar linters y revisión
pertinentes; G04–G10 también valen 0. Se consumieron solo los permisos r7 ya descritos; no
se reutilizaron r4–r6 ni la autorización BFF r2. F2d/F1 y las etapas posteriores siguen
pendientes de sus gates y permisos separados. Development remoto permanece **0/14**.

## Revisión estática del snapshot y paquete r8 pendiente — 2026-10-08

### Revisión independiente

El Codex Security diff scan `2437a725-55cf-403d-8081-2c8f96520245` se completó sobre la
rama `feat/h3req1-sync-20261002`, baseline/HEAD
`4eb4d877a50b012bb630a129bd0c74482c33be9c`, snapshot
`codex-security-snapshot/v1:sha256:2f6b7c1204f9a7e3beb22543f02263a994ce304017705fb350526335179ace58`.
Se revisaron 51/51 filas. El resultado registró cero hallazgos reportables confirmados,
un candidato medio condicional y cobertura parcial. El candidato
`candidate-500f085f897ba6f7` describe que una edición maliciosa de `security-audit.yml`
podría quitar su dependencia del workflow confiable si las reglas remotas exigen solo
`security-audit`. Queda diferido hasta confirmar, mediante lectura aprobada, si las ramas
protegidas requieren por separado `Protected Workflow Integrity`. La observación CORS de
la Edge se suprimió: el código une las listas de origen, pero la revisión no encontró una
ruta navegador que exponga el JWT admin, y los valores remotos son desconocidos. El reporte
canónico está en
`/home/romel/.codex/state/plugins/codex-security/scans/studiamatch-h3req1-sync-20261002/4eb4d877a50b012bb630a129bd0c74482c33be9c_20261008T190200Z_dckntxfa/report.md`.

Es una revisión estática, sin pruebas, consultas remotas, secretos, DB ni despliegues. El
scan señala que el árbol de trabajo cambió durante la revisión; los cambios posteriores
fueron documentales y no sustituyen otra revisión de source. No acredita ausencia general
de riesgos, runtime, G03 completo, `GO_LOCAL_PR` ni aceptación Development remota.

### Paquete G03 r8 congelado

Paquete: `/tmp/h3req1-g03-validation-29d8fff9-r1`; `inputs.sha256` SHA-256
`6b3f3d856f906cb247b792a8d89d29f4abc0422c990fa473222b9dbe89097aee`, 71 entradas. El
paquete y los comandos están congelados. `run-r8.sh` es la invocación exacta, con límite
global de 180 s y sin reintentos. Primero valida el manifiesto y que `default` use un socket
Unix local; luego descarga dos assets de GitHub Releases a
`/tmp/h3req1-g03-validation-29d8fff9-r1.tools`, con TLS, timeout fijo y comprobación SHA-256:

- actionlint `v1.7.7`, archivo `actionlint_1.7.7_linux_amd64.tar.gz`, SHA-256
  `023070a287cd8cccd71515fedc843f1985bf96c436b7effaecce67290e7e0757`.
- ShellCheck `v0.11.0`, archivo `shellcheck-v0.11.0.linux.x86_64.tar.gz`, SHA-256
  `b7af85e41cc99489dcc21d66c6d5f3685138f06d34651e6d34b42ec6d54fe6f6`.

Después ejecuta un único `docker --context default run --rm --pull=never` con la imagen
local `sha256:29d8fff9a799aaacd45d771696f40762511d4c3a4c1ebfe536bd2a69a2f16be0`, red
desactivada, raíz y paquete en solo lectura, UID/GID 1001, capacidades retiradas,
`no-new-privileges`, 512 MiB, 1 CPU y 64 PIDs. Solo monta el paquete de 71 entradas y el
directorio de herramientas en lectura. Usa tmpfs `noexec` para scratch y tmpfs ejecutable
separado para las herramientas y el `grep` falso del scanner. Verifica que `package.json`
y `package-lock.json` coincidan con el manifiesto de dependencias de la imagen antes de
correr comandos.

Comandos interiores exactos: actionlint sobre `security-audit.yml`,
`protected-workflow-integrity.yml` y `db-sync-to-pro.yml`; ShellCheck sobre los siete
scripts que declara CI; `npm run lint`; `./node_modules/.bin/tsc --noEmit`; pytest de
`tests/test_protected_workflow_review.py`; `bash tests/test_scan_credentials.sh`; y
`bash tests/test_protected_path_scope_guard.sh` con el fixture ejecutable separado. Las
pruebas se ejecutan sin red. No instala paquetes npm ni herramientas en la imagen, no
accede a `.env*`, secretos, SQL/DB, servicios remotos ni socket Docker dentro del contenedor;
no inspecciona ni limpia recursos Docker existentes. El permiso de ejecución r8 **está
pendiente**; si llega, se verificará el manifiesto y que no se haya consumido antes de la
única invocación.

### Tablero tras este ciclo

G01 10%, G02 10%; total **20% -> 20%**, delta 0 porque no se cerró ningún gate. G03 sigue
en 0 hasta validar el paquete de linters/regresiones y cerrar su revisión de herramientas.
G04–G10 siguen en 0. r4–r7 y BFF r2 están consumidos; r8 aún no autorizado/ejecutado.
Development remoto D01–D14 permanece 0/14. No se ejecutó F2d contra F1, copia completa,
smoke Pages/workerd, C03 integrado, SQL, push, PR ni despliegue.

## Escalación de r8 rechazada antes de ejecutar — 2026-10-08

Se solicitó al entorno autorización elevada para invocar una vez el runner congelado
`/tmp/h3req1-g03-validation-29d8fff9-r1/run-r8.sh`, manifiesto SHA-256
`6b3f3d856f906cb247b792a8d89d29f4abc0422c990fa473222b9dbe89097aee`, límite 180 s y sin
reintentos. auto_review rechazó la operación porque la aprobación humana recibida cubría r7,
no el paquete r8 exacto. El rechazo ocurrió antes de iniciar el proceso: no hubo descargas,
verificación Docker ni creación de contenedor. La carpeta de herramientas quedó vacía y r8
permanece congelado. Esto es un rechazo del control automático, no una respuesta del usuario;
no consume autorización de r8 ni habilita un intento alternativo. Se requiere aprobación
humana exacta antes de volver a solicitarlo.
Se mantuvo la espera solicitada durante 30 minutos, hasta 2026-10-08 20:05:36 UTC. No llegó
respuesta; la aprobación r8 queda pendiente. La ausencia no se interpretó como aprobación
ni rechazo. Punto de reanudación: verificar que el usuario autorice exactamente este
paquete antes de volver a solicitar el acceso elevado; si lo autoriza, comprobar de nuevo
el manifiesto congelado y ejecutar una sola vez `run-r8.sh`, sin retry. Si la aprobación no
llega, continuar detenido en G03 y no abrir F2d contra F1.

El estado acreditado sigue en **20% -> 20%**, delta 0; G03 no cierra. r4–r7 y BFF r2 están
consumidos, r8 está pendiente y D01–D14 permanece en 0/14. El JIT F2d r2 sigue listo con
manifiesto 17/17, pero su ejecución de host y lectura allowlisted de F1 requieren aprobación
separada y aceptación expresa de los dos riesgos MEDIUM que ya detalla su manifiesto.

## Ejecución autorizada r8 y corrección de paquete r9 — 2026-10-08

El usuario autorizó una sola invocación de hasta 180 segundos y sin retries de
`/tmp/h3req1-g03-validation-29d8fff9-r1/run-r8.sh`, con SHA-256 de `inputs.sha256`
`6b3f3d856f906cb247b792a8d89d29f4abc0422c990fa473222b9dbe89097aee`, las dos descargas
fijadas y un contenedor local fijado. Antes de ejecutar, el SHA del manifiesto coincidía y
`sha256sum -c inputs.sha256` verificó las 71 entradas. El directorio de salida estaba vacío.
La escalación se solicitó para la ruta exacta autorizada.

Resultado consumido: **NO-GO, exit 126**, dentro del límite de 180 s. El wrapper verificó hashes, confirmó que
el contexto `default` exponía un endpoint `unix://`, descargó actionlint 1.7.7 y ShellCheck
0.11.0, y ambos archivos pasaron la verificación SHA-256. El contenedor fijado se invocó
con `--pull=never --network=none --read-only --user 1001:1001`, sin socket montado dentro.
Al intentar iniciar la orden interior, Bash devolvió `run-in-container.sh: Permission
denied`. Ninguna de las herramientas, ESLint, TypeScript, pytest ni las regresiones se
ejecutó; por tanto no hay resultado PASS/FAIL de esos checks.

La causa quedó demostrada por metadata observada después del intento: la raíz
`/tmp/h3req1-g03-validation-29d8fff9-r1` era `0700`, owner UID/GID `1000:1000`; el script
interior era `0755` y el contenedor ejecutaba como UID/GID `1001:1001`. El usuario del
contenedor no podía atravesar la raíz del bind mount para abrir el script. No se atribuye
el fallo a scanner, mount de la aplicación, ownership de los fixtures ni contenido de
imagen. Docker `--rm` retiró solo el contenedor de esta invocación; no se inspeccionaron ni
limpiaron recursos preexistentes. Los tarballs verificados permanecen en el directorio de
salida creado por esta autorización.

La ejecución verificó que el endpoint Docker comenzaba con `unix://`; eso no prueba la
identidad del peer dockerd. F2c ya había quedado NO-GO sin demostrar el peer. Esta ejecución
no se presenta como prueba de identidad del daemon ni de ausencia de proxy/remoto. No se
ejecutará otra operación Docker hasta resolver ese prerrequisito por F2d autorizado o una
alternativa local concreta aprobada.

### r9 preparado, no ejecutado

Se preservaron r8 y su evidencia. Una copia nueva de los mismos 71 inputs quedó en
`/tmp/h3req1-g03-validation-29d8fff9-r2`, raíz `0755`; sus archivos y la sintaxis Bash del
wrapper se validaron sin ejecutar suites. `inputs.sha256` conserva el digest
`6b3f3d856f906cb247b792a8d89d29f4abc0422c990fa473222b9dbe89097aee`. El manifiesto completo
de paquete r9 tiene digest
`b2020404af4ae373907cab6bd777fba2bd397d8b5677c874aaa72bc34083d866`; `run-r9.sh` tiene
digest `2a38e3038440d7b6e6a5c77871eae88f2adba03bf44abca79b76175015eedb97`. Los dos tarballs
de r8 se copiaron localmente, sin nueva descarga, y sus hashes volvieron a coincidir con
los pins. El JIT r9 fija un único contenedor de hasta 180 segundos, egress cero dentro,
stop-on-failure y sin retry; está pendiente de la identidad del daemon y de aprobación
humana nueva. Su SHA-256 es
`49502617f2bb788b2e9664e659c3f9dd4fe3dc84188ee0b5d86e2909c3dadedf`. Ver
[JIT r9](../operaciones/manifiesto_jit_h3_g03_local_validation_r9_2026-10-08.md).

Impacto: ningún contrato, fuente de producto, SQL, recurso cloud o recurso Docker existente
cambió. r8 está consumido, r9 no está autorizado. G03 sigue abierto y el avance acreditado
permanece **20% -> 20%**; no se heredan permisos de r4–r8.
