# TASK-H4-001 - HITO-004

| Campo | Valor |
|---|---|
| ID | `TASK-H4-001` |
| Estado | `PENDING` |
| Requerimiento | `REQ-EST-001` |
| Hito | [HITO-004](../../hitos/hito_004.md) |
| Macrofase vigente | Ninguna; no activa |
| Subfase ejecutable | Ninguna |
| Criterios propuestos | `H4-CA5`, `H4-CA6`, `H4-CA7`, `H4-CA13H` |
| Bloqueador | Hito 3 desplegado si Home consume estado publicado/manual |

## Objetivo

Entregar Home MVP segun referencia aprobada y documentacion tecnica de Sprint
1, manteniendo static export, responsive y accesibilidad.

## Alcance

- Navbar, hero, search, pills, stats y franjas aprobadas.
- Instituciones, destacados, inscripciones abiertas y paises.
- Tipografia, cards, textos y ROI oculto.
- Selector de moneda visual/tasa estatica y placeholders aprobados.
- Documentacion de datos, pipeline y operacion.

## Exclusiones

- Tipo de cambio real.
- Pagina completa Como funciona.
- Nueva ruta SEO de detalle.
- Scraping de logos.
- Resultados/filtros del Hito 5.

## Dependencias

- Contrato publico de datos estable.
- Referencia visual aprobada y contenido final disponible.

## Entregables

- Home responsive y accesible.
- Tests static export, hydration, teclado, zoom y egress.
- Documentacion tecnica cliente y desarrollador.

## Criterios Y Entregables

| Criterio | Entregable | Verificacion | Evidencia | Estado |
|---|---|---|---|---|
| `H4-CA5` | Secciones Home | Visual, datos y responsive | Vacio hasta candidate | `PLANNED` |
| `H4-CA6` | Estilo y quick wins | Regresion visual/accesibilidad | Vacio hasta candidate | `PLANNED` |
| `H4-CA7` | Documentacion tecnica | Revision de tablas, campos y operacion | Vacio hasta candidate | `PLANNED` |
| `H4-CA13H` | Fidelidad Home | Comparacion con referencia aprobada | Vacio hasta candidate | `PLANNED` |

## Seguridad, Privacidad Y RLS

- Solo campos publicos permitidos.
- Sin secret keys, PII ni mutaciones administrativas.
- Estados de error/degradacion no exponen detalle interno.

## Criterio De Salida

Home y documentacion aprobadas, build estatico, accesibilidad, QA y produccion.

## Enlaces Canonicos

- [Requerimiento](./_index.md)
- [Hito](../../hitos/hito_004.md)
- [Estado](../../estado_del_proyecto.md)
