# Guía de Despliegue a Producción - StudIAMatch

Este documento detalla los pasos para el lanzamiento oficial en `studiamatch.com`.

> Estado vigente: LEGACY_BLOQUEADO_NO_EJECUTAR. Esta guia es historica y no autoriza Supabase Pro, Cloudflare manual, `main`, produccion, backup/restore, writers ni secrets. Usar `.context/estado_del_proyecto.md` y `.context/operaciones/flujo_release_minimo.md` como autoridad.

## Fase 1: Base de Datos (Supabase Pro)
**Proyecto:** `[CREAR EN R6]`

Bloqueado hasta que F9 termine en `free_certified` y existan aprobaciones separadas de F10. Los pasos historicos de creacion Pro, restore y seed quedan retirados como instrucciones ejecutables.

## Fase 2: Secretos de GitHub (Producción)
No configurar secretos de Production desde esta guia. La lista historica fue retirada como instruccion ejecutable; cualquier secreto vive solo en el gestor autorizado y bajo el flujo vigente.

## Fase 3: Dominio (Cloudflare Pages)
Bloqueado hasta F10/F11 con autorizacion explicita. Los pasos historicos de dominio, CNAME y rama `main` quedan retirados como instrucciones ejecutables.

## Fase 4: Despliegue Total
No ejecutar. La promocion historica a `main`, el despliegue del dominio oficial y el primer ciclo de datos en Produccion quedan bloqueados por el flujo vigente.

---
*Estado: Legacy bloqueado; no preparado para lanzamiento bajo el flujo vigente.*
