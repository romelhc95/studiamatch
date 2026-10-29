# H3REQ1 C03 startup S8 — despacho detenido antes de Docker

- Fecha: 2026-10-10.
- Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`.
- Rama/HEAD: `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- Comando: `bash tests/h3req1_c03_startup_smoke_s8.sh --jit H3-CLOSE-03-WORKERD-STARTUP-SMOKE-2026-10-10-S8-VALIDATION-DIAGNOSTIC --runner-sha256 30448de4b290b18c7d122feea9632459a5b0d1a21f3b6e406308943a2d367f49 --manifest-sha256 0fe6c977b02fc0479873da252d249da4720042a94e427891c0ba4c1f3538bc95`.
- Entorno: Ubuntu WSL / Bash; no se alcanzó ninguna invocación Docker.
- Fase/exit: carga de declaraciones Bash, exit `1`.
- Evidencia: `tests/h3req1_c03_startup_smoke_s8.sh:45: S7_MANIFEST_SHA256: readonly variable`; el archivo de resultado S8 no existía y no apareció un contenedor con nombre S8.
- Causa demostrada: la variable `S7_MANIFEST_SHA256` estaba declarada dos veces como `readonly`; Bash termina durante la carga del runner, antes del preflight o de cualquier operación Docker.
- Corrección: eliminada solo la segunda declaración idéntica. No se alteraron valores, condiciones, recursos ni alcance. El runner resultante es `2113a49686494357586c31e4e3031f3209986a64ac78498501274ea1c61a5ff4`; el manifiesto fue actualizado.
- Revisión independiente del delta: sin hallazgos; verificó una sola declaración y manifiesto SHA-256 `d3500ba707ebd666f4bcb61d01e625ad325c3c269eda8078a6cb4f61fa209c3f` válido.
- Siguiente acción: revalidar estáticamente runner/manifiesto y sintéticos; después reejecutar S8 bajo la autorización local vigente. No hubo runtime, healthz, Edge, DB ni SQL.
