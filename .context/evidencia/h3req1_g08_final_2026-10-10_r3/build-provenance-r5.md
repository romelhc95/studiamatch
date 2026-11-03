# Procedencia del export R5 para aceptación local G09

Fecha: 2026-10-10. Alcance: vincular el export estático mock R5 y el export
normal R5 con el snapshot de fuentes y con la aceptación local que los consume.
No afirma UAT ni onboarding ejecutados.

## Identidad del build

| Elemento | Identidad comprobada |
|---|---|
| Candidato | `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c` |
| Snapshot de entrada | `source-candidate-r3.tar`, SHA-256 `c41d205cf2b2b8bad72d654dfd1854fbf4f919e5367293541180b59c4c4b9733` |
| Manifiesto de entradas del snapshot | `source-provenance-r5/source-inputs-r5.sha256`, 599 archivos, SHA-256 `7c153c3e9098b7117bddd654f26fd83f8a82db20bda255533a691f32f7728dbc` |
| Builder | `run_candidate_builds_r5.sh`, SHA-256 `02d7b653cc836fe90084cef7d3fcef4cfd01bf024f2f243ca431d4ee49f6f505` |
| Imagen de build | `studiamatch-h3req1:20261009-v3`, ID `sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63` |
| Volumen de trabajo | `h3req1-g08-build-work-r3`, label `com.studiamatch.h3.scope=g08-build-work` |

La comparación acotada de los 599 archivos de fuentes/fixtures del manifiesto
contra el candidato terminó exit 0 y cero diferencias. Los hashes de
`web/package.json`, `web/package-lock.json`, `web/src/app/admin/edit/page.tsx`
y `tests/h3_local_uat.mjs` coinciden entre snapshot y candidato.

Después del build/typegen, el volumen de trabajo tuvo dos diferencias generadas
esperadas: `web/next-env.d.ts` y `web/tsconfig.tsbuildinfo`. Excluidas esas dos
salidas, la comparación SHA-256 del volumen confirmó 597/597 entradas iguales y
cero ausentes. No se aceptan diferencias en fuentes restantes.

## Resultados preservados

| Resultado | Evidencia | SHA-256 |
|---|---|---|
| Build normal | `normal-build-r5.log` | `ab17c72a68c414cb20792630165c7b660e71c14087ca40ecc774da74b2038c1d` |
| Build mock | `mock-build-r5.log` | `fae704e74d6d8d4d2657652843a345b6a710baac04279c544269e7a1fee4203f` |
| Smoke normal | `normal-smoke-r5.log` | `7d64dc65fbb55d62322938d290d4e05fbafd0927120ee3082a12988880ba019a` |
| Manifiesto normal | `normal-out-r5.sha256`, 126 archivos | `f18df77b06b3726bd2028c7538d633eeaa74af7521738cbe7d2261a2a1269a31` |
| Verificación normal | `normal-out-r5-verify.log` | `82bc74e59926392867699906097b775ce1aff9b3005d870632937820006e9933` |
| Manifiesto mock | `mock-out-r5.sha256`, 126 archivos | `f5b7f0bfbfbb1df999d7f41d36b7056f2abb91883117e114c6f1db3e5d2cad4e` |
| Verificación mock | `mock-out-r5-verify.log` | `e2fd753b1aa2f3c485fc291c8a5a077f8f2e2643b11c78e588f3fd0269255ba4` |

La ruta mock sintetizada es `/courses/mock/mock-course/`; el normal export
contiene además `/courses/inst-a/curso-legacy-visible/`. G09 R11/R5 verifican
este documento por hash fijado, el manifiesto de 599 fuentes, los sidecars de
126 archivos y el contenido completo del export antes de crear fixtures.

El registro no incluye credenciales ni valores de entorno. Los tests locales
usan solamente cuentas, correos, tokens y claves sintéticos. La revisión visual
144/144 y onboarding 10/10 siguen pendientes hasta que sus runners terminen.
