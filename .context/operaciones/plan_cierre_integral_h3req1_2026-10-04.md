# H3REQ1 — plan único de cierre: Development real, Certificación y Producción

> **Archivo histórico.** Este plan describe el corte de cierre H3REQ1 de octubre de 2026 y se conserva porque tareas, pruebas y reportes lo citan como contrato histórico. El cierre local posterior y su evidencia delimitan el resultado; el estado operativo vigente y el índice principal gobiernan la continuación. Este documento no habilita ejecución, promoción ni acceso remoto.

## Actualización de estado posterior a D3/J2/D4/J3/F1 — F2 pendiente, 2026-10-07

D3 fue aprobado y ejecutado una vez; falló en la creación/inicio del contenedor sintético
antes de tar, sin demostrar la hipótesis de ownership ni alcanzar snapshot/npm/workerd.
El recurso con ID `81c57f0e70538d7430e46a61d745a3b6296fb943980342f2caeead19c0658ebf`
permanece preservado en estado `created`; no hubo stop/cleanup ni retry. El JIT D3
aprobado y la evidencia original se preservan sin modificación; ver la
[reconciliación](../evidencia/h3req1_c03_d3_create_start_failure_reconciliation_2026-10-07.md)
y la [ruta vigente en el corte 2026-10-08, ahora archivada](../evidencia/planes_historicos/h3req1_ruta_ejecutable_go_pr_y_remoto_2026-10-06.md). La línea de
estado “S1 JIT pendiente” del encabezado histórico siguiente corresponde al corte previo,
no al estado actual. J1 falló cerrado sin exponer salida; J2 fue aprobado/consumido y
demostró que Docker rechazó el logging `local` por compresión habilitada con `max-file=1`.
Ver [evidencia J1](../evidencia/h3req1_c03_snapshot_d3_create_failure_inspect_2026-10-07.md)
y [J2](../evidencia/h3req1_c03_snapshot_d3_state_error_read_2026-10-07_j2.md). Esto no
explica S1 ni prueba ownership. D4 se ejecutó una vez con logging `compress=false` y límites
de 1 MiB/1 archivo; runner SHA-256
`785908597840def21e394c11181114d34a349746226a3c058a8bb3426f2f6107`, sidecar
`84b06ba5dcaa3795e1267397d13d57f12aa0b2b5d83b4beca14a9b8fb49b3e4c`, JIT SHA-256
`fcec517023f4a85e1381ad4b1b2be949fba933596e469293fed28315397a4fba`. `docker wait`
indicó exit 0; el harness falló su verificación porque esperaba el tmpfs dentro de
`.Mounts`, mientras `HostConfig.Tmpfs[/diag]` coincidió. J3 confirmó que ese era el único
desajuste; el fixture sintético confirmó el mecanismo, pero el harness conserva NO-GO.
El recurso quedó exited/preservado. Ver [reconciliación D4](../evidencia/h3req1_c03_d4_metadata_mismatch_reconciliation_2026-10-07.md)
y [J3](../evidencia/h3req1_c03_d4_metadata_read_2026-10-07_j3.md). F1 se aprobó/consumió una
vez tras aceptación del waiver MEDIUM same-user. `docker create` devolvió status 0, pero la
validación pre-start terminó NO-GO; no se llamó `start`, y no hubo stop/remove/retry. ID
preservado `54d0ad11fb6a7e0b91ffa59538958407e36cee79fc875d8446ac7b1e1bf67dd9`; el reporte no
identifica el campo discrepante. F1 no es PASS de snapshot ni explica S1/ownership. Ver
[reconciliación F1](../evidencia/h3req1_c03_source_snapshot_f1_prestart_failure_reconciliation_2026-10-07.md).
F2 propone una sola lectura read-only allowlisted de metadata de ese ID, pero revisión
independiente detectó HIGH: un endpoint Unix puede ser proxy a remoto y no se fija identidad
de daemon; queda MEDIUM por el procesamiento transitorio del objeto inspect completo. F2 es
NO-GO, no aprobado ni ejecutado y no se volvió a consultar Docker. El siguiente gate es
establecer daemon local directo, corregir/re-auditar F2 y luego solicitar aprobación exacta,
sin reusar permisos/recursos D3, S1, D4, J3 o F1. Ver
[JIT F2](manifiesto_jit_h3_close03_source_snapshot_f1_metadata_read_2026-10-07_f2.md) y
[revisión F2](../evidencia/h3req1_c03_source_snapshot_f2_static_review_2026-10-07.md).
C03 integrado y Development real permanecen NO-GO.

## R1/R2 fallidos; resolver R3 PASS; R4/D1/D2 NO-GO; S1 JIT pendiente — 2026-10-06

El JIT R1 fue aprobado y ejecutado con el manifiesto SHA-256
`a1073d93d22b8c01ed0e41031e4c1f41df33848eac1ff31935b223c80f47e101` (62/62). Snapshot y
bootstrap npm finalizaron; el bootstrap Deno Edge falló con exit 1. No se alcanzaron runtime,
PostgREST, PG17 ni SQL; los recursos/caches r3 se preservan y no se reutilizan ni limpian.
R2 fue preparado y ejecutado bajo JIT aprobado
`H3-CLOSE-03-INTEGRATED-2026-10-06-R2` con manifiesto SHA-256
`0e1634876956d8031ac99057dfc14936f65896b7a0d4626b642bfe8c4239aa11` (62/62). Snapshot y npm
completaron, pero Deno Edge falló con exit 1 y resumen `lockfile-resolution-failure`; la causa
exacta no quedó disponible. No se alcanzaron runtime, PostgREST, PG17 ni SQL. Los recursos y
caches r3/r4 se preservan, sin cleanup/reuso. El resolver R3 fue aprobado/consumido con
manifiesto `60805a1aca0dd3fbd96aeabe2f18a3a6c3efa6df8cafccaf184a66cfb92334f0` (4/4); lock v4 SHA-256
`ccb3d17f01947e679fb530ba7cbc9d252263ab1051d1d9ab21429eecde7ba428`. El candidato integrado
R4 incorporaba ese lock y config limpia: manifiesto histórico de 62 inputs SHA-256
`e5d72e06b04fcfd3f68abaeea77fef81c982f24e20e587732de65b63b58167a7`; gates finales
`bash -n`, `diff --check`, `sha256sum -c` 62/62 y auditoría sin HIGH/CRITICAL/blockers.
El LOW de señales se mitigó; permanece el MEDIUM aceptado por JIT. El JIT
`H3-CLOSE-03-INTEGRATED-2026-10-06-R4` fue aprobado/consumido. Los bootstraps y el digest de
dependencias pasaron, pero el runtime agotó 60 intentos de `healthz` en `isolated-workerd-bootstrap`
(exit 1; NO-GO, causa raíz indeterminada). No se alcanzaron PG17, PostgREST, user worker ni SQL.
Recursos R4 creados y log quedan preservados, sin cleanup ni resume. El JIT D1
`H3-CLOSE-03-INTEGRATED-DIAGNOSTIC-2026-10-06-D1` fue aprobado/consumido con manifest SHA-256
`19618493b6ecc5148dd6320a8c915f97563b3d79eea57507950b08928c38a914`. El inspect limitado
rechazó `.Config.Image` al no coincidir con el string digest esperado; la metadata se suprimió,
así que no se confirma discrepancia real de imagen vs normalización del valor. D1 exit 1/NO-GO,
sin estado/OOM/código ni causa del timeout. Reporte SHA-256
`82cda545f327eb721fb1442ba91f962b5b3eb4b4e50a2a86e0c2e175f5a85347`. `log-driver none` impide
leer logs de servicio; cualquier inspect adicional, cambio al guard o retry requiere JIT nuevo.
Cache/volumen R3 no se montó; recursos R1/R2 no se
inspeccionaron. No volver a acceder a `tests/h3req1-c03-bootstrap/node_modules/.deno` debido a
la salvedad documentada del auditor. C02 v4 y C03 SQL v3 no se repiten. Ver el
[protocolo de evidencia R1–R4](../evidencia/h3req1_c03_integrated_protocol_preflight_2026-10-05.md).

D2 se preparó estáticamente con runner/manifiesto nuevos, SHA-256
`f337ed07de258c632c1cfcfa9f6292f8b1f19389bb06112fc5f8bec192e96447` /
`6f6f4e451e45dec30c8145b2bb328286786aaf36d887635ae0be14f5e4547e6c`; evita consultar
`.Config.Image` y se limita a metadata de estado/exit/OOM/log-driver. La auditoría inicial señaló
LOW por falta de guard symlink en `tests/`; se corrigió. La reauditoría cerró el LOW técnico y
halló LOW documental por estado obsoleto, luego remediado. Ese corte pre-JIT tuvo gates
`bash -n`, `diff --check` y hashes 5/5 PASS. Después D2 se aprobó/consumió una sola vez: runtime
`exited`, exit 1, `OOMKilled=false`, `log-driver=none`; no resolvió la causa. Ver resultado/hash en
[estado vivo](../estado_del_proyecto.md). Se preparó el JIT independiente S1 para reproducir
el bootstrap Pages/workerd; queda pendiente su reauditoría final y JIT. El modo diagnóstico
actualizado no cambia C02 v4 ni C03 SQL v3; el manifiesto R4 queda histórico e intacto, pero ya no
valida el runtime editado. No ejecutar Docker sin JIT S1 exacto. Si S1 pasa, C03 integrado
requiere manifiesto full nuevo y JIT propio; no se reutiliza R4.

Fecha: 2026-10-04. Naturaleza: traspaso documental solicitado por el responsable humano.
Estado: **NO-GO vigente; este documento no acredita ejecución ni concede permisos**.

## Navegación del corte histórico del 2026-10-08

Para el contexto histórico de la ejecución siguiente en ese corte, consultar [ruta EXEC-01–06 vigente entonces, archivada como historia](../evidencia/planes_historicos/h3req1_ruta_ejecutable_go_pr_y_remoto_2026-10-06.md),
que operacionaliza este plan sin reemplazar D01–D14 ni gates/aprobaciones. Los prompts
anteriores son cortes históricos; no repetir el bootstrap ya superado ni el drill
antes de conseguir arranque real comprobado. NO-GO actual permanece.
D2 se ejecutó una vez y no identificó causa; logs R4 no recuperables. El alcance exacto
pendiente es el [JIT S1 Pages/workerd](manifiesto_jit_h3_close03_startup_smoke_2026-10-06_s1.md).

Ver [contraste de última sesión, estado PR/remoto y siguiente secuencia](../seguimiento/h3req1_estado_pr_y_remoto_2026-10-05.md).
No hay PR abierto hacia desarrollo en esta revisión; falta C03 integrado antes de la
validación final y readiness. C03 SQL v3 PASS no autoriza integración ni pruebas remotas.

Ver el [traspaso de avance y próximo ciclo](../seguimiento/h3req1_traspaso_avance_y_proximo_ciclo_2026-10-04.md),
[evidencia actual](../evidencia/h3req1_development_candidate_cycle_2026-10-04.md),
[tarea](../backlog_tareas/req_est_001_sprint_1/tarea_003_hito_3.md) y
[mapa documental](../seguimiento/mapa_documental_obsidian_2026-10-04.md).
Gateway payload-bound/guard NULL y remediación local de cardinalidad de cuotas implementados;
Docker pytest 287 PASS/4 skips registrados. **H3-CLOSE-02 PASS local** bajo
[JIT v4 consumido](manifiesto_jit_pg17_postgrest_h3req1_2026-10-05_v4.md): PG17,
replay, PostgREST HTTP/SDK, assert SQL y concurrencia. El permiso MEDIUM de egress
npm se aceptó para el bootstrap v2 y expiró al finalizar; no está pendiente ni habilita
instalaciones nuevas. El [safe-suspend SQL actualizado también pasó](manifiesto_jit_h3_close03_safe_suspend_pg17_2026-10-05_v2.md)
bajo su JIT propio v2. **Siguiente: H3-CLOSE-03 integrado y recuperación operativa**,
seguido de mantenimiento, CI efectivo, validación final e integración/aceptación remota.
No usar hashes/permisos de «sexto JIT» ni repetir v4/v2 consumidos.
Las tareas H3-CLOSE-01–08 son la secuencia vinculada, no ocho GO independientes.

## 1. Cómo debe usar este plan un modelo desarrollador

La autoridad viva continúa siendo [Estado Del Proyecto](../estado_del_proyecto.md).
Este fue el plan único de continuación para H3REQ1 en su corte original. Consolida los pendientes
del [plan anterior archivado](../evidencia/planes_historicos/plan_go_h3req1_local_development_2026-10-02.md) y extiende la hoja
de ruta hasta Certification, Production y contracción. El plan anterior y los cortes
fallidos se conservan como historia; sus pendientes resueltos no deben reaparecer
como trabajo nuevo. La extensión documental no autoriza ejecutar esas promociones.

El primer objetivo ejecutable de una continuación humana es **GO Development real**,
no un GO por componente, un PR abierto ni un PASS mock. Después debe detenerse antes
de Certification y pedir instrucción humana separada. Lo mismo rige antes de Production.

Antes de editar, el desarrollador debe listar tareas concretas y gates; comprobar
baseline, scope, archivos ajenos y evidencia; recibir `continua` para el ciclo funcional.
Trabajar por ciclos analizar -> implementar -> validar -> revisar -> convertir
hallazgos en tareas -> corregir -> revalidar. No detener la entrega al resolver un
hallazgo aislado: continuar el conjunto salvo gate fallido, drift o aprobación necesaria.

No confundir tres hechos:

1. Hay implementación y pruebas históricas válidas.
2. El candidato nuevo requiere validar sus propios cambios y su transición.
3. Una aprobación local, un diseño aprobado o `continua` NO autorizan SQL, Auth,
   secretos, backup/restore, cambios protegidos, push, PR, merge, deploy, rollback,
   `workflow_dispatch`, schedules ni writers. Pedir JIT separado por operación.

Si la fuente cliente o la atestación sanitizada no cubren un cambio, detenerlo y
consultar. No acceder ni reproducir la fuente privada en evidencia/PR. No ampliar
roles, negocio, onboarding, umbrales o arquitectura por iniciativa propia.

## 2. Baseline verificado y comparación de los tres árboles

La revisión del 2026-10-04 fue read-only: Git local, refs remotos, PR #500/checks y
documentación/código. No repitió suites funcionales ni inspeccionó el estado actual
de DB, Auth o Cloudflare. Los estados remotos de esas plataformas deben revalidarse
mediante lectura expresamente autorizada antes de operarlas.

| Árbol/ref | Corte comprobado | Decisión para continuar |
|---|---|---|
| GitHub `desarrollo` | `4eb4d877a50b012bb630a129bd0c74482c33be9c`, PR #500 mergeado; check `security-audit` y los checks consultados del head del PR en success | Baseline de integración; CI verde histórico no demuestra protección independiente ni valida WIP |
| `/home/romel/src/studiamatch` | `feat/h3req1-development-remote-tests`, HEAD `7650093b05a820e8e6faf9ec711e12fab8b50398`, WIP y evidencia histórica | Preservar; no desarrollar ni trasladar archivos completos automáticamente desde aquí |
| `/home/romel/src/studiamatch-h3req1-sync-20261002` | `feat/h3req1-sync-20261002`, HEAD igual al último `desarrollo`, cambios sin commit | Candidato de trabajo; HEAD identifica baseline, NO identifica sus bytes modificados |
| GitHub `certificacion` | `c80f6504a3ea353bc2c222df1da09c4b5ba0ae58` | Snapshot; refrescar antes de su promoción |
| GitHub `main` | `70d0f4fee885be0f6780e5d14f466b2a6c897961` | Snapshot; refrescar antes de Production |

El worktree conserva páginas Admin iguales a las del WIP original, pero difiere en
BFF/middleware, transporte Supabase, Edge, workflows, pruebas y dependencias.
Añade cuotas, Worker privado, rollback seguro y harnesses. No es una mera copia del
checkout antiguo ni un artefacto ya integrado a `desarrollo`.

Preservar reportes remotos e históricos. Excluir estado personal/local (`.openchamber`,
`.obsidian`, `.codex`, `supabase/.temp`), secretos, resultados temporales y los dos
archivos de 0 bytes con nombres literales de plantillas. Excluir NO significa borrar.
Clasificar evidencia versionable por pertinencia y sanitización, no por volumen.
No usar el contenido prellenado de la plantilla PR como resultados actuales.

## 3. Qué está probado y qué no se debe reabrir

| Evidencia | Alcance acreditado | Límite de reutilización |
|---|---|---|
| [Ciclo remoto Development](../evidencia/h3req1_development_remote_cycle_2026-09-26.md), sección `MFA aal2 y operación sensible confirmadas`, 2026-09-27T03:55:45Z | Login, challenge/verify TOTP 200, cola/conteo RPC protegidos 200, panel visible | **Auth+MFA real PASS**, no volver a marcar todo Auth pendiente; no acredita BFF nuevo, refresh/logout ni todas las mutaciones |
| PR #500, `https://github.com/romelhc95/studiamatch/pull/500` | Integración UX y checks verdes del head `37303c07f39511f2b6b40fe1787ddd6aac24adb9`; merge `4eb4d87` | No acredita WIP BFF/cuotas; body conserva estados históricos previos al merge |
| [Readiness 2026-10-03](../evidencia/h3req1_readiness_continuation_2026-10-03.md) | Pytest 283 PASS/4 skips, tooling PASS, lint 0 errores/9 warnings; audit completo/prod 0; snapshot braces 904 tests | Resultados reportados, no reejecutados en el traspaso; fuentes finales no congeladas |
| UAT local r17 y onboarding descritos en readiness/estado | 48/48 casos, 144/144 ejecuciones/capturas, 0 retries; onboarding 10/10 | Local, no correo/Auth real nuevo; cambios posteriores del gateway invalidarán gates afectados |
| Cadena PG17/DO/PostgREST y safe-suspend descritos en [ciclo BFF](../evidencia/h3req1_bff_local_cycle_2026-10-02.md) y estado | Pruebas locales de cadenas y componentes; suspensión SQL, Pages y Edge por separado | No equivalen a metadata remota completa ni al rollback integrado |

Los fallos r8/r10 y previos se conservan, pero r17 posterior no debe ignorarse.
Repetir pruebas por impacto demostrado, no para borrar la historia. No copiar cifras
de suites previas como resultado del nuevo candidato.

El plan/hito histórico excluyó MFA como nuevo criterio contractual. La adenda BFF
posterior exige **conservar MFA existente**. No inventar requisito comercial nuevo:
la transición del transporte debe probar no regresión de MFA/aal2 y los RPCs sensibles.
La [atestación sanitizada](../evidencias_cliente/sprint_1/atestado_aceptacion_plan_ingesta_editorial_auditoria_2026-10-01.md)
incluye destinos JWT acotados adicionales Auth/MFA/Edge. No volver a la excepción
antigua exclusivamente RPC ni ampliarla a destinos arbitrarios.

## 4. Definiciones de salida, sin circularidad

| Gate | Qué significa | Qué NO significa |
|---|---|---|
| R — Ready para PR/pruebas | Candidato local exacto validado, revisión/aceptación/pilares, rollback local integrado, CI confiable efectivo y protocolo remoto listo | No exige que los checks de un PR aún no abierto o la UAT remota aún no autorizada ya hayan pasado |
| D — GO Development real | SHA integrado, despliegue real Free/Development identificado, UAT contractual y transición/rollback remotos aceptados, hallazgos cerrados | No equivale a GO Certification/Production |
| C — GO Certification | Promoción protegida y aceptación sobre deployment/hostname Certification exactos, con evidencia de regresión y rollback | No habilita writes/deploy de Pro ni merge a main |
| P — GO Production y cierre | Pro preparado compatible, main promovido, runtime productivo verificado, estabilidad y contract completados, cierre cliente/pilares documentado | Un deployment success sin aceptación ni contract no cierra H3REQ1 |

No HIGH/CRITICAL abiertos en el alcance de salida, ni pendientes bloqueantes ocultos.
No waivers implícitos. Cualquier waiver requiere causa, evidencia reproducible, owner,
riesgo, vencimiento y aprobación humana; no sustituye aceptación contractual obligatoria.

## 5. Backlog ejecutable hasta GO Development real

### H3-CLOSE-01 — Preflight, alcance y paquete candidato

Responsable funcional: desarrollador; decisiones de alcance: responsable humano.

- Releer AGENTS del worktree, estado, este plan y atestaciones antes de editar.
- Confirmar status, refs, merge-base y diff; identificar cambios posteriores al corte.
  Si el baseline o el alcance cambió, presentar delta y pedir decisión, sin rebase automático.
- Revisar respaldo recuperable del WIP original y preparar manifiesto de incluidos,
  excluidos y evidencia reutilizada. No stagear archivos por carpetas completas.
- Mapear cada cambio a H3-CA4 o a seguridad/compatibilidad aceptadas; no agregar extras.
- Reconciliar solo deltas necesarios; conservar correcciones remotas y trabajo ajeno.
- Confirmar metadata Pro autorizada: el último corte acreditó `provider_used` y
  cohorte presente. El fixture contraído futuro NO representa Pro actual.
- Catalogar migraciones locales nuevas, dependencias, ledger y efectos reales; no
  editar ni renombrar una migración aplicada para fingir convergencia.

Salida: inventario sin drift y alcance trazable. Si necesita nueva lectura remota,
pedir permiso read-only acotado; no exponer PII ni secretos.

### H3-CLOSE-02 — Gateway firmado y cuotas resistentes al aborto

Responsables: desarrollo backend y seguridad; aprobación SQL/infra: humano.
**Estado vigente: PASS del alcance local PG17/PostgREST v4.** Conservar hashes y
resultados registrados; no repetir por instrucciones históricas inferiores. Los JIT
1–5 y v1–v3 con fallos explican las correcciones, no bloqueos aún abiertos. El permiso
de bootstrap npm fue aprobado/consumido; no es una aceptación pendiente ni waiver activo.
El subgate SQL safe-suspend posterior tiene evidencia propia v2. H3-CLOSE-03 integrado,
Ready y Development real continúan NO-GO; el resultado de esta tarea no los sustituye.

#### Historia de implementación 2026-10-04 — runtime pendiente en aquel corte, resuelto en v4

**Actualización posterior a `continua` — 2026-10-04:** se implementó localmente la
remediación en `db/migrations/20261004_h3_admin_rpc_signed_gateway_payload_bound_wrapper.sql`.
El BFF conserva los nombres de destino allowlisted; el transporte firma metadata y una
segunda prueba que incluye el RPC objetivo y el JSON de argumentos, y envía la llamada
al dispatcher `admin_signed_rpc`. El dispatcher compara el texto firmado con `p_args`,
valida target/keys y ejecuta ramas estáticas con casts tipados, sin SQL dinámico. El
pre-request actualizado rechaza llamadas Admin legacy directas de `authenticated`; los
destinos service-role existentes y `auth.uid()`/RLS/RBAC/MFA se preservan. La revisión
de código de producto no encontró defectos LOW+ no mitigados; la revisión posterior del
manifiesto registró egress MEDIUM de bootstrap, documentado y pendiente de aceptación. Sigue faltando la
validación PG17/PostgREST de los bytes actuales. El ciclo local ejecutó
`pytest tests -q` (**287 passed/4 skipped**), credential scan y `git diff --check`; los
resultados completos están en la evidencia enlazada en Estado Del Proyecto. **No hubo
ejecución SQL ni JIT.** NO-GO sigue vigente.

#### Historia de `p_first: null` y migración forward — 2026-10-04

Se cerró localmente el LOW: la RPC fuente rechaza SQL `NULL` antes de los `LIMIT`; la
migración `20261004_h3_admin_queue_first_null_guard.sql` actualiza forward-only la RPC
ya registrada o, si está instalado `H3_QUOTA_WRAPPER_V1`, solo su snapshot privado. La
migración falla cerrada ante ausencia o drift y conserva el wrapper público. El
dispatcher firmado convierte exclusivamente el JSON `null` en sentinel `0` y llama la
RPC pública para conservar cuota, AAL2, RBAC y la respuesta legacy; SQL `NULL` no llega a
`LIMIT`.

Los harnesses versionados cubren RPC directa, reparación del snapshot de cuota, cuotas
firmadas para AAL1/admin/no-editor y nonces independientes. **No se ejecutaron**: pytest
Docker pasó **287 passed/4 skipped**, el credential scan de archivos tocados y
`git diff --check` pasaron, y la revisión estática `security-auditor` terminó con **0
hallazgos LOW+**. Se requiere aprobación JIT nueva con hashes finales antes de PG17,
PostgREST, wire o cualquier SQL. NO-GO sigue vigente.

Secuencia/rollback: tras JIT PG17 explícito, aplicar la migración forward del null guard,
las dos migraciones `20261004_h3_admin_rpc_signed_gateway_expand.sql` y
`20261004_h3_admin_rpc_signed_gateway_payload_bound_wrapper.sql` en ese orden; ejecutar
los harnesses de cuota y gateway; conservar legacy/contrato de valores válidos durante
compatibilidad y despliegue del BFF; activar el pre-request estricto solo tras comprobar
el BFF nuevo. El null guard se conserva también en rollback; no se restaura el camino
`LIMIT NULL`. Rollback del gateway requiere safe-suspend, rollback coordinado de BFF y
restauración aprobada del pre-request anterior, sin DROP de keys/nonces. CONTRACT puede
retirar grants directos legacy tras estabilidad y gate aparte. No se han validado
rollback integrado ni CONTRACT.
Owner: Romel; implementadores: Backend/DB Security; objetivo `2026-10-11`; no es waiver.

Rutas a revisar: `web/functions/_lib/admin-bff.ts`, `admin-quota.ts`,
`workers/admin-quota/`, `supabase/functions/admin-invite/index.ts`,
`db/migrations/20261002_h3_admin_quota_expand.sql`, `20261002_h3_admin_quotas.sql`,
`db/migrations/20261004_h3_admin_queue_first_null_guard.sql`,
`db/migrations/20260927_h3_admin_queue_facets_filter.sql`,
`20261004_h3_admin_rpc_signed_gateway_expand.sql`,
`20261004_h3_admin_rpc_signed_gateway_payload_bound_wrapper.sql`,
`tests/sql/h3_admin_quota_harness.sql`, `tests/sql/h3_admin_rpc_signed_gateway_harness.sql`,
`tests/test_h3_admin_queue_ux_contract.py`, `.github/workflows/security-audit.yml` y
`web/src/lib/supabase-transport.ts`.
El hallazgo histórico fue que la cuota transaccional perdía admisión al abortar y un
contador BFF aislado no impedía invocación directa a Data API. La admisión DO ahora
precede a PostgREST y sobrevive al rollback local. El contrato cubierto por el gate
PG17/PostgREST v4 ya pasó; completar integración y aceptación remota sin ampliar
el alcance de aquel PASS. Revalidar solo cuando cambien inputs/contratos relevantes.

Verificar el diseño ya implementado y corregir solo defectos demostrados, sin rediseñar Auth/onboarding:

1. Admisión de RPC por Durable Object antes de enviar a PostgREST, con actor derivado
   de sesión validada; conservar JWT, `auth.uid()`, RLS, RBAC y MFA.
2. Gate Data API `db_pre_request` con firma temporal allowlisted, actor coincidente
   con JWT y rechazo cerrado de RPC Admin no firmada. Proteger también nombres legacy
   cubiertos; inventariar RPC/rol/método, no un prefijo genérico permisivo.
3. Definir formato firmado, destino, método, actor, vigencia, validación y tratamiento
   de replay/rotación. Si ese detalle requiere decidir entre opciones de seguridad
   diferentes, preguntar antes; no crear permisos o excepciones por inferencia.
4. Mantener finalizadores service-only in-flight y RPC públicas no Admin legítimas.
   `db_pre_request` cubre PostgREST, no todos los servicios Supabase: documentar límites.
5. Edge conserva admisión independiente 120/actor/min antes de Auth, reserve-before-Auth,
   replay idempotente y finalizadores fuera de cuota de iniciación. No duplicar envío.
6. Sin contador/configuración: 503 y sin nuevos efectos; exceso: 429/Retry-After válido.
   Logout y limpieza local continúan operativos. No exponer identidad ni motivos internos.

Umbrales ya aceptados: entrada BFF IP 300/min; login IP 20/10min;
cuenta+IP 10/10min; MFA/callback/password 10/10min por clase;
RPC lecturas 120/min, escrituras 30/min; entrega invitación actor 3/min y 10/h,
destinatario 3/24h, ambiente 50/24h. No modificarlos sin decisión humana.

#### Hallazgos y remediación local — 2026-10-05

La revisión estática detectó un HIGH: login enviaba contadores IP y email:IP en paralelo
a Durable Objects separados; una IP limitada aún podía asignar un objeto persistente por
cada identidad de cuenta. Se corrigió sin cambiar umbrales: el BFF deriva un shard HMAC
por IP; el Worker co-ubica la pareja en un DO, exige máximo un contador IP y uno de
cuenta, conserva el conteo IP cuando solo excede la cuota de cuenta, no añade cuenta
tras bloqueo IP y borra ledger vencido dentro de la transacción de alarma. Para el
payload BFF anterior sin shard, infiere el digest del único contador `login-ip`; esto
mantiene compatibilidad durante `expand -> compatibilidad -> deploy`.

También se cerró el LOW del harness local: al aislar epochs transforma conjuntamente
digest y shard, con regresión que verifica ambos valores cambian y siguen emparejados.
El Worker rechaza múltiples `login-ip` y múltiples `login-account-ip`; pruebas unitarias
y Miniflare cubren cardinalidad, persistencia, legacy payload y cleanup.

Un hallazgo MEDIUM afirmaba que `listFactors()` requiere GET Auth `/factors`. La
inspección Docker de `@supabase/auth-js` 2.109.0 demostró que deriva `user.factors` desde
GET `/auth/v1/user`, ya allowlisted. No se amplió la superficie JWT; la aprobación humana
para el GET adicional quedó sin consumir y la atestación lo documenta.

Resultados del corte pre-JIT (histórico): pytest 287/4 skipped; TypeScript PASS; lint 0 errores/9 warnings;
cuotas, SDK, Auth/BFF/Edge y smoke mock PASS; credential scan/diff check PASS. Revisión
de código producto sin defectos LOW+ no mitigados; egress MEDIUM de bootstrap JIT requiere
aceptación humana. El Miniflare test usó Node `v20.20.2`; el wire PostgREST del
manifiesto utilizará Node 22. Ningún SQL/PG17/PostgREST se ejecutó. La matriz de hashes
y la secuencia íntegra están en el [manifiesto JIT](manifiesto_jit_pg17_postgrest_h3req1_2026-10-05.md),
que en ese corte esperaba autorización. Fue seguido por v2/v3/v4, y v4 completó el
runtime local. NO-GO global permanece por rollback integrado, UAT final, CI/protecciones
y aceptación remota, no por el runtime inicial ya ejecutado.

Antes de autoría/ejecución SQL o grants, solicitar JIT exacto para archivo propuesto,
base PG17 desechable e impacto. El JIT del drill anterior no se reutiliza.
Validar firma inválida/ausente/expirada, actor/método/destino incorrectos, replay,
RPC directa y legacy, aborto/cancelación, concurrencia, restart/ventanas, contador caído,
403 MFA que conserva admisión, finalizadores y tablas/roles sin grants indebidos.

Salida: cuotas y gate sin bypass confirmado, pruebas reproducibles, revisión sin
hallazgos bloqueantes. No presentar SQL local como activación remota.

### H3-CLOSE-03 — Rollback integrado y recuperación segura

Responsables: desarrollo, QA y release. Pendiente: ensayo conjunto, no componentes.

- Crear protocolo local sobre artefacto servido por workerd, Edge y PG17 compatibles.
  Inventariar versiones, bindings, flags, cookies y dependencias en ejecución.
- Probar operación normal -> suspensión Pages/Edge/SQL -> rechazo de nuevos iniciadores
  -> finalización de reservas previas -> verificación de datos/auditoría -> recuperación.
- Mantener páginas públicas, auditoría append-only y al menos otro admin activo;
  limpiar cookies/chunks/verifier y rechazar aliases Admin/hosts no autorizados.
- Suspensión usa artefacto endurecido, `ADMIN_BFF_SAFE_SUSPEND`,
  `ADMIN_INVITE_SAFE_SUSPEND` y `db/rollback/h3req1_safe_suspend.sql`.
  NO restaurar tokens JS ni Edge que envía Auth antes de reservar.
- Diseñar recuperación real explícita. El resume TEST-only solo prueba el harness;
  no es un procedimiento autorizado para remoto. Si falta vía segura, corregirla
  y validarla antes de prometer recuperación.
- Definir condiciones de activación, operador, tiempo medido, efectos esperados,
  verificación y recuperación. No inventar SLA; pedir plazo al humano si es necesario.

Salida: drill integrado PASS local con evidencia de no pérdida/no bypass; paquete
remoto exacto listo para autorización independiente.

**Actualización H3-CLOSE-03 — revisión y validación local 2026-10-05:** revocar las funciones mutadoras
internas no bloqueaba por sí solo el dispatcher autenticado `admin_signed_rpc`, que es
`SECURITY DEFINER`; el harness anterior no probaba esa ruta. Tras autorización local
acotada, `db/rollback/h3req1_safe_suspend.sql` ahora suspende también el dispatcher y
`tests/sql/h3_safe_suspend_harness.sql` captura su ACL, prepara una prueba firmada
payload-bound, comprueba rechazo por privilegios y restaura solo los permisos efectivos
capturados para el test. Bajo una aprobación JIT nueva, en el PG17 desechable pasaron
baseline H2→H3, cuotas y gateway firmado. La salida de este último mostró firmas HMAC
sintéticas del fixture; no se registran sus valores ni hubo credenciales reales. La
continuación del harness safe-suspend pasó con `psql -q -o /dev/null`, exit code 0 y sin
output bajo el [manifiesto JIT v2](manifiesto_jit_h3_close03_safe_suspend_pg17_2026-10-05_v2.md).
El JIT v4 no cubre estos bytes. H3-CLOSE-03 sigue NO-GO: faltan ensayo integrado
workerd+Edge+PG17, recuperación operativa explícita, cookies/bindings, preservación de
otro admin y evidencia de no bypass en los artefactos coordinados. El restore temporal
del harness no es un procedimiento remoto ni una vía de recuperación operativa.

El preflight conserva H3-CLOSE-02 v4: 72/72 inputs no C03 siguen intactos. Se autorizó
la autoría local de `safe_suspend`, `safe_resume` y el harness. Después, bajo JIT C03 v3
exacto y `continua`, los cuatro procesos `psql` terminaron exit 0 en un PG17 desechable;
los tres primeros fueron bootstrap y no son PASS nuevo de gates previos. El PASS safe-suspend
v2 queda histórico por hashes anteriores. El nuevo subgate SQL C03 pasó; el drill integrado
sigue bloqueado y requiere JIT independiente. Ver
[preflight H3-CLOSE-03](../evidencia/h3req1_h3_close03_integrated_preflight_2026-10-05.md).

### H3-CLOSE-04 — Dependencias, warnings y mantenimiento

- `web/vendor/braces-3.0.4-h3.1.tgz` es snapshot upstream fijado, no release oficial.
  Confirmar owner y fecha de revisión, procedencia/hash/licencia y condición de reemplazo.
  Audit 0 por sí solo no cierra su mantenimiento.
- Registrar 9 warnings ESLint: 7 hooks (incluye facetas públicas que pueden no actualizar
  por dependencia `priceMin`) y 2 variables no usadas; deprecación PyPDF2; 4 tests
  live Supabase omitidos. No tratarlos como PASS ejecutado.
- El defecto de facetas es previo y fuera del diff H3: consultar si se corrige con
  alcance aprobado o queda en backlog separado con owner/riesgo. No ampliar PR silenciosamente.
- Asignar responsable a cada pendiente; decisiones de aceptación/waiver corresponden
  al humano. Los 4 tests live deben evaluarse para ejecución remota JIT y justificarse
  individualmente si no aplican.

Salida: mantenimiento y riesgos explícitos, sin owner ficticio ni waivers inventados.

Decisiones humanas registradas en esta continuación (2026-10-04): conservar el
snapshot temporal `braces@3.0.4-h3.1` con Romel como owner de revisión/reemplazo para
`2026-11-03`; no convertirlo en release ni waiver. El defecto previo de facetas por
`priceMin` queda separado del alcance H3, con Romel como owner de seguimiento para
`2026-11-03`. Los dos warnings `no-unused-vars`, la deprecación PyPDF2 y los cuatro
tests live Supabase siguen sin owner/aprobación de ejecución; no se ocultan ni se
declaran aceptados.

### H3-CLOSE-05 — CI independiente protegido y bootstrap

El YAML local `protected-workflow-integrity.yml` NO existe en el baseline remoto
consultado. El HIGH sigue abierto hasta demostrar control confiable y efectivo.
`security-audit` histórico verde no lo cierra. Ruleset observado solo restringe updates,
con bypass del owner; regla clásica/required checks efectivos no acreditados.

- Pedir lectura de reglas/checks/permisos con método que permita acreditar la
  configuración efectiva; 401 o pantalla incompleta significa DESCONOCIDO, no AUSENTE/PASS.
- Mantener dos identidades `romelhc95` y `romelhc95-approver`; autor no se autoaprueba,
  review vigente sobre SHA final y merge por la otra identidad según permisos reales.
- Preparar PR mínimo de bootstrap desde baseline confiable y explicar cómo se revisa
  antes de existir el nuevo check. No activar en ese mismo primer paso una dependencia
  circular que espere un workflow todavía ausente; no deshabilitar protecciones existentes.
- Verificar workflow seguro (sin ejecutar código no confiable con privilegios),
  required checks efectivos, rechazo sin review/review obsoleto y aprobación válida;
  al cambiar SHA deben invalidarse aprobación/evidencia afectadas.
- Instalar y configurar solo con autorizaciones separadas de push/PR, merge y protección.
  Si el bootstrap debe alcanzar bases protegidas posteriores, definir vía protegida
  de controles sin arrastrar código funcional no certificado ni bypass.

Salida: enforcement remoto documentado y HIGH cerrado por revisión/evidencia.
Su PR es prerrequisito del mismo cierre, no entrega final de H3REQ1.

### H3-CLOSE-06 — Validación final, aceptación y Ready

Preparar snapshot Docker aislado del candidato; no tocar `web/out` original.
El script build elimina su output: ejecutarlo únicamente en la copia destinada al gate.
Host Windows no ejecuta npm/python/pip. Confirmar mount y carpeta del contenedor:
`studiamatch-dev` monta el checkout original en `/app`, NO el worktree sincronizado.
No validar por error el código antiguo. Si crear/montar un entorno requiere permiso,
consultar antes; no modificar infraestructura o archivos ajenos por conveniencia.

Entrada de validaciones (leer cada runner y sus argumentos actuales antes de ejecutarlo):

- CI exacto: `.github/workflows/security-audit.yml`, incluidos credential/protected paths,
  Python, DB gate, actionlint/shellcheck y agregado; check independiente separado.
- Frontend en copia `/web`: `npm ci`, `npx tsc --noEmit`, `npm run lint`,
  `npm audit --include=dev`, `npm audit --omit=dev`, build normal y fixture/mock.
  Static export con ruta elegible, no solo fallback `example.invalid`.
- SQL: harness H2/H2-Pro, `h3_from_h2_pro_pg17_harness.sql`, `h3_pg17_harness.sql`,
  invitación/onboarding/Edge runtime, concurrencia, cuotas/PostgREST y safe suspend.
  Pro actual con cohorte y contracción futura son modos distintos. Reapply/NOOP,
  firmas/OIDs/grants/RLS/constraints e identidad deben verificarse.
- Runners `tests/h3_admin_bff_mock_uat.mjs`, `h3_admin_auth_error_uat.mjs`,
  `h3_admin_invite_edge_uat.mjs`, `h3_admin_invite_edge_typecheck.mjs`,
  `h3_supabase_sdk_headers_uat.mjs`, `h3_admin_quota_{uat,runtime,postgrest}.mjs`,
  `h3_admin_safe_suspend_{uat,runtime_uat}.mjs` y suites visual/onboarding
  `h3_local_uat.mjs`/`h3_invitation_uat.mjs`.
- Pytest/contratos y compilación/sintaxis de archivos afectados, H2 writer scan,
  `git diff --check`; no ejecutar workers contra cloud para probar sintaxis.

Resultado visual esperado según runner vigente: 48/48 casos, 144/144 ejecuciones
y capturas, cero retries; onboarding 10/10. Si se agregan casos por cobertura del
gateway, explicar cambio y exigir todos PASS, no mantener cifras por apariencia.
Conservar fallos y timeout, corregir causas, no ocultarlos aumentando retries.

Congelar hashes separados de fuentes, lock/vendor, artefacto y resultados; manifest
de fuentes excluye evidencia generada para evitar digest circular. Registrar herramientas,
configuración sanitizada, fecha UTC, comandos reales y exit codes. Verificar existencia
y recuperabilidad de evidencia en contenedores temporales antes de retirarlos.

Revisión de seguridad exacta según AGENTS y criterios cliente; pilares:
funcionalidad, escalabilidad, seguridad, mantenimiento, calidad y rendimiento.
Medir comportamiento de cola/paginación/carga acotada; no afirmar rendimiento por
un test unitario ni inventar umbrales. Consultar presupuesto si falta decisión necesaria.

Salida R: candidato local final aceptado, CI independiente efectivo, paquetes PR y
operaciones remotas completos. No exige UAT remota anticipada ni concede permisos.

### H3-CLOSE-07 — Integración y despliegue compatible Development real

- Inventario remoto aprobado de Free, schema/ledger/funciones/grants, Auth, Edge,
  Pages, Worker y hosts; usar Pro como baseline, no corregir Pro desde Free.
- PR funcional `feat/h3req1-sync-20261002 -> desarrollo` con plantilla versionada y
  resultados actuales, no tablas históricas copiadas. Push/PR y merge separados.
- Antes de merge: checks reales verdes, review de SHA final y autorización de merge.
  Tras merge, registrar SHA integrado y artefactos derivados; reconstrucción distinta
  exige demostrar equivalencia o repetir gates afectados.
- Preparar manifiesto por ambiente: migraciones exactas y hashes, expand/activación,
  Edge versión/hash, Worker/DO, Pages deployment/artefacto, Auth templates/redirects,
  hostname permitido y rollback. No usar Preview hardcodeado como contrato del ambiente.
- Free/Development: ref `aqrldlmlszjtgpqiegaa`. No usar `admin.studiamatch.com` para UAT
  Development; elegir alias administrativo exacto aprobado y vinculado a `desarrollo`.
- Secuencia a concretar y probar: expand aditivo -> instalar configuración/servicio
  requerido -> Edge compatible reserve-before-Auth -> preparar/desplegar BFF/Worker
  compatibles -> activar controles SQL/gateway solo cuando sus consumidores estén listos
  -> verificar contrato activo. El gateway pendiente puede ajustar el orden: documentar
  dependencias/ventana compatible, no ejecutar este listado como sync ciego.
- Variables/bindings por nombre: `SUPABASE_URL`, `NEXT_SUPABASE_PUBLISHABLE_KEY`,
  `ADMIN_ALLOWED_HOSTS`, `ADMIN_QUOTA`, `ADMIN_QUOTA_HMAC_KEY`,
  `ADMIN_RPC_GATEWAY_HMAC_KEY`, `ADMIN_RPC_GATEWAY_KEY_ID` y flags de suspensión.
  BFF sin secret/service-role key; Edge mantiene credenciales privilegiadas server-side.
  Secreto firmado, DO y configuración PostgREST tienen JIT propios. No exponer valores.
- No habilitar mocks ni excepciones localhost en Cloudflare. No abrir Worker por
  workers.dev/preview/routes. Probar host público/desconocido/aliases codificados
  con fallo cerrado para UI y API.

Salida: candidato realmente desplegado e inventariado, compatible y disponible para
UAT autorizada, no todavía GO D. Cualquier fallo detiene activación siguiente.

### H3-CLOSE-08 — Matriz de aceptación remota y GO Development real

Responsables funcionales: desarrollador/QA/operador, dueño de buzón/decisiones: humano.
No almacenar contraseñas, JWT, códigos/secretos MFA, enlaces Auth ni PII en evidencia.

| ID | Prueba real obligatoria | Evidencia de aceptación |
|---|---|---|
| D01 | Cuenta existente: limpiar sesión legacy, login con misma cuenta y MFA, sin reinvitar/reenrolar; sesión server-side | Panel/RPC AAL2 aceptados; cookies HttpOnly/Secure/SameSite, JWT ausente de JS/storage/respuestas |
| D02 | Refresh, navegación post-refresh, expiración, logout/relogin, múltiples pestañas, errores seguros y CSRF | No pérdida de assurance indebida ni reapertura de sesión cerrada; origen/host inválido bloqueado |
| D03 | Invitación real y buzón autorizado; callback, aceptación, password, MFA/onboarding; expiración/replay/reenvío | Estado ready coherente, un efecto por operación, sin doble correo/reenvío no autorizado, errores sanitizados |
| D04 | Anónimo, autenticado sin membresía, inactivo, invited/password_pending, user y admin | Denegación de no autorizados; user solo missing_fields; admin hereda y tiene acciones propias |
| D05 | Invitación/roles/activar-desactivar, último admin y autobloqueo | Invariante de admin activo y auditoría por cambio; no permisos extra ni último admin perdido |
| D06 | Cola, facetas, filtros, conteos, cursor y segunda página, búsqueda/institución | Resultados coherentes, sin duplicados/pérdidas en escenario controlado; UI responsive |
| D07 | Editar campos allowlisted, ownership/override, faltantes y vista efectiva | 13 campos según contrato, cuatro campos independientes, pipeline no pisa manual ni publica automáticamente |
| D08 | Guardar con dos sesiones/versiones; publicar/despublicar/archivar y calidad | Conflicto visible sin overwrite silencioso, solo rol autorizado, publicación y lectura pública coherentes |
| D09 | Historial editorial y membresías, actor/antes/después | Auditoría atómica append-only protegida, cliente sin acceso directo/alteración |
| D10 | Disponibilidad con evidencia válida, ausente, inválida y vencida >90 días | unknown cuando corresponde; valid_until no excede observed_at+90 días; publicar sigue contrato seguro |
| D11 | Curso nuevo elegible y ruta estática/detalle público tras build/deploy | Ruta real resuelve el curso efectivo, no fallback; elegibilidad/publicación sin romper rutas legacy |
| D12 | Cuotas vía BFF, RPC directa/legacy y Edge, firma, replay, cancelación/fallo | Admisión no evadida, 429/Retry-After y 503 seguros; no efectos al rechazar; finalizadores disponibles |
| D13 | Host Admin autorizado y Access según ambiente; público/host desconocido/API/alias codificado | Perímetro real; dominio público no sirve Admin (404); ningún secreto ni respuesta cacheada privada |
| D14 | Drill remoto integrado autorizado y recuperación | Suspensión/rechazo/cookies/in-flight/datos/auditoría/público correctos; recuperación verificada sobre artefacto endurecido |

Mapear D03 a H3-002, D04–D10 a H3-003 y D01/D02/D11–D14 a H3-004;
H3-001 exige contrato DB y convergencia verificados. Son agrupaciones de evidencia,
no sustitutos de los casos específicos y atestaciones.

Separar cuenta de onboarding y cuenta existente de compatibilidad. La estrategia
previa eligió reinicio Free acotado de cuenta designada tras inventario: no asumir
reset autorizado ni cambiarla por una cuenta nueva sin consultar. Confirmar si aún
hace falta; preservar otro admin, dependencias y auditoría. Nunca resetear Free completo.
No ejecutar writers productivos o ETL remoto para fabricar el curso D11: usar fixture
local para build y datos reales elegibles o fixture remoto mínimo con JIT DML separado.

Pruebas de exceso/cancelación/correo/drill/cleanup implican efectos: pedir JIT con
cuentas/filas/límites/operaciones identificados de forma sanitizada. No hacer carga
indiscriminada ni agotar cuotas de usuarios reales. Cleanup nunca borra auditoría.

Salida D: D01–D14 aplicables PASS, H3-001/002/003/004 reconciliados, revisión de
seguridad/pilares/cliente sin bloqueos, SHA/hosts/DB/Edge/Worker/artefacto identificados,
rollback y recuperación aceptados. Registrar GO Development real en estado y evidencia.
Si falta un caso, reportar NO-GO con tarea concreta; no renombrar acceptance como readiness.

## 6. Posterior: Certification (NO autorizada por este plan)

Solo tras GO D e instrucción humana separada:

1. Refrescar `desarrollo`/`certificacion`, baseline/CI/protecciones y delta. Abrir PR
   protegido `desarrollo -> certificacion` con aceptación D y resultados del candidato.
2. Definir hostname/deployment Certification propio, Access, redirects y bindings.
   Certification usa Free, igual que Development: no son DB físicamente independientes.
   Inventariar coexistencia de schema/Edge/secrets/flags/usuarios; aislar fixtures y
   ventanas. Si requiere configuraciones globales incompatibles, detener y consultar
   estrategia, no afirmar aislamiento inexistente ni crear ambiente extra sin permiso.
3. Merge/deploy y cambios DB/Auth/config separados y autorizados. No reaplicar SQL
   a ciegas por cambiar rama; comprobar ledger y efectos reales, idempotencia y NOOP.
4. Ejecutar D01–D14 adaptados al hostname/SHA Certification, regresión público/Admin,
   compatibilidad de cuentas, permisos reales, carga acotada, auditoría y rollback.
   Reutilizar solo evidencia sin impacto demostrable; resultados Development no
   sustituyen aceptación del deployment Certification.
5. Evaluar aceptación sanitizada y seis pilares, CI/review efectivos, sin HIGH/CRITICAL
   abiertos ni pendientes bloqueantes. Salida C: GO Certification con inventario exacto.

Detener antes de Pro/main. Sin GO C no preparar una promoción funcional siguiente
como si estuviera aprobada; un NO-GO exige remediar y revalidar gates afectados.

## 7. Posterior: Production y cierre contractual (NO autorizados)

Solo tras GO C e instrucción humana separada:

1. Leer baseline Pro actual (`xwhtiqmboljkshrtviyw`) con autorización, incluyendo
   schema/tipos/constraints/grants/RLS/vistas/funciones y migraciones H2. Ledger no
   prueba por sí solo toda aplicación histórica. No suponer cohorte ya retirada.
2. Comparar candidato certificado con Pro, probar cadena limpia contra metadata
   autorizada, compatibilidad del frontend main vigente y rollback. Pro es autoridad;
   no corregirlo por diferencias de Free/local ni transferir datos operativos/fixtures.
3. Preparar manifiesto exacto Pro por fases: expand compatible antes del nuevo
   frontend, Edge/Worker/BFF/config/secrets, activación del gateway/cuotas con
   consumidores listos. El sync DB automático/ciego puede romper ese orden: no
   dispararlo sin aprobar el conjunto preciso. Backup/restore y writers tienen JIT propio.
4. Preparar hostname canónico `admin.studiamatch.com`, Cloudflare Access, redirects,
   cookies y allowlist exactos; `studiamatch.com`/`www` no sirven Admin ni API Admin.
   Sin mock/localhost ni secretos en browser. Recursos por ambiente sin reutilizar keys.
5. PR protegido `certificacion -> main`, checks reales/approval vigentes y merge
   autorizado. Coordinar el deploy normal disparado por merge con prerrequisitos Pro;
   permiso de merge no habilita operaciones manuales adicionales.
6. Verificar runtime productivo con UAT acotada y autorizada, usando la misma matriz
   contractual; no correo masivo ni carga destructiva. Registrar artefactos/SHA y
   transición de cuentas existentes sin reinvitación ni reset MFA.
7. Acordar antes del deploy ventana de observación, owner, señales de estabilidad,
   umbrales de alerta y condición de suspensión/recuperación. No inventar duración
   ni SLA; preguntar en lenguaje simple. Producción publicada no equivale a hito cerrado.
8. Tras estabilidad y aprobación separada, **contract**: retirar bypass/lectores,
   rutas o adapters legacy identificados y dependencias innecesarias, con pruebas
   de no degradación. No DROP CASCADE ni borrar datos/auditoría/contadores; cohorte
   H2 depende de paridad y desacople probado, no se retira por llamar al paso contract.
9. Cierre P: aceptación fuente cliente/atestación, seis pilares, matriz por ambiente,
   cero bloqueos, contract real, rollback/recuperación y estado/índice/hito/tarea/seguimiento
   actualizados. No avanzar H4 por intención ni ocultar pendientes como legado.

## 8. Solicitudes de aprobación: formato y límites

Antes de cada operación protegida presentar ambiente, archivo/hash/SHA o recurso,
operaciones exactas, efectos, actores/datos afectados, prerrequisitos, rollback y
qué NO se hará. Nunca pedir «autorización total». Registrar respuesta y consumo del JIT.

| Operación | Permiso independiente necesario |
|---|---|
| SQL/grants/config PostgREST local | Autoría/ejecución exacta en PG17 desechable; sin reutilizar permiso de harness anterior |
| Lectura remota | Proveedor, ambiente, recursos/campos necesarios; sin valores secretos ni PII |
| Push/PR/bootstrap/protecciones | Instrucciones Git/controles explícitas por operación; review y merge separados |
| DDL/DML Free o Pro | Archivos/hash, inventario de efectos y compatibilidad; no blanket-sync |
| Auth/correo/reset/factores/membresías | Cuentas y acciones acotadas, otro admin preservado; no reset implícito |
| Secretos/bindings/Worker/Edge/Pages/DNS/Access/templates | Recurso y ambiente exactos, orden y reversión; no imprimir secretos |
| Rollback/suspensión/resume/cleanup/backup/restore | Manifiesto independiente; deploy no lo autoriza por extensión |
| Certification/Production | Instrucción humana de etapa más los permisos operativos que corresponden |

### Cómo preguntar si el desarrollador tiene dudas

Hablar de efecto para la persona, no solo siglas. Dar recomendación, alternativas,
ventaja/riesgo y alcance de autorización. No forzar decisiones de implementación
cuando una opción segura ya está aceptada; consultar ambigüedad, drift o JIT real.

Ejemplos:

- «Para probar una invitación nueva necesitamos preparar esta cuenta de prueba.
  ¿Permitís reiniciarla solo en desarrollo, conservando el historial y otro administrador,
  o preferís que revisemos otra opción? No tocaré producción.»
- «Si el panel nuevo falla, propongo dejar la web pública funcionando y pausar solo
  la administración, sin volver al acceso antiguo menos seguro. ¿Autorizás este ensayo
  con estas cuentas y este procedimiento de recuperación?»
- «Hay una advertencia previa en los filtros públicos que no pertenece a este cambio.
  Podemos corregirla ahora y ampliar las pruebas, o dejarla registrada con responsable
  y fecha. ¿Cuál preferís? No la daré por resuelta sin probarla.»
- «Para que nadie pueda aprobar su propio cambio, necesitamos confirmar estas reglas
  de revisión. ¿Autorizás consultar la configuración? Consultarla no la modifica.»
- «La corrección temporal de una dependencia ya pasó las pruebas. ¿Quién revisará su
  reemplazo por la versión oficial y en qué fecha?»
- «Antes de retirar lo antiguo en producción, ¿durante cuánto tiempo querés observar
  que todo funciona y quién dará la conformidad? Te propongo señales verificables.»

Si el usuario no responde, conservar NO-GO del gate afectado y explicar qué decisión
falta. No elegir por silencio, no tratar recomendaciones como permisos concedidos.

## 9. Evidencia y formato de cierre para la siguiente sesión

Cada tarea registra: ID, criterio cliente, estado (pendiente/en ejecución/PASS/FAIL/
bloqueado por aprobación), fuente/candidato hash, ambiente, prueba/comando/exit code,
fecha, evidencia recuperable sanitizada, hallazgos, owner, JIT usado y gate siguiente.
No llenar una tabla con «se validará» bajo columna Resultado.

Al llegar a GO D, entregar: veredicto y alcance; SHA integrado y deployment/host;
contratos/migraciones/Edge/Worker activos; D01–D14 y casos omitidos justificados;
review/CI efectivos; seguridad/pilares/atestación; rollback/recuperación; riesgos
residuales aprobados; documentación actualizada. Terminar explícitamente:
«Development real GO. Certification/Production no ejecutadas; requieren aprobación.»

Si no llega a GO D, entregar bloqueo concreto, evidencia, decisión requerida y opciones
en lenguaje sencillo. Nunca declarar GO porque el modelo agotó tiempo/contexto.

## 10. Prompt de continuación — ejecutar solo hasta GO Development real

Sincronizado con el traspaso el 2026-10-05: H3-CLOSE-02 PASS local v4 y safe-suspend/resume
SQL PASS bajo JIT C03 v3 exacto. El próximo gate es H3-CLOSE-03 integrado; el SQL PASS no
autoriza reintentos, integración ni cleanup de recursos. Reutilización exige hashes/alcance
coincidentes; cambios requieren gates y JIT nuevos según impacto.

```text
continua con H3REQ1 en /home/romel/src/studiamatch-h3req1-sync-20261002,
rama feat/h3req1-sync-20261002.
Lee AGENTS.md, .context/estado_del_proyecto.md,
.context/operaciones/plan_cierre_integral_h3req1_2026-10-04.md y
.context/seguimiento/h3req1_traspaso_avance_y_proximo_ciclo_2026-10-04.md,
con sus evidencias y atestaciones. Lista tareas y gates antes de editar.
H3-CLOSE-02 ya pasó PG17/PostgREST/wire/assert/concurrencia bajo JIT v4;
el subgate SQL safe-suspend/resume persistente pasó bajo JIT C03 v3 exacto.
Empieza en H3-CLOSE-03 integrado: rollback coordinado Pages/workerd+Edge+SQL,
cookies/bindings/in-flight y recuperación operativa segura, no restore TEST-only.
Revalida hashes y alcance; conserva los PASS vigentes y no repitas JIT consumidos.
Si nuevos cambios invalidan evidencia, explica impacto y pide JIT nuevo exacto. El subgate
SQL PASS no autoriza reintentos, integración ni cleanup de sus dos PG17.
Después completa H3-CLOSE-01 pendiente y H3-CLOSE-04–08 hasta GO Development real:
candidato exacto, UAT final, CI obligatorio efectivo, PR/integración/despliegue
y D01–D14 remotos con aprobaciones por operación. No termines solo en PR_READY.
Este continua autoriza el ciclo local funcional, NO SQL/grants, operaciones
remotas, secretos, Auth/reset, push/PR/merge, protección, deploy, rollback/resume,
cleanup ni acciones destructivas: solicita permisos separados y espera respuesta.
Trabaja en Docker contra el worktree correcto; preserva original, WIP, recursos
y evidencias. Conserva Auth+MFA real histórico y prueba transición sin reinvitar
ni reenrolar cuentas existentes. Corrige/revalida sin GO parcial ni bloqueos ocultos.
Actualiza Obsidian enlazado con resultados reales. Ante dudas, explica opciones
en lenguaje sencillo. No revises gobierno general ni recuperes arquitectura histórica.
No ejecutes Certification/Production. Detente en GO Development real o bloqueo
concreto de autorización, drift o validación, con evidencia y siguiente decisión.
```
