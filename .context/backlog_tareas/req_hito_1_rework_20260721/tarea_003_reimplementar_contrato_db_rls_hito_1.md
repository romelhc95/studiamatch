---
id: TAREA-H1R-003
fase: Hito 1 Rework
estado: pendiente
prioridad: alta
estimacion_ref: est_001
requerimiento: req_hito_1_rework_20260721
hito: Hito 1 Rework
paquete: DB/RLS/contrato editorial
cas: "CA1, CA7 preparacion"
responsable: IA implementadora
revisor: supabase-architect, security-auditor
aprobador: Usuario/PM
skill_principal: supabase-architect
skills_apoyo: "qa-test-engineer, data-quality-analyst"
gate_obligatorio: security-auditor
entregable: "Migration versionada Free + PR a desarrollo"
creado: 2026-07-21
tags: [hito-1, rework, supabase, rls]
---

# TAREA-H1R-003: Reimplementar Contrato DB/RLS De Hito 1

## Contexto
- Evaluacion origen: [[../../operaciones/evaluacion_prs_cancelados_hito1_20260721]]
- Referencia historica: PR #203 cerrado.

## Alcance Funcional
- Revalidar contrato editorial/calidad/patrocinio propuesto en #203 contra schema actual.
- Crear migration nueva desde `origin/desarrollo`, no reutilizar migration antigua sin revisar drift.
- Garantizar que anon/authenticated no puedan forzar campos patrocinados o estados editoriales no autorizados.
- Mantener compatibilidad con RLS vigente y `db_client.py`.

## Criterios De Aceptacion
- [ ] Migration es idempotente o tiene precondiciones claras.
- [ ] RLS conserva lectura publica solo de datos permitidos.
- [ ] Escrituras privilegiadas quedan restringidas a backend/CI autorizado.
- [ ] Advisors/security review no reportan hallazgos bloqueantes.
- [ ] No se modifica Supabase Pro desde esta tarea.

## Archivos Candidatos
| Archivo | Tipo de cambio |
|---|---|
| `db/migrations/<fecha>_hito1_*.sql` | Nueva migration |
| `.context/sistema_db_supabase.md` | Documentacion si cambia schema |
| `tests/...` | Tests de contrato si aplica |

## Resultado
Pendiente.
