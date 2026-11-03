# H3REQ1 — análisis de sesión y dependencias para cierre local

Fecha: 2026-10-08. Sesión analizada: `01a11a7e-0f79-7cf2-b37f-409d8d28fed5`.
Clasificación: análisis documental contrastado con fuentes y resultados locales.
Autoridad: [estado vivo](../estado_del_proyecto.md), [AGENTS](../../AGENTS.md) y
[plan único](../operaciones/plan_cierre_integral_h3req1_2026-10-04.md).
Continuación: [prompt Luna 6 Max](../operaciones/h3req1_prompt_luna_6_max_cierre_local_2026-10-08.md).
Esta nota no concede permisos, no es aceptación funcional y no reemplaza resultados.

## Pedido y alcance de esta actualización

El responsable solicita documentar los hallazgos detalladamente y entregar un prompt
para una sesión de Luna 6 Max que trabaje en ciclos hasta acreditar GO. Exige preguntas
concretas si hace falta una decisión o autorización; no desea otro cierre limitado a
preparación. Esa exigencia fija el objetivo, no convierte pruebas pendientes en PASS ni
autoriza acciones protegidas. Un intento fallido debe convertirse en diagnóstico,
corrección y revalidación dentro de la misma sesión cuando existan permisos suficientes.

Ficha constructor: dominio documental DOC/REL y referencias a tooling K14; consumidores:
estado, índice Obsidian, ruta operativa, tarea H3 y entrada técnica. No cambia contratos
de producto, SQL, runtime ni CI. Se preservan WIP, fuentes originales, reportes históricos
y permisos consumidos. Se renuevan navegación y traspaso; los resultados runtime quedan
pendientes. Transición: añadir notas y enlaces compatibles; sin deploy ni contract en
este corte. Rollback documental: retirar únicamente las adiciones de este ciclo, sin
revertir cambios preexistentes. Autoría documental solicitada; sin JIT runtime nuevo.

## Fuentes efectivamente consultadas

- Registro local JSONL de la sesión indicada, bajo `.codex/sessions/2026/10/08/`; se
  revisaron mensajes de usuario/asistente, aprobaciones y cierre. No se copia el registro
  al repositorio ni se publica su contenido completo.
- Encabezado vigente del estado, índice, protocolo constructor, entrada técnica,
  cobertura y ruta de cierre; los cuerpos históricos no sustituyen al corte vigente.
- [Resultado F2b](h3req1_c03_f1_daemon_diagnostic_f2b_2026-10-08.md),
  [resultado F2c](h3req1_c03_f1_daemon_diagnostic_f2c_2026-10-08.md),
  [revisión F2d](h3req1_c03_f2d_diagnostic_static_review_2026-10-08.md) y
  [JIT F2d](../operaciones/manifiesto_jit_h3_close03_f1_diagnostic_f2d_2026-10-08.md).
- Fuentes actuales del runner/helper F2d, proyección Docker y scanner; identidad Git
  local, sidecar e inputs del paquete F2d. Sin conexión al socket Docker, SQL o remoto.

El candidato sigue en `feat/h3req1-sync-20261002`, baseline HEAD
`4eb4d877a50b012bb630a129bd0c74482c33be9c`. HEAD identifica el baseline, no todo el WIP.
El original `/home/romel/src/studiamatch` y su evidencia se preservan; esta actualización
solo escribe documentación en el candidato. Las cifras de WIP de la sesión son históricas,
no un inventario final para PR.

## Secuencia acreditada de la sesión

| Momento UTC del registro | Acción | Resultado y límite |
|---|---|---|
| 07:56 | Ficha de impacto y hashes C02/C03 | La sesión registró 72/72 inputs no-C03 de C02 v4 y 41/41 de C03 SQL v3 coincidentes. Sin ejecución SQL ni nuevos PASS de suites. |
| 08:06 | Corrección scanner y comparador | Temporal privado, errores tratados como fallo y regresiones preparadas; comparación de tmpfs/mounts e identidad de imagen estructurada. Sin validación runtime. |
| 08:20–08:22 | Aprobación y ejecución F2b | Una invocación y dos riesgos MEDIUM aceptados. Falló en canonicalidad del path Unix, antes de prueba del proceso y API Docker. Permiso consumido. |
| 08:43–08:44 | Aprobación y ejecución F2c | Una invocación y aceptación nueva de dos riesgos MEDIUM. Socket local/canónico confirmado; identidad del proceso no probada. Cero API Docker, imagen o inspect F1. Permiso consumido. |
| 08:52 | Preparación F2d | Método directo SO_PEERCRED, pins y límites. Solo revisión estática; helper/parser sin probar en Docker y JIT sin aprobación registrada. |
| 08:56 | Corrección del scope guard | Errores de git diff/grep y paths vacíos pasan a bloquear. Regresiones positivas/negativas y actionlint pendientes. |
| 08:57 | Cierre de sesión | No se acreditó snapshot, arranque ni C03 integrado; tampoco readiness PR o aceptación Development. |

## Hallazgos, causas conocidas y límites

### H01 — F1 aún carece de diagnóstico exacto

F1 creó un contenedor y lo rechazó antes de arrancarlo. El reporte no conserva el nombre
del control discrepante. F2b/F2c se detuvieron antes de leer ese contenedor, por lo que no
resuelven el fallo. No atribuirlo al ownership de tar, al tmpfs, a mounts ni a la imagen por
analogía. D4/J3 sí demostró una expectativa incorrecta sobre Mounts en otro ensayo; esa
evidencia permite una regresión, pero no prueba la causa de F1 o S1.

Cierre: identidad del destino demostrada, lectura allowlisted autorizada del ID F1 exacto,
nombre de cada control discrepante, corrección mínima y regresiones sin quitar aislamiento.

### H02 — F2c no conservó un submotivo útil de identidad

Su reporte contiene `daemon-identity-not-proven`. No distingue falta de permisos/visibilidad
del proceso, ambigüedad, intermediario u otro fallo. No demuestra ninguna de esas hipótesis.
F2d propone códigos sanitizados específicos para evitar otro resultado ambiguo.

Cierre: diagnóstico acotado y accionable; si no se acredita el motor actual, presentar
alternativa local concreta. No repetir métodos equivalentes ni instalar/reconfigurar el
engine sin autorización.

### H03 — F2d tiene una dependencia pre-ejecución sin resolver

La revisión exige validar helper/parser en Docker antes de considerar F2d listo. La
operación F2d, a su vez, intenta acreditar la identidad de ese Docker. El paquete no
documenta todavía un camino autorizado para completar esa validación previa. Además, el
runner invoca `python3` para observar el proceso/socket del host: esto debe reconciliarse
explícitamente con las reglas Docker aplicables, sin interpretar el JIT como excepción
implícita ni trasladar la prueba a un contenedor que cambie la visibilidad requerida.

Es una dependencia operativa identificada por lectura, no un fallo runtime observado.
Resolverla preparando un paquete de validación con fixtures controlados y contexto de
ejecución explícito. Si requiere excepción de ejecución o un entorno alternativo, formular
una decisión humana concreta antes de ejecutar. No rebajar la prueba de identidad a
`unix://`, `stat`, `realpath` o un nombre de proceso.

Pins F2d verificados en la revisión de esta sesión:

- JIT: `f662d26783c9bb09d6cef2688da6bbf55e725dcc7fc77b92472ba0dc83a6c02e`.
- Sidecar del runner: 1/1 entrada coincidente; manifiesto de inputs: 17/17 coincidentes.
- Esto solo acredita integridad de archivos, no corrección del helper ni autorización.

### H04 — tooling corregido no equivale a tooling validado

Scanner: verificar archivo limpio, detección/redacción, fallos de lectura/escritura/grep,
temporales propios y concurrencia. Comparador: formatos observados, positivos y negativos,
tmpfs en HostConfig.Tmpfs, mounts persistentes por separado e imagen por ID inmutable.
Scope guard: rutas H3/documentales explícitas, rechazo de paths ajenos/vacíos y errores de
Git/filtro; no admitir carpetas completas indiscriminadamente. Actionlint/ShellCheck y
revisión independiente siguen pendientes. No ejecutar regresiones en host por conveniencia.

### H05 — falta demostrar la cadena local completa

Separar tres gates: copia completa -> arranque Pages/workerd -> C03 integrado. No lanzar
DB/Edge antes de comprobar el arranque. No repetir todo el drill si falla la copia o el
servidor web. C03 integrado exige servicios reales coordinados y recuperación persistente;
SQL solo, VM de Edge o mocks aislados no lo sustituyen.

La limpieza de fixtures antiguos no es precondición si pueden crearse recursos nuevos.
Antes de eliminar: inventario exacto bajo permiso, evidencia recuperable preservada y JIT
destructivo separado. Preservar studiamatch-dev, ambos checkouts y recursos ajenos.

### H06 — candidato final, CI y disposiciones todavía pendientes

Los resultados previos de 287 tests/4 skips y UAT/onboarding no aceptan automáticamente
las fuentes finales. Identificar el candidato completo, ejecutar checks por impacto y UAT
final de 48 casos × 3 viewports = 144 ejecuciones/capturas, cero retries, onboarding 10/10.
Si cambia cobertura, explicar el delta sin ajustar cifras para aparentar continuidad.

CI independiente efectivo requiere evidencia de protección y revisión sobre el SHA final;
un YAML local o check histórico verde no basta. Preparar su bootstrap desde base confiable
y solicitar lecturas/configuración remotas por separado cuando sean necesarias.

Conservar owner Romel y revisión 2026-11-03 para braces/priceMin: seguimiento, no waiver.
Agrupar las disposiciones faltantes de warnings, PyPDF2 y cuatro tests live; no inventar
owner, aceptación ni ejecución. Hallazgos HIGH/CRITICAL no pueden quedar abiertos al cierre.

## Gates vinculantes y decisiones por objetivo

| Gate | Evidencia exigida | Permiso/decisión si falta |
|---|---|---|
| Diagnóstico suficiente | Validación del auxiliar, destino local acreditado y discrepancia F1 concreta | Resolver contexto de validación/ejecución; después JIT diagnóstico fresco. |
| Copia y arranque | Fuentes aisladas completas y servidor real saludable | JIT de stack con recursos, imágenes, bootstrap/red y fases exactas. |
| C03 integrado | Suspensión, rechazo, finalizadores únicos, datos/auditoría/admin y recuperación reales | SQL/recuperación solo sobre PG17 desechable aprobado. |
| Candidato final | Suites pertinentes, UAT, revisión, cliente/pilares y grafo vigente | Disposiciones de pendientes agrupadas; renovar solo evidencia afectada. |
| GO_LOCAL_PR | Todo lo anterior y CI independiente efectivo conforme al plan | Bootstrap/configuración remota si hace falta; push/PR separados. |
| Inicio remoto | SHA integrado, ambiente/host y servicios identificados, despliegue autorizado y ventana preparada | Merge, deploy, configuración y ventana D01–D14 con permisos propios. |
| GO_DEVELOPMENT_REAL | D01–D14 reales aceptados conforme al plan | No sustituirlos por pruebas locales; corregir y repetir casos afectados autorizados. |

JIT significa aprobación humana específica justo antes de una operación protegida.
CI significa integración continua; PR, solicitud de incorporación de cambios; UAT, pruebas
de aceptación de usuario; MFA, autenticación con segundo factor; BFF, servidor intermedio
que mantiene la sesión fuera del navegador. SO_PEERCRED es el mecanismo del sistema usado
para identificar al proceso del otro extremo de una conexión local.

## Evidencia preservada, seis pilares y cierre de esta nota

Implementación, pruebas, integración y despliegue permanecen separados. La funcionalidad
tiene PASS previos acotados, no aceptación final. Escalabilidad y rendimiento no reciben
mediciones nuevas en este corte. Seguridad conserva controles y pendientes explícitos;
mantenimiento mejora navegación/traspaso; calidad exige regresiones y revisión pendientes.
No declarar ninguno de los seis pilares acreditado globalmente por esta prosa.

Esta actualización no ejecutó Python/npm, Docker, SQL, migraciones, writers ni operaciones
remotas, y no consumió JIT. La comprobación de enlaces/diff es documental; no sustituye
tests docs/cliente en Docker ni revalida el grafo completo. El objetivo de la continuación
es GO demostrado; el estado factual previo permanece hasta sustituirlo por resultados.

Validación documental efectuada: 13 destinos de enlaces locales en las dos notas nuevas
comprobados, cero ausentes; `git diff --check` sin errores en los paths rastreados.
La ficha y enlaces se añadieron a estado, índice, ruta, tarea, hito y entrada técnica.
El diff acumulado incluye WIP anterior; no se atribuye completo a este ciclo. Las notas
nuevas siguen sin stage, al igual que el trabajo previo; no hubo commit ni publicación.
