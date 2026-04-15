import os
import requests
import asyncio
import logging
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

def check_course_url(url: str) -> bool:
    """
    Returns True if the course is STILL ALIVE (active).
    Returns False if it returns 404 or shows clear signs of being inactive.
    """
    try:
        # User-Agent to avoid generic blocks
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
        }
        res = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        
        if res.status_code == 404:
            return False
            
        # Example specific rule for New Horizons or generic closed terms:
        # (Could be expanded reading the DOM, but text search is lightweight and fast)
        text_lower = res.text.lower()
        if "inscripciones cerradas" in text_lower or "<title>404" in text_lower:
            return False
            
        return True
    except requests.RequestException as e:
        logger.warning(f"Connection error or timeout for {url}: {e}")
        # En caso de error de red (no 404 explícito), conservamos el status activo porsiacaso.
        return True

def run_ping():
    logger.info("Iniciando Lightweight Ping de Cursos Activos...")
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("Credenciales de Supabase no encontradas.")
        return
        
    # Obtener solo los cursos activos
    get_url = f"{SUPABASE_URL}/rest/v1/courses?is_active=eq.true&select=id,name,url"
    res = requests.get(get_url, headers=HEADERS)
    
    if res.status_code != 200:
        logger.error(f"Error fetcheando cursos: {res.text}")
        return
        
    courses = res.json()
    logger.info(f"Se encontraron {len(courses)} cursos activos. Procediendo a verificar URLs...")
    
    deactivated_count = 0
    
    for course in courses:
        url = course.get("url")
        course_id = course.get("id")
        name = course.get("name")
        
        if not url:
            continue
            
        is_alive = check_course_url(url)
        
        if not is_alive:
            logger.info(f"DEAD LINK DETECTADO: {name} ({url}). Marcando como inactivo...")
            # Soft-delete the course
            update_url = f"{SUPABASE_URL}/rest/v1/courses?id=eq.{course_id}"
            patch_res = requests.patch(update_url, headers=HEADERS, json={"is_active": False})
            
            if patch_res.status_code in [200, 204]:
                deactivated_count += 1
            else:
                logger.error(f"Fallo al desactivar {course_id}: {patch_res.text}")
    
    logger.info(f"Ping finalizado. Se desactivaron {deactivated_count} cursos obsoletos u offline.")

if __name__ == "__main__":
    run_ping()
