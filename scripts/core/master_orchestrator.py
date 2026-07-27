import subprocess
import logging
import sys
import os
import json
import time
from datetime import datetime, timedelta, timezone

# Add root directory to sys.path for shared imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.db_client import get_db_client
from shared.utils import setup_lima_logging

db = None
logger = setup_lima_logging("MasterOrchestrator")
MAX_RUN_SECONDS = 20400
CIRCUIT_COOLDOWN = timedelta(hours=24)


def _get_db():
    global db
    if db is None:
        db = get_db_client()
    return db


def _parse_timestamp(value):
    if not value:
        return None
    parsed = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def run_script(script_path, args=None, timeout=None):
    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)
    
    logger.info(f"🚀 [STAGE START] {script_path} {' '.join(args) if args else ''}")
    # Explicitly pass environment to subprocess
    try:
        result = subprocess.run(
            cmd,
            capture_output=False,
            env=os.environ.copy(),
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        logger.error(f"[STAGE TIMEOUT] {script_path}")
        return False
    
    if result.returncode == 0:
        logger.info(f"✅ [STAGE SUCCESS] {script_path}")
        return True
    else:
        logger.error(f"❌ [STAGE FAILED] {script_path} (Exit Code: {result.returncode})")
        return False

def get_institutions(limit=10, excluded_slugs=None, now=None):
    """Return eligible institutions after all gates, then apply the limit."""
    if limit <= 0:
        return []
    client = _get_db()
    current_time = now or datetime.now(timezone.utc)
    excluded = set(excluded_slugs or [])
    all_insts = client.select_service_raise(
        'institutions',
        columns="id,name,slug,website_url,last_harvest_at",
        order="last_harvest_at.asc.nullsfirst",
    )
    profiles = client.select_pipeline_raise(
        'institution_site_profiles',
        columns=(
            "institution_id,discovery_enabled,circuit_open,"
            "circuit_opened_at"
        ),
    )
    profile_by_institution = {
        str(profile.get('institution_id')): profile
        for profile in profiles
        if isinstance(profile, dict) and profile.get('institution_id')
    }

    eligible = []
    for institution in all_insts:
        profile = profile_by_institution.get(str(institution.get('id')))
        if institution.get('slug') in excluded:
            continue
        if not profile or not profile.get('discovery_enabled'):
            continue
        if profile.get('circuit_open'):
            try:
                opened_at = _parse_timestamp(profile.get('circuit_opened_at'))
            except (TypeError, ValueError):
                opened_at = None
            if opened_at is None or current_time - opened_at < CIRCUIT_COOLDOWN:
                logger.info(
                    f"[CIRCUIT OPEN] Skipping {institution.get('name')}"
                )
                continue

        try:
            last_harvest = _parse_timestamp(institution.get('last_harvest_at'))
        except (TypeError, ValueError) as exc:
            raise RuntimeError(
                f"Invalid freshness timestamp for {institution.get('name')}"
            ) from exc
        if (
            last_harvest
            and current_time - last_harvest < timedelta(days=3)
            and client.count_pipeline_raise(
                'staging_raw',
                filters=f"institution_id=eq.{institution['id']}",
            ) > 50
        ):
            logger.info(
                f"[FRESHNESS GUARD] Skipping {institution.get('name')}"
            )
            continue

        eligible.append(institution)
        if len(eligible) >= limit:
            break

    return eligible

def main(argv=None):
    import argparse
    
    # Detect Job Start Time from environment (GitHub Actions) or use current time as fallback
    env_start = os.getenv("JOB_START_TIME")
    global_start = float(env_start) if env_start else time.time()
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=5, help="Number of institutions to process")
    parser.add_argument("--exclude", type=str, help="Slugs of institutions to exclude (comma separated)")
    parser.add_argument("--skip-cleansing", action="store_true", help="Skip the cleansing phase (Station 1.5)")
    args = parser.parse_args(argv)

    excluded_slugs = {
        slug.strip() for slug in args.exclude.split(',') if slug.strip()
    } if args.exclude else set()
    failures = []

    # 🚉 PHASE 1: Discovery & Harvesting
    logger.info("--- PHASE 1: DISCOVERY & HARVESTING ---")
    try:
        institutions = get_institutions(
            limit=args.limit,
            excluded_slugs=excluded_slugs,
        )
    except Exception as exc:
        logger.error(f"Failed to select eligible institutions: {exc}")
        return 1
    
    logger.info(f"Found {len(institutions)} institutions to harvest after exclusions.")

    for inst in institutions:
        inst_id = inst['id']
        inst_name = inst['name']
        remaining = MAX_RUN_SECONDS - (time.time() - global_start)
        if remaining <= 0:
            logger.error("[TIME BUDGET] Global harvesting budget exhausted")
            failures.append("global_time_budget")
            break

        logger.info(f"### Processing Institution: {inst_name} ({inst['slug']})")
        inst_json = json.dumps(dict(inst))
        # Pass global start to sub-process
        if not run_script(
            "scripts/core/universal_harvester.py",
            [inst_json, "--global-start", str(global_start)],
            timeout=remaining,
        ):
            failures.append(f"harvester:{inst.get('slug')}")

    # 🚉 PHASE 1.5: Cleansing
    if not args.skip_cleansing:
        logger.info("--- PHASE 1.5: CLEANSING ---")
        remaining = MAX_RUN_SECONDS - (time.time() - global_start)
        if remaining <= 0:
            logger.error("[TIME BUDGET] No budget remains for cleansing")
            failures.append("cleansing:time_budget")
        elif not run_script("scripts/core/cleansing_worker.py", timeout=remaining):
            logger.warning("Cleansing step failed, but continuing pipeline...")
            failures.append("cleansing")
    else:
        logger.info("--- PHASE 1.5: CLEANSING SKIPPED (Delegated to Orchestrator) ---")

    logger.info("🏁 ORCHESTRATOR LOOP FINISHED.")
    return 1 if failures else 0

if __name__ == "__main__":
    sys.exit(main())
