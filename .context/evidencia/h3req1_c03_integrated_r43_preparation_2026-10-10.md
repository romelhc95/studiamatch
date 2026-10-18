# H3REQ1 G07 — preparación R43 con diagnóstico read-only del estado de replay

## Ficha de impacto

- **Componente:** diagnóstico del harness C03 para la invitación sintética persistida al replay Edge.
- **Consumidores:** runtime local integrado, helper de clasificación de prueba, runner R43 y contrato.
- **Contrato preservado:** el replay debe devolver HTTP 200 para la misma invitación y no volver a llamar Auth; no cambia Edge, Pages/BFF, SQL ni status esperado.
- **Pruebas preservadas:** los pasos R42 anteriores al replay, C03 SQL aislado que conserve inputs y el contrato R42 del shape Edge/BFF.
- **Pruebas renovadas:** clasificación sintética de estado persistido, contrato R43 y ejecución integrada del replay.
- **Recuperación:** servicios R43 aislados, credenciales solo sintéticas, PGDATA tmpfs; logs sanitizados. En fallo se paran solo servicios etiquetados del run. La limpieza selectiva posterior requiere inventario; los volúmenes snapshot/TLS R42 y R43 se preservan.

## Evidencia que motiva el probe

R42 terminó exit 1 en `edge-first-pages-last-recovery-smoke`. Pasaron snapshot, PG17 17.11,
bootstrap, PostgREST, Pages/workerd AAL2, reserva, suspensión, dispatcher 403/42501,
finalización Auth una vez, safe-resume y assertions SQL. El replay Edge devolvió status 409 y
código allowlisted `INVITE_EARLY_RECONCILIATION_REQUIRED`.

El source Edge permite más de una condición que resulta en ese código; los logs R42 no permiten
distinguirlas. R43 consulta de forma read-only el registro con el request ID sintético exacto,
limit 2 y máximo 8 KiB. Selecciona datos solo en memoria; el helper devuelve cardinalidad,
coincidencias booleanas de request/actor/correo/rol, clases cerradas de status/delivery y
presencia/coincidencia de user ID. No devuelve valores del registro, código de invitación,
correo, UUID, metadata, errores ni secretos. La consulta va al PostgREST local con credenciales
sintéticas ya creadas por el fixture, no a un servicio operativo. Se hace antes del único replay;
el replay continúa con la expectativa HTTP 200 sin retries.

## Ciclo TDD y validación previa

El contrato sintético R43 se escribió primero. Con un stub sin clasificación devolvió el fallo
esperado (32/33); la implementación mínima produjo después **34/34 PASS** en
`studiamatch-dev`. El test cubre fila coincidente, `send_failed`, mismatch de request/actor/email/
rol, entrega incompleta, ID ausente, cardinalidades zero/multiple/invalid y ausencia de campos
crudos. Los contratos estáticos verifican URL y proyección fijas, GET, filtro exacto, límite,
timeout, techo de bytes, sanitización y que el probe preceda al replay.

- Contrato R43: **34/34 PASS**.
- `node --check` runtime y helper: **PASS**.
- `bash -n` runner R43: **PASS**.
- ShellCheck 0.11.0 (`koalaman/shellcheck:v0.11.0` local, `network=none`, read-only): **PASS**.
- `git diff --check`: **PASS**.
- Manifiesto R42 se archivó sin cambios en
  `h3req1_c03_integrated_manifest_r42.sha256`, SHA-256
  `45c77516393942b00709f50ff7a02578a7d33b7f4f5ef798be17f209918ff33d`. De sus 117 filas,
  116 siguen coincidiendo y solo cambió el runtime fijado por R43.
- Manifiesto R43: **120/120 PASS**, SHA-256
  `acc4b2b733998bd6f5e5be1010c7e7c9e8cc72d26f598d5bcc5c93f21443b096`; conserva los 117
  paths R42 y añade runner R43, contrato R43 y helper. El log y esta preparación quedan fuera
  del manifiesto para evitar ciclo de hashes.
- Runner R43 solo cambia JIT, nombres de recursos/log y path/nombre del contrato frente a R42.

`studiamatch-dev` está healthy con imagen `studiamatch-h3req1:20261009-v3`; `/app` monta el
candidato y `node_modules` está montado. Los siete contenedores y dos redes R42 se retiraron
por identidad exacta tras preservar evidencia. Se retienen los volúmenes de snapshot R42 y TLS
sintético; no se tocaron imágenes ni caches R4.

## Identidad y ejecución R43

- Rama/HEAD: `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- WIP al cierre del preflight R43: 653 entradas (55 tracked modificados, 598 untracked).
- Runner SHA-256: `ad73441a813906bd61588acddfded0c030974a31e5428139a810cf65a2629d47`.
- Runtime SHA-256: `16e98d81693639ee04d613a941f8530166bb42cf5e69f8aaee03c46c11dd3e7e`.
- Helper SHA-256: `2bf5d1be10c92356978b9f07ff4b8e6057c2157f7916de92b7cc69f656aabead`.
- Contrato SHA-256: `6e56950321141c91295ea113d5fbd537cba376b897d255db38ed295b0ecbfe49`.
- Manifiesto SHA-256: `acc4b2b733998bd6f5e5be1010c7e7c9e8cc72d26f598d5bcc5c93f21443b096`.

El preflight integrado comprueba branch/HEAD, manifest, pins, daemon local esperado, caches,
capacidad y colisiones exactas antes de crear recursos. La única ejecución permitida en este
ciclo local es:

```bash
/usr/bin/timeout --foreground --signal=TERM --kill-after=3s 2400s \
  /bin/bash tests/h3req1_c03_integrated_drill_r43.sh \
  --jit H3-CLOSE-03-INTEGRATED-2026-10-10-R43 \
  --manifest-sha256 acc4b2b733998bd6f5e5be1010c7e7c9e8cc72d26f598d5bcc5c93f21443b096
```

No se ejecuta SQL sobre otra base, se lee `.env*`, usan cuentas/correo reales, modifica el
checkout original o llama un servicio remoto. Un fallo detiene las fases dependientes. G07
permanece parcial hasta probar replay 200, misma invitación, ausencia de segundo correo,
sesión AAL2/rol y smoke final.

## Resultado R43 y diagnóstico

R43 se ejecutó una vez, timeout 2400 s, exit 1 en `edge-first-pages-last-recovery-smoke`.
Pasaron snapshot, caches, PG17 17.11, bootstrap, PostgREST readiness, Pages/workerd AAL2,
reserva, suspensión, denegaciones, finalizador in-flight una vez, safe-resume y assertions SQL.
El replay Edge respondió 409 `INVITE_EARLY_RECONCILIATION_REQUIRED`; el probe read-only
respondió 404 `PGRST125` y no leyó filas. La causa probada del 404 fue `/rest/v1/` delante de
un PostgREST directo en `:3000`; PostgREST 13 clasifica PGRST125 como URL path inválido.
No se atribuyó el replay 409 al producto. Resultado/inventario y manifiesto R43 preservados en
[R43](h3req1_c03_r43_result_inventory_2026-10-10.md) y
[manifiesto archivado](h3req1_c03_integrated_manifest_r43.sha256).

Después se hizo una prueba test-first de la ruta directa, se corrigió únicamente el path a
`/admin_invitations`, y se revalidaron los contratos R43/R44: 68/68 PASS. Esto reemplaza el
path afirmado por los contratos R43/R44 vigentes; el manifiesto R43 archivado conserva los
hashes del ensayo histórico y ya no describe los dos inputs cambiados tras ese ensayo.
