# G06 S15 — Pages/workerd sobre snapshot S17

Fecha: 2026-10-10. Candidato `feat/h3req1-sync-20261002`, HEAD baseline
`4eb4d877a50b012bb630a129bd0c74482c33be9c`. Autorización humana vigente:
operaciones H3 locales en el candidato, con fixtures locales y sin servicios,
cuentas, secretos ni escrituras remotas. S17 cerró G05; S15 es el siguiente
gate, todavía no ejecutado.

## Ficha de impacto

- **Componente:** arranque Pages/workerd usando snapshot fuente y dependencias
  locales fijadas.
- **Consumidores:** G07 C03 integrado, que espera healthz PASS.
- **Contrato:** runtime Pages aislado en red interna S11; imagen Node local
  fijada; candidato, tools y dependencias read-only; sin secretos ni `.env*`;
  2 CPU, 2 GiB, timeout 180 s; salida filtrada y allowlisted.
- **Preservado:** snapshots S16/S17, holder y volúmenes S11, runtimes fallidos
  S13/S14 y checkout original. Solo el contenedor exacto S15 se retira tras
  healthz PASS, evidencia preservada y verificación de identidad; ante NO-GO se
  conserva para diagnóstico.
- **Pruebas preservables:** S14 helpers y clasificación si sus hashes coinciden;
  S17 productor/receptor/verificador y S11 locks se validan por inputs fijados.
- **Renovado:** source manifest v9, snapshot S17, identidad S14 como precedente,
  self-test de parada 9/9 y runner/sidecar S15.

## Pins y validación estática

- Los pins previos quedaron supersedidos antes de ejecutar Docker porque el
  manifiesto ya no incluía notas de preparación que cambiaron después de S17.
  El conjunto vigente es: runner SHA-256
  `87d4398287a097edc8bbff7a5d942596be46fb0d1c90fc8a2cf7298d7cc11821`,
  sidecar SHA-256
  `5125df73f572665c5f79fc372319d9316120cd264890b89a4f9b9ce99ac7f8bb` e
  inputs manifest SHA-256
  `f69620d2d7b16d530fe5cd45be3a3f74e1cafb3da0aa9b222058b48aaef78cf7`.
- Recovery self-test SHA-256:
  `bb44bebdd6c1c7b116a259e7ef391350c302e2e434d23e4bb89251d571d21060`;
  9/9 sintéticos PASS. `bash -n` y ShellCheck 0.11.0 PASS en contenedor
  `network=none`, read-only y límites acotados.
- Manifiestos de inputs S15, fuentes v9 y sidecar: hashes PASS.
- Tras actualizar el sidecar: `bash -n` PASS, recovery 9/9 PASS,
  `sha256sum -c` de los inputs PASS y ShellCheck 0.11.0 PASS. La revisión
  independiente de estos pins finales sigue pendiente; todavía no se inició
  Pages/workerd.
- Preflight read-only ambiental PASS: S17 container/volume coinciden con IDs,
  labels y estado; holder S11 conserva mounts read-only de tools/pages y la
  fuente histórica S16; runtime anterior S14 coincide con su evidencia; red
  interna S11 vacía, imagen fijada presente, nombre S15 y ruta de evidencia
  libres. Sin inspección de `Env` ni logs crudos.

El holder S11 conserva intencionalmente `/source` apuntando al volumen S16
histórico. S17 tiene su volumen persistente independiente y el runner lo monta
read-only directamente en `/candidate`; no se cambia ni recrea el holder.

## Estado y comando

Revisión independiente estática del paquete S15 pendiente. El runtime, Edge,
PostgreSQL, PostgREST y SQL no se ejecutaron en esta preparación. G05 completo;
G06 pendiente; G07 sigue bloqueado. Tablero histórico 50%; cierre local 5/9 =
55.56%, mismo nivel que al inicio de este ciclo.

Tras revisión PASS y pins intactos, comando exacto:

```bash
bash tests/h3req1_c03_startup_runtime_diagnostic_s15.sh \
  --runner-sha256 87d4398287a097edc8bbff7a5d942596be46fb0d1c90fc8a2cf7298d7cc11821 \
  --sidecar-sha256 5125df73f572665c5f79fc372319d9316120cd264890b89a4f9b9ce99ac7f8bb
```

Una falla detiene G06; el filtro conserva solo fases/códigos allowlisted. Solo
healthz PASS permite avanzar al C03 integrado local.
