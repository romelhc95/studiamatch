# Estado del proyecto

**Validación local z30 (histórica) — PASS en Docker/red deshabilitada:** escáner árbol+diff PASS sin findings; documentación/self-test PASS (732 fuentes, 9.247 enlaces, 4.625 anchors); guard/scope/negativos PASS (1.196 rutas, 13 catálogos/1.173 refs, negativos 3/1/1/3/2); plantilla PASS (10 headings, 10 enlaces, 16 filas, cero placeholders); contrato de estado 8/8; identidad exacta PASS (9/9 hashes Worker y 798 archivos no contextuales iguales a z20); delta z29→z30 PASS en cuatro archivos `.context/`. actionlint, ShellCheck, Python focal 46/46 y suites Worker se reutilizan por inputs idénticos. El diff desde baseline se puede comprobar tras restaurar el objeto, pero conserva 125 diagnósticos de formato del paquete (107 trailing whitespace, 18 blank-EOF); no se reformatearon fuentes históricas. No equivale a checks GitHub ni aceptación Development.

> Autoridad operativa única. Este documento contiene el corte vigente, sus resultados, pendientes y siguiente paso. La historia detallada vive en hitos, decisiones y evidencia enlazados desde el índice Obsidian.

## Corte vigente

### Preparación local de evidencia H2 — run 91 (2026-11-01)

PR #521 está integrado. Refs confirmadas en este corte: Desarrollo
`64c23fd8a9694f50a2728399bf8e35771bf56fad`, Certification
`605a6ecca29e20ade8cac3874d380758d18e6a11` y main
`70d0f4fee885be0f6780e5d14f466b2a6c897961`. El deployment normal de
Certification `ac707175-75a9-4c5a-9c6b-0786a6a0d517` terminó SUCCESS. La rama de
trabajo es un clon aislado desde Desarrollo en
`/tmp/studiamatch-h3req1-run91-evidence-20261101`, local
`codex/h3req1-run91-evidence-20261101`; el checkout fuente con WIP y los
checkouts TL siguen intactos.

DB Sync run #91 (`41338753002`) fue `workflow_dispatch`, ref `certificacion`,
SHA `605a6ecca29e20ade8cac3874d380758d18e6a11`, SUCCESS. Report pending
migrations dry-run informó cero pendientes. El job Apply terminó SUCCESS como
NO-OP; el paso `Apply migrations to Pro` quedó SKIPPED. `Verify target schema`
y la subida del artefacto fueron SUCCESS. El resultado aplica solo a H2
`h2-expand-compat`: cohorte 224, digest
`sha256:c217dbffc9d50cca0e1f111fcddf1268db9a34e8671a409f3663dcfff1d735e9`.
No se aplicaron migraciones H3 ni se hicieron writes SQL.

El artefacto autenticado `13096761150` (run
[41338753002](https://github.com/romelhc95/studiamatch/actions/runs/41338753002))
tiene ZIP SHA-256
`f7e3ac3a735013f2b3959b668b72913526e51c24dde063ee4c714613d69a5895` y los tres
miembros esperados. El JSON canónico fue copiado byte por byte del miembro
`h2-production-expand-verify-evidence.json`: SHA-256
`563de170bbce697408413a212f39d8592238749856a0c6652e0bea4ce8051195`; el ZIP y
la fuente autenticada son idénticos. Se preserva la etiqueta histórica
`operation=apply` que requiere el gate main; el dispatch remoto fue `verify` y
Apply fue NO-OP. Advisors: 12 de seguridad y 17 de rendimiento; fingerprints
idénticos al baseline, sin HIGH/CRITICAL/ERROR, con INFO/WARN conservados.
Run 89 permanece como historia y no se reutiliza como evidencia actual.

Se actualizaron el JSON canónico, el checkpoint, el estado/índice, fichas,
registro y borrador DDL. Este último permanece `DRAFT_NOT_AUTHORIZED`. La ruta
JSON ya tiene admisión exacta en el guard; su contenido sigue sujeto al gate
independiente de run/jobs/ancestry/ZIP. No se regeneraron pins congelados: sus
baselines anteriores no cambiaron y los callers omiten esos pins en baselines
sucesores usando las allowlists ordinarias. No se cambió código, workflow, guard
ni scope.

Validaciones finales del paquete local se registran en el checkpoint enlazado. Docker sin red: render del registro PASS; suites focales de gate/selector 56/56 PASS; test_protected_path_scope_guard.sh PASS con callers PR/push, selector, pins, acumulado y negativos; scanner de credenciales árbol/delta PASS; git diff --check PASS; artefacto run 91/JSON auténticos verificados byte a byte. Checker integral sin truncar: baseline 348 y candidato 348, 0 nuevos/0 resueltos; self-test PASS, comando integral exit 1 por deuda heredada. Candidate-aware PASS, exit 0. No se repitieron CA4 6/6, R1–R4 4/4 ni smoke Certification 1/1. H3 Pro sigue no aplicado/no verificado; M y P aún no existen; sin commit, push, PR, merge, dispatch, SQL, configuración ni deploy.

### Corte histórico previo a PR #521 — admisión H3 Pro corregida localmente

El paquete local conserva el DDL H3 en `DRAFT_NOT_AUTHORIZED` y admite solo su
ruta exacta. La revisión TL consolidó la evidencia en el checkpoint ya admitido
y trasladó las regresiones a `tests/test_security_flow.py`, que CI ejecuta.
Los fixtures DRAFT/aprobado no fijan permanentemente el estado del documento real.
Docker sin red: 20/20 funciones con DRAFT y 20/20 con estado aprobado sintético;
suite histórica PASS en baseline y candidato tras recuperar los blobs históricos
faltantes del clon parcial, sin cambiar esa suite. Guards, selectores y gates
documentales acotados de Desarrollo/Certification/main PASS; scanner y diff-check
PASS. Integral FAIL 348/348 conservado. Revisión focal: cero HIGH/CRITICAL/P1/P2.
No hubo commit, push, PR, merge, SQL, dispatch ni configuración. Falta publicar e
integrar el guard, obtener nuevo report/verify H2 autorizado en Certification y
consolidar evidencia antes de P. No es GO remoto ni cierre productivo.

### Corte histórico previo a run 91 — admisión exacta de autorización H3 Pro

Refs verificadas por GitHub: Desarrollo `ca63eb4d82bfb1d34f7c7b753942a93039cfe2bc`, Certification `15fdc8dc97933dcc6a77dff65d6b293faadeb2ee` y main `70d0f4fee885be0f6780e5d14f466b2a6c897961`. El trabajo parte de Desarrollo en un checkout aislado con historia completa; los checkouts de TL y el checkout fuente con WIP no se modificaron.

El delta local admite en `scripts/security/protected_path_scope_guard.sh` únicamente la ruta `.context/operaciones/ddl_authorizations/DDL-H3-EDITORIAL-EXPAND-PRO-20261101.md`. El documento permanece `DRAFT_NOT_AUTHORIZED` y no contiene aprobación ni valores dinámicos pendientes declarados como reales. El workflow de apply conserva sus comprobaciones independientes de estado aprobado, identidad, manifest, payload, base/ancestría, digest/cohorte y gates de Backup/PITR/Production. No se cambió el workflow ni se habilitó `apply`.

Las regresiones focales `tests/test_security_flow.py` pasan 11/11 al invocar sus funciones en el contenedor (la imagen no trae pytest). El guard real acepta solo la ruta exacta y rechaza vecinos; los fragmentos reales del workflow rechazan DRAFT/traversal y archivos extra después de `P`. El script amplio `tests/test_protected_path_scope_guard.sh` aún falla tanto en candidato como en baseline completo porque su destino histórico `8ac174d81cf6ce23658bff132236a78935ace1ad` no contiene `.context/componentes/admin_portal.md`; ese fallo es heredado y no se alteró para obtener verde. Scanner de credenciales árbol/delta, sintaxis Bash, render y `git diff --check` pasan. ShellCheck no está instalado en la imagen.

Checker documental: integral FAIL 348 en baseline y 348 en candidato, con las mismas líneas de diagnóstico; `DOC_SELF_TEST_PASS` aparece en ambos, pero el proceso termina 1 por el FAIL integral. No se declara candidate-aware PASS. Codex Security diff scan `8e2f7b24-fd9b-4cd9-8b60-73d9e2929ad5` completado: cero hallazgos reportables, 3/3 superficies `no_issue_found`, limitado al diff local; su reporte y las limitaciones quedan en el [checkpoint del paquete local](evidencia/h3req1_protected_path_scope_fix_2026-10-31.md). Se reutiliza la evidencia previa del run 89 y no se afirma que cubra el guard nuevo; después de integrar el guard a Certification se requieren report y verify H2 nuevos, cada uno con JIT propio. La evidencia auténtica, JSON, pins y documentos deben quedar en el payload antes de `P`; luego la autorización humana cambiará solo el archivo DDL.

Este ciclo no ejecutó commit, push, PR, merge, SQL remoto, dispatch, configuración ni deploy. No repitió CA4 mínimo 6/6, Development 4/4 ni smoke histórico Certification 1/1. Integral documental y regresiones acotadas se mantienen separadas; el cierre productivo no se acredita. Próximo paso: completar revisión de seguridad por impacto y entregar al TL diff, negativos, rollback y límites para revisión. No habilitar FG1/FG2/FG3, writers, schedules ni H1/H4.

### Corte histórico — corrección del historial del gate main (PR #518)

PR #518 está integrado en Desarrollo `893f41fa8ef9f6ee9ad6799824a48abc0bf922c3`.
Certification sigue `15fdc8dc97933dcc6a77dff65d6b293faadeb2ee` y main
`70d0f4fee885be0f6780e5d14f466b2a6c897961`. La promoción documental autorizada
se mantiene sin crear al detectarse un bloqueo adicional de CI para main.
El checkout depth 1 del job H2 no recupera el ancestro verificado tras el fetch
de PR/main; una reproducción Git real falló con `Not a valid object name`.
El fix local añade únicamente `fetch-depth: 0` a ese checkout y una regresión
ejecutable en `tests/test_security_flow.py`. RED antes del fix, GREEN después;
16 pruebas security_flow PASS en Docker sin red. No cambia contrato de datos,
roles, producto ni las validaciones de evidencia. Ambas rutas están permitidas
por el gate post-verify; se conserva la evidencia auténtica del run 89 y su
ancestría. No se repite verify ni aceptación mínima 6/6.
La revisión focal de seguridad no observó HIGH/CRITICAL/P1/P2; no es auditoría
global ni CI remota. Los gates finales se registran en el paquete TL antes de
solicitar publicación. La aprobación de promoción de `893f41f` no cubre publicar
este nuevo delta. No se ejecutó push, PR, merge, SQL, dispatch ni configuración.
Transición: expand = historial completo para resolver ancestry; compatibilidad =
mantener schema/artefacto y todos los checks de run/jobs/ZIP; deploy = PR protegido;
contract = sin legacy de producto nuevo; rollback = revert protegido del fix,
sin DB afectada. Detalle en el [checkpoint](evidencia/h3req1_protected_path_scope_fix_2026-10-31.md).

### Corte histórico — evidencia auténtica del verify H2 Pro run 89 y paquete documental (supersedido por run 91)

PR #517 quedó integrado en Certification. Las refs remotas leídas en esta continuación son Desarrollo `9c2e227078ca75714a215f7f0f43be3b837bda69`, Certification `15fdc8dc97933dcc6a77dff65d6b293faadeb2ee` y main `70d0f4fee885be0f6780e5d14f466b2a6c897961`. Certification conserva el merge 15fdc8d con Desarrollo como ancestro y ambos tienen el árbol `8fd6932b81dfb2d86d355d13ebcf5bd98676bcce`; no existe conflicto de producto por la divergencia de main. Deployment normal de Certification `8960fc62-0fd8-4760-87c9-1c0b682c8e75` terminó SUCCESS en `certificacion.studiamatch-aty.pages.dev`.

DB Sync to Production run 89 es `41274863913` ([enlace correcto](https://github.com/romelhc95/studiamatch/actions/runs/41274863913)); el run `41241415710` corresponde al reporte 88 y no se cita como verify 89. El run 89 tuvo 6 jobs SUCCESS y 1 SKIPPED: el modo verify fue confirmado como NO-OP por Apply pending migrations, Apply migrations to Pro quedó SKIPPED y Verify target schema fue SUCCESS. El workflow informó Target schema check PASSED para `h2-expand-compat`, candidato `15fdc8dc…`, cohorte 224 y digest `sha256:c217dbffc9d50cca0e1f111fcddf1268db9a34e8671a409f3663dcfff1d735e9`. H2 figura verificado en ese alcance; esta ejecución no acredita H3 instalado en Pro.

El TL autenticó el artefacto 13070419512 (digest ZIP `sha256:2bc61bde47b79ae30876c3b1d71598e3a3fc70f56a22c90f4bc2be17f1c3ecef`) y conserva los tres miembros en `/tmp/h3req1-tl-audit-20261101/`. `.context/operaciones/h2_main_production_expand_evidence.json` fue reemplazado byte por byte desde el miembro auténtico, SHA-256 `d38900871fcdf075a9ce7111820cf27757c26cf854d439cada1bbb52750be41c`; los hashes de ambos informes advisors y su alcance están en la [sección verify 89 del checkpoint](evidencia/h3req1_protected_path_scope_fix_2026-10-31.md). Se preserva `operation=apply` del schema histórico que consume el gate; no se editó el generador ni el workflow. El dispatch real fue `verify` y Apply fue NO-OP. No se versiona el ZIP ni los cuerpos crudos de advisors.

Este checkout es `/tmp/studiamatch-h3req1-verify-evidence-20261101`, rama local `codex/h3req1-verify-evidence-20261101`, con HEAD `15fdc8dc97933dcc6a77dff65d6b293faadeb2ee`; se inició desde Desarrollo `9c2e227…` y avanzó por fast-forward local hasta Certification, conservando 15fd como ancestro. El checkout WIP original no se modificó. El paquete local tiene seis rutas, todas documentales, y permanece sin commit/publicación. Para los gates que requieren HEAD se usó un fixture Git desechable derivado de `15fd`, con el mismo contenido de las seis rutas documentales; su identidad temporal consta en los logs de `/tmp`, no es SHA candidato de PR.

Se reutilizan sin repetición las aceptaciones vigentes: E1–E6 local 6/6, R1–R4 Development 4/4 y smoke histórico Certification 1/1. No se repitieron onboarding, cuotas ni UAT. No se volvió a ejecutar el reporte 88 ni verify 89; run 89 ocurrió antes de esta preparación documental. En este ciclo no hubo nuevas escrituras SQL, dispatch, push, PR, merge, cambios de configuración ni deploy.

| Etapa | Estado de este corte | Siguiente acción |
|---|---|---|
| Verify H2 Pro | Acreditado para el candidato y cohorte registrados; Apply fue NO-OP. | Preservar el artefacto auténtico y no repetir verify sin invalidación concreta. |
| H3 Pro / Pages-BFF | No instalado ni verificado por run 89. | Preparar JIT separados después de integrar el paquete y revisar el gate Certification→main. |
| Documentación local | Scanner de árbol/diff, diff-check, render, guardas de las tres rutas, selectores, artefacto y candidate-aware main PASS; integral 348→348 FAIL, self-test PASS, sin delta. | Mantener visible el FAIL integral y someter la disposición limitada a decisión humana. |
| Integración | Sin commit, push, PR ni merge. El TL crea los PRs. | El TL decide la disposición propuesta y solicita por separado la autorización de publicación del paquete exacto. |

El checker normal usó el mismo código/configuración en baseline Desarrollo `9c2e227…` y candidato documental local: integral FAIL 348→348, cero diagnósticos introducidos y cero resueltos. `DOC_SELF_TEST_PASS` aparece en ambos; el comando sale 1 porque conserva el FAIL integral. La comparación no truncada confirma las mismas clases residuales de rutas históricas faltantes/retiradas y referencias incompletas. Candidate-aware para Certification→main: PASS separado; el selector vigente agregó cuatro paquetes/1.628 rutas al fixture local. No es prueba remota ni convierte el integral en PASS.

En Docker `studiamatch-dev:local`, red deshabilitada: scanner de árbol y diff, `git diff --check`, render del registro, tres comparaciones del guard (feature→Development, Development→Certification, acumulado Certification→main), tres selectores y comprobación local del artefacto terminaron PASS. El ZIP de run 89 conserva digest GitHub `2bc61b…3ecef`, tres miembros y JSON idéntico al canónico (`d3890087…be41c`). El contrato de `security-audit.yml` mantiene las verificaciones de SHA/ancestría, metadatos del run, jobs y descarga/comparación del artefacto; los metadatos/jobs del run 89 se reutilizan del informe TL, sin nueva consulta ni dispatch.

El inicio normal de la imagen abortó antes de pruebas porque sus manifests Node no coinciden con los manifests de la app. No se contó como test. Los checks exclusivamente documentales se ejecutaron después en la misma imagen con Bash/Node/Python, red deshabilitada, sin iniciar la app, sin volumen de dependencias ni secretos. Logs y comparación exacta: `/tmp/h3req1-run89-checks-20261101/`.

Transición: expand = actualizar evidencia documental autenticada; compatibilidad = conservar el path y schema que consume el gate, sin cambiar código ni runtime; deploy = integración protegida independiente por ambiente; contract = no aplica hasta instalar y comprobar H3 en Pro y desplegar BFF/configuración; rollback = revertir solo los cambios documentales por PR protegido, conservando artefactos, auditoría y DB. No activar FG1/FG2/FG3, writers, schedules ni H4.

### Corte histórico 2026-10-31 — guard de scope para el candidato H3REQ1

Estado remoto reutilizado del informe TL `/tmp/h3req1-certification-audit-20261031/informe-tl.md` y de lecturas de refs: Desarrollo `965b4862341cb4550c7833677a9675d52404fb4b`, Certification `eddb5527817aa241801ee1477acb9eb1edd8a409`, main `70d0f4fee885be0f6780e5d14f466b2a6c897961`. El deployment normal de Certification corresponde a `eddb5527…`; el reporte #88/run `41241415710` terminó success para `h2-expand-compat`: 5/5 migraciones, 224 cursos elegibles/visibles y cero pendientes. `verify` y `apply` fueron skipped; no se afirma H3 instalado en Pro. Aceptaciones reutilizadas sin repetición: E1–E6 local 6/6, Development R1–R4 4/4 y smoke histórico Certification 1/1.

El candidato local parte de Desarrollo `965b4862341cb4550c7833677a9675d52404fb4b` en `codex/h3req1-protected-path-scope-fix-20261031`; GitHub confirmó esa SHA para `desarrollo`, con Certification `eddb5527817aa241801ee1477acb9eb1edd8a409` y main `70d0f4fee885be0f6780e5d14f466b2a6c897961`. No hay commit candidato ni publicación. Corrige dos límites del guard: admite únicamente el archivo de evidencia H2 Main por path exacto, mientras `security-audit.yml` conserva su validación de contenido independiente; consume los pins congelados de Certification y main solo si `PROTECTED_BASELINE_SHA` coincide con el baseline para el que fueron aprobados. Para cualquier baseline posterior no agrega paths históricos: siguen aplicando las allowlists ordinarias y el rechazo de vecinos. Se preservan las comprobaciones de source, ancestría, blobs, modo, hash y contenido de los pins cuando corresponde consumirlos.

Validación del código/fuentes sin cambios posteriores, Docker sin red y checkout aislado: `tests/test_protected_path_scope_guard.sh` PASS (1196 paths, 13 catálogos/1173 referencias, callers PR/push de ambas promociones, baseline posterior sin pins congelados, source/content drift fail-closed y rutas vecinas rechazadas); `tests/test_security_flow.py` PASS; ShellCheck v0.11.0 PASS en ambos scripts afectados. La comparación acumulada de la ruta real contra baselines Development, Certification y main pasó con commits/tree sintéticos desechables y el mismo set de nueve paths; no son SHAs publicados ni reemplazan CI. Estos controles no cambiaron en la edición documental final.

Validación del árbol documental final, Docker sin red: scanner del árbol rastreado y del checkpoint nuevo PASS; `git diff --check` rastreado PASS y el archivo nuevo no produjo advertencias en `git diff --no-index --check` (exit 1 solo por diferencia frente a `/dev/null`); render PASS. El checker normal, con la misma imagen y configuración sobre baseline y candidato, devolvió FAIL integral en ambos: 348 diagnósticos cada uno, cero nuevos y cero resueltos. El self-test produjo `DOC_SELF_TEST_PASS`; el proceso envolvente terminó exit 1 por el FAIL integral. Los logs completos y la lista no truncada de diagnósticos están en `/tmp/h3req1-protected-path-scope-evidence-20261031/`. No se afirma candidate-aware PASS para este candidato.

El residual requiere disposición humana nueva y específica antes de integrar; las disposiciones anteriores no se extienden. El gate de contenido H2 de main no se cambia ni se dispensa. No hubo escrituras remotas, SQL, workflow, configuración, merge ni deploy en este ciclo. Transición: expand = allowlist exacta y regla de baseline de pins; compatibilidad = PR/push histórico conserva su ruta y baseline posterior depende de allowlists ordinarias; deploy = únicamente por PR protegido de cada ambiente; contract = no existe cambio de comportamiento de producto ni fase remota de contracción; rollback = revert protegido que vuelve al bloqueo fail-closed sin efecto de datos.

La matriz final, revisión de seguridad por impacto, propuesta de disposición pendiente y borrador de PR para el TL están en el [checkpoint del fix de scope](evidencia/h3req1_protected_path_scope_fix_2026-10-31.md). Aceptaciones reutilizadas sin repetición: E1–E6 local 6/6, Development R1–R4 4/4 y smoke histórico Certification 1/1. El cambio local está técnicamente validado; el FAIL integral permanece sin waiver aprobado. Siguiente acción exacta: el TL decide la disposición limitada a este candidato y a integración a Desarrollo; publicación requiere además su autorización específica de commit/push/PR. Este ciclo no autoriza ni ejecuta esas acciones.

### Corte anterior — remediación main validada localmente (histórico; SHAs y estado supersedidos)

Las refs protegidas no cambiaron: Desarrollo `b9eb7718…`, Certification
`03515dee…`, main `70d0f4fe…`. El fix validado `6d73b51b…` permanece local y
congelado; publicación/disposición solicitadas y aún no aprobadas expresamente.
La simulación main rechazó 239 rutas del acumulado de 1.630 archivos. Comparación
estática: el conjunto es idéntico al scope histórico de Certification y todos
sus blobs siguen idénticos a Certification y al source histórico. El follow-up
añade pins exactos/caller para main y tests del caller real, sin ampliar carpetas.
Docker recuperado: regresiones/caller real, comparación main, ShellCheck,
scanner y documentación candidate-aware/self-test PASS; 46 tests Python focales
PASS. Se consolida con el fix anterior en una sola rama candidata desde Desarrollo.
Pins finales: Certification 28 paths contra baseline `03515dee…` y source
`2d3ed36b…`; main 239 paths contra baseline `70d0f4fe…` y source `6d73b51b…`.
Las tres comparaciones reales (feature/Desarrollo, Desarrollo/Certification y
Certification/main) pasan en el commit local `8c2cc6ed…`, junto con scanner y
candidate-aware/self-test. Revisión estática final de pins: sin hallazgos.
Integral conserva FAIL: comparación diagnóstica sin truncar confirma exactamente
348 fallos en baseline y candidato, cero añadidos y cero retirados. La copia
diagnóstica cambia solo root/salida, no reglas/veredicto; checker versionado intacto.
GO local para solicitar publicación; NO-GO remoto/main. La autorización previa
solicitada para `6d73b51b…` no cubre por intención el candidato consolidado.

Docker 29.9.2 está operativo tras recuperación asistida.
Chrome Windows sí responde. Tras el login manual confirmado y recarga MCP,
Supabase Pro está conectado: URL `https://xwhtiqmboljkshrtviyw.supabase.co`.
Corrección de diagnóstico: `supabase_migrations.schema_migrations` tiene 23
entradas, pero el migrador usa `public.supabase_migrations`: tiene 58 entradas,
con las cinco migraciones H2 expand registradas y cero H3. La cohorte elegible,
cohorte capturada y lector efectivo consultado como rol administrativo tienen
224 cursos; ambos digests de cohorte son
`sha256:c217dbffc9d50cca0e1f111fcddf1268db9a34e8671a409f3663dcfff1d735e9`,
con cero diferencias de conjuntos. No leer el ledger interno como falta de apply
H2 ni volver a aplicarlo por esa causa. Esto no prueba visibilidad anónima ni
verify del candidato actual. Cero RPC Admin y ausencia de membresías,
invitaciones, quota, claves gateway y columnas snapshot H3 confirmados.
No se ejecutaron escrituras SQL, workflow, configuración, merge o deploy.

### Corrección P1 del preflight DB Sync — camino a main

Base inmutable de este fix: `desarrollo@b9eb77185f1a037111ce1237820ae6c38b15ea67`.
El PR #514 de promoción permanece abierto, sin merge: el preflight manual buscaba
el literal H3 en el migrador aunque este lo importaba, y abortaba todos los
manifests antes de report/apply/verify. Se reprodujo offline con exit 1.

La corrección local comparte el registro cerrado entre migrador y workflow en
el módulo stdlib existente, sin importar clientes DB. Los seis manifests se
validan ejecutando el bloque real del YAML. Negativos de selección, registro,
SQL ausente y hash H3 alterado preservan fail-closed. Docker sin red/read-only:
87 tests focales y suite CI de 276 tests/10 subtests PASS. Scanner de credenciales,
regresiones scope/selector/pins, candidate-aware/self-test documental y actionlint
PASS. Revisión estática focal security-auditor: cero hallazgos; no sustituye CI
ni revisión productiva. No se repiten aceptaciones E1–E6 6/6, Development 4/4 ni
Certification 1/1. Se actualizarán los pins de promoción sobre el commit local
inmutable del fix antes de publicar para evitar otro follow-up de pins.

NO-GO de promoción hasta integrar el fix, reevaluar el candidato y sus checks.
H2 Pro requiere verificación renovada (véase corrección de ledger arriba);
reporte/verify, SQL H3, BFF/Pages, evidencia H2 de main y smoke
productivo conservan gates independientes. No se ejecutó SQL, workflow remoto,
configuración, merge ni deploy manual. La disposición de #514 solo corresponde
a su SHA anterior y no se extiende por intención al nuevo candidato.

### PR #512 — remediación focal de CI

Integrado el 2026-10-29 a las 23:03 America/Lima. El merge SHA de Desarrollo es
`34469196c5ba4d073b49479f2fb44e84c279dbbb`; el HEAD revisado del PR fue
`317d5e7bc861e414ea1d806774de973abab9fa7b`. Certification permanece en
`03515dee69fc42b10808d1c67cc4e00ebacd0c40`. En el HEAD del PR hubo 16 checks
success y dos skipped (`Supabase Preview`, `H2 Main Production Expand Gate`), sin
fallos ni ejecuciones pendientes; la aprobación humana requerida constaba antes
del merge.

Cloudflare Pages desplegó automáticamente el SHA de Desarrollo en el deployment
`b8255fbf-19e6-4feb-ba06-bb687e079f46`, estado success, alias
`desarrollo.studiamatch-aty.pages.dev`. Lectura de metadatos Preview: existen los
nombres de `ADMIN_ALLOWED_HOSTS`, las HMAC keys y el key id; está el binding de
servicio `ADMIN_QUOTA`. No se leyeron valores de variables ni secretos. No hubo
deploy manual, SQL ni ejecución de workflows de negocio.

### H3REQ1 — preparación real Desarrollo → Certification — NO-GO

Refs observadas: Desarrollo `34469196c5ba4d073b49479f2fb44e84c279dbbb` y
Certification `03515dee69fc42b10808d1c67cc4e00ebacd0c40`. El ancestro común es
`6f059a0b27ef38541a7b62503c78920e621f05c1`; la divergencia Git es 10 commits
adelante / 3 detrás y el delta del candidato suma 31 archivos (+3582/−245).
`merge-tree` no informa conflictos y el árbol resultante coincide con el árbol
de Desarrollo. Esto no actualiza ramas protegidas ni equivale a un PR o merge.

El selector real del workflow eligió el manifiesto H3 de promoción y agregó 46
paths. En Docker, self-test/candidate-aware pasó: 752/752 fuentes asignadas,
119/119 documentos activos alcanzables, 433/433 históricos enlazados. El checker
integral conserva FAIL: 350 diagnósticos en Certification frente a 348 en
Desarrollo, cero nuevos exclusivos y dos resueltos. Se mantiene visible y separado;
la disposición A de #512 fue consumida y solo cubría solicitar integración a
Desarrollo, por lo que no se extiende a Certification.

El guard integrado rechaza el candidato porque sus pins esperan baseline
`c80f6504…` y source `941eca49…`, mientras las refs actuales son `03515dee…` y
`34469196…`. El arreglo local conserva la comprobación de pins: actualiza el par
exacto de SHAs y regenera 27 pins de blobs inmutables para los paths del candidato
que no editaría el follow-up. Los cuatro paths del candidato que sí cambiarán en
ese follow-up, más el propio manifiesto de pins, permanecen cubiertos por
allowlists exactos; no se amplían carpetas ni se omite el gate.

Con este arreglo local no integrado, la comparación exacta del candidato pasa en
Docker y `tests/test_protected_path_scope_guard.sh` pasa con selector, pins,
vecinos negativos y casos fail-closed. También pasan `bash -n`, `git diff --check`,
credential scan del paquete (cinco paths modificados y el test existente). Tras
registrar la disposición A, el self-test documental candidate-aware se ejecutó
en Docker/red `none` sobre una copia temporal del árbol base más exactamente los
cinco paths locales: `DOC_SELF_TEST_PASS`, 752/752 fuentes, 119/119 activos,
433/433 históricos, 9.376 links y 4.699 anchors; `DOC_GATE_PASS`. Log SHA-256
`68349a36e11d1d6c371a497135d3c2a172af0b67db7db9a1f4532da0e8df7de4`. Un
intento diagnóstico sin manifest de candidato tuvo el self-test interno PASS,
pero el gate completo falló al tratar 305 fuentes candidate-only no seleccionadas
como parte del scope; no se cuenta como resultado candidate-aware. El log
integral sigue byte-idéntico al del candidato integrado: 348 diagnósticos.
ShellCheck no está en la imagen Docker y sigue pendiente de CI. El 2026-10-30
01:23 America/Lima Codex Security volvió a rechazar el inicio del diff scan con
`Working-tree contents changed after they were selected. Select Uncommitted
changes again`; no devolvió `scanId` y no cuenta como scan completado. Se hizo
revisión estática focal del guard/pins y sus controles: el diff solo sustituye
los SHAs esperados y los blobs correspondientes; siguen activos el anclaje a
baseline/source, la validación de unicidad/rutas, la comparación de blobs y el
rechazo fail-closed. Esa lectura no sustituye Codex Security ni CI. El guard/pins
remotos no cambian hasta que el follow-up sea integrado a Desarrollo.

Resultado actual: NO-GO para solicitar/crear PR Desarrollo → Certification. No
se ha pedido una disposición documental nueva para Certification ni autorización
para su PR. Siguiente decisión: autorizar por separado el commit/push/PR protegido
a Desarrollo del follow-up local de cinco paths; no incluye merge. Después de
integrarlo se deben refrescar refs y comprobar el pin set efectivo antes de pedir
disposición y autorización nuevas para Certification. E1–E6 local 6/6, R1–R4
Development 4/4 y smoke Certification 1/1 permanecen aceptados y no se repitieron.

### Corte H3REQ1 previo al merge #512 — histórico/supersedido — 2026-10-29 18:57 America/Lima

Worktree `/tmp/studiamatch-h3req1-production-remediation-20261029`, rama
`codex/h3req1-production-remediation-20261029`, base/HEAD
`6f059a0b27ef38541a7b62503c78920e621f05c1`. Inventario actual: 30 paths,
25 modificados y 5 nuevos. La huella estable, inventario de paths y hashes por
archivo se cierran en `/tmp/h3req1-production-remediation-20261029-final/`; el
borrador de revisión refleja 30 paths, no el corte histórico de 27. WIP de
otros checkouts preservado. Sin commit, push, PR, merge, SQL, workflow,
configuración remota ni deploy.

**Corrección H2/Pro:** `h2_pro_preflight_report.py` ahora separa diagnóstico
read-only de autorización de apply. Distingue `BASELINE`, `PARTIAL_UNLEDGERED`,
`H2_COMPATIBLE_OBSERVED_SURFACE`, `INCONSISTENT` y `READ_ERROR`. Para el estado
parcial de Pro produce agregados con `REVIEW_REQUIRED` y omite los valores de
JIT; cualquier estado incompleto queda sin autorización. El digest se calcula
sobre la cohorte elegible ordenada. `apply_authorized` es falso, la decisión es
`NOT_AUTHORIZED`, no hay RPC/SQL/DML/backfill y los guards de `db_migrate.py`
permanecen sin relajación.

**Pruebas nuevas en Docker:** 29 casos del lector y quince controles/regresiones
de lectura/paridad/migrador: 44 passed. Se añadió una prueba que confirma que
la importación del reporte no contamina el stdout JSON. También hay regresiones para agregación
de grupos duplicados, bloqueo de redirects en GET/RPC y comprobación fail-closed
de los probes H3 privados ante HTTP 302/500. Las lecturas no reenvían `apikey`
a otro origen y los errores de servidor no se interpretan como prueba de
privacidad. La lógica de duplicados ya era correcta. Cubre
baseline, H2 parcial sin ledger, superficie compatible solo como diagnóstico,
ledger/schema inconsistente, visibilidad divergente y errores HTTP, red, JSON
forma de respuesta con salida sanitizada, y pin de destino que rechaza host,
esquema, credenciales, puerto, ruta, query y fragmento no canónicos. Imagen
`studiamatch-h3req1:sync-a57bc415-rebuilt-20261018`, red deshabilitada y árbol
read-only. Log focal SHA-256
`2bd78775f382ddb2b7640e87a241317b320cbe2badaea3ff041c0eb404ee7ae8`;
`py_compile` de los módulos afectados PASS (log SHA-256
`70dfa6a2bf0032db1311a455aa076b1fd8cefc461c31853a91323661f6f9dfd9`).

**Aceptaciones reutilizadas:** E1–E6 local 6/6, Development R1–R4 4/4 y smoke
Certification 1/1 siguen aceptados; no se repitieron. El reporte Pro no se
ejecutó. Su futura ejecución usa el service key del environment Production,
que evade RLS; requiere JIT de lectura separado. No se leyó ni imprimió ninguna
clave.

**Integridad documental:** self-test/candidate-aware PASS; checker integral
FAIL, 350 diagnósticos baseline frente a 348 candidato con el mismo
checker/configuración y sin diagnósticos nuevos exclusivos. Baseline y candidato
comparten checker SHA-256
`f2a95870de748b2e59ee0d988abb0b16125da47c996a7f85841f1113fcebbb75`; logs
oficiales y listas completas con hashes están en `final-checksums.txt`. Los 2
diagnósticos baseline-only se resolvieron; el FAIL integral sigue abierto. El
responsable aprobó el 2026-10-30 a las 01:06 America/Lima una disposición nueva
para el residual histórico de esta corrección local: base Desarrollo
`34469196c5ba4d073b49479f2fb44e84c279dbbb`, diff SHA-256
`e6f072cc6a1e63eebe6cad9136b971917386f19ee1ffe432f4e6ba0902c209ce`, cinco
paths. Owner Romel/TL; riesgo: trazabilidad histórica incompleta; vence el
**2026-11-05 23:59 America/Lima** o antes de cualquier promoción a Certification,
lo que ocurra primero. Solo dispone el residual para tramitar la integración
protegida a `desarrollo`; no convierte el FAIL en PASS y no autoriza commit,
push, PR, review, merge, Certification, `main`, SQL, workflow, configuración ni
deploy. La aprobación de publicación se solicitará por separado. La disposición
#509 y la A de #512 están consumidas en sus propios alcances y no se extienden.

**Revisión de seguridad:** Codex Security scan diff-scoped completado sobre el
candidato local, snapshot
`codex-security-snapshot/v1:sha256:22f4ea54b05873332bff3d8130c225d6428180ee408ba0a546051093697d02e5`,
scan `c28d2808-5a58-4342-8284-54715649cb95`: cobertura completa de 12 ítems,
0 findings, 5 superficies sin issue. Reporte en
`/home/romel/.codex/state/plugins/codex-security/scans/studiamatch-h3req1-production-remediation-20261029/6f059a0b27ef38541a7b62503c78920e621f05c1_20261029T235250Z_f_kxu_b3/report.md`.
Es revisión del diff, no auditoría global ni validación de schema/runtime Pro.
Se completó antes de este cierre editorial; después solo se ajusta evidencia y
borradores, sin cambios de código.

**Siguiente gate:** el preflight SELECT-only Pro ya observado (23 entradas,
H2 parcial fuera del ledger) se reutiliza y no se repite. El lector local tiene
44/44 pruebas focales PASS; su futura ejecución mediante `report` sigue
pendiente de JIT read-only explícito porque el workflow usa la service key de
Production, que evade RLS. NO-GO para publicar hasta resolver el gate
documental; después se requiere autorización separada para commit, push no
forzado y PR a `desarrollo`. H2 report/verify, SQL H3, Pages/BFF, promociones
protegidas y smoke Pro requieren JIT propios. H1 sigue sin FG1/FG2/FG3 ni
schedules; H4 depende de paridad H2 y secuencia H2→H3→H4. No hay GO Pro ni
productivo.

### Corte local anterior — supersedido, 2026-10-29 15:18 America/Lima

Worktree `/tmp/studiamatch-h3req1-production-remediation-20261029`, rama
`codex/h3req1-production-remediation-20261029`, base/HEAD
`6f059a0b27ef38541a7b62503c78920e621f05c1`. Inventario final: 27 paths,
23 modificados y 4 nuevos; el paquete es mayor que el delta de 13 paths de un
corte anterior. La lista ordenada y SHA-256 por path están en el checkpoint
externo `/tmp/h3req1-production-remediation-20261029-final/candidate-fingerprint.txt`;
su digest se registra en `pr-body-draft.md` fuera del repo para evitar
autorreferencia. Se preservó el WIP de otros checkouts. Sin commit, push, PR,
merge, SQL, workflow, configuración remota ni deploy.

**Gates locales y seguridad:** en la imagen del proyecto
`studiamatch-h3req1:sync-a57bc415-rebuilt-20261018`, Docker/red deshabilitada,
se validaron los gates focales afectados: manifest H3 con orden/hashes y
entradas inválidas, selector `certificacion→main`, pins y regresión de
interpolación Bash; H2/paridad/boundary; CA4.6; guard documental; TypeScript y
ESLint. El rerun focal final de manifest H3, H2/paridad y boundary pasó 21/21
en 0,23 s; el test Node CA4.6 pasó 1/1 y selector/pins/regresión de
interpolación Bash pasó en `tests/test_protected_path_scope_guard.sh`. El test
de host pin añadido pasó 8/8 en el rerun sin cache. El primer escaneo
detectó el nombre literal de una variable y el prefijo de una key sintética de
prueba (no credencial); el fixture se simplificó, el test afectado se repitió
8/8 y el credential scan de los 27 paths pasó. El
self-test/candidate-aware del árbol final pasó 751/751 fuentes, 119/119 docs
activos y 433/433 históricos. La ejecución sin manifest devuelve exit 1 por el
FAIL integral de 348, no por fallo de la lógica sintética self-test. El build
estático Next 16.3.8 pasó en copia efímera con mock local explícito
(`127.0.0.1`, `NEXT_PUBLIC_H3_ALLOW_MOCK_BUILD=true`), 17 páginas generadas;
no conectó a Supabase ni demuestra runtime Pro. Para ese build solo se descargó
la fuente pública Geist. El log con SHA del escaneo exacto está en
`final-checksums.txt` externo. El chequeo de seguridad
Codex Security sobre el snapshot successor
`codex-security-snapshot/v1:sha256:c74d9d9a6abcb1ba90230e9e5e0d4d3268b1f91e504f3c66fc96dfa53a4048d2`
completó cobertura diff acotada 11/11, cero findings (scan
`ae623b31-4065-4f73-8811-cbde81cd39be`), sin runtime Production.
Después del snapshot solo se ajustó el valor sintético de un test para evitar
el patrón del credential scanner; no cambió lógica de aplicación. La línea
final fue revisada, el módulo afectado pasó 8/8 y el scan exacto de 27 paths pasó.
El primer intento de esta revalidación activó el entrypoint de bootstrap y se
detuvo por node_modules desincronizado antes de ejecutar tests; una segunda
invocación usó `/usr/bin/python3`, que no tiene pytest, y salió antes de
colección; una tercera sí ejecutó pytest del venv, pero no tenía `PYTHONPATH`
y falló en importación durante colección. Ninguna cuenta como test. La corrida
válida usó el entrypoint explícito, `/opt/venv/bin/pytest` y `PYTHONPATH=/app`.
No se cambiaron permisos de `docker.sock`, ni el contenedor `studiamatch-dev` ni
volúmenes ajenos. El árbol corregido incluye host Pro HTTPS/canónico y
aserciones Docker autocontrastadas; la revisión cubrió ambos. Logs por comando,
hashes, salidas de escaneo y huella final constan en el checkpoint externo.

**Aceptaciones reutilizadas, sin repetición:** E1–E6 local 6/6, Development
R1–R4 4/4 y smoke Certification 1/1 siguen aceptados. No hay CI de este
candidato porque no existe PR.

**Integridad documental:** el self-test/candidate-aware actual está PASS; el
checker integral oficial sigue FAIL con 348 diagnósticos frente a 350 en el
baseline (mismo checker/config). El paquete elimina los dos hallazgos
baseline-only y no añade diagnóstico único. Los 348 se agrupan por 79 paths
locales candidate-only repetidos en tres categorías, 88 relaciones sobre 20
paths únicos, 15 exclusiones locales/generadas y 8 referencias a cuatro
originales privados excluidos con reemplazo sanitizado. No se recrearon
fuentes, copiaron documentos privados ni retiraron relaciones en masa. Una
disposición para producción está **propuesta, NO aprobada**, limitada a la
huella/log exactos del paquete; owner Romel/TL; riesgo de trazabilidad
histórica incompleta; vencimiento propuesto 2026-11-05 23:59 America/Lima o
antes del primer merge `certificacion→main`, lo que ocurra primero. El log
oficial del árbol final, su compañero con lista completa, los baselines y sus
hashes se fijan en `final-checksums.txt` externo junto con la huella de 27
rutas; la disposición propuesta debe citar esos bytes exactos. No hereda
ni extiende #509/#510/#511. Sin esa resolución, NO-GO de publicación.

**Pro/H2/H3 y Pages/BFF:** se conserva el preflight SELECT-only ya obtenido
para Pro `xwhtiqmboljkshrtviyw`: 23 migraciones registradas; objetos H2
parciales fuera del ledger; cohorte agregada no leída; faltan columnas
snapshot y objetos Admin/H3. `h2_pro_preflight_report.py` aborta antes de
emitir agregados y necesita una corrección local read-only con pruebas antes
de que un `workflow_dispatch report/verify` sea decidible. No inferir ni
reaplicar H2 por cantidad de entradas. El manifest H3 de 31 migraciones queda
preparado localmente, sin PG17 DDL ni ejecución remota. En Pages Production
faltan hosts Admin, tres HMAC keys distintas por función, key id respaldado
por Pro y binding `ADMIN_QUOTA`; el Worker/DO existe. El metadato
`NEXT_SUPABASE_SECRET_KEY: plain_text` no prueba exposición: su valor no fue
leído y no hay consumidor en Pages Functions. No se alteró Pages/Access.

**Siguiente paso:** resolver el gate integral para la huella final. Después,
solicitar por separado autorización para commit/push no forzado/PR hacia
`desarrollo`. H2 report/verify, workflow SQL H3, Pages/BFF, las promociones
protegidas y el smoke Production requieren payload/JIT propios. H1 queda en
preparación (sin FG1/FG2/FG3 ni schedules); H4 depende de evidencia del
contrato H2 y secuencia H2→H3→H4. No declarar GO de Pro ni producción.

### Corte vigente anterior — supersedido, 2026-10-29 14:40 America/Lima

#### Paquete local ampliado H3REQ1 — estado anterior

Worktree `/tmp/studiamatch-h3req1-production-remediation-20261029`, rama
`codex/h3req1-production-remediation-20261029`, HEAD/base
`6f059a0b27ef38541a7b62503c78920e621f05c1`. GitHub confirma las ramas
protegidas: `desarrollo@6f059a0b27ef38541a7b62503c78920e621f05c1`,
`certificacion@03515dee69fc42b10808d1c67cc4e00ebacd0c40` y
`main@70d0f4fee885be0f6780e5d14f466b2a6c897961`. El paquete tiene 27 paths
(23 modificados y 4 nuevos); se amplió de 25 solo al añadir handoffs H1/H4.
Sin commit, push, PR, merge, SQL, workflow, configuración remota ni deploy.
WIP ajeno preservado.

**Gates locales finales en Docker** (imagen existente del proyecto,
`studiamatch-h3req1:sync-a57bc415-rebuilt-20261018`, red deshabilitada):
20/20 pruebas Python de manifest/orden/hashes H3, guardas H2/paridad y boundary
`main`; 1/1 test Node CA4.6; selector de promoción y pins con casos positivos y
negativos fail-closed; 1.196 rutas, 13 catálogos y sus regresiones; `tsc --noEmit`
y ESLint del editor: PASS. El checkout se montó read-only. TypeScript escribió
su cache exclusivamente en `/tmp`; la dependencia npm preexistente se montó
read-only. Un primer `tsc` intentó escribir en una copia read-only y se repitió
con cache externo; solo la segunda ejecución cuenta. `git diff --check` y el
credential scan sobre las 27 rutas se registran en el checkpoint externo final.
`actionlint` y ShellCheck se reutilizan del corte previo porque sus entradas no
cambiaron. Las aceptaciones E1–E6 local 6/6, Development R1–R4 4/4 y
Certification 1/1 se conservan sin repetición. No hay CI remoto: no se abrió PR.

**Arranque fallido, no test:** `studiamatch-dev:local` rechazó bootstrap por
desajuste de hashes Node. La imagen de proyecto con manifests coincidentes
(`package.json` SHA-256 `dfdd9a7ea0ff192c7eda7c33d9a2141b5b761fb0c53c472d8209e4fa2c309ab2`,
`package-lock.json` SHA-256 `d526163caba9300baf9329121979b9c9bc1bd24dfc10b1b4159d0ee8a36334db`)
expuso un volumen anónimo desincronizado al bootstrap normal; tampoco se cuenta.
Se usó el entrypoint explícito solo en contenedores efímeros y aislados. La API
Docker requirió el permiso elevado normal de esta sesión; no se modificaron
permisos de `docker.sock`, no se alteró el contenedor `studiamatch-dev` y no se
escribió en volúmenes existentes.

**Integridad documental final:** el self-test/candidate-aware actual dio PASS:
751/751 fuentes asignadas, 119/119 documentos activos alcanzables y 433/433
históricos enlazados; 9.372 enlaces/4.696 anchors. El checker integral oficial
actual da FAIL: 348 diagnósticos candidatos frente a 350 en baseline, mismo
checker SHA-256 `f52eb76ad8ea5c64c3eb32ab4cd76661db5d7a33cd45aeb23311d6dc482d5da1`.
El log oficial candidato reproduce exactamente SHA-256
`0d43cdf829066c459ecffc28eb339b9d889c1a12f9e6dbd38adb0dfb90abbb10`; el log
full-list asociado tiene SHA-256 `cb1767e4bdb2abc76d2d411b94b4713be9011d68e3c350008e3f0c86d696d0fe`
y sus primeros 200 diagnósticos coinciden con la ejecución actual. El baseline
completo registra 350 (log SHA-256
`eae1107b5eba56ee9c9a9252f51ad241e95adda7328eb8a1ec33724a363524da`); sus
primeros 200 coinciden con la nueva ejecución baseline. El paquete corrige los
dos diagnósticos baseline-only (`INTEGRATION_PROJECTION_CANDIDATE_ONLY_COUNT`,
`REGISTRY_MARKDOWN_DRIFT`) y no crea diagnósticos únicos. El PASS acotado no
sustituye ni convierte el FAIL integral.

Los 348 residuales se agrupan en 79 rutas candidate-only locales sin origen
Git/copia autorizada (79 + 79 + 79 diagnósticos de alcance/fuente sobre los
mismos paths), 88 relaciones que apuntan a 20 rutas únicas, 15 exclusiones
locales/generadas ausentes y 8 referencias a cuatro originales privados
excluidos cuyos sucesores están sanitizados. El análisis por ruta y el cotejo de
copias Git están en el checkpoint. No se copiaron documentos privados, no se
recrearon archivos históricos y no se borraron relaciones en masa. La
disposición sigue propuesta, NO aprobada, vinculada a la huella y log final
exactos; owner Romel/TL; riesgo: trazabilidad histórica incompleta; vence
propuesto el 2026-11-05 23:59 America/Lima o antes del primer merge
`certificacion→main`, lo que ocurra primero. No extiende #509/#510/#511.

**H2/Pro:** el acceso read-only está verificado; las observaciones previas de
“Pro inaccesible” quedan históricas/supersedidas. Se reutiliza el preflight:
23 entradas de ledger, objetos H2 parciales fuera de ledger, cohorte no leída,
columnas snapshot y objetos Admin/H3 pendientes. `h2_pro_preflight_report.py`
falla antes de emitir aggregates al detectar esos objetos; el report/verify no
está listo para dispatch y requiere una corrección local read-only separada y
sus tests. No reaplicar H2 por ledger ni ejecutar workflow, función o SQL.
H1 sigue en preparación sin activar FG1/FG2/FG3/schedules; H4 sigue en
preparación hasta acreditar contrato H2 y resolver secuencia H2→H3→H4.

**Pages/BFF Pro:** la última lectura Cloudflare filtrada mostró que faltan
`ADMIN_ALLOWED_HOSTS`, las tres HMAC keys por función,
`ADMIN_RPC_GATEWAY_KEY_ID` y el binding `ADMIN_QUOTA`; el Worker/DO de cuota sí
existe. `NEXT_SUPABASE_SECRET_KEY` figura `plain_text`, pero su valor no se leyó,
no se encontró consumidor en `web/`/Pages Functions y el tipo no demuestra
exposición. No copiar claves Preview ni cambiar Pages/Access antes de probar la
dependencia Pro.

**Revisión de seguridad acotada:** Codex Security completó la revisión del
snapshot inmutable pre-fix `f925f6c4…` y registró CWE-78/P3 por strings de
workflow expandidos en Bash antes de validar. El patch actual usa `env` por
step y expansiones citadas; la regresión focal ya había pasado y el árbol
corregido se revisó manualmente. El reporte advierte que el árbol cambió durante
el scan: no es un snapshot inmutable post-fix ni validación de Production.
Sin dispatch, payload ni cambios remotos. Reporte:
`/home/romel/.codex/state/plugins/codex-security/scans/studiamatch-h3req1-production-remediation-20261029/6f059a0b27ef38541a7b62503c78920e621f05c1_20261029T184334Z_f_0npl6f/report.md`.

**Siguiente decisión humana:** resolver la disposición documental residual para
la huella/log exactos del checkpoint. Hasta una resolución aplicable, NO-GO de
commit/push/PR. Después se requiere autorización separada de commit, push no
forzado y PR a `desarrollo`. H2 report/verify, SQL H3, Pages/BFF, promociones
protegidas y smoke productivo requieren solicitudes separadas. Ninguna
aceptación ya cerrada equivale a GO Pro ni activa H1.

### Corte previo de remediación y preparación H3 Pro — histórico, 2026-10-29 13:28 America/Lima

Worktree aislado `/tmp/studiamatch-h3req1-production-remediation-20261029`, rama
`codex/h3req1-production-remediation-20261029`, base
`desarrollo@6f059a0b27ef38541a7b62503c78920e621f05c1`. El delta local contiene
20 paths modificados y 4 nuevos; el checkout documental anterior y el WIP de
otros checkouts se preservan. No hubo commit, push, PR, merge, SQL, workflow,
configuración remota ni deploy.

**Correcciones locales:** CA4.6 cambia la presentación de auditoría solo para la
clave `availability_status` omitida por `admin_publish_course`; `null` explícito,
cambio editorial y eliminación permitida siguen visibles. Test focal: 1/1 PASS en
Docker. El selector documental conserva pins/selección exacta y cubre el acumulado
`certificacion → main` y push posterior; casos positivos/negativos PASS. El
manifiesto H3 se integra al `DB Sync to Production` existente: 31 SQL por
nombre/SHA, dependencias explícitas, rechazo de selección parcial/inválida y
prerrequisito de compatibilidad H2. Es candidato local, no ejecución ni
autorización de SQL/workflow.

**Gates locales afectados:** 20/20 tests Python focales de manifest/H2/main,
1/1 test Node CA4.6, guard/selector positivo y negativos, actionlint del workflow,
ShellCheck y `git diff --check`: PASS en Docker/red deshabilitada. E1–E6 local
6/6, R1–R4 Development 4/4 y smoke Certification 1/1 siguen aceptados; no se
repitieron.

**Integridad documental:** self-test y candidate-aware pasan sobre el árbol
candidato. La comparación integral final, con el mismo checker vigente y config,
es 350 diagnósticos en baseline y 348 en candidato. El baseline incluye dos
diagnósticos que el paquete corrige: contador/proyección candidate-only desfasado
y Markdown de registro generado desactualizado. El candidato no introduce
diagnósticos únicos; sus 348 residuales son 79 rutas candidate-only locales sin
fuente Git autorizada, 88 relaciones sobre 20 de esas rutas, 15 exclusiones
locales/generadas y 8 diagnósticos sobre cuatro exclusiones documentales
históricas. La cifra baseline previa 349 corresponde al corte/checker anterior y
queda histórica, reemplazada por esta comparación final. Ninguna relación se
borró ni se fabricó una fuente. La disposición productiva propuesta sigue sin
aprobación; candidate-aware PASS no satisface el gate integral.

**Pro/H2 — lectura de metadata ya completada:** `xwhtiqmboljkshrtviyw`, ledger
23 migrations (`20260525030610`–`20260607221002`). Hay objetos editoriales H2
parciales fuera del ledger; no se leyó la cohorte ni se invocó
`h2_verify_expand_compat`. Faltan las tres columnas snapshot y los objetos
Admin/H3. El report H2 existente falla cerrado al detectar objetos previos a su
manifest; falta la evidencia agregada de elegibles, digest ordenado, conteo
visible, missing/unexpected y grupos de institution/slug duplicados. No se
infiere qué aplicar por cantidad de migrations. Se preparó la lectura agregada
acotada; no se ejecutó workflow, función ni query adicional.

**Pages/Access Pro — lectura sanitizada:** Pages `studiamatch`, rama `main`.
Production devuelve metadatos de nombres/tipos de URL y publishable keys, y
`NEXT_SUPABASE_SECRET_KEY` como `plain_text`; no se leyó ningún valor y el tipo
no demuestra exposición. No hay consumidores en `web/` ni Pages Functions; los
workflows/scripts backend usan secretos de sus propios ambientes. Para el BFF
Production faltan `ADMIN_ALLOWED_HOSTS`, tres HMAC keys distintas por función y
ambiente, `ADMIN_RPC_GATEWAY_KEY_ID` respaldado por Pro y binding `ADMIN_QUOTA`
compatible con el Worker/DO existente. Access Admin-only/6h queda intacto. Sin
cambio de configuración.

**Disposición documental propuesta, NO aplicada:** solo los 348 diagnósticos
integrales del log candidato de este paquete; evidencia integral 350→348 bajo el
checker vigente, PASS acotado
separado y causas arriba. Owner propuesto: Romel/TL. Riesgo: trazabilidad
histórica incompleta, sin evidencia de pérdida funcional o exposición. Vence
2026-11-05 23:59 America/Lima o antes del primer merge `certificacion → main`,
lo que ocurra primero. No extiende #509/#510/#511 ni otra disposición previa.
Requiere decisión humana sobre la huella final; no autoriza publicación.

**Resultado:** NO-GO para integrar/publicar mientras el gate integral aplicable
no se remedie o disponga para el candidato exacto. Después se necesita
autorización separada para commit, push no forzado y PR a `desarrollo`. Pro/H2,
workflow_dispatch, SQL, Pages/Access y promociones siguen sin autorización.
La huella de los 24 paths se cierra al final en
`/tmp/h3req1-production-remediation-20261029-final/candidate-fingerprint.txt`;
el informe de entrega registra su hash.

### Corte previo de remediación local y preflight de producción — supersedido

El worktree aislado `/tmp/studiamatch-h3req1-production-remediation-20261029`,
rama `codex/h3req1-production-remediation-20261029`, parte de
`desarrollo@6f059a0b27ef38541a7b62503c78920e621f05c1`. El checkout documental
anterior y sus tres documentos WIP, así como el WIP ajeno, se preservan sin
modificación. No hubo commit, push, PR, merge, SQL, cambios remotos, workflow ni
deploy.

**Remediación local:** CA4.6 corrige el falso cambio de auditoría: la UI omite
solo `availability_status` cuando la acción es `publish` y `new_values` no
contiene la clave. `null` explícito, cambios editoriales y eliminación de override
permitida continúan visibles. La prueba sintética focal pasa los cuatro casos.
La severidad del hallazgo original es baja (error de presentación/auditabilidad;
la publicación no cambia disponibilidad ni el evento persistido). El selector
documental ahora agrega el diff y manifiestos para `certificacion -> main` y el
push posterior en `main`; conserva la selección exacta, los pins y los negativos
fail-closed. Sus regresiones focales pasan en Docker.

**Integridad documental:** `--self-test` y el gate candidate-aware pasan en el
árbol candidato, con 749/749 fuentes asignadas. El gate integral sigue en FAIL:
349 diagnósticos en baseline y 348 en el candidato, ejecutados con el mismo
checker/configuración. El baseline conserva un diagnóstico por la proyección
candidate-only observada `304` frente al esperado obsoleto `367`; para el árbol
candidato exacto, el registro refleja 305 rutas candidate-only y 444 fuentes de
integración (443 en baseline), por lo que ese mismatch no se reproduce. Los 348
residuales del candidato se explican por 79 rutas candidate-only
ausentes, 88 relaciones incompletas sobre 20 rutas únicas, 15 exclusiones de
fuentes locales/generadas/cache y 4 exclusiones documentales históricas ausentes
(cada una también reporta stale). El PASS acotado no sustituye el FAIL integral;
no hay disposición vigente para producción.

**Refs y base de producción:** GitHub confirma `desarrollo@6f059a0b`,
`certificacion@03515dee69fc42b10808d1c67cc4e00ebacd0c40` y
`main@70d0f4fee885be0f6780e5d14f466b2a6c897961`. La comparación certificación→main
está divergida (100 commits adelante, 4 atrás, merge base `c80f6504`); el ensayo
local exacto de `merge-tree` fue limpio, árbol sintético
`2028bdc24a720e5a0d19921b559134a9adf77f27`. No equivale a CI ni autoriza la
promoción. El endpoint GitHub de protección de `main` respondió 403; la protección
actual requiere verificación por un lector autorizado antes de abrir el PR final.

**Pro/H2 — preflight SELECT-only completado, sin escrituras:** el MCP WSL
`mcp__supabase_pro` confirmó mediante `get_project_url` el proyecto
`xwhtiqmboljkshrtviyw`. `list_migrations` devolvió 23 versiones, desde
`20260525030610` hasta `20260607221002`; no hay versiones H2/H3 posteriores en
ese ledger. Los catálogos sí muestran el núcleo H2 (`course_editorial_state`,
`course_editorial_audit`, `editorial_field_definitions`, cohorte legacy privada,
vista pública y helpers H2), por lo que el ledger no basta para inferir el estado
de objetos. La cohorte no se leyó ni se invocó el verificador de datos. Los tres
campos del snapshot editorial están ausentes; no hay relaciones, secuencias ni
RPC `admin_*`/`h3_*` en `public`/`private`, incluidos membresías, invitaciones,
colas, quota y gateway. `courses_public_effective` existe como vista
`security_invoker`, con SELECT para anon/authenticated/service_role; el helper H2
es `SECURITY DEFINER`, `search_path=pg_catalog, pg_temp`, EXECUTE explícito para
esos roles. RLS está activo en tablas editoriales; grants/policies y `exec_sql`
se detallan en el checkpoint actualizado.

El ledger no registra las migraciones que corresponden a objetos H2 presentes, y
el contrato H2 de retiro de lectura directa no está activo: anon/authenticated
conservan SELECT en `public.courses`. Esto requiere reconciliar ledger/schema y
cohorte antes de elegir `h2-expand-compat`, `h2-contract-public-reader` o
`h2-contract-legacy-cohort`; no reaplicar por conteo o lista de archivos. La ruta
Pro `DB Sync to Production` solo acepta manifests F10-8/H2, no uno H3. El run H2
`33143730910` es histórico (`93c802c7`), no evidencia del candidato actual. La
matriz de objetos y el orden/dependencias están en el
[checkpoint actualizado](evidencia/h3req1_editorial_contract_2026-10-28.md#preflight-pro-select-only-completado).
No se ejecutaron migraciones, workflows ni llamadas mutadoras.

**Pages/Access:** deployment Production previamente observado
`2b53bc74-576d-4e12-8b80-2986a857bde7`,
SHA `70d0f4fe`, estado success; Pages `studiamatch`, rama `main`, alias
`admin.studiamatch.com`. El URL de Supabase apunta al host Pro; no se leyeron
valores de keys. Producción todavía no tiene runtime BFF H3: faltan
`ADMIN_ALLOWED_HOSTS`, tres HMAC keys distintas por función, `ADMIN_RPC_GATEWAY_KEY_ID`
y binding `ADMIN_QUOTA`. Preview ya liga `ADMIN_QUOTA` al Worker existente
`studiamatch-admin-quota`; sus digests se aíslan por HMAC de ambiente, por lo que
la clave de cuota de Production debe ser distinta a la de Preview. Una consulta
Cloudflare de solo lectura en este ciclo confirmó la aplicación Access
`803f615f-7c2d-4a3d-b99c-b9ab43f543a2` para `admin.studiamatch.com`, sesión `6h`,
una política `allow` con un único selector de correo; no se expuso la dirección ni
se cambió la política. `NEXT_SUPABASE_SECRET_KEY` aparece como `plain_text` en Pages
Production en el metadato sanitizado anterior. La búsqueda local confirma que no
es consumida por `web/` ni Pages Functions; sí la usan workflows/scripts de DB y
pipeline desde sus secretos de ambiente separados. No se leyó su valor. Su retiro
de Pages requiere un JIT propio y rollback desde el almacén seguro. No se volvió a
consultar Pages porque su endpoint de configuración entrega también `env_vars` con
valores y no ofrece una lectura de metadatos aislada.

**NO-GO de promoción productiva:** el preflight Pro ya no está bloqueado por
acceso, pero confirma H3 Admin ausente, snapshot pendiente y discrepancia entre
ledger y objetos H2; falta evidencia de cohorte y el workflow no admite un
manifest H3. El delta local de 13 paths sigue sin commit/PR. El integral documental
mantiene 348 diagnósticos y no tiene disposición para producción. Después de un
candidato integrado aún se requieren gates H2/H3, JIT de SQL/workflow, JIT de
Pages/Access y los PRs protegidos separados. Ninguna autorización de esta pasada
cubre esos pasos. R1–R4 Development 4/4, E1–E6 local 6/6 y smoke Certification 1/1 siguen
cerrados y no se repiten. Detalle y evidencias en el
[checkpoint de remediación](evidencia/h3req1_editorial_contract_2026-10-28.md).

**Continuación y gates documentales — 2026-10-29, 12:58 America/Lima:** el
preflight Pro pasó de “acceso pendiente/reporte TL” a metadata SELECT-only
verificada en este hilo; los objetos, grants, RLS, funciones, vistas y columnas
observados están en el checkpoint. Se conserva como desconocido el contenido de
la cohorte. El self-test/candidate-aware del árbol actualizado pasó en Docker
Node 22 (`DOC_SELF_TEST_PASS`, `DOC_GATE_PASS`, 749/749 fuentes, 119/119 activos,
433/433 históricos); el checker integral repitió exit 1 con 348 diagnósticos,
frente a 349 baseline. El primer intento con la imagen de la app abortó en
infraestructura por `node_modules` desincronizado, antes de cargar el checker;
la corrida Node 22 limpia sí ejecutó los gates. Logs y SHA-256 están en el
checkpoint; fingerprint final del delta de 13 paths en
`/tmp/studiamatch-h3req1-production-remediation-20261029-candidate-fingerprint.txt`,
fuera del worktree.
No se ejecutaron SQL, workflow, escrituras, configuración remota, promoción ni
publicación. El límite de Docker fue resuelto usando la imagen aislada, sin
cambiar permisos del socket.

**Corte anterior, supersedido — 2026-10-29 12:25 America/Lima:** GitHub MCP
reconfirma `desarrollo@6f059a0b27ef38541a7b62503c78920e621f05c1` y
`certificacion@03515dee69fc42b10808d1c67cc4e00ebacd0c40`, ambas ramas protegidas;
`main@70d0f4fee885be0f6780e5d14f466b2a6c897961` queda como lectura previa, no
como candidato de promoción. Cloudflare MCP confirma Access Admin para
`admin.studiamatch.com`, selector único de correo y TTL `6h`; no se cambió. La
lectura Pro seguía pendiente por el catálogo de herramientas de ese corte; el
acceso quedó habilitado y el preflight consta en la actualización siguiente.
Pages no se volvió a consultar porque el endpoint devuelve valores completos de
`env_vars`; se conserva el metadato sanitizado anterior. En Docker/red deshabilitada,
self-test + candidate-aware: PASS (749/749 fuentes, 119/119 activas, 433/433
históricas); integral: exit 1, 348 diagnósticos (baseline 349); scanner de
credenciales: PASS sobre 13 paths; `git diff --check`: PASS. Los logs finales
quedan en `/tmp/h3req1-production-remediation-20261029/final-continuation-*`.
No se repitieron CA4.6/selector funcionales ni aceptaciones E/R/smoke. El candidato
productivo exacto aún no existe: el delta de 13 paths está sin commit en la rama
local basada en `desarrollo@6f059a0b`. La continuación que completa el ledger y el
schema sigue arriba; no hay autorización de publicación o producción.

**Continuación verificada — 2026-10-29 12:45–12:50 America/Lima:** el MCP
`mcp__supabase_pro` quedó disponible tras la intervención de Romel. La URL/ref fue
confirmada, `list_migrations` mostró 23 versiones hasta `20260607221002`, y las
consultas SELECT-only de catálogos confirmaron H2 parcial fuera de ledger, ausencia
de los objetos Admin/H3 y falta de las tres columnas snapshot. En Docker aislado,
red deshabilitada y checkout read-only, el self-test interno pasó y el gate
candidate-aware pasó; el integral conserva exit 1/348 diagnósticos. Logs:
`/tmp/h3req1-production-remediation-20261029/preflight-doc-*`. Los 13 paths siguen
locales, sin commit/push/PR. Siguiente acción: revisar el delta H2/H3 y resolver o
disponer el gate integral para un SHA de producción exacto; no ejecutar SQL ni
workflow hasta aprobación separada.

**Corte anterior — 2026-10-29 11:21 America/Lima (supersedido por esta continuación):** CA4.6, selector
`certificacion → main`, self-test candidato, revisión focal de seguridad y checks
de Docker quedaron ejecutados. Resultado del diff scan Codex Security: cero
findings, limitado al snapshot SHA/digest citado en el checkpoint; las dos
correcciones textuales posteriores se revisaron y registraron por separado. El
checker integral actualizado conserva 348 diagnósticos; no se declara PASS ni GO
productivo. Los cambios permanecen locales, 13 paths, sin commit/push/PR. La
siguiente intervención registrada en el corte actual es habilitar el conector Pro
de solo lectura en este hilo; no implica autorización de publicación.

### Corte histórico — remediación TL de selector y guard previa al PR #510

Este snapshot describe la preparación anterior a la integración #510; se conserva
para trazabilidad y no representa el estado vigente.

**Cierre local actualizado:** suite completa Docker PASS; guard y selección
documental probados contra c80→941 y push de Certification PASS; agregado final
4 paquetes/1.614 paths, checker/self-test 747/747 PASS. Revisión focal final sin
HIGH/CRITICAL/MEDIUM. No hay CI remoto ni commit publicado de esta remediación.
El responsable eligió preparar el acumulado completo. Pendientes inmediatos:
integración protegida de la remediación, gate integral y JIT de configuración;
después promoción y smoke mínimo por ambiente. No se repiten R1–R4 ni E1–E6.

**NO-GO de promoción; bloqueos de selector/guard remediados localmente.** El
responsable eligió preparar el acumulado completo. El guard rechazaba 239 rutas
fuera de las listas H3 entre 1.484 paths protegidos cambiados; ahora solo admite
esas rutas con pins de baseline/origen y metadata Git idéntica a origen, en la
ruta `desarrollo -> certificacion`. Guard real PASS en primer corte y regresiones
negativas PASS; se incluye endurecimiento modo/tipo en la revalidación final.
No hay allowlist por carpeta. El integral `--self-test` conserva 350 entradas:
349 heredadas más self-test fallido por fuente ausente. Scanner final de los 15
archivos, documentación de cierre y `git diff --check` PASS. Ningún pendiente
nuevo de producto acreditado.

La continuación humana de remediación se ejecuta en un worktree aislado desde
`desarrollo@941eca49`, rama `codex/h3req1-certification-remediation-20261028`.
Ambos árboles Git ya se descargaron: el conteo exacto es **9 commits exclusivos
de Certification / 97 de Development**, diff desde ancestro común **1.618 paths**.
El selector local distingue los scopes PR de las selecciones documentales y, solo
en `desarrollo -> certificacion`, construye su unión y la del diff completo con
hashes, conservando el rechazo de ambigüedad en PRs normales. Regresiones Docker
finales PASS, incluida guarda de JSON corrupto, y revisión estática de seguridad
sin hallazgos reportables. Ensayo de promoción con unión de 4 paquetes y 1.613
paths: gate candidate-aware/self-test PASS, 747/747 fuentes. No es CI remoto.
Se copiaron aquí los siete documentos WIP de Luna preservando su worktree.

La lectura Access confirma que ninguna de las cuatro apps inventariadas cubre el
hostname Certification. El alias también falta de `ADMIN_ALLOWED_HOSTS` Preview.
No se cambió configuración. El árbol `c80…` no contiene el checker actual: no se
debe presentar su ausencia como baseline PASS ni como «349 idénticos». Se mantiene
la disposición exclusiva #509 sin extenderla. La incidencia temporal de auto-review
se superó tras aprobación de reintento; clon y ensayo Docker completados. No hubo
commit/push/PR/merge ni operaciones DB.

R1–R4 conserva **4/4** y E1–E6 **6/6**. La protección clásica Certification ya fue
verificada en UI: PR, 1 aprobación, security-audit, rama actualizada y sin bypass.
El paquete de integración y descripción PR están preparados; se solicitó la
autorización específica de publicación y la de ruleset adicional por separado.
El pendiente inmediato es publicar por el flujo autorizado; después configurar
y promover Certification con autorización separada y smoke mínimo. Ver
[evidencia y límites](evidencia/h3req1_editorial_contract_2026-10-28.md#corte-historico-remediacion-local-de-promocion-por-tl-previa-al-pr-510).

### Corte anterior — preparación de promoción H3REQ1 a Certification — NO-GO — 2026-10-28 18:54 Lima

La aceptación mínima del contrato editorial en Development sigue aceptada (R1–R4 4/4); este resultado no se extiende a Certification. El paquete de promoción no está listo para solicitar ejecución: la fuente `desarrollo` es `941eca496676bd11cd0e2796e6c0a34efd62082d`, Certification conserva `c80f6504a3ea353bc2c222df1da09c4b5ba0ae58`, y el flujo de promoción abarca 97 commits desde el ancestro común `a6e39b993b2609641d20e9e24c513f35fd711b96`, no solo H3REQ1.

Bloqueos concretos: (1) el selector `Documentation Source Registry` del workflow no puede seleccionar la colección de manifiestos añadidos desde Certification: hay dos `candidate-pr-scope` con estructura no compatible y cuatro manifiestos candidate-aware válidos, lo que produce invalid structure y, después de corregirlo, selección ambigua. (2) El gate integral de la comparación local HEAD/candidato documental conserva 349 diagnósticos idénticos y el mismo contador 304 en ambos lados; el contraste histórico baseline/candidato de #509 también tuvo 349 por lado, 348 iguales y un cambio en el contador 299→304. La disposición de #509 vence antes de Certification y no se reutiliza. Aún falta el contraste integral exacto `c80… → 941…` en un checkout que contenga ambos árboles. El gate candidate-aware de los documentos locales modificados pasó. (3) Pages Certification sigue en el deployment `3b28949c-7dfe-4b54-bf7a-0db77339d6ab` del SHA `c80…`; el `ADMIN_ALLOWED_HOSTS` de Preview no incluye `certificacion.studiamatch-aty.pages.dev` y su configuración es compartida por los previews no productivos. (4) El detalle de branch protection y Cloudflare Access para el destino no quedó verificado.

La DB es Free `aqrldlmlszjtgpqiegaa`, compartida por Development y Certification. Su ledger ya tiene 83 migraciones, incluidas las dos migrations H3 aplicadas; no corresponde otra aplicación SQL para Certification. No se ejecutaron cambios de configuración, PR de promoción, workflows, migraciones, deploys manuales ni pruebas de negocio en Certification.

La matriz por criterio, evidencia, estado por ambiente, transición/rollback y autorizaciones pendientes está en el [paquete local de promoción y checkpoint](evidencia/h3req1_editorial_contract_2026-10-28.md#preparacion-de-promocion-a-certification). Próximo paso: obtener el árbol exacto `941…`, generar el contraste documental c80→941; preparar una corrección de selector/manifiesto de promoción sin relajar cobertura; después solicitar JIT de configuración Preview para el hostname de Certification y autorización separada para abrir el PR protegido `desarrollo → certificacion`. No hay GO de promoción ni cierre productivo.

### Aceptación remota mínima R1–R4 completada en Development — 2026-10-28 18:34 Lima

La aceptación remota del contrato editorial corregido queda en **4/4 = 100%** (antes de esta pasada: 2/4 = 50%; delta +50 pp). R2 confirmó que un borrador de colaborador no altera lo público; R3 confirmó que la publicación Admin sí expone exactamente el nuevo valor al visitante anónimo. Después se restauró y republicó el texto original autorizado; la última lectura anónima muestra el original y ya no muestra el marcador. R1/R4 se reutilizaron sin repetirlos.

Ejecución en Free/Development `aqrldlmlszjtgpqiegaa`, host `desarrollo.studiamatch-aty.pages.dev`, deployment `27d9ebfc`, merge SHA `941eca496676bd11cd0e2796e6c0a34efd62082d`. La migración `20261028_h3_public_price_projection_empty_price_guard.sql` permanece aplicada una vez bajo JIT, ledger `20261028230928` (83 entradas). La proyección pública anónima terminó HTTP 200; no reapareció `22P02`. R2/R3, versiones v9–v12, recuperación y evidencia por página están en `.context/evidencia/h3req1_editorial_contract_2026-10-28.md`.

GO de aceptación remota mínima Development: **SÍ**, solo R1–R4. No es GO de promoción ni cierre productivo/H3REQ1 total. El FAIL documental integral de 349 diagnósticos sigue visible y separado del resultado candidate-aware. La disposición aprobada cubre únicamente PR #509, owner Romel, vence el 04/11/2026 23:59 America/Lima o antes de promover a Certification; no debe extenderse ni interpretarse como waiver global. Antes de promoción se requiere resolver/disponer el gate documental según el proceso humano y autorización de promoción independiente. No se ejecutó promoción, otro deploy, FG3, writer ni schedule.

### Corte histórico — guard de precio aplicado y lector público recuperado — 2026-10-28 18:19 Lima

El PR #509 quedó integrado en `desarrollo` mediante merge `941eca496676bd11cd0e2796e6c0a34efd62082d`; su HEAD aprobado fue `2b1f533444dab19528d5cb3d912ef6332dc20c41`. El checkpoint del PR registra 16 checks `success`, 2 `skipped`, aprobación humana y la disposición documental acotada vigente; el FAIL integral de 349 diagnósticos permanece visible y no equivale a PASS. No se modificaron protecciones ni se volvió a ejecutar el merge.

Con JIT separado del responsable, se aplicó una vez en Free `aqrldlmlszjtgpqiegaa` (compartido con Certification) `db/migrations/20261028_h3_public_price_projection_empty_price_guard.sql`, SHA-256 `82b8eb0655779f0e82b979cb65a051f2b244b5c4bffb199c5e13c9473132987b`. La versión `20261028230928` aparece en ledger (83 entradas). Verificación read-only confirmó helper seguro, `SECURITY DEFINER`, `search_path=pg_catalog, pg_temp`, ACL sin `PUBLIC`, grants esperados y vista `security_invoker`. El contexto anónimo del curso IDAT vuelve a recibir HTTP 200 y muestra el valor `benefits` original; no reapareció 22P02. No hubo filas de curso modificadas por la migración.

La aceptación remota R1–R4 sigue **2/4 = 50%**: R1 y R4 aceptados; R2 espera revalidación con un borrador nuevo, R3 espera publicación controlada. La lectura pública recuperada no basta para acreditarlos. El colaborador ya completó el acceso en Chrome Windows página 6; el editor confirma curso publicado v8 y `benefits` original. La página Admin 1 sigue en login; intervención solicitada. El JIT exacto de R2/R3 y recuperación está preparado/enviado y pendiente; no se ha usado para escribir. Una vez resueltos esos dos gates, ejecutar solo R2/R3, republicar el original y verificarlo anónimamente; no repetir R1/R4. `git diff --check` pasó. El self-test documental local terminó FAIL con referencias históricas faltantes: 747/747 fuentes asignadas, sin cambiar relaciones. Se conserva el FAIL integral y la disposición exclusiva a #509. Corte de esta continuación: 2026-10-28 18:19 Lima; las solicitudes de intervención Admin y aprobación JIT no estaban respondidas. Detalles y evidencia en `.context/evidencia/h3req1_editorial_contract_2026-10-28.md`.

### Antecedente — primer corte remoto del contrato editorial H3REQ1, 2026-10-28

PR #508 fue aprobado sobre `85e9d1b17ca2808ed320ba2c37d893fbf7619dad` y mergeado
a `desarrollo` en `77b3f4ea27a8aaa6d1d0571ee5a9b5f1afd264a3` el 2026-10-28
12:39:06 America/Lima. El head del PR tuvo 16 checks `success` y 2 `skipped`;
esto no acredita aceptación Development. La aprobación no dispone el FAIL integral
documental heredado ni equivale a una disposición específica de ese gate.

Pages ya sirve la rama Development en
`https://desarrollo.studiamatch-aty.pages.dev`: deployment
`27d9ebfc-1ff4-4c43-b58f-117d98977cd0`, rama `desarrollo`, SHA del merge, estado
`success`. El Preview del PR es distinto: deployment
`920821c9-5fdb-4dbb-94d6-6dc1b9e840af`, rama feature y alias propio; no se usa como
deployment Development.

En Free/Development (`aqrldlmlszjtgpqiegaa`, instancia compartida con Certification)
el preflight previo mostró 81
migraciones y ausencia de `20261028_h3_editorial_publication_snapshot`, con columnas
y RPC/vista bajo contrato anterior. Tras el JIT exacto del responsable, la migración
integrada se aplicó una vez y se verificó en ledger como versión `20261028194353`
(2026-10-28 14:43:53 America/Lima). Existen las tres columnas nullable y ambos
checks; las RPC reemplazadas y la vista `security_invoker` tienen las firmas/grants
previstos. No hubo backfill ni escritura de cursos. El schema se comparte con
Certification por proyecto, pero no hubo una operación separada allí. La incompatibilidad app/schema
observada en preflight quedó resuelta por esta aplicación; no se repitió deploy.

La aceptación remota usa exclusivamente R1–R4 (4 criterios). Baseline de esta
pasada: **0/4**. Resultado al 2026-10-28 15:07 America/Lima: **2/4 aceptados
(50%, delta +50 pp)**; R1 y R4 aceptados, R2 falló y R3 no se ejecutó. E1–E6
locales siguen como evidencia separada y no se reutilizan como R1–R4. El
responsable completó el acceso del colaborador en Chrome Windows; se verificó el
editor con rol colaborador en la misma página aislada. Esto fue una espera de
intervención humana resuelta, no un defecto ni bloqueo técnico.

Durante el único pase autorizado, el colaborador guardó y recargó el marcador
temporal en `benefits` (v6→v7); el preview de Admin siguió mostrando la publicación
anterior y declaró que el borrador difería hasta publicar. Antes de una publicación
Admin, la ruta anónima del mismo curso falló al consultar
`courses_public_effective`: HTTP 400, código Postgres `22P02`, `invalid input syntax
for type numeric: ""` (requests 82 y 116, antes y después de recuperar el valor).
Por ello R2 **FALLÓ** y R3 quedó **PENDIENTE** sin publicarse el marcador. La fuente
integrada contiene un cast sin guarda para `published_editorial_values.price_pen`;
es la causa probable, respaldada por código y mensaje del error, pero no se leyó la
fila operativa para afirmar el contenido exacto que lo disparó.

La recuperación autorizada restauró el texto original de `benefits` (v7→v8), con
auditoría append-only. Admin verificó que v8 está publicado y que el valor original
coincide. No se ofrecía acción de publicar porque ya no había diferencia de borrador
y snapshot; no se despublicó. El contexto anónimo siguió mostrando el error 400, así
que no se afirma verificación pública de la recuperación.

R4 **ACEPTADO**: historial cerrado inicialmente, abierto y cerrado con teclado; se
consultaron los eventos de la pasada con identificadores de actor sanitizados. La
insignia de versión v8 midió 32,6 × 26,1 px. Preview distinguió borrador y snapshot
publicado. La captura remota de estado funcional terminó sin publicar el marcador.

El fix forward-only está preparado en el worktree aislado
`/tmp/studiamatch-h3req1-public-price-projection-20261028`, rama
`codex/h3req1-public-price-projection-20261028`, desde el merge
`77b3f4ea27a8aaa6d1d0571ee5a9b5f1afd264a3`. La migración transforma solo la
definición del lector público: acepta precio decimal acotado a 63 dígitos enteros y
63 fraccionarios; vacío, no numérico o sobredimensionado se vuelve `NULL`. Falla
cerrada si la función o el único cast esperado cambiaron. No escribe filas. El
harness PG17 sintético pasó después de aplicar la migración dos veces; ocho fixtures
cubren vacío, decimal, JSON null, inválido, límites, overflow y fallbacks legacy.
El test Python focal pasó 1/1 y ShellCheck 0.11.0 pasó sobre el runner final. La
migración correctiva no está aplicada ni desplegada.

El gate candidate-aware documental exacto seleccionado por `security-audit` pasó
en baseline y candidato: 742/742 y 747/747 fuentes asignadas, sin diagnósticos; el
self-test pasó. El checker integral sin manifiesto sigue FAIL en ambos: 349
diagnósticos por árbol, 348 idénticos; el único delta es el contador heredado de
rutas candidate-only (`299 != 367` en baseline y `304 != 367` en candidato), que
sube por las cinco fuentes nuevas registradas. La captura completa está en
`/tmp/studiamatch-h3req1-doc-results/`; listas exactas y diff:
`baseline-failures-exact.txt`, `candidate-failures-exact.txt` y
`failure-delta-exact.diff`. El diff estable baseline→candidato tiene SHA-256
`6b8aa40f4123df8e72dbf3bee61286bb05fee938bf9c39b038b08f73215a32cb`. No se
eliminaron ni inventaron referencias históricas. El primer gate candidate-aware del
candidato reportó dos anchors rotos por el cambio del título operativo; se restauró
`## Corte vigente` y el resultado posterior fue PASS.

La revisión del diff encontró y corrigió un warning ShellCheck (`SC2034`) en el
contador de readiness. El scan Codex Security focal `b4f8c079-a0b5-489d-acae-d941bb1c31ec`
terminó con 0 findings/reportables y cobertura manual de los 15 paths cambiados
(4 paths en el worklist del plugin y los 11 restantes revisados por el agente). Su
snapshot es `codex-security-snapshot/v1:sha256:018d8d187e42a5e75e676c2e63784469c11066fb5e102381de200f93ea681db4`;
reporte:
`/home/romel/.codex/state/plugins/codex-security/scans/studiamatch-h3req1-public-price-projection-20261028/77b3f4ea27a8aaa6d1d0571ee5a9b5f1afd264a3_20261028T204548Z_rko0su6k/report.md`.
El preflight registró que workers delegados no estaban disponibles; se inspeccionó
el diff completo localmente. Es una revisión estática focal, no auditoría global ni
comprobación remota.

Las validaciones locales finales observadas en Docker pasan: harness PG17 con
migración aplicada dos veces y 8 fixtures; test Python 1/1; ShellCheck 0.11.0 con
resolución del `source`; `actionlint` 1.7.12; guard de paths con positivos y vecinos
negativos; y gate candidate-aware R21/self-test (747/747 fuentes, 0 diagnósticos).
El checker integral sigue FAIL y se mantiene separado. En el commit local
`3b1123dd110f445dd64c16684e257512f4c8e1dc` pasaron el credential scan pre-commit,
el scan del diff exacto y `protected_path_scope_guard.sh --compare-candidate` contra
`77b3f4e`; los paths protegidos quedan admitidos dentro del scope H3. El siguiente
paso se completó: PR #509 está abierto a `desarrollo` desde
`codex/h3req1-public-price-projection-20261028`, base
`77b3f4ea27a8aaa6d1d0571ee5a9b5f1afd264a3`, HEAD
`7cc3280351b3806853e48fd8993315a33619c3f9` (2 commits, 15 paths). URL:
`https://github.com/romelhc95/studiamatch/pull/509`. En ese HEAD, el check-run
terminó 16 `success` y 2 `skipped`; `security-audit`, PostgreSQL DB Change Gate,
Credential Scan, Protected Path Integrity, Documentation Source Registry, Python,
TypeScript, ESLint, Static Build, actionlint/ShellCheck, PWI y CodeQL están en
`success`; Cloudflare Pages informó `success` para el preview automático. Supabase
Preview y H2 Main Production Expand Gate fueron `skipped`. No hubo smoke de negocio
ni promoción. El PR no está aprobado ni mergeado. Este corte agrega un commit solo
documental; el SHA resultante y sus checks más recientes se registrarán en la
descripción del mismo PR tras completar esta actualización.

En el primer intento de push, el hook pre-push escaneó el árbol entero porque la rama
nueva aún no tenía upstream y notificó un patrón credential-like en
`scripts/maintenance/debug_autocad.py`, path inalterado y fuera del diff. No se copió
ni expuso el valor, ni se modificó el archivo. Se fetched `desarrollo`, se verificó
que era exactamente el baseline y se configuró temporalmente como upstream para la
rama nueva, mecanismo previsto por el propio hook; el hook escaneó el diff real y
pasó, así como el credential scan de CI. Esto no cambia el riesgo/estado del archivo
histórico, que no pertenece a este PR. El push fue no forzado.

La migration correctiva y una nueva pasada remota R1–R4 requieren JIT separados;
la autorización consumida no se reutiliza. Antes de integrar, owner TL/documentación
debe disponer el FAIL integral histórico; PR/CI no equivalen a GO Development.

No declarar GO Development: R2 está FALLÓ y R3 sin ejecutar. El FAIL documental
integral permanece visible y sin waiver; el PASS candidate-aware del paquete es un
resultado distinto y acotado. La revisión semántica universal de páginas HTTP 200
sigue trazada a H1. No se operaron writers, FG3, schedules, Pro, promoción ni deploy
manual.

La revisión semántica universal de páginas HTTP 200 sigue trazada a H1. No se
ejecutaron pruebas con cursos fuera del paquete, writers, FG3, schedules, promoción,
deploy manual ni pruebas sobre Pro.

El corte, evidencia ejecutada/reutilizada, matriz remota antes/después, autorizaciones,
efectos persistentes, límites y siguiente paso exacto están en el
[checkpoint del contrato editorial](evidencia/h3req1_editorial_contract_2026-10-28.md).

## Corte histórico — reconciliación H3REQ1 post-merge 2026-10-21

**Reconciliación H3REQ1 post-merge — 2026-10-21:** GitHub API confirma PR #501 cerrado y mergeado en `8ac174d81cf6ce23658bff132236a78935ace1ad` el 2026-10-21 03:12:35 UTC, desde el head aprobado `2144dddfb200e83d02b7a55b46db84098e2e78f4`; la aprobación de `romelhc95-approver` sobre ese head es del 03:11:47 UTC. El run `39537032896` terminó: 11/11 jobs ejecutados `success`, uno omitido (`H2 Main Production Expand Gate`). La vista de Checks compartida por el responsable muestra 16 verdes y 2 omitidos en el head, y 16 verdes y 1 omitido en el merge. La lectura del check `Supabase Preview` indica que la rama no está asociada con ninguna Supabase Branch; el detalle enlaza al proyecto Pro, sin que se haya efectuado una operación allí. Esto cierra el PR, no la aceptación H3REQ1.

Lectura directa de Check Runs sobre SHA exactos reconcilia la vista: head aprobado 18 runs (16 `success`, 2 `skipped`) y merge 17 (16 `success`, 1 `skipped`); ninguno publica `Protected Workflow Integrity`. El run de Actions contiene 12 jobs (11 `success`, 1 `skipped`), porque no incluye los checks publicados por otras Apps.

El deployment Pages de Development fue confirmado en pantalla por el responsable: ID `09cf72f3-3b39-4385-892b-b59d995ba390`, rama `desarrollo`, SHA merge, estado Success y alias `https://desarrollo.studiamatch-aty.pages.dev`. El hostname temporal del deployment no es el host Admin autorizado. La conexión del verificador PWI independiente sigue sin acreditar: el Worker recibió `check_suite.requested` y respondió HTTP 202 `ignored`; el job Actions `PWI Worker Contract` es una prueba del código, no un check de la GitHub App. La API de GitHub confirma que `desarrollo` está protegida y expone como check requerido solo `security-audit` (`app_id=15368`, GitHub Actions).

Confirmación humana adicional del 2026-10-21: `StudIAMatch PWI Verifier R3` está instalada solo en `romelhc95/studiamatch`; `Pull requests` es Read y `Checks` Write; están suscritos `pull_request`, `pull_request_review` y `check_run`. En el Worker se confirmaron los cuatro nombres y tipos requeridos, la coincidencia del secreto webhook entre GitHub y Cloudflare y que `GITHUB_INSTALLATION_ID` coincide con el ID localizado en GitHub, sin registrar valores. R3/R3-DO se usaron para configurar e instalar la App y desplegar/configurar el Worker/DO. En Advanced, el responsable revisó las entregas de los últimos tres días y confirmó solo dos `check_suite.requested` y un `ping`; los dos `check_suite.requested` respondieron HTTP 202 `ignored`, como espera el Worker para ese tipo. No hay una fila `pull_request` que corrobore el reporte previo de HTTP 200 para `pull_request/synchronize`; ese status además no coincide con la respuesta actual de aceptación (`202 queued`/`already_queued`). La consulta read-only de PRs abiertos devolvió cero; verificar un evento vivo del proveedor requeriría una nueva PR y no se creó ninguna. No se observó `Protected Workflow Integrity` en los SHA exactos del PR. La rama clásica `desarrollo` exige `security-audit` con fuente `any source`/GitHub Actions y requiere estar actualizada; la API `GET /branches/desarrollo` confirma `protected=true` y `security-audit` como único check (`app_id=15368`). Al buscar `Protected Workflow Integrity`, GitHub mostró el nombre en el selector y, al añadirlo solo al formulario sin guardar, la fuente fue `GitHub Actions/any source`; no se guardó. Ese origen no acredita ni restringe al proveedor PWI. La única ruleset activa `owner-only-protected-branch-updates` aplica a `desarrollo`, `certificacion` y `main`, con solo la regla `update`; tiene un actor con bypass `always`, no usado ni modificado. El detalle del endpoint clásico sigue devolviendo HTTP 403 al conector, pero la respuesta de branch y la pantalla humana confirman los checks vigentes. PWI no está exigido por la regla clásica ni la ruleset. El delta R6 está aprobado para redelivery de una fila `failed` del PR 501; no hay evidencia de que esa ruta se ejecutara y, tras el merge, no aplica a otro PR ni autoriza una operación distinta. La App `StudIAMatch Bootstrap Guardian` no tiene referencias en el checkout ni resultado de búsqueda pública por nombre exacto; su función y uso actual quedan desconocidos, sin cambios ni desinstalación.

Supabase Free: el responsable confirmó que la lista conserva la Redirect URL antigua del preview y contiene `https://desarrollo.studiamatch-aty.pages.dev/admin/auth/callback/`. Confirmó los seis nombres de Edge secrets y después guardó cuatro `ADMIN_INVITE_*`; no se leyeron ni confirmaron valores por chat. El preflight OPTIONS al Edge `admin-invite` responde HTTP 200 con `Access-Control-Allow-Origin` exacto de Development. MCP Supabase confirma `admin-invite` ACTIVE v20, `verify_jwt=true`; el archivo remoto `index.ts` coincide byte a byte con la fuente del merge (SHA-256 `1569b90394b313a4b42e4e50158da077cec42d26356c0d713b16535f47053a60`). El proyecto Free está `ACTIVE_HEALTHY`, con 80 migraciones; la última es `20261010_h3_admin_members_service_select` (`20261014144922`). `send-lead-emails` está ACTIVE v27 y su handler remoto devuelve 410 `Gone`; no tiene caller en el árbol actual y el recorrido público muestra el canal de solicitudes cerrado, por lo que no se redepliega solo por número de versión. Cloudflare API docs/search fallaron con error interno; no se tomaron como evidencia de configuración Pages. El reporte R19 conserva la lectura Preview del 2026-10-18 (binding `ADMIN_QUOTA`, HMAC secret types, hosts/URL Free, flags locales ausentes y `NEXT_SUPABASE_SECRET_KEY` ausente); el responsable confirmó posteriormente el `ADMIN_RPC_GATEWAY_KEY_ID` Text y ahora volvió a confirmar que `NEXT_PUBLIC_SUPABASE_URL` apunta al proyecto Free. No se repitió ese inventario sin indicio de drift.

Confirmación humana posterior del 2026-10-21: la persona informa que guardó ambas plantillas Auth y verificó `Site URL = https://desarrollo.studiamatch-aty.pages.dev/admin/auth/callback/`; también confirma que se conservaron las dos Redirect URLs: el destino legacy de Preview y `https://desarrollo.studiamatch-aty.pages.dev/admin/auth/callback/`. Esta es evidencia de intervención humana, no relectura por API ni prueba funcional aprobada. Las fuentes versionadas usan `{{ .RedirectTo }}` + `{{ .TokenHash }}` hacia el callback BFF para `invite` y `recovery`; el contenido actual de las plantillas no se releyó mediante API. El reset manual desde Dashboard depende del fallback Site URL y no se ha vuelto a ejecutar. Free se comparte con Certification.

Corrección MFA local en el checkout aislado, hija directa del merge `8ac174d81cf6ce23658bff132236a78935ace1ad`: el cliente maneja los niveles AAL nulos que devuelve el SDK en una sesión convencional, y AdminCourseQueue los interpreta como AAL1 sin relajar su requisito AAL2. La acción BFF `recovery_assurance` contrasta esos niveles con un inventario validado; reconoce `totp`, `phone` y `webauthn`, pero devuelve únicamente IDs TOTP verificados. Si la cuenta tiene un factor verificado no compatible, la lectura está malformada o `nextLevel=aal2` no tiene un TOTP verificable, la pantalla falla cerrada. Revalida el factor seleccionado antes del challenge y exige confirmar `aal2` antes de habilitar contraseña. La ruta BFF de cambio de contraseña vuelve a leer inventario y assurance y requiere `currentLevel=aal2` cuando hay factores verificados o `nextLevel=aal2`; respuestas inconsistentes/indisponibles fallan cerradas antes de `updateUser`. No enrola ni elimina factores y mantiene tokens en cookies HttpOnly/server-side. Esto implementa el contrato documentado por Supabase: `aal1` o `null` representa autenticación convencional y `aal2` autenticación con MFA ([getAuthenticatorAssuranceLevel](https://supabase.com/docs/reference/javascript/auth-mfa-getauthenticatorassurancelevel)).

Validación local en Docker del árbol actual: ESLint pasó con 0 errores y nueve warnings en `HomeContent.tsx` sin cambios; TypeScript pasó. `tests/h3_admin_bff_mock_uat.mjs`: 127/127; funciones focales de recuperación/MFA: 14/14, `test_password_policy_contract.py`: 4/4 y `h3_admin_auth_error_uat.mjs`: 7/7. Las funciones Python se invocaron directamente (no pytest); `py_compile` 2/2 pasó con caché fuera del montaje read-only. El build estático pasó en copia temporal con URL Free y una publishable key de fixture no secreta, sin Auth remoto; el intento offline previo no pudo obtener las fuentes de Google Fonts y el primer intento de la copia sin configuración pública necesaria falló antes de prerender, ambos corregidos en la corrida final. Guard/negativos del manifiesto y cotejo candidato PASS; `bash -n` y ShellCheck 0.11.0 PASS; credential scan árbol PASS. Documentation Integrity/self-test PASS con el comando CI y manifiesto R19: 732/732 fuentes asignadas, 722/732 relaciones completas, 113/113 docs activos alcanzables, 433/433 históricos enlazados, 9.247 enlaces y 4.625 anchors. `h2_web_mock_smoke.sh` previo pasó con fixture sintético catálogo/detalle; no es aceptación remota. El diff de código MFA quedó revisado por Codex Security en el scan completo `377ea7e4-8f4c-458c-a4ad-5444db17de16`, rango `8ac174d81cf6ce23658bff132236a78935ace1ad..13f3855810f138f7f37a82fc50e37ed043c2c124`, snapshot `codex-security-snapshot/v1:sha256:1a7f55acac262aa4db3e4005276ecc6240274a4493a141a157bdbf8f8934d047`: cinco superficies, 0 findings, sin HIGH/CRITICAL. Revisión estática e independiente de arquitectura; no prueba Auth remoto, despliegue, cuentas ni la App PWI. La confirmación Auth (plantillas guardadas, Site URL callback y dos Redirect URLs conservadas) es humana, no relectura API ni prueba funcional. La última edición Obsidian pasó `git diff --check`; falta completar el cuerpo PR antes de publicar. La autorización vigente cubre push de esta feature y PR protegido solo hacia `desarrollo`, no merge ni deploy. El AAL2 observado anteriormente fue en Preview; no se atribuye a Development.

Smoke GET de solo lectura al alias autorizado, deployment merge: `/`, `/courses/`, `/admin/login/`, `/admin/auth/callback/` y `/admin/reset-password/` devolvieron HTTP 200 y `text/html`. Esto confirma que Pages sirve esas rutas, no que Auth/callback/MFA funcionen ni acredita ningún caso D. La raíz no procesa los parámetros de callback; el callback BFF acepta `type=recovery` y luego redirige a reset. Supabase documenta que `Site URL` es el destino por defecto cuando no se entrega `redirectTo` ([Redirect URLs](https://supabase.com/docs/guides/auth/redirect-urls)). La persona confirma que Site URL ahora apunta directamente al callback Development y que ambas plantillas se guardaron; la configuración no fue rereleída por API y no se ha validado funcionalmente con un correo. No se envió otro correo.

| Gate | Estado y denominador |
|---|---|
| CI PR #501 | Head 16/16 checks no omitidos satisfactorios; 2/18 omitidos. Merge 16/16 no omitidos; 1/17 omitido. Run de Actions: 11/11 jobs ejecutados satisfactorios, 1/12 omitido. |
| Integración | 1/1 PR previsto integrado en `desarrollo`; no implica aceptación. |
| Configuración | Redirect URLs: 2 entradas confirmadas por la persona (legacy + callback). Site URL: la persona confirma `https://desarrollo.studiamatch-aty.pages.dev/admin/auth/callback/`. También confirma que guardó ambas plantillas tras ajustar sus enlaces de acción. Registro humano; sin relectura por API ni prueba funcional. El JIT Auth para estas URLs/action hrefs se consumió dentro del alcance autorizado. Edge: 4 nombres/tipos y CORS preflight constan en el corte previo, no se revalidaron ahora. Pages: inventario requerido aún no completo, sin porcentaje agregado. |
| Verificador independiente | 0/1 check PWI confiable observado; en los últimos tres días hubo 2 `check_suite.requested` `ignored`, 1 `ping` y 0 entregas `pull_request`; PR abiertos 0; la rama clásica exige solo `security-audit` (`app_id=15368`) y el selector PWI ofreció `GitHub Actions/any source`, no la App. La ruleset activa no exige PWI. |
| Deployment Development | 1/1 deployment identificado con Success; no sustituye las pruebas remotas. |
| Aceptación remota | 0/14 casos D satisfactorios y 0/11 grupos adicionales satisfactorios. La recuperación observada fue en el host Preview antiguo y falló AAL2; no se atribuye a Development. |

Revisión Codex Security del scan `4238a8af-36cb-495e-811c-6a3cbf72e394` y snapshot `codex-security-snapshot/v1:sha256:32e1604aefeda72015b7435753dcb894d9b71eae2564046ee76c29ed3da45ecb` queda como evidencia histórica completa de cero hallazgos en un snapshot previo; no cubre el gate explícito de contraseña añadido después. El scan `822d5811-2de4-4ffa-8b83-2335dc605a62` quedó en discovery con digest `ae1b8703…` y cubre la versión anterior del gate; la lectura del helper de preflight fue `ready`, pero la publicación de esos checks fue rechazada porque el scan ya había avanzado de fase. Se preservan ambos registros sin declararlos como revisión final del árbol actual. El scan preliminar `4458dd69-ae48-4990-b0bf-1e8b4efc296e` queda preservado como parcial/supersedido: detectó incompatibilidad con factor `phone`, corregida y cubierta por UAT mixta. La revisión exacta actual ya está completa en `377ea7e4-8f4c-458c-a4ad-5444db17de16` con 0 hallazgos y cinco superficies cubiertas; su alcance es el diff local y no acredita ejecución remota. El manifiesto R19 todavía incluye el workflow PWI retirado, por lo que el pase de integridad documental no acredita operación PWI ni aceptación remota. Smoke GET anterior al alias de Development acredita rutas 200 `text/html`, no Auth ni aceptación remota.

**H3REQ1 permanece NO-GO Development.** La instrucción humana vigente amplía la aceptación operativa a sesión/MFA/recuperación remota; la atestación cliente versionada anterior aún clasifica MFA remoto fuera de su gate y no se modifica por inferencia. La aceptación contractual queda pendiente de evidencia sanitizada alineada con el alcance vigente. Mantener `main`, `certificacion` y Production fuera.

**Siguiente intervención humana exacta:** cuando se abra el PR de esta corrección, revisar el SHA nuevo y emitir aprobación humana sobre ese SHA. La autorización vigente no incluye merge ni deploy. La aceptación remota y D01/D02 seguirán pendientes de la intervención autenticada del responsable y de los paquetes de cuenta ya aprobados; no se hará ninguna operación en cuentas durante este ciclo. Gmail y sus factores permanecen intactos. No compartir contraseñas, códigos MFA, enlaces/tokens ni datos de cuenta por chat.

### Registro histórico pre-merge: candidato z30 y PWI R3

**Corte histórico PWI R3/z30 — 2026-10-20 01:51 UTC:** candidato sucesor z30 en `/tmp/h3req1-pwi-r3-validation-20261020z30/repo`, reconstruido desde baseline `4eb4d877a50b012bb630a129bd0c74482c33be9c` para publicación protegida a `desarrollo`; el último SHA remoto documentado del PR 501 sigue siendo `a73af141…`. El manifiesto enumera fuentes/pins y permisos; el registro de ejecución separado contiene resultados y limitaciones. Sin GO Development ni aceptación remota.

La revisión independiente exacta de z24 (`c4d8c3e1762aa94678a6f10e02eabcbd447414d7`, tree `20a8a91ca1660bf36e1c42b4e376ad70b25de7f9`, scope `d337722c6a8c22eb3c2c3ec64d20eee95a31218ba5bb887dadf986e684f09187`) confirmó que no hay hallazgos HIGH/CRITICAL de código, pero emitió NO-GO P2: body y manifiesto aún marcaban R6 pendiente y el body apuntaba a z21. R6 está aprobado y sin consumir: `/tmp/h3req1_pwi_r3_failed_row_redelivery_jit_delta_20261020_r6.md`, SHA-256 `e19f5eba1b6be5b56be295f3ae62a863db910ee69692c7134ba4e3cc625f9d7e`. z25 corrigió esos estados. En Docker pasaron scanner árbol+diff, self-test documental, scope/negativos, guard y contrato de estado 8/8. La verificación detuvo su finalización porque el body/registro afirmaban 10/10 hashes idénticos a z20 cuando solo nueve hashes de implementación/pruebas/configuración/lock coinciden y el README está modificado. La invocación del auditor de plantilla no encontró el auxiliar montado y no se cuenta; no hubo review independiente. z25 se preserva como snapshot intermedio, no se publica. z26 corrige el conteo y pasa en Docker escáner árbol/diff (0 hallazgos), documentación/self-test (732 fuentes, 9.247 enlaces, 4.625 anchors), scope/negativos/guard (1.196 rutas; 13 catálogos/1.173 referencias; negativos 3/1/1/3/2), plantilla (10 títulos/10 enlaces/16 filas/0 placeholders), contrato de estado (8/8) y diff incremental z25→z26 (4 archivos de contexto). Python 46/46, actionlint y ShellCheck se reutilizan solo por inputs idénticos. La primera comprobación de identidad falló por un expected abreviado en el helper; al corregirlo, z26 pasó con commit `af1026ab3bbd3cb6402fd7470fb369613179749a`, tree `e776eae92029242bbc8d8f9211228d8342428ee3`, padre `4eb4d877a50b012bb630a129bd0c74482c33be9c`, scope `7953df020b14cd5a9eb98fc6a6bc6bde88debbfd1febf436fb2c09cfd2f04738`, 9/9 hashes de implementación/pruebas/configuración/lock y 798 archivos no contextuales idénticos a z20. z27 corrigió el baseline abreviado y pasó sus gates e identidad. z28 registró esos resultados; sus propios gates Docker e identidad exacta también pasaron. z29 tuvo gates Docker PASS e identidad exacta; su review exacta encontró NO-GO P2 documental (código PASS, sin HIGH/CRITICAL). z30 corrige el estado desactualizado y separa el inventario de fuentes de los resultados de ejecución. Inputs ejecutables, permisos, recursos, datos, límites y ambientes sin cambios.

Validación z26 ejecutada: los gates locales y la identidad exacta constan en el registro de checks; el primer error del verificador se conserva como fallo del helper, no del snapshot.

Validación z27 — commit `c5660af200b0d58521639294e5a7569c9e72be28`, tree `bfb5bfa1b512a9cd7214cbab0976b2a45817c16b`, padre baseline completo, scope `727e1c5af934bc1656fa71dcfab3fcf8e183c8487e5f4af63057fe016504359b`: identidad limpia; 9/9 hashes de código/pruebas/config/lock y 798 archivos no contextuales idénticos a z20; 1.190 rutas, 39 artefactos, 13 catálogos/1.173 refs. Docker: scanner árbol+diff sin hallazgos; docs/self-test 732 fuentes, 9.247 enlaces, 4.625 anchors; scope/negativos/guard 1.196 rutas y 3/1/1/3/2; plantilla 10 títulos/10 links/16 filas/0 placeholders; contrato de estado 8/8; diff incremental z26→z27 cuatro archivos de contexto. Python 46/46, actionlint y ShellCheck se reutilizan solo por inputs idénticos. Primera aserción de identidad falló por expected abreviado del helper; se corrigió el helper y la identidad exacta pasó. Ninguna operación remota ni revisión independiente de z27.

Validación z28 — commit `3ec2d71a623ccfe021a9c52b3d9ec46806d5afac`, tree `c41fdf712f7ecd857b0508c856de14029a5822bf`, padre baseline completo, scope `afed3817c7156d94d6262811920b6c944097242ffaea764b25bab5c312598729`: identidad limpia; 9/9 hashes de implementación/test/config/lock y 798 archivos no contextuales idénticos a z20; 1.190 rutas, 39 artefactos, 13 catálogos/1.173 refs. Docker: scanner árbol+diff sin hallazgos; documentación/self-test 732 fuentes, 9.247 enlaces, 4.625 anchors; scope/negativos/guard 1.196 rutas y 3/1/1/3/2; plantilla 10 títulos/10 links/16 filas/0 placeholders; contrato estado 8/8; diff incremental z27→z28 cuatro archivos `.context/`. No se repitieron suites funcionales intactas; sin operación remota ni revisión independiente.

**Resultado exacto z29 preservado:** commit `b97e439d85933e4c5b5061b64978c1281bb95dde`, tree `43c1b229b759289db8cdc57765013667b22030aa`, scope `5a6f23237c05c6a22863ec4f7465ceb425320ec0b7575a1eabd49731eb4a05cb`; 1.190 pins, 39 artefactos, 13 catálogos/1.173 referencias. Escáner completo árbol+diff PASS (0 findings); documentación/self-test PASS (732 fuentes, 9.247 enlaces, 4.625 anchors); scope/negativos/guard PASS (1.196 rutas; negativos 3/1/1/3/2); plantilla PASS (10 headings, 10 links, 16 filas, 0 placeholders); contrato de estado 8/8; diff incremental z28→z29 PASS en cuatro archivos `.context/`. Python focal 46/46, actionlint, ShellCheck y suites Worker se reutilizaron por inputs idénticos. La revisión independiente z29 fue NO-GO P2 solo por body/manifiesto desactualizados; el código fue PASS, sin HIGH/CRITICAL/P1. El revisor comprobó pins, hashes y cierre de catálogos; no ejecutó pruebas. El diff-check directo baseline→z29 no podía leer el blob histórico `03d85fc4…`; el objeto se recuperó después desde GitHub y su identidad ahora está verificada.

Lectura remota de solo lectura realizada: se recuperó el blob histórico `IMPLEMENTATION_PLAN.md` desde GitHub para verificar identidad; no hubo escritura, registro/despliegue App/Worker, secretos, push, actualización de PR, merge ni aceptación.

**Siguiente gate:** revisión independiente exacta de z30. Tras PASS, ejecutar el alta/instalación App, entrada segura de secretos, despliegue `studiamatch-pwi-verifier` con `PWI_COORDINATOR`/`PwiCoordinator` SQLite, exigir el check del App solo en `desarrollo`, y publicar el sucesor. R3/R3-DO y R6 siguen aprobados en sus alcances; R6 no consumido. Después esperar checks completos y revisión humana vigente del SHA sucesor antes de integración. `main`, `certificacion` y Production fuera.

**Histórico de corte PWI R3 — 2026-10-19 22:44 UTC:** candidato `/tmp/studiamatch-pwi-r3-20261019`, rama `codex/pwi-r3-successor`, publicación prevista `feat/h3req1-sync-20261018-r19`, base `4eb4d877a50b012bb630a129bd0c74482c33be9c`, sucesor del SHA histórico `a73af141d8419889ae6922f21e416b207a297391`. Z4 (`7fc1df1b77922de6e0aa74b5c815d28542a3bd65`, tree `241badd0c01c29ae02b3c3289bf71f654bf1d11c`, scope `60b8d41b5b74e5233021ac37df084f171f8c249d5f390e86deef2a9876d50914`) conserva el NO-GO independiente por HIGH/P2. Z5 (`1d5216123c8dd9a966a5c41c1b4de45fd035a9db`, tree `50bebdde27209bb1608c89dd994fc8148f325eb6`, scope `4d4bf03a3810f58f4a9977c1a188b7c3481587db5c53bfc7fed2732f773c8c3f`) tiene el mismo Worker defectuoso y también es NO-GO. Z6 se reconstruyó desde baseline y selección exacta: commit `4edaa116a46767d0a6b7faa78a381ff03f5667b2`, tree `7623f857f1c28ac9a4c68fea9af991795e913beb`, scope `cfc140d70e3147a3e2a9370d18470491718ff3db593da31b09eebc0c7b1002b7`, 1.190 rutas/39 artefactos/unión 1.196/diff esperado 1.195. Z6 pasa escáner completo, gate documental/self-test con manifiesto, guard/negativos, estado 8/8, `npm run check`, Worker unitarias 32/32 y diff incremental `a73..z6`; falla el audit cuerpo/plantilla porque el cuerpo añadía una fila `PWI Worker` fuera de las filas versionadas. La fila extra se quitó en la fuente para z7; z6 queda inmutable y NO-GO.

Corrección local actual: la redelivery pendiente/en proceso vuelve a invalidar el SHA normalizado almacenado para ese delivery (incluido el SHA confirmado por API en overflow), no el SHA posiblemente obsoleto del payload. La regresión da rojo con z5 y verde con el fix. En z6, Docker Node 22.22.0 pasó `npm run check` y unitarias 32/32; el runtime 4/4 ya había pasado sobre la misma fuente/código y se reusa solo al comparar los hashes de todos sus inputs. Los intentos de runtime directo sobre z6 no se cuentan como PASS: el directorio fuente `node_modules` estaba vacío; una copia de caché produjo `vitest: Permission denied` y al invocar Vitest con Node faltó su optional binding WASI. Z7 repetirá el runtime con el paquete de dependencias correcto o conservará el gate pendiente con causa demostrada. `git diff --check a73..z6` pasó; `4eb..z6` no pudo leer el objeto local `03d85fc4…` y no se declara PASS. El audit cuerpo/plantilla de z6 encontró 17 filas frente a las 16 de la plantilla; z7 omite la fila adicional.

Siguiente gate: registrar z6 como histórico NO-GO, repinear el manifiesto/cuerpo tras la corrección de fila y construir z7 desde baseline/alcance exactos; completar los gates afectados en Docker y obtener revisión independiente del código exacto. Pre-ACK JIT 7,5 s y R3 App/Worker + R3-DO aprobados/no consumidos; full-queue R2 sigue pendiente/no aprobado. No registrar App, introducir secretos, desplegar ni publicar. No hubo operación remota; PR 501 conserva a73, fallo PWI histórico y aprobación antigua. Sin commit/push/update PR/merge ni aceptación Development. `main`, `certificacion` y Production fuera; Development NO-GO.

**Corte anterior PWI R3 — 2026-10-19 21:46 UTC:** candidato `/tmp/studiamatch-pwi-r3-20261019` (`codex/pwi-r3-successor`, padre local `a73af141d8419889ae6922f21e416b207a297391`); snapshot autónomo w `/tmp/h3req1-pwi-r3-validation-20261019w/repo`, commit `5e162083f58d61718e05d9dd9fc9363c17e4758c`, tree `8b80fa2d50581b7fb9ed1d8a1e6334a70c2d0a53`, digest `c8399b9d95fa653dbeaffb5123c2e5dd6b35fff4342d9f3cb397ab5f823fa4fc`; 1.190 rutas, 39 artefactos, unión 1.196/diff 1.195, 13 catálogos/1.173 referencias. En Docker/red deshabilitada: full credential scan PASS (exit 0, cero findings), Documentation Integrity/self-test PASS (732 fuentes, 113 activas, 433 históricas), scope guard/negativos PASS (1.196 rutas; ordinary=3, newline=1, controls=1, malformed=3, unmanifested H3=2), estado 8/8, plantilla 10/10 títulos, 10 links, 16 filas, 0 placeholders y `git diff --check a73af141..w` PASS. Otros contratos, Worker syntax/29 unit tests/3 runtime/actionlint/ShellCheck se reutilizan por hashes idénticos. Diff 4eb..w no comprobable por 95 blobs históricos ausentes; no hubo red/fallback. Review independiente aún pendiente; pre-ACK JIT aprobado/no consumido y full-queue JIT pendiente/no aprobado. Sin App/Worker, secretos, commit, push, update PR, review GitHub, merge ni aceptación remota. Fallo PWI de a73 preservado; Development NO-GO.

**Continuación PWI R3 — 2026-10-19 21:23 UTC:** la revisión independiente del snapshot anterior `f6154eabba2c0638a186ba157cc1255ce4c9df1e` encontró HIGH en overflow y orden de supersession. La corrección local valida base/SHA actual, invalida ese check y sustituye como máximo la fila pendiente más antigua de otro SHA para conservar durable el evento vigente; mantiene 8 pendientes/100 terminales. Snapshot autónomo `p`, reconstruido del baseline `4eb4d877a50b012bb630a129bd0c74482c33be9c` sin fallback a Syncthing: commit sintético `ad894278ebfb5f78e9882d1f72817d9a1e6a25c7`, scope digest `231019c75783b0043d1ec4f1564103aa2f0ddbe8e9935970bcfa33f8c6195e93`, 1.190 entradas, 39 artefactos, unión exacta 1.196/diff 1.195. En Docker: escaneo completo sin findings; Documentation Integrity/self-test PASS (732 fuentes, 113 documentos activos, 433 históricos); guard/negativos PASS (13 catálogos, 1.173 referencias); plantilla PASS (10/10 headings, 10 enlaces, 16 filas de tabla incluyendo cabecera, cero placeholders); contratos Python 33/33; `git diff --check` PASS; Worker syntax y 29/29 unitarias/3/3 runtime PASS. Actionlint/ShellCheck se reutilizan por SHA-256 de entradas idéntico. El manifest registra estos resultados y reconstruye un snapshot final autónomo antes de revisión independiente; la revisión exacta del candidato corregido sigue pendiente. El JIT de invalidación pre-ACK está aprobado y sin consumir; el delta distinto para resolver la cabeza actual y reemplazar fila en overflow sigue pendiente de aprobación. No hubo operaciones remotas, App/Worker, secretos, despliegue, commit, push, update PR, nueva aprobación, merge ni aceptación Development. Se preserva el fallo histórico PWI de `a73af141…`; Development sigue NO-GO.

**Ejecución local R3 — 2026-10-19 20:21 UTC:** snapshot autónomo exacto `1ebec3431f0e5f64aad4d9e742a75f61f623a62d`, baseline `4eb4d877a50b012bb630a129bd0c74482c33be9c`, scope digest `10da6476b820d601317ae5725d0597760bfb1b0de70789cd5083a583d27149bc`. En Docker con red deshabilitada y snapshot de solo lectura: full credential scan PASS (0 findings); documentation checker/self-test PASS (732/732 fuentes, 113/113 documentos activos, 433/433 históricos); protected-path guard y negativos PASS (1.196 paths, 13 catálogos, 1.173 targets); contratos de estado/fuente cliente 18/18; cuerpo PR PASS (10/10 títulos, 15/15 filas, 12 enlaces, 0 instrucciones sin completar); `git diff --check a73af141..snapshot` PASS; ShellCheck 0.11.0 PASS. `actionlint` se reutiliza con hash idéntico `d71aae18…`; Worker syntax, unitarias 25/25, runtime 3/3 y 86 paquetes/0 vulnerabilidades conservan sus resultados sobre bytes de código idénticos. Una llamada de documentación sin el manifiesto candidato detectó omisiones WIP esperadas; el gate exacto con manifiesto pasó. La invocación directa del test de guard recibió Permission denied por modo no ejecutable; `bash tests/test_protected_path_scope_guard.sh` pasó. Estos errores de invocación quedan registrados, no son hallazgos del candidato. Revisión independiente del código exacto aún pendiente. No hay App/Worker desplegados, SHA remoto nuevo, checks remotos, aprobación del nuevo SHA, merge ni aceptación Development. NO-GO.

**Ejecución local R3 — 2026-10-19 20:16 UTC:** snapshot autónomo `54b0646ab8bd96e14c328b0f17e260be7c0df74f`, scope digest `9576be4500f6134b116932cc5a36f95b23619135061362ab6b6f972e0be1b3c0`. En Docker, `bash scripts/security/scan_credentials.sh --tree` pasó sobre el árbol completo sin findings; `tests/test_obsidian_context_state.py` y `tests/test_requirement_client_source_validation.py` pasaron 18/18 con `/opt/venv/bin/python`. Checker/self-test documental y scope guard/negativos ya pasaron sobre este mismo digest. El primer intento de pytest usó el Python global de la imagen, que no instala pytest; se conserva como fallo de invocación y no como bloqueo. El delta sucesor `a73af141..snapshot` está limpio; los chequeos de actionlint/ShellCheck se reutilizan porque sus inputs hashados no cambiaron. La revisión independiente del snapshot final sigue pendiente. App/Worker no están desplegados; PR, SHA remoto, checks y aprobación nuevos aún no existen. Sin merge ni aceptación Development. Mantener NO-GO.

**Continuación R3 PWI — 2026-10-19 20:08 UTC:** la revisión independiente del snapshot `46bd77bad486153cd13e896d96ce80a840031b2a` detectó que un check PASS anterior permanecía completado durante las lecturas del PR y podía sobrevivir cuando ya había un evento sucesor en cola. Ambas carreras se reprodujeron en Docker contra ese snapshot anterior. El Worker ahora reabre checks existentes a `in_progress` antes de leer PR/files/reviews y los deja pendientes si el evento ya fue sustituido. En el candidato local: regresiones focalizadas 4/4 y suite Worker 25/25 PASS; `npm run check` PASS; runtime Workers 3/3 PASS tras instalar en copia desechable 86 paquetes (0 vulnerabilidades). Todavía faltan manifiesto/pins finales, reconstrucción autónoma, escaneo/gates completos y revisión independiente del snapshot final. App/Worker remotos no están desplegados; no hay publicación, SHA sucesor en GitHub, merge ni aceptación Development. Mantener NO-GO.

**Continuación R3 PWI — 2026-10-19 19:55 UTC:** PR 501 permanece abierto en `a73af141d8419889ae6922f21e416b207a297391`; su fallo PWI histórico se conserva. El primer revisor halló HIGH en la carrera de revocación durante publicación; el Worker se corrigió y ambas regresiones que fallaban antes pasan ahora. Docker Node 22: 23/23 unitarias, `npm run check` PASS, runtime 3/3; 86 paquetes instalados, 0 vulnerabilidades. En el snapshot autónomo `5f0bf68dc601402a5d947b35ab373c723874487e` con digest de scope `67bff205…`: escaneo completo de credenciales PASS; gate y self-test documental PASS (732/732 fuentes, 13 catálogos); guard/negativos PASS (1196 rutas, 1173 referencias); contratos de estado/fuente cliente 18/18; actionlint 1.7.12 y ShellCheck 0.11.0 PASS en Docker. Diff del sucesor limpio; diff de baseline conserva solo 125 advertencias históricas (107 espacios finales, 18 EOF). La actualización de este checkpoint y su pin requiere una reconstrucción, escaneo y revisión final del árbol exacto. App/Worker no registrados/desplegados; permisos R3/R3-DO aprobados sin consumir. Aprobación humana del PR actual no cubre el SHA sucesor. Sin publicación, merge ni aceptación Development; D01–D14 0/14 y regresión 0/11.

**Ejecución local — 2026-10-19 11:15 UTC:** Docker volvió a validar el snapshot autónomo tras el checkpoint operativo: 1.179 rutas de alcance, unión exacta de 1.185 rutas, 13 catálogos/1.173 referencias y 37 artefactos de contenido más el manifiesto autoexcluido. Checker/self-test documental: 723 fuentes, 113 documentos activos y 433 históricos; scope guard/negativos (3/1/1/3/2), contrato del estado (8 pruebas), árbol del escáner y `git diff --check HEAD`: PASS. El flujo Python amplio (250 + 10 subtests y segunda invocación 41) y actionlint/ShellCheck focal se reutilizan por inputs de código/workflow intactos. La revisión independiente del manifiesto anterior (digest `4416417a…`) fue PASS sin hallazgos; esa revisión es histórica y el manifiesto identifica por separado el estado de revisión del digest vigente. El cotejo baseline conserva 125 avisos de formato históricos (107 espacios finales, 18 líneas vacías finales), sin reformatos. Ningún resultado local equivale a GitHub o aceptación Development.

**El candidato no se publicó:** `/tmp/h3req1_r19_publication_prep_20261018`, rama `feat/h3req1-sync-20261018-r19`, HEAD `074583d9f6ea1b5686dc58c9669111f589cb8e7a`; las correcciones locales siguen sin commit. El snapshot se identifica por el manifiesto vigente: 1.179 entradas más seis artefactos de paquete. R18 (`0d7c89dccffd1146b6cc669d4994787e9b78b533`), el checkout Syncthing (`a57bc415257ab8154d40d7c71d34c69d0bdaeb0d`), respaldos y evidencias previas permanecen sin cambios. `braces@3.0.4-h3.1` se conserva; no se reabrió la reorganización Obsidian.

**Docker:** el contenedor habitual `studiamatch-dev` continúa `running/healthy`, 0 reinicios, imagen `sha256:bb30d6237846f120d39b7c9794f8eb0c938c69e8cc15e0e93d2ca03641a7ade1`, con el checkout de origen montado. Las validaciones del delta se ejecutaron en la imagen aislada R19 con el candidato en solo lectura; no se reconstruyó el contenedor habitual ni se alteraron lockfiles, secretos o recursos ajenos.

**GitHub — solo SHA remoto anterior `074583d9f6ea1b5686dc58c9669111f589cb8e7a`:** lectura de PR, jobs y reviews a las 11:11 UTC confirma que PR 501 sigue abierto en ese SHA; el cuerpo remoto todavía describe el snapshot anterior y se actualizaría solo al publicar el paquete revisado. El run `39228507399` sigue `in_progress` en actionlint y ShellCheck continúa pendiente; Python Compile And Tests, Static Build y PostgreSQL DB Change Gate están `failure` en ese checkout. Documentation Source Registry, TypeScript, Credential Scan, Protected Path Integrity y ESLint están `success`; H2 Main Production Expand Gate está `skipped` fuera del alcance. PWI separado `39228629396` terminó `failure` porque el trusted base carece del helper. No existe SHA/runs del sucesor; la revisión humana anterior permanece `DISMISSED` y debe renovarse sobre el SHA final por alguien distinto de autora y publicadora. Los PASS locales Docker no sustituyen resultados de GitHub.

**Bloqueo PWI:** el workflow `pull_request_target` toma su definición de `main`; agregar el helper solo a `desarrollo` no habilita una fuente confiable. Main/Production permanecen fuera del alcance. Está preparado, pero no aprobado ni ejecutado, el paquete JIT `/tmp/h3req1_pwi_external_check_app_jit_package_20261019.md` para una GitHub App verificadora limitada al repositorio y al check requerido de `desarrollo`. Sin un proveedor PWI confiable, no se puede cerrar el control ni integrar.

A está consumido; B/C/D conservan sus aprobaciones exactas. La excepción temporal Worker v2 vence el 2026-10-25 23:59 UTC; no autoriza otro deploy ni rollback. Gmail sigue intacta. D01/D02, C, invitación nueva, D01–D14 y regresión remota adicional permanecen pendientes: 0/14 y 0/11. Development sigue NO-GO; no hay un deployment R19 para aceptación.

El [reporte remoto R19](evidencia/h3req1_g10_remote_preparation_2026-10-18_r19.md), [paquete Development R19](evidencia/h3req1_development_integration_package_2026-10-18_r19.md), [cuerpo PR R19 basado en plantilla](evidencia/h3req1_pr_body_draft_local_review_2026-10-18_r19.md), [checks R19](evidencia/h3req1_remote_preparation_checks_2026-10-18_r19.txt), [revisión independiente R19](evidencia/h3req1_remote_preparation_independent_review_2026-10-18_r19.txt), [manifiesto R19](evidencia/h3req1_pr_scope_manifest_2026-10-18_r19_reconciled.json) y [tratamiento visual seguro R19](evidencia/h3req1_visual_evidence_redaction_2026-10-18_r19.md) registran el corte vigente y su historia. R18 permanece como evidencia histórica inalterada.

Histórico de gates H3: `H3_READY_FOR_PROMPT_CONTINUA` se conserva en las evidencias del hito; no equivale al estado vigente, que permanece NO-GO Development.

## Pilares Transversales Obligatorios

Todo desarrollo futuro del producto debe preservar continuamente funcionalidad,
escalabilidad, seguridad, mantenimiento, calidad y rendimiento. Ningun hito, task o
requerimiento puede cerrarse sin validar estas premisas frente al alcance
ejecutado.

Para cualquier nuevo desarrollo con requerimiento cliente, antes de iniciar y al cerrar un hito o task vinculado a un requerimiento se debe validar criterios de aceptacion contra el documento privado del cliente mediante atestacion sanitizada versionada.
El documento privado no se versiona y no se expone en PRs;
la evidencia versionada solo registra el identificador de fuente, resultado y
trazabilidad.
Si este gate documental falla, no se puede ejecutar codigo, DB, UI, pipeline ni
PR del hito siguiente hasta corregir la atestacion sanitizada.

Todo cambio funcional, DB, UI, pipeline o despliegue debe incluir una transicion
transparente obligatoria: `expand -> compatibilidad -> deploy -> contract`.
Durante construccion y promocion se debe preservar el comportamiento legacy
necesario para que la aplicacion siga funcionando; luego de estabilizar en
produccion se debe retirar la funcionalidad legacy y dejar activo el nuevo
contrato solicitado. Ningun hito, task o PR puede cerrarse ni promoverse sin
documentar compatibilidad, contraccion, rollback y evidencia de no degradacion
funcional.

Todo prompt futuro de desarrollo queda bajo `PROMPT_RETROALIMENTADO_REQUIRED`
segun [Estandar De Prompts Retroalimentados](operaciones/estandar_prompts_retroalimentados.md).
Un prompt retroalimentado mantiene un ciclo de analizar, implementar, validar,
revisar, convertir cada fallo, hallazgo, drift o gate incompleto en tareas,
corregir y revalidar hasta cumplir sus criterios de GO. No se declara GO por
intencion, implementacion parcial o pruebas locales cuando el alcance exige
evidencia remota. Si se requiere JIT, push, PR, merge, deploy,
workflow_dispatch, Supabase writes, ramas protegidas o acciones destructivas,
la ejecucion se detiene y se pide aprobacion humana separada con opciones
concretas, recomendacion y consecuencias. Cada aprobacion recibida obliga a
reevaluar estado, actualizar el plan y continuar desde el gate detenido. El
cierre exige evidencia canonica, criterios cliente, pruebas completas,
revisiones especializadas y ausencia de hallazgos HIGH/CRITICAL. No se pueden
ocultar fallos como historicos o fuera de alcance sin demostrar baseline; cada
waiver requiere causa, evidencia reproducible, owner, riesgo, vencimiento y
aprobacion humana.

Todo PR debe usar la plantilla versionada `.github/pull_request_template.md`.
Antes de abrir o actualizar un PR se deben ejecutar las validaciones necesarias
para completar sus secciones con resultados reales. La plantilla no se llena con
intenciones, placeholders ni omisiones silenciosas; toda validacion no aplicable
o pendiente debe indicar causa, riesgo residual y owner.

- Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama `feat/h3req1-sync-20261002`, baseline `4eb4d877a50b012bb630a129bd0c74482c33be9c`; el commit `ac4a6c9b233ed450202ae9e6b09a84281fd3d8c5` contiene el candidato funcional inicial. El árbol agregado añade el checkpoint documental R17 y está delimitado por los pins y digests del manifest; la auditoría precommit histórica no sustituye esa reconciliación agregada.
- Checkout original: `/home/romel/src/studiamatch`, rama `feat/h3req1-development-remote-tests`, HEAD `7650093b05a820e8e6faf9ec711e12fab8b50398`; se conserva en solo lectura.
- Se preservan cambios ajenos, historia Git local, evidencia sellada, secretos y recursos Docker. Las lecturas autorizadas R16/R17 fueron read-only y se describen abajo; no se cambió configuración remota.
- El resultado funcional R178 está en [cierre local G01–G09](evidencia/h3req1_g09_local_close_r178_2026-10-11.md). La revisión/correcciones R181/R182 y sus límites están en [revisión del delta R8](evidencia/h3req1_g10_r8_review_corrections_r181_2026-10-12.md), [scope scanner R181](evidencia/h3req1_g10_scope_scan_r181_2026-10-12.txt) y [scope scanner R182](evidencia/h3req1_g10_scope_scan_r182_2026-10-12.txt).
- R8 permanece antecedente inalterado: [manifiesto R8](evidencia/h3req1_pr_scope_manifest_2026-10-12_r8.json) y [cuerpo propuesto R8](evidencia/h3req1_pr_body_draft_local_review_2026-10-12_r8.md).

## Fotografía R17 previa a la actualización humana vigente — histórica

R17 preserva R14/R15/R16 y corrige scope guard, workflow y pins seleccionados. El ciclo independiente 16 corrigió tres pins baseline y un follow-up detectó estados de checks desactualizados, reconciliados en el manifiesto. El ciclo independiente 17 revisó el snapshot `4513da925f7ff667bb66e037acb2e0423133881502f947011941e333b1b63515` / diff `7de593d26a349a7e787ddd5186961cda411611c670b539fe7160b6c15ade8af8`: PASS local, 0 HIGH/CRITICAL/MEDIUM/bloqueos y un LOW editorial en seis razones de checks. Se corrigieron esas razones en el manifiesto y se reconciliaron artefactos/gates afectados; `r17-independent-review` del manifiesto mantiene el estado vigente del follow-up exacto. Cierre funcional R14 no se repite donde inputs permanecen intactos. actionlint y ShellCheck focal se reutilizan por hashes intactos; diff-check continúa WARN 125/63. El responsable confirmó que quiere repetir DELETE de Outlook; la invitación accepted actual lo impide bajo FK/CHECK/trigger. C es retención alternativa no aprobada. No hubo operación remota.

**Hechos R17:** GitHub default `main`; `desarrollo` en `4eb4d877…`; no feature remota; branch protection detallada 403; ruleset permite bypass `always` para esta conexión, que no se utiliza; PWI ausente en base. Free responde `ACTIVE_HEALTHY`, ledger 71 frente a Pro 23 y metadatos de schema/RLS/rutinas/grants divergentes. Pages despliega previews para todas las ramas; `desarrollo` sigue en baseline y Certification está en SHA `c80f6504…`, host alias `certificacion.studiamatch-aty.pages.dev`. Cloudflare documenta que Preview config/bindings aplican a todos los previews y no son branch-specific; el SHA actual de Certification no contiene `web/functions/`. Falta `ADMIN_QUOTA` y no se listan Worker/DO; `NEXT_SUPABASE_SECRET_KEY` aparece `plain_text` en Preview. La lectura actual lista `admin-invite` Free v12 (`verify_jwt=true`), `send-lead-emails` Free v21 y Pro v8. Un chequeo de `information_schema` no encontró tabla de configuración en `auth`; GET Auth settings sin API key devolvió 401 para Free/Pro, por lo que redirects, plantillas y ajustes runtime siguen sin verificación administrativa.

Paquete A propone nueve migrations no aplicadas solamente en Free, luego de validar ledger/schema por hash; dos migrations ya aplicadas se omiten y Pro permanece de solo lectura. B prepara Worker/DO, bindings/variables cifradas y Edge antes de cualquier push que genere preview; registra el alcance Preview global, mantiene fuera el alias Certification y detiene si el alias del candidato difiere del esperado. C propone desactivar la membresía por RPC, cambiar el email Auth anterior a `example.invalid`, bloquear esa identidad y retirar TOTP, preservando la fila Auth, FK/invitación accepted y auditoría. C está aprobado como JIT condicional y no consumido: requiere A migration 3, B y comprobar deshabilitados ambos avisos Auth antes de escribir. D define la ventana de aceptación con efectos y recuperación. A, B y D esperan aprobaciones JIT concretas.

La rama feature puede generar deployment preview automáticamente; por eso no se publica antes de preparar A/B. El filing requiere además resolver bootstrap PWI solo en `desarrollo` y una lectura de protecciones/checks/approvals que actualmente está bloqueada por 403. La autorización previa de push/PR/merge se mantiene bajo sus condiciones; no se usa bypass ni se autoaprueba.

R17 conserva denominadores: D01–D14 0/14; catálogo adicional 0/11. D03 requiere A migration 3, B, las condiciones de C y el paquete D aprobado. Gmail puede actuar como admin para invitar/gestionar Outlook mediante interacción directa del responsable; no se modifica la propia cuenta Gmail. D04 usa Gmail como admin para los cambios de rol de Outlook; Outlook nunca se concede privilegios. D05 requiere cobertura aislada y JIT adicional si no puede probarse preservando Gmail y sin asumir un tercer admin.

**Fotografía histórica previa a la aprobación C:** el responsable prefiere repetir el DELETE anterior para reutilizar Outlook. La invitación accepted registrada después de ese borrado ahora referencia la identidad y activa FK/CHECK/trigger que impiden repetirlo sin alterar datos históricos o el contrato. C propone una alternativa distinta: cambiar la identidad anterior a un email técnico `example.invalid`, bloquearla, desactivar membresía mediante el RPC auditado y retirar TOTP, preservando fila Auth/FK/invitación/auditoría. La respuesta posterior aprobó esta alternativa como JIT condicional no consumido; requiere A migration 3, B y verificar deshabilitadas ambas notificaciones Auth. Esto afecta el Auth compartido Free Development/Certification. C no crea invitación nueva ni autoriza el envío D03. Si no se pueden verificar los ajustes Auth, no se escribe. No se modificaron recursos remotos.

**Reconciliación de paquete posterior — R17, 2026-10-14:** R17-TRACE-06 corrigió el MEDIUM de trazabilidad del ciclo 15; los checks del snapshot ciclo 17 registran docs/self-test, scope/negativos, 45/45 contratos, plantilla, exact-stage y scanners PASS. La revisión independiente ciclo 17 encontró un LOW textual en seis razones del manifiesto; se corrigieron, conservando el resultado medido y su historial. El repin y la verificación afectada se documentan en el manifiesto; no repetir actionlint/ShellCheck con hashes intactos. `git diff --cached --check` WARN cuantificado 125/63 (107 trailing whitespace, 18 blank EOF). Bootstrap protegido y JIT A/B/D siguen pendientes; C fue aprobado después como retentivo, condicional y no consumido. NO-GO Development, D01–D14 0/14, regresión adicional 0/11; no hubo cambios remotos.

## Reconciliación local del candidato R14

R14 combina el alcance funcional R8 con el cierre documental vigente R13 y preserva los manifiestos, cuerpos y evidencias R8/R9/R12/R13. R12 queda contenido por la versión más reciente R13; del delta R9 solo se conservan sus artefactos de evidencia y los archivos que el paquete actual requiere. No se reactivan los ocho mapas R9-only retirados que no tienen referencias en los catálogos. Se conserva la superposición R8/R13 usando los bytes actuales R13 para las rutas compartidas y la atestación cliente sanitizada; no se inspeccionó el documento privado. La corrección documental R14 retira del registro canónico tres enlaces a salidas/cache generadas excluidas del paquete; los artefactos históricos R13 permanecen intactos y el catálogo se regenera desde el JSON canónico.

Los 13 catálogos vigentes contienen 1,173 destinos directos únicos después de corregir tres relaciones a salidas/cache generadas no versionables. El paquete selecciona 166 destinos directamente y el HEAD de base aporta 324 destinos versionados, con 54 rutas compartidas entre esos dos conjuntos; los 737 destinos restantes se incorporan como cierre exacto de referencias, sin seleccionar los demás archivos WIP. R14 fija 1,117 rutas propuestas: 1,082 paths con estado Git propuestos, 35 paths ignorados expresamente y el manifiesto incluido; estos totales se detallan por path en el manifiesto. De los 20,566 paths de `git status`, 19,484 quedan fuera. Los 13 logs ignorados de evidencia R8 y 22 logs de catálogo son destinos directos requeridos. El manifiesto registra los conteos, hashes, estado y origen de cada ruta. La reconciliación ejecutó 78/78 pruebas focales de contratos/workflows; alineó `security_flow` al estado R13 y quitó la rama imposible `pull_request_review` del gate H2 Stage 1, sin activar PWI Stage 2. La revisión independiente local dio PASS, 0 HIGH/CRITICAL y ningún finding de código pendiente. Las siete eliminaciones documentales R13 se mantienen como eliminaciones. No se reabre la reorganización documental.

La dependencia `braces@3.0.4-h3.1` y su tarball local se mantienen sin cambios. Para G10 quedan tres opciones documentadas: conservar el snapshot y verificar procedencia/upstream antes de promoción; reemplazarlo por una versión oficial solo tras comprobar disponibilidad y equivalencia y regenerar/validar el lock; o separar el paquete hasta resolver la procedencia. R14 elige conservarlo localmente sin presentarlo como verificado upstream; responsable Romel, revisión prevista 2026-11-03.

El [reporte R14](evidencia/h3req1_reconciliacion_local_2026-10-13_r14.md), [checks](evidencia/h3req1_reconciliation_checks_2026-10-13_r14.txt), [revisión independiente](evidencia/h3req1_reconciliation_independent_review_2026-10-13_r14.txt), [manifiesto del paquete](evidencia/h3req1_pr_scope_manifest_2026-10-13_r14_reconciled.json) y [cuerpo propuesto con la plantilla versionada](evidencia/h3req1_pr_body_draft_local_review_2026-10-13_r14_reconciled.md) fijan el alcance y sus límites. El inventario observado supera veinte mil rutas WIP; solo se propone el conjunto fijado en R14. Al corte R14 no hubo commit, push, PR, lecturas/configuración remota, despliegue ni escrituras Supabase.

## Corte histórico: preparación remota G10/R16

Las lecturas autorizadas de preparación se refrescaron el 2026-10-14. El [reporte R16](evidencia/h3req1_g10_remote_preparation_2026-10-14_r16.md) separa hechos, discrepancias y superficies que no se pudieron consultar sin arriesgar exposición de valores. El [paquete de integración, transición y rollback](evidencia/h3req1_development_integration_package_2026-10-14_r16.md) prepara gates E0–E5 y fases `expand -> compatibilidad -> deploy -> contract`; no ejecuta ninguna. El [cuerpo local basado en la plantilla versionada](evidencia/h3req1_pr_body_draft_local_review_2026-10-14_r16.md), [checks](evidencia/h3req1_remote_preparation_checks_2026-10-14_r16.txt), [revisión independiente](evidencia/h3req1_remote_preparation_independent_review_2026-10-14_r16.txt) y [overlay manifest](evidencia/h3req1_remote_preparation_manifest_2026-10-14_r16.json) componen el paquete revisable. La revisión independiente dio GO documental local acotado, sin hallazgos HIGH/CRITICAL adicionales; confirmó la cardinalidad del scanner (9 entries de scope más manifest). El scanner final pasó y los diez pins se repinaron tras incluir este dictamen. El scope guard sigue bloqueando el filing y el resultado remoto permanece NO-GO Development.

| Plataforma | Hechos verificados R16 | Discrepancia o pendiente |
|---|---|---|
| GitHub | Default `main`; `desarrollo` sigue en baseline `4eb4…`; las tres ramas objetivo aparecen protegidas; 14/15 checks del SHA base success y uno skipped; siete workflows listados. | WIP no publicado; branch-protection detail 403; approvals/required checks desconocidos; PWI local no listado. |
| Supabase | Pro `ACTIVE_HEALTHY`, 23 migrations hasta `20260607221002`, 18 relaciones en listado de tablas; Edge Pro `send-lead-emails` v8. Free `INACTIVE`; Edge inventory enumera invite v12 y leads v21. | Ledger/objetos Pro discrepan del candidato; Free metadata devuelve `INVALID_ARGUMENT`; Auth Pro 401 y Free DNS error. |
| Cloudflare | Dominios `admin.studiamatch.com` y `www.studiamatch.com` activos en Pages; listados Worker y DO vacíos. | No se consultaron deployments/settings/bindings porque sus respuestas pueden incluir valores. Observaciones de deployments/`plain_text` R15 son históricas, no actuales. |
| `braces` | PR upstream #72 cerrado/no merged; npm oficial indica 3.0.3; snapshot conserva SHA registrado y 9/10 blobs del commit público. | Snapshot local no es release oficial; bytes y pin permanecen sin cambio. |

No se leyeron filas operativas, usuarios, buzones, tokens ni valores secretos. No hubo RPC mutadora, DDL/DML, workflow, PR, push, merge, deploy, purga ni cambio remoto. D01–D14 siguen 0/14. **NO-GO Development.**

Validación local de scope: `tests/test_protected_path_scope_guard.sh` abortó por `referenced target hash differs: .context/componentes/admin_runtime.md`, porque consume el pin inmutable R14 y el overlay R15 actualiza esa ruta. La comparación separada extrae los tres matchers de `.github/workflows/security-audit.yml` y acepta 7/11 rutas R16: no se aceptan el log R181 citado por el estado, checks, revisión ni manifest. La comprobación de referencias añadió solo ese log R181 al overlay para que la evidencia citada esté disponible; no se editó el guard/workflow ni se incluyó el resto del WIP. Ver la [señal local R16](evidencia/h3req1_g10_remote_preparation_2026-10-14_r16.md#señal-local-de-reconciliación-del-scope-guard).

## Corte histórico: preparación remota G10/R15

Las lecturas iniciales se realizaron el 2026-10-13 18:30:52 UTC. El [reporte R15](evidencia/h3req1_g10_remote_preparation_2026-10-13_r15.md), [paquete](evidencia/h3req1_development_integration_package_2026-10-13_r15.md), [checks](evidencia/h3req1_remote_preparation_checks_2026-10-13_r15.txt), [revisión independiente](evidencia/h3req1_remote_preparation_independent_review_2026-10-13_r15.txt), [body](evidencia/h3req1_pr_body_draft_local_review_2026-10-13_r15_remote_prep.md) y [manifest overlay](evidencia/h3req1_remote_preparation_manifest_2026-10-13_r15.json) se conservan como corte histórico. R16 sustituye la actualidad de las observaciones de GitHub/Supabase que volvió a consultar y no puede revalidar deployments/bindings Cloudflare sin arriesgar que se devuelvan valores. La revisión local GO R15 sigue limitada a su snapshot y no acredita estado remoto ni readiness actual. El path guard aceptó 17/20 rutas R15; el bloqueo permanece.

| Plataforma | Hechos verificados | Discrepancia o pendiente que bloquea adopción |
|---|---|---|
| GitHub | Default `main`; `desarrollo` HEAD coincide con baseline `4eb4…`; 14/15 check-runs success (uno skipped); ruleset `update` activo para refs protegidos. | WIP R14 no está en ese SHA; endpoint branch protection 403; approvals/required checks desconocidos; PWI local no aparece en workflows remotos. |
| Supabase | Pro `ACTIVE_HEALTHY`, ledger de 23 migrations hasta junio; Edge Pro `send-lead-emails` v8. Free `INACTIVE`; lista Edge `admin-invite` v12 y `send-lead-emails` v21. | Ninguna de las 28 migrations H3 locales figura en ledger Pro; no se enumeran tablas/RPC Admin esperadas. Free metadata timeout; Auth no secreta no accesible; Edge inventory no acredita funcionamiento. |
| Cloudflare | Pages producción `main`/SHA `70d0f4fe…`; preview `desarrollo`/SHA `4eb4…`; hosts/binding names enumerados en R15. | No es el WIP R14; faltan bindings BFF/Worker/DO esperados y `NEXT_SUPABASE_SECRET_KEY` aparece `plain_text`. DNS fuera del proyecto no verificado. |
| `braces` | PR upstream #72 cerrado/no merged; 9/10 archivos del snapshot coinciden con commit público y npm official declara 3.0.3. | Snapshot local no es un release oficial; se mantiene intacto. |

No se leyeron valores de secretos, usuarios, invitaciones, correos ni filas operativas. No hubo consultas remotas con escritores, SQL mutador, RPC de negocio, workflows, PR, deploy o modificación de configuración. El backup previo a lecturas R15 `/home/romel/backups/studiamatch-docs-2026-10-13/supplemental_before_r15_remote-preparation_2026-10-13` conserva 19/19 archivos; el backup de notas de módulos conserva 2/2. El estado documental R15 antes de correcciones finales está preservado aparte en `/home/romel/backups/studiamatch-docs-2026-10-13/supplemental_before_r15_final_reconcile_2026-10-13`, con 19/19 hashes verificados. Todos están fuera de ambos checkouts y excluidos del paquete.

## Transferencia documental local

**Corte R13: navegación histórica y nomenclatura cerradas localmente con revisión independiente GO.** R12 se conserva como antecedente de transferencia local. La entrada Obsidian sigue siendo [.context/indice.md](indice.md), y este documento conserva la autoridad operativa. El [registro canónico](trazabilidad/registro_fuentes_componentes.md) asigna 801/801 fuentes a 14 componentes y 262 grupos; sus 4,715 relaciones locales aplicables están verificadas, 91 son N/A justificados y cinco verificaciones remotas siguen pendientes.

La extensión R13 organiza la evidencia histórica en 13 catálogos por proceso/módulo. El [reporte R13](evidencia/h3req1_documentacion_navegacion_historica_2026-10-13_r13.md), [checks](evidencia/h3req1_documentacion_checks_2026-10-13_r13.txt), [revisión independiente](evidencia/h3req1_documentacion_revision_independiente_2026-10-13_r13.txt) y [borrador del paquete](evidencia/h3req1_pr_body_draft_local_review_2026-10-13_r13_docs.md) detallan navegación, nomenclatura, validación y límites. El gate Docker reporta 95/95 documentos activos alcanzables y 433/433 documentos históricos enlazados individualmente desde su catálogo; hay cero documentos Markdown excluidos en este corte. El checker procesó 9,340 links y 4,567 anchors. Los catálogos sirven para navegar cortes históricos y no crean autoridad operativa. La preparación R37 enlaza R36 y R38; la secuencia documental continúa hasta R40. El log R37 se conserva y su preparación declara 29/29 en el contrato local, pero el manifiesto consumido por el drill no aparece en el checkout y no puede cotejarse independientemente.

**Completado en R13:** gate normal/self-test Docker, enlaces individuales de historia, scanner explícito actualizado y regresiones scanner/scope. Un snapshot previo con 9,336 links recibió GO. El corte de 9,340 links/4,567 anchors tuvo revisión GO y reconciliación PASS: 138 entradas de scope (131 presentes, 7 eliminadas), 8 pins de evidencia, 26 overlays y 4 artefactos. Una relectura posterior detectó una celda del body que seguía diciendo revisión pendiente y una frase duplicada en el siguiente paso de este estado; ambas se corrigieron. La última relectura independiente dio GO a esta versión, tras confirmar el digest/pins y las métricas actuales. La prueba del consumidor de estado registró 8/8 en una ejecución previa; no pudo repetirse porque el contenedor actual no tiene el módulo `pytest`. El scope guard cotejó 138 entradas (131 presentes, 7 eliminadas) y 125 rutas únicas con el allowlist del workflow. `actionlint` y `shellcheck` tampoco están instalados; `bash -n` pasó. No se repiten suites funcionales con inputs intactos.

La copia completa previa a este ciclo permanece fuera de ambos checkouts en `/home/romel/backups/studiamatch-docs-2026-10-13/supplemental_before_r13_historical_navigation_2026-10-13`; inventario, hashes y comparación con originales se verificaron antes de editar. La [estructura R10](evidencia/h3req1_documentacion_estructura_2026-10-13_r10.md), la [consolidación R11](evidencia/h3req1_documentacion_consolidacion_trazabilidad_2026-10-13_r11.md) y el [cierre R12](evidencia/h3req1_documentacion_cierre_local_2026-10-13_r12.md) mantienen sus cortes y evidencias previas. R8/R9, R178/R181/R182, R12 y evidencia histórica sellada no se modifican. No hubo lectura remota ni acciones protegidas.

## Pendientes operativos — fotografía histórica R13, reemplazada por el corte vigente

Esta lista era válida para R13 y se conserva como historia; sus aprobaciones y siguientes pasos fueron sustituidos por los addenda R17 al final de este estado. No debe usarse para operar.

1. La revalidación post ciclo 13 pasó y ciclo 14 encontró un LOW editorial por repetir el WARN de diff-check en body. Se quitó la repetición; el repin y gates afectados pasan; ciclo independiente 15 sigue pendiente. `git diff --cached --check` sigue WARN cuantificado (125 diagnósticos/63 paths) en documentación/evidencia/fixtures preservados; no se reescribe historia. actionlint y ShellCheck se reutilizan por hashes intactos.
2. Resolver bootstrap PWI solo en `desarrollo` y obtener protección/required checks/approvals/environments/actor de merge. La lectura branch protection devolvió 403; no usar bypass.
3. Aprobar/consumir A y B antes de push/PR que genere un preview; cubrir expand DB, Worker/DO, Pages config y Edge compatible. La autorización humana de push/PR/merge no sustituye estos JIT ni la condición de review/checks.
4. D03: el responsable reitera su preferencia por DELETE Auth, que está bloqueado por FK/CHECK/trigger debido a la invitación accepted actual. La alternativa C de retención conserva el historial y aún requiere decisión/aprobación JIT explícita; no se asume aceptada. Si C no se aprueba, D03 queda pendiente o deberá cubrirse con otra identidad, cuya creación requiere consulta y aprobación adicional. Gmail y los demás admins permanecen intactos.
5. Aprobar D y ejecutar interacciones guiadas y recuperación con el responsable. D01–D14 remotos siguen 0/14; regresión adicional 0/11.
6. Mantener `braces@3.0.4-h3.1`; el snapshot local no es release oficial y no tiene waiver. No sustituirlo en este ciclo.

## Verificaciones remotas pendientes

R17 verificó GitHub refs/workflows/checks/runs/ruleset, metadata schema/ledger Pro y Free, estado Auth agregado del target, Edge, deployment/config Pages por campos sanitizados, bindings Worker/DO por nombre/tipo y procedencia pública de `braces`. Antes de A/B se refrescarán Free activo/schema/ledger, deployments/bindings Cloudflare y controles/refs/checks GitHub. Auth redirects/templates y avisos no se consideran verificados por R17; antes de C se comprobarán solo los dos estados no secretos exigidos. PWI/protecciones aún requieren una ruta protegida válida hacia `desarrollo`; no se consultará ni cambiará `main`. El registro canónico actualizado está en [trazabilidad](trazabilidad/registro_fuentes_componentes.md); ningún resultado de lectura acredita adopción.

## Siguiente paso

cerrar el snapshot R17 con gates afectados y revisión independiente; refrescar los metadatos autorizados. A/B/C/D están aprobados en sus paquetes exactos y no consumidos. Ejecutar A y B solo tras confirmar Free, ledger/schema, coexistencia Certification y configuración actual; no push antes de ello. Resolver una ruta protegida válida de `desarrollo` sin cambiar default branch ni usar bypass. Después integrar/desplegar, completar D01/D02 con la identidad Outlook existente, y solo entonces C si migration 3, B y ambos avisos Auth deshabilitados están confirmados. D03 usa Gmail como actor únicamente con intervención explícita y preservando íntegra su cuenta; D05 requiere escenario remoto aislado adicional si no hay cobertura segura. Al corte de esta actualización no se consumieron permisos ni se ejecutó efecto remoto. R14/R15/R16 quedan preservados y la reorganización Obsidian no se reabre.


## Seguimiento del cuerpo PR — R17-TRACE-02, 2026-10-14

La revisión independiente ciclo 11 confirmó el arreglo R17-DOC-02 y PASS 45/45; verificó pins/manifiesto, 1.137 rutas, 23 pins de artefactos no-manifest y 13 catálogos/1.173 destinos. Encontró una discrepancia MEDIUM en el cuerpo PR: el test DOC-02 figuraba pendiente, el conteo decía 9.528 en vez de 9.529 y el estado de scanner/repin no distinguía la fotografía revisada de las validaciones posteriores. El cuerpo se corrigió. Las validaciones afectadas y el repin del cuerpo corregido pasaron: documentación 9.529 enlaces, scope/negativos, plantilla, 45/45 tests, exact-stage y scanner; se mantienen 0 HIGH/CRITICAL del ciclo 11 sin extrapolarlos al ciclo 12. R17 permanece NO-GO Development; D01–D14 0/14, catálogo adicional 0/11. No hubo operación remota o de cuenta, commit, push, PR, merge, deploy o prueba con efectos.


## Revalidación post-corrección del body — R17-TRACE-02

Tras corregir las inconsistencias del cuerpo PR, las suites focales Docker pasaron 45/45; documentación normal/self-test pasó con 801 fuentes, 9.529 enlaces, 4.584 anchors, 106 documentos activos/433 históricos en 13 catálogos; scope guard/negativos pasó con 1.137 rutas, 1.173 destinos y casos 3/1/1/3/2; la plantilla pasó 10 headings, 15 filas, 18 enlaces/10 destinos y 0 placeholders; exact-stage confirmó 1.130 blobs, 7 eliminaciones y pins/bytes/modos exactos; scanner aislado sin red encontró 0 en 1.130 blobs. `git diff --cached --check` mantiene WARN cuantificado 125/63 (107 espacios finales, 18 EOF) en documentación/evidencia/fixtures preservados. actionlint/ShellCheck se reutilizaron por hashes sin cambio. Esta revalidación aplica al snapshot `e4be87ca…`; el ciclo independiente 12 posterior encontró una discrepancia MEDIUM en el reporte y se corrigió en el registro siguiente. No GO Development; D01–D14 0/14 y regresión adicional 0/11.


## Hallazgo y corrección ciclo independiente 12 — R17-TRACE-03, 2026-10-14

La revisión ciclo 12 confirmó que los gates 45/45, documentación, scope, plantilla, stage y scanner del snapshot `e4be87ca…` estaban incorporados y aprobados. Encontró un MEDIUM en el reporte: una frase decía que el log y estado todavía requerían repin y revalidación. La frase se corrigió para dejar claro que el siguiente repin/retest es por el dictamen ciclo 12. El estado, cuerpo PR, log de checks, reporte y registro de revisión se repinaron; las validaciones afectadas pasan con 45/45, 9.529 enlaces, scope 1.137/1.173, plantilla 10/15/18, stage 1.130 blobs/7 deletes, scanner 0 y diff hygiene WARN 125/63. El manifiesto fija la fotografía; la revisión independiente ciclo 13 queda pendiente. No HIGH/CRITICAL ni bloqueos en el snapshot ciclo 12. Development NO-GO; D01–D14 0/14, regresión adicional 0/11. No hubo lecturas remotas ni operaciones con efectos.


## Seguimiento de revisión independiente ciclo 14 — R17-TRACE-05

La lectura read-only del ciclo 14 revisó scope `ccdf9cf9e0a5c95bd71646f4be318ef6c9f5380b02c249ea8cfbb8c33788faf1` y staged diff reportado `36f5f17ff567148906318966e7e13f882a6f3a355c0ad881b9f61d3050975508`. Confirmó la reconciliación de R14/R15/R16, preservación de R8/R9/R12/R13, 1.137 rutas, catálogos, plantilla, allowlist/negativos, braces y paquetes A–D/C-D03. No encontró defectos funcionales, HIGH, CRITICAL, MEDIUM ni bloqueos. El único hallazgo fue LOW editorial: `git diff --cached --check WARN 125/63` aparecía duplicado en la fila Calidad del body PR. La repetición fue eliminada y el resultado se registró en reporte/body/logs; el repin y gates afectados pasan según R17-TRACE-05; ciclo 15 sigue pendiente.

Checkpoint: R17-TRACE-06 corrigió el MEDIUM de ciclo 15, y el scope guard, stage audit, diff-check y scanner pasan o quedan cuantificados en el manifiesto final repinado. Siguiente gate: revisión independiente ciclo 16; después, continuar únicamente con las lecturas y aprobaciones protegidas pendientes. Development continúa NO-GO; A/B/C/D sin aprobar ni consumirse, D01–D14 0/14 y regresión adicional 0/11. No se realizó acción remota o de cuenta, ni commit/push/PR/merge/deploy. La preferencia del responsable por repetir DELETE Outlook no cambia la FK/CHECK/trigger; C es una alternativa de retención pendiente de aprobación JIT y no ejecutada. R14/R15/R16 permanecen preservados.

## H3REQ1 R17 — checkpoint tras respuesta D03 y lecturas remotas, 2026-10-14

Estado vigente: **NO-GO Development**. La protección GitHub de `desarrollo` dio 403; no se verificaron required checks/approvals efectivos. `protected-workflow-integrity.yml` usa `pull_request_target` y debe existir en la rama predeterminada `main`; el candidate/merge en `desarrollo` no lo activa. Resolverlo exige un seed protegido en `main` o una ruta equivalente fuera de este repo. `main` y esa operación quedan fuera de este ciclo: no abrir PR, no cambiar default branch ni usar bypass hasta nueva decisión/evidencia.

Cloudflare Pages mantiene `desarrollo` en el SHA baseline `4eb4d877…` y el host Development esperado. No existen aún el binding `ADMIN_QUOTA`, el Worker ni la namespace DO requeridos. La configuración Preview es global; cualquier B afecta también previews compartidos con Certification. `NEXT_SUPABASE_SECRET_KEY` figura como `plain_text` en Preview y Production: B solo contempla corregir Preview; la observación Production requiere seguimiento separado y ningún valor fue leído.

Free `aqrldlmlszjtgpqiegaa` está activo; Pro continúa autoritativo y solo lectura. No hubo SQL/RPC/write ni lectura de filas operativas. Auth/redirect settings siguen sin verificación concluyente. La invitación `accepted` actual referencia a la identidad Auth Outlook y las restricciones FK `NO ACTION`, CHECK y append-only bloquean su borrado literal. El responsable reiteró ese borrado; la opción C de retención preserva la invitación/historial, pero es distinta y requiere decisión/JIT nuevos. No resetear ni modificar Outlook hasta esa decisión. Gmail permanece intacta.

Paquetes A–D están preparados, sin aprobación o consumo JIT. Para avanzar se necesita (1) decisión sobre seed PWI fuera de `desarrollo`, (2) aprobación concreta de A/B antes de cualquier push que cree Preview, y (3) elegir C de retención, otra identidad debidamente aprobada, o dejar D03 pendiente. R17-TRACE-07A pasó documentación, scope/negativos, 45/45 contratos, template y scanner; el manifest R17 consigna la auditoría exacta de índice y el estado de revisión independiente vigente. D01–D14: 0/14; regresión adicional: 0/11. R8/R9/R12/R13 y evidencias, R14/R15/R16 se conservan; no se reinicia implementación local ni reorganización Obsidian.


## Cierre local R17 tras revisión independiente ciclo 16

La revisión confirmó 1.137 rutas staged (1.130 blobs/7 deletes), los pins R14/R15/R16, la preservación R8/R9/R12/R13, 13 catálogos con 1.173 destinos, 35 force-adds y el body con plantilla. El hallazgo MEDIUM fue que tres destinos .github/agents/*.md estaban excluidos correctamente, pero el cierre de catálogo usaba hashes del worktree como si fueran baseline limpio. Se corrigió el manifest: bytes/sha256 representan HEAD/index, y observed_workspace_bytes/observed_workspace_sha256 registran el WIP separado y excluido. La revisión confirmó que no hay callers en código, workflows ni runtime. No quedan hallazgos locales HIGH/CRITICAL/MEDIUM/bloqueantes.

Las validaciones R17-TRACE-08 cubren Docker docs normal/self-test (801 fuentes, 14 componentes, 4.715 relaciones locales, 9.529 links, 4.584 anchors, 106 activos/433 históricos, 13 catálogos), 45/45 contratos, scope guard/negativos (1.137 rutas/1.173 destinos; 3/1/1/3/2), plantilla 10/10 headings, 15/15 filas, 18/18 enlaces a 10 destinos del paquete, credential scanner staged y unión candidate-only, y auditoría exact-stage 1.137 rutas/1.130 blobs/7 deletes, modos 1.102 100644/28 100755, bytes/pins exactos y dos logs CRLF. actionlint 1.7.12 y ShellCheck focal 0.11.0 se reutilizaron por hashes intactos. Hygiene sigue WARN 125/63 sin formateo masivo.

No hay PR: el workflow PWI pull_request_target no está en main, la rama default observada, y branch-protection detail sigue 403; no se usó bypass y no se promueven main, Certification ni Production. Cloudflare Preview es global y B necesita JIT antes de push; la metadata plain_text de Production requiere seguimiento separado. Supabase Free sigue activo y Pro read-only; no hubo filas operativas, SQL/RPC, writes ni lectura de valores secretos.

A–D están preparados sin aprobar/consumir. Para D03 el responsable pidió repetir DELETE, pero la invitación accepted, FK NO ACTION, CHECK y trigger append-only lo hacen incompatible; no se eliminará ni se alterará el historial. C de retención requiere elección/JIT aparte. D01–D14 permanecen 0/14 y la regresión adicional 0/11. El próximo avance requiere resolver el bootstrap protegido PWI, aprobar A/B antes del push Preview y decidir C frente a D03 pendiente/otra identidad. La evidencia, scope y hashes exactos vigentes están en manifest/check log R17. No hubo commit, push, PR, merge, deploy, mail, reset ni operación remota con efectos.

## Reconciliación de checks del manifiesto — R17, 2026-10-14

El follow-up independiente detectó un MEDIUM de estado: varias filas `checks` conservaban `PENDING_FINAL_POST_LOG` y el digest `976620b…`, aunque R17-TRACE-08 ya registraba los gates posteriores al log en el snapshot `847c5d8…` / diff staged `af70f660…`. Los resultados ejecutados eran PASS/WARN; la discrepancia estaba en su reconciliación dentro del manifiesto, no en los resultados. Las filas, razones, pins y cierre del stage se alinean con la evidencia y se vuelven a cotejar en Docker. La decisión de la revisión final del snapshot se registra en el manifiesto R17.

El DELETE literal que el responsable pide repetir sigue bloqueado por la FK/CHECK/trigger de la invitación accepted. No se modifican Auth, invitación, constraints, auditoría, Gmail ni Certification. C continúa siendo una alternativa de retención distinta que exige aprobación JIT; si no se elige, D03 queda diferido. El estado vigente de A–D, la revisión independiente y los digests está en el manifiesto. PWI/default-main y el 403 de branch protection mantienen NO-GO; no hay push/PR/merge/deploy ni D01–D14 (0/14) o regresión adicional (0/11).


## Checkpoint R17 posterior al commit local

El candidato local se guardó en `ac4a6c9b233ed450202ae9e6b09a84281fd3d8c5`, hijo directo del baseline `4eb4d877a50b012bb630a129bd0c74482c33be9c`. El pre-commit ejecutó el escáner de credenciales y pasó. La revisión independiente ciclo 19 confirmó la reconciliación de `candidate-package-staging` con `candidate_stage_audit`: scope `100e211b9ba469d241a6863b50cdcd248a343c1d6ad72ea5cbb4b0303dd18efc`, diff sin manifest `43e010b769cf56d2b2c4e5245f9115fcb131235fdc3dfe0a2b23744e60aaa5ba`; 1.137 rutas, 1.130 blobs y 7 eliminaciones.

No se hizo push, PR, merge ni deploy. A/B permanecen preparados y sin JIT; el preview automático exige resolverlos antes de push. Filing/merge siguen NO-GO por PWI ausente de `main` y branch-protection detail 403; no se usa bypass. C de retención sigue pendiente de aprobación explícita; el DELETE literal de Outlook no se ejecutará. D01–D14 permanecen 0/14; regresión adicional 0/11. R8/R9/R12/R13 y evidencias, R14/R15/R16 permanecen preservados. Los cambios locales ajenos y el WIP no manifestado siguen excluidos.


## Revisión independiente ciclo 21 y corrección R17-TRACE-12 — 2026-10-14

El ciclo 21 revisó el snapshot agregado R17, confirmó sus digests y conteos, y no encontró HIGH, CRITICAL, MEDIUM ni bloqueos. Un LOW editorial indicó que el encabezado de este estado y el paquete llamaban “vigente” al ciclo 19 mientras el manifiesto dejaba pendiente el snapshot agregado. Se corrigieron ambas referencias; ciclo 19 queda histórico y el manifiesto R17 es fuente del estado de revisión vigente. La revalidación afectada y lectura independiente del snapshot corregido se registran en el manifiesto y check log. Development sigue NO-GO; no se hicieron cambios remotos.

## Aprobación JIT C retentivo — R17-TRACE-15 (corte anterior a permisos A/B/D)

El responsable aprobó como JIT alternativo el paquete C exacto de §5 del paquete R17: desactivar la membresía Outlook mediante RPC auditado, cambiar el email Auth anterior a un identificador técnico `example.invalid`, bloquear esa identidad y retirar su TOTP verificado, preservando la fila Auth, la invitación accepted y la auditoría. Aprobación registrada el 2026-10-14; **no consumida**. Solo puede ejecutarse después de A migration 3 y B, y si una lectura previa confirma que ambas notificaciones de seguridad Auth están deshabilitadas. Free es compartido con Certification. C no autoriza DELETE Auth, enviar invitación D03, usar otra identidad, actuar sobre Gmail, ni extender la ventana. La frase sobre JIT D pendiente corresponde a este corte anterior; R17-TRACE-20 registra la actualización posterior. No se ejecutaron cambios remotos en ese corte; Development sigue NO-GO, D01–D14 0/14 y regresión adicional 0/11.


## Continuación autorizada R17 — R17-TRACE-20, 2026-10-14

El responsable descarta DELETE físico y mantiene C retentivo aprobado. En esta misma continuación confirma que A/B/C/D están aprobados **solo en los alcances exactos** de sus paquetes R17; los cuatro permanecen `approved_unconsumed`. No volver a solicitar esos permisos ni extenderlos por similitud. A y B se ejecutan luego de refrescar metadatos y validar prerequisitos; el Preview automático no puede adelantarse a B. No se consumió permiso hasta que cada operación se complete y se registre.

D01/D02 deben ejecutarse primero con la identidad Outlook existente, ya desplegada en Development, preservando su resultado. Antes de C, hacer comparación privada de la identidad autorizada, referencias, membership, factores, sesiones, invitaciones y conteo de admins; comprobar Gmail admin activa y no asumir la existencia de un tercer admin. Si el estado no coincide con C, parar. C conserva Auth row, invitación accepted/FK, auditoría e historial, cambia el email antiguo al identificador único preparado `example.invalid`, bloquea la identidad antigua, desactiva su membership mediante RPC auditado y retira su TOTP. Después comprobar que la sesión anterior no puede usar Admin mediante una solicitud no mutadora; no asumir revocación inmediata de JWT ni ejecutar revocación fuera de C.

Con el paquete D aprobado, Gmail puede actuar como admin únicamente para invitar/gestionar Outlook durante intervención explícita del responsable. Gmail conserva identidad/email, membership admin activa, contraseña, factores, sesiones, historial y datos; no se cambian sus ajustes. Outlook completa una identidad Auth nueva; el UUID debe diferir del anterior y la comparación se conserva solo en memoria. No publicar correo, UUID, cookies, JWT ni tokens. D05 no puede desactivar Gmail ni otras identidades preservadas. Si no hay cobertura remota segura de último admin, preparar escenario aislado concreto y pedir solo el JIT incremental necesario.

`main`, default branch, Certification y Production siguen fuera de alcance. Se busca una ruta protegida válida únicamente hacia `desarrollo`: si la lectura actual demuestra que PWI no puede ejecutarse sin seed en `main` y no hay workflow/required check equivalente efectivo, detener filing y presentar la decisión de diseño concreta; no cambiar default branch, usar bypass, autoaprobar ni desactivar checks. Al corte de esta actualización, los permisos no están consumidos y Development permanece NO-GO. D01–D14 0/14 y regresión adicional 0/11 hasta obtener evidencia remota.

## Reanudación local R17 — checkpoint de ciclo 32

El ciclo 29 verificó el agregado y encontró un LOW: `r17_review_corrections.review_status` aún llamaba pendiente al ciclo 27. R17-TRACE-24 marca ese campo histórico/cerrado; el estado vigente permanece en `candidate_commit_audit.review_status` y la fila actual. El ciclo 30 dio PASS local: 0 HIGH/CRITICAL/MEDIUM/LOW/bloqueantes; confirmó pins, catálogos, plantilla y corrección ciclo 29. El ciclo 31 revisó scope `f9b833ace50f1286f9a04007f31a591d5d38b494be794478e05ccd3b07f099d9` y diff `b09b124754912a27692814c08732416efbd2c5962e2069d2043572b130504a01`, con 0 HIGH/CRITICAL/MEDIUM, 2 LOW y 0 bloqueos. Señaló que R17-TRACE-26 dejaba gates como futuros frente a PASS y que la fila `credential-scan` mezclaba 1.129/1.130 blobs y excluía incorrectamente el log. R17-TRACE-27 corrige el estado verbal y deja scan, exclusiones y conteos consistentes; la revalidación Docker afectada y follow-up independiente ciclo 32 deben cerrar antes de lecturas remotas. El revisor no ejecutó Git; el audit local verificó antes el índice/worktree/diff. El agregado mantiene 1.137 rutas (1.130 blobs, 7 eliminaciones); `git diff --cached --check` conserva WARN 125/63 (107 espacios finales, 18 EOF). actionlint 1.7.12 y ShellCheck focal 0.11.0 se reutilizan por hashes intactos.

Estado de permisos: A/B/C/D aprobados solo en sus alcances exactos y no consumidos. El ciclo 32 dio PASS sobre el snapshot prerregistro y R17-TRACE-28 incorporó ese dictamen; las validaciones locales afectadas del agregado posterior al registro están PASS según el manifiesto. Hasta este corte no hubo lecturas remotas, commit, push, PR, merge, deploy, workflow, correo, reset, DDL/DML o write. Siguiente paso: lecturas administrativas read-only autorizadas de GitHub, Free/Pro y Cloudflare y procedencia pública de braces; después, resolver ruta protegida antes de preparar/ejecutar A y B. No se hará push que active Preview antes de sus prerrequisitos. D01/D02 con Outlook actual preceden a C; Gmail permanece intacta y solo participa como admin con el responsable para el onboarding Outlook. Development sigue NO-GO, D01–D14 0/14 y catálogo adicional 0/11.
