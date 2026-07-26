"""Declarative fail-closed contract for the F9.5 read-only inventory."""

from __future__ import annotations

import hashlib
import hmac
import json
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from types import MappingProxyType


FATAL_REASONS = frozenset({
    "ambiguous_target",
    "pii_detected",
    "prohibited_tool",
    "write_detected",
})
ALLOWED_TOOLS = frozenset({"get_project_url", "list_migrations", "execute_sql"})
REQUIRED_CHECKS = (
    "target_binding",
    "package",
    "ledger",
    "columns",
    "constraints",
    "indexes",
    "rls",
    "policies",
    "roles",
    "acl",
    "rpc",
    "data_conflicts",
    "backup_gate",
    "writers_gate",
    "h00",
)
H00_COUNTS = MappingProxyType({
    "leads_total": 3,
    "leads_pre_cutoff": 3,
    "leads_post_cutoff": 0,
    "email_log_total": 0,
})
EXPECTED_COUNTS = MappingProxyType({
    "target_binding": 1,
    "package": 6,
    "columns": 13,
    "constraints": 11,
    "indexes": 9,
    "rls": 6,
    "policies": 22,
    "roles": 9,
    "acl": 201,
    "rpc": 2,
    "data_conflicts": 0,
    "backup_gate": 1,
    "writers_gate": 0,
})
LEDGER_PREFIXES = frozenset({0, 3, 4, 5, 6})
_LEDGER_ENTRIES = (
    ("20260724_fase06_g1b_reconciliation", "sha256:d239f7080c709cdccf7227523ff2b89b48f99a57ace376a18bbdaa4d1a4d75df"),
    ("20260724_fase06_hito1_editorial_contract", "sha256:b8badde99ada9de16aae126497304cfa7d02f9f6df89f3e22604965446c1af8a"),
    ("20260725_fase07_g1b_closure", "sha256:9b83b36e0d90be048ccdfdea8fc1c175b8c7d7ac1fe25d7589d4c653f6a1c120"),
    ("20260725_fase08_hito1_functional_closure", "sha256:7e392473e464df07edbcfcd7b8597ead8d7e10a47d990eedcfe6ed6cee70b527"),
    ("20260726_fase09_5_rls_canary_reconciliation", "sha256:4959b3f1ad60e2fe3a6e9a23161dd0467cfc549e10c1262ba8a0bb2aaf4c9a01"),
    ("20260726_fase09_5_policy_inventory_reconciliation", "sha256:76a7c06bcf1b46a513801d0b1843ac081948a34f552e0371136c6ac2ac097822"),
)
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")


def _canonical_digest(value: object) -> str:
    payload = json.dumps(
        value, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


LEDGER_DIGESTS = MappingProxyType({
    size: _canonical_digest(_LEDGER_ENTRIES[:size]) for size in LEDGER_PREFIXES
})


def _aggregate_inventory(select_sql: str) -> str:
    return (
        "WITH inventory AS (" + select_sql + ") "
        "SELECT count(*)::bigint AS count, "
        "encode(pg_catalog.sha256(pg_catalog.convert_to("
        "COALESCE(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(inventory) "
        "ORDER BY pg_catalog.to_jsonb(inventory)::text)::text, '[]'), "
        "'UTF8')), 'hex') AS digest FROM inventory"
    )


_TABLES = (
    "'courses','leads','ratings','reviews',"
    "'institution_site_profiles','institutions'"
)
CHECK_SQL = MappingProxyType({
    "columns": _aggregate_inventory(
        "SELECT table_name, column_name, data_type, is_nullable, column_default "
        "FROM information_schema.columns WHERE table_schema = 'public' AND ("
        "(table_name = 'courses' AND column_name IN ("
        "'publication_status','data_quality_status','missing_fields',"
        "'field_sources','manual_updated_at','is_sponsored',"
        "'sponsorship_priority','sponsorship_label')) OR "
        "(table_name = 'leads' AND column_name = 'lead_source_type') OR "
        "(table_name IN ('ratings','reviews') AND column_name IN ("
        "'moderation_status','moderated_at')))"
    ),
    "constraints": _aggregate_inventory(
        "SELECT relation.relname AS table_name, constraint_record.conname, "
        "constraint_record.contype, constraint_record.convalidated, "
        "pg_catalog.pg_get_constraintdef(constraint_record.oid, true) AS definition "
        "FROM pg_catalog.pg_constraint AS constraint_record "
        "JOIN pg_catalog.pg_class AS relation "
        "ON relation.oid = constraint_record.conrelid "
        "WHERE constraint_record.connamespace = 'public'::regnamespace AND "
        "constraint_record.conname IN ('chk_courses_publication_status',"
        "'chk_courses_data_quality_status','chk_courses_missing_fields_array',"
        "'chk_courses_field_sources_object',"
        "'chk_courses_sponsorship_priority_nonnegative',"
        "'chk_courses_sponsorship_label_length','chk_leads_source_type',"
        "'ratings_moderation_status_check','ratings_course_id_fkey',"
        "'reviews_moderation_status_check','reviews_course_id_fkey')"
    ),
    "indexes": _aggregate_inventory(
        "SELECT tablename, indexname, indexdef FROM pg_catalog.pg_indexes "
        "WHERE schemaname = 'public' AND indexname IN ("
        "'idx_courses_publication_quality','idx_courses_missing_fields_gin',"
        "'idx_courses_sponsored_priority','idx_leads_source_type_created_at',"
        "'ratings_course_nickname_unique','idx_ratings_course_id',"
        "'idx_ratings_moderation_status','idx_reviews_course_id',"
        "'idx_reviews_moderation_status')"
    ),
    "rls": _aggregate_inventory(
        "SELECT relation.relname AS table_name, relation.relrowsecurity, "
        "relation.relforcerowsecurity, owner.rolname AS owner_name "
        "FROM pg_catalog.pg_class AS relation JOIN pg_catalog.pg_roles AS owner "
        "ON owner.oid = relation.relowner WHERE relation.relnamespace = "
        "'public'::regnamespace AND relation.relname IN (" + _TABLES + ")"
    ),
    "policies": _aggregate_inventory(
        "SELECT tablename, policyname, permissive, roles, cmd, qual, with_check "
        "FROM pg_catalog.pg_policies WHERE schemaname = 'public' AND "
        "tablename IN (" + _TABLES + ")"
    ),
    "roles": _aggregate_inventory(
        "SELECT 'role'::text AS kind, role.rolname AS object_name, "
        "pg_catalog.jsonb_build_object('super', role.rolsuper, 'inherit', "
        "role.rolinherit, 'create_role', role.rolcreaterole, 'create_db', "
        "role.rolcreatedb, 'login', role.rolcanlogin, 'replication', "
        "role.rolreplication, 'bypass_rls', role.rolbypassrls)::text AS detail "
        "FROM pg_catalog.pg_roles AS role WHERE role.rolname IN ("
        "'anon','authenticated','authenticator','service_role','canary_runner') "
        "UNION ALL SELECT 'membership', granted.rolname || '->' || member.rolname, "
        "pg_catalog.jsonb_build_object('admin', membership.admin_option, "
        "'inherit', membership.inherit_option, 'set', membership.set_option)::text "
        "FROM pg_catalog.pg_auth_members AS membership "
        "JOIN pg_catalog.pg_roles AS granted ON granted.oid = membership.roleid "
        "JOIN pg_catalog.pg_roles AS member ON member.oid = membership.member "
        "WHERE granted.rolname IN ('anon','authenticated','authenticator',"
        "'service_role','canary_runner') OR member.rolname IN ('anon','authenticated',"
        "'authenticator','service_role','canary_runner')"
    ),
    "acl": _aggregate_inventory(
        "SELECT 'schema_owner'::text AS kind, namespace_record.nspname AS "
        "object_name, owner.rolname AS grantee, 'OWNER'::text AS privilege_type, "
        "false AS is_grantable FROM pg_catalog.pg_namespace AS namespace_record "
        "JOIN pg_catalog.pg_roles AS owner ON owner.oid = namespace_record.nspowner "
        "WHERE namespace_record.nspname = 'public' UNION ALL "
        "SELECT 'schema'::text AS kind, namespace_record.nspname AS object_name, "
        "COALESCE(grantee.rolname, 'PUBLIC') AS grantee, acl.privilege_type, "
        "acl.is_grantable FROM pg_catalog.pg_namespace AS namespace_record "
        "CROSS JOIN LATERAL pg_catalog.aclexplode(COALESCE(namespace_record.nspacl,"
        "pg_catalog.acldefault('n', namespace_record.nspowner))) AS acl "
        "LEFT JOIN pg_catalog.pg_roles AS grantee ON grantee.oid = acl.grantee "
        "WHERE namespace_record.nspname = 'public' UNION ALL "
        "SELECT 'table', relation.relname, COALESCE(grantee.rolname, 'PUBLIC'), "
        "acl.privilege_type, acl.is_grantable FROM pg_catalog.pg_class AS relation "
        "CROSS JOIN LATERAL pg_catalog.aclexplode(COALESCE(relation.relacl,"
        "pg_catalog.acldefault('r', relation.relowner))) AS acl "
        "LEFT JOIN pg_catalog.pg_roles AS grantee ON grantee.oid = acl.grantee "
        "WHERE relation.relnamespace = 'public'::regnamespace AND "
        "relation.relname IN (" + _TABLES + ") UNION ALL "
        "SELECT 'column', relation.relname || '.' || attribute.attname, "
        "COALESCE(grantee.rolname, 'PUBLIC'), acl.privilege_type, acl.is_grantable "
        "FROM pg_catalog.pg_attribute AS attribute JOIN pg_catalog.pg_class AS "
        "relation ON relation.oid = attribute.attrelid CROSS JOIN LATERAL "
        "pg_catalog.aclexplode(attribute.attacl) AS acl LEFT JOIN "
        "pg_catalog.pg_roles AS grantee ON grantee.oid = acl.grantee WHERE "
        "relation.relnamespace = 'public'::regnamespace AND relation.relname IN ("
        + _TABLES + ") UNION ALL SELECT 'function', procedure_record.proname || "
        "'(' || pg_catalog.pg_get_function_identity_arguments(procedure_record.oid)"
        " || ')', COALESCE(grantee.rolname, 'PUBLIC'), acl.privilege_type, "
        "acl.is_grantable FROM pg_catalog.pg_proc AS procedure_record CROSS JOIN "
        "LATERAL pg_catalog.aclexplode(COALESCE(procedure_record.proacl,"
        "pg_catalog.acldefault('f', procedure_record.proowner))) AS acl LEFT JOIN "
        "pg_catalog.pg_roles AS grantee ON grantee.oid = acl.grantee WHERE "
        "procedure_record.pronamespace = 'public'::regnamespace AND "
        "procedure_record.proname IN ('atomic_enrichment_promote',"
        "'verify_fase08_hito1_contract',"
        "'verify_fase09_5_rls_canary_reconciliation')"
    ),
    "rpc": _aggregate_inventory(
        "SELECT procedure_record.proname, "
        "pg_catalog.pg_get_function_identity_arguments(procedure_record.oid) AS "
        "identity_arguments, owner.rolname AS owner_name, language_record.lanname, "
        "procedure_record.prosecdef, procedure_record.provolatile, "
        "procedure_record.proconfig, procedure_record.proacl FROM "
        "pg_catalog.pg_proc AS procedure_record JOIN pg_catalog.pg_roles AS owner "
        "ON owner.oid = procedure_record.proowner JOIN pg_catalog.pg_language AS "
        "language_record ON language_record.oid = procedure_record.prolang WHERE "
        "procedure_record.pronamespace = 'public'::regnamespace AND "
        "procedure_record.proname IN ('atomic_enrichment_promote',"
        "'verify_fase08_hito1_contract',"
        "'verify_fase09_5_rls_canary_reconciliation')"
    ),
    "data_conflicts": (
        "SELECT ((SELECT count(*) FROM public.ratings AS rating LEFT JOIN "
        "public.courses AS course ON course.id = rating.course_id WHERE "
        "rating.course_id IS NULL OR course.id IS NULL) + (SELECT count(*) FROM "
        "public.reviews AS review LEFT JOIN public.courses AS course ON course.id "
        "= review.course_id WHERE review.course_id IS NULL OR course.id IS NULL) "
        "+ (SELECT count(*) FROM (SELECT course_id, user_nickname FROM "
        "public.ratings GROUP BY course_id, user_nickname HAVING count(*) > 1) "
        "AS duplicate_rating) + (SELECT count(*) FROM public.courses WHERE "
        "publication_status NOT IN ('borrador','pendiente_revision','publicado',"
        "'despublicado') OR data_quality_status NOT IN ('pendiente','completo') "
        "OR pg_catalog.jsonb_typeof(missing_fields) <> 'array' OR "
        "pg_catalog.jsonb_typeof(field_sources) <> 'object' OR "
        "sponsorship_priority < 0 OR pg_catalog.char_length(sponsorship_label) > 80) "
        "+ (SELECT count(*) FROM public.leads WHERE lead_source_type NOT IN "
        "('organic','sponsored')) + (SELECT count(*) FROM public.ratings WHERE "
        "moderation_status NOT IN ('pending','approved','rejected')) + (SELECT "
        "count(*) FROM public.reviews WHERE moderation_status NOT IN "
        "('pending','approved','rejected')))::bigint AS count"
    ),
    "backup_gate": (
        "SELECT count(*)::bigint AS count FROM (SELECT 1 WHERE (SELECT count(*) "
        "FROM pg_catalog.pg_class AS relation WHERE relation.relnamespace = "
        "'public'::regnamespace AND relation.relkind IN ('r','p') AND "
        "relation.relname IN (" + _TABLES + ")) = 6 AND "
        "pg_catalog.has_schema_privilege(CURRENT_USER, 'public', 'USAGE') AND "
        "NOT EXISTS (SELECT 1 FROM pg_catalog.unnest(ARRAY[" + _TABLES + "]::text[]) "
        "AS required_table(table_name) WHERE NOT pg_catalog.has_table_privilege("
        "CURRENT_USER, 'public.' || required_table.table_name, 'SELECT'))) AS feasible"
    ),
    "writers_gate": (
        "SELECT count(*)::bigint AS count FROM pg_catalog.pg_stat_activity WHERE "
        "datname = pg_catalog.current_database() AND pid <> "
        "pg_catalog.pg_backend_pid() AND state IS DISTINCT FROM 'idle' AND "
        "backend_type = 'client backend'"
    ),
    "h00": (
        "SELECT count(*)::bigint AS leads_total, count(*) FILTER (WHERE "
        "created_at < '2026-07-19T00:00:00Z'::timestamptz)::bigint AS "
        "leads_pre_cutoff, count(*) FILTER (WHERE created_at >= "
        "'2026-07-19T00:00:00Z'::timestamptz)::bigint AS leads_post_cutoff, "
        "(SELECT count(*)::bigint FROM public.email_log) AS email_log_total "
        "FROM public.leads"
    ),
})
CHECK_TOOLS = MappingProxyType({
    "target_binding": "get_project_url",
    "package": "list_migrations",
    "ledger": "list_migrations",
    **{
        name: "execute_sql"
        for name in REQUIRED_CHECKS
        if name not in {"target_binding", "package", "ledger"}
    },
})

# These values bind the aggregate catalog rows reconstructed by the synthetic
# observed-Free fixture.
EXPECTED_DIGESTS = MappingProxyType({
    "package": "575f2e21f747b6445911a050c9951ad93372bcb616282b275838ea21e7cf5795",
    "columns": "6cc6bbb290c2c3d0bffba6e4efc28f52ce101d11c9f9b9b87ca52d59b878bf03",
    "constraints": "afe9f209a8e8a63701f383baee09219e213e948e434a304eeaef30e4c45d381d",
    "indexes": "9a7ba78087a79cefe3565b1640a04f0bf37fb11ddf4e62f66e181e73ff7f5e53",
    "rls": "94983a147e03979527dab1a5c7b10a4b0790f78e1910d24f9e184046482061db",
    "policies": "c6d2ba34f5c313feca9458b7dd39a90da98004856368db77641d7bbd9ec4aaea",
    "roles": "1a7dbbee3be8f39ec25d2f49260c31fce70231d98af39c62a4ca2218fd9d1121",
    "acl": "d9fcb8774383725bd2950ee4c399436fd2ee590aa10a287248582198a5ff9f71",
    "rpc": "06e3b1697d595c3419031a8568343bf0e53d8f176f31563a79cc5c0e92329a16",
})


@dataclass(frozen=True)
class CheckEvidence:
    name: str
    count: int | None = None
    digest: str | None = None
    counts: tuple[tuple[str, int], ...] = ()


@dataclass(frozen=True)
class DirectedCheck:
    name: str
    target: str
    tool: str
    sql: str | None
    evidence: CheckEvidence


class FatalPreflightError(RuntimeError):
    def __init__(self, reason: str):
        if reason not in FATAL_REASONS:
            raise ValueError("unsupported fatal preflight reason")
        super().__init__(reason)
        self.reason = reason


def require_free_target(
    target: str,
    observed_digest: str,
    expected_digest: str,
) -> None:
    if (
        target != "free"
        or not _DIGEST_RE.fullmatch(observed_digest)
        or not _DIGEST_RE.fullmatch(expected_digest)
        or observed_digest == "0" * 64
        or not hmac.compare_digest(observed_digest, expected_digest)
    ):
        raise FatalPreflightError("ambiguous_target")


def require_allowed_tool(check_name: str, tool_name: str) -> None:
    if tool_name not in ALLOWED_TOOLS or CHECK_TOOLS.get(check_name) != tool_name:
        raise FatalPreflightError("prohibited_tool")


def require_read_only_sql(check_name: str, tool_name: str, sql: str | None) -> None:
    expected = CHECK_SQL.get(check_name)
    if tool_name == "execute_sql":
        if expected is None or sql != expected:
            raise FatalPreflightError("write_detected")
    elif sql is not None or expected is not None:
        raise FatalPreflightError("write_detected")


def _valid_count(value: object) -> bool:
    return type(value) is int and value >= 0


def _sanitize(
    evidence: CheckEvidence,
    expected_name: str,
) -> dict[str, object]:
    if evidence.name != expected_name:
        raise FatalPreflightError("pii_detected")
    if expected_name == "target_binding":
        if (
            evidence.count != EXPECTED_COUNTS[expected_name]
            or evidence.digest is None
            or not _DIGEST_RE.fullmatch(evidence.digest)
        ):
            raise FatalPreflightError("pii_detected")
        return {
            "name": evidence.name,
            "status": "PASS",
            "count": evidence.count,
        }
    if expected_name == "h00":
        if evidence.count is not None or evidence.digest is not None:
            raise FatalPreflightError("pii_detected")
        if tuple(H00_COUNTS.items()) != evidence.counts:
            supplied = dict(evidence.counts)
            if (
                len(supplied) != len(evidence.counts)
                or tuple(supplied) != tuple(H00_COUNTS)
                or any(not _valid_count(value) for value in supplied.values())
            ):
                raise FatalPreflightError("pii_detected")
            status = "FAIL"
        else:
            supplied = dict(evidence.counts)
            status = "PASS"
        return {"name": evidence.name, "status": status, "counts": supplied}

    if evidence.counts or not _valid_count(evidence.count):
        raise FatalPreflightError("pii_detected")
    count = evidence.count
    assert count is not None
    if expected_name == "ledger":
        expected_digest = LEDGER_DIGESTS.get(count)
        status = (
            "PASS"
            if count in LEDGER_PREFIXES and evidence.digest == expected_digest
            else "FAIL"
        )
    else:
        expected_count = EXPECTED_COUNTS[expected_name]
        expected_digest = EXPECTED_DIGESTS.get(expected_name)
        if expected_digest is None:
            if evidence.digest is not None:
                raise FatalPreflightError("pii_detected")
            status = "PASS" if count == expected_count else "FAIL"
        else:
            if evidence.digest is None or not _DIGEST_RE.fullmatch(evidence.digest):
                raise FatalPreflightError("pii_detected")
            status = (
                "PASS"
                if count == expected_count
                and hmac.compare_digest(evidence.digest, expected_digest)
                else "FAIL"
            )
    result: dict[str, object] = {
        "name": evidence.name,
        "status": status,
        "count": count,
    }
    if evidence.digest is not None:
        result["digest"] = evidence.digest
    return result


def _contract_is_exact(checks: Sequence[DirectedCheck]) -> bool:
    return tuple(check.name for check in checks) == REQUIRED_CHECKS


def run_directed_inventory(
    checks: Sequence[DirectedCheck],
    expected_target_digest: str,
    emit: Callable[[dict[str, object]], None],
) -> dict[str, object]:
    """Validate the closed declaration and emit exactly one safe result."""

    results: list[dict[str, object]] = []
    fatal_reason: str | None = None
    if not _contract_is_exact(checks):
        outcome: dict[str, object] = {
            "result": "FREE_PREFLIGHT_FAIL",
            "checks": results,
        }
        emit(outcome)
        return outcome

    for check in checks:
        try:
            if check.name == "target_binding":
                require_free_target(
                    check.target,
                    check.evidence.digest or "",
                    expected_target_digest,
                )
            elif check.target != "free":
                raise FatalPreflightError("ambiguous_target")
            require_allowed_tool(check.name, check.tool)
            require_read_only_sql(check.name, check.tool, check.sql)
            results.append(_sanitize(check.evidence, check.name))
        except FatalPreflightError as exc:
            fatal_reason = exc.reason
            break

    outcome = {
        "result": (
            "FREE_PREFLIGHT_FAIL"
            if fatal_reason is not None
            or any(item["status"] == "FAIL" for item in results)
            else "FREE_PREFLIGHT_PASS"
        ),
        "checks": results,
    }
    if fatal_reason is not None:
        outcome["fatal"] = fatal_reason
    emit(outcome)
    return outcome
