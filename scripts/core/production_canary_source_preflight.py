import argparse
import asyncio
import contextlib
import ipaddress
import io
import os
import sys
from urllib.parse import urljoin, urlparse

try:
    from curl_cffi.requests import AsyncSession
except ModuleNotFoundError:
    AsyncSession = None

try:
    from playwright.async_api import TimeoutError as PlaywrightTimeoutError
    from playwright.async_api import async_playwright
except ModuleNotFoundError:
    PlaywrightTimeoutError = TimeoutError
    async_playwright = None

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from .production_canary_manifest import (  # type: ignore
        _ensure_github_production_context,
        _ensure_production_supabase_target,
        _load_profile,
        _resolve_institution,
        _validate_profile_contract,
        get_db_client,
    )
except ImportError:
    from production_canary_manifest import (  # type: ignore  # noqa: E402
        _ensure_github_production_context,
        _ensure_production_supabase_target,
        _load_profile,
        _resolve_institution,
        _validate_profile_contract,
        get_db_client,
    )


SOURCE_ACCESS_PASS = "SOURCE_ACCESS_PASS"
SOURCE_BLOCKED_HTTP_403 = "SOURCE_BLOCKED_HTTP_403"
SOURCE_RATE_LIMITED_HTTP_429 = "SOURCE_RATE_LIMITED_HTTP_429"
SOURCE_UPSTREAM_5XX = "SOURCE_UPSTREAM_5XX"
SOURCE_TIMEOUT = "SOURCE_TIMEOUT"
SOURCE_INVALID_RESPONSE = "SOURCE_INVALID_RESPONSE"

ALLOWED_CODES = {
    SOURCE_ACCESS_PASS,
    SOURCE_BLOCKED_HTTP_403,
    SOURCE_RATE_LIMITED_HTTP_429,
    SOURCE_UPSTREAM_5XX,
    SOURCE_TIMEOUT,
    SOURCE_INVALID_RESPONSE,
}
READ_ONLY_DB_METHOD_PREFIXES = ("select", "count")


class _ReadOnlyCanaryDB:
    def __init__(self, db):
        self._db = db

    def __getattr__(self, name):
        if not name.startswith(READ_ONLY_DB_METHOD_PREFIXES):
            raise RuntimeError("Production canary source preflight is read-only")
        return getattr(self._db, name)


def _classify_status(status_code):
    if status_code == 200:
        return SOURCE_ACCESS_PASS
    if status_code == 403:
        return SOURCE_BLOCKED_HTTP_403
    if status_code == 429:
        return SOURCE_RATE_LIMITED_HTTP_429
    if isinstance(status_code, int) and 500 <= status_code <= 599:
        return SOURCE_UPSTREAM_5XX
    return SOURCE_INVALID_RESPONSE


def _is_html_payload(text):
    lowered = str(text or "")[:1000].lower()
    return "<html" in lowered or "<!doctype html" in lowered


def _clean_host(host):
    host = str(host or "").strip().lower().rstrip(".")
    if not host or host == "localhost" or host.endswith(".localhost"):
        return None
    if any(ord(char) <= 32 for char in host):
        return None
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None:
        return host if address.is_global else None
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789-.")
    if any(char not in allowed for char in host) or ".." in host:
        return None
    labels = host.split(".")
    if any(not label or label.startswith("-") or label.endswith("-") for label in labels):
        return None
    return host


def _canonical_host(host):
    host = _clean_host(host)
    if host and host.startswith("www."):
        return host[4:]
    return host


def _matches_institution_host(candidate_host, website_host):
    candidate = _canonical_host(candidate_host)
    base = _canonical_host(website_host)
    return bool(candidate and base and (candidate == base or candidate.endswith(f".{base}")))


def _validate_source_url(source_url, website_url):
    raw_url = str(source_url or "").strip()
    if not raw_url or any(ord(char) <= 32 for char in raw_url):
        return None
    parsed = urlparse(raw_url)
    website = urlparse(str(website_url or "").strip())
    try:
        port = parsed.port
    except ValueError:
        return None
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or parsed.username
        or parsed.password
        or port not in (None, 443)
        or not _matches_institution_host(parsed.hostname, website.hostname)
    ):
        return None
    return parsed._replace(fragment="").geturl()


def _is_browser_allowed_request(request_url, source_host):
    parsed = urlparse(str(request_url or ""))
    try:
        port = parsed.port
    except ValueError:
        return False
    return (
        parsed.scheme == "https"
        and port in (None, 443)
        and not parsed.username
        and not parsed.password
        and _clean_host(parsed.hostname) == source_host
    )


def _candidate_source_urls(institution, profile):
    discovery_mode = profile.get("discovery_mode")
    seed_urls = profile.get("seed_urls") or []
    catalog_patterns = profile.get("catalog_url_patterns") or []
    website_url = institution.get("website_url") or ""

    if discovery_mode == "hardcoded_urls":
        return list(seed_urls)
    elif discovery_mode == "catalog_link_extraction":
        return list(seed_urls) if seed_urls else [website_url]
    elif discovery_mode == "paginated_catalog":
        return [str(pattern).replace("{page}", "1") for pattern in catalog_patterns]
    elif discovery_mode == "sitemap_bfs":
        return [urljoin(website_url, "/sitemap.xml")]
    return []


def _safe_source_url(institution, profile):
    website_url = institution.get("website_url") or ""
    source_urls = _candidate_source_urls(institution, profile)
    if not source_urls:
        return None

    safe_urls = [_validate_source_url(source_url, website_url) for source_url in source_urls]
    if any(not source_url for source_url in safe_urls):
        return None
    return safe_urls[0]


def _needs_browser(profile):
    return (
        profile.get("site_type") in {"spa_js_heavy", "ecommerce"}
        or profile.get("discovery_mode") == "catalog_link_extraction"
    )


async def _probe_http(source_url):
    if AsyncSession is None:
        return SOURCE_INVALID_RESPONSE
    try:
        async with AsyncSession() as session:
            response = await session.get(
                source_url,
                impersonate="chrome110",
                timeout=25,
                allow_redirects=False,
            )
    except Exception as exc:
        if "timeout" in type(exc).__name__.lower() or "timeout" in str(exc).lower():
            return SOURCE_TIMEOUT
        return SOURCE_INVALID_RESPONSE
    code = _classify_status(getattr(response, "status_code", None))
    if code != SOURCE_ACCESS_PASS:
        return code
    return SOURCE_ACCESS_PASS if _is_html_payload(getattr(response, "text", "")) else SOURCE_INVALID_RESPONSE


async def _probe_browser(source_url):
    if async_playwright is None:
        return SOURCE_INVALID_RESPONSE
    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            try:
                context = await browser.new_context(service_workers="block")
                try:
                    source_host = _clean_host(urlparse(source_url).hostname)

                    async def route_read_only(route):
                        request = route.request
                        if request.method.upper() != "GET" or not _is_browser_allowed_request(request.url, source_host):
                            await route.abort()
                            return
                        await route.continue_()

                    def close_popup(popup):
                        asyncio.create_task(popup.close())

                    await context.route("**/*", route_read_only)
                    page = await context.new_page()
                    page.on("popup", close_popup)
                    await page.add_init_script("window.open = () => null")
                    response = await page.goto(source_url, wait_until="domcontentloaded", timeout=60000)
                    if response and getattr(response, "url", source_url) != source_url:
                        return SOURCE_INVALID_RESPONSE
                    status_code = getattr(response, "status", None) if response else None
                    code = _classify_status(status_code)
                    if code != SOURCE_ACCESS_PASS:
                        return code
                    return SOURCE_ACCESS_PASS if _is_html_payload(await page.content()) else SOURCE_INVALID_RESPONSE
                finally:
                    await context.close()
            finally:
                await browser.close()
    except PlaywrightTimeoutError:
        return SOURCE_TIMEOUT
    except Exception:
        return SOURCE_INVALID_RESPONSE


async def _probe_source(source_url, profile):
    if _needs_browser(profile):
        return await _probe_browser(source_url)
    return await _probe_http(source_url)


def _load_canary_context(args):
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        db = _ReadOnlyCanaryDB(get_db_client())
        institution = _resolve_institution(db, args.institution_slug)
        profile = _load_profile(db, institution.get("id"))
    return institution, profile


def run_preflight(args, probe_source=None):
    _ensure_github_production_context()
    _ensure_production_supabase_target()
    institution, profile = _load_canary_context(args)
    _validate_profile_contract(
        profile,
        require_pipeline_enabled=True,
        require_production_enabled=True,
    )

    source_url = _safe_source_url(institution, profile)
    if not source_url:
        print(SOURCE_INVALID_RESPONSE)
        return 1

    if probe_source:
        result = probe_source(source_url, profile)
    else:
        result = asyncio.run(_probe_source(source_url, profile))
    if result not in ALLOWED_CODES:
        result = SOURCE_INVALID_RESPONSE
    print(result)
    return 0 if result == SOURCE_ACCESS_PASS else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run sanitized F10 source access preflight")
    parser.add_argument("--institution-slug", required=True)
    args = parser.parse_args(argv)
    try:
        return run_preflight(args)
    except Exception:
        print(SOURCE_INVALID_RESPONSE)
        return 1


if __name__ == "__main__":
    sys.exit(main())
