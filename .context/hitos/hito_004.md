# HITO-004 - Home MVP Y Documentacion Tecnica

`HITO-004` agrupa los paquetes Home y documentacion tecnica. Esta nota
documenta alcance y trazabilidad; no mantiene estado vivo.

## Alcance Propuesto

- `H4-CA5`: secciones Home de instituciones, destacados/patrocinados,
  inscripciones abiertas y exploracion por pais.
- `H4-CA6`: tipografia, cards, textos aprobados y ROI oculto en superficies
  publicas.
- `H4-CA7`: documentacion de tablas/campos, pipeline y criterios operativos.
- `H4-CA13H`: estructura, paleta, jerarquia y CTA de Home segun referencia
  aprobada.
- Selector de moneda visual o tasa estatica, sin API real.
- Placeholders permitidos para logos, precios y conteos cuando no exista dato
  real.

## Exclusiones

- API real de tipo de cambio.
- Pagina completa Como funciona.
- Nueva ruta canonica de detalle SEO.
- Scraping automatico de logos.
- Resultados, filtros y paginacion del Hito 5.

## Dependencias

- Hito 3 desplegado si Home consume estados publicados/manuales.
- Contrato publico de datos estable y static export verificado.

## Trazabilidad

- [REQ-EST-001](../backlog_tareas/req_est_001_sprint_1/_index.md)
- [TASK-H4-001](../backlog_tareas/req_est_001_sprint_1/tarea_004_hito_4.md)
- [Estado del proyecto](../estado_del_proyecto.md)
