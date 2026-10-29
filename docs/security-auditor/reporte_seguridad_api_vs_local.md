# Reporte de Auditoría de Seguridad: Integración Local vs API REST

**Fecha:** 2026-04-18
**Auditor:** @security-auditor
**Componente Evaluado:** `scripts/core/universal_harvester.py` y configuración de entorno (`.env.local`).

## Análisis de los Cambios Recientes
Se ha detectado una modificación manual en `universal_harvester.py` que revierte el uso del Adaptador Universal (`DatabaseClient`) a favor de llamadas directas mediante `requests` a la API REST de Supabase. A continuación se presentan los hallazgos de seguridad respecto a esta integración.

### 🛡️ Reporte de Vulnerabilidades Detectadas

| Severidad | Vulnerabilidad Detectada | Archivo:Línea | Impacto |
| :--- | :--- | :--- | :--- |
| **[ALTA]** | **Inyección en URL (PostgREST)** | `universal_harvester.py:195` | La construcción `url=eq.{url}` sin URL-encoding permite que URLs maliciosas alteren la sintaxis de la consulta REST de Supabase, pudiendo evadir filtros. |
| **[MEDIA]** | **Omisión de Seguridad Centralizada** | `universal_harvester.py:34` | Ignorar el `db_client.py` y manejar los headers y `SUPABASE_KEY` manualmente fomenta la duplicación de secretos y aumenta la superficie de ataque. |
| **[MEDIA]** | **Transmisión de Secretos** | `universal_harvester.py:38` | Si el entorno local se configura sobre HTTP (Ej. `http://localhost`), el token `apikey` viaja en texto plano (sin TLS). Esto es riesgoso incluso en local. |

### Sugerencias de Integración Segura (Local vs Cloud)

Actualmente, el pipeline mezcla dos filosofías: **Acceso Directo (Local PostgreSQL)** y **Acceso API (Supabase REST)**.
El uso de `requests` directamente en los scripts asume que **siempre** hay una API REST (PostgREST) disponible. Sin embargo, en el entorno local (usando el contenedor original `studiamatch-db-predesa`), solo exponemos el puerto 5432 (PostgreSQL puro), no hay una capa de API REST. 

**Si se mantiene la ejecución mediante API (`requests`)**:
Las Github Actions en local fallarán al intentar conectarse porque el Docker local de Base de Datos espera conexiones SQL (`psycopg2`), no peticiones HTTP REST. 

**Requisito indispensable de seguridad y arquitectura:**
Es mandatorio volver a utilizar el `DatabaseClient` que encapsula la seguridad (usando parámetros `%s` anti-inyección) y determina dinámicamente si usar SQL o HTTP según el entorno, garantizando que el pipeline local o producción sea un éxito absoluto.
