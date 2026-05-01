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
El sistema opera mediante un flujo de datos atómico y resiliente, diseñado para la escalabilidad nacional y la evasión de bloqueos (Stealth):

1.  **FG1: Mapeo Institucional (Mensual)**: Descubrimiento y registro de nuevas semillas académicas licenciadas por MINEDU.
2.  **FG2: Cosecha Masiva y Saneamiento (Semanal)**: Extracción exhaustiva usando **TLS Impersonation (curl_cffi)** y limpieza de alta fidelidad para alimentar el cerebro de IA.
3.  **FG3: Integridad Diaria (Diario)**: Verificación automática de enlaces (404) con lógica de periodo de gracia de 3 días.

## 💻 Stack Tecnológico
- **Frontend**: Next.js 15+ (App Router), Tailwind CSS, Lucide React.
- **Backend**: Supabase (PostgreSQL 15, pgvector, PostgREST).
- **IA/ML**: Cloudflare Workers AI (Llama 3), GitHub Models (GPT-4o), Google Gemini 1.5 Flash.
- **Automation**: GitHub Actions (3 Independent Flows), Python 3.11 (curl_cffi, BeautifulSoup4, Playwright).

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
