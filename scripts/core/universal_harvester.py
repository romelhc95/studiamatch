import asyncio
import os
import json
import logging
import re
import sys
import hashlib
import random
from datetime import datetime, timezone
from urllib.parse import quote, urljoin, urlparse, urlsplit
import xml.etree.ElementTree as ET

_FG2_DIAGNOSTIC_PREFIX = "[FG2_DIAGNOSTIC] "
_FG2_DIAGNOSTIC_PHASES = frozenset({
    "dependency_import",
    "module_initialization",
    "mode_validation",
    "input_decode",
    "harvester_initialization",
    "profile_gate",
    "browser_initialization",
    "source_discovery",
    "course_detail",
    "staging_write",
    "telemetry",
    "shutdown",
})
_FG2_DIAGNOSTIC_CATEGORIES = frozenset({
    "dependency_import_failed",
    "module_initialization_failed",
    "controlled_run_rejected",
    "invalid_input",
    "database_api_error",
    "database_write_outcome_unknown",
    "harvester_rejected",
    "source_request_error",
    "timeout",
    "os_error",
    "profile_missing",
    "circuit_open",
    "discovery_unavailable",
    "unexpected_exception",
})
_FG2_DIAGNOSTIC_TABLES = frozenset({
    "institutions",
    "institution_site_profiles",
    "staging_raw",
    "courses",
    "cleansed_programs",
    "enriched_programs",
})


def _fg2_diagnostics_enabled():
    return (
        bool(os.getenv("F10_PRODUCTION_CANARY_RUN_ID", "").strip())
        or os.getenv("FG2_CONTROLLED_FIRST_RUN", "").strip().lower() == "true"
        or os.getenv("FG2_COHORT_SCOPED", "").strip().lower() == "true"
    )


def _emit_fg2_diagnostic(phase, category, *, table=None, http_status=None):
    """Write a bounded, allowlisted event for the sensitive parent process."""
    if (
        not _fg2_diagnostics_enabled()
        or phase not in _FG2_DIAGNOSTIC_PHASES
        or category not in _FG2_DIAGNOSTIC_CATEGORIES
    ):
        return
    payload = {"version": 1, "phase": phase, "category": category}
    if table in _FG2_DIAGNOSTIC_TABLES:
        payload["table"] = table
    if (
        isinstance(http_status, int)
        and not isinstance(http_status, bool)
        and 100 <= http_status <= 599
    ):
        payload["http_status"] = http_status
    try:
        sys.stderr.write(
            _FG2_DIAGNOSTIC_PREFIX
            + json.dumps(payload, separators=(",", ":"), sort_keys=True)
            + "\n"
        )
        sys.stderr.flush()
    except Exception:
        # The diagnostic must never replace the original worker outcome.
        return


try:
    import requests
    from bs4 import BeautifulSoup
    from playwright.async_api import async_playwright
    from curl_cffi import CurlOpt
    from curl_cffi.requests import AsyncSession
    from dotenv import load_dotenv
except Exception:
    _emit_fg2_diagnostic("dependency_import", "dependency_import_failed")
    raise

try:
    from playwright_stealth import Stealth
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False

try:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from shared.utils import (
        clean_course_name,
        infer_course_type,
        standardize_category,
        slugify,
        normalize_url,
        get_random_user_agent,
        setup_lima_logging,
        normalize_url
    )
    from shared.db_client import DatabaseAPIError, DatabaseWriteOutcomeUnknown, get_db_client
    from shared.site_diagnostics import MAX_RESPONSE_BODY_BYTES
    from scripts.core.fg2_bounded_run import (
        FG2ApprovedLotManifest,
        FG2CohortManifest,
        FG2_LIMITS,
        FG2_NON_HTML_EXTENSIONS,
        FG2RequestBudget,
        InvalidControlledRun,
        OriginDeferred,
        public_url_resolve_entry,
        ResponseBodyTooLarge,
        RunBudgetExceeded,
        SitemapBudgetYield,
        SourceBlocked,
        UnsafePublicTarget,
        append_manifest_entry,
        append_manifest_blocker,
        append_manifest_discovery_row,
        approved_url_alias_filter,
        cleanse_course_url,
        course_identity_url,
        course_url_alias_filter,
        cleansed_url_sha256_for_record,
        stable_json_sha256,
        update_manifest_institution,
        update_manifest_origin_state,
        validate_public_request_url,
        validate_public_url_shape,
        validate_public_redirect_target,
        _safe_regex as safe_regex,
        validate_controlled_profile,
        validate_harvester_run_mode,
        verify_approved_lot_scope,
        profile_seed_role,
        _origin as _request_origin,
        url_sha256,
        _has_nested_quantified_group,
        is_safe_profile_regex,
        profile_url_policy_rejection,
        safe_profile_regex_search,
    )
except Exception:
    _emit_fg2_diagnostic("dependency_import", "dependency_import_failed")
    raise

def _initialize_module_runtime():
    try:
        runtime_logger = setup_lima_logging("UniversalHarvester")
        load_dotenv()
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        return runtime_logger
    except Exception:
        _emit_fg2_diagnostic("module_initialization", "module_initialization_failed")
        raise


logger = _initialize_module_runtime()


DISCOVERED_STATUS = "discovered"
PROTECTED_STAGING_STATUSES = frozenset({
    "pending",
    "processing",
    "processed",
    "discarded",
    "skipped",
    "error",
})
KNOWN_STAGING_STATUSES = PROTECTED_STAGING_STATUSES | {DISCOVERED_STATUS}
CONTROLLED_RESPONSE_BODY_LIMIT_BYTES = MAX_RESPONSE_BODY_BYTES

CANARY_RUN_METADATA_KEYS = (
    ("F10_PRODUCTION_CANARY_RUN_ID", "f10_production_canary_run_id"),
    ("F99_CERTIFICATION_CANARY_RUN_ID", "f99_certification_canary_run_id"),
)


def _active_canary_marker():
    for variable_name, metadata_key in CANARY_RUN_METADATA_KEYS:
        run_id = os.getenv(variable_name, "").strip()
        if run_id:
            return metadata_key, run_id
    return None, None


def _is_f10_production_canary():
    return bool(os.getenv("F10_PRODUCTION_CANARY_RUN_ID", "").strip())


def _is_sensitive_log_context():
    return (
        _is_f10_production_canary()
        or os.getenv("FG2_CONTROLLED_FIRST_RUN", "").strip().lower() == "true"
        or os.getenv("FG2_COHORT_SCOPED", "").strip().lower() == "true"
    )


def _safe_url_label(url=None):
    return "source_url=redacted" if _is_sensitive_log_context() else str(url)


def _safe_institution_label(value=None):
    return "canary_cohort=redacted" if _is_sensitive_log_context() else str(value)


def _safe_error_label(error):
    return type(error).__name__ if _is_sensitive_log_context() else str(error)


def _safe_pattern_label(pattern=None):
    return "profile_pattern=redacted" if _is_sensitive_log_context() else str(pattern)


def _prepare_controlled_request(url):
    resolve_entry = public_url_resolve_entry(url)
    return {CurlOpt.RESOLVE: [resolve_entry]} if resolve_entry else {}


async def _close_controlled_response(response):
    """Stop a controlled stream without blocking its event loop during teardown."""
    quit_now = getattr(response, "quit_now", None)
    if quit_now is not None:
        quit_now.set()
    aclose = getattr(response, "aclose", None)
    if callable(aclose):
        await aclose()
        return
    close = getattr(response, "close", None)
    if callable(close):
        close()


async def _request_with_body_limit(session, url, impersonate, timeout, **request_options):
    """Read response headers first, then retain only a bounded streaming body."""
    body = bytearray()
    response = await session.get(
        url,
        impersonate=impersonate,
        timeout=timeout,
        stream=True,
        **request_options,
    )
    status_code = getattr(response, "status_code", None)
    if status_code in {403, 429}:
        response.content = b""
        await _close_controlled_response(response)
        raise SourceBlocked(f"origin stopped after HTTP {status_code}")

    try:
        async for chunk in response.aiter_content():
            if not isinstance(chunk, bytes):
                await _close_controlled_response(response)
                raise OriginDeferred("response stream returned a non-byte chunk")
            if len(body) + len(chunk) > CONTROLLED_RESPONSE_BODY_LIMIT_BYTES:
                await _close_controlled_response(response)
                if status_code != 200:
                    # Preserve headers for redirect/Retry-After handling without
                    # buffering an oversized non-success body.
                    response.content = bytes(body)
                    return response
                raise ResponseBodyTooLarge(
                    "controlled response body exceeds the approved byte limit"
                )
            body.extend(chunk)
    except (OriginDeferred, ResponseBodyTooLarge):
        raise
    except Exception:
        await _close_controlled_response(response)
        raise

    response.content = bytes(body)
    return response


async def _send_controlled_request(_session, url, curl_options, impersonate, timeout):
    """Send one pinned GET and retain only a fully received, bounded response."""
    async with AsyncSession(
        trust_env=False,
        proxies={},
        curl_options=curl_options or {},
        verify=True,
        allow_redirects=False,
        max_redirects=0,
        retry=0,
    ) as pinned_session:
        return await _request_with_body_limit(
            pinned_session,
            url,
            impersonate,
            timeout,
            allow_redirects=False,
            proxies={},
            verify=True,
        )


def _mark_canary_metadata(metadata):
    payload = dict(metadata or {})
    metadata_key, run_id = _active_canary_marker()
    if metadata_key and run_id:
        payload[metadata_key] = run_id
    return payload


def _mark_canary_notes(notes):
    metadata_key, run_id = _active_canary_marker()
    if not run_id:
        return notes
    label = "F10 production" if metadata_key == "f10_production_canary_run_id" else "F9.9 certification"
    marker = f"{label} canary run {run_id}"
    if notes:
        return f"{notes}\n{marker}"
    return marker


class HarvesterRunError(RuntimeError):
    """Raised when FG2 cannot prove a safe complete outcome."""


class HarvesterPartialError(HarvesterRunError):
    """Raised for a per-URL failure that must preserve the source state."""


def _emit_failure_for_exception(phase, error):
    if isinstance(error, DatabaseWriteOutcomeUnknown):
        category = "database_write_outcome_unknown"
    elif isinstance(error, DatabaseAPIError):
        category = "database_api_error"
    elif isinstance(error, InvalidControlledRun):
        category = "controlled_run_rejected"
    elif isinstance(error, HarvesterRunError):
        category = "harvester_rejected"
    elif isinstance(error, (asyncio.TimeoutError, TimeoutError)):
        category = "timeout"
    elif isinstance(error, requests.RequestException) or type(error).__name__ in {
        "RequestException",
        "ConnectionError",
        "ConnectTimeout",
        "ReadTimeout",
    }:
        category = "source_request_error"
    elif isinstance(error, OSError):
        category = "os_error"
    elif isinstance(error, (json.JSONDecodeError, TypeError, ValueError)):
        category = "invalid_input"
    else:
        category = "unexpected_exception"

    table = getattr(error, "table", None)
    http_status = getattr(error, "status_code", None)
    _emit_fg2_diagnostic(phase, category, table=table, http_status=http_status)


class UniversalHarvester:
    def __init__(
        self,
        institution,
        global_start=None,
        max_discovered_urls=None,
        controlled=False,
        cohort_manifest=None,
        approved_lot_manifest=None,
        approved_lot_reference=None,
        approved_lot_sha256=None,
        require_approved_lot=False,
        scheduled_cohort=False,
        _controlled_transport=None,
    ):
        import time
        self.institution = institution
        self.db = get_db_client()
        self.visited_urls = set()
        self.course_urls = set()
        self._controlled_examined_urls = set()
        self._resumable_urls = []
        self._discovered_rows_by_url = {}
        self._discovery_fetch_attempts = 0
        self._discovery_fetch_successes = 0
        configured_url_limit = max_discovered_urls
        if configured_url_limit is None:
            configured_url_limit = FG2_LIMITS["max_urls_per_institution"]
        if isinstance(configured_url_limit, bool) or not isinstance(configured_url_limit, int) or configured_url_limit < 1:
            raise HarvesterRunError("FG2 URL limit must be a positive integer")
        self.max_discovered_urls = min(
            configured_url_limit,
            FG2_LIMITS["max_urls_per_institution"],
        )
        self.controlled = bool(controlled)
        self.scheduled_cohort = bool(scheduled_cohort)
        self.cohort_manifest_path = cohort_manifest
        self.request_budget = None
        self.controlled_stop_reason = None
        self.sitemap_budget_reached = False
        self.controlled_seed_urls = []
        self.controlled_source_urls = []
        self._browser_navigation_kind = "detail"
        self._browser_blocked_required_count = 0
        self._browser_blocked_resource_count = 0
        self.approved_lot = None
        self.approved_lot_scope = None
        self.approved_lot_scope_verified_for_write = False
        self._staging_rows_by_url = {}
        self._recorded_blocker_ids = set()
        self._recorded_discovery_ids = set()
        self.impersonate = "chrome110"
        self.error_count = 0
        self.BLOCK_THRESHOLD = 5
        self.MAX_DEPTH = 3
        self.semaphore = asyncio.Semaphore(3)
        self.circuit_open = False
        self.profile = self._load_site_profile(allow_auto_detect=not self.controlled)
        if self.controlled:
            if not self.cohort_manifest_path or not self.profile:
                raise HarvesterRunError("controlled run requires a configured profile and cohort manifest")
            approved_seed_urls = self.institution.get("_controlled_seed_urls")
            if approved_lot_manifest and not isinstance(approved_seed_urls, list):
                raise HarvesterRunError("controlled run requires the approved seed selection")
            try:
                preflight = validate_controlled_profile(
                    self.institution,
                    self.profile,
                    selected_seed_urls=approved_seed_urls if approved_lot_manifest else None,
                    scheduled_cohort=scheduled_cohort,
                )
            except InvalidControlledRun as exc:
                raise HarvesterRunError("controlled profile preflight rejected this institution") from exc
            if preflight["profile_sha256"] != institution.get("_controlled_profile_sha256"):
                raise HarvesterRunError("controlled profile changed after master preflight")
            if preflight["seed_sha256"] != institution.get("_controlled_seed_sha256"):
                raise HarvesterRunError("controlled seeds changed after master preflight")
            self.profile = preflight["effective_profile"]
            self.controlled_seed_urls = preflight["seed_urls"]
            self.controlled_source_urls = preflight["source_urls"]
            if require_approved_lot and not all((approved_lot_manifest, approved_lot_reference, approved_lot_sha256)):
                raise HarvesterRunError("controlled harvester requires the reviewed FG2 lot binding")
            if approved_lot_manifest:
                try:
                    self.approved_lot = FG2ApprovedLotManifest.load(
                        approved_lot_manifest,
                        expected_sha256=approved_lot_sha256,
                        expected_reference=approved_lot_reference,
                        expected_source_sha=os.getenv("GITHUB_SHA", ""),
                    )
                    approved_institution = self.approved_lot.institution(str(self.institution.get("id")))
                    self.approved_lot.assert_institution_origin(
                        str(self.institution.get("id")),
                        str(self.institution.get("website_url") or ""),
                    )
                    current_institutions = self.db.select_service_raise(
                        "institutions",
                        filters=f"id=eq.{quote(str(self.institution.get('id')), safe='')}",
                        columns="id,slug,website_url",
                        limit=2,
                    )
                except (InvalidControlledRun, TypeError, ValueError) as exc:
                    raise HarvesterRunError("approved FG2 lot binding is invalid") from exc
                if len(current_institutions) != 1:
                    raise HarvesterRunError("approved FG2 lot institution is missing or duplicated")
                current_institution_fingerprint = stable_json_sha256(
                    {
                        "id": str(current_institutions[0].get("id", "")).lower(),
                        "slug": current_institutions[0].get("slug"),
                        "website_url": current_institutions[0].get("website_url"),
                    }
                )
                if (
                    approved_lot_sha256.lower() != self.approved_lot.sha256
                    or approved_lot_reference != self.approved_lot.reference
                    or current_institution_fingerprint != approved_institution["institution_sha256"]
                    or approved_institution["profile_sha256"] != preflight["profile_sha256"]
                    or approved_institution["seed_sha256"] != preflight["seed_sha256"]
                    or approved_institution["seed_urls"] != preflight["seed_urls"]
                ):
                    raise HarvesterRunError("approved FG2 lot institution or seeds drifted")
                self.approved_lot_scope = {
                    item["url"]: item
                    for item in self.approved_lot.scope_for_institution(str(self.institution.get("id")))
                }
                if not self.approved_lot_scope:
                    raise HarvesterRunError("approved FG2 lot has no URLs for this institution")
                verify_approved_lot_scope(
                    self.db,
                    self.approved_lot,
                    institution_ids=[str(self.institution.get("id"))],
                )
            elif require_approved_lot:
                raise HarvesterRunError("controlled harvester requires the reviewed FG2 lot")
            else:
                self.approved_lot_scope = None
            if self.profile.get("discovery_mode") == "hardcoded_urls":
                self.profile["seed_urls"] = list(self.controlled_seed_urls)
            try:
                self._controlled_manifest = FG2CohortManifest.load(
                    self.cohort_manifest_path,
                    expected_run_id=os.getenv("GITHUB_RUN_ID", ""),
                    expected_run_attempt=int(os.getenv("GITHUB_RUN_ATTEMPT", "")),
                    expected_source_sha=os.getenv("GITHUB_SHA", ""),
                    expected_approved_lot_reference=approved_lot_reference,
                    expected_approved_lot_sha256=approved_lot_sha256,
                    allow_empty=True,
                )
            except (InvalidControlledRun, TypeError, ValueError) as exc:
                raise HarvesterRunError("controlled cohort context is invalid") from exc
            self.request_budget = FG2RequestBudget(
                request_preparer=(
                    _controlled_transport.prepare
                    if _controlled_transport is not None
                    else _prepare_controlled_request
                ),
                requester=(
                    _controlled_transport.request
                    if _controlled_transport is not None
                    else _send_controlled_request
                ),
                origin_state=self._controlled_manifest.payload.get("origin_state", {}),
                on_origin_state_change=lambda origin_sha256, last_started, stop_reason: update_manifest_origin_state(
                    self.cohort_manifest_path,
                    origin_sha256=origin_sha256,
                    last_started_monotonic=last_started,
                    stop_reason=stop_reason,
                ),
                allowed_urls=(
                    tuple(self.approved_lot_scope)
                    if self.approved_lot_scope is not None
                    else None
                ),
                allowed_source_urls=tuple(self.controlled_source_urls),
                allowed_resource_origins=tuple(self._allowed_resource_origins()),
                url_validator=self._validate_profile_request_url,
            )
        else:
            self._controlled_manifest = None
            self.request_budget = FG2RequestBudget(
                request_preparer=_prepare_controlled_request,
                requester=_send_controlled_request,
                allowed_resource_origins=tuple(self._allowed_resource_origins()),
                url_validator=self._validate_profile_request_url,
            )
        self.exclusions = self._load_exclusions()

        # Fase 62: Perfil-driven config — todo el comportamiento diferenciado sale del perfil
        self.site_type = self.profile.get('site_type', 'traditional_ssr') if self.profile else 'traditional_ssr'
        self.discovery_mode = self.profile.get('discovery_mode', 'sitemap_bfs') if self.profile else 'sitemap_bfs'
        self.requires_stealth = self.profile.get('requires_stealth', False) if self.profile else False
        self.requires_cf_bypass = self.profile.get('requires_cloudflare_bypass', False) if self.profile else False
        self.popup_selectors = self.profile.get('popup_close_selectors', []) if self.profile else []
        self.detail_wait_ms = self.profile.get('detail_wait_ms', 2000) if self.profile else 2000
        self.warmup_url = self.profile.get('warmup_url') if self.profile else None
        self.catalog_link_selector = self.profile.get('catalog_link_selector') if self.profile else None
        self.catalog_max_pages = self.profile.get('catalog_max_pages', 5) if self.profile else 5
        self.catalog_scroll_iterations = self.profile.get('catalog_scroll_iterations', 0) if self.profile else 0
        self.section_keywords = self.profile.get('section_keywords', {}) if self.profile else {}
        self.field_defaults = self.profile.get('field_defaults', {}) if self.profile else {}
        # Fase 79B: Circuit Breaker
        self.max_consecutive_errors = self.profile.get('max_consecutive_errors', self.BLOCK_THRESHOLD) if self.profile else self.BLOCK_THRESHOLD
        db_circuit_open = self.profile.get('circuit_open', False) if self.profile else False
        db_circuit_opened_at = self.profile.get('circuit_opened_at') if self.profile else None
        if db_circuit_open and db_circuit_opened_at:
            opened = db_circuit_opened_at
            if isinstance(opened, str):
                opened = datetime.fromisoformat(opened.replace('Z', '+00:00'))
            hours_since = (datetime.now(timezone.utc) - opened).total_seconds() / 3600
            if hours_since < 24:
                self.circuit_open = True
                logger.warning(f"Circuito abierto para {_safe_institution_label(self.institution.get('name'))} (abierto hace {hours_since:.1f}h). Saltando.")
            else:
                logger.info(f"Circuito auto-cerrado para {_safe_institution_label(self.institution.get('name'))} (>24h desde apertura).")
                try:
                    self.db.patch('institution_site_profiles', filters=f"institution_id=eq.{self.institution.get('id')}", data={'circuit_open': False, 'circuit_opened_at': None})
                except Exception:
                    pass

        # ⏱️ TIME GUARD CONFIG
        self.global_start = global_start or time.time()
        self.MAX_RUN_TIME = 20400

    # StudIAMatch-Docs: .context/componentes/pipeline.md#primera-corrida-fg2-acotada
    def _can_discover_more(self):
        if self.max_discovered_urls is None:
            return True
        counted_urls = self.course_urls
        if self.controlled:
            counted_urls = counted_urls | self._controlled_examined_urls
        return len(counted_urls) < self.max_discovered_urls

    def _mark_controlled_url_examined(self, url):
        if not self.controlled:
            return True
        normalized = normalize_url(url)
        if normalized in self.course_urls or normalized in self._controlled_examined_urls:
            return True
        if not self._can_discover_more():
            return False
        self._controlled_examined_urls.add(normalized)
        return True

    def _limit_urls(self, urls):
        urls = list(urls)
        if self.max_discovered_urls is None or len(urls) <= self.max_discovered_urls:
            return urls
        logger.info(f"Canary URL limit applied: {self.max_discovered_urls}/{len(urls)} URLs")
        return urls[:self.max_discovered_urls]

    @staticmethod
    def _normalize_jsonb_list(value):
        """Convert JSONB string to list if needed (Bug 5 defensive fix)."""
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return parsed
            except (json.JSONDecodeError, TypeError):
                pass
            return []
        if isinstance(value, list):
            return value
        return [] if value is None else value

    def _allowed_resource_origins(self):
        """Return exact, explicitly configured browser resource origins.

        The institutional origin is always included. Cross-origin CDN/API
        hosts are opt-in profile values; each request still gets DNS checked,
        pinned and charged to the institution budget.
        """
        website_url = self.institution.get("website_url")
        validate_public_url_shape(str(website_url or ""))
        origins = {_request_origin(str(website_url))}
        raw_origins = self.profile.get("allowed_resource_origins", []) if self.profile else []
        if isinstance(raw_origins, str):
            raw_origins = self._normalize_jsonb_list(raw_origins)
        if not isinstance(raw_origins, list):
            raise HarvesterRunError("browser resource origin allowlist is malformed")
        for value in raw_origins:
            if not isinstance(value, str) or not value.strip():
                raise HarvesterRunError("browser resource origin allowlist is malformed")
            candidate = value.strip()
            validate_public_url_shape(candidate)
            parsed = urlsplit(candidate)
            if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
                raise HarvesterRunError("browser resource allowlist must contain exact origins")
            origins.add(_request_origin(candidate))
        return origins

    def _validate_profile_request_url(self, url, request_kind):
        role = {
            "detail": "course_detail",
            "sitemap": "sitemap_source",
            "catalog_source": "catalog_source",
            "subresource": "subresource",
        }.get(request_kind)
        if role is None:
            return "invalid_url_role"
        return profile_url_policy_rejection(
            url,
            str(self.institution.get("website_url") or ""),
            self.profile,
            approved_lot_scope=(
                self.approved_lot_scope if role == "course_detail" else None
            ),
            role=role,
            regex_module=safe_regex,
        )

    @staticmethod
    def _is_safe_profile_regex(pattern):
        return is_safe_profile_regex(pattern)

    @staticmethod
    def _safe_profile_search(pattern, text):
        evaluated, match = safe_profile_regex_search(
            pattern,
            text,
            regex_module=safe_regex,
        )
        if not evaluated:
            logger.error("Profile regex evaluation failed; URL policy fails closed")
            return None
        return match

    def _load_site_profile(self, allow_auto_detect=True):
        inst_id = self.institution.get('id')
        profiles = self.db.select_pipeline_raise(
            'institution_site_profiles',
            filters=f'institution_id=eq.{inst_id}',
            limit=1,
        )
        if profiles and len(profiles) > 0:
            profile = profiles[0]
            if profile.get("profile_status") == "pending_review":
                logger.info("Profile onboarding is pending review; the harvester will not infer an effective mode.")
                return profile
            has_site_type = profile.get('site_type')
            has_discovery = profile.get('discovery_mode')
            if has_site_type and has_discovery:
                norm_fields = ['catalog_url_patterns', 'exclusion_patterns',
                               'allowed_url_patterns', 'seed_urls']
                for field in norm_fields:
                    if field in profile:
                        profile[field] = self._normalize_jsonb_list(profile[field])
                logger.info(f"Loaded site profile: site_type={profile.get('site_type')}, discovery_mode={profile.get('discovery_mode')}")
                return profile
            logger.info("Profile is incomplete; onboarding owns diagnostics and the harvester fails closed.")
            return profile
        logger.info("No effective site profile exists; an allowlisted FG2 onboarding phase must diagnose it first.")
        return {}

    def _auto_detect_profile(self):
        """Legacy hook intentionally fails closed; onboarding runs before selection."""
        logger.info("Inline profile auto-detection is disabled; use the allowlisted onboarding phase.")
        return {}

    def _load_exclusions(self):
        try:
            if self.profile and self.profile.get('exclusion_patterns'):
                raw = self.profile['exclusion_patterns']
                compiled = []
                for exc in raw:
                    if isinstance(exc, str):
                        if exc.startswith('re:'):
                            pat = exc[3:]
                            if len(pat) > 200:
                                logger.warning(f"Regex pattern too long, skipping: {_safe_pattern_label(pat)}")
                                continue
                            if _has_nested_quantified_group(pat):
                                logger.warning(f"ReDoS-risk pattern rejected: {_safe_pattern_label(pat)}")
                                continue
                            try:
                                compiled.append(('re', pat))
                            except re.error as e:
                                logger.warning(f"Invalid regex pattern {_safe_pattern_label(pat)}: {_safe_error_label(e)}")
                                continue
                        else:
                            compiled.append(exc.lower())
                return compiled
            return []
        except Exception as e:
            logger.warning(f"Error loading exclusions: {_safe_error_label(e)}")
            return []

    def _gate_enabled(self, gate_name):
        if not self.profile:
            return False
        if gate_name in self.profile:
            return bool(self.profile.get(gate_name))
        return bool(self.profile.get('pipeline_ready'))

    def check_time_guard(self):
        """Checks if the global execution time limit has been reached."""
        import time
        elapsed = time.time() - self.global_start
        if elapsed > self.MAX_RUN_TIME:
            logger.warning(f"⚠️ [TIME GUARD] Límite de ejecución global alcanzado ({elapsed/3600:.2f}h). Solicitando detención...")
            self.circuit_open = True
            return True
        return False

    def _extract_canonical(self, html_content):
        if not html_content: return None
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            canonical = soup.find("link", rel="canonical")
            if canonical and canonical.get("href"):
                return normalize_url(canonical["href"].strip())
        except Exception as e:
            logger.warning(f"Error extracting canonical URL: {_safe_error_label(e)}")
        return None

    def _generate_hash(self, text):
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    async def _check_if_changed(self, url, html_content, effective_url=None, canonical_url=None, force_changed=False):
        content_hash = self._generate_hash(html_content)
        if force_changed:
            return True, content_hash
        try:
            ids = [url, effective_url, canonical_url]
            ids = [normalize_url(i) for i in ids if i]
            data = self.db.select_pipeline_raise(
                "staging_raw",
                filters=f"url=eq.{quote(normalize_url(url), safe='')}",
                columns="content_hash",
            )
            if data and len(data) > 0:
                old_hash = data[0].get('content_hash')
                if old_hash == content_hash:
                    return False, content_hash
        except Exception as exc:
            raise DatabaseAPIError(
                "Backend read failed while checking staging content hash"
            ) from exc
        return True, content_hash

    def _is_html_response(self, response):
        headers = getattr(response, "headers", {}) or {}
        content_type = ""
        if isinstance(headers, dict):
            content_type = headers.get("content-type") or headers.get("Content-Type") or ""
        if content_type and "html" not in str(content_type).lower():
            return False
        text = getattr(response, "text", "") or ""
        lowered = text[:1000].lower()
        return "<html" in lowered or "<!doctype html" in lowered

    # StudIAMatch-Docs: .context/componentes/pipeline.md#primera-corrida-fg2-acotada
    async def _safe_request(self, session, url, *, request_kind="detail"):
        try:
            if self.controlled and self.approved_lot is not None and self.request_budget.http_requests == 0:
                self._verify_approved_institution_binding()
                try:
                    verify_approved_lot_scope(
                        self.db,
                        self.approved_lot,
                        institution_ids=[str(self.institution.get("id"))],
                    )
                except InvalidControlledRun as exc:
                    raise HarvesterRunError(
                        "approved FG2 lot state drifted before the first source request"
                    ) from exc
            allowed_origin = (
                _request_origin(url)
                if request_kind == "subresource"
                else self.institution.get("website_url")
            )
            return await self.request_budget.get(
                session,
                url,
                allowed_origin=allowed_origin,
                impersonate=self.impersonate,
                timeout=25,
                request_kind=request_kind,
            )
        except SitemapBudgetYield:
            if request_kind not in {"sitemap", "catalog_source"}:
                raise
            self.sitemap_budget_reached = True
            logger.info(
                "FG2 source traversal yielded its allocation; course-detail capacity remains reserved."
            )
            raise
        except (SourceBlocked, OriginDeferred, RunBudgetExceeded) as exc:
            self.controlled_stop_reason = type(exc).__name__
            self.circuit_open = True
            logger.warning(
                "FG2 institution stopped for this run: %s",
                self.controlled_stop_reason,
            )
            raise

    async def _fetch_sitemap(self, session, sitemap_url):
        if self.check_time_guard() or self.controlled_stop_reason:
            return []
        if getattr(self, "sitemap_budget_reached", False):
            return []
        if self._is_compressed_sitemap_url(sitemap_url):
            self.controlled_stop_reason = "UnsupportedCompressedSitemap"
            self.circuit_open = True
            logger.warning("FG2 stopped on an unsupported compressed sitemap source.")
            return []
        logger.info(f"Checking Sitemap: {_safe_url_label(sitemap_url)}")
        links = []
        self._discovery_fetch_attempts += 1
        try:
            resp = await self._safe_request(session, sitemap_url, request_kind="sitemap")
        except SitemapBudgetYield:
            self.sitemap_budget_reached = True
            return links
        except (SourceBlocked, OriginDeferred, RunBudgetExceeded):
            return links
        if not resp or resp.status_code != 200: return links
        self._discovery_fetch_successes += 1
        try:
            root = ET.fromstring(resp.content)

            def sitemap_location(node):
                element = node.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                value = element.text if element is not None else None
                return value.strip() if isinstance(value, str) and value.strip() else None

            for sitemap in root.findall('{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap'):
                if self.check_time_guard() or self.controlled_stop_reason or (
                    self.controlled and getattr(self, "sitemap_budget_reached", False)
                ):
                    break
                loc = sitemap_location(sitemap)
                if loc:
                    links.extend(await self._fetch_sitemap(session, loc))
            for url in root.findall('{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
                if self.check_time_guard(): break
                loc = sitemap_location(url)
                if loc:
                    links.append(loc)
        except Exception as e:
            logger.warning(f"Failed to parse sitemap {_safe_url_label(sitemap_url)}: {type(e).__name__}")
        return list(dict.fromkeys(links)) if self.controlled else list(set(links))

    async def _bfs_crawl(self, start_url, existing_urls):
        queue = [(start_url, 0)]
        self.visited_urls.add(start_url)
        async with AsyncSession() as session:
            while queue and len(self.course_urls) < 500 and self._can_discover_more():
                if self.circuit_open or self.check_time_guard(): break
                current_batch = [queue.pop(0) for _ in range(min(len(queue), 3))]
                tasks = []
                for url, depth in current_batch:
                    if depth < self.MAX_DEPTH:
                        tasks.append(self._fetch_and_parse(session, url, depth))
                results = await asyncio.gather(*tasks)
                for links, next_depth in results:
                    if self.check_time_guard(): break
                    for link in links:
                        if not self._can_discover_more():
                            break
                        if self._is_valid_crawl_url(link):
                            normalized = normalize_url(link)
                            if normalized not in self.course_urls and normalized not in existing_urls:
                                row = self._queue_discovered_candidate(normalized)
                                if row["status"] == DISCOVERED_STATUS:
                                    self.course_urls.add(normalized)
                            if self._is_valid_crawl_url(link) and link not in self.visited_urls:
                                queue.append((link, next_depth))

    NON_HTML_EXTENSIONS = FG2_NON_HTML_EXTENSIONS

    def _is_valid_crawl_url(self, url):
        profile = getattr(self, "profile", None)
        if not isinstance(profile, dict) or not profile:
            # Keep the legacy/test construction contract fail-closed while
            # routing all decisions through the shared FG2 URL policy.
            exclusions = getattr(self, "exclusions", [])
            normalized_exclusions = []
            for exclusion in exclusions:
                if isinstance(exclusion, tuple) and len(exclusion) == 2 and exclusion[0] == "re":
                    normalized_exclusions.append(f"re:{exclusion[1]}")
                elif isinstance(exclusion, str):
                    normalized_exclusions.append(exclusion)
            profile = {"exclusion_patterns": normalized_exclusions}
        rejection = profile_url_policy_rejection(
            url,
            self.institution.get("website_url"),
            profile,
            approved_lot_scope=getattr(self, "approved_lot_scope", None),
            regex_module=safe_regex,
        )
        if rejection:
            logger.debug("[URL POLICY] Course candidate rejected: %s", rejection)
            return False
        return True

    async def _fetch_and_parse(self, session, url, depth):
        links = []
        if self.circuit_open or self.check_time_guard(): return list(set(links)), depth + 1
        try:
            self._discovery_fetch_attempts += 1
            response = await self._safe_request(session, url, request_kind="catalog_source")
            if response and response.status_code == 200:
                self._discovery_fetch_successes += 1
                html = response.text
                parser = 'xml' if html.strip().startswith('<?xml') or '<urlset' in html else 'html.parser'
                soup = BeautifulSoup(html, parser)
                for a in soup.find_all('a', href=True):
                    full_url = urljoin(url, a['href']).split('#')[0].strip()
                    if full_url.startswith('http'):
                        links.append(full_url)
        except Exception:
            pass
        return list(set(links)), depth + 1

    def _merge_resumable_urls(self, urls):
        final_urls = []
        resumable = [] if self.controlled else self._resumable_urls
        for url in resumable + list(urls):
            normalized = normalize_url(url)
            if normalized not in final_urls:
                final_urls.append(normalized)
        return final_urls

    def _remember_discovered_row(self, row):
        normalized = normalize_url(row.get('url') or '')
        self._discovered_rows_by_url[normalized] = {
            "id": row.get('id'),
            "url": normalized,
            "status": row.get('status'),
            "content_hash": row.get('content_hash'),
            "kind": row.get('kind'),
            "course_id": row.get('course_id'),
            "original_status": row.get("original_status") or row.get("status"),
            "previous_content_hash": row.get("previous_content_hash"),
            "expected_staging_url": row.get("expected_staging_url") or row.get("url"),
            "course_snapshot": row.get("course_snapshot"),
        }

    def _select_staging_rows_by_url(self, url):
        normalized_url = normalize_url(url)
        if self.approved_lot is not None:
            approved_scope = self.approved_lot_scope.get(normalized_url)
            if not approved_scope:
                raise HarvesterRunError("staging URL is outside the reviewed FG2 lot")
            expected_rows = approved_scope["snapshot"]["staging_rows"]
            try:
                if expected_rows:
                    rows = []
                    for expected in expected_rows:
                        current = self.db.select_pipeline_raise(
                            "staging_raw",
                            filters=f"id=eq.{quote(expected['id'], safe='')}",
                            columns="id,url,status,institution_id,content_hash",
                            limit=2,
                        )
                        if len(current) != 1:
                            raise HarvesterRunError("approved FG2 lot staging identity is missing or duplicated")
                        actual = current[0]
                        if any(actual.get(field) != expected.get(field) for field in (
                            "id", "url", "status", "institution_id", "content_hash"
                        )):
                            raise HarvesterRunError("approved FG2 lot staging row drifted")
                        if normalize_url(actual.get("url") or "") != normalized_url:
                            raise HarvesterRunError("approved FG2 lot staging URL identity drifted")
                        rows.append(actual)
                    return rows

                institution_id = str(self.institution.get("id") or "")
                if institution_id.lower() != str(approved_scope.get("institution_id") or "").lower():
                    raise HarvesterRunError("approved FG2 lot institution identity drifted")
                filters = (
                    f"institution_id=eq.{quote(institution_id, safe='')}&"
                    f"{approved_url_alias_filter([normalized_url])}"
                )
                current_rows = self.db.select_pipeline_raise(
                    "staging_raw",
                    filters=filters,
                    columns="id,url,status,institution_id,content_hash",
                    order="id.asc",
                    limit=2,
                )
            except HarvesterRunError:
                raise
            except Exception as exc:
                raise HarvesterRunError("failed to verify approved FG2 staging identity") from exc
            if not isinstance(current_rows, list):
                raise HarvesterRunError("malformed approved FG2 staging inventory")
            if any(
                isinstance(row, dict) and normalize_url(row.get("url") or "") == normalized_url
                for row in current_rows
            ):
                raise HarvesterRunError("approved FG2 lot staging identity appeared after preflight")
            return []
        if self.controlled and getattr(self, "scheduled_cohort", False):
            try:
                rows = self.db.select_pipeline_raise(
                    "staging_raw",
                    filters=approved_url_alias_filter([normalized_url]),
                    columns="id,url,status,institution_id,content_hash",
                    order="id.asc",
                    limit=2,
                )
            except Exception as exc:
                raise HarvesterRunError("failed to verify scheduled staging identity") from exc
            if not isinstance(rows, list):
                raise HarvesterRunError("malformed scheduled staging inventory")
            if len(rows) > 1:
                raise HarvesterRunError("scheduled staging identity is ambiguous")
            if not rows:
                return []

            row = rows[0]
            if not isinstance(row, dict):
                raise HarvesterRunError("malformed scheduled staging identity")
            row_id = row.get("id")
            row_url = row.get("url")
            status = row.get("status")
            if not isinstance(row_id, str) or not row_id:
                raise HarvesterRunError("malformed scheduled staging identity")
            if not isinstance(row_url, str) or not row_url or normalize_url(row_url) != normalized_url:
                raise HarvesterRunError("scheduled staging URL identity drifted")
            if status not in KNOWN_STAGING_STATUSES:
                raise HarvesterRunError("unknown scheduled staging status")
            if str(row.get("institution_id") or "").lower() != str(
                self.institution.get("id") or ""
            ).lower():
                raise HarvesterRunError("scheduled staging owner identity drifted")

            cached = dict(row, url=normalized_url)
            self._staging_rows_by_url[normalized_url] = cached
            return [cached]
        try:
            rows = self.db.select_pipeline_raise(
                "staging_raw",
                filters=f"url=eq.{quote(normalized_url, safe='')}",
                columns="id,url,status,institution_id,content_hash",
            )
        except Exception as exc:
            raise HarvesterRunError("failed to verify URL ownership") from exc
        if not isinstance(rows, list):
            raise HarvesterRunError("malformed URL ownership payload")
        return rows

    def _record_existing_staging_blocker(self, normalized_url):
        row = self._staging_rows_by_url.get(normalized_url)
        if row and row.get("status") in PROTECTED_STAGING_STATUSES:
            self._record_refresh_blocker(row)

    def _record_discovery_row(self, row):
        if not self.controlled or not isinstance(row, dict) or row.get("status") != DISCOVERED_STATUS:
            return
        staging_id = row.get("id")
        if not staging_id or staging_id in self._recorded_discovery_ids:
            return
        initial_status = row.get("original_status") or DISCOVERED_STATUS
        discovery_record = {
            "institution_id": self.institution["id"],
            "staging_id": staging_id,
            "url_sha256": url_sha256(row.get("url") or ""),
            "initial_status": initial_status,
            "kind": row.get("kind") or "new_discovery",
            "course_id": row.get("course_id"),
        }
        if initial_status == "processed":
            discovery_record["content_sha256"] = row.get("previous_content_hash")
        append_manifest_discovery_row(self.cohort_manifest_path, discovery_record)
        self._recorded_discovery_ids.add(staging_id)

    def _course_for_refresh(self, normalized_url):
        normalized_url = normalize_url(normalized_url)
        expected_course_identity = course_identity_url(normalized_url)
        if self.approved_lot is not None:
            approved_scope = self.approved_lot_scope.get(normalized_url)
            if not approved_scope:
                raise HarvesterRunError("course URL is outside the reviewed FG2 lot")
            expected_rows = approved_scope["snapshot"]["course_rows"]
            if not expected_rows:
                try:
                    rows = self.db.select_service_raise(
                        "courses",
                        filters=course_url_alias_filter([normalized_url]),
                        columns="id,institution_id,url,is_active,is_verified,last_404_at",
                        limit=2,
                    )
                except Exception as exc:
                    raise HarvesterRunError("failed to verify approved FG2 course identity") from exc
                if not isinstance(rows, list):
                    raise HarvesterRunError("malformed approved FG2 course inventory")
                if rows:
                    raise HarvesterRunError("approved FG2 new-course identity appeared after preflight")
                return {"kind": "new_discovery", "course_id": None}

            expected = expected_rows[0]
            rows = self.db.select_service_raise(
                "courses",
                filters=f"id=eq.{quote(expected['id'], safe='')}",
                columns="id,institution_id,url,is_active,is_verified,last_404_at",
                limit=2,
            )
            if len(rows) != 1:
                raise HarvesterRunError("approved FG2 course identity is missing or duplicated")
            actual = rows[0]
            if any(actual.get(field) != expected.get(field) for field in (
                "id", "institution_id", "url", "is_active", "is_verified", "last_404_at"
            )):
                raise HarvesterRunError("approved FG2 course row drifted")
            if course_identity_url(actual.get("url") or "") != expected_course_identity:
                raise HarvesterRunError("approved FG2 course URL identity drifted")
            return {
                "kind": "refresh_existing",
                "course_id": actual.get("id"),
                "course_is_active": actual.get("is_active"),
                "course_is_verified": actual.get("is_verified"),
                "course_url": actual.get("url"),
                "course_last_404_at": actual.get("last_404_at"),
            }

        # Cleansing groups detail-page aliases (for example /presentacion)
        # back to the same course URL that sync resolves in courses.
        rows = self.db.select_service_raise(
            "courses",
            filters=course_url_alias_filter([normalized_url]),
            columns="id,institution_id,url,is_active,is_verified",
            limit=2,
        )
        if len(rows) > 1:
            raise HarvesterRunError("known course URL does not resolve to one courses row")
        if not rows:
            return {"kind": "new_discovery", "course_id": None}
        if str(rows[0].get("institution_id")) != str(self.institution.get("id")):
            raise HarvesterRunError("known course URL belongs to another institution")
        result = {"kind": "refresh_existing", "course_id": rows[0].get("id")}
        if getattr(self, "controlled", False):
            result["course_snapshot"] = {
                "id": rows[0].get("id"),
                "institution_id": rows[0].get("institution_id"),
                "url": rows[0].get("url"),
                "is_active": rows[0].get("is_active"),
                "is_verified": rows[0].get("is_verified"),
                "last_404_at": rows[0].get("last_404_at"),
            }
        if self.approved_lot is not None:
            result["course_is_active"] = rows[0].get("is_active")
            result["course_is_verified"] = rows[0].get("is_verified")
        return result

    def _verify_approved_institution_binding(self):
        if self.approved_lot is None:
            return
        institution_id = str(self.institution.get("id", ""))
        expected = self.approved_lot.institution(institution_id)
        try:
            profile = self._load_site_profile(allow_auto_detect=False)
            preflight = validate_controlled_profile(
                self.institution,
                profile,
                selected_seed_urls=expected["seed_urls"],
            )
        except InvalidControlledRun as exc:
            raise HarvesterRunError(
                "approved FG2 lot institution, profile, or seeds drifted"
            ) from exc
        current_institutions = self.db.select_service_raise(
            "institutions",
            filters=f"id=eq.{quote(institution_id, safe='')}",
            columns="id,slug,website_url",
            limit=2,
        )
        if len(current_institutions) != 1:
            raise HarvesterRunError("approved FG2 lot institution is missing or duplicated")
        current_fingerprint = stable_json_sha256(
            {
                "id": str(current_institutions[0].get("id", "")).lower(),
                "slug": current_institutions[0].get("slug"),
                "website_url": current_institutions[0].get("website_url"),
            }
        )
        self.approved_lot.assert_institution_origin(
            institution_id,
            str(current_institutions[0].get("website_url") or ""),
        )
        if (
            current_fingerprint != expected["institution_sha256"]
            or preflight["profile_sha256"] != expected["profile_sha256"]
            or preflight["seed_sha256"] != expected["seed_sha256"]
            or preflight["seed_urls"] != expected["seed_urls"]
        ):
            raise HarvesterRunError("approved FG2 lot institution, profile, or seeds drifted")

    def _preflight_approved_scope_before_write(self, normalized_url, staging_rows, course):
        if self.approved_lot is None:
            return
        approved_scope = self.approved_lot_scope.get(normalized_url)
        if not approved_scope:
            raise HarvesterRunError("URL is outside the reviewed FG2 lot")
        if not self.approved_lot_scope_verified_for_write:
            try:
                self._verify_approved_institution_binding()
                verify_approved_lot_scope(
                    self.db,
                    self.approved_lot,
                    institution_ids=[str(self.institution.get("id"))],
                )
            except InvalidControlledRun as exc:
                raise HarvesterRunError("approved FG2 lot state drifted before the first write") from exc
        actual_staging = [
            {
                "id": str(row.get("id", "")).lower(),
                "institution_id": str(row.get("institution_id", "")).lower(),
                "url": row.get("url"),
                "status": row.get("status"),
                "content_hash": row.get("content_hash"),
            }
            for row in staging_rows
        ]
        actual_staging.sort(key=lambda row: row["id"])
        expected_staging = approved_scope["snapshot"]["staging_rows"]
        if actual_staging != expected_staging:
            raise HarvesterRunError("approved FG2 lot staging row drifted before write")
        expected_courses = approved_scope["snapshot"]["course_rows"]
        expected_course_id = expected_courses[0]["id"] if expected_courses else None
        expected_kind = "refresh_existing" if expected_courses else "new_discovery"
        if course.get("course_id") != expected_course_id or course.get("kind") != expected_kind:
            raise HarvesterRunError("approved FG2 lot course identity drifted before write")
        if expected_courses and (
            course.get("course_is_active") != expected_courses[0]["is_active"]
            or course.get("course_is_verified") != expected_courses[0]["is_verified"]
            or course.get("course_url") != expected_courses[0]["url"]
            or course.get("course_last_404_at") != expected_courses[0]["last_404_at"]
        ):
            raise HarvesterRunError("approved FG2 lot course state drifted before write")

    def _record_refresh_blocker(self, row):
        if not self.controlled or not isinstance(row, dict):
            return
        staging_id = row.get("id")
        if not staging_id or staging_id in self._recorded_blocker_ids:
            return
        if len(self._recorded_blocker_ids) >= FG2_LIMITS["max_urls_per_institution"]:
            return
        blocker = {
            "institution_id": self.institution["id"],
            "staging_id": staging_id,
            "url_sha256": url_sha256(row.get("url") or ""),
            "content_sha256": row.get("content_hash"),
            "status": row.get("status"),
            "reason": "historical_staging_state_protected",
        }
        append_manifest_blocker(self.cohort_manifest_path, blocker)
        self._recorded_blocker_ids.add(staging_id)

    def _verify_controlled_refresh_course(self, row, normalized_url):
        snapshot = row.get("course_snapshot")
        course_id = row.get("course_id")
        if not isinstance(snapshot, dict) or not course_id or snapshot.get("id") != course_id:
            raise HarvesterRunError("controlled refresh course snapshot is missing")
        try:
            current = self.db.select_service_raise(
                "courses",
                filters=f"id=eq.{quote(str(course_id), safe='')}",
                columns="id,institution_id,url,is_active,is_verified,last_404_at",
                limit=2,
            )
        except Exception as exc:
            raise HarvesterRunError("failed to revalidate controlled refresh course identity") from exc
        if not isinstance(current, list) or len(current) != 1:
            raise HarvesterRunError("controlled refresh course identity is missing or ambiguous")
        actual = current[0]
        expected_identity = course_identity_url(normalized_url)
        if (
            str(actual.get("id", "")).lower() != str(course_id).lower()
            or str(actual.get("institution_id", "")).lower() != str(self.institution.get("id", "")).lower()
            or course_identity_url(actual.get("url") or "") != expected_identity
            or any(actual.get(field) != snapshot.get(field) for field in (
                "id", "institution_id", "url", "is_active", "is_verified", "last_404_at"
            ))
        ):
            raise HarvesterRunError("controlled refresh course identity or state drifted")

    def _discovered_row_for_url(self, url):
        normalized = normalize_url(url)
        row = self._discovered_rows_by_url.get(normalized)
        if row:
            return row
        rows = self.db.select_pipeline_raise(
            "staging_raw",
            filters=(
                f"institution_id=eq.{quote(str(self.institution['id']), safe='')}"
                f"&url=eq.{quote(normalized, safe='')}"
                "&status=eq.discovered"
            ),
            columns="id,url,status,content_hash",
            limit=2,
        )
        if len(rows) != 1:
            raise HarvesterRunError(f"expected exactly one discovered row for {normalized}, got {len(rows)}")
        self._remember_discovered_row(rows[0])
        return self._discovered_rows_by_url[normalized]

    def _validate_pending_payload(self, row, item):
        if not isinstance(item, dict):
            raise HarvesterPartialError("pending payload is malformed")
        url = normalize_url(item.get("url") or "")
        if url != normalize_url(row.get("url") or ""):
            raise HarvesterPartialError("pending payload URL does not match discovered row")
        if item.get("institution_id") != self.institution.get("id"):
            raise HarvesterPartialError("pending payload institution mismatch")
        if item.get("status") != "pending":
            raise HarvesterPartialError("pending payload status is not pending")
        raw_html = item.get("raw_html")
        raw_name = item.get("raw_name")
        content_hash = item.get("content_hash")
        if not isinstance(raw_html, str) or not raw_html.strip():
            raise HarvesterPartialError("pending payload raw_html is empty")
        if "<html" not in raw_html[:1000].lower() and "<!doctype html" not in raw_html[:1000].lower():
            raise HarvesterPartialError("pending payload raw_html is not HTML")
        if not isinstance(raw_name, str) or not raw_name.strip():
            raise HarvesterPartialError("pending payload raw_name is empty")
        if not isinstance(content_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", content_hash):
            raise HarvesterPartialError("pending payload content_hash is invalid")
        if content_hash != self._generate_hash(raw_html):
            raise HarvesterPartialError("pending payload content_hash does not match raw_html")

    def _promote_discovered_to_pending(self, row, item):
        self._validate_pending_payload(row, item)
        if (
            self.controlled
            and self.approved_lot is not None
            and not self.approved_lot_scope_verified_for_write
        ):
            normalized_url = normalize_url(item.get("url") or "")
            staging_rows = self._select_staging_rows_by_url(normalized_url)
            course = self._course_for_refresh(normalized_url)
            self._preflight_approved_scope_before_write(normalized_url, staging_rows, course)
        expected_id = row["id"]
        original_status = row.get("original_status") or DISCOVERED_STATUS
        previous_content_hash = row.get("previous_content_hash")
        if original_status == "processed":
            if not self.controlled or row.get("kind") != "refresh_existing":
                raise HarvesterRunError("processed staging refresh requires a controlled existing-course identity")
            if not re.fullmatch(r"[0-9a-f]{64}", str(previous_content_hash or "")):
                raise HarvesterRunError("processed staging refresh has no valid prior content hash")
            if item.get("content_hash") == previous_content_hash:
                return {
                    "id": expected_id,
                    "url": row["url"],
                    "status": "processed",
                    "institution_id": self.institution["id"],
                    "content_hash": previous_content_hash,
                }
        elif original_status != DISCOVERED_STATUS:
            raise HarvesterRunError("staging row is not eligible for controlled promotion")
        if self.controlled and row.get("kind") == "refresh_existing" and self.approved_lot is None:
            self._verify_controlled_refresh_course(row, normalize_url(item.get("url") or ""))
        expected_staging_url = row.get("expected_staging_url") or row.get("url")
        if not isinstance(expected_staging_url, str) or normalize_url(expected_staging_url) != normalize_url(item.get("url") or ""):
            raise HarvesterRunError("controlled staging URL identity changed before promotion")
        patch_payload = dict(item)
        if self.controlled and self.approved_lot is not None:
            approved_scope = self.approved_lot_scope.get(normalize_url(item.get("url") or ""))
            expected_staging = approved_scope["snapshot"]["staging_rows"] if approved_scope else []
            if expected_staging:
                expected_staging_url = expected_staging[0]["url"]
                if (
                    not isinstance(expected_staging_url, str)
                    or normalize_url(expected_staging_url) != normalize_url(item.get("url") or "")
                ):
                    raise HarvesterRunError("approved staging URL identity changed before promotion")
        patch_payload["url"] = expected_staging_url
        filters = (
            f"id=eq.{quote(str(expected_id), safe='')}"
            f"&institution_id=eq.{quote(str(self.institution['id']), safe='')}"
            f"&url=eq.{quote(expected_staging_url, safe='')}"
            f"&status=eq.{original_status}"
        )
        if original_status == "processed":
            filters += f"&content_hash=eq.{quote(previous_content_hash, safe='')}"

        def matches_pending_row(candidate):
            return (
                isinstance(candidate, dict)
                and candidate.get("id") == expected_id
                and candidate.get("status") == "pending"
                and candidate.get("institution_id") == self.institution.get("id")
                and candidate.get("url") == patch_payload.get("url")
                and normalize_url(candidate.get("url") or "") == normalize_url(item["url"])
                and candidate.get("content_hash") == item.get("content_hash")
            )

        try:
            promoted = self.db.patch_exact_one_raise(
                "staging_raw", filters, patch_payload, expected_id
            )
        except Exception as patch_error:
            # The server may commit a PATCH before its response is lost. Prove
            # the exact persisted row before allowing it into the run manifest.
            try:
                rows = self.db.select_pipeline_raise(
                    "staging_raw",
                    filters=f"id=eq.{quote(str(expected_id), safe='')}",
                    columns="id,url,status,institution_id,content_hash",
                    limit=2,
                )
            except Exception as read_error:
                raise HarvesterRunError(
                    "pending promotion result is ambiguous; exact staging row could not be read"
                ) from read_error
            if (
                not isinstance(rows, list)
                or len(rows) != 1
                or not isinstance(rows[0], dict)
            ):
                raise HarvesterRunError(
                    "pending promotion result is ambiguous; exact staging row is missing or duplicated"
                ) from patch_error
            promoted = rows[0]
            if not matches_pending_row(promoted):
                raise HarvesterRunError(
                    "pending promotion result is ambiguous; persisted row does not match the approved payload"
                ) from patch_error

        if not matches_pending_row(promoted):
            raise HarvesterRunError(
                "pending promotion result does not match the exact pending row and payload"
            )
        if self.controlled and self.approved_lot is not None:
            self.approved_lot_scope_verified_for_write = True
        self._discovered_rows_by_url.pop(normalize_url(item["url"]), None)
        return promoted

    async def _load_existing_urls(self, pipeline_enabled=None):
        inst_id = self.institution.get('id')
        if pipeline_enabled is None:
            pipeline_enabled = self._gate_enabled('pipeline_enabled')
        self._resumable_urls = []
        self._discovered_rows_by_url = {}
        self._staging_rows_by_url = {}
        if self.controlled and self.approved_lot is not None:
            scope = getattr(self, "approved_lot_scope", None)
            if not isinstance(scope, dict) or not scope:
                raise HarvesterRunError("approved FG2 lot scope is empty")
            scope_urls = [
                normalize_url(scoped_url)
                for scoped_url in scope
                if isinstance(scoped_url, str)
            ]
            if (
                len(scope_urls) != len(scope)
                or any(not scoped_url for scoped_url in scope_urls)
                or len(set(scope_urls)) != len(scope_urls)
            ):
                raise HarvesterRunError("approved FG2 lot URL identity is ambiguous")
            existing = set()
            for normalized in sorted(scope_urls):
                rows = self._select_staging_rows_by_url(normalized)
                if len(rows) > 1:
                    raise HarvesterRunError("approved FG2 lot staging identity is ambiguous")
                if not rows:
                    continue
                row = rows[0]
                if not isinstance(row, dict):
                    raise HarvesterRunError("malformed approved FG2 staging identity")
                row_id = row.get("id")
                row_url = row.get("url")
                status = row.get("status")
                if not isinstance(row_id, str) or not row_id:
                    raise HarvesterRunError("malformed approved FG2 staging identity")
                if not isinstance(row_url, str) or normalize_url(row_url) != normalized:
                    raise HarvesterRunError("approved FG2 lot staging URL identity drifted")
                if status not in KNOWN_STAGING_STATUSES:
                    raise HarvesterRunError("unknown approved FG2 staging status")
                existing.add(normalized)
                self._staging_rows_by_url[normalized] = dict(row, url=normalized)
                if status == DISCOVERED_STATUS:
                    self._remember_discovered_row(row)
                elif status == "processed" and self.controlled:
                    course = self._course_for_refresh(normalized)
                    if course.get("kind") == "refresh_existing":
                        existing.discard(normalized)
                    else:
                        self._record_refresh_blocker(row)
            logger.info(
                "Loaded %s staging URLs from the reviewed FG2 lot scope.",
                len(existing),
            )
            self.visited_urls.update(existing)
            return existing
        if self.controlled and getattr(self, "scheduled_cohort", False):
            # The schedule resolves staging identity lazily for each discovered
            # URL. Historical rows outside this selected cohort must not block it.
            logger.info("Scheduled FG2 will resolve staging identity per selected URL.")
            return set()
        statuses = "discovered,pending,processing,processed,discarded,skipped,error"
        try:
            data = self.db.select_all_pipeline(
                "staging_raw",
                filters=(
                    f"institution_id=eq.{quote(str(inst_id), safe='')}"
                    f"&status=in.({statuses})"
                ),
                columns="id,url,status,content_hash",
                order="url.asc,id.asc",
            )
        except Exception as exc:
            raise HarvesterRunError("failed to load existing URLs from DB") from exc
        if not isinstance(data, list):
            raise HarvesterRunError("malformed existing URL payload")

        existing = set()
        for index, row in enumerate(data):
            if not isinstance(row, dict):
                raise HarvesterRunError(f"malformed existing URL row at {index}")
            row_id = row.get('id')
            url = row.get('url')
            status = row.get('status')
            if not isinstance(row_id, str) or not row_id:
                raise HarvesterRunError(f"malformed staging id at {index}")
            if not isinstance(url, str) or not url:
                raise HarvesterRunError(f"malformed staging URL at {index}")
            if status not in KNOWN_STAGING_STATUSES:
                raise HarvesterRunError(f"unknown staging status in URL inventory: {status}")
            normalized = normalize_url(url)
            if normalized in existing:
                raise HarvesterRunError(f"duplicate URL in staging inventory: {normalized}")
            existing.add(normalized)
            self._staging_rows_by_url[normalized] = dict(row, url=normalized)
            if status == DISCOVERED_STATUS:
                self._remember_discovered_row(row)
                if pipeline_enabled and not self.controlled:
                    self._resumable_urls.append(normalized)

        logger.info(
            "Loaded %s known staging URLs (%s resumable discovered, %s protected).",
            len(existing),
            len(self._resumable_urls),
            len(existing) - len(self._resumable_urls),
        )
        self.visited_urls.update(existing)
        return existing

    # ─────────────────────────────────────────────────────────
    # Fase 62B: Discovery Modes
    # ─────────────────────────────────────────────────────────

    async def discover_hardcoded_urls(self):
        discovery_mode = self.profile.get('discovery_mode', '')
        seed_urls = self.profile.get('seed_urls', [])
        if discovery_mode != 'hardcoded_urls' or not seed_urls:
            return None
        inst_id = self.institution.get('id')
        seen = set()
        clean_seeds = []
        for u in seed_urls:
            clean_u = normalize_url(u)
            if clean_u not in seen:
                seen.add(clean_u)
                clean_seeds.append(u)
        logger.info(f"[HARDCODED] Loaded {len(clean_seeds)} seed URLs for {_safe_institution_label(self.institution.get('name'))}")
        existing_urls = await self._load_existing_urls()
        new_urls = []
        for url in clean_seeds:
            if self.check_time_guard():
                break
            if not self._can_discover_more():
                break
            normalized = normalize_url(url)
            if not self._mark_controlled_url_examined(normalized):
                break
            if normalized not in existing_urls and self._is_valid_crawl_url(normalized):
                row = self._queue_discovered_candidate(normalized)
                if row["status"] == DISCOVERED_STATUS:
                    new_urls.append(normalized)
                    self.course_urls.add(normalized)
            elif self.controlled and normalized in existing_urls:
                existing = self._staging_rows_by_url.get(normalized, {})
                if existing.get("status") == DISCOVERED_STATUS:
                    self._save_discovered_url(normalized)
                    new_urls.append(normalized)
                    self.course_urls.add(normalized)
                else:
                    self._record_existing_staging_blocker(normalized)
        logger.info(f"Total Discovery (hardcoded): {len(new_urls)} NEW from {len(clean_seeds)} seeds.")
        return self._limit_urls(new_urls)

    async def discover_paginated_catalog(self, browser=None):
        """Discovery mode: iterate catalog_url_patterns with pagination (replaces PUCP harvester)."""
        catalog_patterns = self.profile.get('catalog_url_patterns', [])
        if not catalog_patterns:
            return None
        if self.controlled:
            catalog_urls = list(self.controlled_source_urls)
            if not catalog_urls:
                self.controlled_stop_reason = "InvalidControlledRun"
                logger.error("Controlled paginated catalog has no preflighted source pages.")
                return []
        else:
            catalog_urls = [
                pattern.replace('{page}', str(page_num))
                for pattern in catalog_patterns
                for page_num in range(1, self.catalog_max_pages + 1)
            ]
        logger.info(
            "📑 [PAGINATED CATALOG] Starting pagination discovery "
            f"({len(catalog_patterns)} patterns, {len(catalog_urls)} bounded source pages)"
        )
        existing_urls = await self._load_existing_urls()
        new_urls = []
        async with AsyncSession() as session:
            for page_num, url in enumerate(catalog_urls, start=1):
                if self.check_time_guard():
                    break
                if not self._can_discover_more():
                    break
                links = []
                if browser and self.site_type in ('spa_js_heavy', 'ecommerce'):
                    page = await self._new_browser_page(browser, request_kind="catalog_source")
                    try:
                        self._discovery_fetch_attempts += 1
                        page_response = await self._navigate_browser_page(
                            page,
                            url,
                            request_kind="catalog_source",
                            wait_until="domcontentloaded",
                            timeout=45000,
                        )
                        if not page_response or page_response.status != 200:
                            status = getattr(page_response, "status", None)
                            raise HarvesterPartialError(f"catalog page returned HTTP {status} for {_safe_url_label(url)}")
                        self._discovery_fetch_successes += 1
                        await asyncio.sleep(2)
                        if self.catalog_link_selector:
                            els = await page.query_selector_all(self.catalog_link_selector)
                            for el in els:
                                href = await el.get_attribute('href')
                                if href:
                                    links.append(urljoin(url, href))
                    except Exception as e:
                        logger.warning(f"Error loading catalog page {_safe_url_label(url)}: {type(e).__name__}")
                    finally:
                        await self._close_browser_page(page)
                else:
                    self._discovery_fetch_attempts += 1
                    try:
                        resp = await self._safe_request(
                            session,
                            url,
                            request_kind="catalog_source",
                        )
                    except (SourceBlocked, OriginDeferred, RunBudgetExceeded):
                        # Preserve already discovered staging rows for a later
                        # run, but stop this institution without downstream work.
                        return []
                    except SitemapBudgetYield:
                        return self._limit_urls(new_urls)
                    if not resp or resp.status_code != 200:
                        continue
                    self._discovery_fetch_successes += 1
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    if self.catalog_link_selector:
                        for a in soup.select(self.catalog_link_selector):
                            href = a.get('href')
                            if href:
                                links.append(urljoin(url, href))
                for link in links:
                    if not self._can_discover_more():
                        break
                    full_url = normalize_url(link)
                    if self._is_valid_crawl_url(full_url):
                        if not self._mark_controlled_url_examined(full_url):
                            break
                        if full_url in self.course_urls:
                            continue
                        if full_url in existing_urls:
                            if self.controlled:
                                existing = self._staging_rows_by_url.get(full_url, {})
                                if existing.get("status") == DISCOVERED_STATUS:
                                    self._save_discovered_url(full_url)
                                    new_urls.append(full_url)
                                    self.course_urls.add(full_url)
                                else:
                                    self._record_existing_staging_blocker(full_url)
                        else:
                            row = self._queue_discovered_candidate(full_url)
                            if row["status"] == DISCOVERED_STATUS:
                                new_urls.append(full_url)
                                self.course_urls.add(full_url)
                logger.debug(f"  Page {page_num}: {len(links)} links found")
        logger.info(f"Total Paginated Catalog: {len(new_urls)} NEW URLs")
        return self._limit_urls(new_urls)

    async def discover_catalog_links(self, browser):
        """Discovery mode: Playwright scroll + link extraction (replaces SmartData/New Horizons).
        Navigates through seed_urls (from profile) and fallback to website_url."""
        if not browser:
            logger.warning("Catalog link extraction requires Playwright browser")
            return None
        logger.info(f"[CATALOG LINKS] Starting scroll discovery for {_safe_institution_label(self.institution.get('name'))}")
        existing_urls = await self._load_existing_urls()
        new_urls = []
        if self.controlled:
            catalog_urls = list(self.controlled_source_urls)
        else:
            seed_urls = self.profile.get('seed_urls', []) if self.profile else []
            catalog_urls = list(seed_urls) if seed_urls else []
            fallback_url = self.institution.get('website_url')
            if fallback_url and fallback_url not in catalog_urls:
                catalog_urls.append(fallback_url)
        page = await self._new_browser_page(browser, request_kind="catalog_source")
        try:
            if self.requires_stealth and STEALTH_AVAILABLE:
                stealth_local = Stealth()
                await stealth_local.apply_stealth_async(page)
            for catalog_url in catalog_urls:
                if self.check_time_guard():
                    break
                if not self._can_discover_more():
                    break
                logger.info(f"  Navigating to catalog page: {_safe_url_label(catalog_url)}")
                self._discovery_fetch_attempts += 1
                page_response = await self._navigate_browser_page(
                    page,
                    catalog_url,
                    request_kind="catalog_source",
                    wait_until="domcontentloaded",
                    timeout=60000,
                )
                if not page_response or page_response.status != 200:
                    status = getattr(page_response, "status", None)
                    raise HarvesterPartialError(f"catalog page returned HTTP {status} for {_safe_url_label(catalog_url)}")
                self._discovery_fetch_successes += 1
                await self._dismiss_popups(page)
                for iteration in range(1, self.catalog_scroll_iterations + 1):
                    if self.check_time_guard():
                        break
                    scroll_y = 400 + iteration * 100
                    await page.evaluate(f'window.scrollBy(0, {scroll_y})')
                    await asyncio.sleep(2)
                    if self.catalog_link_selector:
                        els = await page.query_selector_all(self.catalog_link_selector)
                        for el in els:
                            if not self._can_discover_more():
                                break
                            href = await el.get_attribute('href')
                            if href:
                                full_url = normalize_url(urljoin(catalog_url, href))
                                if self._is_valid_crawl_url(full_url) and full_url not in existing_urls:
                                    row = self._queue_discovered_candidate(full_url)
                                    if row["status"] == DISCOVERED_STATUS:
                                        new_urls.append(full_url)
                                        self.course_urls.add(full_url)
                    if iteration % 5 == 0:
                        logger.info(f"  Scroll {iteration}/{self.catalog_scroll_iterations}: {len(new_urls)} new URLs so far")
                    has_footer = await page.evaluate('() => document.querySelector("footer") !== null && window.scrollY + window.innerHeight >= document.body.scrollHeight')
                    if has_footer:
                        logger.info("  Reached page bottom, stopping scroll")
                        break
        except Exception as e:
            logger.warning(f"Error during catalog scroll discovery: {_safe_error_label(e)}")
        finally:
            await self._close_browser_page(page)
        logger.info(f"Total Catalog Links: {len(new_urls)} NEW URLs")
        return self._limit_urls(new_urls)

    # ─────────────────────────────────────────────────────────
    # Fase 62A: Discovery routing
    # ─────────────────────────────────────────────────────────

    @staticmethod
    def _is_sitemap_seed_url(url):
        filename = urlsplit(str(url or "")).path.rsplit("/", 1)[-1].lower()
        return filename.endswith((".xml", ".xml.gz")) or filename.startswith("sitemap")

    @staticmethod
    def _is_compressed_sitemap_url(url):
        return urlsplit(str(url or "")).path.lower().endswith(".xml.gz")

    async def discover_courses(self, browser=None):
        start_url = self.institution.get('website_url')
        if not start_url: return []
        existing_urls = await self._load_existing_urls()
        discovery_mode = self.profile.get('discovery_mode', '')

        if self.controlled and discovery_mode == "sitemap_bfs":
            if self.approved_lot is not None and not getattr(self, "scheduled_cohort", False):
                # Manual lot seeds may be course pages or actual sitemap files.
                # Never send an HTML page to the XML parser; keep both paths
                # inside the exact reviewed seed set.
                sitemap_links = []
                if any(self._is_sitemap_seed_url(seed) for seed in self.controlled_seed_urls):
                    async with AsyncSession() as session:
                        for seed in self.controlled_seed_urls:
                            if (
                                self.check_time_guard()
                                or not self._can_discover_more()
                            ):
                                break
                            if self._is_sitemap_seed_url(seed):
                                if getattr(self, "sitemap_budget_reached", False):
                                    continue
                                sitemap_links.extend(await self._fetch_sitemap(session, seed))
                            else:
                                sitemap_links.append(seed)
                else:
                    sitemap_links = list(self.controlled_seed_urls)
            else:
                sitemap_links = []
                async with AsyncSession() as session:
                    for sitemap_seed in self.controlled_seed_urls:
                        if (
                            self.check_time_guard()
                            or self.controlled_stop_reason
                            or not self._can_discover_more()
                            or getattr(self, "sitemap_budget_reached", False)
                        ):
                            break
                        sitemap_links.extend(await self._fetch_sitemap(session, sitemap_seed))
            stop_reason = getattr(self, "controlled_stop_reason", None)
            if stop_reason and (
                not getattr(self, "scheduled_cohort", False)
                or stop_reason != "RunBudgetExceeded"
            ):
                # A blocked/deferred source ends this institution before any
                # partial links are queued. Scheduled mode preserves links
                # already read before its run budget is exhausted.
                return []
            for link in sitemap_links:
                if self.check_time_guard() or not self._can_discover_more():
                    break
                if not self._is_valid_crawl_url(link):
                    continue
                normalized = normalize_url(link)
                if normalized in existing_urls:
                    existing = self._staging_rows_by_url.get(normalized, {})
                    if existing.get("status") == DISCOVERED_STATUS:
                        if not self._mark_controlled_url_examined(normalized):
                            break
                        row = self._save_discovered_url(normalized)
                        if row["status"] == DISCOVERED_STATUS:
                            self.course_urls.add(normalized)
                    else:
                        self._record_existing_staging_blocker(normalized)
                    continue
                if not self._mark_controlled_url_examined(normalized):
                    break
                row = self._queue_discovered_candidate(normalized)
                if row["status"] == DISCOVERED_STATUS:
                    self.course_urls.add(normalized)
            return self._limit_urls(self._merge_resumable_urls(self.course_urls))

        if discovery_mode == 'hardcoded_urls':
            hardcoded_result = await self.discover_hardcoded_urls()
            if hardcoded_result is not None:
                return self._limit_urls(self._merge_resumable_urls(hardcoded_result))
        elif discovery_mode == 'paginated_catalog':
            cat_result = await self.discover_paginated_catalog(browser)
            if cat_result is not None:
                if self.controlled_stop_reason:
                    return []
                return self._limit_urls(self._merge_resumable_urls(cat_result))
        elif discovery_mode == 'catalog_link_extraction':
            cat_result = await self.discover_catalog_links(browser)
            if cat_result is not None:
                if self.controlled_stop_reason:
                    return []
                return self._limit_urls(self._merge_resumable_urls(cat_result))

        # sitemap_bfs (default)
        logger.info(f"Starting sitemap/BFS discovery for {_safe_institution_label(self.institution.get('name'))}")
        sitemap_url = urljoin(start_url, '/sitemap.xml')
        async with AsyncSession() as session:
            sitemap_links = await self._fetch_sitemap(session, sitemap_url)
        for link in sitemap_links:
            if self.check_time_guard(): break
            if not self._can_discover_more(): break
            if self._is_valid_crawl_url(link):
                normalized = normalize_url(link)
                if normalized in existing_urls:
                    existing = self._staging_rows_by_url.get(normalized, {})
                    if self.controlled and existing.get("status") == DISCOVERED_STATUS:
                        self._save_discovered_url(normalized)
                        self.course_urls.add(normalized)
                    else:
                        self._record_existing_staging_blocker(normalized)
                elif normalized not in self.course_urls:
                    row = self._queue_discovered_candidate(normalized)
                    if row["status"] == DISCOVERED_STATUS:
                        self.course_urls.add(normalized)
        if self.controlled:
            # Controlled mode never expands into an unbounded breadth-first crawl.
            pass
        elif len(self.course_urls) > 50:
            logger.info(f"🚀 [FAST PATH] Found {len(self.course_urls)} courses via Sitemap. Skipping slow BFS crawl.")
        elif not self.circuit_open:
            await self._bfs_crawl(start_url, existing_urls)
        selected_urls = list(self.course_urls) if self.controlled else [url for url in list(self.course_urls) if url not in existing_urls]
        final_urls = self._limit_urls(self._merge_resumable_urls(selected_urls))
        logger.info(f"Total Discovery: {len(final_urls)} NEW potential courses.")
        return final_urls

    # ─────────────────────────────────────────────────────────
    # Fase 62A+62D: Extraction with site_type routing and anti-bot
    # ─────────────────────────────────────────────────────────

    async def scrape_course_detail(self, session, page, url):
        """Playwright-based extraction for spa_js_heavy and ecommerce sites."""
        if self.circuit_open:
            raise HarvesterPartialError(f"circuit is open before scraping {_safe_url_label(url)}")
        logger.info(f"Scraping {_safe_url_label(url)}")
        try:
            response = await self._safe_request(session, url)
            if not response:
                raise HarvesterPartialError(f"request failed for {_safe_url_label(url)}")
            if response.status_code != 200:
                raise HarvesterPartialError(f"invalid HTTP status {response.status_code} for {_safe_url_label(url)}")
            if not self._is_html_response(response):
                raise HarvesterPartialError(f"non-HTML content for {_safe_url_label(url)}")
            eff_url = normalize_url(response.url)
            can_url = self._extract_canonical(response.text)
            if eff_url and not self._is_valid_crawl_url(eff_url):
                raise HarvesterPartialError(f"redirected to excluded URL: {_safe_url_label(eff_url)}")
            if can_url and not self._is_valid_crawl_url(can_url):
                raise HarvesterPartialError(f"canonical URL is excluded: {_safe_url_label(can_url)}")
            discovered_row = self._discovered_row_for_url(url)
            has_changed, _ = await self._check_if_changed(
                url,
                response.text[:200000],
                eff_url,
                can_url,
                force_changed=discovered_row["status"] == DISCOVERED_STATUS,
            )
            if not has_changed:
                logger.info(f"Skipping {_safe_url_label(url)} - No changes.")
                return None

            # Fase 62D: Anti-bot — Playwright page setup
            await self._navigate_browser_page(
                page,
                response.url,
                request_kind="detail",
                prefetched_response=response,
                wait_until="domcontentloaded",
                timeout=45000,
            )
            if self._browser_blocked_required_count:
                raise HarvesterPartialError("required browser resource was blocked by the FG2 request policy")
            await self._dismiss_popups(page)
            if self.requires_cf_bypass:
                await self._check_cloudflare_challenge(page)
            # Fase 62D: Profile-driven wait instead of hardcoded
            wait_sec = self.detail_wait_ms / 1000
            await asyncio.sleep(random.uniform(wait_sec * 0.5, wait_sec * 1.5))

            raw_html = (await page.content())[:200000]
            if not raw_html.strip():
                raise HarvesterPartialError(f"empty rendered HTML for {_safe_url_label(url)}")
            content_hash = self._generate_hash(raw_html)
            json_ld = await self._extract_json_ld(page)
            og_tags = await self._extract_og_tags(page)
            title = await self._extract_title(page, og_tags, json_ld)
            if not str(title or '').strip():
                raise HarvesterPartialError(f"empty raw_name for {_safe_url_label(url)}")
            description = await self._extract_description(page, og_tags, json_ld)

            # Fase 62C: Section keywords extraction from rendered HTML
            sections = self._extract_sections(raw_html)

            # Fase 94: WooCommerce structured data extraction
            woocommerce_price = None
            woocommerce_start_date = None
            woocommerce_category = None
            # Extract price from Product JSON-LD (now a dict of blocks with 'product' key)
            product_ld = json_ld.get('product', {}) if isinstance(json_ld, dict) else {}
            if product_ld:
                offers = product_ld.get('offers')
                if isinstance(offers, list) and len(offers) > 0:
                    offer = offers[0]
                    if isinstance(offer, dict):
                        ps = offer.get('priceSpecification')
                        if isinstance(ps, list) and len(ps) > 0 and isinstance(ps[0], dict):
                            woocommerce_price = ps[0].get('price')
                if not woocommerce_price:
                    woocommerce_price = product_ld.get('price')
            # Extract start_date from data-fecha-inicio attribute via Playwright
            try:
                woocommerce_start_date = await page.evaluate('() => document.querySelector("[data-fecha-inicio]")?.getAttribute("data-fecha-inicio") || null')
            except Exception:
                pass
            # Extract category: from raw_html (breadcrumb), second choice from URL
            # Check raw_html for WooCommerce product category
            cat_match = re.search(r'categoria-produto[^"]*[/]([^/]+)', raw_html[:10000])
            if cat_match:
                woocommerce_category = cat_match.group(1).rstrip('/')
            if not woocommerce_category:
                for seg in url.split('/'):
                    if seg in ('cursos', 'diplomas', 'especializaciones', 'certificaciones'):
                        woocommerce_category = seg
                        break

            return {
                "raw_name": title,
                "url": url,
                "effective_url": eff_url,
                "canonical_url": can_url,
                "raw_description": description,
                "raw_json_ld": json_ld,
                "raw_og_tags": og_tags,
                "raw_html": raw_html,
                "content_hash": content_hash,
                "institution_id": self.institution['id'],
                "status": "pending",
                "metadata": json.dumps(_mark_canary_metadata({
                    "extracted_sections": sections,
                    "field_defaults": self.field_defaults,
                    "woocommerce_price": woocommerce_price,
                    "woocommerce_start_date": woocommerce_start_date,
                    "woocommerce_category": woocommerce_category,
                })),
            }
        except DatabaseAPIError:
            raise
        except HarvesterRunError:
            raise
        except Exception as e:
            raise HarvesterPartialError(f"parser/browser error scraping {_safe_url_label(url)}: {_safe_error_label(e)}") from e

    async def _scrape_http(self, session, url):
        """Fase 62A: HTTP-only extraction for traditional_ssr sites (faster, no Playwright overhead)."""
        if self.circuit_open:
            raise HarvesterPartialError(f"circuit is open before scraping {_safe_url_label(url)}")
        logger.info(f"Scraping (HTTP) {_safe_url_label(url)}")
        try:
            response = await self._safe_request(session, url)
            if not response:
                raise HarvesterPartialError(f"request failed for {_safe_url_label(url)}")
            if response.status_code != 200:
                raise HarvesterPartialError(f"invalid HTTP status {response.status_code} for {_safe_url_label(url)}")
            if not self._is_html_response(response):
                raise HarvesterPartialError(f"non-HTML content for {_safe_url_label(url)}")
            eff_url = normalize_url(response.url)
            can_url = self._extract_canonical(response.text)
            if eff_url and not self._is_valid_crawl_url(eff_url):
                raise HarvesterPartialError(f"redirected to excluded URL: {_safe_url_label(eff_url)}")
            if can_url and not self._is_valid_crawl_url(can_url):
                raise HarvesterPartialError(f"canonical URL is excluded: {_safe_url_label(can_url)}")
            raw_html = response.text[:50000]
            if not raw_html.strip():
                raise HarvesterPartialError(f"empty HTML payload for {_safe_url_label(url)}")
            discovered_row = self._discovered_rows_by_url.get(normalize_url(url))
            has_changed, _ = await self._check_if_changed(
                url,
                raw_html,
                eff_url,
                can_url,
                force_changed=(
                    self.controlled
                    and self.approved_lot is not None
                    and discovered_row is None
                ) or bool(
                    discovered_row
                    and discovered_row.get("status") == DISCOVERED_STATUS
                ),
            )
            if not has_changed:
                logger.info(f"Skipping {_safe_url_label(url)} - No changes.")
                return None

            html = raw_html
            soup = BeautifulSoup(html, 'html.parser')

            # Extract JSON-LD
            json_ld = {}
            for script in soup.select('script[type="application/ld+json"]'):
                try:
                    json_ld = json.loads(script.string)
                    break
                except Exception:
                    continue

            # Extract OG tags
            og_tags = {}
            for meta in soup.select('meta[property^="og:"]'):
                og_tags[meta.get('property')] = meta.get('content')

            # Extract title
            title = og_tags.get('og:title') or (json_ld.get('name') if isinstance(json_ld, dict) else None) or ''
            if not title:
                title_tag = soup.find('title')
                if title_tag:
                    title = title_tag.string or ''
            title = title.strip()
            if not title:
                raise HarvesterPartialError(f"empty raw_name for {_safe_url_label(url)}")

            # Extract description
            desc = og_tags.get('og:description') or (json_ld.get('description') if isinstance(json_ld, dict) else None) or ''
            if not desc:
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                if meta_desc:
                    desc = meta_desc.get('content', '')

            # Fase 62C: Section keywords extraction
            sections = self._extract_sections(html)

            return {
                "raw_name": title,
                "url": url,
                "effective_url": eff_url,
                "canonical_url": can_url,
                "raw_description": desc,
                "raw_json_ld": json_ld,
                "raw_og_tags": og_tags,
                "raw_html": raw_html,
                "content_hash": self._generate_hash(raw_html),
                "institution_id": self.institution['id'],
                "status": "pending",
                "metadata": json.dumps(_mark_canary_metadata({"extracted_sections": sections, "field_defaults": self.field_defaults})),
            }
        except DatabaseAPIError:
            raise
        except HarvesterRunError:
            raise
        except Exception as e:
            raise HarvesterPartialError(f"parser error scraping {_safe_url_label(url)}: {_safe_error_label(e)}") from e

    # ─────────────────────────────────────────────────────────
    # Fase 62C: Section keywords extraction from headings
    # ─────────────────────────────────────────────────────────

    def _extract_sections(self, html: str) -> dict:
        """Scan H2/H3/H4 headings and map to profile section_keywords.

        Handles Bricks/Elementor nested structures: if no direct sibling content
        is found, falls back to searching for the next content block in the
        document after the heading.
        """
        if not self.section_keywords or not html:
            return {}
        soup = BeautifulSoup(html, 'html.parser')
        result = {}
        for heading in soup.find_all(['h2', 'h3', 'h4']):
            text = heading.get_text(strip=True)
            if not text:
                continue
            text_lower = text.lower()
            for keyword, field_name in self.section_keywords.items():
                if keyword.lower() in text_lower:
                    next_el = heading.find_next_sibling()
                    content_parts = []
                    while next_el and next_el.name not in ('h2', 'h3', 'h4'):
                        if next_el.name in ('p', 'ul', 'ol', 'div'):
                            content_parts.append(next_el.get_text(strip=True))
                        next_el = next_el.find_next_sibling()
                    # Fallback: if no sibling content, try parent container
                    if not content_parts:
                        parent = heading.find_parent(['div', 'section', 'article'])
                        if parent:
                            for sibling in parent.find_next_siblings():
                                txt = sibling.get_text(strip=True)
                                if txt and len(txt) > 20:
                                    content_parts.append(txt)
                                if content_parts:
                                    break
                    if not content_parts:
                        content_parts.append(heading.get_text(strip=True))
                    result[field_name] = ' '.join(content_parts)[:1000]
        return result

    # ─────────────────────────────────────────────────────────
    # Fase 62D: Anti-bot helpers
    # ─────────────────────────────────────────────────────────

    @staticmethod
    def _browser_response_headers(response):
        headers = getattr(response, "headers", {}) or {}
        allowed = {
            "content-type",
            "cache-control",
            "etag",
            "last-modified",
            "access-control-allow-origin",
            "access-control-allow-methods",
            "access-control-allow-headers",
            "access-control-max-age",
        }
        return {
            str(key).lower(): str(value)
            for key, value in headers.items()
            if str(key).lower() in allowed
        }

    async def _new_browser_page(self, browser, *, request_kind="detail"):
        """Create a page whose every network request crosses the FG2 budget."""
        context = await browser.new_context(
            user_agent=get_random_user_agent(),
            service_workers="block",
        )
        try:
            route_web_socket = getattr(context, "route_web_socket", None)
            if not callable(route_web_socket):
                raise HarvesterRunError("FG2 browser WebSocket guard is unavailable")

            async def block_websocket(websocket_route):
                self._browser_blocked_resource_count += 1
                self._browser_blocked_required_count += 1
                self.controlled_stop_reason = "BrowserWebSocketBlocked"
                self.circuit_open = True
                try:
                    await websocket_route.close(
                        code=1008,
                        reason="FG2 browser transport disabled",
                    )
                    logger.warning("FG2 browser WebSocket blocked by transport policy.")
                except Exception:
                    self.controlled_stop_reason = "BrowserTransportGuardFailed"
                    logger.error("FG2 browser WebSocket guard failed closed.")

            # HTTP routing does not mediate WebSocket. Install this before any
            # page exists so browser-created connections cannot bypass the
            # pinned HTTP client, request budget, or per-origin policy.
            await route_web_socket("**/*", block_websocket)
            await context.add_init_script(
                """(() => {
                    for (const name of [
                        "RTCPeerConnection",
                        "webkitRTCPeerConnection",
                        "WebTransport",
                    ]) {
                        const descriptor = Object.getOwnPropertyDescriptor(globalThis, name);
                        if (descriptor && descriptor.configurable === false && globalThis[name] !== undefined) {
                            throw new Error("unmediated browser transport cannot be disabled");
                        }
                        Object.defineProperty(globalThis, name, {
                            value: undefined,
                            configurable: false,
                            writable: false,
                        });
                    }
                    Object.defineProperty(globalThis, "__studiamatch_transport_guard__", {
                        value: true,
                        configurable: false,
                        writable: false,
                    });
                })();"""
            )
            page = await context.new_page()
            await page.goto("about:blank", wait_until="load", timeout=5000)
            transport_guard_ready = await page.evaluate(
                """() => window.__studiamatch_transport_guard__ === true
                    && window.RTCPeerConnection === undefined
                    && window.webkitRTCPeerConnection === undefined
                    && window.WebTransport === undefined"""
            )
            if not transport_guard_ready:
                raise HarvesterRunError("FG2 browser transport guard failed closed")

            page._fg2_navigation_kind = request_kind
            page._fg2_prefetched = {}
            await context.route(
                "**/*", lambda route: self._route_browser_request(page, route)
            )
            return page
        except Exception:
            await context.close()
            raise

    async def _close_browser_page(self, page):
        context = getattr(page, "context", None)
        if callable(context):
            context = context()
        if context is not None:
            await context.close()
        else:
            await page.close()

    async def _route_browser_request(self, page, route):
        request = route.request
        resource_type = str(getattr(request, "resource_type", "other") or "other").lower()
        try:
            request_page = request.frame.page
            if request_page != page:
                self._browser_blocked_resource_count += 1
                self._browser_blocked_required_count += 1
                await route.abort()
                return
            is_main_document = bool(
                request.is_navigation_request()
                and request.frame == page.main_frame
            )
        except Exception:
            is_main_document = False

        if is_main_document:
            kind = getattr(page, "_fg2_navigation_kind", self._browser_navigation_kind)
        else:
            kind = "subresource"
        if str(getattr(request, "method", "GET")).upper() != "GET":
            self._browser_blocked_resource_count += 1
            if resource_type in {"document", "script", "xhr", "fetch"}:
                self._browser_blocked_required_count += 1
            await route.abort()
            return

        url = str(getattr(request, "url", "") or "")
        try:
            validate_public_url_shape(url)
            if kind == "detail":
                rejection = profile_url_policy_rejection(
                    url,
                    str(self.institution.get("website_url") or ""),
                    self.profile,
                    approved_lot_scope=self.approved_lot_scope,
                    role="course_detail",
                    regex_module=safe_regex,
                )
                if rejection:
                    raise InvalidControlledRun("browser course URL rejected by shared policy")

            if kind == "subresource":
                response = await self._safe_request(
                    None,
                    url,
                    request_kind="subresource",
                )
            else:
                prefetched = getattr(page, "_fg2_prefetched", {})
                cache_key = normalize_url(url)
                response = prefetched.pop(cache_key, None)
                if response is None:
                    response = await self._safe_request(
                        None,
                        url,
                        request_kind=kind,
                    )
            if response is None:
                raise OriginDeferred("browser request was not completed through FG2 transport")

            body = getattr(response, "content", b"") or b""
            if not isinstance(body, bytes) or len(body) > CONTROLLED_RESPONSE_BODY_LIMIT_BYTES:
                raise ResponseBodyTooLarge("browser response exceeded the FG2 body limit")
            await route.fulfill(
                status=int(getattr(response, "status_code", 502) or 502),
                headers=self._browser_response_headers(response),
                body=body,
            )
        except (SourceBlocked, OriginDeferred, RunBudgetExceeded) as exc:
            self.controlled_stop_reason = type(exc).__name__
            self.circuit_open = True
            if resource_type in {"document", "script", "xhr", "fetch"}:
                self._browser_blocked_required_count += 1
            self._browser_blocked_resource_count += 1
            logger.warning("FG2 browser request stopped: %s", type(exc).__name__)
            await route.abort()
        except Exception as exc:
            if resource_type in {"document", "script", "xhr", "fetch"}:
                self._browser_blocked_required_count += 1
            self._browser_blocked_resource_count += 1
            logger.warning("FG2 browser request rejected: %s", type(exc).__name__)
            await route.abort()

    async def _navigate_browser_page(
        self,
        page,
        url,
        *,
        request_kind="detail",
        prefetched_response=None,
        **kwargs,
    ):
        """Navigate only through the route handler and per-institution budget."""
        validate_public_url_shape(url)
        if self.controlled and getattr(self, "request_budget", None) is None:
            raise HarvesterRunError(
                "controlled browser navigation is outside the request budget"
            )
        page._fg2_navigation_kind = request_kind
        self._browser_blocked_required_count = 0
        if prefetched_response is not None:
            final_url = getattr(prefetched_response, "url", None)
            if final_url:
                page._fg2_prefetched[normalize_url(final_url)] = prefetched_response
        return await page.goto(url, **kwargs)

    async def _warmup_browser(self, browser):
        """Warm up the browser with a homepage visit + mouse simulation for Cloudflare."""
        if not self.warmup_url:
            return
        logger.info(f"Warming up browser at {_safe_url_label(self.warmup_url)}")
        page = await self._new_browser_page(browser, request_kind="catalog_source")
        try:
            await self._navigate_browser_page(
                page, self.warmup_url, wait_until="domcontentloaded", timeout=60000
            )
            await page.mouse.move(random.randint(100, 500), random.randint(100, 500))
            await asyncio.sleep(2)
        except Exception as e:
            logger.warning(f"Warm-up page failed: {_safe_error_label(e)}")
        finally:
            await self._close_browser_page(page)

    async def _check_cloudflare_challenge(self, page):
        """Detect and wait for Cloudflare challenge to pass."""
        for attempt in range(12):
            title = await page.title()
            if "just a moment" not in title.lower():
                return True
            logger.info(f"Cloudflare challenge detected, waiting... (attempt {attempt + 1}/12)")
            await asyncio.sleep(10)
        logger.warning("Cloudflare challenge did not pass after 12 attempts (2 min)")
        return False

    async def _dismiss_popups(self, page):
        """Auto-dismiss popups using profile-driven selectors."""
        for selector in self.popup_selectors:
            try:
                if await page.is_visible(selector, timeout=2000):
                    await page.click(selector)
                    await asyncio.sleep(0.5)
                    logger.debug(f"Dismissed popup via selector: {selector}")
            except Exception:
                pass

    # ─────────────────────────────────────────────────────────
    # Extraction helpers
    # ─────────────────────────────────────────────────────────

    async def _extract_json_ld(self, page):
        scripts = await page.query_selector_all('script[type="application/ld+json"]')
        all_json = []
        for script in scripts:
            try:
                content = await script.inner_text()
                all_json.append(json.loads(content))
            except Exception:
                continue
        # Return dict with all blocks: 'product' (WooCommerce) and 'first' (Yoast fallback)
        result = {}
        for item in all_json:
            if isinstance(item, dict):
                if item.get('@type') == 'Product' or 'offers' in item:
                    result['product'] = item
                elif '@graph' in item:
                    result['seo'] = item
                    for node in item['@graph']:
                        if isinstance(node, dict) and node.get('@type') == 'Product':
                            result['product'] = node
                else:
                    result['first'] = item
        return result  # Returns dict with 'product' and/or 'seo' and/or 'first'

    async def _extract_og_tags(self, page):
        return await page.evaluate('''() => {
            const tags = {};
            document.querySelectorAll('meta[property^="og:"]').forEach(m => {
                tags[m.getAttribute('property')] = m.content;
            });
            return tags;
        }''')

    async def _extract_title(self, page, og, ld):
        # ld is a dict of blocks: {'product': ..., 'seo': ..., 'first': ...}
        ld_block = None
        if isinstance(ld, dict):
            ld_block = ld.get('seo') or ld.get('first') or ld.get('product')
        title = og.get('og:title') or (ld_block.get('name') if isinstance(ld_block, dict) else None)
        if not title:
            title = await page.title()
        return title

    async def _extract_description(self, page, og, ld):
        ld_block = None
        if isinstance(ld, dict):
            ld_block = ld.get('seo') or ld.get('first')
        desc = og.get('og:description') or (ld_block.get('description') if isinstance(ld_block, dict) else None)
        if not desc:
            desc = await page.evaluate('() => document.querySelector("meta[name=\'description\']")?.content || ""')
        return desc

    def _queue_discovered_candidate(self, url):
        normalized = normalize_url(url)
        if self.controlled and self.approved_lot is not None:
            if normalized not in (self.approved_lot_scope or {}):
                raise HarvesterRunError("discovered URL is outside the reviewed FG2 lot")
            if normalized not in self._staging_rows_by_url:
                # Do not persist a new candidate until its bounded detail body
                # has completed and passed HTML parsing.
                return {
                    "id": None,
                    "url": normalized,
                    "status": DISCOVERED_STATUS,
                    "kind": "new_discovery",
                    "course_id": None,
                }
        return self._save_discovered_url(normalized)

    def _save_discovered_url(self, url):
        normalized = normalize_url(url)
        if self.controlled and self.approved_lot is not None:
            if normalized not in self.approved_lot_scope:
                raise HarvesterRunError("discovered URL is outside the reviewed FG2 lot")
        staging_rows = self._select_staging_rows_by_url(normalized)
        course = self._course_for_refresh(normalized) if self.controlled else {}
        if self.controlled and self.approved_lot is not None:
            self._preflight_approved_scope_before_write(normalized, staging_rows, course)
        for row in staging_rows:
            owner = row.get("institution_id")
            status = row.get("status")
            if owner != self.institution.get('id'):
                raise HarvesterRunError(f"cross-institution URL collision for {normalized}")
            if status == DISCOVERED_STATUS:
                stored = {
                    "id": row["id"],
                    "url": normalized,
                    "expected_staging_url": row.get("url"),
                    "status": DISCOVERED_STATUS,
                    **course,
                }
                self._remember_discovered_row(stored)
                self._record_discovery_row(stored)
                return stored
            if status == "processed" and self.controlled and course.get("kind") == "refresh_existing":
                previous_hash = row.get("content_hash")
                if not isinstance(previous_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", previous_hash):
                    self._record_refresh_blocker(row)
                    return {"id": row["id"], "url": normalized, "status": status}
                stored = {
                    **row,
                    "url": normalized,
                    "expected_staging_url": row.get("url"),
                    "status": DISCOVERED_STATUS,
                    "original_status": "processed",
                    "previous_content_hash": previous_hash,
                    **course,
                }
                self._remember_discovered_row(stored)
                self._record_discovery_row(stored)
                return stored
            if status in PROTECTED_STAGING_STATUSES:
                if self.controlled:
                    self._record_refresh_blocker(row)
                return {"id": row["id"], "url": normalized, "status": status}
            raise HarvesterRunError(f"unknown staging status for {normalized}: {status}")

        discovered_data = {
            "url": normalized,
            "institution_id": self.institution['id'],
            "status": DISCOVERED_STATUS,
        }
        discovered_metadata = _mark_canary_metadata({})
        if discovered_metadata:
            discovered_data["metadata"] = json.dumps(discovered_metadata)
        inserted = self.db.insert("staging_raw", discovered_data)
        if inserted is None:
            raise HarvesterRunError(f"failed to insert discovered URL {normalized}")
        rows = self.db.select_pipeline_raise(
            "staging_raw",
            filters=(
                f"institution_id=eq.{quote(str(self.institution['id']), safe='')}"
                f"&url=eq.{quote(normalized, safe='')}"
                "&status=eq.discovered"
            ),
            columns="id,url,status",
            limit=2,
        )
        if len(rows) != 1:
            raise HarvesterRunError(f"failed to verify discovered URL {normalized}")
        if self.controlled and self.approved_lot is not None:
            self.approved_lot_scope_verified_for_write = True
        stored = {
            "id": rows[0]["id"],
            "url": normalize_url(rows[0]["url"]),
            "status": rows[0]["status"],
            **course,
        }
        self._remember_discovered_row(stored)
        self._record_discovery_row(stored)
        return stored

    def _save_to_staging(self, item):
        normalized_url = normalize_url(item.get("url") or "")
        row = self._discovered_rows_by_url.get(normalized_url)
        if row is None and self.controlled and self.approved_lot is not None:
            row = self._save_discovered_url(normalized_url)
        elif row is None:
            row = self._discovered_row_for_url(normalized_url)
        if self.controlled and not row.get("kind"):
            row.update(self._course_for_refresh(normalized_url))
        manifest_entry = None
        if self.controlled:
            manifest_url = item.get("url")
            if self.approved_lot is not None:
                approved_scope = self.approved_lot_scope.get(normalized_url)
                if approved_scope is None:
                    raise HarvesterRunError("URL is outside the reviewed FG2 lot")
                expected_staging = approved_scope["snapshot"]["staging_rows"]
                if expected_staging:
                    manifest_url = expected_staging[0].get("url")
            if not isinstance(manifest_url, str) or normalize_url(manifest_url) != normalized_url:
                raise HarvesterRunError("approved FG2 staging URL identity is missing or drifted")
            manifest_entry = {
                "institution_id": self.institution["id"],
                "staging_id": row["id"],
                "course_id": row.get("course_id"),
                "url_sha256": url_sha256(manifest_url),
                "cleansed_url_sha256": cleansed_url_sha256_for_record(
                    item["url"],
                    effective_url=item.get("effective_url"),
                    canonical_url=item.get("canonical_url"),
                ),
                "content_sha256": item["content_hash"],
                "kind": row.get("kind") or "new_discovery",
            }
        promoted = self._promote_discovered_to_pending(row, item)
        if manifest_entry is not None and promoted.get("status") == "pending":
            append_manifest_entry(self.cohort_manifest_path, manifest_entry)
        if promoted.get("status") == "processed":
            logger.info("Controlled refresh unchanged; processed staging row was not requeued.")
        else:
            logger.info(f"Harvested to Staging: {_safe_url_label(item['url'])}")
        return promoted


def _record_scheduled_attempt(db, institution, *, started_at, completed_at=None):
    completed_at = completed_at or datetime.now()
    institution_id = institution["id"]
    duration = max(0, int(completed_at.timestamp() - started_at))
    db.patch_exact_one_raise(
        "institutions",
        filters=f"id=eq.{quote(str(institution_id), safe='')}",
        data={
            "last_harvest_at": completed_at.isoformat(),
            "last_harvest_duration_sec": duration,
        },
        expected_id=institution_id,
    )


async def main(argv=None):
    import argparse
    import time

    parser = argparse.ArgumentParser()
    parser.add_argument("institution", help="JSON string of the institution")
    parser.add_argument("--global-start", type=float, help="Timestamp when the master orchestrator started")
    parser.add_argument("--max-urls", type=int, default=None, help="Maximum discovered URLs to harvest in this run")
    parser.add_argument("--controlled", action="store_true", help="Enable the approved first-run request/cohort limits")
    parser.add_argument("--scheduled-cohort", action="store_true", help="Enable the bounded main-schedule cohort")
    parser.add_argument("--cohort-manifest", help="Exact manifest path shared by the controlled run")
    parser.add_argument("--approved-lot-manifest", help="Private reviewed FG2 lot payload path")
    parser.add_argument("--approved-lot-reference", help="Human review reference bound to the FG2 lot")
    parser.add_argument("--approved-lot-sha256", help="SHA-256 of the reviewed FG2 lot bytes")
    args = parser.parse_args(argv)
    if args.controlled:
        os.environ["FG2_CONTROLLED_FIRST_RUN"] = "true"
    if args.scheduled_cohort:
        os.environ["FG2_COHORT_SCOPED"] = "true"
    try:
        cohort_mode = validate_harvester_run_mode(
            controlled=args.controlled,
            scheduled=args.scheduled_cohort,
            cohort_manifest=args.cohort_manifest,
            approved_lot_manifest=args.approved_lot_manifest,
            approved_lot_reference=args.approved_lot_reference,
            approved_lot_sha256=args.approved_lot_sha256,
            max_urls=args.max_urls,
            event_name=os.getenv("GITHUB_EVENT_NAME", ""),
            git_ref=os.getenv("GITHUB_REF", ""),
        )
    except InvalidControlledRun as exc:
        _emit_failure_for_exception("mode_validation", exc)
        logger.error("FG2 run mode rejected before database or source access: %s", _safe_error_label(exc))
        return 1
    cohort_scoped = cohort_mode != "ordinary"

    start_time = time.time()
    global_start = args.global_start or start_time
    MAX_RUN_TIME = 20400

    try:
        inst = json.loads(args.institution)
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        _emit_failure_for_exception("input_decode", exc)
        logger.error("FG2 institution input rejected before database or source access: %s", type(exc).__name__)
        return 1
    harvester = None
    browser = None
    pw = None
    phase = "harvester_initialization"

    try:
        harvester = UniversalHarvester(
            inst,
            global_start=global_start,
            max_discovered_urls=args.max_urls,
            controlled=cohort_scoped,
            cohort_manifest=args.cohort_manifest,
            approved_lot_manifest=args.approved_lot_manifest,
            approved_lot_reference=args.approved_lot_reference,
            approved_lot_sha256=args.approved_lot_sha256,
            require_approved_lot=args.controlled,
            scheduled_cohort=args.scheduled_cohort,
        )
        phase = "profile_gate"
        # Fase 75: Require profile
        if not harvester.profile:
            _emit_fg2_diagnostic("profile_gate", "profile_missing")
            logger.error(f"SKIP {_safe_institution_label(inst['name'])}: No existe entrada en institution_site_profiles. "
                         f"Crea un perfil antes de ejecutar el pipeline.")
            return 1
        if (
            harvester.profile.get("profile_status", "active") != "active"
            or harvester.profile.get("site_type") not in {"traditional_ssr", "spa_js_heavy", "ecommerce"}
            or harvester.profile.get("discovery_mode") not in {
                "sitemap_bfs", "hardcoded_urls", "paginated_catalog", "catalog_link_extraction"
            }
        ):
            _emit_fg2_diagnostic("profile_gate", "profile_missing")
            logger.error("FG2 profile is pending review or lacks an effective supported mode; harvester fails closed.")
            return 1
        if not harvester._gate_enabled('discovery_enabled'):
            logger.info(f"SKIP {_safe_institution_label(inst['name'])}: discovery_enabled=false.")
            return 0
        if harvester.circuit_open:
            _emit_fg2_diagnostic("profile_gate", "circuit_open")
            logger.error(f"Circuit is open for {_safe_institution_label(inst['name'])}; failing closed.")
            return 1
        pipeline_enabled = harvester._gate_enabled('pipeline_enabled')
        if not pipeline_enabled:
            logger.info(f"DISCOVERY-ONLY {_safe_institution_label(inst['name'])}: pipeline_enabled=false. "
                        f"Harvester will discover URLs into staging_raw for review. "
                        f"Cleansing/enrichment/sync will skip until pipeline_enabled=true.")

        # Fase 62A: Determine if Playwright is needed based on site_type and discovery_mode
        need_browser = (
            harvester.site_type in ('spa_js_heavy', 'ecommerce') or
            harvester.discovery_mode == 'catalog_link_extraction'
        )
        extraction_needs_browser = harvester.site_type in ('spa_js_heavy', 'ecommerce')

        if need_browser:
            phase = "browser_initialization"
            pw = await async_playwright().start()
            launch_kwargs = {"headless": True}
            if harvester.requires_stealth:
                launch_kwargs["slow_mo"] = 50
            browser = await pw.chromium.launch(**launch_kwargs)
            phase = "source_discovery"
            urls = await harvester.discover_courses(browser)
        else:
            phase = "source_discovery"
            urls = await harvester.discover_courses()

        if cohort_scoped and harvester.controlled_stop_reason:
            result = "blocked" if harvester.controlled_stop_reason == "SourceBlocked" else "deferred"
            snapshot = harvester.request_budget.snapshot()
            update_manifest_institution(
                args.cohort_manifest,
                institution_id=inst["id"],
                http_requests=snapshot["http_requests"],
                unique_urls=snapshot["unique_urls"],
                result=result,
            )
            if args.scheduled_cohort:
                _record_scheduled_attempt(
                    harvester.db,
                    inst,
                    started_at=start_time,
                )
            return 0
        if harvester.controlled_stop_reason:
            _emit_fg2_diagnostic("source_discovery", "source_request_error")
            logger.error("FG2 stopped the institution after a source or budget failure.")
            return 1

        if (
            pipeline_enabled
            and not urls
            and harvester._discovery_fetch_attempts > 0
            and harvester._discovery_fetch_successes == 0
        ):
            _emit_fg2_diagnostic("source_discovery", "discovery_unavailable")
            logger.error(f"FG2 discovery failed closed for {_safe_institution_label(inst['name'])}: all discovery fetches failed.")
            return 1

        if not pipeline_enabled:
            logger.info(f"DISCOVERY-ONLY complete for {_safe_institution_label(inst['name'])}: {len(urls)} URLs discovered; detail scraping skipped.")
            return 0

        failures = []
        promoted_count = 0
        phase = "course_detail"
        async with AsyncSession() as session:
            for i, url in enumerate(urls):
                phase = "course_detail"
                elapsed_total = time.time() - global_start
                if elapsed_total > MAX_RUN_TIME:
                    failures.append((url, "time guard reached"))
                    logger.warning(f"⚠️ [TIME GUARD] Límite de ejecución alcanzado ({elapsed_total/3600:.2f}h).")
                    break

                logger.info(f"Processing {i + 1}/{len(urls)}: {_safe_url_label(url)}")
                page = None
                try:
                    if extraction_needs_browser and browser:
                        page = await harvester._new_browser_page(
                            browser,
                            request_kind="detail",
                        )
                        if harvester.requires_stealth and STEALTH_AVAILABLE:
                            stealth = Stealth()
                            await stealth.apply_stealth_async(page)
                        item = await harvester.scrape_course_detail(session, page, url)
                    else:
                        item = await harvester._scrape_http(session, url)
                    if item:
                        item["status"] = "pending"
                        phase = "staging_write"
                        promoted = harvester._save_to_staging(item)
                        if promoted.get("status") == "pending":
                            promoted_count += 1
                except Exception as exc:
                    _emit_failure_for_exception(phase, exc)
                    failures.append((url, type(exc).__name__))
                    logger.error(f"Partial harvesting failure for {_safe_url_label(url)}: {type(exc).__name__}")
                    if harvester.controlled_stop_reason:
                        break
                finally:
                    if page:
                        await harvester._close_browser_page(page)

        if failures:
            if harvester.controlled_stop_reason and not cohort_scoped:
                logger.error("FG2 stopped this institution after a source or request-budget failure.")
                return 1
            if cohort_scoped and harvester.controlled_stop_reason:
                result = "blocked" if harvester.controlled_stop_reason == "SourceBlocked" else "deferred"
                snapshot = harvester.request_budget.snapshot()
                update_manifest_institution(
                    args.cohort_manifest,
                    institution_id=inst["id"],
                    http_requests=snapshot["http_requests"],
                    unique_urls=snapshot["unique_urls"],
                    result=result,
                )
                if args.scheduled_cohort:
                    _record_scheduled_attempt(
                        harvester.db,
                        inst,
                        started_at=start_time,
                    )
                return 0
            if cohort_scoped and promoted_count:
                snapshot = harvester.request_budget.snapshot()
                update_manifest_institution(
                    args.cohort_manifest,
                    institution_id=inst["id"],
                    http_requests=snapshot["http_requests"],
                    unique_urls=snapshot["unique_urls"],
                    result="partial",
                )
                if args.scheduled_cohort:
                    _record_scheduled_attempt(
                        harvester.db,
                        inst,
                        started_at=start_time,
                    )
                logger.warning(
                    "FG2 harvest partial for %s: successful manifest rows will continue downstream; failures=%s",
                    _safe_institution_label(inst["name"]),
                    len(failures),
                )
                return 0
            logger.error(f"FG2 finished PARTIAL/FAIL for {_safe_institution_label(inst['name'])}: {len(failures)} failures, {promoted_count} promoted.")
            return 1

        if cohort_scoped:
            snapshot = harvester.request_budget.snapshot()
            outcome = (
                "partial"
                if getattr(harvester, "sitemap_budget_reached", False)
                else "complete" if promoted_count else "no_op"
            )
            update_manifest_institution(
                args.cohort_manifest,
                institution_id=inst["id"],
                http_requests=snapshot["http_requests"],
                unique_urls=snapshot["unique_urls"],
                result=outcome,
            )
            if not promoted_count:
                if args.scheduled_cohort:
                    _record_scheduled_attempt(
                        harvester.db,
                        inst,
                        started_at=start_time,
                    )
                return 0

        phase = "telemetry"
        duration = int(time.time() - start_time)
        harvester.db.patch_exact_one_raise("institutions", filters=f"id=eq.{quote(str(inst['id']), safe='')}", data={
            "last_harvest_at": datetime.now().isoformat(),
            "last_harvest_duration_sec": duration
        }, expected_id=inst['id'])
        logger.info(f"Telemetry updated for {_safe_institution_label(inst['name'])}: {duration}s")
        return 0
    except Exception as exc:
        _emit_failure_for_exception(phase, exc)
        logger.error(f"FG2 failed closed for {_safe_institution_label(inst.get('name'))}: {type(exc).__name__}")
        if cohort_scoped and harvester and harvester.controlled_stop_reason:
            result = "blocked" if harvester.controlled_stop_reason == "SourceBlocked" else "deferred"
            snapshot = harvester.request_budget.snapshot()
            update_manifest_institution(
                args.cohort_manifest,
                institution_id=inst["id"],
                http_requests=snapshot["http_requests"],
                unique_urls=snapshot["unique_urls"],
                result=result,
            )
            if args.scheduled_cohort:
                _record_scheduled_attempt(
                    harvester.db,
                    inst,
                    started_at=start_time,
                )
            return 0
        return 1
    finally:
        if browser:
            try:
                await browser.close()
            except Exception as exc:
                _emit_failure_for_exception("shutdown", exc)
                raise
        if pw:
            try:
                await pw.stop()
            except Exception as exc:
                _emit_failure_for_exception("shutdown", exc)
                raise


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    sys.exit(asyncio.run(main()))
