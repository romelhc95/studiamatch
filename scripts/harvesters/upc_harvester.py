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
logger = logging.getLogger("UPCHarvester")

load_dotenv()

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("NEXT_SUPABASE_PUBLISHABLE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

class UPCHarvester:
    def __init__(self):
        self.institution_slug = "upc"
        self.api_url = f"{SUPABASE_URL}/rest/v1"
        self.headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

    async def get_course_urls(self, page):
        return [
            "https://pregrado.upc.edu.pe/facultad-de-ingenieria/ingenieria-de-sistemas-de-informacion/",
            "https://pregrado.upc.edu.pe/facultad-de-negocios/administracion-de-empresas/",
            "https://pregrado.upc.edu.pe/facultad-de-negocios/marketing/"
        ]

    async def scrape_course_detail(self, page, url):
        logger.info(f"Scraping UPC: {url}")
        try:
            # Use a more resilient timeout and wait condition
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(4)
            
            # Subagent findings: h1 is the title
            title_el = await page.query_selector("h1")
            title = await title_el.inner_text() if title_el else "Carrera UPC"
            
            # Clean generic parts
            title = title.replace("Carrera de ", "").strip()
            
            return {
                "name": clean_course_name(title),
                "url": url,
                "price_pen": None,
                "price_status": "consultar",
                "mode": "Presencial",
                "duration": "10 semestres",
                "category": standardize_category(title),
                "course_type": "Pregrado",
                "description_long": title,
                "institution_slug": self.institution_slug,
                "is_verified": True
            }
        except Exception as e:
            logger.error(f"Error scraping UPC: {e}")
            return None

    def save_to_db(self, item):
        if not item or not item.get('name') or item['name'] == "Carrera UPC": return
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
                logger.info(f"Saved UPC course: {item['name']}")
        except Exception as e:
            logger.error(f"DB Error UPC: {e}")

async def main():
    h = UPCHarvester()
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        # Use a mobile user agent or newer chrome to bypass some blocks
        page = await b.new_page(user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        urls = await h.get_course_urls(page)
        for u in urls:
            d = await h.scrape_course_detail(page, u)
            if d: h.save_to_db(d)
        await b.close()

if __name__ == "__main__":
    asyncio.run(main())
