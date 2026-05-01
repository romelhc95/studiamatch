# Informe de Auditoría de Ruido en URLs de Cursos
**Fecha:** 2026-04-25 12:05:49

## 1. Resumen por Institución
| Institución | Total Registros | Sospechosos | % Ruido |
|-------------|-----------------|-------------|---------|
| c64123d6-f00e-4c89-86a8-7706845c0483 | 81 | 78 | 96.30% |
| 24cc140d-de25-4ef1-9316-b897b451be50 | 2 | 1 | 50.00% |
| cf64d254-733d-4a92-8a2d-5df5b9dc80ac | 172 | 58 | 33.72% |
| ccd04100-1bde-427b-b94f-ab24ae233a2a | 60 | 0 | 0.00% |
| 2aa0d175-bfbd-46d0-b84c-14083d2336b0 | 2 | 0 | 0.00% |
| **TOTAL** | **317** | **137** | **43.22%** |

## 2. Listado de Patrones Detectados por Institución
### Institución: `c64123d6-f00e-4c89-86a8-7706845c0483`
| Categoría de Ruido | Frecuencia |
|--------------------|------------|
| Carrito/Checkout | 77 |
| Filtros/Categorías | 1 |

### Institución: `24cc140d-de25-4ef1-9316-b897b451be50`
| Categoría de Ruido | Frecuencia |
|--------------------|------------|
| Páginas de Login/Redirección | 1 |

### Institución: `cf64d254-733d-4a92-8a2d-5df5b9dc80ac`
| Categoría de Ruido | Frecuencia |
|--------------------|------------|
| Subpáginas de Programa | 50 |
| Blogs/Noticias/Eventos | 7 |
| Páginas Genéricas/Landing | 1 |

## 3. Justificación Técnica
- **Carrito/Checkout (`add-to-cart=`):** Enlaces directos a la funcionalidad de compra. No son páginas descriptivas del curso y generan duplicidad masiva.
- **Filtros/Categorías (`_filtro_`):** Resultados de búsqueda interna. No representan un curso individual sino una agrupación dinámica.
- **Subpáginas de Programa:** URLs terminadas en `/malla-curricular`, `/beneficios`, etc. Fragmentan la información de un solo programa en múltiples registros, dificultando la indexación limpia.
- **Archivos Directos (.pdf, .docx):** Documentos que deberían ser tratados como adjuntos o recursos, no como la URL principal del curso.
- **Páginas Administrativas/Login:** Ruido capturado por el crawler al seguir enlaces de pie de página o áreas restringidas.
- **Blogs/Noticias/Eventos:** Contenido efímero o informativo que no forma parte de la oferta académica estructural.

## 4. Recomendaciones para `crawler_exclusions`
Se recomienda añadir los siguientes patrones de exclusión para limpiar la base actual y prevenir futuros ingresos:

### Patrones Globales Recomendados (Regex/Strings):
1. `.*add-to-cart=.*` (Eliminar duplicados de compra)
2. `.*_filtro_.*` (Eliminar páginas de búsqueda/filtros)
3. `.*/noticias/.*`, `.*/blog/.*`, `.*/eventos/.*` (Eliminar contenido temporal)
4. `.*\.pdf$`, `.*\.docx$` (Eliminar archivos directos)
5. `.*/malla-curricular/?$`, `.*/presentacion/?$`, `.*/beneficios/?$` (Evitar fragmentación de programas)

### Acciones de Mantenimiento:
- **Limpieza Inmediata:** Ejecutar un script de borrado para los 67 registros identificados (según el análisis detallado).
- **Sincronización con `crawler_exclusions`:** Insertar estos patrones en la tabla homónima para que los harvesters los omitan automáticamente en el próximo ciclo.
- **Normalización de URLs:** Implementar una regla para remover parámetros de consulta (query params) que no sean esenciales para identificar el curso.
