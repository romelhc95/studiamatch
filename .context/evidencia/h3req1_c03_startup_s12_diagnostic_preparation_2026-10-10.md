# G06 Pages/workerd S12 — preparación diagnóstica

Fecha: 2026-10-10. Candidato: `feat/h3req1-sync-20261002` /
`4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Tarea, ficha y estado

- Gate activo: G06, Pages/workerd hasta `healthz` real. Sigue pendiente; esta
  preparación no suma puntos ni habilita G07.
- Componente: captura sanitizada del error de arranque en
  `tests/h3req1_c03_startup_runtime_probe_s8.mjs` y
  `tests/h3req1_c03_startup_validation_preload_s8.cjs`.
- Consumidores: runner local de startup S11/S12; el runtime candidato S16 y sus
  contratos no cambian.
- Contratos: solo campos allowlisted de clase/código y rutas de validación
  reducidas; sin mensaje, stack, entorno, secretos ni metadata cruda en evidencia.
- Reutilizable: snapshot S16 y sus 13 fuentes/14 archivos; instalaciones de lock
  S11 en los volúmenes de herramientas y Pages; sintéticos G03 ya aprobados.
- A renovar: diagnóstico del runtime workerd y `healthz`; el resultado S11-R2 no
  cierra G06.
- Recuperación: S11 runtime fallido, holder, volúmenes S16/S11 y red internal se
  preservan. `studiamatch-dev` continúa como entorno habitual separado.

## Fallo previo y corrección local

S11-R2 completó ambos `npm ci` desde los locks actuales con lifecycle scripts
desactivados y ejecutó el runtime en la red internal. Terminó exit 1 en
`one-shot-pages-workerd-healthz`: último stage `runtime-uncaught-error`,
`healthz=NO-GO`, exit del runtime 1, `OOMKilled=false`. La salida anterior no
incluía el tipo ni el código y no demostraba una causa. Evidencia preservada en
[`S11-R2`](h3req1_c03_startup_smoke_2026-10-10_s11r2.md); contenedor preservado:
`h3req1-c03-startup-runtime-20261010-s11`, ID
`612d8e1a65358344d8e847ef2b87920a7a7df992b165dd41a972ebdd2176f41d`.

La prueba roja de la nueva composición salió exit 1 con el marcador sanitizado
`runtime-probe-error=type:REFERENCEERROR|code:UNCLASSIFIED`, porque el resumen
todavía no existía. Se implementó solo el transporte allowlisted de `errorType`
y `errorCode`; el preload ahora reduce también path y keys de validation issues
antes de escribir el evento interno. El probe clasifica clase, código y fase;
el filtro CLI `--sanitize` descarta cualquier línea fuera del allowlist. El
runtime funcional y el contrato H3 no se editaron.

Un primer comando de prueba del CLI terminó exit 1 por quoting de su wrapper
shell. La misma prueba se ejecutó después con quoting corregido y pasó; no fue
un fallo del filtro ni del runtime. ShellCheck detectó y llevó a corregir
SC2155 en el RUN_ID del runner. La carga dinámica del filtro se reemplazó por
su CLI para evitar SC1091 y facilitar la prueba aislada.

## Evidencia estática previa a S12

En Node fijado, `network none`, raíz read-only, montajes de helpers read-only:

```text
phase=runtime-preload-diagnostic-synthetic|error_code=PASS
phase=runtime-diagnostic-synthetic|error_code=PASS
phase=runtime-output-filter-synthetic|error_code=PASS
phase=runtime-diagnostic-static-synthetics|error_code=PASS
```

También pasaron `bash -n`, `node --check` de ambos helpers, el modo CLI del
filtro y ShellCheck 0.11.0 sobre runner/filtro. El sidecar de entrada verifica
7/7 pins; SHA-256
`fbfbed931f0253a1a7165419bc9ff3de18e0fad79eb942a2a38d5a2592c5dfba`. El runner
S12 tiene SHA-256 `34fe573e3d6b2dcc5072317a8f0cdb8ee40a2332d3ee7e44dd30765a633ca8f6`.
La revisión independiente estática final sigue pendiente antes de ejecutar el
runtime.

## Alcance S12 y recursos

Una ejecución diagnóstica de Pages/workerd, timeout 180 s, límites 2 CPU/2 GiB,
sin retries. Reusa S16 y los volúmenes read-only S11, imagen Node local fijada y
red Docker internal vacía. No repite instalación, no conecta PG17/PostgREST/Edge,
no lee `.env*`, no usa cuentas/servicios remotos y no modifica el checkout
original. Si hay FAIL, conserva el contenedor S12 para inspección estructurada;
no elimina volúmenes ni red. Si hay PASS, acredita `healthz` real y retira solo
el contenedor S12 exacto tras escribir la evidencia.

Recursos identificados:

| Recurso | Estado | Función |
|---|---|---|
| `studiamatch-dev` | Healthy | Entorno habitual candidato; separado del smoke S12 |
| Snapshot S16 y volumen fuente | Preservados | Candidato Pages/workerd de 13 fuentes |
| Holder S11 | Running, network none | Conserva tmpfs de dependencias |
| Volúmenes tools/pages S11 | Preservados, instalados desde lock | Dependencias actuales de runtime |
| Runtime S11 | Exited 1, sin OOM | Evidencia del fallo previo |
| Network S11 | Internal, 0 endpoints | Runtime aislado de salida de red |

Gates y métricas quedan sin cambio: G01–G05 completos; G06–G09 pendientes/parciales;
G10 remoto pendiente. Tablero G01–G10: 50%; cierre local G01–G09: 5/9 = 55.56%.
Siguiente comando, condicionado a revisión estática: ejecutar una vez
`bash tests/h3req1_c03_startup_runtime_diagnostic_s12.sh` y conservar únicamente
la salida de fases/códigos de `.context/evidencia/h3req1_c03_startup_smoke_2026-10-10_s12_diagnostic.md`.
