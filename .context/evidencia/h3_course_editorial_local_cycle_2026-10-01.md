# Evidencia del ciclo local — edición editorial, disponibilidad y auditoría

**Fecha:** 2026-10-01
**Estado:** `NO-GO_LOCAL_ACCEPTANCE_GAPS_PENDING`
**Atestación de alcance:** [Aceptación sanitizada del plan](../evidencias_cliente/sprint_1/atestado_aceptacion_plan_ingesta_editorial_auditoria_2026-10-01.md)
**Plan:** [Remediación de ingreso, corrección y auditoría](../operaciones/plan_remediacion_ingesta_editorial_auditoria_2026-10-01.md)

## Alcance ejecutado

Se implementó y validó únicamente en el checkout local, Docker y un PostgreSQL 17
efímero:

- `admin_update_course` persiste solo campos enviados, valida el rol activo,
  tipos y versión; `null` retira un override y recupera el valor base del pipeline.
- La respuesta del editor separa valores del pipeline y efectivos, indica
  faltantes/diferencias manuales y conserva origen/timestamp.
- La disponibilidad manual queda en campos separados del cálculo del pipeline,
  con evidencia HTTPS del dominio fuente, fecha observada, caducidad, motivo y
  auditoría. La caducidad vuelve al valor calculado.
- El historial se consulta mediante RPC Admin/MFA paginado; no se otorgó SELECT
  directo autenticado sobre `course_editorial_audit` ni se expuso en vistas
  públicas. La auditoría sigue append-only.
- La publicación valida disponibilidad efectiva, calidad, curso activo/verificado,
  perfil de institución y exclusiones canary. El lector conserva la cohorte legacy;
  un override manual no sustituye valores públicos antes del gate estricto, y una
  determinación `unavailable` vigente sí retira el curso legacy de la vista.
- El editor muestra evidencia, motivo y valores anteriores/nuevos; expone
  restauración al pipeline e historial Admin.

No se cambió el worker, no se hizo backfill ni se escribió en Supabase remoto.

## Validaciones ejecutadas

| Gate | Resultado | Alcance/evidencia |
|---|---|---|
| PG17 | **PASS** | `tests/sql/h3_pg17_harness.sql` termina en `h3_pg17_harness_ok`; incluye re-aplicación idempotente, RBAC, audit paging, disponibilidad vencida/no disponible, control canary y compatibilidad legacy. |
| Tests Python seleccionados | **122 PASS** | Contratos H3, seguridad/credenciales, estado Obsidian y migraciones H2/Pro relevantes. |
| TypeScript | **PASS** | `npx tsc --noEmit` dentro de `studiamatch-dev`. |
| ESLint | **PASS, 0 errores** | Quedan 9 warnings existentes en `web/src/app/HomeContent.tsx`; ninguno corresponde al editor modificado. |
| Static build smoke | **PASS** | `h2_web_mock_smoke_ok`; build y ruta estática de fixture legacy generada. No se usaron credenciales ni endpoints Supabase. |
| Credential scan | **PASS** | `scripts/security/scan_credentials.sh --tree`. |
| Diff whitespace | **PASS** | `git diff --check`. |

## Transición, rollback y límites

- **Expand:** la migración local añade RPC/campos/lectura; no elimina columnas,
  auditorías, funciones legacy ni cohortes.
- **Compatibilidad:** PG17 demuestra preservación de la cohorte con disponibilidad
  `unknown`; solo una evidencia `unavailable` vigente la oculta. Overrides públicos
  siguen condicionados al contrato estricto.
- **Deploy:** no ejecutado. No se solicitó ni consumió JIT para DDL/DML Free,
  Preview, writers, push, PR o promoción.
- **Contract:** no ejecutado; la cohorte legacy permanece intacta.
- **Rollback:** no aplicado. La reversión remota tendría que ser una migración
  compensatoria revisada que restaure las definiciones H3/H2 previas, conserve los
  nuevos datos de auditoría y no borre columnas. Su ejecución requeriría JIT y
  validación independiente.

## NO-GO restante

El resultado es **validación técnica local**, no GO de la UAT completa. Sigue
pendiente una prueba visual/autenticada del panel Admin con MFA y una ruta estática
con datos del curso nuevo elegible; el smoke local solo generó la ruta fixture
legacy. No se acordó un TTL por institución ni un clasificador automático de
inconsistencias: la UI muestra faltantes y diferencias manuales, pero no etiqueta
semánticamente el dato base como incorrecto. Tampoco se comprobó el comportamiento
en Free/Preview ni se midió carga de producción. No declarar cierre, promoción ni
compatibilidad remota estable hasta obtener esa evidencia y las aprobaciones
correspondientes. La UAT global H3 y el estado remoto continúan `NO-GO`.
