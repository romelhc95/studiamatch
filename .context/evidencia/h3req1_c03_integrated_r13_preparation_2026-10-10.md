# G07 R13 — clasificación HTTP precisa y ejecución integrada

## Candidato y delta

- Checkout: `/home/romel/src/studiamatch-h3req1-sync-20261002`.
- Rama/HEAD: `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- Docker Desktop local fijado por el runner: contexto `default`, engine ID
  `fc2115b2-c3c4-440e-89c6-26899eb7cb04`, servidor 29.8.2.
- R11 preservado: integrado falló exit 1 en `real-edge-invite-held-after-reservation` con
  `LOGIN_HTTP_STATUS_NOT_200`; aún no registraba el número HTTP. Log sanitizado
  [R11](h3req1_c03_integrated_run_2026-10-10_r11.log), SHA-256
  `c960ee86ae60a9bdbea1560c43ac2f543de057f61379060cf4c613b880f7f296`. Failure-stop detuvo
  únicamente los cuatro servicios etiquetados R11. No se concluye si la respuesta fue entrada,
  cuota, Auth o sesión.
- R12 preflight preservado: 13/14 pruebas; el fixture sintético AAL reveló un desplazamiento de
  índice en el clasificador después de añadir status HTTP exacto. No creó redes/containers ni
  ejecutó SQL. Evidencia [R12 estática fallida](h3req1_c03_integrated_r12_static_validation.txt),
  SHA-256 `2c51bb6054d651dc6b4dafa2f7d8c3d04382bc77ca3edf389199be854097356a`.
- Corrección R13: asignación explícita correcta de AAL, cookie Auth y cookie actividad; status
  inválido queda `LOGIN_HTTP_STATUS_INVALID`; status entero válido queda `LOGIN_HTTP_STATUS_NNN`
  para 100–599. La salida sigue cerrada y no expone cuerpo, texto, identidad ni cookies.

## Evidencia estática R13

El manifiesto actual tiene 65 entradas y verifica 65/65. SHA-256 del manifiesto:
`4ad2a1814e8b829cec352b78aa91d29aaf1590b72054000d0f6a147e5c37b127`.

- Runner R13: `fc163ce6a912fe5bad8a3e55b4a6d715d4120ed5fb2b6baabca3a3f4c97609a6`.
- Runtime: `8d418f149e0287f9ef2dac737f977c715ac0ee46ff6abec1f43a64be93faa9a3`.
- Helper: `7f98dd2018ef6dee2a2e0d016e2fde90e3ecb379a66a9aded9c1f24ec03dc822`.
- Contract R13: `c19a268c0b22aa762814606a6fea833002f13eb7b6e62340efeeae4a12ae9cd2`.
- SQL fixture R13: `e373f007f06fcdff23a47ff6c8185d9736465480a1acefb0c310f347355870e5`.
- El manifest R12 pre-corrección está preservado en
  [manifest R12](h3req1_c03_integrated_manifest_r12.sha256), SHA-256
  `fe748e5608d1f281f7dfb7bf320e826038ce02ba8a5c369a597302741db2b83d`.
- Bash `-n`, 14/14 pruebas contractuales, ShellCheck 0.11.0 warning-level y `git diff --check`
  pasan en contenedores aislados. Evidencia
  [estática R13](h3req1_c03_integrated_r13_static_validation.txt), SHA-256
  `c3b2f1d0dba568ced0c3d29925622e67959b8804dcc16ae0967e1b406ec77bca`.
- La revisión independiente estática R13 concluyó PASS sin blockers; no ejecutó runtime.
- Todavía no hay resultado runtime R13.

## Invocación integrada autorizada por el ciclo local

```bash
/usr/bin/timeout --foreground --signal=TERM --kill-after=15s 1800s \
  /bin/bash tests/h3req1_c03_integrated_drill_r13.sh \
  --jit H3-CLOSE-03-INTEGRATED-2026-10-10-R13 \
  --manifest-sha256 4ad2a1814e8b829cec352b78aa91d29aaf1590b72054000d0f6a147e5c37b127
```

Cada ejecución usa recursos R13 nuevos, imágenes fijadas locales (`--pull=never`), redes internas,
PGDATA en tmpfs, caches read-only, fuente del candidato snapshotteada y claves sintéticas. Ante
fallo detiene servicios del nonce actual y conserva logs/recursos. No toca `studiamatch-dev`, el
checkout original, `.env*`, cloud ni servicios remotos. Limpieza de containers/redes R13 solo tras
PASS completo y revalidación de ownership; volúmenes e imágenes permanecen.

## G07 y recuperación

G07 permanece parcial hasta que C03 integrated concluya exit 0 con la secuencia completa. G01 y
G03 no se reabren por este delta; G08/G09 quedan dependientes del cierre integrado. Un R13 FAIL se
registra con fase, exit y código sanitizado, y solo se corrige después de demostrar el predicado.
