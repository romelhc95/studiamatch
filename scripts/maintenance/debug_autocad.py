import os
import requests
import json

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}"
}

ids = [
    "5bcd9bb5-c6de-409f-be03-5fdfa4120620",
    "2b566876-8f20-4681-aab8-9e11666bf394",
    "26a0d21a-875a-47cc-9037-22b2359319e4"
]

def fetch_duplicates():
    print("🔍 Fetching specific duplicates...")
    for id_ in ids:
        url = f"{SUPABASE_URL}/rest/v1/courses?id=eq.{id_}&select=*"
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            data = res.json()
            if data:
                print(f"ID: {id_}")
                print(json.dumps(data[0], indent=2))
                print("-" * 20)
            else:
                print(f"ID: {id_} (NOT FOUND)")
        else:
            print(f"ID: {id_} (ERROR {res.status_code})")

if __name__ == "__main__":
    fetch_duplicates()
