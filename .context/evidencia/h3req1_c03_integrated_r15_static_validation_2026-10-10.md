# R15 — preflight y validación estática del harness integrado

## Identidad

- Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama `feat/h3req1-sync-20261002`, HEAD baseline `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- Manifiesto: 65 entradas, SHA-256 `bbe4a9c0f39fc2e066bb19d0f3bc6f0413ee7d5e5913b2b4a2c959be1512624d`.
- Runner R15: SHA-256 `a7d35e173bf0d4d955fe3f6a23d89894148be60cb5249806053bad3a722106ce`.
- Contrato R15: SHA-256 `92bb4113b344f1e57560f3ccc389a71cdef162e2b948c69b056da965952f32ab`.
- Adaptador integrado: SHA-256 `fefa397430c87b4ffbfd64602cb282093b9f505a5d92dfd9487d2f2950999afd`.

## Corrección a partir de R14

El log R14 conservó `step=/control/login`, `type=TypeError`, exit 1. Probe sintético en Miniflare fijado demostró que `worker.fetch()` rechaza con `TypeError` el `Request` global de Node. El `Request` de Undici de la dependencia de Miniflare se acepta. También se comprobó que el hostname `admin.local.test` debe estar en las rutas de Miniflare: sin ruta la capa de simulación devuelve `HTTP_403_INVALID_ORIGIN`; con ruta explícita devuelve HTTP 200 y el Worker ve URL/Origin iguales y `Sec-Fetch-Site=same-origin`.

R15 cambia solo el harness: `Request` y `Headers` proceden del Undici fijado; `admin.local.test/*` se declara en la configuración Pages, heredada por el Worker suspendido. El BFF/producto no cambia. Se añadieron aserciones contractuales para la clase HTTP y la ruta.

## Validaciones ejecutadas

- `bash -n` dentro de imagen Node fijada, bind read-only, red `none`: exit 0.
- ShellCheck 0.11.0, imagen fijada, runner read-only, red `none`: exit 0.
- Suite contractual Node aislada: 16/16 PASS, exit 0, Node fijado, `tests/` read-only, red `none`.
- Manifiesto: `sha256sum -c` 65/65 PASS.
- Probe sintético Miniflare: Undici Request + ruta explícita PASS; resultado 200 y URL/Origin concordantes.
- Contrato de seguridad: error codes cerrados; sin body, correo, cookies, tokens ni detalle arbitrario en la salida runtime.

Incidencias de validación corregidas y preservadas como delta: (a) la primera ejecución R15 contractual tuvo 15/16 porque una expresión del test aún esperaba `new Request`; se actualizó para exigir el constructor compatible `workerRequestConstructor`, luego 16/16; (b) la primera invocación ShellCheck recibió flags `sh` por la imagen que usa ShellCheck como entrypoint y no analizó el archivo (exit 3); se corrigió la invocación al entrypoint directo, que pasó. Ninguna afectó al runner/producto; no hubo reintentos dentro de un ensayo integrado.

## Alcance

Esto acredita solo la estática del runner y el adaptador de simulación. R14 integrado falló en login; R15 integrado aún está pendiente. G07 permanece parcial hasta que el drill C03 integrado completo, incluida recuperación y smoke final, termine exit 0.
