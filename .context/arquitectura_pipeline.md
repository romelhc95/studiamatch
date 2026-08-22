# Arquitectura Pipeline

> Fuente canonica de arquitectura aplicativa, pipeline, runtime e infraestructura. No crea alcance ni autoriza ejecucion; los gates viven en [Estado Del Proyecto](estado_del_proyecto.md) y en los work packages vigentes.

Snapshot de investigacion: `desarrollo@96c6e7e97a1a6c703eb3b5a3a22f6f6d21aa28e9`.
Reconciliacion post-PR425: arquitectura publicada en `desarrollo@4cce43a743de5860c4da86eecf1782efab91d26b`, tree `ac16b545b74a03b149aac538062def20101187fb`.
Reconciliacion post-PR426: GOV-HOM publicado en `desarrollo@fddb9cea6ac44a1f7f7b31e93a7b2f2cc0eeacd1`, tree `5e7d087ac45457264ea29dfc1aa7373efd909290`; GOV-CI prepara la separacion entre `security-audit` y branch protection review.

## Principios Vigentes

- StudIAMatch publica un frontend Next.js con `output: 'export'` en Cloudflare Pages.
- El frontend no usa `@supabase/supabase-js`; usa PostgREST con `fetch` y publishable key en `apikey`.
- El pipeline de datos corre en GitHub Actions con tres flujos principales: FG1 inventario, FG2 ETL, FG3 integridad.
- Supabase/PostgreSQL es el plano de datos y expone PostgREST/RPC/RLS.
- Las escrituras privilegiadas usan `NEXT_SUPABASE_SECRET_KEY` solo en CI/backend autorizado.
- Los datos operativos no se promueven Free -> Pro como flujo normal; cada ambiente produce sus propias filas operativas.

## Diagrama De Contexto

```mermaid
flowchart LR
    User[Usuarios y leads] --> CF[Cloudflare Pages\nstatic export]
    CF --> Browser[Browser runtime\nReact client components]
    Browser -->|PostgREST apikey publishable| SBA[Supabase Data API]
    Browser -->|RPC publicos permitidos| SBA
    SBA --> PG[(Supabase PostgreSQL\nRLS + RPC)]
    Sources[Fuentes institucionales\nSUNEDU/MINEDU + sitios web] --> GHA[GitHub Actions]
    GHA -->|FG1/FG2/FG3 con secret key| SBA
    GHA --> AI[AI providers\nCloudflare + OpenCode/DeepSeek + fallback]
    GHA --> GHArtifacts[Logs y artifacts CI]
    Maintainer[Mantenedor] --> GH[GitHub PRs + branch protection]
    GH --> GHA
```

## Contenedores

```mermaid
flowchart TB
    subgraph Frontend[web/]
        Next[Next.js App Router\nstatic export]
        Home[HomeContent\nbusqueda + leads]
        Detail[CourseDetailClient\nleads + ratings + reviews + view_count]
        Compare[CompareContent\ncomparacion + view_count]
    end

    subgraph CI[GitHub Actions]
        FG1[fg1_inventory.yml\ndiscovery_institutions.py]
        FG2[production_pipeline.yml\nmaster -> cleansing -> enrichment -> sync]
        FG3[fg3_integrity.yml\nintegrity_ping.py]
        DBSync[db-sync-to-pro.yml\nreport/apply/verify]
        Gates[security-audit.yml\nContext Graph + boundary + build]
    end

    subgraph Data[Supabase]
        Catalog[(catalogos/config)]
        Operational[(tablas operativas)]
        Product[(courses + public tables)]
        RPC[RPC/SECURITY DEFINER]
        RLS[RLS/grants]
    end

    Next --> Home
    Next --> Detail
    Next --> Compare
    Home --> Product
    Detail --> Product
    Compare --> Product
    FG1 --> Catalog
    FG2 --> Operational
    FG2 --> Product
    FG3 --> Product
    DBSync --> Catalog
    Gates --> CI
    RPC --> Operational
    RLS --> Product
```

## Runtime Frontend

- Configuracion: `web/next.config.js` usa static export, trailing slash e imagenes sin optimizacion.
- Stack: `web/package.json` declara Next 16, React 19, TypeScript, Tailwind y scripts `dev`, `build`, `lint`.
- Build: `npm run build` limpia `.next` y `out`, luego genera el artefacto estatico.
- Rutas principales: `/`, `/courses`, `/courses/[institution]/[slug]`, `/compare`, `/privacidad`, `/terminos`.
- Variables publicas: `NEXT_PUBLIC_SUPABASE_URL` y `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`.
- Header de API: `apikey` con publishable key; no se usa `Authorization: Bearer` para Data API.
- Lecturas publicas: `courses`, `institutions`, `categories`, `ratings`, `reviews` y queries relacionadas.
- Escrituras publicas previstas: `leads`, `ratings`, `reviews`, y RPC `increment_view_count` cuando RLS/grants lo permitan.
- Ruta dinamica de curso: `generateStaticParams()` intenta prerender desde Supabase y usa fallback seguro si faltan variables o datos.

## Pipeline FG1-FG3

```mermaid
flowchart LR
    FG1[FG1 Inventario\ndiscovery_institutions.py] --> Institutions[(institutions)]
    Institutions --> Profiles[(institution_site_profiles)]
    Institutions --> FG2H[FG2 Harvest\nmaster_orchestrator.py + universal_harvester.py]
    Profiles --> FG2H
    FG2H --> Staging[(staging_raw)]
    Staging --> Clean[FG2 Cleansing\ncleansing_worker.py]
    Clean --> Cleansed[(cleansed_programs)]
    Cleansed --> Enrich[FG2 Enrichment\nenrichment_worker.py]
    Enrich --> Enriched[(enriched_programs)]
    Enriched --> Sync[FG2 Sync\nsync_vector_worker.py]
    Sync --> Courses[(courses)]
    Courses --> FG3[FG3 Integrity\nintegrity_ping.py]
    FG3 --> Courses
```

## Writers Autorizados

| Estacion | Script | Lee | Escribe | Guardas |
|---|---|---|---|---|
| FG1 | `scripts/core/discovery_institutions.py` | `config/institution_sources.json`, `institutions` | `institutions` | `--source-slug`, `--no-insert`, canary redaction |
| FG2 harvest | `scripts/core/master_orchestrator.py`, `universal_harvester.py` | `institutions`, `institution_site_profiles`, `staging_raw` | `staging_raw`, telemetry en `institutions`, perfil si falta | `pipeline_enabled`/`pipeline_ready`, `discovery_enabled`, circuit breaker, exclusiones |
| FG2 cleansing | `scripts/core/cleansing_worker.py` | `staging_raw`, `institution_site_profiles`, `institutions` | `cleansed_programs`, status en `staging_raw` | locks RPC, noise patterns, exclusiones regex |
| FG2 enrichment | `scripts/core/enrichment_worker.py` | `cleansed_programs`, `institution_site_profiles` | `enriched_programs`, status en `cleansed_programs` | `pipeline_enabled`/`pipeline_ready`, provider fallback |
| FG2 sync | `scripts/core/sync_vector_worker.py` | `enriched_programs`, `courses`, `institution_site_profiles` | `courses`, status en `enriched_programs` | noise validation, `production_enabled`, no mock overwrite publico |
| FG3 | `scripts/core/integrity_ping.py` | `courses`, `institutions` | `courses` | HTTPS/public IP validation, grace 404 |

## Workflows Y Ambientes

| Workflow | Trigger | Ambiente | Efecto |
|---|---|---|---|
| `security-audit.yml` | PR/push a `desarrollo`, `certificacion`, `main` | N/A | credential scan, links, Context Graph, manifests, boundary, lint, typecheck, build |
| `fg1_inventory.yml` | schedule mensual `0 0 1 * *`, manual | `Development`, `Certification`, `Production`, `Production-Scheduled-FG1` | inventario institucional; ejecucion requiere gate vigente |
| `production_pipeline.yml` | schedule diario `0 5 * * *`, manual | `Development`, `Certification`, `Production`, `Production-Scheduled-FG2` | FG2 ETL completo hasta sync y boundary audit; ejecucion requiere gate vigente |
| `fg3_integrity.yml` | schedule diario `0 11 * * *`, manual | `Development`, `Certification`, `Production`, `Production-Scheduled-FG3` | integridad y desactivacion por 404; ejecucion requiere gate vigente |
| `db-sync-to-pro.yml` | push a `main`, manual | `Production` | report/apply/verify de DB-as-code bajo gates R3/JIT |
| `production_canary.yml` | manual en `main` | `Production` | canary acotado con writers pausados |
| `f9_9_certification_canary.yml` | manual en `certificacion` | `Certification` | canary de certificacion acotado |
| `f9-7-contract.yml` | PR con paths sensibles | N/A | contrato PostgreSQL 17 y secretos |
| `opencode.yml` | comentarios `/oc` | GitHub | integra OpenCode |

`security-audit.yml` incluye un Governance Preflight R2 aplicable solo a `pull_request` cuyo destino sea `desarrollo`. Ese job valida `Base-SHA`, `Candidate-SHA`, `WP-Digest`, manifest, el `head.sha` real del PR, ancestry, paths y co-change; no consulta reviews ni se dispara por `pull_request_review`. Para `certificacion`, `main` y `push`, el preflight debe quedar skipped y cualquier promocion superior requiere R3/JIT separado. GitHub branch protection es la unica autoridad mecanica de review humana, por lo que no se necesita rerun manual cuando llega la review.

El despliegue automatico de Cloudflare Pages asociado a ramas/PR de `desarrollo` se clasifica como `AUTOMATIC_NON_PRODUCTION_PREVIEW_SIDE_EFFECT` cuando no modifica dominio productivo, environment Production, secrets, triggers manuales ni writers. No sustituye canary, no autoriza produccion y no es evidencia de aceptacion productiva. Si apunta a Production, dispara/reintenta manualmente, cambia configuracion/secrets o ejecuta writers/egress, la promocion debe detenerse y requerir R3 JIT explicito.

## Controles De Produccion

- `.github/scripts/production_control_preflight.sh` centraliza writers permitidos.
- En `main`, schedules productivos existen en YAML pero solo pueden ejecutarse cuando el gate aplicable habilita `AUTOMATION_ENABLED=true` y `PRODUCTION_WRITERS_PAUSED=false`.
- `DB-SYNC` requiere dispatch manual y writers pausados.
- `PRODUCTION-CANARY` requiere dispatch manual, `AUTOMATION_ENABLED=false` y writers pausados.
- Schedules fuera de `main` se bloquean; la disponibilidad tecnica de dispatch manual en `desarrollo`/`certificacion` no autoriza ejecucion sin gate vigente.

## Desarrollo Local

- Desarrollo se ejecuta dentro del contenedor `studiamatch-dev` definido en `docker-compose.yml`.
- El contenedor usa `node:20-bookworm`, Python 3, Playwright y dependencias del sistema.
- El repositorio se monta en `/app` y el frontend expone `3000:3000`.
- Las pruebas de gobierno H2 usan `docker-compose.h2-test.yml` con red deshabilitada y variables cloud vacias.

## Secretos Por Nombre

- Supabase URL: `SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_URL`.
- Publishable keys: `NEXT_SUPABASE_PUBLISHABLE_KEY`, `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`.
- Secret key CI/backend: `NEXT_SUPABASE_SECRET_KEY`.
- AI: `CF_API_TOKEN`, `CF_ACCOUNT_ID`, `OPENCODE_API_KEY`.
- Canary variables: prefijos `F9_9_` y `F10_` documentados en workflows.

## Documentos Legacy

Los documentos bajo `docs/architecture/` y `docs/orquestador-sdlc/` son evidencia historica o explicaciones parciales salvo que enlacen explicitamente a esta nota. Las contradicciones conocidas se registran como `SUPERSEDED_HISTORY` en sus encabezados.

## Mecanismo De Actualizacion

- Cualquier cambio en frontend, pipeline, workflows, Supabase o ambientes debe actualizar esta nota si altera runtime, writer, flujo de datos, gates o secretos por nombre.
- Los cambios de schema/RLS/RPC deben sincronizarse con [Sistema DB Supabase](sistema_db_supabase.md) y [Matriz Adopcion DB](operaciones/matriz_adopcion_db.md).
- La validacion semantica debe fallar si esta nota o sus pares canonicos desaparecen.
