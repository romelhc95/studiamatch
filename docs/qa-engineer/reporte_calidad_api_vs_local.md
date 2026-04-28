# Reporte de Calidad y Refactorización (TDD Workflow)

**Fecha:** 2026-04-18
**Auditor:** @tdd-coder / @qa-engineer
**Componente Evaluado:** `scripts/core/universal_harvester.py`

## Análisis TDD: Integración Local vs Configuración API

### Estado de Pruebas: 🔴 FALLAN EN EJECUCIÓN LOCAL
El script `test_db_compatibility.py` valida la integridad y paridad de operaciones de base de datos a través de `db_client.py`. Dado que `universal_harvester.py` fue revertido a usar la librería `requests` de forma hardcodeada:
1. **Pérdida de Cobertura Universal**: El script ya no es agnóstico del entorno. Ignorará las variables de entorno para la Base de Datos Local (`DATABASE_URL`).
2. **Crash Inminente en Local CI**: Al ejecutar Github Actions localmente con `act`, este levantará los contenedores. Como tenemos `studiamatch-db-predesa` ejecutándose solo con Postgres en puerto 5432 (Sin la instancia de PostgREST API que sí existe en el Supabase Cloud real), la petición `requests.get` a la URL fallará con un "Connection Refused". 

### Deuda Técnica Generada
- **Acoplamiento Fuerte**: Lógica de red (`HTTP requests`) mezclada directamente dentro de lógica de negocio o scraping.
- **Falta de Abstracción `on_conflict`**: En el código introducido, se utiliza el endpoint de API `/staging_raw?on_conflict=url` pero sin garantizar uniformemente la resolución de conflictos si en el futuro se desea apuntar la app a otra tecnología.

### Sugerencia de TDD Repair
Para integrar la ejecución local con la configuración API general y permitir que el workflow (`production_pipeline.yml`) corra éxitosamente a través de `act`, **se recomienda encarecidamente**:
- Remediación Automática: Deshacer los cambios de `requests` y restituir la inyección del `db_client.py` en `universal_harvester.py`. El cliente de Base de Datos es el único componente diseñado y cualificado (100% PASS en las pruebas de compatibilidad) para decidir si enviar peticiones REST (hacia Cloud) o Queries Postgres Directas (sobre el contenedor Local).

## Instrucciones para Ejecutar GitHub Actions Localmente

Alineado a tu necesidad de visualizar y ejecutar el Golden Pipeline usando los recursos de la máquina, aquí te explico cómo ejecutarlo correctamente una vez remediado el script:

### Requisitos previos confirmados:
- Se tiene instalado `nektos.act` (`act version 0.2.87`).
- Dispones del archivo `.env.local`.

### 1. Ejecución del Flujo con `act`
Al usar `act`, simularás el entorno exacto de Github Actions en tu Docker local. A diferencia del comando normal, para ejecutar con un archivo `.env` específico asegurando que use la BD local, correrás:

```powershell
act workflow_dispatch -W .github/workflows/production_pipeline.yml --env-file .env.local -l
```
*(El flag `-l` sirve solo para listar. Para **ejecutar realmente todo el flujo** quita la ` -l` al final)*.

```powershell
act workflow_dispatch -W .github/workflows/production_pipeline.yml --env-file .env.local
```

### 2. Uso del Secret Token en pipeline
Si la pipeline necesita `SUPABASE_KEY` o secrets adicionales no mapeados en tu `.env.local`, a veces es necesario proveer un archivo de secrets específico para act:
```powershell
act workflow_dispatch -W .github/workflows/production_pipeline.yml --secret-file .env.gitdesa
```
*(Esto es ideal para que las ramas de desarrollo local se prueben contra Supabase Cloud antes de producción, pero como tú deseas la base de datos dockerizada, usa `--env-file` primeramente).*

---
**Punto de Decisión:**
> "Se han detectado problemas de calidad y seguridad arquitectónica con el uso directo de `requests` en escenarios locales (ya que Postgres no tiene endpoint REST propio). ¿Desea que el equipo proceda con la remediación automática (TDD Repair) del `universal_harvester.py` para devolver su compatibilidad o prefiere intervenir manualmente antes de lanzar el comando de `act`?"
