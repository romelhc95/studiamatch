import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlparse

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv(*_args, **_kwargs):
        return False

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_db_client():
    from shared.db_client import get_db_client as _get_db_client

    return _get_db_client()


MANIFEST_SCHEMA = "f10-production-canary-manifest.v1"
VALID_DISCOVERY_MODES = {
    "hardcoded_urls",
    "sitemap_bfs",
    "paginated_catalog",
    "catalog_link_extraction",
}
VALID_SITE_TYPES = {"traditional_ssr", "spa_js_heavy", "ecommerce"}
EXACT_F10_LIMITS = {
    "max_staging_records": 5,
    "max_enrichment_records": 3,
    "max_sync_records": 3,
    "max_integrity_courses": 3,
}


def _ensure_github_production_context():
    if os.getenv("GITHUB_ACTIONS") != "true":
        raise RuntimeError("Production canary scripts must run inside GitHub Actions")
    if os.getenv("GITHUB_EVENT_NAME") != "workflow_dispatch":
        raise RuntimeError("Production canary must run from workflow_dispatch")
    if os.getenv("GITHUB_REF_NAME") != "main":
        raise RuntimeError("Production canary must run from the main branch")
    if os.getenv("CANARY_EXPECTED_ENVIRONMENT") != "Production":
        raise RuntimeError("Production canary expected environment mismatch")


def _ensure_production_supabase_target():
    expected_host = os.getenv("F10_PRODUCTION_CANARY_SUPABASE_HOST", "").strip().lower()
    if not expected_host:
        raise RuntimeError("Production canary Supabase host allowlist is not configured")
    for variable_name in ("SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_URL"):
        parsed = urlparse(os.getenv(variable_name, ""))
        host = (parsed.hostname or "").lower()
        try:
            port = parsed.port
        except ValueError as exc:
            raise RuntimeError(f"{variable_name} has invalid Supabase URL port") from exc
        if (
            parsed.scheme != "https"
            or parsed.username
            or parsed.password
            or port not in (None, 443)
            or host != expected_host
        ):
            raise RuntimeError(f"{variable_name} does not match the Production Supabase host allowlist")


def _mask_github_value(value):
    if os.getenv("GITHUB_ACTIONS") == "true" and value not in (None, ""):
        text = str(value)
        if "\n" in text or "\r" in text:
            return
        print(f"::add-mask::{text}")


def _resolve_institution(db, slug):
    rows = db.select_service_raise(
        "institutions",
        filters=f"slug=eq.{quote(str(slug), safe='')}",
        columns="id,slug,website_url",
        limit=2,
    )
    if len(rows) != 1:
        raise RuntimeError("Expected exactly one institution for canary cohort")
    return rows[0]


def _load_profile(db, institution_id):
    rows = db.select_pipeline_raise(
        "institution_site_profiles",
        filters=f"institution_id=eq.{quote(str(institution_id), safe='')}",
        columns=(
            "institution_id,discovery_enabled,pipeline_enabled,"
            "production_enabled,circuit_open,circuit_opened_at,"
            "site_type,discovery_mode,seed_urls,catalog_url_patterns,"
            "allowed_url_patterns,exclusion_patterns,catalog_link_selector"
        ),
        limit=2,
    )
    if len(rows) > 1:
        raise RuntimeError("Expected at most one site profile for canary institution")
    profile = rows[0] if rows else {}
    for field in (
        "seed_urls",
        "catalog_url_patterns",
        "allowed_url_patterns",
        "exclusion_patterns",
    ):
        profile[field] = _normalize_jsonb_list(profile.get(field))
    return profile


def _normalize_jsonb_list(value):
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return []
        return parsed if isinstance(parsed, list) else []
    if isinstance(value, list):
        return value
    return []


def _validate_exact_f10_limits(args):
    for attr, expected in EXACT_F10_LIMITS.items():
        if getattr(args, attr) != expected:
            raise RuntimeError("Production canary limits do not match the F10.8 contract")


def _validate_profile_contract(profile, *, require_pipeline_enabled, require_production_enabled):
    if not profile:
        raise RuntimeError("Canary institution profile is not configured")
    if not profile.get("discovery_enabled"):
        raise RuntimeError("Canary institution is not discovery_enabled")
    if require_pipeline_enabled and not profile.get("pipeline_enabled"):
        raise RuntimeError("Canary institution is not pipeline_enabled")
    if require_production_enabled and not profile.get("production_enabled"):
        raise RuntimeError("Canary institution is not production_enabled")
    if profile.get("circuit_open"):
        raise RuntimeError("Canary institution has circuit_open=true")

    site_type = str(profile.get("site_type") or "").strip()
    discovery_mode = str(profile.get("discovery_mode") or "").strip()
    if site_type not in VALID_SITE_TYPES:
        raise RuntimeError("Canary institution site_type is not valid")
    if discovery_mode not in VALID_DISCOVERY_MODES:
        raise RuntimeError("Canary institution discovery_mode is not valid")

    seed_urls = profile.get("seed_urls") or []
    catalog_patterns = profile.get("catalog_url_patterns") or []
    allowed_patterns = profile.get("allowed_url_patterns") or []
    exclusions = profile.get("exclusion_patterns") or []

    if discovery_mode in {"hardcoded_urls", "catalog_link_extraction"} and not seed_urls:
        raise RuntimeError("Canary institution source seeds are not configured")
    if discovery_mode == "paginated_catalog" and not catalog_patterns:
        raise RuntimeError("Canary institution catalog patterns are not configured")
    if not exclusions:
        raise RuntimeError("Canary institution exclusions are not configured")
    if discovery_mode in {"hardcoded_urls", "sitemap_bfs"} and not allowed_patterns:
        raise RuntimeError("Canary institution allowed URL patterns are not configured")


def _count_pipeline(db, table, filters):
    return db.count_pipeline_raise(table, filters=filters)


def _count_service(db, table, filters):
    return db.count_service_raise(table, filters=filters)


def _write_github_env(env_path, institution_id, institution_slug):
    if not env_path:
        return
    _mask_github_value(institution_id)
    _mask_github_value(institution_slug)
    with open(env_path, "a", encoding="utf-8") as handle:
        handle.write(f"CANARY_INSTITUTION_ID={institution_id}\n")
        handle.write(f"CANARY_INSTITUTION_SLUG={institution_slug}\n")


def build_manifest(args):
    _ensure_github_production_context()
    load_dotenv()
    _ensure_production_supabase_target()
    _validate_exact_f10_limits(args)
    db = get_db_client()
    institution = _resolve_institution(db, args.institution_slug)
    institution_id = institution["id"]
    _mask_github_value(institution_id)
    _mask_github_value(institution["slug"])
    profile = _load_profile(db, institution_id)
    _validate_profile_contract(
        profile,
        require_pipeline_enabled=args.require_pipeline_enabled,
        require_production_enabled=args.require_production_enabled,
    )

    inst_filter = f"institution_id=eq.{quote(str(institution_id), safe='')}"
    counts = {
        "staging_total": _count_pipeline(db, "staging_raw", inst_filter),
        "staging_discovered": _count_pipeline(db, "staging_raw", f"{inst_filter}&status=eq.discovered"),
        "staging_pending": _count_pipeline(db, "staging_raw", f"{inst_filter}&status=eq.pending"),
        "cleansed_pending": _count_pipeline(db, "cleansed_programs", f"{inst_filter}&status=eq.pending"),
        "enriched_pending": _count_pipeline(db, "enriched_programs", f"{inst_filter}&status=eq.pending"),
        "courses_active": _count_service(db, "courses", f"{inst_filter}&is_active=eq.true"),
    }
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "stage": args.stage,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "github": {
            "ref_name": os.getenv("GITHUB_REF_NAME"),
        },
        "cohort": {
            "institution_slug": "redacted",
        },
        "profile_gates": {
            "discovery_enabled": bool(profile.get("discovery_enabled")),
            "pipeline_enabled": bool(profile.get("pipeline_enabled")),
            "production_enabled": bool(profile.get("production_enabled")),
            "circuit_open": bool(profile.get("circuit_open")),
        },
        "profile_contract": {
            "site_type": profile.get("site_type"),
            "discovery_mode": profile.get("discovery_mode"),
            "has_seed_urls": bool(profile.get("seed_urls")),
            "has_allowed_url_patterns": bool(profile.get("allowed_url_patterns")),
            "has_exclusion_patterns": bool(profile.get("exclusion_patterns")),
        },
        "limits": {
            "max_staging_records": args.max_staging_records,
            "max_enrichment_records": args.max_enrichment_records,
            "max_sync_records": args.max_sync_records,
            "max_integrity_courses": args.max_integrity_courses,
        },
        "counts": counts,
    }
    _write_github_env(args.github_env, institution_id, institution["slug"])
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build a sanitized F10 Production canary manifest")
    parser.add_argument("--institution-slug", required=True)
    parser.add_argument("--stage", choices=("pre", "post", "after-cleanup"), required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--github-env")
    parser.add_argument("--require-pipeline-enabled", action="store_true")
    parser.add_argument("--require-production-enabled", action="store_true")
    parser.add_argument("--max-staging-records", type=int, default=5)
    parser.add_argument("--max-enrichment-records", type=int, default=3)
    parser.add_argument("--max-sync-records", type=int, default=3)
    parser.add_argument("--max-integrity-courses", type=int, default=3)
    args = parser.parse_args(argv)

    manifest = build_manifest(args)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote sanitized production canary manifest: {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
