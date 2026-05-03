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

try:
    from playwright_stealth import Stealth
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.utils import (
    clean_course_name,
    infer_course_type,
    standardize_category,
    slugify,
    normalize_url,
    get_random_user_agent,
    setup_lima_logging,
    normalize_url
)
from shared.db_client import get_db_client

logger = setup_lima_logging("UniversalHarvester")
load_dotenv()


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
        self.profile = self._load_site_profile()
        self.exclusions = self._load_exclusions()

        # Fase 62: Perfil-driven config — todo el comportamiento diferenciado sale del perfil
        self.site_type = self.profile.get('site_type', 'traditional_ssr') if self.profile else 'traditional_ssr'
        self.requires_stealth = self.profile.get('requires_stealth', False) if self.profile else False
        self.requires_cf_bypass = self.profile.get('requires_cloudflare_bypass', False) if self.profile else False
        self.popup_selectors = self.profile.get('popup_close_selectors', []) if self.profile else []
        self.detail_wait_ms = self.profile.get('detail_wait_ms', 2000) if self.profile else 2000
        self.warmup_url = self.profile.get('warmup_url') if self.profile else None
        self.catalog_link_selector = self.profile.get('catalog_link_selector') if self.profile else None
        self.catalog_max_pages = self.profile.get('catalog_max_pages', 5) if self.profile else 5
        self.catalog_scroll_iterations = self.profile.get('catalog_scroll_iterations', 0) if self.profile else 0
        self.section_keywords = self.profile.get('section_keywords', {}) if self.profile else {}
        self.field_defaults = self.profile.get('field_defaults', {}) if self.profile else {}

        # ⏱️ TIME GUARD CONFIG
        self.global_start = global_start or time.time()
        self.MAX_RUN_TIME = 20400

    def _load_site_profile(self):
        try:
            inst_id = self.institution.get('id')
            profiles = self.db.select('institution_site_profiles',
                                       filters=f'institution_id=eq.{inst_id}',
                                       limit=1)
            if profiles and len(profiles) > 0:
                logger.info(f"Loaded site profile: site_type={profiles[0].get('site_type')}, discovery_mode={profiles[0].get('discovery_mode')}")
                return profiles[0]
        except Exception as e:
            logger.warning(f"Error loading site profile: {e}")
        return {}

    def _load_exclusions(self):
        try:
            if self.profile and self.profile.get('exclusion_patterns'):
                raw = self.profile['exclusion_patterns']
                compiled = []
                for exc in raw:
                    if isinstance(exc, str):
                        if exc.startswith('re:'):
                            pat = exc[3:]
                            if len(pat) > 200:
                                logger.warning(f"Regex pattern too long, skipping: {pat[:50]}...")
                                continue
                            if re.search(r'(\([^)]*[*+][^)]*\))+[*+]', pat):
                                logger.warning(f"ReDoS-risk pattern rejected: {pat}")
                                continue
                            try:
                                compiled.append(re.compile(pat, re.IGNORECASE))
                            except re.error as e:
                                logger.warning(f"Invalid regex pattern '{pat}': {e}")
                                continue
                        else:
                            compiled.append(exc.lower())
                return compiled
            return []
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
            ids = [url, effective_url, canonical_url]
            ids = [normalize_url(i) for i in ids if i]
            data = self.db.select("staging_raw", filters=f"url=eq.{url}", columns="content_hash")
            if data and len(data) > 0:
                old_hash = data[0].get('content_hash')
                if old_hash == content_hash:
                    return False, content_hash
        except Exception as e:
            logger.warning(f"Error checking hash for {url}: {e}")
        return True, content_hash

    async def _safe_request(self, session, url):
        try:
            await asyncio.sleep(random.uniform(2, 5))
            resp = await session.get(url, impersonate=self.impersonate, timeout=25)
            return resp
        except Exception as e:
            logger.debug(f"Request failed for {url}: {e}")
            return None

    async def _fetch_sitemap(self, session, sitemap_url):
        if self.check_time_guard(): return []
        logger.info(f"Checking Sitemap: {sitemap_url}")
        links = []
        resp = await self._safe_request(session, sitemap_url)
        if not resp or resp.status_code != 200: return links
        try:
            root = ET.fromstring(resp.content)
            for sitemap in root.findall('{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap'):
                if self.check_time_guard(): break
                loc = sitemap.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc').text
                links.extend(await self._fetch_sitemap(session, loc))
            for url in root.findall('{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
                if self.check_time_guard(): break
                loc = url.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc').text
                links.append(loc)
        except Exception as e:
            logger.warning(f"Failed to parse sitemap {sitemap_url}: {e}")
        return list(set(links))

    async def _bfs_crawl(self, start_url):
        queue = [(start_url, 0)]
        self.visited_urls.add(start_url)
        async with AsyncSession() as session:
            while queue and len(self.course_urls) < 500:
                if self.circuit_open or self.check_time_guard(): break
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

    NON_HTML_EXTENSIONS = (
        '.pdf', '.xlsx', '.xls', '.docx', '.doc', '.pptx', '.ppt',
        '.zip', '.rar', '.7z', '.tar', '.gz',
        '.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.bmp', '.ico',
        '.mp4', '.mp3', '.avi', '.mov', '.wmv',
        '.css', '.js', '.json', '.xml',
    )

    def _is_valid_crawl_url(self, url):
        base_domain = urlparse(self.institution.get('website_url')).netloc
        if urlparse(url).netloc != base_domain:
            return False
        low_url = url.lower()
        parsed_path = urlparse(url).path.lower()
        if parsed_path.endswith(self.NON_HTML_EXTENSIONS):
            return False
        for exc in self.exclusions:
            if isinstance(exc, re.Pattern):
                if exc.search(low_url):
                    return False
            elif isinstance(exc, str):
                if exc in low_url:
                    return False
        allowed = self.profile.get('allowed_url_patterns', []) if self.profile else []
        if allowed:
            for pattern in allowed:
                if isinstance(pattern, str):
                    if pattern.startswith('re:'):
                        try:
                            if re.search(pattern[3:], low_url, re.IGNORECASE):
                                return True
                        except re.error:
                            continue
                    elif pattern.lower() in low_url:
                        return True
            return False
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
            data = self.db.select("staging_raw", filters=f"institution_id=eq.{inst_id},status=in.(processed,discarded,discovered)", columns="url")
            if data:
                existing = {row['url'] for row in data}
                logger.info(f"Loaded {len(existing)} existing URLs from DB to skip (incl. discovered).")
                self.visited_urls.update(existing)
                discovered_count = self.db.patch("staging_raw",
                    filters=f"institution_id=eq.{inst_id},status=eq.discovered",
                    data={"status": "pending"})
                if discovered_count and discovered_count.get("status") == "success":
                    logger.info(f"Reset discovered → pending for reprocessing.")
                return existing
        except Exception as e:
            logger.warning(f"Could not load existing URLs from DB: {e}")
        return set()

    # ─────────────────────────────────────────────────────────
    # Fase 62B: Discovery Modes
    # ─────────────────────────────────────────────────────────

    async def discover_hardcoded_urls(self):
        discovery_mode = self.profile.get('discovery_mode', '')
        seed_urls = self.profile.get('seed_urls', [])
        if discovery_mode != 'hardcoded_urls' or not seed_urls:
            return None
        inst_id = self.institution.get('id')
        seen = set()
        clean_seeds = []
        for u in seed_urls:
            clean_u = normalize_url(u)
            if clean_u not in seen:
                seen.add(clean_u)
                clean_seeds.append(u)
        logger.info(f"🔗 [HARDCODED] Loaded {len(clean_seeds)} seed URLs for {self.institution.get('name')}")
        existing_urls = await self._load_existing_urls()
        new_urls = []
        for url in clean_seeds:
            if self.check_time_guard():
                break
            if url not in existing_urls and self._is_valid_crawl_url(url):
                new_urls.append(url)
                self.course_urls.add(url)
                self._save_discovered_url(url)
        logger.info(f"Total Discovery (hardcoded): {len(new_urls)} NEW from {len(clean_seeds)} seeds.")
        return new_urls

    async def discover_paginated_catalog(self, browser=None):
        """Discovery mode: iterate catalog_url_patterns with pagination (replaces PUCP harvester)."""
        catalog_patterns = self.profile.get('catalog_url_patterns', [])
        if not catalog_patterns:
            return None
        logger.info(f"📑 [PAGINATED CATALOG] Starting pagination discovery ({len(catalog_patterns)} patterns, {self.catalog_max_pages} pages max)")
        existing_urls = await self._load_existing_urls()
        new_urls = []
        async with AsyncSession() as session:
            for pattern in catalog_patterns:
                for page_num in range(1, self.catalog_max_pages + 1):
                    if self.check_time_guard():
                        break
                    url = pattern.replace('{page}', str(page_num))
                    links = []
                    if browser and self.site_type in ('spa_js_heavy', 'ecommerce'):
                        page = await browser.new_page(user_agent=get_random_user_agent())
                        try:
                            await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                            await asyncio.sleep(2)
                            if self.catalog_link_selector:
                                els = await page.query_selector_all(self.catalog_link_selector)
                                for el in els:
                                    href = await el.get_attribute('href')
                                    if href:
                                        links.append(urljoin(url, href))
                        except Exception as e:
                            logger.warning(f"Error loading catalog page {url}: {e}")
                        finally:
                            await page.close()
                    else:
                        resp = await self._safe_request(session, url)
                        if not resp or resp.status_code != 200:
                            continue
                        soup = BeautifulSoup(resp.text, 'html.parser')
                        if self.catalog_link_selector:
                            for a in soup.select(self.catalog_link_selector):
                                href = a.get('href')
                                if href:
                                    links.append(urljoin(url, href))
                    for link in links:
                        full_url = normalize_url(link)
                        if self._is_valid_crawl_url(full_url) and full_url not in existing_urls:
                            new_urls.append(full_url)
                            self.course_urls.add(full_url)
                            self._save_discovered_url(full_url)
                    logger.debug(f"  Page {page_num}: {len(links)} links found")
        logger.info(f"Total Paginated Catalog: {len(new_urls)} NEW URLs")
        return new_urls

    async def discover_catalog_links(self, browser):
        """Discovery mode: Playwright scroll + link extraction (replaces SmartData/New Horizons)."""
        catalog_url = self.institution.get('website_url')
        if not browser:
            logger.warning("Catalog link extraction requires Playwright browser")
            return None
        logger.info(f"🔍 [CATALOG LINKS] Starting scroll discovery for {self.institution.get('name')}")
        existing_urls = await self._load_existing_urls()
        new_urls = []
        page = await browser.new_page(user_agent=get_random_user_agent())
        try:
            if self.requires_stealth and STEALTH_AVAILABLE:
                await stealth_async(page)
            await page.goto(catalog_url, wait_until="domcontentloaded", timeout=60000)
            await self._dismiss_popups(page)
            for iteration in range(1, self.catalog_scroll_iterations + 1):
                if self.check_time_guard():
                    break
                scroll_y = 400 + iteration * 100
                await page.evaluate(f'window.scrollBy(0, {scroll_y})')
                await asyncio.sleep(2)
                if self.catalog_link_selector:
                    els = await page.query_selector_all(self.catalog_link_selector)
                    for el in els:
                        href = await el.get_attribute('href')
                        if href:
                            full_url = normalize_url(urljoin(catalog_url, href))
                            if self._is_valid_crawl_url(full_url) and full_url not in existing_urls:
                                new_urls.append(full_url)
                                self.course_urls.add(full_url)
                                self._save_discovered_url(full_url)
                if iteration % 5 == 0:
                    logger.info(f"  Scroll {iteration}/{self.catalog_scroll_iterations}: {len(new_urls)} new URLs so far")
                has_footer = await page.evaluate('() => document.querySelector("footer") !== null && window.scrollY + window.innerHeight >= document.body.scrollHeight')
                if has_footer:
                    logger.info("  Reached page bottom, stopping scroll")
                    break
        except Exception as e:
            logger.warning(f"Error during catalog scroll discovery: {e}")
        finally:
            await page.close()
        logger.info(f"Total Catalog Links: {len(new_urls)} NEW URLs")
        return new_urls

    # ─────────────────────────────────────────────────────────
    # Fase 62A: Discovery routing
    # ─────────────────────────────────────────────────────────

    async def discover_courses(self, browser=None):
        start_url = self.institution.get('website_url')
        if not start_url: return []
        existing_urls = await self._load_existing_urls()
        discovery_mode = self.profile.get('discovery_mode', '')

        if discovery_mode == 'hardcoded_urls':
            hardcoded_result = await self.discover_hardcoded_urls()
            if hardcoded_result is not None:
                return hardcoded_result
        elif discovery_mode == 'paginated_catalog':
            cat_result = await self.discover_paginated_catalog(browser)
            if cat_result is not None:
                return cat_result
        elif discovery_mode == 'catalog_link_extraction':
            cat_result = await self.discover_catalog_links(browser)
            if cat_result is not None:
                return cat_result

        # sitemap_bfs (default)
        logger.info(f"Starting sitemap/BFS discovery for {self.institution.get('name')}")
        sitemap_url = urljoin(start_url, '/sitemap.xml')
        async with AsyncSession() as session:
            sitemap_links = await self._fetch_sitemap(session, sitemap_url)
        for link in sitemap_links:
            if self.check_time_guard(): break
            if self._is_valid_crawl_url(link):
                if link not in self.course_urls and link not in existing_urls:
                    self.course_urls.add(link)
                    self._save_discovered_url(link)
        if len(self.course_urls) > 50:
            logger.info(f"🚀 [FAST PATH] Found {len(self.course_urls)} courses via Sitemap. Skipping slow BFS crawl.")
        elif not self.circuit_open:
            await self._bfs_crawl(start_url)
        final_urls = [url for url in list(self.course_urls) if url not in existing_urls]
        logger.info(f"Total Discovery: {len(final_urls)} NEW potential courses.")
        return final_urls

    # ─────────────────────────────────────────────────────────
    # Fase 62A+62D: Extraction with site_type routing and anti-bot
    # ─────────────────────────────────────────────────────────

    async def scrape_course_detail(self, session, page, url):
        """Playwright-based extraction for spa_js_heavy and ecommerce sites."""
        if self.circuit_open: return None
        logger.info(f"Scraping {url}")
        try:
            response = await self._safe_request(session, url)
            if not response or response.status_code != 200: return None
            eff_url = normalize_url(response.url)
            can_url = self._extract_canonical(response.text)
            if eff_url and not self._is_valid_crawl_url(eff_url):
                logger.info(f"Skipping {url} - Redirected to excluded URL: {eff_url}")
                self.db.upsert('staging_raw', {"url": url, "institution_id": self.institution['id'], "status": "discarded", "metadata": {"discard_reason": "post_scrape_exclusion"}}, on_conflict="url")
                return None
            has_changed, content_hash = await self._check_if_changed(url, response.text, eff_url, can_url)
            if not has_changed:
                logger.info(f"Skipping {url} - No changes.")
                return None

            # Fase 62D: Anti-bot — Playwright page setup
            await page.goto(response.url, wait_until="domcontentloaded", timeout=45000)
            await self._dismiss_popups(page)
            if self.requires_cf_bypass:
                await self._check_cloudflare_challenge(page)
            # Fase 62D: Profile-driven wait instead of hardcoded
            wait_sec = self.detail_wait_ms / 1000
            await asyncio.sleep(random.uniform(wait_sec * 0.5, wait_sec * 1.5))

            raw_html = await page.content()
            json_ld = await self._extract_json_ld(page)
            og_tags = await self._extract_og_tags(page)
            title = await self._extract_title(page, og_tags, json_ld)
            description = await self._extract_description(page, og_tags, json_ld)

            # Fase 62C: Section keywords extraction from rendered HTML
            sections = self._extract_sections(raw_html)

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
                "status": "pending",
                "metadata": json.dumps({"extracted_sections": sections, "field_defaults": self.field_defaults}),
            }
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None

    async def _scrape_http(self, session, url):
        """Fase 62A: HTTP-only extraction for traditional_ssr sites (faster, no Playwright overhead)."""
        if self.circuit_open: return None
        logger.info(f"Scraping (HTTP) {url}")
        try:
            response = await self._safe_request(session, url)
            if not response or response.status_code != 200: return None
            eff_url = normalize_url(response.url)
            can_url = self._extract_canonical(response.text)
            if eff_url and not self._is_valid_crawl_url(eff_url):
                logger.info(f"Skipping {url} - Redirected to excluded URL: {eff_url}")
                self.db.upsert('staging_raw', {"url": url, "institution_id": self.institution['id'], "status": "discarded", "metadata": {"discard_reason": "post_scrape_exclusion"}}, on_conflict="url")
                return None
            has_changed, content_hash = await self._check_if_changed(url, response.text, eff_url, can_url)
            if not has_changed:
                logger.info(f"Skipping {url} - No changes.")
                return None

            html = response.text
            soup = BeautifulSoup(html, 'html.parser')

            # Extract JSON-LD
            json_ld = {}
            for script in soup.select('script[type="application/ld+json"]'):
                try:
                    json_ld = json.loads(script.string)
                    break
                except Exception:
                    continue

            # Extract OG tags
            og_tags = {}
            for meta in soup.select('meta[property^="og:"]'):
                og_tags[meta.get('property')] = meta.get('content')

            # Extract title
            title = og_tags.get('og:title') or (json_ld.get('name') if isinstance(json_ld, dict) else None) or ''
            if not title:
                title_tag = soup.find('title')
                if title_tag:
                    title = title_tag.string or ''
            title = title.strip()

            # Extract description
            desc = og_tags.get('og:description') or (json_ld.get('description') if isinstance(json_ld, dict) else None) or ''
            if not desc:
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                if meta_desc:
                    desc = meta_desc.get('content', '')

            # Fase 62C: Section keywords extraction
            sections = self._extract_sections(html)

            return {
                "raw_name": title,
                "url": url,
                "effective_url": eff_url,
                "canonical_url": can_url,
                "raw_description": desc,
                "raw_json_ld": json_ld,
                "raw_og_tags": og_tags,
                "raw_html": html[:50000],
                "content_hash": content_hash,
                "institution_id": self.institution['id'],
                "status": "pending",
                "metadata": json.dumps({"extracted_sections": sections, "field_defaults": self.field_defaults}),
            }
        except Exception as e:
            logger.error(f"Error scraping (HTTP) {url}: {e}")
            return None

    # ─────────────────────────────────────────────────────────
    # Fase 62C: Section keywords extraction from headings
    # ─────────────────────────────────────────────────────────

    def _extract_sections(self, html: str) -> dict:
        """Scan H2/H3 headings and map to profile section_keywords."""
        if not self.section_keywords or not html:
            return {}
        soup = BeautifulSoup(html, 'html.parser')
        result = {}
        for heading in soup.find_all(['h2', 'h3']):
            text = heading.get_text(strip=True)
            if not text:
                continue
            text_lower = text.lower()
            for keyword, field_name in self.section_keywords.items():
                if keyword.lower() in text_lower:
                    next_el = heading.find_next_sibling()
                    content_parts = []
                    while next_el and next_el.name not in ('h2', 'h3'):
                        if next_el.name in ('p', 'ul', 'ol', 'div'):
                            content_parts.append(next_el.get_text(strip=True))
                        next_el = next_el.find_next_sibling()
                    result[field_name] = ' '.join(content_parts)[:1000]
        return result

    # ─────────────────────────────────────────────────────────
    # Fase 62D: Anti-bot helpers
    # ─────────────────────────────────────────────────────────

    async def _warmup_browser(self, browser):
        """Warm up the browser with a homepage visit + mouse simulation for Cloudflare."""
        if not self.warmup_url:
            return
        logger.info(f"🔄 Warming up browser at {self.warmup_url}")
        page = await browser.new_page()
        try:
            await page.goto(self.warmup_url, wait_until="domcontentloaded", timeout=60000)
            await page.mouse.move(random.randint(100, 500), random.randint(100, 500))
            await asyncio.sleep(2)
        except Exception as e:
            logger.warning(f"Warm-up page failed: {e}")
        finally:
            await page.close()

    async def _check_cloudflare_challenge(self, page):
        """Detect and wait for Cloudflare challenge to pass."""
        for attempt in range(12):
            title = await page.title()
            if "just a moment" not in title.lower():
                return True
            logger.info(f"Cloudflare challenge detected, waiting... (attempt {attempt + 1}/12)")
            await asyncio.sleep(10)
        logger.warning("Cloudflare challenge did not pass after 12 attempts (2 min)")
        return False

    async def _dismiss_popups(self, page):
        """Auto-dismiss popups using profile-driven selectors."""
        for selector in self.popup_selectors:
            try:
                if await page.is_visible(selector, timeout=2000):
                    await page.click(selector)
                    await asyncio.sleep(0.5)
                    logger.debug(f"Dismissed popup via selector: {selector}")
            except Exception:
                pass

    # ─────────────────────────────────────────────────────────
    # Extraction helpers
    # ─────────────────────────────────────────────────────────

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
        if not title:
            title = await page.title()
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
    MAX_RUN_TIME = 20400

    inst = json.loads(args.institution)
    harvester = UniversalHarvester(inst, global_start=global_start)

    # Fase 75: Require profile
    if not harvester.profile:
        logger.error(f"❌ SKIP {inst['name']}: No existe entrada en institution_site_profiles. "
                     f"Crea un perfil antes de ejecutar el pipeline.")
        return
    if not harvester.profile.get('pipeline_ready'):
        logger.info(f"🔍 DISCOVERY-ONLY {inst['name']}: pipeline_ready=false. "
                    f"Harvester will discover URLs into staging_raw for review. "
                    f"Cleansing/enrichment/sync will skip until pipeline_ready=true.")

    # Fase 62A: Determine if Playwright is needed based on site_type and discovery_mode
    need_browser = (
        harvester.site_type in ('spa_js_heavy', 'ecommerce') or
        harvester.discovery_mode == 'catalog_link_extraction'
    )
    extraction_needs_browser = harvester.site_type in ('spa_js_heavy', 'ecommerce')

    urls = []
    browser = None
    pw = None

    if need_browser:
        pw = await async_playwright().start()
        launch_kwargs = {"headless": True}
        if harvester.requires_stealth:
            launch_kwargs["slow_mo"] = 50
        browser = await pw.chromium.launch(**launch_kwargs)
        if harvester.requires_cf_bypass and harvester.warmup_url:
            await harvester._warmup_browser(browser)
        urls = await harvester.discover_courses(browser)
    else:
        urls = await harvester.discover_courses()

    async with AsyncSession() as session:
        for i, url in enumerate(urls):
            elapsed_total = time.time() - global_start
            if elapsed_total > MAX_RUN_TIME:
                logger.warning(f"⚠️ [TIME GUARD] Límite de ejecución alcanzado ({elapsed_total/3600:.2f}h). Realizando cierre elegante...")
                break

            logger.info(f"Processing {i + 1}/{len(urls)}: {url}")

            if extraction_needs_browser and browser:
                page = await browser.new_page(user_agent=get_random_user_agent())
                if harvester.requires_stealth and STEALTH_AVAILABLE:
                    stealth = Stealth()
                    await stealth.apply_stealth_async(page)
                item = await harvester.scrape_course_detail(session, page, url)
                await page.close()
            else:
                item = await harvester._scrape_http(session, url)

            if item:
                item["status"] = "pending"
                harvester._save_to_staging(item)

    if browser:
        await browser.close()
    if pw:
        await pw.stop()

    # Telemetry
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
