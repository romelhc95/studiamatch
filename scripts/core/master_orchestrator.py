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
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from shared.db_client import DatabaseAPIError, get_db_client
from shared.utils import setup_lima_logging
from scripts.core.fg2_bounded_run import (
    FG2ApprovedLotManifest,
    FG2_LIMITS,
    FG2CohortManifest,
    InvalidControlledRun,
    initialize_manifest,
    stable_json_sha256,
    validate_controlled_profile,
    verify_approved_lot_scope,
)
from scripts.core.profile_onboarding import (
    authorized_diagnostic_slugs,
    persist_profile_onboarding_plan,
    plan_profile_onboarding,
)

db = None
logger = setup_lima_logging("MasterOrchestrator")
MAX_RUN_SECONDS = 20400
CIRCUIT_COOLDOWN = timedelta(hours=24)
FG2_DIAGNOSTIC_PREFIX = "[FG2_DIAGNOSTIC] "
FG2_DIAGNOSTIC_PHASES = frozenset({
    "dependency_import",
    "module_initialization",
    "mode_validation",
    "input_decode",
    "harvester_initialization",
    "profile_gate",
    "browser_initialization",
    "source_discovery",
    "course_detail",
    "staging_write",
    "telemetry",
    "shutdown",
})
FG2_DIAGNOSTIC_CATEGORIES = frozenset({
    "dependency_import_failed",
    "module_initialization_failed",
    "controlled_run_rejected",
    "invalid_input",
    "database_api_error",
    "database_write_outcome_unknown",
    "harvester_rejected",
    "source_request_error",
    "timeout",
    "os_error",
    "profile_missing",
    "circuit_open",
    "discovery_unavailable",
    "unexpected_exception",
})
FG2_DIAGNOSTIC_TABLES = frozenset({
    "institutions",
    "institution_site_profiles",
    "staging_raw",
    "courses",
    "cleansed_programs",
    "enriched_programs",
})


def _is_f10_production_canary():
    return bool(os.getenv("F10_PRODUCTION_CANARY_RUN_ID", "").strip())


def _is_sensitive_log_context():
    return (
        _is_f10_production_canary()
        or os.getenv("FG2_CONTROLLED_FIRST_RUN", "").strip().lower() == "true"
        or os.getenv("FG2_COHORT_SCOPED", "").strip().lower() == "true"
    )


def _cohort_label(value=None):
    if _is_sensitive_log_context():
        return "canary_cohort=redacted"
    return str(value)


def _safe_error_label(error):
    return type(error).__name__ if _is_sensitive_log_context() else str(error)


def _approved_lot_preflight_error_label(error):
    if isinstance(error, DatabaseAPIError):
        allowed_tables = {
            "staging_raw",
            "courses",
            "cleansed_programs",
            "enriched_programs",
        }
        table = error.table if error.table in allowed_tables else "unknown"
        status_code = error.status_code
        status = (
            str(status_code)
            if isinstance(status_code, int) and not isinstance(status_code, bool)
            and 100 <= status_code <= 599
            else "unknown"
        )
        return f"database_read_failed table={table} http_status={status}"
    if isinstance(error, InvalidControlledRun):
        return "snapshot_mismatch: InvalidControlledRun"
    return f"verification_failed: {type(error).__name__}"


# StudIAMatch-Docs: .context/componentes/pipeline.md#concurrencia-idempotencia-requeue-y-errores
def _safe_stage_label(script_path):
    """Map child paths to a fixed operational label for sensitive logs."""
    basename = str(script_path).replace("\\", "/").rsplit("/", 1)[-1]
    return {
        "universal_harvester.py": "harvester",
        "cleansing_worker.py": "cleansing",
        "enrichment_worker.py": "enrichment",
        "sync_vector_worker.py": "sync",
    }.get(basename, "unknown")


def _parse_child_diagnostic(stdout, stderr):
    """Accept only the worker's versioned, fixed-vocabulary failure event."""
    for stream in (stderr, stdout):
        if not isinstance(stream, str):
            continue
        for line in (stream or "").splitlines():
            if not line.startswith(FG2_DIAGNOSTIC_PREFIX):
                continue
            try:
                payload = json.loads(line[len(FG2_DIAGNOSTIC_PREFIX):])
            except (TypeError, ValueError):
                continue
            version = payload.get("version") if isinstance(payload, dict) else None
            if not isinstance(version, int) or isinstance(version, bool) or version != 1:
                continue
            phase = payload.get("phase")
            category = payload.get("category")
            if (
                not isinstance(phase, str)
                or phase not in FG2_DIAGNOSTIC_PHASES
                or not isinstance(category, str)
                or category not in FG2_DIAGNOSTIC_CATEGORIES
            ):
                continue
            diagnostic = {"phase": phase, "category": category}
            table = payload.get("table")
            if isinstance(table, str) and table in FG2_DIAGNOSTIC_TABLES:
                diagnostic["table"] = table
            status = payload.get("http_status")
            if isinstance(status, int) and not isinstance(status, bool) and 100 <= status <= 599:
                diagnostic["http_status"] = status
            return diagnostic
    return None


def _get_db():
    global db
    if db is None:
        db = get_db_client()
    return db


def run_profile_onboarding(*, source_sha=None):
    """Run explicit, allowlisted diagnostics before the ordinary cohort selector.

    Newly diagnosed institutions are excluded from this run's harvesting so
    diagnostic HTTP cannot reset or exceed the later harvesting budget.
    """
    if os.getenv("FG2_PROFILE_DIAGNOSTICS_ENABLED", "").strip().lower() != "true":
        return set()
    raw_slugs = os.getenv("FG2_PROFILE_DIAGNOSTIC_SLUGS", "")
    slugs = authorized_diagnostic_slugs(raw_slugs)
    if raw_slugs.strip() and not slugs:
        raise InvalidControlledRun("profile diagnostic slug allowlist is malformed")
    if not slugs:
        raise InvalidControlledRun("profile diagnostics require an explicit institution allowlist")
    if os.getenv("FG2_CONTROLLED_FIRST_RUN", "").strip().lower() == "true":
        raise InvalidControlledRun("profile onboarding cannot mutate an approved controlled lot context")

    from scripts.shared.site_diagnostics import diagnose_site

    client = _get_db()
    institutions = client.select_service_raise(
        "institutions",
        columns="id,name,slug,website_url",
        order="last_harvest_at.asc.nullsfirst",
    )
    profiles = client.select_pipeline_raise("institution_site_profiles", columns="*")
    profile_rows: dict[str, dict] = {}
    for profile in profiles:
        if not isinstance(profile, dict) or not profile.get("institution_id"):
            raise InvalidControlledRun("profile diagnostic inventory is malformed")
        key = str(profile["institution_id"]).lower()
        if key in profile_rows:
            raise InvalidControlledRun("profile diagnostic inventory contains duplicate institution rows")
        profile_rows[key] = profile

    matching = [institution for institution in institutions if institution.get("slug") in slugs]
    found_slugs = {institution.get("slug") for institution in matching}
    if found_slugs != set(slugs):
        missing = len(set(slugs) - found_slugs)
        logger.error("FG2 profile onboarding allowlist does not match the registered catalog (missing=%s).", missing)
        raise InvalidControlledRun("profile diagnostic allowlist does not match registered institutions")

    diagnosed_slugs = set()
    persist_diagnostics = (
        os.getenv("FG2_PROFILE_DIAGNOSTIC_PERSIST_ENABLED", "").strip().lower()
        == "true"
    )
    auto_activate = os.getenv("FG2_PROFILE_AUTO_ACTIVATE_VERIFIED", "").strip().lower() == "true"
    if auto_activate and not persist_diagnostics:
        raise InvalidControlledRun(
            "automatic profile activation requires the separate diagnostic persistence gate"
        )
    for institution in matching:
        inst_id = str(institution["id"])
        existing = profile_rows.get(inst_id.lower())
        if existing and (
            existing.get("profile_status", "active") == "active"
            and existing.get("site_type")
            and existing.get("discovery_mode")
        ):
            continue
        website_url = institution.get("website_url")
        diagnosis = diagnose_site(website_url) if isinstance(website_url, str) and website_url else {
            "status": "review_required",
            "observed": {"website_url_present": False},
            "suggested": {},
            "verification": {"eligible": False, "verified_detail_count": 0, "new_course_discovery": False, "reasons": ["institution_url_missing"]},
        }
        plan = plan_profile_onboarding(
            institution=institution,
            existing_profile=existing,
            diagnosis=diagnosis,
            auto_activation_policy=auto_activate,
            source_sha=source_sha,
        )
        if persist_diagnostics:
            persist_profile_onboarding_plan(client, inst_id, plan)
        diagnosed_slugs.add(institution["slug"])
        logger.info(
            "FG2 profile onboarding completed: status=%s, persisted=%s, auto_activation_policy=%s, requests=%s.",
            plan["row"].get("diagnostic_status", "review_required"),
            persist_diagnostics,
            auto_activate,
            (diagnosis.get("observed") or {}).get("request_count", 0),
        )
    return diagnosed_slugs


def _parse_timestamp(value):
    if not value:
        return None
    parsed = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def run_script(script_path, args=None, timeout=None):
    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)

    sensitive = _is_sensitive_log_context()
    safe_stage = _safe_stage_label(script_path)
    if sensitive:
        logger.info("[STAGE START] stage=%s args=redacted count=%s", safe_stage, len(args or []))
    else:
        logger.info(f"🚀 [STAGE START] {script_path} {' '.join(args) if args else ''}")
    # Explicitly pass environment to subprocess
    try:
        capture_child_output = sensitive
        result = subprocess.run(
            cmd,
            capture_output=capture_child_output,
            text=capture_child_output,
            env=os.environ.copy(),
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        if sensitive:
            logger.error(
                "[STAGE FAILURE] stage=%s phase=subprocess_execution failure_class=child_timeout",
                safe_stage,
            )
        else:
            logger.error(f"[STAGE TIMEOUT] {script_path}")
        return False
    except OSError as exc:
        if sensitive:
            error_class = type(exc).__name__
            if error_class not in {"FileNotFoundError", "PermissionError", "OSError"}:
                error_class = "OSError"
            logger.error(
                "[STAGE FAILURE] stage=%s phase=subprocess_start failure_class=process_start_failed error_class=%s",
                safe_stage,
                error_class,
            )
        else:
            logger.error(f"[STAGE START FAILED] {script_path} ({type(exc).__name__})")
        return False

    if sensitive:
        if result.stdout:
            logger.info("[STAGE STDOUT REDACTED] stage=%s lines=%s", safe_stage, len(result.stdout.splitlines()))
        if result.stderr:
            logger.warning("[STAGE STDERR REDACTED] stage=%s lines=%s", safe_stage, len(result.stderr.splitlines()))

    if result.returncode == 0:
        if sensitive:
            logger.info("[STAGE SUCCESS] stage=%s", safe_stage)
        else:
            logger.info(f"✅ [STAGE SUCCESS] {script_path}")
        return True
    else:
        if sensitive:
            exit_code = (
                result.returncode
                if isinstance(result.returncode, int) and not isinstance(result.returncode, bool)
                else "unknown"
            )
            stdout_lines = len(result.stdout.splitlines()) if result.stdout else 0
            stderr_lines = len(result.stderr.splitlines()) if result.stderr else 0
            diagnostic = _parse_child_diagnostic(result.stdout, result.stderr)
            phase = diagnostic["phase"] if diagnostic else "unknown"
            failure_class = diagnostic["category"] if diagnostic else "child_process_exit"
            table = diagnostic.get("table", "unknown") if diagnostic else "unknown"
            http_status = diagnostic.get("http_status", "unknown") if diagnostic else "unknown"
            logger.error(
                "[STAGE FAILURE] stage=%s phase=%s failure_class=%s table=%s http_status=%s "
                "exit_code=%s stdout_lines=%s stderr_lines=%s",
                safe_stage,
                phase,
                failure_class,
                table,
                http_status,
                exit_code,
                stdout_lines,
                stderr_lines,
            )
            return False
        logger.error(f"❌ [STAGE FAILED] {script_path} (Exit Code: {result.returncode})")
        return False

def get_institutions(
    limit=10,
    excluded_slugs=None,
    only_slug=None,
    now=None,
    controlled=False,
    approved_lot=None,
    scheduled_cohort=False,
):
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
        # The table is small; reading the row keeps this selector compatible
        # with additive onboarding metadata without projecting new columns on
        # installations that have not applied its migration yet.
        columns="*",
    )
    profile_by_institution = {
        str(profile.get('institution_id')).lower(): profile
        for profile in profiles
        if isinstance(profile, dict) and profile.get('institution_id')
    }

    if approved_lot is not None:
        if not controlled or excluded or selected_slug:
            raise InvalidControlledRun("approved FG2 lot cannot be combined with selection overrides")
        if limit < len(approved_lot.institution_ids):
            raise InvalidControlledRun("approved FG2 lot exceeds the selected institution limit")
        institutions_by_id = {
            str(institution.get("id", "")).lower(): institution
            for institution in all_insts
            if institution.get("id")
        }
        if len(institutions_by_id) != len(all_insts):
            raise InvalidControlledRun("current institution catalog contains duplicate or invalid IDs")
        expected_ids = approved_lot.institution_ids
        if any(institution_id not in institutions_by_id for institution_id in expected_ids):
            raise InvalidControlledRun("an approved FG2 lot institution is no longer present")
        rotated_ids = tuple(
            str(institution.get("id", "")).lower()
            for institution in all_insts
            if str(institution.get("id", "")).lower() in set(expected_ids)
        )
        if rotated_ids != expected_ids:
            raise InvalidControlledRun("approved FG2 lot no longer matches the rotation order")

        profile_counts: dict[str, int] = {}
        for profile in profiles:
            if isinstance(profile, dict) and profile.get("institution_id"):
                key = str(profile["institution_id"]).lower()
                profile_counts[key] = profile_counts.get(key, 0) + 1
        if any(profile_counts.get(institution_id, 0) != 1 for institution_id in expected_ids):
            raise InvalidControlledRun("an approved FG2 lot institution profile is missing or duplicated")

        last_expected_index = next(
            index
            for index, institution in enumerate(all_insts)
            if str(institution.get("id", "")).lower() == expected_ids[-1]
        )
        eligible_prefix = []
        for institution in all_insts[: last_expected_index + 1]:
            institution_id = str(institution.get("id", "")).lower()
            if profile_counts.get(institution_id, 0) > 1:
                raise InvalidControlledRun("institution rotation prefix contains duplicate site profiles")
            profile = profile_by_institution.get(institution_id)
            if not profile or not profile.get("discovery_enabled"):
                continue
            if profile.get("circuit_open"):
                try:
                    opened_at = _parse_timestamp(profile.get("circuit_opened_at"))
                except (TypeError, ValueError):
                    opened_at = None
                if opened_at is None or current_time - opened_at < CIRCUIT_COOLDOWN:
                    continue
            last_harvest = _parse_timestamp(institution.get("last_harvest_at"))
            if (
                last_harvest
                and current_time - last_harvest < timedelta(days=3)
                and client.count_pipeline_raise(
                    "staging_raw",
                    filters=f"institution_id=eq.{quote(institution_id, safe='')}",
                ) > 50
            ):
                continue
            try:
                validate_controlled_profile(
                    institution,
                    profile,
                    now=current_time,
                    scheduled_cohort=scheduled_cohort,
                )
            except InvalidControlledRun:
                continue
            eligible_prefix.append(institution_id)
        if tuple(eligible_prefix[: len(expected_ids)]) != expected_ids:
            raise InvalidControlledRun("approved FG2 lot no longer matches the eligible rotation prefix")

        selected = []
        for institution_id in expected_ids:
            institution = institutions_by_id[institution_id]
            profile = profile_by_institution.get(institution_id)
            if not profile or not profile.get("discovery_enabled"):
                raise InvalidControlledRun("an approved FG2 lot institution is no longer discovery eligible")
            if profile.get("circuit_open"):
                try:
                    opened_at = _parse_timestamp(profile.get("circuit_opened_at"))
                except (TypeError, ValueError):
                    opened_at = None
                if opened_at is None or current_time - opened_at < CIRCUIT_COOLDOWN:
                    raise InvalidControlledRun("an approved FG2 lot source circuit is open")
            try:
                last_harvest = _parse_timestamp(institution.get("last_harvest_at"))
            except (TypeError, ValueError) as exc:
                raise InvalidControlledRun("approved FG2 lot freshness timestamp is invalid") from exc
            if (
                last_harvest
                and current_time - last_harvest < timedelta(days=3)
                and client.count_pipeline_raise(
                    "staging_raw",
                    filters=f"institution_id=eq.{quote(institution_id, safe='')}",
                ) > 50
            ):
                raise InvalidControlledRun("an approved FG2 lot institution is no longer freshness eligible")
            expected = approved_lot.institution(institution_id)
            preflight = validate_controlled_profile(
                institution,
                profile,
                now=current_time,
                selected_seed_urls=expected["seed_urls"],
                scheduled_cohort=scheduled_cohort,
            )
            approved_lot.assert_institution_origin(
                institution_id,
                str(institution.get("website_url") or ""),
            )
            institution_fingerprint = stable_json_sha256(
                {
                    "id": institution_id,
                    "slug": institution.get("slug"),
                    "website_url": institution.get("website_url"),
                }
            )
            if (
                institution_fingerprint != expected["institution_sha256"]
                or preflight["profile_sha256"] != expected["profile_sha256"]
                or preflight["seed_sha256"] != expected["seed_sha256"]
                or preflight["seed_urls"] != expected["seed_urls"]
            ):
                raise InvalidControlledRun("approved FG2 lot institution, profile, or seeds drifted")
            selected_institution = dict(institution)
            selected_institution["_controlled_profile_sha256"] = preflight["profile_sha256"]
            selected_institution["_controlled_seed_sha256"] = preflight["seed_sha256"]
            selected_institution["_controlled_seed_urls"] = preflight["seed_urls"]
            selected.append(selected_institution)
        return selected

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
        if profile.get("profile_status", "active") != "active":
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

        if controlled:
            try:
                preflight = validate_controlled_profile(
                    institution,
                    profile,
                    now=current_time,
                    scheduled_cohort=scheduled_cohort,
                )
            except InvalidControlledRun as exc:
                logger.info(
                    "[CONTROLLED PREFLIGHT] Skipping %s: %s",
                    _cohort_label(institution.get('name')),
                    _safe_error_label(exc),
                )
                continue
            institution = dict(institution)
            institution["_controlled_profile_sha256"] = preflight["profile_sha256"]
            institution["_controlled_seed_sha256"] = preflight["seed_sha256"]
            institution["_controlled_seed_urls"] = preflight["seed_urls"]

        eligible.append(institution)
        if len(eligible) >= limit:
            break

    return eligible

# StudIAMatch-Docs: .context/componentes/pipeline.md#primera-corrida-fg2-acotada
def main(argv=None):
    import argparse

    # Detect Job Start Time from environment (GitHub Actions) or use current time as fallback
    env_start = os.getenv("JOB_START_TIME")
    global_start = float(env_start) if env_start else time.time()

    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=5, help="Number of institutions to process")
    parser.add_argument("--exclude", type=str, help="Slugs of institutions to exclude (comma separated)")
    parser.add_argument("--institution-slug", help="Optional exact institution slug for a one-institution run")
    parser.add_argument("--max-urls", type=int, default=None, help="Maximum discovered URLs per institution")
    parser.add_argument(
        "--controlled-first-run",
        action="store_true",
        help="Opt in to the first-run request and cohort budgets; manual use only",
    )
    parser.add_argument(
        "--scheduled-cohort",
        action="store_true",
        help="Build a run-scoped bounded cohort for the main-branch schedule",
    )
    parser.add_argument("--cohort-manifest", help="Path for the controlled-run cohort manifest")
    parser.add_argument("--approved-lot-manifest", help="Private path for the reviewed FG2 lot payload")
    parser.add_argument("--approved-lot-reference", help="Human review reference bound to the approved lot")
    parser.add_argument("--approved-lot-sha256", help="SHA-256 of the exact approved FG2 lot bytes")
    parser.add_argument("--skip-cleansing", action="store_true", help="Skip the cleansing phase (Station 1.5)")
    args = parser.parse_args(argv)
    approved_lot = None
    cohort_scoped = args.controlled_first_run or args.scheduled_cohort

    if args.controlled_first_run and args.scheduled_cohort:
        logger.error("A run cannot be both a reviewed manual first run and an ordinary schedule.")
        return 1

    if args.controlled_first_run:
        if not args.skip_cleansing:
            logger.error(
                "Controlled first run requires --skip-cleansing so the workflow can pass the verified cohort manifest to cleansing."
            )
            return 1
        os.environ["FG2_CONTROLLED_FIRST_RUN"] = "true"
        if not args.cohort_manifest or not args.approved_lot_manifest:
            logger.error("Controlled first run requires both cohort and approved-lot manifests")
            return 1
        if not args.approved_lot_reference or not args.approved_lot_sha256:
            logger.error("Controlled first run requires the approved-lot reference and digest")
            return 1
        if args.max_urls not in (None, FG2_LIMITS["max_urls_per_institution"]):
            logger.error("Controlled first run requires the approved 10 URL limit")
            return 1
        run_id = os.getenv("GITHUB_RUN_ID", "")
        run_attempt = os.getenv("GITHUB_RUN_ATTEMPT", "")
        source_sha = os.getenv("GITHUB_SHA", "")
        github_ref = os.getenv("GITHUB_REF", "")
        if not run_id.isdigit() or not run_attempt.isdigit() or not source_sha or github_ref != "refs/heads/main":
            logger.error("Controlled first-run requires main and the exact GitHub run ID, attempt, and source SHA.")
            return 1
        try:
            approved_lot_b64 = os.environ.pop("FG2_APPROVED_LOT_MANIFEST_B64", "")
            approved_lot = FG2ApprovedLotManifest.from_base64(
                approved_lot_b64,
                path=args.approved_lot_manifest,
                expected_sha256=args.approved_lot_sha256,
                expected_reference=args.approved_lot_reference,
                expected_source_sha=source_sha,
            )
        except (InvalidControlledRun, TypeError, ValueError) as exc:
            logger.error("Approved FG2 lot rejected before database selection: %s", _safe_error_label(exc))
            return 1
    elif args.scheduled_cohort:
        if (
            not args.skip_cleansing
            or not args.cohort_manifest
            or any((args.approved_lot_manifest, args.approved_lot_reference, args.approved_lot_sha256))
        ):
            logger.error("Scheduled FG2 requires only a cohort manifest and delegated cleansing.")
            return 1
        if args.limit != 10 or args.max_urls != FG2_LIMITS["max_urls_per_institution"]:
            logger.error("Scheduled FG2 requires the configured institution and URL bounds.")
            return 1
        run_id = os.getenv("GITHUB_RUN_ID", "")
        run_attempt = os.getenv("GITHUB_RUN_ATTEMPT", "")
        source_sha = os.getenv("GITHUB_SHA", "")
        if (
            os.getenv("GITHUB_EVENT_NAME") != "schedule"
            or os.getenv("GITHUB_REF") != "refs/heads/main"
            or not run_id.isdigit()
            or not run_attempt.isdigit()
            or not source_sha
        ):
            logger.error("Scheduled FG2 cohort requires a schedule event on main with exact run metadata.")
            return 1
        os.environ["FG2_COHORT_SCOPED"] = "true"
    elif any((args.approved_lot_manifest, args.approved_lot_reference, args.approved_lot_sha256)):
        logger.error("Approved FG2 lot inputs are only accepted for a controlled first run")
        return 1

    excluded_slugs = {
        slug.strip() for slug in args.exclude.split(',') if slug.strip()
    } if args.exclude else set()
    failures = []
    newly_diagnosed_slugs = set()
    if os.getenv("FG2_PROFILE_DIAGNOSTICS_ENABLED", "").strip().lower() == "true":
        try:
            newly_diagnosed_slugs = run_profile_onboarding(source_sha=os.getenv("GITHUB_SHA"))
        except Exception as exc:
            logger.error("FG2 profile onboarding stopped before cohort selection: %s", _safe_error_label(exc))
            return 1
        # A diagnosis and its later harvest never share a fresh request budget.
        excluded_slugs.update(newly_diagnosed_slugs)

    # 🚉 PHASE 1: Discovery & Harvesting
    logger.info("--- PHASE 1: DISCOVERY & HARVESTING ---")
    try:
        if _is_sensitive_log_context():
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                institutions = get_institutions(
                    limit=args.limit,
                    excluded_slugs=excluded_slugs,
                    only_slug=args.institution_slug,
                    controlled=cohort_scoped,
                    approved_lot=approved_lot,
                    scheduled_cohort=args.scheduled_cohort,
                )
        else:
            institutions = get_institutions(
                limit=args.limit,
                excluded_slugs=excluded_slugs,
                only_slug=args.institution_slug,
                controlled=cohort_scoped,
                approved_lot=approved_lot,
                scheduled_cohort=args.scheduled_cohort,
            )
    except Exception as exc:
        logger.error(f"Failed to select eligible institutions: {_safe_error_label(exc)}")
        return 1

    if args.institution_slug and not institutions:
        logger.error("No eligible institution found for canary cohort" if _is_sensitive_log_context() else f"No eligible institution found for slug: {args.institution_slug}")
        return 1

    if approved_lot is not None:
        try:
            verify_approved_lot_scope(_get_db(), approved_lot)
        except Exception as exc:
            logger.error(
                "Approved FG2 lot verification failed before harvester launch: %s",
                _approved_lot_preflight_error_label(exc),
            )
            return 1

    logger.info(f"Found {len(institutions)} institutions to harvest after exclusions.")

    if cohort_scoped:
        if not institutions:
            logger.error("Controlled first-run preflight found no eligible seeded institutions.")
            return 1
        initial_institutions = [
            {
                "institution_id": inst["id"],
                "profile_sha256": inst["_controlled_profile_sha256"],
                "seed_sha256": inst["_controlled_seed_sha256"],
                "http_requests": 0,
                "unique_urls": 0,
                "result": "preflight_passed",
            }
            for inst in institutions
        ]
        initialize_manifest(
            args.cohort_manifest,
            run_id=os.getenv("GITHUB_RUN_ID", ""),
            run_attempt=int(os.getenv("GITHUB_RUN_ATTEMPT", "")),
            source_sha=os.getenv("GITHUB_SHA", ""),
            institutions=initial_institutions,
            approved_lot_reference=approved_lot.reference if approved_lot else None,
            approved_lot_sha256=approved_lot.sha256 if approved_lot else None,
        )

    for inst in institutions:
        inst_id = inst['id']
        inst_name = inst['name']
        remaining = MAX_RUN_SECONDS - (time.time() - global_start)
        if remaining <= 0:
            logger.error("[TIME BUDGET] Global harvesting budget exhausted")
            failures.append("global_time_budget")
            break

        logger.info(f"### Processing Institution: {_cohort_label(inst_name)}")
        child_institution = dict(inst)
        if cohort_scoped:
            child_institution["_controlled_profile_sha256"] = inst["_controlled_profile_sha256"]
            child_institution["_controlled_seed_sha256"] = inst["_controlled_seed_sha256"]
        inst_json = json.dumps(child_institution)
        harvester_args = [inst_json, "--global-start", str(global_start)]
        if cohort_scoped:
            harvester_args.extend([
                "--controlled" if args.controlled_first_run else "--scheduled-cohort",
                "--cohort-manifest",
                args.cohort_manifest,
                "--max-urls",
                str(FG2_LIMITS["max_urls_per_institution"]),
            ])
            if approved_lot is not None:
                harvester_args.extend([
                    "--approved-lot-manifest", args.approved_lot_manifest,
                    "--approved-lot-reference", args.approved_lot_reference,
                    "--approved-lot-sha256", args.approved_lot_sha256,
                ])
        elif args.max_urls is not None:
            harvester_args.extend(["--max-urls", str(args.max_urls)])
        # Pass global start to sub-process
        if not run_script(
            "scripts/core/universal_harvester.py",
            harvester_args,
            timeout=remaining,
        ):
            failures.append("harvester:redacted" if _is_sensitive_log_context() else f"harvester:{inst.get('slug')}")
            if cohort_scoped:
                logger.error("Controlled FG2 stops after a failed institution subprocess; no later source is contacted.")
                return 1

    if cohort_scoped:
        try:
            completed_manifest = FG2CohortManifest.load(
                args.cohort_manifest,
                expected_run_id=os.getenv("GITHUB_RUN_ID", ""),
                expected_run_attempt=int(os.getenv("GITHUB_RUN_ATTEMPT", "")),
                expected_source_sha=os.getenv("GITHUB_SHA", ""),
                allow_empty=True,
            )
        except (InvalidControlledRun, TypeError, ValueError) as exc:
            logger.error("Controlled cohort manifest failed postflight: %s", _safe_error_label(exc))
            return 1
        if args.controlled_first_run and not completed_manifest.payload["entries"]:
            logger.error("Controlled first run produced no cohort rows; no downstream stage may run.")
            return 1

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
