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
from shared.utils import infer_course_type, extract_pdf_text_from_url, clean_course_name, standardize_category

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("NewHorizonsHarvester")

load_dotenv()

# Configuration
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("NEXT_SUPABASE_PUBLISHABLE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

class NewHorizonsHarvester:
    def __init__(self):
        self.institution_slug = "new-horizons-peru"
        self.api_url = f"{SUPABASE_URL}/rest/v1"
        self.headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

    async def get_course_urls(self, page):
        """Extracts all course URLs from the main catalog"""
        catalog_url = "https://www.newhorizons.edu.pe/cursos-y-certificaciones-internacionales/ver-todas-las-especialidades"
        logger.info(f"Fetching catalog from {catalog_url}")
        try:
            await page.goto(catalog_url, wait_until="load", timeout=60000)
            await page.wait_for_timeout(5000)
        except Exception as e:
            logger.error(f"Error loading catalog: {e}")
            return []
            
        links = await page.query_selector_all('a[href^="/cursos-y-certificaciones-internacionales/"]')
        urls = []
        for link in links:
            href = await link.get_attribute("href")
            if href and "/especialidades" not in href and "/quienes-somos" not in href:
                if not href.startswith("http"):
                    href = f"https://www.newhorizons.edu.pe{href}"
                urls.append(href)
        
        unique_urls = list(set(urls))
        logger.info(f"Found {len(unique_urls)} unique course URLs.")
        return unique_urls

    async def scrape_course_detail(self, page, url):
        """Extracts detailed information from a course page"""
        logger.info(f"Scraping detail: {url}")
        try:
            await page.goto(url, wait_until="load", timeout=60000)
            
            name_elem = await page.query_selector("h1")
            name = (await name_elem.inner_text()).strip() if name_elem else "N/A"
            
            # Deep Scrape: Capture ALL visible text into description_long
            all_text_elements = await page.query_selector_all("p, li, .course-description, .entry-content, div[class*='text'], div[class*='content']")
            deep_scrape_text = []
            for el in all_text_elements:
                txt = (await el.inner_text()).strip()
                # Filter out navigation, footer, or very short noise
                if len(txt) > 20 and txt not in deep_scrape_text and "Â©" not in txt and "Todos los derechos" not in txt:
                    deep_scrape_text.append(txt)
            
            description_long = "\n\n".join(deep_scrape_text)

            # Helper to extract next sibling full text regardless of tags
            async def get_next_elements_text(header_text):
                return await page.evaluate(f'''(textToFind) => {{
                    const headers = Array.from(document.querySelectorAll('h2, h3, h4, h5, h6, strong, .title, .heading'));
                    const header = headers.find(el => el.innerText && el.innerText.trim().toLowerCase() === textToFind.toLowerCase() || (el.innerText && el.innerText.toLowerCase().includes(textToFind.toLowerCase()) && el.innerText.length < 60));
                    if (!header) return "";
                    
                    let content = "";
                    let next = header.nextElementSibling;
                    
                    if (!next && header.parentElement) {{
                        next = header.parentElement.nextElementSibling;
                    }}
                    if (!next && header.parentElement && header.parentElement.parentElement) {{
                        next = header.parentElement.parentElement.nextElementSibling;
                    }}

                    while (next) {{
                        if (["H1", "H2", "H3"].includes(next.tagName)) break;
                        if (next.tagName === "P" && next.querySelector("strong") && next.innerText.length < 50) break;
                        
                        if (next.innerText) content += next.innerText + "\\n";
                        next = next.nextElementSibling;
                    }}
                    return content.trim();
                }}''', header_text)

            objectives = await get_next_elements_text("aprenderÃ¡s") or await get_next_elements_text("aprender") or await get_next_elements_text("Objetivos")
            
            dirigido_a = await get_next_elements_text("Dirigido a")
            requisitos_str = await get_next_elements_text("Requisitos")
            
            target_audience = dirigido_a
            requirements = requisitos_str
            if requisitos_str and requisitos_str not in target_audience:
                target_audience += f"\n\nRequisitos:\n{requisitos_str}"
            syllabus = await get_next_elements_text("MÃ³dulos") or await get_next_elements_text("Temario")
            
            # Duration - Raw text as requested
            duration = await page.evaluate('''() => {
                const elems = document.querySelectorAll('*');
                for (let el of elems) {
                    if (el.innerText && /\\d+\\s*(horas|meses|semanas)/i.test(el.innerText) && el.innerText.length < 50) {
                        return el.innerText.trim();
                    }
                }
                return "";
            }''')

            # PDF Brochure - Aggressive search
            brochure_url = ""
            brochure_text = ""
            pdf_link_elem = await page.query_selector('a:has-text("Descargar folleto"), a:has-text("DESCARGAR BROCHURE"), a:has-text("Descargar brochure"), a[href$=".pdf"], a:has-text("Folleto")')
            if pdf_link_elem:
                href = await pdf_link_elem.get_attribute("href")
                if href:
                    if not href.startswith("http"):
                        href = f"https://www.newhorizons.edu.pe{href}"
                    brochure_url = href
                    # Use the utility to extract
                    brochure_text = extract_pdf_text_from_url(brochure_url)

            # CategorizaciÃ³n dinÃ¡mica granular
            parts = [p for p in url.split("/") if p]
            potential_cat = ""
            if len(parts) >= 2:
                cat_part = parts[-2]
                if cat_part.lower() not in ["ver-todas-las-especialidades", "cursos-y-certificaciones-internacionales"]:
                    potential_cat = cat_part
            
            category_extracted = standardize_category(potential_cat, name)
            subcategory_extracted = potential_cat.replace("-", " ").title() if potential_cat else ""

            # Limpiar nombre del curso
            clean_name = clean_course_name(name)

            return {
                "name": clean_name,
                "url": url,
                "institution_slug": self.institution_slug,
                "price_pen": 0,
                "price_status": "consultar",
                "mode": "Remoto",
                "address": "San Isidro, Lima",
                "category": category_extracted,
                "subcategory": subcategory_extracted,
                "course_type": infer_course_type(name),
                "brochure_url": brochure_url,
                "brochure_text": brochure_text,
                "syllabus": syllabus,
                "description_long": description_long,
                "objectives": objectives,
                "target_audience": target_audience,
                "requirements": requirements,
                "duration": duration
            }
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None

    def save_to_db(self, item):
        """Saves a single course to Supabase via REST API"""
        if not item: return
        
        try:
            # 1. Resolve/Ensure Institution (GET)
            inst_url = f"{self.api_url}/institutions?slug=eq.{item['institution_slug']}"
            inst_res = requests.get(inst_url, headers=self.headers).json()
            
            if not inst_res or len(inst_res) == 0:
                # POST if missing
                logger.info(f"Institution {item['institution_slug']} missing. Creating...")
                inst_res = requests.post(
                    f"{self.api_url}/institutions?select=id",
                    headers=self.headers,
                    json={"name": "New Horizons PerÃº", "slug": "new-horizons"}
                ).json()
                
                if isinstance(inst_res, dict) and "code" in inst_res:
                    logger.error(f"Error creating institution: {inst_res['message']}")
                    return
                inst_id = inst_res[0]['id']
            else:
                inst_id = inst_res[0]['id']
            
            # 2. Slug
            course_slug = item['name'].lower().replace(" ", "-").replace("/", "-")[:255]
            course_slug = re.sub(r'[^a-z0-9-]', '', course_slug).lstrip('-') or 'curso'

            # 3. UPSERT Course (POST with resolution=merge-duplicates)
            course_data = {
                "institution_id": inst_id,
                "name": item['name'],
                "slug": course_slug,
                "url": item['url'],
                "price_pen": item['price_pen'],
                "price_status": item['price_status'],
                "mode": item['mode'],
                "address": item['address'],
                "category": item.get('category', ''),
                "subcategory": item.get('subcategory', ''),
                "course_type": item.get('course_type', ''),
                "brochure_url": item.get('brochure_url', ''),
                "brochure_text": item.get('brochure_text', ''),
                "syllabus": item.get('syllabus', ''),
                "description_long": item.get('description_long', ''),
                "objectives": item.get('objectives', ''),
                "target_audience": item.get('target_audience', ''),
                "requirements": item.get('requirements', ''),
                "is_active": True,
                "start_date_text": item.get('start_date_text', ''),
                "last_scraped_at": datetime.now().isoformat()
            }
            
            upsert_headers = self.headers.copy()
            upsert_headers["Prefer"] = "resolution=merge-duplicates"
            
            # Use on_conflict parameter to specify the unique constraint fields
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
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("Missing credentials in .env")
        return

    harvester = NewHorizonsHarvester()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
        page = await context.new_page()
        
        urls = await harvester.get_course_urls(page)
        
        # 1. Soft-delete pre-scrape: Desactivamos todos los cursos vivos de esta instituciÃ³n
        try:
            logger.info("Initializing soft-delete protocol (deactivating old courses)...")
            # Obtenemos id
            inst_url = f"{harvester.api_url}/institutions?slug=eq.{harvester.institution_slug}"
            inst_res = requests.get(inst_url, headers=harvester.headers).json()
            if inst_res and len(inst_res) > 0:
                inst_id = inst_res[0]['id']
                requests.patch(
                    f"{harvester.api_url}/courses?institution_id=eq.{inst_id}",
                    headers=harvester.headers,
                    json={"is_active": False}
                )
                logger.info(f"Existing courses for institution {inst_id} deactivated. Active courses will be restored during scrape.")
        except Exception as e:
            logger.error(f"Error in soft-delete protocol: {e}")

        # 2. Process ALL discovered courses
        for url in urls:
            data = await harvester.scrape_course_detail(page, url)
            if data:
                harvester.save_to_db(data)
            await asyncio.sleep(1)
            
        await browser.close()
        logger.info("Harvest complete.")

if __name__ == "__main__":
    asyncio.run(main())
