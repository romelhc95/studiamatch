# Plan H3REQ1 — GO integral para PR y pruebas Development

> Traspaso 2026-10-04: el checklist operativo vigente está en el
> [plan único de cierre hasta Development real, Certification y Production](../../operaciones/plan_cierre_integral_h3req1_2026-10-04.md).
> Esta nota conserva historia y decisiones; sus menciones antiguas a UAT pendiente,
> cuotas sin aprobar o exclusión de Certification/Production describen esos cortes,
> no el alcance documental actual. R17/onboarding posteriores están acreditados localmente;
> el gateway firmado y la aceptación remota siguen pendientes. No concede autorizaciones.

## Autoridad y naturaleza

La autoridad viva es [Estado Del Proyecto](../../estado_del_proyecto.md).
Este documento registra el plan y las decisiones humanas de la conversación;
no acredita ejecución, no declara GO ni concede autorizaciones remotas.
Referencia cliente: [atestación sanitizada](../../evidencias_cliente/sprint_1/atestado_aceptacion_plan_ingesta_editorial_auditoria_2026-10-01.md).
Evidencia técnica: [ciclo BFF local](../h3req1_bff_local_cycle_2026-10-02.md).

## Decisiones humanas registradas

### Checklist mínimo pendiente para GO integral — revisión documental

Pedido humano: **solo documentar lo necesario para GO**. No autoriza implementar,
ejecutar pruebas, congelar/commitear el candidato ni operar GitHub/Supabase/Cloudflare.
El veredicto sigue **NO-GO para PR funcional e inicio de pruebas remotas Development**.
Los PASS focalizados son avance interno; no sustituyen los siguientes gates.

| Orden | Pendiente necesario | Evidencia exigida para darlo por cumplido | Responsable funcional |
|---|---|---|---|
| 1 | Diagnosticar y cerrar UAT final | Suite completa 48/48 casos, 144/144 ejecuciones/capturas y onboarding final PASS sobre los mismos bytes; estabilidad Auth/MFA/AAL2, editorial, roles, rutas públicas y cuotas. Conservar fallos anteriores y diagnosticar timeouts, sin ocultarlos con retries. | Desarrollo / QA |
| 2 | Cerrar riesgos y decisiones de cuotas | Inventariar excepciones `PGRST` del original y abortos que revierten consumo; acreditar tratamiento y límites del control sin afirmar cobertura total. Ratificar límite adicional Edge 120/min antes del despliegue. Cualquier waiver requiere aprobación y causa/evidencia/owner/riesgo/vencimiento. | Backend / Seguridad / Responsable humano |
| 3 | Ensayar rollback integrado seguro | Pages + Edge + cookies + bindings + SQL: suspensión, preservación de páginas públicas/auditoría/otro admin y finalizadores in-flight; recuperación definida y probada localmente. No restaurar tokens JS ni Edge Auth-before-reserve; no usar resume TEST-only remotamente. | Desarrollo / QA / Release |
| 4 | Completar candidato reproducible y aceptación | Inventario exacto de archivos incluidos/excluidos, todos los checks afectados Docker sobre bytes finales, atestación sanitizada cliente y seis pilares, revisión sin HIGH/CRITICAL abiertos; hashes separados de fuentes/build/evidencia. Skips/warnings declarados con causa, riesgo y owner. | Desarrollo / QA / Seguridad |
| 5 | Acreditar CI independiente protegido | Inventario remoto autorizado y, si corresponde, bootstrap separado; workflow instalado y check obligatorio acreditados, review vigente por un colaborador y merge por el otro, sin autoaprobación/bypass. Existencia local del YAML no demuestra enforcement. | Release / Colaboradores humanos |
| 6 | Completar paquete ejecutable de PR/pruebas | Descripción usando estructura de plantilla versionada, reemplazando resultados históricos por evidencia actual; refs/hosts/versiones/bindings/artefactos exactos, casos/aceptación, secuencia expand->compatibilidad->deploy->contract y rollback, operaciones JIT por separado. | Release / Responsable humano |

Higiene del candidato en el gate 4: clasificar antes de stagear el archivo sin
seguimiento `{{.Destination}}{{println}}{{end}}`; no incluirlo ni borrarlo por
suposición. Preservar checkout WIP original, worktree y evidencias históricas.
La plantilla `.github/pull_request_template.md` contiene evidencia de septiembre:
no copiar sus ramas, métricas o PASS como resultados de este candidato.

**Regla de salida:** GO integral solo cuando los seis gates estén acreditados,
sin pendientes bloqueantes ni HIGH/CRITICAL. La UAT r8 FAIL y r10 sin resultado
no cumplen el gate 1; la revisión focalizada sin nuevos hallazgos no cierra el HIGH
runtime previo. No iniciar promoción con un gate fallido.

**Separación no circular:** para abrir el PR no se exige que sus checks remotos ya
hayan corrido; sí CI protegido instalado y candidato local validado. Los checks del
PR y su aprobación son gate posterior de merge. La UAT remota y el drill remoto
determinan aceptación Development después de autorizar su inicio, no son evidencia
anticipada exigida para iniciarlos. Preparación GO no concede push/PR/merge,
inventario remoto, DDL/DML/Auth, secretos, bindings, deploy o rollback: cada operación
conserva autorización humana separada. Certificación/Producción fuera de este pedido.

Este corte es exclusivamente documental: no agrega nuevos PASS ni modifica el
estado de ejecución de los gates. El siguiente ciclo funcional requiere `continua`;
este pedido no lo sustituye ni concede JIT.

### Corte vigente posterior — cuotas aprobadas, implementación local y NO-GO UAT

Este corte sustituye las menciones posteriores a arquitectura/umbrales «pendientes»:
el responsable eligió **Aprobar diseño local** para Durable Objects interno BFF +
controles privados Supabase y los límites de la tabla propuesta. No autoriza remoto.
Se implementó también admisión independiente Edge por actor a 120/min para contar
replay/rechazos antes de body/lookup; entrega sigue 3/min, 10/h, destinatario 3/día y
ambiente 50/día. Este límite técnico adicional debe ratificarse antes del despliegue.

Resultados internos, no GO por componente:
- workerd/Miniflare 4.20260730.0, Node 22.22.0, DO SQLite: 25 concurrentes,
  10 admitidos; 15 rechazados; reinicio conserva límite. Unitario prueba ventanas,
  alarm stale sin borrar admisiones, validación, HMAC y fail-closed.
- PG17 r3 limpio, Pro actual con cohorte y futuro contraído: cadena H2->H3,
  expand -> reserva legacy sin HMAC -> activación -> completion legacy ->
  reaplicación -> cuotas/ACL -> suspensión/finalizadores PASS.
- PostgREST 13.0.7 + SDK instalado: 403 MFA conserva contador; lector legacy
  comparte cuota 120/min y devuelve 429/Retry-After; RPC service-only deniega
  authenticated. Prueba local no acredita versión/configuración Free remota.
- Reauditorías `ses_f01cfaf20ffeWFLG1gyaITUo4r`,
  `ses_f01c56b23ffe2kdQPWZkA7YwOP` y `ses_f0118bf9cffeK47ubskTUvcYSB`:
  cuatro MEDIUM iniciales remediados; última revisión no verifica nuevos HIGH/MEDIUM.
  No cierra HIGH runtime previo sin UAT final.

**Bloqueo de validación concreto:** UAT workerd r8 FAIL, 26/48 casos lógicos y
80/144 ejecuciones PASS, 143 capturas, cero retries. Fallos incluyen snapshot
sin archivos de contratos, query `id` perdida por redirect slash y AAL2 inestable.
HIGH runtime descubierto: `redirect:error` incompatible workerd impide Auth;
remediación `manual` + rechazo 3xx/opaqueredirect pasa contratos y smoke real
workerd login, sin seguir Location ni ampliar destinos. Redirect conserva query.
Se eliminó reemisión manual de cookies Auth antiguas en respuestas de lectura que
podía competir con MFA; solo SDK emite cambios Auth. Logout limpia localmente
cookies/chunks/verifier sin dependencia upstream/config/cuotas, conservando CSRF.
El smoke AAL2 repetido no prueba cierre del fallo intermitente de la suite.

UAT r10 excedió dos timeouts de comando de 20 min; se detuvo exclusivamente su
runner propio tras >40 min, preservando staging/capturas. **Sin resultado final**,
no se etiqueta PASS, ni se reemplaza r8. El driver ahora persiste progreso por
ejecución, limita captura a 10s y preserva backups/staging al fallar. Próximo gate:
diagnosticar suite acotada con progreso, corregir y repetir 144/144 y onboarding;
no avanzar a congelación ni operaciones remotas con esta validación fallida.

### Secuencia expand/compatibilidad/deploy/contract y suspensión propuesta

1. `20261002_h3_admin_quota_expand.sql` aditiva: tabla privada y admisión Edge,
   sin envolver lectores/iniciadores antiguos. Legacy continúa durante preparación.
2. Worker interno sin workers.dev/preview/routes; Pages necesita service binding
   `ADMIN_QUOTA` y secreto `ADMIN_QUOTA_HMAC_KEY` (>=32 caracteres) por ambiente.
   Edge usa su propio binding secreto homónimo; nunca valores versionados.
3. Desplegar Edge compatible reserva-before-Auth con admisión y HMAC antes de
   activar `20261002_h3_admin_quotas.sql`; no aplicar ambas fases mediante sync
   ciego antes del Edge. La activación requiere expand y preserva OIDs/ACL/defaults.
4. Pages y Worker compatibles se despliegan con bindings listos; verificar sesión,
   MFA, invitaciones, cuota directa y finalizadores. Retirar bypass legacy solo
   tras estabilidad y aceptación autorizadas; no DROP de contadores/auditoría.
5. Compensación segura: mantener artefacto endurecido, activar
   `ADMIN_BFF_SAFE_SUSPEND=true` y `ADMIN_INVITE_SAFE_SUSPEND=true`, aplicar
   `db/rollback/h3req1_safe_suspend.sql` con JIT. Admin suspendido, páginas públicas
   conservadas, cookies eliminadas; no downgrade transparente ni restauración de
   tokens JS/Edge Auth-before-reserve. Finalizadores ya reservados permanecen SQL.
   Middleware/Edge fixture de suspensión PASS; ensayo integrado de artefacto aún
   pendiente. Resume remoto no aprobado, no usar el resume TEST-only como operación.

### Matriz de autorizaciones remotas — pendiente, no autorización implícita

| Orden | Operación exacta que debe inventariarse/autorizarse | Gate antes de ejecutar |
|---|---|---|
| 0 | Lectura GitHub protecciones/checks/colaboradores y Free/Preview schema/Edge/hosts/bindings, sin valores secretos ni datos operativos | Autorización read-only específica, ausencia drift y dos colaboradores |
| 1 | Bootstrap CI independiente: commit/push/PR de workflow íntegro, review por colaborador A y merge por B | Candidato bootstrap validado, plantilla real, permisos/protecciones acreditados; sin autoaprobación |
| 2 | PR funcional `feat/h3req1-sync-20261002 -> desarrollo` | GO integral readiness local, candidato exacto/hash, CI efectivo, atestación/pilares; push/PR JIT separado |
| 3 | Merge protegido Development | Checks del PR verdes, review humano, autorización merge independiente |
| 4 | Free expand SQL, secreto Edge, deploy Edge compatible, Worker privado/binding Pages, activación SQL y Pages Preview | JIT por SQL/secreto/deploy/binding, refs/artefactos/hosts exactos y compatibilidad acreditada |
| 5 | UAT real Free/Preview/Auth/MFA/invitación a cuenta designada y cuotas | Autorización Auth/writes acotada, otro admin activo, mailbox autorizado, casos y criterios sin secretos |
| 6 | Drill suspensión y evaluación de aceptación Development | JIT flags/SQL/deploy exactos; preservar auditoría y in-flight; resume requiere aprobación independiente |

Resultados remotos no son condición circular para iniciar las pruebas; son gate
posterior de aceptación. El readiness actual sigue **NO-GO** por UAT local y CI
independiente HIGH sin acreditación. No PR/push/merge/deploy/Auth/DDL/DML remotos.
Riesgos pendientes de evidencia: cuota SQL no contabiliza rechazo antes de invocar
función ni transacción cancelada/abortada; inventariar excepciones PGRST del original
que se repropagan. No waiver concedido ni afirmar que los intentos se cuentan todos.

### Objetivo vinculante actualizado — entrega integral, no por partes

El responsable solicita **GO completo que permita llevar el candidato a PR e
iniciar pruebas remotas**, y pide que la documentación refleje ese objetivo.
Los cierres focalizados y PASS son evidencia de avance, no entregables GO separados.
No concluir el trabajo en cada hallazgo: avanzar sobre el conjunto hasta readiness
integral o un bloqueo concreto de autorización, drift o validación fallida.

**Definición de GO para PR/pruebas:** candidato final validado, sin HIGH/CRITICAL
ni pendientes bloqueantes locales, con CI protegido efectivo, evidencia identificada,
compatibilidad/rollback seguros y matriz remota ejecutable con operaciones exactas.
No exige que las pruebas remotas ya hayan pasado para autorizar su inicio; su resultado
determina la aceptación Development posterior, dentro del mismo objetivo integral.
No acredita GO de producción ni permite omitir approvals/JIT obligatorios.

| Pendiente de la entrega integral | Criterio verificable |
|---|---|
| Cuotas compartidas | Arquitectura/umbrales aprobados; implementación y pruebas de límites, concurrencia, ventanas, 429/Retry-After y fallo del contador. Sin waiver implícito. |
| Candidato final | Jobs afectados completos en Docker y UAT final con Auth/MFA/invitaciones, roles, editorial/auditoría, disponibilidad, rutas estáticas, sesiones y cuotas; r14 no prueba los bytes nuevos. |
| Revisión y evidencia | Atestación cliente y pilares satisfechos para alcance local, reauditoría exacta, hashes separados de fuentes/build/resultados; skips/warnings con causa, riesgo y owner. |
| Rollback | Suspensión SQL probada; falta plan/ensayo local seguro de Pages/Edge y cookies/bindings, sin restaurar Edge que envía Auth antes de reservar ni tokens JS. |
| CI independiente | Bootstrap separado si necesario, revisión por dos colaboradores y enforcement remoto acreditado; sin autoaprobación/bypass. Su PR es prerrequisito, no cierre parcial de H3REQ1. |
| Paquete remoto | Inventario read-only autorizado, SHA/hostname/schema/Edge/bindings exactos, casos y aceptación, JIT separados para Git/DDL/Auth/deploy/cuotas/rollback; preservar otro admin y auditoría. |

Secuencia única: resolver decisiones y pendientes locales -> preparar candidato y
paquete de pruebas/rollback -> acreditar bootstrap CI autorizado -> GO integral
para PR/pruebas -> PR funcional protegido e integración Development autorizados ->
deploy/operaciones Free/Preview autorizados -> UAT remota y evaluación integral.
No Certificación/Producción. Las aprobaciones por operación son controles de
ejecución, no fragmentación del entregable. Este pedido documental no concede
autorización remota general.

### Resultado del ciclo focalizado `Continúa`

### Continuación de cierre integral — propuesta de cuotas para aprobación

El responsable pidió continuar el cierre documentado. Se verificó el BFF y Edge
actuales: Pages no tiene binding de cuotas; Edge autoriza JWT y puede recibir
llamadas fuera del BFF. Las RPC autenticadas conservan su identidad/RLS. Por tanto
un contador exclusivamente BFF no acredita límites de los iniciadores Supabase.
No se implementa esta propuesta hasta aprobación de arquitectura y umbrales.

**Arquitectura recomendada (solo desarrollo/validación local):**

1. Worker interno Cloudflare con Durable Objects vía service binding Pages, sin
   ruta pública del contador. Contadores compartidos persistentes, operaciones
   serializadas, ventanas explícitas y expiración. Claves HMAC con secreto de
   entorno, sin almacenar IP/email crudos, JWT, password ni API key.
2. Controles transaccionales en schema privado PostgreSQL para iniciadores RPC
   autenticados e invitaciones Edge antes de reservar/enviar Auth; actor derivado
   de identidad verificada, nunca del body sin validar. Evitar bypass directo de
   BFF; ningún grant de escritura anónimo ni acceso cliente a tablas de cuotas.
   Edge conserva service-role exclusivamente server-side y autorización actual.
   Identificador destinatario HMAC server-side con secreto de entorno, no hash
   simple reversible por diccionario. Inventariar nuevas variables sin sus valores.
3. Capas cuentan intentos en su propio perímetro, no duplican artificialmente la
   misma cuota de entrega. Replay completado no vuelve a consumir cuota de envío;
   sigue limitado como petición. Completion/failure/reconciliation de operaciones
   reservadas permanecen ejecutables al alcanzar cuotas o suspender iniciadores.
4. Exceso: 429 y Retry-After validado; fallo/configuración ausente: 503 y sin nuevas
   autenticaciones/mutaciones/invitaciones. Logout/limpieza local no se bloquea.
   Error no enumera usuarios/destinatarios. No debilitar RBAC/MFA/CSRF.

| Dimensión / operación | Umbral inicial propuesto |
|---|---|
| Entrada BFF por IP confiable | 300 peticiones/minuto |
| Login por IP | 20 intentos/10 minutos |
| Login por cuenta normalizada + IP | 10 intentos/10 minutos; no bloqueo global de cuenta por terceros |
| MFA/callback/password por actor o IP antes de identidad | 10 intentos/10 minutos por clase |
| Lecturas RPC por actor | 120/minuto |
| Mutaciones RPC por actor | 30/minuto |
| Invitaciones por actor | 3/minuto y 10/hora |
| Invitaciones por destinatario | 3/24 horas |
| Invitaciones por ambiente | 50/24 horas |

Umbrales propuestos, no mediciones de capacidad ni aprobación de negocio; deben
aceptarse o ajustarse. No cambiar Auth/MFA/onboarding ni introducir cuotas sobre
escritores ETL. IP confiable proviene de Cloudflare en runtime real; spoofing de
headers/proxy y ausencia de IP deben probarse con comportamiento fail-closed.

Gates antes de congelar candidato: límites/ventanas/expiración/restart/concurrencia,
sin doble envío/replay, invocación Edge/RPC directa limitada, fallos sin efectos,
logout operativo, finalizadores disponibles y pruebas de carga acotadas Docker;
PG17 cadena/rollback, contratos credenciales, typecheck/lint/build/UAT y auditoría.
Expand: contadores/adaptadores aditivos -> compatibilidad de sesiones y finalizadores
-> deploy remoto JIT pendiente -> contract tras estabilización. Rollback seguro
no retira contadores/grants de forma que se reabra un bypass; artefacto exacto se
seleccionará y ensayará antes del GO. No configuración ni writes remotos autorizados.

La aprobación solicitada cubre implementar y probar este diseño localmente en
Docker/PG17. Crear bindings/secrets, DDL/DML Free, deploy Worker/Edge/Pages y Git
remoto mantienen JIT separado. NO-GO integral vigente mientras la decisión esté
pendiente. Después de decidir se continúa el conjunto, no se entrega un GO por cuota.

- LOW replay recovery: remediado mediante metadata aditiva server-side antes de
  Auth y respuesta idéntica en replay completado, sin reenvío. Legacy sin método
  persiste compatible; no se infiere recovery desde estado Auth mutable.
- MEDIUM drill in-flight: remediado con reservas previas y finalizadores reales
  bajo service_role después de suspensión doble; nuevos iniciadores rechazados.
- Gates Docker Edge/typecheck/pytest y drills PG17 ambos modos PASS; reauditoría
  `ses_f01f31258ffeIQxqU1tGp9N4xX` confirma ambos cierres focalizados.
- NO-GO integral conservado. Siguiente decisión pendiente: arquitectura/cuotas
  compartidas; luego UAT final y congelación, sin autorizaciones remotas implícitas.
- Transición: expand metadata -> compatibilidad legacy -> deploy pendiente JIT ->
  contract pendiente estabilización. Rollback mantiene suspensión segura; no
  restaurar Edge anterior que envía Auth antes de reservar.

- Objetivo actualizado: **GO integral para PR y pruebas Development**, con
  readiness y resultados de ejecución diferenciados, no entregas parciales;
  integración protegida a `desarrollo`, Free/Preview, UAT y rollback en una misma
  secuencia. Sin Certificación ni Producción.
- El responsable comunicó que el cliente conoce las remediaciones de seguridad,
  incluyendo BFF. Solicita considerar en el PR los cambios de remediación de esta
  sesión que aporten al producto. Cada cambio debe tener trazabilidad, alcance,
  seguridad, compatibilidad y evidencia; no se incluyen cambios ajenos o extras
  solo por calificarlos como un «plus».
- Recursos ofrecidos: admin existente con MFA, buzón accesible y cuentas por rol.
  Se reutilizará la cuenta designada por el responsable para onboarding desde cero.
  Su identidad no se reproduce en documentación versionada.
- Estrategia elegida: **reinicio acotado tras inventario** en Supabase Free.
  La decisión define el plan, no autoriza eliminación/reset ni cambios Auth/DB.
- Las 618 min 21 s reportadas no constituyen un criterio de aceptación. El avance
  se mide por gates concretos y evidencia del candidato exacto.
- Continuación Build: actualizar Obsidian primero, corregir build CI, demostrar
  baseline H2 Pro -> H3 encadenado y preparar rollback compensatorio local.
- Rate limiting se incluye ahora en el cierre; se retira el diferimiento anterior,
  sin waiver. El diseño compartido debe aprobarse antes de añadir infraestructura.
- Mantener Auth/MFA/invitaciones existentes y exactamente dos colaboradores: uno
  aprueba y otro mergea. No reabrir negocio/onboarding ni debilitar protección Git.
- Presentar la excepción JWT acotada para aprobación, no ampliarla implícitamente.
  Ninguna consulta u operación remota está autorizada por la continuación Build.

## Diagnóstico histórico — no representa los pendientes vigentes

| Identificado | Estado |
|---|---|
| UAT visual Pages `r14` | PASS: 48/48 casos, 144/144 ejecuciones, 144 capturas, 0 retries; archive SHA-256 `12163e7f33b5fb49b671410a9f2766da39b359b28d611ae891e991f9dfc418f1` |
| UAT invitación/onboarding | PASS: 10/10 casos |
| UAT BFF/Auth/SDK/Edge | PASS reportado: 52/7/15 checks y 6 CORS, 7 clasificaciones, 10 ambigüedad, 4 replay, 1 replay concurrente, 1 expiración. SDK UAT aún no prueba JWT real/rutas allowlisted |
| Pytest | PASS: 281 passed, 4 skipped, 1 deprecation warning `PyPDF2` |
| PG17 | PASS: harness H3 con cohorte Free y sin cohorte Pro; incluye rechazo de edición para membresías activas `invited` y `password_pending`. Baseline H2 Pro deja ausente la cohorte retirada |
| Calidad local | PASS: TypeScript, `actionlint`, `shellcheck`, credential scan, `git diff --check`, `npm audit --include=dev` (0 vulnerabilidades); ESLint 0 errores/9 warnings |
| Reauditoría de seguridad | El informe read-only disponible precede al último delta SQL: HIGH CI, MEDIUM rate-limit, LOW transporte JWT y LOW `account_status`. Este último se corrigió y probó en PG17; falta reauditar el árbol exacto |
| Integridad CI | HIGH abierto: no hay acreditación local/remota de workflow externo instalado y requerido. No se consultó GitHub en esta continuación |
| Rate limiting | MEDIUM abierto, incluido en cierre actual; arquitectura/cuotas pendientes de aprobación, sin waiver |
| Transporte JWT | LOW abierto: la excepción documentada es solo RPC; runtime también envía JWT a Auth/MFA y Edge `admin-invite`. No se amplió el alcance mientras falta decisión humana |
| Baseline/candidato | Worktree aislado en `feat/h3req1-sync-20261002`, `HEAD=4eb4d877…` (baseline) y cambios sin commit. Manifiesto de 701 rutas en evidencia; el SHA de `HEAD` no identifica el árbol candidato |
| Rollback, H3-003/H3-004 y Pages Development | Rollback SQL compensatorio/drill y gates remotos pendientes; requieren aprobación JIT por operación |

## Etapas, tareas y gates de validación

| Etapa | Tareas concretas | Gate de salida |
|---|---|---|
| 0. Traspaso documental | Actualizar plan/estado/evidencia y aceptación; preservar histórico, WIP y gobernanza de los dos colaboradores. | NO-GO y decisiones pendientes explícitos, sin documentación contradictoria. |
| 1. Preflight remoto | Solo tras autorización read-only: GitHub/Cloudflare/Supabase, baseline/checks/workflows/schema/Auth/Edge/bindings; sin valores secretos. | Inventario real sin drift no resuelto. Puede prepararse trabajo local antes; no inferir PASS remoto. |
| 2. Controles locales | Tras decisiones: allowlist JWT exacta y cuotas compartidas. Conservar login/MFA/invitaciones y membresía ready. | Destinos arbitrarios denegados, positivos Auth/MFA/Edge/RPC, cuotas/concurrencia/reset/fallo del contador probados. |
| 3. Reproducibilidad CI/DB | Build con fixture local; H2 Pro completo -> secuencia H3 en la misma base PG17; rollback SQL compensatorio y transición de dependencia de cohorte. | Jobs completos en Docker; idempotencia, permisos, regresión legacy y drill sin pérdida de datos. |
| 4. Bootstrap CI independiente | PR mínimo de controles por vía mantenedora; aprobador/mergeador existentes y aprobación del SHA exacto; JIT separados. No esperar un workflow aún ausente ni debilitar controles. | Check externo efectivo, pruebas de rechazo/aprobación y HIGH cerrado con evidencia, no con intención. |
| 5. Readiness integral para PR/pruebas | Congelar fuentes/artefacto, ejecutar gates afectados/UAT y reauditoría exacta; aceptación/pilares y paquete remoto/rollback. | GO para PR/pruebas solo con criterios completos y CI efectivo; no exige resultados de pruebas remotas aún no iniciadas. |
| 6. Integración Development/Free/Pages | PR funcional protegido a desarrollo; schema Free, Edge, servicio de cuotas y Pages con JIT por operación; inventario mínimo de cuenta si se requiere reinicio. | SHA/hostname/schema/bindings identificados, CI real verde; otro admin y auditoría preservados. |
| 7. UAT y GO Development | Auth/correo/MFA real, roles, editorial/auditoría, 90 días, ruta estática, sesiones, cuotas, cuenta existente y onboarding nuevo; H3-003/H3-004 y rollback autorizado. | Aceptación real sobre el despliegue exacto; sin pendientes ni hallazgos bloqueantes. No Certificación/Producción. |

No se repiten gates indiscriminadamente si nada relevante cambió: cada repetición
debe indicar qué cambio invalida la evidencia anterior. Toda nueva sincronización
o corrección del candidato exige revisar impacto sobre pruebas y hashes.

### Historial de decisiones técnicas y propuesta original — supersedido donde aplique

**Corte de ejecución posterior:** JWT acotado aprobado explícitamente y registrado
en atestación; transporte implementado localmente (SDK 23/BFF 52/pytest 282+4 PASS,
UAT visual y reauditoría pendientes). CI corregido localmente, lint PASS, build
completo pendiente. Harness encadenado creado y ejecutado: FAIL por ausencia de
`courses.provider_used` en fixture H2 Pro. Detener ante baseline drift y pedir
autorización read-only Pro o decisión de reconstrucción exclusivamente versionada;
no introducir columnas ad hoc. Cuotas y rollback SQL/drill siguen pendientes.

Reauditoría posterior read-only: HIGH de Edge happy path (`reserved` fuera de scope,
falsa reconciliación tras envío/persistencia exitosos), MEDIUM rutas propias fuera
de allowlist CI, LOW inventario explícito JWT y LOW cortes documentales contradictorios.
No bypass de transporte confirmado. Tareas antes de reabrir GO: corrección happy paths
con 200/no reconciliación/replay, typecheck Edge semántico, allowlist rutas exactas,
inventario destinos/métodos y Request/init, resolver baseline mediante decisión
humana, luego build/UAT/auditoría final. No añadir columnas por suposición.

**Preflight Pro read-only aprobado y ejecutado:** provider_used existe (text nullable
default mock) y cohorte H2 **presente**. El modelo local contraído no es el baseline
remoto actual. Detener y pedir decisión para corregir fixture según metadata real y
separar prueba encadenada de Pro actual de prueba de contracción futura. No cambiar
Pro ni retirar cohorte; lectura no autoriza DDL/DML. Ledger nativo no basta para
inferir migraciones aplicadas por todas las vías.

**Decisión humana posterior:** se aprobó adoptar Pro actual con cohorte presente y
corregir el fixture según metadata acreditada. El ensayo contraído futuro se mantiene
como modo distinto, no autoridad remota. Continuar solo cambios/pruebas locales;
no aplicar DDL en Pro ni interpretar este acuerdo como despliegue/lectura adicional.

**JWT:** no rediseñar Auth/MFA/invitaciones. El BFF ya utiliza sesión server-side;
el hueco es el contrato de destinos y el helper permisivo. Proponer allowlist por
proyecto/ruta/método: POST a RPCs Admin existentes, operaciones Auth/MFA requeridas
por el SDK y POST a `functions/v1/admin-invite`. Inventariar también la validación
Auth de la identidad en Edge por separado. Denegar tabla Data API directa, RPC
desconocida, host alterno, API key Bearer y método incorrecto. Supabase verifica
firma/expiración/identidad: validar formato no constituye autenticación. La propuesta
no amplía la excepción hasta aprobación humana y actualización de atestación.

**Cuotas:** recomendar servicio interno Cloudflare con Durable Objects y binding
desde Pages, sin endpoint público ni contadores en memoria de cada Worker. No
almacenar JWT/API keys/PII cruda; configurar cuotas por operación/IP/actor/destinatario,
`429` y `Retry-After`, ventanas y comportamiento ante fallo del contador. La
arquitectura y umbrales son propuesta pendiente; implementación/infraestructura y
bindings remotos conservan autorización separada. No introducir writes anónimos de
cuotas en Supabase ni secret/service-role key en el BFF.

**CI:** el job actual corre `npm run build` con `example.invalid` antes del smoke
local. El PASS de un build distinto no acredita ese job. Corregir el orden/configuración
para usar fixture local determinista y validar una ruta estática elegible. Reproducir
la secuencia completa en Docker, no limitarse a YAML/actionlint.

**PG17:** el modo H3 sin cohorte solo modela su ausencia. Crear prueba encadenada
sobre la misma base que termina el baseline H2 Pro, sin reset/fixtures de schema H3
que oculten incompatibilidades. Probar firmas/grants/constraints/lectores y reapply
de deltas idempotentes. No modificar migraciones remotas aplicadas para converger.

**Rollback:** distinguir compensación de entrega Auth del rollback DDL. Restaurar
funciones/vistas anteriores preservando columnas y datos nuevos, restricciones de
seguridad y auditoría append-only. Si el rollback abre un gate más débil, detenerse;
preferir retirada segura del candidato a downgrade inseguro. El wrapper H3 sobre una
cohorte existente crea dependencia: antes de DROP de cohorte, convertir su lector
a vacío tras paridad/estabilidad y probarlo sin CASCADE. No recrear cohorte retirada.

**Evidencia:** hashes separados de fuentes, artefacto y resultados; los documentos
de evidencia no deben entrar al digest de fuentes probadas. Registrar causa/owner
de los cuatro skips y nueve warnings. UAT r14 se conserva y no sustituye UAT final
si cambia el transporte web o se incorpora rate limiting.

## Reinicio de prueba versus compatibilidad

1. **Onboarding desde cero:** cuenta designada reiniciada exclusivamente en Free,
   con invitación real, password, MFA y autenticación.
2. **Compatibilidad BFF:** otra cuenta existente preservada limpia la sesión legacy
   y reautentica con su MFA, sin reinvitación, nueva cuenta ni repetir onboarding.

El primer escenario no demuestra el segundo. Si no existe otro admin activo o no
se puede preservar auditoría/dependencias, detener el reinicio y consultar antes de
proponer alternativa. No reinicializar Free completo ni tocar Pro. No deshabilitar
triggers de auditoría ni borrar historial para «dejar limpio» el ambiente.

## Transición y rollback

- **Expand:** candidato BFF/HttpOnly y deltas aditivos validados en Docker/PG17. La
  vista privada `h3_legacy_public_course_cohort` lee la cohorte H2 cuando existe y
  resuelve una relación vacía cuando Pro ya la retiró; no reconstruye ni reinserta
  cohortes. Las dos ramas pasan el harness local.
- **Compatibilidad:** preservar el contrato lector y funciones previas durante la
  promoción; validar reautenticación de cuentas existentes separadamente del
  onboarding desde cero. La transición real de cuentas no se ejecutó.
- **Deploy:** SHA y hostname exactos con aprobación separada y verificación de
  migraciones/Edge/bindings aplicables. GO Development no equivale a producción.
- **Contract:** retiro del legacy tras estabilidad productiva en un ciclo posterior
  autorizado; no ejecutar contracción prematura ni declarar cerrada esta fase.
- **Rollback:** suspensión SQL e in-flight validados localmente; no downgrade de
  lectores/funciones antiguas. Falta seleccionar y ensayar localmente artefacto
  Pages/Edge seguro y efectos sobre cookies/bindings/datos. Edge anterior a reserva
  previa Auth no es destino seguro. Aplicación remota requiere JIT propio; no volver
  a tokens JS ni asumir que revertir Pages revierte DB/Edge/Auth.

## Preguntas y autorizaciones interactivas

| Disparador | Pregunta / decisión humana requerida |
|---|---|
| Scope o conflicto de baseline | ¿Incluir, separar o detener este cambio? Presentar diff, riesgo y criterio afectado. |
| Hallazgo | ¿Corregir o solicitar waiver formal? Cada waiver necesita causa, evidencia reproducible, owner, riesgo, vencimiento y aprobación. |
| Reinicio Free | ¿Apruebas estas operaciones exactas, dependencias, preservación y contingencia? JIT antes de cualquier mutación. |
| DDL/Edge/Preview | ¿Autorizas estos archivos/hashes, ambiente, SHA/hostname y rollback? No agrupar permisos implícitos. |
| Git/CI protegido | Pedir instrucciones independientes para push/PR, merge y modificaciones de protección/workflow_dispatch. |
| Rollback o cleanup | Pedir JIT específico; no reutilizar permiso de deploy o prueba de correo. |
| Gate de cierre | ¿Los resultados cubren todos los criterios acordados? Si no, registrar bloqueo concreto y siguiente tarea. |

El pedido inicial de documentar no autorizaba ejecución. La continuación Build
posterior autoriza el trabajo local acordado y esta actualización, pero no sustituye
la decisión JWT, aprobación de arquitectura de cuotas ni las autorizaciones remotas.
Este plan conserva el **NO-GO integral vigente**. Readiness para iniciar PR/pruebas
y resultados posteriores son estados de la misma entrega; falta de aprobación
remota no es un fallo de pruebas locales ni permiso para omitir JIT.

## Preflight de sincronización de baseline — solo lectura

La consulta read-only confirmó `origin/desarrollo@4eb4d877a50b012bb630a129bd0c74482c33be9c`
(rama protegida). El checkout permanece en `feat/h3req1-development-remote-tests`,
`HEAD=7650093b05a820e8e6faf9ec711e12fab8b50398`, con merge-base
`97168646b2a6bbd8e59f6d704446759303e11e64`: el ref remoto tiene 27 commits exclusivos
y el candidato 5. `git cherry` identificó tres commits locales equivalentes por patch
ya presentes en `desarrollo` (`4f9de252`, `7722d838`, `74ec6a42`) y dos no equivalentes
(`f05f7a6d`, `7650093b`); no se debe cherry-pick/rebase automáticamente.

El worktree tiene 1.706 entradas de estado y cero staged; hay 24 rutas sucias que
también cambiaron entre el merge-base y el `desarrollo` actual:

```text
.context/indice.md
.context/estado_del_proyecto.md
.context/evidencia/h3req1_development_remote_cycle_2026-09-26.md
.github/workflows/security-audit.yml
STUDIAMATCH-H3-UAT-MOCK-02-REPORT.md
mock-server/server.js
supabase/templates/password-recovery.html
tests/h3_invitation_uat.mjs
tests/h3_local_uat.mjs
tests/sql/h3_invitation_onboarding_harness.sql
tests/sql/h3_pg17_harness.sql
tests/test_h3_admin_queue_ux_contract.py
tests/test_h3_invitation_callback_contract.py
tests/test_h3_password_recovery_contract.py
tests/test_mfa_compatibility_contract.py
tests/test_password_policy_contract.py
tests/test_supabase_credentials_contract.py
web/functions/_middleware.ts
web/src/app/admin/edit/page.tsx
web/src/app/admin/login/page.tsx
web/src/app/admin/reset-password/page.tsx
web/src/app/admin/users/page.tsx
web/src/lib/admin-auth.ts
web/tsconfig.json
```

En particular, el remoto agrega `STUDIAMATCH-H3-UAT-MOCK-02-REPORT.md` mientras el
worktree lo marca borrado; se preservan ambas versiones para una decisión explícita.
También hay que revisar el orden/dependencias de migraciones con prefijo
`20260927` antes de integrar. No se rebasó, cherry-picked, copió ni descartó ningún
archivo. El preflight renovado sí ejecutó credential scan y `git diff --check`, y
creó un respaldo externo verificable antes del traslado; no ejecutó UAT ni gates
funcionales. Los detalles y hashes se registran a continuación.

#### Respaldo real verificado — 2026-10-02

El preflight se revalidó: `HEAD=7650093b05a820e8e6faf9ec711e12fab8b50398`,
`origin/desarrollo=4eb4d877a50b012bb630a129bd0c74482c33be9c`, merge-base
`97168646b2a6bbd8e59f6d704446759303e11e64`, divergencia `27/5`, 1.706 rutas
de estado y 0 staged. La auditoría de credenciales pasó sobre el árbol versionado
y los archivos nuevos candidatos; `git diff --check` pasó.

Se creó un respaldo fuera del checkout en
`C:\Users\Romel\AppData\Local\Temp\opencode\studiamatch-h3req1-sync-backup-20261002-verified5`.
Contiene el diff binario versionado, archivo de 1.652 archivos nuevos/evidencia,
listados de estado y rutas, SHA de baseline, hashes por archivo y log de verificación.
Los 16 archivos de configuración/estado local de `.codex/`, `.obsidian/`,
`.openchamber/` y `supabase/.temp/` no se copiaron; permanecen intactos en el checkout
original y están listados por ruta. El manifiesto externo `SHA256SUMS` verifica patch,
archivo y manifiestos. La inspección read-only encontró cinco entradas stale/prunable
en `git worktree list`; no se ejecutó prune ni cleanup. Tras aprobación humana para
la ruta exacta se creó `/home/romel/src/studiamatch-h3req1-sync-20261002`, branch
`feat/h3req1-sync-20261002`, desde `origin/desarrollo@4eb4d877a50b012bb630a129bd0c74482c33be9c`.
El worktree sigue limpio: se aisló el baseline y no se transfirió ningún delta.

### Secuencia corregida (aislamiento aprobado; reconciliación pendiente)

El responsable solicitó corregir la documentación tras la revisión del plan. Este
pedido no ejecuta la sincronización ni concede permisos remotos. Los SHA y conteos
anteriores son un snapshot: antes de ejecutar se debe confirmar que no cambiaron.

1. **Respaldo verificable.** Mantener intacto el checkout original. Antes de trasladar
   cambios, preservar fuera del candidato y del PR los commits, diff binario,
   archivos nuevos y evidencia histórica/fallida, con manifiesto de rutas, hashes y
   verificación de integridad del respaldo. Inventariar no sustituye respaldar.
   Separar `.codex/`, `.obsidian/`, `.openchamber/`, `supabase/.temp/`,
   `test-results/` y otras rutas privadas/locales. No borrar ni trasladar secretos
   al candidato; el respaldo no reproduce credenciales en logs o documentación.
   Gate: respaldo recuperable verificado y clasificación explícita de cada ruta.
2. **Reconciliación por diferencias.** El worktree aislado se creó tras autorización
   humana exacta desde el SHA confirmado de `desarrollo`; permanece limpio. Hay cinco
   metadatos stale/prunable; no podar ni limpiar como precondición. Comparar
   merge-base, remoto y candidato local; aplicar solo los deltas seleccionados, no
   copiar archivos completos ni cherry-pick/rebase automáticamente. Revisar los dos
   commits no equivalentes, todos los archivos nuevos y cada cambio relevante, no
   solo las 24 rutas solapadas: solapamiento no equivale a conflicto confirmado.
   Registrar por ruta origen, decisión, trazabilidad cliente y resolución; conservar
   correcciones remotas y trabajo ajeno. El borrado del reporte requiere decisión
   explícita, nunca resolución automática. Gate: diff acotado y conflictos resueltos
   sin pérdidas, con baseline y alcance sin drift pendiente.
3. **Baseline y migraciones.** Contrastar versiones, firmas, constraints, grants,
   dependencias, orden e idempotencia con Pro como autoridad mediante lectura, sin
   modificar Pro. Revisar especialmente los prefijos `20260927` y el efecto de los
   deltas nuevos. No renombrar, sustituir ni editar migraciones ya aplicadas para
   forzar convergencia. Solo proponer un delta ante incompatibilidad demostrada;
   aplicar DDL/DML requiere JIT separado. Gate: baseline documentado y harness PG17
   limpio reproducible, sin inferir convergencia remota por un PASS local.
4. **CI y bootstrap sin circularidad.** Preparar antes del cierre el manifiesto de
   instalación del workflow confiable en la rama base y de protección externa del
   check independiente; no ejecutarlo. Definir etapas que no dependan de que el
   primer PR ya produzca un workflow aún ausente de la base. La configuración remota
   requiere aprobaciones separadas para push/PR, merge y protección; no debilitar el
   gate ni interpretar su ausencia como PASS. Separar defecto local confirmado de
   requisito de configuración remota: si el auditor confirma un HIGH local, bloquea
   GO local; un requisito remoto pendiente bloquea integración/GO remoto y debe
   quedar acreditado como tal. No reclasificar ni cerrar el HIGH por conveniencia.
   Gate: revisión especializada de la solución y plan de bootstrap verificable;
   enforcement remoto solo PASS con evidencia remota real.
5. **Candidato exacto y validación.** Congelar el manifiesto/hash de fuentes
   sincronizadas y registrar baseline, herramientas y configuración sanitizada.
   Construir en snapshot Docker aislado sin alterar `web/out` original. Vincular
   build, artefacto servido y UAT a esos hashes; separar fuentes de evidencia generada
   para evitar hashes circulares. Ejecutar actionlint/shellcheck, contratos
   Edge/BFF/cliente, pytest, PG17/concurrencia, TypeScript, lint, dependencias,
   credenciales, onboarding y UAT visual completa de los últimos bytes. Cubrir el
   hostname fail-closed para UI/API con allowlist explícita, excepción local
   activada/desactivada, host desconocido y host público. Justificar skips/warnings
   y cualquier reutilización de evidencia por ausencia demostrada de impacto;
   conservar resultados fallidos. Cualquier corrección invalida los gates afectados
   y exige corregir/revalidar, incluida UAT visual sobre el artefacto final.
   Gate: resultados aplicables completos sobre el mismo candidato, no sobre `r11`.
6. **Reauditoría y cierre separado.** Reauditar correcciones y evaluar aceptación
   cliente, pilares, `expand -> compatibilidad -> deploy -> contract` y rollback.
   Declarar GO local solo con criterios locales completos y sin HIGH/CRITICAL
    locales abiertos; no afirmar deploy, compatibilidad de cuentas reales ni contract
    por pruebas mock. El diferimiento original de rate limiting fue sustituido por
    la decisión de remediarlo en el cierre actual; owner responsable técnico del
    proyecto. No es waiver ni riesgo aceptado. Preparar los manifiestos
   remotos sin ejecutarlos y pedir cada JIT por operación, ambiente y alcance exactos.
   No se avanza a Certificación/Producción. Gate: veredictos local/remoto explícitos,
   evidencia canónica real y ningún pendiente oculto.

### Resultado de reconciliación read-only — 2026-10-02

Después de fetch read-only, las referencias se mantuvieron: checkout WIP
`HEAD=7650093b05a820e8e6faf9ec711e12fab8b50398`, remoto
`origin/desarrollo=4eb4d877a50b012bb630a129bd0c74482c33be9c`, merge-base
`97168646b2a6bbd8e59f6d704446759303e11e64`, divergencia `27/5`; tres patches
locales ya están en remoto y dos commits no son equivalentes. El worktree aislado
está en el SHA remoto y con cero rutas sucias.

El diff de árbol completo local vs remoto comprende 43 rutas tracked. En el WIP
original permanecen 39 rutas tracked modificadas/borradas y 1.652 rutas untracked,
1.488 de ellas evidencia histórica/visual. El respaldo `verified2` excluyó 15 rutas
locales/config; después apareció `.obsidian/workspace.json`, intacto y excluido junto
a la configuración local. El respaldo final `verified5` incluye 1.652 archivos
untracked clasificados y 16 rutas locales/config excluidas; el estado total registró
1.707 entradas. No se copiarán automáticamente artefactos/evidencia. Entre las 24
rutas con cambios en ambos lados, `git merge-file -p`
produjo preview sin conflicto textual en 19. Cuatro rutas fueron añadidas de forma
independiente después del merge-base (`supabase/templates/password-recovery.html`,
`tests/test_h3_password_recovery_contract.py`, `tests/test_password_policy_contract.py`,
`web/src/app/admin/reset-password/page.tsx`) y requieren comparación semántica. Esto
no acredita compatibilidad de comportamiento.

Decisiones conservadoras: mantener del baseline remoto
`STUDIAMATCH-H3-UAT-MOCK-02-REPORT.md` y
`.context/evidencia/h3req1_development_validation_2026-09-24.md`; excluir el
`.github/pull_request_template.md` local porque describe otro PR y contiene checks
prellenados obsoletos. Las cuatro migraciones locales nuevas son
`20260927_h3_publication_visibility_contract.sql`,
`20260928_h3_invitation_accept_email_regex_fix.sql`,
`20261001_h3_course_editorial_audit_availability.sql` y
`20261001_h3_invitation_reservation_compensation.sql`; su orden/compatibilidad Pro
no se ha validado. El fallback de redirect/CORS a un hostname Pages fijado en código
se retiró durante el port: Edge requiere `ADMIN_INVITE_REDIRECT_URL`,
`ADMIN_INVITE_RECOVERY_REDIRECT_URL` y `ADMIN_INVITE_ALLOWED_REDIRECTS` explícitos, y
falla cerrado si faltan o no coinciden. Falta validar la matriz conductual local y
confirmar configuración por ambiente antes de cualquier gate remoto.

La propuesta `protected-workflow-integrity.yml` aún no existe en el baseline remoto;
no se verificó que el check independiente esté requerido. El HIGH de integridad CI
permanece abierto. Nada de este preview mueve cambios ni resuelve GO local/remoto.

### Actualización de triage y UAT — 2026-10-02

El responsable eligió **Triage local** para el hallazgo de dependencias; no autorizó
waiver ni acción remota. El audit inicial `--include=dev` reportó 9 HIGH/0 CRITICAL,
con aviso raíz `GHSA-vfj7-8cjw-p6xm` sobre `braces <=3.0.3` (CVSS 7.5) vía
`micromatch@4.0.8`/`fast-glob` en shadcn y tooling ESLint de Next. `braces@3.0.3`
es la última versión consultada y no tiene fix compatible. Las sugerencias automáticas
de bajar `eslint-config-next` a 14.2.35 (incompatible con Next 16/ESLint 9) o cambiar
`shadcn@4.21.1` por `shadcn@1.0.0` (sin exports equivalentes) se rechazaron.

Tras validar en un snapshot separado, se aplicó únicamente la reclasificación de
`shadcn@4.21.1` a `devDependencies`; el paquete proporciona CSS importado por
`globals.css` en el build del static export, no un módulo runtime. Validaciones
aisladas: `npm ci` limpio, TSC, ESLint y build estático con PostgREST local PASS. Los
151 archivos de `out/` coinciden byte a byte con el export de UAT r14 y las versiones,
URLs e integridades de paquetes permanecen iguales; el lockfile marca dependencias
transitivas como dev. En el worktree, `npm audit --omit=dev` cierra **0 findings**;
`npm audit --include=dev` sigue en **9 HIGH/0 CRITICAL** (exit 1). No se aplicó
`npm audit fix`, downgrade ni waiver: el gate de auditoría completa sigue bloqueando
GO.

UAT visual preservada: r13 falló 142/144 por export mock incompleto/recursos de raíz;
r14 falló 143/144 con un timeout de captura móvil; r15 y r16 fallaron 142/144 por
timeouts de captura de la ruta pública raíz, sin fallos de aserción funcional en esas
ejecuciones. r16 afectó desktop/tablet y registró 0 errores de consola/requests; la
captura aislada posterior duró 901 ms desktop y 419 ms tablet, evidencia de posible
contención transitoria pero no reemplaza UAT. r17 cerró **PASS 48/48, 144/144, 144
capturas, cero retries**, generatedAt `2026-10-03T02:15:53.295Z`. Los artefactos
`r13`–`r17` se conservan bajo
`/tmp/h3req1-go-candidate-20261002-r14/evidence-expanded-uat-r{13..17}` dentro del
contenedor `studiamatch-h3req1-check`; no se reemplazaron rondas fallidas.

El primer intento separado de onboarding terminó esperando 30 s una respuesta del
primer POST UI, sin registrar invitación ni identidad Auth nuevas en PG17. La causa
localizada fue una carrera en el helper: tras verificar MFA esperaba solo un heading,
no confirmaba que `/api/admin/session` reportara AAL2 antes de navegar a usuarios.
Con espera explícita AAL2, el diagnóstico observó assurance AAL2, RPC
`admin_list_members_onboarding` HTTP 200 y el botón de invitación habilitado. Se
actualizó el helper para esperar AAL2, fallar con mensaje claro si el botón sigue
disabled y empezar la espera de response después del pacing con matcher de origen y
ruta exactos; syntax/typecheck focal pasan. La repetición paced cerró **PASS 10/10**
(INV-013, INV-008, INV-001, INV-002, INV-009, INV-007, INV-003, INV-004, INV-005,
INV-012), mínimo 20.1 s entre invitaciones. Resumen sanitizado y checksums en
`/tmp/h3req1-go-candidate-20261002-r14/evidence-onboarding-uat-r1`; no contiene
emails generados, mailbox ni tokens. El primer fallo permanece registrado y no se
atribuye a una invitación emitida.

Los gates posteriores a las últimas ediciones locales pasaron: pytest 283/4 (los
cuatro skips son integraciones live opt-in Supabase), TypeScript, actionlint,
shellcheck, escaneo de credenciales, diff check, Edge/BFF/SDK y pruebas directas y
workerd de suspensión/rutas. ESLint sigue con 0 errores y 9 warnings existentes.
El probe PG17 confirmó que `ROLLBACK` de una RPC revierte su contador SQL del mismo
transaction scope; riesgo MEDIUM de intentos no contabilizados, sin waiver. CI
independiente remoto, rollback Pages/Edge integrado, atestación/pilares/candidato
exacto siguen pendientes. El resultado permanece **NO-GO**.

### Continuación local posterior — ratificación y drill SQL acotado

El responsable ratificó **120 solicitudes/actor/minuto** para admisión independiente
Edge, adicional a las cuotas de entrega, sin aprobar secretos, bindings, SQL ni deploy
remotos. JIT separado aprobó ejecutar solo `tests/sql/h3_safe_suspend_harness.sql` en
`h3_final_uat_go_r14` PG17 desechable; no incluye otras bases ni Supabase Free/Pro.
Preflight confirmó PG17 17.11, schema H3 presente y cero conexiones activas ajenas.
Resultado `h3_safe_suspend_harness_ok` PASS tras aplicar dos veces el artefacto de
suspensión, preservar cohort/visibilidad/evidencia/auditoría, negar nuevos iniciadores,
completar/fallar/reconciliar reservas in-flight y restaurar grants exclusivamente como
paso TEST-ONLY. Inputs SHA-256: harness
`c1dcfef828b836e6627530127eb66a157db1df1437ad923a06f6c64e2c6782f1`,
rollback `09fcd8f6a5b9590f2e8db20f00c0fd9244ffd6a4a8db714c3c2837f04c22369d`;
log en `/tmp/h3req1-go-candidate-20261002-r14/evidence-safe-suspend-pg17-r1/`
del contenedor. Middleware fixture/workerd y Edge fixture PASS por separado; no existe
todavía un ensayo integrado simultáneo Pages + Edge + cookies + bindings + SQL.

Inventario estático: entre 94 archivos `db/migrations/2026*.sql`, solo
`20261002_h3_admin_quota_expand.sql` y `20261002_h3_admin_quotas.sql` emiten
`RAISE SQLSTATE 'PGRST'`; los originales versionados copiados en `private.h3_quota_base_*`
no lo hacen. El wrapper repropaga `PGRST` y deja la admisión dentro de la transacción:
una cancelación o rollback exterior revierte el evento, así que el límite directo SQL
solo asegura admisiones **confirmadas**. El inventario no demuestra ausencia de drift
en Pro ni cobertura de rechazos pre-RPC. No hay waiver ni GO mientras permanezca el
riesgo y el audit completo tenga 9 HIGH. La ratificación no cambia la necesidad de
JIT independientes de PR/DDL/secretos/deploy/rollback remotos.

### Diseño de mitigación solicitado — cuota directa y tooling (solo análisis)

Se investigó la cuota directa sin tocar schema ni alterar permisos. PostgreSQL
ejecuta `private.h3_take_admin_quota` dentro de la misma transacción que la RPC;
`SAVEPOINT`, subtransacción PL/pgSQL o manejo de `PGRST` pueden preservar admisiones
ante fallas internas, **pero no** ante `ROLLBACK` exterior. No se declarará
exactamente-once por intento desde una tabla SQL de esa misma transacción. Para cerrar
el bypass sin waiver, la dirección técnicamente viable es mover la admisión al
perímetro independiente y durable **antes** de llamar a la RPC: BFF/DO ya hace esto
para rutas Pages. Habría que impedir que un JWT de usuario invoque directamente las
RPC públicas iniciadoras sin pasar por BFF/DO; no basta con RLS porque el BFF envía
el mismo JWT para conservar `auth.uid()`. Una fase de expansión podría agregar un
gateway firmado, privado y limitado, conservando wrappers/ACL legacy durante la
transición; una fase contract revocaría el acceso directo tras validar JWT/AAL2/RBAC,
SDK, logout y finalizadores. Requiere diseño de firma/no replay, secretos por ambiente,
migraciones y revalidación integral; **no es una implementación aprobada ni aplicada**.
Edge service-role requiere admisión durable propia antes de Auth, sin rebajar
reserve-before-Auth ni bloquear finalizadores. Ninguna propuesta presupone deploy o
autorización para cambiar DB; mientras tanto solo se garantiza cuota sobre llamadas
SQL confirmadas, no todos los intentos.

Triage adicional del audit en Docker: registry NPM publica `braces@3.0.3` y
`micromatch@4.0.8` como últimas versiones consultadas. El plugin ESLint de Next
**latest** también depende de `fast-glob@3.3.1` (que usa `micromatch` → `braces`);
actualizar `eslint-config-next` dentro de Next 16 no cierra el aviso. El árbol
prod sin dev tiene 0 findings; los 9 HIGH son entradas propagadas por la misma
cadena del tooling de build/lint, no nueve vulnerabilidades raíz independientes.
Eliminar el CLI Shadcn requeriría sustituir y licenciar localmente el CSS importado,
pero **no** eliminaría la cadena ESLint; retirar la configuración oficial Next
suprimiría reglas core-web-vitals/TypeScript y degradaría calidad sin sustituto
probado. No aplicar overrides de paquetes sin compatibilidad demostrada ni disfrazar
dependencias de build como prod-free para declarar PASS del audit completo. Sin fix
upstream verificable o waiver formal (causa, evidencia, owner, riesgo, vencimiento y
aprobación humana), el gate de cero HIGH sigue **NO-GO**.

### Inventario GitHub autorizado solo lectura — sin bootstrap

`origin` apunta a `romelhc95/studiamatch`. Consultas autenticadas read-only:
`desarrollo@4eb4d877a50b012bb630a129bd0c74482c33be9c` figura protegida;
`.github/workflows/` remoto lista `security-audit.yml`, pero NO
`protected-workflow-integrity.yml`. No hay PR abierto con base `desarrollo`.
Colaboradores listados: `romelhc95` (admin) y `romelhc95-approver` (write), sin
aprobar ni mergear nada; los roles de revisión/merge deben confirmarse en un PR
concreto. La interfaz GitHub disponible no da endpoint de branch protection ni
required checks/rulesets, así que **no se acredita** que el job independiente esté
instalado o sea obligatorio. Bootstrap protegido del workflow y lectura verificable
de reglas/checks siguen bloqueantes; push, PR, review, merge y cambios de protección
requieren aprobaciones humanas separadas. No se modificó GitHub.

## Reevaluación y decisiones confirmadas — 2026-10-03

El responsable confirmó esta matriz como el conjunto único de gates y autorizó
integrar localmente un snapshot fijado de `braces`, avanzar con el diseño/implementación
local de un gateway firmado para las RPC Admin directas y consultar GitHub en lectura.
Esto no concede DDL/DML/grants, secretos, bindings, deploy ni escrituras GitHub.

### Tooling

Se integró en el WIP `braces@3.0.4-h3.1`, snapshot del commit
`28d440b5dd449dbf1fe6f3506cf94ecca4d02660` de `FSDevelop/braces` PR #72. El arreglo
añade límites de profundidad a parse/compile/expand/stringify. La procedencia, SHA,
licencia y condición de snapshot no oficial se registran en `web/vendor/README.md`.
En instalación limpia Docker del WIP: audit completo y prod 0 vulnerabilities,
904 tests upstream, TSC/lint/build PASS y 151 assets iguales a la referencia. El
responsable del seguimiento y la fecha de revisión del snapshot siguen sin confirmarse;
no declarar cerrado el pilar de mantenimiento hasta registrarlos. No es waiver.

### Cuotas — contrato aprobado, JIT todavía requerido

Se eligió el gateway firmado para impedir que llamadas directas no limitadas omitan
la admisión durable en Pages. La propuesta conserva el JWT de sesión y `auth.uid()`,
mantiene RLS/RBAC/MFA y requiere validar firmas en `pgrst.db_pre_request` antes de
servir RPC Admin; el BFF cuenta actor por Durable Object antes de emitir cada RPC.
La Edge mantiene el límite ratificado de 120/actor/minuto, reserva antes de Auth y
finalizadores de reservas fuera de la cuota de iniciación. La fuente Supabase confirma
que `db_pre_request` puede validar rate limits/denegar Data API directa, pero solo
cubre PostgREST.

La función SQL, configuración PostgREST, grants a `authenticator` y el harness PG17
no se han creado ni ejecutado. El JIT anterior abarcó exclusivamente
`h3_safe_suspend_harness.sql`; no es reutilizable. Antes de SQL local se requiere
JIT exacto para artefactos/operaciones/base PG17 desechable. Los flujos de Edge,
finalizadores, firma/replay, cancelación, fail-closed y comportamiento por ambiente
deben probarse antes de congelar el candidato.

### GitHub — consulta read-only de reglas

La rama remota `desarrollo` continúa en
`4eb4d877a50b012bb630a129bd0c74482c33be9c` y aparece protegida. El ruleset visible
`owner-only-protected-branch-updates` solo marca `Restrict updates`, permite bypass
`Always allow` a `romelhc95` y no marca PR obligatorio ni status checks. La pantalla
clásica de Branches permanece en `Loading...`; el endpoint REST protegido requiere
autenticación (`401`) y el MCP no expone esa lectura. Por ello sigue faltando evidencia
de protección clásica efectiva y required check `security-audit`; no inferirlos del
flag `protected` de la rama. Colaboradores listados: `romelhc95` admin y
`romelhc95-approver` write; la distinción de review/merge debe verificarse en el
flujo bootstrap. No hubo escrituras.

### Cierre de este corte

Pytest 283 passed/4 skips opt-in, TypeScript, actionlint, shellcheck, credential scan,
`git diff --check`, lint (0 errores/9 warnings) y build limpio PASS en el WIP o copia
limpia descrita en la evidencia. UAT r17 y onboarding 10/10 permanecen PASS de sus
cortes; el build produce los mismos assets, pero el candidato final aún no está
congelado. Continúan abiertos: owner/revisión del snapshot, JIT SQL gateway, rollback
integrado, CI efectivo, evaluación de seis pilares, revalidación final, hashes/paquete
PR y protocolo Development. **NO-GO integral** permanece.

El registro detallado y sus hashes están en
[evidencia de continuación 2026-10-03](../h3req1_readiness_continuation_2026-10-03.md).
