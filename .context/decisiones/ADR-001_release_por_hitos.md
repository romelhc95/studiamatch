---
tags: [adr, sdlc, releases, hitos]
---

# ADR-001: Releases por hito con promocion selectiva

## Estado
Aceptado

## Contexto
StudIAMatch trabaja con entregas por hitos y fechas contractuales. El equipo necesita poder avanzar en `desarrollo` con hitos futuros sin obligar a que todos esos cambios lleguen juntos a produccion.

El riesgo principal aparece cuando `HITO 2` ya fue integrado en `desarrollo`, pero la fecha de entrega requiere promover solo `HITO 1` a `main`. En ese escenario, promover `desarrollo` completo arrastraria cambios no aprobados o no certificados.

## Decision
Se adopta un flujo de releases por hito:

- Cada hito se implementa en una rama `feat/hito-N-*` nacida desde `desarrollo`.
- Los cambios aprobados se integran a `desarrollo` mediante PR y pasan el gate `security-audit`.
- Cuando un hito queda listo para QA/entrega, se crea una rama `release/hito-N` desde el commit exacto aprobado.
- La rama `release/hito-N` congela el alcance entregable y es la unica fuente para promover ese hito a `certificacion` y luego a `main`.
- `desarrollo` puede seguir recibiendo `HITO N+1` sin afectar la entrega de `HITO N`.

Flujo base:

```text
feat/hito-1-* -> desarrollo
                 -> release/hito-1 -> certificacion -> main

feat/hito-2-* -> desarrollo
                 -> queda fuera de main hasta su propio release
```

## Manejo de correcciones
Si durante QA o revision del cliente se detecta que al hito liberable le falta algo, el fix se aplica primero sobre la rama del release afectado:

```text
release/hito-1
  -> fix/hito-1-ajuste
  -> release/hito-1
  -> certificacion
  -> main
```

Luego ese mismo fix se propaga hacia `desarrollo` mediante merge-forward o cherry-pick para evitar regresiones cuando se continue con hitos posteriores.

Regla: los fixes de un hito congelado no se hacen primero sobre `desarrollo` si `desarrollo` ya contiene cambios de hitos futuros.

## Base de datos y ambientes
El flujo mantiene la regla DB-as-Code existente:

- Schema, migraciones, RPCs, triggers, RLS, instituciones, perfiles, categorias, reglas y salarios viajan como cambios versionados.
- Las tablas operativas `staging_raw`, `cleansed_programs`, `enriched_programs` y `courses` son por ambiente y no se sincronizan entre Free y Pro como flujo normal.
- Un snapshot operativo Pro -> Free solo se permite como backfill/remediacion explicita, documentada y aprobada.

Limitacion vigente: `desarrollo` y `certificacion` usan Supabase Free. Para QA totalmente aislado por hito, se recomienda evaluar un branch/proyecto Supabase separado para certificacion o para cada release critico.

## Alternativas consideradas
1. Promover siempre `desarrollo` a produccion: descartado porque arrastra cambios de hitos futuros no aprobados.
2. Mantener todo HITO 2 fuera de `desarrollo` hasta publicar HITO 1: descartado porque bloquea avance e iteracion temprana.
3. Usar solo cherry-pick directo a `main`: descartado porque reduce trazabilidad, salta el flujo `certificacion` y aumenta riesgo operativo.

## Consecuencias
- Positivo: permite avanzar con hitos futuros sin bloquear entregas contractuales.
- Positivo: produccion recibe solo el alcance aprobado y certificado.
- Positivo: los fixes de QA quedan trazables y se pueden propagar hacia trabajo futuro.
- Negativo: requiere disciplina al crear ramas `release/hito-N` desde commits exactos.
- Negativo: si hay cambios DB incompatibles entre hitos, se debe aislar la certificacion o postergar migraciones no liberables.
- Negativo: mientras `certificacion` comparta Supabase Free con `desarrollo`, la validacion de datos puede contaminarse si HITO 2 cambia schema/datos antes del cierre de HITO 1.
