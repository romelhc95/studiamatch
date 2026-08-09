# ADR-0003 - Macrofases, Subfases Y Alias Historicos

| Campo | Valor |
|---|---|
| ID | `ADR-0003` |
| Estado | `ACCEPTED` |
| Decision humana | Restaurar explicitamente el plan temporal inicial `main -> Hito 1` |
| Contexto relacionado | [Estado vigente](../estado_del_proyecto.md), Certificacion macro F9 |

Vigencia parcial: [ADR-0004](./ADR-0004_simplificacion_contractual_hito1.md) sustituye el momento de retiro del plan temporal y la identidad de F9.4/F9.5. ADR-0006 sustituye para Hito 1 CA1-only la ruta `free_certified` por readiness F9.10 y F10 Production, sin renombrar F0-F11 ni los aliases historicos. Las identidades historicas y la taxonomia F0-F11 de esta ADR permanecen vigentes.

## Contexto

El plan temporal inicial fijo macrofases F0-F11: F9 certifica Hito 1 en Free, F10 promueve a Pro/produccion y F11 cierra el ciclo. Durante la preparacion Free se usaron `FASE-09` y `FASE-10` para dos packages locales. Esa numeracion historica colisiono con las macrofases originales y presento incorrectamente F11/F12 como nuevas fases principales.

Los commits, PR, manifests, package IDs, runners y checks historicos son evidencia inmutable y no deben renombrarse. La autoridad viva si debe volver a representar el plan aprobado.

## Decision

1. Las macrofases canonicas conservan exclusivamente los IDs F0-F11 y los significados del plan inicial.
2. F9 significo certificacion completa de Hito 1 en Free hasta `free_certified`; para la ruta CA1-only aprobada, ADR-0006 sustituye ese final por readiness F9.10 para F10 Production.
3. F10 significa promocion a Pro, canary, `main`, smoke y observacion.
4. F11 significa cierre final y retiro mediante PR de `TEMP_PLAN_RECONSTRUCCION_MAIN_HITO1.md`.
5. Las unidades ejecutables dentro de una macrofase usan ID decimal, por ejemplo `F9.3`.
6. `FASE-09`, `fase09-*` y sus PR identifican historicamente el package local mapeado a F9.1.
7. `FASE-10`, `F10-HITO1-PROMOTION-CONTRACT-20260725`, `fase10-*` y sus PR identifican historicamente el package local mapeado a F9.2; no significan macro F10 Produccion.
8. Las reservas no ejecutadas denominadas F11/F12 quedan sustituidas por F9.4/F9.5; F9.3 congela antes el contrato local que hara verificable la lectura remota. No se reescribe evidencia historica.
9. Solo una subfase definida, enlazada como activa y aprobada puede autorizar ejecucion. La frase debe incluir el ID completo: `Ejecuta las tareas pendientes de la Fase F9.3`.
10. Una frase que nombre solo la macrofase o un alias historico permite analizar y reconciliar el plan, pero no agrupa automaticamente lecturas remotas, DDL, DML, backfill o produccion.

## Estado Restaurado

| Macrofase | Significado | Estado |
|---|---|---|
| F0-F8 | Preparacion, convergencia y candidate funcional | `COMPLETED` |
| F9 | Certificacion Hito 1 en Free | `IN_PROGRESS` |
| F10 | Pro y produccion | `PENDING` |
| F11 | Cierre final | `PENDING` |

F9.1 y F9.2 estan completas. Esta decision propone la definicion de F9.3 local; se vuelve autoritativa solo al fusionar su PR. Ninguna subfase remota queda autorizada por esta decision.

## Consecuencias

- El plan temporal sigue siendo antecedente congelado; `.context/` conserva la autoridad documental segun ADR-0001.
- Los artifacts historicos mantienen sus bytes e identificadores.
- F9 vuelve a ser una macrofase con gates separados; cada operacion riesgosa conserva aprobacion propia.
- F10 y F11 recuperan sus significados originales y no pueden adelantarse.
