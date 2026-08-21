# Plan Maestro Sprint 1 H2-H5

## Estado

```text
ESTADO = DOC_GOVERNANCE_CONFORMANCE_COMPLETED_LOCAL
FASE = F10.11
O0 = COMPLETED
O1 = COMPLETED
O2 = COMPLETED
O3 = BLOCKED_BY_SOURCE_CONFORMANCE
H2-H5 = NOT_AUTHORIZED
active_work_package = NONE
next_gate = R2_PUSH_PR_DESARROLLO_REQUIRES_SEPARATE_AUTHORIZATION
```

Este plan no crea alcance ni autoriza ejecucion. Es el contrato documental para corregir la conformidad de `REQ-EST-001` antes de O3 y para dejar trazable la ejecucion futura H2-H5.

## Bases Inmutables

| Rama | Commit | Tree | Estado |
|---|---|---|---|
| `main` | `ad89e8ab9575b37476502d6062e22c044ad6447b` | `54098b3ff581cc7728979afc8e6d47c9535141b5` | Baseline tecnico PR #327 |
| `desarrollo` | `a2c97ec17aabc790b656d6db1b16bdc95f0af1b2` | `a03681d271475e8ccbf6061ce63bc4ee5990cd5c` | O1/O1.5 completado |
| `certificacion` | `4e7e41a9fac08e657308849701b4b1f70b994e3b` | `a03681d271475e8ccbf6061ce63bc4ee5990cd5c` | O2 completado |

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
-> aprobacion digest WP-H2-001
-> H2
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
| D0-D10 | `COMPLETED_LOCAL_VERIFIED` | Conformidad documental, gobierno reutilizable, links, manifests, evidencias y CI verificados localmente. |
| O3 | `BLOCKED` | Requiere D0-D10 mergeado en `certificacion` y nuevo prompt. |
| O4 | `PENDING` | Requiere O3 mergeado. |
| O5 | `PENDING` | Requiere O4 mergeado y tracker final. |

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

H2-H5 usan 12 unidades de 100 puntos. En F10.11 todas quedan `0/100` porque no hay implementacion autorizada.

| Unidad | Hito | Estado F10.11 | Puntos |
|---|---|---|---:|
| `H2-CA2` | H2 | `PLANNED_NOT_ACTIVE` | 0 |
| `H2-CA3` | H2 | `PLANNED_NOT_ACTIVE` | 0 |
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
| T0 | D0-D10 local | `COMPLETED_LOCAL_VERIFIED`. |
| T1 | PR correctivo a `desarrollo` | Requiere autorizacion R2 separada. |
| T2 | re-O2 a `certificacion` | Correctivo en `desarrollo`. |
| T3 | O3 a `main` | Correctivo en `certificacion`; nuevo prompt. |
| T4 | O4 main -> certificacion | O3 mergeado; nuevo prompt. |
| T5 | O5 certificacion -> desarrollo | O4 mergeado; nuevo prompt. |
| T6 | H2 | O5, checkout limpio, digest `WP-H2-001` aprobado. |

Fechas absolutas comerciales quedan fuera de Git. El calendario operativo se expresa por dependencias para evitar falsa autorizacion.

## Estrategia De PR

- Cada gate remoto usa PR protegido y merge commit.
- No squash ni rebase en homologacion.
- No combinar O3/O4/O5 en un mismo prompt.
- No push ni PR hasta autorizacion R2 separada.
- La rama correctiva permitida es `docs/f10-11-source-conformance`.

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
12. Manifest aprobado por digest.
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

El paquete local D0-D10 esta completado y verificado. El unico siguiente gate posible es autorizacion R2 separada para push y PR correctivo a `desarrollo`. O3 y H2 siguen bloqueados.
