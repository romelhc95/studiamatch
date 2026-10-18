# H3REQ1 C03 — salida sintética V4 incompleta en la expectativa

Fecha: 2026-10-09. Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Aprobación e invocación consumida

El usuario aprobó una ejecución del JIT
`H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-CLASSIFIER-V4-R9-ONCE-20261009-V1`, SHA-256
`d6e28031197cf6a2c34ed205ead389d0f7dc514ae745678aa505570a7bfe7648`. Se ejecutó una sola vez
como `romel` no-root en Ubuntu WSL interactiva, con acceso elevado del entorno y sin `sudo`.

Salida sanitaria exacta:

```text
phase=prior-desktop-wsl-endpoint-attestation|error_code=OK
phase=classifier-synthetic-image-read|error_code=OK
phase=classifier-synthetic-tests|error_code=V2_MAIN_OUTPUT_ASSERT_FAILED
exit=1
```

El contenedor sintético y el ID de su imagen llegaron a los predicados esperados. Falló el
assert de secuencia de salida del caso sintético `test_v2_main_failure_emits_exact_sanitized_sequence`.
Stop-on-failure consumió la autorización y detuvo antes de leer imagen/contenedor F1 o ejecutar
r9. No hubo retry, pull/build/instalación/cambio de Docker ni acceso/modificación de
`studiamatch-dev`.

## Predicado y causa demostrada por inspección estática

El test espera `desktop-wsl-endpoint-attested|OK`, `f1-image-read|OK` y
`f1-container-read|INSPECT_TEMPLATE_EVALUATION_ERROR`. Sin embargo,
`f1_read_failure_classification_v2_once.py::main()` emite además
`classifier-synthetic-tests|OK` inmediatamente después de `run_synthetic_tests()` y antes de
leer la imagen F1. El helper sintético se sustituye por no-op en ese caso, pero la emisión de
fase permanece. La expectativa exacta omitía esa fase; el fallo corresponde a la fixture, no
al clasificador ni a Docker.

## Corrección mínima y siguiente comprobación

La corrección añade `phase=classifier-synthetic-tests|error_code=OK` a la secuencia esperada en
su posición de emisión. No cambia código funcional, comportamiento de F1, salida real del
runner ni requisitos del gate. El siguiente JIT separará una sola invocación nueva: primero
corre el mismo conjunto de sintéticos fijado con esa expectativa corregida; solo si todo pasa
lee F1 una vez y luego r9 una vez. El JIT V4 anterior se conserva como consumido y no se repite.

La revisión independiente final no encontró hallazgos en este delta, confirmó que la secuencia
esperada coincide con el orden de `main()` y verificó los pins del test, clasificador y runner
combinado. Fue read-only; no ejecutó Docker, pytest ni Python de proyecto. No se ejecutaron esas
pruebas fuera de la invocación consumida. El cambio requiere una nueva autorización antes de
ejecutar las pruebas en la imagen existente.

## Gates

G01=10/10, G02=10/10, G03–G10=0/10; total 20%, delta 0. D01–D14=0/14. La lectura de endpoint,
la imagen sintética y esta corrección documental/test no suman puntos. No hay
`GO_LOCAL_PR` ni `GO_DEVELOPMENT_REAL`.
