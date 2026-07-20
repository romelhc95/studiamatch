"""Emit run-backed FREE/PRO canary evidence after verified cleanup."""

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
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--cleanup-report", type=Path, required=True)
    parser.add_argument("--env", choices=["free", "pro"], required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--candidate-commit", required=True)
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if hashlib.sha256(args.manifest.read_bytes()).hexdigest() != args.manifest_sha256:
            raise ValueError("Checksum del manifest no coincide")
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        report = json.loads(args.report.read_text(encoding="utf-8"))
        cleanup_report = json.loads(args.cleanup_report.read_text(encoding="utf-8"))
        expected_state = "WRITERS_PAUSED" if args.env == "free" else "PRODUCTION_APPLIED"
        if manifest["state"] != expected_state:
            raise ValueError(f"Canary {args.env} requiere estado {expected_state}")
        if (
            report.get("environment") != args.env
            or report.get("run_id") != args.run_id
            or report.get("candidate_commit") != args.candidate_commit
            or manifest.get("candidate_commit") != args.candidate_commit
            or report.get("cleanup_remaining_rows") != 0
            or report.get("cleanup_errors") != []
            or report.get("cleanup_out_of_scope_unchanged") is not True
            or cleanup_report.get("environment") != args.env
            or cleanup_report.get("run_id") != args.run_id
            or cleanup_report.get("institution_id") != report.get("institution_id")
            or cleanup_report.get("remaining_rows") != 0
            or cleanup_report.get("errors") != []
        ):
            raise ValueError("Reporte canary o cleanup invalido")
        expected_worker_hashes = {
            name: hashlib.sha256((args.candidate_root / path).read_bytes()).hexdigest()
            for name, path in {
                "cleansing": "scripts/core/cleansing_worker.py",
                "enrichment": "scripts/core/enrichment_worker.py",
                "sync": "scripts/core/sync_vector_worker.py",
            }.items()
        }
        if report.get("worker_sha256") != expected_worker_hashes:
            raise ValueError("Los hashes de workers no corresponden al checkout candidato")
        required_report_checks = {
            "pipeline_lineage", "public_fixtures_zero", "out_of_scope_mutations_zero",
            "production_enabled_false", "rpc_fallback_zero", "rls_guard_definitions",
            "mock_provenance",
        }
        if any(report.get("checks", {}).get(check) != "PASS" for check in required_report_checks):
            raise ValueError("Reporte canary no contiene todos los checks PASS")
        event = "FREE_CANARY_PASS" if args.env == "free" else "PRODUCTION_CANARY_PASS"
        next_role = "qa-test-engineer"
        check_ids = ["free-canary" if args.env == "free" else "pro-canary", "fixture-cleanup"]
        if args.env == "pro":
            check_ids.append("public-fixtures-zero")
        report_sha = hashlib.sha256(args.report.read_bytes()).hexdigest()
        cleanup_sha = hashlib.sha256(args.cleanup_report.read_bytes()).hexdigest()
        evidence = {
            "schema_version": 1,
            "release_id": manifest["release_id"],
            "revision": manifest["revision"],
            "candidate_commit": manifest["candidate_commit"],
            "sequence": len(manifest["evidence"]) + 1,
            "role": "pipeline-engineer",
            "actor": {"id": f"github-actions-pipeline-canary-{args.env}", "kind": "ci"},
            "provenance": {
                "source": "github-actions",
                "repository": "romelhc95/studiamatch",
                "run_id": args.run_id,
                "commit": args.commit,
                "workflow": ".github/workflows/pipeline-canary.yml",
                "artifact_name": f"pipeline-canary-{args.env}-{args.run_id}",
                "artifact_file": "evidence.json",
            },
            "event": event,
            "verdict": "PASS",
            "checks": [
                {
                    "id": check_id,
                    "status": "PASS",
                    "evidence": f"report={report_sha} cleanup={cleanup_sha}",
                }
                for check_id in check_ids
            ],
            "findings": [],
            "handoff": {"to_role": next_role, "reason": f"Independently certify {args.env} canary evidence"},
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
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
