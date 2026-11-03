# UAT H3 — invitación Auth normal: preflight read-only

Fecha de consulta: `2026-10-01T03:39Z` (logs acotados a las 24 horas previas).
Estado: `BLOCKED` antes de solicitar una nueva JIT o ejecutar el único POST.

## Alcance

- Supabase Free/Development, project ref `aqrldlmlszjtgpqiegaa`.
- Preview: alias Development ya autorizado.
- No se consultaron ni modificaron Certification o Production.
- No hubo POST, email, lectura de buzón, callback, DDL, DML, deploy, cleanup,
  rollback, push, PR, merge ni promoción.
- El árbol tenía cambios locales previos; se preservaron.

## Edge y datos agregados

`admin-invite` está en v12, `ACTIVE`, `verify_jwt=true`, bundle SHA-256
`87329d8f47ff36917d13e237c09b39763d0088a114fd67acd351cc6642da2111`. El código
remoto contiene el caso `orphanedPendingReinvite`, mapea `auth_rate_limited` a
HTTP 429 y contiene una única llamada de compensación `failInvitation`.

La consulta SQL read-only devolvió solo conteos y timestamps; no expuso emails,
IDs, tokens ni metadatos privados:

| Métrica | Observado |
|---|---:|
| Auth users activos / eliminados | `0 / 0` |
| Identidades / sesiones / refresh tokens / one-time tokens | `0 / 0 / 0 / 0` |
| Factores MFA / factores verificados | `0 / 0` |
| Membresías / membresías activas | `0 / 0` |
| Invitaciones | `1 pending`, `2 superseded`, `2 send_failed` |
| Auditorías | `5`: `invite=1`, `resend=2`, `send_failed=2` |

La fila `pending` informa `expires_at=2026-09-30T02:32:39.726977Z`,
`last_sent_at=2026-09-28T02:32:39.726977Z` y `send_count=3`. No se mutó. Las
invitaciones y auditorías históricas permanecen intactas.

## Logs y gates operativos

La consulta agregada de `auth_logs`/`edge_logs` cubrió
`2026-09-30T03:39:20Z` a `2026-10-01T03:39:20Z`: no encontró coincidencias en
atributos para `over_email_send_rate_limit`, `admin-invite` ni `429`. La última
evidencia positiva conocida sigue siendo el HTTP 429 del intento anterior. La
ausencia de eventos recientes no demuestra que Supabase haya liberado el límite;
no se intentó comprobarlo mediante otro envío.

El template local `supabase/templates/invite.html` tiene un solo
`{{ .ConfirmationURL }}` y copy específico de invitación. El Dashboard Free abrió
Authentication → Email Templates, pero la vista accesible solo mostró el
encabezado y las pestañas; no permitió verificar el subject ni el cuerpo remoto,
ni confirmar que no sea el default. Recovery no se modificó.

La pestaña Preview existente mostró el formulario de login, no un panel autenticado
Admin/AAL2 ni el formulario preparado. No se navegó al callback.

## Decisión y transición

No se pidió una nueva JIT ni se ejecutó el POST: template remoto y sesión
Admin/AAL2 no estaban verificados. La sesión previa de autorización se considera
consumida y no vigente. No se declara UAT completada.

- `expand`: Edge v12 y sus marcadores quedaron confirmados; no hubo nuevo deploy.
- `compatibilidad`: se preservó el historial append-only.
- `deploy`: no se hizo deploy adicional.
- `contract`: pendiente de verificación manual del template, sesión Admin/AAL2,
  nuevo preflight read-only y nueva JIT para un único click.
- `rollback`: no ejecutado; cleanup/rollback necesitan autorización separada.

Estado global: `NO-GO_H3REQ1_DEVELOPMENT_REMOTE_VALIDATION`. Siguiente paso
humano: revisar subject y cuerpo Invite en Dashboard Free y restablecer la sesión
Admin/AAL2 en Preview; no compartir password, OTP, URL ni token.

## Resultado del único clic autorizado — 2026-10-01T04:11Z

Después de confirmar el formulario sin pulsar, se recibió una JIT nueva,
exclusiva para un clic de `Agregar usuario` en Free/Development. La herramienta
confirmó que se pulsó el botón una sola vez. No se hizo un segundo clic, retry ni
POST manual.

La consulta SQL read-only posterior devolvió únicamente agregados y estados:

| Métrica | Observado |
|---|---:|
| Auth users / identidades | `1 / 1` |
| Sesiones / refresh tokens / one-time tokens | `1 / 1 / 0` |
| Factores MFA | `1` (no se consultó si está verificado) |
| Membresías | `1` (no se leyó rol ni estado final) |
| Invitación nueva | `accepted` |
| Invitaciones históricas | `2 send_failed`, `1 expired`, `2 superseded` |
| Auditorías | `8`: `accept=1`, `password_set=1`, `invite=2`, `resend=2`, `send_failed=2` |

El estado `accepted` y las auditorías `accept`/`password_set` son inesperados en
este punto y no permiten atribuir quién realizó esas transiciones ni afirmar
`ready`/Admin/activa o AAL2. La herramienta de clic confirmó la interacción, pero
no se conservó ni se expuso el texto de respuesta de UI.

La verificación agregada de logs, acotada a
`2026-10-01T04:06:11Z`–`2026-10-01T04:11:11Z`, falló con error de backend. Por
eso no se confirma el `POST 200` ni el evento Auth de invitación. No se leyó el
buzón, ningún enlace o código, y no se navegó al callback.

**Decisión:** detenerse y pedir al usuario que confirme si completó manualmente
el onboarding después del envío. Hasta recibir esa confirmación, no se harán más
consultas de identidad/onboarding ni acciones mutantes. No se ejecutaron cleanup,
rollback o promoción; UAT continúa `NO-GO`.

## Post-check tras confirmación manual del usuario — 2026-10-01

El usuario confirmó que la autenticación/onboarding se completó manualmente. La
consulta SQL read-only posterior observó:

| Gate | Resultado |
|---|---|
| Auth user activo / identidad | `1 / 1`; sin duplicados |
| Membresía | `role=admin`, `is_active=true`, `account_status=ready` |
| Invitación reciente | `accepted`; `accepted_at` y `password_set_at` presentes |
| MFA | Un factor TOTP `verified` |
| Sesión actual | Una sesión `aal2` vigente |
| Auditoría | `8` filas: `accept=1`, `password_set=1`, `invite=2`, `resend=2`, `send_failed=2` |
| One-time tokens | `0` |

Esto valida el estado final del caso de invitación/onboarding y la membresía
Admin activa. No se validaron acciones negativas por otros roles. El agente no
abrió el buzón, no leyó enlaces/códigos y no aceptó la invitación. La consulta
agregada de logs del envío falló con error de backend; no se afirma el HTTP
`POST 200` ni se oculta esa brecha.

El usuario observa que la UI muestra el rol `Admin` sin un identificador de la
persona conectada. Se registra como requerimiento UX separado; no se modificó
frontend. Propuesta de siguiente alcance: conservar la insignia del rol y añadir
un identificador de sesión no secreto (nombre visible, con fallback acordado),
con pruebas responsive/accesibles y sin registrar el email en logs.

No se limpió Auth, membresías, invitaciones ni auditorías. Las filas de
invitaciones/auditoría permanecen append-only. Cualquier limpieza para reutilizar
el buzón requiere autorización JIT nueva, exacta y destructiva.

El caso específico queda `PASS_WITH_LOG_EVIDENCE_GAP`; UAT H3 global sigue
`NO-GO`. No hay `contract` global, rollback ni promoción.
