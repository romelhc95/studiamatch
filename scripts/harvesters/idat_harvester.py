import asyncio
from playwright.async_api import async_playwright
import os
import logging
import requests
from datetime import datetime
from dotenv import load_dotenv
import sys
import re

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.utils import (
    clean_course_name,
    infer_course_type,
    standardize_category
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("IDATHarvester")

load_dotenv()

# Configuration
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("NEXT_SUPABASE_PUBLISHABLE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

class IDATHarvester:
    def __init__(self):
        self.institution_slug = "idat"
        self.api_url = f"{SUPABASE_URL}/rest/v1"
        self.headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

    async def get_course_urls(self, page):
        """Discovers course URLs for IDAT"""
        urls = [
            "https://www.idat.edu.pe/cursos-de-formacion-continua/sql",
            "https://www.idat.edu.pe/cursos-de-formacion-continua/data-analytics-i",
            "https://www.idat.edu.pe/cursos-de-formacion-continua/power-bi-avanzado",
            "https://www.idat.edu.pe/programas-especializacion/seguridad-informatica-y-ciberseguridad",
            "https://www.idat.edu.pe/carreras-profesionales-tecnicas/recursos-humanos",
            "https://www.idat.edu.pe/cursos-de-formacion-continua/creacion-de-contenido-en-tik-tok",
            "https://www.idat.edu.pe/cursos-de-formacion-continua/people-analytics-con-power-bi",
            "https://www.idat.edu.pe/cursos-de-formacion-continua/creacion-y-edicion-de-videos-con-ia",
            "https://www.idat.edu.pe/cursos-de-formacion-continua/diseno-en-autocad"
        ]
        return urls

    def _is_valid_title(self, title):
        blacklist = ["diplomados", "cursos", "carreras", "descubre", "error", "404"]
        if not title or len(title) < 5: return False
        if any(b in title.lower() for b in blacklist) and len(title.split()) < 3:
            return False
        return True

    async def scrape_course_detail(self, page, url):
        """Extracts detailed information from an IDAT course page"""
        logger.info(f"Scraping detail: {url}")
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(3)

            # Heuristics for IDAT
            title_el = await page.query_selector("h1")
            title = await title_el.inner_text() if title_el else await page.title()
            
            if " | " in title: title = title.split(" | ")[0]
            
            if not self._is_valid_title(title):
                logger.warning(f"Invalid title skipped: {title}")
                return None

            # Extract content
            description_elements = await page.query_selector_all("p")
            description_text = []
            for el in description_elements:
                txt = (await el.inner_text()).strip()
                if len(txt) > 30:
                    description_text.append(txt)
            
            description_long = "\n\n".join(description_text[:5])

            return {
                "name": clean_course_name(title),
                "url": url,
                "price_pen": None,
                "price_status": "consultar",
                "mode": "Remoto",
                "duration": "A consultar",
                "category": standardize_category(title),
                "course_type": infer_course_type(title),
                "description_long": description_long,
                "target_audience": "",
                "syllabus": "",
                "institution_slug": self.institution_slug,
                "is_verified": True # Confirmed selectors
            }
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None

    def save_to_db(self, item):
        if not item or not item.get('name'): return
        
        try:
            # Resolve Institution
            inst_url = f"{self.api_url}/institutions?slug=eq.{item['institution_slug']}"
            inst_res = requests.get(inst_url, headers=self.headers).json()
            
            if not inst_res:
                logger.error(f"Institution {item['institution_slug']} not found.")
                return
            
            inst_id = inst_res[0]['id']
            
            course_slug = item['name'].lower().replace(" ", "-").replace("/", "-")[:250]
            course_slug = re.sub(r'[^a-z0-9-]', '', course_slug).lstrip('-') or 'curso'

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
                "is_active": True,
                "is_verified": item.get('is_verified', False),
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
                logger.info(f"Saved/Updated: {item['name']}")
            else:
                logger.error(f"Error saving {item['name']}: {res.text}")
                
        except Exception as e:
            logger.error(f"Processing error for {item['name']}: {e}")

async def main():
    harvester = IDATHarvester()
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        urls = await harvester.get_course_urls(page)
        
        for url in urls:
            data = await harvester.scrape_course_detail(page, url)
            if data:
                harvester.save_to_db(data)
            await asyncio.sleep(1)
            
        await browser.close()
        logger.info("IDAT Harvest complete.")

if __name__ == "__main__":
    asyncio.run(main())
