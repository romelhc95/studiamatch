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

from shared.db_client import get_db_client
from shared.utils import setup_lima_logging, TimeGuard, parse_start_date

load_dotenv()
logger = setup_lima_logging("IntegrityPing")

HTTP_GONE_STATUSES = {404, 410}
HTTP_TRANSIENT_STATUSES = {408, 425, 429, 500, 502, 503, 504}
HTTPS_PORT = 443


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


def patch_course_exact_one(db, course_id, data):
    result = db.patch_exact_one_raise(
        'courses',
        filters=f"id=eq.{quote(str(course_id), safe='')}",
        data=data,
        expected_id=course_id,
    )
    if not result:
        raise RuntimeError(f"course patch failed: {course_id}")

def _append_filter(base_filter, extra_filter):
    return f"{base_filter}&{extra_filter}" if base_filter else extra_filter


def run_integrity_ping(institution_id=None, limit=None):
    db = get_db_client()
    guard = TimeGuard(max_seconds=3600, logger=logger)
    logger.info("Iniciando Ping de Integridad Nivel 3...")

    res = db.count_service_raise('institutions')
    logger.info(f"[CHECK] Instituciones en DB: {res}")

    res = db.count_service_raise('courses')
    logger.info(f"[CHECK] Cursos en DB: {res}")

    institution_filter = ""
    if institution_id:
        institution_filter = f"institution_id=eq.{quote(str(institution_id), safe='')}"

    missing_filter = "is_active=eq.true&or=(syllabus.is.null,objectives.is.null)"
    if institution_filter:
        missing_filter = _append_filter(missing_filter, institution_filter)

    res = db.select_service_raise(
        'courses',
        filters=missing_filter,
    )
    missing = len(res)
    logger.info(f"[ALERT] Cursos sin enriquecer: {missing}")

    failed = 0

    if missing > 50:
        logger.warning("[CRITICAL] Demasiados cursos sin metadatos. ¡Alerta Nivel 3!")
    else:
        logger.info("[OK] Integridad de datos dentro de umbrales.")

    # Fase 73: Expiration check — desactivar cursos con start_date expirado (>90d)
    grace_cutoff = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    expired_filter = f"start_date=lt.{grace_cutoff}&is_active=eq.true"
    if institution_filter:
        expired_filter = _append_filter(expired_filter, institution_filter)
    if limit is None:
        expired = db.select_all_service(
            'courses',
            filters=expired_filter,
            columns="id,name,start_date,start_date_text",
            order="id.asc",
        )
    else:
        expired = db.select_service_raise(
            'courses',
            filters=expired_filter,
            columns="id,name,start_date,start_date_text",
            limit=limit,
            order="id.asc",
        )
    expired_count = len(expired)
    partial = False
    if expired_count > 0:
        logger.info(f"⏰ [EXPIRED] {expired_count} cursos con start_date < {grace_cutoff} (90d gracia)")
        for course in expired:
            if guard.should_exit:
                partial = True
                break
            logger.info(f"  Desactivando: {course.get('name')} (start_date={course.get('start_date')}, text={course.get('start_date_text')})")
            patch_course_exact_one(db, course['id'], {"is_active": False})
    else:
        logger.info("[OK] 0 cursos con fecha expirada")

    course_filter = "is_active=eq.true"
    if institution_filter:
        course_filter = _append_filter(course_filter, institution_filter)
    active_limit = None if limit is None else max(limit - expired_count, 0)
    if active_limit == 0:
        courses = []
    elif active_limit is None:
        courses = db.select_all_service(
            'courses',
            filters=course_filter,
            columns="id,name,url,last_404_at",
            batch_size=1000,
            order="id.asc",
        )
    else:
        courses = db.select_service_raise(
            'courses',
            filters=course_filter,
            columns="id,name,url,last_404_at",
            limit=active_limit,
            order="id.asc",
        )
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
                    patch_course_exact_one(db, course_id, {"last_404_at": datetime.now().isoformat()})
                    flagged += 1
                    logger.info(f"[Flagged] {course['name']} ({response.status_code} detectado)")
                else:
                    last_date = datetime.fromisoformat(last_404.replace('Z', '+00:00'))
                    if datetime.now(last_date.tzinfo) > last_date + timedelta(days=3):
                        patch_course_exact_one(db, course_id, {"is_active": False})
                        deactivated += 1
                        logger.info(f"[Deactivated] {course['name']} ({response.status_code} persistente > 3 días)")
            elif response.status_code in HTTP_TRANSIENT_STATUSES:
                failed += 1
                logger.warning(f"[Transient HTTP {response.status_code}] {course['name']}")
            elif 200 <= response.status_code < 300:
                if course.get('last_404_at'):
                    patch_course_exact_one(db, course_id, {"last_404_at": None})
                    recovered += 1
                    logger.info(f"[Recovered] {course['name']} (Vuelve a estar online)")
            else:
                failed += 1
                logger.warning(f"[Unhandled HTTP {response.status_code}] {course['name']}")

        except Exception as e:
            failed += 1
            logger.warning(f"[Timeout/Error] Saltando {course['name']} por error de conexión: {type(e).__name__}")

        guard.tick(every=100)

    logger.info(f"[DONE] Proceso completado.")
    logger.info(f"- Flagged (Nuevos 404): {flagged}")
    logger.info(f"- Desactivados: {deactivated}")
    logger.info(f"- Recuperados: {recovered}")
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
