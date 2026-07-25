# Matriz de adopcion DB

Estado factual al 2026-07-24. Esta matriz separa ledger, postcondicion y disponibilidad de fuente. No contiene keys ni datos operativos.

Enlaces: [Indice](../00_INDICE.md) | [Sistema DB](../sistema_db_supabase.md) | [Arquitectura pipeline](../arquitectura_pipeline.md) | [Estado del proyecto](../estado_del_proyecto.md) | [Tarea Hito 1](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md) | [Flujo release](./flujo_release_minimo.md)

## Leyenda

- `[REMOTE]`: observado con Supabase MCP.
- `[GIT]`: observado en el repositorio actual.
- `[DERIVED]`: comparacion REMOTE/GIT.

Estados permitidos:

| Estado | Significado |
|---|---|
| `ledger_applied` | Hay registro identificable y la postcondicion fue observada. |
| `observed_effective_unledgered` | La postcondicion existe, pero no hay ledger confiable que la explique. |
| `historical_free_only` | Artifact historico que nunca debe promocionarse a Pro. |
| `source_unavailable` | El SQL original no esta demostrado por un artifact con checksum. |
| `superseded` | Fuente historica reemplazada por una postcondicion o migracion posterior. |

Un ledger presente no prueba una postcondicion. Un objeto efectivo no prueba que su SQL fuente este disponible.

## Inventario de ledgers

| Evidencia | Free `aqrldlmlszjtgpqiegaa` | Pro `xwhtiqmboljkshrtviyw` | Lectura correcta |
|---|---|---|---|
| Ledger canonico | `[REMOTE]` 42 entradas | `[REMOTE]` 23 entradas | Autoridad de aplicacion MCP, no prueba por si sola de paridad |
| Ledger de proyecto | `[REMOTE]` 41; todas `version=0` | `[REMOTE]` 52; 15 `version=0` | Ledger auxiliar con semantica divergente |
| SQL Git | `[GIT]` 52 stems | `[GIT]` 52 stems | Fuente versionada hasta 2026-06-02, sin Hito 1/G1b de julio |
| Comparacion de stems | `[DERIVED]` 39 stems Git mas 2 reconciliaciones de julio | `[DERIVED]` contiene los 52 stems Git | Los 52 stems Pro no implican paridad de schema, RLS, RPC ni policies |

## Matriz por artifact o postcondicion

| Alcance | Ambiente | Evidencia de ledger | Postcondicion observada | Fuente SQL actual | Estado | Tratamiento F6 |
|---|---|---|---|---|---|---|
| Cuatro estaciones y gates F100/F121 | Free | Canonico y/o ledger de proyecto identificable | Tablas, FK, RLS, gates y constraints presentes | SQL base disponible en Git | `ledger_applied` | Conservar como baseline de postcondiciones, no copiar filas |
| Cuatro estaciones y gates F100/F121 | Pro | Registro parcial en canonico; 52 stems en ledger auxiliar | Nucleo presente, con ACL/RPC divergentes | SQL base disponible en Git | `ledger_applied` solo para objetos verificados | No elevar el conteo de stems a declaracion de paridad |
| Hito 1 editorial y RLS | Free | Seis entradas canonicas identificables | Once columnas, constraints y policies observadas | SQL de julio ausente de Git | `ledger_applied`; fuente `source_unavailable` | Recuperar artifact con checksum o sustituir con migration nueva |
| Hito 1 editorial y RLS | Pro | Sin entradas canonicas Hito 1 | Columnas, constraints y policies Hito 1 ausentes | SQL de julio ausente de Git | `source_unavailable` | Definir reconciliacion forward-only por postcondicion y backfill separado |
| G1b H01-H07/H10 y correcciones | Free | Trece entradas canonicas del paquete historico | Hardening ETL, RLS, ratings/reviews y view count observable | SQL de julio ausente de Git | `ledger_applied`; fuente `source_unavailable` | Recuperar checksums; consolidar una fuente promocionable sin replay historico |
| G1b H01-H07/H10 y correcciones | Pro | Sin entradas canonicas G1b | Ocho RPC divergen; Hito/RLS publico antiguo persiste | SQL promocionable no demostrado | `source_unavailable` | Crear reemplazo forward-only por postcondiciones, no por stems |
| H00 anonimiza PII | Free | `20260718_h00_anonymize_leads_pii` registrado | No se inspeccionaron filas ni PII | SQL fuente ausente de Git | `historical_free_only` | Mantener historico; no reejecutar ni usar como prueba de contenido |
| H00 anonimiza PII | Pro | Ausente | No inspeccionada ni requerida | No aplicable | `historical_free_only` | Exclusion mecanica obligatoria de manifests, globs y lotes Pro |
| H08 `crawler_exclusions` | Free | Entrada canonica H08 | Tabla ausente | SQL historico local de F74 existe; H08 julio no | `ledger_applied` | H08 esta fuera de G1b minimo; documentar sin promover implicitamente |
| H08 `crawler_exclusions` | Pro | Sin H08 canonico | Tabla presente y visible a roles API | Decision forward aun no versionada | `source_unavailable` | Resolver en artifact separado; nunca por replay implicito de H08 |
| Canary scoped: 4 RPC | Free | Sin entrada canonica canary inequivoca | Funciones y policies acotadas observadas | Fuente activa no identificada en Git | `observed_effective_unledgered` | Inventariar hashes y reconstruir source-of-truth sin copiar filas |
| Canary scoped: 4 RPC | Pro | Sin entrada canonica canary inequivoca | Mismos hashes de las 4 RPC scoped | Fuente activa no identificada en Git | `observed_effective_unledgered` | No afirmar paridad: `verify_release_canary_guards` diverge |
| Core RPC ETL/requeue | Free | G1b canonico registrado | Service-role-only; path vacio; unlock/mark invoker | Fuente julio no disponible | `ledger_applied`; fuente `source_unavailable` | Usar postcondiciones y hashes como contrato de reconciliacion |
| Core RPC ETL/requeue | Pro | Baseline historico registrado | Ocho definiciones/configuraciones divergen de Free | Fuentes Git son pre-G1b | `superseded` para definiciones antiguas | Sustituir con nueva migration, nunca alterar ledger ni replayar baseline |
| View count legacy | Free | H07 W4 registrado | Legacy cerrado; v2 deduplicado presente | Fuente julio ausente | `ledger_applied`; fuente `source_unavailable` | Mantener contrato cerrado en consolidacion G1b |
| View count legacy | Pro | Sin H07 W4 | Legacy `SECURITY DEFINER` ejecutable por roles API; v2 ausente | SQL nuevo no disponible | `source_unavailable` | Reconciliar con frontend y PostgREST antes de retirar superficie |
| Ratings/reviews | Free | H04/WP05 y reconciliacion Hito registrados | Solo lectura moderada; writes publicos apagados | Fuente julio ausente | `ledger_applied`; fuente `source_unavailable` | Preservar minimo; no copiar datos entre ambientes |
| Ratings/reviews | Pro | Sin H04/WP05 canonico | `PUBLIC SELECT` e `PUBLIC INSERT` efectivos | Contrato nuevo no disponible | `source_unavailable` | Reconciliar policies, ACL, columnas y frontend en migration nueva |
| Snapshots `restore_full_schema`, `production_init`, `PRODUCTION_MASTER` | Git | No son ledger vigente | Contradicen Free remoto y Hito/G1b | Archivos disponibles pero obsoletos | `superseded` | Prohibido usarlos como baseline o replay de reconciliacion |

## Drift canary y RPC

### Canary

`[REMOTE]` Hashes iguales en ambos:

| Funcion | SHA-256 prefix |
|---|---|
| `atomic_canary_sync` | `26ded2162905...` |
| `atomic_cleansing_promote_scoped` | `a9c6be6ffab1...` |
| `atomic_enrichment_promote_scoped` | `6fbdb01773fd...` |
| `lock_staging_records_scoped` | `2789ae3ecbec...` |

`verify_release_canary_guards` no coincide: Free `6a4a9ecbafd6...`; Pro `ad2aa03d99ac...`.

### RPC principal

| Funcion | Free SHA-256 prefix / modo | Pro SHA-256 prefix / modo |
|---|---|---|
| `atomic_cleansing_promote` | `f2d7f26b7b87...`, path vacio | `edfcf5744dd2...`, path mutable |
| `atomic_enrichment_promote` | `799a3c70f138...` | `4f311bcc9155...` |
| `lock_staging_records` | `2c8638aa6884...`, path vacio | `4c734beb8ddf...`, path `public` |
| `lock_cleansed_records` | `2bdd0e2e0616...`, path vacio | `eeb44abdba55...`, path mutable |
| `mark_cleansed_processing` | `0f088d885430...`, invoker | `abaee58e6ef3...`, path mutable |
| `unlock_staging_record` | `cb5e1bb3ba17...`, invoker | `5bb48dccac88...`, definer/path mutable |
| `unlock_cleansed_record` | `38370aae7c54...`, invoker | `a9ff27652d3...`, definer/path mutable |
| `requeue_pipeline_records` | `c4f07f960704...`, path vacio | `9b1248ec11e9...`, path mutable |

## Security caveats que condicionan adopcion

| Ambiente | Evidencia | Caveat | Remediation |
|---|---|---|---|
| Free | `[REMOTE Advisor]` | RLS sin policy en `_view_count_dedup`, `schema_repair_audit`, `supabase_migrations`; grants actuales fallan cerrados | [0008](https://supabase.com/docs/guides/database/database-linter?lint=0008_rls_enabled_no_policy) |
| Pro | `[REMOTE Advisor]` | Ocho funciones con `search_path` mutable | [0011](https://supabase.com/docs/guides/database/database-linter?lint=0011_function_search_path_mutable) |
| Pro | `[REMOTE Advisor]` | Leads con `WITH CHECK (true)` | [0024](https://supabase.com/docs/guides/database/database-linter?lint=0024_permissive_rls_policy) |
| Pro | `[REMOTE Advisor]` | `increment_view_count` definer ejecutable por `anon` | [0028](https://supabase.com/docs/guides/database/database-linter?lint=0028_anon_security_definer_function_executable) |
| Pro | `[REMOTE Advisor]` | `increment_view_count` definer ejecutable por `authenticated` | [0029](https://supabase.com/docs/guides/database/database-linter?lint=0029_authenticated_security_definer_function_executable) |
| Pro | `[REMOTE]` | Ratings/reviews con lectura e insercion publica; `crawler_exclusions` expuesto | Requiere nueva reconciliacion versionada |
| Ambos | `[REMOTE]` | ACL de tabla mas amplias que el minimo; `service_role` omite RLS | Aplicar minimo privilegio en el artifact F6 |

`exec_sql(text)` es `SECURITY DEFINER`, service-role-only y coincide en ambos. Sigue siendo una superficie de alto impacto y nunca debe exponerse al cliente.

## Guardrails forward-only F6

1. La unidad de comparacion es la postcondicion, no el stem ni el conteo de ledger.
2. Los ledgers son append-only: no UPDATE, DELETE ni reconstruccion retroactiva.
3. Todo SQL historico sin checksum permanece `source_unavailable`; se reemplaza con migration nueva.
4. H00 permanece `historical_free_only` y un guard mecanico debe impedir su inclusion en Pro.
5. H08/H09 estan fuera del G1b minimo; no entran por glob ni por replay accidental.
6. Schema/RLS/RPC y backfill editorial son artifacts separados. El DML futuro debe ser acotado e idempotente.
7. No se copian `staging_raw`, `cleansed_programs`, `enriched_programs` ni `courses` entre ambientes.
8. Pro genera sus datos operativos ejecutando FG2 con sus propias credenciales y gates.
9. El canary efectivo sin ledger se versiona o clasifica antes de promocion; nunca se copian filas canary.
10. Los snapshots Git `superseded` no se usan para restaurar ni reconciliar.
11. Toda reconciliacion debe verificar RLS, ACL, owner, security mode, `search_path`, objetos calificados, PostgREST y compatibilidad frontend.
12. La promocion sigue [flujo release minimo](./flujo_release_minimo.md): Free, security review, Certification y Pro solo con aprobacion explicita.
