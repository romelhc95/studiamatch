# ADR-0009 - Reconciliacion De Entrega Tecnica Post-Main F10.7

| Campo | Valor |
|---|---|
| ID | `ADR-0009` |
| Estado | `ACCEPTED` |
| Fecha | `2026-08-04` |
| Alcance | `REQ-EST-001`, `HITO-001`, `TASK-H1-001`, `F10.7` |

## Contexto

F10.7 promovio el paquete CA1-only desde `certificacion` hacia `main` mediante
PR #291. La promocion fue aprobada por `APPROVING_REVIEWER_RECORDED_PRIVATELY`, fusionada por PR protegido y
validada por el gate F10 post-merge.

Identidad verificada:

- Base `main` antes de la promocion: `d8f1ea0b210f2a1cf95e73751621cf8b4fcf0f93`.
- Head `certificacion`: `1edc65aa848d32dabfa62aa60b53f4bff9b5716e`.
- Merge `main`: `64e4ed895d43121c5683e26a355993f18e528a5c`.
- Tree publicado: `7d43590c19ca15171d468bf8c823a5e93b47d8cc`.
- Boundary CA1-only: 32 objetos.
- Digest documental post-merge: `8fafc74e415d6875315e8584eb17705e24c40777675996cde9bf4ff0ccf7ddff`.

El digest se calcula como `sha256` de lineas UTF-8 ordenadas por path con formato
`status<TAB>mode<TAB>blob<TAB>path<LF>` para el diff
`d8f1ea0b210f2a1cf95e73751621cf8b4fcf0f93 -> 64e4ed895d43121c5683e26a355993f18e528a5c`.

## Decision

Se acepta documentar F10.7 como **entrega tecnica post-main** del paquete CA1-only,
no como cierre contractual completo del Hito 1.

Se registra que Cloudflare Pages desplego correctamente el commit de `main` y ese
deployment se acepta como publicacion tecnica esperada del arbol ya promovido. Ese
resultado no sustituye el canary Production del pipeline ni la observacion de
schedules.

Se registra que `DB Sync to Production` run `30969158711` fue cancelado con todos
sus jobs en `steps=[]`; por tanto no ejecuto migraciones, verificaciones de
esquema ni operaciones DDL/DML mediante ese workflow.

## Consecuencias

- `EVID-H1-009` queda `VERIFIED` por PR #291 aprobado/fusionado.
- `EVID-H1-014` queda `VERIFIED_POST_MERGE_BOUNDARY` por boundary CA1-only de 32
  objetos, digest post-merge y cero rutas CA2 prohibidas.
- `EVID-H1-010`, `EVID-H1-011`, `EVID-H1-012`, `EVID-H1-013` y `EVID-H1-016`
  permanecen pendientes.
- `TASK-H1-001`, `HITO-001` y `H1-CA1` no se declaran completados
  contractualmente.
- F10.8, F10.9 y F11.1 permanecen bloqueadas hasta autorizacion separada.

## Exclusiones

Esta decision no autoriza canary Production, schedules, Supabase Free/Pro,
DDL/DML, writers, workflow dispatch, backup/restore ni cambios fuera de
`.context/**`.
