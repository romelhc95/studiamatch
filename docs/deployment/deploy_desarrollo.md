# Guía de Despliegue: TIER 1 - Desarrollo

Este documento describe el flujo de despliegue para el entorno de desarrollo de **StudIAMatch**.

> Estado vigente: referencia historica no operativa. No configurar Cloudflare, GitHub Secrets ni workflows desde este documento; usar `.context/estado_del_proyecto.md` y `.context/operaciones/flujo_release_minimo.md`.

## 1. Ficha Técnica del Ambiente
- **Rama Git**: `desarrollo`
- **Hosting**: Cloudflare Pages (Preview)
- **URL**: [https://studiamatch.pages.dev/](https://studiamatch.pages.dev/)
- **Base de Datos**: Supabase Free Project (ID: `YOUR_FREE_PROJECT_REF`)

## 2. Flujo de Trabajo
1. Los desarrollos se inician en ramas de `feature/*`.
2. Los builds automaticos solo se consideran efectos de CI configurado; este documento no autoriza Cloudflare manual.
3. Este entorno (Tier 1) utiliza el proyecto de Supabase Free para aislar datos de experimentación.

## 3. Configuración de Visualización (Dashboard Cloudflare)
Bloqueado como instruccion operativa. No configurar campos, variables ni dashboard Cloudflare desde este documento.
## 4. Secretos de Backend (GitHub Actions)
No configurar ni copiar secretos desde este documento. Los secrets autorizados viven solo en GitHub Environments bajo el flujo vigente.

## 5. Estrategia "Data Drip" (Enriquecimiento IA)
- **Ejecución**: Diaria vía GitHub Actions.
- **Cuota**: Limitada a 100 cursos/día para mantenerse en tier gratuito.
- **Calidad**: Filtro activo de >150 caracteres para descripción inicial.

## 6. Gatekeeper y Calidad
- **Responsable**: `@SDLC-Chief`
- **Métrica de Éxito**: Tasa de enriquecimiento > 90% y auditoría de integridad (`quality_assurance_audit.py`) sin fallos críticos.

---
*Ultima actualización: 2026-04-16 (Fase 31.5 - Estabilización Visual Completa)*
