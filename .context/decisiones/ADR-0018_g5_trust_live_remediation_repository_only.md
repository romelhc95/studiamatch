# ADR-0018 - Remediacion Repository-Only Del Trust Live G5

| Campo | Valor |
|---|---|
| Estado | `ACCEPTED_REPOSITORY_ONLY` |
| Fecha | 2026-08-16 |
| Subfase | `F10.9` |
| Alcance | PR H repository-only |
| Operacion remota | `NO` |

## Contexto

E1 termino `E1_DEPLOYMENT_PASS` y dejo un Worker/Durable Object bootstrap aislado
valido. La evidencia remota queda registrada solo de forma sanitizada: version
logica, binding, clase, migration tag, digests y flags de exposicion disabled. La
credencial E1 queda atestada como `E1_CREDENTIAL_REVOKED_AND_LOCAL_REMOVED`.

Ese bootstrap no acredita trust operacional: no hay GitHub App configurada, no hay
OIDC live, no hay endpoint aprobado, no hay bindings runtime exactos y no hubo smoke
trust-only. E2-E6 permanecen `NOT_EXECUTED`.

## Decision

La autoridad SHA/tree/blob deja de vivir como constantes finales en el repositorio.
La autoridad operacional futura sera un policy runtime compuesto exclusivamente por:

- `G5_ALLOWED_CANDIDATE_SHA`.
- `G5_ALLOWED_CANDIDATE_TREE`.
- `G5_ALLOWED_WORKFLOW_BLOB_SHA`.

La secuencia obligatoria resuelve la autorreferencia:

1. Se promociona primero el commit diagnostico a `main`.
2. Se leen de esa promocion el SHA, tree y blob exactos.
3. Se configuran esos bindings exactos en un gate posterior.
4. El broker consume esos bindings como policy inmutable.
5. Ningun caller puede aportar SHA/tree/blob ni reemplazar la policy.

El broker termina STOP si falta cualquier binding runtime, si el runtime flag no es
`G5_TRUST_RUNTIME_ENABLED=true`, si la GitHub App config esta incompleta, si el
endpoint no fue aprobado, si el workflow no proviene de `main` o si
`run_attempt != 1`.

El fallback a SHA/tree/blob antiguos queda prohibido. Los valores legacy pueden
existir solo como denylist de rechazo, no como autoridad.

## Adapter Live

`G5ConnectedGithubAppAdapter` queda implementado pero disabled por defecto. Solo
puede operar cuando existen todos los bindings runtime exactos, GitHub App config
completa, endpoint aprobado y `G5_TRUST_RUNTIME_ENABLED=true`.

La GitHub App live queda limitada a consultas read-only:

- workflow run;
- jobs/checks;
- deployments;
- environment;
- approvals;
- commit/tree;
- workflow blob.

Toda llamada GitHub write queda prohibida. El unico POST permitido es el exchange de
installation token contra el endpoint de la instalacion y con permisos read-only. La
private key, JWT e installation token no se registran ni se devuelven.

JWKS de GitHub se obtiene con issuer/audience exactos, cache limitado, timeout,
size limit y fail-closed.

## Orden Operacional

La secuencia anterior E4-before-E5 queda
`E4_BEFORE_E5_SUPERSEDED_NOT_EXECUTABLE`. El orden vigente es:

| Gate | Alcance | Estado |
|---|---|---|
| `E1` | Bootstrap Cloudflare Worker/Durable Object aislado | `COMPLETED` |
| `E2` | GitHub App read-only | `NOT_EXECUTED` |
| `E3` | Environment Production disabled | `NOT_EXECUTED` |
| `E4` | Promocion diagnostica Certification/Main | `NOT_EXECUTED` |
| `E4A` | Binding exacto SHA/tree/blob y redeploy aislado | `NOT_EXECUTED` |
| `E4B` | Exposicion endpoint | `NOT_EXECUTED` |
| `E5` | Smoke trust-only sin data plane | `NOT_EXECUTED` |
| `E6` | Creacion, aprobacion y consumo G5 | `NOT_EXECUTED` |

E5 queda bloqueado sin promocion, binding exacto y endpoint aprobado.

No se puede combinar E2, E3, E4, E4A, E4B, E5 o E6 en una sola autorizacion ni
usar E1 como autorizacion implicita de trust operacional.

## Consecuencias

- El Worker remoto permanece sin cambios en PR H.
- No se usan credenciales Cloudflare.
- No se configura GitHub App, secrets, variables o environments.
- No se solicita OIDC live.
- No se ejecuta `workflow_dispatch`.
- No se accede a Production, Supabase o fuentes.
- No se ejecuta SQL, writers o schedules.
- Hito 1 `60%`, F10.9 `38%` y G5 `50%` se mantienen como tracking-only.
