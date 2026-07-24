"""Migrate all configured data from explicit Supabase Free to Pro identities."""

import json
import os
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from scripts.shared.db_client import DatabaseClient
    from scripts.shared.supabase_credentials import (
        build_supabase_headers,
        get_environment_credentials,
        require_distinct_environments,
    )
except ImportError:
    from shared.db_client import DatabaseClient
    from shared.supabase_credentials import (
        build_supabase_headers,
        get_environment_credentials,
        require_distinct_environments,
    )


MGMT_TOKEN = os.environ.get("SUPABASE_MGMT_TOKEN", "")
PRO_TABLES = [
    "ratings", "reviews", "enriched_programs", "cleansed_programs",
    "staging_raw", "crawler_exclusions", "courses", "category_rules",
    "market_salaries", "categories", "institutions",
]
MIGRATION_ORDER = [
    "institutions", "categories", "market_salaries", "category_rules",
    "courses", "crawler_exclusions", "staging_raw", "cleansed_programs",
    "enriched_programs", "ratings", "reviews",
]


def run_mgmt_sql(sql, *, pro_project_ref):
    return requests.post(
        f"https://api.supabase.com/v1/projects/{pro_project_ref}/database/query",
        json={"query": sql},
        headers={
            "Authorization": f"Bearer {MGMT_TOKEN}",
            "Content-Type": "application/json",
        },
    )


def upsert_pro(table, data, *, pro_url, pro_rest_headers, batch_size=200):
    if not data:
        return 0
    inserted = 0
    for index in range(0, len(data), batch_size):
        batch = data[index:index + batch_size]
        clean_batch = []
        for row in batch:
            clean = {}
            for key, value in row.items():
                clean[key] = json.dumps(value) if isinstance(value, (dict, list)) else value
            clean_batch.append(clean)

        headers = {**pro_rest_headers, "Prefer": "resolution=merge-duplicates"}
        response = requests.post(
            f"{pro_url}/rest/v1/{table}",
            headers=headers,
            json=clean_batch,
            timeout=120,
        )
        if response.status_code in (200, 201):
            inserted += len(batch)
            print(f"  +{inserted}/{len(data)}", end="\r")
        else:
            for row in clean_batch:
                row_response = requests.post(
                    f"{pro_url}/rest/v1/{table}",
                    headers=headers,
                    json=[row],
                    timeout=60,
                )
                if row_response.status_code in (200, 201):
                    inserted += 1
                else:
                    print(f"\n  ROW FAIL: HTTP {row_response.status_code}")
        time.sleep(0.3)
    return inserted


def load_free_snapshot(db):
    """Read every source table successfully before any destructive Pro call."""
    snapshot = {}
    for table in MIGRATION_ORDER:
        print(f"  Preflight: {table}")
        rows = db.select_all_service(table)
        if not isinstance(rows, list):
            raise RuntimeError(f"Free preflight returned invalid data for {table}")
        snapshot[table] = rows
        print(f"    Loaded {len(rows)} records")
    return snapshot


def delete_pro_data(run_mgmt_sql_fn):
    """Delete Pro tables in dependency-safe order, aborting on first failure."""
    for table in PRO_TABLES:
        response = run_mgmt_sql_fn(f'DELETE FROM public."{table}" WHERE 1=1;')
        if response.status_code != 201:
            raise RuntimeError(f"Pro DELETE failed for {table}: HTTP {response.status_code}")
        print(f"  OK: {table}")


def execute_migration(db, *, run_mgmt_sql_fn, upsert_pro_fn):
    """Preflight Free completely, then replace Pro from the immutable snapshot."""
    print("\n1. Preflight all Free data...")
    snapshot = load_free_snapshot(db)

    print("\n2. DELETE existing Pro data...")
    delete_pro_data(run_mgmt_sql_fn)

    print("\n3. Migrate preflight snapshot...")
    total = 0
    for table in MIGRATION_ORDER:
        data = snapshot[table]
        if not data:
            print(f"  Empty: {table} (skipping)")
            continue
        migrated = upsert_pro_fn(table, data)
        total += migrated
        print(f"  Migrated {table}: {migrated}/{len(data)}")

    print("\n4. Re-enable triggers...")
    for statement in (
        "ALTER TABLE courses ENABLE TRIGGER tr_auto_assign_category;",
        "ALTER TABLE enriched_programs ENABLE TRIGGER tr_enriched_programs_updated_at;",
    ):
        response = run_mgmt_sql_fn(statement)
        if response.status_code != 201:
            raise RuntimeError(f"Pro trigger restore failed: HTTP {response.status_code}")
    print(f"\n=== Migration complete: {total} total records ===")
    return total


def main():
    print("=== DATA MIGRATION: Free -> Pro ===")
    if not MGMT_TOKEN:
        raise SystemExit("ERROR: Set SUPABASE_MGMT_TOKEN")

    free = get_environment_credentials("FREE")
    pro = get_environment_credentials("PRO")
    require_distinct_environments(free, pro)
    pro_project_ref = pro.url.removeprefix("https://").removesuffix(".supabase.co")
    pro_rest_headers = build_supabase_headers(pro.secret_key, kind="secret")
    db = DatabaseClient(free.url, free.secret_key)

    execute_migration(
        db,
        run_mgmt_sql_fn=lambda sql: run_mgmt_sql(
            sql,
            pro_project_ref=pro_project_ref,
        ),
        upsert_pro_fn=lambda table, data: upsert_pro(
            table,
            data,
            pro_url=pro.url,
            pro_rest_headers=pro_rest_headers,
        ),
    )


if __name__ == "__main__":
    main()
