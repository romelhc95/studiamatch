# Componentes: datos y pipeline

Esta ficha agrupa los objetos DB y su relación con el pipeline. El diccionario campo-a-campo está en [database.md](../database.md); el ledger de SQL en [database_migrations.md](database_migrations.md); las estaciones/gates/writers en [pipeline.md](pipeline.md).

| Componente lógico | Fuente principal | Consumidor/contrato | Datos/estado | Prueba y límite |
|---|---|---|---|---|
| Catálogo institucional | institutions, institution_site_profiles, config/institution_sources.json | FG1, harvester, diagnostics | slug, URLs, perfil, allow/exclusion, gates | tests pipeline/discovery; no leer estado remoto. |
| Pipeline operativo | core workers y staging tables | orchestrator/workflows | raw→cleansed→enriched→courses, status/error/hash | PG17/mock y R178; no datos productivos. |
| Capa editorial | field definitions/state/audit y RPC | Admin + courses_public_effective | pipeline-owned/editorial overrides, publish/quality/availability | harness SQL/UI local; aplicación Pro no verificada. |
| Membresías e invitaciones | admin_members, invitations, membership audit | Admin/Auth/Edge | rol, actividad, onboarding, token hash y transición | UAT/harness sintéticos; identities remotas desconocidas. |
| Seguridad del DB reader | vistas/RLS/grants/gateway | frontend/BFF | campos efectivos/allowlist | tests contracts/PG17; no prueba pre-request remoto. |
| Writer excepcional | scripts/maintenance, scripts/deprecated | operación autorizada por separado | catálogo o datos operativos | no usar nombre de audit como garantía; inspeccionar script, JIT y rollback. |

No existe un único snapshot SQL que represente el remoto actual: restore_full_schema.sql y MASTER son fuentes locales históricas; Pro es el baseline de comparación. Los fixtures PG17 son desechables.

## Navegación relacionada

[Database](../database.md) · [Pipeline](pipeline.md) · [Migrations](database_migrations.md) · [Backend](../backend.md) · [Pruebas](../pruebas.md) · [HITO-002/003](../hitos/README.md) · [Decisiones](../decisiones/README.md) · [Registro](../trazabilidad/registro_fuentes_componentes.md#pipeline)

## Fuentes y relaciones

Los workers, modelos de estado, configuración de discovery y RPCs se asignan path por path en el [registro fuente-componente](../trazabilidad/registro_fuentes_componentes.md#pipeline). Los contratos de tablas y RPC que consumen están en [database](../database.md#rutinas-relevantes-por-proposito).
