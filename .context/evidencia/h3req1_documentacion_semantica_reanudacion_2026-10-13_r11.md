# Reconciliación y reanudación de transferencia documental R11 — 2026-10-13

> Evidencia del corte y punto de continuidad, no autoridad operativa ni permiso para ejecución protegida. La autoridad del estado vigente sigue en [estado del proyecto](../estado_del_proyecto.md); asignaciones en el [registro JSON canónico](../trazabilidad/registro_fuentes_componentes.json), navegación en el [índice único](../indice.md), mantenimiento en el [protocolo constructor](../trazabilidad/protocolo_constructor.md). R10 permanece como snapshot histórico.

> **Clasificación posterior:** R11 fue un corte provisional. La revisión independiente encontró la vista renderizada desfasada y conteos antiguos; además, el gate confirmó que los archivos citados como log/manifiesto R11 no existían. Se preserva este contenido como historia con sus cifras originales, pero no describe el estado actual. El cierre y la evidencia ejecutada del corte corregido están en [R12](h3req1_documentacion_cierre_local_2026-10-13_r12.md).

## Corte identificado

- Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama `feat/h3req1-sync-20261002`, HEAD baseline `4eb4d877a50b012bb630a129bd0c74482c33be9c`. HEAD no identifica todo el WIP.
- Original: `/home/romel/src/studiamatch`, rama `feat/h3req1-development-remote-tests`, HEAD `7650093b05a820e8e6faf9ec711e12fab8b50398`, solo lectura.
- WIP candidato: se mantienen paths funcionales, evidencia y cambios ajenos inventariados; el paquete documental selecciona paths explícitos y no arrastra todo lo untracked.
- Backup completo y overlays verificados fuera de ambos checkouts. No se limpia ninguno; detalle, hashes e inventario en [consolidación R11](h3req1_documentacion_consolidacion_trazabilidad_2026-10-13_r11.md).

## Cobertura con denominadores del gate — corte provisional R11, supersedido

Corte Docker R11 posterior a los cambios documentales actuales:

| Medida | Resultado | Denominador/criterio |
|---|---:|---|
| Asignación estructural | 801/801 (100%) | Paths fuente relevantes descubiertos; cada uno apunta a componente, documento y anchor. |
| Documentos de componente | 12/12 (100%) | Componentes del registro con ficha activa enlazada. |
| Navegación | 77/77 (100%) | Documentos activos alcanzables desde el índice Obsidian único. |
| Relaciones locales | 4,715/4,715 verificadas (100%) | Slots aplicables de las seis dimensiones, ponderados por paths de grupo. |
| Relaciones justificadas N/A | 91/91 (100%) | Slots `not_applicable` con motivo específico; separados de verificaciones locales. |
| Pendientes locales/unknown/invalid | 0/4,806 (0%) | Todos los slots locales; ningún `pending`, `unknown` o inválido en este corte. |
| Grupos semánticos | 256 | Unidad usada cuando sus archivos comparten responsabilidad; el registro conserva la asignación exacta por path. |
| Verificaciones remotas | 0/5 ejecutadas | Fuera del denominador local y sin afirmación de adopción. |

El checker registra `all_relation_dimensions_verified_sources=801/801`, pero esa es una métrica de estados del registro heredados por grupos; no se presenta por sí sola como certificado de calidad narrativa. La medida “fuentes completamente documentadas” queda determinada por la revisión independiente del contenido: cada grupo debe tener una sección útil que explique comportamiento, contratos, consumidores, datos, pruebas/evidencia, permisos/operación, fallos y cómo cambiarlo según aplique. No se reduce el denominador para lograr el 100%.

El denominador estructural pasó de 808 fuentes / 4,848 slots en el primer corte R9 a 801 / 4,806 después de retirar siete documentos de navegación redundantes, que representaban 42 slots. No se eliminaron fuentes de producto. Su contenido y hashes se conservan en los backups externos y sus reemplazos constan en la [matriz origen→destino](h3req1_documentacion_consolidacion_trazabilidad_2026-10-13_r11.md). Los conteos 2,093 verified / 1,236 pending / 1,517 unknown de R9, y 2,928 / 1,787 del corte pre-R11, son históricos y no describen este estado.

## Tareas efectivamente en curso

| ID | Estado | Trabajo restante | Gate de cierre |
|---|---|---|---|
| R11-REVIEW | En curso | Terminar revisión independiente de las fichas, sus grupos, fuentes y recorridos; convertir hallazgos en cambios y corregirlos. | Sin bloqueantes de contenido, afirmaciones, navegación o preservación; revalidación posterior a correcciones. |
| R11-PACKAGE | En curso | Generar manifiesto no circular del delta documental y cuerpo propuesto con la plantilla versionada; separar claramente documentación de WIP funcional. | Scope explícito/hash por path, excludes justificados, R8/R9 inalterados y digest/checks actualizados. |
| R11-FINAL-CHECK | Pendiente hasta cerrar la revisión | Renovar gate normal/self-test, scanner, scope guard, enlaces/anchors y recorridos sobre el paquete reconciliado. | Todos los checks pertinentes ejecutados en Docker; límites de herramientas ausentes consignados. |

No quedan tareas locales de relación `pending`: el último gate registra 0. No se repiten suites funcionales cuyo input no cambió. Si la revisión encuentra una afirmación sin sustento, una responsabilidad mal agrupada o una instrucción de mantenimiento incompleta, se investiga y corrige localmente antes del cierre.

## Recorridos de transferencia a revisar

El [recorrido de transferencia](../transferencia.md) conduce desde índice→dominio→ficha→símbolo/contrato→consumidores/datos→prueba/operación para:

1. Modificar una regla de edición Admin.
2. Añadir un filtro público.
3. Cambiar un campo de datos.
4. Cambiar discovery/procesamiento del pipeline.
5. Entender una invitación, cuota o sesión.
6. Modificar un workflow o herramienta de mantenimiento.

La revisión comprueba que en cada camino se localizan la fuente y símbolo, el contrato, consumidores, datos, evidencia/ausencia, permiso requerido y validaciones a renovar.

## Gates locales ya ejecutados

En Docker `studiamatch-dev`:

- Checker documental `--render`: **PASS**; 801/801 asignaciones, 12/12 componentes, 77/77 documentos activos accesibles, 256 grupos, 5,311 links y 3,326 anchors.
- Checker `--self-test`: **PASS**; prueba rechazo de fuente nueva sin relación, estado genérico `unknown`, paths/anchors inválidos, comentario discrepante, raíz/extensión sin regla, índice principal duplicado y documento retirado aún activo.
- Gate normal: **PASS**, `DOC_GATE_PASS`; 4,715 relaciones locales verified, 91 N/A, 0 pending/unknown/invalid; 5 checks remotos pendientes.
- Credential scanner: **PASS**, scope explícito de 878 paths registrados/documentales/raíces, salida sin valores sensibles.
- `tests/test_protected_path_scope_guard.sh`: **PASS**, regresiones `ordinary=3|newline=1|controls=1|malformed=3`.
- `git diff --check`: **PASS**.
- Runner global de scope/workflow: limitación del contenedor: `/app` no incluye `.git`, requerido por el comparador completo; la regresión del parser/guard sí pasó. No se consultó ni configuró GitHub.
- `pytest`: no instalado en el contenedor (`No module named pytest`); no se instaló. No hubo cambio funcional que justificara repetir suites de producto.

Los archivos de checks y manifiesto previstos para R11 nunca se generaron; no se atribuye ese resultado a artefactos inexistentes. Los resultados ejecutados, inputs y scope del cierre están en [checks R12](h3req1_documentacion_checks_2026-10-13_r12.txt) y en el [manifiesto propuesto R12](h3req1_pr_scope_manifest_2026-10-13_r12_docs.json).

## Verificación remota separada

Siguen 0/5 realizadas; el método futuro requiere autorización independiente y queda fuera de esta transferencia:

1. Schema/migration ledger de Pro y baseline efectivo: comparar el catálogo remoto con migraciones/tipos/constraints locales en lectura autorizada; no aplicar SQL.
2. Edge/callers/correo de invitación: cotejar deployment, logs/configuración autorizada y proveedor; no enviar correo.
3. Bindings, HMAC, gateway firmado y Worker/DO de Admin: inspección de configuración por ambiente y smoke autorizado; nunca registrar secretos.
4. Workflows instalados, schedules, branch protection y checks requeridos: lectura de GitHub después de la autorización correspondiente.
5. Ref, artefacto, cache/CDN y deploy/Pages por ambiente: evidencia de plataforma y smoke remoto autorizados.

Código, SQL, YAML, commit, hash y pruebas locales no acreditan adopción remota. Pro sigue como baseline autoritativo según las reglas existentes; no se consultó ni modificó Supabase.

## Punto de reanudación y preservación

1. Recibir la revisión independiente R11 y anotar cada hallazgo como tarea concreta con source path, evidencia y dueño de corrección local.
2. Corregir y validar primero el contenido. Actualizar registro/checker solo cuando la responsabilidad o la evidencia realmente cambie.
3. Regenerar scope/hashes del paquete documental, rellenar el cuerpo propuesto usando `.github/pull_request_template.md` y validar el paquete en Docker.
4. Si no quedan hallazgos locales, declarar el cierre documental del corte local; las cinco verificaciones remotas siguen pendientes y la etapa G10/Development espera instrucciones separadas.

R178, R181 y R182, sus resultados sellados y los manifiestos/cuerpos R8/R9 se preservan con contenido y alcance originales. No se hizo commit, push, PR, merge, fetch/pull, cambio de rama, SQL operativo, deploy, configuración remota, secrets ni limpieza global.

[Índice único](../indice.md) · [Estado operativo](../estado_del_proyecto.md) · [Consolidación R11](h3req1_documentacion_consolidacion_trazabilidad_2026-10-13_r11.md) · [Registro de asignaciones](../trazabilidad/registro_fuentes_componentes.md)
