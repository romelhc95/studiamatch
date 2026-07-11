---
id: EST-XXX
fecha_recepcion: YYYY-MM-DD
fecha_estimacion: YYYY-MM-DD
estado: pendiente_revision
solicitante: Romel
cliente: Cliente
sprint: Sprint X
documento_cliente: requerimientos/YYYYMMDD/[archivo]
cotizacion_docx: requerimientos/YYYYMMDD/[cotizacion].docx
total_cerrado_pen: 0
adelanto_pen: 0
tags: []
---

# EST-XXX — Estimacion [Sprint/Hito] StudIAMatch

**Fecha de recepcion:** [dia DD/MM/YYYY]
**Fecha de estimacion:** [dia DD/MM/YYYY]
**Estado:** Pendiente de revision y aprobacion del cliente
**Documento comercial de salida:** `[ruta DOCX/PDF]`

## 1. Fuentes analizadas y alcance explicito

### Fuentes
- `[ruta requerimiento cliente]` — requerimientos, criterios de aceptacion y alcance.
- `[ruta referencia visual 1]` — referencia visual oficial, si aplica.
- `[ruta referencia visual 2]` — referencia visual oficial, si aplica.
- Base de conocimiento `.context/`: arquitectura vigente, estado tecnico, limitaciones, SDLC y restricciones de seguridad.

### Alcance evaluado
Esta estimacion cubre exclusivamente **[Sprint/Hito/Modulo]** y segmenta los criterios de aceptacion **[CAx-CAy]**. No se estima ni se crea backlog para requerimientos posteriores salvo que se indique explicitamente.

## 2. Supuestos, dependencias y exclusiones

### Supuestos de arquitectura
- Stack objetivo: **Next.js 16, React 19, Tailwind CSS v4, shadcn/base-nova, Supabase PostgreSQL 15 + PostgREST y static export en Cloudflare Pages**.
- El frontend mantiene el patron vigente de acceso a datos salvo aprobacion explicita.
- Los cambios de DB se versionan como migraciones y se validan primero en Supabase Free/Certificacion.
- Ninguna secret key se expone en frontend, commits o documentos.

### Exclusiones explicitas
- [Exclusion 1]
- [Exclusion 2]
- [Exclusion 3]

## 3. Matriz estricta de precio cerrado aplicada

| Complejidad | Alcance tecnico practico | Coste cerrado | Plazo de entrega |
|---|---|---:|---|
| Baja | Capa visual, textos, estilos Tailwind CSS o filtros simples sin alterar DB | S/. 150 - S/. 250 | Lunes inmediato 9:00 a.m. |
| Media | Conexion Frontend-Backend, columnas en Supabase, APIs externas estandar | S/. 250 - S/. 500 | Lunes inmediato 9:00 a.m. |
| Alta | Funcionalidades complejas desde cero, cambios en harvester, seguridad RLS, pgvector | S/. 500 - S/. 700 | 15 dias calendario; despliegue el lunes posterior a las 9:00 a.m. |
| Macro-proyecto | Modulos completos o masivos que superan 15 dias | Cotizar por hitos | Hitos independientes y secuenciales; cada hito respeta el plazo de su complejidad |

**Clasificacion global:** [Baja/Media/Alta/Macro-proyecto por hitos].

## 4. Segmentacion por paquetes cerrados alineados a CAs

### Paquete 1 — [Nombre]
**CAs cubiertos:** [CAx]
**Complejidad:** [Baja/Media/Alta]
**Importe cerrado:** S/. [monto]

**Alcance funcional:**
- [Entregable funcional 1]
- [Entregable funcional 2]

**Impacto tecnico:**
- **Frontend:** [rutas/componentes]
- **Supabase/PostgREST/RLS:** [tablas/RPC/politicas]
- **Pipeline/workflows:** [scripts/workflows]

## 5. Mapeo CA/requerimiento a arquitectura afectada

| CA | Requerimiento | Frontend/rutas/componentes | Supabase/PostgREST/RLS | Pipeline/workflows |
|---|---|---|---|---|
| CAx | [Descripcion] | [Impacto] | [Impacto] | [Impacto] |

## 6. Valoracion comercial cerrada

| Paquete | CAs | Clasificacion matriz | Precio cerrado |
|---|---|---|---:|
| 1. [Nombre] | [CAx] | [Complejidad] | S/. [monto] |
| **Subtotal** |  |  | **S/. [monto]** |
| **Contingencia** | Incluida en cada paquete; no se adiciona bolsa abierta |  | **S/. 0** |
| **Total cerrado** | [Modelo] |  | **S/. [monto]** |

**Moneda:** Soles peruanos (PEN).
**Modelo:** Pago por entregable bajo precio cerrado.
**Condicion de activacion:** [adelanto/aprobacion requerida].

## 7. Cronograma, hitos y ventanas de desarrollo

| Hito | Paquetes incluidos | Complejidad | Dependencia principal | Ventana de construccion | Despliegue lunes 9:00 a.m. | Saldo contra entrega | Total hito |
|---|---|---|---|---|---|---:|---:|
| Activacion | [Alcance] | [Tipo] | Aprobacion formal | [fecha] | No aplica | No aplica | **S/. [adelanto]** |
| Hito 1 | Paquete 1 | [Complejidad] | Inicio | [fecha inicio] al [fecha fin] | [fecha despliegue] | S/. [saldo] | S/. [total] |

### Dependencias tecnicas entre hitos
1. [Dependencia 1]
2. [Dependencia 2]

## 8. Riesgos arquitectonicos y mitigaciones

1. **[Riesgo].**
   *Mitigacion:* [accion].

## 9. Criterios de aceptacion tecnicos

- [ ] CAx: [criterio verificable]
- [ ] La implementacion mantiene compatibilidad con el stack vigente.
- [ ] No se exponen credenciales.
- [ ] Se registra changelog y se pasa revision de seguridad antes de PR.

## 10. Resumen ejecutivo de despliegues y pagos

| Concepto | Fecha / ventana | Monto |
|---|---|---:|
| Activacion | [fecha] | **S/. [monto]** |
| Saldo hito 1 | [fecha] | S/. [monto] |
| **Total cerrado** | [cierre estimado] | **S/. [monto]** |

## 11. Control de restricciones cumplidas

- [ ] Se analizo solo el alcance solicitado.
- [ ] Se aplico la matriz estricta de precio cerrado.
- [ ] Se calcularon fechas con calendario real.
- [ ] No se crearon tareas antes de aprobacion.
- [ ] El documento comercial final replica esta estructura.

## 12. Aprobacion

- [ ] Pendiente
- [ ] Aprobado — Fecha: ____ — Documento aprobado: ____
- [ ] Rechazado — Razon: ____
