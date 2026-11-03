# Revisión de rumbo H3REQ1 — entorno recuperado, checks pendientes

Fecha local: 2026-10-09, America/Lima. Registro revisado hasta
2026-10-10T04:51:49Z (2026-10-09 23:51:49 Lima).
Sesión `01a11de1-1403-7133-b10e-6fd9f8543905` y continuación
`01a11e41-806e-7581-8bd0-d84b4fb32956`.
Autoridad: [estado](../estado_del_proyecto.md), [AGENTS](../../AGENTS.md).

## Tareas, impacto y límites

Contrastar encabezado con registro posterior; clasificar avances ejecutados;
verificar pendientes/porcentaje y proponer corrección de ejecución sin nuevo scope.
DOC/K14, consumidores responsable/ejecutor/índice; adición de nota e índice, sin
reescribir los archivos que está actualizando otra sesión. Preservar WIP, ambos
checkouts, fuentes, evidencia y aprobaciones. Sin runtime/SQL/Docker/remoto nuevo.
Gate documental: separar observación, evidencia fechada, hipótesis y resultado;
rollback solo de estas adiciones. No acredita pilares por prosa ni suma puntos.

Rama y HEAD baseline confirmados: `feat/h3req1-sync-20261002`,
`4eb4d877a50b012bb630a129bd0c74482c33be9c`. No son manifest del WIP completo.

## Sí hay avances operativos nuevos

1. Entorno habitual: según última lectura acotada registrada, `studiamatch-dev`
   está healthy, ID `500931b0f086d29ec9e751e1fd652f9b7ccd357f3eb64daa8751344776162049`,
   imagen `studiamatch-h3req1:20261009-v3`, checkout candidato en `/app` y volumen
   `studiamatch_h3req1_node_modules`. El original permanece detenido con nombre
   `studiamatch-original-dev-20261009` para rollback. No nueva consulta Docker en esta revisión.
2. V15 aisló en el fixture el conjunto `{NanoCpus, HostConfig.Mounts}`. Es avance
   de diagnóstico sintético, no causa funcional del producto. El formato residual
   posteriormente falló en tmpfs; F1 sigue sin controles acreditados.
3. PG17 editorial llegó al marcador `h3_pg17_harness_ok`, con fases sanitizadas
   OK, pero el exit numérico del harness no quedó preservado. Resultado parcial:
   no inferir PASS completo ni cerrar G01 por el marcador.
4. r9 V4 pasó preflight/sintéticos/actionlint de tres workflows después de corregir
   indentaciones. ShellCheck falló; stop-on-failure dejó ESLint/TypeScript/suites sin ejecutar.
5. ShellCheck V2 fue aprobado el 2026-10-09 23:48:35 Lima y ejecutado. Pasaron
   preflight, extracción y 34 sintéticos; produjo un finding allowlisted:
   `scan_credentials.sh:195:5`, `SC2209`, exit 1. El agente corrigió la asignación
   literal, registrada como `mode="diff"`, y verificó sintaxis/whitespace.
   La validación ShellCheck posterior de esa corrección sigue pendiente.

El encabezado aún afirma ShellCheck V2 pendiente. El registro posterior demuestra
aprobación y ejecución consumida. No volver a solicitar ese V2 ni repetirlo.
El paquete siguiente r6 está preparándose para el scanner corregido y checks no
alcanzados; no se acredita ejecución por su preparación. Comprobar delta posterior
si la sesión sigue activa antes de decidir nueva acción.

Fuentes: [estado](../estado_del_proyecto.md),
[reconciliación y resultados](h3req1_v15_docker_sql_ci_reconciliation_2026-10-09.md),
[PG17/npm](h3req1_pg17_npm_v4_execution_and_preparation_2026-10-09.md),
[cutover/cleanup](h3req1_docker_candidate_cutover_v4_preparation_2026-10-09.md)
y registro local de continuación. No se consultó GitHub/Supabase para sustituir evidencia.

## Lo que todavía no avanza y por qué conviene redirigir

- La limpieza V6 no eliminó contenedores/redes: falló preflight con mismatch genérico.
  No necesita bloquear pruebas nuevas aisladas; preserve recursos/evidencia y difiera
  limpieza hasta tener diagnóstico/acotación aprobada.
- Varias invocaciones se dedicaron a fallos del propio parser/dispatcher. ShellCheck V1
  confundió json/json1 y descartó salida; V2 finalmente produjo finding útil. npm audit
  dejó stdout vacío y stderr no clasificado, sin resultado JSON. No declarar auditoría PASS.
- C03 integrado, Pages/workerd healthz, UAT final y CI efectivo siguen sin evidencia.
  Un contenedor habitual healthy no demuestra Pages/workerd ni esa integración.
- Estado e índices atrasados pueden pedir permisos ya consumidos o insinuar pruebas
  no ejecutadas. Reconciliar aprobación, ejecución, exit, resultado y consumo por objetivo.

Recomendación: mantener alcance, producto y seguridad; cambiar ejecución hacia tres
resultados concretos: G03 completo; cobertura SQL editorial aceptada G01; lectura/snapshot/
arranque e integración por etapas. Preparar trabajo independiente bajo sus permisos;
no avanzar dependientes tras FAIL ni habilitar despliegue con gates abiertos.
Cada próximo runner debe probar previamente su contrato de salida de la herramienta
fijada y registrar códigos de salida separados. No crear un framework diagnóstico nuevo.
Preservar históricos, corregir solo tooling vigente y evitar nuevas variantes si el
contrato canónico puede repararse dentro del alcance autorizado.

## Cuadro y porcentaje

| Gate/grupo | Puntos completos | Resultado/falta |
|---|---:|---|
| G01 SQL/editorial | 0/10 | Marcador observado; recuperar exit si existe registro, o renovar ejecución con captura correcta/JIT |
| G02 suspensión SQL | 10/10 | PASS C03 SQL v3 e inputs exactos 41/41; no integración |
| G03 tooling | 0/10 | Actionlint PASS; scanner corregido; faltan ShellCheck posterior, ESLint/tsc y suites |
| G04 F1 | 0/10 | Reducción sintética parcial; residual tmpfs y controles pendientes |
| G05–G07 copia/arranque/integración | 0/30 | Sin aceptación completa |
| G08–G09 checks/aceptación | 0/20 | npm audit sin resultado válido; UAT 144/onboarding 10/revisión/pilares pendientes |
| G10 CI | 0/10 | Patch local actualizado; sin control instalado/efectivo |
| Total | **10% -> 10%; delta 0** | Avances operativos parciales reales, ningún gate nuevo completo |

El denominador son diez gates iguales. No mide implementación ni tiempo. G03 completo
subiría el total a 20%; G01 también cerrado lo llevaría a 30%, si los demás resultados
conservan aplicabilidad. D01–D14 sobre nuevo artefacto sigue sin aceptación acreditada.

## Prompt de continuidad y corrección de rumbo

```text
continua H3REQ1 desde el estado y el delta de registro más reciente, manteniendo
el prompt unificado de cierre, cuatro ajustes y simplificación Docker. Lee:
.context/evidencia/h3req1_revision_rumbo_y_avance_2026-10-09.md
y AGENTS/estado/protocolo constructor. Empieza con tareas/gates/ficha y candidato.

No reinicies el entorno: studiamatch-dev ya tiene evidencia healthy y monta
el candidato; el original está preservado para rollback. No confundas su salud
con el healthz Pages/workerd. Limpieza Docker no es precondición para las pruebas.
No vuelvas a pedir V15/rebuild/V2 por encabezados atrasados: consulta consumo real.

ShellCheck V2 se aprobó/ejecutó y consumió: 34 sintéticos PASS, SC2209 en
scan_credentials.sh:195:5. La asignación se corrigió. Comprueba si r6 ya avanzó;
si no, termina paquete completo y revisado para validar corrección y continuar
ShellCheck, ESLint, TypeScript y suites no alcanzadas. Reutiliza actionlint solo
si los tres workflows conservan los hashes del PASS. No repitas suites intactas.
JIT nuevo si requiere ejecución fuera de autorización vigente, por objetivo,
sin reinvocar aprobaciones consumidas ni hacer propuestas vagas.

Corrige la ejecución, no amplíes scope: cada runner debe conocer el formato de
la herramienta fijada y preservar exit numérico y fases sanitizadas. No lances
otro diagnóstico que descarte el motivo y obligue a otra invocación para verlo.
Usa herramientas/runners existentes; registra solo rutas/códigos allowlisted,
sin secretos, inspect completo ni logs crudos.

PG17 editorial dejó marcador pero no exit del harness. Primero intenta recuperar
el exit desde evidencia ya existente sin alterar históricos. Si no existe, prepara
renovación exacta con captura separada de productor/psql/verificador/cleanup y
JIT correspondiente. No inventes PASS ni repitas SQL intacto ajeno a ese delta.

Completa la corrección del residual de formato F1 con reproducción mínima,
sin repetir el template total ni atribuir causa al producto por analogía.
Después tooling -> F1/disposición -> snapshot íntegro -> healthz Pages/workerd ->
Edge/PG17/PostgREST y C03 integrado, con permisos y stop-on-failure existentes.
Prepara trabajo independiente CI/SQL según sus permisos mientras otra vía se
bloquea; no avanzar una etapa dependiente tras FAIL.

Conserva los cuatro ajustes, BFF/HttpOnly, roles, MFA, cuotas, gateway y cuenta
existente. Completa npm audit con resultado válido, checks finales, revisión,
UAT 144 sin retries/onboarding 10 separado, aceptación cliente y seis pilares,
compatibilidad/rollback y Obsidian. CI remoto/Git/deploy conservan permisos separados.

Prioridad de resultado: cerrar G03; cerrar cobertura G01; lograr primer arranque
real y ensayo integrado. Total acreditado actual10%; parciales se informan aparte.
No sumar por entorno healthy, documentos, variantes o hashes.
Cada ciclo entrega resultado, exit, evidencia, permiso consumido y siguiente gate.
No finalizar con otro plan cuando quede ejecución autorizada posible. Si falta
permiso, termina preparación revisable y espera respuesta hasta30min en intervalos;
silencio no autoriza. GO_LOCAL_PR y GO_DEVELOPMENT_REAL requieren evidencias distintas.
```

Verificación de esta nota: lecturas focalizadas y `git diff --check`, sin runtime ni
modificación de runners/JIT/state en edición por otra sesión. No incrementa porcentaje.
