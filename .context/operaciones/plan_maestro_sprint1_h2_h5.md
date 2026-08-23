# Plan Maestro Sprint 1 H2-H5

## Estado

```text
ESTADO = F10_11_GOV_CI8_POST_MERGE_ROUTE_CLASSIFICATION_PENDING_R1
FASE = F10.11
O0 = COMPLETED
O1 = COMPLETED
O2 = COMPLETED
O3 = COMPLETED
O4 = COMPLETED
O5 = COMPLETED
H2-H5 = BLOCKED_PENDING_HOMOLOGATION_AND_REBASE
active_work_package = WP-H2-001
governance_work_packages = WP-GOV-OBS-001,WP-GOV-INFRA-001,WP-GOV-ARCH-001,WP-GOV-HOM-001,WP-GOV-CI-001,WP-GOV-CI-002,WP-GOV-CI-003,WP-GOV-CI-004,WP-GOV-CI-005,WP-GOV-CI-006,WP-GOV-CI-007,WP-GOV-CI-008
next_gate = COMPLETE_WP_GOV_CI_008_R1_LOCAL_VALIDATION
lifecycle_stage = ACTIVE
gate_status = APPROVED_R1
implementation_status = BLOCKED_PENDING_HOMOLOGATION_AND_REBASE
criteria_status = H2-CA2:NOT_STARTED,H2-CA3:NOT_STARTED
```

Este plan no crea alcance ni autoriza R2/R3. PR #438 publico GOV-CI7 a `desarrollo`; su run post-merge `32655520324` fallo `Canonical Path Boundary` por clasificar un PR ordinario verificable hacia `desarrollo` como promocion invalida. Ahora F10.11 requiere `WP-GOV-CI-008` local R1 para separar `NOT_APPLICABLE`, `BLOCKED` y `VERIFIED_PROMOTION`, y reemplazar HOM-007 por HOM-008 antes de cualquier nuevo O2. Etapa 1 solo queda cerrada cuando el predicado externo de cierre se cumpla y el checkout ordinario StudIAMatch consuma ese estado validado.

## Bases Inmutables

| Rama | Commit | Tree | Estado |
|---|---|---|---|
| `main` | `9b486146962bd2a092acfd649fdcf716e922de89` | `fcb59095e48441bb4486ccc196aee61e2e1e0fe3` | O3 completado |
| `certificacion` | `2134ebfc1af2097b7e17a31b5376bc6942cf020b` | `3b956049f3535263b2fdbe3177dc7118005b7af1` | PR #437 O2 mergeado; push post-merge fallo CI |
| `desarrollo` | `16045d45811cbe12299ce2ba66f6afd75a93d1ee` | `29f76f029f9c1c664fd8a9fc2ebda30d75a0a4df` | PR #438 completado; requiere `WP-GOV-CI-008` antes de nuevo O2 HOM-008 |

## Fuentes Y Hashes

| ID | Archivo privado local | SHA-256 | Tamano |
|---|---|---|---:|
| `SRC-REQ-001` | `Studiamatch_MVP_Requerimientos_v5.docx` | `3537820f93f3a6880bba22109c020cedb4334f1afd905acea70e809c9748b107` | `2568653` |
| `SRC-UI-HOME-001` | `studiamatch_home.html` | `3e84696c000a9f9875853145c8c2cf227e606a5b5f8527184328629c3b1a135d` | `23459` |
| `SRC-UI-RESULTS-001` | `studiamatch_resultados.html` | `9c2ca7660b412a63b22b355f5345f4c28afc73477c1dc6e9d04f770aecd1c32c` | `25172` |

Las fuentes permanecen fuera de Git. Solo se versiona trazabilidad sanitizada.

## Precedencia

1. Decision humana O0-B.
2. [ADENDA-REQ-EST-001-001](../backlog_tareas/req_est_001_sprint_1/adenda_cliente_001_sanitizada.md).
3. Este Plan Maestro.
4. Seccion Sprint 1 de `SRC-REQ-001`.
5. Resto de `SRC-REQ-001` como contexto/backlog.
6. `SRC-UI-HOME-001` y `SRC-UI-RESULTS-001` como referencia visual.
7. Codigo existente solo como compatibilidad tecnica.

Si existe conflicto, gana la fuente superior. Ningun documento legacy sustituye este grafo ni reactiva F9/F10.10.

## Disposiciones Vinculantes

| Materia | Decision |
|---|---|
| Leads | H2-H5 permiten schema/flags y CTA visual. Prohibidos captura, `POST /leads`, almacenamiento, email, webhook o egress. |
| CTA | Visible segun diseno; solo navegacion interna no transaccional si el WP lo exige. |
| Ruta canonica | `/programas/[slug]`. La pagina SEO completa queda backlog salvo navegacion minima aprobada por WP. |
| Moneda | API de tipo de cambio fuera de Sprint 1; si hay selector visual usa tasas referenciales del mockup y no consume API. |
| ROI | Oculto en vistas publicas H4/H5. |
| Schedules | Permanecen fail-closed con `AUTOMATION_ENABLED=false` y `PRODUCTION_WRITERS_PAUSED=true` hasta JIT R3 posterior a H2. |
| Fuentes HTML | Estructura, paleta, Inter, jerarquia y estados visuales son referencia; datos/valores son placeholders salvo contrato de datos reales. |

## Ruta De Homologacion

```text
D0-D10 paquete correctivo local
-> PR correctivo a desarrollo
-> re-O2 desarrollo -> certificacion
-> O3 certificacion -> main
-> O4 main -> certificacion
-> O5 certificacion -> desarrollo
-> tracker final y checkout limpio
-> aprobacion digest WP-H2-001 completada hasta R1 no activo
-> activacion separada WP-H2-001 R1 completada
-> candidate local Obsidian pendiente de main
-> aprobacion WP-GOV-OBS-001 + WP-GOV-INFRA-001 hasta R2
-> PR/merge a desarrollo
-> aprobacion WP-GOV-ARCH-001 hasta R2
-> PR/merge #425 a desarrollo
-> candidate WP-GOV-HOM-001 produce T_HOM
-> aprobacion WP-GOV-HOM-001 hasta R2
-> PR/merge a desarrollo de T_HOM
-> candidate WP-GOV-CI-001 desacopla security-audit/review
-> aprobacion WP-GOV-CI-001 hasta R2
-> PR/merge a desarrollo de GOV-CI
-> PR #428 O2 falla Canonical Path Boundary y consume O2
-> candidate WP-GOV-CI-002 boundary estructural de promocion
-> aprobacion WP-GOV-CI-002 hasta R2
-> PR/merge a desarrollo de GOV-CI-002
-> candidate WP-GOV-CI-003 bootstrap no autorreferencial de grants
-> aprobacion WP-GOV-CI-003 hasta R2
-> cierre administrativo de PR #428 sin merge
-> PR/merge a desarrollo de GOV-CI-003
-> PR #431 O2 falla Promotion Boundary antes de runner y consume HOM-003 O2
-> candidate WP-GOV-CI-004 Environment Promotion para boundary
-> aprobacion WP-GOV-CI-004 hasta R2
-> cierre administrativo de PR #431 sin merge
-> PR/merge a desarrollo de GOV-CI-004
-> PR #433 O2 mergeado a certificacion pero push post-merge falla Canonical Path Boundary
-> candidate WP-GOV-CI-005 boundary post-merge estructural
-> aprobacion WP-GOV-CI-005 hasta R2
-> PR/merge a desarrollo de GOV-CI-005
-> PR #435 O2 falla F9.7 legacy antes de mergear y consume HOM-005 O2
-> candidate WP-GOV-CI-006 promociones target-aware y retiro F9.7 automatico
-> aprobacion WP-GOV-CI-006 hasta R2
-> PR/merge a desarrollo de GOV-CI-006
-> PR #437 O2 mergeado a certificacion pero falla post-merge y consume HOM-006 O2
-> candidate WP-GOV-CI-007 evidencia post-merge fail-closed y HOM-007
-> aprobacion WP-GOV-CI-007 hasta R2
-> PR/merge a desarrollo de GOV-CI-007
-> PR #438 a desarrollo falla post-merge por clasificar PR ordinario como promocion invalida
-> candidate WP-GOV-CI-008 route classification fail-closed y HOM-008
-> aprobacion WP-GOV-CI-008 hasta R2
-> PR/merge a desarrollo de GOV-CI-008
-> nuevo O2 HOM-008 target-aware desarrollo -> certificacion
-> R3 JIT certificacion
-> R3 JIT main
-> homologacion main -> certificacion -> desarrollo
-> checkout ordinario actualizado
-> cierre Etapa 1 Obsidian
-> nuevo/rebasado WP Hito 2
-> H2-CA2 local R1
-> H2-CA3 local R1 posterior
-> H3
-> H4
-> H5
```

La optimizacion original de cinco PR queda desviada por remediacion documental obligatoria. La desviacion debe registrarse, no ocultarse.

## Gates O0-O5

| Gate | Estado | Criterio de salida |
|---|---|---|
| O0-A | `COMPLETED_READ_ONLY` | Preflight, cutoff, baseline y riesgos revisados. |
| O0-B | `APPROVED` | Decision humana adoptada. |
| O1 | `COMPLETED` | PR #414 a `desarrollo`. |
| O1.5 | `COMPLETED` | PR #415 reconciliacion post-O1. |
| O2 | `COMPLETED` | PR #416 a `certificacion`; tree homologado. |
| D0-D10 | `COMPLETED` | Conformidad documental, gobierno reutilizable, links, manifests, evidencias y CI homologados. |
| O3 | `COMPLETED` | PR #421 mergeado a `main`. |
| O4 | `COMPLETED` | PR #422 mergeado a `certificacion`. |
| O5 | `COMPLETED` | PR #423 mergeado a `desarrollo`; checkout limpio verificado. |
| R2 GOV ARCH | `COMPLETED` | PR #425 a `desarrollo@4cce43a743de5860c4da86eecf1782efab91d26b`; tree `ac16b545b74a03b149aac538062def20101187fb`; digest `df48d75129cfe2ba8971f55573a597ca47fb0e3c20e11a3a6a63377349be44e1`. |
| R2 GOV HOM | `COMPLETED` | PR #426 a `desarrollo@fddb9cea6ac44a1f7f7b31e93a7b2f2cc0eeacd1`; tree `5e7d087ac45457264ea29dfc1aa7373efd909290`; digest `aa9d19408c2750925f5824cdfcc3793e7aca1f38f8d95b8f9c57426139989e7e`. |
| GOV CI/review | `COMPLETED` | PR #427 a `desarrollo@b878c5764e55cb2646b60c4777e363489fe48e8b`; tree `174c18efd840fff6ce27fce9fe1dc4edcd65abe8`; desacopla validacion tecnica de review nativa. |
| GOV CI2 boundary promocion | `COMPLETED` | PR #429 a `desarrollo@1ac74f78fec6290e214444e9d2f18619ae3fd3b6`; tree `8191790192580f2e9fb1ddb48d85ab28714720f9`; digest `30bc9a2e7b201438e7398a46f42e6a719e0e5bb41d46c95c71b02234c9091d04`. |
| GOV CI3 grant bootstrap | `COMPLETED` | PR #430 a `desarrollo@235c2329eb5fd8903c31785640a63466b23f0dd8`; tree `cc774746d21cb6649f7018da3049fc811a3f294b`; digest `60c1fc0978208742597f17ef6f4c1fe5741f59b5de0739accbce24fa613ab9c7`. |
| GOV CI4 Promotion Environment | `COMPLETED` | PR #432 a `desarrollo@32dc50c2a26f0d8cf34c5a39a4f10a821bf821aa`; tree `acabd0965d4aa716904917caab691b3867aa5798`; digest `e267fd204eb818674f382b72497be25e7a32706ff7061bb080eda4293fa40e86`. |
| O2 GOV-HOM CI4 | `MERGED_WITH_POST_MERGE_CI_FAILURE` | PR #433 a `certificacion@3682d0af8c16ed0476663e6727b14f03ec14ed78`; tree `acabd0965d4aa716904917caab691b3867aa5798`; run `32615044699` fallo `Canonical Path Boundary`. |
| GOV CI5 post-merge boundary | `COMPLETED` | PR #434 a `desarrollo@9f265e41eb4724727e5bd4b1a5cf6ef5c75a4845`; tree `fc9ff315d20648e87d049d5fb244a09ea214bfb8`; digest `3912d0b7798068c700facfb054360c531b768f251644fef0dbe456ce4b0567cf`. |
| O2 GOV-HOM CI5 | `FAILED_NOT_MERGED` | PR #435 fallo F9.7 legacy; run `32619372008`; job `97145052119`; `R3-GOV-HOM-005-O2-REQ1_CONSUMED_BY_FAILURE`. |
| GOV CI6 target-aware | `PROPOSED_R2_PENDING_DIGEST_APPROVAL` | Candidate local `WP-GOV-CI-006` retira F9.7 automatico y exige ramas target-aware `promote/gov-hom-006-oN`. |
| O2 GOV-HOM CI6 | `MERGED_WITH_POST_MERGE_CI_FAILURE` | PR #437 a `certificacion@2134ebfc1af2097b7e17a31b5376bc6942cf020b`; run `32650341464` fallo por checks `pull_requests: []` y `merged_by=romelhc95-approver`; `R3-GOV-HOM-006-O2-REQ1_CONSUMED_BY_POST_MERGE_FAILURE`. |
| GOV CI7 evidence fail-closed | `COMPLETED_WITH_POST_MERGE_CI_FAILURE` | PR #438 a `desarrollo@16045d45811cbe12299ce2ba66f6afd75a93d1ee`; tree `29f76f029f9c1c664fd8a9fc2ebda30d75a0a4df`; run `32655520324` fallo `Canonical Path Boundary` por PR ordinario no promocional. |
| GOV CI8 route classification | `IN_PROGRESS_R1_LOCAL` | Candidate local `WP-GOV-CI-008` clasifica PR ordinario a `desarrollo` como `NOT_APPLICABLE`, bloquea direct pushes/rutas superiores no promocionales, y reemplaza HOM-007 por HOM-008. |

Ramas target-aware HOM-008: `promote/gov-hom-008-o2-req1`, `promote/gov-hom-008-o3-req1`, `promote/gov-hom-008-o4-req1`, `promote/gov-hom-008-o5-req1`. HOM-006 y HOM-007 quedan superseded y no utilizables.
| Etapa 1 Obsidian | `DESARROLLO_MERGED_PENDING_HOMOLOGATION` | Vault, enlaces canonicos, evidencia H2, taxonomia y arquitectura existen en `desarrollo`; cierre efectivo pendiente de `T_HOM`, R3 JIT y convergencia final. |

## D0-D10 Correctivo

| Gate | Entregable | Stop condition |
|---|---|---|
| D0 Seguridad suplementaria | Escaneo redactado de emails, UUID, URLs, artifacts, blobs eliminados, WIP y fuentes. | PII/credencial activa o fuente con hash distinto. |
| D1 Autoridad | Restaurar `_index.md` y adenda sanitizada; reparar links. | Adenda no recuperable, ADR legacy reintroducido como autoridad o link roto. |
| D2 Plan Maestro | Completar hitos, dependencias, calendario, scoring, PR, stop conditions y trazabilidad. | Ambiguedad de fuente o contradiccion sin resolver. |
| D3 Contratos H2-H5 | Hitos, tasks y matrices con criterios verificables. | Criterio sin prueba/evidencia trazable. |
| D4 Manifests/Evidencia | Manifests con digest verificable y plantillas de evidencia utilizables. | Digest no verificable o evidencia skeleton sin estructura. |
| D5 Tracker/CI | Tracker reconciliado O2; CI con links/digest y gates blocking. | H2 marcado activo o path fuera de allowlist. |
| D6 Retrospectiva Hito 1 | Tiempo, rework, causas y mejoras registrados como contrafactual trazable. | Productividad inferida sin datos de esfuerzo o causalidad no demostrada. |
| D7 Tracker reutilizable | Plantilla de ocho secciones y Prompt Cavernicola terminal obligatorio. | Tracker sin proximo gate unico, stop conditions o autorizacion exacta. |
| D8 AGENTS y PR template | Modelo R0-R3, WP/digest y prohibiciones R3 homologados. | Microautorizacion decimal usada como unico modelo futuro o PR sin digest. |
| D9 Context Graph semantico | Estado, Plan, Tracker, Hito, TASK y WP coherentes y validables. | Nodo canonico eliminado sin reemplazo/tombstone o estado contradictorio. |
| D10 Enforcement CI | Guards para credenciales, manifests, links, semantic graph, source artifacts y path boundary. | CI no bloquea fuentes privadas, links rotos, drift semantico o paths fuera de alcance. |

## Scoring H2-H5

H2-H5 usan 12 unidades de 100 puntos. Mientras Etapa 1 Obsidian no este cerrada por el predicado externo F10.11 y `WP-H2-001` no sea rebasado, H2-CA2 y H2-CA3 siguen bloqueados y todos los criterios permanecen `0/100`.

| Unidad | Hito | Estado pre-main | Puntos |
|---|---|---|---:|
| `H2-CA2` | H2 | `BLOCKED_PENDING_HOMOLOGATION_AND_REBASE` | 0 |
| `H2-CA3` | H2 | `NOT_STARTED` | 0 |
| `H3-CA4` | H3 | `PLANNED_NOT_ACTIVE` | 0 |
| `H4-CA5` | H4 | `PLANNED_NOT_ACTIVE` | 0 |
| `H4-CA6` | H4 | `PLANNED_NOT_ACTIVE` | 0 |
| `H4-CA7` | H4 | `PLANNED_NOT_ACTIVE` | 0 |
| `H4-CA13H` | H4 | `PLANNED_NOT_ACTIVE` | 0 |
| `H5-CA8` | H5 | `PLANNED_NOT_ACTIVE` | 0 |
| `H5-CA9` | H5 | `PLANNED_NOT_ACTIVE` | 0 |
| `H5-CA10` | H5 | `PLANNED_NOT_ACTIVE` | 0 |
| `H5-CA11` | H5 | `PLANNED_NOT_ACTIVE` | 0 |
| `H5-CA13R` | H5 | `PLANNED_NOT_ACTIVE` | 0 |

`Progreso H2-H5 = 0 / 1200 = 0%`.

## Calendario Relativo

| Secuencia | Trabajo | Dependencias |
|---|---|---|
| T0 | D0-D10 local | `COMPLETED`. |
| T1 | PR correctivo a `desarrollo` | `COMPLETED` mediante PR #417. |
| T2 | re-O2 a `certificacion` | `COMPLETED` mediante PR #418 y PR #420. |
| T3 | O3 a `main` | `COMPLETED` mediante PR #421. |
| T4 | O4 main -> certificacion | `COMPLETED` mediante PR #422. |
| T5 | O5 certificacion -> desarrollo | `COMPLETED` mediante PR #423. |
| T6 | Gobierno Obsidian | `WP-GOV-OBS-001` + `WP-GOV-INFRA-001` candidates; requieren aprobacion R2 compuesta para desarrollo. |
| T7 | Reconciliacion GOV-HOM | `COMPLETED` mediante PR #426. |
| T8 | Desacople GOV-CI | `COMPLETED` mediante PR #427. |
| T9 | Boundary GOV-CI2 | `COMPLETED` mediante PR #429. |
| T9.5 | Bootstrap GOV-CI3 | `COMPLETED` mediante PR #430. |
| T9.6 | Promotion Environment GOV-CI4 | `COMPLETED` mediante PR #432. |
| T9.7 | O2 GOV-CI4 | `MERGED_WITH_POST_MERGE_CI_FAILURE` mediante PR #433; requiere CI5 antes de O3. |
| T9.8 | Boundary post-merge GOV-CI5 | `COMPLETED` mediante PR #434. |
| T9.9 | Promociones target-aware GOV-CI6 | `WP-GOV-CI-006` corrige PR #435/F9.7 y requiere R2 separado a `desarrollo`. |
| T10 | Homologacion Obsidian | R3 JIT separados para O2/O3/O4/O5 target-aware y convergencia final, posterior a CI-006. |
| T10 | H2-CA2 | Bloqueado hasta cierre efectivo de Etapa 1 y WP H2 rebasado/validado. |
| T11 | H2-CA3 | Bloqueado hasta cierre local de H2-CA2. |

Fechas absolutas comerciales quedan fuera de Git. El calendario operativo se expresa por dependencias para evitar falsa autorizacion.

## Estrategia De PR

- Cada gate remoto usa PR protegido y merge commit.
- No squash ni rebase en homologacion.
- No combinar O3/O4/O5 en un mismo prompt.
- No push ni PR hasta autorizacion R2 separada.
- Las ramas correctivas F10.11 son historicas. H2 requiere WP/digest, aprobacion por commit candidate y ramas nuevas segun el WP aprobado.

## H2 - Modelo Editorial Y Calidad

Contrato obligatorio:

1. Contrato editorial por campos publicables, editoriales y pipeline-owned.
2. Diccionario de datos con tipo, nulabilidad, fuente, ownership y uso UI.
3. Estados y transiciones de calidad/editorial.
4. `missing_fields` calculable y auditable.
5. `field_sources` por campo.
6. Ownership manual/pipeline con precedencia manual.
7. Inventario de writers y rutas de mutacion.
8. RLS, grants y pruebas por rol.
9. Migracion forward-only versionada.
10. Backfill separado, reanudable e idempotente.
11. Matriz de pruebas con segundo run `NOOP`.
12. Manifest aprobado por digest hasta R1 no activo.
13. Evidencia usable por ambiente.

Restricciones H2:

1. Migracion nueva; no editar migraciones historicas.
2. Estados editorial/calidad explicitos.
3. `missing_fields` persistente o reproducible.
4. `field_sources` persistente o reproducible.
5. Timestamps manuales preservados.
6. Patrocinio/leads base sin egress.
7. Auditoria append-only.
8. Pipeline tolerante a parciales.
9. Valores manuales protegidos contra overwrite pipeline.
10. Pipeline incapaz de publicar por si solo.
11. Paginacion para mas de 1000 filas.
12. Backfill reanudable.
13. Segundo run `NOOP` obligatorio.
14. H2-CA2 debe cerrarse localmente antes de iniciar H2-CA3.

## H3 - Admin Editorial

Debe cubrir auth, membresia admin, acceso negativo, cola paginada, edicion allowlisted, optimistic locking, publicar/despublicar, auditoria, static export y UAT en Certification. No inicia antes de H2 aceptado.

## H4 - Home Publica

Contrato visual exacto:

- 6 programas patrocinados.
- 3 programas abiertos organicos.
- 3 paises.
- Inter.
- Paleta y gradiente del HTML.
- Logos reales con fallback.
- Conteos reales cuando exista fuente backend; placeholders no cierran criterio.
- CTA visual sin captura ni egress.
- ROI ausente.
- Responsive desktop/mobile.

## H5 - Resultados Publicos

Filtros exactos:

- Disponibilidad.
- Area.
- Modalidad.
- Pais.
- Precio.
- Duracion.

Contrato de interaccion:

- Sticky search.
- Chips removibles.
- Clear-all.
- URL query contract.
- Back/forward.
- Reset de pagina al filtrar.
- Sidebar desktop.
- Panel/drawer movil.
- Contador contextual.
- Orden determinista.
- Paginacion.
- Cuatro estados de card.
- Patrocinados primero.
- Loading, empty y error/retry.
- Precio `A consultar`.
- Fecha `Sin confirmar`.
- Ruta `/programas/[slug]`.
- Cero captura y egress.

## CI Y Validaciones

`security-audit` debe agregar y mantener como blocking:

- Credential scan.
- Python syntax.
- Manifest/digest validation.
- Markdown link validation.
- Context Graph.
- Canonical path boundary.
- ESLint.
- TypeScript typecheck.
- Static build.
- Context Graph semantico.
- Source artifact guard.
- Canonical deletion guard.
- Path boundary acumulado contra baseline.
- PostgreSQL 17 solo cuando cambie `db/**`.

`security-audit` valida candidate/digest y no reviews: el Governance Preflight usa `Base-SHA`, `Candidate-SHA`, head real, manifest, paths y co-change solo en PR a `desarrollo`. La review humana obligatoria pertenece a GitHub branch protection, no dispara CI y no requiere rerun manual. El `Canonical Path Boundary` conserva el modo incremental para PR normales y usa boundary estructural para promociones O2-O5, validando `Promotion Attestation` en lugar del diff historico acumulado. `Promotion Boundary` debe usar el Environment dedicado `Promotion`; no debe reutilizar `Certification`, `Production` ni `Development`, porque los eventos `pull_request` usan refs sinteticos `refs/pull/<n>/merge`. GOV-CI8 implementa route classification post-merge: solo PR ordinario unico a `desarrollo` puede ser `NOT_APPLICABLE`; `BLOCKED` falla cerrado sin fallback y solo HOM-008 exacto puede ser `VERIFIED_PROMOTION`.

Playwright se documenta como gate de H3 en adelante; no se activa en D0-D10.

## Stop Conditions Globales

- Drift de refs o trees base.
- Hash de fuente distinto.
- Autoridad ambigua.
- Link roto.
- Path fuera de allowlist.
- Digest no verificable.
- Evidencia sin estructura.
- Cambio en denylist.
- PII/credencial activa.
- Activacion de lead capture/egress.
- Activacion de schedules/writers.
- Documentacion no trazable a fuente.

## Proximo Gate

F10.11 esta publicada parcialmente en `desarrollo` y `certificacion`, pero Etapa 1 Obsidian sigue como `DESARROLLO_MERGED_PENDING_HOMOLOGATION` hasta que GOV-CI8 sea publicado a `desarrollo`, promovido a `certificacion` mediante O2 HOM-008 y luego homologado por grants R3 JIT separados. PR #437 quedo `MERGED_TO_CERTIFICACION_WITH_POST_MERGE_FAILURE` y consumio `R3-GOV-HOM-006-O2-REQ1`; PR #438 quedo `MERGED_TO_DESARROLLO_WITH_POST_MERGE_CI_FAILURE` por `POST_MERGE_PAIR_INVALID`; HOM-006/HOM-007 quedan superseded. El siguiente gate es completar validacion local R1 de `WP-GOV-CI-008`. Hito 2, H2-CA2, H2-CA3, Main, DB, Supabase, backfill remoto, RLS/grants remotos, writers, schedules o produccion requieren gates posteriores separados.

## Predicado Externo De Cierre F10.11

F10.11 solo cierra cuando `tree(main) == tree(certificacion) == tree(desarrollo) == T_HOM`, `main` sea ancestro de `certificacion`, `certificacion` sea ancestro de `desarrollo`, `DB Sync` reporte cero cambios/cero apply, `O2`/`O3`/`O4`/`O5` hayan consumido grants R3 separados y el checkout ordinario haya consumido el estado final. Declarar cierre antes de ese predicado es drift de autoridad.
