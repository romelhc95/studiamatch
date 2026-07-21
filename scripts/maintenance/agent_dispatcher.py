"""Suggest the next SDLC agent from the deterministic release gate state."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from . import release_gate
except ImportError:
    import release_gate


ROLE_AGENTS = {
    "developer": "general",
    "qa-test-engineer": "qa-test-engineer",
    "security-auditor": "security-auditor",
    "supabase-architect": "supabase-architect",
    "pipeline-engineer": "pipeline-engineer",
    "devops-release-manager": "devops-release-manager",
    "human-approver": "human-approver",
    "none": "none",
}

DOMAIN_RULES = [
    ("frontend", ("web/",), "frontend-architect"),
    ("supabase", ("db/migrations/", "db/nontransactional/", "db/operations/"), "supabase-architect"),
    ("pipeline", ("scripts/core/",), "pipeline-engineer"),
    ("devops", (".github/workflows/", ".github/", "docker", ".docker"), "devops-release-manager"),
    ("release-governance", ("scripts/maintenance/", "schemas/", ".context/evidencias/releases/"), "qa-test-engineer"),
    ("documentation", (".context/", "AGENTS.md", "IMPLEMENTATION_PLAN.md"), "qa-test-engineer"),
]

SECURITY_SENSITIVE_PREFIXES = (
    ".github/workflows/",
    "db/migrations/",
    "db/nontransactional/",
    "db/operations/",
    "scripts/shared/db_client.py",
    "scripts/core/",
    "scripts/maintenance/db_migrate.py",
    "scripts/maintenance/pipeline_canary.py",
    "scripts/maintenance/release_gate.py",
    "scripts/maintenance/agent_dispatcher.py",
    "schemas/",
)

NEXT_EVENT_BY_STATE = {
    state: event
    for (state, event), (_next_state, _role) in release_gate.TRANSITIONS.items()
}


class DispatcherError(ValueError):
    pass


def _normalize_path(value: str) -> str:
    path = value.strip().replace("\\", "/")
    while path.startswith("./"):
        path = path[2:]
    parts = [part for part in path.split("/") if part]
    if not path or path.startswith("/") or ":" in parts[0] or ".." in parts:
        raise DispatcherError(f"Path no canonico: {value}")
    return "/".join(parts)


def _load_changed_files(paths: list[str], changed_files_path: Path | None) -> list[str]:
    files = [_normalize_path(path) for path in paths if path.strip()]
    if changed_files_path:
        try:
            files.extend(
                _normalize_path(line)
                for line in changed_files_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            )
        except OSError as exc:
            raise DispatcherError(f"No se pudo leer changed files: {exc}") from exc
    return sorted(set(files))


def classify_domains(changed_files: list[str]) -> dict[str, list[str]]:
    domains: dict[str, list[str]] = {}
    for path in changed_files:
        matched = False
        for domain, prefixes, _agent in DOMAIN_RULES:
            if any(path == prefix.rstrip("/") or path.startswith(prefix) for prefix in prefixes):
                domains.setdefault(domain, []).append(path)
                matched = True
        if not matched:
            domains.setdefault("unknown", []).append(path)
    return domains


def _domain_support_agents(domains: dict[str, list[str]]) -> list[str]:
    agents = {
        agent
        for domain, _prefixes, agent in DOMAIN_RULES
        if domain in domains
    }
    return sorted(agents)


def _requires_security(changed_files: list[str]) -> bool:
    return any(
        any(path == prefix.rstrip("/") or path.startswith(prefix) for prefix in SECURITY_SENSITIVE_PREFIXES)
        for path in changed_files
    )


def dispatch(
    manifest_path: Path,
    stage: str = "structure",
    repo_root: Path = release_gate.DEFAULT_ROOT,
    changed_files: list[str] | None = None,
    verify_github_provenance: bool = False,
) -> dict:
    gate = release_gate.validate_release(
        manifest_path,
        stage,
        root=repo_root,
        verify_provenance=verify_github_provenance,
    )
    state = gate["state"]
    next_role = gate["next_role"]
    if next_role not in ROLE_AGENTS:
        raise DispatcherError(f"Rol siguiente no soportado: {next_role}")

    files = sorted(set(changed_files or []))
    domains = classify_domains(files)
    recommended_agent = ROLE_AGENTS[next_role]
    next_event = NEXT_EVENT_BY_STATE.get(state)
    required_checks = sorted(release_gate.REQUIRED_PASS_CHECKS.get(next_event, set())) if next_event else []
    support_agents = _domain_support_agents(domains)
    if _requires_security(files) and "security-auditor" not in support_agents:
        support_agents.append("security-auditor")
    support_agents = sorted(agent for agent in set(support_agents) if agent != recommended_agent)

    return {
        "verdict": "PASS",
        "release_id": gate["release_id"],
        "revision": gate["revision"],
        "derived_state": state,
        "next_event": next_event,
        "next_role": next_role,
        "recommended_agent": recommended_agent,
        "support_agents": support_agents,
        "domains": domains,
        "required_checks": required_checks,
        "evidence_schema": "schemas/role-evidence.schema.json",
        "manifest_sha256": gate["manifest_sha256"],
        "notes": [
            "release_gate.py is the source of truth",
            "dispatcher does not authorize human events, merges, Pro, or release",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--stage", choices=sorted(release_gate.STAGE_STATES), default="structure")
    parser.add_argument("--repo-root", type=Path, default=release_gate.DEFAULT_ROOT)
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument("--changed-files", type=Path)
    parser.add_argument("--verify-github-provenance", action="store_true")
    args = parser.parse_args()
    try:
        changed_files = _load_changed_files(args.changed_file, args.changed_files)
        result = dispatch(
            args.manifest,
            stage=args.stage,
            repo_root=args.repo_root,
            changed_files=changed_files,
            verify_github_provenance=args.verify_github_provenance,
        )
    except (DispatcherError, release_gate.GateError, OSError, KeyError, TypeError) as exc:
        print(json.dumps({"verdict": "NO_GO", "handoff": "developer", "reason": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
