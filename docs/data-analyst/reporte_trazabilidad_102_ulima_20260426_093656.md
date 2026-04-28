# Reporte de Trazabilidad: 102 URLs Universidad de Lima

**Fecha:** 2026-04-26 09:36:56
**Objetivo:** Auditar el estado de los 102 programas prioritarios de U. Lima en el pipeline de StudIAMatch.

## 1. Resumen Ejecutivo (Conteo por Estado)

| Estado | Cantidad | Descripción |
| :--- | :--- | :--- |
| Verified Course | 14 | Llegaron al final con éxito |
| Course (Unverified) | 2 | Sincronizados pero requieren verificación |
| Enriched (No Sync) | 1 | Procesados por IA pero no sincronizados |
| Cleansed (No Enrich) | 14 | Pasaron limpieza, fallaron enriquecimiento |
| Staging (Pending) | 0 | En cola de descarga |
| Staging (Discovered) | 0 | **BLOQUEADOS:** Detectados pero no descargados |
| Staging (Discarded) | 70 | **DESCARTADOS:** Filtrados por reglas de ruido |
| Not in System | 0 | El harvester nunca los encontró |

## 2. Análisis por Categoría

### Pregrado (12)
| URL | Estado Actual | Bloqueo Detectado |
| :--- | :--- | :--- |
| https://www.ulima.edu.pe/pregrado/administracion | Staging (Discarded) | Discarded: name_too_short |
| https://www.ulima.edu.pe/pregrado/comunicacion | Staging (Discarded) | Discarded: name_too_short |
| https://www.ulima.edu.pe/pregrado/derecho | Staging (Discarded) | Discarded: name_too_short |
| https://www.ulima.edu.pe/pregrado/ingenieria-ambiental | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/pregrado/ingenieria-industrial | Staging (Discarded) | Discarded: name_too_short |
| https://www.ulima.edu.pe/pregrado/ingenieria-de-sistemas | Staging (Discarded) | Discarded: name_too_short |
| https://www.ulima.edu.pe/pregrado/arquitectura | Staging (Discarded) | Discarded: name_too_short |
| https://www.ulima.edu.pe/pregrado/contabilidad-y-finanzas | Staging (Discarded) | Discarded: name_too_short |
| https://www.ulima.edu.pe/pregrado/economia | Staging (Discarded) | Discarded: name_too_short |
| https://www.ulima.edu.pe/pregrado/ingenieria-civil | Staging (Discarded) | Discarded: name_too_short |
| https://www.ulima.edu.pe/pregrado/ingenieria-mecatronica | Staging (Discarded) | Discarded: name_too_short |
| https://www.ulima.edu.pe/pregrado/marketing | Staging (Discarded) | Discarded: name_too_short |

### Maestria (14)
| URL | Estado Actual | Bloqueo Detectado |
| :--- | :--- | :--- |
| https://www.ulima.edu.pe/posgrado/maestria/macp | Course (Unverified) | Waiting for manual verification or sync flag |
| https://www.ulima.edu.pe/posgrado/maestria/mbf | Cleansed (Not Enriched) | Enrichment failure or AI filter |
| https://www.ulima.edu.pe/posgrado/maestria/mcdn | Cleansed (Not Enriched) | Enrichment failure or AI filter |
| https://www.ulima.edu.pe/posgrado/maestria/mcgc | Cleansed (Not Enriched) | Enrichment failure or AI filter |
| https://www.ulima.edu.pe/posgrado/maestria/mde | Verified Course | N/A |
| https://www.ulima.edu.pe/posgrado/maestria/mdop | Cleansed (Not Enriched) | Enrichment failure or AI filter |
| https://www.ulima.edu.pe/posgrado/maestria/mdie | Cleansed (Not Enriched) | Enrichment failure or AI filter |
| https://www.ulima.edu.pe/posgrado/maestria/mgi | Cleansed (Not Enriched) | Enrichment failure or AI filter |
| https://www.ulima.edu.pe/posgrado/maestria/mgc | Cleansed (Not Enriched) | Enrichment failure or AI filter |
| https://www.ulima.edu.pe/posgrado/maestria/mid | Cleansed (Not Enriched) | Enrichment failure or AI filter |
| https://www.ulima.edu.pe/posgrado/maestria/mlp | Cleansed (Not Enriched) | Enrichment failure or AI filter |
| https://www.ulima.edu.pe/posgrado/maestria/mmgc | Course (Unverified) | Waiting for manual verification or sync flag |
| https://www.ulima.edu.pe/posgrado/maestria/mtpf | Cleansed (Not Enriched) | Enrichment failure or AI filter |
| https://www.ulima.edu.pe/posgrado/maestria/mba | Cleansed (Not Enriched) | Enrichment failure or AI filter |

### Doctorado (3)
| URL | Estado Actual | Bloqueo Detectado |
| :--- | :--- | :--- |
| https://www.ulima.edu.pe/posgrado/doctorado/da | Cleansed (Not Enriched) | Enrichment failure or AI filter |
| https://www.ulima.edu.pe/posgrado/doctorado/dc | Cleansed (Not Enriched) | Enrichment failure or AI filter |
| https://www.ulima.edu.pe/posgrado/doctorado/dge | Cleansed (Not Enriched) | Enrichment failure or AI filter |

### Idiomas (7)
| URL | Estado Actual | Bloqueo Detectado |
| :--- | :--- | :--- |
| https://www.ulima.edu.pe/idiomas/programa-integral-ingles | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/idiomas/english-business | Staging (Discarded) | Discarded: name_too_short |
| https://www.ulima.edu.pe/idiomas/english-media | Staging (Discarded) | Discarded: name_too_short |
| https://www.ulima.edu.pe/idiomas/english-engineering | Staging (Discarded) | Discarded: name_too_short |
| https://www.ulima.edu.pe/idiomas/extension-workshops | Staging (Discarded) | Discarded: name_too_short |
| https://www.ulima.edu.pe/idiomas/intensive-graduation | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/idiomas/b2-first | Staging (Discarded) | Discarded: name_too_short |

### Cursos/Talleres (65)
| URL | Estado Actual | Bloqueo Detectado |
| :--- | :--- | :--- |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-comunicacion-marketing-politico | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-cultura-organizacional | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/vir-presentaciones-alto-impacto | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-alto-impacto-presentaciones | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-arbitraje | Verified Course | N/A |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-app | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-corporate-compliance | Verified Course | N/A |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-legaltech-ia-abogados | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-ley-contrataciones-estado | Verified Course | N/A |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/vir-obras-impuesto | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-obras-publicas | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/vir-resolucion-conflictos | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-gestion-compensacion-total | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-people-analytics | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-domina-tiempo | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-expresate-lidera | Verified Course | N/A |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-power-skills | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-soft-skills | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-liderazgo-alto-desempeno | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-analisis-fundamental | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-analisis-tecnico | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-elaboracion-presupuestos | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-finanzas-no-especialistas | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-gestion-tesoreria | Verified Course | N/A |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-gestion-riesgo-compliance | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-impuesto-renta | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-control-interno | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-niif | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-inversion-bolsa | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-python-aplicado-finanzas | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-fraude-auditoria-forense | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-bloomberg | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-construccion | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-marca-ia | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-growth-hacking | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-ia-marketing-digital | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-kam | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-negociacion-comercial | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/vir-marketing-digital | Verified Course | N/A |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-retail-category-management | Verified Course | N/A |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-social-media | Verified Course | N/A |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-ia-creadores-contenido | Enriched (Not in Courses) | Sync error or filter in course creation |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-metodologias-agiles | Verified Course | N/A |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-direccion-supply-chain | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-gestion-proyectos | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/vir-mejora-rediseno-procesos | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-planeamiento-estrategico | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/vir-seguridad-salud-trabajo | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-future-thinking | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-arquitectura-soluciones-digitales | Verified Course | N/A |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-business-analytics | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-data-analytics | Verified Course | N/A |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-visualizacion-datos-power-bi | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-power-bi | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-excel | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-gobierno-datos | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-ia-generativa-negocios | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-modernizacion-aplicaciones | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-power-bi-desde-cero | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-transformacion-digital | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-fundamentos-power-bi | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-ia-contenido-textual | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-talent-shift | Verified Course | N/A |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-transformacion-digital | Staging (Discarded) | Discarded: description_too_short |
| https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-sql-decisiones-negocio | Verified Course | N/A |

## 3. Identificación de Bloqueos Críticos

1. **Discovery Gap:** Las URLs de Pregrado e Idiomas no están siendo encontradas por el `UniversalHarvester` debido a filtros restrictivos en las keywords de descubrimiento.
2. **Discovered Deadlock:** Muchos registros de Maestría están en estado `discovered` pero el harvester los salta en ejecuciones posteriores porque 'ya existen' en la DB.
3. **Discard Reason Audit:**
   - `description_too_short`: 126 registros.
   - `hard_db_exclusion:/blog/`: 25 registros.
   - `name_too_short`: 193 registros.
   - `hard_db_exclusion:/noticias/`: 120 registros.
   - `hard_db_exclusion:/registro-exitoso`: 2 registros.
   - `hard_db_exclusion:/gabinete-psicometrico/`: 244 registros.
   - `hard_db_exclusion:/news/`: 23 registros.
   - `is_hub_page`: 4 registros.
   - `hard_db_exclusion:/mooc/`: 2 registros.
   - `hard_db_exclusion:/agenda/`: 1 registros.
   - `hard_db_exclusion:/open-registro`: 2 registros.
   - `hard_db_exclusion:/publicaciones/`: 1 registros.

## 4. Recomendaciones para 'Empujar' el Catálogo

1. **Reset Masivo:** Cambiar el estado de todos los registros `discovered` de U. Lima a `pending` para forzar su scraping.
2. **Inyección de Semillas:** Inyectar manualmente las URLs de Pregrado que faltan como `pending` para bypassear el filtro de keywords del buscador automático.
3. **Ajuste de Reglas de Ruido:** Revisar si la regla `hard_db_exclusion:/noticias/` es demasiado agresiva y está capturando páginas de carrera.
4. **Forzar Enriquecimiento:** Ejecutar el `enrichment_worker.py` específicamente para la institución `ccd04100-1bde-427b-b94f-ab24ae233a2a`.
