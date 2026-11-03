# G07 C03 integrado R36 — clasificación del prefijo psql

Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`,
`feat/h3req1-sync-20261002`, baseline `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
G07 parcial; R35 falló y no se repite intacto.

## Corrección acotada

La reproducción PG17 17.11 con `psql -f` produjo la clase sanitizada
`FILE_LINE_PREFIX`: el formato es `psql:<archivo>:<línea>: ERROR: <SQLSTATE>:`.
R36 reconoce ese prefijo antes del formato `ERROR:` sin ruta y del formato
separado `SQL state:`. El log sigue emitiendo solo la fase, etiqueta fija,
exit numérico y SQLSTATE validado; no emite ruta, línea, mensaje o salida cruda.

Runner: `tests/h3req1_c03_integrated_drill_r36.sh`.
Contrato: `tests/h3req1_c03_integrated_drill_r36_contract.test.mjs`.
Cambio normalizado frente a R35: una rama de clasificación del prefijo `psql:`
y pruebas sintéticas para forma válida y prefijo con código inválido. No cambia
SQL, runtime, límites, imágenes, red ni cleanup.

## Validación previa

- `bash -n` PASS.
- `node --check` PASS.
- Contrato en `studiamatch-dev`: 28/28 PASS.
- ShellCheck 0.11.0 local fijado: PASS.
- `git diff --check`: PASS.
- Manifiesto: 105 entradas, 105 hashes PASS; SHA-256
  `65553014311b27ccd1ff76986cb43330feae135da65a11eb47d634e3b84e01d9`.
- ShellCheck reutilizado de imagen local
  `koalaman/shellcheck:v0.11.0` (`sha256:61862eba1fcf09a484ebcc6feea46f1782532571a34ed51fedf90dd25f925a8d`).

## Ejecución fijada

Una ejecución, stop-on-failure, timeout total 2400 s:

```bash
/usr/bin/timeout --foreground --signal=TERM --kill-after=3s 2400s \
  /bin/bash tests/h3req1_c03_integrated_drill_r36.sh \
  --jit H3-CLOSE-03-INTEGRATED-2026-10-10-R36 \
  --manifest-sha256 65553014311b27ccd1ff76986cb43330feae135da65a11eb47d634e3b84e01d9
```

La fase de suspensión SQL solo avanza si el exit y sus aserciones pasan. Si no,
el SQLSTATE permite identificar el predicado sin divulgar salida de psql. No
atribuir causa funcional hasta leer ese código y contrastar la condición exacta.

## Resultado R36

Manifiesto 105/105, contrato, snapshot, cachés, PostgreSQL 17.11, bootstrap,
fixtures, PostgREST readiness, Pages/workerd login AAL2, reserva in-flight,
suspensión Pages/Edge y dispatcher 403/42501 con nonce preservado pasaron.
La aserción SQL de suspensión terminó `psql exit=3`, ahora clasificada como
`H3S11`. El log sanitizado `h3req1_c03_integrated_run_2026-10-10_r36.txt` tiene
SHA-256 `0ff2852831ea52f921d786311d408ef2c498e49ef2038e8de85db6412965310a`.

H3S11 cubre dos predicados: continuidad de la membresía admin sintética y la
fila de auditoría de invitación ligada a la reserva in-flight. La ejecución no
identifica cuál falló. El fixture inserta la membresía admin antes del ensayo,
pero no se inferirá el resultado después de suspensión; el próximo SQL de prueba
separará ambos predicados con códigos distintos. No se cambia el producto ni se
continúa a finalizadores/recuperación hasta tener esa evidencia.
