# Plan de ImplementaciÃ³n: StudIAMatch - Tech Education Intelligence

## ðŸŽ¯ Premisas Obligatorias de IngenierÃ­a (Nivel 0)

> [!IMPORTANT]
> **DocumentaciÃ³n de Referencia (Golden Pipeline)**: El diseÃ±o arquitectÃ³nico, el flujo ETL de 4 estaciones y el diccionario de datos maestro se rigen estrictamente por lo definido en [docs/architecture/Documento_Detallado_workflow](docs/architecture/Documento_Detallado_workflow). Este documento es la "Ãšnica Fuente de Verdad" para la lÃ³gica de datos.
>
> **Aislamiento Total y Paridad Linux**: Queda estrictamente prohibido ejecutar comandos de desarrollo (npm, python, audit) directamente en el host Windows. 
> Todo comando **DEBE** ser ejecutado dentro del contenedor `studiamatch-dev` (Debian) para garantizar la paridad del 100% con los servidores de despliegue (Cloudflare/Linux).
>
> **Comando Base Mandatorio**:
> `docker exec -it studiamatch-dev [comando]`

## ðŸ›  Estado Actual del Proyecto (WORKING-CONTEXT)
- **Estado Actual**: Fase 2.0 (TIER 2 - CertificaciÃ³n) âœ… CERTIFICADO.
- **Ãšltimo Hito**: ConsolidaciÃ³n de pipelines de datos y reingenierÃ­a de calidad.
- **PrÃ³xima AcciÃ³n**: Implementar de-duplicaciÃ³n inteligente por RedirecciÃ³n y Canonical (Fase 39.1).

## ðŸš€ Hoja de Ruta: Lanzamiento ProducciÃ³n
- [ ] **MigraciÃ³n de Schema**: Replicar tablas, RLS e Ã­ndices en el proyecto Pro.
- [ ] **Data Seeding**: Primer harvesting masivo para poblar la base de datos oficial.
- [ ] **Domain Mapping**: Configurar DNS en Cloudflare para `studiamatch.com`.

---

## Estrategia de Ambientes (ECC Tiering)

Para garantizar la estabilidad de **StudIAMatch**, el flujo de trabajo se divide en tres entornos estancos vinculados a sus respectivas ramas de Git:

| Nivel | Rama Git | PropÃ³sito | Infraestructura (DB) | Frontend (Hosting) | DocumentaciÃ³n
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TIER 1: Desarrollo** | `desarrollo` | IteraciÃ³n rÃ¡pida y refactor. | Supabase Free (Actual) | `studiamatch.pages.dev` | `docs/deployment/deploy_desarrollo.md` |
| **TIER 2: CertificaciÃ³n** | `certificacion` | QA, Pruebas de Carga y E2E. | Supabase Free / QA Branch | `staging.studiomatch.com` | `docs/deployment/deploy_certificacion.md` |
| **TIER 3: ProducciÃ³n** | `main` | Servicio estable y escalable. | **Supabase Pro** | `studiomatch.com` | `docs/deployment/deploy_produccion.md` |

---

## Estrategia de Git Flow (PromociÃ³n de CÃ³digo)

El cÃ³digo viajarÃ¡ de forma ascendente cumpliendo "Puertas de Calidad" en cada etapa:

1.  **Work In Progress (WIP)**: Se trabaja en ramas de feature (ej: `feat/new-harvester`) que emergen de `desarrollo`. [x] Ramas `desarrollo` y `certificacion` creadas.
2.  **Pull Request a `desarrollo`**: RevisiÃ³n tÃ©cnica y validaciÃ³n de scripts en el sandbox actual.
3.  **PromociÃ³n a `certificacion`**: EjecuciÃ³n obligatoria de la Suite E2E (`Playwright`) y AuditorÃ­a de Integridad de Datos.
4.  **Merge a `main`**: Despliegue automÃ¡tico a producciÃ³n (Supabase Pro) tras aprobaciÃ³n del @SDLC-Chief.

---

## Arquitectura de EjecuciÃ³n (Macro-Estrategia)
La ejecuciÃ³n del sistema se divide en 3 Fases Generales (FG) para optimizar costos, eficiencia y responsabilidades:

* **FG1: Mapeo Institucional (Frecuencia: Mensual)**
  - **Objetivo**: Descubrir y registrar nuevas universidades e institutos licenciados por MINEDU.
  - **Script Principal**: `register_institution.py` (o procesos de Nivel 1).
* **FG2: Carga Masiva y Delta Scraping (Frecuencia: Semanal)**
  - **Objetivo**: ExtracciÃ³n exhaustiva del catÃ¡logo de cursos. La carga inicial obtiene toda la informaciÃ³n de las webs institucionales. Las ejecuciones posteriores aplican "Delta Scraping" (mediante Hashing) para extraer y procesar *solo* lo nuevo o modificado, reduciendo radicalmente el costo.
  - **Flujo de Scripts**: `universal_harvester.py` -> `cleansing_worker.py` -> `enrichment_worker.py` -> `sync_vector_worker.py` -> auditorÃ­as.
* **FG3: Integridad y Periodo de Gracia (Frecuencia: Diaria)**
  - **Objetivo**: Validar la disponibilidad de los enlaces existentes (404).
  - **Mecanismo**: Comprobar si el curso sigue activo. Si falla, entra en un "Periodo de Gracia" de 3 dÃ­as antes de inactivarse. Esto desliga al harvester de la verificaciÃ³n diaria.
  - **Script Principal**: `integrity_ping.py`.

## Arquitectura del Cerebro de Datos (Flujo ETL HistÃ³rico)
1. **Descubrimiento (The Explorer)** [x] Completado.
2. **Harvesting de URLs (The Collector)** [x] Completado.
3. **ExtracciÃ³n de Data Bruta (Deep Scrape)** [x] Completado.
4. **Enriquecimiento IA/LLM (The Brain)** [x] Completado.
5. **Quality Guard (AuditorÃ­a Aleatoria)** [x] Completado (Salud del catÃ¡logo certificada al 100%).
6. **TaxonomÃ­a AutomÃ¡tica (Motor de Reglas)** [x] Completado.
7. **VisualizaciÃ³n UX (Next.js 15)** [x] Completado (Detalle de 14 pilares y Social Proof funcionales).

## Estructura de Scripts (ProducciÃ³n)
JerarquÃ­a organizada para garantizar el mantenimiento y balanceo de carga:
- `scripts/core/`: OrquestaciÃ³n, Universal Harvester (FG2) y Mapeo (FG1).
- `scripts/harvesters/`: Scrapers especÃ­ficos por instituciÃ³n.
- `scripts/maintenance/`: AuditorÃ­a de calidad y Ping de integridad 404/Gracia (FG3).
- `scripts/legacy/`: Historial de desarrollo y scripts de un solo uso.

## Pasos de ImplementaciÃ³n

### Fase 1 a 10: CimentaciÃ³n y RediseÃ±o [x] Completado
- Todas las tareas certificadas.

### Fase 11: Escalamiento Progresivo y Triaje [x] Completado
- [x] Rescate de Brochures PDF y normalizaciÃ³n de duraciones.

### Fase 12: Inteligencia de RecomendaciÃ³n y Social Proof [x] Completado
- [x] Sistema de Ratings y Reviews operativo en Supabase y Web.
- [x] Motor de RecomendaciÃ³n por CategorÃ­a verificado.

### Fase 13: Escalamiento Nacional e Infraestructura [x] Completado
1. **Nivel 1: Descubrimiento (Monthly Discovery)** [x] Completado
   - [x] `scripts/core/discovery_institutions.py`: Crawler funcional y conectado a Supabase.
2. **Nivel 2: Carga Maestra (Weekly Master Load)** [x] Completado
   - [x] `scripts/core/master_orchestrator.py`: Balanceador de carga certificado.
3. **Nivel 3: Integridad (Daily Integrity Ping)** [x] Completado
   - [x] `scripts/core/integrity_ping.py`: Motor 404 con lÃ³gica de gracia de 3 dÃ­as operativo.
4. **OptimizaciÃ³n de BÃºsqueda (Fuzzy Search)** [x] Completado
   - [x] BÃºsqueda difusa activa en producciÃ³n.

### Fase 14: GarantÃ­a de Calidad y Humo de Datos [x] Completado
- [x] AuditorÃ­a de 14 pilares y eliminaciÃ³n de data acumulada en UI.

### Fase 15: Testeo de Usuario y Funcionalidad E2E [x] Completado
- [x] Corregido bug de botÃ³n de reseÃ±as y habilitadas polÃ­ticas RLS.

### Fase 16: Saneamiento de HuÃ©rfanos y ExpansiÃ³n TaxonÃ³mica [x] Completado
- [x] Implementadas 5 categorÃ­as: Finanzas, IngenierÃ­a, Arte, Derecho, Marketing.
- [x] Cero cursos en categorÃ­a 'General'. CatÃ¡logo 100% autÃ³nomo.

### Fase 17: Refinamiento UX y Comparativa Avanzada [x] Completado
...
### Fase 18: Inteligencia Financiera (ROI & Salarios) [x] Completado
1. **Matriz de Salarios de Mercado (PerÃº 2026)** [x] Completado.
2. **Motor de Inferencia de Nivel de Curso** [x] Completado (Jr/Mid/Sr poblados).
3. **AutomatizaciÃ³n del CÃ¡lculo de ROI** [x] Completado (FÃ³rmula dinÃ¡mica activa).
4. **UI de Transparencia Financiera** [x] Completado (Nota de fuente de datos integrada).

### Fase 19: AuditorÃ­a de Coherencia y Calidad Final [x] Completado
- AcciÃ³n: Ejecutado `taxonomy_roi_audit.py`. ReducciÃ³n de 140 a 0 inconsistencias.
- Resultado: CatÃ¡logo 100% veraz y sincronizado para producciÃ³n.

## Fase 20: CertificaciÃ³n de ProducciÃ³n AutÃ³noma [x] Completado
1. **Saneamiento QuirÃºrgico**: Truncado de tablas `courses`, `institutions`, `leads`, `ratings`, `reviews` (Preservando `market_salaries` y `categories`). [x] Completado
2. **Descubrimiento Nacional (Nivel 1)**: EjecuciÃ³n de `discovery_institutions.py` para identificar ~10 nuevos cursos/instituciones. [x] Completado
3. **Desarrollo de Harvesters (Nivel 2)**: CreaciÃ³n e implementaciÃ³n de scrapers especÃ­ficos para la muestra descubierta. [x] Completado
4. **OrquestaciÃ³n y Enriquecimiento**: EjecuciÃ³n del `master_orchestrator.py` y `llm_enrichment_worker.py` para la muestra. [x] Completado
5. **AuditorÃ­a Final de Integridad**: Validar 0 inconsistencias y 100% de coherencia financiera/taxÃ³nomica. [x] Completado
6. **Firma Digital**: CertificaciÃ³n final de la arquitectura y despliegue en entornos productivos. [x] Completado

## Fase 22: AutomatizaciÃ³n de ProducciÃ³n (Golden Pipeline) [x] Completado
1. **Infraestructura de GitHub Actions**:
   - [x] Crear `.github/workflows/production_pipeline.yml` con 3 niveles de ejecuciÃ³n. [x] Completado
   - [x] Configurar schedules: Diario (05:00), Semanal (Dom 02:00), Mensual (1ero 00:00). [x] Completado
2. **Motor de EjecuciÃ³n en Paralelo**:
   - [x] Crear `scripts/core/worker_runner.py` para consumo dinÃ¡mico de la matriz. [x] Completado
   - [x] Validar compatibilidad de Harvesters con entorno headless. [x] Completado
3. **Persistencia y Seguridad**:
   - [x] Documentar requerimiento de Secrets (SUPABASE_SERVICE_ROLE_KEY). [x] Completado
   - [x] Habilitar `pg_trgm` en base de datos de producciÃ³n. [x] Completado

## Fase 23: Rebranding Total a StudIAMatch [x] Completado
1. **Identidad Visual y Textual**:
   - [x] Actualizar `README.md` con la nueva narrativa de marca StudIAMatch. [x] Completado
   - [x] Actualizar `IMPLEMENTATION_PLAN.md` y documentos de arquitectura. [x] Completado
   - [x] Reemplazo masivo de "Yachachiy" por "StudIAMatch" en todo el codebase (scripts, web, tests). [x] Completado
2. **Componentes UI (Web)**:
   - [x] Actualizar Logo de "Yachachiy" a diseÃ±o "SM". [x] Completado
   - [x] Actualizar tÃ­tulos de pÃ¡gina, meta-tags y textos de footer/header. [x] Completado
   - [x] Ajustar gradientes o colores si es necesario para la nueva identidad. [x] Completado
3. **Persistencia y Pipelines**:
   - [x] Actualizar nombres de servicios en scripts y logs. [x] Completado
   - [x] Verificar que no queden referencias en comentarios o documentaciÃ³n tÃ©cnica. [x] Completado

## Fase 24: RediseÃ±o Minimalista y Compacto [x] Completado
1. **Header & Navigation**:
   - [x] Reducir altura del Header y optimizar branding. [x] Completado
   - [x] TipografÃ­a mÃ¡s nÃ­tida y espaciado compacto. [x] Completado
2. **Hero Section (Concepto StudIAMatch)**:
   - [x] RediseÃ±o minimalista del Hero con el slide "StudIAMatch Â· Data-driven decisions". [x] Completado
   - [x] Mejora de la barra de bÃºsqueda (mÃ¡s compacta y moderna). [x] Completado
3. **CatÃ¡logo y Filtros**:
   - [x] Optimizar sidebar de filtros para que sea mÃ¡s sutil y funcional. [x] Completado
   - [x] Nuevas tarjetas de curso minimalistas con mejor jerarquÃ­a visual. [x] Completado
4. **Footer & Secciones Informativas**:
   - [x] Compactar Footer manteniendo enlaces clave. [x] Completado
   - [x] Pulir secciones "CÃ³mo Funciona" y "Nosotros" con estÃ©tica plana y moderna. [x] Completado

## Fase 25: ValidaciÃ³n Funcional E2E [x] Completado
1. **AuditorÃ­a de NavegaciÃ³n**: Validar scroll suave y anclas de Header. [x] Completado
2. **Test de Detalle de Curso**: Verificar secciÃ³n de ROI y formulario de captura. [x] Completado
3. **AuditorÃ­a de Marca**: Confirmar 0 residuos de marca anterior en UI. [x] Completado
4. **GeneraciÃ³n de Reporte**: Documentar hallazgos en `docs/qa-engineer/`. [x] Completado

## Fase 26: AuditorÃ­a de Rutas y Coherencia v2 [x] Completado
1. **ValidaciÃ³n de Rutas DinÃ¡micas**: Confirmar formato `/courses/[institution]/[slug]` en Home y Detalle. [x] Completado
2. **QA de Integridad de Datos**: Ejecutar `quality_assurance_audit.py` para coherencia en BD. [x] Completado
3. **Pruebas de Carga Directa**: Validar rutas especÃ­ficas (ej: upc/psicologia). [x] Completado
4. **ActualizaciÃ³n de E2E**: Ajustar `mobile_usability.spec.ts` para nuevas rutas y ejecutar. [x] Completado
5. **Reporte Final**: Generar `docs/qa-engineer/reporte_funcionalidad_v2.md`. [x] Completado

## Fase 27: ResoluciÃ³n de ColisiÃ³n de Slugs e Infraestructura de Rutas [x] Completado
1. **RediseÃ±o de Esquema de URLs**: MigraciÃ³n de `/courses/[slug]` a `/courses/[institution]/[slug]` para garantizar unicidad. [x] Completado
2. **RefactorizaciÃ³n de Componentes**:
   - [x] `CourseDetailClient.tsx`: BÃºsqueda dual por slug de curso e instituciÃ³n. [x] Completado
   - [x] `page.tsx` (Home): ConstrucciÃ³n dinÃ¡mica de enlaces con `institution_slug`. [x] Completado
   - [x] `compare/page.tsx`: ActualizaciÃ³n de enlaces de "Ver Detalle". [x] Completado
3. **OptimizaciÃ³n de Backend (Scripts)**:
   - [x] `scripts/shared/utils.py`: Mejora de `slugify` con soporte Unicode/NFD para tildes y Ã±. [x] Completado
   - [x] `UniversalHarvester`: IntegraciÃ³n de la nueva lÃ³gica de saneamiento de slugs. [x] Completado
4. **ValidaciÃ³n de Datos**: ConfirmaciÃ³n de que el 100% de los cursos auditados poseen la relaciÃ³n necesaria con su instituciÃ³n para el nuevo ruteo. [x] Completado

## Fase 28: Robustez de API y Manejo de Errores [x] Completado
1. **Saneamiento de Fetches en Cliente**:
   - [x] `CourseDetailClient.tsx`: Implementado escape de parÃ¡metros con `encodeURIComponent` en todas las rutas de API.
   - [x] Implementada lÃ³gica `try-catch` robusta con validaciÃ³n de estados `response.ok`.
2. **OptimizaciÃ³n de BÃºsqueda Parcial**:
   - [x] Corregida sintaxis de `ilike` para PostgREST (uso de `*` como comodÃ­n en lugar de `%` en la URL).
3. **ValidaciÃ³n de Datos en Social Proof**:
   - [x] AÃ±adida validaciÃ³n de nulidad para `category_id` y manejo de arrays vacÃ­os en recomendaciones.

## Fase 29: AuditorÃ­a de De-duplicaciÃ³n e Integridad de URLs [x] Completado
1. **Filtro de Unicidad en Frontend**: Implementada lÃ³gica en `page.tsx` para de-duplicar por `(institution, url)`. [x] Completado
2. **Sistema de PriorizaciÃ³n**: En caso de duplicidad, se selecciona automÃ¡ticamente el registro tipo 'Programa' sobre 'Curso'. [x] Completado
3. **BÃºsqueda Resiliente (Multi-Strategy Lookup)**: Implementada lÃ³gica en `CourseDetailClient` que busca por (1) Slug exacto, (2) Coincidencia en URL y (3) BÃºsqueda difusa. Esto soluciona problemas de tildes o caracteres corruptos en la DB. [x] Completado
4. **AuditorÃ­a de Salud de Rutas**: Ejecutado script de integridad validando que el 100% de las rutas dinÃ¡micas resuelven correctamente sin errores "Lo sentimos...". [x] Completado
5. **Reporte Formal**: Actualizado `docs/qa-engineer/reporte_duplicidad_integridad.md`. [x] Completado

### Fase 30: AutomatizaciÃ³n Core Flow (CI/CD + AI) [x] COMPLETADO
1. **InvestigaciÃ³n de Costos LLM**: Cloudflare (10k neurons gratis) vs GitHub Models. [x] Completado.
2. **Infraestructura de GitHub Actions**:
   - [x] `.github/workflows/daily_ingestion.yml` activo en rama `desarrollo`.
   - [x] Secrets configurados en Environment `Development`.
3. **Estrategia "Data Drip" (IA Multi-Cloud)**:
   - [x] LÃ­mite dinÃ¡mico (100 cursos: 50 CF + 50 GH/Gemini).
   - [x] Filtro de calidad (Min 150 chars en descripciÃ³n).
   - [x] Fallback automÃ¡tico anti-429 (Cloudflare -> GitHub -> Gemini).

### Fase 31: EstabilizaciÃ³n TIER 1 (Desarrollo) [x] COMPLETADO
- [x] ConfiguraciÃ³n de Environments en GitHub.
- [x] ValidaciÃ³n de 100% de Ã©xitos en batch de enriquecimiento (Triple-Cloud).
- [x] EstabilizaciÃ³n Visual (JSON parsing & Unicode) en `CourseDetailClient.tsx`
- [x] ConfiguraciÃ³n de Pipeline AutomÃ¡tico Zero-Touch (Root: /web, Output: out)
- [x] Limpieza y DocumentaciÃ³n de Tier 1 completada

### Fase 31.5: ConfiguraciÃ³n de VisualizaciÃ³n y TaxonomÃ­a [x] COMPLETADO
- [x] GuÃ­a paso a paso para Cloudflare Dashboard.
- [x] ValidaciÃ³n de estructura URL oficial: `/courses/[institution]/[slug]`.
- [x] EliminaciÃ³n de colisiones de rutas antiguas (`[slug]`).
- [x] Despliegue automÃ¡tico 100% verificado en Cloudflare.

## Fase 32: MigraciÃ³n de Datos y Esquema [ ] Pendiente
1. **SincronizaciÃ³n de Esquema** (DB Migration)
   - AcciÃ³n: Usar `supabase db pull` del proyecto actual y `supabase db push` al nuevo.
   - Dependencias: Fase 31.
   - Riesgo: Medio (Validar RLS y extensiones como `pg_trgm`).
2. **MigraciÃ³n de Datos Maestros** (SQL / CSV)
   - AcciÃ³n: Migrar tablas de referencia: `categories`, `market_salaries`.
   - AcciÃ³n: Migrar datos operativos sanitizados: `institutions`, `courses`.
3. **AuditorÃ­a de Integridad en ProducciÃ³n** (Script)
   - AcciÃ³n: Ejecutar `quality_assurance_audit.py` apuntando al nuevo proyecto.

## Fase 33: Dominios y Cloudflare (studiamatch.com) [ ] Pendiente
1. **ConfiguraciÃ³n de Cloudflare Pages**:
   - `main branch` -> Dominio: `studiamatch.com` (VÃ­a Hostinger CNAME/A).
   - `certificacion branch` -> Dominio: `cert.studiamatch.com` o similar.
   - `desarrollo branch` -> Dominio: `studiamatch.pages.dev`.
2. **PropagaciÃ³n DNS y SSL**:
   - AcciÃ³n: Validar certificados SSL gestionados por Cloudflare para los 3 niveles.
   - AcciÃ³n: Configurar redireccionamientos de seguridad HSTS.
3. **Custom Domain en Supabase**:
   - AcciÃ³n: Configurar Custom Domain en Supabase para `db.studiamatch.com` (Opcional, Pro feature).
4. **OptimizaciÃ³n de Seguridad y Performance** (Cloudflare)
   - AcciÃ³n: Habilitar Proxy (naranja), SSL Full (Strict), y reglas de WAF bÃ¡sicas.
   - AcciÃ³n: Configurar redirecciÃ³n de `www` a non-www.

## Fase 34: Lanzamiento y CertificaciÃ³n Final [ ] Pendiente
1. **Smoke Tests en ProducciÃ³n** (Web)
   - AcciÃ³n: Validar flujo completo desde Home hasta Detalle y Social Proof en el dominio final.
2. **ActivaciÃ³n de Pipelines AutomÃ¡ticos** (GitHub Actions)
   - AcciÃ³n: Habilitar los flujos de `daily_ingestion.yml` apuntando al entorno de producciÃ³n.
3. **Cierre de Ciclo y DocumentaciÃ³n** (Docs)
   - [x] Generadas guÃ­as de despliegue por ambiente en `docs/deployment/`. [x] Completado

## Fase 35: ReingenierÃ­a de Calidad de Datos (Raw Harvesting) [x] Completado
1. **Infraestructura de Staging**:
   - [x] Crear tabla `harvesting` para almacenamiento de data bruta (URL, HTML, Metatags). [x] Completado
   - [x] Implementar estados: `pending`, `processed`, `discarded`, `error`. [x] Completado
2. **Refactor de Universal Harvester**:
   - [x] Separar lÃ³gica de descubrimiento de la de guardado final. [x] Completado
   - [x] Guardar data "en bruto" en `harvesting` sin normalizaciÃ³n agresiva. [x] Completado
   - [x] OptimizaciÃ³n de Gran Volumen (Capacidad 500,000 chars). [x] Completado
3. **Desarrollo del Processor Intelligen (The Curator)**:
   - [x] Crear `scripts/core/harvest_processor.py` para depuraciÃ³n quirÃºrgica. [x] Completado
   - [x] Implementar heurÃ­stica anti-slogan (detectar "Descubre nuestras carreras", "404", etc.). [x] Completado
   - [x] Flujo de promociÃ³n: `harvesting` -> Enriquecimiento -> `courses`. [x] Completado
4. **ValidaciÃ³n de la Muestra en Conflictos**:
   - [x] Re-procesar URL de UPC Marketing para validar limpieza automÃ¡tica del nombre. [x] Completado

## Fase 36: Pipeline de Datos de Alta Fidelidad (4 Estaciones) [x] Completado

Esta fase reemplaza y consolida la anterior estrategia de harvesting, implementando un flujo ETL (Extract, Transform, Load) de grado industrial.

### ðŸš‰ Las 4 Estaciones del Dato
1.  **EstaciÃ³n 1: `staging_raw` (Harvesting)**:
    - [x] Motor de descubrimiento masivo (Sitemaps + BFS Crawl). [x] Completado
    - [x] Almacenamiento de HTML bruto (LÃ­mite 500k chars). [x] Completado
    - [x] Casos de Ã©xito: **UTP (100 URLs)** y **DMC (100 URLs)**. [x] Completado
2.  **EstaciÃ³n 2: `cleansed_programs` (Cleansing)**:
    - [x] Script `cleansing_worker.py` funcional. [x] Completado
    - [x] Ejecutar limpieza masiva para DMC/UTP (Eliminar slogans y duplicados). [x] Completado
    - [x] DeduplicaciÃ³n multi-sede activa. [x] Completado
3.  **EstaciÃ³n 3: `enriched_programs` (Enrichment - IA)**:
    - [x] **ImplementaciÃ³n de IA Real** (OpenAI/Gemini) en `enrichment_worker.py`. [x] Completado
    - [x] ExtracciÃ³n obligatoria de los **14 Pilares de Metadata**. [x] Completado
4.  **EstaciÃ³n 4: `courses` (Production & Vector Sync)**:
    - [x] Script `sync_vector_worker.py` base. [x] Completado
    - [x] GeneraciÃ³n de Embeddings para bÃºsqueda semÃ¡ntica. [x] Completado
    - [x] PublicaciÃ³n final en la Web. [x] Completado

### ðŸš€ Estado Actual: "ConsolidaciÃ³n de Estaciones ETL Completada"
- Las 4 estaciones estÃ¡n integradas y funcionales en producciÃ³n.

## Fase 37: EstabilizaciÃ³n de Pipeline y ProducciÃ³n (Oficial 5 Fases) [x] Finalizado
**Estado**: Operativo y Automatizado.
- [x] **EstandarizaciÃ³n de Secretos**: Todas las variables movidas a `SUPABASE_URL` y `SUPABASE_KEY` (Fix total de error `None URL`).
- [x] **Fase 0 (Inventory)**: Activado `discovery_institutions.py` para alimentar el catÃ¡logo maestro.
- [x] **Fase 1 (Massive Harvesting)**: Re-activado `master_orchestrator.py` con lÃ­mites de 150 URLs (Anti-timeout).
- [x] **Fase 2 (Multicloud Enrichment)**: Implementado `enrichment_worker.py` con cascada CF -> GitHub -> Gemini.
- [x] **Fase 3 (Production Sync)**: Activado `sync_vector_worker.py` con slugs persistentes.
- [x] **Fase 4 (ROI-QA Audit)**: IntegraciÃ³n final de auditorÃ­a de calidad de datos en cada carrera.
- [x] **Golden Pipeline**: YAML optimizado a 5 Jobs secuenciales para mÃ¡xima trazabilidad.

## Fase 38: RefactorizaciÃ³n de universal_harvester.py (Estrategia Stealth Harvesting FG2) [x] Completado
El objetivo fue transformar el harvester en un motor de alta resiliencia y sigilo capaz de alimentar el "cerebro" de la plataforma con +20k registros sin disparar bloqueos de WAFs avanzados (Akamai/Cloudflare).

1. **Protocolo de Sigilo (Stealth) y EvasiÃ³n**:
   - [x] **SuplantaciÃ³n TLS (JA3/JA4)**: Sustituir `aiohttp` por `curl_cffi` para mimetizar la huella TLS de navegadores reales. [x] Completado
   - [x] **Coherencia de Headers**: Implementar rotaciÃ³n de `User-Agent` sincronizada con headers `Sec-CH-UA` y firma TLS. [x] Completado
   - [ ] **Soporte de Proxies**: Configurar pool de Proxies Residenciales Rotativos para distribuciÃ³n de IPs. (Pendiente para escalamiento masivo).
2. **Resiliencia y Concurrencia Responsable**:
   - [x] **SemÃ¡foros por Dominio**: `asyncio.Semaphore(3)` para limitar la carga por servidor. [x] Completado
   - [x] **Delays Adaptativos (Jitter)**: Pausas aleatorias de 2-5s entre peticiones. [x] Completado
   - [x] **PatrÃ³n Circuit Breaker**: Abortar automÃ¡ticamente el scraping de una instituciÃ³n tras 3 errores 403/429 consecutivos. [x] Completado
3. **Checkpointing Inmediato y Persistencia**:
   - [x] **Estado 'Discovered'**: Persistir URLs en `staging_raw` inmediatamente tras el descubrimiento (Sitemap/BFS) para evitar re-escaneos. [x] Completado
   - [x] **GestiÃ³n de Chunks**: Procesar la cola de extracciÃ³n en lotes atÃ³micos que permitan reanudaciÃ³n tras fallos. [x] Completado
4. **OptimizaciÃ³n de Datos (Delta Scraping)**:
   - [x] **Content Hashing**: Solo ejecutar `Upsert` si el hash del contenido limpio ha cambiado. [x] Completado
   - [x] **SanitizaciÃ³n de Backlog**: Implementada lÃ³gica `_load_existing_urls` para saltar el descubrimiento de URLs que ya existen en la DB. [x] Completado

## Fase 39: ReingenierÃ­a y AfinaciÃ³n del Cleansing Worker (EstaciÃ³n 1.5) [x] Completado
Objetivo: Transformar `cleansing_worker.py` en un filtro de alta fidelidad con motor de exclusiÃ³n por instituciÃ³n, consolidaciÃ³n de sedes y limpieza profunda de HTML.

1. **Infraestructura de Datos**:
   - [x] **Tabla de ExclusiÃ³n**: Crear `crawler_exclusions` para filtrar URLs por patrÃ³n (ej. /noticias/, /becas/). [x] Completado
   - [x] **AutogeneraciÃ³n de IDs**: Habilitar `gen_random_uuid()` por defecto en `cleansed_programs`. [x] Completado
2. **RefactorizaciÃ³n del Worker (AfinaciÃ³n QuirÃºrgica)**:
   - [x] **Motor de ExclusiÃ³n Inteligente**: Cargar reglas de `crawler_exclusions` en el worker para validaciÃ³n por patrÃ³n absoluto. [x] Completado
   - [x] **Limpieza Profunda (BeautifulSoup)**: EliminaciÃ³n de `<head>`, `<header>`, `<footer>`, `<nav>` y elementos con clases de ruido (`menu, sidebar, social`). [x] Completado
   - [x] **DetecciÃ³n de Soft 404**: Bloqueo automÃ¡tico de pÃ¡ginas que cargan pero indican "PÃ¡gina no encontrada". [x] Completado
   - [x] **Filtro de Caducidad HistÃ³rica**: Descarte de contenido con aÃ±os obsoletos (2018-2024) en URL o texto. [x] Completado
   - [x] **ConsolidaciÃ³n de Sibling Pages**: AgrupaciÃ³n de sub-pÃ¡ginas (Beneficios, Plana, Malla) en un Ãºnico registro maestro (1:1). [x] Completado
3. **Mantenimiento y Saneamiento**:
   - [x] **Truncado de Plata**: Limpiar `cleansed_programs` para eliminar data con ruido anterior. [x] Completado
   - [x] **Re-procesamiento Masivo**: Resetear `staging_raw` a 'pending' y ejecutar la nueva lÃ³gica sobre los +1,000 registros. [x] Completado

**Resultado Final:** ~156 programas acadÃ©micos puros de alta fidelidad promovidos (ReducciÃ³n de >70% de ruido).

## Fase 39.1: De-duplicaciÃ³n Inteligente por RedirecciÃ³n y Canonical [x] Completado
Objetivo: Resolver el problema de mÃºltiples rutas apuntando al mismo contenido (caso New Horizons) capturando la "Fuente de Verdad" tÃ©cnica definida por el servidor y SEO.

1. **Infraestructura de Datos (SQL)**:
   - [x] **Esquema de Alta Fidelidad**: AÃ±adir columnas `effective_url` y `canonical_url` en `staging_raw` y `cleansed_programs`. [x] Completado
   - [x] **Ãndice Compuesto**: Migrar el Ã­ndice UNIQUE de `cleansed_programs` a la tupla `(institution_id, effective_url)` para evitar colisiones entre instituciones. [x] Completado
2. **RefactorizaciÃ³n de Captura (Harvester)**:
   - [x] **Captura de URL Final**: Almacenar `response.url` tras redirecciones automÃ¡ticas de `curl_cffi` o Playwright. [x] Completado
   - [x] **ExtracciÃ³n de Canonical**: Implementar regex/BeautifulSoup para extraer `<link rel="canonical">` como prioridad de de-duplicaciÃ³n. [x] Completado
3. **LÃ³gica de ConsolidaciÃ³n (Cleanser)**:
   - [x] **NormalizaciÃ³n Robusta**: Implementar `normalize_url` para remover query strings, fragmentos y unificar el `trailing slash`. [x] Completado
   - [x] **Pivot de AgrupaciÃ³n**: Cambiar la lÃ³gica de consolidaciÃ³n para que use `canonical_url` (prioridad) o `effective_url` (fallback) como clave de uniÃ³n. [x] Completado
   - [x] **Trazabilidad de Linaje**: Registrar `sibling_staging_ids` en los metadatos para auditar quÃ© URLs originales fueron "comprimidas". [x] Completado
4. **CertificaciÃ³n y Sanity Check**:
   - [x] **Test de New Horizons**: Validar que las rutas divergentes de TOGAF se fusionen en un Ãºnico registro maestro. [x] Completado
   - [x] **ValidaciÃ³n de Fallback**: Confirmar el uso de `COALESCE` para operar con URLs originales si no hay redirecciÃ³n detectada. [x] Completado

## Fase 40: RefactorizaciÃ³n de Infraestructura CI/CD [x] Completado
Objetivo: Migrar el pipeline monolÃ­tico hacia un sistema de 3 flujos atÃ³micos (Mensual, Semanal, Diario) para optimizar costos de computaciÃ³n y mejorar la observabilidad en la nube.

1. **Estructura de Workflows (GitHub Actions)**:
   - [x] **FG1 - Institution Inventory**: Flujo mensual para descubrimiento de nuevas semillas (`fg1_inventory.yml`). [x] Completado
   - [x] **FG2 - Golden Pipeline**: Flujo semanal de alto volumen con jobs secuenciales aislados (`production_pipeline.yml`). [x] Completado
   - [x] **FG3 - Integrity Management**: Flujo diario ligero para validaciÃ³n de 404s (`fg3_integrity.yml`). [x] Completado
2. **Observabilidad y Resiliencia**:
   - [x] **Jobs Secuenciales**: SeparaciÃ³n de 'Harvesting' y 'Cleansing' en jobs independientes para identificar cuellos de botella. [x] Completado
   - [x] **DelegaciÃ³n del Orquestador**: ModificaciÃ³n de `master_orchestrator.py` para permitir la delegaciÃ³n de fases a GitHub Actions vÃ­a flags (`--skip-cleansing`). [x] Completado
3. **Mantenimiento y Protocolo Local -> Nube (Smart Sync)**:
   - [x] **Protocolo de SincronizaciÃ³n**: AutomatizaciÃ³n del flujo de subida de cambios locales a Supabase Free. [x] Completado
     1. Ejecutar `python scripts/local/maintenance/sync_local_to_cloud.py`.
     2. El script detectarÃ¡ diferencias y realizarÃ¡ **Bulk Upserts** vÃ­a API REST (evitando el colapso del navegador por SQL pesado).
     3. Confirmar en el Dashboard de Supabase que los registros (especialmente `cleansed_programs`) se han actualizado sin duplicados.
   - [x] **Esquema Estructural**: Para cambios en la estructura de tablas (DDL), utilizar el bloque SQL ligero de la arquitectura y ejecutarlo en el SQL Editor (Frecuencia: Solo cuando cambien los campos). [x] Completado

## Fase 41: Saneamiento y PreparaciÃ³n para Repositorio PÃºblico [/] En curso
Objetivo: Blindar el repositorio para su apertura al pÃºblico (Open Source) asegurando la total ausencia de secretos, saneamiento de cÃ³digo histÃ³rico y estandarizaciÃ³n de la estructura de directorios.

1. **Estructura Maestra de Directorios (ECC Standard)**:
   - `.github/agents/`: DefiniciÃ³n de especialistas SDLC (Cerebro del Proyecto).
   - `.github/workflows/`: Pipelines de automatizaciÃ³n industrial (FG1, FG2, FG3).
   - `db/migrations/`: DDL controlado para replicaciÃ³n de base de datos.
   - `docs/`: Reportes de auditorÃ­a y memoria tÃ©cnica (Pilar de Calidad).
   - `scripts/core/`: Motores universales (Harvester, Processor, Sync).
   - `scripts/harvesters/`: Scrapers especÃ­ficos (LÃ³gica de extracciÃ³n).
   - `scripts/maintenance/`: Scripts de salud e integridad.
   - `scripts/shared/`: Utilidades comunes y clientes de API.
   - `web/`: Frontend Next.js 15 (Directorio raÃ­z del despliegue).
   - `local/`: **Caja Negra (Ignorado)**. Contiene scripts experimentales, backups de SQL y logs locales.

2. **Protocolo de Seguridad "Zero-Leak"**:
   - [x] **Aislamiento de Secretos**: Uso mandatorio de `.env` (ignorado) y GitHub Secrets. Prohibido hardcoding de URLs o Keys.
   - [x] **SanitizaciÃ³n de Git History**: AuditorÃ­a mediante `trufflehog` o similar para asegurar que no hay secretos en commits antiguos.
   - [x] **Supabase RLS Policy**: Todas las tablas pÃºblicas deben tener polÃ­ticas de solo lectura habilitadas por defecto.
   - [x] **SanitizaciÃ³n de Datos**: El pipeline de 4 estaciones (FG2) garantiza que solo datos pÃºblicos y limpios lleguen a la tabla `courses`.

3. **Saneamiento QuirÃºrgico de Archivos**:
   - [x] MigraciÃ³n de scripts de un solo uso a `scripts/legacy/`.
   - [x] EliminaciÃ³n de comentarios redundantes y "TODOs" sensibles.
   - [x] NormalizaciÃ³n de licencias y crÃ©ditos en cada script principal.

4. **Definition of Done (DoD) para Apertura PÃºblica**:
   - [ ] **Limpia Total**: NingÃºn archivo `.env`, `.bak`, `.tmp` o credencial JSON en el rastreo de Git.
   - [ ] **DocumentaciÃ³n Completa**: `README.md` actualizado con guÃ­a de "Self-Hosting" y arquitectura.
   - [ ] **Pruebas Verificadas**: Suite de tests en `.github/workflows/` pasando al 100%.
   - [ ] **Escudo de Calidad**: Reporte de `security-auditor` validando el estado del repositorio.

---

4. **Reestructuración de Directorio de Base de Datos (`db/`)**:
   - [x] **División de Archivos**: Clasificación estricta entre infraestructura y activos locales.
     - **Core Infrastructure (permanecen en `db/`)**: Archivos de esquema puro y migraciones controladas (`production_init.sql`, `PRODUCTION_MASTER.sql`, `production_seed.sql` y el directorio `migrations/`).
     - **Local Assets (movidos a `local/db/`)**: Exportaciones de datos, volcados SQL masivos (ej. `MIGRATE_TO_SUPABASE.sql`) y backups temporales.
   - [x] **Certificación de Limpieza**: Se auditó el contenido de `db/` verificando la ausencia total de secretos, contraseñas o cadenas de conexión. Los esquemas son seguros para exposición pública.

## Riesgos y Mitigaciones
- **Riesgo**: Bloqueos persistentes de IP local. -> MitigaciÃ³n: Uso obligatorio de Proxies Residenciales y TLS Impersonation.
- **Riesgo**: Inestabilidad de `curl_cffi` en CI. -> MitigaciÃ³n: Mantener `aiohttp` como fallback con headers bÃ¡sicos.
- **Riesgo**: SaturaciÃ³n de DB por inserts masivos de descubrimiento. -> MitigaciÃ³n: Batch inserts para el estado 'discovered'.
- **Riesgo (Nuevo)**: FiltraciÃ³n accidental de secretos en repo pÃºblico. -> MitigaciÃ³n: RevisiÃ³n obligatoria con escÃ¡ner de secretos antes del primer `public push`.
