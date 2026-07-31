# Guía de Despliegue: TIER 3 - Producción

Este documento describe el flujo de despliegue final para **StudIAMatch**.

> Estado vigente: LEGACY_BLOQUEADO_NO_EJECUTAR. Produccion, Pro, `main`, Cloudflare manual y pipelines Pro permanecen bloqueados hasta que F9 cierre en `free_certified` y F10 tenga autorizaciones separadas.

## 1. Ficha Técnica del Ambiente
- **Rama Git**: `main`
- **Hosting**: Cloudflare Pages (Production)
- **URL**: [https://studiomatch.com/](https://studiomatch.com/)
- **Base de Datos**: **Supabase Pro** (Plan Escalable)

## 2. Flujo de Trabajo
1. No llega codigo aqui mientras `certificacion`/`main` sigan bloqueadas por el flujo vigente.
2. No se ejecuta despliegue Cloudflare manual o automatico desde este documento.
3. No se conectan pipelines diarios al entorno Pro hasta F10 autorizada.

## 3. Configuración de Secretos (GitHub)
No configurar, copiar ni rotar secretos de produccion desde este documento.

- `SUPABASE_URL` (Pro)
- `SUPABASE_SERVICE_ROLE_KEY` (Pro)
- `GEMINI_API_KEY` / `GH_MODELS_TOKEN`

## 4. Gatekeeper
- **Responsable**: `@orquestador-sdlc` / `@devops-engineer`
- **Criterio de Aprobación**: Backup verificado, SSL Full (Strict) activo y Cloudflare WAF configurado.

---
*Ultima actualización: 2026-04-15*
