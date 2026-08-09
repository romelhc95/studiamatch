# ADR-0004 - Simplificacion Contractual De Hito 1

| Campo | Valor |
|---|---|
| ID | `ADR-0004` |
| Estado | `ACCEPTED_PARTIALLY_SUPERSEDED_BY_ADR_0006` |
| Decision humana | Conservar F8, simplificar F9, retirar el plan temporal en F9.4 y exigir executor privado digest-bound/target-bound/single-use para PR-O F9.7 |
| Contexto relacionado | [PLAN-H1-SIMPLIFICADO-001](../operaciones/plan_simplificado_hito1.md), [Estado vigente](../estado_del_proyecto.md) |

Vigencia parcial posterior: ADR-0006
aprueba la rebaseline CA1-only. La secuencia schema/backfill/free_certified de
esta ADR queda `SUPERSEDED_FOR_HITO_1` y se conserva como antecedente CA2 de
Hito 2.

## Contexto

La ruta posterior a F8 agrego una definicion F9.4 remota bloqueada por controles que no corresponden a criterios adicionales de `HITO-001`. La decision humana historica limito entonces el Hito 1 a `H1-CA1`, `H1-CA2P` y `H1-CA7P`; tras ADR-0006, ese alcance queda sustituido para Hito 1 por CA1-only y los criterios parciales pasan a hitos posteriores.

## Decision

1. [PLAN-H1-SIMPLIFICADO-001](../operaciones/plan_simplificado_hito1.md) entro en vigor en F9.4 y tras ADR-0006 queda como antecedente historico no autorizante para Hito 1.
2. F9.4 significa exclusivamente reconciliacion contractual local y documental. No concede red, secretos, DDL, DML, migrations, backfill, H-00, pausa de writers, dispatch ni produccion.
3. La anterior definicion F9.4 `REMOTE_READ_FREE` queda `SUPERSEDED_NON_AUTHORIZABLE`. Sus artifacts F9.3 y su historia tecnica no se reescriben, pero sus blockers, adapter, OpenAPI, advisor bridge, cross-plane binding, nonce y attestations dejan de gobernar el release.
4. F9.5 fue el preflight Free read-only dirigido, sin adapter ni framework. Su gate decimal fue consumido y F9.5 cerro `COMPLETED_WITH_KNOWN_FINDINGS`; los artifacts de PR #245/#247 son `HISTORICAL_NON_PROMOTABLE` y no habilitan otra lectura.
5. La secuencia pendiente original empezaba en F9.6 P0 H-00 Free-only y continuaba con F9.7 backup/schema/RLS Free, F9.8 aprobacion de backfill, F9.9 ejecucion/certificacion de backfill y F9.10 certificacion final Free; tras ADR-0006 queda sustituida para Hito 1 por F9.8 candidate local CA1-only, F9.9 Certification/canary/QA y F9.10 certificacion final/UAT/readiness.
6. La decision humana posterior a PR #262 reconcilio F9.7 con un PR-O sucesor entonces no implementado. La implementacion/certificacion local posterior quedo registrada como `CERTIFIED_LOCAL_PR_O_SUCCESSOR`; sigue sin transport remoto ejecutable, no se expone por Data API, reemplaza `public.exec_sql(text)` como estado final esperado y no concede `GO_FOR_FREE`.
7. El antecedente `TEMP_PLAN_RECONSTRUCCION_MAIN_HITO1.md` se retira en F9.4 despues de preservar su informacion vigente en el Context Graph. F11 conserva el cierre final, sin otra accion sobre ese archivo.
8. `EST-001` conserva complejidad Alta y una estimacion tecnica original de 72h. Esa cifra no es obligacion contractual ni acredita por si sola el saldo real despues del avance registrado.

Esta decision sustituye solo los puntos incompatibles 4 y 8 de [ADR-0003](./ADR-0003_taxonomia_macrofases_subfases.md) y la anterior identidad F9.4. Las identidades historicas F9.1/F9.2, las macrofases F0-F11 y los gates separados para operaciones riesgosas permanecen vigentes.

[ADR-0005](./ADR-0005_corte_seguridad_funcionalidad_estabilidad_hito1.md) conserva esta historia y agrega un corte futuro/local para leads/email; no reabre F9.4-F9.6 ni modifica la simplificacion contractual adoptada aqui.

## Consecuencias

- F9.4 puede cerrarse mediante un PR exclusivamente documental, CI y aprobacion humana.
- El gate F9.5 no quedo autorizado por el cierre F9.4, fue consumido por sus intentos historicos y no es reutilizable.
- Free permanece `UNCHANGED_NOT_ATTESTED` para este rebaseline; Pro y produccion siguen bloqueados.
- La simplificacion no agrega criterios contractuales ni modifica datos o ambientes.
- `certificacion` como rama/release permanece bloqueada hasta los gates F9.10, incluido `USER_PERSONAL_UAT=PASS` sobre candidate commit/tree inmutable.
- `USER_PERSONAL_UAT` es un hold operativo de F9.10 posterior a canary, validaciones tecnicas Certification y QA, y anterior a readiness F10; no agrega criterio, subfase ni transicion.
