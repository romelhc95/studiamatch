# Plan propuesto: ingreso, corrección editorial y auditoría de cursos

**Fecha:** 2026-10-01.

**Estado:** plan aceptado para ejecución local; **no autoriza** cambios remotos,
ejecución de writers, deploy, push, PR ni promoción.

**Ámbito del siguiente ciclo:** trabajo local y, únicamente con autorizaciones
JIT separadas, Free/Development (`aqrldlmlszjtgpqiegaa`) y su Preview.
Certification y Production quedan fuera.

**Autoridad viva:** [Estado Del Proyecto](../estado_del_proyecto.md). Contratos relacionados: [HITO-002](../hitos/hito_002.md), [HITO-003](../hitos/hito_003.md) y [diagnóstico remoto IDAT](../evidencia/h3req1_development_remote_cycle_2026-09-26.md#diagnóstico-read-only-de-publicación-pública-idat).

## Necesidad y elección de arquitectura

Al ingresar un curso nuevo, el harvester debe descubrirlo y extraerlo; cleansing y enrichment procesan el contenido; `sync_vector_worker.py` hace el upsert de la base automática en `courses` y calcula calidad/procedencia en `course_editorial_state`. La persona editora debe poder completar datos faltantes; `admin` debe poder corregir también valores inconsistentes presentes, con identidad y cambios consultables en auditoría. **El pipeline no publica por sí solo.**

**Decisión aceptada para el ciclo local:** conservar `courses` como base del pipeline y `course_editorial_state.manual_overrides` como capa humana persistente. La superficie pública lee el valor efectivo (manual válido, si existe; si no, pipeline), nunca `courses` directamente. Escribir desde el editor directamente en `courses` mezclaría autores y permitiría que el siguiente upsert revirtiera una corrección; para optar por escritura directa habría que diseñar primero ownership por campo, protección ante upsert, historial y reconciliación. Esa variante queda fuera de este ciclo.

En el diagnóstico, la auditoría ya insertaba `actor_user_id`, valores anteriores/nuevos y acción en `course_editorial_audit`, que es append-only; no había un lector de historial Admin. El RPC editorial guarda overrides, no actualiza `courses`; el editor enviaba el conjunto de campos permitidos, y la previsualización no garantizaba que la vista pública estuviera habilitada. El ciclo local añade lectura Admin, payload solo-diferencias y mensajes explícitos de los gates: **guardar no equivale a publicar**.

### Hechos y brechas verificadas

- El contrato de calidad actual calcula faltantes de siete campos (`name`, `institution`, `url`, `slug`, `category`, `mode`, `duration`); `complete` no implica ausencia de inconsistencias u otros datos opcionales. Conciliarlo con el diccionario de publicación/atestación cliente antes de ampliar requisitos: no imponer silenciosamente trece campos ni alterar el alcance existente.
- En la lectura Free observada, los 350 estados editoriales tienen disponibilidad `unknown`; no se identificó un productor vigente para `available`/`unavailable`. No inferir disponibilidad de un HTTP 200, de un CTA genérico ni de la completitud editorial.
- El curso IDAT de la evidencia está `published`/`complete`, tiene override `mode=Remoto`, disponibilidad `unknown` y pertenencia a cohorte legacy: la vista pública conserva `Hibrido` de `courses`. No atribuirlo a caché ni forzar un cambio de disponibilidad sin evidencia. El delta local `db/migrations/20260927_h3_publication_visibility_contract.sql` no está aplicado en Free y no corrige cursos publicados previamente.
- `generateStaticParams()` y `dynamicParams=false` materializan rutas de detalle en el build. Un curso nuevo elegible en la vista DB no adquiere automáticamente una URL pública; un cambio posterior puede actualizar datos cargados por cliente en una ruta ya construida, pero metadatos/HTML prerenderizados pueden quedar desfasados hasta un nuevo build.
- Roles existentes: `user` activo edita solo `missing_fields`; `admin` activo corrige todos los campos editoriales allowlisted y publica. Ampliar la edición de inconsistencias para `user` sería una decisión contractual adicional, no una consecuencia implícita de este plan.
- Decisión humana sanitizada del 2026-10-01: no se requiere clasificador automático en este ciclo. La UI muestra faltantes y diferencias entre override y pipeline; Admin revisa y decide/corrige según su rol. No etiqueta automáticamente un valor extraído como «incorrecto». Cualquier clasificador futuro requiere categorías, reglas, fuentes y criterios de falsos positivos aceptados antes de desarrollo.

## Tareas secuenciales y gates

| Etapa | Implementación propuesta | Evidencia/gate antes de avanzar |
|---|---|---|
| **0. Baseline y fuente cliente** | Validar inicio de task contra la fuente privada mediante atestación sanitizada versionada; contrastar el baseline Pro **solo a través de artefactos existentes** mientras la limitación remota sea Free/Preview. Inventariar función efectiva, roles, RLS/grants, estado de migraciones y casos IDAT. Definir matriz por campo: obligatorio/opcional, `pipeline_owned`/`manual_owned`/`hybrid_manual_preferred`/`computed`, valores válidos, editor autorizado y fuente oficial. | Alcance y criterios trazables; sin drift no resuelto. Si verificar baseline exigiera consultar Pro remotamente, detenerse y pedir autorización nueva; si falla gate documental, no iniciar código/DB/UI/pipeline. |
| **1. Ingreso y calidad** | Preservar gates `pipeline_ready` y `production_enabled`, upsert por URL y estado editorial por curso, sin publicación automática. Separar `missing_fields` de las diferencias visibles entre pipeline y override. Mostrar origen y timestamp disponibles; no inferir contradicción semántica ni etiquetar automáticamente un valor como incorrecto. | Nuevo curso incompleto aparece una sola vez en cola Admin; faltantes y diferencias son visibles para revisión humana, sin esconder programas ni publicar con el pipeline. Repetir sync no duplica registros y preserva overrides. |
| **2. Corrección editorial** | Editar solo campos cambiados con validación de tipo y allowlist; ofrecer retirar un override (volver al pipeline) en vez de persistir un string vacío. Conservar optimistic locking, recomputar faltantes/calidad en servidor y presentar valor base, override y valor efectivo. `admin` resuelve inconsistencias presentes; `user` conserva permiso limitado a faltantes. Diferenciar «vista previa de cambios» de «página actualmente pública». | Casos faltante, inconsistente, conflicto de versión, retiro de override y resync; el override humano válido no se pierde y los cambios no autorizados se rechazan. |
| **3. Disponibilidad y publicación** | Definir fuente oficial y criterios observables. La evidencia global tiene una vigencia máxima de **90 días calendario desde `observed_at`**; `valid_until` posterior a ese máximo se rechaza y lo ausente, inválido o vencido resulta `unknown`. Guardar evidencia mínima, origen, fecha y motivo para `available`/`unavailable`/`unknown`. La confirmación humana excepcional debe ser explícita, respaldada y caducar, sin un botón arbitrario de «disponible». Rebasar el gate local de publicación contra baseline y fijar precondiciones transaccionales: calidad, faltantes, inconsistencias bloqueantes conforme a revisión Admin, disponibilidad, `is_active`, `is_verified`, perfil habilitado y permisos. Decidir la política para cursos **ya** publicados que pasen a `unknown`/`unavailable` sin apagar de golpe la cohorte legacy. | Publicación por Admin solamente cuando se cumplen todos los gates; rechazos explicados y auditados según contrato; sin marcar en masa los 350 `unknown` como disponibles. Caso IDAT se corrige solo con evidencia legítima y comprobación vista→Preview. |
| **4. Historial de auditoría Admin** | RPC de lectura paginada y acotada por curso (o filtros seguros), `SECURITY DEFINER` con `search_path` fijo, validación de rol Admin activo y el control de sesión vigente. Exponer fecha, acción, actor, cambio por campo, antes/después, razón, origen pipeline/humano e identificador de solicitud cuando exista. Resolver actor mediante identificador estable y nombre interno si se autoriza, sin depender de acceso directo del browser a `auth.users` ni incluir identidad en vistas públicas. Pantalla de historial en el editor con paginación y estado de error. | Admin puede atribuir edición/publicación; anon, `user` y membresía inactiva no leen el historial. Sin `SELECT` directo autenticado sobre la tabla, sin secretos/PII en público y sin UPDATE/DELETE de auditorías. |
| **5. Vista efectiva y static export** | Mantener compatibilidad con la cohorte legacy mientras se habilita el contrato estricto para cursos nuevos. Mostrar en el editor estado público actual y motivo de divergencia. Comprobar listado, ficha, comparación y rutas; definir build/deploy autorizado que incluya slug nuevo, además de cuándo regenerar HTML/metadatos para cambios posteriores. | Coincidencia editor→vista efectiva→página para curso elegible; bloqueo y explicación para no elegible. Curso recién publicado tiene ruta tras build autorizado, sin 404 ni metadata engañosa; no afirmar resultado remoto por pruebas locales. |
| **6. Contract posterior** | Solo tras estabilización y aprobación de promoción, retirar la cohorte legacy y el comportamiento viejo; documentar remediación individual de cursos no elegibles y métricas de pérdida potencial. | Ningún curso legacy desaparece inesperadamente; catálogo, seguridad y rendimiento preservados. No ejecutar esta etapa durante la validación limitada a Free/Preview. |

## Validación, transición y rollback

**Expand:** introducir señales de calidad/disponibilidad y lectura de auditoría sin cambiar la visibilidad legacy. **Compatibilidad:** overlays siguen prevaleciendo donde el gate estricto ya se cumple; el resto conserva el comportamiento documentado hasta remediación aprobada. **Deploy:** solo después de Docker/PG17, revisión de seguridad, JIT DDL si aplica y autorización independiente para writes/Preview. **Contract:** retirar legacy únicamente tras evidencia en ambientes promovidos y aprobación; no cerrar el ciclo en estado de compatibilidad indefinida.

Pruebas mínimas locales en Docker: reglas de calidad y procedencia; SQL/RLS/grants con roles anon, `user`, `admin`, inactivo y service; audit append-only; concurrencia/optimistic locking; sync repetido NOOP y preservación manual; publicación permitida/denegada; integración editor/vista/renderer y build estático con ruta nueva; regresión IDAT y muestra legacy; typecheck, lint, tests y security audit. Revisar funcionalidad, escalabilidad (cola/historial paginados), seguridad, mantenimiento, calidad y rendimiento. Revalidar hallazgos y atestación sanitizada al cierre; no declarar GO con HIGH/CRITICAL sin waiver formal aprobado.

**Rollback:** preservar funciones/vista previas como ruta de compatibilidad durante expand/deploy; revertir proyección/feature flags mediante migración compensatoria autorizada, sin borrar datos ni auditorías. Ante fallo de disponibilidad o generación de rutas, detener nuevas publicaciones y mantener lectores legacy existentes; no sobrescribir overrides ni hacer backfills globales para ocultar el fallo. Las migraciones aplicadas remotamente requieren su propio plan de rollback probado antes de JIT.

## Conformidad, ejecución local y aprobaciones

### Actualización: conformidad del cliente — 2026-10-01

El usuario comunicó conformidad explícita del cliente con este plan y confirmó
que no hace falta un contrato nuevo. La atestación sanitizada
[CLIENT_PLAN_ACCEPTED_LOCAL_EXECUTION](../evidencias_cliente/sprint_1/atestado_aceptacion_plan_ingesta_editorial_auditoria_2026-10-01.md)
vincula la aceptación con `SRC-REQ-002`/`ADENDA-REQ-EST-001-001` y los criterios
H2-CA2, H2-CA3 y H3-CA4. El gate documental para implementación local queda
resuelto; la autorización se limita a Docker/PG17 hasta GO local. No habilita
ninguna escritura remota, deploy o promoción. Si una decisión de negocio no está
determinada por el plan, el punto se mantiene fail-closed y requiere consulta; no
se inventa semántica.

### Resultado del gate documental — 2026-10-01

Antes de iniciar el cambio funcional se revisaron las atestaciones sanitizadas
versionadas. `H3-EXPANDED-PROMPT-2026-08-30` autoriza ejecución local Docker
para su alcance H3 y excluye acciones remotas, pero no atesta específicamente
reglas nuevas para valores inconsistentes presentes, productor/evidencia de
disponibilidad ni consulta visual de historial editorial por Admin. La
`ADENDA-REQ-EST-001-001` acredita CA2/CA3/CA4 en términos de calidad por faltantes,
edición manual y publicación; no define esos criterios ampliados. La evidencia
actual no permite afirmar que el nuevo alcance se validó contra la fuente privada
cliente.

En ese momento, por la regla documental del proyecto, este gap detenía código,
DB, UI y pipeline del nuevo alcance (`NO-GO_DOCUMENTARY_SCOPE_GATE`). El gate fue
resuelto para ejecución local por la aceptación humana posterior registrada
arriba; la lectura histórica se conserva. No se abrió ni versionó la fuente
privada y no se consumió ninguna aprobación remota.

La atestación sanitizada registra la conformidad con el plan, pero no agrega
umbrales contractuales ni semántica que no estuviera definida. El candidato local
se limita a estas decisiones explícitas:

1. Overlay humano en `course_editorial_state`; no se cambia ownership ni se
   escribe directamente en `courses` desde el editor.
2. Faltantes se muestran por `missing_fields`; diferencias manuales vs pipeline
   se hacen visibles, pero no se infiere contradicción semántica ni se amplía el
   permiso de `user`.
3. Una verificación Admin exige URL HTTPS del host del curso, instante observado,
   vencimiento explícito y motivo. Al vencer, el estado efectivo vuelve al cálculo
   del pipeline. No hay TTL por institución configurado; el Admin aporta la fecha.
4. Historial paginado Admin/MFA muestra actor, acción, motivo y diferencias; el
   browser no recibe SELECT directo a `course_editorial_audit` ni la vista pública
   expone identidad.
5. El reader local mantiene compatibilidad legacy; solo una declaración vigente
   `unavailable` la retira. La ruta estática del curso nuevo queda pendiente de
   comprobar con datos elegibles y build autorizado; no se infiere desde el smoke
   de la fixture legacy.

### Resultado de implementación y validación local — 2026-10-01

El gate documental quedó resuelto por la conformidad humana sanitizada indicada
arriba. La implementación local y sus resultados están registrados en
[Evidencia del ciclo local](../evidencia/h3_course_editorial_local_cycle_2026-10-01.md):
PG17 `h3_pg17_harness_ok`, 122 tests Python, TypeScript, lint sin errores,
static smoke, credential scan y `git diff --check` PASS.

El cierre del ciclo sigue `NO-GO` hasta completar UAT visual/autenticada del panel
Admin con MFA y verificar una ruta estática generada para un curso nuevo elegible.
La decisión de este ciclo es no requerir clasificación automática: faltantes y
diferencias pipeline/override quedan sujetos a revisión Admin. La ruta
fixture legacy sí pasó el smoke estático. No se ejecutaron Free/Preview,
DDL/DML/writers remotos ni promociones. `expand` y compatibilidad se validaron
localmente; `deploy` y `contract` no se ejecutaron. Rollback remoto requiere una
migración compensatoria probada y autorización JIT.

**Estado de salida:** `NO-GO_LOCAL_ACCEPTANCE_GAPS_PENDING`; cierre
global H3REQ1 y estado remoto continúan `NO-GO`. La mejora UX de mostrar identidad
conectada junto a `Admin` es un task independiente y no se mezcla con este cambio.
