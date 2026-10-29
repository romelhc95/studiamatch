# G07 R17 — preparación y revisión del runner

## Candidato y razón del siguiente ensayo

- Checkout: `/home/romel/src/studiamatch-h3req1-sync-20261002`.
- Rama/HEAD: `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- R16 terminó exit 1 en `create-internal-data-network`, antes de iniciar PG17,
  PostgREST, Pages/workerd o Edge. Docker Desktop agotó el pool de redes. El inventario y
  la retirada selectiva de 19 redes H3 internas vacías quedaron documentados por separado;
  no se alteraron contenedores, imágenes ni los 27 volúmenes H3.
- R17 reusa el runtime, fixtures, dependencias y pasos del R16 preservado. La copia del
  runner y su contrato cambia únicamente la versión identificadora `R16/r16` a `R17/r17`
  para JIT, nombres únicos de recursos, ruta del log, ruta del contrato y mensajes. No
  modifica predicados, límites, imágenes, pins, fixtures SQL, código de producto ni cleanup.

## Pins y validación previa

- Manifiesto R16 preservado: `.context/evidencia/h3req1_c03_integrated_manifest_r16.sha256`,
  SHA-256 `186862f80907e1e668b258d9c3ab7058d0360476be8b58f491288e501a324dfc`.
- Manifiesto actual, 67 entradas: SHA-256
  `6532388df6a09dd7dfd2359cc9979ad6666d1fec8b1f5c9dc1d2a567437f6105`; verificación
  `sha256sum -c` 67/67 PASS. Contiene R16 histórico y agrega las dos rutas R17.
- Runner R17 SHA-256 `6d9ba3b2b88578677c6147d02aac7841f06d3f5f6d225c49c0746a4d6c00deb1`.
- Contrato R17 SHA-256 `33467cf01382cec2342fa339efb672ed2d0bcb65cbcf09fbe09b9c8d9ebc7cf1`.
- `bash -n` y `git diff --check` PASS. Revisión comparativa: solo renombres R16→R17.
- El contrato se ejecutó en `node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844`,
  `--network none --read-only`, mount de tests read-only: 18/18 PASS, exit 0.
- Antes de crear recursos R17, Docker listaba 13 redes y cero redes con la etiqueta
  `com.studiamatch.h3.c03.jit`. Los nombres de recursos nuevos son exclusivos de R17.

## Ejecución prevista

Una ejecución de `tests/h3req1_c03_integrated_drill_r17.sh`, timeout exterior 1800 s,
sin retries y con stop-on-failure. El runner fija el endpoint Docker local, verifica rama,
HEAD, manifiesto, imágenes y caches por digest, valida snapshot íntegro y crea fixtures
etiquetados R17. Las fases runtime dependientes avanzan solo tras readiness real. El log
sanitizado se escribe en `.context/evidencia/h3req1_c03_integrated_run_2026-10-10_r17.log`.
Ante fallo, el runner detiene únicamente servicios del nonce exacto y preserva logs,
snapshot, volumen sintético y caches; no cambia imágenes ni datos operativos.

## Resultado

R17 ejecutado una vez. El preflight, snapshot, contrato, caches, healthz, PG17/PostgREST y login
pasaron; `trigger-inflight` devolvió `INVITE_EARLY_UNAUTHORIZED`, exit 1. La causa entre Auth
simulado y lectura de membresía todavía no está discriminada; véase [resultado R17]
(h3req1_c03_integrated_r17_result_2026-10-10.md). G07 continúa parcial.
