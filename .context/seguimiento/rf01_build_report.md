# RF-01 Build Report - GIT and RELEASE GOVERNANCE

> STATUS: TARGET / NOT ACTIVE. Informe de evidencia del ciclo RF-01 BUILD.
> NO usar para promover H3 actual. Autoridad viva: `estado_del_proyecto.md`.

## Alcance Ejecutado

Documentacion de arquitectura/governance unicamente. No activa el modelo
nuevo, no modifica AGENTS.md, `estado_del_proyecto.md`, workflows, Docker,
gitattributes ni DB. Sin tags reales, sin release branches reales, sin cambios
de environments.

## Baseline Y Precondiciones

- Branch: `chore/rf-01-release-governance`.
- HEAD inicial: `7dbc7ab1100b62e58af804bd013db47e253a635b`.
- `git status --porcelain` vacio al inicio: PASS.

## Decisiones Arquitectonicas

1. Release candidato: rama corta `release/<release_id>` congelada desde un
   `source_sha` exacto; el PR de produccion es `release/<id> -> main`. Se
   RECHAZA `PR desarrollo -> main` como target porque `desarrollo` es movil y
   podria arrastrar contenido no certificado. El `source_sha` es la identity
   primaria; un tag `rc/<release_id>` es opcional y no sustituye la rama.
2. Back-sync: detector content-aware (patch-equivalence), no conteo de
   commits. Caso real verificado: tree de `certificacion` == tree de `main`
   con merge carriers adicionales -> HISTORY_ONLY, sin back-sync obligatorio.
3. Hotfix: dos escenarios. Transicional conserva los guards vigentes con la
   rama `certificacion`. Target usa Certification como environment/gate sin
   rama permanente, hotfix `hotfix/<id> -> main` y reconciliacion obligatoria
   hacia desarrollo.
4. Certificacion branch: POSSIBLE_BUT_NOT_YET. Blockers verificados:
   security-audit trigger, db-sync-to-pro guards, environment mapping,
   certification canary, tests/contracts, documentacion/politicas.
5. Cloudflare: `CLOUDFLARE_DEPLOY_MECHANISM = NO_VERIFICADO` (ver
   `rf01_release_promotion_contract_target.md`). BLOCKER BEFORE RF-07
   IMPLEMENTATION, no blocker documental.
6. Worktrees/ramas historicas: RF01-T08 CANCELADA como artefacto versionado
   (informacion machine-local). Solo se registra: worktree hygiene required
   before WSL migration; propuesta PRE-RF-02 WORKTREE HYGIENE sin acciones
   destructiveas.
7. RF01-T07 original CANCELADA en su parte activa: no se crean tags, release
   markers ni manifests operativos; la especificacion conceptual vive en el
   ADR y el contrato.

## Tareas Canceladas O Reasignadas

- RF01-T07 (marcadores activos): cancelada; concepto delegado al ADR-0028.
- RF01-T08 (inventario worktrees): cancelada como artefacto versionado.
- Detector de drift, automatizacion de releases, JSON Schema de release
  identity y migracion de guards: RF-07.
- Reorden del indice y navegacion: RF-04 (se prohibio editar
  `00_INDICE.md` en este ciclo).

## ADR ID

ADR-0027 esta reservado por referencias existentes (adenda sanitizada y
index de backlog). Se uso ADR-0028, verificado libre en todo el repositorio.

## Validaciones Ejecutadas

Ver informe al cierre del ciclo: `git diff --check`, `git diff --stat`,
escaneo de tokens TARGET obligatorios, verificacion de archivos no tocados y
suite pytest. Resultados registrados en el output del ciclo RF-01 BUILD.

## Findings Deferidos

- Cloudflare deploy mechanism NO_VERIFICADO (bloqueante para RF-07).
- Retiro de la rama certificacion -> RF-07 tras condiciones de ADR-0028.
- Implementacion del detector content-aware -> RF-07.
- Automatizacion de releases y environments -> RF-07.
- Worktree hygiene -> PRE-RF-02 (requerida antes de migracion WSL).