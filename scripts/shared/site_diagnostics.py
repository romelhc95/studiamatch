#!/usr/bin/env python3
"""Fase 121: Modulo compartido de diagnostico de sitios.

Extrae la logica de deteccion de diagnose_institution.py para que
pueda ser usada tanto por el script de diagnostico como por el
universal_harvester.py en modo auto-deteccion.

Uso:
    from shared.site_diagnostics import diagnose_site, assign_template
"""

import json
import re
import time
import asyncio
import contextvars
import xml.etree.ElementTree as ET
from urllib.parse import parse_qsl, urljoin, urlparse, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup
from curl_cffi import CurlOpt
from curl_cffi.requests import Session as CurlSession
# StudIAMatch-Docs: .context/componentes/utilidades_compartidas.md#responsabilidades-y-consumidores
try:
    from scripts.core.fg2_bounded_run import (
        InvalidControlledRun,
        UnsafePublicTarget,
        _normalize_url,
        profile_url_policy_rejection,
        validate_public_request_url,
        validate_public_url_shape,
        validate_public_redirect_target,
    )
except ModuleNotFoundError as exc:
    if exc.name != "scripts":
        raise
    from core.fg2_bounded_run import (
        InvalidControlledRun,
        UnsafePublicTarget,
        _normalize_url,
        profile_url_policy_rejection,
        validate_public_request_url,
        validate_public_url_shape,
        validate_public_redirect_target,
    )

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}
MAX_RESPONSE_BODY_BYTES = 2 * 1024 * 1024
RESPONSE_READ_CHUNK_BYTES = 64 * 1024
REDIRECT_STATUSES = {301, 302, 303, 307, 308}
DIAGNOSTIC_MAX_HTTP_REQUESTS = 20
DIAGNOSTIC_MAX_REDIRECTS = 3
DIAGNOSTIC_MAX_DETAIL_PROBES = 2


class ResponseBodyLimitExceeded(RuntimeError):
    """A response exceeded the bounded body used for site diagnostics."""


class DiagnosticBudgetExceeded(RuntimeError):
    """The initial profile diagnostic exhausted its bounded request budget."""


class DiagnosticRequestBudget:
    """Shared request count and per-origin pacing for one diagnostic pass."""

    def __init__(self, *, max_requests: int = DIAGNOSTIC_MAX_HTTP_REQUESTS) -> None:
        self.max_requests = max_requests
        self.requests = 0
        self._last_started: dict[str, float] = {}
        self.target_validations = 0
        self.transport_starts = 0
        self.completed_responses = 0
        self.redirect_hops = 0
        self.browser_route_requests = 0
        self.browser_controlled_routes = 0
        self.browser_rejected_routes = 0
        self.browser_cache_hits = 0
        self.browser_required_blocks = 0
        self.browser_internal_errors = 0
        self.browser_websocket_attempts = 0
        self.browser_websocket_blocked = 0
        self.browser_websocket_errors = 0
        self.browser_transport_used = False
        self.browser_transport_guarded = False

    def transport_controls_verified(self) -> bool:
        http_verified = bool(
            self.requests > 0
            and self.target_validations >= self.requests
            and self.transport_starts == self.requests
            and self.completed_responses == self.requests
        )
        browser_accounted = (
            self.browser_route_requests == 0
            or (
                self.browser_route_requests
                == self.browser_controlled_routes + self.browser_rejected_routes
                and self.browser_internal_errors == 0
            )
        )
        websocket_accounted = (
            self.browser_websocket_attempts == self.browser_websocket_blocked
            and self.browser_websocket_errors == 0
        )
        browser_guarded = not self.browser_transport_used or self.browser_transport_guarded
        return http_verified and browser_accounted and websocket_accounted and browser_guarded

    def reserve(self, url: str) -> None:
        validate_public_url_shape(url)
        parsed = urlparse(url)
        origin = f"{parsed.scheme.lower()}://{parsed.netloc.lower()}"
        if self.requests >= self.max_requests:
            raise DiagnosticBudgetExceeded("diagnostic request budget exhausted")
        now = time.monotonic()
        delay = self._last_started.get(origin, float("-inf")) + 5.0 - now
        if delay > 0:
            time.sleep(delay)
        self.requests += 1
        self._last_started[origin] = time.monotonic()


_ACTIVE_DIAGNOSTIC_BUDGET = contextvars.ContextVar("fg2_diagnostic_budget", default=None)
_ACTIVE_DIAGNOSTIC_ORIGIN = contextvars.ContextVar("fg2_diagnostic_origin", default=None)


def _read_bounded_response_text(response) -> str:
    body = bytearray()
    try:
        for chunk in response.iter_content(chunk_size=RESPONSE_READ_CHUNK_BYTES):
            if not chunk:
                continue
            if not isinstance(chunk, bytes):
                raise TypeError("response stream returned a non-byte chunk")
            if len(body) + len(chunk) > MAX_RESPONSE_BODY_BYTES:
                raise ResponseBodyLimitExceeded("response body exceeds the 2 MiB limit")
            body.extend(chunk)
        response.content = bytes(body)
        return response.text
    finally:
        response.close()


def _bounded_get(
    url: str,
    timeout: int,
    *,
    role: str = "catalog_source",
    profile: dict | None = None,
    origin_scope: str | None = None,
    include_payload: bool = False,
):
    """GET a public URL chain, pinning and bounding every HTTP hop."""
    # A reviewed browser subresource may use an exact public origin explicitly
    # allowed by its profile. Keep its redirect chain on that origin instead
    # of accidentally forcing it back to the institution's origin.
    expected_origin = origin_scope or _ACTIVE_DIAGNOSTIC_ORIGIN.get()
    _, resolve_entry = validate_public_request_url(url, expected_origin=expected_origin)
    if profile is not None:
        rejection = profile_url_policy_rejection(
            url,
            expected_origin or url,
            profile,
            role=role,
        )
        if rejection is not None:
            raise UnsafePublicTarget("diagnostic request rejected by shared URL policy")
    current_url = url
    budget = _ACTIVE_DIAGNOSTIC_BUDGET.get()
    if budget is not None:
        budget.target_validations += 1
    redirects_followed = 0
    max_redirects = DIAGNOSTIC_MAX_REDIRECTS
    while True:
        if budget is not None:
            budget.reserve(current_url)
        curl_options = {CurlOpt.RESOLVE: [resolve_entry]} if resolve_entry else {}
        session = CurlSession(
            trust_env=False,
            proxies={},
            curl_options=curl_options,
            verify=True,
            allow_redirects=False,
            max_redirects=0,
            retry=0,
            impersonate="chrome124",
        )
        response = None
        try:
            if budget is not None:
                budget.transport_starts += 1
            response = session.get(
                current_url,
                headers=HEADERS,
                timeout=timeout,
                allow_redirects=False,
                stream=True,
                proxies={},
                verify=True,
            )
            if budget is not None:
                budget.completed_responses += 1
            location = response.headers.get("location") or response.headers.get("Location")
            if response.status_code in REDIRECT_STATUSES and location:
                if redirects_followed >= max_redirects:
                    raise requests.TooManyRedirects(
                        f"exceeded {max_redirects} redirects", response=response
                    )
                target_url, target_resolve_entry = validate_public_redirect_target(
                    current_url,
                    location,
                    expected_origin=expected_origin,
                )
                if profile is not None:
                    rejection = profile_url_policy_rejection(
                        target_url,
                        expected_origin or url,
                        profile,
                        role=role,
                    )
                    if rejection is not None:
                        raise UnsafePublicTarget(
                            "diagnostic redirect rejected by shared URL policy"
                        )
                current_url = target_url
                resolve_entry = target_resolve_entry
                if budget is not None:
                    budget.target_validations += 1
                    budget.redirect_hops += 1
                redirects_followed += 1
                continue

            status = response.status_code
            final_url = response.url or current_url
            headers = {
                str(key).lower(): str(value)
                for key, value in (getattr(response, "headers", {}) or {}).items()
            }
            if status in {403, 429}:
                response.close()
                if include_payload:
                    return status, "", final_url, b"", headers
                return status, "", final_url
            text = _read_bounded_response_text(response)
            if include_payload:
                return status, text, final_url, bytes(response.content or b""), headers
            return status, text, final_url
        finally:
            if response is not None:
                response.close()
            session.close()


def _browser_request_key(url: str) -> str:
    parsed = urlsplit(url)
    return urlunsplit(
        (parsed.scheme.lower(), parsed.netloc.lower(), parsed.path or "/", parsed.query, "")
    )


def _browser_content_type(resource_type: str, headers: dict[str, str]) -> str:
    configured = headers.get("content-type")
    if configured:
        return configured
    return {
        "document": "text/html; charset=utf-8",
        "script": "application/javascript; charset=utf-8",
        "stylesheet": "text/css; charset=utf-8",
        "xhr": "application/json; charset=utf-8",
        "fetch": "application/json; charset=utf-8",
    }.get(resource_type, "application/octet-stream")


def _render_controlled_page(
    url: str,
    *,
    role: str,
    profile: dict,
    prefetched: tuple[int, str, str] | None = None,
) -> dict:
    """Render one page while fulfilling every browser request via pinned HTTP.

    Third-party origins are denied unless the diagnostic profile explicitly
    contains their exact public origin. Observed suggestions do not populate
    that allowlist automatically.
    """
    async def render() -> dict:
        from playwright.async_api import async_playwright

        counters = {
            "status": None,
            "required_blocks": 0,
            "cache_hits": 0,
            "source_blocked": False,
            "block_http_status": None,
        }
        cache: dict[str, tuple[int, bytes, dict[str, str]]] = {}
        if prefetched:
            prefetched_status, prefetched_html, prefetched_url = prefetched
            cache[_browser_request_key(prefetched_url)] = (
                prefetched_status,
                prefetched_html.encode("utf-8"),
                {"content-type": "text/html; charset=utf-8"},
            )
        expected_origin = _ACTIVE_DIAGNOSTIC_ORIGIN.get() or url
        budget = _ACTIVE_DIAGNOSTIC_BUDGET.get()
        if budget is not None:
            budget.browser_transport_used = True

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                headless=True,
                args=["--disable-dev-shm-usage", "--disable-quic"],
            )
            context = await browser.new_context(service_workers="block")

            async def route_websocket(websocket_route):
                route_budget = _ACTIVE_DIAGNOSTIC_BUDGET.get()
                if route_budget is not None:
                    route_budget.browser_websocket_attempts += 1
                    route_budget.browser_required_blocks += 1
                counters["required_blocks"] += 1
                try:
                    await websocket_route.close(
                        code=1008,
                        reason="diagnostic transport disabled",
                    )
                    if route_budget is not None:
                        route_budget.browser_websocket_blocked += 1
                except Exception:
                    if route_budget is not None:
                        route_budget.browser_websocket_errors += 1
                        route_budget.browser_internal_errors += 1

            # BrowserContext.route() does not cover WebSocket. Close it before
            # any page is created so it cannot bypass the pinned HTTP client.
            await context.route_web_socket("**/*", route_websocket)
            await context.add_init_script(
                """(() => {
                    for (const name of [
                        "RTCPeerConnection",
                        "webkitRTCPeerConnection",
                        "WebTransport",
                    ]) {
                        const descriptor = Object.getOwnPropertyDescriptor(globalThis, name);
                        if (descriptor && descriptor.configurable === false && globalThis[name] !== undefined) {
                            throw new Error("unmediated browser transport cannot be disabled");
                        }
                        Object.defineProperty(globalThis, name, {
                            value: undefined,
                            configurable: false,
                            writable: false,
                        });
                    }
                    Object.defineProperty(globalThis, "__studiamatch_transport_guard__", {
                        value: true,
                        configurable: false,
                        writable: false,
                    });
                })();"""
            )
            page = await context.new_page()

            # Confirm the API guard on about:blank before loading institutional
            # content; a failed guard must not be followed by navigation.
            await page.goto("about:blank", wait_until="load", timeout=5000)
            transport_guard_ready = await page.evaluate(
                """() => window.__studiamatch_transport_guard__ === true
                    && window.RTCPeerConnection === undefined
                    && window.webkitRTCPeerConnection === undefined
                    && window.WebTransport === undefined"""
            )
            if not transport_guard_ready:
                raise RuntimeError("unmediated browser transport guard unavailable")
            if budget is not None:
                budget.browser_transport_guarded = True

            async def route_request(route):
                request = route.request
                resource_type = str(getattr(request, "resource_type", "other") or "other").lower()
                budget = _ACTIVE_DIAGNOSTIC_BUDGET.get()
                if budget is not None:
                    budget.browser_route_requests += 1
                try:
                    request_page = request.frame.page
                    is_main_document = bool(
                        request.is_navigation_request()
                        and request.frame == page.main_frame
                        and request_page == page
                    )
                except Exception:
                    is_main_document = False
                request_role = role if is_main_document else "subresource"
                required = is_main_document or resource_type in {
                    "document", "script", "xhr", "fetch"
                }

                async def reject(*, internal: bool = False):
                    if budget is not None:
                        budget.browser_rejected_routes += 1
                        if required:
                            budget.browser_required_blocks += 1
                        if internal:
                            budget.browser_internal_errors += 1
                    if required:
                        counters["required_blocks"] += 1
                    await route.abort()

                try:
                    if counters["source_blocked"]:
                        await reject()
                        return
                    request_url = str(getattr(request, "url", "") or "")
                    if str(getattr(request, "method", "GET")).upper() != "GET":
                        await reject()
                        return
                    validate_public_url_shape(request_url)
                    rejection = profile_url_policy_rejection(
                        request_url,
                        expected_origin,
                        profile,
                        role=request_role,
                    )
                    if rejection is not None:
                        await reject()
                        return

                    key = _browser_request_key(request_url)
                    cached = cache.pop(key, None)
                    if cached is not None:
                        status, body, safe_headers = cached
                        if budget is not None:
                            budget.browser_controlled_routes += 1
                            budget.browser_cache_hits += 1
                        counters["cache_hits"] += 1
                        await route.fulfill(status=status, headers=safe_headers, body=body)
                        if is_main_document:
                            counters["status"] = status
                        return

                    status, _text, final_url, body, response_headers = await asyncio.to_thread(
                        _bounded_get,
                        request_url,
                        10,
                        role=request_role,
                        profile=profile if request_role != "subresource" else None,
                        origin_scope=request_url if request_role == "subresource" else None,
                        include_payload=True,
                    )
                    safe_headers = {
                        key: value
                        for key, value in response_headers.items()
                        if key in {"content-type", "cache-control", "etag", "last-modified"}
                    }
                    safe_headers["content-type"] = _browser_content_type(
                        resource_type if not is_main_document else "document",
                        safe_headers,
                    )
                    if _browser_request_key(final_url) != key:
                        cache[_browser_request_key(final_url)] = (status, body, safe_headers)
                        if budget is not None:
                            budget.browser_controlled_routes += 1
                        await route.fulfill(
                            status=302,
                            headers={"location": final_url, "cache-control": "no-store"},
                            body=b"",
                        )
                    else:
                        if budget is not None:
                            budget.browser_controlled_routes += 1
                        await route.fulfill(status=status, headers=safe_headers, body=body)
                    if is_main_document:
                        counters["status"] = status
                    if status in {403, 429}:
                        counters["source_blocked"] = True
                        counters["block_http_status"] = status
                        if budget is not None:
                            budget.browser_required_blocks += 1
                        counters["required_blocks"] += 1
                except (InvalidControlledRun, UnsafePublicTarget, DiagnosticBudgetExceeded):
                    await reject()
                except Exception:
                    await reject(internal=True)

            await context.route("**/*", route_request)
            html = ""
            try:
                response = await page.goto(url, wait_until="domcontentloaded", timeout=20000)
                if response is not None:
                    counters["status"] = response.status
                try:
                    await page.wait_for_load_state("networkidle", timeout=1500)
                except Exception:
                    pass
                html = await page.content()
            except Exception:
                if counters["status"] is None:
                    counters["status"] = None
            finally:
                await context.close()
                await browser.close()
        return {
            "status": counters["status"],
            "html": html,
            "required_blocks": counters["required_blocks"],
            "cache_hits": counters["cache_hits"],
            "source_blocked": counters["source_blocked"],
            "block_http_status": counters["block_http_status"],
        }

    try:
        return asyncio.run(render())
    except Exception as exc:
        budget = _ACTIVE_DIAGNOSTIC_BUDGET.get()
        if budget is not None:
            budget.browser_internal_errors += 1
        return {
            "status": None,
            "html": "",
            "required_blocks": 0,
            "cache_hits": 0,
            "source_blocked": False,
            "block_http_status": None,
            "error_category": "browser_diagnostic_failed",
            "error_class": type(exc).__name__,
        }

NON_HTML_EXTENSIONS = re.compile(
    r"\.(pdf|xlsx?|docx?|pptx?|zip|rar|png|jpe?g|gif|svg|mp4|webm|css|js)$", re.I
)

PRICE_REGEX_PATTERNS = [
    (re.compile(r"S/\s*([\d,]+\.?\d*)", re.I), "PEN"),
    (re.compile(r"\$\s*([\d,]+\.?\d*)"), "USD"),
    (re.compile(r"USD\s*([\d,]+\.?\d*)", re.I), "USD"),
    (re.compile(r"€\s*([\d,]+\.?\d*)"), "EUR"),
]

DATE_KEYWORDS = [
    "inicio", "inicia", "comienza", "fecha de inicio",
    "start date", "duracion", "duración", "duration",
]

NOISE_PATH_PATTERNS = [
    "/blog/", "/noticias/", "/contacto/", "/nosotros/",
    "/sobre-nosotros/", "/author/", "/category/", "/tag/",
    "/eventos/", "/admision/", "/biblioteca/", "/investigacion/",
    "/login/", "/register/", "/politica/", "/terminos/",
    "/checkout/", "/cart/", "/carrito/", "/mi-cuenta/",
]

CATALOG_PATH_PATTERNS = [
    "/cursos/", "/curso/", "/programas/", "/programa/",
    "/carreras/", "/carrera/", "/diplomados/", "/especializaciones/",
    "/producto/", "/maestrias/", "/posgrado/",
]


def _get(url: str, timeout: int = 10):
    try:
        return _bounded_get(url, timeout)
    except Exception:
        return None, "", url


def _is_hubspot_script_url(src: str) -> bool:
    try:
        host = urlparse(src.strip()).hostname
    except ValueError:
        return False
    normalized_host = (host or "").rstrip(".").lower()
    return normalized_host == "hs-scripts.com" or normalized_host.endswith(
        ".hs-scripts.com"
    )


def detect_cms(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    cms = "html_puro"
    signals = []

    meta_gen = soup.find("meta", attrs={"name": "generator"})
    if meta_gen:
        gen = (meta_gen.get("content", "") or "").lower()
        if "wordpress" in gen:
            cms = "wordpress"
            signals.append("meta_generator:wordpress")
        elif "joomla" in gen:
            cms = "joomla"
            signals.append("meta_generator:joomla")
        elif "hubspot" in gen:
            cms = "hubspot"
            signals.append("meta_generator:hubspot")

    if "/wp-content/" in html or "wp-json" in html:
        cms = "wordpress"
        signals.append("wp_content_paths")

    if "woocommerce" in html.lower() or "woocommerce-LoopProduct-link" in html:
        cms = "woocommerce"
        signals.append("woocommerce_markers")

    has_hubspot_script = any(
        _is_hubspot_script_url(script.get("src", ""))
        for script in soup.find_all("script", src=True)
    )
    visible_text_mentions_hubspot = "hubspot" in soup.get_text(" ", strip=True).lower()
    if has_hubspot_script or visible_text_mentions_hubspot:
        if cms == "html_puro":
            cms = "hubspot"
        signals.append("hubspot_scripts")

    scripts_srcs = [s.get("src", "") for s in soup.find_all("script", src=True)]
    for src in scripts_srcs:
        lsrc = src.lower()
        if "react" in lsrc and "react" not in signals:
            signals.append("react_script")
            if cms == "html_puro":
                cms = "react"
        if "vue" in lsrc and "vue" not in signals:
            signals.append("vue_script")
            if cms == "html_puro":
                cms = "vue"
        if "angular" in lsrc and "angular" not in signals:
            signals.append("angular_script")
            if cms == "html_puro":
                cms = "angular"

    return {"cms": cms, "signals": signals}


def _extract_sitemap_detail_urls(xml_text: str, website_url: str) -> list[str]:
    if not isinstance(xml_text, str) or not xml_text.strip():
        return []
    try:
        root = ET.fromstring(xml_text[:MAX_RESPONSE_BODY_BYTES])
    except ET.ParseError:
        return []
    found = []
    for node in root.iter():
        if node.tag.rsplit("}", 1)[-1].lower() != "loc" or not node.text:
            continue
        value = node.text.strip()
        if profile_url_policy_rejection(value, website_url, {}, role="course_detail") is None:
            found.append(_normalize_url(value))
        if len(found) >= 50:
            break
    return list(dict.fromkeys(found))


def detect_sitemap(base_url: str) -> dict:
    parsed = urlparse(base_url)
    root = f"{parsed.scheme}://{parsed.netloc}"
    candidates = [
        f"{root}/sitemap.xml",
        f"{root}/sitemap_index.xml",
    ]
    found = []
    detail_urls = []
    for url in candidates:
        status, body, final_url = _get(url, timeout=5)
        if status in {403, 429}:
            return {
                "found": False,
                "urls": [],
                "detail_urls": [],
                "blocked": True,
                "http_status": status,
            }
        if status == 200:
            if profile_url_policy_rejection(final_url, base_url, {}, role="sitemap_source") is None:
                found.append(_normalize_url(final_url))
                detail_urls.extend(_extract_sitemap_detail_urls(body, base_url))
                if not detail_urls:
                    child_maps = _extract_sitemap_source_urls(body, base_url)
                    if child_maps:
                        child_status, child_body, _ = _get(child_maps[0], timeout=5)
                        if child_status in {403, 429}:
                            return {
                                "found": False,
                                "urls": [],
                                "detail_urls": [],
                                "blocked": True,
                                "http_status": child_status,
                            }
                        if child_status == 200:
                            detail_urls.extend(_extract_sitemap_detail_urls(child_body, base_url))
            if detail_urls:
                break
    return {
        "found": len(found) > 0,
        "urls": list(dict.fromkeys(found)),
        "detail_urls": list(dict.fromkeys(detail_urls))[:50],
        "blocked": False,
        "http_status": None,
    }


def _extract_sitemap_source_urls(xml_text: str, website_url: str) -> list[str]:
    try:
        root = ET.fromstring(xml_text[:MAX_RESPONSE_BODY_BYTES])
    except (ET.ParseError, TypeError):
        return []
    sources = []
    for node in root.iter():
        if node.tag.rsplit("}", 1)[-1].lower() != "loc" or not node.text:
            continue
        value = node.text.strip()
        if profile_url_policy_rejection(value, website_url, {}, role="sitemap_source") is None:
            sources.append(_normalize_url(value))
        if len(sources) >= 10:
            break
    return list(dict.fromkeys(sources))


def detect_json_ld(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    result = {}
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            if isinstance(data, dict):
                at_type = data.get("@type", "")
                result[at_type.lower()] = data
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        at_type = item.get("@type", "")
                        result[at_type.lower()] = item
        except (json.JSONDecodeError, TypeError):
            pass
    return result


def detect_price_patterns(html: str) -> dict:
    text = BeautifulSoup(html, "html.parser").get_text()
    for pattern, currency in PRICE_REGEX_PATTERNS:
        matches = pattern.findall(text)
        if matches:
            prices = []
            for m in matches:
                try:
                    p = float(m.replace(",", ""))
                    if 10 < p < 1000000:
                        prices.append(p)
                except ValueError:
                    pass
            if prices:
                return {
                    "currency": currency,
                    "prices_found": prices[:5],
                    "regex": pattern.pattern,
                }
    return {}


def detect_date_texts(html: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    results = []
    text = soup.get_text()
    for kw in DATE_KEYWORDS:
        idx = text.lower().find(kw)
        if idx >= 0:
            snippet = text[max(0, idx - 5):idx + len(kw) + 60].strip()
            results.append(snippet[:100])
    return results[:10]


def detect_section_headings(html: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    headings = []
    for tag in soup.find_all(["h1", "h2", "h3", "h4"]):
        text = tag.get_text(strip=True).lower()
        headings.append(text[:100])
    return headings


def detect_catalog_links(html: str, base_url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    catalog_urls = []
    detail_urls = []
    noise_urls = []
    pagination_patterns = []
    selector_candidates = []

    for a in soup.find_all("a", href=True):
        href = a["href"]
        full_url = urljoin(base_url, href)
        if NON_HTML_EXTENSIONS.search(full_url):
            continue
        parsed = urlparse(full_url)
        raw_path = parsed.path.lower()
        path = raw_path.rstrip("/") or "/"
        classes = " ".join(a.get("class", [])).lower()
        rel = " ".join(a.get("rel", [])).lower()

        def record_selector_candidate() -> None:
            for class_name in a.get("class", []):
                if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]{0,79}", str(class_name)):
                    selector_candidates.append(f"a.{class_name}")

        if (
            "next" in rel
            or "pagination" in classes
            or re.search(r"(?:/page/\d+/?|[?&](?:page|paged)=\d+)", full_url, re.I)
        ):
            if re.search(r"[?&](?:page|paged)=\d+", full_url, re.I):
                pattern = re.sub(
                    r"([?&](?:page|paged)=)\d+",
                    r"\g<1>{page}",
                    full_url,
                    count=1,
                    flags=re.I,
                )
            else:
                pattern = re.sub(r"/page/\d+/?$", "/page/{page}", full_url, flags=re.I)
            pagination_patterns.append(pattern)
            catalog_urls.append(full_url)
            record_selector_candidate()
            continue
        if any(pattern in raw_path for pattern in NOISE_PATH_PATTERNS):
            noise_urls.append(full_url)
            continue
        if "woocommerce-loopproduct-link" in classes or "product" in classes:
            detail_urls.append(full_url)
            record_selector_candidate()
            continue
        matched_prefix = next((
            prefix for pattern in CATALOG_PATH_PATTERNS
            if path == (prefix := pattern.rstrip("/")) or path.startswith(prefix + "/")
        ), None)
        if matched_prefix:
            remainder = path[len(matched_prefix):].strip("/")
            if not remainder:
                catalog_urls.append(full_url)
            else:
                detail_urls.append(full_url)
            record_selector_candidate()

    return {
        "catalog_urls": list(dict.fromkeys(catalog_urls))[:20],
        "detail_urls": list(dict.fromkeys(detail_urls))[:50],
        "pagination_patterns": list(dict.fromkeys(pagination_patterns))[:10],
        "selector_candidates": list(dict.fromkeys(selector_candidates))[:20],
        "noise_urls_detected": list(dict.fromkeys(noise_urls))[:10],
    }


def detect_noise_patterns(html: str, base_url: str) -> list[str]:
    """Return the noise links recognized while extracting catalog links."""
    return detect_catalog_links(html, base_url)["noise_urls_detected"]


def detect_js_required(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    body_text = soup.body.get_text(" ", strip=True) if soup.body else ""
    body_length = len(body_text)
    app_root_ids = {"root", "app", "app-root", "__next", "__nuxt", "catalog", "application"}
    empty_app_root = any(
        str(node.get("id", "")).strip().lower() in app_root_ids
        and not node.get_text(" ", strip=True)
        for node in soup.find_all(attrs={"id": True})
    )
    has_script = bool(soup.find("script"))
    signals = []
    if body_length < 500:
        signals.append("short_body")
    if empty_app_root:
        signals.append("empty_app_root")
    if has_script:
        signals.append("script_present")
    # Short copy alone is not evidence of a JavaScript application. Require a
    # known empty app root and script to avoid classifying sparse static pages
    # as SPAs, which could otherwise create an unjustified profile suggestion.
    needs_js = body_length < 500 and empty_app_root and has_script
    return {
        "needs_js": needs_js,
        "body_text_length": body_length,
        "signals": signals,
    }


def detect_institution_metadata(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.string.strip() if soup.title else ""
    og_site = soup.find("meta", property="og:site_name")
    site_name = og_site["content"].strip() if og_site else ""
    parsed = urlparse(url)
    domain = parsed.netloc.replace("www.", "")
    slug_candidate = domain.split(".")[0].lower()

    return {
        "title_tag": title[:200],
        "og_site_name": site_name,
        "domain": domain,
        "suggested_slug": slug_candidate,
    }


def suggest_site_type(cms_result: dict, js_result: dict) -> str:
    cms = cms_result.get("cms", "html_puro")
    if cms == "woocommerce":
        return "ecommerce"
    if cms == "hubspot":
        return "traditional_ssr"
    if js_result.get("needs_js"):
        return "spa_js_heavy"
    return "traditional_ssr"


def suggest_discovery_mode(sitemap_result: dict, catalog_result: dict, *, site_type: str | None = None) -> str:
    if site_type == "ecommerce" and catalog_result.get("pagination_patterns"):
        return "paginated_catalog"
    if catalog_result.get("catalog_urls"):
        return "catalog_link_extraction"
    if sitemap_result.get("found"):
        return "sitemap_bfs"
    return "hardcoded_urls"


def build_section_keywords(headings: list) -> dict:
    mapping = {}
    for h in headings:
        hl = h.lower()
        if any(w in hl for w in ["inversión", "inversion", "precio", "costo"]):
            mapping.setdefault("total_cost_est", h)
        elif any(w in hl for w in ["inicio", "fecha", "comienza"]):
            mapping.setdefault("start_date", h)
        elif any(w in hl for w in ["duración", "duracion", "duration"]):
            mapping.setdefault("duration_text", h)
        elif any(w in hl for w in ["modalidad", "presencial", "remoto", "virtual"]):
            mapping.setdefault("modality", h)
        elif any(w in hl for w in ["dirigido a", "requisitos", "prerrequisitos"]):
            mapping.setdefault("requirements", h)
        elif any(w in hl for w in ["certificación", "certificacion", "diploma"]):
            mapping.setdefault("certifications", h)
        elif any(w in hl for w in ["malla", "plan de estudios", "temario", "contenido"]):
            mapping.setdefault("curriculum_summary", h)
        elif any(w in hl for w in ["perfil del egresado", "perfil del graduado", "objetivos"]):
            mapping.setdefault("graduate_profile", h)
    return mapping


def build_exclusion_patterns(base_url: str, catalog_result: dict) -> list:
    """Suggest only exact observed same-origin noise URLs; never broad defaults."""
    origin = urlparse(base_url).netloc.lower()
    exact_urls = []
    for value in catalog_result.get("noise_urls_detected", []):
        try:
            parsed = urlparse(value)
        except (TypeError, ValueError):
            continue
        if parsed.scheme in {"http", "https"} and parsed.netloc.lower() == origin and parsed.path:
            exact_urls.append(f"{parsed.scheme}://{parsed.netloc}{parsed.path}")
    return list(dict.fromkeys(exact_urls))[:10]


def evaluate_discovery_candidates(
    website_url: str,
    profile: dict,
    *,
    source_urls: list[str],
    detail_urls: list[str],
    verified_detail_urls: list[str] | None = None,
) -> dict:
    """Apply the same role-aware URL contract used by preflight and runtime."""
    accepted_sources = []
    rejected_sources = []
    accepted_details = []
    rejected_details = []
    seed_conflicts = []

    def source_role(value: str) -> str:
        parsed = urlparse(value)
        path = parsed.path.lower().rstrip("/") or "/"
        try:
            query = parse_qsl(parsed.query, keep_blank_values=True, max_num_fields=20)
        except ValueError:
            query = []
        query_keys = {key.lower() for key, _value in query}
        if path.endswith((".xml", ".xml.gz")) or "sitemap" in path:
            return "sitemap_source"
        if re.search(r"/page/\d+$", path, re.I) or query_keys.intersection({"page", "paged"}):
            return "catalog_source"
        if any(path == pattern.rstrip("/") for pattern in CATALOG_PATH_PATTERNS):
            return "catalog_source"
        return "course_detail"

    for value in source_urls:
        role = source_role(value)
        rejection = profile_url_policy_rejection(value, website_url, profile, role=role)
        if rejection is None:
            accepted_sources.append(_normalize_url(value))
        else:
            rejected_sources.append({"reason": rejection, "role": role})

    for value in detail_urls:
        rejection = profile_url_policy_rejection(value, website_url, profile, role="course_detail")
        if rejection is None:
            accepted_details.append(_normalize_url(value))
        else:
            rejected_details.append({"reason": rejection})

    for seed in profile.get("seed_urls", []) if isinstance(profile, dict) else []:
        if not isinstance(seed, str):
            seed_conflicts.append({"reason": "malformed_seed"})
            continue
        rejection = profile_url_policy_rejection(
            seed,
            website_url,
            profile,
            role=source_role(seed) if profile.get("discovery_mode") != "hardcoded_urls" else "course_detail",
        )
        if rejection:
            seed_conflicts.append({"reason": "excluded_by_profile" if rejection == "excluded_by_profile" else rejection})

    status = "verified"
    verified_detail_conflicts = []
    for value in verified_detail_urls or []:
        rejection = profile_url_policy_rejection(
            value, website_url, profile, role="course_detail"
        )
        if rejection is not None:
            verified_detail_conflicts.append(rejection)
    if seed_conflicts or verified_detail_conflicts or not accepted_sources or len(accepted_details) < 2:
        status = "review_required"
    return {
        "status": status,
        "source_urls": list(dict.fromkeys(accepted_sources)),
        "rejected_sources": rejected_sources,
        "accepted_detail_urls": list(dict.fromkeys(accepted_details)),
        "rejected_detail_urls": rejected_details,
        "seed_conflicts": seed_conflicts,
        "verification": {
            "eligible": status == "verified",
            "verified_detail_count": len(set(accepted_details)),
            "new_course_discovery": bool(accepted_sources and accepted_details),
            "reasons": (["seed_conflict"] if seed_conflicts else [])
            + (["verified_detail_conflicts_with_profile"] if verified_detail_conflicts else [])
            + (["no_discovery_source"] if not accepted_sources else [])
            + (["insufficient_detail_examples"] if len(accepted_details) < 2 else []),
        },
    }


def assign_template(diagnosis: dict) -> dict:
    """Asigna una plantilla base segun el tipo de sitio detectado."""
    cms = diagnosis.get("cms", {}).get("cms", "html_puro")
    js = diagnosis.get("js", {})

    if cms == "woocommerce":
        return {
            "site_type": "ecommerce",
            "discovery_mode": "catalog_link_extraction",
            "catalog_link_selector": "a.woocommerce-LoopProduct-link",
            "requires_stealth": False,
            "requires_cloudflare_bypass": False,
            "catalog_scroll_iterations": 15,
            "detail_wait_ms": 5000,
            "pipeline_ready": False,
        }
    if cms == "hubspot":
        return {
            "site_type": "traditional_ssr",
            "discovery_mode": "hardcoded_urls",
            "requires_stealth": False,
            "requires_cloudflare_bypass": False,
            "pipeline_enabled": False,
            "pipeline_ready": False,
            "detail_wait_ms": 2000,
        }
    if js.get("needs_js") and cms in ("react", "vue", "angular"):
        return {
            "site_type": "spa_js_heavy",
            "discovery_mode": "sitemap_bfs",
            # JavaScript rendering does not establish a block or authorize bypass.
            "requires_stealth": False,
            "requires_cloudflare_bypass": False,
            "detail_wait_ms": 3000,
            "pipeline_ready": False,
        }

    return {
        "site_type": "traditional_ssr",
        "discovery_mode": "sitemap_bfs",
        "requires_stealth": False,
        "requires_cloudflare_bypass": False,
        "detail_wait_ms": 2000,
        "pipeline_ready": False,
    }


def _looks_like_course_detail(html: str) -> bool:
    """Require positive course evidence; a detail-shaped path alone is insufficient."""
    if not isinstance(html, str) or not html.strip():
        return False
    soup = BeautifulSoup(html, "html.parser")
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if isinstance(item, dict):
                types = item.get("@type", [])
                types = types if isinstance(types, list) else [types]
                if any(str(value).lower() in {"course", "product", "educationaloccupationalprogram"} for value in types):
                    return True
    title = " ".join(
        part for part in (
            soup.title.get_text(" ", strip=True) if soup.title else "",
            soup.find("h1").get_text(" ", strip=True) if soup.find("h1") else "",
        ) if part
    ).lower()
    if not title:
        return False
    course_term = any(term in title for term in ("curso", "programa", "diplomado", "maestría", "maestria", "carrera", "especialización", "especializacion"))
    evidence_text = soup.get_text(" ", strip=True).lower()
    detail_signals = sum(
        term in evidence_text
        for term in ("duración", "duracion", "modalidad", "inversión", "inversion", "malla curricular", "plan de estudios", "créditos", "creditos")
    )
    return course_term and detail_signals >= 1


def _derive_verified_detail_prefix(detail_urls: list[str]) -> str | None:
    """Suggest a positive path prefix shared only by positively verified pages."""
    segment_lists = []
    for value in detail_urls:
        path = urlsplit(value).path.strip("/")
        segments = [segment for segment in path.split("/") if segment]
        if len(segments) < 2:
            return None
        segment_lists.append(segments[:-1])
    if len(segment_lists) < 2:
        return None
    common: list[str] = []
    for parts in zip(*segment_lists):
        if len(set(parts)) != 1:
            break
        common.append(parts[0])
    if not common:
        return None
    return "/" + "/".join(common) + "/"


def diagnose_site(url: str, logger=None) -> dict:
    """Ejecuta diagnostico completo de un sitio web.
    Retorna observaciones, sugerencias y estado explícitos sin activar ni guardar un perfil.
    """
    def _log(msg):
        if logger:
            logger.info(msg)

    parsed_root = urlparse(url)
    expected_origin = f"{parsed_root.scheme.lower()}://{parsed_root.netloc.lower()}"
    budget = DiagnosticRequestBudget()
    budget_token = _ACTIVE_DIAGNOSTIC_BUDGET.set(budget)
    origin_token = _ACTIVE_DIAGNOSTIC_ORIGIN.set(expected_origin)
    _log(f"Diagnosticando host={parsed_root.hostname or 'unknown'} ...")
    t0 = time.time()
    try:
        status, html, final_url = _bounded_get(
            url,
            timeout=15,
            role="catalog_source",
            profile={"allowed_resource_origins": []},
        )
        if status in {403, 429}:
            return {
                "status": "blocked",
                "error": {"category": "institution_blocked", "http_status": status},
                "observed": {"host": parsed_root.hostname, "html_received": bool(html), "request_count": budget.requests},
                "suggested": {},
                "verification": {"eligible": False, "verified_detail_count": 0, "new_course_discovery": False, "reasons": ["institution_blocked"]},
            }
        if status != 200 or not html:
            return {
                "status": "review_required",
                "error": {"category": "homepage_unavailable", "http_status": status if isinstance(status, int) else None},
                "observed": {"host": parsed_root.hostname, "html_received": bool(html), "request_count": budget.requests},
                "suggested": {},
                "verification": {"eligible": False, "verified_detail_count": 0, "new_course_discovery": False, "reasons": ["homepage_unavailable"]},
            }

        initial_html = html
        cms = detect_cms(initial_html)
        js = detect_js_required(initial_html)
        site_type = suggest_site_type(cms, js)
        browser_home = None
        if site_type in {"spa_js_heavy", "ecommerce"}:
            browser_home = _render_controlled_page(
                final_url,
                role="catalog_source",
                profile={"allowed_resource_origins": []},
                prefetched=(status, initial_html, final_url),
            )
            if browser_home.get("source_blocked"):
                blocked_status = browser_home.get("block_http_status")
                return {
                    "status": "blocked",
                    "error": {"category": "institution_blocked", "http_status": blocked_status},
                    "observed": {"host": parsed_root.hostname, "site_type": site_type, "request_count": budget.requests},
                    "suggested": {},
                    "verification": {"eligible": False, "verified_detail_count": 0, "new_course_discovery": False, "reasons": ["institution_blocked"]},
                }
            if browser_home.get("html"):
                html = browser_home["html"]
                cms = detect_cms(initial_html + "\n" + html)
                js = detect_js_required(initial_html)
                js["rendered_body_text_length"] = len(
                    BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
                )
                site_type = suggest_site_type(cms, js)

        sitemap = detect_sitemap(final_url)
        if sitemap.get("blocked"):
            return {
                "status": "blocked",
                "error": {
                    "category": "institution_blocked",
                    "http_status": sitemap.get("http_status"),
                },
                "observed": {
                    "host": parsed_root.hostname,
                    "site_type": site_type,
                    "request_count": budget.requests,
                },
                "suggested": {},
                "verification": {
                    "eligible": False,
                    "verified_detail_count": 0,
                    "new_course_discovery": False,
                    "reasons": ["institution_blocked"],
                },
            }
        ld = detect_json_ld(html)
        price = detect_price_patterns(html)
        dates = detect_date_texts(html)
        headings = detect_section_headings(html)
        catalog = detect_catalog_links(html, final_url)
        meta = detect_institution_metadata(html, final_url)

        # Inspect at most one same-origin catalogue page. It is a discovery
        # source; its child links are course details and use the detail policy.
        for catalog_url in catalog.get("catalog_urls", [])[:1]:
            source_rejection = profile_url_policy_rejection(
                catalog_url,
                final_url,
                {"allowed_resource_origins": []},
                role="catalog_source",
            )
            if source_rejection is not None:
                continue
            source_status, source_html, source_final_url = _bounded_get(
                catalog_url,
                timeout=10,
                role="catalog_source",
                profile={"allowed_resource_origins": []},
            )
            if source_status in {403, 429}:
                return {
                    "status": "blocked",
                    "error": {"category": "institution_blocked", "http_status": source_status},
                    "observed": {"host": parsed_root.hostname, "site_type": site_type, "request_count": budget.requests},
                    "suggested": {},
                    "verification": {"eligible": False, "verified_detail_count": 0, "new_course_discovery": False, "reasons": ["institution_blocked"]},
                }
            if source_status == 200 and source_html and site_type in {"spa_js_heavy", "ecommerce"}:
                rendered_source = _render_controlled_page(
                    source_final_url,
                    role="catalog_source",
                    profile={"allowed_resource_origins": []},
                    prefetched=(source_status, source_html, source_final_url),
                )
                if rendered_source.get("source_blocked"):
                    blocked_status = rendered_source.get("block_http_status")
                    return {
                        "status": "blocked",
                        "error": {"category": "institution_blocked", "http_status": blocked_status},
                        "observed": {"host": parsed_root.hostname, "site_type": site_type, "request_count": budget.requests},
                        "suggested": {},
                        "verification": {"eligible": False, "verified_detail_count": 0, "new_course_discovery": False, "reasons": ["institution_blocked"]},
                    }
                if rendered_source.get("html"):
                    source_html = rendered_source["html"]
            if source_status == 200 and source_html:
                child_links = detect_catalog_links(source_html, catalog_url)
                catalog["detail_urls"] = list(dict.fromkeys(
                    catalog.get("detail_urls", []) + child_links.get("detail_urls", [])
                ))[:50]
                catalog["pagination_patterns"] = list(dict.fromkeys(
                    catalog.get("pagination_patterns", []) + child_links.get("pagination_patterns", [])
                ))[:10]
                catalog["selector_candidates"] = list(dict.fromkeys(
                    catalog.get("selector_candidates", []) + child_links.get("selector_candidates", [])
                ))[:20]

        discovery_mode = suggest_discovery_mode(sitemap, catalog, site_type=site_type)
        source_urls = sitemap.get("urls", []) if sitemap.get("found") else catalog.get("catalog_urls", [])
        detail_candidates = list(dict.fromkeys(
            sitemap.get("detail_urls", []) + catalog.get("detail_urls", [])
        ))[:10]
        exclusion = build_exclusion_patterns(final_url, catalog)
        profile = {
            "site_type": site_type,
            "discovery_mode": discovery_mode,
            "seed_urls": source_urls[:5],
            "catalog_url_patterns": catalog.get("pagination_patterns", [])[:10],
            "catalog_link_selector": (
                "a.woocommerce-LoopProduct-link"
                if cms.get("cms") == "woocommerce"
                else (catalog.get("selector_candidates") or ["a[href]"])[0]
            ),
            "catalog_max_pages": 5,
            "catalog_scroll_iterations": 0,
            "section_keywords": build_section_keywords(headings),
            "price_regex": price.get("regex", ""),
            "duration_regex": "",
            "exclusion_patterns": exclusion,
            "allowed_url_patterns": [],
            "allowed_resource_origins": [],
            "field_defaults": {},
            "requires_stealth": False,
            "requires_cloudflare_bypass": False,
            "detail_wait_ms": 2000,
            "pipeline_ready": False,
            "auto_generated": True,
        }
        # Probe candidates before applying exclusions inferred from this same
        # diagnostic. Otherwise an intended negative example (such as a news
        # link) is misclassified as an exclusion conflict and valid profiles
        # can never reach positive detail verification.
        verification_profile = dict(profile)
        verification_profile["exclusion_patterns"] = []
        evaluation = evaluate_discovery_candidates(
            url,
            verification_profile,
            source_urls=source_urls,
            detail_urls=detail_candidates,
        )

        verified_details = []
        browser_detail_probes = 0
        browser_detail_successes = 0
        institution_block_status = None
        for candidate in evaluation["accepted_detail_urls"][:DIAGNOSTIC_MAX_DETAIL_PROBES]:
            if site_type in {"spa_js_heavy", "ecommerce"}:
                rendered_detail = _render_controlled_page(
                    candidate,
                    role="course_detail",
                    profile=profile,
                )
                browser_detail_probes += 1
                detail_status = rendered_detail.get("status")
                detail_html = rendered_detail.get("html") or ""
                if rendered_detail.get("source_blocked"):
                    institution_block_status = rendered_detail.get("block_http_status")
                    break
                if detail_status == 200 and not rendered_detail.get("required_blocks"):
                    browser_detail_successes += 1
            else:
                detail_status, detail_html, _ = _bounded_get(
                    candidate,
                    timeout=10,
                    role="course_detail",
                    profile=profile,
                )
            if detail_status in {403, 429}:
                institution_block_status = detail_status
                break
            if detail_status == 200 and _looks_like_course_detail(detail_html):
                verified_details.append(candidate)
        reasons = list(evaluation["verification"]["reasons"])
        allowed_prefix = _derive_verified_detail_prefix(verified_details)
        if allowed_prefix:
            profile["allowed_url_patterns"] = [allowed_prefix]
        evaluation = evaluate_discovery_candidates(
            url,
            profile,
            source_urls=source_urls,
            detail_urls=detail_candidates,
            verified_detail_urls=verified_details,
        )
        reasons = list(evaluation["verification"]["reasons"])
        if not allowed_prefix:
            reasons.append("no_verified_course_url_prefix")
        if browser_home and browser_home.get("required_blocks"):
            reasons.append("required_browser_resource_blocked")
        if browser_home and browser_home.get("error_category"):
            reasons.append("controlled_browser_inconclusive")
        if site_type in {"spa_js_heavy", "ecommerce"} and (
            browser_detail_probes < DIAGNOSTIC_MAX_DETAIL_PROBES
            or browser_detail_successes < DIAGNOSTIC_MAX_DETAIL_PROBES
        ):
            reasons.append("controlled_browser_detail_incomplete")
        if len(verified_details) < 2:
            reasons.append("insufficient_verified_course_pages")
        if institution_block_status is not None:
            return {
                "status": "blocked",
                "error": {"category": "institution_blocked", "http_status": institution_block_status},
                "observed": {"host": parsed_root.hostname, "site_type": site_type, "request_count": budget.requests},
                "suggested": {},
                "verification": {"eligible": False, "verified_detail_count": len(verified_details), "new_course_discovery": False, "reasons": ["institution_blocked"]},
            }
        status_label = "verified" if evaluation["status"] == "verified" and len(verified_details) >= 2 else "review_required"
        if not allowed_prefix:
            status_label = "review_required"
        if (
            site_type in {"spa_js_heavy", "ecommerce"}
            and (
                not browser_home
                or browser_home.get("status") != 200
                or browser_home.get("required_blocks")
                or browser_home.get("error_category")
                or browser_detail_probes < DIAGNOSTIC_MAX_DETAIL_PROBES
                or browser_detail_successes < DIAGNOSTIC_MAX_DETAIL_PROBES
            )
        ):
            status_label = "review_required"
        verification = {
            **evaluation["verification"],
            "eligible": status_label == "verified",
            "verified_detail_count": len(verified_details),
            "new_course_discovery": bool(source_urls and verified_details),
            "transport_controls_verified": budget.transport_controls_verified(),
            "automatic_activation_ready": bool(
                status_label == "verified"
                and site_type in {"traditional_ssr", "spa_js_heavy", "ecommerce"}
                and discovery_mode != "hardcoded_urls"
                and budget.transport_controls_verified()
                and budget.browser_required_blocks == 0
                and budget.browser_internal_errors == 0
            ),
            "reasons": list(dict.fromkeys(reasons)),
        }
        if discovery_mode == "hardcoded_urls":
            status_label = "review_required"
            verification["eligible"] = False
            verification["reasons"] = list(dict.fromkeys(verification["reasons"] + ["no_reusable_discovery_source"]))

        observed = {
            "host": parsed_root.hostname,
            "site_type": site_type,
            "cms": cms.get("cms"),
            "js_required": bool(js.get("needs_js")),
            "sitemap_count": len(sitemap.get("urls", [])),
            "catalog_source_count": len(catalog.get("catalog_urls", [])),
            "candidate_detail_count": len(detail_candidates),
            "verified_detail_count": len(verified_details),
            "noise_candidate_count": len(catalog.get("noise_urls_detected", [])),
            "request_count": budget.requests,
            "transport_target_validations": budget.target_validations,
            "transport_starts": budget.transport_starts,
            "completed_responses": budget.completed_responses,
            "redirect_hops": budget.redirect_hops,
            "transport_controls_verified": budget.transport_controls_verified(),
        }
        result = {
            "status": status_label,
            "institution_metadata": meta,
            "observed": observed,
            "suggested": profile,
            "verification": verification,
            "institution_site_profile": profile,
            "raw_diagnostics": {
                "cms": cms,
                "sitemap": {"found": sitemap["found"], "count": len(sitemap.get("urls", []))},
                "json_ld_keys": list(ld.keys()),
                "price_present": bool(price),
                "dates_count": len(dates),
                "headings_count": len(headings),
                "catalog_count": len(catalog.get("catalog_urls", [])),
                "js_required": js,
            },
            "_confidence": {
                "site_type": "high" if cms["cms"] != "html_puro" else "medium",
                "discovery_mode": "high" if source_urls else "low",
                "needs_manual_review": verification["reasons"],
            },
        }
        _log(f"Diagnóstico terminado; status={status_label} requests={budget.requests} elapsed={time.time() - t0:.1f}s")
        return result
    except Exception as exc:
        category = (
            "unsafe_target" if isinstance(exc, UnsafePublicTarget)
            else "request_budget_exhausted" if isinstance(exc, DiagnosticBudgetExceeded)
            else "diagnostic_failed"
        )
        _log(f"Diagnóstico inconcluso; category={category} error_class={type(exc).__name__}")
        return {
            "status": "blocked" if category == "unsafe_target" else "review_required",
            "error": {"category": category},
            "observed": {"host": parsed_root.hostname, "request_count": budget.requests},
            "suggested": {},
            "verification": {"eligible": False, "verified_detail_count": 0, "new_course_discovery": False, "reasons": [category]},
        }
    finally:
        _ACTIVE_DIAGNOSTIC_ORIGIN.reset(origin_token)
        _ACTIVE_DIAGNOSTIC_BUDGET.reset(budget_token)
