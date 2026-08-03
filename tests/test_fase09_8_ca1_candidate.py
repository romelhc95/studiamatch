from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
F97_FROZEN_COMMIT = "258ef3a98c7c1010efe58522bb1eca892e26390e"
ZERO_SHA = "0000000000000000000000000000000000000000"
BASE_SHA = "638c51c668ae914f9308839d3653cd4db3e34251"
HEAD_SHA = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
OTHER_SHA = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"


CA1_ALLOWED_STATUSES = {
    ".github/workflows/fg1_inventory.yml": {"M"},
    ".github/workflows/fg3_integrity.yml": {"M"},
    ".github/workflows/production_pipeline.yml": {"M"},
    "scripts/core/certification_canary_manifest.py": {"A"},
    "scripts/core/cleansing_worker.py": {"M"},
    "scripts/core/discovery_institutions.py": {"M"},
    "scripts/core/enrichment_worker.py": {"M"},
    "scripts/core/integrity_ping.py": {"M"},
    "scripts/core/master_orchestrator.py": {"M"},
    "scripts/core/sync_vector_worker.py": {"M"},
    "scripts/core/universal_harvester.py": {"M"},
    "scripts/shared/db_client.py": {"M"},
}
CA1_ALLOWED = set(CA1_ALLOWED_STATUSES)


def source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def transition_boundary_policy(
    *,
    event_name: str,
    ref: str,
    before: str,
    base_sha: str,
    head_sha: str,
    checkout_sha: str,
    first_parent: str,
    parent_count: int,
    before_is_ancestor: bool,
    commits_exist: bool = True,
) -> tuple[bool, str, str]:
    if event_name == "pull_request":
        transition_base = base_sha
        transition_head = head_sha
    elif event_name == "push":
        if ref != "refs/heads/desarrollo":
            return False, "", ""
        transition_base = before
        transition_head = head_sha
    else:
        return False, "", ""

    valid_sha = lambda value: len(value) == 40 and value != ZERO_SHA and all(ch in "0123456789abcdef" for ch in value)
    if not valid_sha(transition_base) or not valid_sha(transition_head):
        return False, transition_base, transition_head
    if not commits_exist or not before_is_ancestor:
        return False, transition_base, transition_head
    if checkout_sha != transition_head:
        return False, transition_base, transition_head
    if event_name == "push":
        if transition_base == F97_FROZEN_COMMIT:
            return False, transition_base, transition_head
        if parent_count > 1 and transition_base != first_parent:
            return False, transition_base, transition_head
    return True, transition_base, transition_head


def transition_path_policy(changes: list[tuple[str, ...]]) -> bool:
    denied_prefixes = ("db/", "supabase/", "web/", "scripts/maintenance/")
    denied_exact = {".gitattributes"}
    protected_prefixes = ("scripts/core/", "scripts/shared/", "config/")
    for change in changes:
        status = change[0]
        path = change[-1]
        old_path = change[1] if status.startswith(("R", "C")) else None
        paths_to_check = [p for p in (old_path, path) if p]
        if any(p.startswith(denied_prefixes) or p in denied_exact for p in paths_to_check):
            return False
        if any(p.startswith(protected_prefixes) for p in paths_to_check) and not any(p in CA1_ALLOWED for p in paths_to_check):
            return False
        if path in CA1_ALLOWED or old_path in CA1_ALLOWED:
            expected_statuses = CA1_ALLOWED_STATUSES.get(path) or CA1_ALLOWED_STATUSES.get(old_path) or set()
            if status not in expected_statuses:
                return False
    return True


def test_fg1_inventory_is_config_driven_and_fail_closed() -> None:
    code = source("scripts/core/discovery_institutions.py")
    assert "config/institution_sources.json is required" in code
    assert "LEGACY_SOURCES" not in code
    assert "Using legacy hardcoded source list" not in code
    assert "select_all_service(" not in code


def test_harvester_does_not_promote_discovered_before_valid_content() -> None:
    code = source("scripts/core/universal_harvester.py")
    assert 'DISCOVERED_STATUS = "discovered"' in code
    assert "PROTECTED_STAGING_STATUSES" in code
    assert "_resumable_urls" in code
    assert "_validate_pending_payload" in code
    assert "_promote_discovered_to_pending" in code
    assert "patch_exact_one_raise" in code
    assert '"&status=eq.discovered"' in code
    assert 'item["status"] = "pending"' in code
    assert 'data={"status": "pending"}' not in code


def test_sync_paginates_all_pending_records_and_keeps_mock_inactive() -> None:
    code = source("scripts/core/sync_vector_worker.py")
    db_client = source("scripts/shared/db_client.py")
    assert "select_all_pipeline('enriched_programs'" in code
    assert "get_pending_enriched(limit=args.limit, institution_id=args.institution_id)" in code
    assert "is_real_enrichment = enriched.get('is_mock_data') is False" in code
    assert "not is_real_enrichment" in code
    assert "publication_status" not in code
    assert "manual_updated_at" not in code
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
    assert "sys.exit(run_integrity_ping(institution_id=args.institution_id, limit=args.limit))" in code
    assert "failed or partial" in code


def test_scheduled_workflows_have_kill_switch_and_dedicated_environments() -> None:
    workflows = {
        "fg1": source(".github/workflows/fg1_inventory.yml"),
        "fg2": source(".github/workflows/production_pipeline.yml"),
        "fg3": source(".github/workflows/fg3_integrity.yml"),
    }
    for text in workflows.values():
        assert "AUTOMATION_ENABLED" in text
        assert "PRODUCTION_WRITERS_PAUSED" in text
        assert "production_control_preflight:" in text
        assert "needs.production_control_preflight.outputs.allow_writer == 'true'" in text
        assert "github.ref_name == 'main' && vars.AUTOMATION_ENABLED == 'true'" not in text

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
    allowed = workflow.split("f98_ca1_allowed_statuses = {", 1)[1].split("f98_ca1_allowed = set", 1)[0]
    assert "'.github/workflows/security-audit.yml'" not in allowed
    assert "'scripts/core/certification_canary_manifest.py': {'A'}" in allowed
    assert "'scripts/core/enrichment_worker.py': {'M'}" in allowed
    assert "'scripts/core/master_orchestrator.py': {'M'}" in allowed
    assert "len(baseline) != 32" in workflow
    assert "F9.8 CA1 protected-path drift is within the explicit allowlist" in workflow
    assert "F97: ${{ needs.fase09-7-remediation.result }}" in workflow
    assert "fase09-7-remediation" in workflow.split("needs:", 1)[1]
    assert "tests/test_fase09_8_runtime_security.py" in workflow
    assert "fase10-promotion-contract" in workflow
    assert "fase09-9-pre-main-controls" in workflow


def test_f99_gate_expects_go_after_trusted_harness_baseline() -> None:
    workflow = source(".github/workflows/security-audit.yml")
    assert 'if [ "$F99_BASE_HAS_HARNESS" = "true" ]; then' in workflow
    assert 'F99_EXPECTED_DECISION="GO_TO_PREPARE_CERTIFICATION_PR"' in workflow
    assert 'F99_EXPECTED_DECISION="NO_GO_KNOWN_T_H1_CA1_002B"' in workflow
    assert 'if [ "$F99_RUNTIME_CHANGED" = "true" ]; then\n            F99_EXPECTED_DECISION' not in workflow


def test_f9_7_bridge_preserves_frozen_candidate_and_transition_boundary() -> None:
    workflow = source(".github/workflows/f9-7-contract.yml")
    assert "F97_FROZEN_COMMIT: 258ef3a98c7c1010efe58522bb1eca892e26390e" in workflow
    assert "F97_FROZEN_TREE: 2cb182ab9ece141bd8e84d7bbf9c91d771f603de" in workflow
    assert "Validate F9.8 transition boundary" in workflow
    assert "F98_BASE_COMMIT" in workflow
    assert "github.event.pull_request.base.sha" in workflow
    assert "F98_BASE_COMMIT=\"${{ github.event.before }}\"" in workflow
    assert "test \"${{ github.ref }}\" = \"refs/heads/desarrollo\"" in workflow
    assert "test \"$F98_BASE_COMMIT\" != \"$F97_FROZEN_COMMIT\"" in workflow
    assert "git merge-base --is-ancestor \"$F98_BASE_COMMIT\" \"$F98_HEAD_COMMIT\"" in workflow
    assert "git rev-parse \"$F98_HEAD_COMMIT^1\"" in workflow
    assert "F98_TRANSITION_PASS" in workflow
    assert "HISTORICAL_F97_PASS" in workflow
    assert "git checkout --detach \"$F97_CANDIDATE_COMMIT\"" in workflow
    allowed = workflow.split("allowed_statuses = {", 1)[1].split("allowed = set(allowed_statuses)", 1)[0]
    assert allowed.count(".github/workflows/fg1_inventory.yml") == 1
    assert allowed.count(".github/workflows/fg3_integrity.yml") == 1
    assert allowed.count(".github/workflows/production_pipeline.yml") == 1
    assert allowed.count("scripts/core/certification_canary_manifest.py") == 1
    assert allowed.count("scripts/core/cleansing_worker.py") == 1
    assert allowed.count("scripts/core/discovery_institutions.py") == 1
    assert allowed.count("scripts/core/enrichment_worker.py") == 1
    assert allowed.count("scripts/core/integrity_ping.py") == 1
    assert allowed.count("scripts/core/master_orchestrator.py") == 1
    assert allowed.count("scripts/core/sync_vector_worker.py") == 1
    assert allowed.count("scripts/core/universal_harvester.py") == 1
    assert allowed.count("scripts/shared/db_client.py") == 1
    assert "'scripts/core/certification_canary_manifest.py': {'A'}" in workflow
    assert "'scripts/core/enrichment_worker.py': {'M'}" in workflow
    assert "status not in expected_statuses" in workflow
    assert "base-present:{path}" in workflow
    assert "denied_prefixes = ('db/', 'supabase/', 'web/', 'scripts/maintenance/')" in workflow
    assert "paths_to_check" in workflow


def test_transition_boundary_accepts_pull_request_event() -> None:
    passed, base, head = transition_boundary_policy(
        event_name="pull_request",
        ref="refs/pull/1/merge",
        before=ZERO_SHA,
        base_sha=BASE_SHA,
        head_sha=HEAD_SHA,
        checkout_sha=HEAD_SHA,
        first_parent=OTHER_SHA,
        parent_count=1,
        before_is_ancestor=True,
    )
    assert passed
    assert base == BASE_SHA
    assert head == HEAD_SHA


def test_transition_boundary_blocks_pull_request_zero_base_or_head() -> None:
    common = dict(
        event_name="pull_request",
        ref="refs/pull/1/merge",
        before=ZERO_SHA,
        checkout_sha=HEAD_SHA,
        first_parent=OTHER_SHA,
        parent_count=1,
        before_is_ancestor=True,
    )
    assert not transition_boundary_policy(base_sha=ZERO_SHA, head_sha=HEAD_SHA, **common)[0]
    assert not transition_boundary_policy(base_sha=BASE_SHA, head_sha=ZERO_SHA, **common)[0]


def test_transition_boundary_blocks_pull_request_base_not_ancestor() -> None:
    passed, _, _ = transition_boundary_policy(
        event_name="pull_request",
        ref="refs/pull/1/merge",
        before=ZERO_SHA,
        base_sha=BASE_SHA,
        head_sha=HEAD_SHA,
        checkout_sha=HEAD_SHA,
        first_parent=OTHER_SHA,
        parent_count=1,
        before_is_ancestor=False,
    )
    assert not passed


def test_transition_boundary_blocks_pull_request_missing_commits() -> None:
    passed, _, _ = transition_boundary_policy(
        event_name="pull_request",
        ref="refs/pull/1/merge",
        before=ZERO_SHA,
        base_sha=BASE_SHA,
        head_sha=HEAD_SHA,
        checkout_sha=HEAD_SHA,
        first_parent=OTHER_SHA,
        parent_count=1,
        before_is_ancestor=True,
        commits_exist=False,
    )
    assert not passed


def test_transition_boundary_blocks_pull_request_head_mismatch() -> None:
    passed, _, _ = transition_boundary_policy(
        event_name="pull_request",
        ref="refs/pull/1/merge",
        before=ZERO_SHA,
        base_sha=BASE_SHA,
        head_sha=HEAD_SHA,
        checkout_sha=OTHER_SHA,
        first_parent=OTHER_SHA,
        parent_count=1,
        before_is_ancestor=True,
    )
    assert not passed


def test_transition_boundary_accepts_push_merge_first_parent() -> None:
    passed, base, head = transition_boundary_policy(
        event_name="push",
        ref="refs/heads/desarrollo",
        before=BASE_SHA,
        base_sha=OTHER_SHA,
        head_sha=HEAD_SHA,
        checkout_sha=HEAD_SHA,
        first_parent=BASE_SHA,
        parent_count=2,
        before_is_ancestor=True,
    )
    assert passed
    assert base == BASE_SHA
    assert head == HEAD_SHA


def test_transition_boundary_blocks_frozen_commit_as_push_base() -> None:
    passed, _, _ = transition_boundary_policy(
        event_name="push",
        ref="refs/heads/desarrollo",
        before=F97_FROZEN_COMMIT,
        base_sha=OTHER_SHA,
        head_sha=HEAD_SHA,
        checkout_sha=HEAD_SHA,
        first_parent=F97_FROZEN_COMMIT,
        parent_count=2,
        before_is_ancestor=True,
    )
    assert not passed


def test_transition_boundary_blocks_zero_before() -> None:
    passed, _, _ = transition_boundary_policy(
        event_name="push",
        ref="refs/heads/desarrollo",
        before=ZERO_SHA,
        base_sha=OTHER_SHA,
        head_sha=HEAD_SHA,
        checkout_sha=HEAD_SHA,
        first_parent=ZERO_SHA,
        parent_count=2,
        before_is_ancestor=True,
    )
    assert not passed


def test_transition_boundary_blocks_before_not_ancestor() -> None:
    passed, _, _ = transition_boundary_policy(
        event_name="push",
        ref="refs/heads/desarrollo",
        before=BASE_SHA,
        base_sha=OTHER_SHA,
        head_sha=HEAD_SHA,
        checkout_sha=HEAD_SHA,
        first_parent=BASE_SHA,
        parent_count=2,
        before_is_ancestor=False,
    )
    assert not passed


def test_transition_boundary_blocks_non_desarrollo_push() -> None:
    passed, _, _ = transition_boundary_policy(
        event_name="push",
        ref="refs/heads/main",
        before=BASE_SHA,
        base_sha=OTHER_SHA,
        head_sha=HEAD_SHA,
        checkout_sha=HEAD_SHA,
        first_parent=BASE_SHA,
        parent_count=2,
        before_is_ancestor=True,
    )
    assert not passed


def test_transition_boundary_blocks_force_push() -> None:
    passed, _, _ = transition_boundary_policy(
        event_name="push",
        ref="refs/heads/desarrollo",
        before=BASE_SHA,
        base_sha=OTHER_SHA,
        head_sha=HEAD_SHA,
        checkout_sha=HEAD_SHA,
        first_parent=OTHER_SHA,
        parent_count=2,
        before_is_ancestor=False,
    )
    assert not passed


def test_transition_boundary_blocks_head_mismatch() -> None:
    passed, _, _ = transition_boundary_policy(
        event_name="push",
        ref="refs/heads/desarrollo",
        before=BASE_SHA,
        base_sha=OTHER_SHA,
        head_sha=HEAD_SHA,
        checkout_sha=OTHER_SHA,
        first_parent=BASE_SHA,
        parent_count=2,
        before_is_ancestor=True,
    )
    assert not passed


def test_transition_boundary_accepts_fast_forward_multi_commit_push() -> None:
    passed, base, head = transition_boundary_policy(
        event_name="push",
        ref="refs/heads/desarrollo",
        before=BASE_SHA,
        base_sha=OTHER_SHA,
        head_sha=HEAD_SHA,
        checkout_sha=HEAD_SHA,
        first_parent=OTHER_SHA,
        parent_count=1,
        before_is_ancestor=True,
    )
    assert passed
    assert base == BASE_SHA
    assert head == HEAD_SHA


def test_transition_policy_blocks_ca1_plus_db_path() -> None:
    assert not transition_path_policy([
        ("M", "scripts/core/integrity_ping.py"),
        ("M", "db/migrations/ca2.sql"),
    ])


def test_transition_policy_accepts_canary_helper_addition_and_blocks_wrong_status() -> None:
    assert transition_path_policy([("A", "scripts/core/certification_canary_manifest.py")])
    assert not transition_path_policy([("M", "scripts/core/certification_canary_manifest.py")])
    assert not transition_path_policy([("A", "scripts/core/enrichment_worker.py")])


def test_transition_policy_blocks_rename_copy_delete_and_mode_drift() -> None:
    assert not transition_path_policy([("R100", "scripts/core/integrity_ping.py", "scripts/core/integrity_ping_new.py")])
    assert not transition_path_policy([("C100", "scripts/core/integrity_ping.py", "scripts/core/integrity_ping_copy.py")])
    assert not transition_path_policy([("D", "scripts/core/integrity_ping.py")])
    assert not transition_path_policy([("T", "scripts/core/integrity_ping.py")])


def test_replay_historical_f9_7_still_uses_frozen_candidate() -> None:
    workflow = source(".github/workflows/f9-7-contract.yml")
    replay = workflow.split("Resolve frozen F9.7 candidate", 1)[1].split("actions/setup-python", 1)[0]
    assert "F97_CANDIDATE_COMMIT=\"$F97_FROZEN_COMMIT\"" in replay
    assert "test \"$F97_CANDIDATE_TREE\" = \"$F97_FROZEN_TREE\"" in replay
    assert "HISTORICAL_F97_PASS" in replay
