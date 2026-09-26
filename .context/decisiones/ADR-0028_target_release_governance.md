# ADR-0028 - Target Release Governance (RF-01)

> STATUS: TARGET / NOT ACTIVE. Este ADR define el contrato futuro de releases.
> NO usar para promover H3 actual. El flujo vigente
> `feature -> desarrollo -> certificacion -> main` permanece operativo mientras
> H3 este en transito. La activacion requiere RF-07 y aprobacion humana.

## Estado

`ACCEPTED_AS_TARGET_NOT_ACTIVE`

## Activacion Conditions

- H3 completo el flujo vigente o existe decision expresa equivalente.
- RF-07 implemento los cambios tecnicos (detector, environments, automation).
- Validaciones CI/CD correspondientes en PASS.
- Autorizacion humana explicita de activacion.

Mientras ninguna condicion se cumpla, ningun agente debe tratar este documento
como policy operativa activa.

## Modelo Actual (vigente)

`feat/*` o `docs/*` -> PR protegido a `desarrollo` -> PR protegido a
`certificacion` -> PR protegido a `main`. `security-audit` required check,
review humano, `DB Sync to Production` manual-only.

## Modelo Transicional

Sin cambios: el modelo actual se mantiene completo durante construccion e
H3. RF-01 no agrega ni retira gates.

## Modelo Target

```text
feature/*
   |
   v
desarrollo
   |  elegir SOURCE_SHA exacto
   v
release/<release_id>   (rama corta congelada desde SOURCE_SHA)
   |  deploy de SOURCE_SHA a Environment Certification
   |  PASS
   v
PR release/<release_id> -> main
   |
   v
Production
```

Puntos clave:

- El candidato certificado se identifica principalmente por `source_sha`;
  opcionalmente un annotated tag `rc/<release_id>` apunta al mismo SHA.
- El tag NO sustituye la rama: el PR head necesita `release/<id>`.
- NO se aprueba un PR `desarrollo -> main` como mecanismo de release final,
  porque `desarrollo` es movil y puede arrastrar contenido no certificado.

## Retiro De La Rama Certificacion

`POSSIBLE_BUT_NOT_YET`. Blockers verificados: trigger de `security-audit`,
guards de `db-sync-to-pro.yml`, mapeo de environments, certification canary,
tests/contracts, documentacion y politicas dependientes de la rama. El retiro
exige: H3 cerrado o equivalente, RF-07 implementado, Certification environment
validado, guards migrados, E2E/canary PASS y aprobacion humana.

## Invariantes

- `security-audit` sigue siendo required check en target.
- Toda promocion requiere review humano.
- Nunca force push, reset ni rebase de ramas protegidas.
- La DB nunca se promueve por cambio de nombre de rama: ver
  `operaciones/rf01_release_promotion_contract_target.md` (migration_set).
- Toda transicion mantiene expand -> compatibilidad -> deploy -> contract.

## Consecuencias

- CLOUDFLARE_DEPLOY_MECHANISM = NO_VERIFICADO: no se afirma que GitHub Actions
  despliegue Pages ni que Git Integration lo haga. Es BLOCKER BEFORE RF-07
  IMPLEMENTATION, no blocker para la documentacion RF-01.
- El detector de drift y la automatizacion de releases pertenecen a RF-07.

## Referencias

- [Release and promotion contract TARGET](../operaciones/rf01_release_promotion_contract_target.md)
- [Hotfix and reconciliation contract TARGET](../operaciones/rf01_hotfix_reconciliation_contract_target.md)
- [Flujo release minimo vigente](../operaciones/flujo_release_minimo.md)