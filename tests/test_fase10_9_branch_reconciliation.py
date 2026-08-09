from __future__ import annotations

import subprocess
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock
from pathlib import Path

from scripts.security.f109_boundary import (
    BoundaryError,
    CERT_BASE,
    CERT_ANCHOR,
    CERT_ALLOWED_STATUSES,
    DEV_ARCHIVE_TREE,
    DEV_BASE,
    DEV_EXTRACTION,
    MAIN_SOURCE,
    MAIN_SOURCE_TREE,
    P1_ALLOWED_STATUSES,
    changed_statuses,
    detect_mode,
    main,
    require_exact_delta,
    validate_cert,
    validate_context_graph,
    validate_dev,
    validate_p1,
)


def run(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


class F109BoundaryTest(unittest.TestCase):
    def make_repo(self) -> Path:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        repo = Path(temp.name)
        run(repo, "init")
        run(repo, "config", "user.email", "test@example.invalid")
        run(repo, "config", "user.name", "F10.9 Test")
        return repo

    def commit(self, repo: Path, message: str) -> str:
        run(repo, "add", ".")
        run(repo, "commit", "-m", message)
        return run(repo, "rev-parse", "HEAD")

    def test_exact_delta_accepts_expected_path(self) -> None:
        repo = self.make_repo()
        path = repo / "allowed.txt"
        path.write_text("before\n", encoding="utf-8")
        base = self.commit(repo, "base")
        path.write_text("after\n", encoding="utf-8")
        head = self.commit(repo, "head")

        require_exact_delta(repo, base, head, {"allowed.txt": "M"})
        self.assertEqual(changed_statuses(repo, base, head), {"allowed.txt": "M"})

    def test_exact_delta_rejects_extra_path(self) -> None:
        repo = self.make_repo()
        (repo / "allowed.txt").write_text("before\n", encoding="utf-8")
        base = self.commit(repo, "base")
        (repo / "allowed.txt").write_text("after\n", encoding="utf-8")
        (repo / "extra.txt").write_text("extra\n", encoding="utf-8")
        head = self.commit(repo, "head")

        with self.assertRaises(BoundaryError):
            require_exact_delta(repo, base, head, {"allowed.txt": "M"})

    def test_exact_delta_rejects_executable_mode(self) -> None:
        repo = self.make_repo()
        (repo / "README.md").write_text("base\n", encoding="utf-8")
        base = self.commit(repo, "base")
        path = repo / "script.sh"
        path.write_text("#!/bin/sh\n", encoding="utf-8")
        path.chmod(0o755)
        head = self.commit(repo, "head")

        with self.assertRaises(BoundaryError):
            require_exact_delta(repo, base, head, {"script.sh": "A"})

    def test_context_graph_accepts_existing_target(self) -> None:
        repo = self.make_repo()
        context = repo / ".context"
        context.mkdir()
        (context / "target.md").write_text("# Target\n", encoding="utf-8")
        (context / "source.md").write_text("[Target](target.md)\n", encoding="utf-8")

        validate_context_graph(repo, expected_files=2, expected_links=1)

    def test_context_graph_rejects_missing_target(self) -> None:
        repo = self.make_repo()
        context = repo / ".context"
        context.mkdir()
        (context / "source.md").write_text("[Missing](missing.md)\n", encoding="utf-8")

        with self.assertRaises(BoundaryError):
            validate_context_graph(repo, expected_files=1, expected_links=1)

    def test_context_graph_rejects_path_escape(self) -> None:
        repo = self.make_repo()
        context = repo / ".context"
        context.mkdir()
        outside = repo.parent / "outside.md"
        outside.write_text("# Outside\n", encoding="utf-8")
        self.addCleanup(outside.unlink)
        (context / "source.md").write_text("[Outside](../../outside.md)\n", encoding="utf-8")

        with self.assertRaises(BoundaryError):
            validate_context_graph(repo, expected_files=1, expected_links=1)

    def test_context_graph_rejects_forbidden_path(self) -> None:
        repo = self.make_repo()
        context = repo / ".context"
        context.mkdir()
        forbidden = context / "ca2.md"
        forbidden.write_text("# CA2\n", encoding="utf-8")

        with self.assertRaises(BoundaryError):
            validate_context_graph(
                repo,
                expected_files=1,
                expected_links=0,
                forbidden_paths={".context/ca2.md"},
            )

    def test_context_graph_rejects_blob_drift(self) -> None:
        repo = self.make_repo()
        context = repo / ".context"
        context.mkdir()
        path = context / "authority.md"
        path.write_text("# Drift\n", encoding="utf-8")

        with self.assertRaises(BoundaryError):
            validate_context_graph(
                repo,
                expected_files=1,
                expected_links=0,
                expected_blobs={".context/authority.md": "0" * 40},
            )

    def test_mode_detection_is_fail_closed(self) -> None:
        self.assertEqual(detect_mode("pull_request", "other", "branch", "0" * 40), "skip")
        self.assertEqual(
            detect_mode(
                "pull_request",
                "desarrollo",
                "fix/f10-9-p1-rebuilt",
                "1" * 40,
            ),
            "skip",
        )
        self.assertEqual(
            detect_mode(
                "push",
                "desarrollo",
                "desarrollo",
                "1" * 40,
                p1_base="1" * 40,
            ),
            "p1",
        )

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_cert_validator_checks_anchor_contract(
        self,
        require_sha_mock,
        commit_tree_mock,
        commit_parents_mock,
        is_ancestor_mock,
        delta_mock,
        graph_mock,
    ) -> None:
        commit_tree_mock.return_value = MAIN_SOURCE_TREE
        commit_parents_mock.return_value = [CERT_BASE, MAIN_SOURCE]

        validate_cert(Path("."), CERT_BASE, "a" * 40, "pull_request")

        delta_mock.assert_called_once()
        graph_mock.assert_called_once()

    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_p1_validator_requires_frozen_base(
        self,
        require_sha_mock,
        is_ancestor_mock,
        delta_mock,
        parents_mock,
    ) -> None:
        parents_mock.return_value = ["a" * 40]
        validate_p1(Path("."), "a" * 40, "b" * 40, "a" * 40, "pull_request")
        delta_mock.assert_called_once()
        with self.assertRaises(BoundaryError):
            validate_p1(Path("."), "a" * 40, "b" * 40, "c" * 40, "pull_request")

    @mock.patch("scripts.security.f109_boundary.commit_parents", return_value=["c" * 40])
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_p1_validator_rejects_non_direct_parent(
        self,
        require_sha_mock,
        is_ancestor_mock,
        delta_mock,
        parents_mock,
    ) -> None:
        with self.assertRaises(BoundaryError):
            validate_p1(Path("."), "a" * 40, "b" * 40, "a" * 40, "pull_request")

    @mock.patch("scripts.security.f109_boundary.git")
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_dev_validator_rejects_non_merge_history(
        self,
        require_sha_mock,
        commit_tree_mock,
        commit_parents_mock,
        is_ancestor_mock,
        git_mock,
    ) -> None:
        merge_commit = "c" * 40
        cert_tip = "d" * 40
        head = merge_commit

        def tree(repo, commit):
            if commit == DEV_BASE:
                return DEV_ARCHIVE_TREE
            if commit == DEV_EXTRACTION:
                return MAIN_SOURCE_TREE
            return "e" * 40

        def parents(repo, commit):
            if commit == DEV_EXTRACTION:
                return [DEV_BASE]
            if commit == merge_commit:
                return [DEV_EXTRACTION]
            return []

        def git_output(repo, *args, **kwargs):
            if args[:2] == ("rev-parse", "refs/remotes/origin/archive/f10-9-ca2-preserve-desarrollo-20260809"):
                return DEV_BASE
            if args[:3] == ("rev-list", "--reverse", "--first-parent"):
                return f"{DEV_EXTRACTION}\n{merge_commit}\n"
            if args[:1] == ("rev-list",):
                return f"{DEV_EXTRACTION}\n{merge_commit}\n{cert_tip}\n"
            raise AssertionError(args)

        commit_tree_mock.side_effect = tree
        commit_parents_mock.side_effect = parents
        git_mock.side_effect = git_output

        with self.assertRaises(BoundaryError):
            validate_dev(Path("."), DEV_BASE, head, "pull_request", cert_tip)

    @mock.patch("scripts.security.f109_boundary.parse_args")
    def test_cli_rejects_fork(self, parse_args_mock) -> None:
        parse_args_mock.return_value = SimpleNamespace(
            repo=Path("."),
            event="pull_request",
            base_ref="certificacion",
            head_ref="branch",
            base_sha=CERT_BASE,
            head_sha="a" * 40,
            base_repo="owner/repo",
            head_repo="fork/repo",
            cert_tip="",
            p1_base="",
        )

        self.assertEqual(main(), 1)

    def test_cert_allowlist_contains_only_documented_surfaces(self) -> None:
        self.assertIn(".github/workflows/security-audit.yml", CERT_ALLOWED_STATUSES)
        self.assertIn("scripts/security/f109_boundary.py", CERT_ALLOWED_STATUSES)
        self.assertNotIn("db/migrations/example.sql", CERT_ALLOWED_STATUSES)
        self.assertNotIn("web/src/app/page.tsx", CERT_ALLOWED_STATUSES)

    def test_p1_allowlist_is_exact(self) -> None:
        self.assertEqual(
            P1_ALLOWED_STATUSES,
            {
                "scripts/shared/db_client.py": "M",
                "scripts/shared/safe_http.py": "A",
                "scripts/shared/url_identity.py": "A",
                "scripts/shared/utils.py": "M",
                "tests/test_fase10_9_p1_safety_contracts.py": "A",
            },
        )


if __name__ == "__main__":
    unittest.main()
