## Resumen

Sucesor local sanitizado para H3REQ1, construido desde `4eb4d877a50b012bb630a129bd0c74482c33be9c` con alcance R18 más deltas R19 y las correcciones de PR 501. Preserva funcionalidad R8 y selección documental R13 con R14–R18 históricos. R19 reemplaza los 46 PNG seleccionados por derivados neutros, excluye dos videos y reconcilia lecturas B de Cloudflare/Supabase sin exponer secretos ni filas. B permanece incompleto. El manifiesto fija 1.176 rutas y sus pins exactos. HEAD local es `ef306edd91d339af3a9e0623217b49d86f1cdb1c`, con el mismo árbol que el SHA publicado `d5220185cbb8d1975ebb901a5d6e8e77636b8b02`; la selección local incorpora 22 rutas modificadas y 26 añadidas frente a ese árbol. El PR 501 sigue abierto y este sucesor aún no tiene commit ni SHA propio. Branch local: `feat/h3req1-sync-20261018-r19`.

Vínculos requeridos: [estado vigente](https://github.com/romelhc95/studiamatch/blob/feat/h3req1-sync-20261018-r19/.context/estado_del_proyecto.md), [atestación cliente sanitizada](https://github.com/romelhc95/studiamatch/blob/feat/h3req1-sync-20261018-r19/.context/evidencias_cliente/sprint_1/atestado_aceptacion_plan_ingesta_editorial_auditoria_2026-10-01.md), [reporte remoto R19](https://github.com/romelhc95/studiamatch/blob/feat/h3req1-sync-20261018-r19/.context/evidencia/h3req1_g10_remote_preparation_2026-10-18_r19.md), [paquete Development R19](https://github.com/romelhc95/studiamatch/blob/feat/h3req1-sync-20261018-r19/.context/evidencia/h3req1_development_integration_package_2026-10-18_r19.md), [checks R19](https://github.com/romelhc95/studiamatch/blob/feat/h3req1-sync-20261018-r19/.context/evidencia/h3req1_remote_preparation_checks_2026-10-18_r19.txt), [manifiesto R19](https://github.com/romelhc95/studiamatch/blob/feat/h3req1-sync-20261018-r19/.context/evidencia/h3req1_pr_scope_manifest_2026-10-18_r19_reconciled.json) y [tratamiento visual](https://github.com/romelhc95/studiamatch/blob/feat/h3req1-sync-20261018-r19/.context/evidencia/h3req1_visual_evidence_redaction_2026-10-18_r19.md). Estos enlaces quedarán disponibles tras publicar la rama autorizada.

## Evidencia De Este PR

- Fuente Syncthing: `a57bc415257ab8154d40d7c71d34c69d0bdaeb0d`, 19.510 entradas WIP; no copiada. R18 histórico: `0d7c89dccffd1146b6cc669d4994787e9b78b533`, árbol `332ae4d156863c1f5524e7d5f6c8f1ecb4424dc2`; inalterado. Base R19: `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- Reporte remoto R19: lecturas metadata filtradas; Pages Preview compartido con Certification, Worker/DO presentes, Edge `admin-invite` v14 y contenido idéntico a R18. Sin valores secretos ni datos operativos. Confirmaciones humanas posteriores indican que el key ID Text está en Preview, y que los HMAC corresponden a los valores guardados; no se atribuyen al conector ni se publican valores. `NEXT_SUPABASE_SECRET_KEY` no se configura en Pages Preview.
- Este sucesor no tiene commit/push ni actualización del PR 501, y no se han ejecutado D01/D02, C, nueva invitación ni aceptación remota. La lectura filtrada de Cloudflare encontró un deployment Preview exitoso para el SHA anterior `d5220185cbb8d1975ebb901a5d6e8e77636b8b02`: `https://c7adff18.studiamatch-aty.pages.dev`, deployment `c7adff18-9a74-4eb2-9a08-83a5cc05da46`, creado el 2026-10-18 23:43:51 UTC. Ese deployment no incluye el delta local actual ni acredita su smoke. El responsable aceptó Worker #2 como excepción temporal hasta 2026-10-25 23:59 UTC; no autoriza otro deployment/rollback y no prueba compatibilidad runtime.
- Los hashes originales de visuales se guardan en la nota R19 únicamente para identificar inventario local; el contenido original no está en el candidato y no se ha reintentado el PNG rechazado.

## Avances Del Cambio

| Componente/contrato | Cambio implementado | Consumidores/impacto | Evidencia |
|---|---|---|---|
| H3REQ1 funcional | Snapshot funcional R8 preservado desde R18; no se reinicia ni cambia lógica en R19. | Admin BFF, Edge, Worker/DO, Pages y migraciones seleccionados. | Manifiesto R19; pruebas funcionales históricas solo si inputs fuente no cambiaron. |
| Evidencia visual pública | 46 PNG se sustituyen por un PNG opaco uniforme `#E5E5E5`, estándar y sin metadatos; 2 WEBM excluidos; 3 referencias se redirigen a nota R19. | No publica píxeles de capturas ni cuadros de video; no acredita UAT visual. | Nota R19; originales 48/48 preservados localmente con hashes coincidentes. |
| Preparación B | Actualiza la lectura de Preview, binding, Worker/DO y Edge v14; separa lecturas del conector y confirmaciones manuales. | El deployment Preview existente corresponde al SHA remoto anterior; el delta local no está servido y el runtime no se probó allí. B incompleto. | Reporte remoto R19; no se activa gateway ni se hace otro deploy/rollback. |
| Correcciones de PR 501 | Corrige dependencias faltantes del workflow, la invocación/config de PostgREST y cuatro diagnósticos CodeQL del SHA publicado. | Workflow `security-audit` y regresiones focales. | Pruebas locales de los fixes pasan; los resultados remotos siguen ligados al SHA anterior. PWI no se ejecutó desde la base confiable. |
| Control de scope/documentación | El guard usa el manifiesto R19 y admite solo rutas exactas; mantiene exclusiones explícitas. | Workflow `security-audit`, checker, registro y PR. | Pins de scope y cierre de referencias: 1.176/1.176 y 1.173/1.173; guard: 1.182 rutas efectivas, 13 catálogos/1.173 destinos. |

### Code Scanning #15–#18 de main

| Alerta | Cambio local en este candidato | Regresión local | Resultado remoto |
|---|---|---|---|
| #15 `taxonomy_roi_audit.py:86` — almacenamiento claro sensible | El reporte deja de persistir detalle por fila y conserva agregados. | `tests/test_taxonomy_roi_audit_privacy.py` | La última captura del responsable mostraba la alerta abierta en `main`; no hay análisis nuevo ni promoción. |
| #16 `universal_harvester.py:316` — regex ineficiente | Parser lineal de grupos cuantificados; `regex` con timeout de 50 ms y fallo cerrado. | `tests/test_h3req1_local_pipeline_walk.py`: patrones peligrosos, timeout y dependencia ausente. | La última captura la mostraba abierta en `main`; no hay análisis nuevo ni promoción. |
| #17 `site_diagnostics.py:94` — sanitización parcial de URL | Hostname validado tras parsear URL, con host exacto o subdominio permitido. | `tests/test_site_diagnostics_security.py` | La última captura la mostraba abierta en `main`; no hay análisis nuevo. |
| #18 `send-lead-emails/index.ts:156` — exposición de stack | Error externo 500 genérico sin detalle ni stack. | `tests/h3_send_lead_error_uat.mjs` invoca el handler real. | La última captura la mostraba abierta en `main`; no hay análisis nuevo. |

Estas remediaciones están incluidas localmente. No se declara cerrada ninguna alerta de GitHub: el conector no pudo leer el endpoint Code Scanning y las promociones a `main` siguen el flujo protegido.

### Cuatro diagnósticos CodeQL del PR 501

Estos cuatro diagnósticos fueron reportados sobre el SHA antiguo `d5220185cbb8d1975ebb901a5d6e8e77636b8b02` y no son las cuatro alertas históricas de `main` listadas arriba. El análisis remoto del sucesor todavía no existe.

| Regla / ubicación en el SHA reportado | Remediación local actual | Prueba focal | Resultado CodeQL remoto actual |
|---|---|---|---|
| Inefficient regular expression (High), `scripts/core/universal_harvester.py:316` | Detector estructural lineal para cuantificadores anidados; `regex` con timeout de 50 ms y rechazo cerrado si falta la dependencia o vence el límite. | `tests/test_h3req1_local_pipeline_walk.py`: patrones anidados y seguros, timeout sintético y falta de `regex`; `python-check` invoca esta suite. | Pendiente de análisis del nuevo SHA; el resultado del SHA anterior no se reutiliza. |
| Incomplete multi-character sanitization (High), `scripts/maintenance/h3req1_documentation_integrity.mjs:53` | Sustituye el borrado regex de tags por un recorrido que respeta atributos entre comillas; añade casos de markup incompleto y atributo con `>`. | `node scripts/maintenance/h3req1_documentation_integrity.mjs --self-test`; ejecutado en Docker. | Pendiente de análisis del nuevo SHA. |
| Server-side request forgery (Critical), `tests/h3req1_c03_integrated_runtime.mjs:317` | PostgREST acepta método/ruta/consulta exactos y construye destinos desde un mapa local fijo; rechaza parámetros y rutas no incluidos. | `node tests/h3req1_c03_integrated_runtime.mjs --self-test-proxy-destinations`; mocked fetch confirma destino fijo y que el caso rechazado no alcanza `fetch`. | Pendiente de análisis del nuevo SHA. |
| Server-side request forgery (Critical), `tests/h3req1_c03_integrated_runtime.mjs:348` | Edge fija `/admin-invite` al origen configurado y descarta query del caller; ejercita `handleFunction` con query adversarial. | El mismo self-test de destinos proxy, ejecutado en Docker. | Pendiente de análisis del nuevo SHA. |

El resultado local confirma el comportamiento de los casos focales; no sustituye la ejecución CodeQL remota. Las dos alertas SSRF corresponden a un runtime de prueba y no a una ruta de producto desplegada.

## Pilares Obligatorios

| Pilar | Estado | Resultado validado y límites |
|---|---|---|
| Funcionalidad | `PENDIENTE` | El smoke local R19 inició Next y `/admin/login/` respondió HTTP 200. No hubo aceptación remota; evidencia R178/R18 solo se reutiliza en inputs byte-idénticos. |
| Escalabilidad | `PENDIENTE` | Sin carga remota; cuotas y límites D siguen vigentes. |
| Seguridad | `PENDIENTE` | Secret values no leídos; el responsable confirmó presencia/paridad sin compartirlos; B incompleto. Las alertas #15–#18 de main tienen correcciones locales, no un análisis remoto nuevo. PWI pendiente. |
| Mantenimiento | `PASS local documental` | Checker candidato: 722/722 fuentes asignadas; 113/113 documentos activos alcanzables; 433/433 históricos catalogados y enlazados. R8/R13 no se reorganizan. |
| Calidad | `PENDIENTE` | UAT Auth/Edge, SSRF focal, py_compile y build smoke local pasan en Docker; el resultado final del manifiesto y la revisión independiente se registran abajo. CodeQL remoto y PWI pendientes. |
| Rendimiento | `PENDIENTE` | Sin build/runtime R19 ni medición actual. |

## Transicion Transparente

| Fase | Alcance/resultado real | Evidencia / autorización cuando aplique |
|---|---|---|
| expand | A se consumió en Free bajo R18; no repetir. B muestra configuración parcial; no activar gateway. | R18 A; reporte R19; B aprobado en alcance exacto pero incompleto. |
| compatibilidad | Worker/DO, binding Preview y Edge v14 identificados; dos despliegues exceden el límite y Worker #2 está bajo excepción temporal. El Preview existente sirve el SHA antiguo, no este delta. | Reporte R19 y lectura filtrada del 2026-10-19; Preview comparte configuración con Certification, que permanece intacta. |
| deploy | No se ha servido el delta local. El deployment Preview registrado solo cubre `d5220185cbb8d1975ebb901a5d6e8e77636b8b02`. | Se requiere el gate B de Preview del sucesor, Docker, revisión independiente y controles protegidos. |
| contract | Pendiente; no ejecutar antes de estabilidad y aceptación. | Plan canónico; fuera de esta etapa. |
| Rollback/recuperación | No ejercido; preservar versión Worker activa, Edge v14 y schema expandido. | No deployment/rollback extra sin delta aprobado; stop-on-failure, cero retry automático. |
| No degradacion funcional | No acreditada remotamente en R19. | Aceptación runtime/cliente pendiente; evidencia local R178 no sustituye Development. |

## Evidencia Para Cliente

La [atestación sanitizada del criterio cliente](https://github.com/romelhc95/studiamatch/blob/feat/h3req1-sync-20261018-r19/.context/evidencias_cliente/sprint_1/atestado_aceptacion_plan_ingesta_editorial_auditoria_2026-10-01.md) enlaza la fuente privada sin adjuntarla. Aceptación remota H3REQ1 pendiente. D01–D14: 0/14 en R19; regresión adicional: 0/11. No declarar GO Development. El caso de último administrador requiere ambiente remoto aislado y autorización adicional si la cobertura disponible exigiría tocar Gmail u otra identidad protegida.

## Validaciones

| Validacion | Resultado/exit/casos | Ambiente/grado | Evidencia/límites/owner |
|---|---|---|---|
| Credential scan | `PASS` en el árbol completo candidato. | Docker aislado, red deshabilitada. | `credential scan passed`; regresiones del scanner también PASS. No se exponen secretos; owner Codex. |
| Python/contratos funcionales | `PASS`, 21 pruebas focales y 10 subtests. `tests/test_protected_workflow_review.py`: 13 pruebas PASS por separado. | Docker aislado; fixtures deterministas. | Incluye los fixes de seguridad y el helper PWI. No es aceptación remota ni ejecución completa del job remoto. |
| Python compile | `PASS` en los módulos y pruebas afectadas. | Docker aislado, Python 3.11 del venv. | `py_compile` exit 0; pycache aislado. |
| PostgreSQL DB Change Gate | No PASS local del gate completo. | El run remoto anterior falló al ejecutar el archivo de configuración como binario. | La invocación local corregida solo probó el inicio de PostgREST contra loopback sin DB y terminó en timeout esperado; no reemplaza el gate con PostgreSQL 17. No se ejecutó DDL/DML adicional. |
| ESLint | `PASS`, `npm run lint`: 0 errores y 9 warnings ya existentes. | Docker candidato; el árbol `web` coincide con el input validado. | Resultado local; no sustituye el job remoto ni se presentan warnings como errores. |
| TypeScript | `PASS`, `npx tsc --noEmit --incremental false`. | Docker candidato; no hubo cambios posteriores en los inputs TypeScript. | Resultado local; no sustituye el job remoto. |
| Static build y runtimes | `PASS`: `h2_web_mock_smoke_ok`; en Node 22, `h3_admin_quota_runtime.mjs` y `h3_admin_safe_suspend_runtime_uat.mjs` también PASS con el artefacto estático recién compilado. | Build Node 20.20.2 en Docker candidato; runtimes Node 22.22.0 en Docker aislado, red deshabilitada y fixtures locales. | Se corrigió la invocación que corría safe-suspend sin `web/out`; no es Preview ni aceptación remota. Los intentos intermedios de harness quedan registrados en el log. |
| actionlint / ShellCheck | `PASS` en Docker: actionlint 1.7.7 con su invocación de shellcheck desactivada y ShellCheck 0.11.0 focal ejecutado por separado. | Imágenes aisladas; workflow y scripts montados de solo lectura. | Resultados locales; el run remoto anterior terminó cancelado en actionlint y omitió ShellCheck. |
| Documentación, referencias y manifest | `PASS` en Docker: 722/722 fuentes asignadas, 113/113 activos, 433/433 históricos; scope 1.176/1.176 y cierre de referencias 1.173/1.173. | Guard: 1.182 rutas efectivas; 13 catálogos/1.173 destinos. | 37/37 artefactos de contenido coinciden en contenido/bytes y modo Git; el manifiesto R19 excluye solo su propio hash. Los 32 avisos POSIX `0644`/`0664` normalizan a `100644`. No se alteraron modos ni WIP excluido. Se preservan los siete inputs históricamente faltantes; el inventario actual contiene once invocaciones directas Static Build, todas presentes y scoped, y la lista vigente de faltantes está vacía. |
| Contrato de estado Obsidian | `PASS`, 8 pruebas. | Docker aislado, sin red; `tests/test_obsidian_context_state.py`. | La ejecución bloqueada histórica se conserva; el follow-up es el resultado vigente. |
| `git diff --check` y altas locales | `PASS`: delta rastreado y 26 archivos nuevos sin diagnósticos de whitespace. | Docker; `git diff --check HEAD` más revisión `--no-index --check` de las altas. | Se corrigió una línea vacía sobrante al final de `tests/h3req1_c03_docker_daemon_identity_f2d.py`; py_compile focal volvió a pasar. No se reformatearon archivos históricos. |
| UAT/runtime/integración Development | NO EJECUTADO; D01–D14: 0/14; regresión: 0/11. | El smoke local de la app responde HTTP 200. Pages Preview actual es del SHA anterior, no del delta. | Owner responsable/Codex tras integración protegida y bloque de aceptación. |
| security-audit / CI independiente efectivo | El run remoto anterior `39177784316` falló en security-audit. | SHA remoto `d5220185cbb8d1975ebb901a5d6e8e77636b8b02`; no existe run nuevo. PWI no generó job: GitHub toma `pull_request_target` desde `main`, y no puede habilitarse con un bootstrap solo a `desarrollo`. | Los resultados del sucesor requieren PR actualizado. PWI queda bloqueado hasta acordar una fuente confiable compatible; no se cambia `main` ni se debilitan controles. |
| CodeQL si aplica | No reanalizado en el sucesor. | Sobre el SHA anterior se reportaron 2 Critical y 2 High en cuatro diagnósticos del PR. | Requiere nueva ejecución remota; los cuatro fixes locales no equivalen a cierre remoto. |
| Cloudflare Pages / smoke preview | Preview anterior: build/deploy exitoso; smoke remoto del delta actual NO EJECUTADO. | URL `https://c7adff18.studiamatch-aty.pages.dev`; deployment para SHA `d5220185cbb8d1975ebb901a5d6e8e77636b8b02`. | B incompleto hasta servir y comprobar el sucesor dentro del alcance aprobado. |
| Browser snapshot si aplica | NO EJECUTADO. | Sin host candidato. | Requiere guía e interacción humana. |
| security-auditor | El veredicto independiente read-only del digest exacto se registra en el manifiesto. | Revisiones previas y findings históricos se conservan; el digest objetivo está fijado allí. | No sustituye aprobación humana GitHub del SHA que se publique. |
| Documentación / trazabilidad / fuente cliente | Checker, referencias, scope guard y manifiesto pasan en Docker. | 722/722 fuentes; 1.176 pins; 1.173 destinos en 13 catálogos. | R8/R13 no se reorganizan; owner Codex. |

## Seguridad Y Datos

- [x] Scanner R19 PASS en Docker sobre el árbol candidato y pruebas de regresión del scanner.
- [x] Conector no leyó valores secretos ni filas, usuarios, buzones o tokens.
- [x] Confirmación humana de presencia Edge, key ID Text en Preview y paridad HMAC; el conector no puede verificar valores y no se registraron. La solicitud de rotación de `NEXT_SUPABASE_SECRET_KEY` no está aprobada ni ejecutada.
- [x] No se toca Gmail; C retentivo conserva Auth row, referencias e historial.
- [x] No hay DDL/DML, reset, invitación, workflow, PR, push o merge en R19.
- [ ] Las cuatro alertas reportadas para el PR 501 no se han reanalizado sobre el sucesor. Las alertas históricas #15–#18 de `main` están separadas arriba; la última captura del responsable las mostraba abiertas y el endpoint de alertas no está disponible en el conector. PWI pendiente.

## Alcance Y Limites

- [x] Candidato desde baseline con alcance R18 exacto y deltas R19 seleccionados.
- [x] R8/R9/R12/R13/R14/R15/R16/R17/R18 y originales históricos preservados.
- [x] WIP no manifestado, datos operativos, Certification, `main` y Production excluidos.
- [ ] La ruta GitHub efectiva, B completo y candidato exacto aún no verificados para publicar.

## Checklist Tecnico

- [ ] Los gates remotos deben pasar sobre un SHA nuevo; PWI requiere resolver su fuente confiable fuera del default branch protegido; el gate B espera el Preview/smoke del sucesor.
- [x] Ficha B y tratamiento público de visuales escritos sin exponer contenido.
- [x] A/B/C/D registrados sin repetir aprobaciones; A consumido, B parcial, C/D no consumidos.
- [ ] Review humana debe venir de colaborador distinto de autora/pusher y corresponder al SHA más reciente.
- [ ] NO-GO Development; la siguiente promoción no queda implícita.
