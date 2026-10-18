# H3REQ1 C03 — preparación V6 del smoke Go-template y clasificación F1

Fecha: 2026-10-09. Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`. El WIP no se
representa solo por HEAD: 54 entradas tracked modificadas, 200 untracked y 0 staged. El checkout
original y sus cambios permanecen preservados.

## Estado V5 consumido

El JIT V5
`H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-TEMPLATE-NIL-SAFE-V5-R9-ONCE-20261009-V1`, SHA-256
`72d1c46aaa5c615d23308e605e8ad95edd8f8c39b2b0796ef171c355c7c8b316`, fue aprobado y ejecutado
una vez. Endpoint, imagen sintética, 11/11 sintéticos e imagen F1 dieron `OK`; la lectura del
contenedor F1 devolvió `INSPECT_TEMPLATE_EVALUATION_ERROR`, exit 1. El stop-on-failure impidió
ejecutar r9. No hubo retry, pull/build/instalación, cambio Docker, acceso a `studiamatch-dev`,
copia, arranque o integración. El resultado íntegro permanece en
[evidencia V5](h3req1_c03_v5_nil_safe_template_evaluation_failure_2026-10-09.md).

El resultado sanitizado no identifica la expresión que falló y no demuestra que Docker tenga
un defecto. La hipótesis nil-safe previa no explica suficientemente el error.

## Correcciones de preparación V6

- Añade una validación read-only del `Config.Volumes` de la imagen sintética antes de crear
  contenedores y prueba el formato Go F1 exacto contra dos contenedores sintéticos efímeros:
  metadata con labels/Tmpfs presentes y mapas ausentes. El runner comprueba salida de 25 campos,
  campos relevantes, comportamiento fail-closed, límites y cleanup.
- Refina `INSPECT_TEMPLATE_EVALUATION_ERROR` solo cuando stderr acotado contiene expresiones
  allowlisted; en cualquier caso conserva fases/códigos cerrados y nunca emite metadata ni
  texto crudo del Engine.
- El preflight V6 fija el archivo V5 `test_f1_read_failure_classification_v5_once.py` al digest
  `f8880ccb9d6bf2324e5f7982712ce08f6508d09df68b3c087b91b3753e51219f` y asigna ese path al
  precheck heredado. Evita asociar ese digest al path de pruebas V1.
- El runner sintético fija y comprueba la suite base V4 antes de pytest con SHA-256
  `369382daa3445999704d85278a482edf78648a61a8e1ef3703ace37a2b923199`; propaga los errores de
  disponibilidad/hash como códigos cerrados al wrapper.
- La revisión independiente encontró una fuga posible de ruta por stderr del wrapper; el
  comando JIT ahora descarta stderr del wrapper, manteniendo solo stdout sanitario.
- Una segunda revisión halló que la suite V4 no estaba fijada. Se corrigió antes de pedir
  autorización; la revisión independiente final no encontró hallazgos.
- V6 conserva stop-on-failure: F1 se lee una vez tras sintéticos; r9 se ejecuta una vez solo si
  la secuencia completa es `OK` y los controles F1 pasan. La lectura del endpoint/identidad no
  se repite.

## Paquete y validación previa

JIT agrupado pendiente de aprobación nueva:
[V6 template smoke + F1/r9 condicional](../operaciones/jit_h3req1_docker_desktop_wsl_f1_template_smoke_v6_r9_once_2026-10-09.md),
ID `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-TEMPLATE-SMOKE-V6-R9-ONCE-20261009-V1`, SHA-256
`c84491eee2e23bba26be38985e4658ffe280947c43c953f232eb23699d915277`. El wrapper combinado está
fijado a `ba57b3bd613bafdd05ffe7d31377b6468ca1c4a7a74cbbcf39c86130034df080`; el clasificador a
`b17266a33559b16b28cdf1b619f9b5d7dae666203f6d9a357b046ed7ae809128`.

`bash -n` del wrapper, compilación sintáctica Python en memoria y `git diff --check` dieron
`PASS`. Se comprobó la consistencia estática de pins y la secuencia esperada. La revisión
independiente final verificó las suites V4/V5/V6 (7+4+4 casos), salida cerrada, cleanup y gates
F1/r9; no ejecutó tests ni Docker. No se ejecutaron pytest, el runner V6, Docker ni r9 en esta
preparación.

## Límites y gates

La próxima invocación requiere autorización humana nueva porque V5 quedó consumido. Su alcance
se limita al smoke sintético, una lectura F1 y r9 condicional, sin retry ni cambios de Docker,
imagen, daemon, configuración, `studiamatch-dev`, SQL, ramas, remoto o producto. Tras una
autorización y resultados completos PASS se retoma r9 y las etapas locales que sigan autorizadas;
cualquier FAIL detiene la etapa dependiente.

Los cuatro ajustes de producto siguen sin revalidación en este corte; sus inputs, pruebas
preservables, cobertura y siguiente acción están en la
[matriz de aceptación](h3req1_desarrollo_existente_y_cierre_delta_2026-10-08.md#matriz-de-aceptación-de-los-cuatro-ajustes).
CI Protected Workflow Integrity sigue preparado en aislamiento, sin tests locales, instalación,
publicación, resultado remoto, required status ni enforcement.

G01=10/10, G02=10/10, G03–G10=0/10; total **20%**, delta 0. D01–D14=0/14. Parciales V5 se
mantienen separados; no hay `GO_LOCAL_PR` ni `GO_DEVELOPMENT_REAL`.
