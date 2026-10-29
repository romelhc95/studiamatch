# G06 S15 — revisión independiente del paquete antes de runtime

Fecha: 2026-10-10. Candidato `feat/h3req1-sync-20261002` @
`4eb4d877a50b012bb630a129bd0c74482c33be9c`. La revisión fue estática; no se
ejecutaron Docker, Pages/workerd, pruebas ni suites. S15 no se consumió.

## Inputs revisados

- Runner `tests/h3req1_c03_startup_runtime_diagnostic_s15.sh`, SHA-256
  `87d4398287a097edc8bbff7a5d942596be46fb0d1c90fc8a2cf7298d7cc11821`.
- Sidecar `tests/h3req1-c03-startup-runtime-s15.sha256`, SHA-256
  `5125df73f572665c5f79fc372319d9316120cd264890b89a4f9b9ce99ac7f8bb`.
- Inputs manifest SHA-256
  `f69620d2d7b16d530fe5cd45be3a3f74e1cafb3da0aa9b222058b48aaef78cf7`; sus
  26 entradas pasaron `sha256sum -c`.

## Dictamen

**NO-GO para acreditar G06**. Se confirmó un predicado de healthz insuficiente:
el endpoint de control Node devolvía `workerd=true` porque había referencias
Miniflare, pero no enviaba una solicitud al worker Pages. La condición en
`tests/h3req1_c03_integrated_runtime.mjs` debe comprobar una respuesta real del
worker sobre la fixture sintética; no se acepta el healthz del proceso Node
como sustituto.

Dos observaciones LOW también se corregirán antes de repetir la revisión:

1. El startup-only comprobaba que existieran directorios `node_modules`, sin
   comparar su contenido con los volúmenes S11. Se medirán y fijarán sus
   digests y el runtime comprobará que coincidan.
2. El runner validaba la ausencia del archivo de evidencia, pero no la
   canonicalidad física de `.context/evidencia`. Se exigirá que los directorios
   padres sean reales, no symlinks, y resuelvan dentro del checkout.

Las demás garantías estáticas revisadas pasaron: endpoint/imagen, límites,
red interna, mounts read-only, salida allowlisted, stop-on-failure, evidencia
preservada ante fallo y limpieza del runtime exacto solo tras health PASS.

## Siguiente paso

Corregir el health check y los dos controles LOW, agregar cobertura sintética,
generar un snapshot fuente nuevo sin modificar S17, revisar de forma
independiente los pins finales y volver a ejecutar S15 solo tras dictamen PASS.
