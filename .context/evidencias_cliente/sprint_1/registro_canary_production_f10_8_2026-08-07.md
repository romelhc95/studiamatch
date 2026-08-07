# Registro Production Canary F10.8 - 2026-08-07

| Campo | Valor |
|---|---|
| ID | `EVID-H1-CANARY-F10.8-001` |
| Subfase | `F10.8` |
| Run | `31157736479` |
| Estado | `FAIL_CLOSED_HTTP_403_RESTORE_NOOP` |
| Evidencia contractual | `EVID-H1-010=PENDING` |

## Resultado Sanitizado

El Production Canary fue autorizado con aprobacion separada del environment
`Production` y se ejecuto sobre `main@529ca111f1fef40efb15676ad6f07d002a54ae92`.
FG1, el manifest pre-canary y el snapshot privado quedaron completados. FG2
harvest fallo de forma fail-closed por respuestas HTTP `403` de la fuente
externa; cleansing, enrichment, sync y FG3 quedaron `skipped`.

La identidad de la cohorte, URLs, dominios, UUIDs, hosts Supabase, secrets y
datos operativos no se documentan en esta evidencia.

## Recuperacion

- Snapshot privado creado en el runner.
- Restore exacto completado.
- Segundo restore `--expect-noop` completado.
- Manifest `after-cleanup` equivalente al estado pre-canary.
- Environments Production y Production-Scheduled-FG1/2/3 conservaron
  `AUTOMATION_ENABLED=false` y `PRODUCTION_WRITERS_PAUSED=true`.

## Hallazgo De Observabilidad

La verificacion posterior detecto URLs operativas en logs del run. No se
detectaron credenciales, hosts Supabase ni UUIDs en artifacts sanitizados, pero
la presencia de URLs en logs impide usar el run como evidencia positiva y exige
remediacion antes de cualquier retry.

## Accion Pendiente

Antes de un segundo Production Canary F10.8 se requiere promover a `main` una
remediacion que:

- elimine URLs, slugs, nombres, UUIDs y JSON de institucion de logs del canary;
- agregue source-access preflight read-only antes del snapshot;
- endurezca el manifest pre-canary con gates y perfil completos;
- mantenga artifacts exclusivamente sanitizados;
- preserve `EVID-H1-010=PENDING` hasta un canary completo PASS.
