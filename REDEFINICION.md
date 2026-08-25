# Redefinicion Del Flujo

## Estado

`TEMPORARY_SUPPORT_PENDING_CLIENT_GO`

Este documento fue creado como soporte temporal para la transicion al flujo
simplificado. La autoridad viva permanece en `.context/estado_del_proyecto.md`
y las reglas operativas en `AGENTS.md`. Este archivo no crea autoridad
independiente y se conserva hasta recibir el GO para nuevos pedidos del cliente.

## Baseline

- Fuente: `origin/main@9b486146962bd2a092acfd649fdcf716e922de89`.
- Rama local de trabajo: `recovery/simple-flow-source-local`.
- No se preserva el WIP previo al baseline.
- La promocion `desarrollo -> certificacion -> main` fue completada mediante PRs protegidos #451, #452 y #453.
- No se autorizan cambios de base de datos, nuevos pedidos ni cambios de producto.

## Alcance Que Tuvo La Transicion

- `AGENTS.md`
- `REDEFINICION.md`
- `.context/**`
- `.github/**`
- `.githooks/**`
- `scripts/security/**`
- Tests de seguridad y gobernanza

## Alcance Protegido

Estos paths deben permanecer identicos al baseline salvo autorizacion futura separada:

- `web/**`
- `db/**`
- `supabase/**`
- `scripts/core/**`
- `scripts/shared/**`
- `scripts/maintenance/**`
- `config/**`
- Dependencias y lockfiles
- Docker y compose

## Flujo Redefinido

```text
feat/* o docs/* desde desarrollo
-> PR protegido a desarrollo
-> PR protegido desarrollo a certificacion
-> PR protegido certificacion a main
```

## Reglas Operativas

- `security-audit` permanece como required check unico de seguridad tecnica.
- Cada PR requiere review humano.
- `DB Sync to Production` queda manual-only mediante `workflow_dispatch`.
- FG1, FG2 y FG3 conservan sus workflows operativos y sus controles de entorno.
- Cambios DB, produccion, schedules, writers, deploys, secrets y acciones destructivas requieren aprobacion separada.
- Work Packages, grants persistentes, digests documentales, Context Graph y promotion gates historicos dejan de autorizar ejecucion.

## Validacion Local Esperada

- Escaneo de credenciales de tree y diff.
- Compilacion Python de scripts versionados.
- Pytest de contrato de credenciales y flujo de seguridad.
- ESLint, TypeScript y build estatico dentro del contenedor.
- actionlint y shellcheck si estan disponibles en el entorno.
- Integridad de rutas protegidas contra `origin/main@9b486146962bd2a092acfd649fdcf716e922de89`.

## Stop Conditions

- Aparece un secreto o valor credential-like.
- El estado vivo en `.context/estado_del_proyecto.md` contradice el flujo simplificado.
- Una ruta protegida cambia contra el baseline.
- Una validacion tecnica requerida falla sin remediacion local posible.
- Se requiere mutacion Supabase, DB Sync, canary, writer, schedule o decision humana adicional.
