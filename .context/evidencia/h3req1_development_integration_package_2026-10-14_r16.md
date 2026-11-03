# Paquete de integración Development — H3REQ1 R16

> Paquete local de preparación. Estado: **NO-GO Development**. No se ejecuta D01–D14 ni se concede permiso remoto. Se apoya en R14 (candidato) y R15/R16 (overlays documentales); no incorpora automáticamente el WIP restante.

## Candidato y alcance

El candidato funcional/documental base es el snapshot R14: alcance funcional R8 combinado con cierre documental R13, sobre baseline `4eb4d877a50b012bb630a129bd0c74482c33be9c`. R8/R9/R12/R13 y su evidencia quedan preservados. R15 conserva la primera preparación remota. R16 añade hechos de lectura remota y una secuencia de integración condicionada; ninguno añade código funcional ni despliegue.

Para una eventual integración se requiere el alcance fijado en el [manifiesto R14](h3req1_pr_scope_manifest_2026-10-13_r14_reconciled.json) y el overlay documental R15/R16. La comprobación de referencias encontró que el estado vigente enlaza `.context/evidencia/h3req1_g10_scope_scan_r181_2026-10-12.txt`, evidencia requerida por R14 pero ausente de su manifest; R16 añade únicamente ese log para cerrar la referencia. Se excluyen los demás paths WIP, backups externos, archivos de entorno, outputs/caches generados, artefactos remotos crudos y documentación privada del cliente. El overlay R15 tuvo 17/20 paths aceptados. Con el log referenciado, el overlay R16 tiene 7/11 rutas aceptadas; el log, checks, revisión y manifest no tienen cobertura. R16 no amplía workflows/allowlists y no queda listo para filing hasta cerrar esa discrepancia mediante autorización y validación local.

## Hechos, discrepancias y desconocidos

Los [resultados R16](h3req1_g10_remote_preparation_2026-10-14_r16.md) son la fuente de detalle. Hechos acotados: `desarrollo` apunta al baseline; Pro lista 23 migrations sin nombres H3 locales; Free está inactivo y metadata devuelve `INVALID_ARGUMENT`; Auth no respondió a lectura no autenticada; dos dominios Pages aparecen activos y Workers/DO no se listan; `braces` local deriva de un PR no merged. Branch protection completa, Auth settings, Cloudflare deployments/bindings, DNS y aceptación siguen sin verificar.

Los deployments/bindings Cloudflare citados por R15 son históricos: R16 omitió endpoints cuyas respuestas incluyen valores. La ausencia de una lectura segura no se interpreta como ausencia de configuración actual. El riesgo histórico de `NEXT_SUPABASE_SECRET_KEY` tipo `plain_text` permanece pendiente de aclaración sin exponer su contenido.

## Gates de entrada — decisiones concretas

| Gate | Decisión/evidencia necesaria | Owner sugerido | Autoridad que seguirá separada |
|---|---|---|---|
| E0 — ambiente | Confirmar si Free será restaurado como Development o designar otro ref aislado. Repetir metadata de forma legible cuando esté disponible. | Responsable Supabase/Release | Reactivar/cambiar proyecto, DNS o settings. |
| E1 — schema | Entregar ledger, columnas/tipos, constraints, índices, funciones, grants, vistas, RLS y triggers de Pro/target; resolver la discrepancia 18 tablas vs 19 relaciones históricas; aprobar lista forward exacta contra baseline Pro. | Responsable DB | Cualquier SQL, DDL/DML, RPC mutadora, apply o rollback. |
| E2 — runtime/secretos | Proporcionar inventario seguro de nombres/tipos de bindings Pages, service binding, Worker/DO, Edge y host allowlist; aclarar el `plain_text` histórico mediante secret store sin leer/exportar valores. | Responsable Cloudflare/Supabase | Cambiar bindings/secrets, rotar, desplegar Pages/Worker/DO/Edge. |
| E3 — Git | Aportar branch protection, required checks, approvals, bypass, environments y decisión sobre `protected-workflow-integrity.yml`. | Admin GitHub | Cambiar reglas, push, PR, workflow_dispatch, merge. |
| E4 — Auth/hosts | Aportar settings Auth no secretos, callback/redirects, `verify_jwt`, templates y hostname Development/Access autorizado. | Responsable Supabase/Security | Cambiar Auth/DNS/Access, enviar correo o probar cuentas reales. |
| E5 — dependencia | Confirmar que se mantiene el snapshot local o instruir un ciclo separado de sustitución oficial tras verificar disponibilidad/equivalencia. | Responsable de dependencias | Cambiar tarball/lock e instalar; se requiere validación por impacto. |

No se resuelve ningún gate por inferencia, éxito de un run antiguo o referencia histórica. Si una evidencia falta, se detiene la fase dependiente.

## Secuencia futura ejecutable (condicionada a permisos)

| Fase | Acciones concretas | Gate de salida / evidencia |
|---|---|---|
| 0. Congelar paquete | Recalcular merge-base/diff; cotejar paths y hashes R14 más overlays autorizados; excluir todo WIP restante; reconciliar el consumidor del manifest (hoy la regresión fija R14 y falla al leer el path actualizado R15 `admin_runtime.md`), cobertura del path guard (R15 17/20; R16 7/11) y cuerpo PR con plantilla; revisión local independiente. | Manifest reconciliado; cero rutas fuera del alcance aprobado; regresión de scope consume el overlay acordado; checks locales ejecutados contra inputs actuales. |
| 1. Integración Git | Solo tras autorización expresa, publicar rama y abrir PR a `desarrollo`; esperar branch protection/review/required checks sobre SHA exacto. | SHA/manifest coinciden; gates efectivos y aprobaciones satisfechos. No promover a Certification. |
| 2. `expand` DB | Elegir Development; comparar target con baseline Pro y fixture PG17; determinar migrations forward exactas; mantener lecturas legacy. Aplicar solo con JIT SQL por ref/hash/orden. | Ledger y diff metadata coinciden con plan aprobado; DB gate/harness compatible; evidencia before/after; sin sincronizar filas operativas. |
| 3. `compatibilidad` | Provisionar Pages Functions/BFF, Edge, service binding y Worker/DO; configurar nombres requeridos, host allowlist y secretos por proceso seguro. Mantener contratos/fallbacks legacy necesarios. | Versiones/SHA, presencia de bindings por nombre/tipo, `verify_jwt`, HMAC keys distintas y cuota privada confirmados sin exportar valores; fallos cerrados si falta binding. |
| 4. `deploy` Development | Desplegar SHA autorizado en hostname confirmado y orden compatible; comprobar cache/headers/rutas públicas/Admin, safe-suspend y logs sanitizados. | Deployment exacto identificado; smoke sin efectos; versión previa y recuperación listas. Deploy requiere permiso distinto. |
| 5. Aceptación D01–D14 | Ejecutar matriz canónica del plan H3-CLOSE solo con autorización por actor/cuenta/buzón/efecto y evidencia sanitizada. | Cada caso PASS o skip justificado con owner/riesgo; sin HIGH/CRITICAL, regresión ni degradación. Actualmente 0/14. |
| 6. GO Development | Revisión de evidencia, seis pilares, CI efectivo, estabilidad, rollback y aprobación humana explícita. | GO solo en estado tras aceptación; este documento no lo otorga. |
| 7. `contract` | Después de estabilidad y autorización nueva, retirar compatibilidad legacy por consumidor. | No quedan consumidores requeridos; tests por impacto, grants/bypass y rollback revisados. Certificación/Producción son etapas aparte. |

La secuencia funcional de aceptación sigue la matriz D01–D14 del [plan H3-CLOSE](../operaciones/plan_cierre_integral_h3req1_2026-10-04.md#h3-close-08--matriz-de-aceptación-remota-y-go-development-real). D01–D02 cubren sesión/MFA; D03 invitación/onboarding/correo; D04–D05 membresías/permisos/último Admin; D06 cola/facetas; D07–D10 edición/publicación/auditoría/disponibilidad; D11 ruta pública post-build/deploy; D12 firma/cuota/replay; D13 hosts/perímetro/cache; D14 recuperación. Este paquete no ejecuta esos casos.

## `expand -> compatibilidad -> deploy -> contract`

- **`expand`:** solo migrations aditivas aprobadas para Development, preservando columnas/lecturas legacy. No aplicar en Pro como solución a Free. No transportar datos operativos.
- **`compatibilidad`:** nuevas rutas BFF/Auth/RPC/Edge funcionan junto a los lectores legacy imprescindibles. El browser no recibe secretos; API keys quedan en `apikey`; sesión JWT solo en las rutas autorizadas del contrato.
- **`deploy`:** promoción del SHA aprobado con bindings y host verificados. La verificación de configuración nunca requiere mostrar valores secretos. No declarar runtime PASS por metadata o builds locales.
- **`contract`:** se difiere hasta estabilidad y nueva autorización; retirar solo rutas/grants/flags probados sin consumidores requeridos.
- **No degradación:** conservar acceso público/cookies y contratos legacy durante expansión; validar los 6 pilares y acceptance remota antes de contraer.

## Rollback y recuperación

El rollback remoto no se ha probado. No borrar datos, auditoría, keys/nonces ni aplicar `DROP` como respuesta automática.

1. **Antes de expand:** detener promoción y mantener el ambiente/version actual. No reactivar Free ni alterar rutas desde este paquete.
2. **Después de expand, antes de runtime:** detener despliegue/writers; dejar cambios aditivos compatibles; comparar ledger/schema y pedir JIT DB para recuperación. No ejecutar rollback SQL improvisado.
3. **Después de deploy, antes de contract:** si hay riesgo, activar safe-suspend solo con autorización y control preparado; frenar invitaciones/mutaciones, preservar lecturas públicas, restaurar Pages/Edge/Worker al último SHA/version compatible y verificar rutas, sesión, errores y auditoría. Mantener schema expandido.
4. **Fallo de gateway/pre-request:** seguir el orden de safe-suspend y rollback BFF; restaurar configuración previa solo con aprobación DB/infra. Conservar guard `p_first = NULL`, keys/nonces y auditoría.
5. **Daño o efectos:** detener writers y escalar a owners DB/Security. Backup/restore, replay, cleanup y recuperación de cuentas requieren JIT con alcance, snapshot y punto de restauración.
6. **Cierre de rollback:** registrar SHA/versions, estado de bindings por nombre (sin valores), rutas públicas/Admin, ledger, errores y decisión. Repetir UAT solo con autorización nueva.

`contract` queda bloqueado durante rollback hasta nueva evidencia de estabilidad. Restore, purgas, schedules, writers y backfills no se incluyen en esta preparación.

## Permisos posteriores indispensables

- Lectura administrativa sanitizada GitHub de protección/checks; no modificar rulesets.
- Autorización local separada para alinear manifest/allowlist/regresión protegida, si el owner quiere remover el bloqueo de 17/20 y el consumidor R14 desactualizado; no editar esas protecciones dentro de esta preparación documental.
- Decisión de target y lectura metadata Supabase tras disponibilidad; JIT SQL independiente para cualquier migration o reparación.
- Inventario Cloudflare filtrado con nombres/tipos solamente; JIT separado para secretos, bindings, rutas y deploys.
- Lectura Auth no secreta y host/Access confirmado; aprobación separada para cambios y correo/cuenta real.
- Autorización específica para push/PR, merge y workflow_dispatch; una no concede las otras.
- JIT separado por D01–D14 con efectos y por rollback/restore/cleanup. No hay GO implícito.

## Fuentes del paquete

[Estado operativo](../estado_del_proyecto.md) · [Reporte R16](h3req1_g10_remote_preparation_2026-10-14_r16.md) · [Checks R16](h3req1_remote_preparation_checks_2026-10-14_r16.txt) · [Revisión independiente R16](h3req1_remote_preparation_independent_review_2026-10-14_r16.txt) · [Manifest R14](h3req1_pr_scope_manifest_2026-10-13_r14_reconciled.json) · [Overlay R15](h3req1_remote_preparation_manifest_2026-10-13_r15.json) · [Plantilla versionada del PR](../../.github/pull_request_template.md) · [Índice](../indice.md)
