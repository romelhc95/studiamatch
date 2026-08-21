## Checklist - Obligatorio antes de mergear

### Context Graph Y Autorizacion
- [ ] El PR enlaza requerimiento, hito, TASK y WP aplicable
- [ ] La autorizacion coincide con `AGENTS.md`: fase decimal activa o WP/digest vigente
- [ ] `active_work_package` esta coherente entre Estado, Plan Maestro, Tracker y manifest
- [ ] Si hay R3, existe aprobacion JIT single-use separada y vigente
- [ ] No se ejecutan O3, H2, DDL/DML, schedules, writers, deploys ni secrets sin gate separado

### Seguridad (@security-auditor)
- [ ] Ejecuté `@security-auditor` sobre los cambios y no hay hallazgos CRÍTICOS/ALTOS
- [ ] No hay credenciales hardcodeadas (JWT, API keys, Supabase refs, tokens)
- [ ] No se exponen secretos en logs, mensajes de error, ni URLs

### Código
- [ ] `npm run lint` pasa sin errores
- [ ] `npx tsc --noEmit` pasa sin errores
- [ ] Los scripts Python compilan correctamente: `python3 -m py_compile scripts/core/*.py`

### Git
- [ ] La rama de origen es `feat/*` o `docs/*` explicitamente autorizada por Plan Maestro/WP (no se trabaja directo sobre `desarrollo`)
- [ ] El historial no contiene commits con credenciales expuestas
- [ ] El diff respeta allowlist/denylist del WP y no versiona fuentes privadas
- [ ] El PR no mezcla cambios de fases o paquetes distintos

### Evidencia
- [ ] Se registraron commit/tree, CI, ambiente, ultimo gate y proximo gate unico
- [ ] Si actualiza tracker o evidencia, incluye metricas obligatorias o `UNKNOWN` justificado
