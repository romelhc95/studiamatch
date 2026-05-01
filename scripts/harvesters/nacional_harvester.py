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
logger = logging.getLogger("NacionalHarvester")

load_dotenv()

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

class NacionalHarvester:
    def __init__(self):
        self.api_url = f"{SUPABASE_URL}/rest/v1"
        self.headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        self.targets = {
            "uni": [
                "https://www.uni.edu.pe/index.php/formacion-academica/facultades/facultad-de-ingenieria-industrial-y-de-sistemas-fiis",
                "https://www.uni.edu.pe/index.php/formacion-academica/facultades/facultad-de-ingenieria-mecanica-fim"
            ],
            "universidad-del-pacífico": [
                "https://www.up.edu.pe/carreras-postgrado-idiomas/carreras-pregrado/economia/",
                "https://www.up.edu.pe/carreras-postgrado-idiomas/carreras-pregrado/administracion/"
            ]
        }

    async def scrape_target(self, page, slug, url):
        logger.info(f"Scraping {slug}: {url}")
        try:
            # Bypass blockers for Uni
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(4)
            
            title = await page.title()
            if " - " in title: title = title.split(" - ")[0]
            if " | " in title: title = title.split(" | ")[0]
            
            # Special check for Pacífico selector
            if slug == "universidad-del-pacífico":
                h1_el = await page.query_selector("h1")
                if h1_el: title = await h1_el.inner_text()

            return {
                "name": clean_course_name(title),
                "url": url,
                "price_status": "consultar",
                "mode": "Presencial",
                "duration": "10 semestres",
                "category": standardize_category(title),
                "course_type": "Pregrado",
                "institution_slug": slug
            }
        except Exception as e:
            logger.error(f"Error {slug}: {e}")
            return None

    def save_to_db(self, item):
        if not item or not item.get('name') or "error" in item['name'].lower(): return
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
                "duration": item['duration'],
                "category": item['category'],
                "course_type": item['course_type'],
                "is_active": True,
                "last_scraped_at": datetime.now().isoformat()
            }
            requests.post(f"{self.api_url}/courses?on_conflict=institution_id,name,slug",
                         headers={**self.headers, "Prefer": "resolution=merge-duplicates"}, json=course_data)
            logger.info(f"Saved {item['institution_slug']} course: {item['name']}")
        except Exception as e:
            logger.error(f"DB Error: {e}")

async def main():
    h = NacionalHarvester()
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        page = await b.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        for slug, urls in h.targets.items():
            for u in urls:
                d = await h.scrape_target(page, slug, u)
                if d: h.save_to_db(d)
        await b.close()

if __name__ == "__main__":
    asyncio.run(main())
