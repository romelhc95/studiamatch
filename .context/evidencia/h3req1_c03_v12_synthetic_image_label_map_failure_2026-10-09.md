# Resultado V12 — el mapa de labels de la imagen sintética no está vacío

Fecha: 2026-10-09. Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Autorización consumida

- JIT `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-V12-TEMPLATE-VARIANT-DIAGNOSTIC-AND-R9-ONCE-20261009-V1`, SHA-256
  `b06bd50b6bea6c63d0fcec63ffef6fc47527f506e13ca840777bfa652bce16cf`.
- El usuario aprobó una invocación. Se ejecutó una vez con `require_escalated`, como `romel`
  no-root en Ubuntu WSL interactiva, sin `sudo`. Runner SHA-256
  `a02b200efcf377da64bc13caa62136167811f31ac4fa4cf54ed81a4c7338f783`.
- Exit: **1**. Se conservó solo salida de fase/código y exit; no se guardó stdout crudo,
  stderr, contenido de labels, metadata ni secretos.

## Resultado sanitizado

```text
phase=prior-v11-failure|error_code=OK
phase=prior-v10-evidence|error_code=OK
phase=prior-endpoint-attestation|error_code=OK
phase=f1-template-synthetic-label-map|error_code=SYNTHETIC_IMAGE_LABELS_PRESENT
exit=1
```

El preflight confirmó que la imagen sintética fijada tiene un mapa `Config.Labels` no vacío.
No revela si contiene labels ajenos o alguno de los tres labels snapshot del fixture. El runner
se detuvo antes de crear contenedores sintéticos o ejecutar probes. **No leyó F1 ni ejecutó r9.**
La autorización V12 queda consumida.

## Límites observados y siguiente corrección

La discrepancia demostrada está únicamente en la precondición del mapa completo. Aún no se
conoce si la imagen hereda alguno de los tres labels snapshot que el smoke necesita variar.
La siguiente variante de preparación clasificará internamente el JSON de labels y exigirá que
esos tres labels concretos estén ausentes en la imagen; los demás labels no se mostrarán ni
registrarán. Después podrá crear la variante `absent` sin enviar ningún `--label`; `Config.Env`
solo aporta el marcador aleatorio de propiedad usado para verificar cleanup.

No se modificó Docker, no hubo pull/build/install/retry, no se creó ningún contenedor, no se
accedió a `studiamatch-dev`, DB, SQL, Supabase, Git remoto, GitHub ni Cloudflare. G01/G02 siguen
10/10, G03–G10 siguen 0/10; total **20%**, delta 0. D01–D14: 0/14. Sin `GO_LOCAL_PR` ni
`GO_DEVELOPMENT_REAL`.
