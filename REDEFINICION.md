# Redefinicion Del Flujo

## Estado

`VALIDACION_LOCAL`

## Baseline

- Fuente: `origin/main@9b486146962bd2a092acfd649fdcf716e922de89`.
- Rama local de trabajo: `recovery/simple-flow-source-local`.
- No se preserva el WIP previo al baseline.
- No se autorizan acciones remotas, cambios de base de datos, nuevos pedidos ni cambios de producto.

## Alcance Permitido

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
- El baseline local deja de ser `9b486146962bd2a092acfd649fdcf716e922de89`.
- Una ruta protegida cambia contra el baseline.
- Una validacion tecnica requerida falla sin remediacion local posible.
- Se requiere accion remota, mutacion Supabase o decision humana adicional.
