# TASK-H2-001 - HITO-002

| Campo | Valor |
|---|---|
| ID | `TASK-H2-001` |
| Estado | `PENDING` |
| Requerimiento | `REQ-EST-001` |
| Hito | [HITO-002](../../hitos/hito_002.md) |
| Macrofase vigente | Ninguna; no activa |
| Subfase ejecutable | Ninguna |
| Criterios vigentes pendientes | `H2-CA2`, `H2-CA3` |
| Bloqueador | Cierre productivo de Hito 1 y activacion explicita de Hito 2 |

Esta TASK sera la unica autoridad del estado vivo de Hito 2 cuando se active.
Su existencia no autoriza implementacion.

## Objetivo

Completar el contrato CA2 y adaptar el pipeline para conservar y clasificar
programas incompletos sin detener el procesamiento.

## Alcance

- Schema editorial/calidad y separacion de estados ETL.
- Faltantes, fuentes, actualizacion manual y fecha de inicio.
- Patrocinio/leads base sin entrega real-time.
- RLS, grants y RPC/vistas estrictamente necesarias.
- Harvester/cleansing/enrichment/sync preservando parciales.
- Estado pendiente/completo, backfill y adopcion por ambiente.

## Exclusiones

- `/admin` y autenticacion administrativa.
- Home y Resultados.
- Email/webhook real-time de leads.
- Embeddings, reviews reales y scraping de logos.

## Dependencias

- [TASK-H1-001](./tarea_001_hito_1.md) completada en produccion.
- Plan DB forward-only, transport autorizado y backup/restore probado.

## Work Packages Internos

`H2A` y `H2B` son work packages tecnicos dentro del unico Hito 2. No son hitos,
entregables comerciales independientes, subtareas, fases ni eventos de pago.

- `WP-H2-CA2`: candidate CA2, migrations, RLS y matriz por rol.
- `WP-H2-CA3`: pipeline CA2/CA3, backfill, QA y evidencia por ambiente.
- Diccionario de datos y runbook de recuperacion.

## Criterios Y Entregables

| Criterio | Entregable | Verificacion | Evidencia | Estado |
|---|---|---|---|---|
| `H2-CA2` | Contrato schema/seguridad completo | PostgreSQL, PostgREST y pruebas por rol | Vacio hasta candidate | `PLANNED` |
| `H2-CA3` | Pipeline de incompletos | Tests de parciales, idempotencia y backfill | Vacio hasta candidate | `PLANNED` |

## Metodo De Verificacion

- [Matriz de pruebas Hito 2](../../pruebas/02_matriz_tests_hito_2.md), toda en
  `PLANNED` hasta candidate y activacion del Hito.
- PostgreSQL soportado, rollback/replay y ledger/checksums.
- Roles publico, autenticado, pipeline y admin.
- Pipeline con campos vacios, paginacion y fallos parciales.
- Canary, cleanup, smoke y evidencia sanitizada por ambiente.

## Seguridad, Privacidad Y RLS

- Minimo privilegio y separacion browser/backend/admin.
- Ninguna secret key en frontend.
- Leads/email real-time permanece excluido.
- Hallazgos previos se resuelven integralmente, no mediante excepciones parciales.

## Riesgos O Bloqueos

- Catalogo invisible por estado editorial sin backfill.
- Drift de grants/policies entre ambientes.
- Migracion parcial o transport no certificado.
- Datos incompletos que se pierdan o se publiquen sin control.

## Criterio De Salida

CA2 y CA3 certificados por ambiente, backfill idempotente, RLS por rol y
evidencia aprobada. No activa Hito 3 hasta completar este resultado.

## Enlaces Canonicos

- [Requerimiento](./_index.md)
- [Hito](../../hitos/hito_002.md)
- [Estado](../../estado_del_proyecto.md)
- [Riesgos CA2](../../evidencias_cliente/sprint_1/anexo_h1_ca2_seguridad_rls.md)
