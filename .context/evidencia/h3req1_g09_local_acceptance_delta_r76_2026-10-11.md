# H3REQ1 G09 delta R76 — logout de cookies Auth multi-chunk — 2026-10-11

## Candidato y cambio

- Checkout `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
  `feat/h3req1-sync-20261002`, HEAD baseline
  `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- Solo se amplió el test untracked ya presente en WIP
  `tests/h3_admin_bff_mock_uat.mjs`; su SHA final es
  `7c1fefd3f8743a1b3a898bf4a1b200b7c2f486380bc293045760435644065b40`.
- Código BFF bajo prueba `web/functions/_lib/admin-bff.ts` sin cambios; SHA
  `0cf11ce7729dcd0f1a681c5faee81131456f2e1fb337c46611f76507a593dea7`.
- El caso envía logout con cookie Auth base, `.0/.1/.2`, code-verifier base y
  code-verifier `.0/.1`, y requiere `Max-Age=0` para los siete nombres.

## Resultado ejecutado

- Entorno: `studiamatch-dev`, ID
  `500931b0f086d29ec9e751e1fd652f9b7ccd357f3eb64daa8751344776162049`, imagen
  `studiamatch-h3req1:20261009-v3`, healthy; el SHA dentro de `/app` coincidió
  con host. El proceso Node usó `env -i` con solo PATH/HOME.
- Comando: `docker exec -w /app studiamatch-dev /usr/bin/env -i
  PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp node
  tests/h3_admin_bff_mock_uat.mjs`, límite 120 s, una ejecución.
- Salida: `{"result":"PASS","checks":96,"quotaCases":10,
  "activityCookieRejectCases":6,"mfaSessionRebindCases":1,
  "sessionOriginRejectCases":4,"signingKeyConfigRejectCases":4,
  "authCookieNamesCleared":7}`. Exit 0, cero retries. Log sanitizado
  `h3req1_g09_local_acceptance_r76/bff-multichunk-r76.log`; confirmación
  aislada en `h3req1_g09_local_acceptance_r76/bff-multichunk-netnone-r76.log`.
- No se usó navegador, Auth real ni DB; el test invoca BFF con Auth/cuota/RPC
  en memoria. No se cargaron `.env*` ni secretos. La primera corrida heredó la
  red del contenedor habitual; para aplicar el límite de egress se hizo una
  confirmación separada del mismo input en container efímero `--network=none`,
  `--read-only`, user 1000:1000, `--pull=never`, `env -i`, mounts de `/app` y
  dependencias read-only y `/tmp` tmpfs. Imagen ID
  `sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63`.
  El source hash volvió a coincidir y produjo 96 checks PASS, exit 0, cero
  retries; `--rm` retiró el contenedor y postflight no encontró residual. Es una
  verificación de aislamiento, no un retry tras fallo del test.

## Checks afectados y fallos preservados

- `node --check tests/h3_admin_bff_mock_uat.mjs`: PASS, Docker.
- `scripts/security/scan_credentials.sh tests/h3_admin_bff_mock_uat.mjs`: PASS,
  Docker.
- `git diff --check` dentro del contenedor: exit 128 antes de evaluar el diff;
  el puntero Git de `/app` refiere al worktree del host, ausente en el contenedor.
  Se ejecutó el mismo chequeo read-only desde el checkout WSL y pasó exit 0.
- El primer preflight de source hash contenía un marcador literal y se detuvo
  con `SOURCE_HASH_MISMATCH` antes de ejecutar Node. Se calculó el SHA real, se
  confirmó coincidencia host/`/app` y la única ejecución corregida pasó. No hubo
  build, cambio Docker, retry del test ni operaciones remotas.

## Revisión y alcance

El test confirma el comportamiento de `clearServerAuthCookies` para varios
chunks y code verifier. No cambia el BFF. LOCAL-09/G09-T05 avanza, pero siguen
pendientes expiración real de Auth en browser y concurrencia de refresh
end-to-end. No cambia el porcentaje de gate ni autoriza conclusión GO. La prueba
no tuvo ventana gráfica, por lo que no genera captura/video funcional.
