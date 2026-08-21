# HITO-003 - Admin Editorial

| Campo | Valor |
|---|---|
| Estado | `PENDING` |
| Work package | `WP-H3-001` |
| Criterio | `H3-CA4` |
| Gate | H2 aceptado y aprobacion digest `WP-H3-001` |

## Alcance

`/admin/`, Supabase Auth, membresia admin protegida, cola paginada, edicion allowlisted, optimistic locking, publicar/despublicar y auditoria. Debe ser compatible con static export.

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

No inicia antes de aceptar Hito 2 y aprobar `WP-H3-001`. Playwright se habilita desde este hito para UAT y regresion visual/interactiva.
