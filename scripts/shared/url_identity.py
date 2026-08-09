from __future__ import annotations

from dataclasses import dataclass
from posixpath import normpath
from urllib.parse import parse_qsl, quote, unquote, urlencode, urlparse, urlunparse


URL_IDENTITY_VERSION = "url-id-v1"

_TRACKING_QUERY_PREFIXES = ("utm_",)
_TRACKING_QUERY_KEYS = frozenset(
    {
        "fbclid",
        "gclid",
        "gbraid",
        "wbraid",
        "mc_cid",
        "mc_eid",
        "igshid",
        "msclkid",
    }
)


@dataclass(frozen=True)
class URLIdentity:
    version: str
    canonical_url: str
    dedupe_key: str
    host: str
    path: str
    query: str


def _normalize_host(hostname: str | None) -> str:
    host = (hostname or "").strip().rstrip(".").lower()
    if not host:
        return ""
    try:
        return host.encode("idna").decode("ascii")
    except UnicodeError:
        return host


def _normalize_path(path: str) -> str:
    if not path:
        return "/"
    decoded = unquote(path)
    normalized = normpath(decoded)
    if not normalized.startswith("/"):
        normalized = f"/{normalized}"
    if path.endswith("/") and not normalized.endswith("/"):
        normalized = f"{normalized}/"
    if normalized == "/.":
        normalized = "/"
    return quote(normalized, safe="/%:@")


def _normalize_query(query: str) -> str:
    pairs = []
    for key, value in parse_qsl(query, keep_blank_values=True):
        lowered = key.lower()
        if lowered in _TRACKING_QUERY_KEYS:
            continue
        if any(lowered.startswith(prefix) for prefix in _TRACKING_QUERY_PREFIXES):
            continue
        pairs.append((key, value))
    pairs.sort(key=lambda item: (item[0].lower(), item[1]))
    return urlencode(pairs, doseq=True)


def build_url_identity(url: str | None, *, default_scheme: str = "https") -> URLIdentity:
    raw = str(url or "").strip()
    if not raw:
        return URLIdentity(URL_IDENTITY_VERSION, "", "", "", "", "")

    if "://" not in raw and not raw.startswith("//"):
        raw = f"{default_scheme}://{raw}"

    parsed = urlparse(raw)
    scheme = (parsed.scheme or default_scheme).lower()
    host = _normalize_host(parsed.hostname)
    if not scheme or not host:
        return URLIdentity(URL_IDENTITY_VERSION, raw, raw, host, parsed.path, parsed.query)

    try:
        port = parsed.port
    except ValueError:
        return URLIdentity(URL_IDENTITY_VERSION, raw, raw, host, parsed.path, parsed.query)
    netloc = host
    if port and not ((scheme == "http" and port == 80) or (scheme == "https" and port == 443)):
        netloc = f"{host}:{port}"

    path = _normalize_path(parsed.path)
    query = _normalize_query(parsed.query)
    canonical_url = urlunparse((scheme, netloc, path, "", query, ""))
    dedupe_key = f"{URL_IDENTITY_VERSION}:{canonical_url}"
    return URLIdentity(URL_IDENTITY_VERSION, canonical_url, dedupe_key, host, path, query)


def normalize_url(url: str | None) -> str:
    """Return the stable dedupe URL without fragments or tracking params."""
    return build_url_identity(url).canonical_url
