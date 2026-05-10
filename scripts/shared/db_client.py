import os
import requests
import json
import time
from dotenv import load_dotenv
import re
import urllib.parse

DNS_RETRY_DELAYS = [5, 10, 20]
DNS_RETRY_MAX = 3

def _request_with_retry(method, url, **kwargs):
    """
    Executes an HTTP request with exponential backoff retry for DNS/connection errors.
    Non-transient errors (4xx, 5xx) are NOT retried — only network-level failures.
    """
    last_err = None
    for attempt in range(1, DNS_RETRY_MAX + 1):
        try:
            return method(url, **kwargs)
        except (requests.exceptions.ConnectionError,
                getattr(requests.exceptions, 'DNSResolutionError', requests.exceptions.ConnectionError),
                requests.exceptions.Timeout) as e:
            last_err = e
            if attempt < DNS_RETRY_MAX:
                delay = DNS_RETRY_DELAYS[attempt - 1]
                print(f"DB_CLIENT_RETRY: Attempt {attempt}/{DNS_RETRY_MAX} failed ({type(e).__name__}). Retrying in {delay}s...")
                time.sleep(delay)
            else:
                print(f"DB_CLIENT_RETRY: All {DNS_RETRY_MAX} attempts failed for {url}. Last error: {e}")
    raise last_err

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
    
    Legacy anon key (NEXT_PUBLIC_SUPABASE_ANON_KEY) is NOT used — Supabase
    recommends Publishable keys as the modern replacement.
    """
    PIPELINE_TABLES = frozenset([
        'staging_raw', 'cleansed_programs', 'enriched_programs',
        'institution_site_profiles',
    ])

    def __init__(self, supabase_url=None, supabase_key=None):
        self.supabase_url = supabase_url if supabase_url is not None else (os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL"))
        self._publishable_key = os.getenv("NEXT_SUPABASE_PUBLISHABLE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
        self._service_key = os.getenv("NEXT_SUPABASE_SECRET_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
        self.supabase_key = supabase_key if supabase_key is not None else (self._service_key or self._publishable_key)

    def _get_headers(self, use_service_role=None):
        if use_service_role is None:
            key = self.supabase_key
        elif use_service_role and self._service_key:
            key = self._service_key
        elif not use_service_role and self._publishable_key:
            key = self._publishable_key
        else:
            key = self.supabase_key
        return {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }

    def _select_api(self, table, filters, columns, limit, order, use_service_role=False):
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
            
        res = _request_with_retry(requests.get, url, headers=self._get_headers(use_service_role=use_service_role))
        if res.status_code == 200:
            data = res.json()
            if columns == "count":
                return data
            return data
        return []

    def _insert_api(self, table, data):
        url = f"{self.supabase_url}/rest/v1/{table}"
        res = _request_with_retry(requests.post, url, headers=self._get_headers(use_service_role=True), json=data)
        if res.status_code in [200, 201, 204]:
            return res.json() if res.content else {"status": "success"}
        print(f"DB_CLIENT_API_ERROR (Insert): {res.status_code} - {(res.text or '')[:200]}")
        return None

    def _patch_api(self, table, filters, data):
        url = f"{self.supabase_url}/rest/v1/{table}?{filters}"
        res = _request_with_retry(requests.patch, url, headers=self._get_headers(use_service_role=True), json=data)
        if res.status_code in [200, 204]:
            return {"status": "success"}
        print(f"DB_CLIENT_API_ERROR (Patch): {res.status_code} - {(res.text or '')[:200]}")
        return {"status": "error"}

    def _delete_api(self, table, filters):
        url = f"{self.supabase_url}/rest/v1/{table}?{filters}"
        res = _request_with_retry(requests.delete, url, headers=self._get_headers(use_service_role=True))
        if res.status_code in [200, 201, 204]:
            return res.json() if res.content else {"status": "success"}
        print(f"DB_CLIENT_API_ERROR (Delete {table}): {res.status_code} - {(res.text or '')[:200]}")
        return None

    def _upsert_api(self, table, data, on_conflict):
        url = f"{self.supabase_url}/rest/v1/{table}?on_conflict={on_conflict}"
        headers = self._get_headers(use_service_role=True)
        headers["Prefer"] = "resolution=merge-duplicates,return=representation"
        is_batch = isinstance(data, list)
        res = _request_with_retry(requests.post, url, headers=headers, json=data)
        if res.status_code in [200, 201, 204]:
            return res.json() if res.content else {"status": "success"}
        print(f"DB_CLIENT_API_ERROR (Upsert {table}): {res.status_code} - {(res.text or '')[:200]}")
        return None

    # --- Public API methods (Cloud-Only) ---

    def select(self, table, filters=None, columns="*", limit=None, order=None):
        """Select records with Publishable key (respects RLS). For public tables only."""
        return self._select_api(table, filters, columns, limit, order, use_service_role=False)

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
        res = _request_with_retry(requests.get, url, headers=headers)
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

    def insert(self, table, data):
        """Insert a record via Supabase REST API."""
        if isinstance(data, list):
            return self._upsert_api(table, data, on_conflict=None)
        return self._insert_api(table, data)

    def patch(self, table, filters, data):
        """Update records via Supabase REST API."""
        return self._patch_api(table, filters, data)

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
            res = _request_with_retry(requests.get, url, headers=headers)
            if res.status_code == 200:
                batch = res.json()
                if not batch:
                    break
                all_results.extend(batch)
                offset += len(batch)
                if len(batch) < limit:
                    break
            else:
                print(f"DB_CLIENT_API_ERROR (SelectAll {table}): {res.status_code} - {(res.text or '')[:200]}")
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
            res = _request_with_retry(requests.get, url, headers=headers)
            if res.status_code == 200:
                batch = res.json()
                if not batch:
                    break
                all_results.extend(batch)
                offset += len(batch)
                if len(batch) < limit:
                    break
            else:
                print(f"DB_CLIENT_API_ERROR (SelectAllPipeline {table}): {res.status_code} - {(res.text or '')[:200]}")
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
        res = _request_with_retry(requests.get, url, headers=headers)
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
        res = _request_with_retry(requests.post, url, headers=headers, json=params or {})
        if res.status_code in [200, 201, 204]:
            return res.json() if res.content else {"status": "success"}
        print(f"DB_CLIENT_API_ERROR (RPC {function_name}): {res.status_code} - {(res.text or '')[:200]}")
        return None

    def rpc_raise(self, function_name, params=None):
        """
        Like rpc() but raises RuntimeError with the API response text on error.
        Use this when the caller needs to detect specific errors like PGRST202.
        """
        url = f"{self.supabase_url}/rest/v1/rpc/{function_name}"
        headers = self._get_headers(use_service_role=True)
        headers["Prefer"] = "return=representation"
        res = _request_with_retry(requests.post, url, headers=headers, json=params or {})
        if res.status_code in [200, 201, 204]:
            return res.json() if res.content else {"status": "success"}
        err_msg = f"DB_CLIENT_API_ERROR (RPC {function_name}): {res.status_code} - {(res.text or '')[:200]}"
        print(err_msg)
        raise RuntimeError(err_msg)

def get_db_client():
    return DatabaseClient()
