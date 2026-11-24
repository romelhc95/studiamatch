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
    SitemapBudgetYield,
    SourceBlocked,
    UnsafePublicTarget,
    append_manifest_entry,
    append_manifest_blocker,
    cleansed_url_sha256,
    cleansed_url_sha256_for_record,
    initialize_manifest,
    load_manifest_b64,
    require_manifest_sha256,
    stable_json_sha256,
    uuid_in_filter,
    update_manifest_institution,
    update_manifest_origin_state,
    url_sha256,
    public_url_resolve_entry,
    parse_retry_after,
    profile_url_policy_rejection,
    validate_public_redirect_target,
    validate_controlled_profile,
    validate_harvester_run_mode,
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


def test_same_origin_browser_subresources_use_http_budget_without_consuming_course_url_slots() -> None:
    async def scenario() -> None:
        clock = FakeClock()
        session = FakeSession(clock)
        detail = "https://synthetic.example/programas/curso-a"
        budget = make_budget(
            clock,
            max_unique_urls=1,
            allowed_urls=[detail],
        )
        await budget.get(session, detail, allowed_origin="https://synthetic.example")
        await budget.get(
            session,
            "https://synthetic.example/assets/app.js",
            allowed_origin="https://synthetic.example",
            request_kind="subresource",
        )
        assert budget.snapshot() == {"http_requests": 2, "unique_urls": 1}
        with pytest.raises(InvalidControlledRun):
            await budget.get(
                session,
                "https://cdn.synthetic.example/app.js",
                allowed_origin="https://synthetic.example",
                request_kind="subresource",
            )
        assert len(session.calls) == 2

    asyncio.run(scenario())


def test_browser_subresource_policy_allows_only_exact_configured_public_origins() -> None:
    website = "https://institution.example"
    allowed = {
        "allowed_resource_origins": ["https://cdn.institution.example"],
        "exclusion_patterns": ["/logout"],
        "allowed_url_patterns": ["/courses/"],
    }

    assert profile_url_policy_rejection(
        "https://cdn.institution.example/assets/app.js",
        website,
        allowed,
        role="subresource",
    ) is None
    assert profile_url_policy_rejection(
        "https://unlisted.example/assets/app.js",
        website,
        allowed,
        role="subresource",
    ) == "outside_institution_origin"
    assert profile_url_policy_rejection(
        "https://cdn.institution.example/logout",
        website,
        allowed,
        role="subresource",
    ) is None
    assert profile_url_policy_rejection(
        "https://cdn.institution.example/assets/app.js",
        website,
        {"allowed_resource_origins": ["https://cdn.institution.example/private"]},
        role="subresource",
    ) == "invalid_profile_url_policy"


def test_request_budget_revalidates_each_redirect_with_shared_profile_policy() -> None:
    async def scenario() -> None:
        clock = FakeClock()
        session = FakeSession(clock, [FakeResponse(302, {"location": "/news/"})])
        profile = {"exclusion_patterns": ["/news/"], "allowed_url_patterns": ["/courses/"]}
        validator = lambda url, kind: profile_url_policy_rejection(
            url,
            "https://synthetic.example",
            profile,
            role="course_detail" if kind == "detail" else "catalog_source",
        )
        budget = make_budget(clock, url_validator=validator)

        with pytest.raises(OriginDeferred, match="shared FG2 policy"):
            await budget.get(session, "https://synthetic.example/courses/program")

        assert [call[0] for call in session.calls] == [
            "https://synthetic.example/courses/program"
        ]
        assert budget.snapshot() == {"http_requests": 1, "unique_urls": 1}

    asyncio.run(scenario())


def test_budget_rejects_query_for_reviewed_url_before_any_http_request() -> None:
    async def scenario() -> None:
        clock = FakeClock()
        session = FakeSession(clock)
        url = "https://synthetic.example/catalog/?page=1"
        budget = make_budget(clock, allowed_urls=["https://synthetic.example/catalog"])

        with pytest.raises(InvalidControlledRun, match="cannot contain query data"):
            await budget.get(session, url)

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


def test_redirect_targets_count_against_the_unique_url_limit() -> None:
    async def scenario() -> None:
        clock = FakeClock()
        session = FakeSession(
            clock,
            [FakeResponse(302, {"location": "/canonical"}), FakeResponse(200)],
        )
        budget = make_budget(clock, max_unique_urls=2)
        response = await budget.get(session, "https://synthetic.example/course")
        assert response.status_code == 200
        assert budget.http_requests == 2
        assert len(budget.unique_urls) == 2
        assert budget.snapshot() == {"http_requests": 2, "unique_urls": 2}

    asyncio.run(scenario())


def test_redirect_is_not_followed_when_its_target_exceeds_unique_url_limit() -> None:
    async def scenario() -> None:
        clock = FakeClock()
        session = FakeSession(
            clock,
            [FakeResponse(302, {"location": "/canonical"}), FakeResponse(200)],
        )
        budget = make_budget(clock, max_unique_urls=1)
        with pytest.raises(RunBudgetExceeded, match="unique URL budget exhausted"):
            await budget.get(session, "https://synthetic.example/course")
        assert len(session.calls) == 1
        assert budget.snapshot() == {"http_requests": 1, "unique_urls": 1}

    asyncio.run(scenario())


def test_sitemap_unique_url_allocation_reserves_one_detail_and_one_redirect() -> None:
    async def scenario() -> None:
        clock = FakeClock()
        session = FakeSession(
            clock,
            [
                FakeResponse(200),
                FakeResponse(200),
                FakeResponse(302, {"location": "/canonical"}),
                FakeResponse(200),
            ],
        )

        async def requester(current_session, url, _prepared, impersonate, timeout):
            return await current_session.get(url, impersonate=impersonate, timeout=timeout)

        budget = make_budget(
            clock,
            max_unique_urls=4,
            max_http_requests=8,
            request_preparer=lambda url: url,
            requester=requester,
        )
        await budget.get(session, "https://synthetic.example/sitemap-root", request_kind="sitemap")
        await budget.get(session, "https://synthetic.example/sitemap-child", request_kind="sitemap")
        with pytest.raises(SitemapBudgetYield, match="detail URL capacity remains reserved"):
            await budget.get(session, "https://synthetic.example/sitemap-extra", request_kind="sitemap")

        detail = await budget.get(session, "https://synthetic.example/course")
        assert detail.status_code == 200
        assert session.calls[-2][0] == "https://synthetic.example/course"
        assert session.calls[-1][0] == "https://synthetic.example/canonical"
        assert budget.snapshot() == {"http_requests": 4, "unique_urls": 4}

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


@pytest.mark.parametrize("status", [403, 429])
def test_blocked_origin_does_not_retry_and_keeps_other_reviewed_origin_available(status: int) -> None:
    async def scenario() -> None:
        clock = FakeClock()
        origin_state: dict[str, dict] = {}
        blocked_url = "https://blocked.synthetic.example/first"
        allowed_url = "https://approved.synthetic.example/second"
        blocked_headers = {"Retry-After": "1"} if status == 429 else {}
        blocked_session = FakeSession(
            clock,
            [FakeResponse(status, blocked_headers), FakeResponse(200)],
        )
        blocked_budget = make_budget(
            clock,
            allowed_urls=[blocked_url],
            origin_state=origin_state,
        )

        with pytest.raises(SourceBlocked):
            await blocked_budget.get(blocked_session, blocked_url)

        assert len(blocked_session.calls) == 1
        assert blocked_session.calls[0][0] == blocked_url
        assert blocked_budget.http_requests == 1

        allowed_session = FakeSession(clock, [FakeResponse(200)])
        allowed_budget = make_budget(
            clock,
            allowed_urls=[allowed_url],
            origin_state=origin_state,
        )
        response = await allowed_budget.get(allowed_session, allowed_url)

        assert response.status_code == 200
        assert len(allowed_session.calls) == 1
        assert allowed_budget.http_requests == 1

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


def test_public_redirect_to_another_public_origin_is_validated_and_pinned() -> None:
    def answers(host: str, port: int, *, type: int):
        assert host == "catalog.example"
        assert port == 443
        assert type == 1
        return [(2, 1, 6, "", ("93.184.216.34", 443))]

    target, pin = validate_public_redirect_target(
        "https://www.institution.example/programs/",
        "https://catalog.example/catalog/",
        resolver=answers,
    )

    assert target == "https://catalog.example/catalog/"
    assert pin == "catalog.example:443:93.184.216.34"


def test_ssrf_guard_deferral_persists_before_starting_http_request(tmp_path: Path) -> None:
    async def scenario() -> None:
        clock = FakeClock()
        session = FakeSession(clock)
        manifest_path = tmp_path / "fg2_cohort.json"
        _two_institution_manifest(manifest_path)

        def reject(_url: str):
            raise UnsafePublicTarget("synthetic private address")

        async def must_not_send(*_args):
            raise AssertionError("unsafe target reached HTTP sender")

        budget = make_budget(
            clock,
            request_preparer=reject,
            requester=must_not_send,
            on_origin_state_change=_persist_origin_state(manifest_path),
        )
        with pytest.raises(OriginDeferred):
            await budget.get(session, "https://synthetic.example/course")

        assert budget.http_requests == 0
        assert session.calls == []
        manifest = FG2CohortManifest.load(manifest_path, allow_empty=True)
        state = next(iter(manifest.payload["origin_state"].values()))
        assert state == {"last_started_monotonic": None, "stop_reason": "deferred"}

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
        "https://institution.example/programs",
        "https://institution.example/careers",
    ]
    assert len(result["profile_sha256"]) == 64
    assert len(result["seed_sha256"]) == 64
    assert result["circuit_expired"] is False

    profile_as_json = dict(profile)
    profile_as_json["seed_urls"] = json.dumps(profile["seed_urls"])
    json_result = validate_controlled_profile(institution, profile_as_json)
    assert json_result["profile_sha256"] == result["profile_sha256"]


def test_scheduled_sitemap_uses_the_mode_default_instead_of_course_page_seeds() -> None:
    institution, profile = _eligible_institution_and_profile()
    profile["discovery_mode"] = "sitemap_bfs"
    profile["seed_urls"] = ["https://institution.example/catalog/program-one"]

    scheduled = validate_controlled_profile(
        institution,
        profile,
        scheduled_cohort=True,
    )
    controlled_manual = validate_controlled_profile(institution, profile)

    assert scheduled["seed_urls"] == ["https://institution.example/sitemap.xml"]
    assert controlled_manual["seed_urls"] == profile["seed_urls"]


def test_controlled_profile_rejects_compressed_sitemap_seed_before_source_access() -> None:
    institution, profile = _eligible_institution_and_profile()
    profile["discovery_mode"] = "sitemap_bfs"
    profile["seed_urls"] = ["https://institution.example/sitemap.xml.gz"]

    with pytest.raises(InvalidControlledRun, match="compressed sitemap"):
        validate_controlled_profile(institution, profile)


def test_profile_preflight_accepts_an_ordered_reviewed_subset_of_configured_seeds() -> None:
    institution, profile = _eligible_institution_and_profile()
    profile["seed_urls"] = [
        f"https://institution.example/program-{index:02d}/" for index in range(1, 13)
    ]
    default = validate_controlled_profile(institution, profile)
    selected = [profile["seed_urls"][10], profile["seed_urls"][11]]

    result = validate_controlled_profile(
        institution,
        profile,
        selected_seed_urls=selected,
    )

    expected_selected = [
        "https://institution.example/program-11",
        "https://institution.example/program-12",
    ]
    assert result["seed_urls"] == expected_selected
    assert result["profile_sha256"] == default["profile_sha256"]
    assert result["seed_sha256"] == stable_json_sha256(expected_selected)
    assert result["seed_sha256"] != default["seed_sha256"]


@pytest.mark.parametrize("scheduled_cohort", [False, True])
def test_hardcoded_preflight_selects_runtime_admissible_urls_in_profile_order(
    scheduled_cohort: bool,
) -> None:
    institution, profile = _eligible_institution_and_profile()
    profile["seed_urls"] = [
        "https://institution.example/pregrado/hidden/",
        "https://institution.example/courses/first/",
        "https://institution.example/catalog/",
        "https://institution.example/courses/file.pdf",
        "https://institution.example/courses/second/",
    ]
    profile["exclusion_patterns"] = ["/pregrado/"]
    profile["allowed_url_patterns"] = ["/courses/"]

    result = validate_controlled_profile(
        institution,
        profile,
        scheduled_cohort=scheduled_cohort,
    )

    assert result["seed_urls"] == [
        "https://institution.example/courses/first",
        "https://institution.example/courses/second",
    ]


def test_reviewed_hardcoded_lot_rejects_partially_or_completely_excluded_urls() -> None:
    institution, profile = _eligible_institution_and_profile()
    profile["seed_urls"] = [
        "https://institution.example/pregrado/hidden/",
        "https://institution.example/courses/visible/",
    ]
    profile["exclusion_patterns"] = ["/pregrado/"]

    with pytest.raises(InvalidControlledRun, match="runtime-rejected URL"):
        validate_controlled_profile(
            institution,
            profile,
            selected_seed_urls=profile["seed_urls"],
        )
    with pytest.raises(InvalidControlledRun, match="runtime-rejected URL"):
        validate_controlled_profile(
            institution,
            profile,
            selected_seed_urls=[profile["seed_urls"][0]],
        )


def test_sitemap_discovery_seed_is_not_filtered_as_a_course_detail_url() -> None:
    institution, profile = _eligible_institution_and_profile()
    profile.update(
        discovery_mode="sitemap_bfs",
        seed_urls=["https://institution.example/sitemap.xml"],
        exclusion_patterns=["sitemap"],
        allowed_url_patterns=["/program/"],
    )

    result = validate_controlled_profile(institution, profile, scheduled_cohort=True)

    assert result["seed_urls"] == ["https://institution.example/sitemap.xml"]


def test_paginated_catalog_source_is_not_filtered_as_a_course_detail_url() -> None:
    institution, profile = _eligible_institution_and_profile()
    profile.update(
        discovery_mode="paginated_catalog",
        catalog_url_patterns=["https://institution.example/catalog/?page={page}"],
        exclusion_patterns=["/catalog/"],
        allowed_url_patterns=["/program/"],
    )

    result = validate_controlled_profile(institution, profile)

    assert result["seed_urls"] == ["https://institution.example/catalog/?page=1"]


def test_scheduled_paginated_catalog_freezes_all_bounded_query_pages() -> None:
    institution, profile = _eligible_institution_and_profile()
    profile.update(
        discovery_mode="paginated_catalog",
        catalog_url_patterns=["https://institution.example/catalog/?page={page}&limit=20"],
        catalog_max_pages=3,
    )

    result = validate_controlled_profile(institution, profile, scheduled_cohort=True)

    assert result["seed_urls"] == ["https://institution.example/catalog/?limit=20&page=1"]
    assert result["source_urls"] == [
        "https://institution.example/catalog/?limit=20&page=1",
        "https://institution.example/catalog/?limit=20&page=2",
        "https://institution.example/catalog/?limit=20&page=3",
    ]
    assert result["effective_profile"]["catalog_max_pages"] == 3


def test_scheduled_paginated_catalog_caps_source_pages_to_reserved_detail_budget() -> None:
    institution, profile = _eligible_institution_and_profile()
    profile.update(
        discovery_mode="paginated_catalog",
        catalog_url_patterns=["https://institution.example/catalog/?page={page}"],
        catalog_max_pages=100,
    )

    result = validate_controlled_profile(institution, profile, scheduled_cohort=True)

    assert len(result["source_urls"]) == 8
    assert result["source_urls"][0].endswith("page=1")
    assert result["source_urls"][-1].endswith("page=8")
    assert result["effective_profile"]["catalog_max_pages"] == 8


def test_approved_lot_preflight_preserves_bounded_catalog_pagination_query() -> None:
    institution, profile = _eligible_institution_and_profile()
    source_seed = "https://institution.example/catalog/?page=1"
    profile.update(
        discovery_mode="paginated_catalog",
        catalog_url_patterns=["https://institution.example/catalog/?page={page}"],
    )

    accepted = validate_controlled_profile(
        institution,
        profile,
        selected_seed_urls=[source_seed],
    )
    assert accepted["seed_urls"] == [source_seed]
    assert accepted["source_urls"] == [
        f"https://institution.example/catalog/?page={page}"
        for page in range(1, 6)
    ]

    profile["catalog_url_patterns"] = ["https://institution.example/catalog/?page={page}&utm_source=synthetic"]
    tracking_source = "https://institution.example/catalog/?page=1&utm_source=synthetic"
    normalized = validate_controlled_profile(
        institution,
        profile,
        selected_seed_urls=[tracking_source],
    )
    assert normalized["seed_urls"] == [source_seed]

    profile["catalog_url_patterns"] = ["https://institution.example/catalog/?token={page}"]
    with pytest.raises(InvalidControlledRun, match="pagination parameter"):
        validate_controlled_profile(institution, profile)


def test_discovery_sources_still_require_approved_lot_membership() -> None:
    profile = {
        "exclusion_patterns": ["/catalog/"],
        "allowed_url_patterns": ["/program/"],
    }

    rejection = profile_url_policy_rejection(
        "https://institution.example/catalog/?page=1",
        "https://institution.example/",
        profile,
        approved_lot_scope={"https://institution.example/program/approved/"},
        role="catalog_source",
    )

    assert rejection == "outside_approved_lot"


def test_catalog_source_uses_source_rules_while_extracted_courses_use_detail_rules() -> None:
    catalog_url = "https://institution.example/catalog/?page=1"
    profile = {
        "exclusion_patterns": ["/catalog"],
        "allowed_url_patterns": ["/program/"],
    }
    approved_scope = {
        "https://institution.example/catalog",
        "https://institution.example/program/approved",
    }

    assert profile_url_policy_rejection(
        catalog_url,
        "https://institution.example/",
        profile,
        approved_lot_scope=approved_scope,
        role="catalog_source",
    ) is None
    assert profile_url_policy_rejection(
        catalog_url,
        "https://institution.example/",
        profile,
        approved_lot_scope=approved_scope,
        role="course_detail",
    ) == "excluded_by_profile"
    assert profile_url_policy_rejection(
        "https://institution.example/program/approved/",
        "https://institution.example/",
        profile,
        approved_lot_scope=approved_scope,
        role="course_detail",
    ) is None


def test_runtime_detail_policy_normalizes_query_before_allow_and_scope_checks() -> None:
    from scripts.core.universal_harvester import UniversalHarvester

    harvester = object.__new__(UniversalHarvester)
    harvester.institution = {"website_url": "https://institution.example/"}
    harvester.approved_lot_scope = {"https://institution.example/program"}
    harvester.profile = {
        "allowed_url_patterns": ["?campaign=allow-only-sentinel"],
    }

    assert not harvester._is_valid_crawl_url(
        "https://institution.example/program/?campaign=allow-only-sentinel"
    )

    harvester.profile = {"allowed_url_patterns": ["re:^/program$"]}
    assert harvester._is_valid_crawl_url(
        "https://institution.example/en/program/?campaign=not-policy-input"
    )


def test_shared_profile_policy_logs_sanitized_regex_failures_and_fails_closed(caplog) -> None:
    private_url = "https://institution.example/private-url-sentinel/"
    private_pattern = "private-regex-sentinel"

    dependency_rejection = profile_url_policy_rejection(
        private_url,
        "https://institution.example/",
        {"exclusion_patterns": [f"re:{private_pattern}"]},
        regex_module=None,
    )
    assert dependency_rejection == "invalid_profile_url_policy"
    assert "category=dependency_unavailable" in caplog.text
    assert private_url not in caplog.text
    assert private_pattern not in caplog.text

    caplog.clear()

    class BrokenRegex:
        IGNORECASE = 0

        @staticmethod
        def search(*_args, **_kwargs):
            raise RuntimeError("private regex exception sentinel")

    evaluation_rejection = profile_url_policy_rejection(
        private_url,
        "https://institution.example/",
        {"allowed_url_patterns": [f"re:{private_pattern}"]},
        regex_module=BrokenRegex,
    )
    assert evaluation_rejection == "invalid_profile_url_policy"
    assert "category=evaluation_failed" in caplog.text
    assert private_url not in caplog.text
    assert private_pattern not in caplog.text
    assert "private regex exception sentinel" not in caplog.text


def test_shared_profile_policy_logs_unsafe_regex_rules_and_fails_closed(caplog) -> None:
    private_url = "https://institution.example/program/private-url-sentinel/"
    private_pattern = "private-pattern-sentinel(a+)+"
    profile = {
        "exclusion_patterns": [f"re:{private_pattern}"],
        "allowed_url_patterns": [f"re:{private_pattern}"],
    }

    rejection = profile_url_policy_rejection(
        private_url,
        "https://institution.example/",
        profile,
    )

    assert rejection == "invalid_profile_url_policy"
    assert "category=unsafe_exclusion_complexity" in caplog.text
    assert "category=unsafe_allow_pattern_complexity" in caplog.text
    assert private_url not in caplog.text
    assert private_pattern not in caplog.text


def test_preflight_fails_closed_when_all_configured_course_seeds_are_excluded() -> None:
    institution, profile = _eligible_institution_and_profile()
    profile["seed_urls"] = [
        "https://institution.example/pregrado/hidden-one/",
        "https://institution.example/pregrado/hidden-two/",
    ]
    profile["exclusion_patterns"] = ["/pregrado/"]

    with pytest.raises(InvalidControlledRun, match="no runtime-eligible seed URLs"):
        validate_controlled_profile(institution, profile)


def test_fg2_265_approved_ten_seed_lot_is_rejected_when_profile_excludes_all_details() -> None:
    """Match the #265 failure shape: approved hardcoded seeds all conflict with exclusions."""
    institution, profile = _eligible_institution_and_profile()
    selected_seeds = [
        f"https://institution.example/pregrado/programa-{index}/"
        for index in range(10)
    ]
    profile["seed_urls"] = selected_seeds
    profile["exclusion_patterns"] = ["/pregrado/"]

    # The selector cannot choose an institution with no runtime-eligible detail.
    with pytest.raises(InvalidControlledRun, match="no runtime-eligible seed URLs"):
        validate_controlled_profile(institution, profile)

    # An already reviewed lot cannot override the same profile exclusion.
    with pytest.raises(InvalidControlledRun, match="runtime-rejected URL"):
        validate_controlled_profile(
            institution,
            profile,
            selected_seed_urls=selected_seeds,
        )


def test_scheduled_hardcoded_preflight_uses_runtime_normalized_seed_for_policy() -> None:
    institution, profile = _eligible_institution_and_profile()
    raw_seed = "https://institution.example/program/"
    profile["seed_urls"] = [raw_seed]
    profile["allowed_url_patterns"] = ["re:^/program$"]

    preflight = validate_controlled_profile(
        institution,
        profile,
        scheduled_cohort=True,
    )

    assert preflight["seed_urls"] == ["https://institution.example/program"]
    assert profile_url_policy_rejection(
        preflight["seed_urls"][0],
        institution["website_url"],
        profile,
    ) is None


def test_scheduled_hardcoded_preflight_does_not_admit_query_only_allow_match() -> None:
    institution, profile = _eligible_institution_and_profile()
    profile["seed_urls"] = ["https://institution.example/program/"]
    profile["allowed_url_patterns"] = ["?campaign=private-sentinel"]

    with pytest.raises(InvalidControlledRun, match="no runtime-eligible seed URLs"):
        validate_controlled_profile(
            institution,
            profile,
            scheduled_cohort=True,
        )


def test_preflight_and_runtime_keep_trailing_slash_exclusion_after_normalization() -> None:
    institution, profile = _eligible_institution_and_profile()
    profile["seed_urls"] = [
        "https://institution.example/pregrado/",
        "https://institution.example/courses/valid/",
    ]
    profile["exclusion_patterns"] = ["/pregrado/"]
    profile["allowed_url_patterns"] = ["/courses/"]

    result = validate_controlled_profile(institution, profile)

    assert result["seed_urls"] == ["https://institution.example/courses/valid"]
    assert profile_url_policy_rejection(
        "https://institution.example/pregrado/",
        institution["website_url"],
        profile,
    ) == "excluded_by_profile"


def test_controlled_pipeline_eligibility_does_not_imply_public_activation() -> None:
    institution, profile = _eligible_institution_and_profile()
    profile["production_enabled"] = False

    result = validate_controlled_profile(institution, profile)

    assert result["seed_urls"]
    assert result["effective_profile"]["production_enabled"] is False


@pytest.mark.parametrize(
    ("selected", "message"),
    [
        (["https://institution.example/not-configured/"], "outside the configured profile"),
        (["https://institution.example/program-02/", "https://institution.example/program-01/"], "order differs"),
        (["https://institution.example/program-01/", "https://institution.example/program-01/"], "contains duplicates"),
        (["https://elsewhere.example/program-01/"], "outside the institution origin"),
    ],
)
def test_profile_preflight_rejects_invalid_reviewed_seed_subsets(
    selected: list[str], message: str
) -> None:
    institution, profile = _eligible_institution_and_profile()
    profile["seed_urls"] = [
        "https://institution.example/program-01/",
        "https://institution.example/program-02/",
    ]

    with pytest.raises(InvalidControlledRun, match=message):
        validate_controlled_profile(
            institution,
            profile,
            selected_seed_urls=selected,
        )


def test_profile_preflight_rejects_reviewed_seed_subset_over_limit() -> None:
    institution, profile = _eligible_institution_and_profile()
    profile["seed_urls"] = [
        f"https://institution.example/program-{index:02d}/" for index in range(1, 13)
    ]

    with pytest.raises(InvalidControlledRun, match="exceeds the institution URL limit"):
        validate_controlled_profile(
            institution,
            profile,
            selected_seed_urls=profile["seed_urls"][:11],
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("discovery_enabled", False),
        ("pipeline_enabled", False),
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


@pytest.mark.parametrize(
    ("effective_url", "canonical_url", "selected_url"),
    [
        (
            "https://source.example/program/redirected",
            "https://catalog.example/program/presentacion/",
            "https://catalog.example/program/",
        ),
        (
            "https://source.example/program/redirected/presentacion/",
            None,
            "https://source.example/program/redirected/",
        ),
    ],
)
def test_manifest_cleanse_hash_uses_cleansing_identity_precedence(
    effective_url: str,
    canonical_url: str | None,
    selected_url: str,
) -> None:
    requested_url = "https://source.example/program/requested"
    actual = cleansed_url_sha256_for_record(
        requested_url,
        effective_url=effective_url,
        canonical_url=canonical_url,
    )

    assert actual == cleansed_url_sha256(selected_url)
    assert actual != cleansed_url_sha256(requested_url)


def test_schedule_child_mode_requires_main_schedule_and_no_manual_lot() -> None:
    args = {
        "controlled": False,
        "scheduled": True,
        "cohort_manifest": "/tmp/cohort.json",
        "approved_lot_manifest": None,
        "approved_lot_reference": None,
        "approved_lot_sha256": None,
        "max_urls": 10,
        "event_name": "schedule",
        "git_ref": "refs/heads/main",
    }

    assert validate_harvester_run_mode(**args) == "scheduled_cohort"

    with pytest.raises(InvalidControlledRun, match="main-branch schedule"):
        validate_harvester_run_mode(**{**args, "git_ref": "refs/heads/desarrollo"})
    with pytest.raises(InvalidControlledRun, match="only the exact URL bound"):
        validate_harvester_run_mode(
            **{**args, "approved_lot_reference": "manual-reviewed-lot"}
        )


def test_controlled_first_run_requires_manual_dispatch_on_main() -> None:
    args = {
        "controlled": True,
        "scheduled": False,
        "cohort_manifest": "/tmp/cohort.json",
        "approved_lot_manifest": "/tmp/approved-lot.json",
        "approved_lot_reference": "human-reviewed-lot",
        "approved_lot_sha256": "a" * 64,
        "max_urls": 10,
        "event_name": "workflow_dispatch",
        "git_ref": "refs/heads/main",
    }

    assert validate_harvester_run_mode(**args) == "controlled_first_run"

    with pytest.raises(InvalidControlledRun, match="manual workflow_dispatch on main"):
        validate_harvester_run_mode(**{**args, "event_name": "schedule"})
    with pytest.raises(InvalidControlledRun, match="manual workflow_dispatch on main"):
        validate_harvester_run_mode(**{**args, "git_ref": "refs/heads/desarrollo"})
