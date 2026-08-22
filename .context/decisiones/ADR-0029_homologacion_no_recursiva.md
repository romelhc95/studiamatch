# ADR-0029 - Homologacion No Recursiva Post-PR425

## Estado

`PROPOSED`

## Contexto

PR #425 publico arquitectura canonica y Governance Preflight en `desarrollo`, pero `certificacion` y `main` permanecen en el tree anterior. Promover el tree `ac16b545b74a03b149aac538062def20101187fb` antes de reconciliar la autoridad documental crearia una segunda divergencia y obligaria a repetir la homologacion.

## Decision

Crear primero un candidate local `WP-GOV-HOM-001` que produzca `T_HOM`. Solo despues de una aprobacion R2 por digest se publicara ese tree a `desarrollo`. La convergencia posterior usa cuatro grants R3 JIT separados:

1. `O2`: `desarrollo -> certificacion`.
2. `O3`: `certificacion -> main`.
3. `O4`: `main -> certificacion`.
4. `O5`: `certificacion -> desarrollo`.

Cada grant es single-use, expira, requiere actor y aprobador humano distinto, y se consume por exito, fallo, timeout o cancelacion. No se permite agrupar grants ni declarar cierre por prosa antes del predicado externo.

## Predicado De Cierre

F10.11 queda cerrada solo si:

```text
tree(main) == tree(certificacion) == tree(desarrollo) == T_HOM
main es ancestro de certificacion
certificacion es ancestro de desarrollo
DB Sync = SUCCESS_NO_DB_CHANGES_SKIPPED
O2/O3/O4/O5 consumidos individualmente
checkout ordinario actualizado
```

## Cloudflare Pages

El preview automatico de `desarrollo` asociado a PR #425 se clasifica como `AUTOMATIC_NON_PRODUCTION_PREVIEW_SIDE_EFFECT`. No autoriza produccion ni sustituye canary. O3 debe decidir explicitamente si autoriza rebuild automatico de Cloudflare Pages Production y DB Sync fail-closed sin cambios.

## Consecuencias

- `WP-GOV-ARCH-001` queda como artifact firmado consumido; no se muta.
- `WP-H2-001` queda activo hasta R1 pero bloqueado por homologacion y rebaseline.
- H2-CA2/H2-CA3 permanecen `NOT_STARTED` y `0` puntos.
- Cualquier retry R3 requiere nuevo grant.
