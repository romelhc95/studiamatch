#!/usr/bin/env bash
set -euo pipefail

python3 -m py_compile \
  scripts/maintenance/db_migrate.py \
  scripts/maintenance/check_db_parity.py \
  scripts/maintenance/h2_pro_preflight_report.py

python3 -m pytest \
  tests/test_obsidian_context_state.py \
  tests/test_h2_client_evidence_docs.py \
  tests/test_h2_development_legacy_compat.py \
  tests/test_h2_editorial_migration.py \
  tests/test_h2_pro_migration_controls.py \
  tests/test_requirement_client_source_validation.py \
  tests/test_security_flow.py \
  tests/test_supabase_credentials_contract.py \
  -q
