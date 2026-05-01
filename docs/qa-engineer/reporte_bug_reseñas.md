# Reporte de Depuración Técnica: Sistema de Reseñas

**Fecha:** 2024-04-12
**Componente:** `CourseDetailClient.tsx`
**Estado:** Resuelto (Pendiente de aplicación de políticas DB)

## 1. Hallazgos de la Investigación

### A. Problema de Vinculación del Botón (Linkage)
Se identificó que el botón "PUBLICAR RESEÑA" dentro del formulario de Social Proof no tenía el atributo `type="submit"` explícito. Aunque en HTML estándar un botón dentro de un formulario suele actuar como submit, en entornos que utilizan librerías de componentes (como Base UI o Shadcn), este comportamiento puede variar o ser interceptado.
- **Síntoma:** El usuario hace clic y no hay feedback visual (no cambia a "ENVIANDO...").
- **Causa:** El evento `onSubmit` del formulario no se disparaba.

### B. Errores de Consola Ocultos
Tras la inyección de logs de depuración, se observó que en casos donde el envío sí se iniciaba (vía tecla Enter), la promesa de `fetch` permanecía en estado `pending`.
- **Causa Técnica:** Falta de políticas de Row Level Security (RLS) en Supabase para las tablas `ratings` y `reviews`.
- **Comportamiento:** PostgREST, al recibir una solicitud `POST` de un usuario `anon` en una tabla con RLS activo pero sin políticas de `INSERT`, puede experimentar demoras o rechazos que, sumados a la falta de validación de variables de entorno (`SUPABASE_URL` vacío), resultan en un "hang" de la red en el cliente.

## 2. Acciones Realizadas (Fixes)

### Código Frontend (`CourseDetailClient.tsx`)
1. **Atributo Explícito:** Se añadió `type="submit"` al botón de publicación.
2. **Logging Verboso:** Se añadieron `console.log` y `console.error` detallados para trazar el ciclo de vida del envío (Inicio -> POST Rating -> POST Review -> Refresh -> Fin).
3. **Validación de Configuración:** Se añadió un chequeo preventivo de las variables `SUPABASE_URL` y `SUPABASE_ANON_KEY` antes de realizar el fetch.
4. **Captura de Errores Mejorada:** Ahora el `catch` extrae el cuerpo del error JSON de Supabase para mostrar mensajes más precisos.

## 3. Solución Definitiva (Base de Datos)

Para resolver el bloqueo de RLS, se debe ejecutar el siguiente script SQL en el panel de Supabase:

```sql
-- Habilitar RLS
ALTER TABLE public.ratings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reviews ENABLE ROW LEVEL SECURITY;

-- Políticas para Ratings
DROP POLICY IF EXISTS "Enable insert for anonymous users" ON public.ratings;
CREATE POLICY "Enable insert for anonymous users" ON public.ratings 
FOR INSERT TO anon 
WITH CHECK (rating_value >= 1 AND rating_value <= 5);

DROP POLICY IF EXISTS "Enable select for everyone" ON public.ratings;
CREATE POLICY "Enable select for everyone" ON public.ratings 
FOR SELECT USING (true);

-- Políticas para Reviews
DROP POLICY IF EXISTS "Enable insert for anonymous users" ON public.reviews;
CREATE POLICY "Enable insert for anonymous users" ON public.reviews 
FOR INSERT TO anon 
WITH CHECK (char_length(content) > 0);

DROP POLICY IF EXISTS "Enable select for everyone" ON public.reviews;
CREATE POLICY "Enable select for everyone" ON public.reviews 
FOR SELECT USING (true);
```

## 4. Verificación
- [x] Botón vinculado correctamente a `handleSubmitSocial`.
- [x] Logs visibles en consola para depuración.
- [x] Manejo de errores previene el estado `pending` infinito al validar la respuesta.
