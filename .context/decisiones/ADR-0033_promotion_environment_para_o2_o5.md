# ADR-0033 - Environment Promotion para gates O2-O5

## Estado

`ACCEPTED_CANDIDATE`

## Contexto

PR #431 intento consumir `R3-GOV-HOM-003-O2-REQ1` para `O2 desarrollo -> certificacion`. El job `Promotion Boundary` fallo antes de asignar runner con la annotation:

```text
Branch "refs/pull/431/merge" is not allowed to deploy to Certification due to environment protection rules.
```

GitHub Actions evalua environments en eventos `pull_request` contra refs sinteticos `refs/pull/<n>/merge`. El Environment `Certification` solo admite la rama `certificacion` y por eso bloquea el job antes de ejecutar el validator.

## Decision

`Promotion Boundary` debe usar un Environment dedicado llamado `Promotion`.

Configuracion requerida para `Promotion` antes de cualquier nuevo O2-O5:

- Reviewer requerido: `romelhc95-approver`.
- `prevent_self_review=true`.
- Sin deployment branch policy.
- Variables/secret temporales por intento:
  - `R3_JIT_APPROVAL_GRANT_ID`
  - `R3_JIT_APPROVAL_REFERENCE`
  - `R3_JIT_APPROVAL_EXPIRY`

La restriccion de ramas queda en el workflow y en `validate_work_package.py`: mismo repositorio, pares exactos O2-O5, evento `opened`, run attempt `1`, attestation completa, ancestry, tree y digest.

## Consecuencias

- No se relaja `Certification`, `Production` ni `Development`.
- No se permite `refs/pull/*` globalmente en ambientes de despliegue.
- PR #431 y `R3-GOV-HOM-003-O2-REQ1` quedan consumidos por fallo y no pueden reintentarse.
- Un nuevo O2 requiere `R3-GOV-HOM-004-O2-REQ1`, nuevo PR y nuevo grant JIT single-use.
