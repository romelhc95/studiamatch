# TASK-H1-001 - HITO-001

| Campo | Valor |
|---|---|
| ID | `TASK-H1-001` |
| Estado | `IN_PROGRESS` |
| Requerimiento | `REQ-EST-001` |
| Hito | [HITO-001](../../hitos/hito_001.md) |
| Fase vigente | `FASE-08` en `HUMAN_GATE` |
| Criterios | `H1-CA1`, `H1-CA2P`, `H1-CA7P` |

Esta nota es la autoridad exclusiva del estado vivo de `TASK-H1-001` y de sus criterios. La tarea no tiene subtareas.

## Objetivo Contractual

Preparar la orquestacion FG2/FG3, el schema editorial y de calidad, y la seguridad base sin saltar gates, exponer credenciales ni promover cambios no certificados.

## Arbol De Criterios

```text
TASK-H1-001
|- H1-CA1
|- H1-CA2P
`- H1-CA7P
```

Los tres criterios son hijos directos de la tarea, no subtareas.

## Criterios Y Entregables

| Criterio | Entregable | Verificacion | Evidencia | Estado |
|---|---|---|---|---|
| `H1-CA1` | Workflows automaticos y gates | Contrato F7 | PR #226, CI y validacion post-merge | Completed |
| `H1-CA2P` | Schema/RLS | Verificadores F6/F7/F8 + PostgreSQL 17 | Candidate funcional local; package bloqueado hasta Free | In Progress |
| `H1-CA7P` | Contrato documentado | Context Graph + reconciliacion | PR #221, CI y `SRC-REQ-001` reconciliada | Completed |

El detalle contractual de los tres criterios permanece en [REQ-EST-001](./_index.md), [HITO-001](../../hitos/hito_001.md) y [EST-001](../../estimaciones/est_001.md); esta tabla no agrega criterios.

## Contexto Verificable

El baseline de workflows debe contrastarse con `H1-CA1`; los comentarios no sustituyen la configuracion ejecutable. La modalidad aprobada es cadencia automatica con gates, circuit breakers y controles de ambiente.

Los nombres, adopcion Free/Pro y postcondiciones exactas se fijan en [Sistema DB](../../sistema_db_supabase.md) y [Matriz DB](../../operaciones/matriz_adopcion_db.md). No se editan ledgers historicos.

El candidate DB-as-Code vigente se registra en [Reconciliacion F6](../../operaciones/reconciliacion_db_as_code_f6.md). PR #223 incorporo el package a `desarrollo` y PR #224 cerro su portabilidad LF/CRLF. La existencia del candidate no prueba adopcion remota ni completa `H1-CA2P` antes de certificacion.

F8 agrega una closure forward-only y certificacion local reproducible documentadas en [Certificacion local Hito 1 F8](../../operaciones/certificacion_hito1_f8.md). El resultado local no habilita Free/Pro ni autoriza el backfill editorial.

## Allowlist De Implementacion

- `scripts/core/master_orchestrator.py`.
- `scripts/core/cleansing_worker.py`, `enrichment_worker.py` y `sync_vector_worker.py` para compatibilidad G1b minima.
- Frontend de detalle, comparador, catalogo y selector publico para retirar superficies G1b revocadas.
- Workflows FG1 y FG3; FG2 solo para revision contractual y el guard de refs aprobado explicitamente.
- Workflow de seguridad para convertir pruebas y build F7 en gates bloqueantes.
- `scripts/shared/db_client.py` y `check_db_parity.py` solo para lecturas fail-closed y revalidacion F7.
- Migrations forward-only nuevas para el contrato editorial, calidad y RLS.
- Tests de governance, gates del orquestador y RLS.
- Documentos canonicos enlazados desde [el indice](../../00_INDICE.md).

La ampliacion minima de allowlist anterior fue aprobada explicitamente al iniciar F7. El guard FG2 se aprobo despues como remediacion de seguridad acotada. No autoriza redisenos fuera de estas superficies.

## Exclusiones

- Vault historico, revisiones, evidencias y candidates previos.
- Manifest schema v1, dispatcher autonomo y diffs completos de ramas historicas.
- Mutacion de migrations o ledgers existentes.
- Copia de datos operativos Free hacia Pro.
- H-08 y H-09; redisenos definitivos de H-04 y H-07.

## Dependencia G1b Minima

- El paquete minimo conserva los IDs `H-01` a `H-07` y `H-10` sin publicar postcondiciones explotables.
- F7 debe mapear cada postcondicion a `H1-CA2P`, un metodo de verificacion y evidencia nueva.
- La adopcion se decide desde la [matriz DB](../../operaciones/matriz_adopcion_db.md), no desde evidencia historica.
- El frontend debe ser compatible con las superficies que el contrato aprobado retire.

H-00 no forma parte del paquete promocionable. Es DML Free-only, con autorizacion separada, respaldo remoto previo, counts-only y verificacion independiente antes de `FREE_CERTIFIED`. Nunca se aplica en Pro.

## Criterio De Salida

1. Cambios clasificados y limitados a la allowlist.
2. Migrations nuevas, forward-only e idempotentes.
3. Tests de gates, governance y RLS verdes en el entorno autorizado.
4. FG1/FG3 conservan o ajustan su cadencia automatica sin omitir gates, circuit breakers ni controles de ambiente.
5. FG2 conserva credenciales fuera del repositorio y respeta gates.
6. Frontend pasa lint, typecheck y build estatico segun el gate acordado.
7. Candidate inmutable, Context Graph PASS y aprobacion humana antes de promocion.

Ver [Arquitectura](../../arquitectura_pipeline.md), [Estimacion](../../estimaciones/est_001.md) y [Release minimo](../../operaciones/flujo_release_minimo.md).
