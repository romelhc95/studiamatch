import json

import pytest

from scripts.security.protected_workflow_review import (
    has_trusted_current_approval,
    load_pages,
    protected_paths,
)


def review(login, state, association, sha, submitted_at, review_id=1, user_type="User"):
    return {
        "id": review_id,
        "user": {"login": login, "type": user_type},
        "state": state,
        "author_association": association,
        "commit_id": sha,
        "submitted_at": submitted_at,
    }


def test_classifies_protected_path_prefixes_without_splitting_filenames():
    pages = [[
        {"filename": ".github/workflows/build.yml"},
        {"filename": ".github/actions/lint/action.yml"},
        {"filename": ".github/scripts/production_control_preflight.sh"},
        {"filename": ".githooks/pre-commit"},
        {"filename": "scripts/security/scan_credentials.sh"},
        {"filename": "docs/readme\n.github/workflows/injected.yml"},
        {"filename": "README.md"},
    ]]

    assert protected_paths(pages) == [
        ".github/workflows/build.yml",
        ".github/actions/lint/action.yml",
        ".github/scripts/production_control_preflight.sh",
        ".githooks/pre-commit",
        "scripts/security/scan_credentials.sh",
    ]


def test_load_pages_rejects_malformed_or_unreadable_responses(tmp_path):
    response = tmp_path / "response.json"
    for payload in ("{}", "[{}]", "[[null]]", "not-json"):
        response.write_text(payload, encoding="utf-8")
        with pytest.raises(ValueError):
            load_pages(response)

    with pytest.raises(ValueError):
        load_pages(tmp_path / "missing.json")


def test_protected_paths_rejects_missing_filenames():
    with pytest.raises(ValueError):
        protected_paths([[{"status": "modified"}]])


def test_renamed_file_checks_both_current_and_previous_paths():
    pages = [[
        {
            "filename": "docs/workflow.txt",
            "previous_filename": ".github/workflows/security.yml",
            "status": "renamed",
        },
        {
            "filename": ".githooks/pre-push",
            "previous_filename": "docs/pre-push.txt",
            "status": "renamed",
        },
        {
            "filename": ".github/actions/new/action.yml",
            "previous_filename": ".github/actions/old/action.yml",
            "status": "renamed",
        },
    ]]

    assert protected_paths(pages) == [
        ".github/workflows/security.yml",
        ".githooks/pre-push",
        ".github/actions/new/action.yml",
        ".github/actions/old/action.yml",
    ]


@pytest.mark.parametrize(
    "record",
    [
        {"filename": "docs/workflow.txt", "previous_filename": "", "status": "renamed"},
        {"filename": "docs/workflow.txt", "previous_filename": 7, "status": "renamed"},
        {"filename": "docs/workflow.txt", "status": "renamed"},
    ],
)
def test_renamed_file_requires_a_valid_previous_path(record):
    with pytest.raises(ValueError):
        protected_paths([[record]])


def test_changed_file_list_at_github_api_limit_fails_closed():
    pages = [[{"filename": f"docs/file-{index}.md"} for index in range(3000)]]

    with pytest.raises(ValueError, match="3000-file limit"):
        protected_paths(pages)


def test_current_trusted_approval_is_required_and_latest_review_wins():
    head = "a" * 40
    approved = review(
        "trusted-reviewer",
        "APPROVED",
        "MEMBER",
        head,
        "2026-10-08T12:00:00Z",
    )
    assert has_trusted_current_approval(
        [[approved]], head_sha=head, pr_author="author"
    )

    stale = review(
        "trusted-reviewer",
        "APPROVED",
        "MEMBER",
        "b" * 40,
        "2026-10-08T12:00:00Z",
    )
    assert not has_trusted_current_approval(
        [[stale]], head_sha=head, pr_author="author"
    )

    self_approval = review(
        "author",
        "APPROVED",
        "OWNER",
        head,
        "2026-10-08T12:00:00Z",
    )
    assert not has_trusted_current_approval(
        [[self_approval]], head_sha=head, pr_author="author"
    )

    untrusted = review(
        "external-reviewer",
        "APPROVED",
        "FIRST_TIME_CONTRIBUTOR",
        head,
        "2026-10-08T12:00:00Z",
    )
    assert not has_trusted_current_approval(
        [[untrusted]], head_sha=head, pr_author="author"
    )

    bot_approval = review(
        "trusted-bot",
        "APPROVED",
        "MEMBER",
        head,
        "2026-10-08T12:00:00Z",
        user_type="Bot",
    )
    assert not has_trusted_current_approval(
        [[bot_approval]], head_sha=head, pr_author="author"
    )

    dismissed_later = review(
        "trusted-reviewer",
        "DISMISSED",
        "MEMBER",
        head,
        "2026-10-08T13:00:00Z",
        review_id=2,
    )
    assert not has_trusted_current_approval(
        [[approved, dismissed_later]], head_sha=head, pr_author="author"
    )


def test_pending_review_does_not_replace_a_submitted_approval():
    head = "a" * 40
    approved = review(
        "trusted-reviewer",
        "APPROVED",
        "COLLABORATOR",
        head,
        "2026-10-08T12:00:00Z",
    )
    pending = review(
        "trusted-reviewer",
        "PENDING",
        "COLLABORATOR",
        head,
        None,
        review_id=2,
    )
    assert has_trusted_current_approval(
        [[approved, pending]], head_sha=head, pr_author="author"
    )


def test_missing_reviewer_account_type_fails_closed():
    head = "a" * 40
    malformed = review(
        "trusted-reviewer",
        "APPROVED",
        "MEMBER",
        head,
        "2026-10-08T12:00:00Z",
    )
    del malformed["user"]["type"]

    with pytest.raises(ValueError, match="reviewer account type"):
        has_trusted_current_approval(
            [[malformed]], head_sha=head, pr_author="author"
        )


def test_equal_timestamp_reviews_use_github_review_id_as_tie_breaker():
    head = "a" * 40
    older_approval = review(
        "trusted-reviewer",
        "APPROVED",
        "MEMBER",
        head,
        "2026-10-08T12:00:00Z",
        review_id=10,
    )
    newer_dismissal = review(
        "trusted-reviewer",
        "DISMISSED",
        "MEMBER",
        head,
        "2026-10-08T12:00:00Z",
        review_id=11,
    )

    assert not has_trusted_current_approval(
        [[newer_dismissal, older_approval]], head_sha=head, pr_author="author"
    )


def test_loaded_filename_newline_is_not_split_into_an_additional_path(tmp_path):
    response = tmp_path / "files.json"
    response.write_text(
        json.dumps([[{"filename": "README.md\n.github/workflows/fake.yml"}]]),
        encoding="utf-8",
    )
    assert protected_paths(load_pages(response)) == []
