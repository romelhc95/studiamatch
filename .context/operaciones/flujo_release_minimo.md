# Flujo De Release Minimo

## Principio

El release es manual, secuencial y fail-closed. Un estado documental no sustituye una verificacion Git, DB, CI o runtime.

## Secuencia

1. Crear una rama `feat/*` desde `desarrollo` verificado.
2. Clasificar cada cambio por allowlist y excluir artifacts historicos.
3. Implementar migrations forward-only y cambios minimos de codigo.
4. Validar en contenedor: pruebas Python, lint, typecheck y build aplicables.
5. Ejecutar auditoria de secretos sobre el diff; no registrar valores.
6. Aplicar y certificar primero en Supabase Free con postcondiciones y RLS.
7. Congelar un candidate inmutable y respaldarlo remotamente.
8. Ejecutar H-00 solo en Free, con autorizacion separada, counts-only y verificacion independiente.
9. Promover por PR `feat/* -> desarrollo -> certificacion`; cada paso requiere review y CI.
10. Aplicar en Pro solo un manifest `free_certified`, nunca H-00, mediante workflow manual fijado a un commit inmutable, tras aprobacion Production y pausa de writers.
11. Ejecutar canary Pro, negativos anon/authenticated, positivo service role y smoke productivo.
12. Reanudar writers y promover a `main` solo con aprobacion humana; observar antes del cierre.

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

## Separacion De Precertificacion Y Free

- F9 produce solo evidencia local/offline y conserva `reconciled_not_certified` con Free/Pro bloqueados.
- F11 obtiene evidencia remota Free read-only; solo F12 local/documental puede decidir `ready_for_free` al validar esa evidencia, package, commit, plan y aprobacion.
- Plan de backfill, aplicacion de schema en Free, ejecucion de backfill y certificacion Free son gates distintos; ningun resultado local los sustituye.
- El orden obligatorio es readiness -> schema/RLS -> backfill -> certificacion final; F10 debe codificarlo mecanicamente antes de cualquier transicion de status.
- `free_certified` exige postcondiciones Free, RLS por rol, ledger/checksums, PostgREST, advisors y backfill separado certificado.
- Pro permanece bloqueado hasta otro gate Production independiente.

## Maquina De Promocion Hito 1

- F10 define localmente `reconciled_not_certified -> ready_for_free -> free_schema_certified -> free_backfill_certified -> free_certified`.
- Cada transicion requiere attestation inmutable y aprobacion propia; no hay saltos ni continuidad automatica.
- F11 queda reservada para preflight Free read-only y no cambia status por si sola.
- F12 acepta localmente la evidencia F11 y crea T01; no conecta ni aplica schema.
- Aplicacion schema/RLS, backfill y certificacion final Free pertenecen a fases y autorizaciones distintas.
- Un fallo pre-commit revierte package y ledger en la transaccion. Un fallo post-commit mantiene writers pausados y detiene toda mutacion. Forward-fix o restauracion requieren un incidente documentado, identidad Free revalidada, owner de recuperacion, backup attestado y una autorizacion de emergencia exacta separada; esta regla no autoriza ninguna de esas operaciones. No se improvisan down migrations.

## Politica De Resguardo

Los respaldos preservados se conservan fuera del repositorio, sin mover, editar o compactar hasta desplegar Hito 1 y completar observacion. Sus rutas locales no se versionan.

Ver [Estado](../estado_del_proyecto.md) y [Tarea 001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md).
