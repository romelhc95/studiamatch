# Estandar De Prompts Retroalimentados

Estado: `PROMPT_RETROALIMENTADO_REQUIRED`.

Este estandar es vinculante para todo prompt futuro de desarrollo del proyecto.
La autoridad viva permanece en `.context/estado_del_proyecto.md`; este archivo
describe la forma operativa exigida.

Resumen operativo: analizar, implementar, validar, revisar, convertir hallazgos
en tareas, corregir y revalidar hasta GO.

## Ciclo Obligatorio

Todo prompt de desarrollo debe iterar hasta cumplir sus criterios de GO:

```text
analizar
-> implementar el cambio minimo correcto
-> validar
-> revisar
-> convertir fallos y hallazgos en tareas
-> corregir
-> revalidar
-> repetir hasta GO
```

## Reglas

1. Cada fallo de test, hallazgo de auditor, drift o gate incompleto alimenta la siguiente iteracion.
2. No se declara GO por intencion, implementacion parcial o pruebas locales cuando el alcance exige evidencia canonica o remota.
3. Cuando se requiera intervencion humana, se usa Question con opciones concretas, recomendacion y consecuencias.
4. JIT, push, PR, merge, deploy, workflow_dispatch, ramas protegidas, Supabase writes y acciones destructivas requieren aprobaciones humanas separadas.
5. Despues de cada aprobacion se reevalua el estado, se actualiza el plan y se continua desde el gate detenido.
6. El cierre requiere evidencia canonica, criterios cliente, pruebas completas, revisiones especializadas y ausencia de hallazgos HIGH/CRITICAL.
7. No se ocultan fallos clasificandolos genericamente como historicos o fuera de alcance sin demostrar baseline reproducible.
8. Cada waiver requiere causa, evidencia reproducible, owner, riesgo, vencimiento y aprobacion humana.
9. Antes de abrir o actualizar un PR se debe usar `.github/pull_request_template.md` y ejecutar las validaciones necesarias para completar sus tablas con resultados reales. La plantilla no admite placeholders finales ni checks declarados por intencion; si algo no aplica o queda pendiente, se registra causa, riesgo residual y owner.
10. Antes de cualquier plan o build, el agente debe listar las tareas que ejecutara, los gates y la evidencia esperada. La implementacion funcional solo comienza despues del prompt humano `continua`; ese prompt no reemplaza aprobaciones JIT ni aprobaciones protegidas.
11. El cierre de cada ciclo exige checks locales en Docker, pilares y criterios de aceptacion, actualizacion Obsidian, transicion `expand -> compatibilidad -> deploy -> contract`, rollback y promocion protegida `desarrollo -> certificacion -> main`. Cualquier NO-GO bloquea el avance hasta su remediacion y revalidacion.

## H2REQ1

H2REQ1 solo puede cerrarse cuando exista promocion transparente a `main`, Pro
tenga `h2-expand-compat` verificado, produccion este estable,
`h2-contract-public-reader` haya retirado la lectura publica directa legacy y
la evidencia canonica habilite H3REQ1. La cohorte legacy queda como
compatibilidad temporal hasta paridad editorial estricta posterior a H3.
