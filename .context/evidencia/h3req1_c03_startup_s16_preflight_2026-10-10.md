# G06 S16 — bloqueo de preflight, causa identificada

Fecha: 2026-10-10. Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`,
rama `feat/h3req1-sync-20261002`, HEAD baseline
`4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Resultado ejecutado

S16 tuvo revisión estática independiente PASS. El intento único terminó antes
de crear su runtime:

```text
runner-sha256=7cf1f007dcd25d4426fe1f0d9685c96fd3bcbf798d0f2c9d9787c0dbbf080fbe
sidecar-sha256=6c139663c1b3b7d213ea6c79a0f7139de2b081ecc20a1675d23dd7d13d675eb0
command=bash tests/h3req1_c03_startup_runtime_diagnostic_s16.sh --runner-sha256 7cf1f007dcd25d4426fe1f0d9685c96fd3bcbf798d0f2c9d9787c0dbbf080fbe --sidecar-sha256 6c139663c1b3b7d213ea6c79a0f7139de2b081ecc20a1675d23dd7d13d675eb0
phase=preflight
exit=1
predicate=S18 source volume options or attachments differ
runtime-created=false
```

La proyección Docker acotada del volumen S18 mostró opciones `null` y labels
esperadas. El filtro por ese volumen mostró exactamente dos adjuntos: el
snapshot S18 terminado (`48116e932a4756e9180191e69655fc4b7a571c37fc0e4ccfd627e2ad9857f9ea`)
y el runtime S15 preservado (`d45b6f4ef1ab80a4b81bccc2900d073f45d17e655acc776e3044757e60343ae1`).
S15 está `exited/0`, `oom=false`; su mount `/candidate` usa el volumen S18 en
solo lectura. Su evidencia conserva `healthz=PASS`, `smoke=PASS` y el NO-GO
del supervisor por falta del marcador de digest.

## Causa demostrada y corrección

El predicado de S16 exigía que el snapshot S18 fuera el único contenedor
adjunto. Esa condición contradice el estado preservado de S15, que usa el mismo
volumen para ejecutar Pages/workerd y conservar el resultado. No es un fallo
del volumen ni del runtime. S16 no alcanzó el contrato ni arrancó Pages.

Se corrigió el predicado para aceptar únicamente el par exacto snapshot S18 +
runtime S15, normalizando el orden; el runtime S15 debe conservar identidad,
estado y sus cinco mounts exactos, todos read-only. El contrato sintético exige
ambas identidades y la comparación completa contra el conjunto esperado. No se
retiró ni modificó S15, S18, S11, sus volúmenes ni la red.

La lectura inicial de mounts usó una plantilla Go con un campo no disponible y
falló sin devolver datos. Se reemplazó por una proyección válida limitada a
tipo, destino y permiso de escritura; no se leyó `Env` ni un inspect completo.

## Revalidación del delta

- Contrato Pages/startup: `phase=s15-runtime-contract|error_code=PASS|cases=7`
  dentro del Node fijado, `network=none`, runtime del snapshot read-only y
  contrato/probe/runner read-only.
- Probe corregido: `phase=runtime-diagnostic-synthetic|error_code=PASS`.
- ShellCheck 0.11.0: PASS con imagen local fijada, `network=none`.
- Bash syntax, `git diff --check`, INPUTS 32/32 y sidecar: PASS.
- Runner actual: SHA-256
  `2e658f6d2e0dc9e75296080c2c4ca9dd0cee6684edb001208ce2521e3685669e`.
- INPUTS: SHA-256
  `fefd46a83f50fe73fcb717a51c100208e0ec62942b6dfe79414ce94a18c9241e`.
- Sidecar: SHA-256
  `c8c6358427b0948ce5754de5fd2fc0107912fe21b914e1e2a22ba2c303c9ccc0`.

La revisión independiente detectó y detuvo otra invocación antes de runtime
por un `CONTRACT_TEST_SHA` interno antiguo; se actualizó el pin y el test ahora
verifica explícitamente la igualdad exacta del conjunto de adjuntos. Se pidió
revisión estática final de estos pins.

## Resultado posterior

La preflight anterior queda preservada como fallo del predicado de adjuntos.
Tras corregir ese predicado y su pin interno, S16 se ejecutó y cerró con exit 0:
Pages/workerd alcanzó healthz real, `workerd=true`, asset raíz PASS, smoke PASS,
digest de dependencias PASS, 22 intentos y `oom=false`. El runtime temporal se
retiró por ID exacto; S15/S18/S11 y sus volúmenes se conservaron. Evidencia
canónica: [resultado S16](h3req1_c03_startup_smoke_2026-10-10_s16_diagnostic.md).
