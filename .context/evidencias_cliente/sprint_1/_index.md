# Evidencia Cliente - Sprint 1

Este indice reserva y gobierna evidencia sanitizada. No mantiene estado vivo y
no convierte una evidencia planeada en resultado. Los paquetes se crean o
promueven a `VERIFIED` solo cuando existe un candidate real.

## Estados

- `DRAFT`: estructura en preparacion.
- `PLANNED`: evidencia requerida, aun no ejecutada.
- `VERIFIED`: resultado contrastado con candidate y ambiente.
- `APPROVED_FOR_CLIENT`: revisado y aprobado para entrega.
- `SUPERSEDED`: reemplazado sin borrar historia.

## Paquetes

| Hito | Documento | Estado |
|---|---|---|
| Hito 1 | [Paquete Hito 1](./paquete_hito_001.md) | `DRAFT` |
| Hito 2 | Se crea con candidate real | `PLANNED` |
| Hito 3 | Se crea con candidate real | `PLANNED` |
| Hito 4 | Se crea con candidate real | `PLANNED` |
| Hito 5 | Se crea con candidate real | `PLANNED` |

## Anexos

- [Riesgos CA2/RLS trasladados a Hito 2](./anexo_h1_ca2_seguridad_rls.md).

## Reglas De Sanitizacion

No incluir credenciales, endpoints, project refs, UUIDs operativos, filas, PII,
payloads, SQL explotable, nombres de policies/routines sensibles, rutas privadas,
datos bancarios ni firmas.
