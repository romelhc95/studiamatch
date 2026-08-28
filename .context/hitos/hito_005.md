# HITO-005 - Resultados Publicos

| Campo | Valor |
|---|---|
| Estado | `PLANNED_AFTER_H2_CONTRACT_STABLE` |
| Work package | `SUPERSEDED` |
| Criterios | `H5-CA8`, `H5-CA9/CA12`, `H5-CA10`, `H5-CA11`, `H5-CA13R` |
| Gate | Contrato H2 estable |

## Alcance

Resultados publicos fieles a `SRC-UI-RESULTS-001`: search sticky, chips removibles, clear-all, filtros, URL/back-forward, panel movil, contador contextual, orden determinista, paginacion, cards, patrocinados primero y estados loading/empty/error.

## Filtros Exactos

- Disponibilidad.
- Area.
- Modalidad.
- Pais.
- Precio.
- Duracion.

## Contrato De Interaccion

- URL query contract para filtros y busqueda.
- Back/forward preserva estado.
- Reset de pagina al cambiar filtros.
- Sidebar desktop y panel/drawer movil.
- Chips removibles y clear-all.
- Contador contextual refleja filtros activos.
- Cuatro estados de card: patrocinado, organico, abierto y sin fecha confirmada.
- Patrocinados primero con orden secundario determinista.
- Loading, empty y error/retry.
- Precio `A consultar` cuando falte precio.
- Fecha `Sin confirmar` cuando falte fecha.
- Ruta de detalle canonica `/programas/[slug]`.
- Cero captura de leads y cero egress.
