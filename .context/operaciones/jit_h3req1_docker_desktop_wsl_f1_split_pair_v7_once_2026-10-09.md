# JIT H3REQ1 C03 — separación mínima NanoCpus/Mounts, una lectura F1

Fecha: 2026-10-09. Estado: preparado; requiere aprobación humana específica.

## Evidencia y corrección acotada

V14 reprodujo que 25 expresiones inspeccionadas individualmente pasan y que el formato
completo falla. La reducción sintética V15 ya acreditó el conjunto 1-minimal
`NanoCpus` + `HostConfig.Mounts`. No atribuye el resultado al producto ni a Docker Desktop.
La autorización V15 TTY V2 SHA-256
`49243bda140af6038d3e93ed9a2d4d8b19b2206c54a7ac4648f2ab93d5904703` se consumió después
con `PHASE_ORDER_MISMATCH`, antes de F1/r9. La evidencia previa de la reducción se conserva;
no se repiten esos probes.

La modificación V7 conserva juntas las otras 23 expresiones; consulta `NanoCpus` y
`HostConfig.Mounts` por separado y recompone los 25 campos en el orden original solo en
memoria. Rechaza formato, longitud, caracteres de separación/controles y salida fuera del
límite. El parser existente sigue determinando si F1 satisface su política completa.
Las pruebas locales pasan 4/4: composición completa, mapas presentes/ausentes, fallos
cerrados y restauración del formato tras éxito/error. La salida-contract V15 V3 pasa 7/7;
corrige únicamente el prefijo imposible de fases.

## Solicitud concreta, ejecutor y límite

Solicito autorizar una invocación del comando exacto:

```bash
/usr/bin/timeout --foreground --signal=TERM --kill-after=10s 660s /bin/bash /home/romel/src/studiamatch-h3req1-sync-20261002/tests/h3req1_docker_peer_substep_diag/run_wsl_f1_split_pair_v7_once.sh
```

Ejecutor: Codex en Ubuntu WSL con Docker Desktop WSL integration, como `romel` no-root,
con PTY interactivo y sin `sudo`. La invocación debe ejecutarse con `tty=true`; de no
haber TTY, el preflight detiene la ejecución. Una sola llamada, sin retry. Cualquier
FAIL, preflight rechazado o timeout consume la autorización y detiene las fases posteriores.

La secuencia condicional es:

1. Validar rama/HEAD, pines, y la evidencia ya acreditada de endpoint Docker Desktop.
2. Reejecutar los sintéticos V5/V6 fijados, cuatro casos unitarios V7 en un contenedor
   efímero read-only y dos smokes efímeros de la imagen sintética fijada, con mapa de
   política presente y ausente. Solo se proyectan fase y código.
3. Solo con esos PASS, leer una vez el snapshot F1 previamente allowlisted. La
   clasificación hace tres llamadas `docker inspect` de solo lectura al mismo ID
   histórico: las 23 expresiones restantes juntas y las dos expresiones aisladas. No
   consulta `studiamatch-dev` como contenedor ni imprime/persiste metadata.

La única secuencia de éxito aceptada es:

```text
phase=prior-desktop-wsl-endpoint-attestation|error_code=OK
phase=classifier-synthetic-image-volumes-read|error_code=OK
phase=classifier-synthetic-image-read|error_code=OK
phase=classifier-synthetic-unit-tests|error_code=OK
phase=f1-template-synthetic-check|error_code=OK
phase=classifier-synthetic-tests|error_code=OK
phase=f1-image-read|error_code=OK
phase=f1-container-read|error_code=OK
exit=0
```

Las pruebas Docker sintéticas usan imagen local por digest, `--pull=never`,
`--network=none`, `--read-only`, usuario `1001:1001`, `--cap-drop=ALL`,
`no-new-privileges`, memoria 128 MiB, CPU 0.5 y 64 procesos. El runner los nombra con
un token aleatorio, registra IDs completos y ejecuta `docker stop` por esos IDs; cada
contenedor tiene `--rm` y termina su proceso de prueba en 45 s. Si el host termina la
invocación abruptamente, el residual máximo previsto es el proceso sintético hasta ese
límite de 45 s; no se ejecuta limpieza por prefijo.

La única lectura F1 apunta al snapshot histórico C03 ya fijado en el clasificador, no al
contenedor habitual `studiamatch-dev`. El digest sintético local coincide con la imagen
asociada al entorno habitual; solo se consulta la imagen y se crean temporales aislados.
No inspecciona, inicia, detiene, renombra ni cambia `studiamatch-dev`.

No hay r9 en esta invocación. Su dispatcher vigente fija la imagen histórica cuyo
manifiesto de dependencias no coincide con los `package.json`/lock actuales; ejecutarlo
antes de reconstruir el runtime terminaría de forma previsible en el gate de dependencias.
Después del rebuild y health PASS se preparará el r9 contra el digest real del candidato.

No hay build, pull, instalación, acceso a DB, SQL, cambios de configuración Docker,
reconstrucción/cutover/limpieza histórica, archivos de credenciales, write remoto,
publicación CI, push/PR/merge ni deploy. Los temporales y salida cruda no se conservan;
la envoltura permite únicamente líneas sanitizadas `phase=…|error_code=…` y código de
salida. Cualquier fallo detiene esta invocación, sin repetir sintéticos ni F1.

## Pines y revisión

| Entrada | SHA-256 |
|---|---|
| `f1_read_failure_classification_v7_split_pair_once.py` | `331d2a99bfbae7d8bd470a0fc5ac91e74eb8af26f72e2b244ad4683d68d3b4ef` |
| `test_f1_read_failure_classification_v7_split_pair.py` | `c357175e1a72638db7ac494e5ef4ad86b4a4f107863cba49deb3692ee473fef2` |
| `classifier_synthetic_runner_v7_split_pair.py` | `0c0a106a3adfe8a471913ca649ef1af110952a44490f020d5644334e622f68b4` |
| V6 source classifier | `b17266a33559b16b28cdf1b619f9b5d7dae666203f6d9a357b046ed7ae809128` |
| V7 F1-only wrapper | `e1f69e465b0a3a08ea53d2e9ccc0414db94d37cf96c8620ff91531aa53c68a3e` |

Candidate: `/home/romel/src/studiamatch-h3req1-sync-20261002`, branch
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`,
WIP 55 tracked/239 untracked/0 staged. The V7 split-pair case set is the only correction
under review; no product, SQL/wire, BFF/HttpOnly, MFA, role, gateway, quota or secret
changes are part of this JIT.
