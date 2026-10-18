# G07 — C03 integrado R20

## Identidad y evidencia

- Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`.
- Rama `feat/h3req1-sync-20261002`; HEAD baseline
  `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- Runner `tests/h3req1_c03_integrated_drill_r20.sh`; manifiesto 71 entradas,
  SHA-256 `fcccd29bf59bff816bd06d786144e09dabeedf67c165f5422f71a7d377ecb721`.
- Log sanitizado [R20](h3req1_c03_integrated_run_2026-10-10_r20.txt), exit **1**,
  SHA-256 `54ec73abd1ecd9a5364c24875823223008c9b353f257236944137d71e1dc8efd`.
- Edge system/synthetic CA bundle SHA-256
  `4f83094f476d5213a2d82a4cdbbc4374b6fdd5c6ae68b225d904c6bb152895f1`.

## Etapas con PASS

- Docker target: context `default`, endpoint unix local, engine esperado 29.8.2.
- Manifiesto/snapshot: 71/71; no `.env*`, symlinks ni dependencias privadas.
- PG17 pinned image: versión 17.11.
- Safety contract R20 y verificación de cachés R4: PASS.
- H2-Pro→H3 schema bootstrap, setup de quota/gateway y fixture editorial/in-flight:
  SQL `psql` exit 0 cada uno.
- PostgREST readiness: PASS.
- Bundle TLS sintético/de sistema: creado en tmpfs y SHA registrado.
- Pages/workerd login: `aal2`, auth cookie y activity cookie presentes.
- El Edge autenticó sesión y llamó el endpoint de membresía; counters no muestran
  rechazo de API key, sesión ni gateway.

## Fallo y alcance

Fase `real-edge-invite-held-after-reservation`; exit **1**; predicado
`INVITE_EARLY_UNAUTHORIZED`. El resumen allowlisted de la misma solicitud fue:

```text
authUserRequests=2
authUserAccepted=2
adminMemberRequests=1
adminMemberCredentialRejected=0
adminMemberFailureResponses=1
adminMemberLastStatus=403
functionRequests=1
functionCredentialRejected=0
functionSessionRejected=0
functionCalls=1
requestAdmission=0
invitationReserve=0
```

El transporte TLS y Auth ya están acreditados. `admin_members` respondió HTTP 403
antes de admisión/reserva. El runner actual no conserva el código estructurado de
error PostgREST; no se atribuye todavía a RLS, grants, claims ni producto. No se
envió invitación/correo y no hubo mutación de reserva.

El driver detuvo cuatro servicios del run por sus IDs/labels. R20 PG17,
PostgREST, Edge y runtime están `exited`; las redes internas, el snapshot
allowlisted y el volumen TLS permanecen para inspección controlada. `PGDATA` fue
tmpfs; al detenerse el contenedor sus datos temporales no son recuperables. No se
tocaron cachés R4, imágenes, `studiamatch-dev` ni otros recursos. `studiamatch-dev`
sigue healthy en `studiamatch-h3req1:20261009-v3`.

## Siguiente diagnóstico

Añadir al harness únicamente la captura del campo `code` de la respuesta
PostgREST, limitada a `PGRSTddd` o SQLSTATE de cinco caracteres; no guardar
`message`, `details`, `hint` ni cuerpos. Ejecutar el fixture nuevo sobre PG17
efímero con el mismo schema y una sola invitación sintética. Corregir el grant,
policy, fixture o contrato solo si el código estructurado y el SQL demuestran la
causa. No reintentar la invitación sobre el estado detenido.

G07 sigue parcial, sin delta de puntos: tablero G01–G10 **60%**; cierre local
G01–G09 **6/9 = 66.67%**. La ejecución R20 no cierra G07 ni autoriza un GO.
