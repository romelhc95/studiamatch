# R16 — preflight y diagnóstico seguro de respuesta temprana

## Inputs fijados

- Manifiesto: 65 entradas, SHA-256 `186862f80907e1e668b258d9c3ab7058d0360476be8b58f491288e501a324dfc`.
- Runner R16: SHA-256 `4522cf3c9c92353cce7095577e5849abe386ed98584b02cf044ff40cd26daf85`.
- Suite contractual R16: SHA-256 `a12ccde71582b48041f3298f3f98532ce88298e87cc0a56caeccd456998d5ae3`.
- Runtime adaptador: SHA-256 `828b93c2d9774884cd3cfa710b891bb84b8a85ac123445383fac30733a12ca38`.
- Clasificador integrado: SHA-256 `14a69f7cc19197057c29caf8aabdf3117bf1387b616bf591594820b6cecad6b6`.

## Cambio del harness

R15 pasó login con AAL2 y ambas cookies, luego agotó 60 s esperando el evento de retención Auth. El control no observaba si la solicitud BFF/Edge se resolvía antes; por eso no se obtuvo status ni código. R16 compite el evento Auth con la respuesta/rechazo de la promesa de invitación y con timeout interno de 30 s. Una salida temprana emite solo un código fijo (`INVITE_EARLY_*`, HTTP status, timeout o transport); el texto del body nunca se incluye. Cualquier respuesta 2xx antes del hold se clasifica como finalización prematura y detiene el gate. Miniflare fija ambos hosts exactos usados por el smoke: `admin.local.test` y `studiamatch.com`.

## Validaciones

- Manifest 65/65 PASS.
- Bash `-n` dentro del Node image fijado, fuente read-only, network none: exit 0.
- ShellCheck 0.11.0 oficial en contenedor aislado: exit 0.
- Suite contractual aislada: 18/18 PASS, exit 0; Node image fijada, mount `tests/` read-only, network none.
- `git diff --check` y los archivos R16 no rastreados pasaron el control de whitespace.
- No se cambiaron fuentes funcionales, SQL, workflows, locks ni configuración Docker.

Una ejecución contractual intermedia dio 17/18 porque un test estático de login aún exigía el nombre anterior `isLoginFailureCode`; se actualizó al helper integrado que preserva exactamente el allowlist de login y añade los diagnósticos del invite. La versión final pasó 18/18. Esta fue corrección de una expectativa contractual del runner, no una regresión de producto.

## Resultado no acreditado todavía

La suite estática no demuestra la respuesta real BFF/Edge ni reserva/Auth. El siguiente ensayo R16 usa fixture local nuevo y debe entregar ese código sanitizado antes de continuar C03.
