# C03 R41 — inventario y retirada selectiva de recursos

Log sanitizado preservado, SHA-256
`eaa8e006c497401d77c9f2f0fb814e565fc347c6e7a5a47086adefdadc1479c7`.
Run nonce `1761832-1791657067581783595-31358-22059`, JIT
`H3-CLOSE-03-INTEGRATED-2026-10-10-R41`, manifiesto
`c8d2f656b7cfb726ea907d336ca92dd55bef602fcda4245304b56c700fbcf4a4`.
Los siete contenedores estaban detenidos y las redes internas vacías, todos con
las etiquetas indicadas. `studiamatch-dev` quedó fuera del inventario.

| Recurso | ID | Estado/función | Mounts de volumen | Retirada |
|---|---|---|---|---|
| Edge suspended R41 | `ce1cf55151780bc3989583e9609f3decac81ef256315f3ff59d7412d408fb1ea` | exited 15, Edge Runtime | snapshot/cache/TLS/node_modules read-only | ID exacto, sin `-v` |
| Edge active R41 | `94a4b0de1fdf90a19b6fa7069431c6898b366a8b62203353550c46f1d26cb350` | exited 15, Edge Runtime | snapshot/cache/TLS/node_modules read-only | ID exacto, sin `-v` |
| PostgREST R41 | `44d023a18316948389b20159d26a46cb52d8f60b1cf136789b9b2fd9f67cf8fb` | exited 255, PostgREST fijado | ninguno | ID exacto, sin `-v` |
| PG17 R41 | `2356e513497f0be83c9d63f996a298bf025a8422acdcbc87b38b02d1cf5e3a5e` | exited 0, PG17.11; PGDATA tmpfs | snapshot read-only | ID exacto, sin `-v` |
| Runtime R41 | `36af157ea86d688a04157736cf3a290091cfc55dbdfe6fd434043d7a0a9c774a` | exited 143, Pages/workerd driver | snapshot/cache/tools read-only; TLS tmpfs | ID exacto, sin `-v` |
| Cache verifier R41 | `e27668c7287670121c6845901fd26b2e4b2298532b0aa2dd2d003aaf980f6667` | exited 0, cache verifier | caches/source read-only | ID exacto, sin `-v` |
| Snapshot producer R41 | `b729060fa2b88c7307d81afdc40d2b5c6bb2baf5097153b17963a4f61d88b564` | exited 0, snapshot producer | snapshot RW al producir | ID exacto, sin `-v` |

Redes internas vacías retiradas: edge
`h3req1-c03-integrated-edge-20261010-r41`
(`6e6ee747c94a302b98de8fe04c85b4641b4ec06774c852ad66ec659d605ebf56`) y data
`h3req1-c03-integrated-data-20261010-r41`
(`dc5a7eae26d8a5d94bdd2c993b8663274ae46c4e1fb260108ef05ee3d2e28c5f`).

No se retiraron volúmenes, imágenes, fuentes, recursos históricos, cuentas,
datos ajenos, `studiamatch-dev` ni el checkout original.
