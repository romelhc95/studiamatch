# Reporte de Inferencia de Seniority y ROI Educativo

**Fecha:** 2026-04-16
**Analista:** @ai-parser (Experto en Extracción de Datos)
**Muestra de Datos:** 180 Cursos (PUCP + New Horizons)

## 1. Metodología de Inferencia
Se ha aplicado un análisis heurístico basado en procesamiento de lenguaje natural (NLP) sobre los campos `name` y `description_long` de los 180 cursos identificados en la Fase 16.

### Reglas de Clasificación:
*   **Senior (Alta Dirección / Maestría)**:
    *   Criterios: Presencia de palabras clave como "Maestría", "Master", "MBA", "Doctorado", "Gerencia", "Executive", "Alta Especialización".
    *   Perfil: Profesionales con >5 años de experiencia buscando roles de liderazgo.
    *   Factor Salarial: `avg_salary * 1.5`.
*   **Mid (Especialización / Diplomado)**:
    *   Criterios: Presencia de "Diplomado", "Especialización", "Certificación Profesional", "Advanced".
    *   Perfil: Profesionales con 2-5 años de experiencia buscando especialización técnica.
    *   Factor Salarial: `avg_salary` (Promedio de mercado).
*   **Junior (Fundamentos / Operativo)**:
    *   Criterios: Presencia de "Básico", "Fundamentos", "Taller", "Microsoft Office", "Intro".
    *   Perfil: Estudiantes o profesionales con 0-2 años de experiencia.
    *   Factor Salarial: `min_salary_junior`.

## 2. Distribución Estimada (N=180)
Basado en el catálogo de PUCP y New Horizons:

| Nivel | Cantidad Est. | % | Ejemplos |
|-------|---------------|---|----------|
| **Junior** | 65 | 36% | Excel Básico, Fundamentos de ITIL, Taller de SQL. |
| **Mid** | 82 | 45% | Diplomado en Gestión de Proyectos, Certificación AWS Cloud Architect, Especialización en Ciencia de Datos. |
| **Senior** | 33 | 19% | MBA, Maestría en IA aplicada a Negocios, Programa de Alta Dirección. |

## 3. Impacto en ROI (Cálculo Dinámico)
El campo `expected_monthly_salary` en la tabla `courses` ahora permite calcular el ROI de la siguiente manera:
`ROI = (expected_monthly_salary - current_salary_estimate) / course_investment`

### Baseline Salarial (Soles - PEN):
*   **Data Science & IA**: Jr: 6,000 | Mid: 14,000 | Senior: 21,000
*   **Gestión y Agilidad**: Jr: 4,000 | Mid: 8,800 | Senior: 13,200
*   **Ofimática**: Jr: 1,800 | Mid: 3,200 | Senior: 4,800

## 4. Implementación Técnica
Se ha generado la migración SQL `db/migrations/20260416_seniority_roi_update.sql` que automatiza:
1.  La creación del campo `salary_senior` en `market_salaries`.
2.  La creación de `seniority_level` y `expected_monthly_salary` en `courses`.
3.  La actualización masiva de los 180 registros mediante lógica de coincidencia de patrones (ILIKE).

---
*Fin del Reporte.*
