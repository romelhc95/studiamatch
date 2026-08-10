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
    CERT_ALLOWED_MODES,
    CERT_ALLOWED_STATUSES,
    DEV_ARCHIVE_TREE,
    DEV_BASE,
    DEV_EXTRACTION,
    G2_ALLOWED_MODES,
    G2_ALLOWED_STATUSES,
    G2_HEAD_REF,
    G2_WIRING_ALLOWED_MODES,
    G2_WIRING_ALLOWED_STATUSES,
    G2_WIRING_HEAD_REF,
    MAIN_SOURCE,
    MAIN_SOURCE_TREE,
    P1_ALLOWED_STATUSES,
    P1_HEAD_REF,
    P2_ALLOWED_STATUSES,
    P2_HEAD_REF,
    P2_WIRING_ALLOWED_STATUSES,
    P2_WIRING_HEAD_REF,
    P5_ALLOWED_MODES,
    P5_ALLOWED_STATUSES,
    P5_HEAD_REF,
    P5_WIRING_ALLOWED_MODES,
    P5_WIRING_ALLOWED_STATUSES,
    P5_WIRING_HEAD_REF,
    POST_G2_DEV_BASE,
    POST_G2_DEV_TREE,
    POST_P1_DEV_BASE,
    POST_P1_DEV_TREE,
    POST_P2_DEV_BASE,
    POST_P2_DEV_TREE,
    POST_R0_DEV_BASE,
    POST_R0_DEV_TREE,
    WIRING_ALLOWED_STATUSES,
    WIRING_HEAD_REF,
    changed_statuses,
    detect_mode,
    main,
    require_exact_delta,
    validate_cert,
    validate_context_graph,
    validate_dev,
    validate_g2,
    validate_g2_wiring,
    validate_non_p1_delta,
    validate_p1,
    validate_p2,
    validate_p2_wiring,
    validate_p5,
    validate_p5_wiring,
    validate_wiring,
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

    def test_exact_delta_rejects_modified_file_mode_drift(self) -> None:
        repo = self.make_repo()
        path = repo / "p1.py"
        path.write_text("value = 1\n", encoding="utf-8")
        base = self.commit(repo, "base")
        path.write_text("value = 2\n", encoding="utf-8")
        path.chmod(0o755)
        head = self.commit(repo, "mode drift")

        with self.assertRaises(BoundaryError):
            require_exact_delta(repo, base, head, {"p1.py": "M"})

    def test_exact_delta_rejects_deletion(self) -> None:
        repo = self.make_repo()
        path = repo / "p1.py"
        path.write_text("value = 1\n", encoding="utf-8")
        base = self.commit(repo, "base")
        path.unlink()
        head = self.commit(repo, "delete")

        with self.assertRaises(BoundaryError):
            require_exact_delta(repo, base, head, {"p1.py": "M"})

    def test_exact_delta_rejects_rename(self) -> None:
        repo = self.make_repo()
        old_path = repo / "old.py"
        old_path.write_text("value = 1\n", encoding="utf-8")
        base = self.commit(repo, "base")
        old_path.rename(repo / "new.py")
        head = self.commit(repo, "rename")

        with self.assertRaises(BoundaryError):
            require_exact_delta(repo, base, head, {"new.py": "A"})

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

    def test_context_graph_ignores_private_local_artifacts(self) -> None:
        repo = self.make_repo()
        context = repo / ".context"
        private = context / "artifacts" / "private"
        private.mkdir(parents=True)
        (context / "authority.md").write_text("# Authority\n", encoding="utf-8")
        (private / "evidence.md").write_text("[Missing](missing.md)\n", encoding="utf-8")

        validate_context_graph(repo, expected_files=1, expected_links=0)

    def test_context_graph_rejects_tracked_private_artifacts(self) -> None:
        repo = self.make_repo()
        private = repo / ".context" / "artifacts" / "private"
        private.mkdir(parents=True)
        (private / "evidence.md").write_text("# Private\n", encoding="utf-8")
        self.commit(repo, "track private evidence")

        with self.assertRaises(BoundaryError):
            validate_context_graph(repo, expected_files=0, expected_links=0)

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
            "skip",
        )
        self.assertEqual(
            detect_mode(
                "pull_request",
                "desarrollo",
                WIRING_HEAD_REF,
                POST_R0_DEV_BASE,
            ),
            "wiring",
        )
        self.assertEqual(
            detect_mode(
                "pull_request",
                "desarrollo",
                "fix/f10-9-p1-rebuilt",
                "2" * 40,
                p1_base="2" * 40,
            ),
            "p1",
        )
        self.assertEqual(
            detect_mode(
                "pull_request",
                "desarrollo",
                P2_WIRING_HEAD_REF,
                POST_P1_DEV_BASE,
            ),
            "p2_wiring",
        )
        self.assertEqual(
            detect_mode(
                "pull_request",
                "desarrollo",
                P2_HEAD_REF,
                "3" * 40,
                p2_base="3" * 40,
            ),
            "p2",
        )
        self.assertEqual(
            detect_mode(
                "pull_request",
                "desarrollo",
                G2_WIRING_HEAD_REF,
                POST_P2_DEV_BASE,
            ),
            "g2_wiring",
        )
        self.assertEqual(
            detect_mode(
                "pull_request",
                "desarrollo",
                G2_HEAD_REF,
                "4" * 40,
                g2_base="4" * 40,
            ),
            "g2",
        )
        self.assertEqual(
            detect_mode(
                "pull_request",
                "desarrollo",
                P5_WIRING_HEAD_REF,
                POST_G2_DEV_BASE,
            ),
            "p5_wiring",
        )
        self.assertEqual(
            detect_mode(
                "pull_request",
                "desarrollo",
                P5_HEAD_REF,
                "5" * 40,
                p5_base="5" * 40,
            ),
            "p5",
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

    @mock.patch("scripts.security.f109_boundary.commit_tree", return_value="d" * 40)
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
        tree_mock,
    ) -> None:
        parents_mock.return_value = ["a" * 40]
        validate_p1(Path("."), "a" * 40, "b" * 40, "a" * 40, "d" * 40, "pull_request")
        delta_mock.assert_called_once()
        with self.assertRaises(BoundaryError):
            validate_p1(Path("."), "a" * 40, "b" * 40, "c" * 40, "d" * 40, "pull_request")

    @mock.patch("scripts.security.f109_boundary.commit_tree", return_value="d" * 40)
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
        tree_mock,
    ) -> None:
        with self.assertRaises(BoundaryError):
            validate_p1(Path("."), "a" * 40, "b" * 40, "a" * 40, "d" * 40, "pull_request")

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.git")
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_wiring_pr_is_one_exact_commit(
        self,
        require_sha_mock,
        git_mock,
        tree_mock,
        parents_mock,
        delta_mock,
        graph_mock,
    ) -> None:
        git_mock.return_value = DEV_BASE
        tree_mock.side_effect = lambda repo, commit: (
            POST_R0_DEV_TREE if commit == POST_R0_DEV_BASE else DEV_ARCHIVE_TREE
        )
        parents_mock.return_value = [POST_R0_DEV_BASE]

        validate_wiring(Path("."), POST_R0_DEV_BASE, "b" * 40, "pull_request")

        delta_mock.assert_called_once()
        graph_mock.assert_called_once()
        self.assertEqual(graph_mock.call_args.kwargs["expected_files"], 42)
        self.assertEqual(graph_mock.call_args.kwargs["expected_links"], 341)

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.git")
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_wiring_push_validates_merge_and_single_commit_pr(
        self,
        require_sha_mock,
        git_mock,
        tree_mock,
        parents_mock,
        delta_mock,
        graph_mock,
    ) -> None:
        pr_head = "b" * 40
        merge_head = "c" * 40
        git_mock.return_value = DEV_BASE

        def tree(repo, commit):
            if commit == POST_R0_DEV_BASE:
                return POST_R0_DEV_TREE
            if commit == DEV_BASE:
                return DEV_ARCHIVE_TREE
            return "d" * 40

        def parents(repo, commit):
            if commit == merge_head:
                return [POST_R0_DEV_BASE, pr_head]
            if commit == pr_head:
                return [POST_R0_DEV_BASE]
            return []

        tree_mock.side_effect = tree
        parents_mock.side_effect = parents

        validate_wiring(Path("."), POST_R0_DEV_BASE, merge_head, "push")

        delta_mock.assert_called_once_with(
            Path("."),
            POST_R0_DEV_BASE,
            pr_head,
            WIRING_ALLOWED_STATUSES,
            mock.ANY,
        )
        graph_mock.assert_called_once()

    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_p1_push_validates_merge_and_single_commit_pr(
        self,
        require_sha_mock,
        ancestor_mock,
        tree_mock,
        parents_mock,
        delta_mock,
    ) -> None:
        base = "a" * 40
        pr_head = "b" * 40
        merge_head = "c" * 40
        base_tree = "d" * 40
        tree_mock.return_value = base_tree

        def parents(repo, commit):
            if commit == merge_head:
                return [base, pr_head]
            if commit == pr_head:
                return [base]
            return []

        parents_mock.side_effect = parents

        validate_p1(Path("."), base, merge_head, base, base_tree, "push")

        delta_mock.assert_called_once_with(Path("."), base, pr_head, P1_ALLOWED_STATUSES)

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents", return_value=[POST_P1_DEV_BASE])
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.git", return_value=DEV_BASE)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_p2_wiring_pr_is_one_exact_commit(
        self,
        require_sha_mock,
        git_mock,
        tree_mock,
        parents_mock,
        delta_mock,
        graph_mock,
    ) -> None:
        tree_mock.side_effect = lambda repo, commit: (
            POST_P1_DEV_TREE if commit == POST_P1_DEV_BASE else DEV_ARCHIVE_TREE
        )

        validate_p2_wiring(Path("."), POST_P1_DEV_BASE, "b" * 40, "pull_request")

        delta_mock.assert_called_once_with(
            Path("."),
            POST_P1_DEV_BASE,
            "b" * 40,
            P2_WIRING_ALLOWED_STATUSES,
            mock.ANY,
        )
        self.assertEqual(graph_mock.call_args.kwargs["expected_files"], 42)
        self.assertEqual(graph_mock.call_args.kwargs["expected_links"], 341)

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.git", return_value=DEV_BASE)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_p2_wiring_push_validates_merge_and_single_commit_pr(
        self,
        require_sha_mock,
        git_mock,
        tree_mock,
        parents_mock,
        delta_mock,
        graph_mock,
    ) -> None:
        pr_head = "b" * 40
        merge_head = "c" * 40

        def tree(repo, commit):
            if commit == POST_P1_DEV_BASE:
                return POST_P1_DEV_TREE
            if commit == DEV_BASE:
                return DEV_ARCHIVE_TREE
            return "d" * 40

        def parents(repo, commit):
            if commit == merge_head:
                return [POST_P1_DEV_BASE, pr_head]
            if commit == pr_head:
                return [POST_P1_DEV_BASE]
            return []

        tree_mock.side_effect = tree
        parents_mock.side_effect = parents

        validate_p2_wiring(Path("."), POST_P1_DEV_BASE, merge_head, "push")

        delta_mock.assert_called_once_with(
            Path("."),
            POST_P1_DEV_BASE,
            pr_head,
            P2_WIRING_ALLOWED_STATUSES,
            mock.ANY,
        )
        graph_mock.assert_called_once()

    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents", return_value=["a" * 40])
    @mock.patch("scripts.security.f109_boundary.commit_tree", return_value="d" * 40)
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_p2_pr_requires_frozen_direct_base(
        self,
        require_sha_mock,
        ancestor_mock,
        tree_mock,
        parents_mock,
        delta_mock,
    ) -> None:
        validate_p2(Path("."), "a" * 40, "b" * 40, "a" * 40, "d" * 40, "pull_request")
        delta_mock.assert_called_once_with(Path("."), "a" * 40, "b" * 40, P2_ALLOWED_STATUSES)

        with self.assertRaises(BoundaryError):
            validate_p2(Path("."), "a" * 40, "b" * 40, "c" * 40, "d" * 40, "pull_request")

    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_p2_push_validates_merge_and_single_commit_pr(
        self,
        require_sha_mock,
        ancestor_mock,
        tree_mock,
        parents_mock,
        delta_mock,
    ) -> None:
        base = "a" * 40
        pr_head = "b" * 40
        merge_head = "c" * 40
        base_tree = "d" * 40
        tree_mock.return_value = base_tree

        def parents(repo, commit):
            if commit == merge_head:
                return [base, pr_head]
            if commit == pr_head:
                return [base]
            return []

        parents_mock.side_effect = parents

        validate_p2(Path("."), base, merge_head, base, base_tree, "push")

        delta_mock.assert_called_once_with(Path("."), base, pr_head, P2_ALLOWED_STATUSES)

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents", return_value=[POST_P2_DEV_BASE])
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.git", return_value=DEV_BASE)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_g2_wiring_pr_is_one_exact_commit(
        self,
        require_sha_mock,
        git_mock,
        tree_mock,
        parents_mock,
        delta_mock,
        graph_mock,
    ) -> None:
        tree_mock.side_effect = lambda repo, commit: (
            POST_P2_DEV_TREE if commit == POST_P2_DEV_BASE else DEV_ARCHIVE_TREE
        )

        validate_g2_wiring(Path("."), POST_P2_DEV_BASE, "b" * 40, "pull_request")

        delta_mock.assert_called_once_with(
            Path("."),
            POST_P2_DEV_BASE,
            "b" * 40,
            G2_WIRING_ALLOWED_STATUSES,
            G2_WIRING_ALLOWED_MODES,
        )
        self.assertEqual(graph_mock.call_args.kwargs["expected_files"], 43)
        self.assertEqual(graph_mock.call_args.kwargs["expected_links"], 344)

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.git", return_value=DEV_BASE)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_g2_wiring_push_validates_merge_and_single_commit_pr(
        self,
        require_sha_mock,
        git_mock,
        tree_mock,
        parents_mock,
        delta_mock,
        graph_mock,
    ) -> None:
        pr_head = "b" * 40
        merge_head = "c" * 40

        def tree(repo, commit):
            if commit == POST_P2_DEV_BASE:
                return POST_P2_DEV_TREE
            if commit == DEV_BASE:
                return DEV_ARCHIVE_TREE
            return "d" * 40

        def parents(repo, commit):
            if commit == merge_head:
                return [POST_P2_DEV_BASE, pr_head]
            if commit == pr_head:
                return [POST_P2_DEV_BASE]
            return []

        tree_mock.side_effect = tree
        parents_mock.side_effect = parents

        validate_g2_wiring(Path("."), POST_P2_DEV_BASE, merge_head, "push")

        delta_mock.assert_called_once_with(
            Path("."),
            POST_P2_DEV_BASE,
            pr_head,
            G2_WIRING_ALLOWED_STATUSES,
            G2_WIRING_ALLOWED_MODES,
        )
        graph_mock.assert_called_once()

    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents", return_value=["a" * 40])
    @mock.patch("scripts.security.f109_boundary.commit_tree", return_value="d" * 40)
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_g2_pr_requires_frozen_direct_base(
        self,
        require_sha_mock,
        ancestor_mock,
        tree_mock,
        parents_mock,
        delta_mock,
    ) -> None:
        validate_g2(Path("."), "a" * 40, "b" * 40, "a" * 40, "d" * 40, "pull_request")
        delta_mock.assert_called_once_with(
            Path("."), "a" * 40, "b" * 40, G2_ALLOWED_STATUSES, G2_ALLOWED_MODES
        )

        with self.assertRaises(BoundaryError):
            validate_g2(Path("."), "a" * 40, "b" * 40, "c" * 40, "d" * 40, "pull_request")

    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_g2_push_validates_merge_and_single_commit_pr(
        self,
        require_sha_mock,
        ancestor_mock,
        tree_mock,
        parents_mock,
        delta_mock,
    ) -> None:
        base = "a" * 40
        pr_head = "b" * 40
        merge_head = "c" * 40
        base_tree = "d" * 40
        tree_mock.return_value = base_tree

        def parents(repo, commit):
            if commit == merge_head:
                return [base, pr_head]
            if commit == pr_head:
                return [base]
            return []

        parents_mock.side_effect = parents

        validate_g2(Path("."), base, merge_head, base, base_tree, "push")

        delta_mock.assert_called_once_with(
            Path("."), base, pr_head, G2_ALLOWED_STATUSES, G2_ALLOWED_MODES
        )

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents", return_value=[POST_G2_DEV_BASE])
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.git", return_value=DEV_BASE)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_p5_wiring_pr_is_one_exact_commit(
        self,
        require_sha_mock,
        git_mock,
        tree_mock,
        parents_mock,
        delta_mock,
        graph_mock,
    ) -> None:
        tree_mock.side_effect = lambda repo, commit: (
            POST_G2_DEV_TREE if commit == POST_G2_DEV_BASE else DEV_ARCHIVE_TREE
        )

        validate_p5_wiring(Path("."), POST_G2_DEV_BASE, "b" * 40, "pull_request")

        delta_mock.assert_called_once_with(
            Path("."),
            POST_G2_DEV_BASE,
            "b" * 40,
            P5_WIRING_ALLOWED_STATUSES,
            P5_WIRING_ALLOWED_MODES,
        )
        self.assertEqual(graph_mock.call_args.kwargs["expected_files"], 44)
        self.assertEqual(graph_mock.call_args.kwargs["expected_links"], 345)

    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents", return_value=["a" * 40])
    @mock.patch("scripts.security.f109_boundary.commit_tree", return_value="d" * 40)
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_p5_pr_requires_frozen_direct_base(
        self,
        require_sha_mock,
        ancestor_mock,
        tree_mock,
        parents_mock,
        delta_mock,
    ) -> None:
        validate_p5(Path("."), "a" * 40, "b" * 40, "a" * 40, "d" * 40, "pull_request")
        delta_mock.assert_called_once_with(
            Path("."), "a" * 40, "b" * 40, P5_ALLOWED_STATUSES, P5_ALLOWED_MODES
        )

        with self.assertRaises(BoundaryError):
            validate_p5(Path("."), "a" * 40, "b" * 40, "c" * 40, "d" * 40, "pull_request")

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

    @mock.patch("scripts.security.f109_boundary.git")
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_dev_push_validates_second_parent_history(
        self,
        require_sha_mock,
        commit_tree_mock,
        commit_parents_mock,
        is_ancestor_mock,
        git_mock,
    ) -> None:
        pr_head = "b" * 40
        merge_head = "c" * 40
        cert_tip = "d" * 40
        shared_tree = "e" * 40

        def tree(repo, commit):
            if commit == DEV_BASE:
                return DEV_ARCHIVE_TREE
            if commit == DEV_EXTRACTION:
                return MAIN_SOURCE_TREE
            return shared_tree

        def parents(repo, commit):
            if commit == DEV_EXTRACTION:
                return [DEV_BASE]
            if commit == pr_head:
                return [DEV_EXTRACTION, cert_tip]
            if commit == merge_head:
                return [DEV_BASE, pr_head]
            return []

        def git_output(repo, *args, **kwargs):
            if args[:2] == ("rev-parse", "refs/remotes/origin/archive/f10-9-ca2-preserve-desarrollo-20260809"):
                return DEV_BASE
            if args[:3] == ("rev-list", "--reverse", "--first-parent"):
                return f"{DEV_EXTRACTION}\n{pr_head}\n"
            if args[:1] == ("rev-list",):
                return f"{DEV_EXTRACTION}\n{pr_head}\n{cert_tip}\n"
            raise AssertionError(args)

        commit_tree_mock.side_effect = tree
        commit_parents_mock.side_effect = parents
        git_mock.side_effect = git_output

        validate_dev(Path("."), DEV_BASE, merge_head, "push", cert_tip)

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
            p1_base_tree="",
            p2_base="",
            p2_base_tree="",
            g2_base="",
            g2_base_tree="",
            github_output="",
        )

        self.assertEqual(main(), 1)

    def test_cert_allowlist_contains_only_documented_surfaces(self) -> None:
        self.assertIn(".github/workflows/security-audit.yml", CERT_ALLOWED_STATUSES)
        self.assertIn("scripts/security/f109_boundary.py", CERT_ALLOWED_STATUSES)
        self.assertNotIn("db/migrations/example.sql", CERT_ALLOWED_STATUSES)
        self.assertNotIn("web/src/app/page.tsx", CERT_ALLOWED_STATUSES)
        self.assertEqual(CERT_ALLOWED_MODES[".github/workflows/security-audit.yml"], "100755")
        self.assertEqual(CERT_ALLOWED_MODES[".github/workflows/f9-7-contract.yml"], "100644")

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

    def test_p2_allowlists_are_exact(self) -> None:
        self.assertEqual(
            P2_ALLOWED_STATUSES,
            {
                "scripts/shared/f10_9_readonly_planner.py": "A",
                "scripts/maintenance/f10_9_readonly_audit.py": "A",
                "tests/fixtures/f10_9_p2_synthetic.json": "A",
                "tests/test_fase10_9_p2_readonly_planners.py": "A",
            },
        )
        self.assertEqual(
            P2_WIRING_ALLOWED_STATUSES,
            {
                ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
                ".context/estado_del_proyecto.md": "M",
                ".context/operaciones/g0_r0_reconciliacion_f10_9.md": "M",
                ".context/operaciones/plan_remediacion_f10_9_fg2_fg3.md": "M",
                ".context/operaciones/r0_ci_boundary_manifest_2026_08_09.md": "M",
                ".context/operaciones/r0_post_merge_evidence_2026_08_09.md": "M",
                ".github/workflows/f9-7-contract.yml": "M",
                ".github/workflows/security-audit.yml": "M",
                "scripts/security/f109_boundary.py": "M",
                "tests/test_fase10_9_branch_reconciliation.py": "M",
            },
        )
        self.assertFalse(set(P2_ALLOWED_STATUSES).intersection(P1_ALLOWED_STATUSES))

    def test_g2_allowlists_are_exact_and_disjoint(self) -> None:
        self.assertEqual(
            G2_ALLOWED_STATUSES,
            {
                "scripts/core/master_orchestrator.py": "M",
                "scripts/core/integrity_ping.py": "M",
                "scripts/shared/f10_9_fg2_preflight.py": "A",
                "scripts/shared/f10_9_fg3_atomic.py": "A",
                "tests/test_fase10_9_p3_fg2_preflight.py": "A",
                "tests/test_fase10_9_p4_fg3_atomicity.py": "A",
            },
        )
        self.assertEqual(
            G2_WIRING_ALLOWED_STATUSES,
            {
                ".github/workflows/f9-7-contract.yml": "M",
                ".github/workflows/security-audit.yml": "M",
                "scripts/security/f109_boundary.py": "M",
                "tests/test_fase10_9_branch_reconciliation.py": "M",
            },
        )
        self.assertTrue(all(mode == "100644" for mode in G2_ALLOWED_MODES.values()))
        self.assertEqual(G2_WIRING_ALLOWED_MODES[".github/workflows/security-audit.yml"], "100755")
        self.assertFalse(set(G2_ALLOWED_STATUSES).intersection(P1_ALLOWED_STATUSES))
        self.assertFalse(set(G2_ALLOWED_STATUSES).intersection(P2_ALLOWED_STATUSES))

    def test_p5_allowlists_are_exact_and_disjoint(self) -> None:
        self.assertEqual(
            P5_ALLOWED_STATUSES,
            {
                "scripts/shared/f10_9_metadata_planner.py": "A",
                "tests/test_fase10_9_p5_metadata_readonly.py": "A",
            },
        )
        self.assertEqual(P5_WIRING_ALLOWED_STATUSES, G2_WIRING_ALLOWED_STATUSES)
        self.assertTrue(all(mode == "100644" for mode in P5_ALLOWED_MODES.values()))
        self.assertEqual(P5_WIRING_ALLOWED_MODES[".github/workflows/security-audit.yml"], "100755")
        for existing in (P1_ALLOWED_STATUSES, P2_ALLOWED_STATUSES, G2_ALLOWED_STATUSES):
            self.assertFalse(set(P5_ALLOWED_STATUSES).intersection(existing))

    def test_p2_workflow_wiring_is_hard_gated(self) -> None:
        root = Path(__file__).resolve().parents[1]
        for relative in (
            ".github/workflows/f9-7-contract.yml",
            ".github/workflows/security-audit.yml",
        ):
            workflow = (root / relative).read_text(encoding="utf-8")
            with self.subTest(workflow=relative):
                self.assertIn('F109_HEAD_REF" = "feat/f10-9-p2-readonly-planners"', workflow)
                self.assertIn('test "$F109_BASE_SHA" = "$protected_dev_tip"', workflow)
                self.assertIn('--p2-base "$p2_base"', workflow)
                self.assertIn('--p2-base-tree "$p2_base_tree"', workflow)

    def test_g2_workflow_wiring_is_hard_gated(self) -> None:
        root = Path(__file__).resolve().parents[1]
        for relative in (
            ".github/workflows/f9-7-contract.yml",
            ".github/workflows/security-audit.yml",
        ):
            workflow = (root / relative).read_text(encoding="utf-8")
            with self.subTest(workflow=relative):
                self.assertIn('F109_HEAD_REF" = "feat/f10-9-p3-p4-runtime-fail-closed"', workflow)
                self.assertIn('test "$F109_BASE_SHA" = "$protected_dev_tip"', workflow)
                self.assertIn('--g2-base "$g2_base"', workflow)
                self.assertIn('--g2-base-tree "$g2_base_tree"', workflow)

    def test_p5_workflow_wiring_is_hard_gated(self) -> None:
        root = Path(__file__).resolve().parents[1]
        for relative in (
            ".github/workflows/f9-7-contract.yml",
            ".github/workflows/security-audit.yml",
        ):
            workflow = (root / relative).read_text(encoding="utf-8")
            with self.subTest(workflow=relative):
                self.assertIn('F109_HEAD_REF" = "feat/f10-9-p5-metadata-readonly"', workflow)
                self.assertIn('test "$F109_BASE_SHA" = "$protected_dev_tip"', workflow)
                self.assertIn('--p5-base "$p5_base"', workflow)
                self.assertIn('--p5-base-tree "$p5_base_tree"', workflow)

    def test_non_p1_delta_preserves_legacy_denials(self) -> None:
        validate_non_p1_delta(Path("."), "0" * 40, {"README.md": "M"})
        with self.assertRaises(BoundaryError):
            validate_non_p1_delta(Path("."), "0" * 40, {"db/migrations/unexpected.sql": "A"})
        with self.assertRaises(BoundaryError):
            validate_non_p1_delta(Path("."), "0" * 40, {"scripts/security/f109_boundary.py": "M"})
        with self.assertRaises(BoundaryError):
            validate_non_p1_delta(
                Path("."),
                "0" * 40,
                {".context/artifacts/private/evidence.md": "A"},
            )

    def test_non_p1_delta_rejects_legacy_mode_drift(self) -> None:
        repo = self.make_repo()
        path = repo / "scripts" / "core" / "cleansing_worker.py"
        path.parent.mkdir(parents=True)
        path.write_text("value = 1\n", encoding="utf-8")
        base = self.commit(repo, "base")
        path.write_text("value = 2\n", encoding="utf-8")
        path.chmod(0o755)
        head = self.commit(repo, "mode drift")

        with self.assertRaises(BoundaryError):
            validate_non_p1_delta(repo, head, changed_statuses(repo, base, head))

    def test_wiring_allowlist_excludes_p1_runtime(self) -> None:
        self.assertEqual(
            WIRING_ALLOWED_STATUSES,
            {
                "AGENTS.md": "M",
                ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
                ".context/estado_del_proyecto.md": "M",
                ".context/operaciones/g0_r0_reconciliacion_f10_9.md": "M",
                ".context/operaciones/plan_remediacion_f10_9_fg2_fg3.md": "M",
                ".context/operaciones/r0_ci_boundary_manifest_2026_08_09.md": "M",
                ".context/operaciones/r0_post_merge_evidence_2026_08_09.md": "A",
                ".github/workflows/f9-7-contract.yml": "M",
                ".github/workflows/security-audit.yml": "M",
                "scripts/security/f109_boundary.py": "M",
                "tests/test_fase10_9_branch_reconciliation.py": "M",
                "tests/test_fase10_main_boundary.py": "M",
            },
        )
        self.assertNotIn("scripts/shared/db_client.py", WIRING_ALLOWED_STATUSES)
        self.assertNotIn("scripts/shared/safe_http.py", WIRING_ALLOWED_STATUSES)

    @mock.patch("scripts.security.f109_boundary.validate_p1")
    @mock.patch("scripts.security.f109_boundary.changed_statuses")
    @mock.patch("scripts.security.f109_boundary.parse_args")
    def test_cli_rejects_p1_paths_from_wrong_branch(
        self,
        parse_args_mock,
        changed_statuses_mock,
        validate_p1_mock,
    ) -> None:
        parse_args_mock.return_value = SimpleNamespace(
            repo=Path("."),
            event="pull_request",
            base_ref="desarrollo",
            head_ref="wrong-branch",
            base_sha="a" * 40,
            head_sha="b" * 40,
            base_repo="owner/repo",
            head_repo="owner/repo",
            cert_tip="",
            p1_base="",
            p1_base_tree="",
            p2_base="",
            p2_base_tree="",
            g2_base="",
            g2_base_tree="",
            github_output="",
        )
        changed_statuses_mock.return_value = P1_ALLOWED_STATUSES

        self.assertEqual(main(), 1)
        validate_p1_mock.assert_not_called()

    @mock.patch("scripts.security.f109_boundary.validate_p1")
    @mock.patch("scripts.security.f109_boundary.changed_statuses")
    @mock.patch("scripts.security.f109_boundary.parse_args")
    def test_cli_rejects_partial_or_expanded_p1_push(
        self,
        parse_args_mock,
        changed_statuses_mock,
        validate_p1_mock,
    ) -> None:
        parse_args_mock.return_value = SimpleNamespace(
            repo=Path("."),
            event="push",
            base_ref="desarrollo",
            head_ref="desarrollo",
            base_sha="a" * 40,
            head_sha="b" * 40,
            base_repo="owner/repo",
            head_repo="owner/repo",
            cert_tip="",
            p1_base="a" * 40,
            p1_base_tree="c" * 40,
            p2_base="a" * 40,
            p2_base_tree="c" * 40,
            g2_base="a" * 40,
            g2_base_tree="c" * 40,
            github_output="",
        )
        for delta in (
            {"scripts/shared/db_client.py": "M"},
            {**P1_ALLOWED_STATUSES, "extra.txt": "A"},
        ):
            with self.subTest(delta=delta):
                changed_statuses_mock.return_value = delta
                self.assertEqual(main(), 1)
        validate_p1_mock.assert_not_called()

    @mock.patch("scripts.security.f109_boundary.validate_p2")
    @mock.patch("scripts.security.f109_boundary.changed_statuses")
    @mock.patch("scripts.security.f109_boundary.parse_args")
    def test_cli_rejects_p2_paths_from_wrong_branch(
        self,
        parse_args_mock,
        changed_statuses_mock,
        validate_p2_mock,
    ) -> None:
        parse_args_mock.return_value = SimpleNamespace(
            repo=Path("."),
            event="pull_request",
            base_ref="desarrollo",
            head_ref="wrong-branch",
            base_sha="a" * 40,
            head_sha="b" * 40,
            base_repo="owner/repo",
            head_repo="owner/repo",
            cert_tip="",
            p1_base="",
            p1_base_tree="",
            p2_base="",
            p2_base_tree="",
            g2_base="",
            g2_base_tree="",
            github_output="",
        )
        changed_statuses_mock.return_value = P2_ALLOWED_STATUSES

        self.assertEqual(main(), 1)
        validate_p2_mock.assert_not_called()

    @mock.patch("scripts.security.f109_boundary.validate_p2")
    @mock.patch("scripts.security.f109_boundary.changed_statuses")
    @mock.patch("scripts.security.f109_boundary.parse_args")
    def test_cli_rejects_partial_or_expanded_p2_push(
        self,
        parse_args_mock,
        changed_statuses_mock,
        validate_p2_mock,
    ) -> None:
        parse_args_mock.return_value = SimpleNamespace(
            repo=Path("."),
            event="push",
            base_ref="desarrollo",
            head_ref="desarrollo",
            base_sha="a" * 40,
            head_sha="b" * 40,
            base_repo="owner/repo",
            head_repo="owner/repo",
            cert_tip="",
            p1_base="a" * 40,
            p1_base_tree="c" * 40,
            p2_base="a" * 40,
            p2_base_tree="c" * 40,
            g2_base="a" * 40,
            g2_base_tree="c" * 40,
            github_output="",
        )
        for delta in (
            {"scripts/shared/f10_9_readonly_planner.py": "A"},
            {**P2_ALLOWED_STATUSES, "extra.txt": "A"},
        ):
            with self.subTest(delta=delta):
                changed_statuses_mock.return_value = delta
                self.assertEqual(main(), 1)
        validate_p2_mock.assert_not_called()

    @mock.patch("scripts.security.f109_boundary.validate_p2")
    @mock.patch("scripts.security.f109_boundary.validate_p1")
    @mock.patch("scripts.security.f109_boundary.changed_statuses")
    @mock.patch("scripts.security.f109_boundary.parse_args")
    def test_cli_rejects_mixed_p1_p2_candidate(
        self,
        parse_args_mock,
        changed_statuses_mock,
        validate_p1_mock,
        validate_p2_mock,
    ) -> None:
        parse_args_mock.return_value = SimpleNamespace(
            repo=Path("."),
            event="push",
            base_ref="desarrollo",
            head_ref="desarrollo",
            base_sha="a" * 40,
            head_sha="b" * 40,
            base_repo="owner/repo",
            head_repo="owner/repo",
            cert_tip="",
            p1_base="a" * 40,
            p1_base_tree="c" * 40,
            p2_base="a" * 40,
            p2_base_tree="c" * 40,
            g2_base="a" * 40,
            g2_base_tree="c" * 40,
            github_output="",
        )
        changed_statuses_mock.return_value = {
            "scripts/shared/db_client.py": "M",
            "scripts/shared/f10_9_readonly_planner.py": "A",
        }

        self.assertEqual(main(), 1)
        validate_p1_mock.assert_not_called()
        validate_p2_mock.assert_not_called()

    @mock.patch("scripts.security.f109_boundary.validate_g2")
    @mock.patch("scripts.security.f109_boundary.changed_statuses")
    @mock.patch("scripts.security.f109_boundary.parse_args")
    def test_cli_rejects_g2_paths_from_wrong_branch(
        self,
        parse_args_mock,
        changed_statuses_mock,
        validate_g2_mock,
    ) -> None:
        parse_args_mock.return_value = SimpleNamespace(
            repo=Path("."),
            event="pull_request",
            base_ref="desarrollo",
            head_ref="wrong-branch",
            base_sha="a" * 40,
            head_sha="b" * 40,
            base_repo="owner/repo",
            head_repo="owner/repo",
            cert_tip="",
            p1_base="",
            p1_base_tree="",
            p2_base="",
            p2_base_tree="",
            g2_base="",
            g2_base_tree="",
            github_output="",
        )
        changed_statuses_mock.return_value = G2_ALLOWED_STATUSES

        self.assertEqual(main(), 1)
        validate_g2_mock.assert_not_called()

    @mock.patch("scripts.security.f109_boundary.validate_g2")
    @mock.patch("scripts.security.f109_boundary.changed_statuses")
    @mock.patch("scripts.security.f109_boundary.parse_args")
    def test_cli_rejects_partial_or_expanded_g2_push(
        self,
        parse_args_mock,
        changed_statuses_mock,
        validate_g2_mock,
    ) -> None:
        parse_args_mock.return_value = SimpleNamespace(
            repo=Path("."),
            event="push",
            base_ref="desarrollo",
            head_ref="desarrollo",
            base_sha="a" * 40,
            head_sha="b" * 40,
            base_repo="owner/repo",
            head_repo="owner/repo",
            cert_tip="",
            p1_base="a" * 40,
            p1_base_tree="c" * 40,
            p2_base="a" * 40,
            p2_base_tree="c" * 40,
            g2_base="a" * 40,
            g2_base_tree="c" * 40,
            github_output="",
        )
        for delta in (
            {"scripts/core/master_orchestrator.py": "M"},
            {**G2_ALLOWED_STATUSES, "extra.txt": "A"},
        ):
            with self.subTest(delta=delta):
                changed_statuses_mock.return_value = delta
                self.assertEqual(main(), 1)
        validate_g2_mock.assert_not_called()

    @mock.patch("scripts.security.f109_boundary.validate_g2")
    @mock.patch("scripts.security.f109_boundary.validate_p1")
    @mock.patch("scripts.security.f109_boundary.changed_statuses")
    @mock.patch("scripts.security.f109_boundary.parse_args")
    def test_cli_rejects_mixed_p1_g2_candidate(
        self,
        parse_args_mock,
        changed_statuses_mock,
        validate_p1_mock,
        validate_g2_mock,
    ) -> None:
        parse_args_mock.return_value = SimpleNamespace(
            repo=Path("."),
            event="push",
            base_ref="desarrollo",
            head_ref="desarrollo",
            base_sha="a" * 40,
            head_sha="b" * 40,
            base_repo="owner/repo",
            head_repo="owner/repo",
            cert_tip="",
            p1_base="a" * 40,
            p1_base_tree="c" * 40,
            p2_base="a" * 40,
            p2_base_tree="c" * 40,
            g2_base="a" * 40,
            g2_base_tree="c" * 40,
            github_output="",
        )
        changed_statuses_mock.return_value = {
            "scripts/shared/db_client.py": "M",
            "scripts/core/master_orchestrator.py": "M",
        }

        self.assertEqual(main(), 1)
        validate_p1_mock.assert_not_called()
        validate_g2_mock.assert_not_called()

    @mock.patch("scripts.security.f109_boundary.changed_statuses", return_value={"README.md": "M"})
    @mock.patch("scripts.security.f109_boundary.parse_args")
    def test_cli_emits_skip_non_p1_mode(self, parse_args_mock, changed_statuses_mock) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "github-output"
            parse_args_mock.return_value = SimpleNamespace(
                repo=Path("."),
                event="pull_request",
                base_ref="desarrollo",
                head_ref="docs/change",
                base_sha="a" * 40,
                head_sha="b" * 40,
                base_repo="owner/repo",
                head_repo="owner/repo",
                cert_tip="",
                p1_base="",
                p1_base_tree="",
                p2_base="",
                p2_base_tree="",
                g2_base="",
                g2_base_tree="",
                github_output=str(output),
            )

            self.assertEqual(main(), 0)
            self.assertEqual(output.read_text(encoding="utf-8"), "mode=skip_non_p1\n")

    @mock.patch("scripts.security.f109_boundary.changed_statuses")
    @mock.patch("scripts.security.f109_boundary.parse_args")
    def test_cli_rejects_reserved_branch_with_wrong_baseline(
        self,
        parse_args_mock,
        changed_statuses_mock,
    ) -> None:
        parse_args_mock.return_value = SimpleNamespace(
            repo=Path("."),
            event="pull_request",
            base_ref="desarrollo",
            head_ref=P1_HEAD_REF,
            base_sha="a" * 40,
            head_sha="b" * 40,
            base_repo="owner/repo",
            head_repo="owner/repo",
            cert_tip="",
            p1_base="",
            p1_base_tree="",
            p2_base="",
            p2_base_tree="",
            g2_base="",
            g2_base_tree="",
            github_output="",
        )

        self.assertEqual(main(), 1)
        changed_statuses_mock.assert_not_called()

    @mock.patch("scripts.security.f109_boundary.changed_statuses")
    @mock.patch("scripts.security.f109_boundary.parse_args")
    def test_cli_rejects_p2_wiring_branch_with_wrong_baseline(
        self,
        parse_args_mock,
        changed_statuses_mock,
    ) -> None:
        parse_args_mock.return_value = SimpleNamespace(
            repo=Path("."),
            event="pull_request",
            base_ref="desarrollo",
            head_ref=P2_WIRING_HEAD_REF,
            base_sha="a" * 40,
            head_sha="b" * 40,
            base_repo="owner/repo",
            head_repo="owner/repo",
            cert_tip="",
            p1_base="",
            p1_base_tree="",
            p2_base="",
            p2_base_tree="",
            g2_base="",
            g2_base_tree="",
            github_output="",
        )

        self.assertEqual(main(), 1)
        changed_statuses_mock.assert_not_called()

    @mock.patch("scripts.security.f109_boundary.changed_statuses")
    @mock.patch("scripts.security.f109_boundary.parse_args")
    def test_cli_rejects_g2_wiring_branch_with_wrong_baseline(
        self,
        parse_args_mock,
        changed_statuses_mock,
    ) -> None:
        parse_args_mock.return_value = SimpleNamespace(
            repo=Path("."),
            event="pull_request",
            base_ref="desarrollo",
            head_ref=G2_WIRING_HEAD_REF,
            base_sha="a" * 40,
            head_sha="b" * 40,
            base_repo="owner/repo",
            head_repo="owner/repo",
            cert_tip="",
            p1_base="",
            p1_base_tree="",
            p2_base="",
            p2_base_tree="",
            g2_base="",
            g2_base_tree="",
            github_output="",
        )

        self.assertEqual(main(), 1)
        changed_statuses_mock.assert_not_called()

    @mock.patch("scripts.security.f109_boundary.changed_statuses")
    @mock.patch("scripts.security.f109_boundary.parse_args")
    def test_cli_rejects_g2_branch_with_wrong_baseline(
        self,
        parse_args_mock,
        changed_statuses_mock,
    ) -> None:
        parse_args_mock.return_value = SimpleNamespace(
            repo=Path("."),
            event="pull_request",
            base_ref="desarrollo",
            head_ref=G2_HEAD_REF,
            base_sha="a" * 40,
            head_sha="b" * 40,
            base_repo="owner/repo",
            head_repo="owner/repo",
            cert_tip="",
            p1_base="",
            p1_base_tree="",
            p2_base="",
            p2_base_tree="",
            g2_base="",
            g2_base_tree="",
            github_output="",
        )

        self.assertEqual(main(), 1)
        changed_statuses_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
