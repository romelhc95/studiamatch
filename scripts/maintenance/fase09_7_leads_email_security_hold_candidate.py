"""Local-only planner for the F9.7 terminal leads/email security hold."""

from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

try:
    from scripts.maintenance import fase09_7_candidate as v3_candidate
except ModuleNotFoundError:  # pragma: no cover - used when db_migrate.py is run directly.
    from maintenance import fase09_7_candidate as v3_candidate


ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ID = "F9.7-LEADS-EMAIL-SECURITY-HOLD-20260729"
MANIFEST_SHA256 = "3248376c2d92e953907590d158702a07f0b5523f7559ae4a0f85809b4aff4ebb"
HOLD_STEM = "20260729_fase09_7_leads_email_security_hold"
HOLD_ENTRY = {
    "id": "F9.7-LEADS-EMAIL-SECURITY-HOLD",
    "component": "leads_email_security_hold",
    "path": "db/migrations/20260729_fase09_7_leads_email_security_hold.sql",
    "sha256": "29082d96cbfd746753324aef0330a7af6f34b0e8bcfa2db0841ac0a8af90134e",
    "provenance": "new_forward_only_terminal_hold",
    "targets": ["free", "pro"],
}
ALLOWED_BOUNDARIES = {6, 7}
F9_5_HISTORICAL_NON_PROMOTABLE_STEMS = v3_candidate.F9_5_HISTORICAL_NON_PROMOTABLE_STEMS
F9_7_V2_RETIREMENT_STEM = v3_candidate.F9_7_V2_RETIREMENT_STEM
F9_7_ALLOWED_STEMS = frozenset(
    {
        v3_candidate.PUBLIC_ACCESS_STEM,
        v3_candidate.RETIREMENT_STEM,
        HOLD_STEM,
    }
)
F9_7_LEDGER_PREFIXES = (
    "20260727_fase09_7_",
    "20260728_fase09_7_",
    "20260729_fase09_7_",
)
TERMINAL_VERIFIER_SOURCE_SHA256 = "ceb80ae8865cf522b0cf2354c856f13c8c32156e38b492fdc55a223f44b51ab2"
TERMINAL_VERIFIER_SOURCE_OCTETS = 47721


class SecurityHoldManifestError(ValueError):
    pass


@dataclass(frozen=True)
class SecurityHoldPlan:
    boundary: int
    v3_prefix: tuple[tuple[str, str], ...]
    hold_entry: tuple[str, str]
    pending_path: Path | None
    replay_only: bool


def canonical_sql_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def canonical_json_sha256(value: object) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _marker(path: Path) -> str:
    return f"sha256:{canonical_sql_sha256(path)}"


def _sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def load_security_hold_manifest(
    manifest_path: Path,
    target: str = "free",
    *,
    root: Path = ROOT,
) -> tuple[list[Path], Path]:
    if target not in {"free", "pro"}:
        raise SecurityHoldManifestError(f"unsupported target {target}")

    def reject_duplicates(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise SecurityHoldManifestError(f"duplicate manifest key: {key}")
            result[key] = value
        return result

    manifest = json.loads(
        manifest_path.read_text(encoding="utf-8"),
        object_pairs_hook=reject_duplicates,
    )
    if MANIFEST_SHA256 != "TO_BE_FILLED" and not hmac.compare_digest(
        canonical_json_sha256(manifest), MANIFEST_SHA256
    ):
        raise SecurityHoldManifestError("security hold manifest digest drift")
    if (
        manifest.get("schema_version") != 1
        or manifest.get("phase") != "F9.7"
        or manifest.get("package_id") != PACKAGE_ID
        or manifest.get("status") != "local_candidate_blocked"
        or manifest.get("application_authorized") is not False
        or manifest.get("blocked_targets") != ["free", "pro"]
        or manifest.get("allowed_boundaries") != [6, 7]
        or manifest.get("data_plane_roles")
        != ["anon", "authenticated", "authenticator", "service_role"]
    ):
        raise SecurityHoldManifestError("security hold manifest metadata drift")

    control_plane = manifest.get("control_plane_exception")
    if not isinstance(control_plane, dict) or control_plane != {
        "routine": "public.exec_sql(text)",
        "owner": "postgres",
        "security": "SECURITY DEFINER",
        "search_path": "\"\"",
        "execute_grantees": ["service_role"],
        "purpose": "single privileged manifest package application",
        "residual_backlog": "BK-F9.5-07",
    }:
        raise SecurityHoldManifestError("security hold exec_sql exception drift")
    if manifest.get("residuals") != ["BK-F9.5-07"]:
        raise SecurityHoldManifestError("security hold residual backlog drift")

    dependencies = manifest.get("depends_on")
    if not isinstance(dependencies, dict):
        raise SecurityHoldManifestError("security hold dependency block is required")
    if (
        dependencies.get("manifest") != "db/manifests/fase09_7_free_schema_rls_v3.json"
        or dependencies.get("package_id") != v3_candidate.PACKAGE_ID
        or dependencies.get("manifest_sha256") != v3_candidate.MANIFEST_SHA256
    ):
        raise SecurityHoldManifestError("security hold v3 dependency drift")
    dependency_entries = dependencies.get("entries")
    if not isinstance(dependency_entries, list) or len(dependency_entries) != 6:
        raise SecurityHoldManifestError("security hold requires six exact v3 entries")

    v3_paths = v3_candidate.load_manifest(
        root / "db/manifests/fase09_7_free_schema_rls_v3.json",
        target,
        root=root,
    )
    expected_dependency = [
        {"path": str(path.relative_to(root)).replace("\\", "/"), "sha256": canonical_sql_sha256(path)}
        for path in v3_paths
    ]
    if dependency_entries != expected_dependency:
        raise SecurityHoldManifestError("security hold v3 entry digest drift")

    entries = manifest.get("entries")
    if entries != [HOLD_ENTRY]:
        raise SecurityHoldManifestError("security hold must contain exactly one entry")
    hold_path = (root / HOLD_ENTRY["path"]).resolve()
    if root.resolve() not in hold_path.parents:
        raise SecurityHoldManifestError("security hold path escapes repository root")
    if canonical_sql_sha256(hold_path) != HOLD_ENTRY["sha256"]:
        raise SecurityHoldManifestError("security hold SQL checksum drift")
    sql = hold_path.read_text(encoding="utf-8")
    if "CASCADE" in sql.upper():
        raise SecurityHoldManifestError("security hold SQL must not use CASCADE")
    if "ON CONFLICT" in sql.upper():
        raise SecurityHoldManifestError("security hold SQL must not write idempotent ledger")
    return v3_paths, hold_path


def classify_security_hold_ledger(
    v3_paths: Sequence[Path],
    hold_path: Path,
    applied: Mapping[str, str],
) -> SecurityHoldPlan:
    blocked = sorted(
        set(applied).intersection(
            {F9_7_V2_RETIREMENT_STEM, *F9_5_HISTORICAL_NON_PROMOTABLE_STEMS}
        )
    )
    if blocked:
        raise RuntimeError(
            "F9.7 security hold ledger contains non-promotable stem(s): "
            + ", ".join(blocked)
        )
    expected_v3 = tuple((path.stem, _marker(path)) for path in v3_paths)
    for stem, marker in expected_v3:
        actual = applied.get(stem)
        if actual is None:
            raise RuntimeError("security hold requires exact v3 boundary 6")
        if not hmac.compare_digest(actual, marker):
            raise RuntimeError(f"Ledger/checksum mismatch: {stem}")
    expected_hold = (hold_path.stem, _marker(hold_path))
    hold_actual = applied.get(hold_path.stem)
    if hold_actual is None:
        boundary = 6
        pending_path: Path | None = hold_path
        replay_only = False
    elif hmac.compare_digest(hold_actual, expected_hold[1]):
        boundary = 7
        pending_path = None
        replay_only = True
    else:
        raise RuntimeError(f"Ledger/checksum mismatch: {hold_path.stem}")
    known_stems = {stem for stem, _ in expected_v3} | {hold_path.stem}
    unexpected_f97 = sorted(
        stem
        for stem in applied
        if stem.startswith(F9_7_LEDGER_PREFIXES) and stem not in known_stems
    )
    if unexpected_f97:
        raise RuntimeError("security hold ledger contains unknown F9.7 terminal stem")
    if boundary not in ALLOWED_BOUNDARIES:
        raise RuntimeError("security hold only accepts ledger boundaries 6 or 7")
    return SecurityHoldPlan(
        boundary=boundary,
        v3_prefix=expected_v3,
        hold_entry=expected_hold,
        pending_path=pending_path,
        replay_only=replay_only,
    )


def _v3_prefix_sql(plan: SecurityHoldPlan) -> str:
    rows = ",\n        ".join(
        f"({_sql_literal(stem)}, {_sql_literal(marker)})" for stem, marker in plan.v3_prefix
    )
    return f"""DO $security_hold_v3_prefix$
DECLARE
    exact_count integer;
BEGIN
    WITH expected(name, marker) AS (
        VALUES
        {rows}
    )
    SELECT pg_catalog.count(*)::integer
    INTO exact_count
    FROM expected
    JOIN public.supabase_migrations AS ledger
      ON ledger.name = expected.name
     AND ledger.statements = expected.marker;
    IF exact_count <> 6 THEN
        RAISE EXCEPTION 'security hold v3 prefix drift';
    END IF;
    IF EXISTS (
        SELECT 1
        FROM public.supabase_migrations AS ledger
        WHERE ledger.name IN (
            '20260726_fase09_5_rls_canary_reconciliation',
            '20260726_fase09_5_policy_inventory_reconciliation',
            '20260727_fase09_7_notify_new_lead_retirement'
        )
        OR (
            ledger.name LIKE ANY (ARRAY[
                '20260727_fase09_7_%',
                '20260728_fase09_7_%',
                '20260729_fase09_7_%'
            ])
            AND ledger.name NOT IN (
                '20260727_fase09_7_public_access_closure',
                '20260728_fase09_7_notify_new_lead_retirement_v3',
                '20260729_fase09_7_leads_email_security_hold'
            )
        )
    ) THEN
        RAISE EXCEPTION 'security hold ledger contamination';
    END IF;
END;
$security_hold_v3_prefix$;"""


def _terminal_verifier_sql() -> str:
    source_check = "TRUE"
    if TERMINAL_VERIFIER_SOURCE_SHA256 != "TO_BE_FILLED":
        source_check = (
            "pg_catalog.octet_length(pg_catalog.replace(procedure_record.prosrc, "
            "E'\\r\\n', E'\\n')) = "
            f"{TERMINAL_VERIFIER_SOURCE_OCTETS} AND "
            "pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to("
            "pg_catalog.replace(procedure_record.prosrc, E'\\r\\n', E'\\n'), "
            "'UTF8')), 'hex') = "
            f"{_sql_literal(TERMINAL_VERIFIER_SOURCE_SHA256)}"
        )
    return f"""DO $security_hold_terminal_verify$
BEGIN
    IF NOT (
        SELECT pg_catalog.count(*) = 1
           AND pg_catalog.bool_and(
               owner.rolname = 'postgres'
               AND language_record.lanname = 'plpgsql'
               AND return_namespace.nspname = 'pg_catalog'
               AND return_type.typname = 'bool'
               AND procedure_record.prorettype = 'pg_catalog.bool'::pg_catalog.regtype
               AND procedure_record.prokind = 'f'
               AND procedure_record.pronargs = 0
               AND NOT procedure_record.prosecdef
               AND procedure_record.provolatile = 's'
               AND procedure_record.proconfig IS NOT DISTINCT FROM
                   ARRAY['search_path=""']::text[]
               AND {source_check}
                AND NOT pg_catalog.has_function_privilege('anon', procedure_record.oid, 'EXECUTE')
                 AND NOT pg_catalog.has_function_privilege('authenticated', procedure_record.oid, 'EXECUTE')
                 AND NOT pg_catalog.has_function_privilege('authenticator', procedure_record.oid, 'EXECUTE')
                 AND pg_catalog.has_function_privilege('service_role', procedure_record.oid, 'EXECUTE')
            )
        FROM pg_catalog.pg_proc AS procedure_record
        JOIN pg_catalog.pg_namespace AS namespace
          ON namespace.oid = procedure_record.pronamespace
        JOIN pg_catalog.pg_roles AS owner ON owner.oid = procedure_record.proowner
        JOIN pg_catalog.pg_language AS language_record
          ON language_record.oid = procedure_record.prolang
        JOIN pg_catalog.pg_type AS return_type
          ON return_type.oid = procedure_record.prorettype
        JOIN pg_catalog.pg_namespace AS return_namespace
          ON return_namespace.oid = return_type.typnamespace
        WHERE namespace.nspname = 'public'
          AND procedure_record.proname = 'verify_fase09_7_leads_email_security_hold'
    ) THEN
        RAISE EXCEPTION 'security hold verifier identity drift';
    END IF;
    IF NOT (
        SELECT pg_catalog.count(*) = 1
           AND pg_catalog.bool_and(
                owner.rolname = 'postgres'
                AND language_record.lanname = 'plpgsql'
                AND return_namespace.nspname = 'pg_catalog'
                AND return_type.typname = 'jsonb'
                AND procedure_record.prokind = 'f'
                AND procedure_record.prosecdef
                AND procedure_record.pronargs = 1
                AND procedure_record.proconfig IS NOT DISTINCT FROM
                    ARRAY['search_path=""']::text[]
                AND NOT pg_catalog.has_function_privilege('anon', procedure_record.oid, 'EXECUTE')
                AND NOT pg_catalog.has_function_privilege('authenticated', procedure_record.oid, 'EXECUTE')
                AND NOT pg_catalog.has_function_privilege('authenticator', procedure_record.oid, 'EXECUTE')
                AND pg_catalog.has_function_privilege('service_role', procedure_record.oid, 'EXECUTE')
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
           )
        FROM pg_catalog.pg_proc AS procedure_record
        JOIN pg_catalog.pg_namespace AS namespace
          ON namespace.oid = procedure_record.pronamespace
        JOIN pg_catalog.pg_roles AS owner ON owner.oid = procedure_record.proowner
        JOIN pg_catalog.pg_language AS language_record
          ON language_record.oid = procedure_record.prolang
        JOIN pg_catalog.pg_type AS return_type
          ON return_type.oid = procedure_record.prorettype
        JOIN pg_catalog.pg_namespace AS return_namespace
          ON return_namespace.oid = return_type.typnamespace
        WHERE namespace.nspname = 'public'
          AND procedure_record.oid = pg_catalog.to_regprocedure('public.exec_sql(text)')
    ) THEN
        RAISE EXCEPTION 'security hold exec_sql identity drift';
    END IF;
    IF public.verify_fase09_7_leads_email_security_hold() IS NOT TRUE THEN
        RAISE EXCEPTION 'security hold verifier failed';
    END IF;
END;
$security_hold_terminal_verify$;"""


def build_security_hold_package_sql(plan: SecurityHoldPlan, *, version: int) -> str:
    if not isinstance(plan, SecurityHoldPlan):
        raise TypeError("security hold package generation requires SecurityHoldPlan")
    base_header = [
        "SET lock_timeout = '5s';",
        "SET statement_timeout = '60s';",
        "SET search_path = '';",
    ]
    locked_header = base_header + [
        "LOCK TABLE public.supabase_migrations IN SHARE ROW EXCLUSIVE MODE;",
        _v3_prefix_sql(plan),
    ]
    if plan.replay_only:
        stem, marker = plan.hold_entry
        return "\n".join(
            base_header
            + [
                "LOCK TABLE public.supabase_migrations IN SHARE ROW EXCLUSIVE MODE;",
                "LOCK TABLE public.leads IN ACCESS EXCLUSIVE MODE;",
                "LOCK TABLE public.email_log IN ACCESS EXCLUSIVE MODE;",
                _v3_prefix_sql(plan),
                "DO $security_hold_replay$ BEGIN",
                "    IF NOT EXISTS (",
                "        SELECT 1 FROM public.supabase_migrations",
                f"        WHERE name = {_sql_literal(stem)} AND statements = {_sql_literal(marker)}",
                "    ) THEN RAISE EXCEPTION 'security hold replay ledger drift'; END IF;",
                "END;",
                "$security_hold_replay$;",
                _terminal_verifier_sql(),
                "",
            ]
        )
    if plan.pending_path is None:
        raise RuntimeError("security hold boundary 6 requires the terminal migration")
    stem, marker = plan.hold_entry
    sql = plan.pending_path.read_text(encoding="utf-8")
    return "\n".join(
        locked_header
        + [
            "DO $security_hold_pending$ BEGIN",
            "    IF EXISTS (",
            "        SELECT 1 FROM public.supabase_migrations",
            f"        WHERE name = {_sql_literal(stem)}",
            "    ) THEN RAISE EXCEPTION 'security hold pending entry drift'; END IF;",
            "END;",
            "$security_hold_pending$;",
            f"-- manifest-entry {stem}",
            sql,
            _terminal_verifier_sql(),
            "-- security-hold-stage-terminal-verification-complete",
            "-- security-hold-stage-before-ledger",
            "-- manifest-ledger-registration",
            "INSERT INTO public.supabase_migrations ",
            "(version, name, statements, applied_at) VALUES ",
            f"({version}, {_sql_literal(stem)}, {_sql_literal(marker)}, pg_catalog.clock_timestamp());",
            "-- security-hold-stage-after-ledger",
            "",
        ]
    )
