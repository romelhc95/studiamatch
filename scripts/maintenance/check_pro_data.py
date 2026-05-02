#!/usr/bin/env python3
"""Check data in Pro database from yesterday's harvest using urllib."""
import json
import urllib.request
import os
import sys

PRO_URL = os.environ.get("SUPABASE_PRO_URL", "")
SECRET_KEY = os.environ.get("SUPABASE_PRO_SECRET_KEY", "")
if not PRO_URL or not SECRET_KEY:
    print("ERROR: Set SUPABASE_PRO_URL and SUPABASE_PRO_SECRET_KEY environment variables")
    sys.exit(1)

def req(path):
    url = f"{PRO_URL}/rest/v1/{path}"
    h = {
        "apikey": SECRET_KEY,
        "Authorization": f"Bearer {SECRET_KEY}",
        "Prefer": "count=exact",
        "Accept": "application/json"
    }
    r = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(r) as resp:
        count = resp.headers.get("Content-Range", "0-0/0").split("/")[-1]
        data = json.loads(resp.read().decode())
        return data, count

tables = ["staging_raw", "cleansed_programs", "enriched_programs", "courses"]
for table in tables:
    try:
        data, count = req(f"{table}?select=count&limit=0")
        print(f"{table}: {count} registros")
    except Exception as e:
        print(f"{table}: ERROR - {e}")

print()
print("--- staging_raw por status ---")
try:
    data, count = req("staging_raw?select=status,url&limit=1000")
    counts = {}
    for d in data:
        s = d.get("status", "unknown")
        counts[s] = counts.get(s, 0) + 1
    for s, c in counts.items():
        print(f"  {s}: {c}")
    print(f"  Total: {len(data)}")
    if data:
        print(f"  Muestra: {data[0]['url'][:80]}")
except Exception as e:
    print(f"  ERROR: {e}")

print()
print("--- institutions ---")
try:
    data, count = req("institutions?select=id,name,slug")
    for inst in data:
        print(f"  {inst['name']} ({inst['slug']})")
except Exception as e:
    print(f"  ERROR: {e}")
