# Reporte de Evaluación Técnica: Auditoría de Duplicados por Redirección (Fase 39.1)

## 1. Análisis del Problema
Se ha detectado que múltiples URLs (ej. alias, rutas antiguas, o variaciones taxonómicas) resuelven al mismo contenido final. Esto genera redundancia en la base de datos `cleansed_programs` y, eventualmente, duplicidad visual en el frontend.

**Ejemplo detectado:**
- URL A: `universidad.edu.pe/arquitectura-en-ti/togaf`
- URL B: `universidad.edu.pe/gestion-y-procesos-de-ti/togaf`
Ambas redirigen a: `universidad.edu.pe/certificaciones/togaf-v9`

## 2. Comparativa de Estrategias

| Criterio | Estrategia: Último Segmento | Estrategia: Redirección Real (Effective URL) |
| :--- | :--- | :--- |
| **Precisión** | Baja (Riesgo de colisión de slugs genéricos). | Alta (Verdad técnica absoluta). |
| **Performance** | Instantánea (Offline). | Lenta (Requiere I/O de red). |
| **Complejidad** | Mínima (Regex/Split). | Media (Manejo de estados HTTP/Redirecciones). |
| **Sigilo (WAF)** | No afecta. | Riesgo de detección si se hacen re-escaneos masivos. |

## 3. Evaluación de Riesgos
- **Riesgo 1: Falsos Positivos**: Si usamos solo el último segmento (`togaf`), podríamos colapsar erróneamente programas distintos que casualmente comparten slug.
- **Riesgo 2: Sobrecarga de Red**: Ejecutar peticiones `HEAD` por cada registro en el Cleanser duplicaría el tráfico y aumentaría la probabilidad de bloqueo por WAF.

## 4. Plan de Mitigación Propuesto (Estrategia "Effective Sync")

Para mitigar los riesgos, no implementaremos la verificación de red en el `cleansing_worker.py` (que debe ser puramente de transformación), sino que delegaremos la captura a la **Estación 1 (Harvester)**.

### Paso A: Actualización del Harvester (Fase 38.1)
- Modificar `universal_harvester.py` para capturar la `response.url` (la URL final tras redirecciones) y almacenarla en una nueva columna `effective_url` en `staging_raw`.
- **Ventaja**: El Harvester ya está haciendo la petición; capturar la URL final tiene costo cero de red adicional.

### Paso B: Lógica de De-duplicación en Cleansing Worker
- El worker procesará los registros de `staging_raw`.
- Antes de insertar en `cleansed_programs`, realizará un `UPSERT` basado en la clave natural: `(institution_id, effective_url)`.
- Si `effective_url` no está presente, se usará la `url` original como fallback.

### Paso C: Saneamiento de Slugs
- El slug final en `cleansed_programs` se generará a partir de la `effective_url` (último segmento significativo), garantizando que URLs que redirigen a lo mismo terminen con el mismo slug identificador.

## 5. Recomendación Final
**No utilizar únicamente el último segmento**. La implementación debe basarse en la **URL Efectiva** capturada durante el harvesting. Esto garantiza integridad total sin sacrificar performance en la fase de limpieza.

---
**Firma:** Orquestador SDLC (ECC Standard)
**Fecha:** 2026-04-19
