# H3REQ1 C03 — diagnóstico mínimo de interacciones Tmpfs (V8)

Fecha: 2026-10-09. Estado: preparado; requiere autorización humana nueva. No reutiliza
autorizaciones V7, V14 o V15 consumidas.

## Bloqueo que aborda

V14 conserva evidencia de 25 expresiones individuales correctas y un render combinado
fallido. V15 acreditó el par independiente `{NanoCpus, HostConfig.Mounts}`. V7 separó ese
par y volvió a fallar al renderizar el resto de 23 expresiones con
`INSPECT_TEMPLATE_TMPFS_EVALUATION_ERROR`; no leyó F1 ni ejecutó r9. V8 no repite el template
completo: acota hasta 56 consultas al campo Tmpfs (índices 18 y 19) frente a las otras 21
expresiones del residual. Revalida dos singletons, busca en hasta 43 pares y confirma el
singleton contraparte del primer fallo para acreditar 1-minimalidad.

## Solicitud concreta

Autorizar **una invocación** de este comando exacto en Ubuntu WSL interactiva como `romel`
no-root, sin `sudo`:

```bash
/usr/bin/timeout --foreground --signal=TERM --kill-after=10s 900s /bin/bash /home/romel/src/studiamatch-h3req1-sync-20261002/tests/h3req1_docker_peer_substep_diag/v8_tmpfs_pair/run_wsl_f1_tmpfs_pair_diagnostic_v8_once.sh
```

Runner SHA-256:
`ad4214a2f2998c486e1aa5c3d01478e4389f9f0cf162cb20670e57975904c14e`.

Helper SHA-256:
`bf99e3414c6aad157371ad2decdb338a9f07c5587d422d41a0e13ed17147f121`.

Pruebas focales SHA-256:
`b9050f5d2f960beb0a25b0fd239f6e717cf5fe0061c747256255e8bdad51dfdd`.

## Alcance, entradas y límites

- Fija la rama `feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`,
  los helpers V6/V7, atestación previa de endpoint y la imagen sintética por digest
  `sha256:29d8fff9a799aaacd45d771696f40762511d4c3a4c1ebfe536bd2a69a2f16be0`.
- Lee endpoint Docker Desktop por el socket local; no cambia contexto ni configuración.
- Lee solo la imagen sintética fijada, inicia como máximo dos contenedores desechables con
  `--pull=never`, `--network=none`, rootfs de solo lectura, UID/GID 1001, caps vacías,
  `no-new-privileges`, memory/swap 128 MiB, CPU 0.5 y PIDs 64. El contenedor “present” incluye
  las tres etiquetas sintéticas y un tmpfs; “absent” omite ambas clases de mapa.
- Límite de 56 `docker inspect --type container`: dos campos Tmpfs individuales, hasta 43
  pares que incluyen al menos un campo Tmpfs, una confirmación singleton de contraparte al
  primer fallo y diez lecturas para la proyección segmentada presente/ausente. Se añade una
  sola `docker image inspect` del digest sintético. Cada
  lectura tiene timeout de diez segundos; inicio/parada de cada contenedor, 20 segundos;
  timeout global, 900 segundos. Sin retry ni pull/build.
- Salida limitada a 8192 bytes y líneas `phase=…|error_code=…`; stderr/output crudos se
  descartan. Nunca imprime valores de configuración ni metadata del daemon.
- No inspecciona ni contacta el contenedor/imagen F1, no ejecuta r9, no usa credenciales,
  `.env.local`, DB, SQL, GitHub, Cloudflare ni el servicio `studiamatch-dev`.

## Orden y condiciones

1. Revalidar TTY, UID, WSL, rama/HEAD, pines de fuentes, imagen sintética y endpoint. Cualquier
   mismatch detiene antes de crear contenedores.
2. Ejecutar cuatro pruebas puras locales fijadas. Solo marcador exacto `4/4` permite continuar.
3. Crear contenedor sintético aislado “present”. Revalidar por separado los dos campos Tmpfs;
   ante un fallo singleton, detener la reducción.
4. Buscar en el matrix de hasta 43 pares acotados y parar en el primer fallo. Registrar solo
   sus índices estáticos y código cerrado; revalidar el singleton de la contraparte para
   acreditar que el par es 1-minimal. No se expanden a otros campos.
5. Revalidar el proyector segmentado que separa `{NanoCpus, Tmpfs snapshot, Tmpfs count,
   Mounts}` del bloque restante. Debe componer exactamente 25 campos en el fixture “present”.
6. Detener el contenedor por ID exacto. Crear “absent”; la misma proyección debe preservar
   mapas vacíos y hacer fallar el parser de política cerrada. Detener por ID exacto.
7. Si el matrix identifica un par y las dos composiciones pasan, reportar la
   interacción y el split probado. Si no falla ningún par, reportar
   `HIGHER_ORDER_OR_ORDER_INTERACTION`, exit 2; no atribuir causa ni avanzar a F1/r9.
8. Ante error, detener una vez los IDs sintéticos conocidos; el script incluye `--rm` y
   salida automática del proceso a los 120 segundos como última limpieza acotada. No reintentar.

## Gate de decisión

Solo un resultado que incluya singletons `OK`, una pareja mínima con código cerrado,
`segmented-present|OK`, `segmented-absent|OK` y `tmpfs-diagnostic|PAIRWISE_SET_ISOLATED`,
exit 0 permite implementar la segmentación mínima identificada y preparar un JIT posterior
para validación F1/r9. Este paquete no autoriza esa lectura ni r9.

La ejecución no suma puntos G01–G10 por sí sola. No declara PASS de tooling, F1, integración
ni aceptación.
