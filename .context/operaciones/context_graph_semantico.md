# Context Graph Semantico

> Este documento define la estructura reutilizable del grafo. No crea alcance ni autoriza ejecucion.

## Estructura Canonica

```text
.context/
├── 00_INDICE.md
├── estado_del_proyecto.md
├── backlog_tareas/<requerimiento>/
│   ├── _index.md
│   └── tarea_<NNN>_<hito>.md
├── hitos/
│   └── hito_<NNN>.md
├── decisiones/
│   └── ADR-<NNNN>_<decision>.md
├── operaciones/
│   └── plan_maestro_<requerimiento>.md
├── matrices/
│   └── matriz_hito_<NNN>.md
├── work_packages/
│   └── WP-<HITO>-<NNN>.json
├── evidencias_cliente/
│   └── <requerimiento>/
│       └── evidencia_hito_<NNN>.md
└── seguimiento/
    ├── seguimiento_<requerimiento>.md
    └── retrospectiva_<hito>.md
```

## Responsabilidades

| Documento | Responsabilidad |
|---|---|
| Estado | Unica autoridad viva de fase, tarea y WP. |
| Requerimiento | Alcance, fuentes, criterios y exclusiones. |
| Plan Maestro | Dependencias, secuencia, gates y estrategia. |
| Hito | Contrato funcional y criterio de salida. |
| TASK | Trabajo autorizable. |
| ADR | Decision irreversible o relevante. |
| Manifest | Alcance mecanizable e inmutable. |
| Matriz | Criterio, prueba, ambiente y evidencia. |
| Evidencia | Resultado observado. |
| Tracker | Dashboard operativo. |
| Retrospectiva | Tiempo, rework y mejoras. |

## Validacion Semantica Minima

- `estado_del_proyecto.md` debe declarar `F10.11`, `COMPLETED_HOMOLOGATED`, `active_work_package = NONE` o equivalente, y `HUMAN_APPROVAL_WP_H2_001_BY_DIGEST`.
- El Plan Maestro debe mantener `H2-H5 = NOT_AUTHORIZED`, O0-O5 completados y el proximo gate de aprobacion humana por digest.
- El tracker debe contener las ocho secciones operativas y el bloque terminal `Prompt Cavernicola`.
- El indice debe enlazar Estado, Plan Maestro, tracker, retrospectiva, ADR R0-R3 y work packages H2-H5.
- Cada WP Sprint 1 debe permanecer `PROPOSED` hasta aprobacion humana por digest.
- Ninguna evidencia o tracker puede marcar H2 activo antes de aprobacion humana del digest y cualquier R3 JIT requerido.

## Taxonomia De Lifecycle H2

| Campo | Valor preaprobacion H2 | Regla |
|---|---|---|
| `lifecycle_stage` | `AWAITING_DIGEST` | El siguiente gate es aprobacion humana por digest y commit candidate. |
| `gate_status` | `READY_FOR_DIGEST_APPROVAL` | O5 y checkout limpio estan completos. |
| `implementation_status` | `PLANNED_NOT_ACTIVE` | No hay cambios funcionales H2 ejecutados. |
| `work_package_status` | `PROPOSED` | No tiene metadatos de aprobacion. |
| `criteria_status` | `H2-CA2=NOT_STARTED`, `H2-CA3=NOT_STARTED` | Ningun criterio puede estar PASS/ACCEPTED antes de implementacion. |
| `acceptance_status` | `NOT_STARTED` | No existe evidencia de aceptacion H2. |
| `approval_target_lifecycle_stage` | `APPROVED_NOT_ACTIVE` | Resultado permitido por aprobacion futura; no es estado actual. |
| `approval_target_gate_status` | `APPROVED_R1` | Techo autorizado por la primera aprobacion; no concede activacion. |
| `approval_target_level` | `R1` | La primera aprobacion de H2 no puede conceder R2 ni R3. |

Los campos `approval_target_*` forman parte del payload firmado del manifest. El
estado mutable actual (`status`, `lifecycle_stage`, `gate_status`, progreso,
metadata de aprobacion y activacion) queda fuera de esa proyeccion para que una
aprobacion futura pueda registrar evidencia humana sin cambiar el digest firmado.
Un `PROPOSED` con estado actual `APPROVED_NOT_ACTIVE` o `APPROVED_R1` es una
pseudo-aprobacion y debe fallar.

## Transiciones WP Permitidas

```text
PROPOSED -> APPROVED -> ACTIVE -> COMPLETED
PROPOSED/APPROVED/ACTIVE -> REVOKED
PROPOSED/APPROVED/ACTIVE -> EXPIRED
```

`PROPOSED` no puede contener `approval_digest`, `approved_by`, `approved_at`,
`approval_reference` ni `activated_at`. `APPROVED` requiere digest coincidente,
aprobador humano, referencia de aprobacion, timestamp UTC y vigencia. `ACTIVE`
requiere ademas `activated_at` y que `active_work_package` coincida con el WP.
`APPROVED` no desbloquea paths funcionales. Solo un `ACTIVE` estructuralmente
valido y vigente puede usar `allowed_paths`, y aun asi no autoriza R2/R3 ni
operaciones remotas.

## Semantica De Paths

Los patrones de `allowed_paths` son POSIX relativos al root del repositorio. Se
rechazan paths absolutos, backslashes, `..`, segmentos `.`, patrones vacios,
wildcards globales y solapamientos allow/deny. Renames y copias validan origen y
destino.

## Binding De Aprobacion

La aprobacion humana posterior a F10.11 debe vincular externamente el digest del
manifest y el commit candidate que lo contiene. No se introduce el SHA del mismo
commit dentro del manifest para evitar dependencia circular. La primera
aprobacion de `WP-H2-001` solo puede autorizar R1; R2 y R3 requieren gates
posteriores separados.
