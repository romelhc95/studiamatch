# Inventario selectivo de recursos C03 R37

R37 falló en H3S12 durante la aserción previa a finalizar Auth. Log sanitizado
`h3req1_c03_integrated_run_2026-10-10_r37.txt`, SHA-256
`f5b4e9b7f099aa21dad4b73da6fa408c424bf0742548fc955b5bba691c96a3c8`. Los siete
contenedores están detenidos, etiquetados con JIT R37 y nonce
`1747431-1791656179087104238-2086-27679`; PGDATA fue tmpfs, los mounts del
candidato/dependencias read-only, excepto TLS sintético. Se conservan volúmenes
de snapshot, TLS y dependencias.

IDs exactos: Edge suspended `8706be880b8aaf249a0c636f33e170cf44a44809b6e62b087c003ef509c0dd50`; Edge active `37eec86e92046992cde54271c0b878477f7407fd558c12315dc186f7912d17f1`; PostgREST `983e26f5a2a5af5f01ab6bd58d714bfdbf2e68acf8d16ff7ddc0ab62b0c253b2`; PG17 `abe112a3c38f2b0092f34d391bf75cf3f9d77e1da5056e3c77846792f24c4dd5`; Pages/workerd `02b1f4af2f66181afd35018bde12d0c8228ea6cb0e76a2f1b742dae0f40cdb15`; cache verifier `d3d99449073ae566d8808573da8ce8deb47cbd70e6acee636790b26c8e14c594`; snapshot producer `2b4526ba8e6b96bfc254ae93ab1923078effcf46a7c84115b0069a072291d12c`.

Red data interna vacía: `h3req1-c03-integrated-data-20261010-r37`, ID
`76c15253ff520e3fd5a68a86cdd493eb49155939d6816e5740dfd3bb3e1996ae`.
Red edge interna vacía: `h3req1-c03-integrated-edge-20261010-r37`, ID
`94fec21d34b3c517288aefc576ffbd18fa2f7de19e4b0d1e318f70e198f1dcc5`. Ambas
tenían cero adjuntos. La limpieza se limita a estos siete IDs y dos redes; `docker rm`
sin `-v`. Sin prune ni modificación de imágenes, volúmenes o `studiamatch-dev`.
