import os
import requests
import re
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("NEXT_SUPABASE_PUBLISHABLE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

def clean_slug_python(slug_or_url, url=None):
    if url:
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            path = parsed.path.strip('/')
            segments = path.split('/')
            last = segments[-1] if segments else ""
            if last and len(last) > 2:
                # Remove extension if any (.html, .php)
                last = re.sub(r'\.(html|php|aspx|asp)$', '', last)
                res = last.lower()
                res = re.sub(r'[^a-z0-9-]', '-', res)
                res = re.sub(r'-+', '-', res)
                return res.strip('-')
        except Exception:
            pass

    if not slug_or_url: return ""
    import unicodedata
    res = unicodedata.normalize('NFD', slug_or_url).encode('ascii', 'ignore').decode('utf-8').lower()
    res = re.sub(r'[^a-z0-9-]', '-', res)
    res = re.sub(r'-+', '-', res)
    return res.strip('-')

def audit_slugs():
    headers = {
        'apikey': SUPABASE_ANON_KEY,
        'Authorization': f'Bearer {SUPABASE_ANON_KEY}'
    }
    url = f"{SUPABASE_URL}/rest/v1/courses?select=id,name,slug,url,institutions(slug)"
    response = requests.get(url, headers=headers)
    courses = response.json()
    
    mismatches = []
    for c in courses:
        db_slug = c['slug']
        ui_slug = clean_slug_python(c['slug'], c['url'])
        
        if db_slug != ui_slug:
            mismatches.append({
                "name": c['name'],
                "db_slug": db_slug,
                "ui_slug": ui_slug,
                "institution": c['institutions']['slug'] if c['institutions'] else "unknown"
            })
            
    print(f"Total courses audited: {len(courses)}")
    print(f"Total mismatches found: {len(mismatches)}")
    
    if mismatches:
        print("\nTop 10 Mismatches:")
        for m in mismatches[:10]:
            print(f"- {m['name']} ({m['institution']})")
            print(f"  DB: {m['db_slug']} | UI: {m['ui_slug']}")
            
    return mismatches

if __name__ == "__main__":
    audit_slugs()
