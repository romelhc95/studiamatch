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
FROZEN_PROMOTION_PRS = {"443", "445", "447"}


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


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _required_reviewers_rule(environment: dict[str, Any]) -> dict[str, Any]:
    rules = environment.get("protection_rules")
    if rules is None:
        rules = environment.get("protection_rules_url_payload")
    if isinstance(rules, list):
        for rule in rules:
            if isinstance(rule, dict) and rule.get("type") == "required_reviewers":
                return rule
    return {}


def _required_reviewers(environment: dict[str, Any]) -> list[dict[str, Any]]:
    rule = _required_reviewers_rule(environment)
    reviewers: list[dict[str, Any]] = []
    for item in rule.get("reviewers") or []:
        reviewer = item.get("reviewer") if isinstance(item, dict) else None
        if isinstance(reviewer, dict):
            reviewers.append(reviewer)
    return reviewers


def normalize_environment(environment: dict[str, Any]) -> dict[str, Any]:
    required_reviewers_rule = _required_reviewers_rule(environment)
    reviewers = _required_reviewers(environment)
    reviewer_logins = [item.get("login") or item.get("name") for item in reviewers]
    reviewer_ids = [item.get("id") for item in reviewers]
    exact_single_reviewer = reviewer_logins == [EXPECTED_REVIEWER] and reviewer_ids == [EXPECTED_REVIEWER_ID]
    prevent_self_review = required_reviewers_rule.get("prevent_self_review", environment.get("prevent_self_review", UNOBSERVABLE))
    return {
        "id": environment.get("id"),
        "name": environment.get("name"),
        "can_admins_bypass": environment.get("can_admins_bypass", UNOBSERVABLE),
        "prevent_self_review": prevent_self_review,
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
    bypass_observable = ruleset.get("bypass_actors_observable") is True
    if bypass_observable and (ruleset.get("bypass_actor_count") != 1 or ruleset.get("bypass_user") != EXPECTED_MERGER or ruleset.get("excluded_user") != EXPECTED_REVIEWER):
        errors.append("SNAPSHOT_RULESET_BYPASS_INVALID")
    if not EXPECTED_REFS <= set(ruleset.get("protected_refs") or []):
        errors.append("SNAPSHOT_RULESET_REFS_INVALID")
    if str(snapshot.get("current_pr") or "") in FROZEN_PROMOTION_PRS:
        errors.append("SNAPSHOT_FROZEN_PR_INVALID")
    if "current_pr_body" in snapshot:
        errors.append("SNAPSHOT_BODY_FORBIDDEN")
    return errors


def build_snapshot(environment: dict[str, Any], ruleset: dict[str, Any], pulls: list[dict[str, Any]], cloudflare_app: dict[str, Any], current_pr: str) -> dict[str, Any]:
    current = next((item for item in pulls if str(item.get("number")) == str(current_pr)), {})
    return {
        "snapshot_source": "github-api",
        "environment": normalize_environment(environment),
        "ruleset": normalize_ruleset(ruleset),
        "active_promotions": [str(item.get("number")) for item in pulls if str(item.get("number")) not in FROZEN_PROMOTION_PRS and (item.get("head") or {}).get("ref", "").startswith("promote/gov-hom-012-")],
        "current_pr": current_pr,
        "current_pr_head_ref": (current.get("head") or {}).get("ref") if isinstance(current, dict) else None,
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


def workflow_binding_from_source(
    workflow_text: str,
    *,
    source_commit: str,
    workflow_path: str = ".github/workflows/security-audit.yml",
    workflow_name: str = "Security Audit Gate",
    job_key: str = "promotion-boundary",
    job_name: str = "Promotion Boundary",
    environment_name: str = EXPECTED_ENVIRONMENT,
) -> dict[str, Any]:
    errors = validate_workflow_source(workflow_text, job_key=job_key, job_name=job_name, environment_name=environment_name)
    if errors:
        raise SnapshotError(",".join(errors))
    return {
        "schema": "github-workflow-environment-gate-binding-v1",
        "source_commit": source_commit,
        "workflow_path": workflow_path,
        "workflow_name": workflow_name,
        "job_key": job_key,
        "api_job_name": job_name,
        "environment_name": environment_name,
        "artifact_producer_in_same_job": True,
        "extraction_method": "local_workflow_structural_parser_v1",
        "remote_request": False,
        "historical_binding_only": False,
        "candidate_workflow_must_produce_artifact_in_same_job": True,
        "source_blob_sha256": sha256_text(workflow_text),
    }


def _job_block(workflow_text: str, job_key: str) -> str:
    lines = workflow_text.splitlines()
    marker = f"  {job_key}:"
    start = next((idx for idx, line in enumerate(lines) if line == marker), None)
    if start is None:
        return ""
    end = len(lines)
    for idx in range(start + 1, len(lines)):
        line = lines[idx]
        if line.startswith("  ") and not line.startswith("    ") and line.endswith(":"):
            end = idx
            break
    return "\n".join(lines[start:end])


def validate_workflow_source(workflow_text: str, *, job_key: str = "promotion-boundary", job_name: str = "Promotion Boundary", environment_name: str = EXPECTED_ENVIRONMENT) -> list[str]:
    errors: list[str] = []
    if workflow_text.count(f"  {job_key}:") != 1:
        errors.append("WORKFLOW_PROMOTION_JOB_COUNT_INVALID")
        return errors
    block = _job_block(workflow_text, job_key)
    if f"name: {job_name}" not in block:
        errors.append("WORKFLOW_PROMOTION_JOB_NAME_INVALID")
    if f"name: {environment_name}" not in block:
        errors.append("WORKFLOW_PROMOTION_ENVIRONMENT_INVALID")
    if "R3_JIT_APPROVAL_ENVELOPE" not in block:
        errors.append("WORKFLOW_PROMOTION_SECRET_MISSING")
    if "promotion_evidence.py" not in block or "--write-approval-evidence" not in block:
        errors.append("WORKFLOW_PROMOTION_PRODUCER_MISSING")
    if "actions/upload-artifact@" not in block or "promotion-approval-evidence.json" not in block:
        errors.append("WORKFLOW_PROMOTION_UPLOAD_MISSING")
    post_merge = _job_block(workflow_text, "post-merge-approval")
    if "environment:" in post_merge:
        errors.append("WORKFLOW_POST_MERGE_ENVIRONMENT_FORBIDDEN")
    if "R3_JIT_APPROVAL_ENVELOPE" in post_merge:
        errors.append("WORKFLOW_POST_MERGE_SECRET_FORBIDDEN")
    if "github.event.action == 'opened'" not in block:
        errors.append("WORKFLOW_PROMOTION_OPENED_BINDING_MISSING")
    return errors


def collect_run_evidence(
    client: GitHubClient,
    *,
    run_id: int,
    output_dir: Path,
    workflow_path: str = ".github/workflows/security-audit.yml",
    workflow_name: str = "Security Audit Gate",
    job_key: str = "promotion-boundary",
    job_name: str = "Promotion Boundary",
    environment_name: str = EXPECTED_ENVIRONMENT,
    source_commit: str = "",
) -> int:
    approvals = client.get(f"/actions/runs/{run_id}/approvals")
    run_payload = client.get(f"/actions/runs/{run_id}")
    jobs = client.get(f"/actions/runs/{run_id}/jobs?per_page=100")
    if not isinstance(jobs, dict) or not isinstance(jobs.get("jobs"), list) or jobs.get("total_count") != len(jobs.get("jobs")):
        raise SnapshotError("JOBS_SCHEMA_INVALID")
    matches = [job for job in jobs["jobs"] if isinstance(job, dict) and job.get("name") == job_name]
    if len(matches) != 1:
        raise SnapshotError("PROMOTION_BOUNDARY_JOB_UNOBSERVABLE")
    workflow_text = Path(workflow_path).read_text(encoding="utf-8")
    binding = workflow_binding_from_source(
        workflow_text,
        source_commit=source_commit,
        workflow_path=workflow_path,
        workflow_name=workflow_name,
        job_key=job_key,
        job_name=job_name,
        environment_name=environment_name,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "promotion-approval-history.json").write_text(json.dumps(approvals, separators=(",", ":")), encoding="utf-8")
    (output_dir / "promotion-run-payload.json").write_text(json.dumps(run_payload, separators=(",", ":")), encoding="utf-8")
    (output_dir / "promotion-jobs-payload.json").write_text(json.dumps(jobs, separators=(",", ":")), encoding="utf-8")
    (output_dir / "promotion-workflow-gate-binding.json").write_text(json.dumps(binding, separators=(",", ":")), encoding="utf-8")
    (output_dir / "promotion-boundary-job-id.txt").write_text(str(matches[0]["id"]), encoding="utf-8")
    return int(matches[0]["id"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="readiness-snapshot.json")
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--input")
    parser.add_argument("--collect-run-evidence", action="store_true")
    parser.add_argument("--run-id", type=int)
    parser.add_argument("--output-dir", default=".")
    args = parser.parse_args(argv)
    try:
        if args.collect_run_evidence:
            if not args.run_id:
                raise SnapshotError("RUN_ID_REQUIRED")
            client = GitHubClient(repo=os.environ["GH_REPOSITORY"], token=os.environ["GH_TOKEN"])
            collect_run_evidence(client, run_id=args.run_id, output_dir=Path(args.output_dir), source_commit=os.environ.get("GITHUB_SHA", ""))
            return 0
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
