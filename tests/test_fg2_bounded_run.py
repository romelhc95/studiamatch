"""Offline contracts for the opt-in first FG2 controlled run."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path
from urllib.parse import urlsplit

import pytest

from scripts.core.fg2_bounded_run import (
    FG2CohortManifest,
    FG2_LIMITS,
    FG2RequestBudget,
    InvalidControlledRun,
    OriginDeferred,
    RunBudgetExceeded,
    SourceBlocked,
    UnsafePublicTarget,
    append_manifest_entry,
    append_manifest_blocker,
    initialize_manifest,
    load_manifest_b64,
    require_manifest_sha256,
    uuid_in_filter,
    update_manifest_institution,
    update_manifest_origin_state,
    url_sha256,
    public_url_resolve_entry,
    parse_retry_after,
    validate_controlled_profile,
)


INSTITUTION_ID = "00000000-0000-0000-0000-000000000001"
STAGING_ID = "40000000-0000-0000-0000-000000000001"
SOURCE_SHA = "a" * 40


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0
        self.wall = datetime(2026, 11, 9, 12, tzinfo=timezone.utc)
        self.sleeps: list[float] = []

    def monotonic(self) -> float:
        return self.now

    def utcnow(self) -> datetime:
        return self.wall + timedelta(seconds=self.now)

    async def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds
        await asyncio.sleep(0)


class FakeResponse:
    def __init__(self, status: int = 200, headers: dict | None = None, url: str = "") -> None:
        self.status_code = status
        self.headers = headers or {}
        self.url = url
        self.text = "<html><body>synthetic</body></html>"
        self.content = self.text.encode()


class FakeSession:
    def __init__(self, clock: FakeClock, responses: list[object] | None = None) -> None:
        self.clock = clock
        self.responses = list(responses or [])
        self.calls: list[tuple[str, float, dict]] = []
        self.active_by_origin: dict[str, int] = {}
        self.max_active_by_origin: dict[str, int] = {}

    async def get(self, url: str, **kwargs):
        origin = f"{urlsplit(url).scheme}://{urlsplit(url).netloc}"
        active = self.active_by_origin.get(origin, 0) + 1
        self.active_by_origin[origin] = active
        self.max_active_by_origin[origin] = max(
            self.max_active_by_origin.get(origin, 0), active
        )
        self.calls.append((url, self.clock.monotonic(), kwargs))
        try:
            await asyncio.sleep(0)
            value = self.responses.pop(0) if self.responses else FakeResponse(url=url)
            if isinstance(value, Exception):
                raise value
            value.url = value.url or url
            return value
        finally:
            self.active_by_origin[origin] -= 1


def make_budget(clock: FakeClock, **kwargs) -> FG2RequestBudget:
    return FG2RequestBudget(
        max_unique_urls=kwargs.pop("max_unique_urls", 10),
        max_http_requests=kwargs.pop("max_http_requests", 20),
        min_interval_seconds=kwargs.pop("min_interval_seconds", 5),
        max_retry_after_seconds=kwargs.pop("max_retry_after_seconds", 30),
        max_attempts_per_url=kwargs.pop("max_attempts_per_url", 3),
        origin_state=kwargs.pop("origin_state", None),
        on_origin_state_change=kwargs.pop("on_origin_state_change", None),
        monotonic=clock.monotonic,
        sleeper=clock.sleep,
        utcnow=clock.utcnow,
        **kwargs,
    )


def test_budget_serializes_per_origin_and_waits_five_seconds_between_starts() -> None:
    async def scenario() -> None:
        clock = FakeClock()
        session = FakeSession(clock)
        budget = make_budget(clock)
        await asyncio.gather(
            budget.get(session, "https://synthetic.example/a"),
            budget.get(session, "https://synthetic.example/b"),
        )
        assert session.max_active_by_origin["https://synthetic.example"] == 1
        starts = [call[1] for call in session.calls]
        assert starts[1] - starts[0] >= 5

    asyncio.run(scenario())


def test_budget_rejects_unreviewed_url_before_any_http_request() -> None:
    async def scenario() -> None:
        clock = FakeClock()
        session = FakeSession(clock)
        budget = make_budget(clock, allowed_urls=["https://synthetic.example/approved"])
        with pytest.raises(InvalidControlledRun, match="outside the reviewed FG2 lot"):
            await budget.get(session, "https://synthetic.example/unreviewed")
        assert session.calls == []
        assert budget.snapshot() == {"http_requests": 0, "unique_urls": 0}

    asyncio.run(scenario())


def test_budget_does_not_follow_redirect_outside_reviewed_url_scope() -> None:
    async def scenario() -> None:
        clock = FakeClock()
        session = FakeSession(
            clock,
            [FakeResponse(302, {"location": "/unreviewed"})],
        )
        budget = make_budget(clock, allowed_urls=["https://synthetic.example/approved"])
        with pytest.raises(OriginDeferred, match="outside the reviewed FG2 lot"):
            await budget.get(session, "https://synthetic.example/approved")
        assert len(session.calls) == 1
        assert session.calls[0][0] == "https://synthetic.example/approved"
        assert budget.snapshot() == {"http_requests": 1, "unique_urls": 1}

    asyncio.run(scenario())


def test_redirect_and_retry_requests_are_counted_and_retry_after_is_respected() -> None:
    async def scenario() -> None:
        clock = FakeClock()
        session = FakeSession(
            clock,
            [
                FakeResponse(302, {"location": "/redirected"}),
                FakeResponse(503, {"Retry-After": "7"}),
                FakeResponse(200),
            ],
        )
        budget = make_budget(clock)
        response = await budget.get(session, "https://synthetic.example/course")
        assert response.status_code == 200
        assert budget.http_requests == 3
        assert [call[0] for call in session.calls] == [
            "https://synthetic.example/course",
            "https://synthetic.example/redirected",
            "https://synthetic.example/redirected",
        ]
        assert session.calls[2][1] - session.calls[1][1] >= 7

    asyncio.run(scenario())


def test_redirects_count_as_http_requests_without_spending_another_unique_course_url() -> None:
    async def scenario() -> None:
        clock = FakeClock()
        session = FakeSession(
            clock,
            [FakeResponse(302, {"location": "/canonical"}), FakeResponse(200)],
        )
        budget = make_budget(clock, max_unique_urls=1)
        response = await budget.get(session, "https://synthetic.example/course")
        assert response.status_code == 200
        assert budget.http_requests == 2
        assert len(budget.unique_urls) == 1

    asyncio.run(scenario())


def test_default_port_urls_share_origin_budget_and_canonical_url_identity() -> None:
    async def scenario() -> None:
        clock = FakeClock()
        session = FakeSession(clock)
        budget = make_budget(clock)
        await budget.get(session, "https://synthetic.example/course")
        await budget.get(session, "https://synthetic.example:443/course")

        assert session.calls[1][1] - session.calls[0][1] >= 5
        assert budget.http_requests == 2
        assert budget.snapshot()["unique_urls"] == 1
        assert url_sha256("https://synthetic.example/course") == url_sha256(
            "https://synthetic.example:443/course"
        )

    asyncio.run(scenario())


@pytest.mark.parametrize("status", [403, 429])
def test_blocked_status_stops_origin_without_retry(status: int) -> None:
    async def scenario() -> None:
        clock = FakeClock()
        session = FakeSession(clock, [FakeResponse(status), FakeResponse(200)])
        budget = make_budget(clock)
        with pytest.raises(SourceBlocked):
            await budget.get(session, "https://synthetic.example/course")
        with pytest.raises(SourceBlocked):
            await budget.get(session, "https://synthetic.example/another")
        assert len(session.calls) == 1
        assert budget.http_requests == 1

    asyncio.run(scenario())


def test_retry_after_over_thirty_seconds_defers_origin_without_retry() -> None:
    async def scenario() -> None:
        clock = FakeClock()
        session = FakeSession(clock, [FakeResponse(503, {"Retry-After": "31"})])
        budget = make_budget(clock)
        with pytest.raises(OriginDeferred):
            await budget.get(session, "https://synthetic.example/course")
        assert budget.http_requests == 1
        assert len(session.calls) == 1

    asyncio.run(scenario())


def test_http_date_retry_after_is_honored() -> None:
    async def scenario() -> None:
        clock = FakeClock()
        retry_at = format_datetime(clock.utcnow() + timedelta(seconds=9), usegmt=True)
        session = FakeSession(
            clock,
            [FakeResponse(503, {"Retry-After": retry_at}), FakeResponse(200)],
        )
        budget = make_budget(clock)
        await budget.get(session, "https://synthetic.example/course")
        assert session.calls[1][1] - session.calls[0][1] >= 9

    asyncio.run(scenario())


def test_very_large_valid_retry_after_is_deferred_without_float_overflow() -> None:
    async def scenario() -> None:
        clock = FakeClock()
        session = FakeSession(clock, [FakeResponse(503, {"Retry-After": "9" * 5000})])
        budget = make_budget(clock)

        with pytest.raises(OriginDeferred):
            await budget.get(session, "https://synthetic.example/course")

        assert budget.http_requests == 1
        assert len(session.calls) == 1

    asyncio.run(scenario())


def test_retry_after_large_leading_zero_prefix_remains_exact() -> None:
    value = "0" * 5000 + "30"
    assert parse_retry_after(value, datetime(2026, 11, 9, tzinfo=timezone.utc)) == 30


def test_public_target_resolution_rejects_private_and_mixed_dns_answers() -> None:
    def answers(*_args, **_kwargs):
        return [
            (2, 1, 6, "", ("93.184.216.34", 443)),
            (2, 1, 6, "", ("10.20.30.40", 443)),
        ]

    with pytest.raises(UnsafePublicTarget):
        public_url_resolve_entry("https://127.0.0.1/course", resolver=answers)
    with pytest.raises(UnsafePublicTarget):
        public_url_resolve_entry("https://synthetic.example/course", resolver=answers)
    with pytest.raises(UnsafePublicTarget):
        public_url_resolve_entry("https://synthetic.example:8443/course", resolver=answers)


def test_public_target_resolution_pins_every_public_dns_answer() -> None:
    def answers(host: str, port: int, *, type: int):
        assert host == "synthetic.example"
        assert port == 443
        assert type == 1
        return [
            (2, 1, 6, "", ("93.184.216.34", 443)),
            (2, 1, 6, "", ("1.1.1.1", 443)),
        ]

    assert public_url_resolve_entry(
        "https://synthetic.example/course", resolver=answers
    ) == "synthetic.example:443:93.184.216.34,1.1.1.1"


def test_ssrf_guard_defers_before_starting_http_request() -> None:
    async def scenario() -> None:
        clock = FakeClock()
        session = FakeSession(clock)

        def reject(_url: str):
            raise UnsafePublicTarget("synthetic private address")

        async def must_not_send(*_args):
            raise AssertionError("unsafe target reached HTTP sender")

        budget = make_budget(
            clock,
            request_preparer=reject,
            requester=must_not_send,
        )
        with pytest.raises(OriginDeferred):
            await budget.get(session, "https://synthetic.example/course")

        assert budget.http_requests == 0
        assert session.calls == []

    asyncio.run(scenario())


def test_request_pin_is_recomputed_for_each_redirect_hop() -> None:
    async def scenario() -> None:
        clock = FakeClock()
        session = FakeSession(
            clock,
            [FakeResponse(302, {"location": "/canonical"}), FakeResponse(200)],
        )
        prepared: list[str] = []
        sent: list[tuple[str, object]] = []

        def prepare(url: str):
            prepared.append(url)
            return {"resolve": url}

        async def requester(client, url, pin, impersonate, timeout):
            sent.append((url, pin))
            return await client.get(
                url,
                impersonate=impersonate,
                timeout=timeout,
                allow_redirects=False,
            )

        budget = make_budget(
            clock,
            request_preparer=prepare,
            requester=requester,
        )
        response = await budget.get(session, "https://synthetic.example/course")

        assert response.status_code == 200
        assert prepared == [
            "https://synthetic.example/course",
            "https://synthetic.example/canonical",
        ]
        assert sent == [
            (prepared[0], {"resolve": prepared[0]}),
            (prepared[1], {"resolve": prepared[1]}),
        ]
        assert budget.http_requests == 2

    asyncio.run(scenario())


def test_total_http_budget_stops_before_starting_request_after_cap() -> None:
    async def scenario() -> None:
        clock = FakeClock()
        session = FakeSession(clock)
        budget = make_budget(clock, max_http_requests=5)
        for index in range(5):
            await budget.get(session, f"https://synthetic.example/course-{index}")
        with pytest.raises(RunBudgetExceeded):
            await budget.get(session, "https://synthetic.example/course-5")
        assert budget.http_requests == 5
        assert len(session.calls) == 5

    asyncio.run(scenario())


def test_default_candidate_limits_stop_at_ten_urls_and_twenty_http_requests() -> None:
    assert FG2_LIMITS == {
        "max_urls_per_institution": 10,
        "max_http_requests_per_institution": 20,
        "min_request_interval_seconds": 5,
        "max_retry_after_seconds": 30,
        "max_concurrent_requests_per_origin": 1,
        "max_attempts_per_url": 3,
    }

    async def scenario() -> None:
        clock = FakeClock()
        session = FakeSession(clock)
        budget = make_budget(clock)
        for _ in range(20):
            await budget.get(session, "https://synthetic.example/repeated")
        with pytest.raises(RunBudgetExceeded):
            await budget.get(session, "https://synthetic.example/repeated")
        assert budget.http_requests == 20
        assert budget.snapshot()["unique_urls"] == 1
        assert len(session.calls) == 20

        capped_urls = make_budget(clock, max_unique_urls=2)
        capped_session = FakeSession(clock)
        await capped_urls.get(capped_session, "https://synthetic.example/a")
        await capped_urls.get(capped_session, "https://synthetic.example/b")
        with pytest.raises(RunBudgetExceeded):
            await capped_urls.get(capped_session, "https://synthetic.example/c")
        assert capped_urls.snapshot()["unique_urls"] == 2
        assert len(capped_session.calls) == 2

    asyncio.run(scenario())


def _two_institution_manifest(path: Path) -> None:
    initialize_manifest(
        path,
        run_id="123456789",
        run_attempt=1,
        source_sha=SOURCE_SHA,
        institutions=[
            {
                "institution_id": institution_id,
                "profile_sha256": ("b" if index == 0 else "c") * 64,
                "seed_sha256": ("d" if index == 0 else "e") * 64,
                "http_requests": 0,
                "unique_urls": 0,
                "result": "preflight_passed",
            }
            for index, institution_id in enumerate(
                (INSTITUTION_ID, "00000000-0000-0000-0000-000000000002")
            )
        ],
    )


def _persist_origin_state(path: Path):
    def persist(origin_sha256: str, last_started: float | None, stop_reason: str | None) -> None:
        update_manifest_origin_state(
            path,
            origin_sha256=origin_sha256,
            last_started_monotonic=last_started,
            stop_reason=stop_reason,
        )

    return persist


def test_minimum_interval_survives_budget_reset_between_institutions(tmp_path: Path) -> None:
    async def scenario() -> None:
        path = tmp_path / "fg2_cohort.json"
        _two_institution_manifest(path)
        clock = FakeClock()
        persist = _persist_origin_state(path)
        first_session = FakeSession(clock)
        first_budget = make_budget(clock, on_origin_state_change=persist)
        await first_budget.get(first_session, "https://synthetic.example/first")

        current_manifest = FG2CohortManifest.load(path, allow_empty=True)
        second_session = FakeSession(clock)
        second_budget = make_budget(
            clock,
            origin_state=current_manifest.payload["origin_state"],
            on_origin_state_change=persist,
        )
        await second_budget.get(second_session, "https://synthetic.example/second")

        assert second_session.calls[0][1] - first_session.calls[0][1] >= 5
        manifest_text = path.read_text(encoding="utf-8")
        assert "synthetic.example" not in manifest_text
        assert len(current_manifest.payload["origin_state"]) == 1

    asyncio.run(scenario())


def test_blocked_origin_stays_stopped_after_budget_reset_between_institutions(tmp_path: Path) -> None:
    async def scenario() -> None:
        path = tmp_path / "fg2_cohort.json"
        _two_institution_manifest(path)
        clock = FakeClock()
        persist = _persist_origin_state(path)
        first_session = FakeSession(clock, [FakeResponse(429)])
        first_budget = make_budget(clock, on_origin_state_change=persist)
        with pytest.raises(SourceBlocked):
            await first_budget.get(first_session, "https://synthetic.example/first")

        current_manifest = FG2CohortManifest.load(path, allow_empty=True)
        second_session = FakeSession(clock)
        second_budget = make_budget(
            clock,
            origin_state=current_manifest.payload["origin_state"],
            on_origin_state_change=persist,
        )
        with pytest.raises(SourceBlocked):
            await second_budget.get(second_session, "https://synthetic.example/second")

        origin_state = next(iter(current_manifest.payload["origin_state"].values()))
        assert origin_state["stop_reason"] == "blocked"
        assert first_budget.http_requests == 1
        assert second_budget.http_requests == 0
        assert len(first_session.calls) == 1
        assert second_session.calls == []

    asyncio.run(scenario())


def _manifest_payload() -> dict:
    return {
        "schema_version": 1,
        "run_id": "123456789",
        "run_attempt": 1,
        "source_sha": SOURCE_SHA,
        "limits": {
            "max_urls_per_institution": 10,
            "max_http_requests_per_institution": 20,
            "min_request_interval_seconds": 5,
            "max_retry_after_seconds": 30,
            "max_concurrent_requests_per_origin": 1,
            "max_attempts_per_url": 3,
        },
        "institutions": [
            {
                "institution_id": INSTITUTION_ID,
                "profile_sha256": "b" * 64,
                "seed_sha256": "c" * 64,
                "http_requests": 2,
                "unique_urls": 1,
                "result": "complete",
            }
        ],
        "entries": [
            {
                "institution_id": INSTITUTION_ID,
                "staging_id": STAGING_ID,
                "course_id": "70000000-0000-0000-0000-000000000001",
                "url_sha256": "d" * 64,
                "content_sha256": "e" * 64,
                "kind": "refresh_existing",
            }
        ],
    }


def _write_manifest(path: Path, payload: dict | None = None) -> str:
    path.write_text(json.dumps(payload or _manifest_payload(), sort_keys=True), encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_manifest_is_bound_to_file_hash_run_attempt_and_candidate_sha(tmp_path: Path) -> None:
    path = tmp_path / "fg2_cohort.json"
    digest = _write_manifest(path)
    manifest = FG2CohortManifest.load(
        path,
        expected_sha256=digest,
        expected_run_id="123456789",
        expected_run_attempt=1,
        expected_source_sha=SOURCE_SHA,
    )
    assert manifest.staging_ids == (STAGING_ID,)
    assert manifest.institution_ids == (INSTITUTION_ID,)


def test_manifest_job_output_is_hash_bound_and_uuid_filters_are_closed() -> None:
    raw = json.dumps(_manifest_payload(), sort_keys=True, separators=(",", ":")).encode()
    encoded = base64.b64encode(raw).decode("ascii")
    digest = hashlib.sha256(raw).hexdigest()
    manifest = load_manifest_b64(
        encoded,
        expected_sha256=digest,
        expected_run_id="123456789",
        expected_run_attempt=1,
        expected_source_sha=SOURCE_SHA,
    )
    assert manifest.staging_ids == (STAGING_ID,)
    assert uuid_in_filter("id", manifest.staging_ids) == f"id=in.({STAGING_ID})"
    with pytest.raises(InvalidControlledRun):
        load_manifest_b64(
            encoded,
            expected_sha256="0" * 64,
            expected_run_id="123456789",
            expected_run_attempt=1,
            expected_source_sha=SOURCE_SHA,
        )
    with pytest.raises(InvalidControlledRun):
        uuid_in_filter("id", ["not-a-uuid"])


def test_manifest_rejects_hash_drift_unknown_ids_and_non_candidate_limits(tmp_path: Path) -> None:
    path = tmp_path / "fg2_cohort.json"
    digest = _write_manifest(path)
    with pytest.raises(InvalidControlledRun):
        FG2CohortManifest.load(path, expected_sha256="0" * 64)

    payload = _manifest_payload()
    payload["entries"][0]["staging_id"] = "not-a-uuid"
    digest = _write_manifest(path, payload)
    with pytest.raises(InvalidControlledRun):
        FG2CohortManifest.load(path, expected_sha256=digest)

    payload = _manifest_payload()
    payload["limits"]["max_http_requests_per_institution"] = 21
    digest = _write_manifest(path, payload)
    with pytest.raises(InvalidControlledRun):
        FG2CohortManifest.load(path, expected_sha256=digest)

    payload = _manifest_payload()
    payload["entries"][0]["course_id"] = None
    digest = _write_manifest(path, payload)
    with pytest.raises(InvalidControlledRun, match="classification does not match"):
        FG2CohortManifest.load(path, expected_sha256=digest)


@pytest.mark.parametrize("result", ["preflight_passed", "no_op", "failed"])
def test_manifest_rejects_downstream_entries_without_a_harvest_result(result: str) -> None:
    payload = _manifest_payload()
    payload["institutions"][0]["result"] = result

    with pytest.raises(InvalidControlledRun, match="not eligible for downstream work"):
        FG2CohortManifest.from_payload(payload)


def test_manifest_sha256_argument_is_required_only_for_controlled_mode() -> None:
    digest = "a" * 64
    assert require_manifest_sha256(None, None) is None
    assert require_manifest_sha256("manifest.json", digest) == digest

    with pytest.raises(InvalidControlledRun, match="requires an expected SHA-256"):
        require_manifest_sha256("manifest.json", None)
    with pytest.raises(InvalidControlledRun, match="requires an expected SHA-256"):
        require_manifest_sha256("manifest.json", "not-a-digest")
    with pytest.raises(InvalidControlledRun, match="without a manifest"):
        require_manifest_sha256(None, digest)


def test_manifest_rejects_duplicate_and_out_of_cohort_records(tmp_path: Path) -> None:
    path = tmp_path / "fg2_cohort.json"
    payload = _manifest_payload()
    payload["entries"].append(dict(payload["entries"][0]))
    digest = _write_manifest(path, payload)
    with pytest.raises(InvalidControlledRun):
        FG2CohortManifest.load(path, expected_sha256=digest)

    payload = _manifest_payload()
    digest = _write_manifest(path, payload)
    manifest = FG2CohortManifest.load(path, expected_sha256=digest)
    with pytest.raises(InvalidControlledRun):
        manifest.assert_stage_records(
            [{"id": STAGING_ID}, {"id": "40000000-0000-0000-0000-000000000099"}],
            allowed_ids=manifest.staging_ids,
            stage="cleansing",
        )

    manifest.assert_related_stage_records(
        [
            {"id": "50000000-0000-0000-0000-000000000001", "staging_id": STAGING_ID},
        ],
        foreign_key="staging_id",
        allowed_ids=manifest.staging_ids,
        stage="enrichment",
    )
    with pytest.raises(InvalidControlledRun):
        manifest.assert_related_stage_records(
            [
                {
                    "id": "50000000-0000-0000-0000-000000000002",
                    "staging_id": "40000000-0000-0000-0000-000000000099",
                },
            ],
            foreign_key="staging_id",
            allowed_ids=manifest.staging_ids,
            stage="enrichment",
        )


def _eligible_institution_and_profile() -> tuple[dict, dict]:
    return (
        {
            "id": INSTITUTION_ID,
            "website_url": "https://institution.example/",
        },
        {
            "discovery_enabled": True,
            "pipeline_enabled": True,
            "production_enabled": True,
            "circuit_open": False,
            "circuit_opened_at": None,
            "site_type": "traditional_ssr",
            "requires_stealth": False,
            "requires_cloudflare_bypass": False,
            "discovery_mode": "hardcoded_urls",
            "seed_urls": [
                "https://institution.example/programs/",
                "https://institution.example/programs/",
                "https://institution.example/careers/",
            ],
        },
    )


def test_profile_preflight_checks_all_gates_and_normalizes_seeds_without_network() -> None:
    institution, profile = _eligible_institution_and_profile()
    result = validate_controlled_profile(institution, profile)
    assert result["seed_urls"] == [
        "https://institution.example/programs/",
        "https://institution.example/careers/",
    ]
    assert len(result["profile_sha256"]) == 64
    assert len(result["seed_sha256"]) == 64
    assert result["circuit_expired"] is False

    profile_as_json = dict(profile)
    profile_as_json["seed_urls"] = json.dumps(profile["seed_urls"])
    json_result = validate_controlled_profile(institution, profile_as_json)
    assert json_result["profile_sha256"] == result["profile_sha256"]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("discovery_enabled", False),
        ("pipeline_enabled", False),
        ("production_enabled", False),
        ("site_type", "spa"),
        ("requires_stealth", True),
        ("requires_cloudflare_bypass", True),
        ("discovery_mode", "browser_bfs"),
    ],
)
def test_profile_preflight_rejects_ineligible_or_unbounded_profiles(field: str, value: object) -> None:
    institution, profile = _eligible_institution_and_profile()
    profile[field] = value
    with pytest.raises(InvalidControlledRun):
        validate_controlled_profile(institution, profile)


def test_profile_preflight_rejects_open_circuit_and_cross_origin_seed() -> None:
    institution, profile = _eligible_institution_and_profile()
    profile["circuit_open"] = True
    profile["circuit_opened_at"] = "2026-11-09T10:00:00+00:00"
    with pytest.raises(InvalidControlledRun, match="cooldown"):
        validate_controlled_profile(
            institution,
            profile,
            now=datetime(2026, 11, 9, 18, tzinfo=timezone.utc),
        )

    profile["circuit_open"] = False
    profile["circuit_opened_at"] = None
    profile["seed_urls"] = ["https://other.example/not-owned"]
    with pytest.raises(InvalidControlledRun, match="outside the institution origin"):
        validate_controlled_profile(institution, profile)


def test_expired_circuit_is_effective_only_in_memory_and_does_not_write_profile() -> None:
    institution, profile = _eligible_institution_and_profile()
    profile["circuit_open"] = True
    profile["circuit_opened_at"] = "2026-11-08T10:00:00+00:00"
    original = dict(profile)
    result = validate_controlled_profile(
        institution,
        profile,
        now=datetime(2026, 11, 9, 12, tzinfo=timezone.utc),
    )
    assert result["circuit_expired"] is True
    assert result["effective_profile"]["circuit_open"] is False
    assert result["effective_profile"]["circuit_opened_at"] is None
    assert profile == original


def test_manifest_lifecycle_freezes_run_cohort_and_records_hashes(tmp_path: Path) -> None:
    path = tmp_path / "fg2_cohort.json"
    institution = {
        "institution_id": INSTITUTION_ID,
        "profile_sha256": "b" * 64,
        "seed_sha256": "c" * 64,
        "http_requests": 0,
        "unique_urls": 0,
        "result": "preflight_passed",
    }
    initialize_manifest(
        path,
        run_id="123456789",
        run_attempt=1,
        source_sha=SOURCE_SHA,
        institutions=[institution],
    )
    entry = {
        "institution_id": INSTITUTION_ID,
        "staging_id": STAGING_ID,
        "course_id": "70000000-0000-0000-0000-000000000001",
        "url_sha256": "d" * 64,
        "content_sha256": "e" * 64,
        "kind": "refresh_existing",
    }
    digest = append_manifest_entry(path, entry)
    digest = update_manifest_institution(
        path,
        institution_id=INSTITUTION_ID,
        http_requests=3,
        unique_urls=2,
        result="complete",
    )
    manifest = FG2CohortManifest.load(
        path,
        expected_sha256=digest,
        expected_run_id="123456789",
        expected_run_attempt=1,
        expected_source_sha=SOURCE_SHA,
    )
    assert manifest.staging_ids == (STAGING_ID,)
    digest = update_manifest_institution(
        path,
        institution_id=INSTITUTION_ID,
        http_requests=3,
        unique_urls=2,
        result="complete",
    )
    final = FG2CohortManifest.load(path, expected_sha256=digest, allow_empty=False)
    assert final.payload["institutions"][0]["http_requests"] == 3
    assert final.payload["institutions"][0]["unique_urls"] == 2
    assert final.payload["institutions"][0]["result"] == "complete"


def test_manifest_records_protected_historical_rows_without_reopening_them(tmp_path: Path) -> None:
    path = tmp_path / "fg2_cohort.json"
    initialize_manifest(
        path,
        run_id="123456789",
        run_attempt=1,
        source_sha=SOURCE_SHA,
        institutions=[
            {
                "institution_id": INSTITUTION_ID,
                "profile_sha256": "b" * 64,
                "seed_sha256": "c" * 64,
                "http_requests": 0,
                "unique_urls": 0,
                "result": "preflight_passed",
            }
        ],
    )
    blocker = {
        "institution_id": INSTITUTION_ID,
        "staging_id": "40000000-0000-0000-0000-000000000088",
        "url_sha256": "f" * 64,
        "content_sha256": None,
        "status": "processed",
        "reason": "historical_staging_state_protected",
    }
    digest = append_manifest_blocker(path, blocker)
    manifest = FG2CohortManifest.load(path, expected_sha256=digest, allow_empty=True)
    assert manifest.payload["blocked_staging_rows"] == [blocker]
    assert manifest.payload["entries"] == []

    blocker["institution_id"] = "00000000-0000-0000-0000-000000000099"
    with pytest.raises(InvalidControlledRun):
        append_manifest_blocker(path, blocker)
