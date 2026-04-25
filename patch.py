import os
import re

file_path = 'scripts/core/universal_harvester.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update __init__ to load exclusions
init_pattern = r'self\.circuit_open = False\s+# ⏱️ TIME GUARD CONFIG'
init_replacement = '''self.circuit_open = False
        self.exclusions = self._load_exclusions()
        
        # ⏱️ TIME GUARD CONFIG'''
content = re.sub(init_pattern, init_replacement, content)

# 2. Add _load_exclusions method
load_exc_code = '''
    def _load_exclusions(self):
        try: return self.db.select('crawler_exclusions', filters="is_active=eq.true")
        except: return []

'''
content = content.replace('    def check_time_guard(self):', load_exc_code + '    def check_time_guard(self):')

# 3. Update _is_valid_crawl_url
valid_crawl_pattern = r'def _is_valid_crawl_url\(self, url\):.*?return not any\(re\.search\(p, url\.lower\(\)\) for p in self\.blacklist_patterns\)'
valid_crawl_replacement = '''def _is_valid_crawl_url(self, url):
        base_domain = urlparse(self.institution.get('website_url')).netloc
        if urlparse(url).netloc != base_domain:
            return False
            
        low_url = url.lower()
        inst_id = self.institution.get('id')
        
        # Check global and specific exclusions
        for exc in self.exclusions:
            if exc.get('institution_id') and exc['institution_id'] != inst_id: continue
            if exc['pattern'].lower() in low_url: return False
            
        # Legacy blacklist just in case
        if any(re.search(p, low_url) for p in self.blacklist_patterns):
            return False
            
        return True'''
content = re.sub(valid_crawl_pattern, valid_crawl_replacement, content, flags=re.DOTALL)

# 4. Update _load_existing_urls to ignore 'processed' and 'discarded' only
load_existing_pattern = r'def _load_existing_urls\(self\):.*?return set\(\)'
load_existing_replacement = '''def _load_existing_urls(self):
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
        return set()'''
content = re.sub(load_existing_pattern, load_existing_replacement, content, flags=re.DOTALL)

# 5. Remove _is_potential_course_url
content = re.sub(r'\s*def _is_potential_course_url\(self, url\):.*?return any\(k in url\.lower\(\) for k in keywords\)', '', content, flags=re.DOTALL)

# 6. Replace references to _is_potential_course_url with _is_valid_crawl_url
content = content.replace('self._is_potential_course_url(link)', 'self._is_valid_crawl_url(link)')

# 7. Update scrape_course_detail for double layer check
scrape_pattern = r'(has_changed, content_hash = await self\._check_if_changed\(url, response\.text, eff_url, can_url\))'
scrape_replacement = '''# Double Layer Exclusion Check (Post-Scrape)
            if eff_url and not self._is_valid_crawl_url(eff_url):
                logger.info(f"Skipping {url} - Redirected to excluded URL: {eff_url}")
                self.db.upsert('staging_raw', {"url": url, "institution_id": self.institution['id'], "status": "discarded", "metadata": {"discard_reason": "post_scrape_exclusion"}}, on_conflict="url")
                return None
                
            \\1'''
content = re.sub(scrape_pattern, scrape_replacement, content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Patch applied to universal_harvester.py')