# G07 R15 — login PASS; timeout esperando la retención de invitación

## Resultado

- Candidato: `feat/h3req1-sync-20261002` @ `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- Manifiesto: SHA-256 `bbe4a9c0f39fc2e066bb19d0f3bc6f0413ee7d5e5913b2b4a2c959be1512624d`; 65/65.
- Log R15: [integrated run](h3req1_c03_integrated_run_2026-10-10_r15.log), SHA-256 `0dcd11f0a3de7ff12dc5ac7628c1cde65afed1c1ae5ef279044b8c6f2c6a159a`.
- Exit externo 124 / phase `real-edge-invite-held-after-reservation`.
- Login integrado: PASS; `aal=aal2`, auth cookie y activity cookie presentes.
- Luego `trigger-inflight` esperó 60 s por el evento que confirma que la llamada sintética alcanzó Auth. El límite interno del control expiró (exit 124) antes de producir ese evento. No se ejecutó la aserción SQL de reserva, ni suspensión, rechazo, finalización in-flight, recuperación o smoke final.

## Prerrequisitos que sí pasaron

Docker Desktop objetivo, rama/HEAD y manifiesto; snapshot/cache de dependencias; PG17.11; bootstrap H2-Pro→H3; esquema local de cuotas/dispatcher; fixture editorial/in-flight; PostgREST readiness y arranque Edge activo. Estos PASS parciales no cierran G07.

El failure-stop detuvo únicamente los cuatro servicios de aplicación identificados por las etiquetas y nonce R15. PostgreSQL salió 0 al detenerse, PostgREST 255 y runtime 143; esos exits son posteriores al stop y no constituyen la causa. Los contenedores/redes se preservan. No se avanzó a otros gates.

## Causa del diagnóstico incompleto

`triggerInFlight()` solo esperaba `inviteStarted`. Si la petición BFF/Edge terminaba temprano con error antes de la llamada Auth, el runner no observaba su status ni `error.code`; quedaba bloqueado hasta que el timeout exterior de 60 s del `docker exec` interrumpía el diagnóstico. Esto es una limitación demostrada del harness, no una causa demostrada de la respuesta integrada.

## Corrección enfocada

Actualizar `waitForInviteHold` para competir contra la resolución/rechazo de `inFlightInvite`, emitir únicamente status HTTP o códigos fijos allowlisted, y limitar la espera diagnóstica a 30 s para devolver código antes del timeout del exec. Mantener el hold real como requisito del gate y detener el flujo ante cualquier respuesta temprana. No usar body/texto/mensaje crudo. Después ejecutar R16 con recursos nuevos para obtener el predicado real.
