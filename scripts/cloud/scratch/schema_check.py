import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
u = os.environ.get('NEXT_PUBLIC_SUPABASE_URL')
k = os.environ.get('NEXT_PUBLIC_SUPABASE_ANON_KEY')

r = requests.get(f'{u}/rest/v1/?apikey={k}')
schema = r.json()
staging_def = schema.get('definitions', {}).get('staging_raw', {})
print(json.dumps(staging_def, indent=2))
