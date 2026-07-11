# Estado del Proyecto

> **Actualizado**: 2026-07-05 · **Proyecto**: StudIAMatch · **Stack**: Next.js 16 + Supabase + Python Pipeline · **Hosting**: Cloudflare Pages (frontend) + Supabase Free/Pro (backend)

## Resumen Ejecutivo

StudIAMatch es una plataforma serverless de comparacion de programas educativos en Peru. Descubre, extrae, enriquece y publica datos de cursos desde los sitios web de instituciones educativas peruanas hacia un catalogo consultable con metricas de ROI. Opera con dos ambientes Supabase (Free para desarrollo/certificacion, Pro para produccion) y despliega el frontend como sitio estatico en Cloudflare Pages.

## Arquitectura Serverless

```text
┌─────────────────────────────────────────────────────────┐
│                  GitHub Actions (CI/CD)                  │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │ FG2      │  │ FG3      │  │ FG1      │  │ Sec    │ │
│  │ Pipeline │  │ Integrity│  │ Inventory│  │ Audit  │ │
│  │ (diario) │  │ (diario) │  │ (mensual)│  │ (PR)   │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬───┘ │
│       │              │              │              │     │
└───────┼──────────────┼──────────────┼──────────────┼─────┘
        │              │              │              │
        ▼              ▼              ▼              ▼
┌─────────────────────────────────────────────────────────┐
│                    Supabase Cloud                        │
│                                                         │
│  Free (aqrldlmlszjtgpqiegaa) ◄── Desarrollo/Certif     │
│  Pro  (xwhtiqmboljkshrtviyw)  ◄── Produccion            │
│                                                         │
│  PostgreSQL 15 + pg_trgm + vector + PostgREST          │
│  14 tablas activas, 14 RPCs clave, 5 triggers, RLS completo  │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                 Cloudflare Pages                         │
│                                                         │
│  Static export (next build → out/)                      │
│  studiamatch.com (main) + studiamatch.pages.dev (dev)   │
│  Rebuild disparado por pipeline completion              │
└─────────────────────────────────────────────────────────┘
```

## Componentes del Sistema

### 1. Pipeline de Datos (Python 3.11)

| Componente | Estado | Frecuencia | Notas |
|---|---|---|---|
| `universal_harvester.py` | **Activo** | Diario | Multi-site type, multi-discovery mode, Playwright + HTTP |
| `cleansing_worker.py` | **Activo** | Diario | HTML cleaning, sibling consolidation, noise filtering |
| `enrichment_worker.py` | **Activo** | Diario | Triple-cloud LLM fallback (DeepSeek → CF → mock), 14 pilares |
| `sync_vector_worker.py` | **Activo** | Diario | Golden Path writer, ROI compute, slug generation |
| `integrity_ping.py` | **Desactivado** (cron presente) | Diario | HEAD checks, 404 detection, expiration |
| `discovery_institutions.py` | **Desactivado** (cron presente) | Mensual | Institution seeding |
| `master_orchestrator.py` | **Activo** | Diario | Institution iteration, freshness guard |

### 2. Base de Datos (Supabase)

| Proyecto | Ref | Uso | RLS |
|---|---|---|---|
| Free | `aqrldlmlszjtgpqiegaa` | Desarrollo + Certificacion | Hardening completo (Fase 80+) |
| Pro | `xwhtiqmboljkshrtviyw` | Produccion | Sincronizado via `db_migrate.py` |

**Tablas activas**: 14 (5 catálogo, 4 ETL, 4 social/leads, 1 auditoría)
**Extensiones**: `pg_trgm`, `vector`, `pg_net`
**Politicas RLS**: Anon SELECT en catalogo publico, service_role ALL en ETL, RPCs revocadas a PUBLIC

### 3. Frontend (Next.js 16 + React 19)

| Aspecto | Estado |
|---|---|
| Build | Static export (`output: 'export'`) |
| Rutas | 6 (home, courses/:inst/:slug, compare, privacidad, terminos, /courses fallback) |
| Server Components | layout, home shell, detail shell (metadata/LdJson), static pages |
| Client Components | HomeContent, CourseDetailClient, CompareContent, Header, AnimatedCounter, button |
| Supabase client | Fetch directo (sin `@supabase/supabase-js`) |
| SEO | `generateMetadata` + `generateStaticParams` + JSON-LD `Course` schema |
| Despliegue | Cloudflare Pages via API trigger post-pipeline |

## Sistemas de Monitoreo Activos

### FG2-4: QA Audit (integrado en pipeline)
- `quality_assurance_audit.py` — 14 pilares faltantes, resumenes excesivamente largos
- `taxonomy_roi_audit.py` — Consistencia categoria/salario/ROI
- `category_coverage_audit.py` — Cobertura de keywords y categorias confirmadas
- Reports subidos como artifacts de GitHub Actions
- Dispara rebuild de Cloudflare Pages en `main`

### FG3: Integrity Ping (desactivado)
- HEAD-check de URLs activas con periodo de gracia de 3 dias para 404
- Desactivacion de cursos con `start_date` expirada (>90 dias)
- Alertas de salud del catalogo (cursos sin syllabus/objectives)

### Seguridad (obligatorio)
- **Pre-commit hook**: Escanea staged files por credenciales hardcodeadas
- **Pre-push hook**: Escanea diff de commits nuevos
- **CI check `security-audit`**: Credential scan + Python syntax check (bloqueantes) + ESLint + TypeScript (informativos)
- **Branch protection**: PR requerido + 1 approval + `security-audit` passing en `desarrollo`, `certificacion`, `main`

### Contenedor Docker
- `studiamatch-dev` (Debian, node:20-bookworm)
- Python 3 + dependencias de Playwright
- `.env.local` montado como variables de entorno
- Todo el desarrollo ocurre dentro del contenedor

## Limitaciones Tecnicas Detectadas

### Criticas
1. **Embeddings vectoriales no implementados**: `vector` extension instalada pero `enriched_programs.embedding` es `TEXT`, no `vector(N)`. `sync_vector_worker.py` tiene stub. Sin busqueda semantica operativa.
2. **FG3 Integrity desactivado**: Sin monitoreo automatico de 404s ni expiracion de cursos en produccion.
3. **`generateStaticParams` sin paginacion**: Fetch sin `limit` — PostgREST default 1000. Catalogos >1000 cursos tendran paginas de detalle no pre-renderizadas. Con `dynamicParams=false`, esas rutas devolveran 404.
4. **`parseDurationToMonths` defectuoso**: `"12 meses"` retorna 0 porque `toLowerCase()` produce `"12 meses"` y `startsWith('mes')` falla. Afecta computo de ROI.

### Moderadas
5. **Schema drift entre migraciones**: `restore_full_schema.sql` no incluye todas las columnas agregadas por migraciones posteriores (gates, provider tracking, view counters, `email_log`, etc.).
6. **`enriched_programs.start_date` tipo inconsistente**: `TEXT` en canonical schema vs `DATE` en migracion Fase 73.
7. **`generateMetadata` busca solo por slug**: Duplicados de slug entre instituciones producen metadata incorrecta.
8. **`typescript.ignoreBuildErrors: true`**: Regresiones de tipo pueden desplegarse a produccion.
9. **Sin `@supabase/supabase-js`**: Fetch manual sin tipado automatico, sin realtime, codigo de fetch duplicado en 3+ componentes.

### Menores
10. **FG1/FG3 con cron sintacticamente presente pero comentados como desactivados**: Riesgo de activacion accidental si se modifica el YAML sin quitar el comentario.
11. **`notify_new_lead()` hardcodea URL de Edge Function de Pro**: Logica de entorno especifica en schema SQL.
12. **`ratings`/`reviews` sin FK a `courses`**: Integridad referencial debil.
13. **Escrituras desde browser con anon key**: `leads`, `ratings`, `reviews`, `counter` — requieren rate limiting que depende exclusivamente de RLS.
14. **`batch_enrich_courses.py` es bypass del golden pipeline**: Solo debe usarse como remediacion, pero no tiene enforcement mecanico.

## Flujo de Cambios (SDLC)

```text
feat/* ──PR──▶ desarrollo ──PR──▶ certificacion ──PR──▶ main (produccion)
                 │                      │                    │
                 ▼                      ▼                    ▼
           Development env       Certification env     Production env
           (Supabase Free)       (Supabase Free)      (Supabase Pro)
```

- **Desarrollo → Certificacion → Produccion**: Solo avanza con aprobacion explicita del usuario
- **`@security-auditor`**: Obligatorio y automatizado (pre-commit + pre-push + CI + branch protection)
- **DB-as-Code**: `institutions`, `categories`, `category_rules`, `market_salaries`, `institution_site_profiles` son catalogos migrables. Datos operativos (staging/cleansed/enriched/courses) son por ambiente.

## Deuda Tecnica Identificada

| Item | Impacto | Prioridad sugerida |
|---|---|---|
| Implementar busqueda vectorial | Alto — funcionalidad core ausente | P0 |
| Reactivar FG3 Integrity | Alto — sin monitoreo de salud de catalogo | P0 |
| Paginacion en `generateStaticParams` | Medio — SEO y UX para catalogo grande | P1 |
| Arreglar `parseDurationToMonths` | Medio — datos de ROI incorrectos | P1 |
| Normalizar `generateMetadata` con institution+slug | Medio — SEO duplicado | P1 |
| Migrar a `@supabase/supabase-js` | Medio — mantenibilidad y tipado | P2 |
| Consolidar `restore_full_schema.sql` con migraciones | Bajo — riesgo de drift en nuevos ambientes | P2 |
| Agregar FKs a `ratings.course_id` y `reviews.course_id` | Bajo — integridad referencial | P3 |
| Rate limiting en endpoints de escritura publica | Medio — riesgo de spam | P2 |
| Eliminar o reactivar formalmente cron de FG1/FG3 | Bajo — riesgo de activacion accidental | P3 |
