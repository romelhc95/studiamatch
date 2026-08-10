"""Fail-before-write FG2 preflight for F10.9 G2/P3.

The collector only accepts a narrow read facade.  Identifiers and source data are
kept in an immutable private cohort; callers may publish only ``manifest``.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from types import MappingProxyType
from typing import Any, Callable, Mapping, Protocol, Sequence
from urllib.parse import quote

from .safe_http import DEFAULT_POLICY, SafeHTTPPolicy, UnsafeURL, safe_get, safe_head
from .url_identity import URL_IDENTITY_VERSION, build_url_identity


MANIFEST_SCHEMA = "f10.9-g2-p3-fg2-preflight.v1"
RUNTIME_MANIFEST_SCHEMA = "f10.9-g2-p3-fg2-runtime.v1"
ALGORITHM_VERSION = "f10.9-g2-p3-v1"
DEFAULT_PAGE_SIZE = 1000
STALE_AFTER = timedelta(hours=24)
BLOCKING_REASONS = frozenset(
    {
        "DUPLICATE_NORMALIZED_URL",
        "STALE_PROCESSING",
        "CONFLICTING_CONTENT_HASH",
        "DOWNSTREAM_REFERENCE_CONFLICT",
        "INVALID_EMPTY_HARDCODED_PROFILE",
        "INVALID_ENABLED_DISCOVERY_PROFILE",
        "INVALID_URL_IDENTITY",
        "UNKNOWN_STAGING_STATUS",
        "INCOMPLETE_CONTENT_EVIDENCE",
        "SOURCE_ACCESS_403",
        "SOURCE_TIMEOUT",
        "SOURCE_FAILURE",
        "REQUESTED_COHORT_NOT_FOUND",
    }
)
SOURCE_OUTCOMES = frozenset(
    {"ACCESSIBLE", "SOURCE_ACCESS_403", "SOURCE_TIMEOUT", "SOURCE_FAILURE"}
)
_TRANSIENT_HTTP = frozenset({408, 425, 429, 500, 502, 503, 504})
_TRANSIENT_SAFE_REASONS = frozenset(
    {
        "SAFE_TOTAL_TIMEOUT",
        "SAFE_DNS_FAILURE",
        "SAFE_DNS_EMPTY",
        "SAFE_TLS_VERIFY",
        "SAFE_TRANSPORT_FAILURE",
    }
)
_SOURCE_ALIASES = {
    "SOURCE_ACCESS_PASS": "ACCESSIBLE",
    "SOURCE_BLOCKED_HTTP_403": "SOURCE_ACCESS_403",
}
_TABLES = {
    "institutions": "id,name,slug,website_url,last_harvest_at",
    "institution_site_profiles": (
        "id,institution_id,discovery_enabled,pipeline_enabled,pipeline_ready,"
        "discovery_mode,seed_urls,catalog_url_patterns,allowed_url_patterns,"
        "circuit_open,circuit_opened_at"
    ),
    "staging_raw": (
        "id,institution_id,url,status,raw_html,content_hash,last_harvested_at,created_at"
    ),
    "cleansed_programs": "id,staging_id,institution_id,url",
}
_STAGING_STATUSES = frozenset(
    {"discovered", "pending", "processing", "processed", "discarded", "skipped", "error"}
)


class ReadOnlyFacade(Protocol):
    """The only DB capability visible to this module."""

    def select(
        self,
        table: str,
        *,
        columns: str,
        limit: int,
        offset: int,
        order: str,
    ) -> Sequence[Mapping[str, Any]]: ...

    def count(self, table: str) -> int: ...


SourceProbe = Callable[[str, Mapping[str, Any]], str]


class PreflightError(RuntimeError):
    """A sanitized fail-closed preflight error."""


def safe_source_probe(
    url: str,
    _profile: Mapping[str, Any],
    *,
    head: Callable[..., object] = safe_head,
    get: Callable[..., object] = safe_get,
    policy: SafeHTTPPolicy = DEFAULT_POLICY,
) -> str:
    """Probe one source through the shared SSRF-safe transport."""
    try:
        response = head(url, policy=policy)
        status = int(getattr(response, "status_code", 0))
        if 200 <= status < 300:
            return "ACCESSIBLE"
        if status in {403, 405, 501}:
            response = get(url, policy=policy)
            status = int(getattr(response, "status_code", 0))
            if 200 <= status < 300:
                return "ACCESSIBLE"
        if status == 403:
            return "SOURCE_ACCESS_403"
        if status in _TRANSIENT_HTTP:
            return "SOURCE_TIMEOUT"
    except UnsafeURL as exc:
        return "SOURCE_TIMEOUT" if exc.reason_code in _TRANSIENT_SAFE_REASONS else "SOURCE_FAILURE"
    except Exception:
        return "SOURCE_FAILURE"
    return "SOURCE_FAILURE"


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
        default=str,
    )


def _fingerprint(value: object, domain: str) -> str:
    payload = f"studiamatch:f10.9:g2:p3:{domain}:v1\0{_canonical_json(value)}"
    return f"sha256:{hashlib.sha256(payload.encode('utf-8')).hexdigest()}"


def _parse_timestamp(value: object) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise PreflightError("COLLECTION_ERROR") from exc
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _json_list(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (TypeError, json.JSONDecodeError) as exc:
            raise PreflightError("COLLECTION_ERROR") from exc
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise PreflightError("COLLECTION_ERROR")
    return tuple(item for item in value if item.strip())


def _identity(value: object) -> tuple[str, bool]:
    identity = build_url_identity(str(value or ""))
    usable = bool(identity.canonical_url) and not identity.canonical_url.startswith("urn:")
    return identity.dedupe_key, usable


def _collect_table(
    db: ReadOnlyFacade,
    table: str,
    columns: str,
    page_size: int,
) -> tuple[tuple[dict[str, Any], ...], int]:
    expected = db.count(table)
    if isinstance(expected, bool) or not isinstance(expected, int) or expected < 0:
        raise PreflightError("COLLECTION_ERROR")
    rows: list[dict[str, Any]] = []
    offset = 0
    pages = 0
    while offset < expected:
        page = db.select(
            table,
            columns=columns,
            limit=page_size,
            offset=offset,
            order="id.asc",
        )
        if not isinstance(page, Sequence) or isinstance(page, (str, bytes)) or not page:
            raise PreflightError("PAGINATION_INCOMPLETE")
        normalized_page: list[dict[str, Any]] = []
        for row in page:
            if not isinstance(row, Mapping) or not row.get("id"):
                raise PreflightError("COLLECTION_ERROR")
            normalized_page.append(dict(row))
        if len(normalized_page) > page_size:
            raise PreflightError("COLLECTION_ERROR")
        rows.extend(normalized_page)
        offset += len(normalized_page)
        pages += 1
    if len(rows) != expected or db.count(table) != expected:
        raise PreflightError("FINGERPRINT_DRIFT")
    ids = [str(row["id"]) for row in rows]
    if len(ids) != len(set(ids)):
        raise PreflightError("COLLECTION_ERROR")
    return tuple(sorted(rows, key=lambda row: str(row["id"]))), pages


@dataclass(frozen=True)
class _FrozenInstitution:
    identifier: str
    name: str
    slug: str
    website_url: str
    last_harvest_at: object

    def as_runtime_dict(self) -> dict[str, object]:
        return {
            "id": self.identifier,
            "name": self.name,
            "slug": self.slug,
            "website_url": self.website_url,
            "last_harvest_at": self.last_harvest_at,
        }


@dataclass(frozen=True)
class _FrozenCohort:
    institutions: tuple[_FrozenInstitution, ...]
    snapshot_fingerprint: str
    cohort_fingerprint: str
    run_fingerprint: str


class PreflightResult:
    """Public sanitized result with a name-mangled private execution handle."""

    __slots__ = ("manifest", "__cohort")

    def __init__(
        self,
        manifest: Mapping[str, object],
        cohort: _FrozenCohort | None,
    ) -> None:
        self.manifest = manifest
        self.__cohort = cohort

    @property
    def is_runnable(self) -> bool:
        return self.__cohort is not None and self.manifest.get("result") == "PASS"

    @property
    def is_noop(self) -> bool:
        return self.manifest.get("result") == "NOOP"

    def _consume(self) -> _FrozenCohort:
        if not self.is_runnable or self.__cohort is None:
            raise PreflightError("PREFLIGHT_NOT_RUNNABLE")
        return self.__cohort


def _candidate_source(institution: Mapping[str, Any], profile: Mapping[str, Any]) -> str | None:
    mode = str(profile.get("discovery_mode") or "")
    seeds = _json_list(profile.get("seed_urls"))
    catalogs = _json_list(profile.get("catalog_url_patterns"))
    if mode in {"hardcoded_urls", "catalog_link_extraction"}:
        candidates = seeds
    elif mode == "paginated_catalog":
        candidates = tuple(item.replace("{page}", "1") for item in catalogs)
    elif mode == "sitemap_bfs":
        website = str(institution.get("website_url") or "").rstrip("/")
        candidates = (f"{website}/sitemap.xml",) if website else ()
    else:
        candidates = ()
    return candidates[0] if candidates else None


def _enabled(profile: Mapping[str, Any]) -> bool:
    pipeline = profile.get("pipeline_enabled")
    if pipeline is None:
        pipeline = profile.get("pipeline_ready")
    return bool(profile.get("discovery_enabled") and pipeline)


def run_preflight(
    db: ReadOnlyFacade,
    source_probe: SourceProbe | None,
    *,
    limit: int = 5,
    excluded_slugs: set[str] | None = None,
    only_slug: str | None = None,
    now: datetime | None = None,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> PreflightResult:
    """Collect, classify, probe and freeze a deterministic private FG2 cohort."""
    if not 1 <= page_size <= 1000 or limit < 0:
        raise PreflightError("COLLECTION_ERROR")
    observed_at = now or datetime.now(timezone.utc)
    if observed_at.tzinfo is None:
        raise PreflightError("COLLECTION_ERROR")

    tables: dict[str, tuple[dict[str, Any], ...]] = {}
    page_counts: dict[str, int] = {}
    for table, columns in _TABLES.items():
        rows, pages = _collect_table(db, table, columns, page_size)
        tables[table] = rows
        page_counts[table] = pages

    snapshot_fingerprint = _fingerprint(
        {"normalization": URL_IDENTITY_VERSION, "tables": tables}, "snapshot"
    )
    reasons: Counter[str] = Counter()
    profiles = {str(row.get("institution_id")): row for row in tables["institution_site_profiles"]}
    if len(profiles) != len(tables["institution_site_profiles"]):
        raise PreflightError("COLLECTION_ERROR")

    staging_by_identity: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    staging_by_id: dict[str, Mapping[str, Any]] = {}
    staging_counts: Counter[str] = Counter()
    for row in tables["staging_raw"]:
        row_id = str(row["id"])
        staging_by_id[row_id] = row
        identity, usable = _identity(row.get("url"))
        if not usable:
            reasons["INVALID_URL_IDENTITY"] += 1
        else:
            staging_by_identity[identity].append(row)
        raw_html = row.get("raw_html")
        content_hash = row.get("content_hash")
        if str(row.get("status") or "") not in _STAGING_STATUSES:
            reasons["UNKNOWN_STAGING_STATUS"] += 1
        if (raw_html is None) != (content_hash is None):
            reasons["INCOMPLETE_CONTENT_EVIDENCE"] += 1
        if raw_html is not None and content_hash is not None:
            calculated = hashlib.sha256(str(raw_html).encode("utf-8")).hexdigest()
            if calculated != str(content_hash):
                reasons["CONFLICTING_CONTENT_HASH"] += 1
        if row.get("status") == "processing":
            started = _parse_timestamp(row.get("last_harvested_at") or row.get("created_at"))
            if started is None or observed_at - started > STALE_AFTER:
                reasons["STALE_PROCESSING"] += 1
        staging_counts[str(row.get("institution_id"))] += 1

    for rows in staging_by_identity.values():
        if len(rows) < 2:
            continue
        reasons["DUPLICATE_NORMALIZED_URL"] += 1
        hashes = {str(row.get("content_hash")) for row in rows if row.get("content_hash")}
        if len(hashes) > 1:
            reasons["CONFLICTING_CONTENT_HASH"] += 1

    downstream_by_staging: Counter[str] = Counter()
    for row in tables["cleansed_programs"]:
        staging_id = str(row.get("staging_id") or "")
        parent = staging_by_id.get(staging_id)
        downstream_by_staging[staging_id] += 1
        if parent is None:
            reasons["DOWNSTREAM_REFERENCE_CONFLICT"] += 1
            continue
        parent_identity, parent_usable = _identity(parent.get("url"))
        child_identity, child_usable = _identity(row.get("url"))
        if (
            not parent_usable
            or not child_usable
            or parent_identity != child_identity
            or str(parent.get("institution_id")) != str(row.get("institution_id"))
        ):
            reasons["DOWNSTREAM_REFERENCE_CONFLICT"] += 1
    duplicate_references = sum(
        count - 1 for count in downstream_by_staging.values() if count > 1
    )
    if duplicate_references:
        reasons["DOWNSTREAM_REFERENCE_CONFLICT"] += duplicate_references

    for profile in profiles.values():
        if not _enabled(profile):
            continue
        mode = str(profile.get("discovery_mode") or "")
        seeds = _json_list(profile.get("seed_urls"))
        catalogs = _json_list(profile.get("catalog_url_patterns"))
        allowed = _json_list(profile.get("allowed_url_patterns"))
        if mode == "hardcoded_urls" and not seeds:
            reasons["INVALID_EMPTY_HARDCODED_PROFILE"] += 1
        elif (
            mode not in {"hardcoded_urls", "catalog_link_extraction", "paginated_catalog", "sitemap_bfs"}
            or (mode == "catalog_link_extraction" and not seeds)
            or (mode == "paginated_catalog" and not catalogs)
            or (mode in {"hardcoded_urls", "sitemap_bfs"} and not allowed)
        ):
            reasons["INVALID_ENABLED_DISCOVERY_PROFILE"] += 1

    excluded = excluded_slugs or set()
    selected: list[tuple[Mapping[str, Any], Mapping[str, Any]]] = []
    ordered_institutions = sorted(
        tables["institutions"],
        key=lambda row: (
            _parse_timestamp(row.get("last_harvest_at")) or datetime.min.replace(tzinfo=timezone.utc),
            str(row["id"]),
        ),
    )
    for institution in ordered_institutions:
        if len(selected) >= limit:
            break
        profile = profiles.get(str(institution["id"]))
        if not profile or not _enabled(profile):
            continue
        slug = str(institution.get("slug") or "")
        if (only_slug and slug != only_slug) or slug in excluded:
            continue
        if profile.get("circuit_open"):
            opened = _parse_timestamp(profile.get("circuit_opened_at"))
            if opened is None or observed_at - opened < STALE_AFTER:
                continue
        last_harvest = _parse_timestamp(institution.get("last_harvest_at"))
        if last_harvest and observed_at - last_harvest < timedelta(days=3):
            if staging_counts[str(institution["id"])] > 50:
                continue
        selected.append((institution, profile))
        if len(selected) >= limit:
            break

    source_counts: Counter[str] = Counter()
    if selected and source_probe is None:
        raise PreflightError("SOURCE_PROBE_REQUIRED")
    for institution, profile in selected:
        source_url = _candidate_source(institution, profile)
        _, usable = _identity(source_url)
        if not source_url or not usable:
            outcome = "SOURCE_FAILURE"
        else:
            try:
                outcome = source_probe(source_url, MappingProxyType(dict(profile)))  # type: ignore[misc]
            except Exception:
                outcome = "SOURCE_FAILURE"
        outcome = _SOURCE_ALIASES.get(outcome, outcome)
        if outcome not in SOURCE_OUTCOMES:
            outcome = "SOURCE_FAILURE"
        source_counts[outcome] += 1
        if outcome != "ACCESSIBLE":
            reasons[outcome] += 1

    frozen_institutions = tuple(
        _FrozenInstitution(
            identifier=str(institution["id"]),
            name=str(institution.get("name") or ""),
            slug=str(institution.get("slug") or ""),
            website_url=str(institution.get("website_url") or ""),
            last_harvest_at=institution.get("last_harvest_at"),
        )
        for institution, _profile in selected
    )
    if only_slug and not frozen_institutions:
        reasons["REQUESTED_COHORT_NOT_FOUND"] += 1
    cohort_fingerprint = _fingerprint(
        [item.as_runtime_dict() for item in frozen_institutions], "cohort"
    )
    blocking = {code: count for code, count in reasons.items() if code in BLOCKING_REASONS and count}
    result = "BLOCKED_PREWRITE" if blocking else ("NOOP" if not frozen_institutions else "PASS")
    run_fingerprint = _fingerprint(
        {
            "snapshot": snapshot_fingerprint,
            "cohort": cohort_fingerprint,
            "sources": dict(sorted(source_counts.items())),
            "selection": {
                "excluded_count": len(excluded),
                "limit": limit,
                "only_one": bool(only_slug),
            },
        },
        "run",
    )
    manifest: dict[str, object] = {
        "schema": MANIFEST_SCHEMA,
        "algorithm_version": ALGORITHM_VERSION,
        "normalization_version": URL_IDENTITY_VERSION,
        "mode": "READ_ONLY_FAIL_BEFORE_WRITE",
        "result": result,
        "reason_counts": dict(sorted(reasons.items())),
        "source_outcomes": dict(sorted(source_counts.items())),
        "collection": {
            table: {"rows": len(tables[table]), "pages": page_counts[table]}
            for table in sorted(tables)
        },
        "cohort": {"size": len(frozen_institutions), "fingerprint": cohort_fingerprint},
        "snapshot_fingerprint": snapshot_fingerprint,
        "run_fingerprint": run_fingerprint,
        "writes": 0,
    }
    private = None
    if result == "PASS":
        private = _FrozenCohort(
            institutions=frozen_institutions,
            snapshot_fingerprint=snapshot_fingerprint,
            cohort_fingerprint=cohort_fingerprint,
            run_fingerprint=run_fingerprint,
        )
    return PreflightResult(MappingProxyType(manifest), private)


class ExistingDbReadFacade:
    """Read-only adapter for the existing shared DB client.

    It intentionally exposes no mutation method. Full existing-client selects are
    cached and then served as deterministic pages to the preflight collector.
    """

    _PIPELINE_TABLES = frozenset(
        {"institution_site_profiles", "staging_raw", "cleansed_programs"}
    )

    def __init__(self, db: object) -> None:
        self.__db = db
        self.__cache: dict[tuple[str, str, str], tuple[Mapping[str, Any], ...]] = {}

    def select(
        self,
        table: str,
        *,
        columns: str,
        limit: int,
        offset: int,
        order: str,
    ) -> Sequence[Mapping[str, Any]]:
        key = (table, columns, order)
        if key not in self.__cache:
            method_name = "select_all_pipeline" if table in self._PIPELINE_TABLES else "select_all_service"
            method = getattr(self.__db, method_name)
            rows = method(table, columns=columns, batch_size=1000, order=order)
            self.__cache[key] = tuple(dict(row) for row in rows)
        return self.__cache[key][offset : offset + limit]

    def count(self, table: str) -> int:
        method_name = "count_pipeline_raise" if table in self._PIPELINE_TABLES else "count_service_raise"
        return int(getattr(self.__db, method_name)(table))


def sanitized_collection_error(code: str = "COLLECTION_ERROR") -> PreflightResult:
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "algorithm_version": ALGORITHM_VERSION,
        "normalization_version": URL_IDENTITY_VERSION,
        "mode": "READ_ONLY_FAIL_BEFORE_WRITE",
        "result": "BLOCKED_PREWRITE",
        "reason_counts": {code: 1},
        "source_outcomes": {},
        "collection": {},
        "cohort": {"size": 0, "fingerprint": _fingerprint([], "cohort")},
        "snapshot_fingerprint": None,
        "run_fingerprint": None,
        "writes": 0,
    }
    return PreflightResult(MappingProxyType(manifest), None)


def build_runtime_manifest(
    preflight_manifest: Mapping[str, object],
    *,
    result: str,
    member_outcomes: Mapping[str, int],
) -> Mapping[str, object]:
    if result not in {"NOOP", "SUCCESS", "PARTIAL_GLOBAL"}:
        raise PreflightError("RUNTIME_RESULT_INVALID")
    allowed_outcomes = {"SUCCESS", "FAILED", "TIME_BUDGET", "CLEANSING_FAILED"}
    if any(
        key not in allowed_outcomes
        or isinstance(value, bool)
        or not isinstance(value, int)
        or value < 0
        for key, value in member_outcomes.items()
    ):
        raise PreflightError("RUNTIME_RESULT_INVALID")
    document: dict[str, object] = {
        "schema": RUNTIME_MANIFEST_SCHEMA,
        "mode": "RUNTIME_FAIL_CLOSED",
        "result": result,
        "preflight_run_fingerprint": preflight_manifest.get("run_fingerprint"),
        "cohort": dict(preflight_manifest.get("cohort", {})),
        "member_outcomes": dict(sorted(member_outcomes.items())),
        "downstream": "ALLOWED" if result in {"NOOP", "SUCCESS"} else "BLOCKED",
        "sanitization": "NO_IDENTIFIERS_OR_LOCATORS",
    }
    document["manifest_fingerprint"] = _fingerprint(document, "runtime")
    return MappingProxyType(document)


__all__ = [
    "ALGORITHM_VERSION",
    "BLOCKING_REASONS",
    "ExistingDbReadFacade",
    "MANIFEST_SCHEMA",
    "RUNTIME_MANIFEST_SCHEMA",
    "PreflightError",
    "PreflightResult",
    "ReadOnlyFacade",
    "SOURCE_OUTCOMES",
    "run_preflight",
    "safe_source_probe",
    "build_runtime_manifest",
    "sanitized_collection_error",
]
