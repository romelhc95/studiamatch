# ADR-0031 - Boundary De Homologacion Estructural

## Estado

`PROPOSED`

## Contexto

El boundary incremental de WP compara cambios contra el baseline de un PR de trabajo. En promociones protegidas O2-O5 el diff entre ramas puede incluir cambios ya homologados o acumulados, por lo que no debe interpretarse como scope incremental de un WP activo.

PR #428 fallo en `Canonical Path Boundary` durante O2 por esta mezcla de semanticas. El fallo consume el grant JIT O2 y obliga a preparar una correccion separada antes de solicitar un nuevo O2.

## Decision

Se separan dos modos canonicos:

- Boundary incremental: PR normales y candidates R0-R2; valida paths cambiados contra allowlist/denylist del WP vigente.
- Boundary estructural de promocion: PR O2-O5 entre ramas protegidas; valida el evento de promocion y su atestacion, no el scope incremental acumulado entre ramas.

## Reglas

- O2: `desarrollo -> certificacion`.
- O3: `certificacion -> main`.
- O4: `main -> certificacion`.
- O5: `certificacion -> desarrollo`.
- Cada promocion requiere `Promotion Attestation` con `Operation`, `Grant-ID`, `Base-SHA`, `Candidate-SHA`, `Final-WP`, `D_FINAL`, `T_FINAL`, `Approval-Level`, `Approval-Reference` y `Approval-Expiry`.
- La rama origen debe pertenecer al mismo repositorio que la rama destino protegida; nombres de rama equivalentes desde forks no activan boundary estructural.
- PR #428 queda bloqueado permanentemente para promocion; su fallo consumio el grant O2 previo y no puede reabrirse, editarse, sincronizarse ni reintentarse como ruta de homologacion.
- El boundary estructural solo acepta el primer evento `opened` con `GITHUB_RUN_ATTEMPT=1`; eventos `reopened`, `edited`, `synchronize`, `ready_for_review` y reruns fallan cerrados.
- `Approval-Level` debe ser `R3 JIT single-use`.
- `Operation` identifica la promocion (`O2`, `O3`, `O4` u `O5`) y `Grant-ID` debe ser un id nuevo, unico, con sufijo de intento y codigo de operacion; `R3-GOV-HOM-001-O2` queda consumido y rechazado.
- `Approval-Reference` debe apuntar a la aprobacion humana JIT single-use usada para esa promocion.
- `D_FINAL` debe coincidir con el digest canonico del `Final-WP`.
- `T_FINAL` debe coincidir con el tree del candidate SHA.
- El candidate debe descender del base SHA.
- Sin ledger persistente ni writer remoto, CI valida fail-closed la precondicion stateless del grant; el registro externo de consumo por exito, fallo, timeout o cancelacion sigue siendo parte del gate posterior.

## Consecuencias

- El boundary incremental no se relaja para trabajo ordinario.
- Las promociones protegidas dejan de fallar por paths historicos ya existentes en la rama origen.
- Un fallo de CI en promocion sigue consumiendo el grant JIT correspondiente y requiere aprobacion nueva para retry.
