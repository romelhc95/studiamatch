## Resumen

Esta propuesta prepara el paso 2 de transferencia: documentación integral y navegación Obsidian de StudIAMatch en el candidato local. R8 se conserva como antecedente inmutable; este paquete R9 es un delta documental independiente con el checker de enlaces y el allowlist necesario para que CI reconozca las rutas documentales. No incorpora cambios funcionales de H3, dependencias, caches, secretos, outputs ni el resto del WIP.

El scope explícito y los hashes están en el [manifiesto R9 documental](h3req1_pr_scope_manifest_2026-10-12_r9_docs.json). El corte actual registra 51 paths propuestos y 8 evidencias históricas/sanitizadas seleccionadas (59 archivos con contenido hasheado); el check log también está en el scope. El cuerpo PR y el manifiesto son artefactos explícitos del paquete; el manifiesto no se hashea a sí mismo. El backup externo tampoco forma parte del paquete.

Candidato: `feat/h3req1-sync-20261002`, HEAD baseline `4eb4d877a50b012bb630a129bd0c74482c33be9c`; HEAD no identifica el WIP. El body y manifiesto R8 se preservan byte por byte como artefactos históricos; sus resultados no se alteran. Esto no implica que todos los paths fijados por el scope R8 sigan iguales en el candidato: R9 comparte 10 rutas con R8 y cambia nueve contenidos actuales. En el paso 3, al reconciliar el paquete, R9 superpondrá estas versiones actuales: `.context/00_INDICE.md`, `.context/backlog_tareas/req_est_001_sprint_1/tarea_003_hito_3.md`, `.context/estado_del_proyecto.md`, `.context/hitos/h3req1_implementation_report.md`, `.context/hitos/hito_003.md`, `.context/sistema_db_supabase.md`, `.github/pull_request_template.md`, `.github/workflows/security-audit.yml` y `README.md`. `web/vendor/README.md` es la décima ruta compartida y permanece idéntica. El paso 3 volverá a validar consumidores y generará un manifiesto conjunto, sin modificar el body, manifiesto ni evidencia histórica R8. El paquete combinado de integración no está reconciliado en este paso: R8 incluye el tarball local `web/vendor/braces-3.0.4-h3.1.tgz`, y esta transferencia excluye dependencias. La decisión queda preparada para G10 como opciones explícitas: mantener una excepción con auditoría/build renovados, reemplazarla por un release oficial validado y regenerar el lock, o mantener R9 separado hasta que el responsable autorice una de esas vías. No se consulta estado upstream actual.

No se abrió PR ni se iniciaron validaciones remotas. El cuerpo usa la [plantilla versionada](../../.github/pull_request_template.md) y queda como borrador de revisión del responsable.

## Evidencia De Este PR

Corte local: 2026-10-12. WIP observado al corte final: 68 paths tracked cambiados, 918 entradas untracked visibles, 20,427 paths untracked expandidos y 0 staged; el WIP no se propone íntegro. La branch y HEAD se verificaron durante este trabajo. El checkout original `/home/romel/src/studiamatch` solo se leyó.

El backup pre-edición externo conserva 13,856 archivos (13,740 bajo `.context`, 115 Markdown fuera de `.context` y `.env.example`), con manifiestos fuente/copia coincidentes y hashes de sus artefactos verificados. `web/vendor/README.md` fue excluido inicialmente al clasificar el directorio como dependencia; su versión previa se recuperó byte por byte desde evidencia local fechada, SHA-256 `4e7f2700dcc37fe9db4b4fb3834ff7d4a4764e0f9ed3b8ea330e202d1b2ae62d`, y la limitación quedó registrada. El checkpoint de este corte antes de completar el diccionario DB está en `/home/romel/backups/studiamatch-docs-2026-10-12/checkpoint_before_database_dictionary_fix_2026-10-12`: 18,607 archivos, 1,781,934,080 bytes; SHA-256 del manifiesto fuente `a754e7674ff7ff563f8a499d1a9c6a046cdd743165b0f30ea680a4b9f12f7fe2` y del tar `64049be85c706c93b51204ef5b9a6fb2420e72e66c888f89ee777cf838a33ff5`. La copia/candidato se cotejaron path por path y byte por byte. Es posterior a cambios R9 y no es backup pre-edición. Checkpoints separados preservan las ediciones posteriores. Ver ubicaciones e inventarios en [evidencia integral](h3req1_documentacion_integral_2026-10-12.md); ningún backup entra al paquete.

El checkpoint pre-edición y R8 ya están preservados y verificados fuera de ambos checkouts. El primer checkpoint adicional de 18,324 paths conserva integridad verificada pero quedó supersedido para uso como copia filtrada al encontrar 10 tarballs braces y dos snapshots G08 que los contienen; se deja intacto. La copia final filtrada está en `/home/romel/backups/studiamatch-docs-2026-10-12/checkpoint_final_candidate_documentation_filtered_2026-10-12`, con 18,312 paths. Excluye 283 `.next/cache` y 12 artefactos con la dependencia; conserva 4,422 outputs `.next` no-cache como evidencia histórica generada, no como build actual. Los sidecars externos registran inventario y hashes fuente/copia/tar; ningún backup ni esos sidecars están en el paquete R9.
R178 acredita GO local funcional H3REQ1 G01–G09 en sus inputs: G03 337 passed, 4 skipped y 1 warning; G05 snapshot 17/17; G06 artefacto Pages/workerd 201/201; G07 C03 R51 128/128; G08 scanner 854 paths y tool checks; G09 216/216 resultados caso-viewport seleccionados, R173 6/6 viewports con 36 assertions y onboarding 10/10 fixture. Se conservan skips, warning y límites en R178. R181/R182 revisan el paquete R8, no el delta documental de este borrador. Las fuentes ejecutables de producto no cambiaron por R9, así que R178 se reutiliza por impacto.

La validación de este paquete queda en la tabla de [evidencia integral](h3req1_documentacion_integral_2026-10-12.md), el [registro de checks Docker](h3req1_documentacion_checks_2026-10-12.txt) y el manifiesto. El alcance funcional histórico detallado permanece en el [cuerpo R8](h3req1_pr_body_draft_local_review_2026-10-12_r8.md) y su [manifiesto R8](h3req1_pr_scope_manifest_2026-10-12_r8.json).

## Avances Del Cambio

| Componente/contrato | Cambio implementado | Consumidores/impacto | Evidencia |
|---|---|---|---|
| Navegación Obsidian | `indice.md` ordena dominios, estado, requerimientos, hitos, decisiones, componentes e historia; `00_INDICE.md` conserva compatibilidad | Constructores, operadores, lectores de Obsidian | Índice, mapa de reorganización y checker de grafo. |
| Arquitectura, tecnologías y frontend | Límites/runtimes, rutas públicas/Admin, estado, catálogo, filtros, detalle, comparación, edición/publicación, export/cache y límites | Frontend, Pages Functions, Admin y lectores públicos | Fuentes locales citadas en cada dominio y fichas `componentes/`. |
| Backend, database y pipeline | Endpoints/RPC, autorización, cuotas, diccionario de schema desde SQL, baseline Pro, migraciones/rollback, gates y writers clasificados | BFF, Edge, Auth, PostgREST, PostgreSQL, workers, jobs y lectores | Código/config/SQL candidato; el diccionario incluye nueve columnas locales, las 12 acciones del último CHECK de auditoría y la secuencia de definiciones RPC de invitación en migrations locales 20260920/21/28 y 20261001/02; no acredita schema remoto. |
| Seguridad, pruebas, operación y CI/CD | Fronteras, controles, resultados por input, ambientes, bindings por nombre, Docker, schedules declarados y etapas Stage 1/Stage 2 | Equipo de desarrollo/operación y G10 | Referencias fechadas R178/R181/R182; alcance remoto desconocido. |
| Requerimientos, hitos, decisiones e historia | Relación de atestación sanitizada → implementación → pruebas; estados y alternativas solo cuando la fuente las declara | Responsable funcional, QA y mantenimiento | REQ-EST-001/adenda, atestación sanitizada, backlog, ADR y Git local. |
| Registro y cobertura fuente-documento | 808/808 fuentes asignadas a 12 componentes en 44 grupos; 69 documentos vigentes y 429 históricos clasificados | Código, SQL, configuración, workflows, tooling, tests/runners y documentación ejecutable del candidato | Registro JSON canónico, vista generada, checker y gate Docker. Los 28 renglones editoriales son un mapa, no el denominador. |
| Checker y allowlist documental | Checker read-only `.mjs`; wrapper local y job `documentation-integrity` preparado para CI, sin ejecución/configuración GitHub | Índices, anchors, componentes, comentarios ruta-doc y scope | Ejecuciones Docker registradas; adopción/ejecución remota desconocida. |
| Dependencia `braces` | README y situación de integración clasificados sin cambiar package/lock/tarball | Próxima reconciliación G10 | README local fechado 2026-10-03, manifest/lock candidato; upstream actual sin verificar. |

El mapa registra ruta origen, destino, consumidores y tratamiento histórico. No se mueven migrations, rutas públicas, imports, archivos especiales de framework, evidencia sellada ni documentos raíz históricos. El contenido del documento privado de cliente no se leyó; se cita solo su atestación sanitizada.

## Pilares Obligatorios

| Pilar | Estado | Resultado validado y límites |
|---|---|---|
| Funcionalidad | Sin cambios funcionales | R178 GO local se preserva; la propuesta documental no altera entradas ejecutables del producto. No equivale a adopción remota. |
| Escalabilidad | Evidencia histórica acotada | Se conservan las mediciones descriptivas R79/R135 con sus límites; R9 no modifica código ni repite carga. No hay SLA o carga cloud acreditada. |
| Seguridad | PASS local acotado | El checker no lee fuentes con `inline_comment: none`; credential scan sobre el scope explícito pasa sin emitir valores. Secret stores, CI efectivo y remotos no consultados. El follow-up de `braces` requiere resolución G10. |
| Mantenimiento | Asignación fuente-documento local 100% | 808/808 fuentes asignadas a componente/documento/anchor; relaciones: 2,093/4,848 verificadas, 1,236 pendientes, 1,517 desconocidas y 2 N/A. Las relaciones pendientes/desconocidas tienen resolución registrada y no cuentan como validadas; 0/808 fuentes tienen todas las dimensiones verificadas. Owner de `braces` continúa sin confirmación. |
| Calidad | Gate documental y pins PASS; GO independiente para registro/gate y checkpoint pre-final | La revisión confirmó el parser, asignaciones bidireccionales, 25 familias, exclusiones y sidecars pre-final. El checkpoint final filtrado se conserva fuera del PR con inventario y hashes en sidecars externos; WIP/paquete funcional sigue explícito para G10. |
| Rendimiento | Evidencia histórica descriptiva | R79 registra muestras/viewport; R9 no cambia runtime ni declara rendimiento global o remoto. |

## Transicion Transparente

| Fase | Alcance/resultado real | Evidencia / autorización cuando aplique |
|---|---|---|
| expand | Añade documentación y un checker read-only; amplía allowlist para los paths documentales | Manifest R9 documental, revisión de workflow local. |
| compatibilidad | Conserva `estado_del_proyecto.md` como autoridad, `00_INDICE.md` como puente y mantiene rutas históricas | Checker y mapa origen→destino; no se borran fuentes/evidencias. |
| deploy | No aplica a este delta. No hubo PR, workflow_dispatch, DB, Pages, Worker o deploy | Cualquier acción posterior requiere instrucción separada. |
| contract | No se retiraron contratos de producto ni documentos históricos | El contrato funcional permanece igual al corte R178. |
| Rollback/recuperación | Restauración documental desde backup/checkpoint correspondiente al corte; mantener las notas históricas | Manifiestos SHA-256 externos; no limpiar copias ni recursos. |
| No degradacion funcional | R9 no cambia código funcional/SQL/package lock; el cierre R178 se reutiliza por inputs idénticos | R178 y scope R9 explícito. El paquete combinado espera la resolución `braces`. |

## Evidencia Para Cliente

La [atestación sanitizada versionada](../evidencias_cliente/sprint_1/atestado_aceptacion_plan_ingesta_editorial_auditoria_2026-10-01.md) y el [índice de requerimientos](../requerimientos/README.md) siguen siendo la referencia accesible; el documento privado no se lee ni se adjunta. R178 cierra localmente los criterios H3REQ1 declarados para fixtures. Este delta no añade ni modifica comportamiento de cliente, no acredita aceptación remota y no abre el siguiente hito.

## Validaciones

| Validacion | Resultado/exit/casos | Ambiente/grado | Evidencia/límites/owner |
|---|---|---|---|
| Credential scan | PASS tras corregir el check log; 60 archivos exactos | Docker local | Salida `credential scan passed`; no emitió valores. El gate se repite tras refrescar metadata final; no cubre todo el WIP ni stores remotos. |
| Python assertions documentales | PASS; estado 7/7 y atestación sanitizada 10/10 invocados directamente | Docker local | `pytest` no está instalado. El check opcional de hashes retornó con `STUDIAMATCH_PRIVATE_SOURCE_DIR` unset; no leyó la fuente privada. No cambió código Python de producto. R178 se reutiliza para funcionalidad. |
| Python compile | No aplica: no cambió código Python | Docker local | No se renovó. |
| PostgreSQL DB Change Gate | No aplica: no se editó SQL ni se consultó DB | No hay entorno DB utilizado | Pro sigue baseline; SQL local no prueba schema remoto. |
| ESLint | No aplica: no cambió UI ni código JS/TS de producto | Docker local | Checker documental `.mjs` se valida como tooling aparte. |
| TypeScript | No aplica: no cambió TS/TSX | Docker local | Se reutiliza evidencia R178 por inputs idénticos. |
| Static build | No aplica: no cambió fuente/build dependency del producto | Docker local | No se generó ni limpió `.next`/`out`; R178 conserva build local histórico. |
| actionlint / ShellCheck | YAML parse, allowlist, path guard y `bash -n` PASS; actionlint y ShellCheck no instalados | Docker local | El parseo YAML no valida semántica completa del workflow; renovar actionlint/ShellCheck en G10 antes de PR; owner: responsable de integración. |
| UAT/runtime/integración | No aplica: sin cambio funcional ni navegador | Local histórico R178 | No hubo servicio remoto ni smoke nuevo. |
| security-audit / CI independiente efectivo | No ejecutado | GitHub remoto no consultado | Status check/configuración efectiva desconocidos; requiere verificación posterior. |
| CodeQL si aplica | No ejecutado | CI remoto no consultado | Determinar aplicabilidad y resultado en la etapa de PR. |
| Cloudflare Pages / smoke preview | No ejecutado | Remoto no consultado | Requiere instrucción separada de Development. |
| Browser snapshot si aplica | No aplica: sin cambios de UI | N/A | R178 preserva capturas de sus inputs. |
| security-auditor | PASS / GO tras la corrección P2 | Confirmó parser, autopruebas, registro/navegación, límites del checker, 51/51 scope, 8/8 evidencias, 59 hashes y preservación. No consultó servicios remotos ni leyó el contenido de evidencias seleccionadas. |
| Documentación / trazabilidad / fuente cliente | PASS tras corregir el check log; 808/808 fuentes, 12/12 componentes, 44 grupos, 25 familias de artefactos y 69/69 docs vigentes alcanzables | Docker local | Relaciones ponderadas: 2,093/4,848 verificadas; 1,236 pending, 1,517 unknown, 2 N/A; 0/808 con todas las dimensiones verificadas. Autoprueba confirma falla ante fuente nueva sin asignación. |

## Seguridad Y Datos

- Scanner de credenciales limitado al scope enumerado, evidencias seleccionadas, body y manifiesto; el resultado final se registra con rutas/número, sin valores.
- El documento privado de cliente, `.env` operativos, tokens y secretos no se leyeron ni incluyen.
- R181/R182 siguen acotados a R8; no se extrapolan a R9.
- No hubo Supabase, SQL operativo, Cloudflare, writers, schedules, secrets, deploy o lectura remota.
- `braces` conserva un follow-up no resuelto sin waiver: no se conoce el estado upstream actual, owner ni fecha de revisión. El tarball se excluye de esta propuesta documental.

## Alcance Y Limites

- El scope documental R9 se fija por paths explícitos y SHA-256; todo el resto del WIP permanece fuera. El manifiesto diferencia fuente/documentación de evidencia seleccionada. Crear, mover, eliminar o cambiar un contrato requiere actualizar registro, comentarios ruta-doc cuando apliquen, fichas y evidencia por impacto.
- El registro del corte contiene 808 fuentes locales. HEAD tracked + scopes R8/R9 proyectan 441 fuentes; 367 paths actuales quedan fuera del paquete propuesto y se mantienen como WIP explícito. El paso 3 debe reconciliar esos 367 paths contra el paquete combinado, actualizar el registro y regenerar los pins antes de CI; el workflow futuro puede fallar si recibe un paquete sin esa reconciliación.
- R8, R178, R181 y R182 se conservan como antecedente. Body/manifest R8 mantienen sus hashes; el paso 3 superpondrá nueve paths R9 sobre el scope R8 y conservará esos artefactos y resultados históricos.
- Adopción remota de Pro/schema, Auth, Edge, Pages, Workers, bindings/secrets, workflows, schedules, branches/required checks y runtime sigue desconocida.
- Este borrador no abre PR ni autoriza G10 remoto, integración, Development, merge o deploy.

## Checklist Tecnico

- [x] Tarea, gates, candidato, branch, HEAD y WIP delimitados; original de solo lectura.
- [x] Backup pre-edición y checkpoints externos con inventario/hash; recuperación de README declarada sin llamarla backup previo.
- [x] Inventario dinámico, mapa origen→destino/referencias y asignación explícita de 808/808 fuentes a 12 componentes y anchors existentes; las 28 responsabilidades editoriales no son el denominador.
- [x] Índice principal y puentes compatibles; autoridad de estado única.
- [x] R8 preservado; no se incluye cache/dependencias/secretos/todo untracked en el delta documental.
- [x] Revalidar checker, pins/digests y credential scan tras el cambio de política de comentarios.
- [x] Reread independiente posterior a la corrección P2: PASS / GO, sin hallazgos materiales.
- [ ] Actionlint semántico y ShellCheck siguen pendientes de G10 antes de PR; herramientas ausentes en `studiamatch-dev`.
- [x] Sin commit, push, PR, merge, fetch, pull, cambio de ramas, SQL operativo, secreto, writer, deploy ni prueba remota.
