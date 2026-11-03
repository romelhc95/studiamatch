# Inventario selectivo de recursos C03 R36

R36 falló en la aserción SQL H3S11 (`psql exit=3`). Log sanitizado:
`.context/evidencia/h3req1_c03_integrated_run_2026-10-10_r36.txt`, SHA-256
`0ff2852831ea52f921d786311d408ef2c498e49ef2038e8de85db6412965310a`.
Los siete contenedores estaban `exited`, todos con JIT R36 y nonce
`1744718-1791656041051542308-30055-9464`. El candidato y caches estaban montados
read-only; PGDATA fue tmpfs. Solo el volumen TLS sintético fue escribible. Se
conservan volúmenes de snapshot, certificados y dependencias.

| Servicio | ID |
|---|---|
| Edge suspended | `8d9cadd503757589b71efc24e445650c1f8d546f7267f15b36c0ae08d8b01f45` |
| Edge active | `84081736cd5ef262f5f86f372fb9c4b18e8dab8855d6c83af91c5b841e6b23d6` |
| PostgREST | `d627d66c0edd991c8760bd87aeb603ab4c46a86b473d0762a9efd743cc66381f` |
| PG17 | `c632c3e3be4757dea93bba878c1c773c18c3093f30044a4db4eb941157aa1d81` |
| Pages/workerd | `d65322b26397022beccde1e39aec3c909b8f2cd5fe5d3e73e755c431c68b13a6` |
| Cache verifier | `6e4ffbda7743b83a804a365665d484d016e932a1013621308affae75f91cc8a7` |
| Snapshot producer | `551acb9f0e023413244c8d0d12e5e5d156ab365a75994a164b96a175013219b8` |

Red interna `h3req1-c03-integrated-data-20261010-r36`, ID
`0c9a7abd027df16b3a28fb6fa063739d03359bc0b1b5f301381ec938abaa7989`, y red
`h3req1-c03-integrated-edge-20261010-r36`, ID
`705ae8718b4508a6454e20cbff80203bd896d2e32ce0823c102b86607c184225`, ambas
`internal=true`, cero adjuntos.

La retirada selectiva, tras este registro, se limita a los siete IDs y dos redes
R36. No se borra con `-v`, no se retiran volúmenes/imágenes y no se altera el
contenedor de desarrollo ni el checkout original.
