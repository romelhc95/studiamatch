from __future__ import annotations

import contextlib
import hashlib
import io
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
    F1010_M3_PUBLIC_ACL_V2_PAYLOAD_ALLOWED_MODES,
    F1010_M3_PUBLIC_ACL_V2_PAYLOAD_ALLOWED_STATUSES,
    F1010_M3_PUBLIC_ACL_V2_PAYLOAD_BASE,
    F1010_M3_PUBLIC_ACL_V2_PAYLOAD_BASE_TREE,
    F1010_M3_PUBLIC_ACL_V2_PAYLOAD_HEAD_REF,
    F1010_M3_PUBLIC_ACL_V3_ALLOWED_MODES,
    F1010_M3_PUBLIC_ACL_V3_ALLOWED_STATUSES,
    F1010_M3_PUBLIC_ACL_V3_BASE,
    F1010_M3_PUBLIC_ACL_V3_BASE_TREE,
    F1010_M3_PUBLIC_ACL_V3_HEAD_REF,
    F1010_M3_PUBLIC_ACL_V3_BOUND_ALLOWED_MODES,
    F1010_M3_PUBLIC_ACL_V3_BOUND_ALLOWED_STATUSES,
    F1010_M3_PUBLIC_ACL_V3_BOUND_BASE,
    F1010_M3_PUBLIC_ACL_V3_BOUND_BASE_TREE,
    F1010_M3_PUBLIC_ACL_V3_BOUND_HEAD_REF,
    F1010_M3_PUBLIC_ACL_PREFLIGHT_ALLOWED_MODES,
    F1010_M3_PUBLIC_ACL_PREFLIGHT_ALLOWED_STATUSES,
    F1010_M3_PUBLIC_ACL_PREFLIGHT_BASE,
    F1010_M3_PUBLIC_ACL_PREFLIGHT_BASE_TREE,
    F1010_M3_PUBLIC_ACL_PREFLIGHT_HEAD_REF,
    F1010_M3_PUBLIC_ACL_PREFLIGHT_POST_MERGE_ALLOWED_MODES,
    F1010_M3_PUBLIC_ACL_PREFLIGHT_POST_MERGE_ALLOWED_STATUSES,
    F1010_M3_PUBLIC_ACL_PREFLIGHT_POST_MERGE_BASE,
    F1010_M3_PUBLIC_ACL_PREFLIGHT_POST_MERGE_BASE_TREE,
    F1010_M3_PUBLIC_ACL_PREFLIGHT_POST_MERGE_HEAD_REF,
    F1010_M3_PUBLIC_ACL_PRIVATE_PREFLIGHT_V2_PAYLOAD_ALLOWED_MODES,
    F1010_M3_PUBLIC_ACL_PRIVATE_PREFLIGHT_V2_PAYLOAD_ALLOWED_STATUSES,
    F1010_M3_PUBLIC_ACL_PRIVATE_PREFLIGHT_V2_PAYLOAD_BASE,
    F1010_M3_PUBLIC_ACL_PRIVATE_PREFLIGHT_V2_PAYLOAD_BASE_TREE,
    F1010_M3_PUBLIC_ACL_PRIVATE_PREFLIGHT_V2_PAYLOAD_HEAD_REF,
    F1010_M3_PUBLIC_ACL_POST_MERGE_HARNESS_ALLOWED_STATUSES,
    F1010_M3_PUBLIC_ACL_POST_MERGE_HARNESS_BASE,
    F1010_M3_PUBLIC_ACL_POST_MERGE_HARNESS_HEAD_REF,
    F1010_M3_PUBLIC_ACL_V2_EVIDENCE_ALLOWED_STATUSES,
    F1010_M3_PUBLIC_ACL_V2_EVIDENCE_BASE,
    F1010_M3_PUBLIC_ACL_V2_EVIDENCE_HEAD_REF,
    F1010_M3_PUBLIC_ACL_FINAL_READINESS_ALLOWED_STATUSES,
    F1010_M3_PUBLIC_ACL_FINAL_READINESS_BASE,
    F1010_M3_PUBLIC_ACL_FINAL_READINESS_HEAD_REF,
    F1010_H1_CA1_REBASELINE_ALLOWED_MODES,
    F1010_H1_CA1_REBASELINE_ALLOWED_STATUSES,
    F1010_H1_CA1_REBASELINE_BASE,
    F1010_H1_CA1_REBASELINE_BASE_TREE,
    F1010_H1_CA1_REBASELINE_HEAD_REF,
    G5_PRODUCTION_READONLY_ALLOWED_MODES,
    G5_PRODUCTION_READONLY_ALLOWED_STATUSES,
    G5_PRODUCTION_READONLY_BASE,
    G5_PRODUCTION_READONLY_BASE_TREE,
    G5_PRODUCTION_READONLY_HEAD_REF,
    G5_GET_ONLY_ADAPTER_ALLOWED_MODES,
    G5_GET_ONLY_ADAPTER_ALLOWED_STATUSES,
    G5_GET_ONLY_ADAPTER_BASE,
    G5_GET_ONLY_ADAPTER_BASE_TREE,
    G5_GET_ONLY_ADAPTER_CANDIDATE,
    G5_GET_ONLY_ADAPTER_HEAD_REF,
    G5_GET_ONLY_ADAPTER_PREVIOUS_BASE,
    G5_GET_ONLY_ADAPTER_PREVIOUS_RESULT,
    G5_GET_ONLY_ADAPTER_STATUS,
    G5_OPERATIONAL_RUNBOOK_ALLOWED_MODES,
    G5_OPERATIONAL_RUNBOOK_ALLOWED_STATUSES,
    G5_OPERATIONAL_RUNBOOK_BASE,
    G5_OPERATIONAL_RUNBOOK_BASE_TREE,
    G5_OPERATIONAL_RUNBOOK_HEAD_REF,
    G5_OPERATIONAL_RUNBOOK_STATUS,
    G5_E1_DEPLOYMENT_STOP,
    G5_E1_HARDENING_ALLOWED_MODES,
    G5_E1_HARDENING_ALLOWED_STATUSES,
    G5_E1_HARDENING_BASE,
    G5_E1_HARDENING_BASE_TREE,
    G5_E1_HARDENING_HEAD_REF,
    G5_E1_HARDENING_STATUS,
    G5_E1_READINESS_STATUS,
    G5_E1_WRANGLER_COMPAT_ALLOWED_MODES,
    G5_E1_WRANGLER_COMPAT_ALLOWED_STATUSES,
    G5_E1_WRANGLER_COMPAT_BASE,
    G5_E1_WRANGLER_COMPAT_BASE_TREE,
    G5_E1_WRANGLER_COMPAT_HEAD_REF,
    G5_E1_WRANGLER_COMPAT_STATUS,
    G5_E1_CREDENTIAL_ATTESTATION,
    G5_E1_DEPLOYMENT_STATUS,
    G5_TRUST_LIVE_REMEDIATION_ALLOWED_MODES,
    G5_TRUST_LIVE_REMEDIATION_ALLOWED_STATUSES,
    G5_TRUST_LIVE_REMEDIATION_BASE,
    G5_TRUST_LIVE_REMEDIATION_BASE_TREE,
    G5_TRUST_LIVE_REMEDIATION_HEAD_REF,
    G5_TRUST_LIVE_REMEDIATION_STATUS,
    G5_TRUST_RUNTIME_POLICY_NAMES,
    G5_GITHUB_RUNTIME_SCHEMA_ALLOWED_MODES,
    G5_GITHUB_RUNTIME_SCHEMA_ALLOWED_STATUSES,
    G5_GITHUB_RUNTIME_SCHEMA_BASE,
    G5_GITHUB_RUNTIME_SCHEMA_BASE_TREE,
    G5_GITHUB_RUNTIME_SCHEMA_E2_STOP,
    G5_GITHUB_RUNTIME_SCHEMA_HEAD_REF,
    G5_GITHUB_RUNTIME_SCHEMA_PR391_CANDIDATE,
    G5_GITHUB_RUNTIME_SCHEMA_STATUS,
    G5_SECURITY_REMEDIATION_ALLOWED_MODES,
    G5_SECURITY_REMEDIATION_ALLOWED_STATUSES,
    G5_SECURITY_REMEDIATION_BASE,
    G5_SECURITY_REMEDIATION_BASE_TREE,
    G5_SECURITY_REMEDIATION_E2_STOP,
    G5_SECURITY_REMEDIATION_HEAD_REF,
    G5_SECURITY_REMEDIATION_PR392_CANDIDATE,
    G5_SECURITY_REMEDIATION_STATUS,
    G5_RESIDUAL_SECURITY_REMEDIATION_ALLOWED_MODES,
    G5_RESIDUAL_SECURITY_REMEDIATION_ALLOWED_STATUSES,
    G5_RESIDUAL_SECURITY_REMEDIATION_BASE,
    G5_RESIDUAL_SECURITY_REMEDIATION_BASE_TREE,
    G5_RESIDUAL_SECURITY_REMEDIATION_HEAD_REF,
    G5_RESIDUAL_SECURITY_REMEDIATION_PR394_COMMITS,
    G5_RESIDUAL_SECURITY_REMEDIATION_PR393_CANDIDATE,
    G5_RESIDUAL_SECURITY_REMEDIATION_STATUS,
    G5_FOLLOWUP_SECURITY_REMEDIATION_ALLOWED_MODES,
    G5_FOLLOWUP_SECURITY_REMEDIATION_ALLOWED_STATUSES,
    G5_FOLLOWUP_SECURITY_REMEDIATION_BASE,
    G5_FOLLOWUP_SECURITY_REMEDIATION_BASE_TREE,
    G5_FOLLOWUP_SECURITY_REMEDIATION_E2_STOP,
    G5_FOLLOWUP_SECURITY_REMEDIATION_HEAD_REF,
    G5_FOLLOWUP_SECURITY_REMEDIATION_STATUS,
    G5_TRUSTED_BOUNDARY_BOOTSTRAP_ALLOWED_MODES,
    G5_TRUSTED_BOUNDARY_BOOTSTRAP_ALLOWED_STATUSES,
    G5_TRUSTED_BOUNDARY_BOOTSTRAP_BASE,
    G5_TRUSTED_BOUNDARY_BOOTSTRAP_BASE_TREE,
    G5_TRUSTED_BOUNDARY_BOOTSTRAP_E2_STOP,
    G5_TRUSTED_BOUNDARY_BOOTSTRAP_HEAD_REF,
    G5_TRUSTED_BOUNDARY_BOOTSTRAP_PR395_CANDIDATE,
    G5_TRUSTED_BOUNDARY_BOOTSTRAP_STATUS,
    G5_TRUSTED_BOUNDARY_HARDENING_ALLOWED_MODES,
    G5_TRUSTED_BOUNDARY_HARDENING_ALLOWED_STATUSES,
    G5_TRUSTED_BOUNDARY_HARDENING_BASE,
    G5_TRUSTED_BOUNDARY_HARDENING_BASE_TREE,
    G5_TRUSTED_BOUNDARY_HARDENING_E2_STOP,
    G5_TRUSTED_BOUNDARY_HARDENING_HEAD_REF,
    G5_TRUSTED_BOUNDARY_HARDENING_PR396_CANDIDATE,
    G5_TRUSTED_BOUNDARY_HARDENING_STATUS,
    G5_TRUSTED_BOUNDARY_PR_N_CHECK_NAME,
    G5_LINK_HARDENING_CLOSURE_ALLOWED_MODES,
    G5_LINK_HARDENING_CLOSURE_ALLOWED_STATUSES,
    G5_LINK_HARDENING_CLOSURE_BASE,
    G5_LINK_HARDENING_CLOSURE_BASE_TREE,
    G5_LINK_HARDENING_CLOSURE_E2_STOP,
    G5_LINK_HARDENING_CLOSURE_HEAD_REF,
    G5_LINK_HARDENING_CLOSURE_PR397_CANDIDATE,
    G5_LINK_HARDENING_CLOSURE_STATUS,
    G5_DEFAULT_BRANCH_TRUSTED_WORKFLOW_ALLOWED_MODES,
    G5_DEFAULT_BRANCH_TRUSTED_WORKFLOW_ALLOWED_STATUSES,
    G5_DEFAULT_BRANCH_TRUSTED_WORKFLOW_BASE,
    G5_DEFAULT_BRANCH_TRUSTED_WORKFLOW_BASE_TREE,
    G5_DEFAULT_BRANCH_TRUSTED_WORKFLOW_E2_STOP,
    G5_DEFAULT_BRANCH_TRUSTED_WORKFLOW_HEAD_REF,
    G5_DEFAULT_BRANCH_TRUSTED_WORKFLOW_PR398_CANDIDATE,
    G5_DEFAULT_BRANCH_TRUSTED_WORKFLOW_STATUS,
    G5_V2_ATTRIBUTION_ALLOWED_MODES,
    G5_V2_ATTRIBUTION_ALLOWED_STATUSES,
    G5_V2_ATTRIBUTION_BASE,
    G5_V2_ATTRIBUTION_BASE_TREE,
    G5_V2_ATTRIBUTION_HEAD_REF,
    G5_V2_POST_MERGE_ALLOWED_MODES,
    G5_V2_POST_MERGE_ALLOWED_STATUSES,
    G5_V2_POST_MERGE_BASE,
    G5_V2_POST_MERGE_BASE_TREE,
    G5_V2_POST_MERGE_CANDIDATE,
    G5_V2_POST_MERGE_HEAD_REF,
    G5_V2_POST_MERGE_PREVIOUS_BASE,
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
    validate_f1010_m3_public_acl_v2_payload,
    validate_f1010_m3_public_acl_v3,
    validate_f1010_m3_public_acl_v3_bound,
    validate_f1010_m3_public_acl_preflight,
    validate_f1010_m3_public_acl_preflight_post_merge,
    validate_f1010_m3_public_acl_private_preflight_v2_payload,
    validate_f1010_m3_public_acl_post_merge_harness,
    validate_f1010_m3_public_acl_v2_evidence,
    validate_f1010_m3_public_acl_final_readiness,
    validate_f1010_h1_ca1_rebaseline,
    validate_g5_production_readonly,
    validate_g5_get_only_adapter,
    validate_g5_operational_runbook,
    validate_g5_e1_hardening,
    validate_g5_e1_wrangler_compat,
    validate_g5_trust_live_remediation,
    validate_g5_github_runtime_schema,
    validate_g5_residual_security_remediation,
    validate_g5_followup_security_remediation,
    validate_g5_trusted_boundary_bootstrap,
    validate_g5_trusted_boundary_hardening,
    validate_g5_link_hardening_closure,
    validate_g5_default_branch_trusted_workflow_registration,
    validate_g5_security_remediation,
    validate_g5_v2_attribution,
    validate_g5_v2_post_merge,
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

        project_state = (root / ".context/estado_del_proyecto.md").read_text(
            encoding="utf-8"
        )
        metadata_plan = (
            root / ".context/operaciones/plan_remediacion_metadata_f10_10.md"
        ).read_text(encoding="utf-8")
        hito_task = (
            root
            / ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md"
        ).read_text(encoding="utf-8")
        project_state_flat = " ".join(project_state.split())
        metadata_plan_flat = " ".join(metadata_plan.split())
        hito_task_flat = " ".join(hito_task.split())
        assert "SUPERSEDED_FOR_HITO_1_TRANSFERRED_TO_H2_CA2" in project_state
        assert "HISTORICAL_NON_PROMOTABLE" in project_state
        assert "REBASELINED_FG2_FG3_OPERATIONAL_REMEDIATION" in project_state
        assert "exclusivamente para blockers CA1 FG2/FG3" in project_state_flat
        assert (
            "No se heredan gates, payloads, readers, ACL, credentials ni bindings"
        ) in project_state_flat
        assert "SUPERSEDED_FOR_HITO_1_TRANSFERRED_TO_H2_CA2" in hito_task
        assert "HISTORICAL_NON_PROMOTABLE" in hito_task
        assert (
            "Ningun gate, payload, reader, ACL, credential, binding, cohorte o "
            "aprobacion de F10.10 se reutiliza"
        ) in hito_task_flat
        assert "SUPERSEDED_FOR_HITO_1_TRANSFERRED_TO_H2_CA2" in metadata_plan
        assert "HISTORICAL_NON_PROMOTABLE" in metadata_plan
        assert "SUPERSEDED_NON_AUTHORIZABLE" in metadata_plan
        assert "no existe gate sucesor F10.10" in metadata_plan_flat

        historical_scope = (
            root / ".context/operaciones/m3_f10_10_scope_por_ambiente_target.md"
        ).read_text(encoding="utf-8")
        historical_reader = (
            root / ".context/operaciones/m3_reader_f10_10_rebaseline.md"
        ).read_text(encoding="utf-8")
        historical_m3 = "\n".join((historical_scope, historical_reader))
        assert "BLOQUEADO_POST_DIAGNOSTIC_STOP" in historical_scope
        assert "No existe ruta M3 Pro autorizable desde este documento" in historical_scope
        assert "evidencia no autoriza Free ni consume gates" in historical_scope
        assert "NO capacidad vigente" in historical_reader
        assert (
            "El payload preflight anterior y su ventana terminada son evidencia historica"
            in historical_reader
        )
        assert "M3_READER_PREFLIGHT_PAYLOAD_READY_GATE_PENDING" not in historical_m3
        assert "M3_PUBLIC_DB_ACL_PRIVATE_PREFLIGHT_CANDIDATE_PENDING_PROMOTION" not in historical_m3
        assert "M3_PUBLIC_DB_ACL_PRIVATE_PREFLIGHT_POST_MERGE_VERIFIED_GATE_PENDING" not in historical_m3
        assert "M3_PUBLIC_DB_ACL_PRIVATE_PREFLIGHT_FREE_V2_PAYLOAD_POST_MERGE_VERIFIED_CONSUMER_BINDING_REQUIRED" in historical_m3
        assert "APPROVE_F10_10_M3_PUBLIC_DB_ACL_PRIVATE_PREFLIGHT_FREE_V2" in historical_m3
        assert "STOP_PUBLIC_DB_ACL_REMEDIATION_REQUIRED" in historical_m3
        assert "CONSUMED_ONCE_PASS" in historical_m3
        assert "CONSUMED_ONCE_FAILED_ROLLBACK_SUPERSEDED" in historical_m3
        for gate in (
            "APPROVE_F10_10_M3_READER_DDL_FREE",
            "APPROVE_F10_10_M3_READER_Q0_FREE",
            "APPROVE_M3_FREE_READONLY",
            "APPROVE_F10_10_M3_READER_TEARDOWN_FREE",
        ):
            assert gate in historical_m3

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

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_f1010_m3_public_acl_v2_payload_accepts_direct_candidate(
        self, require_sha_mock, ancestor_mock, tree_mock, parents_mock,
        delta_mock, context_mock,
    ) -> None:
        head = "e" * 40
        tree_mock.return_value = F1010_M3_PUBLIC_ACL_V2_PAYLOAD_BASE_TREE
        parents_mock.return_value = [F1010_M3_PUBLIC_ACL_V2_PAYLOAD_BASE]

        validate_f1010_m3_public_acl_v2_payload(
            Path("."), F1010_M3_PUBLIC_ACL_V2_PAYLOAD_BASE, head, "pull_request"
        )

        delta_mock.assert_called_once_with(
            Path("."), F1010_M3_PUBLIC_ACL_V2_PAYLOAD_BASE, head,
            F1010_M3_PUBLIC_ACL_V2_PAYLOAD_ALLOWED_STATUSES,
            F1010_M3_PUBLIC_ACL_V2_PAYLOAD_ALLOWED_MODES,
        )
        context_mock.assert_called_once_with(Path("."), 56, 377)

    def test_f1010_m3_public_acl_v2_payload_contract(self) -> None:
        path = Path(__file__).resolve().parents[1] / ".context/operaciones/m3_public_db_acl_diagnostic_free_v2_payload_2026_08_12.json"
        raw = path.read_bytes()
        payload = json.loads(raw)

        self.assertEqual(raw, (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii"))
        self.assertEqual(payload["schema"], "f10.10-m3-public-db-acl-diagnostic-payload-v2")
        self.assertEqual(payload["gate"], "APPROVE_F10_10_M3_PUBLIC_DB_ACL_DIAGNOSTIC_FREE_V2")
        self.assertEqual(payload["candidate_commit"], F1010_M3_PUBLIC_ACL_V2_PAYLOAD_BASE)
        self.assertEqual(payload["candidate_tree"], F1010_M3_PUBLIC_ACL_V2_PAYLOAD_BASE_TREE)
        self.assertEqual(payload["candidate_head_commit"], "25bb9e0cef87a95f5b2a4c03e59b2aa525938f67")
        self.assertEqual(payload["candidate_parent"], "d6f2570816b6a69bf5e5aad5e37a6dd004e0e0d2")
        self.assertEqual(payload["candidate_pr"], 365)
        self.assertEqual(payload["envelope_digest"], "sha256:cc99a97ce134548ac21dc040ed9ed85e9777d1c724daa0313a9003aad83980fd")
        self.assertEqual(payload["post_merge_checks"], [
            {"conclusion": "success", "name": "Security Audit Gate", "run_id": 31613677711},
            {"conclusion": "success", "name": "F9.7 Public Access, Trigger Retirement, and Security Hold PostgreSQL 17 Contract", "run_id": 31613677704},
        ])
        self.assertEqual(payload["gate_v1_status"], "CONSUMED_ONCE_STOP_CANDIDATE_BINDING_PENDING")
        self.assertEqual(payload["gate_v2_status"], "PENDING_HUMAN_APPROVAL_NOT_EXECUTED")
        self.assertEqual(payload["transaction"], "REPEATABLE_READ_READ_ONLY")
        self.assertEqual(payload["expected_rows"], 1)
        self.assertEqual(payload["max_calls"], 1)
        for field in ("automatic_continuation", "ddl_allowed", "dml_allowed", "rpc_allowed", "password_allowed", "pro_allowed", "q0_allowed"):
            self.assertFalse(payload[field])

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_f1010_m3_public_acl_v3_accepts_direct_candidate(
        self, require_sha_mock, ancestor_mock, tree_mock, parents_mock,
        delta_mock, context_mock,
    ) -> None:
        head = "f" * 40
        tree_mock.return_value = F1010_M3_PUBLIC_ACL_V3_BASE_TREE
        parents_mock.return_value = [F1010_M3_PUBLIC_ACL_V3_BASE]
        validate_f1010_m3_public_acl_v3(Path("."), F1010_M3_PUBLIC_ACL_V3_BASE, head, "pull_request")
        delta_mock.assert_called_once_with(
            Path("."), F1010_M3_PUBLIC_ACL_V3_BASE, head,
            F1010_M3_PUBLIC_ACL_V3_ALLOWED_STATUSES,
            F1010_M3_PUBLIC_ACL_V3_ALLOWED_MODES,
        )
        context_mock.assert_called_once_with(Path("."), 56, 377)

    def test_f1010_m3_public_acl_v3_payload_contract(self) -> None:
        root = Path(__file__).resolve().parents[1]
        raw = (root / ".context/operaciones/m3_public_db_acl_diagnostic_free_v3_payload_2026_08_12.json").read_bytes()
        payload = json.loads(raw)
        self.assertEqual(raw, (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii"))
        self.assertEqual(payload["schema"], "f10.10-m3-public-db-acl-diagnostic-payload-v3")
        self.assertEqual(payload["gate"], "APPROVE_F10_10_M3_PUBLIC_DB_ACL_DIAGNOSTIC_FREE_V3")
        self.assertEqual(payload["authority_commit"], F1010_M3_PUBLIC_ACL_V3_BASE)
        self.assertEqual(payload["authority_tree"], F1010_M3_PUBLIC_ACL_V3_BASE_TREE)
        self.assertEqual(payload["authority_head_commit"], "c9356dea7c5c8b0574244c9ca44ec1597447aca4")
        self.assertEqual(payload["authority_pr"], 366)
        self.assertEqual(payload["envelope_digest"], "sha256:82a5848a8ac5958aa781424a436687117f1c39b7dc07f686993b0765bf110a6d")
        self.assertEqual(payload["gate_v1_status"], "CONSUMED_ONCE_STOP_CANDIDATE_BINDING_PENDING")
        self.assertEqual(payload["gate_v2_status"], "SUPERSEDED_NOT_EXECUTED")
        self.assertEqual(payload["gate_v3_status"], "PENDING_HUMAN_APPROVAL_NOT_EXECUTED")
        self.assertEqual(payload["postgres_major_required"], 17)
        self.assertIsNone(payload["candidate_merge_commit"])
        self.assertIsNone(payload["candidate_tree"])
        for field in ("automatic_continuation", "ddl_allowed", "dml_allowed", "rpc_allowed", "password_allowed", "pro_allowed", "q0_allowed"):
            self.assertFalse(payload[field])

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_f1010_m3_public_acl_v3_bound_accepts_direct_candidate(
        self, require_sha_mock, ancestor_mock, tree_mock, parents_mock,
        delta_mock, context_mock,
    ) -> None:
        head = "a" * 40
        tree_mock.return_value = F1010_M3_PUBLIC_ACL_V3_BOUND_BASE_TREE
        parents_mock.return_value = [F1010_M3_PUBLIC_ACL_V3_BOUND_BASE]
        validate_f1010_m3_public_acl_v3_bound(
            Path("."), F1010_M3_PUBLIC_ACL_V3_BOUND_BASE, head, "pull_request"
        )
        delta_mock.assert_called_once_with(
            Path("."), F1010_M3_PUBLIC_ACL_V3_BOUND_BASE, head,
            F1010_M3_PUBLIC_ACL_V3_BOUND_ALLOWED_STATUSES,
            F1010_M3_PUBLIC_ACL_V3_BOUND_ALLOWED_MODES,
        )
        context_mock.assert_called_once_with(Path("."), 56, 377)

    def test_f1010_m3_public_acl_v3_execution_binding_contract(self) -> None:
        root = Path(__file__).resolve().parents[1]
        path = root / ".context/operaciones/m3_public_db_acl_diagnostic_free_v3_execution_binding_2026_08_12.json"
        raw = path.read_bytes()
        binding = json.loads(raw)
        self.assertEqual(raw, (json.dumps(binding, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii"))
        self.assertEqual(binding["schema"], "f10.10-m3-public-db-acl-diagnostic-execution-binding-v1")
        self.assertEqual(binding["gate"], "APPROVE_F10_10_M3_PUBLIC_DB_ACL_DIAGNOSTIC_FREE_V3_BOUND")
        self.assertEqual(binding["execution_candidate_merge_commit"], F1010_M3_PUBLIC_ACL_V3_BOUND_BASE)
        self.assertEqual(binding["execution_candidate_tree"], F1010_M3_PUBLIC_ACL_V3_BOUND_BASE_TREE)
        self.assertEqual(binding["execution_candidate_head_commit"], "4de7816f6b73405ec55bff3d257c5cc72e137699")
        self.assertEqual(binding["execution_candidate_parent"], "8e6d569dcc2d91479e48172bf18f3024571b95ac")
        self.assertEqual(binding["execution_candidate_pr"], 367)
        self.assertEqual(binding["payload_git_blob_sha1"], "d76b75a4876e600d1a7203c24456ab34ad49c1af")
        self.assertEqual(binding["payload_content_sha256"], "sha256:c3a9279ad789b7809af030f3b68ab8e5491aef4789cb89adcd7e433caf3ece2c")
        self.assertEqual(binding["envelope_digest"], "sha256:82a5848a8ac5958aa781424a436687117f1c39b7dc07f686993b0765bf110a6d")
        self.assertEqual(binding["max_execute_sql_calls"], 1)
        self.assertEqual(binding["expected_rows"], 1)
        self.assertTrue(binding["self_binding_forbidden"])
        forbidden = {"binding_merge_commit", "binding_tree", "binding_digest", "approved", "executed"}
        self.assertTrue(forbidden.isdisjoint(binding))
        for field in ("automatic_continuation", "automatic_retry", "ddl_allowed", "dml_allowed", "rpc_allowed", "password_allowed", "pro_allowed", "q0_allowed"):
            self.assertFalse(binding[field])

    def test_f1010_m3_public_acl_preflight_accepts_linear_candidate(self) -> None:
        repo = self.make_repo()
        for path in F1010_M3_PUBLIC_ACL_PREFLIGHT_ALLOWED_STATUSES:
            target = repo / path
            target.parent.mkdir(parents=True, exist_ok=True)
            if F1010_M3_PUBLIC_ACL_PREFLIGHT_ALLOWED_STATUSES[path] == "M":
                target.write_text("before\n", encoding="utf-8")
        base = self.commit(repo, "base")
        paths = list(F1010_M3_PUBLIC_ACL_PREFLIGHT_ALLOWED_STATUSES.items())
        for path, status in paths[:8]:
            target = repo / path
            target.write_text("after\n" if status == "M" else "new\n", encoding="utf-8")
        self.commit(repo, "candidate part one")
        for path, status in paths[8:]:
            target = repo / path
            target.write_text("after\n" if status == "M" else "new\n", encoding="utf-8")
        head = self.commit(repo, "candidate part two")

        with mock.patch(
            "scripts.security.f109_boundary.F1010_M3_PUBLIC_ACL_PREFLIGHT_BASE", base,
        ), mock.patch(
            "scripts.security.f109_boundary.F1010_M3_PUBLIC_ACL_PREFLIGHT_BASE_TREE",
            run(repo, "rev-parse", f"{base}^{{tree}}"),
        ), mock.patch("scripts.security.f109_boundary.validate_context_graph") as context_mock:
            validate_f1010_m3_public_acl_preflight(repo, base, head, "pull_request")

        context_mock.assert_called_once_with(repo, 57, 377)

    def test_f1010_m3_public_acl_preflight_rejects_extra_path(self) -> None:
        repo = self.make_repo()
        (repo / "README.md").write_text("base\n", encoding="utf-8")
        base = self.commit(repo, "base")
        (repo / "unexpected.txt").write_text("unexpected\n", encoding="utf-8")
        head = self.commit(repo, "expanded candidate")

        with mock.patch(
            "scripts.security.f109_boundary.F1010_M3_PUBLIC_ACL_PREFLIGHT_BASE", base,
        ), mock.patch(
            "scripts.security.f109_boundary.F1010_M3_PUBLIC_ACL_PREFLIGHT_BASE_TREE",
            run(repo, "rev-parse", f"{base}^{{tree}}"),
        ), self.assertRaises(BoundaryError):
            validate_f1010_m3_public_acl_preflight(repo, base, head, "pull_request")

    def test_f1010_m3_public_acl_preflight_rejects_merge_history(self) -> None:
        repo = self.make_repo()
        (repo / "README.md").write_text("base\n", encoding="utf-8")
        base = self.commit(repo, "base")
        run(repo, "switch", "-c", "side")
        (repo / "side.txt").write_text("side\n", encoding="utf-8")
        self.commit(repo, "side")
        run(repo, "switch", "-c", "candidate", base)
        (repo / "candidate.txt").write_text("candidate\n", encoding="utf-8")
        self.commit(repo, "candidate")
        run(repo, "merge", "--no-ff", "side", "-m", "merge side")
        head = run(repo, "rev-parse", "HEAD")

        with mock.patch(
            "scripts.security.f109_boundary.F1010_M3_PUBLIC_ACL_PREFLIGHT_BASE", base,
        ), mock.patch(
            "scripts.security.f109_boundary.F1010_M3_PUBLIC_ACL_PREFLIGHT_BASE_TREE",
            run(repo, "rev-parse", f"{base}^{{tree}}"),
        ), self.assertRaises(BoundaryError):
            validate_f1010_m3_public_acl_preflight(repo, base, head, "pull_request")

    @mock.patch("scripts.security.f109_boundary.changed_statuses")
    @mock.patch("scripts.security.f109_boundary.parse_args")
    def test_cli_rejects_f1010_public_acl_preflight_paths_from_wrong_branch(
        self, parse_args_mock, changed_statuses_mock,
    ) -> None:
        parse_args_mock.return_value = self.cli_args(
            head_ref="wrong-branch",
            base_ref="desarrollo",
            base_sha=F1010_M3_PUBLIC_ACL_PREFLIGHT_BASE,
        )
        changed_statuses_mock.return_value = {
            "tests/sql/run_f10_10_m3_public_db_acl_preflight_postgres17.sh": "A",
        }
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            self.assertEqual(main(), 1)
        self.assertIn("require the protected preflight branch", stderr.getvalue())

    def test_detect_mode_selects_f1010_public_acl_preflight(self) -> None:
        self.assertEqual(
            detect_mode(
                "pull_request", "desarrollo", F1010_M3_PUBLIC_ACL_PREFLIGHT_HEAD_REF,
                F1010_M3_PUBLIC_ACL_PREFLIGHT_BASE,
            ),
            "f1010_m3_public_acl_preflight",
        )

    def test_f1010_public_acl_preflight_post_merge_accepts_direct_candidate(self) -> None:
        repo = self.make_repo()
        for path, status in F1010_M3_PUBLIC_ACL_PREFLIGHT_POST_MERGE_ALLOWED_STATUSES.items():
            target = repo / path
            target.parent.mkdir(parents=True, exist_ok=True)
            if status == "M":
                target.write_text("before\n", encoding="utf-8")
        base = self.commit(repo, "base")
        for path, status in F1010_M3_PUBLIC_ACL_PREFLIGHT_POST_MERGE_ALLOWED_STATUSES.items():
            target = repo / path
            target.write_text("after\n" if status == "M" else "new\n", encoding="utf-8")
        head = self.commit(repo, "post-merge evidence")

        with mock.patch(
            "scripts.security.f109_boundary.F1010_M3_PUBLIC_ACL_PREFLIGHT_POST_MERGE_BASE",
            base,
        ), mock.patch(
            "scripts.security.f109_boundary.F1010_M3_PUBLIC_ACL_PREFLIGHT_POST_MERGE_BASE_TREE",
            run(repo, "rev-parse", f"{base}^{{tree}}"),
        ), mock.patch("scripts.security.f109_boundary.validate_context_graph") as context_mock:
            validate_f1010_m3_public_acl_preflight_post_merge(
                repo, base, head, "pull_request"
            )

        context_mock.assert_called_once_with(repo, 58, 377)

    def test_f1010_public_acl_preflight_post_merge_rejects_extra_path(self) -> None:
        repo = self.make_repo()
        (repo / "README.md").write_text("base\n", encoding="utf-8")
        base = self.commit(repo, "base")
        (repo / "unexpected.txt").write_text("unexpected\n", encoding="utf-8")
        head = self.commit(repo, "expanded evidence")

        with mock.patch(
            "scripts.security.f109_boundary.F1010_M3_PUBLIC_ACL_PREFLIGHT_POST_MERGE_BASE",
            base,
        ), mock.patch(
            "scripts.security.f109_boundary.F1010_M3_PUBLIC_ACL_PREFLIGHT_POST_MERGE_BASE_TREE",
            run(repo, "rev-parse", f"{base}^{{tree}}"),
        ), self.assertRaises(BoundaryError):
            validate_f1010_m3_public_acl_preflight_post_merge(
                repo, base, head, "pull_request"
            )

    def test_f1010_public_acl_preflight_post_merge_accepts_protected_push(self) -> None:
        repo = self.make_repo()
        for path, status in F1010_M3_PUBLIC_ACL_PREFLIGHT_POST_MERGE_ALLOWED_STATUSES.items():
            target = repo / path
            target.parent.mkdir(parents=True, exist_ok=True)
            if status == "M":
                target.write_text("before\n", encoding="utf-8")
        base = self.commit(repo, "base")
        run(repo, "switch", "-c", "candidate")
        for path, status in F1010_M3_PUBLIC_ACL_PREFLIGHT_POST_MERGE_ALLOWED_STATUSES.items():
            target = repo / path
            target.write_text("after\n" if status == "M" else "new\n", encoding="utf-8")
        candidate = self.commit(repo, "post-merge evidence")
        run(repo, "switch", "master")
        run(repo, "merge", "--no-ff", "candidate", "-m", "protected merge")
        merge = run(repo, "rev-parse", "HEAD")

        with mock.patch(
            "scripts.security.f109_boundary.F1010_M3_PUBLIC_ACL_PREFLIGHT_POST_MERGE_BASE",
            base,
        ), mock.patch(
            "scripts.security.f109_boundary.F1010_M3_PUBLIC_ACL_PREFLIGHT_POST_MERGE_BASE_TREE",
            run(repo, "rev-parse", f"{base}^{{tree}}"),
        ), mock.patch("scripts.security.f109_boundary.validate_context_graph"):
            validate_f1010_m3_public_acl_preflight_post_merge(
                repo, base, merge, "push"
            )

        self.assertEqual(run(repo, "rev-parse", f"{merge}^2"), candidate)

    def test_f1010_public_acl_preflight_post_merge_rejects_push_tree_drift(self) -> None:
        base = "1" * 40
        candidate = "2" * 40
        merge = "3" * 40
        with mock.patch(
            "scripts.security.f109_boundary.F1010_M3_PUBLIC_ACL_PREFLIGHT_POST_MERGE_BASE",
            base,
        ), mock.patch(
            "scripts.security.f109_boundary.F1010_M3_PUBLIC_ACL_PREFLIGHT_POST_MERGE_BASE_TREE",
            "4" * 40,
        ), mock.patch("scripts.security.f109_boundary.require_sha"), mock.patch(
            "scripts.security.f109_boundary.commit_tree",
            side_effect=lambda _repo, commit: {
                base: "4" * 40, candidate: "5" * 40, merge: "6" * 40,
            }[commit],
        ), mock.patch(
            "scripts.security.f109_boundary.is_ancestor", return_value=True,
        ), mock.patch(
            "scripts.security.f109_boundary.commit_parents",
            return_value=[base, candidate],
        ), self.assertRaises(BoundaryError):
            validate_f1010_m3_public_acl_preflight_post_merge(
                Path("."), base, merge, "push"
            )

    def test_f1010_public_acl_preflight_post_merge_rejects_wrong_baseline(self) -> None:
        with self.assertRaises(BoundaryError):
            validate_f1010_m3_public_acl_preflight_post_merge(
                Path("."), "1" * 40, "2" * 40, "pull_request"
            )

    def test_detect_mode_selects_f1010_public_acl_preflight_post_merge(self) -> None:
        self.assertEqual(
            detect_mode(
                "pull_request",
                "desarrollo",
                F1010_M3_PUBLIC_ACL_PREFLIGHT_POST_MERGE_HEAD_REF,
                F1010_M3_PUBLIC_ACL_PREFLIGHT_POST_MERGE_BASE,
            ),
            "f1010_m3_public_acl_preflight_post_merge",
        )

    def test_f1010_private_preflight_v2_payload_contract(self) -> None:
        root = Path(__file__).resolve().parents[1]
        path = root / ".context/operaciones/m3_public_db_acl_private_preflight_free_v2_payload_2026_08_13.json"
        raw = path.read_bytes()
        payload = json.loads(raw)
        assert raw == json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii") + b"\n"
        assert set(payload) == {
            "application_rows_allowed", "authority_commit", "authority_head_commit",
            "authority_parent", "authority_pr", "authority_tree", "automatic_continuation",
            "automatic_retry", "candidate_merge_commit", "candidate_tree",
            "collector_result_schema", "collector_sql_digest", "database_classes",
            "ddl_allowed", "dml_allowed", "expected_rows", "gate",
            "managed_dependency_attestation_schema", "max_calls",
            "observed_transport_schema", "password_allowed", "post_merge_checks",
            "postgres_major_required", "private_artifact_schema",
            "private_dependency_attestation_path", "private_env_path",
            "private_result_path", "private_target_binding_path", "pro_allowed",
            "q0_allowed", "reader_required", "remediation_allowed", "remote_read_scope",
            "rpc_allowed", "sanitized_manifest_schema", "schema", "status",
            "target_alias", "target_binding_schema", "transaction",
        }
        assert payload["schema"] == "f10.10-m3-public-db-acl-private-preflight-payload-v2"
        assert payload["gate"] == "APPROVE_F10_10_M3_PUBLIC_DB_ACL_PRIVATE_PREFLIGHT_FREE_V2"
        assert payload["authority_commit"] == F1010_M3_PUBLIC_ACL_PRIVATE_PREFLIGHT_V2_PAYLOAD_BASE
        assert payload["authority_tree"] == F1010_M3_PUBLIC_ACL_PRIVATE_PREFLIGHT_V2_PAYLOAD_BASE_TREE
        assert payload["candidate_merge_commit"] is None
        assert payload["candidate_tree"] is None
        assert payload["max_calls"] == 1 and payload["expected_rows"] == 1
        assert payload["transaction"] == "REPEATABLE_READ_READ_ONLY"
        for field in (
            "automatic_continuation", "automatic_retry", "ddl_allowed", "dml_allowed",
            "password_allowed", "pro_allowed", "q0_allowed", "reader_required",
            "remediation_allowed", "rpc_allowed",
        ):
            assert payload[field] is False
        assert payload["collector_sql_digest"] == "sha256:c109752ce46d3528920527ea034c929ff4e4e6b477576c1fa7514b3fe26f3d35"
        assert payload["target_binding_schema"] == "f10.10-m3-target-binding-v2"
        assert payload["observed_transport_schema"] == "f10.10-m3-observed-transport-v2"
        assert payload["status"] == "PENDING_CANONICAL_TARGET_AND_OBSERVED_TRANSPORT_BINDING_HUMAN_APPROVAL_NOT_EXECUTED"

    def test_f1010_private_preflight_v2_payload_accepts_direct_candidate(self) -> None:
        repo = self.make_repo()
        for path, status in F1010_M3_PUBLIC_ACL_PRIVATE_PREFLIGHT_V2_PAYLOAD_ALLOWED_STATUSES.items():
            target = repo / path
            target.parent.mkdir(parents=True, exist_ok=True)
            if status == "M":
                target.write_text("before\n", encoding="utf-8")
        base = self.commit(repo, "base")
        base_tree = run(repo, "rev-parse", f"{base}^{{tree}}")
        for path, status in F1010_M3_PUBLIC_ACL_PRIVATE_PREFLIGHT_V2_PAYLOAD_ALLOWED_STATUSES.items():
            target = repo / path
            if path.endswith("private_preflight_free_v2_payload_2026_08_13.json"):
                payload = json.loads(
                    (Path(__file__).resolve().parents[1] / path).read_text(encoding="ascii")
                )
                payload["authority_commit"] = base
                payload["authority_tree"] = base_tree
                target.write_text(
                    json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n",
                    encoding="ascii",
                )
            else:
                target.write_text("after\n" if status == "M" else "new\n", encoding="utf-8")
        head = self.commit(repo, "payload")
        with mock.patch(
            "scripts.security.f109_boundary.F1010_M3_PUBLIC_ACL_PRIVATE_PREFLIGHT_V2_PAYLOAD_BASE",
            base,
        ), mock.patch(
            "scripts.security.f109_boundary.F1010_M3_PUBLIC_ACL_PRIVATE_PREFLIGHT_V2_PAYLOAD_BASE_TREE",
            base_tree,
        ), mock.patch("scripts.security.f109_boundary.validate_context_graph") as context_mock:
            validate_f1010_m3_public_acl_private_preflight_v2_payload(repo, base, head, "pull_request")
        context_mock.assert_called_once_with(repo, 58, 377)

    def test_f1010_private_preflight_v2_payload_rejects_extra_path(self) -> None:
        repo = self.make_repo()
        (repo / "README.md").write_text("base\n", encoding="utf-8")
        base = self.commit(repo, "base")
        (repo / "unexpected.txt").write_text("unexpected\n", encoding="utf-8")
        head = self.commit(repo, "expanded")
        with mock.patch(
            "scripts.security.f109_boundary.F1010_M3_PUBLIC_ACL_PRIVATE_PREFLIGHT_V2_PAYLOAD_BASE",
            base,
        ), mock.patch(
            "scripts.security.f109_boundary.F1010_M3_PUBLIC_ACL_PRIVATE_PREFLIGHT_V2_PAYLOAD_BASE_TREE",
            run(repo, "rev-parse", f"{base}^{{tree}}"),
        ), self.assertRaises(BoundaryError):
            validate_f1010_m3_public_acl_private_preflight_v2_payload(repo, base, head, "pull_request")

    def test_detect_mode_selects_f1010_private_preflight_v2_payload(self) -> None:
        self.assertEqual(
            detect_mode(
                "pull_request", "desarrollo",
                F1010_M3_PUBLIC_ACL_PRIVATE_PREFLIGHT_V2_PAYLOAD_HEAD_REF,
                F1010_M3_PUBLIC_ACL_PRIVATE_PREFLIGHT_V2_PAYLOAD_BASE,
            ),
            "f1010_m3_public_acl_private_preflight_v2_payload",
        )

    def test_f1010_public_acl_post_merge_harness_accepts_exact_candidate(self) -> None:
        repo = self.make_repo()
        for path in F1010_M3_PUBLIC_ACL_POST_MERGE_HARNESS_ALLOWED_STATUSES:
            target = repo / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("before\n", encoding="utf-8")
        base = self.commit(repo, "base")
        base_tree = run(repo, "rev-parse", f"{base}^{{tree}}")
        for path in F1010_M3_PUBLIC_ACL_POST_MERGE_HARNESS_ALLOWED_STATUSES:
            (repo / path).write_text("after\n", encoding="utf-8")
        head = self.commit(repo, "harness")
        with mock.patch(
            "scripts.security.f109_boundary.F1010_M3_PUBLIC_ACL_POST_MERGE_HARNESS_BASE",
            base,
        ), mock.patch(
            "scripts.security.f109_boundary.F1010_M3_PUBLIC_ACL_POST_MERGE_HARNESS_BASE_TREE",
            base_tree,
        ):
            validate_f1010_m3_public_acl_post_merge_harness(repo, base, head, "pull_request")

    def test_f1010_public_acl_post_merge_harness_rejects_extra_path(self) -> None:
        repo = self.make_repo()
        (repo / "README.md").write_text("base\n", encoding="utf-8")
        base = self.commit(repo, "base")
        (repo / "unexpected.txt").write_text("unexpected\n", encoding="utf-8")
        head = self.commit(repo, "expanded")
        with mock.patch(
            "scripts.security.f109_boundary.F1010_M3_PUBLIC_ACL_POST_MERGE_HARNESS_BASE",
            base,
        ), mock.patch(
            "scripts.security.f109_boundary.F1010_M3_PUBLIC_ACL_POST_MERGE_HARNESS_BASE_TREE",
            run(repo, "rev-parse", f"{base}^{{tree}}"),
        ), self.assertRaises(BoundaryError):
            validate_f1010_m3_public_acl_post_merge_harness(repo, base, head, "pull_request")

    def test_detect_mode_selects_f1010_public_acl_post_merge_harness(self) -> None:
        self.assertEqual(
            detect_mode(
                "pull_request", "desarrollo",
                F1010_M3_PUBLIC_ACL_POST_MERGE_HARNESS_HEAD_REF,
                F1010_M3_PUBLIC_ACL_POST_MERGE_HARNESS_BASE,
            ),
            "f1010_m3_public_acl_post_merge_harness",
        )

    def test_f1010_public_acl_v2_evidence_accepts_exact_candidate(self) -> None:
        repo = self.make_repo()
        source_root = Path(__file__).resolve().parents[1]
        for path, status in F1010_M3_PUBLIC_ACL_V2_EVIDENCE_ALLOWED_STATUSES.items():
            target = repo / path
            target.parent.mkdir(parents=True, exist_ok=True)
            if status == "M":
                target.write_text("before\n", encoding="utf-8")
        base = self.commit(repo, "base")
        base_tree = run(repo, "rev-parse", f"{base}^{{tree}}")
        for path, status in F1010_M3_PUBLIC_ACL_V2_EVIDENCE_ALLOWED_STATUSES.items():
            target = repo / path
            if path.endswith("m3_public_db_acl_private_preflight_v2_payload_post_merge_evidence_2026_08_13.md"):
                target.write_text((source_root / path).read_text(encoding="utf-8"), encoding="utf-8")
            else:
                target.write_text("after\n" if status == "M" else "new\n", encoding="utf-8")
        head = self.commit(repo, "evidence")
        with mock.patch(
            "scripts.security.f109_boundary.F1010_M3_PUBLIC_ACL_V2_EVIDENCE_BASE", base,
        ), mock.patch(
            "scripts.security.f109_boundary.F1010_M3_PUBLIC_ACL_V2_EVIDENCE_BASE_TREE", base_tree,
        ), mock.patch("scripts.security.f109_boundary.validate_context_graph") as context_mock:
            validate_f1010_m3_public_acl_v2_evidence(repo, base, head, "pull_request")
        context_mock.assert_called_once_with(repo, 59, 378)

    def test_f1010_public_acl_v2_evidence_rejects_extra_path(self) -> None:
        repo = self.make_repo()
        (repo / "README.md").write_text("base\n", encoding="utf-8")
        base = self.commit(repo, "base")
        (repo / "unexpected.txt").write_text("unexpected\n", encoding="utf-8")
        head = self.commit(repo, "expanded")
        with mock.patch(
            "scripts.security.f109_boundary.F1010_M3_PUBLIC_ACL_V2_EVIDENCE_BASE", base,
        ), mock.patch(
            "scripts.security.f109_boundary.F1010_M3_PUBLIC_ACL_V2_EVIDENCE_BASE_TREE",
            run(repo, "rev-parse", f"{base}^{{tree}}"),
        ), self.assertRaises(BoundaryError):
            validate_f1010_m3_public_acl_v2_evidence(repo, base, head, "pull_request")

    def test_detect_mode_selects_f1010_public_acl_v2_evidence(self) -> None:
        self.assertEqual(
            detect_mode(
                "pull_request", "desarrollo",
                F1010_M3_PUBLIC_ACL_V2_EVIDENCE_HEAD_REF,
                F1010_M3_PUBLIC_ACL_V2_EVIDENCE_BASE,
            ),
            "f1010_m3_public_acl_v2_evidence",
        )

    def test_f1010_public_acl_v2_evidence_accepts_protected_merge(self) -> None:
        repo = self.make_repo()
        source_root = Path(__file__).resolve().parents[1]
        for path, status in F1010_M3_PUBLIC_ACL_V2_EVIDENCE_ALLOWED_STATUSES.items():
            target = repo / path
            target.parent.mkdir(parents=True, exist_ok=True)
            if status == "M":
                target.write_text("before\n", encoding="utf-8")
        base = self.commit(repo, "base")
        base_tree = run(repo, "rev-parse", f"{base}^{{tree}}")
        run(repo, "checkout", "-b", "candidate")
        for path, status in F1010_M3_PUBLIC_ACL_V2_EVIDENCE_ALLOWED_STATUSES.items():
            target = repo / path
            if path.endswith("m3_public_db_acl_private_preflight_v2_payload_post_merge_evidence_2026_08_13.md"):
                target.write_text((source_root / path).read_text(encoding="utf-8"), encoding="utf-8")
            else:
                target.write_text("after\n" if status == "M" else "new\n", encoding="utf-8")
        candidate = self.commit(repo, "candidate")
        run(repo, "checkout", "master")
        run(repo, "merge", "--no-ff", candidate, "-m", "merge")
        merge = run(repo, "rev-parse", "HEAD")
        with mock.patch(
            "scripts.security.f109_boundary.F1010_M3_PUBLIC_ACL_V2_EVIDENCE_BASE", base,
        ), mock.patch(
            "scripts.security.f109_boundary.F1010_M3_PUBLIC_ACL_V2_EVIDENCE_BASE_TREE", base_tree,
        ), mock.patch("scripts.security.f109_boundary.validate_context_graph"):
            validate_f1010_m3_public_acl_v2_evidence(repo, base, merge, "push")

    def test_f1010_public_acl_v2_evidence_rejects_non_merge_push(self) -> None:
        repo = self.make_repo()
        (repo / "README.md").write_text("base\n", encoding="utf-8")
        base = self.commit(repo, "base")
        (repo / "README.md").write_text("head\n", encoding="utf-8")
        head = self.commit(repo, "head")
        with mock.patch(
            "scripts.security.f109_boundary.F1010_M3_PUBLIC_ACL_V2_EVIDENCE_BASE", base,
        ), mock.patch(
            "scripts.security.f109_boundary.F1010_M3_PUBLIC_ACL_V2_EVIDENCE_BASE_TREE",
            run(repo, "rev-parse", f"{base}^{{tree}}"),
        ), self.assertRaises(BoundaryError):
            validate_f1010_m3_public_acl_v2_evidence(repo, base, head, "push")

    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_f1010_public_acl_v2_evidence_rejects_merge_tree_drift(
        self, require_sha_mock, is_ancestor_mock, commit_tree_mock, commit_parents_mock,
    ) -> None:
        base = F1010_M3_PUBLIC_ACL_V2_EVIDENCE_BASE
        candidate = "c" * 40
        merge = "d" * 40
        commit_parents_mock.return_value = [base, candidate]
        commit_tree_mock.side_effect = lambda _repo, commit: {
            base: "da92dfa4baf89cc04bc2a67c97f678f3273e152b",
            candidate: "a" * 40,
            merge: "b" * 40,
        }[commit]
        with self.assertRaises(BoundaryError):
            validate_f1010_m3_public_acl_v2_evidence(Path("."), base, merge, "push")

    def test_f1010_public_acl_final_readiness_accepts_exact_candidate(self) -> None:
        repo = self.make_repo()
        source_root = Path(__file__).resolve().parents[1]
        for path, status in F1010_M3_PUBLIC_ACL_FINAL_READINESS_ALLOWED_STATUSES.items():
            target = repo / path
            target.parent.mkdir(parents=True, exist_ok=True)
            if status == "M":
                target.write_text("before\n", encoding="utf-8")
        base = self.commit(repo, "base")
        base_tree = run(repo, "rev-parse", f"{base}^{{tree}}")
        for path in F1010_M3_PUBLIC_ACL_FINAL_READINESS_ALLOWED_STATUSES:
            target = repo / path
            target.write_text((source_root / path).read_text(encoding="utf-8"), encoding="utf-8")
        head = self.commit(repo, "readiness")
        with mock.patch(
            "scripts.security.f109_boundary.F1010_M3_PUBLIC_ACL_FINAL_READINESS_BASE", base,
        ), mock.patch(
            "scripts.security.f109_boundary.F1010_M3_PUBLIC_ACL_FINAL_READINESS_BASE_TREE", base_tree,
        ), mock.patch("scripts.security.f109_boundary.validate_context_graph") as context_mock:
            validate_f1010_m3_public_acl_final_readiness(repo, base, head, "pull_request")
        context_mock.assert_called_once_with(repo, 60, 378)

    def test_f1010_public_acl_final_readiness_rejects_extra_path(self) -> None:
        repo = self.make_repo()
        (repo / "README.md").write_text("base\n", encoding="utf-8")
        base = self.commit(repo, "base")
        (repo / "unexpected.txt").write_text("unexpected\n", encoding="utf-8")
        head = self.commit(repo, "expanded")
        with mock.patch(
            "scripts.security.f109_boundary.F1010_M3_PUBLIC_ACL_FINAL_READINESS_BASE", base,
        ), mock.patch(
            "scripts.security.f109_boundary.F1010_M3_PUBLIC_ACL_FINAL_READINESS_BASE_TREE",
            run(repo, "rev-parse", f"{base}^{{tree}}"),
        ), self.assertRaises(BoundaryError):
            validate_f1010_m3_public_acl_final_readiness(repo, base, head, "pull_request")

    def test_detect_mode_selects_f1010_public_acl_final_readiness(self) -> None:
        self.assertEqual(
            detect_mode(
                "pull_request", "desarrollo",
                F1010_M3_PUBLIC_ACL_FINAL_READINESS_HEAD_REF,
                F1010_M3_PUBLIC_ACL_FINAL_READINESS_BASE,
            ),
            "f1010_m3_public_acl_final_readiness",
        )

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_f1010_h1_ca1_rebaseline_accepts_exact_candidate(
        self, require_sha_mock, ancestor_mock, tree_mock, delta_mock, context_mock,
    ) -> None:
        head = "a" * 40
        tree_mock.return_value = F1010_H1_CA1_REBASELINE_BASE_TREE

        validate_f1010_h1_ca1_rebaseline(
            Path("."), F1010_H1_CA1_REBASELINE_BASE, head, "pull_request"
        )

        delta_mock.assert_called_once_with(
            Path("."), F1010_H1_CA1_REBASELINE_BASE, head,
            F1010_H1_CA1_REBASELINE_ALLOWED_STATUSES,
            F1010_H1_CA1_REBASELINE_ALLOWED_MODES,
        )
        context_mock.assert_called_once_with(Path("."), 64, 391)

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_f1010_h1_ca1_rebaseline_requires_protected_merge_push(
        self, require_sha_mock, ancestor_mock, tree_mock, parents_mock,
        delta_mock, context_mock,
    ) -> None:
        candidate = "b" * 40
        merge = "c" * 40
        tree_mock.side_effect = lambda _repo, commit: {
            F1010_H1_CA1_REBASELINE_BASE: F1010_H1_CA1_REBASELINE_BASE_TREE,
            candidate: "d" * 40,
            merge: "d" * 40,
        }[commit]
        parents_mock.return_value = [F1010_H1_CA1_REBASELINE_BASE, candidate]

        validate_f1010_h1_ca1_rebaseline(
            Path("."), F1010_H1_CA1_REBASELINE_BASE, merge, "push"
        )

        delta_mock.assert_called_once_with(
            Path("."), F1010_H1_CA1_REBASELINE_BASE, candidate,
            F1010_H1_CA1_REBASELINE_ALLOWED_STATUSES,
            F1010_H1_CA1_REBASELINE_ALLOWED_MODES,
        )
        context_mock.assert_called_once_with(Path("."), 64, 391)

    def test_detect_mode_selects_f1010_h1_ca1_rebaseline(self) -> None:
        self.assertEqual(
            detect_mode(
                "pull_request", "desarrollo", F1010_H1_CA1_REBASELINE_HEAD_REF,
                F1010_H1_CA1_REBASELINE_BASE,
            ),
            "f1010_h1_ca1_rebaseline",
        )

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_g5_production_readonly_accepts_exact_candidate(
        self, require_sha_mock, ancestor_mock, tree_mock, parents_mock,
        delta_mock, context_mock,
    ) -> None:
        head = "a" * 40
        tree_mock.return_value = G5_PRODUCTION_READONLY_BASE_TREE
        parents_mock.return_value = [G5_PRODUCTION_READONLY_BASE]

        validate_g5_production_readonly(
            Path("."), G5_PRODUCTION_READONLY_BASE, head, "pull_request"
        )

        delta_mock.assert_called_once_with(
            Path("."), G5_PRODUCTION_READONLY_BASE, head,
            G5_PRODUCTION_READONLY_ALLOWED_STATUSES,
            G5_PRODUCTION_READONLY_ALLOWED_MODES,
        )
        context_mock.assert_called_once_with(Path("."), 65, 400)

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_g5_production_readonly_requires_protected_merge_push(
        self, require_sha_mock, ancestor_mock, tree_mock, parents_mock,
        delta_mock, context_mock,
    ) -> None:
        candidate = "b" * 40
        merge = "c" * 40
        tree_mock.side_effect = lambda _repo, commit: {
            G5_PRODUCTION_READONLY_BASE: G5_PRODUCTION_READONLY_BASE_TREE,
            candidate: "d" * 40,
            merge: "d" * 40,
        }[commit]
        parents_mock.return_value = [G5_PRODUCTION_READONLY_BASE, candidate]

        validate_g5_production_readonly(
            Path("."), G5_PRODUCTION_READONLY_BASE, merge, "push"
        )

        delta_mock.assert_called_once_with(
            Path("."), G5_PRODUCTION_READONLY_BASE, candidate,
            G5_PRODUCTION_READONLY_ALLOWED_STATUSES,
            G5_PRODUCTION_READONLY_ALLOWED_MODES,
        )
        context_mock.assert_called_once_with(Path("."), 65, 400)

    def test_detect_mode_selects_g5_production_readonly(self) -> None:
        self.assertEqual(
            detect_mode(
                "pull_request", "desarrollo", G5_PRODUCTION_READONLY_HEAD_REF,
                G5_PRODUCTION_READONLY_BASE,
            ),
            "g5_production_readonly",
        )

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_g5_v2_attribution_accepts_exact_candidate(
        self, require_sha_mock, ancestor_mock, tree_mock, parents_mock,
        delta_mock, context_mock,
    ) -> None:
        head = "a" * 40
        tree_mock.return_value = G5_V2_ATTRIBUTION_BASE_TREE
        parents_mock.return_value = [G5_V2_ATTRIBUTION_BASE]

        validate_g5_v2_attribution(
            Path("."), G5_V2_ATTRIBUTION_BASE, head, "pull_request"
        )

        delta_mock.assert_called_once_with(
            Path("."), G5_V2_ATTRIBUTION_BASE, head,
            G5_V2_ATTRIBUTION_ALLOWED_STATUSES,
            G5_V2_ATTRIBUTION_ALLOWED_MODES,
        )
        context_mock.assert_called_once_with(Path("."), 66, 403)

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.is_ancestor", return_value=True)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_g5_v2_attribution_requires_protected_merge_push(
        self, require_sha_mock, ancestor_mock, tree_mock, parents_mock,
        delta_mock, context_mock,
    ) -> None:
        candidate = "b" * 40
        merge = "c" * 40
        tree_mock.side_effect = lambda _repo, commit: {
            G5_V2_ATTRIBUTION_BASE: G5_V2_ATTRIBUTION_BASE_TREE,
            candidate: "d" * 40,
            merge: "d" * 40,
        }[commit]
        parents_mock.return_value = [G5_V2_ATTRIBUTION_BASE, candidate]

        validate_g5_v2_attribution(
            Path("."), G5_V2_ATTRIBUTION_BASE, merge, "push"
        )

        delta_mock.assert_called_once_with(
            Path("."), G5_V2_ATTRIBUTION_BASE, candidate,
            G5_V2_ATTRIBUTION_ALLOWED_STATUSES,
            G5_V2_ATTRIBUTION_ALLOWED_MODES,
        )
        context_mock.assert_called_once_with(Path("."), 66, 403)

    def test_detect_mode_selects_g5_v2_attribution(self) -> None:
        self.assertEqual(
            detect_mode(
                "pull_request", "desarrollo", G5_V2_ATTRIBUTION_HEAD_REF,
                G5_V2_ATTRIBUTION_BASE,
            ),
            "g5_v2_attribution",
        )
        self.assertEqual(
            detect_mode(
                "pull_request", "desarrollo", G5_V2_ATTRIBUTION_HEAD_REF,
                "0" * 40,
            ),
            "skip",
        )

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_g5_v2_post_merge_accepts_exact_attestation(
        self, require_sha_mock, tree_mock, parents_mock, delta_mock, context_mock,
    ) -> None:
        head = "a" * 40
        tree_mock.return_value = G5_V2_POST_MERGE_BASE_TREE
        parents_mock.side_effect = lambda _repo, commit: {
            G5_V2_POST_MERGE_BASE: [
                G5_V2_POST_MERGE_PREVIOUS_BASE,
                G5_V2_POST_MERGE_CANDIDATE,
            ],
            head: [G5_V2_POST_MERGE_BASE],
        }[commit]

        validate_g5_v2_post_merge(
            Path("."), G5_V2_POST_MERGE_BASE, head, "pull_request"
        )

        delta_mock.assert_called_once_with(
            Path("."), G5_V2_POST_MERGE_BASE, head,
            G5_V2_POST_MERGE_ALLOWED_STATUSES,
            G5_V2_POST_MERGE_ALLOWED_MODES,
        )
        context_mock.assert_called_once_with(Path("."), 66, 403)

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_g5_v2_post_merge_requires_protected_merge_push(
        self, require_sha_mock, tree_mock, parents_mock, delta_mock, context_mock,
    ) -> None:
        candidate = "b" * 40
        merge = "c" * 40
        tree_mock.return_value = G5_V2_POST_MERGE_BASE_TREE
        parents_mock.side_effect = lambda _repo, commit: {
            G5_V2_POST_MERGE_BASE: [
                G5_V2_POST_MERGE_PREVIOUS_BASE,
                G5_V2_POST_MERGE_CANDIDATE,
            ],
            merge: [G5_V2_POST_MERGE_BASE, candidate],
        }[commit]

        validate_g5_v2_post_merge(
            Path("."), G5_V2_POST_MERGE_BASE, merge, "push"
        )

        delta_mock.assert_called_once_with(
            Path("."), G5_V2_POST_MERGE_BASE, candidate,
            G5_V2_POST_MERGE_ALLOWED_STATUSES,
            G5_V2_POST_MERGE_ALLOWED_MODES,
        )
        context_mock.assert_called_once_with(Path("."), 66, 403)

    def test_detect_mode_selects_g5_v2_post_merge(self) -> None:
        self.assertEqual(
            detect_mode(
                "pull_request", "desarrollo", G5_V2_POST_MERGE_HEAD_REF,
                G5_V2_POST_MERGE_BASE,
            ),
            "g5_v2_post_merge",
        )
        self.assertEqual(
            detect_mode(
                "pull_request", "desarrollo", G5_V2_POST_MERGE_HEAD_REF,
                "0" * 40,
            ),
            "skip",
        )

    @mock.patch("scripts.security.f109_boundary.parse_args")
    def test_cli_rejects_g5_v2_post_merge_branch_from_wrong_base(
        self, parse_args_mock,
    ) -> None:
        parse_args_mock.return_value = SimpleNamespace(
            repo=Path("."),
            event="pull_request",
            base_ref="desarrollo",
            head_ref=G5_V2_POST_MERGE_HEAD_REF,
            base_sha="0" * 40,
            head_sha="1" * 40,
            base_repo="owner/repo",
            head_repo="owner/repo",
            cert_tip="",
            p1_base="",
            p1_base_tree="",
            p2_base="",
            p2_base_tree="",
            g2_base="",
            g2_base_tree="",
            p5_base="",
            p5_base_tree="",
            f1010_m1_base="",
            f1010_m1_base_tree="",
            github_output="",
        )

        self.assertEqual(main(), 1)

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_g5_get_only_adapter_accepts_exact_candidate(
        self, require_sha_mock, tree_mock, parents_mock, delta_mock, context_mock,
    ) -> None:
        self.assertEqual(
            G5_GET_ONLY_ADAPTER_BASE,
            "74defb6326d8432bf790cb84b4aa549fefc425be",
        )
        self.assertEqual(
            G5_GET_ONLY_ADAPTER_BASE_TREE,
            "b9b4cc8a6f8279f898b2b8bf2a900c56a741b528",
        )
        self.assertEqual(
            G5_GET_ONLY_ADAPTER_PREVIOUS_BASE,
            "191539de71cbff95552c476463305e8d6f3e4b73",
        )
        self.assertEqual(
            G5_GET_ONLY_ADAPTER_CANDIDATE,
            "d6e4eaae058b52aacf5099c763204a1343a6eebf",
        )
        self.assertEqual(
            G5_GET_ONLY_ADAPTER_HEAD_REF,
            "feat/f10-9-g5-workflow-pr-d",
        )
        self.assertEqual(
            G5_GET_ONLY_ADAPTER_STATUS,
            "DEPLOYMENT_READY_DISABLED_NOT_CONFIGURED",
        )
        self.assertEqual(
            G5_GET_ONLY_ADAPTER_PREVIOUS_RESULT,
            "MERGED_POST_MERGE_VERIFIED",
        )
        head = "a" * 40
        tree_mock.return_value = G5_GET_ONLY_ADAPTER_BASE_TREE
        parents_mock.side_effect = lambda _repo, commit: {
            G5_GET_ONLY_ADAPTER_BASE: [
                G5_GET_ONLY_ADAPTER_PREVIOUS_BASE,
                G5_GET_ONLY_ADAPTER_CANDIDATE,
            ],
            head: [G5_GET_ONLY_ADAPTER_BASE],
        }[commit]

        validate_g5_get_only_adapter(
            Path("."), G5_GET_ONLY_ADAPTER_BASE, head, "pull_request"
        )

        delta_mock.assert_called_once_with(
            Path("."), G5_GET_ONLY_ADAPTER_BASE, head,
            G5_GET_ONLY_ADAPTER_ALLOWED_STATUSES,
            G5_GET_ONLY_ADAPTER_ALLOWED_MODES,
        )
        context_mock.assert_called_once_with(Path("."), 71, 408)

    def test_g5_get_only_adapter_successor_allowlist_is_minimal_pr_d_paths(self) -> None:
        self.assertEqual(
            G5_GET_ONLY_ADAPTER_ALLOWED_STATUSES,
            {
                ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
                ".context/decisiones/ADR-0015_g5_deployment_ready_disabled.md": "A",
                ".context/estado_del_proyecto.md": "M",
                ".context/operaciones/g5_get_only_adapter_contract_2026_08_14.md": "M",
                ".context/operaciones/plan_remediacion_f10_9_fg2_fg3.md": "M",
                ".github/workflows/f9-7-contract.yml": "M",
                ".github/workflows/g5-manual-trust-gate.yml": "M",
                "scripts/security/f109_boundary.py": "M",
                "scripts/shared/f10_9_g5_get_only_adapter_contract.py": "M",
                "scripts/shared/f10_9_g5_readonly_collector.py": "M",
                "tests/test_fase10_9_branch_reconciliation.py": "M",
                "tests/test_fase10_9_g5_get_only_adapter_contract.py": "M",
                "tests/test_fase10_9_g5_production_readonly.py": "M",
                "workers/g5-trust-broker/src/index.mjs": "M",
                "workers/g5-trust-broker/test/trust-broker.test.mjs": "M",
            },
        )
        self.assertEqual(set(G5_GET_ONLY_ADAPTER_ALLOWED_MODES.values()), {"100644"})

    def test_g5_get_only_adapter_v2_3_required_security_markers(self) -> None:
        source = Path(
            "scripts/shared/f10_9_g5_get_only_adapter_contract.py"
        ).read_text(encoding="utf-8")
        for marker in (
            "f10.9-g5-get-only-adapter-contract.v2.3",
            "f10.9-g5-get-only-adapter-schema.v2.3",
            "f10.9-g5-get-only-adapter-v2.3",
            "class FrozenRow",
            "class LifecycleEvidence",
            "class StaticSourceTarget",
            "class EffectiveProfileRouting",
            "class SourceAttemptResult",
            "class FG3PriorMutationEvidence",
            "SOURCE_ATTEMPT_BUDGET_NS = 15_000_000_000",
            "MAX_SOURCES_PER_PROFILE = 64",
            "MAX_PROFILE_SOURCE_PAIRS = 50_000",
            "MAX_FG3_HISTORICAL_OBSERVATIONS = 50_000",
            "SOURCE_ATTEMPT_GRAMMAR",
            'SOURCE_ROLE_PROBE_TARGET = "PROBE_TARGET"',
            'SOURCE_ROLE_TEMPLATE = "TEMPLATE"',
            'SOURCE_ROLE_FILTER = "FILTER"',
            "from .url_identity import build_url_identity",
            "import ipaddress",
            "identity = build_url_identity(value)",
            "address = ipaddress.ip_address(host)",
            "address is not None and not address.is_global",
            "return identity.canonical_url",
            "def _is_safe_profile_regex",
            "Deliberately linear subset",
            'if character in "()|*+?{}":',
            "len(pattern) > 200",
            "regex_url_text = lowered[:2000]",
            "circuit_effective_open",
            "circuit_auto_closed",
            "observed_at - parsed_circuit_opened_at < timedelta(hours=24)",
            'REDIRECT_EVIDENCE_POLICY = "NO_REDIRECT_WITHOUT_DERIVATION_EVIDENCE"',
            "expected_historical_count = 27 + max(0, len(required_inactive) - 1)",
            "len(evidence.historical_observations) != expected_historical_count",
            "any(len(items) != 1 for items in mutations_by_course.values())",
            "count > MAX_FG3_HISTORICAL_OBSERVATIONS",
            "len(manifest.category_counts) != 3",
            "_enforce_fg3_collection_limit(len(evidence.courses))",
            "_enforce_fg3_collection_limit(len(evidence.prior_mutations))",
            "len(evidence.historical_observations)",
            "if len(target_values) > MAX_SOURCES_PER_PROFILE:\n"
            "        _raise(STOP_TARGET_BINDING_INVALID)",
            "if type(count) is not int or count < 0 or count > MAX_PROFILE_SOURCE_PAIRS:\n"
            "        _raise(STOP_TARGET_BINDING_INVALID)",
            "utc_first = min(first_attempts, key=lambda item: item[1].started_at_utc)",
            "monotonic_first = min(",
            "if utc_first[0] != monotonic_first[0]",
            "routing_observed_at = utc_first[1].started_at_utc",
            "_require_complete",
            "historical_observation_fingerprint",
            "prior_mutation_fingerprint",
            "profile_source_fingerprints",
            "validate_source_coverage",
            "source_terminal_reason",
            "validate_lifecycle_evidence",
            "_STALE_AFTER = timedelta(hours=24)",
            "STOP_G5_SOURCE_BLOCKERS_PRESENT",
            "STOP_G5_LIFECYCLE_BLOCKERS_PRESENT",
            "STOP_G5_TRUST_VERIFICATION_NOT_IMPLEMENTED",
            "REPOSITORY_ONLY_TRUST_PLANE_PR_A_STOP",
            "MERGED_POST_MERGE_VERIFIED",
            "DEPLOYMENT_READY_DISABLED_NOT_CONFIGURED",
            "IMPLEMENTED_DISABLED_NOT_CONFIGURED",
            "class GateIntent",
            "class GitHubOidcClaims",
            "class WorkflowRunEvidence",
            "class EnvironmentEvidence",
            "class ApprovalEvidence",
            "class DeploymentEvidence",
            "class GateConsumptionReceipt",
            "STOP_G5_AUTHORITY_INVALID",
            "STOP_G5_APPROVAL_INVALID",
            "STOP_G5_BINDING_DRIFT",
            "STOP_G5_REPLAY_DETECTED",
            "STOP_G5_GATE_EXPIRED",
            "STOP_G5_CONSUMPTION_AMBIGUOUS",
            "STOP_G5_ATOMIC_LEDGER_REQUIRED",
            "STOP_G5_PROOF_INVALID",
        ):
            self.assertIn(marker, source)
        for forbidden in (
            "asdict",
            "row: Mapping",
            "Protocol",
            "runtime_checkable",
            "SourceAttemptTiming",
        ):
            self.assertNotIn(forbidden, source)

    def test_g5_v2_3_focused_ci_precedes_historical_f9_7_checkout(self) -> None:
        workflow = Path(".github/workflows/f9-7-contract.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("F10.9 G5 Workflow PR D Deployment-Ready Disabled", workflow)
        self.assertIn("workers/g5-trust-broker/**", workflow)
        self.assertIn(".github/workflows/g5-manual-trust-gate.yml", workflow)
        self.assertIn("pull_request:", workflow)
        self.assertIn("branches: [desarrollo]", workflow)
        self.assertIn(
            "github.event.pull_request.head.sha || github.sha", workflow
        )
        self.assertIn(
            "needs: [g5-get-only-v2-3, f1010-m3-zero-write]", workflow
        )
        self.assertIn(
            'test "${{ needs.g5-get-only-v2-3.result }}" = "success"', workflow
        )
        for marker in (
            "Block G5 trust-plane external egress",
            "--bounding-set=-all",
            "env -i HOME=/tmp CI=true",
            "Restore G5 trust-plane external egress",
        ):
            self.assertIn(marker, workflow)
        self.assertLess(
            workflow.index("Run repository-only G5 trust-plane focused contract"),
            workflow.index('git checkout --detach "$F97_CANDIDATE_COMMIT"'),
        )

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_g5_get_only_adapter_requires_protected_merge_push(
        self, require_sha_mock, tree_mock, parents_mock, delta_mock, context_mock,
    ) -> None:
        candidate = "b" * 40
        merge = "c" * 40
        tree_mock.return_value = G5_GET_ONLY_ADAPTER_BASE_TREE
        parents_mock.side_effect = lambda _repo, commit: {
            G5_GET_ONLY_ADAPTER_BASE: [
                G5_GET_ONLY_ADAPTER_PREVIOUS_BASE,
                G5_GET_ONLY_ADAPTER_CANDIDATE,
            ],
            merge: [G5_GET_ONLY_ADAPTER_BASE, candidate],
        }[commit]

        validate_g5_get_only_adapter(
            Path("."), G5_GET_ONLY_ADAPTER_BASE, merge, "push"
        )

        delta_mock.assert_called_once_with(
            Path("."), G5_GET_ONLY_ADAPTER_BASE, candidate,
            G5_GET_ONLY_ADAPTER_ALLOWED_STATUSES,
            G5_GET_ONLY_ADAPTER_ALLOWED_MODES,
        )
        context_mock.assert_called_once_with(Path("."), 71, 408)

    @mock.patch("scripts.security.f109_boundary.commit_tree", return_value="0" * 40)
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_g5_get_only_adapter_rejects_protected_base_tree_drift(
        self, require_sha_mock, tree_mock,
    ) -> None:
        with self.assertRaises(BoundaryError):
            validate_g5_get_only_adapter(
                Path("."), G5_GET_ONLY_ADAPTER_BASE, "a" * 40, "pull_request"
            )

    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch(
        "scripts.security.f109_boundary.commit_tree",
        return_value=G5_GET_ONLY_ADAPTER_BASE_TREE,
    )
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_g5_get_only_adapter_rejects_protected_parent_drift(
        self, require_sha_mock, tree_mock, parents_mock,
    ) -> None:
        parents_mock.return_value = ["0" * 40, G5_GET_ONLY_ADAPTER_CANDIDATE]
        with self.assertRaises(BoundaryError):
            validate_g5_get_only_adapter(
                Path("."), G5_GET_ONLY_ADAPTER_BASE, "a" * 40, "pull_request"
            )

    def test_detect_mode_selects_g5_get_only_adapter(self) -> None:
        self.assertEqual(
            detect_mode(
                "pull_request", "desarrollo", G5_GET_ONLY_ADAPTER_HEAD_REF,
                G5_GET_ONLY_ADAPTER_BASE,
            ),
            "g5_get_only_adapter",
        )
        self.assertEqual(
            detect_mode(
                "pull_request", "desarrollo", G5_GET_ONLY_ADAPTER_HEAD_REF,
                "0" * 40,
            ),
            "skip",
        )

    @mock.patch("scripts.security.f109_boundary.parse_args")
    def test_cli_rejects_g5_get_only_adapter_branch_from_wrong_base(
        self, parse_args_mock,
    ) -> None:
        parse_args_mock.return_value = SimpleNamespace(
            repo=Path("."),
            event="pull_request",
            base_ref="desarrollo",
            head_ref=G5_GET_ONLY_ADAPTER_HEAD_REF,
            base_sha="0" * 40,
            head_sha="1" * 40,
            base_repo="owner/repo",
            head_repo="owner/repo",
            cert_tip="",
            p1_base="",
            p1_base_tree="",
            p2_base="",
            p2_base_tree="",
            g2_base="",
            g2_base_tree="",
            p5_base="",
            p5_base_tree="",
            f1010_m1_base="",
            f1010_m1_base_tree="",
            github_output="",
        )

        self.assertEqual(main(), 1)

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_g5_operational_runbook_accepts_exact_candidate(
        self, require_sha_mock, tree_mock, parents_mock, delta_mock, context_mock,
    ) -> None:
        self.assertEqual(
            G5_OPERATIONAL_RUNBOOK_BASE,
            "bd0d82864c26755435e551b835d145b864383810",
        )
        self.assertEqual(
            G5_OPERATIONAL_RUNBOOK_BASE_TREE,
            "135af5a95237a1d4d6e1b977e8bb9ab82ac95e16",
        )
        self.assertEqual(
            G5_OPERATIONAL_RUNBOOK_HEAD_REF,
            "feat/f10-9-pr-e-reconcile-g5-runbook",
        )
        self.assertEqual(
            G5_OPERATIONAL_RUNBOOK_STATUS,
            "MERGED_POST_MERGE_VERIFIED_WITH_INFRA_RETRY",
        )
        head = "a" * 40
        tree_mock.return_value = G5_OPERATIONAL_RUNBOOK_BASE_TREE
        parents_mock.side_effect = lambda _repo, commit: {
            head: [G5_OPERATIONAL_RUNBOOK_BASE],
        }[commit]

        validate_g5_operational_runbook(
            Path("."), G5_OPERATIONAL_RUNBOOK_BASE, head, "pull_request"
        )

        delta_mock.assert_called_once_with(
            Path("."), G5_OPERATIONAL_RUNBOOK_BASE, head,
            G5_OPERATIONAL_RUNBOOK_ALLOWED_STATUSES,
            G5_OPERATIONAL_RUNBOOK_ALLOWED_MODES,
        )
        context_mock.assert_called_once_with(Path("."), 73, 416)

    def test_g5_operational_runbook_allowlist_is_minimal_pr_e_paths(self) -> None:
        self.assertEqual(
            G5_OPERATIONAL_RUNBOOK_ALLOWED_STATUSES,
            {
                ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
                ".context/decisiones/ADR-0016_g5_operational_activation_gates.md": "A",
                ".context/estado_del_proyecto.md": "M",
                ".context/operaciones/g5_get_only_adapter_contract_2026_08_14.md": "M",
                ".context/operaciones/g5_operational_activation_manifest_2026_08_15.json": "A",
                ".context/operaciones/g5_operational_activation_runbook_2026_08_15.md": "A",
                ".context/operaciones/plan_remediacion_f10_9_fg2_fg3.md": "M",
                ".github/workflows/f9-7-contract.yml": "M",
                "scripts/security/f109_boundary.py": "M",
                "scripts/shared/f10_9_g5_operational_activation_preflight.py": "A",
                "tests/test_fase10_9_branch_reconciliation.py": "M",
                "tests/test_fase10_9_g5_operational_activation_preflight.py": "A",
            },
        )
        self.assertEqual(set(G5_OPERATIONAL_RUNBOOK_ALLOWED_MODES.values()), {"100644"})

    def test_detect_mode_selects_g5_operational_runbook(self) -> None:
        self.assertEqual(
            detect_mode(
                "pull_request", "desarrollo", G5_OPERATIONAL_RUNBOOK_HEAD_REF,
                G5_OPERATIONAL_RUNBOOK_BASE,
            ),
            "g5_operational_runbook",
        )
        self.assertEqual(
            detect_mode(
                "pull_request", "desarrollo", G5_OPERATIONAL_RUNBOOK_HEAD_REF,
                "0" * 40,
            ),
            "skip",
        )

    @mock.patch("scripts.security.f109_boundary.parse_args")
    def test_cli_rejects_g5_operational_runbook_from_wrong_base(
        self, parse_args_mock,
    ) -> None:
        parse_args_mock.return_value = SimpleNamespace(
            repo=Path("."),
            event="pull_request",
            base_ref="desarrollo",
            head_ref=G5_OPERATIONAL_RUNBOOK_HEAD_REF,
            base_sha="0" * 40,
            head_sha="1" * 40,
            base_repo="owner/repo",
            head_repo="owner/repo",
            cert_tip="",
            p1_base="",
            p1_base_tree="",
            p2_base="",
            p2_base_tree="",
            g2_base="",
            g2_base_tree="",
            p5_base="",
            p5_base_tree="",
            f1010_m1_base="",
            f1010_m1_base_tree="",
            github_output="",
        )

        self.assertEqual(main(), 1)

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_g5_e1_hardening_accepts_exact_candidate(
        self, require_sha_mock, tree_mock, parents_mock, delta_mock, context_mock,
    ) -> None:
        self.assertEqual(
            G5_E1_HARDENING_BASE,
            "71d6640b990b934fa02401518650ec38dca6cae4",
        )
        self.assertEqual(
            G5_E1_HARDENING_BASE_TREE,
            "815a2316c8de67047567d89a9928576869f43c4f",
        )
        self.assertEqual(G5_E1_HARDENING_HEAD_REF, "feat/f10-9-pr-f-e1-hardening")
        self.assertEqual(G5_E1_HARDENING_STATUS, "MERGED_POST_MERGE_VERIFIED")
        self.assertEqual(G5_E1_READINESS_STATUS, "E1_ACCOUNT_READINESS_GO")
        self.assertEqual(
            G5_E1_DEPLOYMENT_STOP,
            "E1_DEPLOYMENT_STOP_REPOSITORY_HARDENING_REQUIRED",
        )
        head = "b" * 40
        tree_mock.return_value = G5_E1_HARDENING_BASE_TREE
        parents_mock.side_effect = lambda _repo, commit: {
            head: [G5_E1_HARDENING_BASE],
        }[commit]
        repo = self.make_repo()
        evidence = "\n".join(
            (
                G5_E1_HARDENING_STATUS,
                G5_E1_HARDENING_BASE,
                G5_E1_HARDENING_BASE_TREE,
                "eb052c2755937a2bf239cd778bc814274fbc846f",
                "31917838025=PASS",
                "31917838011=PASS",
                "95092629457=PASS",
                "95092706912=PASS",
                "run_attempt=1",
                G5_E1_READINESS_STATUS,
                "Workers existentes `0`",
                "NOT_EXECUTED",
                G5_E1_DEPLOYMENT_STOP,
                "Hito 1 `60%`",
                "F10.9 `38%`",
                "G5 `50%`",
                "NOT_CREATED_NOT_APPROVED_NOT_CONSUMED",
                "STOP_G5_TRUST_VERIFICATION_NOT_IMPLEMENTED",
                "IMPLEMENTED_DISABLED_NOT_CONFIGURED",
                "G5_TRUST_OPERATIONAL_ENABLED` permanece `ABSENT_NOT_CONFIGURED`",
                "preview_urls:false",
                "workers_dev:false",
                "wrangler deploy --strict --config wrangler.repository-only.jsonc",
                "--dry-run --outdir /tmp/studiamatch-g5-e1-dry-run",
                "CLOUDFLARE_API_TOKEN",
                "CLOUDFLARE_ACCOUNT_ID",
                "CF_API_TOKEN",
                "CF_ACCOUNT_ID",
                "E3A",
                "DEFINED_NOT_EXECUTED",
                "E4 queda bloqueado",
                "Este PR no selecciona ni habilita endpoint",
            )
        )
        for relative in (
            ".context/estado_del_proyecto.md",
            ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md",
            ".context/operaciones/plan_remediacion_f10_9_fg2_fg3.md",
            ".context/operaciones/g5_operational_activation_runbook_2026_08_15.md",
            ".context/decisiones/ADR-0016_g5_operational_activation_gates.md",
            ".context/decisiones/ADR-0017_g5_e1_cloudflare_deployment_hardening.md",
        ):
            path = repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(evidence, encoding="utf-8")
        manifest_path = repo / ".context/operaciones/g5_operational_activation_manifest_2026_08_15.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            json.dumps({"gates": [{"id": gate} for gate in ("E1", "E2", "E3", "E3A", "E4", "E5", "E6")]}),
            encoding="utf-8",
        )
        preflight_path = repo / "tests/test_fase10_9_g5_operational_activation_preflight.py"
        preflight_path.parent.mkdir(parents=True, exist_ok=True)
        preflight_path.write_text(
            "test_gates_e1_to_e6_and_e3a_are_separate_and_non_executing",
            encoding="utf-8",
        )
        e1_path = repo / "tests/test_fase10_9_g5_e1_hardening.py"
        e1_path.write_text(
            "\n".join(
                (
                    "test_wrangler_version_is_exact_and_lockfile_is_versioned",
                    "test_wrangler_config_is_isolated_and_explicitly_non_public",
                    "test_package_scripts_require_dry_run_before_exact_deploy_command",
                    "test_cloudflare_credential_names_are_standard_for_e1_only",
                    "test_e3a_endpoint_gate_is_separate_and_blocks_e4",
                    "test_e1_hardening_docs_preserve_stops_and_no_sensitive_values",
                )
            ),
            encoding="utf-8",
        )
        workflow_path = repo / ".github/workflows/f9-7-contract.yml"
        workflow_path.parent.mkdir(parents=True, exist_ok=True)
        workflow_path.write_text(
            "tests/test_fase10_9_g5_e1_hardening.py\n"
            "tests/test_fase10_9_g5_operational_activation_preflight.py\n",
            encoding="utf-8",
        )
        config_path = repo / "workers/g5-trust-broker/wrangler.repository-only.jsonc"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(
            json.dumps(
                {
                    "name": "g5-trust-broker-repository-only",
                    "main": "src/index.mjs",
                    "compatibility_date": "2026-08-15",
                    "workers_dev": False,
                    "preview_urls": False,
                    "durable_objects": {
                        "bindings": [
                            {"name": "G5_ATOMIC_LEDGER", "class_name": "G5AtomicLedgerDurableObject"}
                        ]
                    },
                    "migrations": [
                        {"tag": "repository-only-v1", "new_sqlite_classes": ["G5AtomicLedgerDurableObject"]}
                    ],
                }
            ),
            encoding="utf-8",
        )
        package_path = repo / "workers/g5-trust-broker/package.json"
        package_path.write_text(
            json.dumps(
                {
                    "scripts": {
                        "e1:dry-run": "wrangler deploy --strict --config wrangler.repository-only.jsonc --dry-run --outdir /tmp/studiamatch-g5-e1-dry-run",
                        "e1:deploy": "wrangler deploy --strict --config wrangler.repository-only.jsonc",
                    },
                    "devDependencies": {"wrangler": "4.30.0"},
                }
            ),
            encoding="utf-8",
        )
        lock_path = repo / "workers/g5-trust-broker/package-lock.json"
        lock_path.write_text(
            json.dumps({"lockfileVersion": 3, "packages": {"node_modules/wrangler": {"version": "4.30.0"}}}),
            encoding="utf-8",
        )

        validate_g5_e1_hardening(repo, G5_E1_HARDENING_BASE, head, "pull_request")

        delta_mock.assert_called_once_with(
            repo, G5_E1_HARDENING_BASE, head,
            G5_E1_HARDENING_ALLOWED_STATUSES,
            G5_E1_HARDENING_ALLOWED_MODES,
        )
        context_mock.assert_called_once_with(repo, 74, 418)

    def test_g5_e1_hardening_allowlist_is_minimal_pr_f_paths(self) -> None:
        self.assertEqual(
            G5_E1_HARDENING_ALLOWED_STATUSES,
            {
                ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
                ".context/decisiones/ADR-0016_g5_operational_activation_gates.md": "M",
                ".context/decisiones/ADR-0017_g5_e1_cloudflare_deployment_hardening.md": "A",
                ".context/estado_del_proyecto.md": "M",
                ".context/operaciones/g5_operational_activation_manifest_2026_08_15.json": "M",
                ".context/operaciones/g5_operational_activation_runbook_2026_08_15.md": "M",
                ".context/operaciones/plan_remediacion_f10_9_fg2_fg3.md": "M",
                ".github/workflows/f9-7-contract.yml": "M",
                "scripts/security/f109_boundary.py": "M",
                "scripts/shared/f10_9_g5_operational_activation_preflight.py": "M",
                "tests/test_fase10_9_branch_reconciliation.py": "M",
                "tests/test_fase10_9_g5_e1_hardening.py": "A",
                "tests/test_fase10_9_g5_operational_activation_preflight.py": "M",
                "workers/g5-trust-broker/package-lock.json": "A",
                "workers/g5-trust-broker/package.json": "A",
                "workers/g5-trust-broker/wrangler.repository-only.jsonc": "M",
            },
        )
        self.assertEqual(set(G5_E1_HARDENING_ALLOWED_MODES.values()), {"100644"})

    def test_detect_mode_selects_g5_e1_hardening(self) -> None:
        self.assertEqual(
            detect_mode(
                "pull_request", "desarrollo", G5_E1_HARDENING_HEAD_REF,
                G5_E1_HARDENING_BASE,
            ),
            "g5_e1_hardening",
        )
        self.assertEqual(
            detect_mode(
                "pull_request", "desarrollo", G5_E1_HARDENING_HEAD_REF,
                "0" * 40,
            ),
            "skip",
        )

    @mock.patch("scripts.security.f109_boundary.parse_args")
    def test_cli_rejects_g5_e1_hardening_from_wrong_base(self, parse_args_mock) -> None:
        parse_args_mock.return_value = SimpleNamespace(
            repo=Path("."),
            event="pull_request",
            base_ref="desarrollo",
            head_ref=G5_E1_HARDENING_HEAD_REF,
            base_sha="0" * 40,
            head_sha="1" * 40,
            base_repo="owner/repo",
            head_repo="owner/repo",
            cert_tip="",
            p1_base="",
            p1_base_tree="",
            p2_base="",
            p2_base_tree="",
            g2_base="",
            g2_base_tree="",
            p5_base="",
            p5_base_tree="",
            f1010_m1_base="",
            f1010_m1_base_tree="",
            github_output="",
        )

        self.assertEqual(main(), 1)

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_g5_e1_wrangler_compat_accepts_exact_candidate(
        self, require_sha_mock, tree_mock, parents_mock, delta_mock, context_mock,
    ) -> None:
        self.assertEqual(
            G5_E1_WRANGLER_COMPAT_BASE,
            "4bdc698cd9a8569e4e8290257effa6bc3aa3bb15",
        )
        self.assertEqual(
            G5_E1_WRANGLER_COMPAT_BASE_TREE,
            "874ccffa3db9871189ca351d88cc84e120251e95",
        )
        self.assertEqual(G5_E1_WRANGLER_COMPAT_HEAD_REF, "feat/f10-9-pr-g-wrangler-compat")
        self.assertEqual(G5_E1_WRANGLER_COMPAT_STATUS, "MERGED_POST_MERGE_VERIFIED")
        head = "b" * 40
        tree_mock.return_value = G5_E1_WRANGLER_COMPAT_BASE_TREE
        parents_mock.side_effect = lambda _repo, commit: {
            head: [G5_E1_WRANGLER_COMPAT_BASE],
        }[commit]

        validate_g5_e1_wrangler_compat(Path("."), G5_E1_WRANGLER_COMPAT_BASE, head, "pull_request")

        delta_mock.assert_called_once_with(
            Path("."), G5_E1_WRANGLER_COMPAT_BASE, head,
            G5_E1_WRANGLER_COMPAT_ALLOWED_STATUSES,
            G5_E1_WRANGLER_COMPAT_ALLOWED_MODES,
        )
        context_mock.assert_called_once_with(Path("."), 74, 418)

    def test_g5_e1_wrangler_compat_allowlist_is_minimal_pr_g_paths(self) -> None:
        self.assertEqual(
            G5_E1_WRANGLER_COMPAT_ALLOWED_STATUSES,
            {
                ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
                ".context/decisiones/ADR-0016_g5_operational_activation_gates.md": "M",
                ".context/decisiones/ADR-0017_g5_e1_cloudflare_deployment_hardening.md": "M",
                ".context/estado_del_proyecto.md": "M",
                ".context/operaciones/g5_operational_activation_manifest_2026_08_15.json": "M",
                ".context/operaciones/g5_operational_activation_runbook_2026_08_15.md": "M",
                ".context/operaciones/plan_remediacion_f10_9_fg2_fg3.md": "M",
                ".github/workflows/f9-7-contract.yml": "M",
                "scripts/security/f109_boundary.py": "M",
                "scripts/shared/f10_9_g5_operational_activation_preflight.py": "M",
                "tests/test_fase10_9_branch_reconciliation.py": "M",
                "tests/test_fase10_9_g5_e1_hardening.py": "M",
                "tests/test_fase10_9_g5_operational_activation_preflight.py": "M",
                "workers/g5-trust-broker/package-lock.json": "M",
                "workers/g5-trust-broker/package.json": "M",
                "workers/g5-trust-broker/test/block-egress.mjs": "A",
            },
        )
        self.assertEqual(set(G5_E1_WRANGLER_COMPAT_ALLOWED_MODES.values()), {"100644"})

    def test_detect_mode_selects_g5_e1_wrangler_compat(self) -> None:
        self.assertEqual(
            detect_mode(
                "pull_request", "desarrollo", G5_E1_WRANGLER_COMPAT_HEAD_REF,
                G5_E1_WRANGLER_COMPAT_BASE,
            ),
            "g5_e1_wrangler_compat",
        )
        self.assertEqual(
            detect_mode(
                "pull_request", "desarrollo", G5_E1_WRANGLER_COMPAT_HEAD_REF,
                "0" * 40,
            ),
            "skip",
        )

    @mock.patch("scripts.security.f109_boundary.parse_args")
    def test_cli_rejects_g5_e1_wrangler_compat_from_wrong_base(self, parse_args_mock) -> None:
        parse_args_mock.return_value = SimpleNamespace(
            repo=Path("."),
            event="pull_request",
            base_ref="desarrollo",
            head_ref=G5_E1_WRANGLER_COMPAT_HEAD_REF,
            base_sha="0" * 40,
            head_sha="1" * 40,
            base_repo="owner/repo",
            head_repo="owner/repo",
            cert_tip="",
            p1_base="",
            p1_base_tree="",
            p2_base="",
            p2_base_tree="",
            g2_base="",
            g2_base_tree="",
            p5_base="",
            p5_base_tree="",
            f1010_m1_base="",
            f1010_m1_base_tree="",
            github_output="",
        )

        self.assertEqual(main(), 1)

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_g5_trust_live_remediation_accepts_exact_candidate(
        self, require_sha_mock, tree_mock, parents_mock, delta_mock, context_mock,
    ) -> None:
        self.assertEqual(
            G5_TRUST_LIVE_REMEDIATION_BASE,
            "9811b19e1527b39366e43907990c4b77d1394f75",
        )
        self.assertEqual(
            G5_TRUST_LIVE_REMEDIATION_BASE_TREE,
            "edb7c827621fce1089d636b50494405115d348a6",
        )
        self.assertEqual(
            G5_TRUST_LIVE_REMEDIATION_HEAD_REF,
            "feat/f10-9-pr-h-trust-live-remediation",
        )
        self.assertEqual(G5_TRUST_LIVE_REMEDIATION_STATUS, "MERGED_POST_MERGE_VERIFIED")
        self.assertEqual(G5_E1_DEPLOYMENT_STATUS, "E1_DEPLOYMENT_PASS")
        self.assertEqual(
            G5_E1_CREDENTIAL_ATTESTATION,
            "E1_CREDENTIAL_REVOKED_AND_LOCAL_REMOVED",
        )
        head = "c" * 40
        tree_mock.return_value = G5_TRUST_LIVE_REMEDIATION_BASE_TREE
        parents_mock.side_effect = lambda _repo, commit: {
            head: [G5_TRUST_LIVE_REMEDIATION_BASE],
        }[commit]
        repo = self.make_repo()
        evidence = "\n".join(
            (
                G5_TRUST_LIVE_REMEDIATION_STATUS,
                "c36cc9b6efb166f2f840615759793b7917142f38",
                G5_TRUST_LIVE_REMEDIATION_BASE,
                G5_TRUST_LIVE_REMEDIATION_BASE_TREE,
                "31926378062=PASS",
                "31926378069=PASS",
                "95114516929=PASS",
                "95114603279=PASS",
                "run_attempt=1",
                G5_E1_DEPLOYMENT_STATUS,
                G5_E1_CREDENTIAL_ATTESTATION,
                "f10.9-g5-trust-broker.v2",
                "G5_ATOMIC_LEDGER",
                "G5AtomicLedgerDurableObject",
                "repository-only-v1",
                "routes/domains/schedules/vars/secrets `0`",
                "E4_BEFORE_E5_SUPERSEDED_NOT_EXECUTABLE",
                "NOT_CREATED_NOT_APPROVED_NOT_CONSUMED",
                "STOP_G5_TRUST_VERIFICATION_NOT_IMPLEMENTED",
                "IMPLEMENTED_DISABLED_NOT_CONFIGURED",
                "Hito 1 `60%`",
                "F10.9 `38%`",
                "G5 `50%`",
                *G5_TRUST_RUNTIME_POLICY_NAMES,
            )
        )
        for relative in (
            ".context/estado_del_proyecto.md",
            ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md",
            ".context/operaciones/plan_remediacion_f10_9_fg2_fg3.md",
            ".context/operaciones/g5_get_only_adapter_contract_2026_08_14.md",
            ".context/operaciones/g5_operational_activation_runbook_2026_08_15.md",
            ".context/decisiones/ADR-0016_g5_operational_activation_gates.md",
            ".context/decisiones/ADR-0018_g5_trust_live_remediation_repository_only.md",
        ):
            path = repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(evidence, encoding="utf-8")
        manifest_path = repo / ".context/operaciones/g5_operational_activation_manifest_2026_08_15.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            json.dumps(
                {
                    "superseded_sequence": "E4_BEFORE_E5_SUPERSEDED_NOT_EXECUTABLE",
                    "e1_deployment_reconciliation": {
                        "status": G5_E1_DEPLOYMENT_STATUS,
                        "credential_state": G5_E1_CREDENTIAL_ATTESTATION,
                    },
                    "required_configuration_names": [
                        {"name": name, "scope": "runtime", "state": "ABSENT_NOT_CONFIGURED"}
                        for name in G5_TRUST_RUNTIME_POLICY_NAMES
                    ],
                    "gates": [
                        {"id": gate}
                        for gate in ("E1", "E2", "E3", "E4", "E4A", "E4B", "E5", "E6")
                    ],
                }
            ),
            encoding="utf-8",
        )
        files = {
            "scripts/shared/f10_9_g5_operational_activation_preflight.py": "from __future__ import annotations\nWRANGLER_VERSION = '4.44.0'\n",
            "tests/test_fase10_9_g5_operational_activation_preflight.py": "\n".join(
                (
                    "test_pr390_and_e1_deployment_are_sanitized_and_reconciled",
                    "test_gates_e1_to_e6_are_reordered_and_non_executing",
                    "G5_TRUST_RUNTIME_ENABLED",
                )
            ),
            "scripts/shared/f10_9_g5_get_only_adapter_contract.py": "\n".join(
                ("RUNTIME_POLICY_BINDING_NAMES", "LEGACY_POLICY_DENYLIST", "_valid_runtime_policy_triplet")
            ),
            "tests/test_fase10_9_g5_get_only_adapter_contract.py": "test_legacy_pr_c_sha_tree_blob_are_denylist_not_authority",
            ".github/workflows/f9-7-contract.yml": ".context/decisiones/ADR-0018_g5_trust_live_remediation_repository_only.md",
            ".github/workflows/g5-manual-trust-gate.yml": "vars.G5_TRUST_RUNTIME_ENABLED == 'true'",
            "workers/g5-trust-broker/src/index.mjs": "\n".join(
                (
                    "RUNTIME_POLICY_BINDING_NAMES",
                    "G5ConnectedGithubAppAdapter",
                    "G5GithubJwksClient",
                    "createGithubAppJwt",
                    "LEGACY_POLICY_DENYLIST",
                    "G5_GITHUB_APP_INSTALLATION_ID",
                    "G5_TRUST_RUNTIME_ENABLED",
                )
            ),
            "workers/g5-trust-broker/test/trust-broker.test.mjs": "G5_TRUST_RUNTIME_ENABLED",
        }
        for relative, content in files.items():
            path = repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

        validate_g5_trust_live_remediation(
            repo, G5_TRUST_LIVE_REMEDIATION_BASE, head, "pull_request"
        )

        delta_mock.assert_called_once_with(
            repo, G5_TRUST_LIVE_REMEDIATION_BASE, head,
            G5_TRUST_LIVE_REMEDIATION_ALLOWED_STATUSES,
            G5_TRUST_LIVE_REMEDIATION_ALLOWED_MODES,
        )
        context_mock.assert_called_once_with(repo, 75, 426)

    def test_g5_trust_live_remediation_allowlist_is_minimal_pr_h_paths(self) -> None:
        self.assertEqual(
            G5_TRUST_LIVE_REMEDIATION_ALLOWED_STATUSES,
            {
                ".context/00_INDICE.md": "M",
                ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
                ".context/decisiones/ADR-0016_g5_operational_activation_gates.md": "M",
                ".context/decisiones/ADR-0018_g5_trust_live_remediation_repository_only.md": "A",
                ".context/estado_del_proyecto.md": "M",
                ".context/operaciones/g5_get_only_adapter_contract_2026_08_14.md": "M",
                ".context/operaciones/g5_operational_activation_manifest_2026_08_15.json": "M",
                ".context/operaciones/g5_operational_activation_runbook_2026_08_15.md": "M",
                ".context/operaciones/plan_remediacion_f10_9_fg2_fg3.md": "M",
                ".github/workflows/f9-7-contract.yml": "M",
                ".github/workflows/g5-manual-trust-gate.yml": "M",
                "scripts/security/f109_boundary.py": "M",
                "scripts/shared/f10_9_g5_get_only_adapter_contract.py": "M",
                "scripts/shared/f10_9_g5_operational_activation_preflight.py": "M",
                "tests/test_fase10_9_branch_reconciliation.py": "M",
                "tests/test_fase10_9_g5_e1_hardening.py": "M",
                "tests/test_fase10_9_g5_get_only_adapter_contract.py": "M",
                "tests/test_fase10_9_g5_operational_activation_preflight.py": "M",
                "workers/g5-trust-broker/src/index.mjs": "M",
                "workers/g5-trust-broker/test/trust-broker.test.mjs": "M",
            },
        )
        self.assertEqual(set(G5_TRUST_LIVE_REMEDIATION_ALLOWED_MODES.values()), {"100644"})

    def test_detect_mode_selects_g5_trust_live_remediation(self) -> None:
        self.assertEqual(
            detect_mode(
                "pull_request", "desarrollo", G5_TRUST_LIVE_REMEDIATION_HEAD_REF,
                G5_TRUST_LIVE_REMEDIATION_BASE,
            ),
            "g5_trust_live_remediation",
        )
        self.assertEqual(
            detect_mode(
                "pull_request", "desarrollo", G5_TRUST_LIVE_REMEDIATION_HEAD_REF,
                "0" * 40,
            ),
            "skip",
        )

    @mock.patch("scripts.security.f109_boundary.parse_args")
    def test_cli_rejects_g5_trust_live_remediation_from_wrong_base(self, parse_args_mock) -> None:
        parse_args_mock.return_value = SimpleNamespace(
            repo=Path("."),
            event="pull_request",
            base_ref="desarrollo",
            head_ref=G5_TRUST_LIVE_REMEDIATION_HEAD_REF,
            base_sha="0" * 40,
            head_sha="1" * 40,
            base_repo="owner/repo",
            head_repo="owner/repo",
            cert_tip="",
            p1_base="",
            p1_base_tree="",
            p2_base="",
            p2_base_tree="",
            g2_base="",
            g2_base_tree="",
            p5_base="",
            p5_base_tree="",
            f1010_m1_base="",
            f1010_m1_base_tree="",
            github_output="",
        )

        self.assertEqual(main(), 1)

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_g5_github_runtime_schema_accepts_exact_candidate(
        self, require_sha_mock, tree_mock, parents_mock, delta_mock, context_mock,
    ) -> None:
        self.assertEqual(
            G5_GITHUB_RUNTIME_SCHEMA_BASE,
            "5a76abaae8760a9ce6a418511264e6742fa5c74c",
        )
        self.assertEqual(
            G5_GITHUB_RUNTIME_SCHEMA_BASE_TREE,
            "9bd83392ade9e245f3fc4ab85bb85eb4f9031040",
        )
        self.assertEqual(
            G5_GITHUB_RUNTIME_SCHEMA_HEAD_REF,
            "feat/f10-9-pr-i-github-runtime-schema",
        )
        self.assertEqual(
            G5_GITHUB_RUNTIME_SCHEMA_PR391_CANDIDATE,
            "77f475af2e5900bc1338967676ebded71b672642",
        )
        self.assertEqual(G5_GITHUB_RUNTIME_SCHEMA_STATUS, "MERGED_POST_MERGE_VERIFIED")
        self.assertEqual(
            G5_GITHUB_RUNTIME_SCHEMA_E2_STOP,
            "E2_STOP_GITHUB_RUNTIME_SCHEMA_INCOMPATIBLE",
        )
        head = "d" * 40
        tree_mock.return_value = G5_GITHUB_RUNTIME_SCHEMA_BASE_TREE
        parents_mock.side_effect = lambda _repo, commit: {
            head: [G5_GITHUB_RUNTIME_SCHEMA_BASE],
        }[commit]
        repo = self.make_repo()
        source_root = Path(__file__).resolve().parents[1]
        for relative in (
            ".context/00_INDICE.md",
            ".context/decisiones/ADR-0019_github_runtime_schema_lifecycle.md",
            ".context/estado_del_proyecto.md",
            ".context/operaciones/g5_operational_activation_manifest_2026_08_15.json",
            ".context/operaciones/g5_operational_activation_runbook_2026_08_15.md",
            ".github/workflows/f9-7-contract.yml",
            "scripts/shared/f10_9_g5_get_only_adapter_contract.py",
            "scripts/shared/f10_9_g5_operational_activation_preflight.py",
            "tests/test_fase10_9_g5_get_only_adapter_contract.py",
            "tests/test_fase10_9_g5_operational_activation_preflight.py",
            "workers/g5-trust-broker/src/index.mjs",
            "workers/g5-trust-broker/test/trust-broker.test.mjs",
        ):
            path = repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text((source_root / relative).read_text(encoding="utf-8"), encoding="utf-8")

        validate_g5_github_runtime_schema(
            repo, G5_GITHUB_RUNTIME_SCHEMA_BASE, head, "pull_request"
        )

        delta_mock.assert_called_once_with(
            repo, G5_GITHUB_RUNTIME_SCHEMA_BASE, head,
            G5_GITHUB_RUNTIME_SCHEMA_ALLOWED_STATUSES,
            G5_GITHUB_RUNTIME_SCHEMA_ALLOWED_MODES,
        )
        context_mock.assert_called_once_with(repo, 77, 428)

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_g5_github_runtime_schema_requires_protected_merge_push(
        self, require_sha_mock, tree_mock, parents_mock, delta_mock, context_mock,
    ) -> None:
        candidate = "e" * 40
        merge = "f" * 40
        tree_mock.side_effect = lambda _repo, commit: {
            G5_GITHUB_RUNTIME_SCHEMA_BASE: G5_GITHUB_RUNTIME_SCHEMA_BASE_TREE,
            candidate: "a" * 40,
            merge: "a" * 40,
        }[commit]
        parents_mock.return_value = [G5_GITHUB_RUNTIME_SCHEMA_BASE, candidate]

        validate_g5_github_runtime_schema(
            Path("."), G5_GITHUB_RUNTIME_SCHEMA_BASE, merge, "push"
        )

        delta_mock.assert_called_once_with(
            Path("."), G5_GITHUB_RUNTIME_SCHEMA_BASE, candidate,
            G5_GITHUB_RUNTIME_SCHEMA_ALLOWED_STATUSES,
            G5_GITHUB_RUNTIME_SCHEMA_ALLOWED_MODES,
        )
        context_mock.assert_called_once_with(Path("."), 77, 428)

    def test_g5_github_runtime_schema_allowlist_is_minimal_pr_i_paths(self) -> None:
        self.assertEqual(
            G5_GITHUB_RUNTIME_SCHEMA_ALLOWED_STATUSES,
            {
                ".context/00_INDICE.md": "M",
                ".context/decisiones/ADR-0019_github_runtime_schema_lifecycle.md": "A",
                ".context/estado_del_proyecto.md": "M",
                ".context/operaciones/g5_operational_activation_manifest_2026_08_15.json": "M",
                ".context/operaciones/g5_operational_activation_runbook_2026_08_15.md": "M",
                ".github/workflows/f9-7-contract.yml": "M",
                "scripts/security/f109_boundary.py": "M",
                "scripts/shared/f10_9_g5_get_only_adapter_contract.py": "M",
                "scripts/shared/f10_9_g5_operational_activation_preflight.py": "M",
                "tests/test_fase10_9_branch_reconciliation.py": "M",
                "tests/test_fase10_9_g5_get_only_adapter_contract.py": "M",
                "tests/test_fase10_9_g5_operational_activation_preflight.py": "M",
                "workers/g5-trust-broker/src/index.mjs": "M",
                "workers/g5-trust-broker/test/trust-broker.test.mjs": "M",
            },
        )
        self.assertEqual(set(G5_GITHUB_RUNTIME_SCHEMA_ALLOWED_MODES.values()), {"100644"})

    def test_detect_mode_selects_g5_github_runtime_schema(self) -> None:
        self.assertEqual(
            detect_mode(
                "pull_request", "desarrollo", G5_GITHUB_RUNTIME_SCHEMA_HEAD_REF,
                G5_GITHUB_RUNTIME_SCHEMA_BASE,
            ),
            "g5_github_runtime_schema",
        )
        self.assertEqual(
            detect_mode(
                "pull_request", "desarrollo", G5_GITHUB_RUNTIME_SCHEMA_HEAD_REF,
                "0" * 40,
            ),
            "skip",
        )

    def test_g5_security_remediation_allowlist_is_minimal_pr_j_paths(self) -> None:
        self.assertEqual(
            G5_SECURITY_REMEDIATION_ALLOWED_STATUSES,
            {
                ".context/00_INDICE.md": "M",
                ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
                ".context/decisiones/ADR-0020_g5_runtime_binding_snapshot_cas.md": "A",
                ".context/estado_del_proyecto.md": "M",
                ".context/operaciones/g5_operational_activation_manifest_2026_08_15.json": "M",
                ".context/operaciones/g5_operational_activation_runbook_2026_08_15.md": "M",
                ".github/workflows/f9-7-contract.yml": "M",
                "scripts/security/f109_boundary.py": "M",
                "scripts/shared/f10_9_g5_operational_activation_preflight.py": "M",
                "tests/test_fase10_9_branch_reconciliation.py": "M",
                "tests/test_fase10_9_g5_operational_activation_preflight.py": "M",
                "workers/g5-trust-broker/src/index.mjs": "M",
                "workers/g5-trust-broker/test/trust-broker.test.mjs": "M",
            },
        )
        self.assertEqual(set(G5_SECURITY_REMEDIATION_ALLOWED_MODES.values()), {"100644"})

    def test_detect_mode_selects_g5_security_remediation(self) -> None:
        self.assertEqual(
            detect_mode(
                "pull_request", "desarrollo", G5_SECURITY_REMEDIATION_HEAD_REF,
                G5_SECURITY_REMEDIATION_BASE,
            ),
            "g5_security_remediation",
        )
        self.assertEqual(
            detect_mode(
                "pull_request", "desarrollo", G5_SECURITY_REMEDIATION_HEAD_REF,
                "0" * 40,
            ),
            "skip",
        )

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_g5_security_remediation_accepts_exact_candidate(
        self, require_sha_mock, tree_mock, parents_mock, delta_mock, context_mock,
    ) -> None:
        self.assertEqual(G5_SECURITY_REMEDIATION_BASE, "0672156ae5ea13a3ba40ab5f4fd4fd184ec5811e")
        self.assertEqual(G5_SECURITY_REMEDIATION_BASE_TREE, "7fa8e5c26ddaa67450584b43d5b61c9f7b9edc98")
        self.assertEqual(G5_SECURITY_REMEDIATION_HEAD_REF, "feat/f10-9-pr-j-security-remediation")
        self.assertEqual(G5_SECURITY_REMEDIATION_PR392_CANDIDATE, "b3f9678e0df76ef8f9dfde8af9147a458a2e033b")
        self.assertEqual(G5_SECURITY_REMEDIATION_STATUS, "MERGED_POST_MERGE_VERIFIED_SECURITY_REMEDIATION_REQUIRED")
        self.assertEqual(G5_SECURITY_REMEDIATION_E2_STOP, "E2_STOP_SECURITY_REMEDIATION_REQUIRED")
        head = "a" * 40
        tree_mock.return_value = G5_SECURITY_REMEDIATION_BASE_TREE
        parents_mock.side_effect = lambda _repo, commit: {head: [G5_SECURITY_REMEDIATION_BASE]}[commit]
        repo = self.make_repo()
        source_root = Path(__file__).resolve().parents[1]
        for relative in G5_SECURITY_REMEDIATION_ALLOWED_STATUSES:
            path = repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text((source_root / relative).read_text(encoding="utf-8"), encoding="utf-8")

        validate_g5_security_remediation(repo, G5_SECURITY_REMEDIATION_BASE, head, "pull_request")

        delta_mock.assert_called_once_with(
            repo, G5_SECURITY_REMEDIATION_BASE, head,
            G5_SECURITY_REMEDIATION_ALLOWED_STATUSES,
            G5_SECURITY_REMEDIATION_ALLOWED_MODES,
        )
        context_mock.assert_called_once_with(repo, 77, 428)

    def test_g5_residual_security_remediation_allowlist_is_minimal_pr_k_paths(self) -> None:
        self.assertEqual(
            G5_RESIDUAL_SECURITY_REMEDIATION_ALLOWED_STATUSES,
            {
                ".context/00_INDICE.md": "M",
                ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
                ".context/decisiones/ADR-0021_g5_terminal_confirmation_token_scope.md": "A",
                ".context/estado_del_proyecto.md": "M",
                ".context/operaciones/g5_operational_activation_manifest_2026_08_15.json": "M",
                ".context/operaciones/g5_operational_activation_runbook_2026_08_15.md": "M",
                ".github/workflows/f9-7-contract.yml": "M",
                "scripts/security/f109_boundary.py": "M",
                "scripts/shared/f10_9_g5_operational_activation_preflight.py": "M",
                "tests/test_fase10_9_branch_reconciliation.py": "M",
                "tests/test_fase10_9_g5_operational_activation_preflight.py": "M",
                "workers/g5-trust-broker/src/index.mjs": "M",
                "workers/g5-trust-broker/test/trust-broker.test.mjs": "M",
            },
        )
        self.assertEqual(set(G5_RESIDUAL_SECURITY_REMEDIATION_ALLOWED_MODES.values()), {"100644"})

    def test_detect_mode_selects_g5_residual_security_remediation(self) -> None:
        self.assertEqual(
            detect_mode(
                "pull_request", "desarrollo", G5_RESIDUAL_SECURITY_REMEDIATION_HEAD_REF,
                G5_RESIDUAL_SECURITY_REMEDIATION_BASE,
            ),
            "g5_residual_security_remediation",
        )
        self.assertEqual(
            detect_mode(
                "pull_request", "desarrollo", G5_RESIDUAL_SECURITY_REMEDIATION_HEAD_REF,
                "0" * 40,
            ),
            "skip",
        )

    @mock.patch("scripts.security.f109_boundary.git")
    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_g5_residual_security_remediation_accepts_exact_candidate(
        self, require_sha_mock, tree_mock, parents_mock, delta_mock, context_mock, git_mock,
    ) -> None:
        self.assertEqual(G5_RESIDUAL_SECURITY_REMEDIATION_BASE, "51aaac5d289226b1f8f16de1daf69a16a084d585")
        self.assertEqual(G5_RESIDUAL_SECURITY_REMEDIATION_BASE_TREE, "7e7be8072cc416d76d2034a126d39393cdbcc968")
        self.assertEqual(G5_RESIDUAL_SECURITY_REMEDIATION_HEAD_REF, "feat/f10-9-pr-k-security-remediation")
        self.assertEqual(G5_RESIDUAL_SECURITY_REMEDIATION_PR393_CANDIDATE, "4d5d97bb37ffcd5126d467bde9152e705a895c85")
        self.assertEqual(
            G5_RESIDUAL_SECURITY_REMEDIATION_PR394_COMMITS,
            (
                "7861af0cf94b726d6ce5fadad9ffb6c2274fdcaa",
                "03bab905901f62dba7631a9fe0a87290d70802d9",
                "82ef6e92c125040cededb4a648d1eedd6d519ecf",
            ),
        )
        self.assertEqual(G5_RESIDUAL_SECURITY_REMEDIATION_STATUS, "MERGED_POST_MERGE_VERIFIED_RESIDUAL_REMEDIATION_REQUIRED")
        first, second, head = G5_RESIDUAL_SECURITY_REMEDIATION_PR394_COMMITS
        tree_mock.return_value = G5_RESIDUAL_SECURITY_REMEDIATION_BASE_TREE
        parents_mock.side_effect = lambda _repo, commit: {
            first: [G5_RESIDUAL_SECURITY_REMEDIATION_BASE],
            second: [first],
            head: [second],
        }[commit]
        repo = self.make_repo()
        source_root = Path(__file__).resolve().parents[1]
        for relative in G5_RESIDUAL_SECURITY_REMEDIATION_ALLOWED_STATUSES:
            path = repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text((source_root / relative).read_text(encoding="utf-8"), encoding="utf-8")
        git_mock.side_effect = lambda tree_repo, _command, spec: (
            tree_repo / spec.split(":", 1)[1]
        ).read_text(encoding="utf-8")

        validate_g5_residual_security_remediation(repo, G5_RESIDUAL_SECURITY_REMEDIATION_BASE, head, "pull_request")

        delta_mock.assert_called_once_with(
            repo, G5_RESIDUAL_SECURITY_REMEDIATION_BASE, head,
            G5_RESIDUAL_SECURITY_REMEDIATION_ALLOWED_STATUSES,
            G5_RESIDUAL_SECURITY_REMEDIATION_ALLOWED_MODES,
        )
        context_mock.assert_called_once_with(repo, 78, 429)

    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_g5_residual_security_remediation_rejects_generic_followup_chain(
        self, require_sha_mock, tree_mock, parents_mock,
    ) -> None:
        head = "a" * 40
        prior = "b" * 40
        tree_mock.return_value = G5_RESIDUAL_SECURITY_REMEDIATION_BASE_TREE
        parents_mock.side_effect = lambda _repo, commit: {
            head: [prior],
            prior: [G5_RESIDUAL_SECURITY_REMEDIATION_BASE],
        }[commit]

        with self.assertRaises(BoundaryError):
            validate_g5_residual_security_remediation(
                Path("."),
                G5_RESIDUAL_SECURITY_REMEDIATION_BASE,
                head,
                "pull_request",
            )

    def test_g5_followup_security_remediation_allowlist_is_minimal_pr_l_paths(self) -> None:
        self.assertEqual(
            G5_FOLLOWUP_SECURITY_REMEDIATION_ALLOWED_STATUSES,
            {
                ".context/00_INDICE.md": "M",
                ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
                ".context/decisiones/ADR-0022_g5_followup_security_remediation.md": "A",
                ".context/estado_del_proyecto.md": "M",
                ".context/operaciones/g5_operational_activation_manifest_2026_08_15.json": "M",
                ".context/operaciones/g5_operational_activation_runbook_2026_08_15.md": "M",
                ".context/operaciones/plan_remediacion_f10_9_fg2_fg3.md": "M",
                ".github/workflows/f9-7-contract.yml": "M",
                "scripts/security/f109_boundary.py": "M",
                "scripts/shared/f10_9_g5_operational_activation_preflight.py": "M",
                "tests/test_fase10_9_branch_reconciliation.py": "M",
                "tests/test_fase10_9_g5_operational_activation_preflight.py": "M",
                "workers/g5-trust-broker/src/index.mjs": "M",
                "workers/g5-trust-broker/test/trust-broker.test.mjs": "M",
            },
        )
        self.assertEqual(set(G5_FOLLOWUP_SECURITY_REMEDIATION_ALLOWED_MODES.values()), {"100644"})

    def test_detect_mode_selects_g5_followup_security_remediation(self) -> None:
        self.assertEqual(
            detect_mode(
                "pull_request", "desarrollo", G5_FOLLOWUP_SECURITY_REMEDIATION_HEAD_REF,
                G5_FOLLOWUP_SECURITY_REMEDIATION_BASE,
            ),
            "g5_followup_security_remediation",
        )
        self.assertEqual(
            detect_mode(
                "pull_request", "desarrollo", G5_FOLLOWUP_SECURITY_REMEDIATION_HEAD_REF,
                "0" * 40,
            ),
            "skip",
        )

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_g5_followup_security_remediation_accepts_one_direct_candidate(
        self, require_sha_mock, tree_mock, parents_mock, delta_mock, context_mock,
    ) -> None:
        self.assertEqual(G5_FOLLOWUP_SECURITY_REMEDIATION_BASE, "25be9caffe5674156c7515735a15ad45c5ad22e2")
        self.assertEqual(G5_FOLLOWUP_SECURITY_REMEDIATION_BASE_TREE, "9f81f71bdabb2012ab593b1999cf4df92fa712eb")
        self.assertEqual(G5_FOLLOWUP_SECURITY_REMEDIATION_HEAD_REF, "feat/f10-9-pr-l-security-remediation")
        self.assertEqual(G5_FOLLOWUP_SECURITY_REMEDIATION_STATUS, "MERGED_POST_MERGE_VERIFIED_FOLLOWUP_SECURITY_REMEDIATION_REQUIRED")
        self.assertEqual(G5_FOLLOWUP_SECURITY_REMEDIATION_E2_STOP, "E2_STOP_FOLLOWUP_SECURITY_REMEDIATION_REQUIRED")
        head = "a" * 40
        tree_mock.return_value = G5_FOLLOWUP_SECURITY_REMEDIATION_BASE_TREE
        parents_mock.return_value = [G5_FOLLOWUP_SECURITY_REMEDIATION_BASE]
        repo = self.make_repo()
        source_root = Path(__file__).resolve().parents[1]
        for relative in G5_FOLLOWUP_SECURITY_REMEDIATION_ALLOWED_STATUSES:
            path = repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text((source_root / relative).read_text(encoding="utf-8"), encoding="utf-8")

        validate_g5_followup_security_remediation(repo, G5_FOLLOWUP_SECURITY_REMEDIATION_BASE, head, "pull_request")

        delta_mock.assert_called_once_with(
            repo, G5_FOLLOWUP_SECURITY_REMEDIATION_BASE, head,
            G5_FOLLOWUP_SECURITY_REMEDIATION_ALLOWED_STATUSES,
            G5_FOLLOWUP_SECURITY_REMEDIATION_ALLOWED_MODES,
        )
        context_mock.assert_called_once_with(repo, 79, 430)

    def test_g5_trusted_boundary_bootstrap_allowlist_is_minimal_pr_m_paths(self) -> None:
        self.assertEqual(
            G5_TRUSTED_BOUNDARY_BOOTSTRAP_ALLOWED_STATUSES,
            {
                ".context/00_INDICE.md": "M",
                ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
                ".context/decisiones/ADR-0023_g5_trusted_boundary_bootstrap.md": "A",
                ".context/estado_del_proyecto.md": "M",
                ".context/operaciones/g5_operational_activation_manifest_2026_08_15.json": "M",
                ".context/operaciones/g5_operational_activation_runbook_2026_08_15.md": "M",
                ".context/operaciones/plan_remediacion_f10_9_fg2_fg3.md": "M",
                ".github/workflows/f10-9-g5-trusted-boundary-bootstrap.yml": "A",
                ".github/workflows/f9-7-contract.yml": "M",
                "scripts/security/f109_boundary.py": "M",
                "scripts/security/f109_trusted_boundary_bootstrap.py": "A",
                "scripts/shared/f10_9_g5_operational_activation_preflight.py": "M",
                "tests/test_f109_trusted_boundary_bootstrap.py": "A",
                "tests/test_fase10_9_branch_reconciliation.py": "M",
                "tests/test_fase10_9_g5_operational_activation_preflight.py": "M",
            },
        )
        self.assertEqual(set(G5_TRUSTED_BOUNDARY_BOOTSTRAP_ALLOWED_MODES.values()), {"100644"})

    def test_detect_mode_selects_g5_trusted_boundary_bootstrap(self) -> None:
        self.assertEqual(
            detect_mode(
                "pull_request", "desarrollo", G5_TRUSTED_BOUNDARY_BOOTSTRAP_HEAD_REF,
                G5_TRUSTED_BOUNDARY_BOOTSTRAP_BASE,
            ),
            "g5_trusted_boundary_bootstrap",
        )
        self.assertEqual(
            detect_mode(
                "pull_request", "desarrollo", G5_TRUSTED_BOUNDARY_BOOTSTRAP_HEAD_REF,
                "0" * 40,
            ),
            "skip",
        )

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_g5_trusted_boundary_bootstrap_accepts_one_direct_candidate(
        self, require_sha_mock, tree_mock, parents_mock, delta_mock, context_mock,
    ) -> None:
        self.assertEqual(G5_TRUSTED_BOUNDARY_BOOTSTRAP_BASE, "d04a174915910f50b8adf3d4d4b1216ffbc90b75")
        self.assertEqual(G5_TRUSTED_BOUNDARY_BOOTSTRAP_BASE_TREE, "b30329f66ad8b8ba36e6cbd51303bd8e729036a0")
        self.assertEqual(G5_TRUSTED_BOUNDARY_BOOTSTRAP_HEAD_REF, "feat/f10-9-pr-m-trusted-boundary-bootstrap")
        self.assertEqual(G5_TRUSTED_BOUNDARY_BOOTSTRAP_STATUS, "MERGED_POST_MERGE_VERIFIED_TRUSTED_BOUNDARY_BOOTSTRAP_REQUIRED")
        self.assertEqual(G5_TRUSTED_BOUNDARY_BOOTSTRAP_PR395_CANDIDATE, "444c674cf2ff2143bb4b511e88ff6cd30c1fb589")
        self.assertEqual(G5_TRUSTED_BOUNDARY_BOOTSTRAP_E2_STOP, "E2_STOP_TRUSTED_BOUNDARY_BOOTSTRAP_REQUIRED")
        head = "a" * 40
        tree_mock.return_value = G5_TRUSTED_BOUNDARY_BOOTSTRAP_BASE_TREE
        parents_mock.return_value = [G5_TRUSTED_BOUNDARY_BOOTSTRAP_BASE]
        repo = self.make_repo()
        source_root = Path(__file__).resolve().parents[1]
        for relative in G5_TRUSTED_BOUNDARY_BOOTSTRAP_ALLOWED_STATUSES:
            path = repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text((source_root / relative).read_text(encoding="utf-8"), encoding="utf-8")

        validate_g5_trusted_boundary_bootstrap(repo, G5_TRUSTED_BOUNDARY_BOOTSTRAP_BASE, head, "pull_request")

        delta_mock.assert_called_once_with(
            repo, G5_TRUSTED_BOUNDARY_BOOTSTRAP_BASE, head,
            G5_TRUSTED_BOUNDARY_BOOTSTRAP_ALLOWED_STATUSES,
            G5_TRUSTED_BOUNDARY_BOOTSTRAP_ALLOWED_MODES,
        )
        context_mock.assert_called_once_with(repo, 80, 431)

    def test_g5_trusted_boundary_hardening_allowlist_is_minimal_pr_m2_paths(self) -> None:
        self.assertEqual(
            G5_TRUSTED_BOUNDARY_HARDENING_ALLOWED_STATUSES,
            {
                ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
                ".context/estado_del_proyecto.md": "M",
                ".context/operaciones/g5_operational_activation_manifest_2026_08_15.json": "M",
                ".context/operaciones/g5_operational_activation_runbook_2026_08_15.md": "M",
                ".context/operaciones/g5_trusted_required_check_payload_sanitized_2026_08_16.json": "A",
                ".context/operaciones/plan_remediacion_f10_9_fg2_fg3.md": "M",
                ".github/workflows/f10-9-g5-trusted-boundary-bootstrap.yml": "M",
                "scripts/security/f109_boundary.py": "M",
                "scripts/security/f109_trusted_boundary_bootstrap.py": "M",
                "scripts/shared/f10_9_g5_operational_activation_preflight.py": "M",
                "tests/test_f109_trusted_boundary_bootstrap.py": "M",
                "tests/test_fase10_9_branch_reconciliation.py": "M",
                "tests/test_fase10_9_g5_operational_activation_preflight.py": "M",
            },
        )
        self.assertEqual(set(G5_TRUSTED_BOUNDARY_HARDENING_ALLOWED_MODES.values()), {"100644"})

    def test_detect_mode_selects_g5_trusted_boundary_hardening(self) -> None:
        self.assertEqual(
            detect_mode(
                "pull_request", "desarrollo", G5_TRUSTED_BOUNDARY_HARDENING_HEAD_REF,
                G5_TRUSTED_BOUNDARY_HARDENING_BASE,
            ),
            "g5_trusted_boundary_hardening",
        )
        self.assertEqual(
            detect_mode(
                "pull_request", "desarrollo", G5_TRUSTED_BOUNDARY_HARDENING_HEAD_REF,
                "0" * 40,
            ),
            "skip",
        )

    @mock.patch("scripts.security.f109_boundary.is_ancestor")
    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_g5_trusted_boundary_hardening_accepts_one_direct_candidate(
        self, require_sha_mock, tree_mock, parents_mock, delta_mock, context_mock, ancestor_mock,
    ) -> None:
        self.assertEqual(G5_TRUSTED_BOUNDARY_HARDENING_BASE, "0ec3da6c77b7819a38adcd2f38cd81699adc9283")
        self.assertEqual(G5_TRUSTED_BOUNDARY_HARDENING_BASE_TREE, "ecbe760d50f06d0edce0f36ef84fabacb0a4037c")
        self.assertEqual(G5_TRUSTED_BOUNDARY_HARDENING_HEAD_REF, "feat/f10-9-pr-m2-trusted-boundary-hardening")
        self.assertEqual(G5_TRUSTED_BOUNDARY_HARDENING_STATUS, "MERGED_POST_MERGE_VERIFIED_TRUSTED_BOUNDARY_HARDENING_REQUIRED")
        self.assertEqual(G5_TRUSTED_BOUNDARY_HARDENING_PR396_CANDIDATE, "063fb88b3b3dabda78ea641f46da69af09058ab7")
        self.assertEqual(G5_TRUSTED_BOUNDARY_HARDENING_E2_STOP, "E2_STOP_TRUSTED_BOUNDARY_HARDENING_REQUIRED")
        self.assertEqual(G5_TRUSTED_BOUNDARY_PR_N_CHECK_NAME, "F10.9 Trusted Boundary PR N v1")
        head = "a" * 40
        tree_mock.return_value = G5_TRUSTED_BOUNDARY_HARDENING_BASE_TREE
        parents_mock.return_value = [G5_TRUSTED_BOUNDARY_HARDENING_BASE]
        ancestor_mock.return_value = True
        repo = self.make_repo()
        source_root = Path(__file__).resolve().parents[1]
        for relative in G5_TRUSTED_BOUNDARY_HARDENING_ALLOWED_STATUSES:
            path = repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text((source_root / relative).read_text(encoding="utf-8"), encoding="utf-8")

        validate_g5_trusted_boundary_hardening(repo, G5_TRUSTED_BOUNDARY_HARDENING_BASE, head, "pull_request")

        delta_mock.assert_called_once_with(
            repo, G5_TRUSTED_BOUNDARY_HARDENING_BASE, head,
            G5_TRUSTED_BOUNDARY_HARDENING_ALLOWED_STATUSES,
            G5_TRUSTED_BOUNDARY_HARDENING_ALLOWED_MODES,
        )
        context_mock.assert_called_once_with(repo, 80, 431)
        ancestor_mock.assert_called_once_with(repo, G5_TRUSTED_BOUNDARY_HARDENING_BASE, head)

    def test_g5_link_hardening_closure_allowlist_matches_pr_n_profile(self) -> None:
        self.assertEqual(G5_LINK_HARDENING_CLOSURE_BASE, "9a5fcf539c69b635a41616e52716c0ee34837df4")
        self.assertEqual(G5_LINK_HARDENING_CLOSURE_BASE_TREE, "b33228a031312062b165f8f612d27eacee2fea00")
        self.assertEqual(G5_LINK_HARDENING_CLOSURE_HEAD_REF, "feat/f10-9-pr-n-link-hardening-closure")
        self.assertEqual(G5_LINK_HARDENING_CLOSURE_STATUS, "CLOSED_BY_PR_N_TRUSTED_BOUNDARY")
        self.assertEqual(G5_LINK_HARDENING_CLOSURE_E2_STOP, "E2_STOP_TRUSTED_BOUNDARY_REQUIRED_CHECK_APPROVAL_PENDING")
        self.assertEqual(G5_LINK_HARDENING_CLOSURE_PR397_CANDIDATE, "8adede3ed10605f3af36e905d8f11e7489815d8a")
        self.assertEqual(G5_LINK_HARDENING_CLOSURE_ALLOWED_STATUSES, {
            ".context/00_INDICE.md": "M",
            ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
            ".context/decisiones/ADR-0024_g5_link_header_hardening_closure.md": "A",
            ".context/estado_del_proyecto.md": "M",
            ".context/operaciones/g5_operational_activation_manifest_2026_08_15.json": "M",
            ".context/operaciones/g5_operational_activation_runbook_2026_08_15.md": "M",
            ".context/operaciones/plan_remediacion_f10_9_fg2_fg3.md": "M",
            "scripts/security/f109_boundary.py": "M",
            "scripts/shared/f10_9_g5_operational_activation_preflight.py": "M",
            "tests/test_fase10_9_branch_reconciliation.py": "M",
            "tests/test_fase10_9_g5_operational_activation_preflight.py": "M",
            "workers/g5-trust-broker/src/index.mjs": "M",
            "workers/g5-trust-broker/test/trust-broker.test.mjs": "M",
        })
        self.assertEqual(set(G5_LINK_HARDENING_CLOSURE_ALLOWED_MODES.values()), {"100644"})

    def test_detect_mode_selects_g5_link_hardening_closure(self) -> None:
        self.assertEqual(
            detect_mode(
                "pull_request", "desarrollo", G5_LINK_HARDENING_CLOSURE_HEAD_REF,
                G5_LINK_HARDENING_CLOSURE_BASE,
            ),
            "g5_link_hardening_closure",
        )
        self.assertEqual(
            detect_mode(
                "pull_request", "desarrollo", G5_LINK_HARDENING_CLOSURE_HEAD_REF,
                "0" * 40,
            ),
            "skip",
        )

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_g5_link_hardening_closure_accepts_one_direct_candidate(
        self, require_sha_mock, tree_mock, parents_mock, delta_mock, context_mock,
    ) -> None:
        head = "a" * 40
        tree_mock.return_value = G5_LINK_HARDENING_CLOSURE_BASE_TREE
        parents_mock.return_value = [G5_LINK_HARDENING_CLOSURE_BASE]
        repo = self.make_repo()
        source_root = Path(__file__).resolve().parents[1]
        for relative in G5_LINK_HARDENING_CLOSURE_ALLOWED_STATUSES:
            path = repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text((source_root / relative).read_text(encoding="utf-8"), encoding="utf-8")

        validate_g5_link_hardening_closure(repo, G5_LINK_HARDENING_CLOSURE_BASE, head, "pull_request")

        delta_mock.assert_called_once_with(
            repo, G5_LINK_HARDENING_CLOSURE_BASE, head,
            G5_LINK_HARDENING_CLOSURE_ALLOWED_STATUSES,
            G5_LINK_HARDENING_CLOSURE_ALLOWED_MODES,
        )
        context_mock.assert_called_once_with(repo, 81, 432)

    def test_g5_default_branch_trusted_workflow_allowlist_matches_pr_o_profile(self) -> None:
        self.assertEqual(G5_DEFAULT_BRANCH_TRUSTED_WORKFLOW_BASE, "85d7f647a37dc784fe16c11da0318956e255b698")
        self.assertEqual(G5_DEFAULT_BRANCH_TRUSTED_WORKFLOW_BASE_TREE, "91706dfcc3766fbf69b4fb8c893318786445a2a9")
        self.assertEqual(G5_DEFAULT_BRANCH_TRUSTED_WORKFLOW_HEAD_REF, "feat/f10-9-pr-o-default-branch-registration")
        self.assertEqual(G5_DEFAULT_BRANCH_TRUSTED_WORKFLOW_STATUS, "MERGED_POST_MERGE_VERIFIED_TRUSTED_ATTESTATION_MISSING_DEFAULT_BRANCH_REGISTRATION_REQUIRED")
        self.assertEqual(G5_DEFAULT_BRANCH_TRUSTED_WORKFLOW_E2_STOP, "E2_STOP_DEFAULT_BRANCH_TRUSTED_WORKFLOW_REGISTRATION_REQUIRED")
        self.assertEqual(G5_DEFAULT_BRANCH_TRUSTED_WORKFLOW_PR398_CANDIDATE, "d03ee28ce90abcbf8efd7c4b37de99b72717207e")
        self.assertEqual(G5_DEFAULT_BRANCH_TRUSTED_WORKFLOW_ALLOWED_STATUSES, {
            ".context/00_INDICE.md": "M",
            ".context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md": "M",
            ".context/decisiones/ADR-0025_g5_default_branch_trusted_workflow_registration.md": "A",
            ".context/estado_del_proyecto.md": "M",
            ".context/operaciones/g5_operational_activation_manifest_2026_08_15.json": "M",
            ".context/operaciones/g5_operational_activation_runbook_2026_08_15.md": "M",
            ".context/operaciones/g5_trusted_boundary_pr_p_probe_2026_08_17.md": "A",
            ".context/operaciones/g5_trusted_workflow_default_branch_promotion_sanitized_2026_08_17.json": "A",
            ".context/operaciones/plan_remediacion_f10_9_fg2_fg3.md": "M",
            ".github/workflows/f10-9-g5-trusted-boundary-bootstrap.yml": "M",
            "scripts/security/f109_boundary.py": "M",
            "scripts/security/f109_trusted_boundary_bootstrap.py": "M",
            "scripts/shared/f10_9_g5_operational_activation_preflight.py": "M",
            "tests/test_f109_trusted_boundary_bootstrap.py": "M",
            "tests/test_fase10_9_branch_reconciliation.py": "M",
            "tests/test_fase10_9_g5_operational_activation_preflight.py": "M",
        })
        self.assertEqual(set(G5_DEFAULT_BRANCH_TRUSTED_WORKFLOW_ALLOWED_MODES.values()), {"100644"})

    def test_detect_mode_selects_g5_default_branch_trusted_workflow_registration(self) -> None:
        self.assertEqual(
            detect_mode(
                "pull_request", "desarrollo", G5_DEFAULT_BRANCH_TRUSTED_WORKFLOW_HEAD_REF,
                G5_DEFAULT_BRANCH_TRUSTED_WORKFLOW_BASE,
            ),
            "g5_default_branch_trusted_workflow_registration",
        )

    @mock.patch("scripts.security.f109_boundary.validate_context_graph")
    @mock.patch("scripts.security.f109_boundary.require_exact_delta")
    @mock.patch("scripts.security.f109_boundary.commit_parents")
    @mock.patch("scripts.security.f109_boundary.commit_tree")
    @mock.patch("scripts.security.f109_boundary.require_sha")
    def test_g5_default_branch_trusted_workflow_accepts_one_direct_candidate(
        self, require_sha_mock, tree_mock, parents_mock, delta_mock, context_mock,
    ) -> None:
        head = "a" * 40
        tree_mock.return_value = G5_DEFAULT_BRANCH_TRUSTED_WORKFLOW_BASE_TREE
        parents_mock.return_value = [G5_DEFAULT_BRANCH_TRUSTED_WORKFLOW_BASE]
        repo = self.make_repo()
        source_root = Path(__file__).resolve().parents[1]
        for relative in G5_DEFAULT_BRANCH_TRUSTED_WORKFLOW_ALLOWED_STATUSES:
            path = repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text((source_root / relative).read_text(encoding="utf-8"), encoding="utf-8")

        validate_g5_default_branch_trusted_workflow_registration(
            repo, G5_DEFAULT_BRANCH_TRUSTED_WORKFLOW_BASE, head, "pull_request"
        )

        delta_mock.assert_called_once_with(
            repo, G5_DEFAULT_BRANCH_TRUSTED_WORKFLOW_BASE, head,
            G5_DEFAULT_BRANCH_TRUSTED_WORKFLOW_ALLOWED_STATUSES,
            G5_DEFAULT_BRANCH_TRUSTED_WORKFLOW_ALLOWED_MODES,
        )
        context_mock.assert_called_once_with(repo, 83, 433)

    @mock.patch("scripts.security.f109_boundary.parse_args")
    def test_cli_rejects_g5_github_runtime_schema_from_wrong_base(self, parse_args_mock) -> None:
        parse_args_mock.return_value = SimpleNamespace(
            repo=Path("."),
            event="pull_request",
            base_ref="desarrollo",
            head_ref=G5_GITHUB_RUNTIME_SCHEMA_HEAD_REF,
            base_sha="0" * 40,
            head_sha="1" * 40,
            base_repo="owner/repo",
            head_repo="owner/repo",
            cert_tip="",
            p1_base="",
            p1_base_tree="",
            p2_base="",
            p2_base_tree="",
            g2_base="",
            g2_base_tree="",
            p5_base="",
            p5_base_tree="",
            f1010_m1_base="",
            f1010_m1_base_tree="",
            github_output="",
        )

        self.assertEqual(main(), 1)

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
        for head_ref in (
            F1010_M2A_HEAD_REF,
            F1010_M1_HEAD_REF,
            F1010_M3_PUBLIC_ACL_V3_BOUND_HEAD_REF,
            F1010_H1_CA1_REBASELINE_HEAD_REF,
        ):
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
