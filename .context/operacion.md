# Operación local y ambientes

> Esta guía describe nombres/configuración, no almacena credenciales. No abrir .env operativo para completar la documentación.

## Ambientes y datos

La guía ejecutable declara Supabase Free como Development/Certification y Pro como Production; Pro es baseline autoritativo de schema. Los scripts/cliente usan variables NEXT_PUBLIC_SUPABASE_URL, SUPABASE_URL, NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY, NEXT_SUPABASE_PUBLISHABLE_KEY y, solo para writers autorizados/CI, NEXT_SUPABASE_SECRET_KEY. Cloudflare AI consume CF_ACCOUNT_ID/CF_API_TOKEN; el código de enrichment actual también lee OPENCODE_API_KEY.

Pages Functions/Admin bindings requieren SUPABASE_URL o NEXT_PUBLIC_SUPABASE_URL, NEXT_SUPABASE_PUBLISHABLE_KEY, ADMIN_ALLOWED_HOSTS, ADMIN_QUOTA, ADMIN_QUOTA_HMAC_KEY, ADMIN_RPC_GATEWAY_HMAC_KEY y ADMIN_RPC_GATEWAY_KEY_ID; la autenticidad de sesión usa ADMIN_SESSION_ACTIVITY_HMAC_KEY. Las dos HMAC keys principales son distintas. Edge invitation usa nombres ADMIN_INVITE_ALLOWED_ORIGINS, ADMIN_INVITE_ALLOWED_REDIRECTS, ADMIN_INVITE_REDIRECT_URL, ADMIN_INVITE_RECOVERY_REDIRECT_URL, ADMIN_INVITE_RESEND_COOLDOWN_SECONDS y ADMIN_INVITE_SAFE_SUSPEND. No se registran valores.

GitHub environments definidos en archivos incluyen Development, Certification, Production y ventanas Scheduled de pipeline. El acceso remoto y sus resultados actuales se registran por corte; no se infieren del YAML.

## H3REQ1 — Auth y Pages en Development

Esta es la configuración remota cotejada para el ciclo 2026-10-21; los valores secretos no se registran.

| Superficie | Development/Free comprobado | Estado |
|---|---|---|
| Supabase Auth URL Configuration | Confirmación humana del 2026-10-21: `Site URL = https://desarrollo.studiamatch-aty.pages.dev/admin/auth/callback/`; se conservaron Redirect URLs legacy de Preview y `https://desarrollo.studiamatch-aty.pages.dev/admin/auth/callback/`. | Es confirmación de guardado/lectura por la persona; no relectura técnica por API. El proyecto Free se comparte con Certification. No se envió correo ni se hizo prueba funcional posterior. |
| Auth templates | Confirmación humana del 2026-10-21: se guardaron Invite User y Reset Password después de alinear sus action hrefs al callback versionado. | La fuente local especifica `{{ .RedirectTo }}` + `{{ .TokenHash }}` con tipos `invite` y `recovery`; no se releyó el HTML remoto por API. `admin-invite` pasa `redirectTo` explícito; el reset manual desde Dashboard depende del fallback Site URL. Guardado humano no equivale a prueba de correo/callback/MFA. No se alteraron SMTP, proveedores ni factores. |
| Edge `admin-invite` y esquema Free | `admin-invite` ACTIVE v20, `verify_jwt=true`, fuente remota igual byte a byte al merge; Free `ACTIVE_HEALTHY`, 80 migraciones, última `20261010_h3_admin_members_service_select` (`20261014144922`). | Los cuatro nombres `ADMIN_INVITE_*` se confirmaron guardados, no sus valores; OPTIONS desde Development devuelve HTTP 200 con CORS exacto. `send-lead-emails` ACTIVE v27 retorna 410 `Gone`; no hay caller local, y la UI de solicitudes está cerrada. No se redepliega sin caller/defecto demostrado. |
| Pages `studiamatch` | `NEXT_PUBLIC_SUPABASE_URL` en Previews apunta a Free, confirmado de nuevo por el responsable. La lectura R19 del 2026-10-18 registró binding `ADMIN_QUOTA`, tres HMAC `secret_text`, host allowlist/URL Free; después se confirmó `ADMIN_RPC_GATEWAY_KEY_ID` Text. | No se releyeron valores ni settings tras el merge; no hay indicio de drift. Preview es global y compartido con Certification. No se leyó configuración Production. API/docs MCP fallaron con error interno; la evidencia anterior se conserva sin repetir inventario. |
| Worker/DO de cuota y verificador PWI | R19 registró Worker `studiamatch-admin-quota` v2 y namespace `AdminQuotaCounter`; su excepción temporal expira 2026-10-25 23:59 UTC. En el log PWI compartido aparece la versión de script `69413b0e-a058-48c0-9668-5209288c35e7`. | GitHub Advanced muestra dos `check_suite.requested` y un `ping` en los últimos 3 días, sin una fila `pull_request`; las dos primeras entregas respondieron HTTP 202 `ignored`, como espera el Worker. Un reporte anterior de `pull_request/synchronize` HTTP 200 queda sin corroborar y no coincide con el contrato actual de aceptación `202 queued`/`already_queued`. La única ruleset activa encontrada solo exige la regla `update`; tiene un bypass actor configurado, no usado ni modificado. La regla clásica de `desarrollo` exige solo `security-audit` con cualquier fuente y require up-to-date; el check PWI no figura entre requisitos. No hay evidencia de check PWI confiable emitido. |
| Deployment | `09cf72f3-3b39-4385-892b-b59d995ba390`, rama `desarrollo`, merge SHA, alias `https://desarrollo.studiamatch-aty.pages.dev`, Success (confirmación humana de pantalla). Cinco rutas públicas/administrativas responden HTTP 200 `text/html`. | Smoke GET únicamente; no prueba callback, sesión o MFA. Es Development Preview; no se tocó Production. |

### Transición por ambiente

1. **Expand:** agregar el callback exacto del ambiente nuevo y conservar redirects aún usados por Certification/Preview.
2. **Compatibilidad:** mantener el callback BFF `/admin/auth/callback/`, hacer que cada caller Auth de producto envíe `redirectTo` explícito y alinear Invite User/Reset Password con los href versionados basados en `{{ .RedirectTo }}` + `{{ .TokenHash }}`. Si el reset manual de Dashboard omite `redirectTo`, el fallback Site URL debe apuntar al callback exacto Development, no a la raíz. La persona confirmó haber guardado Site URL y ambas plantillas; ese reporte no fue releído por API y aún no se valida funcionalmente. No se enviaron correos en esta configuración.
3. **Deploy:** promover únicamente mediante el flujo protegido hacia el ambiente objetivo y cotejar el SHA/alias antes de probar Auth. Production permanece fuera de este ciclo.
4. **Contract:** retirar el redirect antiguo solo al demostrar que no hay enlaces ni callers vivos y con autorización separada.
5. **Rollback:** si una prueba autorizada demuestra incompatibilidad, restaurar exclusivamente el Site URL y action hrefs previos que se hayan cambiado, desde el registro privado acotado tomado antes de guardar; conservar Redirect URLs. No revertir MFA ni ampliar hosts.

Para la migración posterior a Production, repetir la secuencia con el origen y callback exactos de Pro/host productivo, sus propios nombres/valores de secretos y los bindings de Production; no copiar valores de Free ni cambiar Production en este ciclo. Referencias: [Supabase Email Templates](https://supabase.com/docs/guides/auth/auth-email-templates), [Supabase Redirect URLs](https://supabase.com/docs/guides/auth/redirect-urls), [Cloudflare Pages environment variables](https://developers.cloudflare.com/pages/configuration/build-configuration/) y [Pages bindings](https://developers.cloudflare.com/pages/functions/bindings/).

## Inventario remoto histórico de preparación R15

El 2026-10-13 se consultó de forma read-only GitHub, Supabase y Cloudflare. El proyecto Supabase Free declarado para Development está INACTIVE y su metadata de ledger/tablas agotó timeout; Pro responde ACTIVE_HEALTHY pero el ledger/object inventory no coincide con las 28 migrations H3 locales. Cloudflare Pages mostró producción en `main`/SHA `70d0f4fe…` y un preview `desarrollo`/SHA `4eb4…`, ambos anteriores al WIP R14. El preview y producción no muestran todos los bindings BFF requeridos y el Worker/DO esperado no aparece. La variable `NEXT_SUPABASE_SECRET_KEY` figura de tipo `plain_text`; ningún valor se leyó.

El proyecto Pages enumeró `studiamatch-aty.pages.dev`, `admin.studiamatch.com` y `www.studiamatch.com`; no enumeró el apex `studiamatch.com` ni `studiamatch.pages.dev`. Es un resultado del proyecto observado, no un resultado DNS global. La guía local y los límites por proveedor, respuestas de API y decisiones requeridas están en [evidencia R15](evidencia/h3req1_g10_remote_preparation_2026-10-13_r15.md) y [paquete de integración](evidencia/h3req1_development_integration_package_2026-10-13_r15.md). La recuperación de Free, los cambios de bindings, Auth, DNS, Edge y deploy requieren instrucciones separadas.

Free/Pro no comparten datos operativos como flujo normal. Institutions/profiles/categories y definiciones editoriales se gestionan con migrations versionadas; staging_raw, cleansed_programs, enriched_programs y courses son operativos por ambiente. Un backfill o sync entre ambientes requiere alcance, aprobación y mapping de IDs separado.

## Docker Desktop / WSL

docker-compose.yml define studiamatch-dev y node-deps, usa imagen Debian Node 20/Python 3.11, mount del checkout a /app, named volume para web/node_modules, tmpfs para web/.next y port mapping configurado 3000:3000. El compose también monta .env.local como env_file; no leer sus valores. La salida read-only de docker ps en esta sesión mostró studiamatch-dev sano y publicado en 127.0.0.1:3000, sin alterar contenedor ni volúmenes. Esa observación no sustituye configuración YAML ni acredita otros servicios.

Dockerfile instala Chromium y lock Python con hashes. init-container.sh prepara dependencias, no es restauración DB. El contenedor activo compartido y sus volúmenes/imagenes se preservan; esta guía no propone stop, prune o limpieza.

## Pipeline y mantenimiento

Los workflows tienen schedules YAML: FG1 el primer día de mes UTC, FG2 diariamente UTC y FG3 diariamente UTC. La existencia del cron no acredita que esté instalado/activo ni que una corrida haya ocurrido. Control preflight mira AUTOMATION_ENABLED y PRODUCTION_WRITERS_PAUSED; el write job solo continúa si allow_writer es true.

Los scripts/core principales pueden leer y mutar datos de pipeline. scripts/maintenance contiene reportes read-only junto con writers, deletes, backfills, migraciones y cruces de ambiente; clasificar por cuerpo/callgraph antes de ejecutar. Ejemplos excepcionales detectados incluyen db_migrate.py, migrate_data_to_pro.py, migrate_rpcs_to_pro.py, sync_pro_to_free.py, batch_enrich_courses.py, preventive_cleanup.py, apply_noise_exclusions.py, force_harvest_up.py, seed_*.py y syncs específicos PUCP. No se ejecutaron.

## Build, recovery y observabilidad

Static export requiere rebuild para reflejar cambios en detalle. El build script borra .next/* y out antes de construir, por lo que no se ejecutó. La evidencia de build local debe incluir ruta/artefacto/hash e inputs; no confundir con publicación Pages. La lectura R15 encontró deployments del proyecto Pages y registra sus SHA/hosts en su reporte; no leyó DNS fuera de ese proyecto y no vio el WIP R14 desplegado. El mecanismo completo de publicación y los hosts autorizados siguen pendientes de decisión/confirmación. Rollback/pausa de pipeline, DB backups/PITR, apply migrations y recuperación de cuentas son procedimientos separados sujetos a autoridad/JIT. Logs, alertas, schedules efectivos, backups y caché no se consultaron.

## Fuentes

AGENTS.md, Dockerfile, docker-compose.yml, init-container.sh, workers/admin-quota/wrangler.jsonc, web/next.config.js, .github/workflows/{fg1_inventory,production_pipeline,fg3_integrity,production_canary,db-sync-to-pro}.yml, scripts/core, scripts/maintenance y .context/estado_del_proyecto.md.

## Navegación relacionada

[Infraestructura](componentes/infra_release.md) · [Pipeline](componentes/pipeline.md) · [Database](database.md) · [Backend](backend.md) · [Seguridad](seguridad.md) · [CI/CD](ci_cd.md) · [Hitos](hitos/README.md) · [Decisiones](decisiones/README.md) · [Estado operativo](estado_del_proyecto.md) · [Índice](indice.md)

Registro por fuente: [canarios](trazabilidad/registro_fuentes_componentes.md#canarios) · [herramientas de mantenimiento](trazabilidad/registro_fuentes_componentes.md#mantenimiento).
