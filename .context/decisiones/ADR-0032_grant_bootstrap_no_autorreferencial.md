# ADR-0032 - Bootstrap no autorreferencial de grants R3

## Estado

`ACCEPTED_CANDIDATE`

## Contexto

GOV-CI2 separo boundary incremental y estructural, bloqueo PR #428 y rechazo reruns. Sin embargo, su esquema de grant versionado exigia que el archivo del grant contuviera el `candidate_sha` y `t_final` exactos del mismo commit donde vivia el archivo.

Ese modelo no puede congelarse con Git: al escribir el SHA/tree dentro del archivo cambia el blob, cambia el tree y cambia el commit.

## Decision

Los archivos bajo `.context/r3_grants/` son solicitudes estaticas `REQUESTED_JIT_SINGLE_USE`, no grants aprobados. Definen operacion, repositorio, par de ramas, `Final-WP`, evento permitido, run attempt permitido y bindings simbolicos:

- `base_sha_binding = pull_request.base.sha`
- `candidate_sha_binding = pull_request.head.sha`
- `t_final_binding = tree(pull_request.head.sha)`
- `d_final_binding = manifest.candidate_digest`

La aprobacion humana JIT y sus valores exactos viven en la `Promotion Attestation` del PR de promocion y deben coincidir con variables protegidas del workflow:

- `R3_JIT_APPROVAL_GRANT_ID`
- `R3_JIT_APPROVAL_REFERENCE`
- `R3_JIT_APPROVAL_EXPIRY`

CI valida esos valores contra el evento real, contra el manifest canonico y contra las variables protegidas. Si esas variables no existen o no coinciden, la promocion falla cerrada.

## Consecuencias

- El tree final puede contener solicitudes O2-O5 sin autorreferencia.
- PR #428 y `R3-GOV-HOM-001-O2` permanecen bloqueados permanentemente.
- CI sigue siendo stateless: valida precondiciones, pero no registra consumo global.
- Cada fallo, cancelacion o timeout consume externamente el intento; un retry exige nuevo Grant-ID, nuevo PR y nuevo gate.
- No se introduce ledger ni writer remoto; la autenticidad JIT depende de variables protegidas configuradas externamente para el intento single-use.
