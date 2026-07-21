"""Route SDLC review and implementation work to the right agent roles."""

from __future__ import annotations

import argparse
import json
import re
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

IMPLEMENTATION_AGENTS = set(ROLE_AGENTS.values()) | {
    "frontend-architect",
    "data-quality-analyst",
    "data-analyst",
    "accessibility",
    "seo",
    "general",
}

IMPLEMENTATION_STATES = {"aprobada", "aprobado", "approved", "en_ejecucion", "en ejecución"}
TASK_ROLE_KEYS = ("skill_principal", "revisor", "gate_obligatorio")

DOMAIN_RULES = [
    ("frontend", ("web/",), "frontend-architect"),
    ("supabase", ("db/migrations/", "db/nontransactional/", "db/operations/"), "supabase-architect"),
    ("pipeline", ("scripts/core/",), "pipeline-engineer"),
    ("devops", (".github/workflows/", ".github/", "docker", ".docker"), "devops-release-manager"),
    ("data-quality", ("scripts/maintenance/quality_", "scripts/maintenance/taxonomy_", "scripts/maintenance/category_"), "data-quality-analyst"),
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


def _read_task(task_path: Path) -> tuple[dict[str, str], str]:
    try:
        content = task_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise DispatcherError(f"No se pudo leer tarea: {exc}") from exc
    frontmatter: dict[str, str] = {}
    if content.startswith("---"):
        try:
            _, raw_frontmatter, _body = content.split("---", 2)
        except ValueError as exc:
            raise DispatcherError("Frontmatter de tarea invalido") from exc
        for line in raw_frontmatter.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            frontmatter[key.strip()] = value.strip().strip('"')
    return frontmatter, content


def _extract_task_paths(content: str) -> list[str]:
    section = re.search(
        r"(?ims)^##\s+Archivos afectados\s*$([\s\S]*?)(?=^##\s+|\Z)",
        content,
    )
    if not section:
        return []
    paths = []
    for value in re.findall(r"`([^`]+)`", section.group(1)):
        if value.startswith("[") or value.endswith("]") or " " in value:
            continue
        if any(value.startswith(prefix) for prefix in ("web/", "scripts/", "db/", ".context/", ".github/", "schemas/", "tests/")):
            paths.append(_normalize_path(value))
    return sorted(set(paths))


def _canonical_task_path(task_path: Path, repo_root: Path) -> Path:
    root = repo_root.resolve()
    path = task_path.resolve()
    try:
        relative = path.relative_to(root).as_posix()
    except ValueError as exc:
        raise DispatcherError("La tarea debe estar dentro del repositorio") from exc
    if not re.fullmatch(r"\.context/backlog_tareas/[A-Za-z0-9_.-]+/tarea_[0-9]{3}_[A-Za-z0-9_.-]+\.md", relative):
        raise DispatcherError("La tarea debe estar en .context/backlog_tareas/<requerimiento>/")
    return path


def _role_from_task(frontmatter: dict[str, str]) -> str | None:
    for key in TASK_ROLE_KEYS:
        value = frontmatter.get(key, "").strip()
        if value in IMPLEMENTATION_AGENTS:
            return value
    return None


def _support_agents_from_task(frontmatter: dict[str, str]) -> list[str]:
    raw_values = [frontmatter.get("skills_apoyo", ""), frontmatter.get("gate_obligatorio", "")]
    agents = []
    for raw_value in raw_values:
        for value in re.split(r"[,;]", raw_value):
            agent = value.strip().strip("[]")
            if agent in IMPLEMENTATION_AGENTS:
                agents.append(agent)
    return sorted(set(agents))


def _files_outside_task_scope(changed_files: list[str], task_paths: list[str]) -> list[str]:
    if not task_paths:
        return []
    outside = []
    for path in changed_files:
        if not any(path == task_path or path.startswith(f"{task_path.rstrip('/')}/") for task_path in task_paths):
            outside.append(path)
    return outside


def _required_implementation_checks(domains: dict[str, list[str]], requires_security: bool) -> list[str]:
    checks = {"scope-approved"}
    if "frontend" in domains:
        checks.update({"eslint", "typescript-typecheck"})
    if "pipeline" in domains or "release-governance" in domains:
        checks.update({"python-py_compile", "release-gate-tests"})
    if "supabase" in domains:
        checks.update({"schema-review", "rls-review"})
    if "devops" in domains:
        checks.add("workflow-review")
    if "documentation" in domains:
        checks.add("docs-review")
    if requires_security:
        checks.add("security-audit")
    return sorted(checks)


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

    files = _load_changed_files(changed_files or [], None)
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


def dispatch_implementation(
    task_path: Path,
    approved_hito: str,
    repo_root: Path = release_gate.DEFAULT_ROOT,
    changed_files: list[str] | None = None,
) -> dict:
    task_path = _canonical_task_path(task_path, repo_root)
    frontmatter, content = _read_task(task_path)
    task_state = frontmatter.get("estado", "").strip().lower()
    task_hito = frontmatter.get("hito", "").strip()
    if task_state not in IMPLEMENTATION_STATES:
        raise DispatcherError(f"Tarea no aprobada para implementacion: estado={task_state or 'sin_estado'}")
    if not task_hito or task_hito != approved_hito:
        raise DispatcherError(f"Hito no autorizado: tarea={task_hito or 'sin_hito'}, aprobado={approved_hito}")

    files = _load_changed_files(changed_files or [], None)
    task_paths = _extract_task_paths(content)
    outside_scope = _files_outside_task_scope(files, task_paths)
    if outside_scope:
        raise DispatcherError(f"Archivos fuera del alcance aprobado: {', '.join(outside_scope)}")

    domains = classify_domains(files or task_paths)
    support_agents = _domain_support_agents(domains)
    primary_agent = _role_from_task(frontmatter) or (support_agents[0] if support_agents else "general")
    support_agents.extend(_support_agents_from_task(frontmatter))
    requires_security = _requires_security(files or task_paths)
    if requires_security and "security-auditor" not in support_agents:
        support_agents.append("security-auditor")
    implementation_roles = sorted({primary_agent, *support_agents})

    return {
        "verdict": "PASS",
        "mode": "implementation",
        "task": str(task_path).replace("\\", "/"),
        "approved_scope": approved_hito,
        "task_state": task_state,
        "primary_agent": primary_agent,
        "implementation_roles": implementation_roles,
        "support_agents": sorted(agent for agent in set(support_agents) if agent != primary_agent),
        "domains": domains,
        "declared_task_paths": task_paths,
        "required_checks": _required_implementation_checks(domains, requires_security),
        "forbidden_scope": ["otros hitos", "produccion", "supabase-pro", "main"],
        "notes": [
            "implementation routing is limited to the approved task and hito",
            "dispatcher does not create scope, approve estimates, or authorize release",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["review", "implementation"], default="review")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--task", type=Path)
    parser.add_argument("--approved-hito")
    parser.add_argument("--stage", choices=sorted(release_gate.STAGE_STATES), default="structure")
    parser.add_argument("--repo-root", type=Path, default=release_gate.DEFAULT_ROOT)
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument("--changed-files", type=Path)
    parser.add_argument("--verify-github-provenance", action="store_true")
    args = parser.parse_args()
    try:
        changed_files = _load_changed_files(args.changed_file, args.changed_files)
        if args.mode == "review":
            if not args.manifest:
                raise DispatcherError("--manifest es obligatorio en mode=review")
            result = dispatch(
                args.manifest,
                stage=args.stage,
                repo_root=args.repo_root,
                changed_files=changed_files,
                verify_github_provenance=args.verify_github_provenance,
            )
        else:
            if not args.task or not args.approved_hito:
                raise DispatcherError("--task y --approved-hito son obligatorios en mode=implementation")
            result = dispatch_implementation(
                args.task,
                approved_hito=args.approved_hito,
                repo_root=args.repo_root,
                changed_files=changed_files,
            )
    except (DispatcherError, release_gate.GateError, OSError, KeyError, TypeError) as exc:
        print(json.dumps({"verdict": "NO_GO", "handoff": "developer", "reason": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
