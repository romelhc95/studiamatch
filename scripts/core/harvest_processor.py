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
from shared.db_client import get_db_client

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("HarvestProcessor")

load_dotenv()

# Credentials handled by db_client

class HarvestProcessor:
    def __init__(self):
        self.db = get_db_client()

    def get_pending_harvests(self, limit=100):
        # We simplify the select to remove joins for better local compatibility
        # since institutions(slug) was not being used in the logic.
        return self.db.select('harvesting', filters="status=eq.pending", limit=limit)

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
        res = self.db.upsert('courses', course_data, on_conflict="url")

        if res:
            logger.info(f"Successfully promoted to courses: {clean_name}")
            self.update_harvest_status(h_id, "processed")
        else:
            logger.error(f"Error promoting {url}")
            self.update_harvest_status(h_id, "error", error_msg="DB Error")

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
        
        self.db.patch('harvesting', filters=f"id=eq.{h_id}", data=payload)

if __name__ == "__main__":
    processor = HarvestProcessor()
    pending = processor.get_pending_harvests(limit=50)
    logger.info(f"Found {len(pending)} pending harvests.")
    
    for record in pending:
        processor.process_record(record)
    
    logger.info("Batch processing complete.")
