# H3REQ1 C03 integrado R7 — preparación

## Candidato e inputs

- Checkout: `/home/romel/src/studiamatch-h3req1-sync-20261002`.
- Rama `feat/h3req1-sync-20261002`; HEAD baseline
  `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- Gate activo: G07. WIP antes de esta nota: 55 tracked modified / 4390
  untracked / 0 staged (4445 entradas); preservado, sin inferir identidad desde
  HEAD.
- R6 se consumió con exit 1 en `healthz`. Evidencia clasificada y causa
  demostrada: [R6](h3req1_c03_integrated_r6_preparation_2026-10-10.md).
- Corrección mínima R7: el runner y el runtime integrado usan el manifiesto
  canónico `tests/h3req1-c03-integrated.sha256`. Se añadió un test que compara
  ambos paths. No se editó el runtime ni el producto.
- La anterior copia del manifiesto staging se preservó en
  `h3req1_c03_integrated_manifest_pre_r7.sha256`; el manifiesto R6 específico y
  su runner/test también se conservan.

## Validación local

- Test contractual Node: 9/9 PASS en la imagen fijada, `network=none`, rootfs
  read-only, inputs montados read-only.
- ShellCheck 0.11.0 oficial, warning level: PASS.
- `bash -n`, `git diff --check`: PASS.
- Manifiesto canónico: 64 entradas, `sha256sum -c` 64/64 PASS.
- Pins:
  - runner `tests/h3req1_c03_integrated_drill_r7.sh` SHA-256
    `48dc1cc6a9ee98e3bcccf83163a2c5c36ab5ec15ec47333cff47d0e6ab79ec0f`;
  - test `tests/h3req1_c03_integrated_drill_r7_contract.test.mjs` SHA-256
    `0dd050ba3521b66d6662216a857eaf259376141b676377c4aa7e126089e00073`;
  - runtime `tests/h3req1_c03_integrated_runtime.mjs` SHA-256
    `17ddfa989a1f3322fa1812bb4fefbe83161d5a82d289ae170eb6b31ac7a8ec40`;
  - probe `tests/h3req1_c03_postgrest_probe.mjs` SHA-256
    `a3a6bacb4788a179653e6cb980856f4c8bde2be52d2431f62a4d0af0d7004206`;
  - manifiesto canónico SHA-256
    `ee3553d810c9bd3074b856d5c5db9bba1eda1b02e40ab6da5b73edafc98dda5b`.
- El inventario previo dejó `studiamatch-dev` healthy; nombres de recursos R7
  libres. R5/R6, recursos históricos y volúmenes se mantienen separados.
- La primera revisión estática dio PASS; la segunda encontró un residual LOW de
  deadline individual en los dos `docker run` de primer plano.

## Estado de R7

R7 no se ejecutó. Se preservó su manifiesto preejecución y fue supersedido por
R8, que acota las llamadas Docker directas a 60 s, el bootstrap de snapshot a
300 s y el verificador de caches a 180 s. R8 añade pruebas de contrato para
esos límites. Sus pins y revisión quedan en:

[R8](h3req1_c03_integrated_r8_preparation_2026-10-10.md).

R7 no consumió runtime; G07 permanece incompleto.
