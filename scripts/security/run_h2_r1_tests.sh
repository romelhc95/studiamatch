#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPYCACHEPREFIX=/tmp/studiamatch-h2-pycache

for name in \
  NEXT_SUPABASE_SECRET_KEY \
  NEXT_SUPABASE_PUBLISHABLE_KEY \
  NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY \
  NEXT_PUBLIC_SUPABASE_URL \
  SUPABASE_URL \
  CF_API_TOKEN \
  CF_ACCOUNT_ID
do
  if [ -n "${!name:-}" ]; then
    echo "R1_SECRET_ENV_PRESENT:${name}" >&2
    exit 1
  fi
done

python3 scripts/security/validate_work_package.py
python3 scripts/security/validate_context_graph.py
if python3 -m pytest --version >/dev/null 2>&1; then
  python3 -m pytest -q tests/test_work_package_manifest.py tests/test_context_graph_semantics.py
else
  python3 -m unittest tests.test_work_package_manifest tests.test_context_graph_semantics
fi

echo "h2 r1 governance tests passed without cloud secrets"
