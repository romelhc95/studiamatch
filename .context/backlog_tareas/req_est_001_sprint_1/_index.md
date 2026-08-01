# REQ-EST-001 - Sprint 1 Sanitizado

Esta nota es la autoridad documental del alcance aprobado de Sprint 1. No
mantiene estado vivo, precios, fechas ni terminos comerciales. El estado se
consulta en [Estado del proyecto](../../estado_del_proyecto.md) y en la TASK de
cada hito.

## Fuente Y Adenda

- Fuente privada aprobada: `SRC-REQ-001`.
- Adenda propuesta: `SRC-REQ-002`, sanitizada en
  [ADENDA-REQ-EST-001-001](./adenda_cliente_001_sanitizada.md).
- Estado de la adenda: `DRAFT_PENDING_CLIENT_APPROVAL`.

Mientras la adenda no sea aprobada, la distribucion original permanece
contractual. Las notas de Hitos 2 a 5 y sus TASK documentan el plan completo,
pero no autorizan ejecucion.

## Mapa Original Aprobado

| Hito | Paquete | Criterios | Tarea canonica |
|---|---|---|---|
| [HITO-001](../../hitos/hito_001.md) | Orquestacion, schema y seguridad base | `H1-CA1`, `H1-CA2P`, `H1-CA7P` | [TASK-H1-001](./tarea_001_hito_1.md) |
| [HITO-002](../../hitos/hito_002.md) | Pipeline de campos vacios | CA3 y CA2 parcial | [TASK-H2-001](./tarea_002_hito_2.md) |
| [HITO-003](../../hitos/hito_003.md) | Panel admin | CA4 | [TASK-H3-001](./tarea_003_hito_3.md) |
| [HITO-004](../../hitos/hito_004.md) | Home y documentacion | CA5, CA6, CA7 y CA13 Home | [TASK-H4-001](./tarea_004_hito_4.md) |
| [HITO-005](../../hitos/hito_005.md) | Resultados, filtros y cards | CA8 a CA13 Resultados | [TASK-H5-001](./tarea_005_hito_5.md) |

## Criterios Aprobados Sprint 1

| CA | Alcance sanitizado |
|---|---|
| CA1 | Schedules del harvester/pipeline definidos o reactivados sin omitir gates, circuit breakers ni controles de credenciales. |
| CA2 | Schema soporta estado editorial/calidad, faltantes, fuentes, actualizacion manual, fecha de inicio, patrocinio/leads base y separacion ETL/editorial. |
| CA3 | Registros incompletos se conservan y marcan pendientes sin que campos vacios detengan el pipeline. |
| CA4 | `/admin` lista, edita y publica pendientes bajo proteccion compatible con static export. |
| CA5 | Home presenta instituciones, destacados, inscripciones abiertas y exploracion por pais. |
| CA6 | Tipografia/cards/textos aprobados y ROI oculto en vistas publicas. |
| CA7 | Documentacion tecnica describe datos, pipeline y operacion. |
| CA8 | Resultados incluye sticky search, chips removibles y limpiar filtros. |
| CA9 | Sidebar filtra por disponibilidad, area, modalidad, pais, precio y duracion. |
| CA10 | Cards distinguen patrocinado y organico. |
| CA11 | Contador contextual refleja filtros activos. |
| CA12 | Duplicado de CA9, absorbido sin doble alcance. |
| CA13 | Home y Resultados respetan referencias aprobadas en estructura, paleta, jerarquia y CTA. |

## Redistribucion Propuesta Por Adenda

La adenda propone el siguiente mapa, efectivo solo despues de aprobacion
cliente:

| Hito | Criterios normalizados | Regla |
|---|---|---|
| Hito 1 | `H1-CA1` | Cierre productivo CA1-only |
| Hito 2 | `H2-CA2`, `H2-CA3` | CA2 completo antes de integrar CA3 |
| Hito 3 | `H3-CA4` | Sin cambio |
| Hito 4 | `H4-CA5`, `H4-CA6`, `H4-CA7`, `H4-CA13H` | Sin cambio; absorbe preparacion CA7 |
| Hito 5 | `H5-CA8`, `H5-CA9`, `H5-CA10`, `H5-CA11`, `H5-CA12`, `H5-CA13R` | Sin cambio |

Los aliases `H1-CA2P` y `H1-CA7P` preservan la historia local. Si la adenda se
aprueba, su alcance pendiente pasa a `H2-CA2` y `H4-CA7`; la evidencia ya generada
puede servir como preparacion, nunca como adopcion o cierre reutilizado.

## Dependencias Entre Hitos

1. Hito 1 habilita la operacion segura del pipeline.
2. Hito 2 implementa CA2 y CA3 antes de crear una cola administrativa real.
3. Hito 3 habilita curacion/publicacion manual.
4. Hito 4 construye Home y documentacion sobre el contrato estable.
5. Hito 5 completa Resultados y filtros sobre datos/flags disponibles.

## Exclusiones Sprint 1

- Tipo de cambio real.
- Pagina completa Como funciona.
- Nueva ruta SEO canonica de detalle.
- Entrega real-time de leads por email/webhook.
- Scraping automatico de logos.
- Reviews reales.
- Busqueda semantica/embeddings.
- QA de carga masivo y automatizacion de backlog.
- Sistema final de tres estados/alertas de 60 dias mas alla de la base CA2.

## Provenance Sanitizada

- Los originales y terminos comerciales permanecen privados.
- Su custodia e integridad se conservan fuera de Git; las referencias
  `SRC-REQ-*` aportan trazabilidad sanitizada.
- La aprobacion documental no constituye autorizacion de fase.
- No existen subtareas implicitas; los work packages internos no agregan CA.

## Backlog Diferido

- [Hallazgos F9.5](./backlog_f9_5_known_findings.md).
- [Seguridad leads/email](./backlog_seguridad_leads_email.md).
- [Control-plane exec SQL](./backlog_exec_sql_control_plane.md).
- [Riesgos CA2/RLS para cliente](../../evidencias_cliente/sprint_1/anexo_h1_ca2_seguridad_rls.md).

## Dependencias Canonicas

- [Hitos Sprint 1](../../hitos/_index.md)
- [ADR-0006](../../decisiones/ADR-0006_incorporacion_adenda_sprint_1.md)
- [Arquitectura pipeline](../../arquitectura_pipeline.md)
- [Sistema DB](../../sistema_db_supabase.md)
- [Matriz DB](../../operaciones/matriz_adopcion_db.md)
- [Flujo de requerimientos](../../operaciones/flujo_requerimientos.md)
- [Flujo de release](../../operaciones/flujo_release_minimo.md)
