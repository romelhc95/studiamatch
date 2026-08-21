# Retrospectiva Hito 1

> Registro historico para mejora de flujo. No reabre Hito 1 ni autoriza H2.

## Duracion Canonica

```text
Inicio registrado: 2026-07-11
Entrega tecnica: 2026-08-04
Canary productivo: 2026-08-08
Incidente/observacion: 2026-08-09
Cierre contractual con waivers: 2026-08-20
Duracion final: 40 dias transcurridos
Fechas inclusivas: 41
Dias habiles colombianos aproximados: 26
```

Estimacion historica:

```text
Estimacion tecnica original: 72h
Horas reales trabajadas: UNKNOWN
```

Escenario optimizado contrafactual:

```text
20-23 dias calendario
Oportunidad estimada: 17-20 dias
```

El escenario optimizado es una hipotesis de mejora, no causalidad demostrada.

## Metricas Historicas

- 521 commits unicos alcanzables desde todas las refs.
- 202 merge commits.
- PR exactos pendientes de verificacion mediante metadata GitHub.
- Actividad posterior al incidente no debe denominarse churn.
- Simulaciones, promociones y reconstrucciones deben excluirse del throughput funcional.

## Causas De Demora

- CA1-only definido despues de la fecha objetivo.
- Construccion parcial de CA2 antes de excluirlo.
- Taxonomia de fases redefinida repetidamente.
- PR separados para implementacion, evidencia y post-merge.
- Reconstruccion de controles entre ramas.
- Gates de promocion descubiertos tarde.
- Autorizaciones documentales excesivamente granulares.
- Trust plane creciendo dentro del hito.
- Context Graph append-only y contradictorio.
- Checkouts historicos y ramas sucias.
- Correcciones Linux/EOL y CI tardias.
- E2E global posterior al canary.

## Mejoras Adoptadas

- Contract Freeze antes de implementar.
- Un Work Package por paquete funcional salvo cambio de ambiente o riesgo.
- Presupuesto objetivo de 3-6 PR principales por hito.
- Build Once con commit, tree, diff digest, artifact digest, paths, modes y provenance congelados.
- E2E temprano antes de Certification.
- Control explicito de infraestructura correctiva para desacoplar hardening no bloqueante.

## Objetivos Iniciales

```text
3-6 PR por hito
0 reconstrucciones manuales ordinarias
100% WP con digest
100% R3 con JIT single-use
100% E2E contractual antes de Certification
0 rebaseline de alcance despues de iniciar implementacion
```

H2 y H3 calibraran objetivos temporales posteriores.
