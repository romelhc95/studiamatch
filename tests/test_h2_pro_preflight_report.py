from __future__ import annotations

import hashlib
import json
import subprocess
import sys

import pytest
import requests

from scripts.maintenance import h2_pro_preflight_report as preflight


COURSE_ROWS = [
    {
        "id": "synthetic-course-001",
        "institution_id": "synthetic-institution-001",
        "slug": "synthetic-course",
        "is_active": True,
        "is_verified": True,
        "url": "https://synthetic.invalid/course",
    }
]
PROFILE_ROWS = [
    {
        "institution_id": "synthetic-institution-001",
        "production_enabled": True,
        "notes": "synthetic profile",
    }
]


def test_module_import_does_not_pollute_machine_readable_stdout() -> None:
    result = subprocess.run(
        [sys.executable, "-c", "import scripts.maintenance.h2_pro_preflight_report"],
        cwd=preflight.ROOT_DIR,
        capture_output=True,
        check=False,
        text=True,
        timeout=10,
    )

    assert result.returncode == 0
    assert result.stdout == ""


def install_read_fakes(
    monkeypatch: pytest.MonkeyPatch,
    *,
    migration_names: tuple[str, ...] = (),
    public_objects: dict[str, bool] | None = None,
    crawler_exclusions_present: bool = False,
    crawler_exclusions_empty: bool = True,
) -> None:
    presence = public_objects or {}

    def public_rows(_db, table: str, columns: str):
        assert (table, columns) == ("courses", "id")
        return [{"id": row["id"]} for row in COURSE_ROWS]

    def service_rows(_db, table: str, columns: str):
        if table == "courses":
            assert columns == "id,institution_id,slug,is_active,is_verified,url"
            return COURSE_ROWS
        if table == "institution_site_profiles":
            assert columns == "institution_id,production_enabled,notes"
            return PROFILE_ROWS
        if table == "supabase_migrations":
            assert columns == "name"
            return [{"name": name} for name in migration_names]
        raise AssertionError(f"unexpected service read: {table}.{columns}")

    monkeypatch.setattr(preflight, "select_public_all", public_rows)
    monkeypatch.setattr(preflight, "select_service_all", service_rows)
    monkeypatch.setattr(
        preflight,
        "table_exists",
        lambda _db, table: crawler_exclusions_present if table == "crawler_exclusions" else presence.get(table, False),
    )
    monkeypatch.setattr(
        preflight,
        "table_has_rows",
        lambda _db, table: not crawler_exclusions_empty if table == "crawler_exclusions" else False,
    )


@pytest.mark.parametrize("getter", [preflight.public_get, preflight.service_get])
def test_supabase_reads_never_follow_redirects(monkeypatch, getter) -> None:
    calls = []

    def fake_get(url, **kwargs):
        calls.append((url, kwargs))
        return object()

    class FakeDb:
        supabase_url = "https://xwhtiqmboljkshrtviyw.supabase.co"

        @staticmethod
        def _get_headers(*, use_service_role):
            return {"X-Fixture-Auth-Mode": "service" if use_service_role else "public"}

    monkeypatch.setattr(preflight.requests, "get", fake_get)

    getter(FakeDb(), "courses?select=id")

    assert len(calls) == 1
    assert calls[0][1]["allow_redirects"] is False


def test_preflight_reports_pre_h2_baseline_without_granting_apply(monkeypatch) -> None:
    install_read_fakes(monkeypatch)

    report = preflight.build_report(object())

    assert report["h2_state"] == "BASELINE"
    assert report["apply_authorized"] is False
    assert report["application_decision"] == "NOT_AUTHORIZED"
    assert report["jit_fields_available"] is True
    assert report["eligible_count"] == 1
    assert "GO" not in json.dumps(report)


def test_preflight_does_not_count_a_single_course_as_a_duplicate_group(monkeypatch) -> None:
    install_read_fakes(monkeypatch)

    report = preflight.build_report(object())

    assert report["duplicate_institution_slug_groups"] == 0


def test_preflight_counts_repeated_institution_slug_once_as_duplicate_group(monkeypatch) -> None:
    duplicate_rows = [
        {**COURSE_ROWS[0], "id": "synthetic-course-001"},
        {**COURSE_ROWS[0], "id": "synthetic-course-002"},
    ]

    def public_rows(_db, table: str, columns: str):
        assert (table, columns) == ("courses", "id")
        return [{"id": row["id"]} for row in duplicate_rows]

    def service_rows(_db, table: str, columns: str):
        if table == "courses":
            assert columns == "id,institution_id,slug,is_active,is_verified,url"
            return duplicate_rows
        if table == "institution_site_profiles":
            return PROFILE_ROWS
        if table == "supabase_migrations":
            return []
        raise AssertionError(f"unexpected service read: {table}.{columns}")

    monkeypatch.setattr(preflight, "select_public_all", public_rows)
    monkeypatch.setattr(preflight, "select_service_all", service_rows)
    monkeypatch.setattr(preflight, "table_exists", lambda _db, _table: False)

    report = preflight.build_report(object())

    assert report["duplicate_institution_slug_groups"] == 1
    assert "duplicate institution_id+slug groups: 1" in report["data_blockers"]


@pytest.mark.parametrize(
    "url",
    [
        "https://xwhtiqmboljkshrtviyw.supabase.co",
        "https://xwhtiqmboljkshrtviyw.supabase.co/",
        "https://xwhtiqmboljkshrtviyw.supabase.co:443",
    ],
)
def test_pro_target_pin_accepts_only_canonical_origin_forms(url) -> None:
    preflight.assert_pro_target(url)


@pytest.mark.parametrize(
    "url",
    [
        "http://xwhtiqmboljkshrtviyw.supabase.co",
        "https://other.supabase.co",
        "https://user@xwhtiqmboljkshrtviyw.supabase.co",
        "https://user:pass@xwhtiqmboljkshrtviyw.supabase.co",
        "https://xwhtiqmboljkshrtviyw.supabase.co:444",
        "https://xwhtiqmboljkshrtviyw.supabase.co:bad",
        "https://xwhtiqmboljkshrtviyw.supabase.co/rest/v1",
        "https://xwhtiqmboljkshrtviyw.supabase.co?select=*",
        "https://xwhtiqmboljkshrtviyw.supabase.co#fragment",
    ],
)
def test_pro_target_pin_rejects_noncanonical_origins(url) -> None:
    with pytest.raises(RuntimeError, match="pinned"):
        preflight.assert_pro_target(url)


def test_preflight_reports_partial_h2_outside_ledger_and_keeps_aggregates(monkeypatch) -> None:
    install_read_fakes(
        monkeypatch,
        public_objects={"course_editorial_state": True, "courses_public_effective": True},
    )

    report = preflight.build_report(object())

    assert report["h2_state"] == "PARTIAL_UNLEDGERED"
    assert report["h2_ledger_migrations"] == []
    assert report["eligible_count"] == 1
    assert report["public_visible_count"] == 1
    expected_digest = hashlib.sha256(b"synthetic-course-001").hexdigest()
    assert report["ordered_eligible_ids_digest"] == f"sha256:{expected_digest}"
    assert report["jit_fields_available"] is False
    assert report["jit_lines"] == []
    assert report["apply_authorized"] is False
    assert "GO" not in json.dumps(report)
    rendered = json.dumps(report)
    assert "synthetic-course-001" not in rendered
    assert "synthetic-institution-001" not in rendered
    assert "https://synthetic.invalid/course" not in rendered


def test_preflight_reports_compatible_h2_observed_surface_as_diagnostic_only(monkeypatch) -> None:
    objects = {
        "editorial_field_definitions": True,
        "course_editorial_state": True,
        "course_editorial_audit": True,
        "courses_public_effective": True,
    }
    install_read_fakes(
        monkeypatch,
        migration_names=preflight.H2_EXPAND_MIGRATIONS,
        public_objects=objects,
    )

    report = preflight.build_report(object())

    assert report["h2_state"] == "H2_COMPATIBLE_OBSERVED_SURFACE"
    assert report["private_h2_schema_observed"] is None
    assert report["private_h2_schema_probe"] == "not_performed"
    assert report["verification_rpc_probe"] == "not_performed"
    assert report["apply_authorized"] is False
    assert report["application_decision"] == "NOT_AUTHORIZED"
    assert report["jit_fields_available"] is False
    assert "GO" not in json.dumps(report)


def test_preflight_marks_partial_ledger_and_missing_object_inconsistent(monkeypatch) -> None:
    install_read_fakes(
        monkeypatch,
        migration_names=preflight.H2_EXPAND_MIGRATIONS[:2],
        public_objects={"course_editorial_state": True},
    )

    report = preflight.build_report(object())

    assert report["h2_state"] == "INCONSISTENT"
    assert report["report_status"] == "INCOMPLETE"
    assert report["h2_blockers"]
    assert report["apply_authorized"] is False
    assert report["jit_fields_available"] is False
    assert "GO" not in json.dumps(report)


def test_preflight_marks_complete_ledger_with_missing_public_object_inconsistent(monkeypatch) -> None:
    install_read_fakes(
        monkeypatch,
        migration_names=preflight.H2_EXPAND_MIGRATIONS,
        public_objects={"course_editorial_state": True},
    )

    report = preflight.build_report(object())

    assert report["h2_state"] == "INCONSISTENT"
    assert report["report_status"] == "INCOMPLETE"
    assert any("public H2 objects are missing" in blocker for blocker in report["h2_blockers"])
    assert report["jit_fields_available"] is False
    assert report["apply_authorized"] is False
    assert "GO" not in json.dumps(report)


def test_preflight_read_error_is_explicit_and_does_not_echo_response_data(monkeypatch) -> None:
    secret_like_body = "synthetic-secret-value-do-not-print"

    class FailedResponse:
        status_code = 500
        content = secret_like_body.encode("utf-8")
        text = secret_like_body

    def fail_read(_db, _path: str):
        return FailedResponse()

    monkeypatch.setattr(preflight, "public_get", fail_read)

    report = preflight.build_report(object())
    rendered = json.dumps(report)

    assert report["report_status"] == "READ_ERROR"
    assert report["eligible_count"] is None
    assert report["error"]["resource"] == "courses"
    assert report["error"]["category"] == "HTTP 500"
    assert secret_like_body not in rendered
    assert "synthetic-course-001" not in rendered
    assert "https://synthetic.invalid/course" not in rendered
    assert report["apply_authorized"] is False
    assert "GO" not in rendered


def test_preflight_public_visibility_mismatch_is_reported_as_incomplete(monkeypatch) -> None:
    install_read_fakes(monkeypatch)
    monkeypatch.setattr(
        preflight,
        "select_public_all",
        lambda _db, _table, _columns: [],
    )

    report = preflight.build_report(object())

    assert report["report_status"] == "INCOMPLETE"
    assert report["missing_from_public_count"] == 1
    assert report["data_blockers"]
    assert report["jit_fields_available"] is False
    assert report["apply_authorized"] is False
    assert report["ordered_eligible_ids_digest"] == (
        "sha256:" + hashlib.sha256(b"synthetic-course-001").hexdigest()
    )
    assert "GO" not in json.dumps(report)


def test_preflight_network_error_does_not_echo_exception_text(monkeypatch) -> None:
    exception_text = "synthetic-network-secret-never-print"

    def fail_read(_db, _path: str):
        raise requests.ConnectionError(exception_text)

    monkeypatch.setattr(preflight, "public_get", fail_read)

    report = preflight.build_report(object())
    rendered = json.dumps(report)

    assert report["report_status"] == "READ_ERROR"
    assert report["error"]["category"] == "network_error"
    assert exception_text not in rendered
    assert report["eligible_count"] is None


@pytest.mark.parametrize(
    ("response_json", "category"),
    [
        (ValueError("synthetic-invalid-json"), "invalid_json"),
        ({"unexpected": "object"}, "invalid_shape"),
    ],
)
def test_preflight_invalid_read_payloads_are_explicit_and_sanitized(
    monkeypatch, response_json, category
) -> None:
    class Response:
        status_code = 200
        content = b"nonempty"

        def json(self):
            if isinstance(response_json, Exception):
                raise response_json
            return response_json

    monkeypatch.setattr(preflight, "public_get", lambda _db, _path: Response())

    report = preflight.build_report(object())

    assert report["report_status"] == "READ_ERROR"
    assert report["error"] == {"resource": "courses", "category": category}
    assert report["eligible_count"] is None
    assert report["apply_authorized"] is False
    assert report["jit_fields_available"] is False
    assert "GO" not in json.dumps(report)
    assert "unexpected" not in json.dumps(report)


@pytest.mark.parametrize(
    ("rows", "expected"),
    [([], False), ([{"id": "synthetic-exclusion"}], True)],
)
def test_crawler_exclusion_probe_reads_only_presence_metadata(monkeypatch, rows, expected) -> None:
    seen_paths = []

    class Response:
        status_code = 200
        content = b"[]"

        def json(self):
            return rows

    def fake_get(_db, path: str):
        seen_paths.append(path)
        return Response()

    monkeypatch.setattr(preflight, "service_get", fake_get)

    assert preflight.table_has_rows(object(), "crawler_exclusions") is expected
    assert seen_paths == ["crawler_exclusions?select=id&limit=1"]
