# Hotfix And Reconciliation Contract - TARGET / NOT ACTIVE

> STATUS: TARGET / NOT ACTIVE. NO usar para promover H3 actual. RF-07
> implementara los mecanicos. Autoridad viva: `estado_del_proyecto.md`.

## Hotfix Transicional (vigente mientras dure el modelo actual)

Mientras la rama `certificacion` y el pipeline actual sigan activos, el
hotfix mantiene el procedimiento compatible con las restricciones existentes:
cambio por `hotfix/*` o `fix/*` desde `desarrollo`, PR protegido a
`desarrollo`, luego `desarrollo -> certificacion -> main` con security-audit,
review humano y guards de DB. No se documenta bypass alguno que rompa los
guards vigentes.

## Hotfix Target (post RF-07)

```text
main
  |
  v
hotfix/<id>
  | tests locales + security tests
  | deploy del HOTFIX_SHA exacto
  v
Environment Certification
  | PASS / aprobacion
  v
PR hotfix/<id> -> main
  |
  v
Production
  |
  v
reconciliacion obligatoria content-aware hacia desarrollo
```

- En target NO es necesario mergear el hotfix a una rama permanente
  `certificacion`: Certification es un environment/gate.
- El emergency path puede reducir gates unicamente por autorizacion
  humana/JIT documentada; nunca elimina validacion, audit trail ni
  reconciliacion hacia desarrollo.

## Reglas De Back-Sync

Tras una promocion normal: si `main` no contiene contenido unico respecto de
`desarrollo`, NO se crea back-sync solo porque existan merge carriers.

Tras hotfix, correccion production-only, cambio de emergencia o cualquier
contenido unico en `main`: debe existir `PR main -> desarrollo` o mecanismo
equivalente no destructivo.

Prohibido siempre: force push, reset, rebase de rama protegida y cherry-pick
como estrategia normal.

## Deteccion Content-Aware (criterio, no comando)

Un conteo de commits (`git rev-list --count desarrollo..main > 0`) NO es
detector suficiente: confunde HISTORY-ONLY DIVERGENCE con CONTENT DIVERGENCE.
Caso real verificado en RF-01: tree de `certificacion` identico al tree de
`main` pero `main` con merge commits adicionales; eso no exige back-sync.

Clasificacion:

- `HISTORY_ONLY`: carriers de commits/merge distintos sin parches unicos
  relevantes -> NO back-sync obligatorio.
- `CONTENT_UNIQUE_IN_MAIN`: `main` contiene cambio funcional/documental real
  no presente ni patch-equivalente en `desarrollo` -> back-sync obligatorio.

RF-07 implementara y testeara el detector. Candidato conceptual: contenido /
patch-equivalence, por ejemplo `git log --cherry-pick --right-only --no-merges
desarrollo...main` mas validacion de diff/tree cuando corresponda. No se fija
un comando unico hasta validar que captura: merge normal de release, merge
commits history-only, hotfix en main, cambio productivo unico y desarrollo con
trabajo futuro adicional.

## Manejo De Conflictos

Si la reconciliacion `main -> desarrollo` entra en conflicto: PR normal con
resolucion explicita, tests y review. Sin push forzado y sin reescritura de
historia de ramas protegidas.