import os
import requests
import json
import math
import sys
from dotenv import load_dotenv

load_dotenv()

# Configuration
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
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
    # Number of workers (passed as argument or default to 1)
    n_workers = 1
    if len(sys.argv) > 1:
        try:
            n_workers = int(sys.argv[1])
        except ValueError:
            pass

    print(f"Orchestrating for {n_workers} workers...")
    
    institutions = get_active_institutions()
    print(f"Found {len(institutions)} active institutions.")
    
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
    
    # Also print to stdout for GitHub Actions output capture if needed
    # (Using a compact format for GH Actions output if requested, but JSON file is better for complexity)
    # print(json.dumps(output))

if __name__ == "__main__":
    main()
