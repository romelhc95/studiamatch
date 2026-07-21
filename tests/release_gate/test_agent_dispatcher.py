import hashlib
import json
from pathlib import Path

import pytest

from scripts.maintenance import agent_dispatcher, release_gate


def _write_json(path: Path, value: dict) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _base_manifest(state="DRAFT", evidence=None):
    return {
        "schema_version": 1,
        "release_id": "test-release",
        "state": state,
        "revision": 1,
        "candidate_commit": None if state == "DRAFT" else "a" * 40,
        "previous_manifest": None,
        "migrations": [],
        "evidence": evidence or [],
    }


def _manifest_path(root: Path) -> Path:
    return root / ".context/evidencias/releases/test-release/release-manifest.json"


def _build_chain(root: Path, events: list[str]):
    state = "DRAFT"
    entries = []
    for sequence, event in enumerate(events, start=1):
        next_state, role = release_gate.TRANSITIONS[(state, event)]
        evidence = {
            "schema_version": 1,
            "release_id": "test-release",
            "revision": 1,
            "candidate_commit": "a" * 40,
            "sequence": sequence,
            "role": role,
            "actor": {"id": f"{role}-actor", "kind": "agent"},
            "provenance": {
                "source": "opencode",
                "repository": "romelhc95/studiamatch",
                "run_id": None,
                "commit": None,
                "workflow": None,
                "artifact_name": None,
                "artifact_file": None,
            },
            "event": event,
            "verdict": "PASS",
            "checks": [
                {"id": check_id, "status": "PASS", "evidence": f"proof for {check_id}"}
                for check_id in sorted(release_gate.REQUIRED_PASS_CHECKS[event])
            ],
            "findings": [],
            "handoff": {"to_role": release_gate.NEXT_ROLE[next_state], "reason": "next gate"},
            "created_at": f"2026-07-20T00:{sequence:02d}:00Z",
        }
        rel_path = f".context/evidencias/test-{sequence}.json"
        checksum = _write_json(root / rel_path, evidence)
        entries.append({"path": rel_path, "sha256": checksum})
        state = next_state
    path = _manifest_path(root)
    _write_json(path, _base_manifest(state, entries))
    return path


def test_dispatcher_uses_release_gate_next_role(tmp_path):
    manifest = _manifest_path(tmp_path)
    _write_json(manifest, _base_manifest())

    result = agent_dispatcher.dispatch(
        manifest,
        repo_root=tmp_path,
        changed_files=["web/src/app/page.tsx"],
    )

    assert result["verdict"] == "PASS"
    assert result["derived_state"] == "DRAFT"
    assert result["next_event"] == "DEVELOPER_SUBMIT"
    assert result["next_role"] == "developer"
    assert result["recommended_agent"] == "general"
    assert "frontend-architect" in result["support_agents"]
    assert result["required_checks"] == ["implementation-tests"]


def test_dispatcher_adds_security_support_for_sensitive_paths(tmp_path, monkeypatch):
    manifest = _build_chain(tmp_path, ["DEVELOPER_SUBMIT", "QA_PASS"])
    monkeypatch.setenv("RELEASE_CANDIDATE_SHA", "a" * 40)

    result = agent_dispatcher.dispatch(
        manifest,
        repo_root=tmp_path,
        changed_files=["db/migrations/20260720_test.sql"],
    )

    assert result["derived_state"] == "QA_VALIDATED"
    assert result["next_role"] == "security-auditor"
    assert result["recommended_agent"] == "security-auditor"
    assert "supabase" in result["domains"]
    assert result["required_checks"] == ["security-audit"]


def test_dispatcher_fails_closed_on_invalid_manifest(tmp_path):
    manifest = _manifest_path(tmp_path)
    _write_json(manifest, {"schema_version": 1})

    with pytest.raises(release_gate.GateError):
        agent_dispatcher.dispatch(manifest, repo_root=tmp_path)


def test_changed_files_loader_normalizes_paths(tmp_path):
    changed = tmp_path / "changed.txt"
    changed.write_text(".\\web\\src\\app\\page.tsx\n\n./scripts/core/sync.py\n", encoding="utf-8")

    assert agent_dispatcher._load_changed_files(["db/migrations/test.sql"], changed) == [
        "db/migrations/test.sql",
        "scripts/core/sync.py",
        "web/src/app/page.tsx",
    ]


@pytest.mark.parametrize("path", [
    "../outside.py",
    "web/../db/migrations/x.sql",
    "/absolute/path.py",
    "C:/Users/Romel/secret.py",
])
def test_changed_files_loader_rejects_non_canonical_paths(path):
    with pytest.raises(agent_dispatcher.DispatcherError, match="Path no canonico"):
        agent_dispatcher._load_changed_files([path], None)
