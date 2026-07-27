"""Local-only immutable planner for the F9.7 database candidate."""

from __future__ import annotations

import hashlib
import hmac
import json
import re
from pathlib import Path
from typing import Mapping, Sequence

ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ID = "F9.7-PUBLIC-ACCESS-CLOSURE-20260727"
MANIFEST_SHA256 = "5d32ed2c977c59c38d56948e687ba2b05ecd9ad8b2d3f5752cce3a9836889de3"
ENTRY_SPECS = (
    (
        "F6-G1B-FORWARD", "g1b",
        "db/migrations/20260724_fase06_g1b_reconciliation.sql",
        "d239f7080c709cdccf7227523ff2b89b48f99a57ace376a18bbdaa4d1a4d75df",
    ),
    (
        "F6-HITO1-FORWARD", "hito1",
        "db/migrations/20260724_fase06_hito1_editorial_contract.sql",
        "b8badde99ada9de16aae126497304cfa7d02f9f6df89f3e22604965446c1af8a",
    ),
    (
        "F7-G1B-CLOSURE", "g1b_closure",
        "db/migrations/20260725_fase07_g1b_closure.sql",
        "9b83b36e0d90be048ccdfdea8fc1c175b8c7d7ac1fe25d7589d4c653f6a1c120",
    ),
    (
        "F8-HITO1-FUNCTIONAL-CLOSURE", "hito1_functional_closure",
        "db/migrations/20260725_fase08_hito1_functional_closure.sql",
        "7e392473e464df07edbcfcd7b8597ead8d7e10a47d990eedcfe6ed6cee70b527",
    ),
    (
        "F9.7-PUBLIC-ACCESS-CLOSURE", "public_access_closure",
        "db/migrations/20260727_fase09_7_public_access_closure.sql",
        "040584e96996c705add37ae84e163aa51c35c4f65357279146bd6840e61e1d6b",
    ),
)
POSTCONDITIONS = {
    "20260724_fase06_g1b_reconciliation":
        "public.verify_fase06_g1b_reconciliation()",
    "20260724_fase06_hito1_editorial_contract":
        "public.verify_fase06_hito1_contract()",
    "20260725_fase07_g1b_closure": "public.verify_fase07_g1b_closure()",
    "20260725_fase08_hito1_functional_closure":
        "public.verify_fase08_hito1_contract()",
    "20260727_fase09_7_public_access_closure":
        "public.verify_fase09_7_public_access_closure()",
}
ALLOWED_BOUNDARIES = {0, 3, 4, 5}
_DOLLAR_BODY = re.compile(
    r"(?P<tag>\$[A-Za-z_][A-Za-z0-9_]*\$|\$\$).*?(?P=tag)", re.DOTALL
)
_FORBIDDEN = re.compile(
    r"(?:^|;)\s*(?:INSERT\s+INTO|UPDATE\s+[A-Za-z\"]|"
    r"DELETE\s+FROM|MERGE\s+INTO|COPY\s+|CALL\s+|TRUNCATE\s+|"
    r"SELECT\s+|WITH\s+)",
    re.IGNORECASE,
)


class ManifestError(ValueError):
    pass


def canonical_sql_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def canonical_json_sha256(value: object) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_promotable_sql(sql: str, *, label: str) -> None:
    if not re.search(r"(?im)^\s*SET\s+search_path\s*=\s*''\s*;", sql):
        raise ManifestError(f"{label}: empty search_path is required")
    without_bodies = _DOLLAR_BODY.sub("", sql)
    without_comments = re.sub(
        r"--[^\n]*|/\*.*?\*/", "", without_bodies, flags=re.DOTALL
    )
    match = _FORBIDDEN.search(without_comments)
    if match:
        raise ManifestError(f"{label}: forbidden operational SQL {match.group(0)!r}")


def load_manifest(
    manifest_path: Path,
    target: str = "free",
    *,
    root: Path = ROOT,
) -> list[Path]:
    if target not in {"free", "pro"}:
        raise ManifestError(f"unsupported target {target}")
    def reject_duplicates(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ManifestError(f"duplicate manifest key: {key}")
            result[key] = value
        return result

    manifest = json.loads(
        manifest_path.read_text(encoding="utf-8"),
        object_pairs_hook=reject_duplicates,
    )
    if not hmac.compare_digest(canonical_json_sha256(manifest), MANIFEST_SHA256):
        raise ManifestError("F9.7 manifest does not match exact schema-v2 digest")
    if (
        manifest.get("schema_version") != 2
        or manifest.get("phase") != "F9.7"
        or manifest.get("package_id") != PACKAGE_ID
        or manifest.get("status") != "reconciled_not_certified"
        or manifest.get("blocked_targets") != ["free", "pro"]
    ):
        raise ManifestError("F9.7 manifest metadata drift")
    entries = manifest.get("entries")
    if not isinstance(entries, list) or len(entries) != 5:
        raise ManifestError("F9.7 manifest must contain exactly five entries")
    paths: list[Path] = []
    for entry, spec in zip(entries, ENTRY_SPECS):
        entry_id, component, relative_path, expected_hash = spec
        if entry != {
            "id": entry_id,
            "component": component,
            "path": relative_path,
            "sha256": expected_hash,
            "provenance": "new_forward_only",
            "targets": ["free", "pro"],
        }:
            raise ManifestError(f"F9.7 entry drift: {entry_id}")
        path = (root / relative_path).resolve()
        if root.resolve() not in path.parents:
            raise ManifestError("migration path escapes repository root")
        if canonical_sql_sha256(path) != expected_hash:
            raise ManifestError(f"migration checksum drift: {relative_path}")
        validate_promotable_sql(path.read_text(encoding="utf-8"), label=relative_path)
        paths.append(path)
    return paths


def _marker(path: Path) -> str:
    return f"sha256:{canonical_sql_sha256(path)}"


def validate_manifest_ledger_state(
    database,
    migration_files: Sequence[Path],
    applied: Mapping[str, str],
) -> list[Path]:
    expected_stems = [path.stem for path in migration_files]
    projected = {
        stem: applied[stem]
        for stem in expected_stems
        if stem in applied
    }
    prefix_size = 0
    for path in migration_files:
        if path.stem not in projected:
            break
        if not hmac.compare_digest(projected[path.stem], _marker(path)):
            raise RuntimeError(f"Ledger/checksum mismatch: {path.stem}")
        prefix_size += 1
    if any(path.stem in projected for path in migration_files[prefix_size:]):
        raise RuntimeError("Ledger must be a contiguous manifest prefix")
    if prefix_size not in ALLOWED_BOUNDARIES:
        raise RuntimeError("F9.7 only accepts ledger boundaries 0, 3, 4, or 5")
    for path in migration_files[:prefix_size]:
        signature = POSTCONDITIONS[path.stem]
        name = signature.removeprefix("public.").removesuffix("()")
        if not database.rpc_raise(name, {}):
            raise RuntimeError(f"Postcondicion fallida: {path.stem}")
    return list(migration_files[prefix_size:])


def build_manifest_package_sql(
    migration_files: Sequence[Path],
    *,
    expected_prefix: Mapping[str, str] | None = None,
    version: int,
) -> str:
    if not migration_files:
        raise RuntimeError("cannot build a zero-pending package")
    lines = [
        "LOCK TABLE public.supabase_migrations IN SHARE ROW EXCLUSIVE MODE;",
        "-- manifest-prefix-guard",
    ]
    for stem, marker in (expected_prefix or {}).items():
        lines.extend([
            "DO $manifest_prefix$", "BEGIN", "    IF NOT EXISTS (",
            "        SELECT 1 FROM public.supabase_migrations",
            f"        WHERE name = '{stem}' AND statements = '{marker}'",
            "    ) THEN RAISE EXCEPTION 'Manifest prefix drift'; END IF;",
            "END;", "$manifest_prefix$;",
        ])
    for path in migration_files:
        lines.extend([
            "DO $manifest_pending$", "BEGIN", "    IF EXISTS (",
            "        SELECT 1 FROM public.supabase_migrations",
            f"        WHERE name = '{path.stem}'",
            "    ) THEN RAISE EXCEPTION 'Manifest pending entry drift'; END IF;",
            "END;", "$manifest_pending$;",
        ])
        sql = path.read_text(encoding="utf-8")
        validate_promotable_sql(sql, label=path.name)
        lines.extend([f"-- manifest-entry {path.stem}", sql])
    for path in migration_files:
        signature = POSTCONDITIONS[path.stem]
        lines.extend([
            "DO $manifest_verify$", "BEGIN",
            f"    IF NOT {signature} THEN",
            f"        RAISE EXCEPTION 'Postcondicion fallida: {path.stem}';",
            "    END IF;", "END;", "$manifest_verify$;",
        ])
    lines.append("-- manifest-ledger-registration")
    for offset, path in enumerate(migration_files):
        lines.append(
            "INSERT INTO public.supabase_migrations "
            "(version, name, statements, applied_at) VALUES "
            f"({version + offset}, '{path.stem}', '{_marker(path)}', "
            "pg_catalog.clock_timestamp());"
        )
    lines.append("")
    return "\n".join(lines)
