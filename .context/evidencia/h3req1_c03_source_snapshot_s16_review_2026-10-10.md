# Revisión independiente del snapshot S16 — 2026-10-10

Revisión estática de `tests/h3req1_c03_source_snapshot_s16.sh`, su sidecar y el
manifiesto de fuentes v8. No ejecutó Docker, SQL, pruebas ni runtime.

## Resultado

**PASS estático; sin hallazgos bloqueantes.** El revisor contrastó S16 con S15:
el delta funcional del manifiesto de fuentes es una sola entrada, el hash del
runtime integrado. El runtime actual selecciona el manifiesto v8 en modo
`startupOnly`, y el hash coincide.

Pins comprobados: runner `16f160c42ff1e89fd1b6daab876e2c2121cfe51e56f15716851a3c181a33a8e6`,
sidecar `4b159bae0f92fa16d466d6150a6cba8b672ad2d997b15bf14f4b983d4f9bd242`,
manifiesto v8 `5312e12762db37a8a2eac28658bd609d966c74dd0d210d38363cb3ebb62e209e`.
El conjunto contiene 13 fuentes; el snapshot añade el manifiesto para 14 archivos,
sin circularidad.

La allowlist, límites de tamaño, rechazo de symlinks y modos setuid/setgid,
stream tar acotado, imagen fijada, red `none`, recursos limitados y verificación
posterior con mount read-only están presentes. Ante fallo se detiene únicamente
el contenedor de la ejecución y se preservan volumen y evidencia.

## Límite

Esta revisión es estática; no acredita integridad en runtime por sí sola. El
resultado operativo S16 separado registra los exits del productor, limitador,
receptor, filtro y verificador: todos `0`, `source-manifest=13/13`, cero
symlinks y permisos exactos. Evidencia: `h3req1_c03_source_snapshot_2026-10-10_s16.md`.
