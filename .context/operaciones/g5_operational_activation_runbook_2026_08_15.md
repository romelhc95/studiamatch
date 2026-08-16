# F10.9 G5 - Runbook De Activacion Operacional Por Gates Separados

| Campo | Valor |
|---|---|
| Estado | `PREPARED_NOT_CONFIGURED` |
| Subfase | `F10.9` |
| Alcance | PR E + PR F + PR G repository-only |
| Manifest | [`g5_operational_activation_manifest_2026_08_15.json`](./g5_operational_activation_manifest_2026_08_15.json) |
| Preflight offline | `scripts/shared/f10_9_g5_operational_activation_preflight.py` |
| Gate actual | `NOT_CREATED_NOT_APPROVED_NOT_CONSUMED` |
| Trust actual | `STOP_G5_TRUST_VERIFICATION_NOT_IMPLEMENTED` |
| Connected actual | `IMPLEMENTED_DISABLED_NOT_CONFIGURED` |
| Operacion remota | `NO` |

## Proposito

Este runbook prepara, sin ejecutar, la secuencia futura para activar G5 de forma
operacional. PR E, PR F y PR G no despliegan Cloudflare, no configuran GitHub App, no modifican
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

La reconciliacion PR #388 queda clasificada como `MERGED_POST_MERGE_VERIFIED`:

```text
candidate = eb052c2755937a2bf239cd778bc814274fbc846f
merge = 71d6640b990b934fa02401518650ec38dca6cae4
tree = 815a2316c8de67047567d89a9928576869f43c4f
security = 31917838025=PASS
f9_7_run = 31917838011=PASS
focused = 95092629457=PASS
f9_7_job = 95092706912=PASS
run_attempt = 1
```

El preflight operacional read-only de cuenta queda `E1_ACCOUNT_READINESS_GO`, con
Workers existentes `0` y deployment `NOT_EXECUTED`. PR F registra
`E1_DEPLOYMENT_STOP_REPOSITORY_HARDENING_REQUIRED` para endurecer el paquete antes
de solicitar deployment real.

La reconciliacion PR #389 queda clasificada como `MERGED_POST_MERGE_VERIFIED`:

```text
candidate = f48d0f25154970531744815e1d3769a20731717a
merge = 4bdc698cd9a8569e4e8290257effa6bc3aa3bb15
tree = 874ccffa3db9871189ca351d88cc84e120251e95
security = 31921056993=PASS
f9_7_run = 31921056963=PASS
focused = 95100885045=PASS
f9_7_job = 95100958336=PASS
run_attempt = 1
```

El hallazgo `E1_DEPLOYMENT_STOP_WRANGLER_FLAG_INCOMPATIBLE` queda registrado:
Wrangler `4.30.0` no expone `deploy --strict`, por lo que PR G fija Wrangler
exacto `4.44.0` y exige dry-run offline sin credenciales Cloudflare. E1 sigue
`NOT_EXECUTED` hasta autorizacion separada.

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

- PR F y PR G fusionados y CI repository-only PASS.
- ADR-0016 aceptada en `desarrollo`.
- [ADR-0017](../decisiones/ADR-0017_g5_e1_cloudflare_deployment_hardening.md) aceptada en `desarrollo`.
- Versiones congeladas: `f10.9-g5-trust-broker.v2` y `repository-only-v1`.
- Wrangler exacto `4.44.0` instalado desde lockfile dentro del contenedor.
- `wrangler.repository-only.jsonc` mantiene `workers_dev:false` y `preview_urls:false`.
- Cero routes, domains, custom domains, preview URLs o triggers.
- Dry-run obligatorio completado offline antes de deployment, sin `CLOUDFLARE_API_TOKEN` ni `CLOUDFLARE_ACCOUNT_ID`.
- Sin Production y sin data plane.

Comando dry-run obligatorio previo:

```bash
wrangler deploy --strict --config wrangler.repository-only.jsonc --dry-run --outdir /tmp/studiamatch-g5-e1-dry-run
```

Comando deployment futuro exacto:

```bash
wrangler deploy --strict --config wrangler.repository-only.jsonc
```

Flags prohibidos en E1: `--temporary`, `--route`, `--routes`, `--domain`,
`--triggers`, `--schedule`, `--schedules`, `--env-file`, `--secrets-file`,
`--keep-vars` y autoconfiguracion. Los nombres de
credencial E1 son exclusivamente `CLOUDFLARE_API_TOKEN` y
`CLOUDFLARE_ACCOUNT_ID`. `CF_API_TOKEN` y `CF_ACCOUNT_ID` permanecen solo para
usos legacy existentes fuera de E1. Wrangler consumira credenciales durante E1,
pero no puede imprimirlas, retornarlas ni persistirlas.

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
- `deploy --strict` no soportado por Wrangler congelado.
- `workers_dev` distinto de `false` o `preview_urls` distinto de `false`.
- Cualquier intento de route/domain/trigger/deployment fuera del gate E1 aprobado.
- Cualquier prompt de billing, plan o costo.

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

## Gate E3A - Exposicion Del Endpoint Del Trust Broker

Estado: `DEFINED_NOT_EXECUTED`.

Precondiciones:

- Evidencia E1 revisada con Worker aislado y no accesible publicamente.
- Evidencia E2 y E3 revisada.
- Ningun endpoint seleccionado o habilitado por PR F.

Opciones futuras, con autorizacion separada:

- workers.dev explicito y temporal.
- route/custom domain protegido.

Outputs sanitizados:

- Decision de estrategia de endpoint.
- Estado temporal de exposicion.
- Requisito de proteccion.

Rollback:

- Deshabilitar exposicion workers.dev.
- Retirar route/custom domain si se hubiera aprobado posteriormente.
- Mantener E1 aislado.

STOP:

- Endpoint seleccionado sin aprobacion E3A.
- Exposicion publica antes de E3A.
- Intento de E4 antes de E3A.

## Gate E4 - Smoke Test Trust-Only Sin Production

Precondiciones:

- E1-E3A revisados.
- E3A aprobado por separado.
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
- E3A no aprobado.
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

E1, E2, E3, E3A, E4, E5 y E6 requieren autorizaciones separadas. No se puede combinar
deployment, GitHub App, environment, endpoint y Production en una sola autorizacion. Un gate
PASS no concede el siguiente. E4 queda bloqueado hasta que E3A tenga aprobacion separada.

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
