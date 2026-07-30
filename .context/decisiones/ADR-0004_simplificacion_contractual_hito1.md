# ADR-0004 - Simplificacion Contractual De Hito 1

| Campo | Valor |
|---|---|
| ID | `ADR-0004` |
| Estado | `ACCEPTED` |
| Decision humana | Conservar F8, simplificar F9 y retirar el plan temporal en F9.4 |
| Contexto relacionado | [PLAN-H1-SIMPLIFICADO-001](../operaciones/plan_simplificado_hito1.md), [Estado vigente](../estado_del_proyecto.md) |

## Contexto

La ruta posterior a F8 agrego una definicion F9.4 remota bloqueada por controles que no corresponden a criterios adicionales de `HITO-001`. La decision humana vigente limita el Hito 1 a `H1-CA1`, `H1-CA2P` y `H1-CA7P`, conserva el trabajo contractual valido y acorta la certificacion sin eliminar gates humanos de red, datos o release.

## Decision

1. [PLAN-H1-SIMPLIFICADO-001](../operaciones/plan_simplificado_hito1.md) entra en vigor como plan operativo de Hito 1.
2. F9.4 significa exclusivamente reconciliacion contractual local y documental. No concede red, secretos, DDL, DML, migrations, backfill, H-00, pausa de writers, dispatch ni produccion.
3. La anterior definicion F9.4 `REMOTE_READ_FREE` queda `SUPERSEDED_NON_AUTHORIZABLE`. Sus artifacts F9.3 y su historia tecnica no se reescriben, pero sus blockers, adapter, OpenAPI, advisor bridge, cross-plane binding, nonce y attestations dejan de gobernar el release.
4. F9.5 fue el preflight Free read-only dirigido, sin adapter ni framework. Su gate decimal fue consumido y F9.5 cerro `COMPLETED_WITH_KNOWN_FINDINGS`; los artifacts de PR #245/#247 son `HISTORICAL_NON_PROMOTABLE` y no habilitan otra lectura.
5. La secuencia pendiente empieza en F9.6 P0 H-00 Free-only, continua con F9.7 backup/schema/RLS Free, F9.8 aprobacion de backfill, F9.9 ejecucion/certificacion de backfill y F9.10 certificacion final Free.
6. El antecedente `TEMP_PLAN_RECONSTRUCCION_MAIN_HITO1.md` se retira en F9.4 despues de preservar su informacion vigente en el Context Graph. F11 conserva el cierre final, sin otra accion sobre ese archivo.
7. `EST-001` conserva complejidad Alta y una estimacion tecnica original de 72h. Esa cifra no es obligacion contractual ni acredita por si sola el saldo real despues del avance registrado.

Esta decision sustituye solo los puntos incompatibles 4 y 8 de [ADR-0003](./ADR-0003_taxonomia_macrofases_subfases.md) y la anterior identidad F9.4. Las identidades historicas F9.1/F9.2, las macrofases F0-F11 y los gates separados para operaciones riesgosas permanecen vigentes.

[ADR-0005](./ADR-0005_corte_seguridad_funcionalidad_estabilidad_hito1.md) conserva esta historia y agrega un corte futuro/local para leads/email; no reabre F9.4-F9.6 ni modifica la simplificacion contractual adoptada aqui.

## Consecuencias

- F9.4 puede cerrarse mediante un PR exclusivamente documental, CI y aprobacion humana.
- El gate F9.5 no quedo autorizado por el cierre F9.4, fue consumido por sus intentos historicos y no es reutilizable.
- Free permanece `reconciled_not_certified`; Pro y produccion siguen bloqueados.
- La simplificacion no agrega criterios contractuales ni modifica datos o ambientes.
