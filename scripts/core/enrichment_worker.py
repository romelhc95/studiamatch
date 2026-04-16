import os
import json
import logging
import sys
import requests
from dotenv import load_dotenv

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("EnrichmentWorker")

load_dotenv()

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class EnrichmentWorker:
    def __init__(self):
        self.api_url = f"{SUPABASE_URL}/rest/v1"
        self.headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

    def get_pending_cleansed(self, limit=10):
        """Get pending records from cleansed_programs."""
        url = f"{self.api_url}/cleansed_programs?status=eq.pending&limit={limit}"
        res = requests.get(url, headers=self.headers)
        if res.status_code == 200:
            return res.json()
        return []

    def enrich_record(self, cleansed):
        c_id = cleansed['id']
        name = cleansed['clean_name']
        desc = cleansed['clean_description']
        inst_id = cleansed['institution_id']
        url = cleansed['url']

        logger.info(f"Enriching: {name} ({url})")

        # LLM Logic (Simplified for the plan, ideally uses a dedicated prompt)
        try:
            enriched_data = self._call_llm_for_pillars(name, desc)
            if not enriched_data:
                raise Exception("LLM returned empty data")

            # Final data to save
            save_data = {
                "cleansed_id": c_id,
                "institution_id": inst_id,
                "url": url,
                **enriched_data,
                "status": "pending"
            }

            # Upsert to enriched_programs
            res = requests.post(
                f"{self.api_url}/enriched_programs?on_conflict=url",
                headers=self.headers,
                json=save_data
            )

            if res.status_code in [201, 204, 200]:
                logger.info(f"Successfully enriched: {name}")
                self.update_cleansed_status(c_id, "enriched")
            else:
                logger.error(f"Error saving enriched record: {res.text}")
                self.update_cleansed_status(c_id, "error", error_msg=res.text)

        except Exception as e:
            logger.error(f"Enrichment error for {name}: {e}")
            self.update_cleansed_status(c_id, "error", error_msg=str(e))

    def _call_llm_for_pillars(self, name, description):
        """Call LLM to extract the 14 pillars."""
        # This is a placeholder for the actual LLM call logic
        # In production, this uses OpenAI/Anthropic with a JSON schema prompt
        logger.info("Calling LLM (Simulated)...")
        
        # PROMPT MOCK/TEMPLATE:
        # "Extract the following 14 pillars from this course description in JSON format..."
        
        return {
            "official_name": name,
            "duration_text": "5 años",
            "duration_months": 60,
            "total_cost_est": None,
            "requirements": ["Certificado de estudios", "DNI"],
            "graduate_profile": "Profesional capaz de liderar estrategias de marketing...",
            "curriculum_summary": {"ciclo1": ["Matematica", "Marketing 1"]},
            "modality": "Presencial",
            "primary_campus": "Sede Central",
            "degree_type": "Bachiller",
            "start_date": None,
            "partnerships": [],
            "certifications": [],
            "language": "Español",
            "categories": ["Negocios", "Marketing"],
            "ai_summary": f"La carrera de {name} ofrece una formación integral..."
        }

    def update_cleansed_status(self, c_id, status, error_msg=None):
        payload = {"status": status}
        if error_msg: payload["metadata"] = {"error": error_msg}
        
        requests.patch(
            f"{self.api_url}/cleansed_programs?id=eq.{c_id}",
            headers=self.headers,
            json=payload
        )

if __name__ == "__main__":
    worker = EnrichmentWorker()
    pending = worker.get_pending_cleansed(limit=5)
    logger.info(f"Found {len(pending)} pending cleansed records.")
    
    for record in pending:
        worker.enrich_record(record)
    
    logger.info("Enrichment batch complete.")
