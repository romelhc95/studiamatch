---
id: TAREA-003
fase: 3
estado: pendiente
prioridad: critica
estimacion_ref: est_001
hito: Hito 3
paquete: Paquete 3 - Panel /admin para cola de pendientes y curacion manual
cas: "CA4"
fecha_inicio: 2026-08-18
fecha_limite: 2026-09-01
despliegue: "2026-09-07 09:00 PET"
responsable: IA implementadora
revisor: security-auditor
aprobador: Usuario/PM
skill_principal: frontend-architect
subespecialidad: Frontend Next.js 16 admin + Supabase RLS/RPC
skills_apoyo: "supabase-architect, security-auditor, accessibility, qa-test-engineer"
gate_obligatorio: security-auditor
entregable: "PR a desarrollo con /admin seguro para listar, editar y publicar pendientes"
creado: 2026-07-11
tags: []
---

# Tarea 003: Hito 3 - Panel admin para cola de pendientes y curacion manual

## Contexto
Estimacion de referencia: [[../estimaciones/est_001]]

- **Hito:** Hito 3
- **Paquete:** Paquete 3 - Panel /admin para cola de pendientes y curacion manual
- **CAs cubiertos:** CA4
- **Responsable de ejecucion:** IA implementadora
- **Revisor obligatorio:** security-auditor
- **Aprobador:** Usuario/PM
- **Entregable:** PR a desarrollo con /admin seguro para listar, editar y publicar pendientes

## Skills y sub-especialidad
- **Skill principal:** frontend-architect
- **Sub-especialidad tecnica:** Frontend Next.js 16 admin + Supabase RLS/RPC
- **Skills de apoyo:** supabase-architect, security-auditor, accessibility, qa-test-engineer
- **Gate obligatorio:** security-auditor

## Plazos
- **Inicio comprometido:** 2026-08-18
- **Fecha limite de construccion:** 2026-09-01
- **Despliegue objetivo:** 2026-09-07 09:00 PET

## Dependencias
- TAREA-002 desplegada o aprobada internamente

## Fuentes del requerimiento
- Documento fuente: `requerimientos/30062026/Studiamatch_MVP_Requerimientos_v5.pdf`.
- Seccion 8.2: ingreso manual en `/admin`, cola de pendientes, edicion inline, nota libre, sources manuales y timestamps.
- Seccion 8.3: campos de schema que admin debe editar/actualizar.
- Seccion 10: CA4.

## Matriz CA -> detalle implementable
| CA | Detalle exacto del requerimiento | Implicancia tecnica | Fuera de alcance |
|---|---|---|---|
| CA4 | `/admin` con cola de pendientes + formulario de edicion manual para completar datos vacios y publicarlos. | Listar cursos `pendiente`, editar datos criticos visibles, marcar source `manual`, actualizar timestamp y publicar solo si cumple reglas. | Auth empresarial completa, borrado masivo, CRM/email/webhook. |
| Seccion 8.2 | Cola ordenada por campos faltantes y edicion inline con nota libre. | UI admin debe priorizar `missing_fields` y permitir nota/curacion manual si existe campo destino o se define en TAREA-001. | Redisenar Home/Resultados. |

## Alcance incluido
- Crear ruta `/admin` compatible con static export para revisar cola de programas pendientes.
- Listar programas pendientes/incompletos usando campos definidos por TAREA-001 y poblados por TAREA-002.
- Permitir edicion inline de precio, duracion, modalidad, fecha, area y campos faltantes.
- Guardar cambios como fuente manual con timestamp actualizado.
- Publicar solo cuando el registro cumpla criterios minimos bajo mecanismo RLS/RPC seguro.

## Alcance excluido
- No implementar autenticacion empresarial completa salvo decision tecnica aprobada.
- No exponer secret key en browser.
- No implementar CRM, email/webhook o entrega real-time de leads.
- No redisenar Home/Resultados fuera de lo minimo requerido para `/admin`.
- No permitir edicion masiva destructiva ni borrado de cursos.

## Criterios de Aceptacion
- [ ] /admin lista programas pendientes
- [ ] Formulario inline permite editar precio, duracion, modalidad, fecha, area y campos faltantes
- [ ] Al guardar se marca fuente manual y timestamp actualizado
- [ ] Publicar solo es posible cuando el registro cumple criterios minimos bajo RLS/RPC segura
- [ ] La UI no contiene ni requiere secret keys o service role keys.
- [ ] Las operaciones admin quedan encapsuladas en RPC/RLS o mecanismo equivalente aprobado.
- [ ] La pantalla es usable en desktop y mobile para revision basica.

## Matriz CA -> pruebas/evidencia
| CA | Prueba obligatoria | Tipo | Metodo / comando | Resultado esperado | Evidencia requerida |
|---|---|---|---|---|---|
| CA4 | `/admin` lista solo pendientes/incompletos. | Frontend + DB | Query/fetch revisado + captura o salida de prueba. | Cola muestra registros con estado pendiente segun TAREA-001/002. | Captura/descripción + query/fetch. |
| CA4 | Edicion inline actualiza campos permitidos. | Frontend/RPC | Caso manual o test con precio/duracion/modalidad/fecha/area. | Campos se guardan y errores se muestran si formato invalido. | Caso antes/despues. |
| CA4 | Guardado marca fuente manual y timestamp. | DB/RLS | Query posterior al guardado o prueba RPC. | `field_sources.<campo>='manual'` y `manual_updated_at` actualizado. | Query/evidencia. |
| CA4 | Publicar bloquea incompletos. | Frontend/RPC | Intento de publicar con faltantes. | No cambia a publicado y muestra faltantes. | Caso bloqueado documentado. |
| CA4 | Seguridad admin sin secrets. | Security | Diff + `security-auditor`. | No hay secret key en browser; escritura protegida por RPC/RLS/mecanismo aprobado. | Reporte security-auditor. |

## Analisis tecnico previo obligatorio
- [ ] Revisar `requerimientos/30062026/Studiamatch_MVP_Requerimientos_v5.pdf` secciones 8.2, 8.3 y CA4 antes de tocar codigo.
- [ ] Revisar la salida aprobada de TAREA-001: nombres finales de `publication_status`, `data_quality_status`, `missing_fields`, `field_sources`, `manual_updated_at` y campos sponsorship/leads.
- [ ] Revisar la salida aprobada de TAREA-002: reglas reales para pendiente/completo y valores permitidos de `missing_fields`/`field_sources`.
- [ ] Revisar `.context/sistema_db_supabase.md` y policies reales de `courses`/`leads` para no exponer PII ni abrir `UPDATE` anon.
- [ ] Revisar `web/src/app/courses/[institution]/[slug]/CourseDetailClient.tsx` solo como referencia de patrones de fetch/formularios; no modificar detalle de curso salvo aprobacion explicita.
- [ ] Decidir mecanismo admin compatible con static export antes de disenar UI: RPC SECURITY DEFINER, RLS para rol autenticado o flujo aprobado equivalente.
- [ ] Confirmar si Sprint 1 usara auth real para `/admin`; si no esta aprobado, documentar alternativa segura minima antes de implementar escritura.

## Especificacion exacta del cambio

### Ruta y componentes esperados
| Elemento | Cambio exacto esperado |
|---|---|
| `web/src/app/admin/page.tsx` | Nueva ruta `/admin` con shell estatico y componente cliente para cola de pendientes. No debe contener secrets ni service role key. |
| `web/src/app/admin/AdminPendingQueueClient.tsx` o equivalente | Componente cliente para listar pendientes, editar campos criticos, guardar manualmente y publicar. |
| `web/src/app/admin/components/*` si se extrae | Componentes simples para tabla, editor inline, badges de faltantes y acciones. Evitar abstracciones prematuras. |

### Datos editables minimos
| Campo UI | Campo destino esperado | Regla |
|---|---|---|
| Precio | `courses.price_pen` o campo equivalente vigente | Permitir `NULL`/A consultar; si se completa manualmente, `field_sources.price='manual'`. |
| Duracion | `courses.duration` | Requerido para publicar como completo; source manual si se edita. |
| Modalidad | `courses.mode` | Valores controlados segun contrato vigente (`Presencial`, `Remoto`, `Hibrido` o equivalentes reales). |
| Fecha | `courses.start_date`/`courses.start_date_text` | Reutilizar campos existentes; no crear campo nuevo en este hito. |
| Area | `courses.category_id`/`courses.category` | Usar catalogo/campo vigente; no crear taxonomia nueva. |
| Nota libre | Campo aprobado en TAREA-001/TAREA-003 si existe | Si no hay campo destino aprobado, documentar fuera de alcance o agregarlo via migracion segura. |

### Operaciones admin esperadas
| Operacion | Contrato esperado |
|---|---|
| Listar pendientes | Filtrar por `publication_status='pendiente_revision'` o `data_quality_status='pendiente'` segun nombres finales de TAREA-001. No incluir PII de leads. |
| Guardar manual | Actualizar solo campos permitidos, mergear `field_sources` a `manual`, actualizar `manual_updated_at` y recalcular `missing_fields` si corresponde. |
| Publicar | Permitir solo si cumple criterios minimos de TAREA-002; setear `publication_status='publicado'` o valor final aprobado. |
| Bloquear publicacion | Si faltan campos criticos, mostrar faltantes y no modificar estado a publicado. |

### Seguridad/RLS/RPC
- No usar `NEXT_SUPABASE_SECRET_KEY` ni service role en browser.
- No abrir `UPDATE` anon en `courses`.
- Si se usa RPC, definir firma minima, validar campos permitidos en SQL y revocar ejecucion a `public` si no corresponde.
- Mantener lectura publica de `courses` condicionada por policies existentes; `/admin` puede requerir auth o mecanismo aprobado.

## Subtareas tecnicas
- [ ] **ST-01 — Definir mecanismo seguro de acceso admin**
  - Analisis previo: revisar static export, RLS vigente, disponibilidad de Auth/RPC y restricciones de no exponer secrets.
  - Objetivo: decidir si se usara RPC con RLS, policy temporal o mecanismo aprobado compatible con static export.
  - Cambio exacto: documentar el mecanismo elegido y, si requiere SQL, especificar RPC/policy/grants antes de crear UI de escritura.
  - Archivos esperados: `db/migrations/`, `web/src/app/admin/page.tsx` si aplica.
  - CAs relacionados: CA4.
  - Validacion: revision `security-auditor` antes de implementar UI de escritura.
- [ ] **ST-02 — Crear shell de ruta `/admin`**
  - Analisis previo: revisar App Router actual y static export para evitar dependencias server-side incompatibles.
  - Objetivo: agregar pagina admin sin romper static export ni rutas publicas.
  - Cambio exacto: crear `web/src/app/admin/page.tsx` con shell y delegar interactividad a componente cliente.
  - Archivos esperados: `web/src/app/admin/page.tsx`.
  - CAs relacionados: CA4.
  - Validacion: `npm run lint` y `npx tsc --noEmit`.
- [ ] **ST-03 — Implementar consulta de pendientes**
  - Analisis previo: confirmar nombres finales de estados/faltantes desde TAREA-001/TAREA-002 y policies de lectura.
  - Objetivo: cargar cursos con estado pendiente/incompleto y mostrar campos faltantes.
  - Cambio exacto: consultar solo campos necesarios de `courses` y joins publicos seguros; no consultar `leads` ni PII.
  - Archivos esperados: `web/src/app/admin/**`.
  - CAs relacionados: CA4.
  - Validacion: evidencia de query sin PII ni datos privados.
- [ ] **ST-04 — Implementar tabla/formulario inline**
  - Analisis previo: mapear cada campo editable a campo DB vigente y validacion UI.
  - Objetivo: editar precio, duracion, modalidad, fecha, area y faltantes desde la cola.
  - Cambio exacto: implementar controles editables con estado local, validacion de formato y mensajes de error por fila.
  - Archivos esperados: componentes admin en `web/src/app/admin/` o `web/src/components/`.
  - CAs relacionados: CA4.
  - Validacion: revision responsive y manejo de errores.
- [ ] **ST-05 — Implementar guardado manual seguro**
  - Analisis previo: revisar contrato de RPC/policy elegido y campos permitidos.
  - Objetivo: persistir cambios marcando fuente manual y timestamp.
  - Cambio exacto: guardar solo campos whitelist, actualizar `field_sources`/`manual_updated_at` y recalcular faltantes sin exponer secrets.
  - Archivos esperados: `db/migrations/` para RPC/RLS si aplica, componentes admin.
  - CAs relacionados: CA4.
  - Validacion: no hay secret key en frontend; security review.
- [ ] **ST-06 — Implementar accion Publicar**
  - Analisis previo: revisar criterios minimos aprobados por TAREA-002.
  - Objetivo: permitir publicar solo cuando cumple minimos y bloquear caso incompleto.
  - Cambio exacto: validar faltantes antes de cambiar estado; mostrar faltantes bloqueantes si no cumple.
  - Archivos esperados: componentes admin, RPC/RLS si aplica.
  - CAs relacionados: CA4.
  - Validacion: caso bloqueado y caso exitoso documentados.
- [ ] **ST-07 — Validar accesibilidad y UX basica**
  - Analisis previo: revisar tabla/formularios generados y flujos de teclado.
  - Objetivo: asegurar formularios con labels, focus visible, mensajes de error y uso mobile razonable.
  - Cambio exacto: agregar labels, estados `aria-*` donde aplique, focus visible y layout mobile legible.
  - Archivos esperados: componentes admin.
  - CAs relacionados: CA4.
  - Validacion: checklist `accessibility`.

## Archivos afectados
| Archivo | Tipo de cambio |
|---|---|
| `web/src/app/admin/page.tsx` | Nueva ruta admin compatible con static export |
| `web/src/app/admin/` | Nuevos componentes cliente para cola, edicion y publicacion |
| `db/migrations/` | RPC/RLS/vistas seguras para operaciones admin si aplica |

## Plan de ejecucion
1. Leer EST-001, salida de TAREA-001/TAREA-002 y esta tarea antes de tocar codigo.
2. Resolver mecanismo seguro de admin antes de construir formularios.
3. Implementar shell, listado, edicion, guardado y publicacion en orden.
4. Validar frontend y cualquier SQL/RLS dentro del alcance.
5. Invocar accessibility y security review antes de commit/PR.
6. Registrar resultado en changelog y en esta tarea.

## Validaciones requeridas
- [ ] `docker exec studiamatch-dev bash -lc "cd /app/web && npm run lint"` si toca frontend.
- [ ] `docker exec studiamatch-dev bash -lc "cd /app/web && npx tsc --noEmit"` si toca frontend.
- [ ] Revision RLS/RPC si toca Supabase.
- [ ] Checklist accessibility para formularios y tabla.
- [ ] Ejecucion de matriz `CA -> pruebas/evidencia`.
- [ ] Revision `security-auditor` antes de commit/PR.

## Evidencia requerida
- [ ] Captura o descripcion de cola de pendientes.
- [ ] Caso de guardado manual con fuente/timestamp.
- [ ] Caso de publicacion bloqueada por faltantes.
- [ ] Caso de publicacion exitosa.
- [ ] Salida de lint/typecheck y security review.

## Checklist de cierre
- [ ] CA4 cubierto completo.
- [ ] `/admin` no expone secrets.
- [ ] Edicion manual actualiza fuente y timestamp.
- [ ] Publicar valida calidad minima.
- [ ] Changelog actualizado.

## Notas de implementacion
<!-- Detalles tecnicos aqui -->

## Resultado
<!-- Actualizado por la IA al completar: Fecha, commits, PR -->
