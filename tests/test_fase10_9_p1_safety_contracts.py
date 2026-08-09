import socket
import unittest
from unittest import mock

import requests

from scripts.shared.db_client import _request_with_retry
from scripts.shared.safe_http import UnsafeURL, safe_get, validate_public_url
from scripts.shared.url_identity import URL_IDENTITY_VERSION, build_url_identity, normalize_url


class Fase109P1SafetyContractsTest(unittest.TestCase):
    def test_url_identity_is_versioned_and_preserves_meaningful_query(self):
        identity = build_url_identity(
            "HTTPS://Example.COM:443/a/../curso/?b=2&utm_source=x&a=1#fragment"
        )

        self.assertEqual(identity.version, URL_IDENTITY_VERSION)
        self.assertEqual(identity.canonical_url, "https://example.com/curso/?a=1&b=2")
        self.assertEqual(
            identity.dedupe_key,
            f"{URL_IDENTITY_VERSION}:https://example.com/curso/?a=1&b=2",
        )

    def test_normalize_url_does_not_collapse_language_paths(self):
        self.assertEqual(
            normalize_url("https://example.com/en/programa"),
            "https://example.com/en/programa",
        )
        self.assertEqual(
            normalize_url("https://example.com/programa"),
            "https://example.com/programa",
        )

    def test_safe_http_blocks_localhost_before_request(self):
        with mock.patch.object(requests, "request") as request_mock:
            with self.assertRaises(UnsafeURL):
                safe_get("http://localhost/admin")

        request_mock.assert_not_called()

    def test_safe_http_rejects_redirect_override(self):
        with mock.patch.object(
            socket,
            "getaddrinfo",
            return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))],
        ):
            with self.assertRaises(UnsafeURL):
                safe_get("https://example.com/path", allow_redirects=True)

    def test_safe_http_blocks_private_dns_resolution(self):
        with mock.patch.object(
            socket,
            "getaddrinfo",
            return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.5", 443))],
        ):
            with self.assertRaises(UnsafeURL):
                validate_public_url("https://internal.example")

    def test_safe_http_allows_public_dns_resolution_without_fetching(self):
        with mock.patch.object(
            socket,
            "getaddrinfo",
            return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))],
        ):
            hostname, addresses = validate_public_url("https://example.com/path")

        self.assertEqual(hostname, "example.com")
        self.assertEqual(addresses, ("93.184.216.34",))

    def test_safe_http_pins_dns_for_request(self):
        calls = []

        def fake_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
            calls.append(host)
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))]

        def fake_request(method, url, **kwargs):
            resolved = socket.getaddrinfo("example.com", 443)
            self.assertEqual(resolved[0][4][0], "93.184.216.34")
            return object()

        with mock.patch.object(socket, "getaddrinfo", fake_getaddrinfo):
            with mock.patch.object(requests, "request", fake_request):
                safe_get("https://example.com/path")

        self.assertEqual(calls, ["example.com"])

    def test_url_identity_handles_malformed_port(self):
        identity = build_url_identity("https://example.com:bad/path")

        self.assertEqual(identity.canonical_url, "https://example.com:bad/path")

    def test_db_client_does_not_retry_mutation_timeouts(self):
        calls = 0

        def post(url, **kwargs):
            nonlocal calls
            calls += 1
            raise requests.exceptions.Timeout("boom")

        with self.assertRaises(requests.exceptions.Timeout):
            _request_with_retry(post, "https://example.supabase.co/rest/v1/table")

        self.assertEqual(calls, 1)

    def test_db_client_retries_idempotent_get(self):
        calls = 0

        class Response:
            status_code = 200

        def get(url, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise requests.exceptions.Timeout("boom")
            return Response()

        with mock.patch("scripts.shared.db_client.time.sleep", lambda delay: None):
            response = _request_with_retry(get, "https://example.supabase.co/rest/v1/table")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(calls, 2)


if __name__ == "__main__":
    unittest.main()
