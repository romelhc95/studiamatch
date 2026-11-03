# G07 — resultado R18 y clasificación del transporte Edge/Auth

## Candidato y prueba integrada

- Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
  `feat/h3req1-sync-20261002`, HEAD baseline
  `4eb4d877a50b012bb630a129bd0c74482c33be9c`; WIP resumido: 520 entradas.
- Runner R18 SHA-256 `423eca58e71995d0c877f8a539495ccfcc15e9de37b123a5c4546e7ff34051fc`;
  contrato `dfe8bc4377c91118b7af13798827ad8461273c5fbf580d1c2e117f6a57602b2e`;
  runtime `2027f2a04c9c1906b8e14cbc1c618922498e1bcdb346337ab2fb069aa01cf381`.
- Manifiesto actual R18: 69 entradas; SHA-256
  `0be7c1597beb3acbf5755d733febb3e842c662eb661d018ecb91ed92f8ed1a02`.
- Checks previos al runtime: manifiesto 69/69, pruebas del contrato 19/19,
  `node --check`, `bash -n` y `git diff --check`: PASS.
- Ejecución integrada: exit 1 en `real-edge-invite-held-after-reservation`,
  `INVITE_EARLY_UNAUTHORIZED`. Log sanitizado:
  [R18](h3req1_c03_integrated_run_2026-10-10_r18.log), SHA-256
  `7601cf6b955dbf73fdbfe6906e6489c9d63f0bb756a03094623963dc5932f188`.
- Counters R18: `authUserAccepted=1`, `functionCalls=1`, pero
  `adminMemberRequests=0`, `requestAdmission=0` y `invitationReserve=0`. El contador
  Auth compartido no identifica qué cliente lo originó; por eso no se atribuye esa
  aceptación a Edge. No se acreditó reserva y el runner detuvo sus servicios.

## Reproducción focalizada

- Se envió una solicitud sintética directa a Edge, sin correo ni PostgREST disponible.
  Respondió 401 `unauthorized`; los contadores gateway antes/después quedaron en cero.
- Se ejecutó un fixture temporal de Edge Runtime fijado a la misma imagen y red interna,
  con `DENO_CERT` apuntando a la CA sintética. El probe hizo un único GET sin credencial
  real a `/auth/v1/user`; solo informó estado/código.
- Probe V1: `FETCH_FAILED`, cero solicitudes al gateway. Probe V2, con clasificación
  cerrada del error: `TLS_UNKNOWN_ISSUER`, cero solicitudes al gateway. Esto localiza el
  fallo antes de HTTP/Auth, no en PostgREST, membresía, reserva o cuota.
- El archivo CA `ca.pem` montado era legible, pero `openssl x509` informó que no tenía
  extensiones. El certificado servidor tenía SAN `DNS:local.supabase.co`, issuer igual
  al sujeto CA y OpenSSL `verify=OK`; Deno, en cambio, clasificó el issuer como no confiable.
- Hipótesis concreta a validar en R19: el certificado raíz del fixture se genera sin
  `basicConstraints CA:TRUE` ni `keyUsage keyCertSign`, por lo que Deno no lo acepta como
  CA aunque OpenSSL lo verifica. No se atribuye el fallo a código funcional ni a Docker.

La documentación oficial de Deno define `DENO_CERT` como la variable para cargar CA en
PEM; el runner ya suministra esa variable y el archivo es legible. Referencia:
[Deno environment variables](https://docs.deno.com/runtime/reference/env_variables/#special-environment-variables).

## Fallos de preparación sin efecto en servicios

Las invocaciones exploratorias anteriores a la solicitud R19 se detuvieron antes de hacer
una petición Auth por sintaxis del probe, método GET en el lector de un control que exige
POST, ruta de servicio Edge incorrecta y copia al rootfs read-only. Se corrigieron solo los
helpers del diagnóstico; el contenedor creado por error de copia fue verificado como
`created` con etiqueta propia y retirado por ID exacto, sin `-v`. Esos fallos no son
resultados de producto ni retries de R18.

El source del probe y su SHA quedan preservados:

- V1: `2459b5b4d17c53dff558fd67ca468c230f366567af89f923e73e04dd4b7241ee`.
- V2 clasificador: `b1ac07206517cb0765ba51dec3b399e036ba8d4ecc44bbb78419c44a4f615365`.

## Estado y siguiente paso

G01–G06 completos; G07 parcial; G08–G09 pendientes; G10 remoto pendiente. Sin cambio de
puntos: tablero histórico G01–G10 **60%**; cierre local G01–G09 **6/9 = 66.67%**.
R18 no acredita C03 integrado.

El cambio siguiente es local al harness: generar CA sintética v3 con restricciones de CA
explícitas y validar CA/leaf antes de arrancar Edge. Después se revalida con runner R19
nuevo, snapshot/manifiesto propio y stop-on-failure. Los servicios R18 que siguen activos
son solo runtime, Edge activo y el fixture diagnóstico; PG17 y PostgREST están detenidos.
Los logs, scripts, snapshot, volumen TLS y cachés quedan preservados.
