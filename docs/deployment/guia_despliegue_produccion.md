# Guía de Despliegue a Producción - StudIAMatch

Este documento detalla los pasos para el lanzamiento oficial en `studiamatch.com`.

## Fase 1: Base de Datos (Supabase Pro)
**Proyecto:** `zogdcvlqxanzqbvkkdar`

1.  Ingresa al [Dashboard de Supabase](https://supabase.com/dashboard/project/zogdcvlqxanzqbvkkdar).
2.  Ve a la sección **SQL Editor**.
3.  Crea un "New Query".
4.  Copia y pega TODO el contenido de [PRODUCTION_MASTER.sql](../../db/PRODUCTION_MASTER.sql).
5.  Haz clic en **Run**.

## Fase 2: Secretos de GitHub (Producción)
Para que el pipeline de Producción funcione, asegúrate de que los siguientes secretos estén configurados en tu repositorio de GitHub (Settings -> Secrets -> Actions):

| Secreto | Alcance | Nota |
| :--- | :--- | :--- |
| `SUPABASE_URL` | Entorno Production | URL de Supabase Pro |
| `SUPABASE_SERVICE_ROLE_KEY` | Entorno Production | Key maestra para automatización |
| `CF_API_TOKEN` | Repositorio (Global) | Compartido para todos los ambientes |
| `CF_ACCOUNT_ID` | Repositorio (Global) | Compartido para todos los ambientes |
| `GEMINI_API_KEY` | Repositorio (Global) | IA para enriquecimiento diario |

## Fase 3: Dominio (Cloudflare Pages)
1.  En Cloudflare Pages, selecciona el proyecto `studiamatch`.
2.  Ve a **Custom Domains**.
3.  Agrega `studiamatch.com` y sigue las instrucciones para configurar el CNAME.
4.  Asegúrate de que la rama `main` esté apuntando al entorno de Producción.

## Fase 4: Despliegue Total
Una vez configurada la Base de Datos, ejecuta:
```bash
git checkout main
git merge certificacion
git push origin main
```
Esto activará el **Golden Pipeline** que:
1.  Construirá la aplicación de Next.js.
2.  La desplegará en el dominio oficial.
3.  Iniciará el primer ciclo de actualización de datos en Producción.

---
*Estado: Preparado para Lanzamiento*
