import os
import requests
import json
import math
import sys
from dotenv import load_dotenv

load_dotenv()

# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_SERVICE_ROLE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
HARVESTERS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "harvesters")

def get_active_institutions():
    """
    Fetches active institutions from Supabase.
    If no 'is_active' column exists, fetches all as active.
    """
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    # Try filtering by status if it's there (based on schema guide but not seen in live keys)
    # We use a broad select to see what we get. 
    # Actually, let's just fetch everything and handle it.
    url = f"{SUPABASE_URL}/rest/v1/institutions?select=*"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        institutions = response.json()
        
        # Simple heuristic: if we have a way to filter active ones, we do it.
        # For now, we take all that have a website_url.
        active_inst = [inst for inst in institutions if inst.get('website_url')]
        
        # Add harvester info
        for inst in active_inst:
            slug = inst.get('slug')
            harvester_file = f"{slug}_harvester.py"
            harvester_path = os.path.join(HARVESTERS_DIR, harvester_file)
            
            if os.path.exists(harvester_path):
                inst['harvester_type'] = 'dedicated'
                inst['harvester_script'] = f"scripts/harvesters/{harvester_file}"
            else:
                inst['harvester_type'] = 'universal'
                inst['harvester_script'] = "scripts/core/universal_harvester.py"
                
        return active_inst
    except Exception as e:
        print(f"Error fetching institutions: {e}", file=sys.stderr)
        return []

def split_into_groups(institutions, n):
    """
    Divides the list of institutions into N groups for parallel processing.
    """
    if not institutions:
        return [[] for _ in range(n)]
    
    # If N is larger than the number of institutions, some groups will be empty
    if n > len(institutions):
        n = len(institutions)
        
    avg = len(institutions) / n
    groups = []
    last = 0.0

    while last < len(institutions):
        groups.append(institutions[int(last):int(last + avg)])
        last += avg

    # Ensure we return exactly N groups (if possible)
    while len(groups) < n:
        groups.append([])
        
    return groups

def main():
    # Number of workers and limit (parsed from arguments)
    n_workers = 1
    limit = 999
    
    for i, arg in enumerate(sys.argv):
        if arg == "--limit" and i + 1 < len(sys.argv):
            try:
                limit = int(sys.argv[i+1])
            except ValueError: pass
        elif i == 1 and not arg.startswith("-"):
            try:
                n_workers = int(arg)
            except ValueError: pass

    print(f"Orchestrating for {n_workers} workers (Limit: {limit})...")
    
    institutions = get_active_institutions()
    if limit < len(institutions):
        institutions = institutions[:limit]
        
    print(f"Processing {len(institutions)} active institutions.")
    
    groups = split_into_groups(institutions, n_workers)
    
    output = {
        "total_institutions": len(institutions),
        "num_workers": n_workers,
        "worker_assignments": []
    }
    
    for i, group in enumerate(groups):
        assignment = {
            "worker_id": i + 1,
            "tasks": group
        }
        output["worker_assignments"].append(assignment)
    
    # Generate JSON output
    output_file = "orchestration_plan.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
        
    print(f"Orchestration plan saved to {output_file}")
    
    # --- ejecución ---
    print("\nStarting task execution...")
    import subprocess
    
    for task in institutions:
        script = task.get('harvester_script')
        name = task.get('name')
        print(f"[PROCESS] Running harvester for: {name} ({script})")
        
        # Preparamos los argumentos
        cmd = ["python", script]
        
        # El Universal Harvester NECESITA el JSON de la institución como argumento
        if "universal_harvester.py" in script:
            cmd.append(json.dumps(task))
            
        # Pasamos variables de entorno necesarias al subproceso
        env = os.environ.copy()
        
        try:
            # Ejecutamos con un límite de tiempo para evitar bloqueos infinitos
            process = subprocess.run(
                cmd, 
                env=env,
                timeout=300 # 5 minutos por institución
            )
            if process.returncode == 0:
                print(f"[OK] {name} completed successfully.")
            else:
                print(f"[WARN] {name} failed: {process.stderr[:200]}")
        except Exception as e:
            print(f"[ERROR] Critical error in {name}: {e}")

if __name__ == "__main__":
    main()
