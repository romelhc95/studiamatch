# Sistema DB Supabase

> **Actualizado**: 2026-07-05 · **Proyectos**: Free (`aqrldlmlszjtgpqiegaa`) y Pro (`xwhtiqmboljkshrtviyw`) · **Motor**: PostgreSQL 15+ (Supabase) + PostgREST

## Extensiones

> Verificado contra Pro (`xwhtiqmboljkshrtviyw`) el 2026-07-05.

| Extensión | Versión (Pro) | Schema | Uso |
|---|---|---|---|
| `pg_trgm` | 1.6 | `extensions` | Índice GIN `idx_courses_name_trgm` para búsqueda difusa |
| `vector` | 0.8.0 | `extensions` | Instalada; `enriched_programs.embedding` es `TEXT` (sin índice vectorial operativo) |
| `pg_net` | 0.20.0 | `extensions` | `net.http_post` desde trigger de leads → Edge Function |
| `pg_stat_statements` | 1.11 | `extensions` | Monitoreo de queries (Supabase interno) |
| `pgcrypto` | 1.3 | `extensions` | `gen_random_uuid()` |
| `uuid-ossp` | 1.1 | `extensions` | Funciones auxiliares UUID |

## Tablas Activas

### Catálogo público

#### `public.institutions`
Catálogo de instituciones educativas. (16 columnas)

| Columna                     | Tipo                       | Notas                                                          |
| :-------------------------- | :------------------------- | :------------------------------------------------------------- |
| `id`                        | `uuid`                     | PK · `gen_random_uuid()`                                       |
| `name`                      | `character varying`        | NOT NULL · Nombre de la institución                            |
| `slug`                      | `character varying`        | NOT NULL · UNIQUE · URL slug amigable                          |
| `website_url`               | `text`                     | URL base de scraping                                           |
| `official_website`          | `text`                     | URL del portal institucional                                   |
| `type`                      | `character varying`        | `CHECK (type IN ('Univ','Inst'))`                              |
| `status`                    | `character varying`        | `CHECK (status IN ('Activa','Inactiva'))` · default `'Activa'` |
| `region`                    | `character varying`        | Región geográfica (ej. `'Lima'`, `'Arequipa'`)                 |
| `address`                   | `text`                     | Dirección física de la sede principal                          |
| `contact_email`             | `text`                     | Correo de contacto · Agregado en Fase 67B                      |
| `location_lat`              | `numeric`                  | Coordenada latitud geográfica                                  |
| `location_long`             | `numeric`                  | Coordenada longitud geográfica                                 |
| `last_harvest_at`           | `timestamp with time zone` | Fecha/hora del último crawling                                 |
| `last_harvest_duration_sec` | `integer`                  | Duración del último scraping en segundos                       |
| `created_at`                | `timestamp with time zone` | default `now()`                                                |
| `updated_at`                | `timestamp with time zone` | default `now()`                                                |

#### `public.categories`
Catálogo de categorías para clasificar programas educativos. (4 columnas)

| Columna | Tipo | Notas |
| :--- | :--- | :--- |
| `id` | `uuid` | PK · `gen_random_uuid()` |
| `name` | `text` | NOT NULL · UNIQUE · Nombre de la categoría |
| `description` | `text` | Descripción corta |
| `created_at` | `timestamp with time zone` | default `now()` |

#### `public.category_rules`
Mapeo keyword → categoría para trigger de auto-asignación. (5 columnas)

| Columna | Tipo | Notas |
| :--- | :--- | :--- |
| `id` | `uuid` | PK · `gen_random_uuid()` |
| `category_id` | `uuid` | FK → `categories(id)` · `ON DELETE CASCADE` |
| `keyword` | `text` | NOT NULL · UNIQUE · Palabra clave para coincidencia |
| `priority` | `integer` | Prioridad de ejecución del match · default `0` |
| `created_at` | `timestamp with time zone` | default `now()` |

#### `public.courses`
Tabla principal del catálogo de cursos y programas académicos. (39 columnas)

| Columna                   | Tipo                       | Notas                                                              |
| :------------------------ | :------------------------- | :----------------------------------------------------------------- |
| `id`                      | `uuid`                     | PK · `gen_random_uuid()`                                           |
| `institution_id`          | `uuid`                     | FK → `institutions(id)` · `ON DELETE CASCADE`                      |
| `name`                    | `character varying`        | NOT NULL · Nombre del curso/programa                               |
| `slug`                    | `character varying`        | NOT NULL · Generado con UUID prefix para unicidad                  |
| `url`                     | `text`                     | UNIQUE · URL origen del programa                                   |
| `price_pen`               | `numeric`                  | Precio estimado en Soles · `CHECK (price_pen >= 0)`                |
| `price_status`            | `text`                     | default `'publicado'` · Estado de visualización de precios         |
| `mode`                    | `character varying`        | Modalidad · `CHECK (mode IN ('Presencial','Hibrido','Remoto'))`    |
| `duration`                | `character varying`        | Texto libre (ej. `"12 meses"`, `"40 horas"`)                       |
| `category_id`             | `uuid`                     | FK → `categories(id)` · Auto-asignado por trigger                  |
| `category`                | `character varying`        | Texto descriptivo legacy de la categoría                           |
| `category_confirmed`      | `boolean`                  | default `false` · Confirmación manual/curada de categoría          |
| `description_long`        | `text`                     | Descripción enriquecida                                            |
| `syllabus`                | `text`                     | Módulos o temario del curso                                        |
| `target_audience`         | `text`                     | Público objetivo                                                   |
| `requirements`            | `text`                     | Requisitos y pre-requisitos de admisión                            |
| `certification`           | `text`                     | Tipo de certificación otorgada                                     |
| `benefits`                | `text`                     | Beneficios del programa                                            |
| `objectives`              | `text`                     | Objetivos de aprendizaje                                           |
| `expected_monthly_salary` | `numeric`                  | Salario mensual proyectado en PEN                                  |
| `seniority_level`         | `character varying`        | Nivel laboral estimado · default `'Mid'`                           |
| `roi_months`              | `numeric`                  | Retorno de inversión en meses · default `0`                        |
| `course_type`             | `text`                     | Tipo de programa (ej. `'curso'`, `'diplomado'`, `'maestria'`)      |
| `brochure_url`            | `text`                     | URL del brochure descargable                                       |
| `brochure_text`           | `text`                     | Texto extraído del brochure                                        |
| `is_active`               | `boolean`                  | default `true` · Switch de estado lógico                           |
| `is_verified`             | `boolean`                  | default `false` · Marca de calidad y curación de datos             |
| `start_date`              | `date`                     | Fecha de inicio estructurada (Fase 73)                             |
| `start_date_text`         | `character varying`        | Texto original de fecha de inicio                                  |
| `last_scraped_at`         | `timestamp with time zone` | Fecha de la última recolección                                     |
| `last_404_at`             | `timestamp with time zone` | Seteado por FG3 integrity ping si la página cae                    |
| `view_count`              | `integer`                  | default `0` · Contador de visualizaciones                          |
| `comparison_count`        | `integer`                  | default `0` · Contador de comparaciones                            |
| `provider_used`           | `text`                     | default `'mock'` · LLM provider que enriqueció el curso            |
| `is_mock_data`            | `boolean`                  | default `true` · Indica si los datos fueron generados por fallback |
| `address`                 | `text`                     | Dirección específica del campus del curso                          |
| `region`                  | `character varying`        | Región asignada al curso                                           |
| `created_at`              | `timestamp with time zone` | default `now()`                                                    |
| `updated_at`              | `timestamp with time zone` | default `now()`                                                    |

#### `public.market_salaries`
Datos maestros de salarios de mercado por categoría. (7 columnas)

| Columna | Tipo | Notas |
| :--- | :--- | :--- |
| `id` | `uuid` | PK · `gen_random_uuid()` |
| `category_id` | `uuid` | FK → `categories(id)` |
| `category_name` | `text` | NOT NULL · UNIQUE |
| `salary_junior` | `numeric` | NOT NULL · Salario mensual junior estimado |
| `salary_average` | `numeric` | NOT NULL · Salario mensual promedio estimado |
| `salary_senior` | `numeric` | NOT NULL · Salario mensual senior estimado |
| `last_updated` | `timestamp with time zone` | default `now()` · Última actualización manual/cálculo |

### Social / Leads

#### `public.leads`
Captura de leads interesados desde el frontend. (15 columnas)

| Columna | Tipo | Notas |
| :--- | :--- | :--- |
| `id` | `uuid` | PK · `gen_random_uuid()` |
| `first_name` | `character varying` | NOT NULL · Nombre del interesado |
| `last_name` | `character varying` | Apellido |
| `email` | `character varying` | NOT NULL · Correo de contacto |
| `whatsapp` | `character varying` | NOT NULL · Teléfono móvil |
| `type` | `public.lead_type` | ENUM · `'info'` o `'recommendation'` |
| `status` | `public.lead_status` | ENUM · `'pending'`, `'contacted'`, `'resolved'` |
| `course_id` | `uuid` | FK → `courses(id)` |
| `source_page` | `text` | URL de origen · Agregado en Fase 67B |
| `area_interest` | `text` | Área de interés declarada |
| `budget` | `numeric` | Presupuesto máximo del usuario |
| `modality` | `text` | Modalidad preferida |
| `description` | `text` | Mensaje adicional o notas de asesoramiento |
| `is_late_enrollment_request` | `boolean` | default `false` · Solicitud extemporánea |
| `created_at` | `timestamp with time zone` | default `now()` |

#### `public.ratings`
Calificaciones cuantitativas de los cursos. (5 columnas)

| Columna | Tipo | Notas |
| :--- | :--- | :--- |
| `id` | `uuid` | PK · `gen_random_uuid()` |
| `course_id` | `uuid` | NOT NULL · Relación lógica a `courses.id` |
| `rating_value` | `integer` | NOT NULL · Puntuación de `1` a `5` |
| `user_nickname` | `character varying` | NOT NULL · Apodo del estudiante |
| `created_at` | `timestamp with time zone` | NOT NULL · default `now()` |

#### `public.reviews`
Reseñas y comentarios escritos de los estudiantes. (5 columnas)

| Columna | Tipo | Notas |
| :--- | :--- | :--- |
| `id` | `uuid` | PK · `gen_random_uuid()` |
| `course_id` | `uuid` | NOT NULL · Relación lógica a `courses.id` |
| `content` | `text` | NOT NULL · Comentario de la reseña |
| `user_nickname` | `character varying` | NOT NULL · Apodo del estudiante |
| `created_at` | `timestamp with time zone` | NOT NULL · default `now()` |

#### `public.email_log`
Registro histórico de emails enviados de manera automática. (9 columnas)

| Columna | Tipo | Notas |
| :--- | :--- | :--- |
| `id` | `uuid` | PK · `gen_random_uuid()` |
| `lead_id` | `uuid` | FK → `leads(id)` |
| `recipient_type` | `text` | NOT NULL · `'user'`, `'admin'` o `'institution'` |
| `recipient_email` | `text` | NOT NULL · Destinatario del correo |
| `status` | `text` | NOT NULL · `'pending'`, `'sent'` o `'failed'` |
| `subject` | `text` | Asunto del email |
| `resend_id` | `text` | ID transaccional del proveedor Resend |
| `error_message` | `text` | Detalle del error en caso de fallo |
| `created_at` | `timestamp with time zone` | default `now()` |

### Pipeline ETL / Harvester

#### `public.institution_site_profiles`
Configuración detallada por institución para el crawler/harvester. (43 columnas)

| Columna | Tipo | Notas |
| :--- | :--- | :--- |
| `id` | `uuid` | PK · `gen_random_uuid()` |
| `institution_id` | `uuid` | NOT NULL · UNIQUE · FK → `institutions(id)` |
| `site_type` | `text` | NOT NULL · Tipo de sitio (ej. `'traditional_ssr'`, `'spa_js_heavy'`, `'ecommerce'`, etc.) |
| `discovery_mode` | `text` | NOT NULL · Estrategia de descubrimiento (`'sitemap_bfs'`, `'paginated_catalog'`) |
| `seed_urls` | `jsonb` | default `'[]'` · URLs semilla para el crawling |
| `exclusion_patterns` | `jsonb` | default `'[]'` · Substrings/regex de exclusión de URLs |
| `allowed_url_patterns` | `jsonb` | default `'[]'` · Whitelist positiva de regex para URLs válidas |
| `noise_patterns` | `jsonb` | default `'[]'` · Textos ruidosos institucionales a remover |
| `catalog_url_patterns` | `jsonb` | default `'[]'` · Patrones de URLs de catálogos |
| `catalog_link_selector` | `text` | CSS selector para enlaces de cursos en catálogos |
| `catalog_max_pages` | `integer` | default `5` · Límite de paginación del catálogo |
| `requires_stealth` | `boolean` | default `false` · Activa navegación con huella stealth |
| `requires_cloudflare_bypass` | `boolean` | default `false` · Flag para bypass de WAF |
| `price_regex` | `text` | Expresión regular para localizar precio en HTML |
| `duration_regex` | `text` | Expresión regular para localizar duración en HTML |
| `pipeline_ready` | `boolean` | Gate general de 5 capas (Fase 75) |
| `discovery_enabled` | `boolean` | NOT NULL · Habilita el descubrimiento automático |
| `pipeline_enabled` | `boolean` | NOT NULL · Habilita procesamiento ETL completo |
| `production_enabled` | `boolean` | NOT NULL · default `false` · Habilita publicación en producción (Pro) |
| `auto_generated` | `boolean` | NOT NULL · default `false` · Indica si fue creado autodetectado |
| `circuit_open` | `boolean` | NOT NULL · default `false` · Circuit breaker de seguridad |
| `section_keywords` | `jsonb` | Hints de palabras clave para extracción LLM |
| `field_defaults` | `jsonb` | Valores fallback para propiedades vacías |
| `section_mode_map` | `jsonb` | Mapeo de URL/keywords a modalidad física |
| `max_courses_per_run` | `integer` | default `500` · Límite máximo de procesamiento |
| `created_at` | `timestamp with time zone` | default `now()` |
| `updated_at` | `timestamp with time zone` | default `now()` |
| `catalog_scroll_iterations` | `integer` |default `0` · Iteraciones de scroll en SPA |
| `circuit_opened_at` | `timestamp with time zone` | Timestamp en que saltó el circuit breaker |
| `detail_wait_ms` | `integer` | default `2000` · Espera entre peticiones de cursos |
| `extraction_confidence` | `jsonb` | NOT NULL · default `'{}'` · Límites de confianza |
| `extraction_transforms` | `jsonb` | NOT NULL · default `'{}'` · Modificadores post-scraping |
| `field_selectors` | `jsonb` | NOT NULL · default `'{}'` · Selectores CSS específicos |
| `label_selectors` | `jsonb` | NOT NULL · default `'{}'` · Selectores para etiquetas del sitio |
| `max_consecutive_errors` | `integer` | NOT NULL · default `5` · Límite para circuit breaker |
| `notes` | `text` | Notas operativas de mantenimiento |
| `popup_close_selectors` | `jsonb` | default `'[]'` · CSS para cerrar modales de publicidad |
| `section_course_type_map` | `jsonb` | default `'{}'` · Mapeo a tipo de programa |
| `soft_delete_before_scrape` | `boolean` | default `false` · Inactiva registros previos antes de scrapear |
| `title_prefix_removals` | `jsonb` | default `'[]'` · Textos a podar en títulos |
| `title_split_separators` | `jsonb` | default `'[]'` · Separadores para cortar nombres |
| `url_type_rules` | `jsonb` | NOT NULL · default `'[]'` · Reglas de clasificación URL |
| `warmup_url` | `text` | URL de calentamiento de sesión previa |

#### `public.staging_raw`
Estación 1: HTML crudo recolectado por el Harvester. (19 columnas)

| Columna | Tipo | Notas |
| :--- | :--- | :--- |
| `id` | `uuid` | PK · `gen_random_uuid()` |
| `institution_id` | `uuid` | FK → `institutions(id)` · `ON DELETE SET NULL` |
| `url` | `text` | UNIQUE · URL recolectada |
| `raw_name` | `text` | Título crudo de la página |
| `raw_description` | `text` | Meta-descripción o texto inicial de la página |
| `raw_html` | `text` | HTML crudo de la página origen (hasta 500KB) |
| `html_content` | `text` | Texto purgado o simplificado para tokens LLM |
| `raw_json_ld` | `jsonb` | JSON-LD extraído estructurado |
| `raw_og_tags` | `jsonb` | Meta tags OpenGraph de la página |
| `content_hash` | `text` | Hash SHA-256 del HTML para evitar procesar duplicados |
| `effective_url` | `text` | URL final post redireccionamientos |
| `canonical_url` | `text` | URL canonical declarada en el HTML |
| `status` | `text` | default `'pending'` · `discovered→pending→processing→processed/discarded/error` |
| `discard_reason` | `text` | Razón por la cual se descartó la URL |
| `processing_error` | `text` | Traza del error si el procesamiento falló |
| `metadata` | `jsonb` | default `'{}'` · Configuración o auditoría de crawling |
| `last_harvested_at` | `timestamp with time zone` | Fecha de descarga |
| `description_long` | `text` | Descripción extendida recolectada en crudo |
| `created_at` | `timestamp with time zone` | default `now()` |

#### `public.cleansed_programs`
Estación 2: HTML limpio, unificado y depurado de ruido. (15 columnas)

| Columna | Tipo | Notas |
| :--- | :--- | :--- |
| `id` | `uuid` | PK · `gen_random_uuid()` |
| `staging_id` | `uuid` | ID de la fuente en `staging_raw` |
| `institution_id` | `uuid` | FK → `institutions(id)` · `ON DELETE SET NULL` |
| `url` | `text` | UNIQUE · URL canonical del programa |
| `effective_url` | `text` | URL efectiva de scraping |
| `canonical_url` | `text` | URL canonical de la página |
| `clean_name` | `text` | Nombre del curso normalizado |
| `clean_description` | `text` | Descripción consolidada sin tags CSS/JS |
| `modality` | `text` | Modalidad extraída en crudo |
| `location` | `text` | Ubicación física declarada |
| `base_price` | `numeric` | Precio parseado en crudo |
| `currency` | `text` | default `'PEN'` · Moneda detectada |
| `status` | `text` | default `'pending'` · `pending→processing→enriched/skipped/synced` |
| `metadata` | `jsonb` | default `'{}'` · Información extra de depuración |
| `created_at` | `timestamp with time zone` | default `now()` |

#### `public.enriched_programs`
Estación 3: Datos de programas estructurados en base a los 14 Pilares (LLM). (29 columnas)

| Columna | Tipo | Notas |
| :--- | :--- | :--- |
| `id` | `uuid` | PK · `gen_random_uuid()` |
| `cleansed_id` | `uuid` | UNIQUE · ID de la fuente en `cleansed_programs` |
| `institution_id` | `uuid` | FK → `institutions(id)` · `ON DELETE SET NULL` |
| `url` | `text` | URL del programa |
| `official_name` | `text` | Nombre oficial determinado por el LLM |
| `duration_text` | `text` | Texto descriptivo de la duración (ej. `"3 meses"`) |
| `duration_months` | `integer` | Duración convertida a meses · Sanitizado con `int(float())` |
| `total_cost_est` | `numeric` | Costo estimado normalizado a PEN |
| `requirements` | `text` | Lista de requisitos estructurada |
| `graduate_profile` | `text` | Perfil del egresado estructurado |
| `curriculum_summary` | `jsonb` | Temario estructurado en JSONB |
| `modality` | `text` | Modalidad normalizada (`'Presencial'`, `'Hibrido'`, `'Remoto'`) |
| `primary_campus` | `text` | Sede principal donde se dicta |
| `degree_type` | `text` | Tipo de certificación académico |
| `start_date` | `text` | Fecha de inicio inferida por LLM (tipo `text`) |
| `partnerships` | `text` | Alianzas estratégicas |
| `certifications` | `text` | Certificaciones otorgadas |
| `language` | `text` | Idioma de dictado |
| `categories` | `text` | Categoría asignada por LLM |
| `difficulty_level` | `text` | Nivel del curso (ej. `'Introductorio'`, `'Avanzado'`) |
| `ai_summary` | `text` | Resumen breve generado por IA |
| `embedding` | `text` | Almacenamiento vectorial en texto |
| `provider_used` | `text` | LLM proveedor que realizó la llamada (Gemini/CF/GH) |
| `is_mock_data` | `boolean` | Indica si se usó fallback ante fallo del LLM |
| `status` | `text` | default `'pending'` · `pending→synced/error/skipped` |
| `brochure_url` | `text` | URL asociada al folleto informativo |
| `metadata` | `jsonb` | default `'{}'` · Metadata del procesamiento de IA |
| `created_at` | `timestamp with time zone` | default `now()` |
| `updated_at` | `timestamp with time zone` | default `now()` |

### Otras

#### `public.crawler_exclusions`
> **ATENCIÓN**: Esta tabla NO fue eliminada en Pro. Existe con 0 filas pero la estructura, índices, FK y políticas RLS siguen activos. Las exclusiones funcionales se manejan via `institution_site_profiles.exclusion_patterns`. (6 columnas)

| Columna | Tipo | Notas |
| :--- | :--- | :--- |
| `id` | `uuid` | PK · `gen_random_uuid()` |
| `institution_id` | `uuid` | FK → `institutions(id)` |
| `pattern` | `text` | NOT NULL · Patrón de URL a excluir |
| `reason` | `text` | Razón de la exclusión |
| `is_active` | `boolean` | default `true` |
| `created_at` | `timestamp with time zone` | default `now()` |

#### `public.schema_repair_audit`
Tabla de control para auditorías DDL y migraciones críticas sobre el esquema. (6 columnas)

| Columna | Tipo | Notas |
| :--- | :--- | :--- |
| `id` | `bigint` | PK · `BIGSERIAL` autoincremental |
| `migration_name` | `text` | NOT NULL · Nombre del archivo de migración |
| `table_name` | `text` | NOT NULL · Tabla afectada |
| `record_id` | `uuid` | NOT NULL · ID del registro reparado/auditado |
| `old_values` | `jsonb` | NOT NULL · Copia de respaldo de los datos anteriores |
| `created_at` | `timestamp with time zone` | NOT NULL · default `now()` |

## Funciones RPC

> Verificado contra Pro el 2026-07-05. 19 funciones en `public`.

| Función | Tipo | Propósito | Acceso |
|---|---|---|---|
| `lock_staging_records(inst_id uuid, batch_size int)` | `plpgsql` | `RETURNS TABLE` — SELECT con `FOR UPDATE SKIP LOCKED` para Harvester | `SECURITY DEFINER` |
| `unlock_staging_record(rec_id uuid, new_status text, reason text)` | `sql` | Libera un registro staging asignando estado final (`processed`/`discarded`/`error`) | SQL |
| `lock_cleansed_records(batch_size int)` | `plpgsql` | `RETURNS TABLE` — Reserva registros cleansed con `FOR UPDATE SKIP LOCKED` | `SECURITY DEFINER` |
| `mark_cleansed_processing(rec_ids uuid[])` | `sql` | Cambia estado de cleansed a `processing` | SQL |
| `unlock_cleansed_record(rec_id uuid, new_status text, error_msg text)` | `sql` | Registra fin de análisis en cleansed | SQL |
| `atomic_cleansing_promote(p_staging_ids uuid[], p_cleansed_data jsonb)` | `plpgsql` | `RETURNS SETOF cleansed_programs` — Promueve atómicamente staging→cleansed | `SECURITY DEFINER` |
| `atomic_enrichment_promote(p_enriched_data jsonb, p_cleansed_id uuid)` | `plpgsql` | `RETURNS SETOF enriched_programs` — Promueve atómicamente cleansed→enriched | `SECURITY DEFINER` |
| `requeue_pipeline_records(institution_id uuid)` | `plpgsql` | `RETURNS TABLE` — Reencola registros en error para reprocesamiento (Fase 75) | `SECURITY DEFINER` |
| `fn_auto_assign_category()` | `plpgsql` | Trigger — Asigna `category_id` y `category` por keyword matching contra `category_rules` | — |
| `increment_view_count(p_course_id uuid)` | `sql` | `RETURNS void` — Incrementa `view_count` atómicamente | `anon`/`authenticated`/`service_role` |
| `exec_sql(sql_text text)` | `plpgsql` | `RETURNS void` — Ejecuta DDL arbitrario (usado por `db_migrate.py`) | Solo `service_role` |
| `notify_new_lead()` | `plpgsql` | Trigger — Llama `net.http_post` a Edge Function de notificación | — |
| `repair_jsonb_array(jsonb)` | `plpgsql` | `RETURNS jsonb` — Sanitiza arrays JSONB malformados en profiles | — |
| `repair_jsonb_object(jsonb)` | `plpgsql` | `RETURNS jsonb` — Sanitiza objetos JSONB malformados en profiles | — |
| `validate_institution_site_profiles_jsonb()` | `plpgsql` | Trigger — Valida y repara campos JSONB en `institution_site_profiles` | — |
| `deactivate_courses_when_production_disabled()` | `plpgsql` | Trigger — Desactiva cursos si `production_enabled` cambia a `false` | — |
| `update_updated_at_column()` | `plpgsql` | Trigger genérico — `NEW.updated_at = now()` | — |
| `update_updated_at()` | `plpgsql` | Trigger alternativo — misma funcionalidad que `update_updated_at_column` | — |
| `rls_auto_enable()` | `plpgsql` | Event trigger — Habilita RLS automáticamente en tablas nuevas (Supabase interno) | — |

## Triggers

| Trigger | Tabla | Evento | Función |
|---|---|---|---|
| `tr_auto_assign_category` | `courses` | `BEFORE INSERT OR UPDATE OF name, description_long, syllabus` | `fn_auto_assign_category()` |
| `tr_enriched_programs_updated_at` | `enriched_programs` | `BEFORE UPDATE` | `update_updated_at_column()` |
| `trg_validate_institution_site_profiles_jsonb` | `institution_site_profiles` | `BEFORE INSERT OR UPDATE` | `repair_jsonb_object()` / `repair_jsonb_array()` |
| `trg_deactivate_courses_when_production_disabled` | `institution_site_profiles` | `AFTER UPDATE OF production_enabled` | `deactivate_courses_when_production_disabled()` |
| `trg_notify_new_lead` | `leads` | `AFTER INSERT` | `notify_new_lead()` |

## Políticas RLS

> Verificado contra Pro el 2026-07-05. Las políticas listadas son las que existen en producción.

### Tablas públicas (catálogo)

| Tabla | Rol | Permiso | Condición |
|---|---|---|---|
| `courses` | `anon` | `SELECT` | `is_active = true AND is_verified = true AND EXISTS (SELECT 1 FROM institution_site_profiles p WHERE p.institution_id = courses.institution_id AND p.production_enabled = true)` |
| `courses` | `authenticated` | `SELECT` | Ídem |
| `courses` | `service_role` | `ALL` | `true` |
| `institutions` | `anon`, `authenticated` | `SELECT` | `true` |
| `institutions` | `service_role` | `ALL` | `true` |
| `categories` | `public` | `SELECT` | `true` |
| `category_rules` | `public` | `SELECT` | `true` |
| `market_salaries` | `anon`, `authenticated` | `SELECT` | `true` |
| `market_salaries` | `service_role` | `ALL` | `true` |
| `institution_site_profiles` | `anon`, `authenticated` | `SELECT` | `production_enabled = true` (solo columnas `institution_id` y `production_enabled`) |
| `institution_site_profiles` | `service_role` | `ALL` | `true` |

### Social / Leads

| Tabla | Rol | Permiso | Condición |
|---|---|---|---|
| `leads` | `anon`, `authenticated` | `INSERT` | `true` |
| `leads` | `service_role` | `ALL` | `true` |
| `ratings` | `public` | `SELECT`, `INSERT` | INSERT verifica `rating_value 1..5` y nickname no vacío |
| `reviews` | `public` | `SELECT`, `INSERT` | INSERT verifica contenido y nickname no vacíos |

### Email Log

| Tabla | Rol | Permiso | Condición |
|---|---|---|---|
| `email_log` | `authenticated` | `SELECT` | `true` |
| `email_log` | `service_role` | `ALL` | `true` |

### Tablas ETL (pipeline)

| Tabla | Rol | Permiso | Condición |
|---|---|---|---|
| `staging_raw` | `anon` | — (bloqueado) | `USING (false)` |
| `staging_raw` | `service_role` | `ALL` | `true` |
| `cleansed_programs` | `anon` | — (bloqueado) | `USING (false)` |
| `cleansed_programs` | `service_role` | `ALL` | `true` |
| `enriched_programs` | `anon` | — (bloqueado) | `USING (false)` |
| `enriched_programs` | `service_role` | `ALL` | `true` |

### Tabla legacy (existe pero vacía)

| Tabla | Rol | Permiso | Condición |
|---|---|---|---|
| `crawler_exclusions` | `anon`, `authenticated` | `SELECT` | `is_active = true` |
| `crawler_exclusions` | `service_role` | `ALL` | `true` |

### Ejecución de RPCs
- Acceso revocado a `PUBLIC`, `anon`, `authenticated` para todas las funciones internas.
- Concedido a `service_role` para todas las funciones.
- **Excepción**: `increment_view_count(p_course_id UUID)` tiene grant explícito a `anon`, `authenticated`, `service_role`.


## Índices

> Verificado contra Pro el 2026-07-05.

| Índice | Tabla | Tipo | Notas |
|---|---|---|---|
| `idx_courses_name_trgm` | `courses` | `GIN` (`name gin_trgm_ops`) | Búsqueda difusa por nombre |
| `idx_courses_start_date` | `courses` | `BTREE` parcial | `WHERE start_date IS NOT NULL` |
| `idx_courses_url_unique` | `courses` | `UNIQUE BTREE` (`url`) | Duplicado de `courses_url_key` |
| `idx_staging_raw_status` | `staging_raw` | `BTREE` (`status`) | |
| `idx_staging_raw_institution_status` | `staging_raw` | `BTREE` (`institution_id, status`) | Filtro por institución |
| `idx_staging_raw_url` | `staging_raw` | `BTREE` (`url`) | |
| `idx_cleansed_programs_status` | `cleansed_programs` | `BTREE` (`status`) | |
| `idx_cleansed_programs_staging` | `cleansed_programs` | `BTREE` (`staging_id`) | Trazabilidad |
| `idx_cleansed_programs_url` | `cleansed_programs` | `BTREE` (`url`) | |
| `idx_enriched_programs_status` | `enriched_programs` | `BTREE` (`status`) | |
| `idx_enriched_programs_cleansed` | `enriched_programs` | `BTREE` (`cleansed_id`) | |
| `idx_enriched_programs_url` | `enriched_programs` | `BTREE` (`url`) | |
| `idx_enriched_programs_url_unique` | `enriched_programs` | `UNIQUE BTREE` (`url`) | Dedup URL |
| `idx_profiles_institution` | `institution_site_profiles` | `BTREE` (`institution_id`) | |
| `idx_profiles_pipeline_ready` | `institution_site_profiles` | `BTREE` parcial | `WHERE pipeline_ready = true` |
| `idx_email_log_lead_id` | `email_log` | `BTREE` (`lead_id`) | |
| `idx_email_log_status` | `email_log` | `BTREE` (`status`) | |
| `idx_crawler_exclusions_active` | `crawler_exclusions` | `BTREE` parcial | `WHERE is_active = true` |
| `idx_crawler_exclusions_institution` | `crawler_exclusions` | `BTREE` (`institution_id`) | |
| `idx_crawler_exclusions_pattern_inst` | `crawler_exclusions` | `UNIQUE BTREE` (`institution_id, pattern`) | |

## Notas de Schema Drift

> Verificado contra Pro el 2026-07-05.

### Divergencias documentadas

- **`crawler_exclusions` NO fue eliminada en Pro**: Aunque `AGENTS.md` y la documentación indican "DROP TABLE en ambos ambientes", la tabla **existe en Pro** con 0 filas, 4 índices (`idx_crawler_exclusions_active`, `idx_crawler_exclusions_institution`, `idx_crawler_exclusions_pattern_inst`, `crawler_exclusions_pkey`), FK a `institutions(id)`, y 2 políticas RLS activas. Las exclusiones funcionales se manejan exclusivamente via `institution_site_profiles.exclusion_patterns`.
- **`mark_records_processing(uuid[])` no existe en Pro**: El `restore_full_schema.sql` la define, pero en Pro solo existe `mark_cleansed_processing`. Los harvesters deben usar `lock_staging_records` + `unlock_staging_record` sin paso intermedio de marcado masivo.
- **`ratings`/`reviews` tienen RLS PUBLIC en Pro**: Contrario a lo documentado en hardening Fase 115, ambas tablas permiten `SELECT` e `INSERT` a `public` (anon). No se aplicó la restricción a `authenticated`.
- **`institution_site_profiles` RLS**: La política `profiles_select_public` filtra por `production_enabled = true`, no expone todos los perfiles. Las columnas sensibles (`exclusion_patterns`, `allowed_url_patterns`, `field_selectors`, etc.) están protegidas por este filtro.
- **`enriched_programs.start_date`**: Tipo `TEXT` en Pro (almacena salida textual del LLM). La migración Fase 73 referenciaba `DATE` pero el tipo en producción es `text` con comment "Fecha de inicio parseada desde start_date TEXT".
- **`courses` tiene dos índices únicos sobre `url`**: `courses_url_key` (original) y `idx_courses_url_unique` (agregado por `production_full_replace.sql`). Ambos son funcionalmente redundantes pero coexisten.
- **Búsqueda vectorial no implementada**: Extensión `vector` 0.8.0 instalada pero `enriched_programs.embedding` es `TEXT`, sin índice `ivfflat`/`hnsw`. `sync_vector_worker.py` tiene la generación de embeddings como stub.
- **`restore_full_schema.sql` desactualizado**: No incluye columnas agregadas por Fases 67B, 73, 79B, 80, 100, 121 (`contact_email`, `start_date`, `provider_used`, `is_mock_data`, `view_count`, `comparison_count`, `circuit_open`, `auto_generated`, `field_selectors`, `label_selectors`, `url_type_rules`, `extraction_transforms`, `extraction_confidence`, `email_log`, `schema_repair_audit`).
