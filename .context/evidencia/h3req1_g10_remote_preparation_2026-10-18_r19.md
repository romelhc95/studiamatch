# H3REQ1 — Lecturas remotas B y reconciliación de publicación — R19

**Fecha de corte:** 2026-10-18; relectura de objetos públicos 21:04 UTC. **Resultado:** B parcialmente configurado/desplegado; gate B **NO COMPLETO**. No se modificó ningún servicio durante estas lecturas.

## Comprobaciones del conector

### Cloudflare Pages Preview

Lectura filtrada del proyecto Pages `studiamatch`; los valores no se registraron:

- La rama de producción del proyecto sigue siendo `main`; esta reconciliación no la modifica.
- En Preview están presentes `ADMIN_QUOTA_HMAC_KEY`, `ADMIN_RPC_GATEWAY_HMAC_KEY` y `ADMIN_SESSION_ACTIVITY_HMAC_KEY` con tipo `secret_text`. El conector oculta sus valores y no permite comparar secretos.
- `ADMIN_ALLOWED_HOSTS` está presente y su contenido coincide exactamente con los dos hosts previstos en el paquete B R18. La URL Supabase coincide con Free Development.
- El binding Service `ADMIN_QUOTA` ya está presente y apunta al Worker `studiamatch-admin-quota`.
- `ADMIN_RPC_GATEWAY_KEY_ID` no aparece en Preview. Los dos overrides locales `ADMIN_BFF_ALLOW_LOCALHOST` y `ADMIN_BFF_ALLOW_LOCAL_AUTH_MOCK` no aparecen. `NEXT_SUPABASE_SECRET_KEY` tampoco aparece en Preview.
- El servicio Preview es compartido por Preview de Certification; no se cambió esa coexistencia.

### Worker y Durable Object

- Worker `studiamatch-admin-quota`: el binding `ADMIN_QUOTA_COUNTER` figura como `durable_object_namespace`, clase `AdminQuotaCounter`; existe el namespace `studiamatch-admin-quota_AdminQuotaCounter` asociado al Worker.
- El subdominio público `workers.dev` del script figura deshabilitado.
- El historial devuelve **dos** eventos de deployment API el 2026-10-18 (18:29:54Z y 18:30:22Z), con versiones #1 y #2. La versión #2 es la más reciente. Esto excede el límite aprobado en B R18 de un deployment Worker; no se infiere por qué ocurrió ni se ejecutó otro deployment o rollback.

### Supabase Edge

- Free `aqrldlmlszjtgpqiegaa`: `admin-invite` está `ACTIVE`, versión 14, `verify_jwt=true`.
- El contenido remoto `index.ts` de v14 coincide exactamente, byte por byte, con `supabase/functions/admin-invite/index.ts` del snapshot R18.
- El conector no ofrece getter seguro para nombres/presencia de Edge secrets. No se invocó la función y no se leyeron filas, usuarios, buzones, tokens ni secretos.

### Pages deployments

- No existe deployment del candidato R19. La lista de hasta 20 deployments termina el 2026-09-28; el alias `desarrollo.studiamatch-aty.pages.dev` corresponde a un preview exitoso del 2026-09-27, antes del candidato R19. No se ha servido el candidato Pages/BFF.

## Confirmación manual de secretos y solicitud de rotación

El responsable confirmó manualmente en Supabase Dashboard → proyecto Free → Edge Functions → Secrets que `ADMIN_QUOTA_HMAC_KEY` y `NEXT_SUPABASE_SECRET_KEY` están presentes, y que la clave de cuota coincide con Cloudflare Preview. Esta confirmación humana no procede del conector; no se piden ni se registran valores. El conector observó por separado los tres nombres HMAC como `secret_text` en Preview y que `NEXT_SUPABASE_SECRET_KEY` no está presente allí.

El responsable preguntó cómo obtener y rotar `NEXT_SUPABASE_SECRET_KEY`. No se creó ni reemplazó una clave. La nueva clave se obtiene en Supabase Dashboard → proyecto Free → Project Settings → API Keys → pestaña Secret API keys ([documentación de API keys](https://supabase.com/docs/guides/getting-started/api-keys)). El contrato R18 elimina `NEXT_SUPABASE_SECRET_KEY` de Cloudflare Pages Preview: el BFF no la consume y no debe guardar una clave `sb_secret_`. El consumidor H3REQ1 de esta variable es `admin-invite` en Supabase Edge (el panel de secretos está descrito en la [documentación de Edge Function secrets](https://supabase.com/docs/guides/functions/secrets)); antes de rotar hay que inventariar y coordinar los otros consumidores Development (incluidos los stores locales/CI aplicables), actualizar primero los consumidores autorizados, verificar y retirar la anterior solo al final. La rotación no está cubierta por el B previo y queda sin ejecutar hasta aprobar su paquete JIT concreto. No copiar la clave al chat, capturas, logs, Pages o repositorio.

## Estado de autorización y discrepancias

A sigue consumido en su alcance exacto y no se repite. B/C/D conservan las aprobaciones previas; B ya tiene efectos remotos y no se registra como “sin consumir”. La configuración observada cubre Worker/DO, binding Pages, Preview y Edge v14. El cotejo humano de los dos Edge secret names y de la paridad HMAC ya está satisfecho; B sigue incompleto por el key ID del gateway ausente y los dos deployments Worker frente al máximo aprobado de uno. No se autoriza por inferencia un tercer deployment ni un rollback adicional. Se conserva la versión activa para investigación y se solicita reconciliar este hecho con el paquete B antes de continuar. La solicitud de rotación `NEXT_SUPABASE_SECRET_KEY` es independiente, no consumida y no altera los valores configurados.

El endpoint de protección de rama `desarrollo` continúa respondiendo 403 al conector. La lectura del branch confirma `protected=true` y HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`. La captura entregada por el responsable muestra PR requerido, una aprobación, dismissal de reviews obsoletas, aprobación del último push por alguien distinto del pusher, `security-audit` requerido y rama al día; no muestra todos los controles de bypass ni confirma un required workflow organizacional. No se abrió PR ni se usó bypass.

## Objetos aceptados antes del rechazo PNG

Se consultaron solo metadatos, rutas, hashes y tamaños; no se copió contenido privado en este reporte.

- `create_blob` aceptó cuatro blobs de texto. Las lecturas por SHA coinciden exactamente con los archivos R18 locales: `.context/catalogos_historicos/infra_seguridad_ci.md` (260.259 bytes), `.context/catalogos_historicos/operacion_jit.md` (378.989), `.context/evidencia/h3req1_estado_historico_2026-10-12_public_sanitized_r18.md` (418.262) y `.context/arquitectura.md` (6.714). Sus SHA son `e451860cf3554d16c750ede418b93798aabf5c8a`, `127f2355bd058a70272a66b0e79e721fe77a8e4e`, `ec838f064084baeef129c51bbd9f5ae6b2bf6036` y `98a0e1d464e58178f861145a4e856cb7b6066bb0`.
- También se aceptó el blob del tarball ya versionado `web/vendor/braces-3.0.4-h3.1.tgz` (14.492 bytes; SHA `49e41766fdba85ce4d03638b87031eb01ef54bb2`). No forma parte de una nueva sustitución de dependencia.
- Se aceptó el árbol Git `61c34de74fe71debd8d9dadb6e7f09b7476fee39` (782 entradas, no truncado). Entre esos hashes enlaza `.context/arquitectura.md`; no enlaza ninguno de los 48 visuales del delta R18 ni el PNG rechazado. El árbol incluye 144 imágenes cuyos paths y hashes coinciden exactamente con el árbol baseline; ninguna es uno de los visuales seleccionados del delta. De los cuatro blobs de texto aceptados, arquitectura está enlazada en el árbol y tres objetos sueltos se pudieron recuperar por SHA. El tarball recibió aceptación de `create_blob`, pero el conector no permitió releer sus bytes binarios; no está en el árbol y su recuperabilidad como objeto suelto no quedó verificada.
- El blob del PNG rechazado (`af28a6958195751cc33c22f68ff0beb5c53b8d00`) devuelve `NOT_FOUND`; tampoco aparece en el árbol aceptado. No se purgó ni alteró ningún objeto.
- No se aceptaron commit, ref de rama, PR ni deployment Pages a partir de ese intento. Los objetos sueltos existentes se conservan sin nuevas cargas.

**Relectura R19, solo GET:** el árbol volvió a responder con 782 entradas y `truncated=false`; no contiene el blob del PNG rechazado y conserva el path de arquitectura. Los cuatro blobs de texto se recuperaron de nuevo por SHA y el hash Git calculado en memoria coincide con el SHA consultado en los cuatro casos; su contenido no se emitió ni se guardó. El tarball binario no es recuperable por este conector, por lo que la aceptación previa de `create_blob` no acredita que siga descargable. El PNG rechazado devuelve `NOT_FOUND`. No se subieron objetos nuevos ni se creó commit/ref.

## Paquete local R19

R18 permanece inalterado: HEAD `0d7c89dccffd1146b6cc669d4994787e9b78b533`, árbol `332ae4d156863c1f5524e7d5f6c8f1ecb4424dc2`, directo sobre baseline `4eb4d877a50b012bb630a129bd0c74482c33be9c`. El checkout Syncthing se mantiene intacto en HEAD `a57bc415257ab8154d40d7c71d34c69d0bdaeb0d` con 19.510 registros de estado WIP; no se trasladó al paquete.

La comparación R18 `--no-renames` confirma 1.143 paths (1.050 altas, 86 modificaciones, 7 bajas), 1.136 blobs y dos renombres representados como altas+bajas. El árbol R18 reconstruido en `/tmp` coincide con su SHA exacto. R19 se prepara como rama nueva `feat/h3req1-sync-20261018-r19` desde el baseline, preservando R18 local y sin usar la historia del WIP.

El inventario R18 agrega 46 PNG y 2 WEBM. En R19 los PNG se sustituyen por un derivado neutral; los dos WEBM se excluyen y sus tres referencias afectadas apuntan a la nota R19. Los originales permanecen en el checkout de Syncthing y R18 local. El manifiesto R19 y el cuerpo basado en la plantilla documentan el scope; no se publica hasta pasar validaciones y completar los gates autorizados.

## Siguiente estado

Development permanece **NO-GO**. No se integró ni desplegó el candidato Pages, no se ejecutaron D01/D02, C, D03 ni D04–D14. C y D mantienen sus permisos aprobados y no consumidos; C sigue condicionado a B, D01/D02 previos y lectura de los dos avisos Auth deshabilitados. `main`, Certification y Production no se promovieron ni modificaron.
