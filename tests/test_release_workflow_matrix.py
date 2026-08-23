from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_gov_ci6_target_aware_promotions_are_documented_and_gated() -> None:
    validator = source("scripts/security/validate_work_package.py")
    workflow = source(".github/workflows/security-audit.yml")
    plan = source(".context/operaciones/plan_maestro_sprint1_h2_h5.md")
    matrix = source(".context/operaciones/matriz_adopcion_db.md")

    for branch in (
        "promote/gov-hom-006-o2-req1",
        "promote/gov-hom-006-o3-req1",
        "promote/gov-hom-006-o4-req1",
        "promote/gov-hom-006-o5-req1",
    ):
        assert branch in validator
        assert branch in workflow
        assert branch in plan

    assert "candidate_parent_1" in source(".context/work_packages/WP-GOV-CI-006.json")
    assert "candidate_parents != [before, source_sha]" in validator
    assert "MANUAL_FROZEN_ONLY" in source(".context/work_packages/WP-GOV-CI-006.json")
    assert "NO_DB_CHANGES" in matrix


def test_f9_7_contract_is_manual_frozen_only() -> None:
    workflow = source(".github/workflows/f9-7-contract.yml")
    trigger_block = workflow.split("permissions:", 1)[0]

    assert "workflow_dispatch:" in trigger_block
    assert "pull_request:" not in trigger_block
    assert "push:" not in trigger_block
    assert "F97_FROZEN_COMMIT: 258ef3a98c7c1010efe58522bb1eca892e26390e" in workflow
    assert "F97_FROZEN_TREE: 2cb182ab9ece141bd8e84d7bbf9c91d771f603de" in workflow
