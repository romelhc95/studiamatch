# JIT — H3REQ1 G03 r9 ShellCheck continuation V5

Identificador: `H3REQ1-G03-R9-SHELLCHECK-CONTINUATION-V5-ONCE-20261009-V1`  
Estado: **requiere aprobación humana nueva; una invocación**.  
Ejecutor: `romel`, usuario no-root, en una terminal interactiva de Ubuntu WSL conectada a Docker Desktop.  
Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`.  
Rama/HEAD: `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c`.  
WIP fijado después de crear este JIT y actualizar los runners: `55/279/0`.

## Propósito y antecedente

El r9 V4 fue aprobado y consumido. Sus preflight, copia aislada, sintéticos y `actionlint`
pasaron; ShellCheck detuvo la secuencia antes de ESLint, TypeScript y las suites. La única
clasificación recuperable fue `scripts/security/scan_credentials.sh:195`, regla `SC2209`.
Se cambió únicamente la asignación del literal a `mode="diff"`; la sintaxis Bash y el
`git diff --check` pasan. Este JIT valida la fuente candidata actual empaquetada en r6.

La comparación de paquete mostró que r5 contenía un snapshot anterior de
`scripts/security/scan_credentials.sh`: r6 refresca ese único archivo fuente y sus manifiestos.
El archivo actual incluye cambios de WIP ya presentes en el candidato además del quote fix; no
se atribuyen al arreglo de `SC2209`. El resultado V2 acredita el defecto en la línea común, y
r6 fija los 68 inputs actuales para que la nueva pasada valide el candidato completo.

No se vuelve a ejecutar `actionlint`: el JIT V4 ya produjo PASS y el runner nuevo comprueba que
los tres workflows mantienen los mismos hashes. Si alguno difiere, se detiene. El resto de r9
que V4 no alcanzó se ejecuta en orden y con stop-on-failure.

## Artefactos fijados

| Elemento | SHA-256 / identidad |
|---|---|
| Este JIT | Se entrega para aprobación con su SHA-256 calculado después de guardar el archivo |
| Runner host `run-r9-shellcheck-continuation-v5.sh` | `1aa13c054482eecfb78f586913a0a9d60e437606c1a432c72400c86d040da862` |
| Runner de contenedor `run-r9-shellcheck-continuation-inner-v3.sh` | `b4835a286ef036ca733efe6a49be9cc37b19d16bb5ddbfb4a6ea90065461ab71` |
| Clasificador ShellCheck json1 V2 reutilizado | `07a8401aa6a89275362e2456655ad79ec00ff6d3629da5059e851a2520cc38a4` |
| Paquete candidato aislado r6, `r4-package.sha256` | `d10cc19b87adfff36f8092c97b59dc8fb4a247166c0dcbf8f0653dd9f2db6186` |
| Paquete candidato aislado r6, `inputs.sha256` | `c53e3321190646a2449e28b935711fc6f7b8425d1b19289f2374f4488eaff4c8` |
| Herramientas locales, `tools.sha256` | `4c1b3551ac9f09c56f38b441ea33b560e72419c40a942c0103fea689cb094daa` |
| Imagen local | `studiamatch-h3req1:20261009-v3`, `sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63` |
| `studiamatch-dev` fijado | `500931b0f086d29ec9e751e1fd652f9b7ccd357f3eb64daa8751344776162049` |
| Volumen node_modules | `studiamatch_h3req1_node_modules`, solo lectura |
| `web/package.json` / lock | `4567e008756097437c0ef586f1c112c97db3a198bcd521bd62e8342242f7cd8a` / `8bd9c50605a8ce92e87b0ad81e4513fd47fc01ca328079eef792d264c2a292bc` |
| `web/tsconfig.json` / `next-env.d.ts` / `next.config.js` | `661b4cc82da6a8924e8e57c1ccf9ac2e8c3c4d1422d4ce664a45e44ddc4cdc9a` / `0f70629890b72a0a82e91972cc032c04b658b26c265373cb711cf576bfbf8fcc` / `97308c3b1736f0da28fa59f220487a91725a11daaafeb37a7093621130991cd3` |

Los tres workflows reutilizados deben conservar estos hashes exactos:

- `security-audit.yml`: `276641005c0bc1dc64b26e479b9ef197137a69b3dc4b08be8e56246fdb75df23`
- `protected-workflow-integrity.yml`: `016551e6a6e280dcd515788ffcf93b18a6d48647079e3c0cd7be9c2d4f58864b`
- `db-sync-to-pro.yml`: `3899f29a026861400707827e7e6c9248446d938451232eb5fee157775b39fda8`

El paquete r6 es una copia aislada de los inputs actuales allowlisted, no una modificación del
checkout. Sus manifiestos se comprueban dentro del contenedor. La fuente del candidato también
se compara contra las 71 filas del manifiesto antes de crear el contenedor temporal.

## Alcance exacto

Una ejecución del runner fijado, timeout 180 segundos:

1. Verifica usuario/TTY/WSL, rama, HEAD, conteo WIP, manifests, 68 fuentes actuales, imagen
   local, estado/ID del contenedor y existencia del volumen. Comprueba además los cinco hashes
   web fijados arriba. No lee variables `Env`, `.env*` ni credenciales. `studiamatch-dev` se
   inspecciona solo para comprobar identidad y health.
2. Inicia un único contenedor temporal `--rm --pull=never --network=none`, no-root,
   `--read-only`, sin capacidades, con recursos limitados y mounts de paquete, herramientas,
   helper y volumen de dependencias solo lectura. `/tmp` es noexec; `/exec-fixture` es un
   tmpfs exec acotado exigido por `test_scan_credentials.sh`. El candidato se copia a `/tmp`
   efímero.
3. Comprueba que los tres hashes de workflow siguen iguales al actionlint V4 ya aprobado.
4. Ejecuta ShellCheck una vez sobre los mismos siete scripts del alcance r9 V4. Reutiliza el
   clasificador json1 V2 exacto y aprobado para mostrar solo ruta allowlisted, línea, columna y
   `SC####` si falla; se descartan los mensajes. Sus 34 sintéticos dieron PASS en V2 y el hash
   fijado coincide, por lo que no se repiten. Si ShellCheck pasa, ejecuta en orden ESLint,
   vuelve a verificar el marcador de dependencias contra package/lock, versiones Node
   `v20.20.2` y TypeScript `5.9.3`, regenera `next typegen` en el scratch nuevo, luego ejecuta
   `tsc --noEmit`, `tests/test_protected_workflow_review.py`, `tests/test_scan_credentials.sh` y
   `tests/test_protected_path_scope_guard.sh`. El typegen se repite porque el contenedor temporal
   anterior ya fue retirado y sus archivos `.next` no persisten.
5. Ante cualquier mismatch, fallo o timeout, detiene las etapas posteriores. No hay retry.

La salida queda limitada a fases/códigos y, ante ShellCheck FAIL, ruta allowlisted, línea,
columna y regla. Si actionlint tuviera que invalidarse por cambio de hash, no se intenta
reemplazar su resultado en esta invocación: se detiene antes de las suites. No se imprime
stdout/stderr crudo de linters, tests, Docker ni entorno.

El proceso dentro del contenedor empieza con un entorno limpio `env -i`; solo recibe PATH,
HOME temporal, flags de salida y la ruta de fixture `/exec-fixture`. Así no hereda valores Env
de la imagen para typegen/lint.

## Límites y recuperación

Sin pull, build, instalación, egress, acceso a F1, `studiamatch-dev` exec, lectura de secretos,
volúmenes en escritura, limpieza de recursos persistentes, SQL/DB, publicación, push, PR,
merge, despliegue o configuración remota. El único contenedor creado es efímero y lleva
`--rm`; no se ejecutan acciones de cleanup sobre otros recursos. Un FAIL deja intactos el
checkout, los manifiestos, el volumen, la imagen y los contenedores persistentes. Si un timeout
no confirma la retirada automática del temporal, no se inspecciona ni elimina sin autorización
separada.

Este JIT no acredita F1, copia íntegra, Pages/workerd, integración Edge/PG17/PostgREST, C03,
aceptación, UAT, onboarding, CI remoto ni GO. Esas etapas requieren sus predicados y permisos
propios.

## Comando único

Ejecuta este bloque completo una vez, en Ubuntu WSL interactiva como `romel`, sin `sudo`:

```bash
set -Eeuo pipefail
readonly ROOT='/home/romel/src/studiamatch-h3req1-sync-20261002'
readonly RUNNER="$ROOT/tests/h3req1_docker_peer_substep_diag/run-r9-shellcheck-continuation-v5.sh"
readonly RUNNER_SHA256='1aa13c054482eecfb78f586913a0a9d60e437606c1a432c72400c86d040da862'
if (( EUID == 0 )); then
  printf 'phase=dispatch-preflight|error_code=RUN_AS_WSL_USER\n'
  exit 1
fi
if [[ ! -t 0 ]]; then
  printf 'phase=dispatch-preflight|error_code=INTERACTIVE_TTY_REQUIRED\n'
  exit 1
fi
if [[ "$(uname -s 2>/dev/null)" != Linux || "$(uname -r 2>/dev/null | tr '[:upper:]' '[:lower:]')" != *microsoft* ]]; then
  printf 'phase=dispatch-preflight|error_code=WSL_REQUIRED\n'
  exit 1
fi
runner_line="$(/usr/bin/sha256sum -- "$RUNNER" 2>/dev/null)" || {
  printf 'phase=dispatch-preflight|error_code=RUNNER_HASH_FAILED\n'
  exit 1
}
if [[ "${runner_line%% *}" != "$RUNNER_SHA256" ]]; then
  printf 'phase=dispatch-preflight|error_code=RUNNER_HASH_MISMATCH\n'
  exit 1
fi
exec /usr/bin/timeout --foreground --signal=INT --kill-after=5s 180s /bin/bash "$RUNNER"
```

Tras la ejecución, comparte únicamente las líneas `phase=...|error_code=...`, `exit=...` y,
si aparece, la línea `diagnostic=...` allowlisted. No compartas salida cruda ni vuelvas a
ejecutar el bloque.
