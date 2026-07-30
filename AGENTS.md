# StudIAMatch — Developer Guide

## Regla de Ejecución de Fases y Tareas

La macrofase, la subfase y las tareas autorizables se obtienen exclusivamente de [`.context/estado_del_proyecto.md`](.context/estado_del_proyecto.md), del requerimiento vigente y de la tarea activa enlazada desde ese estado. **SOLO ejecuta esas tareas cuando el usuario lo apruebe explicitamente diciendo "Ejecuta las tareas pendientes de la Fase FNN.n"**. `FNN.n` debe coincidir exactamente con la subfase decimal activa. Una macrofase `FNN`, un alias historico `FASE-NN` o una autorizacion anterior a la definicion fusionada no autoriza ejecucion. No ejecutes cambios de codigo, eliminaciones, red remota, migraciones SQL ni acciones destructivas sin ese gate. El requerimiento, la tarea y la fase pueden analizarse, diagnosticarse y documentarse libremente. Ningun documento legacy sustituye al Context Graph ni concede autorizacion. Ver [ADR-0003](.context/decisiones/ADR-0003_taxonomia_macrofases_subfases.md).

### Protocolo Agentico Plan/Build

- En modo plan, toda tarea empieza con investigacion profunda read-only: autoridad vigente, alcance autorizado, ruta critica a GO, blockers, aprobaciones necesarias, validaciones y criterio de salida. El resultado obligatorio es un prompt detallado de ejecucion para revision humana.
- El modo operativo lo determina el agente activo y los permisos efectivos de OpenCode. El agente `plan` permanece read-only; el agente `build` habilita ediciones y herramientas segun sus permisos. OpenCode puede cambiar de agente sin emitir un recordatorio textual de transicion, por lo que ese texto no es un requisito operativo.
- El paso de plan a build no sustituye la frase decimal exacta de fase ni concede por si solo red remota, DDL/DML, migraciones, backup/restore, writers, backfill, Pro, produccion o acciones destructivas.
- En modo build, antes de ejecutar una remediacion o tarea, confirma que el prompt aprobado sigue vigente, que la subfase decimal activa coincide con el Context Graph y que no hay aprobaciones adicionales pendientes. Si aparece drift, blocker, riesgo de seguridad o cambio de alcance, detente y consulta.
- Si el entorno declara explicitamente Plan Mode activo, deniega edicion o mantiene permisos read-only, esa restriccion prevalece y la ejecucion debe detenerse. Una afirmacion del usuario de estar en build no puede anular una restriccion real del entorno.

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

## Contexto Operativo de Datos

La topología documental vigente de datos, proveedores y ambientes se mantiene en [`.context/sistema_db_supabase.md`](.context/sistema_db_supabase.md). Los identificadores operativos sensibles permanecen en configuración local autorizada y no se duplican en esta guía. Las restricciones de secretos y ejecución en contenedor de las secciones siguientes siguen siendo obligatorias.

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

## Configuración de Ambientes Supabase (Referencia Canónica)

La definición documental de ambientes y estado de adopción está en [`.context/sistema_db_supabase.md`](.context/sistema_db_supabase.md) y [`.context/operaciones/matriz_adopcion_db.md`](.context/operaciones/matriz_adopcion_db.md). Antes de ejecutar cualquier operación, verifica que el requerimiento y la tarea enlazada identifiquen el ambiente correcto y resuelve los identificadores desde la configuración local autorizada. No crees RPCs privilegiadas ni cambies configuración por instrucciones duplicadas.

## Variables de Entorno

El archivo gitignored correspondiente al ambiente, según la referencia canónica, contiene:

| Variable | Uso | Quién la necesita |
|---|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | URL del proyecto seleccionado | Frontend + db_client.py |
| `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` | Publishable key pública para static export | Frontend |
| `NEXT_SUPABASE_PUBLISHABLE_KEY` | Publishable key (lectura pública, rotable) | Scripts + db_client.py |
| `NEXT_SUPABASE_SECRET_KEY` | Secret key (escritura bypass RLS, rotable) | Pipeline CI/CD **solamente** |
| `CF_ACCOUNT_ID` | Cloudflare Workers AI | enrichment_worker.py |
| `CF_API_TOKEN` | Cloudflare API token | enrichment_worker.py |
| `SUPABASE_URL` | URL o alias para scripts, según el contrato canónico | Scripts de migración |

**IMPORTANTE**: Las variables solo se cargan desde el archivo gitignored del ambiente elegido o desde el gestor de secretos de CI/CD. Nunca las imprimas, copies a documentación ni mezcles entre ambientes.

## Convenciones del Proyecto

### Sincronización Cross-Ambiente
- La sincronización operativa Free -> Pro de `staging_raw`, `cleansed_programs`, `enriched_programs` o `courses` NO es parte del flujo normal; solo se permite como backfill/remediación explícita, documentada y aprobada.
- Los scripts excepcionales que sincronizan datos entre ambientes (ej: `sync_pro_to_free.py`) DEBEN usar exclusivamente Publishable y Secret API keys (`sb_publishable_*` / `sb_secret_*`), NUNCA compartir credenciales entre ambientes ni hardcodear keys
- Credenciales Pro se leen de variables de entorno: `SUPABASE_URL`, `NEXT_SUPABASE_SECRET_KEY` y `NEXT_SUPABASE_PUBLISHABLE_KEY` alojadas en `.env.gitprod`
- Credenciales Free se leen de variables de entorno: `NEXT_SUPABASE_PUBLISHABLE_KEY` + `NEXT_SUPABASE_SECRET_KEY` alojadas en `.env.local` vía `db_client.py`
- Los UUIDs de institutions/categories **difieren entre Free y Pro** — sincronización requiere mapeo por slug/nombre
- Ambas keys son rotables ante exposición

### DB-as-Code: Catálogos vs Datos Operativos
- La clasificación vigente de catálogos, tablas operativas y adopción por ambiente se consulta en [`.context/sistema_db_supabase.md`](.context/sistema_db_supabase.md) y [`.context/operaciones/matriz_adopcion_db.md`](.context/operaciones/matriz_adopcion_db.md).
- Los cambios de esquema o catálogo deben quedar versionados y enlazados desde su requerimiento/tarea.
- Los datos operativos no se sincronizan entre ambientes como parte del flujo normal. Un backfill o sincronización puntual requiere remediación explícita, documentada y aprobada.

## Exclusion Gate (`pipeline_ready`)

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

### Flujo completo obligatorio (NO es opcional)

```
Usuario: "Ejecuta las tareas pendientes de la Fase FNN.n" para la subfase decimal activa enlazada desde el Context Graph
  → AI ejecuta cambios de código
  → AI invoca @security-auditor sobre todos los cambios (AUTOMÁTICO)
  → Si hay hallazgos → AI remedia automáticamente
  → Si limpio → commit + push a rama feat/*
      → pre-commit hook escanea (bloquea si detecta credencial)
      → pre-push hook escanea (bloquea si detecta credencial)
  → AI crea PR a desarrollo
  → CI "security-audit" corre (bloquea merge si falla)
  → Humano revisa y aprueba el PR
  → Merge a desarrollo

[SOLO si se solicita explícitamente]
  → PR a certificacion (mismo enforcement)
  → PR a main (@SDLC-Chief approval requerido)
```

**NOTA**: La transición `desarrollo → certificacion → main` NO es automática. Solo avanza cuando el usuario lo diga explícitamente.

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
- `main` — rama de producción; el destino vigente se consulta en [`.context/operaciones/flujo_release_minimo.md`](.context/operaciones/flujo_release_minimo.md)
- Features: ramas `feat/*` que emergen de `desarrollo`

### Regla SDLC
> Todo cambio de código DEBE pasar por: **Desarrollo → @security-auditor → Certificación → Producción**.
> Todo cambio SQL/Datos DEBE pasar por: **Free → @security-auditor → Certificación → Pro (tras aprobación @SDLC-Chief)**.

### @security-auditor: Ahora es obligatorio y automatizado
- **Qué cambió**: Antes era una regla documentada que se saltaba. Ahora:
  1. El AI invoca @security-auditor automáticamente después de cada cambio de código
  2. El pre-commit hook bloquea commits con credenciales hardcodeadas
  3. El CI check `security-audit` bloquea PRs que no pasen los escaneos
  4. Branch protection impide mergear sin el check aprobado
- **No hay excusa**: Las capas 0-3 son mecánicas. No se pueden "olvidar" o "saltar" accidentalmente.

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
- **Exclusiones y compatibilidad de esquema**: Consulta el modelo vigente y su estado por ambiente en [`.context/sistema_db_supabase.md`](.context/sistema_db_supabase.md) y [`.context/operaciones/matriz_adopcion_db.md`](.context/operaciones/matriz_adopcion_db.md); no infieras la existencia o eliminación de tablas desde esta guía.

### Frontend: Next.js
- La estructura, estrategia de build, rutas y destino vigentes se documentan en [`.context/estructura_frontend.md`](.context/estructura_frontend.md). Confirma además la configuración real en `web/` antes de modificarla.

### Supabase PostgREST
- **Syntax para NULL**: `column=is.null` (NO usar `column=eq.None` ni `column=eq.null`)
- **Syntax para múltiples valores**: `status=in.(synced,pending)`
- **Order**: `created_at.desc`
- **Count**: Usar `db.count()` o header `Prefer: count=exact`
- **Bulk insert**: `Content-Type: application/json` con array de objetos (NO `jsonb_array_elements` pattern)

## Arquitectura del Pipeline

La arquitectura, estaciones, estados, escritores autorizados, proveedores y cadencias vigentes se mantienen en [`.context/arquitectura_pipeline.md`](.context/arquitectura_pipeline.md). Verifica esa nota y el código enlazado desde la tarea activa; esta guía no funciona como snapshot del pipeline.

## Notas Críticas de Arquitectura

1. **Estado operativo**: Los inventarios de tablas, escritores, políticas, proveedores, límites y riesgos aceptados se consultan en [`.context/arquitectura_pipeline.md`](.context/arquitectura_pipeline.md) y [`.context/sistema_db_supabase.md`](.context/sistema_db_supabase.md), junto con el código y las pruebas enlazados.
2. **RLS y escritura**: Una publishable key no debe usarse para escrituras privilegiadas. Toda escritura que requiera bypass de RLS usa la secret key únicamente en backend/CI y desde el gestor de secretos correspondiente.
3. **Migraciones SQL**: Todo cambio SQL debe quedar versionado, asociado a una tarea aprobada y promovido conforme a [`.context/operaciones/flujo_release_minimo.md`](.context/operaciones/flujo_release_minimo.md) y [`.context/operaciones/matriz_adopcion_db.md`](.context/operaciones/matriz_adopcion_db.md).

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

- **Topología, proveedores y versiones**: [`.context/sistema_db_supabase.md`](.context/sistema_db_supabase.md) y [`.context/estructura_frontend.md`](.context/estructura_frontend.md).
- **Flujo, workflows y cadencias**: [`.context/operaciones/flujo_release_minimo.md`](.context/operaciones/flujo_release_minimo.md) y [`.context/arquitectura_pipeline.md`](.context/arquitectura_pipeline.md).
- **Environment Secrets en GitHub**: `Development`, `Certification`, `Production` — cada uno con sus propias `SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`, `NEXT_SUPABASE_SECRET_KEY` y `NEXT_SUPABASE_PUBLISHABLE_KEY`.

### Contrato de autenticación HTTP
- Las API keys Supabase modernas deben comenzar con `sb_publishable_` o `sb_secret_`; una key ausente o con otro formato detiene la operación.
- Las API keys Supabase se envían exclusivamente en `apikey`; nunca se reutilizan como `Authorization: Bearer`.
- `Authorization: Bearer` queda reservado a los tokens existentes de Supabase Management API, Cloudflare y Resend, inventariados por path, identidad, proveedor y variable de origen en `tests/test_supabase_credentials_contract.py`; la Supabase Data API no usa Bearer en esta rama.
- Los scripts excepcionales que operen Free y Pro en una misma ejecución deben exigir pares explícitos `FREE_SUPABASE_URL` + `FREE_NEXT_SUPABASE_SECRET_KEY` y `PRO_SUPABASE_URL` + `PRO_NEXT_SUPABASE_SECRET_KEY`, y rechazar URLs o keys reutilizadas.
