import os
import sys
import requests
import time
import logging
import ipaddress
import socket
import ssl
from http.client import HTTPSConnection
from urllib.parse import quote, urljoin, urlparse
from datetime import datetime, timedelta
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
HTTPS_PORT = 443
SOURCE_REMOVAL_GRACE = timedelta(days=3)


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
        raw_sock = socket.create_connection((self.fixed_ip, self.port), self.timeout)
        peer_ip = ipaddress.ip_address(raw_sock.getpeername()[0])
        expected_ip = ipaddress.ip_address(self.fixed_ip)
        if peer_ip != expected_ip:
            raw_sock.close()
            raise RuntimeError("connected peer does not match pinned DNS result")
        self.sock = self._context.wrap_socket(raw_sock, server_hostname=self.host)


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


def resolve_public_host(host):
    addresses = []
    for info in socket.getaddrinfo(host, HTTPS_PORT, type=socket.SOCK_STREAM):
        resolved = info[4][0]
        if not is_safe_public_ip(resolved):
            raise RuntimeError(f"unsafe resolved IP for {host}")
        if resolved not in addresses:
            addresses.append(resolved)
    if not addresses:
        raise RuntimeError(f"no DNS results for {host}")
    return addresses


def is_safe_public_url(url):
    parsed = urlparse(str(url or '').strip())
    if parsed.scheme != 'https' or not parsed.netloc:
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
        pass
    else:
        return is_safe_public_ip(host)
    if host.startswith(('127.', '10.', '192.168.', '169.254.')):
        return False
    if host.startswith('172.'):
        try:
            second_octet = int(host.split('.')[1])
            if 16 <= second_octet <= 31:
                return False
        except (IndexError, ValueError):
            pass
    try:
        resolve_public_host(host)
    except (OSError, RuntimeError, ValueError):
        return False
    return True


def request_pinned_public_url(url, method='HEAD', timeout=10):
    parsed = urlparse(str(url or '').strip())
    if parsed.scheme != 'https' or not parsed.hostname:
        raise RuntimeError(f"unsafe URL target: {url}")
    try:
        port = parsed.port
    except ValueError as exc:
        raise RuntimeError(f"unsupported HTTPS port: {url}") from exc
    if port not in (None, HTTPS_PORT):
        raise RuntimeError(f"unsupported HTTPS port: {url}")
    addresses = resolve_public_host(parsed.hostname)
    fixed_ip = addresses[0]
    context = ssl.create_default_context()
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


def fetch_public_url(url, method='HEAD', max_redirects=5):
    current_url = url
    for _ in range(max_redirects + 1):
        if not is_safe_public_url(current_url):
            raise RuntimeError(f"unsafe URL target: {current_url}")
        response = request_pinned_public_url(current_url, method=method, timeout=10)
        if response.is_redirect or response.is_permanent_redirect:
            location = response.headers.get('location')
            if not location:
                return response
            current_url = urljoin(current_url, location)
            continue
        return response
    raise RuntimeError("too many redirects")


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
    return outcome


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

        if not is_safe_public_url(course_url):
            failed += 1
            logger.warning(f"[Unsafe URL] Saltando {course['name']} ({course_url})")
            continue

        try:
            response = fetch_public_url(course_url, method='HEAD')
            if response.status_code in (405, 501):
                response = fetch_public_url(course_url, method='GET')
            final_url = getattr(response, 'url', course_url)
            if not is_safe_public_url(final_url):
                failed += 1
                logger.warning(f"[Unsafe Redirect] Saltando {course['name']} ({final_url})")
                continue

            if response.status_code in HTTP_GONE_STATUSES:
                last_404 = course.get('last_404_at')

                if not last_404:
                    outcome = apply_public_course_transition(
                        db,
                        course,
                        response.status_code,
                        'start_404_grace',
                    )
                    if outcome == 'applied':
                        flagged += 1
                        logger.info(f"[Flagged] {course['name']} ({response.status_code} observado; inicia la gracia de retirada)")
                    else:
                        stale += 1
                        logger.info(f"[Stale eligibility] Sin cambios para {course_id}; la elegibilidad o el estado cambió antes de la transacción FG3")
                elif not is_confirmed_source_removal(response.status_code, last_404):
                    flagged += 1
                    logger.info(f"[Pending] {course['name']} ({response.status_code} repetido antes de confirmar la gracia de retirada)")
                else:
                    outcome = apply_public_course_transition(
                        db,
                        course,
                        response.status_code,
                        'deactivate_after_grace',
                    )
                    if outcome == 'applied':
                        deactivated += 1
                        logger.info(f"[Deactivated] {course['name']} ({response.status_code} repetido tras la gracia de retirada)")
                    elif outcome == 'grace_pending':
                        flagged += 1
                        logger.info(f"[Pending] {course['name']} (la base de datos aún no confirma la gracia de retirada)")
                    else:
                        stale += 1
                        logger.info(f"[Stale eligibility] Sin cambios para {course_id}; la elegibilidad o el estado cambió antes de la transacción FG3")
            elif response.status_code in HTTP_TRANSIENT_STATUSES:
                failed += 1
                logger.warning(f"[Transient HTTP {response.status_code}] {course['name']}")
            elif 200 <= response.status_code < 300:
                if course.get('last_404_at'):
                    outcome = apply_public_course_transition(
                        db,
                        course,
                        response.status_code,
                        'clear_404_grace',
                    )
                    if outcome == 'applied':
                        recovered += 1
                        logger.info(f"[Recovered] {course['name']} (Vuelve a estar online)")
                    else:
                        stale += 1
                        logger.info(f"[Stale eligibility] Sin cambios para {course_id}; la elegibilidad o el estado cambió antes de la transacción FG3")
            else:
                failed += 1
                logger.warning(f"[Unhandled HTTP {response.status_code}] {course['name']}")

        except DatabaseWriteOutcomeUnknown as e:
            failed += 1
            logger.error(
                f"[Write outcome unknown] Deteniendo FG3 en {course_id}; "
                f"sin reintento y sin continuar el lote: {type(e).__name__}"
            )
            partial = True
            break
        except DatabaseAPIError as e:
            failed += 1
            logger.error(
                f"[Write rejected] Deteniendo FG3 en {course_id}; "
                f"no se continúa el lote: {type(e).__name__}"
            )
            partial = True
            break
        except Exception as e:
            failed += 1
            logger.warning(f"[Timeout/Error] Saltando {course['name']} por error de conexión: {type(e).__name__}")

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
