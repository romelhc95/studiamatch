import re
import unicodedata
import random
import logging
import sys
from datetime import datetime, timezone, timedelta

class LimaFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        # Convert to Lima Time (UTC-5)
        lima_tz = timezone(timedelta(hours=-5))
        dt = datetime.fromtimestamp(record.created, tz=lima_tz)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.isoformat()

def setup_lima_logging(name: str):
    """Configures a logger with Lima Time formatting."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = LimaFormatter("%(asctime)s - [%(name)s] - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger

def get_random_user_agent():
    """
    Returns a random real User-Agent for stealth scraping.
    """
    user_agents = [
        # Chrome Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        # Firefox Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        # Chrome Mac
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        # Safari Mac
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        # Edge Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
    ]
    return random.choice(user_agents)

def slugify(text):
    """
    Standardizes a string into a URL-friendly slug.
    Normalizes unicode (NFD) to handle characters like 'í' -> 'i'.
    """
    if not text:
        return ""
    text = unicodedata.normalize('NFD', text)
    text = text.encode('ascii', 'ignore').decode('utf-8')
    text = text.lower()
    text = re.sub(r'[^a-z0-9-]', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')

def standardize_mode(mode_str):
    """
    Standardizes modality using common synonyms for StudIAMatch.
    Returns one of: 'Remoto', 'Híbrido', 'Presencial'.
    """
    if not mode_str:
        return "Presencial"
    
    m = mode_str.lower()
    # List of keywords for Remoto/Virtual
    if any(k in m for k in ["remoto", "online", "virtual", "a distancia", "distancia", "asincronico", "asincrónico"]):
        return "Remoto"
    # List of keywords for Híbrido/Blended
    elif any(k in m for k in ["híbrido", "hybrid", "hibrido", "semipresencial", "blended", "sincronico", "sincrónico", "aula virtual"]):
        return "Híbrido"
    else:
        return "Presencial"

import requests
import tempfile
import PyPDF2
import os

def infer_course_type(name):
    """
    Infers the educational type based on the course name.
    Avoids returning generic 'Otros'.
    """
    if not name:
        return "Programa"
    name_upper = name.upper()
    if any(k in name_upper for k in ["MAESTRÍA", "MAESTRIA", "MASTER", "MBA"]):
        return "Maestría"
    if "DOCTORADO" in name_upper:
        return "Doctorado"
    if "DIPLOMADO" in name_upper:
        return "Diplomado"
    if "CERTIFICACIÓN" in name_upper or "CERTIFICACION" in name_upper or "CERTIFICADO" in name_upper:
        return "Certificación"
    if "POSTGRADO" in name_upper or "POSGRADO" in name_upper:
        return "Postgrado"
    if "TALLER" in name_upper:
        return "Taller"
    if any(k in name_upper for k in ["CURSO", "ESPECIALIZACIÓN", "ESPECIALIZACION"]):
        return "Curso"
    
    # Fallback to "Programa" instead of "Otros"
    return "Programa"

def extract_pdf_text_from_url(url):
    """
    Downloads a PDF from a given URL and extracts its text.
    Returns the extracted string or an empty string if it fails.
    """
    if not url:
        return ""
    
    try:
        response = requests.get(url, stream=True, timeout=15)
        response.raise_for_status()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            for chunk in response.iter_content(chunk_size=8192):
                temp_pdf.write(chunk)
            temp_pdf_path = temp_pdf.name
            
        text_content = []
        try:
            with open(temp_pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                # Parse up to first 20 pages to avoid massive processing
                num_pages = min(20, len(reader.pages))
                for page_num in range(num_pages):
                    page = reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(page_text)
        finally:
            os.remove(temp_pdf_path)
            
        return "\n".join(text_content).strip()
    except Exception as e:
        print(f"Error parseando PDF {url}: {e}")
        return ""

# List of keywords that define a DATA course (Pilot Niche)
DATA_KEYWORDS = [
    r"data science", r"ciencia de datos", r"inteligencia artificial", r"artificial intelligence",
    r"machine learning", r"aprendizaje automático", r"data analytics", r"analítica de datos",
    r"data engineering", r"ingeniería de datos", r"big data", r"deep learning", r"minería de datos"
]

def is_data_course(name):
    """
    Checks if the course name matches DATA keywords for specialized filtering.
    """
    if not name:
        return False
    name_lower = name.lower()
    return any(re.search(k, name_lower) for k in DATA_KEYWORDS)

def clean_course_name(name):
    """
    Removes redundant terms like 'Curso ', 'Oficial ', etc.
    """
    if not name:
        return ""
    
    # Remove common redundant titles/modifiers anywhere they look like a prefix (after boundary)
    # This catches "Curso...", "PECB - Curso...", etc.
    keywords = ["Curso", "Programa", "Diplomado", "Especialización", "Especializacion", "Taller", "Seminario", "Oficial", "Internacional"]
    pattern = r'\b(' + '|'.join(keywords) + r')\b\s+(de\s+|en\s+)?'
    
    name = re.sub(pattern, '', name, flags=re.IGNORECASE)
    
    # Cleanup dash garbage: "PECB -  ISO" -> "PECB - ISO"
    name = re.sub(r'\s*-\s*', ' - ', name)
    name = re.sub(r'\s+', ' ', name)
    
    # Final trim
    return name.strip()

_category_rules_cache = None

def standardize_category(potential_cat, course_name=""):
    """
    Returns a granular category based on rules from Supabase DB or course name.
    Uses an in-memory cache to avoid redundant network calls during mass scraping.
    """
    global _category_rules_cache
    
    text = (potential_cat + " " + course_name).lower()
    url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    key = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

    # 1. Initialize Cache if empty
    if _category_rules_cache is None:
        _category_rules_cache = []
        if url and key:
            try:
                # Fetch rules ordered by priority from the dynamic engine
                headers = {"apikey": key, "Authorization": f"Bearer {key}"}
                # We fetch from the 'category_rules' table and join with 'categories'
                api_url = f"{url}/rest/v1/category_rules?select=keyword,priority,categories(name)&order=priority.desc"
                res = requests.get(api_url, headers=headers, timeout=10)
                if res.status_code == 200:
                    _category_rules_cache = res.json()
                else:
                    print(f"Warning: Could not fetch category rules (Status {res.status_code})")
            except Exception as e:
                print(f"Error initializing category cache: {e}")

    # 2. Try matching via dynamic rules (Highest priority wins)
    for rule in _category_rules_cache:
        keyword = rule.get("keyword", "").lower()
        if keyword and keyword in text:
            # Check if it's a nested object from the join
            cat_obj = rule.get("categories")
            if isinstance(cat_obj, dict):
                return cat_obj.get("name", "Tecnología")
            elif isinstance(cat_obj, list) and len(cat_obj) > 0:
                return cat_obj[0].get("name", "Tecnología")

    # 3. Fallback to hardcoded logic if no DB match found (Legacy support)
    if any(k in text for k in ["office", "excel", "word", "powerpoint", "outlook", "visio", "project"]):
        return "Ofimática y Productividad"
    if any(k in text for k in ["power bi", "tableau", "qlik", "analytics", "analítica"]):
        return "Data Analytics"
    if any(k in text for k in ["seguridad", "hacking", "cyber", "ciber", "owasp", "fortinet", "palo alto", "firewall"]):
        return "Ciberseguridad"
    if any(k in text for k in ["cloud", "azure", "aws", "google cloud", "gcp", "amazon web services"]):
        return "Cloud Computing"
    if any(k in text for k in ["data", "datos", "ia", "artificial", "machine learning", "deep learning", "python for data"]):
        return "Data Science & IA"
    if any(k in text for k in ["devops", "docker", "kubernetes", "jenkins", "terraform", "ansible"]):
        return "DevOps & Infraestructura"
    if any(k in text for k in ["agil", "project", "pmp", "scrum", "itil", "gestión", "gestion", "management", "liderazgo"]):
        return "Gestión y Agilidad"
    if any(k in text for k in ["cisco", "redes", "network", "ccna", "ccnp", "routing", "switching"]):
        return "Redes y Conectividad"
    if any(k in text for k in ["java", "python", "php", "javascript", "react", "desarrollo", "programación", "web", "frontend", "backend", "fullstack", "angular", "vue", "node"]):
        return "Desarrollo y Web"
    
    # 4. Final Fallback
    if potential_cat:
        cat = potential_cat.replace("-", " ").title()
        if cat.lower() not in ["curso", "programa", "especialidad", "taller"]:
            return cat
    
    return "Tecnología"

from urllib.parse import urlparse, urlunparse

def normalize_url(url):
    """
    Normalizes a URL for de-duplication:
    - Lowercases scheme and netloc.
    - Removes query strings and fragments.
    - Removes trailing slashes.
    """
    if not url:
        return ""
    
    try:
        parsed = urlparse(url)
        # 1. Lowercase scheme and netloc
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()
        
        # 2. Path normalization: remove trailing slash
        path = parsed.path
        if path.endswith('/') and len(path) > 1:
            path = path[:-1]
        
        # 3. Deduplicate /en/ language prefix (e.g. /en/posgrado/ → /posgrado/)
        import re as _re
        if '/en/' in path:
            path = _re.sub(r'/en/', '/', path)
        
        # 4. Reconstruct without query strings and fragments
        normalized = urlunparse((scheme, netloc, path, '', '', ''))
        return normalized
    except Exception:
        return url
