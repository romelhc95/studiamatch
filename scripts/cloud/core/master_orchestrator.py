import subprocess
import logging
import sys
import os
import requests
import json

# Add root directory to sys.path for shared imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.db_client import get_db_client

db = get_db_client()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [ORCHESTRATOR] - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("MasterOrchestrator")

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
    """Fetch institutions to harvest."""
    try:
        return db.select('institutions', columns="id,name,slug,website_url", limit=limit)
    except Exception as e:
        logger.error(f"Failed to fetch institutions: {e}")
    return []

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=5, help="Number of institutions to process")
    parser.add_argument("--exclude", type=str, help="Slugs of institutions to exclude (comma separated)")
    parser.add_argument("--skip-cleansing", action="store_true", help="Skip the cleansing phase (Station 1.5)")
    args = parser.parse_args()

    excluded_slugs = args.exclude.split(',') if args.exclude else []

    # DB credentials handled by db_client

    # 🚉 PHASE 1: Discovery & Harvesting
    logger.info("--- PHASE 1: DISCOVERY & HARVESTING ---")
    institutions = get_institutions(limit=args.limit)
    
    # Filter out excluded
    institutions = [i for i in institutions if i['slug'] not in excluded_slugs]
    
    logger.info(f"Found {len(institutions)} institutions to harvest after exclusions.")

    for inst in institutions:
        logger.info(f"### Processing Institution: {inst['name']} ({inst['slug']})")
        # Ensure we convert to dict and serialize cleanly
        inst_json = json.dumps(dict(inst))
        run_script("scripts/cloud/core/universal_harvester.py", [inst_json])

    # 🚉 PHASE 1.5: Cleansing
    if not args.skip_cleansing:
        logger.info("--- PHASE 1.5: CLEANSING ---")
        if not run_script("scripts/cloud/core/cleansing_worker.py"):
            logger.warning("Cleansing step failed, but continuing pipeline...")
    else:
        logger.info("--- PHASE 1.5: CLEANSING SKIPPED (Delegated to Orchestrator) ---")

    logger.info("🏁 ORCHESTRATOR LOOP FINISHED.")

if __name__ == "__main__":
    main()
