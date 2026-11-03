# HITO-001 - Automatizacion Segura CA1

`HITO-001` historico queda preservado por decision humana O0-B con waivers. Para el nuevo pedido, H1 se redefine como automatizacion segura y reactivacion gradual de FG1/FG2/FG3 despues de H2 y H3 aceptados. Esta nota no autoriza ejecucion remota.

## Resultado

| Campo | Valor |
|---|---|
| Estado | `REDEFINED_ACTIVE_AFTER_H2_H3` |
| Criterio activo | `H1-CA1` |
| Cutoff contractual | PR #291 / `64e4ed895d43121c5683e26a355993f18e528a5c` |
| Baseline tecnico posterior | PR #327 / `main@ad89e8ab9575b37476502d6062e22c044ad6447b` |
| Waivers historicos | `EVID-H1-011`, `EVID-H1-012`, `EVID-H1-013`, `EVID-H1-016`; no cierran CA1 nuevo |

## Alcance Nuevo

- Readiness de FG1, FG2 y FG3.
- Preflight distingue `blocked`, `preflight-only` y ejecucion funcional.
- Corridas con estaciones skipped no cierran evidencia funcional.
- Validacion con `actionlint`, frecuencia documentada y concurrency group corregido.
- Confirmacion de `pipeline_ready`, limites, entornos y rollback.
- Activacion JIT secuencial: FG1, observar, repausar/evaluar; FG2, observar, repausar/evaluar; FG3, observar, repausar/evaluar; schedules ordinarios.

## Handoff Vigente — 2026-10-29

**Estado de ejecución: `PREPARATION_ONLY_PENDING_H2_H3_PRO_ACCEPTANCE`.** El H3
editorial está aceptado localmente, en Development y en Certification; eso no
cierra H3 para producción. Pro conserva H2 parcial fuera del ledger, falta la
cohorte agregada y aún no se aplicó el manifest H3. H1 depende de acreditar el
contrato H2 y el despliegue/aceptación H3 en Pro.

No activar FG1, FG2, FG3 ni schedules. Primero reconciliar el estado H2 con
ledger, schema y cohorte; después promover/aplicar el expand compatible de H3,
desplegar y verificar BFF/editorial/publicación. La secuencia de activación de
H1 requiere su propio gate y JIT posteriores; este handoff no los autoriza.

### Actualización del paquete productivo — 2026-10-29

La lectura Pro quedó disponible y el preflight SELECT-only está completado:
23 migraciones registradas, objetos H2 parciales fuera de ledger, cohorte sin
lectura agregada y objetos Admin/H3/snapshot pendientes. H3 editorial sigue
aceptado en Development y Certification, no en Pro. El paquete local de
remediación no está publicado y tiene el gate documental integral FAIL; no hay
GO de promoción ni disposición vigente para producción. Antes de reabrir
readiness de H1 se requieren H2 report/verify con cohort agregada, aplicación
H2/H3 por el flujo protegido que se apruebe, compatibilidad y smoke Pro
aceptados. Mantener sin activar FG1, FG2, FG3 y schedules.

## Transferencias

### Handoff H2 actualizado — 2026-10-29

El reporte local H2/Pro ya reconoce el estado parcial observado fuera del ledger
y produce agregados con `REVIEW_REQUIRED`; no presenta el estado como GO, no
habilita apply y conserva las guardas del migrador. Sus 29 pruebas y quince
controles focales de lectura/paridad/migrador pasan en Docker, 44/44. También se
prueba que una fila no es grupo duplicado, dos cursos con igual institución/slug
sí lo son, GET/RPC no siguen redirects y los probes de privacidad H3 fallan
cerrado ante 302/500, y el stdout del reporte queda como JSON limpio. La cohorte real aún no se ha leído: el workflow `report`
usa el service key Production (bypass RLS) y requiere JIT específico sobre el
SHA integrado en `certificacion`. No reaplicar H2 por diferencias del ledger.
H1 sigue en preparación; no activar FG1, FG2, FG3 ni schedules.

- `H1-CA2P` pasa a `H2-CA2` y requiere evidencia nueva.
- `H1-CA7P` pasa a `H4-CA7` y requiere evidencia nueva.
- F10.9/WP2B y F10.10/M3 son historia no promocionable.
- Waivers historicos de H1 no pueden reutilizarse para cerrar CA1 del nuevo pedido.

## Trazabilidad

- [Acta de cierre contractual](../evidencias_cliente/sprint_1/acta_cierre_contractual_hito_001.md)
- [ADR-0026](../decisiones/ADR-0026_cutoff_h1_y_baseline_sprint1.md)
- [Plan Maestro H2-H5](../operaciones/plan_maestro_sprint1_h2_h5.md)
