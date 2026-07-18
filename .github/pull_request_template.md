## Alcance
- Hito / tarea:
- Resumen:

## Hito Close Gate
- [ ] Reporte candidato generado con `validate_hito_close.py --hito X --generate-report`, staged y enlazado.
- [ ] Verificacion final `validate_hito_close.py --hito X` ejecutada con `GO`.
- [ ] `git diff --check` OK.
- [ ] TAREA, changelog, informe y artefactos versionados no se contradicen.
- [ ] Matriz `CA -> prueba -> evidencia` ejecutada o no aplicable justificada.
- [ ] Supabase/RLS validado si aplica.

## Seguridad Y Git
- [ ] `security-auditor` ejecutado antes de solicitar review, sin hallazgos medios/altos/criticos sin resolver.
- [ ] No hay credenciales hardcodeadas ni secretos expuestos en codigo, logs, errores, URLs o historial.
- [ ] La rama de origen es `feat/*` o una rama documental aprobada; no se trabajo directamente sobre `desarrollo`.

## Validaciones
- [ ] Python: `python3 -m py_compile <archivos>` ejecutado, o N/A justificado en Riesgos / Pendientes.
- [ ] Frontend: `npm run lint` y `npx tsc --noEmit` ejecutados, o N/A justificado en Riesgos / Pendientes.
- [ ] SQL/RLS queries si aplica.
- [ ] Evidencia cliente actualizada en `.context/evidencias/`.

## Riesgos / Pendientes
-
