# G07 — Preparación del diagnóstico integrado R21

## Identidad y recursos

- Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
  `feat/h3req1-sync-20261002`, HEAD baseline
  `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- Antes de crear esta nota: WIP `558` entradas (`git status --short`) y `4578`
  rutas (`--untracked-files=all`). Se preservan los demás cambios del checkout.
- R20 se consumió con exit 1 en `admin_members` HTTP 403. Runtime, Edge, PostgREST,
  PG17 y dos auxiliares exactos quedaron `exited`; PGData era tmpfs. No se limpiaron
  esos recursos, imágenes, volúmenes ni redes. R21 usa nombres nuevos; no había
  colisiones de contenedores, redes ni log.
- `studiamatch-dev` no se usó para este ensayo; no se leyeron `.env*`, sus valores
  ni credenciales operativas.

## Reproducción, cambio y cobertura

El R20 no guardó el código de error de PostgREST. El cambio mínimo está limitado al
harness de `tests/h3req1_c03_integrated_runtime.mjs` y al helper nuevo
`tests/h3req1_c03_safe_postgrest_error_code.mjs`: lee una copia de la respuesta de
error de hasta 8 KiB, permite solo `PGRSTddd` o cinco caracteres SQLSTATE y emite
`UNCLASSIFIED` en otro caso. No lee/guarda `message`, `details`, `hint` ni body crudo;
la respuesta original permanece disponible para el relay.

El contrato R21 añadió clasificación sintética de código válido, minúsculas,
longitud inválida, tipo no-string, array, campo ausente, JSON malformado, body vacío,
límite excedido y preservación de lectura del body original. La primera prueba de
cuerpo grande descubrió que esperar `reader.cancel()` de una rama `Response.clone()`
podía esperar a que se consumiera la rama original. El helper ahora inicia esa
cancelación sin bloquear antes de relayar la respuesta.

## Validación previa

- Node `--check` para helper, runtime y contrato, y Bash `-n` para el runner:
  **PASS**, dentro del contenedor Node fijado
  `sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844`,
  `network=none`, rootfs read-only, tmpfs `/tmp`, solo 7 archivos allowlisted.
- Contrato del runner R21: **22/22 PASS**, exit 0 en ese contenedor.
- `git diff --check`: PASS.
- Manifiesto integrado: **74 entradas**, `sha256sum -c` PASS; digest del manifiesto
  `67000ea1881bc584898ee279d9ac4a0eaaf3835f673c3e5c4a406578d179e19f`.
- Tres intentos de preparación anteriores a los tests fallaron por crear `/candidate`
  sobre rootfs read-only (exit 1), conservar UID/GID de tar sin capacidades (exit 2)
  y pasar un runner Bash a `sh -n` (exit 2). Se corrigió el scratch a `/tmp`, se usó
  extracción sin ownership y `/bin/bash -n`.
- La primera prueba sintética completa terminó cancelada (exit 1); reprodujo la espera
  de `reader.cancel()` descrita arriba. Tras corregirla, la pasada completa fue 22/22.
- Un intento de regenerar el manifiesto mediante un temporal con `rm -f` fue rechazado
  automáticamente antes de ejecutarse. Se actualizó por edición explícita, sin ejecutar
  limpieza ni borrar temporal.

## Próxima ejecución

La autorización humana del 2026-10-10 cubre este ensayo local integrado. El R21 nuevo
reconstruye el mismo PG17 desechable y servicios locales con datos sintéticos, conserva
las respuestas permitidas y detiene servicios propios al fallar. No toca cuentas,
correo, DB cloud, secrets, checkout original, `studiamatch-dev` ni servicios remotos.
El run se detiene en la primera fase fallida; no hay retry automático.

```bash
/usr/bin/timeout --foreground --signal=TERM --kill-after=15s 2400s \
  /bin/bash tests/h3req1_c03_integrated_drill_r21.sh \
  --jit H3-CLOSE-03-INTEGRATED-2026-10-10-R21 \
  --manifest-sha256 67000ea1881bc584898ee279d9ac4a0eaaf3835f673c3e5c4a406578d179e19f
```

G07 sigue parcial, sin delta: histórico G01–G10 **60%**; local G01–G09
**6/9 = 66.67%**. El resultado de la ejecución R21 se registrará aparte.
