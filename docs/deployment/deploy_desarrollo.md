# Guía de Despliegue: TIER 1 - Desarrollo

Este documento describe el flujo de despliegue para el entorno de desarrollo de **StudIAMatch**.

## 1. Ficha Técnica del Ambiente
- **Rama Git**: `desarrollo`
- **Hosting**: Cloudflare Pages (Preview)
- **URL**: [https://studiamatch.pages.dev/](https://studiamatch.pages.dev/)
- **Base de Datos**: Supabase Free Project (ID: `fmcxwoqvxatbrawwtqke`)

## 2. Flujo de Trabajo
1. Los desarrollos se inician en ramas de `feature/*`.
2. Al realizar un commit en `desarrollo`, Cloudflare Pages dispara un despliegue automático.
3. El entorno utiliza variables de desarrollo (Free) para no afectar datos productivos.

## 3. Configuración de Secretos (GitHub)
Los secretos están configurados en el GitHub Environment `Development`:
- `SUPABASE_URL`: URL del proyecto Supabase Free.
- `SUPABASE_SERVICE_ROLE_KEY`: Llave maestra para actualizaciones de backend (IA).
- `SUPABASE_KEY`: Llave pública (Anon).
- `CF_API_TOKEN`: Token para Cloudflare Workers AI.
- `CF_ACCOUNT_ID`: ID de cuenta de Cloudflare.
- `GH_MODELS_TOKEN` (Opcional): Para fallback a GitHub Models.

## 4. Estrategia "Data Drip" (Enriquecimiento)
El ambiente de desarrollo ejecuta un proceso de IA gratuito cada noche:
- **Modelo**: `llama-3-8b-instruct` (Cloudflare).
- **Límite**: 50-100 cursos/día.
- **Cuota**: Se mantiene bajo las 10,000 neuronas gratuitas diarias de Cloudflare.
- **Calidad**: Solo procesa cursos con >150 caracteres en descripción.

## 5. Gatekeeper
- **Responsable**: `@SDLC-Chief`
- **Criterio de Aprobación**: Batch de enriquecimiento con Éxitos > 90% y Build de Cloudflare exitoso.

---
*Ultima actualización: 2026-04-15 (Estabilización Tier 1 completada)*
