# REQ-EST-001 - Hito 1 Sanitizado

Esta nota es la autoridad documental del alcance aprobado y los criterios sanitizados de `REQ-EST-001`. No mantiene ni duplica estado vivo, precios, fechas o terminos comerciales.

## Alcance

| Requerimiento | Hito | Criterios | Tarea canonica |
|---|---|---|---|
| `REQ-EST-001` | [HITO-001](../../hitos/hito_001.md) | `H1-CA1`, `H1-CA2P`, `H1-CA7P` | [TASK-H1-001](tarea_001_hito_1.md) |

## Criterios Aprobados

| ID | Alcance sanitizado |
|---|---|
| `H1-CA1` | Definir o formalizar la cadencia automatica y ejecuciones de la orquestacion FG2/FG3 sin omitir gates, circuit breakers ni controles de ambiente. |
| `H1-CA2P` | Preparar parcialmente el contrato base de schema editorial, calidad y seguridad de datos para campos, fuentes, actualizacion, inicio, patrocinio y leads. |
| `H1-CA7P` | Preparar la documentacion tecnica necesaria para que los hitos posteriores consuman el contrato sin reinterpretarlo. |

No existen otros criterios aprobados para `HITO-001`. La complejidad y el esfuerzo se consultan en [EST-001](../../estimaciones/est_001.md).

## Provenance Sanitizada

- Fuente privada: `SRC-REQ-001`.
- Estado: reconciliada y aprobada sin publicar originales, paths, precios ni terminos comerciales.
- Integridad: inventario y checksums conservados en un artifact privado ignorado.
- Decision `H1-CA1`: cadencia automatica con gates, circuit breakers y controles de ambiente.
- Impacto aprobado en Hito 1: cero horas; [EST-001](../../estimaciones/est_001.md) conserva Alta/72h.
- Una intencion sin destino en Hitos 1-5 se registro como [INTAKE-002](../intake/INTAKE-002.md), fuera del alcance actual.

No existen subtareas para este paquete. El estado vigente se consulta exclusivamente en [Estado del proyecto](../../estado_del_proyecto.md) y [TASK-H1-001](tarea_001_hito_1.md).

## Dependencias Canonicas

- [Estimacion EST-001](../../estimaciones/est_001.md)
- [Arquitectura del pipeline](../../arquitectura_pipeline.md)
- [Sistema DB Supabase](../../sistema_db_supabase.md)
- [Matriz de adopcion DB](../../operaciones/matriz_adopcion_db.md)
- [Flujo de requerimientos](../../operaciones/flujo_requerimientos.md)
- [Flujo de release](../../operaciones/flujo_release_minimo.md)
