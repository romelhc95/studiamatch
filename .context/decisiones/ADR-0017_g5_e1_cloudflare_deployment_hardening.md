# ADR-0017 - Hardening Repository-Only Para E1 Cloudflare

| Campo | Valor |
|---|---|
| Estado | `ACCEPTED_REPOSITORY_ONLY` |
| Fecha | 2026-08-16 |
| Subfase | `F10.9` |
| Alcance | PR F + PR G repository-only |
| Base protegida | PR #389 `MERGED_POST_MERGE_VERIFIED` |
| E1 account readiness | `E1_ACCOUNT_READINESS_GO` |
| Deployment | `NOT_EXECUTED` |
| Stop vigente | `E1_DEPLOYMENT_STOP_WRANGLER_FLAG_INCOMPATIBLE` |
| Operacion remota | `NO` |

## Contexto

PR #388 quedo fusionado en `desarrollo` y verificado post-merge:

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

El preflight operacional read-only de cuenta devolvio `E1_ACCOUNT_READINESS_GO`,
sin Workers existentes y con deployment `NOT_EXECUTED`. Esa lectura no autoriza
despliegue. Antes de solicitar E1 real se requiere congelar el paquete de
deployment para impedir rutas, preview URLs, endpoints o configuracion adicional.

PR #389 quedo fusionado en `desarrollo` y verificado post-merge:

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

El hallazgo posterior es fail-closed: Wrangler `4.30.0` no expone
`deploy --strict`, aunque el comando congelado de E1 lo exige. E1 queda
`E1_DEPLOYMENT_STOP_WRANGLER_FLAG_INCOMPATIBLE` hasta fijar una version compatible
sin ejecutar deployment.

## Decision

El deployment futuro de E1 queda limitado a un Worker aislado, sin exposicion
publica y sin endpoint seleccionado en este PR:

- Wrangler queda fijado a `4.44.0` en `workers/g5-trust-broker/package.json`.
- `package-lock.json` queda versionado para reproducibilidad.
- La regeneracion del lockfile debe usar solo el registry npm dentro del contenedor.
- La instalacion local de verificacion debe usar `npm ci --ignore-scripts` dentro del contenedor.
- `wrangler deploy --help` debe demostrar soporte de `--strict` antes de E1.
- El dry-run debe pasar sin `CLOUDFLARE_API_TOKEN`, sin `CLOUDFLARE_ACCOUNT_ID` y con egress externo bloqueado.
- `workers_dev` permanece `false`.
- `preview_urls` queda explicitamente `false`.
- No hay `routes`, `route`, `domains`, `custom_domains` ni `triggers` en la configuracion.
- E1 solo puede desplegar el Worker `g5-trust-broker-repository-only` con el Durable Object `G5_ATOMIC_LEDGER` y la clase `G5AtomicLedgerDurableObject`.
- La migracion permitida es unicamente `repository-only-v1` con `new_sqlite_classes`.

El comando futuro exacto de deployment es:

```bash
wrangler deploy --strict --config wrangler.repository-only.jsonc
```

Antes de cualquier deployment E1 debe ejecutarse un dry-run con outdir temporal:

```bash
wrangler deploy --strict --config wrangler.repository-only.jsonc --dry-run --outdir /tmp/studiamatch-g5-e1-dry-run
```

El dry-run debe verificar nombre, `main`, compatibility date, `workers_dev:false`,
`preview_urls:false`, cero routes/domains/triggers, binding, clase, tag de
migracion y `new_sqlite_classes`. Si alguno difiere, E1 queda `STOP`.

## Flags Prohibidos

E1 no puede usar `--temporary`, `--route`, `--routes`, `--domain`, `--triggers`,
`--schedule`, `--schedules`, `--env-file`, `--secrets-file`, `--keep-vars` ni
autoconfiguracion. El uso de `--config` es obligatorio para evitar deteccion
automatica del proyecto.

## Credenciales

E1 adopta exclusivamente los nombres estandar de Wrangler:

- `CLOUDFLARE_API_TOKEN`.
- `CLOUDFLARE_ACCOUNT_ID`.

`CF_API_TOKEN` y `CF_ACCOUNT_ID` permanecen solo para usos legacy existentes fuera
de E1 y no se reutilizan implicitamente en el comando de deployment. Durante E1,
Wrangler necesariamente consume credenciales, pero la ejecucion no puede
imprimirlas, retornarlas ni persistirlas. Este ADR no incluye valores, defaults,
identificadores remotos, rutas, dominios ni ejemplos sensibles.

## E3A Endpoint Separado

La exposicion futura del broker se separa en `E3A`, con estado
`DEFINED_NOT_EXECUTED`. E1 despliega el Worker aislado y no accesible
publicamente. `E3A` decidira posteriormente, con autorizacion separada, entre:

- workers.dev explicito y temporal;
- route/custom domain protegido.

Este PR no selecciona ni habilita endpoint. `E4` queda bloqueado hasta que `E3A`
tenga aprobacion separada y evidencia revisada.

## No Decisiones

- No despliegue Cloudflare.
- No Durable Object remoto creado.
- No routes, domains, custom domains, preview URLs ni triggers.
- No acceso Cloudflare durante el dry-run PR G.
- No billing, plan o costo aceptado.
- No GitHub App o environment configurado.
- No OIDC live ni workflow dispatch.
- No Production, Supabase, fuentes, SQL, writers, migrations o schedules.
- Gate real permanece `NOT_CREATED_NOT_APPROVED_NOT_CONSUMED`.
- Trust permanece `STOP_G5_TRUST_VERIFICATION_NOT_IMPLEMENTED`.
- Connected mode permanece `IMPLEMENTED_DISABLED_NOT_CONFIGURED`.
