# ADR-0008 - Rebaseline De F10.7 Para Reconstruccion De Gate Main

| Campo | Valor |
|---|---|
| ID | `ADR-0008` |
| Estado | `ACCEPTED` |
| Estado posterior | Consumida por [ADR-0009](./ADR-0009_reconciliacion_entrega_tecnica_post_main_f10_7.md) |
| Decision humana | `USER_OWNER_APPROVED_F10_7_CYCLE1_2026-08-04` |
| Contexto relacionado | `REQ-EST-001`, `HITO-001`, `TASK-H1-001`, `F10.7`, `PLAN-H1-CA1-ONLY-001` |

## Contexto

Nota posterior: [ADR-0009](./ADR-0009_reconciliacion_entrega_tecnica_post_main_f10_7.md)
registra que F10.7 completo la entrega tecnica post-main por PR #291. Esta ADR
permanece como decision de rebaseline que habilito esa correccion, no como estado
vivo posterior.

F10.6 dejo el control-plane fail-closed y activo F10.7 para preparar el PR `certificacion -> main`. Durante la investigacion read-only de F10.7 se verifico que `certificacion@5cd27c6f6c35808865b7084673a83f9f690d3760` no contiene `.github/workflows/f9-7-contract.yml` ni el job `f10-main-boundary` requerido para bloquear la promocion a `main`.

La ausencia del gate significa que el freeze F9.10 de 32 objetos y su `USER_PERSONAL_UAT=PASS` siguen siendo evidencia historica de readiness, pero ya no son autoridad suficiente para ejecutar F10.7. Un PR directo `certificacion -> main` podria omitir el gate F10 requerido por el plan.

Ademas, se identificaron dos efectos previos que deben resolverse antes de cualquier PR a `main`:

- `.github/workflows/opencode.yml` usa una accion no pinneada y entrega un secreto de repositorio por comentario.
- La integracion de Cloudflare Pages puede desplegar automaticamente al recibir un push en `main`.

## Decision

F10.7 se divide en dos ciclos autorizables dentro de la misma subfase decimal:

1. Cycle 1 es documental y queda autorizado por la frase decimal recibida. Su unica salida es rebaselinear el Context Graph y registrar que la promocion anterior queda bloqueada hasta reconstruir controles.
2. Cycle 2 requiere repetir exactamente `Ejecuta las tareas pendientes de la Fase F10.7` despues de fusionar Cycle 1. Solo entonces se podran modificar workflows/tests, abrir PRs selectivos y preparar el PR `certificacion -> main`.

La correccion F10.7 no debe promover `.github/workflows/f9-7-contract.yml`. Ese workflow pertenece a historia de desarrollo/F9.x y no es parte del candidate de `certificacion` para `main`.

## Requisitos De Cycle 2

Cycle 2 debe cumplir todos estos requisitos antes de abrir PR a `main`:

1. Revalidar refs remotas, branch protection, required checks, environments, runs activos y ausencia de drift.
2. Trabajar desde worktrees limpios y montados en el contenedor `studiamatch-dev`; no reutilizar checkouts sucios.
3. Cambiar en `desarrollo` solo `.github/workflows/security-audit.yml`, `.github/workflows/opencode.yml` y `tests/test_fase10_main_boundary.py`.
4. Endurecer `opencode.yml`: acciones pinneadas por SHA confiable o workflow secret-bearing deshabilitado; actor/association allowlist; sin OIDC innecesario; permisos minimos.
5. Reconstruir selectivamente en `certificacion` exactamente esos tres paths, preservando el modo `100755` de `security-audit.yml`.
6. Agregar un gate `f10-main-boundary` bloqueante, target-aware y agregado por `security-audit`, con validacion por path/status/mode/blob.
7. Configurar variables no secretas de freeze aprobadas para SHA/tree/count/digest y exigir que el PR `certificacion -> main` coincida con ellas.
8. Cancelar con cero pasos el run automatico `F9.9 - Certification Canary` que dispare el merge a `certificacion`; no aprobar environments ni entregar secretos.
9. Recalcular el boundary `main -> certificacion`; bajo el alcance de tres paths se espera un boundary de 33 objetos por la inclusion nueva de `.github/workflows/opencode.yml`.
10. Obtener `USER_PERSONAL_UAT=PASS` nuevo, ligado al SHA/tree final de `certificacion` y al nuevo digest.
11. Prevenir deployment automatico de Cloudflare Pages para `main` antes del PR a `main`; si no puede verificarse, F10.7 queda bloqueada.
12. Al fusionar `main`, cancelar `DB Sync to Production` antes de aprobacion o ejecucion y demostrar `steps=[]`, cero pending deployments y cero acceso Supabase/Production.

## Estado Del Freeze F9.10

El freeze de 32 objetos `34f3789d597bf4012378d6e509a03ee6e9ef37edaee95713023421538cab1aa5` y el UAT ligado a `certificacion@5cd27c6f6c35808865b7084673a83f9f690d3760` quedan `SUPERSEDED_FOR_F10_7_PROMOTION`. Permanecen como evidencia historica F9.10 y no se borran ni reinterpretan como fallo.

## Acciones Prohibidas En Cycle 1

Cycle 1 no autoriza cambios fuera de `.context/**`, PR a `certificacion`, PR a `main`, aprobacion de environments, dispatch de workflows, Supabase Free/Pro, DDL/DML, backup/restore, writers, schedules, canary Production ni Cloudflare.

## Stop Conditions

- Intentar usar el freeze de 32 objetos como autoridad de promocion F10.7.
- Agregar `.github/workflows/f9-7-contract.yml` al candidate de `certificacion -> main`.
- No poder pinnear o deshabilitar de forma segura el workflow OpenCode con secreto.
- No poder prevenir o verificar la prevencion de deployment automatico de Cloudflare Pages en `main`.
- Cualquier drift de refs, paths, modes, count, digest, UAT, branch protection o environment policy.
- Cualquier ejecucion con pasos en Production, schedules, DB Sync, Certification Canary post-merge no autorizado o Cloudflare deployment.

## Enlaces

- [Estado del proyecto](../estado_del_proyecto.md)
- [TASK-H1-001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md)
- [PLAN-H1-CA1-ONLY-001](../operaciones/plan_cierre_hito1_ca1_only.md)
- [Flujo de release minimo](../operaciones/flujo_release_minimo.md)
- [Paquete de evidencia Hito 1](../evidencias_cliente/sprint_1/paquete_hito_001.md)
