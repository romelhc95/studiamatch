# Cierre de transferencia documental local R12 — 2026-10-13

> Evidencia del corte local; no es una autoridad paralela. El estado operativo vigente está únicamente en [estado del proyecto](../estado_del_proyecto.md), la navegación en el [índice Obsidian](../indice.md), y las asignaciones en el [registro JSON canónico](../trazabilidad/registro_fuentes_componentes.json). No acredita adopción remota ni autoriza la etapa de integración/Development.

## Corte y alcance

- Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama `feat/h3req1-sync-20261002`, HEAD baseline `4eb4d877a50b012bb630a129bd0c74482c33be9c`; el HEAD no representa el WIP completo.
- Original: `/home/romel/src/studiamatch`, HEAD `7650093b05a820e8e6faf9ec711e12fab8b50398`, solo lectura.
- Alcance: comprensión, navegación y mantenimiento documental del frontend público, Admin/BFF, DB, pipeline, utilidades, mantenimiento, canarios, seguridad, workflows, pruebas, operación, decisiones e historia local.
- No se desarrolló funcionalidad. Los comentarios `StudIAMatch-Docs` solo enlazan la sección asignada. Los resultados funcionales R178 y la revisión R181/R182 se preservan y solo se reutilizan para inputs que no cambiaron.
- R8/R9 permanecen como antecedentes; esta evidencia y el borrador R12 no reemplazan ni reescriben sus resultados.

## Cobertura y denominadores

R2 dio GO para contenido, relaciones, historia, exclusiones y navegación; R3 dio GO al paquete de ese corte. R4 encontró un P2 en la clasificación de paths de una prueba; la corrección pasa su prueba focalizada y R5 la revisó junto con el paquete final sin bloqueantes. Tras registrar R5 se repitieron gate normal/self-test, scope guard, pins y scanner. `verified` expresa una relación sustentada por fuente concreta; `not_applicable` requiere motivo; ninguna cifra de relaciones equivale a pruebas funcionales.

| Medida | Resultado R12 | Definición |
|---|---:|---|
| Fuentes relevantes asignadas | 801/801 | Paths fuente distintos del inventario del candidato; cada uno tiene componente, documento y anchor exactos. |
| Fuentes completamente documentadas | 801/801 | Asignación, propósito y seis dimensiones relacionales acreditadas por el registro, con N/A justificados por separado. |
| Componentes documentados | 14/14 | Fichas de componente activas con navegación de dominio. |
| Grupos de responsabilidad | 262 | Segmentación semántica que evita tratar fuentes diferentes como una sola relación genérica. |
| Documentos activos navegables | 80/80 | Documentos de Obsidian activos alcanzables desde `.context/indice.md`; el estado conserva autoridad operativa única. |
| Relaciones locales comprobadas | 4,715/4,715 | Slots aplicables de consumers, contracts, data, tests/evidence, operations y provenance; ponderados por paths del grupo. |
| Relaciones N/A justificadas | 91/91 | Slots no aplicables con motivo específico. |
| Relaciones locales pendientes | 0/4,806 | `pending`, `unknown` o inválidas; no se excluyen del denominador. |
| Fuentes con dimensiones relacionales resueltas | 801/801 | Seis dimensiones por path; N/A queda separado de las relaciones comprobadas. |
| Verificaciones remotas | 0/5 | Se excluyen de toda afirmación de adopción o funcionamiento remoto. |

La revisión R2 recorrió los dominios y grupos mantenidos; R3 revisó el paquete y R5 releyó la corrección y los artefactos finales, todos con GO. Por ello, para el corte local, **fuentes completamente documentadas: 801/801**. El gate estructural por sí solo no certifica contenido; ninguna cifra acredita runtime ni adopción remota.

## Módulos y recorridos de transferencia

Los 14 componentes y sus 262 grupos están enlazados en el [registro verificable](../trazabilidad/registro_fuentes_componentes.md) y se agrupan por dominios en el [índice principal](../indice.md). La revisión cubre especialmente Admin/BFF, pipeline, utilidades, mantenimiento, canarios, seguridad, workflows y suites; las responsabilidades con diferencias locales tienen grupos y relaciones separados.

Los seis recorridos ejecutables para quien recibe el proyecto están en [recorridos de transferencia](../transferencia.md):

1. Regla de edición Admin: pantalla/símbolo → cliente Admin → BFF/RPC → datos/permisos → suite y transición.
2. Filtro público: URL/estado → consulta/renderer → vista/datos → tests y rebuild estático.
3. Campo de datos: diccionario → tipos/proyección/editor → migration/RLS/RPC si aplica → consumers y fixtures.
4. Discovery/procesamiento: perfil/gate → estación y estado → writer/datos → replay/requeue y harness aplicable.
5. Invitación, cuota o sesión: UI → cookie/Auth/BFF/Edge/DO/RPC → identidades y secretos por nombre → evidencia mock/local y cotejo remoto pendiente.
6. Workflow o herramienta de mantenimiento: trigger/permiso → script y clasificación read/write/delete → inputs/outputs → runner/scanner y permiso requerido.

## Checks del corte

Los comandos, entradas, códigos de salida, scope, warnings y límites están fijados en [evidencia Docker R12](h3req1_documentacion_checks_2026-10-13_r12.txt). La revisión independiente y la corrección de hallazgos se registran en [revisión R12](h3req1_documentacion_revision_independiente_2026-10-13_r12.txt). El scope explícito, hashes de payload y exclusiones están en el [manifiesto R12](h3req1_pr_scope_manifest_2026-10-13_r12_docs.json); el manifiesto no se hashea a sí mismo.

No se repiten suites funcionales cuyos inputs permanecen intactos. Los nueve warnings ESLint observados en `web/src/app/HomeContent.tsx` se informan separadamente del resultado documental; no se afirma que los haya introducido esta corrección ni se los oculta como PASS sin limitación.

## Backups, historia y preservación

El snapshot filtrado integral preescritura está en `/home/romel/backups/studiamatch-docs-2026-10-12/checkpoint_before_module_documentation_rewrite_2026-10-12/documentation_snapshot.tar` (1,127,424,000 bytes; SHA-256 `78b95d125300e3e4e6762f879969910479dbcb4dbc218fb9ea4c8e2779233366`). Su corte precede el lote de reescritura de fichas R10; no se presenta como una copia anterior a ediciones que ya existían antes de ese corte. Los overlays posteriores, los originales retirados y sus hashes están enumerados en [estructura R10](h3req1_documentacion_estructura_2026-10-13_r10.md) y [consolidación R11](h3req1_documentacion_consolidacion_trazabilidad_2026-10-13_r11.md), fuera de ambos checkouts. El snapshot suplementario previo a esta reconciliación está en `/home/romel/backups/studiamatch-docs-2026-10-13/supplemental_before_final_reconciliation_20261013T075643Z`; incluye 11 rutas y `FILES.sha256` (SHA-256 `3b96c60b8c4f915d56a52908d4c1695defddb694e93aac0b54504bc80b0496bb`). La verificación de contenido y comparación fuente/copia dio cero discrepancias. Antes de añadir la primera nota sobre allowlist, se preservó `.context/componentes/seguridad_tooling.md` en `/home/romel/backups/studiamatch-docs-2026-10-13/supplemental_before_security_allowlist_note_20261013T084450Z`: el archivo respaldado conserva SHA-256 `b7c6a6fe578d0fa59cde7d3a59465f1d137250a771667e06cb93ba47b8816b9e`, igual al origen en el momento de captura; `cmp --silent` confirmó igualdad entonces. Su `INVENTORY.txt` tiene SHA-256 `5f1cf4d32ba3d86dd2802107d4f38eaa094cdb900a4535408e178376c9ce6afb`; `FILES.sha256` tiene SHA-256 `45fb2f3aa5db3648e59d7d332ecb6458ba80f0ab5497e7a78c106d39f2586450`. Antes de distinguir el path activo del grupo retirado se preservaron la ficha y la prueba en `/home/romel/backups/studiamatch-docs-2026-10-13/supplemental_before_scope_guard_test_comment_20261013T090105Z`: dos archivos, ambos comparados byte por byte antes de editar; SHA-256 de `FILES.sha256` `bceab4940edbea6996e1fbf506f6920ecc04d7e85e1db2d4b657b00592c3e35e`, de `INVENTORY.txt` `73d84b84e190ead41943201f18f342e093a725d4c392f1e0928d3b50f667ffea`. La última captura previa a la reconciliación final fijó nueve rutas en `/home/romel/backups/studiamatch-docs-2026-10-13/supplemental_before_r12_final_truth_reconciliation_20261013T090541Z`; `INVENTORY.txt` SHA-256 `5eaecb4168615442333fd1aba80d2af20e5f4cfdeaaaf7e5716b1c6fd20b3c65`, `FILES.sha256` SHA-256 `b211ee5c00ddf52ef5c28cf47436e56a62b7b2738b31f8b40afad61c05cf55f3`. Copias y fuentes se cotejaron byte por byte (9/9 iguales). Un intento suplementario anterior en `supplemental_before_final_component_docs_20261013T074033Z` también se preserva pero no se usa como respaldo válido porque su manifiesto se auto-incluyó y el cotejo de fuentes falló. Todos los checkpoints quedan fuera del paquete y no se limpian.

R11 queda preservado como corte provisional con sus métricas originales; su copia anterior a la corrección está en el snapshot suplementario. Los archivos de checks/manifiesto que se habían planeado con nombre R11 no llegaron a generarse y no se presentan como evidencia. El log R9 del 2026-10-12 sí permanece en el candidato y coincide con el hash fijado por su manifiesto: `c88d6c18ee71c829df140e9f762fabcc766d630f97684ea6fb09b4ad43fb29a`. R178, R181/R182, manifests/body R8/R9 y sus resultados no se alteraron.

## Trabajo local y verificaciones remotas

R2/R3/R5 dieron GO; el P2 de R4 está corregido y revalidado. No quedan pendientes locales de transferencia. Las verificaciones locales no leen configuración operativa ni consultan servicios remotos.

Las cinco verificaciones remotas permanecen fuera de alcance: schema/ledger Pro; Edge/callers/correo; bindings/HMAC/gateway/Worker/DO; workflows/schedules/protecciones; y artifact/ref/cache/CDN/deploy. Cada una requiere la fuente y método descritos en el registro, además de una instrucción separada. SQL local, commits, YAML, hashes y pruebas locales no demuestran adopción remota.

## Traspaso

La propuesta R12 corresponde a la transferencia documental local; la integración funcional completa R8/R9/WIP aún debe reconciliarse en su etapa separada contra los paths y límites del manifiesto. No se abrió PR ni se ejecutaron merge, fetch/pull, deploy, configuraciones, writers, SQL operativo o pruebas remotas.

[Índice único](../indice.md) · [Estado operativo](../estado_del_proyecto.md) · [Consolidación y mapa origen→destino](h3req1_documentacion_consolidacion_trazabilidad_2026-10-13_r11.md) · [Corte R11 provisional](h3req1_documentacion_semantica_reanudacion_2026-10-13_r11.md)
