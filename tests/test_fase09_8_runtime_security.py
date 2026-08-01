from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.core import integrity_ping
from scripts.shared import db_client


ROOT = Path(__file__).resolve().parents[1]
CA1_ALLOWED = {
    ".github/workflows/fg1_inventory.yml",
    ".github/workflows/fg3_integrity.yml",
    ".github/workflows/production_pipeline.yml",
    "scripts/core/discovery_institutions.py",
    "scripts/core/integrity_ping.py",
    "scripts/core/sync_vector_worker.py",
    "scripts/core/universal_harvester.py",
    "scripts/shared/db_client.py",
}


def transition_policy(changes, branch="feat/f9-8-ca1-candidate"):
    del branch
    denied_prefixes = ("db/", "supabase/", "web/", "scripts/maintenance/")
    f97_artifacts = ("db/manifests/fase09_7_", "db/migrations/20260728_fase09_7_")
    for change in changes:
        status = change[0]
        path = change[-1]
        old_path = change[1] if status.startswith(("R", "C")) else None
        paths_to_check = [p for p in (old_path, path) if p]
        if any(p.startswith(denied_prefixes) or p.startswith(f97_artifacts) for p in paths_to_check):
            return False
        if path in CA1_ALLOWED or old_path in CA1_ALLOWED:
            if status != "M":
                return False
        elif any(p.startswith(("scripts/core/", "scripts/shared/", "config/")) for p in paths_to_check):
            return False
    return True


def aggregate_policy(results):
    required = ["credential-scan", "fase09-7-remediation", "fase09-8-ca1"]
    return all(results.get(name) == "success" for name in required)


def credential_policy(tree_clean=True, commit_range_clean=True, diff_only=False):
    return tree_clean and commit_range_clean and not diff_only


def test_transition_policy_allows_exact_eight_ca1_modifications():
    assert transition_policy([("M", path) for path in sorted(CA1_ALLOWED)])


@pytest.mark.parametrize(
    "changes",
    [
        [("M", "scripts/core/new_worker.py")],
        [("M", "scripts/core/integrity_ping.py"), ("M", "db/migrations/ca2.sql")],
        [("M", "db/manifests/fase09_7_free_schema_rls_v3.json")],
        [("R100", "scripts/core/integrity_ping.py", "scripts/core/integrity_ping_new.py")],
        [("C100", "scripts/core/integrity_ping.py", "scripts/core/integrity_ping_copy.py")],
        [("D", "scripts/core/integrity_ping.py")],
        [("T", "scripts/core/integrity_ping.py")],
        [("R100", "db/migrations/ca2.sql", "docs/ca2.sql")],
        [("C100", "supabase/functions/x.ts", "docs/x.ts")],
    ],
)
def test_transition_policy_blocks_non_ca1_and_non_oid_drift(changes):
    assert not transition_policy(changes)


def test_transition_policy_ignores_forged_branch_name():
    assert not transition_policy([("M", "db/migrations/ca2.sql")], branch="feat/f9-8-ca1-candidate")


def test_aggregate_policy_requires_f9_7_and_f9_8_and_blocks_non_success():
    assert aggregate_policy({"credential-scan": "success", "fase09-7-remediation": "success", "fase09-8-ca1": "success"})
    assert not aggregate_policy({"credential-scan": "success", "fase09-8-ca1": "success"})
    assert not aggregate_policy({"credential-scan": "success", "fase09-7-remediation": "success"})
    assert not aggregate_policy({"credential-scan": "success", "fase09-7-remediation": "skipped", "fase09-8-ca1": "success"})
    assert not aggregate_policy({"credential-scan": "success", "fase09-7-remediation": "cancelled", "fase09-8-ca1": "success"})


def test_credential_policy_requires_tree_and_commit_range_scans():
    assert credential_policy()
    assert not credential_policy(tree_clean=False)
    assert not credential_policy(commit_range_clean=False)
    assert not credential_policy(diff_only=True)


def test_resolve_public_host_rejects_rebinding_to_private(monkeypatch):
    monkeypatch.setattr(
        integrity_ping.socket,
        "getaddrinfo",
        lambda *args, **kwargs: [
            (None, None, None, None, ("93.184.216.34", 443)),
            (None, None, None, None, ("10.0.0.1", 443)),
        ],
    )

    with pytest.raises(RuntimeError, match="unsafe resolved IP"):
        integrity_ping.resolve_public_host("example.com")


def test_resolve_public_host_accepts_stable_public(monkeypatch):
    monkeypatch.setattr(
        integrity_ping.socket,
        "getaddrinfo",
        lambda *args, **kwargs: [(None, None, None, None, ("93.184.216.34", 443))],
    )

    assert integrity_ping.resolve_public_host("example.com") == ["93.184.216.34"]


def test_ipv4_mapped_ipv6_private_is_blocked():
    assert not integrity_ping.is_safe_public_ip("::ffff:127.0.0.1")
    assert not integrity_ping.is_safe_public_ip("169.254.169.254")
    assert not integrity_ping.is_safe_public_ip("100.64.0.1")


def test_non_default_https_port_is_blocked(monkeypatch):
    monkeypatch.setattr(integrity_ping, "resolve_public_host", lambda host: ["8.8.8.8"])

    assert not integrity_ping.is_safe_public_url("https://safe.test.edu:8443/start")
    assert not integrity_ping.is_safe_public_url("https://safe.test.edu:bad/start")


def test_fetch_redirect_revalidates_each_hop(monkeypatch):
    resolutions = []

    def resolve(host):
        resolutions.append(host)
        if host == "safe.test.edu":
            return ["8.8.8.8"]
        raise RuntimeError("unsafe resolved IP for unsafe.test.edu")

    calls = []

    def request(url, method="HEAD", timeout=10):
        calls.append(url)
        return integrity_ping.PinnedHTTPResponse(
            302,
            {"Location": "https://unsafe.test.edu/program"},
            url,
        )

    monkeypatch.setattr(integrity_ping, "resolve_public_host", resolve)
    monkeypatch.setattr(integrity_ping, "request_pinned_public_url", request)

    with pytest.raises(RuntimeError, match="unsafe"):
        integrity_ping.fetch_public_url("https://safe.test.edu/start")
    assert calls == ["https://safe.test.edu/start"]
    assert resolutions == ["safe.test.edu", "unsafe.test.edu"]


def test_fetch_safe_redirect_finishes(monkeypatch):
    monkeypatch.setattr(integrity_ping, "resolve_public_host", lambda host: ["8.8.8.8"])
    responses = iter([
        integrity_ping.PinnedHTTPResponse(302, {"Location": "/final"}, "https://safe.test.edu/start"),
        integrity_ping.PinnedHTTPResponse(200, {}, "https://safe.test.edu/final"),
    ])
    monkeypatch.setattr(
        integrity_ping,
        "request_pinned_public_url",
        lambda url, method="HEAD", timeout=10: next(responses),
    )

    response = integrity_ping.fetch_public_url("https://safe.test.edu/start")

    assert response.status_code == 200
    assert response.url == "https://safe.test.edu/final"


def test_lowercase_redirect_header_is_followed(monkeypatch):
    monkeypatch.setattr(integrity_ping, "resolve_public_host", lambda host: ["8.8.8.8"])
    responses = iter([
        integrity_ping.PinnedHTTPResponse(302, {"location": "/final"}, "https://safe.test.edu/start"),
        integrity_ping.PinnedHTTPResponse(200, {}, "https://safe.test.edu/final"),
    ])
    monkeypatch.setattr(
        integrity_ping,
        "request_pinned_public_url",
        lambda url, method="HEAD", timeout=10: next(responses),
    )

    assert integrity_ping.fetch_public_url("https://safe.test.edu/start").status_code == 200


def test_fixed_ip_connection_rejects_peer_mismatch(monkeypatch):
    class FakeRawSocket:
        def getpeername(self):
            return ("93.184.216.35", 443)

        def close(self):
            self.closed = True

    monkeypatch.setattr(
        integrity_ping.socket,
        "create_connection",
        lambda *args, **kwargs: FakeRawSocket(),
    )
    connection = integrity_ping.FixedIPHTTPSConnection(
        "example.com",
        fixed_ip="93.184.216.34",
        context=integrity_ping.ssl.create_default_context(),
    )

    with pytest.raises(RuntimeError, match="peer"):
        connection.connect()


def test_fixed_ip_connection_preserves_tls_hostname(monkeypatch):
    class FakeRawSocket:
        def getpeername(self):
            return ("93.184.216.34", 443)

    class FakeContext:
        def __init__(self):
            self.server_hostname = None
            self.verify_mode = integrity_ping.ssl.CERT_REQUIRED
            self.check_hostname = True

        def wrap_socket(self, sock, server_hostname=None):
            self.server_hostname = server_hostname
            return sock

    context = FakeContext()
    monkeypatch.setattr(
        integrity_ping.socket,
        "create_connection",
        lambda *args, **kwargs: FakeRawSocket(),
    )
    connection = integrity_ping.FixedIPHTTPSConnection(
        "example.com",
        fixed_ip="93.184.216.34",
        context=context,
    )

    connection.connect()

    assert context.server_hostname == "example.com"


class FakeResponse:
    def __init__(self, status_code, payload=None, content=b"[]"):
        self.status_code = status_code
        self._payload = payload
        self.content = content
        self.text = content.decode("utf-8", "ignore") if isinstance(content, bytes) else str(content)

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


def client_with_patch(monkeypatch, response):
    client_class = getattr(db_client, "Database" + "Client")
    client = client_class(
        "https://db.example",
        db_client.SECRET_KEY_PREFIX + "a" * 24,
    )
    captured = {}

    def fake_request(method, url, **kwargs):
        captured["method"] = method
        captured["url"] = url
        captured["headers"] = kwargs["headers"]
        return response

    monkeypatch.setattr(db_client, "_request_with_retry", fake_request)
    return client, captured


def test_patch_exact_one_success(monkeypatch):
    client, captured = client_with_patch(monkeypatch, FakeResponse(200, [{"id": "course-id"}]))

    row = client.patch_exact_one_raise("courses", "id=eq.course-id", {"is_active": False}, "course-id")

    assert row == {"id": "course-id"}
    assert captured["headers"]["Prefer"] == "return=representation"
    assert "id=eq.course-id" in captured["url"]


@pytest.mark.parametrize(
    ("response", "match"),
    [
        (FakeResponse(204, None, b""), "HTTP 204"),
        (FakeResponse(200, ValueError("bad"), b"not-json"), "invalid JSON"),
        (FakeResponse(200, [], b"[]"), "exactly one"),
        (FakeResponse(200, [{"id": "a"}, {"id": "b"}]), "exactly one"),
        (FakeResponse(200, [{"id": "other"}]), "unexpected id"),
    ],
)
def test_patch_exact_one_fail_closed(monkeypatch, response, match):
    client, _ = client_with_patch(monkeypatch, response)

    with pytest.raises(db_client.DatabaseAPIError, match=match):
        client.patch_exact_one_raise("courses", "id=eq.course-id", {"is_active": False}, "course-id")


def test_patch_course_exact_one_does_not_select_first():
    class FakeDB:
        def __init__(self):
            self.selected = False
            self.patched = False

        def select_service_raise(self, *args, **kwargs):
            self.selected = True
            raise AssertionError("SELECT must not be used for exact-one patch")

        def patch_exact_one_raise(self, *args, **kwargs):
            self.patched = True
            return {"id": "course-id"}

    fake = FakeDB()
    integrity_ping.patch_course_exact_one(fake, "course-id", {"is_active": False})

    assert fake.patched is True
    assert fake.selected is False
