# G06 Pages/workerd S14 — causa demostrada: snapshot omitió imports relativos

Fecha: 2026-10-10. Candidato: `feat/h3req1-sync-20261002` /
`4eb4d877a50b012bb630a129bd0c74482c33be9c`. S14 ejecutado una vez y NO-GO;
S17 snapshot correctivo preparado bajo revisión independiente.

## Evidencia de partida

S13 ejecutó una vez y salió 1 en `one-shot-pages-workerd-runtime-diagnostic`.
El runtime Pages/workerd tuvo `ERR_MODULE_NOT_FOUND`, `healthz=NO-GO` tras dos
consultas y `OOMKilled=false`. El sanitizador confirmó su contrato, pero el
clasificador produjo `runtime-missing-module=unclassified|from=other`; el
mensaje y el specifier crudos no se guardaron. Contenedor fallido preservado:
`h3req1-c03-startup-runtime-20261010-s13`, ID
`fdb48dc98b01d6bc413be83bea30c06a49eebb963cc8da03083f1ce77c2f21e5`, exit 1,
red interna S11, filesystem root read-only y cinco mounts read-only. Evidencia:
[resultado S13](h3req1_c03_startup_smoke_2026-10-10_s13_diagnostic.md).

La metadata estructurada del contenedor confirma la identidad y labels fijados.
No se inspeccionaron `Env`, logs crudos ni objetos completos. La evidencia no
demuestra que falte una dependencia ni que Docker esté defectuoso.

## Resultado real S14 y reproducción mínima

S14 pasó preflight y sintéticos, pero salió 1 en
`one-shot-pages-workerd-runtime-diagnostic`: healthz NO-GO tras dos consultas,
`ERR_MODULE_NOT_FOUND`, exit 1 y sin OOM. La salida cerrada fue
`runtime-missing-module=relative-module|from=candidate-tests` y
`runtime-missing-module-shape=module-import`. El contenedor S14 se conserva por
ID `5243c9e452f397f8194501418c897905ac43fda9c298479eaff6d2756a748f5c`; el
filtro dio exit 0 y recovery registró que no se requería stop porque estaba
exited. [Evidencia S14](h3req1_c03_startup_smoke_2026-10-10_s14_diagnostic.md).

La comparación acotada de imports relativos de los 13 sources S16 halló tres
destinos que existen en el candidato pero no en el snapshot:
`tests/h3req1_c03_login_result.mjs`,
`tests/h3req1_c03_safe_postgrest_error_code.mjs` y
`tests/h3req1_c03_replay_state_diagnostic.mjs`. `cache_digest.mjs` sí estaba en
ambos. El orden del runtime muestra que `login_result.mjs` es el primer destino
relativo no-cache presente; una importación aislada del snapshot S16 devolvió
`ERR_MODULE_NOT_FOUND` para ese archivo. No se consultaron logs crudos. Esto
demuestra una omisión de cierre transitivo del snapshot, no una falla de Docker
ni un defecto en los módulos del producto.

## Cambio diagnóstico mínimo

El clasificador anterior reconocía módulos faltantes solo cuando el mensaje
contenía una forma más estricta. Los helpers actuales reconocen las formas
cerradas `package-import`, `package-no-importer`, `module-import`,
`module-no-importer`, `message-empty`, `other-message` y `not-applicable`.
También clasifican importadores `file://` y raíces allowlisted del candidato;
specifier/importador arbitrario no se emite. El evento registra una categoría
cerrada junto al ID ordinal del lockfile y origen enumerado. El filtro rechaza
valores fuera de allowlist y líneas contaminadas. Fue instrumentación para
identificar la forma real; la causa ahora está demostrada por snapshot, import
graph y resolución de Node.

Una aserción sintética falló porque el fixture usó `errorType=ERROR`, valor que
no pertenece a la allowlist de tipos Node; se corrigió el fixture a `Error`, la
clase real esperada. No cambió el comportamiento del runtime. El fallo no se
ocultó: después de corregir la entrada sintética, se volvieron a ejecutar los
tres helpers.

## Validaciones reproducibles completadas

- Imagen Node fijada `node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844`,
  `--network none`, root filesystem read-only y tres mounts read-only:
  `node --check` + preload self-test, probe self-test y filtro self-test:
  3 fases PASS.
- ShellCheck 0.11.0 fijado, red none y mounts read-only: runner S14, recovery
  self-test y filtro PASS; `bash -n` PASS.
- Recovery self-test S14 evalúa la función real del runner con Docker simulado:
  9 casos PASS, incluidos estado desconocido, reinspección fallida, ownership
  cambiado y runtime aún activo después de stop; no invoca Docker.
- Sidecar S14 verifica 16 inputs con SHA-256; todos PASS. No contiene el runner
  S14, evitando hash circular; el runner fija el sidecar SHA
  `e787a7cd371b2f5705646ef6b5322d3562d8bc6c401079bfefc9bef32d3555eb`.
- Filtro: caso permitido `package-no-importer` y caso con token sintético
  descartado; salida PASS. `git diff --check` se ejecutará al cerrar el paquete.

## Alcance S14 ejecutado

Runner `tests/h3req1_c03_startup_runtime_diagnostic_s14.sh`, SHA-256
`fc67fce4b7ba6851c9590bed8d01c17a490b8edc575c40fdc7c71ba332b92ff4`, consumió
una invocación Pages/workerd con snapshot S16 y dependencias S11 fijados;
timeout 180 s, 2 CPU/2 GiB, red internal existente, source/dependencies
read-only, sin secretos, `.env*`, DB, PostgREST, Edge, Auth, SQL, egress ni
checkout original. No hace pull/build/retry. El paquete clasifica y conserva
solo salida allowlisted. Ante NO-GO conserva el contenedor S14 propio y no
avanza a G07; ante healthz PASS retira solo el runtime S14 exacto después de
verificar su identidad, preservando volúmenes y red.

Inputs S14: sidecar SHA
`e787a7cd371b2f5705646ef6b5322d3562d8bc6c401079bfefc9bef32d3555eb`. Incluye helpers actuales,
manifest/snapshot S16, inputs y evidencia S11/S12/S13, y self-tests de recovery.
Runner SHA se valida por separado. El cambio S13→S14 se limita a identidad del
runtime/evidencia, clasificación de la forma y verificación del precedente S13.

## Recursos y gates

`studiamatch-dev` continúa como entorno normal; no se reinició ni modificó.
Permanecen preservados S11 (holder, volúmenes de dependencias y red interna),
snapshots S16 y runtimes fallidos S12/S13/S14. No se retiraron contenedores ni
volúmenes.

G05 se reabre: la verificación 13/13 de S16 fue correcta para su manifest, pero
el manifest omitía tres imports relativos requeridos por runtime. G06 sigue
pendiente. Hasta que S17 pruebe cierre transitivo: histórico G01–G10 40%; cierre
local G01–G09 4/9 = 44.44%, frente al inicio del ciclo 50% y 5/9 (delta temporal
-10 pp / -11.12 pp). Implementación local parcial no suma puntos.
La autorización humana del 2026-10-10 cubre este ciclo local; no habilita
operaciones remotas.

La revisión independiente S14 fue PASS estático; su hallazgo LOW se resolvió
ampliando el self-test de recovery a nueve ramas. El runner correctivo S17 y su
self-test de recovery (13 casos) pasaron revisión independiente estática; G05
espera la ejecución del snapshot. Pines y límites están registrados en
[preparación S17](h3req1_c03_source_snapshot_s17_preparation_2026-10-10.md).

S17 cerró con exit 0: 17 archivos allowlisted, 16 fuentes; productor,
receptor, filtro y verificador 0. G05 queda completo. Siguiente paso:
preparar y revisar Pages/workerd S15 contra el volumen S17, con contenedores
S14/S13 preservados. Edge/PG17/PostgREST esperan healthz PASS.
