<!-- Plantilla reusable. Ningún resultado preaprobado: completar con el candidato real,
no abrir/actualizar PR con placeholders ni checks no ejecutados. Historia preservada en
.context/seguimiento/plantilla_pr_historica_2026-09-24.md. -->

Guía de sistema: [índice integral](../.context/indice.md). Protocolo de impacto y mantenimiento: [protocolo del constructor](../.context/trazabilidad/protocolo_constructor.md).

## Resumen

Describir cambio, requerimiento/criterio cliente, alcance autorizado y veredicto acotado.
Identificar rama/base, SHA y manifest de fuentes/build/resultados; HEAD solo no identifica WIP.
Enlazar estado/atestación sanitizada/evidencia; no adjuntar documento privado del cliente.

## Evidencia De Este PR

Indicar comandos/casos ejecutados, fecha, entorno, inputs/config, grado (mock/runtime/remoto)
y artifacts sanitizados recuperables. Diferenciar NO-EJECUTADO de PASS y lo histórico de
lo vigente. Ninguna tabla de esta plantilla declara resultados hasta rellenarse.

## Avances Del Cambio

| Componente/contrato | Cambio implementado | Consumidores/impacto | Evidencia |
|---|---|---|---|

Usar ficha y matriz de `.context/trazabilidad/`; declarar inclusión/exclusión de paths,
maintenance/WIP/artefactos y revisión del scope guard antes de reclamar readiness.

## Pilares Obligatorios

Sustituir estado de plantilla por veredicto real o N/A justificado con owner/riesgo.

| Pilar | Estado | Resultado validado y límites |
|---|---|---|
| Funcionalidad | `PENDIENTE/APROBADO` | |
| Escalabilidad | | |
| Seguridad | | |
| Mantenimiento | | |
| Calidad | | |
| Rendimiento | | |

## Transicion Transparente

Documentar `expand -> compatibilidad -> deploy -> contract`, rollback, recuperación,
orden de consumidores y evidencia de No degradacion funcional. Si el cambio solo es
documental/tooling, justificar fases no aplicables; no simular despliegues.

| Fase | Alcance/resultado real | Evidencia / autorización cuando aplique |
|---|---|---|
| expand | | |
| compatibilidad | | |
| deploy | | |
| contract | | |
| Rollback/recuperación | | |
| No degradacion funcional | | |

## Evidencia Para Cliente

Enlazar criterio/atestación sanitizada, resultado por ambiente y pendientes. No declarar
cierre contractual remoto por UAT local. Waivers: causa, prueba, owner, riesgo, vencimiento
y aprobación humana. No inventar porcentajes ni copiar conteos de otro candidato.

## Validaciones

Completar esta tabla solo con resultados realmente ejecutados. Si no aplica o está
pendiente, registrar causa, riesgo residual y owner; no silencio ni PASS por intención.

| Validacion | Resultado/exit/casos | Ambiente/grado | Evidencia/límites/owner |
|---|---|---|---|
| Credential scan | | | |
| Python tests | | | |
| Python compile | | | |
| PostgreSQL DB Change Gate | | | |
| ESLint | | | |
| TypeScript | | | |
| Static build | | | |
| actionlint / ShellCheck | | | |
| UAT/runtime/integración | | | |
| security-audit / CI independiente efectivo | | | |
| CodeQL si aplica | | | |
| Cloudflare Pages / smoke preview | | | |
| Browser snapshot si aplica | | | |
| security-auditor | | | |
| Documentación / trazabilidad / fuente cliente | | | |

## Seguridad Y Datos

- [ ] Scanner y revisión del diff sin credenciales/PII/firmas/JWT en código o evidencia.
- [ ] API keys/identidad/RLS/roles/MFA/último admin preservados cuando aplica.
- [ ] HIGH/CRITICAL ausentes; findings/waivers documentados con owner/aprobación.
- [ ] DB/secretos/producción/restore/schedules/writers solo bajo JIT explícito separado.

## Alcance Y Limites

- [ ] Requerimiento/issue y criterio vinculados; PR enlazado a la sesión que lo trabaja.
- [ ] Rama/base/diff/inclusión compatibles con scope autorizado y guard/protecciones.
- [ ] Evidencia vigente/preservada/invalidada por impacto identificada.
- [ ] Promociones/remotos/cleanup pendientes explícitos; este PR no los autoriza.

## Checklist Tecnico

- [ ] Checks necesarios ejecutados contra candidato correcto en Docker; resultados reales.
- [ ] Ficha de impacto, consumidores/contratos y capa técnica actualizados.
- [ ] Modelo/atestación cliente, seis pilares y transición/rollback revisados.
- [ ] Review/CI requerido efectivo y no autodisminuido; no omitir checks por historia.
- [ ] GO local PR distinguido de GO Development real; siguiente promoción no implícita.
