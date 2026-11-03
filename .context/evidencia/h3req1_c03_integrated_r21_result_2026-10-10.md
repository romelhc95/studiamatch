# G07 — Resultado C03 integrado R21

## Identidad y resultado

- Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
  `feat/h3req1-sync-20261002`, HEAD baseline
  `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- Driver: `tests/h3req1_c03_integrated_drill_r21.sh`; manifiesto 74/74,
  SHA-256 `67000ea1881bc584898ee279d9ac4a0eaaf3835f673c3e5c4a406578d179e19f`.
- Ejecución bajo la autorización local explícita del 2026-10-10: una corrida,
  sin retry; exit **1** en `real-edge-invite-held-after-reservation`.
- Log sanitizado [R21](h3req1_c03_integrated_run_2026-10-10_r21.txt), SHA-256
  `37b590faf64a46a56321e4eeb2294efb0029eb347724b3f782febaf0cfd2d9f2`.

## Gates parciales acreditados en esta corrida

- Snapshot integrado allowlisted: 74/74, sin symlinks ni `.env*`.
- PG17 fijado: versión 17.11; bootstrap H2-Pro→H3, fixture SQL integrado,
  cuota/gateway y PostgREST readiness: PASS.
- Pruebas del contrato del runner R21: 22/22; cachés R4 y dependencias fijadas: PASS.
- Pages/workerd login: `aal2`, cookie de sesión y activity cookie presentes.
- Edge completó validación Auth y consultó `admin_members`; no hubo rechazo de
  API key ni de sesión.

## Bloqueo demostrado

Fase `real-edge-invite-held-after-reservation`, exit 1,
`INVITE_EARLY_UNAUTHORIZED`. La captura estructurada y allowlisted fue:

```text
adminMemberRequests=1
adminMemberCredentialRejected=0
adminMemberFailureResponses=1
adminMemberLastStatus=403
adminMemberLastCode=42501
requestAdmission=0
invitationReserve=0
```

SQLSTATE `42501` demuestra insuficiencia de privilegio en la lectura PostgREST.
No identifica por sí solo si el permiso faltante es de relación/columna, una vista,
o el rol efectivo. No atribuir aún a policy RLS ni a la lógica de invitación.
No hubo admisión, reserva ni llamada de correo. Se detuvieron cuatro servicios
R21 exactos (`Edge exit 15`, `PostgREST 255`, `PG17 0`, runtime 143); PGData
tmpfs no persiste. Snapshot/cachés, TLS volume y dos redes internas R21 permanecen;
los seis contenedores exactos R21 figuran `exited`. No se retiró ningún recurso.
`studiamatch-dev` sigue `running/healthy` con imagen
`sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63`.

## Siguiente diagnóstico

Contrastar el código SQLSTATE con el rol efectivo configurado en el cliente Edge,
la consulta `admin_members(user_id,role,is_active,account_status)` y los grants
efectivos de tabla/columnas en el schema reproducido. Ejecutar únicamente consultas
de catálogo/privilegios en PG17 desechable (nunca DB remota). Determinar el objeto
preciso antes de modificar permisos, harness o contrato; no repetir R21 intacto.

G07 sigue parcial y no suma puntos. Métricas: tablero histórico G01–G10 **60%**;
cierre local G01–G09 **6/9 = 66.67%**. G08/G09 siguen pendientes; G10 remoto
permanece fuera de esta autorización.
