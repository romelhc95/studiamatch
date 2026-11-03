# G07 R10 — preparación de diagnóstico PostgREST/PG17

## Continuación vigente — R12 ejecutado y corrección mínima preparada para R10 (2026-10-10)

- Candidato: `feat/h3req1-sync-20261002` / baseline `4eb4d877a50b012bb630a129bd0c74482c33be9c`;
  WIP 55 tracked modificados / 4431 untracked / 0 staged. Checkout original intacto.
- R12 V2 terminó exit 0 como diagnóstico, no como PASS del runtime: manifest/inputs 4/4,
  R9 snapshot 64/64 + dos extras históricos, PG17.11, tres SQL fixtures y TCP/auth antes/después
  PASS. Prerrequisito `EXTENSIONS_SCHEMA_ABSENT`; `--dump-schema` devolvió
  `SQLSTATE_3F000`, exit 1, cuerpo limitado a 8192 bytes. Cleanup por ID de dos contenedores y
  red interna exactos; sin Edge ni logs crudos. Evidencia
  [R12 V2](h3req1_c03_integrated_diagnostic_r12_schema_dump_v2.txt), SHA-256
  `d3136b0fad548608f5dc755f75bdea9b3fa5041ebd5624d073ed436acfd981b7`.
- Corrección: se añadió `tests/sql/h3req1_c03_integrated_extension_setup_r10.sql` con
  `CREATE SCHEMA IF NOT EXISTS extensions AUTHORIZATION postgres;` en la base desechable, según
  el campo ausente que observó R12 y la configuración `PGRST_DB_EXTRA_SEARCH_PATH=public,extensions`.
  Los fixtures y manifiesto históricos R9/R6 se preservaron; el R9 manifest original quedó
  archivado sin cambio en `h3req1_c03_integrated_manifest_r9.sha256`.
- R10 reemplaza runner, contrato y fixture SQL; 61/64 pins previos permanecen idénticos y el
  nuevo manifest verifica 64/64. Bash syntax y contrato 12/12 en Node fijado, network none y
  tests mount read-only; ShellCheck oficial 0.11.0 y `git diff --check` PASS. Revisión
  independiente estática PASS sin blockers. Evidencia estática
  [R10](h3req1_c03_integrated_r10_static_validation.txt), SHA-256
  `ccdab4645bc187729f3ec8001fa2443e54f11f55ffc64e551aef46e849d45664`; ShellCheck
  [R10](h3req1_c03_integrated_r10_shellcheck.txt), SHA-256
  `dc39e8e043b102865371a5a2245f3a8340a6605255c08bb4e44b31da2414c17a`.
- Docker activo: Docker Desktop local/context `default`; `studiamatch-dev` healthy
  (`studiamatch-h3req1:20261009-v3`); startup holders S2/S3 activos. R10 usa nombres/IDs nuevos,
  imágenes locales fijadas, servicios sintéticos aislados y cachés R4 read-only; R9 snapshot
  queda preservado. No se usan `.env*` ni credenciales operativas.
- Gate G07 sigue parcial; sin puntos nuevos: histórico G01–G10 60%, cierre local G01–G09 6/9.
  Resultado integrado R10 pendiente; ejecutar solo tras revalidar su manifest y recursos exactos.

## Continuación R12 — preparación estática (2026-10-10)

- Candidato: rama `feat/h3req1-sync-20261002`, HEAD baseline
  `4eb4d877a50b012bb630a129bd0c74482c33be9c`; WIP observado 55 tracked modificados,
  4423 untracked, 0 staged; checkout original intacto.
- R11 acreditó PG17.11, fixtures SQL y TCP/auth, mientras PostgREST 14.0 seguía
  `HTTP_503_PGRST002`; R12 conserva PostgREST 13.0.7 e invoca su CLI `--dump-schema` una
  vez. La documentación oficial v13 especifica que el comando devuelve el schema cache en JSON.
  R12 no inicia Edge ni expone el JSON.
- El helper limita la captura a 64 KiB iniciales + 64 KiB finales, exige marcador de exit con
  nonce y solo emite fase/código/bucket. Los tests CLI cubren salida sanitizada y nonce incorrecto;
  exit 137 se clasifica `PROCESS_KILLED`.
- Node fijado en contenedor efímero `network=none`, rootfs read-only: 11/11 sintéticos PASS.
  `bash -n`, ShellCheck oficial 0.11.0 warning-level, sidecar 4/4 y `git diff --check`: PASS.
  Manifest de inputs `06135c739473e577873c3c1799db04d060e6bc6e609d8bf94b13321647a79e5e`; runner
  antes de ejecución `e51f558e48012b2847f0fb45bd71a8b04cef18ef2f25b7ce583acc1f08859fa6`.
- Docker Desktop se verificó como contexto `default`, endpoint Unix de WSL, engine
  `fc2115b2-c3c4-440e-89c6-26899eb7cb04`, versión 29.8.2, 15.5 GiB/12 CPU. `studiamatch-dev`
  está healthy. El volumen snapshot R9 conserva labels; contenedores R9 aparecen exited y
  permanecen preservados. R12 no ha creado fixtures ni escrito evidencia de ejecución.
  Revisión independiente pendiente.
- Métricas sin cambio: G07 parcial, G01–G10 60%, G01–G09 6/9. Siguiente: terminar revisión,
  revalidar pins/preflight y ejecutar el diagnóstico una vez bajo la autorización local expresa
  del 2026-10-10; si falla, conservar salida sanitaria y detener fases dependientes.

## Actualización vigente — 2026-10-10, R10 V2 falló en preflight; V3 revisado

- Candidato: rama `feat/h3req1-sync-20261002`, HEAD baseline
  `4eb4d877a50b012bb630a129bd0c74482c33be9c`; WIP actual 55 tracked modificados,
  4413 archivos untracked, 0 staged. Checkout original preservado.
- R10 V2 terminó exit 1 en el preflight `PostgreSQL image version differs from pinned 17.11`,
  antes de crear red o servicios. Evidencia sanitaria
  [R10 V2](h3req1_c03_integrated_diagnostic_r10_v2.txt), SHA-256
  `e390ba35d4452762ea7c9cca6fb90b63a8a13b8e2778b1aeddc213b75a63d8ce`.
- La causa fue el comparador del runner: exigía igualdad literal con `postgres (PostgreSQL) 17.11`.
  Una lectura aislada, `--pull=never --network=none --read-only --rm`, confirmó que el digest
  fijado corresponde a 17.11 y que el banner añade metadata de paquete Debian. El fallo fue del
  predicado del preflight; no se creó ni modificó PG17/PostgREST, y no se atribuye a Docker o al
  producto.
- Corrección mínima: `postgres_version_classifier.sh` separa el release PostgreSQL del sufijo
  Debian y, si este está presente, exige que ambos digan 17.11. Rechaza otra versión, sufijo
  discordante, distro inesperada y texto extra. Su test sintético queda ahora incluido en el
  `inputs.sha256` autenticado por el runner antes de cargar el helper.
- Revalidación en contenedores aislados: clasificador 7/7; suites contract/log/snapshot 16/16;
  `bash -n`, ShellCheck oficial 0.11.0 warning-level, manifests 7/7 y `git diff --check` PASS.
  Revisión independiente final de seguridad y protocolo PASS, sin findings; test y helper están
  fijados por manifiesto.
- Pins actuales: runner `ddfd4b7be0726e4ca290b92ac40dc6a0e32d0e341810f8e691414352559bb6ec`,
  `inputs.sha256` `a86b240ddb1cbe51b3c3c14bc58ff61c38fc9d46699b55f69e749901a2a2b048`, helper
  `c9e5843dc55cdd39c708b8efff09e95eb1f08abb3de8cdf540fcf7007c1b9304`, test
  `b972064e03912e78dbb65e174d8d1bad926e00f05befcbbdd9470a272474ff0b`, contrato
  `dfb5d59946573bb423aa09b06541bff698af999df862259f5e3eca938889dbcd`.
- R10 V3 ejecutó el diagnóstico completo, exit 0. PG17 readiness y los tres SQL bootstrap
  finalizaron exit 0; TCP/auth con el alias pasó antes y después. PostgREST quedó running,
  exit 0/OOM false, pero el probe respondió `HTTP_503_PGRST002`. Los clasificadores devolvieron
  `NO_SCHEMA_CACHE_SQLSTATE`; esto descarta un fallo de auth TCP observado, pero no identifica
  el error SQL interno. Evidencia sanitaria
  [R10 V3](h3req1_c03_integrated_diagnostic_r10_v3.txt), SHA-256
  `06963c9db4674e8cf73275a4f49f1ef1e435dc693282235d339174bf4cbd550a`. El runner retiró los dos
  contenedores exactos y la red interna exacta; no inició Edge y no conservó logs crudos.
- El resultado muestra que el extractor de logs usa un marcador más estrecho que la salida de
  schema-cache de PostgREST 13. El siguiente paso es una corrección focalizada del clasificador
  para reconocer el marcador/código estructurado sin guardar valores crudos, con sintéticos que
  reproduzcan la forma de salida v13; después se ejecutará un diagnóstico nuevo con snapshot PG17
  aislado. G07 permanece parcial, sin sumar puntos; métricas G01–G10 60%, G01–G09 6/9 = 66.67%.

## Punto de recuperación

- Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
  `feat/h3req1-sync-20261002`, HEAD baseline
  `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- Estado medido en esta actualización: 55 tracked modificados, 4412 untracked, 0 staged. Checkout original
  `/home/romel/src/studiamatch` preservado.
- Gate activo: G07. R9 se consumió con exit 1 en `isolated-postgrest`; 60 respuestas fueron
  `HTTP_503_PGRST002`. No se inició Edge. R8/R9 permanecen como historial y no se repiten.
- G01–G06 completos. Métricas sin cambio: G01–G10 60%; G01–G09 6/9 = 66.67%.
- La autorización humana local del 2026-10-10 cubre este diagnóstico; no se consume un JIT ni
  una aprobación adicional. No incluye servicios/DB remotos, secretos operativos, Git remoto,
  producción, Edge en este diagnóstico o checkout original.

## Hipótesis separadas por prueba

R9 no distinguió entre conectividad/autenticación TCP de otro cliente, fallo de consulta del
schema cache o clasificación de logs ausente. R10 fija el mismo PG17 17.11, PostgREST v13.0.7,
R9 manifest/snapshot, alias `h3req1-c03-pg17`, configuración DB y tres SQL/fixtures de R9.
Antes y después del probe PostgREST, un cliente `psql` efímero en la red interna ejecuta una sola
consulta `SELECT 1` con password aleatorio sintético. PostgreSQL incluye únicamente el SQLSTATE
en el prefijo de log. El filtro PostgREST solo busca el JSON `code` en la línea marcada de error
schema-cache. Ambos clasificadores descartan mensaje, query, detalle, hint, JSON y líneas crudas.

La captura usa `json-file`, `max-size=1m`, `max-file=1`; el lector toma como máximo las últimas 64
líneas y el clasificador retiene 64 KiB. Los bytes nunca se escriben a un archivo de evidencia.
El resultado R10 conserva solo fase, SQLSTATE allowlisted o código cerrado. La red es `internal`
sin egress; contenedores sin puertos publicados; no hay `.env*`, datos/cuentas operativas, Pages,
Edge ni PostgREST remoto. Se monta la snapshot R9 existente en modo read-only, tras validar sus
64 inputs y proveniencia.

## Validación previa al runtime

- R9 manifest: 64/64 PASS; snapshot R9 aún presente y con etiquetas de JIT/manifest esperadas.
- Manifiesto ejecutable R10: 7/7 PASS. El manifiesto vigente fija 7 inputs,
  incluidos helper y test del clasificador; el runner fija su digest
  `a86b240ddb1cbe51b3c3c14bc58ff61c38fc9d46699b55f69e749901a2a2b048` antes de confiar en sus
  entradas.
- Sintéticos + contrato: 16/16 PASS en Node fijado, `network=none`, rootfs y mounts read-only.
- `bash -n`: PASS en el mismo Node image fijado.
- ShellCheck oficial 0.11.0, severidad warning: PASS.
- `git diff --check`: PASS.
- La revisión independiente inicial detectó un MEDIUM: el runner verificaba las entradas contra
  `inputs.sha256` sin autenticar primero el propio manifiesto. Se corrigió fijando su digest dentro
  del runner, comprobándolo antes de `sha256sum -c`, y probando el pin en el contrato sintético.
  La prueba de contrato se excluyó del manifiesto ejecutable para evitar circularidad.
- R10 V1 se ejecutó una vez y terminó exit 1 en `r9-manifest-and-snapshot-provenance`, antes de
  crear red o servicios. La evidencia [R10 V1](h3req1_c03_integrated_diagnostic_r10.txt), SHA-256
  `f066662b844fc74f78a3272f1fd0ff800653f29c4974f448dead88df35ad6ef7`, conserva el resultado
  sanitizado: manifest R9 64/64, el verificador exacto del árbol falló y PG17/PostgREST no
  iniciaron. No se limpió ni modificó el snapshot histórico.
- Una primera reproducción mínima del árbol falló exit 2 porque usó here-string de Bash bajo `sh`;
  ningún recurso quedó creado. La versión POSIX corrigió solo el probe y obtuvo
  `expected=64 actual=66 missing=0 extra=2 symlinks=0`. Los extras son
  `supabase/functions/admin-invite/deno.json` SHA-256
  `5335690600914ad53e9b4873a8287e0baba01902ef94eec02d01b35ca6d7b3be` y `deno.lock` SHA-256
  `ccb3d17f01947e679fb530ba7cbc9d252263ab1051d1d9ab21429eecde7ba428`; ambas rutas están ausentes
  del candidato actual y no aparecen en el manifiesto de 64 inputs.
- Corrección focalizada: `source_snapshot_verifier.mjs` comprueba el digest del manifest, todos los
  archivos/ hashes esperados, ausencia de symlinks y un árbol exacto compuesto por los 64 inputs,
  el manifest y únicamente esos dos extras históricos con hash fijado. Rechaza extras desconocidos,
  drift de hash, symlinks, archivos especiales y límites excedidos. El runner confirma que esos
  extras no aparecen en el checkout candidato y no usa su contenido en las pruebas PG/PostgREST.
- Revalidación tras el arreglo: 16/16 sintéticos (exactitud, dos extras fijados, extra desconocido,
  hash alterado, symlink, source drift y digest del manifest), `bash -n`, ShellCheck 0.11.0
  `--severity=warning`, manifests 5/5 y R9 64/64, `git diff --check` PASS. El primer ShellCheck
  por defecto reportó únicamente SC2016 informativo en una cadena literal; el umbral acordado pasó.
  La invocación real del verificador contra el volumen R9, con volumen/mounts read-only,
  `network=none` y `--pull=never`, terminó exit 0:
  `phase=source-snapshot|error_code=VERIFIED_64_2`. No inició PG17/PostgREST ni dejó contenedores.
  La revisión independiente de este delta está pendiente. El runtime R10 V2 tampoco se ha ejecutado.
  Prueba de contrato SHA-256 `bf45e2ab85ec85b747926dbc8e21237ec0385aa42e6fd14143c93d6511ef59f0`;
  test del verificador `fa0158702e1bccf2f134c3a879423a4c54b5ab09c69a872176795773e85d918d`, ambos fuera
  del manifest ejecutable porque el runner no los consume.
- Antes del PASS final, el contrato diagnóstico obtuvo 8/10 porque dos aserciones buscaban una
  forma literal distinta de la invocación válida del filtro; se cambiaron las aserciones para
  comprobar las formas exactas existentes. ShellCheck también reportó tres variables de
  tracking no usadas; se retiraron sin alterar ownership/trap, que consultan etiquetas exactas.
  La revalidación pasó 10/10 y ShellCheck sin findings.
- Una invocación inicial de `bash -n` del contenedor terminó exit 125 (`invalid checksum digest
  length`) por un digest mal transcrito en el comando local; el runner no inició. Se corrigió el
  digest de imagen al pin local registrado y `bash -n` pasó. Ningún recurso H3 fue creado por ese
  intento.

## Inputs y recursos exactos propuestos

- Runner: `tests/h3req1_c03_integrated_diagnostic_r10.sh`, SHA-256
  `89fb9e0ac92a7aabdf9d7803f6420ebee8ea8e4807335a038d3f7907aaff7033`.
- Helper: `tests/h3req1_c03_r10_diag/postgres_log_classifier.mjs`, SHA-256
  `a4c3dcb752f90b2e8e4142d1f552b0209f62167b763d4731f9903a76cc3e26d4`.
- Verificadores: `postgres_log_classifier.mjs` SHA-256
  `a4c3dcb752f90b2e8e4142d1f552b0209f62167b763d4731f9903a76cc3e26d4`, y
  `source_snapshot_verifier.mjs` SHA-256 `b4f73fd6d390c9293315c99b215900a95793c3e201a82db54fbb6d86c86a77f5`.
  La suite de contrato y los sintéticos están en archivos separados; los inputs ejecutables están
  fijados por `tests/h3req1_c03_r10_diag/inputs.sha256`.
- PG image: `postgres@sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f`, versión
  observada de la imagen local `17.11`.
- PostgREST image: `postgrest/postgrest@sha256:0a46780309a604cdc8b56c776c6e5e15788ce58174d709e40459ab5a2d44d228`.
- Node sanitizer/probe: `node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844`.
- Recursos de ejecución: una red interna exacta R10; dos contenedores etiquetados y limitados
  (PG17 2 GiB/2 CPU, PostgREST 512 MiB/1 CPU); clientes y filtros `--rm`, network interna o
  `none`; snapshot R9 read-only; PGDATA/tmpfs; timeout externo 1800 s y límites por llamada.
- Sin pulls: `--pull=never`; todos los digests se prevalidan localmente. No se hace build ni se
  cambia Docker global.
- Al completar captura sanitizada, se detienen y eliminan por ID exacto los dos contenedores y la
  red vacía R10. No se borran imágenes, volúmenes, snapshot R9, cachés ni recursos históricos.
  Si hay fallo, el trap detiene solo servicios con JIT/manifest/nonce R10 coincidentes y conserva
  los recursos para evidencia/revisión; el engine puede retener hasta 1 MiB de log JSON por
  servicio. En ruta PASS la captura se clasifica y elimina los dos contenedores y la red exacta.

## Ejecución y gate

Pins después de la corrección (la revisión independiente final está pendiente): runner
`89fb9e0ac92a7aabdf9d7803f6420ebee8ea8e4807335a038d3f7907aaff7033`, manifest de inputs
`471fcdebec354155459345b9477a406e2770af0052a30f959f3cb16b8cf2908d`,
helper `a4c3dcb752f90b2e8e4142d1f552b0209f62167b763d4731f9903a76cc3e26d4`, suite del helper
`6df30232ca9ca7023a4be95cfdb7f89c66c42ffdc458a04c4f54949479db9281`, probe PostgREST
`92d419157a8669b889edf5cf78a5d54e31040076788d8a39ddf4123b501f69d7` y manifiesto R9
`6b0a469325b466a59211b3f6e50f16bce49910d78cad994068daa51caba13de9`. El próximo archivo de
salida es `h3req1_c03_integrated_diagnostic_r10_v2.txt`; R10 V1 queda preservado y no se sobrescribe.
Comando preparado:

```bash
/usr/bin/timeout --foreground --signal=INT --kill-after=60s 1800s \
  /bin/bash tests/h3req1_c03_integrated_diagnostic_r10.sh
```

Un exit 0 significa que se completó el diagnóstico, no que PostgREST obtuvo readiness ni que
G07 pasó. Solo la evidencia `postgres-tcp-auth-before/after`, resultado HTTP y SQLSTATE
sanitizado decidirá el siguiente cambio. Ningún cambio al parser, configuración, migración o
servicio se hará por analogía. No se inicia Edge hasta que PostgREST pase el predicado del drill.

## Corte 2026-10-10: resultado R10 V4 y preparación R10 V5

### R10 V4 ejecutado

- Candidato: rama `feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- Resultado: exit 0 del diagnóstico; manifiesto R10 7/7 y R9 64/64, snapshot 64+2, PG17.11,
  readiness y tres scripts SQL exit 0. TCP/auth a PG17 pasó antes y después de PostgREST.
- PostgREST quedó `running`, exit 0, OOM false; el probe devolvió
  `phase=postgrest-probe|error_code=HTTP_503_PGRST002`, probe exit 1.
- El parser V4 informó `NO_SCHEMA_CACHE_MARKER`; PostgreSQL no expuso SQLSTATE. Esto no permite
  inferir causa ni atribuirla a SQL, Docker o producto.
- Evidencia sanitizada preservada en
  [`h3req1_c03_integrated_diagnostic_r10_v4.txt`](h3req1_c03_integrated_diagnostic_r10_v4.txt),
  SHA-256 `e932748d438d77e876005ae56c5d3fb602f76f4367e56dc36b7d4485250e6925`.
  Se retiraron por ID exacto los contenedores PostgREST/PG17 y la red interna R10; no se inició
  Edge, no se persistieron logs crudos y el snapshot R9 quedó sin cambios.

### R10 V5: nueva clasificación estática antes de otra captura

V4 mostró que el filtro no reconocía ningún marcador en los últimos logs acotados, pese al
`HTTP_503_PGRST002`. V5 no presupone que había logs ni su formato: distingue `LOG_EMPTY`,
`NO_JSON_RECORD`, `JSON_CODE_NOT_EXPOSED`, marcador de schema-cache sin código y SQLSTATE/PGRST
estructurados aun sin marcador. Conserva límite de 64 KiB, UTF-8 estricto y emite solo códigos
allowlisted; no guarda ni imprime mensajes, detalles ni líneas.

- Runner `tests/h3req1_c03_integrated_diagnostic_r10.sh`: SHA-256
  `cbdbdd1d9a37ec7667b7cc29912aeba399c02dcf13b34fd8e72fe9f617b8e574`.
- Clasificador: `261c446b1900377e21520ac1161191b0979c8e75a64a4cec8fdb68e1e4b2d55f`.
- Pruebas del clasificador: `b6e50646b07789adba494fa37c89e6d32e8cdbef785f1342b5d116602352f58e`.
- Contrato: `05d74f588fb0968fcd86360adf74c4d3b0122fc97d653027fb2b1851ef1db808`.
- Sidecar fijado por el runner: `19271aac83e46f84c36d608956d2ff84e1d8ecf7706edb909f09f3a9f8c122a0`; 7/7 entradas verificadas.
- Validación: 21/21 tests Node; ShellCheck 0.11.0, Bash `-n`, `git diff --check` y hashes PASS.
  Revisión independiente de seguridad: PASS sin hallazgos; revisión protocolo/SQL: pendiente.
- Salida nueva: `h3req1_c03_integrated_diagnostic_r10_v5.txt`; no sobrescribe R10 V3/V4.
  La siguiente ejecución usa las mismas imágenes PG17/PostgREST/Node fijadas, red interna aislada,
  SQL sintético, credencial efímera, snapshot R9 read-only y cleanup solo por IDs/nonce exactos.
  Exit 0 seguirá significando que el diagnóstico terminó; no implica readiness ni cierra G07.

### Incidentes de preflight sin efectos en Docker

Dos comandos de preflight manuales terminaron exit 1 por una transcripción errónea del digest
R9 en la guarda; el segundo se detuvo antes de consultar Docker. El preflight corregido extrae
el pin directamente del runner y pasó; no se creó ni modificó recurso durante los intentos
fallidos. El revisor automático rechazó una limpieza `rm -f` de un log temporal en `/tmp`;
la operación no se ejecutó y ese archivo inocuo permanece allí. No se intentó otra vía de borrado.

## Corte actualizado: R10 V5 ejecutado; comparador PostgREST v14 local — 2026-10-10

### Resultado R10 V5

- Ejecución única de `tests/h3req1_c03_integrated_diagnostic_r10.sh`: wrapper exit 0 y resultado
  duradero [R10 V5](h3req1_c03_integrated_diagnostic_r10_v5.txt), SHA-256
  `9ad4794b11102cb4c834a62996318195da4fed283542736992789bb62e30be5c`.
- Candidato rama `feat/h3req1-sync-20261002`, HEAD baseline `4eb4d877a50b012bb630a129bd0c74482c33be9c`;
  manifiesto diagnóstico 7/7, manifiesto R9 64/64, snapshot 64+2 extras históricos fijados y
  PostgreSQL 17.11 PASS. Los tres SQL fixtures terminaron exit 0 y TCP/auth PG17 pasó antes y
  después del servicio.
- PostgREST candidato v13.0.7 (`sha256:0a46780309a604cdc8b56c776c6e5e15788ce58174d709e40459ab5a2d44d228`)
  quedó `running`, exit 0, OOM false; probe `HTTP_503_PGRST002`, exit 1. Clasificación acotada:
  PostgreSQL `NO_SCHEMA_CACHE_SQLSTATE`; PostgREST `NO_JSON_RECORD`. El exit 0 del runner es
  finalización del diagnóstico, no PASS de PostgREST/G07. Se retiraron solo los dos contenedores
  y la red interna R10 exactos; Edge no inició, no se persistieron logs crudos y el snapshot sigue
  sin cambios.

### Límite de observabilidad confirmado por fuente oficial

El comando en imagen fijada confirmó `PostgREST 13.0.7`; se conserva como pin del runtime candidato.
El [changelog oficial v14](https://github.com/PostgREST/postgrest/blob/main/CHANGELOG.md) registra
que v14.0 corrigió la ausencia del mensaje JSON de error en `stderr` para `PGRST002`. La
[documentación oficial v13 de observabilidad](https://docs.postgrest.org/en/v13/references/observability.html)
describe que la información diagnóstica del servidor se envía por `stderr`. Esto explica por qué
V5 pudo ver solo registros de texto sin el detalle JSON; no identifica la causa del 503 y no
justifica cambiar imagen, SQL, configuración o producto.

### Comparador diagnóstico v14.0 preparado y revisado

Para obtener el detalle del mismo fixture sin alterar el runtime candidato, se preparó un runner
separado que mantiene los SQL, snapshot R9, PG17, URI/configuración, probe, red interna y
protecciones de R10; solo usa PostgREST 14.0 de `postgrest/postgrest:v14.0`, digest
`sha256:f8176256ad55a794a61ee6d76d00121635fac4d63bb3d51594e5ed6790f91c72`. La descarga fue del
registro oficial Docker Hub; el digest se verificó localmente y `postgrest --version` en
`network=none` devolvió exactamente `PostgREST 14.0`. El runtime R9 mantiene su imagen v13.0.7.
El comparador usa IDs/nombres únicos, labels JIT/manifest/nonce, límites, `--pull=never`, logs
leídos en memoria por el clasificador cerrado de 64 KiB, y cleanup por ID exacto. No inicia Edge.
Incluso si da readiness, su salida solo sirve para localizar la causa: no acredita G07.

Pins estáticos actuales:

- Runner R11: SHA-256 `952e07c623056c3e402cc6000e00cd3a7adf5b21e913a3e1b1d7edb680f80442`.
- Test contractual: SHA-256 `e6946eacc164739dda48d0a4d6e75c012d47f674de22e66ea77caf09a9cc37ee`.
- Sidecar R11: SHA-256 `b612f05212d5d2b32782d554265cb1e9c36c6174af079428651659535005cd1a`; verifica 8/8,
  incluido el test contractual. El runner valida el digest del sidecar antes de `sha256sum -c`.
- Pruebas contractuales del comparador: 4/4 en Node 22 fijado, `network=none`, mounts read-only;
  `bash -n`, ShellCheck 0.11.0 warning-level, sidecar 8/8 y `git diff --check` PASS. La primera
  revalidación 3/4 detectó hash anterior en una aserción del test; se corrigió el predicado a
  comprobar presencia de ruta de test con formato de hash, evitando referencia circular. Luego
  volvió a pasar 4/4.
- La revisión independiente de `edge_sql_review` cerró el LOW inicial de pins: runner, sidecar y
  test coinciden con esos hashes; verificó límites, salida filtrada, montaje read-only, red interna,
  cleanup por ownership exacto y que el runtime R9 no cambió. PASS sin otros blockers. Sin Docker
  ni SQL ejecutados por el revisor.
- Se conserva el fallo inicial de ShellCheck exit 2: el despacho duplicó el nombre del ejecutable
  de la imagen como argumento; el comando correcto pasa. Un intento de inspección de labels terminó
  exit 1 porque la imagen no declara `Config.Labels`; fue read-only y no produjo cambios. Ninguno
  inició PG17/PostgREST.

## Resultado R11 — comparador PostgREST 14.0, 2026-10-10

R11 se ejecutó una vez después de confirmar que runner/test/sidecar, Docker Desktop y recursos
fijados coincidían. Diagnóstico exit 0; R11 inputs 8/8, R9 64/64, snapshot 64+2, PostgreSQL
17.11 y PostgREST 14.0 identificados. Los tres fixtures SQL y TCP/autenticación PG antes y
después terminaron PASS. PostgREST quedó running, exit 0/OOM false; el probe único a los cinco
segundos devolvió `HTTP_503_PGRST002`. El clasificador acotado produjo `NO_SCHEMA_CACHE_SQLSTATE`
para PostgreSQL y `NO_JSON_RECORD` para PostgREST. Evidencia sanitaria:
[`R11 V14`](h3req1_c03_integrated_diagnostic_r11_v14.txt), SHA-256
`b5a10e5a6973d76d488b9bdd6a05e52b4a3276664389846872459e6b5a9aaef5`.

El runner retiró únicamente los IDs de sus dos contenedores y la red interna vacía etiquetada
con nonce propio. No hubo Edge, datos operativos, secretos ni logs crudos persistidos. El runtime
candidato conserva PostgREST 13.0.7. V14 no reveló por sí solo la causa; por ello la hipótesis
basada en el observador quedó refutada como explicación suficiente, no la causa del fallo.

### Cambio de método

Los logs sanitizados anteriores solo separaban texto/JSON y no acreditaban cuándo termina la
carga del schema cache. Además, R11 tomó una única muestra a los cinco segundos, mientras que
R9 ya había observado 60 respuestas HTTP 503. No se repite ese polling. La documentación oficial
PostgREST 13 describe un comando síncrono `--dump-schema` y health/metrics `/ready`; primero se
probará el dump una vez con la imagen candidata v13.0.7. Un helper nuevo conservará únicamente
exit, presencia de JSON/código allowlisted y una categoría cerrada; no expondrá nombres de schemas,
funciones, mensajes, DSN ni cuerpos. Si el dump no clasifica el error, el siguiente método leerá
health/metrics y estado agregado de `pg_stat_activity`, sin SQL de producto adicional.

### Estado y recursos

- `studiamatch-dev`: permanece healthy con imagen `studiamatch-h3req1:20261009-v3`; no fue usado
  para secretos o consultas aisladas.
- S2/S3 startup holders: up; snapshot R9 de 64 entradas sigue preservado; R11 no cambió los
  volúmenes persistentes.
- No quedan contenedores ni red R11; el inventario read-only confirmó titulares S2/S3 y dev.
- WIP medido: 55 rutas tracked modificadas, 4419 untracked, 0 staged (4474 entradas). Incluye
  trabajo previo y evidencia; todo se conserva.
- Gate activo G07, parcial; G01–G06 completos. Métricas sin cambio: tablero G01–G10 60%, cierre
  local G01–G09 6/9 = 66.67%. G08/G09/G10 siguen pendientes.
