from __future__ import annotations

import hashlib
import ipaddress
import re
from dataclasses import dataclass
from urllib.parse import quote, unquote_plus, urlsplit, urlunsplit


URL_IDENTITY_VERSION = "url-id-v1"
_PERCENT_ESCAPE = re.compile(r"%([0-9a-fA-F]{2})")
_UNRESERVED = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_~"
)
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


def _invalid_identity(raw: str) -> URLIdentity:
    fingerprint = hashlib.sha256(raw.encode("utf-8", errors="replace")).hexdigest()
    opaque_identity = f"urn:studiamatch:{URL_IDENTITY_VERSION}:invalid:{fingerprint}"
    return URLIdentity(
        URL_IDENTITY_VERSION,
        opaque_identity,
        opaque_identity,
        "",
        "",
        "",
    )


def _normalize_host(hostname: str) -> str:
    host = hostname.strip().rstrip(".").lower()
    if not host or "%" in host:
        return ""
    try:
        return str(ipaddress.ip_address(host))
    except ValueError:
        try:
            return host.encode("idna").decode("ascii")
        except UnicodeError:
            return ""


def _normalize_percent_encoding(path: str) -> str:
    def replace(match: re.Match[str]) -> str:
        character = chr(int(match.group(1), 16))
        return character if character in _UNRESERVED else match.group(0).upper()

    return _PERCENT_ESCAPE.sub(replace, path)


def _normalize_path(path: str) -> str:
    if not path:
        return "/"
    escaped = _normalize_percent_encoding(path)
    output: list[str] = []
    for segment in escaped.split("/"):
        if segment == ".":
            continue
        if segment == "..":
            if output and output[-1] != "":
                output.pop()
            continue
        output.append(segment)
    normalized = "/".join(output)
    if not normalized.startswith("/"):
        normalized = f"/{normalized}"
    if escaped.endswith("/") and normalized != "/" and not normalized.endswith("/"):
        normalized = f"{normalized}/"
    return quote(normalized, safe="/%:@!$&'()*+,;=-._~")


def _normalize_query(query: str) -> str:
    segments = []
    for segment in query.split("&"):
        raw_key = segment.partition("=")[0]
        try:
            lowered = unquote_plus(raw_key, errors="strict").lower()
        except UnicodeDecodeError:
            lowered = raw_key.lower()
        if lowered in _TRACKING_QUERY_KEYS or lowered.startswith(_TRACKING_QUERY_PREFIXES):
            continue
        segments.append(segment)
    return "&".join(segments)


def build_url_identity(
    url: str | None,
    *,
    default_scheme: str = "https",
) -> URLIdentity:
    raw = str(url or "").strip()
    if not raw:
        return URLIdentity(URL_IDENTITY_VERSION, "", "", "", "", "")
    if any(ord(character) < 32 for character in raw):
        return _invalid_identity(raw)
    if "://" not in raw and not raw.startswith("//"):
        raw = f"{default_scheme}://{raw}"

    try:
        parsed = urlsplit(raw)
    except ValueError:
        return _invalid_identity(raw)
    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"} or not parsed.netloc:
        return _invalid_identity(raw)
    if parsed.username is not None or parsed.password is not None or "@" in parsed.netloc:
        return _invalid_identity(raw)
    host = _normalize_host(parsed.hostname or "")
    if not host:
        return _invalid_identity(raw)
    try:
        port = parsed.port
    except ValueError:
        return _invalid_identity(raw)
    if port is not None and not 1 <= port <= 65535:
        return _invalid_identity(raw)

    authority_host = f"[{host}]" if ":" in host else host
    default_port = 443 if scheme == "https" else 80
    netloc = authority_host if port in (None, default_port) else f"{authority_host}:{port}"
    path = _normalize_path(parsed.path)
    query = _normalize_query(parsed.query)
    canonical_url = urlunsplit((scheme, netloc, path, query, ""))
    return URLIdentity(
        URL_IDENTITY_VERSION,
        canonical_url,
        f"{URL_IDENTITY_VERSION}:{canonical_url}",
        host,
        path,
        query,
    )


def normalize_url(url: str | None) -> str:
    """Return a versioned, deterministic dedupe URL or an empty invalid identity."""
    return build_url_identity(url).canonical_url
