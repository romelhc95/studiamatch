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
| Funcionalidad |  |  |
| Escalabilidad |  |  |
| Seguridad |  |  |
| Mantenimiento |  |  |
| Calidad |  |  |
| Rendimiento |  |  |

## Transicion Transparente

| Fase | Evidencia |
|---|---|
| `expand` |  |
| `compatibilidad` |  |
| `deploy` |  |
| `contract` |  |
| Rollback |  |
| No degradacion funcional |  |

## Evidencia Para Cliente

- Acta ejecutiva:
- Matriz de trazabilidad:
- Metricas verificables:
- Grado de evidencia:
- Traduccion cliente incluida:

## Validaciones

Completar esta tabla solo con resultados realmente ejecutados. Si una validacion no aplica o no pudo ejecutarse, indicarlo explicitamente con causa y riesgo residual.

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
| Smoke preview |  |
| Browser snapshot |  |
| security-auditor |  |

## Seguridad Y Datos

- [ ] No hay credenciales hardcodeadas ni secretos en logs, errores, URLs, comentarios o evidencia publica del PR.
- [ ] Los identificadores operativos sensibles o innecesarios se mantienen solo en evidencia interna cuando aplique.
- [ ] `security-audit` esta verde en este PR, o queda pendiente con causa y owner.
- [ ] Ejecute `@security-auditor` sobre los cambios y no hay hallazgos criticos/altos, o existe waiver aprobado.
- [ ] Cambios DB, produccion, schedules, writers, deploys, secrets o acciones destructivas no se ejecutan en este PR salvo aprobacion JIT separada y documentada.

## Alcance Y Limites

- [ ] El PR enlaza requerimiento o issue aplicable.
- [ ] La rama/base corresponde al flujo autorizado.
- [ ] El diff no mezcla pedidos independientes.
- [ ] No se versionan fuentes privadas, `.env*`, artifacts ni salidas generadas.
- [ ] Si toca rutas protegidas, la justificacion y aprobacion estan en el PR.
- [ ] Este PR no autoriza acciones fuera del alcance declarado.
- [ ] El PR documenta `expand -> compatibilidad -> deploy -> contract`, rollback y retiro futuro de legacy cuando aplique.

## Checklist Tecnico

- [ ] `npm run lint` pasa sin errores cuando hay cambios frontend.
- [ ] `npx tsc --noEmit` pasa sin errores cuando hay cambios frontend.
- [ ] Los scripts Python modificados compilan correctamente.
- [ ] Las pruebas relevantes pasan localmente y/o en CI con resultado documentado.
