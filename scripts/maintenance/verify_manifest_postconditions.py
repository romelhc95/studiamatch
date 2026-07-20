"""Execute manifest postconditions in a read-only PostgreSQL transaction."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

try:
    from .apply_nontransactional_migration import assert_database_url
except ImportError:
    from apply_nontransactional_migration import assert_database_url


def validate_query(sql: str) -> None:
    if not re.match(r"^SELECT\s", sql, re.IGNORECASE):
        raise RuntimeError("Postcondition debe ser SELECT")
    if ";" in sql or re.search(r"\b(FOR\s+UPDATE|pg_sleep|dblink|lo_import)\b", sql, re.IGNORECASE):
        raise RuntimeError("Postcondition contiene una operacion no permitida")
    allowed_functions = {"count", "exists", "to_regclass", "coalesce"}
    called_functions = {name.lower() for name in re.findall(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", sql)}
    if called_functions - allowed_functions:
        raise RuntimeError("Postcondition invoca una funcion no permitida")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env", choices=["free", "pro"], required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--expected-manifest-sha256", required=True)
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        actual_manifest_sha = hashlib.sha256(args.manifest.read_bytes()).hexdigest()
        if actual_manifest_sha != args.expected_manifest_sha256:
            raise RuntimeError("Checksum del manifest no coincide")
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        conditions = [
            (migration["path"], condition)
            for migration in manifest["migrations"]
            if args.env in migration["targets"]
            for condition in migration["postconditions"]
        ]
        assert_database_url(args.database_url, args.env)
        import psycopg2

        connection = psycopg2.connect(args.database_url, connect_timeout=15)
        report = {
            "release_id": manifest["release_id"],
            "revision": manifest["revision"],
            "candidate_commit": manifest["candidate_commit"],
            "manifest_sha256": actual_manifest_sha,
            "environment": args.env,
            "results": [],
        }
        try:
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SET LOCAL statement_timeout = '15s'")
                    for migration_path, condition in conditions:
                        validate_query(condition["sql"])
                        cursor.execute(condition["sql"])
                        if not cursor.description or len(cursor.description) != 1:
                            raise RuntimeError(f"Postcondition {condition['id']} debe devolver una columna")
                        row = cursor.fetchone()
                        if row is None or cursor.fetchone() is not None:
                            raise RuntimeError(f"Postcondition {condition['id']} debe devolver una fila")
                        actual = row[0]
                        if type(actual) is not type(condition["expected"]) or actual != condition["expected"]:
                            raise RuntimeError(
                                f"Postcondition {condition['id']} fallo: esperado {condition['expected']!r}, actual {actual!r}"
                            )
                        report["results"].append({
                            "migration": migration_path,
                            "id": condition["id"],
                            "status": "PASS",
                            "actual": actual,
                        })
        finally:
            connection.close()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, KeyError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"NO_GO: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
