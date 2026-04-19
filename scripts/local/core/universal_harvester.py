import asyncio
import os
import json
import logging
import re
import sys
import hashlib
from datetime import datetime
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET

import aiohttp
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# Add the parent directory to sys.path to import shared utilities
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.db_client import get_db_client
from shared.utils import normalize_url

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("UniversalHarvester")

class UniversalHarvester:
    def __init__(self, institution_data):
        self.institution = institution_data
        self.db = get_db_client()
        self.visited_urls = set()
        self.course_urls = set()
        # Limit to 3 hops for BFS
        self.MAX_DEPTH = 3
        # Limit max URLs to process (None for full scan)
        self.MAX_URLS = None
        
        # Blacklist to ignore shopping carts, internal links, etc.
        self.blacklist_patterns = [
            r'add-to-cart', r'cart', r'checkout', r'login', r'registro', 
            r'\.pdf$', r'\.jpg$', r'\.png$', r'\.zip$', r'\.webp$', r'\.doc$', r'\.json$', 
            r'/wp-json/', r'xmlrpc', r'=http', r'\?', r'#',
            r'/tag/', r'/category/noticias/', r'/contacto', r'/nosotros'
        ]

    async def _fetch_sitemap(self, session, sitemap_url):
        urls = set()
        try:
            logger.info(f"Checking sitemap: {sitemap_url}")
            async with session.get(sitemap_url, timeout=15) as response:
                if response.status == 200:
                    text = await response.text()
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
        """Asynchronous BFS up to MAX_DEPTH."""
        queue = [(start_url, 0)]
        
        async with aiohttp.ClientSession() as session:
            while queue:
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
                                self.course_urls.add(link)
                            
                            # Add to next batch if valid domain and not potential (so we can keep clicking)
                            # But wait, if it IS potential, we still might want to click to find more?
                            # For safety, we keep crawling anything on domain.
                            if self._is_valid_crawl_url(link) and link not in self.visited_urls:
                                queue.append((link, next_depth))

    def _is_valid_crawl_url(self, url):
        base_domain = urlparse(self.institution.get('website_url')).netloc
        if urlparse(url).netloc != base_domain:
            return False
            
        return not any(re.search(p, url.lower()) for p in self.blacklist_patterns)

    async def _fetch_and_parse(self, session, url, depth):
        links = []
        try:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    html = await response.text()
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

    async def discover_courses(self):
        """
        Attempts to find course URLs by crawling (BFS) and checking sitemaps.
        """
        start_url = self.institution.get('website_url')
        if not start_url:
            logger.error(f"No website URL for institution: {self.institution.get('name')}")
            return []

        logger.info(f"Starting discovery for {self.institution.get('name')} at {start_url}")
        
        # 1. Try Sitemap first
        sitemap_url = urljoin(start_url, '/sitemap.xml')
        async with aiohttp.ClientSession() as session:
            sitemap_links = await self._fetch_sitemap(session, sitemap_url)
        
        for link in sitemap_links:
            if self._is_potential_course_url(link):
                self.course_urls.add(link)
                
        logger.info(f"Sitemap discovery found {len(self.course_urls)} potential courses.")
        
        # 2. Async BFS Crawl
        logger.info(f"Starting Async BFS Crawl from {start_url} (Max Depth: {self.MAX_DEPTH})")
        await self._bfs_crawl(start_url)
        
        # Convert to list and apply absolute limits if any
        final_urls = list(self.course_urls)
        
        logger.info(f"Total Discovery found {len(final_urls)} potential course URLs.")
        return final_urls

    def _is_potential_course_url(self, url):
        """Heuristic to identify course detail pages."""
        if not self._is_valid_crawl_url(url):
            return False
            
        keywords = ["curso", "diplomado", "maestria", "doctorado", "programa", "especializacion"]
        return any(k in url.lower() for k in keywords)

    def _generate_hash(self, text):
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def _check_if_changed(self, url, html_content):
        content_hash = self._generate_hash(html_content)
        
        try:
            # Check staging_raw
            data = self.db.select(
                'staging_raw', 
                filters=f"url=eq.{url}", 
                columns="content_hash"
            )
            if data and len(data) > 0:
                old_hash = data[0].get('content_hash')
                if old_hash == content_hash:
                    return False, content_hash # Not changed
        except Exception as e:
            logger.warning(f"Error checking hash for {url}: {e}")
            
        return True, content_hash # Changed or new

    async def scrape_course_detail(self, page, url):
        """
        Generic scraping logic using OpenGraph, JSON-LD, and HTML heuristics.
        """
        logger.info(f"Scraping {url}")
        try:
            # Fast check
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=15) as res:
                    if res.status != 200:
                        logger.warning(f"URL returned {res.status}: {url}")
                        return None
                    text = await res.text()
                    effective_url = normalize_url(str(res.url))
                    has_changed, content_hash = self._check_if_changed(url, text)
            
            if not has_changed:
                logger.info(f"Skipping {url} - Content has not changed (Delta check passed).")
                return None

            await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            await asyncio.sleep(2) # Wait for potential JS rendering

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
            
            # Use on_conflict=url
            res = self.db.upsert('staging_raw', harvest_data, on_conflict="url")
            
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

    course_urls = await harvester.discover_courses()
    
    if not course_urls:
        logger.warning(f"No course URLs found for {inst_data.get('name')}")
        return

    # To avoid blowing up free-tier resources rapidly, we limit concurrent browser tabs to 1
    # We navigate one by one with playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        )
        # Block unnecessary resources for faster scraping
        await context.route("**/*", lambda route: route.abort() 
            if route.request.resource_type in ["image", "media", "font", "stylesheet"] 
            else route.continue_()
        )
        
        page = await context.new_page()
        
        for i, url in enumerate(course_urls):
            logger.info(f"Processing {i+1}/{len(course_urls)}: {url}")
            item = await harvester.scrape_course_detail(page, url)
            if item:
                harvester.save_to_staging(item)
                
        await browser.close()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
