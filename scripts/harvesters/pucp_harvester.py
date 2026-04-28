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
from shared.utils import infer_course_type, clean_course_name, standardize_category, extract_pdf_text_from_url

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("PUCPHarvester")

load_dotenv()

# Configuration
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

class PUCPHarvester:
    def __init__(self):
        self.institution_slug = "pucp"
        self.api_url = f"{SUPABASE_URL}/rest/v1"
        self.headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

    async def get_all_course_urls(self, page):
        """Iterates through all 13 pages of the PUCP catalog to find every URL"""
        all_urls = []
        base_url = "https://educacioncontinua.pucp.edu.pe/oferta-academica/"
        
        for page_num in range(1, 14):
            url = f"{base_url}?jsf=jet-engine&pagenum={page_num}"
            logger.info(f"Fetching page {page_num}: {url}")
            try:
                await page.goto(url, wait_until="load", timeout=60000)
                await asyncio.sleep(3) # Wait for AJAX items to settle
                
                links = await page.query_selector_all('a.jet-listing-dynamic-image__link')
                page_urls = []
                for link in links:
                    href = await link.get_attribute("href")
                    if href:
                        page_urls.append(href)
                
                logger.info(f"Page {page_num} found {len(page_urls)} courses.")
                all_urls.extend(page_urls)
            except Exception as e:
                logger.error(f"Error loading page {page_num}: {e}")
        
        unique_urls = list(set(all_urls))
        logger.info(f"Total discovery: Found {len(unique_urls)} unique course URLs across all pages.")
        return unique_urls

    async def scrape_course_detail(self, page, url):
        """Extracts detailed information from a PUCP course page using JetEngine fields"""
        logger.info(f"Scraping detail: {url}")
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=90000)
            await asyncio.sleep(4) # Wait for JetEngine fields to render

            # Capture ALL visible text into description_long as a baseline for "Deep Scrape"
            # We filter out very short strings and noise
            all_text_elements = await page.query_selector_all("p, li, div.jet-listing-dynamic-field__content, .elementor-widget-container")
            deep_scrape_text = []
            for el in all_text_elements:
                txt = (await el.inner_text()).strip()
                if len(txt) > 20 and txt not in deep_scrape_text:
                    deep_scrape_text.append(txt)
            
            description_long = "\n\n".join(deep_scrape_text)

            # Extract all dynamic fields for specific metadata
            fields = await page.query_selector_all(".jet-listing-dynamic-field")
            field_texts = []
            for f in fields:
                field_texts.append((await f.inner_text()).strip())
            
            if not field_texts:
                logger.error(f"No fields found for {url}")
                return None

            name_text = ""
            category = "General"
            duration = ""
            price_pen = None
            price_status = "consultar"
            objectives = ""
            target_audience = ""
            syllabus = ""

            for text in field_texts:
                if not name_text and len(text) > 10 and ("Curso" in text or "Diplomado" in text or "Especialización" in text):
                    name_text = text
                
                if "Duración:" in text:
                    duration = text.replace("Duración:", "").strip()
                
                if "Inversión:" in text:
                    price_match = re.search(r'S/\s*([\d,.]+)', text)
                    if price_match:
                        try:
                            price_pen = float(price_match.group(1).replace(",", ""))
                            price_status = "publicado"
                        except Exception: pass
                
                if "¿Por qué estudiar este curso?" in text or "¿Por qué seguir este programa?" in text:
                    objectives = text
            
            # If name still empty, take the first long field or page title
            if not name_text and len(field_texts) > 0:
                name_text = field_texts[0]
            
            if not name_text:
                page_title = await page.title()
                name_text = page_title.split(" - ")[0]

            # Specific content extraction using headings
            h3s = await page.query_selector_all("h3, h2")
            for h3 in h3s:
                header = (await h3.inner_text()).strip()
                content = await h3.evaluate("el => el.nextElementSibling ? el.nextElementSibling.innerText : ''")
                
                if "Dirigido a" in header:
                    target_audience = content
                elif "Contenidos" in header or "Plan de estudios" in header or "Temario" in header:
                    syllabus = content

            # Aggressive PDF brochure search
            brochure_url = ""
            brochure_text = ""
            pdf_links = await page.query_selector_all('a[href$=".pdf"], a:has-text("Brochure"), a:has-text("Folleto"), a:has-text("Descargar")')
            for link in pdf_links:
                href = await link.get_attribute("href")
                if href and ".pdf" in href.lower():
                    if not href.startswith("http"):
                        href = f"https://educacioncontinua.pucp.edu.pe{href}"
                    brochure_url = href
                    logger.info(f"Found PDF brochure: {brochure_url}")
                    brochure_text = extract_pdf_text_from_url(brochure_url)
                    break # Take the first relevant PDF

            return {
                "name": clean_course_name(name_text),
                "url": url,
                "price_pen": price_pen,
                "price_status": price_status,
                "mode": "Remoto", # Default for PUCP continuous ed if not specified
                "duration": duration,
                "category": standardize_category(field_texts[1] if len(field_texts) > 1 else "General"),
                "course_type": infer_course_type(name_text),
                "description_long": description_long,
                "target_audience": target_audience,
                "syllabus": syllabus,
                "brochure_url": brochure_url,
                "brochure_text": brochure_text,
                "institution_slug": self.institution_slug
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
            
            if not inst_res or len(inst_res) == 0:
                inst_res = requests.post(
                    f"{self.api_url}/institutions?select=id",
                    headers=self.headers,
                    json={"name": "PUCP", "slug": "pucp", "website_url": "https://www.pucp.edu.pe/"}
                ).json()
                inst_id = inst_res[0]['id']
            else:
                inst_id = inst_res[0]['id']
            
            course_slug = item['name'].lower().replace(" ", "-").replace("/", "-")[:250]
            course_slug = re.sub(r'[^a-z0-9-]', '', course_slug)

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
                "brochure_url": item.get('brochure_url', ''),
                "brochure_text": item.get('brochure_text', ''),
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
    harvester = PUCPHarvester()
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Slower context for better bypass of potential minor bot challenges or just stability
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()
        
        urls = await harvester.get_all_course_urls(page)
        
        # Limit for safety in this session triaje, but ready for all 150+
        # urls = urls[:20] 

        for url in urls:
            data = await harvester.scrape_course_detail(page, url)
            if data:
                harvester.save_to_db(data)
            await asyncio.sleep(2) # Humanitarian delay
            
        await browser.close()
        logger.info("PUCP Mass Harvest complete.")

if __name__ == "__main__":
    asyncio.run(main())
