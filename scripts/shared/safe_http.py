from __future__ import annotations

import ipaddress
import json
import queue
import socket
import ssl
import threading
import time
from dataclasses import dataclass
from typing import Mapping
from urllib.parse import urljoin, urlsplit, urlunsplit

import certifi
import urllib3


_REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})
_SAFE_METHODS = frozenset({"GET", "HEAD"})
_ALLOWED_HEADERS = frozenset({"accept"})


class UnsafeURL(RuntimeError):
    """Fail-closed HTTP error whose message is always a sanitized reason code."""

    def __init__(self, reason_code: str):
        self.reason_code = reason_code
        super().__init__(reason_code)


@dataclass(frozen=True)
class SafeHTTPPolicy:
    max_redirects: int = 3
    total_timeout_seconds: float = 20.0
    connect_timeout_seconds: float = 4.0
    read_timeout_seconds: float = 2.0
    max_response_bytes: int = 8 * 1024 * 1024
    user_agent: str = "StudIAMatch-SafeHTTP/1.0"

    def __post_init__(self) -> None:
        if self.max_redirects < 0:
            raise ValueError("max_redirects must be non-negative")
        if min(
            self.total_timeout_seconds,
            self.connect_timeout_seconds,
            self.read_timeout_seconds,
        ) <= 0:
            raise ValueError("timeouts must be positive")
        if self.max_response_bytes <= 0:
            raise ValueError("max_response_bytes must be positive")
        if (
            not self.user_agent
            or len(self.user_agent) > 256
            or any(not 32 <= ord(character) <= 126 for character in self.user_agent)
        ):
            raise ValueError("user_agent must use bounded visible ASCII")


@dataclass(frozen=True)
class SafeHTTPResponse:
    status_code: int
    headers: Mapping[str, str]
    content: bytes

    @property
    def text(self) -> str:
        return self.content.decode("utf-8", errors="replace")

    def json(self):
        return json.loads(self.content)

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            error = UnsafeURL("SAFE_HTTP_STATUS")
            error.status_code = self.status_code
            raise error


@dataclass(frozen=True)
class _ValidatedTarget:
    scheme: str
    hostname: str
    port: int
    request_target: str
    addresses: tuple[str, ...]

    @property
    def host_header(self) -> str:
        if ":" in self.hostname:
            return f"[{self.hostname}]"
        return self.hostname


DEFAULT_POLICY = SafeHTTPPolicy()


def _remaining(deadline: float) -> float:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise UnsafeURL("SAFE_TOTAL_TIMEOUT")
    return remaining


def _is_public_ip(value: str) -> bool:
    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        return False
    if getattr(address, "ipv4_mapped", None) is not None:
        address = address.ipv4_mapped
    return address.is_global and not (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
    )


def _resolve_host(hostname: str, port: int, deadline: float) -> tuple[str, ...]:
    results: queue.Queue[object] = queue.Queue(maxsize=1)

    def resolve() -> None:
        try:
            infos = socket.getaddrinfo(
                hostname,
                port,
                type=socket.SOCK_STREAM,
            )
            results.put(infos)
        except OSError:
            results.put(None)

    thread = threading.Thread(target=resolve, daemon=True)
    thread.start()
    try:
        infos = results.get(timeout=_remaining(deadline))
    except queue.Empty:
        raise UnsafeURL("SAFE_TOTAL_TIMEOUT") from None
    if infos is None:
        raise UnsafeURL("SAFE_DNS_FAILURE")

    addresses = tuple(dict.fromkeys(info[4][0] for info in infos))
    if not addresses:
        raise UnsafeURL("SAFE_DNS_EMPTY")
    public = tuple(address for address in addresses if _is_public_ip(address))
    if len(public) != len(addresses):
        reason = "SAFE_DNS_MIXED_DESTINATION" if public else "SAFE_URL_NON_PUBLIC_IP"
        raise UnsafeURL(reason)
    return public


def _validate_target(url: str, deadline: float) -> _ValidatedTarget:
    raw = str(url or "").strip()
    if not raw or any(ord(character) < 32 for character in raw):
        raise UnsafeURL("SAFE_URL_FORMAT")
    try:
        parsed = urlsplit(raw)
    except ValueError:
        raise UnsafeURL("SAFE_URL_FORMAT") from None
    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"} or not parsed.netloc:
        raise UnsafeURL("SAFE_URL_SCHEME")
    if parsed.username is not None or parsed.password is not None or "@" in parsed.netloc:
        raise UnsafeURL("SAFE_URL_USERINFO")

    hostname = parsed.hostname
    if not hostname or "%" in hostname:
        raise UnsafeURL("SAFE_URL_HOST")
    try:
        hostname = hostname.rstrip(".").encode("idna").decode("ascii").lower()
    except UnicodeError:
        raise UnsafeURL("SAFE_URL_HOST") from None
    if not hostname or hostname == "localhost" or hostname.endswith(".localhost"):
        raise UnsafeURL("SAFE_URL_HOST")
    try:
        port = parsed.port
    except ValueError:
        raise UnsafeURL("SAFE_URL_PORT") from None
    expected_port = 443 if scheme == "https" else 80
    if port not in (None, expected_port):
        raise UnsafeURL("SAFE_URL_PORT")

    try:
        literal = ipaddress.ip_address(hostname)
    except ValueError:
        addresses = _resolve_host(hostname, expected_port, deadline)
    else:
        if not _is_public_ip(str(literal)):
            raise UnsafeURL("SAFE_URL_NON_PUBLIC_IP")
        addresses = (str(literal),)

    request_target = urlunsplit(("", "", parsed.path or "/", parsed.query, ""))
    return _ValidatedTarget(
        scheme=scheme,
        hostname=hostname,
        port=expected_port,
        request_target=request_target,
        addresses=addresses,
    )


def _open_pinned(
    target: _ValidatedTarget,
    address: str,
    method: str,
    headers: Mapping[str, str],
    timeout: urllib3.Timeout,
):
    common = {
        "host": address,
        "port": target.port,
        "timeout": timeout,
        "maxsize": 1,
        "block": True,
        "retries": False,
    }
    if target.scheme == "https":
        pool = urllib3.HTTPSConnectionPool(
            **common,
            cert_reqs=ssl.CERT_REQUIRED,
            ca_certs=certifi.where(),
            assert_hostname=target.hostname,
            server_hostname=target.hostname,
        )
    else:
        pool = urllib3.HTTPConnectionPool(**common)
    try:
        response = pool.urlopen(
            method,
            target.request_target,
            headers=headers,
            redirect=False,
            retries=False,
            assert_same_host=False,
            preload_content=False,
            decode_content=True,
            timeout=timeout,
        )
    except urllib3.exceptions.SSLError:
        pool.close()
        raise UnsafeURL("SAFE_TLS_VERIFY") from None
    except (urllib3.exceptions.HTTPError, OSError):
        pool.close()
        raise UnsafeURL("SAFE_TRANSPORT_FAILURE") from None
    return pool, response


def _read_bounded(response, policy: SafeHTTPPolicy, deadline: float) -> bytes:
    declared = next(
        (
            value
            for key, value in response.headers.items()
            if str(key).lower() == "content-length"
        ),
        None,
    )
    if declared:
        try:
            if int(declared) > policy.max_response_bytes:
                raise UnsafeURL("SAFE_RESPONSE_TOO_LARGE")
        except ValueError:
            pass

    content = bytearray()
    while True:
        _remaining(deadline)
        chunk = response.read1(64 * 1024, decode_content=True)
        if not chunk:
            break
        content.extend(chunk)
        if len(content) > policy.max_response_bytes:
            raise UnsafeURL("SAFE_RESPONSE_TOO_LARGE")
    _remaining(deadline)
    return bytes(content)


def safe_request(
    method: str,
    url: str,
    *,
    policy: SafeHTTPPolicy = DEFAULT_POLICY,
    headers: Mapping[str, str] | None = None,
    proxy: str | None = None,
    verify: bool = True,
) -> SafeHTTPResponse:
    method = str(method or "").upper()
    if method not in _SAFE_METHODS:
        raise UnsafeURL("SAFE_METHOD")
    if proxy is not None:
        raise UnsafeURL("SAFE_PROXY")
    if verify is not True:
        raise UnsafeURL("SAFE_TLS_REQUIRED")

    request_headers = {str(key): str(value) for key, value in (headers or {}).items()}
    if any(
        key.lower() not in _ALLOWED_HEADERS
        or len(key) > 64
        or len(value) > 1024
        or any(not 33 <= ord(character) <= 126 for character in key)
        or any(not 32 <= ord(character) <= 126 for character in value)
        for key, value in request_headers.items()
    ):
        raise UnsafeURL("SAFE_HEADER")
    request_headers.setdefault("User-Agent", policy.user_agent)

    deadline = time.monotonic() + policy.total_timeout_seconds
    current_url = str(url or "")
    initial_scheme: str | None = None
    visited: set[str] = set()
    redirects = 0
    while True:
        target = _validate_target(current_url, deadline)
        if initial_scheme is None:
            initial_scheme = target.scheme
        elif initial_scheme == "https" and target.scheme != "https":
            raise UnsafeURL("SAFE_REDIRECT_DOWNGRADE")
        if current_url in visited:
            raise UnsafeURL("SAFE_REDIRECT_LOOP")
        visited.add(current_url)

        remaining = _remaining(deadline)
        timeout = urllib3.Timeout(
            total=remaining,
            connect=min(policy.connect_timeout_seconds, remaining),
            read=min(policy.read_timeout_seconds, remaining),
        )
        hop_headers = dict(request_headers)
        hop_headers["Host"] = target.host_header
        pool, response = _open_pinned(
            target,
            target.addresses[0],
            method,
            hop_headers,
            timeout,
        )
        try:
            response_headers = {
                str(key).lower(): str(value) for key, value in response.headers.items()
            }
            if response.status in _REDIRECT_STATUSES:
                location = response_headers.get("location")
                if not location:
                    raise UnsafeURL("SAFE_REDIRECT_LOCATION")
                if redirects >= policy.max_redirects:
                    raise UnsafeURL("SAFE_REDIRECT_LIMIT")
                redirects += 1
                current_url = urljoin(current_url, location)
                continue
            try:
                content = b"" if method == "HEAD" else _read_bounded(
                    response,
                    policy,
                    deadline,
                )
            except UnsafeURL:
                raise
            except (urllib3.exceptions.HTTPError, OSError, ValueError):
                raise UnsafeURL("SAFE_TRANSPORT_FAILURE") from None
            return SafeHTTPResponse(response.status, response_headers, content)
        finally:
            try:
                response.close()
            finally:
                pool.close()


def safe_get(
    url: str,
    *,
    policy: SafeHTTPPolicy = DEFAULT_POLICY,
    headers: Mapping[str, str] | None = None,
    proxy: str | None = None,
    verify: bool = True,
) -> SafeHTTPResponse:
    return safe_request(
        "GET",
        url,
        policy=policy,
        headers=headers,
        proxy=proxy,
        verify=verify,
    )


def safe_head(
    url: str,
    *,
    policy: SafeHTTPPolicy = DEFAULT_POLICY,
    headers: Mapping[str, str] | None = None,
    proxy: str | None = None,
    verify: bool = True,
) -> SafeHTTPResponse:
    return safe_request(
        "HEAD",
        url,
        policy=policy,
        headers=headers,
        proxy=proxy,
        verify=verify,
    )
