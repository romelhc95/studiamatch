import os
import requests
import json
import time
from dotenv import load_dotenv
import re
import urllib.parse

from .supabase_credentials import (
    PUBLISHABLE_KEY_PREFIX,
    SECRET_KEY_PREFIX,
    SupabaseCredentialError,
    build_supabase_headers,
    get_publishable_key,
    get_secret_key,
    validate_api_key,
)

DNS_RETRY_DELAYS = [5, 10, 20]
DNS_RETRY_MAX = 3
DB_REQUEST_TIMEOUT = (5, 20)
IDEMPOTENT_HTTP_METHODS = frozenset({"GET", "HEAD"})


class DatabaseAPIError(RuntimeError):
    """Raised when the Data API returns an unexpected response."""


class DatabaseTransportError(DatabaseAPIError):
    """Raised with a sanitized reason when request outcome cannot be proven."""


def _transport_reason(error):
    if isinstance(error, requests.exceptions.Timeout):
        return "DB_TRANSPORT_TIMEOUT"
    dns_error = getattr(requests.exceptions, "DNSResolutionError", ())
    if dns_error and isinstance(error, dns_error):
        return "DB_TRANSPORT_DNS"
    return "DB_TRANSPORT_CONNECTION"


def _request_with_retry(request_fn, url, *, http_method, **kwargs):
    """
    Retry transient transport failures only for explicitly idempotent methods.

    Mutations run exactly once because a timeout or disconnect can occur after the
    server applied the write, making its outcome ambiguous.
    """
    method_name = str(http_method or "").upper()
    if not method_name:
        raise ValueError("http_method is required")
    max_attempts = DNS_RETRY_MAX if method_name in IDEMPOTENT_HTTP_METHODS else 1
    kwargs.setdefault("timeout", DB_REQUEST_TIMEOUT)
    kwargs["allow_redirects"] = False
    for attempt in range(1, max_attempts + 1):
        try:
            return request_fn(url, **kwargs)
        except requests.exceptions.RequestException as e:
            reason = _transport_reason(e)
            transient = isinstance(
                e,
                (
                    requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout,
                    requests.exceptions.ChunkedEncodingError,
                    requests.exceptions.ContentDecodingError,
                ),
            )
            if transient and attempt < max_attempts:
                delay = DNS_RETRY_DELAYS[attempt - 1]
                print(
                    f"DB_CLIENT_RETRY reason={reason} "
                    f"attempt={attempt}/{max_attempts} delay_seconds={delay}"
                )
                time.sleep(delay)
            else:
                outcome = (
                    "DB_MUTATION_OUTCOME_UNKNOWN"
                    if method_name not in IDEMPOTENT_HTTP_METHODS
                    else (
                        "DB_READ_RETRY_EXHAUSTED"
                        if transient
                        else "DB_READ_TRANSPORT_FAILURE"
                    )
                )
                print(f"DB_CLIENT_REQUEST_FAILED reason={outcome}")
                raise DatabaseTransportError(outcome) from None

# Try to load env files from the root of the project (3 levels up from this script: scripts/shared/db_client.py)
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_local = os.path.join(root_dir, '.env.local')
env_std = os.path.join(root_dir, '.env')

if os.path.exists(env_local):
    print(f"DB_CLIENT: Loading env from {env_local}")
    load_dotenv(env_local)
elif os.path.exists(env_std):
    print(f"DB_CLIENT: Loading env from {env_std}")
    load_dotenv(env_std)
else:
    print("DB_CLIENT: Falling back to standard dotenv search")
    load_dotenv() # Fallback to standard search

class DatabaseClient:
    """
    Universal Database Client for StudIAMatch.
    Uses Publishable key for frontend reads (respects RLS, public API)
    and Secret key (service_role) for pipeline writes+reads (bypasses RLS).
    
    Key hierarchy:
    - Publishable key (sb_publishable_...): Frontend-facing reads, respects RLS.
      Used by `select()` for public tables (courses with is_active=true).
    - Secret key (sb_secret_...): Server-side pipeline operations, bypasses RLS.
      Used by all writes and by `select_pipeline()` for pipeline table reads.
    
    Legacy anon keys are not used; Supabase recommends Publishable keys as
    the modern replacement.
    """
    PIPELINE_TABLES = frozenset([
        'staging_raw', 'cleansed_programs', 'enriched_programs',
        'institution_site_profiles',
    ])

    def __init__(self, supabase_url=None, supabase_key=None):
        self.supabase_url = supabase_url if supabase_url is not None else (os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL"))
        if supabase_key is None:
            self._publishable_key = get_publishable_key(required=False)
            self._service_key = get_secret_key(required=False)
        else:
            # An explicitly injected identity must not inherit a key from a
            # different environment through the process-level configuration.
            self._publishable_key = None
            self._service_key = None
            if not isinstance(supabase_key, str):
                raise SupabaseCredentialError(
                    "supabase_key must be a modern Supabase API key string"
                )
            if supabase_key.startswith(PUBLISHABLE_KEY_PREFIX):
                self._publishable_key = validate_api_key(
                    supabase_key,
                    kind="publishable",
                    variable_name="supabase_key",
                )
            elif supabase_key.startswith(SECRET_KEY_PREFIX):
                self._service_key = validate_api_key(
                    supabase_key,
                    kind="secret",
                    variable_name="supabase_key",
                )
            else:
                raise SupabaseCredentialError(
                    "supabase_key must use a modern Supabase API key prefix"
                )
        self.supabase_key = self._service_key or self._publishable_key

    def _get_headers(self, use_service_role=None):
        if use_service_role is True:
            if not self._service_key:
                raise SupabaseCredentialError(
                    "Service operations require a configured Supabase secret key"
                )
            return build_supabase_headers(self._service_key, kind="secret")
        if use_service_role is False:
            if not self._publishable_key:
                raise SupabaseCredentialError(
                    "Public operations require a configured Supabase publishable key"
                )
            return build_supabase_headers(self._publishable_key, kind="publishable")
        if self._service_key:
            return build_supabase_headers(self._service_key, kind="secret")
        if self._publishable_key:
            return build_supabase_headers(self._publishable_key, kind="publishable")
        raise SupabaseCredentialError("No modern Supabase API key is configured")

    def _select_api(
        self,
        table,
        filters,
        columns,
        limit,
        order,
        use_service_role=False,
        raise_on_error=False,
    ):
        if columns == "count":
            url = f"{self.supabase_url}/rest/v1/{table}?select=count"
        else:
            url = f"{self.supabase_url}/rest/v1/{table}?select={columns}"
            
        if filters:
            url += f"&{filters}"
        if order:
            url += f"&order={order}"
        if limit:
            url += f"&limit={limit}"
            
        res = _request_with_retry(requests.get, url, http_method="GET", headers=self._get_headers(use_service_role=use_service_role))
        if res.status_code == 200:
            data = res.json()
            if columns == "count":
                return data
            return data
        if raise_on_error:
            raise RuntimeError(
                f"DB select failed for {table}: HTTP {res.status_code}"
            )
        return []

    def _insert_api(self, table, data):
        url = f"{self.supabase_url}/rest/v1/{table}"
        res = _request_with_retry(requests.post, url, http_method="POST", headers=self._get_headers(use_service_role=True), json=data)
        if res.status_code in [200, 201, 204]:
            return res.json() if res.content else {"status": "success"}
        print(f"DB_CLIENT_API_ERROR reason=insert_http_status status={res.status_code}")
        return None

    def _patch_api(self, table, filters, data, raise_on_error=False, return_representation=False):
        url = f"{self.supabase_url}/rest/v1/{table}?{filters}"
        headers = self._get_headers(True)
        if return_representation:
            headers["Prefer"] = "return=representation"
        res = _request_with_retry(requests.patch, url, http_method="PATCH", headers=headers, json=data)
        if return_representation:
            if res.status_code not in (200, 201):
                raise DatabaseAPIError(
                    f"DB patch representation failed for {table}: HTTP {res.status_code}"
                )
            try:
                payload = res.json()
            except ValueError:
                raise DatabaseAPIError(
                    f"DB patch representation invalid JSON for {table}"
                ) from None
            if not isinstance(payload, list):
                raise DatabaseAPIError(
                    f"DB patch representation invalid payload for {table}"
                )
            return payload
        if res.status_code in [200, 204]:
            return {"status": "success"}
        if raise_on_error:
            raise RuntimeError(
                f"DB patch failed for {table}: HTTP {res.status_code}"
            )
        print(f"DB_CLIENT_API_ERROR reason=patch_http_status status={res.status_code}")
        return {"status": "error"}

    def _delete_api(self, table, filters):
        url = f"{self.supabase_url}/rest/v1/{table}?{filters}"
        res = _request_with_retry(requests.delete, url, http_method="DELETE", headers=self._get_headers(use_service_role=True))
        if res.status_code in [200, 201, 204]:
            return res.json() if res.content else {"status": "success"}
        print(f"DB_CLIENT_API_ERROR reason=delete_http_status status={res.status_code}")
        return None

    def _upsert_api(self, table, data, on_conflict):
        url = f"{self.supabase_url}/rest/v1/{table}"
        if on_conflict:
            url += f"?on_conflict={on_conflict}"
        headers = self._get_headers(use_service_role=True)
        headers["Prefer"] = "resolution=merge-duplicates,return=representation"
        is_batch = isinstance(data, list)
        res = _request_with_retry(requests.post, url, http_method="POST", headers=headers, json=data)
        if res.status_code in [200, 201, 204]:
            return res.json() if res.content else {"status": "success"}
        print(f"DB_CLIENT_API_ERROR reason=upsert_http_status status={res.status_code}")
        return None

    # --- Public API methods (Cloud-Only) ---

    def select(self, table, filters=None, columns="*", limit=None, order=None):
        """Select records with Publishable key (respects RLS). For public tables only."""
        return self._select_api(table, filters, columns, limit, order, use_service_role=False)

    def select_service(self, table, filters=None, columns="*", limit=None, order=None):
        """Select with the configured secret key for explicit backend tooling."""
        return self._select_api(table, filters, columns, limit, order, use_service_role=True)

    def select_service_raise(
        self, table, filters=None, columns="*", limit=None, order=None
    ):
        """Select privileged data and raise when the Data API request fails."""
        return self._select_api(
            table,
            filters,
            columns,
            limit,
            order,
            use_service_role=True,
            raise_on_error=True,
        )

    def select_raise(self, table, filters=None, columns="*", limit=None, order=None):
        """Select public data and raise when the Data API request fails."""
        return self._select_api(
            table,
            filters,
            columns,
            limit,
            order,
            use_service_role=False,
            raise_on_error=True,
        )

    def select_pipeline(self, table, filters=None, columns="*", limit=None, order=None):
        """
        Select records with Secret key (bypasses RLS). For pipeline tables only.
        Required because pipeline tables (staging_raw, cleansed_programs, enriched_programs,
        institution_site_profiles) have RLS policies that block public access.
        Generic: works for any institution, not DMC-specific.
        
        Raises ValueError if called on a non-pipeline table (defense-in-depth).
        """
        if table not in self.PIPELINE_TABLES:
            raise ValueError(
                f"select_pipeline() called on non-pipeline table '{table}'. "
                f"Allowed: {sorted(self.PIPELINE_TABLES)}"
            )
        return self._select_api(table, filters, columns, limit, order, use_service_role=True)

    def select_pipeline_raise(
        self, table, filters=None, columns="*", limit=None, order=None
    ):
        """Select pipeline data and raise instead of returning a false empty queue."""
        if table not in self.PIPELINE_TABLES:
            raise ValueError(
                f"select_pipeline_raise() called on non-pipeline table '{table}'. "
                f"Allowed: {sorted(self.PIPELINE_TABLES)}"
            )
        return self._select_api(
            table,
            filters,
            columns,
            limit,
            order,
            use_service_role=True,
            raise_on_error=True,
        )

    def count_pipeline(self, table, filters=None):
        """
        Returns exact count of rows for pipeline tables using Secret key (bypasses RLS).
        Analogous to select_pipeline() but returns count.
        """
        if table not in self.PIPELINE_TABLES:
            raise ValueError(
                f"count_pipeline() called on non-pipeline table '{table}'. "
                f"Allowed: {sorted(self.PIPELINE_TABLES)}"
            )
        url = f"{self.supabase_url}/rest/v1/{table}?select=id&limit=0"
        if filters:
            url += f"&{filters}"
        headers = self._get_headers(use_service_role=True)
        headers["Prefer"] = "count=exact"
        res = _request_with_retry(requests.get, url, http_method="GET", headers=headers)
        if res.status_code in (200, 206):
            content_range = res.headers.get("Content-Range", "")
            if content_range:
                parts = content_range.split("/")
                if len(parts) == 2:
                    try:
                        return int(parts[1])
                    except ValueError:
                        pass
        return 0

    def count_pipeline_raise(self, table, filters=None):
        """Return a pipeline count and raise when the Data API cannot prove it."""
        if table not in self.PIPELINE_TABLES:
            raise ValueError(
                f"count_pipeline_raise() called on non-pipeline table '{table}'. "
                f"Allowed: {sorted(self.PIPELINE_TABLES)}"
            )
        url = f"{self.supabase_url}/rest/v1/{table}?select=id&limit=0"
        if filters:
            url += f"&{filters}"
        headers = self._get_headers(use_service_role=True)
        headers["Prefer"] = "count=exact"
        res = _request_with_retry(requests.get, url, http_method="GET", headers=headers)
        if res.status_code not in (200, 206):
            raise RuntimeError(
                f"DB count failed for {table}: HTTP {res.status_code}"
            )
        content_range = res.headers.get("Content-Range", "")
        if "/" not in content_range:
            raise RuntimeError(f"DB count missing Content-Range for {table}")
        try:
            return int(content_range.split("/", 1)[1])
        except ValueError:
            raise RuntimeError(f"DB count invalid for {table}") from None

    def insert(self, table, data):
        """Insert a record via Supabase REST API."""
        if isinstance(data, list):
            return self._upsert_api(table, data, on_conflict=None)
        return self._insert_api(table, data)

    def patch(self, table, filters, data):
        """Update records via Supabase REST API."""
        return self._patch_api(table, filters, data)

    def patch_raise(self, table, filters, data):
        """Update privileged data and raise when persistence is not proven."""
        return self._patch_api(table, filters, data, raise_on_error=True)

    def patch_exact_one_raise(self, table, filters, data, expected_id):
        """Patch and prove exactly one returned row matches the intended id."""
        rows = self._patch_api(
            table,
            filters,
            data,
            raise_on_error=True,
            return_representation=True,
        )
        if len(rows) != 1:
            raise DatabaseAPIError(
                f"DB patch expected exactly one row for {table}, got {len(rows)}"
            )
        returned_id = rows[0].get("id") if isinstance(rows[0], dict) else None
        if returned_id != expected_id:
            raise DatabaseAPIError(
                f"DB patch returned unexpected id for {table}"
            )
        return rows[0]

    def upsert(self, table, data, on_conflict=None):
        """Upsert records via Supabase REST API."""
        return self._upsert_api(table, data, on_conflict)

    def select_all(self, table, filters=None, columns="*", batch_size=1000, order=None):
        """
        Paginated select with Publishable key (respects RLS). For public tables only.
        Supabase API limits results to 1000 by default, so this handles pagination transparently.
        """
        all_results = []
        offset = 0
        while True:
            limit = min(batch_size, 1000)
            url = f"{self.supabase_url}/rest/v1/{table}?select={columns}"
            if filters:
                url += f"&{filters}"
            if order:
                url += f"&order={order}"
            url += f"&limit={limit}&offset={offset}"
            headers = self._get_headers(use_service_role=False)
            headers["Range"] = f"{offset}-{offset + limit - 1}"
            headers["Prefer"] = "count=exact"
            res = _request_with_retry(requests.get, url, http_method="GET", headers=headers)
            if res.status_code == 200:
                batch = res.json()
                if not batch:
                    break
                all_results.extend(batch)
                offset += len(batch)
                if len(batch) < limit:
                    break
            else:
                print(f"DB_CLIENT_API_ERROR reason=select_all_http_status status={res.status_code}")
                break
        return all_results

    def select_all_service(self, table, filters=None, columns="*", batch_size=1000, order=None):
        """Paginated select with the configured secret key for backend tooling."""
        all_results = []
        offset = 0
        while True:
            limit = min(batch_size, 1000)
            url = f"{self.supabase_url}/rest/v1/{table}?select={columns}"
            if filters:
                url += f"&{filters}"
            if order:
                url += f"&order={order}"
            url += f"&limit={limit}&offset={offset}"
            headers = self._get_headers(use_service_role=True)
            headers["Range"] = f"{offset}-{offset + limit - 1}"
            headers["Prefer"] = "count=exact"
            res = _request_with_retry(requests.get, url, http_method="GET", headers=headers)
            if res.status_code not in (200, 206):
                raise DatabaseAPIError(
                    f"SelectAllService failed for {table}: "
                    f"unexpected HTTP status {res.status_code}"
                )
            batch = res.json()
            if not batch:
                break
            all_results.extend(batch)
            offset += len(batch)
            if len(batch) < limit:
                break
        return all_results

    def select_all_pipeline(self, table, filters=None, columns="*", batch_size=1000, order=None):
        """
        Paginated select with Secret key (bypasses RLS). For pipeline tables only.
        Required because pipeline tables have RLS policies blocking public access.
        """
        if table not in self.PIPELINE_TABLES:
            raise ValueError(
                f"select_all_pipeline() called on non-pipeline table '{table}'. "
                f"Allowed: {sorted(self.PIPELINE_TABLES)}"
            )
        all_results = []
        offset = 0
        while True:
            limit = min(batch_size, 1000)
            url = f"{self.supabase_url}/rest/v1/{table}?select={columns}"
            if filters:
                url += f"&{filters}"
            if order:
                url += f"&order={order}"
            url += f"&limit={limit}&offset={offset}"
            headers = self._get_headers(use_service_role=True)
            headers["Range"] = f"{offset}-{offset + limit - 1}"
            headers["Prefer"] = "count=exact"
            res = _request_with_retry(requests.get, url, http_method="GET", headers=headers)
            if res.status_code not in (200, 206):
                raise DatabaseAPIError(
                    f"SelectAllPipeline failed for {table}: "
                    f"unexpected HTTP status {res.status_code}"
                )
            batch = res.json()
            if not batch:
                break
            all_results.extend(batch)
            offset += len(batch)
            if len(batch) < limit:
                break
        return all_results

    def count(self, table, filters=None):
        """
        Returns the exact count of rows matching the filters using PostgREST's Prefer: count=exact header.
        Sends a minimal query (limit=0) for optimal performance.
        """
        url = f"{self.supabase_url}/rest/v1/{table}?select=id&limit=0"
        if filters:
            url += f"&{filters}"
        headers = self._get_headers(use_service_role=False)
        headers["Prefer"] = "count=exact"
        res = _request_with_retry(requests.get, url, http_method="GET", headers=headers)
        if res.status_code in (200, 206):
            content_range = res.headers.get("Content-Range", "")
            if content_range:
                parts = content_range.split("/")
                if len(parts) == 2:
                    try:
                        return int(parts[1])
                    except ValueError:
                        pass
        return 0

    def count_service(self, table, filters=None):
        """Return an exact count using the configured secret key."""
        url = f"{self.supabase_url}/rest/v1/{table}?select=id&limit=0"
        if filters:
            url += f"&{filters}"
        headers = self._get_headers(use_service_role=True)
        headers["Prefer"] = "count=exact"
        res = _request_with_retry(requests.get, url, http_method="GET", headers=headers)
        if res.status_code in (200, 206):
            content_range = res.headers.get("Content-Range", "")
            if "/" in content_range:
                try:
                    return int(content_range.split("/", 1)[1])
                except ValueError:
                    pass
        return 0

    def count_service_raise(self, table, filters=None):
        """Return an exact service count or raise when it cannot be proven."""
        url = f"{self.supabase_url}/rest/v1/{table}?select=id&limit=0"
        if filters:
            url += f"&{filters}"
        headers = self._get_headers(use_service_role=True)
        headers["Prefer"] = "count=exact"
        res = _request_with_retry(requests.get, url, http_method="GET", headers=headers)
        if res.status_code not in (200, 206):
            raise DatabaseAPIError(
                f"DB service count failed for {table}: HTTP {res.status_code}"
            )
        content_range = res.headers.get("Content-Range", "")
        parts = content_range.split("/")
        if len(parts) != 2 or not parts[1]:
            raise DatabaseAPIError(
                f"DB service count missing Content-Range for {table}"
            )
        try:
            count = int(parts[1])
        except ValueError:
            raise DatabaseAPIError(
                f"DB service count invalid for {table}"
            ) from None
        if count < 0:
            raise DatabaseAPIError(f"DB service count invalid for {table}")
        return count

    def delete(self, table, filters):
        """Delete records via Supabase REST API."""
        return self._delete_api(table, filters)

    def rpc(self, function_name, params=None):
        """
        Calls a Supabase RPC function.
        Uses service_role key (pipeline RPCs require bypass of RLS).
        Returns None on error (legacy behavior, safe for callers that check `if result:`).
        For error details, check stdout logs (DB_CLIENT_API_ERROR).
        """
        url = f"{self.supabase_url}/rest/v1/rpc/{function_name}"
        headers = self._get_headers(use_service_role=True)
        headers["Prefer"] = "return=representation"
        res = _request_with_retry(requests.post, url, http_method="POST", headers=headers, json=params or {})
        if res.status_code in [200, 201, 204]:
            return res.json() if res.content else {"status": "success"}
        print(f"DB_CLIENT_API_ERROR reason=rpc_http_status status={res.status_code}")
        return None

    def rpc_raise(self, function_name, params=None):
        """
        Like rpc() but raises RuntimeError with the API response text on error.
        Use this when the caller needs to detect specific errors like PGRST202.
        """
        url = f"{self.supabase_url}/rest/v1/rpc/{function_name}"
        headers = self._get_headers(use_service_role=True)
        headers["Prefer"] = "return=representation"
        res = _request_with_retry(requests.post, url, http_method="POST", headers=headers, json=params or {})
        if res.status_code in [200, 201, 204]:
            return res.json() if res.content else {"status": "success"}
        err_msg = f"DB_CLIENT_API_ERROR reason=rpc_http_status status={res.status_code}"
        print(err_msg)
        raise RuntimeError(err_msg)

def get_db_client():
    return DatabaseClient()
