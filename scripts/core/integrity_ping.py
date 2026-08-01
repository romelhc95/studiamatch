import os
import sys
import requests
import time
import logging
import ipaddress
import socket
from urllib.parse import urlparse
from datetime import datetime, timedelta
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.db_client import get_db_client
from shared.utils import setup_lima_logging, TimeGuard, parse_start_date

load_dotenv()
logger = setup_lima_logging("IntegrityPing")

HTTP_GONE_STATUSES = {404, 410}
HTTP_TRANSIENT_STATUSES = {408, 425, 429, 500, 502, 503, 504}


def is_safe_public_url(url):
    parsed = urlparse(str(url or '').strip())
    if parsed.scheme != 'https' or not parsed.netloc:
        return False
    host = parsed.hostname or ''
    if host in ('localhost',) or host.endswith('.localhost'):
        return False
    try:
        ip = ipaddress.ip_address(host)
        return not (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        )
    except ValueError:
        pass
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
        for info in socket.getaddrinfo(host, None):
            resolved = ipaddress.ip_address(info[4][0])
            if (
                resolved.is_private
                or resolved.is_loopback
                or resolved.is_link_local
                or resolved.is_multicast
                or resolved.is_reserved
                or resolved.is_unspecified
            ):
                return False
    except (OSError, ValueError):
        return False
    return True


def fetch_public_url(url, method='HEAD', max_redirects=5):
    current_url = url
    for _ in range(max_redirects + 1):
        if not is_safe_public_url(current_url):
            raise RuntimeError(f"unsafe URL target: {current_url}")
        request = requests.head if method == 'HEAD' else requests.get
        response = request(
            current_url,
            timeout=10,
            allow_redirects=False,
            stream=(method != 'HEAD'),
        )
        if response.is_redirect or response.is_permanent_redirect:
            location = response.headers.get('Location')
            if not location:
                return response
            from urllib.parse import urljoin
            current_url = urljoin(current_url, location)
            continue
        return response
    raise RuntimeError("too many redirects")


def patch_course_exact_one(db, course_id, data):
    existing = db.select_service_raise('courses', filters=f"id=eq.{course_id}", columns='id')
    if len(existing) != 1:
        raise RuntimeError(f"course patch target must match exactly one row: {course_id}")
    result = db.patch_raise('courses', filters=f"id=eq.{course_id}", data=data)
    if not result or result.get('status') != 'success':
        raise RuntimeError(f"course patch failed: {course_id}")

def run_integrity_ping():
    db = get_db_client()
    guard = TimeGuard(max_seconds=3600, logger=logger)
    logger.info("Iniciando Ping de Integridad Nivel 3...")

    res = db.count_service_raise('institutions')
    logger.info(f"[CHECK] Instituciones en DB: {res}")

    res = db.count_service_raise('courses')
    logger.info(f"[CHECK] Cursos en DB: {res}")

    res = db.select_service_raise(
        'courses',
        filters="is_active=eq.true&or=(syllabus.is.null,objectives.is.null)",
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
    expired = db.select_service_raise(
        'courses',
        filters=f"start_date=lt.{grace_cutoff}&is_active=eq.true",
        columns="id,name,start_date,start_date_text",
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

    courses = db.select_all_service(
        'courses',
        filters="is_active=eq.true",
        columns="id,name,url,last_404_at",
        batch_size=1000,
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
            if response.status_code == 405:
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
            elif 200 <= response.status_code < 400:
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
    sys.exit(run_integrity_ping())
