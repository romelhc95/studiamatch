# Flujo De Release Minimo

## Principio

El release es manual, secuencial y fail-closed. Un estado documental no sustituye una verificacion Git, DB, CI o runtime.

## Secuencia

1. Crear una rama `feat/*` desde `desarrollo` verificado.
2. Clasificar cada cambio por allowlist y excluir artifacts historicos.
3. Implementar migrations forward-only y cambios minimos de codigo.
4. Validar en contenedor: pruebas Python, lint, typecheck y build aplicables.
5. Ejecutar auditoria de secretos sobre el diff; no registrar valores.
6. Congelar un candidate inmutable con package, checksum, commit y tree verificables.
7. Completar el preflight Free dirigido y aceptar T01 solo con evidencia sanitizada revisada.
8. Aprobar/verificar el respaldo H-00 y despues ejecutarlo solo en Free, con autorizacion DML separada, counts-only y verificacion independiente.
9. Aprobar/atestiguar backup-restauracion y pausa de writers antes de aplicar y certificar schema/RLS en Free.
10. Aprobar el plan y despues ejecutar/certificar el backfill Free bajo gates separados.
11. Promover por PR `feat/* -> desarrollo -> certificacion`; cada merge requiere review humano y CI.
12. Ejecutar en Free ACL por rol, smoke FG2 sin fallback, canary del package exacto, cleanup idempotente y QA independiente; aceptar T04 solo con aprobacion final y alcanzar `free_certified`/`FREE_CERTIFIED`.
13. Aplicar en Pro solo un manifest `free_certified`, nunca H-00, mediante workflow manual fijado a un commit inmutable, tras aprobacion Production y pausa de writers.
14. Ejecutar canary Pro, negativos anon/authenticated, positivo service role y smoke productivo.
15. Reanudar writers y promover a `main` solo con aprobacion humana; observar antes del cierre.

## Stop Conditions

- Secretos o credenciales en archivos, logs o diffs.
- Tree, ancestry, package o checksum no verificables.
- Mismo stem SQL con contenido distinto o intento de editar ledger.
- H-00 incluido en un glob o manifest Pro.
- DML no acotado, RLS inesperada o writers activos durante migracion Pro.
- Fallo de test, Context Graph, canary o smoke.
- Diferencia no explicada entre [Matriz DB](matriz_adopcion_db.md) y ambiente real.

## Schedules

FG1, FG2 y FG3 conservan cadencia automatica declarada en YAML. Hito 1 exige que toda ejecucion automatica respete gates, circuit breakers, controles de ambiente y las stop conditions de este flujo. Ver [Pipeline](../arquitectura_pipeline.md).

## Separacion Dentro De La Macrofase F9

- F9.1 produce solo evidencia local/offline y conserva `reconciled_not_certified` con Free/Pro bloqueados; su identidad historica es `FASE-09`.
- F9.2 codifica localmente la maquina de promocion; su descriptor e identidad historica permanecen `FASE-10`.
- F9.3 conserva historia del contrato local. F9.4 reconcilia documentalmente el plan y no conecta. F9.5 ejecuta el preflight Free dirigido y solo acepta T01 tras PASS/revision.
- H-00, aplicacion de schema en Free, plan de backfill, ejecucion de backfill y certificacion Free son subfases/gates distintos; ningun resultado local los sustituye.
- El orden obligatorio es readiness -> H-00 Free-only -> schema/RLS -> backfill -> certificacion final.
- `free_certified` exige postcondiciones Free, RLS por rol, ledger/checksums, PostgREST, advisors y backfill separado certificado.
- La macrofase F10 Produccion permanece bloqueada hasta cerrar F9 en `free_certified`.

## Maquina De Promocion Hito 1

- El package historico `FASE-10`/F9.2 define localmente `reconciled_not_certified -> ready_for_free -> free_schema_certified -> free_backfill_certified -> free_certified`.
- Cada transicion requiere attestation inmutable y aprobacion propia; no hay saltos ni continuidad automatica.
- F9.4 adopta el plan simplificado y no conecta. La anterior definicion remota F9.4 no es autorizable.
- F9.5 ejecuta el preflight Free read-only dirigido; T01 requiere PASS y aceptacion local, sin aplicar schema.
- F9.6-F9.10 separan backup/DML H-00, backup/schema/RLS, plan/ejecucion de backfill y certificacion final Free con autorizaciones distintas.
- F10 se limita a Pro/produccion y F11 al cierre final segun [ADR-0003](../decisiones/ADR-0003_taxonomia_macrofases_subfases.md).
- Un fallo pre-commit revierte package y ledger en la transaccion. Un fallo post-commit mantiene writers pausados y detiene toda mutacion. Forward-fix o restauracion requieren un incidente documentado, identidad Free revalidada, owner de recuperacion, backup attestado y una autorizacion de emergencia exacta separada; esta regla no autoriza ninguna de esas operaciones. No se improvisan down migrations.

## Politica De Resguardo

Los respaldos preservados se conservan fuera del repositorio, sin mover, editar o compactar hasta desplegar Hito 1 y completar observacion. Sus rutas locales no se versionan.

Ver [Estado](../estado_del_proyecto.md) y [Tarea 001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md).
