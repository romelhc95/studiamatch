# Plan de Inversión y Estrategia: StudIAMatch.ai (v2.2)

---

## 1. Cronograma de Automatización (3 Niveles)
Para asegurar que la web sea la fuente más confiable de educación en Perú:

| Nivel | Frecuencia | Objetivo |
| :--- | :--- | :--- |
| **L1: Descubrimiento** | Mensual | Mapear nuevas universidades licenciadas por MINEDU. |
| **L2: Carga Maestra** | Domingos 2 AM | Ejecución masiva en paralelo para traer el lote completo de cursos. |
| **L3: Escaneo Diario**| Diario 2 AM | Validación de enlaces (404) y activación de "Periodo de Gracia". |

---

## 2. Desglose detallado de Servicios (¿Qué estás pagando?)

### A. Supabase Pro ($25/mes)
Es el "Cerebro" del proyecto. No es solo una base de datos:
-   **Base de Datos (Postgres)**: Donde se guardan los 10,000+ cursos.
-   **Autenticación**: Gestión de usuarios, login con Google y registro seguro.
-   **Almacenamiento (Storage)**: Para guardar los folletos (PDF) e imágenes de los cursos.
-   **Backups**: Copia de seguridad automática diaria para que nunca pierdas tu historial.

### B. Vercel Pro ($20/mes)
Es el "Cuerpo" y la "Voz" del proyecto:
-   **Alojamiento Web**: Donde vive la cara visible de StudIAMatch.ai.
-   **Infraestructura de Búsqueda**: Hace que los filtros y buscadores sean veloces.
-   **Dominio y Seguridad**: Mantiene el candado de seguridad (SSL) y conecta tu dominio .ai.

---

## 3. Cuadro Final de Costos Proyectado (Actualizado)

| Concepto | Inversión Inicial (S/.) | Cantidad Incluida | Mensual Recurrente (S/.) |
| :--- | :--- | :--- | :--- |
| **Dominio .ai** | S/. 608.00 | 2 años de propiedad. | -- |
| **Supabase Pro** | S/. 95.00 | DB + Auth + Storage. | S/. 95.00 |
| **Vercel Pro** | S/. 76.00 | Web + API + Filtros. | S/. 76.00 |
| **Captcha Balance** | S/. 38.00 | **~3,300 captchas** | Según uso (S/. 0 - S/. 10) |
| **TOTAL ESTIMADO** | **S/. 817.00** | | **S/. 171.00** |

---

> [!NOTE]
> Nota sobre Captchas: Los S/. 38.00 ($10 USD) alcanzan para resolver aproximadamente **3,300 retos de robot**, suficiente para operar varios meses si solo 10-20 instituciones usan protección agresiva.
