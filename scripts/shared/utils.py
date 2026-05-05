import re
import unicodedata
import random
import logging
import signal
import time
import sys
import os
from datetime import datetime, timezone, timedelta


class TimeGuard:
    """
    Reusable graceful shutdown guard for long-running pipeline scripts.
    Sets a flag on SIGTERM/SIGINT so the main loop can finish its current
    iteration before exiting.  Also enforces a wall-clock maximum runtime.

    Usage:
        guard = TimeGuard(max_seconds=20400)   # 5h 40m
        while records and not guard.should_exit:
            ...
            guard.tick()   # optional: log progress every N calls
    """

    def __init__(self, max_seconds=None, logger=None):
        self.max_seconds = max_seconds or int(os.getenv("TIME_GUARD_SECONDS", "20400"))
        self._start = time.time()
        self._shutdown_requested = False
        self._logger = logger or logging.getLogger("TimeGuard")
        self._tick_count = 0
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

    def _handle_signal(self, signum, frame):
        sig_name = signal.Signals(signum).name
        self._logger.warning(f"[TIME_GUARD] Received {sig_name}. Setting shutdown flag...")
        self._shutdown_requested = True

    @property
    def should_exit(self):
        if self._shutdown_requested:
            return True
        elapsed = time.time() - self._start
        if elapsed > self.max_seconds:
            self._logger.warning(
                f"[TIME_GUARD] Max runtime reached ({elapsed/3600:.2f}h / {self.max_seconds/3600:.2f}h). Graceful exit."
            )
            return True
        return False

    @property
    def elapsed_hours(self):
        return (time.time() - self._start) / 3600

    def tick(self, every=100):
        self._tick_count += 1
        if self._tick_count % every == 0:
            elapsed = time.time() - self._start
            remaining = max(0, self.max_seconds - elapsed)
            self._logger.info(
                f"[TIME_GUARD] Tick {self._tick_count} | Elapsed: {elapsed/3600:.2f}h | Remaining: {remaining/3600:.2f}h"
            )

class LimaFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        # Convert to Lima Time (UTC-5)
        lima_tz = timezone(timedelta(hours=-5))
        dt = datetime.fromtimestamp(record.created, tz=lima_tz)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.isoformat()

def setup_lima_logging(name: str):
    """Configures a logger with Lima Time formatting and UTF-8 encoding."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
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
    key = os.getenv("NEXT_SUPABASE_PUBLISHABLE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

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


def parse_start_date(text):
    """
    Parses a Spanish/English start date string into a datetime.date.
    Returns (date, is_expired) tuple or (None, False) if unparseable.
    
    Handles: "Abril 2026", "15 de mayo", "2026-04-15", "Marzo 2024", "15/05/2026"
    Grace period: 90 days past the start date before marking as expired.
    """
    if not text or str(text).strip().lower() in ('none', 'null', 'nan', ''):
        return None, False
    
    from datetime import date, timedelta
    text = str(text).strip()
    
    # Try ISO format first: 2026-04-15 or 2026/04/15
    iso_match = re.match(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', text)
    if iso_match:
        try:
            d = date(int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3)))
            expired = d < date.today() - timedelta(days=90)
            return d, expired
        except ValueError:
            pass
    
    # Try DD/MM/YYYY
    dmy_match = re.match(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', text)
    if dmy_match:
        try:
            d = date(int(dmy_match.group(3)), int(dmy_match.group(2)), int(dmy_match.group(1)))
            expired = d < date.today() - timedelta(days=90)
            return d, expired
        except ValueError:
            pass
    
    # Spanish month names
    months = {
        'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
        'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
        'septiembre': 9, 'setiembre': 9, 'octubre': 10,
        'noviembre': 11, 'diciembre': 12,
        'january': 1, 'february': 2, 'march': 3, 'april': 4,
        'may': 5, 'june': 6, 'july': 7, 'august': 8,
        'september': 9, 'october': 10, 'november': 11, 'december': 12,
    }
    
    text_lower = text.lower()
    
    # Pattern: "Mes AAAA" or "Mes de AAAA" e.g. "Abril 2026", "Marzo de 2024"
    month_year = re.match(r'([a-záéíóúñ]+)\s+(?:de\s+)?(\d{4})', text_lower)
    if month_year:
        month_name = month_year.group(1)
        year_val = int(month_year.group(2))
        if month_name in months:
            d = date(year_val, months[month_name], 1)
            expired = d < date.today() - timedelta(days=90)
            return d, expired
    
    # Pattern: "DD de Mes" or "DD Mes" e.g. "15 de mayo", "15 mayo"
    # Use current year as default
    day_month = re.match(r'(\d{1,2})\s+(?:de\s+)?([a-záéíóúñ]+)', text_lower)
    if day_month:
        month_name = day_month.group(2)
        if month_name in months:
            current_year = date.today().year
            try:
                d = date(current_year, months[month_name], int(day_month.group(1)))
                # If this date is already past for current year, try next year
                if d < date.today() - timedelta(days=90):
                    d = date(current_year + 1, months[month_name], int(day_month.group(1)))
                expired = d < date.today() - timedelta(days=90)
                return d, expired
            except ValueError:
                pass
    
    # Pattern: "DD de Mes de AAAA" e.g. "15 de mayo de 2026"
    full_date = re.match(r'(\d{1,2})\s+(?:de\s+)?([a-záéíóúñ]+)\s+(?:de\s+)?(\d{4})', text_lower)
    if full_date:
        month_name = full_date.group(2)
        if month_name in months:
            try:
                d = date(int(full_date.group(3)), months[month_name], int(full_date.group(1)))
                expired = d < date.today() - timedelta(days=90)
                return d, expired
            except ValueError:
                pass
    
    return None, False


try:
    from json_repair import repair_json as _jsonrepair_repair
    _JSONREPAIR_AVAILABLE = True
except ImportError:
    _JSONREPAIR_AVAILABLE = False


class LLMProvider:
    """Wraps a single LLM provider with health-check and success/fail tracking."""

    def __init__(self, name, call_fn, health_fn=None):
        self.name = name
        self.call_fn = call_fn
        self.health_fn = health_fn
        self.success_count = 0
        self.fail_count = 0
        self.repair_count = 0
        self._healthy = None

    def health_check(self):
        """Ping the provider with a trivial prompt. Returns True if it responds with valid JSON."""
        if self.health_fn:
            try:
                result = self.health_fn()
                self._healthy = bool(result)
            except Exception:
                self._healthy = False
            return self._healthy
        try:
            raw = self.call_fn('Responde SOLO este JSON: {"status": "ok"}')
            if raw:
                import json as _json
                clean = re.sub(r'```json\s*', '', raw)
                clean = re.sub(r'```\s*', '', clean)
                match = re.search(r'\{.*\}', clean, re.DOTALL)
                if match:
                    _json.loads(match.group())
                    self._healthy = True
                    return True
        except Exception:
            pass
        self._healthy = False
        return False

    @property
    def is_healthy(self):
        if self._healthy is None:
            self.health_check()
        return self._healthy

    @property
    def is_degraded(self):
        total = self.success_count + self.fail_count
        if total < 5:
            return False
        return self.fail_rate > 0.8

    @property
    def fail_rate(self):
        total = self.success_count + self.fail_count
        if total == 0:
            return 0.0
        return self.fail_count / total

    def record_success(self):
        self.success_count += 1

    def record_fail(self):
        self.fail_count += 1

    def record_repair(self):
        self.repair_count += 1

    def __repr__(self):
        total = self.success_count + self.fail_count
        return f"LLMProvider({self.name}, healthy={self._healthy}, {self.success_count}/{total})"


class ProviderOrchestrator:
    """Orchestrates multiple LLM providers with health checks, jsonrepair fallback, and dynamic degradation."""

    def __init__(self, providers, logger=None):
        self.providers = list(providers)
        self.logger = logger or logging.getLogger("ProviderOrchestrator")
        self._active_order = list(providers)

    def run_health_checks(self):
        """Run health_check() on every provider and build the active order."""
        results = {}
        healthy = []
        unhealthy = []
        for p in self.providers:
            ok = p.health_check()
            results[p.name] = ok
            if ok:
                healthy.append(p)
            else:
                unhealthy.append(p)
        status_parts = [f"{name}={'✅' if ok else '❌'}" for name, ok in results.items()]
        self.logger.info(f"Health check: {', '.join(status_parts)}")
        self._active_order = healthy + unhealthy
        return [p.name for p in healthy]

    def get_active_providers(self):
        """Return providers in priority order, pushing degraded ones to the end."""
        normal = [p for p in self._active_order if not p.is_degraded]
        degraded = [p for p in self._active_order if p.is_degraded]
        if degraded:
            degraded_names = [p.name for p in degraded]
            self.logger.info(f"Degraded providers moved to end: {', '.join(degraded_names)}")
        return normal + degraded

    def call_with_fallback(self, prompt, clean_fn):
        """Iterate active providers, apply clean_fn, try jsonrepair on failure.
        Returns (parsed_dict, provider_name) on success, or (None, None) if all fail."""
        import json as _json
        active = self.get_active_providers()
        for provider in active:
            try:
                t0 = time.time()
                raw = provider.call_fn(prompt)
                elapsed_ms = int((time.time() - t0) * 1000)
                cleaned = clean_fn(raw) if raw else None
                if cleaned:
                    try:
                        result = _json.loads(cleaned)
                        provider.record_success()
                        self.logger.info(f"Provider {provider.name} success ({elapsed_ms}ms)")
                        return result, provider.name
                    except (_json.JSONDecodeError, ValueError):
                        repaired = self._try_jsonrepair(cleaned)
                        if repaired is not None:
                            provider.record_success()
                            provider.record_repair()
                            self.logger.info(f"JSON reparado vía jsonrepair para {provider.name} ({elapsed_ms}ms)")
                            return repaired, provider.name
                        provider.record_fail()
                        self.logger.warning(f"JSON inválido de {provider.name} ({elapsed_ms}ms, jsonrepair tampoco pudo reparar)")
                else:
                    provider.record_fail()
                    self.logger.warning(f"Provider {provider.name} returned None ({elapsed_ms}ms)")
            except Exception as e:
                provider.record_fail()
                self.logger.warning(f"Fallo con {provider.name}: {e}")
        # All providers failed — check for early-exit
        if self._all_degraded():
            self.logger.warning("TODOS los proveedores están degradados. Activando early-exit.")
        return None, None

    def _all_degraded(self):
        """Returns True if all providers have fail_rate > 0.8 after 5+ calls each."""
        if len(self.providers) == 0:
            return True
        return all(p.is_degraded for p in self.providers)

    def _try_jsonrepair(self, text):
        """Attempt jsonrepair if available, return parsed dict or None."""
        if not _JSONREPAIR_AVAILABLE:
            self.logger.warning("jsonrepair no instalado — instalá con pip install jsonrepair para reparación automática de JSON")
            return None
        try:
            import json as _json
            repaired_text = _jsonrepair_repair(text)
            return _json.loads(repaired_text)
        except Exception:
            return None

    def summary(self):
        """Return a human-readable summary of provider metrics."""
        lines = []
        for p in self.providers:
            total = p.success_count + p.fail_count
            if total > 0:
                pct = p.success_count / total * 100
                repair_info = f", jsonrepair: {p.repair_count}" if p.repair_count > 0 else ""
                lines.append(f"{p.name}: {p.success_count}/{total} ({pct:.0f}%){repair_info}")
            else:
                lines.append(f"{p.name}: sin llamadas")
        return " | ".join(lines)
