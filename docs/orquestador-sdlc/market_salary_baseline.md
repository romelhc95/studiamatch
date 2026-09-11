# Reporte de Rangos Salariales - Perú (Abril 2026)

Este documento detalla la investigación de mercado realizada para establecer los rangos salariales base para las 17 categorías del catálogo de StudIAMatch AI. Estos datos sirven como fundamento para el cálculo dinámico del Retorno de Inversión (ROI) educativo.

## Resumen Ejecutivo
A Abril 2026, el mercado laboral peruano muestra una aceleración significativa en roles tecnológicos impulsados por la IA y la infraestructura cloud. Las carreras tradicionales mantienen un crecimiento estable, mientras que las especialidades técnicas experimentan una prima salarial por escasez de talento.

## Metodología de Estimación
*   **Junior (Min):** Salario inicial para profesionales con 0-2 años de experiencia, incluyendo beneficios de ley (Régimen General).
*   **Promedio (Avg):** Salario medio de mercado para profesionales con 3-5 años de experiencia (Nivel Mid).
*   **Ajuste 2026:** Se ha aplicado un factor de proyección basado en la inflación acumulada (3.5% anual) y un factor de demanda sectorial (2% a 15% según categoría).

## Rangos Salariales por Categoría (Soles - PEN)

| # | Categoría | Salario Junior (PEN) | Salario Promedio (PEN) | Tendencia |
|---|-----------|----------------------|------------------------|-----------|
| 1 | **Data Science & IA** | S/ 6,000 | S/ 14,000 | 🚀 Alta |
| 2 | **Cloud Computing** | S/ 5,200 | S/ 11,500 | 🚀 Alta |
| 3 | **DevOps & Infraestructura** | S/ 5,500 | S/ 12,500 | 🚀 Alta |
| 4 | **Ciberseguridad** | S/ 4,800 | S/ 10,500 | 🚀 Alta |
| 5 | **Desarrollo y Web** | S/ 4,500 | S/ 9,800 | 📈 Creciente |
| 6 | **Data Analytics** | S/ 4,200 | S/ 8,200 | 📈 Creciente |
| 7 | **Ingeniería y Construcción** | S/ 4,000 | S/ 9,000 | ➡️ Estable |
| 8 | **Gestión y Agilidad** | S/ 4,000 | S/ 8,800 | 📈 Creciente |
| 9 | **Finanzas y Legal** | S/ 3,500 | S/ 7,500 | ➡️ Estable |
| 10 | **Tecnología (General)** | S/ 3,800 | S/ 7,500 | 📈 Creciente |
| 11 | **Marketing y Ventas** | S/ 3,200 | S/ 6,800 | 📈 Creciente |
| 12 | **Derecho y Humanidades** | S/ 3,000 | S/ 6,200 | ➡️ Estable |
| 13 | **Logística y Operaciones** | S/ 2,800 | S/ 5,800 | ➡️ Estable |
| 14 | **Redes y Conectividad** | S/ 3,200 | S/ 6,500 | ➡️ Estable |
| 15 | **Arte y Diseño Digital** | S/ 3,000 | S/ 6,000 | ➡️ Estable |
| 16 | **Ofimática y Productividad** | S/ 1,800 | S/ 3,200 | ➡️ Estable |
| 17 | **General / Por Clasificar** | S/ 1,200 | S/ 2,800 | ➡️ Estable |

## Observaciones por Sector

### Tecnología e IA
El sector de IA presenta la mayor brecha salarial, con incrementos de hasta 15% anual en roles especializados. La capacidad de integrar IA generativa en procesos de negocio se ha convertido en un requisito estándar para bandas salariales superiores a S/ 8,000.

### Marketing y Negocios
El marketing de performance y el SEO avanzado han desplazado a los roles tradicionales de publicidad. La logística ha visto un repunte debido a la optimización de última milla y el comercio transfronterizo.

### Derecho y Humanidades
La especialización en derecho digital y compliance es el área de mayor crecimiento dentro de esta categoría, permitiendo a los profesionales superar el promedio de S/ 6,200.

## Implementación Técnica
Los datos han sido insertados en la tabla `market_salaries` mediante la migración `db/migrations/20260415_market_salaries.sql`. Estos valores deben ser consultados por el módulo de ROI para calcular el impacto económico de la formación en cada curso según su categoría principal.

---
*Última actualización: 15 de abril de 2026*
