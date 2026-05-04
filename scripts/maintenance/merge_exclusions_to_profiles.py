import sys
import os

sys.path.insert(0, '/app')
from scripts.shared.db_client import get_db_client
from scripts.shared.utils import setup_lima_logging

logger = setup_lima_logging('merge_exclusions_to_profiles')


def merge():
    db = get_db_client()

    logger.info("=== Fase 61: Merge CE -> SP ===")

    institutions = db.select('institutions', columns='id,slug,name')
    if not institutions:
        logger.error("No institutions found")
        return

    inst_map = {i['id']: i for i in institutions}
    profiles = db.select('institution_site_profiles', columns='institution_id,exclusion_patterns,site_type,discovery_mode')
    profile_map = {p['institution_id']: p for p in profiles} if profiles else {}

    ce_rows = db.select('crawler_exclusions', filters='is_active=eq.true', columns='institution_id,pattern')
    ce_by_inst = {}
    if ce_rows:
        for r in ce_rows:
            iid = r['institution_id']
            if iid not in ce_by_inst:
                ce_by_inst[iid] = set()
            ce_by_inst[iid].add(r['pattern'])

    merged = 0
    created_profiles = 0
    summary = []

    for inst in institutions:
        iid = inst['id']
        slug = inst['slug']
        ce_set = ce_by_inst.get(iid, set())

        if iid in profile_map:
            sp_set = set(profile_map[iid].get('exclusion_patterns', []) or [])
            merged_set = ce_set | sp_set
            has_new = len(merged_set) > len(sp_set)

            if has_new:
                profile_data = dict(profile_map[iid])
                profile_data['exclusion_patterns'] = sorted(merged_set)
                profile_data['institution_id'] = iid
                db.upsert('institution_site_profiles', profile_data, on_conflict='institution_id')
                merged += 1
                logger.info(f"  {slug}: {len(sp_set)} + {len(ce_set - sp_set)} CE-only = {len(merged_set)} total")
            else:
                logger.info(f"  {slug}: {len(sp_set)} (no changes needed)")

            summary.append((slug, len(ce_set), len(sp_set), len(merged_set)))
        elif ce_set:
            logger.info(f"  {slug}: CREATING PROFILE from {len(ce_set)} CE patterns")
            profile_data = {
                'institution_id': iid,
                'site_type': 'ecommerce' if 'dmc' in slug.lower() else 'traditional_ssr',
                'discovery_mode': 'sitemap_bfs',
                'seed_urls': [],
                'exclusion_patterns': sorted(ce_set),
                'catalog_url_patterns': [],
                'catalog_max_pages': 5,
                'catalog_scroll_iterations': 0,
                'requires_stealth': False,
                'requires_cloudflare_bypass': False,
                'popup_close_selectors': [],
                'detail_wait_ms': 2000,
                'section_keywords': {},
                'field_defaults': {},
                'section_mode_map': {},
                'section_course_type_map': {},
                'title_prefix_removals': [],
                'title_split_separators': [],
                'max_courses_per_run': 500,
                'soft_delete_before_scrape': False,
            }
            db.upsert('institution_site_profiles', profile_data, on_conflict='institution_id')
            created_profiles += 1
            summary.append((slug, len(ce_set), 0, len(ce_set)))
        else:
            logger.info(f"  {slug}: NO profile, NO CE patterns (skipped)")

    logger.info(f"\n=== Summary ===")
    for slug, ce_cnt, sp_cnt, final_cnt in summary:
        logger.info(f"  {slug}: CE={ce_cnt} SP={sp_cnt} -> FINAL={final_cnt}")
    logger.info(f"\nProfiles updated: {merged}")
    logger.info(f"Profiles created: {created_profiles}")


if __name__ == '__main__':
    merge()
