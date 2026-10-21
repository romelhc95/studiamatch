# Inventario de redes R17 antes de liberación selectiva

Log sanitizado R17: `h3req1_c03_integrated_run_2026-10-10_r17.log`, SHA-256
`811ebc5d4c53336d0bf55ae7e5dab3ade6e094b609b7a13b9aa7df71ee78e576`.
Manifiesto R17: `h3req1_c03_integrated_manifest_r17.sha256`, SHA-256
`6532388df6a09dd7dfd2359cc9979ad6666d1fec8b1f5c9dc1d2a567437f6105`.

Se consultó solo metadata estructurada de las dos redes creadas por el nonce R17. Ambas son
`Internal=true`, tienen `attached=0`, y sus ID/nombre/JIT/manifiesto/nonce coinciden con la
ejecución fallida. No tienen mounts, volúmenes ni almacenamiento de datos.

| Nombre | ID inmutable | JIT | Adjuntos |
|---|---|---|---:|
| `h3req1-c03-integrated-edge-20261010-r17` | `9d944b05256a6f84e6d080119450995572ad8a8da95ebd8739cad446100af126` | `H3-CLOSE-03-INTEGRATED-2026-10-10-R17` | 0 |
| `h3req1-c03-integrated-data-20261010-r17` | `9dd4a81a17a6712bbc7e42dee6da66aa0de2d37a05be9488b34762efae791615` | `H3-CLOSE-03-INTEGRATED-2026-10-10-R17` | 0 |

Tras preservar esta evidencia, se retiraron únicamente esos dos IDs con revalidación exacta.
Postcondición: cero redes con etiqueta `com.studiamatch.h3.c03.jit`. Los contenedores, volúmenes
de snapshot/TLS, imágenes y el checkout permanecen preservados; no se usa prune.
