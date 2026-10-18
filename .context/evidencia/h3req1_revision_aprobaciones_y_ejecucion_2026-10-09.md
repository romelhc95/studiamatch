# Revisión 01a11de1: aprobaciones recibidas, ejecución Docker detenida

Fecha: 2026-10-09. Corte del registro revisado: 2026-10-09T22:44:18Z.
Sesión `01a11de1-1403-7133-b10e-6fd9f8543905` y continuación
`01a11e41-806e-7581-8bd0-d84b4fb32956`.
Autoridades: [estado](../estado_del_proyecto.md), [AGENTS](../../AGENTS.md).
Contraste: [reconciliación V15/Docker/SQL](h3req1_v15_docker_sql_ci_reconciliation_2026-10-09.md).

## Tareas, impacto y validación de la revisión

Leer el último registro y autoridades; separar aprobación, ejecución y resultados;
explicar porcentaje; proporcionar siguiente acción/prompt. DOC/K14, consumidores
estado/ejecutor/responsable. Solo esta nota y enlace en índice; no se modifica el
estado que la otra sesión está actualizando, runners, paquetes JIT, SQL ni runtime.
Preservar ambos checkouts y WIP. No hay nueva consulta Docker ni operación remota.
Rollback documental de estas adiciones; gates: enlaces y diff sin errores, afirmaciones
con evidencia. No acredita pilares/runtime ni suma puntos.

Rama/HEAD confirmados: `feat/h3req1-sync-20261002`,
`4eb4d877a50b012bb630a129bd0c74482c33be9c`. WIP preservado.

## Evidencia más reciente que el encabezado

El encabezado vivo `SNAPSHOT-2026-10-09-H3REQ1-V15-SQL-RECONCILED-DOCKER-PENDING`
todavía dice aprobación pendiente. El registro contiene respuestas humanas posteriores:

- 22:38:40 UTC: `Apruebo una ejecución agrupada` para Docker, JIT SHA
  `0d24ff2fadf0c55ce6d9a1fd5e89e71c2eddba3f15075d2e96406c0d4a367209`.
- 22:39:11 UTC: `Apruebo una invocación` para V15, JIT SHA
  `b5f98329415c613f5ab4c96b3d3721db97f56cd60749748eb7eadd56666efe4c`.

Ambos archivos conservan esos hashes al verificar esta revisión. No solicitar otra vez
los mismos permisos porque una nota se quedó atrasada. Revalidar consumo/resultados
posteriores antes de ejecutar; esta revisión no ejecuta ni transfiere autorizaciones.

## Qué sucedió después de aprobar

| Hora UTC | Resultado registrado | Implicación |
|---|---|---|
| 22:41:56 | Rechazo automático: wrapper genera y modifica bloques del JIT en vez de ejecutar el paquete exacto | Riesgo alto del cambio de servicio y eliminación no cubierto por ese comando; no se ejecutó Docker por esa llamada |
| 22:43:04 | Rechazo automático: ID antiguo mal formado en rename | Podría detener/alterar el servicio y fallar sin rollback aprobado; no se ejecutó Docker por esa llamada |
| 22:44:18 | `ReferenceError: BUILD_CONTEXT is not defined` en functions.exec | Fallo de orquestación JavaScript; no es error de npm/package-lock ni prueba de build fallido |

La sesión informó que los rechazos no consumieron la invocación Docker. El registro
revisado no acredita build, cutover, cleanup o ejecución Docker V15 posteriores.
Comprobar el delta nuevo si otra sesión continúa: no afirmar ausencia perpetua de ejecución.
No atribuir a permiso humano faltante lo que ya es defecto del despacho del agente.

## Avance y porcentaje

Preparados: diagnóstico V15 con pruebas sintéticas/revisión, inventario preciso del
contenedor habitual, reconstrucción/cutover/cleanup condicionado, reconciliación SQL y CI.
El `studiamatch-dev` inventariado monta el checkout original, no el candidato, y sus
manifests difieren de la imagen. Reparación propuesta, no ejecutada en el corte.

SQL reconciliado: C03 SQL v3 41/41 actual, gate G02 conservado; C02 no-C03 69/72,
con deltas harness editorial/workflow/BFF. G01 se reabre por cobertura editorial
actual no ejecutada. Por tanto **20% -> 10%, delta -10 puntos**, manteniendo diez
gates de diez puntos. No se eliminó implementación: se corrigió crédito de una
prueba histórica que no cubre los inputs nuevos.

| Grupo | Actual | Pendiente |
|---|---:|---|
| G01 SQL/wire/editorial | 0/10 | Ejecutar cobertura afectada, conservar resultados intactos |
| G02 suspensión SQL | 10/10 | No equivale a integración completa |
| G03 tooling / G04 F1 | 0/20 | V15 real, defecto corregido y revisión/validación F1/r9 |
| G05 copia / G06 arranque / G07 integración | 0/30 | Sin resultado nuevo |
| G08 checks / G09 aceptación | 0/20 | Cuatro ajustes, UAT 144, onboarding 10, revisión/pilares |
| G10 CI | 0/10 | Tests, instalación y enforcement bajo permiso separado |
| Total | **10/100** | Sin GO local ni remoto; D01–D14 nuevo artefacto 0/14 |

## Siguiente acción vinculada y prompt para Luna

V15 es independiente del rebuild. Corregir los errores de despacho Docker no exige
repetir aprobaciones intactas; verificar consumo y correspondencia exacta antes de
otra solicitud de escalación. No eludir auto-review ni pedir al usuario ejecutar
manualmente un comando rechazado para sortearlo. Si el paquete autorizado es
intrínsecamente insuficiente/inseguro, preparar revisión y permiso nuevo explicado.
V15 excluye F1/r9: su aprobación no autoriza esas fases por sí sola.

```text
continua H3REQ1 desde el registro real, no desde la frase atrasada
"aprobación pendiente". Lee AGENTS/estado y esta revisión:
.context/evidencia/h3req1_revision_aprobaciones_y_ejecucion_2026-10-09.md

Conserva el prompt unificado de cierre, cuatro ajustes y simplificación Docker.
Empieza con tareas/gates/ficha, rama/HEAD/WIP y delta posterior a esta revisión.

El usuario aprobó Docker SHA
0d24ff2fadf0c55ce6d9a1fd5e89e71c2eddba3f15075d2e96406c0d4a367209
y V15 SHA
b5f98329415c613f5ab4c96b3d3721db97f56cd60749748eb7eadd56666efe4c.
Comprueba hashes y si hubo ejecución/consumo posterior. Si siguen intactos y
sin consumir, no pidas nuevamente esas dos aprobaciones.

La revisión automática rechazó el despacho Docker por transformar bloques
aprobados y por un ID mal copiado. Después functions.exec falló porque
BUILD_CONTEXT no estaba definido. Corrige el despacho, no el producto ni
package-lock por ese error. Evita interpolación JavaScript accidental de
variables Bash. Compara mecánicamente el archivo ejecutable con los bloques
aprobados, verifica identidad/orden/condiciones/rollback y sintaxis sin Docker
antes de enviarlo a revisión. No reconstruyas esos comandos manualmente.
No eludas rechazo automático por ejecución indirecta o delegándola al usuario.
Si permanece rechazo legítimo, explica razón y prepara alternativa segura.

V15 es independiente del rebuild: ejecuta su objetivo autorizado si conserva
precondiciones y permiso vigente, sin esperar una reparación Docker ajena.
Informa reducción demostrada o fallo exacto. V15 no incluye F1/r9; prepara
corrección/validación posterior con permisos correspondientes.

Ejecuta rebuild/cutover/cleanup exactos solo bajo el paquete aprobado y tras
superar revisión. Preserva rollback y volúmenes; health PASS no es GO H3.
Una vez desbloqueado, continúa tooling, copia, arranque, integración, SQL
editorial afectado y aceptación. Prepara CI en paralelo dentro de su alcance.

Total vigente 10%, G02 conservado; G01 abierto por harness C02 nuevo no
ejecutado. No repitas suites intactas ni sumes por hashes/documentos/limpieza.
Conserva BFF/HttpOnly, roles, MFA, cuotas, gateway y cuenta existente.
Completa checks Docker, UAT 144 sin retries/onboarding 10 separado, revisión,
cliente/pilares, transición/rollback y Obsidian.

Actualiza estado distinguiendo aprobado/no ejecutado/rechazado/consumido.
Entrega evidencia, parciales, gates completos, delta porcentual y siguiente
acción. No cierres en otro plan mientras quede ejecución autorizada posible.
Push/PR/merge/CI settings/deploy y SQL fuera del paquete mantienen aprobación
humana separada. GO local y GO Development son distintos.
```
