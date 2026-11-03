# Preparación V11 — lectura F1 y r9 agrupados

Fecha: 2026-10-09. Estado: paquete preparado y revisado estáticamente; su JIT se consumió y
se detuvo en el smoke sintético antes de F1/r9. Ver [resultado V11](h3req1_c03_v11_combined_template_failure_2026-10-09.md).

JIT V11 SHA-256: `7775d8df1a71fe00f27e78e6a4e73599eab0a62bc064b438932adfb2dcd660b7`.

## Tareas y gates

| Tarea | Estado | Gate afectado |
|---|---|---|
| Preservar identidad Docker Desktop WSL y PASS sintético V10 | Evidencia y pins verificados; se reutiliza sin repetir socket ni probes | G04 parcial, sigue 0/10 |
| Smoke combinado del template con dos fixtures efímeros | Runner V11 preparado; requiere aprobación de una ejecución | G04 parcial, no es resultado de runtime actual |
| Leer imagen y contenedor F1 allowlisted | No alcanzados por el FAIL previo; la autorización está consumida | G04 sigue 0/10 hasta controles satisfechos |
| Ejecutar r9 local offline | No alcanzado; la autorización está consumida | G03 sigue 0/10 hasta los 14 checks PASS |
| Actualizar porcentaje y aceptación | No se modifican criterios ni evidencia previa | G01/G02 10/10; G03–G10 0/10; total 20% |

## Identidad y preservación

- Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`,
  `feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- WIP al preparar: 54 tracked modificados, 215 untracked, 0 staged.
- Checkout original preservado: `/home/romel/src/studiamatch`,
  `feat/h3req1-development-remote-tests`, HEAD `7650093b05a820e8e6faf9ec711e12fab8b50398`,
  39 tracked modificados, 39 untracked, 0 staged.
- La proyección fija el snapshot F1 de 2026-10-07. El runner compara su ID con el hash del ID
  aportado para `studiamatch-dev` y detiene la ejecución si coincide. No enumera recursos.
- Comparación estática de ambos IDs por SHA-256: `target-scope=DISTINCT`; no se imprimió el ID.

## Pines y revisión estática

| Recurso | SHA-256 |
|---|---|
| JIT V10 consumido | `08ced8865cffae2c46319897c98d368f45621dbe6650ff445ab701d55f546d7c` |
| Evidencia V10 | `a6bd87303def9c1b4a60f4a1e862deff73e82b20c0855d5050050654bd74da09` |
| Evidencia identidad V3 | `8e6360143d15e47c819beb540edd69bd2a08634ac85b9267d03fd61c5c5ac33a` |
| Orquestador de lectura F1 V11 | `673a37dd8b2294ced7c5fd3a5faba408537df99a75191befb9a14df21c4ba743` |
| Runner interior r9 sanitizado | `d384964d84b86b9a0c006bb819a8795950345513396860efc1168b094061fadc` |
| Runner r9 exterior | `bdef0351abfa8697cb13c788b5b3cdbb7a5568672e4c8c9d56b860826364f0a7` |
| Wrapper único WSL F1 + r9 | `fbd5f3da45c0a5b1f50c6f7f158745f2b0c886c4eac1fb1e579e54e8ac63f4dd` |
| Manifiesto del paquete r3 | `688e81efaae70a841a64cd4c0a074ae3c76c355f5ef9bc77756cff9ad607fc02` |
| Manifiesto de inputs r3 | `6b3f3d856f906cb247b792a8d89d29f4abc0422c990fa473222b9dbe89097aee` |
| Manifiesto de herramientas r2 | `4c1b3551ac9f09c56f38b441ea33b560e72419c40a942c0103fea689cb094daa` |

Validaciones de preparación: `bash -n` en los tres runners shell; compilación sintáctica del
orquestador Python en memoria; `sha256sum -c` en r3, inputs y herramientas; comparación del
manifiesto contra el candidato (**68 coincidencias, 3 auxiliares del paquete, 0 drift**);
`git diff --check`. Todos pasaron. Se revisó el orden condicional, stop-on-failure, contenedor
efímero offline para r9 y salida allowlisted. No se ejecutaron Docker, pytest, npm, lint,
typecheck, F1, r9 ni suites funcionales durante esta preparación. No hubo operaciones remotas.

La revisión es estática de este paquete; no es una revisión independiente ni un PASS runtime.
El JIT V11 está consumido: smoke combinado Go-template FAIL, antes de F1/r9. Su alcance exacto
está en el [JIT V11](../operaciones/jit_h3req1_docker_desktop_wsl_f1_v10_gated_read_and_r9_once_2026-10-09.md);
no reutilizar su aprobación. No solicitar permisos por cada archivo o hash: agrupar por objetivo.

## Resultado al cierre de esta preparación

No se ha leído F1 ni ejecutado r9. G01=10/10 y G02=10/10; G03–G10=0/10; total **20%** sin
delta. D01–D14=0/14, sin `GO_LOCAL_PR` ni `GO_DEVELOPMENT_REAL`. Los checks, aceptación UAT
144 ejecuciones/capturas y onboarding 10/10 siguen pendientes; los parciales históricos se
conservan por separado. El bootstrap CI sigue independiente, aislado y sin publicación,
instalación, enforcement remoto o despliegue.
