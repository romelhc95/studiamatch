# Preparación remota de H3REQ1 — R15

> Corte de lecturas: 2026-10-13 18:30:52 UTC. Evidencia de preparación solamente. No acredita GO Development, aceptación D01–D14, adopción de todo el WIP R14 ni autorización de cambios remotos.

## Alcance, método y clasificación

Se ejecutaron lecturas acotadas en GitHub, Supabase y Cloudflare, más la consulta de procedencia pública de `braces`. Las consultas fueron GET/listado o SELECT de metadata; no se consultaron filas operativas ni identidades, no se leyeron valores de secretos, y no se invocaron RPC de negocio. No se ejecutaron workflows, pruebas remotas, deploys, cambios de configuración, SQL mutador, PR, merge ni escritores.

Esta nota clasifica resultados como **hecho verificado** (la consulta respondió dentro del alcance), **discrepancia** (el dato observado no coincide con el candidato/contrato local), **pendiente de acceso** (la consulta falló o no tuvo permisos), y **desconocido** (la fuente consultada no permite concluir). “Verificado” no significa que una configuración sea segura o que el producto esté adoptado.

## GitHub

Fuente: GitHub REST/API de solo lectura para `romelhc95/studiamatch`; listing de branches, commits, compare, rulesets, workflows, runs y check-runs. No se descargaron logs.

| Área | Hecho observado | Estado y límite |
|---|---|---|
| Rama predeterminada | `main`, HEAD `70d0f4fee885be0f6780e5d14f466b2a6c897961`; marcada protegida. | Verificado para metadata de branch. |
| `desarrollo` | HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`, igual al baseline del checkout candidato; compare reportó 0 commits ahead/behind. | Verificado. Esto compara el commit base: el WIP R14 no está contenido en ese SHA por el solo hecho de coincidir. |
| Protecciones y rulesets | `desarrollo` aparece protegida. El ruleset activo `owner-only-protected-branch-updates` apunta a `desarrollo`, `certificacion` y `main`, con regla `update` y bypass de owner en modo `always`. | El endpoint de branch protection devolvió 403 `Resource not accessible by integration`. No se pudieron confirmar approvals, required checks, dismissal ni reglas clásicas. El ruleset visible no prueba esos controles. |
| Workflows | `desarrollo` y `main` listan siete workflows: `db-sync-to-pro`, `fg1_inventory`, `fg3_integrity`, `opencode`, `production_canary`, `production_pipeline` y `security-audit`. El workflow candidato `protected-workflow-integrity.yml` no aparece en esas listas remotas. | Verificado contra los nombres listados; no se ejecutó ni cambió workflow. La existencia local de Stage 2 no acredita instalación remota. |
| Checks de `desarrollo` | Para SHA `4eb4…`: 15 check-runs, 14 success y `H2 Main Production Expand Gate` skipped. La API clásica de status devolvió `pending` con cero statuses clásicos. | Son superficies distintas de GitHub; se conserva el `pending` clásico como dato, sin reinterpretarlo como fallo ni como aprobación. |
| Runs relevantes | `Security Audit Gate` en `desarrollo` #1094 y CodeQL dynamic #216: success, 2026-09-27. En `main`, CodeQL schedule: success 2026-10-08; `security-audit` #1058: success 2026-08-28. Los últimos runs de schedule visibles de FG2 #249 y FG3 #117 fueron success el 2026-08-25. | Son ejecuciones históricas de sus SHA; no son CI del WIP R14 ni aceptación remota H3REQ1. No se infiere actividad de FG1 a partir de la página consultada. |

## Supabase

Fuente: metadata de proyectos, listado de migrations/tablas/Edge Functions y consultas `SELECT` a `information_schema`/`pg_proc`. No se consultaron filas de negocio, `auth.users`, invitaciones, buzones, tokens ni datos personales.

### Pro (`xwhtiqmboljkshrtviyw`)

- `ACTIVE_HEALTHY`, PostgreSQL `17.6.1.111`, región `us-east-1`.
- El ledger remoto devolvió 23 migrations, desde `20260525030610` hasta `20260607221002` (`20260607_fix_utp_postgrado_patterns`). Ninguno de los 28 nombres H3 del candidato local (archivos entre 20260828 y 20261010) aparece en esa lista.
- El listado de metadata contó 19 relaciones públicas en `information_schema`; la API de tablas enumeró 18. La diferencia entre superficies se conserva, no se fuerza a un total único.
- En el alcance consultado no aparecieron las tablas esperadas `admin_invitations`, `admin_members` ni `admin_membership_audit`; la consulta de funciones públicas `admin_%` devolvió cero filas. Sí aparecen objetos editoriales como `course_editorial_state`, `course_editorial_audit` y `courses_public_effective`.
- Edge Functions: `send-lead-emails` ACTIVE v8; `admin-invite` no apareció.
- La lectura no demuestra por sí sola que las migraciones estén o no estén parcialmente reflejadas en otro contrato/objeto; sí demuestra que el ledger y los objetos enumerados no coinciden con el paquete local descrito arriba.

**Discrepancia bloqueante:** Pro es el baseline de schema según `AGENTS.md`, pero su ledger visible no contiene el conjunto H3 local ni las tablas/RPC de membresía/invitación esperadas. No ejecutar sync, DDL ni intentar “repararlo” desde esta sesión. Antes de cualquier decisión SQL, reconciliar metadata por objeto/migration y confirmar el ref/fuente de verdad con el responsable.

### Free (`aqrldlmlszjtgpqiegaa`)

- Estado `INACTIVE`, PostgreSQL `17.6.1.111`, región `us-west-2`.
- `list_migrations` y `list_tables` terminaron con timeout de conexión. No se obtuvo un schema ni ledger legible; esto **no** demuestra ausencia de tablas/migrations.
- Edge Functions listadas: `admin-invite` ACTIVE v12 y `send-lead-emails` ACTIVE v21. El estado `INACTIVE` del proyecto impide afirmar disponibilidad o funcionamiento end-to-end.
- `GET /auth/v1/settings` no autenticado devolvió 401 para Pro; la URL Free no respondió por `URLError`. No se obtuvo configuración Auth no secreta de redirects, templates o políticas.

**Discrepancia bloqueante:** el ambiente declarado para Development no está disponible en el corte consultado; hace falta una decisión humana sobre si se reactiva Free o se designa otro ambiente. Reanudarlo o cambiar la configuración está fuera de esta autorización.

## Cloudflare Pages, Worker y Durable Object

Fuente: inventario GET del account/proyecto Pages `studiamatch`, deployments, dominios, variables/bindings por nombre y tipo, Worker scripts y namespaces Durable Object. La consulta filtró los valores; ningún valor de binding/secret fue leído o registrado.

- El proyecto Pages usa `main` como production branch. El deployment de producción más reciente observado fue success el 2026-08-28, SHA `70d0f4fee885be0f6780e5d14f466b2a6c897961`, sin Pages Functions.
- El preview más reciente de `desarrollo` observado fue success el 2026-09-27, SHA `4eb4d877a50b012bb630a129bd0c74482c33be9c`, con Pages Functions. El proyecto marca además como último deployment un preview ad hoc de `feat/h3req1-development-remote-tests`, sin SHA asociado. Ninguno corresponde al WIP completo R14.
- En el proyecto observado aparecen `studiamatch-aty.pages.dev`, `admin.studiamatch.com` y `www.studiamatch.com`; los dos dominios custom enumerados figuran activos. El apex `studiamatch.com` y `studiamatch.pages.dev` no aparecen en este proyecto. No se consultó DNS de otras zonas/proyectos, por lo que no se concluye que esos hosts no estén encaminados por otra infraestructura.
- El preview contiene `ADMIN_ALLOWED_HOSTS`; producción no lo muestra. No se observaron `ADMIN_QUOTA`, `ADMIN_QUOTA_HMAC_KEY`, `ADMIN_RPC_GATEWAY_HMAC_KEY` ni `ADMIN_RPC_GATEWAY_KEY_ID` en bindings Pages. El candidato local requiere esos nombres y el service binding privado `ADMIN_QUOTA`.
- `NEXT_SUPABASE_SECRET_KEY` aparece como binding `plain_text` en metadatos tanto de preview como de producción. **No se leyó su valor**, por lo que no se afirma que el valor sea una credencial válida o expuesta. Su tipo sí contradice el contrato de seguridad del candidato, que requiere un secreto server-side protegido.
- La lista de Workers y namespaces Durable Object consultada estaba vacía. El Worker local `studiamatch-admin-quota` y su DO `AdminQuotaCounter` no aparecen en el inventario. La lectura de settings para el Worker esperado devolvió que no existe.

**Discrepancia bloqueante:** faltan en la configuración observada bindings BFF/Worker/DO que exige el código local y la clasificación de `NEXT_SUPABASE_SECRET_KEY` no es aceptable como evidencia de un secret correctamente provisionado. No corregir la configuración ni volver a leer valores en esta sesión.

## Procedencia pública de `braces`

Fuentes públicas: [PR upstream #72](https://github.com/micromatch/braces/pull/72), [commit fuente `28d440b`](https://github.com/FSDevelop/braces/tree/28d440b5dd449dbf1fe6f3506cf94ecca4d02660) y [metadata npm de `braces`](https://registry.npmjs.org/braces/latest).

- El PR #72 está cerrado y no merged. El paquete npm oficial consultado declara `3.0.3`; no se encontró release oficial `3.0.4` ni release en el repositorio.
- El tarball local `web/vendor/braces-3.0.4-h3.1.tgz` tiene SHA-256 `a8c0b0223dc788781252f9b056207b5b053b8dd0896da861c305769b472f0819`.
- Una comparación de árbol entre el snapshot local y el commit público coincidió byte/blob en 9 de 10 archivos; `package.json` difiere solamente en el identificador de versión local `3.0.4-h3.1` frente a `3.0.3`. Esto verifica procedencia del snapshot, no la existencia de una publicación oficial ni el resultado de la suite upstream en StudIAMatch.
- El candidato R14 conserva tarball y lock sin modificación. Decisión para este corte: mantenerlos intactos, describirlos como snapshot local derivado de un PR no merged y no presentarlos como release oficial.
- El manifiesto R14 asigna a Romel el seguimiento del paquete con revisión prevista `2026-11-03`; R15 conserva esa asignación/fecha y no abre un waiver ni declara adopción.

## Comparación y decisiones necesarias

| Tema | Candidato local R14 | Lectura remota | Decisión requerida antes de integración |
|---|---|---|---|
| Base Git | WIP empaquetado sobre baseline `4eb4…` | `desarrollo` está en `4eb4…`; el WIP no está publicado. | Aprobación separada para push/PR; leer protección completa con acceso autorizado antes de tratar checks como obligatorios. |
| Development DB | Free declarado como Development; Pro define el baseline de schema. | Free INACTIVE/metadata timeout; Pro no refleja el ledger/objetos H3 locales enumerados. | Confirmar ambiente target y reconciliar migrations/objetos; cualquier apply es DDL/DML con JIT nuevo. No escribir Pro como parte de Development. |
| Admin runtime | Pages BFF + service binding + HMACs + Worker/DO, Edge invite | Preview/production sin bindings requeridos observados; Worker/DO ausentes; Edge Free v12 pero proyecto INACTIVE; Pro no lista invite. | Resolver bindings, secreto y versión Edge con owners; configuración/deploy requieren autorización distinta. |
| Protección Git | Candidate Stage 1/Stage 2 locales | Ruleset update visible; rama protegida; lectura de branch protection 403; PWI no listado en workflows remotos. | Owner debe proporcionar acceso/lectura sanitizada y decidir si PWI se instala antes del PR. No cambiar reglas ahora. |
| Hosts | Guía local declara hosts de preview/prod | Proyecto Pages enumera otros hosts; no se comprobó DNS fuera de ese proyecto. | Confirmar hostname Development autorizado y sus redirects/Access antes de prueba. |
| `braces` | Snapshot local fijado, no oficial | PR origen cerrado/unmerged; npm latest 3.0.3; snapshot corresponde al commit público salvo versión. | Mantener pin local para este paquete; cambiarlo requiere decisión, lock nuevo y validación renovada. |

## Preservación y fuentes

El checkout original `/home/romel/src/studiamatch` se mantuvo de solo lectura. El backup previo a las lecturas remotas está en `/home/romel/backups/studiamatch-docs-2026-10-13/supplemental_before_r15_remote-preparation_2026-10-13` (19/19 hashes); la copia previa a las notas de los dos módulos está en `supplemental_before_r15_component_remote_notes_2026-10-13` (2/2). Para preservar el estado documental R15 antes de esta última reconciliación se creó `/home/romel/backups/studiamatch-docs-2026-10-13/supplemental_before_r15_final_reconcile_2026-10-13` (19/19 hashes); contiene el estado previo a las correcciones finales, no una copia anterior a R15. Los tres backups están fuera de ambos checkouts y excluidos del paquete propuesto.

Fuentes locales contrastadas: `AGENTS.md`; `.context/estado_del_proyecto.md`; R14 en `evidencia/h3req1_reconciliacion_local_2026-10-13_r14.md`, su manifiesto y checks; `db/migrations/` (28 migrations locales H3); `web/functions/_middleware.ts`, `web/functions/_lib/admin-bff.ts`, `web/functions/_lib/admin-quota.ts`, `workers/admin-quota/wrangler.jsonc`, `supabase/config.toml`, `supabase/functions/admin-invite/index.ts`, `web/vendor/README.md`, `web/package.json` y `web/package-lock.json`. Las lecturas GitHub/Supabase/Cloudflare están acotadas al timestamp de esta nota; no se exportaron respuestas crudas.

## Lo que sigue sin probar

- No se verificó adopción del WIP R14, CI de ese WIP, deploy nuevo, disponibilidad funcional de Free, Auth/email real, bindings secretos, DNS global, triggers externos ni caller remoto de `send-lead-emails`.
- No se leyó protección de branch completa por respuesta 403; required checks y approvals siguen desconocidos.
- No se consultaron filas operativas ni valores secretos. No hubo SQL operativo ni pruebas D01–D14.
- Las discrepancias son bloqueos de preparación. Este informe no cambia estado de la aplicación ni crea permisos.

## Navegación

[Estado operativo](../estado_del_proyecto.md) · [Paquete Development/transición/rollback](h3req1_development_integration_package_2026-10-13_r15.md) · [Checks R15](h3req1_remote_preparation_checks_2026-10-13_r15.txt) · [Revisión independiente R15](h3req1_remote_preparation_independent_review_2026-10-13_r15.txt) · [Manifest overlay R15](h3req1_remote_preparation_manifest_2026-10-13_r15.json) · [Borrador de cuerpo de integración](h3req1_pr_body_draft_local_review_2026-10-13_r15_remote_prep.md) · [CI/CD](../ci_cd.md) · [Database](../database.md) · [Backend](../backend.md) · [Seguridad](../seguridad.md) · [Operación](../operacion.md) · [Índice](../indice.md)
