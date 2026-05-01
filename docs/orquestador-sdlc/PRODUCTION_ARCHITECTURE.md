# Manual de Operación y Arquitectura: StudIAMatch 📘

Este manual describe el funcionamiento autónomo del sistema en producción. StudIAMatch opera bajo una arquitectura de **4 Niveles de Mantenimiento**, garantizando que el catálogo sea siempre veraz, amplio, enriquecido y funcional a través de una automatización total en GitHub Actions.

---

## 1. Diagrama de Arquitectura General

```mermaid
graph TD
    subgraph "🌐 FUENTES DE DATOS"
        A1[SUNEDU / MINEDU]
        A2[Sitios Web\nde Universidades]
        A3[Sitios Web\nde Institutos]
    end

    subgraph "⚙️ GITHUB ACTIONS — Golden Pipeline"
        direction TB

        B1["🛰️ Nivel 1: Discovery\n(Mensual - Día 1, 00:00 UTC)\ndiscovery_institutions.py"]

        B2["🏗️ Nivel 2: Orchestrator\n(Semanal - Dom, 02:00 UTC)\nmaster_orchestrator.py"]

        subgraph "Workers Paralelos"
            W1["Worker 1"]
            W2["Worker 2"]
            W3["Worker 3"]
            W4["Worker 4"]
            W5["Worker 5"]
        end

        B3["🧠 Nivel 2.5: Post-Process\n(Tras Workers)\nllm_enrichment + taxonomy_audit"]

        B4["🩺 Nivel 3: Integrity Ping\n(Diario - 05:00 UTC)\nintegrity_ping.py"]

        B1 --> B2
        B2 --> W1 & W2 & W3 & W4 & W5
        W1 & W2 & W3 & W4 & W5 --> B3
    end

    subgraph "🗄️ SUPABASE (PostgreSQL)"
        direction LR
        DB1[(institutions)]
        DB2[(courses)]
        DB3[(categories)]
        DB4[(leads)]
    end

    subgraph "🌍 FRONTEND — Cloudflare Pages"
        FE1["StudIAMatch.pages.dev\n(Next.js 16 — Static Export)"]
        FE2["🔍 Buscador\n(pg_trgm fuzzy search)"]
        FE3["📋 Catálogo\nSegmentado por Categoria"]
        FE4["📞 Captación de Leads"]
    end

    subgraph "🤖 INTELIGENCIA ARTIFICIAL"
        AI1["Gemini 1.5 Flash\n(Enrichment: syllabus,\nobjectivos, audiencia)"]
    end

    A1 -->|Escaneo mensual| B1
    A2 & A3 -->|Scraping semanal| W1 & W2 & W3 & W4 & W5

    B1 -->|INSERT instituciones| DB1
    W1 & W2 & W3 & W4 & W5 -->|UPSERT cursos| DB2
    B3 -->|PATCH metadata| DB2
    B3 -->|Usa AI real| AI1
    AI1 -->|objectives, syllabus,\ntarget_audience| DB2
    B4 -->|UPDATE is_active| DB2

    DB1 & DB2 & DB3 -->|Supabase API\n(anon key)| FE1
    FE1 --> FE2 & FE3 & FE4
    FE4 -->|INSERT lead| DB4
```

---

## 2. Calendario de Automatización (Cron Schedules)

| Nivel | Nombre | Frecuencia | Horario (UTC) | Script Principal |
| :--- | :--- | :--- | :--- | :--- |
| **Nivel 1** | Descubrimiento | Mensual | Día 1 — 00:00 AM | `discovery_institutions.py` |
| **Nivel 2** | Carga Maestra | Semanal | Dom — 02:00 AM | `master_orchestrator.py` |
| **Nivel 2.5** | Post-Proceso | Tras Nivel 2 | Auto (sin cron) | `llm_enrichment_worker.py` |
| **Nivel 3** | Integridad | Diario | Todos — 05:00 AM | `integrity_ping.py` |

---

## 3. Los 4 Niveles de Operación (The Golden Pipeline)

### 🛰️ Nivel 1: Descubrimiento (Discovery)
- **Script:** `scripts/core/discovery_institutions.py`
- **Funcionamiento:** Escanea registros oficiales (SUNEDU/MINEDU) para identificar instituciones licenciadas que aún no existen en la base de datos.
- **Persistencia:** `INSERT` de nuevas filas en la tabla `institutions` de Supabase.
- **Reflejo:** Las nuevas instituciones aparecen en los filtros de búsqueda una vez que tienen cursos asociados.

### 🏗️ Nivel 2: Carga Maestra (Master Parallel Load)
- **Scripts:** `master_orchestrator.py` + `worker_runner.py` + Harvesters dedicados/universal.
- **Funcionamiento:**
  1. El orquestador consulta Supabase, obtiene todas las instituciones activas y las divide en 5 grupos.
  2. GitHub lanza **5 máquinas virtuales en paralelo**.
  3. Cada Worker usa el harvester dedicado si existe (ej: `pucp_harvester.py`), o el `universal_harvester.py` para el resto.
  4. Los datos se persisten vía UPSERT (`on_conflict=institution_id,name,slug`) garantizando 0 duplicados.
- **Persistencia:** `UPSERT` en la tabla `courses`. Actualiza `last_scraped_at` en cada ciclo.
- **Reflejo:** Precios, descripción breve y disponibilidad actualizados cada domingo en la web.

### 🧠 Nivel 2.5: Post-Procesamiento (Enrichment & Segmentation)
- **Scripts:** `llm_enrichment_worker.py` + `taxonomy_roi_audit.py` + `metadata_quality_report.py`
- **Funcionamiento:**
  1. **LLM Enrichment**: Identifica cursos con `syllabus`, `objectives` o `target_audience` nulos. Llama a **Gemini 1.5 Flash** con un prompt contextualizado (nombre del curso, categoría, tipo) para generarlos en español peruano. Respeta el límite de la API con pausas de 6 segundos.
  2. **Taxonomy Audit**: Recorre todos los cursos activos y valida que tengan una categoría válida del catálogo. Corrige asignaciones automáticamente si detecta inconsistencias.
  3. **Quality Report**: Genera un reporte `docs/metadata_quality_report.md` con métricas de completitud (% de cursos con precio, descripción, syllabus, etc.). El reporte se sube como **artefacto descargable** en GitHub Actions por 30 días.
- **Condición de ejecución:** `if: always()` — se ejecuta aunque algún Worker del Nivel 2 haya fallado parcialmente, protegiendo la data ya insertada.
- **Persistencia:** `PATCH` en campos de metadatos de la tabla `courses`.
- **Reflejo:** Los filtros de categoría y los detalles de cada curso en la web siempre tendrán información completa y segmentada correctamente.

### 🩺 Nivel 3: Integridad y Vigencia (Integrity Ping)
- **Script:** `scripts/core/integrity_ping.py`
- **Funcionamiento:** Hace una petición HTTP HEAD a la URL de cada curso activo. Evalúa el código de respuesta.
- **Lógica de Gracia:**
  - **HTTP 200**: Curso sano → se actualiza `last_ping_status = "ok"`.
  - **HTTP 404/500 (1er día)**: Se registra advertencia.
  - **HTTP 404/500 (3 días consecutivos)**: Se actualiza `is_active = false` automáticamente.
- **Persistencia:** `PATCH` en `is_active` y `last_ping_status` de la tabla `courses`.
- **Reflejo:** Cursos caídos desaparecen del buscador y del catálogo en tiempo real (la web solo consulta `is_active = true`).

---

## 4. Arquitectura de Datos

### Tablas Principales (Supabase/PostgreSQL)
| Tabla | Función |
| :--- | :--- |
| `institutions` | Catálogo maestro de universidades e institutos. |
| `courses` | Todos los cursos scrapeados con 14+ dimensiones de metadata. |
| `categories` | Taxonomía oficial de StudIAMatch. Fuente de verdad para filtros. |
| `category_rules` | Reglas de clasificación dinámica (keyword → categoría). |
| `leads` | Formularios de captación de contacto enviados desde la web. |
| `market_salaries` | Data de referencia salarial por rol (para widget de ROI). |

### Seguridad de Acceso
- **Frontend (Anon Key)**: Solo puede leer cursos activos (`is_active = true`). RLS habilitado.
- **Workers (Service Role Key)**: Bypass de RLS para escritura masiva. Exclusivo de GitHub Actions Secrets.
- **Búsqueda Avanzada**: Extensión `pg_trgm` habilitada para búsqueda difusa tolerante a errores ortográficos.

---

## 5. Stack Tecnológico

| Capa | Tecnología | Propósito |
| :--- | :--- | :--- |
| **Frontend** | Next.js 15 + TypeScript | Interfaz de usuario y SEO |
| **Hosting Web** | Cloudflare Pages | CDN global, HTTPS, 0-downtime deploy |
| **Base de Datos** | Supabase (PostgreSQL) | Almacenamiento, API REST, RLS |
| **Automatización** | GitHub Actions | Orquestación y ejecución de todos los niveles |
| **Scraping** | Playwright + Requests | Extracción de datos estáticos y dinámicos (JS) |
| **IA / Enrichment** | Google Gemini 1.5 Flash | Generación de metadata educativa |
| **Anti-Bot** | playwright-stealth | Bypass de Cloudflare en sitios protegidos |

---

## 6. Gestión de Secretos

Todos los secretos son configurados en **GitHub Repository Settings → Secrets and Variables → Actions** y nunca se escriben en el código fuente.

| Secret | Propósito |
| :--- | :--- |
| `SUPABASE_URL` | Endpoint de la base de datos |
| `SUPABASE_SERVICE_ROLE_KEY` | Token maestro de escritura (Workers) |
| `GEMINI_API_KEY` | API Key para el enriquecimiento con IA |

---

*Este documento es la fuente oficial de verdad para el mantenimiento y escalamiento de StudIAMatch.*
*Última actualización: 2026-04-14*
