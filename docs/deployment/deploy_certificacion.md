# Guía de Despliegue: TIER 2 - Certificación (QA)

Este documento describe el flujo de despliegue para el entorno de certificación de **StudIAMatch**.

> Estado vigente: BLOQUEADO. Free es el ambiente DB de desarrollo/certificacion del contrato; `certificacion` como rama/release permanece bloqueada hasta F9.10, `USER_PERSONAL_UAT=PASS` sobre candidate commit/tree inmutable, CI/review humano y aprobacion final.

## 1. Ficha Técnica del Ambiente
- **Rama Git**: `certificacion`
- **Hosting**: Cloudflare Pages (Alias)
- **URL**: [https://cert.studiomatch.com/](https://cert.studiomatch.com/)
- **Base de Datos**: Supabase Free (Branch o Proyecto QA)

## 2. Flujo de Trabajo
1. No se promociona codigo desde `desarrollo` mientras F9 no alcance `free_certified`.
2. No se habilita despliegue Cloudflare manual desde este documento.
3. Las auditorias y tests F9.10 son prerrequisitos, no autorizaciones de merge.

## 3. Configuración de Secretos (GitHub)
No configurar, rotar ni copiar secretos desde este documento; usar solo los environments autorizados por el flujo vigente.

- `CERT_SUPABASE_URL`
- `CERT_SUPABASE_ANON_KEY`
- `GH_MODELS_TOKEN` (Para auditoría IA)

## 4. Gatekeeper
- **Responsable**: `@qa-engineer`
- **Criterio de Aprobación**: 100% Coherencia de datos (`taxonomy_roi_audit.py`) y 0 fallos en E2E (`Playwright`).

---
*Ultima actualización: 2026-04-15*
