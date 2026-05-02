import os
import sys
import requests
import time
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.db_client import get_db_client
from shared.utils import setup_lima_logging, TimeGuard

load_dotenv()
logger = setup_lima_logging("IntegrityPing")

def run_integrity_ping():
    db = get_db_client()
    guard = TimeGuard(max_seconds=3600, logger=logger)
    logger.info("Iniciando Ping de Integridad Nivel 3...")

    res = db.select('institutions', columns="count")
    logger.info(f"[CHECK] Instituciones en DB: {res}")

    res = db.select('courses', columns="count")
    logger.info(f"[CHECK] Cursos en DB: {res}")

    res = db.select('courses', filters="is_active=eq.true&or=(syllabus.is.null,objectives.is.null)")
    missing = len(res)
    logger.info(f"[ALERT] Cursos sin enriquecer: {missing}")

    if missing > 50:
        logger.warning("[CRITICAL] Demasiados cursos sin metadatos. ¡Alerta Nivel 3!")
    else:
        logger.info("[OK] Integridad de datos dentro de umbrales.")

    courses = db.select_all('courses', filters="is_active=eq.true", columns="id,name,url,last_404_at", batch_size=1000)
    total = len(courses)
    deactivated = 0
    flagged = 0
    recovered = 0

    logger.info(f"Analizando {total} cursos...")

    for i, course in enumerate(courses):
        if guard.should_exit:
            logger.warning(f"⚠️ [TIME_GUARD] Shutdown durante integrity ping. Procesados: {i}/{total}")
            break

        course_id = course['id']
        course_url = course['url']

        try:
            response = requests.head(course_url, timeout=10, allow_redirects=True)

            if response.status_code == 404:
                last_404 = course.get('last_404_at')

                if not last_404:
                    db.patch('courses', filters=f"id=eq.{course_id}", data={"last_404_at": datetime.now().isoformat()})
                    flagged += 1
                    logger.info(f"[Flagged] {course['name']} (404 detectado)")
                else:
                    last_date = datetime.fromisoformat(last_404.replace('Z', '+00:00'))
                    if datetime.now(last_date.tzinfo) > last_date + timedelta(days=3):
                        db.patch('courses', filters=f"id=eq.{course_id}", data={"is_active": False})
                        deactivated += 1
                        logger.info(f"[Deactivated] {course['name']} (404 persistente > 3 días)")
            else:
                if course.get('last_404_at'):
                    db.patch('courses', filters=f"id=eq.{course_id}", data={"last_404_at": None})
                    recovered += 1
                    logger.info(f"[Recovered] {course['name']} (Vuelve a estar online)")

        except Exception as e:
            logger.debug(f"[Timeout/Error] Saltando {course['name']} por error de conexión.")

        guard.tick(every=100)

    logger.info(f"[DONE] Proceso completado.")
    logger.info(f"- Flagged (Nuevos 404): {flagged}")
    logger.info(f"- Desactivados: {deactivated}")
    logger.info(f"- Recuperados: {recovered}")
    logger.info(f"- Tiempo: {guard.elapsed_hours:.2f}h")

if __name__ == "__main__":
    run_integrity_ping()
