from scripts.core.profile_onboarding import (
    authorized_diagnostic_slugs,
    plan_profile_onboarding,
    persist_profile_onboarding_plan,
)


def test_diagnostic_allowlist_is_explicit_and_rejects_malformed_slugs():
    assert authorized_diagnostic_slugs("ulima, pucp,ulima") == ("pucp", "ulima")
    assert authorized_diagnostic_slugs("") == ()
    assert authorized_diagnostic_slugs("ulima,https://private.example/path") == ()


def test_missing_profile_is_saved_pending_without_invented_effective_mode():
    plan = plan_profile_onboarding(
        institution={"id": "inst-1", "slug": "ulima"},
        existing_profile=None,
        diagnosis={
            "status": "review_required",
            "observed": {"site_type": "unknown"},
            "suggested": {"site_type": "traditional_ssr", "discovery_mode": "hardcoded_urls"},
            "verification": {"eligible": False, "reasons": ["no_reusable_source"]},
        },
        auto_activation_policy=False,
    )

    assert plan["operation"] == "insert"
    row = plan["row"]
    assert row["profile_status"] == "pending_review"
    assert row["site_type"] is None
    assert row["discovery_mode"] is None
    assert row["discovery_enabled"] is False
    assert row["pipeline_enabled"] is False
    assert row["production_enabled"] is False
    assert row["diagnostic_suggested"]["site_type"] == "traditional_ssr"


def test_verified_profile_activates_only_under_explicit_policy_and_never_publishes():
    diagnosis = {
        "status": "verified",
        "observed": {"site_type": "traditional_ssr"},
        "suggested": {
            "site_type": "traditional_ssr",
            "discovery_mode": "sitemap_bfs",
            "seed_urls": ["https://ulima.example/sitemap.xml"],
            "allowed_url_patterns": ["/programas/"],
            "exclusion_patterns": [],
        },
        "verification": {
            "eligible": True,
            "automatic_activation_ready": True,
            "verified_detail_count": 2,
            "new_course_discovery": True,
            "reasons": [],
        },
    }
    pending = plan_profile_onboarding(
        institution={"id": "inst-1", "slug": "ulima"},
        existing_profile=None,
        diagnosis=diagnosis,
        auto_activation_policy=False,
    )
    assert pending["row"]["profile_status"] == "pending_review"
    assert pending["row"]["discovery_enabled"] is False

    active = plan_profile_onboarding(
        institution={"id": "inst-1", "slug": "ulima"},
        existing_profile=None,
        diagnosis=diagnosis,
        auto_activation_policy=True,
    )
    assert active["row"]["profile_status"] == "active"
    assert active["row"]["discovery_enabled"] is True
    assert active["row"]["pipeline_enabled"] is True
    assert active["row"]["production_enabled"] is False
    assert active["row"]["diagnostic_suggested"]["seed_urls"] == [
        "https://ulima.example/sitemap.xml"
    ]


def test_sanitizer_preserves_bounded_pagination_and_removes_tracking_query():
    diagnosis = {
        "status": "verified",
        "observed": {},
        "suggested": {
            "site_type": "ecommerce",
            "discovery_mode": "paginated_catalog",
            "catalog_url_patterns": [
                "https://shop.example/catalog/?page={page}&utm_source=synthetic"
            ],
            "seed_urls": ["https://shop.example/catalog/?page=1&utm_campaign=private"],
        },
        "verification": {
            "eligible": True,
            "automatic_activation_ready": True,
            "verified_detail_count": 2,
            "new_course_discovery": True,
            "reasons": [],
        },
    }

    plan = plan_profile_onboarding(
        institution={"id": "inst-2", "slug": "shop"},
        existing_profile=None,
        diagnosis=diagnosis,
        auto_activation_policy=True,
    )

    assert plan["row"]["profile_status"] == "active"
    assert plan["row"]["diagnostic_suggested"]["catalog_url_patterns"] == [
        "https://shop.example/catalog/?page={page}"
    ]
    assert plan["row"]["diagnostic_suggested"]["seed_urls"] == [
        "https://shop.example/catalog/?page=1"
    ]


def test_unknown_query_is_redacted_and_prevents_automatic_activation():
    plan = plan_profile_onboarding(
        institution={"id": "inst-3", "slug": "custom"},
        existing_profile=None,
        diagnosis={
            "status": "verified",
            "observed": {},
            "suggested": {
                "site_type": "traditional_ssr",
                "discovery_mode": "sitemap_bfs",
                "seed_urls": ["https://custom.example/catalog/?token=private-sentinel"],
            },
            "verification": {
                "eligible": True,
                "automatic_activation_ready": True,
                "verified_detail_count": 2,
                "new_course_discovery": True,
                "reasons": [],
            },
        },
        auto_activation_policy=True,
    )

    assert plan["row"]["profile_status"] == "pending_review"
    assert plan["row"]["diagnostic_status"] == "review_required"
    assert plan["row"]["diagnostic_suggested"]["seed_urls"] == [
        "https://custom.example/catalog/"
    ]
    assert "private-sentinel" not in str(plan["row"])


def test_overlong_url_is_redacted_and_prevents_automatic_activation():
    long_url = "https://shop.example/catalog/" + ("x" * 2100) + "/?page=1"
    plan = plan_profile_onboarding(
        institution={"id": "inst-long-url", "slug": "shop"},
        existing_profile=None,
        diagnosis={
            "status": "verified",
            "observed": {"source_url": long_url},
            "suggested": {
                "site_type": "ecommerce",
                "discovery_mode": "paginated_catalog",
                "seed_urls": [long_url],
            },
            "verification": {
                "eligible": True,
                "automatic_activation_ready": True,
                "verified_detail_count": 2,
                "new_course_discovery": True,
                "reasons": [],
            },
        },
        auto_activation_policy=True,
    )

    row = plan["row"]
    assert row["profile_status"] == "pending_review"
    assert row["diagnostic_status"] == "review_required"
    assert row["diagnostic_observed"]["source_url"] == "[unsafe-url-redacted]"
    assert row["diagnostic_suggested"]["seed_urls"] == ["[unsafe-url-redacted]"]
    assert "x" * 100 not in str(row)


def test_unsupported_and_malformed_urls_are_redacted_without_corrupting_text_fields():
    plan = plan_profile_onboarding(
        institution={"id": "inst-3", "slug": "custom"},
        existing_profile=None,
        diagnosis={
            "status": "verified",
            "observed": {
                "website_url": "http:///private-sentinel/path?password=secret-sentinel",
                "description": "Price: 400 soles",
            },
            "suggested": {
                "site_type": "traditional_ssr",
                "discovery_mode": "sitemap_bfs",
                "seed_urls": ["file:///private-sentinel/credential-sentinel"],
            },
            "verification": {
                "eligible": True,
                "automatic_activation_ready": True,
                "verified_detail_count": 2,
                "new_course_discovery": True,
                "reasons": [],
            },
        },
        auto_activation_policy=True,
    )

    row = plan["row"]
    assert row["profile_status"] == "pending_review"
    assert row["diagnostic_status"] == "review_required"
    assert row["diagnostic_observed"]["website_url"] == "[unsafe-url-redacted]"
    assert row["diagnostic_observed"]["description"] == "Price: 400 soles"
    assert row["diagnostic_suggested"]["seed_urls"] == ["[unsafe-url-redacted]"]
    assert all(
        marker not in str(row)
        for marker in ("private-sentinel", "credential-sentinel", "secret-sentinel")
    )


def test_new_diagnosis_never_replaces_manual_profile_fields_or_gates():
    manual = {
        "institution_id": "inst-1",
        "profile_status": "active",
        "auto_generated": False,
        "site_type": "ecommerce",
        "discovery_mode": "paginated_catalog",
        "seed_urls": ["https://shop.example/catalog/page/{page}"],
        "catalog_link_selector": "a.course-card",
        "exclusion_patterns": ["/admission/"],
        "discovery_enabled": True,
        "pipeline_enabled": True,
        "production_enabled": False,
    }
    plan = plan_profile_onboarding(
        institution={"id": "inst-1", "slug": "shop"},
        existing_profile=manual,
        diagnosis={
            "status": "review_required",
            "observed": {"site_type": "spa_js_heavy"},
            "suggested": {
                "site_type": "spa_js_heavy",
                "discovery_mode": "catalog_link_extraction",
                "seed_urls": ["https://shop.example/other"],
            },
            "verification": {"eligible": False, "reasons": ["ambiguous"]},
        },
        auto_activation_policy=True,
    )

    assert plan["operation"] == "patch_diagnostic_metadata"
    patch = plan["row"]
    assert "site_type" not in patch
    assert "discovery_mode" not in patch
    assert "seed_urls" not in patch
    assert "catalog_link_selector" not in patch
    assert "exclusion_patterns" not in patch
    assert "discovery_enabled" not in patch
    assert "pipeline_enabled" not in patch
    assert "production_enabled" not in patch


def _verified_ssr_diagnosis():
    return {
        "status": "verified",
        "observed": {"site_type": "traditional_ssr"},
        "suggested": {
            "site_type": "traditional_ssr",
            "discovery_mode": "sitemap_bfs",
            "seed_urls": ["https://uni.example/sitemap.xml"],
            "allowed_url_patterns": ["/programas/"],
            "exclusion_patterns": [],
        },
        "verification": {
            "eligible": True,
            "automatic_activation_ready": True,
            "verified_detail_count": 2,
            "new_course_discovery": True,
            "reasons": [],
        },
    }


def test_verified_legacy_generated_incomplete_profile_can_activate_with_cas():
    existing = {
        "id": "profile-1",
        "institution_id": "inst-1",
        "profile_status": "active",
        "auto_generated": True,
        "site_type": "traditional_ssr",
        "discovery_mode": None,
        "seed_urls": [],
        "updated_at": "2026-11-20T12:00:00+00:00",
    }

    plan = plan_profile_onboarding(
        institution={"id": "inst-1", "slug": "uni"},
        existing_profile=existing,
        diagnosis=_verified_ssr_diagnosis(),
        auto_activation_policy=True,
    )

    assert plan["operation"] == "activate_pending"
    assert plan["row"]["profile_status"] == "active"
    assert "site_type" not in plan["row"]
    assert plan["row"]["discovery_mode"] == "sitemap_bfs"
    assert plan["expected"] == {
        "id": "profile-1",
        "updated_at": "2026-11-20T12:00:00+00:00",
        "profile_status": "active",
    }


def test_auto_activation_fails_closed_without_updated_at_compare_snapshot():
    existing = {
        "id": "profile-1",
        "institution_id": "inst-1",
        "profile_status": "pending_review",
        "auto_generated": True,
        "site_type": None,
        "discovery_mode": None,
    }

    plan = plan_profile_onboarding(
        institution={"id": "inst-1", "slug": "uni"},
        existing_profile=existing,
        diagnosis=_verified_ssr_diagnosis(),
        auto_activation_policy=True,
    )

    assert plan["operation"] == "patch_diagnostic_metadata"
    assert plan["row"]["profile_status"] == "pending_review"
    assert plan["row"]["diagnostic_status"] == "review_required"
    assert "site_type" not in plan["row"]
    assert "discovery_mode" not in plan["row"]


def test_pending_profile_activation_uses_exact_snapshot_and_requires_one_row():
    plan = {
        "operation": "activate_pending",
        "row": {"profile_status": "active", "pipeline_enabled": True},
        "expected": {
            "id": "profile/1",
            "updated_at": "2026-11-20T12:00:00+00:00",
            "profile_status": "pending_review",
        },
    }

    class Database:
        def __init__(self):
            self.call = None

        def patch_exact_one_raise(self, table, filters, data, expected_id):
            self.call = (table, filters, data, expected_id)

    db = Database()
    persist_profile_onboarding_plan(db, "inst-1", plan)

    assert db.call == (
        "institution_site_profiles",
        "id=eq.profile%2F1&institution_id=eq.inst-1&updated_at=eq.2026-11-20T12%3A00%3A00%2B00%3A00&profile_status=eq.pending_review&auto_generated=eq.true",
        plan["row"],
        "profile/1",
    )


def test_concurrent_profile_change_aborts_automatic_activation():
    plan = {
        "operation": "activate_pending",
        "row": {"profile_status": "active", "pipeline_enabled": True},
        "expected": {
            "id": "profile-1",
            "updated_at": "2026-11-20T12:00:00+00:00",
            "profile_status": "pending_review",
        },
    }

    class StaleDatabase:
        def patch_exact_one_raise(self, *_args, **_kwargs):
            raise RuntimeError("exactly one profile row was not updated")

    import pytest

    with pytest.raises(RuntimeError, match="exactly one"):
        persist_profile_onboarding_plan(StaleDatabase(), "inst-1", plan)
