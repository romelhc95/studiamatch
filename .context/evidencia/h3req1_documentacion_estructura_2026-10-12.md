# Reorganización de la estructura documental

> Corte local: 2026-10-12. La fecha del nombre identifica el ciclo documental; esta nota registra verificaciones realizadas localmente el 2026-10-13. No acredita adopción remota.

## Regla de navegación vigente

- `README.md` presenta StudIAMatch en breve y enlaza una sola vez a `.context/indice.md`.
- `.context/indice.md` es la única entrada principal de Obsidian y enlaza por dominio, módulo, hito, decisión, transferencia y evidencia.
- `.context/estado_del_proyecto.md` es la única autoridad operativa del corte: resultados, pendientes y siguiente paso. Los contratos de sistema, historia extensa y guías de cambio viven en sus documentos de dominio y evidencia.
- Los README e índices subordinados solo ordenan registros de su propio dominio. El registro JSON de `.context/trazabilidad/` conserva las asignaciones fuente→componente→documento/anchor; la vista Markdown es generada.

## Preservación y recuperación

La copia completa previa a las retiradas locales está fuera de ambos checkouts:

`/home/romel/backups/studiamatch-docs-2026-10-12/checkpoint_structure_review_pretrim_20261013T025404Z`

El snapshot contiene 12,320 archivos y 1,128,391,265 bytes; su inventario de rutas es `inventory/included_paths.txt` y el inventario de hashes por archivo es `inventory/files.sha256.jsonl`. Incluye `.context`, la documentación raíz y los documentos inventariados de la fase, excluyendo secretos operativos, dependencias y caches. La comprobación previa comparó los archivos del snapshot con las fuentes que se iban a retirar. Este checkpoint se tomó después de que el trabajo documental R9 ya había empezado; por eso no se presenta como copia anterior a la refactorización completa.

Las ediciones documentales hechas después de ese checkpoint se preservaron además antes de este ciclo de corrección en:

`/home/romel/backups/studiamatch-docs-2026-10-12/supplemental_post_checkpoint_before_continuation_20261013T032102Z`

El overlay conserva 24 archivos y 2,973,117 bytes. `inventory/paths.txt` lista las rutas y `inventory/files.sha256` permite comprobar cada copia. Un recorrido archivo a archivo confirmó que el SHA-256 de cada origen coincidía con el del overlay. Para recuperar ese corte, se usa el checkpoint completo como base y se sobreponen esas 24 versiones posteriores. Las ediciones que sigan a este registro requieren un overlay actualizado antes de concluir.

El workspace de Obsidian tuvo también una copia puntual anterior a cambiar la pestaña abierta de `00_INDICE.md` a `indice.md`:

`/home/romel/backups/studiamatch-docs-2026-10-12/supplemental_workspace_before_index_migration_20261013T030000Z`

Su inventario fija el SHA-256 preedición `5cd170021a612adfa0f1fda85a572138caf03875a8484593028f84523f09bfe0` y los 7,688 bytes del archivo. La versión actual quedó incluida en el overlay posterior. El archivo no se incorpora al paquete de integración.

El estado operativo sustituido se conserva localmente sin cambios; su cuerpo anterior al prefijo de archivo tiene SHA-256 `51942bd6232052aeaad5391fef4f23a7ab7a80186b79ab077fb40d890b995124`. El enlace público apunta a la copia sanitizada R18: conserva ese hash de origen como referencia, pero su propio contenido tiene redacciones y un hash distinto fijado por el manifiesto. El archivo actual mantiene solo el corte operativo y enlaza esta historia; ninguna copia histórica es autoridad vigente.

Antes de corregir la duplicación hallada en la ficha de mantenimiento y reconciliar el inventario de planes, se tomó un overlay local adicional, fuera de ambos checkouts:

`/home/romel/backups/studiamatch-docs-2026-10-12/supplemental_before_structure_cleanup_20261013T034533Z`

Contiene 20 documentos y tooling con rutas en `inventory/paths.txt`, sus SHA-256 en `inventory/files.sha256` y el hash del manifiesto en `inventory/manifest.sha256` (`6d901d072f5a3a2bca4247c32097df309e0721e87e015b120d24a21760e79e4a`). `sha256sum -c` pasó para los 20 archivos y `cmp` confirmó igualdad byte a byte con el candidato al tomar la copia. Es un overlay de continuación, no el backup previo a la refactorización; se combina con el checkpoint completo y los overlays anteriores. No se incluye en el paquete propuesto. Los checksums históricos no se alteran.

Antes de editar las fichas DB y las relaciones de baseline/seed/rollback/helper se guardó otro overlay fuera de ambos checkouts:

`/home/romel/backups/studiamatch-docs-2026-10-12/supplemental_before_relation_cleanup_20261013T040322Z`

Contiene 21 archivos, 2,821,355 bytes. `inventory/files.json` fija rutas, tamaños y hashes; `inventory/files.sha256` permite comprobar cada copia y `inventory/manifest.sha256` registra el SHA-256 `431c4b42b1687852bba1f41c6a51c0cf348ce5791585d13894869248cbd691ac`. La creación verificó SHA-256 y comparación byte a byte origen/copia. Es una copia del estado que ya incluía los cambios R9; no se presenta como backup pre-refactor, no entra al paquete y no se limpia. Se combina con el checkpoint completo y overlays previos para recuperar ese corte documental.

Antes de retirar del directorio operativo los planes H3REQ1 ya sustituidos y actualizar su navegación, se guardó un overlay fuera de ambos checkouts:

`/home/romel/backups/studiamatch-docs-2026-10-12/supplemental_before_single_active_structure_20261013T042513Z`

Contiene 33 documentos/consumidores afectados y 2,989,987 bytes. `inventory/files.json` registra ruta, tamaño y SHA-256; `inventory/files.sha256` y `inventory/manifest.sha256` (SHA-256 `1a00161ef662784b4e584ef6cf80a9b69a0b566a43c4c19d7529e504545692cb`) permiten verificar la copia. La creación comparó cada copia byte por byte con su fuente. Este overlay es posterior al inicio de R9 y anterior a estos movimientos: no se presenta como backup pre-refactor ni reemplaza el checkpoint completo. Junto con el checkpoint y overlays anteriores preserva los documentos/consumidores afectados en este cambio. No se incluye al paquete ni se limpia.

Antes de resolver relaciones de infraestructura, reemplazar referencias genéricas de configuración y completar el inventario de guías/comandos se creó:

`/home/romel/backups/studiamatch-docs-2026-10-12/supplemental_before_infra_workflow_split_20261013T043337Z`

Contiene siete archivos de documentación/configuración versionada, 2,337,557 bytes; su inventario y manifiesto registran SHA-256 `173e12496a975dfe96d99e884ca26a3173a271d0961d48c4d003885a25e67396`. Las copias se verificaron contra las fuentes al tomarlas. Es un overlay posterior a R9, fuera del paquete; se conserva sin limpieza.

Antes de la corrección final de relaciones/estructura se preservó un overlay adicional:

`/home/romel/backups/studiamatch-docs-2026-10-12/supplemental_before_structure_resolution_20261013T043820Z`

Incluye ocho documentos vigentes/derivados (2,464,629 bytes) con SHA-256 por archivo en `inventory/files.json`; su manifiesto tiene SHA-256 `ba3a5970daa1920323fe6a23b6c5a5e64c8371b01820554c639013d32278a7ce`. Cada copia se comparó byte por byte con el candidato. Es un overlay posterior a R9, no un backup previo a la refactorización; no se incluye ni se limpia.

Antes de reparar dos enlaces a planes H3 archivados se preservaron las notas originales en:

`/home/romel/backups/studiamatch-docs-2026-10-12/supplemental_before_historical_link_repair_20261013T044000Z`

El overlay contiene `.context/operaciones/plan_cierre_integral_h3req1_2026-10-04.md` y `.context/seguimiento/mapa_documental_obsidian_2026-10-04.md` (65,187 bytes); `inventory/files.json` registra ambos SHA-256 y su manifiesto tiene SHA-256 `aea4da5708f3cbf8df2491014b18b8407f332a3103f910b7f957ba8191424f16`. La creación verificó igualdad byte por byte. Se actualizaron solo los destinos Markdown para que apunten a la ubicación histórica vigente. No se incluyen ni limpian los backups.

Antes de archivar la ruta H3 desfasada y corregir sus referencias se preservaron 23 documentos/consumidores en el overlay externo `/home/romel/backups/studiamatch-docs-2026-10-12/supplemental_before_h3_route_archive_20261013T044540Z` (3,163,109 bytes). El inventario por path/hash está en `inventory/files.json` y `inventory/files.sha256`; el manifiesto SHA-256 es `49144cad2e5796849a7db88ec54da84d70ed6397b4db7ae7ca6f35859b94e1a7`. Se comparó cada copia byte a byte con la fuente. Es un overlay posterior al inicio de R9, no un backup previo a la refactorización. Se conserva fuera del paquete y no se limpia.

Antes de esta reconciliación final de navegación se preservaron 14 documentos/tooling en `/home/romel/backups/studiamatch-docs-2026-10-12/supplemental_before_final_structure_reconciliation_20261013T050512Z` (2,616,663 bytes). Incluye README, índice, estado, mapa, inventario, changelog, trackers/evidencia, registro JSON/vista, workflow y pruebas afectadas. `inventory/files.json` registra path, tamaño, SHA-256 de origen y copia; `inventory/manifest.sha256` fija el inventario con SHA-256 `641a0e4d81ebbef054294477904ae498a14b0ff5aa42fcad5cebbcb7b6f01222`. Cada archivo se copió y comparó byte a byte. Es un overlay del estado ya editado durante R9 y no se presenta como backup pre-refactor. Está fuera del paquete y no se limpia.

## Índices, README y planes

| Ruta | Decisión | Motivo y destino vigente | Copia verificable |
|---|---|---|---|
| `README.md` raíz | Conservar y reducir a presentación breve | Enlace único a `.context/indice.md`; el índice conduce al estado y a los dominios. | Versión previa en checkpoint; versión intermedia en overlay. |
| `.context/indice.md` | Conservar como entrada principal única | Navega dominios y módulos sin concentrar sus definiciones. | Versión intermedia en overlay; estado final se captura en el overlay de cierre. |
| `.context/00_INDICE.md` | Retirado del árbol activo; no queda puente | Índice duplicado; referencias activas migradas a `indice.md`; el workspace apunta al índice principal y no se halló consumidor de runtime ni de tooling que requiera la ruta antigua. R7/R8 y manifiestos anteriores se conservan como snapshots sin editar. | Checkpoint `snapshot/.context/00_INDICE.md`; SHA-256 `b08491f227286fd10864ae56bc4240eb20d61bf505d625147c0bb2a91b293525`. |
| `.context/trazabilidad/00_entrada_tecnica.md` | R9 la conservó como entrada técnica requerida por AGENTS; se retiró en R11 luego de migrar sus reglas y actualizar consumidores | Contratos, consumidores, impacto y evidencia se integraron en el índice único, protocolo y fichas de dominio vigentes | La fila conserva la decisión histórica R9; el tratamiento actual y la copia exacta están en la [consolidación R11](h3req1_documentacion_consolidacion_trazabilidad_2026-10-13_r11.md). |
| `.context/componentes/index.md` | Retirar del árbol activo | Catálogo redundante; lista de módulos incorporada en la tabla del índice principal, que enlaza las fichas canónicas. | Checkpoint `snapshot/.context/componentes/index.md`; SHA-256 `7a265855f87e9aa17e91b73f95f6d6d60799e520c5080f8ece18ba7757163640`. |
| Índices/README subordinados, plantillas, guía planner y atestación con nombre `plan` | Conservar por propósito separado; su clasificación se conserva en el mapa R9 y la sustitución de ese mapa consta en la [consolidación R11](h3req1_documentacion_consolidacion_trazabilidad_2026-10-13_r11.md#rutas-consolidadas) | Incluye tres README de dominio, un `_index.md` de backlog, dos plantillas de seguimiento, `.github/agents/planner.md` y una atestación sanitizada cuyo nombre incluye `plan`; ninguno duplica la entrada principal o el estado operativo. | Checkpoint completo; referencias y función preservadas. |
| `web/README.md` | Retirar | Era boilerplate del starter; sus destinos son frontend, ficha web pública, tecnologías y CI/CD. `web/vendor/README.md` es metadata distinta de dependencia y permanece. | Checkpoint `snapshot/web/README.md`; SHA-256 `5ee0c8cf1d7fe995f619d54fee84d15c4bbb8f08e06f6437c060c748111a4497`. |
| `web/vendor/README.md` | Conservar como metadata de procedencia de una dependencia vendorizada; no es README de módulo StudIAMatch | Enlazado desde tecnologías/seguridad; no duplica la ficha canónica frontend | No es entrada Obsidian ni definición del módulo; su estado upstream queda limitado a la fecha que declara el archivo. |
| 14 README de `web/` y `web/vendor/` bajo snapshots de evidencia | Conservar sin editar como entradas dentro de builds/capturas sellados; no son documentación activa ni componentes | Las rutas exactas permanecen en el backup R9; la [consolidación R11](h3req1_documentacion_consolidacion_trazabilidad_2026-10-13_r11.md) mantiene la clasificación sin cambiar snapshots. | Permanecen junto a sus manifests/actas; hashes históricos no se reescriben. |
| `.pytest_cache/README.md` | Excluir como cache generado; no tratarlo como índice ni documento de producto | El filename scan lo encontró en el checkout, fuera del inventario de documentación activa. | No incluir al paquete; no limpiar ni inferir ejecución por presencia. |
| `IMPLEMENTATION_PLAN.md` raíz | Retirado como plan obsoleto | Sus propuestas y fases no acreditaban el estado actual. Planner, SDLC chief y health monitor remiten a AGENTS, estado, índice y protocolo. No se transfirieron propuestas futuras como hechos. | Checkpoint `snapshot/IMPLEMENTATION_PLAN.md`; SHA-256 `b212f593477ff86bfc9771f5205d02746dbafcea052f08d4b91a1a89d4eb3dde`. |
| `docs/PLAN_REMEDIACION_DEFINITIVA.md` | Retirar propuesta anticuada | Conteos de datos, diagnóstico RPC y operaciones dependían de un corte previo; el comportamiento actual se documenta desde fuentes locales. | Checkpoint `snapshot/docs/PLAN_REMEDIACION_DEFINITIVA.md`; SHA-256 `e8e657722cadb6816de6cb73ea304f0fb74d0217f32ee491e42bcfe0102f2559`. |
| `docs/architecture/PIPELINE_PLAN.md` | Retirar propuesta de despliegue obsoleta | Workflows, proveedor y horarios propuestos no acreditaban configuración vigente; las páginas de pipeline y CI/CD distinguen definición local de adopción. | Checkpoint `snapshot/docs/architecture/PIPELINE_PLAN.md`; SHA-256 `efaf14327f79dc896b9c809ba1be7ba14119828206a8e4d0edeb12f2c438c614`. |
| `docs/orquestador-sdlc/01_BUSINESS_PLAN_INFRA.md` | Retirar proyección obsoleta | Precios y proyección de proveedor no se trasladan como hechos. La arquitectura, operación y tecnologías se reconstruyen desde el candidato. | Checkpoint `snapshot/docs/orquestador-sdlc/01_BUSINESS_PLAN_INFRA.md`; SHA-256 `cc5902b131d84139ef460f5dfebbc0a2f9fe719b780a7cfc81b9ff618ea9106`. Verificado con `sha256sum` contra la copia conservada. |
| Planes fechados bajo `.context/operaciones/` | Conservar los siete documentos con propósito contractual, de precedencia o evidencia diferente; dos planes H3REQ1 sustituidos pasan a `evidencia/planes_historicos/` | El plan vinculante conserva alcance; `plan_maestro` ordena precedencias; H2/H3 y F10.9 conservan planes, contratos, atestaciones y evidencia fechados. Solo el plan vinculante se enlaza como alcance activo desde el índice. | La [consolidación R11](h3req1_documentacion_consolidacion_trazabilidad_2026-10-13_r11.md) preserva decisiones, destinos y backups verificados. |
| `operaciones/plan_go_h3req1_local_development_2026-10-02.md` → `evidencia/planes_historicos/plan_go_h3req1_local_development_2026-10-02.md` | Archivar como historia: sustituido por el plan de cierre del 2026-10-04; no es una ruta activa de trabajo | El test de contrato Admin y la allowlist local cubren la eliminación y el destino; enlaces desde el cuerpo archivado se rebasaron. | SHA original `f064cf27473ab0f552992afc83f8443c8a8cef534476a7eb164d195755196ebc`; copia externa en checkpoint completo y overlay pre-movimiento. R8/R9 siguen byte-identical. |
| `operaciones/h3req1_remediation_plan_2026-09-24.md` → `evidencia/planes_historicos/h3req1_remediation_plan_2026-09-24.md` | Archivar como historia: checklist sustituido por el plan de cierre del 2026-10-04; no es estado actual | No se halló consumer ejecutable ni test en el alcance candidato; la navegación vigente queda en el mapa y el índice. | SHA original `4dedc2e05d60d2267ac212eab99f7d4a02b7275dead7d8def3d98e3bf18b5f51`; copia externa en checkpoint completo y overlay pre-movimiento. R8/R9 siguen byte-identical. |
| `operaciones/h3req1_ruta_ejecutable_go_pr_y_remoto_2026-10-06.md` → `evidencia/planes_historicos/h3req1_ruta_ejecutable_go_pr_y_remoto_2026-10-06.md` | Archivar como historia: el NO-GO y la “continuación vigente” del 2026-10-08 preceden al cierre local R178/R181/R182 | Se actualizaron la entrada técnica, protocolo constructor, índice, plan de cierre, notas de seguimiento, mapa, registro y allowlist; el histórico de estado/manifiestos sellados no se reescribió. | SHA original `cc875a57143c4dadfb9e177c1c6238e13c05312e00204846bb43f5fc92818570`, copia verificada en el overlay indicado arriba; el archivo rebasado contiene 28 enlaces locales y SHA `b9c980bbe3f3f3333fd43425c60641c19f583a539158991b1b19189c689537e7`. Se conserva el contenido, cambia su clasificación/ruta. |
| Reportes de `docs/**`, R7/R8/R9 y evidencia fechada | Conservar | Explican su corte histórico; menciones antiguas a rutas retiradas no se reescriben para simular que nunca existieron. | R7/R8/R9 y evidencia sellada permanecen inalterados. |

El informe `.context/evidencia/h3req1_documentacion_integral_2026-10-12.md` se conserva como corte inicial histórico: incluye el estado entonces propuesto para `00_INDICE.md` y métricas previas. El changelog lo rotula como histórico y enlaza esta evidencia de estructura para el estado vigente; no se usa como índice, plan activo ni autoridad de cobertura.

El filename scan de Markdown dio 35 coincidencias en el candidato incluyendo `.pytest_cache/README.md`; 34 quedan fuera de esa cache, de las cuales 14 son README de snapshots y 20 son documentos/guías/planes inventariados. En el checkout original se encontraron 19 paths al nivel raíz del checkout al excluir caches y `.worktrees/`, que contiene checkouts independientes y no se editó. El original siguió de solo lectura. La [consolidación R11](h3req1_documentacion_consolidacion_trazabilidad_2026-10-13_r11.md) preserva la clasificación vigente de rutas después retiradas.

## Referencias y consumidores revisados

Antes de retirar los paths se comparó cada archivo con el checkpoint y su manifiesto, se comprobaron destinos y anchors, y se buscaron referencias en los checkouts locales. El alcance de búsqueda incluyó enlaces Markdown/Obsidian, anchors, `.context/.obsidian/workspace.json`, `.github/agents/`, `.github/commands/`, `.github/workflows/`, `tests/`, `scripts/`, `db/`, `web/`, `workers/` y `supabase/`, además del inventario JSON y manifiestos locales disponibles. Los directorios de dependencia y evidencia sellada se excluyeron de la búsqueda de consumidores activos.

El checkout original `/home/romel/src/studiamatch` se mantuvo en solo lectura; contiene su propia historia y puede seguir teniendo los documentos antiguos. Esto no crea una dependencia del candidato ni autoriza copiar o editar el original. No se consultó GitHub ni otro servicio remoto.

Las tres guías de agentes que antes instruían crear/leer el plan raíz se actualizaron. El test documental ahora obtiene hechos históricos de sus documentos de dominio/archivo, no del cuerpo extenso de estado. La allowlist local del workflow apunta a `indice.md`; se preparó el job de integridad documental para el agregador `security-audit`, sin configurar ni ejecutar GitHub.

## Gate y estado probatorio

`bash scripts/security/run_documentation_integrity.sh --render` corrió en el contenedor `studiamatch-dev`; actualiza solo la vista derivada del registro. La primera evaluación normal posterior a las retiradas detectó relaciones locales aún no acreditadas, anclas viejas, un enlace de render con base incorrecta, la nueva evidencia todavía ausente y un marcador `.stfolder/` sin clasificar. Ese resultado fue FAIL y no se cuenta como PASS. El marcador se clasificó por su ruta sin abrir su contenido. Se eliminó un bloque duplicado de navegación/fuentes en la ficha de mantenimiento y se documentaron los planes retenidos por path en el mapa. Los resultados de gates y revisión independiente se actualizarán al final del corte actual; las relaciones locales sin resolver siguen en el punto de reanudación.

La documentación y evidencia nuevas se incluirán explícitamente en el manifiesto y cuerpo propuestos del paso 3. No se alteran snapshots históricos ni el body/manifest/resultados R8. Este archivo y el paquete local no abren PR, no se integran en la rama ni inician pruebas remotas.

## Navegación relacionada

[Índice principal](../indice.md) · [Consolidación R11](h3req1_documentacion_consolidacion_trazabilidad_2026-10-13_r11.md) · [Estado operativo](../estado_del_proyecto.md) · [Registro verificable](../trazabilidad/registro_fuentes_componentes.md)
