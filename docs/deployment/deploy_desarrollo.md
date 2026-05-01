# Guía de Despliegue: TIER 1 - Desarrollo

Este documento describe el flujo de despliegue para el entorno de desarrollo de **StudIAMatch**.

## 1. Ficha Técnica del Ambiente
- **Rama Git**: `desarrollo`
- **Hosting**: Cloudflare Pages (Preview)
- **URL**: [https://studiamatch.pages.dev/](https://studiamatch.pages.dev/)
- **Base de Datos**: Supabase Free Project (ID: `fmcxwoqvxatbrawwtqke`)

## 2. Flujo de Trabajo
1. Los desarrollos se inician en ramas de `feature/*`.
2. Al realizar un commit en `desarrollo`, se dispara un build automático en Cloudflare Pages.
3. Este entorno (Tier 1) utiliza el proyecto de Supabase Free para aislar datos de experimentación.

## 3. Configuración de Visualización (Dashboard Cloudflare)
Para que la web de desarrollo (Preview) muestre los datos de Supabase de forma automática, configure estos campos exactos:
1. **Root Directory**: `/web`
2. **Build command**: `npm install && npm run build`
3. **Build output directory**: `out`
4. **Variables de Entorno (PREVIEW)**:
   - `NEXT_PUBLIC_SUPABASE_URL`: Su URL de Supabase Dev.
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`: Su Anon Key de Supabase Dev.

## 4. Secretos de Backend (GitHub Actions)
Configurados en el Environment `Development` de GitHub para el pipeline de IA:
- `SUPABASE_URL`: URL del proyecto Supabase.
- `SUPABASE_SERVICE_ROLE_KEY`: Permisos de edición para la IA.
- `CF_API_TOKEN` & `CF_ACCOUNT_ID`: Para el motor de Cloudflare AI.
- `GH_MODELS_TOKEN`: Para fallback multi-cloud.

## 5. Estrategia "Data Drip" (Enriquecimiento IA)
- **Ejecución**: Diaria vía GitHub Actions.
- **Cuota**: Limitada a 100 cursos/día para mantenerse en tier gratuito.
- **Calidad**: Filtro activo de >150 caracteres para descripción inicial.

## 6. Gatekeeper y Calidad
- **Responsable**: `@SDLC-Chief`
- **Métrica de Éxito**: Tasa de enriquecimiento > 90% y auditoría de integridad (`quality_assurance_audit.py`) sin fallos críticos.

---
*Ultima actualización: 2026-04-16 (Fase 31.5 - Estabilización Visual Completa)*
