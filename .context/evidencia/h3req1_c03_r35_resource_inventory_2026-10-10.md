# Inventario selectivo de recursos C03 R35

R35 falló en la aserción SQL de suspensión con `psql exit=3`; el log sanitizado
se preserva en `h3req1_c03_integrated_run_2026-10-10_r35.txt`, SHA-256
`3153b3fe12e0a9f1c88d1908f4298afc3f1cfa36bbe033caf10847c9ec0ab78f`. El runner
detuvo los cinco servicios exactos. PGDATA solo usó tmpfs. Los contenedores
estaban `exited`, etiquetados con JIT R35 y nonce
`1741841-1791655869577952016-15350-16698`; los mounts del candidato y cachés
eran read-only, excepto el volumen de certificado TLS sintético. El snapshot y
los certificados/cachés se conservan como volúmenes.

| Contenedor | ID | Estado | Imagen |
|---|---|---|---|
| Edge suspended | `05c242f58ab4894a9795b819a7c9c3a2fd8d6b7045521c0c52df9115e9e3e6bb` | exited 15 | Edge Runtime v1.74.3 fijada |
| Edge active | `c130b5261199af34e577d17ed7a0728a5d4b582e08b7fb9bd0f92f59adbd7b54` | exited 15 | Edge Runtime v1.74.3 fijada |
| PostgREST | `7fcd7b8bf8f4c4c0716b527c415a787f1f6cb59487eb5e23f9e13192127cbd65` | exited 255 | digest fijado |
| PG17 | `5b47678c1526b9d5c3ed9eb68817017e7757adb83f59b2235d8896c9471f74a4` | exited 0 | digest PostgreSQL 17.11 |
| Pages/workerd | `53f13be4c9b946dbb09f491539043b83dd158115133f0fa1144aed74e219790e` | exited 143 | digest Node fijado |
| cache verifier | `c40909fabca58867688aaa40273f4e4d11ec052276b491c468d8722029f72e20` | exited 0 | digest Node fijado |
| snapshot producer | `5d91f6e13e92af6f1a1bacfbd0b224642ee52320018bd7b91698b390fc97eff0` | exited 0 | digest Node fijado |

Red interna vacía `h3req1-c03-integrated-data-20261010-r35`, ID
`4ff3bebee10d1ff630223f9e192a302af3d5fefaefd7ac7246d2ff3a709cfa30`, y red
interna vacía `h3req1-c03-integrated-edge-20261010-r35`, ID
`3899a8062b2fc9444cfb83ef2cde64120a58b031224907656a261c2317f972f5`; ambas
tenían `internal=true` y cero adjuntos.

Tras registrar este inventario y el resultado, la limpieza se limita a estos
siete IDs y dos redes R35; se usa `docker rm` sin `-v`, y no se eliminan volúmenes,
imágenes, `studiamatch-dev` ni datos/fuentes del checkout.

Resultado: el preflight revalidó estado `exited`, JIT y nonce exactos, y cero
adjuntos en ambas redes internas. Se retiraron los siete contenedores y las dos
redes exactas, sin `-v`; `phase=selective-r35-cleanup|error_code=OK|containers=7|internal_networks=2|volumes_removed=0`.
