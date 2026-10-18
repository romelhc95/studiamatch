# H3REQ1 — ruta ejecutable histórica de recuperación del ensayo a GO PR y Development

> **Archivo histórico, no operativo.** Este corte NO-GO del 2026-10-08 fue superado por el cierre local acreditado en R178/R181/R182. Se conserva para explicar decisiones y resultados de ese ciclo; la autoridad actual es [estado del proyecto](../../estado_del_proyecto.md) y la navegación vigente es el [índice Obsidian](../../indice.md). La copia recuperable del origen, tomada antes del movimiento, está en el backup externo registrado en la [evidencia R11](../h3req1_documentacion_consolidacion_trazabilidad_2026-10-13_r11.md).

Antes de tocar componente/runtime, usar el [protocolo del constructor](../../trazabilidad/protocolo_constructor.md)
para contratos, consumidores y pruebas por impacto, con navegación desde el [índice Obsidian](../../indice.md). La guía documental global se agrega
al inventario PR H3 solicitado, sujeto a scope guard y aprobación futura; no cambia gates.

Fecha: 2026-10-06. Pedido humano: documentar acciones detalladas y prompt para alcanzar
un resultado verificable, evitando vueltas de preparación sin ejecución. Esta nota es
un complemento operativo del plan único, no cambia alcance cliente ni concede JIT.
Estado de partida: **NO-GO C03 integrado y Development real**.

## Continuación del candidato en el corte 2026-10-08 — NO-GO histórico

Actualización del ciclo: el BFF ahora falla cerrado con 503 si quota y gateway usan
claves HMAC idénticas, antes de admitir cuota; la UAT sintética de esta barrera aún no
corre. El scan formal actual `13b4219e-4661-4e92-b4e0-1aafffc88ee3` revisó 51/51 rutas
del snapshot actual, cero hallazgos reportables confirmados, cuatro candidatos diferidos,
cobertura parcial. No acredita los valores HMAC/bindings desplegados ni los gates remotos.
El paquete r4 sigue esperando aprobación fresca para una sola ejecución. Candidato,
`GO_LOCAL_PR` y `GO_DEVELOPMENT_REAL` siguen **NO-GO**; ver
[evidencia del ciclo](../h3req1_helper_docker_fixture_2026-10-08.md).

La ejecución r3 autorizada terminó **NO-GO**: manifiesto 13/13, pytest 19/20, comparador
duplicado y scanner no redactaron; scope guard PASS. Se corrigieron las causas y se ampliaron
las regresiones del scanner a contenido binario, `.lock` y líneas `++`. El paquete r4 tiene
13/13 hashes verificados contra las fuentes actuales y espera aprobación humana nueva para
una sola validación Docker. La revisión formal del snapshot se selló con cero hallazgos
reportables confirmados, cuatro candidatos diferidos y cobertura parcial; las reglas remotas
de CI, bindings Auth/Worker y host UAT siguen sin comprobarse. Ver
[evidencia del ciclo](../h3req1_helper_docker_fixture_2026-10-08.md).
No continuar a F2d sobre F1 hasta validar helpers, revisar resultados y obtener JIT separado
con aceptación renovada de los dos riesgos MEDIUM.

Complemento de traspaso: [análisis detallado de sesión 01a11a7e](../h3req1_analisis_sesion_01a11a7e_2026-10-08.md)
y [prompt único para Luna 6 Max](../../operaciones/h3req1_prompt_luna_6_max_cierre_local_2026-10-08.md).
Primero resolver la validación previa y contexto de ejecución del auxiliar F2d; su
preparación estática no basta para solicitar ejecución como paquete ya validado.
La continuación es cíclica hasta GO demostrado, con aprobación humana por objetivo
protegido y preservación de cada resultado fallido. No cambia D01–D14 ni sus gates.

F1 sigue NO-GO y sin campo discrepante registrado. F2b fue consumido en `context-config`;
el endpoint no pasó canonicalidad. F2c recibió aprobación para una invocación, confirmó
socket Unix local/canónico, pero no probó la identidad del peer y terminó en
`daemon-identity-proof`. No hubo Docker API, lectura de imagen ni inspect F1; ambos JIT están
consumidos y no se reintentan. Ningún reporte demuestra proxy ni causa histórica de F1.
[Resultado F2b](../h3req1_c03_f1_daemon_diagnostic_f2b_2026-10-08.md) y
[resultado F2c](../h3req1_c03_f1_daemon_diagnostic_f2c_2026-10-08.md).

F2d usa una conexión Unix local y `SO_PEERCRED` para identificar el peer del kernel sin
enviar bytes de aplicación. Solo continúa a una lectura de imagen fijada y un inspect del ID
F1 exacto tras probar que el peer directo es `dockerd` local. El paquete estático/hash-bound,
pendiente de revisión Docker/aprobación nueva y aceptación expresa de ambos residuales MEDIUM.
[JIT F2d](../../operaciones/manifiesto_jit_h3_close03_f1_diagnostic_f2d_2026-10-08.md).

C02 v4 no-C03 coincide 70/72: cambiaron `.github/workflows/security-audit.yml` y
`web/functions/_lib/admin-bff.ts` por la guardia HMAC. C03 SQL v3 coincide 41/41. Se
preservan los resultados SQL sin repetir suites ni ejecutar SQL; debe renovarse la prueba
BFF afectada y validar el workflow. Ver [revalidación de hashes](../h3req1_revalidacion_hashes_2026-10-08.md).
Scanner y scope guard cambiaron localmente y todavía
requieren regresiones, revisión y checks pertinentes dentro de Docker. Snapshot, smoke,
C03 integrado, `GO_LOCAL_PR` y `GO_DEVELOPMENT_REAL` siguen NO-GO.

## Corte histórico posterior a D3/J2/D4/J3/F1 — F2 pendiente, 2026-10-07

El estado inferior corresponde al corte del 2026-10-07 y queda supersedido por la
continuación vigente F2b/F2c/F2d de arriba.

D3 se aprobó y ejecutó una sola vez. El único contenedor nuevo
`h3req1-c03-snapshot-diagnostic-d3-20261007` devolvió el ID
`81c57f0e70538d7430e46a61d745a3b6296fb943980342f2caeead19c0658ebf`; el runner salió
NO-GO/exit 1 en la fase create/start y su inspección de manejo de fallo lo registró
`created`, preservado sin stop/cleanup. No alcanzó el fixture tar; no prueba ownership
ni explica la causa histórica S1. Ver [reconciliación D3](../h3req1_c03_d3_create_start_failure_reconciliation_2026-10-07.md).

J1 de lectura `inspect` fue aprobado/consumido; el parser falló cerrado sin exponer salida.
J2, aprobado/consumido en una lectura separada de `.State.Error`, recuperó la causa D3:
el logging `local` rechazó compresión junto con `max-file=1`. Ver [evidencia J1](../h3req1_c03_snapshot_d3_create_failure_inspect_2026-10-07.md)
y [J2](../h3req1_c03_snapshot_d3_state_error_read_2026-10-07_j2.md). Esto no
explica S1 ni prueba ownership. D4 fue aprobado/consumido una vez; su proceso sintético
devolvió exit 0. J3 confirmó que el único desajuste era la expectativa del runner de hallar
el tmpfs en `.Mounts`, mientras `HostConfig.Tmpfs[/diag]` sí coincidía; por eso el harness
cerró NO-GO, aunque el fixture confirmó su mecanismo. Ver
[reconciliación D4](../h3req1_c03_d4_metadata_mismatch_reconciliation_2026-10-07.md)
y [evidencia J3](../h3req1_c03_d4_metadata_read_2026-10-07_j3.md). El contenedor
quedó `exited`, preservado. D4 usó runner
`785908597840def21e394c11181114d34a349746226a3c058a8bb3426f2f6107`, sidecar
`84b06ba5dcaa3795e1267397d13d57f12aa0b2b5d83b4beca14a9b8fb49b3e4c` y JIT
`fcec517023f4a85e1381ad4b1b2be949fba933596e469293fed28315397a4fba`. Sintaxis y hashes
locales pasaron antes de ejecución; la revisión independiente cubrió solo el delta, no el
runner completo. J3 fue consumido y dejó demostrada la expectativa incorrecta del verificador
sobre `.Mounts`. F1 posterior fue aprobado una vez tras aceptación del residual MEDIUM
same-user, y quedó consumido. El único `docker create` tuvo status 0; la validación de
identidad/controles pre-start devolvió NO-GO, no se llamó a `start` y el recurso
`54d0ad11fb6a7e0b91ffa59538958407e36cee79fc875d8446ac7b1e1bf67dd9` se preserva. El reporte
no identifica el campo discrepante; no inferirlo ni volver a consultar bajo F1. Ver
[reconciliación F1](../h3req1_c03_source_snapshot_f1_prestart_failure_reconciliation_2026-10-07.md).
F2 está preparado como única lectura de metadata allowlisted del ID exacto, pero la auditoría
independiente encontró HIGH: el endpoint Unix podría ser un proxy a remoto, pues F2 no fija
identidad de daemon. También queda MEDIUM por el procesamiento transitorio del objeto completo
de Docker inspect. JIT F2 propuesto/NO-GO, no aprobado y no ejecutado; no se ha consultado
Docker tras F1. Gate siguiente: fijar identidad de daemon local directo, corregir/re-auditar
F2 y luego solicitar aprobación humana separada bajo hash exacto.
D3/D2/S1/D4/J1/J2/J3/F1 permanecen consumidos; no repetir ni consultar R1–R4. Snapshot
completo, smoke Pages/workerd y C03 integrado siguen NO-GO. Ver
[reconciliación F1](../h3req1_c03_source_snapshot_f1_prestart_failure_reconciliation_2026-10-07.md),
[JIT F2](../../operaciones/manifiesto_jit_h3_close03_source_snapshot_f1_metadata_read_2026-10-07_f2.md) y
[revisión estática F2](../h3req1_c03_source_snapshot_f2_static_review_2026-10-07.md).

## 1. Resultado esperado y límites

Dos resultados distintos, sin usar «GO» ambiguo:

- **GO_LOCAL_PR / readiness local para solicitar push/PR:** C03 integrado PASS, checks
  finales del candidato, criterios/pilares/seguridad y paquete PR completo; prerequisitos
  de CI independiente identificados y acreditados según el plan. No equivale a deploy
  ni aceptación remota. Si el bootstrap del control CI exige una operación remota previa,
  pedir esa autorización explícita y no declarar enforcement por un YAML local.
- **GO_DEVELOPMENT_REAL:** candidato integrado/desplegado autorizado, artefactos/config
  verificados y D01–D14 reales PASS o excepciones formalmente aprobadas según plan.
  Certification/Production quedan fuera hasta nuevas instrucciones.

El pedido de resultado no permite inventar un PASS, quitar gates, modificar protecciones,
reutilizar permisos consumidos, resetear cuentas ni adelantar etapas con fallos abiertos.

## 2. Baseline acreditado; no volver a empezar

- Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
  `feat/h3req1-sync-20261002`; baseline HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
  HEAD no identifica los archivos WIP; conservar original y cambios ajenos.
- H3-CLOSE-02 v4 y C03 SQL v3 conservan sus PASS por hashes/alcance. Revalidar solo
  impactos de cambios nuevos; bootstraps necesarios en DB nueva no son nuevos PASS C02.
- R1/R2 fallaron en dependencias Deno; R3 produjo lock compatible; R4 completó bootstrap
  pero agotó healthz en `isolated-workerd-bootstrap`. No alcanzó PG17/PostgREST/SQL.
- D1 no obtuvo causa: falló una comparación literal `.Config.Image`, sin demostrar
  imagen incorrecta. D2 se ejecutó una sola vez bajo JIT exacto: R4 `exited`, exit 1,
  `OOMKilled=false`, `log-driver=none`; no obtuvo causa porque los logs históricos no
  existen. Evidencia y SHA están en [estado vivo](../../estado_del_proyecto.md).
- Revisión que originó esta ruta: sesión `ses_ef0cce873ffe3X1100DbM8XxSw`, final
  `msg_1120890a5001Y5qRhq0CizLIfR`; 5/5 inputs D2 coincidentes, hash manifiesto
  `6f6f4e451e45dec30c8145b2bb328286786aaf36d887635ae0be14f5e4547e6c`;
  en aquel corte el resultado D2 no existía.

**Corte pre-D3 EXEC-01 — 2026-10-07 (histórico):** D2 y S1 están aprobados/consumidos, no pendientes.
D2 no determinó causa del healthz de R4. S1 intentó reproducir el arranque, pero falló
antes en `create-new-source-snapshot`, exit 2; no alcanzó npm ni workerd. La causa exacta
no quedó registrada porque se suprimió stdout/stderr de esa fase. Ver [evidencia S1](../h3req1_c03_startup_smoke_2026-10-07_s1.md).
NO-GO sigue vigente. R4 manifest es histórico: el runtime actualizado requiere un cierre
full nuevo y JIT independiente para C03; no ejecutar R4/D2/S1 de nuevo por este documento.

### D3 planeado antes de su ejecución — corte histórico; JIT consumido

La preparación y los pasos que siguen describen cortes pre-ejecución. D3 ya se ejecutó
y terminó NO-GO antes del fixture tar; J1/J2 posteriores recuperaron la causa de su logging.
D4 también se ejecutó y terminó NO-GO por discrepancia de identidad/controles tras un
`wait` con exit 0. El gate vigente es aprobación separada del JIT J3 de lectura metadata
descrito al inicio de esta nota.

Hipótesis estática prioritaria, **no causa confirmada**: `tar -xf` intenta restaurar
propietarios UID/GID 1000 dentro de un contenedor con `--cap-drop=ALL`; no se usa
`--no-same-owner`. Tres inputs inspeccionados tienen ownership 1000:1000 y modo 644.
El pipeline devuelve exit 2 y suprime toda salida, por lo que también deben distinguirse
otras causas: productor tar, receptor tar, permisos/espacio y validación de hashes.

Preparación local permitida para el próximo ciclo:

1. Examinar estáticamente `tests/h3req1_c03_startup_smoke_s1.sh:294–313` y manifiestos.
   Mantener S1 y su evidencia como artefactos consumidos; escribir candidato diagnóstico
   nuevo, sin reemplazar hashes de permisos anteriores ni hacer un retry encubierto.
2. Diseñar una reproducción solo del snapshot en recursos nuevos aislados y sin red.
   Empezar con fixture mínimo de contenido público/sintético y propietario 1000, no
   `.env*` ni secretos; probar ownership sin añadir capacidades o privilegiar el contenedor.
   Si confirma la hipótesis, probar extracción sin restaurar propietario, preservando
   controles de symlink/rutas, hashes, permisos necesarios y fuente read-only.
3. Registrar fases y exit codes independientes de productor/receptor; errores sanitizados
   acotados desde origen, sin volcar contenido de fuentes ni secretos. No ocultar todos
   los errores con `/dev/null`. Definir límites RAM/CPU/tiempo/espacio, operación de stop
   solo del recurso nuevo si se autoriza y conservación ante FAIL.
4. Cerrar inputs/hashes/imágenes/comandos/recursos y revisar antes de presentar JIT.
   Declarar si se autorizan dos casos acotados comparativos o un caso corregido y por qué;
   ningún retry ilimitado. No inspeccionar ni montar recursos S1/R1–R4 consumidos.
5. Presentar un JIT diagnóstico NUEVO exacto. No está aprobado por `continua`: esperar
   permiso humano para crear/ejecutar/inspeccionar recursos. No incluir npm, workerd,
   SQL/DB/PostgREST/Edge/Auth, correo, remoto, cleanup ni caches históricos.
6. Tras ejecución autorizada, causa demostrada o evidencia que descarte hipótesis. Si la
   corrección pasa el mínimo, comprobar el snapshot completo con manifiesto fuente bajo
   permiso explícito y luego smoke Pages/workerd en un nuevo cierre/JIT. No reclamar
   smoke PASS por un tar PASS ni integración PASS por smoke PASS.

Un manifiesto JIT ejecutable solo se entrega después de construir y verificar el runner
real. Esta preparación documental no inventa hashes, nombres aprobados ni permisos.
Si aparece un fallo distinto, explicar evidencia y pedir un alcance diagnóstico suficiente,
sin repetir el ensayo completo ni reiniciar el plan.

## 3. Tareas ejecutables y gates

Owner técnico: agente build del próximo ciclo. Owner de decisiones/JIT/aceptación:
responsable humano. Revisión independiente: security-auditor conforme AGENTS.

### EXEC-01 — diagnóstico que produzca una decisión, no otro timeout opaco

1. Leer estado/plan/atestación y esta ruta; listar tareas y gates una sola vez al inicio.
   Confirmar candidato/branch/hash y evidencias locales sin tocar recursos protegidos.
2. Examinar estáticamente runner/runtime: comando/entrypoint, directorios y mounts,
   usuario/permisos, dependencias, arquitectura, binding/puerto healthz, TLS y readiness.
   Formular hipótesis verificables; no afirmar causa raíz por intuición.
3. Elegir el menor diagnóstico suficiente. D2 es una opción acotada, no obligatorio:
   explicar qué decisión permite y qué no. Si hace falta más acceso, presentar desde
   ahora un alcance diagnóstico coherente, en lugar de pedir un permiso por cada campo.
4. Solicitar autorización exacta con inputs/hashes, recurso R4 por nombre/identidad,
   operaciones allowlisted, campos/rutas, salida sanitizada, tiempo y efectos. Inspección
   adicional, logs, exec, mounts de caches o redes no se heredan de D2/R4/D1. No leer
   `.env*`, credenciales, sesiones reales ni payloads de firma. No cleanup/restart implícito.
5. Si `log-driver none` impide recuperar salida histórica, reconocer esa limitación.
   Proponer reproducción mínima NUEVA y autorizada con logging sanitizado desde origen,
   sin DB/SQL ni servicios remotos, para capturar el error de arranque. No prometer logs
   inexistentes ni suprimir toda la salida útil por seguridad.

**Gate EXEC-01:** causa/hypótesis con evidencia suficiente para una corrección concreta;
si no, bloqueo explicado y alcance adicional preciso. Un listado de metadata no es PASS
de arranque. Conservar R1–R4/D1 y no cambiar retrospectivamente artefactos consumidos.

### EXEC-02 — corregir y probar únicamente el arranque del runtime

1. Implementar la corrección local de tooling/fixture dentro del alcance permitido.
   Si cambia producto o criterio cliente, detenerse por drift. SQL/grants mantiene JIT.
2. Añadir diagnósticos sanitizados: fase, readiness, exit code, clasificación de error y
   motivo recuperable; nunca JWT/HMAC/keys. Limitar espera, CPU/RAM/procesos cuando sea
   viable; declarar riesgo de volúmenes/disco y egress residual que necesite aceptación.
3. No comparar identidad real de imagen solo con el texto `.Config.Image`; comprobar
   ID/digest/plataforma con método documentado y operaciones expresamente autorizadas.
4. Preparar smoke de runtime real con recursos nuevos, dependencias fijadas y acceso
   externo bloqueado tras bootstrap. No DB, SQL, Auth real ni correo. Revisión estática,
   hashes y auditoría antes de pedir el JIT de ejecución correspondiente.
5. Pedir permiso exacto para ese smoke: recursos/comandos/duración/logs/efectos y qué
   reintentos acotados, si alguno, incluye. Sin autorización explícita no hay retry.

**Gate EXEC-02:** runtime arranca, healthz responde y smoke real de Pages/workerd pasa;
evidencia reproducible/códigos y diagnósticos disponibles ante FAIL. Este smoke NO cierra
C03, pero evita repetir bootstrap+drill completo cuando el runtime aún no funciona.

### EXEC-03 — ejecutar C03 integrado hasta resultado verificable

1. Incorporar la corrección comprobada a un candidato nuevo del runner; cerrar hashes
   transitivos, imágenes/lockfiles/config/fixtures. No incluir caches históricos a ciegas.
2. Revisión independiente y gates estáticos; presentar JIT integrado exacto para recursos
   nuevos, SQL sintético/ACL/rollback/resume y runtimes. Definir evidencias, salida segura,
   timeout, stop-on-failure y recuperación; cleanup separado salvo autorización explícita.
3. Tras permiso y señal de ciclo, ejecutar: normal -> operación previa reservada ->
   suspensión coordinada -> nuevos iniciadores/dispatcher rechazados -> cookies expiradas
   -> finalizadores in-flight completan una sola vez -> datos/auditoría/publicación y
   último admin preservados -> resume persistente validado -> Edge -> Pages -> smoke.
4. Comprobar cuotas/admission y nonce según protocolo; documentar evento sintético de cuota
   permitido sin confundirlo con nueva invitación. Rechazo de drift mantiene suspensión.
5. PG17/PostgREST, Pages/workerd y Edge Runtime deben ser reales locales; Auth externo
   puede seguir fixture explícito, sin correo. No declarar integración real por VM Edge.

**Gate EXEC-03:** matriz completa PASS con inputs/resultados recuperables; ningún caso
obligatorio omitido. Ante FAIL corregir/revalidar por impacto y renovar JIT cuando cambien
bytes protegidos. No cerrar por cantidad de intentos, auditorías estáticas o agotamiento.

### EXEC-04 — terminar el candidato para PR, sin otra preparación indefinida

Después de C03 PASS, ejecutar los pendientes H3-CLOSE-01/04–06 del plan único:
inventario PR, mantenimiento/owners/skips, actionlint/shellcheck, build/typecheck/lint,
Python y contratos, UAT/onboarding/compatibilidad Auth+MFA del artefacto final, revisión
independiente y criterios cliente/pilares. Todo comando de desarrollo dentro de Docker.
Usar los comandos/runners actuales del plan y registrar conteos reales, no heredados.

Separar manifiestos de fuentes/build/resultados. Revisar ausencia de HIGH/CRITICAL;
waivers requieren evidencia, owner, riesgo, vencimiento y aceptación humana. No ocultar
warnings o skips. Acreditar el control CI obligatorio efectivo con las autorizaciones
remotas necesarias; no emprender rediseño general de gobierno. Completar plantilla PR
versionada con checks ejecutados, pendientes explícitos y trazabilidad sanitizada.

**Gate EXEC-04:** checklist local y prerequisitos del PR completos; entregar veredicto
GO_LOCAL_PR acotado o bloqueos enumerados. No afirmar Development GO en esta etapa.
Pedir autorización para operaciones Git pertinentes; no hacer commit/push/PR implícitos.

### EXEC-05 — PR e integración Development autorizados

Con permiso exacto: push/PR protegido a desarrollo; vincularlo a la sesión al conocerlo.
CI independiente y review humano según protección; resolver findings. Merge requiere
instrucción separada. Verificar SHA integrado, no asumir que HEAD baseline/WIP es candidato.
Planificar secuencia expand compatible -> servicios/frontend -> contract tras estabilidad,
con rollback real y ventanas/fixtures. DB/Edge/Cloudflare/secretos/Auth/deploy/workflow_dispatch
requieren sus permisos separados, ambiente Free correcto y host Development no productivo.

**Gate EXEC-05:** artefacto y contratos/config desplegados coinciden con manifiestos;
perímetro y compatibilidad operativos; autorización de ventana UAT y rollback disponible.

### EXEC-06 — cerrar con pruebas remotas D01–D14

Ejecutar la matriz literal del plan único sobre Development real: cuentas existentes
sin reset/reinvitar/reenrolar, onboarding separado, RBAC/MFA/último admin, edición,
locking/publicación/auditoría, cuotas/perímetro y recuperación. Registrar SHA/host/
deployment/schema/Edge/Worker/config y evidencia sanitizada; no usar la matriz local
como sustituto. Corregir y repetir casos afectados con permisos correspondientes.

**Gate EXEC-06:** GO_DEVELOPMENT_REAL solo con matriz/criterios/pilares y evidencia
canónica completos, sin bloqueantes. Detenerse y pedir promoción separada; nunca ejecutar
Certification/Production por este prompt.

## 4. Reglas para evitar más vueltas

- No repetir lectura exhaustiva, SQL PASS o redacción de planes por pérdida de contexto;
  usar evidencia canónica vigente, comprobar hashes y ejecutar el siguiente gate autorizado.
- No reintentar el drill completo para averiguar si un runtime arranca.
- No pedir un «continua» adicional para cada read/edit dentro de un ciclo ya autorizado;
  sí respetar señal de ciclo cuando corresponda y JIT separado de operaciones protegidas.
- Preparar permisos por objetivo coherente con lista exacta de operaciones/retries y
  límites, no autorizaciones vagas ni grants perpetuos. Un alcance más útil necesita
  aprobación humana; no expandir silenciosamente un permiso estrecho.
- Cada ciclo termina con: ejecutado/resultados, FAIL y causa demostrada o hipótesis,
  archivos/hash afectados, permiso consumido, gate siguiente y UNA decisión concreta.
- Readiness, sintaxis, hashes y revisión no prueban runtime. No declarar GO por intención.

## 5. Prompt vinculante de continuación operativa

Validación de esta edición exclusivamente documental: cinco notas conectadas, 103 destinos
locales existentes, fences/newlines balanceados y `git diff --check` PASS. No se validaron
anchors/URLs externas/render Obsidian ni se ejecutaron suites, Docker o servicios; no hay
cambios funcionales a validar en contenedor en este ciclo. Estos checks no modifican NO-GO.

```text
continua con H3REQ1 en /home/romel/src/studiamatch-h3req1-sync-20261002,
rama feat/h3req1-sync-20261002. Trabaja en build, no en plan.
Lee AGENTS.md, .context/estado_del_proyecto.md, atestación cliente, plan único y
.context/evidencia/planes_historicos/h3req1_ruta_ejecutable_go_pr_y_remoto_2026-10-06.md.
Lee `.context/indice.md` y `protocolo_constructor.md`, localiza la asignación en el registro y presenta ficha de impacto antes de
editar: consumidores/contratos, pruebas, evidencia preservada/a renovar y permisos.
Usa su corte 2026-10-07 y evidencia S1. Lista tareas/gates y avanza lo autorizado;
no redactes otro plan equivalente ni repitas D2/S1/R4 consumidos.
Objetivo: snapshot PASS -> smoke workerd PASS -> C03 integrado PASS -> GO_LOCAL_PR;
después PR/integración/despliegue y D01–D14 para GO_DEVELOPMENT_REAL con permisos.
Preserva C02 v4/C03 SQL v3 por hashes/alcance. D2 ya se ejecutó y no obtuvo causa.
S1 falló create-new-source-snapshot exit 2 ANTES de npm/workerd. No sabemos aún
por qué. La extracción tar restaura ownership 1000 con cap-drop ALL; es hipótesis,
no causa demostrada. No afirmes que el producto o el runtime fallaron en S1.
Examina estáticamente el pipeline y prepara runner/manifiesto nuevos de diagnóstico
solo del snapshot. Reproduce con fixture mínimo público/sintético en Docker aislado,
sin red, secrets ni recursos anteriores; registra productor/receptor y errores
sanitizados acotados. Comprueba ownership sin elevar privilegios ni quitar controles.
Cierra hashes/imágenes/comandos/recursos/límites y revisión; presenta JIT nuevo exacto.
Espera mi aprobación antes de ejecutar. Incluye casos/retries acotados explícitos,
stop/conservación y exclusiones. No ejecutes inspect/logs/exec/mounts protegidos sin JIT.
Tras causa/corrección comprobada, valida snapshot completo bajo alcance aprobado,
luego smoke real Pages/workerd con manifiesto/JIT nuevo. Solo tras smoke PASS ejecuta
C03 integrado autorizado: cookies, dispatcher, in-flight, datos/auditoría y recuperación.
R4 es histórico y ya no cierra el runtime actualizado: recalcula el manifiesto full.
Tras C03 PASS termina candidato, tooling/ShellCheck, Docker checks/build/UAT final,
revisión, cliente/pilares, CI efectivo y manifiestos. Completa plantilla PR con resultados.
Incluye capa documental global solicitada; comprueba scope guard antes del PR y el
scanner oficial válido/fallo cerrado documentado en la evidencia de trazabilidad.
No pares en runner listo ni declares GO con gates pendientes. Pide push/PR, merge,
configuración y deploy por separado; vincula issues/PRs trabajados a la sesión.
Este continua autoriza autoría local permitida, no SQL/grants, diagnóstico/recursos
Docker protegidos, retries, rollback/resume/cleanup, secretos, Auth/reset, remotos,
protección, workflow_dispatch, commit/push/PR/merge/deploy. Espera permisos exactos.
Usa Docker para desarrollo; preserva original/WIP/evidencia/recursos y Auth+MFA
sin reinvitar/reenrolar. Corrige/revalida por impacto y actualiza Obsidian conectado.
Cierra cada ciclo con resultados, causa o hipótesis, permiso consumido y UNA decisión
siguiente en lenguaje sencillo. No inventes GO ni cambies gates; detente ante drift
o falta de aprobación. No ejecutes Certification/Production.
```

Referencias: [estado vivo](../../estado_del_proyecto.md),
[plan único H3-CLOSE-01–08 y D01–D14](../../operaciones/plan_cierre_integral_h3req1_2026-10-04.md),
[JIT S1 de arranque Pages/workerd](../../operaciones/manifiesto_jit_h3_close03_startup_smoke_2026-10-06_s1.md),
[resultado S1](../h3req1_c03_startup_smoke_2026-10-07_s1.md),
[protocolo y cronología](../h3req1_c03_integrated_protocol_preflight_2026-10-05.md),
[log R4](../h3req1_c03_integrated_run_2026-10-06_r4.log),
[avance PR/remoto](../../seguimiento/h3req1_estado_pr_y_remoto_2026-10-05.md),
[traspaso](../../seguimiento/h3req1_traspaso_avance_y_proximo_ciclo_2026-10-04.md).
