# H3REQ1 — paquete mínimo de bootstrap CI

**Candidato:** `H3REQ1-CI-PROTECTED-WORKFLOW-INTEGRITY-BOOTSTRAP-20261009-V4`

**Base confiable:** `4eb4d877a50b012bb630a129bd0c74482c33be9c`

**Estado:** revisión 4; cierra el desfase detectado entre paquete y helper/test del candidato: cubre `.github/scripts/`, exige `user.type == "User"`, ignora cuentas no humanas y falla cerrado si falta el tipo. Reemplaza el patch V3 SHA `4f5c7a946886d1df9cb866bdc057276db9eb5aa47e997be403b092ba6f704d1b`. No publicado, instalado ni GO.

**Resultado:** el patch V4 aplica en una copia aislada de la base; quedan bloqueos de rollout y revisión independiente.

## Patch revisable

[Descargar patch mínimo](../evidencia/h3req1_ci_bootstrap_minimal.patch)

- SHA-256: `68bb4037f665c4e82c91b89faae939a20ab90cebbf85cff0b4a2f90b19682c26`
- Resultado de `git apply --check` sobre snapshot limpio de la base indicada: **PASS**.
- `git apply` en copia temporal basada en HEAD, igualdad de helper/tests con el candidato y whitespace check: **PASS**.
- Cambios en el patch: 4 rutas; 485 inserciones, 1 eliminación.
- La suite oficial pytest no pudo iniciar (`No module named pytest`). Smoke directo de cinco casos de comportamiento, compilación de dos fuentes y regresión shell de protected-path: **PASS**. No se ejecutaron actionlint, Docker ni workflows remotos.

## Rutas incluidas

| Ruta exacta | Motivo |
|---|---|
| `.github/workflows/protected-workflow-integrity.yml` | Emite un job separado en PRs a `desarrollo`, `certificacion` y `main`, y al aprobar/descartar revisiones. Incluye `edited` para reevaluar el diff cuando se cambia la base del PR. Tiene permisos de lectura y compara el SHA del head al inicio/final. `pull_request_target` obtiene la definición del workflow y el helper desde la rama default; no hace checkout ni ejecuta el head del PR. |
| `scripts/security/protected_workflow_review.py` | Clasifica rutas sensibles, incluyendo origen y destino de renames; valida respuestas paginadas y exige la última aprobación enviada por colaborador confiable, distinta del autor, asociada al head vigente y con `user.type == "User"`. Los tipos no humanos no cuentan como aprobación; falta de tipo falla cerrado. También protege `.github/scripts/`, que incluye controles de producción. |
| `tests/test_protected_workflow_review.py` | Pruebas sintéticas del helper: rutas, renames, respuestas malformadas, límite de archivos, asociación al head, autoría, asociación del revisor, rechazo de cuenta Bot, tipo ausente fail-closed y revocación/actualización de review. Incluye `.github/scripts/`. La suite pytest está preparada; no pudo ejecutarse en este entorno porque falta pytest. |
| `.github/workflows/security-audit.yml` | Dos adiciones puntuales: incorpora la suite sintética al pytest offline e incluye el nuevo workflow en actionlint. **No** cambia el agregador `security-audit`; el check nuevo se mantiene independiente para poder exigirlo por separado sin dependencia circular. |

No entran producto, DB, UI, pipelines de producto, secretos, archivos de estado, diagnósticos Docker ni el resto del WIP local. El patch se construyó copiando solo estas fuentes del WIP; las fuentes compartidas no se editaron.

El patch V4 sigue siendo un artefacto aislado; no se aplicó en bloque al checkout compartido.
El helper/test de este candidato se actualizaron en sitio para cerrar el defecto y ahora
coinciden byte por byte con esas dos secciones del patch. Los demás paths WIP no se
reemplazaron. Esto no acredita instalación remota.

El workflow WIP ya existente en el checkout no es idéntico al workflow nuevo del patch: usa
`github.event.pull_request.base.sha` para el helper, mientras el patch fija
`github.event.repository.default_branch`. Se conserva esa diferencia local sin sobrescribir
el draft; el evento `edited` se añadió al draft para reevaluar cambios explícitos de base.
El patch V4 conserva su helper de la rama default. Antes de usar el draft en otro artefacto,
revisar su origen confiable por separado. La comparación mecánica confirmó que, al normalizar
esas dos líneas (origen del helper y comentario), el resto del workflow coincide exactamente
con el workflow del patch.

## Revisión focal V4

La comparación código/paquete encontró dos diferencias demostradas: faltaba `.github/scripts/`
en el prefijo protegido y el helper no verificaba `user.type` aunque el paquete lo requería.
V4 exige el tipo exacto `User` antes de contar la revisión; un tipo no humano no satisface el
gate y un tipo vacío/ausente devuelve error cerrado. Se añadió cobertura para `.github/scripts/`,
cuenta Bot y tipo ausente. Revisión focal local: las condiciones siguen acotadas al reviewer,
la asociación, el autor y el SHA vigente; no se ejecuta código del PR.

Resultados locales: aplicación temporal del patch PASS; comparación byte a byte de helper/tests
PASS; syntax compile de dos fuentes PASS; smoke directo de cinco casos de comportamiento PASS;
regresión shell protected-path PASS.
La suite pytest oficial no corrió por dependencia ausente y no se instaló. No hubo revisión
independiente nueva del patch V4, actionlint ni workflow remoto; siguen siendo gates antes de
publicación/GO.

## Secuencia de instalación y prueba

La metadata leída por GitHub MCP confirma que la rama default es `main`. `pull_request_target`
carga la definición del workflow desde la rama default y el patch V4 checkout explícitamente
el helper de `github.event.repository.default_branch`; el evento no ejecuta la definición ni
el helper incluido solo en el head del PR. El workflow draft que ya existía en el checkout es
otro artefacto y apunta a `github.event.pull_request.base.sha`; no forma parte del patch V4 y
no se sustituyó. La revisión estática compara el patch aislado y no acredita la política/runtime
ni la protección efectiva de la rama default.

1. **Ruta concreta para evitar Production al instalar:** el usuario confirmó Production branch `main`, includes `*` y excludes vacíos. Los cuatro cambios del patch coinciden con Build watch paths; el default permite todos los archivos. La metadata read-only confirma squash merge habilitado. Ruta preparada: PR de solo controles y revisión humana independiente; el mensaje del commit bootstrap y el título del squash comienzan con `[CF-Pages-Skip]`, que Cloudflare documenta para omitir ese deployment. No se ha probado en este proyecto ni autoriza abrir PR/merge. Antes del merge, observar el PR: si aparece un Preview inesperado o el skip no se aplica, detenerse y pedir una autorización agrupada para excluir las cuatro rutas exactas de Build watch paths. No aceptar un deployment Production de producto como fallback. Tras instalación autorizada, registrar el resultado real en Pages. Referencias: [Build watch paths](https://developers.cloudflare.com/pages/configuration/build-watch-paths/) y [GitHub integration / skip builds](https://developers.cloudflare.com/pages/configuration/git-integration/github-integration/).
2. **Bootstrap hasta la rama default, sin exigir el check nuevo todavía.** El patch debe recorrer PR protegido a `desarrollo`, luego a `certificacion` y finalmente a `main`. Mientras `main` no contenga el workflow, GitHub no ejecuta `pull_request_target` para esos PRs: el evento requiere que el workflow exista en la rama default. Esos PRs quedan bajo las protecciones actuales —PR, aprobación humana, `security-audit` y rama al día— y requieren revisión independiente del patch. Después de integrar en `main`, el workflow queda instalado; su check independiente se acredita en PRs posteriores antes de cambiar Settings. Esta ventana de bootstrap es residual conocido, no evidencia de que el nuevo control ya esté efectivo.
3. **Comprobar el job independiente antes de editar Settings.** Después de integrar el bootstrap, verificar en PRs reales a las ramas protegidas que aparece el contexto exacto `Protected Workflow Integrity`, asociado al head/candidato actual. Confirmar al menos: PR ordinario pasa; cambio a workflow/control sin aprobación válida falla; aprobación confiable del head vigente pasa; un head nuevo invalida la aprobación previa; editar el PR para cambiar su base vuelve a consultar la lista de archivos usando la base actual. La pantalla de branch protection solo debe usar el nombre/contexto que GitHub haya emitido efectivamente.
4. **Exigir el status por rama, después de observarlo.** Añadir `Protected Workflow Integrity` junto a `security-audit` en la regla clásica de cada rama solo cuando ese check exista y se haya vinculado al candidato actual para esa rama. La activación de `desarrollo`, `certificacion` y `main` se agrupa en un objetivo de Settings, registrando evidencia por rama. Las capturas ya confirman para las tres reglas clásicas la desestimación de approvals obsoletas y el requisito de branch up-to-date; se preservan. Mantener también PR, una aprobación, “Do not allow bypassing”, restricciones de force-push/deletion y el actor de bypass del ruleset. No habilitar el check antes de su primera emisión.

La lista de archivos de un PR es el diff contra su base actual. El evento `edited` reejecuta PWI cuando cambia explícitamente el destino/base aunque no cambie el head; la API de archivos se vuelve a consultar en esa corrida. Los demás tipos configurados de `pull_request_target` (`opened`, `synchronize`, `reopened`, `ready_for_review`) y `pull_request_review` (`submitted`, `dismissed`) cubren creación/actualización del head, reapertura/estado de revisión y cambios de review; no aportan otro cambio de archivos sin head que requiera un evento distinto. Un avance de la rama base también puede cambiar el diff sin mover el head y no es, por sí mismo, una edición del PR. Aunque las reglas actuales requieren que la rama esté actualizada, eso no demuestra estáticamente que un avance del base genere una corrida nueva: un head que ya desciende del nuevo base podría continuar actualizado. Antes de requerir PWI, comprobar en GitHub que un avance del base recalcula el contexto contra la lista de archivos vigente aun cuando el SHA del head no cambie. Si no se demuestra, añadir una señal confiable que fuerce esa reevaluación o mantener G10 bloqueado; no asumir que `synchronize` siempre se emite en ese caso.

La aceptación del status y su asociación con el head son gates runtime; el patch no los acredita. GitHub documenta que `pull_request_target` usa contexto de la rama default y que un required check debe pasar sobre el SHA más reciente. Por eso el paso 3 es obligatorio aun cuando el YAML tenga el job correcto:
[eventos de Actions](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows), [uso seguro de `pull_request_target`](https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target), [required status checks](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks).

## Revisión estática independiente de V3 (histórica)

La revisión independiente del patch V3 lo clasificó hold_for_evidence: no confirmó bypass
de código y confirmó el alcance de cuatro rutas, base y SHA descritos arriba. Permanecen
decisiones runtime/configuración que el patch no puede acreditar:

- La emisión del primer check PRT y su resultado de evaluación de la policy predeterminada
  de repo público; la cuenta es personal, sin Policy insights Enterprise.
- El posible cambio de archivos por avance de la base sin cambio de SHA head; las capturas
  recibidas confirman dismiss stale y branch up-to-date, pero no prueban por sí solas una
  nueva ejecución del workflow.
- El efecto del primer merge a main sobre Cloudflare Pages y la asociación del check PWI
  al SHA actual. Las reglas vigentes, según las capturas, solo requieren security-audit.
- Si hay merge queue, compatibilidad del check con ese evento antes de hacerlo requerido.

La revisión V3 no ejecutó pytest, actionlint, Docker ni workflows remotos. Sus hallazgos de
runtime/configuración siguen vigentes y G10 permanece abierto.

## Lecturas administrativas recibidas — 2026-10-08

- GitHub MCP reporta `owner.type=User` para `romelhc95/studiamatch`: es repositorio de cuenta
  personal, no de organización/Enterprise. El usuario confirmó que Settings → Actions → Policies
  no muestra policies creadas y que Policy insights indica que la supervisión de reglas está
  disponible para cuentas Enterprise. No hay evidencia de scope superior aplicable. Por ser un
  repositorio público, la policy predeterminada de `pull_request_target` está en evaluate hoy;
  GitHub anuncia su enforcement para 2026-11-02. El intento read-only de consultar Actions
  settings por el GitHub MCP fue rechazado por la allowlist del conector; no se modificó nada.
- Cloudflare Pages: Production branch `main`, automatic deployments enabled, Build watch paths
  incluye `*` y excluye nada; raíz `web`, build `npm install && npm run build`, output `out`,
  build comments enabled, build cache disabled, build system v3 y sin deploy hooks.
  La documentación oficial indica que * coincide con todos los archivos, y que un cambio
  coincidente dispara un build ([Build watch paths](https://developers.cloudflare.com/pages/configuration/build-watch-paths/)).
  Por lo tanto, el patch de controles no queda filtrado por esta configuración; un merge a
  main entra en el flujo de builds/deployment de la rama Production. No se observó un build
  del bootstrap. En respuesta sobre Preview branches, el usuario indicó que Production usa
  solo `main` y compartió Deployments con un Preview histórico de
  `feat/h3req1-development-remote-tests`; eso acredita un Preview para esa rama, no el selector
  actual Preview branch control ni su efecto para el bootstrap. El usuario indicó que existe
  un MCP cf-builds, pero ese conector no está expuesto en las herramientas de esta sesión.
- La merge queue sigue sin confirmarse. Falta una respuesta sí/no para cada rama protegida
  (desarrollo, certificacion, main).
- La metadata read-only del repositorio indica `allow_squash_merge=true`, `allow_merge_commit=true`,
  `allow_rebase_merge=true` y `allow_auto_merge=false`. El squash ofrece un mecanismo concreto
  para fijar el título `[CF-Pages-Skip]` en el commit bootstrap; su efecto real aún debe
  comprobarse en Pages y el uso requiere autorización de promoción independiente.
- No se recibió el selector de Preview branch control (`None`, `All` o `Custom` y patrones).
  Ya existe evidencia de un Preview histórico, pero no de la regla actual ni de su aplicación
  al bootstrap. Confirmar el selector antes de abrir el PR, que aún no está autorizado.

Con estos datos, la configuración de Pages para Production está confirmada: include `*` hace
que los cuatro cambios del patch coincidan y automatic deployments está habilitado. Cloudflare
documenta que un mensaje de commit que comienza con `[CF-Pages-Skip]` omite ese deployment;
la propuesta futura prefija tanto el commit bootstrap como el squash y verifica el resultado
del PR antes del merge. El efecto real del proyecto aún no está comprobado. El Preview branch
control se reportará cuando se prepare esa única promoción; no se pide repetir Production ni
watch paths ya recibidos.

El repositorio es público. GitHub documenta una policy predeterminada que bloquea
pull_request_target cuando no existe una Actions event policy aplicable; ahora está en
evaluate, por lo que los runs continúan, y la aplicación está anunciada para el 2 de
noviembre de 2026. Si Policy insights confirma que no hay una policy efectiva heredada, el
bootstrap requiere que el administrador autorice ese evento antes de la fecha de enforcement.
Fuente: [GitHub — securely using pull_request_target](https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target)
 y [control de ejecución de workflows](https://docs.github.com/en/actions/how-tos/administer/control-workflow-execution).

## Dependencias y bloqueos concretos

1. **Política Actions para `pull_request_target`:** GitHub MCP confirma que el repo es público y personal (`owner.type=User`); el usuario confirmó que no es Enterprise y no hay Policies creadas. GitHub documenta que la policy pública predeterminada está hoy en `evaluate`, así que las ejecuciones continúan, con enforcement anunciado el 2026-11-02. Policy Insights es Enterprise-only y no se vuelve a pedir. Antes de cerrar G10 hay que observar un run PRT real y su resultado de evaluación. Si PWI sigue usando PRT después del 2026-11-02, agrupar antes de esa fecha una escritura Actions event policy a nivel repo que permita exactamente PRT; la preparación no cambia policy. Fuente primaria: [Securely using `pull_request_target`](https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target).
2. **Cloudflare Pages:** Production branch y Build watch paths ya están recibidos; no volver a pedirlos. Falta el modo Preview branches (`None`, `All` o `Custom` y patrones si aplica). La documentación oficial de Pages indica que los prefijos `[CI Skip]`, `[CI-Skip]`, `[Skip CI]`, `[Skip-CI]` y `[CF-Pages-Skip]` omiten el deployment y no distinguen mayúsculas; cuando se omite un build, no aparece su check run. En un bootstrap autorizado, el commit de rama y squash title pueden llevar `[CF-Pages-Skip]`, pero su efecto en este repo/PR aún debe comprobarse antes del merge; no tratar ausencia de estado Pages como build PASS. Si aparece un deployment Preview inesperado o el skip no resulta aplicable, no integrar y preparar una alternativa agrupada con excludes precisos de las cuatro rutas. La configuración y resultado real deben demostrar que no se publica producto. No cambiar Settings de Pages en esta preparación. Fuente primaria: [Cloudflare Pages GitHub integration](https://developers.cloudflare.com/pages/configuration/git-integration/github-integration/).
3. **Primera instalación en default branch:** el workflow no puede ser requerido antes de instalarse. Los PRs de bootstrap a `desarrollo`, `certificacion` y `main` no ejecutan PWI hasta que el archivo exista en `main`; quedan bajo las protecciones existentes y revisión humana independiente. Su riesgo de bootstrap no se oculta como si ya existiera el control.
4. **Ejecución local:** suites y actionlint no fueron ejecutados por el límite de esta preparación. Requieren acreditación de Docker y la ejecución local autorizada dentro del contenedor. El resultado estático/aplicabilidad no equivale a PASS de runtime.
5. **GitHub real:** todavía no se han observado check run, fuente de status, asociación al SHA actual, bloqueo ante falta de aprobación humana (incluida aprobación solo de Bot), re-evaluación tras un avance de base con head estable ni estado exacto disponible en Settings. El estado de merge queue no está confirmado en las capturas; si está habilitada, verificar compatibilidad del required check con `merge_group` antes de exigirlo. Sin esas evidencias, G10 permanece abierto.
6. **Ruta de promoción:** el patch parte de la base confiable especificada; antes de publicarlo se debe cotejar que el candidato de cada PR no arrastre archivos WIP fuera de las cuatro rutas anteriores. No se ha creado rama ni PR.

## Límite de autorización agrupada

Un único objetivo de autorización posterior debe cubrir: commit de solo controles con prefijo `[CF-Pages-Skip]`, PR por flujo protegido, revisión humana independiente del bootstrap inicial, merge squash del patch V4, validación CI local/remota, observación del check por rama y la actualización agrupada de las tres reglas clásicas para requerir el nuevo contexto. Antes del 2026-11-02, incluir también una escritura de Actions event policy de repo para permitir PRT si el comportamiento observado aún lo requiere. No autoriza código de producto, pushes directos, merge automático, cambios de secreto, instalación/cambio de motor Docker, deploys, DB ni alteración del ruleset/bypass actual. Si el skip no se demuestra antes del merge, se detiene el PR y se presenta una alternativa de Build watch paths para autorización agrupada.

No se suman puntos de gate por este documento o el patch preparado. El estado vigente es **10%**; G10 sigue abierto y no hay GO.

## Addendum de dependencias — respuesta del usuario y lectura vigente — 2026-10-08

Este addendum sustituye la solicitud anterior de Policy insights/scope como dato humano
pendiente. El usuario confirmó que Settings → Actions → Policies no tiene policies creadas,
que la cuenta no es Enterprise y que Policy insights muestra supervisión solo para Enterprise.
GitHub MCP reporta `owner.type=User`; el repositorio público pertenece a una cuenta personal,
sin scope de organización. La policy predeterminada GitHub para PRT aplica hoy en modo
`evaluate`, que deja continuar las ejecuciones, y GitHub anuncia enforcement el 2026-11-02.
No se pide volver a consultar Policy insights ni a reenviar capturas. El primer run real
determinará si la evaluación del workflow queda registrada y si PRT ejecuta en el repo.
Si PWI debe seguir usando PRT después del 2026-11-02, se agrupa antes de esa fecha la escritura
de Actions event policy del repositorio que permita exactamente ese evento; sin esa excepción,
la policy predeterminada lo bloqueará. No se cambia policy en esta preparación.

El usuario confirmó el resto de Build configuration de Cloudflare Pages: Production `main`,
automatic deployments, include `*`, exclude vacío, root `web`, `npm install && npm run build`,
salida `out`, build comments activo, cache desactivado, build system v3 y sin deploy hooks.
Esto demuestra que las cuatro rutas bootstrap coinciden con el watch path. El usuario compartió
un Preview histórico en Deployments, pero siguen pendientes el selector de Preview branch
control (`None`, `All` o `Custom` y, si aplica, patrones) y sí/no de merge queue por
`desarrollo`, `certificacion`, `main`. La lectura del MCP `cf-builds`
no puede hacerse en esta sesión porque no hay herramienta de ese conector habilitada.

No se usará `[CF-Pages-Skip]` ni se escribirá Build watch paths sin autorización. En la
autorización agrupada futura se incluirá, si hace falta para evitar builds del patch de
controles, excluir solo las cuatro rutas del bootstrap y verificar el efecto real antes de
integrar el PR. No hubo cambios externos; el patch, sus pins y su revisión siguen intactos.

## Addendum vigente — patch sincronizado y resultado r9 — 2026-10-09

La sección inicial describe el artefacto V4 previo a sincronizar el origen del helper; conserva
su historial y no identifica el patch que debe usarse ahora. El patch operativo vigente es
`../evidencia/h3req1_ci_bootstrap_minimal.patch`, SHA-256
`033fe1263ceb86b1f609613de52de41b071153f7e8eabb6a11848b5b69c1a450`. El artefacto anterior se
preserva como `h3req1_ci_bootstrap_minimal_v4_pre_sync.patch`, SHA-256
`68bb4037f665c4e82c91b89faae939a20ab90cebbf85cff0b4a2f90b19682c26`. El patch vigente cambia
el checkout del helper a `github.event.pull_request.base.sha` para coincidir con el workflow
candidato; la diferencia con el draft de default branch descrita arriba corresponde al artefacto
histórico anterior.

El patch vigente afecta únicamente cuatro rutas: PWI workflow, `security-audit.yml`, helper y
pruebas. Su `git apply --check` en snapshot limpio, aplicación aislada, `diff --check` y
coincidencia del workflow/helper/test con el candidato fueron acreditados en la reconciliación
vigente. `git apply --stat` confirma 4 rutas, 485 inserciones y 1 eliminación. En r9 V4,
actionlint pasó sobre los tres workflows candidatos; ShellCheck falló después, por lo que la
suite pytest oficial, ESLint, TypeScript y suites focales no se alcanzaron. No se ha publicado ni
instalado el control, no se abrió PR, no se tocó GitHub Settings y G10 continúa 0/10.

La autorización agrupada futura debe referirse al patch sincronizado SHA `033fe…` y revisar su
diff final antes de cualquier commit/PR. Los datos administrativos ya recibidos no se vuelven a
solicitar; siguen pendientes el resultado real del primer workflow, el modo Preview branch y la
compatibilidad de merge queue antes de exigir el check, sin cambios remotos en esta preparación.

### Addendum de mitigación Pages documentada — 2026-10-08

La documentación oficial de la integración GitHub de Pages confirma que un prefijo de commit
`[CF-Pages-Skip]` omite el deployment; también confirma que los builds omitidos no generan un
check run de Pages. El mecanismo está documentado, pero aún no se verificó en un PR de este
repositorio ni bajo la regla real de squash. La autorización futura debe conservar el prefijo
en el commit y squash title, comprobar explícitamente que no se creó un deployment Preview o
Production y no interpretar la falta de check run como validación satisfactoria. Si falla esa
comprobación, detener la integración y solicitar por objetivo la alternativa de Build watch
paths; no escribir configuración durante esta preparación. Fuente primaria:
[GitHub integration](https://developers.cloudflare.com/pages/configuration/git-integration/github-integration/).
