# Atestación sanitizada — corrección del contrato editorial CA4

Estado: `HUMAN_SCOPE_ATTESTED_LOCAL_IMPLEMENTATION`

| Campo | Valor |
|---|---|
| ID | `H3-CA4-EDITORIAL-CONTRACT-2026-10-28` |
| Criterio vinculado | `H3-CA4`, en especial CA4.2 (ownership), CA4.5 (mutaciones), CA4.6 (auditoría) y CA4.11 (UAT) |
| Fuente de decisión | Prompt humano `CONTINUA — H3REQ1: corrección del contrato editorial según evaluación manual del responsable`, 2026-10-28 |
| Decisión | Membresía editorial activa puede corregir y volver a corregir los 13 campos de la allowlist. El rol User conserva límites administrativos. Los cambios guardados son borrador; solo Admin puede publicar. El último snapshot editorial publicado prevalece sobre el harvester y la disponibilidad hasta nueva publicación, reversión explícita o desactivación del curso. |
| Disponibilidad y vigencia | La expiración de evidencia puede devolver inscripción a `unknown`; no revierte contenido publicado ni desactiva el curso. FG3 desactiva únicamente tras respuestas 404/410 repetidas separadas por la gracia vigente de tres días. Una fecha antigua, una respuesta transitoria o la expiración de evidencia no bastan. |
| Límite de origen | HTTP 200 no demuestra que el curso siga perteneciendo al catálogo institucional. La retirada semántica de páginas que siguen respondiendo 200 queda trazada a H1 si los mecanismos actuales no pueden verificarla sin un crawler nuevo. |
| Preview e historial | El editor distingue borrador local y contenido publicado; el historial de auditoría queda plegado inicialmente y la versión se muestra compacta, manteniendo control optimista y carga/paginación existentes. |
| Alcance autorizado | Implementación y validación local con Docker y fixtures sintéticos. La instrucción humana posterior `CONTINUA DESDE EL ESTADO ACTUAL — H3REQ1` del 2026-10-28 autoriza commit, push no forzado a esta rama feature y PR hacia `desarrollo` únicamente después de superar los gates y completar el paquete revisable. |
| Exclusiones | Aprobación de review, merge, aplicación remota de migraciones/escrituras Supabase, cuentas/datos reales, writers/schedules/FG3 remoto, deploy manual y promoción. El efecto automático habitual de Preview/CI al crear PR está aceptado; no autoriza otros automatismos, migraciones ni pruebas de negocio remotas. |
| Fuente privada | No se accedió, copió ni modificó. Esta atestación registra únicamente la decisión humana sanitizada del ciclo. |
| Sanitización | Sin identidades, correo, PII, secretos, tokens, evidencia de cursos reales ni contenido privado del cliente. |

La decisión actualiza para este alcance el contrato anterior que limitaba al rol
`user` a `missing_fields`. No concede edición de identidad, institución, URL, slug,
campos internos, cálculos o metadatos; tampoco concede publicación, membresías,
calidad u otras acciones administrativas. Los resultados anteriores permanecen
históricos y no se reinterpretan como pruebas del contrato nuevo.

### Estado al corte inicial de implementación local — 2026-10-28

La autorización descrita en este corte cubría el paquete de esa rama feature. El texto conserva la decisión original y no se extiende a otras operaciones.

### Resultado posterior de implementación y aceptación — 2026-10-28

El paquete se integró mediante PR #509. E1–E6 locales quedaron aceptados; R1–R4 remotos quedaron aceptados en Development (4/4), y el valor público original se restauró y republicó. El resultado y sus límites están en [checkpoint canónico](../../evidencia/h3req1_editorial_contract_2026-10-28.md). Esta actualización es trazabilidad del resultado, no autorización para promover a Certification, cambiar configuración, aplicar SQL, abrir/mergear un nuevo PR ni hacer deploy. La disposición documental asociada a #509 vence antes de Certification y no se reutiliza.
