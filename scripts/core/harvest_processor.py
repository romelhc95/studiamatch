import os
import json
import logging
import re
import sys
from datetime import datetime
import requests
from dotenv import load_dotenv

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.utils import (
    clean_course_name,
    infer_course_type,
    standardize_category,
    slugify,
    standardize_mode
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("HarvestProcessor")

load_dotenv()

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

class HarvestProcessor:
    def __init__(self):
        self.api_url = f"{SUPABASE_URL}/rest/v1"
        self.headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

    def get_pending_harvests(self, limit=100):
        url = f"{self.api_url}/harvesting?status=eq.pending&limit={limit}&select=*,institutions(slug)"
        res = requests.get(url, headers=self.headers)
        if res.status_code == 200:
            return res.json()
        return []

    def is_invalid_course(self, name, description, html=""):
        """Heuristics to identify non-course pages."""
        if not name or len(name) < 5:
            return "name_too_short"
            
        blacklist = [
            "descubre nuestras", "explorar carreras", "oferta académica", 
            "página no encontrada", "404", "error", "portal", "home",
            "inicio", "contactanos", "nosotros", "malla curricular",
            "admision", "revisa nuestro", "conoce mas", "universidad peruana",
            "todos los derechos", "facultad de", "escuela de", "lista de cursos"
        ]
        
        low_name = name.lower()
        for b in blacklist:
            if b in low_name:
                return f"blacklist_match:{b}"
        
        if not description or len(description) < 100:
            return "description_too_short"

        return None

    def process_record(self, harvest):
        h_id = harvest['id']
        url = harvest['url']
        raw_name = harvest.get('raw_name') or ""
        raw_desc = harvest.get('raw_description') or ""
        raw_html = harvest.get('raw_html') or ""
        inst_id = harvest['institution_id']

        logger.info(f"Processing: {url}")

        # 1. Validation
        discard_reason = self.is_invalid_course(raw_name, raw_desc, raw_html)
        if discard_reason:
            logger.warning(f"Discarding {url}: {discard_reason}")
            self.update_harvest_status(h_id, "discarded", discard_reason=discard_reason)
            return

        # 2. Cleaning & Normalization
        clean_name = clean_course_name(raw_name)
        course_type = infer_course_type(clean_name)
        category = standardize_category("", clean_name)
        
        # Mode detection from raw content
        mode = self._detect_mode(raw_desc + " " + raw_html)
        
        # Price detection
        price_pen, price_status = self._extract_price(raw_desc + " " + raw_html)

        # 3. Save to Courses
        course_data = {
            "institution_id": inst_id,
            "name": clean_name,
            "slug": slugify(clean_name),
            "url": url,
            "price_pen": price_pen,
            "price_status": price_status,
            "mode": mode,
            "category": category,
            "course_type": course_type,
            "description_long": raw_desc,
            "is_active": True,
            "last_scraped_at": datetime.now().isoformat()
        }

        # Upsert to courses (using URL as unique key)
        res = requests.post(
            f"{self.api_url}/courses?on_conflict=url",
            headers=self.headers,
            json=course_data
        )

        if res.status_code in [201, 204, 200]:
            logger.info(f"Successfully promoted to courses: {clean_name}")
            self.update_harvest_status(h_id, "processed")
        else:
            logger.error(f"Error promoting {url}: {res.text}")
            self.update_harvest_status(h_id, "error", error_msg=res.text)

    def _detect_mode(self, text):
        text = text.lower()
        if any(k in text for k in ["semipresencial", "híbrido", "hibrido", "blended"]):
            return "Híbrido"
        if any(k in text for k in ["remoto", "virtual", "a distancia", "online"]):
            return "Remoto"
        return "Presencial"

    def _extract_price(self, text):
        # Very basic regex for Peruvian Sole
        price_match = re.search(r'S/\s*([\d,.]+)', text, re.IGNORECASE)
        if price_match:
            try:
                price_str = price_match.group(1).replace(",", "")
                price_pen = float(price_str)
                # Validation: A course rarely costs more than 1,000,000 PEN
                # If it's higher, it's likely a phone number or metadata error
                if 10 < price_pen < 1000000:
                    return price_pen, "publicado"
            except: pass
        return None, "consultar"

    def update_harvest_status(self, h_id, status, discard_reason=None, error_msg=None):
        payload = {"status": status}
        if discard_reason: payload["discard_reason"] = discard_reason
        if error_msg: payload["processing_error"] = error_msg
        
        requests.patch(
            f"{self.api_url}/harvesting?id=eq.{h_id}",
            headers=self.headers,
            json=payload
        )

if __name__ == "__main__":
    processor = HarvestProcessor()
    pending = processor.get_pending_harvests(limit=50)
    logger.info(f"Found {len(pending)} pending harvests.")
    
    for record in pending:
        processor.process_record(record)
    
    logger.info("Batch processing complete.")
