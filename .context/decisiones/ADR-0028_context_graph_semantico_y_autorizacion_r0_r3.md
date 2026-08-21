# ADR-0028 - Context Graph Semantico Y Autorizacion R0-R3

## Estado

`ACCEPTED`

## Decision

El Context Graph deja de ser un conjunto append-only de notas y pasa a ser un grafo semantico validable. La autoridad viva permanece en [Estado Del Proyecto](../estado_del_proyecto.md), y los nodos canonicos deben ser coherentes entre Estado, Requerimiento, Plan Maestro, Hito, TASK, WP, Matriz, Evidencia, Tracker y Retrospectiva.

El modelo objetivo de autorizacion es R0-R3:

| Nivel | Operacion | Autorizacion |
|---|---|---|
| `R0` | Lectura y planificacion local | Ninguna |
| `R1` | Edicion local y tests Docker | Grant persistente WP/digest |
| `R2` | Push, PR y merge a `desarrollo` | WP/digest, CI y review |
| `R3` | Certification/Main, DB, deploys, schedules, writers, secrets | JIT single-use |
| `R3+` | Destruccion o recuperacion productiva | JIT y doble aprobacion |

Formato objetivo posterior a F10.11:

```text
Apruebo WP-<ID> de TASK-<ID> segun manifest sha256:<digest> contenido en candidate commit:<commit>, hasta <nivel> y hasta <expiry_utc>.
```

Durante la transicion F10.11 sigue vigente la frase decimal exacta exigida por `AGENTS.md`. Una vez versionado este ADR en las ramas homologadas, la fase decimal queda como trazabilidad dentro del manifest y no como microautorizacion repetitiva.

## Reglas

- Un solo Estado vivo.
- Una TASK activa por hito.
- Un ADR por decision real.
- No copiar historia completa en cada nodo.
- Los documentos superseded deben indicarlo claramente.
- Ningun documento historico puede reactivar trabajo.
- Todo nodo canonico eliminado requiere reemplazo o tombstone.
- La informacion mecanizable debe vivir en JSON o CI, no solo en prosa.
- R3 expira entre 15 y 60 minutos y se consume por exito, fallo, timeout o cancelacion.
- Retry R3 requiere nueva aprobacion.
- Autor y aprobador R3 deben ser distintos.
- La primera aprobacion de `WP-H2-001` solo puede ser hasta R1.
- La aprobacion por digest no autoriza por si sola DDL/DML, Supabase, backfill, RLS/grants, writers, schedules, workflow_dispatch, Certification, Main ni produccion.
- `APPROVED` y `ACTIVE` requieren `approval_digest`, `approved_by`, `approved_at`, `approval_reference` y vigencia verificable.
- El manifest candidato puede firmar `approval_target_lifecycle_stage`, `approval_target_gate_status` y `approval_target_level`; esos campos describen el resultado permitido por la aprobacion futura y no cambian el estado actual.
- `status`, lifecycle actual, progreso, metadata de aprobacion y activacion son mutables controlados por transiciones, no por el digest candidate.
- `PROPOSED` con lifecycle actual aprobado o activo es una pseudo-aprobacion y debe fallar.
- `APPROVED` no desbloquea paths funcionales; `ACTIVE` requiere activacion explicita, aprobacion R1 vigente y un unico WP activo.

## Enforcement

`security-audit` debe bloquear credenciales, fuentes privadas, manifests con digest invalido, links rotos, incoherencia semantica del Context Graph, eliminaciones canonicas no justificadas y paths fuera del alcance aprobado.

Los cambios ordinarios de un WP funcional no pueden modificar los validadores,
workflows o documentos de autoridad que deciden si ese WP es valido. Esos cambios
requieren un paquete de gobierno separado.
