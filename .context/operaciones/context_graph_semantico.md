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

- `estado_del_proyecto.md` debe declarar `F10.11`, `active_work_package = NONE` o equivalente, y `D0-D10` mientras O3 este bloqueado.
- El Plan Maestro debe mantener `H2-H5 = NOT_AUTHORIZED` y `O3 = BLOCKED`.
- El tracker debe contener las ocho secciones operativas y el bloque terminal `Prompt Cavernicola`.
- El indice debe enlazar Estado, Plan Maestro, tracker, retrospectiva, ADR R0-R3 y work packages H2-H5.
- Cada WP Sprint 1 debe permanecer `PROPOSED` hasta aprobacion humana por digest.
- Ninguna evidencia o tracker puede marcar H2 activo antes de O5 y checkout limpio.
