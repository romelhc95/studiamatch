# Release And Promotion Contract - TARGET / NOT ACTIVE

> STATUS: TARGET / NOT ACTIVE. Define el contrato logico futuro de releases.
> NO usar para promover H3 actual. RF-07 implementara mecanica y automatizacion.
> La autoridad viva esta en `estado_del_proyecto.md`; este documento no crea
> alcance ni autoriza ejecucion.

## Release Identity (minima)

| Campo | Definicion |
|---|---|
| `release_id` | Identificador unico del release (formato abajo) |
| `source_sha` | Commit exacto de `desarrollo` que origina el candidato |
| `tree_sha` | Tree hash asociado al `source_sha`; identifica el contenido certificado |
| `migration_set` | Conjunto de migraciones DB derivadas del release |
| `validation_evidence_ref` | Referencia a la evidencia de validacion |
| `certification_result` | PASS / FAIL de la certificacion |

### Formato de `release_id` (F3)

Formato recomendado:

```
release_id = YYYYMMDD-rN-<shortsha>
```

Ejemplo: `20260910-r1-7dbc7ab`. Derivados del mismo id:

- Branch: `release/20260910-r1-7dbc7ab`
- Optional tag: `rc/20260910-r1-7dbc7ab`

Reglas:

- El `release_id` NO contiene los prefijos `release/` ni `rc/`; los prefijos
  pertenecen al nombre del ref, no a la identidad.
- El id es unico, legible, auditable y simple. No hay schema machine-readable
  en esta fase (la completa definira RF-07 si existe consumidor).

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

### Inmutabilidad del candidato certificado (F1)

Identidad del candidato antes del PASS: mientras
`certification_result != PASS`, el candidato todavia puede ser sustituido por
una nueva revision conforme al proceso definido.

Cuando `certification_result = PASS`, ese candidato certificado queda
INMUTABLE. Despues del PASS esta prohibido:

- Commits adicionales sobre el candidato.
- Force update de la rama `release/<id>`.
- Mover silenciosamente la rama.
- Sustituir `source_sha` o `tree_sha` del candidato.

Si aparece cualquier fix o cambio posterior al PASS:

1. El candidato anterior queda invalidado para toda promocion futura
   (pero permanece historicamente identificable).
2. Se genera una NUEVA revision del release con nuevo `release_id`
   (incrementando `rN`), nuevo `source_sha`, nuevo `tree_sha` y un
   `certification_result` FAIL/PENDIENTE hasta repasar Certification completa.

Ejemplo conceptual:

```
RC r1: source_sha = X, Certification = PASS
Aparece fix Y
-> r1 queda invalidado para promocion (historicamente identificado)
-> r2 = nuevo candidato: source_sha = Y
-> Certification vuelve a ejecutarse para r2
```

Este apartado es contrato TARGET / NOT ACTIVE: no implementa branch
protection ni automatizacion en esta fase; RF-07 hara cumplir los mecanicos.

## Production

Merge del PR `release/<release_id> -> main` en main tras PASS en Certification
y aprobacion humana.

### Equivalentencia de contenido certificado (F2)

El merge del PR puede producir un merge commit, por lo que el SHA de main
tras el merge (`promoted_main_sha`) usualmente difiere del `source_sha`
certificado. Eso es valido mientras el CONTENIDO certificado no cambie.

Identidad de la promocion:

- `certified_source_sha` = `source_sha` del candidato certificado (X).
- `certified_tree_sha` = `tree_sha` del candidato certificado (TX).
- `promoted_main_sha` = SHA del merge commit (o fast-forward) resultante (Y).
- `promoted_main_tree_sha` = tree hash de main tras el merge (TY).

Condicion minima de promocion VALIDA:

- Documentacion PREFERRED: `TY == TX` (el estado final de main es el arbol
  certificado).

- Si una estrategia futura hace que la igualdad literal del arbol no sea
  aplicable (por historia preexistente o mecanica de merge), RF-07 debera
  demostrar mediante tests un mecanismo equivalente basado en
  patch-equivalence / content-equivalence antes de activar el pipeline.

Interpretacion:

- `Y != X` y `TY == TX` => valid promotion carrier; la historia cambia, el
  contenido certificado se preserva.
- `Y != X` y `TY != TX` => STOP: content drift detectado; la promocion no
  puede considerarse equivalente y requiere investigacion / re-certification.

No se aceptan como prueba de contenido solo el conteo de commits ni solo la
igualdad de SHAs.

### Trazabilidad de promocion (audit trail)

La identidad de cada promocion deberia permitir registrar conceptualmente:

- `release_id`
- `certified_source_sha`
- `certified_tree_sha`
- `promoted_main_sha`
- `promoted_main_tree_sha`
- `certification_result`
- `validation_evidence_ref`

Estos campos de promocion quedan definidos como informacion de trazabilidad
para RF-07; no constituyen schema obligatorio de RF-01 ni JSON ejecutable.

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

### Despliegue a Production respecto del contenido certificado

Production debe corresponder al contenido certificado del release, cuya
identidad parte de `certified_source_sha` y `certified_tree_sha`. Lo que se
registra en main tras el merge es un promotion carrier: `promoted_main_sha`,
que puede diferir del `source_sha` (ver Equivalentencia de contenido
certificado); no se presupone que el SHA de main en Production iguale el
`source_sha` certificado.

- Si el mecanismo de deployment real permite desplegar directamente un
  source SHA, podra hacerlo RF-07.
- Si despliega desde main, debera verificar equivalentencia de contenido
  (TY == TX o mecanismo patch/content-equivalent que RF-07 demuestre con
  tests).

`CLOUDFLARE_DEPLOY_MECHANISM` sigue `NO_VERIFICADO`: no se afirma ni se
inventa mecanismo de deploy.

## Cierre

Ningun release puede cerrarse con hallazgos HIGH/CRITICAL abiertos o sin
evidencia canonica. Este contrato permanece NOT ACTIVE hasta que RF-07
implemente los mecanicos y exista autorizacion humana; mientras tanto el flujo
vigente `desarrollo -> certificacion -> main` es el unico autorizado.