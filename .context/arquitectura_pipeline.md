# Arquitectura del Pipeline

> **Actualizado**: 2026-07-05 · **Orquestacion**: GitHub Actions + `master_orchestrator.py` · **Runtime**: Python 3.11 dentro de contenedor `ubuntu-latest`

## Vision General

El pipeline StudIAMatch transforma URLs de programas educativos en datos estructurados para el catalogo `courses`. Opera como una cadena de 4 estaciones secuenciales con una estacion de auditoria final.

```text
┌─────────────────────────────────────────────────────────────┐
│                    FG2 — Golden Pipeline                     │
│                                                             │
│  institutions + institution_site_profiles                   │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────────┐      ┌──────────────────┐            │
│  │ FG2-1 Harvester   │─────▶│ FG2-1.5 Cleansing │            │
│  │ universal_harv... │      │ cleansing_worker  │            │
│  │ master_orchest... │      └────────┬─────────┘            │
│  └──────────────────┘               │                       │
│         staging_raw                  ▼                       │
│                            ┌──────────────────┐            │
│                            │ FG2-2 Enrichment  │            │
│                            │ enrichment_worker │            │
│                            └────────┬─────────┘            │
│                    cleansed_programs│                       │
│                                     ▼                       │
│                            ┌──────────────────┐            │
│                            │ FG2-3 Sync Vector │            │
│                            │ sync_vector_worker│            │
│                            └────────┬─────────┘            │
│                    enriched_programs│                       │
│                                     ▼                       │
│                              courses (public)               │
│                                     │                       │
│                                     ▼                       │
│                            ┌──────────────────┐            │
│                            │ FG2-4 QA Audit    │            │
│                            └──────────────────┘            │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ FG3 — Daily Integrity Ping (independiente)            │  │
│  │ integrity_ping.py: HEAD checks, 404 detection,       │  │
│  │ expiration deactivation, catalog health              │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Workflows GitHub Actions

### `production_pipeline.yml` — FG2 Golden Pipeline

| Trigger | Detalle |
|---|---|
| `schedule` | `0 5 * * *` — Diario a las 5 AM UTC |
| `workflow_dispatch` | Manual |

| Job | Worker | Timeout | Dependencia | Necesita Secret Key |
|---|---|---|---|---|
| `phase_1_harvesting` | `master_orchestrator.py --limit 10 --skip-cleansing` | 350 min | — | Si (escribe a staging_raw) |
| `phase_1_5_cleansing` | `cleansing_worker.py` | 60 min | `phase_1_harvesting` | Si |
| `phase_2_enrichment` | `enrichment_worker.py` | 350 min | `phase_1_5_cleansing` | Si + CF_API_TOKEN + OPENCODE_API_KEY |
| `phase_3_sync` | `sync_vector_worker.py` | 60 min | `phase_2_enrichment` | Si |
| `phase_4_audit` | 3 scripts de auditoria + upload artifacts + CF Pages rebuild | 20 min | `phase_3_sync` | Solo publishable key |

**Seleccion de environment por branch**:
- `main` → `Production`
- `certificacion` → `Certification`
- resto → `Development`

**Post-pipeline**: En `main`, el job `phase_4_audit` dispara rebuild de Cloudflare Pages via API.

### `fg3_integrity.yml` — FG3 Daily Integrity

| Trigger | Detalle |
|---|---|
| `schedule` | `0 5 * * *` (marcado como desactivado, cron sintacticamente presente) |
| `workflow_dispatch` | Manual |

Ejecuta `integrity_ping.py`: HEAD-check de URLs activas, deteccion 404, desactivacion tras 3 dias, conteo de salud del catalogo.

### `fg1_inventory.yml` — Inventory

| Trigger | Detalle |
|---|---|
| `schedule` | `0 0 1 * *` (mensual, marcado como desactivado) |
| `workflow_dispatch` | Manual |

Ejecuta `discovery_institutions.py`: seeding de instituciones desde `config/institution_sources.json`.

### `db-sync-to-pro.yml` — DB Sync a Pro

| Trigger | Detalle |
|---|---|
| `push` | Solo `main` |
| `workflow_dispatch` | Manual |

- `db_migrate.py --env pro --dry-run` (deteccion)
- `db_migrate.py --env pro` (aplicacion)
- `check_db_parity.py --env pro --target-only` (verificacion)
- No ejecuta FG2 automaticamente post-sync

### `security-audit.yml` — CI Gate

| Trigger | Comportamiento |
|---|---|
| `pull_request` | En `desarrollo`, `certificacion`, `main` |
| `push` | En `desarrollo`, `certificacion`, `main` |

**Bloqueantes**: credential-scan (regex), python-check (`py_compile` en `scripts/core`, `scripts/maintenance`, `scripts/shared`)
**Informativos** (non-blocking): ESLint, TypeScript typecheck (`npx tsc --noEmit`)

## Estaciones del Pipeline en Detalle

### FG2-1: Harvester (`universal_harvester.py` + `master_orchestrator.py`)

**Orquestador**: `master_orchestrator.py` itera sobre instituciones ordenadas por `last_harvest_at`, con freshness guard: skip si catalogo denso fue cosechado hace <3 dias.

**Descubrimiento**:
- `hardcoded_urls`: URLs semilla directas del profile
- `paginated_catalog`: Navegacion de paginas de catalogo
- `catalog_link_extraction`: Extraccion de links desde paginas indice
- `sitemap_bfs`: BFS desde sitemaps XML (default)

**Extraccion**:
- `traditional_ssr`: HTTP GET + BeautifulSoup
- `spa_js_heavy` / `ecommerce`: Playwright (Chromium headless)

**Anti-bot**:
- User agents aleatorios
- `requires_stealth`: playwright-stealth
- `requires_cloudflare_bypass`: espera de challenge + warmup URL
- Circuit breaker: se abre con 403/429 repetidos, persiste en `circuit_open`

**Dedup**: Content hashing (SHA256 del texto limpio) — solo re-procesa URLs cuyo HTML cambio.

**Time Guard**: Cap global de ~5h40m (20400s) con shutdown elegante.

### FG2-1.5: Cleansing (`cleansing_worker.py`)

**Flujo**:
1. Lock de records `pending` via RPC `lock_staging_records` (fallback: SELECT)
2. Limpieza agresiva de HTML
3. Agrupacion de sub-paginas hermanas por URL base normalizada
4. Seleccion del mejor nombre (title/H1/paginas de presentacion)
5. Filtros de calidad:
   - Soft 404
   - Hub/listing pages
   - Nombres/descripciones demasiado cortos
   - Anos obsoletos
   - Fechas de inicio expiradas
   - `exclusion_patterns` + `noise_patterns` del profile
6. Extraccion: modalidad, ubicaciones, precio (regex del profile o fallback), fecha de inicio
7. Promocion atomica via RPC `atomic_cleansing_promote` (fallback: upsert + patch)

### FG2-2: Enrichment (`enrichment_worker.py`)

**14 pilares** extraidos por LLM:
1. `official_name` — Nombre oficial del programa
2. `duration_text` / `duration_months` — Duracion
3. `total_cost_est` — Costo total estimado
4. `requirements` — Requisitos de admision
5. `graduate_profile` — Perfil del egresado
6. `curriculum_summary` — Resumen curricular (JSONB)
7. `modality` — Modalidad
8. `primary_campus` — Campus principal
9. `degree_type` — Tipo de titulo/certificacion
10. `start_date` — Fecha de inicio
11. `partnerships` — Alianzas/convenios
12. `certifications` — Certificaciones incluidas
13. `categories` — Categorias tematicas
14. `ai_summary` — Resumen generado por IA

**Provider fallback (triple cloud)**:
1. DeepSeek via OpenCode endpoint (`OPENCODE_API_KEY`)
2. Cloudflare Workers AI (`CF_API_TOKEN`, `CF_ACCOUNT_ID`)
3. Smart mock fallback si todos los providers degradan

`ProviderOrchestrator` maneja health checks, ordenamiento de providers, degradacion y limpieza de JSON.

**Post-procesamiento**: normalizacion de modality, parseo de precio (`S/ 1,500` → float), sanitizacion de `duration_months` (`int(float())`), rechazo de strings `"None"`/`"null"`.

**Promocion**: `atomic_enrichment_promote` (RPC) o upsert + patch como fallback.

### FG2-3: Sync (`sync_vector_worker.py`)

**Golden Path writer** a `courses`:
1. Re-check de `pipeline_enabled`
2. Validacion de ruido institucional (ultima capa antes de publicar)
3. Rechazo de nombres invalidos
4. Generacion de slugs legibles con UUID prefix
5. Parseo de `start_date`; marcado de cursos expirados como inactivos (90 dias de gracia)
6. Si `production_enabled=false`, escribe curso inactivo
7. Aplicacion de defaults y mapeos del profile
8. Computo de seniority + ROI:
   - `duration_months → hours`
   - `infer_seniority(junior/mid/senior)`
   - `lookup_market_salary(category)`
   - `compute_roi(cost, salary)`
9. Escritura en `courses` por `url`: preserva cursos existentes con `is_active=false`, actualiza solo filas activas e inserta si no existe
10. Marca enriched como `synced` o `error`

**Embeddings**: Stub — la generacion de vectores no esta implementada.

### FG3: Integrity (`integrity_ping.py`)

Monitoreo independiente del catalogo:
- Cuenta instituciones y cursos
- Flaggea cursos activos sin `syllabus` u `objectives`
- Desactiva cursos con `start_date > 90 dias`
- HEAD-check de todas las URLs activas:
  - Primer 404 → setea `last_404_at`
  - 404 persistente >3 dias → `is_active=false`
  - URL recuperada → limpia `last_404_at`

### FG2-4: QA Audit

Scripts ejecutados secuencialmente en `phase_4_audit`:
- `quality_assurance_audit.py` — Campos faltantes en 14 pilares, resumenes largos
- `taxonomy_roi_audit.py` — Consistencia categoria/salario/ROI
- `category_coverage_audit.py` — Cobertura de `category_confirmed`, keywords sugeridas

## Sistema de Gating (5 capas)

| Capa | Worker | Mecanismo |
|---|---|---|
| 0 | Todos | `pipeline_ready` / `pipeline_enabled` gate en profile |
| 1 | Harvester + Cleansing | `exclusion_patterns` con prefijo `re:` para regex |
| 2 | Cleansing | `NOISE_NAME_PATTERNS` y patrones institucionales |
| 3 | Enrichment | Regla absoluta en prompt LLM (devolver null para paginas no-programa) |
| 4 | Sync | Validacion final de `noise_patterns` antes de escribir en `courses` |

**Jerarquia de gates moderna** (sobreescribe `pipeline_ready` legacy):
- `discovery_enabled`: controla si el harvester descubre URLs
- `pipeline_enabled`: controla scraping+cleansing+enrichment+sync (`=> discovery_enabled`)
- `production_enabled`: controla si cursos son publicos (`=> pipeline_enabled`)

## `db_client.py` — Cliente de Datos

Cliente REST/PostgREST singleton para todos los scripts Python.

**Key hierarchy**:
- **Publishable key** (`sb_publishable_*`): Lecturas publicas con RLS
- **Secret key** (`sb_secret_*`): Escrituras + lecturas de tablas pipeline (bypass RLS)

**Tablas pipeline protegidas**: `staging_raw`, `cleansed_programs`, `enriched_programs`, `institution_site_profiles` → usan `select_pipeline()` / `select_all_pipeline()` que requieren secret key.

**API methods**: `select`, `insert`, `upsert`, `patch`, `delete`, `rpc`, `count`, `select_all` (paginacion 1000 registros).

**Retry**: 3 intentos con backoff exponencial (5s, 10s, 20s) para errores DNS/Connection.

**Regla critica**: `db.rpc()` NO usa `json.dumps()` en parametros (el metodo serializa con `json=`). Si se usa `json.dumps()`, causa error "cannot extract elements from a scalar".

## Entorno de Desarrollo (Docker)

```bash
docker compose up -d --build       # Contenedor studiamatch-dev (Debian)
docker exec -it studiamatch-dev bash
```

- `node:20-bookworm` con Python 3, pip, dependencias de Playwright
- Monta `.env.local` como variables de entorno
- Puerto 3000 expuesto para Next.js dev server
- `init-container.sh` para instalacion inicial (npm + pip + playwright)

## Limitaciones Operativas

- Sin base de datos local — todo opera contra Supabase cloud
- Las escrituras del pipeline requieren secret key (RLS bloquea anon en tablas ETL)
- Embeddings vectoriales no implementados (stub en `sync_vector_worker.py`)
- `batch_enrich_courses.py` es bypass del golden pipeline (solo remediacion)
- `crawler_exclusions` legacy eliminado; exclusiones solo en `institution_site_profiles`
- FG1 y FG3 tienen cron sintacticamente presente pero marcados como desactivados
- Límite de 1000 registros por query PostgREST sin paginacion explicita
- `db_migrate.py` requiere `exec_sql` RPC en la DB target
