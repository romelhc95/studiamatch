# TASK-H5-001 - HITO-005

| Campo | Valor |
|---|---|
| ID | `TASK-H5-001` |
| Estado | `PENDING` |
| Requerimiento | `REQ-EST-001` |
| Hito | [HITO-005](../../hitos/hito_005.md) |
| Macrofase vigente | Ninguna; no activa |
| Subfase ejecutable | Ninguna |
| Criterios vigentes pendientes | `H5-CA8`, `H5-CA9`, `H5-CA10`, `H5-CA11`, `H5-CA12`, `H5-CA13R` |
| Bloqueador | Home y datos/flags base listos |

## Objetivo

Entregar Resultados con busqueda, filtros, chips, cards, conteo y paginacion
segun referencia aprobada.

## Alcance

- Sticky search y chips removibles.
- Sidebar escalable por disponibilidad, area, modalidad, pais, precio y duracion.
- Cards patrocinadas/organicas y acciones sin navegacion accidental.
- La card navega al detalle; Comparar, Me interesa y Avisarme no navegan y no
  usan el texto Contactar.
- Contador contextual, orden y paginacion deterministas.
- Estados vacios, error y responsive.

## Exclusiones

- Email/webhook real-time de leads.
- Busqueda semantica.
- Sistema real de reviews.
- Migracion de detalle canonico SEO.

## Dependencias

- Hito 4 y contrato visual publico.
- Campos CA2 consumidos por filtros certificados y con indices adecuados.

## Entregables

- Vista de Resultados y componentes.
- Semantica URL/query y filtros PostgREST.
- Tests de accesibilidad, performance, conteo y paginacion.

## Criterios Y Entregables

| Criterio | Entregable | Verificacion | Evidencia | Estado |
|---|---|---|---|---|
| `H5-CA8` | Search/chips | UI, query y accesibilidad | Vacio hasta candidate | `PLANNED` |
| `H5-CA9` | Sidebar/filtros | Semantica y escalabilidad | Vacio hasta candidate | `PLANNED` |
| `H5-CA10` | Cards patrocinadas/organicas | Orden, badge y navegacion | Vacio hasta candidate | `PLANNED` |
| `H5-CA11` | Contador | Consistencia con filtros | Vacio hasta candidate | `PLANNED` |
| `H5-CA12` | Absorbido en CA9 | Sin doble alcance | Vacio hasta candidate | `PLANNED` |
| `H5-CA13R` | Fidelidad Resultados | Comparacion con referencia | Vacio hasta candidate | `PLANNED` |

## Seguridad, Privacidad Y RLS

- Queries solo sobre campos publicos permitidos.
- Sin credenciales privilegiadas ni PII.
- Limites/paginacion que eviten abuso y respuestas masivas.

## Metodo De Verificacion

La [matriz de pruebas Hito 5](../../pruebas/05_matriz_tests_hito_5.md) permanece
`PLANNED`; CA12 reutiliza CA9 sin crear doble alcance.

## Criterio De Salida

Resultados completos, filtros/conteos consistentes, build, QA y produccion.

## Enlaces Canonicos

- [Requerimiento](./_index.md)
- [Hito](../../hitos/hito_005.md)
- [Estado](../../estado_del_proyecto.md)
