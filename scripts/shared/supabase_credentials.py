"""Supabase API-key loading and HTTP header contracts.

Modern publishable and secret keys identify the calling application and must be
sent through ``apikey``. ``Authorization`` is reserved for a separate user or
worker access token.
"""

from __future__ import annotations

import os
from collections.abc import Mapping


PUBLISHABLE_KEY_PREFIX = "sb_publishable_"
SECRET_KEY_PREFIX = "sb_secret_"


class SupabaseCredentialError(RuntimeError):
    """Raised when Supabase credentials are absent or use an unsafe shape."""


def validate_api_key(value: str, *, kind: str, variable_name: str) -> str:
    """Return a stripped modern API key or fail without exposing its value."""
    prefixes = {
        "publishable": PUBLISHABLE_KEY_PREFIX,
        "secret": SECRET_KEY_PREFIX,
    }
    try:
        expected_prefix = prefixes[kind]
    except KeyError as exc:
        raise ValueError(f"Unsupported Supabase API key kind: {kind}") from exc

    key = value.strip() if isinstance(value, str) else ""
    if not key:
        raise SupabaseCredentialError(f"Missing required environment variable: {variable_name}")
    if not key.startswith(expected_prefix) or len(key) == len(expected_prefix):
        raise SupabaseCredentialError(
            f"{variable_name} must use the {expected_prefix} prefix"
        )
    return key


def get_publishable_key(
    environ: Mapping[str, str] | None = None,
    *,
    required: bool = True,
) -> str | None:
    """Load and validate the first configured modern publishable key."""
    env = os.environ if environ is None else environ
    names = (
        "NEXT_SUPABASE_PUBLISHABLE_KEY",
        "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY",
    )
    for name in names:
        value = env.get(name, "")
        if value:
            return validate_api_key(value, kind="publishable", variable_name=name)
    if required:
        raise SupabaseCredentialError(
            "Missing required environment variable: NEXT_SUPABASE_PUBLISHABLE_KEY "
            "or NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY"
        )
    return None


def get_secret_key(
    environ: Mapping[str, str] | None = None,
    *,
    required: bool = True,
) -> str | None:
    """Load the canonical backend secret key without legacy fallbacks."""
    env = os.environ if environ is None else environ
    value = env.get("NEXT_SUPABASE_SECRET_KEY", "")
    if value:
        return validate_api_key(
            value,
            kind="secret",
            variable_name="NEXT_SUPABASE_SECRET_KEY",
        )
    if required:
        raise SupabaseCredentialError(
            "Missing required environment variable: NEXT_SUPABASE_SECRET_KEY"
        )
    return None


def get_access_token(
    environ: Mapping[str, str] | None = None,
    *,
    required: bool = False,
) -> str | None:
    """Load a separate authorization token and reject API keys in its place."""
    env = os.environ if environ is None else environ
    access_token = env.get("NEXT_SUPABASE_ACCESS_TOKEN", "").strip()
    if not access_token:
        if required:
            raise SupabaseCredentialError(
                "Missing required environment variable: NEXT_SUPABASE_ACCESS_TOKEN"
            )
        return None
    if access_token.startswith((PUBLISHABLE_KEY_PREFIX, SECRET_KEY_PREFIX)):
        raise SupabaseCredentialError(
            "NEXT_SUPABASE_ACCESS_TOKEN must be an access token, not an API key"
        )
    return access_token


def build_supabase_headers(
    api_key: str,
    *,
    kind: str,
    access_token: str | None = None,
    content_type: bool = True,
) -> dict[str, str]:
    """Build headers with API keys only in ``apikey``."""
    key = validate_api_key(api_key, kind=kind, variable_name=f"Supabase {kind} key")
    headers = {"apikey": key}
    if access_token:
        access_token = access_token.strip()
        if access_token.startswith((PUBLISHABLE_KEY_PREFIX, SECRET_KEY_PREFIX)):
            raise SupabaseCredentialError(
                "Authorization requires a separate access token"
            )
        headers["Authorization"] = f"Bearer {access_token}"
    if content_type:
        headers["Content-Type"] = "application/json"
    return headers
