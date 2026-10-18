# Documentación integral StudIAMatch — corte local 2026-10-12

> Evidencia del paso 2 de transferencia: documentación integral y navegación Obsidian. Tras reproducir y corregir el P2 de sufijos/duplicados, la revisión independiente final dio GO sin hallazgos materiales. El checker/pines/scanner y el path guard pasan en Docker; el cierre sigue acotado al candidato local, R8/R178 y límites remotos.

## Candidato, WIP y límites

| Elemento | Observación |
|---|---|
| Checkout candidato editable | `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama `feat/h3req1-sync-20261002`, HEAD baseline `4eb4d877a50b012bb630a129bd0c74482c33be9c`. |
| Checkout original | `/home/romel/src/studiamatch`, rama `feat/h3req1-development-remote-tests`, HEAD `7650093b05a820e8e6faf9ec711e12fab8b50398`; solo lectura. |
| WIP observado al corte final | 68 paths tracked cambiados, 918 entradas untracked visibles, 20,427 paths untracked expandidos, 0 staged. HEAD no identifica el WIP; el paquete se limita a paths enumerados por el manifest documental. |
| Autoridad | `.context/estado_del_proyecto.md` mantiene autoridad operativa; `.context/indice.md` es navegación. `.context/00_INDICE.md` sigue como puente y no crea autoridad nueva. |
| Permisos de esta sesión | Sin commit, push, PR, merge, cambios de branch, fetch/pull, lectura remota, acceso o escritura Supabase, secretos, writers, schedules, SQL operativo, deploy ni smoke remoto. No se leyó `.env` operativo ni documento privado de cliente. |

## Preservación documental

La copia previa a edición está en `/home/romel/backups/studiamatch-docs-2026-10-12`, fuera de ambos checkouts. Se creó el 2026-10-12 07:43:48 -05 y contiene 13,856 archivos: 13,740 bajo `.context`, 115 Markdown fuera de `.context` y `.env.example`. `inventory/source.sha256` y `inventory/copy.sha256` tienen 13,856 entradas y SHA-256 de manifiesto `e43386e9eb0ecf0a2b7d9d9d2459832053da1a8765286a5dddd79af27c153223`; se compararon byte a byte. Los 9 artefactos registrados en `inventory/backup_artifacts.sha256` verificaron. Se excluyeron dependencias/caches, `.git`, symlink de dependencia y candidatos por nombre para env/credenciales/certificados; se registraron rutas de exclusión sin abrir sus contenidos.

El inventario inicial omitió `web/vendor/README.md` porque su carpeta se excluyó como dependencia. La omisión está explicada en `SUPPLEMENTAL_AFTER_DISCOVERY.md`. Se preservó una copia suplementaria posterior al descubrimiento y se recuperó el contenido anterior desde evidencia local `.context/evidencia/h3req1_g09_uat_2026-10-10_r4/build-context-final-r17/vendor/README.md`. Fuente, captura posterior y recuperación histórica coinciden byte a byte, SHA-256 `4e7f2700dcc37fe9db4b4fb3834ff7d4a4764e0f9ed3b8ea330e202d1b2ae62d`. Esa copia histórica no se llama backup pre-edición; no se encontró historia Git del README porque es untracked.

Checkpoints externos, cada uno con path inventory y hashes fuente/copia cotejados:

- `/home/romel/backups/studiamatch-docs-2026-10-12/checkpoint_current_before_overlay_correction_2026-10-12`: corte completo actual de la documentación antes de las correcciones finales R8→R9; 13,889 rutas. `inventory/source.sha256` y `inventory/copy.sha256` coinciden byte a byte; SHA-256 del manifiesto fuente: `ff3a7abf3a5673f84437ca582833b8d9e04fdce4c3250649bad3ae47fe5b92e1`. No es el backup pre-edición inicial, que se conserva separado.
- `/home/romel/backups/studiamatch-docs-2026-10-12/checkpoint_pre_additional_fixes_2026-10-12`: 13,886 archivos, incluido `.context` actual de ese corte y 116 Markdown externos; antes de corregir contratos RPC/visibilidad.
- `/home/romel/backups/studiamatch-docs-2026-10-12/checkpoint_current_before_manifest_reconciliation_2026-10-12`: 13,886 archivos; estado anterior al seguimiento `braces` y a esta reconciliación.
- `/home/romel/backups/studiamatch-docs-2026-10-12/checkpoint_after_vendor_followup_docs_2026-10-12`: 13,886 archivos, incluidos cambios de `braces`, conteo de Markdown y mapa; su inventario SHA-256 se verificó contra la copia.
- `checkpoint_current_before_continuation_2026-10-12` se conserva marcado como supersedido: un recorrido inicial demasiado amplio alcanzó algunos README de caches/dependencias. No se usa como backup válido y no se borró.

El corte posterior no se presenta como pre-edición. Un intento de checkpoint intermedio quedó incompleto, sin manifiestos ni verificación; no se usa como respaldo y se conserva marcado como incompleto. El checkpoint verificado posterior a la expansión del registro está en `/home/romel/backups/studiamatch-docs-2026-10-12/checkpoint_after_source_registry_expansion_verified_2026-10-12`: 12,293 paths, manifiesto fuente/copia `5486b51bfcb5c99f2fcb073d255d50880808969d7387ad1795e9be0bec76a9e9` y tar `bfd76fcd1602138120186c3e54596a4b999806d3e4a51f0e7adb4a04ccd26924`. El checkpoint inmediatamente anterior a la corrección del diccionario de base de datos está en `/home/romel/backups/studiamatch-docs-2026-10-12/checkpoint_before_database_dictionary_fix_2026-10-12`: 18,607 archivos, 1,781,934,080 bytes; los manifiestos fuente/copia tienen SHA-256 `a754e7674ff7ff563f8a499d1a9c6a046cdd743165b0f30ea680a4b9f12f7fe2` y `6a2aabc53b907816861038ef9351b433f4520d1dfe3b633e7cff7e7b7ce85083`; el tar SHA-256 es `64049be85c706c93b51204ef5b9a6fb2420e72e66c888f89ee777cf838a33ff5`. Se cotejaron los 18,607 paths y el contenido byte por byte. Es posterior a R9 y no es backup pre-edición. Ningún backup se incluye en el paquete ni se limpia evidencia histórica o recursos Docker.

El primer checkpoint adicional `/home/romel/backups/studiamatch-docs-2026-10-12/checkpoint_final_candidate_documentation_2026-10-12` tuvo cotejo de integridad PASS (18,324 paths, 1,289,715,139 bytes, tar SHA-256 `fb7531628419da616ce60575e4cb76e7c317768d1b195360b8cf9070643e07d8`), pero la revisión independiente lo declaró no apto como copia final filtrada: contiene 10 copias del tarball de dependencia `braces` y dos tarballs de snapshots G08 que también contienen esa dependencia. Se conserva intacto y fuera del paquete; no se borró evidencia. La copia documental filtrada queda en `/home/romel/backups/studiamatch-docs-2026-10-12/checkpoint_final_candidate_documentation_filtered_2026-10-12` y comprende 18,312 paths. Excluye 283 `.next/cache` y 12 artefactos con dependencia (10 copias `.tgz` más dos `.tar` que las incluyen). Mantiene 4,422 outputs `.next` no-cache como artefactos generados dentro de evidencia histórica fechada; no acreditan build actual ni deploy. Cuatro archivos `.pem` se clasificaron como certificados X.509 mediante `openssl x509 -noout`, sin imprimir campos. Los 12 archivos excluidos permanecen en el candidato y el checkpoint ampliado supersedido. Los sidecars externos registran inventario, exclusiones, hashes fuente/copia y tar; la captura no entra en R9.
## Estructura y cobertura

Entrada principal: [índice](../indice.md). Se reorganizó navegación sin mover ni renombrar migrations, rutas, imports, archivos especiales de framework, evidencia sellada, logs o documentación raíz histórica. El mapa declara origen → destino → consumidores/referencias → tratamiento histórico.

Al corte local, el registro asigna **808/808 fuentes relevantes** a **12 componentes** mediante **44 grupos**, con documento/anchor comprobado para cada grupo. El grafo tiene **69/69 documentos vigentes alcanzables**, **429 documentos históricos clasificados**, **25 familias de artefactos** y **26 exclusiones justificadas**. El resultado de fuentes bajo `.context` incluye el JSON canónico y dos overrides WIP; no abre contenido de evidencia operativa excluida. El checker reportó 4,848 slots de relación ponderados por path: 2,093 verificados (43.2%), 1,236 pendientes (25.5%), 1,517 desconocidos (31.3%) y 2 no aplicables. **0/808** fuentes tienen verificadas sus seis dimensiones. `pending`/`unknown` conservan método de resolución y no son relaciones validadas.

El conteo editorial de 28 responsabilidades sigue como mapa de lectura, no denominador. Los 116 Markdown externos al vault, los 83 archivos en `docs/**` y los artefactos/caches/WIP se mantienen como familias, no se convierten en componentes independientes. El grupo `legacy-docs` incluye la resolución `.md.resolved` con estado histórico.

Para el paso 3, el conjunto calculado como HEAD tracked + scope R8 (92 paths) + scope R9 actualizado (51 paths) proyecta 441 fuentes del registro; **367 fuentes actuales** están fuera de ese conjunto propuesto y se conservan como WIP local, principalmente diagnósticos/fixtures C03. No se infiere ausencia de funcionalidad. El manifest y registro combinados deberán reconciliar esos paths antes de una ejecución CI real.

Dominios vigentes: arquitectura; tecnologías; frontend público/Admin; backend/BFF/Edge/Worker; database/diccionario/ledger; pipeline; seguridad; pruebas; operación; CI/CD; requerimientos sanitizados; hitos; decisiones; changelog; componentes. Las fichas enlazan entre sí y a fuentes, consumidores, contratos, pruebas, hitos y evidencia. Las notas históricas permanecen en sus rutas y se subordinan al corte de código/evidencia.

## Fuentes y reconstrucción

| Prioridad | Uso y autoridad | Límite |
|---|---|---|
| Estado operativo y alcance cliente sanitizado | `.context/estado_del_proyecto.md`, `AGENTS.md`, REQ-EST-001/adenda y atestación versionada | El privado no se leyó; la atestación disponible acota criterios y permisos locales. |
| Código/config/schema candidato | `web/src`, `web/functions`, `workers`, `supabase`, `scripts`, `config`, `db`, manifests, Docker, workflows y tests | Implementación observada en WIP local; presencia no prueba prueba o adopción. SQL local no prueba aplicación remota. |
| Resultados locales fechados | [R178](h3req1_g09_local_close_r178_2026-10-11.md), [R181/R182](h3req1_g10_r8_review_corrections_r181_2026-10-12.md) y evidencia por gate | Cada resultado solo vale para inputs, entorno y alcance de su acta. R181/R182 aplican a R8, no a este R9 documental. |
| Documentación vigente de ambos checkouts | Estado, índices, trazabilidad, tareas, ADR, notas y documentación técnica | Contradicciones se clasifican; nota histórica no gobierna runtime. El original no se escribe. |
| Historia Git local de ambos checkouts | `git log`, `git show`, diffs/versiones por path y `git blame` focalizados en contratos/migrations/workflows | No se hizo fetch/pull ni se usó GitHub para sustituir evidencia local. Un commit prueba existencia histórica, no ejecución, PASS o adopción. |
| Historia documental | ADR-0027 agregado en `70917eb5` y eliminado por `a92f1753` el 2026-08-25; notas sustituidas conservan corte/ubicación | No se restaura ni eleva a autoridad vigente. |

Se identificaron implementaciones actuales por sus símbolos y rutas en las páginas de dominio: por ejemplo, `EnrichmentWorker.__init__`, `_call_deepseek`, `_call_cloudflare`; `web/functions/_lib/admin-bff.ts` y su lista `ADMIN_RPC_ALLOWLIST`; `private.h2_public_courses_effective()` y `courses_public_effective`; workers FG; migraciones/funciones con número y path en el ledger database. Las pruebas se enlazan por suite/caso → componente → criterio → entorno → evidencia.

## Clasificación, contradicciones y desconocidos

- **Implementación candidata**: `EnrichmentWorker` usa endpoint OpenCode-compatible/DeepSeek y fallback Cloudflare; `AGENTS.md` describe Cloudflare → GitHub → Gemini. Se conserva como discrepancia código vs guía; proveedor remoto efectivo desconocido.
- **Validación local acreditada**: R178 GO G01–G09; R181/R182 revisión/scope/scanner de R8. No se hereda PASS a R9 documental ni a integración remota.
- **Adopción remota verificada aquí**: ninguna. No se consultaron Supabase, GitHub Settings/Actions, Cloudflare Pages/Workers o ambientes.
- **Database**: Pro sigue baseline autoritativo según guía operativa; migration, SQL y fixtures locales no demuestran ledger/schema remoto aplicado. PG17 se describe como fixture desechable. La revisión del diccionario confrontó nueve campos con SQL local; el último CHECK local de auditoría admite 12 acciones.
- **Schedules y release**: cron y branches públicos están declarados en YAML/guía; instalación, ejecución, branch protection, required checks, mecanismo Pages, SHA publicado, caché y smoke actuales desconocidos.
- **Seguridad**: bindings HMAC/Worker/DO, JWT y grants SQL se describen desde fuente local; provisionamiento y uso remoto desconocidos. `send-lead-emails` tiene riesgo estático de método/body/CORS/PII y fallback literal (valor omitido); caller/deploy desconocidos, no se declara incidente ni waiver.
- **Dependencia `braces`**: `web/package.json` y lock consumen `file:vendor/braces-3.0.4-h3.1.tgz`; el README de vendor identifica el commit fuente fijado, SHA-256 y nota que al 2026-10-03 no había release oficial. El estado upstream actual no se consultó; 904 tests son de suite upstream histórica, no de StudIAMatch. Owner/fecha de revisión siguen sin confirmación y no hay waiver. R8 incluye el tarball; este delta documental lo excluye. G10 debe elegir entre excepción documentada con auditoría/build renovados o reemplazo por release oficial con lock/build renovados. Hasta entonces, paquete funcional combinado no reconciliado.
- **Fuente ausente**: `.context/arquitectura_pipeline.md` no está en candidato; la ruta del original se inspeccionó solo lectura y está vacía. No se importó ni inventó contenido.

## Gates locales documentales

| Gate | Resultado de este corte | Evidencia y límite |
|---|---|---|
| Backup y preservación | Backup pre-edición y R8 PASS; checkpoint final externo | El checkpoint pre-diccionario tiene 18,607 paths cotejados; el backup pre-edición tiene 13,856. La captura ampliada inicial (18,324 paths) se conserva intacta pero quedó supersedida tras identificar 12 copias/archivos con dependencia. La copia filtrada usa 18,312 paths, excluye 283 `.next/cache` y esos 12 artefactos; mantiene outputs `.next` no-cache como evidencia generada histórica. Inventario, exclusiones y verificación fuente/copia/tar constan en sidecars externos y no entran en el paquete. |
| Registro fuentes/documentos | PASS de asignación; relaciones incompletas declaradas | Docker: 808/808 (100%) asignadas y con componente/anchor existentes; 12/12 componentes, 44 grupos, 69/69 documentos vigentes accesibles, 429 históricos clasificados. Seis dimensiones ponderadas por fuente: 2,093/4,848 verificadas (43.2%), 1,236 pendientes (25.5%), 1,517 desconocidas (31.3%), 2 N/A; 0/808 fuentes con todas las dimensiones verificadas. Toda relación pendiente/desconocida tiene un método de resolución registrado; no cuenta como validada. |
| Links, anchors, índices, autoridad | PASS local del checker | Docker: 4,959 links, 2,812 anchors, 69/69 documentos vigentes alcanzables; 25 familias de artefactos y 26 exclusiones justificadas. La única autoridad operativa sigue siendo `estado_del_proyecto.md`. |
| Autopruebas del checker | PASS | Rechaza una fuente nueva sin asignación; confirma ambas asignaciones Docker, sin leer YAML; valida que `inline_comment: none` no escanea contenido; rechaza root/extensión desconocidos, comentario discordante y path/anchor inexistentes. El runner local y un job futuro `documentation-integrity` invocan el mismo checker; GitHub no se configuró ni ejecutó. |
| Scope allowlist | PASS | Docker: `proposed=51|regex=6|exact=45|review_fixes=6/6|missing=0`. El tarball `braces` no está en paths propuestos. |
| Manifest package pins | PASS local; reread del registro/gate GO | Docker confirma 51/51 scope, 8/8 evidencia, 59 hashes y 3 artefactos con self-hash excluido. El revisor dio GO al delta de 25 familias y al checkpoint pre-final; el checkpoint final filtrado se controla con sidecars externos separados del PR. |
| Credential scanner | PASS tras corregir el check log; 60 paths exactos | Se ejecutó en Docker después de actualizar el registro y refrescar pins; no cubre todo el WIP ni stores remotos. |
| Workflow/path guard | PASS local parcial | `tests/test_protected_path_scope_guard.sh`: 8/8 (ordinary 3, newline 1, controls 1, malformed 3); YAML de ambos workflows parseado y allowlist reconciliada. `bash -n` valida el runner; ShellCheck y actionlint no están instalados en `studiamatch-dev`. Sin CI remoto. |
| Aceptación cliente / trazabilidad | PASS mediante llamadas locales directas | Docker invocó directamente 7/7 funciones de estado Obsidian y 10/10 de atestación sanitizada; `pytest` no está instalado. `STUDIAMATCH_PRIVATE_SOURCE_DIR` estaba unset, por lo que el check opcional de hashes retornó sin abrir fuente privada; no se leyó el documento privado. |
| Revisión independiente de ampliación | GO para contenido/registro y checkpoint pre-final | El revisor confirmó brevedad/unicidad, cobertura, navegación, familias/exclusiones, checker y límites. La copia final filtrada se conserva fuera del paquete; sus hashes e inventario se registran en sidecars externos. |

## Revisión de procedencia de RPC — 2026-10-12

El reread independiente del paquete identificó que la fila de ciclo de invitación atribuía toda la secuencia a migrations 20260918–28. El SQL local confirma definiciones/reiteraciones en `20260920_h3_invitation_edge_runtime.sql` y `20260921_h3_invitation_onboarding_rpc.sql`, corrección de aceptación en `20260928_h3_invitation_accept_email_regex_fix.sql`, revisiones/compensaciones y reconciliación en `20261001_h3_invitation_reservation_compensation.sql`, y definición de `admin_invitation_request_admit` en `20261002_h3_admin_quota_expand.sql`. Se actualizó `.context/database.md` con la secuencia y líneas de definición. No se añadió comentario a migrations históricas. La rerevisión independiente del corte corregido dio GO, confirmó 51/51 y 8/8 pins y no encontró contradicciones materiales. Los gates locales se repiten tras incorporar este dictamen en el paquete.

No se repiten suites funcionales/build/lint/UAT porque el delta documental no cambia inputs ejecutables del producto. Se reutiliza R178 y se declara el alcance histórico; no se ejecutan pruebas remotas. El actionlint faltante y la reconciliación del paquete `braces` quedan explícitos para G10, no se presentan como PASS. Los comandos, resultados y límites se guardan en el [registro de checks](h3req1_documentacion_checks_2026-10-12.txt).

## Paquete documental propuesto

El [cuerpo R9](h3req1_pr_body_draft_local_review_2026-10-12_r9_docs.md) usa la plantilla versionada y el [manifest R9](h3req1_pr_scope_manifest_2026-10-12_r9_docs.json) fija 51 paths de cambio y 8 evidencias seleccionadas (59 archivos con contenido hasheado). El check log se encuentra en el scope; el body y el manifest son artefactos explícitos del paquete. El manifest excluye su propio hash y el body no incluye su digest. El paquete R9 es documentación/tooling/allowlist únicamente y no incorpora tarball, caches, secretos, backups externos ni todo untracked.

### Tratamiento histórico R8→R9

El body y el manifiesto R8 se preservan byte por byte como artefactos históricos, y R8 conserva sus resultados de validación. Esto no significa que todo archivo fijado en el scope R8 mantenga hoy el mismo contenido en el candidato. R9 comparte 10 rutas con esos pins: cambia nueve versiones actuales y deja `web/vendor/README.md` idéntico. El paso 3 deberá superponer las nueve versiones R9 sobre el paquete funcional de R8, regenerar el manifiesto combinado y volver a comprobar consumidores; mantendrá intactos body, manifiesto y evidencia de resultados R8. La superposición no se ejecuta en este paso.

Rutas cuyo contenido actual pasa a R9 en el paso 3:

- `.context/00_INDICE.md`
- `.context/backlog_tareas/req_est_001_sprint_1/tarea_003_hito_3.md`
- `.context/estado_del_proyecto.md`
- `.context/hitos/h3req1_implementation_report.md`
- `.context/hitos/hito_003.md`
- `.context/sistema_db_supabase.md`
- `.github/pull_request_template.md`
- `.github/workflows/security-audit.yml`
- `README.md`

## Lecturas y decisiones para G10 / Development

Orden recomendado: `.context/estado_del_proyecto.md` → [índice](../indice.md) → arquitectura/database/seguridad/CI/CD/operación → requerimientos/hitos/decisiones → este corte y manifest/body → cuerpos/evidencias R8, R178, R181/R182.

G10 deberá cotejar por ambiente y SHA, en lectura autorizada: refs/branches y required checks; Stage 1/PWI/Stage 2 instalado y runs; Pro ledger/schema/RLS/grants/RPC; Pages build/ref/host/cache; Edge/Worker/DO bindings/secrets por nombre; redirects/hosts; cron y últimas corridas; logs/observabilidad; smoke Development. No inferir esos datos de commits, YAML o SQL local.

Decisión requerida para reconciliar integración H3: (A) autorizar mantener excepción `braces` en paquete funcional con owner/fecha y renovar scanner/auditoría/build; (B) sustituirlo por release oficial verificado, regenerar package lock y renovar build/seguridad; o (C) mantener el paquete documental R9 separado y posponer integración funcional hasta resolver A o B. El estado upstream, owner y deadline siguen desconocidos. Cualquier lectura/escritura remota, PR, merge, deploy o prueba remota requiere instrucción separada.
