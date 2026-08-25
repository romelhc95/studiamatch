## Checklist - Obligatorio antes de mergear

### Alcance
- [ ] El PR enlaza requerimiento o issue aplicable.
- [ ] La rama nace de `desarrollo` salvo promocion `desarrollo -> certificacion -> main`.
- [ ] El diff no mezcla pedidos independientes.
- [ ] Cambios DB, produccion, schedules, writers, deploys, secrets o acciones destructivas tienen aprobacion separada.

### Seguridad
- [ ] Ejecute `@security-auditor` sobre los cambios y no hay hallazgos criticos/altos.
- [ ] No hay credenciales hardcodeadas ni secretos en logs, errores o URLs.
- [ ] `security-audit` esta verde.

### Código
- [ ] `npm run lint` pasa sin errores cuando hay cambios frontend.
- [ ] `npx tsc --noEmit` pasa sin errores cuando hay cambios frontend.
- [ ] Los scripts Python modificados compilan correctamente.

### Git
- [ ] El historial no contiene commits con credenciales expuestas.
- [ ] No se versionan fuentes privadas, `.env*`, artifacts ni salidas generadas.
- [ ] Si toca rutas protegidas, la justificacion y aprobacion estan en el PR.
