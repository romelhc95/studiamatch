# JIT — repetir lectura Docker Desktop WSL con captura visible

ID: `H3REQ1-C03-DOCKER-DESKTOP-WSL-OUTPUT-CAPTURE-ONCE-20261008-V1`  
Estado: **preparado; requiere aprobación nueva; no ejecutado**.  
Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Motivo y alcance solicitado

El usuario ejecutó la invocación aprobada en
`H3REQ1-C03-DOCKER-DESKTOP-WSL-ENDPOINT-F1-ONCE-20261008-V1` y confirmó que la ventana
cerró sin que pudiera ver o recuperar las líneas de resultado. El runner consumido usa
`exec`, por lo que reemplaza la shell desde la que se pegó el bloque; el resultado solo iba
a stdout y no dejó archivo local. No se puede inferir si alcanzó endpoint/Linux o F1.

La invocación anterior queda consumida. Esta solicitud es una autorización nueva para una
sola repetición **read-only**, ahora capturando stdout en la shell interactiva y esperando a
que el usuario copie las líneas antes de cerrar la pausa. El comando no invoca `exec` en la
shell interactiva y no guarda salida en disco. La captura valida cada línea contra el formato
sanitizado antes de mostrarla.

La repetición volvería a consultar el contexto `default`, el SO del Engine, la imagen fijada y,
si las fases previas pasan, el mismo ID F1 allowlisted. Como el resultado anterior se perdió,
no se sabe si F1 ya se leyó. La duplicación posible es una lectura Docker API allowlisted, sin
mutación. Si las tres líneas F1 pasan, la aprobación solicitada también permite continuar r9
y las etapas locales dentro de la autorización consolidada existente, con sus mismos límites
y criterio de parada.

Se mantiene el residual **MEDIUM** ya aceptado para esta vía: confirma endpoint WSL local,
respuesta Linux del Engine y disposición del F1 exacto, no PID/UID/ejecutable/namespace del
daemon. Owner del residual: Romel. No demuestra que Docker esté mal ni habilita cambiarlo.

## Solicitud de autorización agrupada

Se solicita aprobar una vez el ID y SHA de este documento para:

1. ejecutar el comando único de abajo en Ubuntu WSL como `romel`, no root;
2. mostrar únicamente líneas `phase=…|error_code=…` y mantener abierta la shell hasta que el
   usuario confirme que copió la salida;
3. si y solo si aparecen las tres líneas `error_code=OK` enumeradas, continuar r9 y el cierre
   local iterativo dentro del alcance ya aprobado.

No hay retry. Un error, timeout, salida vacía o línea inválida consume esta autorización y
detiene G04/r9. No autoriza pull/rebuild, instalación, cambio de contexto, configuración,
limpieza, creación/arranque/parada/eliminación de recursos, writes remotos, PR, merge ni deploy.
No se pide permiso separado por runner, helper, F1 o hash.

## Ejecutor y comando único

Ejecutor: el usuario `romel`, en una **terminal interactiva Ubuntu WSL** del host Windows con
Docker Desktop WSL integration y el checkout indicado. No usar PowerShell, `studiamatch-dev`,
otro contenedor ni la distro interna `docker-desktop`. No usar `sudo`.

Pegar el bloque completo exactamente una vez:

```bash
(
set -u -o pipefail
readonly RUNNER='/home/romel/src/studiamatch-h3req1-sync-20261002/tests/h3req1_docker_peer_substep_diag/run_wsl_desktop_attestation_once.sh'
readonly RUNNER_SHA256='39cebc3e0dbf1e290c11ff6fce0f7a98586209bd94a8af2acf0e6d43cad88f87'
readonly SAFE_LINE_RE='^phase=[a-z][a-z0-9-]{0,47}\|error_code=[A-Z][A-Z0-9_]{0,47}$'
readonly EXPECTED_OK=$'phase=desktop-wsl-endpoint-attested|error_code=OK\nphase=f1-image-read|error_code=OK\nphase=f1-container-read|error_code=OK'

if (( EUID == 0 )); then
  printf 'phase=capture-preflight|error_code=RUN_AS_WSL_USER\n'
  exit 1
fi
if [[ ! -t 0 ]]; then
  printf 'phase=capture-preflight|error_code=INTERACTIVE_TTY_REQUIRED\n'
  exit 1
fi
if [[ ! -x /usr/bin/sha256sum || ! -x /usr/bin/timeout ]]; then
  printf 'phase=capture-preflight|error_code=RUNTIME_UNAVAILABLE\n'
  exit 1
fi
if ! hash_line="$(/usr/bin/sha256sum -- "$RUNNER" 2>/dev/null)"; then
  printf 'phase=capture-preflight|error_code=RUNNER_HASH_FAILED\n'
  exit 1
fi
if [[ "${hash_line%% *}" != "$RUNNER_SHA256" ]]; then
  printf 'phase=capture-preflight|error_code=RUNNER_HASH_MISMATCH\n'
  exit 1
fi

runner_output="$(/usr/bin/timeout --foreground --signal=TERM --kill-after=1s 55s \
  /bin/bash "$RUNNER" 2>/dev/null)"
runner_status=$?

safe_output=''
invalid_output=0
while IFS= read -r line; do
  [[ -n "$line" ]] || continue
  if [[ "$line" =~ $SAFE_LINE_RE ]]; then
    safe_output+="${line}"$'\n'
  else
    invalid_output=1
    break
  fi
done <<< "$runner_output"

if (( invalid_output )); then
  printf 'phase=output-capture|error_code=OUTPUT_REJECTED\n'
elif [[ -z "$safe_output" ]]; then
  printf 'phase=output-capture|error_code=NO_SANITIZED_OUTPUT\n'
elif (( runner_status == 0 )) && [[ "$runner_output" == "$EXPECTED_OK" ]]; then
  printf '%s' "$safe_output"
elif (( runner_status == 0 )) || [[ "$runner_output" == "$EXPECTED_OK" ]]; then
  printf '%s' "$safe_output"
  printf 'phase=output-capture|error_code=INCOMPLETE_RESULT\n'
else
  printf '%s' "$safe_output"
fi

IFS= read -r -p 'Copia solo las lineas phase/error_code; presiona Enter cuando las tengas: ' _ || true
)
```

La shell debe quedarse en la pausa final. Copiar y compartir solo las líneas `phase=…|error_code=…`;
después presionar Enter. No compartir el prompt, salida cruda, datos de sesión ni capturas.
Si la shell no permanece abierta o la salida no aparece, detenerse; no ejecutar de nuevo.

## Lecturas y límites

El runner fijado verifica checkout/branch/HEAD, hashes del helper y proyector, WSL, usuario,
contexto `default` y endpoint `unix:///var/run/docker.sock`. Consulta únicamente el SO del
Engine; si es `linux`, lee volúmenes de la imagen fijada
`node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844`; solo si esa
fase pasa, consulta la proyección F1 allowlisted del ID
`54d0ad11fb6a7e0b91ffa59538958407e36cee79fc875d8446ac7b1e1bf67dd9`.

No ejecuta `docker info`, logs, `ps`, `/proc`, `SO_PEERCRED`, metadata no allowlisted,
pull/build, create/run/start/exec/wait/stop/rm, redes/volúmenes, limpieza ni cambios de Docker.
El timeout total externo es 55 s y cada comando interno conserva sus límites existentes.
Los runners y helpers anteriores no se editan.

## Revisión y estado

Preparación documental y revisión estática del wrapper; no se ejecutaron pruebas, runner,
Docker ni F1 durante esta preparación. El wrapper captura solo stdout del runner cuyo SHA
está fijado, valida el formato de cada línea, no persiste datos y pausa en una terminal TTY.
La revisión no acredita runtime. Los pins del runner/helper siguen siendo los del JIT V1
consumido.

G04 permanece 0/10 y el total 20% hasta recibir salida runtime válida, disposición F1 y
completar los gates locales correspondientes. Sin aprobación de este nuevo JIT no se repite
la lectura ni se inicia r9.
