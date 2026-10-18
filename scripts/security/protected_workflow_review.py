#!/usr/bin/env python3
"""Fail-closed parsing helpers for the protected workflow review gate."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROTECTED_PREFIXES = (
    ".github/workflows/",
    ".github/actions/",
    ".github/scripts/",
    ".githooks/",
    "scripts/security/",
)
TRUSTED_ASSOCIATIONS = {"OWNER", "MEMBER", "COLLABORATOR"}
MAX_PULL_REQUEST_FILES = 3000


def load_pages(path: str | Path) -> list[list[dict[str, Any]]]:
    """Load and validate gh --paginate --slurp output."""
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("GitHub API response is unreadable or invalid JSON") from exc

    if not isinstance(value, list):
        raise ValueError("GitHub API response must contain a page array")
    pages: list[list[dict[str, Any]]] = []
    for page in value:
        if not isinstance(page, list):
            raise ValueError("GitHub API response contains a malformed page")
        if any(not isinstance(item, dict) for item in page):
            raise ValueError("GitHub API response contains a malformed record")
        pages.append(page)
    return pages


def protected_paths(pages: list[list[dict[str, Any]]]) -> list[str]:
    """Return protected source/destination paths without splitting filenames."""
    found: list[str] = []
    file_count = 0
    for page in pages:
        for item in page:
            file_count += 1
            if file_count >= MAX_PULL_REQUEST_FILES:
                raise ValueError("GitHub changed-file list reached its 3000-file limit")
            filename = item.get("filename")
            if not isinstance(filename, str) or not filename:
                raise ValueError("GitHub file record is missing a valid filename")
            if filename.startswith(PROTECTED_PREFIXES):
                found.append(filename)
            previous_filename = item.get("previous_filename")
            if previous_filename is not None:
                if not isinstance(previous_filename, str) or not previous_filename:
                    raise ValueError("GitHub rename record has an invalid previous filename")
                if previous_filename.startswith(PROTECTED_PREFIXES):
                    found.append(previous_filename)
            elif item.get("status") == "renamed":
                raise ValueError("GitHub rename record is missing its previous filename")
    return found


def _submitted_at(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if not isinstance(value, str):
        raise ValueError("GitHub review has a malformed submission timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("GitHub review has a malformed submission timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError("GitHub review timestamp has no timezone")
    return parsed.astimezone(timezone.utc)


def has_trusted_current_approval(
    pages: list[list[dict[str, Any]]], *, head_sha: str, pr_author: str
) -> bool:
    """Require the latest submitted review by a trusted non-author to approve this head."""
    if not head_sha or not pr_author:
        raise ValueError("PR head SHA and author are required")

    author_key = pr_author.casefold()
    latest_reviews: dict[str, tuple[datetime, int, dict[str, Any]]] = {}
    for page in pages:
        for review in page:
            user = review.get("user")
            if not isinstance(user, dict) or not isinstance(user.get("login"), str):
                raise ValueError("GitHub review record is missing reviewer identity")
            reviewer = user["login"]
            if not reviewer:
                raise ValueError("GitHub review record has an empty reviewer identity")
            user_type = user.get("type")
            if not isinstance(user_type, str) or not user_type:
                raise ValueError("GitHub review record is missing reviewer account type")
            if user_type != "User":
                # Bot and other non-human accounts cannot satisfy the approval gate.
                continue
            state = review.get("state")
            if not isinstance(state, str):
                raise ValueError("GitHub review record is missing review state")
            review_id = review.get("id")
            if not isinstance(review_id, int) or isinstance(review_id, bool) or review_id < 0:
                raise ValueError("GitHub review record is missing a valid review ID")
            submitted_at = _submitted_at(review.get("submitted_at"))
            if submitted_at is None:
                # Pending reviews are not approvals and cannot supersede a submitted review.
                continue
            reviewer_key = reviewer.casefold()
            if reviewer_key == author_key:
                continue
            previous = latest_reviews.get(reviewer_key)
            if previous is None or (submitted_at, review_id) >= (previous[0], previous[1]):
                latest_reviews[reviewer_key] = (submitted_at, review_id, review)

    return any(
        review.get("state") == "APPROVED"
        and review.get("commit_id") == head_sha
        and review.get("author_association") in TRUSTED_ASSOCIATIONS
        for _, _, review in latest_reviews.values()
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--protected-files-json", metavar="PATH")
    mode.add_argument("--check-approval-json", metavar="PATH")
    parser.add_argument("--head-sha")
    parser.add_argument("--pr-author")
    args = parser.parse_args(argv)

    try:
        pages = load_pages(
            args.protected_files_json or args.check_approval_json
        )
        if args.protected_files_json:
            print(json.dumps(protected_paths(pages), ensure_ascii=True, separators=(",", ":")))
            return 0
        if not args.head_sha or not args.pr_author:
            raise ValueError("--check-approval-json requires --head-sha and --pr-author")
        if has_trusted_current_approval(
            pages, head_sha=args.head_sha, pr_author=args.pr_author
        ):
            print("protected workflow/security changes have a current trusted approval")
            return 0
        print(
            "::error::protected workflow/security changes require a current approval "
            "from a trusted repository collaborator",
            file=sys.stderr,
        )
        return 1
    except ValueError as exc:
        print(f"::error::{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
