# G07 — diagnóstico TLS Edge Runtime R20–R24

## Identidad y alcance

- Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`.
- Rama `feat/h3req1-sync-20261002`; HEAD baseline
  `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- Alcance: fixture sintético local, Docker Desktop/WSL, sin credenciales reales,
  sin conexión a servicios externos y sin cambios al código funcional.
- El gateway devuelve deliberadamente HTTP 401 para el API key sintético. Ese
  código acredita que TLS llegó a HTTP; no es una prueba de Auth ni de invitación.

## Ensayos y causa aislada

| Ensayo | Exit del runner | Resultado relevante | Conclusión |
|---|---:|---|---|
| R20 | 1 | `docker cp` devolvió `container rootfs is marked read-only`; `probe=NOT_RUN`. | El runner intentó escribir código en un rootfs de solo lectura. No fue un fallo Edge ni Docker TLS. Los fixtures exactos se retiraron. |
| R21 | 1 | Gateway y Edge main listos; `TLS_UNKNOWN_ISSUER`; gateway Auth GET `0`. | `DENO_CERT` por sí solo no dio confianza efectiva al userWorker. |
| R22 | 0 | `main=TLS_UNKNOWN_ISSUER`, `userWorker=WORKER_START_FAILED`, `cert_env=MATCH`, `cert_file=READABLE`; GET `0`. | La variable y el archivo montado estaban presentes y legibles, pero el fetch del proceso Edge main no confió en esa CA. La creación del worker no llegó a una respuesta útil. |
| R23 | 1 | `TLS_UNKNOWN_ISSUER` con `DENO_TLS_CA_STORE=mozilla,system`; GET `0`. | Cambiar solo la lista de almacenes no bastó mientras la CA no estuviera en el bundle de sistema. |
| R24 | 0 | Bundle de sistema más CA sintética; `DENO_TLS_CA_STORE=system`, `SSL_CERT_FILE` y `DENO_CERT` apuntan al bundle; userWorker devolvió `HTTP_401`; Auth GET `1`, otras rutas `0`. | La CA se validó cuando el bundle se construyó dentro de `/tmp` del contenedor Edge y se seleccionó el almacén de sistema. TLS sigue validado; no se relajó la verificación. |

R20 diagnostic source injection se corrigió escribiendo por stdin solo en
directorios tmpfs del contenedor (`docker exec -i ... cat > ...`). El archivo de
CA de cada ensayo quedó archivado antes de retirar únicamente sus contenedores,
red interna y volumen etiquetados. Las redes fueron internas; no hubo pull,
build, instalación ni acceso a `studiamatch-dev`.

## Evidencia

- R20: [resultado](h3req1_c03_edge_transport_probe_r20_2026-10-10.txt), SHA-256
  `9e7b5e4ecac99e0107d8bf6b14e1c59988d98e4358d103bb8bb5880442997ee2`.
- R21: [resultado](h3req1_c03_edge_transport_probe_r21_2026-10-10.txt), SHA-256
  `30def8b9599875b66cbaeb72dad3a2c30f19d7f17690c7d5b98e42af0c2f48b5`; CA
  pública `h3req1_c03_edge_transport_ca_r21_2026-10-10.pem`, SHA-256
  `6f399af92d84ca0f33406305321c538ebedad1adc5a45ed88c3e7dc664e31c02`.
- R22: [resultado](h3req1_c03_edge_transport_probe_r22_2026-10-10.txt), SHA-256
  `92c0261cb695ed98b146c56ac4db0a8c2cdc0d6212267f49737c1cc630278a55`.
- R23: [resultado](h3req1_c03_edge_transport_probe_r23_2026-10-10.txt), SHA-256
  `9af80236e422ebbe76ffb0d1ccb7068a629c7849944e79eba88ee726afb0bab0`; CA
  pública `h3req1_c03_edge_transport_ca_r23_2026-10-10.pem`, SHA-256
  `e7d9a51936501b9e16b52723f76048ce4fb0ebe6da627519ffbd6cc2184b9ddc`.
- R24: [resultado](h3req1_c03_edge_transport_probe_r24_2026-10-10.txt), SHA-256
  `40cad2cd4e47097417d0d586138a68db2af7f3fff993d6a934a96cfea636a71f`; CA
  pública `h3req1_c03_edge_transport_ca_r24_2026-10-10.pem`, SHA-256
  `a020d56fafb63b844fcaaa64acfbe9d1ff6afb48f5a79778793db2bbebb6833b`.
  Bundle generado en el contenedor, SHA-256
  `4f395773ab082e6f352655ddbfdefb6508bcb3e98dca3e7aa3db370a9d56daf8`.

La evidencia verifica transporte sintético de un userWorker y la ruta GET Auth.
No acredita el Edge Admin real, reserva, PostgREST integrado ni C03 completo.

## Ajuste del runner C03

Se prepara R20 con estos cambios acotados respecto al driver R19:

1. el shell del contenedor Edge concatena `/etc/ssl/certs/ca-certificates.crt`
   y la CA sintética montada en un bundle dentro de `/tmp` tmpfs;
2. comprueba que el bundle existe antes de arrancar Edge Runtime;
3. fija `DENO_TLS_CA_STORE=system`, `DENO_CERT=/tmp/ca-bundle.pem` y
   `SSL_CERT_FILE=/tmp/ca-bundle.pem`;
4. verifica y registra solo el SHA-256 del bundle, sin imprimir su contenido;
5. conserva imágenes, snapshots y cachés fijados, las redes internas y el
   cleanup por identidad/labels del run.

Manifiesto R20: 71 entradas, SHA-256
`fcccd29bf59bff816bd06d786144e09dabeedf67c165f5422f71a7d377ecb721`;
`sha256sum -c` pasó. `bash -n`, `node --check` y ShellCheck 0.11.0 con nivel
`warning` pasaron para el runner R20. La revisión del delta R19→R20 encontró
solo nombres/resultado/contrato R20 y la preparación del bundle TLS descrita.

## Gate y recuperación

G07 sigue parcial hasta que el driver integrado R20 acredite los flujos C03
completos. No se suma un punto por este diagnóstico. El siguiente comando local
autorizado es:

```bash
bash tests/h3req1_c03_integrated_drill_r20.sh --jit H3-CLOSE-03-INTEGRATED-2026-10-10-R20 --manifest-sha256 fcccd29bf59bff816bd06d786144e09dabeedf67c165f5422f71a7d377ecb721
```

Se detiene ante el primer fallo, preserva el resultado sanitizado y no repite
ninguna etapa intacta. El checkout original permanece intacto.
