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

## Corte histórico — evidencia auténtica del verify H2 Pro, run 89 (anterior al guard actualizado)

Esta sección actualiza el estado posterior al PR #517 integrado. No reescribe los resultados/disposición del paquete local del 2026-10-31 que anteceden a esta sección.

### Identidad y procedencia

- Fecha: 2026-11-01, America/Lima.
- Refs GitHub leídas: Desarrollo `9c2e227078ca75714a215f7f0f43be3b837bda69`; Certification `15fdc8dc97933dcc6a77dff65d6b293faadeb2ee`; main `70d0f4fee885be0f6780e5d14f466b2a6c897961`.
- PR #517 integrado en Certification; `15fdc8d` conserva `9c2e227` como ancestro y ambos tienen el árbol `8fd6932b81dfb2d86d355d13ebcf5bd98676bcce`.
- Deployment normal de Certification: `8960fc62-0fd8-4760-87c9-1c0b682c8e75`, SUCCESS, host `certificacion.studiamatch-aty.pages.dev`.
- Ejecución correcta: [DB Sync to Production, run 41274863913](https://github.com/romelhc95/studiamatch/actions/runs/41274863913), evento `workflow_dispatch`, ref `certificacion`, SHA `15fdc8dc97933dcc6a77dff65d6b293faadeb2ee`. El enlace `41241415710` corresponde al reporte 88, no a este verify.
- Artefacto autenticado: [ID 13070419512](https://github.com/romelhc95/studiamatch/actions/runs/41274863913/artifacts/13070419512), digest GitHub `sha256:2bc61bde47b79ae30876c3b1d71598e3a3fc70f56a22c90f4bc2be17f1c3ecef`. El TL conserva el ZIP íntegro y sus tres miembros en `/tmp/h3req1-tl-audit-20261101/`; no se versiona el ZIP ni los cuerpos crudos de advisors.

### Ejecución y resultado

- Run SUCCESS: 6 jobs SUCCESS, 1 SKIPPED.
- `Apply pending migrations` confirmó verify como NO-OP; `Apply migrations to Pro` quedó SKIPPED. No se aplicó SQL.
- `Verify target schema` SUCCESS; el log informa `Target schema check PASSED` para `h2-expand-compat`.
- Cohorte: 224 elegibles/visibles, digest `sha256:c217dbffc9d50cca0e1f111fcddf1268db9a34e8671a409f3663dcfff1d735e9`.
- H2 está verificado para el candidato y entradas de este run. No se acredita instalación H3 en Pro.

### JSON canónico y artefactos

El ZIP contiene exactamente `h2-production-expand-verify-evidence.json`, `supabase-security-advisors.json` y `supabase-performance-advisors.json`. Sus SHA-256 son, respectivamente, `d38900871fcdf075a9ce7111820cf27757c26cf854d439cada1bbb52750be41c`, `8e13f3e73e681931a7fe55bcdd6891a2d009cdc680834c56ad07b6fb5690c1f9` y `f484e558056b6590366dd2782f8f23e48f622fa7c7ffa8921e803ce9cb5978ac`.

`.context/operaciones/h2_main_production_expand_evidence.json` se sustituyó byte por byte desde el JSON autenticado. El campo `operation=apply` se conserva sin editar porque lo exige el contrato histórico del gate main. El dispatch remoto fue `verify`: Apply fue NO-OP y la aplicación de migraciones quedó skipped. No se modificaron generador, workflow ni schema de evidencia.

Security Advisors registra 3 INFO y 9 WARN; Performance Advisors, 16 INFO y 1 WARN. No reportan HIGH/CRITICAL dentro de esos artefactos. No es una auditoría global ni una afirmación de ausencia general de vulnerabilidades.

### Antes → después y límites

Antes, el JSON versionado apuntaba al candidato `93c802c7b0af2339a50ba3b4526fced9e1b3f7fd` y run `33143730910`. Después, su contenido es idéntico al miembro autenticado del run `41274863913` y apunta a `15fdc8dc97933dcc6a77dff65d6b293faadeb2ee`. E1–E6 local 6/6, R1–R4 Development 4/4 y smoke histórico Certification 1/1 permanecen aceptados y no se repitieron.

La edición local de este corte se limita a evidencia/estado/registro; no cambia código, producto, DB, cuentas, configuración ni runtime. La rama `codex/h3req1-verify-evidence-20261101` parte de Desarrollo `9c2e227…` y avanzó por fast-forward local hasta `15fdc8d…`, preservando el SHA verificado como ancestro. El checkout WIP original no fue alterado.

### Validación del paquete documental final

El árbol de prueba usó el mismo contenido de los seis paths modificados en un fixture Git descartable derivado de `15fdc8dc97933dcc6a77dff65d6b293faadeb2ee`. El fixture no es candidato remoto ni forma parte del paquete; `15fd` sigue siendo ancestro del contenido probado.

- `scan_credentials.sh --tree` y `--diff 15fd..fixture`: PASS; `git diff --check`: PASS; `--render`: PASS.
- Guard real sobre las rutas del árbol: feature→Development (baseline `9c2e227…`), Development→Certification (baseline `15fdc8d…`) y acumulado Certification→main (baseline `70d0f4f…`): PASS en cada llamada.
- Selector extraído byte por byte del bloque vigente en `.github/workflows/security-audit.yml`: PASS para las tres rutas. En Certification→main creó un agregado de 4 paquetes/1.628 paths. El checker candidate-aware informó `DOC_SELF_TEST_PASS` y `DOC_GATE_PASS`, con 752/752 fuentes asignadas, 120/120 documentos activos alcanzables y 433/433 históricos enlazados. Es un PASS acotado del candidato local, no PASS integral ni GO remoto.
- Checker integral sin cambiar reglas/configuración, mismo SHA del script baseline/candidato `f2a95870de748b2e59ee0d988abb0b16125da47c996a7f85841f1113fcebbb75`: FAIL en ambos, 348 diagnósticos baseline y 348 candidato; conjunto no truncado comparado, 0 introducidos/0 resueltos. El self-test interno pasó; exit 1 refleja el FAIL integral.
- Para obtener el multiconjunto completo se usó una copia efímera del mismo checker que solo parametrizó el root y retiró el límite de impresión de 200 filas; no cambió reglas ni lógica. La ejecución normal versionada sigue mostrando el FAIL integral en ambos árboles.
- ZIP autenticado del run 89: digest `2bc61bde47b79ae30876c3b1d71598e3a3fc70f56a22c90f4bc2be17f1c3ecef`, exactamente 3 miembros. El miembro JSON y el canónico son byte idénticos (`d38900871fcdf075a9ce7111820cf27757c26cf854d439cada1bbb52750be41c`). Los hashes de Security/Performance Advisors coinciden con el checkpoint y sus cuerpos no se versionan. El gate main local conserva lectura de metadatos reales del run, exige los jobs `Apply pending migrations`/`Verify target schema` satisfactorios y compara los tres miembros del ZIP; esos datos del run 89 se reutilizan del informe TL y no se generó otra ejecución.
- Revisión de seguridad por impacto: los seis cambios son documentación/evidencia; el JSON se obtuvo byte por byte del artefacto verificado, no se añadieron cuerpos de advisors, secretos ni datos personales. Scanner árbol/diff PASS; no se identifican hallazgos HIGH/CRITICAL en este delta documental. Esto no es un scan global.
- Scanner, diff-check, render, los tres guardas, los tres selectores y el contrato del artefacto quedaron en PASS. El arranque ordinario de la imagen detuvo el contenedor por desajuste de manifests Node antes de ejecutar checks; no cuenta como fallo de prueba. Los checks documentales sí corrieron en `studiamatch-dev:local`, red deshabilitada y sin aplicación/volúmenes/secretos. Logs sanitizados: `/tmp/h3req1-run89-checks-20261101/`.

### Deuda documental y disposición propuesta

El residual integral está demostrado en baseline y candidato: 88 `RELATION_PATH_MISSING`, 79 `SOURCE_PATH_MISSING_OR_OUT_OF_SCOPE`, 79 `SOURCE_PATH_MISSING`, 79 `CANDIDATE_ONLY_PATH_MISSING`, 15 `EXCLUSION_PATH_MISSING`, 4 `DOC_EXCLUSION_STALE` y 4 `DOCUMENT_EXCLUSION_PATH_MISSING`. Son referencias históricas de fuentes/relaciones ausentes o retiradas; el delta no añade ni resuelve diagnósticos. Riesgo: trazabilidad histórica incompleta; no se observó impacto funcional atribuible al paquete. Propuesta pendiente, no aplicada: owner Romel/TL; vencimiento 2026-11-05 23:59 America/Lima o antes de integrar este paquete en Development, lo que ocurra primero; alcance solo disponer este residual para que el TL pueda solicitar la integración protegida de este paquete documental exacto a Development. No convierte el FAIL en PASS y no cubre Certification, main, producción, SQL, workflow ni configuración. El TL debe solicitar por separado autorización de commit/push/PR; el merge requiere su decisión independiente.

Transición: expand = incorporar la evidencia auténtica en su ruta canónica; compatibilidad = conservar el path/schema y la validación independiente del gate; deploy = PRs protegidos creados por el TL, con review/merge por ambiente; contract = no aplica hasta instalación/verificación H3 Pro y despliegue BFF/Pages; rollback = revert documental por flujo protegido, sin borrar ZIP, auditorías, ledger ni datos. Siguiente etapa: preparar el candidato real Certification→main y su disposición/gates propios; H3 Pro y Pages/BFF tienen JIT separados. No activar FG1/FG2/FG3, writers, schedules ni H4.

## Corrección del checkout del gate main — 01-nov-2026

Después del merge de PR #518, Desarrollo está en `893f41fa8ef9f6ee9ad6799824a48abc0bf922c3`.
La revisión previa de contenido había usado Git con historial completo. Una prueba
adicional con el checkout real depth 1 y el fetch vigente de PR/main demuestra
que el objeto `15fdc8dc97933dcc6a77dff65d6b293faadeb2ee` no está disponible:
`git cat-file -e ...^{commit}` falla. Es un bloqueo del gate, no un fallo de H2.

El cambio mínimo es `fetch-depth: 0` en el checkout de
`h2-main-production-expand-gate`; se conserva `persist-credentials: false`, ref
exacta, ancestry, allowlist y validación de ejecución/jobs/artefacto. La regresión
`test_h2_main_gate_checkout_resolves_verified_ancestor` deriva profundidad y fetch
del YAML, usa un remoto `file://` y prueba un candidato padre de HEAD no apuntado
por otra ref: RED con el checkout anterior y GREEN con el fix. Las 16 funciones
de `test_security_flow.py` pasaron en Docker sin red. La reproducción remota Git
también resolvió el candidato y su ancestry al recuperar el historial completo.

Revisión security-auditor focal de workflow/test: cero HIGH/CRITICAL/P1/P2.
No altera el JSON auténtico del run 89 ni requiere volver a ejecutarlo: workflow,
test_security_flow y documentación están expresamente permitidos por la regla de
cambios posteriores al verify. El paquete nuevo conserva sus propios gates y
requiere autorización específica de publicación; la promoción de `893f41f` quedó
sin crear para no llevar un fallo conocido hacia main. No se ejecutaron PR,
push, merge, SQL, workflows ni configuración por este fix local.

Expand: recuperar historial para resolver el ancestro. Compatibilidad: mismos
contratos/artefactos y validaciones. Deploy: flujo protegido. Contract: sin legacy
de producto nuevo. Rollback: revert protegido del fix, sin datos que restaurar.
El integral histórico sigue separado del gate acotado; los resultados finales
reproducibles se adjuntan al paquete TL antes de solicitar publicación.


# Admisión exacta de autorización H3 Pro — checkpoint local

## Alcance

Admitir en el scope guard una sola ruta del archivo DDL H3 Pro y probar que su
estado de borrador no satisface el apply gate. No se cambian workflows, SQL,
producto o ambiente. No se ejecuta SQL remoto, dispatch, configuración,
secreto, commit, push, PR, merge o deploy.

La autorización H3 está en
[`DDL-H3-EDITORIAL-EXPAND-PRO-20261101.md`](../operaciones/ddl_authorizations/DDL-H3-EDITORIAL-EXPAND-PRO-20261101.md)
y permanece `DRAFT_NOT_AUTHORIZED`.

## Identidad del checkout

- Refs observadas por GitHub MCP: Development `ca63eb4d82bfb1d34f7c7b753942a93039cfe2bc`, Certification `15fdc8dc97933dcc6a77dff65d6b293faadeb2ee`, main `70d0f4fee885be0f6780e5d14f466b2a6c897961`.
- Checkout aislado: `/tmp/studiamatch-h3req1-ddl-auth-admission-20261101`.
- Rama local: `codex/h3req1-ddl-auth-admission-20261101`.
- Base/HEAD antes del cambio: `ca63eb4d82bfb1d34f7c7b753942a93039cfe2bc`; árbol `41b26e41cecb9e2a1e72de39e5c0e7a247bd9ed5`.
- Historia completa; el checkout fuente con WIP no se modificó.

## Relaciones y consumidores

- `scripts/security/protected_path_scope_guard.sh`: una ruta literal en
  `allowed_h3_local`; sin patrón de directorio.
- `tests/test_security_flow.py`: invoca el guard real para el
  positivo exacto y vecinos/ID distinto; la ruta traversal se evalúa contra el
  matcher exacto. Git no representa segmentos de path `..` en árboles.
- `.github/workflows/db-sync-to-pro.yml`: el apply exige el estado autorizado
  exacto, valida identidad/gates/ancestría y requiere que el diff posterior al
  payload sea exactamente el archivo de autorización.
- `tests/test_security_flow.py`: regresiones sobre los comandos de
  estado y diff del workflow real en fixtures Git sintéticos.
- La navegación, ficha de seguridad, ficha de migraciones y el registro
  fuente-componente enlazan el borrador y sus consumidores.

## Resultados históricos de Luna (antes de la corrección TL)

Contenedor `studiamatch-dev:local`, red `none`, checkout montado en `/workspace`;
no se inició la app ni se conectó a DB. Logs reproducibles en
`/tmp/h3req1-ddl-auth-admission-20261101-logs/`.

- `tests/test_security_flow.py`: 11/11 funciones PASS ejecutadas por un
  runner de funciones en Python dentro del contenedor porque la imagen no
  incluye pytest. Las pruebas invocan el guard real en repos Git temporales y
  extraen del workflow real sus checks de estado, ID y cambio posterior a `P`.
- Admisión: el path literal exacto pasa el guard; ID distinto/vecino se rechaza.
  El matcher no admite el directorio. El DRAFT real falla el `grep` de estado
  aprobado; un archivo adicional después de `P` falla el comparador exacto.
  El ID con traversal falla el regex del workflow. La única prueba positiva de
  estado aprobado usa un archivo sintético temporal y no confiere autoridad.
- `bash -n` sobre guard y suite shell: PASS.
- Scanner de credenciales del árbol y de los paths modificados/nuevos: PASS.
- Render del registro fuente-componente: PASS. `git diff --check` y check de
  los dos documentos nuevos: PASS.
- Suite amplia `tests/test_protected_path_scope_guard.sh`: FAIL antes de llegar
  a las regresiones por una referencia heredada. Falla igual en candidato y en
  checkout full-history del baseline `ca63eb4…`: espera que
  `.context/componentes/admin_portal.md` exista en el commit histórico
  `8ac174d81cf6ce23658bff132236a78935ace1ad`, donde no existe. No se cambió la
  suite ni el guard para ocultar este fallo.
- ShellCheck: no disponible en la imagen Docker; queda como check de CI.
- Checker integral: FAIL 348 en baseline y 348 en candidato; las líneas
  `DOC_GATE_FAIL` son idénticas. El grafo registra las dos nuevas páginas y
  tres enlaces adicionales; no aparecen diagnósticos nuevos ni resueltos.
  `DOC_SELF_TEST_PASS` está presente en ambas ejecuciones. El comando total
  conserva exit 1 por el FAIL integral. No se ejecutó gate candidate-aware para
  este paquete y no se lo presenta como PASS.
- Codex Security diff scan completado: `8e2f7b24-fd9b-4cd9-8b60-73d9e2929ad5`,
  cero hallazgos reportables y 3/3 superficies `no_issue_found` en el diff
  acotado. Informe generado en
  `/home/romel/.codex/state/plugins/codex-security/scans/studiamatch-h3req1-ddl-auth-admission-20261101/ca63eb4d82bfb1d34f7c7b753942a93039cfe2bc_20261101T075339Z_qdambcof/report.md`.
  Daybreak devolvió `not_granted`; el informe está disponible en este
  workbench, aunque su visualización protegida fuera de él puede estar limitada.
  El inventario normalizado del workbench mostró dos items; los 10 paths del
  diff se revisaron directamente. Esto no es auditoría global ni validación
  remota, y no demuestra ausencia global de vulnerabilidades.

No reutilizar run 89 para el candidato que incluya este guard. Sus resultados
H2 fueron obtenidos sobre un SHA anterior a este cambio. El FAIL integral y
cualquier PASS acotado se reportarán por separado; este checkpoint no concede
disposición documental.

## Secuencia sin ejecución remota

1. Integrar el guard y sus relaciones a Development y Certification.
2. En el SHA real de Certification con el guard, obtener report y verify H2
   nuevos con autorizaciones independientes; no reaplicar H2.
3. Integrar JSON auténtico, pins y documentación antes de congelar `P`.
4. Tras decisión humana y JIT específico, cambiar únicamente este archivo de
   DDL; mantener el resto del payload inmutable.
5. Continuar por promociones protegidas; SQL y despliegues requieren sus
   aprobaciones respectivas.

## Reversión

El cambio local es reversible al revertir los cambios exactos de esta rama.
Antes de integrar no modifica datos ni entornos. Si se integra y surge un
problema, el rollback es un revert protegido del guard y de su documentación;
no se amplía el alcance ni se altera el estado de Pro.

## Corrección y validación independiente TL — 01-nov-2026

Los resultados anteriores de Luna son antecedentes del paquete revisado, no
sus resultados finales. El TL reprodujo tres defectos de preparación: checkpoint
nuevo fuera de scope, regresiones fuera de la lista CI y una aserción que exigía
que el documento real permaneciera en DRAFT incluso tras un JIT válido.

El paquete corregido usa este checkpoint ya admitido, mantiene únicamente el
nuevo path DDL literal en el guard y coloca las regresiones en
`tests/test_security_flow.py`, ya incluido en CI. Los casos de DRAFT y aprobado
usan fixtures; no cambian ni autorizan el documento operativo real.

Docker desechable, red deshabilitada, sin iniciar app ni DB:

- 20/20 funciones de security_flow PASS con el documento DRAFT actual y 20/20
  con estado aprobado simulado únicamente en el fixture de prueba.
- Suite histórica de scope PASS en baseline y candidato. Su fallo previo se
  debía a blobs faltantes del clon parcial: se recuperaron 28 blobs por Git de
  solo lectura. La suite histórica no se modificó ni se exceptuó.
- Paquete completo: scope guard, selector YAML real y gate documental
  candidate-aware/self-test PASS en Desarrollo, Certification y main.
- Render, scanner árbol/diff y diff-check PASS. El integral conserva FAIL con
  348 diagnósticos en ambos árboles, sin diagnósticos nuevos. No es PASS integral.
- Revisión focal independiente de los cambios de código: cero hallazgos
  HIGH/CRITICAL/P1/P2; no auditoría global ni validación remota.

Checkout TL: `/tmp/studiamatch-h3req1-ddl-auth-tl-fix-20261101`, baseline
`ca63eb4d82bfb1d34f7c7b753942a93039cfe2bc`. Evidencia reproducible y fixtures
en `/tmp/h3req1-tl-review-admission-20261101/`. Los commits de los fixtures son
sintéticos; no son commits de publicación ni autorizaciones productivas.

No se publicó el paquete ni se repitió UAT aceptada. La admisión de la ruta no
autoriza DDL. El nuevo verify H2, evidencia auténtica antes de P y JIT posterior
siguen pendientes de las integraciones y decisiones humanas correspondientes.


## Continuación 2026-11-01 — evidencia autenticada H2 verify run 91 y paquete desde Desarrollo

### Candidato y procedencia

- PR #521 quedó integrado; HEAD revisado del PR `64c23fd8a9694f50a2728399bf8e35771bf56fad` y merge SHA Certification `605a6ecca29e20ade8cac3874d380758d18e6a11`.
- Refs del corte: Desarrollo `64c23fd8a9694f50a2728399bf8e35771bf56fad`, Certification `605a6ecca29e20ade8cac3874d380758d18e6a11`, main `70d0f4fee885be0f6780e5d14f466b2a6c897961`. El deployment normal de Certification `ac707175-75a9-4c5a-9c6b-0786a6a0d517` terminó SUCCESS.
- Trabajo local: clon limpio iniciado desde Desarrollo 64c23fd en `/tmp/studiamatch-h3req1-run91-evidence-20261101`, rama local `codex/h3req1-run91-evidence-20261101`. El checkout histórico con WIP y los checkouts del TL no se editaron.

### Run #91 autenticado

El [DB Sync to Production run #91](https://github.com/romelhc95/studiamatch/actions/runs/41338753002), run ID `41338753002`, fue `workflow_dispatch` en `certificacion`, candidato C `605a6ecca29e20ade8cac3874d380758d18e6a11`, inicio `2026-11-01 13:51:32` y fin `13:55:15` America/Lima. El workflow concluyó SUCCESS. Los gates Production del mismo run habían sido aprobados por el reviewer autorizado.

- `Report pending migrations`: dry-run SUCCESS, cero pendientes; el paso `H2 Pro preflight digest report` fue SKIPPED en operation verify.
- Job `Apply pending migrations`: SUCCESS por `Confirm verify no-op`; `Apply migrations to Pro` y pasos de autorización/apply fueron SKIPPED. No hubo aplicación SQL.
- `Verify target schema`: SUCCESS para `h2-expand-compat`; el reporte indica `Target schema check PASSED`.
- El artefacto se escribió y subió con SUCCESS. `FG2 deferred` solo registra aplazamiento; no ejecuta writers.
- Cohorte: 224; digest `sha256:c217dbffc9d50cca0e1f111fcddf1268db9a34e8671a409f3663dcfff1d735e9`.
- Advisors comparados con baseline: seguridad 12/12 y rendimiento 17/17, fingerprints idénticos; cero hallazgos nuevos/bloqueantes. No hubo HIGH/CRITICAL/ERROR; INFO/WARN se conservan.

### Integridad del artefacto y JSON canónico

El TL conserva los miembros autenticados en `/tmp/h3req1-tl-supervision-20261101/verify91/`. Artefacto GitHub `13096761150`; ZIP SHA-256 `f7e3ac3a735013f2b3959b668b72913526e51c24dde063ee4c714613d69a5895`; exactamente tres miembros: el JSON de evidencia y los dos reportes de advisors. Los cuerpos del ZIP y los advisors no se versionan.

El JSON de origen `h2-production-expand-verify-evidence.json`, el miembro JSON del ZIP y `.context/operaciones/h2_main_production_expand_evidence.json` tienen SHA-256 `563de170bbce697408413a212f39d8592238749856a0c6652e0bea4ce8051195` y bytes idénticos. Contiene `branch=certificacion`, C como `candidate_sha` y `payload_sha`, `run_id=41338753002`, `manifest=h2-expand-compat`, `verify_result=success`, cohorte 224 y el digest acreditado. Conserva `operation=apply` porque lo requiere el contrato histórico del gate main; el dispatch real fue `verify`, el job Apply fue NO-OP y las migrations to Pro quedaron SKIPPED. La etiqueta del JSON no se interpreta como ejecución de apply.

Hashes locales de los miembros conservados: Security Advisors `ccf20e9fbbbadc5a7a70fcfe7bda3e01883cad87c82eaff326541692b27bf09b`; Performance Advisors `aae2eb25b7bb244157989f72340889a70c9cd6dcb75bf6f8f7f83e7960ada2f3`. Se registra comparación/resumen sanitizado, no sus cuerpos crudos.

Antes del reemplazo, el JSON canónico era run 89 con SHA-256 `d38900871fcdf075a9ce7111820cf27757c26cf854d439cada1bbb52750be41c` y candidato `15fdc8dc97933dcc6a77dff65d6b293faadeb2ee`. Run 89 queda preservado en las secciones históricas anteriores; run 91 es el artefacto operativo vigente para C. No se reejecutó report, verify, login, Resync ni UAT.

### Relaciones, pins y contratos de promoción

Los consumidores reales verificados son `.github/workflows/security-audit.yml` (gate de contenido H2, ancestry, run, jobs y comparación del ZIP), `scripts/security/protected_path_scope_guard.sh` (ruta literal), `tests/test_fase10_main_boundary.py`, `tests/test_h2_pro_migration_controls.py`, `tests/test_protected_path_scope_guard.sh` y el selector de manifiestos de `security-audit.yml`. La ruta ya estaba admitida exactamente; por eso no se amplió el guard ni una carpeta. El H2 main gate permite cambios de gobernanza bajo `.context/` tras C y conserva su comprobación de artefacto independiente.

No se regeneran los pins congelados de Certification/main: sus fuentes y baselines históricos no cambiaron y solo se consumen en el baseline exacto aprobado. El nuevo JSON no modifica el selector ni los caller manifests. Los cambios de este paquete son exclusivamente `.context/`; tests locales no convierten esto en CI remoto. Para H2, el candidato final `M` debe conservar `C` como ancestro y `diff(C,M)` debe pasar el `disallowed_after_candidate` real. No existe aún M final para declarar esa condición satisfecha.

Para el futuro gate H3, `auth_base` debe ser ancestro de `P`; `P` debe ser ancestro de `M`; y `diff(P,M)` debe cambiar únicamente el archivo DDL aprobado. El JSON auténtico, las relaciones, registro, fichas, pins requeridos y evidencia deben integrarse antes de congelar `P`. H2 candidate/payload C no se trata como P y no se añade una condición C→P que el contrato no exige. No se debe hacer squash/rebase en las promociones. El archivo DDL continúa `DRAFT_NOT_AUTHORIZED`; cualquier transición a aprobado requiere una decisión humana separada.

### Transición, límites y rollback

- **Expand:** incluir JSON autenticado y referencias antes de P.
- **Compatibilidad:** conservar el contrato exacto del gate H2 y la autorización H3 Draft; el cambio no altera runtime ni schema.
- **Deploy:** solo integraciones protegidas normales. Esta preparación no autoriza publicación ni deploy manual.
- **Contract:** no hay contracción de producto en este paquete; H3 Pro sigue sin aplicarse/verificarse.
- **Rollback:** antes de integrar, revertir el diff local documental. Después, usar únicamente un revert protegido del paquete documental si el TL confirma que no invalida el gate H2; nunca reemplazar la evidencia reciente por run 89 para simular vigencia ni tocar DB.

No hubo commit, push, PR, merge, dispatch, SQL remoto, configuración ni deploy ejecutados por esta sesión. Aceptaciones E1–E6 6/6, R1–R4 4/4 y smoke histórico 1/1 se reutilizan intactas. La nota anterior era provisional; los resultados finales del paquete constan en «Revalidación final del paquete local run 91» inmediatamente debajo.

### Revalidación final del paquete local run 91 — 2026-11-01

Esta sección sustituye solo los resultados provisionales de validación local
anotados antes de completar los objetos del fixture histórico. No modifica ni
reinterpreta el resultado remoto autenticado de run 91.

- Checkout: `/tmp/studiamatch-h3req1-run91-evidence-20261101`, rama
  `codex/h3req1-run91-evidence-20261101`, base/HEAD local
  `64c23fd8a9694f50a2728399bf8e35771bf56fad`; 10 paths, todos `.context/`.
- El render del registro fuente-componente pasó en Docker sin red. `pytest` focal
  de `tests/test_fase10_main_boundary.py`, `tests/test_h2_pro_migration_controls.py`
  y `tests/test_security_flow.py`: 56/56 PASS. El cache `.pytest_cache` creado
  por pytest fue retirado antes de comparar el checker integral.
- `tests/test_protected_path_scope_guard.sh` pasó en Docker sin red después de
  hidratar localmente los blobs del ref histórico PR #501 que faltaban en el
  clon `blob:none`. El test informa manifest/scope 1196 paths, 13 catálogos y
  1173 targets; caller PR/push de Certification y main PASS; baseline posterior
  omite pins históricos; source/content drift falla cerrado; selectores
  desarrollo→Certification y Certification→main PASS con union/digests y
  entradas inválidas fail-closed. No se alteraron el guard ni las pruebas.
- Scanner de credenciales de árbol y del diff: PASS. `git diff --check`: PASS.
  Los 10 paths del paquete cumplen las regex/listas reales del guard; la
  evidencia H2 se conserva como ruta exacta y los cambios `.context/` pasan la
  regex real `disallowed_after_candidate`. Los paths vecinos de evidencia y de
  estado no quedan admitidos. El check de rutas fue análisis de las reglas
  locales, no una ejecución GitHub.
- Verificador local del run 91: PASS para run/jobs, Apply NO-OP, Verify SUCCESS,
  conteo/digest de cohorte, hashes ZIP/JSON, tres miembros y bytes JSON
  idénticos. El artifact raw y cuerpos de advisors siguen fuera del repositorio.
- Checker integral instrumentado solo en copias temporales fuera del repo para
  imprimir todos los diagnósticos: baseline y candidato 348/348, 0 agregados y
  0 removidos. `DOC_SELF_TEST_PASS` en ambos, pero exit 1 por el FAIL integral
  heredado. El self-test candidate-aware del paquete exacto pasó (exit 0); no se
  presenta como PASS integral. Logs reproducibles:
  `/tmp/h3req1-run91-validation-20261101/logs/`.
- La validación de seguridad del delta se limitó a un cambio documental: scanner
  limpio, revisión de procedencia/JSON/DRAFT sin secretos ni contenido de
  usuario, y sin cambios ejecutables. No es un scan global ni una revisión CI.
  ShellCheck/CI remotos no se ejecutaron en este paquete.

No hay SHA de candidato porque no se hizo commit. No existen aún los M/P reales:
la ancestralidad `C→M`, `auth_base→P`, `P→M` y `diff(P,M)` de un solo archivo
solo podrán acreditarse después de las integraciones protegidas. Run 91 valida
H2 en C; no instala ni verifica H3 Pro. El DDL permanece
`DRAFT_NOT_AUTHORIZED`; run 89 conserva valor histórico. No se repitieron CA
aceptados ni se hicieron operaciones remotas.

### Disposición documental para este paquete — propuesta pendiente

El gate integral conserva FAIL en el baseline Development `64c23fd8a9694f50a2728399bf8e35771bf56fad` y en el paquete local de 10 paths: 348 diagnósticos idénticos, 0 nuevos y 0 resueltos. Causa demostrada: relaciones/referencias históricas a fuentes retiradas o ausentes que no se recuperan desde Git/copia autorizada. El candidate-aware self-test pasa por separado; no convierte el integral en PASS.

Propuesta para decisión humana, no aprobada: disponer únicamente este residual para tramitar la integración protegida del paquete exacto de la rama local `codex/h3req1-run91-evidence-20261101` hacia Development, sobre la base indicada. Owner propuesto: Romel/TL. Vencimiento propuesto: 2026-11-03 23:59 America/Lima o antes de integrar este paquete, lo que ocurra primero. Riesgo: referencias históricas incompletas; no se identificó impacto funcional en un diff exclusivamente documental. No cubre Certification, main, Pro/H3 DDL, SQL, workflow, configuración, deploy ni checks/review; no habilita publicación, commit, push o merge y no extiende disposiciones anteriores.
