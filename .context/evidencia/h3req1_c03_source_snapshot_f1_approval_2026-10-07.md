# Atestación de aprobación humana JIT F1 — H3REQ1

Fecha: 2026-10-07. Registro local de la decisión explícita del usuario en esta sesión; no
modifica el JIT F1 consumido ni amplía su alcance.

## Decisión registrada

Decision: accept waiver and approve one F1 execution.

El usuario eligió **“Acepto y apruebo F1”** ante la solicitud que fijaba el JIT F1
`H3-CLOSE-03-SOURCE-SNAPSHOT-F1-2026-10-07`, SHA-256
`e4a651f47322cec8a9d7551a93b40186d2c25089215aa1b7b8c87a4263c2547f`. La respuesta aceptó
explícitamente el residual MEDIUM de bypass same-user y aprobó una sola ejecución con el
alcance exacto del JIT: `docker create`, verificación pre-start, un `docker start` con tar
`--no-same-owner`, inspección final y, ante fallo/señal posterior a start, como máximo un
`docker stop --time 5` al mismo ID pre-verificado.

No aprobó reintentos, logs/exec, remove, npm/workerd/Pages, otros recursos, Supabase, red
externa, remoto, push/PR/merge/deploy. La aprobación quedó consumida por la única ejecución
F1, cuyo resultado factual es NO-GO pre-start; no se reutiliza.

## Procedencia y límite

La respuesta visible en el historial de esta sesión es el registro de la decisión humana.
Esta nota sanitizada versiona el alcance/resultado sin incorporar datos privados ni
credenciales. El JIT F1 original permanece preservado con su estado de propuesta previo; la
atestación documenta la decisión posterior y no lo reescribe.
