import os
import requests
import json
from dotenv import load_dotenv
import re
import urllib.parse

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
    Switches automatically between local PostgreSQL (direct SQL) 
    and Supabase Cloud (Rest API) based on environment.
    """
    def __init__(self, supabase_url=None, supabase_key=None):
        self.supabase_url = supabase_url if supabase_url is not None else (os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL"))
        self.supabase_key = supabase_key if supabase_key is not None else (os.getenv("SUPABASE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY"))

    def _get_headers(self):
        return {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json"
        }

    def _select_api(self, table, filters, columns, limit, order):
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
            
        res = requests.get(url, headers=self._get_headers())
        if res.status_code == 200:
            data = res.json()
            if columns == "count":
                # Supabase returns count as a number if using head or specific headers,
                # but with select=count it usually returns a list with a count object or exact number
                return data
            return data
        return []

    def _insert_api(self, table, data):
        url = f"{self.supabase_url}/rest/v1/{table}"
        res = requests.post(url, headers=self._get_headers(), json=data)
        if res.status_code in [200, 201, 204]:
            return res.json() if res.content else {"status": "success"}
        print(f"DB_CLIENT_API_ERROR (Insert): {res.status_code} - {res.text}")
        return None

    def _patch_api(self, table, filters, data):
        url = f"{self.supabase_url}/rest/v1/{table}?{filters}"
        res = requests.patch(url, headers=self._get_headers(), json=data)
        if res.status_code in [200, 204]:
            return {"status": "success"}
        print(f"DB_CLIENT_API_ERROR (Patch): {res.status_code} - {res.text}")
        return {"status": "error"}

    def _delete_api(self, table, filters):
        url = f"{self.supabase_url}/rest/v1/{table}?{filters}"
        res = requests.delete(url, headers=self._get_headers())
        if res.status_code in [200, 201, 204]:
            return res.json() if res.content else {"status": "success"}
        print(f"DB_CLIENT_API_ERROR (Delete {table}): {res.status_code} - {res.text}")
        return None

    def _upsert_api(self, table, data, on_conflict):
        url = f"{self.supabase_url}/rest/v1/{table}?on_conflict={on_conflict}"
        headers = self._get_headers()
        headers["Prefer"] = "resolution=merge-duplicates,return=representation"
        is_batch = isinstance(data, list)
        res = requests.post(url, headers=headers, json=data)
        if res.status_code in [200, 201, 204]:
            return res.json() if res.content else {"status": "success"}
        print(f"DB_CLIENT_API_ERROR (Upsert {table}): {res.status_code} - {res.text}")
        return None

    # --- Public API methods (Cloud-Only) ---

    def select(self, table, filters=None, columns="*", limit=None, order=None):
        """Select records from Supabase REST API."""
        return self._select_api(table, filters, columns, limit, order)

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
        Paginated select that returns ALL matching records by looping through batches.
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
            headers = self._get_headers()
            headers["Range"] = f"{offset}-{offset + limit - 1}"
            headers["Prefer"] = "count=exact"
            res = requests.get(url, headers=headers)
            if res.status_code == 200:
                batch = res.json()
                if not batch:
                    break
                all_results.extend(batch)
                offset += len(batch)
                if len(batch) < limit:
                    break
            else:
                print(f"DB_CLIENT_API_ERROR (SelectAll {table}): {res.status_code} - {res.text}")
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
        headers = self._get_headers()
        headers["Prefer"] = "count=exact"
        res = requests.get(url, headers=headers)
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
        """
        url = f"{self.supabase_url}/rest/v1/rpc/{function_name}"
        headers = self._get_headers()
        headers["Prefer"] = "return=representation"
        res = requests.post(url, headers=headers, json=params or {})
        if res.status_code in [200, 201, 204]:
            return res.json() if res.content else {"status": "success"}
        print(f"DB_CLIENT_API_ERROR (RPC {function_name}): {res.status_code} - {res.text}")
        return None

def get_db_client():
    return DatabaseClient()
