import hashlib
import io
import json
import zipfile
from pathlib import Path

import pytest

from scripts.maintenance import release_gate


PASS_EVENTS = [
    "DEVELOPER_SUBMIT", "QA_PASS", "SECURITY_PASS", "DATABASE_PASS", "PIPELINE_PASS",
    "WRITERS_PAUSE", "FREE_CANARY_PASS", "FREE_PASS", "AUTHORIZE_PRODUCTION",
    "PRODUCTION_APPLY", "PRODUCTION_CANARY_PASS", "PRODUCTION_PASS", "AUTHORIZE_RESUME",
    "RELEASE_READY", "PROMOTE",
]


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


def _build_chain(root: Path, events: list[str], actor_overrides=None):
    actor_overrides = actor_overrides or {}
    state = "DRAFT"
    entries = []
    for sequence, event in enumerate(events, start=1):
        next_state, role = release_gate.TRANSITIONS[(state, event)]
        kind = actor_overrides.get(event, "human" if event in release_gate.HUMAN_EVENTS else "agent")
        is_run_backed = event in release_gate.HUMAN_EVENTS | release_gate.CI_EVENTS
        evidence = {
            "schema_version": 1,
            "release_id": "test-release",
            "revision": 1,
            "candidate_commit": "a" * 40,
            "sequence": sequence,
            "role": role,
            "actor": {"id": f"{role}-actor", "kind": kind},
            "provenance": {
                "source": (
                    "github-environment" if event in release_gate.HUMAN_EVENTS
                    else "github-actions" if event in release_gate.CI_EVENTS
                    else "opencode"
                ),
                "repository": "romelhc95/studiamatch",
                "run_id": "12345" if is_run_backed else None,
                "commit": "a" * 40 if is_run_backed else None,
                "workflow": release_gate.EVENT_WORKFLOWS.get(event),
                "artifact_name": f"test-artifact-{sequence}" if is_run_backed else None,
                "artifact_file": "evidence.json" if is_run_backed else None,
            },
            "event": event,
            "verdict": "PASS",
            "checks": [
                {"id": check_id, "status": "PASS", "evidence": f"proof for {check_id}"}
                for check_id in sorted(release_gate.REQUIRED_PASS_CHECKS[event])
            ],
            "findings": [],
            "handoff": {"to_role": release_gate.NEXT_ROLE[next_state], "reason": "next gate"},
            "created_at": f"2026-07-19T00:{sequence:02d}:00Z",
        }
        rel_path = f".context/evidencias/test-{sequence}.json"
        checksum = _write_json(root / rel_path, evidence)
        entries.append({"path": rel_path, "sha256": checksum})
        state = next_state
    manifest = _base_manifest(state, entries)
    path = _manifest_path(root)
    _write_json(path, manifest)
    return path, state


def test_draft_is_only_a_structurally_valid_release(tmp_path):
    path = _manifest_path(tmp_path)
    _write_json(path, _base_manifest())
    result = release_gate.validate_release(path, "structure", root=tmp_path)
    assert result["state"] == "DRAFT"
    assert result["validation"] == "structure"
    with pytest.raises(release_gate.GateError, match="no habilita stage development"):
        release_gate.validate_release(path, "development", root=tmp_path)


def test_full_chain_is_required_for_release(tmp_path, monkeypatch):
    path, state = _build_chain(tmp_path, PASS_EVENTS)
    monkeypatch.setenv("RELEASE_CANDIDATE_SHA", "a" * 40)
    assert state == "RELEASED"
    assert release_gate.validate_release(path, "release", root=tmp_path)["state"] == "RELEASED"


def test_release_stage_rejects_ready_for_human_decision(tmp_path, monkeypatch):
    path, state = _build_chain(tmp_path, PASS_EVENTS[:-1])
    monkeypatch.setenv("RELEASE_CANDIDATE_SHA", "a" * 40)
    assert state == "READY_FOR_HUMAN_DECISION"
    with pytest.raises(release_gate.GateError, match="no habilita stage release"):
        release_gate.validate_release(path, "release", root=tmp_path)


def test_human_event_rejects_agent_actor(tmp_path, monkeypatch):
    path, _ = _build_chain(
        tmp_path,
        PASS_EVENTS[:9],
        actor_overrides={"AUTHORIZE_PRODUCTION": "agent"},
    )
    monkeypatch.setenv("RELEASE_CANDIDATE_SHA", "a" * 40)
    with pytest.raises(release_gate.GateError, match="requiere un actor humano"):
        release_gate.validate_release(path, "structure", root=tmp_path)


def test_pass_requires_canonical_checks(tmp_path, monkeypatch):
    path, _ = _build_chain(tmp_path, ["DEVELOPER_SUBMIT"])
    evidence_path = tmp_path / ".context/evidencias/test-1.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    evidence["checks"] = [{"id": "anything", "status": "NOT_APPLICABLE", "evidence": "n/a"}]
    checksum = _write_json(evidence_path, evidence)
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["evidence"][0]["sha256"] = checksum
    _write_json(path, manifest)
    monkeypatch.setenv("RELEASE_CANDIDATE_SHA", "a" * 40)
    with pytest.raises(release_gate.GateError, match="carece de checks PASS"):
        release_gate.validate_release(path, "structure", root=tmp_path)


def test_no_go_requires_developer_handoff(tmp_path, monkeypatch):
    evidence = {
        "schema_version": 1,
        "release_id": "test-release",
        "revision": 1,
        "candidate_commit": "a" * 40,
        "sequence": 1,
        "role": "security-auditor",
        "actor": {"id": "security-1", "kind": "agent"},
        "provenance": {
            "source": "opencode",
            "repository": "romelhc95/studiamatch",
            "run_id": None,
            "commit": None,
            "workflow": None,
            "artifact_name": None,
            "artifact_file": None,
        },
        "event": "GATE_FAIL",
        "verdict": "NO_GO",
        "checks": [{"id": "scan", "status": "FAIL", "evidence": "failure"}],
        "findings": [{"severity": "high", "summary": "blocking"}],
        "handoff": {"to_role": "qa-test-engineer", "reason": "wrong handoff"},
        "created_at": "2026-07-19T00:00:00Z",
    }
    rel_path = ".context/evidencias/fail.json"
    checksum = _write_json(tmp_path / rel_path, evidence)
    manifest = _base_manifest("NO_GO", [{"path": rel_path, "sha256": checksum}])
    path = _manifest_path(tmp_path)
    _write_json(path, manifest)
    monkeypatch.setenv("RELEASE_CANDIDATE_SHA", "a" * 40)
    with pytest.raises(release_gate.GateError, match="handoff a developer"):
        release_gate.validate_release(path, "structure", root=tmp_path)


def test_pro_migration_must_also_target_free(tmp_path):
    migration = tmp_path / "db/migrations/test.sql"
    migration.parent.mkdir(parents=True)
    migration.write_text("select 1;", encoding="utf-8")
    manifest = _base_manifest()
    manifest["migrations"] = [{
        "path": "db/migrations/test.sql",
        "sha256": hashlib.sha256(migration.read_bytes()).hexdigest(),
        "transactional": True,
        "targets": ["pro"],
        "postconditions": [{"id": "object-exists", "sql": "SELECT true", "expected": True}],
        "rollback": {"strategy": "forward_fix", "instructions": "apply corrective migration"},
    }]
    path = _manifest_path(tmp_path)
    _write_json(path, manifest)
    with pytest.raises(release_gate.GateError, match="certificarse primero en Free"):
        release_gate.validate_release(path, "structure", root=tmp_path)


def test_schema_rejects_additional_properties(tmp_path):
    manifest = _base_manifest()
    manifest["self_approved"] = True
    path = _manifest_path(tmp_path)
    _write_json(path, manifest)
    with pytest.raises(release_gate.GateError, match="Schema invalido"):
        release_gate.validate_release(path, "structure", root=tmp_path)


def test_manifest_must_use_canonical_release_path(tmp_path):
    path = tmp_path / "manifest.json"
    _write_json(path, _base_manifest())
    with pytest.raises(release_gate.GateError, match="path canonico"):
        release_gate.validate_release(path, "structure", root=tmp_path)


def test_github_provenance_is_verified_against_run_api(monkeypatch):
    evidence = {
        "verdict": "PASS",
        "provenance": {
            "source": "github-actions",
            "repository": "romelhc95/studiamatch",
            "run_id": "12345",
            "commit": "a" * 40,
            "workflow": ".github/workflows/pipeline-canary.yml",
            "artifact_name": "pipeline-canary-test",
            "artifact_file": "evidence.json",
        }
    }

    class Response:
        def __init__(self, payload=None, content=b""):
            self.status_code = 200
            self._payload = payload
            self.content = content

        def json(self):
            return self._payload

    archive_buffer = io.BytesIO()
    with zipfile.ZipFile(archive_buffer, "w") as archive:
        archive.writestr("evidence.json", json.dumps(evidence))

    def fake_get(url, **_kwargs):
        if url.endswith("/12345"):
            return Response({
                "repository": {"full_name": "romelhc95/studiamatch"},
                "head_sha": "a" * 40,
                "conclusion": "success",
                "path": ".github/workflows/pipeline-canary.yml",
            })
        if "artifacts?" in url:
            return Response({
                "artifacts": [{
                    "name": "pipeline-canary-test",
                    "expired": False,
                    "archive_download_url": "https://api.github.com/artifact.zip",
                }]
            })
        return Response(content=archive_buffer.getvalue())

    monkeypatch.setattr(release_gate.requests, "get", fake_get)
    release_gate.verify_github_provenance([evidence], "token")
    evidence["provenance"]["workflow"] = ".github/workflows/other.yml"
    with pytest.raises(release_gate.GateError, match="provenance invalido"):
        release_gate.verify_github_provenance([evidence], "token")
