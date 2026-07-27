# Sistema DB Supabase

Snapshot canonico observado vigente. Resume el estado aplicado de Supabase sin publicar identificadores de proyecto, endpoints, credenciales, hashes, conteos de ledger ni detalles de findings. Las decisiones de adopcion se toman exclusivamente en la [matriz canonica de adopcion DB](./operaciones/matriz_adopcion_db.md).

Enlaces canonicos: [Indice](./00_INDICE.md) | [Arquitectura pipeline](./arquitectura_pipeline.md) | [Estado del proyecto](./estado_del_proyecto.md) | [Tarea Hito 1](./backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md) | [Flujo release](./operaciones/flujo_release_minimo.md) | [Matriz DB](./operaciones/matriz_adopcion_db.md)

## Autoridad y evidencia

- `[REMOTE]`: observacion de catalogos, RLS, roles, funciones, policies, advisors y ledgers de los ambientes Free y Pro.
- `[GIT]`: migraciones y snapshots disponibles en el repositorio.
- `[DERIVED]`: comparacion entre estado remoto, ledger, postcondicion y fuente Git.
- Una entrada de ledger no prueba por si sola una postcondicion.
- Una postcondicion observada no prueba que su SQL fuente este versionado.

Este archivo es el snapshot canonico observado. No sustituye la matriz ni registra decisiones de promocion.

## Ambientes

| Ambiente | Uso |
|---|---|
| Free | Desarrollo y certificacion del contrato DB |
| Pro | Produccion |

`[REMOTE]` Ambos ambientes usan roles publicos sujetos a RLS, un rol privilegiado reservado al pipeline y un rol canary acotado. Las credenciales privilegiadas no pertenecen al cliente.

## Pipeline de cuatro estaciones

```text
staging_raw -> cleansed_programs -> enriched_programs -> courses
```

`[REMOTE]` Las cuatro estaciones existen en Free y Pro, con relaciones por institucion, RLS y gates de procesamiento. Los datos operativos pertenecen a cada ambiente y no forman parte de DB-as-Code.

Regla inmutable:

- No copiar entre ambientes `staging_raw`, `cleansed_programs`, `enriched_programs` ni `courses`.
- Pro genera sus propios datos operativos mediante el pipeline y sus gates.
- Catalogos, schema, RLS, RPC y configuracion versionada se promueven por artifacts forward-only.

## Adopcion Hito 1 y G1b

Trazabilidad: `H1-CA1`, `H1-CA2P`, `H1-CA7P`.

- `[REMOTE Free]` Se observaron efectos del contrato Hito 1 y del hardening G1b.
- `[REMOTE Free]` [Gate B F9.7](./operaciones/gate_b_f9_7.md) observo en modo read-only drift de acceso incompatible con el gate y se detuvo antes de HTTP, aprobaciones operativas o DDL.
- `[REMOTE Pro]` La adopcion equivalente no esta demostrada; F6 confirmo divergencia por postcondicion.
- `[GIT/DERIVED]` Los bundles preservados recuperan consolidados verificables, pero no demuestran el SQL historico aplicado byte a byte. F6 creo fuentes nuevas forward-only en un manifest cerrado.
- `[GIT]` F6-F8 son la base funcional contractual de Hito 1. Los artifacts F9.5 de PR #245/#247 son `HISTORICAL_NON_PROMOTABLE` y no cambian el snapshot observado.
- H-00 es P0 `historical_free_only`, queda excluido de Pro y cerro `H00_ALREADY_REMEDIATED_NO_DML`: la cohorte con PII directa remediada se conserva pseudonimizada bajo riesgo aceptado; Gate B DELETE fue sustituido.
- Los objetos y diferencias sensibles permanecen en el artifact privado ignorado. El contrato publicable F6 vive en la [reconciliacion DB-as-Code](./operaciones/reconciliacion_db_as_code_f6.md).

## Ledgers y fuentes

- `[REMOTE]` Free y Pro tienen historiales de ledger distintos.
- `[GIT]` El repositorio contiene una linea base anterior al paquete completo Hito 1/G1b.
- `[DERIVED]` La presencia de todos los stems Git en un ledger auxiliar Pro no implica paridad con Free.
- `[DERIVED]` Existen efectos sin atribucion canonica inequivoca y se clasifican `observed_effective_unledgered`.
- `[DERIVED]` El SQL historico no recuperado con checksum se clasifica `source_unavailable`.
- `[GIT/REMOTE]` Los snapshots DB historicos que contradicen el remoto se clasifican `superseded` y no son baseline de restauracion.

## Caveats de seguridad publicables

`[REMOTE]` Existen hallazgos de seguridad y hardening pendientes que condicionan la certificacion Free. La documentacion publica no enumera clases explotables, objetos ni identidades.

Los detalles tecnicos se conservan solo en el artifact privado local ignorado. Ninguna credencial, secreto, PII ni fila operativa se registra alli.

## Guardrails forward-only F6

1. Comparar y adoptar postcondiciones, no conteos ni stems.
2. Mantener los ledgers append-only; no actualizar, borrar ni reconstruir historia.
3. Recuperar artifacts historicos solo con checksum verificable.
4. Si la fuente no se demuestra, mantener `source_unavailable` y crear una migracion nueva forward-only.
5. Mantener H-00 como P0 `historical_free_only`, enlazar su [cierre F9.6](./operaciones/cierre_h00_f9_6.md) y excluirlo mecanicamente de Pro.
6. Separar schema/RLS/RPC de cualquier backfill editorial.
7. Todo backfill futuro debe ser acotado, idempotente, auditable y aprobado.
8. No copiar datos operativos entre Free y Pro.
9. Clasificar y versionar la superficie canary antes de promocionarla.
10. No usar snapshots `superseded` como baseline ni replay.
11. Verificar RLS, grants, owner, modo de seguridad, path, PostgREST y compatibilidad frontend.
12. Seguir el [flujo release minimo](./operaciones/flujo_release_minimo.md) y requerir aprobacion explicita para Pro.

La clasificacion por alcance y ambiente vive en la [matriz canonica de adopcion DB](./operaciones/matriz_adopcion_db.md).
