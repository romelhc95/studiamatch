# Operación local y ambientes

> Esta guía describe nombres/configuración, no almacena credenciales. No abrir .env operativo para completar la documentación.

## Ambientes y datos

La guía ejecutable declara Supabase Free como Development/Certification y Pro como Production; Pro es baseline autoritativo de schema. Los scripts/cliente usan variables NEXT_PUBLIC_SUPABASE_URL, SUPABASE_URL, NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY, NEXT_SUPABASE_PUBLISHABLE_KEY y, solo para writers autorizados/CI, NEXT_SUPABASE_SECRET_KEY. Cloudflare AI consume CF_ACCOUNT_ID/CF_API_TOKEN; el código de enrichment actual también lee OPENCODE_API_KEY.

Pages Functions/Admin bindings requieren SUPABASE_URL o NEXT_PUBLIC_SUPABASE_URL, NEXT_SUPABASE_PUBLISHABLE_KEY, ADMIN_ALLOWED_HOSTS, ADMIN_QUOTA, ADMIN_QUOTA_HMAC_KEY, ADMIN_RPC_GATEWAY_HMAC_KEY y ADMIN_RPC_GATEWAY_KEY_ID; la autenticidad de sesión usa ADMIN_SESSION_ACTIVITY_HMAC_KEY. Las dos HMAC keys principales son distintas. Edge invitation usa nombres ADMIN_INVITE_ALLOWED_ORIGINS, ADMIN_INVITE_ALLOWED_REDIRECTS, ADMIN_INVITE_REDIRECT_URL, ADMIN_INVITE_RECOVERY_REDIRECT_URL, ADMIN_INVITE_RESEND_COOLDOWN_SECONDS y ADMIN_INVITE_SAFE_SUSPEND. No se registran valores.

GitHub environments definidos en archivos incluyen Development, Certification, Production y ventanas Scheduled de pipeline. El acceso remoto y sus resultados actuales se registran por corte; no se infieren del YAML.

## Inventario remoto de preparación R15

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
