# G07 C03 integrado R35 — preparación focalizada del SQLSTATE

Fecha: 2026-10-10. Candidato local: `/home/romel/src/studiamatch-h3req1-sync-20261002`,
rama `feat/h3req1-sync-20261002`, baseline `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
G07 sigue parcial. No se modificaron el checkout original, `studiamatch-dev`, secretos
ni servicios remotos.

## Hallazgo y corrección

R34 alcanzó Pages/workerd, Edge, PostgREST y la suspensión; el dispatcher devolvió
HTTP 403, SQLSTATE `42501`, con nonce preservado. La aserción SQL posterior falló
con `psql exit=3`, pero R34 reportó `UNCLASSIFIED`. El parser buscaba `SQL state:`.

En una PG17 17.11 sintética, con red deshabilitada, mounts ausentes y PGDATA en
tmpfs, se generó `H3S04` de forma deliberada. La salida acotada por patrón indicó
`phase=synthetic-sqlstate|error_code=ERROR_PREFIX_WITH_SQLSTATE`, demostrando que
el formato emitido comienza con `ERROR:  H3S04:`. R35 extrae el código de ese
prefijo y conserva el formato separado `SQL state:` como compatibilidad. Nunca
emite texto, archivo o metadata cruda de `psql`.

El ensayo sintético R3, con un perfil más estricto que añadía `cap-drop ALL`,
terminó exit 1 antes de producir una clasificación útil; su motivo no se capturó,
por lo que no se usa como diagnóstico. Su contenedor exacto fue retirado antes de
R4. R4 fue el caso mínimo concluyente.

## Inputs, revisión y gates

- Runner: `tests/h3req1_c03_integrated_drill_r35.sh`.
- Contrato: `tests/h3req1_c03_integrated_drill_r35_contract.test.mjs`.
- Cambio normalizado frente a R34: únicamente extracción `ERROR: <SQLSTATE>:` y
  regresiones sintéticas para formato nuevo, formato compatible y prefijo inválido.
- Bash syntax: PASS.
- Node syntax y contrato Docker `studiamatch-dev`: 28/28 PASS.
- ShellCheck 0.11.0 en imagen local fijada `sha256:61862eba1fcf09a484ebcc6feea46f1782532571a34ed51fedf90dd25f925a8d`: PASS.
- Manifiesto integrado: 103 entradas; todos los hashes PASS;
  SHA-256 `8ffd4dc69d50ba72e6bd714e41511fb9fe943d674405d947f0fe8e1d6431e624`.
- Revisión estática del delta R34→R35: sin cambios de runtime, SQL, límites,
  rutas de cleanup o controles Docker; el SQLSTATE sale de una captura en memoria
  y pasa por validación de cinco caracteres antes del registro.

## Ejecución fijada

Comando previsto, una sola vez y stop-on-failure:

```bash
/usr/bin/timeout --foreground --signal=TERM --kill-after=3s 2400s \
  /bin/bash tests/h3req1_c03_integrated_drill_r35.sh \
  --jit H3-CLOSE-03-INTEGRATED-2026-10-10-R35 \
  --manifest-sha256 8ffd4dc69d50ba72e6bd714e41511fb9fe943d674405d947f0fe8e1d6431e624
```

El runtime usa solo candidatos/sintéticos y servicios aislados. Si falla, solo se
considerará el SQLSTATE allowlisted para identificar la aserción. No avanzar a
dependientes hasta corregir y validar el predicado que la evidencia señale.

## Resultado R35

R35 ejecutó con el manifiesto aprobado (103/103 hashes), contrato PASS, PG17 17.11,
bootstrap H2-Pro→H3 y fixtures SQL PASS, PostgREST readiness PASS, Pages/workerd
login PASS con `aal2`, cookies y reserva in-flight PASS. La suspensión Pages/Edge
PASS y el dispatcher firmado devolvió HTTP 403/SQLSTATE `42501` con nonce preservado.
La aserción SQL de suspensión falló con `psql exit=3`; R35 produjo
`sql-gate-failure|label=suspended ACL/data/quota/audit assertions|exit=3|code=UNCLASSIFIED`.
El log sanitizado `h3req1_c03_integrated_run_2026-10-10_r35.txt` tiene SHA-256
`3153b3fe12e0a9f1c88d1908f4298afc3f1cfa36bbe033caf10847c9ec0ab78f`.

La causa demostrada de `UNCLASSIFIED` fue que el parser R35 cubría `ERROR:` al
inicio de línea y `SQL state:` separado, pero no el prefijo `psql:<archivo>:<línea>:`
que aparece al ejecutar `psql -f`. La reproducción mínima R5, en PG17 17.11 aislado,
capturó solamente la clase sanitizada
`phase=synthetic-psql-file|error_code=FILE_LINE_PREFIX`. La causa de la aserción SQL
misma aún no está identificada; R36 deberá clasificar su SQLSTATE antes de atribuir
un defecto al fixture o al producto.
