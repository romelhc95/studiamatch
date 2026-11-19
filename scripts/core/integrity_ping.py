import os
import sys
import requests
import time
import logging
import ipaddress
import socket
import ssl
from dataclasses import dataclass, field
from email.utils import parsedate_to_datetime
from http.client import HTTPSConnection
from urllib.parse import quote, urljoin, urlparse
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.db_client import (
    DatabaseAPIError,
    DatabaseWriteOutcomeUnknown,
    get_db_client,
)
from shared.utils import setup_lima_logging, TimeGuard

load_dotenv()
logger = setup_lima_logging("IntegrityPing")

HTTP_GONE_STATUSES = {404, 410}
HTTP_TRANSIENT_STATUSES = {408, 425, 429, 500, 502, 503, 504}
HTTP_GET_CONFIRMATION_STATUSES = {403, 404, 405, 410, 501}
HTTPS_PORT = 443
SOURCE_REMOVAL_GRACE = timedelta(days=3)
MAX_HTTP_ATTEMPTS_PER_URL = 3
HTTP_REQUEST_TIMEOUT_SECONDS = 10
MAX_REDIRECTS_PER_METHOD = 2
MAX_TOTAL_RETRY_DELAY_SECONDS = 30
MAX_URL_PROBE_SECONDS = 60

DIAGNOSTIC_PHASES = frozenset({
    "target_validation",
    "dns_resolution",
    "tcp_connect",
    "tls_handshake",
    "http_request",
    "redirect_validation",
    "retry_backoff",
    "time_budget",
    "response_classification",
    "transition_write",
})
DIAGNOSTIC_CATEGORIES = frozenset({
    "unsafe_target",
    "unsafe_dns_answer",
    "dns_no_answers",
    "dns_failure",
    "pinned_peer_mismatch",
    "tls_failure",
    "timeout",
    "transport_os_error",
    "unexpected_runtime_error",
    "unexpected_exception",
    "http_transient_status",
    "http_status_inconclusive",
    "exponential_backoff",
    "retry_after",
    "attempts_exhausted",
    "time_budget_exhausted",
    "retry_after_budget_exhausted",
    "retry_after_invalid",
    "redirect_limit",
    "database_write_outcome_unknown",
    "database_api_error",
})


class ProbeFailure(RuntimeError):
    """Internal failure with fixed, sanitized phase/category fields."""

    def __init__(self, phase, category, trace=None, retryable=False):
        self.phase = phase if phase in DIAGNOSTIC_PHASES else "http_request"
        self.category = category if category in DIAGNOSTIC_CATEGORIES else "unexpected_exception"
        self.trace = trace
        self.retryable = retryable
        super().__init__(f"{self.phase}:{self.category}")


@dataclass
class ProbeTrace:
    """One URL's bounded wire-request and retry accounting."""

    started_at: float = field(default_factory=time.monotonic)
    attempts: int = 0
    retry_delay_seconds: float = 0
    methods: list = field(default_factory=list)
    statuses: list = field(default_factory=list)
    diagnostics: list = field(default_factory=list)

    def add_diagnostic(self, phase, category):
        if phase not in DIAGNOSTIC_PHASES:
            phase = "http_request"
        if category not in DIAGNOSTIC_CATEGORIES:
            category = "unexpected_exception"
        self.diagnostics.append((phase, category))

    def elapsed_seconds(self):
        try:
            return time.monotonic() - self.started_at
        except RuntimeError:
            self.add_diagnostic("time_budget", "unexpected_runtime_error")
            raise ProbeFailure(
                "time_budget", "unexpected_runtime_error", self
            ) from None

    def check_time(self):
        if self.elapsed_seconds() >= MAX_URL_PROBE_SECONDS:
            self.add_diagnostic("time_budget", "time_budget_exhausted")
            raise ProbeFailure("time_budget", "time_budget_exhausted", self)

    def reserve_attempt(self, method):
        self.check_time()
        if self.attempts >= MAX_HTTP_ATTEMPTS_PER_URL:
            self.add_diagnostic("retry_backoff", "attempts_exhausted")
            raise ProbeFailure("retry_backoff", "attempts_exhausted", self)
        self.attempts += 1
        self.methods.append(method)

    def record_status(self, status_code):
        if isinstance(status_code, int) and 100 <= status_code <= 599:
            self.statuses.append(status_code)

    def wait_before_retry(self, delay_seconds, phase, category):
        if self.attempts >= MAX_HTTP_ATTEMPTS_PER_URL:
            self.add_diagnostic("retry_backoff", "attempts_exhausted")
            raise ProbeFailure("retry_backoff", "attempts_exhausted", self)
        if self.retry_delay_seconds + delay_seconds > MAX_TOTAL_RETRY_DELAY_SECONDS:
            failure = "retry_after_budget_exhausted" if category == "retry_after" else "time_budget_exhausted"
            self.add_diagnostic("retry_backoff", failure)
            raise ProbeFailure("retry_backoff", failure, self)
        if self.elapsed_seconds() + delay_seconds >= MAX_URL_PROBE_SECONDS:
            self.add_diagnostic("time_budget", "time_budget_exhausted")
            raise ProbeFailure("time_budget", "time_budget_exhausted", self)
        self.add_diagnostic(phase, category)
        self.retry_delay_seconds += delay_seconds
        try:
            time.sleep(delay_seconds)
        except RuntimeError:
            self.add_diagnostic("retry_backoff", "unexpected_runtime_error")
            raise ProbeFailure(
                "retry_backoff", "unexpected_runtime_error", self
            ) from None

    def safe_summary(self):
        methods = ",".join(method for method in self.methods if method in {"HEAD", "GET"}) or "none"
        statuses = ",".join(str(code) for code in self.statuses) or "none"
        diagnostics = ",".join(f"{phase}:{category}" for phase, category in self.diagnostics) or "none"
        return methods, statuses, diagnostics


def _retry_after_seconds(value):
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip()
    try:
        seconds = float(raw)
        return seconds if seconds >= 0 else None
    except ValueError:
        pass
    try:
        retry_at = parsedate_to_datetime(raw)
        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=timezone.utc)
        return max(0.0, (retry_at - datetime.now(timezone.utc)).total_seconds())
    except (TypeError, ValueError, OverflowError):
        return None


def _network_failure(exc, default_phase="http_request"):
    if isinstance(exc, socket.gaierror):
        return "dns_resolution", "dns_failure", True
    if isinstance(exc, ssl.SSLError):
        return "tls_handshake", "tls_failure", True
    if isinstance(exc, (socket.timeout, TimeoutError)):
        return default_phase, "timeout", True
    if isinstance(exc, OSError):
        return default_phase, "transport_os_error", True
    if isinstance(exc, RuntimeError):
        return default_phase, "unexpected_runtime_error", False
    return default_phase, "unexpected_exception", False


def _retry_delay(trace, response=None, fallback_category="exponential_backoff"):
    retry_after = None
    if response is not None:
        retry_after = _retry_after_seconds(response.headers.get("retry-after"))
        if response.headers.get("retry-after") and retry_after is None:
            trace.add_diagnostic("retry_backoff", "retry_after_invalid")
    if retry_after is not None:
        return retry_after, "retry_after"
    return float(2 ** max(0, trace.attempts - 1)), fallback_category


def _is_retryable_http_status(status_code, method):
    if status_code in HTTP_TRANSIENT_STATUSES:
        return True
    return 500 <= status_code < 600 and not (method == "HEAD" and status_code == 501)


def is_confirmed_source_removal(status_code, last_404_at, now=None):
    """Require a repeated 404/410 after the existing three-day grace period."""
    if status_code not in HTTP_GONE_STATUSES or not last_404_at:
        return False
    try:
        last_date = datetime.fromisoformat(str(last_404_at).replace('Z', '+00:00'))
    except (TypeError, ValueError):
        return False
    observed_at = now or datetime.now(last_date.tzinfo)
    if last_date.tzinfo is not None and observed_at.tzinfo is None:
        observed_at = observed_at.replace(tzinfo=last_date.tzinfo)
    if last_date.tzinfo is None and observed_at.tzinfo is not None:
        last_date = last_date.replace(tzinfo=observed_at.tzinfo)
    return observed_at > last_date + SOURCE_REMOVAL_GRACE


class FixedIPHTTPSConnection(HTTPSConnection):
    def __init__(self, host, fixed_ip, timeout=10, context=None):
        super().__init__(host, port=HTTPS_PORT, timeout=timeout, context=context)
        self.fixed_ip = fixed_ip

    def connect(self):
        try:
            raw_sock = socket.create_connection((self.fixed_ip, self.port), self.timeout)
        except Exception as exc:
            phase, category, retryable = _network_failure(exc, "tcp_connect")
            raise ProbeFailure(phase, category, retryable=retryable) from None
        try:
            try:
                peer_ip = ipaddress.ip_address(raw_sock.getpeername()[0])
                expected_ip = ipaddress.ip_address(self.fixed_ip)
            except Exception as exc:
                phase, category, retryable = _network_failure(exc, "tcp_connect")
                raise ProbeFailure(phase, category, retryable=retryable) from None
            if peer_ip != expected_ip:
                raise ProbeFailure("tls_handshake", "pinned_peer_mismatch")
            try:
                self.sock = self._context.wrap_socket(raw_sock, server_hostname=self.host)
            except Exception as exc:
                phase, category, retryable = _network_failure(exc, "tls_handshake")
                raise ProbeFailure(phase, category, retryable=retryable) from None
        except Exception:
            raw_sock.close()
            raise


class PinnedHTTPResponse:
    def __init__(self, status_code, headers, url, body=b''):
        self.status_code = status_code
        self.headers = {str(k).lower(): v for k, v in headers.items()}
        self.url = url
        self.content = body

    @property
    def is_redirect(self):
        return 300 <= self.status_code < 400 and bool(self.headers.get('location'))

    @property
    def is_permanent_redirect(self):
        return self.status_code in (301, 308) and bool(self.headers.get('location'))


def is_safe_public_ip(value):
    try:
        ip = ipaddress.ip_address(value)
    except ValueError:
        return False
    if getattr(ip, 'ipv4_mapped', None):
        ip = ip.ipv4_mapped
    return ip.is_global and not (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def resolve_public_host(host, budget=None):
    addresses = []
    try:
        address_info = socket.getaddrinfo(host, HTTPS_PORT, type=socket.SOCK_STREAM)
    except Exception as exc:
        phase, category, retryable = _network_failure(exc, "dns_resolution")
        raise ProbeFailure(phase, category, retryable=retryable) from None
    if budget is not None:
        budget.check_time()
    for info in address_info:
        resolved = info[4][0]
        if not is_safe_public_ip(resolved):
            raise ProbeFailure("dns_resolution", "unsafe_dns_answer")
        if resolved not in addresses:
            addresses.append(resolved)
    if not addresses:
        raise ProbeFailure("dns_resolution", "dns_no_answers")
    return addresses


def _is_syntactically_safe_public_url(url):
    """Validate the URL shape without an unbudgeted hostname lookup."""
    parsed = urlparse(str(url or '').strip())
    if (
        parsed.scheme != 'https'
        or not parsed.netloc
        or parsed.username is not None
        or parsed.password is not None
    ):
        return False
    try:
        port = parsed.port
    except ValueError:
        return False
    if port not in (None, HTTPS_PORT):
        return False
    host = parsed.hostname or ''
    if host in ('localhost',) or host.endswith('.localhost'):
        return False
    try:
        ipaddress.ip_address(host)
    except ValueError:
        return bool(host) and not any(ord(char) < 32 for char in host)
    else:
        return is_safe_public_ip(host)


def is_safe_public_url(url):
    """Return whether a URL resolves only to public HTTPS targets.

    SyncVectorWorker uses this before persisting a course URL, so hostname
    validation includes a public DNS resolution. The FG3 probe uses the
    syntax-only helper and performs its own budgeted DNS resolution/pinning
    immediately before each request.
    """
    if not _is_syntactically_safe_public_url(url):
        return False

    host = urlparse(str(url or '').strip()).hostname or ''
    try:
        ipaddress.ip_address(host)
    except ValueError:
        try:
            resolve_public_host(host)
        except ProbeFailure:
            return False
    return True


def request_pinned_public_url(url, method='HEAD', timeout=10, budget=None):
    parsed = urlparse(str(url or '').strip())
    if (
        parsed.scheme != 'https'
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
    ):
        raise ProbeFailure("target_validation", "unsafe_target")
    try:
        port = parsed.port
    except ValueError:
        raise ProbeFailure("target_validation", "unsafe_target") from None
    if port not in (None, HTTPS_PORT):
        raise ProbeFailure("target_validation", "unsafe_target")
    addresses = resolve_public_host(parsed.hostname, budget=budget)
    fixed_ip = addresses[0]
    try:
        context = ssl.create_default_context()
    except Exception as exc:
        phase, category, retryable = _network_failure(exc, "tls_handshake")
        raise ProbeFailure(phase, category, retryable=retryable) from None
    connection = FixedIPHTTPSConnection(
        parsed.hostname,
        fixed_ip=fixed_ip,
        timeout=timeout,
        context=context,
    )
    path = parsed.path or '/'
    if parsed.query:
        path = f"{path}?{parsed.query}"
    headers = {'Host': parsed.netloc, 'User-Agent': 'StudIAMatch-IntegrityPing/1.0'}
    try:
        connection.request(method, path, headers=headers)
        response = connection.getresponse()
        response_headers = {k.lower(): v for k, v in response.getheaders()}
        body = b'' if method == 'HEAD' else response.read(1024)
        return PinnedHTTPResponse(response.status, response_headers, url, body)
    finally:
        connection.close()


def fetch_public_url(url, method='HEAD', max_redirects=MAX_REDIRECTS_PER_METHOD, budget=None):
    trace = budget or ProbeTrace()
    method = method.upper()
    if method not in {"HEAD", "GET"}:
        trace.add_diagnostic("target_validation", "unsafe_target")
        raise ProbeFailure("target_validation", "unsafe_target", trace)
    current_url = url
    redirects = 0
    while True:
        if not _is_syntactically_safe_public_url(current_url):
            trace.add_diagnostic("redirect_validation", "unsafe_target")
            raise ProbeFailure("redirect_validation", "unsafe_target", trace)
        trace.reserve_attempt(method)
        try:
            response = request_pinned_public_url(
                current_url,
                method=method,
                timeout=HTTP_REQUEST_TIMEOUT_SECONDS,
                budget=trace,
            )
            trace.check_time()
        except ProbeFailure as failure:
            trace.add_diagnostic(failure.phase, failure.category)
            if failure.retryable:
                delay, delay_category = _retry_delay(trace)
                trace.wait_before_retry(delay, "retry_backoff", delay_category)
                continue
            raise ProbeFailure(failure.phase, failure.category, trace) from None
        except Exception as exc:
            phase, category, retryable = _network_failure(exc)
            trace.add_diagnostic(phase, category)
            if not retryable:
                raise ProbeFailure(phase, category, trace) from None
            delay, delay_category = _retry_delay(trace)
            trace.wait_before_retry(delay, "retry_backoff", delay_category)
            continue

        trace.record_status(response.status_code)
        if response.is_redirect or response.is_permanent_redirect:
            location = response.headers.get('location')
            if not location:
                return response
            redirects += 1
            if redirects > max_redirects:
                trace.add_diagnostic("redirect_validation", "redirect_limit")
                raise ProbeFailure("redirect_validation", "redirect_limit", trace)
            next_url = urljoin(current_url, location)
            if not _is_syntactically_safe_public_url(next_url):
                trace.add_diagnostic("redirect_validation", "unsafe_target")
                raise ProbeFailure("redirect_validation", "unsafe_target", trace)
            current_url = next_url
            continue
        if _is_retryable_http_status(response.status_code, method):
            trace.add_diagnostic("http_request", "http_transient_status")
            delay, delay_category = _retry_delay(trace, response)
            trace.wait_before_retry(delay, "retry_backoff", delay_category)
            continue
        return response


def probe_public_course(url):
    """Probe HEAD and, only for ambiguous/removal statuses, confirm with bounded GET."""
    try:
        trace = ProbeTrace()
    except RuntimeError:
        raise ProbeFailure("time_budget", "unexpected_runtime_error") from None
    response = fetch_public_url(url, method="HEAD", budget=trace)
    method = "HEAD"
    if response.status_code in HTTP_GET_CONFIRMATION_STATUSES:
        confirmation_url = getattr(response, "url", url)
        response = fetch_public_url(confirmation_url, method="GET", budget=trace)
        method = "GET"
    return response, method, trace


def load_selected_course_state(db, public_courses, batch_size=100):
    """Read mutable courses fields only for IDs selected by the public view."""
    selected_ids = list(dict.fromkeys(str(course['id']) for course in public_courses))
    snapshots = {}

    for offset in range(0, len(selected_ids), batch_size):
        batch = selected_ids[offset:offset + batch_size]
        encoded_ids = ','.join(quote(course_id, safe='') for course_id in batch)
        rows = db.select_service_raise(
            'courses',
            filters=f"id=in.({encoded_ids})",
            columns="id,institution_id,url,is_active,is_verified,last_404_at",
        )
        allowed_ids = set(batch)
        for row in rows:
            course_id = str(row.get('id'))
            if course_id not in allowed_ids or course_id in snapshots:
                raise RuntimeError("course snapshot returned an unexpected or duplicate id")
            snapshots[course_id] = row

    return snapshots


def apply_public_course_transition(db, course, http_status, action):
    """Atomically recheck public eligibility and update only an FG3-owned field."""
    response = db.rpc_once_raise(
        'fg3_apply_public_course_transition',
        {
            'p_course_id': course['id'],
            'p_institution_id': course['institution_id'],
            'p_url': course.get('url'),
            'p_observed_last_404_at': course.get('last_404_at'),
            'p_http_status': http_status,
            'p_action': action,
        },
    )
    if (
        not isinstance(response, list)
        or len(response) != 1
        or not isinstance(response[0], dict)
        or response[0].get('outcome') not in {'applied', 'stale', 'grace_pending'}
    ):
        raise DatabaseWriteOutcomeUnknown(
            "FG3 transition returned no single recognized result; do not retry"
        )
    outcome = response[0]['outcome']
    resulting_marker = response[0].get('resulting_last_404_at')
    resulting_active = response[0].get('resulting_is_active')
    if outcome == 'applied':
        expected_state_matches = (
            action == 'start_404_grace'
            and resulting_marker is not None
            and resulting_active is True
        ) or (
            action == 'clear_404_grace'
            and resulting_marker is None
            and resulting_active is True
        ) or (
            action == 'deactivate_after_grace'
            and resulting_marker is not None
            and resulting_active is False
        )
        if not expected_state_matches:
            raise DatabaseWriteOutcomeUnknown(
                "FG3 transition returned a state inconsistent with the action; do not retry"
            )
    if outcome == 'grace_pending' and action != 'deactivate_after_grace':
        raise DatabaseWriteOutcomeUnknown(
            "FG3 transition returned an invalid grace result; do not retry"
        )
    if outcome == 'grace_pending' and (resulting_marker is None or resulting_active is not True):
        raise DatabaseWriteOutcomeUnknown(
            "FG3 grace result returned an invalid course state; do not retry"
        )
    logger.info(
        "[FG3_TRANSITION] course_id=%s action=%s http_status=%s outcome=%s "
        "resulting_last_404_at=%s resulting_is_active=%s",
        course['id'],
        action,
        http_status,
        outcome,
        resulting_marker if resulting_marker is not None else "null",
        resulting_active if isinstance(resulting_active, bool) else "unknown",
    )
    return outcome


def _log_probe_trace(course_id, response, method, trace):
    methods, statuses, diagnostics = trace.safe_summary()
    logger.info(
        "[FG3_PROBE] course_id=%s outcome=response method=%s http_status=%s "
        "attempts=%s attempt_methods=%s response_statuses=%s retry_delay_seconds=%s diagnostics=%s",
        course_id,
        method,
        response.status_code,
        trace.attempts,
        methods,
        statuses,
        int(trace.retry_delay_seconds),
        diagnostics,
    )


def _log_probe_failure(course_id, phase, category, trace=None, http_status="unknown"):
    methods, statuses, diagnostics = trace.safe_summary() if trace else ("none", "none", "none")
    logger.warning(
        "[FG3_DIAGNOSTIC] course_id=%s phase=%s category=%s http_status=%s "
        "attempts=%s attempt_methods=%s response_statuses=%s retry_delay_seconds=%s history=%s",
        course_id,
        phase if phase in DIAGNOSTIC_PHASES else "http_request",
        category if category in DIAGNOSTIC_CATEGORIES else "unexpected_exception",
        http_status if isinstance(http_status, int) and 100 <= http_status <= 599 else "unknown",
        trace.attempts if trace else 0,
        methods,
        statuses,
        int(trace.retry_delay_seconds) if trace else 0,
        diagnostics,
    )


def _append_filter(base_filter, extra_filter):
    return f"{base_filter}&{extra_filter}" if base_filter else extra_filter


def run_integrity_ping(institution_id=None, limit=None):
    db = get_db_client()
    guard = TimeGuard(max_seconds=3600, logger=logger)
    logger.info("Iniciando Ping de Integridad Nivel 3...")

    institution_filter = ""
    if institution_id:
        institution_filter = f"institution_id=eq.{quote(str(institution_id), safe='')}"

    missing_filter = "or=(syllabus.is.null,objectives.is.null)"
    if institution_filter:
        missing_filter = _append_filter(missing_filter, institution_filter)

    missing = db.count_service_raise(
        'courses_public_effective',
        filters=missing_filter,
    )
    logger.info(f"[ALERT] Cursos públicos efectivos sin enriquecer: {missing}")

    failed = 0

    if missing > 50:
        logger.warning("[CRITICAL] Demasiados cursos sin metadatos. ¡Alerta Nivel 3!")
    else:
        logger.info("[OK] Integridad de datos dentro de umbrales.")

    partial = False

    course_filter = ""
    if institution_filter:
        course_filter = _append_filter(course_filter, institution_filter)
    active_limit = limit
    if active_limit == 0:
        courses = []
    elif active_limit is None:
        courses = db.select_all_service(
            'courses_public_effective',
            filters=course_filter,
            columns="id,institution_id,name,url",
            batch_size=1000,
            order="id.asc",
        )
    else:
        courses = db.select_service_raise(
            'courses_public_effective',
            filters=course_filter,
            columns="id,institution_id,name,url",
            limit=active_limit,
            order="id.asc",
        )

    base_snapshots = load_selected_course_state(db, courses)
    eligible_courses = []
    stale = 0
    for public_course in courses:
        snapshot = base_snapshots.get(str(public_course['id']))
        if (
            snapshot is None
            or snapshot.get('institution_id') != public_course.get('institution_id')
            or snapshot.get('url') != public_course.get('url')
            or snapshot.get('is_active') is not True
            or snapshot.get('is_verified') is not True
        ):
            stale += 1
            logger.info(
                f"[Stale selection] Saltando curso {public_course['id']} antes de consultar su URL"
            )
            continue
        eligible_courses.append({**public_course, 'last_404_at': snapshot.get('last_404_at')})

    courses = eligible_courses
    total = len(courses)
    deactivated = 0
    flagged = 0
    recovered = 0

    logger.info(f"Analizando {total} cursos...")

    for i, course in enumerate(courses):
        if guard.should_exit:
            logger.warning(f"⚠️ [TIME_GUARD] Shutdown durante integrity ping. Procesados: {i}/{total}")
            partial = True
            break

        course_id = course['id']
        course_url = course['url']
        trace = None
        response = None
        phase = "http_request"

        try:
            response, response_method, trace = probe_public_course(course_url)
            _log_probe_trace(course_id, response, response_method, trace)
            final_url = getattr(response, 'url', course_url)
            if not _is_syntactically_safe_public_url(final_url):
                trace.add_diagnostic("redirect_validation", "unsafe_target")
                raise ProbeFailure("redirect_validation", "unsafe_target", trace)

            phase = "response_classification"
            if response.status_code in HTTP_GONE_STATUSES:
                last_404 = course.get('last_404_at')

                if not last_404:
                    phase = "transition_write"
                    outcome = apply_public_course_transition(
                        db,
                        course,
                        response.status_code,
                        'start_404_grace',
                    )
                    if outcome == 'applied':
                        flagged += 1
                        logger.info(
                            "[FG3_RESULT] course_id=%s outcome=grace_started http_status=%s",
                            course_id,
                            response.status_code,
                        )
                    else:
                        stale += 1
                        logger.info(
                            "[FG3_RESULT] course_id=%s outcome=stale_transition action=start_404_grace",
                            course_id,
                        )
                elif not is_confirmed_source_removal(response.status_code, last_404):
                    flagged += 1
                    logger.info(
                        "[FG3_RESULT] course_id=%s outcome=grace_pending http_status=%s",
                        course_id,
                        response.status_code,
                    )
                else:
                    phase = "transition_write"
                    outcome = apply_public_course_transition(
                        db,
                        course,
                        response.status_code,
                        'deactivate_after_grace',
                    )
                    if outcome == 'applied':
                        deactivated += 1
                        logger.info(
                            "[FG3_RESULT] course_id=%s outcome=deactivated http_status=%s",
                            course_id,
                            response.status_code,
                        )
                    elif outcome == 'grace_pending':
                        flagged += 1
                        logger.info(
                            "[FG3_RESULT] course_id=%s outcome=grace_pending http_status=%s",
                            course_id,
                            response.status_code,
                        )
                    else:
                        stale += 1
                        logger.info(
                            "[FG3_RESULT] course_id=%s outcome=stale_transition action=deactivate_after_grace",
                            course_id,
                        )
            elif (
                response.status_code in HTTP_TRANSIENT_STATUSES
                or 500 <= response.status_code < 600
            ):
                failed += 1
                _log_probe_failure(
                    course_id,
                    "response_classification",
                    "http_transient_status",
                    trace,
                    response.status_code,
                )
            elif 200 <= response.status_code < 300:
                if course.get('last_404_at'):
                    phase = "transition_write"
                    outcome = apply_public_course_transition(
                        db,
                        course,
                        response.status_code,
                        'clear_404_grace',
                    )
                    if outcome == 'applied':
                        recovered += 1
                        logger.info(
                            "[FG3_RESULT] course_id=%s outcome=marker_cleared http_status=%s",
                            course_id,
                            response.status_code,
                        )
                    else:
                        stale += 1
                        logger.info(
                            "[FG3_RESULT] course_id=%s outcome=stale_transition action=clear_404_grace",
                            course_id,
                        )
            else:
                failed += 1
                _log_probe_failure(
                    course_id,
                    "response_classification",
                    "http_status_inconclusive",
                    trace,
                    response.status_code,
                )

        except ProbeFailure as exc:
            failed += 1
            failure_trace = exc.trace if isinstance(exc.trace, ProbeTrace) else trace
            _log_probe_failure(
                course_id,
                exc.phase,
                exc.category,
                failure_trace,
            )

        except DatabaseWriteOutcomeUnknown:
            failed += 1
            _log_probe_failure(
                course_id,
                "transition_write",
                "database_write_outcome_unknown",
                trace,
                response.status_code if response else "unknown",
            )
            partial = True
            break
        except DatabaseAPIError:
            failed += 1
            _log_probe_failure(
                course_id,
                "transition_write",
                "database_api_error",
                trace,
                response.status_code if response else "unknown",
            )
            partial = True
            break
        except RuntimeError:
            failed += 1
            _log_probe_failure(
                course_id,
                phase,
                "unexpected_runtime_error",
                trace,
                response.status_code if response else "unknown",
            )
            if phase == "transition_write":
                partial = True
                break
        except Exception:
            failed += 1
            _log_probe_failure(
                course_id,
                phase,
                "unexpected_exception",
                trace,
                response.status_code if response else "unknown",
            )

        guard.tick(every=100)

    logger.info(f"[DONE] Proceso completado.")
    logger.info(f"- Flagged (Nuevos 404): {flagged}")
    logger.info(f"- Desactivados: {deactivated}")
    logger.info(f"- Recuperados: {recovered}")
    logger.info(f"- Selecciones/observaciones obsoletas omitidas: {stale}")
    logger.info(f"- Fallidos/No concluyentes: {failed}")
    logger.info(f"- Tiempo: {guard.elapsed_hours:.2f}h")
    return 1 if failed or partial else 0

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run FG3 integrity ping")
    parser.add_argument("--institution-id", help="Optional exact institution UUID for a cohort-limited run")
    parser.add_argument("--limit", type=int, default=None, help="Maximum active courses to ping")
    args = parser.parse_args()
    sys.exit(run_integrity_ping(institution_id=args.institution_id, limit=args.limit))
