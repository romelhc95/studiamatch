# ADR-0027 - Work Packages Y Convergencia

## Estado

`ACCEPTED`

## Decision

El modelo operativo futuro usa work packages persistentes y aprobacion por digest.

| Nivel | Capacidad | Autorizacion |
|---|---|---|
| `R0` | Lectura local y plan | Ninguna |
| `R1` | Edicion local y tests | Work package aprobado |
| `R2` | Push, PR y merge a desarrollo | Work package, CI y review |
| `R3` | Certification/Main, DB, deploys, schedules, writers, secrets o destruccion | Aprobacion JIT |

Estados validos de manifest:

```text
PROPOSED
APPROVED
ACTIVE
COMPLETED
REVOKED
EXPIRED
```

Formato de aprobacion futura:

```text
Apruebo WP-H2-001 segun manifest sha256:<digest>.
```

## Convergencia

La homologacion posterior a Etapa 1 debe preservar historia y converger trees:

```text
candidate -> desarrollo
desarrollo -> certificacion
certificacion -> main
main -> certificacion
certificacion -> desarrollo
```

Invariante final:

```text
tree(main) == tree(certificacion) == tree(desarrollo) == T_CANONICO
main es ancestro de certificacion
certificacion es ancestro de desarrollo
```

Cada PR de homologacion debe validar ejecutablemente:

- Diff efectivo contra `TECH_BASE` limitado a la allowlist canonica.
- `web/**`, `db/**`, `supabase/**`, `scripts/core/**` y `scripts/maintenance/**` sin cambios frente a `TECH_BASE`.
- Ramas protegidas sin force push ni deletion.
- DB Sync en main con resultado esperado `SUCCESS_NO_DB_CHANGES_SKIPPED`.
- Tree final identico a `T_CANONICO` antes de avanzar al siguiente PR.

`PATCH_CANONICO` incluye explicitamente `.github/workflows/security-audit.yml`,
`.github/workflows/f9_9_certification_canary.yml`,
`scripts/security/validate_work_package.py` y `tests/test_work_package_manifest.py`.

## Invalidacion De Aprobacion

Scope drift, baseline drift, paths nuevos, cambio de riesgo, cambio de ambiente,
expiracion, cambio del manifest u operacion R3 no prevista invalidan la aprobacion.
