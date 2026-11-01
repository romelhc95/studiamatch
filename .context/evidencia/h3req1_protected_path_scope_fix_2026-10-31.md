# H3REQ1 — corrección focal del guard de scope

## Corte, autoridad y límites

- Fecha: 2026-10-31, America/Lima.
- Checkout: `/tmp/studiamatch-h3req1-protected-path-scope-fix-20261031`.
- Rama: `codex/h3req1-protected-path-scope-fix-20261031`.
- Base local y Desarrollo remoto confirmado por GitHub: `965b4862341cb4550c7833677a9675d52404fb4b`.
- Certification: `eddb5527817aa241801ee1477acb9eb1edd8a409`; main: `70d0f4fee885be0f6780e5d14f466b2a6c897961`.
- No hay commit candidato, push ni PR. El TL es responsable de abrir PRs; este paquete es solo local y no autoriza publicación.
- PRs #514/#515 y resultados remotos se reutilizan conforme al informe TL `/tmp/h3req1-certification-audit-20261031/informe-tl.md`.
- Reporte #88 / run `41241415710`: `h2-expand-compat` report-only success, 5/5 migraciones, 224 elegibles/visibles y cero pendientes; verify/apply skipped. No acredita H3 instalado en Pro.
- Aceptaciones reutilizadas, no repetidas: E1–E6 local 6/6; R1–R4 Development 4/4; smoke histórico Certification 1/1. No se combinan como porcentaje global.
- Ningún SQL remoto, workflow, configuración, deploy, cambio de ramas, merge o prueba sobre cursos reales se ejecutó en este ciclo.

## Criterio y cambio local

El fallo reproducido por TL ocurría al cambiar únicamente `.context/operaciones/h2_main_production_expand_evidence.json`: la ruta exacta quedaba fuera de la allowlist del guard. También se consumían pins de promoción congelados al validar un baseline distinto de aquel para el que fueron aprobados.

El cambio:

1. Permite solo la ruta exacta de evidencia H2 Main. El contenido sigue sujeto al gate independiente `h2-main-production-expand-gate` de `security-audit.yml`.
2. Consume los pins congelados de Certification solo con baseline `03515dee69fc42b10808d1c67cc4e00ebacd0c40`, tanto en PR como en push.
3. Consume los pins congelados de main solo con baseline `70d0f4fee885be0f6780e5d14f466b2a6c897961`, tanto en PR como en push.
4. Para baselines posteriores conserva las allowlists ordinarias y no añade rutas de esos pins históricos.
5. Mantiene controles de schema, ruta segura y única, source SHA, ancestría, blobs de baseline/source, árbol de HEAD y rechazo de drift. Los vecinos del path H2 siguen rechazados.

La prueba del gate de contenido main ahora fija regresiones estáticas de schema, manifest, operación, verify, advisors, ancestry y artifact. No se modifica ni se relaja el gate.

## Inventario local exacto

| Path | Propósito |
|---|---|
| `scripts/security/protected_path_scope_guard.sh` | Path exacto de evidencia y consumo de pins solo en su baseline aprobado. |
| `tests/test_protected_path_scope_guard.sh` | Callers PR/push de Certification y main, baselines posteriores, drift, vecinos y validaciones acumuladas. |
| `tests/test_fase10_main_boundary.py` | Regresión del gate semántico H2 Main independiente. |
| `.context/trazabilidad/registro_fuentes_componentes.json` | Relaciones fuente, controles, consumidores y evidencia. |
| `.context/trazabilidad/registro_fuentes_componentes.md` | Proyección renderizada del registro canónico. |
| `.context/componentes/seguridad_tooling.md` | Contrato del guard, límites y evidencia final. |
| `.context/estado_del_proyecto.md` | Corte operativo y siguiente gate. |
| `.context/indice.md` | Entrada canónica Obsidian. |
| `.context/evidencia/h3req1_protected_path_scope_fix_2026-10-31.md` | Este checkpoint y borrador para revisión TL. |

No se incluyeron WIP de otros checkouts, datos, secretos ni archivos generados de build.

## Validación local final

Docker aislado, sin red, sin volúmenes ajenos. El candidato se montó desde el checkout aislado; el contenedor inicial no llegó a ejecutar tests porque su entrypoint requería `node_modules` de otro checkout. Se repitió con la misma imagen y `bash` como entrypoint; el intento inicial no se contabilizó como test.

| Gate | Resultado observado | Evidencia y límite |
|---|---|---|
| `bash -n` sobre los dos scripts afectados | PASS | Sintaxis de `protected_path_scope_guard.sh` y `test_protected_path_scope_guard.sh`. |
| `tests/test_protected_path_scope_guard.sh` | PASS | 1196 paths, 13 catálogos/1173 referencias; caller real PR/push para ambas rutas de promoción; pins históricos en baseline exacto; baseline posterior no consume pins; source/content drift fail-closed; path exacto admitido y vecinos rechazados. |
| `tests/test_fase10_main_boundary.py` | PASS | Aserciones del contenido semántico del gate H2 permanecen presentes. |
| ShellCheck v0.11.0 | PASS | Ambos scripts afectados, imagen Docker dedicada, sin red. |
| Regresiones del credential scanner | PASS en snapshot anterior | Suite sintética pasó con tmpfs `exec`; el primer intento falló al ejecutar hook sintético desde `/tmp` con `noexec`, antes de aserciones. El scanner del árbol final también pasó en la fila siguiente. |
| Scanner sobre árbol candidato y checkpoint nuevo | PASS | `scan_credentials.sh --tree` para paths rastreados y `scan_credentials.sh <checkpoint>` para el archivo nuevo, Docker sin red. Un intento previo usó un flag inexistente (`--files`) y el scanner lo rechazó antes de leer; la invocación corregida pasó. |
| Comparación acumulada feature→Development | PASS para mismo set de paths | Comparador contra baseline Development `965b4862…`, commit desechable. La edición posterior cambió contenido documental, no el set/path evaluado. |
| Comparación acumulada Development→Certification | PASS para mismo set de paths | Comparador contra Certification `eddb5527…`, tree desechable. No es SHA publicado. |
| Comparación acumulada Certification→main | PASS para mismo set de paths | Tree de merge de prueba contra main `70d0f4fe…`, fixture desechable. No es SHA publicado. |
| `git diff --check` | PASS | Diff rastreado PASS en Docker. El archivo nuevo se comprobó con `git diff --no-index --check /dev/null <checkpoint>`: salida vacía; exit 1 esperado por la diferencia del archivo nuevo. |
| Checker integral, baseline vs candidato | FAIL 348→348; delta 0 | Checker versionado sin modificar, misma imagen/configuración, Docker sin red; ambos retornan 1 por FAIL integral. Las listas exactas actuales están en `/tmp/h3req1-protected-path-scope-evidence-20261031/{baseline-diagnostics-v2-exact.txt,candidate-diagnostics-v2-exact.txt}` (SHA-256 idéntico `738e442d6b13b3f604376a3f274747b8208f389fa3c2712e535d5fa015527a92`); `diagnostic-delta-v2.diff` está vacío. La extracción sin truncamiento usó una copia temporal que solo cambió root y límite de impresión; no cambió reglas. El candidato añade un checkpoint alcanzable y dos links al resumen, sin añadir/resolver diagnósticos. |
| Self-test documental | PASS acotado; comando envuelto exit 1 | El árbol candidato produjo `DOC_SELF_TEST_PASS`; el mismo comando ejecuta también el gate integral que permanece FAIL 348, de ahí el exit 1. |
| Candidate-aware de este candidato | NO EJECUTADO | No se reclama PASS. Los resultados candidate-aware de candidatos anteriores no se reutilizan. |
| CI/Actions, promoción, Pages, runtime Pro | NO EJECUTADO | No hay PR ni autorización remota en este ciclo. |

Tras el rechazo instrumental inicial, el responsable restauró el permiso normal de Docker. Se usó la imagen del proyecto con `--network none`; no se cambió `docker.sock` ni se usó otro runtime. Render, scanner, diff-check, checker integral y self-test se ejecutaron sobre el árbol final. El checkpoint no versionado se escaneó aparte. El checker normal imprimió 200 de 348 diagnósticos y su resumen “148 more”; para cotejo se extrajo la lista completa sin cambiar su lógica. El delta exacto de fallos es cero. Logs/listas quedaron en `/tmp/h3req1-protected-path-scope-evidence-20261031/`.

## Antes → después y revisión de seguridad

| Caso | Antes | Después |
|---|---|---|
| Evidencia H2 Main exacta dentro del diff | Rechazada por ruta fuera de allowlist | Admitida únicamente por path exacto; el gate de contenido sigue independiente. |
| Pins Certification/main sobre el baseline aprobado | Validación histórica con caller rígido | Siguen disponibles en PR y push solo para el baseline exacto aprobado. |
| Pins sobre baseline posterior | Podían invocarse/requerirse pese a que el estado remoto ya avanzó | No se consumen; operan allowlists normales y los paths ajenos se rechazan. |
| Rutas vecinas y drift de pins | Debían conservar rechazo | Negativos de caller real y checker siguen fail-closed. |

Revisión focal del diff: no cambia Auth, membresías, datos, SQL, runtime de producto, gates de contenido ni permisos GitHub. La admisión de la ruta de evidencia no la considera válida por sí sola. Los pins mantienen source, ancestría, blobs y tree; cambiar baseline no crea una excepción nueva. No se observaron hallazgos HIGH/CRITICAL en este diff. Esta revisión por impacto no es auditoría global, ejecución de Actions ni aprobación de promoción.

## Gate documental y disposición pendiente

Resultado integral verificado con el mismo checker/configuración: 348 diagnósticos en baseline y candidato, sin delta. El FAIL heredado sigue visible. La causa residual demostrada es la deuda documental histórica (rutas/fuentes retiradas y exclusiones/relaciones heredadas), que no se corrige recreando archivos privados ni eliminando relaciones en masa.

**Propuesta sin aprobar y sin efecto de waiver:** disposición limitada al candidato local de esta rama para tramitar integración protegida a Desarrollo. Evidencia: logs completos baseline/candidato y delta vacío bajo `/tmp/h3req1-protected-path-scope-evidence-20261031/`; base exacta `965b4862341cb4550c7833677a9675d52404fb4b`; nueve paths enumerados arriba. Causa: referencias históricas a fuentes retiradas no recuperables desde Git/copia autorizada. Riesgo: trazabilidad histórica incompleta; no se encontró impacto funcional atribuible al delta. Owner propuesto: Romel/TL. Vencimiento propuesto: 2026-11-05 23:59 America/Lima o antes de integrar este candidato, lo que ocurra primero. No autoriza commit, push, PR, review, merge, Certification, main, SQL, workflows, configuración ni deploy. Requiere decisión humana expresa; ninguna disposición anterior se extiende a este candidato.

## Transición, recuperación y estado

| Fase | Aplicación a este cambio |
|---|---|
| Expand | Añade el path exacto de evidencia H2 y condiciona los pins a sus baselines aprobados. |
| Compatibilidad | PR/push con baseline congelado conserva el scope previamente aprobado. Baselines posteriores siguen el allowlist ordinario; el gate de contenido mantiene el mismo contrato. |
| Deploy | Solo tras revisión y merge por flujo protegido. No se ejecutó deployment. |
| Contract | No hay cambio de producto ni contrato runtime legacy a retirar. |
| Rollback | Revertir el cambio mediante PR protegido restituye el comportamiento anterior del guard. No hay efecto de datos ni recuperación DB. |
| No degradación | Tests focales, negativos y comparaciones de tres baselines PASS en Docker; no sustituye CI ni smoke remoto. |

Estado: **GO técnico local del delta acotado**: código, negativos, ShellCheck, scanner, diff-check, render y self-test ejecutados en Docker; sin HIGH/CRITICAL observados en la revisión focal. El gate integral permanece **FAIL 348→348, delta cero** y la disposición específica continúa pendiente; por eso **NO-GO para publicar** hasta resolver esa decisión. No hay GO para Certification/main/producción; H3 en Pro y cierre productivo siguen sin acreditarse.

## Borrador de PR para el TL — plantilla versionada completada

### Resumen

Corrección focal del scope guard de H3REQ1: permite el archivo de evidencia H2 Main exacto sin sustituir su validación semántica y limita los pins congelados de Promotion Scope al baseline aprobado, para eventos PR y push. Rama `codex/h3req1-protected-path-scope-fix-20261031`, base `desarrollo@965b4862341cb4550c7833677a9675d52404fb4b`; candidato aún local/sin commit. No cambia producto, datos o SQL. La disposición documental integral de este candidato sigue pendiente de aprobación. Referencias: estado operativo y este checkpoint; no se incluye fuente privada de cliente.

### Evidencia de este PR

Validaciones locales ejecutadas el 2026-10-31 en Docker sin red sobre el checkout aislado: guard, contrato H2 main, ShellCheck, comparaciones de callers contra los tres baselines, scanner, diff-check, render y self-test PASS. El checker integral mantiene FAIL 348→348, delta cero; su código de salida 1 refleja ese FAIL, no un fallo de self-test. No se ejecutaron CI, Actions, SQL, workflows, smoke, promoción ni deploy. Las pruebas E1–E6 6/6, R1–R4 4/4 y smoke histórico Certification 1/1 se citan como aceptaciones previas reutilizadas, no se repitieron ni son tests de este diff. Logs/listas: `/tmp/h3req1-protected-path-scope-evidence-20261031/`.

### Avances del cambio

| Componente/contrato | Cambio implementado | Consumidores/impacto | Evidencia |
|---|---|---|---|
| Scope guard | Admite path H2 exacto; pins solo para baseline aprobado, PR/push. | CI local de selección de paths y gate de contenido main permanece independiente. | Guard/callers/negativos y acumulados PASS en Docker. |
| Trazabilidad | Registro, ficha, estado, índice y checkpoint actualizados. | Mantenimiento documental del contrato de seguridad/tooling. | Render y self-test PASS; checker integral FAIL 348→348 sin delta. |

### Pilares obligatorios

| Pilar | Estado | Resultado validado y límites |
|---|---|---|
| Funcionalidad | PASS acotado | Regresiones de selección/pins y gate H2; no es aceptación runtime. |
| Escalabilidad | N/A | No cambian rutas, datos, consultas ni carga del producto. |
| Seguridad | PASS acotado | Revisión focal sin HIGH/CRITICAL y scanner del árbol candidato PASS; no es auditoría global. |
| Mantenimiento | PASS acotado | Registro/ficha/estado actualizados; residual documental integral sigue FAIL. |
| Calidad | PASS acotado; integridad documental FAIL heredado | ShellCheck, suites focales, comparación de paths, render, self-test y whitespace PASS; checker integral 348→348 con delta cero. |
| Rendimiento | N/A | No cambia runtime de producto. |

### Transición transparente

| Fase | Alcance/resultado real | Evidencia/autorización |
|---|---|---|
| Expand | Allowlist exacta y condición por baseline. | Local; sin efectos remotos. |
| Compatibilidad | Baseline histórico conserva pins; baseline sucesor usa allowlists normales y gate semántico sin cambios. | Tests PR/push y fixtures acumulados PASS. |
| Deploy | No ejecutado. Requiere revisión y flujo protegido. | No autorizado por este ciclo. |
| Contract | No aplica a runtime de producto; no hay legacy nuevo que retirar. | Sin cambios de comportamiento. |
| Rollback/recuperación | Revert del diff mediante PR protegido; retorna a la denegación previa. | No modifica DB ni datos. |
| No degradación funcional | Solo contrato de path guard comprobado localmente; aceptación funcional remota no se repite ni se reclama. | Resultados locales y límites anteriores explícitos. |

### Evidencia para cliente

Este fix de tooling no altera criterios funcionales H3REQ1. Se conservan por referencia E1–E6 local 6/6, Development R1–R4 4/4 y Certification 1/1; no se mezclan con los tests de esta rama. H3 en Pro, promoción a main y cierre productivo no acreditados. La disposición propuesta para el residual integral es pendiente de aprobación y solo cubriría tramitar este candidato a Desarrollo.

### Validaciones

| Validación | Resultado/exit/casos | Ambiente/grado | Evidencia/límites/owner |
|---|---|---|---|
| Credential scan | PASS sobre el árbol rastreado y el checkpoint nuevo. | Docker sin red. | No escanea secret stores; solo patrones y archivos del repositorio. |
| Python tests | PASS `test_fase10_main_boundary.py`; bloques Python del guard incluidos en suite Bash PASS. | Docker sin red. | Suite focal, inputs y fixtures descartables. |
| Python compile | N/A | No hay archivos Python de runtime modificados. | No ejecutado ni requerido para este diff. |
| PostgreSQL DB Change Gate | N/A | No hay SQL ni DDL. | No se conectó a DB. |
| ESLint | N/A | Sin UI/JavaScript de producto. | Sin cambios frontend. |
| TypeScript | N/A | Sin TypeScript. | Sin cambios frontend. |
| Static build | N/A | Sin build de producto. | No cambia artefactos Pages. |
| actionlint / ShellCheck | ShellCheck PASS; actionlint N/A | Docker sin red. | No se modificó YAML/workflow. |
| UAT/runtime/integración | N/A para producto | No se ejecutó entorno remoto. | Reutiliza aceptación previa; no prueba este guard. |
| security-audit / CI independiente efectivo | PENDIENTE | No existe PR del candidato. | TL abrirá PR solo después de decisión/disposición y autorización separada. |
| CodeQL | PENDIENTE / aplicabilidad por CI | No disparado. | Sin PR ni CI en este ciclo. |
| Cloudflare Pages / smoke preview | N/A | No hay cambio de producto ni deploy. | No ejecutado. |
| Browser snapshot | N/A | Sin UI. | No ejecutado. |
| security-auditor | PASS focal por impacto | Revisión estática de este diff. | Sin HIGH/CRITICAL observados; no auditoría global ni CI. |
| Documentación / trazabilidad / fuente cliente | Render y self-test PASS; integral FAIL 348→348, delta cero. | Checker versionado y configuración iguales en baseline y candidato, Docker sin red. | Disposición nueva para este candidato pendiente; no se reutiliza waiver anterior. |

### Seguridad y datos

- La revisión focal del diff no encontró hallazgos HIGH/CRITICAL; el escaneo de credenciales del árbol rastreado y del checkpoint no versionado pasó en Docker sin red.
- El gate semántico H2 permanece independiente; la ruta permitida no valida contenido.
- No cambia identidad, roles, API, DB, claves, datos ni secretos.
- Ningún SQL, workflow, configuración, PR, merge, despliegue o smoke remoto está autorizado o ejecutado aquí.

### Alcance y límites

El diff contiene únicamente los nueve paths enumerados en este checkpoint. El checkout de origen con WIP ajeno no participa. Base observada: Development `965b4862341cb4550c7833677a9675d52404fb4b`. El TL debe anclar la revisión al hash final del patch y no hereda approvals ni waivers anteriores. La parte técnica local está validada; la disposición pendiente bloquea publicación y las promociones siguen pendientes.

### Checklist técnico

- Las suites focales y gates locales del árbol final están ejecutados. El checker integral conserva FAIL; la disposición de este candidato requiere decisión humana antes de publicar.
- Relaciones, ficha, estado e índice actualizados; sin reducir el checker.
- Pilares y `expand -> compatibilidad -> deploy -> contract` y rollback descritos; fases remotas no ejecutadas.
- CI requerido, aprobación humana, merge y promoción deben evaluarse por separado sobre el SHA que publique el TL.

## Siguiente acción exacta

1. El TL revisa la huella/diff y decide la disposición documental pendiente para estos nueve paths y esta base; el checker integral permanece FAIL.
2. Si se aprueba la disposición, el TL obtiene por separado autorización de commit, push no forzado y PR a Desarrollo; esta sesión no los ejecutó.
3. Tras PR, revisar CI y aprobación; merge requiere instrucción separada. No ejecutar SQL/workflow verify/Pro ni promover a Certification/main bajo este checkpoint.
