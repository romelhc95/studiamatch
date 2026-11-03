# Evidencia G03 — filtro seguro del diagnóstico Next typegen

Fecha: 2026-10-10. Candidato: rama `feat/h3req1-sync-20261002`, HEAD baseline
`4eb4d877a50b012bb630a129bd0c74482c33be9c`. La WIP local se preservó; ningún archivo del
checkout original fue modificado.

## Hallazgo reproducido

La revisión independiente detectó que el clasificador embebido aceptaba `/home/.../file` con su
regex de nombres de módulo. Reproducción sintética en Docker aislado, imagen local fijada
`sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63`, `--pull=never`,
`--network=none`, filesystem read-only y entorno vacío:

```text
synthetic_absolute_path_accepted=true
```

Esto acredita un riesgo de privacidad del diagnóstico, no una causa del fallo de Next ni un defecto
del producto.

## Corrección mínima y prueba

Se extrajo la clasificación a `tests/h3req1_docker_peer_substep_diag/r9_typegen_classifier_v1.py`.
El clasificador ahora acepta únicamente identificadores de paquetes declarados en las secciones
de dependencias de `web/package.json`, valida segmentos de subpath y emite solo el root package.
Rutas absolutas, relativas, traversal, separadores Windows, nombres no declarados o sintaxis
desconocida producen `module=UNCLASSIFIED`. El host también limita la salida a identificadores de
paquete válidos. El fallo de Next no se considera remediado por este cambio.

Sintéticos ejecutados en Docker aislado y en red `none`:

- Emitir `next` y `@studiamatch/ui-kit` como raíces declaradas: PASS.
- Aceptar el subpath `next/dist/bin/next`, pero emitir solo `next`: PASS.
- Rechazar ruta absoluta Unix, ruta absoluta Windows, `./`, `../`, traversal embebido, ruta
  `web/src/...` y paquete no declarado: PASS.
- Preservar categorías cerradas de error de permisos y dependencias: PASS.
- Resultado durable del runner sintético: `phase=r9-typegen-classifier-synthetics|error_code=OK`,
  exit 0.

Validaciones auxiliares del cambio: Python compile PASS; `bash -n` para host/inner PASS;
ShellCheck 0.11.0 sobre ambos runners PASS usando el bundle cacheado con SHA-256
`b7af85e41cc99489dcc21d66c6d5f3685138f06d34651e6d34b42ec6d54fe6f6` en contenedor aislado;
`git diff --check` PASS. No hubo descarga, instalación, pull, cambio de imagen ni lectura de
secretos/Env.

La revisión de seguridad independiente se volvió a solicitar para los hashes del helper, sintéticos,
host e inner actualizados. El runner completo aún no se ejecutó después de este ajuste; por ello
G03 sigue parcial, TypeScript y las tres suites focales siguen sin resultado, y esta evidencia no
cierra ningún gate ni modifica el porcentaje.

## Actualización posterior — ejecución G03 V5

El runner completo V4 y su causa quedaron preservados en la evidencia de ciclo. V4 pasó typegen y
TypeScript, pero falló antes de ejecutar la suite protegida: `python3` del sistema no tenía pytest.
La imagen fija incluye pytest 9.1.1 en `/opt/venv/bin/python`, donde el Dockerfile instala los
requisitos versionados. Se corrigió la invocación del runner para usar ese intérprete y cerrar con
un código explícito si el runtime pytest falta. La revisión independiente quedó sin hallazgos.

En V5, `next typegen`, `tsc --noEmit` y las tres suites focales pasaron; se preservó actionlint por
hashes idénticos y ShellCheck/ESLint previos porque las 68 fuentes del candidato coinciden con el
snapshot r6. El fixture temporal se retiró con cleanup PASS. Referencias: [evidencia V4](h3req1_g03_r9_tsc_heap_and_pending_suites_2026-10-10_v4.txt),
[evidencia V5](h3req1_g03_r9_tsc_heap_and_pending_suites_2026-10-10_v5.txt) y [registro de ciclo](h3req1_ciclo_validacion_local_2026-10-10.md).
