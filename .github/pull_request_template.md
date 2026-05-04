## Checklist — Obligatorio antes de mergear

### Seguridad (@security-auditor)
- [ ] Ejecuté `@security-auditor` sobre los cambios y no hay hallazgos CRÍTICOS/ALTOS
- [ ] No hay credenciales hardcodeadas (JWT, API keys, Supabase refs, tokens)
- [ ] No se exponen secretos en logs, mensajes de error, ni URLs

### Código
- [ ] `npm run lint` pasa sin errores
- [ ] `npx tsc --noEmit` pasa sin errores
- [ ] Los scripts Python compilan correctamente: `python3 -m py_compile scripts/core/*.py`

### Git
- [ ] La rama de origen es `feat/*` (no se trabaja directo sobre `desarrollo`)
- [ ] El historial no contiene commits con credenciales expuestas
