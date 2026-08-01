# HITO-005 - Resultados, Filtros Y Cards

`HITO-005` agrupa el paquete final de Resultados. Esta nota documenta alcance y
trazabilidad; no mantiene estado vivo.

## Alcance Propuesto

- `H5-CA8`: sticky search, chips removibles y limpiar filtros.
- `H5-CA9`: sidebar de disponibilidad, area, modalidad, pais, precio y duracion.
- `H5-CA10`: distincion visual patrocinado/organico.
- `H5-CA11`: contador contextual de resultados.
- `H5-CA12`: absorbido por CA9 sin doble alcance.
- `H5-CA13R`: Resultados segun referencia visual aprobada.

Incluye paginacion funcional, orden determinista, estados vacios/error y CTA sin
usar el texto Contactar.

La card navega al detalle; Comparar, Me interesa y Avisarme no navegan. Su
comportamiento funcional depende de los contratos disponibles y no habilita
email/webhook real-time.

## Exclusiones

- Entrega real-time de leads por email/webhook.
- Busqueda semantica con embeddings.
- Migracion de la ruta canonica de detalle.
- Sistema real de reviews.

## Dependencias

- Home y contrato visual Hito 4.
- Campos/flags CA2 disponibles y certificados cuando sean consumidos.
- Consultas PostgREST/RLS y performance de filtros verificadas.

## Trazabilidad

- [REQ-EST-001](../backlog_tareas/req_est_001_sprint_1/_index.md)
- [TASK-H5-001](../backlog_tareas/req_est_001_sprint_1/tarea_005_hito_5.md)
- [Estado del proyecto](../estado_del_proyecto.md)
