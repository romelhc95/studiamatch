# Flujo recurrente de requerimientos y entregas

## Objetivo
Estandarizar el ciclo desde que el cliente envía un requerimiento hasta la entrega del hito aprobado, evitando atrasos y cambios de alcance no controlados.

## Flujo obligatorio

| Paso                  | Responsable                          | Entrada                                                                | Salida                                          | Regla de control                                                                       |
| --------------------- | ------------------------------------ | ---------------------------------------------------------------------- | ----------------------------------------------- | -------------------------------------------------------------------------------------- |
| 1. Recepcion          | Usuario/PM                           | Documento, correo, audio transcrito o referencias visuales del cliente | Carpeta `requerimientos/YYYYMMDD/`              | Todo insumo del cliente queda versionado o referenciado antes de estimar.              |
| 2. Contexto           | IA estimadora                        | `.context/00_INDICE.md`, prompt base y arquitectura relevante          | Contexto tecnico vigente                        | Si hay discrepancia entre `.context` y codigo, se reporta antes de cotizar.            |
| 3. Estimacion         | `tech-estimator`                     | Requerimiento + referencias + matriz de precios                        | `.context/estimaciones/est_XXX.md`              | Usar `_plantilla_estimacion.md`; no crear tareas todavia.                              |
| 4. Cotizacion cliente | Usuario/PM                           | `est_XXX.md` aprobado internamente                                     | DOCX/PDF en `requerimientos/YYYYMMDD/`          | El formato comercial debe replicar `EstimacionStudIAMatch_05072026.docx`.              |
| 5. Aprobacion         | Cliente + Usuario/PM                 | Cotizacion enviada                                                     | Estado aprobado/rechazado en `est_XXX.md`       | Sin aprobacion no hay backlog ni ejecucion.                                            |
| 6. Creacion de tareas | IA implementadora + skill asignada   | Estimacion aprobada                                                    | Archivos en `.context/backlog_tareas/`          | Una tarea por paquete/hito; incluir CAs, fechas, skill principal, sub-especialidad, revisor y entregable. |
| 7. Ejecucion          | Skill principal asignada             | Tareas aprobadas por fase                                              | Cambios en rama `feat/*`                        | Solo ejecutar cuando el usuario apruebe la fase correspondiente.                       |
| 8. Validacion         | Skill principal + `security-auditor` | Cambios implementados                                                  | Evidencia de lint/typecheck/py_compile/security | Todo corre en contenedor `studiamatch-dev`; security-auditor antes de commit/PR.       |
| 9. Entrega interna    | IA implementadora                    | Cambios validados                                                      | PR a `desarrollo`                               | No mezclar estructura/contexto con implementacion funcional si son alcances distintos. |
| 10. Entrega cliente   | Usuario/PM                           | Hito desplegado/validado                                               | Conformidad y saldo contra entrega              | Se entrega por hito, no por tarea tecnica individual.                                  |

## Regla de plazos
- Las fechas de la estimacion aprobada son contractuales.
- Cada tarea debe incluir `fecha_inicio`, `fecha_limite` y `despliegue`.
- Si una dependencia amenaza el plazo, se reporta el mismo dia y se documenta en la tarea.
- No se mueve una fecha sin aprobacion explicita del usuario y actualizacion de la estimacion/tarea.

## Responsables

| Rol | Responsabilidad |
|---|---|
| Cliente | Aprueba cotizacion, alcance y conformidad del hito. |
| Usuario/PM | Decide prioridades, aprueba fases, comunica con cliente y acepta entregas internas. |
| `tech-estimator` | Extrae requerimientos, segmenta paquetes, calcula precio cerrado, calendario y riesgos contractuales. |
| IA implementadora | Crea tareas, implementa cambios y registra evidencia, usando la skill principal asignada por tarea. |
| security-auditor | Revisa cambios antes de commit/PR, especialmente secrets, RLS, auth y entradas. |

## Matriz de skills y sub-especialidades

| Momento del flujo | Skill/agente principal | Sub-especialidad sugerida | Cuándo usarla | Entregable esperado |
|---|---|---|---|---|
| Estimacion comercial/técnica | `tech-estimator` | Arquitectura StudIAMatch + matriz contractual | Siempre que llegue un nuevo requerimiento del cliente | `est_XXX.md` con paquetes, CAs, precio cerrado, cronograma y riesgos. |
| Seguridad/gate final | `security-auditor` | Secrets, RLS, auth, input validation, exposición de datos | Siempre antes de commit/PR y cuando haya DB, admin, leads o integraciones | Reporte de hallazgos y remediaciones requeridas. |
| Frontend/UI | `frontend-architect` | Next.js 16, React 19, Tailwind v4, shadcn/base-nova | Home, resultados, cards, admin UI, formularios, responsive | Componentes/rutas consistentes con mockups y sistema visual. |
| Accesibilidad | `accessibility` | WCAG 2.2, teclado, screen reader, contraste | Formularios, navegación, cards interactivas, admin | Checklist a11y y correcciones necesarias. |
| SEO | `seo` | Metadata, JSON-LD, rutas estáticas, contenido indexable | Home, resultados, detalle, cambios de rutas o contenido público | Checklist SEO y ajustes de metadata/estructura. |
| Python pipeline | `pipeline-engineer` | Python 3.11, harvester, cleansing, enrichment, sync, db_client | Cambios en `scripts/core`, ETL o reglas de parsing | Código Python mantenible y validado con `py_compile`. |
| Testing/QA | `qa-test-engineer` | Pytest, regresiones, validación frontend, matriz CA | Cuando un hito necesite evidencia repetible o go/no-go | Matriz de pruebas, evidencias y riesgos residuales. |
| Datos/algoritmos | `data-quality-analyst` | Métricas, ROI, categorías, scoring, calidad de datos | Reglas de ranking, métricas, auditorías, umbrales | Criterios cuantitativos y validación de datos. |
| DevOps/CI/CD | `devops-release-manager` | GitHub Actions, Cloudflare Pages, Docker, ramas | Workflows, despliegues, sincronización de rama, scripts de CI | Cambios operativos con validación en contenedor. |
| Supabase/DB | `supabase-architect` + `security-auditor` | PostgreSQL 15, RLS, RPC, PostgREST, migrations | Migraciones, RPC, políticas, tablas, grants | SQL versionado, validación RLS y revisión de seguridad. |

## Regla de asignacion de skill por tarea

- Los agentes viven globalmente en `~/.config/opencode/agents/` para evitar versionarlos en git.
- Este repo no debe crear `.opencode/agents/` salvo aprobacion explicita.
- La especializacion por proyecto se define en `.context/`, no dentro de los agentes globales reutilizables.
- Cada tarea debe declarar `skill_principal`, `subespecialidad`, `skills_apoyo` y `gate_obligatorio`.
- Si el cambio toca más de un dominio, la skill principal corresponde al mayor riesgo técnico y las demás van como apoyo.
- Si toca Supabase, RLS, auth, secrets, leads, admin o endpoints, `security-auditor` es obligatorio aunque no sea la skill principal.
- Si toca UI pública, usar `frontend-architect` y agregar `accessibility`; si afecta indexación o rutas públicas, agregar `seo`.
- Si toca pipeline Python, usar `pipeline-engineer`; si el cambio puede romper lógica histórica, agregar `qa-test-engineer`.
- Si toca métricas, ROI, ranking, calidad de datos o criterios cuantitativos, usar `data-quality-analyst`.
- Si toca CI/CD, ramas, Docker, Cloudflare o GitHub Actions, usar `devops-release-manager`.
- Si toca PostgreSQL, RLS, RPC, PostgREST o migraciones, usar `supabase-architect` y `security-auditor`.
- Si no existe una skill especializada para el dominio, usar `general` y registrar la sub-especialidad concreta.
- El dispatcher asistivo vive en `scripts/maintenance/agent_dispatcher.py` y esta documentado en [[agent_dispatcher]]. En `mode=implementation` define roles de desarrollo solo para la tarea/hito aprobado; en `mode=review` sugiere handoffs SDLC desde `release_gate.py`.
- Si el dispatcher detecta una tarea pendiente, hito distinto o archivos fuera del alcance declarado, debe devolver `NO_GO` y no se implementa.

## Sub-especialidades técnicas estándar

| Sub-especialidad | Archivos típicos | Validaciones mínimas |
|---|---|---|
| Frontend Next.js 16 + React 19 | `web/src/app/**`, `web/src/components/**` | `npm run lint`, `npx tsc --noEmit`, revisión responsive si aplica. |
| UI/UX mockups aprobados | `HomeContent.tsx`, cards, CSS global | Comparación contra HTML/mockup aprobado y revisión mobile. |
| Supabase PostgreSQL/RLS/RPC | `db/migrations/**`, `.context/sistema_db_supabase.md` | Revisión de RLS, grants, migración idempotente y security-auditor. |
| Pipeline Python ETL | `scripts/core/**`, `scripts/shared/**` | `python3 -m py_compile`, pruebas con datos controlados si aplica. |
| GitHub Actions/Cloudflare | `.github/workflows/**`, config deploy | Validación YAML, secrets por environment, no hardcodear credenciales. |
| Datos/ROI/categorías | auditorías, reglas, salary/category logic | Verificación de supuestos, conteos y regresiones de datos. |

## Politica de backlog
- El backlog nace solo desde una estimacion aprobada.
- Cada paquete comercial debe mapearse a una o mas tareas tecnicas.
- La tarea debe ser suficientemente detallada para ejecutarse sin reinterpretar el documento comercial.
- Cada tarea debe incluir skill principal, sub-especialidad, skills de apoyo y gate obligatorio.
- Las tareas no reemplazan la estimacion; la estimacion es la fuente contractual.

## Politica de git
- La estructura documental (`.context`, `requerimientos`, `desestimado`) debe subirse separada de cambios funcionales.
- Las implementaciones aprobadas se hacen en ramas `feat/*` desde `desarrollo`.
- Las ramas permanentes son `desarrollo`, `certificacion` y `main`; las demas ramas son temporales y deben cerrarse o eliminarse tras merge, reemplazo o desestimacion documentada.
- Si `desarrollo` esta divergente frente a remoto, se resuelve la sincronizacion antes de push.
- No se hace push si hay riesgo de mezclar cambios no revisados o ajenos.
- Los scripts de prueba de ejecucion unica, diagnostico local o backfill excepcional no se suben a GitHub; se conservan en `desestimado/` o `scripts/local/` si hace falta retenerlos localmente.

## Checklist antes de iniciar una fase aprobada
- [ ] Estimacion aprobada y actualizada.
- [ ] Tareas creadas con CAs, fechas y entregables.
- [ ] `agent_dispatcher.py --mode implementation` ejecutado contra la tarea aprobada y el hito autorizado.
- [ ] Rama base sincronizada.
- [ ] Alcance de la fase confirmado por el usuario.
- [ ] Riesgos de seguridad identificados.
- [ ] Validaciones previstas definidas.
