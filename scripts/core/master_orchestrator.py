import subprocess
import logging
import sys
import os
import json
import time
import contextlib
import io
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

# Add root directory to sys.path for shared imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.db_client import get_db_client
from shared.f10_9_fg2_preflight import (
    ExistingDbReadFacade,
    PreflightError,
    build_runtime_manifest,
    run_preflight,
    safe_source_probe,
    sanitized_collection_error,
)
from shared.utils import setup_lima_logging

db = None
logger = setup_lima_logging("MasterOrchestrator")
MAX_RUN_SECONDS = 20400
CIRCUIT_COOLDOWN = timedelta(hours=24)


def _is_f10_production_canary():
    return bool(os.getenv("F10_PRODUCTION_CANARY_RUN_ID", "").strip())


def _cohort_label(value=None):
    return "canary_cohort=redacted" if _is_f10_production_canary() else "cohort_member=redacted"


def _safe_error_label(error):
    return type(error).__name__ if _is_f10_production_canary() else str(error)


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

    logger.info(f"[STAGE START] {script_path} args=redacted count={len(args or [])}")
    # Explicitly pass environment to subprocess
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=os.environ.copy(),
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        logger.error(f"[STAGE TIMEOUT] {script_path}")
        return False

    if result.stdout:
        logger.info(f"[STAGE STDOUT REDACTED] {script_path} lines={len(result.stdout.splitlines())}")
    if result.stderr:
        logger.warning(f"[STAGE STDERR REDACTED] {script_path} lines={len(result.stderr.splitlines())}")

    if result.returncode == 0:
        logger.info(f"✅ [STAGE SUCCESS] {script_path}")
        return True
    else:
        logger.error(f"❌ [STAGE FAILED] {script_path} (Exit Code: {result.returncode})")
        return False

def get_institutions(limit=10, excluded_slugs=None, only_slug=None, now=None):
    """Return eligible institutions after all gates, then apply the limit."""
    if limit <= 0:
        return []
    client = _get_db()
    current_time = now or datetime.now(timezone.utc)
    excluded = set(excluded_slugs or [])
    selected_slug = only_slug.strip() if only_slug else None
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
        slug = institution.get('slug')
        if selected_slug and slug != selected_slug:
            continue
        if slug in excluded:
            continue
        if not profile or not profile.get('discovery_enabled'):
            continue
        if profile.get('circuit_open'):
            try:
                opened_at = _parse_timestamp(profile.get('circuit_opened_at'))
            except (TypeError, ValueError):
                opened_at = None
            if opened_at is None or current_time - opened_at < CIRCUIT_COOLDOWN:
                logger.info(f"[CIRCUIT OPEN] Skipping {_cohort_label(institution.get('name'))}")
                continue

        try:
            last_harvest = _parse_timestamp(institution.get('last_harvest_at'))
        except (TypeError, ValueError) as exc:
            raise RuntimeError("Invalid freshness timestamp for canary cohort") from exc
        if (
            last_harvest
            and current_time - last_harvest < timedelta(days=3)
            and client.count_pipeline_raise(
                'staging_raw',
                filters=f"institution_id=eq.{quote(str(institution['id']), safe='')}",
            ) > 50
        ):
            logger.info(f"[FRESHNESS GUARD] Skipping {_cohort_label(institution.get('name'))}")
            continue

        eligible.append(institution)
        if len(eligible) >= limit:
            break

    return eligible

def main(
    argv=None,
    *,
    db_facade=None,
    source_probe=None,
    script_runner=None,
    clock=None,
    manifest_sink=None,
):
    import argparse

    # Detect Job Start Time from environment (GitHub Actions) or use current time as fallback
    env_start = os.getenv("JOB_START_TIME")
    clock = clock or time.time
    global_start = float(env_start) if env_start else clock()

    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=5, help="Number of institutions to process")
    parser.add_argument("--exclude", type=str, help="Slugs of institutions to exclude (comma separated)")
    parser.add_argument("--institution-slug", help="Optional exact institution slug for a one-institution run")
    parser.add_argument("--max-urls", type=int, default=None, help="Maximum discovered URLs per institution")
    parser.add_argument("--skip-cleansing", action="store_true", help="Skip the cleansing phase (Station 1.5)")
    args = parser.parse_args(argv)

    excluded_slugs = {
        slug.strip() for slug in args.exclude.split(',') if slug.strip()
    } if args.exclude else set()
    failures = []
    member_outcomes = {}
    runner = script_runner or run_script
    effective_probe = source_probe or safe_source_probe

    def emit_runtime(result):
        manifest = build_runtime_manifest(
            preflight.manifest,
            result=result,
            member_outcomes=member_outcomes,
        )
        if manifest_sink is not None:
            manifest_sink(manifest)
        logger.info(
            f"[FG2 RUNTIME] result={result} "
            f"manifest_fingerprint={manifest['manifest_fingerprint']}"
        )

    # G2/P3: no harvester construction or subprocess is permitted before both
    # the frozen preflight and its immediately-before-run drift check pass.
    logger.info("[FG2 PREFLIGHT] collecting read-only cohort")
    try:
        output_guard = (
            contextlib.redirect_stdout(io.StringIO())
            if _is_f10_production_canary()
            else contextlib.nullcontext()
        )
        error_guard = (
            contextlib.redirect_stderr(io.StringIO())
            if _is_f10_production_canary()
            else contextlib.nullcontext()
        )
        with output_guard, error_guard:
            first_facade = db_facade or ExistingDbReadFacade(_get_db())
            preflight = run_preflight(
                first_facade,
                effective_probe,
                limit=args.limit,
                excluded_slugs=excluded_slugs,
                only_slug=args.institution_slug,
            )
            second_facade = db_facade or ExistingDbReadFacade(_get_db())
            verified = run_preflight(
                second_facade,
                effective_probe,
                limit=args.limit,
                excluded_slugs=excluded_slugs,
                only_slug=args.institution_slug,
            )
    except Exception as exc:
        reason = str(exc) if isinstance(exc, PreflightError) else "COLLECTION_ERROR"
        preflight = sanitized_collection_error(reason)
        logger.error(f"[FG2 PREFLIGHT] result=BLOCKED reason={reason}")
        return 1

    if (
        preflight.manifest.get("run_fingerprint")
        != verified.manifest.get("run_fingerprint")
        or preflight.manifest.get("snapshot_fingerprint")
        != verified.manifest.get("snapshot_fingerprint")
    ):
        logger.error("[FG2 PREFLIGHT] result=BLOCKED reason=FINGERPRINT_DRIFT")
        return 1

    if preflight.is_noop and verified.is_noop:
        emit_runtime("NOOP")
        logger.info("[FG2 PREFLIGHT] result=NOOP cohort_size=0")
        return 0
    if not preflight.is_runnable or not verified.is_runnable:
        logger.error("[FG2 PREFLIGHT] result=BLOCKED")
        return 1
    cohort = preflight._consume()
    institutions = tuple(item.as_runtime_dict() for item in cohort.institutions)
    logger.info(
        f"[FG2 PREFLIGHT] result=PASS cohort_size={len(institutions)} "
        f"run_fingerprint={cohort.run_fingerprint}"
    )

    # 🚉 PHASE 1: Discovery & Harvesting
    logger.info("--- PHASE 1: DISCOVERY & HARVESTING ---")

    for inst in institutions:
        inst_id = inst['id']
        remaining = MAX_RUN_SECONDS - (clock() - global_start)
        if remaining <= 0:
            logger.error("[TIME BUDGET] Global harvesting budget exhausted")
            failures.append("global_time_budget")
            member_outcomes["TIME_BUDGET"] = member_outcomes.get("TIME_BUDGET", 0) + 1
            break

        logger.info(f"### Processing Institution: {_cohort_label()}")
        inst_json = json.dumps(dict(inst))
        harvester_args = [inst_json, "--global-start", str(global_start)]
        if args.max_urls is not None:
            harvester_args.extend(["--max-urls", str(args.max_urls)])
        # Pass global start to sub-process
        if not runner(
            "scripts/core/universal_harvester.py",
            harvester_args,
            timeout=remaining,
        ):
            failures.append("harvester:redacted")
            member_outcomes["FAILED"] = member_outcomes.get("FAILED", 0) + 1
        else:
            member_outcomes["SUCCESS"] = member_outcomes.get("SUCCESS", 0) + 1

    # A failed institution blocks cleansing/downstream while preserving already
    # persisted work from successful institutions.
    if failures:
        emit_runtime("PARTIAL_GLOBAL")
        return 1

    # 🚉 PHASE 1.5: Cleansing
    if not args.skip_cleansing:
        logger.info("--- PHASE 1.5: CLEANSING ---")
        remaining = MAX_RUN_SECONDS - (clock() - global_start)
        if remaining <= 0:
            logger.error("[TIME BUDGET] No budget remains for cleansing")
            failures.append("cleansing:time_budget")
            member_outcomes["TIME_BUDGET"] = member_outcomes.get("TIME_BUDGET", 0) + 1
        elif not runner("scripts/core/cleansing_worker.py", timeout=remaining):
            logger.warning("Cleansing step failed; downstream remains blocked.")
            failures.append("cleansing")
            member_outcomes["CLEANSING_FAILED"] = 1
    else:
        logger.info("--- PHASE 1.5: CLEANSING SKIPPED (Delegated to Orchestrator) ---")

    if failures:
        emit_runtime("PARTIAL_GLOBAL")
        return 1
    emit_runtime("SUCCESS")
    logger.info("🏁 ORCHESTRATOR LOOP FINISHED.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
