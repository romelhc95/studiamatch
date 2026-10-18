# G08 R176 — cobertura de variables secretas y allowlist del scanner — 2026-10-11

## Alcance y revisiones

Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD baseline
`4eb4d877a50b012bb630a129bd0c74482c33be9c`; se preservan el checkout original,
WIP y recursos ajenos. R176 continúa el cierre G08/G09 local; no ejecuta CI,
push, PR, merge ni servicios remotos.

La revisión independiente del alcance encontró dos problemas distintos:

1. El scanner reconocía formatos prefijados, pero aceptaba valores sintéticos
   opacos asignados a nombres de secretos usados por el repositorio
   (`CF_API_TOKEN`, `SUPABASE_ACCESS_TOKEN`, `RESEND_API_KEY` y
   `NEXT_SUPABASE_SECRET_KEY`). Esto es una brecha de cobertura del control, no
   evidencia de un secreto expuesto.
2. El workflow `security-audit` no incluía el nuevo helper
   `scripts/security/scan_worktree_file.py` ni `.githooks/pre-push` en las dos
   capas de allowlist. El job protegido los clasificaría como
   `scoped_disallowed` al integrarse.

La revisión de seguridad también recomendó cubrir el caso de symlink final;
se añadieron pruebas de lectura solo del texto del enlace y de no seguimiento
del destino externo. R175 contiene la evidencia del rechazo seguro de padres
symlink con `O_NOFOLLOW`.

## Reproducción y cambios

- Se añadió primero una prueba con valores opacos creados en tiempo de
  ejecución. Antes de ampliar los patrones, la suite terminó exit 1 con
  `scanner regression failed: opaque named credential assignments were not rejected`.
- Se ampliaron los patrones para asignaciones a los nombres variables
  identificados, conservando el umbral y la redacción. La prueba contiene
  cuatro variantes (`=`, `:`, comillas simples y dobles); el valor no aparece
  en stdout ni stderr.
- Un test sintético de `security-audit` falló antes de editar la allowlist al
  verificar que ambas rutas coincidieran con `allowed_h3_extra` y aparecieran
  exactamente en `allowed_h3_local`. Se añadieron las dos rutas en ambas capas.
- La primera reejecución focal de contratos encontró que el inventario de
  consumidores Supabase clasificaba el scanner como consumidor por contener
  nombres de variables. Se excluyó el catálogo de patrones de la inferencia de
  consumidores y se añadió una aserción de que ese archivo no contiene rutas
  Data API/Management API (`api.supabase.com`, `/rest/v1`, `apikey`). No se
  cambió el inventario de clientes de producto.

## Validación ejecutada

| Check | Entorno / inputs | Resultado |
|---|---|---|
| Scanner focal | `studiamatch-dev`, suite `tests/test_scan_credentials.sh` y helper en `/app`; cadena sintética | **PASS**, exit 0: `named-credentials=4`, `tree=6`, `history=5`, errores I/O 4, concurrencia 2 y redacción PASS. Incluye padres symlink externos rechazados, symlink final escaneado como texto y target externo no leído. |
| Contratos G03 afectados | `studiamatch-dev`, `tests/test_security_flow.py`, `tests/test_supabase_credentials_contract.py`, `tests/test_protected_workflow_review.py` | **PASS**, 71 passed, exit 0. Incluye allowlist de las dos rutas y exclusión explícita del scanner del inventario de consumidores. |
| Python/shell syntax | `studiamatch-dev`, `python3 -m py_compile` de helper/tests y `bash -n` de scanner/suite | **PASS**, exit 0. |
| ShellCheck | imagen fijada local `koalaman/shellcheck:v0.11.0`, `--pull=never --network none --read-only`, tres archivos read-only | **PASS**, exit 0. |
| Actionlint | asset oficial actionlint 1.7.7 existente, digest comprobado con `sha256sum -c tools.sha256`; contenedor `studiamatch-h3req1:20261009-v3`, solo lectura, sin red; tres workflows fijados | **PASS**, exit 0 para `security-audit.yml`, `protected-workflow-integrity.yml` y `db-sync-to-pro.yml`. La primera llamada usó la bandera inexistente `-color=never` (exit 2, sin análisis); la invocación corregida usa `-no-color` y pasó. No se descargó ni instaló software. |
| Escaneo índice tracked | 679 paths `git ls-files -z` del candidato, contenido revisado en `studiamatch-dev` | **PASS**, exit 0. |
| Scope/evidencia propuesta | Scope R4 de 88 paths, 138 evidencias, helper y notas R175/R176 | **PASS** al recuento de este corte: 229 paths únicos, exit 0. El set final R5 se recalcula aparte e incorpora el informe de cierre; no se reutilizan esos digests. |

## Seguimiento de revisión — lock de dependencias del workflow

La revisión marcó como LOW que `python-check` instalaba cinco paquetes Python
sin fijar. Se añadió primero una aserción de contrato que falló con el comando
anterior; después, `.github/workflows/security-audit.yml` pasó a instalar
`requirements-pipeline.txt` con `--require-hashes`, lock existente que fija
versiones y hashes. La aserción junto con los contratos afectados terminó en
Docker con **72 passed**. Actionlint 1.7.7 pasa sobre los tres workflows.
Esta modificación prepara reproducibilidad local; no ejecuta el workflow ni
crea enforcement remoto.

## Límites y estado

Los runners UAT, fuentes web, SQL, manifests de dependencias y runtime no
cambiaron en este delta; sus resultados se conservan por input compatible.
Los scans y pruebas usaron Docker local, sin montar `.env*`, sin leer secretos,
cuentas reales ni datos operativos, y sin egress durante actionlint/ShellCheck.
El scan completo `--tree` en `/app` sigue limitado por el `.git` del
contenedor; los seis casos de `--tree` se ejecutan en repositorios sintéticos,
y las 679 rutas tracked/candidate scope se recorren por lista explícita.

R176 cierra las brechas locales identificadas en el scanner y deja la ruta
allowlisted para una futura promoción; no acredita enforcement remoto. G08 se
mantiene completo en la métrica de gates; G09/LOCAL-23 sigue pendiente hasta
actualizar R5 y recibir revisión independiente del scope/manifiesto/cuerpo
actuales. G10 remoto permanece pendiente. Las métricas no cambian en R176.
