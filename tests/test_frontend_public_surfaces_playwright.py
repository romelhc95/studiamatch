from __future__ import annotations

import contextlib
import http.server
import json
import os
import socket
import threading
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

from playwright.sync_api import Browser, Page, expect, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
WEB_OUT = ROOT / "web" / "out"
COURSE_ID = "00000000-0000-0000-0000-000000000001"
COURSE_ID_UPPER = COURSE_ID.upper()
COURSE_ID_2 = "00000000-0000-0000-0000-000000000002"
COURSE_ID_3 = "00000000-0000-0000-0000-000000000003"
COURSE_ID_4 = "00000000-0000-0000-0000-000000000004"
LEADS_ENDPOINT = "".join(["/rest/v1", "/leads"])
MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
EXPECTED_APIKEY = "sb_publishable_ci_test"
COURSE_PUBLIC_FIELDS = "id,name,slug,url,institution_id,price_pen,price_status,mode,course_type,category_id,duration,start_date_text,description_long,syllabus,target_audience,requirements,certification,benefits,objectives,expected_monthly_salary,seniority_level,roi_months,address,region,is_active,is_verified,brochure_url,start_date,created_at,updated_at"


def configured_supabase_test_origin() -> str:
    raw = os.environ.get("SUPABASE_TEST_ORIGIN", "http://127.0.0.1:54321")
    parsed = urlsplit(raw)
    assert parsed.scheme == "http"
    assert parsed.hostname == "127.0.0.1"
    assert parsed.port is not None
    assert not parsed.username
    assert not parsed.password
    assert parsed.path in {"", "/"}
    assert not parsed.query
    assert not parsed.fragment
    return f"http://127.0.0.1:{parsed.port}"


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
    "Access-Control-Allow-Methods": "GET",
}


COURSE = {
    "id": COURSE_ID,
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
    "start_date_text": "Consultar",
    "category": "Tecnologia",
    "description_long": "Programa publico de prueba para build local.",
    "syllabus": "Modulo 1\nModulo 2",
    "target_audience": "Personas interesadas en tecnologia.",
    "requirements": "Conocimientos basicos.",
    "is_active": True,
    "is_verified": True,
    "roi_months": 2.5,
    "expected_monthly_salary": 4500,
    "institutions": {"name": "PUCP", "slug": "pucp"},
    "categories": {"name": "Tecnologia"},
}
INSTITUTION = {"id": COURSE["institution_id"], "name": "PUCP", "slug": "pucp"}


def query_dict(query: str) -> dict[str, str]:
    return dict(parse_qsl(query, keep_blank_values=True))


def valid_course_compare_query(params: dict[str, str]) -> bool:
    ids = params.get("id", "")
    return (
        ids.startswith("in.(")
        and ids.endswith(")")
        and params
        == {
            "id": ids,
            "select": f"{COURSE_PUBLIC_FIELDS},institutions(name,slug),categories(name)",
            "is_active": "eq.true",
            "is_verified": "eq.true",
        }
        and all(part in {COURSE_ID, COURSE_ID_2, COURSE_ID_3} for part in ids[4:-1].split(","))
        and COURSE_ID_4 not in ids
    )


def allowed_data_query(path: str, query: str) -> bool:
    params = query_dict(query)
    if path == "/rest/v1/institutions":
        return params == {"select": "id,name,slug"}
    if path == "/rest/v1/ratings":
        return params == {
            "course_id": f"eq.{COURSE_ID}",
            "select": "id,course_id,rating_value,user_nickname,created_at",
        }
    if path == "/rest/v1/reviews":
        return params == {
            "course_id": f"eq.{COURSE_ID}",
            "select": "id,course_id,content,user_nickname,created_at",
            "order": "created_at.desc",
        }
    if path != "/rest/v1/courses":
        return False
    if valid_course_compare_query(params):
        return True
    return params in (
        {
            "is_active": "eq.true",
            "is_verified": "eq.true",
            "select": f"{COURSE_PUBLIC_FIELDS},categories(name),institutions(name,slug)",
            "order": "created_at.desc",
        },
        {
            "slug": "eq.estudios-generales",
            "institutions.slug": "eq.pucp",
            "select": f"{COURSE_PUBLIC_FIELDS},institutions!inner(name,slug),categories(name)",
            "is_active": "eq.true",
            "is_verified": "eq.true",
        },
        {
            "url": "ilike.*estudios-generales*",
            "institutions.slug": "eq.pucp",
            "select": f"{COURSE_PUBLIC_FIELDS},institutions!inner(name,slug),categories(name)",
            "is_active": "eq.true",
            "is_verified": "eq.true",
            "limit": "1",
        },
        {
            "slug": "ilike.*estudios*generales*",
            "institutions.slug": "eq.pucp",
            "select": f"{COURSE_PUBLIC_FIELDS},institutions!inner(name,slug),categories(name)",
            "is_active": "eq.true",
            "is_verified": "eq.true",
            "limit": "1",
        },
        {
            "category_id": f"eq.{COURSE['category_id']}",
            "id": f"neq.{COURSE_ID}",
            "is_active": "eq.true",
            "is_verified": "eq.true",
            "limit": "3",
            "select": f"{COURSE_PUBLIC_FIELDS},institutions(name,slug)",
        },
    )


def data_body(path: str, query: str) -> str:
    if path == "/rest/v1/institutions":
        return json.dumps([INSTITUTION])
    if path in {"/rest/v1/ratings", "/rest/v1/reviews"}:
        return "[]"
    params = query_dict(query)
    if path == "/rest/v1/courses" and params.get("category_id"):
        return "[]"
    return json.dumps([COURSE])


def install_public_routes(
    page: Page,
    unexpected: list[str],
    canaries: list[str],
    data_requests: list[str],
    static_origin: str,
) -> None:
    def block_or_fulfill_canary(route, label: str, url: str) -> None:
        if "__wp03_canary" in url:
            canaries.append(label)
            route.fulfill(status=204, headers=ACCESS_CONTROL_HEADERS, body="")
        else:
            unexpected.append(f"{label} {url}")
            route.abort("blockedbyclient")

    def handle(route):
        request = route.request
        parsed = urlsplit(request.url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        path = parsed.path

        if path == LEADS_ENDPOINT or path.startswith("/rest/v1/leads"):
            block_or_fulfill_canary(route, f"FORBIDDEN_LEADS_ENDPOINT {request.method}", request.url)
            return
        if path.startswith("/functions/v1") or "send-lead-emails" in path or "email_log" in path:
            block_or_fulfill_canary(route, f"FORBIDDEN_EMAIL_EGRESS {request.method}", request.url)
            return
        if request.method in MUTATING_METHODS:
            block_or_fulfill_canary(route, f"FORBIDDEN_MUTATION {request.method}", request.url)
            return
        if parsed.scheme not in {"http", "https"}:
            block_or_fulfill_canary(route, f"FORBIDDEN_PROTOCOL {request.method}", request.url)
            return
        if origin == static_origin:
            if request.method not in {"GET", "HEAD"}:
                block_or_fulfill_canary(route, f"FORBIDDEN_STATIC_METHOD {request.method}", request.url)
                return
            route.continue_()
            return
        if "/rest/v1/" not in path:
            block_or_fulfill_canary(route, f"UNEXPECTED_EGRESS {request.method}", request.url)
            return
        if origin != SUPABASE_TEST_ORIGIN:
            block_or_fulfill_canary(route, f"WRONG_SUPABASE_ORIGIN {request.method}", request.url)
            return
        if request.method not in {"GET", "HEAD"}:
            block_or_fulfill_canary(route, f"FORBIDDEN_DATA_METHOD {request.method}", request.url)
            return
        headers = request.headers
        if "authorization" in headers:
            block_or_fulfill_canary(route, f"FORBIDDEN_AUTHORIZATION {request.method}", request.url)
            return
        if headers.get("apikey") != EXPECTED_APIKEY:
            block_or_fulfill_canary(route, f"FORBIDDEN_APIKEY {request.method}", request.url)
            return
        if not allowed_data_query(path, parsed.query):
            block_or_fulfill_canary(route, f"FORBIDDEN_QUERY {request.method}", request.url)
            return
        data_requests.append(request.url)
        route.fulfill(
            status=200,
            headers=ACCESS_CONTROL_HEADERS,
            content_type="application/json",
            body=data_body(path, parsed.query),
        )

    page.route("**/*", handle)


def assert_no_horizontal_overflow(page: Page) -> None:
    metrics = page.evaluate(
        """() => ({
            scrollWidth: document.documentElement.scrollWidth,
            clientWidth: document.documentElement.clientWidth,
        })"""
    )
    assert metrics["scrollWidth"] <= metrics["clientWidth"] + 1, metrics


def assert_visible_boxes(page: Page) -> None:
    boxes = page.evaluate(
        """() => {
            const selectors = 'h1,h2,h3,input,button,[role="tab"],article,[data-compare-bar-link]';
            return Array.from(document.querySelectorAll(selectors))
              .filter((el) => {
                const style = getComputedStyle(el);
                const rect = el.getBoundingClientRect();
                return style.visibility !== 'hidden' && style.display !== 'none' && rect.width > 0 && rect.height > 0;
              })
              .map((el) => {
                const rect = el.getBoundingClientRect();
                return { tag: el.tagName, text: (el.textContent || el.getAttribute('aria-label') || '').slice(0, 80), x: rect.x, width: rect.width };
              });
        }"""
    )
    viewport_width = page.viewport_size["width"] if page.viewport_size else 0
    for box in boxes:
        assert box["x"] >= -1, box
        assert box["x"] + box["width"] <= viewport_width + 1, box
    focused = page.evaluate(
        """() => {
            const el = document.activeElement;
            if (!el || el === document.body) return null;
            const rect = el.getBoundingClientRect();
            return { tag: el.tagName, text: (el.textContent || el.getAttribute('aria-label') || '').slice(0, 80), x: rect.x, y: rect.y, width: rect.width, height: rect.height, viewportWidth: innerWidth, viewportHeight: innerHeight };
        }"""
    )
    if focused:
        assert focused["x"] >= -1, focused
        assert focused["x"] + focused["width"] <= focused["viewportWidth"] + 1, focused
        assert focused["y"] >= -1, focused
        assert focused["y"] + focused["height"] <= focused["viewportHeight"] + 1, focused


def assert_no_lead_controls(page: Page) -> None:
    expect(page.locator("[data-pii-control]")).to_have_count(0)
    expect(page.locator("[data-lead-capture-form]")).to_have_count(0)
    expect(page.locator('[id^="home-lead-"]')).to_have_count(0)
    expect(page.locator('[id^="detail-lead-"]')).to_have_count(0)
    expect(page.get_by_text("Solicitar Info")).to_have_count(0)
    expect(page.get_by_text("Solicitar Asesor")).to_have_count(0)
    expect(page.get_by_label("Email", exact=False)).to_have_count(0)
    expect(page.get_by_label("Telefono", exact=False)).to_have_count(0)
    expect(page.get_by_label("Teléfono", exact=False)).to_have_count(0)
    expect(page.get_by_label("WhatsApp", exact=False)).to_have_count(0)


def record_request_failure(request, request_failures: list[str]) -> None:
    if "__wp03_canary" in request.url:
        return
    failure = request.failure or "unknown failure"
    request_failures.append(f"{request.method} {request.url} {failure}")


def new_public_page(
    browser: Browser,
    unexpected: list[str],
    canaries: list[str],
    data_requests: list[str],
    request_failures: list[str],
    response_errors: list[str],
    console_errors: list[str],
    page_errors: list[str],
    websockets: list[str],
    static_origin: str,
    init_script: str = "localStorage.clear();",
    viewport: dict[str, int] | None = None,
) -> Page:
    page = browser.new_page(viewport=viewport or {"width": 375, "height": 667})
    page.add_init_script(init_script)
    install_public_routes(page, unexpected, canaries, data_requests, static_origin)
    page.on("requestfailed", lambda request: record_request_failure(request, request_failures))
    page.on(
        "response",
        lambda response: response_errors.append(f"{response.status} {response.url}")
        if response.status >= 400 and "__wp03_canary" not in response.url
        else None,
    )
    page.on(
        "console",
        lambda message: console_errors.append(message.text)
        if message.type in {"error", "warning"} and "__wp03_canary_ws" not in message.text
        else None,
    )
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    page.on(
        "websocket",
        lambda ws: canaries.append("FORBIDDEN_WEBSOCKET")
        if "__wp03_canary_ws" in ws.url
        else websockets.append(ws.url),
    )
    return page


def run_egress_canaries(page: Page, base_url: str) -> None:
    canary_calls = [
        (f"{base_url}/rest/v1/leads?__wp03_canary=leads", {"method": "POST"}),
        (f"{base_url}/__wp03_canary_static", {"method": "POST"}),
        (
            f"http://127.0.0.2:{urlsplit(SUPABASE_TEST_ORIGIN).port}/rest/v1/courses?__wp03_canary=wrong-host",
            {"headers": {"apikey": EXPECTED_APIKEY}},
        ),
        (
            f"{SUPABASE_TEST_ORIGIN}/rest/v1/courses?__wp03_canary=authorization",
            {"headers": {"apikey": EXPECTED_APIKEY, "Authorization": "Bearer blocked"}},
        ),
        (
            f"{SUPABASE_TEST_ORIGIN}/rest/v1/courses?select=id&__wp03_canary=query",
            {"headers": {"apikey": EXPECTED_APIKEY}},
        ),
        (
            f"{SUPABASE_TEST_ORIGIN}/rest/v1/courses?__wp03_canary=mutation",
            {"method": "PATCH", "headers": {"apikey": EXPECTED_APIKEY}},
        ),
    ]
    for url, options in canary_calls:
        page.evaluate("""async ([url, options]) => fetch(url, options).catch(() => null)""", [url, options])
    page.evaluate(
        """(url) => {
            const socket = new WebSocket(url);
            socket.addEventListener('error', () => socket.close());
        }""",
        base_url.replace("http://", "ws://") + "/__wp03_canary_ws",
    )
    page.wait_for_timeout(250)


def assert_public_page(page: Page) -> None:
    assert_no_horizontal_overflow(page)
    assert_visible_boxes(page)
    assert_no_lead_controls(page)


def test_public_static_export_has_no_lead_capture_even_with_hostile_flag() -> None:
    unexpected: list[str] = []
    canaries: list[str] = []
    data_requests: list[str] = []
    request_failures: list[str] = []
    response_errors: list[str] = []
    console_errors: list[str] = []
    page_errors: list[str] = []
    websockets: list[str] = []

    with static_server(WEB_OUT) as base_url:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()

            home_page = new_public_page(
                browser,
                unexpected,
                canaries,
                data_requests,
                request_failures,
                response_errors,
                console_errors,
                page_errors,
                websockets,
                base_url,
            )
            run_egress_canaries(home_page, base_url)
            home_page.goto(f"{base_url}/")
            home_page.wait_for_load_state("networkidle")
            assert_public_page(home_page)
            expect(home_page.get_by_role("link", name="Explorar programas")).to_be_visible()
            search = home_page.get_by_label("Búsqueda")
            search.fill("Estudios")
            price = home_page.get_by_label("Precio máximo")
            price.fill("2000")
            expect(home_page.get_by_text("Estudios Generales").first).to_be_visible()
            more_filters = home_page.get_by_role("button", name="Más filtros")
            expect(more_filters).to_have_attribute("aria-expanded", "false")
            more_filters.focus()
            home_page.keyboard.press("Enter")
            expect(more_filters).to_have_attribute("aria-expanded", "true")
            tipo_button = home_page.get_by_role("button", name="Tipo")
            expect(tipo_button).to_be_visible()
            expect(tipo_button).to_be_focused()
            tipo_button.click()
            expect(tipo_button).to_have_attribute("aria-expanded", "true")
            home_page.keyboard.press("Escape")
            expect(tipo_button).to_have_attribute("aria-expanded", "false")
            expect(tipo_button).to_be_focused()
            home_page.keyboard.press("Escape")
            expect(more_filters).to_have_attribute("aria-expanded", "false")
            expect(more_filters).to_be_focused()
            assert_public_page(home_page)

            compare_toggle = home_page.get_by_role("button", name="Agregar Estudios Generales a la comparativa")
            box = compare_toggle.bounding_box()
            assert box and box["width"] >= 24 and box["height"] >= 24, box
            compare_toggle.focus()
            home_page.keyboard.press("Enter")
            selected_toggle = home_page.get_by_role("button", name="Quitar Estudios Generales de la comparativa")
            expect(selected_toggle).to_have_attribute("aria-pressed", "true")
            expect(selected_toggle).to_have_attribute("title", "Quitar Estudios Generales de la comparativa")
            expect(home_page.locator("[data-compare-bar-link]")).to_be_visible()
            assert_public_page(home_page)
            home_page.locator("[data-compare-bar-link]").click()
            home_page.wait_for_load_state("networkidle")
            expect(home_page).to_have_url(f"{base_url}/compare?ids={COURSE_ID}")
            expect(home_page.get_by_text("Comparativa de Programas")).to_be_visible()
            expect(home_page.get_by_text("Estudios Generales").first).to_be_visible()
            expect(home_page.get_by_role("link", name="Ver detalle").first).to_be_visible()
            assert_public_page(home_page)

            canonical_page = new_public_page(
                browser,
                unexpected,
                canaries,
                data_requests,
                request_failures,
                response_errors,
                console_errors,
                page_errors,
                websockets,
                base_url,
            )
            canonical_page.goto(
                f"{base_url}/compare?ids={COURSE_ID_UPPER},{COURSE_ID},bad-id,{COURSE_ID_2},{COURSE_ID_3},{COURSE_ID_4}"
            )
            canonical_page.wait_for_load_state("networkidle")
            expect(canonical_page).to_have_url(f"{base_url}/compare?ids={COURSE_ID},{COURSE_ID_2},{COURSE_ID_3}")
            assert COURSE_ID_4 not in "\n".join(data_requests)
            assert_public_page(canonical_page)

            compare_zoom_page = new_public_page(
                browser,
                unexpected,
                canaries,
                data_requests,
                request_failures,
                response_errors,
                console_errors,
                page_errors,
                websockets,
                base_url,
                viewport={"width": 188, "height": 334},
            )
            compare_zoom_page.goto(f"{base_url}/compare?ids={COURSE_ID}")
            compare_zoom_page.wait_for_load_state("networkidle")
            expect(compare_zoom_page.get_by_text("Estudios Generales").first).to_be_visible()
            assert_public_page(compare_zoom_page)

            courses_page = new_public_page(
                browser,
                unexpected,
                canaries,
                data_requests,
                request_failures,
                response_errors,
                console_errors,
                page_errors,
                websockets,
                base_url,
            )
            courses_page.goto(f"{base_url}/courses/")
            courses_page.wait_for_load_state("networkidle")
            expect(courses_page.get_by_text("Estudios Generales").first).to_be_visible()
            assert_public_page(courses_page)

            for viewport in ({"width": 375, "height": 667}, {"width": 188, "height": 334}):
                privacy_page = new_public_page(
                    browser,
                    unexpected,
                    canaries,
                    data_requests,
                    request_failures,
                    response_errors,
                    console_errors,
                    page_errors,
                    websockets,
                    base_url,
                    viewport=viewport,
                )
                privacy_page.goto(f"{base_url}/privacidad/")
                privacy_page.wait_for_load_state("networkidle")
                expect(privacy_page.get_by_role("heading", name="Política de Privacidad")).to_be_visible()
                assert_public_page(privacy_page)
                terms_page = new_public_page(
                    browser,
                    unexpected,
                    canaries,
                    data_requests,
                    request_failures,
                    response_errors,
                    console_errors,
                    page_errors,
                    websockets,
                    base_url,
                    viewport=viewport,
                )
                terms_page.goto(f"{base_url}/terminos/")
                terms_page.wait_for_load_state("networkidle")
                expect(terms_page.get_by_role("heading", name="Términos de Uso")).to_be_visible()
                assert_public_page(terms_page)

            detail_page = new_public_page(
                browser,
                unexpected,
                canaries,
                data_requests,
                request_failures,
                response_errors,
                console_errors,
                page_errors,
                websockets,
                base_url,
            )
            detail_page.goto(f"{base_url}/courses/pucp/estudios-generales/")
            detail_page.wait_for_load_state("networkidle")
            assert_public_page(detail_page)
            general_tab = detail_page.get_by_role("tab", name="GENERAL", exact=True)
            requisitos_tab = detail_page.get_by_role("tab", name="REQUISITOS", exact=True)
            reviews_tab = detail_page.get_by_role("tab", name="RESEÑAS (0)", exact=True)
            for tab in (general_tab, requisitos_tab, reviews_tab):
                controls = tab.get_attribute("aria-controls")
                assert controls
                expect(detail_page.locator(f"#{controls}")).to_have_count(1)
            expect(detail_page.locator('[role="tabpanel"]:not([hidden])')).to_have_count(1)
            expect(general_tab).to_have_attribute("aria-selected", "true")
            general_tab.focus()
            detail_page.keyboard.press("ArrowRight")
            expect(requisitos_tab).to_have_attribute("aria-selected", "true")
            expect(requisitos_tab).to_be_focused()
            detail_page.keyboard.press("End")
            expect(reviews_tab).to_have_attribute("aria-selected", "true")
            expect(reviews_tab).to_be_focused()
            detail_page.keyboard.press("Home")
            expect(general_tab).to_have_attribute("aria-selected", "true")
            expect(general_tab).to_be_focused()
            detail_page.keyboard.press("Tab")
            expect(general_tab).not_to_be_focused()
            for tab in (general_tab, requisitos_tab, reviews_tab):
                tab.click()
                expect(detail_page.locator('[role="tabpanel"]:not([hidden])')).to_have_count(1)
                assert_public_page(detail_page)
            detail_compare = detail_page.get_by_role("button", name="Agregar Estudios Generales a la comparativa")
            detail_compare.focus()
            detail_page.keyboard.press("Enter")
            selected_detail_compare = detail_page.get_by_role("button", name="Quitar Estudios Generales de la comparativa")
            expect(selected_detail_compare).to_have_attribute("aria-pressed", "true")
            expect(detail_page.get_by_role("link", name="Ver comparativa")).to_be_visible()

            zoom_detail = new_public_page(
                browser,
                unexpected,
                canaries,
                data_requests,
                request_failures,
                response_errors,
                console_errors,
                page_errors,
                websockets,
                base_url,
                viewport={"width": 188, "height": 334},
            )
            zoom_detail.goto(f"{base_url}/courses/pucp/estudios-generales/")
            zoom_detail.wait_for_load_state("networkidle")
            for tab_name in ("GENERAL", "REQUISITOS", "RESEÑAS (0)"):
                zoom_detail.get_by_role("tab", name=tab_name, exact=True).click()
                assert_public_page(zoom_detail)

            malformed_storage_page = new_public_page(
                browser,
                unexpected,
                canaries,
                data_requests,
                request_failures,
                response_errors,
                console_errors,
                page_errors,
                websockets,
                base_url,
                init_script="localStorage.setItem('StudIAMatch_compare_list', '{not-json');",
            )
            malformed_storage_page.goto(f"{base_url}/")
            malformed_storage_page.wait_for_load_state("networkidle")
            expect(malformed_storage_page.locator("[data-compare-bar-link]")).to_have_count(0)

            oversized_storage_page = new_public_page(
                browser,
                unexpected,
                canaries,
                data_requests,
                request_failures,
                response_errors,
                console_errors,
                page_errors,
                websockets,
                base_url,
                init_script=f"""
                localStorage.setItem('StudIAMatch_compare_list', JSON.stringify([
                  {{id: '{COURSE_ID_UPPER}', name: '  Estudios Generales  ', extra: 'ignored'}},
                  {{id: '{COURSE_ID}', name: 'Duplicado'}},
                  {{id: '{COURSE_ID_2.upper()}', name: 'Segundo'}},
                  {{id: 'bad-id', name: 'Malo'}},
                  {{id: '{COURSE_ID_3}', name: 'Tercero'}},
                  {{id: '{COURSE_ID_4}', name: 'Cuarto'}}
                ]));
                """,
            )
            oversized_storage_page.goto(f"{base_url}/")
            oversized_storage_page.wait_for_load_state("networkidle")
            sanitized = oversized_storage_page.evaluate("JSON.parse(localStorage.getItem('StudIAMatch_compare_list'))")
            assert sanitized == [
                {"id": COURSE_ID, "name": "Estudios Generales"},
                {"id": COURSE_ID_2, "name": "Segundo"},
                {"id": COURSE_ID_3, "name": "Tercero"},
            ]

            zoom_page = new_public_page(
                browser,
                unexpected,
                canaries,
                data_requests,
                request_failures,
                response_errors,
                console_errors,
                page_errors,
                websockets,
                base_url,
                viewport={"width": 188, "height": 334},
            )
            zoom_page.goto(f"{base_url}/")
            zoom_page.wait_for_load_state("networkidle")
            assert_public_page(zoom_page)
            more_filters_zoom = zoom_page.get_by_role("button", name="Más filtros")
            more_filters_zoom.click()
            assert_public_page(zoom_page)
            zoom_page.get_by_role("button", name="Tipo").click()
            assert_public_page(zoom_page)
            zoom_page.get_by_label("Búsqueda").fill("Estudios")
            zoom_page.get_by_role("button", name="Agregar Estudios Generales a la comparativa").click()
            expect(zoom_page.locator("[data-compare-bar-link]")).to_be_visible()
            assert_public_page(zoom_page)

            browser.close()

    required_canaries = {
        "FORBIDDEN_LEADS_ENDPOINT POST",
        "FORBIDDEN_MUTATION POST",
        "WRONG_SUPABASE_ORIGIN GET",
        "FORBIDDEN_AUTHORIZATION GET",
        "FORBIDDEN_QUERY GET",
        "FORBIDDEN_MUTATION PATCH",
        "FORBIDDEN_WEBSOCKET",
    }
    assert required_canaries.issubset(set(canaries)), canaries
    assert unexpected == []
    assert request_failures == []
    assert response_errors == []
    assert console_errors == []
    assert page_errors == []
    assert websockets == []
