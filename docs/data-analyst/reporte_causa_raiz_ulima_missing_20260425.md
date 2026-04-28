# Informe de Causa Raíz: URLs Faltantes de la Universidad de Lima (U. Lima)

**Fecha:** 2026-04-25
**Analista:** Data Analyst Agent
**Estado del Catálogo:** 35 cursos activos (vs. 102 esperados)

## 1. Resumen del Diagnóstico
Tras un rastreo de linaje desde la fase de descubrimiento hasta la sincronización final, se han identificado **tres cuellos de botella críticos** que impiden que los 102 programas de U. Lima se reflejen en StudIAMatch:

1.  **Filtro de Descubrimiento Restrictivo (Harvester):** El motor de búsqueda descarta URLs que no contienen palabras clave académicas específicas. Esto elimina el 100% de las carreras de **Pregrado** e **Idiomas**.
2.  **Bloqueo de Estado "Discovered" (Deadlock):** 124 URLs fueron identificadas pero nunca procesadas. El harvester omite el scraping de cualquier URL que ya exista en la base de datos, incluso si está pendiente de recolección.
3.  **Colisión con Reglas de Ruido:** Gran parte del contenido de U. Lima se filtra como "noticias" debido a que la estructura de la web de la universidad mezcla información académica con blogs bajo rutas similares.

---

## 2. Análisis Detallado por Categoría

| Categoría | Status en StudIAMatch | Causa Raíz |
| :--- | :--- | :--- |
| **Pregrado** | ❌ Ausente | **Filtro de URL:** Las rutas `/pregrado/[carrera]` no contienen las palabras "curso", "maestría" o "programa", por lo que el `UniversalHarvester` las ignora en el Nivel 2. |
| **Maestrías / Doctorados** | ⚠️ Parcial | **Deadlock de Scraping:** 124 URLs de posgrado están en `staging_raw` con estado `discovered` pero nunca fueron "abiertas" por el navegador porque el sistema detecta que "ya existen" y salta el scraping. |
| **Idiomas** | ❌ Ausente | **Filtro de URL:** La ruta `/idiomas/` no está en la lista blanca de términos del buscador automático. |
| **Educación Ejecutiva** | ✅ Mayoría | **Éxito Parcial:** Al contener términos como `/cursos-talleres/`, estas URLs superan el filtro inicial. Sin embargo, algunas se pierden si el nombre es corto o la descripción es insuficiente (<100 caracteres). |

---

## 3. Identificación de Bloqueos Técnicos

### A. El Filtro "Potential Course" (`universal_harvester.py`)
El script `universal_harvester.py` utiliza la siguiente lógica para decidir qué guardar:
```python
keywords = ["curso", "diplomado", "maestria", "doctorado", "programa", "especializacion"]
return any(k in url.lower() for k in keywords)
```
*   **Problema:** URLs como `ulima.edu.pe/pregrado/administracion` o `ulima.edu.pe/idiomas/english` fallan esta validación.
*   **Impacto:** Los programas no llegan ni siquiera a la tabla `staging_raw`.

### B. El Bucle de Persistencia
En `discover_courses`, el harvester carga las URLs existentes para evitarlas:
```python
existing_urls = await self._load_existing_urls() # Carga todas con status != 'error'
final_urls = [url for url in list(self.course_urls) if url not in existing_urls]
```
*   **Problema:** Si una URL se guardó como `discovered` pero el proceso se interrumpió antes de hacer el `scrape_course_detail`, en la siguiente ejecución el sistema la verá como "existente" y **NUNCA** la procesará.
*   **Impacto:** 124 registros de U. Lima están "congelados" en estado `discovered`.

### C. Ruido de Noticias (Falsos Positivos)
Se detectaron 152 registros descartados con la razón `hard_db_exclusion:/noticias/`.
*   **Hallazgo:** El harvester encuentra URLs de noticias que sí contienen la palabra "curso" (ej: `/pregrado/administracion/noticias/inscripciones-al-curso...`).
*   **Impacto:** El sistema gasta recursos en descubrir noticias mientras ignora las páginas principales de las carreras.

---

## 4. Detección de Falsos Positivos (Fase 46/47)
Se verificó si las reglas de saneamiento están borrando cursos válidos:
- **Regla de Año (<2026):** No parece estar afectando los 102 programas principales, ya que sus URLs no suelen llevar el año.
- **Normalización de Slash:** Se detectaron 17 duplicados resueltos, lo cual es correcto.
- **Exclusiones Manuales:** El patrón `/agenda/` y `/tags/` es correcto, pero debe vigilarse que no colisione con rutas de Educación Ejecutiva.

---

## 5. Recomendaciones de Acción Inmediata

1.  **Actualizar Harvester (Filtros):** Expandir la lista de keywords en `universal_harvester.py` para incluir: `"pregrado"`, `"carrera"`, `"idiomas"`, `"talleres"`, `"facultad"`.
2.  **Corregir Lógica de Scraping:** Modificar `_load_existing_urls` para que solo ignore URLs con status `processed` o `pending`. Las que estén en `discovered` deben ser re-evaluadas para scraping.
3.  **Reset de U. Lima:** Ejecutar un SQL para resetear el estado de los 124 registros "congelados":
    ```sql
    UPDATE staging_raw SET status = 'pending' 
    WHERE institution_id = 'ccd04100-1bde-427b-b94f-ab24ae233a2a' 
    AND status = 'discovered';
    ```
4.  **Inyección Manual de Semillas:** Dado que el crawler se pierde en las noticias, se recomienda inyectar las 102 URLs mapeadas manualmente directamente en `staging_raw` con status `pending` para forzar su procesamiento inmediato.

---
**Reporte generado por:** Data Analyst Agent
**Timestamp:** 20260425_144500
