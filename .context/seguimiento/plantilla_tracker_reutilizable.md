# Plantilla Tracker Reutilizable

> Todo requerimiento futuro debe copiar esta estructura y completar solo hechos verificables.

## 1. Verificacion

Debe incluir fase, requerimiento, hito/TASK, WP activo, branch, commit, tree, sources/hashes, CI, ambiente, ultimo gate y proximo gate.

## 2. Porcentaje De Avance

Separar progreso contractual y madurez de entrega.

Progreso contractual:

| Estado | Puntos |
|---|---:|
| Unidad aceptada | 100 |
| Unidad no aceptada | 0 |
| Waiver aceptado | 100 reportado aparte |

Madurez operativa permitida:

```text
PLANNED
ACTIVE
IMPLEMENTED
VERIFIED_DEVELOPMENT
CERTIFIED
ACCEPTED
ACCEPTED_WITH_WAIVER
```

## 3. Porcentaje De Desviacion

Debe incluir baseline, actual, diferencia, unidad, fuente y supuestos. Nunca declarar `0%` sin calendario aprobado.

## 4. Cumplimiento De Criterios

Usar matriz:

```text
CA -> cambio -> prueba -> ambiente -> evidencia -> resultado
```

## 5. Hallazgos Y Backlog

Clasificacion obligatoria:

```text
BLOCKER
SECURITY
CONTRACTUAL
PLATFORM_BACKLOG
NON_BLOCKING
```

## 6. Avances

Registrar solo hechos demostrables: commit/tree, PR, check, run, artifact o aprobacion.

## 7. Siguientes Pasos

Debe incluir proximo gate unico, dependencias, aprobaciones, stop conditions y operaciones prohibidas.

## 8. Fecha

Debe incluir fecha del snapshot, fuente temporal, zona horaria y fecha de expiracion del estado.

## Bloque Terminal - Prompt Cavernicola

Debe contener frase de autorizacion exacta, alcance exclusivo, baselines, sources/hashes, precedencia, orden obligatorio, allowlist, denylist, validaciones, stop conditions, salida esperada, prohibiciones y proximo gate unico.

No puede contener secretos, PII, UUID operativos ni URLs sensibles.

## Metricas Obligatorias Por WP Y Evidencia

```text
estimate_h
started_at
completed_at
elapsed_calendar_h
active_effort_h
blocked_wait_h
ci_review_wait_h
rework_effort_h
rework_reason
actual_source
```

## KPIs

- Lead time tecnico.
- Tiempo hasta aceptacion contractual.
- Tiempo bloqueado.
- PR cycle time mediano y p85.
- First-pass yield.
- Correctivos atribuibles a 7/14 dias.
- Change failure rate.
- Tiempo de recuperacion.
- Gates aprobados al primer intento.
- Throughput funcional.
- Throughput de seguridad.
- Throughput documental.
- Promocion y simulacion separadas.
