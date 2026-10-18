# H3REQ1 G10 — paquete local de bootstrap CI en dos etapas — R179

## Estado y candidato

Preparación local para revisión; no se creó commit, push, PR, merge, configuración remota,
workflow run ni deploy. G01–G09 conservan el cierre local R178. G10 sigue pendiente y no se
declara `GO_LOCAL_PR`.

- Checkout: `/home/romel/src/studiamatch-h3req1-sync-20261002`.
- Rama: `feat/h3req1-sync-20261002`.
- HEAD baseline: `4eb4d877a50b012bb630a129bd0c74482c33be9c`; no identifica por sí solo el WIP.
- R6 preservado antes de este delta: manifest SHA-256
  `331aa3ccd9d3fbc6476637d929d69b853d44247bb91e5d75671174f1f9a056ac`, cuerpo SHA-256
  `5541f60fe3dddab4c302d6de28dfb8116239d7e48666a909e4620a71b31deb09`; sus 234/234 archivos
  fijados coincidían byte/modo/hash y sus diez encabezados coincidían con la plantilla.
- R7 queda fijado por `.context/evidencia/h3req1_pr_scope_manifest_2026-10-12_r7.json` y el
  cuerpo local `.context/evidencia/h3req1_pr_body_draft_local_review_2026-10-12_r7.md`.
  El manifest R7 incluye explícitamente `tests/test_protected_workflow_review.py` y este
  documento; enumera por separado las evidencias y exclusiones.

## Bootstrap en dos etapas

### Etapa 1 — primer PR, sin dependencia circular

El primer PR incluye el workflow independiente `.github/workflows/protected-workflow-integrity.yml`,
el helper `scripts/security/protected_workflow_review.py` y sus pruebas
`tests/test_protected_workflow_review.py`. `security-audit` continúa ejecutando la suite del
helper y actionlint valida el workflow nuevo. El workflow `security-audit` de la etapa 1
mantiene los demás jobs/controles del candidato y su agregador `security-audit`; quita solamente
el waiter de Protected Workflow Integrity, su evento `pull_request_review`, los permisos de
lectura `checks`/`pull-requests` que el waiter necesitaba, y la dependencia/aserción del agregador.
No se quita ni se relaja el check `security-audit`, no se modifica ninguna protección remota y
no se sustituye la revisión humana.

Esto evita que el primer PR espere un workflow que todavía no está disponible en la rama
predeterminada. GitHub documenta que `pull_request_target` solo dispara si el workflow existe en
la rama predeterminada; el `workflow_dispatch`/archivo dentro del PR no demuestra que ese evento
haya corrido. Véase [eventos de Actions](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)
y [uso seguro de pull_request_target](https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target).

Cambios exactos del candidato R7:

- `security-audit.yml` etapa 1 SHA-256:
  `ddbb87677dfe7aed2da346ae9d4c139ede0af5b75a7c04372f6ec1b7bf2a473d`.
- Workflow PWI SHA-256: `016551e6a6e280dcd515788ffcf93b18a6d48647079e3c0cd7be9c2d4f58864b`.
- Helper SHA-256: `87ad479158a24fb528f0c58464ebb202858cdaea10e7badb2cb4b00ac5ee6827`.
- Pruebas SHA-256: `1abd99e6130fed9e3df499e59252eb3a0de9f32d5b3019e34056dda4812ad4c6`.
- El patch mínimo de controles preexistente, base/rutas limitadas, conserva SHA-256
  `033fe1263ceb86b1f609613de52de41b071153f7e8eabb6a11848b5b69c1a450`; no contiene el waiter.
  No reemplaza el diff integral del candidato R7.

### Etapa 2 — habilitar PWI en el agregador

Después de que el workflow PWI exista en la rama predeterminada y se compruebe una ejecución
real exitosa para el SHA esperado, aplicar el parche local preparado
`.context/evidencia/h3req1_g10_security_audit_stage2_2026-10-12.patch` (SHA-256
`c522720a8bfd26b47c09036fdc69cf86d4a34065bfedc9abb11d66790e4b317d`). El parche añade el
trigger de revisión, solo permisos de lectura `checks` y `pull-requests`, el job waiter que
comprueba workflow/job, PR, evento y `head SHA`, y la condición que exige PASS dentro del
agregador existente `security-audit`. El resultado requerido por las reglas clásicas continúa
siendo el agregado `security-audit`; no se cambia ni desactiva otro check o protección.

El SHA de la variante completa de etapa 2 es
`59723860d8f1b60521469d6c8310d5500a87841b27bf4d1f08138ad778a902b8`, idéntico al `security-audit.yml`
preservado en el manifest R6. El parche es evidencia para una segunda operación protegida;
no forma parte del cambio activo de etapa 1 ni se aplicó al checkout.

## Validaciones ejecutadas y límites

- Integridad R6 antes de editar: 234/234 entradas (scope + evidencia), modo/tamaño/SHA exactos;
  hash del body y manifest R6 verificados; plantilla R6 con 10/10 encabezados exactos.
- Transición estructural R7: `security-audit` de etapa 1 no declara trigger `pull_request_review`,
  job waiter ni referencia `needs.trusted-workflow-integrity`; conserva el agregador y los nueve
  jobs/gates originales del candidato. El test protegido sigue en la lista offline y PWI en
  actionlint. PASS.
- Aplicación en copia temporal del parche de etapa 2: `patch --dry-run` y aplicación PASS; el
  archivo resultante coincide byte por byte con SHA-256 `59723860…902b8`. `git apply --check`
  contra el archivo de etapa 1 PASS. No se modificó el estado activo a etapa 2.
- R176 ya acredita actionlint 1.7.7 sobre la variante completa de etapa 2 con hash R6 exacto,
  el workflow PWI y `db-sync-to-pro.yml`; su resultado se reutiliza solo para esas entradas.
- La pasada pytest focal que incluyó `tests/test_protected_workflow_review.py` junto con
  dos archivos de contrato terminó 72 passed en Docker en R176; el hash de este test es el mismo (`1abd99e…ad4c6`). No se repitió la suite.
- Una invocación local para volver a pasar actionlint sobre la variante de etapa 1 fue rechazada
  por revisión automática antes de ejecutarse: el comando incluía borrado recursivo del directorio
  temporal. No se ejecutó ese comando ni se buscó una vía para eludir el rechazo. Por ello
  actionlint de la variante de etapa 1 queda explícitamente pendiente; el resultado R176 de
  etapa 2 no se atribuye a la entrada distinta de etapa 1.
- No hubo prueba GitHub real, enforcement, revisión real, merge queue, check del SHA remoto ni
  despliegue. R5 es revisión estática anterior del scope R5/R6; no se extiende como revisión
  independiente de los deltas R7.

## Inventario de R7

El manifest R7 propone únicamente las rutas explícitas en `scope.entries`, incluye el test
protegido que faltaba en R6 y la nota R179. Los artefactos de etapa 2 quedan seleccionados como
evidencia local, no como fuente activa del primer PR. No se incluyen automáticamente caches,
`node_modules`, `.next`, `out`, dependencias vendorizadas no listadas, datos temporales, secretos,
`.env*`, Docker resources ni el resto de los untracked. El inventario distingue `proposed_change`
de `canonical_evidence`; evidencia no significa inclusión en el PR.

La revisión R5 cubrió el inventario anterior y se conserva sin alteración. Por el nuevo archivo de
test/package y la edición de `security-audit.yml`, el alcance actual necesita revisión independiente
R7 antes de cualquier PR; esta preparación no la inventa ni la sustituye.

## Configuración remota: comprobado frente a antecedente

No se hicieron lecturas remotas en esta preparación. Los siguientes son antecedentes aportados
por el responsable/capturas, no configuración actual revalidada:

- GitHub Branches mostró reglas clásicas para `desarrollo`, `certificacion` y `main`, con PR,
  una aprobación y `security-audit`; también reglas de stale review/up-to-date y sin force-push/
  deletion. Una Ruleset activa `owner-only-protected-branch-updates` apuntaba a esas ramas y
  mostraba un actor de bypass. Su interacción efectiva con las reglas clásicas no se deduce aquí.
- El responsable informó que Actions Policies estaba sin policies creadas y que la cuenta no es
  Enterprise. No prueba la política efectiva heredada ni la evaluación actual de
  `pull_request_target`.
- Cloudflare Pages fue descrito con Production branch `main`, deployments automáticos e include
  `*`/exclude vacío; hay una captura de deployment Preview histórico. No se vuelve a afirmar como
  lectura actual ni se infiere de esto la rama predeterminada de GitHub.
- `main` como rama de Production no demuestra que `main` sea la rama predeterminada de GitHub.

## Lecturas remotas necesarias (solo lectura, sanitizadas)

1. **Rama predeterminada:** GitHub Settings → General → Default branch; confirmar también
   visibilidad del repo. API de lectura: `GET /repos/romelhc95/studiamatch` (`default_branch`,
   `visibility`). No mostrar credenciales.
2. **Protección efectiva por rama:** Branches → revisar cada regla clásica y Rulesets activos
   para `desarrollo`, `certificacion`, `main`: target/patrón, enforcement, PR requerido,
   approvals, stale dismissal, up-to-date, status contexts exactos, required workflows, bypass
   actors/tipo/cantidad, force-push y deletion. Confirmar además merge queue por rama. La lectura
   debe distinguir reglas individuales de su efecto combinado.
3. **Actions:** Settings → Actions → General/Policies: alcance efectivo repo/owner, política de
   ejecución de `pull_request_target`, acciones permitidas, permisos predeterminados del token y
   cualquier regla heredada. Después de la instalación, leer el run de PWI: evento, workflow/job,
   conclusión, base y `head SHA`; compararlo con `security-audit` para el mismo SHA. Antes de
   exigir el waiter, confirmar que PWI corre en el repo con token de lectura y que el check se
   emite para el evento esperado.
4. **Cloudflare Pages:** proyecto `studiamatch` → Settings → Builds/Deployments: branch control
   de Preview (None/All/Custom y patrones), Production branch, automatic deployments, watch
   includes/excludes y deploy hooks. En Deployments, confirmar el branch/SHA/Environment del último
   Production y Preview y qué combinación de rutas los dispara.

GitHub actualmente documenta una policy predeterminada que afecta `pull_request_target` en
repositorios públicos y fecha de enforcement anunciada para 2026-11-02. Antes de integrar se debe
leer su decisión efectiva; si bloqueará el evento, hace falta una decisión/authorization separada
para una excepción mínima que permita solo el flujo aprobado. No se amplían permisos del token ni
se crea una policy en esta preparación. Fuente: [GitHub — securely using pull_request_target](https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target).

## Decisiones antes de la ejecución remota

- Confirmar si el Preview de una rama `desarrollo` es aceptable. Si no, elegir posteriormente,
  con autorización propia, un mecanismo limitado para impedir ese build; no asumir que un prefijo
  de commit lo evita sin verificar la configuración/efecto de este repo.
- Confirmar el impacto de la rama `main`: con auto-deploy Production activo, una promoción a
  `main` puede ejecutar un build/deploy. La aceptación del responsable o una excepción precisa
  de watch path debe preceder esa promoción; no se hizo ninguna.
- Si una merge queue está activa, revisar y preparar `merge_group` antes de exigir el check;
  GitHub explica que los checks de cola deben ejecutarse para ese evento. Fuente: [required checks y merge queue](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks).
- Acordar si el bootstrap de controles viaja con el candidato H3 por el flujo protegido normal o
  como PR separado de controles. El segundo evita mezclar la promoción funcional, pero también
  requiere su propio ciclo protegido y no elimina el efecto Pages en la llegada a `main`.
- La etapa 2 necesita una instrucción separada para preparar/publicar el cambio, revisión humana
  independiente y comprobar el nuevo check. No ejecutar el patch ni configurar GitHub hasta esa
  instrucción.

## Resultado

R179 deja listo para revisión el manifiesto/cuerpo PR R7, el workflow Stage 1 activo local y el
parche Stage 2 separado. G01–G09 locales permanecen completos por R178; G10 remoto, revisión R7,
actionlint exacto de Stage 1 y lecturas/decisiones remotas siguen pendientes. Métricas no cambian:
tablero G01–G10 9/10 = 90%; cierre local G01–G09 9/9 = 100%, sin equivalencia a `GO_LOCAL_PR`.
