
import os
import requests
from dotenv import load_dotenv

load_dotenv('.env.local')

SUPABASE_URL = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
SUPABASE_KEY = os.getenv('NEXT_PUBLIC_SUPABASE_ANON_KEY')

def check_duplicates(query):
    url = f"{SUPABASE_URL}/rest/v1/courses?name=ilike.*{query}*&select=id,name,slug,institution_id,institutions(name,slug)"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        courses = response.json()
        print(f"Found {len(courses)} results for '{query}':")
        for c in courses:
            inst_name = c.get('institutions', {}).get('name', 'N/A')
            print(f"- ID: {c['id']} | Title: {c['name']} | Slug: {c['slug']} | Institution: {inst_name}")
    else:
        print(f"Error querying Supabase: {response.status_code} - {response.text}")

if __name__ == "__main__":
    check_duplicates("autocad")
