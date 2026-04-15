# StudIAMatch - Tech Education Intelligence

StudIAMatch es una plataforma premium diseñada para auditar y comparar la oferta educativa tecnológica en Perú, permitiendo a los usuarios tomar decisiones basadas en ROI, calidad curricular e impacto salarial.

## 🚀 Estado del Proyecto: Fase 8.1 Certificada
El sistema ha alcanzado su madurez visual y funcional con la implementación del **Rediseño Premium Retráctil**.

### Novedades de la Fase 8.1
- **UX Inmersiva**: Catálogo de 3 columnas que se expande al 100% del ancho para una visualización cinematográfica.
- **Filtros Inteligentes**: Sidebar retráctil dinámico que permite filtrar por Verticales IT (Ciberseguridad, AI, Cloud), Institución y Rango de Precios sin sacrificar espacio.
- **Branding Premium**: Cada tarjeta de curso destaca ahora la institución de origen con un lenguaje visual elegante y badges de alta visibilidad.
- **Data Integrada**: Motor de búsqueda y filtrado 100% calibrado para detectar instituciones como "New Horizons", eliminando bugs de visibilidad de datos.
- **Arquitectura**: Next.js 16 con Turbopack y Supabase REST API (Join de datos en tiempo real en frontend).

## 🛠️ Stack Tecnológico
- **Frontend**: Next.js 16 (App Router), Tailwind CSS, Lucide Icons.
- **Backend**: Supabase (PostgreSQL + REST API).
- **Ingeniería**: Harvesters automáticos en Python (Playwright) para New Horizons y otras instituciones.

## 📦 Instalación y Ejecución

1. **Clonar y configurar**:
   ```bash
   cd web
   npm install
   ```

2. **Variables de Entorno**:
   Configurar `.env.local` con `NEXT_PUBLIC_SUPABASE_URL` y `NEXT_PUBLIC_SUPABASE_ANON_KEY`.

3. **Ejecutar**:
   ```bash
   npm run dev
   ```

## 📊 Módulos de Datos
- **Harvester New Horizons**: Script automatizado en `scripts/newhorizons_harvester.py` que extrae y sincroniza cursos mensualmente.
- **Filtros Verticales**: Categorización automática basada en palabras clave para Ciberseguridad, AI & Data Science, Cloud Computing y Desarrollo.

---
© 2026 StudIAMatch - Auditoría Educativa Tech

