# C03 R39 — inventario y retirada selectiva de recursos

Se preservó primero el log sanitizado R39; su SHA-256 es
`b526908cd89b0b30c440ac184a795a14c23244f31a264258f7b0f39c30ac79d3`.
Los siete contenedores mostraron el mismo JIT R39, manifiesto
`703129159e15e1a3…`, estado `exited` y ninguno requirió leer Env. `studiamatch-dev`
estaba `running/healthy` con `studiamatch-h3req1:20261009-v3` y quedó fuera del
inventario removible.

| Recurso | ID completo | Estado | Función / mounts | Resultado |
|---|---|---|---|---|
| `h3req1-c03-integrated-edge-suspended-20261010-r39` | `9dc1ccc635e11101c47589b522717005c3092313c5b53d994a9ae11b466dacba` | exited 15 | Edge Runtime; snapshot, cache Deno, TLS sintético y node_modules read-only | retirado por ID exacto, sin `-v` |
| `h3req1-c03-integrated-edge-active-20261010-r39` | `c4ec3d1246578be4af2c0232bc591d44a3546f4bcb26bbfeaa711e4c3189e3e7` | exited 15 | Edge Runtime; mismos mounts read-only | retirado por ID exacto, sin `-v` |
| `h3req1-c03-integrated-postgrest-20261010-r39` | `58122e420244d6c2c6622555ac704104ba9d19b4c46f057b5ee91054ec35b409` | exited 255 | PostgREST fijado | retirado por ID exacto, sin `-v` |
| `h3req1-c03-integrated-pg17-20261010-r39` | `0bf50efc52c3f2683b33471a05b63513117b5ae141ba96c9a4513717c5f2aa97` | exited 0 | PostgreSQL 17.11; snapshot read-only; PGDATA tmpfs | retirado por ID exacto, sin `-v` |
| `h3req1-c03-integrated-runtime-20261010-r39` | `f77b44ba6e5eea9400e4a8f7b50cd3370ae1a909a7e2f712a1add648e0cadfb8` | exited 143 | Driver Pages/workerd + control; snapshot/cache/tools read-only, TLS tmpfs | retirado por ID exacto, sin `-v` |
| `h3req1-c03-dependency-cache-verify-20261010-r39` | `caeb8f0ccbffbc1b0912b2e6984d59bc66abe0e9c248398c0c65ca7826c66d2b` | exited 0 | Verificación de dependencias; mounts read-only | retirado por ID exacto, sin `-v` |
| `h3req1-c03-source-snapshot-20261010-r39` | `77e908a162cfaf9375a2ddf924859befd05866e737080732801720326eb10d7c` | exited 0 | Productor de snapshot; snapshot volume RW durante producción | retirado por ID exacto, sin `-v` |

Redes internas sin contenedores adjuntos, verificadas antes de retirada:

- `h3req1-c03-integrated-edge-20261010-r39`, ID
  `6b154205dbcfe00addfc13b8d94dd470d0bb534c6cb8faaab3bd6af6a3b421e6`.
- `h3req1-c03-integrated-data-20261010-r39`, ID
  `00bef50ee7aee399db899118ad80e4ac2fc1a14ae6aa68da3fe3a2a3e5993637`.

Solo se retiraron los siete contenedores anteriores y esas dos redes internas
vacías. No se eliminaron volúmenes, imágenes, datos persistentes, fuentes,
recursos históricos, `studiamatch-dev` ni recursos del checkout original. Los
volúmenes de snapshot, TLS sintético y caches se conservan para preservar evidencia.
