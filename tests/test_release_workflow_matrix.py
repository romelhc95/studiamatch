from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_gov_ci7_target_aware_promotions_are_documented_and_gated() -> None:
    validator = source("scripts/security/validate_work_package.py")
    workflow = source(".github/workflows/security-audit.yml")
    plan = source(".context/operaciones/plan_maestro_sprint1_h2_h5.md")
    matrix = source(".context/operaciones/matriz_adopcion_db.md")

    for branch in (
        "promote/gov-hom-007-o2-req1",
        "promote/gov-hom-007-o3-req1",
        "promote/gov-hom-007-o4-req1",
        "promote/gov-hom-007-o5-req1",
    ):
        assert branch in validator
        assert branch in workflow
        assert branch in plan

    assert "VERIFIED_PROMOTION" in source(".context/work_packages/WP-GOV-CI-007.json")
    assert "candidate_parents != [before, source_sha]" in validator
    assert "BLOCKED" in validator
    assert "NO_DB_CHANGES" in matrix


def test_o5_uses_promotion_boundary_and_skips_governance_preflight() -> None:
    workflow = source(".github/workflows/security-audit.yml")
    governance_job = workflow.split("  governance-preflight:", 1)[1].split("  governance-tests:", 1)[0]
    aggregate = workflow.split("  security-audit:", 1)[1]

    assert "github.event.pull_request.head.ref == 'promote/gov-hom-007-o5-req1'" in governance_job
    assert "desarrollo:promote/gov-hom-007-o5-req1" in aggregate
    assert "test '${{ needs.promotion-boundary.result }}' = 'success'" in aggregate
    assert "test '${{ needs.governance-preflight.result }}' = 'skipped'" in aggregate


def test_o2_o3_o4_promotion_pairs_remain_gated() -> None:
    workflow = source(".github/workflows/security-audit.yml")
    for pair in (
        "certificacion:promote/gov-hom-007-o2-req1",
        "main:promote/gov-hom-007-o3-req1",
        "certificacion:promote/gov-hom-007-o4-req1",
    ):
        assert pair in workflow


def test_unknown_same_repo_promotion_branches_fail_before_ordinary_boundary() -> None:
    workflow = source(".github/workflows/security-audit.yml")
    path_boundary = workflow.split("  path-boundary:", 1)[1].split("  path-boundary-push:", 1)[0]

    assert "promote/gov-hom-*" in path_boundary
    assert "blocked superseded or unknown promotion branch" in path_boundary
    assert "exit 1" in path_boundary
    assert "promote/gov-hom-006-o3-req1" in path_boundary
    assert "promote/gov-hom-006-o5-req1" in path_boundary


def test_post_merge_tri_state_controls_fallback_and_approval_job() -> None:
    workflow = source(".github/workflows/security-audit.yml")
    push_job = workflow.split("  path-boundary-push:", 1)[1].split("  post-merge-approval:", 1)[0]
    approval_job = workflow.split("  post-merge-approval:", 1)[1].split("  promotion-boundary:", 1)[0]
    aggregate = workflow.split("  security-audit:", 1)[1]

    assert "post_merge_classification" in push_job
    assert '"NOT_APPLICABLE"' in push_job
    assert '"VERIFIED_PROMOTION"' in push_job
    assert "exit 1" in push_job
    assert "--post-merge-push-event" in approval_job
    assert "for line in str(pr.get" not in approval_job
    assert "needs.path-boundary-push.outputs.post_merge_promotion" in aggregate


def test_f9_7_contract_is_manual_frozen_only() -> None:
    workflow = source(".github/workflows/f9-7-contract.yml")
    trigger_block = workflow.split("permissions:", 1)[0]

    assert "workflow_dispatch:" in trigger_block
    assert "pull_request:" not in trigger_block
    assert "push:" not in trigger_block
    assert "F97_FROZEN_COMMIT: 258ef3a98c7c1010efe58522bb1eca892e26390e" in workflow
    assert "F97_FROZEN_TREE: 2cb182ab9ece141bd8e84d7bbf9c91d771f603de" in workflow
