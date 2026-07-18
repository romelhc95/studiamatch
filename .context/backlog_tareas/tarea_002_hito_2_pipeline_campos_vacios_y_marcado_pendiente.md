---
id: TAREA-002
fase: 2
estado: pendiente
prioridad: critica
estimacion_ref: est_001
hito: Hito 2
paquete: Paquete 2 - Pipeline deteccion de campos vacios y marcado pendiente
cas: "CA3, CA2 parcial"
fecha_inicio: 2026-07-28
fecha_limite: 2026-08-11
despliegue: "2026-08-17 09:00 PET"
responsable: IA implementadora
revisor: security-auditor
aprobador: Usuario/PM
skill_principal: pipeline-engineer
subespecialidad: Pipeline Python ETL + Supabase PostgREST
skills_apoyo: "supabase-architect, security-auditor, data-quality-analyst, qa-test-engineer"
gate_obligatorio: security-auditor
entregable: "PR a desarrollo con pipeline tolerante a campos vacios y estado pendiente/completo"
creado: 2026-07-11
tags: []
---

# Tarea 002: Hito 2 - Pipeline campos vacios y marcado pendiente

## Contexto
Estimacion de referencia: [[../estimaciones/est_001]]

- **Hito:** Hito 2
- **Paquete:** Paquete 2 - Pipeline deteccion de campos vacios y marcado pendiente
- **CAs cubiertos:** CA3, CA2 parcial
- **Responsable de ejecucion:** IA implementadora
- **Revisor obligatorio:** security-auditor
- **Aprobador:** Usuario/PM
- **Entregable:** PR a desarrollo con pipeline tolerante a campos vacios y estado pendiente/completo

## Skills y sub-especialidad
- **Skill principal:** pipeline-engineer
- **Sub-especialidad tecnica:** Pipeline Python ETL + Supabase PostgREST
- **Skills de apoyo:** supabase-architect, security-auditor, data-quality-analyst, qa-test-engineer
- **Gate obligatorio:** security-auditor

## Plazos
- **Inicio comprometido:** 2026-07-28
- **Fecha limite de construccion:** 2026-08-11
- **Despliegue objetivo:** 2026-08-17 09:00 PET

## Dependencias
- TAREA-001 desplegada o aprobada internamente

## Fuentes del requerimiento
- Documento fuente: `requerimientos/30062026/Studiamatch_MVP_Requerimientos_v5.pdf`.
- Seccion 5: `Datos criticos visibles en el frontend` define los datos que bloquean lanzamiento.
- Seccion 6: `Logica de cards y botones` define los 3 estados de disponibilidad y CTA asociado.
- Seccion 8.1: `Flujo A — Scraping automatico` define que precio, duracion, modalidad, fecha de inicio y area vacios no deben romper el proceso y deben marcar `pendiente`/`campos_faltantes`.
- CA2: cambios schema para `status`, source, updated_at, fecha, tabla leads y flag de datos criticos incompletos.
- CA3: deteccion de campos vacios en harvester + marca `pendiente`.

## Matriz CA -> detalle implementable
| CA | Detalle exacto del requerimiento | Implicancia tecnica | Fuera de alcance |
|---|---|---|---|
| CA2 parcial | Schema soporta `status`, sources, timestamps, fecha y flag/datos criticos incompletos. | Consumir campos definidos por TAREA-001: estado editorial/calidad, faltantes, fuentes y timestamps. | Crear panel admin o UI publica. |
| CA3 | Si faltan precio, duracion, modalidad, fecha de inicio o area, el pipeline no falla; guarda lo encontrado y marca `pendiente`. | Workers deben normalizar vacios, llenar `missing_fields`, conservar parciales y no publicar como completo. | Scraping de logos, entrega real-time de leads, embeddings. |
| Seccion 5 alta | Datos criticos visibles: nombre, institucion/logo fallback, modalidad, duracion, precio/A consultar, area, pais/ciudad, disponibilidad. | Matriz de calidad minima debe basarse en estos datos del PDF v5, no en criterios internos legacy. | ROI y reseñas quedan baja prioridad/fases posteriores. |
| Seccion 5 media | Fecha de ultima actualizacion y enlace al sitio de la institucion. | Pipeline debe preservar timestamps/fuentes y URL institucional/origen disponible. | Metodologia publica de ROI. |
| Seccion 6 | Disponibilidad tiene 3 estados: inscripciones abiertas, fecha proxima confirmada, sin fecha confirmada. | Sync debe derivar estado de disponibilidad desde fecha/campos disponibles para que cards puedan mostrar badge/CTA. | UI de cards se implementa en Hito 5. |

## Alcance incluido
- Hacer que el pipeline preserve datos parciales cuando falten datos criticos definidos por el PDF v5, especialmente precio, duracion, modalidad, fecha de inicio, area y pais/ciudad.
- Registrar campos faltantes usando el contrato definido en TAREA-001.
- Marcar registros como pendientes o completos segun calidad minima.
- Mantener continuidad de corrida sin fallar por nulos, strings vacios o valores LLM invalidos.
- Alinear la matriz de calidad a los datos criticos visibles del frontend definidos por el PDF v5, no a criterios internos legacy del enriquecimiento LLM.

## Alcance excluido
- No crear `/admin`; corresponde a TAREA-003.
- No cambiar el diseno publico de Home o Resultados.
- No implementar busqueda semantica ni embeddings reales.
- No sincronizar datos operativos entre ambientes.
- No relajar gates `pipeline_ready` ni circuit breakers.

## Criterios de Aceptacion
- [ ] El scraping/enriquecimiento no falla si faltan precio, duracion, modalidad, fecha o area
- [ ] Los campos encontrados se guardan y los vacios quedan registrados como campos faltantes o equivalente
- [ ] El registro queda pendiente o completo segun calidad minima y queda disponible para curacion admin
- [ ] Los valores `None`, `"None"`, `"null"`, strings vacios y formatos invalidos se normalizan antes del sync final.
- [ ] Los cursos incompletos no quedan publicados como completos por error.
- [ ] La corrida continua aunque un registro individual sea incompleto o invalido.
- [ ] La calidad minima se evalua contra los datos criticos visibles del PDF v5: nombre, institucion, modalidad, duracion, precio/A consultar, area, pais/ciudad y disponibilidad.
- [ ] ROI y reseñas no forman parte del criterio de completitud de Sprint 1.

## Matriz CA -> pruebas/evidencia
| CA | Prueba obligatoria | Tipo | Metodo / comando | Resultado esperado | Evidencia requerida |
|---|---|---|---|---|---|
| CA3 | Caso con precio faltante no rompe pipeline. | Pipeline smoke | Ejecutar caso controlado o documentar input/salida esperada si no hay fixture. | Registro preserva datos encontrados, `missing_fields` incluye `price`, precio queda `A consultar`/NULL. | Matriz de caso incompleto + salida esperada/real. |
| CA3 | Caso con duracion/modalidad/fecha/area faltante marca pendiente. | Pipeline smoke | Caso controlado por campo critico. | `data_quality_status='pendiente'` y `publication_status` no queda publicado automaticamente. | Evidencia por campo critico. |
| CA2 parcial | Sync final escribe `missing_fields` y `field_sources`. | DB integration | Query posterior o prueba aislada de mapping. | JSONB array/object validos y fuentes `scraped/llm/derived/missing/manual` segun contrato. | Query o fixture esperado. |
| Seccion 5/6 | Disponibilidad se deriva en tres estados. | Data-quality | Casos con fecha presente, fecha textual y sin fecha. | abierto/proxima/sin fecha segun regla documentada. | Tabla de casos y resultado. |
| Seguridad | No se relajan gates/RLS ni se escriben secretos. | Security | `security-auditor` + diff. | 0 hallazgos bloqueantes o estado observado con subtareas refinadas. | Reporte security-auditor. |

## Analisis tecnico previo obligatorio
- [ ] Revisar PDF v5 secciones 5, 6, 8.1 y CA2/CA3 antes de modificar workers.
- [ ] Revisar salida de TAREA-001 para confirmar nombres exactos de `publication_status`, `data_quality_status`, `missing_fields`, `field_sources`, timestamps y campos de disponibilidad.
- [ ] Revisar `scripts/core/universal_harvester.py`, `cleansing_worker.py`, `enrichment_worker.py`, `sync_vector_worker.py` y `master_orchestrator.py` para ubicar donde se extraen, normalizan o descartan datos criticos.
- [ ] Revisar mapeo actual de `courses`: `name`, `institution_id`, `mode`, `duration`, `price_pen`, `category_id/category`, `region/address`, `start_date/start_date_text`, `url`, `updated_at`.
- [ ] Confirmar que ningun worker use criterios internos legacy del enriquecimiento LLM como criterio de completitud de Sprint 1; si lo usa, sustituir por matriz de datos criticos visibles.

## Especificacion exacta del cambio

### Datos criticos visibles que gobiernan CA3
| Dato requerido PDF v5 | Tabla/campo destino esperado | Regla de completitud | Valor fallback permitido |
|---|---|---|---|
| Nombre del programa | `courses.name` desde `official_name`/nombre limpio | Obligatorio para `data_quality_status='completo'`. | No permitido; si falta, descartar o mantener pendiente no publicable segun regla existente. |
| Institucion | `courses.institution_id` + join `institutions.name` | Obligatorio. | No permitido. |
| Logo institucion | `institutions`/frontend fallback por iniciales | No bloquea pipeline; frontend debe tener fallback. | Iniciales coloreadas. |
| Modalidad | `courses.mode` | Requerido para completo si se infiere de fuente confiable. | `NULL` + `missing_fields` incluye `mode`. |
| Duracion | `courses.duration` | Requerido para completo si existe en HTML/LLM. | `NULL` + `missing_fields` incluye `duration`. |
| Precio | `courses.price_pen` + `price_status` existente si aplica | No bloquea guardado; si falta, UI muestra `A consultar`. | `price_pen=NULL` y/o `price_status='a_consultar'` si existe/queda definido. |
| Area tematica | `courses.category_id`/`courses.category` | Requerida para filtros/resultados. | `NULL` + `missing_fields` incluye `area`. |
| Pais/ciudad | `courses.region`/`courses.address` o equivalente existente | Requerido para filtros si dato disponible. | `NULL` + `missing_fields` incluye `location` si falta. |
| Estado disponibilidad | Derivado de `start_date`/`start_date_text` y estado editorial | Requerido para cards: abierto, fecha proxima, sin fecha. | `sin_fecha_confirmada` si no hay fecha. |
| Fecha ultima actualizacion | `updated_at`, `manual_updated_at` o timestamps por fuente | Prioridad media; no bloquea guardado. | Timestamp automatico del registro si no hay manual. |
| Enlace institucion | `courses.url`/`institutions.official_website` | Prioridad media; conservar si existe. | Link origen del programa. |

### Estados de calidad/publicacion esperados
| Condicion | `data_quality_status` | `publication_status` esperado | Razon |
|---|---|---|---|
| Tiene nombre, institucion, modalidad, duracion, area y disponibilidad; precio puede estar como `A consultar`. | `completo` | No publicar automaticamente salvo regla de Hito 3/admin; mantener segun contrato de TAREA-001. | Cumple datos criticos altos. |
| Falta cualquiera de modalidad, duracion, area, pais/ciudad o fecha/disponibilidad. | `pendiente` | `pendiente_revision` o equivalente definido por TAREA-001. | Requiere curacion admin. |
| Falta nombre o institucion. | `pendiente` o descarte controlado segun worker. | No publicable. | No se puede mostrar card confiable. |

### `missing_fields` esperado
Valores permitidos para Sprint 1: `name`, `institution`, `mode`, `duration`, `price`, `area`, `location`, `availability`, `source_url`, `last_updated`.

### `field_sources` esperado
Objeto JSON por campo critico con valores permitidos: `scraped`, `llm`, `manual`, `derived`, `missing`. Ejemplo: `{"price":"missing","duration":"scraped","mode":"llm","area":"derived"}`.

## Subtareas tecnicas
- [ ] **ST-01 — Definir matriz de datos criticos PDF v5**
  - Analisis previo: leer PDF v5 seccion 5 y separar prioridad alta, media y baja; excluir ROI/resenas del criterio Sprint 1.
  - Objetivo: listar campos requeridos, opcionales y derivables para calidad minima segun el requerimiento aprobado.
  - Cambio exacto: documentar la matriz de `Datos criticos visibles que gobiernan CA3` y usarla como fuente para workers.
  - Archivos esperados: notas en tarea/changelog; uso posterior en codigo.
  - CAs relacionados: CA3, CA2 parcial.
  - Validacion: matriz aprobada contra PDF v5 secciones 5/6/8.1 antes de cambiar workers.
- [ ] **ST-02 — Auditar descartes prematuros en harvester**
  - Analisis previo: ubicar reglas que descartan por precio/duracion/modalidad/fecha/area faltante.
  - Objetivo: detectar si `universal_harvester.py` descarta URLs por datos incompletos recuperables.
  - Cambio exacto: preservar HTML/URL si hay nombre/institucion y evidencia de programa aunque falten otros datos criticos.
  - Archivos esperados: `scripts/core/universal_harvester.py` si aplica.
  - CAs relacionados: CA3.
  - Validacion: `python3 -m py_compile scripts/core/universal_harvester.py` si cambia.
- [ ] **ST-03 — Ajustar cleansing para conservar parciales**
  - Analisis previo: revisar filtros de calidad/noise para distinguir pagina ruido vs programa incompleto recuperable.
  - Objetivo: permitir que registros validos incompletos avancen y registren faltantes detectables.
  - Cambio exacto: generar/propagar faltantes detectables para `mode`, `duration`, `price`, `area`, `location`, `availability` sin descartar el registro si nombre/institucion son validos.
  - Archivos esperados: `scripts/core/cleansing_worker.py`.
  - CAs relacionados: CA3.
  - Validacion: `python3 -m py_compile scripts/core/cleansing_worker.py`.
- [ ] **ST-04 — Normalizar salida LLM en enrichment**
  - Analisis previo: revisar prompt/schema actual de enrichment y mapear su salida a los datos criticos PDF v5, sin usar criterios internos legacy como criterio Sprint 1.
  - Objetivo: convertir nulos/string basura a valores seguros y preservar datos criticos visibles parciales.
  - Cambio exacto: normalizar `official_name`, `duration_text`, `total_cost_est`, `modality`, `primary_campus`, `start_date`, `categories` hacia la matriz de datos criticos; contenido curricular adicional puede conservarse como dato complementario, no como bloqueo.
  - Archivos esperados: `scripts/core/enrichment_worker.py`.
  - CAs relacionados: CA3.
  - Validacion: `python3 -m py_compile scripts/core/enrichment_worker.py`.
- [ ] **ST-05 — Mapear faltantes en sync final**
  - Analisis previo: revisar campos destino de `courses` y contrato SQL de TAREA-001.
  - Objetivo: escribir campos encontrados, `missing_fields`, `field_sources` y estados de calidad/publicacion en `courses`.
  - Cambio exacto: calcular `missing_fields` solo con valores permitidos Sprint 1 y derivar `data_quality_status` desde datos criticos visibles; no usar ROI, resenas ni criterios internos legacy para completitud.
  - Archivos esperados: `scripts/core/sync_vector_worker.py`.
  - CAs relacionados: CA2 parcial, CA3.
  - Validacion: `python3 -m py_compile scripts/core/sync_vector_worker.py`.
- [ ] **ST-06 — Proteger continuidad del orquestador**
  - Analisis previo: revisar manejo de excepciones por registro/lote y como se reportan errores parciales.
  - Objetivo: asegurar que fallas parciales no aborten la corrida completa sin registro.
  - Cambio exacto: registrar error/faltantes por programa y continuar lote cuando la URL sea recuperable.
  - Archivos esperados: `scripts/core/master_orchestrator.py` si aplica.
  - CAs relacionados: CA3.
  - Validacion: `python3 -m py_compile scripts/core/master_orchestrator.py` si cambia.
- [ ] **ST-07 — Preparar casos de prueba/smoke**
  - Analisis previo: construir casos a partir de la seccion 5/6/8.1 del PDF, no desde criterios internos legacy.
  - Objetivo: validar casos con precio faltante, duracion faltante, modalidad faltante, fecha faltante, area faltante y pais/ciudad faltante.
  - Cambio exacto: documentar input esperado y salida esperada para `missing_fields`, `field_sources`, `data_quality_status` y disponibilidad.
  - Archivos esperados: tests existentes o evidencia manual documentada si no hay suite.
  - CAs relacionados: CA3.
  - Validacion: comandos ejecutados o matriz de evidencia.

## Archivos afectados
| Archivo | Tipo de cambio |
|---|---|
| `scripts/core/universal_harvester.py` | Preservar extraccion parcial sin fallar por campos ausentes |
| `scripts/core/cleansing_worker.py` | Registrar faltantes detectables y no descartar registros validos incompletos |
| `scripts/core/enrichment_worker.py` | Normalizar nulos y salida parcial de datos criticos visibles del PDF v5 |
| `scripts/core/sync_vector_worker.py` | Mapear faltantes a estado editorial pendiente/completo |
| `scripts/core/master_orchestrator.py` | Asegurar continuidad de corrida ante parciales |

## Plan de ejecucion
1. Leer PDF v5 secciones 5/6/8.1, EST-001, salida de TAREA-001 y esta tarea antes de tocar codigo.
2. Confirmar nombres exactos de campos agregados por TAREA-001.
3. Ejecutar subtareas desde matriz de datos criticos visibles hasta sync final.
4. Validar cada worker modificado con `py_compile` en Docker.
5. Probar/evidenciar al menos un caso incompleto por campo critico.
6. Invocar revision de seguridad antes de commit/PR.
7. Registrar resultado en changelog y en esta tarea.

## Validaciones requeridas
- [ ] `docker exec studiamatch-dev python3 -m py_compile scripts/core/universal_harvester.py` si cambia.
- [ ] `docker exec studiamatch-dev python3 -m py_compile scripts/core/cleansing_worker.py` si cambia.
- [ ] `docker exec studiamatch-dev python3 -m py_compile scripts/core/enrichment_worker.py` si cambia.
- [ ] `docker exec studiamatch-dev python3 -m py_compile scripts/core/sync_vector_worker.py` si cambia.
- [ ] Smoke/matriz de casos incompletos documentada contra PDF v5 seccion 5/6/8.1.
- [ ] Ejecucion de matriz `CA -> pruebas/evidencia`.
- [ ] Revision `security-auditor` antes de commit/PR.

## Evidencia requerida
- [ ] Matriz de datos criticos visibles del PDF v5 y reglas pendiente/completo.
- [ ] Ejemplos de entradas incompletas y salida esperada.
- [ ] Salida de `py_compile` por worker modificado.
- [ ] Resumen de campos escritos en `courses`.
- [ ] PR a `desarrollo` con alcance limitado a pipeline.

## Checklist de cierre
- [ ] CA3 cubierto para datos criticos altos del PDF v5.
- [ ] Datos parciales se conservan.
- [ ] Faltantes quedan registrados.
- [ ] Registros incompletos quedan disponibles para TAREA-003.
- [ ] No se usan criterios internos legacy como criterio de completitud Sprint 1.
- [ ] No se relajan gates ni RLS.
- [ ] Changelog actualizado.

## Notas de implementacion
<!-- Detalles tecnicos aqui -->

## Resultado
<!-- Actualizado por la IA al completar: Fecha, commits, PR -->
