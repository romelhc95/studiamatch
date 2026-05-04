import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os
import logging
import requests
from datetime import datetime
from dotenv import load_dotenv
import sys
import re

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.utils import infer_course_type, extract_pdf_text_from_url, clean_course_name, standardize_category, standardize_mode

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SmartDataHarvester")

load_dotenv()

# Configuration
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("NEXT_SUPABASE_PUBLISHABLE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

class SmartDataHarvester:
    def __init__(self):
        self.institution_slug = "smartdata"
        self.institution_name = "SmartData"
        self.api_url = f"{SUPABASE_URL}/rest/v1"
        self.headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

    async def apply_stealth(self, page):
        await Stealth().apply_stealth_async(page)
        await page.set_extra_http_headers({
            "Accept-Language": "es-ES,es;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "DNT": "1",
            "Upgrade-Insecure-Requests": "1"
        })

    async def get_course_urls(self, page):
        """Extracts all course URLs from SmartData catalogs with scroll support"""
        
        # Warm up session by visiting root
        try:
            logger.info("Warming up session at root...")
            await page.goto("https://smartdata.com.pe/", wait_until="load", timeout=60000)
            await asyncio.sleep(5)
            # Human-like interaction
            await page.mouse.move(500, 500)
            await page.mouse.wheel(0, 300)
            await asyncio.sleep(2)
        except Exception as e:
            logger.warning(f"Root warm-up failed: {e}")

        catalog_urls = [
            "https://smartdata.com.pe/programas-de-especializacion/",
            "https://smartdata.com.pe/cursos/"
        ]
        
        all_urls = []
        for catalog_url in catalog_urls:
            logger.info(f"Fetching catalog from {catalog_url}")
            try:
                # Increased timeout and wait for Cloudflare
                await page.goto(catalog_url, wait_until="load", timeout=120000)
                
                # Robust Cloudflare wait (up to 60s)
                for i in range(12):
                    title = await page.title()
                    if any(x in title for x in ["Just a moment", "Cloudflare", "Un momento"]):
                        logger.info(f"Cloudflare challenge detected (Title: {title}). Waiting 10s ({i+1}/12)...")
                        # Move mouse to simulate activity
                        await page.mouse.move(100 * (i % 5), 100 * (i % 5))
                        await asyncio.sleep(10)
                    else:
                        break
                
                # Wait for potential redirect after challenge
                await asyncio.sleep(5)
                logger.info(f"Final Page Title: {await page.title()}")

                # Automatic scroll to trigger dynamic content / Elementor loading
                logger.info("Scrolling to load dynamic content...")
                for i in range(15):
                    try:
                        # Scroll in increments to be more natural
                        await page.evaluate(f"window.scrollBy(0, {400 + (i * 100)})")
                        await asyncio.sleep(2)
                        
                        # Check if we hit footer or end of page
                        if i > 5:
                            links_count = len(await page.query_selector_all('article.elementor-post a, a.elementor-button-link'))
                            if links_count > 0:
                                logger.info(f"Found {links_count} Elementor links during scroll.")
                    except Exception as e:
                        logger.warning(f"Scroll error (might be navigating): {e}")
                        await asyncio.sleep(5)
                        break
                
                # Re-verify page after scroll/navigation
                logger.info(f"Page Title after scroll: {await page.title()}")
                
                # 1. Extract links using specific Elementor selectors
                selectors = [
                    ".elementor-post__title a",
                    ".elementor-post__read-more",
                    ".elementor-post__thumbnail__link",
                    ".elementor-button-link",
                    "article.elementor-post a",
                    "a.elementor-button",
                    "div.elementor-button-wrapper a"
                ]
                
                for selector in selectors:
                    elements = await page.query_selector_all(selector)
                    for el in elements:
                        href = await el.get_attribute("href")
                        if href:
                            all_urls.append(href)
                
                # 2. General link extraction as fallback
                links = await page.query_selector_all('a')
                logger.info(f"Total links found in {catalog_url}: {len(links)}")
                
                for link in links:
                    href = await link.get_attribute("href")
                    if not href: continue
                    
                    # More flexible pattern: must be on the domain, but NOT a known navigation page
                    is_internal = "smartdata.com.pe" in href
                    is_nav = any(p in href for p in [
                        "/cursos/", "/programas-de-especializacion/", "whatsapp", 
                        "facebook", "linkedin", "instagram", "quienes-somos", 
                        "blog", "contact", "servicios", "/tag/", "/category/",
                        "/cart/", "/checkout/", "/mi-cuenta/"
                    ])
                    is_root = href == "https://smartdata.com.pe/" or href == "https://smartdata.com.pe"
                    
                    if is_internal and not is_nav and not is_root:
                        if not href.startswith("http"):
                            href = f"https://smartdata.com.pe{href}"
                        all_urls.append(href)

            except Exception as e:
                logger.error(f"Error loading catalog {catalog_url}: {e}")
        
        # Clean and unique
        unique_urls = []
        seen = set()
        for url in all_urls:
            # Remove query params / fragments
            clean_url = url.split("?")[0].split("#")[0].rstrip("/")
            if clean_url not in seen and "smartdata.com.pe" in clean_url:
                unique_urls.append(clean_url)
                seen.add(clean_url)
                
        logger.info(f"Found {len(unique_urls)} unique potential course URLs.")
        if unique_urls:
            logger.info(f"Sample URLs: {unique_urls[:5]}")
        return unique_urls

    async def scrape_course_detail(self, page, url):
        """Extracts detailed information from a course page"""
        logger.info(f"Scraping detail: {url}")
        try:
            await page.goto(url, wait_until="load", timeout=90000)
            await asyncio.sleep(5)
            
            # 1. Name
            name_elem = await page.query_selector("h1")
            name = (await name_elem.inner_text()).strip() if name_elem else "N/A"
            clean_name = clean_course_name(name)
            
            # 2. Extract whole body text for pattern matching
            body_text = await page.inner_text("body")
            
            # Helper to extract section content
            async def get_section_text(keywords):
                for kw in keywords:
                    try:
                        # Try to find element by text
                        elem = await page.query_selector(f"text=/{kw}/i")
                        if elem:
                            # Try to get content from next siblings using evaluation
                            return await page.evaluate(f'''(kw) => {{
                                const headers = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6, strong, b, span, p'));
                                const header = headers.find(el => el.innerText && el.innerText.trim().toLowerCase().includes(kw.toLowerCase()));
                                if (!header) return "";
                                
                                let content = "";
                                let next = header.nextElementSibling;
                                if (!next && header.parentElement) next = header.parentElement.nextElementSibling;
                                
                                let count = 0;
                                while (next && count < 10) {{
                                    // Stop if we hit another H1, H2, H3
                                    if (["H1", "H2", "H3"].includes(next.tagName) && !next.innerText.toLowerCase().includes(kw.toLowerCase())) break;
                                    content += next.innerText + "\\n";
                                    next = next.nextElementSibling;
                                    count++;
                                }}
                                return content.trim();
                            }}''', kw)
                    except Exception:
                        continue
                return ""

            # 3. Temario (Syllabus)
            syllabus = await get_section_text(["Temario", "MÃ³dulos", "Contenido", "Plan de estudios"])
            
            # 4. Audiencia (Target Audience)
            target_audience = await get_section_text(["Dirigido a", "Perfil del participante", "Audiencia"])
            
            # 5. DuraciÃ³n (Duration)
            duration = ""
            # Often looks like "40 horas" or similar
            duration_match = re.search(r'(\d+)\s*(horas|meses|semanas)', body_text, re.IGNORECASE)
            if duration_match:
                duration = duration_match.group(0)
            
            # 6. InversiÃ³n (Price)
            price_pen = 0.0
            price_status = "consultar"
            # Look for S/ or PEN or Sifersas
            price_match = re.search(r'(S/|PEN)\.?\s*([\d,]+(\.\d+)?)', body_text)
            if price_match:
                price_str = price_match.group(2).replace(",", "")
                try:
                    price_pen = float(price_str)
                    price_status = "confirmado"
                except Exception:
                    pass
            
            # 7. Objetivos
            objectives = await get_section_text(["Objetivos", "Lo que aprenderÃ¡s", "AprenderÃ¡s"])
            
            # 8. Requisitos
            requirements = await get_section_text(["Requisitos", "Pre-requisitos", "Conocimientos previos"])
            
            # 9. Modalidad (Mode)
            # Default to Remoto as SmartData is known for live virtual classes
            mode = "Remoto"
            if "presencial" in body_text.lower():
                mode = "HÃ­brido" if "virtual" in body_text.lower() or "online" in body_text.lower() else "Presencial"
            mode = standardize_mode(mode)
            
            # 10. Description Long
            # Use intro text if possible, else first 2000 chars of body
            description_long = body_text[:2000]
            
            # Category & Subcategory
            category_extracted = standardize_category("", clean_name)
            subcategory_extracted = category_extracted
            
            course_type = infer_course_type(clean_name)

            return {
                "name": clean_name,
                "url": url,
                "institution_slug": self.institution_slug,
                "price_pen": price_pen,
                "price_status": price_status,
                "mode": mode,
                "address": "Remoto/Lima",
                "category": category_extracted,
                "subcategory": subcategory_extracted,
                "course_type": course_type,
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
            # 1. Resolve/Ensure Institution
            inst_url = f"{self.api_url}/institutions?slug=eq.{item['institution_slug']}"
            inst_res = requests.get(inst_url, headers=self.headers).json()
            
            if not inst_res or len(inst_res) == 0:
                logger.info(f"Institution {item['institution_slug']} missing. Creating...")
                create_res = requests.post(
                    f"{self.api_url}/institutions?select=id",
                    headers=self.headers,
                    json={
                        "name": self.institution_name, 
                        "slug": self.institution_slug, 
                        "website_url": "https://smartdata.com.pe/",
                        "address": "Remoto / Lima"
                    }
                ).json()
                if isinstance(create_res, dict) and "code" in create_res:
                    logger.error(f"Error creating institution: {create_res['message']}")
                    return
                inst_id = create_res[0]['id']
            else:
                inst_id = inst_res[0]['id']
            
            # 2. Slug
            course_slug = item['name'].lower().replace(" ", "-").replace("/", "-")[:255]
            course_slug = re.sub(r'[^a-z0-9-]', '', course_slug).lstrip('-') or 'curso'

            # 3. UPSERT Course
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
                "syllabus": item.get('syllabus', ''),
                "description_long": item.get('description_long', ''),
                "objectives": item.get('objectives', ''),
                "target_audience": item.get('target_audience', ''),
                "requirements": item.get('requirements', ''),
                "duration": item.get('duration', ''),
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
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("Missing credentials in .env")
        return

    harvester = SmartDataHarvester()
    
    async with async_playwright() as p:
        # Note: Added slow_mo to further simulate human behavior
        browser = await p.chromium.launch(headless=True, slow_mo=500)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800}
        )
        page = await context.new_page()
        await harvester.apply_stealth(page)
        
        urls = await harvester.get_course_urls(page)
        
        if not urls:
            logger.error("No course URLs found. Check catalog selectors or website status.")
            await browser.close()
            return

        # Soft-delete protocol
        try:
            inst_url = f"{harvester.api_url}/institutions?slug=eq.{harvester.institution_slug}"
            inst_res = requests.get(inst_url, headers=harvester.headers).json()
            if inst_res and len(inst_res) > 0:
                inst_id = inst_res[0]['id']
                logger.info(f"Deactivating old courses for {harvester.institution_name}...")
                requests.patch(
                    f"{harvester.api_url}/courses?institution_id=eq.{inst_id}",
                    headers=harvester.headers,
                    json={"is_active": False}
                )
        except Exception as e:
            logger.error(f"Error in soft-delete protocol: {e}")

        # Process courses (limit to 15 for relevance and speed)
        count = 0
        for url in urls:
            if count >= 15: break
            data = await harvester.scrape_course_detail(page, url)
            if data:
                harvester.save_to_db(data)
                count += 1
            await asyncio.sleep(3) # Respect rate limiting
            
        await browser.close()
        logger.info(f"Harvest complete. {count} courses processed.")

if __name__ == "__main__":
    asyncio.run(main())
