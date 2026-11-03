# Transferencia documental semántica — punto de reanudación

> Corte de trabajo: 2026-10-12, America/Lima. Continuación del inventario R9; no reinicia ni sustituye la historia anterior. Este archivo es una lista de trabajo documental, no autoridad operativa.

## Estado inicial de esta continuación

- Checkout candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama `feat/h3req1-sync-20261002`, HEAD baseline `4eb4d877a50b012bb630a129bd0c74482c33be9c`. El inventario incluye el WIP no identificado por HEAD.
- Checkout original: `/home/romel/src/studiamatch`, solo lectura, rama `feat/h3req1-development-remote-tests`, HEAD `7650093b05a820e8e6faf9ec711e12fab8b50398`.
- El corte R9 anterior registró 808 fuentes, 12 componentes, 44 grupos y 4.848 slots de relación. Distribución al iniciar esta continuación: 2.093 `verified`, 1.236 `pending`, 1.517 `unknown`, 2 `not_applicable`; 0/808 fuentes con todas las dimensiones verificadas. La asignación estructural previa era 808/808; no equivale a cobertura semántica.
- Evidencia local nueva en esta continuación: `h3req1_historia_paths_local_2026-10-12.md` (historia por path en ambos checkouts) y `h3req1_relaciones_semanticas_locales_2026-10-12.md` (imports/callers de frontend, BFF, ROI, workflows, canarios y referencias de tests). Son búsquedas estáticas, no ejecución de runtime.
- Hallazgo corregible: `taxonomy_roi_audit.py` sí importa el ROI compartido. El registro/ficha anterior que lo excluía del conjunto de consumidores está desactualizado.
- El checker en esta continuación rechaza `unknown` como estado de dimensión y distingue `remote_only`; el registro aún debe migrarse a estos estados y el gate no debe tratarse como PASS hasta validarlo con el registro actualizado.

## Preservación previa a más reescrituras

Checkpoint fuera de ambos checkouts: `/home/romel/backups/studiamatch-docs-2026-10-12/checkpoint_before_module_documentation_rewrite_2026-10-12`.

- Archivo integral base: `documentation_snapshot.tar`, SHA-256 `78b95d125300e3e4e6762f879969910479dbcb4dbc218fb9ea4c8e2779233366`; coincide por path, modo, bytes y SHA-256 con el checkpoint filtrado completo existente.
- Superposición que preserva el estado exacto antes de nuevas fichas: checker `scripts/maintenance/h3req1_documentation_integrity.mjs` y los dos informes de evidencia de esta continuación.
- SHA-256 del manifiesto de superposición: `1c03a5b76a2088ef1c668dcd6b031ab3dca87c496aeafec71ae61dee88619ffa`. `SHA256SUMS.overlay` se verificó con `sha256sum -c`; cada copia pasó `cmp` contra su fuente.
- El archivo base conserva la política de exclusión documentada (caches, dependencias empaquetadas y secretos privados); no se ha eliminado ni modificado ningún checkpoint histórico. El backup no pertenece al paquete propuesto.

## Tareas del ciclo y gates

| ID | Tarea | Gate de cierre | Estado |
|---|---|---|---|
| DOC-SEM-01 | Alinear esquema del registro, estados por dimensión, evidencia de búsqueda y checks remotos únicos. | Sin `unknown` heredado; cada `pending` tiene pregunta/resolución local concreta; cada `remote_only` refiere una lectura futura con método/owner. Self-test negativo para fuente no asignada y relación genérica. | En curso |
| DOC-SEM-02 | Completar frontend público, Admin, sesión/MFA, edición/publicación, BFF, invitación, cuota y gateway. | Recorridos por ruta→símbolo→contrato→consumidor/datos→casos/evidencia→operación/modificación; imports/callsites acreditados. | Pendiente |
| DOC-SEM-03 | Completar diccionario y ledger por objeto/migration; conectar RPC, RLS, grants y harnesses. | Cada migration local relaciona objetos declarados, callers/harnesses hallados, baseline/rollback y límite remoto; SQL no se ejecuta. | Pendiente |
| DOC-SEM-04 | Describir FG1/FG2/FG3, utilidades compartidas, ROI, canarios y mantenimiento por capacidad/callgraph. | Fuentes con responsabilidades distintas separadas; operaciones read/write/delete/DDL/cross-env, efectos y permisos basados en código. | Pendiente |
| DOC-SEM-05 | Cubrir workflows, seguridad, config, suites/runners/fixtures, legacy y tooling. | Cada fuente con dependencia/caller, datos o N/A argumentado, suite/evidencia o ausencia buscada, historial local y estado remoto separado. | Pendiente |
| DOC-SEM-06 | Verificar recorridos de transferencia de seis cambios representativos y hacer la navegación bidireccional. | Desde índice se llega a módulo, sección, path/símbolo y desde fuente/registro se vuelve a documento; pruebas/permisos indicados para cada recorrido. | Pendiente |
| DOC-SEM-07 | Validar checker en Docker, scope/credenciales, referencias y contenido; obtener revisión independiente; convertir hallazgos en tareas y revalidar. | Gate estructural + negativos PASS; revisión sin bloqueantes; manifests/body reconciliados por impacto; gates funcionales intactos no se repiten. | Pendiente |
| DOC-SEM-08 | Preparar la copia final filtrada y paquete concreto para etapa separada G10/Development. | Inventario/hash verificado, PR draft y manifest actualizados sin alterar R8; ninguna ejecución remota. | Pendiente |

## Verificaciones exclusivamente remotas

No se ejecutan en este ciclo. Registrar cada pregunta en `remote_checks` y conservar estos resultados fuera del denominador de relaciones locales:

- Cotejar el schema aplicado de Pro con el baseline, vistas/funciones, políticas, grants, índices y migration ledger; Pro no se consulta en esta etapa.
- Leer estado/versión de Supabase Edge `admin-invite`, trigger/caller externo de `send-lead-emails`, y bindings/keys por nombre en los ambientes autorizados.
- Verificar Worker/DO, bindings Pages, pre-request/gateway y sus despliegues reales.
- Leer instalación y ejecución reciente de workflows/schedules, required checks, permisos, branch protection, Pages deployment/ref y cache/CDN.

Un YAML, migration, binding declarado o commit no acredita ejecución/adopción remota.

## Regla de reanudación

Retomar desde la primera tarea no cerrada de la tabla. Reutilizar la evidencia enlazada y no repetir búsquedas ya delimitadas. Si una afirmación no se acredita con código, configuración, caso de prueba/evidencia fechada o búsqueda de ausencia con alcance explícito, mantenerla `pending` local o `remote_only` según corresponda. No cambiar el denominador para cerrar el ciclo.
