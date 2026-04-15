import os
import requests
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

def run_integrity_ping():
    print(f"[{datetime.now().isoformat()}] Iniciando Ping de Integridad Nivel 3...")
    
    # Check Institutions
    res = requests.get(f"{SUPABASE_URL}/rest/v1/institutions?select=count", headers=headers)
    print(f"[CHECK] Instituciones en DB: {res.json()}")

    # Check Courses
    res = requests.get(f"{SUPABASE_URL}/rest/v1/courses?select=count", headers=headers)
    print(f"[CHECK] Cursos en DB: {res.json()}")

    # Check Missing Metadata (Level 3 requirement)
    res = requests.get(f"{SUPABASE_URL}/rest/v1/courses?is_active=eq.true&or=(syllabus.is.null,objectives.is.null)", headers=headers)
    missing = len(res.json())
    print(f"[ALERT] Cursos sin enriquecer: {missing}")

    if missing > 50:
        print("[CRITICAL] Demasiados cursos sin metadatos. ¡Alerta Nivel 3!")
    else:
        print("[OK] Integridad de datos dentro de umbrales.")
        
    # 1. Obtener todos los cursos activos
    url = f"{SUPABASE_URL}/rest/v1/courses?is_active=eq.true&select=id,name,url,last_404_at"
    res = requests.get(url, headers=headers)
    
    if res.status_code != 200:
        print(f"[ERROR] Error al conectar con Supabase: {res.status_code}")
        return

    courses = res.json()
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
                    requests.patch(f"{SUPABASE_URL}/rest/v1/courses?id=eq.{course_id}", 
                                 headers=headers, 
                                 json={"last_404_at": datetime.now().isoformat()})
                    flagged += 1
                    print(f"[Flagged] {course['name']} (404 detectado)")
                else:
                    last_date = datetime.fromisoformat(last_404.replace('Z', '+00:00'))
                    if datetime.now(last_date.tzinfo) > last_date + timedelta(days=3):
                        requests.patch(f"{SUPABASE_URL}/rest/v1/courses?id=eq.{course_id}", 
                                     headers=headers, 
                                     json={"is_active": False})
                        deactivated += 1
                        print(f"[Deactivated] {course['name']} (404 persistente > 3 días)")
            else:
                if course.get('last_404_at'):
                    requests.patch(f"{SUPABASE_URL}/rest/v1/courses?id=eq.{course_id}", 
                                 headers=headers, 
                                 json={"last_404_at": None})
                    print(f"[Recovered] {course['name']} (Vuelve a estar online)")

        except Exception as e:
            print(f"[Timeout/Error] Saltando {course['name']} por error de conexión.")

    print(f"\n[DONE] Proceso completado.")
    print(f"- Flagged (Nuevos 404): {flagged}")
    print(f"- Desactivados: {deactivated}")

if __name__ == "__main__":
    run_integrity_ping()
