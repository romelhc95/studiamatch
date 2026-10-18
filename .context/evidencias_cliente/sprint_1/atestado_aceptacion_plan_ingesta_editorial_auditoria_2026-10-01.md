# Atestación sanitizada — aceptación del plan editorial y auditoría

| Campo | Valor |
|---|---|
| Fecha | `2026-10-01` |
| Fuente cliente | `SRC-REQ-002`, trazado por `ADENDA-REQ-EST-001-001` y criterios `H2-CA2`, `H2-CA3`, `H3-CA4` |
| Evidencia | Conformidad explícita del cliente comunicada por el responsable humano del proyecto con el plan versionado en `plan_remediacion_ingesta_editorial_auditoria_2026-10-01.md` |
| Resultado | `CLIENT_PLAN_ACCEPTED_LOCAL_EXECUTION` |
| Contrato | No se crea ni modifica un contrato comercial; se acepta el plan de implementación dentro del alcance Sprint 1/Hitos 2–3 ya versionado |
| Autorización técnica | Implementación y validación local en Docker/PG17 hasta GO local |
| No autorizado | Supabase remoto (DDL/DML/writers), Auth remoto, Cloudflare real, deploy, schedules, `workflow_dispatch`, push, PR, merge, Certification, Production o promoción |
| Sanitización | No se incorpora el documento privado, texto contractual, precios, PII ni detalles confidenciales |

## Criterios aceptados y trazabilidad

La aceptación comunicada aplica al plan citado como interpretación implementable
de los criterios ya versionados. La tabla no amplía los criterios contractuales
base ni sustituye las atestaciones H2/H3 existentes.

| Criterio del plan | Trazabilidad existente | Límite aceptado |
|---|---|---|
| Pipeline tolerante a datos parciales; curso nuevo pendiente para revisión y sin publicación automática | `H2-CA2`, `H2-CA3`; [HITO-002](../../hitos/hito_002.md) | Mantener gates e idempotencia; no ejecutar writers remotos |
| Admin puede completar/corregir manualmente campos editoriales; separar faltantes de inconsistencias y conservar ownership | `H3-CA4`; [HITO-003](../../hitos/hito_003.md), contrato de campos | Validar roles y cambios permitidos; no otorgar a `user` permisos adicionales por inferencia |
| Cada mutación conserva actor y valores previos/nuevos en auditoría append-only y Admin puede consultar historial protegido | Auditoría editorial de `H3-CA4` y conformidad explícita con el plan | No abrir lectura directa de auditoría al navegador, no alterar ni borrar historial |
| Disponibilidad se resuelve solo con evidencia trazable/vigente; ausencia o evidencia caducada permanece `unknown` | Regla de publicación segura aceptada en el plan | No inferir disponibilidad ni hacer backfill remoto; ante ambigüedad conservar `unknown` y detener publicación |
| Vista efectiva y rutas estáticas deben reflejar curso elegible sin degradar legado | Compatibilidad con static export de `H3-CA4` y transición del plan | Mantener fase legacy; ningún deploy o contracción de ambientes compartidos queda autorizado |
| Identidad visible de la sesión Admin | Solicitud explícita del responsable humano del proyecto, 2026-10-01 | Mostrar el correo del usuario autenticado en el encabezado en lugar de su rol; el rol continúa gobernando permisos y no se agrega un username |

## Alcance y efecto

Esta atestación registra la conformidad humana comunicada y vincula el plan a las
referencias sanitizadas existentes. No afirma que el agente abrió o versionó la
fuente privada. El plan se implementa únicamente como cambio local y se debe
revalidar frente a sus criterios al cierre; cualquier ambigüedad de negocio que
no permita una regla fail-closed vuelve a `NO-GO` y requiere decisión humana.

La aceptación del 2026-10-01 incluye además el cambio local del encabezado Admin:
usar el correo de la sesión Auth autenticada como identidad visible, en lugar del
distintivo de rol. No crea contrato nuevo, no solicita username único ni modifica
RBAC, Auth remoto o membresías.

## Adenda de decisiones — seguridad de sesión y evidencia — 2026-10-01

El responsable humano del proyecto confirmó que el alcance del borrador
`borrador_bff_httponly_admin_h3req1_2026-10-01.md` está alineado con la fuente
privada del cliente y debe incorporarse a esta evidencia sanitizada. Esta adenda
registra el alcance aceptado para diseño e implementación **local**:

| Decisión | Resultado aceptado | Límite |
|---|---|---|
| Sesión Admin | Mover Auth y operaciones Admin al BFF same-origin de Cloudflare Pages Functions y proteger la sesión con cookie HttpOnly; conservar RBAC, MFA y static export. | La elección concreta de adapter/runtime debe validarse localmente. No autoriza Preview, Auth remoto ni deploy. |
| Transición de sesiones existentes | Expirar/limpiar la sesión legacy del navegador y solicitar nuevo login con la cuenta y MFA existentes. | No crear otra cuenta, reinvitar ni repetir onboarding. No canjear tokens legacy server-side. |
| Identidad hacia RPC Admin | Autorizar al BFF a enviar el JWT de sesión del usuario como Bearer solo a RPCs allowlisted de Supabase Data API; la publishable key permanece separada en `apikey`. | Solo server-side; conservar RLS, `auth.uid()`, RBAC y MFA. Nunca enviar API keys como Bearer, exponer el JWT al browser ni sustituir la identidad por service role. Actualizar el inventario contractual. |
| Disponibilidad | Máximo global de **90 días calendario** desde `observed_at`; `valid_until` no puede exceder `observed_at + 90 días`. | Evidencia ausente, inválida o vencida permanece `unknown`; no se infiere disponibilidad. |
| Clasificación de inconsistencias | Sin clasificador automático en este ciclo. Admin revisa faltantes y diferencias entre pipeline/override, y decide/corrige según su rol. | No etiquetar automáticamente un dato como incorrecto. Categorías o reglas nuevas requieren decisión y atestación antes de implementarse. |

Esta adenda no versiona ni reproduce la fuente privada; registra la confirmación
sanitizada del responsable. No autoriza Supabase remoto, Auth/correo, Preview,
deploy, push, PR, merge, cleanup, rollback ni promoción; cada operación conserva
su gate JIT independiente. El estado global permanece `NO-GO` hasta validar todos
los criterios contra el mismo candidato.

La autoridad viva continúa en
[Estado Del Proyecto](../../estado_del_proyecto.md). Esta evidencia no cambia el
estado global `NO-GO_H3REQ1_DEVELOPMENT_REMOTE_VALIDATION` ni concede JIT para
acciones remotas.

## Aprobación acotada de transporte JWT — continuación Build 2026-10-02

El responsable aprobó explícitamente `Aprobar cierre` para registrar y endurecer el
transporte server-side existente, sin rediseñar Auth/MFA/invitaciones ni ampliar
RBAC. Esta adenda sustituye el límite exclusivamente RPC de la decisión anterior
solo en los destinos enumerados; no agrega funcionalidad de negocio.

| Origen de identidad | Proyecto/destino permitido | Método |
|---|---|---|
| BFF: sesión leída de cookie HttpOnly | Proyecto Supabase configurado, RPCs Admin ya allowlisted | POST |
| BFF: misma sesión | Auth `/auth/v1/user` | GET, PUT |
| BFF: misma sesión | MFA `/auth/v1/factors`, `/factors/<uuid>/challenge`, `/factors/<uuid>/verify`, `/factors/<uuid>` | POST (alta/challenge/verify), DELETE (baja) |
| BFF: misma sesión | Edge `/functions/v1/admin-invite` | POST |
| Edge: JWT del solicitante validado por Auth | Mismo proyecto configurado, `/auth/v1/user` | GET |

API keys exclusivamente en `apikey`. El JWT no se expone ni persiste en JavaScript
del navegador, no se envía a tablas Data API ni a destinos arbitrarios, y service
role no sustituye al usuario. Bloquear redirecciones que pudieran reenviar identidad.
Supabase verifica firma/expiración/identidad; comprobar formato no autentica.
Login, OTP/PKCE y renovación se inventarían como operaciones separadas de Auth:
no autorizan Bearer arbitrario por el hecho de usar `apikey`.

Autorización limitada a documentación, implementación y pruebas locales Docker.
No concede lectura/escritura Supabase/Auth, Git/CI remoto, Cloudflare, deploy,
reset de cuentas ni promoción. GO sigue condicionado a gates y reauditoría.

## Verificación de necesidad GET factores — decisión humana 2026-10-05

Ante un hallazgo estático que afirmaba que `listFactors()` necesitaba
`GET /auth/v1/factors`, el responsable autorizó añadir únicamente esa ruta/método
y una regresión SDK local. Antes de ampliar la allowlist, la inspección Docker de la dependencia fijada
`@supabase/auth-js` 2.109.0 demostró que `listFactors()` llama `getUser()` y deriva
los factores de `user.factors`, por lo que el destino real es el GET
`/auth/v1/user` ya permitido.

| Decisión recibida | Hallazgo reproducible | Resultado de alcance |
|---|---|---|
| Aprobación para `GET /auth/v1/factors` únicamente si era necesario para listar factores existentes | El SDK actual solicita GET `/auth/v1/user`; no solicita GET `/auth/v1/factors` | Se conserva la allowlist original; no se implementa ni consume la ampliación innecesaria. |

La regresión local usa sesión sintética, comprueba el request real de
`listFactors()` y mantiene restringidos origen/proyecto, headers, redirects y
métodos. No reabre ni repite el PASS remoto Auth+MFA histórico, no cambia ni
reinicia factores/cuentas, y no concede JIT para llamadas Auth remotas, correo,
secretos, Cloudflare, Git remoto o despliegue.
