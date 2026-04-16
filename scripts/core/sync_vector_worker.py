import os
import json
import logging
import sys
import requests
from dotenv import load_dotenv

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.utils import slugify

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("SyncVectorWorker")

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("❌ CRITICAL ERROR: SUPABASE_URL or SUPABASE_KEY is not set.")
    sys.exit(1)

class SyncVectorWorker:
    def __init__(self):
        self.api_url = f"{SUPABASE_URL}/rest/v1"
        self.headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

    def get_pending_enriched(self, limit=50):
        url = f"{self.api_url}/enriched_programs?status=eq.pending&limit={limit}"
        res = requests.get(url, headers=self.headers)
        if res.status_code == 200:
            return res.json()
        return []

    def sync_to_production(self, enriched):
        e_id = enriched['id']
        name = enriched['official_name']
        url = enriched['url']

        logger.info(f"Syncing to Production: {name}")

        # Map Enriched Pillars to Courses Schema with robust list handling
        def list_to_str(val):
            if isinstance(val, list):
                return ", ".join([str(v) for v in val if v])
            return str(val) if val else ""

        # Generate unique slug (include location and short ID if needed)
        base_slug = slugify(name)
        location = enriched.get('location', 'Nacional')
        
        # Add location if specific
        if location and location not in ["Nacional", "Nacional/No especificado"]:
            base_slug = f"{base_slug}-{slugify(location)}"
        
        # Add a short unique identifier from the original ID to guarantee uniqueness
        # while keeping the URL readable
        short_id = str(e_id).split('-')[0]
        full_slug = f"{base_slug}-{short_id}"

        course_data = {
            "institution_id": enriched['institution_id'],
            "name": name,
            "slug": full_slug,
            "url": url,
            "price_pen": enriched.get('total_cost_est'),
            "mode": enriched.get('modality'),
            "duration": enriched.get('duration_text'),
            "description_long": enriched.get('ai_summary'),
            "requirements": list_to_str(enriched.get('requirements')),
            "certification": list_to_str(enriched.get('certifications')),
            "course_type": enriched.get('degree_type'),
            "category": enriched.get('categories')[0] if enriched.get('categories') and isinstance(enriched.get('categories'), list) else None,
            "is_active": True,
            "last_scraped_at": "now()"
        }

        # Generate Embedding (Placeholder for OpenAI call)
        # course_data["embedding"] = self._generate_embedding(course_data["description_long"])

        # Upsert to production courses
        res = requests.post(
            f"{self.api_url}/courses?on_conflict=url",
            headers=self.headers,
            json=course_data
        )

        if res.status_code in [201, 204, 200]:
            logger.info(f"Successfully synced to production courses: {name}")
            self.update_enriched_status(e_id, "synced")
        else:
            logger.error(f"Error syncing to production: {res.text}")
            self.update_enriched_status(e_id, "error", error_msg=res.text)

    def update_enriched_status(self, e_id, status, error_msg=None):
        payload = {"status": status}
        if error_msg: payload["metadata"] = {"error": error_msg}
        requests.patch(
            f"{self.api_url}/enriched_programs?id=eq.{e_id}",
            headers=self.headers,
            json=payload
        )

if __name__ == "__main__":
    worker = SyncVectorWorker()
    pending = worker.get_pending_enriched()
    logger.info(f"Found {len(pending)} pending enriched records.")
    for record in pending:
        worker.sync_to_production(record)
    logger.info("Sync batch complete.")
