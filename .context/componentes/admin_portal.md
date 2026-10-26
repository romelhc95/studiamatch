# Componente: portal Admin

## Propósito y límites

Interfaz para cola editorial, edición/vista previa, control de publicación, gestión de miembros e onboarding. No accede directo a tablas privadas desde el browser: llama el BFF same-origin.

## Cola editorial

`web/src/components/AdminCourseQueue.tsx` se monta desde `/admin/` después de que la página resuelve el rol `admin` o `user`. La cola comprueba AAL2 antes de consultar facetas y filas; la autorización final sigue en el BFF, RPC y base de datos. Los valores iniciales de filtros difieren por rol: `admin` abre `pending_review`/`complete`, `user` abre `draft`/`pending`.

El componente pide facetas y conteos (`admin_get_course_queue_facets`, `admin_count_course_queue_filtered`) y filas con `admin_get_course_queue_filtered`. Envía filtros editorial/calidad/institución, page size 20 y cursor opaco serializado; la búsqueda por nombre se aplica localmente al lote recibido. Mantiene cursor actual/historial, resultados, conteo y errores en estado React. No modifica cursos: la edición/publicación pertenece a `/admin/edit/` y sus RPC.

Si no hay AAL2 presenta `MfaRequiredCard`; si fallan facetas o filas muestra error y reintento; una respuesta sin filas vacía la cola sin mutar datos. La UI puede mostrar errores del BFF y debe continuar usando el wrapper same-origin. Al cambiar filtros reinicia el historial de cursores. Si cambia shape, orden estable, cursor, estado o RPC, coordinar la función SQL, BFF allowlist/contrato, roles, índices y `tests/test_h3_admin_queue_ux_contract.py`/MFA; revisar además el UAT local R178 sin atribuirle cobertura nueva.

El encabezado de `/admin/` apila identidad y acciones en anchuras menores a `sm` y permite que estas envuelvan; el test local `tests/admin_header_responsive.test.mjs` protege las clases responsivas seleccionadas, pero no sustituye medición visual en navegador. `AdminCourseQueue` asigna una generación a cada consulta y solo permite que la solicitud más reciente actualice resultados, error o estado de carga. El evento de cambio de estado o institución invalida inmediatamente la generación anterior antes del próximo efecto/solicitud; esto cubre también el intervalo entre actualizar el filtro y comenzar la nueva lectura. `web/src/lib/admin-queue-request-guard.mjs` contiene los predicados puros y `tests/admin_queue_request_guard.test.mjs` cubre respuesta fuera de orden y respuesta que llega durante esa ventana. Los filtros, facetas, conteos y cursor siguen consumiendo las mismas RPC sin cambios de contrato. Repetir la lectura/orden de cola Admin y el encabezado móvil requiere el Preview/Development que contenga el candidato; la sesión Gmail observada en el deployment anterior no valida estas correcciones.

## Política de contraseñas

`web/src/lib/password-policy.ts` ofrece validación previa y mensajes para `/admin/setup-password/` y `/admin/reset-password/`, además de `PasswordInput` y `PasswordRequirements`. La UI exige 12 puntos de código Unicode, minúscula/mayúscula ASCII, dígito ASCII, símbolo de su allowlist y coincidencia de confirmación. Contraseña y confirmación son valores transitorios del cliente: no se guardan ni se registran aquí.

La aplicación también valida en server-side: `web/functions/_lib/admin-bff.ts` exige 12–128 unidades UTF-16, mayúscula/minúscula ASCII, dígito y cualquier carácter fuera de `[A-Za-z0-9]` antes de llamar `auth.updateUser`; Auth conserva la validación final. Las dos reglas no son idénticas: una secuencia Unicode puede contar distinto y el conjunto de símbolos de la UI es más estrecho. No las “alinear” incidentalmente al cambiar una capa; el cambio de contrato requiere decisión de producto/auth y actualización coordinada de ambas.

Ante una regla nueva o cambiada, revisar la política de cliente, gate server-side BFF, errores accesibles, ambas páginas, `PasswordInput`, `PasswordRequirements`, `admin-auth.updateAdminPassword`, `tests/test_password_policy_contract.py` y `tests/test_h3_password_recovery_contract.py`; revisar `tests/test_mfa_compatibility_contract.py` si cambia onboarding. La búsqueda local de `tests/` no encontró un caso dedicado que rechace en ejecución una contraseña inválida en el endpoint BFF; impacto: las reglas de servidor podrían divergir sin que esa capa tenga un test focal. Seguimiento: añadir ese caso cuando se cambie funcionalmente la validación (owner no asignado en este corte). No relajar el gate server-side ni registrar valores.

## Recuperación con MFA

La página de reset comprueba que exista una sesión BFF autenticada; el callback de recuperación establece esa sesión en el flujo previsto, pero el runtime no conserva una marca separada que impida abrir la ruta con otra sesión Admin activa. Antes del cambio de contraseña, el BFF valida el inventario MFA y assurance; si encuentra cualquier factor verificado o Auth informa `nextLevel=aal2`, exige `currentLevel=aal2`; listas, niveles ausentes/malformados o errores fallan cerrado sin llamar a Auth. Supabase Auth aplica además su propio requisito AAL2 para cambiar una contraseña con MFA habilitado. El SDK puede devolver niveles AAL nulos; la recuperación contrasta esa respuesta con el inventario de factores, en vez de tratar `null` como error o como prueba de que no hay MFA. El endpoint separado `recovery_assurance` devuelve `hasVerifiedFactor` y solo los IDs de TOTP verificados; el BFF reconoce `totp`, `phone` y `webauthn`, y bloquea factores verificados no compatibles con esta pantalla. Tipos desconocidos y UUID no canónicos fallan cerrados. Si hay TOTP verificado, la UI solicita el código, permite elegir entre varios, revalida el factor antes del challenge, crea un challenge nuevo por intento y confirma `aal2` antes de habilitar la contraseña. Un `nextLevel=aal2` sin TOTP verificable bloquea el flujo. No enrola ni elimina factores, limpia el código y no persiste la contraseña. `AdminCourseQueue` interpreta `currentLevel=null` como AAL1 y sigue requiriendo AAL2. Admin-Invite envía callback explícito; el reset manual desde Supabase Dashboard omite el redirectTo del caller y depende del Site URL y de los action hrefs activos.

Validación focal en Docker: ESLint pasó con 0 errores y nueve warnings en `HomeContent.tsx` sin cambios; TypeScript y el build estático pasaron. `tests/h3_admin_bff_mock_uat.mjs` pasó 127/127; las siete funciones de recuperación y las siete de compatibilidad MFA pasaron por invocación directa (14/14, no pytest); las cuatro funciones de `tests/test_password_policy_contract.py` pasaron (4/4), `h3_admin_auth_error_uat.mjs` pasó 7/7 y `py_compile` pasó. El build temporal usó URL Free y un valor publicable de fixture con prefijo válido, sin conexión Auth; sus artefactos se quedaron en `/tmp` del contenedor. `h2_web_mock_smoke.sh` terminó con `h2_web_mock_smoke_ok` y verificó portada/detalle sintéticos; no valida catálogo remoto. El guard de rutas protegidas/negativos, comparación del candidato, `bash -n`, ShellCheck 0.11.0, escáner de credenciales árbol y gate documental/self-test pasaron en Docker. La revisión Codex Security del snapshot que incluye este último delta está pendiente de completar antes de publicar. No se ha ejecutado el caso remoto.

## Componentes compartidos

La cola usa primitives visuales y el renderer público en la vista previa del editor. Sus responsabilidades compartidas están documentadas en [presentación web compartida](presentacion_web_compartida.md); no pertenecen exclusivamente a Admin. El transporte HTTP/API-key y JWT de sesión está en [Supabase transport](supabase_transport.md), y los límites server-side en [runtime Admin](admin_runtime.md).

## Fuentes, contratos y datos

- Rutas: /admin/, login, auth/callback, accept-invite, setup-password, reset-password, edit y users; source en web/src/app/admin/.
- Componentes: AdminCourseQueue, AdminSessionGuard, MfaRequiredCard, PasswordInput/Requirements, CourseLivePreview, editorial-ui.
- Cliente: web/src/lib/admin-auth.ts; RPC allowlist y shapes en backend.md.
- Datos: sesión Auth, role/is_active/account_status, queue, curso editorial, version optimista, disponibilidad con evidencia/fecha/actor, auditoría e invitations.

## Consumidores, pruebas y operación

Miembros Admin/user consumen la UI por host aprobado. MFA AAL2 protege acciones sensibles. Contratos/tests H3 incluyen local mock, Postgres 17 y runtime Pages local. R178 registra 10/10 onboarding en la ejecución nombrada, UAT viewport y límites; no es UAT remota.

## Fuentes

Rutas bajo `web/src/app/admin/`, `web/src/components/AdminCourseQueue.tsx`, `web/src/components/admin/`, `web/src/lib/admin-auth.ts` y `web/src/lib/password-policy.ts`; H3 migrations y atestación sanitizada de Sprint 1. Implementación candidata; schema/deploy remoto sin verificar. Los primitives, renderer y transporte compartidos enlazados arriba mantienen fichas separadas.

## Navegación relacionada

[Frontend](../frontend.md) · [Backend](../backend.md) · [Database](../database.md) · [Seguridad](../seguridad.md) · [Pruebas](../pruebas.md) · [Requerimientos](../requerimientos/README.md) · [HITO-003](../hitos/hito_003.md) · [R178](../evidencia/h3req1_g09_local_close_r178_2026-10-11.md) · [Índice](../indice.md)


## Mapa de fuentes, consumidores y suites

La tabla contiene una fila por path del componente y se deriva de la búsqueda estática local enlazada; los consumers de Next se marcan como convención y las ausencias quedan limitadas al alcance. No añade resultados de ejecución.

| Fuente | Consumidor/entrada | Suite con referencia o ausencia en scope |
|---|---|---|
| `web/src/app/admin/accept-invite/page.tsx` | Next.js App Router convention (URL/layout/favicon entry); direct importer: none expected | sin referencia literal de path en el scope de tests; assertions por símbolo requieren revisar suite |
| `web/src/app/admin/auth/callback/page.tsx` | Next.js App Router convention (URL/layout/favicon entry); direct importer: none expected | sin referencia literal de path en el scope de tests; assertions por símbolo requieren revisar suite |
| `web/src/app/admin/edit/page.tsx` | Next.js App Router convention (URL/layout/favicon entry); direct importer: none expected | `tests/h3_local_uat.mjs`, `tests/test_h3_admin_queue_ux_contract.py` |
| `web/src/app/admin/layout.tsx` | Next.js App Router convention (URL/layout/favicon entry); direct importer: none expected | sin referencia literal de path en el scope de tests; assertions por símbolo requieren revisar suite |
| `web/src/app/admin/login/page.tsx` | Next.js App Router convention (URL/layout/favicon entry); direct importer: none expected | `tests/test_admin_invite_edge_contract.py`, `tests/test_h3_admin_queue_ux_contract.py`, `tests/test_mfa_compatibility_contract.py` |
| `web/src/app/admin/page.tsx` | Next.js App Router convention (URL/layout/favicon entry); direct importer: none expected | `tests/test_h3_admin_queue_ux_contract.py` |
| `web/src/app/admin/reset-password/page.tsx` | Next.js App Router convention (URL/layout/favicon entry); direct importer: none expected | `tests/test_h3_password_recovery_contract.py`, `tests/test_mfa_compatibility_contract.py`, `tests/test_password_policy_contract.py` |
| `web/src/app/admin/setup-password/page.tsx` | Next.js App Router convention (URL/layout/favicon entry); direct importer: none expected | `tests/test_mfa_compatibility_contract.py` |
| `web/src/app/admin/users/page.tsx` | Next.js App Router convention (URL/layout/favicon entry); direct importer: none expected | `tests/h3_local_uat.mjs`, `tests/test_h3_admin_queue_ux_contract.py` |
| `web/src/components/admin/AdminSessionGuard.tsx` | web/src/app/admin/layout.tsx | `tests/test_h3_admin_queue_ux_contract.py` |
| `web/src/components/admin/CourseLivePreview.tsx` | web/src/app/admin/edit/page.tsx | `tests/test_h3_admin_queue_ux_contract.py` |
| `web/src/components/admin/MfaRequiredCard.tsx` | web/src/app/admin/edit/page.tsx, web/src/app/admin/users/page.tsx, web/src/components/AdminCourseQueue.tsx | `tests/test_mfa_compatibility_contract.py` |
| `web/src/components/AdminCourseQueue.tsx` | web/src/app/admin/page.tsx; RPC `admin_get_course_queue_facets`, `admin_get_course_queue_filtered`, `admin_count_course_queue_filtered` vía `adminRpc` | `tests/test_h3_admin_queue_ux_contract.py`, `tests/test_mfa_compatibility_contract.py` |
| `web/src/components/admin/PasswordInput.tsx` | web/src/app/admin/reset-password/page.tsx, web/src/app/admin/setup-password/page.tsx | sin referencia literal de path en el scope de tests; assertions por símbolo requieren revisar suite |
| `web/src/components/admin/PasswordRequirements.tsx` | web/src/app/admin/reset-password/page.tsx, web/src/app/admin/setup-password/page.tsx | sin referencia literal de path en el scope de tests; assertions por símbolo requieren revisar suite |
| `web/src/components/admin/editorial-ui.tsx` | web/src/app/admin/edit/page.tsx, web/src/components/AdminCourseQueue.tsx | sin referencia literal de path en el scope de tests; assertions por símbolo requieren revisar suite |
| `web/src/lib/admin-auth.ts` | web/src/app/admin/accept-invite/page.tsx, web/src/app/admin/auth/callback/page.tsx, web/src/app/admin/edit/page.tsx, web/src/app/admin/login/page.tsx, web/src/app/admin/page.tsx, web/src/app/admin/reset-password/page.tsx, web/src/app/admin/setup-password/page.tsx, web/src/app/admin/users/page.tsx, web/src/components/AdminCourseQueue.tsx, web/src/components/admin/AdminSessionGuard.tsx, web/src/components/admin/MfaRequiredCard.tsx | `tests/h3_admin_auth_error_uat.mjs`, `tests/test_h3_admin_queue_ux_contract.py`, `tests/test_mfa_compatibility_contract.py` |
| `web/src/lib/password-policy.ts` | setup-password/page.tsx, reset-password/page.tsx, PasswordInput.tsx, PasswordRequirements.tsx; validation continua en admin-auth→`/api/admin/auth/password` | `tests/test_password_policy_contract.py`, `tests/test_h3_password_recovery_contract.py`, `tests/test_mfa_compatibility_contract.py`; no se encontró prueba de rechazo de password inválido en el BFF |

## Fuentes y relaciones

La asignación de cada ruta/UI, símbolos, contratos HTTP/RPC, consumidores, datos, pruebas y estado es el [registro fuente-componente](../trazabilidad/registro_fuentes_componentes.md#portal-admin). La sesión y los roles de la UI no sustituyen los gates del BFF ni RLS.

## Navegación histórica local

Evidencia preservada por proceso; cada catálogo enlaza sus documentos históricos individualmente y no es una autoridad operativa.

- [C03 integrado: sesiones, invitación y recuperación](../catalogos_historicos/c03_integrado.md#documentos-preservados)
- [Admin, autenticación e historia editorial](../catalogos_historicos/admin_auth_editorial.md#documentos-preservados)
- [Frontend público y UAT](../catalogos_historicos/frontend_publico_uat.md#documentos-preservados)
- [Pipeline, datos y base de datos](../catalogos_historicos/pipeline_base_datos.md#documentos-preservados)
- [Infraestructura, seguridad y CI](../catalogos_historicos/infra_seguridad_ci.md#documentos-preservados)
- [Documentación, trazabilidad y transferencia](../catalogos_historicos/documentacion_trazabilidad.md#documentos-preservados)
- [Registros operativos históricos y JIT](../catalogos_historicos/operacion_jit.md#documentos-preservados)
- [Evidencia histórica de requerimientos e hitos](../catalogos_historicos/requerimientos_hitos.md#documentos-preservados)
- [Seguimiento y handoffs históricos](../catalogos_historicos/seguimiento_historico.md#documentos-preservados)
