---
id: TAREA-H1R-005
fase: Post-Hito 1
estado: pendiente
prioridad: media
estimacion_ref: est_001
requerimiento: req_hito_1_rework_20260721
hito: Post-Hito 1
paquete: Promocion a certificacion
cas: "Gate SDLC"
responsable: IA implementadora
revisor: devops-release-manager, security-auditor
aprobador: Usuario/PM
skill_principal: devops-release-manager
skills_apoyo: "qa-test-engineer, security-auditor"
gate_obligatorio: security-auditor
entregable: "PR nuevo desarrollo -> certificacion"
creado: 2026-07-21
tags: [hito-1, certificacion, promocion]
---

# TAREA-H1R-005: Regenerar Promocion A Certificacion

## Contexto
- Evaluacion origen: [[../../operaciones/evaluacion_prs_cancelados_hito1_20260721]]
- Referencia historica: PR #207 cerrado.

## Alcance Funcional
- Crear promocion nueva solo despues de que el nuevo Hito 1 este mergeado en `desarrollo`.
- Regenerar manifests/evidencias desde el commit final de `desarrollo`.
- No reutilizar `promote/pre-hito1-to-certification` ni sus checks anteriores.

## Criterios De Aceptacion
- [ ] Existe commit final de Hito 1 en `desarrollo`.
- [ ] Manifests/evidencias usan checksums actualizados.
- [ ] PR nuevo apunta a `certificacion` y pasa `security-audit`.
- [ ] No se promueve a `main` ni Supabase Pro sin aprobacion explicita.

## Archivos Candidatos
| Archivo | Tipo de cambio |
|---|---|
| `.context/evidencias/releases/...` | Nueva evidencia |
| `.github/workflows/...` | Solo si la promocion requiere ajustes |

## Resultado
Pendiente.
