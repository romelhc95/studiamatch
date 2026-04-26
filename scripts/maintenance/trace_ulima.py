import requests
import os
from dotenv import load_dotenv

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Prefer": "count=exact"
}
inst_id = "ccd04100-1bde-427b-b94f-ab24ae233a2a"

def get_count(endpoint, extra_filters=""):
    full_url = f"{url}/rest/v1/{endpoint}?institution_id=eq.{inst_id}{extra_filters}&select=count"
    res = requests.get(full_url, headers=headers)
    if res.status_code == 200:
        return res.json()[0]['count']
    return f"Error {res.status_code}"

print("--- Seguimiento de Datos: Universidad de Lima ---")
print(f"1. staging_raw (Total URLs): {get_count('staging_raw')}")
print(f"2. staging_raw (Pendientes Scrape): {get_count('staging_raw', '&status=eq.pending')}")
print(f"3. staging_raw (Descubiertas/Vacias): {get_count('staging_raw', '&status=eq.discovered')}")
print(f"4. cleansed_programs: {get_count('cleansed_programs')}")
print(f"5. courses (Total): {get_count('courses')}")
print(f"6. courses (Visibles: Active+Verified): {get_count('courses', '&is_active=eq.true&is_verified=eq.true')}")
print(f"7. courses (Borradores: Verified=False): {get_count('courses', '&is_verified=eq.false')}")
