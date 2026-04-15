# StudIAMatch - Tech Education Intelligence

StudIAMatch es la plataforma líder en **inteligencia educativa tecnológica** en Perú. Nuestra misión es democratizar el acceso a datos reales para que estudiantes y profesionales tomen decisiones basadas en **ROI (Retorno de Inversión)**, calidad curricular e impacto salarial, eliminando el sesgo institucional.

## 🚀 El Enfoque StudIAMatch
A diferencia de los buscadores de cursos tradicionales, StudIAMatch audita cada programa bajo una matriz rigurosa de **14 pilares de calidad**:
1.  **Transparencia de Inversión**: Costos claros y actualizados.
2.  **Impacto Salarial**: Vinculación con salarios reales del mercado peruano (Matriz 2026).
3.  **Cálculo de ROI**: Fórmula dinámica que estima el tiempo de recuperación de la inversión.
4.  **Calidad Curricular**: Auditoría de contenido técnico.
5.  **Social Proof**: Sistema de ratings y reviews verificado.
6.  **Nivel de Seniority**: Clasificación inteligente (Jr/Mid/Sr).
7.  ... (y otros 8 pilares estratégicos de auditoría).

## 🛠️ Arquitectura y "Golden Pipeline"
El sistema opera mediante un flujo de datos autónomo diseñado para la escalabilidad nacional:

1.  **Descubrimiento (The Explorer)**: Rastreo mensual de nuevas instituciones y programas.
2.  **Harvesting (The Collector)**: Scrapers especializados en Python (Playwright) para extracción masiva.
3.  **Enriquecimiento IA (The Brain)**: Integración con **Cloudflare Workers AI (Llama 3)** y **GitHub Models** para procesar los 14 pilares de forma autónoma.
4.  **Auditoría de Integridad**: Verificación diaria de enlaces (404) y coherencia taxonómica.
5.  **Visualización Premium**: Interfaz minimalista y compacta construida con Next.js 15+ y Turbopack.

## 💻 Stack Tecnológico
- **Frontend**: Next.js 15/16 (App Router), Tailwind CSS (Vanilla), Lucide React.
- **Backend**: Supabase (PostgreSQL, RLS, PostgREST).
- **IA/ML**: Cloudflare Workers AI, GitHub Models (GPT-4o mini / Llama 3).
- **Automation**: GitHub Actions (Golden Pipeline CI/CD), Python 3.11 (Playwright).

## 📦 Configuración Local

1.  **Requisitos**: Node.js 20+, Python 3.11+.
2.  **Instalación Frontend**:
    ```bash
    cd web
    npm install
    ```
3.  **Variables de Entorno** (`.env.local`):
    - `NEXT_PUBLIC_SUPABASE_URL`
    - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
    - `CLOUDFLARE_API_TOKEN` (para el Golden Pipeline)
4.  **Ejecutar Desarrollo**:
    ```bash
    npm run dev
    ```

## 🔄 Gobernanza de Ramas
- **`main`**: Código certificado para producción.
- **`certificacion`**: Entorno de validación y QA final.
- **`desarrollo`**: Rama activa para nuevas funcionalidades y experimentos de IA.

---
© 2026 StudIAMatch · Data-driven decisions for Tech Education.
