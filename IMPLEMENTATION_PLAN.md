# Plan de Implementación: StudIAMatch - Tech Education Intelligence

## Contexto de Trabajo (WORKING-CONTEXT)
- **Estado Actual**: Fase 31 (Iniciada). Configurando TIER 1: Desarrollo.
- **Último Hito**: Auditoría de datos "Gold Standard" completada.
- **Próxima Acción**: Configurar secretos de GitHub para el ambiente Desarrollo.

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

## Arquitectura del Cerebro de Datos (Core Flow)
1. **Descubrimiento (The Explorer)** [x] Completado.
2. **Harvesting de URLs (The Collector)** [x] Completado.
3. **Extracción de Data Bruta (Deep Scrape)** [x] Completado.
4. **Enriquecimiento IA/LLM (The Brain)** [x] Completado.
5. **Quality Guard (Auditoría Aleatoria)** [x] Completado (Salud del catálogo certificada al 100%).
6. **Taxonomía Automática (Motor de Reglas)** [x] Completado.
7. **Visualización UX (Next.js 15)** [x] Completado (Detalle de 14 pilares y Social Proof funcionales).

---

## Estructura de Scripts (Producción)
Jerarquía organizada para garantizar el mantenimiento y balanceo de carga:
- `scripts/core/`: Orquestación y Harvester Universal (Motor Maestro).
- `scripts/harvesters/`: Scrapers específicos por institución.
- `scripts/maintenance/`: Auditoría de calidad y Ping de integridad (404).
- `scripts/legacy/`: Historial de desarrollo y scripts de un solo uso.

---

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

## Fase 22: Automatización de Producción (Golden Pipeline) [/] Pendiente
1. **Infraestructura de GitHub Actions**:
   - [ ] Crear `.github/workflows/production_pipeline.yml` con 3 niveles de ejecución. [ ] Pendiente
   - [ ] Configurar schedules: Diario (05:00), Semanal (Dom 02:00), Mensual (1ero 00:00). [ ] Pendiente
2. **Motor de Ejecución en Paralelo**:
   - [ ] Crear `scripts/core/worker_runner.py` para consumo dinámico de la matriz. [/] En curso
   - [ ] Validar compatibilidad de Harvesters con entorno headless. [ ] Pendiente
3. **Persistencia y Seguridad**:
   - [ ] Documentar requerimiento de Secrets (SUPABASE_SERVICE_ROLE_KEY). [ ] Pendiente
   - [ ] Habilitar `pg_trgm` en base de datos de producción. [ ] Pendiente

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

## Fase 29: Auditoría de De-duplicación e Integridad de URLs [x] Completado
1. **Filtro de Unicidad en Frontend**: Implementada lógica en `page.tsx` para de-duplicar por `(institution, url)`. [x] Completado
2. **Sistema de Priorización**: En caso de duplicidad, se selecciona automáticamente el registro tipo 'Programa' sobre 'Curso'. [x] Completado
3. **Búsqueda Resiliente (Multi-Strategy Lookup)**: Implementada lógica en `CourseDetailClient` que busca por (1) Slug exacto, (2) Coincidencia en URL y (3) Búsqueda difusa. Esto soluciona problemas de tildes o caracteres corruptos en la DB. [x] Completado
4. **Auditoría de Salud de Rutas**: Ejecutado script de integridad validando que el 100% de las rutas dinámicas resuelven correctamente sin errores "Lo sentimos...". [x] Completado
5. **Reporte Formal**: Actualizado [reporte_duplicidad_integridad.md](file:///c:/Users/Romel/Proyectos/studiamatch/docs/qa-engineer/reporte_duplicidad_integridad.md). [x] Completado

## Fase 30: Automatización Core Flow (CI/CD + AI) [/] En curso
1. **Investigación de Costos LLM**: Evaluados Cloudflare Workers AI (10k neurons free) y GitHub Models (Beta Gratis). [x] Completado
2. **Infraestructura de GitHub Actions**:
   - [x] Creado `.github/workflows/daily_ingestion.yml` para flujo diario automatizado.
   - [ ] Configurar Secrets en el repositorio (SUPABASE_URL, GH_MODELS_TOKEN). [ ] Pendiente
3. **Worker de Enriquecimiento (LLM)**:
   - [ ] Adaptar `llm_enrichment_worker.py` para compatibilidad con la API de GitHub Models. [ ] Pendiente
4. **Estrategia de Low-Cost**: Implementar balanceo de carga para rotar entre modelos gratuitos en caso de cuota agotada. [ ] Pendiente

## Fase 31: Migración a Supabase Pro (Producción) [ ] Pendiente
1. **Aprovisionamiento de Cuenta Pro** (Admin Console)
   - Acción: Actualizar la organización actual al plan Pro.
2. **Setup de Branching en Supabase** (Dashboard)
   - Acción: Activar 'Supabase Branching' para que `certificacion` y `desarrollo` puedan tener sus propios aislados si es necesario, o mantener proyectos separados.
3.   - [x] Certificación de Calidad de Datos (Auditoría "Gold Standard"). [x] Completado
   - [ ] **Configuración de TIER 1 (Desarrollo)**:
     - Acción: El usuario debe crear el Environment `Development` en GitHub.
     - Acción: Agregar Secrets al Environment: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` (del proyecto Free actual).
     - Acción: Agregar Secrets Globales (si no están): `CF_API_TOKEN`, `CF_ACCOUNT_ID` (para Cloudflare Workers AI).
   - `PROD_SUPABASE_URL`: Proyecto Pro (Main).

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

## Fase 33: Dominios y Cloudflare (studiomatch.com) [ ] Pendiente
1. **Configuración de Cloudflare Pages**:
   - `main branch` -> Dominio: `studiomatch.com` (Vía Hostinger CNAME/A).
   - `certificacion branch` -> Dominio: `cert.studiomatch.com` o similar.
   - `desarrollo branch` -> Dominio: `studiamatch.pages.dev`.
2. **Propagación DNS y SSL**:
   - Acción: Validar certificados SSL gestionados por Cloudflare para los 3 niveles.
   - Acción: Configurar redireccionamientos de seguridad HSTS.
3. **Custom Domain en Supabase**:
   - Acción: Configurar Custom Domain en Supabase para `db.studiomatch.com` (Opcional, Pro feature).
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
   - [ ] Actualizar `README.md` con las URLs definitivas y manual de mantenimiento. [ ] Pendiente

## Fase 28: Robustez de API y Manejo de Errores [x] Completado
1. **Saneamiento de Fetches en Cliente**:
   - [x] `CourseDetailClient.tsx`: Implementado escape de parámetros con `encodeURIComponent` en todas las rutas de API.
   - [x] Implementada lógica `try-catch` robusta con validación de estados `response.ok`.
2. **Optimización de Búsqueda Parcial**:
   - [x] Corregida sintaxis de `ilike` para PostgREST (uso de `*` como comodín en lugar de `%` en la URL).
3. **Validación de Datos en Social Proof**:
   - [x] Añadida validación de nulidad para `category_id` y manejo de arrays vacíos en recomendaciones.

## Riesgos y Mitigaciones
- **Riesgo**: Pérdida de usabilidad por exceso de minimalismo. -> Mitigación: Mantener contrastes altos y botones de acción claros.
- **Riesgo**: Incomatibilidad con datos de Supabase. -> Mitigación: Asegurar que los componentes manejen estados `loading` y `error`.
