# G08/G09 delta del candidato actual — R143/R144 — 2026-10-11

## Identidad y alcance probado

- Checkout: `/home/romel/src/studiamatch-h3req1-sync-20261002`.
- Rama/HEAD base: `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- Los 63 archivos de la copia `web/` del build R143 coinciden con el checkout:
  63/63, 0 discrepancias. Manifiesto de contenido:
  `ec9001e3d26939c638e3bb7f535eeb1aae7eb7a197e94438b909ca807d82f242`.
- La copia aislada excluyó `.env*`, node_modules y outputs/cache; el build usó
  la imagen local fijada `studiamatch-h3req1:20261009-v3`, sin `.env*`.

## G08 renovado para el delta R143

- Build normal candidato contra las 16 filas sintéticas del PostgREST/PG17 local:
  exit 0; artifact con 201 archivos y 16 rutas de detalle. La verificación del
  manifiesto SHA-256 terminó PASS. Manifiesto:
  `913acb1757b97678520af87037ea93b7e0b01677b3469eca0a21e6ed83f624ee`.
  Log `uat-fullcatalog-r143-build/normal-postgrest-build-fixed.log`, SHA-256
  `b3f2b6af49833d25708ed7e0216c029a75174036c6f015d8eb9374523960fd47`.
- Build normal smoke y mock smoke: exit 0; artefactos respectivos de 126
  archivos con manifests verificados. El intento de build con una clave local
  sin prefijo `sb_publishable_` falló antes del prerender; se conserva como
  configuración de fixture inválida. La repetición corregida usó solo la clave
  sintética `sb_publishable_h3req1_fixture` y pasó.
- ESLint: exit 0, 0 errores y 9 warnings conocidos. Next typegen: exit 0.
  TypeScript: exit 0, heap Node 3072 MiB en contenedor de 4 GiB.
- H2 writer scan: PASS; `tests/test_h2_writer_scan.py`: 4 passed; scanner de
  credenciales focal: PASS. Se ejecutaron en `studiamatch-dev` con `env -i`;
  `PYTHON_DOTENV_DISABLED=1` en los comandos Python.
- Pytest completo 335/4 skips, actionlint/ShellCheck, scanner/scope guard,
  auditorías npm y checks previos se reutilizan por inputs coincidentes con el
  delta R142; no se repitieron sus suites intactas.
- No se ejecutaron checks live ni accesos a cuentas/servicios remotos.

La salida de los scans R143 se conserva en esta nota y en la salida del comando
de ejecución; sus fuentes incluyen `scripts/maintenance/h2_scan_unauthorized_writers.py`
(`cda1abb0fbfb4d3318b3ba65d15f024d364c26f107ffdeadd6c031e6e8c5b5ed`),
`tests/test_h2_writer_scan.py`
(`8735a11715e29bb179d502599867b35a09f6c6f4c41203a91f28d0ef4df3188c`) y el
scanner de credenciales
(`72690e56100cad81b99c52f6d4a9a729f75de2324848bfb5b1ec9bdfd9ccbaeb`).

## LOCAL-07/08/19 — persistencia y recuperación en PostgreSQL 17

Se ejecutó el runner nuevo
`tests/sql/run_h3req1_pipeline_persistence_recovery_pg17_r1.sh` en un PostgreSQL
17.11 desechable fijado a la imagen local
`sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f`.
El contenedor `h3req1-g09-pipeline-pg17-r144` tuvo `network none`, sin puertos ni
volúmenes, PGDATA tmpfs, 2 CPU y 4 GiB; solo montó SQL/migraciones read-only y se
retiró por nombre exacto al terminar. No tocó PG17 R12 ni la base UAT.

Resultado final: exit 0. Sobre un curso sintético, una reconexión observó el
checkpoint `discovered`; el resume continuó a cleansing y dejó stage `processed`
y una fila persistida. Las migraciones vigentes de cleansing (`20260808`) y
enrichment (`20260525 Fase 113`) se ejecutaron en PG17. Se rechazó duración
malformada sin alterar estado ni crear enrichment; la recuperación persistió
una sola fila y el requeue actualizó el mismo registro. Sync confirmó el estado
parcial posterior al fallo de actualización, recuperó el mismo URL/ID y pasó la
segunda upsert sin duplicados. Los fallos/recovery/idempotencia quedan cubiertos
por R2/R18/R140 junto con este contrato SQL persistente.

Log final:
`h3req1_g09_pipeline_pg17_r144/pg17-persistence-r1-final.log`, SHA-256
`3ba8bbe4892ac1050c495021264b52e938d6020c09f747dd608c34f9ea287003`.
Runner SHA-256 `70c901c5cbad1108a9ed953ca90949fe1e6e25f5410aff99560dcadbfec1a04d`;
SQL SHA-256 `3f94e2a7dd0276d91c68b8756ec0f8e084ab56b8491123077aacfa9fdc59e7c5`.
Migraciones fijadas: DDL intermediario
`b6e03ef574728b388399f54edd5b5ed748b9d2a9ac562d4b68849a56faa19219`, cleansing
`741edac171fa2b8431ea3e850ece09324c718b191bc0654801c27dde41aeaeb7`, enrichment
`c44a3fbfb4c25c37dbe51a69303fdc1243ee2ae28686659725d3fe8097214092`.

Dos intentos previos del harness se preservan, no cuentan como fallo de producto:
R1 construyó JSON concatenando saltos de línea inválidos; R2 tenía una variable
PL/pgSQL homónima a una columna. Las causas se corrigieron en el fixture y R3
terminó PASS. Las 24 pruebas Python R18 siguen cubriendo lógica de discovery y
worker con adaptadores; la prueba R144 renueva persistencia SQL, no sustituye
llamada live del crawler, LLM o proveedor cloud.

## UAT R143 sobre artifact actual

- Artifact R143 ya está montado en una segunda instancia Pages/workerd del
  contenedor UAT R12; home y detalle devuelven HTTP 200. Chromium 1228 es
  headless, sin ventana. La instancia nueva usa puertos internos 3370/3371/3373;
  R12 Windows (`127.0.0.1:3333`) sigue intacto.
- Se detuvo y preservó un primer intento en
  `uat-r143-invalid-host-partial/`: el runner usó `127.0.0.1`, distinto del
  origen `localhost` de la configuración vigente; terminó tras 114/213 y mostró
  fallos de cookies `__Host-`. Es un intento inválido de entorno, no se cuenta
  como UAT del candidato ni se atribuye a producto. Cero retries.
- Nueva corrida completa en curso con `H3_BASE_URL=http://localhost:3370`, mock
  `localhost:3371`, perimeter `localhost:3373`, runner de 71 casos y tres
  viewports (213 ejecuciones previstas), cero retries. Evidencia incremental y
  final: `uat-r143-candidate-full71/`.

Al último checkpoint de esta nota, la corrida corregida recién había iniciado;
G09 no se cierra hasta conocer su exit y conciliar todos los casos.
