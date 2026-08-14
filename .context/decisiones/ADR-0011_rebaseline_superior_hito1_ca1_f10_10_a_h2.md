# ADR-0011 - Rebaseline Superior Hito 1 CA1-Only

| Campo | Valor |
|---|---|
| Estado | `APPROVED_EFFECTIVE` |
| Fecha | `2026-08-13` |
| Autoridad | Decision superior humana del Hito 1 |
| F10.10 | `SUPERSEDED_FOR_HITO_1_TRANSFERRED_TO_H2_CA2` |
| F10.9 | `REBASELINED_FG2_FG3_OPERATIONAL_REMEDIATION` |
| G4 | `PASS_CA1_FG2_FG3_ONLY_METADATA_TRANSFERRED_TO_H2` |

## Contexto

La adenda CA1-only limita Hito 1 a operacion segura FG2/FG3, schedules, gates,
circuit breakers, evidencia Production y observacion natural. ADR-0010 agrego a
esa ruta un gate de metadata cero y F10.10/M3-M9 para remediarlo. Esa decision
creo una tension de alcance: metadata, lineage, providers, revision editorial y
backfill pertenecen a `H2-CA2`, aunque quedaron bloqueando el cierre de Hito 1.

El snapshot historico de F10.9 conserva `104/224` cursos activos incompletos:
`102` sin syllabus y `2` sin syllabus ni objectives. La deuda permanece visible
y sus conteos no se alteran, reducen ni reinterpretan.

## Decision

1. Hito 1 conserva exclusivamente `H1-CA1`: operacion segura FG2/FG3,
   schedules, gates/circuit breakers, evidencia Production y tres pares
   naturales FG2 -> FG3 consecutivos durante al menos 72 horas.
2. Los `104` cursos incompletos y toda remediacion de syllabus/objectives se
   transfieren a Hito 2 como `H2-CA2` no bloqueante para Hito 1.
3. F10.10 queda `SUPERSEDED_FOR_HITO_1_TRANSFERRED_TO_H2_CA2`; M4-M9 quedan
   `NOT_EXECUTED_TRANSFERRED_TO_H2`. Ningun componente F10.10 bloquea F10.9.
4. F10.9 queda `REBASELINED_FG2_FG3_OPERATIONAL_REMEDIATION` y G4 queda
   `PASS_CA1_FG2_FG3_ONLY_METADATA_TRANSFERRED_TO_H2`.
5. ADR-0010 queda superseded unicamente para Hito 1. Su investigacion se
   preserva como antecedente de Hito 2, sin conceder ejecucion ni adopcion.
6. Las evidencias historicas, gates consumidos, runs, conteos y decisiones
   fail-closed permanecen inmutables.

## Prohibicion De Reutilizacion

Hito 2 debe producir un rebaseline nuevo. Queda prohibido reutilizar gates,
aprobaciones, payloads, manifests, readers, roles, ACL, credentials, target
bindings, transport bindings, cohortes, backups o identities de F10.10/M3. La
investigacion puede citarse; ninguna capacidad operativa se hereda.

El worktree/candidate M3 local no promovido, derivado de
`docs/f10-10-m3-ddl-free-v2-payload@c04c7c9`, queda
`HISTORICAL_NON_PROMOTABLE`. Se conserva sin eliminarlo, incorporarlo ni
mezclarlo en el candidate documental de este rebaseline.

## Consecuencias

- Metadata incompleta se registra como deuda visible
  `TRANSFERRED_NON_BLOCKING_H2_CA2`.
- F10.9 puede continuar solo mediante gates separados y aprobaciones nuevas para
  diagnostico read-only, remediaciones operativas CA1, promocion y observacion.
- Metadata cero se elimina de G9, G11 y del criterio de salida de Hito 1.
- Duplicados, lifecycle, perfiles/fuentes, inconclusos FG3, 404 y desactivacion
  siguen siendo blockers CA1.
- `EVID-H1-011/012/013`, tres pares naturales, minimo 72 horas y
  `EVID-H1-016` posterior siguen siendo obligatorios.
- Dispatches y reruns no acreditan observacion natural.

## Frontera De Esta Decision

Esta ADR autoriza solo documentacion y promocion Git por PR protegido a
`desarrollo`. No autoriza remediacion funcional, Free/Pro, SQL, DDL/DML/RPC,
providers, writers, workflows operativos, gates, schedules, environments,
secrets, Certification, Main ni Production.

El candidate y su denylist se registran en el
[boundary documental](../operaciones/rebaseline_f10_10_h1_h2_ca2_2026_08_13.md).
