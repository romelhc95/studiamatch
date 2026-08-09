# ADENDA-REQ-EST-001-001 - Redistribucion De Hitos Sprint 1

| Campo | Valor |
|---|---|
| ID | `ADENDA-REQ-EST-001-001` |
| Estado | `APPROVED_EFFECTIVE` |
| Requerimiento | `REQ-EST-001` |
| Fuente privada | `SRC-REQ-002` |
| Decision interna | Aprobada y adoptada por autorizacion humana en F9.7 |
| Vigencia | Efectiva desde `2026-08-01` tras evidencia privada verificada |

Esta nota conserva el delta sanitizado aprobado. No contiene precios,
condiciones de pago, firmas, datos bancarios, credenciales, datos personales,
rutas privadas ni identificadores operativos. La evidencia privada de aprobacion
permanece fuera de Git; la atestacion publicable vive como `EVID-H1-001` en el
[paquete de evidencia Hito 1](../../evidencias_cliente/sprint_1/paquete_hito_001.md).

## Proposito

Cerrar Hito 1 con CA1 desplegado en produccion y trasladar CA2 completo al
Hito 2, donde se integra con CA3. La redistribucion no agrega alcance a Sprint
1 ni habilita implementacion, despliegue o cambios de datos.

## Delta Aprobado

| Materia | Distribucion original | Distribucion vigente por adenda |
|---|---|---|
| Hito 1 | CA1, CA2 parcial y preparacion CA7 | CA1 exclusivamente |
| Hito 2 | CA3 y CA2 parcial | CA2 completo y CA3 |
| Hito 3 | CA4 | Sin cambio |
| Hito 4 | CA5, CA6, CA7 y CA13 Home | Sin cambio; absorbe la preparacion CA7 pendiente |
| Hito 5 | CA8 a CA13 Resultados | Sin cambio |

## Hito 1 Vigente

Hito 1 conserva exclusivamente `H1-CA1`:

- schedules y ejecucion segura del harvester/pipeline;
- FG2 y FG3 como alcance cliente de CA1;
- FG1 como soporte operativo de inventario, sin crear un criterio adicional;
- gates, limites y circuit breakers;
- secrets solo en CI/environments autorizados;
- promocion selectiva `local -> desarrollo -> certificacion -> main`;
- evidencia de funcionamiento productivo.

El release Hito 1 debe conservar sin cambios funcionales las superficies CA2:
schema, RLS, RPC, frontend, leads/email, backfill, campos editoriales y tooling
DB. Los aliases `H1-CA2P` y `H1-CA7P` quedan solo como antecedentes historicos.

## Hito 2 Vigente

Hito 2 empieza por CA2 y luego integra CA3:

1. schema editorial/calidad, faltantes, fuentes, actualizacion manual e inicio;
2. constraints, indices, RLS y contratos de acceso;
3. campos y flags base de patrocinio/leads, sin entrega comercial real-time;
4. pipeline tolerante a datos parciales;
5. marcado pendiente/completo y persistencia de CA2;
6. aplicacion, backfill y pruebas por ambiente bajo gates propios.

## Leads Y Email

Hito 1 conserva el comportamiento productivo actual. No promueve retiro de UI,
tombstone, automatizacion, schema ni reglas nuevas de leads/email. La entrega
real-time por email/webhook permanece excluida de Sprint 1.

## Motivo Del Traslado De CA2

La validacion encontro que aplicar solo una parte del contrato CA2 puede dejar
permisos, reglas y procesos internos inconsistentes entre ambientes. El riesgo
se gestiona evitando un despliegue parcial y completando CA2 como unidad en
Hito 2. El resumen no tecnico vive en el
anexo de seguridad y RLS.

## Condiciones Sin Cambio

- Sprint 1 conserva cinco hitos y seis paquetes.
- El alcance total no cambia; el detalle economico revisado permanece privado.
- Las integraciones comerciales de leads siguen excluidas.
- Todo cambio DB se versiona, valida primero fuera de produccion y requiere
  aprobacion separada para promoverse.
- La aprobacion de esta adenda no sustituye la frase decimal de ejecucion.

## Efectividad

La aprobacion cliente integral de `SRC-REQ-002` fue verificada de forma privada y
registrada de forma sanitizada como `EVID-H1-001`. Desde esta rebaseline:

1. ADR-0006
   conserva el mapa aprobado como autoridad contractual.
2. [REQ-EST-001](./_index.md) adopta el mapa revisado como alcance vigente.
3. Hito 1 continua hasta obtener evidencia productiva CA1-only.
4. Hitos 2 a 5 permanecen `PENDING` hasta su activacion individual.

La aprobacion abarca integralmente el artifact privado `SRC-REQ-002`, incluido
alcance, cronograma y condiciones revisadas. Ese detalle no se publica en Git.

## Enlaces

- [REQ-EST-001](./_index.md)
- Hitos Sprint 1
- [Plan de cierre Hito 1](../../operaciones/plan_cierre_hito1_ca1_only.md)
- Flujo de requerimientos
- ADR-0002
