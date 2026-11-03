# H3REQ1 — verificación remota y checkpoint de integración R18

Fecha: 2026-10-14. Checkout local `feat/h3req1-sync-20261002`; HEAD `a57bc415257ab8154d40d7c71d34c69d0bdaeb0d`; baseline `4eb4d877a50b012bb630a129bd0c74482c33be9c`. El manifiesto R18 identifica el árbol candidato completo; HEAD por sí solo no lo representa. R17 y sus fuentes permanecen inalterados como evidencia histórica.

## Resultado ejecutivo

**NO-GO Development.** El paquete A aprobado se ejecutó sobre Supabase Free y las nueve migrations exactas se verificaron en ledger y metadata. Pro permaneció de solo lectura. B no se ejecutó: falta un método disponible y seguro para provisionar la misma clave HMAC en Cloudflare Pages Preview y Supabase Edge sin exponerla, y no está disponible Wrangler ni un setter de secretos Supabase en los conectores presentes. No se hizo cambio parcial de Preview, Worker/DO ni Edge. No hay push, PR, merge ni deployment del candidato.

El responsable confirmó en esta continuación que descarta DELETE físico y mantiene aprobado C retentivo: conservar la identidad Auth antigua, referencias, invitación accepted y auditoría, inhabilitarla con las operaciones exactas del paquete, liberar el correo para una identidad nueva y comparar el UUID únicamente en memoria. C sigue sin consumirse y sus prerrequisitos pendientes no se consideran satisfechos. Gmail permanece intacta y no se presupone un tercer administrador.

La metadata actual de GitHub se leyó el 2026-10-14 16:02 UTC: el repositorio es público, activo y conserva `main` como default. `desarrollo` está marcada protegida y sigue en el baseline; también `certificacion`. `GET /branches/desarrollo/protection` devuelve 403 a esta integración, así que no acredita required checks, approvals, enforcement ni bypass efectivo. El ruleset activo `owner-only-protected-branch-updates` tiene una regla `update` y un actor con modo `always`; no se usará bypass. El directorio de workflows de `desarrollo` contiene `security-audit.yml` y no contiene `protected-workflow-integrity.yml`; tampoco se encuentra PWI en `main`. El último run de `Security Audit Gate` es un push exitoso sobre el baseline del 2026-09-27. Ese SHA tiene 15 check-runs: 14 success y `H2 Main Production Expand Gate` skipped; no son checks del candidato ni PR runs. Un combined status separado devuelve 0 statuses. La ruta a `desarrollo` puede conservar el flujo PR existente, pero antes de publicar el owner debe confirmar desde una superficie administrativa que `security-audit` es requerido, que se exige una aprobación no autora y que el merge ordinario no usa bypass. Si esos controles no están configurados, el único cambio propuesto es una regla limitada a `desarrollo`; no se toca `main`, la rama default ni el ruleset de bypass.

## A — ejecución remota verificada

Target único: Free `aqrldlmlszjtgpqiegaa`, compartido por Development y Certification. Estado al cierre: `ACTIVE_HEALTHY`, PostgreSQL `17.6.1.111`, 80 entradas en ledger. Las nueve migrations aprobadas constan en ledger con sus hashes locales verificados:

| Migration | SHA-256 |
|---|---|
| `20260927_h3_publication_visibility_contract` | `2b02df3f9ab5736da292d5b8653ca567111cd82705ada182b5baa8085b21e1aa` |
| `20261001_h3_course_editorial_audit_availability` | `14e47f4ab4a50382bbea8453b84295bcb2f707e760c8c0a9ae5da4c1f71c3097` |
| `20261001_h3_invitation_reservation_compensation` | `1001c059b951eaa907016e31be08bef9f3e0a7835f30ea2cac5227a123927270` |
| `20261002_h3_admin_quota_expand` | `d839f7f760bdb12025297a24e09b547cf4f0b5989d3c0142835978083be9bb67` |
| `20261002_h3_admin_quotas` | `7ea746ca73f2acee31956e59d490083c4fbfcaebf51941d4c6cb52618c906619` |
| `20261004_h3_admin_queue_first_null_guard` | `012f994af8b44353e385e68b22dc1b15535e31f47f8f990716cbd726f1908711` |
| `20261004_h3_admin_rpc_signed_gateway_expand` | `e80e236348c2eefe79035c6f6ea5e22bc5dea194555d07a1f1b5a8b41a02876c` |
| `20261004_h3_admin_rpc_signed_gateway_payload_bound_wrapper` | `c8a69e06e2d1d3a7f5e2245f6fb68ac6220deac3fd0b273edb5bcedafdba81a5` |
| `20261010_h3_admin_members_service_select` | `6a4d4476e5143537b51390becfe995ca5cb9340ed891c1232e7af2cb1cb9e49c` |

The two migrations already present before A were not reapplied: `20260927_h3_admin_queue_facets_filter` and `20260928_h3_invitation_accept_email_regex_fix`. The ledger moved from 71 to 80; latest version is `20261014144922`. Final Free catalog metadata: 29 relations, 398 columns, 130 constraints, 45 policies, 108 functions, 240 routine grants, 458 table grants and 20 triggers. Pro remains `ACTIVE_HEALTHY`, PostgreSQL `17.6.1.111`, ledger 23/latest `20260607221002`; no Pro writes. Catalog digest after A: `14094ee18b1b47b1b02d57fcd8d28ba9`.

Un helper de orquestación falló con `ARG_MAX` al serializar metadata de catálogo después de aplicar las migrations 2 y 3; la migration 4 no fue aplicada por ese intento. La recuperación fue de solo lectura: verificó hashes locales, ambas entradas de ledger y catálogo. No hubo retry ni reapply. Los pasos A restantes se aplicaron una vez, en orden, y el ledger final se volvió a leer. La migration 3 requerida por C está presente y validada.

La configuración `pgrst.db_pre_request` sigue sin activarse. No se aprovisionó clave de gateway; no se ejecutaron RPCs mutadoras, consultas de filas operativas, DML adicional, reset, invitación ni correo.

## Estado de otros proveedores

Las lecturas R18 refrescaron GitHub, Cloudflare y metadata Supabase después del avance A. No se devolvieron valores de variables ni filas de aplicación.

- **GitHub:** el SHA base de `desarrollo` conserva 15 check-runs (14 success, uno skipped); el run `Security Audit Gate` correspondiente fue un push exitoso. Protecciones detalladas y required status no son visibles por 403; PWI está ausente de `main` y `desarrollo`. Ver el corte exacto en la sección anterior.
- **Cloudflare:** el proyecto Pages `studiamatch` mantiene producción en `main`; su Preview es global y compartido con Certification. La consulta de hasta 25 deployments encontró `desarrollo` en el SHA base `4eb4d877…`, success, alias `desarrollo.studiamatch-aty.pages.dev`, creado el 2026-09-27; no hay deployment del candidato. En Preview existen `ADMIN_ALLOWED_HOSTS`, `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`, `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_SUPABASE_PUBLISHABLE_KEY` y `NEXT_SUPABASE_SECRET_KEY`, todos declarados como `plain_text`. No hay bindings Preview ni Pages Functions; el inventario devuelve 0 Worker scripts y 0 namespaces Durable Objects. No se leyeron valores y no se cambió configuración. B sigue sin canal coordinado para provisionar las claves de Pages/Edge y desplegar en orden.
- **Supabase Auth/Edge:** Free sigue `ACTIVE_HEALTHY`, PG `17.6.1.111`, ledger 80/latest `20261014144922`; Pro sigue `ACTIVE_HEALTHY`, ledger 23/latest `20260607221002`, sin writes. `admin-invite` Free está ACTIVE v12 con `verify_jwt=true`; `send-lead-emails` está ACTIVE v21. Las herramientas disponibles no exponen getter de configuración Auth no secreta para confirmar los avisos `Email address changed` y `Verification method removed`; ambos deben comprobarse deshabilitados antes de C. No se leyeron filas de usuarios, buzón, UUID Auth, token ni sesión.
- **braces:** se conserva el snapshot local `3.0.4-h3.1`. La procedencia pública R17 identifica el commit upstream, pero el PR fuente está cerrado sin merge y npm no registra esta variante como release oficial. No se sustituyó el snapshot ni se crea waiver.

## Visibilidad pública y derivados sanitizados

El repositorio GitHub es público. Una revisión del paquete exacto encontró el correo de la cuenta de prueba en dos fuentes locales R17/archivo histórico y el correo de la administración principal en la matriz vigente (este último ya estaba en el baseline 4eb). Los originales locales se conservaron sin cambios y quedan excluidos del paquete público; cuatro copias públicas sanitizadas R18 sustituyen sus referencias. La copia candidata de la matriz omite el identificador preexistente. No se reescribe la historia del remoto.

La rama local `feat/h3req1-sync-20261002` está dos commits por delante del baseline y contiene los originales R17 en su historia local; no existe una rama remota coincidente según `git ls-remote` de solo lectura. No se publicará esta historia. Para una publicación futura, el commit/PR deberá partir del baseline aprobado y contener solo el snapshot sanitizado reconciliado, manteniendo el branch local original intacto. No se creó commit ni rama nueva en este checkpoint.

Derivados públicos R18: [estado histórico](h3req1_estado_historico_2026-10-12_public_sanitized_r18.md), [reporte R17](h3req1_g10_remote_preparation_2026-10-14_r17_public_sanitized_r18.md), [paquete R17](h3req1_development_integration_package_2026-10-14_r17_public_sanitized_r18.md) y [cuerpo R17](h3req1_pr_body_draft_local_review_2026-10-14_r17_public_sanitized_r18.md). Cada uno conserva su original solo local; el contenido personal identificado se retiró de las copias públicas, y el scan no halló JWT con forma de sesión en ellas. Las direcciones de fixtures que permanecen en suites usan dominios de prueba; no son las identidades protegidas. No se publica ninguna UUID de Auth ni material de sesión; la UUID de la identidad nueva se comprobará en memoria solo tras C/D.

Los 18 artefactos históricos seleccionados con modo local `0600` por cierre de catálogo siguen incluidos tras scan de contenido/sanitización sin marcadores personales, UUID, JWT, clave Supabase o asignación sensible. La revisión independiente final del paquete R18 concluyó PASS sin hallazgos; Git no persiste el modo `0600` y no hubo publicación.

## Permisos y pruebas

El repositorio es público. El paquete exacto incluye 18 evidencias históricas R14 seleccionadas por el cierre de referencias de los catálogos; en el checkout tienen modo POSIX `0600`, pero Git solo persiste el bit ejecutable. El scan aislado de esos 18 archivos y el scanner del paquete completo pasaron sin marcadores sensibles; la revisión independiente final R18 también pasó sin hallazgos. No se mostró contenido ni valores. No hubo publicación; si una revisión posterior identifica contenido privado, detener el push y reconciliar el defecto sin alterar la evidencia fuente.

## Permisos y pruebas

| Alcance | Estado R18 | Condiciones vigentes |
|---|---|---|
| A DB Development | **Consumido** | Nueve migrations exactas aplicadas y verificadas en Free; Pro y datos operativos fuera. No repetir. |
| B runtimes/configuración | **Aprobado, no consumido** | No tocar Preview compartido hasta resolver el canal privado de secretos, verificar configuración actual y desplegar Worker/DO→Edge→Pages según paquete. |
| C retentivo Outlook | **Aprobado, no consumido** | A migration 3 satisfecha; todavía requiere B, D01/D02 con la identidad actual, preflight privado exacto, Gmail admin activa y lectura que confirme ambos avisos Auth deshabilitados. No DELETE físico. |
| D aceptación | **Aprobado, no consumido** | D01–D14 0/14 y regresión adicional 0/11. D05 no puede desactivar Gmail; si no existe cobertura remota compatible, requiere paquete/JIT aislado adicional. |
| Commit/push/PR/merge | **Autorización condicional vigente** | No hubo commit R18, push, PR ni merge. No push hasta completar B; merge solo con checks obligatorios y review humana válida sobre SHA exacto. |
| Deployment Development | **No ejecutado** | No hay SHA/deployment candidato. Certification, `main` y Production fuera. |

No se accedió a buzones, credenciales, valores de secretos ni filas operativas. Gmail no se releyó ni modificó; sus propiedades autorizadas permanecen como invariantes y se cotejarán antes de C/D. No hay aceptación cliente remota, observación de navegador ni GO Development.

## Próximo checkpoint

1. Obtener un canal seguro para configurar el secreto compartido de cuota en Pages Preview y Supabase Edge y las otras claves distintas de Pages; confirmar solo nombres/presencia, nunca valores. Si el responsable realiza esa operación en consola privada, responder únicamente con estado de finalización.
2. Resolver la ruta protegida sin cambiar default branch ni tocar `main` en este ciclo: configurar fuera del repositorio un required workflow confiable para `desarrollo` y obtener lectura efectiva de protecciones/checks/approvals, o pausar integración y tramitar posteriormente el bootstrap `main` como autorización independiente.
3. Revalidar Free/Cloudflare/GitHub antes de cada siguiente operación. Completar B antes de cualquier push/Preview. Luego D01/D02 con Outlook existente; después evaluar C solo si B y ambos avisos Auth están verificados.
4. Solicitar intervención humana antes de cada bloque de navegador y el JIT incremental de D05 si aplica. No hay permiso consumido que se renueve por este checkpoint.
