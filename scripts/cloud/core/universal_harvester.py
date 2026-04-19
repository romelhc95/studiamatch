import asyncio
import os
import json
import logging
import re
import sys
import hashlib
import random
from datetime import datetime
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from curl_cffi.requests import AsyncSession

# Add the parent directory to sys.path to import shared utilities
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.utils import get_random_user_agent, normalize_url
from shared.db_client import get_db_client

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
        self.db = get_db_client()
        self.visited_urls = set()
        self.course_urls = set()
        # Limit to 3 hops for BFS
        self.MAX_DEPTH = 3
        
        # --- Stealth & Resilience Config ---
        self.semaphore = asyncio.Semaphore(3) # Max 3 concurrent requests
        self.consecutive_blocks = 0
        self.BLOCK_THRESHOLD = 3 # Abort after 3 consecutive 403/429
        self.circuit_open = False
        
        # Checkpoint directory
        self.checkpoint_dir = os.path.join(os.getcwd(), "checkpoints")
        os.makedirs(self.checkpoint_dir, exist_ok=True)

        # Blacklist to ignore shopping carts, internal links, etc.
        self.blacklist_patterns = [
            r'add-to-cart', r'cart', r'checkout', r'login', r'registro', 
            r'\.pdf$', r'\.jpg$', r'\.png$', r'\.zip$', r'\.webp$', r'\.doc$', r'\.json$', 
            r'/wp-json/', r'xmlrpc', r'=http', r'\?', r'#',
            r'/tag/', r'/category/noticias/', r'/contacto', r'/nosotros'
        ]

    async def _safe_request(self, session, url, method="GET", **kwargs):
        """
        Executes a network request with semaphores, jitter, UA rotation, and Circuit Breaker logic.
        """
        if self.circuit_open:
            return None

        async with self.semaphore:
            # 1. Jitter (Delays)
            await asyncio.sleep(random.uniform(2, 5))

            # 2. UA Rotation & Impersonation
            impersonate = random.choice(["chrome120", "chrome119", "edge101", "safari15_5"])
            
            try:
                # Use curl_cffi for TLS Impersonation
                response = await session.request(
                    method, url, 
                    impersonate=impersonate,
                    timeout=20,
                    **kwargs
                )

                # 3. Circuit Breaker Logic
                if response.status_code in [403, 429]:
                    self.consecutive_blocks += 1
                    logger.warning(f"Blocked ({response.status_code}) at {url}. Count: {self.consecutive_blocks}")
                else:
                    self.consecutive_blocks = 0 # Reset on success
                
                if self.consecutive_blocks >= self.BLOCK_THRESHOLD:
                    logger.error(f"CIRCUIT BREAKER OPEN for {self.institution.get('name')}. Aborting.")
                    self.circuit_open = True

                return response
            except asyncio.TimeoutError:
                self.consecutive_blocks += 1
                logger.warning(f"Timeout at {url}. Count: {self.consecutive_blocks}")
                if self.consecutive_blocks >= self.BLOCK_THRESHOLD:
                    self.circuit_open = True
                return None
            except Exception as e:
                logger.warning(f"Request failed for {url}: {e}")
                return None

    def _save_discovered_url(self, url):
        """
        Checkpointing: Save discovered URL immediately to DB with 'discovered' status.
        Fallback to local JSON if DB fails.
        """
        success = False
        try:
            payload = {
                "institution_id": self.institution.get('id'),
                "url": url,
                "status": "discovered"
            }
            # Use direct DB client (handles SQL vs API automatically)
            res = self.db.upsert("staging_raw", payload, on_conflict="url")
            if res:
                success = True
                logger.info(f"DB Checkpoint Success: {url}")
        except Exception as e:
            logger.warning(f"DB Checkpoint failed for {url}, falling back to local JSON: {e}")

        # Local Fallback (Always save locally for safety)
        try:
            filename = f"discovered_{self.institution.get('slug')}.json"
            filepath = os.path.join(self.checkpoint_dir, filename)
            
            data = []
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    data = json.load(f)
            
            if url not in data:
                data.append(url)
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Critical: Local JSON checkpoint failed: {e}")

    async def _fetch_sitemap(self, session, sitemap_url):
        urls = set()
        if self.circuit_open: return urls

        try:
            logger.info(f"Checking sitemap: {sitemap_url}")
            response = await self._safe_request(session, sitemap_url)
            
            if response and response.status_code == 200:
                text = response.text
                try:
                    root = ET.fromstring(text)
                    
                    # Handle sitemap indexes recursively
                    for sitemap in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap'):
                        loc = sitemap.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                        if loc is not None and loc.text:
                            urls.update(await self._fetch_sitemap(session, loc.text))
                            
                    # Handle standard sitemap entries
                    for url in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
                        loc = url.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                        if loc is not None and loc.text:
                            urls.add(loc.text)
                except Exception as parse_e:
                    logger.warning(f"Error parsing sitemap XML: {parse_e}")
                    
                    # Fallback for plain text extraction
                    links = re.findall(r'<loc>(http.*?)</loc>', text)
                    for l in links:
                        urls.add(l)
        except Exception as e:
            logger.warning(f"Failed to fetch sitemap {sitemap_url}: {e}")
            
        return urls

    async def _bfs_crawl(self, start_url):
        """Asynchronous BFS up to MAX_DEPTH with checkpointing."""
        queue = [(start_url, 0)]
        
        async with AsyncSession() as session:
            while queue and not self.circuit_open:
                current_batch = queue[:]
                queue.clear()
                
                tasks = []
                for url, depth in current_batch:
                    if url not in self.visited_urls:
                        self.visited_urls.add(url)
                        if depth <= self.MAX_DEPTH:
                            tasks.append(self._fetch_and_parse(session, url, depth))
                
                if not tasks:
                    break
                    
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for res in results:
                    if isinstance(res, tuple):
                        found_links, next_depth = res
                        for link in found_links:
                            if self._is_potential_course_url(link):
                                if link not in self.course_urls:
                                    self.course_urls.add(link)
                                    self._save_discovered_url(link) # Checkpoint
                            
                            if self._is_valid_crawl_url(link) and link not in self.visited_urls:
                                queue.append((link, next_depth))

    def _is_valid_crawl_url(self, url):
        base_domain = urlparse(self.institution.get('website_url')).netloc
        if urlparse(url).netloc != base_domain:
            return False
            
        return not any(re.search(p, url.lower()) for p in self.blacklist_patterns)

    async def _fetch_and_parse(self, session, url, depth):
        links = []
        if self.circuit_open: return list(set(links)), depth + 1

        try:
            response = await self._safe_request(session, url)
            if response and response.status_code == 200:
                html = response.text
                # Use XML parser if content looks like XML (e.g. sitemap hit during crawl)
                parser = 'xml' if html.strip().startswith('<?xml') or '<urlset' in html else 'html.parser'
                soup = BeautifulSoup(html, parser)
                for a in soup.find_all('a', href=True):
                    full_url = urljoin(url, a['href']).split('#')[0].strip()
                    if full_url.startswith('http'):
                        links.append(full_url)
        except Exception:
            pass
        return list(set(links)), depth + 1

    async def _load_existing_urls(self):
        """
        Loads already discovered/processed URLs from staging_raw to avoid re-crawling.
        """
        try:
            inst_id = self.institution.get('id')
            # Fetch URLs that are not errors
            data = self.db.select("staging_raw", filters=f"institution_id=eq.{inst_id},status=neq.error", columns="url")
            if data:
                existing = {row['url'] for row in data}
                logger.info(f"Loaded {len(existing)} existing URLs from DB to skip.")
                self.visited_urls.update(existing)
                return existing
        except Exception as e:
            logger.warning(f"Could not load existing URLs from DB: {e}")
        return set()

    async def discover_courses(self):
        """
        Attempts to find course URLs by crawling (BFS) and checking sitemaps.
        """
        start_url = self.institution.get('website_url')
        if not start_url:
            logger.error(f"No website URL for institution: {self.institution.get('name')}")
            return []

        logger.info(f"Starting discovery for {self.institution.get('name')} at {start_url}")
        
        # 0. Load existing URLs to skip
        existing_urls = await self._load_existing_urls()
        
        # 1. Try Sitemap first
        sitemap_url = urljoin(start_url, '/sitemap.xml')
        async with AsyncSession() as session:
            sitemap_links = await self._fetch_sitemap(session, sitemap_url)
        
        for link in sitemap_links:
            if self._is_potential_course_url(link):
                if link not in self.course_urls and link not in existing_urls:
                    self.course_urls.add(link)
                    self._save_discovered_url(link) # Checkpoint
                
        logger.info(f"Sitemap discovery found {len(self.course_urls)} NEW potential courses.")
        
        # 2. Async BFS Crawl
        if not self.circuit_open:
            logger.info(f"Starting Async BFS Crawl from {start_url} (Max Depth: {self.MAX_DEPTH})")
            await self._bfs_crawl(start_url)
        
        # Convert to list and only return NEW URLs
        final_urls = [url for url in list(self.course_urls) if url not in existing_urls]
        
        logger.info(f"Total Discovery found {len(final_urls)} NEW potential course URLs (Skipped {len(existing_urls)} existing).")
        return final_urls

    def _is_potential_course_url(self, url):
        """Heuristic to identify course detail pages."""
        if not self._is_valid_crawl_url(url):
            return False
            
        keywords = ["curso", "diplomado", "maestria", "doctorado", "programa", "especializacion"]
        return any(k in url.lower() for k in keywords)

    def _generate_hash(self, text):
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    async def _check_if_changed(self, url, html_content):
        content_hash = self._generate_hash(html_content)
        
        try:
            # Check staging_raw via shared DB client
            data = self.db.select("staging_raw", filters=f"url=eq.{url}", columns="content_hash")
            
            if data and len(data) > 0:
                old_hash = data[0].get('content_hash')
                if old_hash == content_hash:
                    return False, content_hash # Not changed
        except Exception as e:
            logger.warning(f"Error checking hash for {url}: {e}")
            
        return True, content_hash # Changed or new

    async def scrape_course_detail(self, session, page, url):
        """
        Generic scraping logic using OpenGraph, JSON-LD, and HTML heuristics.
        """
        if self.circuit_open: return None
        
        logger.info(f"Scraping {url}")
        try:
            # 1. Fast check with curl_cffi for Delta
            response = await self._safe_request(session, url)
            if not response or response.status_code != 200:
                logger.warning(f"URL returned {response.status_code if response else 'No Response'}: {url}")
                return None
                
            effective_url = normalize_url(response.url)
            has_changed, content_hash = await self._check_if_changed(url, response.text)
            
            if not has_changed:
                logger.info(f"Skipping {url} - Content has not changed (Delta check passed).")
                return None

            # 2. Extract detail using Playwright (only if changed)
            # Use effective_url if available to ensure we scrape the final page
            scrape_target = response.url if response else url
            await page.goto(scrape_target, wait_until="domcontentloaded", timeout=45000)
            await asyncio.sleep(random.uniform(1, 3)) # Stealth wait

            raw_html = await page.content()

            json_ld = await self._extract_json_ld(page)
            og_tags = await self._extract_og_tags(page)
            
            title = await self._extract_title(page, og_tags, json_ld)
            description = await self._extract_description(page, og_tags, json_ld)
            
            if not self._is_valid_title(title):
                 logger.info(f"Skipping {url} - Invalid title detected: {title}")
                 return None
            
            return {
                "name": title,
                "url": url,
                "effective_url": effective_url,
                "description_long": description,
                "json_ld": json_ld,
                "og_tags": og_tags,
                "raw_html": raw_html[:50000],
                "content_hash": content_hash
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
            
        if len(title.split()) < 2 and len(title) < 15:
            return False
            
        return True

    async def _extract_title(self, page, og, schema):
        title = schema.get("name") or og.get("title")
        
        if not title:
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

    async def _extract_description(self, page, og, schema):
        desc = schema.get("description") or og.get("description")
        if not desc:
            paragraphs = await page.query_selector_all("p")
            texts = []
            for p in paragraphs[:5]:
                t = await p.inner_text()
                if len(t.strip()) > 50:
                    texts.append(t.strip())
            desc = "\n\n".join(texts)
        return desc.strip() if desc else ""

    def save_to_staging(self, item):
        if not item or not item.get('url'): return
        
        try:
            harvest_data = {
                "institution_id": self.institution.get('id'),
                "url": item['url'],
                "effective_url": item.get('effective_url'),
                "raw_name": item.get('name'),
                "raw_description": item.get('description_long'),
                "raw_html": item.get('raw_html'),
                "raw_json_ld": item.get('raw_json_ld'),
                "raw_og_tags": item.get('raw_og_tags'),
                "content_hash": item.get('content_hash'),
                "status": "pending"
            }
            
            # Use direct DB client (handles SQL vs API automatically)
            res = self.db.upsert("staging_raw", harvest_data, on_conflict="url")
            
            if res:
                logger.info(f"Harvested to Staging: {item['url']}")
            else:
                logger.error(f"Error harvesting {item['url']}")
                
        except Exception as e:
            logger.error(f"Harvesting error for {item['url']}: {e}")


async def main():
    if len(sys.argv) < 2:
        logger.error("No institution JSON provided.")
        return

    try:
        inst_data = json.loads(sys.argv[1])
    except Exception as e:
        logger.error(f"Invalid JSON provided: {e}")
        return

    harvester = UniversalHarvester(inst_data)

    # 1. Discovery Phase
    course_urls = await harvester.discover_courses()
    
    if not course_urls:
        logger.warning(f"No course URLs found for {inst_data.get('name')}")
        if not harvester.circuit_open:
            return # Only return if it's not a circuit break

    if harvester.circuit_open:
        logger.error(f"Discovery aborted due to Circuit Breaker for {inst_data.get('name')}")
        return

    # 2. Scraping Phase
    # We use Playwright for deep extraction and curl_cffi for fast delta checks
    async with AsyncSession() as session:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            # Use random User-Agent from our utilities
            ua = get_random_user_agent()
            context = await browser.new_context(user_agent=ua)
            
            # Block unnecessary resources for faster scraping
            await context.route("**/*", lambda route: route.abort() 
                if route.request.resource_type in ["image", "media", "font", "stylesheet"] 
                else route.continue_()
            )
            
            page = await context.new_page()
            
            for i, url in enumerate(course_urls):
                if harvester.circuit_open:
                    logger.error("Scraping aborted mid-process due to Circuit Breaker.")
                    break

                logger.info(f"Processing {i+1}/{len(course_urls)}: {url}")
                item = await harvester.scrape_course_detail(session, page, url)
                if item:
                    harvester.save_to_staging(item)
                    
            await browser.close()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
