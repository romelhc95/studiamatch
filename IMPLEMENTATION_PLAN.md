# Plan de Implementación: StudIAMatch - Tech Education Intelligence

## Contexto de Trabajo (WORKING-CONTEXT)
- **Estado Actual**: Fase 18 (Saneamiento) completada. Catálogo 100% categorizado automáticamente.
- **Último Hito**: Social Proof habilitado y corregido. Eliminada la dependencia manual de categorías.
- **Próxima Acción**: Iniciar Fase 13 (Escalamiento Nacional).

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

## Riesgos y Mitigaciones
- **Riesgo**: Pérdida de usabilidad por exceso de minimalismo. -> Mitigación: Mantener contrastes altos y botones de acción claros.
- **Riesgo**: Incomatibilidad con datos de Supabase. -> Mitigación: Asegurar que los componentes manejen estados `loading` y `error`.
