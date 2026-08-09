from __future__ import annotations

import ipaddress
import socket
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from urllib.parse import urlparse

import requests


class UnsafeURL(RuntimeError):
    """Raised when a URL targets a non-public or unsupported destination."""


@dataclass(frozen=True)
class SafeHTTPPolicy:
    allowed_schemes: tuple[str, ...] = ("http", "https")
    blocked_hostnames: tuple[str, ...] = ("localhost",)
    timeout: int = 20


DEFAULT_POLICY = SafeHTTPPolicy()
_DNS_PIN_LOCK = threading.RLock()


def _public_ip_addresses(hostname: str) -> tuple[str, ...]:
    try:
        infos = socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise UnsafeURL(f"Unable to resolve host: {hostname}") from exc

    addresses = sorted({info[4][0] for info in infos})
    if not addresses:
        raise UnsafeURL(f"Unable to resolve host: {hostname}")

    for address in addresses:
        ip = ipaddress.ip_address(address)
        if not ip.is_global:
            raise UnsafeURL(f"Blocked non-public address for {hostname}: {address}")
    return tuple(addresses)


def validate_public_url(url: str, *, policy: SafeHTTPPolicy = DEFAULT_POLICY) -> tuple[str, tuple[str, ...]]:
    parsed = urlparse(str(url or "").strip())
    scheme = parsed.scheme.lower()
    if scheme not in policy.allowed_schemes:
        raise UnsafeURL(f"Unsupported URL scheme: {parsed.scheme or '<missing>'}")

    hostname = (parsed.hostname or "").strip().rstrip(".").lower()
    if not hostname:
        raise UnsafeURL("URL is missing a hostname")
    if hostname in policy.blocked_hostnames:
        raise UnsafeURL(f"Blocked hostname: {hostname}")

    addresses = _public_ip_addresses(hostname)
    return hostname, addresses


@contextmanager
def _pinned_dns(hostname: str, addresses: tuple[str, ...]):
    original_getaddrinfo = socket.getaddrinfo

    def getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        normalized_host = str(host or "").strip().rstrip(".").lower()
        if normalized_host == hostname:
            return [
                (
                    socket.AF_INET6 if ":" in address else socket.AF_INET,
                    type or socket.SOCK_STREAM,
                    proto or socket.IPPROTO_TCP,
                    "",
                    (address, port, 0, 0) if ":" in address else (address, port),
                )
                for address in addresses
            ]
        return original_getaddrinfo(host, port, family, type, proto, flags)

    with _DNS_PIN_LOCK:
        socket.getaddrinfo = getaddrinfo
        try:
            yield
        finally:
            socket.getaddrinfo = original_getaddrinfo


def safe_request(method: str, url: str, *, policy: SafeHTTPPolicy = DEFAULT_POLICY, **kwargs):
    hostname, addresses = validate_public_url(url, policy=policy)
    if kwargs.get("allow_redirects") is True:
        raise UnsafeURL("Redirect following is disabled for safe HTTP requests")
    kwargs.setdefault("timeout", policy.timeout)
    kwargs["allow_redirects"] = False
    with _pinned_dns(hostname, addresses):
        return requests.request(method, url, **kwargs)


def safe_get(url: str, *, policy: SafeHTTPPolicy = DEFAULT_POLICY, **kwargs):
    return safe_request("GET", url, policy=policy, **kwargs)


def safe_head(url: str, *, policy: SafeHTTPPolicy = DEFAULT_POLICY, **kwargs):
    return safe_request("HEAD", url, policy=policy, **kwargs)
