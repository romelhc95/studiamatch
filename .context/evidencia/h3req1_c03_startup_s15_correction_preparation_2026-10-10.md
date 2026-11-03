# G06 — corrección del health check S15 y preparación del snapshot S18

Fecha: 2026-10-10. Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`,
rama `feat/h3req1-sync-20261002`, HEAD baseline
`4eb4d877a50b012bb630a129bd0c74482c33be9c`. Se conserva el checkout original,
S16/S17 y todos los recursos históricos.

## Bloqueo demostrado y corrección

La revisión independiente S15 encontró que `/healthz` respondía desde el
controlador Node y marcaba `workerd=true` por referencias a Miniflare, sin
hacer una petición al worker Pages. No se ejecutó S15 con ese predicado.

Se añadió `pagesWorkerRootProbe()`: solo acepta status 200 y el cuerpo sintético
exacto que entrega el binding ASSETS para `/`. El control `/healthz` lo invoca
una vez a través de `pagesRequest(pagesActive, '/')`, verifica que el contador
ASSETS sea uno y que el gateway sintético no se haya usado. El probe exterior
requiere además `pagesWorkerProbe=root-asset`, status 200 y coincidencia del
marcador antes de imprimir PASS.

El modo startup-only ahora calcula los hashes de contenido de los dos árboles
`node_modules` S11 con el helper ya usado por el drill integrado, y los compara
con un JSON fijado en el runner. Medición read-only previa, sin red, sobre los
volúmenes actuales:

- tools: `82385e75623f0a0b7f6c2919232634b92b0d1c0709cef6d3af34730676b3629e`
- Pages: `b7bb98f751194c0c28c793bf64debdccedbe94c5b8f5e0157374b5accf555ea1`

La medición acredita los bytes presentes al preparar S15; no se presenta como
una medición tomada durante el bootstrap S11. El runtime volverá a comprobar
los mismos bytes con los mounts en solo lectura. JSON sanitizado en
`h3req1_c03_startup_s11_dependency_digests_2026-10-10.json`.

El runner S15 exige que `.context` y `.context/evidencia` sean directorios
físicos, no symlinks, y que sus rutas canónicas sean las del checkout antes de
abrir el archivo de resultado.

## Ficha de impacto

- **Componente:** health check Pages/workerd, verificación de dependencias y
  controles del runner S15.
- **Consumidor:** G06 y después G07 C03 integrado.
- **Contrato preservado:** BFF/HttpOnly, gateway, cuotas, roles y MFA; el probe
  usa solo el asset sintético `/`, no Auth, DB, Edge, PostgREST o correo.
- **Preservado:** S17 permanece inmutable; S18 tendrá volumen y contenedor
  nuevos. Volúmenes S11 se montan read-only y no se reinstalan dependencias.
- **Cobertura nueva:** seis casos del contrato S15: respuesta del worker,
  digest de dependencias, ruta física de evidencia, respuesta válida, status o
  cuerpo inválido, y excepción del fetch.
- **Recuperación:** ante NO-GO se conserva runtime y evidencia S15; la parada
  verifica identidad, JIT, manifest y nonce. En PASS solo se retira el runtime
  S15 exacto; snapshots/volúmenes S11/S18 se conservan.

## Validación reproducible

El contrato previo dio RED esperado con exit 1 y 3 casos fallidos: el healthz
viejo no llamaba al worker, startup-only no comprobaba contenido de dependencias
y el runner no fijaba las rutas padre de evidencia. Tras la corrección, el
contrato dio `phase=s15-runtime-contract|error_code=PASS|cases=6` dentro de un
contenedor Node fijado, read-only y `network=none`. También pasan recovery S15
9/9, recovery de snapshot 13/13, sanitizador PASS, Bash syntax, ShellCheck
0.11.0 y manifiesto v10 17/17.

## S18 antes de S15

El runtime cambiado exige un snapshot nuevo; S17 queda preservado. El paquete
S18 fija imagen Node por digest, `network=none`, 0.5 CPU/128 MiB, 17 archivos
fuente allowlisted más el manifest, un límite de archivo de 9 MiB y timeout
acotado del stream. No instala dependencias ni lee secretos. Runner SHA-256
`870acaf354481de9b36a493f954355b1dfaf8555a60f7354a6147b3fa20a241e`, sidecar
SHA-256 `13a4bea55ed248d1ec0567f21258c5ccbc8dbfc9fb02667016aba0298ab262cf`,
manifest v10 SHA-256
`29d8459b81656d5947a6e2c771616ff6a59d1719af13b1f686a8d58b7ce5bc6e`.
Revisión independiente estática S18/G06: PASS; no ejecutó Docker ni runtime.
La ejecución S18 terminó exit 0 con los pins anteriores. Evidencia durable:
`h3req1_c03_source_snapshot_2026-10-10_s18.md`. Container ID
`48116e932a4756e9180191e69655fc4b7a571c37fc0e4ccfd627e2ad9857f9ea`, estado
exited/0, `oom=false`, `network=none`; volumen persistente
`h3req1-c03-startup-source-20261010-s18`, JIT/sidecar/run labels verificados.
Resultado: 18 archivos, 17/17 fuentes, permisos exactos, cero symlinks,
productor/receptor/verificador 0. S16/S17 no se modificaron. Esto renueva G05
para los inputs actuales; no acredita G06.

Comando exacto S18, después de revisión PASS y pins intactos:

```bash
bash tests/h3req1_c03_source_snapshot_s18.sh \
  --jit H3-CLOSE-03-SOURCE-SNAPSHOT-S18-2026-10-10 \
  --runner-sha256 870acaf354481de9b36a493f954355b1dfaf8555a60f7354a6147b3fa20a241e \
  --sidecar-sha256 13a4bea55ed248d1ec0567f21258c5ccbc8dbfc9fb02667016aba0298ab262cf
```

S18 no acredita G06. Tras su PASS se fijarán sus IDs y manifest en S15, se
revisará el paquete S15 final y solo entonces se ejecutará Pages/workerd.
G06/G07 y las métricas no cambian por esta preparación.

## Continuación autorizada — S18 PASS y repinado S15

Recuento actual del candidato: 55 rutas tracked modificadas, 744 untracked,
0 staged (799 entradas). Rama y HEAD siguen en los valores fijados; el
checkout original no se abrió para escritura. Los recursos S18 creados están
limitados a su volumen fuente y contenedor finalizado; la ruta de evidencia
S18 ya existe.

Checks ejecutados en esta continuación:

- `git diff --check` sobre runtime, probe, contrato, filtro y runners S15/S18:
  exit 0.
- `node --check` dentro de la imagen Node fijada, contenedor `network=none`,
  root read-only y mounts individuales read-only para runtime, helper de
  healthz, probe exterior y contrato: exit 0.
- `bash -n` del filtro S8, runner S15 y runner S18: exit 0.
- Sidecar del runner S18 y manifiesto de fuentes v10: hashes y archivos
  allowlisted verifican; 17 fuentes más el manifiesto.
- Preflight de colisión S18 previo a la ejecución: PASS.
- Inspección estructurada posterior de container ID, labels, estado y mount del
  volumen: coincidencia exacta con la evidencia S18; no se leyó `Env`.
- Runner S18: ejecución única, exit 0; snapshot 18 archivos, source manifest
  17/17, modos exactos, cero symlinks; productor, receptor y verificador 0.
- Contrato S15 con el volumen S18 read-only: 6/6 PASS en contenedor Node
  fijado, `network=none`, root read-only, contrato/helper/runner montados
  read-only.
- Recovery S15 9/9, filtro sintético PASS, ShellCheck 0.11.0, `bash -n`,
  hashes de INPUTS/runner/sidecar y `git diff --check`: PASS.

S15 todavía no se ejecutó. Las revisiones independientes encontraron dos
blockers sucesivos y ambos se corrigieron: (1) contrato sin SHA/inclusión en
inputs y pins viejos del filtro/probe; (2) Options/adjuntos del volumen no
verificados. Docker Desktop no expone `.Containers` en el template de `volume
inspect` (consulta read-only exit 1); se usó el filtro acotado
`docker ps -a --no-trunc --filter volume=<nombre>`, que mostró solo el snapshot
S18 terminado. Metadata verificada: `Options=null`, driver local, labels S18
exactos, único adjunto snapshot. El runner exige Options nulas y un adjunto
exacto al snapshot antes del contrato y otra vez inmediatamente antes de
runtime; ningún writer concurrente queda adjunto. Se añadió un caso sintético
que exige esas condiciones. Contrato final 7/7 PASS; los metadatos reales del
volumen dieron options PASS/attachments PASS.

El contrato SHA `298e0d824236f87d33674d241012d7c6527299b7ffdcb2470c8e710a161e680d`
está en INPUTS y en el pin directo del runner. INPUTS incluye S18, su runner y
sidecar y el source manifest v10. Recovery 9/9, filtro sintético, ShellCheck
0.11.0, `bash -n`, hashes, `git diff --check` y el preflight del volumen:
PASS. Pines para revisión independiente final: runner
`34618ac7d3a14578305de5122acea51fd2fd3470786ac05a1e0924b47eb68294`, sidecar
`9bc9f9fd3cfe0ec4df73a1e94145b96795075dac1ee1b95f82698c8517e79568`, INPUTS
`b2a6a47c4407caef78b2c731b223c4fc5c8fd5f7226982c9baa8aae671852484`.
Revisión independiente estática final: PASS; no ejecutó runtime. Métricas
vigentes: G01–G10 50%; cierre local G01–G09 5/9 (55.56%); delta 0. La siguiente
operación es revalidar pins/estado y ejecutar S15 una vez; G06 y G07 siguen
pendientes hasta los resultados runtime e integración.
