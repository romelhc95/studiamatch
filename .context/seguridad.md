# Seguridad y fronteras de confianza

> Estado: controles del candidato y lecturas remotas acotadas a 2026-10-13. No contiene valores de secretos. La verificación remota no es un GO ni prueba adopción del WIP.

## Modelo de confianza y permisos

| Frontera | Identidad/datos | Control local | Límite |
|---|---|---|---|
| Visitante → frontend público | Datos públicos de cursos/instituciones | Lectura por Supabase publishable key en header apikey y vista efectiva; filtros de publicación/actividad/calidad | No se supone que datos públicos sean confidenciales; el entorno remoto no se probó. |
| Browser → Admin | Cookie de sesión Supabase SSR, origen, host y actividad | Pages Functions same-origin, cookie HttpOnly/Secure, allowlist de host, CSRF/origin, cuotas | Excepciones localhost/mock solo en desarrollo aislado; no usar en Cloudflare. |
| BFF → Auth | JWT de sesión y API key publishable | `createApiKeyOnlyFetch` restringe destino, método y ruta al mismo proyecto; key solo en `apikey` | El JWT no llega al browser; el BFF no usa secret/service-role key. |
| BFF → PostgREST RPC | JWT de sesión, RPC y argumentos | Solo RPC POST allowlisted; `signAdminRpc` remapea a `admin_signed_rpc` y firma metadata/payload; SQL valida actor/key/nonce | Requiere `pgrst.db_pre_request` y claves espejo; configuración remota no consultada. |
| BFF → Edge `admin-invite` | JWT del solicitante y API key publishable | POST same-project allowlisted; `verify_jwt`, `getUser`, AAL2, origen y Admin activo | El BFF solo pasa la sesión; no tiene secret/service-role key. Despliegue remoto desconocido. |
| Edge → PostgREST RPC de invitación | Actor explícito y API key server-side `service_role` | El handler valida sesión, AAL2 y membresía antes de llamar RPC lifecycle; pre-request SQL local retorna temprano para `service_role` | Canal distinto del gateway HMAC. La key/configuración Edge y la migration aplicada remotamente no se verificaron. |
| Pipeline → servicios | Variables por environment, contenido externo, credenciales de proveedor | Jobs separados, gates de perfil y preflight de writer; scan de source paths activos | No se ejecutó proveedor/writer durante esta sesión. |
| Git local → remoto | Diff, actions y credenciales | hooks de escaneo y workflows de seguridad versionados | R15 confirmó branch protegida y un ruleset update; branch-protection API devolvió 403, por lo que approvals/required checks siguen sin verificar. Instalación de hooks local tampoco se consultó. |

## Hallazgos de preparación remota R15

El metadata Pages de Cloudflare clasifica `NEXT_SUPABASE_SECRET_KEY` como `plain_text` en preview y producción; su valor no fue leído. El contrato candidato requiere que la credencial server-side se maneje como secreto. Es un bloqueo de seguridad hasta que el owner confirme de forma segura la naturaleza del binding y, si aplica, autorice reaprovisionarlo/rotarlo. No imprimir ni copiar ese valor.

El proyecto Pages no muestra los bindings BFF de cuota/firma ni el Worker/DO local esperado. GitHub marca `desarrollo` protegida y lista un ruleset `update`, pero branch protection devolvió 403 y no se acreditaron required checks/approvals. `protected-workflow-integrity.yml` está en el candidato, no entre los workflows listados remotamente. Son discrepancias de configuración/provisión, no hallazgos de ejecución de runtime. Ver [reporte R15](evidencia/h3req1_g10_remote_preparation_2026-10-13_r15.md#github) y [paquete de integración](evidencia/h3req1_development_integration_package_2026-10-13_r15.md#permisos-posteriores-separados).

## Sesiones, MFA, RBAC e invitaciones

Los roles de aplicación son admin y user, persistidos en admin_members; account_status y is_active no sustituyen al rol. Las mutaciones sensibles requieren MFA AAL2 según RPC. Las transiciones de membresía bloquean auto-bloqueo y desactivar/retirar el último Admin activo. Las invitaciones conservan hash de token, lifecycle append-only, expiración, cadena de reenvío, request ID/idempotencia y reconciliación de envío. Audit tables rechazan UPDATE/DELETE.

La cookie HttpOnly evita exponer JWT al JavaScript de la interfaz. El BFF pasa el JWT del usuario a Auth y, para invitaciones, a la Edge Function del proyecto configurado. La Edge valida el JWT/AAL2/membresía y luego usa `NEXT_SUPABASE_SECRET_KEY` server-side en `apikey` para RPC de invitación, con `p_actor_user_id` explícito; esa llamada privilegiada no usa HMAC. La API key nunca se usa como `Authorization: Bearer`; esa cabecera queda para tokens proveedor y la excepción estrecha de JWT de sesión por ruta. Fuente local: `web/src/lib/supabase-transport.ts` (`signAdminRpc`), `supabase/functions/admin-invite/index.ts` y `20261004_h3_admin_rpc_signed_gateway_payload_bound_wrapper.sql` (`h3_admin_rpc_signed_gateway_pre_request`).

La ficha [transporte Supabase](componentes/supabase_transport.md#contrato-api-key-y-sesion) contiene la allowlist exacta, límites de payload/identidad, firma y consumidores browser/BFF. El helper aplica política de transporte; no valida criptográficamente el JWT ni reemplaza Auth, RLS o gateway SQL.

## Scanner, hooks y CI

- scripts/security/scan_credentials.sh recorre archivos/diffs y detecta patrones de credenciales; no demuestra que una credencial no exista en otros almacenes ni que el control remoto esté activo.
- .githooks/pre-commit y pre-push están versionados; el developer debe comprobar core.hooksPath en el clon. No se instaló ni alteró hooks en esta sesión.
- .github/workflows/security-audit.yml define escaneo, path guard, Python/tests, lint, typecheck, static build, workflow lint, DB gate y agregador security-audit.
- protected-workflow-integrity.yml valida cambios protegidos en PR contra ramas protegidas.
- H3 R182 acredita scanner y scope local 92/92 en Docker para el paquete R8. R14 registra su scanner/scope final; los workflows/checks remotos siguen separados y el WIP del candidato no tiene run remoto acreditado.
- La revisión R181 de paquete R8 reporta cero HIGH/CRITICAL/bloqueos en su alcance estático. No es certificación de seguridad de toda dependencia o runtime remoto.

## Correcciones conocidas y límites/riesgos

La historia local incluye fixes de Search Path mutable, errores RPC P0003/referencia ambigua, endurecimiento RLS, contrato de credenciales, callbacks/invitaciones y gateway firmado. Los commits prueban que los cambios existieron en la historia local; los resultados se citan desde pruebas/evidencias, no se infieren del mensaje de commit.

Riesgos que se mantienen explícitos: la edición Free puede tener límites de CORS indicados en la guía operativa; el estático publica campos autorizados y no ofrece secreto de contenido; locks de cuota/gateway necesitan config remota; servicios externos pueden fallar; scripts de maintenance incluyen writers y cross-environment; migraciones nuevas no implican schema aplicado. No se declaran waivers nuevos.

`supabase/functions/send-lead-emails/index.ts` presenta riesgo pendiente de verificación antes de reactivarlo: el source local no aplica una allowlist de métodos después de OPTIONS ni valida/limita el body antes de usar datos de lead; configura CORS abierto, puede enviar datos personales a destinatarios del body/catalog y contiene un destinatario literal de fallback cuando falta `ADMIN_EMAIL` (valor omitido). No reactivar hasta retirar/verificar ese fallback y revisar el contrato de datos. No se confirmó que la función esté desplegada ni que tenga un caller remoto. Esta observación estática no declara un incidente ni una vulnerabilidad remota confirmada; owner y resolución se deben asignar antes de cualquier activación, invocación o cambio de privacidad.

### Dependencia de seguridad `braces`

El candidato fija `braces` a un tarball local `3.0.4-h3.1` derivado del PR upstream #72 y commit `28d440b5dd449dbf1fe6f3506cf94ecca4d02660`; R15 verificó públicamente que el PR está cerrado/no merged y el paquete oficial consultado sigue en `3.0.3`. El snapshot local coincide byte/blob con 9/10 archivos del commit; el décimo solo difiere por la versión en `package.json`. Su hash está en [tecnologías](tecnologias.md) y el detalle está en [`web/vendor/README.md`](../web/vendor/README.md). Esto verifica procedencia de la copia, no un release oficial ni la suite en este producto; la suite de 904 tests mencionada allí es upstream.

El estado local incluye el tarball porque el manifest y lock JS lo consumen. R8 lo incluyó en el antecedente funcional. El paquete documental R9 lo deja fuera como dependencia, de acuerdo con la instrucción de transferencia; por ello el paquete combinado no debe declararse reconciliado hasta que G10 decida explícitamente entre mantener la excepción con auditoría/validación renovadas o sustituirla por un release oficial validado. El [manifiesto R14](evidencia/h3req1_pr_scope_manifest_2026-10-13_r14_reconciled.json) registra a Romel como owner y `2026-11-03` como revisión prevista; R15 conserva la disposición y no cambia ese follow-up. Es una asignación local, no un waiver ni prueba de adopción remota.

## Evidencia y fuentes

Código: web/functions/_middleware.ts; web/functions/_lib/admin-bff.ts; web/src/lib/admin-auth.ts; supabase/functions/admin-invite/index.ts; migraciones 20260828_h3_admin_auth.sql, 20260829_h3_rbac_users.sql, 20260830_h3_expanded_contract.sql, 20260918–28_h3*, 20261002_h3_admin_quota_expand.sql y 20261004_h3_admin_rpc_signed_gateway*.sql.

Herramientas: scripts/security/, .githooks/, .github/workflows/security-audit.yml, protected-workflow-integrity.yml; tests/test_supabase_credentials_contract.py; tests/test_protected_workflow_review.py. Evidencia fechada: [R178](evidencia/h3req1_g09_local_close_r178_2026-10-11.md), [R181/R182](evidencia/h3req1_g10_r8_review_corrections_r181_2026-10-12.md), [scope/scanner R182](evidencia/h3req1_g10_scope_scan_r182_2026-10-12.txt). Estado remoto: desconocido.

## Navegación relacionada

[BFF/Admin runtime](componentes/admin_runtime.md) · [Portal Admin](componentes/admin_portal.md) · [Transporte Supabase](componentes/supabase_transport.md) · [Pruebas](pruebas.md) · [CI/CD](ci_cd.md) · [Operación](operacion.md) · [Contratos de backend](backend.md) · [Evidencia remota R15](evidencia/h3req1_g10_remote_preparation_2026-10-13_r15.md) · [Paquete de integración](evidencia/h3req1_development_integration_package_2026-10-13_r15.md) · [Hitos](hitos/README.md) · [Decisiones](decisiones/README.md) · [Historia y evidencia](indice.md#historia-y-evidencia) · [Índice](indice.md)

Registro por fuente: [seguridad y tooling](trazabilidad/registro_fuentes_componentes.md#seguridad-y-tooling).
