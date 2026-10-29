# H3REQ1 G06 S9 — función de compatibilidad invocada antes de definirse

Fecha: 2026-10-10. Checkout candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Resultado

La invocación S9 con runner SHA-256
`b12ab1815eaf1e0cbe6cf3655176c5299b089c9b8c63615eab3102f926597c9d` y sidecar SHA-256
`06b5d651ee2279bbdc503d6112ee874eb29f74e65fb32cca0973223f42f9839c` terminó `exit=127` en
`phase=preflight`: `verify_s3_dependency_inputs_compatible: command not found`.

El shell alcanzó la validación de fuente y falló en la llamada situada antes de las definiciones
de ambas funciones auxiliares. La llamada ocurre antes de la primera consulta Docker del runner.
La inspección read-only posterior no encontró contenedor ni volumen S9 con el nombre reservado;
no se creó archivo de resultado de runtime y ningún recurso previo fue retirado o modificado.

## Causa demostrada y corrección

Bash ejecuta las órdenes en secuencia; una función declarada más abajo no existe todavía cuando
se alcanza la llamada. Se movieron únicamente `verify_preserved_manifest_compatible` y
`verify_s3_dependency_inputs_compatible` para que ambas definiciones precedan a la invocación
pre-Docker. El contenido y los predicados de compatibilidad no cambiaron. El dispatcher sigue
fallando cerrado ante drift; el orden y los checks S3/S4/S5/S6/S7/S12 no se relajan.

La corrección requiere renovar la fila del runner en el sidecar S9, `bash -n`, `git diff --check`,
ShellCheck dentro de Docker y revisión independiente antes de la siguiente ejecución S9.
La ejecución fallida no acreditó Pages/workerd ni `healthz`; G06 continúa pendiente y G07 no inicia.
