# Paquete de integración Development — H3REQ1 R15

> Preparación local ejecutable una vez resueltos los bloqueos y concedidas autorizaciones separadas. **NO-GO Development** en este corte. No se ejecutó ni se autoriza ejecutar D01–D14, PR, push, merge, deploy, SQL operativo, configuración remota, envío de correo, escritores o recuperación.

## Objetivo y autoridad

Este paquete convierte los hallazgos R15 en un orden de integración, verificación, transición y rollback. La autoridad operativa sigue siendo [Estado del proyecto](../estado_del_proyecto.md); el plan H3-CLOSE D01–D14 se conserva en [plan único de cierre](../operaciones/plan_cierre_integral_h3req1_2026-10-04.md#h3-close-08--matriz-de-aceptación-remota-y-go-development-real). Este documento no crea permisos ni cambia ese plan.

El candidato local corresponde a la rama `feat/h3req1-sync-20261002`, baseline `4eb4d877a50b012bb630a129bd0c74482c33be9c`, con WIP R14 seleccionado explícitamente por [manifiesto R14](h3req1_pr_scope_manifest_2026-10-13_r14_reconciled.json). Ese SHA también es el HEAD remoto de `desarrollo`, pero el WIP no está en el remoto. El paquete posterior se expresa como R14 más el overlay de documentación R15; el [manifiesto R15](h3req1_remote_preparation_manifest_2026-10-13_r15.json) registra únicamente el overlay y no altera el snapshot R14.

La [evidencia remota R15](h3req1_g10_remote_preparation_2026-10-13_r15.md) contiene las lecturas sanitizadas, diferencias y límites. R178 acredita pruebas locales; R181/R182 son evidencia del delta local. Ninguna de esas fuentes equivale a adopción remota.

## Gates de entrada: decisiones obligatorias

No iniciar la integración hasta que cada fila tenga dueño, evidencia y autorización apropiada.

| ID | Bloqueo/decisión | Evidencia requerida para destrabar | Permiso separado posterior |
|---|---|---|---|
| E0 | **Elegir el ambiente Development.** El proyecto Free esperado está `INACTIVE`; su metadata de schema/ledger agotó timeout. | Confirmación del responsable de que Free se restaurará y es el target, o designación de otro ref/proyecto/host con su aislamiento de datos. | Reactivar/cambiar proyecto, settings o DNS requiere instrucción remota específica. |
| E1 | **Reconciliar schema H3.** Pro es baseline declarado, pero su ledger termina en junio y no lista las 28 migrations H3 locales ni las tablas/RPC de membresía/invitación enumeradas en R15. | Inventario metadata versionado por ambiente: migrations, columnas, tipos, constraints, índices, funciones, grants, vistas, RLS y triggers; explicación del corte/diferencia y lista exacta forward-only para Development. | Cualquier DDL/DML/apply/rollback requiere JIT con ref, hashes, orden, límites y recuperación. No aplicar en Pro como atajo. |
| E2 | **Provisionar perímetro y runtime Admin.** No se observaron los bindings BFF/Worker/DO exigidos por el candidato; el Worker esperado no aparece. `NEXT_SUPABASE_SECRET_KEY` figura `plain_text`. | Inventario sin valores que confirme bindings Pages, service binding privado, Worker/DO, allowlist exacta y Edge target/version. Owner debe confirmar si el binding `plain_text` era credencial válida, placeholder o residuo; el valor no se exporta. | Cambiar/clasificar bindings, rotar credenciales o desplegar Pages/Worker/DO/Edge requiere aprobaciones Cloudflare/Supabase separadas. |
| E3 | **Confirmar controles Git.** Branch protection devolvió 403; el ruleset observado solo demuestra regla `update`. PWI no aparece en la lista de workflows remotos. | Lectura autorizada o atestación administrativa sanitizada de required checks, approvals, bypass, environments y decisión explícita de Stage 1/Stage 2/PWI. | Cambiar protección, instalar workflows, push o PR requiere instrucción separada. |
| E4 | **Confirmar Auth y host.** Settings Auth no fueron legibles; los hosts Pages observados no coinciden por completo con la guía local y no se consultó DNS externo. | Redirect/origin/template/verify-JWT y hostname Admin Development confirmados por el owner, sin tokens ni valores secretos. | Cambiar Auth, redirect, DNS/Access, enviar correo o probar cuenta real requiere autorización específica. |
| E5 | **Acordar uso del snapshot `braces`.** Procedencia pública se verificó: deriva del PR cerrado/unmerged #72, no de un release oficial. | Mantener `3.0.4-h3.1` para este paquete o autorizar una sustitución oficial tras demostrar disponibilidad/equivalencia. | Sustitución toca manifiestos/lock e instala dependencias; requiere un ciclo local separado y validación por impacto. |

No se permite rebajar un bloqueo llamándolo “warning”. Si un owner no puede acreditar una pieza, conservarla como pendiente y detener solo la secuencia dependiente; el resto de preparación local puede continuar.

## Secuencia propuesta de integración

| Fase | Trabajo cuando sea autorizado | Gate de salida | Evidencia obligatoria |
|---|---|---|---|
| 0. Congelar candidato | Recalcular diff/merge-base y scope sobre el WIP completo; reconfirmar los hashes del manifiesto R14 más overlay R15; excluir el resto de WIP y backups. | Ningún drift respecto a la selección; branch rules y CI de destino conocidos; revisión local final sin bloqueantes. | Manifest combinado nuevo sin hashes circulares, diff allowlisted, scanner y scope guard sobre los paths exactos. |
| 1. Integración Git | Solo después de instrucción: publicar la rama/candidato, abrir PR contra `desarrollo` y esperar required checks/review configurados. | SHA de PR coincide con el manifest; checks requeridos efectivos en ese SHA; gates de seguridad verdes; no se promueve a Certification. | PR/check runs/reviews referidos por SHA exacto. Esta sesión no los creó. |
| 2. `expand` Development | Con ref/ambiente confirmado, comparar Free con Pro y el fixture PG17; acordar migrations forward exactas; aplicar únicamente a Development tras JIT SQL. Conservar rutas/lectores legacy. | Migration ledger coincide con la lista aprobada; comprobación de schema y harnesses relevantes pasan; sin degradar reads antiguos. | Antes/después de metadata schema y ledger, hashes SQL, outputs PG17/DB gate y respaldo/recuperación autorizados. No sincronizar filas operativas. |
| 3. `compatibilidad` | Preparar Pages Functions/BFF, Edge `admin-invite`, Worker y DO con bindings requeridos; mantener API/RPC y fallback legacy necesario. Provisionar secretos por store seguro y validar nombres/presencia sin leerlos. | Health/config metadata, verify-JWT, host allowlist, HMAC keys distintas por proceso seguro, cuota privada y rutas internas; API falla cerrada si binding falta. | SHA/versiones exactos, diff de bindings por nombre/tipo, smoke sin efectos y evidencia de credencial no exportada. No usar `plain_text` para una credencial. |
| 4. `deploy` Development | Desplegar el SHA aprobado en hostname Development confirmado; publicar Edge/Worker/DO compatibles siguiendo el orden aprobado; no usar preview ad hoc como host contractual. | Deployment identificado por SHA/ref/host; páginas públicas y Admin con cache privado/no-store donde corresponde; error, timeout y safe-suspend verificados. | IDs/versions sanitizados, host exacto, logs sin PII/secretos, checks de deployment y rollback listo antes de UAT. |
| 5. Aceptación D01–D14 | El owner concede permisos independientes para cuenta existente, buzón designado, UAT real, casos con efectos y drill. Ejecutar sin grabar contraseña, JWT, MFA, enlaces Auth, tokens o PII. Usar el detalle de D01–D14 del plan único, sin sustituir casos por mocks. | Cada caso aplicable PASS contra SHA/host/DB/Edge/Worker identificados; fallos o skips con causa/owner; sin HIGH/CRITICAL ni pérdida de seguridad/datos. | Matriz D01–D14, trazas sanitizadas, resultado por actor/rol, auditoría, estado de datos y revisión independiente. No se ejecutan en este corte. |
| 6. Aceptar Development | Cotejar aceptación sanitizada, seis pilares, CI/protección, estabilidad y rollback integrado; decisión humana explícita de GO D. | Solo entonces el responsable puede declarar GO Development en estado. | Reporte final y pins del artefacto exacto. Un deploy `success` aislado no basta. |
| 7. `contract` | Tras estabilidad observada y permiso distinto: retirar compatibilidad legacy seleccionada, grants/bypass/flags solo con plan por consumidor. | No quedan consumidores legacy requeridos; controles, lectura pública, Admin, auditoría y rollback conservan contrato. | Migraciones/contract, pruebas por impacto y decisión explícita; Certification/Production siguen fuera. |

### Correspondencia de D01–D14

La matriz canónica completa, criterios y grupos H3 están en la sección H3-CLOSE-08 del plan enlazado arriba. D01–D02 validan sesión/MFA; D03 invitación/onboarding y correo; D04–D05 permisos/membresías/último Admin; D06 cola/facetas; D07–D10 edición/publicación/auditoría/disponibilidad; D11 ruta pública tras build/deploy; D12 cuotas, firma, replay y rechazo; D13 perímetro/hosts/Access/cache; D14 drill/recuperación. Las pruebas de correo, cuotas, DB, cuentas y drill pueden producir efectos y requieren JIT por operación. En este corte el resultado sigue **0/14 ejecutadas**.

## Rollback y recuperación

El rollback remoto no se ha probado. R178 y el plan aportan diseño/evidencia local, no ejecución en Cloudflare/Supabase. Preparar de antemano el SHA y versions anteriores, personas de guardia, owner del ambiente, acción safe-suspend, criterio de restauración y evidencia aceptable. Cada mutación remota de rollback mantiene permiso separado.

1. **Antes de `expand`:** detener la promoción; dejar el ambiente/versión existente sin cambio. No reactivar Free ni modificar DNS/bindings desde este paquete.
2. **Después de `expand`, antes del runtime:** detener el siguiente writer/deploy. Mantener los objetos aditivos compatibles; no aplicar `DROP` ni rollback SQL automático. Comparar ledger y estado real y acordar recuperación bajo JIT DB.
3. **Después de deploy y antes de contract:** si hay riesgo, aplicar safe-suspend solo con el control y autorización preparados; frenar nuevas invitaciones/mutaciones, mantener lecturas públicas, volver Pages/Edge/Worker al último SHA/version compatible y confirmar sesión/cookies, errores y auditoría. Mantener esquema expandido, keys/nonces y registros append-only. No borrar datos ni auditoría.
4. **Fallo del gateway o pre-request:** no restaurar grants ni cambiar `pgrst.db_pre_request` por improvisación. La secuencia documentada exige safe-suspend, rollback coordinado BFF y restauración aprobada del pre-request previo; el guard de `p_first = NULL` se conserva y no se eliminan keys/nonces.
5. **Si hubo efectos o daño de datos:** detener writers y escalar al owner DB/Security; backup/restore, replay y recuperación de cuentas requieren autorización JIT con scope y punto de restauración. No ejecutar cleanup como parte del rollback.
6. **Después del rollback:** registrar SHA/versiones reales, estado de bindings por nombre, resultado de rutas públicas/Admin, ledger no mutado/expandido, errores y decisiones; revisar evidencia sin adjuntar datos sensibles. Repetir UAT solo tras nueva autorización.

No ejecutar rollback/restore como ensayo en Development sin un drill y JIT independientes. `contract` no forma parte del rollback automático: se mantiene bloqueado hasta estabilidad y autorización.

## Permisos posteriores separados

- Lectura de branch protection requerida, reglas de checks y scopes de instalación; solicitar al admin acceso de solo lectura o evidencia sanitizada. No cambiar rulesets.
- Si el owner lo decide, reactivación/configuración de Development Free y consultas de metadata schema/Auth necesarias para cerrar la preflight.
- JIT SQL específico para cualquier `expand`/repair/rollback de DB; no Pro writes.
- JIT Cloudflare para secret bindings, allowlists, service binding, Worker/DO, Pages deployment, routes o DNS; nunca pedir ni registrar valores.
- JIT Supabase para Edge deployment/config/auth redirects y pruebas de correo/invitación; no exponer tokens/buzones.
- Autorización separada para push, PR, merge y workflow_dispatch; aprobación explícita posterior para cada transición/host y cada D01–D14 con efectos.
- Recuperación/restore/schedules/writers/backfills tienen scopes propios y no quedan cubiertos por aceptar este documento.

## Navegación

[Resultado de lecturas remotas R15](h3req1_g10_remote_preparation_2026-10-13_r15.md) · [Checks R15](h3req1_remote_preparation_checks_2026-10-13_r15.txt) · [Revisión independiente R15](h3req1_remote_preparation_independent_review_2026-10-13_r15.txt) · [Manifiesto overlay R15](h3req1_remote_preparation_manifest_2026-10-13_r15.json) · [Estado operativo](../estado_del_proyecto.md) · [CI/CD](../ci_cd.md) · [Database](../database.md) · [Backend](../backend.md) · [Operación](../operacion.md) · [Seguridad](../seguridad.md) · [Plan H3-CLOSE D01–D14](../operaciones/plan_cierre_integral_h3req1_2026-10-04.md) · [Índice](../indice.md)
