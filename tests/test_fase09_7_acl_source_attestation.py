import csv
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
QUERY_PATH = ROOT / "scripts/maintenance/fase09_7_acl_source_attestation.sql"
MANIFEST_PATH = ROOT / "db/manifests/fase09_7_acl_source_attestation.json"
QUERY_SHA256 = "71ff247d9608257ea99777d8f72f7d7db7f8f688601c4d8311c6bc6ee5bd8889"

OUTPUT_SCHEMA = [
    "query_id", "schema_version", "snapshot_claim", "closure_coverage",
    "package_source_coverage", "policy_expression_attested",
    "pg17_semantics_supported", "target_relation_count", "missing_target_count",
    "rls_enabled_count", "owner_mismatch_count", "requested_role_count",
    "role_posture_violation_count", "role_inherit_default_off_count",
    "membership_route_count",
    "inherited_route_count", "set_route_count", "set_then_inherit_route_count",
    "implicit_database_owner_route_count", "membership_depth_truncated_count",
    "admin_option_count", "elevated_role_path_count", "table_acl_source_count",
    "column_acl_source_count", "schema_acl_source_count",
    "direct_acl_source_count", "public_acl_source_count",
    "inherited_acl_source_count", "set_acl_source_count",
    "grant_option_source_count", "unknown_acl_source_count",
    "schema_usage_missing_count", "public_schema_create_count",
    "public_table_capability_count", "public_denied_column_capability_count",
    "public_select_source_count", "leads_missing_insert_column_count",
    "leads_extra_insert_column_count", "service_select_missing_count",
    "service_required_capability_missing_count",
    "policy_count", "managed_preclosure_policy_count", "unmanaged_policy_count",
    "applicable_policy_source_count", "public_select_policy_count",
    "unexpected_policy_count", "owner_access_source_count",
    "public_owner_access_count", "indirect_view_path_count",
    "indirect_rule_path_count", "target_rule_path_count",
    "indirect_security_definer_path_count",
    "indirect_trigger_path_count", "unexpected_trigger_path_count",
    "dynamic_indirect_path_count", "publication_path_count",
    "partition_descendant_count",
    "catalog_comparison_pass", "fail_closed", "requires_supplemental_attestation",
]


def _query_bytes() -> bytes:
    return QUERY_PATH.read_bytes().replace(b"\r\n", b"\n")


def _manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def test_query_is_frozen_single_select_and_catalog_only():
    canonical = _query_bytes()
    assert hashlib.sha256(canonical).hexdigest() == QUERY_SHA256
    sql = canonical.decode("ascii")
    assert sql.startswith("WITH RECURSIVE\n")
    assert sql.endswith(";\n")
    assert sql.count(";") == 1

    without_literals = re.sub(r"'(?:''|[^'])*'", "''", sql)
    assert not re.search(
        r"(?i)\b(?:ALTER|CALL|COPY|CREATE|DELETE|DO|DROP|GRANT|INSERT|LOCK|"
        r"MERGE|REASSIGN|RESET|REVOKE|SET|TRUNCATE|UPDATE|VACUUM)\b",
        without_literals,
    )
    assert not re.search(
        r"(?i)\b(?:dblink|http|net\.|pg_read_file|lo_import|lo_export)\b",
        without_literals,
    )
    assert "public.supabase_migrations" not in sql
    assert not re.search(r"(?i)\b(?:FROM|JOIN)\s+public\.", without_literals)
    assert not re.search(r"(?i)\bpublic\.[a-z_][a-z0-9_]*\s*\(", without_literals)

    ctes = set(re.findall(r"(?m)^([a-z_][a-z0-9_]*)\s*(?:\([^)]*\))?\s+AS\s*\(", sql))
    relation_tokens = re.findall(
        r"(?i)\b(?:FROM|JOIN)\s+([a-z_][a-z0-9_.]*)", without_literals
    )
    for token in relation_tokens:
        assert (
            token.startswith("pg_catalog.")
            or token.lower() in ctes
            or token.lower() == "lateral"
        ), token

    calls = set(re.findall(r"\b([a-z_][a-z0-9_.]*)\s*\(", without_literals))
    special_forms = {"coalesce", "exists", "case", "in", "not"}
    relation_aliases = set(re.findall(
        r"(?i)\bAS\s+([a-z_][a-z0-9_]*)\s*\(", without_literals
    ))
    for call in calls:
        assert (
            call.startswith("pg_catalog.")
            or call.lower() in special_forms
            or call.lower() in ctes
            or call.lower() in relation_aliases
        ), call


def test_fixed_sanitized_output_contract_and_single_use_manifest():
    manifest = _manifest()
    assert manifest["query"]["canonical_sha256"] == QUERY_SHA256
    assert manifest["output_schema"] == OUTPUT_SCHEMA
    scope = manifest["authorization_scope"]
    assert scope == {
        "query_id": "F9.7-ACL-SOURCE-CATALOG-PG17-V1",
        "max_calls": 1,
        "retries": 0,
        "http_calls": 0,
        "statement_count": 1,
        "read_only": True,
        "catalog_only": True,
        "snapshot_claim": "observed_only_not_convergence",
    }
    assert manifest["target"] == "free"
    assert manifest["tool"] == "supabase-free.execute_sql"
    assert "supabase_pro" in manifest["explicitly_prohibited"]
    assert "ledger_read_or_write" in manifest["explicitly_prohibited"]
    assert "business_row_read" in manifest["explicitly_prohibited"]
    assert "any_retry_or_http_attempt" in manifest["stop_conditions"]
    assert manifest["application"] == "forbidden_in_this_contract"
    assert manifest["application_gate"] == (
        "pg17_and_policy_expression_attested_and_closure_coverage_complete_"
        "and_catalog_comparison_pass_and_package_source_coverage_complete_"
        "and_no_supplemental_attestation_required"
    )
    assert manifest["allowed_evidence"] == [
        "fixed_scalar_counts", "fixed_booleans", "closure_coverage_enum",
        "package_source_coverage_enum", "snapshot_claim_enum",
        "git_artifact_digests",
    ]

    sql = _query_bytes().decode("ascii")
    assert "VALUES (128::integer, false)" in sql
    assert "membership_depth_truncated_count > 0 THEN 'unknown'" in sql
    assert "AND (SELECT policy_expression_attested FROM contract_constants)" in sql
    assert "NOT assessment.catalog_comparison_pass" in sql
    assert "assessment.package_source_coverage <> 'complete'" in sql
    assert "OR assessment.supplemental_required" in sql
    final_select = sql.rsplit("\nSELECT\n", 1)[1]
    aliases = re.findall(r"\bAS\s+([a-z_][a-z0-9_]*)", final_select)
    aliases.extend(
        line.strip().rstrip(",")
        for line in final_select.splitlines()
        if re.fullmatch(r"\s*assessment\.[a-z_][a-z0-9_]*,?\s*", line)
    )
    normalized = [item.removeprefix("assessment.") for item in aliases]
    assert len(normalized) == len(OUTPUT_SCHEMA)
    assert set(normalized) == set(OUTPUT_SCHEMA)


def test_security_no_go_guards_are_explicit_and_fail_closed():
    sql = _query_bytes().decode("ascii")
    lowered = sql.lower()
    assert "polqual" not in lowered
    assert "polwithcheck" not in lowered
    assert "pg_get_expr" not in lowered
    assert "path.depth" not in lowered
    assert "depth < 32" not in lowered
    assert "(pg_catalog.to_jsonb(membership) ->> 'inherit_option')" in lowered
    assert "(pg_catalog.to_jsonb(membership) ->> 'set_option')" in lowered
    assert "(pg_catalog.to_jsonb(membership) ->> 'admin_option')" in lowered
    membership_source = lowered.split("membership_edges", 1)[1].split("targets", 1)[0]
    assert "membership.inherit_option" not in membership_source
    assert "membership.set_option" not in membership_source
    assert "membership.admin_option" not in membership_source
    assert "policy_expression_attested) as (\n    values (128::integer, false)" in lowered
    assert lowered.count("current_setting('server_version_num')::integer < 170000") >= 2
    assert lowered.count("current_setting('server_version_num')::integer >= 180000") >= 2
    assert "current_setting('server_version_num')::integer >= 170000" in lowered
    assert "current_setting('server_version_num')::integer < 180000" in lowered
    for required in (
        "pg_catalog.pg_database",
        "pg_catalog.current_database()",
        "membership_depth_truncations",
        "usable_public_schemas",
        "target_rule_paths",
        "pg_catalog.pg_inherits",
        "decision.target_rule_path_count > 0",
        "decision.partition_descendant_count > 0",
    ):
        assert required.lower() in lowered


def _postgres_fixture_sql(query: str) -> str:
    columns = """
        id uuid, first_name text, last_name text, email text, whatsapp text,
        source_page text, type text, course_id uuid, area_interest text,
        budget numeric, modality text, description text,
        is_late_enrollment_request boolean, status text
    """
    deep_views = [
        "CREATE VIEW public.acl_deep_view_000 AS "
        "SELECT email FROM public.leads;"
    ]
    deep_views.extend(
        f"CREATE VIEW public.acl_deep_view_{index:03d} AS "
        f"SELECT email FROM public.acl_deep_view_{index - 1:03d};"
        for index in range(1, 33)
    )
    deep_view_sql = "\n".join(deep_views)
    return f"""
BEGIN;
CREATE ROLE anon NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
CREATE ROLE authenticated NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
CREATE ROLE service_role NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION BYPASSRLS;
CREATE ROLE acl_fixture_inherit NOLOGIN;
CREATE ROLE acl_fixture_set NOLOGIN;
CREATE ROLE acl_fixture_set_child NOLOGIN;
CREATE ROLE acl_fixture_elevated NOLOGIN BYPASSRLS;
GRANT acl_fixture_inherit TO anon WITH ADMIN TRUE, INHERIT TRUE, SET FALSE;
GRANT acl_fixture_set TO authenticated WITH INHERIT FALSE, SET TRUE;
GRANT acl_fixture_set_child TO acl_fixture_set WITH INHERIT TRUE, SET FALSE;
GRANT acl_fixture_elevated TO anon WITH INHERIT FALSE, SET TRUE;
CREATE TABLE public.leads ({columns}) PARTITION BY LIST (status);
CREATE TABLE public.acl_fixture_leads_partition
PARTITION OF public.leads FOR VALUES IN ('fixture');
CREATE TABLE public.email_log (id uuid, recipient_email text, status text);
ALTER TABLE public.leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.email_log ENABLE ROW LEVEL SECURITY;
CREATE POLICY leads_insert_public ON public.leads FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY leads_insert_authenticated ON public.leads FOR INSERT TO authenticated WITH CHECK (true);
CREATE POLICY leads_service_role ON public.leads FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY email_log_service_role ON public.email_log FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY acl_fixture_unmanaged ON public.email_log FOR SELECT TO acl_fixture_inherit USING (true);
GRANT INSERT (first_name,last_name,email,whatsapp,source_page,type,course_id,area_interest,budget,modality,description,is_late_enrollment_request) ON public.leads TO anon, authenticated;
GRANT SELECT ON public.leads, public.email_log TO service_role;
GRANT SELECT ON public.leads TO acl_fixture_inherit;
GRANT SELECT ON public.email_log TO acl_fixture_set, acl_fixture_set_child;
GRANT SELECT ON public.leads TO anon WITH GRANT OPTION;
ALTER TABLE public.email_log OWNER TO service_role;
CREATE VIEW public.acl_fixture_view AS SELECT email FROM public.leads;
GRANT SELECT ON public.acl_fixture_view TO anon;
{deep_view_sql}
GRANT SELECT ON public.acl_deep_view_032 TO anon;
CREATE RULE acl_fixture_target_rule AS ON UPDATE TO public.leads DO INSTEAD NOTHING;
CREATE FUNCTION public.acl_fixture_reader() RETURNS bigint
LANGUAGE sql SECURITY DEFINER SET search_path = ''
BEGIN ATOMIC SELECT count(*) FROM public.email_log; END;
REVOKE ALL ON FUNCTION public.acl_fixture_reader() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.acl_fixture_reader() TO authenticated;
CREATE FUNCTION public.acl_fixture_trigger() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
BEGIN INSERT INTO public.email_log(status) VALUES ('fixture'); RETURN NEW; END;
$$;
REVOKE ALL ON FUNCTION public.acl_fixture_trigger() FROM PUBLIC;
CREATE TRIGGER acl_fixture_trigger AFTER INSERT ON public.leads
FOR EACH ROW EXECUTE FUNCTION public.acl_fixture_trigger();
CREATE FUNCTION public.acl_fixture_dynamic() RETURNS integer
LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
BEGIN EXECUTE 'SELECT 1'; RETURN 1; END;
$$;
CREATE SCHEMA acl_fixture_usable;
GRANT USAGE ON SCHEMA acl_fixture_usable TO anon;
CREATE FUNCTION acl_fixture_usable.acl_fixture_reader() RETURNS bigint
LANGUAGE sql SECURITY DEFINER SET search_path = ''
BEGIN ATOMIC SELECT count(*) FROM public.email_log; END;
CREATE PUBLICATION acl_fixture_publication FOR TABLE public.leads;
{query}
ROLLBACK;
"""


def _repairable_preclosure_fixture_sql(query: str) -> str:
    columns = """
        id uuid, first_name text, last_name text, email text, whatsapp text,
        source_page text, type text, course_id uuid, area_interest text,
        budget numeric, modality text, description text,
        is_late_enrollment_request boolean, status text
    """
    return f"""
BEGIN;
CREATE ROLE anon NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
CREATE ROLE authenticated NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
CREATE ROLE service_role NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION BYPASSRLS;
CREATE TABLE public.leads ({columns});
CREATE TABLE public.email_log (id uuid, recipient_email text, status text);
ALTER TABLE public.leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.email_log ENABLE ROW LEVEL SECURITY;
CREATE POLICY leads_insert_public ON public.leads FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY leads_insert_authenticated ON public.leads FOR INSERT TO authenticated WITH CHECK (true);
CREATE POLICY leads_service_role ON public.leads FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY email_log_service_role ON public.email_log FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY leads_select_public ON public.leads FOR SELECT TO anon USING (true);
CREATE POLICY leads_select_authenticated ON public.leads FOR SELECT TO authenticated USING (true);
CREATE POLICY email_log_select_public ON public.email_log FOR SELECT TO anon USING (true);
CREATE POLICY email_log_select_authenticated ON public.email_log FOR SELECT TO authenticated USING (true);
GRANT ALL ON public.leads TO service_role;
GRANT SELECT ON public.email_log TO service_role;
GRANT SELECT ON public.leads TO anon;
GRANT SELECT ON public.email_log TO PUBLIC;
GRANT INSERT (first_name,status) ON public.leads TO anon, authenticated;
CREATE FUNCTION public.notify_new_lead() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
BEGIN INSERT INTO public.email_log(status) VALUES ('fixture'); RETURN NEW; END;
$$;
REVOKE ALL ON FUNCTION public.notify_new_lead() FROM PUBLIC, anon, authenticated;
CREATE TRIGGER trg_notify_new_lead AFTER INSERT ON public.leads
FOR EACH ROW EXECUTE FUNCTION public.notify_new_lead();
{query}
ROLLBACK;
"""


def _database_owner_fixture_sql(query: str) -> str:
    script = _repairable_preclosure_fixture_sql(query)
    marker = "CREATE ROLE authenticated NOLOGIN"
    owner_change = (
        "SELECT pg_catalog.format('ALTER DATABASE %I OWNER TO anon;', "
        "pg_catalog.current_database()) \\gexec\n"
    )
    return script.replace(marker, owner_change + marker, 1)


def _depth_truncation_fixture_sql(query: str) -> str:
    script = _repairable_preclosure_fixture_sql(query)
    roles = "\n".join(
        f"CREATE ROLE acl_depth_{index:03d} NOLOGIN;" for index in range(129)
    )
    grants = [
        "GRANT acl_depth_000 TO anon WITH INHERIT TRUE, SET FALSE;"
    ]
    grants.extend(
        f"GRANT acl_depth_{index:03d} TO acl_depth_{index - 1:03d} "
        "WITH INHERIT TRUE, SET FALSE;"
        for index in range(1, 129)
    )
    insertion = roles + "\n" + "\n".join(grants) + "\n"
    return script.replace("CREATE TABLE public.leads", insertion + "CREATE TABLE public.leads", 1)


def _run_fixture(script: str) -> dict[str, str]:
    completed = subprocess.run(
        [
            "psql", "-X", "--quiet", "--csv", "--set=ON_ERROR_STOP=1",
            os.environ["TEST_DATABASE_URL"],
        ],
        input=script,
        text=True,
        capture_output=True,
        check=True,
    )
    rows = list(csv.DictReader(io.StringIO(completed.stdout)))
    assert len(rows) == 1
    assert list(rows[0]) == OUTPUT_SCHEMA
    return rows[0]


@pytest.mark.skipif(
    not os.environ.get("TEST_DATABASE_URL") or shutil.which("psql") is None,
    reason="ephemeral PostgreSQL 17 DSN and psql are required",
)
def test_pg17_source_routes_and_indirect_paths_fail_closed_without_identifier_output():
    query = _query_bytes().decode("ascii")
    script = _postgres_fixture_sql(query)
    row = _run_fixture(script)
    assert row["query_id"] == "F9.7-ACL-SOURCE-CATALOG-PG17-V1"
    assert row["snapshot_claim"] == "observed_only_not_convergence"
    assert row["closure_coverage"] == "incomplete"
    assert row["package_source_coverage"] == "incomplete"
    assert int(row["managed_preclosure_policy_count"]) == 4
    assert int(row["unmanaged_policy_count"]) > 0
    assert row["pg17_semantics_supported"] == "t"
    assert row["policy_expression_attested"] == "f"
    for field in (
        "direct_acl_source_count", "inherited_acl_source_count",
        "set_acl_source_count", "set_then_inherit_route_count",
        "grant_option_source_count",
        "owner_access_source_count", "admin_option_count",
        "elevated_role_path_count",
        "indirect_security_definer_path_count",
        "target_rule_path_count", "partition_descendant_count",
        "indirect_trigger_path_count", "unexpected_trigger_path_count",
        "dynamic_indirect_path_count", "publication_path_count",
    ):
        assert int(row[field]) > 0, field
    assert row["catalog_comparison_pass"] == "f"
    assert row["fail_closed"] == "t"
    assert row["requires_supplemental_attestation"] == "t"
    assert int(row["indirect_view_path_count"]) >= 2

    serialized = "|".join(row.values()).lower()
    for forbidden in (
        "acl_fixture_inherit", "acl_fixture_set", "acl_fixture_set_child",
        "acl_fixture_elevated",
        "acl_fixture_view", "acl_fixture_reader", "acl_fixture_trigger",
        "acl_fixture_dynamic", "acl_fixture_publication",
        "acl_fixture_target_rule", "acl_fixture_leads_partition",
        "acl_fixture_usable", "acl_deep_view_032",
    ):
        assert forbidden not in serialized


@pytest.mark.skipif(
    not os.environ.get("TEST_DATABASE_URL") or shutil.which("psql") is None,
    reason="ephemeral PostgreSQL 17 DSN and psql are required",
)
def test_pg17_direct_managed_preclosure_drift_is_package_repairable_but_blocked():
    query = _query_bytes().decode("ascii")
    row = _run_fixture(_repairable_preclosure_fixture_sql(query))
    assert row["closure_coverage"] == "incomplete"
    assert row["package_source_coverage"] == "complete"
    assert row["policy_expression_attested"] == "f"
    assert row["catalog_comparison_pass"] == "f"
    assert row["requires_supplemental_attestation"] == "t"
    assert row["fail_closed"] == "t"
    assert int(row["managed_preclosure_policy_count"]) == 8
    assert int(row["unmanaged_policy_count"]) == 0
    assert int(row["direct_acl_source_count"]) > 0
    assert int(row["public_acl_source_count"]) > 0
    assert int(row["leads_missing_insert_column_count"]) > 0
    assert int(row["leads_extra_insert_column_count"]) > 0
    assert int(row["inherited_acl_source_count"]) == 0
    assert int(row["set_acl_source_count"]) == 0
    assert int(row["indirect_trigger_path_count"]) > 0
    assert int(row["unexpected_trigger_path_count"]) == 0


@pytest.mark.skipif(
    not os.environ.get("TEST_DATABASE_URL") or shutil.which("psql") is None,
    reason="ephemeral PostgreSQL 17 DSN and psql are required",
)
def test_pg17_current_database_owner_gets_implicit_cycle_safe_route():
    query = _query_bytes().decode("ascii")
    row = _run_fixture(_database_owner_fixture_sql(query))
    assert int(row["implicit_database_owner_route_count"]) > 0
    assert int(row["membership_depth_truncated_count"]) == 0
    assert row["catalog_comparison_pass"] == "f"
    assert row["fail_closed"] == "t"


@pytest.mark.skipif(
    not os.environ.get("TEST_DATABASE_URL") or shutil.which("psql") is None,
    reason="ephemeral PostgreSQL 17 DSN and psql are required",
)
def test_pg17_membership_depth_truncation_is_unknown_and_fail_closed():
    query = _query_bytes().decode("ascii")
    row = _run_fixture(_depth_truncation_fixture_sql(query))
    assert int(row["membership_depth_truncated_count"]) > 0
    assert row["closure_coverage"] == "unknown"
    assert row["package_source_coverage"] == "unknown"
    assert row["catalog_comparison_pass"] == "f"
    assert row["fail_closed"] == "t"
