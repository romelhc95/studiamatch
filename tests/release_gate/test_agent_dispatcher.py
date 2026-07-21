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


def _write_task(path: Path, *, estado="aprobada", hito="Hito 2", skill="pipeline-engineer"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""---
id: TAREA-123
fase: 02
estado: {estado}
hito: {hito}
skill_principal: {skill}
skills_apoyo: security-auditor, qa-test-engineer
gate_obligatorio: security-auditor
---

# Tarea 123

## Archivos afectados
| Archivo | Tipo de cambio |
|---|---|
| `scripts/core/sync_vector_worker.py` | Modificacion |
| `tests/release_gate/test_agent_dispatcher.py` | Test |
""",
        encoding="utf-8",
    )


def test_implementation_mode_routes_approved_task_to_roles(tmp_path):
    task = tmp_path / ".context/backlog_tareas/tarea_123.md"
    _write_task(task)

    result = agent_dispatcher.dispatch_implementation(
        task,
        approved_hito="Hito 2",
        repo_root=tmp_path,
        changed_files=["scripts/core/sync_vector_worker.py"],
    )

    assert result["verdict"] == "PASS"
    assert result["mode"] == "implementation"
    assert result["approved_scope"] == "Hito 2"
    assert result["primary_agent"] == "pipeline-engineer"
    assert "security-auditor" in result["implementation_roles"]
    assert "python-py_compile" in result["required_checks"]
    assert "security-audit" in result["required_checks"]


def test_implementation_mode_rejects_unapproved_task(tmp_path):
    task = tmp_path / ".context/backlog_tareas/tarea_123.md"
    _write_task(task, estado="pendiente")

    with pytest.raises(agent_dispatcher.DispatcherError, match="Tarea no aprobada"):
        agent_dispatcher.dispatch_implementation(task, approved_hito="Hito 2", repo_root=tmp_path)


def test_implementation_mode_rejects_wrong_hito(tmp_path):
    task = tmp_path / ".context/backlog_tareas/tarea_123.md"
    _write_task(task, hito="Hito 3")

    with pytest.raises(agent_dispatcher.DispatcherError, match="Hito no autorizado"):
        agent_dispatcher.dispatch_implementation(task, approved_hito="Hito 2", repo_root=tmp_path)


def test_implementation_mode_rejects_changed_files_outside_task_scope(tmp_path):
    task = tmp_path / ".context/backlog_tareas/tarea_123.md"
    _write_task(task)

    with pytest.raises(agent_dispatcher.DispatcherError, match="fuera del alcance aprobado"):
        agent_dispatcher.dispatch_implementation(
            task,
            approved_hito="Hito 2",
            repo_root=tmp_path,
            changed_files=["web/src/app/page.tsx"],
        )


def test_implementation_mode_respects_frontend_task_role(tmp_path):
    task = tmp_path / ".context/backlog_tareas/tarea_123.md"
    _write_task(task, skill="frontend-architect")

    result = agent_dispatcher.dispatch_implementation(task, approved_hito="Hito 2", repo_root=tmp_path)

    assert result["primary_agent"] == "frontend-architect"
    assert "qa-test-engineer" in result["implementation_roles"]


def test_implementation_mode_ignores_backticks_outside_affected_files(tmp_path):
    task = tmp_path / ".context/backlog_tareas/tarea_123.md"
    _write_task(task)
    content = task.read_text(encoding="utf-8")
    task.write_text(
        content.replace("# Tarea 123", "# Tarea 123\n\nReferencia no autorizante: `web/src/app/page.tsx`"),
        encoding="utf-8",
    )

    with pytest.raises(agent_dispatcher.DispatcherError, match="fuera del alcance aprobado"):
        agent_dispatcher.dispatch_implementation(
            task,
            approved_hito="Hito 2",
            repo_root=tmp_path,
            changed_files=["web/src/app/page.tsx"],
        )


def test_implementation_mode_normalizes_changed_files_when_used_as_api(tmp_path):
    task = tmp_path / ".context/backlog_tareas/tarea_123.md"
    _write_task(task)

    with pytest.raises(agent_dispatcher.DispatcherError, match="Path no canonico"):
        agent_dispatcher.dispatch_implementation(
            task,
            approved_hito="Hito 2",
            repo_root=tmp_path,
            changed_files=["scripts/core/../shared/db_client.py"],
        )


def test_implementation_mode_rejects_task_outside_backlog(tmp_path):
    task = tmp_path / "task.md"
    _write_task(task)

    with pytest.raises(agent_dispatcher.DispatcherError, match="backlog_tareas"):
        agent_dispatcher.dispatch_implementation(task, approved_hito="Hito 2", repo_root=tmp_path)


def test_implementation_mode_wraps_malformed_frontmatter(tmp_path):
    task = tmp_path / ".context/backlog_tareas/tarea_123.md"
    task.parent.mkdir(parents=True, exist_ok=True)
    task.write_text("---\nestado: aprobada\n", encoding="utf-8")

    with pytest.raises(agent_dispatcher.DispatcherError, match="Frontmatter"):
        agent_dispatcher.dispatch_implementation(task, approved_hito="Hito 2", repo_root=tmp_path)
