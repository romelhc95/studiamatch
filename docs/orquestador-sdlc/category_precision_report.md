# Reporte de Precisión de Categorías - StudIAMatch.ai

## 1. Resumen Ejecutivo
Tras el reciente refactor del motor de categorización (`standardize_category`), se ha realizado un análisis exhaustivo de los **172 cursos** actuales en la base de datos de Supabase. El objetivo fue evaluar la precisión del mapeo semántico y proponer reglas que mejoren la calidad del catálogo.

**Hallazgos Clave:**
- **Cursos no estandarizados (General):** 27 cursos (15.7%) permanecen fuera de las categorías estándar del sistema.
- **Falsos Positivos Críticos:** Se detectó una alta tasa de falsos positivos en la categoría **"Data Science & IA"** (60 cursos), causada por una regla de coincidencia parcial demasiado agresiva ("ia").
- **Mapeo Incompleto:** Áreas como Marketing, Finanzas y Derecho carecen de reglas de mapeo, resultando en una fragmentación del catálogo.

---

## 2. Evaluación de Categoría 'General'
Se consideran "General" aquellos cursos que no coincidieron con ninguna regla del motor dinámico y mantuvieron su etiqueta original de la fuente (PUCP o New Horizons) que no pertenece al set de las 11 categorías estándar.

### Distribución de Cursos "General / No Estandarizados" (27 en total):
| Categoría Original | Cantidad | Ejemplo de Curso |
|--------------------|----------|------------------|
| Ingeniería Y Tecnología | 5 | Manejo de Hojas de Cálculo: Nivel Intermedio |
| Innovación Educativa | 5 | Fundamentos del Diseño de Juegos de Mesa |
| Arte Y Diseño | 4 | Escultura y Modelado 3D en Blender |
| Contabilidad Y Finanzas | 4 | Finanzas para no Financieros |
| Power Skills | 3 | Power Skills para Directivos |
| Marketing Digital | 2 | Growth Marketing & Automation |
| Otros (Teatro, Derecho) | 4 | Introducción al Sistema Interamericano de Derechos Humanos |

**Observación:** Muchos de estos cursos deberían ser absorbidos por categorías existentes o nuevas para mejorar la experiencia de búsqueda del usuario.

---

## 3. Análisis de Errores en el Motor de Reglas
El motor actual presenta dos debilidades principales que afectan la precisión:

1.  **Falso Positivo por "ia"**: La regla `if "ia" in text` está capturando palabras comunes como "Soc**ia**l", "Comerc**ia**l", "Exper**ia**", "Innovac**ió**n" y "Tecnolog**ía**". 
    *   *Impacto:* Cursos de "Coaching", "Innovation" o "Networking" (CCNA) están cayendo erróneamente en **Data Science & IA**.
2.  **Shadow Categories**: Categorías como "Ingeniería Y Tecnología" están actuando como un fallback genérico que oculta cursos de "Ofimática" (Excel intermedio).

---

## 4. Propuesta de Nuevas Reglas de Mapeo
Para reducir el volumen de cursos en "General" y corregir los errores de precisión, se proponen las siguientes 6 reglas adicionales para la tabla `category_rules`:

| Palabra Clave (Keyword) | Nueva Categoría Destino | Prioridad | Justificación |
|-------------------------|-------------------------|-----------|---------------|
| `marketing` | Marketing Digital | 25 | Cubre Marketing Digital, Growth y Content Marketing. |
| `finanzas`, `contable` | Finanzas y Contabilidad | 25 | Absorbe cursos de NIF, Controlling e instrumentos financieros. |
| `compliance`, `derecho` | Derecho y Normativa | 30 | Clasifica correctamente programas de cumplimiento y arbitraje. |
| `coaching`, `liderazgo` | Power Skills | 20 | Mueve cursos de habilidades blandas fuera de "General". |
| `aprendizaje`, `docente`| Educación e Innovación | 20 | Agrupa metodologías de enseñanza y diseño instruccional. |
| `togaf`, `architecture` | Arquitectura TI | 30 | Especialización técnica diferenciada de redes. |

---

## 5. Recomendaciones de Implementación Técnica
1.  **Delimitadores de Palabra (`\b`)**: Modificar la lógica en `scripts/shared/utils.py` y el trigger SQL para usar límites de palabra en las reglas cortas (como "ia").
2.  **Jerarquía de Prioridades**: Aumentar la prioridad de términos específicos (ej: "excel" = 40) sobre términos genéricos (ej: "datos" = 5).
3.  **Corrección de Backfill**: Ejecutar un script de actualización masiva una vez aplicadas las nuevas reglas para limpiar los 60 cursos de "Data Science & IA" que son falsos positivos.

**Generado por:** Data Analyst Skill
**Fecha:** 2024-04-12
