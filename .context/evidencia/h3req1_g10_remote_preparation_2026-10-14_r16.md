# Preparación remota de H3REQ1 — R16

> Corte de lectura: 2026-10-14 UTC. Verificación remota de preparación, read-only. **NO-GO Development**. No acredita adopción del WIP, autorización de integración ni aceptación D01–D14.

## Alcance y método

Se verificaron únicamente superficies de metadata previamente delimitadas: ramas, rulesets, checks, workflows y runs GitHub; metadata de schema/ledger Pro y Free, Edge Functions y Auth no secreto; dominios Pages y listados de Workers/Durable Objects; procedencia pública del snapshot `braces`. Se usó el repositorio confirmado `https://github.com/romelhc95/studiamatch`.

No se consultaron filas operativas, usuarios, invitaciones, buzones, tokens o valores de secretos. No se usaron credenciales para Auth settings. No se llamaron RPC mutadoras, DDL/DML, pruebas con efectos, workflows, PR, push, merge, deploy, purgas ni endpoints de configuración. Las respuestas se anotaron sanitizadas; no se guardaron cuerpos crudos que pudieran contener valores.

Clasificación: **hecho verificado** describe solo una respuesta de lectura dentro del alcance; **discrepancia** compara esa respuesta con R14/contrato local; **pendiente** indica que el endpoint no respondió o no se leyó; **desconocido** delimita lo que una lista/metadata no prueba.

## GitHub — `romelhc95/studiamatch`

| Superficie | Hecho verificado | Discrepancia / límite |
|---|---|---|
| Ramas | Default `main` en `70d0f4fee885be0f6780e5d14f466b2a6c897961`; `desarrollo` en `4eb4d877a50b012bb630a129bd0c74482c33be9c`; `certificacion` en `c80f6504a3ea353bc2c222df1da09c4b5ba0ae58`. Las tres aparecen protegidas. El HEAD de `desarrollo` coincide con el baseline del checkout candidato. | El WIP R14 no está en esos SHA. La etiqueta `protected=true` no expone por sí sola approvals ni checks requeridos. |
| Ruleset | `owner-only-protected-branch-updates` aparece activo, regla `update`, aplicado a `desarrollo`, `certificacion` y `main`, con bypass de clase `User` en modo `always`. | No se registró identidad de actor. No equivale a la configuración de branch protection ni prueba el flujo de aprobación. |
| Branch protection | GET de detalle para `desarrollo` devolvió HTTP 403 `Resource not accessible by integration`. | Approvals, required checks, dismissals, restricciones de push y environments quedan sin verificar. No se cambió el ruleset. |
| Checks del baseline | Para SHA `4eb4…`: 15 check-runs, 14 `success` y `H2 Main Production Expand Gate` `skipped`. El endpoint clásico informa `pending` y cero statuses clásicos. | Son superficies distintas. No se interpreta el status clásico como fallo ni como aprobación; estos resultados no son CI del WIP. |
| Workflows | En `main` y `desarrollo` se listan `db-sync-to-pro.yml`, `fg1_inventory.yml`, `fg3_integrity.yml`, `opencode.yml`, `production_canary.yml`, `production_pipeline.yml` y `security-audit.yml`. `protected-workflow-integrity.yml` local no está listado. | El inventario de archivos no acredita triggers, required status ni ejecución. `security-audit.yml` difiere entre refs. |
| Runs relevantes | `Security Audit Gate` y `Push on desarrollo` en el SHA base terminaron `success` (2026-09-27). En `main`, el run Scheduled #37831724423 terminó `success` (2026-10-08); el previo #36914071310 también `success` (2026-10-01). | Son runs históricos de sus SHA, no CI del WIP ni aceptación H3REQ1. No se descargaron logs. |

## Supabase

Se consultó metadata, no filas. Pro continúa siendo el baseline de schema declarado por `AGENTS.md`; estos resultados no autorizan reparar Pro ni aplicar SQL.

### Pro — `xwhtiqmboljkshrtviyw`

- `ACTIVE_HEALTHY`, PostgreSQL `17.6.1.111`, `us-east-1`.
- Ledger visible: 23 migrations, hasta `20260607221002`; no aparecen los 28 nombres de migrations H3 locales descritos en R14.
- El listado de tablas de `public` devuelve 18 relaciones. En la metadata devuelta no aparecen `admin_invitations`, `admin_members` ni `admin_membership_audit`. La consulta de `information_schema` que en R15 había contado 19 no se repitió; la diferencia entre superficies queda sin reconciliar.
- Edge inventory: `send-lead-emails` ACTIVE v8; `admin-invite` no listado.

**Discrepancia:** ledger/objetos enumerados no coinciden con el candidato local. El inventario parcial no determina qué migrations aplicar ni demuestra ausencia en todos los schemas/superficies.

### Free — `aqrldlmlszjtgpqiegaa`

- El metadata de proyecto consultado continúa indicando `INACTIVE`, PostgreSQL `17.6.1.111`, `us-west-2`.
- `list_migrations` y `list_tables` respondieron `INVALID_ARGUMENT`; no se obtuvo ledger ni catálogo. No se concluye ausencia de schema.
- Edge inventory enumera `admin-invite` ACTIVE v12 y `send-lead-emails` ACTIVE v21, aunque el proyecto está inactivo. El listado no prueba disponibilidad ni invocation.

**Bloqueo:** Development no es un target verificable mientras Free siga `INACTIVE` y el ledger/catálogo no sean legibles. Reactivar o cambiar el target queda fuera de esta autorización.

### Auth no secreto

- GET no autenticado a `/auth/v1/settings` en Pro devolvió HTTP 401.
- La consulta equivalente a Free terminó con error de resolución DNS (`gaierror`).
- No se llamó endpoint administrativo ni se usó token. Redirects, origins, políticas y templates Auth quedan desconocidos.

## Cloudflare — superficies seguras

Se revisó el esquema de los endpoints antes de consultarlos. No se llamó a Pages project/deployments ni a Worker settings porque sus respuestas pueden contener valores de variables (incluidos `plain_text`) o contenido secreto; no había un filtro de respuesta que garantizara excluirlos. Por la misma razón, el inventario de bindings no se declara refrescado en R16.

- GET del inventario de dominios del proyecto Pages `studiamatch`: `admin.studiamatch.com` y `www.studiamatch.com` aparecen activos.
- GET de Workers del account devuelve lista vacía.
- GET de namespaces Durable Objects devuelve lista vacía.
- No se verificaron refs/SHA de deployment actuales, producción/preview, Pages Functions, bindings BFF, Worker settings, secrets, service bindings, routes ni DNS externo.

R15 reportó deployments antiguos (`main`/SHA `70d0…` y preview `desarrollo`/SHA `4eb4…`) y metadatos de bindings, incluido `NEXT_SUPABASE_SECRET_KEY` con tipo `plain_text`. Esos datos permanecen como **observaciones históricas R15** y no se repiten como estado actual. La clasificación de ese binding sigue siendo un riesgo pendiente que el owner debe aclarar sin exportar el valor.

## Procedencia pública de `braces`

Fuentes consultadas: [PR upstream #72](https://github.com/micromatch/braces/pull/72), [commit público fuente](https://github.com/FSDevelop/braces/tree/28d440b5dd449dbf1fe6f3506cf94ecca4d02660) y [versions oficiales de npm](https://www.npmjs.com/package/braces?activeTab=versions).

- El PR #72 está cerrado, no merged; el commit fuente observado es `28d440b5dd449dbf1fe6f3506cf94ecca4d02660`.
- El registro oficial consultado muestra `braces` `3.0.3` como última versión; no muestra release oficial `3.0.4`.
- El tarball local `web/vendor/braces-3.0.4-h3.1.tgz` conserva SHA-256 `a8c0b0223dc788781252f9b056207b5b053b8dd0896da861c305769b472f0819`. La comparación preservada R15 cotejó 9/10 blobs con el commit público; la única diferencia es el campo `version` de `package.json` (`3.0.3` vs `3.0.4-h3.1`). No se modificó tarball ni lock.

## Comparación con R14 y decisiones

| Área | Candidato R14 | Observación R16 | Decisión / estado |
|---|---|---|---|
| Git | WIP local sobre baseline `4eb4…`. | `desarrollo` sigue en `4eb4…`; no hay evidencia de WIP remoto. Reglas detalladas no accesibles (403). | No filing. Obtener una lectura administrativa sanitizada de protección antes de autorización futura. |
| DB | Pro es autoridad declarada; candidato incluye migrations/contratos H3 locales. | Ledger Pro no enumera H3; Free sigue inactivo y falla metadata con `INVALID_ARGUMENT`. | No SQL. Owner debe seleccionar target y aportar diff metadata completo Pro/Free/local, explicando deltas. |
| Auth / Edge | BFF, invitaciones y contrato Auth del candidato. | Pro/Free Edge inventories difieren; Auth settings inaccesibles y Free inactivo. | No prueba con cuenta/correo. Resolver target, config `verify_jwt`, redirects/templates con lectura autorizada no secreta. |
| Cloudflare | Candidato exige bindings BFF, quota, HMAC y Worker/DO. | R16 solo confirma dos dominios activos y listas Worker/DO vacías; deployments/bindings no se releen con seguridad. | No desplegar/configurar. Owner debe facilitar inventario metadata-only por un endpoint/proceso que no incluya valores. |
| `braces` | Pin local `3.0.4-h3.1`, sin ser release oficial. | Procedencia pública y diferencia de versión corroboradas. | Mantener bytes/pin. Cualquier sustitución requiere decisión explícita, versión oficial, equivalencia y ciclo de lock/validación propio. |

## Resultado y límites

- Hechos R16: rama/refs/checks/workflows/runs y ruleset listados; ledger/tables Pro y Edge inventories; estado y error de metadata Free; fallos Auth; dominios Pages; Workers/DO vacíos; procedencia pública de braces.
- Bloqueos: Free inactivo; ledger/objetos Pro discrepantes; branch protection 403; Auth no legible; Cloudflare deployments/bindings no refrescados por riesgo de exposición; falta confirmación del hostname Development.
- Desconocido: protección clásica completa, CI del WIP, estado de bindings actuales, DNS/Access externo, configuración Auth, disponibilidad funcional Edge, callers/triggers externos.
- No hubo mutaciones, lectura de datos operativos/secretos ni acciones protegidas. **D01–D14 siguen 0/14; no se declara GO Development.**

## Señal local de reconciliación del scope guard

La regresión local `tests/test_protected_path_scope_guard.sh` se ejecutó en Docker y falló antes de comparar allowlists: `referenced target hash differs: .context/componentes/admin_runtime.md`. La prueba fija como entrada el manifiesto inmutable R14, cuyo pin de esa ruta es `594a89e7…`; el overlay R15 actualiza la misma ruta a `4f38b51b…`, que coincide con el archivo actual. No se modificaron R14, workflow ni prueba para ocultar el delta. R15 ya documenta 17/20 paths aceptados por el workflow; R16 deja esta discrepancia de consumidor como bloqueo local de filing hasta una reconciliación aprobada del manifiesto/allowlist/regresión.

La comparación extrae `allowed_h3`, `allowed_h3_extra` y el heredoc `H3_LOCAL_PATHS` de `.github/workflows/security-audit.yml`; evalúa cada ruta del overlay con los mismos `re.search` y pertenencia exacta usados por la regresión. El paquete de diez archivos R16 más el manifest tiene once rutas: 7/11 aceptadas. No se aceptan `.context/evidencia/h3req1_g10_scope_scan_r181_2026-10-12.txt`, el log de checks R16, la revisión independiente R16 y el manifest R16. El cierre de referencias añadió solo el log R181 directamente citado por el estado; no incorporó el WIP restante. No se alteró el workflow ni se ejecutó CI; el overlay también queda bloqueado para filing.

La inspección de enlaces de los cinco documentos de entrada (estado, índice, reporte, paquete y cuerpo) encontró que el estado incluía una referencia directa a `h3req1_g10_scope_scan_r181_2026-10-12.txt`, ausente del paquete R14. R16 incluye ese archivo exacto como evidencia referenciada; no selecciona otros logs WIP. La validación final de disponibilidad y el conteo de enlaces quedan en [checks R16](h3req1_remote_preparation_checks_2026-10-14_r16.txt).

## Navegación

[Estado operativo](../estado_del_proyecto.md) · [Paquete Development/transición/rollback R16](h3req1_development_integration_package_2026-10-14_r16.md) · [Checks R16](h3req1_remote_preparation_checks_2026-10-14_r16.txt) · [Revisión independiente R16](h3req1_remote_preparation_independent_review_2026-10-14_r16.txt) · [Manifiesto R16](h3req1_remote_preparation_manifest_2026-10-14_r16.json) · [Plantilla del cuerpo de integración](h3req1_pr_body_draft_local_review_2026-10-14_r16.md) · [Índice](../indice.md)
