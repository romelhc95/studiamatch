import os
from supabase import create_client

def main():
    # Allow overriding from env, or fall back to known local values for testing
    url = os.environ.get('SUPABASE_URL', os.environ.get('NEXT_PUBLIC_SUPABASE_URL'))
    key = os.environ.get('SUPABASE_KEY', os.environ.get('NEXT_PUBLIC_SUPABASE_ANON_KEY'))
    if not url or not key:
        print("Missing SUPABASE_URL or SUPABASE_KEY")
        return
        
    try:
        supabase = create_client(url, key)
        # Attempt to truncate or delete all rows in staging_raw
        # Supabase python client doesn't support 'truncate' directly, so we delete everything.
        # Alternatively, we just query it to see if it exists.
        res = supabase.table('staging_raw').select('id', count='exact').limit(1).execute()
        print("Table 'staging_raw' exists. Count:", res.count)
        
        # Deleting all rows (requires appropriate RLS or service_role key)
        delete_res = supabase.table('staging_raw').delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        print("Deleted rows from 'staging_raw'.")
    except Exception as e:
        print("Error accessing staging_raw:", e)

if __name__ == "__main__":
    main()
