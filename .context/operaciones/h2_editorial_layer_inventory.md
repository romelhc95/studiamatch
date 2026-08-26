# H2 Editorial Layer Inventory

> Documento preparatorio. No autoriza DDL, DML, Supabase MCP, backfill, writers,
> schedules, deploys ni produccion. La autoridad viva esta en
> [`estado_del_proyecto.md`](../estado_del_proyecto.md).

## Rama

`feat/h2-editorial-model`

## Objetivo H2

Agregar una capa editorial separada sobre `courses` para que el pipeline siga
produciendo datos base, pero la publicacion, patrocinio, CTA visual, calidad,
faltantes, overrides y auditoria dependan de estado editorial controlado.

## Hallazgos De Schema Local

| Objeto | Fuente local | Hallazgo |
|---|---|---|
| `courses` | `db/restore_full_schema.sql` | Tabla producto/pipeline con `is_active`, `is_verified`, precio, modalidad, fechas, contenido, ROI y URL unica. |
| `leads` | `db/restore_full_schema.sql` y migraciones posteriores | Contiene PII y policies historicas de insert publico; H2 debe revocar captura publica antes de H4/H5. |
| `ratings` / `reviews` | `db/restore_full_schema.sql`, `20260413_social_proof.sql`, hardening posterior | Existe drift potencial entre frontend anonimo y RLS endurecida. No es cierre H2 salvo bloqueo de exposicion indebida. |
| `exec_sql` | `20260525_fase114_security_contract_hardening.sql` | Debe permanecer restringido a `service_role`; cualquier creacion, reemplazo o grant requiere JIT DDL separado. |

## Writers Identificados

| Writer | Superficie | Riesgo H2 | Tratamiento |
|---|---|---|---|
| `scripts/core/sync_vector_worker.py` | Upsert y patch a `courses` | Puede tratar `is_active/is_verified` como publicacion y sobreescribir campos base. | Mantener como productor pipeline; publicacion real debe depender de `course_editorial_state`. |
| `scripts/core/integrity_ping.py` | Patch a `courses` | Desactiva por expiracion/404 sin auditoria editorial. | Mantener como salud tecnica; no publicar ni reactivar editorialmente. |
| `scripts/maintenance/batch_enrich_courses.py` | Patch directo a `courses` | Bypass historico de pipeline/editorial. | Marcar como remediacion excepcional; no usar para cierre H2 sin control JIT. |
| `scripts/maintenance/preventive_cleanup.py` | Delete a `courses` | Destructivo e incompleto si hay mas de 1000 filas. | Convertir a reporte o mantener fuera de flujo H2. |
| `scripts/maintenance/lightweight_ping.py` | Patch directo REST a `courses` | Redundante y menos controlado que FG3. | Mantener fuera de flujo H2. |
| Frontend `/leads` | `web/src/app/HomeContent.tsx`, detalle de curso | Captura PII publica. | Retirar llamadas en PR funcional autorizado; DB debe revocar insert publico. |

## Diseno Propuesto

| Objeto | Proposito | Exposicion esperada |
|---|---|---|
| `public.editorial_field_definitions` | Diccionario allowlist y ownership por campo. | `SELECT` anon/auth solo para campos publicos si es necesario. Writes solo service/admin controlado. |
| `public.course_editorial_state` | Estado editorial/calidad, overrides publicos allowlisted, faltantes, fuentes, patrocinio, CTA visual y version. | `SELECT` anon/auth limitado por columnas y RLS equivalente a la vista; writes solo service/admin controlado. |
| `public.course_editorial_audit` | Auditoria append-only de cambios editoriales. | Sin acceso publico; sin `UPDATE`, `DELETE` ni `TRUNCATE`. |
| `public.courses_public_effective` | Vista publica efectiva con prioridad `override manual > valor pipeline`. | `SELECT` anon/auth; `security_invoker = true`; solo cursos `published` y `complete`. |

## Reglas SQL Requeridas

- Migracion forward-only.
- RLS habilitado en toda tabla nueva.
- Grants explicitos; no depender de auto-exposure de Data API.
- `REVOKE ALL` a `PUBLIC`, `anon` y `authenticated` donde no haya lectura publica intencional.
- Vista `courses_public_effective` con `security_invoker = true`.
- Cero `SECURITY DEFINER` nuevo en H2 salvo necesidad justificada, `search_path` fijado y `EXECUTE` revocado a `PUBLIC`.
- Autorizacion futura de admin via `auth.uid()` contra tabla server-side; nunca `user_metadata`.
- Audit append-only: sin grants de update/delete/truncate y con tests estaticos.

## Backfill Propuesto

El backfill debe ser DML JIT separado del DDL:

1. `--dry-run` por defecto.
2. `--apply` obligatorio para writes.
3. Paginacion keyset por `id.asc` o `select_all_service` con batch maximo 1000.
4. Estado inicial recomendado: `pending_review`, no `published` masivo.
5. `missing_fields` deterministico por campos minimos de publicacion.
6. `field_sources` inicial con fuente `pipeline_legacy` para campos presentes.
7. No tocar filas con `manual_updated_at` o overrides existentes salvo recomputos seguros.
8. Segunda corrida debe producir `NOOP` real.

## Stop Conditions

- Falta aprobacion JIT para escribir `db/migrations/**` o ejecutar DDL/DML remoto.
- Se intenta publicar masivamente cursos sin aceptacion humana.
- Se concede acceso publico no controlado o full-table a `course_editorial_state`, o cualquier acceso publico a `course_editorial_audit`.
- Se deja `leads` con insert publico despues de retirar captura frontend.
- Se mezcla H2 DB con H4/H5 frontend fuera del alcance autorizado.
