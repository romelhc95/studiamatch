
import os
import requests
from dotenv import load_dotenv

load_dotenv('.env.local')

SUPABASE_URL = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
SUPABASE_KEY = os.getenv('NEXT_PUBLIC_SUPABASE_ANON_KEY')

def delete_duplicates(ids_to_delete):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    for course_id in ids_to_delete:
        url = f"{SUPABASE_URL}/rest/v1/courses?id=eq.{course_id}"
        response = requests.delete(url, headers=headers)
        if response.status_code in [200, 204]:
            print(f"Successfully deleted duplicate ID: {course_id}")
        else:
            print(f"Error deleting ID {course_id}: {response.status_code} - {response.text}")

if __name__ == "__main__":
    # IDs redundantes identificados:
    # 2b566876... (slug mal formado 'diseo')
    # 26a0d21a... (nombre incompleto 'Autocad')
    ids_to_clean = [
        "2b566876-8f20-4681-aab8-9e11666bf394",
        "26a0d21a-875a-47cc-9037-22b2359319e4"
    ]
    delete_duplicates(ids_to_clean)
