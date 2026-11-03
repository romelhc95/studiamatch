# H3REQ1 G09 delta R74 — identidad PG17, artefacto y runtime público — 2026-10-11

## Candidato y entradas

- Checkout `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
  `feat/h3req1-sync-20261002`, HEAD baseline
  `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- Se reutilizaron sin reconstrucción el artefacto de detalle del build normal
  R69 y la ruta pública de loopback R12/R47. El artefacto R69 tiene SHA-256
  `feb1a795255cec5bfe286d37f9373d6513f106a522590ae73685b30078e47029`.
- Se leyó una sola fila sintética en la base local
  `h3_final_uat_g09_20261010_r12` dentro del contenedor PostgreSQL 17
  `h3req1-g09-uat-pg17-20261010-r12`, en transacción `READ ONLY` seguida de
  `ROLLBACK`. La proyección se limitó a identidad y campos de curso; no se
  inspeccionaron variables de entorno ni datos no sintéticos.
- Ruta pública consultada:
  `http://localhost:3336/courses/ulima/analitica-aplicada-60000000/`.
  El request fue GET por loopback, timeout 5 s, cero retries.

## Resultado

PASS para el curso sintético `70000000-0000-0000-0000-000000000091`:

- PG17 devolvió una fila con institución `00000000-0000-0000-0000-000000000001`,
  nombre `Analítica Aplicada`, slug `analitica-aplicada-60000000` y URL
  `https://synthetic.h3.example/programs/analitica-aplicada/`.
- El artefacto estático R69 tiene la ruta canónica de ULima y presenta el mismo
  nombre/slug.
- El runtime Windows/loopback devolvió HTTP 200 y el HTML contiene nombre,
  slug y título esperado.
- Los tres resultados conservaron una misma identidad de curso en los campos
  comparados. El resumen sanitizado está en
  `h3req1_g09_local_acceptance_r74/pg17-static-identity-r74.json` y la respuesta
  HTTP se resume en `h3req1_g09_local_acceptance_r74/windows-r12-public-detail-r74.json`.

## Revisión y límites

Los campos `provider` y `duration_months` son nulos en la fila consultada; no se
cuentan como campos comparados ni se inventan valores. Esta comprobación
read-only acredita identidad/ruta entre PG17 sintético, HTML generado y runtime
existente. No demuestra que una edición cambie y vacíe caché, que el bundle se
reconstruya automáticamente, ni la consistencia de todo el catálogo. El runtime
HTTP y el artefacto R69 se conservaron; no se recrearon servicios ni se hizo una
escritura.

R74 amplía LOCAL-01/03/16 y G09-T10. Es evidencia parcial, no cierra esas áreas
ni G09. No cambió código de producto ni las métricas de gates.
