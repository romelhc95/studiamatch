# G0-R0-F10.9 - Baseline Protegido, Boundaries Y Context Graph

| Campo | Valor |
|---|---|
| ID | `G0-R0-F10.9` |
| Plan padre | [PLAN-REM-F10.9-001](./plan_remediacion_f10_9_fg2_fg3.md) |
| Subfase | `F10.9` |
| Estado | `COMPLETED_PASS_GO_G1_P2` |
| Autoriza ejecucion | `NO` |
| Gate siguiente | `G1/P2` requiere wiring integrado y autorizacion separada |

Freeze vigente: [R0-FREEZE-F10.9-2026-08-09](./r0_freeze_f10_9_2026_08_09.md).
Manifest del graph:
[R0-CONTEXT-GRAPH-F10.9-2026-08-09](./r0_context_graph_manifest_2026_08_09.md).

## Proposito

Obtener un baseline protegido y trazable antes de implementar P2. G0/R0 debe:

1. corregir los boundaries CI que bloquean las reconciliaciones F10.9;
2. preservar CA2 fuera del arbol activo sin perder su commit/tree;
3. restaurar ancestry `main <= certificacion <= desarrollo` mediante merge
   commits protegidos;
4. reconciliar el Context Graph heredado sin importar CA2 ni inventar contenido;
5. estabilizar e integrar P1 como un diff aislado;
6. demostrar checks post-merge verdes en `desarrollo`.

Este documento no concede pushes, PRs, approvals, merges ni cambios CI. Su
ejecucion requiere una autorizacion futura con la frase decimal exacta
`Ejecuta las tareas pendientes de la Fase F10.9` y alcance Git/CI remoto
explicito. Branch protection y review humano permanecen obligatorios.

## Baseline Congelado

Snapshot documental: `2026-08-09`.

| Objeto | Commit | Tree/estado |
|---|---|---|
| `main` observado | `ad89e8ab9575b37476502d6062e22c044ad6447b` | `54098b3ff581cc7728979afc8e6d47c9535141b5` |
| `certificacion` observado | `2a70dd001d8ded34d5ba67c19221f7f5e291d2c8` | Requiere reconciliacion con `main` |
| `desarrollo` observado | `8f4b4b0cbd8fd8ed096a34d8fa826f39ba6ec3fc` | `13d3926f21b65abc73d1e8ef6e4305b2d61e0c77` |
| Archive CA2 | `archive/f10-9-ca2-preserve-desarrollo-20260809@8f4b4b0cbd8fd8ed096a34d8fa826f39ba6ec3fc` | Tree `13d3926f21b65abc73d1e8ef6e4305b2d61e0c77` |
| Merge preparado `main -> certificacion` | `f8695f2463f5f8bf2d887bdd344f7f102afc13cd` | Parents baseline/source; tree `54098b3ff581cc7728979afc8e6d47c9535141b5` |
| Extraccion forward-only CA2 | `2c83cde5bc6e04f01c595a629e5694bd6de3e286` | Parent `8f4b4b0`; tree `54098b3ff581cc7728979afc8e6d47c9535141b5` |
| Merge preparado `certificacion -> desarrollo` | `4c4080ed95b407f2126f1908d171d2d73859f810` | Tree `54098b3ff581cc7728979afc8e6d47c9535141b5` |
| P1 referencia descartada | `8333102c44ea3278a05c3dad82763d55706b7e4f` | Tree `fab0ca1bbad12fd633b7574a44ab0a52ea00a1ac`; PR #330 cerrado como superseded, ancestry no reutilizado |
| Wiring P1 integrado | `4f47836a8c80bbab396e30ed65f424e58e772987` | PR #331 fusionado; checks post-merge PASS |
| P1 integrado | `53921e3ec845f4a248e586a0ecd667c64f4c070d` | PR #332 fusionado; tree `0344c649772aea18314fe022d5f24898e3dc03d0` |
| Wiring P2 integrado | `d5433ea9f810b0338513665bb95ba28715c6c8b5` | PR #333 fusionado; tree `24a270f314b46728d5ae9847dafba0ff1999be7f`; checks post-merge PASS |

Estos valores son anchors de diagnostico, no autorizaciones. Un cambio remoto
antes de ejecutar G0 obliga a recalcular heads, parents y manifests. No se
actualiza silenciosamente ningun SHA congelado.

## Blockers Resueltos En G0

### B1 - Security Audit No Reconoce F10.9

El agregador de `.github/workflows/security-audit.yml` trataba toda transicion a
`certificacion` como un baseline historico enumerado. Si ningun flag `*_REQUIRED`
coincide, produce `certification-transition: unsupported baseline`.

### B2 - F9.7 Contract Interpreta R0/P1 Como Drift Historico

`.github/workflows/f9-7-contract.yml` ejecutaba el boundary F9.8 para PRs y pushes
de `desarrollo`. Su allowlist/protected-prefix logic interpreta la extraccion
CA2 y los nuevos `scripts/shared/**` de P1 como drift F9.7/F9.8.

### B3 - Context Graph Selectivo Incompleto

El tree inicialmente observado de `origin/main` contenia `11` archivos Markdown bajo
`.context`, `135` enlaces locales y `78` targets heredados ausentes. Los seis
targets tocados por la documentacion F10.9 existen, pero el graph global queda
`BLOCKED_INHERITED_CONTEXT_GRAPH`. R0 termino con `42` Markdown, `341` enlaces
locales y `0` rotos.

### B4 - P1 Requiere Estabilizacion

P1 fue reconstruido desde el tip protegido post-wiring, cerro los findings de
transporte/retries, paso las suites focused y de regresion y quedo integrado por
PR #332 con checks post-merge verdes.

## Frontera G0/R0

Permitido solo despues de autorizacion especifica futura:

- modificar boundaries CI y sus tests offline;
- generar manifests de reconciliacion y Context Graph;
- restaurar/repoint/remove enlaces conforme a clasificacion aprobada;
- actualizar ramas de PR mediante merge normal;
- solicitar review humano y fusionar manualmente en orden aprobado;
- estabilizar P1 dentro de sus cinco paths exactos.

Prohibido en G0/R0:

- force-push, rebase de ramas publicadas, reset o bypass de branch protection;
- auto-approval, auto-merge o aprobacion del propio ultimo push;
- DDL/DML, Supabase, Free/Pro, backup/restore o datos operativos;
- schedules, dispatches, retries, reruns o cambios de environments/secrets;
- runtime P2-P7, backfill o re-enrichment;
- importar `db/**`, `supabase/**`, `web/**` o runtime CA2;
- inventar documentos ausentes o reclasificar evidencia historica como PASS.

## Paso 0 - Revalidar Autoridad Y Freeze

Antes de editar:

1. Confirmar que `F10.9=IN_PROGRESS_BLOCKED_BY_INCIDENT` en la autoridad viva.
2. Confirmar heads protegidos y comparar con el baseline congelado.
3. Confirmar que no existe otro PR/merge concurrente que cambie los parents.
4. Verificar el archive CA2 por commit y tree.
5. Capturar `git status`, `git worktree list`, branch protection y checks
   requeridos sin leer secrets.
6. Congelar manifest `R0-FREEZE` con timestamp UTC, repositorio, base/head/tree y
   estado de PRs/checks.

Branch protection debe revalidarse otra vez inmediatamente antes de cada merge
y despues de cada merge. Cualquier diferencia invalida `R0-FREEZE`.

Stop conditions:

- archive CA2 ausente o tree distinto;
- cambio de head protegido no explicado;
- worktree con cambios no atribuibles;
- branch protection debilitada;
- secreto o dato operativo en logs/manifests.

## Paso 1 - Implementar Boundary CI F10.9

### 1.1 Job Bloqueante En Security Audit

Agregar un job dedicado, por ejemplo `f109-branch-reconciliation`, y agregarlo a
`needs` del agregador `security-audit`. El agregador debe exigir `success` solo
cuando un modo F10.9 exacto aplique y mantener el fallback actual fail-closed.

Modos minimos:

| Modo | Evento/target | Invariantes |
|---|---|---|
| `F109_CERT_RECONCILIATION` | PR/push a `certificacion` | Baseline protegido exacto, source `main` exacto, same-repository, anchor merge con parents/tree esperados y delta posterior allowlisted. |
| `F109_DEV_RECONCILIATION` | PR/push a `desarrollo` | Archive CA2 exacto, parent original de `desarrollo`, tip protegido final de `certificacion` como ancestro y tree final identico a certificacion. |
| `F109_P1` | PR/push a `desarrollo` post-R0 | Parent igual al tip protegido post-R0 y diff exacto de cinco paths P1. |
| `F109_CONTEXT_GRAPH` | Dentro de R0 | Manifest aprobado de paths `.context`, provenance por blob y cero targets rotos finales. |

La deteccion no puede depender solo del nombre de rama. Debe atar:

- event type y base ref;
- repository head/base iguales al repositorio del evento;
- base SHA, head SHA y parents validos;
- ancestry requerida;
- tree y blob modes;
- allowlist exacta por modo;
- manifest digest esperado.

### 1.2 Boundary F9.7

Modificar `.github/workflows/f9-7-contract.yml` para seleccionar primero los
modos exactos F10.9. Solo cuando ninguno aplique se ejecuta el boundary historico
F9.8 actual.

Reglas:

- no omitir la suite congelada F9.7/PostgreSQL 17;
- cambiar solo la validacion del delta de transicion;
- no agregar skip por actor/admin;
- no permitir `scripts/shared/**` globalmente;
- P1 permite exclusivamente sus cinco paths y statuses/modes esperados;
- R0 Context Graph permite exclusivamente paths presentes en su manifest;
- cualquier path adicional produce salida no cero.

### 1.3 Tests Del Boundary

Crear `tests/test_fase10_9_branch_reconciliation.py` y actualizar solamente los
tests legacy estrictamente afectados.

Casos obligatorios:

- cert reconciliation valida parents/tree/same-repository;
- dev reconciliation valida archive, ancestry y tree equality;
- P1 acepta exactamente cinco paths y rechaza un sexto;
- Context Graph acepta solo manifest aprobado;
- PR y push post-merge quedan cubiertos;
- baseline, head, parent, mode, blob o digest incorrectos fallan;
- fork, actor bypass, auto-approval y auto-merge no existen;
- `security-audit` agrega el job nuevo como requisito duro;
- el boundary `certificacion -> main` previo conserva su contrato;
- la assertion legacy global sobre `merge-base` se limita al bloque que realmente
  debe permanecer exact-tip, sin prohibir ancestry checks de R0.

### 1.4 Atestacion Independiente Del Workflow Que Se Modifica

El required check no puede ser su unica prueba porque R0 modifica el workflow que
lo genera. Antes del primer push se congela un validator independiente fuera del
diff R0, ligado por SHA-256 y ejecutado desde un checkout limpio/container. Ese
validator debe comparar el workflow candidate contra las invariantes de este
runbook y producir una atestacion sanitizada.

Ademas del status check se requieren:

- security-auditor independiente sin permisos de merge;
- reviewer humano distinto del autor del ultimo push;
- atestacion del validator congelado con digest y resultado PASS;
- revision manual del diff completo de workflows y branch protection.

Un cambio al validator, a su digest o a este contrato despues del freeze produce
STOP. No se permite que el PR candidate reemplace el validator y se autoateste.

## Paso 2 - Reconciliar Context Graph

### 2.1 Inventario Reproducible

Generar un inventario ordenado de todos los enlaces locales `.context` desde el
tip protegido que servira de candidate. Para cada target ausente registrar:

```text
source_path
source_line
target_path
classification
source_commit
source_blob
proposed_action
proposed_target_blob
review_status
```

El manifest privado puede contener paths internos; la evidencia publica conserva
conteos, categorias, commit/tree y digest, sin identificadores operativos.

### 2.2 Clasificacion Obligatoria

| Clasificacion | Accion permitida |
|---|---|
| `RESTORE_CA1_CANONICAL` | Restaurar byte-identico desde un commit protegido cuya vigencia CA1 este demostrada. |
| `RESTORE_HISTORICAL_REFERENCE_ONLY` | Restaurar byte-identico solo si el blob original ya declara de forma inequívoca su estado historico/no ejecutable. Si no lo declara, usar HOLD y decision de repoint/remove; no modificar el blob y llamarlo byte-identico. |
| `REPOINT_TO_EXISTING_CANONICAL` | Cambiar el enlace a una autoridad vigente ya presente, preservando semantica. |
| `REMOVE_STALE_LINK` | Retirar el enlace roto sin retirar evidencia necesaria; requiere razon y review. |
| `HOLD_CA2` | No importar contenido; mantener fuera del candidate hasta decision humana de repoint/remove. |
| `HOLD_UNKNOWN_PROVENANCE` | STOP; no inventar ni reconstruir por inferencia. |

No se restaura por nombre de archivo solamente. Cada restauracion exige commit,
blob, clasificacion y prueba de que no activa CA2 ni contradice el estado vivo.

### 2.3 Denylist Context Graph

El package no puede introducir:

- migrations, manifests DB, SQL o tooling de apply;
- snapshots con URLs, UUIDs, payloads o hosts;
- instrucciones ejecutables superseded sin tombstone/historical status;
- estados paralelos que contradigan `estado_del_proyecto.md` o `TASK-H1-001`;
- documentos CA2 activos; los antecedentes solo pueden ser historical/reference.

### 2.4 Gate Del Graph

Ejecutar el validador sobre el tree materializado, no solo el working tree.

```text
markdown_files_scanned > 0
local_links_scanned > 0
broken_local_targets = 0
duplicate_live_authorities = 0
hold_unknown_provenance = 0
active_ca2_documents_added = 0
new_sensitive_identifiers = 0
```

El digest del inventario after debe quedar ligado al commit/tree candidate.

## Paso 3 - Validacion Local Del Package R0

Ejecutar dentro de Docker:

1. tests del boundary F10.9;
2. `tests/test_fase10_main_boundary.py`;
3. tests F9.7/F9.8 congelados aplicables;
4. Context Graph y enlaces;
5. `actionlint 1.7.7` sobre todos los workflows;
6. `ShellCheck 0.9.0` sobre shell standalone y embebido detectado;
7. credential scan y security-auditor;
8. `git diff --check` y verificacion de modes/blobs.

No se permite declarar `actionlint`/ShellCheck no aplicable porque R0 modifica
workflows. No se ejecutan workers, npm, Supabase ni proveedores externos.

## Paso 4 - PR #329 Main A Certificacion

1. Incorporar el package CI/Context Graph validado a la rama de #329 mediante
   commits forward-only.
2. Regenerar manifest con baseline/source, anchor merge, delta allowlisted,
   head/tree final, status/mode/blob por path y digest.
3. Confirmar same-repository y cero paths fuera del package.
4. Esperar todos los checks requeridos en PASS.
5. Revalidar branch protection y la atestacion independiente inmediatamente
   antes de solicitar aprobacion.
6. Solicitar aprobacion humana despues del ultimo push.
7. Fusionar mediante merge commit humano; no squash/rebase/auto-merge.
8. Revalidar branch protection y registrar merge SHA/tree y checks post-merge de
   `certificacion`.

Si #329 cambia durante review, la aprobacion y el manifest quedan stale.

## Paso 5 - PR #328 Certificacion A Desarrollo

Solo despues del merge humano de #329:

1. Fetch del tip protegido final de `certificacion`.
2. Merge normal de ese tip en la rama de #328; no rebase ni force-push.
3. Revalidar archive CA2 commit/tree.
4. Confirmar que el tip certificado final es ancestro del head.
5. Confirmar tree final identico al tree de `certificacion`.
6. Regenerar manifest y Context Graph sobre el nuevo tree.
7. Esperar CI PASS y revalidar branch protection/atestacion independiente.
8. Obtener aprobacion humana posterior al ultimo push.
9. Fusionar mediante merge commit humano a `desarrollo`.
10. Revalidar branch protection y registrar merge SHA/tree/checks post-merge.

## Paso 5A - Wiring CI P1 Post-R0

Despues del merge humano de #328 y antes de tocar runtime P1:

1. congelar `desarrollo` post-R0 y su tree;
2. crear `ci/f10-9-p1-boundary` desde ese tip protegido;
3. habilitar modos fail-closed para el PR de wiring, P1 PR y push protegido;
4. exigir same-repository, tip protegido vigente, parent/first-parent y allowlist
   exacta de cinco paths P1;
5. mantener P1 runtime y #330 sin cambios;
6. ejecutar validator independiente porque el package modifica su propio CI;
7. abrir PR a `desarrollo` y esperar aprobacion humana posterior al ultimo push.

El wiring no declara G0 PASS ni autoriza reconstruir P1 antes de su merge y
checks post-merge.

## Paso 6 - Reconstruir Y Estabilizar P1

Solo despues del merge humano del wiring P1 (#331):

1. Crear una rama nueva desde el tip protegido post-R0 de `desarrollo`.
2. Aplicar semanticamente P1 sin reutilizar ancestry apilada de #330.
3. Cerrar los findings SSRF/retries del plan padre.
4. Mantener el diff exacto de cinco paths P1.
5. Ejecutar tests P1, `py_compile`, regresion, credential scan y
   security-auditor.
6. Abrir PR protegido a `desarrollo`; #330 puede quedar superseded, nunca
   force-pusheado para ocultar su historia.
7. Esperar CI PASS y revalidar branch protection/atestacion independiente.
8. Obtener aprobacion humana posterior al ultimo push.
9. Fusionar manualmente, revalidar branch protection y verificar checks
   post-merge.

Resultado: completado por PR #332. Candidate
`e9fb19a217cf1ad3bd9924afb0d3bdbebed7a694`; merge
`53921e3ec845f4a248e586a0ecd667c64f4c070d`; tree
`0344c649772aea18314fe022d5f24898e3dc03d0`; Security Audit
`31350585499=success`; F9.7 Contract `31350585516=success`.

## Manifests R0

| Manifest | Contenido minimo |
|---|---|
| `R0-FREEZE` | Heads/trees iniciales, branch protection, PR/check state y archive CA2. |
| `R0-CI-BOUNDARY` | Modos, baselines, parents, allowlists, workflow/test blobs y digest. |
| `R0-CONTEXT-GRAPH` | Inventario before/after, clasificaciones, provenance, actions y digest. |
| `R0-CERT-MERGE` | PR #329 head, merge SHA/tree, parents, checks y approval posterior al ultimo push. |
| `R0-DEV-MERGE` | PR #328 head, archive attestation, tree equality, merge SHA/tree y checks. |
| `R0-P1` | Parent protegido, cinco paths, status/mode/blob, tests, PR/merge SHA/tree y digest. |

La evidencia versionada debe ser sanitizada. Los manifests privados no se
publican ni se copian a artifacts publicos.

## Criterios De Salida G0

G0 termina `PASS` solo si todos son verdaderos:

```text
f10_9_authority_still_active = true
ca2_archive_commit_tree_match = true
main_is_ancestor_of_certificacion = true
certificacion_is_ancestor_of_desarrollo = true
certificacion_post_merge_checks = success
desarrollo_post_merge_checks = success
security_audit_f109_boundary = success
f9_7_contract_f109_modes = success
independent_frozen_validator = success
context_graph_broken_local_targets = 0
context_graph_unknown_provenance_holds = 0
active_ca2_paths_added = 0
p1_diff_paths = exact_five_path_allowlist
p1_security_auditor_blockers = 0
p1_post_merge_checks = success
human_approval_after_each_last_push = true
force_push_rebase_auto_merge_auto_approval = 0
remote_data_operations = 0
```

Resultado alternativo: cualquier predicado falso produce `G0=STOP`, no
`PARTIAL_PASS`. P2 permanece prohibido hasta resolverlo y emitir un manifest G0
nuevo.

Resultado observado: todos los predicados quedaron verdaderos. G0 termina
`PASS/GO_G1_P2`. Este resultado habilita preparar el boundary de G1, pero no
autoriza implementar P2, acceder a red remota ni operar data plane.

El boundary G1 fue integrado posteriormente por PR #333. La autorizacion
decimal separada para G1/P2 se limita a implementacion local read-only/offline;
no modifica el resultado historico G0.

## Evidencia De Entrega

Al terminar G0 deben presentarse:

- SHA/tree protegido final de `main`, `certificacion` y `desarrollo`;
- commit/tree del archive CA2;
- manifests R0 y sus digests;
- lista exacta de paths Context Graph restaurados/repointed/retirados/HOLD;
- conteo before/after de enlaces rotos;
- resultados Docker, actionlint, ShellCheck, credential scan y security-auditor;
- PR/merge/check/review state de #329, #328 y P1 reconstruido;
- declaracion `GO_G1_P2` o `NO_GO_G1_P2`.

Este documento no cambia `EVID-H1-011..013/016`, no inicia observacion y no
autoriza G1/P2.
