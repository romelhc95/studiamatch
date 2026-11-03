# G07 — C03 integrado R22 y diagnóstico R23

## R22: el grant corrigió el primer bloqueo; el siguiente predicado de Pages falló

- Candidato: rama `feat/h3req1-sync-20261002`, HEAD baseline
  `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- Driver R22 y manifiesto: `tests/h3req1_c03_integrated_drill_r22.sh`, 77/77;
  SHA del manifiesto `62ce09c082d9990fe9518aff8b94062a9de22786f0645d7968fa38e9781021b7`.
- Log sanitizado: [R22](h3req1_c03_integrated_run_2026-10-10_r22.txt), SHA-256
  `c6de00c806d76e63b8efce92eefef579e381d7d80c175c5111e10cd19336f496`.
- Resultado: **exit 1**, fase `safe-suspend-and-runtime-denials`, control
  `/control/pages-suspended`, tipo `AssertionError`.

R22 superó snapshot íntegro, cachés fijadas read-only, PostgreSQL 17.11,
bootstrap H2-Pro→H3, setup integrado de cuota/gateway, fixture de invitación
in-flight, readiness PostgREST y login workerd (`aal2`, cookies sintéticas). El
Edge leyó `admin_members` después de la migración aditiva
`20261010_h3_admin_members_service_select.sql`; no volvió a aparecer el 403/42501.
La reserva sintética se confirmó antes de mantener el request Auth in-flight y
`h3req1_safe_suspend.sql` pasó. El fallo ocurrió en la comprobación Pages antes
de los controles Edge suspendido, dispatcher, finalización, resume y recuperación.

El control previo no identificaba cuál status, header o cookie había discrepado.
No se atribuye aún a producto. La solicitud de Auth estaba interceptada por el
gateway sintético local; no hubo correo ni llamada a servicios remotos. El PGDATA
era tmpfs y no se considera evidencia recuperable después de detener PG17.

Al fallar, el runner detuvo cinco contenedores del run por sus IDs etiquetados;
conservó contenedores, snapshot, TLS sintético, redes internas, imágenes y cachés.
`studiamatch-dev` permaneció `running/healthy`. No hubo cleanup de recursos R22.

## Diagnóstico acotado y R23

Se cambió solo el harness de `tests/h3req1_c03_integrated_runtime.mjs` para que
cada predicado de Pages falle con un código fijo `PAGES_*` (ruta lógica, status,
header o índice de cookie), sin incluir valores, path de usuario, texto de
assertion ni contenido de respuesta. La allowlist se limita a
`PAGES_SUSPEND_CONTRACT_FAILED`; el identificador del predicado tiene patrón
cerrado. El código funcional no se modificó.

R23 fijó las fuentes nuevas en el manifiesto SHA-256
`053649f5a2e21cf6b86435fef1ffb584d22767a61e46092b58cc182dfd900090`. Fue
consumido con exit 1 durante `verify-preserved-r4-dependency-caches-read-only`,
antes de snapshot o servicios: el volumen Miniflare R4 estaba montado por un
contenedor de diagnóstico efímero `139778ff488d` (`node --input-type=module`).
La metadata confirmó que ese contenedor fue creado en esta sesión para la sonda
aislada; se detuvo ese ID exacto y su `--rm` lo retiró. Después no hubo consumers
activos de los cuatro caches. No se tocó cache ni servicio persistente.

La primera sonda ad hoc también se detuvo: su configuración mínima omitía un
service binding; la segunda no terminó de iniciar su Miniflare aislado dentro de
la ventana acotada. Ambas son fallos del diagnóstico auxiliar, no evidencia del
comportamiento Pages. Sus contenedores efímeros exactos se detuvieron; no se
retiraron recursos del proyecto. La comprobación siguiente debe volver a usar
el contexto de workerd integrado fijado por el runner, con el nuevo código
allowlisted, antes de corregir el componente funcional.

## Gates y métrica

- G01–G06: completos según evidencia vigente.
- G07: parcial; SQLSTATE 42501 corregido localmente y el flujo avanza hasta una
  aserción Pages aún no clasificada.
- G08–G09: pendientes; UAT 144/0 retries y onboarding 10/10 no ejecutados.
- G10: pendiente remoto y fuera de esta autorización local.
- No cambia la métrica: histórico G01–G10 **60%**; cierre local G01–G09
  **6/9 = 66.67%**. Ninguno de estos runs cerró un gate completo.
