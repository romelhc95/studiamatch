# Reporte Técnico de Escalamiento: StudIAMatch.ai (v2.2)

**Estado**: Ingeniería de Alta Disponibilidad  
**Benchmark**: Basado en **New Horizons Perú** (~86 registros en 8 min).

---

## 1. Eficiencia de Procesamiento (Análisis Comparativo)
El análisis de tiempos se proyecta a partir de los datos reales obtenidos de New Horizons:

-   **Base de Datos**: 1 institución = 8 minutos de procesamiento promedio.
-   **Escala 100 Inst. (Secuencial)**: 800 min (~13.3 horas).
-   **Escala 100 Inst. (Paralelo - 5 Workers)**: **2.6 horas**.
    -   *Efecto*: Reducción masiva de latencia de datos.

---

## 2. Impacto de Seguridad Anti-Bot (Holgura)
**¿Qué pasa si encontramos 10 instituciones con captchas agresivos?**
-   **Tiempo de Resolución**: Un captcha de imagen tarda entre 30 y 45 segundos en resolverse vía API.
-   **Impacto Total**: 10 instituciones x 45 seg = **+7.5 minutos** adicionales en toda la carga.
-   **Veredicto**: El impacto en la "ventana de entrega" del domingo por la mañana es **despreciable** (menos del 5% del tiempo total). El sistema sigue siendo ultra-eficiente.

---

## 3. Matriz de Servicios y Seguridad
Esta arquitectura garantiza que cada dólar invertido aporte seguridad:

| Servicio | Componente Técnico | Seguridad Aplicada |
| :--- | :--- | :--- |
| **Supabase** | PostgreSQL + Auth + Storage | **RLS** (Seguridad a nivel de fila) + **Backups**. |
| **Vercel** | Next.js Engine + Edge Runtime | **WAF** (Firewall web) + **DDoS Protection**. |
| **Automation** | GitHub Actions YAML | **Secrets Injection** (Tus llaves nunca se ven). |

---

## 4. Optimización Semántica (Implementación Inmediata)
Instalaremos `pg_trgm` en esta fase para habilitar:
-   **Fuzzy Search**: Búsqueda por similitud (ej. si el usuario busca "Excel 360", sale "Excel 365").
-   **Indexación Proactiva**: Creación de índices sobre nombres de cursos para asegurar respuestas <100ms.

---

**Plan de Infraestructura validado.** Con estas precisiones sobre el benchmark de New Horizons y la holgura de los captchas, el sistema está listo para la ejecución técnica.
