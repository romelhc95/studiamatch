# Revisión independiente final del paquete R5 — 2026-10-11

## Alcance y resultado

Dictamen estático independiente del inventario R5, los cambios propuestos,
las evidencias seleccionadas, la matriz LOCAL-01..23 y el cuerpo preparado con
`.github/pull_request_template.md`.

- Manifiesto R5 SHA-256:
  `e8813e32e037d5b0306a9827b30b0f152654bf3d5515b0e13df3113295f2744f`.
- Cuerpo R5 SHA-256:
  `66bfbe070714e4c762c6dbf8c216baeb0f86b1b2ed00494e1d991e142df6bdb1`.
- Alcance: 89 paths; 141 evidencias; 230 archivos con contenido, modo y tamaño
  comprobados; cero solapamientos entre las listas de cambios y evidencia.
- Ambas listas quedaron ordenadas byte a byte por ruta; los digests declarados
  coinciden con JSON compacto serializado sobre ese orden.
- Rama `feat/h3req1-sync-20261002`, HEAD baseline
  `4eb4d877a50b012bb630a129bd0c74482c33be9c`, 61 paths tracked modificados,
  28 untracked propuestos, cero staged; los digests WIP/diff se reproducen.
- El cuerpo sigue la plantilla versionada: todas sus secciones y filas están
  presentes, cero placeholders y 22/22 links locales resuelven.
- La matriz y el cuerpo coinciden en 216 PASS caso-viewport seleccionados
  (72×3), 189 ejecuciones R28/R29/R30 y LOCAL-23 pendiente de esta revisión.

**PASS estático. No se encontraron findings HIGH/MEDIUM ni bloqueantes para
LOCAL-23.** No se ejecutaron pruebas ni Docker durante esta revisión.

## Seguimiento LOW no bloqueante

La migración `db/migrations/20261010_h3_admin_members_service_select.sql`
concede SELECT de tabla a `service_role`, mientras el consumidor revisado
consulta cuatro columnas. Un grant por columna podría reducir metadata visible
si se comprometiera esa credencial. En el flujo revisado la credencial queda
server-side, el actor se autoriza antes de consultar la membresía y no se
concede acceso directo a `anon` ni `authenticated`. No se observó un camino de
exposición a usuarios cliente ni un defecto de aceptación local. Se deja como
endurecimiento opcional para la revisión de schema previa a cualquier
promoción remota; no se cambia la migración ni se declara una waiver.

Una ruta histórica R176 ausente de la lista de exclusiones WIP es no-op y no
omite rutas existentes.
