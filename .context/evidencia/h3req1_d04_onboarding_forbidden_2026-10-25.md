# D04 — denegación de rol del lector de membresías

Fecha: 2026-10-25. Checkout de código: `/home/romel/src/studiamatch-h3req1-d04-onboarding-denial-20261025`, rama `feat/h3req1-d04-onboarding-denial-20261025`, base/HEAD `6b3ec2d5cc647f81e05fe99cb1b48b39658a1e87`. El corte original de esta ficha era local y no publicado; el estado de publicación vigente se actualiza en la última sección fechada.

## Diagnóstico remoto conservado

Development es `https://desarrollo.studiamatch-aty.pages.dev/`, SHA `6b3ec2d5cc647f81e05fe99cb1b48b39658a1e87`, deployment `4c95ce98-cc78-4bf0-a99e-e7bcc773c01e`. El lector `admin_list_members_onboarding` devolvió históricamente HTTP 502 `rpc_failed` en sesiones Outlook `user` e `inactivo`; no se expusieron request/response bodies ni credenciales y no se repitió la RPC en esta etapa. Logs cercanos contenían SQLSTATE `PGRST` y texto de conexión sin función/request correlacionada. El estado `user/activo` tenía `/api/admin/session` 200 y lectura `admin_current_user_role` 200; eso reduce la hipótesis de caída global de sesión, pero no demuestra la causa del 502 del lector.

Lectura de la implementación local: el guard de la función privada usa `RAISE EXCEPTION`, cuyo estado predeterminado es P0001; el wrapper de cuota captura `42501` y lo mapea a `403`, y sus otros fallos toman una ruta genérica. La documentación oficial de [PostgREST](https://docs.postgrest.org/en/v14/references/errors.html) registra el mapeo de `42501` a 403 y P0001 a 400 para requests autenticados. Esto demuestra una incompatibilidad del contrato de denegación en el código local; no demuestra que fuera la causa del 502 remoto observado.

## Recorrido UI user activo — delta del 2026-10-25

Chrome DevTools MCP `list_pages` mostró la pestaña Windows existente 19; `select_page(..., bringToFront:true)` y el snapshot identificaron Outlook en `/admin/`, con el panel “Panel de actualización de información”. Una navegación directa a `/admin/users/` terminó de vuelta en `/admin/`; la UI mostró nuevamente la sesión Outlook y el panel limitado user, sin lista de membresías. Network MCP se usó únicamente para método/path/status: mostró sesión/RPC con respuestas 200 durante la carga, pero no expuso nombres RPC ni bodies suficientes para atribuir esos 200 a `admin_list_members_onboarding`. Resultado: **PASS de la ocultación/redirección visible de esta ruta**, no PASS de guarda SQL/API. No se mutaron datos.

En un escenario anónimo previo de esta etapa, el logout BFF respondió 200; la ruta directa `/admin/users/` acabó en `/admin/login/` sin tabla y una RPC anónima devolvió 401. No se leyeron cuerpos ni encabezados. Esto es evidencia de un subcaso anónimo y no se generaliza a CSRF autenticado, expiración, refresh ni todas las APIs.

## Corrección local

- `db/migrations/20261025_h3_admin_members_onboarding_forbidden_status.sql`: valida firmas, wrapper/marker y una ocurrencia exacta del guard legacy, reemplazándola por SQLSTATE `42501`; ante drift se detiene. No altera filas, grants, cuota o firma. No aplicada.
- `web/functions/_lib/admin-bff.ts`: traduce el HTTP 403 recibido en código/mensaje seguros `forbidden`; se conserva la clasificación MFA y el tratamiento genérico de errores desconocidos.
- `tests/h3_admin_bff_mock_uat.mjs`: regresiones de 403 sanitizado, error desconocido y MFA.
- `tests/sql/h3_admin_quota_harness.sql`: Admin puede leer sus filas; user recibe estado 403 sin datos; conserva el cupo total ajustando el número de lecturas previas.
- `tests/test_h3_admin_onboarding_denial_contract.py` y `tests/test_security_flow.py`: aserciones de contrato/mapeo.

## Validación local y límites

Docker aislado, Linux amd64, image `studiamatch-h3req1:sync-a57bc415-rebuilt-20261018`, fuentes read-only, red deshabilitada:

- `tests/h3_admin_bff_mock_uat.mjs`: **PASS 127 checks**.
- `tests/test_h3_admin_onboarding_denial_contract.py`: **PASS 3 funciones**.
- `test_admin_invitation_bff_sanitizes_internal_edge_business_codes` de `tests/test_security_flow.py`: **PASS**.
- `git diff --check`: **PASS**.

Estos resultados acreditan mock y contrato estático. El harness SQL/PG17 no fue ejecutado, la migration no fue aplicada, no se hicieron escrituras remotas ni se publicó código. No hay revisión de seguridad integral concluida; la revisión focal del delta no identifica cambio de grants, exposición de datos o secreto.

## Compatibilidad, recuperación y siguientes gates

- **Expand:** reemplazo idempotente de un guard con preflight estricto; el wrapper/gateway permanecen intactos.
- **Compatibilidad:** firma, grants, cuota, shape de respuesta y error MFA no cambian; solo la denegación explícita toma el 403 ya esperado.
- **Deploy:** requiere autorización de pruebas SQL/PG17 y después una publicación protegida separada; ninguna se consumió aquí.
- **Contract:** no se eliminan rutas ni errores legacy durante este corte. Solo reconsiderar tras estabilidad demostrada en el runtime.
- **Rollback:** restaurar el guard solo con la definición exacta verificada y una migration inversa revisada/autorizada; no ejecutar rollback automático ni revertir otros consumidores.

Estado: **REQUIERE REMEDIACIÓN / PENDIENTE SQL local y remoto** para D04 server-side. El 502 histórico queda sin causa demostrada. No repetir la lectura hasta tener correlación nueva o el candidato desplegado con el cambio y permiso de prueba remota.

## Actualización de validación local — 2026-10-25 20:42 UTC

En Docker Linux amd64, red deshabilitada y fuentes read-only:

- `tests/h3_admin_bff_mock_uat.mjs`: PASS, 127 checks.
- Las **cuatro** funciones de `tests/test_h3_admin_onboarding_denial_contract.py` y `test_admin_invitation_bff_sanitizes_internal_edge_business_codes` de `tests/test_security_flow.py`: PASS por invocación directa de funciones. La imagen no tenía `pytest`; esto no se registra como ejecución pytest.
- `tests/h3_admin_invite_edge_uat.mjs`: PASS; salida: `successAndReplayCases=3`, `corsCases=6`, `errorClassificationCases=7`, `ambiguousDeliveryCases=10`, `replayCases=4`, `concurrentReplayCases=1`, `expiryCases=1`. Son escenarios mock de Edge/reservación: prueban que replay/duplicado detiene efectos Auth y que la reserva expirada va por RPC auditable, no el token OTP real del proyecto.
- `node --check` de los runners ejecutados, `scan_credentials.sh` sobre los 15 paths explícitos y `git diff --check`: PASS. Un intento previo del scanner con `--files` falló porque la interfaz acepta paths posicionales; el modo corregido pasó. El modo `--tree` tampoco sirve dentro del bind mount porque el `.git` pointer queda fuera del contenedor.
- Revisión focal de seguridad diff Codex Security, scan `ccd4106f-1884-445d-ac64-e777460ae607`, snapshot `codex-security-snapshot/v1:sha256:9b587758bbd57a0ff8e9253c74c984f454dc9ea99c6b640c110e44780b8ecf16`: completa sobre el diff local, cero findings reportables. No revisa runtime; no atribuye el 502 histórico ni acredita la migration.

El JIT PG17 aprobado se detuvo en su preflight porque `tests/sql/h3_quota_postgrest_fixture.sql` está modificado pero fuera de las 50 fuentes aprobadas. Ningún contenedor ni base fue creado y no se ejecutó SQL. La evidencia de esa parada está en el checkout operativo: `.context/evidencia/h3req1_d04_d05_pg17_jit_2026-10-25.results.txt`.

El resultado de Edge local amplía cobertura sintética D03 (reserva/replay/duplicado/expiry), pero no verifica callback contra Supabase Auth, expiración OTP real, email, membresía/auditoría en Development ni onboarding de una identidad nueva. D03 sigue parcial. D04 sigue REQUIERE REMEDIACIÓN en DB/HTTP real y la migración permanece sin aplicar.

## Reconciliación del JIT PG17 y alcance de publicación — 2026-10-25 20:44 UTC

La verificación `sha256sum -c` del manifiesto conservado en el checkout operativo se ejecutó con este worktree D04 como directorio base: las 50 fuentes devolvieron `OK`. Un recorrido read-only de inclusiones desde los tres roots del paquete confirmó clausura de 50 paths; `tests/sql/h3_quota_postgrest_fixture.sql` no está referenciada. Su SHA local actual es `296ace8bb9e452f43239f5af2c5047fb6e29fc4950463b703aea968771825661`. El JIT aprobado se detuvo antes de crear el contenedor por su condición explícita de parar ante todo delta SQL no descrito. Esta inspección adicional explica el drift, pero no reactiva el permiso ni autoriza ejecutar los roots; la propuesta de addendum queda en el checkout operativo.

La revisión estática Codex Security del diff local concluyó con scan `ccd4106f-1884-445d-ac64-e777460ae607`, digest `codex-security-snapshot/v1:sha256:9b587758bbd57a0ff8e9253c74c984f454dc9ea99c6b640c110e44780b8ecf16` y cero findings reportables. No valida runtime. El self-test documental de este checkout continúa fallando por rutas C03 WIP ausentes/fuera del alcance del worktree; no se modificaron checker ni relaciones para suprimir el resultado.

Para un PR futuro se propone incluir solo BFF, migration, mock BFF, `h3_admin_quota_harness.sql`, contrato Python, prueba de seguridad, tres fichas, evidencia D04, índice y registry JSON/Markdown (13 paths). Se preservan fuera del candidato `tests/h3_admin_quota_postgrest.mjs` y `tests/sql/h3_quota_postgrest_fixture.sql` (2 paths), porque no pertenecen a la secuencia aprobada y no tienen ejecución funcional acreditada. El scope permanece **no listo para publicación** hasta superar el PG17 y cerrar los gates documentales/plantilla/checks; no se ha solicitado ni ejecutado publicación.

## Resultado de la ejecución PG17 única — 2026-10-25 20:55 UTC

El JIT original se detuvo antes de escribir; el responsable aprobó el addendum-1 y su única ejecución pasó. Checkout, rama, HEAD `6b3ec2d5cc647f81e05fe99cb1b48b39658a1e87`, imagen `postgres:17@sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f`, manifiesto 50/50, cierre de inclusiones exacto y WIP fueron revalidados inmediatamente antes de crear recursos. El SQL adicional `tests/sql/h3_quota_postgrest_fixture.sql` permaneció fuera de la clausura por su SHA aprobado. Se crearon dos bases nuevas vacías en un único contenedor sin red y se ejecutaron una vez los tres roots autorizados.

Resultado PASS local: markers `h3_onboarding_rbac_hardening_harness_ok`, `h3_pg17_harness_ok`, `h3_from_h2_pro_pg17_harness_ok` y `h3_admin_quota_harness_ok`. Postflight read-only: 2/2 Admin sintéticos activos/ready y 4 eventos de auditoría para el segundo en `h3_gate`; guard privado con SQLSTATE `42501`, 2 miembros en la base de cadena (1 Admin activo/ready, 1 user activo/ready). Las aserciones comprueban Admin permitido, user rechazado con estado 403 y sin columnas de miembro, además de MFA/cuotas y protección de último Admin sintéticos. El contenedor creado fue detenido y auto-retirado.

Este resultado prueba el contrato bajo PG17 sintético, no PostgREST HTTP, runtime BFF remoto ni Development; el 502 histórico conserva causa no demostrada. No hubo SQL remoto, cuentas, correo o publicación. No repetir el paquete consumido.

## Revisión de impacto y paquete exacto D04

El delta cruza cuatro superficies enlazadas: guard privado SQL -> wrapper de cuota -> status PostgREST consumido por `/api/admin/rpc` -> consumidor único `web/src/app/admin/users/page.tsx` (`admin_list_members_onboarding`). La migration verifica las dos firmas fijas, el marker y una única frase legacy; sustituye P0001 por `42501` solo para esa denegación. No cambia firma, grants, consulta, cuota ni datos. El BFF mapea únicamente status HTTP 403 a un error `forbidden` sanitizado, conserva prioridad MFA y no devuelve mensajes internos. El mock/contratos cubren el boundary; el PG17 ejecutó la migration y las aserciones, pero no un servidor PostgREST.

**Scope propuesto: 13 paths**

- `web/functions/_lib/admin-bff.ts`
- `db/migrations/20261025_h3_admin_members_onboarding_forbidden_status.sql`
- `tests/h3_admin_bff_mock_uat.mjs`
- `tests/sql/h3_admin_quota_harness.sql`
- `tests/test_security_flow.py`
- `tests/test_h3_admin_onboarding_denial_contract.py`
- `.context/componentes/admin_runtime.md`
- `.context/componentes/database_migrations.md`
- `.context/componentes/pruebas_evidencia.md`
- `.context/evidencia/h3req1_d04_onboarding_forbidden_2026-10-25.md`
- `.context/indice.md`
- `.context/trazabilidad/registro_fuentes_componentes.json`
- `.context/trazabilidad/registro_fuentes_componentes.md`

Quedan fuera los dos WIP PostgREST: `tests/h3_admin_quota_postgrest.mjs` y `tests/sql/h3_quota_postgrest_fixture.sql`; el segundo es precisamente el delta excluido por el addendum. No publicar esos paths ni el resto del WIP por implicación. Los tests focales previos son: mock BFF 127 checks; cuatro funciones de contrato Python y una función de seguridad invocadas directamente (no pytest); Edge mock agregado; revisión Codex Security del diff 0 reportables (estática); ahora PG17 roots PASS. No hay ejecución del cliente PostgREST, documentación global PASS, publicación, check de PR ni prueba Development renovada. Por ello el paquete de publicación queda **pendiente** de resolver o declarar el fallo real del gate documental con manifiesto candidato válido; una aprobación de publicación no se solicita todavía. Un futuro PR tampoco cerrará D04 remoto: requiere autorización protegida separada, integración/despliegue y comprobación una vez sobre el artefacto nuevo. El histórico 502 no se atribuye definitivamente a esta incompatibilidad.


## Gate documental del checkout — 2026-10-25 21:01 UTC

Docker studiamatch-dev:local, bind read-only, network none: self-test exit 1 por dos rutas C03 override registradas ausentes/fuera del snapshot; gate normal exit 1 con 353 diagnósticos C03/WIP (200 impresos y 153 adicionales). Ambos verifican 737/737 fuentes asignadas, 115/115 documentos activos alcanzables y 433/433 históricos catalogados/enlazados. No se usó un manifiesto de otro candidato. No se tocaron checker ni relaciones para ocultar el bloqueo. Estado de publicación D04: PENDIENTE hasta preparar un snapshot-manifest sucesor exacto, ejecutarlo con --candidate-manifest --self-test y resolver cualquier discrepancia real sin incluir WIP ajeno.

## Reconciliación del gate y scope D04 — 2026-10-25

La invocación exacta de CI reveló que el delta D04 no estaba representado por la selección R20 de #503: la migration y la prueba Python eran dos fuentes `candidate_only` nuevas, por lo que el checker reportó `294 != 292`; además, el encabezado Markdown no generaba el anchor con prefijo `database-`, y la evidencia D04 no estaba clasificada como documento activo. R19/R20 permanecen intactos.

Correcciones locales: el heading de la ficha de migrations ahora coincide con el anchor canónico; la evidencia D04 quedó en `active_documents`; el registro refleja la ejecución PG17 sintética aprobada (sin atribuir ejecución remota), y el Markdown generado se volverá a renderizar. R21 conserva las 297 entradas de selección R20 y añade solo los dos sources D04, total 299; los artifacts son la evidencia D04 y el manifiesto exacto del PR. El manifiesto exacto propone 19 paths y excluye expresamente `tests/h3_admin_quota_postgrest.mjs` y `tests/sql/h3_quota_postgrest_fixture.sql`. El workflow apunta a R21 y ejecuta el contrato Python en pytest. El scope guard agrega esos paths exactos y conserva la regresión R20 de #503 junto con negativos vecinos.

Estado de esa revisión a las 21:01 UTC: **preparación local; gate Docker y revisión final de scope pendientes**. No se hizo push, PR, merge, deploy ni SQL remoto. El PG17 autorizado pasó una vez con los markers del harness; no se repite. D04 no queda cerrado en Development: se necesita publicar/integrar el candidato con permiso separado, comprobar el deployment y probar el consumidor PostgREST/BFF real bajo user/Admin con las pruebas remotas aprobadas. El 502 histórico conserva causa no demostrada.

## Reconciliación posterior y revisión por impacto — 2026-10-25 21:22 UTC

El gate CI anterior reveló una aserción fuera del candidato: la cuarta función de `tests/test_h3_admin_onboarding_denial_contract.py` leía `tests/h3_admin_quota_postgrest.mjs` y `tests/sql/h3_quota_postgrest_fixture.sql`, dos paths WIP excluidos de los 19 paths de PR. La prueba había pasado solo en el árbol de trabajo que contenía esos cambios; no era reproducible desde el contenido publicado. Se eliminó esa aserción, se conservaron ambos WIP sin cambio y se actualizó la ficha/registro para describir exclusivamente las tres funciones del contrato incluidas. El test vuelve a probarse sin referencias a esos dos paths.

Resultado Docker posterior a la corrección: `pytest` ejecutó las tres funciones del contrato D04 más el test focal `test_admin_invitation_bff_sanitizes_internal_edge_business_codes` (**4 passed**); el contrato del workflow pasó 13/13; TypeScript `--noEmit --incremental false` pasó; el mock BFF pasó 127 checks; el parser `js-yaml` aceptó `.github/workflows/security-audit.yml`; el scanner de credenciales pasó en los 19 paths incluidos. La regresión de scope protegido pasó con `candidate_paths=1196`, 13 catálogos, 1,173 targets y negativos de rutas ordinarias, separadores, controles, malformed y H3 no manifiestas; `bash -n` pasó para ambos scripts del guard. R21 mantiene exactamente las 297 entradas R20 más los dos sources D04, total 299; se renderizó el registro generado y el gate exacto `--self-test --candidate-manifest h3req1_d04_candidate_docs_scope_2026-10-25.json` terminó `DOC_SELF_TEST_PASS` y `DOC_GATE_PASS`, con 737/737 fuentes asignadas, 737/737 estructuralmente enlazadas, 116/116 documentos activos alcanzables y 433/433 documentos históricos catalogados/enlazados. El manifiesto de PR conserva exactamente 19 paths y excluye los dos WIP.

Revisión de código: la migration se limita a las dos firmas fijas, exige el marker/mapeo del wrapper, reemplaza una sola frase legacy por SQLSTATE `42501`, vuelve a comprobarla y no cambia grants, signature, filas ni cuota. El harness aprobado confirmó Admin sintético permitido y user sintético rechazado con 403/cero columnas de membresía; el mock BFF cubre 403 sanitizado, prioridad MFA y fallos genéricos. El mapeo no identifica retroactivamente la causa del 502. No se encontró un nuevo bypass de authz, exposición de datos, secreto o ampliación de allowlist en la revisión focal de los paths incluidos.

Limitaciones de este corte: `actionlint` y `shellcheck` no están instalados en la imagen, así que no se atribuyen esos checks; el YAML se validó con `js-yaml`, los scripts con `bash -n` y el test de contrato del workflow. La revisión Codex Security iniciada antes de retirar la dependencia de WIP conserva su digest anterior y no debe citarse como scan del snapshot final; se registra como fase en curso, no como cierre de seguridad. No hubo push, PR, merge, deployment ni SQL remoto. D04 permanece parcial/bloqueado para aceptación Development hasta integrar la migration/BFF con permiso separado y comprobar una vez los caminos PostgREST/BFF Admin y user en el deployment identificado.

## Revisión de seguridad y paquete D04 — 2026-10-25 21:29 UTC

El gate R21 del candidato exacto pasó en Docker: `DOC_SELF_TEST_PASS` y `DOC_GATE_PASS`, con 737/737 fuentes asignadas y estructuralmente enlazadas, 116/116 documentos activos alcanzables y 433/433 históricos catalogados/enlazados. Se retiró la dependencia de WIP de la prueba D04; el paquete queda en 19 paths exactos y conserva fuera dos archivos PostgREST WIP. Las pruebas focales Docker registradas en el corte actual pasaron: pytest 4/4, mock BFF 127 checks, contrato del workflow 13/13, TypeScript, parseo YAML con `js-yaml`, scanner de credenciales y regresión del scope guard.

Codex Security scan `d77c88cd-7f9e-4984-a33b-9fe60c6b1315` completó con cero findings. Reporte sellado: `/home/romel/.codex/state/plugins/codex-security/scans/studiamatch-h3req1-d04-onboarding-denial-20261025/6b3ec2d5cc647f81e05fe99cb1b48b39658a1e87_20261025T211638Z_p6albuti/report.md`. El snapshot `codex-security-snapshot/v1:sha256:630f98fa3f2c12082f70a95f315f040b622106261b6b066d22685b53c8a4ec2d` se creó antes de retirar la aserción que dependía de WIP excluido; la aserción final y las 19 rutas actuales fueron revisadas manualmente. La cobertura es estática/local y no valida el PostgREST ni el runtime Development. El 502 histórico no tiene una causa demostrada.

El candidato sigue sin publicar: worktree `/home/romel/src/studiamatch-h3req1-d04-onboarding-denial-20261025`, rama `feat/h3req1-d04-onboarding-denial-20261025`, baseline `6b3ec2d5cc647f81e05fe99cb1b48b39658a1e87`; manifest `h3req1_d04_candidate_pr_scope_2026-10-25.json` enumera 19 paths incluidos y dos exclusiones exactas. No hubo commit, push, PR, merge, deployment ni SQL remoto. Requiere autorización nueva de commit/push/PR protegido a `desarrollo`; después harán falta checks GitHub, revisión humana, integración/deployment autorizados y una sola revalidación remota de las rutas Admin/user afectadas. `actionlint` y ShellCheck siguen sin estar instalados y no se declaran PASS.

## Revalidación local posterior del paquete D04 — 2026-10-25 22:25 UTC

El estado de 21:29 UTC se conserva como histórico. En una comprobación posterior, sobre el mismo worktree/HEAD y sin modificar los archivos bajo prueba, `actionlint` 1.7.12 en contenedor pasó `.github/workflows/security-audit.yml` (exit 0) y ShellCheck 0.11.0 pasó `scripts/security/protected_path_scope_guard.sh` y `tests/test_protected_path_scope_guard.sh` (exit 0). Se usaron mounts read-only y red Docker deshabilitada; no se accedió a secretos ni a servicios remotos.

La revisión Codex Security final registrada para el snapshot del candidato es scan `10dccbf2-0d3a-4f92-906b-df855503f804`, digest `codex-security-snapshot/v1:sha256:8ade5ba59e666422724ee5c1266be82281981e532f25a5e660dce52a3735d8cc`, cero hallazgos reportables y cuatro superficies. Es revisión estática/local; no demuestra la causa del 502 histórico ni comportamiento de PostgREST/Development. La referencia anterior al scan `d77c88cd-7f9e-4984-a33b-9fe60c6b1315` queda histórica y no reemplaza esta revisión final.

El paquete sigue en 19 paths incluidos, con `tests/h3_admin_quota_postgrest.mjs` y `tests/sql/h3_quota_postgrest_fixture.sql` excluidos. HEAD/base continúan `6b3ec2d5cc647f81e05fe99cb1b48b39658a1e87`; el diff continúa local y sin publicar. Estos dos checks y la revisión no autorizan commit, push, PR, merge ni deployment; el permiso de publicación sigue pendiente.

Tras registrar este delta, el gate Docker R21 se ejecutó con red deshabilitada, checkout read-only y `h3req1_d04_candidate_docs_scope_2026-10-25.json`: `DOC_SELF_TEST_PASS` y `DOC_GATE_PASS`; 737/737 fuentes asignadas/enlazadas, 116/116 documentos activos, 433/433 históricos, 9.283 enlaces y 4.641 anchors. Relaciones remotas: 9/15 verificadas y 6 pendientes. La edición se limitó a evidencia ya incluida en el manifiesto de 19 paths; no se generó código ni operación remota.

## Autorización y corte de publicación — 2026-10-25 22:46 UTC

El corte anterior de 22:25 UTC conserva correctamente que todavía no existía permiso de publicación en ese momento. La instrucción humana vigente autoriza ahora, y solo para este candidato, un commit aditivo, push no forzado y apertura de PR protegido hacia `desarrollo` limitados a los 19 paths incluidos en `h3req1_d04_candidate_pr_scope_2026-10-25.json`. La autorización incluye únicamente el Preview automático de esa publicación. Los dos archivos WIP PostgREST permanecen excluidos. No incluye merge, deploy manual, `workflow_dispatch`, cambios de protección ni aplicación SQL remota.

El criterio asociado en la atestación cliente sanitizada y su resumen es preservar el rol como autoridad de permisos: la identidad `user` no obtiene lectura administrativa. El escenario D04 mide esa denegación; no constituye un CA independiente ni demuestra por sí solo el 502 histórico. El 502 remoto anterior sigue sin causa demostrada. La publicación prepara el cambio compatible; la verificación real de PostgREST/BFF en Development requiere integración, deployment y permisos agrupados separados.

## Diagnóstico del primer check de #504 y corrección local — 2026-10-25

El SHA publicado `e073f8883e8bfb56368d8706b1716f8b1067fb87` obtuvo nueve jobs exitosos, un job saltado y una falla en `Python Compile And Tests`; por ello el agregador `security-audit` también falló. El fallo único fue `tests/test_h3_admin_queue_ux_contract.py::test_queue_pagination_rejects_null_limits_in_rpc_and_signed_dispatcher`: su contrato espera que el harness preserve `FOR i IN 1..119 LOOP`, pero el delta D04 había colocado las nuevas lecturas de membresía antes del límite de cuota y había cambiado el literal a `118`.

Corrección local mínima en `tests/sql/h3_admin_quota_harness.sql`: se conservaron sin cambios las aserciones de rol Admin/User, se movieron después del bloque que comprueba el límite y se restauró el bucle de 119 iteraciones. No se alteró la aserción ni la lógica de cuota; no se incluyó ninguno de los dos WIP PostgREST excluidos. El SHA-256 actual del harness es `a783d3bbfd94d2bc756c7d26a4c22a7d46f54aa91772b5897c78c299f9d73c16`.

Revalidación Docker read-only: `tests/test_h3_admin_onboarding_denial_contract.py` y `tests/test_h3_admin_queue_ux_contract.py` pasaron 16/16, incluido el test que falló en CI; `git diff --check` pasó. El gate documental candidate-aware del checkout D04 pasó con el manifiesto `.context/evidencia/h3req1_d04_candidate_docs_scope_2026-10-25.json`: `DOC_SELF_TEST_PASS`, 737/737 fuentes asignadas, 116/116 documentos activos alcanzables, 433/433 históricos enlazados, 9.283 enlaces y 4.641 anchors. El PG17 sintético previo corresponde al harness anterior y no se reutiliza para esta nueva disposición. La rama de trabajo conserva dos archivos WIP PostgREST modificados, fuera del manifiesto; no se staging ni se incluyeron en el commit/árbol remoto. El nuevo job PostgreSQL DB Change Gate debe validar el harness corregido tras una publicación adicional autorizada.

El PR permanece abierto y sin merge. La ejecución actual no actualizó remotamente el commit ni la descripción; el check rojo sigue siendo el resultado vigente del SHA publicado. Para cerrar este hallazgo falta autorizar el commit aditivo y push no forzado de esta corrección dentro del mismo manifiesto exacto de 19 paths, actualizar la descripción con el fallo y su corrección real, y esperar el conjunto de checks del nuevo SHA. El job PWI Worker Contract exitoso es de Actions y no acredita el check de la GitHub App.
