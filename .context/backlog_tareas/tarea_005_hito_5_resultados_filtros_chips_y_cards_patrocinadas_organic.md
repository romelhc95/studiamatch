---
id: TAREA-005
fase: 5
estado: pendiente
prioridad: critica
estimacion_ref: est_001
hito: Hito 5
paquete: Paquete 5 - Resultados filtrados, sidebar, chips y cards patrocinadas/organicas
cas: "CA8, CA9, CA10, CA11, CA12, CA13 Resultados"
fecha_inicio: 2026-09-15
fecha_limite: 2026-09-29
despliegue: "2026-10-05 09:00 PET"
responsable: IA implementadora
revisor: security-auditor
aprobador: Usuario/PM
skill_principal: frontend-architect
subespecialidad: Frontend Next.js 16 resultados + filtros + cards
skills_apoyo: "accessibility, seo, security-auditor, data-quality-analyst, qa-test-engineer"
gate_obligatorio: security-auditor
entregable: "PR a desarrollo con resultados filtrados segun mockup aprobado"
creado: 2026-07-11
tags: []
---

# Tarea 005: Hito 5 - Resultados filtros chips y cards patrocinadas organicas

## Contexto
Estimacion de referencia: [[../estimaciones/est_001]]

- **Hito:** Hito 5
- **Paquete:** Paquete 5 - Resultados filtrados, sidebar, chips y cards patrocinadas/organicas
- **CAs cubiertos:** CA8, CA9, CA10, CA11, CA12, CA13 Resultados
- **Responsable de ejecucion:** IA implementadora
- **Revisor obligatorio:** security-auditor
- **Aprobador:** Usuario/PM
- **Entregable:** PR a desarrollo con resultados filtrados segun mockup aprobado

## Skills y sub-especialidad
- **Skill principal:** frontend-architect
- **Sub-especialidad tecnica:** Frontend Next.js 16 resultados + filtros + cards
- **Skills de apoyo:** accessibility, seo, security-auditor, data-quality-analyst, qa-test-engineer
- **Gate obligatorio:** security-auditor

## Plazos
- **Inicio comprometido:** 2026-09-15
- **Fecha limite de construccion:** 2026-09-29
- **Despliegue objetivo:** 2026-10-05 09:00 PET

## Dependencias
- TAREA-004 desplegada o aprobada internamente

## Fuentes del requerimiento
- Documento fuente: `requerimientos/30062026/Studiamatch_MVP_Requerimientos_v5.pdf`.
- Mockup fuente: `requerimientos/30062026/studiamatch_resultados.html`.
- Secciones 4.1, 4.2, 4.3 y 4.4: vista resultados, filtros, cards, paginacion y placeholders vs definitivo.
- Seccion 5: datos criticos visibles en cards/resultados.
- Seccion 6: estados de disponibilidad y logica de botones.
- Seccion 10: CA8, CA9, CA10, CA11, CA12, CA13 Resultados.

## Matriz CA -> detalle implementable
| CA | Detalle exacto del requerimiento | Implicancia tecnica | Fuera de alcance |
|---|---|---|---|
| CA8 | Barra sticky con chips removibles y limpiar todo. | Implementar estado de filtros, chips con X y reset total. | Busqueda semantica. |
| CA9/CA12 | Sidebar con disponibilidad, area, modalidad, pais, precio, duracion y `Ver mas areas`. | Filtros funcionales contra datos criticos visibles. | Ranking pagado avanzado. |
| CA10 | Distincion visual patrocinado/organico. | Cards con barra `PATROCINADO`, borde #B8D0F8 y estados organicos. | Subasta/monetizacion avanzada. |
| CA11 | Contador contextual con filtros aplicados. | Conteo y texto contextual reflejan filtros activos. | Analytics avanzado. |
| CA13 Resultados | Implementar segun mockup filtrado. | Respetar diseño, estados de card, paginacion y CTAs `Me interesa`/`Avisarme`. | Cambiar ruta canonica de detalle. |

## Alcance incluido
- Implementar vista de resultados segun `requerimientos/30062026/studiamatch_resultados.html`.
- Agregar sticky search bajo nav, chips removibles y accion `Limpiar todo`.
- Implementar sidebar con filtros por disponibilidad, area, modalidad, pais, precio y duracion.
- Distinguir cards patrocinadas y organicas, con navegacion correcta y CTAs permitidos.
- Implementar contador contextual y paginacion funcional.

## Alcance excluido
- No implementar ranking pagado avanzado ni subasta de patrocinio.
- No implementar API real de leads patrocinados en tiempo real.
- No cambiar ruta canonica de detalle fuera de la navegacion existente.
- No introducir texto `Contactar` en CTAs.
- No implementar busqueda semantica/pgvector.

## Criterios de Aceptacion
- [ ] Resultados incluyen sticky search bajo nav, chips removibles y Limpiar todo
- [ ] Sidebar filtra por disponibilidad, area, modalidad, pais, precio y duracion con pills escalables
- [ ] Cards distinguen patrocinado y organico; card navega a detalle y botones internos no navegan
- [ ] Contador contextual y paginacion reflejan filtros activos
- [ ] No se usa el texto Contactar en CTAs
- [ ] La vista respeta el mockup aprobado de resultados.
- [ ] Los filtros no rompen navegacion ni comparacion existente.
- [ ] La UI funciona en desktop y mobile.

## Matriz CA -> pruebas/evidencia
| CA | Prueba obligatoria | Tipo | Metodo / comando | Resultado esperado | Evidencia requerida |
|---|---|---|---|---|---|
| CA8 | Sticky search, chips removibles y limpiar todo. | Frontend interaction | Caso manual o test UI con filtro activo. | Chips aparecen, se remueven individualmente y `Limpiar todo` resetea filtros/resultados. | Captura/descripción de caso. |
| CA9/CA12 | Sidebar filtra por disponibilidad, area, modalidad, pais, precio y duracion. | Frontend/data | Probar cada filtro con dataset disponible. | Cada filtro modifica resultados y chips; pills escalables funcionan. | Matriz de filtros con resultado. |
| CA10 | Cards patrocinadas/organicas y navegacion correcta. | Frontend interaction | Click card y botones internos. | Card navega a detalle; `Comparar`, `Me interesa`, `Avisarme` no navegan; patrocinado visible. | Evidencia de handlers/captura. |
| CA11 | Contador y paginacion reflejan filtros. | Frontend/data | Filtrar y cambiar pagina. | Conteo/paginacion se recalculan sobre dataset filtrado. | Caso antes/despues. |
| CA13 Resultados | Vista respeta mockup y CTAs permitidos. | Visual/textual | Comparar contra `studiamatch_resultados.html` + busqueda `Contactar`. | No aparece `Contactar`; layout/CTAs/paleta coinciden o desviacion justificada. | Captura + salida busqueda. |

## Analisis tecnico previo obligatorio
- [ ] Revisar `requerimientos/30062026/studiamatch_resultados.html` y extraer layout, filtros, cards, estados y paginacion antes de editar.
- [ ] Revisar `requerimientos/30062026/Studiamatch_MVP_Requerimientos_v5.pdf` secciones 4.1 a 4.4, 5, 6, 10 y CA8-CA13.
- [ ] Revisar ruta actual de resultados: `web/src/app/courses/page.tsx`, componentes fallback/listado y cualquier uso de filtros desde Home.
- [ ] Confirmar campos disponibles por salida de TAREA-001/TAREA-002: `is_sponsored`, `sponsorship_priority`, `publication_status`, `data_quality_status`, `start_date`, `mode`, `duration`, `price_pen`, area y pais/ciudad.
- [ ] Definir ruta unica para implementar resultados antes de tocar UI, evitando duplicar logica entre Home y `/courses`.
- [ ] Revisar navegacion actual de cards, comparar y CTAs para no romper detalle/compare existente.
- [ ] Confirmar que no se implementara busqueda semantica, ranking pagado avanzado ni API real de leads patrocinados.

## Especificacion exacta del cambio

### Ruta y componentes esperados
| Elemento | Cambio exacto esperado |
|---|---|
| `web/src/app/courses/page.tsx` o ruta vigente | Shell/fetch inicial para vista de resultados si actualmente existe. |
| `CoursesFallbackPage.tsx` o equivalente | Vista cliente con filtros, chips, sidebar, cards y paginacion si esa es la ruta vigente. |
| `ResultsSearchStrip` o equivalente | Search sticky bajo nav, sincronizado con filtros activos. |
| `ActiveFilterChips` o equivalente | Chips removibles con `x` y accion `Limpiar todo`. |
| `ResultsSidebar` o equivalente | Filtros por disponibilidad, area, modalidad, pais, precio y duracion. |
| `CourseResultCard` o equivalente | Card patrocinada/organica, CTAs permitidos y navegacion controlada. |
| `ResultsPagination` o equivalente | Paginacion funcional sobre dataset filtrado. |

### Filtros requeridos
| Filtro | Campo fuente esperado | Regla |
|---|---|---|
| Disponibilidad | `start_date`/`start_date_text` + estado derivado de TAREA-002 | Estados: inscripciones abiertas, fecha proxima confirmada, sin fecha confirmada. |
| Area | `category_id`/`category` | Usar catalogo/campo vigente; pills escalables. |
| Modalidad | `mode` | Valores normalizados disponibles. |
| Pais/ciudad | `region`/`address` o campo vigente | No inventar ubicaciones; fallback si falta dato. |
| Precio | `price_pen`/estado `A consultar` | Rango funcional y soporte de precio faltante. |
| Duracion | `duration` | Filtrado por rangos simples o buckets definidos en UI. |

### Reglas de cards
- Card completa navega al detalle actual (`/courses/[institution]/[slug]`), sin migrar ruta canonica.
- Botones `Comparar`, `Me interesa` y `Avisarme` no navegan al hacer click; usar control de propagacion o estructura equivalente.
- No usar texto `Contactar` en ningun CTA de resultados.
- Card patrocinada usa estado visual diferenciado segun mockup (`PATROCINADO`, borde/paleta aprobada) sin implementar subasta/ranking pagado avanzado.
- Card organica conserva estilo diferenciado y datos criticos visibles definidos en PDF v5.

### Conteo y paginacion
- Contador debe reflejar filtros activos.
- `Limpiar todo` debe resetear filtros, chips, contador y paginacion.
- Paginacion debe operar sobre resultados filtrados, no sobre dataset original sin filtrar.

## Subtareas tecnicas
- [ ] **ST-01 — Comparar resultados actuales contra mockup aprobado**
  - Analisis previo: revisar mockup HTML y vista actual antes de editar.
  - Objetivo: listar brechas visuales/funcionales antes de editar.
  - Cambio exacto: producir checklist por layout, search sticky, chips, sidebar, cards, CTAs, contador y paginacion.
  - Archivos esperados: `requerimientos/30062026/studiamatch_resultados.html`, rutas actuales de courses/Home.
  - CAs relacionados: CA8, CA9, CA10, CA11, CA13 Resultados.
  - Validacion: checklist de brechas documentado.
- [ ] **ST-02 — Definir ruta y flujo de datos de resultados**
  - Analisis previo: revisar rutas/componentes actuales y decidir punto unico de implementacion.
  - Objetivo: decidir si la implementacion vive en `/courses`, `CoursesFallbackPage` o vista derivada de Home sin duplicar logica innecesaria.
  - Cambio exacto: documentar ruta final, props/datos iniciales, estado cliente y componentes antes de modificar UI.
  - Archivos esperados: `web/src/app/courses/page.tsx`, `CoursesFallbackPage.tsx`, `HomeContent.tsx` si aplica.
  - CAs relacionados: CA8-CA13.
  - Validacion: decision documentada antes de implementar.
- [ ] **ST-03 — Implementar sticky search y chips activos**
  - Analisis previo: mapear filtros activos y estado URL/local requerido.
  - Objetivo: search bajo nav, chips removibles y `Limpiar todo`.
  - Cambio exacto: implementar search sticky, chips con remocion individual y reset global sincronizados con resultados.
  - Archivos esperados: componentes ResultsSearchStrip/ActiveFilterChips o equivalentes.
  - CAs relacionados: CA8.
  - Validacion: filtros se agregan/remueven sin recargar innecesariamente.
- [ ] **ST-04 — Implementar sidebar de filtros**
  - Analisis previo: confirmar campos fuente disponibles para disponibilidad, area, modalidad, pais, precio y duracion.
  - Objetivo: disponibilidad, area, modalidad, pais, precio y duracion.
  - Cambio exacto: implementar controles de filtro con estado controlado y aplicacion al dataset visible.
  - Archivos esperados: ResultsSidebar o equivalente.
  - CAs relacionados: CA9, CA12.
  - Validacion: cada filtro altera resultados y chips.
- [ ] **ST-05 — Implementar pills escalables**
  - Analisis previo: revisar cantidad esperada de areas/paises y comportamiento del mockup.
  - Objetivo: `Ver mas areas/paises` sin saturar UI.
  - Cambio exacto: mostrar subset inicial y toggle expandido/colapsado para areas/paises.
  - Archivos esperados: ResultsSidebar/pill components.
  - CAs relacionados: CA9, CA12.
  - Validacion: estado expandido/colapsado funciona.
- [ ] **ST-06 — Implementar cards patrocinadas y organicas**
  - Analisis previo: confirmar campos sponsorship definidos por TAREA-001 y disponibles en datos.
  - Objetivo: diferenciar visualmente patrocinado/organico sin romper card actual.
  - Cambio exacto: renderizar badge/estilo patrocinado y fallback organico; ordenar solo si criterio simple aprobado existe.
  - Archivos esperados: CourseResultCard o equivalente.
  - CAs relacionados: CA10.
  - Validacion: badge/estado visible y orden/control documentado.
- [ ] **ST-07 — Corregir navegacion de cards y botones**
  - Analisis previo: revisar handlers actuales de card, comparar, lead y aviso.
  - Objetivo: card completa navega a detalle; `Comparar`, `Me interesa`, `Avisarme` no navegan.
  - Cambio exacto: aplicar `stopPropagation`/estructura equivalente y mantener rutas actuales de detalle/compare.
  - Archivos esperados: CourseResultCard/actions.
  - CAs relacionados: CA10.
  - Validacion: manejo de `stopPropagation` o equivalente documentado.
- [ ] **ST-08 — Implementar contador contextual y paginacion**
  - Analisis previo: definir pagina actual, tamano de pagina y conteo filtrado.
  - Objetivo: contador refleja filtros activos y paginacion respeta dataset filtrado.
  - Cambio exacto: recalcular contador y paginas despues de cada cambio de filtro; resetear pagina al filtrar/limpiar.
  - Archivos esperados: Results header/pagination components.
  - CAs relacionados: CA11.
  - Validacion: conteo cambia al filtrar y al limpiar.
- [ ] **ST-09 — Validar CTAs permitidos**
  - Analisis previo: buscar copy actual de CTAs en componentes de resultados.
  - Objetivo: asegurar que no aparece `Contactar` y que CTAs usan textos aprobados.
  - Cambio exacto: reemplazar copy no aprobado por `Me interesa`, `Avisarme` o texto aprobado por requerimiento.
  - Archivos esperados: cards/resultados.
  - CAs relacionados: CA13 Resultados.
  - Validacion: busqueda textual de `Contactar` en componentes tocados.
- [ ] **ST-10 — Revisar responsive, accesibilidad y SEO basico**
  - Analisis previo: revisar comportamiento mobile del sidebar/filtros y estructura semantica.
  - Objetivo: filtros usables en mobile, focus visible y estructura semantica.
  - Cambio exacto: asegurar labels, focus, layout mobile de filtros y headings consistentes.
  - Archivos esperados: resultados/components.
  - CAs relacionados: CA8-CA13.
  - Validacion: checklist accessibility/seo si aplica.

## Archivos afectados
| Archivo | Tipo de cambio |
|---|---|
| `web/src/app/courses/page.tsx` | Ajuste de ruta/resultados si aplica |
| `web/src/app/courses/CoursesFallbackPage.tsx` | Vista funcional de resultados/fallback |
| `web/src/app/HomeContent.tsx` | Integracion de filtros/resultados derivados desde Home si aplica |
| `web/src/components/` | Componentes ResultsSearchStrip, chips, sidebar, cards y paginacion |

## Plan de ejecucion
1. Leer EST-001, mockup Resultados y esta tarea antes de tocar codigo.
2. Definir ruta y componentes concretos antes de implementar UI.
3. Implementar search/chips, sidebar, cards, contador y paginacion en orden.
4. Validar desktop/mobile, lint/typecheck y busqueda de CTAs prohibidos.
5. Invocar accessibility/seo/security segun cambios antes de commit/PR.
6. Registrar resultado en changelog y en esta tarea.

## Validaciones requeridas
- [ ] `docker exec studiamatch-dev bash -lc "cd /app/web && npm run lint"`.
- [ ] `docker exec studiamatch-dev bash -lc "cd /app/web && npx tsc --noEmit"`.
- [ ] Revision responsive desktop/mobile.
- [ ] Busqueda textual de `Contactar` en componentes modificados.
- [ ] Checklist de filtros contra CA8-CA13.
- [ ] Ejecucion de matriz `CA -> pruebas/evidencia`.
- [ ] Revision `security-auditor` antes de commit/PR.

## Evidencia requerida
- [ ] Checklist de filtros y chips implementados.
- [ ] Caso de card patrocinada y organica.
- [ ] Caso de boton interno que no navega.
- [ ] Contador/paginacion con filtros activos.
- [ ] Salida de lint/typecheck.
- [ ] PR a `desarrollo`.

## Checklist de cierre
- [ ] CA8 cubierto.
- [ ] CA9/CA12 cubierto.
- [ ] CA10 cubierto.
- [ ] CA11 cubierto.
- [ ] CA13 Resultados cubierto.
- [ ] No aparece `Contactar` en CTAs.
- [ ] Changelog actualizado.

## Notas de implementacion
<!-- Detalles tecnicos aqui -->

## Resultado
<!-- Actualizado por la IA al completar: Fecha, commits, PR -->
