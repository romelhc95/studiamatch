import subprocess
import logging
import sys
import os
import requests
import json

# Add root directory to sys.path for shared imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.db_client import get_db_client
from shared.utils import setup_lima_logging

db = get_db_client()
logger = setup_lima_logging("MasterOrchestrator")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def run_script(script_path, args=None):
    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)
    
    logger.info(f"🚀 [STAGE START] {script_path} {' '.join(args) if args else ''}")
    # Explicitly pass environment to subprocess
    result = subprocess.run(cmd, capture_output=False, env=os.environ.copy())
    
    if result.returncode == 0:
        logger.info(f"✅ [STAGE SUCCESS] {script_path}")
        return True
    else:
        logger.error(f"❌ [STAGE FAILED] {script_path} (Exit Code: {result.returncode})")
        return False

def get_institutions(limit=10):
    """Fetch institutions to harvest, prioritizing those not processed recently."""
    try:
        # Use ordering to implement Round-Robin/Rolling Shard logic
        return db.select('institutions', 
                         columns="id,name,slug,website_url,last_harvest_at", 
                         order="last_harvest_at.asc.nullsfirst", 
                         limit=limit)
    except Exception as e:
        logger.error(f"Failed to fetch institutions: {e}")
    return []

def main():
    import argparse
    import time
    
    # Detect Job Start Time from environment (GitHub Actions) or use current time as fallback
    env_start = os.getenv("JOB_START_TIME")
    global_start = float(env_start) if env_start else time.time()
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=5, help="Number of institutions to process")
    parser.add_argument("--exclude", type=str, help="Slugs of institutions to exclude (comma separated)")
    parser.add_argument("--skip-cleansing", action="store_true", help="Skip the cleansing phase (Station 1.5)")
    args = parser.parse_args()

    excluded_slugs = args.exclude.split(',') if args.exclude else []

    # 🚉 PHASE 1: Discovery & Harvesting
    logger.info("--- PHASE 1: DISCOVERY & HARVESTING ---")
    institutions = get_institutions(limit=args.limit)
    
    # Filter out excluded
    institutions = [i for i in institutions if i['slug'] not in excluded_slugs]
    
    logger.info(f"Found {len(institutions)} institutions to harvest after exclusions.")

    for inst in institutions:
        inst_id = inst['id']
        inst_name = inst['name']
        last_harvest = inst['last_harvest_at']
        
        # 🛡️ FRESHNESS GUARD: Skip if already dense (>50 urls) and updated in the last 3 days (72h)
        if last_harvest:
            try:
                # Handle ISO format from DB
                from datetime import datetime, timezone, timedelta
                last_dt = datetime.fromisoformat(last_harvest.replace('Z', '+00:00'))
                now_dt = datetime.now(timezone.utc)
                
                if (now_dt - last_dt) < timedelta(days=3):
                    # Quick count in staging_raw
                    res = db.select('staging_raw', filters=f"institution_id=eq.{inst_id}", columns="count")
                    count = res[0]['count'] if res else 0
                    
                    if count > 50:
                        logger.info(f"🛡️ [FRESHNESS GUARD] Skipping {inst_name}: Dense catalog ({count} URLs) updated recently ({last_dt.strftime('%Y-%m-%d %H:%M')}).")
                        continue
            except Exception as e:
                logger.warning(f"Failed to check freshness for {inst_name}: {e}")

        logger.info(f"### Processing Institution: {inst_name} ({inst['slug']})")
        inst_json = json.dumps(dict(inst))
        # Pass global start to sub-process
        run_script("scripts/core/universal_harvester.py", [inst_json, "--global-start", str(global_start)])

    # 🚉 PHASE 1.5: Cleansing
    if not args.skip_cleansing:
        logger.info("--- PHASE 1.5: CLEANSING ---")
        if not run_script("scripts/core/cleansing_worker.py"):
            logger.warning("Cleansing step failed, but continuing pipeline...")
    else:
        logger.info("--- PHASE 1.5: CLEANSING SKIPPED (Delegated to Orchestrator) ---")

    logger.info("🏁 ORCHESTRATOR LOOP FINISHED.")

if __name__ == "__main__":
    main()
