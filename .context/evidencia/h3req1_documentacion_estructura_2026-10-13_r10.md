# Estructura documental Obsidian R10 — corte local 2026-10-13

> Esta evidencia registra la consolidación documental y su preservación local. No es autoridad operativa, no altera R8/R9 históricos y no acredita adopción remota.

> Adenda R11: a la fecha de corte R10 se conservaron los mapas técnicos y el inventario de cobertura. Esas rutas se consolidaron después; véase [consolidación R11](h3req1_documentacion_consolidacion_trazabilidad_2026-10-13_r11.md). Los conteos y resultados R10 se mantienen como evidencia de su propio corte.

## Navegación activa

1. `README.md` raíz: presentación breve con un enlace al vault.
2. `.context/indice.md`: única entrada principal Obsidian; recorre dominios, módulos, requerimientos, hitos, decisiones, evidencia y recorridos de transferencia.
3. `.context/estado_del_proyecto.md`: única autoridad operativa para corte, resultados, pendientes y siguiente paso. Las definiciones y la historia permanecen en sus páginas de dominio, decisiones y evidencia.
4. Páginas de dominio y módulos: `.context/arquitectura.md`, `tecnologias.md`, `frontend.md`, `backend.md`, `database.md`, `seguridad.md`, `pruebas.md`, `operacion.md`, `ci_cd.md` y `.context/componentes/*.md`.
5. Subnavegación conservada solo por propósito: README de decisiones, hitos y requerimientos; `_index.md` del backlog Sprint 1; y la entrada técnica de constructores exigida por `AGENTS.md`.

El inventario actual de fuentes asigna cada path a ficha/anchor en `.context/trazabilidad/registro_fuentes_componentes.json`; su Markdown es generado. Ningún índice duplicado ni página de estado alternativa queda activa.

## Inventario de README, índices y planes

La búsqueda local ejecutada el 2026-10-13 incluyó Markdown oculto del candidato y excluyó `.git`, worktrees, cachés, dependencias y `.context/evidencia/**`. Encontró 17 rutas activas cuyos nombres contienen `README`, `index`, `indice`, `plan` o `planner`; el grupo incluye plantillas y una atestación, además de páginas de navegación/planes. El mapa R10 fue sustituido por la [consolidación R11](h3req1_documentacion_consolidacion_trazabilidad_2026-10-13_r11.md).

| Decisión | Rutas y propósito |
|---|---|
| Conservar como entrada principal | `.context/indice.md`. |
| Conservar como presentación breve | `README.md` raíz; enlaza a `.context/indice.md` sin duplicar navegación ni contratos. |
| Fusionar y retirar la copia | `.context/componentes/index.md` se integró en `.context/indice.md` y salió del árbol activo. |
| Sustituir y retirar el índice previo | `.context/00_INDICE.md` fue sustituido por `.context/indice.md`; las referencias vigentes se migraron y no se requiere puente. |
| Conservar subnavegación específica | `.context/decisiones/README.md`, `.context/hitos/README.md`, `.context/requerimientos/README.md` y `.context/backlog_tareas/req_est_001_sprint_1/_index.md`. |
| Conservar guía de constructor, no índice (decisión R10) | `.context/trazabilidad/00_entrada_tecnica.md`, entonces requerida por `AGENTS.md`; su contenido útil se integró al protocolo y se retiró en R11 tras actualizar consumidores. |
| Conservar como guías/plantillas distintas | `.github/agents/planner.md` no es un plan del producto; las plantillas de `.context/seguimiento/` no son planes activos ni autoridad. |
| Conservar por alcance/precedencia o historia | Los siete documentos de `.context/operaciones/` listados en el mapa. Solo `plan_vinculante_nuevo_pedido_2026_08_25.md` conserva alcance vinculante; los demás tienen consumidores contractuales/históricos y quedan subordinados al estado operativo. |
| Conservar como atestación, no plan | `.context/evidencias_cliente/sprint_1/atestado_aceptacion_plan_ingesta_editorial_auditoria_2026-10-01.md`; es atestación cliente sanitizada, no autorización ni evidencia de ejecución. |
| Retirar boilerplate de módulo | `web/README.md`; su contenido se sustituye por documentación frontend y CI/CD. `web/vendor/README.md` permanece como metadata de dependencia y no es ficha de producto. |
| Retirar plan inicial obsoleto | `IMPLEMENTATION_PLAN.md`; la navegación, autoridad y definiciones se distribuyen entre índice, estado, dominios, hitos y decisiones. |
| Retirar tres planes de `docs/` | `docs/PLAN_REMEDIACION_DEFINITIVA.md`, `docs/architecture/PIPELINE_PLAN.md` y `docs/orquestador-sdlc/01_BUSINESS_PLAN_INFRA.md`; la configuración actual se contrasta con código, workflow y fichas vigentes, sin rescatar como actuales sus precios, frecuencias o propuestas vencidas. |
| Archivar, no borrar | `plan_go_h3req1_local_development_2026-10-02.md`, `h3req1_remediation_plan_2026-09-24.md` y `h3req1_ruta_ejecutable_go_pr_y_remoto_2026-10-06.md` se movieron a `.context/evidencia/planes_historicos/`, con origen, sustitución, referencias y hashes indicados en el mapa. |
| Conservar fuera de navegación activa | 14 README dentro de snapshots sellados de `.context/evidencia/**`; se preservan junto a sus manifiestos. `.pytest_cache/README.md` es cache generado. Ambos grupos se excluyen del paquete. |

El mismo filtro de nombres en el checkout original encontró 19 rutas. Ese árbol e historia permanecieron en solo lectura. La diferencia de conteo no es una equivalencia de contenido: incluye el inventario propio de cada checkout. `web/vendor/README.md` y el cache se inventarían por separado como dependencia y archivo generado, no como documentación de módulo.

## Cambios exactos de ruta

| Origen | Destino/decisión | Preservación |
|---|---|---|
| `.context/00_INDICE.md` | Retirado; reemplazado por `.context/indice.md`. | Snapshot externo y referencias históricas R7/R8/R9 intactos. |
| `.context/componentes/index.md` | Contenido de navegación fusionado en `.context/indice.md`; archivo retirado. | Snapshot externo; fichas individuales permanecen. |
| `web/README.md` | Retirado; destino canónico frontend/tecnologías/CI-CD. | Snapshot externo; `web/vendor/README.md` permanece. |
| `IMPLEMENTATION_PLAN.md` | Retirado; información vigente distribuida por autoridad/dominio, propuestas vencidas no promovidas. | Snapshot externo y referencias históricas intactas. |
| Los tres planes iniciales de `docs/` | Retirados; sustituidos por arquitectura, frontend, pipeline, operación, CI/CD y seguridad según responsabilidad. | Copias/hash recuperables en los respaldos externos; el mapa registra cada fuente y sustituto. |
| Tres planes H3REQ1 iniciales bajo `operaciones/` | Movidos, sin borrar, a `evidencia/planes_historicos/`. | Hash original y ruta destino preservados; enlaces vigentes corregidos. |

R8, R9, snapshots de build, resultados sellados y documentos de aceptación no se alteraron. `00_INDICE.md` no requiere puente porque las referencias vigentes ya se migraron; su path solo permanece en material que conserva la historia de ese corte.

## Respaldos externos verificados

Los respaldos están fuera de ambos checkouts y no forman parte de ningún paquete propuesto. Cada overlay válido conserva bytes del estado anterior a la siguiente edición, compara cada copia con su fuente y registra SHA-256 y tamaño por path.

| Snapshot | Inventario/hash verificable | Alcance |
|---|---|---|
| `/home/romel/backups/studiamatch-docs-2026-10-12/checkpoint_before_module_documentation_rewrite_2026-10-12` | `documentation_snapshot.tar`, SHA-256 `78b95d125300e3e4e6762f879969910479dbcb4dbc218fb9ea4c8e2779233366` | Snapshot filtrado integral preescritura; las reglas de exclusión se detallan en la evidencia de preservación R9. |
| `/home/romel/backups/studiamatch-docs-2026-10-12/supplemental_before_r10_structure_close_20261013T051343Z` | `MANIFEST.tsv`, SHA-256 `53cd40b91dfa054e7390e0a9ef5c84205655afe09f7319166ed0c9a91d55143b`; 15 files / 2,611,354 bytes | Estado documental superpuesto antes del cierre de estructura. |
| `/home/romel/backups/studiamatch-docs-2026-10-12/supplemental_before_r10_semantic_and_map_retry1_20261013T053900Z` | `MANIFEST.tsv`, SHA-256 `b1f7d38f993abaf710aecb1e16fb34446f0a361036a03981a9d639f0d0c5faf2`; 21 files | Estado exacto previo al lote de relaciones C03 y cambios de página/registro. |
| `/home/romel/backups/studiamatch-docs-2026-10-12/supplemental_before_r10_reconcile_20261013T054501Z` | `MANIFEST.tsv`, SHA-256 `446b892c5e05b08c7fd908286ca09fdce8fb18f5b90462b59c2f6cd810883d89`; 22 files | Superposición anterior a actualizar estado, mapa, inventario, changelog y paquete. |
| `/home/romel/backups/studiamatch-docs-2026-10-12/supplemental_before_final_r10_state_20261013T054906Z` | `MANIFEST.tsv`, SHA-256 `04e99505374f5d94b537403cabb3d208b49747849c6022c2c33c31ca839d8716`; 18 files | Estado exacto antes de la última reconciliación de corte. |
| `/home/romel/backups/studiamatch-docs-2026-10-12/supplemental_before_r10_structure_reconcile_20261013T055128Z` | `MANIFEST.tsv`, SHA-256 `a9f2a378fcb6e690e9a2a0990dc79238f21ca9c00738ee569b674c27366a7cf8`; 8 files / 74,899 bytes | README, índice, estado, changelog, mapa, inventario y las dos evidencias R10 copiadas con tamaño y SHA-256 comparados contra sus originales antes de esta edición. |
| `/home/romel/backups/studiamatch-docs-2026-10-12/supplemental_before_r10_scope_test_fix_20261013T055327Z` | `MANIFEST.tsv`, SHA-256 `6d35b6c7e2e81aac99dbc1561d34f9dac8e5701a101ba2a7c30afd7cbc0bd4e7`; 1 file / 8,749 bytes | Versión del test antes de corregir la ruta histórica esperada; fuente y copia comparadas byte a byte. |
| `/home/romel/backups/studiamatch-docs-2026-10-12/supplemental_before_r10_validation_reconcile_20261013T055357Z` | `MANIFEST.tsv`, SHA-256 `59ccbf9f13a053b0fa42d20dd5e0f152bdf5478839f5ecc943700bd3ffa9e5ba`; 6 files / 66,932 bytes | Estado, changelog, mapa, esta evidencia, reanudación y test después de la corrección de navegación, antes de registrar resultados de validación. |
| `/home/romel/backups/studiamatch-docs-2026-10-12/supplemental_before_r10_independent_review_reconcile_20261013T055819Z` | `MANIFEST.tsv`, SHA-256 `cbadfc471982cce15f20d62671dddf14e60797d9dd97cf2f6f10eadeed5494a6`; 5 files / 60,798 bytes | Estado, changelog, mapa y evidencias R10 copiados y comparados antes de precisar el criterio de búsqueda y registrar la revisión independiente. |

El intento inicial `supplemental_before_r10_semantic_and_map_20261013T053840Z` no verificó los paths al copiar y no se usa como respaldo; quedó intacto fuera de los checkouts. Los overlays válidos y el snapshot base se preservan sin limpieza.

## Evidencia y límites de este corte

Después de separar las familias C03 y registrar esta evidencia más la reanudación R10, el checker Docker registró 801/801 fuentes asignadas y enlazadas, 12/12 componentes con ficha, 249 grupos y 77/77 documentos activos alcanzables. Las relaciones locales fueron 2,903/4,715 verificadas (61.6%), 1,812 pendientes (38.4%), cero `unknown` y 91 `not_applicable`; el gate estructural pasa, pero el semántico sigue incompleto. Cinco verificaciones remotas continúan pendientes. El detalle y la reanudación viven en [relaciones semánticas C03](h3req1_relaciones_semanticas_c03_2026-10-13.md) y [reanudación R10](h3req1_documentacion_semantica_reanudacion_2026-10-13_r10.md).

La suite documental en Docker encontró una aserción desactualizada de la evidencia de estructura 2026-10-12 en `tests/test_obsidian_context_state.py`; se cambió al path R10 vigente y las suites `test_obsidian_context_state.py` y `test_protected_workflow_review.py` cerraron con **21 passed**. También pasaron el self-test negativo del checker, el gate normal (5,332 links, 3,263 anchors, 77/77 alcanzables), `tests/test_protected_path_scope_guard.sh` y el scanner de credenciales sobre los documentos R10, changelog, mapa, estado y test modificado.

La revisión independiente de estructura del 2026-10-13 dio **GO sin bloqueantes**. Confirmó README raíz → índice único → autoridad operativa, las decisiones de navegación/archivo, la integridad de los conteos 17/14/1/1 y 77/77, y la preservación declarada de R8/R9. Sugirió precisar que el filtro de 17 rutas busca términos contenidos en el nombre; se incorporó esa precisión. La revisión no repitió gates ni examinó snapshots sellados. No se repitieron pruebas funcionales, Compose ni servicios remotos.

El gate estructural y su revisión independiente están cerrados. El manifiesto/cuerpo R10 propuesto queda pendiente hasta reconciliar el paquete después del trabajo semántico; no declara transferencia integral. Ningún resultado R178/R181/R182 se renueva por cambios exclusivamente documentales.

[Índice principal](../indice.md) · [Estado operativo](../estado_del_proyecto.md) · [Consolidación R11](h3req1_documentacion_consolidacion_trazabilidad_2026-10-13_r11.md)
