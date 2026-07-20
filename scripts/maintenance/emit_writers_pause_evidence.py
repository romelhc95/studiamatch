"""Emit WRITERS_PAUSE evidence after the shared lock and active-run checks pass."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker, ValidationError


ROOT = Path(__file__).resolve().parents[2]


def build_evidence(manifest, run_id, commit):
    if manifest["state"] != "PIPELINE_VALIDATED" or not run_id.isdigit():
        raise ValueError("WRITERS_PAUSE requiere PIPELINE_VALIDATED y run-id valido")
    return {
        "schema_version": 1,
        "release_id": manifest["release_id"],
        "revision": manifest["revision"],
        "candidate_commit": manifest["candidate_commit"],
        "sequence": len(manifest["evidence"]) + 1,
        "role": "devops-release-manager",
        "actor": {"id": "github-actions-writer-lock", "kind": "ci"},
        "provenance": {
            "source": "github-actions",
            "repository": "romelhc95/studiamatch",
            "run_id": run_id,
            "commit": commit,
            "workflow": ".github/workflows/pause-production-writers.yml",
            "artifact_name": f"writers-pause-evidence-{run_id}",
            "artifact_file": "writers-pause.json",
        },
        "event": "WRITERS_PAUSE",
        "verdict": "PASS",
        "checks": [
            {"id": "writers-paused", "status": "PASS", "evidence": f"shared lock held by run {run_id}"},
            {"id": "active-runs-zero", "status": "PASS", "evidence": f"writer workflow API check in run {run_id}"},
        ],
        "findings": [],
        "handoff": {"to_role": "pipeline-engineer", "reason": "Execute isolated Free canary"},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if hashlib.sha256(args.manifest.read_bytes()).hexdigest() != args.manifest_sha256:
            raise ValueError("Checksum del manifest no coincide")
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        evidence = build_evidence(manifest, args.run_id, args.commit)
        schema = json.loads((ROOT / "schemas/role-evidence.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(evidence)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, KeyError, ValueError, json.JSONDecodeError, ValidationError) as exc:
        print(f"NO_GO: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
