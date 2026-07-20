"""Deterministic release gate for role-separated StudIAMatch promotions."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import sys
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
import requests


DEFAULT_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_ROOT = DEFAULT_ROOT / "schemas"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")

TRANSITIONS = {
    ("DRAFT", "DEVELOPER_SUBMIT"): ("DEVELOPER_READY", "developer"),
    ("DEVELOPER_READY", "QA_PASS"): ("QA_VALIDATED", "qa-test-engineer"),
    ("QA_VALIDATED", "SECURITY_PASS"): ("SECURITY_VALIDATED", "security-auditor"),
    ("SECURITY_VALIDATED", "DATABASE_PASS"): ("DATABASE_VALIDATED", "supabase-architect"),
    ("DATABASE_VALIDATED", "PIPELINE_PASS"): ("PIPELINE_VALIDATED", "pipeline-engineer"),
    ("PIPELINE_VALIDATED", "WRITERS_PAUSE"): ("WRITERS_PAUSED", "devops-release-manager"),
    ("WRITERS_PAUSED", "FREE_CANARY_PASS"): ("FREE_CANARY_PASSED", "pipeline-engineer"),
    ("FREE_CANARY_PASSED", "FREE_PASS"): ("FREE_CERTIFIED", "qa-test-engineer"),
    ("FREE_CERTIFIED", "AUTHORIZE_PRODUCTION"): ("PRODUCTION_APPROVED", "human-approver"),
    ("PRODUCTION_APPROVED", "PRODUCTION_APPLY"): ("PRODUCTION_APPLIED", "devops-release-manager"),
    ("PRODUCTION_APPLIED", "PRODUCTION_CANARY_PASS"): ("PRODUCTION_CANARY_PASSED", "pipeline-engineer"),
    ("PRODUCTION_CANARY_PASSED", "PRODUCTION_PASS"): ("PRODUCTION_CERTIFIED", "qa-test-engineer"),
    ("PRODUCTION_CERTIFIED", "AUTHORIZE_RESUME"): ("RESUME_AUTHORIZED", "human-approver"),
    ("RESUME_AUTHORIZED", "RELEASE_READY"): ("READY_FOR_HUMAN_DECISION", "devops-release-manager"),
    ("READY_FOR_HUMAN_DECISION", "PROMOTE"): ("RELEASED", "human-approver"),
}

NEXT_ROLE = {
    "DRAFT": "developer",
    "DEVELOPER_READY": "qa-test-engineer",
    "QA_VALIDATED": "security-auditor",
    "SECURITY_VALIDATED": "supabase-architect",
    "DATABASE_VALIDATED": "pipeline-engineer",
    "PIPELINE_VALIDATED": "devops-release-manager",
    "WRITERS_PAUSED": "pipeline-engineer",
    "FREE_CANARY_PASSED": "qa-test-engineer",
    "FREE_CERTIFIED": "human-approver",
    "PRODUCTION_APPROVED": "devops-release-manager",
    "PRODUCTION_APPLIED": "pipeline-engineer",
    "PRODUCTION_CANARY_PASSED": "qa-test-engineer",
    "PRODUCTION_CERTIFIED": "human-approver",
    "RESUME_AUTHORIZED": "devops-release-manager",
    "READY_FOR_HUMAN_DECISION": "human-approver",
    "RELEASED": "none",
    "NO_GO": "developer",
}

STAGE_STATES = {
    "structure": set(NEXT_ROLE),
    "development": set(NEXT_ROLE) - {"DRAFT", "NO_GO"},
    "certification": {
        "PIPELINE_VALIDATED", "WRITERS_PAUSED", "FREE_CANARY_PASSED", "FREE_CERTIFIED",
        "PRODUCTION_APPROVED", "PRODUCTION_APPLIED", "PRODUCTION_CANARY_PASSED",
        "PRODUCTION_CERTIFIED", "RESUME_AUTHORIZED", "READY_FOR_HUMAN_DECISION", "RELEASED",
    },
    "free": {
        "FREE_CERTIFIED", "PRODUCTION_APPROVED", "PRODUCTION_APPLIED",
        "PRODUCTION_CANARY_PASSED", "PRODUCTION_CERTIFIED", "RESUME_AUTHORIZED",
        "READY_FOR_HUMAN_DECISION", "RELEASED",
    },
    "free-canary": {"WRITERS_PAUSED"},
    "production": {"PRODUCTION_APPROVED"},
    "pro-canary": {"PRODUCTION_APPLIED"},
    "post-production": {
        "PRODUCTION_CERTIFIED", "RESUME_AUTHORIZED", "READY_FOR_HUMAN_DECISION", "RELEASED",
    },
    "pipeline-resume": {"RESUME_AUTHORIZED", "READY_FOR_HUMAN_DECISION", "RELEASED"},
    "release-decision": {"READY_FOR_HUMAN_DECISION"},
    "release": {"RELEASED"},
}

REQUIRED_PASS_CHECKS = {
    "DEVELOPER_SUBMIT": {"implementation-tests"},
    "QA_PASS": {"acceptance-tests"},
    "SECURITY_PASS": {"security-audit"},
    "DATABASE_PASS": {"schema-review", "rls-review"},
    "PIPELINE_PASS": {"pipeline-tests"},
    "WRITERS_PAUSE": {"writers-paused", "active-runs-zero"},
    "FREE_CANARY_PASS": {"free-canary", "fixture-cleanup"},
    "FREE_PASS": {"free-certification"},
    "AUTHORIZE_PRODUCTION": {"human-approval"},
    "PRODUCTION_APPLY": {"manifest-applied", "ledger-recorded"},
    "PRODUCTION_CANARY_PASS": {"pro-canary", "fixture-cleanup", "public-fixtures-zero"},
    "PRODUCTION_PASS": {"pro-certification"},
    "AUTHORIZE_RESUME": {"human-approval"},
    "RELEASE_READY": {"release-summary"},
    "PROMOTE": {"human-approval"},
}

HUMAN_EVENTS = {"AUTHORIZE_PRODUCTION", "AUTHORIZE_RESUME", "PROMOTE"}
CI_EVENTS = {"WRITERS_PAUSE", "FREE_CANARY_PASS", "PRODUCTION_APPLY", "PRODUCTION_CANARY_PASS"}
EVENT_WORKFLOWS = {
    "WRITERS_PAUSE": ".github/workflows/pause-production-writers.yml",
    "FREE_CANARY_PASS": ".github/workflows/pipeline-canary.yml",
    "AUTHORIZE_PRODUCTION": ".github/workflows/authorize-release.yml",
    "PRODUCTION_APPLY": ".github/workflows/db-sync-to-pro.yml",
    "PRODUCTION_CANARY_PASS": ".github/workflows/pipeline-canary.yml",
    "AUTHORIZE_RESUME": ".github/workflows/authorize-release.yml",
    "PROMOTE": ".github/workflows/authorize-release.yml",
}


class GateError(ValueError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GateError(f"No se pudo leer JSON {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise GateError(f"{path} debe contener un objeto JSON")
    return data


def _validate_schema(data: dict[str, Any], schema_name: str, source: Path) -> None:
    schema = _load_json(SCHEMA_ROOT / schema_name)
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(data),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.absolute_path) or "root"
        raise GateError(f"Schema invalido en {source} ({location}): {error.message}")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_repo_path(root: Path, value: str) -> Path:
    if not isinstance(value, str) or "\\" in value:
        raise GateError(f"Path no canonico: {value}")
    pure = PurePosixPath(value)
    if pure.is_absolute() or ".." in pure.parts or pure.as_posix() != value:
        raise GateError(f"Path no canonico: {value}")
    path = (root / value).resolve()
    if root != path and root not in path.parents:
        raise GateError(f"Path fuera del repositorio: {value}")
    return path


def _validate_previous_manifest(manifest: dict[str, Any], root: Path) -> None:
    previous = manifest["previous_manifest"]
    if manifest["revision"] == 1:
        if previous is not None:
            raise GateError("La revision 1 no puede referenciar un manifest anterior")
        return
    if not isinstance(previous, dict):
        raise GateError("Una revision posterior requiere previous_manifest")
    path = _canonical_repo_path(root, previous["path"])
    if _sha256(path) != previous["sha256"]:
        raise GateError("Checksum del manifest anterior no coincide")
    prior = _load_json(path)
    _validate_schema(prior, "release-manifest.schema.json", path)
    if prior["release_id"] != manifest["release_id"]:
        raise GateError("El manifest anterior pertenece a otro release")
    if prior["revision"] + 1 != manifest["revision"] or prior["state"] != "NO_GO":
        raise GateError("La revision nueva debe seguir exactamente a un manifest NO_GO")
    _validate_previous_manifest(prior, root)
    validate_artifacts(prior, root)
    prior_state, _ = derive_state(prior, root)
    if (
        prior_state != "NO_GO"
    ):
        raise GateError("La revision nueva debe seguir exactamente a un manifest NO_GO")


def validate_artifacts(manifest: dict[str, Any], root: Path) -> None:
    seen_paths: set[str] = set()
    seen_resolved: set[Path] = set()
    seen_migration_names: set[str] = set()
    seen_nontransactional = False
    for group in ("migrations", "evidence"):
        for item in manifest[group]:
            rel_path = item["path"]
            path = _canonical_repo_path(root, rel_path)
            if rel_path in seen_paths or path in seen_resolved:
                raise GateError(f"Artefacto duplicado: {rel_path}")
            seen_paths.add(rel_path)
            seen_resolved.add(path)
            if not path.is_file():
                raise GateError(f"Artefacto inexistente: {rel_path}")
            actual = _sha256(path)
            if actual != item["sha256"]:
                raise GateError(f"Checksum distinto para {rel_path}: esperado {item['sha256']}, actual {actual}")
            if group == "migrations":
                migration_name = path.stem
                if migration_name in seen_migration_names:
                    raise GateError(f"Nombre de migration duplicado: {migration_name}")
                seen_migration_names.add(migration_name)
                if not item["transactional"]:
                    seen_nontransactional = True
                elif seen_nontransactional:
                    raise GateError("Las migrations transaccionales deben preceder a las no transaccionales")
                expected_prefix = "db/migrations/" if item["transactional"] else "db/nontransactional/"
                if not rel_path.startswith(expected_prefix):
                    raise GateError(
                        f"Path incompatible con transactional={item['transactional']}: {rel_path}"
                    )
                if "pro" in item["targets"] and "free" not in item["targets"]:
                    raise GateError(f"Una migration para Pro debe certificarse primero en Free: {rel_path}")
                if item["transactional"]:
                    sql = "\n".join(
                        line for line in path.read_text(encoding="utf-8").splitlines()
                        if not line.lstrip().startswith("--")
                    )
                    if re.search(r"(?im)^\s*(BEGIN|COMMIT|ROLLBACK)\s*;\s*$", sql):
                        raise GateError(f"La migration controla transacciones explicitamente: {rel_path}")
                    if re.search(r"\bCONCURRENTLY\b", sql, re.IGNORECASE):
                        raise GateError(f"CONCURRENTLY requiere db/nontransactional: {rel_path}")
            elif not rel_path.startswith(".context/evidencias/"):
                raise GateError(f"Path de evidencia invalido: {rel_path}")


def derive_state(manifest: dict[str, Any], root: Path) -> tuple[str, list[dict[str, Any]]]:
    state = "DRAFT"
    evidence_docs: list[dict[str, Any]] = []
    role_by_actor: dict[str, str] = {}
    for expected_sequence, item in enumerate(manifest["evidence"], start=1):
        path = _canonical_repo_path(root, item["path"])
        evidence = _load_json(path)
        _validate_schema(evidence, "role-evidence.schema.json", path)
        evidence_docs.append(evidence)
        for key in ("release_id", "revision", "candidate_commit"):
            if evidence[key] != manifest[key]:
                raise GateError(f"{item['path']} no coincide con manifest en {key}")
        if evidence["sequence"] != expected_sequence:
            raise GateError(f"Secuencia invalida en {item['path']}: se esperaba {expected_sequence}")
        role = evidence["role"]
        actor_id = evidence["actor"]["id"]
        previous_role = role_by_actor.get(actor_id)
        if previous_role and previous_role != role:
            raise GateError(f"El actor {actor_id} no puede certificar roles distintos")
        role_by_actor[actor_id] = role
        event = evidence["event"]
        verdict = evidence["verdict"]
        checks = evidence["checks"]
        findings = evidence["findings"]
        handoff = evidence["handoff"]
        if event == "GATE_FAIL" or verdict == "NO_GO" or any(check["status"] == "FAIL" for check in checks):
            if verdict != "NO_GO" or not findings or handoff["to_role"] != "developer":
                raise GateError(f"NO_GO sin findings o handoff a developer en {item['path']}")
            state = "NO_GO"
            if expected_sequence != len(manifest["evidence"]):
                raise GateError("NO_GO debe ser la ultima evidencia de la revision")
            continue
        if state == "NO_GO":
            raise GateError("Tras NO_GO se requiere un manifest nuevo con revision incrementada")
        transition = TRANSITIONS.get((state, event))
        if not transition:
            raise GateError(f"Transicion invalida: {state} + {event}")
        next_state, expected_role = transition
        if role != expected_role or verdict != "PASS":
            raise GateError(f"{event} requiere rol {expected_role} y verdict PASS")
        if event in HUMAN_EVENTS and evidence["actor"]["kind"] != "human":
            raise GateError(f"{event} requiere un actor humano")
        if event in HUMAN_EVENTS:
            provenance = evidence["provenance"]
            if (
                provenance["source"] != "github-environment"
                or not provenance["run_id"]
                or not provenance["commit"]
                or provenance["workflow"] != EVENT_WORKFLOWS[event]
                or not provenance["artifact_name"]
                or not provenance["artifact_file"]
            ):
                raise GateError(f"{event} requiere provenance de GitHub Environment")
        if event in CI_EVENTS:
            provenance = evidence["provenance"]
            if (
                provenance["source"] != "github-actions"
                or not provenance["run_id"]
                or not provenance["commit"]
                or provenance["workflow"] != EVENT_WORKFLOWS[event]
                or not provenance["artifact_name"]
                or not provenance["artifact_file"]
            ):
                raise GateError(f"{event} requiere provenance de GitHub Actions")
        passed_ids = {check["id"] for check in checks if check["status"] == "PASS"}
        missing_checks = REQUIRED_PASS_CHECKS[event] - passed_ids
        if missing_checks:
            raise GateError(f"{event} carece de checks PASS: {', '.join(sorted(missing_checks))}")
        if findings:
            raise GateError(f"Una evidencia PASS no puede contener findings: {item['path']}")
        if handoff["to_role"] != NEXT_ROLE[next_state]:
            raise GateError(f"Handoff invalido en {item['path']}; se esperaba {NEXT_ROLE[next_state]}")
        state = next_state
    return state, evidence_docs


def verify_github_provenance(evidence_docs: list[dict[str, Any]], token: str) -> None:
    if not token:
        raise GateError("GITHUB_TOKEN es obligatorio para verificar provenance")
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    for evidence in evidence_docs:
        provenance = evidence["provenance"]
        if provenance["source"] not in {"github-actions", "github-environment"}:
            continue
        response = requests.get(
            f"https://api.github.com/repos/{provenance['repository']}/actions/runs/{provenance['run_id']}",
            headers=headers,
            timeout=30,
        )
        if response.status_code != 200:
            raise GateError(f"No se pudo verificar GitHub run {provenance['run_id']}")
        run = response.json()
        expected_conclusion = "failure" if evidence["verdict"] == "NO_GO" else "success"
        if (
            run.get("repository", {}).get("full_name") != provenance["repository"]
            or run.get("head_sha") != provenance["commit"]
            or run.get("conclusion") != expected_conclusion
            or run.get("path") != provenance["workflow"]
        ):
            raise GateError(f"GitHub provenance invalido para run {provenance['run_id']}")
        artifacts_response = requests.get(
            f"https://api.github.com/repos/{provenance['repository']}/actions/runs/{provenance['run_id']}/artifacts?per_page=100",
            headers=headers,
            timeout=30,
        )
        if artifacts_response.status_code != 200:
            raise GateError(f"No se pudieron verificar artifacts del run {provenance['run_id']}")
        artifacts = [
            artifact
            for artifact in artifacts_response.json().get("artifacts", [])
            if artifact.get("name") == provenance["artifact_name"] and not artifact.get("expired")
        ]
        if len(artifacts) != 1:
            raise GateError(f"Artifact de provenance ausente o ambiguo para run {provenance['run_id']}")
        archive_response = requests.get(
            artifacts[0]["archive_download_url"],
            headers=headers,
            timeout=30,
        )
        if archive_response.status_code != 200:
            raise GateError(f"No se pudo descargar artifact del run {provenance['run_id']}")
        try:
            with zipfile.ZipFile(io.BytesIO(archive_response.content)) as archive:
                artifact_evidence = json.loads(archive.read(provenance["artifact_file"]))
        except (KeyError, zipfile.BadZipFile, json.JSONDecodeError) as exc:
            raise GateError(f"Artifact de evidencia invalido para run {provenance['run_id']}") from exc
        if artifact_evidence != evidence:
            raise GateError(f"La evidencia no coincide con el artifact del run {provenance['run_id']}")


def validate_release(
    manifest_path: Path,
    stage: str,
    expected_manifest_sha256: str | None = None,
    root: Path = DEFAULT_ROOT,
    verify_provenance: bool = False,
) -> dict[str, Any]:
    root = root.resolve()
    manifest_path = manifest_path.resolve()
    try:
        relative_manifest = manifest_path.relative_to(root).as_posix()
    except ValueError as exc:
        raise GateError("El manifest debe estar dentro del repositorio candidato") from exc
    if not re.fullmatch(r"\.context/evidencias/releases/[a-z0-9._-]+/release-manifest\.json", relative_manifest):
        raise GateError("El manifest no esta en el path canonico de releases")
    if expected_manifest_sha256 and _sha256(manifest_path) != expected_manifest_sha256:
        raise GateError("El checksum del manifest no coincide con la autorizacion")
    manifest = _load_json(manifest_path)
    _validate_schema(manifest, "release-manifest.schema.json", manifest_path)
    _validate_previous_manifest(manifest, root)
    validate_artifacts(manifest, root)
    derived_state, evidence = derive_state(manifest, root)
    if verify_provenance:
        verify_github_provenance(evidence, os.environ.get("GITHUB_TOKEN", ""))
    if derived_state != manifest["state"]:
        raise GateError(f"Estado declarado {manifest['state']} no coincide con estado derivado {derived_state}")
    if derived_state != "DRAFT":
        expected_commit = os.environ.get("RELEASE_CANDIDATE_SHA")
        if expected_commit and manifest["candidate_commit"] != expected_commit:
            raise GateError("candidate_commit no coincide con el commit autorizado/checkout")
    if derived_state not in STAGE_STATES[stage]:
        raise GateError(f"Estado {derived_state} no habilita stage {stage}")
    return {
        "release_id": manifest["release_id"],
        "revision": manifest["revision"],
        "state": derived_state,
        "next_role": NEXT_ROLE[derived_state],
        "evidence_count": len(evidence),
        "manifest_sha256": _sha256(manifest_path),
        "validation": "structure" if stage == "structure" else "promotion-gate",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--stage", choices=sorted(STAGE_STATES), default="structure")
    parser.add_argument("--expected-manifest-sha256")
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--verify-github-provenance", action="store_true")
    args = parser.parse_args()
    try:
        result = validate_release(
            args.manifest,
            args.stage,
            args.expected_manifest_sha256,
            args.repo_root,
            args.verify_github_provenance,
        )
    except (GateError, OSError, KeyError, TypeError) as exc:
        print(json.dumps({"verdict": "NO_GO", "handoff": "developer", "reason": str(exc)}, ensure_ascii=True))
        return 1
    print(json.dumps({"verdict": "PASS", **result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
