"""Fail-closed primitives for the opt-in, first controlled FG2 run.

This module is deliberately independent of Supabase and external services so
its request and cohort contracts can be exercised with synthetic fixtures.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import ipaddress
import json
import math
import os
import re
import socket
import tempfile
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.parse import urljoin, urlsplit, urlunsplit


FG2_LIMITS = {
    "max_urls_per_institution": 10,
    "max_http_requests_per_institution": 20,
    "min_request_interval_seconds": 5,
    "max_retry_after_seconds": 30,
    "max_concurrent_requests_per_origin": 1,
    "max_attempts_per_url": 3,
}
_UUID = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SOURCE_SHA = re.compile(r"^[0-9a-f]{40}$")
_REDIRECTS = {301, 302, 303, 307, 308}
_TRANSIENT = {408, 425} | set(range(500, 600))


class InvalidControlledRun(ValueError):
    """Invalid or mismatched controlled-run input; callers must fail closed."""


class UnsafePublicTarget(InvalidControlledRun):
    """A controlled request cannot be pinned to a public destination."""


class SourceBlocked(RuntimeError):
    """An origin returned an explicit source block (403 or 429)."""


class OriginDeferred(RuntimeError):
    """An origin must be deferred for this run without another request."""


class RunBudgetExceeded(RuntimeError):
    """The institution's approved URL or HTTP request budget was exhausted."""


def _origin(url: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        raise InvalidControlledRun("controlled request URL must be absolute HTTP(S)")
    if parsed.username is not None or parsed.password is not None:
        raise InvalidControlledRun("controlled request URL cannot contain userinfo")
    scheme = parsed.scheme.lower()
    host = parsed.hostname.lower()
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    try:
        port = parsed.port
    except ValueError as exc:
        raise InvalidControlledRun("controlled request URL has an invalid port") from exc
    default_port = 80 if scheme == "http" else 443
    port_suffix = f":{port}" if port is not None and port != default_port else ""
    return f"{scheme}://{host}{port_suffix}"


def _is_public_ip(value: str) -> bool:
    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        return False
    if getattr(address, "ipv4_mapped", None):
        address = address.ipv4_mapped
    return address.is_global and not (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
    )


def validate_public_url_shape(url: str) -> tuple[str, int, bool]:
    """Validate the controlled transport's URL shape without resolving DNS."""
    parsed = urlsplit(url)
    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"} or not parsed.hostname:
        raise UnsafePublicTarget("controlled target must be absolute HTTP(S)")
    if parsed.username is not None or parsed.password is not None:
        raise UnsafePublicTarget("controlled target cannot contain userinfo")
    host = parsed.hostname.lower()
    normalized_host = host.rstrip(".")
    if (
        not normalized_host
        or "%" in host
        or normalized_host == "localhost"
        or normalized_host.endswith(".localhost")
    ):
        raise UnsafePublicTarget("controlled target hostname is not public")
    try:
        port = parsed.port
    except ValueError as exc:
        raise UnsafePublicTarget("controlled target port is invalid") from exc
    port = port if port is not None else (80 if scheme == "http" else 443)
    if port != (80 if scheme == "http" else 443):
        raise UnsafePublicTarget("controlled target port is unsupported")

    try:
        literal = ipaddress.ip_address(normalized_host)
    except ValueError:
        literal = None
    if literal is not None:
        if not _is_public_ip(str(literal)):
            raise UnsafePublicTarget("controlled target resolves to a non-public address")
        return host, port, True
    if "." not in normalized_host:
        raise UnsafePublicTarget("controlled target hostname is not fully qualified")
    return host, port, False


def public_url_resolve_entry(
    url: str,
    *,
    resolver: Callable[..., list[tuple[Any, ...]]] | None = None,
) -> str | None:
    """Resolve one controlled URL and return a curl CURLOPT_RESOLVE entry.

    All returned addresses must be globally routable. Callers apply the entry
    to a fresh, direct curl session for each HTTP hop, pinning that connection
    against DNS rebinding. A public IP literal is already pinned by the URL.
    """
    host, port, is_ip_literal = validate_public_url_shape(url)
    if is_ip_literal:
        return None

    getaddrinfo = resolver or socket.getaddrinfo
    try:
        records = getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except (OSError, ValueError) as exc:
        raise UnsafePublicTarget("controlled target DNS resolution failed") from exc
    addresses: list[str] = []
    for record in records:
        try:
            address = str(record[4][0]).split("%", 1)[0]
        except (IndexError, TypeError):
            raise UnsafePublicTarget("controlled target DNS response is invalid")
        if not _is_public_ip(address):
            raise UnsafePublicTarget("controlled target resolves to a non-public address")
        if address not in addresses:
            addresses.append(address)
    if not addresses:
        raise UnsafePublicTarget("controlled target DNS response is empty")

    pinned_addresses = ",".join(
        f"[{address}]" if ":" in address else address
        for address in addresses
    )
    return f"{host}:{port}:{pinned_addresses}"


def _origin_digest(origin: str) -> str:
    """Return a non-reversible key for sharing source pacing without storing hosts."""
    return hashlib.sha256(origin.encode("utf-8")).hexdigest()


def _canonical_request_url(url: str) -> str:
    parsed = urlsplit(url)
    origin = _origin(url)
    netloc = origin.split("://", 1)[1]
    return urlunsplit((parsed.scheme.lower(), netloc, parsed.path or "/", parsed.query, ""))


def _header(headers: Any, name: str) -> str | None:
    if not headers:
        return None
    wanted = name.lower()
    try:
        for key, value in headers.items():
            if str(key).lower() == wanted:
                return str(value).strip()
    except AttributeError:
        return None
    return None


def parse_retry_after(value: str | None, now: datetime) -> int | float | None:
    """Parse RFC Retry-After seconds/date; invalid values return None."""
    if not value:
        return None
    value = str(value).strip()
    if re.fullmatch(r"[0-9]+", value):
        # Values beyond the approved wait are represented as infinity. This
        # avoids Python's integer digit cap and ensures the caller defers them.
        normalized = value.lstrip("0") or "0"
        if len(normalized) > 18:
            return math.inf
        return int(normalized)
    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        return max(0.0, (parsed - now).total_seconds())
    except (TypeError, ValueError, OverflowError):
        return None


class FG2RequestBudget:
    """Serializes and accounts for every outbound request made by one institution."""

    def __init__(
        self,
        *,
        max_unique_urls: int = FG2_LIMITS["max_urls_per_institution"],
        max_http_requests: int = FG2_LIMITS["max_http_requests_per_institution"],
        min_interval_seconds: float = FG2_LIMITS["min_request_interval_seconds"],
        max_retry_after_seconds: float = FG2_LIMITS["max_retry_after_seconds"],
        max_attempts_per_url: int = FG2_LIMITS["max_attempts_per_url"],
        max_redirects: int = 5,
        origin_state: Mapping[str, Mapping[str, Any]] | None = None,
        on_origin_state_change: Callable[[str, float | None, str | None], Any] | None = None,
        request_preparer: Callable[[str], Any] | None = None,
        requester: Callable[[Any, str, Any, str, int], Any] | None = None,
        monotonic: Callable[[], float] | None = None,
        sleeper: Callable[[float], Any] | None = None,
        utcnow: Callable[[], datetime] | None = None,
    ) -> None:
        if max_unique_urls < 1 or max_http_requests < 1 or max_attempts_per_url < 1:
            raise ValueError("request limits must be positive")
        if min_interval_seconds < 0 or max_retry_after_seconds < 0 or max_redirects < 0:
            raise ValueError("request delays and redirects cannot be negative")
        if (request_preparer is None) != (requester is None):
            raise ValueError("controlled request preparation and sender must be configured together")
        self.max_unique_urls = max_unique_urls
        self.max_http_requests = max_http_requests
        self.min_interval_seconds = float(min_interval_seconds)
        self.max_retry_after_seconds = float(max_retry_after_seconds)
        self.max_attempts_per_url = max_attempts_per_url
        self.max_redirects = max_redirects
        self._monotonic = monotonic or __import__("time").monotonic
        self._sleep = sleeper or asyncio.sleep
        self._utcnow = utcnow or (lambda: datetime.now(timezone.utc))
        self._semaphores: dict[str, asyncio.Semaphore] = {}
        self._state_lock = asyncio.Lock()
        self._last_started: dict[str, float] = {}
        self._unique_urls: set[str] = set()
        self._blocked_origins: set[str] = set()
        self._deferred_origins: set[str] = set()
        self._on_origin_state_change = on_origin_state_change
        self._request_preparer = request_preparer
        self._requester = requester
        for digest, state in (origin_state or {}).items():
            if not _SHA256.fullmatch(str(digest)) or not isinstance(state, Mapping):
                raise ValueError("invalid persisted origin state")
            last_started = state.get("last_started_monotonic")
            if last_started is not None:
                if isinstance(last_started, bool) or not isinstance(last_started, (int, float)):
                    raise ValueError("invalid persisted origin start time")
                if not math.isfinite(float(last_started)) or float(last_started) < 0:
                    raise ValueError("invalid persisted origin start time")
                self._last_started[str(digest)] = float(last_started)
            stop_reason = state.get("stop_reason")
            if stop_reason == "blocked":
                self._blocked_origins.add(str(digest))
            elif stop_reason == "deferred":
                self._deferred_origins.add(str(digest))
            elif stop_reason is not None:
                raise ValueError("invalid persisted origin stop reason")
        self._run_exhausted = False
        self.http_requests = 0

    @property
    def unique_urls(self) -> tuple[str, ...]:
        return tuple(sorted(self._unique_urls))

    def snapshot(self) -> dict[str, int]:
        return {"http_requests": self.http_requests, "unique_urls": len(self._unique_urls)}

    def _semaphore(self, origin: str) -> asyncio.Semaphore:
        if origin not in self._semaphores:
            self._semaphores[origin] = asyncio.Semaphore(1)
        return self._semaphores[origin]

    def _publish_origin_state(self, digest: str) -> None:
        if not self._on_origin_state_change:
            return
        stop_reason = (
            "blocked" if digest in self._blocked_origins
            else "deferred" if digest in self._deferred_origins
            else None
        )
        self._on_origin_state_change(digest, self._last_started.get(digest), stop_reason)

    async def _defer(self, origin: str) -> None:
        digest = _origin_digest(origin)
        async with self._state_lock:
            if digest not in self._blocked_origins:
                self._deferred_origins.add(digest)
            self._publish_origin_state(digest)

    async def _reserve_unique_url(self, canonical: str, origin: str) -> None:
        digest = _origin_digest(origin)
        async with self._state_lock:
            if digest in self._blocked_origins:
                raise SourceBlocked("origin stopped after HTTP 403/429")
            if digest in self._deferred_origins:
                raise OriginDeferred("origin deferred for this run")
            if self._run_exhausted:
                raise RunBudgetExceeded("institution HTTP budget exhausted")
            if canonical not in self._unique_urls:
                if len(self._unique_urls) >= self.max_unique_urls:
                    self._run_exhausted = True
                    raise RunBudgetExceeded("institution unique URL budget exhausted")
                self._unique_urls.add(canonical)

    async def _one_request(self, session: Any, url: str, *, impersonate: str, timeout: int):
        origin = _origin(url)
        digest = _origin_digest(origin)
        async with self._semaphore(origin):
            if digest in self._blocked_origins:
                raise SourceBlocked("origin stopped after HTTP 403/429")
            if digest in self._deferred_origins:
                raise OriginDeferred("origin deferred for this run")
            if self._run_exhausted:
                raise RunBudgetExceeded("institution HTTP budget exhausted")

            delay = max(
                0.0,
                self._last_started.get(digest, float("-inf"))
                + self.min_interval_seconds
                - self._monotonic(),
            )
            if delay:
                await self._sleep(delay)

            try:
                prepared_request = (
                    self._request_preparer(url)
                    if self._request_preparer is not None
                    else None
                )
            except UnsafePublicTarget as exc:
                await self._defer(origin)
                raise OriginDeferred("controlled target failed the public-address guard") from exc

            async with self._state_lock:
                if digest in self._blocked_origins:
                    raise SourceBlocked("origin stopped after HTTP 403/429")
                if digest in self._deferred_origins:
                    raise OriginDeferred("origin deferred for this run")
                if self._run_exhausted or self.http_requests >= self.max_http_requests:
                    self._run_exhausted = True
                    raise RunBudgetExceeded("institution HTTP budget exhausted")
                self.http_requests += 1
                self._last_started[digest] = self._monotonic()
                # Persist before the outbound call so the next institution process
                # inherits both the pacing mark and the fail-closed stop state.
                self._publish_origin_state(digest)

            try:
                if self._requester is not None:
                    response = await self._requester(
                        session,
                        url,
                        prepared_request,
                        impersonate,
                        timeout,
                    )
                else:
                    if prepared_request:
                        raise UnsafePublicTarget("controlled transport cannot apply DNS pinning")
                    response = await session.get(
                        url,
                        impersonate=impersonate,
                        timeout=timeout,
                        allow_redirects=False,
                    )
            except UnsafePublicTarget as exc:
                await self._defer(origin)
                raise OriginDeferred("controlled target could not be pinned") from exc
            except Exception as exc:
                return None, exc

            if getattr(response, "status_code", None) in {403, 429}:
                async with self._state_lock:
                    self._blocked_origins.add(digest)
                    self._publish_origin_state(digest)
            return response, None

    async def get(
        self,
        session: Any,
        url: str,
        *,
        allowed_origin: str | None = None,
        impersonate: str = "chrome110",
        timeout: int = 25,
    ) -> Any:
        """GET with explicit redirect accounting, pacing, retry and stop rules."""
        current = _canonical_request_url(url)
        origin = _origin(current)
        permitted_origin = _origin(allowed_origin) if allowed_origin else origin
        if origin != permitted_origin:
            raise InvalidControlledRun("initial request is outside the preflighted origin")
        await self._reserve_unique_url(current, permitted_origin)
        redirects = 0

        while True:
            response = None
            for attempt in range(1, self.max_attempts_per_url + 1):
                response, error = await self._one_request(
                    session, current, impersonate=impersonate, timeout=timeout
                )
                if error is not None:
                    if attempt == self.max_attempts_per_url:
                        await self._defer(permitted_origin)
                        raise OriginDeferred("transient request failed; origin deferred") from error
                    await self._sleep(min(5.0 * (2 ** (attempt - 1)), self.max_retry_after_seconds))
                    continue

                status = getattr(response, "status_code", None)
                if status in {403, 429}:
                    raise SourceBlocked(f"origin stopped after HTTP {status}")
                if status in _TRANSIENT:
                    if attempt == self.max_attempts_per_url:
                        await self._defer(permitted_origin)
                        raise OriginDeferred("transient HTTP status exhausted per-URL attempts")
                    retry_after = parse_retry_after(_header(getattr(response, "headers", {}), "retry-after"), self._utcnow())
                    if retry_after is not None and retry_after > self.max_retry_after_seconds:
                        await self._defer(permitted_origin)
                        raise OriginDeferred("Retry-After exceeds the approved maximum")
                    delay = retry_after if retry_after is not None else min(
                        5.0 * (2 ** (attempt - 1)), self.max_retry_after_seconds
                    )
                    await self._sleep(delay)
                    continue
                break

            status = getattr(response, "status_code", None)
            location = _header(getattr(response, "headers", {}), "location")
            if status not in _REDIRECTS or not location:
                return response
            if redirects >= self.max_redirects:
                await self._defer(permitted_origin)
                raise OriginDeferred("redirect limit exceeded")
            target = _canonical_request_url(urljoin(current, location))
            if _origin(target) != permitted_origin:
                await self._defer(permitted_origin)
                raise OriginDeferred("cross-origin redirect rejected")
            current = target
            redirects += 1


def _valid_uuid(value: Any) -> bool:
    return isinstance(value, str) and bool(_UUID.fullmatch(value))


def _valid_sha256(value: Any) -> bool:
    return isinstance(value, str) and bool(_SHA256.fullmatch(value))


@dataclass(frozen=True)
class FG2CohortManifest:
    """Immutable input contract shared by controlled FG2 downstream jobs."""

    payload: dict[str, Any]

    @classmethod
    def load(
        cls,
        path: str | Path,
        *,
        expected_sha256: str | None = None,
        expected_run_id: str | None = None,
        expected_run_attempt: int | None = None,
        expected_source_sha: str | None = None,
        allow_empty: bool = False,
    ) -> "FG2CohortManifest":
        source = Path(path)
        try:
            raw = source.read_bytes()
            payload = json.loads(raw)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise InvalidControlledRun("cohort manifest is missing or invalid JSON") from exc
        if expected_sha256 is not None and hashlib.sha256(raw).hexdigest() != expected_sha256.lower():
            raise InvalidControlledRun("cohort manifest digest mismatch")
        return cls.from_payload(
            payload,
            expected_run_id=expected_run_id,
            expected_run_attempt=expected_run_attempt,
            expected_source_sha=expected_source_sha,
            allow_empty=allow_empty,
        )

    @classmethod
    def from_payload(
        cls,
        payload: Any,
        *,
        expected_run_id: str | None = None,
        expected_run_attempt: int | None = None,
        expected_source_sha: str | None = None,
        allow_empty: bool = False,
    ) -> "FG2CohortManifest":
        if not isinstance(payload, dict) or payload.get("schema_version") != 1:
            raise InvalidControlledRun("unsupported cohort manifest schema")
        if not isinstance(payload.get("run_id"), str) or not payload["run_id"].isdigit():
            raise InvalidControlledRun("invalid workflow run id")
        if not isinstance(payload.get("run_attempt"), int) or payload["run_attempt"] < 1:
            raise InvalidControlledRun("invalid workflow run attempt")
        if not isinstance(payload.get("source_sha"), str) or not _SOURCE_SHA.fullmatch(payload["source_sha"]):
            raise InvalidControlledRun("invalid source SHA")
        if expected_run_id is not None and payload["run_id"] != str(expected_run_id):
            raise InvalidControlledRun("cohort manifest run id mismatch")
        if expected_run_attempt is not None and payload["run_attempt"] != int(expected_run_attempt):
            raise InvalidControlledRun("cohort manifest run attempt mismatch")
        if expected_source_sha is not None and payload["source_sha"] != expected_source_sha.lower():
            raise InvalidControlledRun("cohort manifest source SHA mismatch")
        if payload.get("limits") != FG2_LIMITS:
            raise InvalidControlledRun("cohort manifest limits differ from the approved candidate")

        institutions = payload.get("institutions")
        if not isinstance(institutions, list) or not institutions or len(institutions) > 10:
            raise InvalidControlledRun("cohort institution set must contain 1..10 entries")
        institution_ids: set[str] = set()
        institution_results: dict[str, str] = {}
        for item in institutions:
            if not isinstance(item, dict) or not _valid_uuid(item.get("institution_id")):
                raise InvalidControlledRun("invalid institution id in cohort manifest")
            institution_id = item["institution_id"].lower()
            if institution_id in institution_ids:
                raise InvalidControlledRun("duplicate institution in cohort manifest")
            institution_ids.add(institution_id)
            institution_results[institution_id] = item.get("result")
            if not _valid_sha256(item.get("profile_sha256")) or not _valid_sha256(item.get("seed_sha256")):
                raise InvalidControlledRun("invalid profile or seed digest")
            if not isinstance(item.get("http_requests"), int) or not 0 <= item["http_requests"] <= FG2_LIMITS["max_http_requests_per_institution"]:
                raise InvalidControlledRun("institution HTTP count is outside its budget")
            if not isinstance(item.get("unique_urls"), int) or not 0 <= item["unique_urls"] <= FG2_LIMITS["max_urls_per_institution"]:
                raise InvalidControlledRun("institution URL count is outside its budget")
            if item.get("result") not in {"preflight_passed", "complete", "no_op", "blocked", "deferred", "failed"}:
                raise InvalidControlledRun("invalid institution result")

        origin_state = payload.get("origin_state", {})
        if not isinstance(origin_state, dict):
            raise InvalidControlledRun("invalid shared source-origin state")
        for digest, state in origin_state.items():
            if not _valid_sha256(digest) or not isinstance(state, dict):
                raise InvalidControlledRun("invalid shared source-origin state")
            last_started = state.get("last_started_monotonic")
            if last_started is not None:
                if isinstance(last_started, bool) or not isinstance(last_started, (int, float)):
                    raise InvalidControlledRun("invalid shared source-origin start time")
                if not math.isfinite(float(last_started)) or float(last_started) < 0:
                    raise InvalidControlledRun("invalid shared source-origin start time")
            if state.get("stop_reason") not in {None, "blocked", "deferred"}:
                raise InvalidControlledRun("invalid shared source-origin stop reason")
            if state.get("stop_reason") is not None and last_started is None:
                raise InvalidControlledRun("source origin cannot stop before an HTTP request")

        entries = payload.get("entries")
        if not isinstance(entries, list) or (not entries and not allow_empty):
            raise InvalidControlledRun("controlled cohort is empty")
        discovery_rows = payload.get("discovery_rows", [])
        if not isinstance(discovery_rows, list):
            raise InvalidControlledRun("invalid controlled discovery-row list")
        discovery_ids: set[str] = set()
        for row in discovery_rows:
            if not isinstance(row, dict):
                raise InvalidControlledRun("invalid controlled discovery row")
            institution_id = row.get("institution_id")
            staging_id = row.get("staging_id")
            if not _valid_uuid(institution_id) or institution_id.lower() not in institution_ids:
                raise InvalidControlledRun("discovery row institution is outside the frozen cohort")
            if not _valid_uuid(staging_id) or staging_id.lower() in discovery_ids:
                raise InvalidControlledRun("invalid or duplicate controlled discovery-row id")
            if not _valid_sha256(row.get("url_sha256")):
                raise InvalidControlledRun("controlled discovery-row URL digest is invalid")
            if row.get("initial_status") != "discovered":
                raise InvalidControlledRun("controlled discovery row must retain discovered status")
            if row.get("kind") not in {"new_discovery", "refresh_existing"}:
                raise InvalidControlledRun("invalid controlled discovery-row classification")
            course_id = row.get("course_id")
            if course_id is not None and not _valid_uuid(course_id):
                raise InvalidControlledRun("invalid controlled discovery course id")
            if (row["kind"] == "refresh_existing") != (course_id is not None):
                raise InvalidControlledRun("controlled discovery classification does not match its course reference")
            discovery_ids.add(staging_id.lower())

        entry_ids: set[str] = set()
        urls_by_institution: dict[str, set[str]] = {}
        counts_by_institution: dict[str, int] = {}
        for entry in entries:
            if not isinstance(entry, dict):
                raise InvalidControlledRun("invalid cohort entry")
            institution_id = entry.get("institution_id")
            staging_id = entry.get("staging_id")
            if not _valid_uuid(institution_id) or institution_id.lower() not in institution_ids:
                raise InvalidControlledRun("entry institution is outside the frozen cohort")
            if not _valid_uuid(staging_id) or staging_id.lower() in entry_ids:
                raise InvalidControlledRun("invalid or duplicate staging id")
            if not _valid_sha256(entry.get("url_sha256")) or not _valid_sha256(entry.get("content_sha256")):
                raise InvalidControlledRun("invalid URL or content digest")
            if entry.get("kind") not in {"new_discovery", "refresh_existing"}:
                raise InvalidControlledRun("invalid URL classification")
            course_id = entry.get("course_id")
            if course_id is not None and not _valid_uuid(course_id):
                raise InvalidControlledRun("invalid existing course id")
            if (entry["kind"] == "refresh_existing") != (course_id is not None):
                raise InvalidControlledRun("cohort classification does not match its course reference")
            entry_ids.add(staging_id.lower())
            key = institution_id.lower()
            if not allow_empty and institution_results.get(key) not in {"complete", "blocked", "deferred"}:
                raise InvalidControlledRun("institution result is not eligible for downstream work")
            urls_by_institution.setdefault(key, set()).add(entry["url_sha256"])
            counts_by_institution[key] = counts_by_institution.get(key, 0) + 1
        for institution_id, count in counts_by_institution.items():
            if count > FG2_LIMITS["max_urls_per_institution"]:
                raise InvalidControlledRun("institution cohort exceeds the approved URL cap")
            if len(urls_by_institution[institution_id]) != count:
                raise InvalidControlledRun("duplicate URL hash in institution cohort")
        blockers = payload.get("blocked_staging_rows", [])
        if not isinstance(blockers, list):
            raise InvalidControlledRun("invalid historical staging blocker list")
        blocker_ids: set[str] = set()
        for blocker in blockers:
            if not isinstance(blocker, dict):
                raise InvalidControlledRun("invalid historical staging blocker")
            institution_id = blocker.get("institution_id")
            staging_id = blocker.get("staging_id")
            if not _valid_uuid(institution_id) or institution_id.lower() not in institution_ids:
                raise InvalidControlledRun("historical blocker institution is outside the frozen cohort")
            if not _valid_uuid(staging_id) or staging_id.lower() in blocker_ids or staging_id.lower() in entry_ids:
                raise InvalidControlledRun("invalid or duplicate historical staging blocker id")
            if not _valid_sha256(blocker.get("url_sha256")):
                raise InvalidControlledRun("historical blocker URL digest is invalid")
            content_sha = blocker.get("content_sha256")
            if content_sha is not None and not _valid_sha256(content_sha):
                raise InvalidControlledRun("historical blocker content digest is invalid")
            if blocker.get("status") not in {"pending", "processing", "processed", "discarded", "skipped", "error"}:
                raise InvalidControlledRun("historical blocker must retain a protected state")
            if blocker.get("reason") != "historical_staging_state_protected":
                raise InvalidControlledRun("historical blocker reason is not recognized")
            blocker_ids.add(staging_id.lower())
        return cls(payload)

    @property
    def staging_ids(self) -> tuple[str, ...]:
        return tuple(entry["staging_id"] for entry in self.payload["entries"])

    @property
    def institution_ids(self) -> tuple[str, ...]:
        return tuple(item["institution_id"] for item in self.payload["institutions"])

    def assert_stage_records(
        self,
        records: list[dict[str, Any]],
        *,
        allowed_ids: tuple[str, ...] | list[str],
        stage: str,
        require_exact: bool = False,
    ) -> None:
        allowed = {str(value).lower() for value in allowed_ids}
        seen: set[str] = set()
        for row in records:
            row_id = row.get("id") if isinstance(row, dict) else None
            if not _valid_uuid(row_id):
                raise InvalidControlledRun(f"{stage} returned an invalid row id")
            normalized = row_id.lower()
            if normalized not in allowed:
                raise InvalidControlledRun(f"{stage} returned a row outside the frozen cohort")
            if normalized in seen:
                raise InvalidControlledRun(f"{stage} returned a duplicate row id")
            seen.add(normalized)
        if require_exact and seen != allowed:
            raise InvalidControlledRun(f"{stage} did not return the exact frozen id set")

    def assert_related_stage_records(
        self,
        records: list[dict[str, Any]],
        *,
        foreign_key: str,
        allowed_ids: tuple[str, ...] | list[str],
        stage: str,
    ) -> None:
        """Reject downstream rows whose parent ID is outside the raw cohort."""
        allowed = {str(value).lower() for value in allowed_ids}
        seen: set[str] = set()
        for row in records:
            if not isinstance(row, dict) or not _valid_uuid(row.get("id")):
                raise InvalidControlledRun(f"{stage} returned a row with an invalid id")
            row_id = row["id"].lower()
            if row_id in seen:
                raise InvalidControlledRun(f"{stage} returned a duplicate row id")
            seen.add(row_id)
            parent_id = row.get(foreign_key)
            if not _valid_uuid(parent_id) or parent_id.lower() not in allowed:
                raise InvalidControlledRun(f"{stage} returned a row outside the frozen cohort")


def manifest_file_sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_manifest_b64(
    encoded: str,
    *,
    expected_sha256: str,
    expected_run_id: str,
    expected_run_attempt: int,
    expected_source_sha: str,
    allow_empty: bool = False,
) -> FG2CohortManifest:
    """Load a compact Actions job output and verify its exact byte digest."""
    try:
        raw = base64.b64decode(encoded, validate=True)
        payload = json.loads(raw)
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InvalidControlledRun("cohort manifest job output is invalid") from exc
    if not _valid_sha256(expected_sha256) or hashlib.sha256(raw).hexdigest() != expected_sha256.lower():
        raise InvalidControlledRun("cohort manifest job output digest mismatch")
    return FG2CohortManifest.from_payload(
        payload,
        expected_run_id=expected_run_id,
        expected_run_attempt=expected_run_attempt,
        expected_source_sha=expected_source_sha,
        allow_empty=allow_empty,
    )


def uuid_in_filter(column: str, values: tuple[str, ...] | list[str]) -> str:
    """Build a PostgREST `in` filter from validated UUID values only."""
    if not isinstance(column, str) or not re.fullmatch(r"[a-z_][a-z0-9_]*", column):
        raise InvalidControlledRun("invalid PostgREST filter column")
    normalized = [str(value).lower() for value in values]
    if not normalized or any(not _valid_uuid(value) for value in normalized):
        raise InvalidControlledRun("UUID filter must contain only valid IDs")
    if len(set(normalized)) != len(normalized):
        raise InvalidControlledRun("UUID filter cannot contain duplicate IDs")
    return f"{column}=in.({','.join(normalized)})"


def require_manifest_sha256(manifest_path: str | None, expected_sha256: str | None) -> str | None:
    """Require an exact digest whenever a worker enters controlled-manifest mode."""
    has_manifest = bool(manifest_path)
    has_digest = bool(expected_sha256)
    if has_manifest and (not has_digest or not _valid_sha256(expected_sha256)):
        raise InvalidControlledRun("controlled cohort requires an expected SHA-256")
    if has_digest and not has_manifest:
        raise InvalidControlledRun("cohort SHA-256 supplied without a manifest")
    return expected_sha256.lower() if expected_sha256 else None


def write_manifest_atomic(path: str | Path, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    fd, temp_path = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, target)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def stable_json_sha256(value: Any) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def url_sha256(url: str) -> str:
    return hashlib.sha256(_canonical_request_url(url).encode("utf-8")).hexdigest()


def _json_list(value: Any, field: str) -> list[Any]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as exc:
            raise InvalidControlledRun(f"profile {field} is not valid JSON") from exc
    if not isinstance(value, list):
        raise InvalidControlledRun(f"profile {field} must be a list")
    return value


def validate_controlled_profile(
    institution: Mapping[str, Any],
    profile: Mapping[str, Any],
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Validate gates and configured seeds without making a network request."""
    if not isinstance(institution, Mapping) or not isinstance(profile, Mapping):
        raise InvalidControlledRun("institution/profile preflight payload is malformed")
    if not _valid_uuid(institution.get("id")):
        raise InvalidControlledRun("institution id is invalid")
    normalized_profile = dict(profile)
    for field in ("catalog_url_patterns", "exclusion_patterns", "allowed_url_patterns", "seed_urls"):
        if field in normalized_profile:
            normalized_profile[field] = (
                [] if normalized_profile[field] is None else _json_list(normalized_profile[field], field)
            )
    for gate in ("discovery_enabled", "pipeline_enabled", "production_enabled"):
        if profile.get(gate) is not True:
            raise InvalidControlledRun(f"institution {gate} is not enabled")

    effective_profile = dict(normalized_profile)
    circuit_expired = False
    if profile.get("circuit_open") is True:
        opened_value = profile.get("circuit_opened_at")
        if not isinstance(opened_value, str) or not opened_value.strip():
            raise InvalidControlledRun("open source circuit has no valid timestamp")
        try:
            opened = datetime.fromisoformat(opened_value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise InvalidControlledRun("open source circuit timestamp is invalid") from exc
        if opened.tzinfo is None:
            opened = opened.replace(tzinfo=timezone.utc)
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None:
            current = current.replace(tzinfo=timezone.utc)
        if current - opened < timedelta(hours=24):
            raise InvalidControlledRun("source circuit is still within its cooldown")
        circuit_expired = True
        effective_profile["circuit_open"] = False
        effective_profile["circuit_opened_at"] = None

    if profile.get("site_type", "traditional_ssr") != "traditional_ssr":
        raise InvalidControlledRun("controlled run supports only traditional SSR profiles")
    if profile.get("requires_stealth") is True or profile.get("requires_cloudflare_bypass") is True:
        raise InvalidControlledRun("controlled run defers stealth/anti-bot profiles before origin access")

    website_url = institution.get("website_url")
    validate_public_url_shape(str(website_url or ""))
    website_origin = _origin(str(website_url or ""))
    mode = profile.get("discovery_mode")
    if mode == "hardcoded_urls":
        seeds = _json_list(profile.get("seed_urls", []), "seed_urls")
    elif mode == "sitemap_bfs":
        configured = _json_list(profile.get("seed_urls", []), "seed_urls")
        seeds = configured or [urljoin(str(website_url), "/sitemap.xml")]
    elif mode == "paginated_catalog":
        patterns = _json_list(profile.get("catalog_url_patterns", []), "catalog_url_patterns")
        seeds = [str(item).replace("{page}", "1") for item in patterns]
    else:
        raise InvalidControlledRun("discovery mode is not supported in the bounded run")
    if not seeds:
        raise InvalidControlledRun("eligible source has no configured seed URL")

    normalized_seeds: list[str] = []
    seen: set[str] = set()
    for seed in seeds:
        if not isinstance(seed, str) or not seed.strip():
            raise InvalidControlledRun("source seed is empty or malformed")
        validate_public_url_shape(seed.strip())
        normalized = _canonical_request_url(seed.strip())
        if _origin(normalized) != website_origin:
            raise InvalidControlledRun("source seed is outside the institution origin")
        if normalized not in seen:
            seen.add(normalized)
            normalized_seeds.append(normalized)
    selected_seeds = normalized_seeds[: FG2_LIMITS["max_urls_per_institution"]]
    if not selected_seeds:
        raise InvalidControlledRun("source seed set is empty after validation")

    return {
        "effective_profile": effective_profile,
        "seed_urls": selected_seeds,
        "profile_sha256": stable_json_sha256(normalized_profile),
        "seed_sha256": stable_json_sha256(selected_seeds),
        "circuit_expired": circuit_expired,
    }


def initialize_manifest(
    path: str | Path,
    *,
    run_id: str,
    run_attempt: int,
    source_sha: str,
    institutions: list[dict[str, Any]],
) -> str:
    payload = {
        "schema_version": 1,
        "run_id": str(run_id),
        "run_attempt": int(run_attempt),
        "source_sha": source_sha.lower(),
        "limits": dict(FG2_LIMITS),
        "institutions": institutions,
        "origin_state": {},
        "entries": [],
        "discovery_rows": [],
        "blocked_staging_rows": [],
    }
    FG2CohortManifest.from_payload(payload, allow_empty=True)
    write_manifest_atomic(path, payload)
    return manifest_file_sha256(path)


def append_manifest_entry(path: str | Path, entry: dict[str, Any]) -> str:
    target = Path(path)
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InvalidControlledRun("cannot append to missing/invalid cohort manifest") from exc
    payload.setdefault("entries", []).append(entry)
    FG2CohortManifest.from_payload(payload, allow_empty=True)
    write_manifest_atomic(target, payload)
    return manifest_file_sha256(target)


def append_manifest_discovery_row(path: str | Path, row: dict[str, Any]) -> str:
    """Record a persisted discovered row even if extraction later stops or defers."""
    target = Path(path)
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InvalidControlledRun("cannot read controlled cohort manifest") from exc
    discoveries = payload.setdefault("discovery_rows", [])
    if not isinstance(discoveries, list):
        raise InvalidControlledRun("invalid controlled discovery-row list")
    existing = next(
        (item for item in discoveries if isinstance(item, dict) and item.get("staging_id") == row.get("staging_id")),
        None,
    )
    if existing is not None:
        if existing != row:
            raise InvalidControlledRun("controlled discovery row changed after being frozen")
        return manifest_file_sha256(target)
    discoveries.append(row)
    FG2CohortManifest.from_payload(payload, allow_empty=True)
    write_manifest_atomic(target, payload)
    return manifest_file_sha256(target)


def append_manifest_blocker(path: str | Path, blocker: dict[str, Any]) -> str:
    target = Path(path)
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InvalidControlledRun("cannot append to missing/invalid cohort manifest") from exc
    payload.setdefault("blocked_staging_rows", []).append(blocker)
    FG2CohortManifest.from_payload(payload, allow_empty=True)
    write_manifest_atomic(target, payload)
    return manifest_file_sha256(target)


def update_manifest_institution(
    path: str | Path,
    *,
    institution_id: str,
    http_requests: int,
    unique_urls: int,
    result: str,
) -> str:
    target = Path(path)
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InvalidControlledRun("cannot update missing/invalid cohort manifest") from exc
    matches = [
        item for item in payload.get("institutions", [])
        if item.get("institution_id", "").lower() == institution_id.lower()
    ]
    if len(matches) != 1:
        raise InvalidControlledRun("institution is not uniquely present in frozen manifest")
    matches[0].update({
        "http_requests": int(http_requests),
        "unique_urls": int(unique_urls),
        "result": result,
    })
    FG2CohortManifest.from_payload(payload, allow_empty=True)
    write_manifest_atomic(target, payload)
    return manifest_file_sha256(target)


def update_manifest_origin_state(
    path: str | Path,
    *,
    origin_sha256: str,
    last_started_monotonic: float | None,
    stop_reason: str | None = None,
) -> str:
    """Persist per-run pacing and source-stop state without retaining hostnames."""
    if not _valid_sha256(origin_sha256):
        raise InvalidControlledRun("invalid source-origin digest")
    if last_started_monotonic is not None:
        if isinstance(last_started_monotonic, bool) or not isinstance(last_started_monotonic, (int, float)):
            raise InvalidControlledRun("invalid source-origin start time")
        if not math.isfinite(float(last_started_monotonic)) or float(last_started_monotonic) < 0:
            raise InvalidControlledRun("invalid source-origin start time")
    if stop_reason not in {None, "blocked", "deferred"}:
        raise InvalidControlledRun("invalid source-origin stop reason")

    target = Path(path)
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InvalidControlledRun("cannot update missing/invalid cohort manifest") from exc
    origin_state = payload.setdefault("origin_state", {})
    if not isinstance(origin_state, dict):
        raise InvalidControlledRun("invalid shared source-origin state")
    existing = origin_state.get(origin_sha256, {})
    if not isinstance(existing, dict):
        raise InvalidControlledRun("invalid shared source-origin state")
    prior_start = existing.get("last_started_monotonic")
    if prior_start is not None and (
        isinstance(prior_start, bool)
        or not isinstance(prior_start, (int, float))
        or not math.isfinite(float(prior_start))
        or float(prior_start) < 0
    ):
        raise InvalidControlledRun("invalid persisted source-origin start time")
    latest_start = last_started_monotonic
    if prior_start is not None:
        latest_start = max(float(prior_start), float(latest_start or prior_start))
    prior_stop = existing.get("stop_reason")
    if prior_stop == "blocked":
        stop_reason = "blocked"
    elif stop_reason is None:
        stop_reason = prior_stop
    origin_state[origin_sha256] = {
        "last_started_monotonic": latest_start,
        "stop_reason": stop_reason,
    }
    FG2CohortManifest.from_payload(payload, allow_empty=True)
    write_manifest_atomic(target, payload)
    return manifest_file_sha256(target)
