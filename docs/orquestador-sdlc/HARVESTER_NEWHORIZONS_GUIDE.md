# Documentación Técnica: Extracción de New Horizons Perú

**Fecha de Última Actualización**: 2026-04-10
**Módulo**: `scripts/newhorizons_harvester.py`
**Responsable**: Especialista en Automatización / Orquestador SDLC

## 1. Descripción General
Este componente automatiza la ingesta de programas educativos desde New Horizons Perú hacia la base de datos de StudIAMatch.ai. Está diseñado para ser resiliente a cambios en el DOM y para escalar horizontalmente a medida que la institución añade nuevos cursos.

## 2. Arquitectura de Extracción

### A. Capa de Descubrimiento (Discovery)
El script utiliza Playwright para navegar al catálogo completo:
- **URL Semilla**: `https://www.newhorizons.edu.pe/cursos-y-certificaciones-internacionales/ver-todas-las-especialidades`
- **Lógica**: Extrae todas las URLs que coinciden con el patrón `/cursos-y-certificaciones-internacionales/` y filtra enlaces administrativos o estáticos.
- **Detección de Nuevos Cursos**: Al ejecutarse, compara las URLs descubiertas contra los registros existentes en Supabase (basado en el campo `slug` o `url`).

### B. Capa de Extracción Semántica (Deep Scraping)
Para cada curso, se extraen 6 bloques de información crítica utilizando **anclajes semánticos de texto**:

| Bloque | Anclaje de Texto (Header) | Estrategia |
| :--- | :--- | :--- |
| **¿Sobre qué trata?** | "Presentación" | Captura el hermano siguiente (`nextElementSibling`) en el DOM. |
| **Objetivos** | "Objetivos de aprendizaje" | Extrae el contenido textual de la lista siguiente. |
| **Público Objetivo** | "¿A quién está dirigido?" | Captura el párrafo descriptivo siguiente. |
| **Requisitos** | "Requisitos" | Captura los prerrequisitos técnicos o académicos. |
| **Precio** | N/A | Se establece en `0` con estatus `consultar` por falta de transparencia pública en el sitio. |

## 3. Persistencia (API REST)
Para evitar problemas de conectividad con proxies o drivers de PostgreSQL directos, el harvester utiliza la **REST API de Supabase**:
1. **Validación de Institución**: Verifica si "New Horizons Perú" existe, de lo contrario la crea.
2. **UPSERT**: Utiliza la cabecera `Prefer: resolution=merge-duplicates` para actualizar registros existentes o insertar nuevos sin duplicar.

## 4. Automatización (Cronjob)
Se ha configurado un script de Windows (`scripts/run_harvesters_weekly.bat`) que puede ser programado en el **Programador de Tareas de Windows** para ejecutarse semanalmente.

## 5. Mantenimiento y Alertas
- **Logs**: Se generan logs detallados en `harvester_log.txt`.
- **Fallos comunes**: Si New Horizons cambia el nombre de los encabezados (p.ej. de "Presentación" a "Intro"), se debe actualizar el diccionario `sections` en el script.

---
*StudIAMatch.ai Engineering Team*
