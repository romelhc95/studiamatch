# H3REQ1 — avance comprobado, PR y pruebas remotas

## Continuación registrada como vigente en el corte 2026-10-08 — histórica

F2b y F2c se consumieron una vez. F2b falló en canonicalidad; F2c verificó el socket Unix
local/canónico, pero no probó el peer y terminó antes de Docker API, imagen o inspect F1.
F1 sigue sin control discrepante identificado. F2d prepara una prueba directa `SO_PEERCRED`
y requiere aprobación nueva y aceptación fresca de ambos residuales MEDIUM. La revalidación
vigente de C02 v4 no-C03 es 70/72 por cambios del workflow y guard HMAC BFF; C03 SQL v3
conserva 41/41. Las suites SQL no se repitieron.
El paquete helper r4 espera aprobación de una ejecución; el BFF UAT también requiere
validación en Docker. Scanner/scope guard y stack integrado siguen pendientes.
`GO_LOCAL_PR` y `GO_DEVELOPMENT_REAL` siguen NO-GO. Ver [revalidación](../evidencia/h3req1_revalidacion_hashes_2026-10-08.md), [resultado F2c](../evidencia/h3req1_c03_f1_daemon_diagnostic_f2c_2026-10-08.md),
[JIT F2d](../operaciones/manifiesto_jit_h3_close03_f1_diagnostic_f2d_2026-10-08.md) y
[estado vivo](../estado_del_proyecto.md).

Continuación 2026-10-07: [ruta y prompt reconciliados tras S1](../evidencia/planes_historicos/h3req1_ruta_ejecutable_go_pr_y_remoto_2026-10-06.md).
D2 consumido no obtuvo causa; S1 consumido falló snapshot antes de npm/workerd. Los
cortes inferiores conservan historia. Próximo: snapshot mínimo observable y JIT nuevo,
después smoke/integrado/gates finales; PR y remoto aún pendientes. Ownership tar es
hipótesis, no causa confirmada. No volver a ejecutar los permisos consumidos.

Continuación vigente por pedido humano 2026-10-06: [ruta detallada EXEC-01–06 del corte, ahora histórica, y prompt](../evidencia/planes_historicos/h3req1_ruta_ejecutable_go_pr_y_remoto_2026-10-06.md).
Los prompts inferiores conservan historia; usar la nueva ruta para diagnosticar,
probar arranque antes del drill y alcanzar readiness PR sin confundirlo con GO remoto.

## Corte anterior: R4/D1 NO-GO; D2 estático pendiente de JIT — 2026-10-06

JIT `H3-CLOSE-03-INTEGRATED-2026-10-06-R4` aprobado/consumido con manifiesto
`e5d72e06b04fcfd3f68abaeea77fef81c982f24e20e587732de65b63b58167a7` (62/62). Deno frozen y
verificación de digests de dependencias pasaron. El runtime integrado no llegó a `healthz`
tras 60 intentos en fase `isolated-workerd-bootstrap`; exit 1, **NO-GO**. Causa raíz no
determinada. No se alcanzaron PG17, PostgREST, user worker ni SQL. Recursos creados hasta el
runtime y log preservados; no hubo cleanup/resume. Durante R4 no hubo inspección post-fallo ni
acceso remoto. Diagnóstico/retry requieren un JIT independiente; R4 está consumido.

JIT D1 `H3-CLOSE-03-INTEGRATED-DIAGNOSTIC-2026-10-06-D1` aprobado/consumido con manifiesto
`19618493b6ecc5148dd6320a8c915f97563b3d79eea57507950b08928c38a914` (4/4). El único `docker
inspect` encontró `.Config.Image` distinto del literal digest fijado; el guard suprimió la
metadata y salió `NO-GO: R4 runtime image does not match the pinned digest` (exit 1). No confirma
si fue normalización de Docker o imagen distinta. No se obtuvo estado/OOM/exit ni causa del
timeout. No se leyeron logs, caches, redes ni volúmenes; el reporte quedó en
`../evidencia/h3req1_c03_integrated_runtime_diag_2026-10-06_d1.log` (SHA-256
`82cda545f327eb721fb1442ba91f962b5b3eb4b4e50a2a86e0c2e175f5a85347`). D1 está consumido;
cualquier inspect adicional, corrección del guard o retry requiere nuevo JIT/ciclo. Ver
[protocolo D1](../evidencia/h3req1_c03_integrated_protocol_preflight_2026-10-05.md).

Se preparó estáticamente D2 para evitar `.Config.Image` y consultar solo estado/exit/OOM/
log-driver del runtime exacto. Manifiesto de cinco inputs SHA-256
`6f6f4e451e45dec30c8145b2bb328286786aaf36d887635ae0be14f5e4547e6c`, runner SHA-256
`f337ed07de258c632c1cfcfa9f6292f8b1f19389bb06112fc5f8bec192e96447`. La auditoría inicial
detectó LOW por falta de guard del directorio `tests/`; se añadió antes de leer inputs. La
reauditoría cerró el hallazgo técnico y señaló un LOW documental por estado obsoleto, remediado
en el estado canónico en este ciclo. Sin HIGH/CRITICAL/MEDIUM técnicos. Gates `bash -n`,
`diff --check`, hashes 5/5 pasan. JIT D2 `H3-CLOSE-03-INTEGRATED-DIAGNOSTIC-2026-10-06-D2`
no aprobado.
Sin inspect/Docker ni logs en esta preparación; cualquier ejecución requiere aprobación nueva.

Lock R3 fijado: SHA-256 `ccb3d17f01947e679fb530ba7cbc9d252263ab1051d1d9ab21429eecde7ba428`;
runner SHA `28c417bee4bd0f3c0d9d1e576397c8be1af9e7d0309b81a58c1fcc4f3639f474`. Gates estáticos
finales y auditoría sin HIGH/CRITICAL/blockers; LOW de señales mitigado. El JIT aceptó egress
bridge general, lifecycle scripts Miniflare y ausencia de límites cgroup/cuota/timeout. R1/R2
no se inspeccionaron; cache/volumen R3 tampoco se montó. La salvedad antigua de lectura del
auditor bajo `tests/h3req1-c03-bootstrap/node_modules/.deno` permanece documentada y esa ruta
no se volvió a consultar. C02 v4 PASS y C03 SQL v3 PASS se preservan sin repetición. Evidencia:
[log R4 y protocolo](../evidencia/h3req1_c03_integrated_protocol_preflight_2026-10-05.md).

R3 conserva los recursos; no se accedió a su cache/volumen. La salvedad previa se mantiene:
una búsqueda del auditor leyó coincidencias en archivos locales generados bajo
`tests/h3req1-c03-bootstrap/node_modules/.deno`, sin modificarlos; no se inspeccionaron
volúmenes Docker R1/R2. No volver a acceder a esa ruta sin instrucción. C02 v4 PASS y C03 SQL
v3 PASS se preservan sin repetición. Ver
[protocolo R3/R4](../evidencia/h3req1_c03_integrated_protocol_preflight_2026-10-05.md).

## Resultado histórico R2 — NO-GO — 2026-10-06

JIT `H3-CLOSE-03-INTEGRATED-2026-10-06-R2` aprobado y consumido con SHA-256
`0e1634876956d8031ac99057dfc14936f65896b7a0d4626b642bfe8c4239aa11`. `sha256sum -c` verificó
62/62. Snapshot y ambos bootstrap npm completaron; Deno Edge falló exit 1 y el resumen seguro
reportó `lockfile-resolution-failure` junto con dos categorías no reconocidas. La causa
concreta sigue indeterminada. No hubo runtime/Edge integrado, PostgREST, PG17, SQL ni acceso
remoto. Recursos R2 y caches r4 preservados, potencialmente parciales; R1 r3 intactos, sin
inspección/reuso/cleanup. **No retry ni cleanup autorizado.** Evidencia:
[log R2 y protocolo](../evidencia/h3req1_c03_integrated_protocol_preflight_2026-10-05.md).

## Resultado histórico de ejecución C03 R1 — 2026-10-06

JIT `H3-CLOSE-03-INTEGRATED-2026-10-06-R1` aprobado para el SHA-256 de manifiesto
`a1073d93d22b8c01ed0e41031e4c1f41df33848eac1ff31935b223c80f47e101`; `sha256sum -c` verificó
62/62. Snapshot y los dos bootstrap npm completaron; el bootstrap Deno Edge falló con exit 1
(`isolated-deno-edge-dependency-bootstrap-with-registry-egress`, contenedor
`h3req1-c03-bootstrap-edge-deps-20261006-r3`: `exited|1|false`). El detalle de stderr no se
retuvo: el runner lo suprime y usa Docker `log-driver none`.

No se iniciaron runtime/Edge integrado, PostgREST o PG17 ni se ejecutó SQL; no hubo acceso
remoto. Sin cleanup/resume, los recursos y caches r3 quedan preservados, potencialmente
parciales. No reintentar ni limpiar sin una instrucción/JIT actualizado. C03 integrado sigue
**NO-GO**. Ver [protocolo y log](../evidencia/h3req1_c03_integrated_protocol_preflight_2026-10-05.md).

## Preflight estático anterior a JIT — 2026-10-06 (histórico)

C02 v4 (72/72) y C03 SQL v3 (41/41) siguen preservados y no se repitieron. El runner,
router Edge y fixtures integrados R1 están preparados y revisados estáticamente en
[`h3req1_c03_integrated_protocol_preflight_2026-10-05.md`](../evidencia/h3req1_c03_integrated_protocol_preflight_2026-10-05.md);
el snapshot de fuentes del manifiesto `tests/h3req1-c03-integrated.sha256` verificó 62/62
inputs, SHA-256 `a1073d93d22b8c01ed0e41031e4c1f41df33848eac1ff31935b223c80f47e101`; `bash -n` y
`git diff --check` terminaron con exit 0. En ese corte aún no se habían iniciado servicios
ni ejecutado SQL/tests o instalaciones npm. Los tres bootstraps usan Docker bridge con egress
general, sin allowlist FQDN; lifecycle de workerd y ese riesgo quedaron expresamente incluidos
en el JIT aprobado. No se reutilizaron los volúmenes Deno Edge r2.

## Registro histórico de cortes previos — no es el estado vivo

Revisión documental/read-only: 2026-10-05 local. Última sesión principal consultada:
`ses_ef11f2ae6ffepnyJCGOF2UxCTF`, «Continuación H3REQ1: gates de cierre y rollback integrado»;
mensaje final `msg_10f26155a001cKINVLwGfaemwF`, cierre 2026-10-06 UTC.
Estado: **NO-GO Development real; PR funcional todavía no listo**.

Revalidación posterior: C02 v4 **72/72** inputs no-C03 y C03 SQL v3 **41/41** hashes
vigentes. Package lock npm generado; Deno 2.9.7 resolvió el grafo y creó lock v5, pero
no es compatible con Deno 2.1.4 embebido en Edge Runtime v1.74.3. El cache no está
montado/exportado como artefacto offline. Los contenedores bootstrap están detenidos y
preservados; egress bridge se aceptó solo para las resoluciones autorizadas. El resolver
Deno 2.1.4 falló antes del lock porque el import npm requiere `node_modulesDir: auto`; su
contenedor y cache parcial permanecen preservados. Retry con `--node-modules-dir=auto` y
volúmenes nuevos aún requiere JIT exacto. La afirmación «runner integrado aún no está
preparado» que sigue corresponde al corte documental anterior a la actualización de
continuación que encabeza esta nota. Ver el [protocolo y resultado](../evidencia/h3req1_c03_integrated_protocol_preflight_2026-10-05.md).

**Actualización bootstrap (corte previo, 2026-10-06; reemplazada por la actualización de continuación al inicio):**
el JIT Deno 2.1.4 r2 generó lock v4 compatible, SHA-256
`ce8a4a433e58cc9a4cee0e908cb7b629305b58a790666e107d56f53a6a3548b1`, y llenó DENO_DIR
 y `node_modules` en volúmenes nuevos. El postinstall de workerd no se ejecutó; Node
Miniflare aún no estaba instalado. En ese corte no había runner/fixtures; no hubo ensayo.
Los recursos de bootstrap permanecen preservados.

## Tareas y gates de esta revisión

Consultar resultado de sesión, contrastarlo con fuentes/evidencia/recursos, consultar
Development/PR abiertos y actualizar próximos pasos. Gates: no ejecutar SQL, suites
funcionales, servicios ni writes remotos; preservar WIP y recursos; comprobar enlaces,
prompts y whitespace documental. Esta revisión no constituye auditoría integral de seguridad.

## Qué avanzó y qué falta

| Etapa | Avance acreditado | Pendiente / condición para avanzar |
|---|---|---|
| H3-CLOSE-01, candidato | Worktree y baseline definidos; WIP preservado | Inventario definitivo de inclusión PR; manifiestos separados de fuentes/build/resultados y trazabilidad cliente |
| H3-CLOSE-02 | PASS local v4 registrado para PG17/PostgREST, wire, replay y cuotas | Conservar evidencia por hashes/alcance; no repetir el permiso consumido ni confundir PASS local con enforcement remoto |
| H3-CLOSE-03 SQL | Nuevo PASS v3: captura ACL persistente, reconexión, rechazo de drift H3D01 y resume idempotente; cuatro procesos psql exit 0 registrados | El PASS v2 anterior es histórico para otros bytes; no reutilizarlo para el SQL actual |
| H3-CLOSE-03 integrado | Runner/fixtures R1 revisados estáticamente; SQL y PASS parciales previos preservados | **JIT exacto pendiente:** ensayo coordinado Pages/workerd + Edge + PG17/PostgREST, cookies/bindings, dispatcher y operaciones in-flight; recuperación sin bypass |
| H3-CLOSE-04–06 | Checks locales anteriores registrados, no repetidos aquí | Disposición de mantenimiento/owners/skips, tooling actionlint/shellcheck, build y UAT final/onboarding, revisión independiente y CI obligatorio efectivo |
| PR / integración | `desarrollo` remoto sigue en `4eb4d877a50b012bb630a129bd0c74482c33be9c`; consulta GitHub: ningún PR abierto hacia desarrollo | Congelar candidato validado, completar plantilla con resultados reales, aprobación separada para commit/push/PR según operación; review/CI y autorización de merge |
| Development remoto | Auth+MFA histórico se conserva | Desplegar/configurar bajo permisos separados, verificar artefacto/host/schema/Edge/Worker y ejecutar D01–D14; todavía no ejecutado por este candidato |
| Certification / Production | No ejecutadas | Solo después de GO Development real y nuevas instrucciones humanas |

No asignar un porcentaje: un único gate integrado pendiente puede bloquear todo el PR.

## Contraste con la sesión más reciente

- El resultado final de OpenChamber coincide con el estado vivo y el preflight: subgate
  SQL PASS, **C03 integrado NO-GO**, sin operaciones remotas ni cleanup.
- En esta revisión se recalcularon **41/41 hashes** del manifiesto C03 v3: cero discrepancias.
  Se inspeccionó el contenedor `h3req1-c03-safe-resume-pg17-20261005`: ID
  `6bd601683e6c1d036990b684f59cd6d2ae818f3fd36ff4f8c03e224ab9958b32`, en ejecución,
  red `none`, sin puertos publicados, tmpfs 1 GiB y tres mounts de candidato read-only.
  Esto corrobora fuentes/recursos, **no reproduce las aserciones del harness**.
- La API de mensajes devolvió solo mensajes del asistente; el filtro usuario devolvió
  vacío. La aprobación JIT y `continua` constan en la evidencia y en el relato de la
  sesión, pero esta revisión **no recuperó su texto humano original**. No es un permiso nuevo.
- Discrepancia documental: el manifiesto v3 aún comienza `PREPARADO_NO_APROBADO` y el
  preflight conserva frases «propuesta»/«necesita autorización» del corte anterior.
  La ejecución consumida está registrada después. Esos párrafos son históricos, no un
  pedido vigente de repetir SQL. Se aclara el preflight; se preservan los bytes del
  manifiesto aprobado, evitando cambiar su hash retrospectivamente. Consultar siempre
  el estado de ejecución en evidencia, no inferir autorización del documento propuesto.
- No se comprobó en esta revisión la configuración efectiva de branch protection,
  un deployment nuevo, logs remotos, D01–D14 ni el render de Obsidian.

## Secuencia ejecutable siguiente

Validación documental de esta revisión: 108 destinos locales existentes en siete notas;
fences/newline 7/7 PASS en Docker por stdin; `git diff --check` PASS. El primer comando
de fences falló por quoting PowerShell, se corrigió y terminó exit 0. No se repitieron
suites funcionales ni se validaron anchors, URLs externas o render Obsidian.

1. Preflight estático R1 cerrado: 62/62 hashes, `bash -n`, `git diff --check`, rama y HEAD
   verificados; antes de cualquier JIT, revalidar que no haya drift de rama/HEAD/recursos.
2. Presentar el JIT exacto R1, incluyendo bootstrap npm bridge (egress general), red
   interna del ensayo, fixtures sintéticos y ciclo de vida tmpfs; esperar aprobación humana
   separada. No crear recursos ni instalar paquetes antes de esa aprobación.
3. Tras JIT aprobado y `continua` asociado al ciclo, ejecutar normal -> suspensión coordinada ->
   rechazo de iniciadores/dispatcher ->
   cookies limpiadas -> finalizadores in-flight permitidos -> datos/auditoría/publicación
   pública preservados -> recuperar SQL verificado -> Edge -> Pages al final -> smoke.
   Rechazar drift manteniendo suspensión; sin tokens JS ni reapertura legacy. No declarar
   PASS si algún runtime se sustituye por mock sin explicitar cobertura faltante.
4. Tras C03 integrado PASS, cerrar mantenimiento/tooling y UAT/build/review del candidato
   final. Resolver HIGH/CRITICAL; justificar skips/warnings con owner y aceptación cuando
   corresponda. Acreditar CI independiente sin reducir protecciones. Su bootstrap remoto
   requiere aprobación separada; no bloquearlo silenciosamente ni afirmar enforcement local.
5. Congelar fuentes/build/resultados y lista PR, cerrar criterios/pilares/atestación,
   documentar expand -> compatibilidad -> deploy -> contract y rollback. Completar
   `.github/pull_request_template.md` con checks ejecutados y límites explícitos.
6. Solicitar push/PR, vincular el PR a la sesión al abrirlo, comprobar CI/review y pedir
   merge por separado. Después solicitar cambios DB/Edge/Cloudflare/Auth necesarios y
   despliegue Development por sus scopes exactos, sin reset/reinvitación implícitos.
7. Ejecutar D01–D14 del plan sobre Free y el host Development reales; registrar SHA,
   artefactos, configuración y resultados sanitizados. Corregir/revalidar hasta GO real
   o bloqueo concreto. Detenerse antes de Certification/Production.

## Prompt para nueva sesión

```text
continua con H3REQ1 en /home/romel/src/studiamatch-h3req1-sync-20261002,
rama feat/h3req1-sync-20261002. Lee AGENTS.md, .context/estado_del_proyecto.md,
.context/seguimiento/h3req1_estado_pr_y_remoto_2026-10-05.md,
.context/operaciones/plan_cierre_integral_h3req1_2026-10-04.md y el traspaso
enlazado, con atestación cliente y evidencia. Lista tareas y gates antes de editar.
Conserva H3-CLOSE-02 PASS v4 y C03 SQL safe-suspend/resume PASS v3 si sus
hashes/alcance siguen vigentes. V2 SQL es histórico. No repitas JIT consumidos.
Termina la revisión estática y el manifiesto de `tests/h3req1_c03_integrated_drill.sh`
R1 y sus fixtures. Presenta el JIT exacto `H3-CLOSE-03-INTEGRATED-2026-10-06-R1`, que
incluye bootstrap npm con egress bridge, workerd lifecycle y ensayo solo en red interna.
Espera aprobación humana separada y `continua` antes de instalar/crear/ejecutar. No
reutilices ni limpies recursos preservados.
Después de C03 PASS, completa H3-CLOSE-01 pendiente y H3-CLOSE-04–08: mantenimiento,
tooling, UAT/build final, seguridad/pilares/cliente, CI obligatorio efectivo, manifiestos
y plantilla PR real. Pide autorizaciones separadas para push/PR, merge, configuración
y despliegue Development; vincula cualquier issue/PR trabajado a esta sesión.
Ejecuta D01–D14 remotos solo con scopes aprobados. No cierres solo en PR_READY.
Este continua habilita el ciclo local, no SQL/grants, secretos, operaciones remotas,
Auth/reset, protección, workflow_dispatch, push/PR/merge/deploy, rollback/resume ni
cleanup. Explica decisiones en lenguaje sencillo y espera permisos exactos.
Trabaja en Docker contra el candidato; preserva original/WIP/evidencia y Auth+MFA
existente sin reinvitar ni reenrolar. Corrige/revalida y actualiza Obsidian enlazado.
No recuperes arquitectura histórica ni rediseñes gobierno general ahora.
Detente en GO Development real o bloqueo concreto con evidencia/decisión requerida.
No ejecutes Certification/Production; requieren instrucciones nuevas.
```

Referencias: [estado](../estado_del_proyecto.md),
[plan único](../operaciones/plan_cierre_integral_h3req1_2026-10-04.md),
[traspaso](h3req1_traspaso_avance_y_proximo_ciclo_2026-10-04.md),
[preflight y resultado SQL v3](../evidencia/h3req1_h3_close03_integrated_preflight_2026-10-05.md),
[manifiesto v3 preservado](../operaciones/manifiesto_jit_h3_close03_safe_resume_pg17_2026-10-05_v3.md).
