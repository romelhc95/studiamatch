#!/usr/bin/env python3
"""Collect and normalize GitHub promotion readiness metadata.

The workflow uses this module instead of inline Python so REST shape changes and
permission gaps are testable offline. Missing sensitive fields are represented as
UNOBSERVABLE, never as a safe empty value.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import socket
import urllib.error
import urllib.request
from urllib.parse import urlencode
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


EXPECTED_ENVIRONMENT = "Promotion"
EXPECTED_RULESET = "owner-only-protected-branch-updates"
EXPECTED_REVIEWER = "romelhc95-approver"
EXPECTED_REVIEWER_ID = 306979205
EXPECTED_MERGER = "romelhc95"
EXPECTED_MERGER_ID = 18040405
EXPECTED_REFS = {"refs/heads/desarrollo", "refs/heads/certificacion", "refs/heads/main"}
UNOBSERVABLE = "UNOBSERVABLE"


class SnapshotError(RuntimeError):
    """Raised when GitHub metadata cannot be normalized safely."""


@dataclass(frozen=True)
class GitHubClient:
    repo: str
    token: str
    sleeper: Callable[[float], None] | None = None

    def get(self, path: str) -> Any:
        url = path if path.startswith("https://") else f"https://api.github.com/repos/{self.repo}{path}"
        sleeper = self.sleeper or (lambda seconds: None)
        for attempt in range(4):
            request = urllib.request.Request(
                url,
                headers={
                    "Accept": "application/vnd.github+json",
                    "Authorization": f"Bearer {self.token}",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    try:
                        return json.loads(response.read().decode("utf-8"))
                    except json.JSONDecodeError as exc:
                        raise SnapshotError("INVALID:json") from exc
            except urllib.error.HTTPError as exc:
                if exc.code == 401:
                    raise SnapshotError("PERMISSION_DENIED:401") from exc
                if exc.code == 403:
                    raise SnapshotError("PERMISSION_DENIED:403") from exc
                if exc.code in {404, 429, 500, 503} and attempt < 3:
                    sleeper(0.25 * (2 ** attempt))
                    continue
                raise SnapshotError(f"UNOBSERVABLE:http_{exc.code}") from exc
            except (TimeoutError, socket.timeout, urllib.error.URLError) as exc:
                if attempt < 3:
                    sleeper(0.25 * (2 ** attempt))
                    continue
                raise SnapshotError("UNOBSERVABLE:timeout") from exc
        raise SnapshotError("UNOBSERVABLE:retry_budget")

    def get_paginated(self, path: str, *, per_page: int = 100) -> list[Any]:
        items: list[Any] = []
        page = 1
        separator = "&" if "?" in path else "?"
        while True:
            batch = self.get(f"{path}{separator}{urlencode({'per_page': per_page, 'page': page})}")
            if not isinstance(batch, list):
                raise SnapshotError("paginated response must be a list")
            items.extend(batch)
            if len(batch) < per_page:
                return items
            page += 1


def canonical_digest(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _required_reviewers(environment: dict[str, Any]) -> list[dict[str, Any]]:
    rules = environment.get("protection_rules")
    if rules is None:
        rules = environment.get("protection_rules_url_payload")
    reviewers: list[dict[str, Any]] = []
    if isinstance(rules, list):
        for rule in rules:
            if not isinstance(rule, dict) or rule.get("type") != "required_reviewers":
                continue
            for item in rule.get("reviewers") or []:
                reviewer = item.get("reviewer") if isinstance(item, dict) else None
                if isinstance(reviewer, dict):
                    reviewers.append(reviewer)
    return reviewers


def normalize_environment(environment: dict[str, Any]) -> dict[str, Any]:
    reviewers = _required_reviewers(environment)
    reviewer_logins = [item.get("login") or item.get("name") for item in reviewers]
    reviewer_ids = [item.get("id") for item in reviewers]
    exact_single_reviewer = reviewer_logins == [EXPECTED_REVIEWER] and reviewer_ids == [EXPECTED_REVIEWER_ID]
    return {
        "id": environment.get("id"),
        "name": environment.get("name"),
        "can_admins_bypass": environment.get("can_admins_bypass", UNOBSERVABLE),
        "prevent_self_review": environment.get("prevent_self_review", UNOBSERVABLE),
        "deployment_branch_policy": environment.get("deployment_branch_policy", UNOBSERVABLE),
        "reviewer": EXPECTED_REVIEWER if exact_single_reviewer else None,
        "reviewer_id": EXPECTED_REVIEWER_ID if exact_single_reviewer else None,
        "required_reviewers_observed": reviewer_logins,
        "required_reviewer_ids_observed": reviewer_ids,
    }


def normalize_ruleset(ruleset: dict[str, Any]) -> dict[str, Any]:
    bypass_actors = ruleset.get("bypass_actors", UNOBSERVABLE)
    if bypass_actors is None:
        bypass_actors = UNOBSERVABLE
    protected_refs = ((ruleset.get("conditions") or {}).get("ref_name") or {}).get("include") or []
    restrict_updates = any(rule.get("type") == "update" for rule in ruleset.get("rules") or [])
    if bypass_actors == UNOBSERVABLE:
        bypass_user = UNOBSERVABLE
        excluded_user = UNOBSERVABLE
        bypass_actor_count: int | str = UNOBSERVABLE
    elif isinstance(bypass_actors, list):
        bypass_actor_count = len(bypass_actors)
        bypass_user = EXPECTED_MERGER if any(actor.get("actor_type") == "User" and actor.get("actor_id") == EXPECTED_MERGER_ID for actor in bypass_actors if isinstance(actor, dict)) else None
        excluded_user = EXPECTED_REVIEWER if not any(actor.get("actor_id") == EXPECTED_REVIEWER_ID for actor in bypass_actors if isinstance(actor, dict)) else None
    else:
        bypass_user = UNOBSERVABLE
        excluded_user = UNOBSERVABLE
        bypass_actor_count = UNOBSERVABLE
    normalized = {
        "id": ruleset.get("id"),
        "name": ruleset.get("name"),
        "enforcement": ruleset.get("enforcement"),
        "restrict_updates": restrict_updates,
        "protected_refs": protected_refs,
        "bypass_actor_count": bypass_actor_count,
        "bypass_user": bypass_user,
        "excluded_user": excluded_user,
        "bypass_actors_observable": bypass_actors != UNOBSERVABLE,
    }
    normalized["canonical_digest"] = canonical_digest(normalized)
    return normalized


def validate_snapshot(snapshot: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    environment = snapshot.get("environment") or {}
    ruleset = snapshot.get("ruleset") or {}
    if environment.get("name") != EXPECTED_ENVIRONMENT:
        errors.append("SNAPSHOT_ENVIRONMENT_INVALID")
    if environment.get("reviewer") != EXPECTED_REVIEWER or environment.get("reviewer_id") != EXPECTED_REVIEWER_ID:
        errors.append("SNAPSHOT_REQUIRED_REVIEWER_INVALID")
    if environment.get("can_admins_bypass") is not False:
        errors.append("SNAPSHOT_CAN_ADMINS_BYPASS_INVALID")
    if environment.get("prevent_self_review") is not True:
        errors.append("SNAPSHOT_PREVENT_SELF_REVIEW_INVALID")
    if environment.get("deployment_branch_policy") is not None:
        errors.append("SNAPSHOT_DEPLOYMENT_BRANCH_POLICY_INVALID")
    if ruleset.get("name") != EXPECTED_RULESET or ruleset.get("enforcement") != "active":
        errors.append("SNAPSHOT_RULESET_INVALID")
    if ruleset.get("restrict_updates") is not True:
        errors.append("SNAPSHOT_RULESET_RESTRICT_UPDATES_INVALID")
    if ruleset.get("bypass_actors_observable") is not True:
        errors.append("SNAPSHOT_RULESET_BYPASS_UNOBSERVABLE")
    if ruleset.get("bypass_actor_count") != 1 or ruleset.get("bypass_user") != EXPECTED_MERGER or ruleset.get("excluded_user") != EXPECTED_REVIEWER:
        errors.append("SNAPSHOT_RULESET_BYPASS_INVALID")
    if not EXPECTED_REFS <= set(ruleset.get("protected_refs") or []):
        errors.append("SNAPSHOT_RULESET_REFS_INVALID")
    return errors


def build_snapshot(environment: dict[str, Any], ruleset: dict[str, Any], pulls: list[dict[str, Any]], cloudflare_app: dict[str, Any], current_pr: str) -> dict[str, Any]:
    current = next((item for item in pulls if str(item.get("number")) == str(current_pr)), {})
    return {
        "snapshot_source": "github-api",
        "environment": normalize_environment(environment),
        "ruleset": normalize_ruleset(ruleset),
        "active_promotions": [str(item.get("number")) for item in pulls if (item.get("head") or {}).get("ref", "").startswith("promote/gov-hom-012-")],
        "current_pr": current_pr,
        "current_pr_head_ref": (current.get("head") or {}).get("ref") if isinstance(current, dict) else None,
        "current_pr_body": current.get("body") if isinstance(current, dict) else None,
        "cloudflare_pages_app_id": cloudflare_app.get("id"),
        "repository_id": environment.get("repository_id"),
    }


def collect_snapshot(client: GitHubClient, pr_number: str) -> dict[str, Any]:
    environment = client.get("/environments/Promotion")
    rulesets = client.get_paginated("/rulesets")
    if not isinstance(rulesets, list):
        raise SnapshotError("rulesets response must be a list")
    target = next((item for item in rulesets if item.get("name") == EXPECTED_RULESET), {})
    if not target.get("id"):
        raise SnapshotError("owner-only ruleset missing")
    ruleset = client.get(f"/rulesets/{target['id']}")
    pulls = client.get_paginated("/pulls?state=open")
    cloudflare_app = client.get("https://api.github.com/apps/cloudflare-workers-and-pages")
    return build_snapshot(environment, ruleset, pulls, cloudflare_app, pr_number)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="readiness-snapshot.json")
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--input")
    args = parser.parse_args(argv)
    try:
        if args.input:
            snapshot = json.loads(Path(args.input).read_text(encoding="utf-8"))
        else:
            client = GitHubClient(repo=os.environ["GH_REPOSITORY"], token=os.environ["GH_TOKEN"])
            snapshot = collect_snapshot(client, os.environ.get("GH_PR_NUMBER", ""))
        errors = validate_snapshot(snapshot) if args.validate else []
        if errors:
            for error in errors:
                print(error)
            return 1
        Path(args.output).write_text(json.dumps(snapshot, ensure_ascii=True, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        return 0
    except Exception as exc:  # pragma: no cover - CLI guard
        print(f"SNAPSHOT_COLLECTION_FAILED:{exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
