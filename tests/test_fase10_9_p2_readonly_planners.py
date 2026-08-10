from __future__ import annotations

import ast
import copy
import io
import json
import random
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from scripts.shared import f10_9_readonly_planner as planner
from scripts.maintenance.f10_9_readonly_audit import DEFAULT_FIXTURE, main
from scripts.shared.f10_9_readonly_planner import (
    INPUT_SCHEMA,
    MANIFEST_SCHEMA,
    PlannerInputError,
    build_readonly_manifest,
    canonical_json,
    fingerprint,
    load_snapshot,
)
from scripts.shared.url_identity import URL_IDENTITY_VERSION


ROOT = Path(__file__).resolve().parents[1]


class F109P2ReadonlyPlannerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.snapshot = load_snapshot(DEFAULT_FIXTURE)

    def test_fixture_manifest_is_deterministic_and_read_only(self) -> None:
        original = copy.deepcopy(self.snapshot)
        first = build_readonly_manifest(self.snapshot)
        second = build_readonly_manifest(self.snapshot)

        self.assertEqual(first, second)
        self.assertEqual(self.snapshot, original)
        self.assertEqual(first["schema"], MANIFEST_SCHEMA)
        self.assertEqual(first["mode"], "LOCAL_OFFLINE_READ_ONLY")
        self.assertEqual(first["writes"], {"actual": 0, "expected": 0, "planned": 0})
        self.assertEqual(
            first["capabilities"],
            {"apply": False, "database": False, "http": False, "providers": False},
        )
        self.assertFalse(first["decision"]["next_gate_eligible"])
        self.assertEqual(first["decision"]["repeat_semantics"], "IDENTICAL_INPUT_NOOP")
        self.assertEqual(first["decision"]["result"], "STOP_REQUIRES_REBASELINE")
        self.assertEqual(first["provenance"]["candidate_binding"], "UNBOUND_LOCAL_IMPLEMENTATION")
        self.assertEqual(
            first["provenance"]["candidate_contract"]["expected_paths"],
            [
                "scripts/maintenance/f10_9_readonly_audit.py",
                "scripts/shared/f10_9_readonly_planner.py",
                "tests/fixtures/f10_9_p2_synthetic.json",
                "tests/test_fase10_9_p2_readonly_planners.py",
            ],
        )
        self.assertTrue(all(item["delta"] == 0 for item in first["before_after"].values()))

    def test_expected_duplicate_and_lifecycle_classifications(self) -> None:
        manifest = build_readonly_manifest(self.snapshot)

        self.assertEqual(manifest["deduplication"]["duplicate_groups"], 2)
        self.assertEqual(manifest["deduplication"]["excess_rows"], 2)
        self.assertEqual(manifest["deduplication"]["survivors_identified"], 1)
        self.assertEqual(manifest["deduplication"]["hold_manual_groups"], 1)
        self.assertEqual(manifest["lifecycle"]["stale_processing"], 5)
        self.assertEqual(
            manifest["lifecycle"]["classifications"],
            {
                "CANDIDATE_DISCOVERED": 1,
                "CANDIDATE_PENDING": 1,
                "CANDIDATE_PROCESSED": 1,
                "HOLD_DEPENDENCY_CONFLICT": 1,
                "HOLD_MANUAL": 2,
            },
        )
        self.assertEqual(manifest["lifecycle"]["planned_transitions"], 0)

    def test_reason_codes_cover_required_g1_findings(self) -> None:
        reasons = build_readonly_manifest(self.snapshot)["reason_counts"]
        for code in (
            "DUPLICATE_NORMALIZED_URL",
            "STALE_PROCESSING",
            "CONFLICTING_CONTENT_HASH",
            "DOWNSTREAM_REFERENCE_CONFLICT",
            "INVALID_EMPTY_HARDCODED_PROFILE",
            "SOURCE_ACCESS_403",
            "SOURCE_TIMEOUT",
        ):
            with self.subTest(code=code):
                self.assertGreater(reasons.get(code, 0), 0)

    def test_metadata_counts_null_blank_and_versioned_placeholders(self) -> None:
        metadata = build_readonly_manifest(self.snapshot)["metadata"]
        self.assertEqual(metadata["active_courses"], 4)
        self.assertEqual(metadata["incomplete_active_courses"], 3)
        self.assertEqual(metadata["missing_syllabus"], 2)
        self.assertEqual(metadata["missing_objectives"], 2)
        self.assertEqual(metadata["missing_both"], 1)
        self.assertEqual(metadata["planned_enrichment_calls"], 0)

    def test_metadata_placeholder_matching_is_exact_not_substring(self) -> None:
        snapshot = copy.deepcopy(self.snapshot)
        snapshot["courses"][0]["syllabus"] = "Information is not available in this excerpt"
        metadata = build_readonly_manifest(snapshot)["metadata"]
        self.assertEqual(metadata["missing_syllabus"], 1)

    def test_prior_mutation_2xx_stops_without_restoration(self) -> None:
        snapshot = copy.deepcopy(self.snapshot)
        snapshot["prior_mutation_checks"][0]["observed_outcome"] = "HTTP_2XX"
        manifest = build_readonly_manifest(snapshot)

        self.assertEqual(manifest["decision"]["result"], "STOP_REQUIRES_REBASELINE")
        self.assertEqual(manifest["prior_mutations"]["planned_restorations"], 0)
        self.assertEqual(manifest["prior_mutations"]["STOP_REQUIRES_REBASELINE"], 1)

    def test_prior_mutation_inconclusive_holds_without_write(self) -> None:
        snapshot = copy.deepcopy(self.snapshot)
        snapshot["prior_mutation_checks"][0]["observed_outcome"] = "INCONCLUSIVE"
        manifest = build_readonly_manifest(snapshot)
        self.assertEqual(manifest["prior_mutations"]["HOLD_MANUAL"], 1)
        self.assertEqual(manifest["writes"]["actual"], 0)

    def test_prior_mutation_state_must_match_mutation_kind(self) -> None:
        snapshot = copy.deepcopy(self.snapshot)
        snapshot["prior_mutation_checks"][2]["course_id"] = "c-05"
        manifest = build_readonly_manifest(snapshot)
        self.assertEqual(manifest["prior_mutations"]["HOLD_MANUAL"], 1)
        self.assertEqual(manifest["reason_counts"]["PRIOR_MUTATION_STATE_CONFLICT"], 1)

    def test_prior_mutation_2xx_remains_stop_when_state_is_inconsistent(self) -> None:
        cases = ((0, "c-01", "last_404_at", None), (2, "c-04", "is_active", True))
        for index, course_id, field, value in cases:
            snapshot = copy.deepcopy(self.snapshot)
            snapshot["prior_mutation_checks"][index]["observed_outcome"] = "HTTP_2XX"
            course = next(item for item in snapshot["courses"] if item["id"] == course_id)
            course[field] = value
            manifest = build_readonly_manifest(snapshot)
            with self.subTest(mutation_index=index):
                self.assertEqual(manifest["decision"]["result"], "STOP_REQUIRES_REBASELINE")
                self.assertGreater(manifest["reason_counts"]["PRIOR_MUTATION_RECOVERY_REQUIRED"], 0)
                self.assertGreater(manifest["reason_counts"]["PRIOR_MUTATION_STATE_CONFLICT"], 0)

    def test_input_order_does_not_change_manifest(self) -> None:
        shuffled = copy.deepcopy(self.snapshot)
        random.Random(20260810).shuffle(shuffled["staging_raw"])
        random.Random(20260811).shuffle(shuffled["courses"])
        self.assertEqual(
            build_readonly_manifest(self.snapshot),
            build_readonly_manifest(shuffled),
        )

    def test_page_size_only_changes_pages_processed(self) -> None:
        small = build_readonly_manifest(self.snapshot, page_size=1)
        large = build_readonly_manifest(self.snapshot, page_size=1000)
        self.assertEqual(small["reason_counts"], large["reason_counts"])
        self.assertEqual(small["lifecycle"], large["lifecycle"])
        self.assertEqual(small["deduplication"], large["deduplication"])
        for name in small["pagination"]:
            self.assertEqual(
                small["pagination"][name]["cohort_fingerprint"],
                large["pagination"][name]["cohort_fingerprint"],
            )

    def test_more_than_one_thousand_rows_are_fully_paginated(self) -> None:
        snapshot = copy.deepcopy(self.snapshot)
        snapshot["staging_raw"] = [
            {
                "id": f"s-bulk-{index:04d}",
                "institution_id": "i-01",
                "url": f"https://example.invalid/bulk/{index}",
                "status": "pending",
                "payload": "payload-valid",
                "content_hash": "920cf4f620dc8e329c6647fb8652aa5dd9dc15726db242560c1ca008ef78782b",
                "processing_since": None,
                "created_at": "2026-08-09T00:00:00Z",
            }
            for index in range(1005)
        ]
        snapshot["downstream_references"] = []
        with mock.patch.object(planner, "_iter_pages", wraps=planner._iter_pages) as paginate:
            manifest = build_readonly_manifest(snapshot, page_size=1000)
        self.assertEqual(manifest["pagination"]["staging_raw"]["rows"], 1005)
        self.assertEqual(manifest["pagination"]["staging_raw"]["pages_processed"], 2)
        self.assertGreater(paginate.call_count, 6)

    def test_concurrent_planners_are_identical(self) -> None:
        with ThreadPoolExecutor(max_workers=2) as executor:
            manifests = list(executor.map(build_readonly_manifest, [self.snapshot, self.snapshot]))
        self.assertEqual(manifests[0], manifests[1])

    def test_survivor_ranking_prefers_downstream_reference(self) -> None:
        manifest = build_readonly_manifest(self.snapshot)
        survivor_groups = [
            group
            for group in manifest["deduplication"]["groups"]
            if group["decision"] == "SURVIVOR_IDENTIFIED_READ_ONLY"
        ]
        self.assertEqual(len(survivor_groups), 1)
        self.assertEqual(survivor_groups[0]["loser_count"], 1)
        self.assertIsNotNone(survivor_groups[0]["survivor_fingerprint"])

    def test_oldest_attributable_timestamp_precedes_id_tiebreaker(self) -> None:
        snapshot = copy.deepcopy(self.snapshot)
        base = copy.deepcopy(snapshot["staging_raw"][-1])
        base.update({"id": "s-tie-b", "url": "https://example.invalid/tie", "created_at": "2026-08-01T00:00:00Z"})
        peer = copy.deepcopy(base)
        peer.update({"id": "s-tie-a", "created_at": "2026-08-09T00:00:00Z"})
        snapshot["staging_raw"].extend([base, peer])

        manifest = build_readonly_manifest(snapshot)
        resolved = [
            group
            for group in manifest["deduplication"]["groups"]
            if group["decision"] == "SURVIVOR_IDENTIFIED_READ_ONLY"
        ]
        expected = build_readonly_manifest({
            **snapshot,
            "staging_raw": list(reversed(snapshot["staging_raw"])),
        })
        self.assertEqual(manifest, expected)
        self.assertEqual(len(resolved), 2)
        self.assertIn(
            fingerprint(
                {
                    "cohort_context": manifest["input"]["cohort_fingerprint"],
                    "kind": "staging",
                    "id": "s-tie-b",
                },
                domain="entity",
            ),
            {group["survivor_fingerprint"] for group in resolved},
        )

    def test_standalone_and_duplicate_payload_hash_conflicts_are_blocking(self) -> None:
        standalone = copy.deepcopy(self.snapshot)
        standalone["staging_raw"][-1]["content_hash"] = standalone["staging_raw"][0]["content_hash"]
        manifest = build_readonly_manifest(standalone)
        self.assertGreater(manifest["reason_counts"]["CONFLICTING_CONTENT_HASH"], 1)
        self.assertGreater(manifest["evidence_holds"]["PAYLOAD_HASH_CONTRADICTION"], 1)

        duplicate = copy.deepcopy(self.snapshot)
        duplicate["staging_raw"][3]["content_hash"] = duplicate["staging_raw"][0]["content_hash"]
        manifest = build_readonly_manifest(duplicate)
        self.assertEqual(manifest["deduplication"]["hold_manual_groups"], 1)
        self.assertEqual(manifest["deduplication"]["survivors_identified"], 1)

    def test_unresolved_lifecycle_statuses_cannot_be_survivors(self) -> None:
        snapshot = copy.deepcopy(self.snapshot)
        first = copy.deepcopy(snapshot["staging_raw"][-1])
        first.update({"id": "s-error-a", "url": "https://example.invalid/error-group", "status": "error"})
        second = copy.deepcopy(first)
        second.update({"id": "s-error-b", "status": "skipped"})
        snapshot["staging_raw"].extend([first, second])
        manifest = build_readonly_manifest(snapshot)
        self.assertEqual(manifest["reason_counts"]["INELIGIBLE_SURVIVOR_STATUS"], 1)
        self.assertEqual(manifest["deduplication"]["hold_manual_groups"], 2)

        standalone = copy.deepcopy(self.snapshot)
        row = copy.deepcopy(standalone["staging_raw"][-1])
        row.update({"id": "s-error-only", "url": "https://example.invalid/error-only", "status": "error"})
        standalone["staging_raw"].append(row)
        manifest = build_readonly_manifest(standalone)
        self.assertEqual(manifest["reason_counts"]["UNRESOLVED_STAGING_STATUS"], 1)
        self.assertGreater(manifest["evidence_holds"]["HOLD_MANUAL"], 0)

    def test_cross_institution_identity_is_dependency_hold(self) -> None:
        snapshot = copy.deepcopy(self.snapshot)
        peer = copy.deepcopy(snapshot["staging_raw"][-1])
        peer.update({"id": "s-cross", "institution_id": "i-02"})
        snapshot["staging_raw"].append(peer)
        manifest = build_readonly_manifest(snapshot)
        self.assertEqual(manifest["deduplication"]["hold_dependency_groups"], 1)

    def test_future_processing_timestamp_is_manual_hold(self) -> None:
        snapshot = copy.deepcopy(self.snapshot)
        snapshot["staging_raw"][9]["processing_since"] = "2026-08-11T00:00:00Z"
        manifest = build_readonly_manifest(snapshot)
        self.assertEqual(manifest["reason_counts"]["PROCESSING_TIME_IN_FUTURE"], 1)
        self.assertEqual(manifest["lifecycle"]["classifications"]["HOLD_MANUAL"], 3)

    def test_invalid_identity_is_blocked_not_grouped(self) -> None:
        snapshot = copy.deepcopy(self.snapshot)
        snapshot["staging_raw"].append(
            {
                **snapshot["staging_raw"][-1],
                "id": "s-invalid",
                "url": "file:///tmp/not-http",
            }
        )
        manifest = build_readonly_manifest(snapshot)
        self.assertEqual(manifest["reason_counts"]["INVALID_URL_IDENTITY"], 1)
        self.assertEqual(manifest["deduplication"]["duplicate_groups"], 2)

    def test_manifest_contains_no_raw_fixture_values(self) -> None:
        serialized = canonical_json(build_readonly_manifest(self.snapshot))
        for row in self.snapshot["staging_raw"]:
            for value in (row["id"], row["url"], row["payload"]):
                if value:
                    self.assertNotIn(str(value), serialized)
        self.assertNotIn("example.invalid", serialized)
        self.assertNotIn("Valid syllabus", serialized)

    def test_strict_schema_rejects_unknown_key_and_wrong_type(self) -> None:
        unknown = copy.deepcopy(self.snapshot)
        unknown["unexpected"] = True
        with self.assertRaisesRegex(PlannerInputError, "P2_INPUT_SCHEMA_INVALID"):
            build_readonly_manifest(unknown)

        wrong_type = copy.deepcopy(self.snapshot)
        wrong_type["page_size"] = True
        with self.assertRaises(PlannerInputError):
            build_readonly_manifest(wrong_type)

    def test_strict_schema_rejects_incomplete_snapshot_coverage(self) -> None:
        for collection in ("staging_raw", "profiles", "source_access", "courses", "prior_mutation_checks"):
            snapshot = copy.deepcopy(self.snapshot)
            snapshot[collection] = []
            with self.subTest(collection=collection), self.assertRaisesRegex(
                PlannerInputError,
                "P2_INPUT_COVERAGE_INCOMPLETE",
            ):
                build_readonly_manifest(snapshot)

    def test_strict_schema_rejects_reference_and_version_drift(self) -> None:
        broken_reference = copy.deepcopy(self.snapshot)
        broken_reference["downstream_references"][0]["staging_id"] = "s-missing"
        with self.assertRaisesRegex(PlannerInputError, "P2_INPUT_REFERENCE_INVALID"):
            build_readonly_manifest(broken_reference)

        wrong_version = copy.deepcopy(self.snapshot)
        wrong_version["normalization_version"] = "url-id-v2"
        with self.assertRaisesRegex(PlannerInputError, "P2_INPUT_VERSION_UNSUPPORTED"):
            build_readonly_manifest(wrong_version)

    def test_strict_schema_rejects_invalid_status_hash_and_timestamp(self) -> None:
        cases = []
        invalid_status = copy.deepcopy(self.snapshot)
        invalid_status["staging_raw"][0]["status"] = "unknown"
        cases.append(invalid_status)
        invalid_hash = copy.deepcopy(self.snapshot)
        invalid_hash["staging_raw"][0]["content_hash"] = "not-a-hash"
        cases.append(invalid_hash)
        invalid_timestamp = copy.deepcopy(self.snapshot)
        invalid_timestamp["observed_at"] = "2026-08-10T12:00:00"
        cases.append(invalid_timestamp)

        for snapshot in cases:
            with self.subTest(snapshot=snapshot), self.assertRaises(PlannerInputError):
                build_readonly_manifest(snapshot)

    def test_provenance_is_fixed_and_cannot_exfiltrate_input(self) -> None:
        for field, value in (
            ("source_kind", "https://example.invalid/leak"),
            ("environment", "secret-value"),
            ("run_id", "synthetic-run?token=leak"),
            ("required_approver", "person@example.invalid"),
        ):
            snapshot = copy.deepcopy(self.snapshot)
            snapshot["provenance"][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(
                PlannerInputError,
                "P2_INPUT_PROVENANCE_INVALID",
            ):
                build_readonly_manifest(snapshot)

    def test_prior_mutation_cardinality_and_run_binding_are_exact(self) -> None:
        extra = copy.deepcopy(self.snapshot)
        row = copy.deepcopy(extra["prior_mutation_checks"][0])
        row.update({"id": "m-04", "course_id": "c-03"})
        extra["prior_mutation_checks"].append(row)
        with self.assertRaisesRegex(PlannerInputError, "P2_INPUT_COVERAGE_INCOMPLETE"):
            build_readonly_manifest(extra)

        wrong_run = copy.deepcopy(self.snapshot)
        wrong_run["prior_mutation_checks"][0]["run_id"] = "synthetic-other-run"
        with self.assertRaisesRegex(PlannerInputError, "P2_INPUT_PROVENANCE_INVALID"):
            build_readonly_manifest(wrong_run)

    def test_profile_patterns_reject_unsafe_regex(self) -> None:
        for pattern in ("re:", "re:(?=unsafe)", "re:(a+)+", r"re:(a)\1", "x" * 201):
            snapshot = copy.deepcopy(self.snapshot)
            snapshot["profiles"][2]["allowed_url_patterns"] = [pattern]
            with self.subTest(pattern=pattern), self.assertRaisesRegex(
                PlannerInputError,
                "P2_INPUT_PROFILE_INVALID",
            ):
                build_readonly_manifest(snapshot)

    def test_paginated_catalog_requires_safe_url_template(self) -> None:
        for pattern in (
            "https://example.invalid/catalog",
            "file:///catalog/{page}",
            "https://example.invalid/{other}",
            "https://example.invalid/catalog/{page}/" + "x" * 180,
        ):
            snapshot = copy.deepcopy(self.snapshot)
            snapshot["profiles"][1]["catalog_url_patterns"] = [pattern]
            with self.subTest(pattern=pattern), self.assertRaisesRegex(
                PlannerInputError,
                "P2_INPUT_PROFILE_INVALID",
            ):
                build_readonly_manifest(snapshot)

    def test_expired_fixture_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            PlannerInputError,
            "P2_INPUT_EXPIRED",
        ):
            load_snapshot(DEFAULT_FIXTURE, now=datetime(2026, 8, 18, tzinfo=timezone.utc))

    def test_exact_stale_boundary_is_not_stale(self) -> None:
        manifest = build_readonly_manifest(self.snapshot)
        self.assertEqual(manifest["lifecycle"]["stale_processing"], 5)
        self.assertNotIn("PROCESSING_TIME_IN_FUTURE", manifest["reason_counts"])
        self.assertEqual(manifest["reason_counts"]["ACTIVE_PROCESSING"], 1)

    def test_loader_rejects_duplicate_keys_and_non_finite_numbers(self) -> None:
        for payload in ('{"schema":"x","schema":"y"}', '{"value":NaN}'):
            with self.subTest(payload=payload), mock.patch.object(
                planner,
                "_read_bounded_regular_file",
                return_value=payload.encode("utf-8"),
            ):
                with self.assertRaises(PlannerInputError):
                    load_snapshot(DEFAULT_FIXTURE)

    def test_loader_rejects_unc_external_and_special_paths(self) -> None:
        for path in (
            Path("//host/share/fixture.json"),
            ROOT / "outside.json",
            DEFAULT_FIXTURE.parent / "nested" / "fixture.json",
        ):
            with self.subTest(path=path), self.assertRaisesRegex(
                PlannerInputError,
                "P2_INPUT_FILE_UNAVAILABLE",
            ):
                load_snapshot(path)

    def test_cli_defaults_to_fixture_and_emits_only_json(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            result = main(["--compact"])
        self.assertEqual(result, 0)
        self.assertEqual(stderr.getvalue(), "")
        parsed = json.loads(stdout.getvalue())
        self.assertEqual(parsed["schema"], MANIFEST_SCHEMA)

    def test_cli_rejects_remote_input_and_invalid_page_size(self) -> None:
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            self.assertEqual(main(["--input", "https://example.invalid/data.json"]), 2)
        self.assertEqual(stderr.getvalue().strip(), "P2_INPUT_FILE_UNAVAILABLE")

        stderr = io.StringIO()
        with redirect_stderr(stderr):
            self.assertEqual(main(["--page-size", "0"]), 2)
        self.assertEqual(stderr.getvalue().strip(), "P2_INPUT_LIMIT_EXCEEDED")

    def test_cli_has_no_apply_or_write_option(self) -> None:
        stderr = io.StringIO()
        with redirect_stderr(stderr), self.assertRaises(SystemExit) as raised:
            main(["--apply"])
        self.assertEqual(raised.exception.code, 2)

    def test_modules_have_no_remote_or_mutating_dependencies(self) -> None:
        forbidden_imports = {
            "dotenv",
            "httpx",
            "requests",
            "socket",
            "subprocess",
            "supabase",
            "urllib.request",
        }
        forbidden_names = {"delete", "patch", "rpc", "upsert", "write"}
        for relative in (
            "scripts/shared/f10_9_readonly_planner.py",
            "scripts/maintenance/f10_9_readonly_audit.py",
        ):
            tree = ast.parse((ROOT / relative).read_text(encoding="utf-8"))
            imports = {
                alias.name
                for node in ast.walk(tree)
                if isinstance(node, ast.Import)
                for alias in node.names
            } | {
                node.module or ""
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom)
            }
            names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
            attributes = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
            with self.subTest(module=relative):
                self.assertFalse(imports.intersection(forbidden_imports))
                self.assertFalse((names | attributes).intersection(forbidden_names))

    def test_contract_versions_are_frozen(self) -> None:
        self.assertEqual(INPUT_SCHEMA, "f10.9-p2-readonly-input.v1")
        self.assertEqual(MANIFEST_SCHEMA, "f10.9-p2-readonly-manifest.v1")
        self.assertEqual(URL_IDENTITY_VERSION, "url-id-v1")


if __name__ == "__main__":
    unittest.main()
