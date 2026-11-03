# H3REQ1 G07 — preparación R42 tras clasificar el replay Edge

## Ficha de impacto

- **Componente:** harness de C03 integrado, lectura diagnóstica del replay directo Edge.
- **Consumidores:** `tests/h3req1_c03_integrated_runtime.mjs`, runner R42 y sus contratos sintéticos.
- **Contrato conservado:** replay integrado exige HTTP 200; fallo informa solo status y clases/códigos cerrados. Pages/BFF mantiene su forma `error.code`. Edge directo emite `{ error, code, request_id }` en la raíz.
- **Preservable:** todos los pasos R41 anteriores al replay; resultado R41, manifiesto, snapshots/caches R4 y evidencia SQL. No se repiten suites ajenas al delta.
- **Renovado:** contrato sintético de respuesta directa Edge, manifiesto del harness/runtime y replay C03 integrado.
- **Recuperación:** runner R42 crea recursos con nombres, labels y nonce nuevos; en fallo detiene solo servicios de ese run y conserva log/recursos. PGDATA es tmpfs. Imágenes, caches y volúmenes existentes se conservan.

## Evidencia que localiza el defecto

R41 completó snapshot, PG17 17.11, bootstrap H2→H3, PostgREST, login Pages/workerd AAL2,
reserva, suspensión persistente, rechazo del dispatcher, finalización in-flight y safe-resume
con assertions SQL. En el replay Edge falló exit 1 con HTTP 409 y `errorCodeClass=ABSENT`.
Log sanitizado SHA-256:
`eaa8e006c497401d77c9f2f0fb814e565fc347c6e7a5a47086adefdadc1479c7`.

La fuente local `supabase/functions/admin-invite/index.ts` devuelve el error Edge como campos
de primer nivel `{ error, code, request_id }`. El runtime de prueba usaba
`payload?.error?.code`, por lo que el código existente no llegaba al clasificador. La llamada
temprana Pages `/api/admin/invitations` sí devuelve `{ error: { code, message }, request_id }`;
ese lector se conserva anidado. La corrección se limita al helper que clasifica el replay
directo Edge y a una prueba que distingue ambos contratos. No se cambia código funcional Edge,
Pages, SQL, el status esperado ni la política de retry.

## Ciclo de corrección y validación estática

Durante la corrección, una primera prueba R42 terminó 31/32 porque una edición provisional
había aplicado la forma directa Edge a la ruta Pages/BFF. El source de Pages confirmó su
shape anidado; se restauró ese lector. No fue un fallo del producto ni una ejecución integrada.

Con la corrección focal actual:

- contrato R42 en `studiamatch-dev`: **32/32 PASS**;
- `node --check tests/h3req1_c03_integrated_runtime.mjs`: **PASS**;
- `bash -n tests/h3req1_c03_integrated_drill_r42.sh`: **PASS**;
- ShellCheck 0.11.0, imagen local `koalaman/shellcheck:v0.11.0`, read-only y `network=none`:
  **PASS**;
- `git diff --check` desde el host del checkout: **PASS**. El intento dentro de `studiamatch-dev`
  no pudo resolver el puntero `.git` a su worktree padre no montado (exit 128); el check se
  ejecutó en el checkout original del candidato y pasó;
- los 115 hashes de R41 fueron comprobados: 114 fuentes sin cambio y solo el runtime esperado
  actualizado. Se preservó el manifiesto R41 exacto en
  `h3req1_c03_integrated_manifest_r41.sha256`, SHA-256
  `c8d2f656b7cfb726ea907d336ca92dd55bef602fcda4245304b56c700fbcf4a4`;
- manifiesto R42: **117/117 PASS**, SHA-256
  `45c77516393942b00709f50ff7a02578a7d33b7f4f5ef798be17f209918ff33d`.
  Conserva los 115 inputs previos y añade runner/contrato R42; evidencia y log se mantienen
  fuera para evitar hashes circulares.

El contenedor habitual está healthy: `studiamatch-dev`, imagen
`studiamatch-h3req1:20261009-v3`; `/app` monta este candidato y `node_modules` está montado.
No se leen Env ni `.env*`. La ausencia de `shellcheck` dentro de esa imagen se resolvió con la
imagen local fijada y efímera; no se instaló software.

## Ejecución R42

Ejecutar una sola vez, timeout 2400 s y stop-on-failure:

```bash
/usr/bin/timeout --foreground --signal=TERM --kill-after=3s 2400s \
  /bin/bash tests/h3req1_c03_integrated_drill_r42.sh \
  --jit H3-CLOSE-03-INTEGRATED-2026-10-10-R42 \
  --manifest-sha256 45c77516393942b00709f50ff7a02578a7d33b7f4f5ef798be17f209918ff33d
```

La invocación usó servicios y usuarios sintéticos en Docker local; no accedió a cuentas, correo
ni DB cloud, secretos, checkout original, `studiamatch-dev` exec, SQL remoto, PR, CI o deploy.

Resultado ejecutado: exit 1 en `edge-first-pages-last-recovery-smoke`. El replay directo Edge
devolvió status 409 y el clasificador ya recuperó `errorCodeClass=ALLOWLISTED`,
`classification=INVITE_EARLY_RECONCILIATION_REQUIRED`. Los pasos previos terminaron PASS,
incluyendo Auth exactamente una vez y safe-resume SQL. Log sanitizado SHA-256
`cec6e2cd7224289e427591560a67c5948e37101ec989e02d5496ae1e665981a4`; inventario/retirada en
[R42 recursos](h3req1_c03_r42_resource_inventory_2026-10-10.md).

La causa ya está localizada al resultado de negocio `reconciliation_required`, pero el source
permite varias condiciones y el log no expone la fila sintética. No se cambia Edge/SQL por
analogía. El siguiente runner añade un probe REST read-only acotado al request ID sintético que
emitirá solo cardinalidad, coincidencias booleanas y clases cerradas de status/delivery. Esto
decidirá si el lookup de idempotencia encontró una fila con metadata incompleta o si el Edge
tomó otra rama. No altera el comportamiento ni debilita el predicado de replay HTTP 200.

Después de preservar log y snapshot, se retiraron los siete contenedores exactos R42 y sus dos
redes internas vacías por IDs verificados. Los volúmenes etiquetados de snapshot y TLS sintético
se conservan; PGDATA tmpfs ya no está montado y no se recupera. No se retiró imagen, cache,
volumen ni recurso ajeno.

G07 sigue parcial. La ejecución completa requiere identificar la condición de reconciliación,
corregir solo si se demuestra un defecto, repetir C03 con fuentes/manifiesto nuevos y pasar el
smoke final.
