import asyncio
import os
import json
import logging
import re
import sys
from datetime import datetime
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from playwright.async_api import async_playwright

# Add the parent directory to sys.path to import shared utilities
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.utils import (
    clean_course_name,
    extract_pdf_text_from_url,
    infer_course_type,
    standardize_category,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("UniversalHarvester")

load_dotenv()

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

class UniversalHarvester:
    def __init__(self, institution_data):
        self.institution = institution_data
        self.api_url = f"{SUPABASE_URL}/rest/v1"
        self.headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        self.visited_urls = set()
        self.course_urls = set()

    async def discover_courses(self, page):
        """
        Attempts to find course URLs by crawling or checking sitemaps.
        """
        start_url = self.institution.get('website_url')
        if not start_url:
            logger.error(f"No website URL for institution: {self.institution.get('name')}")
            return []

        logger.info(f"Starting discovery for {self.institution.get('name')} at {start_url}")
        
        # 1. Try common paths for education programs
        common_paths = [
            "/oferta-academica", "/cursos", "/diplomados", "/posgrado", 
            "/programas", "/educacion-continua", "/extension-universitaria"
        ]
        
        to_check = [start_url]
        for path in common_paths:
            to_check.append(urljoin(start_url, path))

        for url in to_check:
            try:
                logger.info(f"Checking {url}")
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(2)
                
                # Extract links that look like courses
                links = await page.query_selector_all("a")
                for link in links:
                    href = await link.get_attribute("href")
                    if not href: continue
                    
                    full_url = urljoin(url, href)
                    if self._is_potential_course_url(full_url):
                        self.course_urls.add(full_url)
                
                if len(self.course_urls) > 50: # Limit discovery for a single run
                    break
            except Exception as e:
                logger.warning(f"Failed to check {url}: {e}")

        logger.info(f"Discovery found {len(self.course_urls)} potential course URLs.")
        return list(self.course_urls)

    def _is_potential_course_url(self, url):
        """Heuristic to identify course detail pages."""
        # Must be same domain
        base_domain = urlparse(self.institution.get('website_url')).netloc
        if urlparse(url).netloc != base_domain:
            return False
            
        # Avoid assets
        if any(url.endswith(ext) for ext in ['.pdf', '.jpg', '.png', '.zip', '.doc']):
            return False
            
        # Keywords in URL
        keywords = ["curso", "diplomado", "maestria", "doctorado", "programa", "especializacion"]
        return any(k in url.lower() for k in keywords)

    async def scrape_course_detail(self, page, url):
        """
        Generic scraping logic using OpenGraph, JSON-LD, and HTML heuristics.
        """
        logger.info(f"Scraping {url}")
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            await asyncio.sleep(3) # Wait for potential JS rendering

            # 1. Extract JSON-LD (Schema.org)
            course_data = await self._extract_json_ld(page)
            
            # 2. Extract OpenGraph Tags
            og_data = await self._extract_og_tags(page)
            
            # 3. HTML Heuristics
            title = await self._extract_title(page, og_data, course_data)
            description = await self._extract_description(page, og_data, course_data)
            
            if not self._is_valid_title(title):
                logger.warning(f"Invalid title detected for {url}: {title}")
                return None

            # Get duration, price, mode if possible
            duration = await self._find_text_pattern(page, [r"\d+\s*ciclos", r"\d+\s*semestres", r"\d+\s*años", r"duración"])
            mode = await self._detect_mode(page)
            price_text = await self._find_text_pattern(page, [r"inversión", r"precio", r"costo", r"s/."])
            
            price_pen = None
            price_status = "consultar"
            if price_text:
                price_match = re.search(r'S/\s*([\d,.]+)', price_text, re.IGNORECASE)
                if price_match:
                    try:
                        price_pen = float(price_match.group(1).replace(",", ""))
                        price_status = "publicado"
                    except: pass

            # Syllabus search (looking for common headers)
            syllabus = await self._extract_section(page, ["temario", "contenido", "módulos", "plan de estudios"])
            target_audience = await self._extract_section(page, ["dirigido a", "público"])

            return {
                "name": clean_course_name(title),
                "url": url,
                "price_pen": price_pen,
                "price_status": price_status,
                "mode": mode,
                "duration": duration[:100] if duration else "10 ciclos",
                "category": standardize_category(title),
                "course_type": infer_course_type(title),
                "description_long": description,
                "target_audience": target_audience,
                "syllabus": syllabus,
                "institution_slug": self.institution.get('slug')
            }
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None

    async def _extract_json_ld(self, page):
        scripts = await page.query_selector_all('script[type="application/ld+json"]')
        for script in scripts:
            try:
                content = await script.inner_text()
                data = json.loads(content)
                if isinstance(data, list):
                    for item in data:
                        if item.get("@type") in ["Course", "EducationalOccupationalProgram"]:
                            return item
                elif data.get("@type") in ["Course", "EducationalOccupationalProgram"]:
                    return data
            except: continue
        return {}

    async def _extract_og_tags(self, page):
        og_data = {}
        metas = await page.query_selector_all('meta[property^="og:"]')
        for meta in metas:
            prop = await meta.get_attribute("property")
            content = await meta.get_attribute("content")
            if prop and content:
                og_data[prop.replace("og:", "")] = content
        return og_data

    def _is_valid_title(self, title):
        if not title or len(title) < 5:
            return False
            
        blacklist = [
            "página no encontrada", "pagina no encontrada", "404", "error", 
            "blocked", "discover", "descubre", "nuestras carreras", 
            "sorry", "has sido bloqueado", "explora", "portal utp",
            "carrera upc", "carrera usil", "carrera utp"
        ]
        
        low_title = title.lower()
        if any(b in low_title for b in blacklist):
            return False
            
        # If it's just a single generic word usually it's a category
        if len(title.split()) < 2 and len(title) < 15:
            return False
            
        return True

    async def _extract_title(self, page, og, schema):
        # Priority: Schema > OG > Specific Hero Classes > Page Title > H1
        title = schema.get("name") or og.get("title")
        
        if not title:
            # Common hero classes found in Peruvian unis
            hero_selectors = [".title-carrera-hero h1", ".banner-principal h1", ".hero-title", ".career-title h1"]
            for sel in hero_selectors:
                el = await page.query_selector(sel)
                if el:
                    title = await el.inner_text()
                    break
        
        if not title:
            title = await page.title()
            if " | " in title: title = title.split(" | ")[0]
            if " - " in title: title = title.split(" - ")[0]
        
        if not title or len(title) < 5:
            h1s = await page.query_selector_all("h1")
            for h1 in h1s:
                t = await h1.inner_text()
                if len(t.strip()) > 5:
                    title = t
                    break
            
        return title.strip() if title else ""

    async def _detect_mode(self, page):
        """Detects if the course is Presencial, Híbrido or Remoto."""
        content = (await page.inner_text("body")).lower()
        if "semipresencial" in content or "híbrido" in content or "hibrido" in content:
            return "Híbrido"
        if "remoto" in content or "virtual" in content or "a distancia" in content:
            return "Remoto"
        return "Presencial"

    async def _extract_description(self, page, og, schema):
        desc = schema.get("description") or og.get("description")
        if not desc:
            # Get the first few paragraphs
            paragraphs = await page.query_selector_all("p")
            texts = []
            for p in paragraphs[:5]:
                t = await p.inner_text()
                if len(t.strip()) > 50:
                    texts.append(t.strip())
            desc = "\n\n".join(texts)
        return desc.strip() if desc else ""

    async def _find_text_pattern(self, page, patterns):
        body_text = await page.inner_text("body")
        lines = body_text.split("\n")
        for line in lines:
            if any(re.search(p, line, re.IGNORECASE) for p in patterns):
                if len(line.strip()) < 100:
                    return line.strip()
        return ""

    async def _extract_section(self, page, keywords):
        # Find headers that match keywords
        headers = await page.query_selector_all("h2, h3, h4, strong")
        for h in headers:
            text = (await h.inner_text()).lower()
            if any(k in text for k in keywords):
                # Try to get the next sibling or parent's next sibling content
                content = await h.evaluate("""el => {
                    let next = el.nextElementSibling;
                    if (!next) next = el.parentElement.nextElementSibling;
                    return next ? next.innerText : '';
                }""")
                if len(content) > 20:
                    return content.strip()
        return ""

    def save_to_db(self, item):
        if not item or not item.get('name'): return
        
        try:
            inst_id = self.institution.get('id')
            
            import unicodedata
            def slugify(text):
                text = unicodedata.normalize('NFD', text)
                text = text.encode('ascii', 'ignore').decode('utf-8')
                text = text.lower()
                text = re.sub(r'[^a-z0-9-]', '-', text)
                text = re.sub(r'-+', '-', text)
                return text.strip('-')

            course_slug = slugify(item['name'])[:250]

            course_data = {
                "institution_id": inst_id,
                "name": item['name'],
                "slug": course_slug,
                "url": item['url'],
                "price_pen": item['price_pen'],
                "price_status": item['price_status'],
                "mode": item['mode'],
                "duration": item.get('duration', ''),
                "category": item.get('category', 'General'),
                "course_type": item.get('course_type', 'Curso'),
                "description_long": item.get('description_long', ''),
                "target_audience": item.get('target_audience', ''),
                "syllabus": item.get('syllabus', ''),
                "is_active": True,
                "last_scraped_at": datetime.now().isoformat()
            }
            
            upsert_headers = self.headers.copy()
            upsert_headers["Prefer"] = "resolution=merge-duplicates"
            
            res = requests.post(
                f"{self.api_url}/courses?on_conflict=institution_id,name,slug",
                headers=upsert_headers,
                json=course_data
            )
            
            if res.status_code in [201, 204, 200]:
                logger.info(f"Saved: {item['name']}")
            else:
                logger.error(f"Error saving {item['name']}: {res.text}")
                
        except Exception as e:
            logger.error(f"Processing error for {item['name']}: {e}")


async def main():
    if len(sys.argv) < 2:
        logger.error("No institution JSON provided.")
        return

    try:
        inst_data = json.loads(sys.argv[1])
    except Exception as e:
        logger.error(f"Error parsing institution data: {e}")
        return

    harvester = UniversalHarvester(inst_data)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()
        
        urls = await harvester.discover_courses(page)
        
        # Limit to 5 for universal harvester to avoid broad crawling in a single pass
        # unless configured otherwise.
        urls = urls[:10] 

        for url in urls:
            data = await harvester.scrape_course_detail(page, url)
            if data:
                harvester.save_to_db(data)
            await asyncio.sleep(2) 
            
        await browser.close()
        logger.info(f"Harvest complete for {inst_data.get('name')}.")

if __name__ == "__main__":
    asyncio.run(main())
