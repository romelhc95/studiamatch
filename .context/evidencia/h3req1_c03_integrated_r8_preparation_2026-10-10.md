# H3REQ1 C03 integrado R8 — preparación

## Candidato y gate

- Checkout `/home/romel/src/studiamatch-h3req1-sync-20261002`.
- Rama `feat/h3req1-sync-20261002`; HEAD baseline
  `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- Gate activo G07. WIP antes de esta nota: 55 tracked modified / 4394
  untracked / 0 staged (4449 entradas); todos los cambios preexistentes y de
  esta sesión se preservan. Checkout original intacto.
- R5/R6: R5 alcanzó PG17 setup y Pages/workerd healthz, pero no readiness
  PostgREST; R6 falló healthz porque su snapshot omitió el manifiesto canónico
  requerido por el runtime. Causas y resultados clasificados en [R5](h3req1_c03_integrated_r5_preparation_2026-10-10.md)
  y [R6](h3req1_c03_integrated_r6_preparation_2026-10-10.md).
- R7 no se ejecutó: revisión estática recomendó acotar dos llamadas Docker en
  primer plano. Artefactos/manifiesto R7 se preservan.

## Cambios y entradas R8

- R8 usa `tests/h3req1-c03-integrated.sha256`, la ruta que consume el runtime.
  Su prueba contractual confirma consistencia runner/runtime.
- Cada llamada Docker directa tiene deadline de 60 s; el snapshot en primer
  plano, 300 s; cache verifier, 180 s; test contractual, 90 s; `docker exec`
  conserva límites anidados. Las imágenes son locales/fijadas (`--pull=never`),
  redes aisladas `--internal`/`none`, caches read-only, datos y credenciales
  sintéticos.
- Manifiesto canónico, 64 entradas: SHA-256
  `a8ed50ca7d75c3d75a4e9667639c3fdfeb82d0026cd7f344bd48ef8a6fb41ad1`;
  `sha256sum -c` 64/64 PASS.
- Runner `tests/h3req1_c03_integrated_drill_r8.sh`, SHA-256
  `77f52f773cd7a694c3f3dd46e785450415296617ae34dddabc4fa9421de64c5e`.
- Contrato `tests/h3req1_c03_integrated_drill_r8_contract.test.mjs`, SHA-256
  `1a120e900d2558d585c086d9bd7b1fd0d36163d372818de796b37053b4bfb3a7`.
- Runtime compartido SHA-256
  `17ddfa989a1f3322fa1812bb4fefbe83161d5a82d289ae170eb6b31ac7a8ec40`.
- Probe PostgREST compartido SHA-256
  `a3a6bacb4788a179653e6cb980856f4c8bde2be52d2431f62a4d0af0d7004206`.

## Validación y revisión

- Tests Node de contrato: 10/10 PASS en imagen fijada, `network=none`, rootfs y
  mounts read-only.
- ShellCheck 0.11.0 oficial en warning-level: PASS; Bash syntax y
  `git diff --check`: PASS.
- Revisión estática independiente de protocolo/SQL y seguridad: ambas PASS;
  revisaron canonical manifest, deadlines, aislamiento, datos sintéticos,
  salida allowlisted y ownership/cleanup. No ejecutaron el runtime.
- `studiamatch-dev` sigue `healthy`, imagen local
  `studiamatch-h3req1:20261009-v3`; R8 utilizará recursos aislados.

## Resultado runtime R8

La ejecución del comando fijado terminó con **exit 1** en `isolated-postgrest`:

```bash
/usr/bin/timeout --foreground --signal=INT --kill-after=60s 1800s \
  /bin/bash tests/h3req1_c03_integrated_drill_r8.sh \
  --jit H3-CLOSE-03-INTEGRATED-2026-10-10-R8 \
  --manifest-sha256 a8ed50ca7d75c3d75a4e9667639c3fdfeb82d0026cd7f344bd48ef8a6fb41ad1
```

Antes del fallo pasaron snapshot/cache, verificación de imagen PostgreSQL 17.11,
Pages/workerd `healthz`, bootstrap SQL H2→Pro→H3, setup C03 integrado y fixture
sintético. El probe obtuvo `HTTP_503` en los 60 sondeos; R8 no leía el JSON de
respuesta. El proceso de fallo detuvo tres servicios etiquetados del mismo run;
los recursos quedaron preservados. El estado posterior mostró runtime exit 143,
PostgreSQL exit 0 y PostgREST exit 255 después del stop, todos OOM false. Ese
estado posterior no identifica por sí solo la causa del HTTP 503; no se atribuye
el fallo a PostgREST, SQL ni Docker. Edge no se inició y C03 integrado no pasó.

Log sanitizado: [R8 runtime](h3req1_c03_integrated_run_2026-10-10_r8.log).
La corrección R9 añadirá lectura del campo JSON `code` con límite de 8192 bytes,
allowlist y fallback `HTTP_503`; nunca emitirá `message`, `details`, headers ni
body. R8 y sus pins/manifiesto consumidos permanecen preservados. G07 sigue
parcial y no suma puntos.
