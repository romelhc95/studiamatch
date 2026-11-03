# Inventario selectivo de recursos C03 R34

Fecha: 2026-10-10. Candidato: rama `feat/h3req1-sync-20261002`, baseline
`4eb4d877a50b012bb630a129bd0c74482c33be9c`. Uso: preservar el resultado del
fallo antes de liberar únicamente los contenedores y redes exactos de R34.

Resultado preservado: `.context/evidencia/h3req1_c03_integrated_run_2026-10-10_r34.txt`,
SHA-256 `d3b2b99af10bdffb3ce7d159dcd7cc9cc661347a4648752f47b32e9019134a64`.
R34 alcanzó los controles Pages/Edge y se detuvo en la aserción SQL de suspensión:
exit `3`, clasificación `UNCLASSIFIED`; el parser no reconoció el SQLSTATE. Sus
servicios estaban detenidos. Los contenedores usan etiquetas del JIT R34 y el mismo
nonce de ejecución, mounts de candidato en solo lectura salvo el volumen TLS sintético;
PG17 solo escribió en PGDATA tmpfs. No contienen datos operativos ni credenciales.

| Contenedor | ID | Estado | Imagen | Mounts relevantes |
|---|---|---|---|---|
| edge-suspended | `4037dcb36bd37d488b6f2ef19f8e15f3527e7efe5c148ad0405bc63382846cce` | exited 15 | `supabase/edge-runtime:v1.74.3_amd64` | candidato, Deno cache, TLS y node_modules read-only |
| edge-active | `6480e4748ef652219bf99ac6899c2a919ee4f08c6dccd2d38a9375e491f00e9b` | exited 15 | `supabase/edge-runtime:v1.74.3_amd64` | candidato, Deno cache, TLS y node_modules read-only |
| PostgREST | `e58b441f4003968128c7bf8784240bd10b6fa99e44de767a2e2e8d419810dc37` | exited 255 | `postgrest/postgrest` fijada por digest en R34 | sin mounts |
| PostgreSQL 17 | `7d06b88fe96b719b7df4dbc17c07c12cc9269ec48578d2f3eaf16a5cfaf74e09` | exited 0 | digest local PG 17.11 | candidato read-only; PGDATA tmpfs |
| Pages/workerd | `157bac4b41cb58044370af1c012e648bd994d22d73f2a69ef67e6cafbf829048` | exited 143 | imagen Node fijada en R34 | candidato/deps read-only; TLS sintético |
| cache verifier | `c4449d8005e4ba50f50cfe2f07f458f085fc8e5f93e80b53e8f5c5a219bbca96` | exited 0 | imagen Node fijada en R34 | snapshot/caches read-only |
| snapshot producer | `a522ee089174acb603af3de5c7542386be43c70070c2a876b75508d9de4d9c9b` | exited 0 | imagen Node fijada en R34 | escribió solo al volumen snapshot H3 |

Redes internas exactas `h3req1-c03-integrated-data-20261010-r34`
(`3c0fc2c6b6314aaa95dc1ba91c5ac38cd83ecbd3606f79cadb2f2fbd8908b6fb`) y
`h3req1-c03-integrated-edge-20261010-r34`
(`c890f9d35deedb5f83688d0c8f50528977a31b0c292cfa41f8fc2d2d971ee546`) estaban
`internal=true`, con cero adjuntos. Los volúmenes R34 de snapshot, certificados
sintéticos y cachés se conservan. `studiamatch-dev`, imágenes y checkout original
no se modifican.

La retirada autorizada se limita a esos siete IDs y dos redes. Se usa `docker rm`
sin `-v`, luego `docker network rm` de los dos nombres exactos; no se ejecutan
prune ni borrados globales.

Resultado ejecutado: preflight confirmó los siete IDs en estado `exited`, con el
JIT y nonce R34 exactos; ambas redes seguían internas y vacías. `docker rm` sin
`-v` retiró los siete contenedores y `docker network rm` retiró las dos redes.
Resultado sanitizado: `phase=selective-r34-cleanup|error_code=OK|containers=7|internal_networks=2|volumes_removed=0`.
No se tocó ningún volumen, imagen, servicio habitual o checkout.
