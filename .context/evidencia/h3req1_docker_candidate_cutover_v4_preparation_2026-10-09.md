# Preparación del cutover Docker V4 — reutilización de la imagen candidata — 2026-10-09

## Tareas y gates

1. Resolver el cutover fallido a `studiamatch-dev` sin repetir build/pull: solo pasa con
   identidad del runtime, manifiestos compatibles y health `healthy`.
2. Preservar rollback, el runtime R4 fallido y volúmenes. Solo después de guardar evidencia y
   health PASS retirar los contenedores/redes históricos exactos autorizados en el nuevo JIT.
3. Tras cutover, ejecutar r9, copia íntegra aislada, Pages/workerd, integración Edge/PG17/
   PostgREST, C03 integrado y aceptación. Ninguna suite corre en este paquete.

## Impacto y lectura puntual del entorno

- Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
  `feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`. El estado de
  trabajo conserva 55 tracked modificados y 267 entradas untracked en esta preparación; no hay
  staged. El original permanece en `/home/romel/src/studiamatch`, rama
  `feat/h3req1-development-remote-tests`, HEAD `7650093b05a820e8e6faf9ec711e12fab8b50398`, WIP
  39/39/0.
- El contenedor original `studiamatch-dev`, ID
  `115d4041bf3f23a5fcb109a4a33bf3a9abf038e72655040f676aa5cb0c89a68a`, estaba `restarting`,
  exit 1, reinicio 78, imagen `studiamatch-dev:local`, policy `unless-stopped`; bind del checkout
  original a `/app` y `studiamatch_node_modules` en `web/node_modules`. La cantidad de reinicios
  es una lectura puntual y no se fija en el JIT.
- `studiamatch-node-deps`, ID
  `20f9f5a75ebce7fb7f890f50577a00edb8fb29f0c15b928bffd3f08414c21e16`, estaba `exited` y usa la
  imagen vieja; pertenece al Compose del checkout original y se conserva. No existe
  `studiamatch-h3req1-node-deps`, volumen `studiamatch_h3req1_node_modules` ni red
  `studiamatch-h3req1_default`.
- La imagen candidata `studiamatch-h3req1:20261009-v3` existe local con ID
  `sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63`. Build/smoke V3
  pasaron. La ejecución V3 falló porque faltó `.env.local` en el checkout candidato; el rollback
  restauró el original y el cleanup no se alcanzó. El candidato no tiene ese archivo; el del
  checkout original existe y es legible. No se inspeccionaron sus valores.
- La nueva composición dirige solo `app` al `.env.local` de desarrollo normal, con el binding
  loopback. El candidato `node-deps` solo monta package/lock read-only y el volumen candidato
  independiente. El inicializador copia la dependencia ya staged en la imagen y no ejecuta
  `npm ci`. El `app` recibe el env_file normal al iniciar; Codex no carga, imprime, copia ni
  versiona los valores.
- Docker Compose local es V5.5.1; su ayuda confirma `up --no-build` y `--pull
  always|missing|never`. El JIT fija `--pull never`. El bridge normal permite egress, pero no se
  solicitan descargas ni llamadas remotas; el healthcheck consultado es local. Si luego se usan
  rutas integradas, podrían conectar a servicios configurados en el env_file; eso no queda
  cubierto por esta invocación.

## Cambios del paquete y revisión

- El override V4 conserva el tag/digest construidos, da un nombre propio al `node-deps`, cambia
  el volumen al nombre nuevo `studiamatch_h3req1_node_modules`, publica `127.0.0.1:3000` y
  sustituye `env_file` relativo ausente por la ruta absoluta ya existente del checkout original.
  `node-deps` mantiene binds read-only únicamente para los manifests.
- El runner no hace build, pull, install, push, deploy ni SQL. Comprueba hashes, candidate
  identity/WIP, imagen, volumen/red/nombres ausentes, montajes y `docker compose config --quiet`.
  El cutover guarda fases sanitizadas; valida image digest, tag, labels, montajes, servicio de
  provisión `exited/0` y health. El rollback solo mueve recursos cuya identidad y montajes
  coinciden.
- Se preserva el contenedor original renombrado como rollback, el contenedor R4 fallido
  `b8aff87745e80a82265be0019be5530e9173fc621ab3ff47754f85e933a1508f`, seis volúmenes R4/R5,
  las redes Edge/Data R4, el volumen original y todas las imágenes. No hay prune ni borrado de
  volúmenes. Tras health PASS, el JIT permite retirar solo 11 IDs históricos y 3 redes internas
  vacías; las redes y contenedor R4 se excluyen.
- La evidencia de salida se crea durante la invocación antes de cualquier cleanup, con líneas
  fase/código y exit. Si falla health, el cleanup histórico se omite y se restaura el original.
  Si falla el cleanup después de health PASS, el candidato permanece activo y el rollback sigue
  disponible.
- `bash -n` del runner V4: PASS. `git diff --check` de runner/override: PASS. La revisión
  mecánica confirmó las llamadas `--no-build --pull never`, ausencia de `BUILD_CONTEXT`,
  `INPUT_MANIFEST`, `docker volume rm`, `docker image rm`, `docker rm -v` y prune. El SHA del
  ejecutable y su igualdad con el pin del paquete se vuelven a comprobar antes de pedir
  aprobación.

## Permiso y gates

El JIT V3 anterior está consumido; no se reutiliza. El V4 concreto está en
[`JIT cutover V4`](../operaciones/jit_h3req1_docker_candidate_cutover_v4_once_2026-10-09.md),
SHA-256 `4753244a0eacc25714455c9d0053e58de05b7d9bad64c7cb8c97a60ce39ac56f`. Requiere
aprobación nueva para una invocación que incluye el runtime regular cargando el env_file
existente y la limpieza selectiva condicionada a PASS.

El paquete recibió aprobación humana para una invocación y se consumió con exit 1 en
`phase=candidate-wip|error_code=STATUS_DRIFT`, antes de cualquier llamada Docker. El JIT exige
WIP `55/268/0` después de crear su log, pero `*.log` está ignorado por Git y el conteo real siguió
en `55/267/0`. No se reintenta con este JIT; se necesita una revisión corregida y aprobación
nueva. Resultado y hashes quedan registrados en el log JIT y en la evidencia viva PG17/npm. No
suma porcentaje. G01 0/10; G02 10/10
por el corte separado C03 SQL v3 41/41; G03 0/10; G04–G10 0/10. Total 10%, delta 0. No hay
`GO_LOCAL_PR` ni `GO_DEVELOPMENT_REAL`.

## V5 preparado tras `STATUS_DRIFT` V4 — 2026-10-09

El V4 consumido esperaba 55/268/0 después de crear el log, pero `*.log` está ignorado. Se
detuvo antes de Docker con 55/267/0. V5 mantiene intacta la secuencia, recursos, imagen, override,
healthcheck y rollback; su único delta ejecutable contra V4 cambia el destino del log al nombre
V5. La condición sigue `55/268/0`, válida porque el nuevo JIT markdown agrega el registro que
faltaba en `.context/operaciones`; el log V5 también será ignorado. La WIP actual es 55/268/0.

Runner V5: `tests/h3req1_docker_peer_substep_diag/docker_candidate_cutover_v5.sh`, SHA-256
`a36a06f976c835a38796fb68e165e24ede3ed2de583443ad79d0f1644d775ba0`. JIT
`operaciones/jit_h3req1_docker_candidate_cutover_v5_once_2026-10-09.md`, SHA-256
`b5c38e3e149402ab46dec17b1c49ff5b18d5a5a6495a631ed79a229148209b73`. `bash -n`, diff mecánico
(solo ruta del log), orden rollback/cutover/health/cleanup, límites de mutación y WIP actual pasan.
Al cierre de esta preparación original, el ejecutor aún estaba pendiente; el resultado de la
invocación aprobada se conserva en la sección siguiente.

## V5 ejecutado — candidato saludable; cleanup bloqueado por un mapa histórico — 2026-10-09

La aprobación V5 quedó registrada y se consumió una sola vez. JIT SHA-256
`b5c38e3e149402ab46dec17b1c49ff5b18d5a5a6495a631ed79a229148209b73`; runner SHA-256
`a36a06f976c835a38796fb68e165e24ede3ed2de583443ad79d0f1644d775ba0`. La invocación fijada
terminó exit 1 con estas fases sanitizadas:

```text
phase=candidate-wip|error_code=OK
phase=preflight|error_code=OK
phase=cutover|error_code=COMMANDS_OK
phase=candidate-health|error_code=OK
phase=cutover-complete|error_code=OK
phase=cleanup-preflight|error_code=VOLUME_MAP_MISMATCH
phase=historical-cleanup|error_code=COMMAND_FAILED
phase=runner-exit|error_code=EXIT_1
```

La secuencia del runner ubica toda llamada `docker rm`/`docker network rm` después del éxito de
`cleanup-preflight`. El gate falló antes de esa sección, por lo que no se borró ninguno de los 11
contenedores ni las tres redes fijadas. El runtime candidato quedó activo y healthy; una lectura
posterior de campos acotados confirma ID `500931b0f086d29ec9e751e1fd652f9b7ccd357f3eb64daa8751344776162049`,
imagen `studiamatch-h3req1:20261009-v3`, bind del checkout candidato en `/app` y volumen nuevo
`studiamatch_h3req1_node_modules`. El provisionador terminó exit 0. El original se renombró y
preservó como `studiamatch-original-dev-20261009`, con su checkout y volumen originales.

### Causa mínima demostrada

El primer mapa que no coincide es el contenedor histórico
`d6a26afbaf943b58d6f0f529331139dad4efff47f2509371229f817b03e0c929`. El runner fijaba el volumen
`h3req1-c03-integrated-source-snapshot-20261006-r4` en `/source` como `RW=true`; la consulta Docker
read-only devuelve `RW=false`. Los mapas previos del provisionador Miniflare y Pages coinciden;
los mapas restantes consultados también muestran los valores fijados. La discrepancia es del
predicado del runner y no demuestra defecto de producto, volumen o Docker. La condición observada
es más restrictiva (read-only), así que la corrección mínima es cambiar solo ese valor esperado a
`false`, conservando intactos el ID, los otros cinco mounts, los controles R4, las listas de
cleanup y el rollback.

La proyección inicial de inventario del runtime devolvió un error de formato que el fallback
clasificó como `RESOURCE_NOT_FOUND`; no se usó como evidencia de ausencia. Una proyección simple
corregida confirmó el runtime y sus mounts. No se leyó Env ni otro campo de secretos.

El candidato saludable no cierra G03 ni integración. El runtime habitual quedó simplificado, pero
G03 sigue 0/10 porque r9 y el tooling completo están pendientes. G01 sigue 0/10; G02 conserva 10/10
solo para C03 SQL v3 41/41; G03–G10 siguen 0/10. Total 10%, delta 0. V5 está consumido y no se
reintenta. V6 preparado corrige únicamente `RW=true` a `RW=false`; su runner de limpieza se
ejecutará solo con una autorización nueva. Runner SHA-256
`37386e4a640618356f7cea8ac630ae298e8537380680255e4a4105e127214e63`; JIT SHA-256
`efcce4f8e762264a41b766904c0e4f1aaa3d4d4023ff3a289a80d761d62acdd9`. `bash -n`, pins y orden
estático PASS; V6 todavía no ejecutado.

## Revalidación focal del paquete r9 antes de retomar G03 — 2026-10-09

El paquete externo `/tmp/h3req1-g03-validation-29d8fff9-r3` conserva sus checksums internos:
71 inputs y manifests pasan. Al compararlo solo contra las rutas del manifiesto en el checkout
vigente, 64 coinciden, 4 difieren y 3 son helpers del paquete sin ruta fuente en el checkout.
No se ejecutó r9.

Las cuatro diferencias son concretas: (1) `protected-workflow-integrity.yml` incluye el evento
`edited`; (2) `protected_workflow_review.py` incluye `.github/scripts/` y requiere account type
`User`; (3) `test_protected_workflow_review.py` cubre el scope nuevo, bots y reviewer type ausente;
(4) `next-env.d.ts` referencia `./.next/dev/types/*`. Las primeras tres modifican cobertura y
comportamiento del gate CI independiente; la cuarta afecta el typecheck r9. El paquete r3 no
representa el candidato actual; conservarlo byte por byte y preparar un paquete separado antes de
autorizar r9. La evidencia histórica de r8/r9 queda intacta.

Se preparó un paquete r4 externo y separado en `/tmp/h3req1-g03-validation-29d8fff9-r4`, sin
modificar r3. Las cuatro rutas fueron copiadas del checkout actual; las 71 rutas mantienen
integridad y la comparación contra fuentes actuales queda en 68 coincidencias, 0 drift y 3
helpers package-only. El wrapper de ejecución está en
`tests/h3req1_docker_peer_substep_diag/run-r9-r4-candidate-image-sanitized.sh`, SHA-256
`13b6310a2eaaeab1dda49d5bf645c26c9f677c9a468b31242764b2c15761d00e`. `bash -n` para wrapper e
inner runner, manifests y revisión estática de `network=none`, root filesystem/inputs/dependency
volume read-only, `--pull=never`, capacidades vacías y recursos acotados pasaron. Usa la imagen
candidata V3 fijada y el volumen de dependencias en solo lectura; no monta checkout, `.env*` ni
secrets, no instala npm y no accede al daemon desde dentro. Al comprobar el input `next-env.d.ts`
se encontró que sus `.next/dev/types` referidos no están en el checkout; el r4 inner runner ahora
ejecuta `next typegen` dentro del scratch antes de `tsc`, sin escribir al candidato. Next fijado
16.3.8 documenta ese comando para generar tipos sin `next build` y advierte que carga la
configuración [Next CLI](https://nextjs.org/docs/app/api-reference/cli/next). Package manifest
SHA-256 `ca30a43c990e45e634412219c9a28d964b410068671c499048e80f2ff8c9068b`; wrapper actualizado
SHA-256 `13b6310a2eaaeab1dda49d5bf645c26c9f677c9a468b31242764b2c15761d00e`. r9 no se ejecutó;
la solicitud JIT nueva aún requiere aprobación independiente.

## Resultado de limpieza Docker V6 — 2026-10-09

El JIT V6 fue aprobado y consumido una vez. Resultado exit 1:
`candidate-wip|OK`, `cleanup-preflight|CONTAINER_MISMATCH`, `runner-exit|EXIT_1`. El código
proviene de la comparación común de las once tuplas de identidad/estado; la salida no conserva
ordinal ni campo, por lo que la discrepancia vista durante el JIT no se puede reconstruir. Una
consulta read-only posterior de esos once IDs y seis campos estructurados encontró todas las
tuplas actuales iguales a los valores esperados; no identifica ni explica el valor observado
antes. No se infiere una carrera ni un defecto del runtime.

Por orden del runner, todos los `docker rm` y `docker network rm` ocurren después de
`cleanup-preflight|OK`. Esa fase no se emitió; no hubo eliminación de contenedores, redes,
imágenes o volúmenes. No se ejecutó un retry. Candidato/rollback fueron validados antes de
entrar en la fase que falló. Se preservó el log sanitizado exacto en
`.context/evidencia/h3req1_docker_candidate_cleanup_v6_once_2026-10-09.log`. El total se mantiene
en 10%, delta 0.
