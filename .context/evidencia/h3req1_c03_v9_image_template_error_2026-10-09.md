# Resultado del diagnóstico V9 — error de template en image inspect

Fecha: 2026-10-09. Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Invocación y resultado

El usuario aprobó una invocación de
`H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-IMAGE-READ-CLASSIFIER-V9-BASH-DISPATCH-ONCE-20261009-V1`,
JIT SHA-256 `a1b28cb9b3a2bc40bc9d4150dc2ffd8d90371e78672920ba75028c064abf8c43`. Se ejecutó el
bloque revisado como `romel` no-root en Ubuntu WSL interactiva, con `require_escalated` y sin
`sudo`. El preflight de hashes pasó. Salida sanitizada y exit del runner:

```text
phase=prior-endpoint-attestation|error_code=OK
phase=synthetic-image-read|error_code=IMAGE_INSPECT_TEMPLATE_ERROR
exit=1
```

La aprobación se consumió. La lectura fue de solo lectura y usó la imagen sintética fijada. El
clasificador detectó el marcador cerrado de error de Go template en la respuesta de Docker; el
stderr crudo se descartó. No permite identificar cuál subexpresión falló ni probar un defecto del
Engine.

## Etapas detenidas

El stop-on-failure ocurrió antes de las catorce pruebas focales, el contenedor de probes y las 25
expresiones de `docker inspect`. No se creó ni eliminó contenedor. No hubo lectura de F1, r9,
`studiamatch-dev`, pull/build/install, retry ni cambios de configuración Docker.

## Corrección y siguiente gate

No repetir el template combinado `{{.Id}}|{{json .Config.Volumes}}`. El siguiente diagnóstico
aislará, con argv exactos y salida acotada, `{{.Id}}` y `{{json .Config.Volumes}}` en llamadas
separadas. El fallo de cada llamada se clasificará en memoria y solo emitirá fase/código. Una nueva
invocación requiere su propia aprobación.

G01=10/10, G02=10/10, G03–G10=0/10; total 20%, delta cero. Las pruebas parciales anteriores se
conservan por separado; no hay `GO_LOCAL_PR` ni `GO_DEVELOPMENT_REAL`.
