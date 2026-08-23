# REQ-EST-001 - Sprint 1 Sanitizado

Esta nota es la autoridad documental sanitizada del alcance aprobado de Sprint 1. No mantiene estado vivo, precios, fechas ni terminos comerciales. El estado ejecutable se consulta en [Estado del proyecto](../../estado_del_proyecto.md), en la TASK de cada hito y en el work package aprobado por digest.

## Fuente Y Adenda

| Fuente | Uso | Estado |
|---|---|---|
| `SRC-REQ-001` | Requerimiento privado original `Studiamatch_MVP_Requerimientos_v5.docx` | Custodia local, no versionado |
| `SRC-REQ-002` | Adenda cliente aprobada | Sanitizada en [ADENDA-REQ-EST-001-001](./adenda_cliente_001_sanitizada.md) |
| `SRC-UI-HOME-001` | `studiamatch_home.html` | Referencia visual, no versionada |
| `SRC-UI-RESULTS-001` | `studiamatch_resultados.html` | Referencia visual, no versionada |

Hashes vigentes de fuentes locales:

| Fuente | SHA-256 |
|---|---|
| `SRC-REQ-001` | `3537820f93f3a6880bba22109c020cedb4334f1afd905acea70e809c9748b107` |
| `SRC-UI-HOME-001` | `3e84696c000a9f9875853145c8c2cf227e606a5b5f8527184328629c3b1a135d` |
| `SRC-UI-RESULTS-001` | `9c2ca7660b412a63b22b355f5345f4c28afc73477c1dc6e9d04f770aecd1c32c` |

Los archivos fuente privados no deben versionarse. Solo se versiona esta trazabilidad sanitizada.

## Precedencia

1. Decision humana O0-B.
2. [ADENDA-REQ-EST-001-001](./adenda_cliente_001_sanitizada.md).
3. [Plan Maestro Sprint 1 H2-H5](../../operaciones/plan_maestro_sprint1_h2_h5.md).
4. Seccion Sprint 1 de `SRC-REQ-001`.
5. Resto de `SRC-REQ-001` como contexto/backlog.
6. `SRC-UI-HOME-001` y `SRC-UI-RESULTS-001` como referencia visual.
7. Codigo existente solo como compatibilidad tecnica.

Cualquier conflicto se resuelve a favor de la fuente superior. Esta nota no autoriza ejecucion; tras F10.11 la frase decimal queda como trazabilidad y la autorizacion operativa requiere work package aprobado por digest y commit candidate.

## Mapa Contractual Vigente

| Hito | Criterios normalizados | Regla |
|---|---|---|
| [HITO-001](../../hitos/hito_001.md) | `H1-CA1` | Cerrado contractualmente con waivers por O0-B. |
| [HITO-002](../../hitos/hito_002.md) | `H2-CA2`, `H2-CA3` | CA2 completo antes de CA3; requiere digest y JIT R3 para DDL/DML. |
| [HITO-003](../../hitos/hito_003.md) | `H3-CA4` | Panel admin bloqueado por H2 aceptado y `WP-H3-001`. |
| [HITO-004](../../hitos/hito_004.md) | `H4-CA5`, `H4-CA6`, `H4-CA7`, `H4-CA13H` | Home publica fiel a HTML; cero captura/egress. |
| [HITO-005](../../hitos/hito_005.md) | `H5-CA8`, `H5-CA9/CA12`, `H5-CA10`, `H5-CA11`, `H5-CA13R` | Resultados y filtros fieles a HTML; CA12 absorbido por CA9. |

Los aliases `H1-CA2P` y `H1-CA7P` preservan historia local solamente. Su alcance pendiente pasa a `H2-CA2` y `H4-CA7`; evidencia previa puede servir como antecedente, nunca como cierre reutilizado.

## Criterios Aprobados Sprint 1

| CA | Alcance sanitizado |
|---|---|
| CA1 | Schedules del harvester/pipeline definidos o reactivados solo con gates, circuit breakers y controles de credenciales. En F10.11 permanecen fail-closed hasta JIT R3 posterior a H2. |
| CA2 | Schema soporta estado editorial/calidad, faltantes, fuentes, actualizacion manual, fecha de inicio, patrocinio/leads base y separacion ETL/editorial. |
| CA3 | Registros incompletos se conservan y marcan pendientes sin que campos vacios detengan el pipeline. |
| CA4 | `/admin` lista, edita y publica pendientes bajo proteccion compatible con static export. |
| CA5 | Home presenta instituciones, destacados, inscripciones abiertas y exploracion por pais. |
| CA6 | Tipografia/cards/textos aprobados y ROI oculto en vistas publicas. |
| CA7 | Documentacion tecnica describe datos, pipeline, operacion, gates y evidencia. |
| CA8 | Resultados incluye sticky search, chips removibles y limpiar filtros. |
| CA9 | Sidebar filtra por disponibilidad, area, modalidad, pais, precio y duracion. |
| CA10 | Cards distinguen patrocinado y organico. |
| CA11 | Contador contextual refleja filtros activos. |
| CA12 | Duplicado de CA9, absorbido sin doble alcance. |
| CA13 | Home y Resultados respetan referencias aprobadas en estructura, paleta, jerarquia, tipografia y CTA. |

## Disposiciones Sprint 1

| Materia | Disposicion vinculante |
|---|---|
| Leads | H2-H5 permiten schema/flags y CTA visual; prohibidos `POST /leads`, almacenamiento de lead, email, webhook o egress. |
| CTA | Visible segun diseno, sin captura ni notificacion. Si requiere accion durante H4/H5, solo navegacion interna no transaccional. |
| Ruta detalle | La ruta canonica de contrato es `/programas/[slug]`. La pagina SEO completa queda backlog salvo navegacion minima acordada por WP. |
| Moneda | API de tipo de cambio fuera de Sprint 1. Un selector visual solo puede usar tasas referenciales del mockup y quedar marcado como no integrado a API. |
| ROI | Oculto en vistas publicas durante H4/H5. |
| Schedules | `AUTOMATION_ENABLED=false` y `PRODUCTION_WRITERS_PAUSED=true` hasta aprobacion JIT R3 posterior a H2. |
| Fuentes HTML | Valores, precios y conteos son placeholders salvo que el WP exija datos reales desde backend; estructura, paleta, Inter y jerarquia visual si son referencia. |

## Dependencias Entre Hitos

1. Hito 1 habilita la operacion segura del pipeline como antecedente cerrado.
2. Hito 2 implementa CA2 y CA3 antes de crear una cola administrativa real.
3. Hito 3 habilita curacion/publicacion manual y pruebas UAT.
4. Hito 4 construye Home y documentacion sobre contrato estable.
5. Hito 5 completa Resultados y filtros sobre datos/flags disponibles.

## Exclusiones Sprint 1

- API real de tipo de cambio.
- Pagina completa Como funciona.
- Entrega real-time de leads por email/webhook.
- Captura o almacenamiento comercial de leads.
- Scraping automatico de logos.
- Reviews reales.
- Busqueda semantica/embeddings.
- QA de carga masivo y automatizacion de backlog.
- Sistema final de tres estados/alertas de 60 dias mas alla de la base CA2.

## Provenance Sanitizada

- Los originales y terminos comerciales permanecen privados.
- Su custodia e integridad se conservan fuera de Git; las referencias `SRC-*` aportan trazabilidad sanitizada.
- La aprobacion documental no constituye autorizacion de fase.
- No existen subtareas implicitas; los work packages internos no agregan CA.

## Dependencias Canonicas

- [Estado del proyecto](../../estado_del_proyecto.md)
- [Plan Maestro Sprint 1 H2-H5](../../operaciones/plan_maestro_sprint1_h2_h5.md)
- [ADR-0026](../../decisiones/ADR-0026_cutoff_h1_y_baseline_sprint1.md)
- [ADR-0027](../../decisiones/ADR-0027_work_packages_y_convergencia.md)
- [Flujo de release](../../operaciones/flujo_release_minimo.md)
- [Baseline, preservacion y homologacion](../../operaciones/baseline_preservacion_homologacion_sprint1.md)
