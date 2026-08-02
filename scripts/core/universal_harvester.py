import asyncio
import os
import json
import logging
import re
import sys
import hashlib
import random
from datetime import datetime, timezone
from urllib.parse import quote, urljoin, urlparse
import xml.etree.ElementTree as ET

import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from curl_cffi.requests import AsyncSession
from dotenv import load_dotenv

try:
    import regex as safe_regex
except ImportError:
    safe_regex = None

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
from shared.db_client import DatabaseAPIError, get_db_client

logger = setup_lima_logging("UniversalHarvester")
load_dotenv()

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


DISCOVERED_STATUS = "discovered"
PROTECTED_STAGING_STATUSES = frozenset({
    "pending",
    "processing",
    "processed",
    "discarded",
    "skipped",
    "error",
})
KNOWN_STAGING_STATUSES = PROTECTED_STAGING_STATUSES | {DISCOVERED_STATUS}


class HarvesterRunError(RuntimeError):
    """Raised when FG2 cannot prove a safe complete outcome."""


class HarvesterPartialError(HarvesterRunError):
    """Raised for a per-URL failure that must preserve the source state."""


class UniversalHarvester:
    def __init__(self, institution, global_start=None):
        import time
        self.institution = institution
        self.db = get_db_client()
        self.visited_urls = set()
        self.course_urls = set()
        self._resumable_urls = []
        self._discovered_rows_by_url = {}
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
        self.discovery_mode = self.profile.get('discovery_mode', 'sitemap_bfs') if self.profile else 'sitemap_bfs'
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
        # Fase 79B: Circuit Breaker
        self.max_consecutive_errors = self.profile.get('max_consecutive_errors', self.BLOCK_THRESHOLD) if self.profile else self.BLOCK_THRESHOLD
        db_circuit_open = self.profile.get('circuit_open', False) if self.profile else False
        db_circuit_opened_at = self.profile.get('circuit_opened_at') if self.profile else None
        if db_circuit_open and db_circuit_opened_at:
            opened = db_circuit_opened_at
            if isinstance(opened, str):
                opened = datetime.fromisoformat(opened.replace('Z', '+00:00'))
            hours_since = (datetime.now(timezone.utc) - opened).total_seconds() / 3600
            if hours_since < 24:
                self.circuit_open = True
                logger.warning(f"Circuito abierto para {self.institution.get('name')} (abierto hace {hours_since:.1f}h). Saltando.")
            else:
                logger.info(f"Circuito auto-cerrado para {self.institution.get('name')} (>24h desde apertura).")
                try:
                    self.db.patch('institution_site_profiles', filters=f"institution_id=eq.{self.institution.get('id')}", data={'circuit_open': False, 'circuit_opened_at': None})
                except Exception:
                    pass

        # ⏱️ TIME GUARD CONFIG
        self.global_start = global_start or time.time()
        self.MAX_RUN_TIME = 20400

    @staticmethod
    def _normalize_jsonb_list(value):
        """Convert JSONB string to list if needed (Bug 5 defensive fix)."""
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return parsed
            except (json.JSONDecodeError, TypeError):
                pass
            return []
        if isinstance(value, list):
            return value
        return [] if value is None else value

    @staticmethod
    def _is_safe_profile_regex(pattern):
        if not isinstance(pattern, str) or len(pattern) > 200:
            return False
        unsafe = [r'(\([^)]*[*+][^)]*\))+[*+]', r'\\[1-9]', r'\(\?([=!<])']
        return not any(re.search(expr, pattern) for expr in unsafe)

    @staticmethod
    def _safe_profile_search(pattern, text):
        text = str(text or '')[:2000]
        if safe_regex:
            try:
                return safe_regex.search(pattern, text, safe_regex.IGNORECASE, timeout=0.05)
            except TimeoutError:
                logger.warning(f"Profile regex timed out and was rejected: {pattern}")
                return None
            except Exception as e:
                logger.warning(f"Profile regex rejected: {pattern} ({e})")
                return None
        return re.search(pattern, text, re.IGNORECASE)

    def _load_site_profile(self):
        inst_id = self.institution.get('id')
        profiles = self.db.select_pipeline_raise(
            'institution_site_profiles',
            filters=f'institution_id=eq.{inst_id}',
            limit=1,
        )
        if profiles and len(profiles) > 0:
            profile = profiles[0]
            has_site_type = profile.get('site_type')
            has_discovery = profile.get('discovery_mode')
            if has_site_type and has_discovery:
                norm_fields = ['catalog_url_patterns', 'exclusion_patterns',
                               'allowed_url_patterns', 'seed_urls']
                for field in norm_fields:
                    if field in profile:
                        profile[field] = self._normalize_jsonb_list(profile[field])
                logger.info(f"Loaded site profile: site_type={profile.get('site_type')}, discovery_mode={profile.get('discovery_mode')}")
                return profile
            logger.info(f"Profile exists but incomplete for {self.institution.get('slug')}, will auto-detect.")
        return self._auto_detect_profile()

    def _auto_detect_profile(self):
        """Fase 121: Auto-detecta tipo de sitio cuando no hay perfil configurado."""
        try:
            from shared.site_diagnostics import diagnose_site
        except ImportError:
            logger.warning("site_diagnostics module not available, skipping auto-detection")
            return {}

        inst_name = self.institution.get('name', '')
        inst_slug = self.institution.get('slug', '')
        website_url = self.institution.get('website_url', '')
        inst_id = self.institution.get('id')

        if not website_url:
            logger.warning(f"No website_url for {inst_name}, skipping auto-detection")
            return {}

        logger.info(f"Auto-detecting profile for {inst_slug} ({inst_name}) from {website_url}")
        try:
            diag = diagnose_site(website_url, logger=logger)
        except Exception as e:
            logger.warning(f"Auto-diagnosis failed for {inst_slug}: {e}")
            return {}

        if 'error' in diag:
            logger.warning(f"Auto-diagnosis error for {inst_slug}: {diag['error']}")
            return {}

        profile = diag.get('institution_site_profile', {})
        profile['institution_id'] = inst_id
        profile['auto_generated'] = True
        profile['pipeline_ready'] = False

        existing = self.db.select_pipeline_raise(
            'institution_site_profiles',
            filters=f'institution_id=eq.{inst_id}',
            limit=1,
        )
        try:
            if existing:
                self.db.patch('institution_site_profiles',
                              filters=f'institution_id=eq.{inst_id}',
                              data=profile)
                logger.info(f"Updated auto-generated profile for {inst_slug}")
            else:
                self.db.insert('institution_site_profiles', profile)
                logger.info(f"Created auto-generated profile for {inst_slug}")
        except Exception as e:
            logger.warning(f"Could not save auto-generated profile for {inst_slug}: {e}")

        confidence = diag.get('_confidence', {})
        confidence_str = ", ".join(confidence.get('needs_manual_review', []))
        logger.info(f"Auto-detected: site_type={profile.get('site_type')}, discovery_mode={profile.get('discovery_mode')}, confidence={confidence.get('site_type', '?')}, needs_review: [{confidence_str}]")

        return profile

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
                                compiled.append(('re', pat))
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

    def _gate_enabled(self, gate_name):
        if not self.profile:
            return False
        if gate_name in self.profile:
            return bool(self.profile.get(gate_name))
        return bool(self.profile.get('pipeline_ready'))

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

    async def _check_if_changed(self, url, html_content, effective_url=None, canonical_url=None, force_changed=False):
        content_hash = self._generate_hash(html_content)
        if force_changed:
            return True, content_hash
        try:
            ids = [url, effective_url, canonical_url]
            ids = [normalize_url(i) for i in ids if i]
            data = self.db.select_pipeline_raise(
                "staging_raw",
                filters=f"url=eq.{quote(normalize_url(url), safe='')}",
                columns="content_hash",
            )
            if data and len(data) > 0:
                old_hash = data[0].get('content_hash')
                if old_hash == content_hash:
                    return False, content_hash
        except Exception as exc:
            raise DatabaseAPIError(
                "Backend read failed while checking staging content hash"
            ) from exc
        return True, content_hash

    def _is_html_response(self, response):
        headers = getattr(response, "headers", {}) or {}
        content_type = ""
        if isinstance(headers, dict):
            content_type = headers.get("content-type") or headers.get("Content-Type") or ""
        if content_type and "html" not in str(content_type).lower():
            return False
        text = getattr(response, "text", "") or ""
        lowered = text[:1000].lower()
        return "<html" in lowered or "<!doctype html" in lowered

    async def _safe_request(self, session, url):
        try:
            await asyncio.sleep(random.uniform(2, 5))
            resp = await session.get(url, impersonate=self.impersonate, timeout=25)
            # Fase 79B: Circuit Breaker — detectar 403/429
            if resp and resp.status_code in (403, 429):
                self.error_count += 1
                logger.warning(f"HTTP {resp.status_code} para {url} (error #{self.error_count}/{self.max_consecutive_errors})")
                if self.error_count >= self.max_consecutive_errors:
                    logger.error(f"DEMASIOADOS ERRORES ({self.error_count}). Abriendo circuito para {self.institution.get('name')}.")
                    self.circuit_open = True
                    try:
                        self.db.patch('institution_site_profiles', filters=f"institution_id=eq.{self.institution.get('id')}", data={'circuit_open': True, 'circuit_opened_at': datetime.now(timezone.utc).isoformat()})
                    except Exception as e:
                        logger.warning(f"No se pudo actualizar circuit_open en DB: {e}")
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

    async def _bfs_crawl(self, start_url, existing_urls):
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
                            normalized = normalize_url(link)
                            if normalized not in self.course_urls and normalized not in existing_urls:
                                row = self._save_discovered_url(normalized)
                                if row["status"] == DISCOVERED_STATUS:
                                    self.course_urls.add(normalized)
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
            if isinstance(exc, tuple) and exc[0] == 're':
                if self._safe_profile_search(exc[1], low_url):
                    return False
            elif isinstance(exc, re.Pattern):
                if exc.search(low_url[:2000]):
                    return False
            elif isinstance(exc, str):
                if exc in low_url:
                    return False
        allowed = self.profile.get('allowed_url_patterns', []) if self.profile else []
        if allowed:
            for pattern in allowed:
                if isinstance(pattern, str):
                    if pattern.startswith('re:'):
                        pat = pattern[3:]
                        if not self._is_safe_profile_regex(pat):
                            logger.warning(f"ReDoS-risk allowed pattern rejected: {pat}")
                            continue
                        try:
                            if self._safe_profile_search(pat, parsed_path):
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

    def _merge_resumable_urls(self, urls):
        final_urls = []
        for url in self._resumable_urls + list(urls):
            normalized = normalize_url(url)
            if normalized not in final_urls:
                final_urls.append(normalized)
        return final_urls

    def _remember_discovered_row(self, row):
        normalized = normalize_url(row.get('url') or '')
        self._discovered_rows_by_url[normalized] = {
            "id": row.get('id'),
            "url": normalized,
            "status": row.get('status'),
        }

    def _select_staging_rows_by_url(self, url):
        try:
            rows = self.db.select_pipeline_raise(
                "staging_raw",
                filters=f"url=eq.{quote(normalize_url(url), safe='')}",
                columns="id,url,status,institution_id",
            )
        except Exception as exc:
            raise HarvesterRunError("failed to verify URL ownership") from exc
        if not isinstance(rows, list):
            raise HarvesterRunError("malformed URL ownership payload")
        return rows

    def _discovered_row_for_url(self, url):
        normalized = normalize_url(url)
        row = self._discovered_rows_by_url.get(normalized)
        if row:
            return row
        rows = self.db.select_pipeline_raise(
            "staging_raw",
            filters=(
                f"institution_id=eq.{quote(str(self.institution['id']), safe='')}"
                f"&url=eq.{quote(normalized, safe='')}"
                "&status=eq.discovered"
            ),
            columns="id,url,status",
            limit=2,
        )
        if len(rows) != 1:
            raise HarvesterRunError(f"expected exactly one discovered row for {normalized}, got {len(rows)}")
        self._remember_discovered_row(rows[0])
        return self._discovered_rows_by_url[normalized]

    def _validate_pending_payload(self, row, item):
        if not isinstance(item, dict):
            raise HarvesterPartialError("pending payload is malformed")
        url = normalize_url(item.get("url") or "")
        if url != normalize_url(row.get("url") or ""):
            raise HarvesterPartialError("pending payload URL does not match discovered row")
        if item.get("institution_id") != self.institution.get("id"):
            raise HarvesterPartialError("pending payload institution mismatch")
        if item.get("status") != "pending":
            raise HarvesterPartialError("pending payload status is not pending")
        raw_html = item.get("raw_html")
        raw_name = item.get("raw_name")
        content_hash = item.get("content_hash")
        if not isinstance(raw_html, str) or not raw_html.strip():
            raise HarvesterPartialError("pending payload raw_html is empty")
        if "<html" not in raw_html[:1000].lower() and "<!doctype html" not in raw_html[:1000].lower():
            raise HarvesterPartialError("pending payload raw_html is not HTML")
        if not isinstance(raw_name, str) or not raw_name.strip():
            raise HarvesterPartialError("pending payload raw_name is empty")
        if not isinstance(content_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", content_hash):
            raise HarvesterPartialError("pending payload content_hash is invalid")
        if content_hash != self._generate_hash(raw_html):
            raise HarvesterPartialError("pending payload content_hash does not match raw_html")

    def _promote_discovered_to_pending(self, row, item):
        self._validate_pending_payload(row, item)
        expected_id = row["id"]
        filters = (
            f"id=eq.{quote(str(expected_id), safe='')}"
            f"&institution_id=eq.{quote(str(self.institution['id']), safe='')}"
            "&status=eq.discovered"
        )
        promoted = self.db.patch_exact_one_raise("staging_raw", filters, item, expected_id)
        if promoted.get("status") != "pending":
            raise HarvesterRunError("pending promotion did not persist pending status")
        if promoted.get("institution_id") != self.institution.get("id"):
            raise HarvesterRunError("pending promotion changed institution")
        self._discovered_rows_by_url.pop(normalize_url(item["url"]), None)
        return promoted

    async def _load_existing_urls(self, pipeline_enabled=None):
        inst_id = self.institution.get('id')
        if pipeline_enabled is None:
            pipeline_enabled = self._gate_enabled('pipeline_enabled')
        self._resumable_urls = []
        self._discovered_rows_by_url = {}
        statuses = "discovered,pending,processing,processed,discarded,skipped,error"
        try:
            data = self.db.select_pipeline_raise(
                "staging_raw",
                filters=(
                    f"institution_id=eq.{quote(str(inst_id), safe='')}"
                    f"&status=in.({statuses})"
                ),
                columns="id,url,status",
                order="url.asc,id.asc",
            )
        except Exception as exc:
            raise HarvesterRunError("failed to load existing URLs from DB") from exc
        if not isinstance(data, list):
            raise HarvesterRunError("malformed existing URL payload")

        existing = set()
        for index, row in enumerate(data):
            if not isinstance(row, dict):
                raise HarvesterRunError(f"malformed existing URL row at {index}")
            row_id = row.get('id')
            url = row.get('url')
            status = row.get('status')
            if not isinstance(row_id, str) or not row_id:
                raise HarvesterRunError(f"malformed staging id at {index}")
            if not isinstance(url, str) or not url:
                raise HarvesterRunError(f"malformed staging URL at {index}")
            if status not in KNOWN_STAGING_STATUSES:
                raise HarvesterRunError(f"unknown staging status in URL inventory: {status}")
            normalized = normalize_url(url)
            if normalized in existing:
                raise HarvesterRunError(f"duplicate URL in staging inventory: {normalized}")
            existing.add(normalized)
            if status == DISCOVERED_STATUS:
                self._remember_discovered_row({"id": row_id, "url": normalized, "status": status})
                if pipeline_enabled:
                    self._resumable_urls.append(normalized)

        logger.info(
            "Loaded %s known staging URLs (%s resumable discovered, %s protected).",
            len(existing),
            len(self._resumable_urls),
            len(existing) - len(self._resumable_urls),
        )
        self.visited_urls.update(existing)
        return existing

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
            normalized = normalize_url(url)
            if normalized not in existing_urls and self._is_valid_crawl_url(normalized):
                row = self._save_discovered_url(normalized)
                if row["status"] == DISCOVERED_STATUS:
                    new_urls.append(normalized)
                    self.course_urls.add(normalized)
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
                            row = self._save_discovered_url(full_url)
                            if row["status"] == DISCOVERED_STATUS:
                                new_urls.append(full_url)
                                self.course_urls.add(full_url)
                    logger.debug(f"  Page {page_num}: {len(links)} links found")
        logger.info(f"Total Paginated Catalog: {len(new_urls)} NEW URLs")
        return new_urls

    async def discover_catalog_links(self, browser):
        """Discovery mode: Playwright scroll + link extraction (replaces SmartData/New Horizons).
        Navigates through seed_urls (from profile) and fallback to website_url."""
        if not browser:
            logger.warning("Catalog link extraction requires Playwright browser")
            return None
        logger.info(f"🔍 [CATALOG LINKS] Starting scroll discovery for {self.institution.get('name')}")
        existing_urls = await self._load_existing_urls()
        new_urls = []
        seed_urls = self.profile.get('seed_urls', []) if self.profile else []
        catalog_urls = list(seed_urls) if seed_urls else []
        fallback_url = self.institution.get('website_url')
        if fallback_url and fallback_url not in catalog_urls:
            catalog_urls.append(fallback_url)
        page = await browser.new_page(user_agent=get_random_user_agent())
        try:
            if self.requires_stealth and STEALTH_AVAILABLE:
                stealth_local = Stealth()
                await stealth_local.apply_stealth_async(page)
            for catalog_url in catalog_urls:
                if self.check_time_guard():
                    break
                logger.info(f"  Navigating to catalog page: {catalog_url}")
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
                                    row = self._save_discovered_url(full_url)
                                    if row["status"] == DISCOVERED_STATUS:
                                        new_urls.append(full_url)
                                        self.course_urls.add(full_url)
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
                return self._merge_resumable_urls(hardcoded_result)
        elif discovery_mode == 'paginated_catalog':
            cat_result = await self.discover_paginated_catalog(browser)
            if cat_result is not None:
                return self._merge_resumable_urls(cat_result)
        elif discovery_mode == 'catalog_link_extraction':
            cat_result = await self.discover_catalog_links(browser)
            if cat_result is not None:
                return self._merge_resumable_urls(cat_result)

        # sitemap_bfs (default)
        logger.info(f"Starting sitemap/BFS discovery for {self.institution.get('name')}")
        sitemap_url = urljoin(start_url, '/sitemap.xml')
        async with AsyncSession() as session:
            sitemap_links = await self._fetch_sitemap(session, sitemap_url)
        for link in sitemap_links:
            if self.check_time_guard(): break
            if self._is_valid_crawl_url(link):
                normalized = normalize_url(link)
                if normalized not in self.course_urls and normalized not in existing_urls:
                    row = self._save_discovered_url(normalized)
                    if row["status"] == DISCOVERED_STATUS:
                        self.course_urls.add(normalized)
        if len(self.course_urls) > 50:
            logger.info(f"🚀 [FAST PATH] Found {len(self.course_urls)} courses via Sitemap. Skipping slow BFS crawl.")
        elif not self.circuit_open:
            await self._bfs_crawl(start_url, existing_urls)
        final_urls = self._merge_resumable_urls([url for url in list(self.course_urls) if url not in existing_urls])
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
            if not response:
                raise HarvesterPartialError(f"request failed for {url}")
            if response.status_code != 200:
                raise HarvesterPartialError(f"invalid HTTP status {response.status_code} for {url}")
            if not self._is_html_response(response):
                raise HarvesterPartialError(f"non-HTML content for {url}")
            eff_url = normalize_url(response.url)
            can_url = self._extract_canonical(response.text)
            if eff_url and not self._is_valid_crawl_url(eff_url):
                raise HarvesterPartialError(f"redirected to excluded URL: {eff_url}")
            if can_url and not self._is_valid_crawl_url(can_url):
                raise HarvesterPartialError(f"canonical URL is excluded: {can_url}")
            discovered_row = self._discovered_row_for_url(url)
            has_changed, _ = await self._check_if_changed(
                url,
                response.text[:200000],
                eff_url,
                can_url,
                force_changed=discovered_row["status"] == DISCOVERED_STATUS,
            )
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

            raw_html = (await page.content())[:200000]
            if not raw_html.strip():
                raise HarvesterPartialError(f"empty rendered HTML for {url}")
            content_hash = self._generate_hash(raw_html)
            json_ld = await self._extract_json_ld(page)
            og_tags = await self._extract_og_tags(page)
            title = await self._extract_title(page, og_tags, json_ld)
            if not str(title or '').strip():
                raise HarvesterPartialError(f"empty raw_name for {url}")
            description = await self._extract_description(page, og_tags, json_ld)

            # Fase 62C: Section keywords extraction from rendered HTML
            sections = self._extract_sections(raw_html)

            # Fase 94: WooCommerce structured data extraction
            woocommerce_price = None
            woocommerce_start_date = None
            woocommerce_category = None
            # Extract price from Product JSON-LD (now a dict of blocks with 'product' key)
            product_ld = json_ld.get('product', {}) if isinstance(json_ld, dict) else {}
            if product_ld:
                offers = product_ld.get('offers')
                if isinstance(offers, list) and len(offers) > 0:
                    offer = offers[0]
                    if isinstance(offer, dict):
                        ps = offer.get('priceSpecification')
                        if isinstance(ps, list) and len(ps) > 0 and isinstance(ps[0], dict):
                            woocommerce_price = ps[0].get('price')
                if not woocommerce_price:
                    woocommerce_price = product_ld.get('price')
            # Extract start_date from data-fecha-inicio attribute via Playwright
            try:
                woocommerce_start_date = await page.evaluate('() => document.querySelector("[data-fecha-inicio]")?.getAttribute("data-fecha-inicio") || null')
            except Exception:
                pass
            # Extract category: from raw_html (breadcrumb), second choice from URL
            # Check raw_html for WooCommerce product category
            cat_match = re.search(r'categoria-produto[^"]*[/]([^/]+)', raw_html[:10000])
            if cat_match:
                woocommerce_category = cat_match.group(1).rstrip('/')
            if not woocommerce_category:
                for seg in url.split('/'):
                    if seg in ('cursos', 'diplomas', 'especializaciones', 'certificaciones'):
                        woocommerce_category = seg
                        break

            return {
                "raw_name": title,
                "url": url,
                "effective_url": eff_url,
                "canonical_url": can_url,
                "raw_description": description,
                "raw_json_ld": json_ld,
                "raw_og_tags": og_tags,
                "raw_html": raw_html,
                "content_hash": content_hash,
                "institution_id": self.institution['id'],
                "status": "pending",
                "metadata": json.dumps({
                    "extracted_sections": sections,
                    "field_defaults": self.field_defaults,
                    "woocommerce_price": woocommerce_price,
                    "woocommerce_start_date": woocommerce_start_date,
                    "woocommerce_category": woocommerce_category,
                }),
            }
        except DatabaseAPIError:
            raise
        except HarvesterRunError:
            raise
        except Exception as e:
            raise HarvesterPartialError(f"parser/browser error scraping {url}: {e}") from e

    async def _scrape_http(self, session, url):
        """Fase 62A: HTTP-only extraction for traditional_ssr sites (faster, no Playwright overhead)."""
        if self.circuit_open: return None
        logger.info(f"Scraping (HTTP) {url}")
        try:
            response = await self._safe_request(session, url)
            if not response:
                raise HarvesterPartialError(f"request failed for {url}")
            if response.status_code != 200:
                raise HarvesterPartialError(f"invalid HTTP status {response.status_code} for {url}")
            if not self._is_html_response(response):
                raise HarvesterPartialError(f"non-HTML content for {url}")
            eff_url = normalize_url(response.url)
            can_url = self._extract_canonical(response.text)
            if eff_url and not self._is_valid_crawl_url(eff_url):
                raise HarvesterPartialError(f"redirected to excluded URL: {eff_url}")
            if can_url and not self._is_valid_crawl_url(can_url):
                raise HarvesterPartialError(f"canonical URL is excluded: {can_url}")
            raw_html = response.text[:50000]
            if not raw_html.strip():
                raise HarvesterPartialError(f"empty HTML payload for {url}")
            discovered_row = self._discovered_row_for_url(url)
            has_changed, _ = await self._check_if_changed(
                url,
                raw_html,
                eff_url,
                can_url,
                force_changed=discovered_row["status"] == DISCOVERED_STATUS,
            )
            if not has_changed:
                logger.info(f"Skipping {url} - No changes.")
                return None

            html = raw_html
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
            if not title:
                raise HarvesterPartialError(f"empty raw_name for {url}")

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
                "raw_html": raw_html,
                "content_hash": self._generate_hash(raw_html),
                "institution_id": self.institution['id'],
                "status": "pending",
                "metadata": json.dumps({"extracted_sections": sections, "field_defaults": self.field_defaults}),
            }
        except DatabaseAPIError:
            raise
        except HarvesterRunError:
            raise
        except Exception as e:
            raise HarvesterPartialError(f"parser error scraping {url}: {e}") from e

    # ─────────────────────────────────────────────────────────
    # Fase 62C: Section keywords extraction from headings
    # ─────────────────────────────────────────────────────────

    def _extract_sections(self, html: str) -> dict:
        """Scan H2/H3/H4 headings and map to profile section_keywords.

        Handles Bricks/Elementor nested structures: if no direct sibling content
        is found, falls back to searching for the next content block in the
        document after the heading.
        """
        if not self.section_keywords or not html:
            return {}
        soup = BeautifulSoup(html, 'html.parser')
        result = {}
        for heading in soup.find_all(['h2', 'h3', 'h4']):
            text = heading.get_text(strip=True)
            if not text:
                continue
            text_lower = text.lower()
            for keyword, field_name in self.section_keywords.items():
                if keyword.lower() in text_lower:
                    next_el = heading.find_next_sibling()
                    content_parts = []
                    while next_el and next_el.name not in ('h2', 'h3', 'h4'):
                        if next_el.name in ('p', 'ul', 'ol', 'div'):
                            content_parts.append(next_el.get_text(strip=True))
                        next_el = next_el.find_next_sibling()
                    # Fallback: if no sibling content, try parent container
                    if not content_parts:
                        parent = heading.find_parent(['div', 'section', 'article'])
                        if parent:
                            for sibling in parent.find_next_siblings():
                                txt = sibling.get_text(strip=True)
                                if txt and len(txt) > 20:
                                    content_parts.append(txt)
                                if content_parts:
                                    break
                    if not content_parts:
                        content_parts.append(heading.get_text(strip=True))
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
        all_json = []
        for script in scripts:
            try:
                content = await script.inner_text()
                all_json.append(json.loads(content))
            except Exception:
                continue
        # Return dict with all blocks: 'product' (WooCommerce) and 'first' (Yoast fallback)
        result = {}
        for item in all_json:
            if isinstance(item, dict):
                if item.get('@type') == 'Product' or 'offers' in item:
                    result['product'] = item
                elif '@graph' in item:
                    result['seo'] = item
                    for node in item['@graph']:
                        if isinstance(node, dict) and node.get('@type') == 'Product':
                            result['product'] = node
                else:
                    result['first'] = item
        return result  # Returns dict with 'product' and/or 'seo' and/or 'first'

    async def _extract_og_tags(self, page):
        return await page.evaluate('''() => {
            const tags = {};
            document.querySelectorAll('meta[property^="og:"]').forEach(m => {
                tags[m.getAttribute('property')] = m.content;
            });
            return tags;
        }''')

    async def _extract_title(self, page, og, ld):
        # ld is a dict of blocks: {'product': ..., 'seo': ..., 'first': ...}
        ld_block = None
        if isinstance(ld, dict):
            ld_block = ld.get('seo') or ld.get('first') or ld.get('product')
        title = og.get('og:title') or (ld_block.get('name') if isinstance(ld_block, dict) else None)
        if not title:
            title = await page.title()
        return title

    async def _extract_description(self, page, og, ld):
        ld_block = None
        if isinstance(ld, dict):
            ld_block = ld.get('seo') or ld.get('first')
        desc = og.get('og:description') or (ld_block.get('description') if isinstance(ld_block, dict) else None)
        if not desc:
            desc = await page.evaluate('() => document.querySelector("meta[name=\'description\']")?.content || ""')
        return desc

    def _save_discovered_url(self, url):
        normalized = normalize_url(url)
        for row in self._select_staging_rows_by_url(normalized):
            owner = row.get("institution_id")
            status = row.get("status")
            if owner != self.institution.get('id'):
                raise HarvesterRunError(f"cross-institution URL collision for {normalized}")
            if status == DISCOVERED_STATUS:
                stored = {"id": row["id"], "url": normalized, "status": DISCOVERED_STATUS}
                self._remember_discovered_row(stored)
                return stored
            if status in PROTECTED_STAGING_STATUSES:
                return {"id": row["id"], "url": normalized, "status": status}
            raise HarvesterRunError(f"unknown staging status for {normalized}: {status}")

        inserted = self.db.insert("staging_raw", {
            "url": normalized,
            "institution_id": self.institution['id'],
            "status": DISCOVERED_STATUS,
        })
        if inserted is None:
            raise HarvesterRunError(f"failed to insert discovered URL {normalized}")
        rows = self.db.select_pipeline_raise(
            "staging_raw",
            filters=(
                f"institution_id=eq.{quote(str(self.institution['id']), safe='')}"
                f"&url=eq.{quote(normalized, safe='')}"
                "&status=eq.discovered"
            ),
            columns="id,url,status",
            limit=2,
        )
        if len(rows) != 1:
            raise HarvesterRunError(f"failed to verify discovered URL {normalized}")
        stored = {"id": rows[0]["id"], "url": normalize_url(rows[0]["url"]), "status": rows[0]["status"]}
        self._remember_discovered_row(stored)
        return stored

    def _save_to_staging(self, item):
        row = self._discovered_row_for_url(item.get("url"))
        promoted = self._promote_discovered_to_pending(row, item)
        logger.info(f"Harvested to Staging: {item['url']}")
        return promoted


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
    browser = None
    pw = None

    try:
        # Fase 75: Require profile
        if not harvester.profile:
            logger.error(f"❌ SKIP {inst['name']}: No existe entrada en institution_site_profiles. "
                         f"Crea un perfil antes de ejecutar el pipeline.")
            return 1
        if not harvester._gate_enabled('discovery_enabled'):
            logger.info(f"⏭️ SKIP {inst['name']}: discovery_enabled=false.")
            return 0
        if harvester.circuit_open:
            logger.error(f"Circuit is open for {inst['name']}; failing closed.")
            return 1
        pipeline_enabled = harvester._gate_enabled('pipeline_enabled')
        if not pipeline_enabled:
            logger.info(f"🔍 DISCOVERY-ONLY {inst['name']}: pipeline_enabled=false. "
                        f"Harvester will discover URLs into staging_raw for review. "
                        f"Cleansing/enrichment/sync will skip until pipeline_enabled=true.")

        # Fase 62A: Determine if Playwright is needed based on site_type and discovery_mode
        need_browser = (
            harvester.site_type in ('spa_js_heavy', 'ecommerce') or
            harvester.discovery_mode == 'catalog_link_extraction'
        )
        extraction_needs_browser = harvester.site_type in ('spa_js_heavy', 'ecommerce')

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

        if not pipeline_enabled:
            logger.info(f"🔍 DISCOVERY-ONLY complete for {inst['name']}: {len(urls)} URLs discovered; detail scraping skipped.")
            return 0

        failures = []
        promoted_count = 0
        async with AsyncSession() as session:
            for i, url in enumerate(urls):
                elapsed_total = time.time() - global_start
                if elapsed_total > MAX_RUN_TIME:
                    failures.append((url, "time guard reached"))
                    logger.warning(f"⚠️ [TIME GUARD] Límite de ejecución alcanzado ({elapsed_total/3600:.2f}h).")
                    break

                logger.info(f"Processing {i + 1}/{len(urls)}: {url}")
                page = None
                try:
                    if extraction_needs_browser and browser:
                        page = await browser.new_page(user_agent=get_random_user_agent())
                        if harvester.requires_stealth and STEALTH_AVAILABLE:
                            stealth = Stealth()
                            await stealth.apply_stealth_async(page)
                        item = await harvester.scrape_course_detail(session, page, url)
                    else:
                        item = await harvester._scrape_http(session, url)
                    if item:
                        item["status"] = "pending"
                        harvester._save_to_staging(item)
                        promoted_count += 1
                except Exception as exc:
                    failures.append((url, str(exc)))
                    logger.error(f"Partial harvesting failure for {url}: {exc}")
                finally:
                    if page:
                        await page.close()

        if failures:
            logger.error(f"FG2 finished PARTIAL/FAIL for {inst['name']}: {len(failures)} failures, {promoted_count} promoted.")
            return 1

        duration = int(time.time() - start_time)
        harvester.db.patch_exact_one_raise("institutions", filters=f"id=eq.{quote(str(inst['id']), safe='')}", data={
            "last_harvest_at": datetime.now().isoformat(),
            "last_harvest_duration_sec": duration
        }, expected_id=inst['id'])
        logger.info(f"✅ Telemetry updated for {inst['name']}: {duration}s")
        return 0
    except Exception as exc:
        logger.error(f"FG2 failed closed for {inst.get('name')}: {exc}")
        return 1
    finally:
        if browser:
            await browser.close()
        if pw:
            await pw.stop()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    sys.exit(asyncio.run(main()))
