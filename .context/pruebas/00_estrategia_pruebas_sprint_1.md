# Estrategia De Pruebas Sprint 1

Esta estrategia deriva exclusivamente de [REQ-EST-001](../backlog_tareas/req_est_001_sprint_1/_index.md)
y la [adenda aprobada](../backlog_tareas/req_est_001_sprint_1/adenda_cliente_001_sanitizada.md).
No mantiene estado vivo, no certifica candidates y no crea alcance.

## Principios

1. Cada test se enlaza con un CA aprobado y una unica TASK.
2. Un gate tecnico protege la entrega, pero no se convierte en funcionalidad
   cliente ni en CA adicional.
3. Todos los casos permanecen `PLANNED` hasta ejecutarse contra un candidate
   inmutable y revisarse de forma independiente.
4. Evidencia local no certifica Free, Pro o produccion.
5. Evidencia historica no se hereda como resultado del candidate nuevo.
6. CA12 se prueba por trazabilidad de su absorcion en CA9, sin suite o
   entregable duplicado.
7. CA13 conserva dos trazas: Home `H4-CA13H` y Resultados `H5-CA13R`.

## Clasificacion De Tests

| Clasificacion | Uso |
|---|---|
| `CONTRACTUAL_CA` | Demuestra directamente el comportamiento de un CA aprobado. |
| `SECURITY_REQUIRED` | Protege secretos, acceso, RLS, PII, egress o minimo privilegio del alcance modificado. |
| `REGRESSION_REQUIRED` | Demuestra que una superficie vigente protegida no se rompe. |
| `OPERABILITY_REQUIRED` | Valida build, jobs, observabilidad, rollback, recovery, canary o smoke necesarios para operar. |
| `QUALITY_ADVISORY` | Mejora recomendada y no bloqueante; no cambia el criterio de salida. |
| `OUT_OF_SCOPE` | Valida o registra una frontera excluida; nunca crea trabajo dentro del Hito. |

Un caso puede cubrir varias dimensiones, pero registra una clasificacion
primaria para evitar duplicar cobertura.

## Matriz Canonica

Cada matriz usa estas columnas:

| Columna | Regla |
|---|---|
| Test ID | Identidad estable dentro del Hito |
| CA | CA original y alias normalizado cuando aplique |
| Requisito verificable | Derivado de REQ/TASK, sin reinterpretacion |
| Clasificacion | Uno de los seis valores autorizados |
| Precondicion | Candidate, fixture o gate necesario |
| Procedimiento | Accion minima reproducible |
| Resultado esperado | Condicion binaria o evidencia objetiva |
| Ambiente | Local, Free, Certification o Production segun TASK |
| Evidencia | Vacia hasta candidate o referencia sanitizada futura |
| Estado | `PLANNED`, `PENDING_QA` o `VERIFIED` |

## Ejecucion Y Evidencia

Una ejecucion futura debe registrar:

```text
Run ID | Test ID | Candidate commit | Candidate tree | Ambiente |
Version o herramienta | Fecha UTC | Procedimiento | Resultado observado |
Outcome | Warnings o skips | Evidencia | Revisor
```

`Outcome` admite `PASS`, `FAIL`, `BLOCKED`, `SKIPPED` o
`DEVIATION_ACCEPTED_FAIL_CLOSED`. `VERIFIED` indica que el resultado fue
contrastado; no significa necesariamente `PASS` ni `APPROVED_FOR_CLIENT`.
`PENDING_QA` indica evidencia primaria localizada pero todavia sin revision
independiente suficiente.

Para pasar de `PLANNED` a `VERIFIED` se requieren candidate commit/tree
inmutables, ambiente identificado sin datos sensibles, procedimiento
reproducible, resultado observado, warnings/skips, evidencia sanitizada y
revision QA independiente.

## Matrices Por Hito

- [Hito 1](./01_matriz_tests_hito_1.md): CA1 runtime y guards de traslado/preservacion historica CA2P/CA7P.
- [Hito 2](./02_matriz_tests_hito_2.md): CA2 y CA3 vigentes pendientes.
- [Hito 3](./03_matriz_tests_hito_3.md): CA4 vigente pendiente.
- [Hito 4](./04_matriz_tests_hito_4.md): CA5, CA6, CA7 y CA13 Home vigentes pendientes.
- [Hito 5](./05_matriz_tests_hito_5.md): CA8 a CA12 y CA13 Resultados vigentes pendientes.
- [Gobierno de hallazgos](./06_gobierno_hallazgos.md).

## Gates Documentales

- Mermaid parseable o gap declarado; nunca asumir PASS visual.
- Todos los enlaces locales y notas alcanzables desde `00_INDICE.md`.
- Context Graph, EOL, secret scan y `git diff --check` en PASS.
- Diff limitado a `.context/**` para este paquete.
- Ningun documento de pruebas mantiene estado vivo de Hito o TASK.
