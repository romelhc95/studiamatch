# Guía de Despliegue: TIER 2 - Certificación (QA)

Este documento describe el flujo de despliegue para el entorno de certificación de **StudIAMatch**.

## 1. Ficha Técnica del Ambiente
- **Rama Git**: `certificacion`
- **Hosting**: Cloudflare Pages (Alias)
- **URL**: [https://cert.studiomatch.com/](https://cert.studiomatch.com/)
- **Base de Datos**: Supabase Free (Branch o Proyecto QA)

## 2. Flujo de Trabajo
1. Se promociona código mediante un Pull Request desde `desarrollo`.
2. El despliegue en Cloudflare se vincula a la rama `certificacion`.
3. Se ejecutan scripts de auditoría de datos y tests E2E obligatorios.

## 3. Configuración de Secretos (GitHub)
- `CERT_SUPABASE_URL`
- `CERT_SUPABASE_ANON_KEY`
- `GH_MODELS_TOKEN` (Para auditoría IA)

## 4. Gatekeeper
- **Responsable**: `@qa-engineer`
- **Criterio de Aprobación**: 100% Coherencia de datos (`taxonomy_roi_audit.py`) y 0 fallos en E2E (`Playwright`).

---
*Ultima actualización: 2026-04-15*
