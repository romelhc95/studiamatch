# Plan de Implementación: StudIAMatch - Tech Education Intelligence

## Premisas Obligatorias de Ingenierí­a (Nivel 0)

> [!IMPORTANT]
> **Documentación de Referencia (Golden Pipeline)**: El diseño arquitectónico, el flujo ETL de 4 estaciones y el diccionario de datos maestro se rigen estrictamente por lo definido en [docs/architecture/Documento_Detallado_workflow](docs/architecture/Documento_Detallado_workflow). Este documento es la "íšnica Fuente de Verdad" para la lógica de datos.
>
> **Aislamiento Total y Paridad Linux**: Queda estrictamente prohibido ejecutar comandos de desarrollo (npm, python, audit) directamente en el host Windows. 
> Todo comando **DEBE** ser ejecutado dentro del contenedor `studiamatch-dev` (Debian) para garantizar la paridad del 100% con los servidores de despliegue (Cloudflare/Linux).
>
> **Comando Base Mandatorio**:
> `docker exec -it studiamatch-dev [comando]`

## Estado Actual del Proyecto (WORKING-CONTEXT)
- **Estado Actual**: Fase 2.0 (TIER 2 - Certificación) âœ… CERTIFICADO.
- **íšltimo Hito**: Consolidación de pipelines de datos y reingenierí­a de calidad.
- **Próxima Acción**: Implementar de-duplicación inteligente por Redirección y Canonical (Fase 39.1).

## Hoja de Ruta: Lanzamiento Producción
- [ ] **Migración de Schema**: Replicar tablas, RLS e í­ndices en el proyecto Pro.
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
2.  **Pull Request a `desarrollo`**: Revisión tí©cnica y validación de scripts en el sandbox actual.
3.  **Promoción a `certificacion`**: Ejecución obligatoria de la Suite E2E (`Playwright`) y Auditorí­a de Integridad de Datos.
4.  **Merge a `main`**: Despliegue automático a producción (Supabase Pro) tras aprobación del @SDLC-Chief.

---

## Arquitectura de Ejecución (Macro-Estrategia)
La ejecución del sistema se divide en 3 Fases Generales (FG) para optimizar costos, eficiencia y responsabilidades:

* **FG1: Mapeo Institucional (Frecuencia: Mensual)**
  - **Objetivo**: Descubrir y registrar nuevas universidades e institutos licenciados por MINEDU.
  - **Script Principal**: `register_institution.py` (o procesos de Nivel 1).
* **FG2: Carga Masiva y Delta Scraping (Frecuencia: Semanal)**
  - **Objetivo**: Extracción exhaustiva del catálogo de cursos. La carga inicial obtiene toda la información de las webs institucionales. Las ejecuciones posteriores aplican "Delta Scraping" (mediante Hashing) para extraer y procesar *solo* lo nuevo o modificado, reduciendo radicalmente el costo.
  - **Flujo de Scripts**: `universal_harvester.py` -> `cleansing_worker.py` -> `enrichment_worker.py` -> `sync_vector_worker.py` -> auditorí­as.
* **FG3: Integridad y Periodo de Gracia (Frecuencia: Diaria)**
  - **Objetivo**: Validar la disponibilidad de los enlaces existentes (404).
  - **Mecanismo**: Comprobar si el curso sigue activo. Si falla, entra en un "Periodo de Gracia" de 3 dí­as antes de inactivarse. Esto desliga al harvester de la verificación diaria.
  - **Script Principal**: `integrity_ping.py`.

## Arquitectura del Cerebro de Datos (Flujo ETL Histórico)
1. **Descubrimiento (The Explorer)** [x] Completado.
2. **Harvesting de URLs (The Collector)** [x] Completado.
3. **Extracción de Data Bruta (Deep Scrape)** [x] Completado.
4. **Enriquecimiento IA/LLM (The Brain)** [x] Completado.
5. **Quality Guard (Auditorí­a Aleatoria)** [x] Completado (Salud del catálogo certificada al 100%).
6. **Taxonomí­a Automática (Motor de Reglas)** [x] Completado.
7. **Visualización UX (Next.js 15)** [x] Completado (Detalle de 14 pilares y Social Proof funcionales).

## Estructura de Scripts (Producción)
Jerarquí­a organizada para garantizar el mantenimiento y balanceo de carga:
- `scripts/core/`: Orquestación, Universal Harvester (FG2) y Mapeo (FG1).
- `scripts/harvesters/`: Scrapers especí­ficos por institución.
- `scripts/maintenance/`: Auditorí­a de calidad y Ping de integridad 404/Gracia (FG3).
- `scripts/legacy/`: Historial de desarrollo y scripts de un solo uso.

## Pasos de Implementación

### Fase 1 a 10: Cimentación y Rediseño [x] Completado
- Todas las tareas certificadas.

### Fase 11: Escalamiento Progresivo y Triaje [x] Completado
- [x] Rescate de Brochures PDF y normalización de duraciones.

### Fase 12: Inteligencia de Recomendación y Social Proof [x] Completado
- [x] Sistema de Ratings y Reviews operativo en Supabase y Web.
- [x] Motor de Recomendación por Categorí­a verificado.

### Fase 13: Escalamiento Nacional e Infraestructura [x] Completado
1. **Nivel 1: Descubrimiento (Monthly Discovery)** [x] Completado
   - [x] `scripts/core/discovery_institutions.py`: Crawler funcional y conectado a Supabase.
2. **Nivel 2: Carga Maestra (Weekly Master Load)** [x] Completado
   - [x] `scripts/core/master_orchestrator.py`: Balanceador de carga certificado.
3. **Nivel 3: Integridad (Daily Integrity Ping)** [x] Completado
   - [x] `scripts/core/integrity_ping.py`: Motor 404 con lógica de gracia de 3 dí­as operativo.
4. **Optimización de Búsqueda (Fuzzy Search)** [x] Completado
   - [x] Búsqueda difusa activa en producción.

### Fase 14: Garantí­a de Calidad y Humo de Datos [x] Completado
- [x] Auditorí­a de 14 pilares y eliminación de data acumulada en UI.

### Fase 15: Testeo de Usuario y Funcionalidad E2E [x] Completado
- [x] Corregido bug de botón de reseñas y habilitadas polí­ticas RLS.

### Fase 16: Saneamiento de Huí©rfanos y Expansión Taxonómica [x] Completado
- [x] Implementadas 5 categorí­as: Finanzas, Ingenierí­a, Arte, Derecho, Marketing.
- [x] Cero cursos en categorí­a 'General'. Catálogo 100% autónomo.

### Fase 17: Refinamiento UX y Comparativa Avanzada [x] Completado
...
### Fase 18: Inteligencia Financiera (ROI & Salarios) [x] Completado
1. **Matriz de Salarios de Mercado (Perú 2026)** [x] Completado.
2. **Motor de Inferencia de Nivel de Curso** [x] Completado (Jr/Mid/Sr poblados).
3. **Automatización del Cálculo de ROI** [x] Completado (Fórmula dinámica activa).
4. **UI de Transparencia Financiera** [x] Completado (Nota de fuente de datos integrada).

### Fase 19: Auditorí­a de Coherencia y Calidad Final [x] Completado
- Acción: Ejecutado `taxonomy_roi_audit.py`. Reducción de 140 a 0 inconsistencias.
- Resultado: Catálogo 100% veraz y sincronizado para producción.

### Fase 20: Certificación de Producción Autónoma [x] Completado
1. **Saneamiento Quirúrgico**: Truncado de tablas `courses`, `institutions`, `leads`, `ratings`, `reviews` (Preservando `market_salaries` y `categories`). [x] Completado
2. **Descubrimiento Nacional (Nivel 1)**: Ejecución de `discovery_institutions.py` para identificar ~10 nuevos cursos/instituciones. [x] Completado
3. **Desarrollo de Harvesters (Nivel 2)**: Creación e implementación de scrapers especí­ficos para la muestra descubierta. [x] Completado
4. **Orquestación y Enriquecimiento**: Ejecución del `master_orchestrator.py` y `llm_enrichment_worker.py` para la muestra. [x] Completado
5. **Auditorí­a Final de Integridad**: Validar 0 inconsistencias y 100% de coherencia financiera/taxónomica. [x] Completado
6. **Firma Digital**: Certificación final de la arquitectura y despliegue en entornos productivos. [x] Completado

### Fase 21: Automatización de Producción (Golden Pipeline) [x] Completado
1. **Infraestructura de GitHub Actions**:
   - [x] Crear `.github/workflows/production_pipeline.yml` con 3 niveles de ejecución. [x] Completado
   - [x] Configurar schedules: Diario (05:00), Semanal (Dom 02:00), Mensual (1ero 00:00). [x] Completado
2. **Motor de Ejecución en Paralelo**:
   - [x] Crear `scripts/core/worker_runner.py` para consumo dinámico de la matriz. [x] Completado
   - [x] Validar compatibilidad de Harvesters con entorno headless. [x] Completado
3. **Persistencia y Seguridad**:
   - [x] Documentar requerimiento de Secrets (SUPABASE_SERVICE_ROLE_KEY). [x] Completado
   - [x] Habilitar `pg_trgm` en base de datos de producción. [x] Completado

### Fase 22: Rebranding Total a StudIAMatch [x] Completado
1. **Identidad Visual y Textual**:
   - [x] Actualizar `README.md` con la nueva narrativa de marca StudIAMatch. [x] Completado
   - [x] Actualizar `IMPLEMENTATION_PLAN.md` y documentos de arquitectura. [x] Completado
   - [x] Reemplazo masivo de "Yachachiy" por "StudIAMatch" en todo el codebase (scripts, web, tests). [x] Completado
2. **Componentes UI (Web)**:
   - [x] Actualizar Logo de "Yachachiy" a diseño "SM". [x] Completado
   - [x] Actualizar tí­tulos de página, meta-tags y textos de footer/header. [x] Completado
   - [x] Ajustar gradientes o colores si es necesario para la nueva identidad. [x] Completado
3. **Persistencia y Pipelines**:
   - [x] Actualizar nombres de servicios en scripts y logs. [x] Completado
   - [x] Verificar que no queden referencias en comentarios o documentación tí©cnica. [x] Completado

### Fase 23: Rediseño Minimalista y Compacto [x] Completado
1. **Header & Navigation**:
   - [x] Reducir altura del Header y optimizar branding. [x] Completado
   - [x] Tipografí­a más ní­tida y espaciado compacto. [x] Completado
2. **Hero Section (Concepto StudIAMatch)**:
   - [x] Rediseño minimalista del Hero con el slide "StudIAMatch Â· Data-driven decisions". [x] Completado
   - [x] Mejora de la barra de búsqueda (más compacta y moderna). [x] Completado
3. **Catálogo y Filtros**:
   - [x] Optimizar sidebar de filtros para que sea más sutil y funcional. [x] Completado
   - [x] Nuevas tarjetas de curso minimalistas con mejor jerarquí­a visual. [x] Completado
4. **Footer & Secciones Informativas**:
   - [x] Compactar Footer manteniendo enlaces clave. [x] Completado
   - [x] Pulir secciones "Cómo Funciona" y "Nosotros" con estí©tica plana y moderna. [x] Completado

### Fase 24: Validación Funcional E2E [x] Completado
1. **Auditorí­a de Navegación**: Validar scroll suave y anclas de Header. [x] Completado
2. **Test de Detalle de Curso**: Verificar sección de ROI y formulario de captura. [x] Completado
3. **Auditorí­a de Marca**: Confirmar 0 residuos de marca anterior en UI. [x] Completado
4. **Generación de Reporte**: Documentar hallazgos en `docs/qa-engineer/`. [x] Completado

### Fase 25: Auditorí­a de Rutas y Coherencia v2 [x] Completado
1. **Validación de Rutas Dinámicas**: Confirmar formato `/courses/[institution]/[slug]` en Home y Detalle. [x] Completado
2. **QA de Integridad de Datos**: Ejecutar `quality_assurance_audit.py` para coherencia en BD. [x] Completado
3. **Pruebas de Carga Directa**: Validar rutas especí­ficas (ej: upc/psicologia). [x] Completado
4. **Actualización de E2E**: Ajustar `mobile_usability.spec.ts` para nuevas rutas y ejecutar. [x] Completado
5. **Reporte Final**: Generar `docs/qa-engineer/reporte_funcionalidad_v2.md`. [x] Completado

### Fase 26: Resolución de Colisión de Slugs e Infraestructura de Rutas [x] Completado
1. **Rediseño de Esquema de URLs**: Migración de `/courses/[slug]` a `/courses/[institution]/[slug]` para garantizar unicidad. [x] Completado
2. **Refactorización de Componentes**:
   - [x] `CourseDetailClient.tsx`: Búsqueda dual por slug de curso e institución. [x] Completado
   - [x] `page.tsx` (Home): Construcción dinámica de enlaces con `institution_slug`. [x] Completado
   - [x] `compare/page.tsx`: Actualización de enlaces de "Ver Detalle". [x] Completado
3. **Optimización de Backend (Scripts)**:
   - [x] `scripts/shared/utils.py`: Mejora de `slugify` con soporte Unicode/NFD para tildes y ñ. [x] Completado
   - [x] `UniversalHarvester`: Integración de la nueva lógica de saneamiento de slugs. [x] Completado
4. **Validación de Datos**: Confirmación de que el 100% de los cursos auditados poseen la relación necesaria con su institución para el nuevo ruteo. [x] Completado

### Fase 27: Robustez de API y Manejo de Errores [x] Completado
1. **Saneamiento de Fetches en Cliente**:
   - [x] `CourseDetailClient.tsx`: Implementado escape de parámetros con `encodeURIComponent` en todas las rutas de API.
   - [x] Implementada lógica `try-catch` robusta con validación de estados `response.ok`.
2. **Optimización de Búsqueda Parcial**:
   - [x] Corregida sintaxis de `ilike` para PostgREST (uso de `*` como comodí­n en lugar de `%` en la URL).
3. **Validación de Datos en Social Proof**:
   - [x] Añadida validación de nulidad para `category_id` y manejo de arrays vací­os en recomendaciones.

### Fase 28: Auditorí­a de De-duplicación e Integridad de URLs [x] Completado
1. **Filtro de Unicidad en Frontend**: Implementada lógica en `page.tsx` para de-duplicar por `(institution, url)`. [x] Completado
2. **Sistema de Priorización**: En caso de duplicidad, se selecciona automáticamente el registro tipo 'Programa' sobre 'Curso'. [x] Completado
3. **Búsqueda Resiliente (Multi-Strategy Lookup)**: Implementada lógica en `CourseDetailClient` que busca por (1) Slug exacto, (2) Coincidencia en URL y (3) Búsqueda difusa. Esto soluciona problemas de tildes o caracteres corruptos en la DB. [x] Completado
4. **Auditorí­a de Salud de Rutas**: Ejecutado script de integridad validando que el 100% de las rutas dinámicas resuelven correctamente sin errores "Lo sentimos...". [x] Completado
5. **Reporte Formal**: Actualizado `docs/qa-engineer/reporte_duplicidad_integridad.md`. [x] Completado

### Fase 29: Automatización Core Flow (CI/CD + AI) [x] COMPLETADO
1. **Investigación de Costos LLM**: Cloudflare (10k neurons gratis) vs GitHub Models. [x] Completado.
2. **Infraestructura de GitHub Actions**:
   - [x] `.github/workflows/daily_ingestion.yml` activo en rama `desarrollo`.
   - [x] Secrets configurados en Environment `Development`.
3. **Estrategia "Data Drip" (IA Multi-Cloud)**:
   - [x] Lí­mite dinámico (100 cursos: 50 CF + 50 GH/Gemini).
   - [x] Filtro de calidad (Min 150 chars en descripción).
   - [x] Fallback automático anti-429 (Cloudflare -> GitHub -> Gemini).

### Fase 30: Estabilización TIER 1 (Desarrollo) [x] COMPLETADO
- [x] Configuración de Environments en GitHub.
- [x] Validación de 100% de í©xitos en batch de enriquecimiento (Triple-Cloud).
- [x] Estabilización Visual (JSON parsing & Unicode) en `CourseDetailClient.tsx`
- [x] Configuración de Pipeline Automático Zero-Touch (Root: /web, Output: out)
- [x] Limpieza y Documentación de Tier 1 completada

### Fase 31: Configuración de Visualización y Taxonomí­a [x] COMPLETADO
- [x] Guí­a paso a paso para Cloudflare Dashboard.
- [x] Validación de estructura URL oficial: `/courses/[institution]/[slug]`.
- [x] Eliminación de colisiones de rutas antiguas (`[slug]`).
- [x] Despliegue automático 100% verificado en Cloudflare.

### Fase 32: Migración de Datos y Esquema [ ] Pendiente
1. **Sincronización de Esquema** (DB Migration)
   - Acción: Usar `supabase db pull` del proyecto actual y `supabase db push` al nuevo.
   - Dependencias: Fase 31.
   - Riesgo: Medio (Validar RLS y extensiones como `pg_trgm`).
2. **Migración de Datos Maestros** (SQL / CSV)
   - Acción: Migrar tablas de referencia: `categories`, `market_salaries`.
   - Acción: Migrar datos operativos sanitizados: `institutions`, `courses`.
3. **Auditorí­a de Integridad en Producción** (Script)
   - Acción: Ejecutar `quality_assurance_audit.py` apuntando al nuevo proyecto.

### Fase 33: Dominios y Cloudflare (studiamatch.com) [ ] Pendiente
1. **Configuración de Cloudflare Pages**:
   - `main branch` -> Dominio: `studiamatch.com` (Ví­a Hostinger CNAME/A).
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

### Fase 34: Lanzamiento y Certificación Final [ ] Pendiente
1. **Smoke Tests en Producción** (Web)
   - Acción: Validar flujo completo desde Home hasta Detalle y Social Proof en el dominio final.
2. **Activación de Pipelines Automáticos** (GitHub Actions)
   - Acción: Habilitar los flujos de `daily_ingestion.yml` apuntando al entorno de producción.
3. **Cierre de Ciclo y Documentación** (Docs)
   - [x] Generadas guí­as de despliegue por ambiente en `docs/deployment/`. [x] Completado

### Fase 35: Reingenierí­a de Calidad de Datos (Raw Harvesting) [x] Completado
1. **Infraestructura de Staging**:
   - [x] Crear tabla `harvesting` para almacenamiento de data bruta (URL, HTML, Metatags). [x] Completado
   - [x] Implementar estados: `pending`, `processed`, `discarded`, `error`. [x] Completado
2. **Refactor de Universal Harvester**:
   - [x] Separar lógica de descubrimiento de la de guardado final. [x] Completado
   - [x] Guardar data "en bruto" en `harvesting` sin normalización agresiva. [x] Completado
   - [x] Optimización de Gran Volumen (Capacidad 500,000 chars). [x] Completado
3. **Desarrollo del Processor Intelligen (The Curator)**:
   - [x] Crear `scripts/core/harvest_processor.py` para depuración quirúrgica. [x] Completado
   - [x] Implementar heurí­stica anti-slogan (detectar "Descubre nuestras carreras", "404", etc.). [x] Completado
   - [x] Flujo de promoción: `harvesting` -> Enriquecimiento -> `courses`. [x] Completado
4. **Validación de la Muestra en Conflictos**:
   - [x] Re-procesar URL de UPC Marketing para validar limpieza automática del nombre. [x] Completado

### Fase 36: Pipeline de Datos de Alta Fidelidad (4 Estaciones) [x] Completado

Esta fase reemplaza y consolida la anterior estrategia de harvesting, implementando un flujo ETL (Extract, Transform, Load) de grado industrial.

### Las 4 Estaciones del Dato
1.  **Estación 1: `staging_raw` (Harvesting)**:
    - [x] Motor de descubrimiento masivo (Sitemaps + BFS Crawl). [x] Completado
    - [x] Almacenamiento de HTML bruto (Lí­mite 500k chars). [x] Completado
    - [x] Casos de í©xito: **UTP (100 URLs)** y **DMC (100 URLs)**. [x] Completado
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

### Estado Actual: "Consolidación de Estaciones ETL Completada"
- Las 4 estaciones están integradas y funcionales en producción.

### Fase 37: Estabilización de Pipeline y Producción (Oficial 5 Fases) [x] Finalizado
**Estado**: Operativo y Automatizado.
- [x] **Estandarización de Secretos**: Todas las variables movidas a `SUPABASE_URL` y `SUPABASE_KEY` (Fix total de error `None URL`).
- [x] **Fase 0 (Inventory)**: Activado `discovery_institutions.py` para alimentar el catálogo maestro.
- [x] **Fase 1 (Massive Harvesting)**: Re-activado `master_orchestrator.py` con lí­mites de 150 URLs (Anti-timeout).
- [x] **Fase 2 (Multicloud Enrichment)**: Implementado `enrichment_worker.py` con cascada CF -> GitHub -> Gemini.
- [x] **Fase 3 (Production Sync)**: Activado `sync_vector_worker.py` con slugs persistentes.
- [x] **Fase 4 (ROI-QA Audit)**: Integración final de auditorí­a de calidad de datos en cada carrera.
- [x] **Golden Pipeline**: YAML optimizado a 5 Jobs secuenciales para máxima trazabilidad.

### Fase 38: Refactorización de universal_harvester.py (Estrategia Stealth Harvesting FG2) [x] Completado
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

### Fase 39: Reingenierí­a y Afinación del Cleansing Worker (Estación 1.5) [x] Completado
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

**Resultado Final:** ~156 programas acadí©micos puros de alta fidelidad promovidos (Reducción de >70% de ruido).

### Fase 39.1: De-duplicación Inteligente por Redirección y Canonical [x] Completado
Objetivo: Resolver el problema de múltiples rutas apuntando al mismo contenido (caso New Horizons) capturando la "Fuente de Verdad" tí©cnica definida por el servidor y SEO.

1. **Infraestructura de Datos (SQL)**:
   - [x] **Esquema de Alta Fidelidad**: Añadir columnas `effective_url` y `canonical_url` en `staging_raw` y `cleansed_programs`. [x] Completado
   - [x] **índice Compuesto**: Migrar el í­ndice UNIQUE de `cleansed_programs` a la tupla `(institution_id, effective_url)` para evitar colisiones entre instituciones. [x] Completado
2. **Refactorización de Captura (Harvester)**:
   - [x] **Captura de URL Final**: Almacenar `response.url` tras redirecciones automáticas de `curl_cffi` o Playwright. [x] Completado
   - [x] **Extracción de Canonical**: Implementar regex/BeautifulSoup para extraer `<link rel="canonical">` como prioridad de de-duplicación. [x] Completado
3. **Lógica de Consolidación (Cleanser)**:
   - [x] **Normalización Robusta**: Implementar `normalize_url` para remover query strings, fragmentos y unificar el `trailing slash`. [x] Completado
   - [x] **Pivot de Agrupación**: Cambiar la lógica de consolidación para que use `canonical_url` (prioridad) o `effective_url` (fallback) como clave de unión. [x] Completado
   - [x] **Trazabilidad de Linaje**: Registrar `sibling_staging_ids` en los metadatos para auditar quí© URLs originales fueron "comprimidas". [x] Completado
4. **Certificación y Sanity Check**:
   - [x] **Test de New Horizons**: Validar que las rutas divergentes de TOGAF se fusionen en un único registro maestro. [x] Completado
   - [x] **Validación de Fallback**: Confirmar el uso de `COALESCE` para operar con URLs originales si no hay redirección detectada. [x] Completado

### Fase 40: Refactorización de Infraestructura CI/CD [x] Completado
Objetivo: Migrar el pipeline monolí­tico hacia un sistema de 3 flujos atómicos (Mensual, Semanal, Diario) para optimizar costos de computación y mejorar la observabilidad en la nube.

1. **Estructura de Workflows (GitHub Actions)**:
   - [x] **FG1 - Institution Inventory**: Flujo mensual para descubrimiento de nuevas semillas (`fg1_inventory.yml`). [x] Completado
   - [x] **FG2 - Golden Pipeline**: Flujo semanal de alto volumen con jobs secuenciales aislados (`production_pipeline.yml`). [x] Completado
   - [x] **FG3 - Integrity Management**: Flujo diario ligero para validación de 404s (`fg3_integrity.yml`). [x] Completado
2. **Observabilidad y Resiliencia**:
   - [x] **Jobs Secuenciales**: Separación de 'Harvesting' y 'Cleansing' en jobs independientes para identificar cuellos de botella. [x] Completado
   - [x] **Delegación del Orquestador**: Modificación de `master_orchestrator.py` para permitir la delegación de fases a GitHub Actions ví­a flags (`--skip-cleansing`). [x] Completado
3. **Mantenimiento y Protocolo Local -> Nube (Smart Sync)**:
   - [x] **Protocolo de Sincronización**: Automatización del flujo de subida de cambios locales a Supabase Free. [x] Completado
     1. Ejecutar `python scripts/local/maintenance/sync_local_to_cloud.py`.
     2. El script detectará diferencias y realizará **Bulk Upserts** ví­a API REST (evitando el colapso del navegador por SQL pesado).
     3. Confirmar en el Dashboard de Supabase que los registros (especialmente `cleansed_programs`) se han actualizado sin duplicados.
   - [x] **Esquema Estructural**: Para cambios en la estructura de tablas (DDL), utilizar el bloque SQL ligero de la arquitectura y ejecutarlo en el SQL Editor (Frecuencia: Solo cuando cambien los campos). [x] Completado

### Fase 41: Saneamiento y Preparación para Repositorio Público [/] En curso
Objetivo: Blindar el repositorio para su apertura al público (Open Source) asegurando la total ausencia de secretos, saneamiento de código histórico y estandarización de la estructura de directorios.

1. **Estructura Maestra de Directorios (ECC Standard)**:
   - `.github/agents/`: Definición de especialistas SDLC (Cerebro del Proyecto).
   - `.github/workflows/`: Pipelines de automatización industrial (FG1, FG2, FG3).
   - `db/migrations/`: DDL controlado para replicación de base de datos.
   - `docs/`: Reportes de auditorí­a y memoria tí©cnica (Pilar de Calidad).
   - `scripts/core/`: Motores universales (Harvester, Processor, Sync).
   - `scripts/harvesters/`: Scrapers especí­ficos (Lógica de extracción).
   - `scripts/maintenance/`: Scripts de salud e integridad.
   - `scripts/shared/`: Utilidades comunes y clientes de API.
   - `web/`: Frontend Next.js 15 (Directorio raí­z del despliegue).
   - `local/`: **Caja Negra (Ignorado)**. Contiene scripts experimentales, backups de SQL y logs locales.

2. **Protocolo de Seguridad "Zero-Leak"**:
   - [x] **Aislamiento de Secretos**: Uso mandatorio de `.env` (ignorado) y GitHub Secrets. Prohibido hardcoding de URLs o Keys.
   - [x] **Sanitización de Git History**: Auditorí­a mediante `trufflehog` o similar para asegurar que no hay secretos en commits antiguos.
   - [x] **Supabase RLS Policy**: Todas las tablas públicas deben tener polí­ticas de solo lectura habilitadas por defecto.
   - [x] **Sanitización de Datos**: El pipeline de 4 estaciones (FG2) garantiza que solo datos públicos y limpios lleguen a la tabla `courses`.

3. **Saneamiento Quirúrgico de Archivos**:
   - [x] Migración de scripts de un solo uso a `scripts/legacy/`.
   - [x] Eliminación de comentarios redundantes y "TODOs" sensibles.
   - [x] Normalización de licencias y crí©ditos en cada script principal.

4. **Definition of Done (DoD) para Apertura Pública**:
   - [ ] **Limpia Total**: Ningún archivo `.env`, `.bak`, `.tmp` o credencial JSON en el rastreo de Git.
   - [ ] **Documentación Completa**: `README.md` actualizado con guí­a de "Self-Hosting" y arquitectura.
   - [ ] **Pruebas Verificadas**: Suite de tests en `.github/workflows/` pasando al 100%.
   - [ ] **Escudo de Calidad**: Reporte de `security-auditor` validando el estado del repositorio.

5. **Reestructuración de Directorio de Base de Datos (`db/`)**:
   - [x] **División de Archivos**: Clasificación estricta entre infraestructura y activos locales.
     - **Core Infrastructure (permanecen en `db/`)**: Archivos de esquema puro y migraciones controladas (`production_init.sql`, `PRODUCTION_MASTER.sql`, `production_seed.sql` y el directorio `migrations/`).
     - **Local Assets (movidos a `local/db/`)**: Exportaciones de datos, volcados SQL masivos (ej. `MIGRATE_TO_SUPABASE.sql`) y backups temporales.
   - [x] **Certificación de Limpieza**: Se auditó el contenido de `db/` verificando la ausencia total de secretos, contraseñas o cadenas de conexión. Los esquemas son seguros para exposición pública.

### Fase 42: Orquestación Inteligente y Resiliencia al Tiempo [x] Completado
Objetivo: Implementar inteligencia de orquestación basada en datos históricos y límites de tiempo de la nube para garantizar la escalabilidad y eficiencia del pipeline.

1. **Ampliación de Telemetría (DB)**:
   - [x] **Columnas de Seguimiento**: Añadidas `last_harvest_at` y `last_harvest_duration_sec` a la tabla `institutions`. [x] Completado
2. **Refactorización de Lógica (Scripts)**:
   - [x] **Registro de Tiempos**: `universal_harvester.py` captura la duración de la sesión y actualiza la tabla maestra. [x] Completado
   - [x] **Priorización Inteligente**: `master_orchestrator.py` ordena instituciones por `last_harvest_at.asc.nullsfirst` (Ciclo Round-Robin). [x] Completado
3. **Time-Aware Harvesting (Cierre Elegante)**:
   - [x] **Cerca de Tiempo**: Implementada lógica en el Harvester para realizar un cierre controlado faltando 20 minutos para el límite de 6 horas (5h 40m). [x] Completado
   - [x] **Reloj Global**: El orquestador sincroniza el tiempo de inicio con todos los sub-procesos. [x] Completado
4. **Optimización CI/CD (Workflows)**:
   - [x] **Unificación Horaria (Lima Time)**: Implementado `LimaFormatter` (UTC-5) en todos los workers para consistencia de logs. [x] Completado
   - [x] **Control de Disparadores**: Eliminado el trigger `push` en favor de CRON Diario y ejecución Manual. [x] Completado

**Resultado Final:** El sistema es ahora 100% autónomo, resiliente al tiempo y reporta con precisión en horario local.

## Riesgos y Mitigaciones
- **Riesgo**: Bloqueos persistentes de IP local. -> Mitigación: Uso obligatorio de Proxies Residenciales y TLS Impersonation.
- **Riesgo**: Inestabilidad de `curl_cffi` en CI. -> Mitigación: Mantener `aiohttp` como fallback con headers básicos.
- **Riesgo**: Saturación de DB por inserts masivos de descubrimiento. -> Mitigación: Batch inserts para el estado 'discovered'.
- **Riesgo (Nuevo)**: Desfase temporal entre datos de diferentes instituciones. -> Mitigación: La sincronización final a la tabla `courses` será incremental; los datos antiguos se mantienen hasta que su shard sea actualizado.

