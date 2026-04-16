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
logger = logging.getLogger("CleansingWorker")

load_dotenv()

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

class CleansingWorker:
    def __init__(self):
        self.api_url = f"{SUPABASE_URL}/rest/v1"
        self.headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

    def get_pending_staging(self, limit=100):
        """Get pending records from staging_raw."""
        url = f"{self.api_url}/staging_raw?status=eq.pending&limit={limit}"
        res = requests.get(url, headers=self.headers)
        if res.status_code == 200:
            return res.json()
        return []

    def is_invalid_course(self, name, description, url="", html=""):
        """Heuristics to identify non-course pages."""
        low_url = url.lower()
        url_blacklist = ["/noticias/", "/noticia/", "/blog/", "/eventos/", "/comunicados/", "/articulo/", "/articulos/"]
        if any(pattern in low_url for pattern in url_blacklist):
            return "url_blacklist_match"

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

    def process_record(self, raw):
        r_id = raw['id']
        url = raw['url']
        raw_name = raw.get('raw_name') or ""
        raw_desc = raw.get('raw_description') or ""
        raw_html = raw.get('raw_html') or ""
        inst_id = raw['institution_id']

        logger.info(f"Cleansing: {url}")

        # 1. Validation
        discard_reason = self.is_invalid_course(raw_name, raw_desc, url, raw_html)
        if discard_reason:
            logger.warning(f"Discarding {url}: {discard_reason}")
            self.update_staging_status(r_id, "discarded", discard_reason=discard_reason)
            return

        # 2. Cleaning & Normalization
        clean_name = clean_course_name(raw_name)
        
        # Mode detection
        mode = self._detect_mode(raw_desc + " " + raw_html)
        
        # Location detection (Critical for multiple records per location)
        locations = self._detect_locations(raw_desc + " " + raw_html)
        
        # Price detection
        price_pen, _ = self._extract_price(raw_desc + " " + raw_html)

        # 3. Create Cleansed Records (One per location)
        created_count = 0
        for loc in locations:
            cleansed_data = {
                "staging_id": r_id,
                "institution_id": inst_id,
                "url": url if len(locations) == 1 else f"{url}#{slugify(loc)}",
                "clean_name": clean_name,
                "clean_description": raw_desc[:5000], # Keep a reasonable chunk
                "modality": mode,
                "location": loc,
                "base_price": price_pen,
                "currency": "PEN",
                "status": "pending",
                "metadata": {
                    "raw_name": raw_name,
                    "location_detected": loc
                }
            }

            # Upsert to cleansed_programs
            res = requests.post(
                f"{self.api_url}/cleansed_programs?on_conflict=url",
                headers=self.headers,
                json=cleansed_data
            )

            if res.status_code in [201, 204, 200]:
                created_count += 1
            else:
                logger.error(f"Error saving cleansed record for {url}: {res.text}")

        if created_count > 0:
            logger.info(f"Promoted to cleansed: {clean_name} ({created_count} locations)")
            self.update_staging_status(r_id, "processed")
        else:
            self.update_staging_status(r_id, "error", error_msg="No cleansed records created")

    def _detect_mode(self, text):
        text = text.lower()
        if any(k in text for k in ["semipresencial", "híbrido", "hibrido", "blended"]):
            return "Híbrido"
        if any(k in text for k in ["remoto", "virtual", "a distancia", "online"]):
            return "Remoto"
        return "Presencial"

    def _detect_locations(self, text):
        # Common Peruvian cities/campus
        cities = ["Lima", "Arequipa", "Trujillo", "Cusco", "Piura", "Chiclayo", "Huancayo", "Ica", "Tacna"]
        found = []
        for city in cities:
            if re.search(r'\b' + city + r'\b', text, re.IGNORECASE):
                found.append(city)
        return found if found else ["Nacional/No especificado"]

    def _extract_price(self, text):
        price_match = re.search(r'S/\s*([\d,.]+)', text, re.IGNORECASE)
        if price_match:
            try:
                price_str = price_match.group(1).replace(",", "")
                price_pen = float(price_str)
                if 10 < price_pen < 1000000:
                    return price_pen, "publicado"
            except: pass
        return None, "consultar"

    def update_staging_status(self, r_id, status, discard_reason=None, error_msg=None):
        payload = {"status": status}
        if discard_reason: payload["metadata"] = {"discard_reason": discard_reason}
        if error_msg: payload["metadata"] = {"error": error_msg}
        
        requests.patch(
            f"{self.api_url}/staging_raw?id=eq.{r_id}",
            headers=self.headers,
            json=payload
        )

if __name__ == "__main__":
    worker = CleansingWorker()
    pending = worker.get_pending_staging(limit=50)
    logger.info(f"Found {len(pending)} pending raw records.")
    
    for record in pending:
        worker.process_record(record)
    
    logger.info("Cleansing batch complete.")
