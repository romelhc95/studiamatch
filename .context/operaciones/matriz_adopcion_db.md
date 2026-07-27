# Matriz de adopcion DB

Nota canonica para decisiones de adopcion Supabase desde F5. Separa ledger, postcondicion y fuente. El estado observado que la sustenta vive en el [snapshot canonico del sistema DB](../sistema_db_supabase.md); esta matriz no compite con ese snapshot.

Enlaces canonicos: [Indice](../00_INDICE.md) | [Sistema DB](../sistema_db_supabase.md) | [Arquitectura pipeline](../arquitectura_pipeline.md) | [Estado del proyecto](../estado_del_proyecto.md) | [Tarea Hito 1](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md) | [Flujo release](./flujo_release_minimo.md)

## Evidencia

- `[REMOTE]`: observacion de los ambientes Free y Pro.
- `[GIT]`: fuente o snapshot disponible en el repositorio.
- `[DERIVED]`: comparacion entre ledger, fuente y postcondicion.

## Estados de adopcion

| Estado | Uso canonico |
|---|---|
| `ledger_applied` | Hay registro identificable y la postcondicion fue observada. |
| `observed_effective_unledgered` | La postcondicion existe, pero no hay ledger canonico inequivoco que la explique. |
| `historical_free_only` | Artifact historico exclusivo de Free; nunca se promociona a Pro. |
| `source_unavailable` | El SQL original no esta demostrado por un artifact con checksum. |
| `superseded` | Fuente historica reemplazada por una postcondicion o migracion posterior. |

## Regla de lectura

Las columnas de ledger y postcondicion son independientes. `ledger presente` no equivale a `postcondicion efectiva`, y `postcondicion efectiva` no equivale a `fuente disponible`.

## Matriz canonica

| Alcance | Ambiente | Ledger | Postcondicion | Fuente | Estado de adopcion | Decision F6 |
|---|---|---|---|---|---|---|
| Cuatro estaciones y gates | Free | Evidencia identificable | Efectiva | Base Git disponible | `ledger_applied` | Conservar como contrato; no copiar filas |
| Cuatro estaciones y gates | Pro | Evidencia parcial y auxiliar | Efectiva con drift | Base Git disponible | `ledger_applied` solo para postcondiciones verificadas | No inferir paridad por stems |
| Hito 1 (`H1-CA1`, `H1-CA2P`, `H1-CA7P`) | Free | Evidencia identificable | Efectiva | Base funcional F6-F8; artifacts F9.5 no promocionables | `ledger_applied` y `source_unavailable` | Certificar base F6-F8; H-00 cerrado sin DML y backfill separado |
| Hito 1 (`H1-CA1`, `H1-CA2P`, `H1-CA7P`) | Pro | Sin evidencia de adopcion completa | Pendiente/divergente | Base F6-F8 aun no aplicada | `source_unavailable` | Promover solo package certificado y sin H-00 |
| G1b promocionable | Free | Evidencia identificable | Efectiva; closure F7 no aplicado | Package F6/F7 forward-only | `ledger_applied` y `source_unavailable` | Certificar package en Free sin replay |
| G1b promocionable | Pro | Sin evidencia de adopcion completa | Pendiente de reconciliacion | Package F6/F7, aun no aplicado | `source_unavailable` | Promover por postcondicion despues de Free |
| H-00 P0 | Free | [Evidencia sanitizada F9.6](./cierre_h00_f9_6.md) | PII directa remediada; cohorte pseudonimizada | Operacion historica separada, no package contractual | `historical_free_only` | `H00_ALREADY_REMEDIATED_NO_DML`; Gate B DELETE sustituido, verificar acceso en F9.7 y nunca promover a Pro |
| H-00 P0 | Pro | Ausente | No aplicable | No aplicable | `historical_free_only` | Prohibicion mecanica obligatoria |
| Efectos sin fuente canonica | Free/Pro | Sin atribucion inequivoca | Observados | Fuente activa no identificada | `observed_effective_unledgered` | Inventariar y versionar sin copiar filas |
| Snapshots DB historicos | Git | No son ledger vigente | Contradicen el remoto actual | Disponibles pero obsoletos | `superseded` | Prohibido usarlos como baseline o replay |

## Categorias de reconciliacion F6

1. Contrato de schema y acceso.
2. Procedencia de fuentes y migrations.
3. Alineacion de ledger y postcondiciones.
4. Compatibilidad de pipeline, release y frontend.

Los detalles tecnicos sensibles para operar esta reconciliacion permanecen en un artifact privado local excluido de Git. Esta matriz no publica identificadores de proyecto, endpoints, hashes, conteos, findings explotables ni URLs especificas de remediation.

El candidate y sus exclusiones se describen en [Reconciliacion DB-as-Code F6](./reconciliacion_db_as_code_f6.md); su compatibilidad G1b se mapea en [Certificacion F7](./certificacion_g1b_f7.md).

## Cierre Contractual F9.5

F6-F8 permanecen como base funcional contractual de Hito 1. Los artifacts de F9.5 introducidos por PR #245 y PR #247 son `HISTORICAL_NON_PROMOTABLE`: se preservan para trazabilidad, no se eliminan en esta fase y no son fuente, candidate, package contractual ni replay aplicable.

`H-00` es P0 separado y obligatorio antes de `FREE_CERTIFIED`, pero no agrega un criterio a `H1-CA1`, `H1-CA2P` ni `H1-CA7P`. El backfill editorial queda como dependencia `H1-CA2P` de F9.8/F9.9 para evitar que el catalogo quede invisible.

## Cierre F9.6 H-00

La [verificacion sanitizada](./cierre_h00_f9_6.md) confirmo la cohorte con PII directa remediada y conservada como pseudonimizada. El data owner acepta el riesgo residual de UUID/metadatos en Free restringido. Gate B DELETE queda `SUPERSEDED_NON_AUTHORIZABLE`; no hubo DML, backup valido, acceso Pro, schema, migrations, writers ni backfill. F9.7 debe verificar ausencia de lectura publica; F11 revaluara la retencion.

## Guardrails forward-only F6

1. La unidad de adopcion es la postcondicion verificable.
2. Los ledgers son append-only.
3. Un stem coincidente no prueba paridad.
4. Toda fuente historica sin checksum permanece `source_unavailable`.
5. H-00 permanece `historical_free_only`, cierra como `H00_ALREADY_REMEDIATED_NO_DML` y queda fuera de todo manifest Pro.
6. Los artifacts fuera del minimo no entran por glob ni replay accidental.
7. Schema/RLS/RPC y backfill editorial se mantienen separados.
8. No se copian `staging_raw`, `cleansed_programs`, `enriched_programs` ni `courses` entre ambientes.
9. Pro genera sus datos operativos con su propio pipeline y gates.
10. La superficie canary se versiona antes de promocion; nunca se copian filas canary.
11. Las fuentes `superseded` no se restauran ni se reejecutan.
12. Toda reconciliacion verifica RLS, grants, owner, modo de seguridad, path, PostgREST y frontend por comportamiento semantico, no por conteos nominales de policies.
13. La promocion sigue el [flujo release minimo](./flujo_release_minimo.md) y requiere aprobacion explicita para Pro.
