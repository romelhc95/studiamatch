import sys
import os
import uuid
from datetime import datetime

# Añadir el path raíz para importar shared
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.db_client import get_db_client

def test_db_client():
    print("--- INICIANDO TEST DE COMPATIBILIDAD DB ---")
    db = get_db_client()
    # Identificar modo por la presencia de conn (Postgres) o supabase_url (API)
    modo = "Postgres Local" if db.use_local else "Supabase API"
    print(f"Modo detectado: {modo}")

    # 1. Test Select Simple
    print("\n[TEST 1] Select Institutions (limit 1)...")
    insts = db.select('institutions', filters="limit=1")
    if insts:
        print(f"OK: Encontrada institución {insts[0].get('name')}")
    else:
        print("WARN: No se encontraron instituciones.")

    # 2. Test Count
    print("\n[TEST 2] Select Count Courses...")
    count = db.select('courses', columns="count")
    print(f"OK: Conteo de cursos: {count}")

    # 3. Test Complex Filter (is.null)
    print("\n[TEST 3] Select Courses with null objectives...")
    null_objs = db.select('courses', filters="objectives.is.null", limit=5)
    print(f"OK: Cursos con objetivos null: {len(null_objs)}")

    # 4. Test OR Filter (si el adaptador lo soporta)
    print("\n[TEST 4] Select with OR filter...")
    try:
        or_res = db.select('courses', filters="or=(syllabus.is.null,objectives.is.null)", limit=1)
        print(f"OK: Resultados con OR: {len(or_res)}")
    except Exception as e:
        print(f"FAIL/WARN: Error en OR filter: {e}")

    # 5. Test Insert/Delete (Transaction safety)
    print("\n[TEST 5] Insert and Delete test institution...")
    test_id = str(uuid.uuid4())
    try:
        db.insert('institutions', {
            "id": test_id,
            "name": "TEST-ADAPTER-DELETE-ME",
            "slug": f"test-slug-{test_id}",
            "website_url": "http://test.com"
        })
        print("OK: Inserción exitosa.")
        
        # Patch test
        db.patch('institutions', filters=f"id=eq.{test_id}", data={"name": "TEST-ADAPTER-PATCHED"})
        print("OK: Patch exitoso.")
        
        # Eliminarlo manualmente para limpiar (requiere delete en client si estuviera, 
        # pero db_client no tiene delete expuesto en la interfaz simplificada, 
        # solo select/insert/patch/upsert. Usaremos execute_sql si es local o lo dejaremos si es API)
        # Nota: PostgREST delete es DELETE request. DBClient no tiene .delete()
        if hasattr(db, 'conn'): # Es Postgres Local
            with db.conn.cursor() as cur:
                cur.execute("DELETE FROM institutions WHERE id = %s", (test_id,))
                db.conn.commit()
            print("OK: Limpieza post-test (Postgres) exitosa.")
        else:
            print("INFO: Limpieza en API Supabase requiere permiso DELETE (se omite).")
            
    except Exception as e:
        print(f"FAIL: Error en ciclo de vida datos: {e}")

    print("\n--- FIN DE TESTS ---")

if __name__ == "__main__":
    test_db_client()
