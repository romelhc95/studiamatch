# Resultado V14 — campos aislados pasan; template combinado falla

Fecha: 2026-10-09. Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Autorización consumida

- JIT `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-V14-OUTPUT-CAPTURE-AND-R9-ONCE-20261009-V1`,
  SHA-256 `60ba16f2b29919ef89869625360416cb87470a7e4ad374f7c1d4b763d9686f48`.
- Una invocación autorizada, ejecutada con `require_escalated` como `romel` no-root en Ubuntu
  WSL interactiva, sin `sudo`. El runner y helper V14 tenían SHA-256
  `9b87fc79cfa93e5515fb0e0746bbcbe947df070961c32b1c47ef83ec619259aa` y
  `776d56c87101f5f4b632f7dd58fddc3405f591cfcd756343741ce4095a47ce29`.
- La autorización V14 queda consumida. No hay retry.

## Salida sanitizada completa

```text
phase=prior-v13-output-capture|error_code=OK
phase=prior-v12-failure|error_code=OK
phase=classifier-v13-null|error_code=OK
phase=classifier-v13-empty-object|error_code=OK
phase=classifier-v13-unrelated-label|error_code=OK
phase=classifier-v13-target-label-1|error_code=OK
phase=classifier-v13-target-label-2|error_code=OK
phase=classifier-v13-target-label-3|error_code=OK
phase=classifier-v13-malformed-json|error_code=OK
phase=prior-v11-failure|error_code=OK
phase=prior-v10-evidence|error_code=OK
phase=prior-endpoint-attestation|error_code=OK
phase=prior-v13-container-audit|error_code=OK
phase=f1-template-synthetic-label-map|error_code=OK
phase=f1-template-present-inspect|error_code=INSPECT_TEMPLATE_EVALUATION_ERROR
phase=f1-template-present-probe-id|error_code=OK
phase=f1-template-present-probe-name|error_code=OK
phase=f1-template-present-probe-state-status|error_code=OK
phase=f1-template-present-probe-state-exit-code|error_code=OK
phase=f1-template-present-probe-state-oom-killed|error_code=OK
phase=f1-template-present-probe-label-jit|error_code=OK
phase=f1-template-present-probe-label-manifest|error_code=OK
phase=f1-template-present-probe-label-run|error_code=OK
phase=f1-template-present-probe-network-mode|error_code=OK
phase=f1-template-present-probe-readonly-rootfs|error_code=OK
phase=f1-template-present-probe-user|error_code=OK
phase=f1-template-present-probe-cap-drop|error_code=OK
phase=f1-template-present-probe-security-opt|error_code=OK
phase=f1-template-present-probe-memory|error_code=OK
phase=f1-template-present-probe-memory-swap|error_code=OK
phase=f1-template-present-probe-nano-cpus|error_code=OK
phase=f1-template-present-probe-pids-limit|error_code=OK
phase=f1-template-present-probe-restart-policy|error_code=OK
phase=f1-template-present-probe-tmpfs-snapshot|error_code=OK
phase=f1-template-present-probe-tmpfs-count|error_code=OK
phase=f1-template-present-probe-log-config|error_code=OK
phase=f1-template-present-probe-port-bindings|error_code=OK
phase=f1-template-present-probe-shm-size|error_code=OK
phase=f1-template-present-probe-binds|error_code=OK
phase=f1-template-present-probe-mounts|error_code=OK
phase=f1-template-present-probe-summary|error_code=ALL_FIELDS_OK
phase=f1-template-present-summary|error_code=FIELD_INTERACTION_ERROR
exit=1
```

## Clasificación y alcance

El endpoint Docker Desktop WSL, las siete fixtures de clasificación V13, la auditoría read-only de
residuales con prefijo V12 y el mapa de labels sintético dieron `OK`. El smoke `present` falló al
evaluar el formato completo con `INSPECT_TEMPLATE_EVALUATION_ERROR`; sus 25 campos individuales
dieron `OK` (`ALL_FIELDS_OK`). El clasificador informa `FIELD_INTERACTION_ERROR`: queda
demostrado un fallo de interacción del formato combinado del smoke, no un defecto de Docker ni del
candidato de producto.

El runner detuvo el ciclo después del primer smoke. La inspección del segundo variant, ambas
lecturas F1 y r9 no se ejecutaron. La ruta de cleanup del contenedor temporal no emitió error; no
quedó un fallo de cleanup en la salida. No hubo acceso a `studiamatch-dev`, pull/build/install,
retry, cambios de configuración Docker, DB/SQL/Supabase ni operaciones remotas.

## Estado de gates

G01=10/10, G02=10/10, G03–G10=0/10; total **20%**, delta 0. D01–D14=0/14. Se conservan los
parciales sintéticos, sin sumarlos a controles de cierre. No hay `GO_LOCAL_PR` ni
`GO_DEVELOPMENT_REAL`. El siguiente cambio debe corregir solo el formato combinado sintético o su
clasificación, agregar la prueba enfocada faltante y recibir una autorización agrupada nueva para
una futura invocación Docker.
