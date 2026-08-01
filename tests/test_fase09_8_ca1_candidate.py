from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_fg1_inventory_is_config_driven_and_fail_closed() -> None:
    code = source("scripts/core/discovery_institutions.py")
    assert "config/institution_sources.json is required" in code
    assert "LEGACY_SOURCES" not in code
    assert "Using legacy hardcoded source list" not in code
    assert "select_all_service(" not in code


def test_harvester_does_not_promote_discovered_before_valid_content() -> None:
    code = source("scripts/core/universal_harvester.py")
    assert '"status": "discovered"' in code
    assert 'item["status"] = "pending"' in code
    assert 'data={"status": "pending"}' not in code
    assert 'status=eq.discovered' not in code


def test_sync_paginates_all_pending_records_and_keeps_mock_inactive() -> None:
    code = source("scripts/core/sync_vector_worker.py")
    db_client = source("scripts/shared/db_client.py")
    assert "select_all_pipeline('enriched_programs'" in code
    assert "get_pending_enriched(limit=None)" in code
    assert "not enriched.get('is_mock_data', True)" in code
    assert "manual_updated_at,last_404_at" in code
    assert "existing_course.get('last_404_at') is not None" in code
    assert "sys.exit(1 if failed or partial else 0)" in code
    assert "res.status_code not in (200, 206)" in db_client
    assert "SelectAllPipeline failed" in db_client


def test_fg3_integrity_ping_is_safe_and_fail_closed() -> None:
    code = source("scripts/core/integrity_ping.py")
    assert "def is_safe_public_url" in code
    assert "ipaddress.ip_address" in code
    assert "socket.getaddrinfo" in code
    assert "parsed.scheme != 'https'" in code
    assert "request_pinned_public_url" in code
    assert "HTTP_GONE_STATUSES = {404, 410}" in code
    assert "HTTP_TRANSIENT_STATUSES" in code
    assert "def patch_course_exact_one" in code
    assert "request_pinned_public_url" in code
    assert "FixedIPHTTPSConnection" in code
    assert "server_hostname=self.host" in code
    assert "getpeername" in code
    assert "response.status_code in (405, 501)" in code
    assert "200 <= response.status_code < 300" in code
    assert "patch_exact_one_raise" in code
    assert "sys.exit(run_integrity_ping())" in code
    assert "failed or partial" in code


def test_scheduled_workflows_have_kill_switch_and_dedicated_environments() -> None:
    workflows = {
        "fg1": source(".github/workflows/fg1_inventory.yml"),
        "fg2": source(".github/workflows/production_pipeline.yml"),
        "fg3": source(".github/workflows/fg3_integrity.yml"),
    }
    for text in workflows.values():
        assert "AUTOMATION_ENABLED" in text
        assert "github.event_name != 'schedule'" in text
        assert "github.ref_name == 'main' && vars.AUTOMATION_ENABLED == 'true'" in text

    assert "Production-Scheduled-FG1" in workflows["fg1"]
    assert "Production-Scheduled-FG2" in workflows["fg2"]
    assert "Production-Scheduled-FG3" in workflows["fg3"]
    assert "group: studiamatch-fg2" in workflows["fg3"]


def test_fg2_candidate_does_not_invoke_out_of_scope_audits_or_canaries() -> None:
    workflow = source(".github/workflows/production_pipeline.yml")
    assert "scripts/maintenance/" not in workflow
    assert "requirements-db-migrate.txt" not in workflow
    assert "pages/projects" not in workflow
    assert "Trigger Cloudflare Pages rebuild" not in workflow
    assert "CA1-only candidate stops after FG2 sync" in workflow


def test_security_audit_aggregates_f9_8_ca1_gate_additively() -> None:
    workflow = source(".github/workflows/security-audit.yml")
    assert "fase09-8-ca1:" in workflow
    assert "F9.8 CA1 Pipeline Candidate Contract" in workflow
    assert "needs.fase09-8-ca1.result" in workflow
    assert "Run focused F9.8 CA1 tests" in workflow
    assert "tests/test_fase09_8_ca1_candidate.py tests/test_fase09_8_runtime_security.py" in workflow
    assert "! grep -q" not in workflow
    assert "git grep -a -q -E \"$F97_CREDENTIAL_PATTERN\" \"$F97_CANDIDATE_TREE\" -- ." in workflow
    assert "git rev-list \"$F97_BASELINE_COMMIT..$F97_CANDIDATE_COMMIT\"" in workflow
    assert "'.github/workflows/security-audit.yml'" not in workflow.split("f98_ca1_allowed =", 1)[1].split("}", 1)[0]
    assert "len(baseline) != 32" in workflow
    assert "F9.8 CA1 protected-path drift is within the explicit allowlist" in workflow
    assert "F97: ${{ needs.fase09-7-remediation.result }}" in workflow
    assert "fase09-7-remediation" in workflow.split("needs:", 1)[1]
    assert "tests/test_fase09_8_runtime_security.py" in workflow
    assert "fase10-promotion-contract" in workflow


def test_f9_7_bridge_preserves_frozen_candidate_and_transition_boundary() -> None:
    workflow = source(".github/workflows/f9-7-contract.yml")
    assert "F97_FROZEN_COMMIT: 258ef3a98c7c1010efe58522bb1eca892e26390e" in workflow
    assert "F97_FROZEN_TREE: 2cb182ab9ece141bd8e84d7bbf9c91d771f603de" in workflow
    assert "Validate F9.8 transition boundary" in workflow
    assert "F98_BASE_COMMIT" in workflow
    assert "github.event.pull_request.base.sha" in workflow
    assert "d9c7f180495c985a1e9a0ada4a42525fda60a870" in workflow
    assert "F98_TRANSITION_PASS" in workflow
    assert "HISTORICAL_F97_PASS" in workflow
    assert "git checkout --detach \"$F97_CANDIDATE_COMMIT\"" in workflow
    allowed = workflow.split("allowed = {", 1)[1].split("}", 1)[0]
    assert allowed.count(".github/workflows/fg1_inventory.yml") == 1
    assert allowed.count(".github/workflows/fg3_integrity.yml") == 1
    assert allowed.count(".github/workflows/production_pipeline.yml") == 1
    assert allowed.count("scripts/core/discovery_institutions.py") == 1
    assert allowed.count("scripts/core/integrity_ping.py") == 1
    assert allowed.count("scripts/core/sync_vector_worker.py") == 1
    assert allowed.count("scripts/core/universal_harvester.py") == 1
    assert allowed.count("scripts/shared/db_client.py") == 1
    assert "status != 'M'" in workflow
    assert "denied_prefixes = ('db/', 'supabase/', 'web/', 'scripts/maintenance/')" in workflow
    assert "paths_to_check" in workflow
