import os
import requests

# CLAVES PROPORCIONADAS (Simulación Cloudflare)
URL = "https://zogdcvlqxanzqbvkkdar.supabase.co"
KEY = "REMOVED_HISTORICAL_CREDENTIAL_004"

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
