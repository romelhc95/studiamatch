## Resumen

- Cambio principal:
- Hito/requerimiento:
- Veredicto tecnico:
- Evidencia canonica:

## Avances Del Cambio

| Area | Avance | Evidencia |
|---|---|---|
| Producto |  |  |
| Base de datos |  |  |
| Pipeline/scripts |  |  |
| Frontend |  |  |
| Seguridad |  |  |
| Documentacion |  |  |

## Pilares Obligatorios

| Pilar | Estado | Resultado validado |
|---|---|---|
| Escalabilidad | `PENDIENTE/APROBADO` |  |
| Seguridad | `PENDIENTE/APROBADO` |  |
| Mantenimiento | `PENDIENTE/APROBADO` |  |
| Calidad | `PENDIENTE/APROBADO` |  |
| Rendimiento | `PENDIENTE/APROBADO` |  |

## Evidencia Para Cliente

- Acta ejecutiva:
- Matriz de trazabilidad:
- Metricas verificables:
- Grado de evidencia:
- Traduccion cliente incluida: `SI/NO`

## Validaciones

| Validacion | Resultado |
|---|---|
| Credential scan |  |
| Python tests |  |
| Python compile |  |
| PostgreSQL DB Change Gate |  |
| ESLint |  |
| TypeScript |  |
| Static build |  |
| security-audit |  |
| CodeQL |  |
| Cloudflare Pages |  |

## Seguridad Y Datos

- [ ] No hay credenciales hardcodeadas ni secretos en logs, errores, URLs, comentarios o evidencia publica del PR.
- [ ] Los identificadores operativos sensibles o innecesarios se mantienen solo en evidencia interna cuando aplique.
- [ ] `security-audit` esta verde.
- [ ] Ejecute `@security-auditor` sobre los cambios y no hay hallazgos criticos/altos.
- [ ] Cambios DB, produccion, schedules, writers, deploys, secrets o acciones destructivas tienen aprobacion separada.

## Alcance Y Limites

- [ ] El PR enlaza requerimiento o issue aplicable.
- [ ] La rama nace de `desarrollo` salvo promocion `desarrollo -> certificacion -> main`.
- [ ] El diff no mezcla pedidos independientes.
- [ ] No se versionan fuentes privadas, `.env*`, artifacts ni salidas generadas.
- [ ] Si toca rutas protegidas, la justificacion y aprobacion estan en el PR.
- [ ] Este PR no autoriza acciones fuera del alcance declarado.

## Checklist Tecnico

- [ ] `npm run lint` pasa sin errores cuando hay cambios frontend.
- [ ] `npx tsc --noEmit` pasa sin errores cuando hay cambios frontend.
- [ ] Los scripts Python modificados compilan correctamente.
- [ ] Las pruebas relevantes pasan localmente o en CI.
- [ ] El historial no contiene commits con credenciales expuestas.
