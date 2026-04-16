import os
import requests

# CLAVES PROPORCIONADAS (Simulación Cloudflare)
URL = "https://zogdcvlqxanzqbvkkdar.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpvZ2RjdmxxeGFuenFidmtrZGFyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYxODkzODUsImV4cCI6MjA5MTc2NTM4NX0.QtEkJZGmRZ5v_vEmnZNOxKTHuZGwzOU6MvoU08d1V6k"

def test_production_connection():
    print(f"--- SIMULACRO CLOUDFLARE ---")
    print(f"Probando URL: {URL}")
    
    headers = {
        "apikey": KEY,
        "Authorization": f"Bearer {KEY}"
    }
    
    try:
        # Intentamos obtener las instituciones (tabla pública con RLS para anon)
        response = requests.get(f"{URL}/rest/v1/institutions?select=name&limit=5", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ ¡ÉXITO! Conexión establecida con Producción.")
            print(f"Instituciones encontradas: {[i['name'] for i in data]}")
            return True
        else:
            print(f"❌ FALLO. Código de error: {response.status_code}")
            print(f"Respuesta del servidor: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR de red: {str(e)}")
        return False

if __name__ == "__main__":
    test_production_connection()
