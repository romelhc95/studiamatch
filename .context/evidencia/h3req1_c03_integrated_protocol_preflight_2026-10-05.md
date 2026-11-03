# H3-CLOSE-03 integrado — protocolo y preflight de autorización

Fecha: 2026-10-05. Estado: **NO-GO; ensayo integrado no ejecutado ni autorizado**.

## Resultado del preflight de solo lectura — corte histórico 2026-10-05

- Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
  `feat/h3req1-sync-20261002`, `HEAD=4eb4d877a50b012bb630a129bd0c74482c33be9c`.
  El HEAD es el baseline, no identifica el WIP. Revisión actual: 0 staged, 48 tracked
  modificados y 63 untracked (111 entradas de estado); la cuenta incluye WIP anterior,
  protocolo y artefactos bootstrap, y no atribuye todos los cambios a este ciclo. Se
  preserva todo el árbol y el checkout original.
- **H3-CLOSE-02 PASS v4 preservado:** se compararon los 72 inputs no-C03 del
  manifiesto base con las dos sustituciones autorizadas por v4; 72/72 coinciden.
  No se repitió ningún harness ni se reutiliza el JIT consumido.
- **C03 SQL safe-suspend/resume PASS v3 preservado:** 41/41 hashes del manifiesto
  v3 coinciden. V2 es histórico. No se conectó ni ejecutó SQL en ninguno de los
  dos PG17 C03 preservados.
- Se enumeraron imágenes/recursos Docker en solo lectura. PG17, PostgREST 13,
  Node 22 y contenedores/redes previos continúan intactos. No se conectó, inició,
  detuvo ni limpió ningún recurso preservado.
- La UAT Pages existente ejecuta el middleware real en workerd/Miniflare, pero
  usa assets fixture. La UAT Edge actual transpila el TypeScript y lo ejecuta en
  un VM Node con Auth/DB simulados; no equivale al Edge Runtime de Deno.
- No hay `deno` ni Supabase CLI en el host WSL. La imagen Edge Runtime fijada ya está
  descargada, pero su fuente v1.74.3 pinnea Deno **2.1.4**. El resolver ejecutado con
  Deno 2.9.7 generó un lock v5, que Deno 2.1.4 no puede leer; se conserva como artefacto,
  pero no sirve para el runtime integrado. Aún falta un lock v4 y una caché offline
  generados por Deno 2.1.4.
- `tests/h3req1-c03-bootstrap/package-lock.json` fija Miniflare/esbuild/TypeScript,
  pero se creó con `--package-lock-only`: no están instalados ni cacheados npm/workerd.
  Esa fase de bootstrap deberá estar descrita expresamente en el JIT integrado.
- `admin-invite` valida exclusivamente URL HTTPS `*.supabase.co`; conectarla a PostgREST
  local requiere un alias y puente TLS aislado. Todavía no hay runner ni fixtures
  integrados, ni conjunto final de hashes. Los hashes siguientes son inventario de
  fuentes, no autorización para ejecutarlas.

## Recursos y protocolo propuestos — sin crear ni activar

Todo ensayo sería local y sobre recursos nuevos. Los nombres y topología se fijarán al
concluir el runner. Hace falta al menos una instancia Edge activa para dejar una petición
pre-reservada dentro de Auth local, y una instancia Edge con safe-suspend activado para
probar que un nuevo inicio no reserva ni llama Auth mientras SQL está suspendido. Se
mantendrá la instancia activa solo para completar esa única operación in-flight. Los
servicios de prueba nunca se conectarán a recursos PG17/PostgREST preservados.

Imágenes disponibles localmente: PostgreSQL 17
`postgres@sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f`;
PostgREST 13.0.7
`postgrest/postgrest@sha256:0a46780309a604cdc8b56c776c6e5e15788ce58174d709e40459ab5a2d44d228`;
Node 22
`node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844`.
Ninguna de esas imágenes está autorizada para arrancar como recurso del ensayo.

La imagen Edge Runtime oficial v1.74.3 Linux/amd64 está descargada bajo el bootstrap
aprobado: `supabase/edge-runtime:v1.74.3_amd64@sha256:cc355c3d0e9c063a351cad56d1c4c52a3c4d85aff4e1fad9d91688e75f9aad09`
(índice OCI `sha256:fb0937be6163aa5ead2cecf853f93deca05586cb46ee402936606bd8d8580608`).
El upstream [`deno/Cargo.toml`](https://github.com/supabase/edge-runtime/blob/v1.74.3/deno/Cargo.toml)
pinnea Deno 2.1.4. Para ejecutar sin egress, se requiere generar el lock/caché
compatible con Deno 2.1.4 antes del ensayo. Deno 2.1.x solo lee lock v4; Deno 2.3+
introdujo formato v5 (ver [compatibilidad del lock v5](https://github.com/dependabot/dependabot-core/pull/15319)).

Secuencia a implementar y someter a hashes/JIT nuevos:

1. Resolver/prefetch el lock/cache Deno 2.1.4 y los paquetes npm/workerd bajo los
   permisos bootstrap que se indiquen explícitamente. Después, crear únicamente la red
   Docker `--internal` y contenedores nuevos fijados por digest, sin puertos publicados
   ni volúmenes de datos persistentes; fuentes y cachés se montan read-only. No habrá
   egress externo durante el ensayo integrado.
2. En una DB PG17 nueva, preparar schema/fixtures sintéticos con los harnesses
   existentes de cadena H2-Pro→H3, cuotas y dispatcher firmado. Su ejecución será
   prerrequisito de C03, no un PASS nuevo de C02 ni repetición del PASS C03 v3.
3. Añadir fixtures SQL por etapas para datos/auditoría y una solicitud Edge normal
   con identidad/correo sintéticos. El Auth local de prueba se detendrá después de
   la reserva para dejar una operación realmente in-flight; no se contactará Auth
   ni se enviará correo real.
4. Suspender solo esa DB nueva mediante `db/rollback/h3req1_safe_suspend.sql`.
   Workerd/Pages debe responder 503 privado y borrar las cuatro cookies/chunks,
   mantener rutas públicas, y rechazar aliases Admin. La instancia Edge suspendida
   debe responder mantenimiento sin nueva reserva ni llamada Auth. El admission RPC
   Edge ocurre antes del guard y puede dejar **un evento sintético de cuota**;
   se medirá y documentará, no se confundirá con una invitación.
5. Mientras SQL permanece suspendido, enviar al PostgREST local una prueba HMAC
   válida al dispatcher: debe ser denegada por ACL, sin consumir nonce. Liberar
   después la petición previamente reservada; su finalizador `service_role` debe
   completar una sola vez y dejar la auditoría esperada.
 6. Comprobar datos editoriales/auditoría/publicación, membresía del admin actor
   sintético y estados de invitación antes de recuperar. En una conexión nueva,
   ejecutar `safe_resume` solo si identidad, captura persistente y fingerprint
   coinciden; comprobar diez ACL, resultado y replay ya completado sin segundo
   efecto Auth.
7. Recuperar Edge primero y Pages/workerd al final; smoke público y administrativo
   local, sin abrir rutas legacy. Cualquier mismatch/fallo detiene la ejecución y conserva
   evidencia/recursos. Si falla antes de aplicar safe-suspend, el Edge activo podría seguir
   atendiendo únicamente en la red interna; no hay correo real ni puerto publicado. No se
   afirma suspensión hasta completar y verificar ese paso. Si falla después, no se ejecuta
   resume automático. No hay cleanup incluido.

## Efectos acotados y límites

El JIT final tendrá que autorizar explícitamente: imágenes/paquetes locales exactos;
red/contenedores nuevos y su preservación; DDL/DML/grants **solo** dentro de la DB
PG17 nueva; registros sintéticos de curso, auditoría, invitación, cuota y snapshot ACL;
JWT/HMAC/certificado TLS sintéticos en memoria/fixtures; llamada simulada a Auth sin
correo; suspensión y recuperación SQL persistente del recurso nuevo; y orden Edge→Pages
de recuperación. Ningún secreto real, `.env*`, cuenta, factor MFA ni dato operativo
se montará o utilizará.

Quedan excluidos: los PG17/runner/redes existentes; Supabase Free/Pro, Auth real,
correo, Cloudflare, Workers/Pages remotos, GitHub/protecciones, push/PR/merge/deploy,
`workflow_dispatch`, Certification/Production y cleanup. El JIT SQL v3 y JIT v4
consumidos no se extienden a estas operaciones.

## PASS integrado requerido

- Hashes transitivos cerrados para SQL, runtime Edge, middleware/Pages, runner,
  lockfiles, fixtures/configuración e imágenes; red de prueba aislada y sin egress.
- Pages/workerd real: suspensión 503 con `private, no-store`, las cuatro cookies
  de sesión/verifier/activity/CSRF expiradas, host/aliases Admin bloqueados y rutas
  públicas intactas.
- Edge Runtime real: iniciador nuevo rechazado antes de reserva/Auth; solo el evento
  de admission quota documentado; operación previa reserva-before-Auth finalizada
  después de la suspensión con una sola auditoría y sin segundo envío.
- PostgREST/PG17 reales del ensayo: dispatcher firmado denegado por ACL antes del
  cuerpo `SECURITY DEFINER`, nonce intacto, datos/auditoría/publicación y último
  administrador sintético preservados; finalizadores in-flight disponibles.
- Resume persistente solo tras verificar identidad/fingerprint; Edge recuperado antes
  que Pages; smoke posterior sin tokens JS ni bypass legacy. Evidencia sanitizada,
  salida y códigos de proceso completos; ninguna aserción sustituida silenciosamente
  por mock. Las limitaciones de Auth simulada quedan declaradas.
- Todo PASS se limita a este ensayo local y no acredita rollback remoto, CI efectivo,
  aceptación D01–D14 ni GO Development.

## Inventario de hashes al corte histórico 2026-10-05

Los hashes C03 completos (41) constan en el [manifiesto SQL v3](../operaciones/manifiesto_jit_h3_close03_safe_resume_pg17_2026-10-05_v3.md);
los 72 inputs H3-CLOSE-02 no-C03 coinciden con el [resultado v4](../operaciones/manifiesto_jit_pg17_postgrest_h3req1_2026-10-05_v4.md).
Se vuelven a listar solo los inputs runtime inspeccionados en este preflight:

| Ruta | SHA-256 |
|---|---|
| `web/functions/_middleware.ts` | `237bc47043ed8a7f0604445d43c2ca2042e352373ee165a56cf669dd4821fd9b` |
| `web/functions/_lib/admin-bff.ts` | `1cb1ad95d723e884f58cf98dd5b2600e59fa8230aa044cb25e6ebb41f1db7ed7` |
| `web/functions/_lib/admin-quota.ts` | `738a3267d645fdca40b77b8d8fb9877c209992296031b0d670b6153c9a9134d6` |
| `web/src/lib/supabase-transport.ts` | `b115c8f1c46f7c33c80f6ace8fc9d5c2409898ca1833851e58d1361d640571b0` |
| `workers/admin-quota/index.ts` | `392d0f9ad183ac871a16d01c6f6b5e6fd18edd26c18fd3221a1d16f8bb0a869f` |
| `workers/admin-quota/wrangler.jsonc` | `f90ffabbfe79c5ebf8f98da12b6604fc6a2961fa8b8811ce48dd2a23e855bbf5` |
| `supabase/functions/admin-invite/index.ts` | `1569b90394b313a4b42e4e50158da077cec42d26356c0d713b16535f47053a60` |
| `supabase/config.toml` | `531705c8502ca635a08d2d484368165dc493b71b984a65d4fc249ced138e6857` |
| `tests/h3_admin_safe_suspend_runtime_uat.mjs` | `44a0b8419828611811c6cba57c8398dfe23e319a7a3ac310690efff502d8ea74` |
| `tests/h3_admin_invite_edge_uat.mjs` | `13d608cf1ac51bf66122460a258b7249f7cc6cb7074ec3456e971e45e755fbdf` |
| `tests/h3_admin_quota_postgrest.mjs` | `e11034070050212bffe961f87467cc727b0c16053a3319515acb477f63d28e95` |
| `web/package.json` | `4567e008756097437c0ef586f1c112c97db3a198bcd521bd62e8342242f7cd8a` |
| `web/package-lock.json` | `8bd9c50605a8ce92e87b0ad81e4513fd47fc01ca328079eef792d264c2a292bc` |

## Bootstrap reproducible — resultado parcial y límite vigente

La API `session.messages` de `ses_ef0cce873ffe3X1100DbM8XxSw` muestra prompts/cierres,
pero no expone respuestas a preguntas interactivas. En el historial de interacción
conservado sí está la respuesta humana exacta `Aprobar bootstrap local` y el alcance
presentado: descargar Edge Runtime fijado y resolver/generar locks para Miniflare
`4.20260730.0`, esbuild `0.25.10`, TypeScript `5.9.3` e imports Edge npm/JSR; sin
arrancar contenedores ni ejecutar paquetes/pruebas, SQL, grants, Auth/correo, servicios
del producto o cleanup. Esa respuesta no autorizó el drill.

Resultados/efectos observados:

- `2026-10-06T03:49:53Z`: `docker pull` obtuvo la imagen oficial Supabase Edge Runtime
  Linux/amd64 `supabase/edge-runtime:v1.74.3_amd64@sha256:cc355c3d0e9c063a351cad56d1c4c52a3c4d85aff4e1fad9d91688e75f9aad09`.
  `docker image inspect` confirma el mismo digest/arquitectura. No se inició el runtime.
- Tras una aprobación JIT interactiva limitada a los resolvers de locks, se usó
  `node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844`
  (`NODE_VERSION=22.23.2`, npm `10.9.8`) en el contenedor nuevo
  `h3req1-c03-bootstrap-node-locks-20261006-r1`. El único comando fue `npm install
  --package-lock-only --ignore-scripts --no-audit --no-fund --registry=https://registry.npmjs.org/`;
  terminó exit 0 y generó el lock de Miniflare `4.20260730.0`, esbuild `0.25.10` y
  TypeScript `5.9.3`. `package.json` SHA-256
  `539384b46b23ef1056acdb5dcf11cb8583269c82c16e37e6af3d69fc030ef287`;
  `package-lock.json` SHA-256
  `997c48e9522522779b746a9c8b2d171d2e6f28b857dd4cba1faccd17d273e477`.
- También se descargó Deno 2.9.7 Linux/amd64
  `denoland/deno:2.9.7@sha256:869d374bdaddda4fde029c492d7219199b0e821c2c53cca5357b3a6f5b9336fc`;
  Docker confirmó el digest.
- El primer intento con `--lock-write` terminó exit 1 porque Deno 2.9.7 ya no acepta
  ese flag; el parser rechazó el comando antes de resolver imports. El contenedor
  `h3req1-c03-bootstrap-deno-locks-20261006-r1` está detenido y preservado.
- Tras una segunda aprobación humana, exacta para un retry con el riesgo de egress bridge
  reconocido, `h3req1-c03-bootstrap-deno-locks-20261006-r2` ejecutó
  `deno cache --lock=/out/deno.lock --frozen=false /src/index.ts` y terminó exit 0.
  Generó `tests/h3req1-c03-bootstrap/deno.lock`, SHA-256
  `2517370708f2846728a331b94fe2b1bd952e1d112a23fc6566457d4d3cc5e8e5`, formato v5.
  Upstream de Edge Runtime v1.74.3 fija Deno 2.1.4, incompatible con v5; el lock se
  conserva pero no se acepta para el runtime integrado. Su DENO_DIR quedó en ese
  contenedor detenido y no se exportó como caché offline reutilizable.
- Bajo un JIT adicional exacto se descargó Deno 2.1.4 amd64
  `denoland/deno:2.1.4@sha256:bc48369c9b1810da957cabcac234094a691f94cb6cd0e88d533ccac89f2f0cb9`.
  El contenedor `h3req1-c03-bootstrap-edge-locks-20261006-r1` ejecutó el resolver v4
  con exit 1 tras descargar metadata/type declarations de JSR; Deno informó que el
  import npm requiere `node_modulesDir: auto` o dependencias declaradas. No apareció
  archivo `deno-edge-runtime-v1.74.3.lock`. El volumen nuevo
  `h3req1-c03-edge-deno-cache-20261006-r1` contiene esa caché parcial. Contenedor y
  volumen están detenidos/preservados; no se reutilizarán.
- Los resolvers no publicaron puertos; montaron el `index.ts` read-only y el directorio
  de salida. No se montaron `.env*`/secretos ni se inició Edge Runtime, la función, tests,
  SQL, Auth ni servicios del producto. No hubo cleanup; todos los contenedores/volúmenes
  de bootstrap quedan preservados.

Límite/riesgo operativo: los resolvers usaron Docker `bridge`, que permite egress general;
no hubo allowlist técnica por hostname. El riesgo residual se aceptó expresamente solo
para cada resolver aprobado y esos JIT están consumidos. npm se configuró con
`registry.npmjs.org`, auditoría/scripts deshabilitados, pero tampoco tuvo restricción de
red por hostname. Aún no hay tarballs npm ni caché Deno completa reusable. Para resolver
el grafo npm con Deno 2.1.4 se necesita `--node-modules-dir=auto` (CLI presente en la
[fuente v2.1.4](https://github.com/denoland/deno/blob/v2.1.4/cli/args/flags.rs#L4280));
el retry requiere otro JIT, contenedor nuevo y dos volúmenes nuevos. Ningún recurso
bootstrap preservado se reutilizará ni limpiará.

## JIT lock/cache compatible — resultado

El JIT exacto se aprobó tras revisar que la imagen ya estuviera fijada, el source hash
coincidiera y los nombres de salida fueran nuevos. El comando autorizado ejecutó en
Docker `bridge`:

```bash
docker run --platform linux/amd64 --name h3req1-c03-bootstrap-edge-locks-20261006-r2 --network bridge --mount type=bind,src=/home/romel/src/studiamatch-h3req1-sync-20261002/supabase/functions/admin-invite/index.ts,dst=/src/index.ts,readonly --mount type=bind,src=/home/romel/src/studiamatch-h3req1-sync-20261002/tests/h3req1-c03-bootstrap,dst=/out --mount type=volume,src=h3req1-c03-edge-deno-cache-20261006-r2,dst=/deno-cache --mount type=volume,src=h3req1-c03-edge-node-modules-20261006-r2,dst=/src/node_modules --workdir /out --env DENO_DIR=/deno-cache denoland/deno:2.1.4@sha256:bc48369c9b1810da957cabcac234094a691f94cb6cd0e88d533ccac89f2f0cb9 cache --node-modules-dir=auto --lock=/out/deno-edge-runtime-v1.74.3-r2.lock --frozen=false /src/index.ts
```

Resultado **exit 0**. `deno-edge-runtime-v1.74.3-r2.lock` quedó en formato v4, SHA-256
`ce8a4a433e58cc9a4cee0e908cb7b629305b58a790666e107d56f53a6a3548b1`; corresponde a
Deno 2.1.4, la versión fijada por Edge Runtime v1.74.3. Se resolvió el grafo npm/JSR en
los volúmenes nuevos `h3req1-c03-edge-deno-cache-20261006-r2` y
`h3req1-c03-edge-node-modules-20261006-r2`. El contenedor
`h3req1-c03-bootstrap-edge-locks-20261006-r2` terminó y queda preservado.

Deno advirtió que el script lifecycle de `npm:workerd@1.20260730.1` no se ejecutó; no se
usó `--allow-scripts`, ni se inició workerd. Esto es correcto para el cache Edge, pero
significa que Miniflare/workerd aún necesita una instalación de herramientas separada
en el JIT integrado. El `package-lock.json` Node de herramientas también es solo metadata;
no se descargaron sus tarballs.

El acceso Docker `bridge` permitía egress general sin allowlist FQDN; el riesgo se aceptó
solo para este resolver. No se iniciaron Edge Runtime/la función, PG17/PostgREST, Pages,
workerd, tests, SQL, Auth ni correo. No hubo cleanup ni se usó un recurso preservado. Este
PASS cubre únicamente lock/cache Edge, no el ensayo integrado ni GO Development.

Siguen sin permiso/ejecución: SQL/grants, suspensión/resume, Pages/workerd, Edge Runtime
como servicio, PostgREST/PG17, tests, Auth/correo, runtime remoto y cleanup. El texto de
este corte antecede la preparación descrita abajo; no representa el estado más reciente.

## Runner y fixtures integrados — revisión estática R1 pre-JIT, 2026-10-06

**Estado en ese corte: PREPARADO_ESTÁTICAMENTE / NO-GO / JIT pendiente.** C02 v4 (72/72) y
C03 SQL v3 (41/41) permanecen preservados; no se repitieron ni se conectó a sus recursos.
Al terminar el preflight estático aún no se había iniciado ningún contenedor, runtime,
PostgREST o PG17 ni se habían ejecutado SQL/tests, npm installs, Auth o correo. La revisión
y las correcciones descritas en esta sección fueron estáticas; el resultado de la ejecución
JIT posterior se registra al final de este documento.

Artefactos integrados:

- `tests/h3req1_c03_integrated_drill.sh` — único orquestador. Requiere la etiqueta
  `H3-CLOSE-03-INTEGRATED-2026-10-06-R1` y el SHA-256 aprobado del manifiesto, valida
  rama/HEAD, inputs y nombres libres; no hace pull ni cleanup. Los argumentos son guards,
  no sustituyen la aprobación humana JIT.
- `tests/h3req1_c03_integrated_runtime.mjs` — Miniflare/workerd Pages real, servicio de
  cuota Durable Object efímero, puente HTTP/TLS sintético, Auth adapter local, hold
  determinista de la llamada Auth, operaciones workerd/Edge y assertions de recuperación.
- `tests/h3req1_c03_cache_digest.mjs` — calcula SHA-256 determinista de árboles de
  dependencias (bytes, rutas, symlinks y modos); se ejecuta en una imagen Node fijada,
  con el snapshot y los volúmenes read-only, en red `none`. El mismo cálculo se repite en
  runtime antes de Miniflare y se compara con el digest recién generado. El digest de cada
  árbol se registra en el log para identificar exactamente los módulos ejecutados.
- El primer contenedor crea un snapshot Docker de solo los archivos del manifiesto, más el
  manifiesto mismo; verifica su digest y todos los hashes, rechaza symlinks, copia
  determinísticamente `deno.json`/`deno.lock` junto al Edge function y crea allí un
  mountpoint `node_modules` vacío. No monta el checkout completo ni `.env*`. Bootstraps,
  PG17, runtime y Edge consumen ese snapshot, no bind mounts vivos del checkout.
- `tests/h3req1-c03-edge-main/index.ts` — router local de ruta fija, basado en el patrón
  del servicio principal Supabase. Edge Runtime carga `admin-invite/index.ts` como
  user worker aislado vía `EdgeRuntime.userWorkers.create`; el gateway local traduce
  `/functions/v1/admin-invite` a `/admin-invite`, igual que el strip-prefix de Kong.
- `tests/sql/h3req1_c03_integrated_extension_setup.sql` — aplica únicamente migrations
  de cuotas y dispatcher firmado necesarias para el drill; no reejecuta los harnesses
  funcionales de cuotas ni del dispatcher ya validados.
- `tests/sql/h3req1_c03_integrated_setup.sql` y `tests/sql/h3req1_c03_integrated_assert_*.sql`
  — identidad/curso/auditoría sintéticos, reserva previa a Auth, estado suspendido,
  finalización in-flight, recuperación y replay idempotente. El `request_id` se valida
  desde `admin_invitations.metadata`, que es su contrato real.
- `tests/h3req1-c03-bootstrap/deno.json` y
  `deno-edge-runtime-v1.74.3-r2.lock` — Deno 2.1.4 lock v4 y configuración compatible
  con Edge Runtime v1.74.3. El lock se aplica en modo `--frozen` para construir volúmenes
  Edge r3 nuevos; los volúmenes preservados r2 no se inspeccionan, montan ni reutilizan.

El runner bootstrap de dependencias antes de crear las redes del ensayo, en tres
contenedores nuevos sobre Docker `bridge`, sin secretos ni puertos publicados:

1. `npm ci` desde `tests/h3req1-c03-bootstrap/package-lock.json`, con lifecycle scripts
   activos para que se instale workerd `1.20260730.1` (Miniflare `4.20260730.0`, esbuild
   `0.25.10`, TypeScript `5.9.3`).
2. `npm ci --omit=dev --ignore-scripts` desde `web/package-lock.json`, solo para resolver
   en esbuild los imports `@supabase/ssr`/`@supabase/supabase-js` usados por el BFF.
3. `deno cache --node-modules-dir=auto --lock=/source/supabase/functions/admin-invite/deno.lock --frozen`
   con Deno 2.1.4 fijado y fuentes de snapshot read-only; crea DENO_DIR y el `node_modules`
   Edge en volúmenes separados. Runtime vuelve a comprobar los hashes fuente del snapshot.

Los bootstraps npm usan la imagen Node 22 fijada; el tercero usa la imagen Deno 2.1.4 fijada.
El snapshot permanece read-only después de crearse. Se crean cuatro volúmenes de dependencias
(Miniflare, Pages, DENO_DIR y Edge `node_modules`) y uno TLS; cache/verificador y runtime los
montan read-only. Las tres fases de dependencias usan
Docker `bridge`, que **no impone allowlist FQDN**; `registry.npmjs.org` y el lock frozen
limitan resolución, no red. El egress general del tercero y lifecycle scripts del primer
bootstrap podrían contactar destinos externos adicionales. El JIT debe autorizar
expresamente ese riesgo, snapshot y bootstrap containers, los dos `npm ci`, `deno cache`,
lifecycle workerd y preservación de recursos. Después, los digest de los cuatro árboles
instalados se registran y verifican antes de ejecutar Pages/Edge. El ensayo usa solo redes
`docker network create --internal`, sin puertos publicados ni egress externo. El router
Edge se limita al nombre exacto `admin-invite`; no carga funciones adicionales ni usa un
mock del runtime.

Efectos/nombres fijados en el runner:

- Imágenes solo se validan con `docker image inspect`; **no hay pull ni build** y el runner
  falla cerrado si falta alguna: `postgres@sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f`,
  `postgrest/postgrest@sha256:0a46780309a604cdc8b56c776c6e5e15788ce58174d709e40459ab5a2d44d228`,
  `node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844` y
  `denoland/deno:2.1.4@sha256:bc48369c9b1810da957cabcac234094a691f94cb6cd0e88d533ccac89f2f0cb9` y
  `supabase/edge-runtime:v1.74.3_amd64@sha256:cc355c3d0e9c063a351cad56d1c4c52a3c4d85aff4e1fad9d91688e75f9aad09`.
- Bootstrap: contenedores
  `h3req1-c03-bootstrap-miniflare-20261006-r1` y
  `h3req1-c03-bootstrap-pages-deps-20261006-r1`, además de
  `h3req1-c03-bootstrap-edge-deps-20261006-r3`, el verificador
  `h3req1-c03-dependency-cache-verify-20261006-r1` y snapshot container
  `h3req1-c03-source-snapshot-20261006-r1`; volúmenes
  `h3req1-c03-integrated-source-snapshot-20261006-r1`,
  `h3req1-c03-integrated-miniflare-node-modules-20261006-r1` y
  `h3req1-c03-integrated-pages-node-modules-20261006-r1`,
  `h3req1-c03-integrated-edge-deno-cache-20261006-r3` y
  `h3req1-c03-integrated-edge-node-modules-20261006-r3`. El snapshot conserva solo el
  mountpoint vacío `node_modules`; los módulos instalados viven en el volumen dedicado.
  Los caches r2 originales siguen preservados sin inspección ni montaje.
- Ensayo: contenedores
  `h3req1-c03-integrated-pg17-20261006-r1`,
  `h3req1-c03-integrated-postgrest-20261006-r1`,
  `h3req1-c03-integrated-runtime-20261006-r1`,
  `h3req1-c03-integrated-edge-active-20261006-r1` y
  `h3req1-c03-integrated-edge-suspended-20261006-r1`; redes internas separadas
  `h3req1-c03-integrated-edge-20261006-r1` y
  `h3req1-c03-integrated-data-20261006-r1`; Edge solo comparte la primera con el runtime,
  que es el único contenedor unido también a la red de datos. Runtime inicia solo en EDGE,
  detecta su única IPv4 no-loopback y fija HTTPS a esa IP antes de conectarse a DATA;
  HTTP BFF y control escuchan solo en loopback. Los peers DATA no pueden iniciar el gateway
  TLS Edge. Node/Miniflare,
  PostgreSQL 17, PostgREST, Edge activo y Edge suspendido con nombres `...-20261006-r1`
  establecidos literalmente por `tests/h3req1_c03_integrated_drill.sh`. No se publica
  ningún puerto al host; runtime y servicios usan `--log-driver none`, y stdout/stderr del
  proceso runtime se suprime.
- PostgreSQL requiere SCRAM y una contraseña aleatoria sintética de 256 bits; solo PostgREST
  la recibe aparte del contenedor PostgreSQL. Docker conserva esos valores sintéticos en
  metadata inspectable de ambos contenedores detenidos hasta cleanup humano separado. La
  ruta de acceso Edge→BFF/función pasa por el gateway HTTP/TLS,
  y Edge no comparte red con PostgREST ni PG. Los contenedores de servicio fijan
  `--log-driver none`; el log de resultado es el único registro persistente planificado.
- Runtime TLS: volumen nuevo `h3req1-c03-integrated-tls-20261006-r1` con CA/certificado
  sintéticos; claves privadas temporales en tmpfs y no se montan en Edge. JWT, API keys,
  password y claves HMAC son fixtures sintéticos derivados o generados localmente; la
  password PostgreSQL se genera aleatoriamente y queda en metadata Docker preservada.
- PostgreSQL solo usa tmpfs. Ante fallo no hay cleanup ni resume automático y se preserva el
  estado que se haya alcanzado; si falla durante shutdown, algunos servicios podrían estar ya
  detenidos y PG tmpfs podría haberse perdido. Al PASS el runtime
  debe salir naturalmente con código 0; se detienen Edge activo/suspendido, PostgREST y PG.
  Se comprueba `exited`, `OOMKilled=false` y que ningún proceso termine con código 137. El
  contenido efímero de PG se pierde por diseño, mientras contenedores, red y volúmenes
  permanecen. No hay `docker rm`, `volume rm`,
  `image rm` ni limpieza. Este ciclo de vida de datos debe figurar en el JIT.
- El único log de resultado previsto es
  `.context/evidencia/h3req1_c03_integrated_run_2026-10-06_r1.log`; se rechaza si ya existe,
  incluso como symlink, y `noclobber` protege su creación. La salida se redirige directamente
  al archivo (sin `tee`) y el gate exige leer de regreso la línea final PASS antes de anunciar
  éxito al terminal. Las respuestas de control son sanitizadas;
  stdout/stderr de ambos `npm ci` y salidas SQL se suprimen; el Docker log driver es `none`.
  Se registra solo resultado/exit code por gate. Un error detiene etapas y preserva recursos;
  Edge podría seguir activo en su red interna antes de safe-suspend o después de un safe-resume
  ya completado; no hay nuevas transiciones automáticas.

Cobertura preparada: login SSR AAL2 y cookies reales en workerd; el gateway fija el origen
PostgREST y rechaza rutas con autoridad/backslash antes de reenviar; 7 cookies/chunks expirados
durante 503, 3 rutas de middleware Pages/workerd con `ASSETS` sintético preservadas y
8 aliases Admin rechazados;
reserva de invitación y hold antes de Auth; safe-suspend con rechazo Edge, una admisión
sintética y cero nuevas reservas/llamadas de correo; dispatcher HMAC válido denegado por
ACL sin nonce consumido; finalizador `service_role` de la petición previa mientras SQL
sigue suspendido; safe-resume en una conexión nueva; replay Edge antes del smoke BFF/Pages,
misma invitación y sin segundo correo. Auth/correo son un adapter local sintético: Edge
Runtime sí es real, pero el drill no acredita Auth remoto ni entrega de correo.

JIT exacto pendiente: `H3-CLOSE-03-INTEGRATED-2026-10-06-R1`. El JIT debe aceptar por
separado el digest del manifiesto indicado abajo y cubrir los tres bootstraps con egress
general, lifecycle workerd, las imágenes locales fijadas, redes/volúmenes/contenedores,
`DROP SCHEMA public/private CASCADE`, roles y DDL/DML solo dentro del PG17 efímero, snapshot
de fuentes, retención de recursos/log y pérdida intencional del PG tmpfs al detenerlo. No
autoriza ambientes remotos, Supabase remoto, correo, push, PR, merge ni deploy. Comando
propuesto, solo tras aprobación humana separada:

```bash
bash tests/h3req1_c03_integrated_drill.sh --jit H3-CLOSE-03-INTEGRATED-2026-10-06-R1 \
  --manifest-sha256 a1073d93d22b8c01ed0e41031e4c1f41df33848eac1ff31935b223c80f47e101
```

El comando fija `HEAD=4eb4d877a50b012bb630a129bd0c74482c33be9c`. El manifiesto
`tests/h3req1-c03-integrated.sha256` contiene **62 inputs**; `sha256sum -c` verificó
62/62. SHA-256 del manifiesto: `a1073d93d22b8c01ed0e41031e4c1f41df33848eac1ff31935b223c80f47e101`.
`bash -n tests/h3req1_c03_integrated_drill.sh` y `git diff --check` terminaron con exit 0.
La auditoría estática detectó y se corrigió la ruta de digest de `node_modules` Edge: el
runtime ahora verifica el volumen read-only montado en `/edge-node-modules`. El snapshot,
listener HTTPS solo en la red Edge, los cuatro árboles de dependencias y el cierre de
contenedores también están cubiertos por los guards. Permanece el riesgo MEDIUM de egress
general durante los tres bootstrap; debe aceptarse expresamente en el JIT. El hash anterior
`3e34dbebc42a53333305e7fe1c7ff5265e243dfb08ca555ae0ca549a8c731c0a` queda revocado; el
único digest vigente para aprobación JIT es
`a1073d93d22b8c01ed0e41031e4c1f41df33848eac1ff31935b223c80f47e101`, ya incluido en el
comando y verificado contra el manifiesto al cierre del preflight. El resultado de su
ejecución autorizada posterior se documenta abajo; ningún resultado local declara GO
Development.

Referencias: [estado vivo](../estado_del_proyecto.md),
[estado PR/remoto](../seguimiento/h3req1_estado_pr_y_remoto_2026-10-05.md),
[plan único](../operaciones/plan_cierre_integral_h3req1_2026-10-04.md),
[traspaso](../seguimiento/h3req1_traspaso_avance_y_proximo_ciclo_2026-10-04.md),
[evidencia preflight SQL v3](h3req1_h3_close03_integrated_preflight_2026-10-05.md) y
[atestación cliente](../evidencias_cliente/sprint_1/atestado_aceptacion_plan_ingesta_editorial_auditoria_2026-10-01.md).

## Resultado de ejecución autorizada R1 — 2026-10-06

El responsable aprobó el JIT exacto `H3-CLOSE-03-INTEGRATED-2026-10-06-R1` y el SHA-256
`a1073d93d22b8c01ed0e41031e4c1f41df33848eac1ff31935b223c80f47e101`. Se ejecutó únicamente
`tests/h3req1_c03_integrated_drill.sh` con esos guards. El preflight del manifiesto verificó
62/62 y los bootstrap de snapshot, Miniflare y Pages terminaron; el bootstrap Deno Edge se
detuvo con exit 1 en la fase `isolated-deno-edge-dependency-bootstrap-with-registry-egress`.
El contenedor `h3req1-c03-bootstrap-edge-deps-20261006-r3` quedó `exited|1|false`.

La salida stderr/stdout del bootstrap fue redirigida a `/dev/null` y el contenedor usó
`--log-driver none`; el log no contiene la causa raíz. No se iniciaron Edge Runtime, Pages/
workerd integrado, PostgREST ni PG17; no se ejecutó SQL, Auth ni correo, y no hubo acceso
remoto. El runner no hizo cleanup ni resume: snapshot, contenedores de bootstrap y volúmenes
permanecen preservados. En particular, los volúmenes Deno r3 podrían contener dependencias
parciales; no inspeccionar, reutilizar ni eliminar sin instrucción/JIT separado. El resultado
es **NO-GO** y no autoriza un retry. Evidencia: log sanitizado
[`h3req1_c03_integrated_run_2026-10-06_r1.log`](h3req1_c03_integrated_run_2026-10-06_r1.log).

## Preparación estática R2 pre-JIT — corte pre-ejecución, 2026-10-06

R1 quedó consumido tras el fallo del bootstrap Deno. Su causa raíz no está determinada:
stderr/stdout fueron suprimidos y `log-driver none` no guardó una copia recuperable. No se
inspeccionaron ni reutilizaron los volúmenes R1 r3; permanecen preservados, potencialmente
parciales. R2 conserva ese límite y no ejecuta Docker para mirar o limpiar esos recursos.

La corrección preparada permite diagnóstico sin guardar el texto libre de bootstraps: Miniflare,
Pages y Deno se resumen mediante clases allowlisted (`permission-denied`, `not-capable`,
`missing-file-or-directory`, `integrity-or-checksum-failure`, `lockfile-resolution-failure`,
`module-resolution-failure`, `network-or-registry-failure`, `bootstrap-error` o
`no-recognized-safe-category`). `control()` pasa stdout/stderr por el redactor, que elimina
líneas con marcadores sensibles y reconoce tokens conocidos, JWT, Bearer y userinfo de URLs.
El JSON de digests solo se registra si tiene exactamente las cuatro claves esperadas y valores
hexadecimales SHA-256 de 64 caracteres. Ningún bootstrap recibe credenciales de host; Deno
solo recibe `HOME` y `DENO_DIR`, npm solo `HOME` y `npm_config_cache`. `set -o pipefail` conserva
los códigos de salida Docker/bootstrap a través de los resúmenes seguros.

Manifiesto actual: `tests/h3req1-c03-integrated.sha256`, **62 inputs**, verificación local
`sha256sum -c` 62/62. SHA-256 de manifiesto para el guard JIT R2:
`0e1634876956d8031ac99057dfc14936f65896b7a0d4626b642bfe8c4239aa11`. `bash -n` y
`git diff --check` terminaron con exit 0. Rama/HEAD esperados permanecen
`feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

JIT exacto propuesto en ese corte: `H3-CLOSE-03-INTEGRATED-2026-10-06-R2`; entonces estaba
**pendiente de aprobación**. La invocación con guards fue:

```bash
bash tests/h3req1_c03_integrated_drill.sh --jit H3-CLOSE-03-INTEGRATED-2026-10-06-R2 \
  --manifest-sha256 0e1634876956d8031ac99057dfc14936f65896b7a0d4626b642bfe8c4239aa11
```

El JIT debe autorizar explícitamente los tres bootstraps sobre Docker `bridge`, sin allowlist
FQDN ni limitación efectiva de destinos: dos `npm ci` (el de Miniflare/workerd mantiene
lifecycle scripts) y `deno cache`; resolver/registry puede alcanzar egress general. Debe
cubrir las imágenes locales fijadas, los recursos R2 enumerados abajo, preservación de logs y
recursos ante fallo/PASS, y `DROP SCHEMA public/private CASCADE`, roles, DDL/DML exclusivamente
en el PG17 R2 descartable con tmpfs. Al detener ese PG17, se pierde intencionalmente su base.
No autoriza Supabase remoto Free/Pro, correo, sincronización de datos, cleanup de R1, push,
PR, merge, deploy ni otros workflows.

R2 usa nombres nuevos y no monta/reutiliza caches r3: contenedores
`h3req1-c03-source-snapshot-20261006-r2`,
`h3req1-c03-bootstrap-miniflare-20261006-r2`,
`h3req1-c03-bootstrap-pages-deps-20261006-r2`,
`h3req1-c03-bootstrap-edge-deps-20261006-r4`,
`h3req1-c03-dependency-cache-verify-20261006-r2`,
`h3req1-c03-integrated-runtime-20261006-r2`,
`h3req1-c03-integrated-pg17-20261006-r2`,
`h3req1-c03-integrated-postgrest-20261006-r2`,
`h3req1-c03-integrated-edge-active-20261006-r2` y
`h3req1-c03-integrated-edge-suspended-20261006-r2`; redes
`h3req1-c03-integrated-edge-20261006-r2` y
`h3req1-c03-integrated-data-20261006-r2`; volúmenes
`h3req1-c03-integrated-source-snapshot-20261006-r2`,
`h3req1-c03-integrated-tls-20261006-r2`,
`h3req1-c03-integrated-miniflare-node-modules-20261006-r2`,
`h3req1-c03-integrated-pages-node-modules-20261006-r2`,
`h3req1-c03-integrated-edge-deno-cache-20261006-r4` y
`h3req1-c03-integrated-edge-node-modules-20261006-r4`. En el corte pre-JIT, el resultado aún
no existía; la ejecución posterior y su log se documentan a continuación. Un fallo requiere
detenerse y preservar recursos, sin cleanup/resume automático.

## Resultado de ejecución autorizada R2 — 2026-10-06

El responsable aprobó el JIT exacto `H3-CLOSE-03-INTEGRATED-2026-10-06-R2` y el digest
`0e1634876956d8031ac99057dfc14936f65896b7a0d4626b642bfe8c4239aa11`. El runner verificó
62/62 al inicio. Snapshot y los dos bootstrap npm terminaron; Deno Edge falló con exit 1 en
`isolated-deno-edge-dependency-bootstrap-with-registry-egress`. El log registra dos veces
`bootstrap-diagnostic-class=no-recognized-safe-category` y una vez
`bootstrap-diagnostic-class=lockfile-resolution-failure`, además de
`Deno Edge bootstrap process exit=1`. Esto apunta a una categoría de resolución del lock, no
confirma la causa raíz: no se guardó texto libre y el detalle disponible es insuficiente.

Solo se alcanzaron el snapshot y los bootstrap: contenedores source snapshot, Miniflare, Pages
y Deno Edge; los dos npm completaron y Deno terminó fallido. Volúmenes source snapshot,
Miniflare modules, Pages modules, Deno cache r4 y Edge `node_modules` r4 quedan preservados,
potencialmente parciales. No se crearon redes internas ni se iniciaron Edge Runtime, Pages/
workerd integrado, PostgREST o PG17; no se ejecutó SQL/Auth/correo y no hubo acceso remoto.
Los caches R1 r3 no fueron inspeccionados, montados, reutilizados ni limpiados. No se ejecutó
cleanup/resume. Evidencia: log sanitizado
[`h3req1_c03_integrated_run_2026-10-06_r2.log`](h3req1_c03_integrated_run_2026-10-06_r2.log).

El JIT R2 queda consumido y el resultado es **NO-GO**. No hay aprobación de retry ni limpieza.
Cualquier investigación adicional, cambio del lock/bootstrap o nuevo intento necesita otro
ciclo y un JIT R3 con manifiesto actualizado; recursos R2 y caches r4 permanecen preservados.

## Preparación estática del resolver Deno R3 — corte pre-JIT, 2026-10-06

El log R2 no confirma causa raíz. La inspección estática encontró una hipótesis concreta:
`tests/h3req1-c03-bootstrap/package.json` incluye `esbuild`, `miniflare` y `typescript`; el
lock v4 se generó desde ese directorio junto al `index.ts` Edge. El drill copia dicho lock al
directorio `supabase/functions/admin-invite`, donde no hay ese `package.json`, y luego resuelve
con `--frozen`. Este desajuste de contexto podría explicar el diagnóstico de lock, pero no está
confirmado. No se inspeccionaron volúmenes Docker R1/R2; véase la salvedad de alcance de
auditoría registrada al final de esta sección.

La preparación R3 separa el grafo: `tests/h3req1-c03-edge-lock-resolver/deno.json` contiene solo
`nodeModulesDir: auto`; el fixture no tiene `package.json`. Source y config se montan read-only;
el contenedor copia solo esos inputs a un workspace named volume vacío y ejecuta `deno cache
--node-modules-dir=auto --config=/workspace/deno.json
--lock=/workspace/deno-edge-runtime-v1.74.3-r3.lock --frozen=false /workspace/index.ts`.
El proceso usa `--user 0:0` para escribir el volumen; rootfs read-only, `--cap-drop=ALL` y
`no-new-privileges` limitan privilegios, y las únicas rutas escribibles son DENO_DIR, workspace
y `/tmp`. Antes de terminar con exit 0, el shell fijo valida existencia/formato v4. Solo después
de exit 0 se copia el candidato a staging de evidencia, se valida otra vez y se promueve
atómicamente al path final; no hay bind mount host writable. No se usa npm, `npm ci` ni
`--allow-scripts`; no se pasan credenciales. El `--entrypoint /bin/sh` requiere que la shell y
`deno` estén disponibles en la imagen fijada; cualquier fallo impide promover el lock. El
output libre se reduce a clases constantes allowlisted y `pipefail` conserva el fallo real.

Manifiesto R3 `tests/h3req1-c03-edge-lock-resolver-r3.sha256`: **4 inputs**, todos deben
verificar antes de resolver:

| Input | SHA-256 |
|---|---|
| `tests/h3req1_c03_edge_lock_resolver_r3.sh` | `76ecba4e5b30df66ed096c8f4ef5e2a99318c6f9b37cfcb7f48d4f8eb6c78dbb` |
| `tests/h3req1-c03-edge-lock-resolver/deno.json` | `5335690600914ad53e9b4873a8287e0baba01902ef94eec02d01b35ca6d7b3be` |
| `tests/h3req1-c03-edge-lock-output-r3/.gitkeep` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `supabase/functions/admin-invite/index.ts` | `1569b90394b313a4b42e4e50158da077cec42d26356c0d713b16535f47053a60` |

SHA-256 del manifiesto completo: `60805a1aca0dd3fbd96aeabe2f18a3a6c3efa6df8cafccaf184a66cfb92334f0`.
`bash -n`, `git diff --check` y `sha256sum -c` pasaron 4/4 en el gate pre-JIT.
Rama/HEAD fijados: `feat/h3req1-sync-20261002` /
`4eb4d877a50b012bb630a129bd0c74482c33be9c`.

JIT exacto propuesto en ese corte: `H3-CLOSE-03-EDGE-LOCK-RESOLVER-2026-10-06-R3`, entonces
**pendiente de aprobación humana**. Invocación con guards:

```bash
bash tests/h3req1_c03_edge_lock_resolver_r3.sh \
  --jit H3-CLOSE-03-EDGE-LOCK-RESOLVER-2026-10-06-R3 \
  --manifest-sha256 60805a1aca0dd3fbd96aeabe2f18a3a6c3efa6df8cafccaf184a66cfb92334f0
```

El JIT debe aceptar egress general de Docker `bridge` sin allowlist FQDN durante únicamente
este proceso Deno (la resolución accede JSR/npm registry). Comprende la imagen local fijada
`denoland/deno:2.1.4@sha256:bc48369c9b1810da957cabcac234094a691f94cb6cd0e88d533ccac89f2f0cb9`; ningún
pull. Recursos nuevos que quedarían preservados: contenedor
`h3req1-c03-edge-lock-resolver-20261006-r3`, volúmenes
`h3req1-c03-edge-lock-deno-cache-20261006-r5` y
`h3req1-c03-edge-lock-workspace-20261006-r3` (incluye `node_modules`/lock candidato); staging
`.context/evidencia/h3req1_c03_edge_lock_r3_candidate.tmp` se crea solo después de exit 0 y
validación dentro del contenedor; log
`.context/evidencia/h3req1_c03_edge_lock_resolver_2026-10-06_r3.log`; lock final
`tests/h3req1-c03-edge-lock-output-r3/deno-edge-runtime-v1.74.3-r3.lock`. No autoriza leer,
montar, reutilizar ni eliminar recursos/caches R1/R2; tampoco autoriza el drill integrado,
runtime Edge/Pages, PG17, SQL, Supabase remoto, correo, push, PR, merge, deploy o cleanup.
La creación exige nombre exacto libre y verifica un label de run nonce nuevo por volumen para
evitar reuso ante una carrera. Perfil: 2 CPUs, RAM/swap total 2 GiB, 256 procesos y `/tmp`
tmpfs de 512 MiB. No hay cuota de disco para los named volumes ni timeout de pared; el JIT debe
aceptar expresamente el potencial consumo del Docker data-root y duración no acotada, además
del egress.

En el corte pre-ejecución estaban cerrados los gates estáticos y la auditoría no detectó
HIGH/CRITICAL ni blockers. El riesgo MEDIUM residual (egress general, UID 0, named volumes sin
cuota y sin timeout) se incluyó en el JIT. El resultado de la ejecución aprobada se registra
debajo. Es tooling local sin cambio del contrato de producto; la atestación sanitizada H3 se
conserva como límite de ejecución local.

Salvedad de alcance de auditoría: una búsqueda estática del subagente se extendió por accidente
a archivos generados en `tests/h3req1-c03-bootstrap/node_modules/.deno` y leyó coincidencias;
no modificó archivos, no incorporó sus contenidos a la evidencia y no inspeccionó los
volúmenes Docker R1/R2. No se determinó si esos archivos tienen relación con caches anteriores.
No volver a acceder, reutilizar ni limpiar esa ruta sin instrucción humana separada.

## Resultado de ejecución autorizada del resolver R3 — 2026-10-06

El responsable aprobó y consumió el JIT exacto `H3-CLOSE-03-EDGE-LOCK-RESOLVER-2026-10-06-R3`
con el manifiesto SHA-256 `60805a1aca0dd3fbd96aeabe2f18a3a6c3efa6df8cafccaf184a66cfb92334f0`.
El runner verificó 4/4 inputs y terminó exit 0. Deno generó lock formato v4 en
`tests/h3req1-c03-edge-lock-output-r3/deno-edge-runtime-v1.74.3-r3.lock`, SHA-256
`ccb3d17f01947e679fb530ba7cbc9d252263ab1051d1d9ab21429eecde7ba428`. `specifiers` registra
solo `jsr:@supabase/functions-js`, `npm:@supabase/supabase-js` y el transitivo
`npm:openai`; el lock no contiene las dependencias tooling `miniflare`, `esbuild` ni
`typescript`. Esto valida la resolución aislada, pero no equivale a ejecutar Edge Runtime ni
a un pase frozen/integrado.

El staging se validó y promovió al path final. Contenedor y volúmenes R3 quedaron preservados;
no se ejecutó cleanup ni se accedió a caches/volúmenes R1/R2. En el corte de esa ejecución no
se había modificado aún el runner integrado ni iniciado Edge Runtime, Pages/workerd, PostgREST
o PG17; no se ejecutó SQL ni hubo acceso remoto. El JIT R3 está consumido y no autoriza retry,
limpieza ni el drill integrado. Evidencia: [log del resolver R3](h3req1_c03_edge_lock_resolver_2026-10-06_r3.log).

## Preparación estática del candidato integrado R4 — corte pre-JIT, 2026-10-06

El candidato sustituye los inputs Deno mezclados de Miniflare en el snapshot por el config
aislado `tests/h3req1-c03-edge-lock-resolver/deno.json` y el lock R3 aprobado
`tests/h3req1-c03-edge-lock-output-r3/deno-edge-runtime-v1.74.3-r3.lock` (SHA-256
`ccb3d17f01947e679fb530ba7cbc9d252263ab1051d1d9ab21429eecde7ba428`). El runner copia estos
inputs a `supabase/functions/admin-invite/deno.json` y `deno.lock`, comprueba ambos con `cmp`,
rechaza `package.json` en ese directorio y ejecuta solo en el futuro `deno cache` con `--config`
explícito y `--frozen`. El Edge Runtime recibiría el mismo snapshot/caché validado. No se usa
el bootstrap `deno.json`/lock R2. El lock y todos los demás inputs son parte del manifiesto;
el snapshot se construye con la lista de archivos aprobada, no con un checkout mutable completo.

Digest del manifiesto integrado actualizado: **62 inputs**, SHA-256
`e5d72e06b04fcfd3f68abaeea77fef81c982f24e20e587732de65b63b58167a7`. Hash del runner:
`28c417bee4bd0f3c0d9d1e576397c8be1af9e7d0309b81a58c1fcc4f3639f474`. Gates finales:
`bash -n`, `git diff --check`, `sha256sum -c` 62/62; rama/HEAD
`feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c`. Auditoría final de
solo lectura: cero HIGH/CRITICAL/bloqueantes; el LOW de interrupción fue mitigado con traps
HUP/INT/TERM que registran fase/señal/salida y no limpian/reanudan. Persiste un MEDIUM de
egress bridge general, scripts de ciclo de vida, límites cgroup/cuota de disco/timeout, que el
JIT debe aceptar expresamente. Ningún Docker/Deno/SQL/runtime se ejecutó en este ciclo.

JIT exacto propuesto en ese corte:
`H3-CLOSE-03-INTEGRATED-2026-10-06-R4`. Comando protegido, entonces pendiente de aprobación:

```bash
bash tests/h3req1_c03_integrated_drill.sh \
  --jit H3-CLOSE-03-INTEGRATED-2026-10-06-R4 \
  --manifest-sha256 e5d72e06b04fcfd3f68abaeea77fef81c982f24e20e587732de65b63b58167a7
```

La autorización futura debe cubrir de forma explícita: tres bootstraps aislados en Docker
`bridge` con egress general/no FQDN allowlist (dos `npm ci`; Miniflare/workerd conserva
lifecycle scripts y Pages usa `--ignore-scripts`; más `deno cache --frozen` a partir del lock),
imágenes fijadas PostgreSQL, PostgREST, Node, Deno y Edge Runtime; creación/uso de los 10
contenedores, 2 redes y 6 volúmenes R4 listados en `.context/estado_del_proyecto.md`; y DDL/DML
solo en el PostgreSQL 17 nuevo, desechable y almacenado en tmpfs. No se publican puertos. No
hay límites cgroup globales de CPU/RAM, cuota de disco de named volumes ni timeout global; los
tmpfs individuales sí están acotados por los flags del runner. El JIT debe aceptar consumo
potencial del Docker data-root y duración no acotada. Ante fallo no hay cleanup ni resume y se
preservan los recursos/log; el cierre exitoso detiene servicios y PG tmpfs (se pierde su DB)
pero conserva contenedores y volúmenes. Los guards comparan nombres exactos tras filtros
parciales y cada volumen nuevo lleva labels JIT/manifiesto/nonce para impedir reuso por carrera.

Exclusiones: jamás montar, inspeccionar, reutilizar o eliminar recursos/caches R1/R2 ni caches
volumen R3; el único artefacto R3 permitido como input es el lock file cuyo SHA está fijado.
No autoriza Supabase remoto Free/Pro, Auth externo, correo, Cloudflare real, datos operativos,
push, PR, merge, deploy, schedules, workflow dispatch ni cleanup. C02 v4 y C03 SQL v3 siguen
PASS preservados y no se repiten; el PG17 local nuevo corre solo el conjunto de SQL versionado
indicado por el manifiesto.

Compatibilidad y rollback del cambio de tooling: **expand** agrega lock/config R3 al candidato
de test; **compatibilidad** mantiene sin cambios el contrato de producto/Edge y la ejecución
de producción; **deploy** no ocurre ni se autoriza; **contract** corresponde a promoción
protegida futura. Si el resolver integrado o un gate falla, parar, no hacer cleanup/resume,
preservar el estado, y no degradar silenciosamente al lock R2 fallido. La restauración o
limpieza de recursos requiere un JIT separado. La auditoría estática permitió presentar el
JIT, pero no lo aprobó.

## Resultado de ejecución autorizada del drill integrado R4 — 2026-10-06

El responsable aprobó y consumió el JIT exacto `H3-CLOSE-03-INTEGRATED-2026-10-06-R4` con
manifiesto SHA-256 `e5d72e06b04fcfd3f68abaeea77fef81c982f24e20e587732de65b63b58167a7`. El runner
verificó 62/62 hashes y completó source snapshot, dos bootstrap npm, Deno `cache --frozen` y
verificación de digests de dependencias. En fase `isolated-workerd-bootstrap`, el runtime se
inició, pero el control agotó los 60 intentos de `healthz`, reportando `NO-GO: runtime state
timeout: healthz` y exit 1. El log contiene tres `bootstrap-diagnostic-class=no-recognized-safe-category`;
no permite atribuir causa raíz del timeout. Evidencia: [log R4](h3req1_c03_integrated_run_2026-10-06_r4.log).

No se alcanzaron las fases PG17/PostgREST, Edge active/suspended, user worker ni SQL. No hubo
acceso remoto, Auth externo, correo ni puertos publicados. El runner preservó recursos/logs y
no hizo cleanup/resume. No se inspeccionó estado ni logs de contenedores tras el fallo; tampoco
se montaron caches R1/R2/R3. Solo se incorporó como archivo el lock R3 ya fijado en el manifiesto.
C02 v4 y C03 SQL v3 permanecen PASS, sin repetición. R4 está consumido: el diagnóstico del
runtime, cualquier inspección adicional y cualquier retry/cleanup requieren JIT nuevo. El
resultado es **NO-GO**; no inferir causa raíz del `healthz timeout`.

## Preparación estática de diagnóstico read-only D1 — corte pre-JIT

Tras el NO-GO R4 se propone una inspección de metadata del único contenedor
`h3req1-c03-integrated-runtime-20261006-r4`. Runner
`tests/h3req1_c03_integrated_runtime_diag_d1.sh`; manifiesto
`tests/h3req1-c03-integrated-diagnostic-r4-d1.sha256` (**4 inputs**), SHA-256
`19618493b6ecc5148dd6320a8c915f97563b3d79eea57507950b08928c38a914`. Runner SHA-256
`e77be4ef49976dab09ccbb0a6c78934eade5ad3f8514fe8d4bab82078ea48239`. Inputs fijan el manifiesto
R4 (`e5d72e06b04fcfd3f68abaeea77fef81c982f24e20e587732de65b63b58167a7`) y log R4
(`208e42cb55cd7de5d74a9960655ac3cdec6accbeab1fc5f00a7a3e8eb047eb34`), además del runner R4
(`28c417bee4bd0f3c0d9d1e576397c8be1af9e7d0309b81a58c1fcc4f3639f474`). Gates finales:
`bash -n`, `git diff --check`, `sha256sum -c` 4/4; auditoría final sin HIGH/CRITICAL/MEDIUM
ni LOW bloqueantes. El LOW de log-driver se mitigó exigiendo exactamente `none`.

JIT exacto propuesto en ese corte, entonces **pendiente**:
`H3-CLOSE-03-INTEGRATED-DIAGNOSTIC-2026-10-06-D1`. Comando protegido:

```bash
bash tests/h3req1_c03_integrated_runtime_diag_d1.sh \
  --jit H3-CLOSE-03-INTEGRATED-DIAGNOSTIC-2026-10-06-D1 \
  --manifest-sha256 19618493b6ecc5148dd6320a8c915f97563b3d79eea57507950b08928c38a914
```

El alcance propuesto era solo `docker inspect --format` sobre ese nombre exacto, validando
nombre/image digest y emitiendo enums controlados de estado, exit code, OOM y log-driver. No
consulta listas de contenedores, redes, volúmenes o caches; no hace `docker exec`, no lee
`docker logs`, no abre puertos y no arranca/detiene/reinicia/limpia nada. Solo lee el log R4
guardado para confirmar el timeout esperado. La evidencia nueva iría a
`.context/evidencia/h3req1_c03_integrated_runtime_diag_2026-10-06_d1.log`; no crea recursos.

El runtime R4 fue creado con `--log-driver none`, así que este diagnóstico no puede recuperar
stdout/stderr del servicio; únicamente informa metadata del container. No presentar metadata
como causa raíz. Cualquier inspección más amplia, instrumentar logging, leer logs, ejecutar
comandos en el container o reintentar requiere otro JIT/ciclo. No autoriza inspección/uso de
caches o recursos R1/R2/R3, volúmenes R4, PG17/PostgREST, SQL, Supabase remoto, correo,
Cloudflare, push, PR, merge, deploy ni cleanup. La transición es read-only y no modifica
contrato: expand/contract/deploy no aplican; rollback consiste en no ejecutar y preservar el
estado.

## Resultado de ejecución autorizada del diagnóstico D1 — 2026-10-06

El responsable aprobó/consumió el JIT exacto `H3-CLOSE-03-INTEGRATED-DIAGNOSTIC-2026-10-06-D1`
con manifiesto SHA-256 `19618493b6ecc5148dd6320a8c915f97563b3d79eea57507950b08928c38a914`.
El runner verificó 4/4 inputs y realizó su única llamada Docker: `inspect --format` del
contenedor R4 exacto. La metadata recibida no pasó la igualdad literal de `.Config.Image` con
el string pinned; el runner suprimió el valor y emitió un NO-GO por mismatch del digest pinned,
exit 1 en `read-only-inspect-exact-r4-runtime`. Esto **no confirma** que la imagen real fuera
distinta: podría ser solo una diferencia en la forma (tag/digest) reportada por Docker. No se
emitieron status/exit/OOM/log-driver, no se obtuvo causa raíz y no se leyó stdout/stderr
(`log-driver none`).

Reporte sanitizado D1: [log de diagnóstico](h3req1_c03_integrated_runtime_diag_2026-10-06_d1.log),
SHA-256 `82cda545f327eb721fb1442ba91f962b5b3eb4b4e50a2a86e0c2e175f5a85347`. No se ejecutó
`docker logs/exec`, no se inspeccionaron redes/volúmenes/caches, y no hubo stop/restart/cleanup
ni acceso remoto. El contenedor/recursos R4 quedan preservados. D1 está consumido: cualquier
nueva inspección, cambio al guard o retry requiere ciclo/JIT nuevos. R4 y D1 quedan **NO-GO**;
no inferir causa raíz del mismatch ni del `healthz timeout`.

## Preparación estática del diagnóstico D2 — runtime R4 — JIT pendiente

D2 es un runner/manifiesto nuevo, no altera ni reutiliza el runner D1 consumido. JIT propuesto
`H3-CLOSE-03-INTEGRATED-DIAGNOSTIC-2026-10-06-D2`; runner
`tests/h3req1_c03_integrated_runtime_diag_d2.sh`, SHA-256
`f337ed07de258c632c1cfcfa9f6292f8b1f19389bb06112fc5f8bec192e96447`; manifiesto de cinco
inputs `tests/h3req1-c03-integrated-diagnostic-r4-d2.sha256`, SHA-256
`6f6f4e451e45dec30c8145b2bb328286786aaf36d887635ae0be14f5e4547e6c`. Fija los digests de
R4 manifest/runner, log R4 y reporte D1: `e5d72e06b04fcfd3f68abaeea77fef81c982f24e20e587732de65b63b58167a7`,
`28c417bee4bd0f3c0d9d1e576397c8be1af9e7d0309b81a58c1fcc4f3639f474`,
`208e42cb55cd7de5d74a9960655ac3cdec6accbeab1fc5f00a7a3e8eb047eb34` y
`82cda545f327eb721fb1442ba91f962b5b3eb4b4e50a2a86e0c2e175f5a85347`. Al igual que D1,
valida JIT/digest/branch/HEAD, paths regulares no symlink y un destino de evidencia nuevo.

Tras el NO-GO D1, D2 **no consulta `.Config.Image`**: la comparación literal anterior no
permitió distinguir normalización de Docker de una discrepancia real, y reintentar identidad
de imagen queda fuera del alcance. Si un JIT futuro lo autoriza, D2 hará un único
`docker inspect --format` del nombre exacto `h3req1-c03-integrated-runtime-20261006-r4`, con
solo `.Name`, `.State.Status`, `.State.ExitCode`, `.State.OOMKilled` y
`.HostConfig.LogConfig.Type`; la salida valida enums/códigos y exige `log-driver=none`. No usa
`docker logs/exec`, listas, redes, volúmenes/caches, ni mutaciones/stop/restart/cleanup/resume.
Lee los dos logs locales fijados para verificar los outcomes R4/D1 y escribe solo el reporte
sanitizado `.context/evidencia/h3req1_c03_integrated_runtime_diag_2026-10-06_d2.log`. Como el
runtime tiene logging Docker deshabilitado, no recuperará stdout/stderr y no promete causa raíz.

Gates finales: `bash -n`, `git diff --check`, `sha256sum -c` 5/5; rama/HEAD
`feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c`; output D2 ausente.
La auditoría inicial encontró LOW porque `tests/` no se rechazaba si era symlink; se corrigió
con un guard antes de lecturas. La reauditoría cerró ese LOW de implementación, sin hallazgos
técnicos HIGH/CRITICAL/MEDIUM, y detectó un LOW documental porque algunas secciones aún decían
“pendiente”; esa inconsistencia queda corregida en esta actualización. No se ejecutó
Docker/inspect ni otra operación. El comando protegido
solo tras auditoría y aprobación humana exacta sería:

```bash
bash tests/h3req1_c03_integrated_runtime_diag_d2.sh \
  --jit H3-CLOSE-03-INTEGRATED-DIAGNOSTIC-2026-10-06-D2 \
  --manifest-sha256 6f6f4e451e45dec30c8145b2bb328286786aaf36d887635ae0be14f5e4547e6c
```

D2 no autoriza otro acceso distinto de ese `inspect`, ni logs de servicio, recursos/caches
R1/R2/R3, volúmenes R4, PG17/PostgREST, SQL, Supabase remoto, correo, Cloudflare, push, PR,
merge, deploy, cleanup o retry. Rollback: no ejecutar y preservar recursos/evidencias; al ser
diagnóstico metadata-only no se modifica contrato y expand/deploy/contract no aplican. Cualquier
ampliación necesita nuevo ciclo/JIT. C02 v4 PASS y C03 SQL v3 PASS permanecen sin repetición.
