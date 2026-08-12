#!/usr/bin/env python3
"""Offline contract for the single-use F10.10 PUBLIC database ACL diagnostic."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import os
import stat
from pathlib import Path
from typing import Any, Sequence


SCHEMA = "f10.10-m3-public-db-acl-diagnostic-v1"
GATE = "APPROVE_F10_10_M3_PUBLIC_DB_ACL_DIAGNOSTIC_FREE"
MAX_INPUT_BYTES = 4096

DIAGNOSTIC_SQL = """BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY;
WITH database_acl AS (
  SELECT d.datname, d.datallowconn,
    COALESCE(bool_or(x.privilege_type = 'CONNECT') FILTER (WHERE x.grantee = 0), false) AS public_connect,
    COALESCE(bool_or(x.privilege_type = 'TEMPORARY') FILTER (WHERE x.grantee = 0), false) AS public_temporary,
    COALESCE(bool_or(x.privilege_type = 'CREATE') FILTER (WHERE x.grantee = 0), false) AS public_create
  FROM pg_catalog.pg_database AS d
  CROSS JOIN LATERAL pg_catalog.aclexplode(
    COALESCE(d.datacl, pg_catalog.acldefault('d', d.datdba))
  ) AS x
  GROUP BY d.oid, d.datname, d.datallowconn
), classified AS (
  SELECT *, CASE
    WHEN datname = 'postgres' THEN 'TARGET'
    WHEN datallowconn THEN 'OTHER_CONNECTABLE'
    ELSE 'NON_CONNECTABLE'
  END AS database_class
  FROM database_acl
)
SELECT
  pg_catalog.current_setting('transaction_read_only') = 'on' AS transaction_read_only,
  pg_catalog.current_setting('transaction_isolation') = 'repeatable read' AS transaction_repeatable_read,
  count(*) FILTER (WHERE database_class = 'TARGET')::integer AS target_count,
  COALESCE(bool_and(datallowconn) FILTER (WHERE database_class = 'TARGET'), false) AS target_connectable,
  count(*) FILTER (WHERE database_class = 'TARGET' AND public_connect)::integer AS target_public_connect_count,
  count(*) FILTER (WHERE database_class = 'TARGET' AND (public_temporary OR public_create))::integer AS target_violation_count,
  count(*) FILTER (WHERE database_class = 'OTHER_CONNECTABLE')::integer AS other_connectable_count,
  count(*) FILTER (WHERE database_class = 'OTHER_CONNECTABLE' AND (public_connect OR public_temporary OR public_create))::integer AS other_connectable_violation_count,
  count(*) FILTER (WHERE database_class = 'NON_CONNECTABLE')::integer AS non_connectable_count,
  count(*) FILTER (WHERE database_class = 'NON_CONNECTABLE' AND public_connect)::integer AS non_connectable_public_connect_acl_count,
  count(*) FILTER (WHERE database_class = 'NON_CONNECTABLE' AND public_temporary)::integer AS non_connectable_public_temporary_acl_count,
  count(*) FILTER (WHERE database_class = 'NON_CONNECTABLE' AND public_create)::integer AS non_connectable_public_create_acl_count
FROM classified;
COMMIT;"""

FIELDS = (
    "transaction_read_only",
    "transaction_repeatable_read",
    "target_count",
    "target_connectable",
    "target_public_connect_count",
    "target_violation_count",
    "other_connectable_count",
    "other_connectable_violation_count",
    "non_connectable_count",
    "non_connectable_public_connect_acl_count",
    "non_connectable_public_temporary_acl_count",
    "non_connectable_public_create_acl_count",
)


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()


def sql_digest() -> str:
    return "sha256:" + hashlib.sha256(DIAGNOSTIC_SQL.encode()).hexdigest()


def validate_row(row: Any) -> dict[str, Any]:
    if not isinstance(row, dict) or tuple(sorted(row)) != tuple(sorted(FIELDS)):
        raise ValueError("STOP_DIAGNOSTIC_SCHEMA")
    values: dict[str, int | bool] = {}
    for field in FIELDS:
        value = row[field]
        if field in {"transaction_read_only", "transaction_repeatable_read", "target_connectable"}:
            if not isinstance(value, bool):
                raise ValueError("STOP_DIAGNOSTIC_SCHEMA")
        elif isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError("STOP_DIAGNOSTIC_SCHEMA")
        values[field] = value

    policy_conformant = (
        values["transaction_read_only"] is True
        and values["transaction_repeatable_read"] is True
        and values["target_count"] == 1
        and values["target_connectable"] is True
        and values["target_violation_count"] == 0
        and values["other_connectable_violation_count"] == 0
        and values["non_connectable_public_temporary_acl_count"] == 0
        and values["non_connectable_public_create_acl_count"] == 0
    )
    return {
        "schema": SCHEMA,
        "gate": GATE,
        "query_digest": sql_digest(),
        "database_classes": ["TARGET", "OTHER_CONNECTABLE", "NON_CONNECTABLE"],
        "summary": values,
        "policy_conformant": policy_conformant,
        "application_rows_read": 0,
        "provider_calls": 0,
        "writer_calls": 0,
        "ddl": 0,
        "dml": 0,
        "decision": "OFFLINE_ROW_VALIDATED_NOT_REMOTE_EVIDENCE",
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("sql", "validate"), required=True)
    parser.add_argument("--input")
    return parser


def run(argv: Sequence[str]) -> tuple[int, dict[str, Any]]:
    args = _parser().parse_args(argv)
    if args.mode == "sql":
        if args.input is not None:
            raise ValueError("STOP_CLI_INVALID")
        return 0, {"schema": SCHEMA, "query_digest": sql_digest(), "sql": DIAGNOSTIC_SQL}
    if not args.input:
        raise ValueError("STOP_CLI_INVALID")
    path = Path(args.input)
    descriptor = -1
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size <= 0 or metadata.st_size > MAX_INPUT_BYTES:
            raise ValueError("STOP_INPUT_INVALID")
        raw = os.read(descriptor, MAX_INPUT_BYTES + 1)
        if len(raw) != metadata.st_size or os.read(descriptor, 1):
            raise ValueError("STOP_INPUT_INVALID")
    except OSError as exc:
        raise ValueError("STOP_INPUT_INVALID") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    manifest = validate_row(json.loads(raw.decode("utf-8")))
    # Local JSON can exercise the schema but can never attest remote execution.
    return 3, manifest


def main(argv: Sequence[str] | None = None) -> int:
    try:
        code, output = run(sys.argv[1:] if argv is None else argv)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        reason = str(exc) if str(exc).startswith("STOP_") else "STOP_INPUT_INVALID"
        code, output = 2, {"schema": SCHEMA, "gate": GATE, "decision": reason}
    sys.stdout.buffer.write(canonical_json(output) + b"\n")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
