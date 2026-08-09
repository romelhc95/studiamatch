import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlparse

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv(*_args, **_kwargs):
        return False

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_db_client():
    from shared.db_client import get_db_client as _get_db_client

    return _get_db_client()


STATE_SCHEMA = "f10-production-canary-state.v1"
SUMMARY_SCHEMA = "f10-production-canary-state-summary.v1"

TABLES = {
    "staging_raw": {"pipeline": True, "cohort_column": "institution_id"},
    "cleansed_programs": {"pipeline": True, "cohort_column": "institution_id"},
    "enriched_programs": {"pipeline": True, "cohort_column": "institution_id"},
    "courses": {"pipeline": False, "cohort_column": "institution_id"},
    "institution_site_profiles": {"pipeline": True, "cohort_column": "institution_id"},
    "institutions": {"pipeline": False, "cohort_column": "id"},
}
VOLATILE_RESTORE_COLUMNS = {"created_at", "updated_at"}
CANARY_RUN_METADATA_KEY = "f10_production_canary_run_id"
CANARY_PROVIDER_MARKER = "f10-production-canary"
CANARY_PROFILE_NOTE_PREFIX = "F10 production canary run "
NON_COHORT_ATTESTATION_BATCH_SIZE = 10


def _ensure_github_production_context():
    if os.getenv("GITHUB_ACTIONS") != "true":
        raise RuntimeError("Production canary scripts must run inside GitHub Actions")
    if os.getenv("GITHUB_EVENT_NAME") != "workflow_dispatch":
        raise RuntimeError("Production canary must run from workflow_dispatch")
    if os.getenv("GITHUB_REF_NAME") != "main":
        raise RuntimeError("Production canary must run from the main branch")
    if os.getenv("CANARY_EXPECTED_ENVIRONMENT") != "Production":
        raise RuntimeError("Production canary expected environment mismatch")


def _ensure_production_supabase_target():
    expected_host = os.getenv("F10_PRODUCTION_CANARY_SUPABASE_HOST", "").strip().lower()
    if not expected_host:
        raise RuntimeError("Production canary Supabase host allowlist is not configured")
    for variable_name in ("SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_URL"):
        parsed = urlparse(os.getenv(variable_name, ""))
        host = (parsed.hostname or "").lower()
        try:
            port = parsed.port
        except ValueError as exc:
            raise RuntimeError(f"{variable_name} has invalid Supabase URL port") from exc
        if (
            parsed.scheme != "https"
            or parsed.username
            or parsed.password
            or port not in (None, 443)
            or host != expected_host
        ):
            raise RuntimeError(f"{variable_name} does not match the Production Supabase host allowlist")


def _mask_github_value(value):
    if os.getenv("GITHUB_ACTIONS") == "true" and value not in (None, ""):
        print(f"::add-mask::{value}")


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _restorable_row(row):
    return {
        key: value
        for key, value in row.items()
        if key not in VOLATILE_RESTORE_COLUMNS
    }


def _restorable_rows(rows):
    return [_restorable_row(row) for row in _sort_rows(rows)]


def _row_metadata(row):
    metadata = row.get("metadata") if isinstance(row, dict) else {}
    if isinstance(metadata, dict):
        return metadata
    if isinstance(metadata, str):
        try:
            parsed = json.loads(metadata)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _has_canary_marker(table, row, canary_run_id):
    if not canary_run_id:
        return False
    if table == "courses":
        marker = f"{CANARY_PROVIDER_MARKER}:{canary_run_id}"
        return marker in str(row.get("provider_used") or "").split("|")
    if table == "institution_site_profiles":
        marker = f"{CANARY_PROFILE_NOTE_PREFIX}{canary_run_id}"
        return marker in [line.strip() for line in str(row.get("notes") or "").splitlines()]
    return _row_metadata(row).get(CANARY_RUN_METADATA_KEY) == canary_run_id


def _has_any_canary_marker(table, row):
    if table == "courses":
        return any(
            part.startswith(f"{CANARY_PROVIDER_MARKER}:")
            for part in str(row.get("provider_used") or "").split("|")
        )
    if table == "institution_site_profiles":
        return any(
            line.strip().startswith(CANARY_PROFILE_NOTE_PREFIX)
            for line in str(row.get("notes") or "").splitlines()
        )
    return CANARY_RUN_METADATA_KEY in _row_metadata(row)


def _ensure_clean_prestate(tables):
    dirty_count = sum(
        1
        for table, rows in tables.items()
        for row in rows
        if _has_any_canary_marker(table, row)
    )
    if dirty_count:
        raise RuntimeError("Canary pre-state contains dirty canary leftovers")


def _digest_rows(rows):
    return hashlib.sha256(_canonical(_sort_rows(rows)).encode("utf-8")).hexdigest()


def _row_id(row):
    row_id = row.get("id") if isinstance(row, dict) else None
    if row_id in (None, ""):
        raise RuntimeError("Canary state row missing id")
    return str(row_id)


def _sort_rows(rows):
    return sorted(rows, key=lambda row: _row_id(row))


def _row_map(rows):
    result = {}
    for row in rows:
        row_id = _row_id(row)
        if row_id in result:
            raise RuntimeError("Duplicate row id in canary state")
        result[row_id] = row
    return result


def _parse_timestamp(value):
    if not value:
        return None
    try:
        if isinstance(value, str):
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        else:
            parsed = value
    except (TypeError, ValueError) as exc:
        raise RuntimeError("Invalid production canary timestamp") from exc
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _select_rows(db, table, filters, *, batch_size=1000):
    config = TABLES[table]
    if config["pipeline"]:
        rows = db.select_all_pipeline(
            table,
            filters=filters,
            columns="*",
            batch_size=batch_size,
            order="id.asc",
        )
    else:
        rows = db.select_all_service(
            table,
            filters=filters,
            columns="*",
            batch_size=batch_size,
            order="id.asc",
        )
    return _sort_rows(rows or [])


def _resolve_institution(db, slug):
    rows = db.select_service_raise(
        "institutions",
        filters=f"slug=eq.{quote(str(slug), safe='')}",
        columns="id,slug",
        limit=2,
    )
    if len(rows) != 1:
        raise RuntimeError("Expected exactly one institution for canary cohort")
    return rows[0]


def _select_table_rows(db, table, institution_id):
    column = TABLES[table]["cohort_column"]
    filters = f"{column}=eq.{quote(str(institution_id), safe='')}"
    return _select_rows(db, table, filters)


def _select_rows_by_ids(db, table, row_ids):
    if not row_ids:
        return []
    quoted_ids = ",".join(quote(str(row_id), safe="") for row_id in sorted(set(row_ids)))
    return _select_rows(db, table, f"id=in.({quoted_ids})")


def _select_restore_rows(db, table, institution_id, before_rows):
    rows_by_id = _row_map(_select_table_rows(db, table, institution_id))
    missing_before_ids = [
        _row_id(row)
        for row in before_rows
        if _row_id(row) not in rows_by_id
    ]
    for row in _select_rows_by_ids(db, table, missing_before_ids):
        rows_by_id[_row_id(row)] = row
    return _sort_rows(rows_by_id.values())


def _select_non_cohort_groups(db, table, institution_id):
    config = TABLES[table]
    column = config["cohort_column"]
    batch_size = NON_COHORT_ATTESTATION_BATCH_SIZE
    return {
        "not_institution": _select_rows(
            table=table,
            db=db,
            filters=f"{column}=neq.{quote(str(institution_id), safe='')}",
            batch_size=batch_size,
        ),
        "null_institution": _select_rows(
            table=table,
            db=db,
            filters=f"{column}=is.null",
            batch_size=batch_size,
        ),
    }


def _attest_non_cohort(db, table, institution_id):
    return {
        name: {
            "count": len(rows),
            "digest": _digest_rows(_restorable_rows(rows)),
        }
        for name, rows in _select_non_cohort_groups(db, table, institution_id).items()
    }


def _sanitize_non_cohort_attestations(attestations):
    return {
        table: {
            name: {"count": group["count"]}
            for name, group in groups.items()
        }
        for table, groups in attestations.items()
    }


def _sanitize_snapshot(snapshot):
    table_summaries = {}
    for table, rows in snapshot["tables"].items():
        status_counts = {}
        for row in rows:
            status = str(row.get("status", "__no_status__"))
            status_counts[status] = status_counts.get(status, 0) + 1
        table_summaries[table] = {
            "row_count": len(rows),
            "status_counts": status_counts,
        }
    return {
        "schema": SUMMARY_SCHEMA,
        "operation": "snapshot",
        "generated_at": snapshot["generated_at"],
        "github": {"ref_name": snapshot["github"].get("ref_name")},
        "cohort": {"institution_slug": "redacted"},
        "tables": table_summaries,
        "non_cohort_counts": _sanitize_non_cohort_attestations(snapshot["non_cohort_attestations"]),
    }


def _write_json(path, payload, *, private=False):
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    if private:
        os.chmod(output.parent, 0o700)
        flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
        fd = os.open(output, flags, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        os.chmod(output, 0o600)
        return
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def capture_snapshot(args):
    _ensure_github_production_context()
    load_dotenv()
    _ensure_production_supabase_target()
    db = get_db_client()
    institution = _resolve_institution(db, args.institution_slug)
    institution_id = institution["id"]
    _mask_github_value(institution_id)
    _mask_github_value(institution["slug"])

    tables = {
        table: _select_table_rows(db, table, institution_id)
        for table in TABLES
    }
    _ensure_clean_prestate(tables)
    non_cohort_attestations = {
        table: _attest_non_cohort(db, table, institution_id)
        for table in TABLES
    }
    snapshot = {
        "schema": STATE_SCHEMA,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "canary_run_id": os.getenv("F10_PRODUCTION_CANARY_RUN_ID"),
        "github": {
            "event_name": os.getenv("GITHUB_EVENT_NAME"),
            "ref_name": os.getenv("GITHUB_REF_NAME"),
            "sha": os.getenv("GITHUB_SHA"),
            "run_id": os.getenv("GITHUB_RUN_ID"),
        },
        "cohort": {
            "institution_slug": institution["slug"],
        },
        "tables": tables,
        "non_cohort_attestations": non_cohort_attestations,
    }
    _write_json(args.output, snapshot, private=True)
    if args.summary_output:
        _write_json(args.summary_output, _sanitize_snapshot(snapshot))
    print("Wrote private production canary state snapshot")


def _delete_extra_rows(db, table, rows, snapshot_generated_at, canary_run_id):
    deleted = 0
    snapshot_time = _parse_timestamp(snapshot_generated_at)
    for row in rows:
        row_id = _row_id(row)
        created_at = _parse_timestamp(row.get("created_at"))
        if (
            not _has_canary_marker(table, row, canary_run_id)
            or not created_at
            or not snapshot_time
            or created_at <= snapshot_time
        ):
            raise RuntimeError(
                "Refusing to delete pre-existing or unverified extra canary row"
            )
        result = db.delete(table, filters=f"id=eq.{quote(row_id, safe='')}")
        if not result:
            raise RuntimeError(f"Failed to delete canary-created row from {table}")
        deleted += 1
    return deleted


def _patch_changed_rows(db, table, before_by_id, current_by_id):
    patched = 0
    missing = []
    for row_id, before in before_by_id.items():
        current = current_by_id.get(row_id)
        if current is None:
            missing.append(row_id)
            continue
        if _canonical(_restorable_row(current)) == _canonical(_restorable_row(before)):
            continue
        payload = {
            key: value
            for key, value in before.items()
            if key not in {"id", *VOLATILE_RESTORE_COLUMNS}
        }
        db.patch_exact_one_raise(
            table,
            filters=f"id=eq.{quote(row_id, safe='')}",
            data=payload,
            expected_id=before.get("id"),
        )
        patched += 1
    if missing:
        raise RuntimeError(f"Canary restore cannot recreate missing {table} rows")
    return patched


def restore_snapshot(args):
    _ensure_github_production_context()
    load_dotenv()
    _ensure_production_supabase_target()
    snapshot = json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
    if snapshot.get("schema") != STATE_SCHEMA:
        raise RuntimeError("Unsupported production canary state snapshot schema")
    if snapshot.get("cohort", {}).get("institution_slug") != args.institution_slug:
        raise RuntimeError("Production canary state snapshot does not match requested institution")

    db = get_db_client()
    institution = _resolve_institution(db, args.institution_slug)
    institution_id = institution["id"]
    _mask_github_value(institution_id)
    _mask_github_value(institution["slug"])
    summary = {
        "schema": SUMMARY_SCHEMA,
        "operation": "restore",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "github": {
            "ref_name": os.getenv("GITHUB_REF_NAME"),
        },
        "cohort": {"institution_slug": "redacted"},
        "tables": {},
        "non_cohort_attestations_match": True,
        "after_matches_snapshot": True,
        "expect_noop": bool(args.expect_noop),
    }

    for table in TABLES:
        before_rows = _sort_rows(snapshot["tables"].get(table, []))
        before_by_id = _row_map(before_rows)
        current_rows = _select_restore_rows(db, table, institution_id, before_rows)
        current_by_id = _row_map(current_rows)
        current_cohort_ids = {
            _row_id(row)
            for row in _select_table_rows(db, table, institution_id)
        }
        extra_rows = [
            row
            for row in current_rows
            if _row_id(row) in current_cohort_ids and _row_id(row) not in before_by_id
        ]
        deleted = _delete_extra_rows(
            db,
            table,
            extra_rows,
            snapshot["generated_at"],
            snapshot.get("canary_run_id"),
        )
        patched = _patch_changed_rows(db, table, before_by_id, current_by_id)
        after_rows = _select_table_rows(db, table, institution_id)
        after_matches = _canonical(_restorable_rows(after_rows)) == _canonical(_restorable_rows(before_rows))
        non_cohort_attestation = _attest_non_cohort(db, table, institution_id)
        non_cohort_matches = non_cohort_attestation == snapshot["non_cohort_attestations"].get(table)
        summary["tables"][table] = {
            "deleted_canary_rows": deleted,
            "restored_existing_rows": patched,
            "snapshot_row_count": len(before_rows),
            "after_row_count": len(after_rows),
            "after_matches_snapshot": after_matches,
            "non_cohort_attestation_matches": non_cohort_matches,
            "volatile_columns_excluded": sorted(VOLATILE_RESTORE_COLUMNS),
        }
        summary["after_matches_snapshot"] = summary["after_matches_snapshot"] and after_matches
        summary["non_cohort_attestations_match"] = summary["non_cohort_attestations_match"] and non_cohort_matches

    if args.summary_output:
        _write_json(args.summary_output, summary)
    if not summary["after_matches_snapshot"]:
        raise RuntimeError("Production canary cleanup did not restore the exact restorable pre-state")
    if not summary["non_cohort_attestations_match"]:
        raise RuntimeError("Non-cohort row content changed during production canary")
    if args.expect_noop:
        changed = [
            table
            for table, data in summary["tables"].items()
            if data["deleted_canary_rows"] or data["restored_existing_rows"]
        ]
        if changed:
            raise RuntimeError(f"Production canary cleanup was not idempotent: {', '.join(changed)}")
    print("Restored production canary state from private snapshot")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Snapshot or restore bounded F10 Production canary state")
    subparsers = parser.add_subparsers(dest="command", required=True)

    snapshot = subparsers.add_parser("snapshot")
    snapshot.add_argument("--institution-slug", required=True)
    snapshot.add_argument("--output", required=True)
    snapshot.add_argument("--summary-output")

    restore = subparsers.add_parser("restore")
    restore.add_argument("--institution-slug", required=True)
    restore.add_argument("--snapshot", required=True)
    restore.add_argument("--summary-output")
    restore.add_argument("--expect-noop", action="store_true")

    args = parser.parse_args(argv)
    if args.command == "snapshot":
        capture_snapshot(args)
    elif args.command == "restore":
        restore_snapshot(args)
    else:
        raise RuntimeError(f"Unsupported command: {args.command}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
