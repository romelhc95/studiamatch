# ADR-0006 - Incorporacion De Adenda Sprint 1

| Campo | Valor |
|---|---|
| ID | `ADR-0006` |
| Estado | `ACCEPTED` |
| Decision humana | Preparar la redistribucion CA1/CA2 y el mapa de cinco hitos |
| Contexto relacionado | [Adenda sanitizada](../backlog_tareas/req_est_001_sprint_1/adenda_cliente_001_sanitizada.md) |

## Contexto

La fuente privada aprobada distribuyo Sprint 1 en cinco hitos. Hito 1 incluyo
CA1 y CA2 parcial; Hito 2 ya incluyo otra parte de CA2 junto con CA3. La
validacion tecnica demostro que CA2 necesita tratarse de forma integral para no
promover schema, seguridad o comportamiento parcial.

La decision humana solicita preparar una adenda que cierre Hito 1 con CA1 en
produccion y traslade CA2 completo a Hito 2, sin modificar el alcance total ni
promover cambios CA2 con el release CA1-only.

## Decision

1. La adenda se conserva como `DRAFT_PENDING_CLIENT_APPROVAL` hasta recibir
   conformidad externa verificable.
2. Cuando sea aprobada, Hito 1 queda limitado a CA1 y Hito 2 contiene CA2
   completo antes de CA3.
3. Hito 3 conserva CA4; Hito 4 conserva CA5, CA6, CA7 y CA13 Home; Hito 5
   conserva CA8 a CA13 Resultados.
4. Los avances CA2 existentes son preparacion local de Hito 2 y no acreditan
   adopcion remota ni entran al release CA1-only.
5. Produccion conserva su comportamiento actual para leads/email durante Hito
   1.
6. La documentacion versionada no contiene terminos comerciales privados. La
   adenda comercial y su aprobacion viven en artifacts ignorados.
7. Cada Hito tiene una nota de alcance y una unica TASK como autoridad de su
   estado vivo. Solo la TASK activa y [Estado del proyecto](../estado_del_proyecto.md)
   mantienen estado.
8. La evidencia cliente se crea por candidate real; los documentos previstos
   se mantienen `DRAFT` o `PLANNED` hasta verificarse.
9. Ninguna aprobacion documental sustituye el gate decimal de ejecucion.
10. Se permite crear indices y paquetes de evidencia en estado `DRAFT` o
    `PLANNED` antes del candidate, por decision humana explicita de esta
    autorizacion. Esto sustituye solo esa restriccion de ADR-0002; ningun draft
    puede marcarse `VERIFIED` sin candidate real.

## Fuentes Autorizadas

- Fuente privada original: `SRC-REQ-001`.
- Adenda privada propuesta: `SRC-REQ-002`.
- Alcance normalizado: [REQ-EST-001](../backlog_tareas/req_est_001_sprint_1/_index.md).
- Estado vivo: [Estado del proyecto](../estado_del_proyecto.md) y la TASK activa.

## Relacion Con Decisiones Previas

- [ADR-0001](./ADR-0001_autoridad_fuentes_context_graph.md) conserva sus
  principios; ADR-0006 generaliza el mapa de autoridad de una TASK a cinco.
- [ADR-0002](./ADR-0002_ciclo_requerimientos_privados.md) sigue vigente y
  gobierna sanitizacion, aprobacion y evidencia privada.
- [ADR-0003](./ADR-0003_taxonomia_macrofases_subfases.md) sigue exigiendo
  autorizacion decimal.
- [ADR-0004](./ADR-0004_simplificacion_contractual_hito1.md) y
  [ADR-0005](./ADR-0005_corte_seguridad_funcionalidad_estabilidad_hito1.md)
  conservan la historia local F9; sus rutas CA2 no forman parte del candidate
  productivo CA1-only si la adenda es aprobada.

## Relacion Con Autoridad Tecnica

Git determina el comportamiento versionado. Un avance local CA2 no se considera
entregado ni aplicado hasta que exista candidate, adopcion remota y evidencia
del Hito 2. El release Hito 1 debe demostrar por object IDs y diff cerrado que
las superficies CA2 permanecen iguales al baseline productivo.

## Consecuencias

- La estructura Obsidian queda aceptada; la adenda requiere aprobacion cliente
  antes de cambiar el alcance vigente.
- Hito 1 puede cerrarse con CA1-only despues de produccion observada.
- Hito 2 aumenta su alcance interno a CA2 completo + CA3.
- El cronograma se recalcula desde la aprobacion de la adenda.
- Hitos 2 a 5 quedan documentados pero `PENDING`.
- El trabajo terminal F9.7 no comprometido se clasifica como WIP CA2 no
  promocionable y no se mezcla con este PR documental.

## Enlaces

- [Adenda sanitizada](../backlog_tareas/req_est_001_sprint_1/adenda_cliente_001_sanitizada.md)
- [Hitos Sprint 1](../hitos/_index.md)
- [Plan de cierre Hito 1](../operaciones/plan_cierre_hito1_ca1_only.md)
- [Evidencia cliente](../evidencias_cliente/sprint_1/_index.md)
