#!/usr/bin/env python3
"""Read-only readiness preflight for HOM-011 promotions."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

try:
    from scripts.security.validate_work_package import (
        CLOUDFLARE_PAGES_APP_ID,
        DB_SYNC_DETECT_ONLY_RESULT,
        PROMOTION_CANDIDATE_BRANCHES,
        PROMOTION_ENVELOPE_SCHEMA,
        PROMOTION_FINAL_WP,
        compute_digest,
        load_manifest_by_id,
    )
except ModuleNotFoundError:
    from validate_work_package import (  # type: ignore
        CLOUDFLARE_PAGES_APP_ID,
        DB_SYNC_DETECT_ONLY_RESULT,
        PROMOTION_CANDIDATE_BRANCHES,
        PROMOTION_ENVELOPE_SCHEMA,
        PROMOTION_FINAL_WP,
        compute_digest,
        load_manifest_by_id,
    )


ROOT = Path(__file__).resolve().parents[2]
EXPECTED_ENVIRONMENT = "Promotion"
EXPECTED_RULESET = "owner-only-protected-branch-updates"
EXPECTED_REVIEWER = "romelhc95-approver"
EXPECTED_MERGER = "romelhc95"
EXPECTED_PROTECTED_REFS = {"refs/heads/desarrollo", "refs/heads/certificacion", "refs/heads/main"}


def load_json(path: str | None) -> dict:
    if not path:
        return {}
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def validate_readiness(snapshot: dict, *, root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    wp = load_manifest_by_id(PROMOTION_FINAL_WP, root=root)
    if not wp:
        errors.append("READINESS_WP_MISSING")
    elif wp.get("candidate_digest") != compute_digest(wp):
        errors.append("READINESS_WP_DIGEST_MISMATCH")

    if snapshot.get("snapshot_source") != "github-api":
        errors.append("READINESS_SNAPSHOT_SOURCE_INVALID")

    environment = snapshot.get("environment")
    if not isinstance(environment, dict):
        errors.append("READINESS_ENVIRONMENT_MISSING")
    else:
        if environment.get("name") != EXPECTED_ENVIRONMENT:
            errors.append("READINESS_ENVIRONMENT_INVALID")
        if environment.get("can_admins_bypass") is not False:
            errors.append("READINESS_ENVIRONMENT_ADMIN_BYPASS_INVALID")
        if environment.get("reviewer") != EXPECTED_REVIEWER:
            errors.append("READINESS_ENVIRONMENT_REVIEWER_INVALID")

    ruleset = snapshot.get("ruleset")
    if not isinstance(ruleset, dict):
        errors.append("READINESS_RULESET_MISSING")
    else:
        if ruleset.get("name") != EXPECTED_RULESET:
            errors.append("READINESS_RULESET_INVALID")
        if ruleset.get("enforcement") != "active":
            errors.append("READINESS_RULESET_ENFORCEMENT_INVALID")
        if ruleset.get("restrict_updates") is not True:
            errors.append("READINESS_RULESET_RESTRICT_UPDATES_INVALID")
        if ruleset.get("bypass_actor_count") != 1:
            errors.append("READINESS_RULESET_BYPASS_EXCLUSIVE_INVALID")
        protected_refs = set(ruleset.get("protected_refs") or [])
        if not EXPECTED_PROTECTED_REFS <= protected_refs:
            errors.append("READINESS_RULESET_REFS_INVALID")
        if ruleset.get("bypass_user") != EXPECTED_MERGER or ruleset.get("excluded_user") != EXPECTED_REVIEWER:
            errors.append("READINESS_RULESET_IDENTITY_INVALID")

    active = snapshot.get("active_promotions")
    if not isinstance(active, list):
        errors.append("READINESS_ACTIVE_PROMOTIONS_MISSING")
    elif len(active) != 1:
        errors.append("READINESS_ACTIVE_PROMOTION_COUNT_INVALID")
    elif snapshot.get("current_pr") and active[0] != str(snapshot.get("current_pr")):
        errors.append("READINESS_ACTIVE_PROMOTION_CURRENT_PR_INVALID")

    for operation, branch in PROMOTION_CANDIDATE_BRANCHES.items():
        grant_id = f"R3-GOV-HOM-011-{operation.split(' ', 1)[0]}-REQ1"
        grant_path = root / ".context" / "r3_grants" / f"{grant_id}.json"
        if not grant_path.exists():
            errors.append(f"READINESS_GRANT_MISSING:{grant_id}")
            continue
        grant = json.loads(grant_path.read_text(encoding="utf-8"))
        if grant.get("candidate_branch") != branch or grant.get("approval_envelope_schema") != PROMOTION_ENVELOPE_SCHEMA:
            errors.append(f"READINESS_GRANT_INVALID:{grant_id}")
        if operation.startswith("O3"):
            if grant.get("cloudflare_pages_production_rebuild_expected") is not True or grant.get("db_sync_expected_result") != DB_SYNC_DETECT_ONLY_RESULT:
                errors.append("READINESS_O3_SIDE_EFFECTS_INVALID")
        if operation.startswith("O4") and grant.get("blocked_until_o3_closed") is not True:
            errors.append("READINESS_O4_NOT_BLOCKED")

    if snapshot.get("cloudflare_pages_app_id") != CLOUDFLARE_PAGES_APP_ID:
        errors.append("READINESS_CLOUDFLARE_APP_INVALID")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", help="Optional local JSON snapshot of read-only remote metadata")
    parser.add_argument("--require-snapshot", action="store_true", help="Fail closed if no snapshot is provided")
    args = parser.parse_args(argv)
    if (args.require_snapshot or os.environ.get("GITHUB_ACTIONS") == "true") and not args.snapshot:
        print("READINESS_SNAPSHOT_REQUIRED")
        return 1
    try:
        snapshot = load_json(args.snapshot)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"READINESS_SNAPSHOT_INVALID:{exc}")
        return 1
    errors = validate_readiness(snapshot)
    if errors:
        for error in errors:
            print(error)
        return 1
    print("promotion readiness preflight passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
