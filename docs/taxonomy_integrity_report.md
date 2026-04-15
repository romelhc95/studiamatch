# Informe de Integridad Taxonómica - StudIAMatch.ai

## 1. Cursos en 'General / Por Clasificar'
Se han identificado **28 cursos** que aún permanecen en la categoría 'General / Por Clasificar'. La mayoría de estos cursos pertenecen a la **PUCP** (23) y a **New Horizons** (5).

### Listado de Cursos sin Clasificar:
- **Aventura Teens: Mentes que Innovan** (PUCP)
- **Diplomatura de Estudio Empresarial en Métodos Ágiles e Innovación** (PUCP)
- **Automatización Robótica de Procesos (RPA) con Power Automate** (New Horizons)
- **OKR Certified Professional** (New Horizons)
- **Diseño e Implementación de Programas de Compliance Corporativo** (PUCP)
- **Diplomatura de Instrumentos Financieros: Valorización y Tratamiento Contable** (PUCP)
- **Gerencia Estratégica de Tecnologías de la Información** (PUCP)
- **Diplomatura en Dirección de Innovación, Agilidad y Transformación Digital** (PUCP)
- **Introducción al Sistema Interamericano de Derechos Humanos** (PUCP)
- **Aislamiento Sísmico de Edificios según la Norma Técnica E.031** (PUCP)
- **Planeamiento Estratégico** (PUCP)
- **Habilidades Blandas para el Acompañamiento de Dispute Boards** (PUCP)
- **Creación en Stop Motion** (PUCP)
- **Justicia en Salud, Bioética y Derecho** (PUCP)
- **Marketing y Patrocinio Deportivo** (PUCP)
- **Fundamentos del Diseño de Juegos de Mesa** (PUCP)
- **Growth Marketing & Automation** (PUCP)
- **Windows Server Hybrid: AZ - 800T00 y AZ - 801T00** (New Horizons)
- **Escultura y Modelado 3D en Blender** (PUCP)
- **COBIT 2019** (New Horizons)
- **Spray Lab Intermedio: Técnicas de Aerosol** (PUCP)
- **Diplomatura de Estudio en Dirección de Ventas** (PUCP)
- **Estrategias para la Enseñanza de Problemas en Matemáticas** (PUCP)
- **Junta de Prevención y Resolución de Disputas en el Sector Construcción** (PUCP)
- **Diplomatura de Normas Internacionales de Información Financiera** (PUCP)
- **Tributación Empresarial: IGV y Renta** (PUCP)
- **Formulación y Evaluación de Proyectos de Centrales Hidroeléctricas** (PUCP)
- **SQL Server 2025** (New Horizons)

## 2. Categorías Fantasma (0 Cursos)
- **Tecnología**: Esta categoría no tiene cursos asociados actualmente. Esto ocurre porque el motor de reglas clasifica los cursos técnicos en categorías más granulares (Cloud, DevOps, Ciberseguridad).

## 3. Propuestas de Remediación

### A. Nuevas Categorías Recomendadas
Debido a la diversidad de los cursos sin clasificar, se recomienda crear las siguientes dimensiones de negocio:
1. **Finanzas y Legal**: Para cursos como Tributación, NIIF, Compliance e Instrumentos Financieros.
2. **Ingeniería y Construcción**: Para cursos como Aislamiento Sísmico, Centrales Hidroeléctricas y Juntas de Resolución de Disputas.
3. **Arte y Diseño Digital**: Para cursos como Blender, Stop Motion, Escultura y Spray Lab.
4. **Derecho y Humanidades**: Para cursos como Bioética, Derechos Humanos y Justicia en Salud.
5. **Marketing y Ventas**: Para cursos como Growth Marketing, Marketing Deportivo y Dirección de Ventas.

### B. Nuevas Reglas de Clasificación (Category Rules)
Para reducir el número de cursos en 'General', se deben agregar las siguientes reglas al motor de IA:

| Palabra Clave | Nueva Categoría Destino | Prioridad |
|---------------|-------------------------|-----------|
| "Agilidad" / "Agiles" / "OKR" | Gestión y Agilidad | 8 |
| "SQL Server" | Data Science & IA | 7 |
| "Windows Server" | Cloud Computing | 7 |
| "Power Automate" / "RPA" | Ofimática y Productividad | 6 |
| "Tributación" / "Contable" | Finanzas y Legal | 5 |
| "Símico" / "Hidroeléctrica" | Ingeniería y Construcción | 5 |

### C. Acción sobre 'Tecnología'
**Recomendación**: Mantenerla como "Categoría de Respaldo" (Fallback) en lugar de eliminarla. Sin embargo, para que deje de estar vacía, se puede reconfigurar como categoría padre de "Desarrollo" y "Redes" en el futuro, o usarla para cursos técnicos transversales como "Gerencia de TI".

## 4. Conclusión
La salud taxonómica es **buena (84% clasificado)**. Los cursos sin clasificar representan una oportunidad para expandir la oferta de StudIAMatch.ai más allá del nicho puramente tecnológico, capturando la oferta de Instituciones como la PUCP que es más generalista.
