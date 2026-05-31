# 📊 Reporte de Revisión Manual por Institución — StudIAMatch

**Base de datos:** Supabase Pro (`xwhtiqmboljkshrtviyw`)  
**Fecha de generación:** 31 de mayo de 2026 — Actualizado post-FG2 IDAT  
**Propósito:** Revisión manual de sitios web institucionales para verificar disponibilidad de información de programas y mejorar la extracción.

---

## Resumen Ejecutivo

| Métrica | Valor |
|---|---|
| Total instituciones | 27 |
| Con perfil de scraping | 27 |
| `pipeline_ready = true` | 22 |
| `production_enabled = true` | 14 |
| Cursos publicados (activos + verificados) | **142** (en 8 instituciones) |
| Cursos inactivos | 44 (en 3 instituciones) |
| Cursos mock data | 92 de 142 (65%) |
| Enriched synced totales | 211 |

### Distribución de Cursos Publicados

| # | Institución | Publicados | Mock | Pipeline Ready | Prod |
|---|---|---|---|---|---|
| 1 | **IDAT** | 63 | 55 (87%) | ✅ | ✅ | ⭐ <small>Perfil actualizado</small> |
| 2 | **DMC** | 39 | 17 (44%) | ✅ | ✅ |
| 3 | **Universidad de Lima** | 17 | 6 (35%) | ✅ | ✅ |
| 4 | **CoderHouse** | 10 | 3 (30%) | ✅ | ✅ |
| 5 | **DataPath** | 6 | 0 | ✅ | ✅ |
| 6 | **Le Wagon** | 4 | 0 | ✅ | ✅ |
| 7 | **TripleTen** | 2 | 0 | ✅ | ✅ |
| 8 | **UPC** | 1 | 0 | ✅ | ✅ |
| 9 | PUCP | 0 (20 inactivos) | 11 | ✅ | ❌ |
| 10 | SENATI | 0 (14 inactivos) | 1 | ✅ | ❌ |
| 11 | U. Continental | 0 (10 inactivos) | 0 | ❌ | ❌ |

### Pipeline por Institución (Staging Raw)

| Institución | Staging Raw | Pipeline |
|---|---|---|
| PUCP | 416 processing + 69 processed + 10 discovered | Activo |
| U. Lima | 159 processing + 18 processed | Activo |
| SENATI | 169 processing + 16 processed + 73 discovered | Activo |
| UPC | 57 discovered + 1 processed | Activo |
| IDAT | 64 processed + 29 processing | Activo |
| UTP | 221 skipped + 95 discarded | **Inactivo** |
| UNMSM | 49 discarded + 47 discovered | Activo (prod ❌) |
| U. Continental | 52 discovered + 13 processing | **Inactivo** |
| UNI | 1 discarded | **Inactivo** |

---

## 📋 Leyenda de Pilares

Cada pilar tiene un número, nombre, campo en base de datos y tabla donde se almacena:

| # | Pilar | Campo en DB | Tabla |
|---|---|---|---|
| **P1** | Nombre del programa | `name` | `courses` / `enriched_programs` |
| **P2** | Institución | `institution_id` | `courses` / `enriched_programs` |
| **P3** | Categoría / Área de estudio | `category_id` | `courses` / `enriched_programs` |
| **P4** | Nivel académico | `course_type` (courses) / `degree_type` (enriched) | `courses` / `enriched_programs` |
| **P5** | Modalidad | `mode` (courses) / `modality` (enriched) | `courses` / `enriched_programs` |
| **P6** | Duración (meses) | `duration` (courses) / `duration_months` (enriched) | `courses` / `enriched_programs` |
| **P7** | Costo total | `price_pen` (courses) / `total_cost_est` (enriched) | `courses` / `enriched_programs` |
| **P8** | Plan de estudios | `curriculum_summary` (JSONB) | `enriched_programs` |
| **P9** | Requisitos de admisión | `requirements` | `enriched_programs` |
| **P10** | URL del programa | `url` | `courses` / `enriched_programs` |
| **P11** | Slug amigable | `slug` | `courses` |
| **P12** | Descripción | `description_long` | `courses` |
| **P13** | ¿Requiere examen de admisión? | ❌ **No existe en schema** | — |
| **P14** | Horas/créditos académicos | ❌ **No existe en schema** | — |

> **Nota:** P13 (`entry_exam_required`) y P14 (`credit_hours`) no existen como columnas en la base de datos actual. Se recomienda agregarlas al schema.

---

## SECCIÓN A: INSTITUCIONES CON CURSOS PUBLICADOS

---

### A1. IDAT (`idat`) ⭐ ACTUALIZADO POST-FG2

| Campo | Valor |
|---|---|
| **Website** | [https://www.idat.edu.pe/](https://www.idat.edu.pe/) |
| **Tipo** | Instituto |
| **Pipeline ready** | ✅ |
| **Production enabled** | ✅ |
| **Site type** | `spa_js_heavy` |
| **Discovery mode** | `hardcoded_urls` |
| **Seed URLs** | 0 (vacío) |
| **Requires stealth** | No |
| **CF bypass** | No |
| **Notes** | "IDAT uses heavy JS." |
| **Exclusiones** | Incluye `https://www.idat.edu.pe/` (homepage) para evitar ruido |

#### Perfil actual (section_keywords + field_defaults)

| Tipo | Configuración |
|---|---|
| `section_keywords` | Duración→duration_text, Modalidad→modality, Horarios→schedule_info, Plan de estudios→curriculum_summary, Ciclo→curriculum_summary, Áreas de trabajo→graduate_profile |
| `field_defaults` | mode=Presencial, **total_cost_est=null**, **requirements=null**, **price_status=consultar** |

#### Resumen de Pilares en Cursos Publicados (63 total, 55 mock) — POST-FG2

| P# | Pilar | Campo | Presentes | Ausentes | % | vs Antes |
|---|---|---|---|---|---|---|
| P4 | Nivel académico | `course_type` | 63 | 0 | ✅ **100%** | +40% |
| P5 | Modalidad | `mode` | 63 | 0 | ✅ 100% | = |
| P6 | Duración | `duration` | 63 | 0 | ✅ 100% | +97% |
| P7 | Costo total | `price_pen` | 0 | 63 | ✅ **correcto** | IDAT no publica |
| P7b | Price status | `price_status` | 63 consultar | 0 | ✅ **100%** | corregido |
| P12 | Descripción | `description_long` | 55 | 8 | 🟡 **87.3%** | +64% |
| P9 | Requisitos | `requirements` | 0 | 63 | ✅ **correcto** | IDAT no publica |
| P3 | Categoría | `category_id` | 63 | 0 | ✅ 100% | = |

#### Pilares en Enriched (64 synced: 8 Cloudflare + 56 mock) — POST-FG2

| P# | Pilar | Campo | Ausentes | % | vs Antes |
|---|---|---|---|---|---|
| P4 | Nivel académico | `degree_type` | 0 | ✅ 0% | +40% |
| P5 | Modalidad | `modality` | 0 | ✅ 0% | = |
| P6 | Duración | `duration_months` | 63 | 🔴 98.4% | persiste |
| P7 | Costo total | `total_cost_est` | 64 | ✅ **100% null** | correcto |
| P8 | Plan de estudios | `curriculum_summary` | 56 | 🔴 87.5% | empeoró* |
| P9 | Requisitos | `requirements` | 64 | ✅ **100% vacío** | correcto |

> \* `curriculum_summary` empeoró porque 56/64 registros usaron mock (Cloudflare falló). Los 8 Cloudflare sí tienen curriculum.

#### Pipeline Status
- **Staging:** 64 processed, 0 processing, 0 discovered, 1 skipped
- **Cleansed:** 64 enriched
- **Enriched:** 8 Cloudflare synced, 56 mock synced
- **Courses:** 63 activos + 1 inactivo (homepage eliminado)

#### Muestra de Cursos (post-FG2)
| Curso | URL | Type | Mode | Duration | Price | Desc |
|---|---|---|---|---|---|---|
| Desarrollo Front-End | [link](https://www.idat.edu.pe/escuela-de-coding/desarrollo-front-end/) | Curso | Presencial | Consultar | Consultar | ✅ |
| Macros y Prog. Visual Basic | [link](https://www.idat.edu.pe/cursos-de-formacion-continua/macros-y-programacion-visual-basic/) | Curso | Presencial | Consultar | Consultar | ✅ |
| Diseño de Autocad | [link](https://www.idat.edu.pe/cursos-de-formacion-continua/diseno-en-autocad/) | Curso | Presencial | ✅ texto | Consultar | 🔴 |
| Mecatrónica Industrial | [link](https://www.idat.edu.pe/carreras-profesionales-tecnicas/mecatronica-industrial/) | Curso | Presencial | Consultar | Consultar | ✅ |
| Adm. Bancaria y Financiera | [link](https://www.idat.edu.pe/carreras-profesionales-tecnicas/administracion-bancaria-y-financiera/) | Curso | Presencial | Consultar | Consultar | ✅ |

#### 🔍 Preguntas para Revisión Manual
1. ¿El sitio web de IDAT lista precios de cada programa individualmente? → **NO** (confirmado por scraping manual)
2. ¿Se puede inferir la duración en meses desde la página de cada programa? → **SÍ** (ej: "2 años", "24 horas / 1 mes")
3. ¿Las páginas de carreras tienen requisitos de admisión explícitos? → **NO**
4. ¿Existe un catálogo central de cursos cortos con toda la info en una sola página?
5. ¿Por qué los seed_urls están vacíos? ¿Deberían agregarse seeds específicos?

#### ⚠️ Pendientes IDAT
| Issue | Detalle |
|---|---|
| `duration = "Consultar"` | El mock no extrajo duración real del HTML. Los 8 Cloudflare sí la extraen. |
| 87% mock data | Cloudflare LLM falló (timeout/JSON inválido), DeepSeek sin API key |
| `course_type = "Curso"` | Las carreras técnicas deberían clasificarse como "Carrera Técnica" |

---

### A2. DMC (`dmc`)

| Campo | Valor |
|---|---|
| **Website** | [https://dmc.pe](https://dmc.pe) |
| **Tipo** | Instituto |
| **Pipeline ready** | ✅ |
| **Site type** | `ecommerce` |
| **Discovery mode** | `catalog_link_extraction` |
| **Seed URLs** | 4 páginas de categoría (cursos, especializaciones, diplomas, certificaciones) |
| **Requires stealth** | ✅ Sí |
| **CF bypass** | ✅ Sí |

#### Resumen de Pilares en Cursos Publicados (39 total, 17 mock)

| P# | Pilar | Campo | Presentes | Ausentes | % Completo |
|---|---|---|---|---|---|
| P4 | Nivel académico | `course_type` | 19 | 20 | 🟡 48.7% |
| P5 | Modalidad | `mode` | 39 | 0 | ✅ 100% |
| P6 | Duración | `duration` (válida) | 1 | 38 | 🔴 2.6% |
| P7 | Costo total | `price_pen` (>0) | 37 | 2 | ✅ 94.9% |
| P12 | Descripción | `description_long` | 17 | 22 | 🟡 43.6% |
| P3 | Categoría | `category_id` | 39 | 0 | ✅ 100% |

#### Pilares en Enriched (39 synced)

| P# | Pilar | Campo | Ausentes | % |
|---|---|---|---|---|
| P4 | Nivel académico | `degree_type` | 20 | 🔴 51.3% |
| P6 | Duración | `duration_months` | 39 | 🔴 100% |
| P7 | Costo total | `total_cost_est` | 2 | ✅ 5.1% |
| P8 | Plan de estudios | `curriculum_summary` | 17 | 🟡 43.6% |
| P9 | Requisitos | `requirements` | 17 | 🟡 43.6% |
| P3 | Categoría | `categories` | 39 | 🔴 100% |

#### Pipeline Status
- **Staging:** 39 processed
- **Cleansed:** 39 enriched
- **Enriched:** 22 Cloudflare synced, 17 mock synced

#### 🔍 Preguntas
1. DMC destaca por tener precios (95% de cursos) — ¿de dónde se extraen? ¿Están visibles en la página de producto?
2. El 44% de datos son mock — ¿es porque el LLM falló o porque las páginas no tienen suficiente texto?
3. ¿Las páginas de producto muestran duración en horas/meses? (0% duration_months en enriched)
4. ¿Los requisitos están en una sección separada o en el cuerpo del texto?
5. Al ser ecommerce (WooCommerce), ¿se puede scrapear vía API REST de WordPress?

---

### A3. Universidad de Lima (`universidad-de-lima`)

| Campo | Valor |
|---|---|
| **Website** | [https://www.ulima.edu.pe/](https://www.ulima.edu.pe/) |
| **Tipo** | Universidad |
| **Pipeline ready** | ✅ |
| **Site type** | `traditional_ssr` |
| **Discovery mode** | `hardcoded_urls` |
| **Seed URLs** | 102 URLs curadas (pregrados, posgrados, idiomas, educación ejecutiva) |
| **Requires stealth** | No |
| **CF bypass** | No |
| **Notes** | "102 seed URLs curated. Pipeline activated by 20260526_ulima_pipeline_activation.sql." |

#### Resumen de Pilares en Cursos Publicados (17 total, 6 mock)

| P# | Pilar | Campo | Presentes | Ausentes | % Completo |
|---|---|---|---|---|---|
| P4 | Nivel académico | `course_type` | 11 | 6 | 🟡 64.7% |
| P5 | Modalidad | `mode` | 17 | 0 | ✅ 100% |
| P6 | Duración | `duration` (válida) | 5 | 12 | 🔴 29.4% |
| P7 | Costo total | `price_pen` (>0) | 0 | 17 | 🔴 0% |
| P12 | Descripción | `description_long` | 6 | 11 | 🔴 35.3% |
| P3 | Categoría | `category_id` | 17 | 0 | ✅ 100% |

#### Pilares en Enriched (17 synced)

| P# | Pilar | Campo | Ausentes | % |
|---|---|---|---|---|
| P4 | Nivel académico | `degree_type` | 6 | 🔴 35.3% |
| P6 | Duración | `duration_months` | 15 | 🔴 88.2% |
| P7 | Costo total | `total_cost_est` | 17 | 🔴 100% |
| P8 | Plan de estudios | `curriculum_summary` | 6 | 🔴 35.3% |
| P9 | Requisitos | `requirements` | 17 | 🔴 100% |
| P3 | Categoría | `categories` | 17 | 🔴 100% |

#### Pipeline Status
- **Staging:** 159 processing, 18 processed
- **Cleansed:** 17 enriched
- **Enriched:** 11 Cloudflare synced, 6 mock synced

#### 🔍 Preguntas
1. U. Lima tiene 102 seed URLs — ¿todas apuntan a páginas de programa o algunas son páginas institucionales?
2. 0% de precios en 17 cursos — ¿la universidad publica costos en sus páginas de programa?
3. 159 URLs en "processing" en staging_raw — ¿el pipeline se estancó? Revisar logs.
4. ¿Las páginas de posgrado/maestría tienen más información que las de pregrado?
5. ¿Los requisitos están listados o solo se menciona "tener grado de bachiller"?

---

### A4. CoderHouse (`coderhouse`)

| Campo | Valor |
|---|---|
| **Website** | [https://www.coderhouse.com/](https://www.coderhouse.com/) |
| **Tipo** | Instituto |
| **Pipeline ready** | ✅ |
| **Site type** | `spa_js_heavy` |
| **Discovery mode** | `hardcoded_urls` |
| **Seed URLs** | 10 URLs hardcodeadas (carreras y cursos en /pe/) |
| **Requires stealth** | ✅ Sí |
| **CF bypass** | ✅ Sí |

#### Resumen de Pilares en Cursos Publicados (10 total, 3 mock)

| P# | Pilar | Campo | Presentes | Ausentes | % Completo |
|---|---|---|---|---|---|
| P4 | Nivel académico | `course_type` | 7 | 3 | 🟡 70% |
| P5 | Modalidad | `mode` | 10 | 0 | ✅ 100% |
| P6 | Duración | `duration` (válida) | 0 | 10 | 🔴 0% |
| P7 | Costo total | `price_pen` (>0) | 0 | 10 | 🔴 0% |
| P12 | Descripción | `description_long` | 3 | 7 | 🔴 30% |
| P3 | Categoría | `category_id` | 10 | 0 | ✅ 100% |

#### Pilares en Enriched (10 synced)

| P# | Pilar | Campo | Ausentes | % |
|---|---|---|---|---|
| P4 | Nivel académico | `degree_type` | 3 | 🔴 30% |
| P6 | Duración | `duration_months` | 10 | 🔴 100% |
| P7 | Costo total | `total_cost_est` | 10 | 🔴 100% |
| P8 | Plan de estudios | `curriculum_summary` | 3 | 🔴 30% |
| P9 | Requisitos | `requirements` | 9 | 🔴 90% |
| P3 | Categoría | `categories` | 5 | 🟡 50% |

#### Pipeline Status
- **Staging:** 10 processed
- **Cleansed:** 10 enriched
- **Enriched:** 7 Cloudflare synced, 3 mock

#### 🔍 Preguntas
1. CoderHouse requiere stealth + CF bypass — ¿está funcionando correctamente el bypass?
2. ¿La página de cada curso/carrera muestra duración? (0% duration en courses)
3. ¿Los precios están detrás de login? ¿Se pueden scrapear?
4. 10 seeds es poco — ¿se pueden descubrir más programas desde el sitemap o navegación?

---

### A5. DataPath (`datapath`)

| Campo | Valor |
|---|---|
| **Website** | [https://www.datapath.ai/](https://www.datapath.ai/) |
| **Tipo** | Instituto |
| **Pipeline ready** | ✅ |
| **Site type** | `spa_js_heavy` |
| **Discovery mode** | `hardcoded_urls` |
| **Seed URLs** | 9 URLs (cursos + rutas/bootcamps) |
| **Requires stealth** | ✅ Sí |
| **CF bypass** | No |

#### Resumen de Pilares en Cursos Publicados (6 total, 0 mock)

| P# | Pilar | Campo | Presentes | Ausentes | % Completo |
|---|---|---|---|---|---|
| P4 | Nivel académico | `course_type` | 6 | 0 | ✅ 100% |
| P5 | Modalidad | `mode` | 6 | 0 | ✅ 100% |
| P6 | Duración | `duration` (válida) | 6 | 0 | ✅ 100% |
| P7 | Costo total | `price_pen` (>0) | 6 | 0 | ✅ 100% |
| P12 | Descripción | `description_long` | 1 | 5 | 🔴 16.7% |
| P3 | Categoría | `category_id` | 6 | 0 | ✅ 100% |

#### Pilares en Enriched (6 synced)

| P# | Pilar | Campo | Ausentes | % |
|---|---|---|---|---|
| P4 | Nivel académico | `degree_type` | 0 | ✅ 0% |
| P6 | Duración | `duration_months` | 2 | 🟡 33.3% |
| P7 | Costo total | `total_cost_est` | 0 | ✅ 0% |
| P8 | Plan de estudios | `curriculum_summary` | 0 | ✅ 0% |
| P9 | Requisitos | `requirements` | 4 | 🔴 66.7% |
| P3 | Categoría | `categories` | 0 | ✅ 0% |

#### Pipeline Status
- **Staging:** 6 processed, 3 processing
- **Cleansed:** 6 enriched
- **Enriched:** 6 Cloudflare synced

#### 🔍 Preguntas
1. DataPath es la institución con mejor completitud de datos — ¿qué hace diferente su sitio?
2. 0% de datos mock — ¿el HTML de sus páginas es particularmente limpio/estructurado?
3. 5 de 6 cursos sin description_long en courses pero con enriched completo — ¿el sync no está copiando bien el campo?
4. ¿Las páginas de "rutas" vs "cursos" tienen estructura diferente?

---

### A6. Le Wagon (`lewagon`)

| Campo | Valor |
|---|---|
| **Website** | [https://www.lewagon.com/es/lima](https://www.lewagon.com/es/lima) |
| **Tipo** | Instituto |
| **Pipeline ready** | ✅ |
| **Site type** | `spa_js_heavy` |
| **Discovery mode** | `hardcoded_urls` |
| **Seed URLs** | 4 cursos |
| **Requires stealth** | ✅ Sí |
| **CF bypass** | No |

#### Resumen de Pilares en Cursos Publicados (4 total, 0 mock)

| P# | Pilar | Campo | Presentes | Ausentes | % Completo |
|---|---|---|---|---|---|
| P4 | Nivel académico | `course_type` | 4 | 0 | ✅ 100% |
| P5 | Modalidad | `mode` | 4 | 0 | ✅ 100% |
| P6 | Duración | `duration` (válida) | 4 | 0 | ✅ 100% |
| P7 | Costo total | `price_pen` (>0) | 0 | 4 | 🔴 0% |
| P12 | Descripción | `description_long` | 0 | 4 | 🔴 0% |
| P3 | Categoría | `category_id` | 4 | 0 | ✅ 100% |

#### Pilares en Enriched (4 synced)

| P# | Pilar | Campo | Ausentes | % |
|---|---|---|---|---|
| P4 | Nivel académico | `degree_type` | 0 | ✅ 0% |
| P6 | Duración | `duration_months` | 0 | ✅ 0% |
| P7 | Costo total | `total_cost_est` | 4 | 🔴 100% |
| P8 | Plan de estudios | `curriculum_summary` | 0 | ✅ 0% |
| P9 | Requisitos | `requirements` | 4 | 🔴 100% |
| P3 | Categoría | `categories` | 4 | 🔴 100% |

#### 🔍 Preguntas
1. Le Wagon tiene precios en su web pero no se extraen — ¿están en USD y el parser no los reconoce?
2. ¿Los requisitos están en la página o son implícitos?
3. ¿Hay más programas en `/es/` que no están en los seeds?

---

### A7. TripleTen (`tripleten`)

| Campo | Valor |
|---|---|
| **Website** | [https://tripleten.ec/](https://tripleten.ec/) |
| **Tipo** | Instituto |
| **Pipeline ready** | ✅ |
| **Site type** | `spa_js_heavy` |
| **Seed URLs** | 2 programas |
| **Requires stealth** | ✅ Sí |

#### Resumen de Pilares (2 cursos, 0 mock)

| P# | Pilar | Campo | Presentes | Ausentes |
|---|---|---|---|---|
| P4 | Nivel académico | `course_type` | 2 | 0 ✅ |
| P5 | Modalidad | `mode` | 2 | 0 ✅ |
| P6 | Duración | `duration` | 2 | 0 ✅ |
| P7 | Costo total | `price_pen` | 0 | 2 🔴 |
| P12 | Descripción | `description_long` | 0 | 2 🔴 |

#### 🔍 Preguntas
1. Solo 2 programas — ¿TripleTen tiene más cursos en su web que no fueron descubiertos?
2. ¿Los precios están en USD o moneda local?

---

### A8. UPC (`upc`)

| Campo | Valor |
|---|---|
| **Website** | [https://www.upc.edu.pe/](https://www.upc.edu.pe/) |
| **Tipo** | Universidad |
| **Pipeline ready** | ✅ |
| **Site type** | `spa_js_heavy` |
| **Seed URLs** | 0 (vacío) |
| **Notes** | "UPC uses heavy JS rendering." |

#### Pipeline Status
- **Staging:** 57 discovered, 1 processed, 1 processing
- **Cleansed:** 1 enriched
- **Enriched:** 1 Cloudflare synced
- **Courses:** 1 publicado

#### 🔍 Preguntas
1. Solo 1 curso publicado de 57 URLs discovered — ¿el pipeline está funcionando?
2. 0 seed URLs — ¿qué URLs deberían agregarse manualmente?
3. UPC es SPA pesado — ¿el renderizado JS está funcionando correctamente?
4. Revisar las 57 URLs discovered: ¿cuántas son realmente páginas de programa?

---

## SECCIÓN B: INSTITUCIONES CON PERFIL PERO SIN CURSOS PUBLICADOS

---

### B1. Pontificia Universidad Católica del Perú (`pucp`)

| Campo | Valor |
|---|---|
| **Website** | [https://www.pucp.edu.pe](https://www.pucp.edu.pe) |
| **Pipeline ready** | ✅ |
| **Production enabled** | ❌ |
| **Site type** | `spa_js_heavy` |
| **Seed URLs** | 0 |
| **Notes** | "PUCP website. Paginated catalog discovery via JetEngine." |

#### Pipeline Status
| Tabla | Estado |
|---|---|
| Staging raw | 416 processing, 69 processed, 10 discovered, 5 discarded |
| Cleansed | 20 enriched, 48 pending |
| Enriched | 9 Cloudflare synced, 11 mock synced |
| Courses | 20 inactivos |

#### URLs Discovered (ejemplos)
- [https://www.pucp.edu.pe/admision/admision-pregrado/costo-estudios/pensiones/valor-de-las-cuotas/](https://www.pucp.edu.pe/admision/admision-pregrado/costo-estudios/pensiones/valor-de-las-cuotas/)
- [https://www.pucp.edu.pe/recursos-para-la-virtualizacion/planificacion-de-clases/](https://www.pucp.edu.pe/recursos-para-la-virtualizacion/planificacion-de-clases/)
- [https://www.pucp.edu.pe/beca/estudiorodrigo/](https://www.pucp.edu.pe/beca/estudiorodrigo/)
- [https://www.pucp.edu.pe/certificaciones/grados-y-titulos/](https://www.pucp.edu.pe/certificaciones/grados-y-titulos/)

#### Pilares en Enriched (20 synced, pero cursos inactivos)

| P# | Pilar | Campo | Ausentes |
|---|---|---|---|
| P6 | Duración | `duration_months` | 13 (65%) |
| P7 | Costo total | `total_cost_est` | 20 (100%) |
| P8 | Plan de estudios | `curriculum_summary` | 11 (55%) |
| P9 | Requisitos | `requirements` | 18 (90%) |
| P3 | Categoría | `categories` | 18 (90%) |

#### 🔍 Preguntas
1. ¿Por qué los 20 cursos están inactivos si enriched está synced? ¿Fallo en sync_vector_worker?
2. 416 URLs en "processing" — ¿el pipeline tiene un cuello de botella?
3. ¿Las URLs discovered son páginas de programa o institucionales? (los ejemplos parecen institucionales)
4. `production_enabled = false` — ¿es intencional? ¿Cuándo activarlo?
5. 0 seed URLs — ¿qué URLs de programas PUCP deberían listarse?

---

### B2. SENATI (`senati`)

| Campo | Valor |
|---|---|
| **Website** | [https://www.senati.edu.pe/](https://www.senati.edu.pe/) |
| **Pipeline ready** | ✅ |
| **Production enabled** | ❌ |
| **Site type** | `traditional_ssr` |
| **Seed URLs** | 0 |

#### Pipeline Status
| Tabla | Estado |
|---|---|
| Staging raw | 169 processing, 16 processed, 73 discovered, 5 discarded |
| Cleansed | 15 enriched |
| Enriched | 12 Cloudflare synced, 1 DeepSeek, 1 mock, 1 error |
| Courses | 14 inactivos |

#### URLs Discovered (ejemplos)
- [http://www.senati.edu.pe/content/centro-tecnologico-de-textiles-y-confecciones](http://www.senati.edu.pe/content/centro-tecnologico-de-textiles-y-confecciones)
- [http://www.senati.edu.pe/buscar/carreras](http://www.senati.edu.pe/buscar/carreras)
- [https://www.senati.edu.pe/buscar/tipo/curso](https://www.senati.edu.pe/buscar/tipo/curso)
- [http://www.senati.edu.pe/empresas/bolsa-de-trabajo](http://www.senati.edu.pe/empresas/bolsa-de-trabajo)

#### 🔍 Preguntas
1. SENATI tiene un buscador de carreras — ¿se puede scrapear sistemáticamente?
2. 73 discovered — ¿cuántas son URLs de programa vs institucionales?
3. ¿Las páginas de carrera de SENATI muestran malla curricular, duración y costo?
4. `production_enabled = false` — misma situación que PUCP.

---

### B3. Universidad Continental (`universidad-continental`)

| Campo | Valor |
|---|---|
| **Website** | [https://ucontinental.edu.pe/](https://ucontinental.edu.pe/) |
| **Pipeline ready** | ❌ |
| **Production enabled** | ❌ |
| **Site type** | `traditional_ssr` |
| **Seed URLs** | 0 |
| **Notes** | "SPA-like pages but SSR accessible." |

#### Pipeline Status
| Tabla | Estado |
|---|---|
| Staging raw | 52 discovered, 13 processing, 10 processed, 8 discarded, 6 skipped |
| Cleansed | 10 enriched |
| Enriched | 9 Cloudflare synced, 1 DeepSeek |
| Courses | 10 inactivos |

#### URLs Discovered (ejemplos — ¡son páginas de carrera!)
- [https://ucontinental.edu.pe/carrera/tecnologia-medica-especialidad-en-terapia-fisica-y-rehabilitacion/](https://ucontinental.edu.pe/carrera/tecnologia-medica-especialidad-en-terapia-fisica-y-rehabilitacion/)
- [https://ucontinental.edu.pe/carrera/administracion-y-finanzas/](https://ucontinental.edu.pe/carrera/administracion-y-finanzas/)
- [https://ucontinental.edu.pe/carrera/administracion-y-gestion-del-talento-humano/](https://ucontinental.edu.pe/carrera/administracion-y-gestion-del-talento-humano/)
- [https://ucontinental.edu.pe/carrera/ingenieria-mecanica/](https://ucontinental.edu.pe/carrera/ingenieria-mecanica/)

#### 🔍 Preguntas
1. `pipeline_ready = false` — ¿por qué? Las URLs discovered SÍ parecen ser programas válidos.
2. ¿Qué falta para activar U. Continental? Tiene 52 URLs discovered con buen potencial.
3. 10 enriched synced pero 10 cursos inactivos — mismo patrón que PUCP/SENATI.

---

### B4. UNMSM (`unmsm`) — Pipeline activo, sin cursos

| Campo | Valor |
|---|---|
| **Website** | [https://unmsm.edu.pe/](https://unmsm.edu.pe/) |
| **Pipeline ready** | ✅ |
| **Production enabled** | ❌ |
| **Site type** | `traditional_ssr` |
| **Seed URLs** | 0 |

#### Pipeline Status
| Tabla | Estado |
|---|---|
| Staging raw | 49 discarded, 47 discovered |
| Cleansed | 0 |
| Enriched | 0 |
| Courses | 0 |

#### URLs Discovered (ejemplos)
- [https://unmsm.edu.pe/cursos-y-talleres/taller-de-violin](https://unmsm.edu.pe/cursos-y-talleres/taller-de-violin)
- [https://unmsm.edu.pe/direcciones-artisticas/banda-universitaria](https://unmsm.edu.pe/direcciones-artisticas/banda-universitaria)
- [https://unmsm.edu.pe/cursos-y-talleres/taller-de-cine-para-adolescencias](https://unmsm.edu.pe/cursos-y-talleres/taller-de-cine-para-adolescencias)
- [https://unmsm.edu.pe/agenda-cultural](https://unmsm.edu.pe/agenda-cultural)

#### 🔍 Preguntas
1. 49 discarded + 47 discovered pero 0 en cleansed/enriched — ¿el pipeline no ha corrido cleansing?
2. Las URLs discovered no parecen programas académicos (talleres de violín, banda, cine).
3. ¿Dónde están las páginas de carreras profesionales de UNMSM?
4. `production_enabled = false` — mismo patrón.

---

### B5. UTP (`utp`) — Pipeline inactivo

| Campo | Valor |
|---|---|
| **Website** | [https://www.utp.edu.pe/](https://www.utp.edu.pe/) |
| **Pipeline ready** | ❌ |
| **Production enabled** | ❌ |
| **Site type** | `traditional_ssr` |
| **Discovery mode** | `sitemap_bfs` |
| **Seed URLs** | 0 |

#### Pipeline Status
| Tabla | Estado |
|---|---|
| Staging raw | 221 skipped, 95 discarded, 10 discovered |
| Cleansed | 0 |
| Enriched | 0 |
| Courses | 0 |

#### URLs Discarded (ejemplos)
- [https://www.utp.edu.pe/web/ugo](https://www.utp.edu.pe/web/ugo)
- [http://www.utp.edu.pe/carreras-a-distancia/facultad-de-ingenieria/ingenieria-ambiental](http://www.utp.edu.pe/carreras-a-distancia/facultad-de-ingenieria/ingenieria-ambiental)
- [https://www.utp.edu.pe/web/node/219?page=1](https://www.utp.edu.pe/web/node/219?page=1)

#### 🔍 Preguntas
1. 95 descartadas — ¿los exclusion patterns están descartando páginas de carrera?
2. `carreras-a-distancia/facultad-de-ingenieria/ingenieria-ambiental` fue descartada pero parece una página de carrera válida.
3. 221 skipped — ¿por contenido duplicado o por content hash?
4. Pipeline inactivo — ¿plan para reactivar?

---

### B6. UPC — Pipeline activo con pocos resultados

*Ya cubierta en Sección A8 (1 curso publicado).*

**Datos adicionales de pipeline:**
- 57 discovered — ejemplos:
  - [https://www.upc.edu.pe/servicios/matricula/](https://www.upc.edu.pe/servicios/matricula/)
  - [https://www.upc.edu.pe/upc-internacional/ncuk/ncuk-university-options/](https://www.upc.edu.pe/upc-internacional/ncuk/ncuk-university-options/)
  - [https://www.upc.edu.pe/servicios/becas-creditos-y-cobranzas/sistema-de-pago-upc/](https://www.upc.edu.pe/servicios/becas-creditos-y-cobranzas/sistema-de-pago-upc/)

🔍 Las URLs discovered no son páginas de programa sino páginas institucionales — las exclusiones y seed URLs necesitan refinamiento.

---

### B7. UNI (`uni`) — Pipeline inactivo

| Campo | Valor |
|---|---|
| **Website** | [https://www.uni.edu.pe/](https://www.uni.edu.pe/) |
| **Pipeline ready** | ❌ |
| **Production enabled** | ❌ |
| **Site type** | `traditional_ssr` |
| **Discovery mode** | `sitemap_bfs` |

#### Pipeline Status
| Tabla | Estado |
|---|---|
| Staging raw | 1 discarded |
| Cleansed | 0 |
| Enriched | 0 |
| Courses | 0 |

🔍 Pipeline inactivo — sin actividad significativa.

---

## SECCIÓN C: INSTITUCIONES CON PERFIL PERO SIN DATOS EN PIPELINE

Las siguientes instituciones tienen perfil de scraping configurado (`pipeline_ready = true`) pero **cero actividad en staging_raw, cleansed_programs, enriched_programs, ni courses**:

| Institución | Slug | Website | Stealth | CF Bypass | Prod |
|---|---|---|---|---|---|
| Certus | `certus` | [certus.edu.pe](https://www.certus.edu.pe/) | No | No | ✅ |
| Cibertec | `cibertec` | [educacioncontinua.cibertec.edu.pe](https://educacioncontinua.cibertec.edu.pe/) | No | No | ✅ |
| Colectivo23 | `colectivo23` | [colectivo23.com](https://colectivo23.com/) | No | No | ✅ |
| Digital House | `digitalhouse` | [digitalhouse.com/pe](https://www.digitalhouse.com/pe) | ✅ | No | ✅ |
| EducaciónIT | `educacionit` | [educacionit.com](https://www.educacionit.com/) | ✅ | No | ✅ |
| New Horizons | `newhorizons` | [newhorizons.edu.pe](https://www.newhorizons.edu.pe/) | No | No | ✅ |
| PBS | `pbs` | [pbs.edu.pe](https://pbs.edu.pe/) | No | No | ✅ |
| Smart Data | `smartdata` | [smartdata.com.pe](https://smartdata.com.pe/) | No | No | ✅ |
| SoyHenry | `soyhenry` | [soyhenry.com](https://www.soyhenry.com/) | ✅ | No | ✅ |
| UTEC | `utec` | [posgrado.utec.edu.pe](https://posgrado.utec.edu.pe/) | No | No | ✅ |
| U. del Pacífico | `universidad-del-pacifico` | [up.edu.pe](https://www.up.edu.pe/) | No | No | ❌ |
| USIL | `usil` | [usil.edu.pe](https://www.usil.edu.pe/) | No | No | ✅ |

### Instituciones con `pipeline_ready = false`

| Institución | Slug | Website | Notas |
|---|---|---|---|
| UCAL | `ucal` | [ucal.edu.pe](https://www.ucal.edu.pe/) | Sin pipeline |
| WE Educación | `we-educacion` | [weedu.pe](https://weedu.pe/) | Sin pipeline |

#### 🔍 Preguntas para la Sección C
1. ¿Por qué estas 12 instituciones con `pipeline_ready = true` y `production_enabled = true` no tienen datos? ¿No se ha ejecutado el harvester?
2. ¿Todas tienen seed_urls adecuados? Verificar que apunten a páginas de programa reales.
3. ¿Las que requieren stealth/CF bypass tienen la configuración correcta de Playwright?
4. Priorizar: ¿cuáles de estas instituciones tienen la información más rica y accesible?

---

## SECCIÓN D: GUÍA DE REVISIÓN MANUAL

### Checklist por Institución

Para cada institución listada arriba, visita su sitio web y responde:

1. **Catálogo de programas:** ¿Existe una página que liste TODOS los programas? URL: ______
2. **Página individual de programa:** Al abrir un programa, ¿qué información está visible SIN login? — Ver [Leyenda de Pilares](#-leyenda-de-pilares)
   - [ ] (P1) Nombre del programa
   - [ ] (P4) Tipo (curso, carrera, diplomado, maestría, etc.)
   - [ ] (P5) Modalidad (presencial, virtual, semipresencial)
   - [ ] (P6) Duración (en meses, horas, créditos o ciclos)
   - [ ] (P7) Costo total (en PEN, USD o la moneda que sea)
   - [ ] (P12) Descripción del programa
   - [ ] (P8) Plan de estudios / malla curricular
   - [ ] (P9) Requisitos de admisión
   - [ ] (P13) ¿Requiere examen de admisión?
   - [ ] (P14) Horas/créditos académicos
   - [ ] (P3) Categoría / Área de estudio
   - [ ] Fecha de inicio
   - [ ] Perfil del egresado
3. **Formato de la información:** ¿Está en HTML estructurado (tablas, listas) o en texto libre?
4. **JavaScript necesario:** ¿La información se carga con JS (SPA) o está en el HTML inicial (SSR)?
5. **Anti-bot:** ¿Hay Cloudflare, CAPTCHA, o bloqueo por user-agent?
6. **Sitemap:** ¿Tiene sitemap.xml? ¿Lista todas las páginas de programa? URL: ______
7. **Paginación / Scroll infinito:** ¿El catálogo usa paginación? ¿Cuántas páginas?
8. **Precios:** ¿Están visibles públicamente o requieren login/contacto?
9. **URLs canónicas:** ¿Cada programa tiene una URL única y limpia? Ejemplo: ______
10. **Información faltante en nuestro pipeline:** Comparando lo que ves en el sitio vs nuestros datos en Supabase Pro, ¿qué pilares se podrían extraer que actualmente faltan?

### Prioridades de Acción

| Prioridad | Institución | Acción |
|---|---|---|
| 🔴 Crítica | UTP, UNMSM, UPC | Las URLs discovered no son programas — refinar exclusiones y agregar seed URLs correctos. |
| 🔴 Crítica | PUCP, SENATI, U. Continental | 44 cursos enriquecidos pero inactivos — investigar por qué sync_vector_worker no los activó. |
| 🟡 Alta | Certus, Cibertec, Digital House, etc. (12 inst.) | `production_enabled = true` pero cero datos — ¿no se ejecutó el harvester en Pro? |
| 🟡 Alta | IDAT | 63 cursos, perfil actualizado con section_keywords + field_defaults. 87% mock data (Cloudflare falló). price_status corregido. |
| 🟡 Alta | DMC | 44% mock data — mejorar calidad del scraping o prompt del LLM. |
| 🟢 Media | U. Lima | 159 URLs en "processing" — verificar que el pipeline no esté estancado. |
| 🟢 Media | CoderHouse | 0% precios — ver si los precios son visibles sin login. |

---

## Notas Finales

- **Datos mock (87% en IDAT post-FG2):** La mayoría de IDAT (55/63) usa mock porque Cloudflare LLM falló (timeout/JSON inválido) al re-ejecutar el enrichment. Los 8 registros Cloudflare exitosos tienen datos correctos. DeepSeek no está disponible (sin API key). Habilitar DeepSeek mejoraría la calidad significativamente.
- **Cursos enriquecidos pero inactivos:** PUCP (20), SENATI (14), U. Continental (10) tienen enriched synced pero courses is_active=false. Posible bug en `sync_vector_worker.py` o decisión de diseño (¿`production_enabled=false` los bloquea?).
- **Staging "processing" estancado:** PUCP (416), U. Lima (159), SENATI (169) tienen muchas URLs en estado "processing" — verificar que no haya workers zombie o locks no liberados.
- **Diferencia Free vs Pro:** En Free, PUCP/U. Lima pueden tener cursos activos. En Pro no. Si se espera paridad, verificar por qué.

---

*Reporte generado automáticamente desde Supabase Pro el 31 de mayo de 2026. Solo se usaron consultas SELECT.*
