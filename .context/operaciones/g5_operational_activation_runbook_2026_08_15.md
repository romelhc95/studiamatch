# F10.9 G5 - Runbook De Activacion Operacional Por Gates Separados

| Campo | Valor |
|---|---|
| Estado | `PREPARED_NOT_CONFIGURED` |
| Subfase | `F10.9` |
| Alcance | PR E repository-only |
| Manifest | [`g5_operational_activation_manifest_2026_08_15.json`](./g5_operational_activation_manifest_2026_08_15.json) |
| Preflight offline | `scripts/shared/f10_9_g5_operational_activation_preflight.py` |
| Gate actual | `NOT_CREATED_NOT_APPROVED_NOT_CONSUMED` |
| Trust actual | `STOP_G5_TRUST_VERIFICATION_NOT_IMPLEMENTED` |
| Connected actual | `IMPLEMENTED_DISABLED_NOT_CONFIGURED` |
| Operacion remota | `NO` |

## Proposito

Este runbook prepara, sin ejecutar, la secuencia futura para activar G5 de forma
operacional. PR E no despliega Cloudflare, no configura GitHub App, no modifica
environments, no solicita OIDC live, no ejecuta Production, no accede a Supabase
o fuentes, no ejecuta SQL y no crea writers o schedules.

La reconciliacion PR #387 queda clasificada como
`MERGED_POST_MERGE_VERIFIED_WITH_INFRA_RETRY`:

```text
candidate = d62c8969e7d229bb8d2a9e1f8c6db6a1c4ef4d1d
merge = bd0d82864c26755435e551b835d145b864383810
tree = 135af5a95237a1d4d6e1b977e8bb9ab82ac95e16
security = 31912540519=PASS
focused_pr_d = 95079685172=PASS
m3 = 95079685191=PASS
f9_7_run = 31912540528
attempt_1_job = 95079764790=CANCELLED
attempt_1_classification = CI_INFRA_TIMEOUT_PLAYWRIGHT_APT
attempt_2_job = 95084155346=PASS
attempt_2_classification = CI_RETRY_PASS
attempt_2_run_attempt = 2
```

`run_attempt=2` pertenece solo al retry CI de F9.7. El gate G5 operacional futuro
mantiene `run_attempt=1` obligatorio para evitar replay, partial rerun o aprobacion
ambigua. El retry CI no constituye gate G5 operacional.

## Nombres Repository-Only

El manifest registra solo nombres futuros, sin valores:

- `G5_GITHUB_APP_PRIVATE_KEY`.
- `G5_GITHUB_APP_ID`.
- `G5_OIDC_AUDIENCE`.
- `G5_TRUST_BROKER_ENDPOINT`.
- `G5_TRUST_OPERATIONAL_ENABLED`.

`G5_TRUST_OPERATIONAL_ENABLED` permanece `ABSENT_NOT_CONFIGURED`. Este runbook no
incluye identificadores numericos remotos, direcciones reales, installation IDs,
project refs, tokens, secrets, claves ni material privado.

## Permisos Futuros Minimos

GitHub App read-only:

| Permiso | Acceso |
|---|---|
| Actions | `read` |
| Checks | `read` |
| Contents | `read` |
| Deployments | `read` |
| Metadata | `read` |

Todo permiso GitHub App `write` queda prohibido.

Workflow:

| Permiso | Acceso |
|---|---|
| `contents` | `read` |
| `actions` | `read` |
| `deployments` | `read` |
| `id-token` | `write` |

Todo otro permiso workflow `write` queda prohibido. La rama futura debe ser
`main`, la ref `refs/heads/main` y el environment `Production`.

## Separacion Trust Plane / Data Plane

Cloudflare Worker y Durable Object pertenecen al trust plane G5. El trust plane
solo valida identidad, receipt, nonce, `jti`, gate single-use y reason codes. No
lee ni escribe data plane, no consulta Supabase por si mismo y no reemplaza los
guards del collector GET-only. El data plane permanece fuera hasta un gate futuro
con aprobacion separada.

## Gate E1 - Deployment Cloudflare Worker/Durable Object

Precondiciones:

- PR E fusionado y CI repository-only PASS.
- ADR-0016 aceptada en `desarrollo`.
- Versiones congeladas: `f10.9-g5-trust-broker.v2` y `repository-only-v1`.
- Sin Production y sin data plane.

Outputs sanitizados:

- Version del Worker.
- Nombre logico del Durable Object.
- Digest de deployment, sin direccion real ni identificador remoto.

Rollback:

- Deshabilitar ruta o binding futuro.
- Restaurar version previa del Worker.
- Preservar ledger y receipts para auditoria.

STOP:

- Binding faltante o inesperado.
- Version no congelada.
- Cualquier intento de route/domain/deployment fuera del gate E1 aprobado.

## Gate E2 - GitHub App Read-Only

Precondiciones:

- Evidencia E1 revisada.
- Matriz read-only aprobada.
- Ningun permiso `write` solicitado.

Outputs sanitizados:

- Matriz de permisos.
- Alias del app, sin identificador numerico.
- Inventario de nombres, sin valores.

Rollback:

- Revocar instalacion futura.
- Retirar nombre de clave configurada.
- Conservar nota de auditoria sanitizada.

STOP:

- Cualquier permiso `write`.
- Alcance de repositorio inesperado.
- Material privado no revisado o expuesto.

## Gate E3 - Environment Production

Precondiciones:

- Evidencia E2 revisada.
- Branch policy `main` confirmada por nombre.
- Reviewer humano requerido y self-review bloqueado.
- `G5_TRUST_OPERATIONAL_ENABLED` sigue ausente antes de este gate.

Outputs sanitizados:

- Inventario name-only de variables/secrets.
- Estado de reviewer policy.
- Estado disabled por defecto.

Rollback:

- Remover `G5_TRUST_OPERATIONAL_ENABLED`.
- Retirar nombres de configuracion agregados.
- Restaurar estado disabled.

STOP:

- Branch distinta de `main`.
- Environment distinto de `Production`.
- Flag operacional habilitado antes de autorizacion E6.

## Gate E4 - Smoke Test Trust-Only Sin Production

Precondiciones:

- E1-E3 revisados.
- Sin target data plane configurado.
- Solo trust broker y ledger disponibles.

Outputs sanitizados:

- Reason code de trust.
- Receipt digest.
- Prueba de no acceso data plane.

Rollback:

- Deshabilitar flag operacional.
- Expirar gate de smoke.
- Conservar receipts sanitizados.

STOP:

- Intento de data plane.
- Receipt ausente o ambiguo.
- Capacidad write detectada.

## Gate E5 - Promocion Diagnostica Certification/Main

Precondiciones:

- E4 PASS.
- Reviews protegidas frescas.
- Alcance diagnostico, sin Production operacional.

Outputs sanitizados:

- Commit y tree.
- Nombres de required checks.
- Decision de promocion diagnostica.

Rollback:

- Revertir PR diagnostico si corresponde.
- Mantener G5 disabled.
- Bloquear gate sucesor.

STOP:

- Approval stale.
- Tree drift.
- Job Production inesperado.

## Gate E6 - Creacion, Aprobacion Y Consumo G5

Precondiciones:

- E5 PASS.
- Approval manual listo.
- `run_attempt=1` obligatorio.
- Gate `READY` no consumido.

Outputs sanitizados:

- Digest de identidad del gate.
- Receipt digest.
- Reason code final.

Rollback:

- Preservar gate consumido aunque falle el diagnostico posterior.
- Deshabilitar flag operacional.
- Abrir remediacion repository-only si hay ambiguedad.

STOP:

- `run_attempt != 1`.
- Approval mismatch.
- Receipt replay o consumo ambiguo.

## Regla De No Combinacion

E1, E2, E3, E4, E5 y E6 requieren autorizaciones separadas. No se puede combinar
deployment, GitHub App, environment y Production en una sola autorizacion. Un gate
PASS no concede el siguiente.

Un gate PASS no concede el siguiente.

## Preflight Offline

El preflight offline valida solo:

- presencia futura por nombre;
- formato no sensible de nombres;
- permisos exactos;
- branch `main`;
- environment `Production`;
- versiones congeladas;
- ausencia de writes y operaciones remotas.

El preflight no lee valores reales, no consulta variables de entorno, no realiza red
y no prueba disponibilidad operacional. Su salida PASS solo significa que el paquete
repository-only no contiene configuracion sensible ni combinacion de gates.
