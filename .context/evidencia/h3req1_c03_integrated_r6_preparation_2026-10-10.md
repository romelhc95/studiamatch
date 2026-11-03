# H3REQ1 C03 integrado R6 — preparación

## Alcance

- Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
  `feat/h3req1-sync-20261002`, HEAD baseline `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- Gate activo: G07, C03 integrado local. R5 se consumió con exit 1 en
  `isolated-postgrest`; antes pasaron el snapshot, PG17 17.11 con bootstrap
  H2→Pro→H3, setup/fixtures C03 y Pages/workerd `healthz`.
- Causa demostrada: no existe causa de servicio aún. R5 no clasificaba el
  resultado de `GET /`; PostgREST aparecía `running` y 60 respuestas no 2xx
  producían el mismo NO-GO. No se atribuye a Docker ni al producto.
- Consumidores del probe: runtime Pages/workerd del ensayo integrado y runner
  C03. El probe llama al hostname fijo de PostgREST en red interna de pruebas.
  No altera BFF, Edge, SQL funcional ni contrato de producto.

## Paquete R6

- `tests/h3req1_c03_postgrest_probe.mjs` conserva solo fase y código sanitizado:
  estado HTTP, DNS, conexión, timeout o `FETCH_FAILED`; no escribe mensaje,
  cuerpo, headers ni metadata cruda.
- El runner espera `phase=postgrest-probe|error_code=OK`, clasifica únicamente
  códigos allowlisted, descarta stderr y falla cerrado ante salida inesperada.
  Las redes son internas (`--internal`), los pulls están prohibidos y los
  recursos se etiquetan con JIT/manifiesto/nonce. Los caches R4/R5 usados son
  read-only y se verifican contra digests históricos.
- El contrato R6 importa el runner R6 y cubre límites, pin del daemon, stop por
  ownership, cleanup por IDs inmutables y fallos sintéticos del probe.
- La primera revisión independiente encontró un hallazgo LOW: el stop best-effort
  omitía snapshot bootstrap y cache verifier ante señal/fallo. Se añadieron ambos
  recursos al stop limitado por labels/nonce y una aserción de contrato; cleanup
  normal ya los incluía.
- Manifiesto R6: 64 entradas; SHA-256
  `edd839808edc90683d035073abdd1038a8546658257363c3df5bd827fcc4a92d`;
  validación `sha256sum -c` 64/64.
- Runner SHA-256 `56444b6776f775c08be2e403661e374f00ac6e9d7b3dbc49ff7dc0e21c361c3e`.
- Contrato SHA-256
  `51a0b103b61706903db979facf26f6414cc949f2e164fa84a811c7e83d2af071`.
- Probe SHA-256
  `a3a6bacb4788a179653e6cb980856f4c8bde2be52d2431f62a4d0af0d7004206`.

## Validación previa a runtime

- Pruebas Node en imagen fijada, `network=none`, rootfs read-only y tres mounts
  de fuente read-only: 8/8 PASS tras incluir el test del stop de helpers.
- ShellCheck 0.11.0 oficial, nivel warning: PASS. Un primer despacho intentó
  usar `/bin/sh` dentro de la imagen mínima, que no lo contiene; falló antes de
  ejecutar ShellCheck y el contenedor `--rm` se retiró. El despacho corregido
  invocó el entrypoint del binario directamente y pasó.
- `bash -n`, `git diff --check`: PASS.
- Inventario acotado: `studiamatch-dev` permanece `healthy` en la imagen local
  `studiamatch-h3req1:20261009-v3`; nombres de contenedores/volúmenes R6 libres.
  R5 detenido y evidencia, volúmenes y redes internas se conservan.
- WIP antes de este registro: 55 tracked modified / 4386 untracked / 0 staged;
  preservar el checkout original y todos los artefactos preexistentes.

## Estado

Revisión independiente final: ambas revisiones dieron PASS estático en los pins
actualizados, incluyendo la corrección del stop de emergencia. La ejecución R6
terminó exit 1 en `healthz`; G07 continúa parcial. El log sanitizado es
`h3req1_c03_integrated_run_2026-10-10_r6.log`. Snapshot, caches y 64/64 hashes
pasaron; el runtime salió exit 1 en 0.45 s, `OOMKilled=false`, `log-driver=none`.

La causa quedó demostrada en el snapshot R6: estaba ausente
`tests/h3req1-c03-integrated.sha256`, que el runtime integrado lee en
`tests/h3req1_c03_integrated_runtime.mjs:734–736`; solo estaba presente el
manifiesto renombrado `tests/h3req1-c03-integrated-r6.sha256`. Un contenedor de
lectura con el volumen snapshot devolvió `runtime-manifest=missing` y
`r6-manifest=present`. No es un fallo de producto ni de Docker. R7 conserva el
nombre canónico consumido por el runtime y añade una prueba de contrato para
evitar la divergencia. No hubo SQL ni Edge en R6; los recursos R6 se retienen.

No se considera G07 completo hasta que el runtime C03 atraviese todas las
aserciones y cierre con exit 0. La preparación y validación R7 están en
[R7](h3req1_c03_integrated_r7_preparation_2026-10-10.md).

```bash
/usr/bin/timeout --foreground --signal=INT --kill-after=60s 1800s \
  /bin/bash tests/h3req1_c03_integrated_drill_r6.sh \
  --jit H3-CLOSE-03-INTEGRATED-2026-10-10-R6 \
  --manifest-sha256 edd839808edc90683d035073abdd1038a8546658257363c3df5bd827fcc4a92d
```
