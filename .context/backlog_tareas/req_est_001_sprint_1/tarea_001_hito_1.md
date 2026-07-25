# Tarea 001 - Hito 1

Estado: `PENDING`
Requerimiento: `REQ-EST-001 Sprint 1`
Criterios: CA1, CA2 parcial, preparacion CA7

## Objetivo Contractual

Preparar la orquestacion FG2/FG3, el schema editorial y de calidad, y la seguridad base sin saltar gates, exponer credenciales ni promover cambios no certificados.

## Criterios

### CA1

- Definir los schedules del harvester y pipeline sin saltar gates.
- Mantener FG2 con secrets suministrados por GitHub Environments.
- Convertir FG1 y FG3 a manual-only con autorizacion explicita, si la revision contractual lo confirma.
- Aplicar los gates de institucion antes del `limit` del orquestador.

Estado actual: FG1 y FG3 todavia tienen `schedule` YAML activo ademas de `workflow_dispatch`. Los comentarios de desactivacion no cambian ese hecho. Manual-only es el objetivo a implementar y revisar.

### CA2 Parcial

- Versionar soporte de estado editorial y calidad en `courses` y schema relacionado.
- Cubrir campos faltantes, fuente manual o scraping, timestamps y proxima fecha de inicio.
- Preparar las bases de leads y patrocinio con RLS publica/admin separada y anti-spoofing.
- Mantener al writer compatible con `publication_status`.

Los nombres, adopcion Free/Pro y postcondiciones exactas se fijan en [Sistema DB](../../sistema_db_supabase.md) y [Matriz DB](../../operaciones/matriz_adopcion_db.md). No editar ledgers historicos.

### Preparacion CA7

Documentar tablas, campos, RLS, comportamiento del pipeline y decisiones operativas para que los hitos siguientes no reinterpreten el contrato.

## Allowlist De Implementacion

- `scripts/core/master_orchestrator.py`.
- Workflows FG1 y FG3; FG2 solo para revision de compatibilidad contractual.
- Migrations forward-only nuevas para el contrato editorial, calidad y RLS.
- Tests de governance, gates del orquestador y RLS.
- Documentos canonicos enlazados desde [el indice](../../00_INDICE.md).

## Exclusiones

- Vault historico, revisiones, evidencias y candidates previos.
- Manifest schema v1, dispatcher autonomo y diffs completos de ramas historicas.
- Mutacion de migrations o ledgers existentes.
- Copia de datos operativos Free hacia Pro.
- H-08 y H-09; redisenos definitivos de H-04 y H-07.

## Dependencia G1b Minima

- H-01: RPC ETL solo para service role.
- H-02: owner, mode, `search_path` y objetos calificados.
- H-03: `cleansed_programs` no publico.
- H-04: mutaciones de ratings/reviews apagadas.
- H-05: helpers de test retirados y estado processing cerrado.
- H-06: ACL minima acoplada.
- H-07: view count legacy apagado.
- H-10: requeue y `updated_at` seguros; razon canonica `pipeline_gate=false`.
- Frontend compatible con superficies revocadas.

H-00 no forma parte del paquete promocionable. Es DML Free-only, con autorizacion separada, respaldo remoto previo, counts-only y verificacion independiente antes de `FREE_CERTIFIED`. Nunca se aplica en Pro.

## Criterio De Salida

1. Cambios clasificados y limitados a la allowlist.
2. Migrations nuevas, forward-only e idempotentes.
3. Tests de gates, governance y RLS verdes en el entorno autorizado.
4. FG1/FG3 reflejan la decision manual-only sin cron activo, si queda aprobada.
5. FG2 conserva credenciales fuera del repositorio y respeta gates.
6. Frontend pasa lint, typecheck y build estatico segun el gate acordado.
7. Candidate inmutable, Context Graph PASS y aprobacion humana antes de promocion.

Ver [Arquitectura](../../arquitectura_pipeline.md), [Estimacion](../../estimaciones/est_001.md) y [Release minimo](../../operaciones/flujo_release_minimo.md).
