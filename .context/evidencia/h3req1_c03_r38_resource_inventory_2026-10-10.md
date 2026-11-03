# Inventario selectivo de recursos C03 R38

R38 pasó SQL suspendido, finalizer in-flight, safe-resume y aserciones recuperadas;
falló `/control/recovery` con `AssertionError`. Log sanitizado
`h3req1_c03_integrated_run_2026-10-10_r38.txt`, SHA-256
`5bbd56dedf647ca7f391ef792b466f8cfdd8bb7b2ddc97bc65729178e5c6beee`. Siete
contenedores estaban `exited`, con JIT R38 y nonce
`1750127-1791656299886349120-31603-3506`; PGDATA fue tmpfs, candidato/cachés
read-only salvo certificado TLS sintético. Se retienen los volúmenes de
snapshot, TLS y dependencias.

IDs exactos: Edge suspended `e092e10b45572f911a7329260b396b367379484ab5f7d0dd7c5f3d9509304e65`; Edge active `0b9b129c6b1e9dcba43fe8772a148b1bbe9c87436f8f2ff2825bf4e4581113e9`; PostgREST `31a5f15bc0fa9794dc2c71ab74b928ccbd53cf60190f2c35c9eeaf462a377464`; PG17 `d09f3f51eeb13c9ce73ce3dd28c55e58b20f89b855681e9735ccf52a97642917`; Pages/workerd `5979fcd09f7b793cd084dc8acc20fa41128b4551f6518280c62acf1620378f41`; cache verifier `51158711f50223b6140eb84f30420587a43b5a2a667227631ffc5c3ff53aa0f2`; snapshot producer `cfe3dcd26793611879d01bdc6b6501a86d516abe44f560840afb3199764161d4`.

Red data interna vacía `h3req1-c03-integrated-data-20261010-r38`, ID
`5a2f3393df72427415cd746eacfbd580bf72a5fa631d3e733fdfc135a4e34dc9`; red Edge
interna vacía `h3req1-c03-integrated-edge-20261010-r38`, ID
`def70b513e818a2b799d51391322a4ecdeefe05d630468847a280faf10da1742`. Ambas
tenían cero adjuntos. La retirada se limita a estos IDs y redes, `docker rm` sin
`-v`; no se eliminan volúmenes/imágenes ni se toca `studiamatch-dev`.
