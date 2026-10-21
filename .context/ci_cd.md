# CI/CD, release y promoción

## Workflows locales

| Archivo | Triggers declarados | Jobs/responsabilidad | Estado real |
|---|---|---|---|
| security-audit.yml | pull_request, push, workflow_dispatch | credenciales, protected paths, Python, ESLint, TypeScript, static build, actionlint/ShellCheck, DB gate, agregador security-audit | YAML del candidato; instalación/required check remoto sin verificar. |
| protected-workflow-integrity.yml | pull_request_target, pull_request_review | revisión de cambios a workflows protegidos usando base confiable | Declarado local; enforcement remoto no verificado. |
| production_pipeline.yml | schedule diario UTC, workflow_dispatch | preflight y FG2 harvest/cleanse/enrichment/sync/audit | Cron definido; ejecución actual desconocida. |
| fg1_inventory.yml | schedule mensual UTC, workflow_dispatch | preflight e inventario institucional | Cron definido; ejecución actual desconocida. |
| fg3_integrity.yml | schedule diario UTC, workflow_dispatch | preflight e integrity ping | Cron definido; ejecución actual desconocida. |
| production_canary.yml | workflow_dispatch | canary acotado y manifiestos/estado | Manual, requiere inputs/aprobación de ambiente; no ejecutado aquí. |
| db-sync-to-pro.yml | workflow_dispatch | detect/report/apply/verify schema/migrations | apply requiere autorización DDL/JIT; no ejecutado aquí. |
| opencode.yml | issue_comment, pull_request_review_comment | integración OpenCode según condiciones YAML | Config local; uso remoto no comprobado. |

Workflows FG llaman .github/scripts/production_control_preflight.sh antes de los writers y solo continúan con allow_writer. Sus ramas/ref/environment son expresiones del YAML, no prueba de branch protection ni de schedule instalado. Permissions local más visible: contents: read; security audit añade actions: read y workflow-integrity pull-requests: read. Revisar permisos completos por job cuando se cambie.

`db-sync-to-pro.yml` instala `requirements-db-migrate.txt` con `pip install --require-hashes` en tres pasos; ese lock específico queda descrito en [tecnologías](tecnologias.md). La definición versionada del workflow no acredita que haya corrido ni que una migration se haya aplicado. Los cinco `.github/commands/*.toml`, como [`gemini-invoke.toml`](../.github/commands/gemini-invoke.toml), son prompts de Gemini auxiliares y no se referencian como jobs/triggers en los workflows inspeccionados; su invocación desde herramientas/personas no está comprobada.

## Guías auxiliares `.github/agents/`

El candidato contiene 19 perfiles Markdown versionados, clasificados por propósito: diseño/API/backend (`api-designer`, `architect-hexagonal`, `backend-architect`, `frontend-architect`, `mobile-architect`); datos y runtime (`data-analyst`, `db-migrator`, `python-expert`); entrega y control (`devops-engineer`, `health-monitor`, `planner`, `sdlc-chief`, `tech-evaluator`, `researcher`, `doc-writer`, `code-cleaner`, `tdd-coder`, `qa-engineer`, `security-auditor`). Se revisaron workflows/scripts locales y no se encontró un consumidor que los ejecute como jobs; su invocación por personas o plataforma y su actividad actual son desconocidas. Son guías versionadas, no evidencia de agentes activos, permisos efectivos ni controles ejecutados.

Los comandos en `.github/commands/` y habilidades en `.agents/skills/` tienen el mismo límite: material auxiliar versionado, sin consumidor local confirmado; se preservan y su uso por clientes/plataformas queda desconocido. La asignación exacta está en el [registro canónico](trazabilidad/registro_fuentes_componentes.md#asignaciones-por-fuente); la decisión de retirar mapas redundantes consta en la [evidencia de consolidación R11](evidencia/h3req1_documentacion_consolidacion_trazabilidad_2026-10-13_r11.md).

## Publicación de Cloudflare Pages

`AGENTS.md` declara el mapeo `main` → `studiamatch.com` y `desarrollo` → `studiamatch.pages.dev`. El inventario de `.github/workflows/` del candidato no contiene un job Pages/deploy; `web/next.config.js` configura static export, que por sí solo no publica el artefacto. Por tanto, el mapeo es una declaración de guía/configuración del proyecto, no evidencia del mecanismo instalado ni de adopción remota actual. Antes de R15 no se habían consultado los proyectos Pages. R15 inventarió dominios del proyecto, refs/deployments y nombres/tipos de bindings; no leyó reglas de caché, DNS fuera del proyecto ni toda la configuración de deployment. G10/Development debe cotejarlos por ambiente y SHA.

### Lectura remota R15

GitHub `main` es default; `desarrollo` estaba en el baseline R14 `4eb4d877a50b012bb630a129bd0c74482c33be9c`, no en el WIP completo. Se observaron los rulesets y runs descritos en la [evidencia R15](evidencia/h3req1_g10_remote_preparation_2026-10-13_r15.md#github). El endpoint de branch protection devolvió 403; approvals y required checks quedan **desconocidos**, aunque branch y ruleset indiquen protección. `desarrollo` y `main` listan siete workflows; `protected-workflow-integrity.yml` está en el candidato local, pero no en esas listas remotas. No se ejecutaron workflows ni se infiere enforcement de los resultados históricos.

Cloudflare Pages `studiamatch` mostró production `main` en SHA `70d0f4fe…` y un preview `desarrollo` en SHA `4eb4d877…`; ninguno incorpora el WIP R14. Los dominios del proyecto y sus límites de alcance están en [R15](evidencia/h3req1_g10_remote_preparation_2026-10-13_r15.md#cloudflare-pages-worker-y-durable-object). La presencia de `NEXT_SUPABASE_SECRET_KEY` como `plain_text` y los bindings BFF/Worker ausentes bloquean preparación; no se leyó ningún valor.

## Ramas y controles

Git flow declarado: feat/docs → PR a desarrollo → PR a certificacion → PR a main, con revisión y required security-audit según reglas de AGENTS.md. R15 consultó refs, rulesets, check-runs, status, workflows y runs; el endpoint de branch protection devolvió 403, por lo que approvals y required checks efectivos siguen desconocidos. No se leyeron secrets ni environments. No inferir controles efectivos por YAML o commits locales.

## Stage 1 / Stage 2 H3REQ1

La evidencia R181/R182 deja Stage 1 como workflow local existente y validado por acción local actionlint; Stage 2 permanece como patch separado/inactivo hasta instalación PWI y verificaciones remotas. No afirmar que Stage 2 esté merged/instalado ni correr workflow_dispatch.

R180 documenta actionlint Stage 1 y transición 9/9; R182 documenta scope/scanner 92/92 sobre snapshot R8. Son inputs de R8, no resultado R9. R13 agrega las rutas exactas que faltaban para su paquete a `allowed_h3_local`; `tests/test_protected_path_scope_guard.sh` lee el manifiesto de paquete y comprueba que cada path cambiado del scope y cada artefacto incluido coincide con las expresiones o la lista literal del workflow. El test forma parte del job local `python-check`. R14 acredita en Docker `actionlint` v1.7.12 en todos los workflows y `ShellCheck -x` 0.11.0 en los dos scripts focales; el barrido de 181 scripts históricos tuvo diagnósticos y no se limpió en bloque. No se repiten esas validaciones intactas. GitHub remoto no ejecutó el WIP R14. Para cada cambio futuro, actualiza registro, manifiesto, allowlist y prueba por impacto; los tests locales no acreditan Actions o branch protection activos.

## Promoción expand → compatibilidad → deploy → contract

1. Expandir schema/contrato manteniendo lectores y writers legacy necesarios; migration idempotente y rollback específico.
2. Validar coexistencia en fixture y ambiente objetivo mediante permiso separado.
3. Deploy de consumidor/configuración y observación de evidencia en ese ambiente.
4. Contract solo tras compatibilidad y estabilidad, retirando legacy bajo gate y rollback.

La ruta no autoriza DB Sync, workflows, deploys, schedules, secrets ni grants. H3 local R178 comprobó código/build y fixtures; no desplegó ni contrajo remoto. La [preparación R15](evidencia/h3req1_development_integration_package_2026-10-13_r15.md) deja las fases y rollback listos para revisión, pero Free inactivo, schema discrepante y bindings ausentes impiden empezar integración/UAT. Cada acción futura requiere su instrucción separada.

## PR

R8 sigue antecedente inmutable con sus resultados. R14 permanece como paquete/revisión local antecedente. El [borrador R15](evidencia/h3req1_pr_body_draft_local_review_2026-10-13_r15_remote_prep.md), basado en [.github/pull_request_template.md](../.github/pull_request_template.md), registra la preflight y el NO-GO remoto; no está listo para filing y no se abrió PR.

## Fuentes

.github/workflows/*.yml, .github/scripts/production_control_preflight.sh, .github/pull_request_template.md, `web/next.config.js`, `AGENTS.md` (mapeo de refs/host), `.githooks/`, `scripts/security/`, evidencia R178/R180/R181/R182 y [lecturas GitHub/Pages R15](evidencia/h3req1_g10_remote_preparation_2026-10-13_r15.md). Protecciones completas, required checks, CI del WIP, DNS fuera del proyecto Pages y publicación del WIP siguen desconocidos/no verificados.

## Navegación relacionada

[Infraestructura/release](componentes/infra_release.md) · [Seguridad](seguridad.md) · [Pruebas](pruebas.md) · [Operación](operacion.md) · [Arquitectura](arquitectura.md) · [ADR-0028](decisiones/ADR-0028_target_release_governance.md) · [H3REQ1](hitos/README.md) · [Evidencia R181/R182](evidencia/h3req1_g10_r8_review_corrections_r181_2026-10-12.md) · [Índice](indice.md)

Registro por fuente: [infraestructura y release](trazabilidad/registro_fuentes_componentes.md#infraestructura-y-release).
