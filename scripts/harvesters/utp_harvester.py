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
    standardize_category
)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("UTPHarvester")

load_dotenv()

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

class UTPHarvester:
    def __init__(self):
        self.institution_slug = "utp"
        self.api_url = f"{SUPABASE_URL}/rest/v1"
        self.headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

    async def get_course_urls(self, page):
        return [
            "https://www.utp.edu.pe/pregrado/facultad-de-ingenieria/ingenieria-de-sistemas-e-informatica",
            "https://www.utp.edu.pe/pregrado/facultad-de-administracion-y-negocios/administracion-de-empresas",
            "https://www.utp.edu.pe/pregrado/facultad-de-ingenieria/ingenieria-industrial"
        ]

    async def scrape_course_detail(self, page, url):
        logger.info(f"Scraping UTP: {url}")
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(4)
            
            title_el = await page.query_selector(".title-carrera-hero h1")
            title = await title_el.inner_text() if title_el else await page.title()
            
            mode_el = await page.query_selector(".items-info-carrera .item-info:nth-child(1) span")
            mode = await mode_el.inner_text() if mode_el else "Presencial"
            
            duration_el = await page.query_selector(".items-info-carrera .item-info:nth-child(2) span")
            duration = await duration_el.inner_text() if duration_el else "10 ciclos"

            return {
                "name": clean_course_name(title),
                "url": url,
                "price_pen": None,
                "price_status": "consultar",
                "mode": mode if mode in ["Presencial", "Híbrido", "Remoto"] else "Presencial",
                "duration": duration,
                "category": standardize_category(title),
                "course_type": "Pregrado",
                "description_long": title,
                "institution_slug": self.institution_slug,
                "is_verified": True
            }
        except Exception as e:
            logger.error(f"Error scraping UTP: {e}")
            return None

    def save_to_db(self, item):
        if not item or not item.get('name'): return
        try:
            inst_url = f"{self.api_url}/institutions?slug=eq.{item['institution_slug']}"
            inst_res = requests.get(inst_url, headers=self.headers).json()
            if not inst_res: return
            inst_id = inst_res[0]['id']
            
            course_slug = item['name'].lower().replace(" ", "-").replace("/", "-")[:250]
            course_slug = re.sub(r'[^a-z0-9-]', '', course_slug).lstrip('-') or 'curso'

            course_data = {
                "institution_id": inst_id,
                "name": item['name'],
                "slug": course_slug,
                "url": item['url'],
                "price_status": item['price_status'],
                "mode": item['mode'],
                "duration": item.get('duration', ''),
                "category": item.get('category', 'General'),
                "course_type": item.get('course_type', 'Curso'),
                "is_active": True,
                "is_verified": item.get('is_verified', False),
                "last_scraped_at": datetime.now().isoformat()
            }
            res = requests.post(f"{self.api_url}/courses?on_conflict=institution_id,name,slug",
                                headers={**self.headers, "Prefer": "resolution=merge-duplicates"}, json=course_data)
            if res.status_code in [200, 201, 204]:
                logger.info(f"Saved UTP course: {item['name']}")
        except Exception as e:
            logger.error(f"DB Error UTP: {e}")

async def main():
    h = UTPHarvester()
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        page = await b.new_page()
        urls = await h.get_course_urls(page)
        for u in urls:
            d = await h.scrape_course_detail(page, u)
            if d: h.save_to_db(d)
        await b.close()

if __name__ == "__main__":
    asyncio.run(main())
