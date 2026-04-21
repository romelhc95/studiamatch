import os
import json
import logging
import sys
import requests
from dotenv import load_dotenv

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.utils import slugify, setup_lima_logging
from shared.db_client import get_db_client

# Setup logging
load_dotenv()
logger = setup_lima_logging("SyncVectorWorker")

# Supabase credentials are now handled by db_client

class SyncVectorWorker:
    def __init__(self):
        self.db = get_db_client()

    def get_pending_enriched(self, limit=50):
        return self.db.select('enriched_programs', filters="status=eq.pending", limit=limit)

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

        # Robust category extraction
        raw_categories = enriched.get('categories')
        main_category = None
        if isinstance(raw_categories, list) and raw_categories:
            main_category = raw_categories[0]
        elif isinstance(raw_categories, str) and raw_categories:
            main_category = raw_categories.split(',')[0].strip()

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
            "category": main_category,
            "is_active": True,
            "last_scraped_at": "now()"
        }

        # Generate Embedding (Placeholder for OpenAI call)
        # course_data["embedding"] = self._generate_embedding(course_data["description_long"])

        # Upsert to production courses
        res = self.db.upsert('courses', course_data, on_conflict="url")

        if res:
            logger.info(f"Successfully synced to production courses: {name}")
            self.update_enriched_status(e_id, "synced")
        else:
            logger.error(f"Error syncing to production")
            self.update_enriched_status(e_id, "error", error_msg="DB Error")

    def update_enriched_status(self, e_id, status, error_msg=None):
        payload = {"status": status}
        if error_msg: payload["metadata"] = {"error": error_msg}
        self.db.patch('enriched_programs', filters=f"id=eq.{e_id}", data=payload)

if __name__ == "__main__":
    worker = SyncVectorWorker()
    pending = worker.get_pending_enriched()
    logger.info(f"Found {len(pending)} pending enriched records.")
    for record in pending:
        worker.sync_to_production(record)
    logger.info("Sync batch complete.")
