# H3REQ1 C03 — V7 smoke clasificado, evaluación de template sin localizar

Fecha: 2026-10-09. Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Invocación consumida

El usuario aprobó una invocación de
`H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-TEMPLATE-SMOKE-CLASSIFIED-V7-R9-ONCE-20261009-V1`, SHA-256
`d83ae63a49ce94be4672822758fb294c5a951af1a060ddfcb63f59d764808f2f`. Se ejecutó una vez con
`require_escalated` como `romel` no-root en Ubuntu WSL interactiva, sin `sudo`.

Salida sanitaria:

```text
phase=prior-desktop-wsl-endpoint-attestation|error_code=OK
phase=classifier-synthetic-image-volumes-read|error_code=OK
phase=classifier-synthetic-image-read|error_code=OK
phase=classifier-v7-focused-tests|error_code=OK
phase=f1-template-synthetic-inspect|error_code=INSPECT_TEMPLATE_EVALUATION_ERROR
```

El runner terminó con exit 1. El primer smoke, con labels allowlisted y tmpfs presente,
alcanzó inspect y se detuvo; el cleanup no emitió un código de fallo. Los cuatro casos V7
aprobaron. No se inició el smoke con mapas ausentes, lectura F1, r9 ni otra etapa. La invocación
queda consumida: no retry, pull/build/install, cambios de Docker, ni acceso a `studiamatch-dev`.

## Qué demuestra el resultado

El código `INSPECT_TEMPLATE_EVALUATION_ERROR` significa que el clasificador identificó una
evaluación Go-template fallida, pero no encontró una expresión/categoría concreta en su lista
cerrada. La prueba V7 que pasó cubre una firma sintética específica para `.Config.Labels`; no
demuestra que esa firma coincida con el error observado. La salida disponible no identifica la
expresión que falla, así que no atribuyo la causa a Docker ni a un campo concreto.

## Corrección y siguiente gate

El V7 se detuvo en el primer smoke antes de F1 y r9. Preparar un diagnóstico aislado por
expresión del mismo formato allowlisted, conservando la captura de stderr en memoria y emitiendo
solo `phase` y un código de error cerrado. Añadir pruebas sintéticas para expresiones permitidas,
errores conocidos y fallback desconocido; revisión independiente; ejecutar una sola vez después
de autorización concreta. No volver a ejecutar V7 ni las 15 pruebas V4–V6. Una vez identificado y
corregido el subpaso en el runner, solicitar un JIT nuevo antes de cualquier operación Docker.

## Gates y parciales

G01=10/10, G02=10/10, G03–G10=0/10; total 20%, delta 0; D01–D14=0/14. Parciales separados:
atestación de endpoint previa PASS; V4/V5/V6 15/15 sintéticos históricos PASS con sus pines;
V7 focused tests PASS; imagen sintética y lectura de volúmenes PASS; primer template smoke FAIL;
smoke sin mapas, F1, r9, copia íntegra, Pages/workerd, integración C03 y aceptación final no
alcanzados. No existe `GO_LOCAL_PR` ni `GO_DEVELOPMENT_REAL`.
