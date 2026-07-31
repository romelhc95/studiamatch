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
7. Mantener F9.5 `COMPLETED_WITH_KNOWN_FINDINGS`; sus artifacts de PR #245/#247 son `HISTORICAL_NON_PROMOTABLE` y T01 queda solo como antecedente documental.
8. Conservar el [cierre F9.6](./cierre_h00_f9_6.md) `H00_ALREADY_REMEDIATED_NO_DML`: cohorte con PII directa remediada y conservada como pseudonimizada, Gate B DELETE sustituido, cero DML y nunca Pro.
9. Conservar el candidate local contractual F9.7 v3 byte-identico de seis entradas, el security hold actual bloqueado de [ADR-0005](../decisiones/ADR-0005_corte_seguridad_funcionalidad_estabilidad_hito1.md), el [PR-O v1 superseded](./pr_o_f9_7_v3_hold.md) y el [PR-O executor privado](./pr_o_f9_7_successor_private_executor.md) definido localmente sin implementacion. PR #262 quedo mergeado en `desarrollo@c0b6c5efaaaca25f7946e114cc53f63f3a5daa66` / tree `3e5537f01ebf4bec94ada99b274415fc13a2f039`. Gate B termino FAIL, la atestacion ACL atribuyo fuentes reparables, v2 queda historico no promocionable, el hold actual queda `SUPERSEDED_NON_PROMOTABLE_FOR_FUTURE_ROUTE`, `public.exec_sql(text)` debe desaparecer del estado final sucesor y la Edge Function historica requiere estado remoto valido antes del cierre; snapshot remoto y gates operativos siguen bloqueados. Antes de cualquier lectura o aplicacion se requieren gates nuevos. Resguardo-restauracion, pausa de writers y aplicacion v3 + hold sucesor siguen sin aprobar y conservan decisiones separadas.
10. Aprobar el plan y despues ejecutar/certificar el backfill editorial Free de `H1-CA2P` bajo gates separados para evitar catalogo invisible.
11. Mantener `certificacion` como rama/release bloqueada; Free es el ambiente DB de desarrollo/certificacion del contrato, no una rama Git.
12. Ejecutar en Free ACL por rol, smoke FG2 sin fallback, canary del package exacto, cleanup idempotente y QA independiente.
13. Cumplir el hold operativo F9.10 `USER_PERSONAL_UAT` despues de todas las validaciones tecnicas Free y antes de T04, writer resume o cualquier PR/merge `desarrollo -> certificacion`; requiere candidate commit/tree inmutable y `PASS` personal explicito del usuario.
14. Aceptar T04 solo despues del hold operativo, aprobacion final, CI y review humano; despues alcanzar `free_certified`/`FREE_CERTIFIED` y promover por PR `desarrollo -> certificacion`.
15. Aplicar en Pro solo un manifest `free_certified`, nunca H-00, mediante workflow manual fijado a un commit inmutable, tras aprobacion Production y pausa de writers.
16. Ejecutar canary Pro, negativos anon/authenticated, positivo service role y smoke productivo.
17. Reanudar writers y promover a `main` solo con aprobacion humana; observar antes del cierre.

## Stop Conditions

- Secretos o credenciales en archivos, logs o diffs.
- Tree, ancestry, package o checksum no verificables.
- Mismo stem SQL con contenido distinto o intento de editar ledger.
- H-00 incluido en un glob o manifest Pro.
- Artifact F9.5 de PR #245 o PR #247 tratado como candidate, package contractual o insumo de aplicacion.
- DML no acotado, RLS inesperada o writers activos durante migracion Pro.
- Fallo de test, Context Graph, canary o smoke.
- Diferencia no explicada entre [Matriz DB](matriz_adopcion_db.md) y ambiente real.

## Schedules

FG1, FG2 y FG3 conservan cadencia automatica declarada en YAML. Hito 1 exige que toda ejecucion automatica respete gates, circuit breakers, controles de ambiente y las stop conditions de este flujo. Ver [Pipeline](../arquitectura_pipeline.md).

## Separacion Dentro De La Macrofase F9

- F9.1 produce solo evidencia local/offline y conserva `reconciled_not_certified` con Free/Pro bloqueados; su identidad historica es `FASE-09`.
- F9.2 codifica localmente la maquina de promocion; su descriptor e identidad historica permanecen `FASE-10`.
- F9.3 conserva historia del contrato local. F9.4 reconcilia documentalmente el plan. F9.5 queda `COMPLETED_WITH_KNOWN_FINDINGS`; no se repite la lectura Free y sus artifacts no se promueven.
- T01 queda `CONDITIONAL_ACCEPTED` como antecedente de F9.6, sin attestation tecnica ni capacidad heredada.
- F9.6 cierra H-00 como `H00_ALREADY_REMEDIATED_NO_DML`; Gate B DELETE es `SUPERSEDED_NON_AUTHORIZABLE`.
- F9.7 schema/RLS/corte local, F9.8 plan de backfill, F9.9 ejecucion de backfill y F9.10 certificacion Free son gates distintos; F9.7 tiene v3 byte-identico, PR-O v1/hold actual `SUPERSEDED_NON_PROMOTABLE` y PR-O sucesor con executor privado `DEFINED_LOCAL_NOT_IMPLEMENTED`; sigue bloqueada por implementacion/certificacion local del sucesor, aprobacion Free independiente, snapshot remoto y gates operativos. El T02 historico F10 no se reactiva.
- El orden obligatorio es readiness -> H-00 Free-only -> schema/RLS -> backfill -> validaciones tecnicas Free -> `USER_PERSONAL_UAT` -> T04/certificacion final.
- `free_certified` exige postcondiciones Free, RLS por rol, ledger/checksums, PostgREST, advisors, backfill separado certificado, candidate commit/tree inmutable y `USER_PERSONAL_UAT=PASS`.
- La macrofase F10 Produccion permanece bloqueada hasta cerrar F9 en `free_certified`.

## Maquina De Promocion Hito 1

- El package historico `FASE-10`/F9.2 define localmente `reconciled_not_certified -> ready_for_free -> free_schema_certified -> free_backfill_certified -> free_certified`.
- Cada transicion requiere attestation inmutable y aprobacion propia; no hay saltos ni continuidad automatica.
- F9.4 adopta el plan simplificado y no conecta. La anterior definicion remota F9.4 no es autorizable.
- F9.5 queda cerrada; su T01 condicionado es antecedente historico y no cambia ningun estado DB.
- La maquina de attestations del package historico `FASE-10` no gobierna el T01 documental actual: este no es una attestation ni una transicion de estado.
- F9.6 cerro P0 H-00 sin DML. F9.7-F9.10 separan resguardo/schema/RLS, plan/ejecucion de backfill y certificacion final Free con autorizaciones distintas.
- `USER_PERSONAL_UAT` es hold operativo F9.10, no attestation de la maquina ni transicion nueva; se ubica despues de validaciones tecnicas Free y antes de T04, writer resume o PR/merge `desarrollo -> certificacion`.
- F9.7 requiere conservar identidad backend de servicio para superficies autorizadas y negar a todos los roles de aplicacion, incluido `service_role`, cualquier acceso a `leads`/`email_log`; el hold debe validar rutas directas e indirectas dentro del threat model.
- F10 se limita a Pro/produccion y F11 al cierre final segun [ADR-0003](../decisiones/ADR-0003_taxonomia_macrofases_subfases.md).
- Un fallo pre-commit revierte package y ledger en la transaccion. Un fallo post-commit mantiene writers pausados y detiene toda mutacion. Forward-fix o restauracion requieren un incidente documentado, identidad Free revalidada, owner de recuperacion, backup attestado y una autorizacion de emergencia exacta separada; esta regla no autoriza ninguna de esas operaciones. No se improvisan down migrations.
- La definicion F9.7 exige executor privado no expuesto por Data API, restore `RESTORE_PROVEN` y writers `HELD` antes de una ventana, y conserva writers pausados ante cualquier fallo post-commit.

## Politica De Resguardo

Los respaldos preservados se conservan fuera del repositorio, sin mover, editar o compactar hasta desplegar Hito 1 y completar observacion. Sus rutas locales no se versionan.

Ver [Estado](../estado_del_proyecto.md) y [Tarea 001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md).
