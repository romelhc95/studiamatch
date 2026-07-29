from __future__ import annotations

import contextlib
import http.server
import json
import os
import socket
import threading
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import Page, expect, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
WEB_OUT = ROOT / "web" / "out"


def configured_supabase_test_origin() -> str:
    raw = os.environ.get("SUPABASE_TEST_ORIGIN", "http://127.0.0.1:54321")
    parsed = urlsplit(raw)
    assert parsed.scheme in {"http", "https"}
    assert parsed.netloc
    assert parsed.path in {"", "/"}
    assert not parsed.query
    assert not parsed.fragment
    return f"{parsed.scheme}://{parsed.netloc}"


SUPABASE_TEST_ORIGIN = configured_supabase_test_origin()


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        return


@contextlib.contextmanager
def static_server(root: Path):
    assert root.exists(), "web/out must exist before running Playwright assertions"
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    handler = lambda *args, **kwargs: QuietHandler(*args, directory=str(root), **kwargs)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()
        thread.join(timeout=5)


ACCESS_CONTROL_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "apikey, content-type, prefer",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
}


def install_routes(
    page: Page,
    posts: list[dict],
    unexpected_rest: list[str],
    *,
    lead_status: int = 201,
    abort_lead_post: bool = False,
) -> None:
    course = {
        "id": "00000000-0000-0000-0000-000000000001",
        "name": "Estudios Generales",
        "slug": "estudios-generales",
        "url": "https://example.edu/programa/estudios-generales",
        "institution_id": "10000000-0000-0000-0000-000000000001",
        "price_pen": 1000,
        "price_status": "published",
        "mode": "Remoto",
        "course_type": "Curso",
        "category_id": "20000000-0000-0000-0000-000000000001",
        "duration": "3 meses",
        "category": "Tecnologia",
        "is_active": True,
        "is_verified": True,
        "institutions": {"name": "PUCP", "slug": "pucp"},
        "categories": {"name": "Tecnologia"},
    }

    def handle(route):
        request = route.request
        url = request.url
        parsed = urlsplit(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        path = parsed.path
        if "/rest/v1/" in path and origin != SUPABASE_TEST_ORIGIN:
            unexpected_rest.append(f"WRONG_SUPABASE_ORIGIN {request.method} {url}")
            route.abort("blockedbyclient")
        elif path == "/rest/v1/leads" and request.method == "OPTIONS":
            route.fulfill(status=204, headers=ACCESS_CONTROL_HEADERS, body="")
        elif path == "/rest/v1/leads" and request.method == "POST":
            if abort_lead_post:
                route.abort("failed")
                return
            assert request.headers.get("apikey") == "sb_publishable_ci_test"
            assert "authorization" not in request.headers
            payload = json.loads(request.post_data or "{}")
            assert set(payload).issubset(
                {
                    "first_name",
                    "last_name",
                    "email",
                    "whatsapp",
                    "source_page",
                    "type",
                    "course_id",
                    "area_interest",
                    "budget",
                    "modality",
                    "description",
                    "is_late_enrollment_request",
                }
            )
            posts.append(payload)
            route.fulfill(status=lead_status, headers=ACCESS_CONTROL_HEADERS, body="")
        elif path == "/rest/v1/courses":
            route.fulfill(
                status=200,
                headers=ACCESS_CONTROL_HEADERS,
                content_type="application/json",
                body=json.dumps([course]),
            )
        elif path == "/rest/v1/institutions":
            route.fulfill(
                status=200,
                headers=ACCESS_CONTROL_HEADERS,
                content_type="application/json",
                body=json.dumps([
                    {
                        "id": "10000000-0000-0000-0000-000000000001",
                        "name": "PUCP",
                        "slug": "pucp",
                    }
                ]),
            )
        elif path in {"/rest/v1/ratings", "/rest/v1/reviews"}:
            route.fulfill(status=200, headers=ACCESS_CONTROL_HEADERS, content_type="application/json", body="[]")
        elif "/rest/v1/" in path:
            unexpected_rest.append(f"{request.method} {url}")
            route.abort("blockedbyclient")
        elif url.startswith("http://127.0.0.1:"):
            route.continue_()
        else:
            unexpected_rest.append(f"UNEXPECTED_EGRESS {request.method} {url}")
            route.abort("blockedbyclient")

    page.route("**/*", handle)


def fill_home_form(page: Page) -> None:
    page.get_by_role("button", name="Solicitar asesoría").click()
    expect(page.locator('[data-lead-capture-surface="home-modal"]')).to_be_visible()
    page.locator('[data-pii-control="first_name"]').fill("Ada")
    page.locator('[data-pii-control="whatsapp"]').fill("999999999")
    page.locator('[data-pii-control="email"]').fill("ada@example.test")
    page.get_by_role("button", name="Confirmar solicitud").click()


def assert_home_validation_accessibility(page: Page) -> None:
    page.get_by_role("button", name="Solicitar asesoría").click()
    expect(page.locator('[data-lead-capture-surface="home-modal"]')).to_be_visible()
    page.locator('[data-pii-control="first_name"]').fill("Ada")
    page.locator('[data-pii-control="whatsapp"]').fill("123")
    page.locator('[data-pii-control="email"]').fill("ada@example.test")
    page.get_by_role("button", name="Confirmar solicitud").click()
    expect(page.locator("#home-lead-error")).to_contain_text("WhatsApp válido")
    whatsapp = page.locator("#home-lead-whatsapp")
    expect(whatsapp).to_have_attribute("aria-invalid", "true")
    expect(whatsapp).to_have_attribute("aria-describedby", "home-lead-error")
    expect(whatsapp).to_be_focused()


def fill_detail_form(page: Page) -> None:
    expect(page.locator('[data-lead-capture-form="course-detail"]')).to_be_visible()
    page.locator('#detail-lead-first-name').fill("Ada")
    page.locator('#detail-lead-whatsapp').fill("999999999")
    page.locator('#detail-lead-email').fill("ada@example.test")
    page.get_by_role("button", name="Confirmar Solicitud").click()


def assert_no_horizontal_overflow(page: Page) -> None:
    metrics = page.evaluate(
        """() => ({
            scrollWidth: document.documentElement.scrollWidth,
            clientWidth: document.documentElement.clientWidth,
        })"""
    )
    assert metrics["scrollWidth"] <= metrics["clientWidth"] + 1, metrics


def assert_no_horizontal_overflow_at_200_zoom(page: Page) -> None:
    session = page.context.new_cdp_session(page)
    session.send("Emulation.setPageScaleFactor", {"pageScaleFactor": 2})
    assert_no_horizontal_overflow(page)
    session.send("Emulation.setPageScaleFactor", {"pageScaleFactor": 1})


def assert_home_modal_keyboard_contract(page: Page) -> None:
    trigger = page.get_by_role("button", name="Solicitar asesoría")
    trigger.click()
    expect(page.locator('[data-lead-capture-surface="home-modal"]')).to_be_visible()
    expect(page.get_by_label("Cerrar formulario de contacto")).to_be_focused()
    page.keyboard.press("Shift+Tab")
    expect(page.get_by_role("button", name="Confirmar solicitud")).to_be_focused()
    page.keyboard.press("Tab")
    expect(page.get_by_label("Cerrar formulario de contacto")).to_be_focused()
    page.keyboard.press("Escape")
    expect(trigger).to_be_focused()


def assert_more_filters_no_overflow(page: Page) -> None:
    page.get_by_role("button", name="Más filtros").click()
    expect(page.get_by_role("button", name="Tipo")).to_be_visible()
    assert_no_horizontal_overflow(page)
    assert_no_horizontal_overflow_at_200_zoom(page)
    page.get_by_role("button", name="Más filtros").click()


def track_request_failures(page: Page, failures: list[str]) -> None:
    page.on(
        "requestfailed",
        lambda request: failures.append(
            f"{request.method} {request.url} {request.failure or 'unknown failure'}"
        ),
    )


def track_console_errors(page: Page, messages: list[str]) -> None:
    page.on("console", lambda message: messages.append(f"{message.type}: {message.text}"))


def test_lead_capture_static_export_local_only() -> None:
    expected = os.environ.get("LEAD_CAPTURE_EXPECTED", "disabled")
    assert expected in {"enabled", "disabled", "unset"}
    capture_enabled = expected == "enabled"
    posts: list[dict] = []
    unexpected_rest: list[str] = []
    request_failures: list[str] = []
    console_messages: list[str] = []

    with static_server(WEB_OUT) as base_url:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 375, "height": 667})
            track_request_failures(page, request_failures)
            track_console_errors(page, console_messages)
            install_routes(page, posts, unexpected_rest)

            page.goto(f"{base_url}/")
            page.wait_for_load_state("networkidle")
            assert_no_horizontal_overflow(page)
            assert_no_horizontal_overflow_at_200_zoom(page)
            assert_more_filters_no_overflow(page)
            if capture_enabled:
                assert_home_modal_keyboard_contract(page)
                fill_home_form(page)
                assert len(posts) == 1, {
                    "posts": posts,
                    "unexpected_rest": unexpected_rest,
                    "request_failures": request_failures,
                    "console_messages": console_messages,
                }
                expect(page.get_by_text("Enviado con éxito")).to_be_visible()
                expect(page.locator('[data-lead-capture-status="success"]')).to_be_focused()
            else:
                page.get_by_role("button", name="Solicitar asesoría").click()
                expect(page.locator('[data-lead-capture-surface="home-modal"][data-lead-capture-state="disabled"]')).to_be_visible()
                expect(page.locator('[data-lead-capture-form="home"]')).to_have_count(0)
                expect(page.locator('[data-pii-control]')).to_have_count(0)
                page.keyboard.press("Escape")
                expect(page.get_by_role("button", name="Solicitar asesoría")).to_be_focused()

            page.goto(f"{base_url}/courses/pucp/estudios-generales/")
            page.wait_for_load_state("networkidle")
            assert_no_horizontal_overflow(page)
            assert_no_horizontal_overflow_at_200_zoom(page)
            if capture_enabled:
                fill_detail_form(page)
                expect(page.get_by_text("Solicitud enviada")).to_be_visible()
                expect(page.locator('[data-lead-capture-status="success"]')).to_be_focused()
                assert len(posts) == 2
                assert {post["source_page"] for post in posts} == {"home", "detail"}
            else:
                expect(page.locator('[data-lead-capture-surface="course-detail"][data-lead-capture-state="disabled"]')).to_be_visible()
                expect(page.locator('[data-lead-capture-form="course-detail"]')).to_have_count(0)
                assert posts == []
            assert unexpected_rest == []

            browser.close()


def test_lead_capture_error_states_are_accessible_when_enabled() -> None:
    if os.environ.get("LEAD_CAPTURE_EXPECTED") != "enabled":
        return

    with static_server(WEB_OUT) as base_url:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()

            validation_posts: list[dict] = []
            validation_unexpected_rest: list[str] = []
            validation_page = browser.new_page(viewport={"width": 375, "height": 667})
            install_routes(validation_page, validation_posts, validation_unexpected_rest)
            validation_page.goto(f"{base_url}/")
            validation_page.wait_for_load_state("networkidle")
            assert_home_validation_accessibility(validation_page)
            assert validation_posts == []
            assert validation_unexpected_rest == []

            http_posts: list[dict] = []
            http_unexpected_rest: list[str] = []
            http_request_failures: list[str] = []
            http_console_messages: list[str] = []
            http_page = browser.new_page(viewport={"width": 375, "height": 667})
            track_request_failures(http_page, http_request_failures)
            track_console_errors(http_page, http_console_messages)
            install_routes(http_page, http_posts, http_unexpected_rest, lead_status=500)
            http_page.goto(f"{base_url}/")
            http_page.wait_for_load_state("networkidle")
            fill_home_form(http_page)
            expect(http_page.locator("#home-lead-error")).to_contain_text("No pudimos registrar la solicitud")
            expect(http_page.locator("#home-lead-error")).to_be_focused()
            assert len(http_posts) == 1, {
                "posts": http_posts,
                "unexpected_rest": http_unexpected_rest,
                "request_failures": http_request_failures,
                "console_messages": http_console_messages,
            }
            assert http_unexpected_rest == []

            network_posts: list[dict] = []
            network_unexpected_rest: list[str] = []
            network_request_failures: list[str] = []
            network_page = browser.new_page(viewport={"width": 375, "height": 667})
            track_request_failures(network_page, network_request_failures)
            install_routes(network_page, network_posts, network_unexpected_rest, abort_lead_post=True)
            network_page.goto(f"{base_url}/courses/pucp/estudios-generales/")
            network_page.wait_for_load_state("networkidle")
            fill_detail_form(network_page)
            expect(network_page.locator("#detail-lead-error")).to_contain_text("No pudimos registrar la solicitud")
            expect(network_page.locator("#detail-lead-error")).to_be_focused()
            assert network_posts == []
            assert network_unexpected_rest == []
            assert any("/rest/v1/leads" in failure for failure in network_request_failures)

            browser.close()


def test_playwright_routes_block_wrong_supabase_origin() -> None:
    posts: list[dict] = []
    unexpected_rest: list[str] = []

    with static_server(WEB_OUT) as base_url:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 375, "height": 667})
            install_routes(page, posts, unexpected_rest)
            page.goto(f"{base_url}/")
            page.evaluate(
                """async () => {
                    try {
                        await fetch('https://evil.example/rest/v1/leads', { method: 'POST' });
                    } catch (_error) {}
                }"""
            )
            assert posts == []
            assert unexpected_rest == [
                "WRONG_SUPABASE_ORIGIN POST https://evil.example/rest/v1/leads"
            ]
            browser.close()
