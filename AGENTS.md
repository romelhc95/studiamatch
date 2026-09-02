# StudIAMatch — Developer Guide

## Regla De Ejecucion

La autoridad viva del proyecto esta en [`.context/estado_del_proyecto.md`](.context/estado_del_proyecto.md), con estas reglas de ejecucion como contrato operativo. La documentacion Obsidian versionada bajo [`.context/`](.context/) conserva alcance, decisiones, planes y trazabilidad; ningun documento raiz temporal crea autoridad independiente. Los Work Packages, digests documentales, grants persistentes, Context Graph y promotion gates historicos no autorizan ejecucion.

Flujo normal:

```text
feat/* o docs/* desde desarrollo
-> PR protegido a desarrollo
-> PR protegido desarrollo a certificacion
-> PR protegido certificacion a main
```

Reglas obligatorias:

1. Toda edicion local debe respetar el alcance vigente y pasar validaciones en Docker cuando aplique.
2. Push, PR, merge, deploys, schedules y cambios de ramas protegidas requieren instruccion humana separada.
3. Cambios DB, migraciones SQL, DDL/DML, writes Supabase, writers productivos, secretos, backup/restore y acciones destructivas requieren aprobacion JIT separada.
4. Si aparece drift de scope, baseline, ambiente, secreto o ruta protegida, detente y consulta.
5. El pedido nuevo de Sprint 1 queda gobernado por `.context/estado_del_proyecto.md` y el plan vinculante Obsidian; `REDEFINICION.md` fue retirado definitivamente y no debe recrearse.
6. Todo desarrollo futuro del producto debe preservar continuamente funcionalidad, escalabilidad, seguridad, mantenimiento, calidad y rendimiento; ningun hito, task o requerimiento puede cerrarse sin validar esas premisas frente al alcance ejecutado.
7. Para cualquier nuevo desarrollo con requerimiento cliente, antes de iniciar y al cerrar un hito o task vinculado a un requerimiento, la evidencia canonica debe validar los criterios de aceptacion contra el documento privado del cliente mediante su atestacion sanitizada versionada. El documento privado no se versiona ni se expone en PRs. Si el gate documental contra fuente cliente falla, no se puede ejecutar codigo, DB, UI, pipeline ni PR del hito siguiente hasta corregir la atestacion sanitizada.
8. Todo cambio funcional, DB, UI, pipeline o despliegue debe planificar una transicion transparente: durante construccion y promocion debe existir una fase de compatibilidad que preserve el comportamiento legacy necesario para que la aplicacion siga funcionando; al llegar y estabilizarse en produccion debe existir una fase de contraccion que retire la funcionalidad legacy y deje activo el nuevo contrato solicitado. Ningun cambio puede cerrarse ni promoverse si no documenta `expand -> compatibilidad -> deploy -> contract`, rollback y evidencia de que funcionalidad no se degrada.
9. Todo prompt futuro de desarrollo queda bajo `PROMPT_RETROALIMENTADO_REQUIRED`: debe operar por ciclos de analizar, implementar, validar, revisar, convertir hallazgos en tareas, corregir y revalidar hasta cumplir sus criterios de GO. Si requiere JIT, push, PR, merge, deploy, workflow_dispatch, Supabase writes, ramas protegidas o acciones destructivas, debe detenerse y pedir aprobacion humana separada mediante opciones concretas. Ningun GO se declara por intencion, implementacion parcial o pruebas locales cuando el alcance exige evidencia canonica o remota; el cierre exige ausencia de hallazgos HIGH/CRITICAL y cada waiver requiere causa, evidencia reproducible, owner, riesgo, vencimiento y aprobacion humana.
10. Todo PR debe usar la plantilla versionada `.github/pull_request_template.md`. Antes de abrir o actualizar un PR se deben ejecutar las validaciones necesarias para completar sus tablas con resultados reales; no se permite llenar la plantilla con intenciones, placeholders, omisiones silenciosas ni checks no ejecutados. Si una validacion no aplica o queda pendiente, debe declararse con causa, riesgo residual y owner.
11. Todo agente debe comenzar cualquier trabajo de plan o build listando las tareas concretas que ejecutara y sus gates de validacion. Ningun cambio funcional se ejecuta hasta recibir el prompt humano `continua` asociado al ciclo; `continua` no sustituye JIT, aprobacion de PR, merge, deploy, workflow_dispatch ni writes Supabase.
12. El cierre de cada ciclo exige checks locales en Docker, pilares y criterios de aceptacion, revision de hallazgos, actualizacion Obsidian, evidencia de `expand -> compatibilidad -> deploy -> contract` y promocion protegida `desarrollo -> certificacion -> main`. Un NO-GO detiene la siguiente etapa hasta remediar y revalidar.

## Auditoría de Credenciales (Obligatorio — ahora automatizado)

**NUNCA** expongas credenciales (API keys, Publishable and secret API keys, management tokens, passwords, secret tokens) en el repositorio, ni público ni privado. La detección ahora es **automática** vía:

- **pre-commit hook** (`.githooks/pre-commit`): Escanea staged files por patrones `eyJhbG` (JWT), `sbp_` (Supabase management token), `sb_secret_` (Supabase secret key), etc. Bloquea el commit si encuentra.
- **pre-push hook** (`.githooks/pre-push`): Escanea el diff de commits nuevos antes de enviarlos al remoto.
- **CI workflow** (`.github/workflows/security-audit.yml`): Corre en cada PR como status check obligatorio.

Reglas adicionales (además de la detección automática):
1. Eliminar credenciales hardcodeadas con `os.environ.get('VAR', '')` y salir con error si falta
2. Verificar que `.env*` esté en `.gitignore` (ya cubierto por `.env*` y `*.env`)
3. Los scripts que necesiten credenciales Pro deben leerlas de variables de entorno:
   - `NEXT_PUBLIC_SUPABASE_URL` — URL del proyecto Supabase Free/Pro
   - `NEXT_SUPABASE_PUBLISHABLE_KEY` — Publishable key para scripts/backend
   - `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` — Publishable key para frontend static export
   - `NEXT_SUPABASE_SECRET_KEY` — Secret key (solo backend/CI)
4. Para CI/CD, las credenciales van en GitHub Secrets por environment — nunca en el código
5. Si descubres credenciales hardcodeadas en el repo, reemplázalas con `os.environ.get()` inmediatamente Y rota la credencial expuesta

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

## Configuración de Ambientes Supabase (Fuente de Verdad)

> **Regla Inmutable**: La siguiente tabla es la fuente de verdad para los refs de proyectos Supabase. Cualquier discrepancia debe reportarse y corregirse inmediatamente.
>
> Para H3REQ1, Pro es además el baseline autoritativo de schema, tipos, constraints, campos y últimas migraciones H2. Free y PostgreSQL 17 local deben converger hacia Pro; no se usa Free/local para modificar Pro ni se sincronizan datos operativos como mecanismo normal.

| Ambiente | Project Ref | URL | Archivo local | GitHub Environment |
|---|---|---|---|---|
| Free (Desarrollo/Certificación) | `aqrldlmlszjtgpqiegaa` | `https://aqrldlmlszjtgpqiegaa.supabase.co` | `.env.local` / `.env.gitdesa` | `Development` / `Certification` |
| Pro (Producción) | `xwhtiqmboljkshrtviyw` | `https://xwhtiqmboljkshrtviyw.supabase.co` | `.env.gitprod` | `Production` |

**Requisito crítico para Pro**: La función RPC `public.exec_sql(sql_text text)` debe existir en el proyecto Pro para que `db_migrate.py` pueda aplicar migrations. Si `db-sync-to-pro.yml` falla con `PGRST202`, primero se debe detener la operación y solicitar aprobación JIT DDL separada. Solo con esa aprobación humana explícita se puede crear o reemplazar la función manualmente en Supabase Dashboard → SQL Editor:
```sql
CREATE OR REPLACE FUNCTION public.exec_sql(sql_text text)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN EXECUTE sql_text; END;
$$;
```

## Variables de Entorno Desarrollo/Certificación

El archivo `.env.local` o `.env.gitdesa` (gitignored) contiene:

| Variable | Uso | Quién la necesita |
|---|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | URL del proyecto Free (`aqrldlmlszjtgpqiegaa`) | Frontend + db_client.py |
| `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` | Publishable key pública para static export | Frontend |
| `NEXT_SUPABASE_PUBLISHABLE_KEY` | Publishable key (lectura pública, rotable) | Scripts + db_client.py |
| `NEXT_SUPABASE_SECRET_KEY` | Secret key (escritura bypass RLS, rotable) | Pipeline CI/CD **solamente** |
| `CF_ACCOUNT_ID` | Cloudflare Workers AI | enrichment_worker.py |
| `CF_API_TOKEN` | Cloudflare API token | enrichment_worker.py |
| `SUPABASE_URL` | Alias para scripts (deriva a `NEXT_PUBLIC_SUPABASE_URL`) | Scripts de migración |

**IMPORTANTE**: El contenedor Docker tiene acceso a `NEXT_SUPABASE_PUBLISHABLE_KEY` + `NEXT_SUPABASE_SECRET_KEY` alojadas en `.env.local`.

## Variables de Entorno Producción

El archivo `.env.gitprod` (gitignored) contiene:

| Variable | Uso | Quién la necesita |
|---|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | URL del proyecto Supabase Pro (`xwhtiqmboljkshrtviyw`) | Frontend + db_client.py |
| `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` | Publishable key pública para static export | Frontend |
| `NEXT_SUPABASE_PUBLISHABLE_KEY` | Publishable key (lectura pública, rotable) | Scripts + db_client.py |
| `NEXT_SUPABASE_SECRET_KEY` | Secret key (escritura bypass RLS, rotable) | Pipeline CI/CD **solamente** |
| `CF_ACCOUNT_ID` | Cloudflare Workers AI | enrichment_worker.py |
| `CF_API_TOKEN` | Cloudflare API token | enrichment_worker.py |
| `SUPABASE_URL` | URL del proyecto producción | Scripts de migración diagnósticos |

**IMPORTANTE**: El contenedor Docker tiene acceso a `NEXT_SUPABASE_PUBLISHABLE_KEY` + `NEXT_SUPABASE_SECRET_KEY` alojadas en `.env.gitprod`.

## Convenciones del Proyecto

### H3REQ1: Baseline y membresías

- Pro (`xwhtiqmboljkshrtviyw`) es la autoridad de schema, tipos, constraints, campos y últimas migraciones H2.
- Free (`aqrldlmlszjtgpqiegaa`) y PostgreSQL 17 local deben converger hacia Pro. No se corrige Pro por diferencias de Free/local ni se sincronizan datos operativos como flujo normal.
- El rol `admin` puede invitar por correo, cambiar el rol y activar/desactivar cualquier membresía `admin`/`user` desde el panel mediante botón o checkbox, pero no puede dejar el sistema sin un admin activo ni auto-bloquear accidentalmente al último admin.
- Las migraciones H3 ya validadas en Docker se reutilizan; deben rebasarse contra el baseline Pro en una base PG17 limpia. Solo se crean deltas idempotentes cuando exista incompatibilidad demostrada; los datos de prueba locales no se promueven.

### Sincronización Cross-Ambiente
- La sincronización operativa Free -> Pro de `staging_raw`, `cleansed_programs`, `enriched_programs` o `courses` NO es parte del flujo normal; solo se permite como backfill/remediación explícita, documentada y aprobada.
- Los scripts excepcionales que sincronizan datos entre ambientes (ej: `sync_pro_to_free.py`) DEBEN usar exclusivamente Publishable y Secret API keys (`sb_publishable_*` / `sb_secret_*`), NUNCA compartir credenciales entre ambientes ni hardcodear keys
- Credenciales Pro se leen de variables de entorno: `SUPABASE_URL`, `NEXT_SUPABASE_SECRET_KEY` y `NEXT_SUPABASE_PUBLISHABLE_KEY` alojadas en `.env.gitprod`
- Credenciales Free se leen de variables de entorno: `NEXT_SUPABASE_PUBLISHABLE_KEY` + `NEXT_SUPABASE_SECRET_KEY` alojadas en `.env.local` vía `db_client.py`
- Los UUIDs de institutions/categories **difieren entre Free y Pro** — sincronización requiere mapeo por slug/nombre
- Ambas keys son rotables ante exposición

### DB-as-Code: Catálogos vs Datos Operativos
- `institutions` es catálogo migrable: altas, slugs, URLs base y metadata institucional deben viajar como SQL versionado en `db/migrations/` junto con `institution_site_profiles`, `categories`, `category_rules` y `market_salaries`.
- `staging_raw`, `cleansed_programs`, `enriched_programs` y `courses` son tablas operativas por ambiente: NO se sincronizan desde Free hacia Pro como parte del flujo DB-as-Code.
- Pro debe generar sus propios registros operativos ejecutando FG2 con sus propias credenciales, perfiles y ventanas de scraping; Free se usa para validar configuración y comportamiento antes de promover migrations.
- Si una institución nueva queda definida en migrations, Pro debe recibir el registro de `institutions` y su perfil sin alta manual duplicada; los cursos aparecerán cuando FG2 corra en Pro.
- Scripts de backfill o sincronización puntual de datos operativos solo se permiten como remediación explícita, documentada y aprobada; no son el mecanismo normal de promoción.

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

### Enforcement Automático del Gate @security-auditor

**PROBLEMA**: La regla "@security-auditor review antes de push" se documentó pero se saltó repetidamente.

**SOLUCIÓN MECÁNICA**: 5 capas de defensa que PREVIENE que credenciales entren al historial, no solo las detecta después.

### Capa 0: Pre-commit hook (`.githooks/pre-commit`)
```
git commit → escanea staged files por credenciales hardcodeadas
  → Si encuentra → ABORTA el commit (el secreto NUNCA entra al historial local)
  → Si limpio → commit exitoso ✅
```

### Capa 1: Pre-push hook (`.githooks/pre-push`)
```
git push → escanea diff de commits nuevos por credenciales
  → Si encuentra → ABORTA el push (el secreto NUNCA sale al remoto)
  → Si limpio → push exitoso ✅
```

### Capa 2: Branch Protection (GitHub — CONFIGURADO ✅)
```
Ramas desarrollo, certificacion, main:
  - Require PR + 1 approval + required check "security-audit"
  - enforce_admins: true (aplica a admins también)
  - dismiss_stale_reviews: true
  - allow_force_pushes: false
  - allow_deletions: false
```

### Capa 3: CI Security Audit (`.github/workflows/security-audit.yml`)
```
PR abierto → corre automáticamente: credential-scan + lint + typecheck + python-check
  → Si falla cualquier check → "security-audit" FAILED → PR bloqueado (no mergeable)
  → Si pasa → "security-audit" PASSED → PR puede mergearse (tras aprobación humana)
```

### Capa 4: Plan de Remediación (si un secreto ya entró al historial)
1. **Rotar la credencial INMEDIATAMENTE** (Supabase Dashboard → API → Rotate)
2. **Limpiar historial** con `git filter-repo`
3. **Force push** con historial limpio (coordinar con el equipo)

### Flujo completo obligatorio

```text
Rama feature/docs local
  -> validaciones locales y @security-auditor
  -> PR protegido a desarrollo con security-audit verde
  -> review humano y merge
  -> PR protegido desarrollo a certificacion
  -> PR protegido certificacion a main
```

La transicion `desarrollo -> certificacion -> main` no es automatica. Solo avanza cuando el usuario lo pida explicitamente. DB Sync, Production Canary, schedules, writers y deploys fuera del despliegue normal de la rama requieren aprobacion separada.

### Instalación de hooks (una vez por clon)
```bash
git config core.hooksPath .githooks
```

Esto hace que Git use `.githooks/` del repo en vez de `.git/hooks/`. Como está versionado, todos los desarrolladores lo tienen.

### CI Status Check: `security-audit`
- Nombre exacto del check: **security-audit**
- Debe configurarse como required check en GitHub Branch Protection
- Si este check falla → el PR NO se puede mergear

## Git Flow
- `desarrollo` — rama activa de desarrollo (PR requerido, review técnico, security-audit CI check obligatorio)
- `certificacion` — QA, E2E Playwright, auditoría de datos
- `main` — producción (Supabase Pro, despliegue automático a Cloudflare)
- Features: ramas `feat/*` que emergen de `desarrollo`

### Regla SDLC
> Todo cambio de código DEBE pasar por: **Desarrollo → @security-auditor → Certificación → Producción**.
> Todo cambio SQL/Datos DEBE pasar por: **Free → @security-auditor → Certificación → Pro (tras aprobación @SDLC-Chief)**.

### @security-auditor
- El AI invoca @security-auditor despues de cada cambio de codigo.
- El pre-commit hook bloquea commits con credenciales hardcodeadas.
- El pre-push hook bloquea pushes con credenciales en commits nuevos.
- El CI check `security-audit` bloquea PRs que no pasen los escaneos y validaciones tecnicas.

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
- **RLS**: La publishable key NO puede escribir en tablas intermedias (`enriched_programs`, `cleansed_programs`, `staging_raw`). Solo SELECT está permitido. Para escritura se necesita la secret key.
- **Exclusiones**: Se gestionan exclusivamente vía `institution_site_profiles.exclusion_patterns` (JSONB). La tabla legacy `crawler_exclusions` fue eliminada (DROP TABLE en ambos ambientes, Free y Pro).

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

1. **CORS en Supabase Free tier**: Por defecto, Supabase Free permite todos los orígenes (`Access-Control-Allow-Origin: *`). No es posible restringir CORS en Free tier. Esto es un **riesgo aceptado** — la API solo expone datos públicos (RLS filtra `is_active=true AND is_verified=true`). En Pro tier se debe restringir a `https://studiamatch.com` y `https://*.studiamatch.pages.dev`.

2. **7 escritores a `courses`** (histórico, ahora solo 2): Los harvesters dedicados (IDAT, UPC, PUCP, USIL, UTP, U. Lima) escriben directo a `courses` con `is_verified=True`. Solo `sync_vector_worker.py` (Golden Path) e `integrity_ping.py` (PATCH mantenimiento) son los escritores autorizados restantes post-Fase 52.

2. **La publishable key NO puede escribir en tablas ETL**: Cualquier script que necesite modificar `staging_raw`, `cleansed_programs`, `enriched_programs` **debe** usar la secret key. Si necesitas ejecutar algo local que modifique esas tablas, hazlo vía SQL en Supabase Dashboard.

3. **`batch_enrich_courses.py`** (scripts/maintenance/): Bypass del pipeline. Lee HTML de `staging_raw` y escribe directo a `courses`. Útil para corregir datos puntuales sin pasar por las 4 estaciones.

4. **Migraciones SQL**: Se ejecutan manualmente en Supabase Dashboard > SQL Editor. Los archivos en `db/migrations/` son la fuente de verdad. El contenedor no puede ejecutarlas (publishable key sin permisos DDL).

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
| PATCH en `enriched_programs` retorna success sin modificar datos | RLS bloquea escritura con publishable key | Usar secret key o ejecutar SQL en Supabase Dashboard |
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
- **Environment Secrets en GitHub**: `Development`, `Certification`, `Production` — cada uno con sus propias `SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`, `NEXT_SUPABASE_SECRET_KEY` y `NEXT_SUPABASE_PUBLISHABLE_KEY`.

### Contrato de autenticación HTTP
- Las API keys Supabase modernas deben comenzar con `sb_publishable_` o `sb_secret_`; una key ausente o con otro formato detiene la operación.
- Las API keys Supabase se envían exclusivamente en `apikey`; nunca se reutilizan como `Authorization: Bearer`.
- `Authorization: Bearer` queda reservado a los tokens existentes de Supabase Management API, Cloudflare y Resend, inventariados por path, identidad, proveedor y variable de origen en `tests/test_supabase_credentials_contract.py`; la Supabase Data API no usa Bearer en esta rama.
- Los scripts excepcionales que operen Free y Pro en una misma ejecución deben exigir pares explícitos `FREE_SUPABASE_URL` + `FREE_NEXT_SUPABASE_SECRET_KEY` y `PRO_SUPABASE_URL` + `PRO_NEXT_SUPABASE_SECRET_KEY`, y rechazar URLs o keys reutilizadas.
