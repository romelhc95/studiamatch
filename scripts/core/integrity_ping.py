import requests
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from shared.db_client import get_db_client

load_dotenv()

# Credentials and connection handled by db_client

def run_integrity_ping():
    db = get_db_client()
    print(f"[{datetime.now().isoformat()}] Iniciando Ping de Integridad Nivel 3...")
    
    # Check Institutions
    res = db.select('institutions', columns="count")
    print(f"[CHECK] Instituciones en DB: {res}")

    # Check Courses
    res = db.select('courses', columns="count")
    print(f"[CHECK] Cursos en DB: {res}")

    # Check Missing Metadata (Level 3 requirement)
    # Using the new OR filter support in db_client
    res = db.select('courses', filters="is_active=eq.true&or=(syllabus.is.null,objectives.is.null)")
    missing = len(res)
    print(f"[ALERT] Cursos sin enriquecer: {missing}")

    if missing > 50:
        print("[CRITICAL] Demasiados cursos sin metadatos. ¡Alerta Nivel 3!")
    else:
        print("[OK] Integridad de datos dentro de umbrales.")
        
    # 1. Obtener todos los cursos activos (con paginación para evitar límite 1000 de Supabase)
    courses = db.select_all('courses', filters="is_active=eq.true", columns="id,name,url,last_404_at", batch_size=1000)
    total = len(courses)
    deactivated = 0
    flagged = 0

    print(f"Analizando {total} cursos...")

    for course in courses:
        course_id = course['id']
        course_url = course['url']
        
        try:
            # Petición HEAD ligera para no saturar el servidor origen
            response = requests.head(course_url, timeout=10, allow_redirects=True)
            
            if response.status_code == 404:
                last_404 = course.get('last_404_at')
                
                if not last_404:
                    db.patch('courses', filters=f"id=eq.{course_id}", data={"last_404_at": datetime.now().isoformat()})
                    flagged += 1
                    print(f"[Flagged] {course['name']} (404 detectado)")
                else:
                    last_date = datetime.fromisoformat(last_404.replace('Z', '+00:00'))
                    if datetime.now(last_date.tzinfo) > last_date + timedelta(days=3):
                        db.patch('courses', filters=f"id=eq.{course_id}", data={"is_active": False})
                        deactivated += 1
                        print(f"[Deactivated] {course['name']} (404 persistente > 3 días)")
            else:
                if course.get('last_404_at'):
                    db.patch('courses', filters=f"id=eq.{course_id}", data={"last_404_at": None})
                    print(f"[Recovered] {course['name']} (Vuelve a estar online)")

        except Exception as e:
            print(f"[Timeout/Error] Saltando {course['name']} por error de conexión.")

    print(f"\n[DONE] Proceso completado.")
    print(f"- Flagged (Nuevos 404): {flagged}")
    print(f"- Desactivados: {deactivated}")

if __name__ == "__main__":
    run_integrity_ping()
