"""Emit structured NO_GO evidence when a release workflow fails."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker, ValidationError


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--workflow", required=True)
    parser.add_argument("--role", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        actual_manifest_sha = hashlib.sha256(args.manifest.read_bytes()).hexdigest()
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        evidence = {
            "schema_version": 1,
            "release_id": manifest["release_id"],
            "revision": manifest["revision"],
            "candidate_commit": manifest["candidate_commit"],
            "sequence": len(manifest["evidence"]) + 1,
            "role": args.role,
            "actor": {"id": "github-actions-failure-gate", "kind": "ci"},
            "provenance": {
                "source": "github-actions",
                "repository": "romelhc95/studiamatch",
                "run_id": args.run_id,
                "commit": args.commit,
                "workflow": args.workflow,
                "artifact_name": f"release-no-go-{args.run_id}",
                "artifact_file": "no-go.json",
            },
            "event": "GATE_FAIL",
            "verdict": "NO_GO",
            "checks": [{
                "id": "workflow-run",
                "status": "FAIL",
                "evidence": (
                    f"GitHub run {args.run_id}; manifest expected={args.manifest_sha256} "
                    f"actual={actual_manifest_sha}"
                ),
            }],
            "findings": [{"severity": "high", "summary": args.summary}],
            "handoff": {"to_role": "developer", "reason": "Remediate the failed workflow and open a new revision"},
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        schema = json.loads((ROOT / "schemas/role-evidence.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(evidence)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, KeyError, ValueError, json.JSONDecodeError, ValidationError) as exc:
        print(f"NO_GO evidence could not be emitted: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
