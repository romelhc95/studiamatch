# Diagnóstico de fallo de extracción del startup S2 — 2026-10-10

## Resultado del ensayo

- Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
  `feat/h3req1-sync-20261002`, HEAD baseline
  `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- Runner S2 SHA-256 `67f108ee253e8c7540f5f6bd3fc8533576b1ceaf264fe8f5c1a70525b8e3daae`;
  manifiesto SHA-256 `18cda74992361c971d355159c6454477111d86216af30e11089e3ced3575dc62`.
- Fase: `create-new-source-snapshot`; receptor Docker exit 2; runner exit 1.
- El contenedor de snapshot fallido y todos los recursos S2 se conservaron. No se alcanzaron
  npm ci, la red interna, Pages/workerd ni `healthz`.

## Causa demostrada

El productor empaqueta los archivos con propietarios numéricos. El receptor ejecuta como root
con `cap-drop=ALL` y usaba `tar -xf - -C /snapshot`, que intenta restablecer UID/GID y falla
cuando no está permitida esa operación. La reproducción mínima de un único archivo, en la imagen
Node fijada y con el mismo aislamiento/capabilities, terminó exit 2 (`OWNER_RESTORE_DENIED`). El
mismo fixture terminó exit 0 usando `tar --no-same-owner -xf - -C /snapshot`.

El contenido del snapshot S2 sí quedó extraído: inspección estructurada y read-only encontró
14 archivos, cero symlinks, rutas exactas y todos los hashes del source manifest vigentes. Esto
no convierte el productor/receptor S2 en PASS: el proceso de extracción reportó exit 2 y el gate
se detuvo antes de verificar runtime.

## Corrección preparada y revisión

Se creó `tests/h3req1_c03_startup_smoke_s3.sh` desde S2. Mantiene iguales source manifest,
identidad del daemon/checkout, límites, allowlists, etiquetas, flujo de fallo cerrado, bootstrap,
runtime y healthz. Cambia únicamente la restauración de ownership en la extracción del snapshot;
usa manifiesto, salida y recursos S3 independientes. No edita ni sobrescribe S2.

- Runner S3 SHA-256:
  `4077a9c6e14a0588fb972f77c4b27385cc223306a63bbaea553b239c87af1689`.
- Manifiesto S3 SHA-256:
  `351c6590c24c466fe8af531f1d9661ef7a6fcc1f7170c617f223fefc70bdc018`.
- Sintaxis Bash en Docker: PASS.
- ShellCheck 0.11.0, severity warning, en contenedor aislado: PASS.
- `git diff --check`: PASS.
- Revisión independiente estática: sin hallazgos; no ejecutó Docker.

S3 no se considera PASS hasta que el runner termine, el receptor compruebe hashes y ausencia de
symlinks, y Pages/workerd complete el smoke real con healthz.
