# Reporte de Funcionalidad V1 - Fase 17
**Fecha:** 2024-04-12
**Estado Global:** ✅ APROBADO CON OBSERVACIÓN (RLS en leads)

## 1. Prueba del Buscador Principal
Se probaron términos reales y se validó la normalización y sensibilidad.
- **Término 'IA'**: 137 resultados encontrados. (Exitoso)
- **Término 'Logística'**: 4 resultados encontrados. (Exitoso)
- **Término 'Excel'**: 4 resultados encontrados. (Exitoso)
- **Observación**: La normalización de tildes funciona correctamente (ej. 'Logística' vs 'logistica').

## 2. Validación de Filtros de Sidebar
- Se verificó la sincronización entre la tabla `categories` y las categorías asignadas a los cursos.
- **Categorías en DB**: 12 categorías activas.
- **Categorías en Cursos**: Todas las categorías presentes en la oferta académica están debidamente registradas en la tabla maestra.
- **Resultado**: Sincronización 100% coherente.

## 3. Carrusel de 'Programas Similares'
- Se validó la lógica de recomendación en la página de detalle.
- **Filtro ID**: Se confirmó que el curso actual se excluye del carrusel mediante `id=neq.${course.id}`.
- **Filtro Categoría**: Los programas sugeridos pertenecen a la misma `category_id`.
- **Resultado**: Coherencia semántica verificada.

## 4. Envío de Lead (Simulación)
- **Estado**: ⚠️ FALLIDO (Error 401 - RLS Policy Violation).
- **Detalle**: El intento de inserción con la clave `anon` fue rechazado por la política de seguridad de la base de datos.
- **Acción Requerida**: Actualizar la política RLS en Supabase para permitir `INSERT` al rol `anon` en la tabla `leads`.

## 5. Publicación de Reseñas (Social Proof)
- Se simuló el envío de una calificación (Rating) y un comentario (Review).
- **Inserción**: Exitosa en ambas tablas.
- **Visibilidad**: La reseña fue verificada en la base de datos inmediatamente después del envío.
- **Resultado**: Sistema de Social Proof operativo.

## Próximos Pasos
1. Corregir la política RLS de la tabla `leads`.
2. Habilitar `pg_trgm` en Supabase para mejorar la búsqueda difusa (Fuzzy Search).
