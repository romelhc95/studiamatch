# Release And Promotion Contract - TARGET / NOT ACTIVE

> STATUS: TARGET / NOT ACTIVE. Define el contrato logico futuro de releases.
> NO usar para promover H3 actual. RF-07 implementara mecanica y automatizacion.
> La autoridad viva esta en `estado_del_proyecto.md`; este documento no crea
> alcance ni autoriza ejecucion.

## Release Identity (minima)

| Campo | Definicion |
|---|---|
| `release_id` | Identificador unico del release |
| `source_sha` | Commit exacto de `desarrollo` que origina el candidato |
| `tree_sha` | Tree hash asociado al `source_sha` |
| `migration_set` | Conjunto de migraciones DB derivadas del release |
| `validation_evidence_ref` | Referencia a la evidencia de validacion |
| `certification_result` | PASS / FAIL de la certificacion |

Campos `artifact_digest`, `build_digest`, `deployed_version` son opcionales y
solo se registran si la plataforma los provee con valor. No existe todavia un
JSON Schema ejecutable; si un workflow real de RF-07 consume estos datos,
RF-07 definira el schema formal machine-readable (no crear infraestructura sin
consumidor).

## Release Branch Lifecycle

1. Se elige un `SOURCE_SHA` exacto de `desarrollo`.
2. Se crea la rama corta congelada `release/<release_id>` desde ese SHA.
3. Se despliega el `source_sha` en Environment Certification.
4. Con PASS, se abre `PR release/<release_id> -> main`.
5. Tras review humana y checks verdes, merge a `main` y despliegue a Production.

La rama `release/<id>` es el HEAD utilizable del PR. Ninguna promocion usa PR
`desarrollo -> main`. Un annotated tag `rc/<release_id>` al mismo SHA es
opcional y nunca sustituye la rama.

## Certification

Certification es el gate obligatorio previo a Production: deploy desde
`source_sha` o de la rama `release/<id>` a Environment Certification, con
validaciones (security-audit, tests, canary de certificacion) y evidencia
trazable. En target, certificacion es un environment/gate; no requiere rama
permanente (ver ADR-0028 para el retiro de la rama `certificacion`).

## Production

Merge del PR `release/<release_id> -> main` en main tras PASS en Certification
y aprobacion humana. El despliegue a Production opera sobre el mismo
`source_sha` certificado.

## Migration Set Y Governance DB

- Cada release declara un `migration_set` derivado del contenido del
  `source_sha` (nada entra en el set que no este en el contenido).
- Fases conceptuales: validacion local -> validacion en Certification -> JIT
  explicito -> apply en Production -> verificacion.
- Rollback default: forward-fix. Rollback destructivo o reverse DDL solo con
  autorizacion especifica.
- La migration identity queda vinculada a la release identity; la DB no se
  promueve porque una rama cambio de nombre.
- Sin ejecucion: este contrato no aplica ninguna migracion.

## Contrato Build Reproducible

- `CLOUDFLARE_DEPLOY_MECHANISM = NO_VERIFICADO`. No se afirma como despliega
  Cloudflare Pages (GitHub Actions vs Git Integration); se registra como
  BLOCKER BEFORE RF-07 IMPLEMENTATION, no como blocker de la documentacion.
- Build-once/promote-many NO se impone si variables tipo `NEXT_PUBLIC_*`
  exigen build por ambiente.
- Contrato deseado: mismo `source_sha`, mismo lockfile, misma toolchain/build
  image cuando aplique, configuracion de ambiente explicita, resultado
  trazable.
- Si existe artifact reproducible/promovible se usa artifact identity; si no,
  reproducible rebuild desde el mismo `SOURCE_SHA`.

## Cierre

Ningun release puede cerrarse con hallazgos HIGH/CRITICAL abiertos o sin
evidencia canonica. Este contrato permanece NOT ACTIVE hasta que RF-07
implemente los mecanicos y exista autorizacion humana; mientras tanto el flujo
vigente `desarrollo -> certificacion -> main` es el unico autorizado.