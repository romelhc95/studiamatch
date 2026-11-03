# G09 delta R92–R93 — membresías concurrentes — 2026-10-11

## Candidato y runtime

- Checkout: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
  `feat/h3req1-sync-20261002`, HEAD baseline
  `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- Runner R93 `tests/h3_local_uat.mjs`, SHA-256
  `1b2b6b2a581a14ca336d1d125b6cf405b4d6b1382138a1f4e82e6793261aab6d`, igual
  al archivo montado en el contenedor driver.
- Pages/workerd: build normal R41, URL interna `http://localhost:3350`, su mock
  local en `:3351`, mismo PostgreSQL 17.11 sintético R12. El build R41 verifica
  126 artefactos; su fuente allowlisted R9 corresponde al candidato funcional
  probado. Chromium 1228 headless en Docker; no se abrió ventana.
- No se accedió a cuentas/datos reales, secretos operativos, egress o servicios
  remotos. Las mutaciones tocaron únicamente el miembro sintético y el bloque
  `finally` restauró su estado inicial.

## Resultados

| Corte | Resultado | Diagnóstico |
|---|---|---|
| R92 | Exit 1 antes de ejecutar mutaciones | Se apuntó al R12, cuya carpeta `site-out-r12` no contenía la región accesible presente en el source. La página Admin se renderizó, pero la espera de `role=region` falló. El artefacto R41 sí incluye `Membresías existentes`; el error es del runtime/export antiguo, no del test nuevo ni de `web/src`. Se preservan las tres capturas y el log. |
| R93 | Exit 0, H3-UAT-040 3/3 viewports, 19/19 assertions cada uno | Dos RPC de mutación concurrentes contra el mismo miembro se serializaron; el actor activo quedó admin y el objetivo terminó admin/inactivo. El intento posterior de degradar al único admin activo fue rechazado. El cleanup restauró la membresía original. Total 57/57, retries 0, cero errores de consola/requests. |

R93 amplía la concurrencia con dos solicitudes simultáneas del mismo actor; no
simula dos sesiones de Admin distintas. La cobertura del último-admin guard y
la serialización está demostrada para el escenario; el requisito de dos actores
distintos permanece pendiente hasta un ensayo SQL sintético aislado o sesiones
Admin independientes.

## Evidencia

- Desktop `h3req1_g09_uat_2026-10-10_r4/uat-membership-concurrency-r93/H3-UAT-040-desktop.png`, SHA-256 `c9c365b874e8a740749940ac272d06ea3712544390c3e072596e6a645ef61341`.
- Tablet `h3req1_g09_uat_2026-10-10_r4/uat-membership-concurrency-r93/H3-UAT-040-tablet.png`, SHA-256 `38c4f493c693451a79e387eafcbd57cb81ce25d4b6a6ed26af21eb7c3b1654e3`.
- Móvil `h3req1_g09_uat_2026-10-10_r4/uat-membership-concurrency-r93/H3-UAT-040-mobile.png`, SHA-256 `4a969f86e144c40fa8de7a28938fcd9b86464bf5a168720ea1427754caee87fb`.
- R93 manifest, JSON de ejecuciones y conteos en el mismo directorio; R92 rojo
  y capturas en `uat-membership-concurrency-r92/`.

LOCAL-10/G09-T06 avanza pero sigue parcial por falta del segundo actor. G09 y
ambas métricas permanecen abiertos/sin delta.

