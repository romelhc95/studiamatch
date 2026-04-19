import os
import json
import logging
import re
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Generator

from bs4 import BeautifulSoup
import html
from dotenv import load_dotenv

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.utils import (
    clean_course_name,
    slugify,
    standardize_mode,
    normalize_url
)
from shared.db_client import get_db_client, DatabaseClient

# Setup logging
load_dotenv()
log_dir = os.path.join(".github", "log", "local")
os.makedirs(log_dir, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = f"cleansed_programs_{timestamp}.log"
log_path = os.path.join(log_dir, log_filename)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_path, encoding='utf-8')
    ],
)
logger = logging.getLogger("CleansingWorker")

# --- Pure Functions (Detections & Cleaning) ---

def aggressive_html_clean(raw_html: str) -> str:
    """
    Removes header, footer, nav, aside, script, style, and structural tags using BeautifulSoup.
    Also removes elements with classes/IDs related to navigation/branding.
    """
    if not raw_html:
        return ""
    
    soup = BeautifulSoup(raw_html, "html.parser")
    
    # 1. Decompose noisy tags
    for tag in soup(["head", "header", "footer", "nav", "aside", "script", "style", "noscript", "iframe", "svg"]):
        tag.decompose()
    
    # 2. Decompose elements with navigation/branding classes or IDs
    noise_patterns = re.compile(r'header|footer|nav|menu|topbar|sidebar|social|copyright|breadcrumb|banner', re.I)
    for element in soup.find_all(True, {"class": noise_patterns}):
        element.decompose()
    for element in soup.find_all(True, {"id": noise_patterns}):
        element.decompose()

    # 3. Extract text with separator to preserve block structure
    text = soup.get_text(separator="\n", strip=True)
    
    # 4. Final sanitization
    text = html.unescape(text)
    text = re.sub(r'\n\s*\n+', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    
    return text.strip()

def detect_locations(text: str) -> List[str]:
    cities = [
        "Lima", "Arequipa", "Trujillo", "Chiclayo", "Piura", "Iquitos", "Cusco", "Chimbote", 
        "Huancayo", "Tacna", "Ica", "Juliaca", "Ayacucho", "Cajamarca", "Pucallpa", "Sullana", 
        "Huanuco", "Huánuco", "Chincha", "Tarapoto", "Puno", "Tumbes", "Talara", "Huaraz", 
        "Cerro de Pasco", "Abancay", "Moquegua", "Ilo", "Puerto Maldonado"
    ]
    found = []
    campus_matches = re.findall(r'(?:campus|sede|filial|local|ubicaci[óo]n)\s+([A-Z][a-zñáéíóú]+(?:\s+[A-Z][a-zñáéíóú]+)*)', text, re.IGNORECASE)
    if campus_matches:
        for match in campus_matches:
            match_clean = match.strip()
            if match_clean and match_clean not in found: 
                found.append(match_clean)
    
    for city in cities:
        if re.search(r'\b' + city + r'\b', text, re.IGNORECASE):
            if city not in found: found.append(city)
            
    return found if found else ["Nacional/No especificado"]

def is_soft_404(text: str) -> bool:
    """Detects if the page content indicates a 404 error (Soft 404)."""
    patterns = [
        r"p[áa]gina no encontrada",
        r"error 404",
        r"no existe la p[áa]gina",
        r"lo sentimos.*?p[áa]gina.*?no existe",
        r"404 - ",
        r"page not found"
    ]
    low_text = text.lower()
    return any(re.search(p, low_text) for p in patterns)

def detect_obsolete_dates(text: str, url: str = "", name: str = "") -> Optional[str]:
    """
    Detects if the content mentions start dates in the past (e.g. 2025 when it is 2026).
    Rule: if date < current_date - 3 days.
    """
    today = datetime.now()
    
    # Hard block for years 2024 or older in URL or Name
    year_match = re.search(r'\b(20[0-1][0-9]|202[0-4])\b', f"{url} {name}")
    if year_match:
        return f"hard_obsolete_year:{year_match.group(1)}"

    # Check for past years with context in text
    past_years = [str(y) for y in range(2000, today.year)]
    for year in past_years:
        pattern = r'(?:inicio|clases|admisi[óo]n|fecha|ciclo|semestre).*?\b' + year + r'\b'
        if re.search(pattern, text, re.IGNORECASE | re.DOTALL):
            return f"obsolete_year:{year}"
            
    # Check for specific 2025 mentions that are likely old
    if "2025" in text and today.year == 2026:
        if re.search(r'(?:hasta el|desde el|inicia|comienza).*?2025', text, re.IGNORECASE):
            return "obsolete_date_2025"

    return None

def extract_price(text: str) -> Tuple[Optional[float], str]:
    price_match = re.search(r'S/\.?\s*([\d,.]+)', text, re.IGNORECASE)
    if price_match:
        try:
            price_str = price_match.group(1).replace(",", "")
            price_pen = float(price_str)
            if 10 < price_pen < 1000000:
                return price_pen, "publicado"
        except (ValueError, TypeError):
            pass
    return None, "consultar"

class CleansingWorker:
    def __init__(self, db_client: Optional[DatabaseClient] = None) -> None:
        self.db = db_client or get_db_client()
        self.exclusions = self._load_exclusions()
        logger.info(f"Loaded {len(self.exclusions)} exclusion patterns from DB.")

    def _load_exclusions(self) -> List[Dict[str, Any]]:
        try:
            return self.db.select('crawler_exclusions', filters="is_active=eq.true")
        except Exception as e:
            logger.warning(f"Could not load exclusions from DB: {e}.")
            return []

    def _get_base_url(self, url: str) -> str:
        """Strips common academic sub-page suffixes to group sibling pages."""
        suffixes = [
            'presentacion/', 'presentacion', 
            'beneficios/', 'beneficios', 
            'plana-docente/', 'plana-docente', 
            'malla-curricular/', 'malla-curricular', 
            'admision/', 'admision',
            'objetivos/', 'objetivos',
            'certificacion/', 'certificacion',
            'requisitos/', 'requirements/',
            'Paginas/curso-actualizacion.aspx'
        ]
        clean_url = url.rstrip('/') + '/'
        for s in suffixes:
            pattern = re.escape(s.rstrip('/')) + r'/?$'
            if re.search(pattern, clean_url, re.IGNORECASE):
                return re.sub(pattern, '', clean_url, flags=re.IGNORECASE).rstrip('/') + '/'
        return clean_url

    def stream_pending_staging(self, batch_size: int = 100) -> Generator[Dict[str, Any], None, None]:
        while True:
            try:
                batch = self.db.select('staging_raw', filters="status=eq.pending", limit=batch_size)
                if not batch:
                    break
                for record in batch:
                    yield record
            except Exception as e:
                logger.error(f"Error fetching staging records: {e}")
                break

    def is_invalid_course(self, name: str, description: str, url: str, inst_id: str, clean_text: str = "") -> Optional[str]:
        low_url = url.lower()
        low_name = name.lower()
        
        # 1. Hard DB Exclusions (Absolute block)
        for exc in self.exclusions:
            if exc.get('institution_id') and exc['institution_id'] != inst_id:
                continue
            pattern = exc['pattern'].lower()
            if pattern in low_url:
                return f"hard_db_exclusion:{pattern}"

        # 2. Soft 404 Check
        if is_soft_404(f"{name} {clean_text}"):
            return "soft_404_detected"

        # 3. Strict Keyword Validation (Rescue only)
        valid_patterns = [
            r'\bmaestr[íi]a\b', r'\bdiplomado\b', r'\bespecializaci[óo]n\b', 
            r'\bdoctorado\b', r'\bcurso\b', r'\btaller\b'
        ]
        has_valid_keyword = any(re.search(p, low_name) for p in valid_patterns)

        # 4. Minimum context check
        if not name or len(name) < 5:
            return "name_too_short"
        if not description or len(description) < 100:
            return "description_too_short"

        return None

    def process_batch(self, batch: List[Dict[str, Any]]) -> int:
        # Group by de-duplication key (Effective URL if present, else Base URL)
        groups: Dict[str, List[Dict[str, Any]]] = {}
        for raw in batch:
            # Prefer effective_url for technical de-duplication (redirection aware)
            key = raw.get('effective_url') or self._get_base_url(raw['url'])
            if key not in groups: groups[key] = []
            groups[key].append(raw)

        cleansed_batch = []
        staging_updates = []
        processed_count = 0

        for dedupe_url, members in groups.items():
            combined_html = ""
            combined_desc = ""
            
            # Aggregate content
            for m in members:
                combined_html += f"\n--- URL: {m['url']} ---\n" + (m.get('raw_html') or "")
                combined_desc += f" {m.get('raw_description') or ''}"

            # Select primary member (prefer one that matches the dedupe_url exactly, or just the first one)
            main_raw = members[0]
            for m in members:
                if m.get('effective_url') == dedupe_url or m['url'].rstrip('/') + '/' == dedupe_url:
                    main_raw = m
                    break
            
            inst_id = main_raw['institution_id']
            clean_text_context = aggressive_html_clean(combined_html)
            
            # Quality Gates
            discard_reason = self.is_invalid_course(main_raw.get('raw_name', ''), combined_desc, dedupe_url, inst_id, clean_text_context)
            if not discard_reason:
                discard_reason = detect_obsolete_dates(clean_text_context, dedupe_url, main_raw.get('raw_name', ''))
            
            if discard_reason:
                for m in members:
                    staging_updates.append({"id": m['id'], "status": "discarded", "metadata": {"discard_reason": discard_reason}})
                continue

            # Normalization
            clean_name = clean_course_name(main_raw.get('raw_name', ''))
            combined_full_text = f"{clean_name}\n{combined_desc}\n{clean_text_context}"
            
            mode = standardize_mode(combined_full_text)
            locations = detect_locations(combined_full_text)
            price_pen, p_status = extract_price(combined_full_text)

            cleansed_item = {
                "staging_id": main_raw['id'],
                "institution_id": inst_id,
                "url": dedupe_url,
                "clean_name": clean_name,
                "clean_description": combined_full_text[:15000], # High fidelity context
                "modality": mode,
                "location": ", ".join(locations),
                "base_price": price_pen,
                "currency": "PEN",
                "status": "pending",
                "metadata": {
                    "raw_name": main_raw.get('raw_name'),
                    "price_status": p_status,
                    "cleansed_at": datetime.now().isoformat(),
                    "sibling_urls": list(set([m['url'] for m in members])),
                    "sibling_staging_ids": [m['id'] for m in members]
                }
            }
            cleansed_batch.append(cleansed_item)
            for m in members:
                staging_updates.append({"id": m['id'], "status": "processed"})
            processed_count += len(members)

        if cleansed_batch:
            try:
                self.db.upsert('cleansed_programs', cleansed_batch, on_conflict="url")
                logger.info(f"Promoted {len(cleansed_batch)} courses (Consolidated {processed_count} URLs).")
            except Exception as e:
                logger.error(f"Failed bulk upsert: {e}")
                return 0

        for update in staging_updates:
            try:
                self.db.patch('staging_raw', filters=f"id=eq.{update['id']}", data={"status": update['status'], "metadata": update.get('metadata', {})})
            except Exception as e:
                pass

        return processed_count

if __name__ == "__main__":
    worker = CleansingWorker()
    logger.info("--- Starting Station 1.5: Surgical High Fidelity Cleansing ---")
    
    total_processed = 0
    batch_accumulator = []
    
    for record in worker.stream_pending_staging(batch_size=200): # Larger batches for better grouping
        batch_accumulator.append(record)
        if len(batch_accumulator) >= 100:
            total_processed += worker.process_batch(batch_accumulator)
            batch_accumulator = []

    if batch_accumulator:
        total_processed += worker.process_batch(batch_accumulator)

    logger.info(f"Session finished. Total staging URLs processed: {total_processed}")
