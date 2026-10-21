# H3REQ1 C03 — V4 corregido pasó sintéticos; F1 container inspect falló

Fecha: 2026-10-09. Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Aprobación e invocación consumida

El usuario aprobó una invocación del JIT
`H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-CLASSIFIER-V4-FIX-AND-R9-ONCE-20261009-V1`, SHA-256
`949748aa95a4bc3aa0ed6ecda4c95ed1157ba0840cf89dc2cbc4b5c11521878c`. Se ejecutó una vez
como `romel` no-root en terminal Ubuntu WSL interactiva, con acceso elevado del entorno y sin
`sudo`.

Salida sanitaria exacta:

```text
phase=prior-desktop-wsl-endpoint-attestation|error_code=OK
phase=classifier-synthetic-image-read|error_code=OK
phase=classifier-synthetic-tests|error_code=OK
phase=f1-image-read|error_code=OK
phase=f1-container-read|error_code=INSPECT_TEMPLATE_EVALUATION_ERROR
exit=1
```

Los sintéticos V4 corregidos, incluida la aserción de secuencia exacta, pasaron. La imagen F1
allowlisted pasó su predicado. La lectura del contenedor F1 no satisfizo su predicado; el runner
detuvo el ciclo antes de r9. La aprobación quedó consumida. No hubo retry, pull, build,
instalación, cambio Docker, ni acceso o modificación de `studiamatch-dev`.

## Predicado discrepante

Resultado esperado: `phase=f1-container-read|error_code=OK`. Resultado observado:
`INSPECT_TEMPLATE_EVALUATION_ERROR`. Esto localiza el fallo en la evaluación de la plantilla de
lectura del contenedor; no permite inferir metadata del contenedor ni si el daemon la considera
inválida. No se conservó salida cruda y no se repetirá la lectura Docker para aclararlo.

## Siguiente paso

La revisión estática confirmó cuatro `index` directos en la plantilla: tres sobre
`Config.Labels` y uno sobre `HostConfig.Tmpfs`. El error de evaluación es compatible con un mapa
nil en cualquiera de ellos, pero la salida sanitaria no identifica cuál. No se infirió que
faltara metadata ni se leyó de nuevo el contenedor.

Se preparó el helper V5 con `with` para esas lecturas; preserva el orden de 25 campos y el parser
estricto que exige labels y tmpfs. El cambio solo mejora cómo se representa un mapa ausente:
produce campos vacíos y el parser devuelve `F1_POLICY_MISMATCH`. Cuatro sintéticos cubren las
guardas, su aplicación antes del inspect, y el rechazo de labels/Tmpfs ausentes. Los siete casos
V4 previos se conservan como entrada del reporter; el runner exige PASS de todos los 11 casos y
falla cerrado ante skip, missing, colección distinta o fallo.

La revisión independiente no encontró hallazgos; verificó los pins, el orden de campos, la
aplicación de plantilla, el parser estricto, el filtro sanitario y el r9 condicional. Revisión
read-only; no ejecutó Docker, pytest ni Python de proyecto. `bash -n` del wrapper V5 pasó y
`git diff --check` no reportó whitespace. Los sintéticos V5 aún no se ejecutaron.

El siguiente paquete [JIT V5 nil-safe + F1/r9 condicional](../operaciones/jit_h3req1_docker_desktop_wsl_f1_template_nil_safe_v5_r9_once_2026-10-09.md),
SHA-256 `72d1c46aaa5c615d23308e605e8ad95edd8f8c39b2b0796ef171c355c7c8b316`, requiere nueva
aprobación. La revisión final read-only confirmó que pines, operaciones, frontera de r9
condicional y salida `exit=<n>` alinean con el runner; `exit=<n>` solo se imprime ante fallo r9.
Tras autorizarlo, valida sintéticos primero, realiza una lectura de F1 y corre r9 solo con PASS
completo. El JIT V4-FIX sigue consumido; no se reintenta.

## Gates

G01=10/10, G02=10/10, G03–G10=0/10; total 20%, delta 0. D01–D14=0/14. Parciales separados:
endpoint/identity previo PASS; JIT V4-FIX sintéticos 7/7 PASS; imagen sintética y F1 image read
PASS; F1 container read FAIL; r9 no ejecutado. No cierran un gate. No hay `GO_LOCAL_PR` ni
`GO_DEVELOPMENT_REAL`.
