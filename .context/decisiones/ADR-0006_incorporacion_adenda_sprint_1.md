# ADR-0006 - Incorporacion De Adenda Sprint 1

| Campo | Valor |
|---|---|
| ID | `ADR-0006` |
| Estado | `ACCEPTED` |
| Decision humana | Adoptar la rebaseline CA1-only y el mapa contractual de cinco hitos |
| Contexto relacionado | [Adenda sanitizada](../backlog_tareas/req_est_001_sprint_1/adenda_cliente_001_sanitizada.md) |

## Contexto

La fuente privada aprobada distribuyo Sprint 1 en cinco hitos. Hito 1 incluyo
CA1 y CA2 parcial; Hito 2 ya incluyo otra parte de CA2 junto con CA3. La
validacion tecnica demostro que CA2 necesita tratarse de forma integral para no
promover schema, seguridad o comportamiento parcial.

La decision humana confirmo que el cliente aprobo integralmente `SRC-REQ-002`,
incluidos alcance, cronograma y condiciones revisadas. La evidencia privada se
conserva fuera de Git y solo se registra una atestacion sanitizada.

## Decision

1. La adenda `ADENDA-REQ-EST-001-001` pasa a `APPROVED_EFFECTIVE`.
2. Hito 1 queda limitado exclusivamente a `H1-CA1`.
3. Hito 2 contiene `H2-CA2` completo antes de `H2-CA3`.
4. Hito 3 conserva `H3-CA4`; Hito 4 conserva `H4-CA5`, `H4-CA6`, `H4-CA7` y
   `H4-CA13H`; Hito 5 conserva `H5-CA8` a `H5-CA13R`.
5. `H1-CA2P` y `H1-CA7P` se preservan solo como antecedentes historicos; su
   alcance pendiente se traslada a `H2-CA2` y `H4-CA7` sin reutilizar evidencia
   historica como cierre.
6. Los avances CA2 existentes son preparacion local de Hito 2 y no acreditan
   adopcion remota ni entran al release CA1-only.
7. Produccion conserva su comportamiento actual para leads/email durante Hito
   1.
8. La documentacion versionada no contiene terminos comerciales privados. La
   adenda comercial y su aprobacion viven en artifacts ignorados.
9. Cada Hito tiene una nota de alcance y una unica TASK como autoridad de su
   estado vivo. Solo la TASK activa y [Estado del proyecto](../estado_del_proyecto.md)
   mantienen estado.
10. `EVID-H1-001` puede quedar `VERIFIED` como aprobacion contractual; las
    evidencias `EVID-H1-002..016` permanecen `PLANNED` hasta candidate,
    ambientes, observacion y conformidad final.
11. Ninguna aprobacion documental sustituye el gate decimal de ejecucion.
12. F9.7 queda cerrada documentalmente por rebaseline; F9.8 queda como subfase
    activa para candidate local CA1-only y requiere su frase exacta.

## Fuentes Autorizadas

- Fuente privada original: `SRC-REQ-001`.
- Adenda privada aprobada: `SRC-REQ-002`.
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
  conservan la historia local F9; sus rutas CA2 quedan superseded para Hito 1 y
  son antecedente de Hito 2, no candidate productivo CA1-only.

## Relacion Con Autoridad Tecnica

Git determina el comportamiento versionado. Un avance local CA2 no se considera
entregado ni aplicado hasta que exista candidate, adopcion remota y evidencia
del Hito 2. El release Hito 1 debe demostrar por object IDs y diff cerrado que
las superficies CA2 permanecen iguales al baseline productivo.

## Consecuencias

- La estructura Obsidian queda aceptada; la adenda cambia el alcance vigente
  desde esta rebaseline.
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
