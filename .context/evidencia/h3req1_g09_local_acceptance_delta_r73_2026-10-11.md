# H3REQ1 G09 delta R73 — recuperación tras fallos parciales de discovery — 2026-10-11

## Identidad y ejecución

- Checkout: `/home/romel/src/studiamatch-h3req1-sync-20261002`.
- Rama/HEAD baseline: `feat/h3req1-sync-20261002` /
  `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- Fuente ejecutada: `tests/test_h3req1_local_pipeline_walk.py`, SHA-256
  `3e72ee4c846c3dbed16c23a19bd892ecc1998a5de017a10ad5a762f87895e4bb`.
- Contenedor: `studiamatch-dev`, estado healthy, imagen local
  `studiamatch-h3req1:20261009-v3`; `/app` está montado desde el checkout
  candidato con lectura/escritura y el digest de la fuente dentro/fuera del
  contenedor coincidió. No se leyó `.env*`.
- Comando ejecutado dentro de Docker, con `env -i`, bytecode y cache pytest
  desactivados, y timeout de la invocación de 120 s:

  ```text
  /opt/venv/bin/python -m pytest -q -p no:cacheprovider \
    tests/test_h3req1_local_pipeline_walk.py::test_paginated_discovery_preserves_and_resumes_results_after_later_page_failure \
    tests/test_h3req1_local_pipeline_walk.py::test_catalog_scroll_keeps_discovered_links_when_a_later_scroll_fails
  ```

## Resultado

Exit 0: **2 passed**, cero retries, 0,54 s; se conservó una advertencia de
deprecación PyPDF2. Log:
`h3req1_g09_local_acceptance_r73/pipeline-partial-recovery-r73.log`;
exit: `h3req1_g09_local_acceptance_r73/pipeline-partial-recovery-r73.exit`.

La primera página/scroll deja una URL `discovered`; un fallo posterior no la
borra. La recuperación vuelve a visitar la fuente, reutiliza la URL previa,
incorpora la segunda y termina con dos filas únicas en estado `discovered`.
La página sintética se cierra. No hubo HTTP externo, writers cloud ni llamadas
a la base de datos.

## Impacto y límite

Esto renueva solamente la prueba de recuperación parcial de discovery que no
estaba incluida en el resultado R18 descrito por la evidencia anterior.
LOCAL-07 queda más cubierto y LOCAL-08 conserva evidencia de recuperación por
etapa ya existente. **No cierra G09-T04:** el adaptador es en memoria, no PG17;
faltan la persistencia/checkpoint y el recorrido de recuperación contra el
fixture PostgreSQL integrado, además de escenarios faltantes de otras áreas.
No cambió código de producto y las métricas de gates no cambian.
