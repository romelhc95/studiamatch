import os
import logging
from supabase import create_client
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PurgeWorker")

load_dotenv()

def purge():
    url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    key = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
    supabase = create_client(url, key)
    
    blacklist = ["noticia", "noticias", "blog", "articulo", "eventos", "comunicados"]
    
    for b in blacklist:
        target = f"%/{b}/%"
        res = supabase.table("cleansed_programs").delete().ilike("url", target).execute()
        # In newer supabase-py versions, res.data contains the deleted records
        count = len(res.data) if hasattr(res, 'data') else "Unknown"
        logger.info(f"Purged {count} entries containing '{b}' in URL from cleansed_programs")

if __name__ == "__main__":
    purge()
