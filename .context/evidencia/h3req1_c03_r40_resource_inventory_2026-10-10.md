# C03 R40 — inventario y retirada selectiva de recursos

Log sanitizado R40 preservado, SHA-256
`76f9b2a975cff439d69893c71c7c3c85482ad378558edb8cb58e83d68a03871a`.
Run nonce `1758324-1791656874529748865-17642-31688`, JIT
`H3-CLOSE-03-INTEGRATED-2026-10-10-R40`, manifiesto
`7233b21cc615ff6427e043fdae11cd97b61ebffe8c39a92f11f769c28fbb4799`.
Los siete contenedores estaban detenidos y tenían esas mismas etiquetas. No se
leyeron Env ni objetos inspect completos. `studiamatch-dev` permaneció healthy y
fuera de los recursos de limpieza.

| Recurso | ID | Estado/función | Mounts de volumen relevantes | Resultado |
|---|---|---|---|---|
| Edge suspended R40 | `d8c4140910e9868746fbebf0a709521768929067d77670bac2e5434a5b0c08d4` | exited 15, Edge Runtime | snapshot/cache/TLS/node_modules read-only | retirado por ID exacto, sin `-v` |
| Edge active R40 | `e2a1d5d488375f6af6547486f15279203f266c609454423631f56599dd09156d` | exited 15, Edge Runtime | snapshot/cache/TLS/node_modules read-only | retirado por ID exacto, sin `-v` |
| PostgREST R40 | `675bf0313116aa39b260a582c52b474aa7a26240865d1918381905acc9445746` | exited 255, PostgREST fijado | ninguno | retirado por ID exacto, sin `-v` |
| PG17 R40 | `b504be954d79277c436bfbac4ee2cfa5d4c8abcb99d777e71263b37a18d9d4d7` | exited 0, PostgreSQL 17.11; PGDATA tmpfs | snapshot read-only | retirado por ID exacto, sin `-v` |
| Runtime R40 | `6c975b3956bb68de90c7dbca4a16fc644a14ffa8b05467057854f9728f8c7e58` | exited 143, Pages/workerd driver | snapshot/cache/tools read-only; TLS tmpfs | retirado por ID exacto, sin `-v` |
| Cache verifier R40 | `2f52e7ac6bcfe5b4075067b2f0022fa074863b59cb89e8440bed84c4e1dce367` | exited 0, verificación de dependencias | caches/snapshot read-only | retirado por ID exacto, sin `-v` |
| Snapshot producer R40 | `376561c27941eddd869202c73f406c5e7133595d26014b8f3332c484e03ea7a9` | exited 0, productor de snapshot | snapshot RW durante la producción | retirado por ID exacto, sin `-v` |

Redes internas vacías, IDs confirmados y retirados: `h3req1-c03-integrated-edge-20261010-r40`
(`5cfb743ca7021c0488ee6b2dade155bdfb24d3f4a0cf5fdf5e5eb85a9edca0cf`) y
`h3req1-c03-integrated-data-20261010-r40`
(`54d99061d3c2f20b50cf9397fca97e636ad0e47850a78c1e24f183b9f9aa53d2`).

Solo se retiraron esos siete contenedores detenidos y las dos redes internas sin
adjuntos. Los volúmenes R40 de snapshot, TLS sintético y caches compartidos de
dependencias, las imágenes, fuentes, recursos históricos, datos ajenos,
`studiamatch-dev` y el checkout original se conservaron.
