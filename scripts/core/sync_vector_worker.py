import os
import json
import logging
import sys
import re
import requests
from datetime import datetime, timezone
from typing import List
from urllib.parse import urlparse
from dotenv import load_dotenv

try:
    import regex as safe_regex
except ImportError:
    safe_regex = None

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.utils import slugify, setup_lima_logging, TimeGuard, parse_start_date
from shared.db_client import get_db_client
from shared.roi_engine import compute_roi, duration_months_to_hours, infer_seniority, lookup_market_salary

# Setup logging
load_dotenv()
logger = setup_lima_logging("SyncVectorWorker")

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Supabase credentials are now handled by db_client

class SyncVectorWorker:
    def __init__(self):
        self.db = get_db_client()
        self.profiles = self._load_profiles()
        # Fase 100: pipeline_enabled supersedes pipeline_ready, with temporary fallback.
        self.ready_inst_ids = {
            str(p['institution_id']) for p in self.profiles
            if isinstance(p, dict) and self._gate_enabled(p, 'pipeline_enabled')
        }
        # Fase 79C: Noise patterns cargados desde DB con fallback hardcodeado.
        # NOTA: Ya no se cargan globalmente — se obtienen por institución vía
        # _get_noise_patterns_for_inst() para que patrones de una institución
        # no afecten a otras.
        self.default_noise_patterns = [
            re.compile(r'agradecimiento', re.IGNORECASE),
            re.compile(r'thank.?\s*you', re.IGNORECASE),
            re.compile(r'^https?://[^/]+/?$'),
            re.compile(r'/facultad-de-[^/]+/?$'),
            re.compile(r'matr[ií]cul', re.IGNORECASE),
            re.compile(r'inscr[ií]b', re.IGNORECASE),
        ]

    def _load_profiles(self):
        try:
            return self.db.select_pipeline('institution_site_profiles') or []
        except Exception as e:
            logger.warning(f"Error loading site profiles: {e}")
            return []

    def _get_profile(self, institution_id):
        for p in self.profiles:
            if str(p.get('institution_id')) == str(institution_id):
                return p
        return {}

    @staticmethod
    def _gate_enabled(profile, gate_name):
        if gate_name in profile:
            return bool(profile.get(gate_name))
        return bool(profile.get('pipeline_ready'))

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
        logger.warning("Profile regex rejected because safe regex engine is unavailable")
        return None

    def _get_noise_patterns_for_inst(self, inst_id) -> List[re.Pattern]:
        """
        Retorna noise patterns COMPILADOS de la institución específica.
        Si la institución no tiene patrones, usa fallback hardcodeado.
        Esto evita que patrones de una institución afecten a otras.
        Genérico: funciona para cualquier institución.
        """
        profile = self._get_profile(inst_id) if inst_id else {}
        patterns = profile.get('noise_patterns', []) if isinstance(profile, dict) else []
        if isinstance(patterns, list) and len(patterns) > 0:
            validated = []
            for pat in patterns:
                if not isinstance(pat, str):
                    continue
                if not self._is_safe_profile_regex(pat):
                    logger.warning(f"ReDoS-risk noise pattern rejected: {pat}")
                    continue
                try:
                    validated.append(pat)
                except re.error as e:
                    logger.warning(f"Invalid noise regex '{pat}': {e}")
                    continue
            if validated:
                return validated
        return list(self.default_noise_patterns)

    @staticmethod
    def _curriculum_to_text(curriculum_summary):
        """Convert enrichment JSON into plain text accepted by courses.syllabus."""
        if not curriculum_summary:
            return None
        if isinstance(curriculum_summary, str):
            stripped = curriculum_summary.strip()
            if not stripped or stripped in ("{}", "[]"):
                return None
            try:
                curriculum_summary = json.loads(stripped)
            except json.JSONDecodeError:
                return stripped
        if isinstance(curriculum_summary, dict):
            pilares = curriculum_summary.get('pilares')
            if isinstance(pilares, list):
                lines = [f"- {str(item).strip()}" for item in pilares if str(item or '').strip()]
                return "\n".join(lines) if lines else None
            values = [str(v).strip() for v in curriculum_summary.values() if isinstance(v, str) and v.strip()]
            return "\n".join(values) if values else None
        if isinstance(curriculum_summary, list):
            lines = [f"- {str(item).strip()}" for item in curriculum_summary if str(item or '').strip()]
            return "\n".join(lines) if lines else None
        return str(curriculum_summary).strip() or None

    def get_pending_enriched(self, limit=500):
        if not self.ready_inst_ids:
            return []
        inst_ids = ",".join(sorted(self.ready_inst_ids))
        filters = f"status=eq.pending&institution_id=in.({inst_ids})"
        return self.db.select_pipeline('enriched_programs', filters=filters, limit=limit)

    def sync_to_production(self, enriched):
        e_id = enriched['id']
        raw_name = enriched.get('official_name')
        url = enriched['url']

        # Fase 100: skip si la institucion no tiene pipeline habilitado
        inst_id = enriched.get('institution_id')
        if inst_id and str(inst_id) not in self.ready_inst_ids:
            logger.warning(f"⏭️ SKIP enriched {e_id}: institution {inst_id} pipeline_enabled=false")
            self.update_enriched_status(e_id, "skipped", error_msg="pipeline_enabled=false")
            return False

        # Fase 75: Post-sync noise validation (per-institution, no global)
        noise_patterns = self._get_noise_patterns_for_inst(inst_id)
        for pat in noise_patterns:
            try:
                if isinstance(pat, re.Pattern):
                    matched = pat.search(str(url or '')[:2000]) or pat.search(str(raw_name or '')[:2000])
                    pat_label = pat.pattern
                else:
                    matched = self._safe_profile_search(pat, str(url or '')) or self._safe_profile_search(pat, str(raw_name or ''))
                    pat_label = pat
                if matched:
                    logger.warning(f"⏭️ SKIP enriched {e_id}: noise pattern '{pat_label}' matched on '{raw_name}'")
                    self.update_enriched_status(e_id, "error", error_msg=f"noise_pattern:{pat_label}")
                    return False
            except re.error:
                continue

        # Validate name: reject None, "None", empty, or too-short names
        if not raw_name or str(raw_name).strip().lower() in ('none', 'null', 'nan', '') or len(str(raw_name).strip()) < 3:
            logger.warning(f"Skipping record {e_id}: invalid official_name '{raw_name}'")
            self.update_enriched_status(e_id, "error", error_msg="invalid_name")
            return False

        name = str(raw_name).strip()
        logger.info(f"Syncing to Production: {name}")

        # Map Enriched Pillars to Courses Schema with robust list handling
        def list_to_str(val):
            if isinstance(val, list):
                return ", ".join([str(v) for v in val if v])
            return str(val) if val else ""

        # Generate unique slug (include location and short ID if needed)
        base_slug = slugify(name)

        # Fallback: if slugify returns empty (non-ASCII names), use last URL segment
        if not base_slug:
            url = enriched.get('url', '')
            if url:
                last_segment = urlparse(url).path.strip('/').split('/')[-1]
                base_slug = slugify(last_segment)
                logger.warning(f"Empty name slug for '{name}', using URL fallback: '{last_segment}' -> '{base_slug}'")
            if not base_slug:
                base_slug = 'curso'
                logger.warning(f"All slug methods failed for '{name}', using default 'curso'")

        location = enriched.get('location', 'Nacional')
        
        # Add location if specific
        if location and location not in ["Nacional", "Nacional/No especificado"]:
            base_slug = f"{base_slug}-{slugify(location)}"
        
        # Add a short unique identifier from the original ID to guarantee uniqueness
        # while keeping the URL readable
        short_id = str(e_id).split('-')[0]
        full_slug = f"{base_slug}-{short_id}"
        # Ensure slug never starts with dash
        full_slug = full_slug.lstrip('-')

        # Robust category extraction
        raw_categories = enriched.get('categories')
        main_category = None
        if isinstance(raw_categories, list) and raw_categories:
            main_category = raw_categories[0]
        elif isinstance(raw_categories, str) and raw_categories:
            main_category = raw_categories.split(',')[0].strip()

        # Fase 73: Parse start_date and determine expiration
        start_date_text = enriched.get('start_date')
        parsed_date, is_expired = parse_start_date(start_date_text)
        
        # Determine is_active: False if expired (90d grace already in parse_start_date)
        course_is_active = not is_expired
        if is_expired:
            logger.info(f"⏰ [EXPIRED] {name} — start_date='{start_date_text}' parsed as {parsed_date}, marking inactive")

        # Fase 63: Load profile defaults for this institution
        profile = self._get_profile(enriched.get('institution_id'))
        production_enabled = self._gate_enabled(profile, 'production_enabled') if profile else True
        course_is_active = course_is_active and production_enabled
        if not production_enabled:
            logger.info(f"🚧 [NOT PUBLIC] {name} — production_enabled=false, syncing inactive")
        defaults = profile.get('field_defaults', {}) if profile else {}
        section_mode_map = profile.get('section_mode_map', {}) if profile else {}

        # Apply section_mode_map: derive mode from URL path
        resolved_mode = enriched.get('modality') or defaults.get('mode')
        if not enriched.get('modality') and section_mode_map:
            course_url = enriched.get('url', '')
            for path_key, mode_val in section_mode_map.items():
                if path_key in course_url:
                    resolved_mode = mode_val
                    break

        # Normalize mode to match DB check constraint (e.g. Híbrido → Hibrido)
        if resolved_mode:
            mode_normalized = resolved_mode.lower().replace("í", "i").replace("ó", "o").replace("é", "e").replace("á", "a").replace("ú", "u")
            if mode_normalized == "hibrido":
                resolved_mode = "Hibrido"

        duration_hours = enriched.get('duration_hours') or duration_months_to_hours(enriched.get('duration_months'))
        seniority_level = infer_seniority(enriched.get('degree_type'), duration_hours)

        course_data = {
            "institution_id": enriched['institution_id'],
            "name": name,
            "slug": full_slug,
            "url": url,
            "price_pen": enriched.get('total_cost_est'),
            "price_status": defaults.get('price_status', 'publicado') if not enriched.get('total_cost_est') else 'publicado',
            "mode": resolved_mode,
            "duration": enriched.get('duration_text') or enriched.get('duration'),
            "start_date_text": start_date_text,
            "start_date": parsed_date.isoformat() if parsed_date else None,
            "description_long": enriched.get('ai_summary'),
            "requirements": list_to_str(enriched.get('requirements')),
            "objectives": enriched.get('graduate_profile'),
            "target_audience": enriched.get('graduate_profile'),
            "syllabus": self._curriculum_to_text(enriched.get('curriculum_summary')),
            "brochure_url": enriched.get('brochure_url'),
            "certification": "",
            "seniority_level": seniority_level,
            "course_type": enriched.get('degree_type'),
            "category": main_category,
            "is_active": course_is_active,
            "is_verified": True,
            "last_scraped_at": datetime.now(timezone.utc).isoformat(),
            "provider_used": enriched.get('provider_used', 'mock'),
            "is_mock_data": enriched.get('is_mock_data', True)
        }

        # Generate Embedding (Placeholder for OpenAI call)
        # course_data["embedding"] = self._generate_embedding(course_data["description_long"])

        # Check if course was manually deactivated (don't reactivate)
        url_encoded = url.replace("'", "''")
        existing = self.db.select('courses', filters=f"url=eq.{url_encoded}", columns='id,is_active')
        if existing and len(existing) > 0 and existing[0].get('is_active') == False:
            logger.info(f"⏭️ [SKIP] {name} — manually deactivated, skipping sync")
            self.update_enriched_status(e_id, "synced")
            return True

        # Upsert to production courses
        res = self.db.upsert('courses', course_data, on_conflict="url")

        if res:
            synced_course = res[0] if isinstance(res, list) and res else res
            if isinstance(synced_course, dict):
                salary_base = lookup_market_salary(self.db, synced_course.get('category_id'), seniority_level)
                expected_salary, roi_months = compute_roi(
                    enriched.get('total_cost_est'),
                    salary_base,
                    enriched.get('degree_type'),
                )
                roi_payload = {"seniority_level": seniority_level}
                if expected_salary is not None:
                    roi_payload["expected_monthly_salary"] = expected_salary
                    roi_payload["roi_months"] = roi_months
                course_id = synced_course.get('id')
                if course_id:
                    roi_res = self.db.patch('courses', filters=f"id=eq.{course_id}", data=roi_payload)
                    if not roi_res or roi_res.get("status") != "success":
                        logger.error(f"Error updating ROI fields for course {course_id}")
                        self.update_enriched_status(e_id, "error", error_msg="roi_patch_failed")
                        return False
            logger.info(f"Successfully synced to production courses: {name}")
            self.update_enriched_status(e_id, "synced")
            return True
        else:
            logger.error(f"Error syncing to production")
            self.update_enriched_status(e_id, "error", error_msg="DB Error")
            return False

    def update_enriched_status(self, e_id, status, error_msg=None):
        payload = {"status": status}
        if error_msg: payload["metadata"] = {"error": error_msg}
        self.db.patch('enriched_programs', filters=f"id=eq.{e_id}", data=payload)

if __name__ == "__main__":
    worker = SyncVectorWorker()
    guard = TimeGuard(max_seconds=1800, logger=logger)
    pending = worker.get_pending_enriched()
    logger.info(f"Found {len(pending)} pending enriched records.")
    synced = 0
    for record in pending:
        if guard.should_exit:
            logger.warning(f"⚠️ [TIME_GUARD] Shutdown durante sync. Synced: {synced}/{len(pending)}")
            break
        if worker.sync_to_production(record):
            synced += 1
        guard.tick(every=50)
    logger.info(f"Sync batch complete. Synced: {synced}/{len(pending)} | Time: {guard.elapsed_hours:.2f}h")
