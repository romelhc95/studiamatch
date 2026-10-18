# Diagnóstico S5 de Pages/workerd — 2026-10-10

## Alcance y resultado

S5 revalidó los recursos S3 y la red interna por ID, pasó las pruebas sintéticas del clasificador,
confirmó `dependency-roots-present` y ejecutó una vez el runtime Pages/workerd desde el snapshot
read-only. El proceso terminó con exit 1, sin OOM; el health check recibió tres intentos sin
`ready=true`/`workerd=true`. El runner se detuvo en `one-shot-pages-workerd-runtime-healthz` y
preservó el contenedor y todos los recursos S3.

Evidencia sanitizada emitida:

```text
phase=s3-resources|error_code=OK
phase=s3-network-id-resolution|error_code=OK
phase=runtime-diagnostic-synthetic|error_code=PASS
runtime-stage=dependency-roots-present
runtime-project-frame=line:800:column:3
runtime-last-stage=dependency-roots-present
healthz=NO-GO reason=runtime-not-ready attempts=3
runtime-exit=code:1 signal:none
container=h3req1-c03-startup-runtime-20261010-s5 state=exited|1|false network=internal-s3
NO-GO: Pages/workerd startup runtime failed
```

El marco apunta a la llamada de `runServer({ startupOnly: true })`, que espera la inicialización
Miniflare/workerd. No se registró una clase de error ni un paso interno; por ello la causa exacta
dentro de construcción del bundle, creación de Miniflare/workers o arranque sigue **no determinada**.
No se atribuye el fallo a Docker, al producto ni a un requisito cliente.

El diagnóstico S5 omitió errores JavaScript cuyo nombre/clase no estaba en su allowlist y conservó
solo el primer marco del archivo runtime. La próxima corrección será exclusivamente del probe:
emitir una clase cerrada para errores genéricos y hasta ocho marcos `runtime.mjs` numéricos, además
de observar excepciones no capturadas sin imprimir mensajes, stack crudo, rutas externas ni
metadata. Pruebas sintéticas comprobarán la redacción antes de una única continuación S6.

## Pins y recursos

- Runner S5 SHA-256: `6e886754cde2c4a3feb998adaea6d8d5ecde03558eae15841e4cdb2c60347fdf`.
- Manifiesto S5 SHA-256: `08a428daf847d690f4f72fdad03379eab4faeeba64362b78762c28e6f9e4ab03`.
- Probe S5 SHA-256: `b0a232c0348756af03798c2c0f8c7223a0b3d1d524fb013bd9cba0c8cc65261d`.
- Resultado S5 SHA-256: `c7d32cbe20929e5db473fa6331d5a34117a30a7ad24776ebb412d88e06b45f3b`.
- El revisor independiente cerró el finding LOW del preflight de rutas de evidencia; no reportó
  hallazgos nuevos en pins, red, sanitización, runtime o stop conditions.
- Contenedor S5 `h3req1-c03-startup-runtime-20261010-s5`, ID corto `d95d6c56bc4d`, quedó
  `exited=1`, `OOMKilled=false`; `HostConfig.NetworkMode` y `NetworkID` coinciden con la red S3
  internal fijada. No se borró ni reinició.
- Snapshot, volúmenes, holder y red S3; contenedores S2–S5 y checkout original permanecen intactos.
- No hubo egress, DB, Edge, SQL, Auth, correo, secretos, cambios remotos ni limpieza.

G06 permanece incompleto y bloquea G07. Métricas sin cambio: G01–G10 = 50%; cierre local = 5/9
(55.56%).
