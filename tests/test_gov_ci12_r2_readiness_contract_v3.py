import hashlib
import json
from pathlib import Path

from scripts.security.validate_work_package import validate_gov_ci12_v3_contract_case


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "governance" / "gov-ci12"
V3 = FIXTURES / "v3" / "r2_readiness_contract_v3.json"
V3_SHA = FIXTURES / "v3" / "r2_readiness_contract_v3.sha256"


def load_contract():
    return json.loads(V3.read_text(encoding="utf-8"))


def load_case_payload(case):
    fixture = case.get("target_fixture", "v3/positive_control.json")
    payload = json.loads((FIXTURES / fixture).read_text(encoding="utf-8")) if fixture else {"case_id": "CONTROL"}
    mutation = case.get("mutation") or {"op": "replace", "pointer": "/case_id", "value": case["id"]}
    assert mutation == {"op": "replace", "pointer": "/case_id", "value": case["id"]}
    payload["case_id"] = mutation["value"]
    family = case["id"][0]
    if family == "A":
        payload["approval_history"] = {"invalid": True}
    elif family == "R":
        payload["run_payload"] = []
    elif family == "J":
        payload["jobs_payload"] = []
    elif family == "W":
        payload["workflow_gate_binding"] = {}
    elif family == "S":
        payload["readiness_snapshot"] = []
    elif family == "E":
        payload["approval_evidence"] = []
    elif family == "P":
        payload["postmerge_observation"] = {}
        payload["premerge_evidence"] = {}
    elif case["id"] == "H01":
        payload["workflow_text"] = _workflow_source(postmerge_secret=True)
    elif case["id"] == "H02":
        payload["workflow_text"] = _workflow_source(upload=False)
    elif case["id"] == "H03":
        payload["workflow_text"] = _workflow_source(postmerge_environment=True)
    elif case["id"] == "H04":
        payload["artifact_listing"] = {"requires_page_2": True}
    elif case["id"] == "H05":
        payload["fixture_versions"] = ["v2", "v3"]
    elif case["id"] == "H06":
        payload["readiness_snapshot"] = _valid_snapshot(current_pr="443")
    elif case["id"] == "H07":
        payload["approval_history"] = [_valid_approval_record(created_at="2026-08-23T19:41:33Z")]
    return payload


def _workflow_source(*, upload=True, postmerge_secret=False, postmerge_environment=False):
    upload_step = "\n      - uses: actions/upload-artifact@v4\n        with:\n          path: promotion-approval-evidence.json" if upload else ""
    post_env = "\n    environment:\n      name: Promotion" if postmerge_environment else ""
    post_secret = "\n      - run: echo R3_JIT_APPROVAL_ENVELOPE" if postmerge_secret else ""
    return f"""
jobs:
  promotion-boundary:
    name: Promotion Boundary
    environment:
      name: Promotion
    if: github.event.action == 'opened'
    steps:
      - run: echo R3_JIT_APPROVAL_ENVELOPE
      - run: python scripts/security/promotion_evidence.py --write-approval-evidence{upload_step}
  post-merge-approval:
    name: Post Merge Approval{post_env}
    steps:{post_secret}
      - run: echo postmerge
"""


def _valid_snapshot(current_pr="500"):
    return {
        "environment": {"name": "Promotion", "reviewer": "romelhc95-approver", "reviewer_id": 306979205, "can_admins_bypass": False, "prevent_self_review": True, "deployment_branch_policy": None},
        "ruleset": {"name": "owner-only-protected-branch-updates", "enforcement": "active", "restrict_updates": True, "bypass_actors_observable": True, "bypass_actor_count": 1, "bypass_user": "romelhc95", "excluded_user": "romelhc95-approver", "protected_refs": ["refs/heads/desarrollo", "refs/heads/certificacion", "refs/heads/main"]},
        "current_pr": current_pr,
    }


def _valid_approval_record(**extra):
    record = {"state": "approved", "user": {"login": "romelhc95-approver", "id": 306979205}, "environments": [{"id": 20409543239, "name": "Promotion", "can_admins_bypass": False}], "comment": None}
    record.update(extra)
    return record


def test_v1_v2_byte_hashes_are_preserved():
    hashes = {
        "r2_readiness_contract_v1.json": "9b1033b259a45a6513deb0ae468d2dea9645a4cc5a5cccc4e6ad01baa561d985",
        "v2/r2_readiness_contract_v2.json": "d8f8bba99522a79af023f7bf242cf8ca42fad2535dbb4280e088d2c5d8ecd5a0",
    }
    for relative, expected in hashes.items():
        assert hashlib.sha256((FIXTURES / relative).read_bytes()).hexdigest() == expected


def test_v3_detached_digest_matches_exact_bytes():
    expected = V3_SHA.read_text(encoding="utf-8").split()[0]
    assert hashlib.sha256(V3.read_bytes()).hexdigest() == expected


def test_v3_contract_has_no_self_referential_candidate_identity():
    contract = load_contract()
    raw = json.dumps(contract, sort_keys=True)
    assert "contract_digest" not in contract
    assert "candidate_commit" not in raw
    assert "candidate_tree" not in raw
    assert contract["candidate_identity"] == "external_after_commit_only"


def test_v3_required_case_ids_are_exactly_the_original_98():
    contract = load_contract()
    cases = contract["required_test_cases"]
    ids = [case["id"] for case in cases]
    expected = []
    for family, count in [("A", 16), ("R", 10), ("J", 24), ("W", 7), ("S", 15), ("E", 15), ("P", 11)]:
        expected.extend(f"{family}{index:02d}" for index in range(1, count + 1))
    assert ids == expected
    assert len(ids) == 98
    assert len(set(ids)) == 98


def test_v3_required_contract_cases_call_productive_entrypoint():
    for case in load_contract()["required_test_cases"]:
        errors = validate_gov_ci12_v3_contract_case(case, load_case_payload(case))
        assert errors == case["expected_errors"], case["id"]


def test_v3_hardening_cases_call_productive_entrypoint():
    cases = load_contract()["hardening_test_cases"]
    assert cases
    for case in cases:
        errors = validate_gov_ci12_v3_contract_case(case, load_case_payload(case))
        assert errors == case["expected_errors"], case["id"]


def test_v3_contract_entrypoint_rejects_unmutated_payload():
    case = load_contract()["required_test_cases"][0]
    assert validate_gov_ci12_v3_contract_case(case, {"case_id": "CONTROL"}) == ["CONTRACT_CASE_PAYLOAD_INVALID"]
