# Manifiesto JIT v4 — PG17/PostgREST local H3REQ1 — 2026-10-05

**Estado:** `JIT_V4_COMPLETED_LOCAL_PASS_NO_GO_REMAINS` — aprobado/ejecutado; alcance local PASS, gates de GO restantes pendientes.
**Alcance solicitado:** revalidar la cadena SQL y wire local con la migración `v_key_id` y el replay harness corregido, usando una red y un PostgreSQL limpios. Sin servicios del producto ni operaciones remotas.
**JIT v3:** [resultado detenido](manifiesto_jit_pg17_postgrest_h3req1_2026-10-05_v3.md). No repetir su hash ni continuar en la base parcial.

## Motivo y cambio local aprobado

La revisión del fallo v3 encontró que el harness había restaurado los JWT claims del actor
admin tras el escenario non-editor, pero dejó en `request.headers` el actor/RPC/nonce/firmas
del non-editor. El replay falló en la validación de firma antes de alcanzar el guard de nonce.
La hipótesis inicial de expiración del timestamp no se confirmó y queda supersedida.

Con autorización humana explícita `continua — autorizar edición`, solo se modificó
`tests/sql/h3_admin_rpc_signed_gateway_harness.sql`: la verificación de consumo y el replay
exacto se movieron inmediatamente después de la primera llamada positiva, antes de cambiar
claims/headers para el non-editor. La prueba reutiliza el mismo nonce, actor, target, payload,
timestamp, headers y firmas, y exige `rpc_replay_rejected`/409. No cambia la migración,
funciones, políticas ni lógica de producto.

| Gate | Resultado |
|---|---|
| Atestación sanitizada | La atestación de cliente limita RPCs Admin al JWT de sesión, exige conservar RLS, `auth.uid()`, RBAC/MFA y prohíbe sustituir identidad por service role. El cambio es de test fixture: conserva exactamente el actor autenticado original y no amplía el alcance funcional. |
| Revisión `security-auditor` | Revisión inicial señaló robustez por TTL de 60 s; se remedió ubicando el replay junto a la llamada positiva y usando la misma prueba firmada. Segunda revisión: **0 hallazgos**; no se ejecutó runtime. |
| Validación estática | PASS: el check de nonce y la llamada replay preceden los escenarios NULL/non-editor, conservan el contexto firmado original y mantienen la aserción 409. No se ejecutó SQL. |
| Limitación de revisión | El harness es untracked; no existe diff Git confiable contra HEAD. La revisión se basó en el contenido actual y el delta aplicado con `patch`. Una pausa externa superior a la ventana de 60 s aún podría hacer vencer la fixture; la secuencia normal `psql -f` las ejecuta consecutivamente. |
| Runtime del nuevo harness | **NO EJECUTADO**. El JIT v3 está consumido y no autoriza ningún reintento. |

## Baseline y cierre de hashes

| Campo | Valor |
|---|---|
| Worktree | `/home/romel/src/studiamatch-h3req1-sync-20261002` |
| Rama / `HEAD` / `origin/desarrollo` | `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c` / mismo SHA; merge-base igual, divergencia `0/0`. |
| WIP después de crear v4 | 104 entradas: 0 staged, 48 tracked modificadas, 56 untracked. Preservar íntegramente. Baseline inmediatamente anterior: 103 / 0 / 48 / 55. |
| Manifiesto base | v1 SHA-256 `45654420e7e3ce00a362b7e91a3877f129789a655ccf6ce45ccc1e087434de12`; 74 inputs (57 SQL/harness). El v3 aprobado se registró con SHA `f6905fe2b5e93e4bd9db3defa33870b9273ce75cf2ddd30b9ca5ca892b87facd`; su contenido documental posterior registra el resultado, no se usa como hash de inputs. |
| Delta de los 74 inputs frente a v1 | Exactamente dos hashes cambiados; los otros 72 deben coincidir. Migración `db/migrations/20261004_h3_admin_rpc_signed_gateway_payload_bound_wrapper.sql`: `f1b4dce0dc0634585b5448514877b200924448c7e2dcc06441f1c3f66af78d0f` → `c8a69e06e2d1d3a7f5e2245f6fb68ac6220deac3fd0b273edb5bcedafdba81a5`. Harness `tests/sql/h3_admin_rpc_signed_gateway_harness.sql`: `221e9100e9353db89e3fafd7f16fad4addcd9f958d8738b4d9a262e62819af01` → `376bd1cba0c557b5a62fe0b7f175bd7ef7493de5c9d98a4f78d4ddc48346812f`. |
| Preflight | 74 rutas presentes; 2 discrepancias esperadas, ambas listadas; 72/72 hashes restantes coinciden. Recalcular rama, WIP, manifiestos y hashes inmediatamente antes del JIT. Cualquier otro delta detiene este manifiesto. |

No stagear, reescribir fuentes ni editar inputs durante la operación. Si el preflight difiere,
no conectar ni ejecutar; preparar un manifiesto nuevo.

## Recursos y secuencia cuya autorización se solicita

### Red y runner

1. Crear `h3req1-jit-internal-v4-20261005` como Docker bridge con `--internal`.
2. Reutilizar `h3req1-node22-jit-v2-20261005`, imagen Node 22 fijada en `sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844`, sus cuatro mounts read-only y `node_modules` ya instalado. Confirmar `node v22.23.2`, SDK `@supabase/supabase-js 2.109.0` y hashes de `web/package.json`, lock y vendor. **No ejecutar npm, instalar paquetes ni habilitar egress.**
3. Conectar runner v2 a la red v4 y desconectarlo de la red interna v3 `h3req1-jit-internal-v3-20261005`; debe quedar solo en v4. No conectarlo a `bridge`. El runner v1 permanece idle en `bridge`; no tocarlo.

### PostgreSQL y PostgREST desechables

- Crear `h3req1-pg17-jit-v4-20261005` desde `postgres@sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f`, solo en red v4, sin puertos publicados, datos `/var/lib/postgresql/data` en tmpfs y mounts read-only únicamente para `tests/sql`, `db/migrations`, `db/rollback` y `db/seeds`. No volumen persistente; password sintético local `postgres`, nunca imprimirlo ni persistirlo.
- **Solo después de que todos los harness SQL anteriores pasen**, crear `h3req1-postgrest-jit-20261005` desde `postgrest/postgrest:v13.0.7@sha256:0a46780309a604cdc8b56c776c6e5e15788ce58174d709e40459ab5a2d44d228`, únicamente red v4, sin puertos publicados, puerto interno 3233, DB `h3_pro_chain_gate`, schema `public`, anon role `anon` y pre-request `public.h3_admin_rpc_signed_gateway_pre_request`. El hostname/puerto corresponden exactamente a la allowlist estática del driver. Confirmar que el nombre del contenedor esté libre; no hacer pulls.
- Antes de SQL/wire, verificar que en red v4 solo estén runner v2 y PostgreSQL v4; PostgREST se une posteriormente. Confirmar image digests, cuatro mounts read-only, tmpfs, ausencia de volumen persistente y puertos publicados.

### Ejecución secuencial en la instancia PG17 v4 limpia

Ejecutar `createdb`/`psql` dentro de `h3req1-pg17-jit-v4-20261005` con `ON_ERROR_STOP=1` y detenerse ante cualquier fallo:

1. DB `postgres`: `tests/sql/h2_pg17_harness.sql`; luego `tests/sql/h2_pro_pg17_harness.sql`.
2. DB `h3_gate`: `tests/sql/h3_pg17_harness.sql` con defaults.
3. DB `h3_pro_gate`: `h3_pg17_harness.sql` con `h3_pro_baseline=1`.
4. DB `h3_pro_chain_gate`: `h3_from_h2_pro_pg17_harness.sql`, `h3_admin_quota_harness.sql`, `h3_admin_rpc_signed_gateway_harness.sql` actualizado, `h3_safe_suspend_harness.sql`, en ese orden.
5. Crear `h3_future_contract_gate`; ejecutar `h3_from_h2_pro_pg17_harness.sql` con `h3_contracted_baseline=1`.
6. En `h3_pro_chain_gate`, ejecutar `h3_quota_postgrest_fixture.sql`, reaplicar `20261004_h3_admin_rpc_signed_gateway_payload_bound_wrapper.sql` y arrancar PostgREST. Desde runner v2 ejecutar `tests/h3_admin_quota_postgrest.mjs` únicamente contra `http://h3req1-postgrest-jit-20261005:3233` con fixtures/firmas sintéticos efímeros; luego `h3_quota_postgrest_assert.sql`.
7. Ejecutar `tests/sql/h3_invitation_reservation_concurrency.sh` solo contra `h3_gate`, con identidades y correos sintéticos.

No guardar JWTs, firmas ni secretos sintéticos en logs/evidencias. Ante cualquier error,
detenerse y conservar evidencia sanitizada; no seguir a PostgREST ni reintentar con v4.

## Aprobación y límites

**Aprobación humana v4 recibida** mediante “Aprobar v4 local”. Cubrió solamente la red
interna v4, mover el runner v2 entre redes internas (sin bridge/egress), crear PG17 en tmpfs
y, tras los PASS SQL, PostgREST interno, para ejecutar la secuencia local anterior con los
hashes indicados. La autorización quedó consumida al completarse el ciclo.

No autoriza cambios adicionales de fuente, repetir v2/v3, SQL Supabase remoto, Auth/correo,
Cloudflare, secretos de producto, Git/CI remoto, push/PR/merge, deploy, Certification/
Production, rollback integrado ni cleanup. Preservar runners, redes, bases parciales v2/v3
y recursos v4 al terminar. Cualquier cleanup requiere JIT independiente.

## Resultado de ejecución JIT v4 — 2026-10-05

- Aprobación recibida mediante “Aprobar v4 local”. SHA-256 del manifiesto aprobado antes
  de ejecutar: `27643875098604c40ca3ce511d710ff08583c4acd7f1bad04ef25c23224a3ccb`.
- Preflight repetido: manifiesto v1 y v4 con SHA esperado; 74 inputs presentes, exactamente
  dos hashes distintos y ambos coincidentes con el delta autorizado; rama, HEAD, origin,
  merge-base y WIP alineados; runner Node v2, mounts, digest, Node `v22.23.2` y SDK
  `2.109.0` verificados. No hubo npm ni egress.
- Red `h3req1-jit-internal-v4-20261005`: ID
  `f8851397653ad3eb5f013331de5bb947a6b74f338ba813c3fb233855a73daa3c`. PG17 v4 ID
  `4e26f117f76eab6ab3e6adbe3fd328ff8b463ffaef677f460d83be5c86314b27`, PostgREST ID
  `4cbde5dbc489032b8ce142d5c03457d852118e3f595e8b0afd5370d9f52aecf6`. Imágenes fijadas;
  PG sin puertos, datos tmpfs y cuatro mounts read-only; PostgREST sin puertos ni mounts;
  la red quedó solo interna.
- PASS SQL: H2 y H2 Pro (incluido rechazo esperado del rollback guard); H3 default; H3 Pro
  baseline; cadena H2 Pro→H3; cuotas; signed gateway con el replay exacto (`h3_admin_rpc_signed_gateway_harness_ok`);
  safe-suspend (`h3_safe_suspend_harness_ok`); baseline futuro contraído.
- PostgREST local/wire PASS: `tests/h3_admin_quota_postgrest.mjs` informó
  `result=PASS`, `mfaStatus=403`, `readAdmissions=120`, `deniedLegacyStatus=429`,
  `serviceOnly=true`. `h3_quota_postgrest_assert.sql` terminó PASS.
- Concurrencia PASS: `h3_invitation_reservation_concurrency_ok` en `h3_gate` con datos
  sintéticos. Las claves JWT/RPC de test se tomaron en memoria de la configuración local;
  no se imprimieron ni se guardaron en evidencia.
- El JIT v4 queda consumido. **No se ejecutaron** SQL remoto, Auth/correo remoto, Git/CI,
  Cloudflare, PR/merge/deploy, rollback integrado ni cleanup. Se conservan runners,
  redes y bases parciales/v4 en tmpfs.
- Resultado: **PASS del runtime local cubierto por H3-CLOSE-02**, pero el proyecto permanece
  **`NO-GO_H3REQ1_DEVELOPMENT_FREE`**. H3-CLOSE-03 integrado, mantenimiento, CI efectivo,
  validación final/atestación y promoción/aceptación D01–D14 siguen pendientes; este JIT no
  autoriza sus ejecuciones.
