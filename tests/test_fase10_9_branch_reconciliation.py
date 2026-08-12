from __future__ import annotations

import hashlib
import json
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
    F1010_M1_ALLOWED_MODES,
    F1010_M1_ALLOWED_STATUSES,
    F1010_M1_HEAD_REF,
    F1010_M2A_ALLOWED_MODES,
    F1010_M2A_ALLOWED_STATUSES,
    F1010_M2A_BASE,
    F1010_M2A_BASE_TREE,
    F1010_M2A_HEAD_REF,
    F1010_M3_ALLOWED_MODES,
    F1010_M3_ALLOWED_STATUSES,
    F1010_M3_BASE,
    F1010_M3_BASE_TREE,
    F1010_M3_HEAD_REF,
    F1010_M3_READER_ALLOWED_MODES,
    F1010_M3_READER_ALLOWED_STATUSES,
    F1010_M3_READER_BASE,
    F1010_M3_READER_BASE_TREE,
    F1010_M3_READER_HEAD_REF,
    F1010_M3_READER_POST_MERGE_ALLOWED_MODES,
    F1010_M3_READER_POST_MERGE_ALLOWED_STATUSES,
    F1010_M3_READER_POST_MERGE_BASE,
    F1010_M3_READER_POST_MERGE_BASE_TREE,
    F1010_M3_READER_POST_MERGE_DOCS_COMMIT,
    F1010_M3_READER_POST_MERGE_HEAD_REF,
    F1010_M3_ROTATION_ALLOWED_MODES,
    F1010_M3_ROTATION_ALLOWED_STATUSES,
    F1010_M3_ROTATION_BASE,
    F1010_M3_ROTATION_BASE_TREE,
    F1010_M3_ROTATION_HEAD_REF,
    F1010_M3_PASSWORDLESS_ALLOWED_MODES,
    F1010_M3_PASSWORDLESS_ALLOWED_STATUSES,
    F1010_M3_PASSWORDLESS_BASE,
    F1010_M3_PASSWORDLESS_BASE_TREE,
    F1010_M3_PASSWORDLESS_HEAD_REF,
    F1010_M3_PREFLIGHT_PAYLOAD_ALLOWED_MODES,
    F1010_M3_PREFLIGHT_PAYLOAD_ALLOWED_STATUSES,
    F1010_M3_PREFLIGHT_PAYLOAD_BASE,
    F1010_M3_PREFLIGHT_PAYLOAD_BASE_TREE,
    F1010_M3_PREFLIGHT_PAYLOAD_HEAD_REF,
    F1010_M3_PREFLIGHT_EVIDENCE_ALLOWED_MODES,
    F1010_M3_PREFLIGHT_EVIDENCE_ALLOWED_STATUSES,
    F1010_M3_PREFLIGHT_EVIDENCE_BASE,
    F1010_M3_PREFLIGHT_EVIDENCE_BASE_TREE,
    F1010_M3_PREFLIGHT_EVIDENCE_HEAD_REF,
    F1010_M3_FINAL_READINESS_ALLOWED_MODES,
    F1010_M3_FINAL_READINESS_ALLOWED_STATUSES,
    F1010_M3_FINAL_READINESS_BASE,
    F1010_M3_FINAL_READINESS_BASE_TREE,
    F1010_M3_FINAL_READINESS_HEAD_REF,
    F1010_M3_APPLY_PROJECTION_ALLOWED_MODES,
    F1010_M3_APPLY_PROJECTION_ALLOWED_STATUSES,
    F1010_M3_APPLY_PROJECTION_BASE,
    F1010_M3_APPLY_PROJECTION_BASE_TREE,
    F1010_M3_APPLY_PROJECTION_HEAD_REF,
    F1010_M3_DDL_PAYLOAD_ALLOWED_MODES,
    F1010_M3_DDL_PAYLOAD_ALLOWED_STATUSES,
    F1010_M3_DDL_PAYLOAD_BASE,
    F1010_M3_DDL_PAYLOAD_BASE_TREE,
    F1010_M3_DDL_PAYLOAD_HEAD_REF,
    F1010_M3_DDL_PAYLOAD_REFRESH_ALLOWED_MODES,
    F1010_M3_DDL_PAYLOAD_REFRESH_ALLOWED_STATUSES,
    F1010_M3_DDL_PAYLOAD_REFRESH_BASE,
    F1010_M3_DDL_PAYLOAD_REFRESH_BASE_TREE,
    F1010_M3_DDL_PAYLOAD_REFRESH_HEAD_REF,
    F1010_M3_NULLABILITY_REMEDIATION_ALLOWED_MODES,
    F1010_M3_NULLABILITY_REMEDIATION_ALLOWED_STATUSES,
    F1010_M3_NULLABILITY_REMEDIATION_BASE,
    F1010_M3_NULLABILITY_REMEDIATION_BASE_TREE,
    F1010_M3_NULLABILITY_REMEDIATION_HEAD_REF,
    F1010_M3_DDL_V2_PAYLOAD_ALLOWED_MODES,
    F1010_M3_DDL_V2_PAYLOAD_ALLOWED_STATUSES,
    F1010_M3_DDL_V2_PAYLOAD_BASE,
    F1010_M3_DDL_V2_PAYLOAD_BASE_TREE,
    F1010_M3_DDL_V2_PAYLOAD_HEAD_REF,
    F1010_M3_PUBLIC_ACL_REBASELINE_ALLOWED_MODES,
    F1010_M3_PUBLIC_ACL_REBASELINE_ALLOWED_STATUSES,
    F1010_M3_PUBLIC_ACL_REBASELINE_BASE,
    F1010_M3_PUBLIC_ACL_REBASELINE_BASE_TREE,
    F1010_M3_PUBLIC_ACL_REBASELINE_HEAD_REF,
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
    validate_f1010_m1,
    validate_f1010_m2a_wiring,
    validate_f1010_m3,
    validate_f1010_m3_reader,
    validate_f1010_m3_reader_post_merge,
    validate_f1010_m3_rotation,
    validate_f1010_m3_passwordless,
    validate_f1010_m3_preflight_payload,
    validate_f1010_m3_preflight_evidence,
    validate_f1010_m3_final_readiness,
    validate_f1010_m3_apply_projection,
    validate_f1010_m3_ddl_payload,
    validate_f1010_m3_ddl_payload_refresh,
    validate_f1010_m3_nullability_remediation,
    validate_f1010_m3_ddl_v2_payload,
    validate_f1010_m3_public_acl_rebaseline,
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

    def cli_args(self, **overrides: object) -> SimpleNamespace:
        values: dict[str, object] = {
            "repo": Path("."),
            "event": "pull_request",
            "base_ref": "desarrollo",
            "head_ref": "branch",
            "base_sha": "a" * 40,
            "head_sha": "b" * 40,
            "base_repo": "owner/repo",
            "head_repo": "owner/repo",
            "cert_tip": "",
            "p1_base": "",
            "p1_base_tree": "",
            "p2_base": "",
            "p2_base_tree": "",
            "g2_base": "",
            "g2_base_tree": "",
            "p5_base": "",
            "p5_base_tree": "",
            "f1010_m1_base": "",
            "f1010_m1_base_tree": "",
            "github_output": "",
        }
        values.update(overrides)
        return SimpleNamespace(**values)

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
        self.assertEqual(
            detect_mode(
                "pull_request",
                "desarrollo",
                F1010_M2A_HEAD_REF,
                F1010_M2A_BASE,
            ),
            "f1010_m2a",
        )
        self.assertEqual(
            detect_mode(
                "pull_request",
                "desarrollo",
                F1010_M1_HEAD_REF,
                "6" * 40,
                f1010_m1_base="6" * 40,
            ),
            "f1010_m1",
        )
        self.assertEqual(
            detect_mode(
                "push",
                "desarrollo",
                "desarrollo",
                F1010_M2A_BASE,
            ),
            "f1010_m2a",
        )
        self.assertEqual(
            detect_mode(
                "pull_request",
                "desarrollo",
                F1010_M3_HEAD_REF,
                F1010_M3_BASE,
            ),
            "f1010_m3",
        )
        self.assertEqual(
            detect_mode(
                "pull_request",
                "desarrollo",
                F1010_M3_READER_HEAD_REF,
                F1010_M3_READER_BASE,
            ),
            "f1010_m3_reader",
        )
        self.assertEqual(
            detect_mode(
                "pull_request",
                "desarrollo",
                F1010_M3_READER_POST_MERGE_HEAD_REF,
                F1010_M3_READER_POST_MERGE_BASE,
            ),
            "f1010_m3_reader_post_merge",
        )
        self.assertEqual(
            detect_mode(
                "pull_request",
                "desarrollo",
                F1010_M3_ROTATION_HEAD_REF,
                F1010_M3_ROTATION_BASE,
            ),
            "f1010_m3_rotation",
        )
        self.assertEqual(
            detect_mode(
                "pull_request",
                "desarrollo",
                F1010_M3_PASSWORDLESS_HEAD_REF,
                F1010_M3_PASSWORDLESS_BASE,
            ),
            "f1010_m3_passwordless",
        )
        self.assertEqual(
            detect_mode(
                "pull_request",
                "desarrollo",
                F1010_M3_PREFLIGHT_PAYLOAD_HEAD_REF,
                F1010_M3_PREFLIGHT_PAYLOAD_BASE,
            ),
            "f1010_m3_preflight_payload",
        )
        self.assertEqual(
            detect_mode(
                "pull_request",
                "desarrollo",
                F1010_M3_PREFLIGHT_EVIDENCE_HEAD_REF,
                F1010_M3_PREFLIGHT_EVIDENCE_BASE,
            ),
            "f1010_m3_preflight_evidence",
        )
        self.assertEqual(
            detect_mode(
                "pull_request", "desarrollo", F1010_M3_FINAL_READINESS_HEAD_REF,
                F1010_M3_FINAL_READINESS_BASE,
            ),
            "f1010_m3_final_readiness",
        )
        self.assertEqual(
            detect_mode(
                "pull_request",
                "desarrollo",
                F1010_M3_APPLY_PROJECTION_HEAD_REF,
                F1010_M3_APPLY_PROJECTION_BASE,
            ),
            "f1010_m3_apply_projection",
        )
        self.assertEqual(
            detect_mode(
                "push",
                "desarrollo",
                "desarrollo",
                F1010_M3_APPLY_PROJECTION_BASE,
            ),
            "f1010_m3_apply_projection",
        )
        self.assertEqual(
            detect_mode(
                "pull_request",
                "desarrollo",
                "feat/not-the-projection-branch",
                F1010_M3_APPLY_PROJECTION_BASE,
            ),
            "skip",
        )
        self.assertEqual(
            detect_mode(
                "pull_request",
                "desarrollo",
                F1010_M3_DDL_PAYLOAD_HEAD_REF,
                F1010_M3_DDL_PAYLOAD_BASE,
            ),
            "f1010_m3_ddl_payload",
        )
        self.assertEqual(
            detect_mode(
                "push",
                "desarrollo",
                "desarrollo",
                F1010_M3_DDL_PAYLOAD_BASE,
            ),
            "f1010_m3_ddl_payload",
        )
        self.assertEqual(
            detect_mode(
                "pull_request",
                "desarrollo",
                "docs/not-the-ddl-payload",
                F1010_M3_DDL_PAYLOAD_BASE,
            ),
            "skip",
        )
        self.assertEqual(
            detect_mode(
                "pull_request",
                "desarrollo",
                F1010_M3_DDL_PAYLOAD_REFRESH_HEAD_REF,
                F1010_M3_DDL_PAYLOAD_REFRESH_BASE,
            ),
            "f1010_m3_ddl_payload_refresh",
        )
        self.assertEqual(
            detect_mode(
                "pull_request",
                "desarrollo",
                F1010_M3_NULLABILITY_REMEDIATION_HEAD_REF,
                F1010_M3_NULLABILITY_REMEDIATION_BASE,
            ),
            "f1010_m3_nullability_remediation",
        )
        self.assertEqual(
            detect_mode(
                "push",
                "desarrollo",
                "desarrollo",
                F1010_M3_DDL_PAYLOAD_REFRESH_BASE,
            ),
            "f1010_m3_ddl_payload_refresh",
        )
        self.assertEqual(
            detect_mode(
                "pull_request",
                "desarrollo",
                F1010_M3_APPLY_PROJECTION_HEAD_REF,
                "7" * 40,
            ),
            "skip",
        )
        self.assertEqual(
            detect_mode(
                "pull_request",
                "desarrollo",
                F1010_M2A_HEAD_REF,
                "7" * 40,
            ),
            "skip",
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

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents", return_value=[F1010_M2A_BASE])
    @mock.patch("scripts.security.f109_boundary.commit_tree", return_value=F1010_M2A_BASE_TREE)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_f1010_m2a_wiring_pr_is_one_exact_commit(
        self,
        require_sha_mock,
        tree_mock,
        parents_mock,
        delta_mock,
        graph_mock,
    ) -> None:
        head = "b" * 40

        validate_f1010_m2a_wiring(Path("."), F1010_M2A_BASE, head, "pull_request")

        delta_mock.assert_called_once_with(
            Path("."),
            F1010_M2A_BASE,
            head,
            F1010_M2A_ALLOWED_STATUSES,
            F1010_M2A_ALLOWED_MODES,
        )
        self.assertEqual(graph_mock.call_args.kwargs["expected_files"], 48)
        self.assertEqual(graph_mock.call_args.kwargs["expected_links"], 345)

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_f1010_m2a_wiring_push_requires_protected_merge(
        self,
        require_sha_mock,
        tree_mock,
        parents_mock,
        delta_mock,
        graph_mock,
    ) -> None:
        pr_head = "b" * 40
        merge_head = "c" * 40

        def tree(repo, commit):
            if commit == F1010_M2A_BASE:
                return F1010_M2A_BASE_TREE
            return "d" * 40

        def parents(repo, commit):
            if commit == merge_head:
                return [F1010_M2A_BASE, pr_head]
            if commit == pr_head:
                return [F1010_M2A_BASE]
            return []

        tree_mock.side_effect = tree
        parents_mock.side_effect = parents

        validate_f1010_m2a_wiring(Path("."), F1010_M2A_BASE, merge_head, "push")

        delta_mock.assert_called_once_with(
            Path("."),
            F1010_M2A_BASE,
            pr_head,
            F1010_M2A_ALLOWED_STATUSES,
            F1010_M2A_ALLOWED_MODES,
        )

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents", return_value=["0" * 40])
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_f1010_m2a_rejects_tree_drift_and_non_direct_pr(
        self,
        require_sha_mock,
        tree_mock,
        parents_mock,
        delta_mock,
        graph_mock,
    ) -> None:
        tree_mock.return_value = "d" * 40
        with self.assertRaises(BoundaryError):
            validate_f1010_m2a_wiring(Path("."), F1010_M2A_BASE, "b" * 40, "pull_request")

        tree_mock.return_value = F1010_M2A_BASE_TREE
        with self.assertRaises(BoundaryError):
            validate_f1010_m2a_wiring(Path("."), F1010_M2A_BASE, "b" * 40, "pull_request")
        delta_mock.assert_not_called()

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_f1010_m2a_rejects_push_first_parent_and_tree_drift(
        self,
        require_sha_mock,
        tree_mock,
        parents_mock,
        delta_mock,
        graph_mock,
    ) -> None:
        pr_head = "b" * 40
        merge_head = "c" * 40
        tree_mock.side_effect = lambda repo, commit: (
            F1010_M2A_BASE_TREE if commit == F1010_M2A_BASE else "d" * 40
        )
        parents_mock.return_value = ["0" * 40, pr_head]
        with self.assertRaises(BoundaryError):
            validate_f1010_m2a_wiring(Path("."), F1010_M2A_BASE, merge_head, "push")

        parents_mock.return_value = [F1010_M2A_BASE, pr_head]
        tree_mock.side_effect = lambda repo, commit: {
            F1010_M2A_BASE: F1010_M2A_BASE_TREE,
            merge_head: "d" * 40,
            pr_head: "e" * 40,
        }[commit]
        with self.assertRaises(BoundaryError):
            validate_f1010_m2a_wiring(Path("."), F1010_M2A_BASE, merge_head, "push")
        delta_mock.assert_not_called()

    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents", return_value=["a" * 40])
    @mock.patch("scripts.security.f109_boundary.commit_tree", return_value="d" * 40)
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_f1010_m1_pr_requires_frozen_direct_base(
        self,
        require_sha_mock,
        ancestor_mock,
        tree_mock,
        parents_mock,
        delta_mock,
    ) -> None:
        base = "a" * 40
        head = "b" * 40
        tree = "d" * 40

        validate_f1010_m1(Path("."), base, head, base, tree, "pull_request")
        delta_mock.assert_called_once_with(
            Path("."),
            base,
            head,
            F1010_M1_ALLOWED_STATUSES,
            F1010_M1_ALLOWED_MODES,
        )

        with self.assertRaises(BoundaryError):
            validate_f1010_m1(Path("."), base, head, "c" * 40, tree, "pull_request")

    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree", return_value="d" * 40)
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_f1010_m1_push_requires_protected_merge(
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

        def parents(repo, commit):
            if commit == merge_head:
                return [base, pr_head]
            if commit == pr_head:
                return [base]
            return []

        parents_mock.side_effect = parents

        validate_f1010_m1(Path("."), base, merge_head, base, "d" * 40, "push")
        delta_mock.assert_called_once_with(
            Path("."),
            base,
            pr_head,
            F1010_M1_ALLOWED_STATUSES,
            F1010_M1_ALLOWED_MODES,
        )

    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents", return_value=["0" * 40])
    @mock.patch("scripts.security.f109_boundary.commit_tree", return_value="d" * 40)
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_f1010_m1_rejects_tree_drift_and_non_direct_pr(
        self,
        require_sha_mock,
        ancestor_mock,
        tree_mock,
        parents_mock,
        delta_mock,
    ) -> None:
        base = "a" * 40
        head = "b" * 40
        with self.assertRaises(BoundaryError):
            validate_f1010_m1(Path("."), base, head, base, "e" * 40, "pull_request")

        with self.assertRaises(BoundaryError):
            validate_f1010_m1(Path("."), base, head, base, "d" * 40, "pull_request")
        delta_mock.assert_not_called()

    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_f1010_m3_pr_requires_frozen_direct_base(
        self,
        require_sha_mock,
        ancestor_mock,
        tree_mock,
        parents_mock,
        delta_mock,
    ) -> None:
        head = "b" * 40
        tree_mock.return_value = F1010_M3_BASE_TREE
        parents_mock.return_value = [F1010_M3_BASE]

        validate_f1010_m3(Path("."), F1010_M3_BASE, head, "pull_request")

        delta_mock.assert_called_once_with(
            Path("."),
            F1010_M3_BASE,
            head,
            F1010_M3_ALLOWED_STATUSES,
            F1010_M3_ALLOWED_MODES,
        )

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_f1010_m3_reader_pr_requires_frozen_direct_base(
        self,
        require_sha_mock,
        ancestor_mock,
        tree_mock,
        parents_mock,
        delta_mock,
        context_mock,
    ) -> None:
        head = "c" * 40
        tree_mock.return_value = F1010_M3_READER_BASE_TREE
        parents_mock.return_value = [F1010_M3_READER_BASE]

        validate_f1010_m3_reader(
            Path("."), F1010_M3_READER_BASE, head, "pull_request"
        )

        delta_mock.assert_called_once_with(
            Path("."),
            F1010_M3_READER_BASE,
            head,
            F1010_M3_READER_ALLOWED_STATUSES,
            F1010_M3_READER_ALLOWED_MODES,
        )
        context_mock.assert_called_once_with(Path("."), 52, 363)

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    @mock.patch("scripts.security.f109_boundary.git")
    def test_f1010_m3_reader_post_merge_requires_exact_docs_delta(
        self,
        git_mock,
        require_sha_mock,
        ancestor_mock,
        tree_mock,
        parents_mock,
        delta_mock,
        context_mock,
    ) -> None:
        head = "d" * 40
        tree_mock.return_value = F1010_M3_READER_POST_MERGE_BASE_TREE
        parents_mock.side_effect = (
            lambda repo, commit: [F1010_M3_READER_POST_MERGE_BASE]
            if commit == F1010_M3_READER_POST_MERGE_DOCS_COMMIT
            else [F1010_M3_READER_POST_MERGE_DOCS_COMMIT]
        )
        git_mock.side_effect = [
            f"{F1010_M3_READER_POST_MERGE_DOCS_COMMIT}\n{head}",
            f"{head}\n{F1010_M3_READER_POST_MERGE_DOCS_COMMIT}",
        ]

        validate_f1010_m3_reader_post_merge(
            Path("."), F1010_M3_READER_POST_MERGE_BASE, head, "pull_request"
        )

        delta_mock.assert_called_once_with(
            Path("."),
            F1010_M3_READER_POST_MERGE_BASE,
            head,
            F1010_M3_READER_POST_MERGE_ALLOWED_STATUSES,
            F1010_M3_READER_POST_MERGE_ALLOWED_MODES,
        )
        context_mock.assert_called_once_with(Path("."), 53, 362)

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    @mock.patch("scripts.security.f109_boundary.git")
    def test_f1010_m3_reader_post_merge_accepts_protected_push(
        self,
        git_mock,
        require_sha_mock,
        ancestor_mock,
        tree_mock,
        parents_mock,
        delta_mock,
        context_mock,
    ) -> None:
        merge = "e" * 40
        candidate = "d" * 40

        def parents(repo, commit):
            if commit == merge:
                return [F1010_M3_READER_POST_MERGE_BASE, candidate]
            if commit == F1010_M3_READER_POST_MERGE_DOCS_COMMIT:
                return [F1010_M3_READER_POST_MERGE_BASE]
            return [F1010_M3_READER_POST_MERGE_DOCS_COMMIT]

        def tree(repo, commit):
            if commit == F1010_M3_READER_POST_MERGE_BASE:
                return F1010_M3_READER_POST_MERGE_BASE_TREE
            return "f" * 40

        parents_mock.side_effect = parents
        tree_mock.side_effect = tree
        git_mock.side_effect = [
            f"{F1010_M3_READER_POST_MERGE_DOCS_COMMIT}\n{candidate}",
            f"{candidate}\n{F1010_M3_READER_POST_MERGE_DOCS_COMMIT}",
        ]

        validate_f1010_m3_reader_post_merge(
            Path("."), F1010_M3_READER_POST_MERGE_BASE, merge, "push"
        )

        delta_mock.assert_called_once_with(
            Path("."),
            F1010_M3_READER_POST_MERGE_BASE,
            candidate,
            F1010_M3_READER_POST_MERGE_ALLOWED_STATUSES,
            F1010_M3_READER_POST_MERGE_ALLOWED_MODES,
        )
        context_mock.assert_called_once_with(Path("."), 53, 362)

    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.is_ancestor")
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_f1010_m3_reader_post_merge_rejects_push_candidate_without_ancestry(
        self,
        require_sha_mock,
        ancestor_mock,
        tree_mock,
        parents_mock,
    ) -> None:
        merge = "e" * 40
        candidate = "d" * 40
        tree_mock.return_value = F1010_M3_READER_POST_MERGE_BASE_TREE
        parents_mock.return_value = [F1010_M3_READER_POST_MERGE_BASE, candidate]
        ancestor_mock.side_effect = [True, False]

        with self.assertRaises(BoundaryError):
            validate_f1010_m3_reader_post_merge(
                Path("."), F1010_M3_READER_POST_MERGE_BASE, merge, "push"
            )

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_f1010_m3_rotation_requires_one_direct_commit(
        self,
        require_sha_mock,
        ancestor_mock,
        tree_mock,
        parents_mock,
        delta_mock,
        context_mock,
    ) -> None:
        head = "f" * 40
        tree_mock.return_value = F1010_M3_ROTATION_BASE_TREE
        parents_mock.return_value = [F1010_M3_ROTATION_BASE]

        validate_f1010_m3_rotation(
            Path("."), F1010_M3_ROTATION_BASE, head, "pull_request"
        )

        delta_mock.assert_called_once_with(
            Path("."),
            F1010_M3_ROTATION_BASE,
            head,
            F1010_M3_ROTATION_ALLOWED_STATUSES,
            F1010_M3_ROTATION_ALLOWED_MODES,
        )
        context_mock.assert_called_once_with(Path("."), 54, 369)

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_f1010_m3_rotation_accepts_protected_push(
        self,
        require_sha_mock,
        ancestor_mock,
        tree_mock,
        parents_mock,
        delta_mock,
        context_mock,
    ) -> None:
        merge = "e" * 40
        candidate = "f" * 40

        def parents(repo, commit):
            if commit == merge:
                return [F1010_M3_ROTATION_BASE, candidate]
            return [F1010_M3_ROTATION_BASE]

        def tree(repo, commit):
            if commit == F1010_M3_ROTATION_BASE:
                return F1010_M3_ROTATION_BASE_TREE
            return "1" * 40

        parents_mock.side_effect = parents
        tree_mock.side_effect = tree

        validate_f1010_m3_rotation(
            Path("."), F1010_M3_ROTATION_BASE, merge, "push"
        )

        delta_mock.assert_called_once_with(
            Path("."),
            F1010_M3_ROTATION_BASE,
            candidate,
            F1010_M3_ROTATION_ALLOWED_STATUSES,
            F1010_M3_ROTATION_ALLOWED_MODES,
        )
        context_mock.assert_called_once_with(Path("."), 54, 369)

    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_f1010_m3_rotation_rejects_invalid_push_topology(
        self,
        require_sha_mock,
        ancestor_mock,
        tree_mock,
        parents_mock,
    ) -> None:
        merge = "e" * 40
        candidate = "f" * 40
        tree_mock.return_value = F1010_M3_ROTATION_BASE_TREE
        invalid_parents = (
            [F1010_M3_ROTATION_BASE],
            ["0" * 40, candidate],
            [F1010_M3_ROTATION_BASE, candidate, "1" * 40],
        )
        for parents in invalid_parents:
            with self.subTest(parents=parents):
                parents_mock.return_value = parents
                with self.assertRaises(BoundaryError):
                    validate_f1010_m3_rotation(
                        Path("."), F1010_M3_ROTATION_BASE, merge, "push"
                    )

    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_f1010_m3_rotation_rejects_push_tree_mismatch(
        self,
        require_sha_mock,
        ancestor_mock,
        tree_mock,
        parents_mock,
    ) -> None:
        merge = "e" * 40
        candidate = "f" * 40
        parents_mock.side_effect = [
            [F1010_M3_ROTATION_BASE, candidate],
            [F1010_M3_ROTATION_BASE],
        ]
        tree_mock.side_effect = [
            F1010_M3_ROTATION_BASE_TREE,
            "1" * 40,
            "2" * 40,
        ]

        with self.assertRaises(BoundaryError):
            validate_f1010_m3_rotation(
                Path("."), F1010_M3_ROTATION_BASE, merge, "push"
            )

    @mock.patch("scripts.security.f109_boundary.validate_f1010_m3_rotation")
    @mock.patch("scripts.security.f109_boundary.changed_statuses")
    @mock.patch("scripts.security.f109_boundary.parse_args")
    def test_cli_rejects_rotation_attestation_from_wrong_branch(
        self,
        parse_args_mock,
        changed_statuses_mock,
        validate_rotation_mock,
    ) -> None:
        parse_args_mock.return_value = self.cli_args(head_ref="wrong-branch")
        changed_statuses_mock.return_value = {
            ".context/operaciones/m3_reader_f10_10_rotation_attestation_2026_08_11.md": "A"
        }

        self.assertEqual(main(), 1)
        validate_rotation_mock.assert_not_called()

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_f1010_m3_passwordless_requires_one_direct_commit(
        self,
        require_sha_mock,
        ancestor_mock,
        tree_mock,
        parents_mock,
        delta_mock,
        context_mock,
    ) -> None:
        head = "1" * 40
        tree_mock.return_value = F1010_M3_PASSWORDLESS_BASE_TREE
        parents_mock.return_value = [F1010_M3_PASSWORDLESS_BASE]

        validate_f1010_m3_passwordless(
            Path("."), F1010_M3_PASSWORDLESS_BASE, head, "pull_request"
        )

        delta_mock.assert_called_once_with(
            Path("."),
            F1010_M3_PASSWORDLESS_BASE,
            head,
            F1010_M3_PASSWORDLESS_ALLOWED_STATUSES,
            F1010_M3_PASSWORDLESS_ALLOWED_MODES,
        )
        context_mock.assert_called_once_with(Path("."), 54, 369)

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_f1010_m3_passwordless_accepts_protected_push(
        self,
        require_sha_mock,
        ancestor_mock,
        tree_mock,
        parents_mock,
        delta_mock,
        context_mock,
    ) -> None:
        merge = "2" * 40
        candidate = "1" * 40

        def parents(repo, commit):
            if commit == merge:
                return [F1010_M3_PASSWORDLESS_BASE, candidate]
            return [F1010_M3_PASSWORDLESS_BASE]

        def tree(repo, commit):
            if commit == F1010_M3_PASSWORDLESS_BASE:
                return F1010_M3_PASSWORDLESS_BASE_TREE
            return "3" * 40

        parents_mock.side_effect = parents
        tree_mock.side_effect = tree

        validate_f1010_m3_passwordless(
            Path("."), F1010_M3_PASSWORDLESS_BASE, merge, "push"
        )

        delta_mock.assert_called_once_with(
            Path("."),
            F1010_M3_PASSWORDLESS_BASE,
            candidate,
            F1010_M3_PASSWORDLESS_ALLOWED_STATUSES,
            F1010_M3_PASSWORDLESS_ALLOWED_MODES,
        )
        context_mock.assert_called_once_with(Path("."), 54, 369)

    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_f1010_m3_passwordless_rejects_invalid_push_topology(
        self,
        require_sha_mock,
        ancestor_mock,
        tree_mock,
        parents_mock,
    ) -> None:
        merge = "2" * 40
        candidate = "1" * 40
        tree_mock.return_value = F1010_M3_PASSWORDLESS_BASE_TREE
        for parents in (
            [F1010_M3_PASSWORDLESS_BASE],
            ["0" * 40, candidate],
            [F1010_M3_PASSWORDLESS_BASE, candidate, "3" * 40],
        ):
            with self.subTest(parents=parents):
                parents_mock.return_value = parents
                with self.assertRaises(BoundaryError):
                    validate_f1010_m3_passwordless(
                        Path("."), F1010_M3_PASSWORDLESS_BASE, merge, "push"
                    )

    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_f1010_m3_passwordless_rejects_push_tree_mismatch(
        self,
        require_sha_mock,
        ancestor_mock,
        tree_mock,
        parents_mock,
    ) -> None:
        merge = "2" * 40
        candidate = "1" * 40
        parents_mock.side_effect = [
            [F1010_M3_PASSWORDLESS_BASE, candidate],
            [F1010_M3_PASSWORDLESS_BASE],
        ]
        tree_mock.side_effect = [
            F1010_M3_PASSWORDLESS_BASE_TREE,
            "3" * 40,
            "4" * 40,
        ]

        with self.assertRaises(BoundaryError):
            validate_f1010_m3_passwordless(
                Path("."), F1010_M3_PASSWORDLESS_BASE, merge, "push"
            )

    @mock.patch("scripts.security.f109_boundary.validate_f1010_m3_passwordless")
    @mock.patch("scripts.security.f109_boundary.parse_args")
    def test_cli_rejects_passwordless_branch_with_baseline_drift(
        self,
        parse_args_mock,
        validate_passwordless_mock,
    ) -> None:
        parse_args_mock.return_value = self.cli_args(
            head_ref=F1010_M3_PASSWORDLESS_HEAD_REF,
            base_sha="0" * 40,
        )

        self.assertEqual(main(), 1)
        validate_passwordless_mock.assert_not_called()

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_f1010_m3_preflight_payload_accepts_pr_and_protected_push(
        self,
        require_sha_mock,
        ancestor_mock,
        tree_mock,
        parents_mock,
        delta_mock,
        context_mock,
    ) -> None:
        candidate = "4" * 40
        merge = "5" * 40

        tree_mock.return_value = F1010_M3_PREFLIGHT_PAYLOAD_BASE_TREE
        parents_mock.return_value = [F1010_M3_PREFLIGHT_PAYLOAD_BASE]
        validate_f1010_m3_preflight_payload(
            Path("."), F1010_M3_PREFLIGHT_PAYLOAD_BASE, candidate, "pull_request"
        )
        delta_mock.assert_called_with(
            Path("."), F1010_M3_PREFLIGHT_PAYLOAD_BASE, candidate,
            F1010_M3_PREFLIGHT_PAYLOAD_ALLOWED_STATUSES,
            F1010_M3_PREFLIGHT_PAYLOAD_ALLOWED_MODES,
        )

        delta_mock.reset_mock()
        context_mock.reset_mock()
        parents_mock.side_effect = [
            [F1010_M3_PREFLIGHT_PAYLOAD_BASE, candidate],
            [F1010_M3_PREFLIGHT_PAYLOAD_BASE],
        ]
        tree_mock.side_effect = [
            F1010_M3_PREFLIGHT_PAYLOAD_BASE_TREE,
            "6" * 40,
            "6" * 40,
        ]
        validate_f1010_m3_preflight_payload(
            Path("."), F1010_M3_PREFLIGHT_PAYLOAD_BASE, merge, "push"
        )
        delta_mock.assert_called_once_with(
            Path("."), F1010_M3_PREFLIGHT_PAYLOAD_BASE, candidate,
            F1010_M3_PREFLIGHT_PAYLOAD_ALLOWED_STATUSES,
            F1010_M3_PREFLIGHT_PAYLOAD_ALLOWED_MODES,
        )
        context_mock.assert_called_once_with(Path("."), 54, 374)

    @mock.patch("scripts.security.f109_boundary.validate_f1010_m3_preflight_payload")
    @mock.patch("scripts.security.f109_boundary.changed_statuses")
    @mock.patch("scripts.security.f109_boundary.parse_args")
    def test_cli_rejects_preflight_payload_from_wrong_branch(
        self,
        parse_args_mock,
        changed_statuses_mock,
        validate_payload_mock,
    ) -> None:
        parse_args_mock.return_value = self.cli_args(head_ref="wrong-branch")
        changed_statuses_mock.return_value = {
            ".context/operaciones/m3_reader_f10_10_preflight_payload_2026_08_11.json": "A"
        }

        self.assertEqual(main(), 1)
        validate_payload_mock.assert_not_called()

    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_f1010_m3_preflight_payload_rejects_invalid_push_topology(
        self,
        require_sha_mock,
        ancestor_mock,
        tree_mock,
        parents_mock,
    ) -> None:
        merge = "5" * 40
        tree_mock.return_value = F1010_M3_PREFLIGHT_PAYLOAD_BASE_TREE
        for parents in (
            [F1010_M3_PREFLIGHT_PAYLOAD_BASE],
            ["0" * 40, "4" * 40],
            [F1010_M3_PREFLIGHT_PAYLOAD_BASE, "4" * 40, "6" * 40],
        ):
            with self.subTest(parents=parents):
                parents_mock.return_value = parents
                with self.assertRaises(BoundaryError):
                    validate_f1010_m3_preflight_payload(
                        Path("."), F1010_M3_PREFLIGHT_PAYLOAD_BASE, merge, "push"
                    )

    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_f1010_m3_preflight_payload_rejects_push_tree_mismatch(
        self,
        require_sha_mock,
        ancestor_mock,
        tree_mock,
        parents_mock,
    ) -> None:
        merge = "5" * 40
        candidate = "4" * 40
        parents_mock.side_effect = [
            [F1010_M3_PREFLIGHT_PAYLOAD_BASE, candidate],
            [F1010_M3_PREFLIGHT_PAYLOAD_BASE],
        ]
        tree_mock.side_effect = [
            F1010_M3_PREFLIGHT_PAYLOAD_BASE_TREE,
            "6" * 40,
            "7" * 40,
        ]

        with self.assertRaises(BoundaryError):
            validate_f1010_m3_preflight_payload(
                Path("."), F1010_M3_PREFLIGHT_PAYLOAD_BASE, merge, "push"
            )

    def test_f1010_m3_preflight_payload_is_canonical_and_zero_capability(self) -> None:
        root = Path(__file__).resolve().parents[1]
        payload = json.loads(
            (root / ".context/operaciones/m3_reader_f10_10_preflight_payload_2026_08_11.json")
            .read_text(encoding="utf-8")
        )
        canonical = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        ).encode("ascii")

        assert hashlib.sha256(canonical).hexdigest() == (
            "68fd845808dbe694984ffbdd087b44e19754b4c76c14da862d74dad232971613"
        )
        assert payload["gate"] == "APPROVE_F10_10_M3_READER_PREFLIGHT_FREE"
        assert payload["target_alias"] == "FREE_DB"
        assert payload["candidate_commit"] == F1010_M3_PREFLIGHT_PAYLOAD_BASE
        assert payload["candidate_tree"] == F1010_M3_PREFLIGHT_PAYLOAD_BASE_TREE
        assert payload["max_window_seconds"] == 14_400
        for capability in (
            "network_allowed", "password_allowed", "remote_ddl_allowed",
            "remote_dml_allowed", "remote_read_allowed",
        ):
            assert payload[capability] is False
        rendered = canonical.decode("ascii").lower()
        assert not any(
            marker in rendered
            for marker in ("supabase.co", "project_ref", "sql_host", "password\"")
        )

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_f1010_m3_preflight_evidence_accepts_pr_and_protected_push(
        self,
        require_sha_mock,
        ancestor_mock,
        tree_mock,
        parents_mock,
        delta_mock,
        context_mock,
    ) -> None:
        candidate = "8" * 40
        merge = "9" * 40
        tree_mock.return_value = F1010_M3_PREFLIGHT_EVIDENCE_BASE_TREE
        parents_mock.return_value = [F1010_M3_PREFLIGHT_EVIDENCE_BASE]
        validate_f1010_m3_preflight_evidence(
            Path("."), F1010_M3_PREFLIGHT_EVIDENCE_BASE, candidate, "pull_request"
        )
        delta_mock.assert_called_with(
            Path("."), F1010_M3_PREFLIGHT_EVIDENCE_BASE, candidate,
            F1010_M3_PREFLIGHT_EVIDENCE_ALLOWED_STATUSES,
            F1010_M3_PREFLIGHT_EVIDENCE_ALLOWED_MODES,
        )

        delta_mock.reset_mock()
        context_mock.reset_mock()
        parents_mock.side_effect = [
            [F1010_M3_PREFLIGHT_EVIDENCE_BASE, candidate],
            [F1010_M3_PREFLIGHT_EVIDENCE_BASE],
        ]
        tree_mock.side_effect = [
            F1010_M3_PREFLIGHT_EVIDENCE_BASE_TREE,
            "a" * 40,
            "a" * 40,
        ]
        validate_f1010_m3_preflight_evidence(
            Path("."), F1010_M3_PREFLIGHT_EVIDENCE_BASE, merge, "push"
        )
        context_mock.assert_called_once_with(Path("."), 55, 379)

    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_f1010_m3_preflight_evidence_rejects_invalid_push(
        self,
        require_sha_mock,
        ancestor_mock,
        tree_mock,
        parents_mock,
    ) -> None:
        merge = "9" * 40
        candidate = "8" * 40
        tree_mock.return_value = F1010_M3_PREFLIGHT_EVIDENCE_BASE_TREE
        for parents in (
            [F1010_M3_PREFLIGHT_EVIDENCE_BASE],
            ["0" * 40, candidate],
            [F1010_M3_PREFLIGHT_EVIDENCE_BASE, candidate, "a" * 40],
        ):
            with self.subTest(parents=parents):
                parents_mock.return_value = parents
                with self.assertRaises(BoundaryError):
                    validate_f1010_m3_preflight_evidence(
                        Path("."), F1010_M3_PREFLIGHT_EVIDENCE_BASE, merge, "push"
                    )

        parents_mock.side_effect = [
            [F1010_M3_PREFLIGHT_EVIDENCE_BASE, candidate],
            [F1010_M3_PREFLIGHT_EVIDENCE_BASE],
        ]
        tree_mock.side_effect = [
            F1010_M3_PREFLIGHT_EVIDENCE_BASE_TREE,
            "a" * 40,
            "b" * 40,
        ]
        with self.assertRaises(BoundaryError):
            validate_f1010_m3_preflight_evidence(
                Path("."), F1010_M3_PREFLIGHT_EVIDENCE_BASE, merge, "push"
            )

    @mock.patch("scripts.security.f109_boundary.validate_f1010_m3_preflight_evidence")
    @mock.patch("scripts.security.f109_boundary.changed_statuses")
    @mock.patch("scripts.security.f109_boundary.parse_args")
    def test_cli_rejects_preflight_evidence_from_wrong_branch(
        self,
        parse_args_mock,
        changed_statuses_mock,
        validate_evidence_mock,
    ) -> None:
        parse_args_mock.return_value = self.cli_args(head_ref="wrong-branch")
        changed_statuses_mock.return_value = {
            ".context/operaciones/m3_reader_f10_10_preflight_evidence_2026_08_11.md": "A"
        }
        self.assertEqual(main(), 1)
        validate_evidence_mock.assert_not_called()

    def test_f1010_m3_preflight_result_and_gate_ledger_are_canonical(self) -> None:
        root = Path(__file__).resolve().parents[1]
        result = json.loads(
            (root / ".context/operaciones/m3_reader_f10_10_preflight_result_2026_08_11.json")
            .read_text(encoding="utf-8")
        )
        canonical = json.dumps(
            result, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        ).encode("ascii")

        assert hashlib.sha256(canonical).hexdigest() == (
            "9ea235083a5c7e32df30c62a462fefb96bc91d19295e1339a3e9112b2d3a41b1"
        )
        assert result["decision"] == "PASS"
        assert result["network"] == "none"
        assert result["password_consumed"] is False
        assert result["reason_codes"] == []
        assert result["remote_read"] is False
        assert result["remote_ddl"] is False
        assert result["remote_dml"] is False
        assert result["executed_at"] < result["valid_until"]

        authority_paths = (
            ".context/estado_del_proyecto.md",
            ".context/operaciones/m3_f10_10_scope_por_ambiente_target.md",
            ".context/operaciones/m3_reader_f10_10_rebaseline.md",
            ".context/operaciones/plan_remediacion_metadata_f10_10.md",
            ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md",
        )
        authority = "\n".join(
            (root / path).read_text(encoding="utf-8") for path in authority_paths
        )
        assert "M3_READER_PREFLIGHT_PAYLOAD_READY_GATE_PENDING" not in authority
        assert "M3_PUBLIC_DB_ACL_DIAGNOSTIC_STOP_BINDING_REQUIRED" in authority
        assert "CONSUMED_ONCE_PASS" in authority
        assert "CONSUMED_ONCE_FAILED_ROLLBACK_SUPERSEDED" in authority
        for gate in (
            "APPROVE_F10_10_M3_READER_DDL_FREE",
            "APPROVE_F10_10_M3_READER_Q0_FREE",
            "APPROVE_M3_FREE_READONLY",
            "APPROVE_F10_10_M3_READER_TEARDOWN_FREE",
        ):
            assert gate in authority

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_f1010_m3_final_readiness_accepts_direct_candidate(
        self,
        require_sha_mock,
        ancestor_mock,
        tree_mock,
        parents_mock,
        delta_mock,
        context_mock,
    ) -> None:
        head = "c" * 40
        tree_mock.return_value = F1010_M3_FINAL_READINESS_BASE_TREE
        parents_mock.return_value = [F1010_M3_FINAL_READINESS_BASE]
        validate_f1010_m3_final_readiness(
            Path("."), F1010_M3_FINAL_READINESS_BASE, head, "pull_request"
        )
        delta_mock.assert_called_once_with(
            Path("."), F1010_M3_FINAL_READINESS_BASE, head,
            F1010_M3_FINAL_READINESS_ALLOWED_STATUSES,
            F1010_M3_FINAL_READINESS_ALLOWED_MODES,
        )
        context_mock.assert_called_once_with(Path("."), 55, 379)

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_f1010_m3_final_readiness_accepts_protected_push(
        self,
        require_sha_mock,
        ancestor_mock,
        tree_mock,
        parents_mock,
        delta_mock,
        context_mock,
    ) -> None:
        candidate = "c" * 40
        merge = "d" * 40
        parents_mock.side_effect = [
            [F1010_M3_FINAL_READINESS_BASE, candidate],
            [F1010_M3_FINAL_READINESS_BASE],
        ]
        tree_mock.side_effect = [
            F1010_M3_FINAL_READINESS_BASE_TREE,
            "e" * 40,
            "e" * 40,
        ]
        validate_f1010_m3_final_readiness(
            Path("."), F1010_M3_FINAL_READINESS_BASE, merge, "push"
        )
        delta_mock.assert_called_once_with(
            Path("."), F1010_M3_FINAL_READINESS_BASE, candidate,
            F1010_M3_FINAL_READINESS_ALLOWED_STATUSES,
            F1010_M3_FINAL_READINESS_ALLOWED_MODES,
        )
        context_mock.assert_called_once_with(Path("."), 55, 379)

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_f1010_m3_apply_projection_accepts_direct_candidate(
        self,
        require_sha_mock,
        ancestor_mock,
        tree_mock,
        parents_mock,
        delta_mock,
        context_mock,
    ) -> None:
        head = "c" * 40
        tree_mock.return_value = F1010_M3_APPLY_PROJECTION_BASE_TREE
        parents_mock.return_value = [F1010_M3_APPLY_PROJECTION_BASE]

        validate_f1010_m3_apply_projection(
            Path("."), F1010_M3_APPLY_PROJECTION_BASE, head, "pull_request"
        )

        delta_mock.assert_called_once_with(
            Path("."),
            F1010_M3_APPLY_PROJECTION_BASE,
            head,
            F1010_M3_APPLY_PROJECTION_ALLOWED_STATUSES,
            F1010_M3_APPLY_PROJECTION_ALLOWED_MODES,
        )
        context_mock.assert_called_once_with(Path("."), 55, 379)

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_f1010_m3_apply_projection_accepts_protected_push(
        self,
        require_sha_mock,
        ancestor_mock,
        tree_mock,
        parents_mock,
        delta_mock,
        context_mock,
    ) -> None:
        candidate = "c" * 40
        merge = "d" * 40
        parents_mock.side_effect = [
            [F1010_M3_APPLY_PROJECTION_BASE, candidate],
            [F1010_M3_APPLY_PROJECTION_BASE],
        ]
        tree_mock.side_effect = [
            F1010_M3_APPLY_PROJECTION_BASE_TREE,
            "e" * 40,
            "e" * 40,
        ]

        validate_f1010_m3_apply_projection(
            Path("."), F1010_M3_APPLY_PROJECTION_BASE, merge, "push"
        )

        delta_mock.assert_called_once_with(
            Path("."),
            F1010_M3_APPLY_PROJECTION_BASE,
            candidate,
            F1010_M3_APPLY_PROJECTION_ALLOWED_STATUSES,
            F1010_M3_APPLY_PROJECTION_ALLOWED_MODES,
        )
        context_mock.assert_called_once_with(Path("."), 55, 379)

    @mock.patch("scripts.security.f109_boundary.commit_parents", return_value=["0" * 40])
    @mock.patch(
        "scripts.security.f109_boundary.commit_tree",
        return_value=F1010_M3_APPLY_PROJECTION_BASE_TREE,
    )
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_f1010_m3_apply_projection_rejects_non_direct_pr(
        self,
        require_sha_mock,
        ancestor_mock,
        tree_mock,
        parents_mock,
    ) -> None:
        with self.assertRaises(BoundaryError):
            validate_f1010_m3_apply_projection(
                Path("."),
                F1010_M3_APPLY_PROJECTION_BASE,
                "c" * 40,
                "pull_request",
            )

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_f1010_m3_ddl_payload_accepts_direct_candidate(
        self,
        require_sha_mock,
        ancestor_mock,
        tree_mock,
        parents_mock,
        delta_mock,
        context_mock,
    ) -> None:
        head = "c" * 40
        tree_mock.return_value = F1010_M3_DDL_PAYLOAD_BASE_TREE
        parents_mock.return_value = [F1010_M3_DDL_PAYLOAD_BASE]

        validate_f1010_m3_ddl_payload(
            Path("."), F1010_M3_DDL_PAYLOAD_BASE, head, "pull_request"
        )

        delta_mock.assert_called_once_with(
            Path("."),
            F1010_M3_DDL_PAYLOAD_BASE,
            head,
            F1010_M3_DDL_PAYLOAD_ALLOWED_STATUSES,
            F1010_M3_DDL_PAYLOAD_ALLOWED_MODES,
        )
        context_mock.assert_called_once_with(Path("."), 55, 382)

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_f1010_m3_ddl_payload_accepts_protected_push(
        self,
        require_sha_mock,
        ancestor_mock,
        tree_mock,
        parents_mock,
        delta_mock,
        context_mock,
    ) -> None:
        candidate = "c" * 40
        merge = "d" * 40
        parents_mock.side_effect = [
            [F1010_M3_DDL_PAYLOAD_BASE, candidate],
            [F1010_M3_DDL_PAYLOAD_BASE],
        ]
        tree_mock.side_effect = [
            F1010_M3_DDL_PAYLOAD_BASE_TREE,
            "e" * 40,
            "e" * 40,
        ]

        validate_f1010_m3_ddl_payload(
            Path("."), F1010_M3_DDL_PAYLOAD_BASE, merge, "push"
        )

        delta_mock.assert_called_once_with(
            Path("."),
            F1010_M3_DDL_PAYLOAD_BASE,
            candidate,
            F1010_M3_DDL_PAYLOAD_ALLOWED_STATUSES,
            F1010_M3_DDL_PAYLOAD_ALLOWED_MODES,
        )
        context_mock.assert_called_once_with(Path("."), 55, 382)

    def test_f1010_m3_ddl_payload_is_canonical_and_non_executable(self) -> None:
        root = Path(__file__).resolve().parents[1]
        payload_path = (
            root
            / ".context/operaciones/m3_reader_f10_10_ddl_free_payload_2026_08_12.json"
        )
        raw = payload_path.read_bytes()
        payload = json.loads(raw)
        canonical = (
            json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"
        ).encode("ascii")

        self.assertEqual(raw, canonical)
        self.assertEqual(payload["gate"], "APPROVE_F10_10_M3_READER_DDL_FREE_V2")
        self.assertEqual(payload["candidate_commit"], "bc268f119e04791bc17439aaa096e9e06c8b5e8b")
        self.assertEqual(payload["candidate_tree"], "fd08e8cee5cc7cc6d031fd59fbb5ed97e9f9ad68")
        self.assertEqual(payload["target_alias"], "FREE_DB")
        self.assertEqual(payload["migration_name"], payload["idempotency_identity"])
        self.assertEqual(payload["apply_migration_max_calls"], 1)
        self.assertEqual(payload["automatic_retries"], 0)
        self.assertFalse(payload["execute_sql_fallback_allowed"])
        self.assertEqual(payload["status"], "PROPOSED_NOT_EXECUTED")
        self.assertEqual(
            payload["applied_query_digest"],
            "sha256:a13e0e814185f756d612d8b092561a5baa71442a2cff2e83db081eb32ddd2f3f",
        )
        self.assertEqual(
            payload["package_digest"],
            "sha256:d68d44c6ae61bac120f460955f86547082c0e42b70868a35a330fda8fb7883aa",
        )
        self.assertEqual(
            payload["compensation_digest"],
            "sha256:609a5b22202021de44ff1fa484ddb1a35fbb7bb15f495bc9afe304542d288fe0",
        )
        self.assertEqual(
            payload["query_set_digest"],
            "sha256:d3bc8fddf7d0d8b39497e4f184c7669bec3cbc4537dde7aeb3757d4afe53957a",
        )
        self.assertEqual(
            payload["provisioner_fingerprint"],
            "sha256:e8bb3d66f6efdfb2699307759b8729d9b586bd42856c3600e43d93e78bcd9381",
        )
        self.assertEqual(
            payload["target_binding_digest"],
            "sha256:68fa6d9566799eb19c99b2415fabad472a8a3a4e51eefb54510c93afbfe91715",
        )
        for field in (
            "network_allowed",
            "password_allowed",
            "remote_ddl_allowed",
            "remote_dml_allowed",
            "remote_read_allowed",
            "q0_allowed",
            "teardown_allowed",
        ):
            self.assertFalse(payload[field])
        self.assertNotEqual(
            payload["target_binding_digest"],
            "sha256:013972e22906ea23d2aa6d4f7caaa9a92f93d6c4618d5e44e93f49c897ae0f01",
        )
        for key, value in payload.items():
            if key.endswith("digest") or key.endswith("fingerprint"):
                self.assertRegex(value, r"^sha256:[0-9a-f]{64}$")
        serialized = raw.decode("ascii").lower()
        for forbidden in (
            "project_ref",
            "sql_host",
            "api_url",
            "password_value",
            "q0_predecessor",
            "execute_sql\"",
        ):
            self.assertNotIn(forbidden, serialized)

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_f1010_m3_ddl_payload_refresh_accepts_direct_candidate(
        self,
        require_sha_mock,
        ancestor_mock,
        tree_mock,
        parents_mock,
        delta_mock,
        context_mock,
    ) -> None:
        head = "c" * 40
        tree_mock.return_value = F1010_M3_DDL_PAYLOAD_REFRESH_BASE_TREE
        parents_mock.return_value = [F1010_M3_DDL_PAYLOAD_REFRESH_BASE]

        validate_f1010_m3_ddl_payload_refresh(
            Path("."), F1010_M3_DDL_PAYLOAD_REFRESH_BASE, head, "pull_request"
        )

        delta_mock.assert_called_once_with(
            Path("."),
            F1010_M3_DDL_PAYLOAD_REFRESH_BASE,
            head,
            F1010_M3_DDL_PAYLOAD_REFRESH_ALLOWED_STATUSES,
            F1010_M3_DDL_PAYLOAD_REFRESH_ALLOWED_MODES,
        )
        context_mock.assert_called_once_with(Path("."), 55, 382)

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_f1010_m3_ddl_payload_refresh_accepts_protected_push(
        self,
        require_sha_mock,
        ancestor_mock,
        tree_mock,
        parents_mock,
        delta_mock,
        context_mock,
    ) -> None:
        candidate = "c" * 40
        merge = "d" * 40
        parents_mock.side_effect = [
            [F1010_M3_DDL_PAYLOAD_REFRESH_BASE, candidate],
            [F1010_M3_DDL_PAYLOAD_REFRESH_BASE],
        ]
        tree_mock.side_effect = [
            F1010_M3_DDL_PAYLOAD_REFRESH_BASE_TREE,
            "e" * 40,
            "e" * 40,
        ]

        validate_f1010_m3_ddl_payload_refresh(
            Path("."), F1010_M3_DDL_PAYLOAD_REFRESH_BASE, merge, "push"
        )

        delta_mock.assert_called_once_with(
            Path("."),
            F1010_M3_DDL_PAYLOAD_REFRESH_BASE,
            candidate,
            F1010_M3_DDL_PAYLOAD_REFRESH_ALLOWED_STATUSES,
            F1010_M3_DDL_PAYLOAD_REFRESH_ALLOWED_MODES,
        )
        context_mock.assert_called_once_with(Path("."), 55, 382)

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_f1010_m3_nullability_remediation_accepts_direct_candidate(
        self, require_sha_mock, ancestor_mock, tree_mock, parents_mock,
        delta_mock, context_mock,
    ) -> None:
        head = "c" * 40
        tree_mock.return_value = F1010_M3_NULLABILITY_REMEDIATION_BASE_TREE
        parents_mock.return_value = [F1010_M3_NULLABILITY_REMEDIATION_BASE]

        validate_f1010_m3_nullability_remediation(
            Path("."), F1010_M3_NULLABILITY_REMEDIATION_BASE, head, "pull_request"
        )

        delta_mock.assert_called_once_with(
            Path("."), F1010_M3_NULLABILITY_REMEDIATION_BASE, head,
            F1010_M3_NULLABILITY_REMEDIATION_ALLOWED_STATUSES,
            F1010_M3_NULLABILITY_REMEDIATION_ALLOWED_MODES,
        )
        context_mock.assert_called_once_with(Path("."), 55, 379)

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_f1010_m3_nullability_remediation_accepts_protected_push(
        self, require_sha_mock, ancestor_mock, tree_mock, parents_mock,
        delta_mock, context_mock,
    ) -> None:
        candidate = "c" * 40
        merge = "d" * 40
        parents_mock.side_effect = [
            [F1010_M3_NULLABILITY_REMEDIATION_BASE, candidate],
            [F1010_M3_NULLABILITY_REMEDIATION_BASE],
        ]
        tree_mock.side_effect = [
            F1010_M3_NULLABILITY_REMEDIATION_BASE_TREE, "e" * 40, "e" * 40,
        ]

        validate_f1010_m3_nullability_remediation(
            Path("."), F1010_M3_NULLABILITY_REMEDIATION_BASE, merge, "push"
        )

        delta_mock.assert_called_once_with(
            Path("."), F1010_M3_NULLABILITY_REMEDIATION_BASE, candidate,
            F1010_M3_NULLABILITY_REMEDIATION_ALLOWED_STATUSES,
            F1010_M3_NULLABILITY_REMEDIATION_ALLOWED_MODES,
        )
        context_mock.assert_called_once_with(Path("."), 55, 379)

    def test_f1010_m3_nullability_remediation_payload_is_non_executable(self) -> None:
        root = Path(__file__).resolve().parents[1]
        path = root / ".context/operaciones/m3_reader_f10_10_nullability_remediation_2026_08_12.json"
        raw = path.read_bytes()
        payload = json.loads(raw)

        self.assertEqual(
            raw,
            (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii"),
        )
        self.assertEqual(payload["baseline_commit"], F1010_M3_NULLABILITY_REMEDIATION_BASE)
        self.assertEqual(payload["baseline_tree"], F1010_M3_NULLABILITY_REMEDIATION_BASE_TREE)
        self.assertEqual(payload["superseded_migration_identity"], "fase10_10_m3_free_reader_free_ddl_v1")
        self.assertEqual(payload["next_migration_identity"], "fase10_10_m3_free_reader_free_ddl_v2")
        self.assertEqual(payload["apply_migration_max_calls"], 0)
        self.assertFalse(payload["ddl_binding_generated"])
        self.assertIsNone(payload["target_binding_digest"])
        self.assertIsNone(payload["private_projection_sql_path"])
        self.assertIsNone(payload["private_projection_manifest_path"])
        for field in (
            "network_allowed", "password_allowed", "remote_ddl_allowed",
            "remote_dml_allowed", "remote_read_allowed", "q0_allowed",
            "teardown_allowed",
        ):
            self.assertFalse(payload[field])

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_f1010_m3_ddl_v2_payload_accepts_direct_candidate(
        self, require_sha_mock, ancestor_mock, tree_mock, parents_mock,
        delta_mock, context_mock,
    ) -> None:
        head = "c" * 40
        tree_mock.return_value = F1010_M3_DDL_V2_PAYLOAD_BASE_TREE
        parents_mock.return_value = [F1010_M3_DDL_V2_PAYLOAD_BASE]

        validate_f1010_m3_ddl_v2_payload(
            Path("."), F1010_M3_DDL_V2_PAYLOAD_BASE, head, "pull_request"
        )

        delta_mock.assert_called_once_with(
            Path("."), F1010_M3_DDL_V2_PAYLOAD_BASE, head,
            F1010_M3_DDL_V2_PAYLOAD_ALLOWED_STATUSES,
            F1010_M3_DDL_V2_PAYLOAD_ALLOWED_MODES,
        )
        context_mock.assert_called_once_with(Path("."), 55, 376)

    def test_f1010_m3_ddl_v2_payload_contract(self) -> None:
        root = Path(__file__).resolve().parents[1]
        path = root / ".context/operaciones/m3_reader_f10_10_ddl_free_payload_2026_08_12.json"
        raw = path.read_bytes()
        payload = json.loads(raw)

        canonical = (
            json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"
        ).encode("ascii")
        self.assertEqual(raw, canonical)
        self.assertEqual(payload["gate"], "APPROVE_F10_10_M3_READER_DDL_FREE_V2")
        self.assertEqual(payload["migration_name"], "fase10_10_m3_free_reader_free_ddl_v2")
        self.assertEqual(payload["idempotency_identity"], payload["migration_name"])
        self.assertEqual(payload["apply_migration_max_calls"], 1)
        self.assertEqual(payload["automatic_retries"], 0)
        self.assertFalse(payload["execute_sql_fallback_allowed"])
        self.assertFalse(payload["network_allowed"])
        self.assertFalse(payload["password_allowed"])
        self.assertFalse(payload["remote_ddl_allowed"])
        self.assertFalse(payload["remote_dml_allowed"])
        self.assertFalse(payload["remote_read_allowed"])
        self.assertFalse(payload["q0_allowed"])
        self.assertFalse(payload["teardown_allowed"])
        self.assertEqual(payload["status"], "PROPOSED_NOT_EXECUTED")

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_f1010_m3_public_acl_rebaseline_accepts_direct_candidate(
        self, require_sha_mock, ancestor_mock, tree_mock, parents_mock,
        delta_mock, context_mock,
    ) -> None:
        head = "d" * 40
        tree_mock.return_value = F1010_M3_PUBLIC_ACL_REBASELINE_BASE_TREE
        parents_mock.return_value = [F1010_M3_PUBLIC_ACL_REBASELINE_BASE]

        validate_f1010_m3_public_acl_rebaseline(
            Path("."), F1010_M3_PUBLIC_ACL_REBASELINE_BASE, head, "pull_request"
        )

        delta_mock.assert_called_once_with(
            Path("."), F1010_M3_PUBLIC_ACL_REBASELINE_BASE, head,
            F1010_M3_PUBLIC_ACL_REBASELINE_ALLOWED_STATUSES,
            F1010_M3_PUBLIC_ACL_REBASELINE_ALLOWED_MODES,
        )
        context_mock.assert_called_once_with(Path("."), 56, 377)

    def test_f1010_m3_public_acl_diagnostic_payload_contract(self) -> None:
        path = Path(__file__).resolve().parents[1] / ".context/operaciones/m3_public_db_acl_diagnostic_free_payload_2026_08_12.json"
        raw = path.read_bytes()
        payload = json.loads(raw)

        self.assertEqual(raw, (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii"))
        self.assertEqual(payload["gate"], "APPROVE_F10_10_M3_PUBLIC_DB_ACL_DIAGNOSTIC_FREE")
        self.assertEqual(payload["max_calls"], 1)
        self.assertEqual(payload["remote_read_scope"], "PG_CATALOG_COUNTS_AND_FLAGS_ONLY")
        self.assertEqual(payload["application_rows_allowed"], 0)
        self.assertFalse(payload["ddl_allowed"])
        self.assertFalse(payload["dml_allowed"])
        self.assertFalse(payload["automatic_continuation"])
        self.assertIsNone(payload["candidate_commit"])
        self.assertIsNone(payload["candidate_tree"])

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

    def test_f1010_allowlists_are_exact_and_disjoint(self) -> None:
        self.assertEqual(
            F1010_M2A_ALLOWED_STATUSES,
            {
                ".github/workflows/f9-7-contract.yml": "M",
                ".github/workflows/security-audit.yml": "M",
                "scripts/security/f109_boundary.py": "M",
                "tests/test_fase10_9_branch_reconciliation.py": "M",
            },
        )
        self.assertEqual(
            F1010_M1_ALLOWED_STATUSES,
            {
                "scripts/shared/f10_10_metadata_remediation.py": "A",
                "tests/test_fase10_10_m1_offline_tooling.py": "A",
            },
        )
        self.assertEqual(F1010_M2A_ALLOWED_MODES[".github/workflows/security-audit.yml"], "100755")
        self.assertTrue(all(mode == "100644" for mode in F1010_M1_ALLOWED_MODES.values()))
        self.assertEqual(
            F1010_M3_ALLOWED_STATUSES,
            {
                ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
                ".context/estado_del_proyecto.md": "M",
                ".context/operaciones/flujo_release_minimo.md": "M",
                ".context/operaciones/m3_f10_10_scope_por_ambiente_target.md": "M",
                ".context/operaciones/plan_cierre_hito1_ca1_only.md": "M",
                ".context/operaciones/plan_remediacion_metadata_f10_10.md": "M",
                ".github/workflows/f9-7-contract.yml": "M",
                "scripts/maintenance/f10_10_m3_readonly_collector.py": "A",
                "scripts/security/f109_boundary.py": "M",
                "tests/test_f10_10_m3_readonly_collector.py": "A",
                "tests/test_fase10_9_branch_reconciliation.py": "M",
            },
        )
        self.assertTrue(all(mode == "100644" for mode in F1010_M3_ALLOWED_MODES.values()))
        self.assertEqual(len(F1010_M3_READER_ALLOWED_STATUSES), 19)
        self.assertEqual(
            F1010_M3_READER_ALLOWED_MODES[
                "tests/sql/run_fase10_10_m3_free_reader_postgres17.sh"
            ],
            "100755",
        )
        self.assertTrue(
            all(
                mode == "100644"
                for path, mode in F1010_M3_READER_ALLOWED_MODES.items()
                if path != "tests/sql/run_fase10_10_m3_free_reader_postgres17.sh"
            )
        )
        self.assertEqual(
            F1010_M3_READER_POST_MERGE_ALLOWED_STATUSES,
            {
                ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
                ".context/estado_del_proyecto.md": "M",
                ".context/operaciones/flujo_release_minimo.md": "M",
                ".context/operaciones/m3_f10_10_scope_por_ambiente_target.md": "M",
                ".context/operaciones/m3_reader_f10_10_post_merge_evidence_2026_08_11.md": "A",
                ".context/operaciones/m3_reader_f10_10_rebaseline.md": "M",
                ".context/operaciones/plan_cierre_hito1_ca1_only.md": "M",
                ".context/operaciones/plan_remediacion_metadata_f10_10.md": "M",
                "scripts/security/f109_boundary.py": "M",
                "tests/test_fase10_9_branch_reconciliation.py": "M",
            },
        )
        self.assertTrue(
            all(
                mode == "100644"
                for mode in F1010_M3_READER_POST_MERGE_ALLOWED_MODES.values()
            )
        )
        self.assertEqual(
            F1010_M3_ROTATION_ALLOWED_STATUSES,
            {
                ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
                ".context/estado_del_proyecto.md": "M",
                ".context/operaciones/flujo_release_minimo.md": "M",
                ".context/operaciones/m3_f10_10_scope_por_ambiente_target.md": "M",
                ".context/operaciones/m3_reader_f10_10_post_merge_evidence_2026_08_11.md": "M",
                ".context/operaciones/m3_reader_f10_10_rebaseline.md": "M",
                ".context/operaciones/m3_reader_f10_10_rotation_attestation_2026_08_11.md": "A",
                ".context/operaciones/plan_cierre_hito1_ca1_only.md": "M",
                ".context/operaciones/plan_remediacion_metadata_f10_10.md": "M",
                "scripts/security/f109_boundary.py": "M",
                "tests/test_fase10_9_branch_reconciliation.py": "M",
            },
        )
        self.assertTrue(
            all(mode == "100644" for mode in F1010_M3_ROTATION_ALLOWED_MODES.values())
        )
        self.assertEqual(
            F1010_M3_PASSWORDLESS_ALLOWED_STATUSES,
            {
                ".context/operaciones/m3_f10_10_scope_por_ambiente_target.md": "M",
                ".context/operaciones/m3_reader_f10_10_rebaseline.md": "M",
                "scripts/maintenance/f10_10_m3_readonly_collector.py": "M",
                "scripts/security/f109_boundary.py": "M",
                "tests/test_f10_10_m3_readonly_collector.py": "M",
                "tests/test_fase10_9_branch_reconciliation.py": "M",
            },
        )
        self.assertTrue(
            all(
                mode == "100644"
                for mode in F1010_M3_PASSWORDLESS_ALLOWED_MODES.values()
            )
        )
        self.assertEqual(len(F1010_M3_PREFLIGHT_PAYLOAD_ALLOWED_STATUSES), 11)
        self.assertTrue(
            all(
                mode == "100644"
                for mode in F1010_M3_PREFLIGHT_PAYLOAD_ALLOWED_MODES.values()
            )
        )
        self.assertEqual(len(F1010_M3_PREFLIGHT_EVIDENCE_ALLOWED_STATUSES), 11)
        self.assertTrue(
            all(
                mode == "100644"
                for mode in F1010_M3_PREFLIGHT_EVIDENCE_ALLOWED_MODES.values()
            )
        )
        self.assertEqual(len(F1010_M3_FINAL_READINESS_ALLOWED_STATUSES), 6)
        self.assertTrue(
            all(
                mode == "100644"
                for mode in F1010_M3_FINAL_READINESS_ALLOWED_MODES.values()
            )
        )
        self.assertEqual(
            F1010_M3_APPLY_PROJECTION_ALLOWED_STATUSES,
            {
                ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
                ".context/estado_del_proyecto.md": "M",
                ".context/operaciones/m3_f10_10_scope_por_ambiente_target.md": "M",
                ".context/operaciones/m3_reader_f10_10_rebaseline.md": "M",
                ".github/workflows/f9-7-contract.yml": "M",
                "scripts/maintenance/f10_10_m3_apply_projection.py": "A",
                "scripts/security/f109_boundary.py": "M",
                "tests/sql/run_fase10_10_m3_free_reader_postgres17.sh": "M",
                "tests/test_f10_10_m3_apply_projection.py": "A",
                "tests/test_f10_10_m3_reader_package.py": "M",
                "tests/test_fase10_9_branch_reconciliation.py": "M",
            },
        )
        self.assertEqual(
            F1010_M3_APPLY_PROJECTION_ALLOWED_MODES[
                "tests/sql/run_fase10_10_m3_free_reader_postgres17.sh"
            ],
            "100755",
        )
        self.assertTrue(
            all(
                mode == "100644"
                for path, mode in F1010_M3_APPLY_PROJECTION_ALLOWED_MODES.items()
                if path != "tests/sql/run_fase10_10_m3_free_reader_postgres17.sh"
            )
        )
        for existing in (P1_ALLOWED_STATUSES, P2_ALLOWED_STATUSES, G2_ALLOWED_STATUSES, P5_ALLOWED_STATUSES):
            self.assertFalse(set(F1010_M1_ALLOWED_STATUSES).intersection(existing))

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

    def test_f1010_m1_workflow_wiring_is_hard_gated(self) -> None:
        root = Path(__file__).resolve().parents[1]
        for relative in (
            ".github/workflows/f9-7-contract.yml",
            ".github/workflows/security-audit.yml",
        ):
            workflow = (root / relative).read_text(encoding="utf-8")
            with self.subTest(workflow=relative):
                self.assertIn('F109_HEAD_REF" = "feat/f10-10-m1-offline-tooling"', workflow)
                self.assertIn('test "$F109_BASE_SHA" = "$protected_dev_tip"', workflow)
                self.assertIn('--f1010-m1-base "$f1010_m1_base"', workflow)
                self.assertIn('--f1010-m1-base-tree "$f1010_m1_base_tree"', workflow)
                self.assertIn('f1010_m1_base=""', workflow)
                self.assertIn('f1010_m1_base_tree=""', workflow)
                self.assertIn('f1010_m1_base="$F109_BASE_SHA"', workflow)
                self.assertIn('f1010_m1_base_tree="$(git rev-parse "$F109_BASE_SHA^{tree}")"', workflow)
                self.assertIn('f1010_m1_base_tree="$p1_base_tree"', workflow)

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

    @mock.patch("scripts.security.f109_boundary.validate_f1010_m1")
    @mock.patch("scripts.security.f109_boundary.changed_statuses")
    @mock.patch("scripts.security.f109_boundary.parse_args")
    def test_cli_rejects_f1010_m1_paths_from_wrong_branch(
        self,
        parse_args_mock,
        changed_statuses_mock,
        validate_m1_mock,
    ) -> None:
        parse_args_mock.return_value = self.cli_args(head_ref="wrong-branch")
        changed_statuses_mock.return_value = F1010_M1_ALLOWED_STATUSES

        self.assertEqual(main(), 1)
        validate_m1_mock.assert_not_called()

    @mock.patch("scripts.security.f109_boundary.validate_f1010_m1")
    @mock.patch("scripts.security.f109_boundary.changed_statuses")
    @mock.patch("scripts.security.f109_boundary.parse_args")
    def test_cli_rejects_partial_or_expanded_f1010_m1_push(
        self,
        parse_args_mock,
        changed_statuses_mock,
        validate_m1_mock,
    ) -> None:
        parse_args_mock.return_value = self.cli_args(
            event="push",
            head_ref="desarrollo",
            f1010_m1_base="a" * 40,
            f1010_m1_base_tree="c" * 40,
        )
        for delta in (
            {"scripts/shared/f10_10_metadata_remediation.py": "A"},
            {**F1010_M1_ALLOWED_STATUSES, "extra.txt": "A"},
        ):
            with self.subTest(delta=delta):
                changed_statuses_mock.return_value = delta
                self.assertEqual(main(), 1)
        validate_m1_mock.assert_not_called()

    @mock.patch("scripts.security.f109_boundary.validate_f1010_m1")
    @mock.patch("scripts.security.f109_boundary.validate_p1")
    @mock.patch("scripts.security.f109_boundary.changed_statuses")
    @mock.patch("scripts.security.f109_boundary.parse_args")
    def test_cli_rejects_mixed_f109_and_f1010_candidate(
        self,
        parse_args_mock,
        changed_statuses_mock,
        validate_p1_mock,
        validate_m1_mock,
    ) -> None:
        parse_args_mock.return_value = self.cli_args(
            event="push",
            head_ref="desarrollo",
            p1_base="a" * 40,
            p1_base_tree="c" * 40,
            f1010_m1_base="a" * 40,
            f1010_m1_base_tree="c" * 40,
        )
        changed_statuses_mock.return_value = {
            "scripts/shared/db_client.py": "M",
            "scripts/shared/f10_10_metadata_remediation.py": "A",
        }

        self.assertEqual(main(), 1)
        validate_p1_mock.assert_not_called()
        validate_m1_mock.assert_not_called()

    @mock.patch("scripts.security.f109_boundary.changed_statuses")
    @mock.patch("scripts.security.f109_boundary.parse_args")
    def test_cli_rejects_f1010_reserved_branches_with_wrong_baseline(
        self,
        parse_args_mock,
        changed_statuses_mock,
    ) -> None:
        for head_ref in (F1010_M2A_HEAD_REF, F1010_M1_HEAD_REF):
            with self.subTest(head_ref=head_ref):
                parse_args_mock.return_value = self.cli_args(head_ref=head_ref)
                self.assertEqual(main(), 1)
        changed_statuses_mock.assert_not_called()

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
