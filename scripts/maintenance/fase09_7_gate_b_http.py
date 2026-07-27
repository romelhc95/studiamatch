"""Free-only, GET-only runtime attestation for F9.7 Gate B."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import re
from urllib.parse import urlsplit

import requests


ORIGIN_ENV = "NEXT_PUBLIC_SUPABASE_URL"
PUBLISHABLE_ENV = "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY"
SERVICE_ENV = "NEXT_SUPABASE_SECRET_KEY"
EXPECTED_FINGERPRINT_ENV = "F9_7_EXPECTED_FREE_TARGET_FINGERPRINT"
PATHS = (
    ("courses", "/rest/v1/courses?select=id&limit=0"),
    ("leads", "/rest/v1/leads?select=id&limit=0"),
    ("email_log", "/rest/v1/email_log?select=id&limit=0"),
)
FORBIDDEN_ENV = (
    "PRO_SUPABASE_URL",
    "PRO_NEXT_SUPABASE_PUBLISHABLE_KEY",
    "PRO_NEXT_SUPABASE_SECRET_KEY",
)
AMBIGUOUS_ENV = (
    "SUPABASE_URL",
)


class GateBError(RuntimeError):
    pass


def _required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise GateBError(f"missing required private binding: {name}")
    return value


def _load_private_binding() -> tuple[str, str, str]:
    if any(os.environ.get(name, "").strip() for name in FORBIDDEN_ENV) or any(
        name.startswith("PRO_") and "SUPABASE" in name and value.strip()
        for name, value in os.environ.items()
    ):
        raise GateBError("Pro binding is forbidden in F9.7 Gate B")
    if any(os.environ.get(name, "").strip() for name in AMBIGUOUS_ENV):
        raise GateBError("ambiguous generic Supabase binding is forbidden")

    origin = _required_env(ORIGIN_ENV).rstrip("/")
    publishable = _required_env(PUBLISHABLE_ENV)
    service = _required_env(SERVICE_ENV)
    parsed = urlsplit(origin)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or not re.fullmatch(r"[a-z0-9]{20}\.supabase\.co", parsed.hostname)
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port is not None
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
    ):
        raise GateBError("invalid private Free origin binding")
    if not publishable.startswith("sb_publishable_"):
        raise GateBError("invalid private Free publishable identity")
    if not service.startswith("sb_secret_"):
        raise GateBError("invalid private Free service identity")
    if hmac.compare_digest(publishable, service):
        raise GateBError("Free identities must be distinct")
    return origin.lower(), publishable, service


def derive_target_fingerprint(origin: str, publishable: str, service: str) -> str:
    publishable_digest = hashlib.sha256(publishable.encode("utf-8")).hexdigest()
    service_digest = hashlib.sha256(service.encode("utf-8")).hexdigest()
    material = (
        "studiamatch-gate-b-target-v1\0free\0"
        f"{origin}\0{publishable_digest}\0{service_digest}"
    ).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def _headers(key: str) -> dict[str, str]:
    return {
        "apikey": key,
        "Accept": "application/json",
        "Prefer": "count=exact",
    }


def execute_attestation(request_get=None) -> dict:
    origin, publishable, service = _load_private_binding()
    fingerprint = derive_target_fingerprint(origin, publishable, service)
    expected = _required_env(EXPECTED_FINGERPRINT_ENV)
    if not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise GateBError("invalid expected Free target fingerprint")
    if not hmac.compare_digest(fingerprint, expected):
        raise GateBError("Free target fingerprint mismatch")

    session = None
    if request_get is None:
        session = requests.Session()
        session.trust_env = False
        request_get = session.get

    checks = []
    try:
        for identity, key in (
            ("publishable", publishable),
            ("service", service),
        ):
            for path_id, path in PATHS:
                response = None
                expected_success = identity == "service" or path_id == "courses"
                accepted_statuses = {200, 206} if expected_success else {401, 403}
                range_required = expected_success
                try:
                    response = request_get(
                        f"{origin}{path}",
                        headers=_headers(key),
                        timeout=15,
                        allow_redirects=False,
                        stream=True,
                    )
                    content_range_present = bool(response.headers.get("Content-Range"))
                    passed = (
                        response.status_code in accepted_statuses
                        and content_range_present is range_required
                    )
                    checks.append({
                        "identity_class": identity,
                        "path_id": path_id,
                        "status_class": (
                            "success" if response.status_code in {200, 206}
                            else "denied" if response.status_code in {401, 403}
                            else "unexpected"
                        ),
                        "content_range_present": content_range_present,
                        "pass": passed,
                    })
                except requests.RequestException as exc:
                    raise GateBError("sanitized Free transport failure") from exc
                finally:
                    if response is not None:
                        response.close()
    finally:
        if session is not None:
            session.close()

    return {
        "query_id": "F9.7-GATE-B-HTTP-V1",
        "target_scope": "free",
        "target_fingerprint_sha256": fingerprint,
        "checks": checks,
        "gate_b_http_pass": len(checks) == 6 and all(item["pass"] for item in checks),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--fingerprint-only", action="store_true")
    mode.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    try:
        origin, publishable, service = _load_private_binding()
        if args.fingerprint_only:
            print(derive_target_fingerprint(origin, publishable, service))
            return 0
        result = execute_attestation()
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0 if result["gate_b_http_pass"] else 1
    except GateBError as exc:
        print(json.dumps({
            "query_id": "F9.7-GATE-B-HTTP-V1",
            "target_scope": "free",
            "gate_b_http_pass": False,
            "error": str(exc),
        }, sort_keys=True, separators=(",", ":")))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
