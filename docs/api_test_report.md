# Reporte de Pruebas Integrales de la API - StudIAMatch.AI

**Fecha de Ejecución:** 31/03/2026 (Hora Peruana)
**Estado General:** 🟠 PARCIAL (5 Pasaron, 3 Fallaron)

## 1. Resumen de Resultados

| Categoría | Total | Pasó | Falló | % Éxito |
|-----------|-------|-------|--------|---------|
| Lectura (GET) | 4 | 4 | 0 | 100% |
| Escritura (POST) | 2 | 0 | 2 | 0% |
| Resiliencia | 2 | 1 | 1 | 50% |
| **TOTAL** | **8** | **5** | **3** | **62.5%** |

## 2. Detalle Técnico de Endpoints Probados

### GET /courses
- **Básico:** Pasó (1.359s). Obtención de los primeros 5 cursos.
- **Filtro Modalidad:** Pasó (0.800s). Filtro por `mode=eq.Presencial` verificado correctamente.
- **Ordenamiento:** Pasó (0.686s). Orden por `price_pen.asc` verificado correctamente.

### GET /institutions
- **Básico:** Pasó (0.786s). Obtención de instituciones piloto (UTEC, UPC).

### POST /leads (Escritura)
- **Tipo Info:** **FALLÓ** (0.503s). 
  - **Request:** Datos completos de lead tipo info (course_id asociado).
  - **Status Esperado:** 201 Created.
  - **Status Obtenido:** 401 Unauthorized / 42501 (RLS violation).
- **Tipo Recommendation:** **FALLÓ** (0.835s).
  - **Request:** Datos de recomendación (area_interest, budget, etc.).
  - **Status Esperado:** 201 Created.
  - **Status Obtenido:** 401 Unauthorized / 42501 (RLS violation).

### Resiliencia
- **Campos faltantes:** **FALLÓ** (0.767s). El sistema falló por RLS antes de que PostgREST pudiera validar las restricciones `NOT NULL`.
- **UUID inválido:** Pasó (0.780s). PostgREST validó el tipo de dato UUID antes de aplicar las políticas de RLS, devolviendo 400 Bad Request como se esperaba.

## 3. Análisis del Fallo de RLS en la tabla `leads`

El error `42501: new row violates row-level security policy for table "leads"` indica que:
1.  **RLS está activado** en la tabla `leads`.
2.  **No existe una política permisiva** para el rol `anon` (anónimo) que permita la operación `INSERT`.

Debido a la naturaleza de Supabase, cuando se habilita RLS, se bloquea todo el tráfico por defecto. Dado que los leads se envían desde el frontend público, el rol `anon` debe tener permisos explícitos para insertar filas.

## 4. Sugerencias de Remediación SQL

Se recomienda ejecutar el siguiente script en el editor SQL de Supabase para habilitar correctamente el flujo de leads:

```sql
-- 1. Habilitar RLS en la tabla leads (si no está ya habilitado)
ALTER TABLE public.leads ENABLE ROW LEVEL SECURITY;

-- 2. Permitir que usuarios anónimos (público) inserten leads
CREATE POLICY "Permitir inserción pública de leads"
ON public.leads
FOR INSERT
TO anon
WITH CHECK (true);

-- 3. (Opcional) Permitir que usuarios autenticados (admin) vean los leads
CREATE POLICY "Permitir lectura de leads a usuarios autenticados"
ON public.leads
FOR SELECT
TO authenticated
USING (true);
```

## 5. Tiempos de Latencia Observados

- **Latencia Mínima:** 0.503s (POST /leads)
- **Latencia Máxima:** 1.359s (GET /courses)
- **Latencia Promedio:** **0.815s**

*Nota: Las latencias de POST son menores porque la operación se interrumpe inmediatamente por la base de datos debido a la infracción de RLS.*

---
**Reporte generado automáticamente por el Guardián de la Calidad.**
