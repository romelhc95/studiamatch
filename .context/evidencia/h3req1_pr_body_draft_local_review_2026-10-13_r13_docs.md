<!-- Borrador local basado en la plantilla versionada .github/pull_request_template.md. No abrir ni actualizar PR desde este documento. -->

Guía de sistema: [índice integral](../indice.md). Protocolo de impacto: [constructor y nomenclatura](../trazabilidad/protocolo_constructor.md).

## Resumen

R13 completa la navegación histórica local de StudIAMatch: 13 catálogos enlazan individualmente 433 documentos preservados; el índice resume sus conteos desde el registro canónico y el checker detecta discrepancias. También añade al allowlist protegido las rutas R13 faltantes y prueba ese allowlist contra el scope real y los artefactos incluidos. Mantiene `.context/indice.md` como entrada Obsidian y `.context/estado_del_proyecto.md` como autoridad operativa. Candidato `feat/h3req1-sync-20261002`, baseline `4eb4d877a50b012bb630a129bd0c74482c33be9c`; HEAD no representa todo el WIP. El checkout original permaneció en solo lectura. No se ejecutó PR.

## Evidencia De Este PR

Corte local 2026-10-13. El [reporte R13](h3req1_documentacion_navegacion_historica_2026-10-13_r13.md), [checks](h3req1_documentacion_checks_2026-10-13_r13.txt), [manifiesto propuesto](h3req1_pr_scope_manifest_2026-10-13_r13_docs.json) y [revisión independiente](h3req1_documentacion_revision_independiente_2026-10-13_r13.txt) distinguen resultados locales, históricos y remotos pendientes. No se consultó GitHub, Supabase, Cloudflare ni documento privado de cliente. El manifiesto no incluye su propio hash.

## Avances Del Cambio

| Componente/contrato | Cambio implementado | Consumidores/impacto | Evidencia |
|---|---|---|---|
| Navegación histórica | 13 catálogos subordinados, cada target Markdown enlazado, estado histórico/sustituido y relaciones localmente identificables. | Índice, 14 fichas de módulo, lectores Obsidian y registro canónico. | Catálogos, checker, [reporte R13](h3req1_documentacion_navegacion_historica_2026-10-13_r13.md). |
| Índice y registro | Resumen de conteos generado del JSON; gate compara el bloque real y self-test introduce conteo desactualizado. | `.context/indice.md`, registro JSON, vista generada, checker y wrapper Docker. | Gate normal y `--self-test`. |
| Protected paths CI | Allowlist documental explícito para el scope R13; el test consume `scope.entries` y `package_artifacts` frente a las regex/lista del workflow. | `.github/workflows/security-audit.yml`, `tests/test_protected_path_scope_guard.sh`, seguridad tooling, manifiesto. | Regresión Docker `candidate_paths=125` PASS; no equivale a ejecución GitHub. |
| R37 y secuencia C03 | R37 enlazado con su preparación, runner, test, log, antecedentes/continuaciones explícitos; se registra ausencia local del manifiesto consumido. | Ficha C03/DB/Admin, runner y evidencia histórica. | Catálogo C03; digest del log cotejado con la preparación. |
| Nomenclatura | Convención registrada; no se proponen renombres. | Mantenimiento de fuentes, docs, imports, consumers y runners. | Protocolo constructor; revisión de consumidores e historia local. |

## Pilares Obligatorios

| Pilar | Estado | Resultado validado y límites |
|---|---|---|
| Funcionalidad | N/A para el cambio documental | No cambió comportamiento de producto; se preserva cierre local R178/R181/R182. |
| Escalabilidad | Sin runtime change | No se realizó medición nueva; límites por módulo permanecen documentados. |
| Seguridad | PASS scanner R13: exit 0 en 155 paths únicos explícitos | Alcance explícito en checks; sin lecturas de secretos, `.env` ni documento privado. |
| Mantenimiento | PASS local con revisión independiente GO | 433/433 enlaces históricos, 95/95 activos accesibles; clasificaciones no se confunden con actualidad. |
| Calidad | Gate normal/self-test PASS; `tests/test_obsidian_context_state.py` registró 8/8 en corte previo, pero no se pudo repetir porque falta `pytest` en el contenedor actual. | El resultado anterior no se declara como ejecución vigente; no equivale a pruebas de producto ni CI remota. |
| Rendimiento | N/A | No se alteró ni midió runtime. |

## Transicion Transparente

El cambio es documental y de tooling del gate. No cambia contratos funcionales, DB, UI, pipeline ni despliegue. Sí modifica `.github/workflows/security-audit.yml` para ampliar el allowlist de rutas locales protegidas; no se configuró ni ejecutó GitHub.

| Fase | Alcance/resultado real | Evidencia / autorización cuando aplique |
|---|---|---|
| expand | Se añadieron rutas de catálogo/índice, relaciones en JSON y entradas exactas en `allowed_h3_local` con un test conectado al manifiesto. | Backup previo R13 externo, catálogos generados y regresión protected-path. |
| compatibilidad | Se preservaron rutas históricas; no se renombró R37 ni fuentes consumidas por runners. El job existente incluye el test de allowlist en `python-check`. | Gate de links/anchors, catálogo y test del manifiesto; no se ejecutó GitHub. |
| deploy | No ejecutado ni solicitado en esta sesión. | Requiere instrucción separada. |
| contract | No aplica a runtime; no se retiran fuentes/evidencia en R13. | No hay cambio funcional para contraer. |
| Rollback/recuperación | Restaurar archivos desde el backup identificado y regenerar Markdown desde JSON. | Backup externo verificado; no incluido en paquete. |
| No degradacion funcional | Código de producto intacto; no se repiten suites de inputs intactos. | Cierre funcional preservado; pytest cubre consumidor de estado. |

## Evidencia Para Cliente

No se leyó ni versionó el documento privado. No se agrega criterio de producto ni nueva aceptación. Diez registros de historia de cliente conservan path y límites sin inspección del contenido. Criterios sanitizados vigentes siguen en los documentos existentes.

## Validaciones

| Validacion | Resultado/exit/casos | Ambiente/grado | Evidencia/límites/owner |
|---|---|---|---|
| Credential scan | PASS, exit 0; 155 paths únicos explícitos. | Docker; 131 entradas de scope presentes, 26 marcadores con tres solapamientos, más el manifiesto. | No incluye `.env`, secretos operativos ni todos los untracked. |
| Python tests | `tests/test_obsidian_context_state.py`: 8 passed en la validación previa del corte R13; no repetido tras cambios de documentación/workflow. | Resultado previo en Docker. | El intento de repetir no inició porque el contenedor actual no tiene el módulo `pytest`; inputs del test no cambiaron. No se ejecutan suites funcionales con inputs intactos. |
| Python compile | No aplica; no se editaron fuentes Python. | — | — |
| PostgreSQL DB Change Gate | N/A; no se editó ni ejecutó SQL. | No se usó DB. | Pro remoto no cotejado. |
| ESLint | No repetido; no hubo cambios TS/TSX. | — | — |
| TypeScript | No repetido; no hubo cambios TS/TSX. | — | — |
| Static build | No repetido; no hubo cambio de frontend. | — | Cierre funcional previo no se amplía. |
| Workflow lint / ShellCheck | No ejecutado: `actionlint` y `shellcheck` no están instalados en el contenedor actual. `bash -n` del test y el consumidor del allowlist pasaron. | Docker local. | Requiere un entorno con ambos linters; no equivale a validar GitHub. |
| Protected-path consumer | PASS: `tests/test_protected_path_scope_guard.sh` coteja el manifiesto R13 con `allowed_h3`, `allowed_h3_extra` y `allowed_h3_local`; 125 rutas del scope/artefactos aceptadas. | Docker local. | Simula el matcher documentado; no ejecuta el workflow ni GitHub. |
| UAT/runtime/integración | No ejecutado de nuevo. | No runtime ni servicios remotos. | R178/R181/R182 permanecen como cortes preservados. |
| security-audit / CI independiente efectivo | No ejecutado en GitHub. | Remoto. | Job versionado previamente; instalación/ejecución no verificada. |
| CodeQL si aplica | No ejecutado. | Remoto. | Determinar en la etapa PR. |
| Cloudflare Pages / smoke preview | No ejecutado. | Remoto. | Requiere instrucción separada. |
| Browser snapshot si aplica | N/A; no hay cambio visual. | — | — |
| security-auditor | Revisión documental independiente local: GO final para 9,340 links/4,567 anchors. Una rerevisión posterior halló dos frases de estado P2; se corrigieron y la última lectura confirmó el paquete y sus pins. | Local, lectura independiente. | El GO previo de 9,336 links se conserva como corte anterior. El GO final se limita a documentación/gates locales y no sustituye CI ni verificación remota. |
| Documentación / trazabilidad / fuente cliente | Gate Docker normal/self-test PASS; 801/801 fuentes, 14/14 componentes, 95/95 docs activos, 433/433 históricos enlazados, 0 excluidos; 4,715/4,715 relaciones locales, 91 N/A justificados y 4,806 slots totales. 9,340 links/4,567 anchors; scanner y scope/scanner regressions PASS. | Docker local. | 5 checks remotos siguen pendientes; 10 documentos cliente no inspeccionados. |

## Seguridad Y Datos

- No se leyeron secretos operativos, variables `.env`, tokens, dumps ni documento privado del cliente.
- El scanner cubrirá el conjunto explícito R13 y marcadores seleccionados; no valida stores o servicios remotos.
- No se ejecutaron SQL operativo, writers, schedules, workflow_dispatch, cambios de secretos ni despliegues.

## Alcance Y Limites

- El alcance exacto y hashes están en el manifiesto R13; se heredan los antecedentes del paquete documental R12 y se añaden solo los archivos de navegación/evidencia/tooling seleccionados.
- Los artefactos generados y caches/dependencias no se incorporan; el backup queda fuera del paquete. La disponibilidad de históricos en la rama de integración debe cotejarse en el paso 3.
- Los 433 enlaces son locales y no prueban presencia remota. El manifiesto R37 consumido no está disponible localmente.
- No se afirma adopción remota, apertura de PR ni cierre de la reconciliación funcional R8/R9/WIP.

## Checklist Tecnico

- [x] Preservación previa externa comprobada; no se limpió ni modificó material histórico.
- [x] Entrada Obsidian única y autoridad operativa única.
- [x] Catálogos individuales, resumen derivado del JSON y links/backlinks revisados por gate.
- [x] R37 conserva nombre, hash de log y límites de manifiesto.
- [x] Cierre funcional previo intacto; sin suites redundantes.
- [x] Scanner explícito R13 actualizado, regresiones scanner/scope, integración protected-path de 125 rutas y gate documental normal/self-test PASS según los checks adjuntos.
- [x] Reconciliación/verificación de hashes del snapshot actual: 138 entradas de scope, 8 pins de evidencias seleccionadas, 26 overlays y 4 artefactos; digest, hashes, tamaños y modos verificados; self-hash del manifiesto excluido.
- [x] Relectura independiente final GO después de corregir la celda de mantenimiento y la frase duplicada de siguiente paso.
- [x] Sin PR, commit, push, merge, deploy, SQL operativo ni lecturas remotas.
