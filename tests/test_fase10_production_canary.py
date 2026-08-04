from __future__ import annotations

import ast
import json
import os
import stat
import tempfile
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import unquote

from scripts.core import production_canary_manifest, production_canary_state


ROOT = Path(__file__).resolve().parents[1]


def source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


@contextmanager
def temporary_env(values: dict[str, str], *, delete: tuple[str, ...] = ()):  # noqa: ANN201
    keys = set(values) | set(delete)
    previous = {key: os.environ.get(key) for key in keys}
    try:
        for key in delete:
            os.environ.pop(key, None)
        os.environ.update(values)
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


class FakeProductionCanaryDB:
    def __init__(self, tables: dict[str, list[dict[str, object]]], *, patch_fails: bool = False):
        self.tables = {
            table: [dict(row) for row in rows]
            for table, rows in tables.items()
        }
        self.patch_fails = patch_fails

    def _matches(self, row: dict[str, object], filters: str | None) -> bool:
        if not filters:
            return True
        for clause in filters.split("&"):
            if not clause:
                continue
            if "=eq." in clause:
                column, value = clause.split("=eq.", 1)
                if str(row.get(column)) != unquote(value):
                    return False
            elif "=neq." in clause:
                column, value = clause.split("=neq.", 1)
                if str(row.get(column)) == unquote(value):
                    return False
            elif clause.endswith("=is.null"):
                column = clause.removesuffix("=is.null")
                if row.get(column) is not None:
                    return False
            elif "=in.(" in clause and clause.endswith(")"):
                column, values = clause.split("=in.(", 1)
                allowed = {unquote(value) for value in values[:-1].split(",") if value}
                if str(row.get(column)) not in allowed:
                    return False
            else:
                raise AssertionError(f"Unsupported fake filter: {clause}")
        return True

    def _select(self, table: str, filters: str | None = None) -> list[dict[str, object]]:
        return [dict(row) for row in self.tables.get(table, []) if self._matches(row, filters)]

    def select_service_raise(self, table: str, filters: str | None = None, **_kwargs) -> list[dict[str, object]]:
        return self._select(table, filters)

    def select_pipeline_raise(self, table: str, filters: str | None = None, **_kwargs) -> list[dict[str, object]]:
        return self._select(table, filters)

    def select_all_service(self, table: str, filters: str | None = None, **_kwargs) -> list[dict[str, object]]:
        return self._select(table, filters)

    def select_all_pipeline(self, table: str, filters: str | None = None, **_kwargs) -> list[dict[str, object]]:
        return self._select(table, filters)

    def count_service_raise(self, table: str, filters: str | None = None) -> int:
        return len(self._select(table, filters))

    def count_pipeline_raise(self, table: str, filters: str | None = None) -> int:
        return len(self._select(table, filters))

    def delete(self, table: str, filters: str) -> list[dict[str, object]]:
        deleted = [row for row in self.tables[table] if self._matches(row, filters)]
        self.tables[table] = [row for row in self.tables[table] if not self._matches(row, filters)]
        return [dict(row) for row in deleted]

    def patch_exact_one_raise(self, table: str, filters: str, data: dict[str, object], expected_id: object) -> None:
        if self.patch_fails:
            raise RuntimeError("synthetic patch failure")
        matches = [row for row in self.tables[table] if self._matches(row, filters)]
        if len(matches) != 1 or matches[0].get("id") != expected_id:
            raise RuntimeError("fake patch did not match exactly one expected row")
        matches[0].update(data)


def _production_canary_env(*, run_id: str = "run-1") -> dict[str, str]:
    return {
        "GITHUB_ACTIONS": "true",
        "GITHUB_EVENT_NAME": "workflow_dispatch",
        "GITHUB_REF_NAME": "main",
        "GITHUB_SHA": "a" * 40,
        "GITHUB_RUN_ID": "100",
        "CANARY_EXPECTED_ENVIRONMENT": "Production",
        "F10_PRODUCTION_CANARY_SUPABASE_HOST": "prod.example.supabase.co",
        "SUPABASE_URL": "https://prod.example.supabase.co",
        "NEXT_PUBLIC_SUPABASE_URL": "https://prod.example.supabase.co",
        "F10_PRODUCTION_CANARY_RUN_ID": run_id,
    }


def _fake_tables() -> dict[str, list[dict[str, object]]]:
    return {
        "institutions": [
            {"id": "inst-1", "slug": "demo"},
            {"id": "inst-2", "slug": "other"},
        ],
        "institution_site_profiles": [
            {
                "id": "profile-1",
                "institution_id": "inst-1",
                "discovery_enabled": True,
                "pipeline_enabled": True,
                "production_enabled": True,
                "circuit_open": False,
                "notes": "stable",
            },
            {"id": "profile-2", "institution_id": "inst-2", "notes": "other"},
        ],
        "staging_raw": [
            {
                "id": "stage-1",
                "institution_id": "inst-1",
                "status": "pending",
                "metadata": {},
                "created_at": "2026-01-01T00:00:00+00:00",
                "updated_at": "2026-01-01T00:00:00+00:00",
            },
            {"id": "stage-2", "institution_id": "inst-2", "status": "pending", "metadata": {"stable": True}},
        ],
        "cleansed_programs": [
            {"id": "clean-1", "institution_id": "inst-1", "status": "pending", "metadata": {}},
            {"id": "clean-2", "institution_id": "inst-2", "status": "pending", "metadata": {"stable": True}},
        ],
        "enriched_programs": [
            {"id": "enriched-1", "institution_id": "inst-1", "status": "pending", "metadata": {}},
            {"id": "enriched-2", "institution_id": "inst-2", "status": "pending", "metadata": {"stable": True}},
        ],
        "courses": [
            {
                "id": "course-1",
                "institution_id": "inst-1",
                "is_active": True,
                "provider_used": "baseline",
                "created_at": "2026-01-01T00:00:00+00:00",
                "updated_at": "2026-01-01T00:00:00+00:00",
            },
            {"id": "course-2", "institution_id": "inst-2", "is_active": True, "provider_used": "stable"},
        ],
    }


def _snapshot_args(tmp_path: Path) -> SimpleNamespace:
    return SimpleNamespace(
        institution_slug="demo",
        output=str(tmp_path / "private" / "snapshot.json"),
        summary_output=str(tmp_path / "artifacts" / "snapshot.json"),
    )


def _restore_args(tmp_path: Path, *, expect_noop: bool = False) -> SimpleNamespace:
    return SimpleNamespace(
        institution_slug="demo",
        snapshot=str(tmp_path / "private" / "snapshot.json"),
        summary_output=str(tmp_path / "artifacts" / ("restore_noop.json" if expect_noop else "restore.json")),
        expect_noop=expect_noop,
    )


def _with_fake_clients(fake: FakeProductionCanaryDB):  # noqa: ANN201
    original_manifest_client = production_canary_manifest.get_db_client
    original_state_client = production_canary_state.get_db_client
    production_canary_manifest.get_db_client = lambda: fake
    production_canary_state.get_db_client = lambda: fake

    def restore() -> None:
        production_canary_manifest.get_db_client = original_manifest_client
        production_canary_state.get_db_client = original_state_client

    return restore


def _expect_runtime_error(message: str, func, *args, **kwargs) -> None:  # noqa: ANN001, ANN201
    try:
        func(*args, **kwargs)
    except RuntimeError as exc:
        assert message in str(exc)
    else:
        raise AssertionError(f"Expected RuntimeError containing {message!r}")


def _helper_namespace(relative: str, names: set[str]) -> dict[str, object]:
    tree = ast.parse(source(relative))
    selected = []
    constants = {
        "CANARY_RUN_METADATA_KEYS",
        "CANARY_PROVIDER_MARKERS",
    }
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id in constants
            for target in node.targets
        ):
            selected.append(node)
        if isinstance(node, ast.FunctionDef) and node.name in names:
            selected.append(node)
    namespace: dict[str, object] = {"os": os}
    module = ast.Module(body=selected, type_ignores=[])
    ast.fix_missing_locations(module)
    exec(compile(module, relative, "exec"), namespace)
    return namespace


def test_production_canary_workflow_is_manual_main_only_and_sha_locked() -> None:
    workflow = source(".github/workflows/production_canary.yml")

    assert "workflow_dispatch:" in workflow
    assert "schedule:" not in workflow
    assert workflow.split("workflow_dispatch:", 1)[1].split("concurrency:", 1)[0].count("description:") == 10
    assert "name: Production" in workflow
    assert "github.ref_name == 'main'" in workflow
    assert 'test "$GITHUB_REF_NAME" = "main"' in workflow
    assert "candidate_sha:" in workflow
    assert 'test "$(git rev-parse HEAD)" = "$INPUT_CANDIDATE_SHA"' in workflow
    assert 'test "$(git rev-parse origin/main)" = "$INPUT_CANDIDATE_SHA"' in workflow
    assert "Production-Scheduled" not in workflow


def test_production_canary_requires_target_allowlist_and_mutable_authorization() -> None:
    workflow = source(".github/workflows/production_canary.yml")

    assert "F10_PRODUCTION_CANARY_SUPABASE_HOST: ${{ vars.F10_PRODUCTION_CANARY_SUPABASE_HOST }}" in workflow
    assert "AUTOMATION_ENABLED: ${{ vars.AUTOMATION_ENABLED }}" in workflow
    assert "PRODUCTION_WRITERS_PAUSED: ${{ vars.PRODUCTION_WRITERS_PAUSED }}" in workflow
    assert "F10_PRODUCTION_CANARY_SUPABASE_HOST is required" in workflow
    assert "mutable_stages:" in workflow
    assert "default: fg2_fg3" in workflow
    assert "Invalid mutable_stages value" in workflow
    assert "mutable_authorized:" in workflow
    assert "FG2/FG3 require mutable_authorized=true" in workflow
    assert workflow.count("production_control_preflight.sh PRODUCTION-CANARY --enforce") >= 8
    assert "--require-production-enabled" in workflow
    guard_step = workflow.split("Guard Production target, candidate and limits", 1)[1].split(
        "echo \"CANARY_REQUESTED_INSTITUTION_SLUG", 1
    )[0]
    assert "bash .github/scripts/production_control_preflight.sh PRODUCTION-CANARY --enforce" in guard_step
    assert guard_step.index("production_control_preflight.sh PRODUCTION-CANARY --enforce") < guard_step.index(
        "FG2/FG3 require mutable_authorized=true"
    )


def test_production_canary_uses_private_snapshot_and_idempotent_restore() -> None:
    workflow = source(".github/workflows/production_canary.yml")

    assert "CANARY_PRIVATE_SNAPSHOT=$RUNNER_TEMP/f10_production_canary_state/private_snapshot.json" in workflow
    assert "umask 077" in workflow
    assert "install -d -m 700 \"$CANARY_STATE_DIR\"" in workflow
    assert "stat -c '%a' \"$CANARY_PRIVATE_SNAPSHOT\"" in workflow
    assert "production_canary_state.py snapshot" in workflow
    assert "production_canary_state.py restore" in workflow
    assert "--expect-noop" in workflow
    upload_section = workflow.split("Upload sanitized canary manifests", 1)[1]
    assert "name: f10-production-canary-manifests" in upload_section
    assert "${{ github.run_id }}" not in upload_section
    assert "${{ github.run_attempt }}" not in upload_section
    assert "path: artifacts/f10_production_canary_*.json" in workflow
    assert "private_snapshot.json" not in upload_section


def test_production_canary_avoids_input_shell_injection_with_secrets() -> None:
    workflow = source(".github/workflows/production_canary.yml")

    run_blocks = "\n".join(block for block in workflow.split("\n      - name:") if "run: |" in block)
    assert "${{ inputs.institution_slug }}" not in run_blocks
    assert "${{ inputs.fg1_source_slug }}" not in run_blocks
    assert "${{ inputs.max_harvest_urls }}" not in run_blocks
    assert "${{ inputs.max_staging_records }}" not in run_blocks
    assert "${{ inputs.max_enrichment_records }}" not in run_blocks
    assert "${{ inputs.max_sync_records }}" not in run_blocks
    assert "${{ inputs.max_integrity_courses }}" not in run_blocks
    assert "SUPABASE_URL: ${{ secrets.SUPABASE_URL }}" in workflow


def test_production_canary_manifests_are_sanitized() -> None:
    manifest = source("scripts/core/production_canary_manifest.py")
    state = source("scripts/core/production_canary_state.py")

    assert '"institution_slug"' in manifest
    assert '"institution_slug": "redacted"' in manifest
    assert '"institution_name"' not in manifest
    assert '"sha": os.getenv("GITHUB_SHA")' not in manifest
    assert '"run_id": os.getenv("GITHUB_RUN_ID")' not in manifest
    assert "CANARY_INSTITUTION_ID" in manifest
    assert "F10_PRODUCTION_CANARY_SUPABASE_HOST" in manifest
    assert "F10_PRODUCTION_CANARY_SUPABASE_HOST" in state
    assert '"private_digest"' not in state
    assert '"cohort": {"institution_slug": "redacted"}' in state
    assert '"institution_name"' not in state


def test_production_canary_scripts_reject_local_cli() -> None:
    with temporary_env({}, delete=("GITHUB_ACTIONS",)):
        _expect_runtime_error("GitHub Actions", production_canary_manifest._ensure_github_production_context)
        _expect_runtime_error("GitHub Actions", production_canary_state._ensure_github_production_context)


def test_production_canary_manifest_uses_fake_db_and_sanitizes_artifact() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        env_file = tmp_path / "github.env"
        fake = FakeProductionCanaryDB(_fake_tables())
        restore_clients = _with_fake_clients(fake)
        try:
            with temporary_env(_production_canary_env()):
                args = SimpleNamespace(
                    institution_slug="demo",
                    stage="pre",
                    github_env=str(env_file),
                    require_pipeline_enabled=True,
                    require_production_enabled=True,
                    max_staging_records=5,
                    max_enrichment_records=3,
                    max_sync_records=3,
                    max_integrity_courses=3,
                )
                manifest = production_canary_manifest.build_manifest(args)
        finally:
            restore_clients()

        assert manifest["cohort"] == {"institution_slug": "redacted"}
        assert "sha" not in manifest["github"]
        assert "run_id" not in manifest["github"]
        assert manifest["profile_gates"]["production_enabled"] is True
        assert manifest["counts"]["staging_pending"] == 1
        assert "CANARY_INSTITUTION_ID=inst-1" in env_file.read_text(encoding="utf-8")


def test_production_canary_snapshot_restore_and_second_noop_are_offline_and_sanitized() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        fake = FakeProductionCanaryDB(_fake_tables())
        restore_clients = _with_fake_clients(fake)
        try:
            with temporary_env(_production_canary_env()):
                production_canary_state.capture_snapshot(_snapshot_args(tmp_path))
                private_snapshot = tmp_path / "private" / "snapshot.json"
                public_summary = tmp_path / "artifacts" / "snapshot.json"
                assert stat.S_IMODE(private_snapshot.parent.stat().st_mode) == 0o700
                assert stat.S_IMODE(private_snapshot.stat().st_mode) == 0o600
                assert "digest" in private_snapshot.read_text(encoding="utf-8")
                assert "digest" not in public_summary.read_text(encoding="utf-8")

                fake.tables["staging_raw"].append(
                    {
                        "id": "stage-new",
                        "institution_id": "inst-1",
                        "status": "discovered",
                        "metadata": {"f10_production_canary_run_id": "run-1"},
                        "created_at": "2999-01-01T00:00:00+00:00",
                    }
                )
                fake.tables["courses"][0]["provider_used"] = "changed|f10-production-canary:run-1"

                production_canary_state.restore_snapshot(_restore_args(tmp_path))
                production_canary_state.restore_snapshot(_restore_args(tmp_path, expect_noop=True))
        finally:
            restore_clients()

        assert [row["id"] for row in fake.tables["staging_raw"]] == ["stage-1", "stage-2"]
        assert fake.tables["courses"][0]["provider_used"] == "baseline"
        noop_summary = json.loads((tmp_path / "artifacts" / "restore_noop.json").read_text(encoding="utf-8"))
        assert noop_summary["expect_noop"] is True
        assert noop_summary["after_matches_snapshot"] is True
        assert noop_summary["non_cohort_attestations_match"] is True
        assert "digest" not in json.dumps(noop_summary)


def test_production_canary_restore_detects_non_cohort_content_mutation_with_same_count() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        fake = FakeProductionCanaryDB(_fake_tables())
        restore_clients = _with_fake_clients(fake)
        try:
            with temporary_env(_production_canary_env()):
                production_canary_state.capture_snapshot(_snapshot_args(tmp_path))
                fake.tables["staging_raw"][1]["status"] = "same-count-drift"
                _expect_runtime_error("Non-cohort row content changed", production_canary_state.restore_snapshot, _restore_args(tmp_path))
        finally:
            restore_clients()


def test_production_canary_restore_rejects_wrong_marker_or_invalid_timestamp() -> None:
    cases = [
        (
            {
                "id": "wrong-marker",
                "institution_id": "inst-1",
                "status": "discovered",
                "metadata": {"f10_production_canary_run_id": "other-run"},
                "created_at": "2999-01-01T00:00:00+00:00",
            },
            "Refusing to delete",
        ),
        (
            {
                "id": "bad-timestamp",
                "institution_id": "inst-1",
                "status": "discovered",
                "metadata": {"f10_production_canary_run_id": "run-1"},
                "created_at": "not-a-timestamp",
            },
            "Invalid production canary timestamp",
        ),
    ]
    for extra_row, message in cases:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake = FakeProductionCanaryDB(_fake_tables())
            restore_clients = _with_fake_clients(fake)
            try:
                with temporary_env(_production_canary_env()):
                    production_canary_state.capture_snapshot(_snapshot_args(tmp_path))
                    fake.tables["staging_raw"].append(extra_row)
                    _expect_runtime_error(message, production_canary_state.restore_snapshot, _restore_args(tmp_path))
            finally:
                restore_clients()


def test_production_canary_restore_fails_if_existing_row_disappears() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        fake = FakeProductionCanaryDB(_fake_tables())
        restore_clients = _with_fake_clients(fake)
        try:
            with temporary_env(_production_canary_env()):
                production_canary_state.capture_snapshot(_snapshot_args(tmp_path))
                fake.tables["courses"] = [row for row in fake.tables["courses"] if row["id"] != "course-1"]
                _expect_runtime_error("cannot recreate missing courses rows", production_canary_state.restore_snapshot, _restore_args(tmp_path))
        finally:
            restore_clients()


def test_production_canary_restore_fails_closed_on_partial_patch_failure() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        fake = FakeProductionCanaryDB(_fake_tables(), patch_fails=True)
        restore_clients = _with_fake_clients(fake)
        try:
            with temporary_env(_production_canary_env()):
                production_canary_state.capture_snapshot(_snapshot_args(tmp_path))
                fake.tables["courses"][0]["provider_used"] = "changed|f10-production-canary:run-1"
                _expect_runtime_error("synthetic patch failure", production_canary_state.restore_snapshot, _restore_args(tmp_path))
        finally:
            restore_clients()


def test_runtime_scripts_add_env_gated_production_canary_markers() -> None:
    harvester = source("scripts/core/universal_harvester.py")
    cleansing = source("scripts/core/cleansing_worker.py")
    enrichment = source("scripts/core/enrichment_worker.py")
    sync = source("scripts/core/sync_vector_worker.py")

    assert "F10_PRODUCTION_CANARY_RUN_ID" in harvester
    assert "f10_production_canary_run_id" in harvester
    assert "F10_PRODUCTION_CANARY_RUN_ID" in cleansing
    assert "f10_production_canary_run_id" in cleansing
    assert "F10_PRODUCTION_CANARY_RUN_ID" in enrichment
    assert "f10_production_canary_run_id" in enrichment
    assert "F10_PRODUCTION_CANARY_RUN_ID" in sync
    assert "f10-production-canary" in sync


def test_runtime_canary_marker_helpers_propagate_f10_run_id() -> None:
    with temporary_env({"F10_PRODUCTION_CANARY_RUN_ID": "run-1"}, delete=("F99_CERTIFICATION_CANARY_RUN_ID",)):
        harvester = _helper_namespace(
            "scripts/core/universal_harvester.py",
            {"_active_canary_marker", "_mark_canary_metadata"},
        )
        cleansing = _helper_namespace(
            "scripts/core/cleansing_worker.py",
            {"_active_canary_marker", "_mark_canary_metadata"},
        )
        enrichment = _helper_namespace(
            "scripts/core/enrichment_worker.py",
            {"_active_canary_marker", "_mark_canary_metadata"},
        )
        sync = _helper_namespace(
            "scripts/core/sync_vector_worker.py",
            {"_active_canary_provider_marker", "_mark_canary_provider"},
        )

        assert harvester["_mark_canary_metadata"]({}) == {"f10_production_canary_run_id": "run-1"}
        assert cleansing["_mark_canary_metadata"]({}) == {"f10_production_canary_run_id": "run-1"}
        assert enrichment["_mark_canary_metadata"]({}) == {"f10_production_canary_run_id": "run-1"}
        assert sync["_mark_canary_provider"]("baseline") == "baseline|f10-production-canary:run-1"
