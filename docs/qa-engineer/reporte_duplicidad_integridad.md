# Informe de Unicidad e Integridad - Phase 29

## 1. Análisis de Unicidad (Caminos de Ruta)
- **Total de registros en DB:** 217
- **Cursos únicos renderizados:** 208
- **Registros filtrados (Duplicados técnicos):** 9
- **Criterio de De-duplicación:** `(institution_id, source_url)`. Se prioriza 'Programa' sobre 'Curso'.

### Ejemplos de Duplicados Identificados y Filtrados
- `Creación de contenido en Tik Tok` (Programa) - URL: https://www.idat.edu.pe/cursos-de-formacion-continua/creacion-de-contenido-en-tik-tok
- `Diseño en Autocad` (Programa) - URL: https://www.idat.edu.pe/cursos-de-formacion-continua/diseno-en-autocad
- `Seguridad Informática y Ciberseguridad` (Curso) - URL: https://www.idat.edu.pe/programas-especializacion/seguridad-informatica-y-ciberseguridad
- `Data Analytics I` (Programa) - URL: https://www.idat.edu.pe/cursos-de-formacion-continua/data-analytics-i
- `Microsoft Power Bi Avanzado` (Curso) - URL: https://www.idat.edu.pe/cursos-de-formacion-continua/power-bi-avanzado

## 2. Auditoría de Integridad (URLs Vivas)
Se ha verificado la navegación dinámica hacia el detalle de los cursos para asegurar que el ruteo `/[institution]/[slug]` resuelve correctamente.

| Curso | URL Local | Estado |
| :--- | :--- | :--- |
| Gestión Avanzada de Compras | [http://localhost:3000/courses/pucp/especializacion-gestion-avanzada-compras](http://localhost:3000/courses/pucp/especializacion-gestion-avanzada-compras) | ✅ ALIVE |
| Creación de contenido en Tik Tok | [http://localhost:3000/courses/idat/creacion-de-contenido-en-tik-tok](http://localhost:3000/courses/idat/creacion-de-contenido-en-tik-tok) | ✅ ALIVE |
| PECB - ISO 27001 Information Security Management Systems | [http://localhost:3000/courses/new-horizons-peru/pecb-iso-27001-information-security-management-systems](http://localhost:3000/courses/new-horizons-peru/pecb-iso-27001-information-security-management-systems) | ✅ ALIVE |
| Scrum Product Owner Certified (SPOC) | [http://localhost:3000/courses/new-horizons-peru/scrum-product-owner-certified](http://localhost:3000/courses/new-horizons-peru/scrum-product-owner-certified) | ✅ ALIVE |
| Diseño Instruccional y Gestión de Experiencias de Aprendizaje | [http://localhost:3000/courses/pucp/diseno-instruccional-gestion-experiencias-aprendizaje](http://localhost:3000/courses/pucp/diseno-instruccional-gestion-experiencias-aprendizaje) | ✅ ALIVE |
| Gestión de Recursos Humanos 3.0 | [http://localhost:3000/courses/pucp/especializacion-gestion-recursos-humanos-3-0](http://localhost:3000/courses/pucp/especializacion-gestion-recursos-humanos-3-0) | ✅ ALIVE |
| Gestión de Operaciones Mineras | [http://localhost:3000/courses/pucp/especializacion-gestion-operaciones-mineras](http://localhost:3000/courses/pucp/especializacion-gestion-operaciones-mineras) | ✅ ALIVE |
| Inteligencia Artificial Aplicada a las Finanzas | [http://localhost:3000/courses/pucp/inteligencia-artificial-aplicada-finanzas](http://localhost:3000/courses/pucp/inteligencia-artificial-aplicada-finanzas) | ✅ ALIVE |
| Data Analytics | [http://localhost:3000/courses/idat/data-analytics-i](http://localhost:3000/courses/idat/data-analytics-i) | ✅ ALIVE |
| Creciendo en Escena (9 a 12 años) | [http://localhost:3000/courses/pucp/creciendo-escena](http://localhost:3000/courses/pucp/creciendo-escena) | ✅ ALIVE |
| IA Aplicada a la Logística | [http://localhost:3000/courses/pucp/ia-aplicada-logistica](http://localhost:3000/courses/pucp/ia-aplicada-logistica) | ✅ ALIVE |
| AI - 900T00 - A: Microsoft Azure AI Fundamentals | [http://localhost:3000/courses/new-horizons-peru/az-900-con-ia-microsoft-azure](http://localhost:3000/courses/new-horizons-peru/az-900-con-ia-microsoft-azure) | ✅ ALIVE |
| Teatro I: Introducción a la Actuación | [http://localhost:3000/courses/pucp/teatro-introduccion-a-la-actuacion](http://localhost:3000/courses/pucp/teatro-introduccion-a-la-actuacion) | ✅ ALIVE |
| Business Process Management(BPM) & Robotic Process Automation (RPA) | [http://localhost:3000/courses/new-horizons-peru/business-process-management-bpm](http://localhost:3000/courses/new-horizons-peru/business-process-management-bpm) | ✅ ALIVE |
| AZ - 305T00: Diseño de Soluciones de Infraestructura de Microsoft Azure | [http://localhost:3000/courses/new-horizons-peru/az-305t00-diseno-de-soluciones-de-infraestructura-de-microsoft-azure](http://localhost:3000/courses/new-horizons-peru/az-305t00-diseno-de-soluciones-de-infraestructura-de-microsoft-azure) | ✅ ALIVE |


---
*Reporte generado automáticamente por Antigravity QA Engine.*