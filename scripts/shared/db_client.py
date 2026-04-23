import os
import requests
import json
import psycopg2
import psycopg2.extras
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
    def __init__(self, supabase_url=None, supabase_key=None, database_url="DEFAULT"):
        self.supabase_url = supabase_url if supabase_url is not None else (os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL"))
        self.supabase_key = supabase_key if supabase_key is not None else (os.getenv("SUPABASE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY"))
        self.database_url = database_url if database_url != "DEFAULT" else os.getenv("DATABASE_URL")
        
        # Handle Docker-to-Host connectivity automatically
        # Inside 'act' or Docker containers, localhost/127.0.0.1 won't reach the host.
        # We replace it with the Docker bridge IP or host.docker.internal
        if self.database_url and ("localhost" in self.database_url or "127.0.0.1" in self.database_url):
            self.database_url = self.database_url.replace("localhost", "172.18.0.1").replace("127.0.0.1", "172.18.0.1")
            print(f"DB_CLIENT: Adjusted local DATABASE_URL for Docker connectivity.")

        if self.supabase_url and ("localhost" in self.supabase_url or "127.0.0.1" in self.supabase_url):
            self.supabase_url = self.supabase_url.replace("localhost", "172.18.0.1").replace("127.0.0.1", "172.18.0.1")
            print(f"DB_CLIENT: Adjusted SUPABASE_URL for Docker connectivity.")

        # Decide mode: If DATABASE_URL is present, we use direct PostgreSQL
        self.use_local = False # Default to Cloud
        
        if self.database_url:
            try:
                self.conn = psycopg2.connect(self.database_url)
                self.conn.autocommit = True
                self.use_local = True
            except Exception as e:
                print(f"Error connecting to local DB: {e}. Falling back to API Mode.")
        
        if not self.use_local and (not self.supabase_url or not self.supabase_key):
            print("Warning: No DB configuration found (neither Local nor Cloud).")

    def select(self, table, filters=None, columns="*", limit=None, order=None):
        """
        Generic select. 
        Filters should be in PostgREST style for compatibility: "col=eq.val"
        Order should be in PostgREST style: "col.asc" or "col.desc.nullsfirst"
        """
        if self.use_local:
            return self._select_local(table, filters, columns, limit, order)
        else:
            return self._select_api(table, filters, columns, limit, order)

    def insert(self, table, data):
        """Generic insert."""
        if self.use_local:
            return self._insert_local(table, data)
        else:
            return self._insert_api(table, data)

    def patch(self, table, filters, data):
        """Generic update."""
        if self.use_local:
            return self._update_local(table, filters, data)
        else:
            return self._patch_api(table, filters, data)

    def upsert(self, table, data, on_conflict="url"):
        """
        Generic upsert. Supports single dict or list of dicts.
        """
        if self.use_local:
            return self._upsert_local(table, data, on_conflict)
        else:
            return self._upsert_api(table, data, on_conflict)

    # --- Local Implementations (psycopg2) ---
    def _prepare_values(self, data):
        """Serializes dicts to JSON strings for psycopg2."""
        return [json.dumps(v) if isinstance(v, dict) else v for v in data.values()]

    def _select_local(self, table, filters, columns, limit, order):
        if columns == "count":
            query = f"SELECT COUNT(*) as count FROM {table}"
        else:
            query = f"SELECT {columns} FROM {table}"
            
        params = []
        if filters:
            where_clauses, params = self._parse_rest_filters(filters)
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
        
        if order:
            # Handle "col.asc.nullsfirst" -> "col ASC NULLS FIRST"
            parts = order.split('.')
            col = parts[0]
            direction = "ASC" if "asc" in parts else "DESC"
            nulls = ""
            if "nullsfirst" in parts: nulls = " NULLS FIRST"
            if "nullslast" in parts: nulls = " NULLS LAST"
            query += f" ORDER BY {col} {direction}{nulls}"

        if limit and columns != "count":
            query += f" LIMIT {limit}"
            
        with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            results = cur.fetchall()
            if columns == "count":
                return results # [{ "count": X }]
            return results

    def _insert_local(self, table, data):
        columns = data.keys()
        values = self._prepare_values(data)
        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(['%s'] * len(values))}) RETURNING *"
        with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, values)
            return cur.fetchone()

    def _update_local(self, table, filters, data):
        set_clauses = [f"{k} = %s" for k in data.keys()]
        params = self._prepare_values(data)
        query = f"UPDATE {table} SET {', '.join(set_clauses)}"
        
        if filters:
            where_clauses, filter_params = self._parse_rest_filters(filters)
            query += " WHERE " + " AND ".join(where_clauses)
            params.extend(filter_params)
            
        with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            return {"status": "success"}

    def _upsert_local(self, table, data, on_conflict):
        items = data if isinstance(data, list) else [data]
        results = []
        
        for item in items:
            columns = list(item.keys())
            values = self._prepare_values(item)
            placeholders = ["%s"] * len(columns)
            
            update_clauses = [f"{c} = EXCLUDED.{c}" for c in columns if c != on_conflict]
            
            query = f"""
                INSERT INTO {table} ({', '.join(columns)}) 
                VALUES ({', '.join(placeholders)})
                ON CONFLICT ({on_conflict}) 
                DO UPDATE SET {', '.join(update_clauses)}
                RETURNING *
            """
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(query, values)
                res = cur.fetchone()
                if res: results.append(res)
        
        return results if isinstance(data, list) else (results[0] if results else None)

    def _translate_op(self, col, op_val):
        if '.' not in op_val: return None, None
        op, val = op_val.split('.', 1)
        
        if op == 'eq': return f"{col} = %s", val
        if op == 'ilike': 
            sql_val = val.replace('*', '%')
            return f"{col} ILIKE %s", sql_val
        if op == 'is' and val == 'null':
            return f"{col} IS NULL", None
        if op == 'is' and val == 'not.null':
            return f"{col} IS NOT NULL", None
        return None, None

    def _parse_rest_filters(self, filters):
        clauses = []
        params = []
        
        # Handle "or=(col1.op.val,col2.op.val)"
        if filters.startswith("or=(") and filters.endswith(")"):
            inner = filters[4:-1]
            or_parts = inner.split(',')
            or_clauses = []
            for part in or_parts:
                if '.' in part:
                    col, op, val = part.split('.', 2)
                    clause, param = self._translate_op(col, f"{op}.{val}")
                    if clause:
                        or_clauses.append(clause)
                        if param is not None: params.append(param)
            if or_clauses:
                clauses.append("(" + " OR ".join(or_clauses) + ")")
            return clauses, params

        parts = filters.split('&')
        for part in parts:
            if '=' in part:
                col, op_val = part.split('=', 1)
                clause, param = self._translate_op(col, op_val)
                if clause:
                    clauses.append(clause)
                    if param is not None:
                        params.append(param)
        return clauses, params

    # --- API Implementations (requests) ---
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

    def _upsert_api(self, table, data, on_conflict):
        url = f"{self.supabase_url}/rest/v1/{table}?on_conflict={on_conflict}"
        headers = self._get_headers()
        headers["Prefer"] = "resolution=merge-duplicates,return=representation"
        res = requests.post(url, headers=headers, json=data)
        if res.status_code in [200, 201, 204]:
            return res.json() if res.content else {"status": "success"}
        print(f"DB_CLIENT_API_ERROR (Upsert): {res.status_code} - {res.text}")
        return None

def get_db_client():
    return DatabaseClient()
