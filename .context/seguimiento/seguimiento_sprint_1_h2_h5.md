# Seguimiento Sprint 1 H2-H5

> Esta nota no crea alcance ni autoriza ejecucion.

## Verificacion

`F11_FREE_H2_PUBLIC_SURFACE_VALIDATED_PR_READY`

| Control | Estado |
|---|---|
| O0-A preflight | `COMPLETED_READ_ONLY` |
| O0-B decision humana | `APPROVED` |
| Seguridad historica | `SECURITY_HISTORY_GO_WITH_SUPPLEMENTAL_REQUIRED` |
| Seguridad suplementaria D0 | `COMPLETED_REDACTED_NO_ACTIVE_SECRET_IN_SOURCES` |
| Preservacion archives | `COMPLETED` |
| T_CANONICO construccion | `COMPLETED` |
| O1 desarrollo | `COMPLETED` mediante PR #414 |
| Reconciliacion post-O1 | `COMPLETED` mediante PR #415 |
| Desarrollo commit | `a2c97ec17aabc790b656d6db1b16bdc95f0af1b2` |
| Desarrollo tree | `a03681d271475e8ccbf6061ce63bc4ee5990cd5c` |
| O2 certificacion | `COMPLETED` mediante PR #416 |
| Certificacion commit | `4e7e41a9fac08e657308849701b4b1f70b994e3b` |
| Certificacion tree | `a03681d271475e8ccbf6061ce63bc4ee5990cd5c` |
| Redefinicion de flujo | `DEPLOYED_TO_MAIN_SUPERSEDED_BY_NEW_GO` |
| Acciones remotas | `NORMAL_FLOW_RESTORED` |
| DB | `FREE_H2_PUBLIC_SURFACE_VALIDATED` |
| GO documental | `RECEIVED` |
| GO tecnico PR H2 | `GO_TECHNICAL_FOR_PROTECTED_PR` |
| Work package activo | `NONE_SUPERSEDED` |
| Proximo gate unico | `PR_H2_A_DESARROLLO` |

## Porcentaje De Avance

### Hitos H2-H5

| Unidad | Estado | Puntos |
|---|---|---:|
| `H2-CA2` | `FREE_DDL_REMEDIATED_READONLY_VERIFIED` | 0 |
| `H2-CA3` | `FREE_BACKFILL_AND_SEED_VALIDATED` | 0 |
| `H3-CA4` | `PLANNED_AFTER_H2_ACCEPTED` | 0 |
| `H4-CA5` | `PLANNED_AFTER_H2_CONTRACT_STABLE` | 0 |
| `H4-CA6` | `PLANNED_AFTER_H2_CONTRACT_STABLE` | 0 |
| `H4-CA7` | `PLANNED_AFTER_H2_CONTRACT_STABLE` | 0 |
| `H4-CA13H` | `PLANNED_AFTER_H2_CONTRACT_STABLE` | 0 |
| `H5-CA8` | `PLANNED_AFTER_H2_CONTRACT_STABLE` | 0 |
| `H5-CA9/CA12` | `PLANNED_AFTER_H2_CONTRACT_STABLE` | 0 |
| `H5-CA10` | `PLANNED_AFTER_H2_CONTRACT_STABLE` | 0 |
| `H5-CA11` | `PLANNED_AFTER_H2_CONTRACT_STABLE` | 0 |
| `H5-CA13R` | `PLANNED_AFTER_H2_CONTRACT_STABLE` | 0 |

`Progreso H2-H5 = 0 / 1200 x 100 = 0%`

### Homologacion

`Flujo simple promovido por PR protegido a desarrollo, certificacion y main. Nuevos alcances esperan GO del cliente.`

## Porcentaje De Desviacion

`FREE_H2_PUBLIC_SURFACE_VALIDATED_PR_READY`.

La ruta excede la optimizacion original de cinco PR porque la auditoria detecto autoridad faltante, enlaces rotos, trazabilidad insuficiente y endurecimiento H2 adicional. La desviacion queda registrada como remediacion obligatoria previa al PR H2.

## Cumplimiento De Criterios

- Hito 1: `COMPLETED_CONTRACTUALLY_WITH_WAIVERS`.
- Hito 2: DDL Free remediada, backfill editorial, seed diccionario y fix de vista publica aplicados/verificados; PR listo con veredicto `GO_TECHNICAL_FOR_PROTECTED_PR` bajo instruccion humana separada.
- Hitos 3-5: planificados segun dependencias del nuevo plan vinculante.
- Evidencia historica: no reutilizable como PASS.
- `active_work_package = NONE_SUPERSEDED`.
- Redefinicion: `DEPLOYED_TO_MAIN_SUPERSEDED_BY_NEW_GO`.
- Rutas protegidas: sin cambios frente a `origin/main@9b48614`.
- Leads: schema/flags y CTA visual solamente; cero captura/egress.
- Schedules: requieren autorizacion separada para cambios de estado.

## Hallazgos Y Backlog

- PR #414, #415 y #416 fueron fusionados mediante PR protegidos.
- El flujo normal de PR protegido queda restaurado para cambios futuros.
- H2 es el siguiente alcance tecnico despues del PR documental y requiere JIT DB para cualquier DDL/DML.
- API de tipo de cambio permanece backlog.
- Ruta canonica contractual futura: `/programas/[slug]`.
- H2 remediacion Free: `20260826_h2_security_advisor_remediation.sql` aplicado y verificado read-only; backfill Free aplicado con segundo `NOOP`; seed `editorial_field_definitions` aplicado con 41 definiciones y visibilidad publica acotada; `20260826_h2_public_effective_view_public_fields_fix.sql` aplicado y verificado con `0` campos privados en `courses_public_effective` remoto.

### Backlog Tecnico Post Requerimiento 1

- `BACKLOG-HIGIENE-EOL-001`: se detectaron nueve archivos con ruido exclusivo CRLF/LF; `git diff --ignore-space-at-eol` no mostro cambios funcionales y fueron restaurados a HEAD para no contaminar H2. Si reaparece el ruido, normalizar EOL en tarea separada.
- `BACKLOG-MAINT-WRITERS-001`: `scripts/maintenance/lightweight_ping.py` y `scripts/maintenance/preventive_cleanup.py` son herramientas manuales con capacidad de escritura/borrado sobre datos; quedan fuera del alcance H2 actual y deben revisarse despues de cerrar el requerimiento 1 antes de conservarlas, retirarlas o endurecerlas.
- `BACKLOG-MAINT-REPORTS-001`: reportes legacy en `scripts/maintenance/*audit*.py` y `metadata_quality_report.py` siguen leyendo `courses` directamente; deben evaluarse frente al contrato H2 `courses_public_effective`, RLS/grants y pipeline tolerante antes de reutilizarlos.
- `BACKLOG-TEST-LEGACY-001`: `tests/test_harvester.py` contiene pruebas de integracion vivas contra Supabase y supuestos legacy sobre `courses`; requiere clasificacion posterior para mantenerlo, aislarlo o migrarlo al contrato H2.
- `BACKLOG-UTILS-ACTIVE-001`: `scripts/shared/utils.py` es dependencia activa de workers core; no debe eliminarse como basura. Solo corresponde normalizar EOL o modificarlo con alcance tecnico explicito.
- Estos hallazgos no autorizan cambios de codigo, DB, writers, backfill, schedules ni limpieza destructiva durante H2; se revisaran al finalizar el requerimiento 1.

## Avances

- O0-A completado.
- O0-B aprobado.
- Escaneo historico completado.
- D0 suplementario ejecutado con reporte redactado.
- Archives de desarrollo y certificacion preservados.
- Fuentes locales verificadas y hasheadas sin versionar contenido.
- T_CANONICO construido desde PR #327.
- Flujo simple desplegado y luego superseded por GO documental.
- Soporte temporal raiz eliminado definitivamente; autoridad queda en `AGENTS.md` y Obsidian.
- WP/digest/Context Graph dejan de ser autoridad ejecutable.
- PR #413 cerrado sin merge y excluido.
- PR #414, #415 y #416 fusionados.

## Siguientes Pasos

1. Preparar PR H2 limpio hacia `desarrollo` cuando el usuario lo instruya.
2. Verificar/publicar las tres fuentes solo si los archivos locales estan disponibles, inspeccionados y sus hashes coinciden.
3. No tocar Supabase Pro, writers, schedules ni deploys sin aprobacion JIT separada posterior.

## Fecha

2026-08-25

## Proximo Prompt Cavernicola

```text
Preparar PR H2 hacia desarrollo.
No autoriza Supabase Pro, schedules, writers, deploys ni produccion sin aprobacion JIT separada.
```
