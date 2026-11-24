"""Boundary adapters for the isolated FG2 PG17/PostgREST fixture.

Only HTTP endpoints, DNS answers for the reserved synthetic test domain, and
the external model-response boundary are substituted. The real provider
orchestrator, pipeline code, budgets, URL policy, Playwright, parsers, SQL/RPCs,
and stage entrypoints remain the candidate implementations.
"""

from __future__ import annotations

import atexit
import base64
import hashlib
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import re
import requests
import socket
import sys
import threading
import time as _real_time
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlsplit, urlunsplit

os.environ["PYTHON_DOTENV_DISABLED"] = "1"
_core_script_dir = str(Path(__file__).resolve().parents[2] / "scripts" / "core")
if _core_script_dir not in sys.path:
    sys.path.insert(0, _core_script_dir)


def _b64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _jwt(role: str = "service_role", sub: str | None = None) -> str:
    secret = os.environ["FG2_FIXTURE_JWT_SECRET"].encode("utf-8")
    header = _b64url(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    claims = {"role": role, "iat": int(_real_time.time()), "exp": int(_real_time.time()) + 7200}
    if sub:
        claims.update({"sub": sub, "aal": "aal2"})
    payload = _b64url(json.dumps(claims, separators=(",", ":")).encode())
    content = f"{header}.{payload}".encode("ascii")
    signature = _b64url(hmac.new(secret, content, hashlib.sha256).digest())
    return f"{header}.{payload}.{signature}"


SERVICE_JWT = _jwt()


def _fixture_url_key(value: str) -> str:
    parsed = urlsplit(str(value))
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path or "/", parsed.query, ""))


_response_path = Path(os.environ["FG2_FIXTURE_RESPONSE_FILE"])
_responses = json.loads(_response_path.read_text(encoding="utf-8"))
_responses = {_fixture_url_key(key): value for key, value in _responses.items()}
_event_path = Path(os.environ["FG2_FIXTURE_EVENT_LOG"])


def _record(url: str, *, status: int, pinned: bool, boundary: str) -> None:
    parsed = urlsplit(url)
    event = {
        "boundary": boundary,
        "run_id": os.environ.get("GITHUB_RUN_ID", "unknown"),
        "host": parsed.hostname or "invalid",
        "path": parsed.path or "/",
        "query": parsed.query,
        "status": status,
        "pinned": bool(pinned),
    }
    line = (json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n").encode()
    descriptor = os.open(_event_path, os.O_CREAT | os.O_APPEND | os.O_WRONLY, 0o600)
    try:
        os.write(descriptor, line)
    finally:
        os.close(descriptor)


def _record_api_response(method: str, url: str, status: int) -> None:
    parsed = urlsplit(str(url))
    if parsed.netloc != "postgrest:3000" or not parsed.path.startswith("/rest/v1/"):
        return
    event = {
        "boundary": "postgrest_api",
        "method": method.upper(),
        "resource": parsed.path.removeprefix("/rest/v1/")[:100],
        "status": int(status),
    }
    line = (json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n").encode()
    descriptor = os.open(_event_path, os.O_CREAT | os.O_APPEND | os.O_WRONLY, 0o600)
    try:
        os.write(descriptor, line)
    finally:
        os.close(descriptor)


for _method_name in ("get", "post", "patch", "delete"):
    _original_request = getattr(requests, _method_name)

    def _request_with_safe_status(method_name, original_request):
        def _wrapped(url, *args, **kwargs):
            parsed = urlsplit(str(url))
            routed_url = url
            if parsed.netloc == "postgrest:3000" and parsed.path.startswith("/rest/v1/"):
                # Supabase's Kong gateway owns /rest/v1; standalone PostgREST
                # serves the same resource path at /. This fixture-only route
                # adapter preserves the real PostgREST request and response.
                routed_url = urlunsplit((
                    parsed.scheme,
                    parsed.netloc,
                    parsed.path.removeprefix("/rest/v1"),
                    parsed.query,
                    "",
                ))
            response = original_request(routed_url, *args, **kwargs)
            _record_api_response(method_name, url, response.status_code)
            return response

        return _wrapped

    setattr(requests, _method_name, _request_with_safe_status(_method_name, _original_request))


class _SyntheticResponse:
    def __init__(self, url: str, value: dict, *, forced_status: int | None = None, pinned: bool = True, boundary: str):
        self.url = str(value.get("final_url") or url)
        self.status_code = int(forced_status if forced_status is not None else value.get("status", 599))
        self.status = self.status_code
        self.headers = {str(k).lower(): str(v) for k, v in (value.get("headers") or {}).items()}
        content_type = value.get("content_type")
        if content_type:
            self.headers.setdefault("content-type", str(content_type))
        self.content = str(value.get("body", "")).encode("utf-8")
        self.text = self.content.decode("utf-8", errors="replace")
        self.pinned = pinned
        self.closed = False
        _record(url, status=self.status_code, pinned=pinned, boundary=boundary)

    def iter_content(self, chunk_size: int = 65536):
        for offset in range(0, len(self.content), chunk_size):
            yield self.content[offset : offset + chunk_size]

    def close(self):
        self.closed = True


def _lookup_response(url: str, *, boundary: str, pinned: bool):
    key = _fixture_url_key(url)
    value = _responses.get(key)
    if value is None:
        return _SyntheticResponse(
            url,
            {"status": 599, "content_type": "text/plain", "body": "unmapped synthetic fixture request"},
            pinned=pinned,
            boundary=boundary,
        )
    return _SyntheticResponse(url, value, pinned=pinned, boundary=boundary)


_original_getaddrinfo = socket.getaddrinfo


def _synthetic_public_dns(host, port, *args, **kwargs):
    hostname = str(host or "").rstrip(".").lower()
    if hostname.endswith(".fg2.example"):
        return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("93.184.216.34", port or 443))]
    return _original_getaddrinfo(host, port, *args, **kwargs)


socket.getaddrinfo = _synthetic_public_dns


class _VirtualClock:
    def __init__(self):
        self.value = 1_000_000.0

    def monotonic(self):
        return self.value

    async def sleep(self, seconds):
        self.value += max(0.0, float(seconds))

    def advance(self, seconds):
        self.value += max(0.0, float(seconds))


_clock = _VirtualClock()


async def _synthetic_budget_requester(_session, url, prepared, _impersonate, _timeout):
    from curl_cffi import CurlOpt

    pinned = bool(prepared and prepared.get(CurlOpt.RESOLVE))
    response = _lookup_response(url, boundary="harvester_budget", pinned=pinned)
    if not pinned:
        response.status_code = response.status = 598
    return response


from scripts.core import fg2_bounded_run as _bounded
from scripts.shared import db_client as _db_client
from scripts.shared import utils as _script_utils
import shared.db_client as _legacy_import_path_db_client
import shared.utils as _legacy_utils
from scripts.shared import site_diagnostics as _diagnostics
from curl_cffi import CurlOpt

if os.environ.get("FG2_FIXTURE_RECOVERY_SOURCE") == "1":
    # Keep the worker's normal pinned-provenance validation active, but bind
    # this isolated fixture to its synthetic immutable source artifact. The
    # production pins remain untouched outside this test-only process.
    _source_path = Path("/run/post272-source-manifest.json")
    _source_raw = _source_path.read_bytes()
    _source = json.loads(_source_raw)
    _bounded.FG2_POST272_RECOVERY_SOURCE = {
        "run_id": str(_source["run_id"]),
        "run_attempt": int(_source["run_attempt"]),
        "source_sha": str(_source["source_sha"]),
        "workflow_id": 261386590,
        "artifact_id": "9000004001",
        "artifact_sha256": "b" * 64,
        "manifest_sha256": hashlib.sha256(_source_raw).hexdigest(),
        "approved_lot_reference": str(_source["approved_lot_reference"]),
        "approved_lot_sha256": str(_source["approved_lot_sha256"]),
    }
    _bounded.FG2_POST272_RECOVERY_INSTITUTION_ID = "20000000-0000-0000-0000-000000000001"
    _bounded.FG2_POST272_RECOVERY_COURSE_STAGING_IDS = {
        f"53000000-0000-0000-0000-{ordinal:012d}": f"52000000-0000-0000-0000-{ordinal:012d}"
        for ordinal in range(1, 7)
    }
    _bounded.FG2_POST272_RECOVERY_EXCLUDED_COURSE_ID = "53000000-0000-0000-0000-000000000006"
    _bounded.FG2_POST272_RECOVERY_EXCLUDED_URL = (
        "https://ssr.fg2.example/programas/post272-refresh-06"
    )


_SYNTHETIC_PROVIDER_RESULT = {
    "official_name": "Programa sintético verificado",
    "duration_text": "6 meses",
    "duration_months": 6,
    "total_cost_est": 1250,
    "requirements": ["Conocimientos iniciales"],
    "graduate_profile": "Perfil sintético",
    "target_audience": "Personas en formación",
    "objectives": "Aprender con evidencia sintética",
    "benefits": "Ejercicios prácticos",
    "certification": "Constancia sintética",
    "curriculum_summary": {"pilares": ["Contenido sintético"]},
    "modality": "Remoto",
    "primary_campus": "Virtual",
    "degree_type": "Curso",
    "start_date": None,
    "categories": ["Data"],
    "difficulty_level": "Básico",
    "ai_summary": "Resumen de curso sintético.",
}


def _install_synthetic_provider_boundary(orchestrator_class):
    """Substitute provider output while retaining the candidate orchestrator."""
    if getattr(orchestrator_class, "_fg2_synthetic_boundary_installed", False):
        return
    original_init = orchestrator_class.__init__

    def _fixture_init(orchestrator, providers, logger=None):
        original_init(orchestrator, providers, logger)
        providers = orchestrator.providers
        if len(providers) != 2 or [provider.name for provider in providers] != ["OpenAI", "Cloudflare"]:
            raise RuntimeError("fixture_provider_order_mismatch")
        primary = providers[0]
        primary.name = "fixture-provider"
        primary.health_fn = lambda: True
        primary.call_fn = lambda _prompt: json.dumps(
            _SYNTHETIC_PROVIDER_RESULT, ensure_ascii=False
        )

    orchestrator_class.__init__ = _fixture_init
    orchestrator_class._fg2_synthetic_boundary_installed = True


def _install_loopback_http_provider_boundary():
    """Route the actual Requests provider callers to a local synthetic HTTP server."""
    pillars = {
        "official_name": "Fixture OpenAI course",
        "duration_text": "6 meses",
        "duration_months": 6,
        "total_cost_est": 1250,
        "requirements": ["Synthetic requirement"],
        "graduate_profile": "Synthetic graduate profile",
        "target_audience": "Synthetic audience",
        "objectives": "Synthetic objectives",
        "benefits": "Synthetic benefits",
        "certification": "Synthetic certification",
        "curriculum_summary": {"pilares": ["Synthetic curriculum"]},
        "modality": "Remoto",
        "primary_campus": "Virtual",
        "degree_type": "Curso",
        "start_date": None,
        "categories": ["Data"],
        "difficulty_level": "Básico",
        "ai_summary": "Synthetic provider summary",
    }

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def do_POST(self):
            request_length = int(self.headers.get("Content-Length", "0"))
            try:
                request = json.loads(self.rfile.read(request_length))
                if self.path == "/openai":
                    fmt = request.get("text", {}).get("format", {})
                    valid = (
                        request.get("model") == "gpt-6-luna"
                        and request.get("store") is False
                        and fmt.get("type") == "json_schema"
                        and fmt.get("strict") is True
                        and len(fmt.get("schema", {}).get("properties", {})) == 18
                    )
                    response_pillars = pillars
                    prompt = request.get("input")
                    recovery_match = (
                        re.search(
                            r"^\[SYS\] Nombre: Post-272 recovered course ([0-9]{2})$",
                            prompt,
                            flags=re.MULTILINE,
                        )
                        if isinstance(prompt, str)
                        else None
                    )
                    if recovery_match:
                        response_pillars = dict(pillars)
                        response_pillars["official_name"] = (
                            f"Synthetic recovered course {recovery_match.group(1)}"
                        )
                    response = {
                        "status": "completed",
                        "output": [{
                            "type": "message",
                            "content": [{
                                "type": "output_text",
                                "text": json.dumps(response_pillars, ensure_ascii=False),
                            }],
                        }],
                    }
                    provider_name = "OpenAI"
                elif self.path == "/cloudflare":
                    valid = True
                    response = {
                        "result": {"response": json.dumps(pillars, ensure_ascii=False)}
                    }
                    provider_name = "Cloudflare"
                else:
                    valid = False
                    response = {"error": "fixture_route_rejected"}
                    provider_name = "unknown"
            except (UnicodeDecodeError, json.JSONDecodeError, AttributeError, TypeError):
                valid = False
                response = {"error": "fixture_request_rejected"}
                provider_name = "unknown"

            failure_mode = os.environ.get("FG2_FIXTURE_PROVIDER_MODE", "success")
            if failure_mode == "fail_all":
                status = 503
                response = {"error": {"type": "synthetic_provider_unavailable"}}
            else:
                status = 200 if valid else 400
            payload = json.dumps(response, ensure_ascii=False).encode("utf-8")
            _record_provider_response(provider_name, status, valid)
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, _format, *_args):
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    original_post = requests.post

    def route_provider_request(url, *args, **kwargs):
        parsed = urlsplit(str(url))
        if parsed.hostname == "api.openai.com" and parsed.path == "/v1/responses":
            return original_post(f"http://127.0.0.1:{server.server_port}/openai", *args, **kwargs)
        if parsed.hostname == "api.cloudflare.com" and parsed.path.startswith("/client/v4/accounts/"):
            return original_post(f"http://127.0.0.1:{server.server_port}/cloudflare", *args, **kwargs)
        return original_post(url, *args, **kwargs)

    requests.post = route_provider_request

    def close_server():
        server.shutdown()
        server.server_close()
        thread.join(timeout=1)

    atexit.register(close_server)


def _record_provider_response(provider: str, status: int, valid: bool) -> None:
    event = {
        "boundary": "provider_loopback",
        "run_id": os.environ.get("GITHUB_RUN_ID", "unknown"),
        "provider": provider,
        "status": int(status),
        "valid_schema_request": bool(valid),
    }
    line = (json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n").encode()
    descriptor = os.open(_event_path, os.O_CREAT | os.O_APPEND | os.O_WRONLY, 0o600)
    try:
        os.write(descriptor, line)
    finally:
        os.close(descriptor)


if os.environ.get("FG2_FIXTURE_PROVIDER_HTTP") == "1":
    if os.environ.get("FG2_FIXTURE_PROVIDER_ADAPTER") == "1":
        raise RuntimeError("fixture_provider_boundary_conflict")
    _install_loopback_http_provider_boundary()
elif os.environ.get("FG2_FIXTURE_PROVIDER_ADAPTER") == "1":
    _install_synthetic_provider_boundary(_script_utils.ProviderOrchestrator)
    _install_synthetic_provider_boundary(_legacy_utils.ProviderOrchestrator)

_original_budget_init = _bounded.FG2RequestBudget.__init__


def _fixture_budget_init(self, *args, **kwargs):
    if kwargs.get("request_preparer") is not None:
        kwargs["requester"] = _synthetic_budget_requester
        kwargs["monotonic"] = _clock.monotonic
        kwargs["sleeper"] = _clock.sleep
    _original_budget_init(self, *args, **kwargs)


_bounded.FG2RequestBudget.__init__ = _fixture_budget_init


def _fixture_headers(self, use_service_role=None):
    return {
        "apikey": os.environ["FG2_FIXTURE_SECRET_API_KEY"],
        "Authorization": f"Bearer {SERVICE_JWT}",
        "Content-Type": "application/json",
    }


_db_client.DatabaseClient._get_headers = _fixture_headers
_legacy_import_path_db_client.DatabaseClient._get_headers = _fixture_headers
if (
    _db_client.DatabaseClient._get_headers is not _fixture_headers
    or _legacy_import_path_db_client.DatabaseClient._get_headers is not _fixture_headers
):
    raise RuntimeError("fixture_db_adapter_not_installed")


class _FixtureCurlSession:
    def __init__(self, *args, **kwargs):
        self.options = kwargs.get("curl_options") or {}
        self.verify = kwargs.get("verify")
        self.closed = False

    def get(self, url, **kwargs):
        pinned = bool(self.options.get(CurlOpt.RESOLVE)) and self.verify is True
        response = _lookup_response(url, boundary="site_diagnostics", pinned=pinned)
        if not pinned:
            response.status_code = response.status = 598
        return response

    def close(self):
        self.closed = True


_diagnostics.CurlSession = _FixtureCurlSession


class _DiagnosticClock:
    def monotonic(self):
        return _clock.monotonic()

    def time(self):
        return _real_time.time()

    def sleep(self, seconds):
        _clock.advance(seconds)


_diagnostics.time = _DiagnosticClock()
