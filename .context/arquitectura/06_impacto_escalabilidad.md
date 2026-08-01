# Impacto Y Escalabilidad

Esta vista registra impacto tecnico esperado y limites conocidos. No crea
requisitos de capacidad, SLO, subtareas ni criterios adicionales.

## Impacto Por Hito

| Hito | Superficies afectadas | Dependencia principal | No alcance protegido |
|---|---|---|---|
| Hito 1 / CA1 | FG2, FG3, environments y observabilidad; FG1 solo como soporte operativo | Evidencia efectiva por ambiente | Cero CA2, DB, frontend o leads/email en candidate CA1-only propuesto |
| Hito 2 / CA2-CA3 | Schema, RLS, PostgREST, cuatro estaciones y backfill | CA2 integral antes de CA3 | Sin `/admin`, Home o entrega real-time |
| Hito 3 / CA4 | Identidad admin, writer seguro, auditoria y `/admin` | Hito 2 desplegado | Sin redefinir CA2/CA3 |
| Hito 4 / CA5-CA7-CA13H | Home, contrato publico y documentacion | Datos publicos estables y referencia aprobada | Sin Resultados ni tipo de cambio real |
| Hito 5 / CA8-CA13R | Resultados, filtros, cards y paginacion | Campos CA2 e indices certificados | Sin busqueda semantica, reviews o email real-time |

## Limites Actuales Conocidos

| Componente | Limite o riesgo | Control actual o requerido |
|---|---|---|
| Orquestador | Cohorte acotada y presupuesto global | Gates, freshness y circuit breaker antes del limite |
| Harvester | Crawl/Playwright costoso y volumen acotado | Allowlist, exclusiones, hashing y persistencia temprana |
| Cleansing | Lotes y posible competencia de workers | RPC atomica o fallback idempotente |
| Enrichment | Dependencia externa y camino secuencial | Provider health y fallback marcado como mock |
| Sync | Cohorte limitada por corrida | Idempotencia por URL; drenaje/paginacion debe demostrarse donde aplique |
| FG3 | HEAD secuencial y timeout global | Concurrencia con FG2 y clasificacion fail-closed requerida |
| Frontend | Dataset y filtros pueden crecer en cliente | Paginacion, limites de consulta y presupuesto de performance por candidate |
| Data API | Limite de respuesta por consulta | Paginacion explicita y allowlist de columnas |

## Regla De Escalabilidad

Sprint 1 no incluye QA de carga masivo. Los tests de resiliencia, paginacion e
idempotencia demuestran correccion dentro del candidate, pero no autorizan
promesas de capacidad no aprobadas. Un nuevo umbral contractual sigue
`INTAKE -> EST -> REQ -> TASK`.

## Referencias

- [Pipeline y estados](./03_pipeline_estados.md)
- [Datos y seguridad](./04_datos_seguridad.md)
- [Estrategia de pruebas](../pruebas/00_estrategia_pruebas_sprint_1.md)
