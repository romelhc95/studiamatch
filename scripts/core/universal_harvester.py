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
from playwright.async_api import async_playwright
from curl_cffi.requests import AsyncSession
from dotenv import load_dotenv

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.utils import (
    clean_course_name,
    infer_course_type,
    standardize_category,
    slugify,
    get_random_user_agent,
    setup_lima_logging,
    normalize_url
)
from shared.db_client import get_db_client

# Setup logging
logger = setup_lima_logging("UniversalHarvester")

load_dotenv()

def normalize_url(url: str) -> str:
    """Removes query strings, fragments, and trailing slashes for clean mapping."""
    if not url: return ""
    try:
        parsed = urlparse(url)
        # Forzar minúsculas en el dominio y limpiar el path de la barra final
        path = parsed.path.rstrip('/')
        # Reconstruir solo con esquema, host y path limpio
        return f"{parsed.scheme}://{parsed.netloc.lower()}{path}"
    except Exception:
        return url.rstrip('/')

class UniversalHarvester:
    def __init__(self, institution, global_start=None):
        import time
        self.institution = institution
        self.db = get_db_client()
        self.visited_urls = set()
        self.course_urls = set()
        self.impersonate = "chrome110"
        self.error_count = 0
        self.BLOCK_THRESHOLD = 5
        self.MAX_DEPTH = 3
        self.semaphore = asyncio.Semaphore(3)
        self.circuit_open = False
        self.exclusions = self._load_exclusions()

        # ⏱️ TIME GUARD CONFIG (Global awareness)
        self.global_start = global_start or time.time()
        self.MAX_RUN_TIME = 19200 # 5h 20m (19,200s)

    def _load_exclusions(self):
        try:
            return self.db.select('crawler_exclusions', filters="is_active=eq.true") or []
        except Exception as e:
            logger.warning(f"Error loading exclusions: {e}")
            return []

    def check_time_guard(self):
        """Checks if the global execution time limit has been reached."""
        import time
        elapsed = time.time() - self.global_start
        if elapsed > self.MAX_RUN_TIME:
            logger.warning(f"⚠️ [TIME GUARD] Límite de ejecución global alcanzado ({elapsed/3600:.2f}h). Solicitando detención...")
            self.circuit_open = True
            return True
        return False

    def _extract_canonical(self, html_content):
        """Extracts the <link rel='canonical'> href from HTML."""
        if not html_content: return None
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            canonical = soup.find("link", rel="canonical")
            if canonical and canonical.get("href"):
                return normalize_url(canonical["href"].strip())
        except Exception as e:
            logger.warning(f"Error extracting canonical URL: {e}")
        return None

    def _generate_hash(self, text):
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    async def _check_if_changed(self, url, html_content, effective_url=None, canonical_url=None):
        content_hash = self._generate_hash(html_content)
        try:
            # Check by any of the possible identities to find existing records
            ids = [url, effective_url, canonical_url]
            ids = [normalize_url(i) for i in ids if i]
            
            # PostgREST style query for multiple OR values is complex, 
            # so we check by the main URL first and fallback to a list check if needed
            data = self.db.select("staging_raw", filters=f"url=eq.{url}", columns="content_hash")
            
            if data and len(data) > 0:
                old_hash = data[0].get('content_hash')
                if old_hash == content_hash:
                    return False, content_hash
        except Exception as e:
            logger.warning(f"Error checking hash for {url}: {e}")
            
        return True, content_hash

    async def _safe_request(self, session, url):
        """Wrapper for curl_cffi to handle retries and stealth."""
        try:
            # Use random delay to simulate human behavior
            await asyncio.sleep(random.uniform(2, 5))
            resp = await session.get(url, impersonate=self.impersonate, timeout=25)
            return resp
        except Exception as e:
            logger.debug(f"Request failed for {url}: {e}")
            return None

    async def _fetch_sitemap(self, session, sitemap_url):
        """Recursively fetches and parses sitemaps."""
        if self.check_time_guard(): return []
        
        logger.info(f"Checking Sitemap: {sitemap_url}")
        links = []
        resp = await self._safe_request(session, sitemap_url)
        if not resp or resp.status_code != 200: return links

        try:
            root = ET.fromstring(resp.content)
            # Handle sitemap indexes
            for sitemap in root.findall('{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap'):
                if self.check_time_guard(): break
                loc = sitemap.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc').text
                links.extend(await self._fetch_sitemap(session, loc))
            
            # Handle standard urlset
            for url in root.findall('{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
                if self.check_time_guard(): break
                loc = url.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc').text
                links.append(loc)
        except Exception as e:
            logger.warning(f"Failed to parse sitemap {sitemap_url}: {e}")
        
        return list(set(links))

    async def _bfs_crawl(self, start_url):
        """Async BFS to discover internal links."""
        queue = [(start_url, 0)]
        self.visited_urls.add(start_url)
        
        async with AsyncSession() as session:
            while queue and len(self.course_urls) < 500: # Safety cap per institution
                if self.circuit_open or self.check_time_guard(): break
                
                # Process in small parallel batches to respect the server
                current_batch = [queue.pop(0) for _ in range(min(len(queue), 3))]
                tasks = []
                for url, depth in current_batch:
                    if depth < self.MAX_DEPTH:
                        tasks.append(self._fetch_and_parse(session, url, depth))
                
                results = await asyncio.gather(*tasks)
                for links, next_depth in results:
                    if self.check_time_guard(): break
                    for link in links:
                        if self._is_valid_crawl_url(link):
                            if link not in self.course_urls:
                                self.course_urls.add(link)
                                self._save_discovered_url(link)
                            
                            if self._is_valid_crawl_url(link) and link not in self.visited_urls:
                                queue.append((link, next_depth))

    def _is_valid_crawl_url(self, url):
        base_domain = urlparse(self.institution.get('website_url')).netloc
        if urlparse(url).netloc != base_domain:
            return False
            
        low_url = url.lower()
        inst_id = self.institution.get('id')
        
        # Check global and specific exclusions
        for exc in self.exclusions:
            if exc.get('institution_id') and exc['institution_id'] != inst_id: continue
            if exc['pattern'].lower() in low_url: return False
            
        return True

    async def _fetch_and_parse(self, session, url, depth):
        links = []
        if self.circuit_open or self.check_time_guard(): return list(set(links)), depth + 1

        try:
            response = await self._safe_request(session, url)
            if response and response.status_code == 200:
                html = response.text
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
        try:
            inst_id = self.institution.get('id')
            data = self.db.select("staging_raw", filters=f"institution_id=eq.{inst_id},status=in.(processed,discarded)", columns="url")
            if data:
                existing = {row['url'] for row in data}
                logger.info(f"Loaded {len(existing)} completed URLs from DB to skip.")
                self.visited_urls.update(existing)
                return existing
        except Exception as e:
            logger.warning(f"Could not load existing URLs from DB: {e}")
        return set()

    async def discover_courses(self):
        start_url = self.institution.get('website_url')
        if not start_url: return []

        logger.info(f"Starting discovery for {self.institution.get('name')}")
        existing_urls = await self._load_existing_urls()
        
        sitemap_url = urljoin(start_url, '/sitemap.xml')
        async with AsyncSession() as session:
            sitemap_links = await self._fetch_sitemap(session, sitemap_url)
        
        for link in sitemap_links:
            if self.check_time_guard(): break
            if self._is_valid_crawl_url(link):
                if link not in self.course_urls and link not in existing_urls:
                    self.course_urls.add(link)
                    self._save_discovered_url(link)
        
        # 🚀 FAST PATH: If sitemap gave us enough NEW courses, skip the slow BFS crawl
        if len(self.course_urls) > 50:
            logger.info(f"🚀 [FAST PATH] Found {len(self.course_urls)} courses via Sitemap. Skipping slow BFS crawl.")
        elif not self.circuit_open:
            await self._bfs_crawl(start_url)
        
        final_urls = [url for url in list(self.course_urls) if url not in existing_urls]
        logger.info(f"Total Discovery: {len(final_urls)} NEW potential courses.")
        return final_urls

    async def scrape_course_detail(self, session, page, url):
        if self.circuit_open: return None
        
        logger.info(f"Scraping {url}")
        try:
            # 1. Delta Check & Canonical
            response = await self._safe_request(session, url)
            if not response or response.status_code != 200: return None
                
            eff_url = normalize_url(response.url)
            can_url = self._extract_canonical(response.text)
            
            # Double Layer Exclusion Check (Post-Scrape)
            if eff_url and not self._is_valid_crawl_url(eff_url):
                logger.info(f"Skipping {url} - Redirected to excluded URL: {eff_url}")
                self.db.upsert('staging_raw', {"url": url, "institution_id": self.institution['id'], "status": "discarded", "metadata": {"discard_reason": "post_scrape_exclusion"}}, on_conflict="url")
                return None
                
            has_changed, content_hash = await self._check_if_changed(url, response.text, eff_url, can_url)
            if not has_changed:
                logger.info(f"Skipping {url} - No changes.")
                return None

            # 2. Extract with Playwright
            await page.goto(response.url, wait_until="domcontentloaded", timeout=45000)
            await asyncio.sleep(random.uniform(1, 3))

            raw_html = await page.content()
            json_ld = await self._extract_json_ld(page)
            og_tags = await self._extract_og_tags(page)
            title = await self._extract_title(page, og_tags, json_ld)
            description = await self._extract_description(page, og_tags, json_ld)
            
            return {
                "raw_name": title,
                "url": url,
                "effective_url": eff_url,
                "canonical_url": can_url,
                "raw_description": description,
                "raw_json_ld": json_ld,
                "raw_og_tags": og_tags,
                "raw_html": raw_html[:50000],
                "content_hash": content_hash,
                "institution_id": self.institution['id'],
                "status": "pending"
            }
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None

    async def _extract_json_ld(self, page):
        scripts = await page.query_selector_all('script[type="application/ld+json"]')
        for script in scripts:
            try:
                content = await script.inner_text()
                return json.loads(content)
            except Exception:
                continue
        return {}

    async def _extract_og_tags(self, page):
        return await page.evaluate('''() => {
            const tags = {};
            document.querySelectorAll('meta[property^="og:"]').forEach(m => {
                tags[m.getAttribute('property')] = m.content;
            });
            return tags;
        }''')

    async def _extract_title(self, page, og, ld):
        title = og.get('og:title') or (ld.get('name') if isinstance(ld, dict) else None)
        if not title: title = await page.title()
        return title

    async def _extract_description(self, page, og, ld):
        desc = og.get('og:description') or (ld.get('description') if isinstance(ld, dict) else None)
        if not desc:
            desc = await page.evaluate('() => document.querySelector("meta[name=\'description\']")?.content || ""')
        return desc

    def _save_discovered_url(self, url):
        self.db.upsert("staging_raw", {"url": url, "institution_id": self.institution['id'], "status": "discovered"}, on_conflict="url")

    def _save_to_staging(self, item):
        try:
            self.db.upsert("staging_raw", item, on_conflict="url")
            logger.info(f"Harvested to Staging: {item['url']}")
        except Exception as e:
            logger.error(f"Failed DB save: {e}")

async def main():
    import argparse
    import time
    
    parser = argparse.ArgumentParser()
    parser.add_argument("institution", help="JSON string of the institution")
    parser.add_argument("--global-start", type=float, help="Timestamp when the master orchestrator started")
    args = parser.parse_args()

    start_time = time.time()
    global_start = args.global_start or start_time
    
    # ⏱️ TIME GUARD CONFIG (GitHub Actions 6h limit)
    # We exit gracefully at 5h 40m (20400s) to allow subsequent stages to run
    MAX_RUN_TIME = 20400 
    
    inst = json.loads(args.institution)
    harvester = UniversalHarvester(inst, global_start=global_start)
    
    urls = await harvester.discover_courses()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        async with AsyncSession() as session:
            for i, url in enumerate(urls):
                # Check Time Guard
                elapsed_total = time.time() - global_start
                if elapsed_total > MAX_RUN_TIME:
                    logger.warning(f"⚠️ [TIME GUARD] Límite de ejecución alcanzado ({elapsed_total/3600:.2f}h). Realizando cierre elegante...")
                    break

                logger.info(f"Processing {i+1}/{len(urls)}: {url}")
                page = await browser.new_page(user_agent=get_random_user_agent())
                item = await harvester.scrape_course_detail(session, page, url)
                if item:
                    # Update status to pending for cleanser
                    item["status"] = "pending"
                    harvester._save_to_staging(item)
                await page.close()
            await browser.close()

    # 📊 Update Telemetry in institutions table
    duration = int(time.time() - start_time)
    try:
        harvester.db.patch("institutions", filters=f"id=eq.{inst['id']}", data={
            "last_harvest_at": datetime.now().isoformat(),
            "last_harvest_duration_sec": duration
        })
        logger.info(f"✅ Telemetry updated for {inst['name']}: {duration}s")
    except Exception as e:
        logger.error(f"Failed to update telemetry: {e}")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
