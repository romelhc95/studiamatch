# H3REQ1 G10 — cierre local del paquete CI — R180, 2026-10-12

## Candidato y alcance

- Checkout: `/home/romel/src/studiamatch-h3req1-sync-20261002`.
- Rama: `feat/h3req1-sync-20261002`.
- HEAD baseline: `4eb4d877a50b012bb630a129bd0c74482c33be9c`; identifica la base, no el WIP.
- El checkout original `/home/romel/src/studiamatch` y la evidencia R6/R7 se preservan.
- No hubo commit, push, PR, merge, lectura/configuración remota, workflow remoto ni deploy.
- G01–G09 se conservan completos por R178. Este corte solo corrige y valida la preparación local G10.

## Hallazgos de la revisión R7 y correcciones

La revisión independiente R7 confirmó el inventario de 91 rutas propuestas, 149 evidencias,
240 entradas únicas, hashes/modos/tamaños, la plantilla y la exclusión de WIP no listado. No
identificó HIGH/CRITICAL. Encontró seis rutas de R7 que no coincidían con las tres allowlists de
Stage 1 y por ello hacían fallar el scope guard del candidato combinado. Se agregaron como
coincidencias exactas a `allowed_h3_local`; no se amplió ningún patrón:

- `db/migrations/20261010_h3_admin_members_service_select.sql`
- `scripts/core/universal_harvester.py`
- `tests/test_h3req1_local_pipeline_walk.py`
- `web/src/app/HomeContent.tsx`
- `web/src/app/compare/CompareContent.tsx`
- `web/src/app/page.tsx`

La revisión también observó que Stage 2 no consume la Checks API. El patch R8 elimina `checks:
read` y evita propagar `pull-requests: read` a todos los jobs: el waiter recibe solo
`actions: read` y `pull-requests: read` a nivel del job. El permiso global `actions: read` de
Stage 1 se conserva porque el gate H2 existente consulta runs/jobs/artifacts; Stage 1 no recibe
`checks` ni `pull-requests`.

La pasada semántica independiente detectó que el evento `pull_request_review` de Stage 2 no tenía
filtro de rama, aunque `Protected Workflow Integrity` solo ejecuta para `desarrollo`,
`certificacion` y `main`. Se ajustó el job waiter para esas tres bases y el agregador acepta el
resultado `skipped` solo para eventos/base fuera de ese conjunto. La base se transmite por `env`
para evitar interpolarla dentro del shell. El checker sintético cubre PR/review protegido,
review de base no protegida, push y dispatch. No se modifica el trigger ni el agregado activo
Stage 1.

La revisión independiente final del inventario/cuerpo R8 queda pendiente hasta congelar y fijar
los hashes finales; la pasada semántica previa no se trata como revisión integral del paquete.

## Stage 1: flujo preservado

`security-audit.yml` continúa con el agregado/status `security-audit` y sus jobs y condiciones
existentes. Stage 1 no declara el evento `pull_request_review`, no define el job
`trusted-workflow-integrity` y el agregado no depende de ese job. El primer PR no espera un
workflow que aún no esté instalado en la rama predeterminada. Los controles existentes no se
eliminaron ni debilitaron.

Workflow Stage 1 después de la corrección: SHA-256
`105ac6eb2c615e6b6ddaba51c02295c696b18faa51dc638048ca516c2f9b2e91`.

## Stage 2: parche separado e inactivo

El patch R8 es `.context/evidencia/h3req1_g10_security_audit_stage2_2026-10-12_r8.patch`,
SHA-256 `f55a1b17aab8cad4b6071e62df8318339686038ce6827cd938f973f046a1a5f1`. `git apply --check`
pasó contra Stage 1. En una copia temporal del workflow el patch se aplicó y generó Stage 2;
actionlint validó esa variante. La copia temporal
`/tmp/h3req1-stage2-r8-protected-base-awgcxmpm/.github/workflows/security-audit.yml` se conserva.
El patch no se aplicó al workflow activo. Solo una etapa futura, después de instalar PWI en la
rama predeterminada y comprobar un run real exitoso para el SHA/evento requerido, puede integrar
el waiter y su dependencia al agregado. Eso requiere autorización protegida separada.

## Validaciones locales ejecutadas

### actionlint en Docker

- Asset: actionlint 1.7.7; tarball verificado contra el pin SHA-256
  `023070a287cd8cccd71515fedc843f1985bf96c436b7effaecce67290e7e0757`; binario SHA-256
  `9f7dedb4e23f89f2922073d1a6720405b7b520d4f5832ebb96f0d55a2958886c`.
- Imagen local: `sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63`.
- Contenedor `h3req1-r180-actionlint-protected-base-v2-20261012`: sin red, rootfs read-only, capacidades retiradas,
  límites de 256 MiB/1 CPU; cuatro workflows montados read-only, sin checkout ni secretos.
- Se validaron Stage 1 exacto, Stage 2 sintético R8, `protected-workflow-integrity.yml` y
  `db-sync-to-pro.yml`; salida `actionlint_exit=0`.
- La invocación R179 anterior fue rechazada por el revisor automático antes de ejecutarse porque
  incluía eliminación recursiva de un temporal. No se atribuye resultado a esa invocación; R180
  conserva temporales y contenedores y no ejecuta limpieza.
- El intento anterior con el flag inválido `-color=never` terminó en exit 2 antes de analizar YAML.
  No cuenta como validación. Se corrigió a la opción compatible `-no-color`; el comando corregido
  sí ejecutó los cuatro archivos.

### Transición local Stage 1 → Stage 2

- El checker estructural `.context/evidencia/h3req1_g10_transition_check_r180.py` (SHA-256
  `da5272c6492fd3952e13d2cdd42e0f6a18516630b0ab72a9e19459bc3487cdf1`) se ejecutó en Docker
  contra Stage 1, Stage 2 derivado y patch. Resultado:
  `transition=PASS|shell_gate_cases=9/9|stage1_waiter=absent|stage1_aggregate=preserved|stage2_waiter=protected-bases-only|stage2_permissions=job-scoped|unprotected-review=skipped|checks_read=absent`, exit 0.
- La primera ejecución del checker terminó con `stage2_aggregate_gate=missing` porque su propio
  texto esperado asumía una indentación distinta del patch; el YAML no se había cambiado por esa
  falla. Tras corregir la aserción y agregar cobertura de base protegida/no protegida, la nueva
  ejecución pasó. El contenedor fallido se conserva.
- `git apply --check` verifica que el patch sigue siendo aplicable al Stage 1 actual; actionlint
  validó los cuatro workflows exactos/derivados después del cambio.
- ShellCheck 0.11.0 validó el bloque nuevo de clasificación de base/evento extraído del Stage 2,
  exit 0 (`h3req1-r180-shellcheck-stage2-gate-v1-20261012`). La primera inspección del paso
  agregado completo sin preprocesar GitHub expressions terminó en exit 1 por SC2016/SC2050 sobre
  expresiones `${{ ... }}` no expandidas y por falta de shebang en la extracción temporal; ese
  intento no se cuenta. El gate aislado conserva el código nuevo exacto, declara Bash y pasó 9
  escenarios de shell en el checker Docker.

### Scanner del candidato R8

- El scanner versionado `scripts/security/scan_credentials.sh` (SHA-256
  `5d74e61c3aa2afabea5da78c7d60504bfb154035204000e9469e3788bd28571e`) se ejecutó en Docker
  sobre las 91 rutas de `scope.entries`, no sobre el WIP completo. Antes del scan se comprobaron
  SHA-256, tamaño y modo de todas las entradas; no había symlinks ni `.env*` operativos.
- Contenedor `h3req1-r180-credential-scan-v1-20261012`, misma imagen fijada, sin red, rootfs
  read-only, sin gitdir ni secretos montados. Resultado `credential_scan=PASS|paths=91|exit=0`,
  exit 0. La captura sanitizada durable está en
  `h3req1_g10_credential_scan_r180_2026-10-12.txt`; no se emitieron valores.

### Scope guard de Stage 1

El comprobador reproducible
`.context/evidencia/h3req1_g10_scope_allowlist_check_r180.py` (SHA-256
`d6ac37bfa7091cf8728a420b3c55527406eb2716fd1f7ba2ee12a5862998183c`) compara las 91 rutas
propuestas con las dos expresiones y la lista exacta extraídas del workflow. Corrió en el
contenedor `h3req1-r180-scope-allowlist-v2-20261012`, aislado y sin red, sobre el manifest R7
preservado. Resultado: `scope_allowlist=PASS|proposed=91|regex=71|exact=20|review_fixes=6/6|missing=0`, exit 0.
Las 20 rutas exactas incluyen las seis correcciones y el checker confirma que cada una está en
la lista exacta (no depende de un patrón más amplio). Es una comprobación sintética del allowlist,
no un workflow run de GitHub.

El diff de la corrección pasó `git diff --check`. Los resultados R176/R5 solo se reutilizan donde
sus inputs siguen idénticos; no se atribuye actionlint R176 a Stage 1. El test focal R176 que
incluye `tests/test_protected_workflow_review.py` permanece válido por hash coincidente y no se
repitió.

## Inventario y límites

R7 se preserva como antecedente y no se reescribe. R8 conserva las mismas 91 rutas propuestas; se
renuevan los hashes de los archivos que cambiaron y se separan las evidencias del código propuesto.
La lista completa de modos, tamaños y SHA está en el manifiesto R8. No se incorporan automáticamente
caches, `node_modules`, `.next`, `out`, `.env*`, secretos, datos temporales o WIP no listado. El patch
Stage 2 y esta nota son evidencia local, no cambios activos adicionales del workflow.

No se leyó GitHub ni Cloudflare. Rama predeterminada, reglas clásicas/Rulesets efectivos, merge
queue, Actions policy, ejecución PWI para el SHA, required checks efectivos y automatismos Pages
siguen pendientes de lectura autorizada en otra sesión. YAML/actionlint local no prueba instalación,
enforcement, revisión humana, resultado CI remoto ni despliegue.

## Estado

El delta local de Stage 1, el parche separado Stage 2 y sus checks locales están preparados para
revisión final independiente del inventario/cuerpo R8. G10 remoto permanece NO-EJECUTADO. G01–G09
no se reabren. La métrica histórica sigue en 9/10 (90%) y la métrica local G01–G09 en 9/9 (100%);
ninguna implica `GO_LOCAL_PR` ni `GO_DEVELOPMENT_REAL`.
