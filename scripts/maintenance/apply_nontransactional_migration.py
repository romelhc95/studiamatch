"""Apply manifest-pinned CREATE INDEX CONCURRENTLY migrations via PostgreSQL autocommit."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

try:
    from .db_migrate import EXPECTED_PROJECT_REFS, extract_name, migration_entries_from_manifest
except ImportError:
    from db_migrate import EXPECTED_PROJECT_REFS, extract_name, migration_entries_from_manifest


INDEX_STATEMENT = re.compile(
    r"^CREATE\s+(?P<unique>UNIQUE\s+)?INDEX\s+CONCURRENTLY\s+IF\s+NOT\s+EXISTS\s+"
    r"(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)\s+ON\s+"
    r"(?P<table>public\.[a-zA-Z_][a-zA-Z0-9_]*)\s*"
    r"\((?P<columns>[a-zA-Z_][a-zA-Z0-9_]*(?:\s*,\s*[a-zA-Z_][a-zA-Z0-9_]*)*)\)"
    r"(?:\s+WHERE\s+(?P<predicate>[a-zA-Z0-9_\s.=<>]+))?$",
    re.IGNORECASE,
)


def split_index_statements(sql: str) -> list[dict]:
    body = "\n".join(line for line in sql.splitlines() if not line.lstrip().startswith("--"))
    statements = [statement.strip() for statement in body.split(";") if statement.strip()]
    parsed = []
    for statement in statements:
        match = INDEX_STATEMENT.fullmatch(statement)
        if not match:
            raise RuntimeError("Solo se permite CREATE INDEX CONCURRENTLY IF NOT EXISTS")
        parsed.append({
            "name": match.group("name"),
            "table": match.group("table").lower(),
            "columns": tuple(column.strip().lower() for column in match.group("columns").split(",")),
            "predicate": _normalize_predicate(match.group("predicate")),
            "unique": bool(match.group("unique")),
            "sql": statement,
        })
    if not parsed:
        raise RuntimeError("La migration no contiene indices concurrentes")
    return parsed


def _normalize_predicate(predicate):
    if not predicate:
        return None
    return re.sub(r"[()\s]+", "", predicate).lower()


def _read_index_state(cursor, spec):
    cursor.execute(
        """
        SELECT i.indisvalid, i.indisready, i.indisunique, n.nspname, t.relname,
               pg_catalog.pg_get_expr(i.indpred, i.indrelid), am.amname
        FROM pg_catalog.pg_index i
        JOIN pg_catalog.pg_class idx ON idx.oid = i.indexrelid
        JOIN pg_catalog.pg_class t ON t.oid = i.indrelid
        JOIN pg_catalog.pg_namespace n ON n.oid = t.relnamespace
        JOIN pg_catalog.pg_am am ON am.oid = idx.relam
        WHERE idx.oid = pg_catalog.to_regclass(%s)
        """,
        (f"public.{spec['name']}",),
    )
    row = cursor.fetchone()
    if not row:
        return None
    cursor.execute(
        """
        SELECT a.attname
        FROM pg_catalog.pg_index i
        JOIN LATERAL unnest(i.indkey) WITH ORDINALITY AS key(attnum, ord) ON true
        JOIN pg_catalog.pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = key.attnum
        WHERE i.indexrelid = pg_catalog.to_regclass(%s)
        ORDER BY key.ord
        """,
        (f"public.{spec['name']}",),
    )
    columns = tuple(item[0].lower() for item in cursor.fetchall())
    return {
        "valid": row[0],
        "ready": row[1],
        "unique": row[2],
        "table": f"{row[3]}.{row[4]}".lower(),
        "predicate": _normalize_predicate(row[5]),
        "method": row[6].lower(),
        "columns": columns,
    }


def _assert_index_definition(spec, state):
    expected = {**spec, "ready": True, "method": "btree"}
    for key in ("ready", "method", "unique", "table", "predicate", "columns"):
        if state[key] != expected[key]:
            raise RuntimeError(f"Indice {spec['name']} existe con definicion distinta ({key})")


def preflight_ledger(connection, entries):
    with connection.cursor() as cursor:
        for entry in entries:
            name = extract_name(entry["absolute_path"])
            cursor.execute(
                "SELECT statements FROM public.supabase_migrations WHERE name = %s",
                (name,),
            )
            row = cursor.fetchone()
            if not row:
                continue
            try:
                metadata = json.loads(row[0])
            except (TypeError, json.JSONDecodeError) as exc:
                raise RuntimeError(f"Ledger sin metadata valida para {name}") from exc
            if metadata.get("sha256") != entry["sha256"]:
                raise RuntimeError(f"Drift de checksum en ledger para {name}")


def preflight_indexes(connection, entries):
    with connection.cursor() as cursor:
        for entry in entries:
            content = Path(entry["absolute_path"]).read_bytes()
            if hashlib.sha256(content).hexdigest() != entry["sha256"]:
                raise RuntimeError(f"Checksum cambio antes del preflight de {entry['path']}")
            for spec in split_index_statements(content.decode("utf-8")):
                state = _read_index_state(cursor, spec)
                if state and state["valid"]:
                    _assert_index_definition(spec, state)


def assert_database_url(dsn: str, target: str) -> None:
    parsed = urlparse(dsn)
    expected_ref = EXPECTED_PROJECT_REFS[target]
    direct_host = f"db.{expected_ref}.supabase.co"
    is_direct = parsed.hostname == direct_host and parsed.username == "postgres"
    is_pooler = (
        bool(parsed.hostname)
        and parsed.hostname.endswith(".pooler.supabase.com")
        and parsed.username == f"postgres.{expected_ref}"
    )
    sslmode = parse_qs(parsed.query).get("sslmode", [""])[0]
    if parsed.scheme not in {"postgres", "postgresql"} or not (is_direct or is_pooler):
        raise RuntimeError(f"SUPABASE_DB_URL no corresponde al project ref de {target}")
    if sslmode != "verify-full":
        raise RuntimeError("SUPABASE_DB_URL debe exigir TLS e identidad con sslmode=verify-full")


def _apply_entry(connection, entry, release_metadata, dry_run=False):
    path = Path(entry["absolute_path"])
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != entry["sha256"]:
        raise RuntimeError(f"Checksum cambio antes de aplicar {entry['path']}")
    statements = split_index_statements(content.decode("utf-8"))
    if dry_run:
        for spec in statements:
            print(f"  PENDIENTE: {spec['name']}")
        return

    with connection.cursor() as cursor:
        for spec in statements:
            state = _read_index_state(cursor, spec)
            if state and not state["valid"]:
                cursor.execute(f'DROP INDEX CONCURRENTLY IF EXISTS public."{spec["name"]}"')
                state = None
            if state:
                _assert_index_definition(spec, state)
            cursor.execute(spec["sql"])
            verified = _read_index_state(cursor, spec)
            if not verified or not verified["valid"]:
                raise RuntimeError(f"Indice invalido despues de aplicar: {spec['name']}")
            _assert_index_definition(spec, verified)

        name = extract_name(path)
        metadata = json.dumps(
            {"sha256": entry["sha256"], **release_metadata},
            sort_keys=True,
            separators=(",", ":"),
        )
        cursor.execute(
            """
            INSERT INTO public.supabase_migrations(version, name, statements, applied_at)
            VALUES (0, %s, %s, pg_catalog.now())
            ON CONFLICT (name) DO NOTHING
            """,
            (name, metadata),
        )
        cursor.execute("SELECT statements FROM public.supabase_migrations WHERE name = %s", (name,))
        recorded = cursor.fetchone()
        if not recorded:
            raise RuntimeError(f"No se registro {name} en el ledger")
        try:
            recorded_metadata = json.loads(recorded[0])
        except (TypeError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Ledger sin metadata valida para {name}") from exc
        if recorded_metadata.get("sha256") != entry["sha256"]:
            raise RuntimeError(f"Drift de checksum en ledger para {name}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env", choices=["free", "pro"], required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--expected-manifest-sha256", required=True)
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        manifest, entries = migration_entries_from_manifest(
            args.manifest,
            args.env,
            args.expected_manifest_sha256,
            args.repo_root,
            transactional=False,
        )
        if not entries:
            print("No hay migrations no transaccionales para este target")
            return 0
        dsn = os.environ.get("SUPABASE_DB_URL", "")
        if not dsn:
            raise RuntimeError("Falta SUPABASE_DB_URL")
        assert_database_url(dsn, args.env)
        import psycopg2

        connection = psycopg2.connect(dsn, connect_timeout=15)
        connection.autocommit = True
        metadata = {
            "release_id": manifest["release_id"],
            "revision": manifest["revision"],
            "candidate_commit": manifest["candidate_commit"],
            "manifest_sha256": args.expected_manifest_sha256,
            "runner": "nontransactional-v1",
        }
        try:
            preflight_ledger(connection, entries)
            preflight_indexes(connection, entries)
            for entry in entries:
                _apply_entry(connection, entry, metadata, args.dry_run)
        finally:
            connection.close()
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"NO_GO: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
