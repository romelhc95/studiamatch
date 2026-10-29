#!/usr/bin/env bash
# StudIAMatch-Docs: .context/componentes/seguridad_tooling.md#registro-de-fuentes-y-gate
set -euo pipefail

if [[ -f /.dockerenv && -f /app/scripts/maintenance/h3req1_documentation_integrity.mjs ]]; then
  cd /app
  exec node scripts/maintenance/h3req1_documentation_integrity.mjs "$@"
fi

exec docker exec -w /app studiamatch-dev node scripts/maintenance/h3req1_documentation_integrity.mjs "$@"
