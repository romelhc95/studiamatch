# Pg Net Queue Drain F9.7

## Alcance

Runbook documental para un gate futuro de F9.7. No fue ejecutado en esta remediacion local. No autoriza acceso remoto, DDL/DML, lectura de payloads, backup/restore, pausa de writers, backfill, Pro ni produccion.

## Regla Counts-Only

El drenaje se valida solo con conteos agregados. Queda prohibido seleccionar `url`, `headers`, `body`, `content`, `payload`, `record`, correos, nombres, telefonos o cualquier columna con PII.

Consulta permitida para una ejecucion futura autorizada:

```sql
SELECT
    (
        SELECT pg_catalog.count(*)
        FROM net.http_request_queue
    ) AS queued_count,
    (
        SELECT pg_catalog.count(*)
        FROM net._http_response
        WHERE created > pg_catalog.clock_timestamp() - interval '30 minutes'
          AND status_code IS NULL
    ) AS unresolved_recent_count,
    (
        SELECT pg_catalog.count(*)
        FROM net._http_response
        WHERE created > pg_catalog.clock_timestamp() - interval '30 minutes'
          AND status_code >= 400
    ) AS failed_recent_count;
```

## Stop Condition

El gate solo puede avanzar si la consulta devuelve exactamente:

- `queued_count = 0`.
- `unresolved_recent_count = 0`.
- `failed_recent_count = 0`.

Si alguna relacion `net.*` no existe, no hay permiso para inspeccionarla, o cualquier conteo es distinto de cero, el drenaje queda `NOT_PROVEN` y la aplicacion F9.7 permanece bloqueada.

[ADR-0005](../decisiones/ADR-0005_corte_seguridad_funcionalidad_estabilidad_hito1.md) no ejecuta este drenaje. La Edge Function tombstoneada en Git y el security hold local no prueban el estado de `pg_net` remoto; un gate futuro debera seguir esta regla counts-only sin leer payloads.

## Referencias

- [Remediacion local del trigger F9.7](./remediacion_trigger_f9_7.md)
- [Estado del proyecto](../estado_del_proyecto.md)
- [Matriz DB](./matriz_adopcion_db.md)
