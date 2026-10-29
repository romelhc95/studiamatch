# Checkpoint local — contrato editorial H3REQ1

## Remediación local de promoción por TL

Revisión posterior de continuidad: la sesión Luna conserva como último mensaje
el NO-GO del 2026-10-29 00:04:23 UTC; no hay continuación nueva acreditada allí.
Lectura GitHub actual confirma Development `941eca49`, Certification `c80f6504`,
main `70d0f4fe`; PR más reciente #509 integrado, sin PR posterior de remediación.
Los 15 archivos de esta rama permanecen WIP local. Se reutilizan las validaciones
anteriores porque no se cambió código ni configuración desde su cierre.

La UI GitHub permitió leer la protección clásica Certification `76533723` después
del 403 del conector: PR obligatorio, 1 aprobación, dismiss stale, aprobación del
último push por otra persona, security-audit, rama actualizada y sin bypass; sin
force pushes/deletions/lock. No se guardó ningún cambio. Se preparó descripción
PR con plantilla completa (`/tmp/h3-certification-pr-body.md`) y propuesta de
autorizaciones (`/tmp/h3-certification-remaining-jit.md`). Se solicitaron por
separado commit/push/PR hacia Development y retirada exclusiva de Certification
del ruleset adicional preservando main y protección clásica. No se presumen
aprobadas; sin respuesta no se ejecutan ni implican merge/promoción.

**Resultado final local:** selector y guard de rutas remediados para preparar el
acumulado completo elegido por el responsable. Suite completa Docker **PASS**,
incluido helper de pins con modo/tipo/objeto. Ensayos sobre refs reales en evento
PR y push posterior a Certification **PASS**: guard de rutas, selección de cuatro
manifiestos, unión de 1.614 paths (incluye el manifest nuevo) y checker/self-test
747/747 fuentes. Scope agregado final SHA-256
`8823ab542c34aea5bafa40afd1de442c132cd3e605a91ce31660b6315afee1d0`.
Los ensayos usaron el clon con WIP superpuesto; no son CI de un commit publicado.
Scanner final de los 15 archivos **PASS** (`credentials-final.log`); evidencia
final revalidada **PASS** (`documentation-final-evidence.log`); `git diff --check`
PASS. Los dos logs están en el mismo directorio de resultados indicado debajo.
Logs finales: `regressions-final.log`, `protected-paths-remediated-final.log`,
`protected-paths-push.log`, `selector-push.log` y `documentation-push.log` en
`/tmp/h3-certification-final-results/`. La revisión focal independiente del último
delta no encontró HIGH/CRITICAL/MEDIUM. No se repitieron pruebas de producto.

Los controles normales conservan su comportamiento. Solo el primer push de
Certification desde baseline `c80…` puede consumir los pins fuente `941…`; no se
autoriza cualquier sucesor ni se cubre `main`. El FAIL integral permanece separado.
Faltan integración protegida de esta remediación (con CI/approval de su HEAD),
disposición o corrección del integral para promoción, hostname/Access/redirects,
verificación de restricciones de rama y autorización/smoke Certification. Es GO
local de los dos controles corregidos; **NO-GO de ejecución de promoción** aún.

Continuación autorizada por el responsable: «Remedia bloqueos que luna tenga para
promover a certificación». Rama aislada
`codex/h3req1-certification-remediation-20261028`, worktree
`/tmp/studiamatch-h3req1-certification-remediation-20261028`, base local integrada
`941eca496676bd11cd0e2796e6c0a34efd62082d`. Se copiaron los siete documentos de
Luna sin modificar su worktree ni convertir su WIP en commit. No hubo commit,
push, PR, merge, writes remotos ni deploy.

### Diagnóstico y corrección

- Fetch de lectura completado: ambos árboles existen. `git rev-list --left-right
  --count c80f6504a3ea353bc2c222df1da09c4b5ba0ae58...941eca496676bd11cd0e2796e6c0a34efd62082d`
  da **9/97**, no 1/97. El diff desde el ancestro común abarca **1.618 archivos**.
  Estos conteos corrigen el corte anterior; no autorizan una resolución automática
  de conflictos ni prueban por sí solos la compatibilidad del merge.
- Ensayo de lectura `git merge-tree <ancestro> c80… 941…`: sin secciones de
  conflicto ni marcadores. Los 9 commits exclusivos de Certification son merges;
  `git diff --name-status <ancestro> c80…` está vacío. Por tanto el árbol destino
  no incorpora un delta de contenido independiente respecto de ese ancestro.
  Esto reduce el riesgo de conflicto textual, sin acreditar runtime/CI.
- Existen cuatro selecciones documentales y **tres** scopes de paths PR en el
  diff de evidencia, no dos. El selector anterior confundía los tipos y rechazaba
  la pluralidad. El cambio local distingue el schema de paths PR únicamente en
  promoción y agrega las cuatro selecciones más el diff completo, con hashes.
  En PRs normales conserva la selección única y el rechazo de ambigüedad.
- Regresiones Docker sin red, candidato read-only:
  `bash tests/test_protected_path_scope_guard.sh` **PASS**, incluidas regresiones
  previas y nuevas de promoción: unión/cobertura, hashes, ausencia de input,
  schema PR inválido y rechazo de ambigüedad normal. Log local:
  `/tmp/h3-certification-selector-tests.log`. Hubo una primera corrida FAIL por
  import ausente del test; se corrigió y revalidó. No se atribuye CI remoto.
  Después se añadió un caso adicional y su guarda: corromper el JSON de un
  manifiesto con rol ya presente en baseline debe fallar aunque su basename sea
  genérico. Tras el reintento humano autorizado, la suite final completa **PASS**;
  log `/tmp/h3-certification-selector-tests-final.log`. La revisión estática del
  bloque final tampoco encontró hallazgos; no se ejecutó CI remoto.
- Revisión focal independiente `security-auditor` de workflow/test: sin hallazgos
  de seguridad reportables; lectura estática sin operaciones remotas. Confirmó
  alcance de ruta, unión/cobertura, hashes, rutas seguras y controles negativos.
  No sustituye el ensayo real ni los gates pendientes.
- El árbol Certification `c80…` **no contiene el checker documental actual**.
  Por ello no es válido afirmar «349 idénticos en baseline/candidato» para esa
  promoción ejecutando comandos nativos equivalentes. Los 349 se refieren al
  baseline Development/candidato de #509; la ausencia del gate antiguo debe
  registrarse en la evaluación del delta real sin inventar un PASS del baseline.

### Configuración remota verificada en lectura

Proyecto Pages real: `studiamatch`, subdominio `studiamatch-aty.pages.dev`.
`ADMIN_ALLOWED_HOSTS` de Preview contiene exclusivamente
`feat-h3req1-sync-20261002.studiamatch-aty.pages.dev` y
`desarrollo.studiamatch-aty.pages.dev`; falta el alias de Certification. El
inventario Access completo de cuenta (4 apps, una página) contiene el host Admin
productivo, un deployment Development antiguo y apps ajenas; **ninguno incluye
certificacion.studiamatch-aty.pages.dev**. Esto reemplaza «Access no verificado»
por «no hay aplicación Access que cubra ese host según inventario leído»; no se
modificó ninguna policy ni se leen identidades/secretos.

La lectura API de ruleset `21255108` confirma que sigue activa con regla `update`
para `certificacion` y `main`. Development fue retirado en la remediación #509.
La ruta normal de merge de Certification debe verificarse antes de abrir/promover
el PR: esa restricción adicional puede reproducir el bloqueo de #509. No se usó
bypass ni se cambió la regla; cualquier remediación de ramas protegidas requiere
su instrucción humana específica, preservando PR/review/checks clásicos.

Paquete remoto a aprobar separadamente: añadir únicamente el hostname
Certification a la variable Preview preservando los dos valores; definir la
cobertura Access del panel y BFF de Certification mediante una policy de cuentas
de prueba autorizadas (sin ampliar a todo el catálogo público ni bypass). Debe
comprobarse también el callback Auth del host y la compatibilidad del Free
compartido antes del deploy. Ninguna autorización SQL se solicita: las dos
migraciones ya están aplicadas. No copiar secretos ni provisionar nuevos por
inferencia. Rollback de configuración: retirar exclusivamente la entrada/recursos
añadidos mediante alcance JIT aprobado, conservando Development y producción.

### Gates pendientes y límite de la ejecución

Las pruebas E1–E6 y R1–R4 siguen 6/6 y 4/4; no se repitieron. No hay un defecto
funcional nuevo acreditado contra CA4. La prueba del selector sobre el delta real
pasó: **4 paquetes / 1.613 paths supervivientes**, baseline `c80…`, HEAD `941…`,
scope SHA-256 `27953739f85650ded346ae2539e5b3e001a4edcda36f84030b516e8efb00eb09`.
El clon contiene los cambios locales superpuestos, no un commit publicado nuevo.
Primera corrida: FAIL `REGISTRY_MARKDOWN_DRIFT`; se regeneró la vista Markdown
desde JSON, se copió al candidato y se revalidó: **PASS**, self-test PASS,
747/747 fuentes, 119/119 documentos activos y 433/433 históricos enlazados.
Log `/tmp/h3-certification-real-promotion-gate-rendered.log`. El agregado usa el
diff de los refs exactos y añade los paquetes completos; los documentos locales
se validan en el mismo árbol superpuesto. Se requiere CI del futuro HEAD para
declarar integración. Queda preparar/publicar el PR con autorización separada y
resolver configuración/promoción/smoke.
El FAIL integral no se convierte en PASS ni se extiende la disposición #509.

La preparación del clon desechable para el ensayo real fue detenida antes de
ejecutarse: auto-review informó «application network permission was revoked» y no
pudo completar la revisión. Es fallo del mecanismo de autorización, no un rechazo
por inseguridad ni defecto del producto. El responsable autorizó reintentar y la
aplicación aceptó los comandos; **incidencia de permiso superada**, sin intervención
adicional necesaria ni elusión. Clon local y Docker se completaron después. No se
declara GO de promoción por esos checks locales.

Se intentó también pytest focal de workflow/security: no ejecutado porque esta
imagen no tiene pytest. No se instalaron dependencias ni se etiquetó ese intento
como PASS; la suite shell/Node/Python propia del selector sí se ejecutó completa.

### Gate completo y decisión de alcance

El wrapper obligatorio en el clon final terminó candidate-aware **exit 0 / PASS**
y modo integral `--self-test` **exit 1 / FAIL**. El integral contiene los 349
diagnósticos heredados más `DOC_SELF_TEST_FAILED` por una fuente diagnóstica
registrada ausente: **350 entradas de fallo**, no una regresión funcional nueva.
El comando previo de comparación sin `--self-test` reportaba 349. Se conservan
ambos modos separados; logs y exits en `/tmp/h3-certification-final-results/`.
El scanner de los 12 archivos modificados pasó en Docker; `git diff --check` PASS.

El ensayo adicional del guard real con `RUNNER_TEMP=/tmp` y baseline `c80…`
terminó **FAIL**: `protected path changed outside allowlists`. La primera corrida
sin RUNNER_TEMP no reprodujo Actions y falló por variable ausente; el segundo
ensayo sí incluyó esa variable y conserva el fallo genuino. Log:
`/tmp/h3-certification-real-protected-paths.log`.

Se enumeraron 1.484 paths del conjunto protegido en el delta real. La comparación
con regex H3/H3-extra y lista exacta local identifica **239 paths fuera de esa
lista H3**: 145 bajo evidencia `h3-expanded`, 23 migrations, más fuentes/config y
documentos anteriores. Algunos tienen cobertura legacy independiente; el fallo
del guard completo demuestra que ese fallback tampoco admite el conjunto.
No se confunden «fuera de lista actual» con «nunca aprobados». Lista diagnóstica:
`/tmp/h3-certification-unadmitted-paths.json`. No se amplió ninguna allowlist.

Este hallazgo afecta al alcance acumulado, más amplio que el arreglo editorial.
El responsable eligió explícitamente «Revisar y preparar el acumulado completo
de Development hacia Certification». Esa decisión habilita su preparación local,
sin merge/SQL/configuración remota. Se agregó el manifest exacto de 239 paths
adicionales con blobs baseline/origen, consumido solo en la ruta de promoción.
El caller fija separadamente baseline `c80…` y origen `941…`; exige ancestry y
modo/tipo/objeto HEAD idénticos al origen en cada path adicional. No usa un patrón
de carpeta ni acepta contenido nuevo por editar el manifest. La entrada del
manifest se admite por nombre exacto para su integración a Development.

Regresiones del primer corte PASS: pins correctos, vecino no seleccionado,
baseline incorrecto, blob falso, duplicado y drift de contenido; log
`/tmp/h3-certification-full-regressions.log`. Guard sobre delta real con ese
manifest PASS: `/tmp/h3-certification-final-results/protected-paths-remediated.log`.
Revisión independiente focal del guard/manifest/tests: sin HIGH/CRITICAL/MEDIUM,
estática sin writes. El endurecimiento posterior de modo/tipo/objeto se incluye
en la revalidación final, cuyos logs quedan en
`/tmp/h3-certification-final-results/`. No se atribuye aprobación funcional de
todo el acumulado ni CI remoto por admitir rutas.

**NO-GO de promoción se mantiene** hasta integrar la remediación, resolver/disponer
el FAIL integral para el candidato exacto y preparar hostname/Access/redirects y
ruta protegida. No hay un nuevo desarrollo funcional de CA4 identificado; sus
pruebas Development permanecen aceptadas. La validación por ambiente en
Certification sigue pendiente. No repetir SQL ya consumido ni invitaciones.

## Preparación de promoción a Certification

**Resultado del corte:** NO-GO — 2026-10-28 18:54 America/Lima.

### Tareas, gates y estado observado

| Gate | Resultado | Evidencia / límite |
|---|---|---|
| Autoridad y WIP | Revisado; WIP conservado | Se leyó `AGENTS.md`, `.context/indice.md`, estado operativo y esta evidencia. Al retomar, el worktree era `/tmp/studiamatch-h3req1-public-price-projection-20261028`, rama `codex/h3req1-public-price-projection-20261028`, HEAD `2b1f533444dab19528d5cb3d912ef6332dc20c41`; estaban modificados localmente estado/evidencia. Ese SHA es HEAD feature de #509, no el merge de desarrollo. El diff documental final se acotó a estado, checkpoint, atestación sanitizada, índice, ficha, navegación de hitos y matriz HITO-003. No se hizo fetch, cambio de rama, reset, commit ni publicación. |
| Promoción Git | NO-GO | Origen remoto confirmado: `desarrollo@941eca496676bd11cd0e2796e6c0a34efd62082d`. Destino: `certificacion@c80f6504a3ea353bc2c222df1da09c4b5ba0ae58`. Ancestro común `a6e39b993b2609641d20e9e24c513f35fd711b96`; Desarrollo tiene 97 commits desde ese ancestro y Certification conserva un commit. La promoción acumula cambios anteriores, no solo #508/#509. El objeto de merge `941…` no existe en este checkout, así que el candidato de promoción no fue reconstruido localmente. |
| PR #509 / CI | Evidencia reutilizada, no CI de promoción | #509 está integrado. Su HEAD `2b1f533444dab19528d5cb3d912ef6332dc20c41` recibió aprobación humana; CI de ese HEAD: 16 `success`, 2 `skipped` (`Supabase Preview`, `H2 Main Production Expand Gate`). Esos checks pertenecen al PR #509 y no acreditan el futuro PR a Certification ni el merge SHA. Ambas ramas reportan protegidas; los requisitos detallados de Certification no estuvieron disponibles por la lectura actual. No se usará bypass. |
| Pages | Deployment de Certification obsoleto frente al origen | Development sirve `https://desarrollo.studiamatch-aty.pages.dev`, deployment `87a65f76-b341-4e7c-9e50-ae5f3aa497f2`, `success`, SHA `941…`. Certification sirve `https://certificacion.studiamatch-aty.pages.dev`, deployment `3b28949c-7dfe-4b54-bf7a-0db77339d6ab`, `success`, SHA `c80…` (2026-08-28). El Preview de PR es distinto del deployment de rama. No se pidió ni hizo deploy manual. |
| Free / schema | Compatible; sin SQL pendiente para Certification | Development y Certification comparten Free `aqrldlmlszjtgpqiegaa`; estado `ACTIVE_HEALTHY`, PostgreSQL 17.6.1.166, ledger 83. Incluye `20261028194353` (`20261028_h3_editorial_publication_snapshot`) y `20261028230928` (`20261028_h3_public_price_projection_empty_price_guard`). No reaplicar, backfill ni cambiar datos. Pro es separado y queda fuera de esta etapa. |
| Configuración del hostname | BLOQUEANTE; JIT faltante | La configuración Preview de Cloudflare es compartida por las ramas no productivas. El `ADMIN_ALLOWED_HOSTS` observado contiene el alias feature y `desarrollo.studiamatch-aty.pages.dev`, pero no `certificacion.studiamatch-aty.pages.dev`. No se leyeron valores secretos ni se modificó configuración. El acceso Cloudflare Access para el host de Certification no quedó verificado. |
| Evidencia Development | ACEPTADA, solo en ese ambiente | E1–E6 local: 6/6; R1–R4 remoto Development: antes 2/4, después 4/4 (+50 pp). No son porcentajes globales de H3REQ1 ni prueba de Certification. R2/R3 restauraron y republicaron el `benefits` original; el público quedó sin marcador. |
| Gate documental | BLOQUEANTE sin resolución | El candidate-aware de #509 pasó 747/747 en su propio baseline/candidato. El checker integral de esa comparación falló con 349 diagnósticos en cada lado; 348 iguales, y el único delta reportado fue `INTEGRATION_PROJECTION_CANDIDATE_ONLY_COUNT` 299→304 frente al esperado 367. Ese contraste no es c80→941. La disposición humana cubre solo #509 y expira antes de Certification. |

### Diagnóstico documental aplicado al alcance de promoción

El workflow `.github/workflows/security-audit.yml` selecciona archivos JSON por el nombre basename que contiene `candidate` y `scope`/`manifest`, o por rol `candidate-aware documentation integrity selection`; exige una única selección válida contra `PROTECTED_BASELINE_SHA`. En el delta remoto observado c80→941 aparecen seis archivos: dos `candidate-pr-scope` no tienen el schema (`manifest_role`, `scope.entries`, `package_artifacts`) y detonan `changed candidate-aware documentation manifest has an invalid structure`; cuatro manifests documentales válidos detonan `multiple candidate-aware documentation manifests changed; selection is ambiguous`. Este es un fallo reproducible por la regla actual del selector, no una atribución a los 349 diagnósticos heredados.

La corrección mínima no es eliminar manifests ni reducir alcance: construir un manifest agregador de promoción para el delta completo y adaptar el selector para elegirlo de forma explícita y validar que cubre la unión de los paquetes/manifests afectados, conservando todos los controles. Eso cambia el workflow/gate y requiere un PR focal a `desarrollo`, checks y aprobación propios. No está implementado ni autorizado por esta preparación. Hasta obtener los árboles c80 y 941 juntos tampoco se puede emitir una comparación integral exacta para Certification.

La regla operativa exige PR protegido a la rama destino, aprobación y el check de seguridad requerido; `AGENTS.md` además exige el self-test documental antes de integrar. No se encontró una regla que convierta un candidate-aware PASS de #509 en disposición del FAIL integral. Por ello la disposición #509 no se extiende: para Certification se requiere reconciliar el integral o presentar una disposición humana nueva, limitada al candidato exacto, después de obtener sus logs baseline/candidato. Riesgo residual de la disposición: fuentes y referencias históricas continuarían sin reconciliarse; owner propuesto: Romel/TL de documentación; caducidad propuesta para decisión: antes de promoción a `main` y no después del 04/11/2026 23:59 America/Lima. Esto es una propuesta, no una aprobación ni un waiver vigente.

**Validación Docker de esta actualización documental — 2026-10-28 18:58 America/Lima:** `git diff --check` PASS. Con `node:22-bookworm-slim`, red deshabilitada, mount read-only y el manifest `h3req1_editorial_contract_candidate_scope_2026-10-28.json`, `--self-test --candidate-manifest` PASS: 747/747 fuentes asignadas, 0 diagnósticos del gate; grafo 119/119 docs activos alcanzables, 433/433 históricos enlazados. El checker integral, mismo comando/configuración sin manifest, terminó exit 1 tanto en `git archive HEAD` (baseline local `2b1f533`) como en el worktree candidato: 349 diagnósticos cada uno, diff de líneas `DOC_GATE_FAIL` vacío; contador de proyección candidate-only 304 en ambos. El grafo subió de 9.334 a 9.339 enlaces y de 4.675 a 4.677 anchors por esta actualización; los anchors agregados se revalidaron. Logs reproducibles: `/tmp/h3req1-promotion-prep-20261028/logs/baseline.log` y `candidate.log`. Esto demuestra que los documentos locales no añaden diagnósticos sobre HEAD `2b1f`; no es el contraste de promoción `certificacion@c80… → desarrollo@941…` ni un PASS integral.

Después se actualizaron los resúmenes subordinados de HITO-003 para que el 5/6 histórico de E1–E6 y el estado R178 no parezcan actuales. La pasada final en Docker volvió a validar esos cambios; el candidate-aware sigue PASS y el integral conserva los 349 diagnósticos sin delta frente al baseline local. El paquete conserva NO-GO para el gate integral y la comparación exacta de promoción sigue pendiente.

**Conteos de la revalidación documental final:** candidate-aware PASS, 747/747 fuentes asignadas, 0 diagnósticos, 119/119 documentos activos alcanzables, 433/433 históricos enlazados; grafo 9.343 enlaces/4.679 anchors. Checker integral exit 1, 349 diagnósticos; diff `DOC_GATE_FAIL` baseline local/candidato vacío. Logs finales: `candidate-aware.log`, `baseline.log`, `candidate.log` en `/tmp/h3req1-promotion-prep-20261028/logs/`. Sigue sin ser un gate integral PASS ni una comparación c80→941.

En una corrida intermedia después de resumir HITO-003, el candidate-aware detectó tres `DOC_ORPHAN` (reporte de implementación, revisión de cierre y waiver enlazado transitivamente) porque se habían retirado los enlaces del índice de hitos. Se restauraron los dos enlaces históricos existentes; la corrida final documentada arriba pasó con 119/119 activos alcanzables. No se borró ni alteró la evidencia histórica.

### Matriz breve de CA vigentes y acción mínima

El backlog vigente asigna HITO-003 al criterio cliente `H3-CA4`. Los subcriterios `.1–.11` de la ficha son su descomposición interna histórica; la tabla no crea criterios nuevos ni porcentajes globales.

| CA | Evidencia reutilizable | Estado demostrado | Acción mínima para Certification |
|---|---|---|---|
| `H3-CA4` (panel editorial) | E1–E6 local 6/6; R1–R4 Development 4/4; atestación humana CA4 | ACEPTADO en Development; PENDIENTE en Certification | Destrabar gate documental y hostname; después verificar la ruta desplegada y ejecutar el smoke acotado del contrato. |
| `H3-CA4.1` Auth/RBAC | D01/D02/D06 y aceptaciones humanas de límites; R1/R3 con roles existentes | ACEPTADO en el alcance mínimo de Development | Reutilizar; en Certification validar acceso por el host nuevo y límites de rol solo si el smoke lo toca. |
| `H3-CA4.2` allowlist editorial | Implementación/E1 local; `benefits` poblado en R1–R3 Development | ACEPTADO para el contrato en Development; no es prueba remota exhaustiva de los 13 campos | Un campo poblado representativo; no repetir matriz de 13 campos. |
| `H3-CA4.3` transporte/RPC y controles | Evidencia de seguridad/RPC/cuotas aceptada previamente; no hubo cambios de este contrato en la aceptación | ACEPTADO por evidencia reutilizada, con el alcance/límites históricos | No repetir si código e inputs del transporte permanecen iguales; comprobar solo el BFF en el host de Certification. |
| `H3-CA4.4` cola | MIN-01 aceptado en la pasada mínima anterior | ACEPTADO para Development | Una consulta de pendientes por la sesión autorizada en el smoke de Certification; sin paginación/carga ampliada. |
| `H3-CA4.5` mutaciones | E1–E5 local; R1 edición, R2 borrador aislado del público y R3 publicación efectiva | ACEPTADO en Development | Smoke representativo con JIT y recuperación exacta; no repetir E1–E5 localmente. |
| `H3-CA4.6` auditoría | D09 aceptado; auditoría/versionado en E1/R1/R4 y eventos de la pasada remota | ACEPTADO en Development dentro del alcance verificado | Confirmar que el smoke de Certification deja evento visible a Admin; no repetir auditoría general. |
| `H3-CA4.7` MFA/`aal2` | Decisión humana previa lo dejó fuera del gate | FUERA DE GATE; no pendiente | Ninguna prueba o cambio de factor. |
| `H3-CA4.8` membresías | Aceptación humana del onboarding real y permisos básicos reutilizados | ACEPTADO en el recorrido aceptado; no se repite onboarding | Usar membresía existente; no enviar invitaciones ni cambiar roles. |
| `H3-CA4.9` hostname/Access | Host Development desplegado; deployment Certification antiguo. Allowlist Preview sin alias Certification; Access no verificado | PENDIENTE | Lectura/policy preflight; JIT específico para añadir el alias preservando entries actuales; luego smoke del BFF y la protección. |
| `H3-CA4.10` convergencia | Free compartido; ledger con ambas migraciones H3 | ACEPTADO para Development/Certification en el schema Free; Pro fuera de alcance | No aplicar SQL a Certification; cotejar Pro solo en una futura etapa de producción. |
| `H3-CA4.11` UAT/artefactos | E1–E6 locales 6/6; R1–R4 Development 4/4 | ACEPTADO local y en Development; PENDIENTE por ambiente en Certification | Smoke mínimo tras el PR/deployment; evidence específica del alias y SHA efectivos. |

### Paquete y secuencia sin ejecutar

- **Origen/destino:** `desarrollo@941eca496676bd11cd0e2796e6c0a34efd62082d` → `certificacion@c80f6504a3ea353bc2c222df1da09c4b5ba0ae58`. El delta amplio de 97 commits requiere revisión del PR completo; no está aislado a H3REQ1.
- **CI/protecciones:** #509 quedó aprobado y 16 checks success/2 skipped en su HEAD. Ambas ramas aparecen protegidas; detalle de reglas para Certification no verificado. No hubo CI/approval del futuro PR ni bypass.
- **Expand:** schema editorial y guard de precio ya aplicados una vez a Free compartido, versiones `20261028194353` y `20261028230928`; no hay migración Certification separada.
- **Compatibilidad:** mantener snapshots nullable, fallback para cursos sin snapshot, auditoría append-only y comportamiento legacy; no backfill ni contracción antes de estabilización.
- **Deploy:** abrir el PR protegido y dejar que el despliegue normal de rama genere el deployment Certification. No hacer build/deploy manual. Antes se necesita corregir el selector documental y resolver el host allowlist.
- **Contract:** solo tras estabilidad y aceptación autorizada; retirar el fallback legacy mediante delta revisado aparte. No contraer en esta preparación.
- **Rollback:** detener/retirar el código de app mediante PR revert protegido; conservar columnas, snapshots, cursos y auditoría. Si el cambio de allowlist se autoriza y falla, restaurar el valor anterior de `ADMIN_ALLOWED_HOSTS` según su JIT; no borrar datos ni revertir la migración aplicada.
- **Smoke mínimo propuesto:** comprobar deployment/SHA del alias; Admin existente consulta pendientes; colaborador con membresía existente corrige un campo poblado y el público mantiene el snapshot hasta publish; Admin publica; visitante sin sesión ve el valor exacto; historial/version/preview siguen operativos; restaurar y republicar el original incluido en el JIT. No repetir invitación/onboarding, cuotas ni los 14 escenarios. Como Free es compartido, el paquete JIT debe declarar el efecto de cualquier escritura sobre lectores de Development y Certification.

### Acciones no ejecutadas y autorizaciones necesarias

No se hicieron cambios remotos, commit, push, PR, merge, SQL, Auth, Access, configuración Cloudflare, workflow, deploy ni prueba de negocio en Certification. La autorización previa de #509 se consumió y era para otro destino.

1. **Autorización local de preparación de CI/manifiesto y documentación:** el selector necesita una corrección focal con PR a `desarrollo`; esta sesión solo deja diagnóstico. Se requiere instrucción para implementar y validar ese delta. La integración de los docs de aceptación que siguen sin commit también requiere autorización específica de commit/push/PR en una rama basada en SHA `941…`.
2. **JIT Cloudflare Preview:** solo cambiar `ADMIN_ALLOWED_HOSTS` para conservar los valores actuales e incluir `certificacion.studiamatch-aty.pages.dev`; confirmar la aplicación a Preview compartido, efecto en previews y recuperación al valor anterior. Sin modificar secretos, Access policies u otros bindings.
3. **Autorización de promoción:** abrir PR protegido `desarrollo → certificacion` tras resolver los gates, y posteriormente autorización separada de merge; no cubre SQL ni configuración.
4. **JIT de smoke Certification:** un curso/campo/fixture existente y valor de prueba/recovery exactos, roles existentes, lectura anónima, efecto visible debido al Free compartido y republicación restauradora. No reutilizar el JIT Development.

**Decisión de este corte:** NO-GO para solicitar/ejecutar la promoción; sí se completó el diagnóstico y el paquete local de preparación. No hay GO de Certification ni de producción. Hora inicial de esta continuación no quedó registrada al retomar el hilo; corte de verificación local: 2026-10-28 18:54 America/Lima.

## Addendum final — R2/R3 aceptadas y recuperación verificada — 2026-10-28

**Verificación de navegador terminada:** 18:33:18 America/Lima. **Checkpoint
documental cerrado:** 18:34:31 America/Lima. Esta continuación retomó el
checkpoint de las 18:19; la hora exacta de inicio de la sesión del navegador no
quedó expuesta por el puente. Ambiente Free/Development `aqrldlmlszjtgpqiegaa`,
host `desarrollo.studiamatch-aty.pages.dev`, deployment `27d9ebfc`, SHA integrado
`941eca496676bd11cd0e2796e6c0a34efd62082d`. PR #509 permanece integrado. La
migración correctiva de precio ya estaba aplicada una vez bajo su JIT separado:
`20261028230928`, 83 entradas de ledger; no se reejecutó ni se hizo otro cambio
de schema.

### Matriz remota R1–R4

Denominador fijo: 4. Antes de esta pasada: **2/4 = 50%** (R1/R4 aceptados;
R2 había fallado por `22P02`; R3 pendiente). Después: **4/4 = 100%**, delta
**+50 puntos porcentuales**. Se conservan separados los resultados históricos y
el arreglo posterior.

| ID | Resultado de esta pasada | Evidencia nueva / reutilizada |
|---|---|---|
| R1 | ACEPTADO, reutilizado | Edición de colaborador sobre campo poblado, persistencia tras recarga y auditoría de la pasada anterior; inputs/contrato no cambiaron. |
| R2 | ACEPTADO | En page 6 (Chrome Windows, contexto aislado de colaborador), curso ID `fd47da34-4a65-4a71-bc49-aea6db713500`, publicado v8 y `benefits` original. Colaborador guardó el marcador en v9 y recargó. Antes de publicar, page 3 anónima mostró únicamente los cuatro elementos originales; el marcador no se filtró. La lectura `courses_public_effective` respondió 200. |
| R3 | ACEPTADO | Admin publicó el borrador con marcador; tras recargar page 3 anónima, “Qué Incluye” mostró el texto exacto `* [H3REQ1 CA4 — verificación temporal 2026-10-28]` junto a los cuatro elementos originales. El preview Admin indicó “Curso publicado”; la versión avanzó a v10. |
| R4 | ACEPTADO, reutilizado | Historial/versión compacta y preview borrador/publicado aceptados en la pasada previa; no se repitió ese criterio. En esta ejecución el contador de historial llegó a 12 después de guardar/publicar y restaurar/publicar, compatible con registro append-only. |

### Restauración, efectos y recuperación del lector

- El mismo JIT exacto de R2/R3 incluyó restauración. Colaborador guardó el
  `benefits` original, SHA-256
  `0e0e139a5b59153b2fc219d618ae57d4f2903a3a7e0e516b6fe62dbb81a8741f`, y recargó:
  versión v11, borrador original, preview publicado todavía con el marcador y
  aviso de diferencia. Admin republicó el original; versión v12, estado
  Publicado y preview publicado sin marcador.
- La última recarga anónima de page 3 mostró exactamente los cuatro beneficios
  originales, sin el marcador. Network del mismo curso: GET a
  `courses_public_effective` HTTP 200 (reqid 144 en la captura MCP final); la
  lectura de recomendaciones también respondió 200. No volvió a aparecer
  SQLSTATE `22P02`.
- Efectos persistentes limitados al curso/campo autorizados: dos ediciones de
  contenido y dos publicaciones, con versiones v9–v12 y eventos auditados. El
  texto público final quedó restaurado a su valor previo. No se tocaron otros
  campos, disponibilidad, membresías, cursos adicionales, pipeline, FG3,
  schedules, deployments, Pro ni Certification como ambiente de promoción.
- No hubo una nueva espera humana: la intervención Admin y el acceso previo del
  colaborador se completaron en sus sesiones Chrome existentes. No se solicitaron
  credenciales ni códigos.

### Resultado y gates restantes

GO de aceptación remota mínima del contrato corregido en Development: **SÍ**,
limitado a R1–R4 (4/4). No equivale a GO de promoción, producción ni cierre total
de H3REQ1. El FAIL integral del checker documental (349 diagnósticos heredados)
permanece visible; el PASS candidate-aware y la disposición humana exclusiva
para PR #509 siguen separados. Esa disposición es del owner Romel y vence el
04/11/2026 23:59 America/Lima o antes de promover a Certification, lo que ocurra
primero; no es un waiver global ni una aprobación de promoción.

Siguiente acción exacta: antes de cualquier promoción a Certification, resolver
o disponer el gate documental integral por el proceso humano aplicable y obtener
las autorizaciones específicas de promoción. No aplicar otra migración, no probar
remotamente en Certification/Pro y no ejecutar writers/schedules en este corte.

## Addendum — corrección SQL aplicada y lector público recuperado; R2/R3 pendientes — 2026-10-28

**Corte:** 18:19 America/Lima. En el Free compartido
`aqrldlmlszjtgpqiegaa` se aplicó una vez, con JIT exacto, la migración integrada
`db/migrations/20261028_h3_public_price_projection_empty_price_guard.sql`
(SHA-256 `82b8eb0655779f0e82b979cb65a051f2b244b5c4bffb199c5e13c9473132987b`).
Ledger confirmado: versión `20261028230928`, 83 entradas; no se reejecutará.
Verificación de solo lectura: `private.h2_public_courses_effective()` mantiene
`SECURITY DEFINER`, `search_path=pg_catalog, pg_temp`, EXECUTE para
`anon`/`authenticated`/`service_role`, sin EXECUTE para `PUBLIC`; la guarda segura
está presente y el cast numérico directo ya no aparece. La vista
`public.courses_public_effective` sigue como `security_invoker`, llama al helper y
permite SELECT a `anon`/`authenticated`.

En Chrome Windows, contexto anónimo aislado, la ruta del mismo curso IDAT ahora
carga y la request a `courses_public_effective` devuelve HTTP 200. El catálogo
detallado muestra “Python for Data Analyst” y el `benefits` aprobado original, con
sus cuatro elementos; no se volvió a observar `22P02`. Esto prueba recuperación
del lector público, pero no completa R2 sin la edición de borrador controlada.
Estado R1–R4 se conserva en 2/4 (50%) en este corte: R1/R4 aceptados, R2 aún
pendiente de revalidación tras el arreglo y R3 pendiente. La pasada anterior con
2/4 queda como antecedente; no se convierte el error histórico en PASS ni se repiten
R1/R4.

No se escribieron cursos ni se cambió pipeline, cuenta, disponibilidad, despliegue
o Pro. Tras completar el acceso en Chrome Windows, página 6, el editor confirma
curso publicado/completo, versión v8, `benefits` igual al original y los mismos
cuatro elementos en preview público. La página Admin 1 sigue en login; a las 18:14
se pidió al responsable completar acceso Admin. Se preparó y envió JIT nuevo para
R2/R3 y recuperación exacta; está pendiente y ninguna escritura de curso se ha
realizado bajo ese paquete. Siguiente paso: verificar el estado Admin después de la
intervención, esperar el JIT y luego ejecutar solo R2/R3 más la republicación del
original. Este corte se detiene a las 18:19 sin tratar la espera de intervención ni
la autorización pendiente como defecto técnico.

Validación documental local: `git diff --check` pasó. El self-test del checker de
integridad ejecutado en Docker efímero sin red y con worktree read-only terminó
FAIL (código 1), con 747/747 fuentes asignadas y errores de rutas/referencias
históricas; el FAIL integral de 349 diagnósticos y la disposición limitada a #509
siguen visibles, no se alteraron relaciones ni se declaró PASS. El wrapper de imagen
intentó inicializar `node_modules` y falló por volumen fuera de sincronía; el checker
sin dependencias externas se ejecutó directamente en el mismo contenedor aislado.
No se ejecutó un gate candidate-aware nuevo para este addendum documental.

## Addendum post-merge y aceptación remota R1–R4 — 2026-10-28

**Continuación retomada:** 14:50:14 America/Lima. **Corte remoto R1–R4:**
2026-10-28, desde 14:50 hasta 15:07 America/Lima. El arreglo posterior se prepara
en el worktree separado `codex/h3req1-public-price-projection-20261028`; su gate
local/documental y publicación se registrarán en un addendum final. Se conserva
debajo la historia previa sin cambiar sus resultados.

### Integración, deployment y schema verificados

- PR #508: `https://github.com/romelhc95/studiamatch/pull/508`; aprobado sobre
  `85e9d1b17ca2808ed320ba2c37d893fbf7619dad`, merge en `desarrollo`:
  `77b3f4ea27a8aaa6d1d0571ee5a9b5f1afd264a3`, 2026-10-28 12:39:06
  America/Lima. El head tuvo 16 checks `success` y 2 `skipped`.
- Checkout de evidencia preservado: `/tmp/studiamatch-h3req1-editorial-contract-20261028`,
  rama `codex/h3req1-editorial-contract-20261028`, HEAD local aprobado
  `85e9d1b17ca2808ed320ba2c37d893fbf7619dad`. No se cambió a `desarrollo` ni se
  modificó código; únicamente están modificadas localmente las tres fuentes
  documentales de este corte, sin commit/push.
- Deployment de rama Development: Pages `27d9ebfc-1ff4-4c43-b58f-117d98977cd0`,
  rama `desarrollo`, SHA `77b3f4ea27a8aaa6d1d0571ee5a9b5f1afd264a3`, etapa
  `success`, alias `https://desarrollo.studiamatch-aty.pages.dev`. No confundir
  con el Preview de PR `920821c9-5fdb-4dbb-94d6-6dc1b9e840af`, que corresponde a
  la rama feature y tiene alias propio. No se hizo deploy manual.
- Supabase Free/Development `aqrldlmlszjtgpqiegaa` (instancia compartida con
  Certification): preflight mostró 81 entradas
  de ledger, sin la migration y con columnas/RPC/vista bajo el contrato anterior.
  JIT exacto aprobado y consumido: una aplicación de
  `db/migrations/20261028_h3_editorial_publication_snapshot.sql`, SHA-256
  `2c2bd2238f03a1b5bec2d47fb4bc8a9f0fe1650501378a8ff2dde8746b2a0fef`.
  Ledger posterior: 82 entradas; versión `20261028194353`,
  2026-10-28 14:43:53 America/Lima. Postcheck: tres columnas snapshot nullable,
  dos checks validados, firmas/RPC/helper esperados, `security_invoker` en la vista
  pública y grants acordes; ejecución Admin negada a `anon` y permitida a
  `authenticated`/`service_role`. Se comprobó la proyección/shape, sin leer datos de
  otros cursos. Efecto persistente: solo schema, funciones, grants y ledger; sin
  backfill ni escritura de filas de cursos. El schema queda compartido con
  Certification por el proyecto Free; no hubo una operación separada contra un
  ambiente Certification. No repetir la migración.
- La discrepancia app/schema detectada antes de migrar quedó resuelta según el
  contrato verificado; no fue necesario un redeploy. No se operó Pro, Certification
  como destino, escritores, pipeline, FG3, schedules ni promoción.
- Integridad documental: permanece el FAIL integral histórico de 350 diagnósticos
  (349 comunes entre baseline/candidato) y, por separado, el PASS candidate-aware
  exacto del paquete. El merge no dispone ni convierte el FAIL integral en PASS;
  owner de reconciliación/disposición: TL/documentación. No se borraron relaciones
  ni se fabricó evidencia.

### R1–R4: matriz remota antes/después

Denominador fijo: 4. Antes de la pasada había **0/4 criterios aceptados con
evidencia remota del contrato corregido**. Después hay **2/4 = 50%**, delta
**+50 puntos porcentuales**. Las evidencias E1–E6 locales y la pasada MIN-01..06
anterior no se cuentan en esta matriz.

| ID | Criterio | Antes de la pasada | Después de la pasada actual | Tipo y evidencia |
|---|---|---|---|---|
| R1 | Colaborador corrige campo poblado, guarda, recarga y persiste. | PENDIENTE; sin ejecución de este contrato en el deployment integrado. | ACEPTADO. | Ejecución remota 2026-10-28. En editor colaborador se cambió `benefits`, guardó (toast correcto), v6→v7 y recargó; marcador exacto persistió. |
| R2 | Antes de publicar, visitante anónimo conserva el último snapshot aprobado. | PENDIENTE; sin ejecución de este contrato en el deployment integrado. | FALLÓ. | Ejecución remota 2026-10-28. Preview editorial conservó snapshot, pero ruta anónima dio HTTP 400/SQLSTATE `22P02` antes de renderizar. |
| R3 | Admin publica y visitante sin sesión ve el valor exacto nuevo. | PENDIENTE; sin ejecución de este contrato en el deployment integrado. | PENDIENTE. | No se publicó el marcador porque R2 reveló que la proyección pública está fallando; la acción aprobada no se consumió para exponer un cambio no verificable. |
| R4 | Historial/versión y preview distinguen borrador/publicado. | PENDIENTE; sin smoke remoto de este deployment. | ACEPTADO. | Ejecución remota 2026-10-28: diferencia draft/published visible, 8 eventos consultados, disclosure inicialmente cerrado y operable con teclado; insignia v8 32,6 × 26,1 px. |

- El JIT de prueba cubrió un único curso IDAT, `benefits`, la membresía colaborador
  existente, Admin existente y visitante aislado. La publicación de la marca solo
  habría ocurrido tras verificar R2; como la lectura anónima falló, no se hizo. El
  paquete cubrió la recuperación exacta, auditoría append-only y ningún otro campo,
  disponibilidad, membresía/rol, SQL, pipeline, FG3, schedule, deploy o promoción.
- Preflight UI sanitizado: `Python for Data Analyst`, ID
  `fd47da34-4a65-4a71-bc49-aea6db713500`, publicado, completo, versión v6. El
  campo `benefits` del snapshot y del preview publicado coincide con el original
  aprobado (SHA-256 `0e0e139a5b59153b2fc219d618ae57d4f2903a3a7e0e516b6fe62dbb81a8741f`).
  La página anónima aislada muestra esos mismos cuatro beneficios antes del cambio.
  No se exponen datos de la cuenta colaboradora.
- Páginas de Chrome Windows: Admin página 1; visitante anónimo página 5; colaborador
  en página 6 de contexto aislado. La página 6 se enfocó con `bringToFront:true`; el
  responsable completó login. El editor mostró rol colaborador y no ofreció
  publicación ni administración de miembros. No se reinició onboarding/login.
- R1: el marcador literal fue
  `* [H3REQ1 CA4 — verificación temporal 2026-10-28]`; razón guardada
  `Validación temporal CA4 H3REQ1; restauración inmediata conforme JIT aprobado 2026-10-28.`
  El guardado desde DOM `fill` no habilitó el botón por el estado React; se repitió
  el mismo valor con interacción de teclado. Una primera entrada de razón tampoco
  habilitó el estado y no generó escritura; se completó con teclado y se verificó
  antes de guardar. El valor del marcador persistió después de recargar.
- R2: el lector público mostró el error funcional genérico de conexión. Network del
  pageId anónimo registró request `82`, status 400, body saneado:
  `{"code":"22P02","message":"invalid input syntax for type numeric: \"\""}`.
  Después de la recuperación, una sola comprobación del mismo lector registró
  request `116`, status 400 con el mismo error. No se consultó la fila operativa ni
  otros cursos. La probable causa está en la migración integrada, que hace cast
  directo de `published_editorial_values.price_pen` a NUMERIC cuando la propiedad
  está presente; la fila exacta que lo dispara no se verificó y no se afirma.
- Recuperación: el colaborador volvió a guardar exactamente el original de `benefits`
  (SHA-256 `0e0e139a5b59153b2fc219d618ae57d4f2903a3a7e0e516b6fe62dbb81a8741f`),
  con razón `Restauración del valor original aprobado; recuperación de la verificación H3REQ1 conforme al JIT 2026-10-28.`; v7→v8. Admin comprobó v8 publicado y preview igual al original. No se despublicó: UI no mostró botón publicar al no existir diferencia entre borrador y snapshot. El público no confirmó la recuperación por el error de lectura; no hubo marcador público.
- R4: disclosure de `Historial de auditoría 8` inició cerrado. Al abrir se verificaron
  los 8 eventos disponibles, incluidas las dos escrituras y la publicación histórica;
  IDs de actor omitidos/sanitizados. Se cerró con Space y no quedaron eventos
  desplegados. Preview mostró snapshot publicado y advirtió que un borrador posterior
  requeriría publicación Admin. Insignia `Versión editorial 8`: 32,6 × 26,1 px.
- Acciones persistentes: dos ediciones autorizadas en `benefits` (marcador y
  restauración), dos eventos/aumentos de versión append-only; no se publicó el
  marcador ni se alteró disponibilidad/estado de curso. El JIT de prueba queda
  consumido. La migración inicial también queda consumida; no cubre la corrección.
- No hubo corrección remota, nuevas consultas a la DB, deploy, ni promoción. GO
  Development: **NO**. R1/R4 aceptados; R2 falló y R3 sigue pendiente. Las rutas
  públicas continuaron fallando por el error de tipo tras restaurar el contenido.
- El checkpoint siguiente documenta el paquete correctivo local y su contraste
  documental. R1–R4 no se repiten con este arreglo; una nueva pasada remota necesita
  un deployment compatible y JIT exacto independiente.

## Addendum — corrección de proyección pública y gates locales

**Continuación:** retomada desde el checkpoint a las 15:21:49 America/Lima;
reanudada para cerrar el PR a las 16:04 America/Lima; edición documental cerrada
localmente a las 16:07 America/Lima. El entorno es
`codex/h3req1-public-price-projection-20261028`, basado
en el merge `77b3f4ea27a8aaa6d1d0571ee5a9b5f1afd264a3`. No se cambió el deployment
Development `27d9ebfc` ni el proyecto Free `aqrldlmlszjtgpqiegaa`.

### Corrección implementada

- La request anónima 82 del smoke R2 falló en la vista efectiva con SQLSTATE
  `22P02` por convertir texto vacío de precio a `NUMERIC`. La fila real no se leyó;
  el vínculo entre el error y el cast integrado está respaldado por el error y la
  definición SQL, pero el contenido exacto de la fila sigue sin verificarse.
- `db/migrations/20261028_h3_public_price_projection_empty_price_guard.sql`
  reemplaza un único fragmento dentro de
  `private.h2_public_courses_effective()`. Solo admite texto decimal con hasta 63
  dígitos enteros y 63 fraccionarios; vacío, formato no decimal y texto mayor se
  proyectan como `NULL`. Valida existencia y ocurrencia exacta; aborta ante drift.
  SHA-256 del archivo integrado: `82b8eb0655779f0e82b979cb65a051f2b244b5c4bffb199c5e13c9473132987b`.
  Reafirma ACL actuales del lector. No toca cursos, snapshots, disponibilidad ni
  auditoría. Se aplicó dos veces únicamente en la base sintética PG17.
- El baseline sintético reprodujo `22P02` antes del guard. La versión corregida pasó
  con ocho filas: vacío, decimal normal, JSON null, texto inválido, decimal de
  63 dígitos, 131073 dígitos que exceden el rango, precio editorial sin snapshot y
  fallback de source legacy. También verificó grants anon/authenticated/service,
  ausencia de `PUBLIC EXECUTE`, `SECURITY DEFINER` y `search_path`.
- El test Python focal pasó `1 passed`; `bash -n` y ShellCheck `0.11.0` pasaron
  sobre el runner final. El primer ShellCheck detectó `SC2034` en el contador de
  readiness; el bucle se cambió a `_` y la revalidación pasó. El binario no existía
  en la imagen de desarrollo; se usó la imagen `koalaman/shellcheck:v0.11.0` ya
  presente localmente, sin red. Sin build frontend: el delta es exclusivamente SQL,
  harnesses y documentación.
- La migración correctiva no se aplicó a Supabase, y no se hizo deploy, publicación
  de curso ni otra prueba funcional remota. No hay nuevos efectos persistentes fuera
  de los commits/documentos locales. La migration requiere revisión y JIT remoto
  nuevo; la pasada R1–R4 anterior quedó consumida.

- Revalidación local de esta continuación: el harness PG17 volvió a pasar con ocho
  fixtures y dos aplicaciones de la migration; `tests/test_h3_public_price_projection_migration.py`
  pasó 1/1 en Docker; ShellCheck 0.11.0 pasó con `-x -P /src`; `actionlint` 1.7.12
  pasó el workflow; la regresión `tests/test_protected_path_scope_guard.sh` pasó con
  positivos y vecinos negativos; `git diff --check` pasó antes y después de este
  update. El checker candidate-aware R21/self-test se ejecutó
  otra vez en Docker después del último cambio documental y pasó: 747/747 fuentes
  asignadas, 119/119 docs activos alcanzables, 433/433 históricos enlazados, cero
  diagnósticos. El intento inicial de invocación ShellCheck omitía `-x` y dio
  únicamente SC1091; al seguir el source con `-x -P /src`, la validación pasó sin
  modificar código. `python3 -m py_compile tests/test_h3_public_price_projection_migration.py`
  también pasó en Docker con el bytecode fuera del checkout.

### Integridad documental

- El workflow `security-audit.yml` selecciona el manifiesto candidate-aware R21
  (`h3req1_public_admin_corrections_2026-10-26/candidate-scope-manifest-2026-10-26.json`)
  si el diff no cambia un manifiesto candidato. El mismo checker/configuración pasa
  en baseline merge (`742/742` fuentes, self-test PASS, 0 diagnósticos) y candidato
  (`747/747`, self-test PASS, 0 diagnósticos). Las cinco fuentes nuevas están
  asignadas al grupo de la migration correctiva.
- El checker integral sin manifiesto falla en baseline y candidato. Se capturaron
  todos los mensajes con el mismo checker/configuración y un ajuste de solo impresión
  en memoria para superar su límite de 200; el estado del checker y el algoritmo de
  validación no se modificaron. Cada árbol tiene 349 diagnósticos reales, 348
  idénticos. El único cambia por las cinco fuentes candidate-only añadidas:
  `299 != 367` en baseline frente a `304 != 367` en candidato. Por tanto el delta
  conserva el FAIL histórico y no reclama PASS integral.
- Logs íntegros:
  `/tmp/studiamatch-h3req1-doc-results/integral-baseline-exact.log` (SHA-256
  `0c2c76acfd4d1a0a549acdde24a470906df85e10ec7ee18ef383cc2d441c3398`) y
  `integral-candidate-exact.log` (SHA-256
  `6c995f7170899885e686bd13de837590d1f356f25fe1a9badad00d763acf7e5e`). Listas
  exactas de 349 errores y diff:
  `baseline-failures-exact.txt` (`dee27d01d01bc722ffa2db96c78e951ef7431bde4e121e41319e7a8ca4ea370c`),
  `candidate-failures-exact.txt` (`51189e74ec28d64f4e22c34c2daeeebc7496702dbd76bb84269d5afc26790b85`),
  `failure-delta-exact.diff` (`6b8aa40f4123df8e72dbf3bee61286bb05fee938bf9c39b038b08f73215a32cb`).
- La primera corrida candidate-aware encontró dos anclas rotas hacia
  `#corte-vigente`, por el cambio documental del título operativo. Se restauró el
  heading canónico `## Corte vigente`; la repetición del mismo gate pasó en baseline
  y candidato. No se borraron relaciones ni se inventaron archivos históricos.

### Estado, autorización y siguiente acción

- Baseline de código: merge real #508 `77b3f4ea27a8aaa6d1d0571ee5a9b5f1afd264a3`;
  rama aislada `codex/h3req1-public-price-projection-20261028`. El host Development
  mantiene el deployment previo `27d9ebfc` y continúa bloqueado por la lectura
  pública fallida; R1/R4 siguen aceptados, R2 falló y R3 no se ejecutó (2/4).
- Autorizaciones consumidas: solo harness sintético y validaciones Docker locales.
  Ningún JIT remoto nuevo, SQL remoto, escritura Supabase, cuenta real, FG3, writer,
  schedule, deploy o promoción se autorizó ni ejecutó en este delta.
- El scan Codex Security focal quedó completado: ID
  `b4f8c079-a0b5-489d-acae-d941bb1c31ec`, digest
  `codex-security-snapshot/v1:sha256:018d8d187e42a5e75e676c2e63784469c11066fb5e102381de200f93ea681db4`,
  cobertura completa de 15/15 paths, cero findings. El worklist del plugin enumeró
  cuatro paths; los once restantes se inspeccionaron manualmente y quedaron en el
  recibo `artifacts/manual-diff-review.md`. Delegación no disponible fue un warning
  de preflight, no un bloqueo: el agente revisó el diff completo. Reporte:
  `/home/romel/.codex/state/plugins/codex-security/scans/studiamatch-h3req1-public-price-projection-20261028/77b3f4ea27a8aaa6d1d0571ee5a9b5f1afd264a3_20261028T204548Z_rko0su6k/report.md`.
- El PR #509 está abierto hacia `desarrollo`: rama
  `codex/h3req1-public-price-projection-20261028`, base
  `77b3f4ea27a8aaa6d1d0571ee5a9b5f1afd264a3`, HEAD observado antes de este checkpoint
  `7cc3280351b3806853e48fd8993315a33619c3f9` (2 commits, 15 paths), URL
  `https://github.com/romelhc95/studiamatch/pull/509`. En ese SHA se leyeron 18
  check runs: 16 `success`, 2 `skipped`, ninguno fallido o pendiente. Cloudflare
  Pages informó `success` para el preview automático; no hubo smoke de negocio.
  `Supabase Preview` y `H2 Main Production Expand Gate` fueron `skipped`. El PR no
  está aprobado ni mergeado.
- El primer intento de push fue detenido por el hook pre-push, que escaneó el árbol
  completo al no existir upstream de la rama e indicó un patrón credential-like en
  `scripts/maintenance/debug_autocad.py`, path sin cambios y fuera del diff. No se
  copió ni modificó el valor. Tras verificar que `origin/desarrollo` coincidía con
  el baseline, se usó temporalmente como upstream según el mecanismo del hook; el
  escaneo del diff real pasó y el push fue no forzado.
- Esta continuación añade solo documentación canónica al PR existente. El commit
  documental genera otro SHA y checks nuevos; tras leerlos se actualizará la
  descripción del PR con la identificación final y resultados efectivos. R1–R4 no
  se repiten. No se hará SQL remoto, merge, deploy ni promoción.

## Registro histórico del candidato y sus gates locales — previo al merge

**Corte:** 2026-10-28, America/Lima. Continuación iniciada a las 11:24:51 (-05:00);
este corte se actualizó a las 11:50:04 (-05:00). El checkpoint anterior cerró a
las 10:08:44 (-05:00). Todos los tiempos usan America/Lima.

## Baseline y estado

- Checkout aislado: `/tmp/studiamatch-h3req1-editorial-contract-20261028`.
- Rama: `codex/h3req1-editorial-contract-20261028`.
- Base: `desarrollo@f39a688f75531d190745225f11524414181ed425`; el HEAD local incluye
  la corrección `393d3543` y la actualización documental de este corte. El remoto
  del PR aún no incluye ninguno de esos commits.
- El primer commit del PR es `475f3dce36dd798035661b2c9190527b7f4712e9`. El
  follow-up `393d354303f0ee620b0199e89d2ed2d6f43cf634` corrige los dos fallos del
  primer CI; está comprometido localmente y espera push no forzado.
- PR #508 abierto hacia `desarrollo`: `https://github.com/romelhc95/studiamatch/pull/508`.
  El remoto aún muestra head `475f3dce36dd798035661b2c9190527b7f4712e9`; su primer
  run CI fue `40727339670`. Los dos fallos reproducibles se corrigieron en paths y
  clasificación de test exactos; no hubo aprobación ni merge.
- Deployment Development de referencia observado previamente: `d6e7b158-b26f-4504-b445-1facac915269`, host `desarrollo.studiamatch-aty.pages.dev`, SHA `f39a688f75531d190745225f11524414181ed425`. No hay deployment del candidato.
- No se modificó el WIP de otros checkouts. No hubo Supabase, SQL remoto, cuentas,
  sesiones reales, writers, schedules, FG3 remoto ni configuración remota.

## Matriz antes/después E1–E6

Antes: en el baseline `f39a688` no se encontró evidencia que probara los nuevos
comportamientos juntos; el permiso de edición User seguía restringido por
`missing_fields` y la proyección no separaba un snapshot editorial aprobado.
Las pruebas históricas no acreditan el contrato de esta matriz.

| ID | Criterio | Antes del cambio | Después y evidencia nueva | Estado |
|---|---|---|---|---|
| E1 | Colaborador corrige campo poblado, guarda/recarga y vuelve a corregir con auditoría. | Sin prueba del permiso nuevo sobre campos poblados. | Harness PG17 sintético: las dos correcciones persisten en borrador y cada una conserva auditoría/versionado. Log `harness-r4.log`; assertion en `tests/sql/h3_pg17_harness.sql`. | ACEPTADO local |
| E2 | Colaborador no publica ni administra miembros; anónimo rechazado. | Sin ejecución nueva del contrato revisado. | Harness PG17: rol User no puede publicar; anónimo no puede leer la RPC editorial; los RPCs de administración conservan el gate Admin. No se usaron cuentas reales. | ACEPTADO local |
| E3 | Admin publica; el público usa snapshot, que sobrevive borrador posterior, cambio de base/pipeline, expiración y `unknown`. | Sin separación verificada de borrador y snapshot. | Harness PG17: publicación toma la corrección; ediciones ulteriores no se filtran; vencimiento/unknown y cambios base no sustituyen el snapshot; una nueva publicación lo reemplaza. | ACEPTADO local |
| E4 | Versión obsoleta rechazada sin pisar ganador. | No se ejecutó el delta nuevo. | Harness PG17 devuelve conflicto de versión obsoleta y el valor ganador permanece. | ACEPTADO local |
| E5 | Fecha antigua, evidencia vencida y error transitorio no desactivan; retirada inequívoca sí, sin borrar fila. | FG3 podía desactivar por fecha base antigua. | `tests/test_integrity_ping_retirement_contract.py`, 4/4 en Docker: HTTP 503, HTTP 200, fecha antigua y availability vencida/desconocida no desactivan; 404 inicia gracia; 410 reiterado tras más de tres días desactiva sin borrar el curso. | ACEPTADO local, con límite semántico |
| E6 | Historial cerrado/teclado, versión compacta, preview draft/publicado, sin overflow desktop/móvil. | No se había probado el nuevo UI. | Ejecución nueva del candidato de la rama indicada arriba en Chrome Windows del puente; solo fixture sintético local `00000000-0000-4000-8000-000000000001`, servido por Docker en `http://localhost:38741/admin/edit/`. Historial inicialmente cerrado; Enter abrió y mostró el evento sintético; Space lo cerró. Preview mostró exactamente `CURSO SINTÉTICO EN BORRADOR` / `CURSO SINTÉTICO PUBLICADO`. Insignia `v7`: 32,6 px. Escritorio: document/client width 1428/1428; móvil emulado 390×844: 390/390, sin overflow. | ACEPTADO local |

Resultado local de la matriz nueva: antes **0/6** con evidencia del contrato nuevo;
después **6/6 = 100 %**, delta **+100 puntos porcentuales**. E1–E5 son evidencia
local aceptada del checkpoint anterior y E6 es ejecución nueva. Esos números
solo describen E1–E6 locales y no son aceptación remota, seguridad global ni avance
total de H3REQ1. El antiguo 6/6 MIN-01..06 no se reutiliza.

## Evidencia ejecutada y reusada

### Ejecución nueva

- Migration `db/migrations/20261028_h3_editorial_publication_snapshot.sql` aplicada
  dos veces en PostgreSQL 17 desechable y sintético dentro de Docker; pasa la
  idempotencia y el harness termina `h3_pg17_harness_ok`. Log:
  `/tmp/h3req1-editorial-pg17.CfjBsf/harness-r4.log`. El contenedor usa red `none`,
  filesystem PG temporal y fixtures montados de solo lectura; se retiró al terminar.
- Prueba FG3 aislada: `tests/test_integrity_ping_retirement_contract.py`, 4 passed.
- Suite de contrato Admin: `tests/test_h3_admin_queue_ux_contract.py`, reejecutada
  en fixture temporal del contenedor con `PYTHONDONTWRITEBYTECODE=1` y sin cache:
  13/13 PASS. El primer intento del fixture tuvo 11 PASS y 2 errores `FileNotFound`
  porque no incluía `web/functions`; se copió esa ruta desde este SHA y la repetición
  focal pasó completa. No se modificaron fuentes por ese error instrumental.
- `npm run lint`: 0 errores, 9 warnings preexistentes en `HomeContent.tsx`;
  `npx tsc --noEmit`: PASS; `npm run build:mock`: PASS y export estático de
  `/admin/edit/`; `node --check tests/h3_local_uat.mjs`: PASS. Build de Docker con
  acceso de red necesario solo para descargar las fuentes oficiales de Geist.
- Casos source-level y contratos estáticos actualizados, incluidos labels de draft
  y publicación y las nuevas aserciones E6. No se usaron como sustituto del navegador.
- E6 se hizo únicamente con el fixture UUID sintético
  `00000000-0000-4000-8000-000000000001` en
  `http://localhost:38741/admin/edit/`; la respuesta de sesión, curso y auditoría
  fue simulada en memoria. No se emitió RPC de escritura, no se usó cuenta real ni
  pestaña remota. El viewport móvil se emuló en la misma pestaña Windows porque el
  tamaño mínimo de ventana del sistema impedía reducirla a 390 px. La emulación
  recargó el fixture en login; se reinyectó el mismo stub local y se continuó sin
  repetir autenticación. Chrome Windows no permitió guardar una captura en la ruta
  `/tmp` propuesta; la evidencia conservada es DOM/ARIA, resultado de teclado y
  medidas de viewport reproducibles.
- Documentación integral comparada con el mismo checker sin red, misma imagen Docker
  y configuración: baseline `f39a688` y candidato ambos FAIL con 350 diagnósticos
  completos; 349 son idénticos. El inventario se generó con el checker de la misma
  versión en un árbol diagnóstico temporal cuyo único cambio elimina el límite de
  impresión de 200 líneas; la lógica y parámetros de validación no cambian. Se
  confirmará el resultado integral otra vez con el checker original al cierre. El
  único texto que cambia es el contador heredado
  `INTEGRATION_PROJECTION_CANDIDATE_ONLY_COUNT` (baseline `297 != 367`, candidato
  `299 != 367`) porque el paquete añade dos rutas candidate-only. Los logs completos,
  lista exacta de errores y hashes quedan en
  `/tmp/h3req1-editorial-doc-logs/baseline/diagnostic.log` y
  `/tmp/h3req1-editorial-doc-logs/candidate-diagnostic.log`; las listas exactas y el
  diff están en `baseline/failures-exact.txt`, `candidate-failures-exact.txt`,
  `introduced-failures-exact.txt` y `resolved-failures-exact.txt` bajo ese directorio.
  La lista candidata tiene SHA-256
  `40afdbb5c700d9c18443e6c783307efde32fc3ddc3abeeeee18518066175a0bd`.
  Las clases comunes son `CANDIDATE_ONLY_PATH_MISSING` (79), `RELATION_PATH_MISSING`
  (88), `SOURCE_PATH_MISSING` (79), `SOURCE_PATH_MISSING_OR_OUT_OF_SCOPE` (79),
  `EXCLUSION_PATH_MISSING` (15), `DOCUMENT_EXCLUSION_PATH_MISSING` (4),
  `DOC_EXCLUSION_STALE` (4), `DOC_SELF_TEST_FAILED` (1) y un contador de proyección.
  El modo integral permanece FAIL; no se borraron ni fabricaron fuentes históricas.
- El proyecto define `--candidate-manifest` como gate candidate-aware en
  `security-audit.yml`. El manifiesto exacto del paquete está en
  `.context/evidencia/h3req1_editorial_contract_candidate_scope_2026-10-28.json`,
  SHA-256 `819bcc3d7f33883990e23af97b9863afe4cf9b5ca3e35d3672b78be1a4359bde`.
  La corrida final con la nueva entrada del inventario Python pasó: 742/742 fuentes
  asignadas, 119/119 documentos activos alcanzables, 433/433 históricos enlazados;
  self-test y gate PASS. El manifiesto coincide exactamente con las 28 rutas del PR.
  Este resultado acotado sigue separado del FAIL integral.
- El gate integral del proyecto sigue FAIL (exit 1), tanto en baseline como en el
  candidato. No se oculta ni sustituye por el PASS candidate-aware. Ambos árboles
  tienen 350 diagnósticos completos; 349 son idénticos. El delta solo cambia el
  contador de proyección candidate-only (`297 != 367` a `299 != 367`) por las dos
  rutas candidate-only añadidas. No se quitaron relaciones ni se inventaron archivos.
  El checker original imprimió sus primeros 200 mensajes y el resumen de 150 más;
  inventario exacto generado con la misma versión y lógica, sin límite de impresión,
  está en `/tmp/h3req1-editorial-doc-logs/` y su SHA figura arriba. Corridas oficiales:
  `/tmp/h3req1-editorial-final-logs/baseline-integral.log` y
  `/tmp/h3req1-editorial-final-logs/candidate-integral.log` (exit 1/1).
- Guard final validado en Docker sin red con worktree/Git común en solo lectura:
  `bash -n` PASS; `tests/test_protected_path_scope_guard.sh` PASS, incluyendo paths
  exactos del paquete, vecinos negativos y selector de manifests; inventario base
  de 1.196 paths, 13 catálogos/1.173 referencias. ShellCheck 0.11.0 PASS sobre el
  conjunto completo del job `actionlint And shellcheck` (siete archivos) desde la
  imagen local en caché. `git diff --check` PASS.
- Scanner versionado de credenciales del delta pasó para las 28 rutas, en Docker sin
  red. Compilación Python focal de `integrity_ping.py` y su prueba: 2/2 módulos PASS.
  JSON válido; candidate-aware consumió el mismo manifiesto que selecciona el workflow
  CI. El gate integral obligatorio antes de integrar sigue sin resolver por referencias
  históricas y no se declara PASS.

### Evidencia reutilizada

No se repitieron D01–D14, onboarding, invitación, recuperación, cuotas ni pruebas
remotas. No se acreditan como aceptación nueva.

## Acciones persistentes y fallos corregidos

- Efectos persistentes: solo código y documentación del worktree local. No se
  escribieron datos de aplicación; el harness SQL solo usó una base PG17 efímera.
- El guard y su regresión admiten solo las rutas nuevas exactas del paquete. Se añadió
  el manifiesto candidate-aware como path exacto; su vecino negativo continúa rechazado.
  No se ampliaron patrones de carpeta, workflows, permisos ni controles remotos.
- El primer CI del PR encontró dos omisiones atribuibles al delta. `Protected Path
  Integrity` rechazó `web/src/components/admin/CourseLivePreview.tsx` y
  `web/src/components/admin/editorial-ui.tsx`, ausentes del allowlist local de paths
  protegidos. Se añadieron esos dos paths exactos y vecinos negativos. `Python Compile
  And Tests` tuvo 251 PASS y un FAIL porque el test FG3 nuevo usa el cliente Supabase
  bajo fixture y no estaba en `DIRECT_SUPABASE_CONSUMERS`; se clasificó como
  `supabase-data-api-test`. La suite focal local pasó 45/45 en imagen Docker con
  pytest; el compare-candidate y su regresión también pasaron con los nuevos exactos.
  El commit correctivo `393d354303f0ee620b0199e89d2ed2d6f43cf634` está comprometido
  en el checkout local; los checks focales post-commit pasaron en Docker sin red:
  guard/compare-candidate, 49/49 tests Python de los dos contratos afectados y scan
  de credenciales. El gate candidate-aware documental también pasó para el manifiesto
  exacto. El commit aún no se ha enviado y GitHub debe reevaluarlo.
- El primer arranque de PG17 no tenía el modo de autenticación de test requerido;
  se corrigió solo el comando del contenedor. La siguiente ejecución encontró una
  función JSONB no disponible en PG17 y una colisión de fixtures; se corrigió el
  harness sintético y el r4 final pasó.
- La prueba FG3 inicial no tenía `supabase_credentials.py` en su fixture y el fake
  DB esperaba un filtro no usado por la ruta de lectura; se completó el fixture y se
  alineó la expectativa con el lector ilimitado de cursos. Revalidación: 4/4.
- El primer build offline no pudo descargar Geist; además la primera copia Docker
  no montaba `eslint.config.mjs`. Se repitió en Docker con el config presente y red
  solo para fonts: lint/types/build pasaron.
- Sin defecto de producto confirmado por esos fallos instrumentales.

## Seguridad, autorizaciones y límites

- Autorización vigente: implementación/tests Docker/PG17 y commit, push no forzado
  y PR a `desarrollo`, ya consumidos solo para esta feature. PR #508 está abierto.
  El delta correctivo local de 28 rutas pasó los gates focales indicados arriba. La
  acción exacta pendiente es push no forzado del commit `393d3543` y lectura de CI
  para el nuevo SHA.
  La rama protegida no se modificó.
- No autorizados ni ejecutados: aprobación de review, merge, SQL/migración remota,
  Supabase writes, interacción de cuenta real, FG3/pipeline/schedule, deploy manual,
  promoción y pruebas de negocio remotas.
- Revisión Codex Security formal completada: scan diff
  `a39fcd65-8774-40dc-afdf-75ff8654cd52`, snapshot
  `codex-security-snapshot/v1:sha256:9b4506019b938300c6df6a540818c7fa253b01f6d1f9dea43731d12d9222b03b`,
  cinco superficies, cero candidatos/reportables. El resultado corresponde a ese
  snapshot; la herramienta advierte que cambió el worktree mientras corría. Los ajustes
  posteriores de allowlist/inventario son paths/providers exactos, sin ampliar permisos
  de runtime: revisión estática focal, regresiones positivas/negativas y ShellCheck PASS.
  No es escaneo global ni validación remota. Reporte:
  `/home/romel/.codex/state/plugins/codex-security/scans/studiamatch-h3req1-editorial-contract-20261028/f39a688f75531d190745225f11524414181ed425_20261028T132753Z_9o66ixd8/report.md`.
- Revisión focal del delta de seguimiento `475f3dce..393d3543`: los únicos cambios
  de seguridad agregan tres rutas H3 exactas al allowlist, mantienen tres vecinos
  negativos, clasifican el test FG3 como consumidor Data API y lo incluyen en el
  manifiesto candidate-aware. No alteran permisos de runtime ni writers. La revisión
  estática de ese diff se respalda con guard/compare-candidate, scan de credenciales,
  ShellCheck y 49/49 pruebas focales PASS en Docker sin red; no se declara un segundo
  scan formal para este ajuste acotado.
- La vista usa `security_invoker`; la guía oficial de
  [Supabase Views](https://supabase.com/docs/guides/database/views) confirma que
  ese modo comprueba permisos/RLS del rol lector sobre las tablas subyacentes. La
  herramienta no abrió `changelog.md` por su `text/markdown`; el delta no adopta una
  API Supabase nueva.
- Límite FG3: HTTP 200 prueba respuesta HTTP, no pertenencia vigente al catálogo.
  Retirada semántica de páginas 200 queda trazada a H1; no construir crawler en H3.

## Transición y recuperación

- **Expand:** aplicar primero, con JIT DB nuevo, la migration forward-only que crea
  columnas snapshot nullable; no requiere backfill masivo. Mantener firmas/grants y
  compatibilidad de cursos sin snapshot.
- **Compatibilidad:** la lectura conserva el fallback legacy; la primera edición
  captura el valor público anterior antes de separar el nuevo borrador.
- **Deploy:** solo tras revisión/aprobación y autorización separada, aplicar la
  migration en el ambiente objetivo antes del deployment de la app compatible; luego
  hacer el smoke remoto mínimo aprobado: colaborador corrige campo poblado, Admin
  publica, visitante anónimo ve el valor, vencimiento/unknown conserva snapshot,
  historial y versión funcionan. La prueba remota no se autoriza en este ciclo.
- **Contract:** mantener snapshot como fuente pública; retirar la dependencia de
  disponibilidad para proyecto nuevo tras estabilidad y evidencia remota, en un
  paso de promoción separado. La retirada por HTTP 200 sigue fuera de cobertura.
- **Rollback:** restaurar código/RPC de la última versión compatible por deploy o
  migration correctiva; conservar las columnas y eventos append-only. No borrar
  snapshots, filas ni historial con rollback.

## Diferidos y siguiente acción exacta

1. **Revisión del gate documental integral** — owner TL/documentación; riesgo:
   350 referencias históricas/checks del baseline siguen rojos. Punto de revisión:
   antes de integración; el gate CI candidate-aware del paquete es independiente y
   debe pasar. Acción: reconciliar con fuente histórica o disposición canónica, sin
   quitar relaciones ni inventar archivos. El integral no se registra PASS.
2. **Revisión humana y promoción** — owner TL; antes de merge se revisan migración,
   transición y resultados CI. Migración remota, merge, deploy y smoke remoto requieren
   autorización separada y siguen pendientes.
3. **Retirada semántica HTTP 200** — owner H1; riesgo: un URL vivo puede mostrar una
   página que ya no lista el programa. Punto de revisión: diseño/ingesta H1; sin
   crawler universal ni waiver en este paquete.
