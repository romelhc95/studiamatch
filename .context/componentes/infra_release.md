# Componentes: infraestructura y release

> Alcance: configuración versionada, workflows y guías de operación local. Las definiciones en YAML describen el candidato; no prueban que GitHub, Cloudflare, Docker remoto o un editor hayan instalado, activado o ejecutado esos contratos.

## Límites y dependencias

Docker local prepara los runtimes de Python/Node y fixtures de prueba. GitHub Actions define controles y automatización; sus jobs consumen scripts del repo y variables por nombre. Next.js produce el export estático que Pages puede servir; Pages Functions y Worker tienen sus contratos propios en [Runtime Admin](admin_runtime.md). Supabase y Cloudflare son dependencias externas. Las páginas [Tecnologías](../tecnologias.md), [Operación](../operacion.md), [CI/CD](../ci_cd.md), [Seguridad](../seguridad.md) y [Arquitectura](../arquitectura.md) explican ambiente, secretos por nombre, permisos y recuperación.

## Workflows versionados

### workflow-fg1-discovery

Fuente: `.github/workflows/fg1_inventory.yml`. Declara `schedule` mensual (`0 0 1 * *`) y `workflow_dispatch`. El job de control invoca `.github/scripts/production_control_preflight.sh FG1`; el job de inventario instala `requirements-fg1.txt`, vuelve a exigir el preflight con `--enforce` y ejecuta `scripts/core/discovery_institutions.py`. El productor/consumidor de datos se describe en [Pipeline](pipeline.md#gates-y-perfiles); el workflow no es un runner local de la documentación.

Las pruebas `tests/test_fase09_10_pre_main_controls.py` y `tests/test_fase10_main_boundary.py` leen el YAML para verificar límites pre-main y configuración de los workflows FG1/FG2/FG3. `tests/test_supabase_credentials_contract.py` inventaría la identidad `supabase-ci` asociada al workflow. La existencia de esos casos no atribuye un resultado de ejecución actual ni prueba que el schedule esté activo.

### workflow-fg3-integrity

Fuente: `.github/workflows/fg3_integrity.yml`. Declara `schedule` diario (`0 11 * * *`) y `workflow_dispatch`; el comentario YAML lo sitúa después de la ventana FG2. El flujo pasa por el preflight FG3, instala `requirements-fg3.txt` y ejecuta `scripts/core/integrity_ping.py` desde `scripts/core`. Ese worker revisa enlaces y cambia el estado operativo de cursos según su contrato documentado en [Pipeline](pipeline.md#estaciones-y-contratos).

Los consumidores de prueba son `tests/test_fase09_10_pre_main_controls.py`, `tests/test_fase10_main_boundary.py` y el inventario de credenciales de `tests/test_supabase_credentials_contract.py`. Son contratos locales sobre el YAML; no acreditan el último run, horario remoto ni writes actuales.

### workflow-fg2-pipeline

Fuente: `.github/workflows/production_pipeline.yml`. Declara ventana diaria (`0 5 * * *`) y `workflow_dispatch`. Encadena preflight de control, harvesting mediante `scripts/core/master_orchestrator.py`, `cleansing_worker.py`, `enrichment_worker.py`, `sync_vector_worker.py` y una auditoría final. Los jobs Python instalan `requirements-pipeline.txt` con `--require-hashes`; cada estación vuelve a pasar su gate con `--enforce`. Los límites de estados, tablas y requeue están en [Pipeline](pipeline.md) y [Datos/Pipeline](datos_pipeline.md).

`tests/test_fase09_10_pre_main_controls.py`, `tests/test_fase10_main_boundary.py` y `tests/test_supabase_credentials_contract.py` leen estos pasos para validar controles, ramas y origen de credenciales. La secuencia local no demuestra schedule activo, secrets provisionados, datos procesados o que una estación haya terminado correctamente en un run remoto.

### workflow-opencode

Fuente: `.github/workflows/opencode.yml`. Sus eventos declarados son `issue_comment` y `pull_request_review_comment`; ejecuta la acción externa `anomalyco/opencode/github@latest`. No se encontró un caller local adicional en workflows, scripts, tests o código en ninguno de los dos checkouts. Esto acredita el grafo local de archivos, no la instalación/configuración de la app, su ejecución remota o el contenido de comentarios. No se trata como un endpoint de StudIAMatch ni como parte del pipeline de datos.

## Configuración y toolchain

### repo-tools-config

`.editorconfig` fija convenciones para editores; `.gitattributes`, `.gitignore` y `web/.gitignore` configuran Git; `.actrc` es una preferencia de la herramienta local `act`. Son archivos reconocidos por sus herramientas, no importados por el runtime del producto. `.actrc` no se lee ni se interpreta aquí. Su existencia no prueba que `act` esté instalado o se haya ejecutado.

| Fuente | Responsabilidad local |
|---|---|
| `.editorconfig` | Convenciones de formato al editar archivos. |
| `.gitattributes` | Atributos Git para rutas del repositorio. |
| `.gitignore` | Exclusiones Git del checkout raíz. |
| `web/.gitignore` | Exclusiones Git específicas del workspace web. |
| `.actrc` | Configuración de `act`; el contenido se preserva sin leer por posible dato operativo. |

### docker-runtime-config

Fuentes: `.dockerignore`, `Dockerfile`, `docker-compose.yml` e `init-container.sh`. El compose de desarrollo define el contenedor `studiamatch-dev`; el Dockerfile prepara Python, Node y el workspace web; el inicializador configura el contenedor según [AGENTS.md](../../AGENTS.md). El punto de entrada operativo es [Docker local](../operacion.md#docker-desktop--wsl). Los recursos ya existentes se preservan: documentar no autoriza rebuild, restart, prune o limpieza.

### docker-h2-fixture

Fuente: `docker-compose.h2-test.yml`. Es la configuración aparte para el fixture H2/PG17; no es una base local de producto ni sustituye Supabase cloud. `scripts/security/run_h2_r1_tests.sh` selecciona esa configuración. La suite fixture se enlaza desde [Pruebas](../pruebas.md#tipos-de-prueba-y-fixtures). No ejecutar este compose sin el scope/JIT propio del fixture.

### env-template

Fuente: `.env.example`. Es una plantilla de nombres/forma de configuración para desarrollo; no es un archivo operativo ni un registro de valores provisionados. Se documentan los nombres de variables en [Operación](../operacion.md#ambientes-y-datos); los valores locales no se leen ni se copian al paquete.

### python-dependencies

| Archivo | Consumidor local verificable | Función |
|---|---|---|
| `requirements.txt` | `Dockerfile` | Dependencias Python base del contenedor. |
| `requirements-pipeline.txt` | `Dockerfile`, `production_pipeline.yml`, `production_canary.yml` | Dependencias del pipeline/canario; CI exige hashes. |
| `requirements-fg1.txt` | `fg1_inventory.yml` | Entorno del discovery mensual definido. |
| `requirements-fg3.txt` | `fg3_integrity.yml` | Entorno del worker de integridad definido. |
| `requirements-db-migrate.txt` | `.github/workflows/db-sync-to-pro.yml` | Herramientas de migración/revisión DB; ese workflow tiene permisos y gates separados. |

La configuración de dependencias describe resolución reproducible. No prueba paquete instalado ni ejecución remota. Los rangos/versiones y hashes se mantienen en cada requirements y se resumen en [Tecnologías](../tecnologias.md#dependencias-y-locks).

### web-toolchain

| Fuente | Uso local / consumidor | Consideración de cambio |
|---|---|---|
| `web/package.json` | Scripts/dependencias ejecutados desde `web/` por npm. | Revisar consumidores de cada script y renovar suite/build por impacto. |
| `web/package-lock.json` | `npm ci`; dependencias transitivas. | Mantenerlo coherente con package manifest y resolución local; la dependencia empaquetada tiene decisión separada en [Tecnologías](../tecnologias.md#dependencia-local-braces). |
| `web/next.config.js` | Next build/export; `@/*` y opciones de Pages. | Validar rutas dinámicas, export y consumidores públicos/Admin. |
| `web/eslint.config.mjs` | `npm run lint`. | Renovar ESLint si cambia configuración o regla. |
| `web/postcss.config.mjs` | Pipeline CSS del build web. | Revisar CSS generado y build si cambia plugin/config. |
| `web/tsconfig.json` | TypeScript (`npx tsc --noEmit`). | Revisar aliases/includes y typecheck. |
| `web/components.json` | Configuración del generador de componentes UI. | No es un módulo de runtime ni una dependencia de cada componente creado. |

`AGENTS.md` acredita los comandos de build, lint y typecheck usados por el equipo; no se ejecutan por un cambio documental sin impacto. No hay un workflow versionado que haga deploy Pages en este corte local.

## Guías, comandos y plantillas

### agent-guides

Las guías describen roles/instrucciones para trabajo humano o asistido; no son GitHub Actions, servicios ni permisos. La búsqueda local acotada a `.github/workflows`, `.github/scripts`, `scripts`, `tests`, `web`, `workers`, `supabase`, `db` y `config` no encontró referencias ejecutables a esos paths en candidato u original; no se inventa un importer. La asociación y el consumidor externo de la plataforma/editor quedan sin verificar.

| Fuente | Propósito indicado por la guía |
|---|---|
| `.github/agents/api-designer.md` | Proceso de diseño de interfaces y APIs. |
| `.github/agents/architect-hexagonal.md` | Guía histórica de arquitectura hexagonal. |
| `.github/agents/backend-architect.md` | Patrones de desarrollo backend. |
| `.github/agents/code-cleaner.md` | Refactorización y limpieza. |
| `.github/agents/data-analyst.md` | Análisis de datos y soporte a decisiones. |
| `.github/agents/db-migrator.md` | Migraciones de bases de datos. |
| `.github/agents/devops-engineer.md` | Patrones de despliegue y DevOps. |
| `.github/agents/doc-writer.md` | Documentación y mapas de código. |
| `.github/agents/frontend-architect.md` | Patrones de desarrollo frontend. |
| `.github/agents/health-monitor.md` | Auditoría de activos auxiliares y estado documental. |
| `.github/agents/mobile-architect.md` | Desarrollo móvil Flutter/Dart; no se encontró módulo móvil en el inventario. |
| `.github/agents/planner.md` | Planificación subordinada a la autoridad operativa. |
| `.github/agents/python-expert.md` | Patrones de desarrollo Python. |
| `.github/agents/qa-engineer.md` | Estrategia de pruebas end-to-end. |
| `.github/agents/researcher.md` | Investigación y extracción. |
| `.github/agents/sdlc-chief.md` | Coordinación SDLC con límites de autorización. |
| `.github/agents/security-auditor.md` | Revisión de seguridad. |
| `.github/agents/tdd-coder.md` | Flujo de desarrollo dirigido por pruebas. |
| `.github/agents/tech-evaluator.md` | Evaluación y selección de tecnología. |

### command-prompts

Los cinco `.github/commands/*.toml` describen comandos asistidos por Gemini CLI. La misma búsqueda de consumidores ejecutables en ambos checkouts no encontró un runner o workflow que los cargue. La invocación manual/editorial y la instalación externa no se afirman; no forman parte de CI demostrado.

| Fuente | Descripción del TOML |
|---|---|
| `.github/commands/gemini-invoke.toml` | Invoca Gemini CLI. |
| `.github/commands/gemini-plan-execute.toml` | Invoca Gemini CLI para plan/ejecución. |
| `.github/commands/gemini-review.toml` | Revisa un pull request con Gemini CLI. |
| `.github/commands/gemini-scheduled-triage.toml` | Clasifica incidencias en un flujo programado asistido. |
| `.github/commands/gemini-triage.toml` | Clasifica una incidencia asistida. |

### root-readme

`README.md` raíz es una presentación corta y contiene un enlace al único índice Obsidian, `.context/indice.md`. Además de lectores humanos, el checker documental y tests de scope/state inspeccionan el README; la ruta se conserva para que sea el punto de orientación del checkout.

### pull-request-template

`.github/pull_request_template.md` contiene la lista de evidencia y gates que deben llenarse antes de un PR. `AGENTS.md` instruye a usar la plantilla; el workflow de seguridad y tests de aceptación la leen como fuente local. Esto no demuestra el comportamiento actual de GitHub al abrir un PR.

## Seguridad, permisos y operación

- Los workflows no incluyen valores secretos en la documentación; consultan nombres de variables/bindings indicados en [Operación](../operacion.md) y [Seguridad](../seguridad.md).
- Los preflights por fase limitan la ejecución localmente declarada. Modificar un workflow requiere revisar su `permissions`, eventos, `environment`, `concurrency`, gates y cada comando directo antes de ajustar allowlists.
- `schedule` en YAML significa “definido en el checkout”. R15 consultó runs y deployments, pero el endpoint de branch protection dio 403; resultados históricos no prueban latest/required status del WIP, secrets provisionados ni enforcement completo.
- Un cambio de Docker/requirements requiere renovar los checks de imagen/dependencias pertinentes. Un cambio web requiere build/lint/typecheck según paths e inputs afectados. Un cambio de workflow requiere parse YAML, tests de contrato del workflow, scope guard y scanner. No se repiten suites cuyo input no cambió.

R15 registró `main` como default y `desarrollo` en el SHA base del candidato, con siete workflows listados en cada ref y un ruleset `update`; `protected-workflow-integrity.yml` sigue solo en el candidato local. Pages `studiamatch` mostró production `main`/SHA `70d0f4fe…` y preview `desarrollo`/SHA `4eb4…`, no el WIP R14. Detalle, permisos faltantes y estado NO-GO en [lecturas R15](../evidencia/h3req1_g10_remote_preparation_2026-10-13_r15.md#github) y [paquete futuro](../evidencia/h3req1_development_integration_package_2026-10-13_r15.md).

## Navegación relacionada

[Infraestructura y release](../ci_cd.md) · [Operación](../operacion.md) · [Seguridad](../seguridad.md) · [Tecnologías](../tecnologias.md) · [Pruebas](../pruebas.md) · [Arquitectura](../arquitectura.md) · [Registro de fuentes](../trazabilidad/registro_fuentes_componentes.md#infraestructura-y-release)

## Fuentes y relaciones

El registro JSON mantiene el mapeo exacto por fuente, responsabilidad y anchor; la tabla renderizada enlaza a [Infraestructura y release](../trazabilidad/registro_fuentes_componentes.md#infraestructura-y-release). Las relaciones de tests describen qué contrato leen; los logs fechados y este corte determinan si un resultado pasó. Los workflows históricos/logs no se convierten en estado actual.

## Navegación histórica local

Evidencia preservada por proceso; cada catálogo enlaza sus documentos históricos individualmente y no es una autoridad operativa.

- [C03 integrado: sesiones, invitación y recuperación](../catalogos_historicos/c03_integrado.md#documentos-preservados)
- [Admin, autenticación e historia editorial](../catalogos_historicos/admin_auth_editorial.md#documentos-preservados)
- [Pipeline, datos y base de datos](../catalogos_historicos/pipeline_base_datos.md#documentos-preservados)
- [Infraestructura, seguridad y CI](../catalogos_historicos/infra_seguridad_ci.md#documentos-preservados)
- [Documentación, trazabilidad y transferencia](../catalogos_historicos/documentacion_trazabilidad.md#documentos-preservados)
- [Registros operativos históricos y JIT](../catalogos_historicos/operacion_jit.md#documentos-preservados)
- [Seguimiento y handoffs históricos](../catalogos_historicos/seguimiento_historico.md#documentos-preservados)
- [C03 — diagnóstico de arranque de runtimes locales](../catalogos_historicos/c03_inicio_runtime.md#documentos-preservados)
- [C03 — diagnósticos Docker, F1 y clasificadores](../catalogos_historicos/c03_diagnosticos_runtime.md#documentos-preservados)
