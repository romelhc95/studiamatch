# Guía de Despliegue: TIER 3 - Producción

Este documento describe el flujo de despliegue final para **StudIAMatch**.

## 1. Ficha Técnica del Ambiente
- **Rama Git**: `main`
- **Hosting**: Cloudflare Pages (Production)
- **URL**: [https://studiomatch.com/](https://studiomatch.com/)
- **Base de Datos**: **Supabase Pro** (Plan Escalable)

## 2. Flujo de Trabajo
1. El código solo llega aquí tras superar la certificación total.
2. Despliegue automático gestionado por Cloudflare Pages mediante el dominio integrado con Hostinger.
3. Actualización de Pipelines de ingestión diaria conectados al entorno Pro.

## 3. Configuración de Secretos (GitHub)
- `SUPABASE_URL` (Pro)
- `SUPABASE_SERVICE_ROLE_KEY` (Pro)
- `GEMINI_API_KEY` / `GH_MODELS_TOKEN`

## 4. Gatekeeper
- **Responsable**: `@orquestador-sdlc` / `@devops-engineer`
- **Criterio de Aprobación**: Backup verificado, SSL Full (Strict) activo y Cloudflare WAF configurado.

---
*Ultima actualización: 2026-04-15*
