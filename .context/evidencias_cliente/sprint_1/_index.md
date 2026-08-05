# Evidencia Cliente - Sprint 1

Este indice reserva y gobierna evidencia sanitizada. No mantiene estado vivo y
no convierte una evidencia planeada en resultado. `EVID-H1-001` es la excepcion
contractual de aprobacion de adenda y puede estar `VERIFIED` antes del candidate;
`EVID-H1-002..005` quedan `VERIFIED` por el candidate CA1-only F9.8 replay-validado
post-merge; `EVID-H1-006/007` quedan `VERIFIED` por PR #277 y CI; `EVID-H1-008`
queda `DEVIATION_ACCEPTED_FAIL_CLOSED`, no `PASS`; `EVID-H1-015` queda
`VERIFIED` por QA independiente de la desviacion; `EVID-H1-009` queda `VERIFIED`
por PR #291 y `EVID-H1-014` queda `VERIFIED_POST_MERGE_BOUNDARY`. `EVID-H1-010..013/016`
solo se promueven cuando exista canary Production, observacion o conformidad
segun corresponda.

## Estados

- `DRAFT`: estructura en preparacion.
- `PLANNED`: evidencia requerida, aun no ejecutada.
- `PENDING`: evidencia iniciada o condicionada, pendiente de revision/ejecucion adicional.
- `VERIFIED`: resultado contrastado con candidate y ambiente.
- `VERIFIED_POST_MERGE_BOUNDARY`: boundary post-merge contrastado, sin cerrar runtime ni conformidad.
- `DEVIATION_ACCEPTED_FAIL_CLOSED`: resultado negativo aceptado por decision humana como evidencia de control fail-closed; no equivale a `PASS` ni cierra el Hito.
- `PENDING_REVERIFY_MAIN_CANDIDATE`: evidencia previa suficiente para Certification pero pendiente de reverificacion contra el candidate `main`.
- `APPROVED_FOR_CLIENT`: revisado y aprobado para entrega.
- `SUPERSEDED`: reemplazado sin borrar historia.

## Paquetes

| Hito | Documento | Estado |
|---|---|---|
| Hito 1 | [Paquete Hito 1](./paquete_hito_001.md) | `DRAFT_WITH_F10_7_TECHNICAL_DELIVERY_RECORDED` |
| Hito 2 | Se crea con candidate real | `PLANNED` |
| Hito 3 | Se crea con candidate real | `PLANNED` |
| Hito 4 | Se crea con candidate real | `PLANNED` |
| Hito 5 | Se crea con candidate real | `PLANNED` |

## Anexos

- [Riesgos CA2/RLS trasladados a Hito 2](./anexo_h1_ca2_seguridad_rls.md).
- [Registro de entrega tecnica Hito 1 - 2026-08-04](./registro_entrega_tecnica_hito_001_2026-08-04.md).

## Reglas De Sanitizacion

No incluir credenciales, endpoints, project refs, UUIDs operativos, filas, PII,
payloads, SQL explotable, nombres de policies/routines sensibles, rutas privadas,
datos bancarios ni firmas.

La cobertura tecnica y las reglas para pasar de `PLANNED` a `VERIFIED` viven en
la [Estrategia de pruebas Sprint 1](../../pruebas/00_estrategia_pruebas_sprint_1.md).
