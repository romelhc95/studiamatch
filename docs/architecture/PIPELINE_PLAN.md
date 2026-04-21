# Plan de Despliegue: Pipeline de Producción StudIAMatch (GitActions + AI)

Este documento detalla la estrategia para automatizar el ciclo de vida de los datos del proyecto StudIAMatch utilizando servicios gratuitos o de bajo costo.

## 1. Análisis de Costos de Modelos AI

| Proveedor | Modelo Recomendado | Costo | Ventajas |
| :--- | :--- | :--- | :--- |
| **GitHub Models (Beta)** | Llama 3.1 - 70B / 8B | **Gratis** (Limits beta) | Integración nativa con GitHub Actions, alta calidad. |
| **Cloudflare Workers AI** | Llama 3.1 - 8B | 10k Neurons/día **Gratis** | Extremadamente rápido, ideal para tareas masivas. |
| **Groq Cloud** | Llama 3.1 - 8B/70B | Tier **Gratis** Generoso | Baja latencia, API compatible con OpenAI. |

**Recomendación**: Usar **GitHub Models** para el pipeline inicial debido a que ya estamos en el ecosistema de GitHub y el límite gratuito de la beta es suficiente para el enriquecimiento diario de ~50-100 cursos.

## 2. Arquitectura del Pipeline (GitHub Actions)

El ciclo se dividirá en 3 workflows para optimizar el consumo de recursos y tokens:

### A. `discovery.yml` (Mensual)
- **Frecuencia**: Día 1 de cada mes.
- **Acción**: Ejecuta `discovery_institutions.py`.
- **Objetivo**: Identificar nuevas universidades o dominios.

### B. `daily_ingestion.yml` (Diario)
- **Frecuencia**: Todos los días 04:00 AM (Hora Lima).
- **Flujo**:
  1. `UniversalHarvester`: Descarga URLs de cursos nuevos.
  2. `LLMWorker`: Procesa los "14 Pilares" usando la API de GitHub Models.
  3. `DatabaseMigrator`: Inyecta los datos limpios a Supabase.

### C. `health_check.yml` (Continuo/Trigger)
- **Frecuencia**: Tras cada ingesta o semanal.
- **Acción**: Ejecuta `dedup_integrity_audit.py` y `quality_assurance_audit.py`.

## 3. Configuración de Secretos (GitHub Secrets)

Para que el pipeline funcione, se deben configurar las siguientes variables en el repositorio:
- `NEXT_PUBLIC_SUPABASE_URL`: URL de tu proyecto Supabase.
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`: Key anónima para lectura/escritura básica.
- `SUPABASE_SERVICE_ROLE_KEY`: Requerido para operaciones de mantenimiento y bypass de RLS.
- `GITHUB_TOKEN` o `GH_MODELS_TOKEN`: Para acceder a la API de modelos de GitHub.

## 4. Hoja de Ruta de Implementación

- [x] **Paso 1**: Investigación de costos y viabilidad técnica.
- [ ] **Paso 2**: Crear el archivo `.github/workflows/production_pipeline.yml`.
- [ ] **Paso 3**: Adaptar `scripts/core/llm_enrichment_worker.py` para usar el SDK de OpenAI apuntando a GitHub Models (`https://models.inference.ai.azure.com`).
- [ ] **Paso 4**: Realizar un "Dry Run" de ingesta para validar que el worker no exceda los rate limits de la beta.
- [ ] **Paso 5**: Habilitar el pipeline automático.
