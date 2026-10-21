# Paquete de integración Development H3REQ1 — R19

> **Estado: NO-GO Development; aún no actualizar el PR 501.** Este sucesor parte del baseline y contiene el snapshot R18 reconciliado más los deltas R19 seleccionados. Preserva R8/R9/R12/R13, R14–R18 y sus evidencias. El checkout Syncthing no se sincroniza ni publica. No incluye WIP automáticamente.

## Candidato, base y alcance

- Repositorio: `https://github.com/romelhc95/studiamatch`; target final `desarrollo`.
- Base exacta: `4eb4d877a50b012bb630a129bd0c74482c33be9c`. El sucesor local está en `/tmp/h3req1_r19_publication_prep_20261018`, rama `feat/h3req1-sync-20261018-r19`; PR 501 ya existe en el SHA remoto anterior. Este sucesor sigue sin commit, push o actualización del PR, y no tiene deployment Pages.
- R18 histórico permanece en `/home/romel/src/studiamatch-h3req1-publication-prep-r18`, HEAD `0d7c89dccffd1146b6cc669d4994787e9b78b533`, árbol `332ae4d156863c1f5524e7d5f6c8f1ecb4424dc2`. La fuente Syncthing permanece intacta en HEAD `a57bc415257ab8154d40d7c71d34c69d0bdaeb0d`; no se trasladan sus 19.510 entradas WIP.
- El delta R18 reconstruido respecto del baseline tiene 1.143 rutas sin detección de renombres: 1.050 altas, 86 cambios y 7 bajas; dos renombres se contabilizan como alta+baja. R19 sustituye 46 PNG por un placeholder neutral y excluye dos WEBM; conserva los originales en fuentes históricas locales. Ningún original visual se vuelve a cargar.
- R19 añade reporte remoto, esta ficha, cuerpo PR con la plantilla versionada, log de checks, revisión independiente, manifiesto y nota de tratamiento visual. Los tres documentos con referencias a video apuntan a la nota R19. No reabre la reorganización Obsidian.
- Se mantiene `braces@3.0.4-h3.1`; no se cambia lockfile ni tarball. No se declara release oficial upstream ni waiver.

## Permisos y estado de consumo

- A: aprobado y consumido una vez en Free en el alcance del paquete R18. No repetir; Pro queda de solo lectura.
- B: aprobado en alcance exacto, con efectos parciales observados. No volver a pedir aprobación. El responsable confirmó manualmente el key ID Text en Preview y aceptó temporalmente la versión Worker #2 como baseline hasta el 2026-10-25 23:59 UTC; eso no autoriza otro deployment ni rollback. El candidato Pages R19 no está desplegado y B/runtime no se declaran completos.
- C: alternativa retentiva aprobada, no consumida. Depende de B, D01/D02 con la identidad Outlook existente y lectura administrativa de las dos notificaciones Auth en estado deshabilitado. No DELETE físico. Gmail permanece intacta.
- D: aprobado, no consumido. La interacción del responsable en navegador sigue siendo necesaria. Sin secretos, códigos MFA o links por chat.
- `main`, Certification y Production siguen fuera de alcance. No cambiar rama default, bypass, autoaprobar ni relajar checks.

## B — lecturas y discrepancias actuales

El reporte [R19 remoto](h3req1_g10_remote_preparation_2026-10-18_r19.md) distingue los datos del conector de la confirmación humana.

**Leído por conector, sin valores secretos ni filas operativas:**

- Pages Preview tiene `ADMIN_QUOTA` como Service binding al Worker esperado, los tres nombres HMAC con tipo secreto, `ADMIN_ALLOWED_HOSTS` y URL Free compatibles. En la lectura inicial del conector, `ADMIN_RPC_GATEWAY_KEY_ID` no estaba presente; después, el responsable confirmó manualmente que la variable Text con el identificador acordado sí aparece en Preview. Los dos flags locales no están configurados. Preview comparte configuración con Certification.
- Worker `studiamatch-admin-quota` y namespace `AdminQuotaCounter` están vinculados por nombre/clase. `workers.dev` está desactivado. La lista de deployments muestra versiones 1 y 2 en dos eventos diferentes. El responsable aceptó la versión #2 como baseline temporal hasta el 2026-10-25 23:59 UTC; la excepción reconoce el exceso frente al límite original y su riesgo runtime no probado, y no autoriza otro deployment o rollback.
- Free `admin-invite` está ACTIVE v14 con `verify_jwt=true`; el código remoto coincide byte por byte con R18 local. Supabase connector no tiene getter de presencia/nombres de Edge secrets.
- No hay deployment Pages R19 ni candidato servido.

**Confirmación manual recibida:** el responsable confirmó en Supabase Dashboard → Free → Edge Functions → Secrets que `ADMIN_QUOTA_HMAC_KEY` y `NEXT_SUPABASE_SECRET_KEY` están presentes y que la primera coincide con Pages Preview. También confirmó después que el key ID Text aparece en Pages Preview y que su HMAC de gateway coincide con el valor guardado en Supabase Vault. El conector no puede verificar esas comparaciones ni leer valores, y no volvió a consultar la variable Text. En Pages Preview, `NEXT_SUPABASE_SECRET_KEY` no está presente, conforme al paquete R18: el BFF no la consume y Pages no debe alojar una clave `sb_secret_`.

**Solicitud nueva, aún no ejecutada:** el responsable quiere rotar `NEXT_SUPABASE_SECRET_KEY`. Supabase Dashboard → Free → Project Settings → API Keys → Secret API keys es el origen para crear una nueva clave `sb_secret_`. La rotación no está incluida en B: requiere un paquete JIT aparte que inventaríe consumidores Development, actualice y verifique primero Edge `admin-invite` y los demás stores autorizados y retire la anterior al final. No ponerla en Pages Preview, no pegarla en chat/capturas y no borrarla antes de confirmar todos los consumidores. No se ha generado ni cambiado ninguna clave.

**Estado restante:** el responsable ya aceptó la versión Worker #2 como excepción temporal y confirmó manualmente el key ID y la paridad HMAC; no se repite esa solicitud. No existe deployment ni smoke remoto Pages R19; el smoke de aplicación local se documenta más abajo y no cierra B. Mantener el riesgo de compatibilidad Worker sin prueba remota hasta la aceptación autorizada. No activar el pre-request. La publicación podrá crear un Preview compartido con Certification, pero la integración y el merge quedan bloqueados hasta resolver el gate confiable PWI sin debilitar protecciones. La rotación `NEXT_SUPABASE_SECRET_KEY` no pertenece a B y requiere paquete JIT independiente.

## Ruta GitHub y publicación

- GitHub confirma `desarrollo` protegida y en el baseline. Las capturas del responsable muestran PR requerido, una aprobación, dismissal de approvals obsoletas, aprobación del último push por persona distinta, `security-audit` requerido, rama al día, bypass no permitido y force pushes/deletions deshabilitados.
- El conector recibió 403 al leer branch protection detallada; no acredita reglas organizacionales ocultas. No hay job PWI en el run actual. GitHub documenta que `pull_request_target` toma el workflow del default branch (`main`), por lo que un bootstrap solo a `desarrollo` no habilitaría PWI ([evento](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows), [modelo de confianza](https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target)). El paquete de bootstrap a `desarrollo` descrito antes queda invalidado; no se cambia el límite de confianza, no se modifica `main`, no se usa bypass ni se cambia la rama predeterminada. No se encontró una ruta confiable existente en el repo para habilitarlo dentro de desarrollo.
- PR 501 ya existe en el SHA anterior. El responsable informa que el aprobador ya lo aprobó; no se volvió a leer la review. Un push del sucesor invalida esa aprobación por dismissal de reviews obsoletas, así que se requiere una revisión humana nueva sobre el SHA vigente. No se hará force push.
- Publicar solo cuando B de configuración y las condiciones protegidas estén satisfechas; actualizar el PR 501 existente hacia `desarrollo`, no crear otro PR equivalente. La revisión debe venir de una persona distinta de autora y pusher. No se autoaprueba ni se mergea sin `security-audit` verde y aprobación válida en el SHA actual.

## Checks del PR y alertas Code Scanning — seguimiento 2026-10-19

La lectura GitHub actual del PR 501 confirma que sigue abierto, dirigido a `desarrollo`, y que su SHA publicado es `d5220185cbb8d1975ebb901a5d6e8e77636b8b02`. La review `APPROVED` del aprobador corresponde a ese SHA anterior. No se reutiliza: el push sucesor descartará reviews obsoletas según la protección observada por el responsable.

El último workflow remoto disponible, run `39177784316` para ese SHA, no se ejecutó sobre las correcciones locales:

| Check remoto (SHA anterior) | Resultado | Corrección del candidato / límite |
|---|---|---|
| Documentation Source Registry | PASS | No cambió después de ese run; se revalidó localmente tras registrar las tres pruebas de regresión. |
| TypeScript Typecheck | PASS | No cambió TypeScript de la aplicación; el UAT Edge añadido se ejecuta en Static Build. |
| Protected Path Integrity | PASS | No sustituye al scope guard R19 ni al PWI confiable pendiente. |
| Credential Scan | PASS | El scanner y el alcance del nuevo candidato se revalidaron localmente en Docker. |
| ESLint | PASS | El run es del SHA anterior; fuentes de interfaz no cambiaron. |
| Python Compile And Tests | FAIL | Faltaba `tests/test_h3req1_c03_docker_daemon_identity_f2d.py` en el SHA publicado; ahora está incluido y las suites afectadas pasan localmente. |
| Static Build | FAIL | Faltaba `tests/h3_admin_auth_error_uat.mjs`; ahora está incluido. Los UAT afectados pasan; el smoke de aplicación local R19 responde HTTP 200. |
| actionlint And shellcheck | CANCELLED | actionlint se reejecutó localmente sobre el workflow; ShellCheck focal se reutiliza con el mismo SHA de sus scripts sin cambios. |
| PostgreSQL DB Change Gate | FAIL | Falló al intentar ejecutar el archivo de configuración como binario (exit 126). El workflow ahora invoca `/bin/postgrest /etc/postgrest.conf` y deja el bind config en modo 0644. No se ejecutó un gate DB completo adicional: la fixture PG17 con DDL/DML requiere JIT separado. |
| H2 Main Production Expand Gate | SKIPPED | Es ajeno al objetivo Development y no se solicita para este ciclo. |
| security-audit (agregado) | FAIL | Agregó los fallos anteriores en el SHA publicado; no existe resultado nuevo para las correcciones locales. |

Los diagnósticos CodeQL de ese PR (1 regex/ReDoS, 1 sanitización incompleta y 2 avisos SSRF de fixtures) tienen correcciones y regresiones locales en el sucesor. El nuevo análisis CodeQL del sucesor aún no existe.

Las cuatro alertas Code Scanning que el responsable mostró abiertas en `main` tienen estos estados:

| Alerta | Corrección incluida en el candidato | Prueba local | Estado remoto acreditado |
|---|---|---|---|
| #15 — clear-text storage en `taxonomy_roi_audit.py` | El reporte deja de almacenar detalle por fila y conserva conteos agregados. | `tests/test_taxonomy_roi_audit_privacy.py` | La captura del responsable mostraba `main` abierta. No hay análisis posterior ni promoción; permanece sin cierre remoto acreditado. |
| #16 — regex ineficiente en `universal_harvester.py` | Detección lineal de grupos cuantificados; `regex` con timeout de 50 ms y fallo cerrado ante dependencia ausente o timeout. | `tests/test_h3req1_local_pipeline_walk.py` | Mismo límite: alerta `main` abierta en la captura; requiere CodeQL tras publicación y promoción regular para llegar a `main`. |
| #17 — sanitización parcial de URL en `site_diagnostics.py` | Comprobación por hostname analizado, con host exacto/subdominio autorizado. | `tests/test_site_diagnostics_security.py` | Mismo límite: alerta `main` abierta en la captura; no se obtuvo lectura actual del endpoint Code Scanning. |
| #18 — stack trace en `send-lead-emails` | La falla externa devuelve un cuerpo 500 genérico sin detalle ni stack. | `tests/h3_send_lead_error_uat.mjs`, ejecuta el handler real con fallo simulado. | Mismo límite: alerta `main` abierta en la captura; necesita análisis nuevo y promoción protegida. |

El conector GitHub rechazó la lectura de `code-scanning/alerts` (endpoint no permitido); por eso la captura del responsable es la última evidencia visual del estado remoto. Los cuatro cambios de código locales no cierran alertas en `main`; primero deben pasar el PR protegido a `desarrollo`, luego la promoción regular a `certificacion` y `main`.

## Docker y ejecución local del candidato — seguimiento 2026-10-19

- El servicio estable `studiamatch-dev` corre la imagen `studiamatch-h3req1:sync-a57bc415-rebuilt-20261018`, monta el checkout de origen `/home/romel/src/studiamatch-h3req1-sync-20261002` en `/app` y `studiamatch_h3req1_node_modules_recovered_20261018` en `/app/web/node_modules`; health `healthy`, reinicios `0`. `/admin/login/` responde HTTP 200.
- La imagen aislada candidata `studiamatch-dev:r19-20261018` es `sha256:460484fdb765674851a450473d88778336ac5402cb171580e3b0c0beca188255`. El `package.json` y `package-lock.json` de origen, candidato e imagen coinciden byte a byte. El volumen R19 de 733 MB contiene Next y React y su marker corresponde a esos manifiestos.
- En una copia temporal Docker del frontend R19, con fuentes del candidato montadas `read-only`, dependencias colocadas dentro de la copia para respetar el límite de raíz de Turbopack y variables Supabase sintéticas, `npm run dev` quedó listo y `/admin/login/` respondió HTTP 200. La prueba no inició sesión, no contactó Supabase y no es aceptación remota.
- El primer smoke con un symlink de `node_modules` fuera del árbol fue rechazado por Turbopack; se conservó como intento fallido del harness y se corrigió la forma de montar dependencias. El smoke final con copia interna fue PASS. No se cambió ningún lockfile.
- El mock static build R19 ya ejecutado en Docker pasó con salida `h2_web_mock_smoke_ok`; la interfaz/lockfile no cambiaron después. Es evidencia local, no deployment Pages.
- El manifiesto R19 detectó antes de esta revisión pins obsoletos del estado, registro fuente y prueba de pipeline, y tres pins `catalog_reference_closure` para archivos de código corregidos. El sucesor se mantiene NO-GO hasta reconciliar esos bytes, repetir los gates afectados y completar la revisión independiente final.

## Secuencia preparada, aún no ejecutable

1. Preservar Worker #2 como baseline bajo la excepción aceptada hasta 2026-10-25 23:59 UTC; no hacer upload, rollback o cambio de binding no listado.
2. La confirmación manual del key ID Text, presencia Edge y paridad HMAC ya está registrada. No activar gateway pre-request todavía.
3. Mantener las validaciones locales y revisión final registradas; resolver el gate PWI en `desarrollo` sin cambiar su checkout confiable, y confirmar el alcance efectivo de branch protection con el admin.
4. Solo después: publicar el sucesor sin force push y actualizar PR 501; verificar checks en el SHA exacto y obtener revisión humana nueva. No mergear antes de esas condiciones.
5. Merge protegido a `desarrollo` tras aceptación válida; identificar Pages deployment, SHA, hostname, Worker y Edge activos. No usar `admin.studiamatch.com` como Development.
6. Antes de C, ejecutar D01/D02 con la identidad Outlook anterior y confirmar el estado vigente de Gmail. C usa solo el RPC auditado, cambio de correo antiguo a `example.invalid`, bloqueo y retiro TOTP; conserva Auth row, referencias, invitación accepted y auditoría. Detener si el bloqueo no rechaza operaciones Admin o si requiere revocación no incluida.
7. Tras C, invitar Outlook otra vez desde Gmail con intervención del responsable, verificar UUID nuevo de forma privada y completar D03; continuar D04–D14 y 11 grupos de regresión adicional dentro de límites de D.

## Reconciliación acotada del gate documental

La validación del snapshot R19 reveló un defecto del checker, no de la reorganización: el JSON canónico marca 367 rutas como `candidate_only_paths`; 103 no seleccionadas y 40 referencias de evidencia a esas mismas rutas pertenecen al WIP excluido. El snapshot también omite 16 rutas de exclusión de fuentes y 4 rutas de exclusión documental que el registro enumera exactamente. Se corrigió el checker para que solo el modo con manifiesto exacto tolere ausencias expresamente registradas en esas listas y no seleccionadas; cada ruta seleccionada por manifiesto debe existir y una ausencia no listada sigue fallando. El modo normal de checkout completo conserva su exigencia. Se añadieron cinco artefactos concretos que el registro sí referenciaba fuera de esas listas, tras revisión de ruta y scanner.

La primera lectura histórica del R19 usó fallback Node en host mientras Docker fallaba. En el seguimiento actual, el checker Docker informa 711/711 fuentes asignadas; 113/113 documentos activos alcanzables; 433/433 históricos catalogados y enlazados. El self-test incluye negativos para fuente no asignada, omisiones no permitidas, rutas/anchors inexistentes, relaciones inválidas, índice duplicado y documento retirado presente. Los pins de estado, registro fuente, test y cierre de referencias detectados desfasados se reconcilian en el manifiesto sucesor actual antes del gate final.

Cinco relaciones de evidencia adicionales no estaban en el alcance R18 y no pertenecían a `candidate_only_paths`. Se incluyeron individualmente porque el registro canónico las cita: dos logs ignorados, dos artefactos pequeños de UAT y una lista de hashes de inputs. Un scan sobre esos cinco archivos halló cero credenciales, correos, UUID o asignaciones de sesión. No se añadió ningún otro WIP. El guard independiente sigue comprobando 13 catálogos y 1.173 destinos.

## Transición, límites y recuperación

| Etapa | Acción / gate | Efectos y límite |
|---|---|---|
| `expand` | A ya aplicado en Free; no repetir. Las confirmaciones de Preview/Edge son manuales; el conector no leyó valores. | Pro solo lectura; no DDL/DML adicional, datos operativos, claves leídas ni escritores. |
| `compatibilidad` | Worker/DO, Preview compartido y Edge v14 identificados; Worker #2 aceptado temporalmente y key ID/HMAC confirmados por el responsable. | No activar pre-request; candidato Pages aún no servido; preservar Certification. |
| `deploy` | No hay Preview del SHA feature ni deployment Development del candidato. Merge protegido debe identificar su deployment real. | No deployment/retry/rollback adicional de Worker. Excepción temporal hasta 2026-10-25 23:59 UTC. Timeout 10 min; cero retries automáticos; ante timeout releer deployment antes de decidir. |
| `contract` | Solo tras aceptación y estabilidad, conforme a plan; no ocurre en este paquete. | Sin contracción en esta fase; conservar schema expandido. |
| `rollback/recuperación` | Preferir retorno al deployment compatible ya existente y detener nuevas mutaciones. | No restaurar DB, borrar DO/namespace, purgar cuota/auditoría ni rotar secretos. Cualquier despliegue/rollback adicional exige paquete JIT. |

## Aceptación y evidencia

D01–D14: 0/14 acreditados en remoto para este candidato. Regresión adicional: 0/11. No hay deployment Pages R19, aceptación cliente, onboarding nuevo ni resultado runtime. El último-admin requiere escenario remoto aislado y permiso adicional si no puede validarse sin tocar Gmail u otras identidades protegidas. Catálogo, discovery/pipeline y aceptación de producto no se fabrican con scraping, LLM, ETL cloud ni writers productivos.

Cualquier intervención humana se solicitará en bloques pequeños con objetivo, URL, cuenta, efectos y resultado esperado. Contraseña, MFA, tokens y enlaces Auth solo se introducen en navegador; la confirmación humana no equivale a PASS técnico. No capturar valores en screenshots/logs. Si no llega confirmación, mantener checkpoint y avanzar tareas independientes.

## Gates y dueños

| Gate | Estado R19 | Próximo responsable |
|---|---|---|
| B secretos Edge/Preview | Cotejo humano recibido; sin valores compartidos | Codex registra la confirmación, no la atribuye al conector. La rotación consultada queda fuera de B y pendiente de paquete JIT. |
| B deployment Worker | Versión #2 aceptada como baseline temporal hasta 2026-10-25 23:59 UTC; riesgo runtime todavía no probado | Responsable Cloudflare: conservar metadata y no iniciar otro deployment/rollback. |
| B key ID gateway | Responsable confirmó manualmente el Text en Preview y la paridad con Vault; no hay reread del conector | Sin nueva acción de configuración; preservar el secreto y no exponer valores. |
| GitHub protección/ruta | Capturas parciales acreditan protecciones clave; detalle endpoint 403; PWI no puede arrancar con un bootstrap solo en `desarrollo`, porque `pull_request_target` toma el workflow del default `main` | Sin intervención inmediata: no cambiar controles. Para habilitarlo dentro del alcance, el admin debe presentar un proveedor externo de check confiable ya aprobado, o preparar una decisión de arquitectura/configuración protegida por separado. `main` permanece fuera de alcance. |
| Docker/validaciones | PASS focal en Docker: 14 pytest, py_compile, scanner, guard/negativos, checker documental, `git diff --check`; actionlint PASS, ShellCheck reutilizado sin cambios. | No repetir suites intactas; validar por impacto ante cualquier cambio posterior. |
| Revisión independiente local | Veredicto integral del snapshot vigente registrado en `independent_review` del manifiesto R19, con su digest exacto | No sustituye approval GitHub del SHA nuevo ni las revisiones remotas pendientes. |
| Review GitHub | PR 501 existe; aprobación del SHA remoto anterior reportada por el responsable; aún no hay revisión del sucesor | Colaborador distinto de autora/pusher: aprobar el SHA vigente después de checks; stale review anterior no basta. |
| D01/D02, C y D | No ejecutados | Responsable participa en navegador; Codex observa y registra evidencia sanitizada. |

## Salida de GO

No declarar GO Development hasta candidato integrado y deployment identificado, protecciones efectivas/review/checks válidos, D01–D14 y regresión aplicable acreditados, aceptación cliente sanitizada, seis pilares satisfechos, rollback/transición documentados y ausencia de bloqueantes. R19 no satisface esos criterios.

## Addendum PWI R3 — corrección de carrera full-queue

La revisión independiente anterior encontró HIGH reproducible: con ocho filas activas y el evento actual ya `processing`, un webhook posterior del mismo SHA podía reabrir el check pero no quedar persistido. La alarma activa podía publicar un resultado calculado antes de la revocación. La fuente local `/tmp/studiamatch-pwi-r3-20261019` corrige este caso, redelivery fuera de orden y finalización tardía sin alterar esquema ni máximos 8/100. Docker ejecutó `node --check index.mjs`, Node 32/32, runtime Durable Object/SQLite 4/4 y `npm run check`; todos PASS en fuente candidata. El snapshot autónomo final, escáner integral, gates de documentación/manifest y revisión independiente exacta siguen pendientes; no se declara cierre local ni remoto con esas pruebas fuente.

El paquete ampliado `/tmp/h3req1_pwi_r3_full_queue_current_head_jit_delta_20261019_r2.md` está pendiente de aprobación separada. Añade lectura mínima del head del PR 501 cuando la cola está llena, reemplazo determinista de una fila activa (incluida fila `processing` únicamente cuando no hay otra elegible), resecuencia monótona de delivery `failed` y finalización condicional. Reutiliza, sin ampliar, R3 App/Worker/R3-DO y el JIT pre-ACK ya aprobados. No se instala la App, se ingresan secretos, se despliega el Worker ni se consume el paquete mientras R2 no esté aprobado y el snapshot final no pase revisión.

El PR 501 continúa abierto en `a73af141…`; su PWI fallido y su aprobación permanecen ligados a ese SHA. No existe check nuevo, deployment del candidato, integración, D01–D14 ni regresión remota. `main`, `certificacion` y Production continúan fuera.

## Reconciliación ejecutada — 2026-10-19 07:06 UTC

Esta sección sustituye estados anteriores del mismo documento cuando describen que Docker seguía detenido, que no existía Preview, o que los últimos resultados eran solo validaciones de 14 pruebas. No modifica R18 ni sus evidencias.

### Candidato local y Docker

- Workspace exacto: `/tmp/h3req1_r19_publication_prep_20261018`; rama `feat/h3req1-sync-20261018-r19`; HEAD `ef306edd91d339af3a9e0623217b49d86f1cdb1c`; base `4eb4d877a50b012bb630a129bd0c74482c33be9c`. El snapshot de publicación aún es un árbol local con cambios sin commit y se identifica por el manifiesto de 1.176 rutas y sus pins; HEAD solo no lo identifica.
- El contenedor habitual `studiamatch-dev` fue revalidado `running/healthy`, reinicios 0, imagen `sha256:bb30d6237846f120d39b7c9794f8eb0c938c69e8cc15e0e93d2ca03641a7ade1`. Monta `/home/romel/src/studiamatch-h3req1-sync-20261002`, no el candidato R19. `/admin/login/` responde HTTP 200. No se reconstruyó ni limpió ese contenedor.
- Los resultados Docker del candidato incluyen: static mock build `h2_web_mock_smoke_ok`; actionlint 1.7.7 y ShellCheck 0.11.0 PASS; proxy SSRF focal PASS con destinos PostgREST estáticos y `handleFunction` ejercitado; handler real `send-lead-emails` PASS con fallo simulado y cuerpo genérico 500; suites Python focales 21 passed/10 subtests y helper PWI 13 passed; tests de estado Obsidian 8 passed; scanner, guard/negativos, checker documental, referencias y `git diff --check` PASS. Son resultados locales, no resultados de Actions.
- Checker documental actual: 722/722 fuentes asignadas, 113/113 activos y 433/433 históricos. Manifiesto: 1.176/1.176 pins de scope y 1.173/1.173 referencias de catálogo cerradas. Guard: 1.182 rutas efectivas (unión de 1.176 rutas del scope y seis artefactos de paquete), 13 catálogos y 1.173 destinos. El cotejo actual encontró 32 diferencias POSIX `0644`/`0664` en artefactos históricos; las 37 entradas de artefactos coinciden en contenido, bytes y modo Git normalizado (`100644`). No se cambió ningún modo.

### Estado remoto consultado

- PR 501 continúa abierto hacia `desarrollo` en SHA `d5220185cbb8d1975ebb901a5d6e8e77636b8b02`, con run `39177784316` fallido. Aprobación registrada en ese SHA: no se reutiliza para un sucesor. No se ha creado commit nuevo, actualizado el PR ni ejecutado un push.
- GitHub run actual de ese SHA: documentación, TypeScript, Protected Path Integrity, credential scan y ESLint `success`; Python `failure` (faltaba el test directo del runner); Static Build `failure` (faltaba el UAT); PostgreSQL DB Change Gate `failure` (config PostgREST tratada como ejecutable); `actionlint And shellcheck` `cancelled` en actionlint y ShellCheck `skipped`; `security-audit` agregado `failure`; `H2 Main Production Expand Gate` `skipped` por estar fuera del ciclo. No hay resultados remotos nuevos del snapshot local.
- Cloudflare Pages Preview se releyó con campos filtrados: deployment `c7adff18-9a74-4eb2-9a08-83a5cc05da46`, `https://c7adff18.studiamatch-aty.pages.dev`, `success`, creado `2026-10-18T23:43:51Z`, branch `feat/h3req1-sync-20261018-r19`, SHA `d5220185cbb8d1975ebb901a5d6e8e77636b8b02`. Es el SHA remoto antiguo, no el delta local actual, y no se hizo smoke funcional allí. El Preview comparte configuración con Certification.
- PWI no produjo job: el workflow/helper están ausentes de `main`, que es la rama desde la que GitHub toma `pull_request_target`. Un bootstrap solo a `desarrollo` no funciona y queda cancelado como opción; no se rebajó el checkout ni los controles. No existe un check confiable alternativo verificado. `main` está fuera de alcance, así que PWI sigue sin resolución para este ciclo.

### Code Scanning: alcances distintos

Las cuatro alertas del PR 501 fueron reportadas sobre el SHA `d5220185…`: `Inefficient regular expression` High en `scripts/core/universal_harvester.py:316`; `Incomplete multi-character sanitization` High en `scripts/maintenance/h3req1_documentation_integrity.mjs:53`; y dos `Server-side request forgery` Critical en `tests/h3req1_c03_integrated_runtime.mjs:317` y `:348`. El candidato local contiene los arreglos y pruebas focales descritos arriba. GitHub no ha analizado el sucesor; por tanto, las cuatro disposiciones remotas quedan pendientes.

Revisión de seguridad independiente, solo lectura, sobre los fixes de código del digest `4bcc1d5a3a7155ac57fa2b645f5ae9b637d2cf5dd9c1499c307b2ea9df8e55d4`: 0 Critical, 0 High, 0 Medium, 0 Low y 0 bloqueantes reportados para las cuatro alertas de PR y las cuatro históricas de `main`. La revisión confirma los límites del regex con timeout/fail-closed, el saneamiento de anchors sin insertar HTML, destinos SSRF exactos, agregación privada ROI, host exacto/subdominio y error 500 genérico. No ejecutó pruebas; las pruebas focales locales quedan acreditadas aparte en el log Docker. No revisó los cambios documentales PWI añadidos después de ese digest. El resultado de revisión integral del snapshot exacto queda registrado exclusivamente en el bloque `independent_review` del manifiesto R19.

Las alertas históricas #15–#18 pertenecen a `main`, no al análisis del PR: #15 `Clear-text storage` en `scripts/maintenance/taxonomy_roi_audit.py:86`; #16 `Inefficient regular expression` en `universal_harvester.py:316`; #17 `Incomplete URL substring sanitization` en `scripts/shared/site_diagnostics.py:94` (commit analizado `70d0f4fee885be0f6780e5d14f466b2a6c897961`); y #18 `Information exposure through a stack trace` en `supabase/functions/send-lead-emails/index.ts:156`. La última captura aportada las mostró abiertas. El conector no ofrece un getter de alertas; no se declara ninguna cerrada remotamente. #16 es el mismo flujo regex que se solapa con una alerta del PR, no un quinto fix.

### Ruta protegida y siguiente gate

### PWI: bloqueo de rama predeterminada y decisión pendiente

GitHub documenta que `pull_request_target` toma el workflow de la rama predeterminada del repositorio y ejecuta código confiable de esa rama ([eventos](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows), [seguridad](https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target)). El default observado aquí es `main`. Por eso, añadir `.github/workflows/protected-workflow-integrity.yml` y `scripts/security/protected_workflow_review.py` únicamente a `desarrollo` no habilita el job para PR 501. El paquete `/tmp/h3req1_pwi_bootstrap_package_20261019.md` se invalida y no se publicará. Esta limitación ya constaba en R17; esta corrección solo actualiza R19 y no reabre la reorganización documental.

Dentro del alcance actual no se encontró una ruta local que haga confiable PWI en `desarrollo` sin editar `main` o cambiar el diseño/infraestructura del check. `main` está explícitamente fuera de alcance. Una alternativa sin depender del default branch sería un proveedor externo de checks confiable, por ejemplo una GitHub App instalada en el repositorio, que use código fijado fuera de la PR, valide las rutas protegidas y la aprobación vigente del SHA exacto, y publique `Protected Workflow Integrity` contra ese SHA. No hay una app así verificada o preparada. Su creación/instalación, permisos, servicio, secretos de integración y selección como source del required check son cambios administrativos protegidos y necesitan paquete concreto y autorización aparte. No se usará `pull_request` con YAML/script de la propia PR como sustituto confiable.

No se modifica `main`, la rama predeterminada ni las reglas; tampoco se usa bypass. PWI permanece bloqueante para cierre/merge hasta que exista una ruta confiable y autorizada.

No hay todavía cero fallos remotos para el sucesor: Python, Static Build, PostgreSQL, CodeQL, actionlint/ShellCheck y `security-audit` no tienen run en un SHA nuevo; PWI está bloqueado porque no existe un verificador confiable activo en el default branch y ese cambio está fuera de alcance. D01–D14 permanecen 0/14 y los 11 bloques adicionales 0/11. B permanece incompleto hasta que el sucesor servido en Preview pase el smoke autorizado y se documente la compatibilidad runtime. A está consumido; B/C/D continúan en sus alcances aprobados. Gmail y otros ambientes protegidos permanecen intactos. No GO Development.

## Corrección de manifiesto y gate local — 2026-10-19

La revisión de seguridad del paquete encontró una contradicción vigente en el manifiesto: siete dependencias exactas del Static Build estaban presentes y fijadas en el scope, pero también aparecían en `missing_static_build_inputs`. Se conserva esa lista bajo `historically_missing_static_build_inputs`, se registran los siete paths como resueltos y la lista vigente `missing_static_build_inputs` queda vacía. El recuento reconciliado del scope es 1.176 rutas: 89 modificadas, 1.080 no rastreadas y siete eliminadas; 37 no rastreadas están explícitamente ignoradas por Git y preservadas como tales. Frente al árbol remoto d522, el delta de publicación es 22 modificadas y 26 añadidas, sin eliminaciones, apto para fast-forward.

El cotejo de modo normaliza permisos POSIX a los modos que Git realmente almacena: 37/37 artefactos de contenido tienen bytes y modo Git coincidentes; el manifiesto R19 es la única entrada con `self_hash_excluded`. Las 32 diferencias POSIX `0644`/`0664` son solo variación del checkout y no requieren `chmod`. No se cambió contenido o modo histórico. El manifiesto R19 y el PR body registran esta resolución; revisión independiente exacta y gates remotos permanecen pendientes hasta sus resultados correspondientes.

La revalidación final de este corte pasó en Docker: checker/self-test documental (722 fuentes, 113 activos, 433 históricos, 13 catálogos), guard (1.182 rutas/1.173 referencias y todos los casos negativos), scanner sobre la selección exacta, suite contractual focal (130 pruebas, 10 subtests), contrato de plantilla (10 encabezados ordenados y 0 placeholders), `git diff --check HEAD` y no-index sobre 26 altas. Los 11 comandos Node directos del bloque Static Build están disponibles dentro del scope; esto comprueba integridad/selección local, no sustituye el job remoto. actionlint/ShellCheck pasan en imágenes aisladas. El detalle y los errores de invocación corregidos quedan en el log. El veredicto independiente exacto se conserva en el manifiesto; los checks remotos del nuevo SHA no existen y PWI sigue bloqueado por el default branch fuera de alcance, no por falta de un PR a `desarrollo`.

### Revalidación runtime de Static Build — 2026-10-19 08:18 UTC

El mock build del candidato volvió a completarse dentro de Docker con `h2_web_mock_smoke_ok` (Node 20.20.2). El primer traspaso del artefacto local falló por permisos de escritura del volumen temporal; se corrigió ejecutando solo ese contenedor desechable como UID 0. El código y la imagen de dependencias se montaron de solo lectura y no se alteraron lockfiles ni volúmenes habituales. Con `web/out` generado por ese build, los dos runtime UAT de la secuencia workflow se ejecutaron en Docker Node 22.22.0, red deshabilitada, Miniflare 4.20260730.0 y esbuild 0.25.10: `h3_admin_quota_runtime.mjs` PASS (25 concurrentes; 10 admitidas; persistencia y compatibilidad de payload anterior) y `h3_admin_safe_suspend_runtime_uat.mjs` PASS (3 rutas Admin suspendidas, 3 rutas públicas disponibles, 8 alias codificados rechazados y 4 cookies limpiadas). La ejecución anterior de safe-suspend sin el artefacto `web/out` fue un fallo de invocación que devolvió 404 y queda en el log; no se toma como prueba del producto. Ninguna prueba conectó con Supabase, Pages o un Worker remoto.

ESLint `npm run lint` conserva PASS (0 errores, 9 warnings existentes) y TypeScript `npx tsc --noEmit --incremental false` PASS sobre inputs sin cambios. actionlint 1.7.7 y ShellCheck 0.11.0 acaban de pasar en sus imágenes Docker separadas. Estos son resultados locales; seis gates remotos siguen pendientes de un nuevo SHA (Python, Static Build, PostgreSQL, CodeQL, `security-audit` y actionlint/ShellCheck); PWI está bloqueado porque su fuente confiable tendría que estar en el `main` predeterminado, que permanece fuera del alcance. Después de publicar se requiere una aprobación humana fresca sobre el SHA actual.

### Identidad del snapshot de publicación

La auditoría compara tres vistas distintas. `HEAD` e índice son el padre local `ef306edd91d339af3a9e0623217b49d86f1cdb1c`, cuyo árbol coincide con el SHA remoto anterior `d5220185cbb8d1975ebb901a5d6e8e77636b8b02`. El worktree candidato agrega 22 modificaciones y 26 archivos nuevos respecto de ese padre: 48 rutas para el sucesor del PR, sin bajas. La diferencia histórica `baseline..HEAD` contiene 1.153 rutas; las 29 rutas del scope que aún no aparecen allí son 26 altas y tres archivos del baseline modificados por este sucesor. Las 29 están presentes en el worktree y fijadas por el manifiesto. El scope completo tiene 1.176 entradas; con seis artefactos de paquete fuera del scope, el guard valida la unión exacta de 1.182 rutas. No hay archivos staged ni se usó el índice como snapshot publicable.

La lista histórica conserva los siete inputs que antes se registraron ausentes. El job Static Build actual invoca directamente once archivos Node: los siete históricos, dos pruebas añadidas por este sucesor (`h3_admin_auth_error_uat.mjs` y `h3_send_lead_error_uat.mjs`) y dos inputs ya presentes en el padre. Los once existen y están incluidos en el scope; `missing_static_build_inputs` describe únicamente el estado vigente y permanece vacío. El updater que corre por segunda vez había borrado la lista histórica al leer el campo actual ya vacío; el error quedó registrado, se restauró la lista desde los registros de adición y el updater quedó idempotente.

### Ejecución local reconciliada — 2026-10-19 10:42 UTC

Esta actualización es la fuente vigente para el candidato local y sus gates; las referencias anteriores a HEAD `ef306...`, 1.176 rutas y 1.182 rutas describen snapshots previos. El workspace es `/tmp/h3req1_r19_publication_prep_20261018`, rama `feat/h3req1-sync-20261018-r19`, HEAD `074583d9f6ea1b5686dc58c9669111f589cb8e7a`, base `4eb4d877a50b012bb630a129bd0c74482c33be9c`. El sucesor permanece sin commit; el manifiesto reconcilia 1.179 entradas y seis artefactos fuera del scope. R18, la fuente Syncthing, el historial y los cambios ajenos siguen preservados.

- La suite Python del workflow de `security-audit` pasó dentro de Docker después de instalar/verificar `requirements-pipeline.txt` con hashes: compile de todos los scripts; escritor H2; scanner de credenciales y regresiones; guard y negativos; pytest primario `250 passed, 10 subtests`; segunda invocación `41 passed`. Un rerun afectado más pequeño dio `34 passed`. El guard informó 1.185 rutas efectivas, 13 catálogos/1.173 destinos y 37 ignored exactos; negativos ordinary=3, newline=1, controls=1, malformed=3 y unmanifested H3=2.
- Las tres causas pytest anteriores quedaron resueltas: se restauró en el estado la frase contractual `El candidato no se publicó:`, y dos tests H2 ahora consultan la allowlist desde `protected_path_scope_guard.sh`. Se añadieron solo esos dos tests a las rutas exactas local/legacy del guard. No se amplió una carpeta ni se alteró el workflow por esos consumidores.
- actionlint 1.7.7, ShellCheck 0.11.0 y `bash -n` pasaron en contenedores de herramientas con el candidato montado de solo lectura. El cambio de helper se validó con ShellCheck; workflows y otros inputs focales conservan los mismos bytes.
- Los gates locales PostgreSQL 17.11/PostgREST 13.0.7 y las 11 invocaciones Node del Static Build permanecen PASS con inputs intactos; esos resultados se reutilizan y no son checks remotos.
- La lectura GitHub de 10:42 UTC sigue limitada al SHA anterior `074583d9…`: run `39228507399` permanece `in_progress` mientras actionlint se ejecuta; Python, Static Build y PostgreSQL fallaron en ese SHA por inputs ausentes, y otros jobs completados figuran success. PWI separado sigue fallando porque la base confiable carece del helper. No hay análisis CodeQL ni checks del sucesor, ni aprobación humana válida sobre un SHA nuevo.
- B sigue incompleto: el responsable confirmó manualmente el ID Text y la paridad HMAC en Preview/Vault; Worker #2 se conserva bajo la excepción temporal vigente. No hay Preview/runtime smoke de este sucesor, por lo que no se declara pasado el gate B. No hubo ajustes remotos.

La revisión independiente del paquete y las verificaciones finales de referencias/plantilla/manifiesto deben cubrir el digest resultante de este corte. No se ha publicado, no se hizo merge y Development sigue NO-GO. La resolución JIT del proveedor PWI aún requiere una decisión humana concreta; no se cambia ni el default branch ni una protección para continuar.

### Reconciliación local del snapshot exacto — 2026-10-19 10:57 UTC

- Se construyó un snapshot de validación autocontenido desde el baseline y solo con las rutas/artefactos fijados por el manifiesto. El diff coincide con la unión exacta de 1.185 rutas (1.179 de scope + seis artefactos); referencias 1.173/1.173 en 13 catálogos. El SHA temporal `9c1c599aea644743e3e583f82d6d60f8a0d8d240` identifica únicamente ese fixture local, no la rama ni el candidato a publicar.
- En Docker pasó el scope guard/negativos, scanner de credenciales y árbol, checker/self-test (723 fuentes, 113 activas, 433 históricas), 46 contratos focales y auditoría de plantilla (10 headings, 9 enlaces del candidato, 0 placeholders). El `git diff --check HEAD` del delta R19 pasa. Se preservan 125 avisos de formato del paquete histórico baseline→snapshot (107 espacios finales y 18 líneas vacías al EOF); no fueron introducidos por el delta R19 y no justifican cambios editoriales de la reorganización.
- Se reutilizan los PASS Docker anteriores para full Python (250 + 10 subtests; segunda invocación 41), PostgreSQL 17.11/PostgREST 13.0.7, Static Build (11 invocaciones), actionlint 1.7.7, ShellCheck 0.11.0, ESLint y TypeScript, porque sus entradas de código, workflows y lockfiles no cambiaron. El contenedor habitual está `healthy`, reinicios 0; no se reconstruyó.
- Última lectura remota 10:57 UTC: el SHA de PR 501 sigue `074583d9…`; run `39228507399` todavía `in_progress` durante actionlint (ShellCheck pendiente), con fallos previos Python/Static Build/PostgreSQL; PWI `39228629396` falla por helper ausente en la base confiable; no hay run CodeQL ni checks del successor local. La revisión GitHub anterior sigue `DISMISSED`. No se afirma PASS remoto del candidato ni aceptación Development.
- El proveedor externo PWI del paquete JIT `/tmp/h3req1_pwi_external_check_app_jit_package_20261019.md` no está aprobado/instalado y es la condición administrativa pendiente antes de publicar el SHA sucesor. No se modifica `main`, ni se cambia o elude una protección. B y el despliegue Preview no se declaran completos; D01–D14 y regresión remota siguen 0/14 y 0/11.

### Corte PWI App + Worker R3/DO aprobado — 2026-10-19 20:10 UTC

Este corte reemplaza únicamente las notas anteriores que describían la aprobación R3 como pendiente. El responsable mantiene aprobado el paquete R3 de GitHub App + Worker y aprueba el delta exacto R3-DO `/tmp/h3req1_pwi_external_check_app_jit_package_20261019_r3_do_delta.md`. Alcance consumible: Worker `studiamatch-pwi-verifier`, binding `PWI_COORDINATOR`, clase SQLite `PwiCoordinator`, tabla `pwi_event_queue` y las columnas, límites, alarmas y operaciones ya descritos en R3/R3-DO. No permite otras tablas, datos, ambientes, Workers o bindings.

**Estado:** todavía sin consumo. Primero debe completarse la revisión independiente del snapshot autónomo exacto y todos los controles locales pendientes. Después, el responsable GitHub registra el App, lo instala solo en `romelhc95/studiamatch`, declara `Pull requests: read` y `Checks: write` (metadata read automática), y suscribe `pull_request`, `pull_request_review` y `check_run`. No conceder Contents, Actions, administración o bypass. El responsable introduce la clave privada del App y el secreto webhook únicamente en la pantalla segura del Worker en Cloudflare; el mismo secreto webhook se configura directamente en la pantalla del App. `GITHUB_APP_ID` e `GITHUB_INSTALLATION_ID` son identificadores no secretos que el operador puede leer sin exponer claves.

Luego se despliega solo el Worker y el DO del paquete; se comprueban versión, hostname, nombre/tipo del binding y clase, columnas exactas de `pwi_event_queue`, estado de webhook y ausencia de valores secretos en la evidencia. El administrador requiere `Protected Workflow Integrity` del proveedor App únicamente en la regla protegida de `desarrollo`, conservando PR obligatorio, una aprobación, `security-audit`, aprobación del último push, dismiss stale, no bypass, no force-push y no deletion. No cambia `main`, `certificacion` ni Production.

El workflow defectuoso se elimina únicamente en el sucesor del PR. El fallo PWI en `a73af141d8419889ae6922f21e416b207a297391` permanece histórico, intacto. Aún no existe SHA sucesor publicado ni check del App, deployment del Worker, revisión humana nueva o resultado remoto. No integrar con checks fallidos, cancelados o pendientes; la autorización de merge sigue condicionada a sus gates y no se consume aquí.

### Hallazgo independiente R3-DO y corrección local — 2026-10-19 20:37 UTC

La revisión exacta del snapshot `6f8bdc41a19d1bbc90e13fc50991c1ead4abd9ad` (árbol `ccac8f086c1a7269a790bace87566297edc09543`, digest `61cbd0dc2bf76112bd420596bde9ed39549427cc270d777c7ed5221e968b8dbf`) detectó HIGH: el check App anterior podía quedarse en `completed/success` entre el `202` del webhook y el inicio de la alarma del Durable Object. La corrección local invalida primero ese check exacto a `in_progress`, con plazo máximo 7,5 s, y solo luego reconoce el webhook; los errores/timeout devuelven `503` y exigen redelivery, sin bypass. Las unitarias 26/26 y la runtime Workers/SQLite 3/3 pasan en Docker Node 22. El nuevo orden contradice una condición explícita del paquete R3-DO, que indica responder `202` sin esperar la API de GitHub. Hay un delta JIT separado pendiente y no se despliega hasta resolverlo. Faltan snapshot autónomo final, full scan final y revisión independiente del código exacto. No hay App/Worker remoto ni nuevo SHA/PR/checks; el fallo de `a73af141…` queda histórico. Development continúa NO-GO.

### Gates locales PWI R3 — snapshot autónomo p — 2026-10-19 21:23 UTC

Snapshot `p` (`ad894278ebfb5f78e9882d1f72817d9a1e6a25c7`, scope `231019c75783b0043d1ec4f1564103aa2f0ddbe8e9935970bcfa33f8c6195e93`) reconstruido desde baseline con 1.190 rutas y 39 artefactos. En Docker pasó el escaneo completo sin findings, Documentation Integrity/self-test, guard/negativos, cuerpo PR (10 headings, 10 enlaces, 16 filas de tabla con cabecera, cero placeholders), contratos Python 33/33, `git diff --check`, Worker syntax, 29/29 unitarias y 3/3 runtime SQLite/DO. Actionlint/ShellCheck se reutilizan por input SHA-256 idéntico. El manifest se está reconciliando con estos resultados antes del snapshot final para revisión exacta.

El JIT de invalidación pre-ACK fue aprobado y permanece sin consumir. La lectura de base/SHA actual de PR 501 y el reemplazo de una fila pendiente stale-SHA requieren el delta específico aún no aprobado; sin él no se desplegará este comportamiento. App/Worker no registrados/desplegados. No hubo escrituras remotas, push, PR update, revisión GitHub nueva, merge ni aceptación Development. El fallo histórico PWI de `a73af141` se preserva; Development sigue NO-GO.


## Reconciliación local PWI R3 — 2026-10-19 21:30 UTC

Snapshot autónomo q quedó validado localmente en Docker: digest `2e91d682f9b35522d694c81b1111a4c532dc5641c41577f588491e5e5691720a`, commit sintético `03eb77e398e00e371c43e4f86d753edc374d2ddf`, árbol `f54cdfbbec63b25c275ddd950eb5a638bde76ddb`; full credential scan, Documentation Integrity/self-test, scope guard y negativos, 33 contratos Python, plantilla y diff incremental desde a73 PASS. Worker tests, actionlint y ShellCheck se reutilizan por hashes idénticos. La revisión independiente exacta continúa pendiente, por lo que este paquete no habilita publicación. El diff global desde 4eb permanece limitado por blobs históricos ausentes en la copia promisor; sin fallback ni red. R3 App/Worker, R3-DO y JIT pre-ACK están aprobados y no consumidos; el delta JIT full-queue/current-head sigue pendiente de aprobación. No hubo operaciones remotas ni se cambió PR 501.


## Snapshot local r — resultado de gates — 2026-10-19 21:32 UTC

Snapshot autónomo r validado en Docker: full scan, Documentation Integrity/self-test, scope guard/negativos, 33 contratos Python, auditoría de plantilla y diff incremental desde a73 PASS. Worker tests, actionlint y ShellCheck se reutilizan con hashes de inputs idénticos. La revisión independiente exacta está pendiente; la ruta protegida R3 aún no se desplegó. El diff global 4eb..r no pudo leer 95 blobs históricos de la copia promisor y queda explícitamente no comprobado. Pre-ACK JIT sigue aprobado/no consumido; el delta full-queue adicional sigue pendiente/no aprobado. El resultado no habilita publicación, merge ni Development GO.


## Snapshot u — gates locales exactos — 2026-10-19 21:38 UTC

Full scan, documentación/self-test, scope guard/negativos, plantilla y diff incremental `a73af141..u` pasaron en Docker. Estado 8/8 se revalidó en s y el archivo de estado permanece byte idéntico en u; los otros contratos y Worker/linter inputs son idénticos a los PASS previos. Revisión independiente todavía pendiente y no existe SHA nuevo remoto. El full diff desde 4eb queda limitado por 95 blobs base ausentes; sin fetch/fallback. Pre-ACK JIT aprobado/no consumido, full-queue JIT pendiente/no aprobado. No ejecutar App/Worker ni publicar hasta revisión y el permiso pendiente.


## Snapshot v — gates locales — 2026-10-19 21:42 UTC

Snapshot v pasó full scan, Documentation Integrity/self-test, scope guard/negatives, estado 8/8, plantilla y diff incremental desde a73 en Docker. Worker suites/actionlint/ShellCheck y otros contratos se reutilizan con hashes idénticos. La revisión independiente final se solicitará para w, luego de repinar estos resultados. Full-queue JIT no aprobado; sin operaciones remotas.


## Snapshot w — gates locales — 2026-10-19 21:46 UTC

Snapshot w pasó escaneo, docs/self-test, scope guard/negativos, estado 8/8, plantilla y diff incremental desde a73 en Docker. Otros contratos/Worker/linters se reutilizan por hashes idénticos. La revisión independiente se solicitará para x. El full diff 4eb sigue no comprobable por blobs históricos ausentes; no hubo fetch/fallback ni operación remota.

## Reconciliación PWI R3 — gates locales z2 — 2026-10-19 22:23 UTC

El snapshot autónomo z2 y su validación están registrados en el manifest/cuerpo/check log. Docker completó los gates sensibles al manifiesto: full scan exit 0, docs/self-test, scope guard y negativos, plantilla, estado 8/8 y diff incremental a73..z2. El Python CI completo y Worker/linter gates de z se reutilizaron únicamente tras verificar hashes de sus entradas. La revisión independiente local del código/test exacto sigue pendiente sobre el siguiente snapshot z3. App/Worker R3, R3-DO y el delta JIT pre-ACK de 7,5 s están aprobados y sin consumir. Sigue pendiente/no aprobado el delta R2 separado para leer la cabeza actual del PR y resolver el overflow. No hay operación remota, SHA nuevo, deploy, merge ni aceptación; no publicar hasta cerrar la revisión y obtener R2. `desarrollo` es el único target; `main`, `certificacion` y Production permanecen fuera.

### Corrección bloqueante de revisión z4 — 2026-10-19 22:35 UTC

La revisión independiente de z4 encontró HIGH: tras un precheck fallido en overflow, la redelivery idempotente podía invalidar el SHA obsoleto del payload y devolver 202 mientras el SHA API-confirmado guardado retenía un check `completed/success`. z4 y z5 se preservan como NO-GO; z5 pasó sus gates de snapshot, pero contiene el mismo código con HIGH. El candidato actual invalida el SHA persistido de la fila existente. La prueba de regresión falla sobre z5 y pasa en el candidato corregido. En Docker Node 22.22.0 pasan `npm run check`, Worker 32/32 y runtime 4/4. Siguiente gate: snapshot z6 autónomo, scanner y gates afectados, revisión independiente exacta; solo después de PASS puede continuarse hacia publicación. R3 App/Worker, R3-DO y pre-ACK permanecen aprobados/no consumidos; JIT full-queue R2 sigue pendiente/no aprobado. No hubo operación remota, App, secreto, deploy, PR update, merge ni aceptación. No cambia la aprobación humana condicionada de merge ni se toca main, certificación o Production.

### Gate z6 y corrección de body — 2026-10-19 22:44 UTC

Z6 exacto pasó escáner completo, documentación/self-test bajo manifiesto, scope guard/negativos, estado 8/8, `npm run check`, Worker unit 32/32 y diff incremental a73..z6. El audit de PR falló por una fila `PWI Worker` fuera del template versionado; la fila se retiró de la fuente y z6 se preserva NO-GO. El gate runtime 4/4 previo se reutiliza solo con hashes de inputs coincidentes; el intento exacto z6 tuvo fallos de dependencia/caché y no se contabiliza como nuevo PASS. El diff desde baseline no se declara por un blob promisor faltante. Se prepara z7 con esa única corrección documental, pines actualizados y revisión independiente final. La autorización R2 full-queue sigue pendiente; pre-ACK, R3 App/Worker y R3-DO aprobados/no consumidos. No hubo acción remota ni publicación.

## Continuación local PWI R3 — 2026-10-19 23:09 UTC

El Worker del sucesor ahora serializa sus secuencias de Check Run por Durable Object/PR. La redelivery del mismo delivery activo reordena la fila existente; el timeout del precheck es cerrado (`503`, sin ACK, redelivery posterior) y un Check Run duplicado falla sin escrituras. Docker Node 22.22.0: `npm run check` PASS, 36/36 unitarias y 4/4 runtime Workers/SQLite. Son resultados locales de fuente, no aceptación remota. El full scan, snapshot autónomo actualizado y revisión independiente exacta siguen pendientes.

El JIT pre-ACK aprobado permanece sin consumir. El JIT R2 full-queue previo no se ejecutará aislado; el paquete consolidado exacto de cola llena y serialización `/tmp/h3req1_pwi_r3_queue_serialization_jit_delta_20261019_r3.md` está pendiente de aprobación. R3 App/Worker y R3-DO siguen aprobados sin consumir. No hubo App, secreto, Worker deployment, push, actualización PR, SHA nuevo, checks, revisión GitHub, merge ni prueba Development. Se preserva el fallo PWI de a73; `main`, `certificacion` y Production quedan fuera de alcance.

### Checkpoint R3 — 2026-10-19 23:13 UTC

El responsable aprobó el paquete exacto de invalidación pre-ACK de 7,5 s; permanece sin consumir. No cubre exclusión mutua, requeue activo, duplicados de Check Run ni cola llena. El delta combinado `/tmp/h3req1_pwi_r3_queue_serialization_jit_delta_20261019_r3.md` que sí describe esas operaciones continúa pendiente de aprobación. `studiamatch-dev` está saludable y sin reinicios; la suite Worker actual sigue validada únicamente en el contenedor Node 22.22.0 aislado. El snapshot autónomo y la revisión independiente final siguen pendientes. No hubo acción remota.

### Resultado local z10 — 2026-10-19 23:23 UTC

z10 quedó reconstruido desde baseline y pasó el escaneo completo, integridad/self-test documental, guard/negativos, estado 8/8, cuatro consumidores Python afectados 46/46, auditoría de plantilla, actionlint, ShellCheck y diff-check incremental. La suite Worker 36/36 + runtime 4/4 coincide por diez hashes exactos; Python completo, Static Build y PostgreSQL se reutilizan con igualdad de inputs/job demostrada. El resultado detallado está en el checks log. El body/log/manifiesto se están actualizando con esos resultados; el siguiente snapshot repetirá escaneo y gates sensibles a documentos antes de revisión independiente. Aún no hay App, secreto, Worker deploy, publicación, revisión remota, merge o aceptación Development.


### Checkpoint z14 y próximo gate — 2026-10-19 23:50 UTC

z14 autónomo pasó los gates locales Docker registrados en el reporte vigente; el snapshot y su identidad quedan preservados. Se actualizan los documentos/manifiesto con esos resultados y se construirá z15 para los gates sensibles y la revisión independiente exacta. El delta pre-ACK de 7,5 s está aprobado/no consumido; el delta r4 adicional de serialización/cola sigue pendiente de aprobación y App/Worker R3/R3-DO continúan aprobados/no consumidos. No se ha registrado App, ingresado secretos, desplegado Worker, actualizado PR ni ejecutado operación remota.

## Revisión z15 y corrección local — 2026-10-20 00:04 UTC

La review independiente exacta de z15 fue NO-GO con un HIGH: en cola llena, una redelivery que ve su fila activa puede esperar la lectura de cabeza; si durante esa espera la alarma finaliza el mismo delivery como `done`, el intento de insertar una fila duplicada falla antes de invalidar el check, y la redelivery siguiente podría ACKear por `already_processed`. Se conserva z15 y su dictamen. La corrección actual reusa esa fila terminal, la asigna a la cabeza confirmada, la resecuencia y la deja `pending` antes de invalidar el check; una fila que ya estaba `done` al comienzo mantiene su fast-path idempotente.

En Docker Node 22.22.0: `npm run check` PASS, unitarias 39/39 y Durable Object/SQLite runtime 7/7. Esos resultados corresponden a los bytes Worker de la fuente, no al snapshot autónomo. R4 queda sustituido por el JIT r5 exacto `/tmp/h3req1_pwi_r3_queue_serialization_jit_delta_20261019_r5.md`, pendiente de aprobación. z16 será el siguiente snapshot; requiere full scan, gates locales afectados y revisión independiente exacta. No hubo operación remota. El pre-ACK exacto sigue aprobado/no consumido; el fallo remoto PWI de a73 permanece histórico; Development NO-GO.

## Snapshot z16 y resultado local actual — 2026-10-20 00:15 UTC

z16 fue reconstruido desde `4eb4d877a50b012bb630a129bd0c74482c33be9c` con el manifiesto exacto, sin fallback: commit `78c5ecd4d1f7088ccd2972138ebfda5e5919654d`, tree `aaf1b8a357b98388bb904d6b744baaff24380461`, scope `60345902b4068d696211c0e59a1a863792eea6defaa2e6fc6288924aac75b36a`; 1.190 entradas, 39 artefactos, unión 1.196/diff 1.195, 13 catálogos/1.173 referencias. Snapshot limpio.

Docker/red deshabilitada: escáner completo sin findings; documentation/self-test PASS (732 fuentes, 113 activas, 433 históricas, 9.247 enlaces/4.625 anchors); guard/negativos PASS (1.196; 3/1/1/3/2); contratos focales Python 46/46; body/template PASS (10 headings, 10 links de candidato resolubles, 16 filas, 0 placeholders); `git diff --check a73..z16` PASS. Los diez hashes de código/tests/config/lock del Worker en z16 igualan la fuente validada en Docker Node 22.22.0: `npm run check`, 39/39 unitarias, 7/7 Workers/SQLite runtime. Los 789 inputs comunes fuera de documentación y paquete Worker coinciden con z10; se reutilizan sus gates locales de Python CI, Static Build, PostgreSQL, actionlint y ShellCheck. Las pruebas reutilizadas no son resultados remotos.

La primera llamada a documentación omitió `--candidate-manifest` y falló por aplicar el modo de checkout completo a omisiones WIP intencionales; se conserva y clasifica como error de invocación. La llamada corregida con el manifiesto y self-test pasó. Se actualizan estos resultados en un sucesor documental z17; esa versión repetirá los gates sensibles y será revisada independientemente. z15 conserva NO-GO/HIGH. R5 sigue pendiente; no hubo operación remota ni consumo de permisos.

## Snapshot z17 — validación local actual — 2026-10-20 00:18 UTC

Snapshot autónomo z17: commit `235094e0fb75ef08cb4aa6f70a7af036f66014c0`, árbol `1bcdc9586abfd3445944f523c7314a883dbfc43e`, parent `4eb4d877a50b012bb630a129bd0c74482c33be9c`, scope `5bffe8054c5ab5a6c50000ae4517148ca01398fbc236e1cbba23df1baff56f7b`; 1.190 scope, 39 artefactos, unión 1.196/diff 1.195, 13 catálogos/1.173 refs, árbol limpio.

En Docker/red deshabilitada pasaron escáner completo, docs/self-test, scope guard/negativos, contratos focales 46/46, body/template y diff-check a73..z17. La revisión de plantilla comprobó diez títulos ordenados, diez enlaces a rutas incluidas, 16 filas y ningún marcador; una primera regla temporal detectó por error la palabra «Todo», que no era placeholder. La regla corregida pasó sin cambiar el snapshot. Diez inputs Worker igualan la fuente con 39 unitarias/7 runtime; los 789 inputs restantes no documentales/no Worker coinciden con z10 y permiten reutilizar gates locales anteriores. Los resultados son locales.

Se registran estos hechos en z18 antes de review independiente. El fallo z15 queda histórico; JIT R5, configuración App y publicación permanecen pendientes. No hubo operación remota ni aceptación Development.
