"""Emit human authorization evidence from the protected Production environment."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker, ValidationError

try:
    from .release_gate import EVENT_WORKFLOWS, NEXT_ROLE, REQUIRED_PASS_CHECKS, TRANSITIONS
except ImportError:
    from release_gate import EVENT_WORKFLOWS, NEXT_ROLE, REQUIRED_PASS_CHECKS, TRANSITIONS


ROOT = Path(__file__).resolve().parents[2]
EVENTS = {"AUTHORIZE_PRODUCTION", "AUTHORIZE_RESUME", "PROMOTE"}


def build_evidence(manifest, event, run_id, commit):
    if event not in EVENTS or not run_id.isdigit():
        raise ValueError("Evento o run-id invalido")
    transition = TRANSITIONS.get((manifest["state"], event))
    if not transition:
        raise ValueError(f"{event} no es valido desde {manifest['state']}")
    next_state, role = transition
    if role != "human-approver":
        raise ValueError("La transicion no pertenece al aprobador humano")
    return {
        "schema_version": 1,
        "release_id": manifest["release_id"],
        "revision": manifest["revision"],
        "candidate_commit": manifest["candidate_commit"],
        "sequence": len(manifest["evidence"]) + 1,
        "role": role,
        "actor": {"id": f"protected-environment-reviewer-run-{run_id}", "kind": "human"},
        "provenance": {
            "source": "github-environment",
            "repository": "romelhc95/studiamatch",
            "run_id": run_id,
            "commit": commit,
            "workflow": EVENT_WORKFLOWS[event],
            "artifact_name": f"release-authorization-{event}-{run_id}",
            "artifact_file": "authorization.json",
        },
        "event": event,
        "verdict": "PASS",
        "checks": [
            {
                "id": check_id,
                "status": "PASS",
                "evidence": f"Production environment approval in workflow run {run_id}",
            }
            for check_id in sorted(REQUIRED_PASS_CHECKS[event])
        ],
        "findings": [],
        "handoff": {
            "to_role": NEXT_ROLE[next_state],
            "reason": f"Protected environment authorized transition to {next_state}",
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--event", choices=sorted(EVENTS), required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if hashlib.sha256(args.manifest.read_bytes()).hexdigest() != args.manifest_sha256:
            raise ValueError("Checksum del manifest no coincide")
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        evidence = build_evidence(manifest, args.event, args.run_id, args.commit)
        schema = json.loads((ROOT / "schemas/role-evidence.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(evidence)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(hashlib.sha256(args.output.read_bytes()).hexdigest())
    except (OSError, KeyError, ValueError, json.JSONDecodeError, ValidationError) as exc:
        print(f"NO_GO: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
