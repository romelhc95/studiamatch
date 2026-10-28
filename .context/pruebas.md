# Pruebas y evidencia

## Corte local nuevo — 2026-10-28

El [checkpoint editorial H3REQ1](evidencia/h3req1_editorial_contract_2026-10-28.md)
separa el nuevo contrato E1–E6 de métricas históricas. E1–E4 se ejercitaron en
PostgreSQL 17 desechable con fixtures sintéticos; E5 en pruebas unitarias Docker de
FG3; E6 está pendiente de navegador. Los logs e intentos/fixes se resumen allí. No
hubo PR, CI, pruebas de negocio remotas ni acceso a cuentas reales.

## Correspondencia suite → componente → entorno → resultado

| Suite/caso | Componente/criterio | Entorno e input | Resultado vigente para el cierre | Evidencia y límites |
|---|---|---|---|---|
| Python contracts/functional set de G03 | Pipeline, Auth/Admin, credenciales, seguridad y aceptación | Docker; candidato con inputs identificados | 337 passed, 4 skipped, 1 warning | R178. Skips/warning declarados; no convertirlos en PASS. |
| G01 PostgreSQL editorial | Tablas/funciones H2/H3 y contratos de publicación | PostgreSQL 17 desechable, schema sintético | Completo en R178 para casos locales seleccionados | R178 y harnesses tests/sql; no DB operativa. |
| G05 source snapshot S18 | Integridad de archivos del runtime Pages | Docker/read-only snapshot local | 17/17 fuentes; manifest 17/17 | R178 y evidencia G05 S18. |
| G06 Pages/workerd y static artifact | Runtime local y export | Docker; Pages/workerd local y artefacto input R146 | runtime smoke PASS; artifact normal 201/201 | R178; no implica deploy ni cache remoto. |
| G07 C03 integrado R51 | Pages Functions, Edge simulado, PostgREST/PG17 | Contenedores aislados, 128/128 inputs fijados | 128/128 y recorrido integrado PASS | R178; sintéticos/locales, no Free/Pro. |
| G08 scanner/lint/types/build/contracts | Seguridad y calidad del candidato | Docker, snapshots y rutas de evidencia declaradas | R178: scanner 854 paths PASS; actionlint 1.7.7 y ShellCheck 0.11.0 PASS; otros checks según tabla de R178 | Input exacto por R178/R159–R176; los cambios de docs renuevan el scanner/scope, no todos los funcionales. |
| G09 caso/viewport | UI pública/Admin, estados, responsive y criterios cliente | Fixtures sintéticos locales | 216/216 resultados seleccionados; R173 6/6 viewports y 36/36 assertions | R178; no auditoría WCAG completa ni QA remota. |
| Onboarding invitaciones | Aceptar/recovery/password/MFA | Mock/synthetic isolated | 10/10 en la ejecución R6 declarada | R178/R6; el fallo intermitente anterior se conserva en su evidencia histórica. |
| R181/R182 package review | Alcance/manifiestos/plantilla/evidence R8 | Candidato local; revisión estática independiente | PASS sin HIGH/CRITICAL/bloqueos; R182 scope/scanner 92/92 | Evidencia R181/R182; no incluye los nuevos docs R9. |
| Supabase remoto / GitHub CI / Cloudflare | Adoption, auth real, applied schema, remote workflows | No se ejecutó en esta sesión | Pendiente/desconocido | Requiere lectura y autorización en etapa futura; no se infiere por código o commits. |

## Tipos de prueba y fixtures

- Unitarias/contratos Python: tests/test_*.py y tests de security. Muchos leen fuentes estáticas y fixtures.
- Contract/runtime JS: tests/*.mjs; mock-server y adaptadores de Pages Functions para no llamar servicios reales.
- SQL: tests/sql/*.sql, harnesses H2/H3 y PostgreSQL 17 sintético, desechable.
- Navegador: runners UAT/Playwright locales y capturas por viewport.
- Integración: Pages/workerd + Edge/Auth/PostgREST local o simulado, identificado caso por caso en manifiesto.
- Diagnósticos one-off de transferencia C03: están separados de las suites de producto en la [ficha de pruebas](componentes/pruebas_evidencia.md#diagnosticos-de-transferencia-c03); sus wrappers pueden cambiar recursos Docker y requieren inspección por path antes de uso.
- Remotas: no ejecutadas para este corte documental. Tests históricos que usaron servicios remotos solo se presentan desde su evidencia fechada y no como estado presente.

Mocks/test data no representan estudiantes, instituciones activas ni filas reales. No se ejecutan scripts que importen DB client con efectos de conexión/write para inventariar.

El [compose de fixture H2](../docker-compose.h2-test.yml) declara `h2-r1-tests`, que invoca `scripts/security/run_h2_r1_tests.sh`, con red deshabilitada y checkout montado en solo lectura. Es una configuración aislada histórica; no se ejecutó en esta sesión ni sustituye la evidencia H3REQ1 R178/R9. `test-results/.last-run.json` es estado Playwright generado/versionado, no prueba autocontenida ni resultado vigente.

## Reproducción segura

Use el contenedor Docker permitido por AGENTS.md y un checkout/fixture con input fijado. La suite documental nueva es read-only y se reproduce desde /app con `docker exec studiamatch-dev bash -lc 'cd /app && node scripts/maintenance/h3req1_documentation_integrity.mjs'`; el código fuente es [h3req1_documentation_integrity.mjs](../scripts/maintenance/h3req1_documentation_integrity.mjs). Para repetir una prueba funcional, seguir el comando y el input exactos de la evidencia R178 enlazada al caso, no un runner amplio con credenciales reales. No correr static build sin analizar que elimina .next/out y puede consultar Supabase al generar rutas.

## Revalidación por impacto

Documentación/enlaces/anchors: grafo Obsidian completo y test de índices. Cambios al alcance/atestación: validador de fuente cliente y criterios. Cambios en allowlist/workflows: actionlint, protected workflow review, scope guard y scanner en Docker. Cambios de UI/BFF/SQL/pipeline: suites de componente correspondientes; cambios de runtime/credencial: integración con fixture apropiado. Los cambios documentales no reabren G01–G09 si los inputs funcionales permanecen iguales.

## Fuentes

R178, evidencias G01–G09 y matrices LOCAL-01..23 en .context/evidencia; tests/, tests/fixtures/, tests/sql/, mock-server/; atestación cliente sanitizada en .context/evidencias_cliente/sprint_1/. Cada PASS está limitado por fecha, checkout y entorno descritos en la evidencia citada.

## Navegación relacionada

[Fichas de suites](componentes/pruebas_evidencia.md) · [Registro de fuentes](trazabilidad/registro_fuentes_componentes.md#asignaciones-por-fuente) · [Frontend](frontend.md) · [Backend](backend.md) · [Database](database.md) · [Pipeline](componentes/pipeline.md) · [Seguridad](seguridad.md) · [R178](evidencia/h3req1_g09_local_close_r178_2026-10-11.md) · [R181/R182 R8](evidencia/h3req1_g10_r8_review_corrections_r181_2026-10-12.md) · [Requerimientos](requerimientos/README.md) · [Hitos](hitos/README.md) · [Índice](indice.md)

Registro por fuente: [suites, fixtures, runners y evidencia](trazabilidad/registro_fuentes_componentes.md#pruebas-y-evidencia).
