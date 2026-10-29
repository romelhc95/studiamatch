# Tecnologías, versiones y runtimes

> Las versiones se extraen de manifests/config local y pueden diferir del entorno remoto. Una dependencia declarada no demuestra que el runtime remoto use esa versión.

| Herramienta | Propósito | Versión/rango acreditado | Fuente |
|---|---|---|---|
| Node.js | desarrollo/build Next, tooling local y tests JS | imagen Docker node:20-bookworm; no implica versión exacta de patch | Dockerfile, web/package.json. |
| Next.js | frontend App Router y export estático | 16.3.8 | web/package.json, web/package-lock.json. |
| React / React DOM | interfaz | 19.2.4 | web/package.json, lock. |
| TypeScript | fuentes TS/TSX y chequeo | ^5; lock resuelve paquete exacto | web/package.json, lock. |
| ESLint / config Next | lint | ESLint ^9, config Next ^16.2.1 | web/package.json, web/eslint.config.mjs. |
| Tailwind CSS | estilos | ^4; plugin PostCSS ^4 | web/package.json, lock. |
| Supabase JS / SSR | clientes públicos y manejo de sesión | @supabase/supabase-js 2.109.0; @supabase/ssr 0.10.0 | web/package.json, lock. |
| Python | pipeline, mantenimiento y tests contractuales | Python 3.11 declarado por imagen y locks de pip-tools | Dockerfile, requirements-pipeline.txt. |
| Python pipeline | HTTP, HTML, navegador, parsing y DB | dependencias fijadas con hashes en requirements-pipeline.txt; lista fuente en requirements.txt | requirements*.txt, Dockerfile. |
| Python DB migration | Entorno controlado del workflow db-sync-to-pro | requirements-db-migrate.txt: requests/python-dotenv y dependencias transitivas fijadas con versiones y hashes; Python minor según runner del workflow | .github/workflows/db-sync-to-pro.yml (3 instalaciones con `pip install --require-hashes`), requirements-db-migrate.txt. No demuestra que el workflow se haya ejecutado. |
| Playwright Chromium | scraping de sitios que lo requieren y pruebas de navegador | Chromium instalado durante la imagen Docker; build exacto no está versionado en esta documentación | Dockerfile, requirements-pipeline.txt. |
| PostgreSQL | almacenamiento administrado por Supabase | versión operativa no comprobada aquí; PG17 aparece como fixture desechable | AGENTS.md, tests/sql/*pg17*, harnesses. |
| pgvector | extensión declarada por el baseline local | disponible en SQL fuente; activación remota no comprobada | db/restore_full_schema.sql, migraciones. |
| Cloudflare Pages | hosting del export y Pages Functions | refs/deployments/hosts y nombres/tipos de bindings consultados en R15; producción activa del WIP no acreditada | web/next.config.js, web/functions/; [evidencia R15](evidencia/h3req1_g10_remote_preparation_2026-10-13_r15.md#cloudflare-pages-worker-y-durable-object). |
| Cloudflare Workers / Durable Objects | contador/cuota interno para Admin | compat date 2026-07-30 en wrangler; clase AdminQuotaCounter | workers/admin-quota/wrangler.jsonc, workers/admin-quota/index.ts. |
| GitHub Actions | workflows de CI, pipeline y operaciones controladas | definición YAML en candidato; instalación, schedules y required checks remotos desconocidos | .github/workflows/*.yml. |
| Proveedor LLM | extracción estructurada de datos | En el código candidato, OpenCode-compatible endpoint con DeepSeek v4 Flash y después Cloudflare Workers AI con Meta Llama 3.1 8B; proveedor real disponible y fallback ejecutado no se verificaron | scripts/core/enrichment_worker.py (EnrichmentWorker.__init__, _call_deepseek, _call_cloudflare). |
| `braces` local | Paquete npm vendorizado fijado para el build actual | `3.0.4-h3.1` es una versión local, no un release upstream; fuente fijada al commit `28d440b5dd449dbf1fe6f3506cf94ecca4d02660`; SHA-256 del tarball `a8c0b0223dc788781252f9b056207b5b053b8dd0896da861c305769b472f0819` | [`web/vendor/README.md`](../web/vendor/README.md), `web/package.json`, `web/package-lock.json`. |
| Configuración UI `web/components.json` | base Nova, React Server Components, TSX, Tailwind CSS y alias del proyecto para componentes/utilidades | Archivo local; el generador y sus paquetes pertenecen a web/package.json/lock; el archivo no declara una versión propia | web/components.json, web/package.json, web/src/components y web/src/lib. |

## Dependencias y locks

- web/package.json y web/package-lock.json son el contrato JS; Docker usa npm ci.
- requirements.txt enumera dependencias directas, varias sin pin. Los locks con hashes (requirements-pipeline.txt y variantes de FG/DB migration) son los artefactos reproducibles usados por workflows/Docker cuando la ruta los referencia.
- mock-server/package.json y lock describen un runtime fixture separado.
- [`requirements-db-migrate.txt`](../requirements-db-migrate.txt) es el lock hash-pinned que [`db-sync-to-pro.yml`](../.github/workflows/db-sync-to-pro.yml) instala en sus tres pasos de setup; se conserva separado del lock de pipeline. [`.dockerignore`](../.dockerignore), [`.editorconfig`](../.editorconfig), [`.gitattributes`](../.gitattributes) y [`.gitignore`](../.gitignore) configuran respectivamente el contexto Docker, editor, atributos y exclusiones Git. `.actrc` fue inventariado pero su contenido no se inspeccionó por ser configuración local potencialmente sensible.
- [`.github/commands/gemini-invoke.toml`](../.github/commands/gemini-invoke.toml), [perfil `.github/agents/doc-writer.md`](../.github/agents/doc-writer.md), [guía `.agents/skills/accessibility/SKILL.md`](../.agents/skills/accessibility/SKILL.md) y [patrones WCAG relacionados](../.agents/skills/accessibility/references/WCAG.md) representan prompts, perfiles y guías auxiliares; no se encontraron callsites locales desde workflows/scripts. No acreditan ejecución ni control activo de agentes externos. Las asignaciones están en el [registro canónico](trazabilidad/registro_fuentes_componentes.md#asignaciones-por-fuente); el tratamiento de mapas anteriores queda en la [evidencia R11](evidencia/h3req1_documentacion_consolidacion_trazabilidad_2026-10-13_r11.md).
- `.context/.obsidian/` contiene preferencias locales del vault; se preservan en el backup y se excluyen del paquete compartido. Su clasificación está en el [registro de fuentes](trazabilidad/registro_fuentes_componentes.md#descubrimiento-y-exclusiones).
- [`web/components.json`](../web/components.json) configura el generador UI local; los componentes resultantes y alias se documentan por separado de rutas y contratos runtime.
- No actualizar dependencias solo a partir de esta documentación. El lock debe cambiar junto al manifest y las validaciones afectadas.

## Build, pruebas y despliegue

- Desarrollo local: studiamatch-dev ejecuta Next en Linux; Docker también instala Python y Chromium.
- Build web: next build con output: export; el script limpia .next y out antes de construir. El static build puede leer Supabase al generar rutas. No usar como prueba de schema remoto.
- Frontend runtime de producción: archivos estáticos y Pages Functions, no SSR Node.
- Backend: Supabase PostgreSQL/Auth/PostgREST/Edge Function y Worker de cuota como runtimes separados.
- Pipeline: scripts Python invocados por GitHub Actions; servicios externos según configuración privada del ambiente.

## Excepciones y deuda documentada

web/next.config.js conserva typescript.ignoreBuildErrors: true, excepción para un problema de combinación Next/React registrado en el proyecto. El typecheck separado sigue siendo un gate. La extensión TypeScript de los módulos es .mjs solo para JavaScript con módulos; no existe convención .msj. El campo courses.embedding y el nombre sync_vector_worker.py no prueban búsqueda vectorial activa; revisar su código antes de afirmar uso de embeddings.

### Dependencia local `braces`

El `package.json` y su lock resuelven `braces` desde `file:vendor/braces-3.0.4-h3.1.tgz`; `npm ci` depende de ese artefacto local. El README del vendor registra el snapshot del cambio propuesto en PR upstream #72, desde el commit fijado arriba; su afirmación “abierto” pertenece al corte 2026-10-03. R15 verificó que el PR está cerrado/no merged y que el metadata npm oficial consultado declara `3.0.3`; el paquete local no es un release upstream. La comparación de árboles dio 9/10 archivos idénticos y la única diferencia restante fue el número de versión en `package.json`. Ver [evidencia R15](evidencia/h3req1_g10_remote_preparation_2026-10-13_r15.md).

El reporte de 904 tests corresponde a la suite upstream ejecutada históricamente en Docker; no es resultado de tests de StudIAMatch ni evidencia de una auditoría completa del tarball. R15 decide mantener el snapshot y lock sin modificación para este paquete porque el PR fuente no se merged y no se verificó un release oficial equivalente. No es un waiver ni un release. Cambiarlo requiere decisión separada, lock nuevo y validaciones por impacto. El [manifiesto R14](evidencia/h3req1_pr_scope_manifest_2026-10-13_r14_reconciled.json) conserva a Romel como owner y `2026-11-03` como revisión prevista; R15 no modifica ese follow-up. La integración Development sigue bloqueada por E0–E5, no por volver a investigar la procedencia de `braces`.

### Conflicto documental de proveedores

AGENTS.md y notas previas describen Cloudflare → GitHub → Gemini. El código de EnrichmentWorker del candidato actual construye solo DeepSeek por el endpoint OpenCode-compatible y Cloudflare. Este corte registra la diferencia como contradicción de fuentes: implementación candidata observada en código; runtime/provider remoto desconocido. No asumir el orden histórico como vigente ni corregir/provisionar proveedores como parte de esta documentación.

## Fuentes

Dockerfile, docker-compose.yml, web/package.json, web/package-lock.json, web/next.config.js, requirements*.txt, workers/admin-quota/wrangler.jsonc, supabase/config.toml, .github/workflows/. La estructura es candidata local; estado de deploy/versiones remotas: desconocido.

## Navegación relacionada

[Frontend](frontend.md) · [Backend](backend.md) · [Componentes de infraestructura](componentes/infra_release.md) · [Operación](operacion.md) · [CI/CD](ci_cd.md) · [Pruebas](pruebas.md) · [Decisiones](decisiones/README.md) · [Índice principal](indice.md)

Registro por fuente: [infraestructura y release](trazabilidad/registro_fuentes_componentes.md#infraestructura-y-release).
