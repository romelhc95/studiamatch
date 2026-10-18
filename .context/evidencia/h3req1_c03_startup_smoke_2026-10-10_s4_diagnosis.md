# Diagnóstico S4 de Pages/workerd — 2026-10-10

## Alcance y resultado

S4 reusó únicamente los tres volúmenes S3 read-only y la red interna S3. La verificación de
propiedad, pins, snapshot, imagen local y red pasó. No hubo bootstrap npm, egress, DB, Edge, SQL,
Auth, correo, secreto operativo ni servicio remoto.

El runtime S4 terminó `exited=1`, `OOMKilled=false`; healthz devolvió `ECONNREFUSED` y el proceso
salió antes del marcador `runtime-ready`. La salida permitió acreditar `dependency-roots-present`,
pero no distingue todavía si el fallo ocurrió durante la generación TLS, el inicio de Miniflare/
workerd o el bind de los listeners. Las líneas restantes quedaron como clase `unclassified`; no
se conservó ni expuso texto crudo. Por tanto, la causa interna del exit 1 permanece **no
determinada** y no se atribuye a Pages, workerd, Docker ni al producto.

El runner además devolvió exit 1 al comprobar la adjunción de red después de que el contenedor ya
hubiera terminado. La inspección estructurada posterior muestra `HostConfig.NetworkMode` igual al
ID S3 fijado, clave `h3req1-c03-startup-net-20261010-s3` y `NetworkID` igual al mismo ID. Docker
dejó `EndpointID` vacío para el contenedor detenido; exigir ese campo después de la salida fue un
predicado incorrecto del runner. La conexión efectiva se hará comprobable durante la vida del
contenedor o mediante el ID exacto configurado y el mapa de red persistente, sin exigir un
EndpointID efímero post-exit.

## Identidad y evidencia

- Runner S4 SHA-256: `c4659f16889a41987c6512d7167ffe397d6a31edf58b645a77bc888d627eca7c`.
- Manifiesto S4 SHA-256: `1cb90249466e65ccf59fc6ae3d2d7088f8c658917d91ece5f55c66bfd9268f29`.
- Resultado sanitizado: `h3req1_c03_startup_smoke_2026-10-10_s4.md`.
- Contenedor S4: `h3req1-c03-startup-runtime-20261010-s4`, conservado, exit 1, sin OOM.
- Red S3: ID `ffc476c62637ef44316255202a6b08a170df514685bb6d16efcf7976fd79a13f`, `Internal=true`,
  cero endpoints tras el exit; tres volúmenes S3 y holder preservados.

La corrección concreta siguiente separa el predicado de red persistente del `EndpointID` de vida
del proceso y añade diagnóstico sanitizado de etapa/tipo de error para identificar el fallo
previo a `runtime-ready`. No se repetirá el runner S4 sin esos cambios.
