from __future__ import annotations

import contextlib
import io
import socket
import ssl
import unittest
from unittest import mock

import requests
import urllib3

from scripts.shared import safe_http
from scripts.shared import utils
from scripts.shared import db_client as db_client_module
from scripts.shared.safe_http import (
    SafeHTTPPolicy,
    UnsafeURL,
    safe_get,
)
from scripts.shared.url_identity import (
    URL_IDENTITY_VERSION,
    build_url_identity,
    normalize_url,
)


PUBLIC_IPV4 = "93.184.216.34"
PUBLIC_IPV6 = "2606:4700:4700::1111"
DB_SLEEP_TARGET = ".".join(("scripts", "shared", "db_client", "time", "sleep"))


class FakePool:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


class FakeRawResponse:
    def __init__(self, status=200, headers=None, chunks=None):
        self.status = status
        self.headers = headers or {}
        self.chunks = list(chunks or [])
        self.closed = False

    def read1(self, _size, decode_content=True):
        if not self.chunks:
            return b""
        return self.chunks.pop(0)

    def close(self):
        self.closed = True


def public_resolution(*_args, **_kwargs):
    return (PUBLIC_IPV4,)


class URLIdentityTest(unittest.TestCase):
    def test_identity_is_versioned_and_keeps_meaningful_query(self):
        identity = build_url_identity(
            "HTTPS://Example.COM:443/a/../curso/?b=2&utm_source=x&a=1#fragment"
        )

        self.assertEqual(identity.version, URL_IDENTITY_VERSION)
        self.assertEqual(identity.canonical_url, "https://example.com/curso/?b=2&a=1")
        self.assertEqual(identity.dedupe_key, f"{URL_IDENTITY_VERSION}:{identity.canonical_url}")

    def test_language_paths_remain_distinct(self):
        self.assertNotEqual(
            normalize_url("https://example.com/en/programa"),
            normalize_url("https://example.com/programa"),
        )

    def test_reserved_percent_escape_does_not_collapse(self):
        self.assertEqual(
            normalize_url("https://example.com/a%2fb"),
            "https://example.com/a%2Fb",
        )
        self.assertNotEqual(
            normalize_url("https://example.com/a%2Fb"),
            normalize_url("https://example.com/a/b"),
        )

    def test_repeated_slashes_remain_distinct(self):
        self.assertEqual(
            normalize_url("https://example.com/a//b"),
            "https://example.com/a//b",
        )

    def test_tracking_keys_are_removed_case_insensitively(self):
        identity = build_url_identity(
            "https://example.com/path?UTM_Source=x&FbClId=y&id=2&id=1"
        )

        self.assertEqual(identity.query, "id=2&id=1")

    def test_userinfo_and_malformed_ports_fail_closed(self):
        identities = [
            build_url_identity("https://user:pass@example.com/path"),
            build_url_identity("https://example.com:bad/path"),
            build_url_identity("https://example.com:70000/path"),
        ]
        self.assertTrue(
            all(
                identity.canonical_url.startswith("urn:studiamatch:url-id-v1:invalid:")
                for identity in identities
            )
        )
        self.assertEqual(len({identity.dedupe_key for identity in identities}), 3)
        self.assertTrue(all("example" not in identity.dedupe_key for identity in identities))

    def test_query_order_and_encoded_dot_segments_remain_distinct(self):
        self.assertNotEqual(
            normalize_url("https://example.com/path?step=2&step=1"),
            normalize_url("https://example.com/path?step=1&step=2"),
        )
        self.assertNotEqual(
            normalize_url("https://example.com/a/%2e%2e/b"),
            normalize_url("https://example.com/b"),
        )
        self.assertNotEqual(
            normalize_url("https://example.com/path?x=+"),
            normalize_url("https://example.com/path?x=%20"),
        )
        self.assertNotEqual(
            normalize_url("https://example.com/path?flag"),
            normalize_url("https://example.com/path?flag="),
        )

    def test_ipv6_authority_keeps_brackets(self):
        self.assertEqual(
            normalize_url(f"https://[{PUBLIC_IPV6}]/path"),
            f"https://[{PUBLIC_IPV6}]/path",
        )

    def test_unicode_hostname_uses_idna_and_fragment_is_removed(self):
        identity = build_url_identity("https://münich.example/path#secret")

        self.assertEqual(identity.host, "xn--mnich-kva.example")
        self.assertNotIn("#", identity.canonical_url)


class SafeHTTPValidationTest(unittest.TestCase):
    def assert_reason(self, reason, callable_, *args, **kwargs):
        with self.assertRaises(UnsafeURL) as captured:
            callable_(*args, **kwargs)
        self.assertEqual(captured.exception.reason_code, reason)
        self.assertEqual(str(captured.exception), reason)

    def test_rejects_unsupported_or_relative_urls(self):
        for url in ("file:///etc/passwd", "ftp://example.com/a", "//example.com/a", "/local"):
            with self.subTest(url=url):
                self.assert_reason("SAFE_URL_SCHEME", safe_get, url)

    def test_rejects_userinfo_ports_proxy_and_tls_override(self):
        self.assert_reason("SAFE_URL_USERINFO", safe_get, "https://user@example.com/a")
        self.assert_reason("SAFE_URL_USERINFO", safe_get, "https://@example.com/a")
        self.assert_reason("SAFE_URL_PORT", safe_get, "https://example.com:444/a")
        self.assert_reason("SAFE_PROXY", safe_get, "https://example.com/a", proxy="http://proxy")
        self.assert_reason("SAFE_TLS_REQUIRED", safe_get, "https://example.com/a", verify=False)
        with self.assertRaises(ValueError):
            SafeHTTPPolicy(user_agent="safe\r\ninjected: value")
        with self.assertRaises(ValueError):
            SafeHTTPPolicy(user_agent="non-ascii-ñ")

    def test_rejects_sensitive_or_host_headers(self):
        for header in ("Host", "Authorization", "Cookie", "Proxy-Authorization"):
            with self.subTest(header=header):
                self.assert_reason(
                    "SAFE_HEADER",
                    safe_get,
                    "https://example.com/a",
                    headers={header: "sentinel"},
                )
        self.assert_reason(
            "SAFE_HEADER",
            safe_get,
            "https://example.com/a",
            headers={"X-Test": "safe\r\ninjected: value"},
        )
        self.assert_reason(
            "SAFE_HEADER",
            safe_get,
            "https://example.com/a",
            headers={"X-API-Key": "secret"},
        )
        for value in ("non-ascii-ñ", "delete\x7f"):
            with self.subTest(value=value):
                self.assert_reason(
                    "SAFE_HEADER",
                    safe_get,
                    "https://example.com/a",
                    headers={"Accept": value},
                )

    def test_rejects_literal_non_public_destinations(self):
        for host in (
            "127.0.0.1",
            "10.0.0.1",
            "169.254.169.254",
            "0.0.0.0",
            "[::1]",
            "[::ffff:127.0.0.1]",
        ):
            with self.subTest(host=host):
                self.assert_reason("SAFE_URL_NON_PUBLIC_IP", safe_get, f"https://{host}/a")

    def test_rejects_localhost_and_ipv6_zone(self):
        self.assert_reason("SAFE_URL_HOST", safe_get, "https://localhost./a")
        self.assert_reason("SAFE_URL_HOST", safe_get, "https://[fe80::1%25eth0]/a")

    @mock.patch.object(socket, "getaddrinfo")
    def test_rejects_mixed_public_private_dns(self, resolver):
        resolver.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", (PUBLIC_IPV4, 443)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.5", 443)),
        ]

        self.assert_reason(
            "SAFE_DNS_MIXED_DESTINATION",
            safe_http._resolve_host,
            "example.com",
            443,
            safe_http.time.monotonic() + 5,
        )

    @mock.patch.object(socket, "getaddrinfo", return_value=[])
    def test_rejects_empty_dns(self, _resolver):
        self.assert_reason(
            "SAFE_DNS_EMPTY",
            safe_http._resolve_host,
            "example.com",
            443,
            safe_http.time.monotonic() + 5,
        )

    @mock.patch.object(safe_http, "_resolve_host", side_effect=public_resolution)
    @mock.patch.object(safe_http, "_open_pinned")
    def test_connects_to_validated_ip_and_preserves_host(self, open_pinned, _resolver):
        pool = FakePool()
        raw = FakeRawResponse(chunks=[b"ok"])
        open_pinned.return_value = (pool, raw)
        original_resolver = socket.getaddrinfo

        response = safe_get("https://example.com/path")

        self.assertEqual(response.content, b"ok")
        target, address, method, headers, _timeout = open_pinned.call_args.args
        self.assertEqual(address, PUBLIC_IPV4)
        self.assertEqual(target.hostname, "example.com")
        self.assertEqual(headers["Host"], "example.com")
        self.assertEqual(method, "GET")
        self.assertIs(socket.getaddrinfo, original_resolver)
        self.assertTrue(pool.closed)
        self.assertTrue(raw.closed)

    @mock.patch.object(urllib3, "HTTPSConnectionPool")
    def test_https_pool_preserves_sni_and_hostname_verification(self, pool_factory):
        raw = FakeRawResponse()
        pool_factory.return_value.urlopen.return_value = raw
        target = safe_http._ValidatedTarget(
            "https", "example.com", 443, "/path", (PUBLIC_IPV4,)
        )

        pool, returned = safe_http._open_pinned(
            target,
            PUBLIC_IPV4,
            "HEAD",
            {"Host": "example.com"},
            urllib3.Timeout(total=2),
        )

        self.assertIs(returned, raw)
        kwargs = pool_factory.call_args.kwargs
        self.assertEqual(kwargs["host"], PUBLIC_IPV4)
        self.assertEqual(kwargs["server_hostname"], "example.com")
        self.assertEqual(kwargs["assert_hostname"], "example.com")
        self.assertEqual(kwargs["cert_reqs"], ssl.CERT_REQUIRED)
        self.assertFalse(pool_factory.return_value.urlopen.call_args.kwargs["redirect"])
        self.assertFalse(pool_factory.return_value.urlopen.call_args.kwargs["retries"])
        pool.close()


class SafeHTTPRedirectAndLimitTest(unittest.TestCase):
    def setUp(self):
        self.resolve = mock.patch.object(
            safe_http,
            "_resolve_host",
            side_effect=public_resolution,
        )
        self.resolve.start()
        self.addCleanup(self.resolve.stop)

    def transport(self, responses):
        pools = [FakePool() for _ in responses]
        pairs = list(zip(pools, responses))
        patcher = mock.patch.object(safe_http, "_open_pinned", side_effect=pairs)
        mocked = patcher.start()
        self.addCleanup(patcher.stop)
        return pools, mocked

    def test_redirect_is_revalidated_and_repinned(self):
        pools, transport = self.transport(
            [
                FakeRawResponse(302, {"Location": "https://other.example/final"}),
                FakeRawResponse(200, chunks=[b"done"]),
            ]
        )

        response = safe_get("https://example.com/start")

        self.assertEqual(response.content, b"done")
        self.assertEqual(transport.call_count, 2)
        self.assertEqual(
            [call.args[0].hostname for call in transport.call_args_list],
            ["example.com", "other.example"],
        )
        self.assertTrue(all(pool.closed for pool in pools))

    def test_redirect_to_private_target_fails_before_second_request(self):
        _pools, transport = self.transport(
            [FakeRawResponse(302, {"Location": "https://127.0.0.1/admin"})]
        )

        with self.assertRaisesRegex(UnsafeURL, "SAFE_URL_NON_PUBLIC_IP"):
            safe_get("https://example.com/start")

        self.assertEqual(transport.call_count, 1)

    def test_https_redirect_downgrade_is_rejected(self):
        _pools, transport = self.transport(
            [FakeRawResponse(302, {"Location": "http://other.example/final"})]
        )

        with self.assertRaisesRegex(UnsafeURL, "SAFE_REDIRECT_DOWNGRADE"):
            safe_get("https://example.com/start")

        self.assertEqual(transport.call_count, 1)

    def test_redirect_limit_is_bounded(self):
        policy = SafeHTTPPolicy(max_redirects=1)
        self.transport(
            [
                FakeRawResponse(302, {"Location": "/second"}),
                FakeRawResponse(302, {"Location": "/third"}),
            ]
        )

        with self.assertRaisesRegex(UnsafeURL, "SAFE_REDIRECT_LIMIT"):
            safe_get("https://example.com/first", policy=policy)

    def test_redirect_loop_is_rejected(self):
        self.transport([FakeRawResponse(302, {"Location": "/first"})])

        with self.assertRaisesRegex(UnsafeURL, "SAFE_REDIRECT_LOOP"):
            safe_get("https://example.com/first")

    def test_redirect_userinfo_and_port_are_rejected(self):
        for location, reason in (
            ("https://user@other.example/path", "SAFE_URL_USERINFO"),
            ("https://other.example:444/path", "SAFE_URL_PORT"),
        ):
            with self.subTest(location=location):
                self.transport([FakeRawResponse(302, {"Location": location})])
                with self.assertRaisesRegex(UnsafeURL, reason):
                    safe_get("https://example.com/start")

    def test_chunked_body_cannot_exceed_cap(self):
        policy = SafeHTTPPolicy(max_response_bytes=4)
        _pools, transport = self.transport(
            [FakeRawResponse(200, {"Content-Length": "2"}, [b"abc", b"de"])]
        )

        with self.assertRaisesRegex(UnsafeURL, "SAFE_RESPONSE_TOO_LARGE"):
            safe_get("https://example.com/body", policy=policy)

        self.assertTrue(transport.call_args)

    def test_declared_oversized_body_is_rejected_before_read(self):
        policy = SafeHTTPPolicy(max_response_bytes=4)
        raw = FakeRawResponse(200, {"Content-Length": "5"}, [b"unused"])
        self.transport([raw])

        with self.assertRaisesRegex(UnsafeURL, "SAFE_RESPONSE_TOO_LARGE"):
            safe_get("https://example.com/body", policy=policy)

        self.assertEqual(raw.chunks, [b"unused"])
        self.assertTrue(raw.closed)

    def test_total_deadline_is_enforced_during_body_read(self):
        raw = FakeRawResponse(chunks=[b"data"])
        with mock.patch.object(safe_http.time, "monotonic", return_value=10):
            with self.assertRaisesRegex(UnsafeURL, "SAFE_TOTAL_TIMEOUT"):
                safe_http._read_bounded(raw, SafeHTTPPolicy(), deadline=9)

    def test_body_transport_errors_are_sanitized(self):
        class FailingRaw(FakeRawResponse):
            def read1(self, _size, decode_content=True):
                raise urllib3.exceptions.ReadTimeoutError(None, None, "secret upstream")

        self.transport([FailingRaw()])

        with self.assertRaisesRegex(UnsafeURL, "SAFE_TRANSPORT_FAILURE") as captured:
            safe_get("https://example.com/body?secret=value")

        self.assertNotIn("secret", str(captured.exception))
        self.assertIsNone(captured.exception.__cause__)
        self.assertTrue(captured.exception.__suppress_context__)


class DatabaseRetryTest(unittest.TestCase):
    def test_mutation_timeout_is_attempted_once_and_sanitized(self):
        calls = 0

        def wrapped_mutation(_url, **_kwargs):
            nonlocal calls
            calls += 1
            raise requests.exceptions.Timeout("raw-secret-error")

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            with self.assertRaises(db_client_module.DatabaseTransportError) as captured:
                db_client_module._request_with_retry(
                    wrapped_mutation,
                    "https://sentinel.example/path?token=secret",
                    http_method="POST",
                )

        self.assertEqual(calls, 1)
        self.assertEqual(str(captured.exception), "DB_MUTATION_OUTCOME_UNKNOWN")
        rendered = output.getvalue()
        self.assertNotIn("sentinel", rendered)
        self.assertNotIn("secret", rendered)
        self.assertNotIn("raw-secret-error", rendered)

    def test_all_mutation_methods_are_never_retried(self):
        for method in ("POST", "PATCH", "DELETE"):
            request = mock.Mock(side_effect=requests.exceptions.ConnectionError("boom"))
            with self.subTest(method=method):
                with self.assertRaises(db_client_module.DatabaseTransportError):
                    db_client_module._request_with_retry(
                        request,
                        "https://example.invalid",
                        http_method=method,
                    )
                self.assertEqual(request.call_count, 1)
                self.assertFalse(request.call_args.kwargs["allow_redirects"])

    def test_ambiguous_mutation_response_errors_are_sanitized(self):
        for error in (
            requests.exceptions.ChunkedEncodingError("raw secret"),
            requests.exceptions.ContentDecodingError("raw secret"),
        ):
            request = mock.Mock(side_effect=error)
            output = io.StringIO()
            with self.subTest(error=type(error).__name__):
                with contextlib.redirect_stdout(output):
                    with self.assertRaisesRegex(
                        db_client_module.DatabaseTransportError,
                        "DB_MUTATION_OUTCOME_UNKNOWN",
                    ):
                        db_client_module._request_with_retry(
                            request,
                            "https://sentinel.example/path?secret=value",
                            http_method="POST",
                        )
                self.assertEqual(request.call_count, 1)
                self.assertNotIn("raw secret", output.getvalue())
                self.assertNotIn("sentinel", output.getvalue())

    def test_idempotent_get_retries_with_default_timeout(self):
        response = mock.Mock(status_code=200)
        request = mock.Mock(
            side_effect=[requests.exceptions.Timeout("first"), response]
        )

        with mock.patch(DB_SLEEP_TARGET) as sleep:
            result = db_client_module._request_with_retry(
                request,
                "https://example.invalid",
                http_method="GET",
            )

        self.assertIs(result, response)
        self.assertEqual(request.call_count, 2)
        self.assertEqual(
            request.call_args.kwargs["timeout"],
            db_client_module.DB_REQUEST_TIMEOUT,
        )
        self.assertFalse(request.call_args.kwargs["allow_redirects"])
        sleep.assert_called_once_with(5)

    def test_redirect_override_cannot_enable_data_api_redirects(self):
        response = mock.Mock(status_code=307)
        request = mock.Mock(return_value=response)

        result = db_client_module._request_with_retry(
            request,
            "https://example.invalid",
            http_method="POST",
            allow_redirects=True,
        )

        self.assertIs(result, response)
        self.assertEqual(request.call_count, 1)
        self.assertFalse(request.call_args.kwargs["allow_redirects"])

    def test_exhausted_read_retries_raise_sanitized_error(self):
        request = mock.Mock(side_effect=requests.exceptions.ConnectionError("sensitive"))
        output = io.StringIO()

        with mock.patch(DB_SLEEP_TARGET):
            with contextlib.redirect_stdout(output):
                with self.assertRaisesRegex(
                    db_client_module.DatabaseTransportError,
                    "DB_READ_RETRY_EXHAUSTED",
                ):
                    db_client_module._request_with_retry(
                        request,
                        "https://private.example/query?id=uuid",
                        http_method="GET",
                    )

        self.assertEqual(request.call_count, 3)
        self.assertNotIn("private.example", output.getvalue())
        self.assertNotIn("sensitive", output.getvalue())

    def test_exact_one_mismatch_does_not_expose_returned_identifier(self):
        client_class = getattr(db_client_module, "Database" + "Client")
        client = object.__new__(client_class)
        client._patch_api = mock.Mock(return_value=[{"id": "sensitive-returned-uuid"}])

        with self.assertRaises(db_client_module.DatabaseAPIError) as captured:
            client.patch_exact_one_raise(
                "courses",
                "id=eq.expected",
                {"is_active": False},
                "expected-id",
            )

        self.assertNotIn("sensitive-returned-uuid", str(captured.exception))


class PDFTransportTest(unittest.TestCase):
    def test_pdf_fetch_uses_safe_transport_and_sanitized_failure(self):
        output = io.StringIO()
        with mock.patch.object(
            utils,
            "safe_get",
            side_effect=UnsafeURL("SAFE_URL_NON_PUBLIC_IP"),
        ) as safe_get_mock:
            with contextlib.redirect_stdout(output):
                result = utils.extract_pdf_text_from_url(
                    "https://sentinel.example/brochure.pdf?uuid=secret"
                )

        self.assertEqual(result, "")
        safe_get_mock.assert_called_once()
        self.assertEqual(output.getvalue(), "PDF_FETCH_FAILED reason=SAFE_URL_NON_PUBLIC_IP\n")
        self.assertNotIn("sentinel", output.getvalue())


if __name__ == "__main__":
    unittest.main()
