# Transporte Supabase para browser y BFF

## Propósito y frontera de confianza

`web/src/lib/supabase-transport.ts` exporta `createApiKeyOnlyFetch(apiKey, fetcher, policy?)`. Lo usan dos runtimes con políticas diferentes: `web/src/lib/supabase.ts` para las consultas públicas del SDK y `web/functions/_lib/admin-bff.ts` para llamadas server-side con JWT de sesión Admin. Mantiene las API keys modernas en el header `apikey` y evita que el SDK las copie como `Authorization: Bearer`.

La función es un control de transporte. No verifica criptográficamente el JWT ni reemplaza autenticación/autorización de Supabase Auth, RLS o gateway. No recibe ni requiere service-role/secret key. La fuente de asignaciones y relaciones es el [registro canónico](../trazabilidad/registro_fuentes_componentes.md#supabase-transport).

## Contrato API key y sesión

### Cliente público del SDK

`supabase.ts` construye `createApiKeyOnlyFetch(PUBLISHABLE_KEY, fetch)` sin `ServerSessionTransportPolicy`. Una cabecera Authorization idéntica a la publishable key se elimina; una sesión Bearer distinta no se acepta en esta ruta. Las consultas públicas usan `apikey`, origin y endpoints de Supabase configurados.

### Pages BFF

`admin-bff.ts` crea el server client con un `ServerSessionTransportPolicy` compuesto por:

- `projectOrigin`: origen exacto del proyecto Supabase configurado.
- `rpcAllowlist`: nombres de RPC permitidas por Admin.
- `rpcGateway`: `projectRef`, `keyId` y `hmacKey` por ambiente; la HMAC es secreta y separada de la clave de cuota.

Con policy, el JWT de usuario solo se reenvía al mismo origin, sin usuario/contraseña/hash en la URL, y por estas rutas/métodos:

| Ruta | Método admitido | Restricción adicional |
|---|---|---|
| `/rest/v1/rpc/<nombre>` | POST | `<nombre>` debe estar en `rpcAllowlist`; el body debe ser objeto JSON y no exceder 64 KiB serializados. |
| `/auth/v1/user` | GET, PUT | Proyecto configurado; Supabase Auth valida la sesión. |
| `/auth/v1/factors` | POST | Alta de factor MFA. |
| `/auth/v1/factors/<uuid>` | DELETE | UUID debe cumplir el patrón válido. |
| `/auth/v1/factors/<uuid>/challenge` y `/verify` | POST | Factor UUID válido. |
| `/functions/v1/admin-invite` | POST | Llamada Edge desde BFF; caller Edge limita sus destinos downstream por separado. |

Para RPC allowlisted, el helper cambia el endpoint al wrapper `admin_signed_rpc`. Firma metadatos (project ref, método, actor, timestamp, nonce y key ID) y un payload canónico que contiene el nombre RPC y args; reemplaza el body por `p_rpc_name`, `p_args` y `p_signed_payload`, y añade headers `x-studiamatch-admin-rpc-*`. Los headers de firma entrantes se limpian antes de calcular una firma nueva.

Límites observados en el código: la HMAC key requiere al menos 32 bytes UTF-8; `projectRef` acepta `[a-z0-9-]{1,64}`, y el valor `local` solo apunta a `localhost`/`127.0.0.1`; `keyId` acepta `[A-Za-z0-9._-]{1,32}`; el `sub` del JWT debe ser UUID; args JSON serializados no pueden exceder 64 KiB. `ADMIN_RPC_GATEWAY_HMAC_KEY` debe ser distinta de `ADMIN_QUOTA_HMAC_KEY`. Son validaciones locales, no valores para registrar ni evidencia de provisionamiento por ambiente.

El fetch usa `redirect: manual`; rechaza respuestas 3xx y `opaqueredirect`. Los redirects no transportan cookies/sesiones hacia otro destino.

## Datos, estado y errores

El helper lee URL, método, body, headers, configuración del proyecto y la claim `sub` del token para construir el actor. No almacena token, identity, nonce, args ni resultado. El BFF administra cookies HttpOnly; el transporte solo aplica la política al request que recibe.

Falla cerrado cuando la API key tiene formato inválido aguas arriba, el destino/origen no coincide, la sesión no tiene forma JWT, el método/path no está permitido, el factor ID es inválido, faltan args RPC, el JSON no es objeto, el payload supera 64 KiB, el gateway no tiene un ID/key de forma aceptada, el proyecto no coincide o hay redirect. Los callers deben convertir estos errores en respuestas sanitizadas; no registrar `Authorization`, body de sesión ni secretos.

Concurrencia y reintentos pertenecen a Auth/RPC/Edge/quotas. La firma incluye timestamp y nonce, y el wrapper valida replay según su contrato DB local. No se supone que repetir una llamada firmada sea idempotente. Para invitación, el caller conserva el request ID de idempotencia descrito en la ficha Admin y el RPC correspondiente.

## Consumidores, pruebas y estado

| Consumidor | Uso | Pruebas/lectura local |
|---|---|---|
| `web/src/lib/supabase.ts` | cliente SDK público, publishable key y consultas del catálogo | `tests/h3_supabase_sdk_headers_uat.mjs`, `tests/test_supabase_credentials_contract.py` |
| `web/functions/_lib/admin-bff.ts` | server client con cookies, allowlist, JWT y gateway firmado | `tests/test_supabase_credentials_contract.py`, `tests/h3_admin_bff_mock_uat.mjs`, `tests/test_admin_invite_edge_contract.py` |
| `supabase/functions/admin-invite/index.ts` | consumidor indirecto del contrato de invitación; no importa este módulo | contrato Edge/Auth en `tests/test_admin_invite_edge_contract.py` |

La matriz de relaciones enlaza imports y suites con su alcance. R178/R181/R182 acreditan solo los casos que cada evidencia declara; no se infiere un PASS por esta relación. La implementación y su firma son locales. HMAC provisionadas, wrapper activo, Edge desplegada, secretos, schema aplicado y adopción remota permanecen sin verificar.

## Cómo cambiarlo con seguridad

1. Antes de añadir path/método/tipo de identidad, actualizar el contrato y revisar caller browser/BFF/Edge, `admin-auth.ts`, `admin-bff.ts`, `supabase.ts`, la RPC wrapper y la lista de credenciales.
2. Mantener API keys solo en `apikey`; no abrir destinos, métodos o RPC arbitrarios y nunca introducir secretos en browser.
3. Actualizar `tests/test_supabase_credentials_contract.py` y los UAT de headers/BFF/Edge para el path afectado; ejecutar solo suites compatibles con los inputs cambiados y guardar evidencia con entorno/mock identificado.
4. Revisar RLS/grants/gateway en SQL local para la compatibilidad del contrato. Cualquier DDL, binding, HMAC, secret o deployment necesita aprobación/etapa separada; esta ficha no autoriza cambios remotos.
5. Correr checker de documentación, marker, credential scanner, typecheck/lint/build por impacto. No declarar adopción hasta lectura autorizada del ambiente.

## Navegación relacionada

[Backend](../backend.md#bff-y-contrato-de-error) · [Seguridad](../seguridad.md#modelo-de-confianza-y-permisos) · [Admin runtime](admin_runtime.md) · [Admin portal](admin_portal.md#componentes-compartidos) · [Frontend](../frontend.md#componentes-principales) · [Database](../database.md) · [Pruebas](../pruebas.md) · [Operación](../operacion.md) · [Índice](../indice.md)

## Fuentes y relaciones

La fila fuente es `web/src/lib/supabase-transport.ts`; consumers, operaciones, datos, suites y Git local se relacionan en el [registro verificable](../trazabilidad/registro_fuentes_componentes.md#supabase-transport). El contrato de credenciales sanitizado en `AGENTS.md` y las pruebas se actualizan en la misma revisión por impacto.

## Navegación histórica local

Evidencia preservada por proceso; cada catálogo enlaza sus documentos históricos individualmente y no es una autoridad operativa.

- [C03 integrado: sesiones, invitación y recuperación](../catalogos_historicos/c03_integrado.md#documentos-preservados)
- [Admin, autenticación e historia editorial](../catalogos_historicos/admin_auth_editorial.md#documentos-preservados)
- [Frontend público y UAT](../catalogos_historicos/frontend_publico_uat.md#documentos-preservados)
- [Infraestructura, seguridad y CI](../catalogos_historicos/infra_seguridad_ci.md#documentos-preservados)
- [Documentación, trazabilidad y transferencia](../catalogos_historicos/documentacion_trazabilidad.md#documentos-preservados)
- [Registros operativos históricos y JIT](../catalogos_historicos/operacion_jit.md#documentos-preservados)
- [Seguimiento y handoffs históricos](../catalogos_historicos/seguimiento_historico.md#documentos-preservados)
- [Documentación DB sustituida](../catalogos_historicos/database_legacy.md#documentos-preservados)
- [C03 — diagnóstico de arranque de runtimes locales](../catalogos_historicos/c03_inicio_runtime.md#documentos-preservados)
- [C03 — diagnósticos Docker, F1 y clasificadores](../catalogos_historicos/c03_diagnosticos_runtime.md#documentos-preservados)
