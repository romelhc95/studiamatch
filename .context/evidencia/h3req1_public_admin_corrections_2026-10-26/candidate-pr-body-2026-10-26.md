## Resumen

R21 agrupa correcciones locales reproducidas para el catálogo público y Admin: la regla de “Actualizarme” ahora reconoce Hibrido/Híbrido; el resumen y botón “Limpiar todo” caben en 320 px; la cabecera Admin se adapta a móvil; y las respuestas antiguas de la cola ya no pueden sobrescribir el resultado de filtros más recientes. Cambia también las pruebas, el control literal de alcance, el workflow de validación y la documentación relacionada. No cambia Auth, membresías, permisos, RPC, payloads, esquema ni datos.

Candidato local: rama `feat/h3req1-public-admin-corrections-20261026`, worktree `/home/romel/src/studiamatch-h3req1-public-admin-corrections-20261026`. Se preparó desde `6b3ec2d5cc647f81e05fe99cb1b48b39658a1e87` y se rebasó sobre Development vigente `4939e0d08422068f75618c51ec2d1344b9625a69`, que contiene el merge de #504. Se conservan exactamente 22 paths (16 modificados y 6 nuevos) sobre esa base; el manifiesto exacto es `candidate-pr-scope-2026-10-26.json`. El usuario autorizó commit, push no forzado y PR protegido a `desarrollo` para esos 22 paths. No incluye aprobación/merge ni deploy manual.

## Evidencia De Este PR

- Los 22 paths se limitan a producto, regresiones, tooling de alcance/workflow y documentación. Se excluyen WIP de Auth/BFF/FG3/PostgREST, los SQL/migraciones y fixture D07–D11, cuentas, datos operativos y secretos. El manifiesto identifica los nombres reales de esos SQL excluidos.
- El guard Docker reconoce los 22 paths exactos, añade solo seis literales permitidos, confirma cinco sources/tests candidate-only seleccionados y conserva R20/R19. La primera invocación aislada no tenía montado el Git common-dir y se detuvo antes de la aserción histórica; la reejecución montó ese objeto read-only y pasó. No se amplían patrones.
- H3-UAT-059 se reutiliza, no se repite, porque los tres SHA-256 de las fuentes públicas y el runner coinciden con la ejecución conservada: 1/1 caso, 3/3 viewports y 118/118 aserciones (Desktop 39, Tablet 39, Mobile 40); cero retries y resets. Es cobertura local sintética de CA4.9, no aceptación remota ni de Admin.
- Docker: pruebas focales 18/18; TypeScript PASS; ESLint PASS con 0 errores y 9 warnings existentes en líneas no modificadas; static mock smoke PASS. El primer smoke se detuvo antes de build porque Turbopack no podía resolver el enlace externo a node_modules; el segundo usó copia scratch y dependencia read-only dentro del proyecto, pasó h2_web_mock_smoke.sh y dejó el árbol fuente intacto.
- Gate candidate-aware R21 PASS después del rebase: self-test y gate para los 22 paths seleccionados; 740/740 fuentes asignadas, 117/117 documentos activos alcanzables y 433/433 históricos catalogados/enlazados. Esto no cierra el gate integral de la autoridad.
- Gate documental integral de la autoridad FAIL (exit 1): 200 diagnósticos explícitos más 153 resumidos, 353 en total. La evidencia íntegra está en el worktree autoridad `/home/romel/src/studiamatch-h3req1-postmerge-20261025/.context/evidencia/h3req1_public_admin_corrections_2026-10-26/validation-20261026-r21/authority-full-doc-gate-20261026.stdout`; la reconciliación explica que una referencia representativa está ausente de autoridad y candidato y solo aparece como archivo untracked en un checkout sincronizado antiguo. No se borró historia ni se debilitó el checker.
- Un Standard scan adicional del repositorio completo (`40d903d1-dd41-4736-9b57-1f286acb2e70`) sigue incompleto en preflight 1/2: no produjo inventario ni revisión; no cuenta como scan limpio. La revisión Codex Security source-backed del diff final rebasado (`4939e0d08422068f75618c51ec2d1344b9625a69..f0573817a70ca45b885de9ecbb9188bac542cd64`, 22 paths) terminó con cobertura completa del diff y 0 findings: scan `b3cfe192-3059-4610-8516-d4e08996f9f8`, snapshot `codex-security-snapshot/v1:sha256:d469090b56085bac06a90f17d0c5529123401a94b48a537754fc130e44d337e2`. No es el Standard scan integral ni evidencia de runtime remoto.
- Tras integrar la base #504, la primera ejecución encontró desincronizado el Markdown generado del registro; se regeneró en un scratch y se copió únicamente ese archivo incluido en R21. Después del rebase, Docker `DOC_SELF_TEST_PASS`/`DOC_GATE_PASS`, scope guard exacto (22/22; R20 preservado), credential scan staged y `git diff --cached --check` pasaron. La validación de workflow tras el rebase pasó parseo YAML, `bash -n` y pruebas del selector: prioridad R21, fallback D04 y fallo cerrado si falta el manifiesto. `actionlint` y `ShellCheck` no están instalados en las imágenes Docker fijadas y no se declaran PASS para el contenido ya combinado; sus resultados de proveedor quedan pendientes.
- El fixture Chrome Windows de cabecera Admin midió innerWidth/clientWidth/scrollWidth = 320/320/320 con identidad sintética. No comparte la sesión del portal ni acredita Development.
- La revisión Codex Security del diff rebasado final cubrió los 22 paths y no encontró findings (scan `b3cfe192-3059-4610-8516-d4e08996f9f8`, snapshot `codex-security-snapshot/v1:sha256:d469090b56085bac06a90f17d0c5529123401a94b48a537754fc130e44d337e2`). La actualización posterior de este archivo solo reconcilia el estado de revisión; no cambia código ni controles. No hubo operación remota ni lectura de secretos.

## Avances Del Cambio

| Componente/contrato | Cambio implementado | Consumidores/impacto | Evidencia |
|---|---|---|---|
| Elegibilidad “Actualizarme” | Helper común normaliza acentos, mayúsculas y espacios; conserva los criterios existentes de modalidad remoto/híbrido y duración corta. | Catálogo público y segundo consumidor del modal de actualización; no cambia consulta ni datos. | H3-UAT-059 local, hashes exactos, 118/118; prueba focal de duración. |
| “Limpiar todo” y responsive público | El resumen permite wrap y el botón conserva su tamaño y texto sin empujar el viewport a 320 px. | Resumen de filtros activos y reset; no altera filtros, query ni semántica de limpieza. | H3-UAT-059 local; runner mide el estado y viewport móvil. |
| Cabecera Admin móvil | Identidad y acciones envuelven/apilan para conservar el ancho disponible. | Admin y User en /admin/; no modifica sesión, rol ni autorización. | Prueba responsive local y fixture visual 320/320/320. |
| Cola Admin | Un contador de generación invalida éxito, error y finally de solicitudes que ya quedaron obsoletas; invalida en el cambio de filtro para cubrir también la ventana previa al siguiente efecto. | Cola, facetas, búsqueda e institución; conserva RPC y payload. | Regresión local de respuestas fuera de orden y cambios rápidos de filtro. |
| Pruebas y gates | Pruebas focales, runner H3, guard con seis rutas literales, selector candidate-aware que conserva D04 y R21, y documentación. | CI local/PR y mantenimiento de fuentes; R20/R19 no se reemplazan ni se debilitan. | Scope guard y documentación Docker PASS; YAML parse, `bash -n` y selección R21/D04 PASS. `actionlint` y `ShellCheck` no disponibles localmente después del rebase. |

## Pilares Obligatorios

| Pilar | Estado | Resultado validado y límites |
|---|---|---|
| Funcionalidad | LOCAL_VALIDADO | Regla pública, reset, cabecera y carrera de solicitudes tienen regresiones locales; repetición remota después de un deployment que incluya R21. |
| Escalabilidad | SIN_CAMBIO_DE_CONTRATO | No añade RPC ni amplía páginas/cardinalidad. No se ejecutó prueba de carga. |
| Seguridad | LOCAL_REVISADO | No cambia autenticación, RLS, roles, tokens o endpoints. Revisión Codex Security del diff rebasado de 22 paths: 0 findings; scan `b3cfe192-3059-4610-8516-d4e08996f9f8`. El Standard scan integral y runtime remoto siguen pendientes; el proveedor PWI no se infiere. |
| Mantenimiento | PASS_LOCAL | Checker documental y guard exacto PASS; 22 paths declarados y relacionados. |
| Calidad | LOCAL_VALIDADO | 18/18 focales, H3-UAT-059 reutilizado por hashes iguales, TypeScript y smoke PASS; ESLint mantiene nueve warnings preexistentes fuera del delta. |
| Rendimiento | SIN_MEDICION | No introduce solicitudes ni reclama mejora de rendimiento; no hubo benchmark. |

## Transicion Transparente

| Fase | Alcance/resultado real | Evidencia / autorización cuando aplique |
|---|---|---|
| expand | Cambios locales aditivos, helpers y regresiones dentro de los 22 paths. | Rama candidata y manifiesto R21. |
| compatibilidad | Conserva payloads/RPC, roles, filtros y comportamiento existente; la versión anterior sigue compatible. | Revisión de consumidores y pruebas focales. |
| deploy | Pendiente. El push autorizado puede producir el Preview automático normal de Pages; no hubo push ni deploy manual. | Esta instrucción autoriza commit/push/PR. Merge y deploy manual permanecen separados. |
| contract | No aplica: no se retira contrato, API ni columna. | Sin contracción DB/API. |
| Rollback/recuperación | Revertir el commit aditivo de R21 si Preview falla; sin migración ni restauración de datos. | Procedimiento previsto; no ejecutado. |
| No degradacion funcional | Evidencia local para los casos descritos; aún falta el deployment de R21 y repetir pruebas afectadas. | H3-UAT-059, mock local y fixture Chrome no equivalen a runtime remoto. |

## Evidencia Para Cliente

CA4.9 queda cubierto localmente solo para el escenario H3-UAT-059 y sus inputs sintéticos. R21 no completa aceptación Development ni D06. Tras la integración y deployment que contengan este cambio deben repetirse: H3-UAT-059 en las tres vistas; D06 responsive de cabecera a 320 px; cola Admin con filtros rápidos/cambio de institución y respuestas fuera de orden, comprobando que solo se presenta el resultado de la consulta vigente. Los subcasos previos de paginación, búsqueda y conteos de D06 pertenecen al deployment anterior y no validan estos arreglos.

No se adjunta la atestación privada del cliente. Los fixtures D07–D11 quedan separados y fuera de estos 22 paths. La autorización vigente cubre commit, push no forzado y apertura del PR protegido a `desarrollo`, incluido el Preview automático habitual. No incluye aprobación/merge ni deploy manual; este PR no declara GO Development.

## Validaciones

| Validacion | Resultado/exit/casos | Ambiente/grado | Evidencia/límites/owner |
|---|---|---|---|
| Credential scan | PASS, 22 paths incluidos, sin credenciales detectadas. | Local/Docker. | Sin abrir .env; salida de validación local. |
| Python tests | No ejecutados: no hay cambios Python. | N/A para el delta. | El workflow mantiene sus jobs existentes. |
| Python compile | No ejecutado: no hay fuentes Python modificadas. | N/A para el delta. | Owner: CI si el proveedor dispara el job. |
| PostgreSQL DB Change Gate | N/A: no incluye SQL, DDL, DML ni write remoto. | Sin cambio de base. | Fixture editorial en worktree distinto y fuera del scope. |
| ESLint | PASS, exit 0; 0 errores y 9 warnings no modificados. | Docker, archivos UI del candidato. | No se suprimieron warnings. |
| TypeScript | PASS, exit 0, sin errores. | Docker/candidato. | Salida vacía registrada tras exit 0. |
| Static build | PASS mediante h2_web_mock_smoke.sh con bridge local; el primer intento offline falló antes del build al resolver una dependencia enlazada fuera del árbol. | Docker, mock HTTP local y scratch. | El fallo instrumental se conserva; el smoke final terminó h2_web_mock_smoke_ok. |
| YAML / actionlint / ShellCheck | YAML parse, `bash -n` del bloque selector y pruebas de prioridad R21/fallback D04/fallo cerrado PASS. `actionlint` y `ShellCheck` no ejecutados: los binarios no existen en las imágenes Docker fijadas. | Docker, workflow/script/test final combinado con #504. | Los jobs/checks del proveedor sobre el SHA publicado quedan pendientes; no se informa PASS local para esos dos binarios. |
| UAT/runtime/integración | H3-UAT-059 PASS reutilizado por SHA idénticos: 1/1, 3/3 viewports, 118/118; sin reintento. D06 Admin anterior tiene subcasos PASS de lectura, pero no valida R21. | Local sintético / Development anterior. | Evidencia histórica enlazada desde pruebas_evidencia.md; remoto R21 pendiente. |
| security-audit / CI independiente efectivo | Pendiente de publicar el SHA R21 para que comiencen los checks. El verificador independiente de GitHub sigue OPEN; Worker Contract no lo sustituye. | Checks remotos y Preview pendientes de publicación. | Owner: revisión de integración/repositorio. |
| CodeQL si aplica | No se ejecutó localmente; no hay dependencia nueva ni endpoint externo. | N/A local. | Revaluar cualquier check que el proveedor real requiera. |
| Cloudflare Pages / smoke preview | Pendiente; no hubo push ni Preview R21. | Remoto no probado. | Requiere publicación autorizada y luego identificación del deployment. |
| Browser snapshot si aplica | PASS local geométrico 320/320/320 en el fixture Admin, no en el deployment. | Chrome Windows, localhost con identidad sintética. | No expone sesión ni datos personales. |
| security-auditor | Revisión source-backed final del diff rebasado: 0 findings en 22 paths. Scan `b3cfe192-3059-4610-8516-d4e08996f9f8`; snapshot `codex-security-snapshot/v1:sha256:d469090b56085bac06a90f17d0c5529123401a94b48a537754fc130e44d337e2`. | Diff local sobre `4939e0d08422068f75618c51ec2d1344b9625a69`. | Cubre la selección del workflow ya reconciliada con #504. El Standard scan integral sigue incompleto; tampoco demuestra runtime remoto ni protección PWI efectiva. |
| Documentación / trazabilidad / fuente cliente | PASS solo para self-test y gate candidate-aware R21 tras rebase: 740/740 fuentes asignadas, 117/117 docs activos alcanzables, 433/433 históricos enlazados. Gate integral de la autoridad FAIL: 353 diagnósticos, evidencia local enlazada arriba. | Docker, manifiesto R21. | El documento privado del cliente no se incluye. |

## Seguridad Y Datos

- [x] Scan source-backed del diff rebasado final sin findings; credenciales del candidato final examinadas localmente y sin detecciones.
- [x] Revisión de los 22 paths exactos del diff final; snapshot y límites registrados arriba.
- [x] API keys, identidades, RLS, roles y MFA quedan fuera del cambio de producto.
- [x] El snapshot source-backed anterior y su límite están identificados arriba.
- [x] DB, secretos, Production, restore, schedules y writers quedan fuera del alcance.

## Alcance Y Limites

- [x] Criterios y fichas vinculados; la atestación privada no se versiona ni adjunta.
- [x] Rama/base y 22 paths fijados en candidate-pr-scope-2026-10-26.json.
- [x] WIP Admin/MFA/BFF/FG3, WIP PostgREST, fixtures SQL y evidencia personal excluidos.
- [x] El push autorizado puede crear el Preview automático normal. Merge/deploy manual y promoción permanecen separados.
- [x] No se afirma aceptación remota ni cierre global H3REQ1.

## Checklist Tecnico

- [x] Gates locales aplicables completados en Docker y registrados arriba.
- [x] Fichas, consumidores, trazabilidad y candidate manifest actualizados; R20/R19 se conservan.
- [ ] Verificador PWI real y protección requerida no acreditados para SHA R21; revisar el proveedor después de publicar.
- [ ] Pruebas remotas del candidato pendientes de integración y deployment.
