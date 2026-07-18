---
id: TAREA-004
fase: 4
estado: pendiente
prioridad: alta
estimacion_ref: est_001
hito: Hito 4
paquete: Paquetes 4 y 6 - Home MVP + documentacion tecnica
cas: "CA5, CA6, CA7, CA13 Home"
fecha_inicio: 2026-09-12
fecha_limite: 2026-09-13
despliegue: "2026-09-14 09:00 PET"
responsable: IA implementadora
revisor: security-auditor
aprobador: Usuario/PM
skill_principal: frontend-architect
subespecialidad: Frontend Next.js 16 + UI Home + documentacion tecnica
skills_apoyo: "accessibility, seo, security-auditor, qa-test-engineer"
gate_obligatorio: security-auditor
entregable: "PR a desarrollo con Home segun mockup aprobado y documentacion tecnica Sprint 1"
creado: 2026-07-11
tags: []
---

# Tarea 004: Hito 4 - Home MVP quick wins visuales y documentacion tecnica

## Contexto
Estimacion de referencia: [[../estimaciones/est_001]]

- **Hito:** Hito 4
- **Paquete:** Paquetes 4 y 6 - Home MVP + documentacion tecnica
- **CAs cubiertos:** CA5, CA6, CA7, CA13 Home
- **Responsable de ejecucion:** IA implementadora
- **Revisor obligatorio:** security-auditor
- **Aprobador:** Usuario/PM
- **Entregable:** PR a desarrollo con Home segun mockup aprobado y documentacion tecnica Sprint 1

## Skills y sub-especialidad
- **Skill principal:** frontend-architect
- **Sub-especialidad tecnica:** Frontend Next.js 16 + UI Home + documentacion tecnica
- **Skills de apoyo:** accessibility, seo, security-auditor, qa-test-engineer
- **Gate obligatorio:** security-auditor

## Plazos
- **Inicio comprometido:** 2026-09-12
- **Fecha limite de construccion:** 2026-09-13
- **Despliegue objetivo:** 2026-09-14 09:00 PET

## Dependencias
- TAREA-003 desplegada o aprobada internamente

## Fuentes del requerimiento
- Documento fuente: `requerimientos/30062026/Studiamatch_MVP_Requerimientos_v5.pdf`.
- Mockup fuente: `requerimientos/30062026/studiamatch_home.html`.
- Secciones 3.1, 3.2, 3.3 y 3.4: estructura visual Home, placeholders vs definitivo.
- Seccion 5: datos criticos visibles que deben alimentar cards/secciones.
- Seccion 10: CA5, CA6, CA7, CA13 Home.

## Matriz CA -> detalle implementable
| CA | Detalle exacto del requerimiento | Implicancia tecnica | Fuera de alcance |
|---|---|---|---|
| CA5 | Home: instituciones, patrocinados, abiertos, paises. | Construir secciones con datos Supabase o fallback permitido por PDF. | API real de moneda, scraping de logos. |
| CA6 | Tipografia, cards, `institutos` -> `instituciones`, ocultar ROI. | Aplicar Inter/estilos, revisar copy y ocultar ROI publico. | Metodologia ROI publica. |
| CA7 | README/documentacion tecnica historica y relacion de tablas/campos. | Documentar cambios Sprint 1 y contrato de datos. | Crear documentacion comercial cliente nueva. |
| CA13 Home | Implementar siguiendo mockup Home. | Respetar orden, gradientes, paleta, banner y footer del HTML aprobado. | Cambiar jerarquia visual aprobada. |

## Alcance incluido
- Implementar Home MVP segun `requerimientos/30062026/studiamatch_home.html`.
- Agregar secciones solicitadas: navbar sticky, selector moneda visual, hero, search, pills, stats, instituciones, destacados, inscripciones abiertas, paises, banner y footer.
- Aplicar quick wins visuales: Inter, cards alineadas al mockup, texto `instituciones`, ROI oculto en vistas publicas.
- Documentar tecnicamente tablas/campos, pipeline y criterios operativos modificados durante Sprint 1.

## Alcance excluido
- No implementar API real de tipo de cambio.
- No implementar pagina completa `Como funciona`.
- No migrar detalle SEO a `/programas/[slug]`.
- No implementar sistema real de resenas.
- No modificar reglas de pipeline salvo documentacion de lo ya entregado.

## Criterios de Aceptacion
- [ ] Home implementa navbar sticky, selector moneda visual, hero, search bar, pills, stats, instituciones, destacados, inscripciones abiertas, paises, banner y footer
- [ ] Se aplica Inter, cards alineadas al mockup, texto instituciones y ROI oculto en vistas publicas
- [ ] Documentacion tecnica describe tablas/campos, pipeline y criterios operativos modificados
- [ ] Home respeta la referencia visual aprobada sin introducir secciones fuera de alcance.
- [ ] La pagina carga correctamente en desktop y mobile.
- [ ] El selector de moneda es visual/estatico, no promete conversion real.

## Matriz CA -> pruebas/evidencia
| CA | Prueba obligatoria | Tipo | Metodo / comando | Resultado esperado | Evidencia requerida |
|---|---|---|---|---|---|
| CA5 | Home contiene todas las secciones aprobadas. | Frontend visual | Checklist contra `studiamatch_home.html`. | Navbar, selector moneda, hero, search, pills, stats, instituciones, destacados, abiertos, paises, banner y footer presentes. | Checklist + captura/descripcion. |
| CA6 | Quick wins visuales aplicados. | Frontend visual/textual | Buscar `institutos`, `ROI` visible y revisar tipografia/cards. | Texto `instituciones`, ROI oculto, Inter/cards alineadas. | Salida busqueda + evidencia visual. |
| CA7 | Documentacion tecnica actualizada. | Documental | Revisar changelog/informe/docs internas. | Tablas/campos/pipeline/admin/criterios operativos documentados. | Referencias a archivos/secciones. |
| CA13 Home | Home respeta mockup aprobado. | Visual responsive | Comparacion desktop/mobile con HTML aprobado. | Jerarquia, paleta, CTAs y orden de secciones coinciden o desviaciones justificadas. | Capturas/checklist responsive. |
| Exclusion moneda | Selector no llama API real. | Frontend/code review | Revisar diff/fetches. | No hay llamadas a API tipo cambio ni promesa de conversion real. | Diff/revision documentada. |

## Analisis tecnico previo obligatorio
- [ ] Revisar `requerimientos/30062026/studiamatch_home.html` y extraer orden visual, secciones, copy, paleta y CTAs antes de editar componentes.
- [ ] Revisar `requerimientos/30062026/Studiamatch_MVP_Requerimientos_v5.pdf` secciones 3.1 a 3.4, 5, 10 y CA5/CA6/CA7/CA13 Home.
- [ ] Revisar `web/src/app/page.tsx`, `web/src/app/HomeContent.tsx`, `web/src/components/Header.tsx` y estilos globales para preservar patrones actuales.
- [ ] Confirmar que ROI no se muestra publicamente en Home ni cards usadas por Home.
- [ ] Confirmar que el selector de moneda no llama APIs externas ni promete conversion real en Sprint 1.
- [ ] Definir que datos vendran de Supabase y que placeholders/fallbacks estan permitidos por el PDF antes de construir secciones.
- [ ] Revisar salida de TAREA-001/TAREA-002/TAREA-003 para documentar tablas/campos/pipeline en CA7 sin inventar cambios no implementados.

## Especificacion exacta del cambio

### Secciones Home requeridas
| Seccion | Componente/ruta esperada | Cambio exacto esperado | Fuente |
|---|---|---|---|
| Navbar sticky | `Header` o bloque Home vigente | Header fijo/sticky, copy alineado a mockup, CTA sin texto prohibido. | Mockup Home + CA5/CA13. |
| Selector moneda visual | Header/Home | Control visual/estatico; no API real ni conversion dinamica. | EST-001 exclusion API tipo cambio. |
| Hero + search | `HomeContent` | Gradiente/paleta aprobada, titulo, subtitulo y buscador principal. | Secciones 3.1/3.2. |
| Pills por area | `HomeContent`/componente simple | Pills navegables/filtrables segun datos disponibles o fallback. | CA5. |
| Stats | `HomeContent` | Contadores con datos reales si existen o placeholder permitido. | Mockup Home. |
| Instituciones | `HomeContent` | Usar texto `instituciones`, logos si existen o fallback por iniciales. | CA5/CA6. |
| Programas destacados/patrocinados | Cards Home | Mostrar cards alineadas a mockup; no ranking pagado avanzado. | CA5. |
| Inscripciones abiertas | Cards Home | Usar `start_date`/estado disponible si existe; fallback permitido. | Seccion 5. |
| Explorar por pais | `HomeContent` | Seccion pais/ciudad usando campos disponibles; sin crear datos artificiales. | CA5. |
| Banner proposito + footer | Home/Footer | Copy y jerarquia visual del mockup. | CA13 Home. |

### Datos y placeholders permitidos
- Logos: usar logo real si existe; si falta, iniciales/placeholder visual.
- Precios: si falta precio, mostrar `A consultar` o copy equivalente aprobado; no inventar montos.
- Conteos/stats: preferir datos reales; si no hay campo confiable, placeholder claramente no enganoso.
- ROI: oculto en vistas publicas Sprint 1 salvo aprobacion posterior.

### Documentacion tecnica CA7
- Documentar solo cambios realmente implementados en Sprint 1.
- Incluir tablas/campos agregados por TAREA-001, comportamiento pipeline de TAREA-002, admin de TAREA-003 y decisiones de Home.
- No crear documentacion comercial nueva ni prometer funcionalidades fuera de alcance.

## Subtareas tecnicas
- [ ] **ST-01 — Comparar Home actual contra mockup aprobado**
  - Analisis previo: revisar mockup HTML completo y Home actual antes de editar.
  - Objetivo: listar brechas visuales y funcionales antes de modificar componentes.
  - Cambio exacto: producir checklist de brechas por seccion: navbar, hero, search, pills, stats, instituciones, cards, abiertos, paises, banner y footer.
  - Archivos esperados: `requerimientos/30062026/studiamatch_home.html`, `web/src/app/HomeContent.tsx`.
  - CAs relacionados: CA5, CA6, CA13 Home.
  - Validacion: checklist de brechas documentado.
- [ ] **ST-02 — Ajustar shell/datos iniciales de Home**
  - Analisis previo: revisar fetch actual y campos disponibles desde Supabase/PostgREST.
  - Objetivo: asegurar que `/` obtiene datos necesarios sin romper SSR/static export.
  - Cambio exacto: ajustar queries o props existentes para alimentar secciones Home con datos reales/fallbacks permitidos.
  - Archivos esperados: `web/src/app/page.tsx`, `web/src/app/HomeContent.tsx`.
  - CAs relacionados: CA5.
  - Validacion: lint/typecheck.
- [ ] **ST-03 — Implementar navbar sticky y hero**
  - Analisis previo: comparar Header/Home actual contra mockup y revisar responsive.
  - Objetivo: adaptar cabecera, gradiente, copy y search bar al mockup.
  - Cambio exacto: implementar header sticky, hero, gradiente/paleta, copy y buscador sin cambiar rutas fuera de alcance.
  - Archivos esperados: `Header`, `HomeContent`, CSS si aplica.
  - CAs relacionados: CA5, CA13 Home.
  - Validacion: revision desktop/mobile.
- [ ] **ST-04 — Implementar secciones Home solicitadas**
  - Analisis previo: mapear cada seccion a datos reales o fallback permitido.
  - Objetivo: crear pills, stats, instituciones, destacados, inscripciones abiertas, paises, banner y footer.
  - Cambio exacto: renderizar cada seccion del mockup en orden aprobado y sin secciones adicionales no solicitadas.
  - Archivos esperados: `HomeContent.tsx`, `web/src/components/**` si se extrae.
  - CAs relacionados: CA5.
  - Validacion: checklist de secciones completo.
- [ ] **ST-05 — Aplicar quick wins visuales**
  - Analisis previo: buscar apariciones publicas de `institutos`, `ROI` y estilos/card actuales.
  - Objetivo: Inter, cards, texto `instituciones` y ROI oculto en vistas publicas.
  - Cambio exacto: ajustar tipografia/copy/cards y ocultar ROI publico sin eliminar calculos internos.
  - Archivos esperados: `globals.css`, componentes Home/cards.
  - CAs relacionados: CA6.
  - Validacion: busqueda de `institutos` y `ROI` visible en Home.
- [ ] **ST-06 — Implementar selector moneda visual**
  - Analisis previo: confirmar exclusion de API real de tipo de cambio en EST-001.
  - Objetivo: mostrar selector sin API real ni conversion dinamica fuera de alcance.
  - Cambio exacto: control visual que no llama servicios externos y no altera precios reales.
  - Archivos esperados: componente Home/Header.
  - CAs relacionados: CA5.
  - Validacion: copy claro y sin llamadas externas.
- [ ] **ST-07 — Actualizar documentacion tecnica Sprint 1**
  - Analisis previo: recopilar commits/resultados reales de TAREA-001 a TAREA-004.
  - Objetivo: documentar campos/tablas, pipeline, admin y criterios operativos modificados.
  - Cambio exacto: actualizar changelog/docs internas con cambios reales y decisiones, sin prometer funcionalidades no entregadas.
  - Archivos esperados: `.context/changelog/`, docs internas que apliquen.
  - CAs relacionados: CA7.
  - Validacion: documento/changelog revisable.
- [ ] **ST-08 — Revisar accesibilidad/SEO basico**
  - Analisis previo: revisar estructura semantica, labels y metadata vigente.
  - Objetivo: conservar estructura semantica, labels de busqueda, contraste y metadata existente.
  - Cambio exacto: ajustar labels/aria/focus/heading hierarchy solo donde el rediseño lo requiera.
  - Archivos esperados: Home/components.
  - CAs relacionados: CA5, CA6, CA13 Home.
  - Validacion: checklist `accessibility`/`seo` si aplica.

## Archivos afectados
| Archivo | Tipo de cambio |
|---|---|
| `web/src/app/page.tsx` | Ajuste shell/datos iniciales de Home |
| `web/src/app/HomeContent.tsx` | Rediseño Home segun mockup y quick wins |
| `web/src/app/globals.css` | Tokens/estilos Tailwind v4 necesarios |
| `web/src/components/` | Componentes reutilizables para cards/sections si aplica |
| `.context/changelog/` | Registro de cierre tecnico del hito |

## Plan de ejecucion
1. Leer EST-001, mockup Home y esta tarea antes de tocar codigo.
2. Levantar brechas visuales contra el HTML aprobado.
3. Implementar secciones y quick wins manteniendo componentes simples.
4. Validar desktop/mobile, lint/typecheck y documentacion.
5. Invocar accessibility/seo/security segun cambios antes de commit/PR.
6. Registrar resultado en changelog y en esta tarea.

## Validaciones requeridas
- [ ] `docker exec studiamatch-dev bash -lc "cd /app/web && npm run lint"`.
- [ ] `docker exec studiamatch-dev bash -lc "cd /app/web && npx tsc --noEmit"`.
- [ ] Revision responsive desktop/mobile.
- [ ] Checklist de secciones contra mockup aprobado.
- [ ] Ejecucion de matriz `CA -> pruebas/evidencia`.
- [ ] Revision `security-auditor` antes de commit/PR.

## Evidencia requerida
- [ ] Checklist de secciones Home implementadas.
- [ ] Evidencia de ROI oculto y texto `instituciones`.
- [ ] Salida de lint/typecheck.
- [ ] Resumen de documentacion tecnica actualizada.
- [ ] PR a `desarrollo`.

## Checklist de cierre
- [ ] CA5 cubierto.
- [ ] CA6 cubierto.
- [ ] CA7 cubierto.
- [ ] CA13 Home cubierto.
- [ ] No se implementa API real de moneda.
- [ ] Changelog actualizado.

## Notas de implementacion
<!-- Detalles tecnicos aqui -->

## Resultado
<!-- Actualizado por la IA al completar: Fecha, commits, PR -->
