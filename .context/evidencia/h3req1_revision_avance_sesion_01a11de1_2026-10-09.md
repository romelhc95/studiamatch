# Revisión del avance 01a11de1 — 2026-10-09, corte V14

Autoridad: [estado vigente](../estado_del_proyecto.md), [AGENTS](../../AGENTS.md).
Sesión `01a11de1-1403-7133-b10e-6fd9f8543905` y continuación local
`01a11e41-806e-7581-8bd0-d84b4fb32956`. Corte factual:
`SNAPSHOT-2026-10-09-H3REQ1-V14-TEMPLATE-INTERACTION-FAILURE`.
Si otra sesión avanza después, esta revisión permanece fechada; no sustituir resultados nuevos.

## Tareas, impacto y gates de esta revisión

Comparar estado y registro; verificar evidencia V10/V13/V14; distinguir producto,
tooling, pruebas e integración; revisar contradicción de inputs SQL; proponer siguiente
ciclo ejecutable y prompt. Gate documental: cada afirmación enlaza resultado real,
las hipótesis no se presentan como causa demostrada y el porcentaje no aumenta por prosa.

DOC/K14, consumidores responsable/ejecutor/índice. Solo esta nota y enlace en índice,
sin cambios funcionales ni SQL, Docker, Git remoto, secretos o permisos. Preservar WIP,
checkouts, recursos y JIT consumidos. Compatibilidad de documentación: añadir revisión
fechada sin reescribir evidencia aprobada; rollback solo de las dos adiciones documentales.
Pilares: trazabilidad/calidad/mantenimiento documental; sin métricas runtime nuevas.

Rama y HEAD confirmados: `feat/h3req1-sync-20261002`,
`4eb4d877a50b012bb630a129bd0c74482c33be9c`. El diff tracked contiene cambios frontend,
SQL, tests y workflows acumulados desde baseline; no se pueden atribuir todos a estas
horas por `git diff`. El estado reporta 54 tracked y 227 entradas untracked antes de
esta revisión. No se enumeraron dependencias `.deno` excluidas para recomputar ese total.
Se observó fuente V15 de diagnóstico por prefijos en preparación, sin resultado acreditado
por el encabezado V14; no editarla ni duplicar una ejecución de otra sesión.

## Resultado: avances de diagnóstico, cierre estancado

| Aspecto | Antes | Evidencia al corte | Consecuencia |
|---|---|---|---|
| Acceso Docker Desktop WSL | Identidad/acceso sin acreditar | Socket/conexión/HTTP/Engine Linux acreditados en evidencia V3; posteriores reutilizan atestación | No repetir requisito `/proc` directo en Ubuntu ni pedir reinstalar Docker |
| Lecturas sintéticas | Errores genéricos de inspect | [V10](h3req1_c03_v10_image_template_field_isolation_result_2026-10-09.md): exit 0, 17/17 casos focales, 25 expresiones y cleanup OK | Progreso técnico real de la herramienta, no prueba del producto |
| Mapa de labels | Se exigía mapa vacío completo | V12 falló por labels presentes; V13/V14 distinguen labels ajenos frente a claves H3 | Corrige una condición sintética demasiado amplia sin demostrar causa F1 |
| Resultado visible | V13 perdió fases por OUTPUT_REJECTED | [V13](h3req1_c03_v13_output_rejected_2026-10-09.md) no distingue bytes/línea; [V14](h3req1_c03_v14_template_field_interaction_failure_2026-10-09.md) conserva fases y exit 1 | Mejor diagnóstico, no resultado F1 recuperado de V13 |
| Formato combinado | Fallo repetido de evaluación | V14: formato completo FAIL, 25 campos aislados OK, FIELD_INTERACTION_ERROR | Defecto del camino de composición acotado; causa exacta todavía pendiente |
| F1/r9 | Pendientes | V14 no alcanzó ninguno; V13 no permite saber si leyó F1 y no ejecutó r9 | No declarar F1 nunca leído en todas las versiones; r9 sigue sin PASS |
| Cuatro ajustes | Implementación/pruebas iniciales anteriores | Matriz reconciliada; sin ejecución actual sobre candidato final | No contarlos como nuevas pruebas por actualizar la matriz |
| CI independiente | Patch V3 preparado | Revisión hold_for_evidence; sin pytest/actionlint/Docker/publicación/enforcement | No hay avance de funcionamiento del control CI |

Los fallos V9 por ejecutar shell con Python, V12 por criterio de labels y V13 por salida
rechazada son errores del proceso/tooling, no defectos de negocio demostrados. Revisiones
estáticas sin hallazgos no predijeron todos los fallos runtime. El stop-on-failure
preservó los límites autorizados, pero no convierte las múltiples versiones en progreso
de aceptación. Cada JIT consumido se conserva; no hay autorización nueva por esta nota.

## Porcentaje y salvedad de evidencia

El tablero y estado siguen G01=10/10, G02=10/10, G03–G10=0/10: **20% -> 20%, delta 0**.
Es métrica de diez gates completos de cierre, no porcentaje de implementación ni esfuerzo.

| Grupo | Puntos reportados | Falta |
|---|---:|---|
| G01 SQL/wire, G02 suspensión SQL | 20/20 históricos | Reconciliar aplicabilidad de inputs actuales |
| G03 tooling, G04 diagnóstico suficiente/F1 | 0/20 | Composición corregida, F1 con controles/disposición y r9 completo |
| G05 snapshot, G06 arranque, G07 integración | 0/30 | Copia íntegra, healthz real, C03 integrado |
| G08 checks/revisión, G09 aceptación | 0/20 | Candidato final, cliente/pilares, UAT 144 y onboarding 10 |
| G10 CI/paquete PR/review | 0/10 | Control instalado/efectivo y review humano final |

Hay una contradicción documental que debe resolverse antes de reutilizar SQL: la
[matriz del candidato](h3req1_desarrollo_existente_y_cierre_delta_2026-10-08.md#matriz-de-aceptación-sobre-el-candidato-vigente)
registra cambio del `tests/sql/h3_pg17_harness.sql`, hash actual
`8d4ea8d0e55525b835f2e6220486860b685a9dff7e65cf1c0cb46efbf35adce5`, respecto al corte
2026-10-04 `e1525daa888895619b477402b688e0a3409d2eba9d53c1e2c60f674f03aa61d3`.
La evidencia de 41/41 corresponde a una revalidación anterior. Esta revisión no recalculó
el cierre transitivo SQL vigente. Identificar si el delta pertenece al manifiesto exacto
C03 v3, a sus prerrequisitos o a otro harness editorial antes de renovar o conservar G02.
No afirmar 41/41 actual por copiar estado, ni invalidar todas las suites por un delta
ajeno a sus inputs. El 20% citado es el reportado; no certificación nueva de esos dos gates.
D01–D14 nuevo artefacto permanece 0/14; las pruebas remotas anteriores se preservan.

## Siguiente ciclo y permisos

1. Usar V14 como punto de partida y coordinar con preparación V15 existente. Aislar la
   primera combinación/prefijo que falla, con errores sanitizados que identifiquen campo,
   categoría y fase, sin imprimir inspect/Env/stderr crudo. Formular hipótesis concreta
   y caso mínimo; no volver a ejecutar el mismo template completo para confirmar lo ya sabido.
2. Corregir únicamente composición/contexto/serialización que la reproducción demuestre.
   Verificar formato combinado tanto con mapas presentes como ausentes, resultado estructural,
   límites y casos negativos. Conservar todos los controles de aislamiento. Si se opta por
   lecturas separadas, justificar coherencia del recurso/estado y acotar cantidad, límite y
   drift en el JIT; no cambiar estrategia de lectura implícitamente.
3. Preparar antes de pedir permiso el paquete completo de diagnóstico/corrección y fases
   condicionadas F1+r9, con límites iterativos explícitos y stop-on-failure. No aprobación
   ilimitada. No reutilizar V14 ni otros consumidos. Una autorización por objetivo permite
   evitar aprobaciones por cada metadata dentro del alcance; excepciones nuevas no se heredan.
4. Tras tooling PASS, snapshot -> healthz -> C03 integrado. Si falla una etapa, resolverla
   con prueba mínima sin reiniciar todo. Preparar CI independiente mientras tanto, incluyendo
   sus tests locales; no declarar esas pruebas autorizadas si el paquete vigente las excluye.
5. Reconciliar inputs SQL y renovar solo evidencia afectada. Ejecutar aceptación de los
   cuatro ajustes, no regresión de sesión/roles/MFA y UAT final. Consolidar manifest del
   candidato, revisión independiente, cliente/pilares y documentación.
6. CI protegido, push/PR/merge y despliegue siguen requiriendo instrucciones separadas.
   Evitar efecto Pages Production del bootstrap en main; demostrar aislamiento antes de
   promocionar. Después de GO_LOCAL_PR, integrar/deploy Development y D01–D14 autorizados.

No falta una nueva decisión funcional para los cuatro ajustes. El bloqueo inmediato es
corregir la herramienta de lectura y conseguir permiso del nuevo objetivo delimitado.
No solicitar al usuario reinstalar/borrar Docker, copiar secretos o rehacer cuenta/MFA.

## Prompt sustituto para Luna 6 Max

```text
continua H3REQ1 desde el corte vigente. Lee AGENTS, encabezado actual del estado,
protocolo constructor y:
.context/evidencia/h3req1_revision_avance_sesion_01a11de1_2026-10-09.md
No reutilices el prompt que solicita la captura WSL inicial: esa fase ya avanzó.

Candidato /home/romel/src/studiamatch-h3req1-sync-20261002,
feat/h3req1-sync-20261002, baseline 4eb4d877a50b012bb630a129bd0c74482c33be9c.
Confirma WIP y preserva original, evidencia, secretos y dependencias excluidas.
Empieza con tareas/gates y ficha de impacto. No reconstruyas todo el proyecto.

Al corte V14: endpoint WSL acreditado; V10 tuvo 17 casos focales y 25 campos PASS.
V14 pasó siete fixtures de labels y 25 campos aislados, pero el formato combinado
falló FIELD_INTERACTION_ERROR antes de F1/r9. V13 no permite saber si leyó F1.
Todos esos JIT están consumidos. No repitas un paquete consumido ni atribuyas
esto a Docker defectuoso o a los cuatro requisitos del cliente.

Hay preparación V15 por prefijos: comprueba su estado actual y úsala si sigue
siendo el siguiente ciclo; no dupliques runners ni ejecuciones de otra sesión.
Primero localiza la combinación mínima que falla y la condición exacta; después
corrige el defecto demostrado. No publiques otra variante que solo agregue una
etiqueta de error sin acercarse a la reproducción/corrección. Prueba el formato
completo con mapas presentes/ausentes y negativos; conserva aislamiento y fail-closed.

Prepara paquete coherente de objetivo, comandos/pins/recursos/operaciones,
egress/timeout/límites de iteración/fallo/recuperación, con F1 y r9 condicionados.
Pide JIT nuevo solo cuando el paquete concreto esté revisado. Las pruebas/recursos
fuera de autorización vigente requieren permiso; esta instrucción no lo concede.
No prometas un cierre con aprobación ilimitada ni relajes controles para obtener PASS.

Tras validación del tooling, continúa snapshot -> healthz real Pages/workerd ->
C03 integrado Edge/PG17/PostgREST dentro del alcance aprobado, sin pedir continua
por cada paso cubierto. No reinicies todo al fallar una fase. Preserva pruebas SQL
aplicables, pero reconcilia antes el harness actual frente al cierre transitivo
C03 v3: el hash editorial cambió y 41/41 fue una revalidación anterior. Explica
qué evidencia sigue vigente y cuál necesita ejecución, sin invalidación general.

Prepara y valida el CI independiente en lo que permita el paquete vigente,
sin esperar a F1 para trabajo independiente. Su publicación, configuración y
enforcement requieren instrucción protegida separada y evitar deploy Production.

Los cuatro ajustes ya están implementados inicialmente. Renueva cobertura
afectada sobre candidato exacto: edición/procedencia, auditoría atómica protegida,
disponibilidad <=90 días con compatibilidad legacy, correo autenticado y fallback.
Conserva BFF/HttpOnly, roles, MFA, cuotas, gateway y cuenta existente.
Completa checks Docker, revisión independiente, UAT vigente 144 sin retries,
onboarding 10 en escenario separado, cliente/pilares y transición/rollback.

Reporta gates completos y parciales por separado. Total reportado al corte:20%,
delta0; no es implementación del producto. Resuelve la salvedad G02 antes de
certificar reutilización. No sumes puntos por versiones, hashes o documentos.
Cada ciclo informa fase, resultado/exit, causa demostrada, evidencia, permiso
consumido y siguiente gate. Espera aprobación hasta30min en intervalos que
permitan mensajes; silencio nunca autoriza. No cierres en otro plan si existe
trabajo autorizado ejecutable. GO_LOCAL_PR y GO_DEVELOPMENT_REAL son distintos;
operaciones remotas/promoción mantienen instrucciones separadas.
```

## Verificación

Lecturas locales de registros, fuentes y evidencia; `git diff --check` documental.
Sin nuevas pruebas de producto, Docker/SQL/remotos ni cambios en runners o JIT.
No incrementa porcentaje. La presencia de fuente V15 es preparación, no PASS.
