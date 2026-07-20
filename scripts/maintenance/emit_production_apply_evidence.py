"""Emit structured PRODUCTION_APPLY evidence after a successful trusted workflow run."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker, ValidationError


ROOT = Path(__file__).resolve().parents[2]


def build_evidence(manifest, run_id, actor, commit, manifest_sha="unknown", package_sha="unknown", report_sha="unknown"):
    if manifest["state"] != "PRODUCTION_APPROVED":
        raise ValueError("El manifest debe estar en PRODUCTION_APPROVED")
    if not run_id.isdigit():
        raise ValueError("run-id invalido")
    if len(commit) != 40 or any(char not in "0123456789abcdef" for char in commit):
        raise ValueError("commit invalido")
    return {
        "schema_version": 1,
        "release_id": manifest["release_id"],
        "revision": manifest["revision"],
        "candidate_commit": manifest["candidate_commit"],
        "sequence": len(manifest["evidence"]) + 1,
        "role": "devops-release-manager",
        "actor": {"id": actor, "kind": "ci"},
        "provenance": {
            "source": "github-actions",
            "repository": "romelhc95/studiamatch",
            "run_id": run_id,
            "commit": commit,
            "workflow": ".github/workflows/db-sync-to-pro.yml",
            "artifact_name": f"production-apply-evidence-{run_id}",
            "artifact_file": "production-apply.json",
        },
        "event": "PRODUCTION_APPLY",
        "verdict": "PASS",
        "checks": [
            {
                "id": "manifest-applied",
                "status": "PASS",
                "evidence": f"run={run_id} package={package_sha} manifest={manifest_sha}",
            },
            {
                "id": "ledger-recorded",
                "status": "PASS",
                "evidence": f"run={run_id} postconditions_report={report_sha}",
            },
        ],
        "findings": [],
        "handoff": {
            "to_role": "pipeline-engineer",
            "reason": "Execute the isolated Pro canary and cleanup checks",
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--actor", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--package-sha", required=True)
    parser.add_argument("--verification-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        actual_manifest_sha = hashlib.sha256(args.manifest.read_bytes()).hexdigest()
        if actual_manifest_sha != args.manifest_sha256:
            raise ValueError("manifest-sha256 no coincide")
        report_sha = hashlib.sha256(args.verification_report.read_bytes()).hexdigest()
        evidence = build_evidence(
            manifest,
            args.run_id,
            args.actor,
            args.commit,
            actual_manifest_sha,
            args.package_sha,
            report_sha,
        )
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
