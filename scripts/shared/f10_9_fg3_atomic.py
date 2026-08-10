from __future__ import annotations

import hashlib
import json
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Mapping
from urllib.parse import quote

from .safe_http import (
    DEFAULT_POLICY,
    SafeHTTPPolicy,
    UnsafeURL,
    safe_get,
    safe_head,
)


TRANSIENT_HTTP = frozenset({408, 425, 429, 500, 502, 503, 504})
GONE_HTTP = frozenset({404, 410})
GET_REQUIRED_HTTP = frozenset({403, 404, 405, 410, 501})
TRANSIENT_SAFE_REASONS = frozenset(
    {
        "SAFE_TOTAL_TIMEOUT",
        "SAFE_DNS_FAILURE",
        "SAFE_DNS_EMPTY",
        "SAFE_TLS_VERIFY",
        "SAFE_TRANSPORT_FAILURE",
    }
)
MAX_HTTP_ATTEMPTS = 3
RETRY_DELAYS = (0.05, 0.1)
MANIFEST_SCHEMA = "f10.9-p4-fg3-atomic-manifest.v1"


@dataclass(frozen=True)
class CourseState:
    course_id: object
    url: str
    is_active: bool
    last_404_at: str | None
    start_date: str | None


@dataclass(frozen=True)
class ProbeResult:
    classification: str
    reason: str
    attempts: int


@dataclass(frozen=True)
class MutationPlan:
    course: CourseState
    kind: str
    expected: Mapping[str, object]
    desired: Mapping[str, object]


@dataclass(frozen=True)
class FG3RunResult:
    exit_code: int
    result: str
    manifest: Mapping[str, object]


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def _fingerprint(value: object) -> str:
    material = "studiamatch:f10.9:p4:manifest:v1\0" + _canonical_json(value)
    return "sha256:" + hashlib.sha256(material.encode("utf-8")).hexdigest()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_timestamp(value: str | None) -> datetime | None:
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _retry_delay(response: object | None, retry_index: int) -> float:
    headers = getattr(response, "headers", {}) or {}
    raw = next(
        (value for key, value in headers.items() if str(key).lower() == "retry-after"),
        None,
    )
    if raw is not None:
        try:
            return max(0.0, min(float(raw), 1.0))
        except (TypeError, ValueError):
            pass
    return RETRY_DELAYS[min(retry_index, len(RETRY_DELAYS) - 1)]


def probe_course(
    course: CourseState,
    *,
    head: Callable[..., object] = safe_head,
    get: Callable[..., object] = safe_get,
    policy: SafeHTTPPolicy = DEFAULT_POLICY,
    sleeper: Callable[[float], None] = time.sleep,
) -> ProbeResult:
    """Probe one URL with a single, bounded three-call budget."""
    method = "HEAD"
    attempts = 0
    retry_index = 0
    while attempts < MAX_HTTP_ATTEMPTS:
        attempts += 1
        transport = head if method == "HEAD" else get
        response: object | None = None
        try:
            response = transport(course.url, policy=policy)
        except UnsafeURL as exc:
            if exc.reason_code in TRANSIENT_SAFE_REASONS and attempts < MAX_HTTP_ATTEMPTS:
                sleeper(_retry_delay(None, retry_index))
                retry_index += 1
                continue
            reason = (
                "HTTP_TRANSIENT_EXHAUSTED"
                if exc.reason_code in TRANSIENT_SAFE_REASONS
                else "HTTP_UNSAFE_TARGET"
            )
            return ProbeResult("INCONCLUSIVE", reason, attempts)
        except Exception:
            if attempts < MAX_HTTP_ATTEMPTS:
                sleeper(_retry_delay(None, retry_index))
                retry_index += 1
                continue
            return ProbeResult("INCONCLUSIVE", "HTTP_TRANSPORT_EXHAUSTED", attempts)

        status = int(getattr(response, "status_code", 0))
        if status in TRANSIENT_HTTP:
            if attempts < MAX_HTTP_ATTEMPTS:
                sleeper(_retry_delay(response, retry_index))
                retry_index += 1
                continue
            return ProbeResult("INCONCLUSIVE", "HTTP_TRANSIENT_EXHAUSTED", attempts)

        if method == "HEAD":
            if 200 <= status < 300:
                return ProbeResult("HEALTHY", "HEAD_2XX", attempts)
            if status in GET_REQUIRED_HTTP:
                method = "GET"
                continue
            return ProbeResult("INCONCLUSIVE", "HTTP_UNHANDLED", attempts)

        if 200 <= status < 300:
            return ProbeResult("HEALTHY", "GET_2XX", attempts)
        if status in GONE_HTTP:
            return ProbeResult("GONE", "GET_CONFIRMED_GONE", attempts)
        if status == 403:
            return ProbeResult("INCONCLUSIVE", "GET_403", attempts)
        return ProbeResult("INCONCLUSIVE", "HTTP_UNHANDLED", attempts)

    return ProbeResult("INCONCLUSIVE", "HTTP_ATTEMPT_BUDGET", attempts)


def _course_from_row(row: Mapping[str, object]) -> CourseState:
    required = {"id", "url", "is_active", "last_404_at", "start_date"}
    if not required.issubset(row) or row["id"] is None or not isinstance(row["url"], str):
        raise ValueError("FG3_COLLECTION_ROW_INVALID")
    if not isinstance(row["is_active"], bool):
        raise ValueError("FG3_COLLECTION_ROW_INVALID")
    return CourseState(
        course_id=row["id"],
        url=row["url"],
        is_active=row["is_active"],
        last_404_at=None if row["last_404_at"] is None else str(row["last_404_at"]),
        start_date=None if row["start_date"] is None else str(row["start_date"]),
    )


def collect_courses(db: object, *, institution_id: str | None, limit: int | None) -> list[CourseState]:
    filters = "is_active=eq.true"
    if institution_id:
        filters += "&institution_id=eq." + quote(str(institution_id), safe="")
    expected = db.count_service_raise("courses", filters=filters)
    if isinstance(expected, bool) or not isinstance(expected, int) or expected < 0:
        raise ValueError("FG3_COLLECTION_INVALID")
    rows = db.select_all_service(
        "courses",
        filters=filters,
        columns="id,url,is_active,last_404_at,start_date",
        batch_size=1000,
        order="id.asc",
    )
    if not isinstance(rows, list) or len(rows) != expected:
        raise ValueError("FG3_COLLECTION_INVALID")
    if db.count_service_raise("courses", filters=filters) != expected:
        raise ValueError("FG3_COLLECTION_INVALID")
    if limit is not None:
        if limit < 0:
            raise ValueError("FG3_LIMIT_INVALID")
        rows = rows[:limit]
    return [_course_from_row(row) for row in rows]


def aggregate_plans(
    courses: list[CourseState],
    probes: Mapping[object, ProbeResult],
    *,
    now: datetime,
) -> list[MutationPlan]:
    plans: list[MutationPlan] = []
    grace_cutoff = now - timedelta(days=90)
    for course in courses:
        probe = probes[course.course_id]
        expected = {
            "is_active": course.is_active,
            "last_404_at": course.last_404_at,
            "url": course.url,
            "start_date": course.start_date,
        }
        desired = dict(expected)
        kinds: list[str] = []
        start_date = _parse_date(course.start_date)
        if start_date is not None and start_date < grace_cutoff:
            desired["is_active"] = False
            kinds.append("EXPIRE")
        if probe.classification == "HEALTHY" and course.last_404_at is not None:
            desired["last_404_at"] = None
            kinds.append("RECOVER")
        elif probe.classification == "GONE":
            last_gone = _parse_timestamp(course.last_404_at)
            if course.last_404_at is None:
                desired["last_404_at"] = now.isoformat().replace("+00:00", "Z")
                kinds.append("FIRST_GONE_FLAG")
            elif last_gone is None:
                # Invalid persisted evidence cannot authorize a lifecycle mutation.
                raise ValueError("FG3_LAST_GONE_STATE_INVALID")
            elif now > last_gone + timedelta(days=3):
                desired["is_active"] = False
                kinds.append("DEACTIVATE_PERSISTENT_GONE")
        changed = {key: value for key, value in desired.items() if expected[key] != value}
        if changed:
            plans.append(
                MutationPlan(
                    course=course,
                    kind="+".join(sorted(kinds)),
                    expected=expected,
                    desired=changed,
                )
            )
    return plans


def _postgrest_value(value: object) -> str:
    if value is None:
        return "is.null"
    if isinstance(value, bool):
        return "eq.true" if value else "eq.false"
    return "eq." + quote(str(value), safe="")


def _expected_filter(plan: MutationPlan) -> str:
    parts = ["id=eq." + quote(str(plan.course.course_id), safe="")]
    for key in ("is_active", "last_404_at", "url", "start_date"):
        parts.append(f"{key}={_postgrest_value(plan.expected[key])}")
    return "&".join(parts)


def _read_exact(db: object, course_id: object) -> Mapping[str, object]:
    rows = db.select_service_raise(
        "courses",
        filters="id=eq." + quote(str(course_id), safe=""),
        columns="id,is_active,last_404_at,url,start_date",
        limit=2,
        order="id.asc",
    )
    if not isinstance(rows, list) or len(rows) != 1 or rows[0].get("id") != course_id:
        raise RuntimeError("FG3_EXACT_READ_FAILED")
    return rows[0]


def _state_matches(row: Mapping[str, object], state: Mapping[str, object]) -> bool:
    return all(row.get(key) == value for key, value in state.items())


def _reconcile(db: object, plan: MutationPlan) -> str:
    try:
        row = _read_exact(db, plan.course.course_id)
    except Exception:
        return "OUTCOME_UNKNOWN"
    desired_full = dict(plan.expected)
    desired_full.update(plan.desired)
    if _state_matches(row, desired_full):
        return "ALREADY_APPLIED"
    if _state_matches(row, plan.expected):
        return "OUTCOME_UNKNOWN"
    return "CONFLICT"


def apply_plans(db: object, plans: list[MutationPlan]) -> tuple[str, Counter[str]]:
    outcomes: Counter[str] = Counter()
    for plan in plans:
        try:
            db.patch_exact_one_raise(
                "courses",
                filters=_expected_filter(plan),
                data=dict(plan.desired),
                expected_id=plan.course.course_id,
            )
            outcomes["APPLIED"] += 1
        except Exception:
            outcome = _reconcile(db, plan)
            outcomes[outcome] += 1
            if outcome != "ALREADY_APPLIED":
                return "PARTIAL_APPLY_STOP", outcomes
    return "APPLIED", outcomes


def verify_plans(db: object, plans: list[MutationPlan]) -> bool:
    for plan in plans:
        desired_full = dict(plan.expected)
        desired_full.update(plan.desired)
        try:
            row = _read_exact(db, plan.course.course_id)
        except Exception:
            return False
        if not _state_matches(row, desired_full):
            return False
    return True


def _manifest(
    *,
    result: str,
    courses: int,
    probes: Counter[str],
    reasons: Counter[str],
    attempts: int,
    plans: list[MutationPlan],
    outcomes: Counter[str],
    verified: int,
) -> dict[str, object]:
    document: dict[str, object] = {
        "schema": MANIFEST_SCHEMA,
        "mode": "RUNTIME_FAIL_CLOSED",
        "pipeline": ["probe", "classify", "aggregate", "apply", "verify"],
        "result": result,
        "collection": {"rows": courses},
        "probe": {
            "attempts": attempts,
            "classifications": dict(sorted(probes.items())),
            "reasons": dict(sorted(reasons.items())),
        },
        "aggregate": {
            "planned": len(plans),
            "kinds": dict(sorted(Counter(plan.kind for plan in plans).items())),
        },
        "apply": {"outcomes": dict(sorted(outcomes.items()))},
        "verify": {"desired_states_verified": verified},
        "sanitization": "NO_IDENTIFIERS_OR_LOCATORS",
        "transactionality": "CONDITIONAL_EXACT_ONE_NOT_GLOBAL_DB_TRANSACTION",
    }
    document["manifest_fingerprint"] = _fingerprint(document)
    return document


def run_fg3_atomic(
    db: object,
    *,
    institution_id: str | None = None,
    limit: int | None = None,
    head: Callable[..., object] = safe_head,
    get: Callable[..., object] = safe_get,
    policy: SafeHTTPPolicy = DEFAULT_POLICY,
    sleeper: Callable[[float], None] = time.sleep,
    now: datetime | None = None,
    guard: object | None = None,
) -> FG3RunResult:
    effective_now = (now or _utc_now()).astimezone(timezone.utc)
    probes_count: Counter[str] = Counter()
    reasons: Counter[str] = Counter()
    outcomes: Counter[str] = Counter()

    try:
        courses = collect_courses(db, institution_id=institution_id, limit=limit)
    except Exception:
        manifest = _manifest(
            result="COLLECTION_ERROR",
            courses=0,
            probes=probes_count,
            reasons=Counter({"COLLECTION_ERROR": 1}),
            attempts=0,
            plans=[],
            outcomes=outcomes,
            verified=0,
        )
        return FG3RunResult(1, "COLLECTION_ERROR", manifest)

    ids = [course.course_id for course in courses]
    if len(set(ids)) != len(ids):
        manifest = _manifest(
            result="DUPLICATE_ID",
            courses=len(courses),
            probes=probes_count,
            reasons=Counter({"DUPLICATE_ID": 1}),
            attempts=0,
            plans=[],
            outcomes=outcomes,
            verified=0,
        )
        return FG3RunResult(1, "DUPLICATE_ID", manifest)

    probe_results: dict[object, ProbeResult] = {}
    for course in courses:
        if guard is not None and bool(guard.should_exit):
            reasons["TIME_GUARD"] += 1
            break
        result = probe_course(
            course,
            head=head,
            get=get,
            policy=policy,
            sleeper=sleeper,
        )
        probe_results[course.course_id] = result
        probes_count[result.classification] += 1
        reasons[result.reason] += 1

    inconclusive = probes_count["INCONCLUSIVE"] > 0 or len(probe_results) != len(courses)
    if inconclusive:
        result_name = "TIME_GUARD" if reasons["TIME_GUARD"] else "INCONCLUSIVE"
        manifest = _manifest(
            result=result_name,
            courses=len(courses),
            probes=probes_count,
            reasons=reasons,
            attempts=sum(item.attempts for item in probe_results.values()),
            plans=[],
            outcomes=outcomes,
            verified=0,
        )
        return FG3RunResult(1, result_name, manifest)

    try:
        plans = aggregate_plans(courses, probe_results, now=effective_now)
    except Exception:
        reasons["AGGREGATE_ERROR"] += 1
        manifest = _manifest(
            result="AGGREGATE_ERROR",
            courses=len(courses),
            probes=probes_count,
            reasons=reasons,
            attempts=sum(item.attempts for item in probe_results.values()),
            plans=[],
            outcomes=outcomes,
            verified=0,
        )
        return FG3RunResult(1, "AGGREGATE_ERROR", manifest)
    # This is the final global stop point: expiration and HTTP changes are only plans.
    if guard is not None and bool(guard.should_exit):
        reasons["TIME_GUARD_BEFORE_APPLY"] += 1
        manifest = _manifest(
            result="TIME_GUARD_BEFORE_APPLY",
            courses=len(courses),
            probes=probes_count,
            reasons=reasons,
            attempts=sum(item.attempts for item in probe_results.values()),
            plans=plans,
            outcomes=outcomes,
            verified=0,
        )
        return FG3RunResult(1, "TIME_GUARD_BEFORE_APPLY", manifest)

    if not plans:
        manifest = _manifest(
            result="NOOP",
            courses=len(courses),
            probes=probes_count,
            reasons=reasons,
            attempts=sum(item.attempts for item in probe_results.values()),
            plans=plans,
            outcomes=outcomes,
            verified=0,
        )
        return FG3RunResult(0, "NOOP", manifest)

    apply_result, outcomes = apply_plans(db, plans)
    if apply_result != "APPLIED":
        manifest = _manifest(
            result=apply_result,
            courses=len(courses),
            probes=probes_count,
            reasons=reasons,
            attempts=sum(item.attempts for item in probe_results.values()),
            plans=plans,
            outcomes=outcomes,
            verified=0,
        )
        return FG3RunResult(1, apply_result, manifest)

    if not verify_plans(db, plans):
        manifest = _manifest(
            result="VERIFY_FAILED",
            courses=len(courses),
            probes=probes_count,
            reasons=reasons,
            attempts=sum(item.attempts for item in probe_results.values()),
            plans=plans,
            outcomes=outcomes,
            verified=0,
        )
        return FG3RunResult(1, "VERIFY_FAILED", manifest)

    manifest = _manifest(
        result="APPLIED_VERIFIED",
        courses=len(courses),
        probes=probes_count,
        reasons=reasons,
        attempts=sum(item.attempts for item in probe_results.values()),
        plans=plans,
        outcomes=outcomes,
        verified=len(plans),
    )
    return FG3RunResult(0, "APPLIED_VERIFIED", manifest)


__all__ = [
    "CourseState",
    "FG3RunResult",
    "MANIFEST_SCHEMA",
    "MutationPlan",
    "ProbeResult",
    "aggregate_plans",
    "apply_plans",
    "collect_courses",
    "probe_course",
    "run_fg3_atomic",
    "verify_plans",
]
