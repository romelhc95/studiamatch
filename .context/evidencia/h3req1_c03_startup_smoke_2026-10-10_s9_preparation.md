# H3REQ1 G06 S9 — preparación de snapshot y smoke Pages/workerd

## Estado y alcance

- Checkout candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`.
- Rama/HEAD: `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- WIP al preparar este registro: 55 modificados / 347 entradas untracked / 0 staged; no se limpió ni reemplazó.
- Gate activo: G05 snapshot completo; G06 Pages/workerd y `healthz` permanece bloqueado hasta PASS del snapshot.
- Componente: harness de arranque `tests/h3req1_c03_integrated_runtime.mjs` y fixture de source snapshot. Consumidores: smoke Pages/workerd S9; C03 integrado G07 solo después de G06.
- Contrato: 14 archivos allowlisted (13 entradas fuente y su manifiesto V4), hashes y modos exactos, cero symlinks, red `none` para snapshot, dependencias S3 read-only e internal network sin egress en runtime.

## Recuperación del fallo S8

La evidencia S8 aisló `MiniflareCoreError` en validación de constructor y registró
`path=log|code=custom|keys=none`. El schema fijado de Miniflare 4.20260730.0 confirma que
`log` acepta `Log`, no `{ level: 'error' }`. Se corrigió solamente el logger a
`new Log(LogLevel.ERROR)` y se generó el source manifest V4. Un smoke Miniflare mínimo,
con imagen/dependencias fijadas, `network=none` y fixture sintético, pasó y obtuvo la
respuesta esperada. No altera bindings, workers, fixture C03 ni Edge/DB.

## Ejecución S9 — stop antes de iniciar el receptor

Se ejecutó una vez el runner S9 (`bf28878cbecfa11554978100ea1bd8f34dcee46581bca4feef72bde317c4407b`),
con sidecar `a79edd244558338c94c1667d1d3bc7a30324b35fa0eb2b917595dca576b8617a`. Resultado: exit 1
en `create-container-and-verify-controls-before-start`; el productor tar, receptor y verificador
no comenzaron. La inspección estructurada mostró que Docker serializa el objeto vacío de
`HostConfig.PortBindings` como `{}`, mientras el predicado esperaba `null`. Los demás campos
revisados coincidían; no se relajó el control de puertos.

Quedan conservados la evidencia S9, el contenedor exacto en estado `created` y el volumen S9
etiquetado. El contenedor no se inició; no hubo extracción ni escritura de archivos fuente.
Todavía no se retiraron los recursos; su limpieza selectiva requiere verificar metadata/uso y
ausencia de contenido, dejando intacta la evidencia histórica.

## Ejecución S10 — receptor PASS, contenido no persistió entre mounts

El runner S10 (`354292c1fa0d022d6f771e98c28017afa32ac1281bc5e14126333907132f9f67`, sidecar
`d9b418da57e8fe2b9ba5f8a4cb343bbe21f2c322d1cc4ab1366bfd2e9902cde4`) corrigió el predicado
de puertos y pasó la metadata pre-start. El productor tar, receptor y filtro terminaron exit 0;
el receptor informó 14 archivos, source manifest 13/13 y modos exactos. El verificador posterior
falló exit 1 en `independent-read-only-volume-verification`.

Diagnóstico read-only acotado del volumen S10 mostró: manifest ausente, cero archivos,
symlinks PASS (ninguno), y consecuentemente file-count/permisos FAIL. La metadata confirma
`Driver=local`, `type=tmpfs`, `device=tmpfs`, `size=96m`. Por tanto, en este daemon Docker Desktop
el contenido se observó durante el receptor, pero no quedó disponible en el siguiente montaje
tras detenerse ese contenedor. No es fallo de fuente, hash, extracción ni runtime. El contenedor
receptor exited 0 y el volumen S10 se conservan con la evidencia; no se usaron para Pages.

## Preparación del snapshot S11

Runner S11 `tests/h3req1_c03_source_snapshot_s11.sh`, SHA-256
`1a61fafbddfb316c35186b4e952bc8ca4ee67352b63b18856aa2a847a1889ed7`; sidecar SHA-256
`c33d2a9167f583d34caacbb7e87c9098a670717bdd17cfeb76a3ef6b741d1f55`; source manifest V4
SHA-256 `fdcba48af1ec5ffeba91de0a6fa44022dd3027b85d6b9a5c02afea4c79678233`. El runner fija
rama/HEAD, Docker Desktop/context/endpoint, source allowlist, tamaños, rutas, modos, owner
labels, límites de recursos y recursos con nombres nuevos. Conserva el volumen y contenedor
de snapshot para evidencia. No instala dependencias ni usa egress, DB, Edge, SQL, secretos,
servicios remotos o credenciales operativas.

| Preflight | Resultado |
|---|---|
| Primera sintaxis Bash | FAIL exit 2: `)` adicional en la captura del verificador read-only; no se creó contenedor. Corregido. |
| Primera ShellCheck 0.11.0 warning | FAIL exit 1: SC2155 y SC2034. Separé asignación/readonly y eliminé variable no utilizada. |
| `bash -n` sobre bytes corregidos | PASS |
| Sidecar runner SHA-256 | PASS |
| ShellCheck 0.11.0, severity warning, contenedor aislado | PASS exit 0; imagen oficial local `koalaman/shellcheck:v0.11.0`, digest `sha256:61862eba1fcf09a484ebcc6feea46f1782532571a34ed51fedf90dd25f925a8d` |
| Source manifest V4, 13/13 | PASS |
| Revisión independiente del runner S9 | PASS sin hallazgos bloqueantes para el contrato revisado; el fallo de ejecución fue el predicado `null`/`{}` posterior. |
| Revisión independiente del runner S10 | PASS sin findings en el cambio `null` → `{}`. |
| Revisión independiente del runner S11 | Pendiente; el verificador de permisos/hashes y límites se preparó, pero aún no hay ejecución. |

Los intentos fallidos del preflight no iniciaron Docker. El inventario read-only conserva
snapshot/tools/pages S3, holder, volúmenes y red interna; S2 y runtimes S4–S8 siguen
preservados. El inventario no leyó `Env` ni objetos inspect completos y no retiró recursos.

## Secuencia pendiente

1. Cerrar revisión estática del runner y fijar hashes actuales.
2. Ejecutar el snapshot S9 una vez, con productor, receptor y verificador read-only reportados por separado.
3. Solo tras snapshot PASS, adaptar el smoke de startup a fuente V4 y volumen S9; verificar S3 tools/pages/internal network sin egress.
4. Ejecutar Pages/workerd y probar `healthz` real. Si falla, preservar recursos/evidencia y detener G07.
5. G07 integrado no ha comenzado. G01–G05 continúan completos; ninguna métrica aumenta por esta preparación.

Resultado hasta aquí: S9 falló antes de start; S10 verificó extracción solo dentro del contenedor y falló persistencia posterior del volumen tmpfs. S11 usa volumen local persistente; `bash -n`, ShellCheck warning, sidecar y source manifest pasan. Revisión independiente y ejecución S11 pendientes. G05 sigue sin PASS vigente y G06 NO-GO. Las pruebas G03/G01 preservables no se repitieron.

## S11 revisión de la cota y despacho — 2026-10-10

La revisión independiente inicial encontró que el volumen `local` no lleva cuota y que la
validación de 8 MiB ocurría antes de que `tar` volviera a leer las fuentes. S11 no se había
ejecutado. Se agregó un limitador de streaming: emite como máximo 9 MiB al receptor, pide como
máximo un byte adicional para detectar exceso y sale con código 42 sin reenviar ese byte. El
runner exige exit 0 de tar, limitador, receptor y filtro; el receptor valida hashes, conjunto de
14 archivos, symlinks y modos. Se añadieron dos sintéticos del helper (exactamente el límite y
límite más uno). La evidencia no presenta el volumen como si tuviera cuota.

Pins revisados: runner SHA-256
`b94f47b64d5afe20a6b952ac4e61c16eddaaf1fb808dd770cdf609341bb73f41`; sidecar SHA-256
`39b70d59d93d6ddbaaea97a8c4d452691d7331304cef39c88d0c7827a48e96a1`; el sidecar fija el runner.
Manifiesto fuente V4 SHA-256
`fdcba48af1ec5ffeba91de0a6fa44022dd3027b85d6b9a5c02afea4c79678233` (13/13). `bash -n` y
ShellCheck 0.11.0 `--severity=warning` en contenedor aislado terminaron exit 0. Revisión
independiente final: sin blockers estáticos; autorizó el despacho de S11. No se ejecutaron aún
Docker, snapshot ni runtime en este paso. Candidato confirmado: rama esperada y HEAD baseline;
WIP medido ahora: 55 entradas tracked modificadas / 4365 archivos untracked / 0 staged; se
preserva íntegro.

S11 se ejecutó una vez y terminó exit 1 en `synthetic-archive-limiter-tests`, antes de crear
volumen o contenedor. El caso limit+1 esperaba exactamente los 5 bytes permitidos; el helper
leyó 6 bytes en un chunk y rechazó el chunk completo con exit 42, sin emitir bytes. La cota era
segura; el predicado sintético era demasiado estricto. Evidencia
[`S11`](h3req1_c03_source_snapshot_2026-10-10_s11.md) preserva exit, fase y que no se alcanzó
Docker. La reproducción focalizada confirmó que una lectura separada del byte de sonda permite
emitir los 5 bytes permitidos y aun así rechaza el excedente.

S12 conserva S11 y ajusta solo el limitador para leer `remaining` y, al alcanzar el máximo, leer
un byte de sonda sin reenviarlo. Sintéticos exact-limit y limit+1 pasan; `bash -n`, sidecar,
ShellCheck warning en contenedor aislado y `git diff --check` pasan. Pins S12: runner SHA-256
`e03287ad6d05bbb497f7cfc87aac3ad4fe9ef33a7e059396dd2d9fe0ebd69807`, sidecar SHA-256
`2d89fa0edc87f744a5e602acd5ddf8e9417083c94b1eb4842ef365f2e7028872`, source manifest V4 SHA-256
`fdcba48af1ec5ffeba91de0a6fa44022dd3027b85d6b9a5c02afea4c79678233`. Revisión independiente
final sin blockers: también se precisó que el volumen no tiene cuota y puede conservar contenido
parcial en NO-GO. S12 se ejecutó bajo la autorización local vigente y pasó. Evidencia
[`S12`](h3req1_c03_source_snapshot_2026-10-10_s12.md): source set 540851 bytes, stream limitado a
9437184 bytes, sintéticos exact-limit/limit+1 PASS, 14 archivos, manifiesto 13/13, symlinks 0,
modos exactos, tar productor 0, limiter 0, receptor 0, filtro 0, verificador read-only 0; red
none, rootfs read-only, 128 MiB/0.5 CPU/pids64, sin OOM. Contenedor exacto exit 0 y volumen
`h3req1-c03-startup-source-20261010-s12` se preservan. G05 vuelve a completo con manifiesto V4
actual. G06 sigue NO-GO hasta que el arranque Pages/workerd completo acredite `healthz`.

## Preparación G06 S9 sobre S12

Actualización posterior al S9: la ejecución final acreditó `healthz=PASS` y completó G06; ver
[resultado S9](h3req1_c03_startup_smoke_2026-10-10_s9.md). Dos preflights previos detectaron
filas V3 en S3/S4 y un dispatch posterior salió exit 127 antes de Docker porque los helpers
estaban definidos después de invocarse. La evidencia y corrección focalizada están en
[S9 preflight](h3req1_c03_startup_smoke_2026-10-10_s9_preflight1.md) y
[S9 dispatch](h3req1_c03_startup_smoke_2026-10-10_s9_dispatch_failure.md). Las funciones se
movieron antes de la llamada pre-Docker, el sidecar se repineó, Bash/ShellCheck/manifiestos
pasaron y la revisión independiente quedó sin blockers.

Pins finales S9: runner `9e8019f686b50835cf3c14f6d29cbdf8c45db305eb3c95fe5365103f2da2d19f`,
sidecar `d9e51fd2487edcff096ee630de2ed9d1f30b7de323a79cbfae9d60516c3d3bf4`; resultado SHA-256
`5703e866bd09b0ef654478bf23a2e3842921ec008069c9552d56712ad1ee4bc3`. G01–G06 completos;
G07 Edge/PG17/PostgREST/C03 integrado pendiente. Métricas: G01–G10 60%, G01–G09 6/9 = 66.67%.

El runner S9 se adaptó desde S8 para conservar los prechecks de ownership S3–S7, fijar el
manifiesto fuente V4 y usar como candidato el volumen persistente S12 montado read-only. Antes
del runtime verifica pines/evidencia S12, ID exacto, labels de contenedor/volumen y run nonce;
reconstruye el mapa de modos y prueba el contenido del volumen con un verificador Docker
`network=none`, rootfs read-only y montaje read-only. Solo después corre las pruebas sintéticas
del filtro/diagnóstico y Pages/workerd con las dependencias S3 read-only en la red interna
verificada, sin Edge, DB, PostgREST, SQL, secretos ni egress.

Pins actuales: runner SHA-256
`a3767e62dcf35a1cf4d8bc72fc52141a3d116172b9fb5ba9c43474766be18739`; manifest SHA-256
`7faee4ce38d14baf8929b87bdd143d20302ae5745a1d25b17f00eef22669cfa8`. El manifiesto fija
source manifests V3/V4 y helpers S8 además del runner. V3/V4 contienen 13 rutas iguales; el único
delta es `tests/h3req1_c03_integrated_runtime.mjs`, y los cuatro manifests/lockfiles de paquetes
coinciden. El preflight valida que la fila S3 antigua corresponde a V3, todas las otras entradas
del manifiesto S3 verifican contra las fuentes actuales y ningún hash no-runtime cambió.
`bash -n`, `git diff --check`, sidecar `sha256sum -c`, source manifest V4, mapa de permisos,
verificador read-only del volumen S12 y ShellCheck oficial 0.11.0 con 512 MiB terminaron PASS.
La primera ejecución S9 terminó `preflight`, exit 1, porque intentó verificar el runtime V3
histórico como fuente actual; no consultó Docker ni creó recursos. El hallazgo y corrección están
en [S9 preflight 1](h3req1_c03_startup_smoke_2026-10-10_s9_preflight1.md). Revisión independiente
del runner/sidecar corregidos: sin blockers. La siguiente ejecución debe acreditar el arranque
real y healthz; G06 sigue pendiente.
