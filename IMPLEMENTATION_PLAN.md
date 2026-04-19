# Plan de Implementación: StudIAMatch - Tech Education Intelligence

## 🎯 Premisas Obligatorias de Ingeniería (Nivel 0)

> [!IMPORTANT]
> **Documentación de Referencia (Golden Pipeline)**: El diseño arquitectónico, el flujo ETL de 4 estaciones y el diccionario de datos maestro se rigen estrictamente por lo definido en [docs/architecture/Documento_Detallado_workflow](docs/architecture/Documento_Detallado_workflow). Este documento es la "Única Fuente de Verdad" para la lógica de datos.
>
> **Aislamiento Total y Paridad Linux**: Queda estrictamente prohibido ejecutar comandos de desarrollo (npm, python, audit) directamente en el host Windows. 
> Todo comando **DEBE** ser ejecutado dentro del contenedor `studiamatch-dev` (Debian) para garantizar la paridad del 100% con los servidores de despliegue (Cloudflare/Linux).
>
> **Comando Base Mandatorio**:
> `docker exec -it studiamatch-dev [comando]`

## 🛠 Estado Actual del Proyecto (WORKING-CONTEXT)
- **Estado Actual**: Fase 2.0 (TIER 2 - Certificación) ✅ CERTIFICADO.
- **Último Hito**: Consolidación de pipelines de datos y reingeniería de calidad.
- **Próxima Acción**: Implementar de-duplicación inteligente por Redirección y Canonical (Fase 39.1).

## 🚀 Hoja de Ruta: Lanzamiento Producción
- [ ] **Migración de Schema**: Replicar tablas, RLS e índices en el proyecto Pro.
- [ ] **Data Seeding**: Primer harvesting masivo para poblar la base de datos oficial.
- [ ] **Domain Mapping**: Configurar DNS en Cloudflare para `studiamatch.com`.

---

## Estrategia de Ambientes (ECC Tiering)

Para garantizar la estabilidad de **StudIAMatch**, el flujo de trabajo se divide en tres entornos estancos vinculados a sus respectivas ramas de Git:

| Nivel | Rama Git | Propósito | Infraestructura (DB) | Frontend (Hosting) | Documentación
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TIER 1: Desarrollo** | `desarrollo` | Iteración rápida y refactor. | Supabase Free (Actual) | `studiamatch.pages.dev` | `docs/deployment/deploy_desarrollo.md` |
| **TIER 2: Certificación** | `certificacion` | QA, Pruebas de Carga y E2E. | Supabase Free / QA Branch | `staging.studiomatch.com` | `docs/deployment/deploy_certificacion.md` |
| **TIER 3: Producción** | `main` | Servicio estable y escalable. | **Supabase Pro** | `studiomatch.com` | `docs/deployment/deploy_produccion.md` |

---

## Estrategia de Git Flow (Promoción de Código)

El código viajará de forma ascendente cumpliendo "Puertas de Calidad" en cada etapa:

1.  **Work In Progress (WIP)**: Se trabaja en ramas de feature (ej: `feat/new-harvester`) que emergen de `desarrollo`. [x] Ramas `desarrollo` y `certificacion` creadas.
2.  **Pull Request a `desarrollo`**: Revisión técnica y validación de scripts en el sandbox actual.
3.  **Promoción a `certificacion`**: Ejecución obligatoria de la Suite E2E (`Playwright`) y Auditoría de Integridad de Datos.
4.  **Merge a `main`**: Despliegue automático a producción (Supabase Pro) tras aprobación del @SDLC-Chief.

---

## Arquitectura de Ejecución (Macro-Estrategia)
La ejecución del sistema se divide en 3 Fases Generales (FG) para optimizar costos, eficiencia y responsabilidades:

* **FG1: Mapeo Institucional (Frecuencia: Mensual)**
  - **Objetivo**: Descubrir y registrar nuevas universidades e institutos licenciados por MINEDU.
  - **Script Principal**: `register_institution.py` (o procesos de Nivel 1).
* **FG2: Carga Masiva y Delta Scraping (Frecuencia: Semanal)**
  - **Objetivo**: Extracción exhaustiva del catálogo de cursos. La carga inicial obtiene toda la información de las webs institucionales. Las ejecuciones posteriores aplican "Delta Scraping" (mediante Hashing) para extraer y procesar *solo* lo nuevo o modificado, reduciendo radicalmente el costo.
  - **Flujo de Scripts**: `universal_harvester.py` -> `cleansing_worker.py` -> `enrichment_worker.py` -> `sync_vector_worker.py` -> auditorías.
* **FG3: Integridad y Periodo de Gracia (Frecuencia: Diaria)**
  - **Objetivo**: Validar la disponibilidad de los enlaces existentes (404).
  - **Mecanismo**: Comprobar si el curso sigue activo. Si falla, entra en un "Periodo de Gracia" de 3 días antes de inactivarse. Esto desliga al harvester de la verificación diaria.
  - **Script Principal**: `integrity_ping.py`.

## Arquitectura del Cerebro de Datos (Flujo ETL Histórico)
1. **Descubrimiento (The Explorer)** [x] Completado.
2. **Harvesting de URLs (The Collector)** [x] Completado.
3. **Extracción de Data Bruta (Deep Scrape)** [x] Completado.
4. **Enriquecimiento IA/LLM (The Brain)** [x] Completado.
5. **Quality Guard (Auditoría Aleatoria)** [x] Completado (Salud del catálogo certificada al 100%).
6. **Taxonomía Automática (Motor de Reglas)** [x] Completado.
7. **Visualización UX (Next.js 15)** [x] Completado (Detalle de 14 pilares y Social Proof funcionales).

## Estructura de Scripts (Producción)
Jerarquía organizada para garantizar el mantenimiento y balanceo de carga:
- `scripts/core/`: Orquestación, Universal Harvester (FG2) y Mapeo (FG1).
- `scripts/harvesters/`: Scrapers específicos por institución.
- `scripts/maintenance/`: Auditoría de calidad y Ping de integridad 404/Gracia (FG3).
- `scripts/legacy/`: Historial de desarrollo y scripts de un solo uso.

## Pasos de Implementación

### Fase 1 a 10: Cimentación y Rediseño [x] Completado
- Todas las tareas certificadas.

### Fase 11: Escalamiento Progresivo y Triaje [x] Completado
- [x] Rescate de Brochures PDF y normalización de duraciones.

### Fase 12: Inteligencia de Recomendación y Social Proof [x] Completado
- [x] Sistema de Ratings y Reviews operativo en Supabase y Web.
- [x] Motor de Recomendación por Categoría verificado.

### Fase 13: Escalamiento Nacional e Infraestructura [x] Completado
1. **Nivel 1: Descubrimiento (Monthly Discovery)** [x] Completado
   - [x] `scripts/core/discovery_institutions.py`: Crawler funcional y conectado a Supabase.
2. **Nivel 2: Carga Maestra (Weekly Master Load)** [x] Completado
   - [x] `scripts/core/master_orchestrator.py`: Balanceador de carga certificado.
3. **Nivel 3: Integridad (Daily Integrity Ping)** [x] Completado
   - [x] `scripts/core/integrity_ping.py`: Motor 404 con lógica de gracia de 3 días operativo.
4. **Optimización de Búsqueda (Fuzzy Search)** [x] Completado
   - [x] Búsqueda difusa activa en producción.

### Fase 14: Garantía de Calidad y Humo de Datos [x] Completado
- [x] Auditoría de 14 pilares y eliminación de data acumulada en UI.

### Fase 15: Testeo de Usuario y Funcionalidad E2E [x] Completado
- [x] Corregido bug de botón de reseñas y habilitadas políticas RLS.

### Fase 16: Saneamiento de Huérfanos y Expansión Taxonómica [x] Completado
- [x] Implementadas 5 categorías: Finanzas, Ingeniería, Arte, Derecho, Marketing.
- [x] Cero cursos en categoría 'General'. Catálogo 100% autónomo.

### Fase 17: Refinamiento UX y Comparativa Avanzada [x] Completado
...
### Fase 18: Inteligencia Financiera (ROI & Salarios) [x] Completado
1. **Matriz de Salarios de Mercado (Perú 2026)** [x] Completado.
2. **Motor de Inferencia de Nivel de Curso** [x] Completado (Jr/Mid/Sr poblados).
3. **Automatización del Cálculo de ROI** [x] Completado (Fórmula dinámica activa).
4. **UI de Transparencia Financiera** [x] Completado (Nota de fuente de datos integrada).

### Fase 19: Auditoría de Coherencia y Calidad Final [x] Completado
- Acción: Ejecutado `taxonomy_roi_audit.py`. Reducción de 140 a 0 inconsistencias.
- Resultado: Catálogo 100% veraz y sincronizado para producción.

## Fase 20: Certificación de Producción Autónoma [x] Completado
1. **Saneamiento Quirúrgico**: Truncado de tablas `courses`, `institutions`, `leads`, `ratings`, `reviews` (Preservando `market_salaries` y `categories`). [x] Completado
2. **Descubrimiento Nacional (Nivel 1)**: Ejecución de `discovery_institutions.py` para identificar ~10 nuevos cursos/instituciones. [x] Completado
3. **Desarrollo de Harvesters (Nivel 2)**: Creación e implementación de scrapers específicos para la muestra descubierta. [x] Completado
4. **Orquestación y Enriquecimiento**: Ejecución del `master_orchestrator.py` y `llm_enrichment_worker.py` para la muestra. [x] Completado
5. **Auditoría Final de Integridad**: Validar 0 inconsistencias y 100% de coherencia financiera/taxónomica. [x] Completado
6. **Firma Digital**: Certificación final de la arquitectura y despliegue en entornos productivos. [x] Completado

## Fase 22: Automatización de Producción (Golden Pipeline) [x] Completado
1. **Infraestructura de GitHub Actions**:
   - [x] Crear `.github/workflows/production_pipeline.yml` con 3 niveles de ejecución. [x] Completado
   - [x] Configurar schedules: Diario (05:00), Semanal (Dom 02:00), Mensual (1ero 00:00). [x] Completado
2. **Motor de Ejecución en Paralelo**:
   - [x] Crear `scripts/core/worker_runner.py` para consumo dinámico de la matriz. [x] Completado
   - [x] Validar compatibilidad de Harvesters con entorno headless. [x] Completado
3. **Persistencia y Seguridad**:
   - [x] Documentar requerimiento de Secrets (SUPABASE_SERVICE_ROLE_KEY). [x] Completado
   - [x] Habilitar `pg_trgm` en base de datos de producción. [x] Completado

## Fase 23: Rebranding Total a StudIAMatch [x] Completado
1. **Identidad Visual y Textual**:
   - [x] Actualizar `README.md` con la nueva narrativa de marca StudIAMatch. [x] Completado
   - [x] Actualizar `IMPLEMENTATION_PLAN.md` y documentos de arquitectura. [x] Completado
   - [x] Reemplazo masivo de "Yachachiy" por "StudIAMatch" en todo el codebase (scripts, web, tests). [x] Completado
2. **Componentes UI (Web)**:
   - [x] Actualizar Logo de "Yachachiy" a diseño "SM". [x] Completado
   - [x] Actualizar títulos de página, meta-tags y textos de footer/header. [x] Completado
   - [x] Ajustar gradientes o colores si es necesario para la nueva identidad. [x] Completado
3. **Persistencia y Pipelines**:
   - [x] Actualizar nombres de servicios en scripts y logs. [x] Completado
   - [x] Verificar que no queden referencias en comentarios o documentación técnica. [x] Completado

## Fase 24: Rediseño Minimalista y Compacto [x] Completado
1. **Header & Navigation**:
   - [x] Reducir altura del Header y optimizar branding. [x] Completado
   - [x] Tipografía más nítida y espaciado compacto. [x] Completado
2. **Hero Section (Concepto StudIAMatch)**:
   - [x] Rediseño minimalista del Hero con el slide "StudIAMatch · Data-driven decisions". [x] Completado
   - [x] Mejora de la barra de búsqueda (más compacta y moderna). [x] Completado
3. **Catálogo y Filtros**:
   - [x] Optimizar sidebar de filtros para que sea más sutil y funcional. [x] Completado
   - [x] Nuevas tarjetas de curso minimalistas con mejor jerarquía visual. [x] Completado
4. **Footer & Secciones Informativas**:
   - [x] Compactar Footer manteniendo enlaces clave. [x] Completado
   - [x] Pulir secciones "Cómo Funciona" y "Nosotros" con estética plana y moderna. [x] Completado

## Fase 25: Validación Funcional E2E [x] Completado
1. **Auditoría de Navegación**: Validar scroll suave y anclas de Header. [x] Completado
2. **Test de Detalle de Curso**: Verificar sección de ROI y formulario de captura. [x] Completado
3. **Auditoría de Marca**: Confirmar 0 residuos de marca anterior en UI. [x] Completado
4. **Generación de Reporte**: Documentar hallazgos en `docs/qa-engineer/`. [x] Completado

## Fase 26: Auditoría de Rutas y Coherencia v2 [x] Completado
1. **Validación de Rutas Dinámicas**: Confirmar formato `/courses/[institution]/[slug]` en Home y Detalle. [x] Completado
2. **QA de Integridad de Datos**: Ejecutar `quality_assurance_audit.py` para coherencia en BD. [x] Completado
3. **Pruebas de Carga Directa**: Validar rutas específicas (ej: upc/psicologia). [x] Completado
4. **Actualización de E2E**: Ajustar `mobile_usability.spec.ts` para nuevas rutas y ejecutar. [x] Completado
5. **Reporte Final**: Generar `docs/qa-engineer/reporte_funcionalidad_v2.md`. [x] Completado

## Fase 27: Resolución de Colisión de Slugs e Infraestructura de Rutas [x] Completado
1. **Rediseño de Esquema de URLs**: Migración de `/courses/[slug]` a `/courses/[institution]/[slug]` para garantizar unicidad. [x] Completado
2. **Refactorización de Componentes**:
   - [x] `CourseDetailClient.tsx`: Búsqueda dual por slug de curso e institución. [x] Completado
   - [x] `page.tsx` (Home): Construcción dinámica de enlaces con `institution_slug`. [x] Completado
   - [x] `compare/page.tsx`: Actualización de enlaces de "Ver Detalle". [x] Completado
3. **Optimización de Backend (Scripts)**:
   - [x] `scripts/shared/utils.py`: Mejora de `slugify` con soporte Unicode/NFD para tildes y ñ. [x] Completado
   - [x] `UniversalHarvester`: Integración de la nueva lógica de saneamiento de slugs. [x] Completado
4. **Validación de Datos**: Confirmación de que el 100% de los cursos auditados poseen la relación necesaria con su institución para el nuevo ruteo. [x] Completado

## Fase 28: Robustez de API y Manejo de Errores [x] Completado
1. **Saneamiento de Fetches en Cliente**:
   - [x] `CourseDetailClient.tsx`: Implementado escape de parámetros con `encodeURIComponent` en todas las rutas de API.
   - [x] Implementada lógica `try-catch` robusta con validación de estados `response.ok`.
2. **Optimización de Búsqueda Parcial**:
   - [x] Corregida sintaxis de `ilike` para PostgREST (uso de `*` como comodín en lugar de `%` en la URL).
3. **Validación de Datos en Social Proof**:
   - [x] Añadida validación de nulidad para `category_id` y manejo de arrays vacíos en recomendaciones.

## Fase 29: Auditoría de De-duplicación e Integridad de URLs [x] Completado
1. **Filtro de Unicidad en Frontend**: Implementada lógica en `page.tsx` para de-duplicar por `(institution, url)`. [x] Completado
2. **Sistema de Priorización**: En caso de duplicidad, se selecciona automáticamente el registro tipo 'Programa' sobre 'Curso'. [x] Completado
3. **Búsqueda Resiliente (Multi-Strategy Lookup)**: Implementada lógica en `CourseDetailClient` que busca por (1) Slug exacto, (2) Coincidencia en URL y (3) Búsqueda difusa. Esto soluciona problemas de tildes o caracteres corruptos en la DB. [x] Completado
4. **Auditoría de Salud de Rutas**: Ejecutado script de integridad validando que el 100% de las rutas dinámicas resuelven correctamente sin errores "Lo sentimos...". [x] Completado
5. **Reporte Formal**: Actualizado `docs/qa-engineer/reporte_duplicidad_integridad.md`. [x] Completado

### Fase 30: Automatización Core Flow (CI/CD + AI) [x] COMPLETADO
1. **Investigación de Costos LLM**: Cloudflare (10k neurons gratis) vs GitHub Models. [x] Completado.
2. **Infraestructura de GitHub Actions**:
   - [x] `.github/workflows/daily_ingestion.yml` activo en rama `desarrollo`.
   - [x] Secrets configurados en Environment `Development`.
3. **Estrategia "Data Drip" (IA Multi-Cloud)**:
   - [x] Límite dinámico (100 cursos: 50 CF + 50 GH/Gemini).
   - [x] Filtro de calidad (Min 150 chars en descripción).
   - [x] Fallback automático anti-429 (Cloudflare -> GitHub -> Gemini).

### Fase 31: Estabilización TIER 1 (Desarrollo) [x] COMPLETADO
- [x] Configuración de Environments en GitHub.
- [x] Validación de 100% de éxitos en batch de enriquecimiento (Triple-Cloud).
- [x] Estabilización Visual (JSON parsing & Unicode) en `CourseDetailClient.tsx`
- [x] Configuración de Pipeline Automático Zero-Touch (Root: /web, Output: out)
- [x] Limpieza y Documentación de Tier 1 completada

### Fase 31.5: Configuración de Visualización y Taxonomía [x] COMPLETADO
- [x] Guía paso a paso para Cloudflare Dashboard.
- [x] Validación de estructura URL oficial: `/courses/[institution]/[slug]`.
- [x] Eliminación de colisiones de rutas antiguas (`[slug]`).
- [x] Despliegue automático 100% verificado en Cloudflare.

## Fase 32: Migración de Datos y Esquema [ ] Pendiente
1. **Sincronización de Esquema** (DB Migration)
   - Acción: Usar `supabase db pull` del proyecto actual y `supabase db push` al nuevo.
   - Dependencias: Fase 31.
   - Riesgo: Medio (Validar RLS y extensiones como `pg_trgm`).
2. **Migración de Datos Maestros** (SQL / CSV)
   - Acción: Migrar tablas de referencia: `categories`, `market_salaries`.
   - Acción: Migrar datos operativos sanitizados: `institutions`, `courses`.
3. **Auditoría de Integridad en Producción** (Script)
   - Acción: Ejecutar `quality_assurance_audit.py` apuntando al nuevo proyecto.

## Fase 33: Dominios y Cloudflare (studiamatch.com) [ ] Pendiente
1. **Configuración de Cloudflare Pages**:
   - `main branch` -> Dominio: `studiamatch.com` (Vía Hostinger CNAME/A).
   - `certificacion branch` -> Dominio: `cert.studiamatch.com` o similar.
   - `desarrollo branch` -> Dominio: `studiamatch.pages.dev`.
2. **Propagación DNS y SSL**:
   - Acción: Validar certificados SSL gestionados por Cloudflare para los 3 niveles.
   - Acción: Configurar redireccionamientos de seguridad HSTS.
3. **Custom Domain en Supabase**:
   - Acción: Configurar Custom Domain en Supabase para `db.studiamatch.com` (Opcional, Pro feature).
4. **Optimización de Seguridad y Performance** (Cloudflare)
   - Acción: Habilitar Proxy (naranja), SSL Full (Strict), y reglas de WAF básicas.
   - Acción: Configurar redirección de `www` a non-www.

## Fase 34: Lanzamiento y Certificación Final [ ] Pendiente
1. **Smoke Tests en Producción** (Web)
   - Acción: Validar flujo completo desde Home hasta Detalle y Social Proof en el dominio final.
2. **Activación de Pipelines Automáticos** (GitHub Actions)
   - Acción: Habilitar los flujos de `daily_ingestion.yml` apuntando al entorno de producción.
3. **Cierre de Ciclo y Documentación** (Docs)
   - [x] Generadas guías de despliegue por ambiente en `docs/deployment/`. [x] Completado

## Fase 35: Reingeniería de Calidad de Datos (Raw Harvesting) [x] Completado
1. **Infraestructura de Staging**:
   - [x] Crear tabla `harvesting` para almacenamiento de data bruta (URL, HTML, Metatags). [x] Completado
   - [x] Implementar estados: `pending`, `processed`, `discarded`, `error`. [x] Completado
2. **Refactor de Universal Harvester**:
   - [x] Separar lógica de descubrimiento de la de guardado final. [x] Completado
   - [x] Guardar data "en bruto" en `harvesting` sin normalización agresiva. [x] Completado
   - [x] Optimización de Gran Volumen (Capacidad 500,000 chars). [x] Completado
3. **Desarrollo del Processor Intelligen (The Curator)**:
   - [x] Crear `scripts/core/harvest_processor.py` para depuración quirúrgica. [x] Completado
   - [x] Implementar heurística anti-slogan (detectar "Descubre nuestras carreras", "404", etc.). [x] Completado
   - [x] Flujo de promoción: `harvesting` -> Enriquecimiento -> `courses`. [x] Completado
4. **Validación de la Muestra en Conflictos**:
   - [x] Re-procesar URL de UPC Marketing para validar limpieza automática del nombre. [x] Completado

## Fase 36: Pipeline de Datos de Alta Fidelidad (4 Estaciones) [x] Completado

Esta fase reemplaza y consolida la anterior estrategia de harvesting, implementando un flujo ETL (Extract, Transform, Load) de grado industrial.

### 🚉 Las 4 Estaciones del Dato
1.  **Estación 1: `staging_raw` (Harvesting)**:
    - [x] Motor de descubrimiento masivo (Sitemaps + BFS Crawl). [x] Completado
    - [x] Almacenamiento de HTML bruto (Límite 500k chars). [x] Completado
    - [x] Casos de éxito: **UTP (100 URLs)** y **DMC (100 URLs)**. [x] Completado
2.  **Estación 2: `cleansed_programs` (Cleansing)**:
    - [x] Script `cleansing_worker.py` funcional. [x] Completado
    - [x] Ejecutar limpieza masiva para DMC/UTP (Eliminar slogans y duplicados). [x] Completado
    - [x] Deduplicación multi-sede activa. [x] Completado
3.  **Estación 3: `enriched_programs` (Enrichment - IA)**:
    - [x] **Implementación de IA Real** (OpenAI/Gemini) en `enrichment_worker.py`. [x] Completado
    - [x] Extracción obligatoria de los **14 Pilares de Metadata**. [x] Completado
4.  **Estación 4: `courses` (Production & Vector Sync)**:
    - [x] Script `sync_vector_worker.py` base. [x] Completado
    - [x] Generación de Embeddings para búsqueda semántica. [x] Completado
    - [x] Publicación final en la Web. [x] Completado

### 🚀 Estado Actual: "Consolidación de Estaciones ETL Completada"
- Las 4 estaciones están integradas y funcionales en producción.

## Fase 37: Estabilización de Pipeline y Producción (Oficial 5 Fases) [x] Finalizado
**Estado**: Operativo y Automatizado.
- [x] **Estandarización de Secretos**: Todas las variables movidas a `SUPABASE_URL` y `SUPABASE_KEY` (Fix total de error `None URL`).
- [x] **Fase 0 (Inventory)**: Activado `discovery_institutions.py` para alimentar el catálogo maestro.
- [x] **Fase 1 (Massive Harvesting)**: Re-activado `master_orchestrator.py` con límites de 150 URLs (Anti-timeout).
- [x] **Fase 2 (Multicloud Enrichment)**: Implementado `enrichment_worker.py` con cascada CF -> GitHub -> Gemini.
- [x] **Fase 3 (Production Sync)**: Activado `sync_vector_worker.py` con slugs persistentes.
- [x] **Fase 4 (ROI-QA Audit)**: Integración final de auditoría de calidad de datos en cada carrera.
- [x] **Golden Pipeline**: YAML optimizado a 5 Jobs secuenciales para máxima trazabilidad.

## Fase 38: Refactorización de universal_harvester.py (Estrategia Stealth Harvesting FG2) [x] Completado
El objetivo fue transformar el harvester en un motor de alta resiliencia y sigilo capaz de alimentar el "cerebro" de la plataforma con +20k registros sin disparar bloqueos de WAFs avanzados (Akamai/Cloudflare).

1. **Protocolo de Sigilo (Stealth) y Evasión**:
   - [x] **Suplantación TLS (JA3/JA4)**: Sustituir `aiohttp` por `curl_cffi` para mimetizar la huella TLS de navegadores reales. [x] Completado
   - [x] **Coherencia de Headers**: Implementar rotación de `User-Agent` sincronizada con headers `Sec-CH-UA` y firma TLS. [x] Completado
   - [ ] **Soporte de Proxies**: Configurar pool de Proxies Residenciales Rotativos para distribución de IPs. (Pendiente para escalamiento masivo).
2. **Resiliencia y Concurrencia Responsable**:
   - [x] **Semáforos por Dominio**: `asyncio.Semaphore(3)` para limitar la carga por servidor. [x] Completado
   - [x] **Delays Adaptativos (Jitter)**: Pausas aleatorias de 2-5s entre peticiones. [x] Completado
   - [x] **Patrón Circuit Breaker**: Abortar automáticamente el scraping de una institución tras 3 errores 403/429 consecutivos. [x] Completado
3. **Checkpointing Inmediato y Persistencia**:
   - [x] **Estado 'Discovered'**: Persistir URLs en `staging_raw` inmediatamente tras el descubrimiento (Sitemap/BFS) para evitar re-escaneos. [x] Completado
   - [x] **Gestión de Chunks**: Procesar la cola de extracción en lotes atómicos que permitan reanudación tras fallos. [x] Completado
4. **Optimización de Datos (Delta Scraping)**:
   - [x] **Content Hashing**: Solo ejecutar `Upsert` si el hash del contenido limpio ha cambiado. [x] Completado
   - [x] **Sanitización de Backlog**: Implementada lógica `_load_existing_urls` para saltar el descubrimiento de URLs que ya existen en la DB. [x] Completado

## Fase 39: Reingeniería y Afinación del Cleansing Worker (Estación 1.5) [x] Completado
Objetivo: Transformar `cleansing_worker.py` en un filtro de alta fidelidad con motor de exclusión por institución, consolidación de sedes y limpieza profunda de HTML.

1. **Infraestructura de Datos**:
   - [x] **Tabla de Exclusión**: Crear `crawler_exclusions` para filtrar URLs por patrón (ej. /noticias/, /becas/). [x] Completado
   - [x] **Autogeneración de IDs**: Habilitar `gen_random_uuid()` por defecto en `cleansed_programs`. [x] Completado
2. **Refactorización del Worker (Afinación Quirúrgica)**:
   - [x] **Motor de Exclusión Inteligente**: Cargar reglas de `crawler_exclusions` en el worker para validación por patrón absoluto. [x] Completado
   - [x] **Limpieza Profunda (BeautifulSoup)**: Eliminación de `<head>`, `<header>`, `<footer>`, `<nav>` y elementos con clases de ruido (`menu, sidebar, social`). [x] Completado
   - [x] **Detección de Soft 404**: Bloqueo automático de páginas que cargan pero indican "Página no encontrada". [x] Completado
   - [x] **Filtro de Caducidad Histórica**: Descarte de contenido con años obsoletos (2018-2024) en URL o texto. [x] Completado
   - [x] **Consolidación de Sibling Pages**: Agrupación de sub-páginas (Beneficios, Plana, Malla) en un único registro maestro (1:1). [x] Completado
3. **Mantenimiento y Saneamiento**:
   - [x] **Truncado de Plata**: Limpiar `cleansed_programs` para eliminar data con ruido anterior. [x] Completado
   - [x] **Re-procesamiento Masivo**: Resetear `staging_raw` a 'pending' y ejecutar la nueva lógica sobre los +1,000 registros. [x] Completado

**Resultado Final:** ~156 programas académicos puros de alta fidelidad promovidos (Reducción de >70% de ruido).

## Fase 39.1: De-duplicación Inteligente por Redirección y Canonical [/] Pendiente de Revisión
Objetivo: Resolver el problema de múltiples rutas apuntando al mismo contenido (caso New Horizons) capturando la "Fuente de Verdad" técnica definida por el servidor y SEO.

1. **Infraestructura de Datos (SQL)**:
   - [ ] **Esquema de Alta Fidelidad**: Añadir columnas `effective_url` y `canonical_url` en `staging_raw` y `cleansed_programs`.
   - [ ] **Índice Compuesto**: Migrar el índice UNIQUE de `cleansed_programs` a la tupla `(institution_id, effective_url)` para evitar colisiones entre instituciones.
2. **Refactorización de Captura (Harvester)**:
   - [ ] **Captura de URL Final**: Almacenar `response.url` tras redirecciones automáticas de `curl_cffi` o Playwright.
   - [ ] **Extracción de Canonical**: Implementar regex/BeautifulSoup para extraer `<link rel="canonical">` como prioridad de de-duplicación.
3. **Lógica de Consolidación (Cleanser)**:
   - [ ] **Normalización Robusta**: Implementar `normalize_url` para remover query strings, fragmentos y unificar el `trailing slash`.
   - [ ] **Pivot de Agrupación**: Cambiar la lógica de consolidación para que use `canonical_url` (prioridad) o `effective_url` (fallback) como clave de unión.
   - [ ] **Trazabilidad de Linaje**: Registrar `sibling_staging_ids` en los metadatos para auditar qué URLs originales fueron "comprimidas".
4. **Certificación y Sanity Check**:
   - [ ] **Test de New Horizons**: Validar que las rutas divergentes de TOGAF se fusionen en un único registro maestro.
   - [ ] **Validación de Fallback**: Confirmar el uso de `COALESCE` para operar con URLs originales si no hay redirección detectada.

## Fase 40: Refactorización de Infraestructura CI/CD [/] En curso
Objetivo: Migrar el pipeline monolítico hacia un sistema de 3 flujos atómicos (Mensual, Semanal, Diario) para optimizar costos de computación y mejorar la observabilidad en la nube.

1. **Estructura de Workflows (GitHub Actions)**:
   - [x] **FG1 - Institution Inventory**: Flujo mensual para descubrimiento de nuevas semillas (`fg1_inventory.yml`). [x] Completado
   - [x] **FG2 - Golden Pipeline**: Flujo semanal de alto volumen con jobs secuenciales aislados (`production_pipeline.yml`). [x] Completado
   - [x] **FG3 - Integrity Management**: Flujo diario ligero para validación de 404s (`fg3_integrity.yml`). [x] Completado
2. **Observabilidad y Resiliencia**:
   - [x] **Jobs Secuenciales**: Separación de 'Harvesting' y 'Cleansing' en jobs independientes para identificar cuellos de botella. [x] Completado
   - [x] **Delegación del Orquestador**: Modificación de `master_orchestrator.py` para permitir la delegación de fases a GitHub Actions vía flags (`--skip-cleansing`). [x] Completado
3. **Mantenimiento y Protocolo Local -> Nube (Smart Sync)**:
   - [ ] **Protocolo de Sincronización**: Automatización del flujo de subida de cambios locales a Supabase Free.
     1. Ejecutar `python scripts/local/maintenance/sync_local_to_cloud.py`.
     2. El script detectará diferencias y realizará **Bulk Upserts** vía API REST (evitando el colapso del navegador por SQL pesado).
     3. Confirmar en el Dashboard de Supabase que los registros (especialmente `cleansed_programs`) se han actualizado sin duplicados.
   - [ ] **Esquema Estructural**: Para cambios en la estructura de tablas (DDL), utilizar el bloque SQL ligero de la arquitectura y ejecutarlo en el SQL Editor (Frecuencia: Solo cuando cambien los campos).

## Riesgos y Mitigaciones
- **Riesgo**: Bloqueos persistentes de IP local. -> Mitigación: Uso obligatorio de Proxies Residenciales y TLS Impersonation.
- **Riesgo**: Inestabilidad de `curl_cffi` en CI. -> Mitigación: Mantener `aiohttp` como fallback con headers básicos.
- **Riesgo**: Saturación de DB por inserts masivos de descubrimiento. -> Mitigación: Batch inserts para el estado 'discovered'.