# Controles de seguridad y tooling

## Límites del control local

| Control | Fuente | Qué comprueba | Límite |
|---|---|---|---|
| Credential scan | `scripts/security/scan_credentials.sh`, `scan_worktree_file.py`, `.githooks/pre-commit`, `.githooks/pre-push` | Patrones configurados en staged/diff/tree y scripts de invocación; la lista concreta de consumidores está en el [registro](../trazabilidad/registro_fuentes_componentes.md#seguridad-y-tooling). | Solo cubre archivos/diffs y patrones escaneados; no lee secret stores ni demuestra hook instalado. No exponer valores al registrar fallos. |
| Protected path/scope guard | `scripts/security/protected_path_scope_guard.sh`, pruebas correspondientes y `security-audit.yml` | Restringe paths protegidos a allowlists para ramas de desarrollo protegidas. | YAML/código local no demuestra branch protection remoto ni required checks activos. |
| Revisión estática de workflows | `scripts/security/protected_workflow_review.py` y `tests/test_protected_workflow_review.py` | Contratos estáticos de workflows, eventos, permisos y límites ejecutados por el agregado `security-audit`. | No equivale a `actionlint`, ejecución de Actions ni al check PWI externo. |
| Verificador PWI externo | `scripts/security/pwi_worker/` y el GitHub App configurado fuera del repositorio | Valida firma, repo/rama/SHA, archivos cambiados y aprobación vigente. El candidato local invalida un check App previo a `in_progress` antes del `202` (deadline 7,5 s) y agenda la fila persistida para reintento Durable Object si falla el precheck. Con cola llena consulta la base/SHA actual del PR; reemplaza como máximo un evento elegible, reutiliza la misma fila si una redelivery activa pasa a `done` durante la lectura de cabeza, reordena filas y protege el cierre con secuencia/estado/intento actuales. Mantiene ocho pendientes/procesando y 100 terminales. | R3/R3-DO se consumieron al registrar/instalar la App y configurar/desplegar `studiamatch-pwi-verifier` con `PWI_COORDINATOR`. El responsable confirmó que el ID de instalación coincide con el guardado en Cloudflare, sin registrar el número. Las autorizaciones de precheck/R5/R6 cubren solo sus operaciones exactas y no autorizan despliegues, publicación ni configuración de branch protection. No hay evidencia de ejecución de la ruta R6 (`failed` redelivery) y su alcance era PR 501, ahora cerrado; no se reutiliza para otro PR. La entrega `check_suite.requested` respondió `202 ignored`; una entrega `pull_request/synchronize` fue reportada como HTTP 200, pero su respuesta sanitizada sigue pendiente. No se ha observado un check PWI del proveedor sobre un SHA exacto ni se ha acreditado la regla required de `desarrollo`. |
| Registro fuente-documento | `.context/trazabilidad/registro_fuentes_componentes.json`, `scripts/maintenance/h3req1_documentation_integrity.mjs`, `scripts/security/run_documentation_integrity.sh`, `security-audit.yml` | Fuentes nuevas sin asignar, componentes/fichas, documentos/anchors, backlinks, comentarios discordantes, roots/extensiones, enlaces huérfanos, una sola entrada principal, README raíz y retiros con reemplazo/hash externo. | El wrapper local usa Docker; el checker no importa módulos de producto ni consulta red/entorno. Para `inline_comment: none`, usa la asignación externa y no lee el archivo fuente buscando marcadores. `--render` solo escribe la vista Markdown generada. El job local de CI `documentation-integrity` está incluido en el agregado `security-audit`; su definición no demuestra que GitHub lo haya instalado o ejecutado. |
| Credenciales Supabase | `scripts/shared/supabase_credentials.py`, `web/src/lib/supabase.ts`, BFF/Edge y `tests/test_supabase_credentials_contract.py` | Formato de API key, origen de variable, destinos/métodos permitidos y excepción acotada de JWT de sesión. | Pruebas locales no demuestran que secrets/bindings remotos tengan esos valores/configuración. |
| RLS/RPC | migrations SQL, `web/functions/_lib/admin-bff.ts`, Edge de invitación y harnesses | Roles, grants, RPC allowlist, HMAC/gateway y seguridad de filas por código/fixture. | SQL local no prueba schema, `pgrst.db_pre_request`, llaves o policies remotas. No ejecutar SQL en esta sesión. |

`security-audit.yml` conserva literales de rutas documentales retiradas en `allowed_h3_local`; `tests/test_admin_invite_edge_contract.py` comprueba ese grupo de eliminaciones. Son excepciones del scope guard para que una eliminación documental acotada pueda activar y pasar el gate, no enlaces ni documentos activos. El path vigente `.context/trazabilidad/protocolo_constructor.md` se permite por separado como documento mantenido y la prueba comprueba también su existencia; no pertenece al grupo retirado. Al retirar o cambiar una ruta, actualiza juntos el allowlist, su prueba y el mapa origen→destino; conserva la excepción de borrado mientras el gate necesite reconocer el path eliminado. La sustitución documental y el respaldo de esas rutas están registrados en [la consolidación R11](../evidencia/h3req1_documentacion_consolidacion_trazabilidad_2026-10-13_r11.md#consumidores-y-referencias-revisadas).

La reconciliación vigente conserva rutas explícitas y regex acotadas de `allowed_h3_local`. `tests/test_protected_path_scope_guard.sh` lee `scope.entries` y los `package_artifacts` incluidos del manifiesto exacto invocado por `security-audit.yml` y compara cada path seleccionado con las regex y la lista exacta del workflow. También valida los 13 catálogos, el conteo de referencias directas fijado por ese manifiesto y los hashes de documentos/destinos de candidato. Para preservar la evidencia R19 del PR 501, esos pins históricos se cotejan contra el árbol integrado inmutable `8ac174d81cf6ce23658bff132236a78935ace1ad` mediante `git cat-file --batch`; el checkout sucesor se valida aparte con `protected_path_scope_guard.sh --compare-candidate`. Incluye positivos exactos del Worker PWI y negativos para rutas vecinas no revisadas. El manifiesto sucesor se incluye como artifact sin hash propio. El test local no ejecuta GitHub ni acredita Actions o branch protection remotos. Cada continuación debe actualizar conjuntamente el consumidor, manifiesto, allowlist y referencias documentales, sin ampliar carpetas.

El paquete local del contrato editorial H3REQ1 (2026-10-28) añade a `allowed_h3_local` solo cinco rutas explícitas: la migración snapshot, el cambio de FG3, su test, el checkpoint y la atestación CA4. La regresión del guard exige esas rutas y rechaza vecinos no revisados; no se añadió un patrón de carpeta.

El fix de lectura pública de precio extiende esa lista con cinco paths exactos: una migration y cuatro fixtures/tests PG17. `tests/test_protected_path_scope_guard.sh` exige las cinco rutas y rechaza sus vecinos `_extra`; no se amplían patrones ni carpetas. El resultado se limita al scope guard local y no prueba branch protection remota.

`security-audit.yml` agrega `tests/test_h3_public_price_projection_migration.py` a la suite pytest offline. Esa prueba valida el contrato estático de la migration; el comportamiento SQL queda cubierto por el harness sintético PG17, ejecutado localmente y no como efecto remoto.

El delta D04 mantiene R20/#503 intacto. El sucesor R21 `h3req1_d04_candidate_docs_scope_2026-10-25.json` conserva los 297 paths de selección R20 y añade únicamente la migration y el contrato Python D04 (299 entradas); `security-audit.yml` usa este snapshot y ejecuta el nuevo contrato con pytest. El manifiesto exacto de publicación `h3req1_d04_candidate_pr_scope_2026-10-25.json` enumera 19 paths, excluye explícitamente los dos WIP PostgREST y no incluye Admin/MFA/FG3 ajenos. La regresión protegida compara ese set con la allowlist exacta y prueba vecinos negativos; el guard solo agrega los paths concretos del paquete. Ambos JSON pertenecen a la familia de evidencia y no fijan su propio hash. Esto es validación local de alcance/CI, no publica ni demuestra el check remoto.

La regla de mantenimiento es bidireccional: crear/mover/eliminar/cambiar fuente, contrato, workflow, hook, permiso o scanner requiere actualizar el registro, la ficha de dominio, tests/evidencia y manifest por impacto. La prueba negativa del checker debe fallar para una fuente nueva no asignada. La revisión R11 mapea los contratos de scanner, scope guard, workflow review, preflight y política a los tests que los inspeccionan, con los límites de ejecución local/remota en [resolución de relaciones](../evidencia/h3req1_sem_resolucion_relaciones_locales_2026-10-13_r11.md#seguridad-workflows-y-el-gate-documental).

El workflow local `protected-workflow-integrity.yml` se retira en el sucesor R3 porque su helper falta en la base confiable y su ejecución no puede acreditar ese contrato. Su fallo remoto de `a73af141…` se conserva histórico. El contrato local exige que el check vigente provenga del GitHub App instalado solo en `romelhc95/studiamatch`, con permisos mínimos y el Worker `studiamatch-pwi-verifier`; el App evalúa exclusivamente PRs hacia `desarrollo`. La lectura de rulesets GitHub del 2026-10-21 encontró un único ruleset activo, `owner-only-protected-branch-updates`, dirigido a `desarrollo`, `certificacion` y `main`, con solo la regla `update`; no contiene requisito de PR ni check PWI. Ese ruleset tiene un actor con bypass `always`; no se usó ni modificó y queda fuera del alcance de este ciclo. La inspección humana de la regla clásica de `desarrollo` confirmó `Require status checks` y `Require branches to be up to date`; la única entrada requerida es `security-audit`, con fuente `any source` / GitHub Actions. `Protected Workflow Integrity` no está requerido. La regla de conversación solo se muestra en pantalla y su estado no fue confirmado. No se activa una alternativa que permita eludir la protección.

## GitHub Apps

### StudIAMatch PWI Verifier R3

Propósito: emitir el check externo `Protected Workflow Integrity` para un PR dirigido a `desarrollo`, validando repositorio, rama, SHA, rutas protegidas y aprobación humana mediante el Worker `studiamatch-pwi-verifier`. Responsable de la App: `@romelhc95` según la pantalla de configuración compartida. El responsable confirmó que la App está instalada únicamente en `romelhc95/studiamatch`, con `Pull requests: read`, `Checks: write` y eventos `pull_request`, `pull_request_review` y `check_run`.

Configuración del Worker confirmada por el responsable en Cloudflare, sin leer ni registrar valores: `GITHUB_APP_ID` (Text), `GITHUB_INSTALLATION_ID` (Text), `GITHUB_APP_PRIVATE_KEY` (Secret) y `GITHUB_WEBHOOK_SECRET` (Secret). El responsable confirmó que el secreto del webhook coincide entre GitHub App y Worker y, en una comparación privada, que `GITHUB_INSTALLATION_ID` coincide con el ID de instalación en GitHub; no se registra ninguno de los valores.

Evidencia operativa disponible: el historial `Advanced → Recent Deliveries` revisado por el responsable contiene solo dos `check_suite.requested` y un `ping` en los últimos tres días; ambas entregas `check_suite.requested` respondieron HTTP 202 `{"status":"ignored"}`, comportamiento esperado para ese evento. No aparece una entrega `pull_request` en ese intervalo. Esto no corrobora el reporte anterior de HTTP 200 para `pull_request/synchronize`; además, el contrato actual del Worker responde 202 `queued`/`already_queued` al aceptar trabajo. La consulta read-only de PRs abiertos del repositorio devolvió una lista vacía: no hay una PR disponible para producir ahora una entrega PWI. No se crea otra PR sin la autorización protegida correspondiente. No se ha observado un check `Protected Workflow Integrity` de este proveedor sobre un SHA exacto. La API `GET /branches/desarrollo` confirma la rama protegida y un solo check requerido: `security-audit` (`app_id=15368`, GitHub Actions); la inspección humana confirma `require up-to-date`. El responsable buscó `Protected Workflow Integrity` y el selector lo ofreció desde `GitHub Actions/any source`; se agregó solo al formulario sin guardar. Esa fuente no acredita la App PWI y no se guarda como reemplazo. La única ruleset activa no exige el check. El contrato Actions `PWI Worker Contract` prueba código; no sustituye esas comprobaciones remotas. GitHub documenta que Advanced muestra las entregas de los últimos tres días: [Viewing webhook deliveries](https://docs.github.com/en/webhooks/testing-and-troubleshooting-webhooks/viewing-webhook-deliveries).

Mantenimiento: limitar la instalación al repositorio aprobado y a los permisos/eventos mínimos; cualquier rotación del secreto webhook debe actualizar ambos lados en una misma intervención coordinada. No copiar claves o valores a código, documentación, logs o chat. Estado vigente: instalación y variables confirmadas por la persona responsable; integración de eventos, check confiable y branch protection aún sin acreditación técnica.

### StudIAMatch Bootstrap Guardian

El nombre fue comunicado como una GitHub App existente. La búsqueda de todo el checkout, incluidos workflows y archivos ocultos, no encontró referencias de integración o consumo; la búsqueda pública por el nombre exacto tampoco produjo resultados. No hay evidencia suficiente para determinar propósito, responsable, repositorios instalados, permisos, eventos, servicio asociado, configuración o mantenimiento. La relación con PWI y cualquier posible duplicación siguen **desconocidas**. No se modifica ni desinstala; antes de documentar su operación hace falta observar su pantalla de configuración y contrastar el uso en GitHub.

## Registro de fuentes y gate

### Selección documental de promoción — remediación local 28-oct-2026

El responsable eligió revisar el acumulado completo hacia Certification. El guard
conserva sus regex/listas normales y añade, solo para esa ruta, los 239 paths del
[scope de promoción](../evidencia/h3req1_certification_promotion_path_scope_2026-10-28.json).
Cada entrada fija blobs del baseline `c80f6504…` y del origen `941eca49…`; ambos
commits se fijan también independientemente en el caller del guard. El validador
exige baseline exacto, origen ancestro de HEAD y contenido HEAD idéntico al origen
para cada path adicional. No permite paths nuevos, duplicados, control/traversal,
blobs falsos o drift de esos archivos. Solo emite la lista después de validar todos
los pins. Un sucesor que cambie uno requiere revisión y actualización explícita;
no hereda una excepción por carpeta. La entrada del propio manifest se admite
por nombre exacto para su PR de remediación. Su scope no autoriza ejecución remota.
Los tests usan Git desechable y comprueban baseline incorrecto, blobs falsos,
duplicados, vecino no incluido y drift de contenido. El rollback retira el
manifest y su consumo por PR protegido, restituyendo el rechazo de promoción.
El `push` normal posterior al merge en Certification conserva la selección
documental agregada; el guard admite los pins en ese evento únicamente si el
baseline sigue siendo el `c80…` exacto de esta primera promoción. Así el check
posterior al merge no pierde el contrato validado en el PR ni habilita sucesores
arbitrarios. Los PRs de otras rutas siguen bajo selección única.

El selector de `security-audit.yml` conserva una única selección y rechaza
ambigüedad en PRs normales. Para las rutas GitHub `desarrollo -> certificacion`
y `certificacion -> main` genera un agregado efímero en
`.git/h3req1-promotion-documentation.json`: unión de
todos los paquetes documentales cambiados, sus artifacts incluidos y todas las
rutas supervivientes del diff Git real. Registra baseline, HEAD y SHA-256 de cada
paquete. Los paths seleccionados ausentes o inseguros y los manifiestos
documentales malformados siguen fallando. Los manifests de paths PR con schema
propio no son selecciones documentales; se reconocen únicamente por su estructura
válida, y sus archivos siguen incluidos en el diff agregado. JSON histórico que no
puede ser una selección por nombre ni tiene rol JSON válido no se interpreta como
selector. No se elimina ni altera ese artifact.

`tests/test_protected_path_scope_guard.sh` prueba ambas rutas PR, los pushes
posteriores a cada promoción, la unión y cobertura del diff, hashes, inputs
ausentes, PR scope inválido y ambigüedad normal. PASS Docker local no acredita
Actions ni promoción. Se conserva el checker integral y su FAIL histórico: esta
remediación no concede waiver ni autorización remota. Se expande el selector
manteniendo compatibilidad con una selección; el despliegue sigue el PR protegido
del ambiente correspondiente. No hay
legacy nuevo que retirar. Rollback: revertir el cambio por PR protegido; la
promoción volvería a fallar cerrada, sin efectos DB. La revisión/evidencia de este
ciclo se registra en el [checkpoint](../evidencia/h3req1_editorial_contract_2026-10-28.md).

[`registro_fuentes_componentes.json`](../trazabilidad/registro_fuentes_componentes.json) es la autoridad verificable de asignaciones. Cada ruta mantenida queda enlazada a un componente, una ficha/anchor de fuente y una página de dominio; el registro añade propósito, contrato, consumidores/dependencias, datos, pruebas/evidencia, operación/permisos y procedencia. Las relaciones se anotan por grupos con límites explícitos: `pending` y `unknown` no cuentan como verificadas ni se convierten en consumidores por similitud de nombre.

El Markdown de [asignaciones y navegación](../trazabilidad/registro_fuentes_componentes.md#asignaciones-por-fuente) se genera con `bash scripts/security/run_documentation_integrity.sh --render`; no es una segunda autoridad. El checker local compara el inventario encontrado bajo raíces declaradas y la raíz no Markdown de `.context`, exige asignación/documento/ancla, detecta grupos huérfanos, rutas o anchors inexistentes, enlaces de retorno y marcadores `StudIAMatch-Docs:` discordantes en políticas `required`/`optional`.

Para validar un snapshot de publicación que excluye WIP, se puede pasar `--candidate-manifest <ruta-relativa>` al checker/wrapper. Ese modo acepta únicamente rutas ausentes que estén enumeradas exactamente en `candidate_only_paths` o en las exclusiones de fuente/documento del registro canónico, y que el manifiesto exacto no seleccione; las rutas seleccionadas por el manifiesto deben existir y las ausencias no declaradas siguen fallando. El modo normal del checkout completo no cambia ni tolera esas ausencias. Esta verificación de snapshot no sustituye el self-test ni el guard de referencias a catálogos. También exige `.context/indice.md` como entrada única, root README con un enlace a ese índice, documentos vigentes alcanzables y retiros ausentes del árbol con reemplazo y respaldo hash-registrado. La política `none` usa el registro y no lee el archivo buscando comentarios. El modo normal no escribe; `--render` solo regenera la vista. El self-test incluye una fuente nueva no asignada, raíz/extensión desconocida, comentarios incompatibles, path/anchor inexistente, índice duplicado y documento retirado que sigue presente; también verifica que una omisión exacta registrada solo se tolere bajo el manifiesto exacto y fuera de sus paths seleccionados; las rutas no registradas, seleccionadas o probadas sin manifiesto siguen fallando. `security-audit.yml` ejecuta el gate como job que alimenta el agregado `security-audit`; esto deja preparado el contrato local de CI, no acredita instalación ni ejecución remota.

Los comentarios fuente solo señalan una ruta documental breve y única; no llevan descripción adicional. El detalle vive aquí y en el registro. Se exigen donde el grupo los marca `required`, incluidos `roi_engine.py`, el workflow de seguridad, el renderer y las primitivas/clases compartidas, la cola Admin, la política de contraseñas y el transporte Supabase. JSON, migrations históricas, evidencia sellada, snapshots, salidas generadas y dependencias se relacionan externamente o se excluyen con motivo, sin comentarios artificiales.

El gate comprueba existencia de paths/anchors, estructura y coherencia de marcadores. Un `commit:<hash>` se comprueba solo por formato, no por existencia del objeto; `path:<...>` prueba existencia, no un símbolo ni la verdad semántica de la afirmación. Esa revisión requiere `git show`/`git blame` local y revisión de fuentes; si la historia local no conserva el objeto, el follow-up de G10 debe pedir la lectura remota específica. Ningún check de este registro acredita adopción remota.

## Fuentes y relaciones

[Seguridad](../seguridad.md) · [CI/CD](../ci_cd.md) · [Operación](../operacion.md) · [Pruebas](../pruebas.md) · [Registro](../trazabilidad/registro_fuentes_componentes.md#seguridad-y-tooling) · [Registro canónico y checker](../trazabilidad/registro_fuentes_componentes.json)

## Navegación histórica local

Evidencia preservada por proceso; cada catálogo enlaza sus documentos históricos individualmente y no es una autoridad operativa.

- [Admin, autenticación e historia editorial](../catalogos_historicos/admin_auth_editorial.md#documentos-preservados)
- [Frontend público y UAT](../catalogos_historicos/frontend_publico_uat.md#documentos-preservados)
- [Pipeline, datos y base de datos](../catalogos_historicos/pipeline_base_datos.md#documentos-preservados)
- [Infraestructura, seguridad y CI](../catalogos_historicos/infra_seguridad_ci.md#documentos-preservados)
- [Documentación, trazabilidad y transferencia](../catalogos_historicos/documentacion_trazabilidad.md#documentos-preservados)
- [Registros operativos históricos y JIT](../catalogos_historicos/operacion_jit.md#documentos-preservados)
- [Seguimiento y handoffs históricos](../catalogos_historicos/seguimiento_historico.md#documentos-preservados)
- [Documentación DB sustituida](../catalogos_historicos/database_legacy.md#documentos-preservados)
