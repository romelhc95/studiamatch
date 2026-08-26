# HITO-003 - Admin Editorial

| Campo | Valor |
|---|---|
| Estado | `PRESTART_CLIENT_SOURCE_ATTESTED_AFTER_H2_CERTIFICATION` |
| Work package | `SUPERSEDED` |
| Criterio | `H3-CA4` |
| Gate | Gate fuente cliente aprobado; ejecucion requiere instruccion humana separada |

## Alcance

`/admin/`, Supabase Auth, membresia admin protegida, cola paginada, edicion allowlisted, optimistic locking, publicar/despublicar y auditoria. Debe ser compatible con static export.

## Validacion Contra Fuente Cliente

El pre-arranque de H3 valida `H3-CA4` contra la fuente privada cliente `SRC-REQ-002` mediante la atestacion sanitizada versionada [ADENDA-REQ-EST-001-001](../backlog_tareas/req_est_001_sprint_1/adenda_cliente_001_sanitizada.md). La fuente privada no se versiona ni se expone en PRs.

## Contrato De Acceso

- Usuario anonimo no accede.
- Usuario autenticado no admin no accede.
- Admin accede solo a la cola allowlisted.
- Toda mutacion exige identidad admin y deja auditoria.

## Contrato Funcional

- Cola paginada con filtros por estado editorial/calidad.
- Edicion solo de campos allowlisted.
- Optimistic locking por version o timestamp.
- Publicar/despublicar sin que pipeline pueda saltar revision.
- Auditoria append-only por cambio.
- UAT en Certification con casos positivos y negativos.

## Gate

No ejecuta codigo, DB, UI ni PR de implementacion antes de pasar el gate de fuente cliente y recibir instruccion humana separada. Playwright se habilita desde este hito para UAT y regresion visual/interactiva.
