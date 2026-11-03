# Paquete de integración Development H3REQ1 — R18

> **Estado: NO-GO Development.** R18 conserva R17/R16/R15/R14, la base funcional R8, la selección documental R13 y sus evidencias. No reinicia implementación ni reorganización Obsidian. Este paquete registra A consumido y los bloqueos actuales; sus operaciones restantes heredan únicamente el alcance exacto de [paquete R17](h3req1_development_integration_package_2026-10-14_r17_public_sanitized_r18.md). El manifiesto R18 determina el árbol candidato completo.

## Identidad del candidato y límites
## Decisión de preservación de la cuenta de prueba

La instrucción humana vigente descarta el borrado físico. C retentivo está aprobado exactamente como paquete: preservar la fila Auth, referencias, invitación accepted y auditoría; desactivar la membresía por RPC auditado, trasladar el correo Auth antiguo al identificador técnico único `example.invalid`, bloquear la identidad y retirar los factores TOTP cubiertos. La nueva invitación podrá usar el mismo buzón solo después de C; el nuevo usuario Auth debe tener UUID distinto, comprobado sin publicarlo. C no se consumió. Antes requiere B, D01/D02 con la identidad existente, settings Auth de avisos verificados deshabilitados y preflight privado aprobado en el paquete. Gmail se conserva íntegra; puede gestionar Outlook solo durante la interacción explícita del responsable.


- Repositorio: `https://github.com/romelhc95/studiamatch`.
- Lectura GitHub R18 del 2026-10-14 16:02 UTC: el repositorio está público, activo y usa `main` por rama predeterminada; `desarrollo` está marcada protegida y conserva el baseline. La lectura detallada de branch protection devuelve 403. `security-audit.yml` existe en `desarrollo`, PWI no existe allí ni en `main`; el ruleset activo de actualización tiene un actor `always` que no se usará. Aprobaciones/status requeridos no quedan acreditados.
- Checkout: `/home/romel/src/studiamatch-h3req1-sync-20261002`; branch `feat/h3req1-sync-20261002`; HEAD observado `a57bc415257ab8154d40d7c71d34c69d0bdaeb0d`; baseline `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- R17 sigue preservado. R18 selecciona solo la evidencia nueva y los consumidores exactos del manifest; todo el WIP restante, originales, backups, secretos y salidas quedan excluidos. El checkout `/home/romel/src/studiamatch` continúa en solo lectura.
- Free `aqrldlmlszjtgpqiegaa` es Development y comparte proyecto con Certification. Pro `xwhtiqmboljkshrtviyw` sigue siendo baseline autoritativo de solo lectura. No copiar datos operativos.
- `main`, Certification y Production quedan fuera de esta integración. No cambiar la rama predeterminada, usar bypass, autoaprobar, bajar checks ni ejecutar workflow_dispatch.

El candidato incluye 18 evidencias históricas R14 con modo local `0600`, seleccionadas por referencias directas de catálogos. Git solo almacena `100644/100755`; no conservará el modo local restringido. El scan de contenido sanitizado de esos 18 archivos encontró cero email, UUID, JWT, clave Supabase o asignación sensible; la revisión independiente final del paquete R18 pasó sin hallazgos. Git no preserva el modo local `0600`; no hubo publicación y el cuerpo PR no incluye sus contenidos. No exponer ni copiar sus contenidos al chat.

## A. Delta DB — consumido

El paquete R17 A fue ejecutado una vez sobre Free: nueve migrations exactas, cada una presente en ledger con hash local coincidente; las dos ya aplicadas se omitieron. Free quedó activo y saludable, ledger 80, metadata catalogada; Pro permanece activo con ledger 23 y sin writes. El reporte [R18](h3req1_g10_remote_preparation_2026-10-14_r18.md) conserva hashes y conteos sanitizados. La migration 3 de reserva/compensación está verificada, por lo que se satisface ese prerrequisito técnico de C.

No repetir A ni ejecutar `db push`, DML, backfill o SQL de rollback. La activation de gateway (`pgrst.db_pre_request` y una clave privada) no se incluyó en las nueve migrations ni se ejecutó. Cualquier futuro subpaso de gateway solo después de que BFF/Edge compatibles estén desplegados, con su input revisado según el paquete R17.

## B. Runtimes, bindings y Preview — aprobado, sin consumo

B no tiene efectos remotos todavía. La configuración Preview de Pages aplica a todos los previews del proyecto compartido, incluido Certification; el deployment actual observado de Certification no tenía Functions. El paquete B R17 limita `ADMIN_ALLOWED_HOSTS`, elimina `NEXT_SUPABASE_SECRET_KEY` solo de Preview y crea el binding interno `ADMIN_QUOTA`, además de desplegar Worker/DO y Edge en orden. Production queda fuera.

**Estado remoto observado:** Preview declara como `plain_text` `ADMIN_ALLOWED_HOSTS`, las tres variables Supabase publicables/URL y `NEXT_SUPABASE_SECRET_KEY`; no tiene bindings ni Pages Functions. En la cuenta no se listan scripts Worker ni namespaces DO. El deployment `desarrollo` success permanece en el SHA base y hostname de Desarrollo. No se leyeron valores.

**Bloqueo de ejecución:** aunque la lectura/configuración Pages está disponible, no hay un setter de secretos para Supabase Edge, Supabase CLI ni una autenticación Management API disponible dentro del contenedor, y Wrangler no está instalado. Sin el canal privado compartido, no se pueden provisionar las claves de Pages/Edge y desplegar el conjunto en orden. No enviar valores en chat, repositorio, argumentos, logs o evidencia. No se hará un cambio parcial de Preview/Worker/DO/Edge.

El siguiente avance requiere que el owner habilite una vía privada soportada o configure las variables desde las consolas privadas exactas. Los nombres, targets, separación entre claves, hashes de artefactos, hosts, pasos, límites y rollback ya constan en [paquete R17 §4](h3req1_development_integration_package_2026-10-14_r17_public_sanitized_r18.md#4-paquete-b--workerdo-pages-preview-edge-y-secuencia-de-deploy). La confirmación puede limitarse a nombres/tipos/presencia y resultado de despliegue, sin valores.

## Ruta protegida de integración hacia `desarrollo`

Lectura R18: default `main`; rama `desarrollo` protegida en el listado, pero detalle de branch protection 403; el ruleset activo de actualización tiene un bypass `always` que no se usará; PWI `pull_request_target` no aparece en `main` ni `desarrollo`. El workflow base `security-audit` sí existe y el SHA actual tiene sus checks exitosos, pero eso no demuestra que el status sea requerido ni que se exija aprobación. No se ha creado PR.

**Ruta que preserva `main`:** mantener la integración como PR feature→`desarrollo` usando el `security-audit` que ya existe en el branch base, sin bypass. Antes del push el owner debe confirmar en una vista administrativa que exige ese check y una aprobación no autora sobre el SHA vigente. Si falta cualquiera, el cambio concreto necesario es una regla de protección limitada a `desarrollo` que exija PR, `security-audit` y una aprobación, descarte reviews obsoletas, aplique a admins y bloquee force-push/deletion; no tocar la default branch ni `main`. Si además se requiere PWI, su origen confiable debe vivir fuera del candidato y la regla required-workflow limitarse a `desarrollo`; no se bootstrapeará desde el PR que protege. La integración no avanzará hasta que el owner aporte la verificación o autorice ese paquete de configuración por separado.

La autorización condicional de commit/push/PR/merge sigue vigente para el paquete validado. No push que cree Preview antes de B. No merge sin checks obligatorios aprobados y review humana válida no autora sobre el SHA exacto.

## C. Reinicio retentivo Outlook — aprobado, sin consumo

C no es borrado físico. La instrucción humana descarta DELETE y aprueba conservar la fila Auth anterior, referencias, invitación accepted y auditoría, desactivar su membresía por el RPC auditado, mover su email Auth a identificador técnico único `example.invalid`, bloquearla y retirar los factores TOTP incluidos en el paquete. A migration 3 ya satisface su precondición de esquema; B, D01/D02 y la lectura administrativa de ambos avisos Auth aún faltan. Las herramientas actuales no exponen si `Email address changed` y `Verification method removed` están deshabilitados; no tocar esos settings fuera del alcance aprobado. C permanece detenido.

Antes de ejecutar C: D01/D02 con la identidad actual; inventario privado por identidad de Auth/membresía/factores/dependencias; confirmar que Outlook coincide exactamente con C y que Gmail sigue admin activa; conservar comparación mínima fuera de evidencia pública. Después de C verificar bloqueo efectivo, disponibilidad del email, integridad de referencias/auditoría, y que la identidad anterior no usa Admin. No asumir que cambiar ban invalida JWT existentes; cualquier revocación no incluida exige delta JIT antes.

La identidad/correo, membresía admin activa, contraseña, MFA, sesiones, historial y datos Gmail son invariantes de preservación. R18 no modificó Gmail; verificar en privado que mantiene esos atributos antes de C/D y detenerse si no coinciden. Gmail puede ser actor admin para invitar/gestionar Outlook solo con el responsable usando el navegador. La cuenta Auth nueva debe tener UUID distinto del viejo; la comparación ocurre en memoria y jamás se publica.

## D. Aceptación Development — aprobado, sin consumo

D01–D14 continúan 0/14; regresión adicional definida, 0/11. No se ejecutó prueba remota ni browser real. Tras B y la integración protegida, ejecutar literalmente el plan canónico con límites D del paquete R17, conservando fallos, evidencia sanitizada y confirmaciones humanas por bloque. D01/D02 usan la identidad anterior antes de C. D03 requiere Gmail como actor y la nueva Auth identity Outlook; D04 gestiona roles desde admin autorizado y Outlook no puede autoasignárselos.

No desactivar Gmail ni otra identidad preservada para D05. Si no existe cobertura remota autorizada compatible, el escenario aislado propuesto es un proyecto Supabase temporal separado de Free/Certification, con identidades y datos sintéticos `example.invalid`, una membresía admin de prueba y una membresía objetivo; probar que la última administración activa no se puede desactivar, y desechar el proyecto completo después de guardar evidencia sanitizada. Crear proyecto, usuarios sintéticos, seed de DB, correo/identidades y destrucción del proyecto requiere un paquete y JIT adicionales. No crear aliases/cuentas ni asumir un tercer admin antes de esa aprobación.

Los 30 minutos por intervención humana se esperan en segmentos cortos; silencio no es aprobación. Nunca pedir o capturar contraseña, MFA, enlace Auth, JWT o secreto por chat.

## Estado de transición y recuperación

| Fase | Resultado al corte R18 | Próximo gate |
|---|---|---|
| `expand` | Nueve migrations A aplicadas y verificadas en Free; metadata Pro sin cambios. | Conservar expand aditivo; sin rollback SQL. |
| `compatibilidad` | Worker/DO, BFF, bindings, Preview y Edge sin cambiar. | Resolver provisión privada de secretos y completar B en orden. |
| `deploy` | Sin push, PR, merge ni deployment candidato; Pages sigue SHA base. | Ruta protegida válida, B completo, checks/review sobre SHA exacto. |
| `contract` | No ejecutado. | Diferido hasta estabilidad y regresión/aceptación. |
| rollback/recuperación | No ejercido; conservar deployment/versiones actuales, gateway inactivo y auditoría/datos. | Solo paquetes exactos A/B/D; no restore/purga/deploy adicional. |
| no degradación | No demostrada en runtime Development. | Aceptación remota y catálogo adicional después de integrar. |

No declarar GO Development. El [reporte R18](h3req1_g10_remote_preparation_2026-10-14_r18.md), [manifest R18](h3req1_pr_scope_manifest_2026-10-14_r18_reconciled.json), [checks R18](h3req1_remote_preparation_checks_2026-10-14_r18.txt), [revisión independiente R18](h3req1_remote_preparation_independent_review_2026-10-14_r18.txt) y [cuerpo PR R18](h3req1_pr_body_draft_local_review_2026-10-14_r18.md) forman el checkpoint del paquete. La plantilla versionada es [`.github/pull_request_template.md`](../../.github/pull_request_template.md). El plan D01–D14 canónico permanece en [H3-CLOSE-08](../operaciones/plan_cierre_integral_h3req1_2026-10-04.md#h3-close-08--matriz-de-aceptación-remota-y-go-development-real).
