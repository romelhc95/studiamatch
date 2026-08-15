# ADR-0013 - Trust Broker G5 Y Ledger Durable Object

| Campo | Valor |
|---|---|
| Estado | `ACCEPTED_REPOSITORY_ONLY` |
| Subfase | `F10.9` |
| Proveedor futuro | `Cloudflare Worker + Durable Object` |
| Deployment | `NOT_EXECUTED` |
| Gate real | `NOT_CREATED_NOT_APPROVED_NOT_CONSUMED` |
| Trust operacional | `STOP_G5_TRUST_VERIFICATION_NOT_IMPLEMENTED` |
| Connected mode | `STOP_G5_CONNECTED_MODE_NOT_IMPLEMENTED` |

## Contexto

PR #384 quedo `MERGED_POST_MERGE_VERIFIED` en
`desarrollo@7a4c6420214dd1ffcc367b1f35cb5f553d07c99c` / tree
`4c647e87a4effbc577d1653fd023375c2c87fa3e`: Security
`31899873186=PASS`, focused trust-plane `95048814844=PASS` y F9.7 run
`31899873143` / job `95048918881=PASS`, `run_attempt=1`.

PR A cerro el modelo de autoridad pero no implemento un coordinador serializable.
G5 necesita una identidad por gate, consumo single-use, replay de nonce/`jti`,
expiracion y receipt inmutable sin acoplar el ledger al data plane.

## Decision

Se selecciona un Cloudflare Worker como trust broker futuro y un unico Durable
Object coordinador como ledger CAS externo. Dentro de ese coordinador, cada gate
usa una clave de identidad derivada de
`repository_id/run_id/run_attempt/check_run_id/environment_id/deployment_id`.
Dentro de una transaccion serializada, la unica secuencia valida es:

```text
ABSENT -> READY -> CONSUMED
```

`READY` solo deriva de evidencia exact-one consultada por un adapter GitHub App
read-only. Estado del gate, nonce y `jti` se reservan junto con el receipt dentro de
la misma transaccion serializada; no existe una ventana entre dos Durable Objects.
La frontera RPC valida shape y tipos exactos antes de tocar storage. Los resultados
del adapter deben declarar `complete=true` para demostrar que exact-one se evalua
sobre el conjunto completo. El ledger falla cerrado al alcanzar 10.000 registros;
no compacta ni elimina replay/tombstones en este alcance repository-only.
`READY` y `CONSUMED` pueden persistirse en una transaccion, pero el
receipt conserva ambas transiciones. El primer consumo crea un receipt inmutable;
todo consumo posterior termina `STOP_G5_REPLAY_DETECTED`. Una falla del diagnostico
despues del CAS no revierte `CONSUMED`. Expiracion crea tombstone `EXPIRED`; cleanup
no elimina el tombstone ni permite resurreccion.

El broker verifica offline JWT RS256 contra JWKS inyectado: issuer GitHub,
audience dedicada, firma, `exp/nbf/iat`, repository/owner IDs, ref main protegida,
workflow ref/SHA, candidate SHA, run/attempt, environment Production y `actor_id`.
Bindings no emitidos por OIDC se resuelven por consultas GitHub App read-only al
mismo run: ref protegida, triggering actor, check/job, deployment, environment,
approval/reviewer, commit/tree y workflow blob. El nonce del broker se deriva de
`jti/repository_id/run_id/run_attempt`; no se inventa un claim GitHub. El request
solo contiene bearer OIDC y `runId/expectedRunAttempt`
como referencia no autoritativa.

El adapter expone interfaces read-only cerradas que corresponden a consultas
autoritativas: workflow run, jobs del run, deployments por SHA/environment,
environment, approvals del run/deployment, commit con tree y contenido del workflow
con blob/ref. El broker realiza los joins; los fixtures no aportan un objeto de
autoridad final. Una policy interna separada congela repository, workflow ref,
candidate SHA/tree y workflow blob. Si GitHub no permite obtener una relacion
exact-one con permisos read-only, el futuro connected gate termina STOP.

## Lo Que No Es CAS

Ninguna de estas superficies constituye por si sola un ledger atomico single-use:

- environment approval prueba una decision, no compare-and-set;
- deployment ID identifica un deployment, no serializa consumidores;
- artifacts y cache son blobs reemplazables o eventualmente disponibles;
- `concurrency` coordina ejecuciones, pero no produce receipt durable ni replay
  ledger;
- variables y comments son metadata mutable sin transaccion;
- custom deployment protection rules serian un gate externo, pero no se crean en
  este PR.

## Limites

- Supabase, SQL, DDL, RPC, grants, credenciales DB y data plane quedan fuera.
- GitHub App futuro: `Actions: read`, `Checks: read`, `Contents: read`,
  `Deployments: read`, `Metadata: read`; todo write prohibido.
- Worker y Durable Object no tienen permisos write sobre GitHub.
- No hay account ID, app ID, URL privada, secret real, installation token, JWKS
  live, API GitHub live, deployment, billing ni configuracion remota.
- No se crea workflow manual G5, environment, protection rule, branch rule ni
  repository secret.
- El archivo Wrangler es solo configuracion local separada con `workers_dev=false`.

## Fronteras

1. Workflow GitHub futuro obtiene bearer OIDC, pero no decide autoridad.
2. GitHub OIDC prueba identidad criptografica y claims emitidos.
3. GitHub App read-only completa evidencia no presente en OIDC.
4. Trust broker liga ambas fuentes y deriva identidad.
5. Un Durable Object coordinador serializa por clave de identidad
   `ABSENT -> READY -> CONSUMED`, replay global y expiracion.
6. Connected collector futuro solo podria iniciar despues de un gate posterior;
   hoy termina antes de transporte.

## Logging Y Output

No se registran JWT, Authorization, installation tokens, URLs, hosts, UUID,
project refs, payloads, claims completos ni datos operativos. La salida publica se
limita a version, decision, reason code, receipt digest y flags sanitizados.
Secrets futuros se documentan solo por nombre, sin valores ni defaults:
`G5_GITHUB_APP_PRIVATE_KEY`, `G5_GITHUB_APP_ID`, `G5_OIDC_AUDIENCE`.
