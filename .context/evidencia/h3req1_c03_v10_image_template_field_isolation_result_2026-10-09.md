# Resultado V10 — aislamiento de campos y probes sintéticos

Fecha: 2026-10-09. Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Autorización e invocación

- JIT `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-IMAGE-TEMPLATE-FIELD-ISOLATION-V10-ONCE-20261009-V1`,
  SHA-256 `08ced8865cffae2c46319897c98d368f45621dbe6650ff445ab701d55f546d7c`.
- Autorizada una invocación; ejecutada como `romel` no-root en Ubuntu WSL interactiva,
  `require_escalated`, sin `sudo`. El dispatcher validó el SHA del wrapper y usó Bash y timeout
  fijados por el JIT.
- Exit del runner: **0**. Se conserva únicamente salida `phase/error_code` allowlisted; no se
  guardaron stderr, metadata cruda ni secretos.

## Resultado sanitizado

```text
phase=prior-endpoint-attestation|error_code=OK
phase=image-id-isolated|error_code=OK
phase=classifier-v8-focused-tests|error_code=OK
phase=image-volumes-isolated|error_code=OK
phase=synthetic-image-read|error_code=OK
phase=probe-container-start|error_code=OK
phase=template-probe-id|error_code=OK
phase=template-probe-name|error_code=OK
phase=template-probe-state-status|error_code=OK
phase=template-probe-state-exit-code|error_code=OK
phase=template-probe-state-oom-killed|error_code=OK
phase=template-probe-label-jit|error_code=OK
phase=template-probe-label-manifest|error_code=OK
phase=template-probe-label-run|error_code=OK
phase=template-probe-network-mode|error_code=OK
phase=template-probe-readonly-rootfs|error_code=OK
phase=template-probe-user|error_code=OK
phase=template-probe-cap-drop|error_code=OK
phase=template-probe-security-opt|error_code=OK
phase=template-probe-memory|error_code=OK
phase=template-probe-memory-swap|error_code=OK
phase=template-probe-nano-cpus|error_code=OK
phase=template-probe-pids-limit|error_code=OK
phase=template-probe-restart-policy|error_code=OK
phase=template-probe-tmpfs-snapshot|error_code=OK
phase=template-probe-tmpfs-count|error_code=OK
phase=template-probe-log-config|error_code=OK
phase=template-probe-port-bindings|error_code=OK
phase=template-probe-shm-size|error_code=OK
phase=template-probe-binds|error_code=OK
phase=template-probe-mounts|error_code=OK
phase=probe-summary|error_code=ALL_FIELDS_OK
phase=probe-container-cleanup|error_code=OK
```

`classifier-v8-focused-tests` representa el bloque focal exacto del JIT (5 casos V8, 9 V9 y
3 V10: **17/17**, sin skips). La inspección sintética separó `{{.Id}}` y
`{{json .Config.Volumes}}`; ambos valores cumplieron los predicados fijados. El contenedor de
probes completó las 25 expresiones del allowlist y su cleanup pasó.

## Alcance acreditado y gate siguiente

El resultado acredita únicamente la herramienta de lectura y las expresiones sintéticas bajo
este corte. No leyó F1, no ejecutó r9, no inspeccionó `studiamatch-dev` y no hizo pull, build,
install, retry ni cambios Docker. No acredita copia íntegra, arranque Pages/workerd, healthz,
Edge/PG17/PostgREST, C03 integrado, checks finales, UAT 144 ejecuciones/capturas ni onboarding
10/10. Esos gates no avanzan por este PASS parcial y G01–G10 permanece 20%.

La siguiente operación de lectura F1/r9 requiere una autorización agrupada propia: los JITs
one-shot anteriores se consumieron y V10 excluye ambas fases. La preparación del paquete
posterior debe reutilizar la evidencia V10 y no repetir su suite ni sus probes.
