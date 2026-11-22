import unittest
from unittest.mock import patch

from scripts.shared.site_diagnostics import (
    DiagnosticRequestBudget,
    _ACTIVE_DIAGNOSTIC_BUDGET,
    _ACTIVE_DIAGNOSTIC_ORIGIN,
    _render_controlled_page,
    assign_template,
    detect_catalog_links,
    detect_cms,
    detect_js_required,
    evaluate_discovery_candidates,
    suggest_discovery_mode,
)
from scripts.shared import site_diagnostics as diagnostics_module
from scripts.core import fg2_bounded_run as bounded_run_module


class SyntheticDiagnosticResponse:
    encoding = "utf-8"

    def __init__(self, url, status, body=b"", headers=None):
        self.url = url
        self.status_code = status
        self.body = body
        self.headers = headers or {"content-type": "text/html; charset=utf-8"}
        self.content = b""
        self.closed = False
        self.bytes_read = 0

    @property
    def text(self):
        return self.content.decode(self.encoding)

    def iter_content(self, chunk_size):
        assert chunk_size > 0
        if self.body:
            self.bytes_read += len(self.body)
            yield self.body

    def close(self):
        self.closed = True


class SyntheticDiagnosticSession:
    def __init__(self, responses, calls):
        self.responses = responses
        self.calls = calls

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        response = self.responses(url)
        response.url = url
        return response

    def close(self):
        return None


class DetectCmsSecurityTests(unittest.TestCase):
    def test_detects_hubspot_script_by_parsed_hostname(self):
        trusted_script_urls = [
            "https://hs-scripts.com/123.js",
            "https://app.hs-scripts.com/embed.js",
            "//HS-SCRIPTS.COM/forms.js",
        ]
        for src in trusted_script_urls:
            with self.subTest(src=src):
                result = detect_cms(f'<html><script src="{src}"></script></html>')

                self.assertEqual(result["cms"], "hubspot")
                self.assertIn("hubspot_scripts", result["signals"])

    def test_does_not_detect_hubspot_from_untrusted_url_substrings(self):
        untrusted_script_urls = [
            "https://attacker.example/path/hs-scripts.com/123.js",
            "https://hs-scripts.com.attacker.example/123.js",
            "https://attacker-hs-scripts.com/123.js",
            "https://attacker.example/?next=https%3A%2F%2Fhs-scripts.com",
            "https://hs-scripts.com@attacker.example/123.js",
        ]
        for src in untrusted_script_urls:
            with self.subTest(src=src):
                result = detect_cms(f'<html><script src="{src}"></script></html>')

                self.assertNotEqual(result["cms"], "hubspot")
                self.assertNotIn("hubspot_scripts", result["signals"])


def test_spa_diagnostic_executes_js_through_pinned_budget_and_rejects_unlisted_origin(monkeypatch):
    origin = "https://spa.example"
    homepage = f"{origin}/"
    script = f"{origin}/assets/app.js"
    api = f"{origin}/api/catalog?page=1"
    external = "https://cdn-unapproved.example/tracker.js"
    html = '<html><body><div id="app"></div><script src="/assets/app.js"></script></body></html>'
    javascript = (
        "fetch('/api/catalog?page=1').then(r => r.json()).then(items => {"
        "document.querySelector('#app').innerHTML = "
        "'<a class=program href=/programas/nuevo>Programa nuevo</a>' + items[0].name;});"
        "document.querySelector('#app').dataset.transportGuard = "
        "String(typeof RTCPeerConnection) + ':' + String(typeof WebTransport);"
        "const diagnosticSocket = new WebSocket('wss://127.0.0.1:9/private');"
        "diagnosticSocket.addEventListener('close', () => {"
        "document.querySelector('#app').dataset.websocket = 'closed';});"
        "fetch('https://cdn-unapproved.example/tracker.js').catch(() => {});"
    ).encode()
    calls = []
    responses = {
        script: SyntheticDiagnosticResponse(
            script, 200, javascript, {"content-type": "application/javascript"}
        ),
        api: SyntheticDiagnosticResponse(
            api, 200, b'[{"name":"Synthetic catalog result"}]', {"content-type": "application/json"}
        ),
    }

    def response_for(url):
        if url not in responses:
            raise AssertionError(f"unexpected external transport URL: {url}")
        original = responses[url]
        return SyntheticDiagnosticResponse(url, original.status_code, original.body, dict(original.headers))

    monkeypatch.setattr(
        bounded_run_module,
        "public_url_resolve_entry",
        lambda _url, **_kwargs: "spa.example:443:93.184.216.34",
    )
    monkeypatch.setattr(
        diagnostics_module,
        "CurlSession",
        lambda **_kwargs: SyntheticDiagnosticSession(response_for, calls),
    )
    monkeypatch.setattr(diagnostics_module.time, "sleep", lambda _seconds: None)
    budget = DiagnosticRequestBudget()
    budget_token = _ACTIVE_DIAGNOSTIC_BUDGET.set(budget)
    origin_token = _ACTIVE_DIAGNOSTIC_ORIGIN.set(origin)
    try:
        result = _render_controlled_page(
            homepage,
            role="catalog_source",
            profile={"allowed_resource_origins": []},
            prefetched=(200, html, homepage),
        )
    finally:
        _ACTIVE_DIAGNOSTIC_BUDGET.reset(budget_token)
        _ACTIVE_DIAGNOSTIC_ORIGIN.reset(origin_token)

    assert result["status"] == 200
    assert "Programa nuevo" in result["html"], (
        f"rendered diagnostic did not execute the fixture bundle; result={result}; "
        f"transport_urls={[url for url, _kwargs in calls]}"
    )
    assert "Synthetic catalog result" in result["html"]
    assert 'data-transport-guard="undefined:undefined"' in result["html"]
    assert 'data-websocket="closed"' in result["html"]
    assert result["cache_hits"] >= 1
    assert result["required_blocks"] >= 1
    assert external not in [url for url, _kwargs in calls]
    assert [url for url, _kwargs in calls] == [script, api]
    assert budget.browser_route_requests == (
        budget.browser_controlled_routes + budget.browser_rejected_routes
    )
    assert budget.browser_cache_hits >= 1
    assert budget.browser_websocket_attempts == 1
    assert budget.browser_websocket_blocked == 1
    assert budget.browser_transport_guarded is True
    assert budget.transport_controls_verified() is True


def test_transport_verification_fails_for_unaccounted_or_unavailable_browser_guards():
    budget = DiagnosticRequestBudget()
    budget.requests = 1
    budget.target_validations = 1
    budget.transport_starts = 1
    budget.completed_responses = 1
    budget.browser_transport_used = True

    assert budget.transport_controls_verified() is False
    budget.browser_transport_guarded = True
    assert budget.transport_controls_verified() is True

    budget.browser_websocket_attempts = 1
    assert budget.transport_controls_verified() is False
    budget.browser_websocket_blocked = 1
    assert budget.transport_controls_verified() is True
    budget.browser_websocket_errors = 1
    assert budget.transport_controls_verified() is False


def test_spa_diagnostic_fetches_exact_allowlisted_public_subresource_origin(monkeypatch):
    origin = "https://spa.example"
    homepage = f"{origin}/"
    cdn_script = "https://cdn.spa.example/assets/app.js"
    html = (
        '<html><body><main id="app"></main>'
        f'<script src="{cdn_script}"></script></body></html>'
    )
    calls = []
    session_options = []

    def response_for(url):
        if url != cdn_script:
            raise AssertionError("only the reviewed CDN subresource may be fetched")
        return SyntheticDiagnosticResponse(
            url,
            200,
            b"document.querySelector('#app').textContent = 'Allowlisted catalog';",
            {"content-type": "application/javascript"},
        )

    def session_factory(**kwargs):
        session_options.append(kwargs)
        return SyntheticDiagnosticSession(response_for, calls)

    monkeypatch.setattr(
        bounded_run_module,
        "public_url_resolve_entry",
        lambda url, **_kwargs: (
            "cdn.spa.example:443:93.184.216.34"
            if "cdn.spa.example" in url
            else "spa.example:443:93.184.216.34"
        ),
    )
    monkeypatch.setattr(diagnostics_module, "CurlSession", session_factory)
    monkeypatch.setattr(diagnostics_module.time, "sleep", lambda _seconds: None)
    budget = DiagnosticRequestBudget()
    budget_token = _ACTIVE_DIAGNOSTIC_BUDGET.set(budget)
    origin_token = _ACTIVE_DIAGNOSTIC_ORIGIN.set(origin)
    try:
        result = _render_controlled_page(
            homepage,
            role="catalog_source",
            profile={"allowed_resource_origins": ["https://cdn.spa.example"]},
            prefetched=(200, html, homepage),
        )
    finally:
        _ACTIVE_DIAGNOSTIC_BUDGET.reset(budget_token)
        _ACTIVE_DIAGNOSTIC_ORIGIN.reset(origin_token)

    assert result["status"] == 200
    assert "Allowlisted catalog" in result["html"]
    assert [url for url, _kwargs in calls] == [cdn_script]
    assert session_options[0]["trust_env"] is False
    assert session_options[0]["verify"] is True
    assert session_options[0]["allow_redirects"] is False
    assert session_options[0]["retry"] == 0
    assert session_options[0]["curl_options"]
    assert budget.transport_controls_verified() is True


def test_allowlisted_subresource_redirect_cannot_escape_its_origin(monkeypatch):
    origin = "https://spa.example"
    homepage = f"{origin}/"
    cdn_script = "https://cdn.spa.example/assets/app.js"
    unsafe_redirect = "https://other-cdn.example/app.js"
    html = (
        '<html><body><main id="app"></main>'
        f'<script src="{cdn_script}"></script></body></html>'
    )
    calls = []
    response = SyntheticDiagnosticResponse(
        cdn_script,
        302,
        b"",
        {"location": unsafe_redirect, "content-type": "application/javascript"},
    )

    def response_for(url):
        if url != cdn_script:
            raise AssertionError("cross-origin redirect must be rejected before transport")
        return SyntheticDiagnosticResponse(
            url, response.status_code, response.body, dict(response.headers)
        )

    monkeypatch.setattr(
        bounded_run_module,
        "public_url_resolve_entry",
        lambda url, **_kwargs: (
            "cdn.spa.example:443:93.184.216.34"
            if "cdn.spa.example" in url
            else "spa.example:443:93.184.216.34"
        ),
    )
    monkeypatch.setattr(
        diagnostics_module,
        "CurlSession",
        lambda **_kwargs: SyntheticDiagnosticSession(response_for, calls),
    )
    monkeypatch.setattr(diagnostics_module.time, "sleep", lambda _seconds: None)
    budget = DiagnosticRequestBudget()
    budget_token = _ACTIVE_DIAGNOSTIC_BUDGET.set(budget)
    origin_token = _ACTIVE_DIAGNOSTIC_ORIGIN.set(origin)
    try:
        result = _render_controlled_page(
            homepage,
            role="catalog_source",
            profile={"allowed_resource_origins": ["https://cdn.spa.example"]},
            prefetched=(200, html, homepage),
        )
    finally:
        _ACTIVE_DIAGNOSTIC_BUDGET.reset(budget_token)
        _ACTIVE_DIAGNOSTIC_ORIGIN.reset(origin_token)

    assert result["status"] == 200
    assert result["required_blocks"] >= 1
    assert [url for url, _kwargs in calls] == [cdn_script]
    assert unsafe_redirect not in [url for url, _kwargs in calls]
    assert budget.transport_controls_verified() is True


def test_browser_diagnostic_stops_after_http_429_without_reading_or_retrying(monkeypatch):
    origin = "https://blocked.example"
    homepage = f"{origin}/"
    script = f"{origin}/app.js"
    html = '<html><body><div id="app"></div><script src="/app.js"></script></body></html>'
    calls = []
    body_read = []

    def response_for(url):
        if url == script:
            response = SyntheticDiagnosticResponse(
                url, 429, b"large body must remain unread", {"content-type": "application/javascript"}
            )
            body_read.append(response)
            return response
        raise AssertionError("the blocked institution must not receive another request")

    monkeypatch.setattr(
        bounded_run_module,
        "public_url_resolve_entry",
        lambda _url, **_kwargs: "blocked.example:443:93.184.216.34",
    )
    monkeypatch.setattr(
        diagnostics_module,
        "CurlSession",
        lambda **_kwargs: SyntheticDiagnosticSession(response_for, calls),
    )
    monkeypatch.setattr(diagnostics_module.time, "sleep", lambda _seconds: None)
    budget = DiagnosticRequestBudget()
    budget_token = _ACTIVE_DIAGNOSTIC_BUDGET.set(budget)
    origin_token = _ACTIVE_DIAGNOSTIC_ORIGIN.set(origin)
    try:
        result = _render_controlled_page(
            homepage,
            role="catalog_source",
            profile={"allowed_resource_origins": []},
            prefetched=(200, html, homepage),
        )
    finally:
        _ACTIVE_DIAGNOSTIC_BUDGET.reset(budget_token)
        _ACTIVE_DIAGNOSTIC_ORIGIN.reset(origin_token)

    assert result["source_blocked"] is True
    assert result["block_http_status"] == 429
    assert len(calls) == 1 and calls[0][0] == script
    assert body_read[0].bytes_read == 0
    assert body_read[0].closed is True

    def test_spa_classification_does_not_enable_stealth_or_bypass(self):
        template = assign_template({
            "cms": {"cms": "react"},
            "js": {"needs_js": True},
        })
        self.assertEqual(template["site_type"], "spa_js_heavy")
        self.assertFalse(template["requires_stealth"])
        self.assertFalse(template["requires_cloudflare_bypass"])

    def test_short_static_page_is_not_misclassified_as_javascript_required(self):
        result = detect_js_required(
            "<html><body><main><h1>Información institucional</h1></main></body></html>"
        )

        self.assertFalse(result["needs_js"])
        self.assertIn("short_body", result["signals"])

    def test_empty_scripted_application_root_is_javascript_required(self):
        result = detect_js_required(
            '<html><body><main id="catalog"></main><script src="/assets/catalog.js"></script></body></html>'
        )

        self.assertTrue(result["needs_js"])
        self.assertTrue({"empty_app_root", "script_present"}.issubset(result["signals"]))

    def test_catalog_links_keep_document_order_and_separate_noise(self):
        html = """
        <a href="/programas/">Programas</a>
        <a href="/programas/data/">Data</a>
        <a href="/noticias/launch/">News</a>
        <a href="/programas/ai/">AI</a>
        <a href="/login/">Login</a>
        """
        result = detect_catalog_links(html, "https://uni.example/")
        self.assertEqual(result["catalog_urls"], [
            "https://uni.example/programas/",
        ])
        self.assertEqual(result["detail_urls"], [
            "https://uni.example/programas/data/",
            "https://uni.example/programas/ai/",
        ])
        self.assertEqual(result["noise_urls_detected"], [
            "https://uni.example/noticias/launch/",
            "https://uni.example/login/",
        ])

    def test_ecommerce_prefers_pagination_mode_when_catalog_pattern_exists(self):
        self.assertEqual(
            suggest_discovery_mode(
                {"found": False, "urls": []},
                {"catalog_urls": ["https://shop.example/cursos/1"], "pagination_patterns": ["https://shop.example/page/{page}"]},
                site_type="ecommerce",
            ),
            "paginated_catalog",
        )

    def test_profile_diagnosis_uses_same_url_policy_and_flags_seed_conflict(self):
        result = evaluate_discovery_candidates(
            "https://ulima.example/",
            {
                "seed_urls": ["https://ulima.example/pregrado/"],
                "exclusion_patterns": ["/pregrado/"],
                "allowed_url_patterns": [],
            },
            source_urls=["https://ulima.example/sitemap.xml"],
            detail_urls=[
                "https://ulima.example/pregrado/curso-a/",
                "https://ulima.example/programas/curso-b/",
            ],
        )
        self.assertEqual(result["source_urls"], ["https://ulima.example/sitemap.xml"])
        self.assertEqual(result["accepted_detail_urls"], ["https://ulima.example/programas/curso-b"])
        self.assertEqual(result["status"], "review_required")
        self.assertEqual(result["seed_conflicts"][0]["reason"], "excluded_by_profile")

    def test_inferred_exact_noise_exclusion_does_not_conflict_with_verified_courses(self):
        source = "https://uni.example/sitemap.xml"
        detail_a = "https://uni.example/programas/curso-a"
        detail_b = "https://uni.example/programas/curso-b"
        news = "https://uni.example/noticias/launch"
        result = evaluate_discovery_candidates(
            "https://uni.example/",
            {
                "seed_urls": [source],
                "exclusion_patterns": [news],
                "allowed_url_patterns": ["re:^/programas/"],
            },
            source_urls=[source],
            detail_urls=[detail_a, detail_b, news],
            verified_detail_urls=[detail_a, detail_b],
        )

        self.assertEqual(result["status"], "verified")
        self.assertEqual(result["accepted_detail_urls"], [detail_a, detail_b])
        self.assertFalse(result["verification"]["reasons"])

    def test_proposed_exclusion_of_positive_detail_requires_review(self):
        source = "https://uni.example/sitemap.xml"
        detail = "https://uni.example/programas/curso-a"
        result = evaluate_discovery_candidates(
            "https://uni.example/",
            {
                "seed_urls": [source],
                "exclusion_patterns": ["/programas/"],
                "allowed_url_patterns": ["re:^/programas/"],
            },
            source_urls=[source],
            detail_urls=[detail, "https://uni.example/programas/curso-b"],
            verified_detail_urls=[detail],
        )

        self.assertEqual(result["status"], "review_required")
        self.assertIn(
            "verified_detail_conflicts_with_profile",
            result["verification"]["reasons"],
        )

    def test_detects_hubspot_mentioned_in_visible_page_text(self):
        result = detect_cms("<html><body>Powered by HubSpot</body></html>")

        self.assertEqual(result["cms"], "hubspot")
        self.assertIn("hubspot_scripts", result["signals"])

    def test_ignores_malformed_script_urls_without_aborting_diagnosis(self):
        for src in ("https://[broken", "//[broken"):
            with self.subTest(src=src):
                result = detect_cms(f'<html><script src="{src}"></script></html>')

                self.assertEqual(result["cms"], "html_puro")
                self.assertNotIn("hubspot_scripts", result["signals"])


if __name__ == "__main__":
    unittest.main()
