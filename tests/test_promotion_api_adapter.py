import json
import socket
import urllib.error

import pytest

from scripts.security.github_promotion_snapshot import GitHubClient, SnapshotError, build_snapshot, collect_snapshot, validate_snapshot


def raw_environment():
    return {
        "id": 10,
        "name": "Promotion",
        "can_admins_bypass": False,
        "prevent_self_review": True,
        "deployment_branch_policy": None,
        "protection_rules": [
            {"type": "required_reviewers", "reviewers": [{"reviewer": {"login": "romelhc95-approver", "id": 306979205}}]}
        ],
    }


def raw_ruleset(**updates):
    payload = {
        "id": 21255108,
        "name": "owner-only-protected-branch-updates",
        "enforcement": "active",
        "conditions": {"ref_name": {"include": ["refs/heads/desarrollo", "refs/heads/certificacion", "refs/heads/main"]}},
        "rules": [{"type": "update"}],
        "bypass_actors": [{"actor_type": "User", "actor_id": 18040405, "bypass_mode": "always"}],
    }
    payload.update(updates)
    return payload


def test_collector_parses_required_reviewers_and_ruleset_digest():
    snapshot = build_snapshot(raw_environment(), raw_ruleset(), [{"number": 445, "head": {"ref": "promote/gov-hom-012-o2-req1"}}], {"id": 85455}, "445")
    assert validate_snapshot(snapshot) == []
    assert snapshot["environment"]["reviewer"] == "romelhc95-approver"
    assert snapshot["ruleset"]["canonical_digest"].startswith("sha256:")


def test_collector_treats_missing_bypass_actors_as_unobservable():
    ruleset = raw_ruleset()
    ruleset.pop("bypass_actors")
    snapshot = build_snapshot(raw_environment(), ruleset, [{"number": 445, "head": {"ref": "promote/gov-hom-012-o2-req1"}}], {"id": 85455}, "445")
    assert "SNAPSHOT_RULESET_BYPASS_UNOBSERVABLE" in validate_snapshot(snapshot)
    assert snapshot["ruleset"]["bypass_actor_count"] == "UNOBSERVABLE"


def test_collector_requires_required_reviewers_protection_rule():
    environment = raw_environment()
    environment.pop("protection_rules")
    environment["reviewers"] = [{"reviewer": {"login": "romelhc95-approver", "id": 306979205}}]
    snapshot = build_snapshot(environment, raw_ruleset(), [{"number": 445, "head": {"ref": "promote/gov-hom-012-o2-req1"}}], {"id": 85455}, "445")
    assert "SNAPSHOT_REQUIRED_REVIEWER_INVALID" in validate_snapshot(snapshot)


def test_collector_rejects_extra_required_reviewer():
    environment = raw_environment()
    environment["protection_rules"][0]["reviewers"].append({"reviewer": {"login": "someone-else", "id": 123}})
    snapshot = build_snapshot(environment, raw_ruleset(), [], {"id": 85455}, "445")
    assert "SNAPSHOT_REQUIRED_REVIEWER_INVALID" in validate_snapshot(snapshot)


def test_collector_rejects_wrong_bypass_actor():
    snapshot = build_snapshot(raw_environment(), raw_ruleset(bypass_actors=[{"actor_type": "User", "actor_id": 306979205, "bypass_mode": "always"}]), [], {"id": 85455}, "445")
    assert "SNAPSHOT_RULESET_BYPASS_INVALID" in validate_snapshot(snapshot)


def test_fixture_is_sanitized_and_valid():
    fixture = json.loads(open("tests/fixtures/governance/gov-ci12/readiness_valid.json", encoding="utf-8").read())
    assert validate_snapshot(fixture) == []


def test_collector_paginates_all_open_pull_requests(monkeypatch):
    def fake_get(self, path):
        if path == "/environments/Promotion":
            return raw_environment()
        if path == "/rulesets?per_page=100&page=1":
            return [{"id": 21255108, "name": "owner-only-protected-branch-updates"}]
        if path == "/rulesets/21255108":
            return raw_ruleset()
        if path == "https://api.github.com/apps/cloudflare-workers-and-pages":
            return {"id": 85455}
        if path == "/pulls?state=open&per_page=100&page=1":
            return [{"number": number, "head": {"ref": "feature"}} for number in range(100)]
        if path == "/pulls?state=open&per_page=100&page=2":
            return [{"number": 777, "head": {"ref": "promote/gov-hom-012-o3-req1"}}]
        raise AssertionError(path)

    monkeypatch.setattr(GitHubClient, "get", fake_get)
    snapshot = collect_snapshot(GitHubClient(repo="romelhc95/studiamatch", token="token"), "445")
    assert snapshot["active_promotions"] == ["777"]


def test_collector_paginates_rulesets(monkeypatch):
    def fake_get(self, path):
        if path == "/environments/Promotion":
            return raw_environment()
        if path == "/rulesets?per_page=100&page=1":
            return [{"id": number, "name": f"other-{number}"} for number in range(100)]
        if path == "/rulesets?per_page=100&page=2":
            return [{"id": 21255108, "name": "owner-only-protected-branch-updates"}]
        if path == "/rulesets/21255108":
            return raw_ruleset()
        if path == "/pulls?state=open&per_page=100&page=1":
            return []
        if path == "https://api.github.com/apps/cloudflare-workers-and-pages":
            return {"id": 85455}
        raise AssertionError(path)

    monkeypatch.setattr(GitHubClient, "get", fake_get)
    assert validate_snapshot(collect_snapshot(GitHubClient(repo="romelhc95/studiamatch", token="token"), "445")) == []


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        (401, "PERMISSION_DENIED:401"),
        (403, "PERMISSION_DENIED:403"),
        (404, "UNOBSERVABLE:http_404"),
        (429, "UNOBSERVABLE:http_429"),
        (500, "UNOBSERVABLE:http_500"),
        (503, "UNOBSERVABLE:http_503"),
    ],
)
def test_collector_http_errors_are_diagnostic(monkeypatch, code, expected):
    def fake_urlopen(request, timeout):
        raise urllib.error.HTTPError(request.full_url, code, "boom", {}, None)

    sleeps = []
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    with pytest.raises(SnapshotError) as exc:
        GitHubClient(repo="romelhc95/studiamatch", token="token", sleeper=sleeps.append).get("/rulesets")
    assert expected in str(exc.value)
    if code in {404, 429, 500, 503}:
        assert sleeps == [0.25, 0.5, 1.0]


def test_collector_timeout_is_diagnostic(monkeypatch):
    def fake_urlopen(request, timeout):
        raise socket.timeout("slow")

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    with pytest.raises(SnapshotError) as exc:
        GitHubClient(repo="romelhc95/studiamatch", token="token").get("/rulesets")
    assert "UNOBSERVABLE:timeout" in str(exc.value)


def test_collector_invalid_json_is_diagnostic(monkeypatch):
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b"{"

    monkeypatch.setattr("urllib.request.urlopen", lambda request, timeout: Response())
    with pytest.raises(SnapshotError) as exc:
        GitHubClient(repo="romelhc95/studiamatch", token="token").get("/rulesets")
    assert "INVALID:json" in str(exc.value)
