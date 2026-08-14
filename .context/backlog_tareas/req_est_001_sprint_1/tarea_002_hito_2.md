# TASK-H2-001 - HITO-002

| Campo | Valor |
|---|---|
| ID | `TASK-H2-001` |
| Estado | `PENDING_REBASELINE` |
| Requerimiento | `REQ-EST-001` |
| Hito | [HITO-002](../../hitos/hito_002.md) |
| Criterios | `H2-CA2`, `H2-CA3` |
| Subfase activa | `NONE` |

Esta nota es la autoridad del estado de `TASK-H2-001`. Su creacion recibe
alcance, pero no activa Hito 2 ni autoriza codigo, datos o ambientes.

## H2-CA2 Recibido

H2-CA2 recibe metadata incompleta, sources/lineage, providers, revision
editorial, fill-only/backfill, cohortes, pilot, lotes, restore, idempotencia y
cualquier reader/ACL futuro. Incluye la deuda historica F10.9 de `104/224`
cursos activos (`102` sin syllabus y `2` sin syllabus ni objectives), con estado
`TRANSFERRED_NON_BLOCKING_H2_CA2`.

Antes de cualquier ejecucion se exige un rebaseline H2 nuevo que derive una
cohorte vigente, defina targets, seguridad, calidad, rollback, gates y
aprobaciones propias. No puede reutilizar gates, payloads, readers, ACL,
credentials, bindings, manifests, cohortes ni capacidades F10.10/M3.

## Criterio De Activacion Futuro

Hito 2 permanece `PENDING_REBASELINE` hasta una decision humana y una subfase
decimal exacta futura. La investigacion de ADR-0010 se conserva como antecedente;
[ADR-0011](../../decisiones/ADR-0011_rebaseline_superior_hito1_ca1_f10_10_a_h2.md)
es la frontera vigente de transferencia.
