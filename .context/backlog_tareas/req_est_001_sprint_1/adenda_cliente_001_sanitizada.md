# ADENDA-REQ-EST-001-001 - Redistribucion De Hitos Sprint 1

| Campo | Valor |
|---|---|
| ID | `ADENDA-REQ-EST-001-001` |
| Estado | `APPROVED_EFFECTIVE` |
| Requerimiento | `REQ-EST-001` |
| Fuente privada | `SRC-REQ-002` |
| Decision interna | Aprobada y adoptada por autorizacion humana en F9.7; preservada por O0-B en F10.11 |
| Vigencia | Efectiva desde `2026-08-01`; revalidada documentalmente en F10.11 |

Esta nota conserva el delta sanitizado aprobado. No contiene precios, condiciones de pago, firmas, datos bancarios, credenciales, datos personales, rutas privadas ni identificadores operativos. La evidencia privada de aprobacion permanece fuera de Git; la atestacion publicable vive como `EVID-H1-001` en el [paquete de evidencia Hito 1](../../evidencias_cliente/sprint_1/paquete_hito_001.md).

## Proposito

Cerrar Hito 1 con CA1 desplegado en produccion y trasladar CA2 completo al Hito 2, donde se integra con CA3. La redistribucion no agrega alcance a Sprint 1 ni habilita implementacion, despliegue o cambios de datos.

## Delta Aprobado

| Materia | Distribucion original | Distribucion vigente por adenda |
|---|---|---|
| Hito 1 | CA1, CA2 parcial y preparacion CA7 | CA1 exclusivamente |
| Hito 2 | CA3 y CA2 parcial | CA2 completo y CA3 |
| Hito 3 | CA4 | Sin cambio |
| Hito 4 | CA5, CA6, CA7 y CA13 Home | Sin cambio; absorbe la preparacion CA7 pendiente |
| Hito 5 | CA8 a CA13 Resultados | Sin cambio; CA12 absorbido por CA9 |

## Hito 1 Vigente

Hito 1 conserva exclusivamente `H1-CA1`:

- schedules y ejecucion segura del harvester/pipeline como antecedente contractual;
- FG2 y FG3 como alcance cliente de CA1;
- FG1 como soporte operativo de inventario, sin crear un criterio adicional;
- gates, limites y circuit breakers;
- secrets solo en CI/environments autorizados;
- promocion selectiva `local -> desarrollo -> certificacion -> main`;
- evidencia de funcionamiento productivo.

El release Hito 1 debe conservar sin cambios funcionales las superficies CA2: schema, RLS, RPC, frontend, leads/email, backfill, campos editoriales y tooling DB. Los aliases `H1-CA2P` y `H1-CA7P` quedan solo como antecedentes historicos.

## Hito 2 Vigente

Hito 2 empieza por CA2 y luego integra CA3:

1. schema editorial/calidad, faltantes, fuentes, actualizacion manual e inicio;
2. constraints, indices, RLS y contratos de acceso;
3. campos y flags base de patrocinio/leads, sin entrega comercial real-time;
4. pipeline tolerante a datos parciales;
5. marcado pendiente/completo y persistencia de CA2;
6. aplicacion, backfill y pruebas por ambiente bajo gates propios.

## Leads Y Email

Hito 1 conserva el comportamiento productivo actual. H2-H5 pueden preparar schema/flags y representar el CTA visual, pero no autorizan captura real de leads, `POST /leads`, almacenamiento, email, webhook ni egress. La entrega real-time por email/webhook permanece excluida de Sprint 1.

## Schedules Y Writers

Aunque CA1 menciona schedules definidos o reactivados, F10.11 no activa schedules ni writers. En el estado actual, activarlos puede ejecutar FG1, FG2 o FG3 con secret key, scraping, enriquecimiento, sync o integridad. Permanecen fail-closed hasta aprobacion JIT R3 posterior a H2:

```text
AUTOMATION_ENABLED=false
PRODUCTION_WRITERS_PAUSED=true
```

## Motivo Del Traslado De CA2

La validacion encontro que aplicar solo una parte del contrato CA2 puede dejar permisos, reglas y procesos internos inconsistentes entre ambientes. El riesgo se gestiona evitando un despliegue parcial y completando CA2 como unidad en Hito 2.

## Condiciones Sin Cambio

- Sprint 1 conserva cinco hitos.
- El alcance total no cambia; el detalle economico revisado permanece privado.
- Las integraciones comerciales de leads siguen excluidas.
- Todo cambio DB se versiona, valida primero fuera de produccion y requiere aprobacion separada para promoverse.
- La aprobacion de esta adenda no sustituye la frase decimal de ejecucion.
- ADR-0026 y ADR-0027 sustituyen referencias operativas legacy para F10.11; ningun ADR legacy reabre ejecucion.

## Efectividad

La aprobacion cliente integral de `SRC-REQ-002` fue verificada de forma privada y registrada de forma sanitizada como `EVID-H1-001`. Desde F10.11:

1. [REQ-EST-001](./_index.md) adopta el mapa revisado como alcance vigente.
2. [ADR-0026](../../decisiones/ADR-0026_cutoff_h1_y_baseline_sprint1.md) fija cutoff y baseline Sprint 1.
3. [ADR-0027](../../decisiones/ADR-0027_work_packages_y_convergencia.md) fija work packages y convergencia.
4. Hitos 2 a 5 permanecen pendientes hasta su activacion individual.

La aprobacion abarca integralmente el artifact privado `SRC-REQ-002`, incluido alcance, cronograma y condiciones revisadas. Ese detalle no se publica en Git.

## Enlaces

- [REQ-EST-001](./_index.md)
- [Plan Maestro Sprint 1 H2-H5](../../operaciones/plan_maestro_sprint1_h2_h5.md)
- [Plan de cierre Hito 1](../../operaciones/plan_cierre_hito1_ca1_only.md)
- [ADR-0026](../../decisiones/ADR-0026_cutoff_h1_y_baseline_sprint1.md)
- [ADR-0027](../../decisiones/ADR-0027_work_packages_y_convergencia.md)
