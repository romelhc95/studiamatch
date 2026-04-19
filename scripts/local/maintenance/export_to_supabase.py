import os
import subprocess
from datetime import datetime

def run_command(cmd):
    print(f"Executing: {cmd}")
    # Run in binary mode to avoid encoding issues with subprocess.run
    result = subprocess.run(cmd, shell=True, capture_output=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr.decode('utf-8', errors='ignore')}")
    return result.stdout.decode('utf-8', errors='ignore')

def export_db():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_dir = f"db/exports/{timestamp}"
    os.makedirs(export_dir, exist_ok=True)
    
    print(f"--- Exporting Local DB to {export_dir} ---")
    
    # 1. Export Schema only
    schema_file = f"{export_dir}/01_schema.sql"
    cmd_schema = f"docker exec studiamatch-db-predesa pg_dump -U postgres -d studiamatch_predesa --schema-only --no-owner --no-privileges"
    schema_data = run_command(cmd_schema)
    with open(schema_file, "w", encoding="utf-8") as f:
        f.write(schema_data)
    
    # 2. Export Seeds (Support tables)
    seeds_file = f"{export_dir}/02_seeds.sql"
    tables = ["institutions", "categories", "category_rules", "market_salaries", "crawler_exclusions"]
    table_flags = " ".join([f"-t {t}" for t in tables])
    cmd_seeds = f"docker exec studiamatch-db-predesa pg_dump -U postgres -d studiamatch_predesa --data-only --inserts --no-owner --no-privileges {table_flags}"
    seeds_data = run_command(cmd_seeds)
    with open(seeds_file, "w", encoding="utf-8") as f:
        f.write(seeds_data)
    
    # 3. Export Operative Data (Optional)
    data_file = f"{export_dir}/03_operative_data.sql"
    tables_data = ["staging_raw", "cleansed_programs"]
    table_flags_data = " ".join([f"-t {t}" for t in tables_data])
    cmd_data = f"docker exec studiamatch-db-predesa pg_dump -U postgres -d studiamatch_predesa --data-only --inserts --no-owner --no-privileges {table_flags_data}"
    operative_data = run_command(cmd_data)
    with open(data_file, "w", encoding="utf-8") as f:
        f.write(operative_data)
    
    print(f"\n--- SUCCESS ---")
    print(f"Files generated in: {export_dir}")
    print("\nNext Steps for Supabase Migration:")
    print(f"1. Open Supabase SQL Editor.")
    print(f"2. Execute 01_schema.sql to sync schema (adjusting for existing tables).")
    print(f"3. Execute 02_seeds.sql to populate core logic.")
    print(f"4. Execute 03_operative_data.sql to restore harvesting progress.")

if __name__ == "__main__":
    export_db()
