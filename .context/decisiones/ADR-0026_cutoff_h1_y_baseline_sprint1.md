# ADR-0026 - Cutoff H1 Y Baseline Sprint 1

## Estado

`ACCEPTED`

## Contexto

El Plan Maestro `REQ-EST-001` separa el cierre contractual de Hito 1 del baseline
tecnico usado para construir la siguiente etapa. O0-A verifico remotamente los
refs protegidos y O0-B aprobo la decision superior.

## Decision

- `CUTOFF_CONTRACTUAL_H1 = PR #291 / 64e4ed895d43121c5683e26a355993f18e528a5c`.
- `TECH_BASE = PR #327 / main@ad89e8ab9575b37476502d6062e22c044ad6447b`.
- `AUTH_BASE = desarrollo@9f163c2c5f8dc54b4986ce75ef1d5c69a740bedf`.
- Hito 1 queda `COMPLETED_CONTRACTUALLY_WITH_WAIVERS`.
- PR #413 queda `CLOSED_NOT_MERGED_EXCLUDED`.
- F10.9/WP2B y F10.10/M3 quedan historicos no promocionables.

## Consecuencias

- `T_CANONICO` se construye desde `TECH_BASE`, no desde `desarrollo`.
- Las fuentes DOCX/HTML permanecen locales; solo se versionan hashes y tamanos.
- H2-H5 requieren work packages nuevos y evidencia nueva.

## Referencias

- [Acta de cierre Hito 1](../evidencias_cliente/sprint_1/acta_cierre_contractual_hito_001.md)
- [Baseline y homologacion](../operaciones/baseline_preservacion_homologacion_sprint1.md)
