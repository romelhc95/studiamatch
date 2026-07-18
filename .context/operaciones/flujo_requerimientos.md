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
| 6. Creacion de tareas | IA implementadora + skill asignada   | Estimacion aprobada + requerimiento fuente                             | Archivos en `.context/backlog_tareas/`          | Una tarea por paquete/hito; primero mapear CAs contra secciones del requerimiento fuente, analizar codigo/schema actual y luego documentar subtareas con cambio exacto, fechas, skill, validaciones, evidencia, revisor y entregable. |
| 6b. Refinamiento tecnico | `task-refiner`/IA implementadora + skill principal del dominio | Tareas creadas + requerimiento fuente + arquitectura vigente | Tareas listas para ejecucion | Gate obligatorio antes de HITO 1 o cualquier fase: completar `Analisis tecnico previo obligatorio`, `Especificacion exacta del cambio` y subtareas con `Analisis previo`, `Cambio exacto`, archivos, CAs y validacion. No toca codigo funcional. |
| 6c. Diseno de pruebas por CA | `qa-test-engineer` + skill principal del dominio | Tarea refinada + CAs + especificacion exacta | Matriz CA -> prueba -> evidencia | Antes de ejecutar, cada CA debe tener al menos una prueba concreta, resultado esperado y evidencia requerida. Si no se puede probar, se refina la tarea antes de tocar codigo. |
| 7. Ejecucion          | Skill principal asignada             | Tareas refinadas y aprobadas por fase                                  | Cambios en rama `feat/*`                        | Solo ejecutar cuando el usuario apruebe la fase correspondiente.                       |
| 8. Validacion         | Skill principal + `security-auditor` | Cambios implementados                                                  | Evidencia de lint/typecheck/py_compile/security | Todo corre en contenedor `studiamatch-dev`; security-auditor antes de commit/PR.       |
| 8b. Informe de cumplimiento | IA implementadora + QA/PM | Cambios validados + tarea + CAs + evidencias | `.context/evidencias/hito_X_informe_cumplimiento.md` | Se genera antes de PR/listo para entrega. Debe ser entendible para cliente y mapear CA -> cambio -> evidencia. |
| 8c. Gate mecanico de cierre | IA implementadora + `qa-test-engineer` | Tarea + informe + changelog + diff + artefactos versionados | `validate_hito_close.py --hito N` OK | Obligatorio antes de declarar listo para PR. Si falla, el hito queda `observado` y se corrigen artefactos o se refinan subtareas. |
| 8d. Gate de conformidad | QA/PM + skill principal + `security-auditor` si aplica | Diff real + informe + tarea + requerimiento fuente + resultado del gate mecanico | Veredicto GO/NO-GO | Si los cambios no coinciden con requerimiento/CAs o la evidencia no coincide con artefactos versionados, NO se toca mas codigo: se refina la tarea/subtareas y el hito queda `observado`. |
| 9. Entrega interna    | IA implementadora                    | Cambios validados + informe de cumplimiento                            | PR a `desarrollo`                               | No mezclar estructura/contexto con implementacion funcional si son alcances distintos. |
| 10. Entrega cliente   | Usuario/PM                           | Hito desplegado/validado + informe                                     | Conformidad y saldo contra entrega              | Se entrega por hito; el informe puede compartirse en Notion como vista cliente.        |

> Para hitos con fechas de entrega distintas o desarrollo paralelo, aplicar tambien `operaciones/flujo_hitos_release.md`: el entregable se congela en `release/hito-N` y no se promueve `desarrollo` completo si contiene cambios de hitos futuros.

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
| `task-refiner` / backlog architect | Convierte una estimacion aprobada en tareas tecnicas ejecutables, trazadas a requerimiento fuente, sin tocar codigo funcional. Si no existe como skill/agente dedicado, lo asume la IA implementadora usando la skill principal de cada dominio. |
| IA implementadora | Crea tareas, implementa cambios y registra evidencia, usando la skill principal asignada por tarea. |
| QA/PM de evidencia | Revisa que el informe sea entendible para cliente, no exponga detalles sensibles y conecte cada CA con evidencia verificable. |
| security-auditor | Revisa cambios antes de commit/PR, especialmente secrets, RLS, auth y entradas. |

## Matriz de skills y sub-especialidades

| Momento del flujo | Skill/agente principal | Sub-especialidad sugerida | Cuándo usarla | Entregable esperado |
|---|---|---|---|---|
| Estimacion comercial/técnica | `tech-estimator` | Arquitectura StudIAMatch + matriz contractual | Siempre que llegue un nuevo requerimiento del cliente | `est_XXX.md` con paquetes, CAs, precio cerrado, cronograma y riesgos. |
| Refinamiento de tareas | `task-refiner` / skill principal del dominio | Backlog tecnico ejecutable + trazabilidad CA | Siempre despues de aprobar `est_XXX.md` y antes de ejecutar cualquier fase | `tarea_XXX.md` con fuentes, matriz CA, alcance, analisis previo, especificacion exacta, subtareas, validaciones y evidencia. |
| Diseno de pruebas por CA | `qa-test-engineer` + skill principal del dominio | Criterios de aceptacion + especificacion exacta | Antes de ejecutar una fase | Matriz `CA -> prueba -> resultado esperado -> evidencia`, lista para ejecutarse al cierre. |
| Informe de cumplimiento | `qa-test-engineer` / IA implementadora + Usuario/PM | Evidencia tecnica traducida a lenguaje cliente | Al cerrar cada hito, despues de validaciones y antes de PR/entrega interna | `.context/evidencias/hito_X_informe_cumplimiento.md` listo para compartir o copiar a Notion. |
| Gate mecanico de cierre | `qa-test-engineer` / IA implementadora | Tarea, informe, changelog, diff y artefactos versionados | Antes de marcar listo para PR | `docker exec studiamatch-dev python3 scripts/maintenance/validate_hito_close.py --hito X` con salida GO. |
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
- `tech-estimator` no ejecuta este refinamiento: su salida es contractual/comercial. El refinamiento lo hace `task-refiner` o la IA implementadora con la skill principal del dominio.
- Ninguna fase puede iniciar si su tarea no paso el gate de refinamiento tecnico.
- Cada tarea debe incluir skill principal, sub-especialidad, skills de apoyo y gate obligatorio.
- Cada tarea debe separar `Alcance incluido` y `Alcance excluido` para evitar sobre-implementacion.
- Cada tarea debe declarar `Fuentes del requerimiento`: documento aprobado, secciones exactas y mockups/referencias aplicables.
- Cada tarea debe incluir `Matriz CA -> detalle implementable` para que el desarrollador no trabaje solo desde el titulo del CA.
- Cada tarea debe contener `Analisis tecnico previo obligatorio` antes de la implementacion.
- Cada tarea debe contener `Especificacion exacta del cambio`; no se aceptan frases genericas como "agregar campos necesarios" sin detallar que campos son.
- Cada tarea debe contener `Matriz CA -> pruebas/evidencia`; no se acepta ejecutar un hito si un CA no tiene prueba y evidencia esperada.
- Si el requerimiento define nuevos datos criticos, esos datos sustituyen conceptos internos legacy en el backlog operativo, aunque la arquitectura historica mencione otros nombres.
- Cada subtarea tecnica debe incluir analisis previo, objetivo, cambio exacto, archivos esperados, CA relacionado y validacion concreta.
- Si toca DB/Supabase, la subtarea debe indicar tabla, columna, tipo, nullability, default, checks, indices, RLS/RPC/grants, migracion esperada y si hay backfill o no.
- Si toca frontend, la subtarea debe indicar ruta, componente, estado/props, eventos, fetch/query, copy, responsive y criterio visual esperado.
- Si toca pipeline Python, la subtarea debe indicar archivo, funcion/bloque, input, output, normalizacion, escritura destino y manejo de errores.
- Si toca CI/CD, la subtarea debe indicar workflow, trigger, job, environment, secrets, condiciones y validacion.
- Cada tarea debe definir evidencia requerida y checklist de cierre antes de considerarse lista para ejecucion.
- Cada hito debe cerrar con un informe de cumplimiento en `.context/evidencias/` usando `_plantilla_informe_cumplimiento.md`.
- Cada hito debe pasar el gate mecanico `scripts/maintenance/validate_hito_close.py --hito N` antes de marcarse listo para PR.
- Si la validacion detecta que lo implementado no coincide con el requerimiento, criterios de aceptacion, evidencia o artefactos versionados, se debe volver a refinar la tarea/subtareas en Obsidian antes de tocar codigo adicional.
- Si una tarea supera 10-12 subtareas o mezcla dominios sin dependencia directa, dividirla en subtareas numeradas dentro del hito o crear tareas tecnicas hijas vinculadas al mismo hito.
- Las tareas no reemplazan la estimacion; la estimacion es la fuente contractual.

## Gate de refinamiento tecnico de tareas

Este gate se ejecuta despues de aprobar la estimacion y antes de cualquier implementacion. Su objetivo es impedir que una tarea se ejecute desde titulos generales o CAs ambiguos.

Entrada obligatoria:
- Estimacion aprobada `est_XXX.md`.
- Documento fuente en `requerimientos/YYYYMMDD/`.
- Mockups/referencias aprobadas si existen.
- `.context/00_INDICE.md`, arquitectura relevante y estado del proyecto.

Salida obligatoria por tarea:
- `Fuentes del requerimiento` con documento, secciones y mockups exactos.
- `Matriz CA -> detalle implementable` con implicancia tecnica y fuera de alcance.
- `Alcance incluido` y `Alcance excluido`.
- `Analisis tecnico previo obligatorio` por dominio afectado.
- `Especificacion exacta del cambio` con tablas/campos, rutas/componentes, workers o workflows concretos.
- `Subtareas tecnicas` con `Analisis previo`, `Objetivo`, `Cambio exacto`, `Archivos esperados`, `CAs relacionados` y `Validacion`.
- `Matriz CA -> pruebas/evidencia` con tipo de prueba, metodo/comando, resultado esperado y evidencia.
- `Validaciones requeridas`, `Evidencia requerida` y `Checklist de cierre`.

Reglas del gate:
- No modifica codigo core, workflows, SQL ni assets funcionales; solo documentacion Obsidian/backlog.
- Si durante el refinamiento aparece una decision pendiente, se documenta como bloqueador y no se inventa implementacion.
- Si una tarea mezcla demasiados dominios, se divide en subtareas o tareas hijas antes de ejecutar.
- Si una subtarea dice `por definir`, `si aplica` o `equivalente` sin una decision concreta, no esta lista para implementacion.
- Para DB/Supabase, los nombres de columnas, tipos, defaults, checks, indices y RLS/RPC deben quedar explicitados antes de escribir migraciones.
- Para frontend, la ruta, componente, estado, evento, fetch/query, copy, responsive y criterio visual deben quedar explicitados antes de tocar UI.
- Para pipeline, el worker, funcion/bloque, input, output, normalizacion, escritura final y manejo de errores deben quedar explicitados antes de tocar Python.
- Para CI/CD, workflow, trigger, job, environment, secrets y condiciones deben quedar explicitados antes de tocar YAML.

## Gate de pruebas por criterio de aceptacion

Este gate se define antes de implementar y se ejecuta al cierre del hito. Su objetivo es evitar pruebas genericas que no demuestran cumplimiento del requerimiento.

Reglas:
- Cada CA debe tener al menos una prueba concreta.
- Cada prueba debe indicar tipo: documental, unit/syntax, integracion DB, RLS/security, workflow/devops, frontend visual, accesibilidad, SEO o smoke manual.
- Cada prueba debe tener metodo reproducible: comando, query, revision de archivo versionado, captura o checklist.
- Cada prueba debe declarar resultado esperado antes de ejecutarse.
- Cada prueba debe producir evidencia que pueda copiarse al informe del hito.
- Si una prueba falla, el CA queda `observado` o `parcial`; no se marca el hito como completado.
- Si el desarrollador no sabe como probar un CA, no debe implementar: primero se refina la tarea en Obsidian.
- Si el cambio toca Supabase, la evidencia debe diferenciar `estado aplicado en ambiente` vs `artefacto versionado en migration`.
- Si el cambio toca frontend/mockups, la evidencia debe mapear seccion del mockup a componente/ruta y validacion desktop/mobile.
- Si el cambio toca pipeline, la evidencia debe incluir sintaxis Python y al menos un caso de entrada/salida o razon documentada para no ejecutarlo.

## Gate de conformidad requerimiento/evidencia

Este gate se ejecuta despues de implementar y validar, antes de PR listo. Su objetivo es confirmar que lo entregado coincide con el requerimiento aprobado y que la evidencia coincide con los artefactos versionados.

Entrada obligatoria:
- Diff real del hito (`git diff`, archivos nuevos y cambios en DB si aplica).
- Tarea del hito y estimacion aprobada.
- Documento fuente en `requerimientos/YYYYMMDD/`.
- Informe de cumplimiento del hito.
- Resultado de validaciones y security-auditor si aplica.

Reglas:
- Si un cambio existe en Supabase/Cloud/GitHub pero no esta versionado en el repo y el proyecto exige DB-as-Code/IaC, el hito queda `observado`.
- Si tarea, changelog e informe se contradicen, el hito queda `observado`.
- Si un CA queda parcial o no verificable, se agregan subtareas concretas antes de seguir implementando.
- Si aparecen hallazgos de seguridad medios/altos, no se marca `completado` salvo aceptacion explicita del Usuario/PM documentada.
- Si falta detalle, se modifica solo documentacion Obsidian (`.context/backlog_tareas/`, `.context/evidencias/`, `.context/operaciones/`) y no codigo core.
- La salida debe ser un veredicto `GO`, `GO condicionado` o `NO-GO`, con brechas y subtareas refinadas.

## Gate mecanico de cierre de hito

Este gate se ejecuta antes del gate de conformidad humano/QA. Su objetivo es impedir que un modelo cierre un hito usando solo evidencia narrada por si mismo.

Comando obligatorio:
```bash
docker exec studiamatch-dev python3 scripts/maintenance/validate_hito_close.py --hito N --generate-report
# Stagear el reporte, enlazarlo en el informe y luego verificar:
docker exec studiamatch-dev python3 scripts/maintenance/validate_hito_close.py --hito N
```

Reglas:
- `--generate-report` produce evidencia candidata; no autoriza el cierre por si solo.
- Solo el comando final sin flags puede devolver `GO` de cierre, despues de verificar el reporte staged y su huella.
- Si cualquiera de los comandos devuelve `NO-GO`, el hito no puede marcarse como completado ni listo para PR.
- Cada ejecucion con `--generate-report` genera un reporte versionable con timestamp en `.context/evidencias/hito_N_qa_gate_report_YYYYMMDD_HHMMSS.md`; la verificacion final no crea ni sobrescribe evidencia.
- El gate revisa `git diff --cached --check`, archivos untracked relevantes, scope de archivos staged, migraciones referenciadas, tablas Markdown rotas, contradicciones entre TAREA/informe/changelog, terminos reales del schema, workflows que no hacen lo que la documentacion afirma y excepciones DML sobre tablas operativas.
- Si hay archivos staged fuera del scope del hito, el gate debe fallar aunque el codigo compile.
- El gate no reemplaza `security-auditor`; lo complementa. `security-auditor` sigue siendo obligatorio cuando hay DB, RLS, auth, leads, admin, workflows o integraciones.
- Si el gate falla, no se acepta una explicacion del modelo como sustituto. Se corrigen los artefactos o se documenta la excepcion aprobada y se vuelve a ejecutar.
- Para Supabase/RLS, el informe debe incluir queries reales o evidencia de `pg_policies`, `information_schema`, `pg_constraint` y `pg_indexes` cuando aplique.

## Politica de git
- La estructura documental (`.context`, `requerimientos`, `desestimado`) debe subirse separada de cambios funcionales.
- Las implementaciones aprobadas se hacen en ramas `feat/*` desde `desarrollo`.
- Si hay desarrollo paralelo de hitos, crear `release/hito-N` desde el commit exacto aprobado y promover solo esa rama a `certificacion`/`main`.
- Los fixes de un hito ya congelado nacen desde `release/hito-N` y luego se propagan a `desarrollo`.
- Si `desarrollo` esta divergente frente a remoto, se resuelve la sincronizacion antes de push.
- No se hace push si hay riesgo de mezclar cambios no revisados o ajenos.

## Informe de cumplimiento por hito

El informe de cumplimiento es obligatorio para cerrar un hito. Se genera **despues de implementar y validar los cambios**, pero **antes de marcar el PR como listo para entrega interna**. Durante la ejecucion se puede ir completando incrementalmente, pero la version final se cierra al terminar validaciones.

Ubicacion:
- Plantilla: `.context/evidencias/_plantilla_informe_cumplimiento.md`.
- Informe por hito: `.context/evidencias/hito_N_informe_cumplimiento.md`.

Reglas:
- Debe estar escrito para que el cliente entienda que se entrego y como se relaciona con su requerimiento.
- Debe mapear cada CA a cambio realizado, evidencia verificable y estado.
- Debe incluir fuera de alcance no implementado para evitar confusiones comerciales.
- Debe resumir validaciones sin exponer secrets, tokens, PII ni detalles sensibles.
- Puede copiarse a Notion como vista cliente, pero la fuente versionada queda en Git.
- Si Notion se automatiza, los tokens deben vivir en variables de entorno o GitHub Secrets; nunca en el repo.
- Si un CA queda parcial o bloqueado, debe decirlo explicitamente con causa, decision y siguiente accion.

## Checklist antes de iniciar una fase aprobada
- [ ] Estimacion aprobada y actualizada.
- [ ] Tareas creadas con fuentes del requerimiento, matriz CA-detalle, CAs, fechas, entregables, alcance incluido/excluido, analisis previo, especificacion exacta, subtareas, validaciones y evidencia.
- [ ] Cada CA tiene prueba definida con resultado esperado y evidencia requerida.
- [ ] Rama base sincronizada.
- [ ] Alcance de la fase confirmado por el usuario.
- [ ] Riesgos de seguridad identificados.
- [ ] Validaciones previstas definidas.

## Checklist antes de cerrar un hito
- [ ] Tarea actualizada con resultado, commits/PR y evidencia.
- [ ] Changelog actualizado.
- [ ] Informe `.context/evidencias/hito_N_informe_cumplimiento.md` generado.
- [ ] Cada CA tiene estado y evidencia.
- [ ] Cada prueba definida por CA fue ejecutada o justificada como no aplicable.
- [ ] Validaciones ejecutadas o justificadas como no aplicables.
- [ ] Gate mecanico ejecutado: `validate_hito_close.py --hito N` con resultado GO.
- [ ] Reporte QA del gate generado en `.context/evidencias/hito_N_qa_gate_report_YYYYMMDD_HHMMSS.md`.
- [ ] Gate de conformidad requerimiento/evidencia ejecutado con veredicto documentado.
- [ ] Tarea, changelog, informe y artefactos versionados no se contradicen.
- [ ] Informe revisado para lenguaje cliente y sin datos sensibles.
- [ ] Si se usa Notion, contenido copiado/sincronizado desde el informe versionado.
