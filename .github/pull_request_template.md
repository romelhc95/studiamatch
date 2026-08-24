## Governance Attestation

Completar solo para PR R1/R2 normales hacia `desarrollo`. En PR O2-O5, remover esta seccion o dejar todos sus campos vacios; cualquier valor en la seccion inactiva bloquea el PR.

Base-SHA:
Candidate-SHA:
Estado-Snapshot:
Requerimiento:
Hito:
TASK:
WP:
WP-Digest:
Approval-Level:
Approval-Expiry:
Architecture-Snapshot:
Data-Architecture-Snapshot:
Adoption-Matrix-Snapshot:
Architecture-Impact:
Architecture-Impact-Reason:
Data-Impact:
Data-Impact-Reason:
Security-Auditor:

## Promotion Attestation

Completar solo para promociones O2-O5 con ramas runtime `promote/gov-hom-011-oN`. En PR R1/R2 normales, remover esta seccion o dejar todos sus campos vacios; cualquier valor en la seccion inactiva bloquea el PR.

Operation:
Grant-ID:
Base-Ref:
Base-SHA:
Source-Ref:
Source-SHA:
Candidate-SHA:
Candidate-Tree:
Final-WP:
D_FINAL:
T_FINAL:
Approval-Level:
Approval-Reference:
Approval-Expiry:

## Checklist - Obligatorio antes de mergear

### Context Graph Y Autorizacion
- [ ] Lei `AGENTS.md`, `.context/00_INDICE.md` y `.context/estado_del_proyecto.md` antes de implementar.
- [ ] El PR enlaza requerimiento, hito, TASK y WP aplicable.
- [ ] La autorizacion coincide con `AGENTS.md` y usa WP/digest vigente.
- [ ] La attestation tecnica incluye Base-SHA, Candidate-SHA, WP-Digest y manifest vigente; `security-audit` valida digest, head real, paths y co-change.
- [ ] La review humana obligatoria queda a cargo de GitHub branch protection; no necesita repetir el digest en el texto de review.
- [ ] `active_work_package` esta coherente entre Estado, Plan Maestro, Tracker y manifest.
- [ ] Si hay R3, existe aprobacion JIT single-use separada y vigente.
- [ ] Si es promocion O2-O5, usa rama target-aware `promote/gov-hom-011-oN`, el PR no es #428/#431/#433/#435/#437/#440/#441/#443, fue abierto una sola vez, usa `R3_JIT_APPROVAL_ENVELOPE` schema `promotion-jit-envelope-v1` y no usa un Grant-ID consumido o superseded.
- [ ] Si el PR apunta a `desarrollo`, `certificacion` o `main`, `romelhc95-approver` revisa/aprueba y `romelhc95` ejecuta el merge; el reviewer no actualiza ramas protegidas.
- [ ] No se ejecutan H2 funcional, DDL/DML, schedules, writers, deploys ni secrets sin gate separado.

### Arquitectura Y Datos
- [ ] Lei `.context/arquitectura_pipeline.md` si el cambio toca web, pipeline, workflows, runtime, infraestructura o deploy.
- [ ] Lei `.context/sistema_db_supabase.md` si el cambio toca DB, Supabase, tablas, RLS, RPC, grants, lectores o escritores.
- [ ] Lei `.context/operaciones/matriz_adopcion_db.md` si el cambio toca schema, migraciones, ambientes, promocion o drift.
- [ ] Actualice los documentos canonicos requeridos o justifique `Architecture-Impact=none` / `Data-Impact=none`.

### Seguridad (@security-auditor)
- [ ] Ejecute `@security-auditor` sobre los cambios y no hay hallazgos CRITICOS/ALTOS.
- [ ] No hay credenciales hardcodeadas.
- [ ] No se exponen secretos en logs, mensajes de error, URLs ni documentacion.

### Git
- [ ] La rama de origen es `feat/*`, `fix/*`, `docs/*`, `governance/*` o `chore/*` autorizado por WP.
- [ ] La rama nace del HEAD vigente de `desarrollo` o fue actualizada antes del merge.
- [ ] El diff respeta allowlist/denylist del WP y no versiona fuentes privadas.
- [ ] El PR no mezcla cambios de fases o paquetes distintos.

### Evidencia
- [ ] Se registraron commit/tree, CI, ambiente, ultimo gate y proximo gate unico.
- [ ] Si actualiza tracker o evidencia, incluye metricas obligatorias o `UNKNOWN` justificado.
