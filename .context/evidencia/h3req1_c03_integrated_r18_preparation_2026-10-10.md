# G07 R18 — preparación y revisión del diagnóstico de invitación

## Candidato y alcance

- Checkout `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
  `feat/h3req1-sync-20261002`, HEAD baseline `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- R17 alcanzó Pages/workerd healthz, PG17/PostgREST y login; `trigger-inflight` produjo
  `INVITE_EARLY_UNAUTHORIZED` antes de acreditar reserva. El resultado y runtime R17 exactos
  están preservados. No se repite el R17 intacto.
- El único cambio funcional del harness R18 agrega counters de etapa sintéticos para separar:
  rechazo de API/credencial o sesión del mock Auth, entrada y aceptación de Function, consulta
  PostgREST a `admin_members` con status numérico y RPCs de admisión/reserva. El control informa
  únicamente deltas enteros con claves fijas. No emite tokens, claves, headers, cuerpo, email,
  mensajes, detalles ni SQL.
- R18 conserva código de producto, fixtures SQL, runtime Pages/Edge, imágenes, límites, timeouts,
  sin retries, stop-on-failure y recuperación del runner. Usa nombres, JIT y log propios R18.

## Pins y revisión

- Manifiesto: 69 entradas, SHA-256
  `0be7c1597beb3acbf5755d733febb3e842c662eb661d018ecb91ed92f8ed1a02`; verificación 69/69 PASS.
- Runner R18 SHA-256 `423eca58e71995d0c877f8a539495ccfcc15e9de37b123a5c4546e7ff34051fc`.
- Contrato R18 SHA-256 `dfe8bc4377c91118b7af13798827ad8461273c5fbf580d1c2e117f6a57602b2e`.
- Runtime R18 SHA-256 `2027f2a04c9c1906b8e14cbc1c618922498e1bcdb346337ab2fb069aa01cf381`.
- Fuente comparada con el runtime R17 preservado; el diff se limita a contadores del mock y a
  transportar el selector numérico fijo en errores de la fase de invitación. No modifica BFF,
  Edge ni SQL.
- R18 contract suite: 19/19 PASS en imagen Node fijada, `network none`, mount de tests read-only.
  `node --check`, `bash -n` y `git diff --check` PASS.
- Una ejecución contractual inicial fue 18/19 por expectativa antigua de firma de función;
  corregida esa aserción, la revalidación completa pasó. No hubo Docker runtime en esa ejecución.
- La revisión advirtió que un campo `*ApiKeyRejected` activaría el filtro de salida por contener
  `apikey`. Se renombró a `*CredentialRejected` y se agregó una aserción contra etiquetas
  sensibles; el resultado 19/19 anterior corresponde a estos bytes.
- Redes R17 vacías retiradas tras preservar inventario; no quedaron redes H3 C03 etiquetadas.

## Comando y condición

Ejecutar una vez, timeout exterior 1800 s, cero retries:

```bash
/usr/bin/timeout --foreground --signal=TERM --kill-after=15s 1800s \
  /bin/bash tests/h3req1_c03_integrated_drill_r18.sh \
  --jit H3-CLOSE-03-INTEGRATED-2026-10-10-R18 \
  --manifest-sha256 0be7c1597beb3acbf5755d733febb3e842c662eb661d018ecb91ed92f8ed1a02
```

El runner valida rama/HEAD, hashes, imágenes, snapshot, contrato, caches y recursos exactos.
La integración avanza solo tras cada readiness gate; cualquier fallo detiene servicios del
nonce exacto y conserva el log sanitizado, snapshot, contenedores y volúmenes propios para
evidencia. El comando no accede a servicios remotos, credenciales operativas, `studiamatch-dev`
ni al checkout original.

## Resultado

Pendiente de ejecución R18; preparación y estáticos no acreditan G07.
