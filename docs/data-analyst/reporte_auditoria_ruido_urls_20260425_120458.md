# Informe de Auditoría de Ruido en URLs de Cursos
**Fecha:** 2026-04-25 12:04:58

## 1. Resumen por Institución
| Institución | Total Registros | Sospechosos | % Ruido |
|-------------|-----------------|-------------|---------|
| c64123d6-f00e-4c89-86a8-7706845c0483 | 81 | 0 | 0.00% |
| ccd04100-1bde-427b-b94f-ab24ae233a2a | 60 | 0 | 0.00% |
| cf64d254-733d-4a92-8a2d-5df5b9dc80ac | 172 | 8 | 4.65% |
| 24cc140d-de25-4ef1-9316-b897b451be50 | 2 | 0 | 0.00% |
| 2aa0d175-bfbd-46d0-b84c-14083d2336b0 | 2 | 0 | 0.00% |
| **TOTAL** | **317** | **8** | **2.52%** |

## 2. Listado de Patrones Detectados por Institución
### cf64d254-733d-4a92-8a2d-5df5b9dc80ac
| Patrón Detectado | Frecuencia |
|------------------|------------|
| `/eventos/` | 6 |
| `index.html` | 1 |
| `/noticias/` | 1 |

## 3. Justificación Técnica
- **Noticias/Blogs/Eventos:** Estas páginas contienen información temporal o institucional que no describe una oferta académica permanente.
- **Páginas Administrativas/Transparencia:** Portales de trámites, transparencia y organigramas que son necesarios para la navegación pero no son cursos.
- **Tags/Categorías:** Páginas de listado que duplican contenido o agrupan posts, generando redundancia sin aportar datos únicos de programas.
- **Páginas de Agradecimiento/Contacto:** Formularios y respuestas automáticas capturadas por el crawler.
- **Documentos Directos:** Enlaces a archivos (PDF, DOCX) que deben ser procesados como metadatos, no como páginas de curso independientes (si no tienen contenido extra).

## 4. Recomendaciones para `crawler_exclusions`
Se recomienda añadir los siguientes patrones globales y específicos a la tabla `crawler_exclusions` para optimizar futuros rastreos:

### Patrones Globales Recomendados:
- `/noticias/`
- `/eventos/`

### Acciones Sugeridas:
1. **Limpieza Quirúrgica:** Eliminar los registros identificados como ruido en este reporte.
2. **Actualización de Exclusiones:** Poblar `crawler_exclusions` con los patrones listados para evitar su re-ingreso.
3. **Refinamiento de Reglas de Selección:** Ajustar el `universal_harvester` para que ignore estas rutas mediante regex antes de intentar la extracción de metadatos.
