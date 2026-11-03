# Diagnóstico del rechazo del network-create en S3 — 2026-10-10

## Resultado real

- Runner S3 SHA-256 `4077a9c6e14a0588fb972f77c4b27385cc223306a63bbaea553b239c87af1689`;
  manifiesto `351c6590c24c466fe8af531f1d9661ef7a6fcc1f7170c617f223fefc70bdc018`.
- Snapshot: exit 0; 14 entradas, cero symlinks, hashes verificados, ownership restore desactivado.
- Bootstraps de herramientas y Pages: ambos contenedores terminaron exit 0.
- Fase detenida: `create-new-egress-blocked-internal-network`, runner exit 1. No se lanzó
  `h3req1_c03_startup_smoke_s1.mjs`; Pages/workerd y healthz no se alcanzaron.

## Causa demostrada

El Docker CLI completó `docker network create` y creó la red solicitada. El runner esperaba que
stdout de esa operación fuera el nombre; el CLI devuelve el ID del network. La comparación
`created_network == NETWORK` fue por tanto incorrecta aunque la creación hubiera tenido éxito.
Lectura estructurada read-only de la red existente confirmó ID con formato hexadecimal de Docker,
nombre exacto `h3req1-c03-startup-net-20261010-s3`, driver `bridge`, `Internal=true`, etiquetas
JIT/manifiesto S3 coincidentes y etiqueta de ejecución presente. Las cuatro etiquetas/recursos S3
preexistentes se reconciliaron sin imprimir el nonce: snapshot/tools/Pages `exited 0`, holder
`running`, tres volúmenes tmpfs con tamaños exactos y propiedad S3. No fue un fallo del engine ni
de Pages/workerd.

## Recursos preservados

- Contenedores: `h3req1-c03-startup-snapshot-20261010-s3` (exited 0),
  `h3req1-c03-startup-tools-20261010-s3` (exited 0),
  `h3req1-c03-startup-pages-20261010-s3` (exited 0),
  `h3req1-c03-startup-volume-holder-20261010-s3` (running).
- Volúmenes tmpfs exactos: `h3req1-c03-startup-source-20261010-s3` (96 MiB),
  `h3req1-c03-startup-tools-20261010-s3` (768 MiB),
  `h3req1-c03-startup-pages-20261010-s3` (1024 MiB).
- Red interna: `h3req1-c03-startup-net-20261010-s3`.
- S2 sigue preservado aparte. Ninguna limpieza ni modificación de los recursos ocurrió.

La continuación S4 se limita a verificar otra vez los artefactos y la propiedad S3, resolver la
red por nombre con metadata estructurada y ejecutar el runtime Pages/workerd únicamente dentro
de la red interna ya creada. Reutiliza los volúmenes de dependencias montados read-only; no repite
bootstrap ni usa egress. La continuación no inicia Edge, Postgres, PostgREST ni SQL.
