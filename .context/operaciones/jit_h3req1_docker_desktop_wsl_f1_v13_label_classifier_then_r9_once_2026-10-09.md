# JIT V13 — clasificador de labels H3 sintéticos + F1/r9 condicional

Fecha: 2026-10-09. Estado: paquete preparado; requiere aprobación humana nueva. La autorización V12 está consumida.

## Objetivo y límite

Resolver únicamente el preflight demostrado en V12. El mapa `Config.Labels` de la imagen sintética fijada no está vacío. V13 analiza su JSON en memoria y comprueba si contiene alguna de las tres claves snapshot H3 fijadas por V7. Permite claves ajenas, no emite ni persiste claves/valores/metadata y falla cerrado ante JSON inválido o una clave objetivo presente. Esto no demuestra nada sobre el estado de Docker ni sobre F1.

La invocación agrupada propuesta permite una lectura read-only del mapa sintético, hasta dos contenedores sintéticos temporales, una lectura de imagen F1 allowlisted y una lectura de contenedor F1 allowlisted. r9 se ejecuta una vez únicamente si todos los predicados previos pasan. Cualquier error, salida inesperada o timeout detiene la secuencia y consume la autorización.

## Candidato, impacto y gates

| Campo | Valor |
|---|---|
| Checkout | `/home/romel/src/studiamatch-h3req1-sync-20261002` |
| Rama / HEAD | `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c` |
| WIP al preparar | 54 tracked modificados, 220 rutas untracked, 0 staged; checkout original separado preservado |
| Archivos nuevos del runner | `tests/h3req1_docker_peer_substep_diag/f1_template_label_classifier_v13_once.py`; `tests/h3req1_docker_peer_substep_diag/run_wsl_f1_v13_label_classifier_then_r9_once.sh` |
| Impacto funcional | Ninguno: diagnóstico y validación local; no cambia producto, contrato, DB, Docker ni estado remoto |
| G03/G04 | 0/10. F1 y r9 permanecen no alcanzados en V12 |
| Porcentaje | 20%: G01/G02=10/10; G03–G10=0/10; D01–D14=0/14 |

## Evidencia previa y alcance de V13

El resultado V12 fijado es `.context/evidencia/h3req1_c03_v12_synthetic_image_label_map_failure_2026-10-09.md`, SHA-256 `790dba22c034a79a4620a8303b3de23ddffc6c9b88b19adf8d79efb79f992c46`. Emitió endpoint, evidencia V10/V11 en `OK` y luego `f1-template-synthetic-label-map/SYNTHETIC_IMAGE_LABELS_PRESENT`, exit 1. Se detuvo antes de crear contenedores, F1 y r9. No se repite ese diagnóstico exacto.

Antes de cualquier llamada Docker, V13 ejecuta siete fixtures cerrados: JSON `null`, objeto vacío, objeto con label ajeno, cada una de las tres claves snapshot objetivo por separado y JSON malformado. El resultado local del clasificador puro fue 7/7 PASS, sin Docker. Durante la invocación aprobada, estos fixtures vuelven a ejecutarse antes de cualquier acceso al daemon para proteger los bytes fijados del runner.

Tras los fixtures, V13 reutiliza el diagnóstico V12 fijado, sustituyendo únicamente el predicado que exige mapa completo vacío. El nuevo predicado inspecciona el objeto una sola vez y cachea únicamente el resultado `OK` durante las dos variantes. El output de Docker se mantiene en memoria y no se escribe en logs. Solo se permiten códigos cerrados `SYNTHETIC_IMAGE_TARGET_LABEL_PRESENT` y `SYNTHETIC_IMAGE_LABELS_INVALID` para la clasificación nueva.

## Secuencia stop-on-failure

1. El wrapper comprueba usuario no-root, TTY, rama/HEAD, ausencia de overrides Docker, hashes de runners/evidencia, manifiestos r9 y 68 inputs del candidato sin drift.
2. El runner verifica V12 consumido y las fuentes V7/V12 fijadas, y ejecuta los siete fixtures puros. No toca Docker si falla un pin o fixture.
3. El runner acredita evidencia endpoint/V10/V11 ya fijada; lee el mapa JSON de labels de la imagen sintética local. Permite labels ajenos, exige ausencia de las tres claves snapshot H3, y no guarda metadata.
4. Como máximo crea las dos variantes V12 desde la imagen local fijada con `--pull=never`, sin red, read-only, UID no-root, límites de recursos y nombre/marcador aleatorios. El mapa sintético se inspecciona una vez. Cleanup verifica propiedad antes de detener; fallo de cleanup impide continuar.
5. Solo si smoke y controles previos pasan, lee una vez imagen F1 y una vez la proyección del contenedor F1. El ID objetivo conocido se compara por hash para impedir alcanzar `studiamatch-dev`.
6. Solo si F1 pasa, ejecuta r9 una vez dentro del contenedor efímero offline: copia aislada, manifiestos, dependencias, Node/TypeScript, actionlint, ShellCheck, ESLint, typecheck, tests PWI, scanner de credenciales y scope guard. Se requiere coincidencia exacta de los 68 inputs fijados.

No se repite F2d, V10, V11 ni V12; no se consulta `/proc` del motor, ni se requiere sudo. Sin retry, pull, build, install, limpieza de recursos preexistentes, cambios de configuración o imagen Docker, DB/SQL/Supabase, Auth/correo, Git remoto/GitHub/Cloudflare, push/PR/merge, ramas protegidas o deploy. No lee secretos ni `.env*`. No toca ni inspecciona `studiamatch-dev` salvo comparar localmente su ID conocido mediante hash; si coincide, detiene antes de leer F1.

La salida permitida son líneas `phase=…|error_code=…` del allowlist exacto y, ante fallo, `exit=<decimal>`. La terminal debe ser interactiva y permanecer abierta hasta copiar la salida sanitizada.

El wrapper exige la secuencia diagnóstica exacta siguiente antes de entrar a r9:

```text
phase=prior-v12-failure|error_code=OK
phase=classifier-v13-null|error_code=OK
phase=classifier-v13-empty-object|error_code=OK
phase=classifier-v13-unrelated-label|error_code=OK
phase=classifier-v13-target-label-1|error_code=OK
phase=classifier-v13-target-label-2|error_code=OK
phase=classifier-v13-target-label-3|error_code=OK
phase=classifier-v13-malformed-json|error_code=OK
phase=prior-v11-failure|error_code=OK
phase=prior-v10-evidence|error_code=OK
phase=prior-endpoint-attestation|error_code=OK
phase=f1-template-synthetic-label-map|error_code=OK
phase=f1-template-present-inspect|error_code=OK
phase=f1-template-absent-inspect|error_code=OK
phase=f1-template-synthetic-check|error_code=OK
phase=f1-image-read|error_code=OK
phase=f1-container-read|error_code=OK
```

Después r9 debe emitir su secuencia completa de checks `OK` y `phase=r9-summary|error_code=ALL_CHECKS_OK`. Un output distinto consume la invocación y detiene.

## Pines

| Recurso | SHA-256 |
|---|---|
| Clasificador V13 | `e2cb61472552dab4165014347f63232a3f8d1d888efa7b75aea918a02c71d073` |
| Wrapper V13 | `59781a6607da28918536e57698e683051967e3407ec30e09a148692675d9ddb7` |
| Evidencia V12 consumida | `790dba22c034a79a4620a8303b3de23ddffc6c9b88b19adf8d79efb79f992c46` |
| JIT V12 consumido | `b06bd50b6bea6c63d0fcec63ffef6fc47527f506e13ca840777bfa652bce16cf` |
| Diagnóstico V12 base | `6ab7887690fc81a2fa5f97f047fc4a3973a4add8cb649751fdcd241c4db31e66` |
| Fixture V7 | `5b5341f7775b38350197976fe3d0246702e1158ae1578a2957717f97b5f9d0c1` |
| Runner r9 | `bdef0351abfa8697cb13c788b5b3cdbb7a5568672e4c8c9d56b860826364f0a7` |
| Runner r9 in-container | `d384964d84b86b9a0c006bb819a8795950345513396860efc1168b094061fadc` |
| Paquete r9 | `688e81efaae70a841a64cd4c0a074ae3c76c355f5ef9bc77756cff9ad607fc02` |
| Inputs r9 | `6b3f3d856f906cb247b792a8d89d29f4abc0422c990fa473222b9dbe89097aee` |
| Herramientas r9 | `4c1b3551ac9f09c56f38b441ea33b560e72419c40a942c0103fea689cb094daa` |

## Solicitud de autorización concreta

La solicitud al usuario fija el SHA-256 de este JIT antes de la ejecución. ¿Apruebas una sola invocación de `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-V13-LABEL-CLASSIFIER-AND-R9-ONCE-20261009-V1` con ese digest? Ejecutaré el bloque único en Ubuntu WSL interactiva como `romel` no-root, con `sandbox_permissions=require_escalated` y sin sudo. El alcance es exactamente la secuencia anterior. Cualquier FAIL o timeout consume la invocación y detiene las etapas posteriores; no se reintenta ni se cambian imágenes, Docker o configuración.

```bash
(
set -u -o pipefail
readonly RUNNER='/home/romel/src/studiamatch-h3req1-sync-20261002/tests/h3req1_docker_peer_substep_diag/run_wsl_f1_v13_label_classifier_then_r9_once.sh'
readonly RUNNER_SHA256='59781a6607da28918536e57698e683051967e3407ec30e09a148692675d9ddb7'
if (( EUID == 0 )); then
  printf 'phase=jit-preflight|error_code=RUN_AS_WSL_USER\n'
  exit 1
fi
if [[ ! -t 0 ]]; then
  printf 'phase=jit-preflight|error_code=INTERACTIVE_TTY_REQUIRED\n'
  exit 1
fi
if [[ ! -x /usr/bin/sha256sum || ! -x /usr/bin/timeout ]]; then
  printf 'phase=jit-preflight|error_code=RUNTIME_UNAVAILABLE\n'
  exit 1
fi
hash_line="$(/usr/bin/sha256sum -- "$RUNNER" 2>/dev/null)" || {
  printf 'phase=jit-preflight|error_code=RUNNER_HASH_FAILED\n'
  exit 1
}
if [[ "${hash_line%% *}" != "$RUNNER_SHA256" ]]; then
  printf 'phase=jit-preflight|error_code=RUNNER_HASH_MISMATCH\n'
  exit 1
fi
/usr/bin/timeout --foreground --signal=TERM --kill-after=5s 900s /bin/bash "$RUNNER" 2>/dev/null
)
```

La autorización solo cubre este comando y esta secuencia. Una salida incompleta o distinta del PASS exacto detiene la etapa y no autoriza retry. Sin autorización, no se ejecuta Docker, F1 ni r9.
