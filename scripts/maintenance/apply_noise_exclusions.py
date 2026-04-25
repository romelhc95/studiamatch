import requests
import os
from dotenv import load_dotenv

url = "https://fmcxwoqvxatbrawwtqke.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZtY3h3b3F2eGF0YnJhd3d0cWtlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ3MjE5MjcsImV4cCI6MjA5MDI5NzkyN30.yHThxpyDnVEgZ3dpI5WD4qBgIJE7PHITuJYeapLSVi8"
headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

ulima_id = "ccd04100-1bde-427b-b94f-ab24ae233a2a"

# Patrones aprobados (Solo ruido técnico/genérico)
noise_patterns = [
    "/blog-tags/", "/ventana-indiscreta/", "/node/", 
    "/promociones/", "/taxonomy/", "/la-universidad/", 
    "/centros-e-institutos/"
]

print("--- 1. Inyectando Exclusiones Aprobadas ---")
for pat in noise_patterns:
    res = requests.post(f"{url}/rest/v1/crawler_exclusions", headers=headers, json={
        "institution_id": ulima_id,
        "pattern": pat,
        "reason": "Ruido detectado por AI-Sentinel Fase 50 (Aprobado)"
    })
    if res.status_code in [200, 201]:
        print(f"✅ Exclusión registrada: {pat}")

print("\n--- 2. Limpiando cola de Staging (Retroactivo) ---")
total_cleaned = 0
for pat in noise_patterns:
    # Eliminamos de staging_raw para que el robot no los visite
    clean_p = pat.replace("/", "")
    res = requests.delete(f"{url}/rest/v1/staging_raw?institution_id=eq.{ulima_id}&url=ilike.*{clean_p}*", headers=headers)
    if res.status_code in [200, 204]:
        count = len(res.json()) if res.content else 0
        total_cleaned += count

print(f"🗑️ Se eliminaron {total_cleaned} registros de ruido de la cola actual.")
print("\n✅ Saneamiento completado. El robot ahora tiene una ruta despejada.")
