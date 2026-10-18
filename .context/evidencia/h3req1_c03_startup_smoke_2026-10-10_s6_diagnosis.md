# Diagnóstico S6 — G06 Pages/workerd startup aún NO-GO

Fecha: 2026-10-10. Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD baseline `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Ejecución

S6 se ejecutó una vez tras validar sintéticos, pins, manifiestos y revisión independiente. El
contenedor usó la imagen Node fijada, snapshot/dependencias S3 read-only, red interna Docker
`h3req1-c03-startup-net-20261010-s3` sin egress, filesystem read-only, variables sintéticas y
sin DB, PostgREST, Edge, SQL, Auth, correo ni servicios remotos. No hubo OOM ni cleanup de recursos
S3. La parada acotada verificó etiquetas de propiedad del contenedor S6.

El filtro rechazó líneas con sufijos arbitrarios y códigos con forma de secreto; admitió solo tipos
Miniflare y códigos cerrados. Node sintéticos, Bash syntax, ShellCheck oficial 0.11.0, manifiesto,
`git diff --check` y revisión independiente pasaron.

Evidencia de runtime: `runtime-stage=dependency-roots-present`,
`runtime-error-class=MINIFLARECOREERROR`, `runtime-project-frame=line:800:column:3`, healthz
NO-GO tras 4 intentos y `runtime-exit=code:1 signal:none`. El contenedor
`h3req1-c03-startup-runtime-20261010-s6` quedó `exited|1|false`; ID
`e7dcb0e20e47fd8d1c26ab6e5ce6674b10fb480bcc67dabcaf24cbe2e7cf1f36`. El resultado sanitizado es
[S6](h3req1_c03_startup_smoke_2026-10-10_s6.md), SHA-256
`38f5ff8c466886ae405db19bc26ad498accacf14e9de95218d1f7816bcde9b74`.

## Alcance de la conclusión

La clase `MiniflareCoreError` ubica el error en la inicialización Miniflare/workerd. El marco
`runtime.mjs:800:3` es el `await runServer({ startupOnly: true })`; el último evento precede a
directorios/TLS sintético, compilación esbuild, construcción Miniflare y llamadas `getWorker`.
La evidencia no permite distinguir cuál de esas operaciones lanzó la excepción ni muestra un
código cerrado. No se concluye defecto del producto o del daemon Docker.

## Siguiente diagnóstico

Preparar eventos de fase allowlisted alrededor de las fronteras existentes y capturar tipo/código
solo desde propiedades estructuradas mapeadas a enums cerrados. Mantener el resultado filtrado,
no imprimir mensaje/stack, preservar los recursos y no iniciar Edge/DB hasta healthz PASS. La nueva
ejecución debe tener inputs/manifiesto propios y revisión de seguridad antes del runtime.
