# G05 S17 — cierre de imports transitivos: preparación y revisión

Fecha: 2026-10-10. Candidato `feat/h3req1-sync-20261002`, HEAD baseline
`4eb4d877a50b012bb630a129bd0c74482c33be9c`. La autorización local expresa del
responsable cubre snapshots y fixtures Docker de H3, pruebas y correcciones en
este checkout. No autoriza operaciones remotas ni el checkout original.

## Tareas y gates

1. Incluir exactamente los tres imports relativos que S14 demostró ausentes en
   S16; pasar hashes, modos, allowlist, extracción y verificación independiente.
2. Comprobar recuperación del contenedor ante fallo con 13 escenarios
   sintéticos; `bounded-stop=completed` solo se emite tras `docker stop` exitoso
   y una reinspección que confirma identidad y estado terminal.
3. ShellCheck, `bash -n`, manifiesto y diff limpios; revisión independiente.
4. Tras revisión PASS, ejecutar S17 una vez y registrar por separado productor,
   receptor y verificador. G06 Pages/workerd depende de G05 PASS.

## Ficha de impacto

- **Componente:** productor/receptor/verificador del snapshot aislado S17.
- **Consumidores:** Pages/workerd S15 y después C03 integrado G07.
- **Contrato:** 16 fuentes allowlisted, manifest v9 fijado, 17 archivos en la
  copia, cierre de imports relativos demostrado, sin symlinks ni modos
  especiales, límites de bytes, red `none`, imagen local fijada, volumen y
  contenedor identificados y preservados.
- **Preservado:** resultados y snapshots S14/S16; el checkout original y
  `studiamatch-dev` no se modifican. No se retiran recursos históricos.
- **Renovado:** self-test de recuperación S17, ShellCheck y pins del runner.
- **Recuperación:** ante fallo se preservan el volumen y contenedor exactos;
  una parada solo se informa completa después de inspección posterior.

## Cambio focalizado

S16 confirmó su propio manifiesto 13/13, pero no incluía los imports relativos
existentes en el candidato: `tests/h3req1_c03_login_result.mjs`,
`tests/h3req1_c03_safe_postgrest_error_code.mjs` y
`tests/h3req1_c03_replay_state_diagnostic.mjs`. El manifest v9 conserva los 13
sources de S16 y añade solo esos tres archivos. No se cambia lógica de producto.

La revisión S17 previa encontró LOW en recuperación: el runner podía informar
parada completada para cualquier estado que no fuera `running`. Se corrigió
para aceptar como no requerido solo `created|exited|dead`; estados inesperados
fallan cerrados. Si el estado inicial es `running`, se ejecuta una sola parada
acotada y luego se revalida ID, nombre, JIT, manifest, nonce y estado terminal.
No se elimina el contenedor. El self-test evalúa la función real con Docker
simulado y cubre 13 rutas, incluidos ownership incorrecto, estado inesperado,
fallo de stop/reinspect y estado aún activo.

## Evidencia estática y sintética

- Manifiesto v9 SHA-256
  `b1711c0b253c077fc1ff9493d9c74a11d12fa684acc0a144a97f5889b5d63012`;
  `sha256sum -c`: 16/16 PASS.
- Runner S17 SHA-256
  `8a4864f94753bad494cafa5a0061825e6256762d75bc1076b98f73d03069646f`.
- Self-test recovery S17 SHA-256
  `cdff899956c4030adb8c5c69ff55076294d8656117c81b64b213e82b63af5100`;
  13/13 PASS sin Docker.
- Sidecar S17 SHA-256
  `a1c5ae0bb76c75b763a15b38eaad9f19c4ca0311aefd323ee73575ddf5bf4450`;
  fija el runner y evita hash circular.
- `bash -n`, `git diff --check` y ShellCheck 0.11.0 PASS. ShellCheck usó la
  imagen ya local `koalaman/shellcheck:v0.11.0` con digest
  `sha256:61862eba1fcf09a484ebcc6feea46f1782532571a34ed51fedf90dd25f925a8d`,
  `network=none`, root read-only y mounts read-only; contenedor efímero.
- Dos fallos de preparación quedaron corregidos antes de runtime: el mock
  inicial contó inspecciones en un subshell y no conservó el contador; se usó
  la traza temporal como fuente del conteo. ShellCheck señaló dos SC2034 en
  globals consumidos por la función extraída; se documentaron las supresiones
  locales específicas. Reejecución sintética y ShellCheck: PASS.

La revisión independiente del paquete corregido fue **PASS estático**, sin
hallazgos abiertos. S17 de Docker se ejecutó una vez y cerró con exit 0,
`phase=complete`. Productor, receptor, filtro y verificador terminaron en 0;
17 archivos (16 fuentes) quedaron copiados, 16/16 hashes, modos exactos y cero
symlinks. Evidencia real:
[resultado S17](h3req1_c03_source_snapshot_2026-10-10_s17.md). El volumen
persistente S17 y contenedor terminado se conservaron. No se ejecutó runtime,
Edge, PostgreSQL, PostgREST o SQL en esta fase.

## Estado y siguiente paso

G05 está **completo** tras el resultado S17; G06 **pendiente** hasta el arranque
Pages/workerd. Métrica vigente: G01–G10 50%; G01–G09 5/9 = 55.56%. Frente al
inicio de este ciclo (50% y 5/9), el delta es 0 pp; implementación y revisión
estática no sumaron puntos. El comando ejecutado fue:

```bash
bash tests/h3req1_c03_source_snapshot_s17.sh \
  --jit H3-CLOSE-03-SOURCE-SNAPSHOT-S17-2026-10-10 \
  --runner-sha256 8a4864f94753bad494cafa5a0061825e6256762d75bc1076b98f73d03069646f \
  --sidecar-sha256 a1c5ae0bb76c75b763a15b38eaad9f19c4ca0311aefd323ee73575ddf5bf4450
```

Timeout y límites permanecen fijados en el runner; un fallo detiene el ciclo y
preserva recursos para inspección. S17 pasó. El runner S15 está preparado y
espera revisión independiente antes de una ejecución real de Pages/workerd.
G07 integrado, G08 y G09 esperan sus gates y pruebas propias.
