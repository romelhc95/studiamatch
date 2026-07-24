# Taxonomía de Sitios y Plantillas Base

> Documento de referencia para el diagnóstico automático (`diagnose_institution.py`) y la configuración manual de `institution_site_profiles`.

Los 21 sitios web de instituciones analizados caen en 5 categorías recurrentes de sitio web. Cada plantilla define valores base de `institution_site_profiles` que cubren el 80% de la configuración. Solo el 20% restante (section_keywords específicos, exclusiones adicionales) necesita ajuste manual por institución.

---

## Tipo 1: WordPress + WooCommerce (E-commerce Educativo)

**Descripción**: Vende cursos como productos. Catálogo paginado con tarjetas de producto. Precio en JSON-LD estructurado (`Product.offers[0].price`). Fecha de inicio en atributo HTML personalizado (`data-fecha-inicio`). URLs limpias tipo `/producto/nombre-del-curso/`.

### Señales de detección
- Clases CSS `woocommerce-LoopProduct-link`, `woocommerce`
- `<script type="application/ld+json">` con `@type: Product`
- `<meta name="generator" content="WordPress...WooCommerce...">`
- URLs con `/producto/`, `/categoria-producto/`, `/carrito/`, `/checkout/`
- Scroll infinito o paginación AJAX en catálogos

### Perfil base

| Campo | Valor |
|-------|-------|
| `site_type` | `ecommerce` |
| `discovery_mode` | `catalog_link_extraction` |
| `catalog_link_selector` | `a.woocommerce-LoopProduct-link` |
| `price_regex` | *No necesario* — precio viene de JSON-LD |
| `requires_stealth` | `false` |
| `extraction_needs_browser` | `true` |
| `catalog_scroll_iterations` | `15` |
| `section_keywords` | Inicio, Duración, Modalidad, Dirigido a, Requisitos, Certificación, Objetivo General |
| `exclusion_patterns` | `/checkout/`, `/carrito/`, `/mi-cuenta/`, `add-to-cart=`, `/categoria-producto/` |
| `allowed_url_patterns` | `["^/producto/", "^/curso/", "^/diplomado/", "^/especializacion/"]` |
| `detail_wait_ms` | `5000` |

### Instituciones ejemplo
- **DMC Institute** (`dmc.pe`) — WooCommerce puro, Cloudflare protection, 45 programas activos

---

## Tipo 2: WordPress SSR Estándar (Instituto / Consultora Educativa)

**Descripción**: Sitio WordPress sin WooCommerce. Páginas de curso individuales con contenido estático renderizado en servidor. Estructura de headings predecible (h2 para secciones, h3 para subsecciones). Generalmente tiene sitemap XML completo.

### Señales de detección
- `<meta name="generator" content="WordPress">` sin WooCommerce
- `/wp-content/` en CSS/JS paths
- Sitemap en `/sitemap.xml` con >50 URLs de tipo `post` o `page`
- Estructura HTML semántica: article > h1 > section > h2

### Perfil base

| Campo | Valor |
|-------|-------|
| `site_type` | `traditional_ssr` |
| `discovery_mode` | `sitemap_bfs` |
| `price_regex` | `S/[\s]*[\d,]+` (Perú) |
| `requires_stealth` | `false` |
| `extraction_needs_browser` | `false` |
| `section_keywords` | Inversión, Inicio, Duración, Modalidad, Dirigido a, Requisitos, Certificación, Malla curricular, Perfil del egresado |
| `exclusion_patterns` | `/blog/`, `/contacto/`, `/nosotros/`, `/sobre-nosotros/`, `/author/`, `/category/`, `/tag/`, `/eventos/` |
| `allowed_url_patterns` | `["^/cursos/", "^/programas/", "^/diplomados/"]` |
| `detail_wait_ms` | `2000` |

### Instituciones ejemplo
- **DataPath** (`datapath.ai`) — WordPress SSR, programas tech bootcamp
- **Cibertec** (subdominio `educacioncontinua.cibertec.edu.pe`) — WordPress, catálogo extenso
- **SmartData** (`smartdata.com.pe`) — WordPress, programas data science
- **EducacionIT** (`educacionit.com`) — WordPress, tech courses Argentina
- **New Horizons** (`newhorizons.com.pe`) — WordPress estándar, programas IT
- **Colectivo23** (`colectivo23.com`) — WordPress, diseño y tecnología

---

## Tipo 3: EdTech SPA (Bootcamp / Plataforma JS-heavy)

**Descripción**: Single Page Application construida con React, Angular o Vue. Contenido cargado dinámicamente vía API interna. Frecuentemente tiene CDN/Cloudflare con protección anti-bot. URLs limpias con locale (`/pe/`, `/es/`, `/co/`). Precios en USD o moneda local.

### Señales de detección
- `<body>` casi vacío sin JS (solo `<div id="root">` o `<div id="app">`)
- Scripts con `react`, `vue`, `angular` en src
- API calls en background (`/api/v1/courses`, `/graphql`)
- Cloudflare challenge ("Checking your browser...") común
- `<link rel="preload">` con chunks JS, CSS asíncrono

### Perfil base

| Campo | Valor |
|-------|-------|
| `site_type` | `spa_js_heavy` |
| `discovery_mode` | `sitemap_bfs` |
| `extraction_needs_browser` | `true` |
| `requires_stealth` | `true` |
| `requires_cloudflare_bypass` | `true` (variable) |
| `popup_close_selectors` | `["[class*=\"modal\"] button.close", "[class*=\"popup\"] [class*=\"close\"]", "[aria-label=\"Close\"]"]` |
| `detail_wait_ms` | `3000` |
| `price_regex` | `USD\s*[\d,]+` o `\$\s*[\d,]+` |
| `section_keywords` | Inicio, Duración, Modalidad, Requisitos, Plan de estudios, Certificación, Salida laboral |
| `exclusion_patterns` | `/blog/`, `/contacto/`, `/login/`, `/register/`, `/politica/`, `/terminos/` |

### Instituciones ejemplo
- **CoderHouse** (`coderhouse.com.pe`) — React SPA, scroll infinito
- **SoyHenry** (`soyhenry.com`) — React, bootcamp full-stack
- **Le Wagon** (`lewagon.com/es/lima`) — React/Vue, CDN global
- **TripleTen** (`tripleten.com/es-pe/`) — React, protect Cloudflare
- **Digital House** (`digitalhouse.com/pe`) — React SPA

---

## Tipo 4: Universidad Tradicional SSR

**Descripción**: Sitio universitario con múltiples subdominios o secciones (pregrado, posgrado, educación ejecutiva). Páginas de programa con estructura académica formal. Secciones bien definidas con headings. Frecuentemente tiene sitemap pero con mucho ruido (noticias, eventos, investigaciones, admisión).

### Señales de detección
- Dominio `.edu.pe` o `.edu`
- Subdominios segmentados: `posgrado.university.pe`, `postgrado.university.pe`
- Múltiples secciones de ruido: `/noticias/`, `/eventos/`, `/investigacion/`, `/admision/`
- `<meta name="author" content="Universidad...">`
- Title tag largo con nombre de universidad + programa

### Perfil base

| Campo | Valor |
|-------|-------|
| `site_type` | `traditional_ssr` |
| `discovery_mode` | `sitemap_bfs` o `hardcoded_urls` |
| `extraction_needs_browser` | `false` |
| `requires_stealth` | `false` |
| `price_regex` | `S/[\s]*[\d,.]+` |
| `duration_regex` | `(\d+\.?\d*)\s*(meses|años|ciclos|horas|créditos)` |
| `section_keywords` | Inversión, Inicio, Duración, Modalidad, Perfil del egresado, Malla curricular, Requisitos, Grado académico, Campo laboral |
| `exclusion_patterns` | `/noticias/`, `/eventos/`, `/admision/`, `/biblioteca/`, `/investigacion/`, `.pdf` |
| `title_prefix_removals` | `["Universidad X \\| ", "U. X - "]` |
| `section_mode_map` | Mapea segmentos de URL a modalidad |
| `detail_wait_ms` | `3000` |

### Instituciones ejemplo
- **U. Lima** (`ulima.edu.pe`) — SSR, 59+ exclusiones afinadas
- **UPC** (`postgrado.upc.edu.pe`) — SSR, subdominio
- **USIL** (`usil.edu.pe`) — SSR, popups de admisión
- **UTP** (`postgradoutp.edu.pe`) — SSR, subdominio
- **UNI** (`fieecs.uni.edu.pe`) — SSR, subdominio de facultad
- **PUCP** (`pucp.edu.pe`) — SSR, catálogo paginado JetEngine
- **U. Continental** (`ucontinental.edu.pe`) — SSR
- **U. del Pacífico** (`up.edu.pe`) — SSR
- **SENATI** (`senati.edu.pe`) — SSR
- **UNMSM** (`unmsm.edu.pe`) — SSR
- **IDAT** (`idat.edu.pe`) — SSR

---

## Tipo 5: HubSpot / Lead-Gen Landing

**Descripción**: Páginas de aterrizaje construidas con HubSpot, Instapage u otro CMS de marketing. Frecuentemente son formularios de captación de leads disfrazados de página de curso. Contenido mínimo o embebido en iframes/slides. URLs con parámetros UTM, `hsLang`, o fragmentadas por campaña.

### Señales de detección
- Scripts con `hs-scripts.com`, `hubspot.com`, `hubapi.com`
- `<form>` con `data-hs-cf-bound` u otros atributos HubSpot
- URLs con `hsLang=`, `utm_source=`, `utm_campaign=`
- Contenido sustancial < 500 chars sin JS
- iframes de SlideShare, Canva, o plataformas de presentación

### Perfil base

| Campo | Valor |
|-------|-------|
| `site_type` | `traditional_ssr` |
| `discovery_mode` | `hardcoded_urls` |
| `pipeline_enabled` | `false` |
| `pipeline_ready` | `false` |
| `extraction_needs_browser` | `false` |
| `price_regex` | *Generalmente sin precio visible* |
| `requires_stealth` | `false` |
| `exclusion_patterns` | `hsLang=`, `utm_`, `/thank-you`, `/gracias`, `/confirmacion`, `/ty/` |
| `detail_wait_ms` | `2000` |

### Señales de alerta para revisión manual
- La URL principal es un formulario de contacto, no un programa
- Sin información de precio, duración ni fechas
- El contenido "del curso" está en un PDF descargable o en Slides
- Redirecciones a WhatsApp Business API
- Múltiples URLs que llevan al mismo formulario

### Instituciones ejemplo
- **UCAL** (subdominio `informes.ucal.edu.pe`) — HubSpot lead-gen puro
- **WE Educación** (`weedu.pe`) — Slides, sin páginas de detalle reales

---

## Uso con `diagnose_institution.py`

El script de diagnóstico (`scripts/maintenance/diagnose_institution.py`) detecta automáticamente el tipo de sitio y sugiere el perfil correspondiente. El flujo es:

1. **CMS Detection** → identifica WordPress, WooCommerce, React, etc.
2. **JS-Required Check** → determina si necesita `spa_js_heavy`
3. **Asignación de plantilla** → elige la plantilla base según el CMS detectado
4. **Ajuste de fields** → sobrescribe section_keywords, exclusiones con lo detectado en la página
5. **Output** → JSON con perfil sugerido + `_confidence` por campo

### Matriz de asignación automática

| CMS Detectado | JS-Required | Plantilla Asignada |
|---------------|-------------|-------------------|
| WooCommerce | true | Tipo 1 — Ecommerce |
| WordPress | false | Tipo 2 — WordPress SSR |
| WordPress | true | Tipo 4 — Universidad SSR (con browser) |
| React / Vue / Angular | true | Tipo 3 — EdTech SPA |
| HubSpot | false | Tipo 5 — Lead-Gen |
| HTML puro | false | Tipo 2 (revisar) |
| HTML puro | true | Tipo 3 (revisar) |

### Campos que SIEMPRE requieren validación humana

- `section_keywords` — el mapeo heading→campo depende del naming específico de cada institución
- `exclusion_patterns` — cada institución tiene ruido diferente (blogs, news, eventos)
- `allowed_url_patterns` — la estructura de URLs varía por institución
- `price_regex` — formato de moneda y ubicación en DOM varía
- `pipeline_ready` — solo se activa tras revisión humana de las 5 capas de defensa

---

## Evolución futura

Cuando `diagnose_institution.py` alcance madurez suficiente (>90% tasa de acierto), la auto-detección se integrará en `universal_harvester.py` (Fase 121). El harvester creará perfiles automáticamente para instituciones sin perfil, con `auto_generated=true` y `pipeline_ready=false` para revisión humana.

Las plantillas se mantendrán en este documento hasta que se considere migrarlas a una tabla `site_templates` en DB (Fase 120 Actividad 3, opcional).
