# Preservacion Y Retiro Del Plan Temporal F9.4

## Estado

- Antecedente: `TEMP_PLAN_RECONSTRUCCION_MAIN_HITO1.md`.
- Resultado: `PRESERVED_AND_RETIRED` al fusionar la reconciliacion F9.4.
- Autoridad vigente: [Estado del proyecto](../estado_del_proyecto.md), [PLAN-H1-SIMPLIFICADO-001](./plan_simplificado_hito1.md) y [ADR-0004](../decisiones/ADR-0004_simplificacion_contractual_hito1.md).

Esta nota conserva solo informacion vigente. El tablero, los heads iniciales, los estados intermedios, el siguiente paso F5 y la estimacion de 14-20 jornadas del antecedente eran historia sustituida; Git, los PR y los changelogs preservan esa trazabilidad sin convertirla en estado vivo.

La comprobacion comparativa se realizo localmente antes del retiro y clasifico las 23 secciones del antecedente. No se accedio a red ni a ambientes DB.

## Informacion Preservada

- La ruta F0-F11 y sus resultados vigentes se mantienen en [Estado del proyecto](../estado_del_proyecto.md).
- La topologia y adopcion DB viven en [Sistema DB](../sistema_db_supabase.md) y [Matriz DB](./matriz_adopcion_db.md), sin duplicar identificadores operativos.
- El alcance contractual vive en [REQ-EST-001](../backlog_tareas/req_est_001_sprint_1/_index.md), [HITO-001](../hitos/hito_001.md) y [TASK-H1-001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md).
- El release sigue siendo secuencial, fail-closed, Free antes de Pro, con PR, CI y aprobacion humana en [Flujo de release](./flujo_release_minimo.md).
- No se usa force-push, no se relajan branch protections y no se usa `git reset --hard` contra ramas remotas.
- Se mantiene un solo workspace operativo; no se crean worktrees persistentes y las ramas temporales se retiran despues de su merge o cierre autorizado.
- Un hallazgo nuevo solo entra en la ruta critica si bloquea seguridad, integridad de datos, reproducibilidad del release o un criterio contractual.
- No se abre una segunda rama funcional mientras exista un PR activo del Hito 1; el trabajo ajeno a Free certificada o produccion se envia al backlog.

## Backups Preservados

Los artifacts permanecen fuera del repositorio y no se mueven, editan ni compactan hasta completar produccion y observacion.

| Artifact logico | Ref preservada | SHA-256 |
|---|---|---|
| `g1b-r7-local.bundle` | `40d88862124e8f84c6050fc6273a8b01a75b02de` | `05DD5B8AEFF7EF2D3435A3047A964FFF8533F6B98C0221973CAB81C23D7DFE55` |
| `hito1-r6-local.bundle` | `20fd179c5743e53355af900170735c36da2879ce` | `727204B58091C9B1E6D82ED0DA84E4CAA1D2BD048E1B57D51AE9917F2D188268` |

La nota no publica rutas locales, credenciales, PII ni identificadores de proyectos.

## Disposicion De F0-F4

- F0-F4 permanecen `COMPLETED`; sus resultados vivos estan en el snapshot canonico.
- Los detalles intermedios, inventarios temporales y reparaciones de PR son evidencia historica, no dependencias ejecutables.
- Las reglas de preservacion, Git y workspace que continuan vigentes quedan explicitadas arriba.
- El retiro del antecedente no elimina historia Git, backups ni evidencia externa, y no autoriza limpiar ninguno de ellos.

## Matriz De Disposicion

| Secciones del antecedente | Informacion vigente preservada en | Disposicion del resto |
|---|---|---|
| 1-2 Objetivo y principios | Esta nota, ADR-0003/ADR-0004 y flujo de release | Narrativa inicial sustituida |
| 3 Baselines y backups | Tabla de bundles de esta nota y politica de resguardo del flujo | Heads/conteos iniciales historicos |
| 4 Ambientes DB | Sistema DB y matriz de adopcion | Identificadores operativos no se duplican |
| 5-6 Estados y tablero | Estado del proyecto y taxonomia canonica | Tablero temporal sustituido |
| 7-12 F0-F5 | Estado del proyecto, changelogs y PR historicos | Checklists intermedios no autoritativos |
| 13-18 F6-F11 | Notas canonicas F6, F7, F8, F9, plan simplificado y flujo | Secuencia anterior sustituida donde ADR-0004 aplica |
| 19 Gates humanos | Flujo de release y macrofase F9 | Gates consumidos permanecen historia |
| 20 Coste y alcance | REQ-EST-001, TASK-H1-001 y reglas de esta nota | Reglas duplicadas retiradas |
| 21 Estimacion | EST-001 | 14-20 jornadas sustituida |
| 22 Registro | Git, PR y changelogs | No determina estado vivo |
| 23 Proximo paso | Estado del proyecto | F5 pendiente era obsoleto |
