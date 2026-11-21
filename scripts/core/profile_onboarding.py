"""Fail-closed persistence plan for the FG2 profile onboarding stage.

Diagnostic observations and suggestions are stored separately from the
effective profile. Existing effective fields are never replaced by a later
diagnosis. Activation requires an explicit, environment-wide policy gate.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any, Mapping
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


_SLUG = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,78}[a-z0-9])?$")
_SUPPORTED_TYPES = {"traditional_ssr", "spa_js_heavy", "ecommerce"}
_SUPPORTED_MODES = {
    "sitemap_bfs", "paginated_catalog", "catalog_link_extraction", "hardcoded_urls"
}
_EFFECTIVE_FIELDS = (
    "site_type", "discovery_mode", "seed_urls", "catalog_url_patterns",
    "catalog_link_selector", "exclusion_patterns", "allowed_url_patterns",
    "allowed_resource_origins",
    "catalog_max_pages", "catalog_scroll_iterations", "requires_stealth",
    "requires_cloudflare_bypass", "detail_wait_ms",
)
_SENSITIVE_KEYS = {
    "raw_html", "body", "response_body", "headers", "cookies", "token",
    "secret", "authorization", "password", "api_key", "apikey",
}
_URL_FIELD_NAMES = {
    "url", "urls", "website_url", "source_url", "source_urls", "detail_url",
    "detail_urls", "catalog_url", "catalog_urls", "seed_urls",
    "allowed_resource_origins",
}
_URL_LIKE = re.compile(
    r"^(?:[a-z][a-z0-9+.-]*://|(?:data|javascript|file|mailto|blob|about|chrome-extension):)",
    re.IGNORECASE,
)
_PAGINATION_QUERY_KEYS = {
    "page", "paged", "offset", "limit", "per_page", "page_size", "pagesize",
}
_TRACKING_QUERY_KEYS = {"gclid", "fbclid", "msclkid"}


def authorized_diagnostic_slugs(value: str | None) -> tuple[str, ...]:
    """Parse an explicit per-environment examination allowlist; invalid input fails closed."""
    if value is None or not value.strip():
        return ()
    values = [part.strip().lower() for part in value.split(",")]
    if any(not _SLUG.fullmatch(part) for part in values):
        return ()
    return tuple(sorted(set(values)))


def _safe_url(value: str, review_flags: list[str] | None) -> str:
    try:
        parsed = urlsplit(value)
        if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
            if review_flags is not None:
                review_flags.append("unsupported_or_malformed_url")
            return "[unsafe-url-redacted]"
        hostname = parsed.hostname.lower()
        if ":" in hostname and not hostname.startswith("["):
            hostname = f"[{hostname}]"
        port = parsed.port
        netloc = hostname if port is None else f"{hostname}:{port}"
        if parsed.username is not None or parsed.password is not None:
            if review_flags is not None:
                review_flags.append("url_userinfo")

        kept: list[tuple[str, str]] = []
        seen: set[str] = set()
        try:
            parameters = parse_qsl(parsed.query, keep_blank_values=True, max_num_fields=20)
        except ValueError:
            parameters = []
            if review_flags is not None:
                review_flags.append("malformed_url_query")
        for key, item in parameters:
            normalized_key = key.strip().lower()
            if normalized_key.startswith("utm_") or normalized_key in _TRACKING_QUERY_KEYS:
                continue
            if normalized_key not in _PAGINATION_QUERY_KEYS or normalized_key in seen:
                if review_flags is not None:
                    review_flags.append("unsupported_url_query")
                continue
            if item == "{page}":
                normalized_value = item
            elif item.isdecimal() and len(item) <= 7:
                numeric_value = int(item)
                upper_bound = 1_000_000 if normalized_key == "offset" else 1_000
                if numeric_value < 1 or numeric_value > upper_bound:
                    if review_flags is not None:
                        review_flags.append("pagination_out_of_range")
                    continue
                normalized_value = str(numeric_value)
            else:
                if review_flags is not None:
                    review_flags.append("malformed_pagination_query")
                continue
            seen.add(normalized_key)
            kept.append((normalized_key, normalized_value))
        kept.sort()
        sanitized = urlunsplit(
            (parsed.scheme.lower(), netloc, parsed.path or "/", urlencode(kept, safe="{}"), "")
        )
        if len(sanitized) > 2048:
            if review_flags is not None:
                review_flags.append("url_too_long")
            return "[unsafe-url-redacted]"
        return sanitized
    except (TypeError, ValueError):
        if review_flags is not None:
            review_flags.append("malformed_url")
        return "[unsafe-url-redacted]"


def _safe_json(
    value: Any,
    *,
    depth: int = 0,
    review_flags: list[str] | None = None,
    field_name: str | None = None,
) -> Any:
    if depth > 8:
        return "[depth-limited]"
    if isinstance(value, Mapping):
        result = {}
        for key, item in value.items():
            name = str(key).lower()
            if any(secret in name for secret in _SENSITIVE_KEYS):
                continue
            result[str(key)[:80]] = _safe_json(
                item,
                depth=depth + 1,
                review_flags=review_flags,
                field_name=str(key),
            )
        return result
    if isinstance(value, list):
        return [
            _safe_json(
                item,
                depth=depth + 1,
                review_flags=review_flags,
                field_name=field_name,
            )
            for item in value[:100]
        ]
    if isinstance(value, str):
        normalized_field = (field_name or "").lower()
        if normalized_field in _URL_FIELD_NAMES or normalized_field.endswith(("_url", "_urls")) or _URL_LIKE.match(value):
            return _safe_url(value, review_flags)
        return value[:2048]
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return str(type(value).__name__)


def _verified(diagnosis: Mapping[str, Any]) -> bool:
    verification = diagnosis.get("verification")
    suggestion = diagnosis.get("suggested")
    if not isinstance(verification, Mapping) or not isinstance(suggestion, Mapping):
        return False
    sanitization_flags: list[str] = []
    _safe_json(suggestion, review_flags=sanitization_flags)
    return bool(
        not sanitization_flags
        and diagnosis.get("status") == "verified"
        and verification.get("eligible") is True
        and verification.get("automatic_activation_ready") is True
        and verification.get("new_course_discovery") is True
        and isinstance(verification.get("verified_detail_count"), int)
        and verification["verified_detail_count"] >= 2
        and suggestion.get("site_type") in _SUPPORTED_TYPES
        and suggestion.get("discovery_mode") in _SUPPORTED_MODES
        and suggestion.get("discovery_mode") != "hardcoded_urls"
        and not verification.get("reasons")
    )


def _diagnostic_metadata(diagnosis: Mapping[str, Any], source_sha: str | None) -> dict[str, Any]:
    sanitization_flags: list[str] = []
    observed = _safe_json(diagnosis.get("observed", {}), review_flags=sanitization_flags)
    suggested = _safe_json(diagnosis.get("suggested", {}), review_flags=sanitization_flags)
    metadata = {
        "diagnostic_status": (
            "verified"
            if _verified(diagnosis) and not sanitization_flags
            else "review_required"
        ),
        "diagnostic_observed": observed,
        "diagnostic_suggested": suggested,
        "diagnostic_provenance": {
            "policy_version": "fg2-profile-onboarding-v1",
            "source_sha": source_sha if isinstance(source_sha, str) and re.fullmatch(r"[0-9a-f]{40}", source_sha) else None,
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "evidence_sha256": hashlib.sha256(
                json.dumps({"observed": observed, "suggested": suggested}, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest(),
        },
    }
    return metadata


def plan_profile_onboarding(
    *,
    institution: Mapping[str, Any],
    existing_profile: Mapping[str, Any] | None,
    diagnosis: Mapping[str, Any],
    auto_activation_policy: bool,
    source_sha: str | None = None,
) -> dict[str, Any]:
    """Return one insert/patch payload without mutating caller-owned data."""
    institution_id = institution.get("id")
    if not isinstance(institution_id, str) or not institution_id.strip():
        raise ValueError("registered institution ID is required")
    suggestion = diagnosis.get("suggested")
    suggestion = suggestion if isinstance(suggestion, Mapping) else {}
    metadata = _diagnostic_metadata(diagnosis, source_sha)
    can_activate = bool(auto_activation_policy and _verified(diagnosis))

    if existing_profile is None:
        row = {
            "institution_id": institution_id,
            "profile_status": "active" if can_activate else "pending_review",
            "site_type": suggestion.get("site_type") if can_activate else None,
            "discovery_mode": suggestion.get("discovery_mode") if can_activate else None,
            "discovery_enabled": can_activate,
            "pipeline_enabled": can_activate,
            "production_enabled": False,
            "auto_generated": True,
            "pipeline_ready": False,
            **metadata,
        }
        if can_activate:
            for field in _EFFECTIVE_FIELDS:
                if field in suggestion:
                    row[field] = _safe_json(suggestion[field], field_name=field)
        return {"operation": "insert", "row": row}

    # Persist only the new observation/suggestion fields for an existing row.
    # A routine diagnosis cannot change a validated manual profile or its gates.
    row = dict(metadata)
    incomplete_effective_mode = not existing_profile.get("site_type") or not existing_profile.get("discovery_mode")
    if incomplete_effective_mode:
        # An incomplete legacy row is visible as pending, but its non-empty
        # effective fields remain untouched until an operator resolves it.
        row["profile_status"] = "pending_review"
    existing_status = existing_profile.get("profile_status") or "active"
    if (
        can_activate
        and (existing_status == "pending_review" or incomplete_effective_mode)
        and existing_profile.get("auto_generated") is True
    ):
        missing_effective_fields = [
            field for field in _EFFECTIVE_FIELDS
            if existing_profile.get(field) not in (None, "", [], {})
            and field in suggestion
            and existing_profile.get(field) != suggestion[field]
        ]
        # Existing generated rows may be completed automatically only when
        # the snapshot has a versioned updated_at value for compare-and-swap.
        # The database trigger updates this value for every row mutation, so a
        # concurrent manual edit invalidates this plan before activation.
        expected_updated_at = existing_profile.get("updated_at")
        if not missing_effective_fields and isinstance(expected_updated_at, str) and expected_updated_at:
            for field in _EFFECTIVE_FIELDS:
                if existing_profile.get(field) in (None, "", [], {}) and field in suggestion:
                    row[field] = _safe_json(suggestion[field], field_name=field)
            row.update({
                "profile_status": "active",
                "discovery_enabled": True,
                "pipeline_enabled": True,
                # FG2 activation never implies public publication.
                "production_enabled": False,
            })
        elif not missing_effective_fields:
            row["profile_status"] = "pending_review"
            row["diagnostic_status"] = "review_required"
            metadata["diagnostic_status"] = "review_required"
        else:
            row["diagnostic_status"] = "review_required"
            metadata["diagnostic_status"] = "review_required"
    operation = (
        "activate_pending"
        if row.get("profile_status") == "active"
        else "patch_diagnostic_metadata"
    )
    plan = {"operation": operation, "row": row}
    if operation == "activate_pending":
        plan["expected"] = {
            "id": existing_profile.get("id"),
            "updated_at": existing_profile.get("updated_at"),
            "profile_status": existing_status,
        }
    return plan


def persist_profile_onboarding_plan(db: Any, institution_id: str, plan: Mapping[str, Any]) -> None:
    """Persist the plan through the pipeline DB client; no raw diagnostic data is logged."""
    operation = plan.get("operation")
    row = plan.get("row")
    if not isinstance(row, Mapping):
        raise ValueError("profile onboarding payload is malformed")
    if operation == "insert":
        db.insert("institution_site_profiles", dict(row))
        return
    if operation == "patch_diagnostic_metadata":
        db.patch(
            "institution_site_profiles",
            filters=f"institution_id=eq.{institution_id}",
            data=dict(row),
        )
        return
    if operation == "activate_pending":
        expected = plan.get("expected")
        if not isinstance(expected, Mapping):
            raise RuntimeError("pending profile activation snapshot is missing")
        expected_id = expected.get("id")
        expected_updated_at = expected.get("updated_at")
        expected_status = expected.get("profile_status")
        if (
            not isinstance(expected_id, str)
            or not expected_id.strip()
            or not isinstance(expected_updated_at, str)
            or not expected_updated_at.strip()
            or expected_status not in {"active", "pending_review"}
        ):
            raise RuntimeError("pending profile activation snapshot is invalid")
        from urllib.parse import quote

        db.patch_exact_one_raise(
            "institution_site_profiles",
            filters=(
                f"id=eq.{quote(expected_id, safe='')}"
                f"&institution_id=eq.{quote(institution_id, safe='')}"
                f"&updated_at=eq.{quote(expected_updated_at, safe='')}"
                f"&profile_status=eq.{expected_status}&auto_generated=eq.true"
            ),
            data=dict(row),
            expected_id=expected_id,
        )
        return
    raise ValueError("unsupported profile onboarding operation")
