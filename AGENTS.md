# StudIAMatch — Developer Guide

## Regla de Ejecución de Fases

**SOLO ejecuta las tareas de una fase del IMPLEMENTATION_PLAN.md cuando el usuario lo apruebe explícitamente diciendo "Ejecuta las tareas pendientes de la Fase XX"**. No ejecutes cambios de código, eliminaciones de archivos, migraciones SQL, ni ninguna acción destructiva sin autorización explícita. Las fases del plan pueden ser analizadas, diagnosticadas y documentadas libremente, pero la ejecución requiere aprobación.

## Auditoría de Credenciales (Obligatorio antes de push)

**NUNCA** expongas credenciales (API keys, Publishable and secret API keys, management tokens, passwords, secret tokens) en el repositorio, ni público ni privado. Antes de cada `git push`:

1. Buscar strings con patrón `eyJhbG` (JWT), `sbp_` (Supabase management token), o cualquier URL que contenga un project ref real
2. Verificar que ningún script Python tenga credenciales hardcodeadas — usar `os.environ.get('VAR', '')` y salir con error si falta
3. Verificar que `.env*` esté en `.gitignore` (ya cubierto por `.env*` y `*.env`)
4. Los scripts que necesiten credenciales Pro deben leerlas de variables de entorno:
   - `NEXT_PUBLIC_SUPABASE_URL` — URL del proyecto Supabase Free/Pro
   - `NEXT_SUPABASE_PUBLISHABLE_KEY` — Publishable key: This key is safe to use in a browser if you have enabled Row Level Security (RLS) for your tables and configured policies. (Pro o Free según el ambiente)
   - `NEXT_SUPABASE_SECRET_KEY` — Secret keys: These API keys allow privileged access to your project's APIs. Use in servers, functions, workers or other backend components of your application.  (Pro o Free según el ambiente)
5. Para CI/CD, las credenciales van en GitHub Secrets por environment — nunca en el código
6. Si descubres credenciales hardcodeadas en el repo, reemplázalas con `os.environ.get()` inmediatamente

## Arquitectura Cloud-Only (Supabase)

Este proyecto NO tiene base de datos local. Todo el desarrollo usa la instancia Supabase Free tier apuntada por `.env.local`. Los scripts Python y el frontend Next.js comparten la misma base de datos cloud.

## Contenedor Docker (Obligatorio)

**NUNCA** ejecutes comandos de desarrollo (npm, python, pip) en el host Windows. Todo debe correr dentro del contenedor `studiamatch-dev` (Debian Linux) para garantizar paridad con los servidores de despliegue (Cloudflare/Linux).

```bash
# Construir e iniciar (una sola vez)
docker compose up -d --build

# Ejecutar init script dentro del contenedor (primera vez)
docker exec -it studiamatch-dev bash init-container.sh

# Comandos dentro del contenedor
docker exec -it studiamatch-dev bash
docker exec studiamatch-dev python3 scripts/core/sync_vector_worker.py
docker exec studiamatch-dev python3 -m py_compile scripts/core/universal_harvester.py
```

## Comandos de Desarrollo

```bash
# Frontend (dentro del contenedor, directorio /app/web)
npm run dev       # Next.js dev server en localhost:3000
npm run build     # Static export (output: out/)
npm run lint      # ESLint (reglas: core-web-vitals + TypeScript)

# TypeScript typecheck (dentro del contenedor, directorio /app/web)
npx tsc --noEmit  # Verificar tipos (0 errores esperado)

# Python (dentro del contenedor, directorio /app)
python3 scripts/core/universal_harvester.py
python3 scripts/core/cleansing_worker.py
python3 scripts/core/enrichment_worker.py
python3 scripts/core/sync_vector_worker.py

# Python syntax check
python3 -m py_compile scripts/core/<archivo>.py

# Ejecutar cualquier script desde /app (PYTHONPATH implícito)
python3 scripts/maintenance/<script>.py
```

## Variables de Entorno Desarrollo/Certifición

El archivo `.env.local` o `.env.gitdesa` (gitignored) contiene:

| Variable | Uso | Quién la necesita |
|---|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | URL del proyecto Supabase Free | Frontend + db_client.py |
| `NEXT_SUPABASE_PUBLISHABLE_KEY` | Publishable key (lectura pública, rotable) | Frontend + db_client.py |
| `NEXT_SUPABASE_SECRET_KEY` | Secret key (escritura bypass RLS, rotable) | Pipeline CI/CD **solamente** |
| `CF_ACCOUNT_ID` | Cloudflare Workers AI | enrichment_worker.py |
| `CF_API_TOKEN` | Cloudflare API token | enrichment_worker.py |
| `GH_MODELS_TOKEN` | GitHub Models (GPT-4o) | enrichment_worker.py |
| `GEMINI_API_KEY` | Google Gemini 1.5 Flash | enrichment_worker.py |
| `NEXT_PUBLIC_SUPABASE_URL` | URL del proyecto desarrollo | Scripts de migración diagnósticos |

**IMPORTANTE**: El contenedor Docker tiene acceso a `NEXT_SUPABASE_PUBLISHABLE_KEY` + `NEXT_SUPABASE_SECRET_KEY` alojadas en `.env.local`.

## Variables de Entorno Producción

El archivo `.env.gitprod` (gitignored) contiene:

| Variable | Uso | Quién la necesita |
|---|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | URL del proyecto Supabase Pro| Frontend + db_client.py |
| `NEXT_SUPABASE_PUBLISHABLE_KEY` | Publishable key (lectura pública, rotable) | Frontend + db_client.py |
| `NEXT_SUPABASE_SECRET_KEY` | Secret key (escritura bypass RLS, rotable) | Pipeline CI/CD **solamente** |
| `CF_ACCOUNT_ID` | Cloudflare Workers AI | enrichment_worker.py |
| `CF_API_TOKEN` | Cloudflare API token | enrichment_worker.py |
| `GH_MODELS_TOKEN` | GitHub Models (GPT-4o) | enrichment_worker.py |
| `GEMINI_API_KEY` | Google Gemini 1.5 Flash | enrichment_worker.py |
| `NEXT_PUBLIC_SUPABASE_URL` | URL del proyecto producción | Scripts de migración diagnósticos |

**IMPORTANTE**: El contenedor Docker tiene acceso a `NEXT_SUPABASE_PUBLISHABLE_KEY` + `NEXT_SUPABASE_SECRET_KEY` alojadas en `.env.gitprod`.

## Convenciones del Proyecto

### Sincronización Cross-Ambiente
- Los scripts que sincronizan datos entre Free y Pro (ej: `sync_pro_to_free.py`) DEBEN usar exclusivamente Publishable y Secret API keys (`sb_publishable_*` / `sb_secret_*`), NUNCA compartir credenciales entre ambientes ni hardcodear keys
- Credenciales Pro se leen de variables de entorno: `SUPABASE_URL`, `NEXT_SUPABASE_SECRET_KEY` y `NEXT_SUPABASE_PUBLISHABLE_KEY` alojadas en `.env.gitprod`
- Credenciales Free se leen de variables de entorno: `NEXT_SUPABASE_PUBLISHABLE_KEY` + `NEXT_SUPABASE_SECRET_KEY` alojadas en `.env.local` vía `db_client.py`
- Los UUIDs de institutions/categories **difieren entre Free y Pro** — sincronización requiere mapeo por slug/nombre
- Ambas keys son rotables ante exposición

## Fase 75: Exclusion Gate (`pipeline_ready`)

**Cada institución debe tener exclusiones afinadas antes de que el pipeline la procese.**

- `institution_site_profiles.pipeline_ready` (booleano, default `false`) — gate de 5 capas
- `pipeline_ready = false` → los 4 workers saltan la institución (harvester, cleansing, enrichment, sync)
- Para activar: afinar `exclusion_patterns`, revisar URLs descubiertas, luego set `pipeline_ready = true`
- `allowed_url_patterns` (JSONB) — whitelist positiva de regex para URLs que SÍ son programas

**Patrones regex** (prefijo `re:`): Los patterns en `exclusion_patterns` pueden comenzar con `re:` para usar búsqueda regex en vez de substring match. Ej: `re:agradecimiento` atrapa `/agradecimiento/` y `-agradecimiento/`.

**Capas de defensa**:
| Capa | Worker | Mecanismo |
|---|---|---|
| 0 | Todos | `pipeline_ready` gate |
| 1 | harvester + cleansing | Regex exclusion patterns (`re:` prefix) |
| 2 | cleansing | `NOISE_NAME_PATTERNS` (agradecimiento, matrícula, facultad de...) |
| 3 | enrichment | Regla absoluta en prompt LLM |
| 4 | sync | `NOISE_PATTERNS` post-sync validation |

### Git Flow
- `desarrollo` — rama activa de desarrollo (PR requerido, review técnico)
- `certificacion` — QA, E2E Playwright, auditoría de datos
- `main` — producción (Supabase Pro, despliegue automático a Cloudflare)
- Features: ramas `feat/*` que emergen de `desarrollo`

### Python: db_client.py
```python
import sys
sys.path.insert(0, '/app')
from scripts.shared.db_client import get_db_client

db = get_db_client()  # singleton, lee env vars automáticamente

# Métodos disponibles
db.select('courses', filters='is_active=eq.true', columns='id,name,slug,url')
db.insert('staging_raw', {'url': url, 'institution_id': inst_id, 'status': 'discovered'})
db.upsert('courses', course_data, on_conflict='url')
db.patch('courses', 'id=eq.abc', {'is_active': True})
db.delete('staging_raw', filters='status=eq.discarded')
db.rpc('atomic_cleansing_promote', {'p_staging_ids': [...], 'p_cleansed_data': [...]})
db.count('courses', filters='is_active=eq.true')
```

**Reglas críticas de db_client**:
- **NUNCA** uses `json.dumps()` en los parámetros de `db.rpc()` — el método ya serializa con `json=` internamente (causa error "cannot extract elements from a scalar").
- **Sí** usa `json.dumps()` para campos de tipo TEXT/JSONB que guardas vía `db.insert()` o `db.upsert()` (ej: `curriculum_summary`, `requirements`).
- Los filtros usan sintaxis PostgREST: `is_active=eq.true`, `name=is.null`, `status=in.(synced,pending)`.
- **Límite**: 1000 registros por query sin paginación (usa `db.select_all()` si necesitas más).
- **RLS**: El anon key NO puede escribir en tablas intermedias (`enriched_programs`, `cleansed_programs`, `staging_raw`). Solo SELECT está permitido. Para escritura se necesita `publishable_key` o `secret_key`.
- **Exclusiones**: Se gestionan exclusivamente vía `institution_site_profiles.exclusion_patterns` (JSONB). La tabla legacy `crawler_exclusions` fue eliminada (DROP TABLE en Pro, Free pendiente).

### Frontend: Next.js
- **Static export**: `next.config.js` → `output: 'export'` en producción para Cloudflare Pages
- **TypeScript errors ignorados en build**: `ignoreBuildErrors: true` (workaround por bug de Next.js 16 + React 19 en static export con `useOptimistic`)
- **Trailing slash**: habilitado (`trailingSlash: true`) para URLs consistentes
- **Path alias**: `@/*` → `web/src/*`
- **Rutas**: `/courses/[institution]/[slug]` (formato: `/courses/ulima/curso-ejemplo`)

### Supabase PostgREST
- **Syntax para NULL**: `column=is.null` (NO usar `column=eq.None` ni `column=eq.null`)
- **Syntax para múltiples valores**: `status=in.(synced,pending)`
- **Order**: `created_at.desc`
- **Count**: Usar `db.count()` o header `Prefer: count=exact`
- **Bulk insert**: `Content-Type: application/json` con array de objetos (NO `jsonb_array_elements` pattern)

## Arquitectura del Pipeline (4 Estaciones + Auditoría)

```
staging_raw ──→ cleansed_programs ──→ enriched_programs ──→ courses
   (1)              (2)                    (3)                (4)
Harvester       Cleansing              Enrichment           Sync Vector
                                   (LLM: CF→GH→Gemini)     + Embeddings
                                                               │
                                                    Frontend (Next.js)
                                                    Cloudflare Pages
```

| Fase | Script | Tabla fuente | Tabla destino | Lógica |
|---|---|---|---|---|
| FG2-1 | `universal_harvester.py` | Sitemaps + BFS crawl | `staging_raw` | Descubre y extrae HTML crudo (hasta 500KB) |
| FG2-1.5 | `cleansing_worker.py` | `staging_raw` | `cleansed_programs` | Limpia HTML, consolida subpáginas, filtra ruido |
| FG2-2 | `enrichment_worker.py` | `cleansed_programs` | `enriched_programs` | LLM extrae 14 pilares, triple-cloud fallback |
| FG2-3 | `sync_vector_worker.py` | `enriched_programs` | `courses` | Golden Path writer. Sincroniza datos finales |
| FG3 | `integrity_ping.py` | `courses` | `courses` (PATCH) | Verifica links 404, inactiva tras 3 días de gracia |

### Estados por tabla
| Tabla | Estados |
|---|---|
| `staging_raw` | `discovered` → `pending` → `processing` → `processed` / `error` / `discarded` |
| `cleansed_programs` | `pending` → `processing` → `synced` / `discarded` |
| `enriched_programs` | `pending` → `synced` / `discarded` |
| `courses` | `is_active` + `is_verified` (booleans independientes) |

## Notas Críticas de Arquitectura

1. **7 escritores a `courses`** (histórico, ahora solo 2): Los harvesters dedicados (IDAT, UPC, PUCP, USIL, UTP, U. Lima) escriben directo a `courses` con `is_verified=True`. Solo `sync_vector_worker.py` (Golden Path) e `integrity_ping.py` (PATCH mantenimiento) son los escritores autorizados restantes post-Fase 52.

2. **El anon key NO puede escribir en tablas ETL**: Cualquier script que necesite modificar `staging_raw`, `cleansed_programs`, `enriched_programs` **debe** usar `publishable_key` o `secret_key`. Si necesitas ejecutar algo local que modifique esas tablas, hazlo vía SQL en Supabase Dashboard.

3. **`batch_enrich_courses.py`** (scripts/maintenance/): Bypass del pipeline. Lee HTML de `staging_raw` y escribe directo a `courses`. Útil para corregir datos puntuales sin pasar por las 4 estaciones.

4. **Migraciones SQL**: Se ejecutan manualmente en Supabase Dashboard > SQL Editor. Los archivos en `db/migrations/` son la fuente de verdad. El contenedor no puede ejecutarlas (anon key sin permisos DDL).

5. **Time Guard**: `universal_harvester.py` tiene un límite de ejecución de 20400s (5h 40m) — 20 min antes del timeout de GitHub Actions (6h). Hace shutdown elegante.

6. **Content Hashing**: El harvester solo re-procesa URLs cuyo contenido HTML haya cambiado (compara SHA256 del texto limpio).

7. **Prompt LLM Rules**: El prompt de `enrichment_worker.py` instruye al LLM a responder `null` (NO el string `"None"`) cuando no puede inferir un campo. Las validaciones post-LLM normalizan `modality`, parsean `total_cost_est` de strings como `"S/ 1,500"` a float, y sanitizan `duration_months` con `int(float())`.

## Errores Comunes y Soluciones

| Error | Causa | Solución |
|---|---|---|
| `"None"` como nombre de curso | LLM devolvió `"None"` string literal | Validación en `sync_vector_worker.py` skippea estos registros |
| `cannot extract elements from a scalar` | `json.dumps()` aplicado sobre parámetros de `db.rpc()` | Pasar dicts/listas directamente, sin serializar |
| `column reference "id" is ambiguous` | SQL function con OUT parameter `id` colisiona con columna `id` | Calificar con `tabla.` prefix (fix: migration `20260429_rpc_ambiguous_fix.sql`) |
| `query returned more than one row` (P0003) | `INTO` scalar recibe múltiples filas de `ON CONFLICT DO UPDATE` | Usar `RETURN QUERY` en vez de `RETURNING * INTO` (fix: migration `20260429_fix_p0003_duplicate_rows.sql`) |
| `invalid input syntax for type integer: "3.5"` | LLM devuelve decimal para campo INT | Sanitizar con `int(float(val))`; SQL: `::NUMERIC` → `::INT` |
| Playwright descarga PDFs | El harvester no filtra extensiones de archivo | `NON_HTML_EXTENSIONS` en `_is_valid_crawl_url()` bloquea `.pdf`, `.xlsx`, etc. |
| PATCH en `enriched_programs` retorna success sin modificar datos | RLS bloquea escritura con anon key | Usar `publishable_key` o `secret_key` o ejecutar SQL en Supabase Dashboard |
| `db_client print` en cada import | `db_client.py` imprime "DB_CLIENT: Loading env..." al importarse | Comportamiento esperado, no es error |

## Estructura de Scripts

```
scripts/
├── core/           # Pipeline principal (harvester, cleansing, enrichment, sync)
├── harvesters/     # Scrapers específicos por institución (bypass, escriben directo a courses)
├── maintenance/    # Auditoría, integridad, sitemap, batch fixes
├── shared/         # Utilidades (db_client.py, utils.py, prompt_loader.py)
├── deprecated/     # Código legacy no usado
└── legacy/         # Historial de desarrollo
```

## Despliegue

- **Frontend**: Cloudflare Pages con GitHub Actions. Static export (`next build` → `out/`). Rama `main` → `studiamatch.com`, `desarrollo` → `studiamatch.pages.dev`.
- **Backend**: Supabase (PostgreSQL 15 + pgvector + PostgREST).
- **CI/CD**: 3 pipelines en `.github/workflows/`: `production_pipeline.yml` (FG2 semanal), `fg1_inventory.yml` (mensual), `fg3_integrity.yml` (diario).
- **Environment Secrets en GitHub**: `Development`, `Certification`, `Production` — cada uno con sus propias `SUPABASE_URL`, `NEXT_SUPABASE_SECRET_KEY` y `NEXT_SUPABASE_PUBLISHABLE_KEY`.
