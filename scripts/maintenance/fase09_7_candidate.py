"""Local-only immutable planner for the F9.7 database candidate."""

from __future__ import annotations

import hashlib
import hmac
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from scripts.maintenance.fase09_7_notify_truth import NOTIFY_VARIANTS_BY_NAME

ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ID = "F9.7-PUBLIC-ACCESS-TRIGGER-RETIREMENT-V3-20260728"
MANIFEST_SHA256 = "33c3b262dd1754d2fd8e7c8684e50601043654010c41b2d7b97c7386645a180c"
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
    (
        "F9.7-NOTIFY-NEW-LEAD-RETIREMENT-V3",
        "notify_new_lead_retirement_v3",
        "db/migrations/20260728_fase09_7_notify_new_lead_retirement_v3.sql",
        "f1fd6e618bd16ff4216f46587ce897756e465ada92ee9bc398335cd9239fe188",
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
    "20260728_fase09_7_notify_new_lead_retirement_v3":
        "public.verify_fase09_7_notify_new_lead_retirement()",
}
ALLOWED_BOUNDARIES = {0, 3, 4, 5, 6}
F9_7_V2_RETIREMENT_STEM = "20260727_fase09_7_notify_new_lead_retirement"
RETIREMENT_STEM = "20260728_fase09_7_notify_new_lead_retirement_v3"
PUBLIC_ACCESS_STEM = "20260727_fase09_7_public_access_closure"
F9_5_HISTORICAL_NON_PROMOTABLE_STEMS = frozenset(
    {
        "20260726_fase09_5_rls_canary_reconciliation",
        "20260726_fase09_5_policy_inventory_reconciliation",
    }
)
PUBLIC_ACCESS_VERIFIER_SOURCE_SHA256 = (
    "207ea3023a7485bbec6cf4e90a975d15907bcd771cf155d2f4d0bc97ff1b7d2a"
)
PUBLIC_ACCESS_VERIFIER_DEFINITION_SHA256 = (
    "be9d1514c8f40eae3b9a351640c0c2a21f3308224de103a4b8e9f4c4193ae137"
)
PUBLIC_ACCESS_VERIFIER_ATTESTATION = f"""(
    SELECT pg_catalog.count(*) = 1
       AND pg_catalog.bool_and(
           owner.rolname = 'postgres'
           AND language_record.lanname = 'plpgsql'
           AND return_namespace.nspname = 'pg_catalog'
           AND return_type.typname = 'bool'
           AND procedure_record.prokind = 'f'
           AND NOT procedure_record.prosecdef
           AND procedure_record.provolatile = 's'
           AND NOT procedure_record.proisstrict
           AND NOT procedure_record.proleakproof
           AND procedure_record.proparallel = 'u'
           AND NOT procedure_record.proretset
           AND procedure_record.pronargs = 0
           AND procedure_record.pronargdefaults = 0
           AND procedure_record.proconfig IS NOT DISTINCT FROM
               ARRAY['search_path=""']::text[]
           AND pg_catalog.octet_length(pg_catalog.replace(
               procedure_record.prosrc, E'\\r\\n', E'\\n'
           )) = 35054
           AND pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
               pg_catalog.replace(procedure_record.prosrc, E'\\r\\n', E'\\n'),
               'UTF8'
           )), 'hex') = '{PUBLIC_ACCESS_VERIFIER_SOURCE_SHA256}'
           AND pg_catalog.octet_length(pg_catalog.replace(
               pg_catalog.pg_get_functiondef(procedure_record.oid), E'\\r\\n', E'\\n'
           )) = 35218
           AND pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
               pg_catalog.replace(
                   pg_catalog.pg_get_functiondef(procedure_record.oid),
                   E'\\r\\n', E'\\n'
               ),
               'UTF8'
           )), 'hex') = '{PUBLIC_ACCESS_VERIFIER_DEFINITION_SHA256}'
           AND (
               SELECT pg_catalog.count(*)
               FROM pg_catalog.aclexplode(COALESCE(
                   procedure_record.proacl,
                   pg_catalog.acldefault('f', procedure_record.proowner)
               )) AS acl
           ) = 2
           AND (
               SELECT pg_catalog.count(*)
               FROM pg_catalog.aclexplode(COALESCE(
                   procedure_record.proacl,
                   pg_catalog.acldefault('f', procedure_record.proowner)
               )) AS acl
               WHERE acl.privilege_type = 'EXECUTE'
                 AND NOT acl.is_grantable
                 AND acl.grantee = procedure_record.proowner
           ) = 1
           AND (
               SELECT pg_catalog.count(*)
               FROM pg_catalog.aclexplode(COALESCE(
                   procedure_record.proacl,
                   pg_catalog.acldefault('f', procedure_record.proowner)
               )) AS acl
               WHERE acl.privilege_type = 'EXECUTE'
                 AND NOT acl.is_grantable
                 AND acl.grantee = (
                     SELECT role.oid
                     FROM pg_catalog.pg_roles AS role
                     WHERE role.rolname = 'service_role'
                 )
           ) = 1
           AND (
               SELECT pg_catalog.count(*)
               FROM pg_catalog.pg_depend AS dependency
               WHERE dependency.classid =
                     'pg_catalog.pg_proc'::pg_catalog.regclass
                 AND dependency.objid = procedure_record.oid
                 AND dependency.objsubid = 0
           ) = 2
           AND (
               SELECT pg_catalog.count(*)
               FROM pg_catalog.pg_depend AS dependency
               WHERE dependency.classid =
                     'pg_catalog.pg_proc'::pg_catalog.regclass
                 AND dependency.objid = procedure_record.oid
                 AND dependency.objsubid = 0
                 AND dependency.refclassid =
                     'pg_catalog.pg_namespace'::pg_catalog.regclass
                 AND dependency.refobjid = procedure_record.pronamespace
                 AND dependency.refobjsubid = 0
                 AND dependency.deptype = 'n'
           ) = 1
           AND (
               SELECT pg_catalog.count(*)
               FROM pg_catalog.pg_depend AS dependency
               WHERE dependency.classid =
                     'pg_catalog.pg_proc'::pg_catalog.regclass
                 AND dependency.objid = procedure_record.oid
                 AND dependency.objsubid = 0
                 AND dependency.refclassid =
                     'pg_catalog.pg_language'::pg_catalog.regclass
                 AND dependency.refobjid = procedure_record.prolang
                 AND dependency.refobjsubid = 0
                 AND dependency.deptype = 'n'
           ) = 1
       )
    FROM pg_catalog.pg_proc AS procedure_record
    JOIN pg_catalog.pg_namespace AS namespace
      ON namespace.oid = procedure_record.pronamespace
    JOIN pg_catalog.pg_roles AS owner
      ON owner.oid = procedure_record.proowner
    JOIN pg_catalog.pg_language AS language_record
      ON language_record.oid = procedure_record.prolang
    JOIN pg_catalog.pg_type AS return_type
      ON return_type.oid = procedure_record.prorettype
    JOIN pg_catalog.pg_namespace AS return_namespace
      ON return_namespace.oid = return_type.typnamespace
    WHERE namespace.nspname = 'public'
      AND procedure_record.proname = 'verify_fase09_7_public_access_closure'
) AND public.verify_fase09_7_public_access_closure() IS TRUE"""
RETIREMENT_VERIFIER_SOURCE_SHA256 = (
    "38172c8a98884d317567e4a9814f7b8c340dfd0df9f5d2b2f39ae89e8e34e618"
)
RETIREMENT_VERIFIER_ATTESTATION = f"""(
    SELECT pg_catalog.count(*) = 1
       AND pg_catalog.bool_and(
           owner.rolname = 'postgres'
           AND language_record.lanname = 'sql'
           AND return_namespace.nspname = 'pg_catalog'
           AND return_type.typname = 'bool'
           AND procedure_record.prokind = 'f'
           AND NOT procedure_record.prosecdef
           AND procedure_record.provolatile = 's'
           AND NOT procedure_record.proisstrict
           AND NOT procedure_record.proleakproof
           AND procedure_record.proparallel = 'u'
           AND NOT procedure_record.proretset
           AND procedure_record.pronargs = 0
           AND procedure_record.pronargdefaults = 0
           AND procedure_record.proconfig IS NOT DISTINCT FROM
               ARRAY['search_path=""']::text[]
           AND pg_catalog.octet_length(pg_catalog.replace(
               procedure_record.prosrc, E'\\r\\n', E'\\n'
            )) = 7059
           AND pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
               pg_catalog.replace(procedure_record.prosrc, E'\\r\\n', E'\\n'),
               'UTF8'
           )), 'hex') = '{RETIREMENT_VERIFIER_SOURCE_SHA256}'
           AND (
               SELECT pg_catalog.count(*)
               FROM pg_catalog.aclexplode(COALESCE(
                   procedure_record.proacl,
                   pg_catalog.acldefault('f', procedure_record.proowner)
               )) AS acl
           ) = 2
           AND (
               SELECT pg_catalog.count(*)
               FROM pg_catalog.aclexplode(COALESCE(
                   procedure_record.proacl,
                   pg_catalog.acldefault('f', procedure_record.proowner)
               )) AS acl
               WHERE acl.privilege_type = 'EXECUTE'
                 AND NOT acl.is_grantable
                 AND acl.grantee = procedure_record.proowner
           ) = 1
           AND (
               SELECT pg_catalog.count(*)
               FROM pg_catalog.aclexplode(COALESCE(
                   procedure_record.proacl,
                   pg_catalog.acldefault('f', procedure_record.proowner)
               )) AS acl
               WHERE acl.privilege_type = 'EXECUTE'
                 AND NOT acl.is_grantable
                 AND acl.grantee = (
                     SELECT role.oid
                     FROM pg_catalog.pg_roles AS role
                     WHERE role.rolname = 'service_role'
                 )
           ) = 1
           AND (
               SELECT pg_catalog.count(*)
               FROM pg_catalog.pg_depend AS dependency
               WHERE dependency.classid =
                     'pg_catalog.pg_proc'::pg_catalog.regclass
                 AND dependency.objid = procedure_record.oid
                 AND dependency.objsubid = 0
           ) = 1
           AND (
               SELECT pg_catalog.count(*)
               FROM pg_catalog.pg_depend AS dependency
               WHERE dependency.classid =
                     'pg_catalog.pg_proc'::pg_catalog.regclass
                 AND dependency.objid = procedure_record.oid
                 AND dependency.objsubid = 0
                 AND dependency.refclassid =
                     'pg_catalog.pg_namespace'::pg_catalog.regclass
                 AND dependency.refobjid = procedure_record.pronamespace
                 AND dependency.refobjsubid = 0
                 AND dependency.deptype = 'n'
           ) = 1
       )
    FROM pg_catalog.pg_proc AS procedure_record
    JOIN pg_catalog.pg_namespace AS namespace
      ON namespace.oid = procedure_record.pronamespace
    JOIN pg_catalog.pg_roles AS owner
      ON owner.oid = procedure_record.proowner
    JOIN pg_catalog.pg_language AS language_record
      ON language_record.oid = procedure_record.prolang
    JOIN pg_catalog.pg_type AS return_type
      ON return_type.oid = procedure_record.prorettype
    JOIN pg_catalog.pg_namespace AS return_namespace
      ON return_namespace.oid = return_type.typnamespace
    WHERE namespace.nspname = 'public'
      AND procedure_record.proname =
          'verify_fase09_7_notify_new_lead_retirement'
) AND public.verify_fase09_7_notify_new_lead_retirement() IS TRUE"""
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


@dataclass(frozen=True)
class ManifestPlan:
    boundary: int
    exact_prefix: tuple[tuple[str, str], ...]
    pending_paths: tuple[Path, ...]


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
        raise ManifestError("F9.7 manifest does not match exact schema-v3 digest")
    if (
        manifest.get("schema_version") != 3
        or manifest.get("phase") != "F9.7"
        or manifest.get("package_id") != PACKAGE_ID
        or manifest.get("status") != "reconciled_not_certified"
        or manifest.get("blocked_targets") != ["free", "pro"]
    ):
        raise ManifestError("F9.7 manifest metadata drift")
    entries = manifest.get("entries")
    if not isinstance(entries, list) or len(entries) != 6:
        raise ManifestError("F9.7 manifest must contain exactly six entries")
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
) -> ManifestPlan:
    plan = classify_manifest_ledger(migration_files, applied)
    for path in migration_files[:plan.boundary]:
        signature = POSTCONDITIONS[path.stem]
        name = signature.removeprefix("public.").removesuffix("()")
        if not database.rpc_raise(name, {}):
            raise RuntimeError(f"Postcondicion fallida: {path.stem}")
        if (
            path.stem == PUBLIC_ACCESS_STEM
            and not database.scalar_bool(PUBLIC_ACCESS_VERIFIER_ATTESTATION)
        ):
            raise RuntimeError(f"Postcondicion externa fallida: {path.stem}")
        if (
            path.stem == RETIREMENT_STEM
            and not database.scalar_bool(RETIREMENT_VERIFIER_ATTESTATION)
        ):
            raise RuntimeError(f"Postcondicion externa fallida: {path.stem}")
    return plan


def classify_manifest_ledger(
    migration_files: Sequence[Path],
    applied: Mapping[str, str],
) -> ManifestPlan:
    blocked = sorted(
        set(applied).intersection(
            {F9_7_V2_RETIREMENT_STEM, *F9_5_HISTORICAL_NON_PROMOTABLE_STEMS}
        )
    )
    if blocked:
        raise RuntimeError(
            "F9.7 ledger contains non-promotable historical stem(s): "
            + ", ".join(blocked)
        )
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
        raise RuntimeError("F9.7 only accepts ledger boundaries 0, 3, 4, 5, or 6")
    return ManifestPlan(
        boundary=prefix_size,
        exact_prefix=tuple((path.stem, projected[path.stem]) for path in migration_files[:prefix_size]),
        pending_paths=tuple(migration_files[prefix_size:]),
    )


def _manifest_revalidation_sql(plan: ManifestPlan) -> str:
    expected_rows = []
    for ordinal, (stem, marker) in enumerate(plan.exact_prefix, start=1):
        expected_rows.append(f"({ordinal}, '{stem}', '{marker}')")
    for ordinal, path in enumerate(plan.pending_paths, start=len(plan.exact_prefix) + 1):
        expected_rows.append(f"({ordinal}, '{path.stem}', '{_marker(path)}')")
    expected_values = ",\n        ".join(expected_rows)
    blocked_names = "', '".join(
        [F9_7_V2_RETIREMENT_STEM, *sorted(F9_5_HISTORICAL_NON_PROMOTABLE_STEMS)]
    )
    return f"""DO $manifest_ledger_revalidate$
DECLARE
    ledger_record record;
BEGIN
    IF EXISTS (
        SELECT 1
        FROM public.supabase_migrations AS migration
        WHERE migration.name IN ('{blocked_names}')
    ) THEN
        RAISE EXCEPTION 'F9.7 ledger contains non-promotable historical stem';
    END IF;

    WITH expected_ledger(ordinal, migration_name, checksum_marker) AS (
        VALUES
        {expected_values}
    ),
    expected_with_state AS (
        SELECT
            expected.ordinal,
            expected.migration_name,
            expected.checksum_marker,
            ledger.name IS NOT NULL AS is_present,
            ledger.statements IS NOT DISTINCT FROM expected.checksum_marker AS is_exact,
            COALESCE(ledger.match_count, 0) AS match_count
        FROM expected_ledger AS expected
        LEFT JOIN (
            SELECT name, statements, pg_catalog.count(*) AS match_count
            FROM public.supabase_migrations
            GROUP BY name, statements
        ) AS ledger
          ON ledger.name = expected.migration_name
    ),
    ledger_summary AS (
        SELECT
            pg_catalog.count(*) FILTER (WHERE ordinal <= {plan.boundary} AND is_exact)::integer AS exact_prefix_count,
            pg_catalog.count(*) FILTER (WHERE ordinal <= {plan.boundary} AND NOT is_exact)::integer AS prefix_drift_count,
            pg_catalog.count(*) FILTER (WHERE ordinal > {plan.boundary} AND is_present)::integer AS suffix_present_count,
            pg_catalog.count(*) FILTER (WHERE is_present AND NOT is_exact)::integer AS checksum_drift_count,
            pg_catalog.count(*) FILTER (WHERE match_count > 1)::integer AS duplicate_count
        FROM expected_with_state
    )
    SELECT * INTO ledger_record FROM ledger_summary;

    IF ledger_record.exact_prefix_count <> {plan.boundary}
       OR ledger_record.prefix_drift_count <> 0
       OR ledger_record.suffix_present_count <> 0
       OR ledger_record.checksum_drift_count <> 0
       OR ledger_record.duplicate_count <> 0 THEN
        RAISE EXCEPTION 'Manifest prefix drift';
    END IF;
END;
$manifest_ledger_revalidate$;"""


def build_manifest_migration_sql(plan: ManifestPlan) -> str:
    lines = [
        "SET lock_timeout = '5s';",
        "SET statement_timeout = '60s';",
        "LOCK TABLE public.supabase_migrations IN SHARE ROW EXCLUSIVE MODE;",
        _manifest_revalidation_sql(plan),
        "-- manifest-prefix-guard",
    ]
    for stem, marker in plan.exact_prefix:
        if stem not in POSTCONDITIONS:
            raise RuntimeError(f"unknown manifest prefix verifier: {stem}")
        lines.extend([
            "DO $manifest_prefix$", "BEGIN", "    IF NOT EXISTS (",
            "        SELECT 1 FROM public.supabase_migrations",
            f"        WHERE name = '{stem}' AND statements = '{marker}'",
            "    ) THEN RAISE EXCEPTION 'Manifest prefix drift'; END IF;",
            "END;", "$manifest_prefix$;",
        ])
        signature = POSTCONDITIONS[stem]
        lines.extend([
            "DO $manifest_prefix_verify$", "BEGIN",
            f"    IF {signature} IS NOT TRUE THEN",
            f"        RAISE EXCEPTION 'Postcondicion de prefijo fallida: {stem}';",
            "    END IF;", "END;", "$manifest_prefix_verify$;",
        ])
        if stem == PUBLIC_ACCESS_STEM:
            lines.extend([
                "DO $manifest_prefix_external_verify$", "BEGIN",
                f"    IF ({PUBLIC_ACCESS_VERIFIER_ATTESTATION}) IS NOT TRUE THEN",
                f"        RAISE EXCEPTION 'Postcondicion externa de prefijo fallida: {stem}';",
                "    END IF;", "END;", "$manifest_prefix_external_verify$;",
            ])
        if stem == RETIREMENT_STEM:
            lines.extend([
                "DO $manifest_prefix_external_verify$", "BEGIN",
                f"    IF ({RETIREMENT_VERIFIER_ATTESTATION}) IS NOT TRUE THEN",
                f"        RAISE EXCEPTION 'Postcondicion externa de prefijo fallida: {stem}';",
                "    END IF;", "END;", "$manifest_prefix_external_verify$;",
            ])
    for path in plan.pending_paths:
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
    for path in plan.pending_paths:
        signature = POSTCONDITIONS[path.stem]
        lines.extend([
            "DO $manifest_verify$", "BEGIN",
            f"    IF {signature} IS NOT TRUE THEN",
            f"        RAISE EXCEPTION 'Postcondicion fallida: {path.stem}';",
            "    END IF;", "END;", "$manifest_verify$;",
        ])
        if path.stem == PUBLIC_ACCESS_STEM:
            lines.extend([
                "DO $manifest_external_verify$", "BEGIN",
                f"    IF ({PUBLIC_ACCESS_VERIFIER_ATTESTATION}) IS NOT TRUE THEN",
                f"        RAISE EXCEPTION 'Postcondicion externa fallida: {path.stem}';",
                "    END IF;", "END;", "$manifest_external_verify$;",
            ])
        if path.stem == RETIREMENT_STEM:
            lines.extend([
                "DO $manifest_external_verify$", "BEGIN",
                f"    IF ({RETIREMENT_VERIFIER_ATTESTATION}) IS NOT TRUE THEN",
                f"        RAISE EXCEPTION 'Postcondicion externa fallida: {path.stem}';",
                "    END IF;", "END;", "$manifest_external_verify$;",
            ])
    return "\n".join(lines)


def build_manifest_ledger_sql(plan: ManifestPlan, *, version: int) -> str:
    lines = ["-- manifest-ledger-registration"]
    for offset, path in enumerate(plan.pending_paths):
        lines.append(
            "INSERT INTO public.supabase_migrations "
            "(version, name, statements, applied_at) VALUES "
            f"({version + offset}, '{path.stem}', '{_marker(path)}', "
            "pg_catalog.clock_timestamp());"
        )
    return "\n".join(lines)


def build_manifest_package_sql(plan: ManifestPlan, *, version: int) -> str:
    if not isinstance(plan, ManifestPlan):
        raise TypeError("F9.7 package generation requires a validated ManifestPlan")
    if not plan.pending_paths:
        raise RuntimeError("cannot build a zero-pending package")
    return "\n".join([
        build_manifest_migration_sql(plan),
        build_manifest_ledger_sql(plan, version=version),
        "",
    ])
