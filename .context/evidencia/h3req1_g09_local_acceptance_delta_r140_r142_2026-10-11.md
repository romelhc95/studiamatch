# G09 delta R140–R142 — SQL de cleansing e conciliación de inventario — 2026-10-11

## Candidato y runtimes

- Checkout: `/home/romel/src/studiamatch-h3req1-sync-20261002`.
- Rama/HEAD: `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c`; el HEAD es el baseline, no la identidad completa del WIP.
- `studiamatch-dev` (`500931b0f086`) siguió healthy sobre `studiamatch-h3req1:20261009-v3`; se usó solo para scanner/comparador, no para alojar el navegador.
- App UAT R12 `h3req1-g09-uat-app-20261010-r12`, Pages/workerd `127.0.0.1:3330`, mock Auth/PostgREST `:3331`, y PG17.11 sintético R12 se conservaron. Playwright Chromium 1228 corrió headless dentro del contenedor; no se abrió una ventana.
- No hubo cuentas reales, correo real, secretos, egress cloud, escritores operativos, operaciones remotas, ni cambios de producto.

## R140 — atomicidad de cleansing contra PG17.11

El runner existente `tests/sql/run_fase10_8_atomic_cleansing_postgres.sh` se ejecutó una vez, timeout 180 s, exit 0, en el contenedor desechable `h3req1-g09-pipeline-pg17-r140` (ID `a470e72d85d386be949c86cc481d7ff32a88a1a4d5ddc7c3d351caef3a8d8cbd`). Imagen fijada por digest local `sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f`, PostgreSQL 17.11, red none, 2 CPU, memoria 4 GiB, PGDATA tmpfs, sin volúmenes ni puertos. Solo runner y migration se montaron read-only.

El test verificó inserción/upsert por URL, preservación de metadata histórica y refresh de procedencia, transiciones `pending/processing → processed`, requeue idempotente, unicidad e inmutabilidad del ID existente, y grants/search_path del RPC. El contenedor exacto se retiró después de preservar el log y su identidad; no se borraron imágenes, volúmenes ni datos de otros servicios.

- Runner SHA-256: `2b36d95806a0120a2631de7b1f504e379c98d01ea3e3c14f3e5a7e4838714103`.
- Migration SHA-256: `741edac171fa2b8431ea3e850ece09324c718b191bc0654801c27dde41aeaeb7`.
- Log: [R140 PG17](h3req1_g09_pipeline_pg17_r140/pg17-atomic-cleansing.log), SHA-256 `71e0b93ca5efe3f23409d4734d4bf6ef6d7cb987fbb6cc0a4926d18d2ee3eea6`.
- Identidad/red/recursos sanitizados: [R140 container](h3req1_g09_pipeline_pg17_r140/container-identity.txt), SHA-256 `e40576518bbb693b0c142867a2e708624425a5eb2d59a3343c94ec296cdc0cf0`.

Este resultado renueva solo el RPC de cleansing. No acredita aún que checkpoint/recovery de discovery, enrichment y sync sobreviva a fallos entre requests contra el mismo PG17; LOCAL-07/08/19 permanecen parciales.

## R141–R142 — identidad PG17, lector público, artifact y listing

R141 tomó una proyección read-only de 31 cursos sintéticos PG17: 16 elegibles en `courses_public_effective`, 15 no elegibles. El comparador estructurado coincide en el conjunto exacto de 16 identidades (ID/institución/slug) entre PG17 y lector público. Las 16 rutas elegibles respondieron HTTP 200 con título propio; las 15 rutas no elegibles respondieron 404. Todo fue local y con consultas `READ ONLY`/`ROLLBACK`.

Las 16 rutas PG17 elegibles coinciden con las 16 rutas de producto del artifact estático R69 montado por R12. El primer comparador marcó 32 diferencias al mezclar una lista relativa con rutas absolutas; se conserva como fallo del comparador, no de la aplicación. Se corrigió solo la normalización del comparador y la misma comparación devolvió 16/16, cero diferencias, sin rebuild ni nueva consulta.

R142 añadió al runner UAT existente H3-UAT-071. La prueba atiende una respuesta local sintética que reproduce el inventario PG17 elegible y compara todas las rutas de tarjeta. Pasa desktop/tablet/mobile: 3/3 ejecuciones, 6/6 aserciones por viewport (18/18), 16 tarjetas exactas entre páginas 12+4, cero identidades duplicadas, cero rutas extra/no elegibles, cero requests a orígenes externos, cero errores de consola/requests y cero retries. Se conservaron tres capturas y vídeo desktop. Esta prueba verifica el renderer/listing en Chromium; la correspondencia del origen se demuestra aparte con el comparador R141 y no se presenta como una conexión directa del navegador a PG17.

El runner UAT `tests/h3_local_uat.mjs` tiene SHA-256 `08cf76f22f211fccb325bdd6ab90eb132e238435d982d0419f36fb2b2e9a321c`. `node --check`, validación estructural del caso seleccionado y credential scanner focal pasaron. El candidato está en el mismo runtime R12/imagen V3, sin reconstruir el entorno.

- [Comparación PG17/API](h3req1_g09_local_inventory_r141/identity-set-comparison.json), SHA-256 `7106ee114920637631261d70f3c40cc18ab5474090d61b8ca34d83f7c82fefcb`.
- [Comparación contra artifact](h3req1_g09_local_inventory_r141/static-artifact-comparison.txt), SHA-256 `edf3889bdd078990c8672d00dd12d44a6cffeaf585935092662a033c33ab6136`; intento del comparador con rutas absolutas conservado en `static-artifact-comparison-attempt1.txt`, SHA-256 `84e40d029a0c8855caeef69f42726d76bfd5373daafece398c1c27c6472a80dd`.
- Proyección PG17, SHA-256 `fc565ff43d43b5d6f07b2c094ebc3e31b0be864e58286f8fee6db264916d5740`.
- Lector y detalles, SHA-256 `bfe152fed0d26c9c616953f1f0265fa5c0712246b022a639e808c1912bd09b18`; 15 rutas no elegibles 404, SHA-256 `c6c65f06c6064f663f993263de017d960f44b89cab170a28ca3b10046f6e6982`.
- Matriz R142: [JSON](h3req1_g09_uat_2026-10-10_r4/uat-public-inventory-r142/h3-expanded-uat-matrix.json), SHA-256 `06dc3489a743bdef74bd310899ad4d5280a6830b9572c0f6f9e58ca2d903a550`.
- Ejecuciones R142: [JSON](h3req1_g09_uat_2026-10-10_r4/uat-public-inventory-r142/h3-expanded-uat-executions.json), SHA-256 `fb7341293401e2c8739da287af766a51d0890e599cdd337febb6ae1d379fecc3`.
- Manifiesto R142 SHA-256 `35b3726747a7a981d6e9bfa7affaeed09f745a567f7a1b8dd45e619e827a8768`; hashes de artefactos SHA-256 `47679fbdc011a4645d2e4e51200d1edcbce73c28b69534986a5e86e90ec3c9ca`.
- Capturas: [desktop](h3req1_g09_uat_2026-10-10_r4/uat-public-inventory-r142/H3-UAT-071-desktop.png), [tablet](h3req1_g09_uat_2026-10-10_r4/uat-public-inventory-r142/H3-UAT-071-tablet.png), [mobile](h3req1_g09_uat_2026-10-10_r4/uat-public-inventory-r142/H3-UAT-071-mobile.png); [vídeo desktop](h3req1_g09_uat_2026-10-10_r4/uat-public-inventory-r142/H3-UAT-071-desktop.webm).

Dos fallos de despacho se conservaron y no llegaron a lanzar navegador: un `docker exec` sin nombre de contenedor y después una ruta de evidencia `/app/.context` inexistente en R12. Se corrigió únicamente el destino de evidencia a `/tmp` del contenedor; los outputs se copiaron al checkout y se verificaron por hash. Son fallos de ejecución/preflight, no de producto.

## Matriz y estado de aceptación

- LOCAL-01 se completa para el fixture sintético actual: 31 filas, 16 identidades elegibles enlazadas PG17 → lector → artifact → listing, 16 detalles 200 propios y 15 rutas no elegibles 404. No representa inventario operativo.
- LOCAL-03 avanza, pero sigue parcial: el inventario completo, artifact y listing coinciden; falta mutación del mismo registro seguida por rebuild/cache/reset y nuevo cotejo de todos sus consumidores.
- LOCAL-07/08/19 avanzan con R140; siguen parciales hasta probar persistencia y recuperación integrada por etapa en el mismo PG17. El LLM/embeddings, fuentes HTTP/DNS y writers cloud siguen fuera de esta prueba.
- INV-008 no se volvió a ejecutar: R8 ya conserva causa reproducida y onboarding sintético 10/10.
- No cambia el porcentaje de gates: tablero G01–G10 80% (8/10); cierre local G01–G09 88,89% (8/9). LOCAL-23 y G09 siguen pendientes.

