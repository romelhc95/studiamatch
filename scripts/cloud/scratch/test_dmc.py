import os
import sys
import json
import requests
import subprocess
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get('SUPABASE_URL') or os.environ.get('NEXT_PUBLIC_SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY') or os.environ.get('NEXT_PUBLIC_SUPABASE_ANON_KEY')

def get_dmc():
    url = f"{SUPABASE_URL}/rest/v1/institutions?select=id,name,slug,website_url&slug=eq.dmc"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    res = requests.get(url, headers=headers)
    if res.status_code == 200 and len(res.json()) > 0:
        return res.json()[0]
    return None

if __name__ == "__main__":
    dmc = get_dmc()
    if not dmc:
        print("Could not find DMC in standard institution fetch.")
        dmc = {
            "id": "e6f98011-8be8-42f0-beb7-0331f6e210ac", # Mock ID if missing
            "name": "Data Mining Consulting",
            "slug": "dmc",
            "website_url": "https://dmc.pe"
        }
    print(f"Testing Universal Harvester on DMC: {dmc['website_url']}")
    inst_json = json.dumps(dmc)
    
    # We will pass HARVESTER_MAX_URLS directly inside docker to limit the test
    cmd = [sys.executable, "scripts/core/universal_harvester.py", inst_json]
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, env=os.environ.copy())
    print(f"Done with exit code {result.returncode}")
