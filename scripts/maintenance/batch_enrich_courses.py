import sys
import os
import json
import time
import requests
import argparse
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bs4 import BeautifulSoup
from shared.db_client import get_db_client
from shared.utils import setup_lima_logging
from core.enrichment_worker import EnrichmentWorker

logger = setup_lima_logging("BatchEnricher")

def list_to_str(val):
    if isinstance(val, list):
        return ', '.join([str(v) for v in val if v])
    return str(val) if val else ''

def apply_validations(enriched, course_name):
    # official_name
    official_name = enriched.get("official_name")
    if not official_name or str(official_name).strip().lower() in ('none', 'null', 'nan', '') or len(str(official_name).strip()) < 3:
        enriched["official_name"] = course_name

    # modality
    modality_raw = enriched.get("modality")
    modality_norm = str(modality_raw).strip() if modality_raw else ""
    modality_map = {"presencial": "Presencial", "remoto": "Remoto", "virtual": "Remoto",
                    "online": "Remoto", "hibrido": "Híbrido", "híbrido": "Híbrido",
                    "semipresencial": "Híbrido", "blend": "Híbrido"}
    if modality_norm.lower() in modality_map:
        enriched["modality"] = modality_map[modality_norm.lower()]
    elif not modality_norm or modality_norm.lower() in ('none', 'null', 'nan', ''):
        enriched["modality"] = "Presencial"
    elif modality_norm not in ("Presencial", "Remoto", "Híbrido"):
        enriched["modality"] = "Presencial"

    # total_cost_est
    cost_raw = enriched.get("total_cost_est")
    if cost_raw is not None and str(cost_raw).strip().lower() not in ('none', 'null', 'nan', ''):
        try:
            cost_str = str(cost_raw).replace("S/", "").replace("s/", "").replace("PEN", "").replace("pen", "")
            cost_str = cost_str.replace("soles", "").replace("Soles", "").replace(",", "").strip()
            enriched["total_cost_est"] = float(cost_str)
        except (ValueError, TypeError):
            enriched["total_cost_est"] = None
    else:
        enriched["total_cost_est"] = None

    # start_date
    sd = enriched.get("start_date")
    if sd and str(sd).strip().lower() in ('none', 'null', 'nan', ''):
        enriched["start_date"] = None

    # duration_months
    dm_raw = enriched.get("duration_months")
    dm_val = 0
    if dm_raw is not None:
        try:
            dm_val = int(float(dm_raw))
        except (ValueError, TypeError):
            dm_val = 0
    enriched["duration_months"] = dm_val

    return enriched


def enrich_course(worker, db, course):
    """Enrich a single course by fetching HTML and running LLM extraction."""
    url = course.get('url')
    if not url:
        logger.warning(f"Course {course.get('id','?')} has no URL, skipping")
        return False

    name = course.get('name') or "Programa Pendiente"

    try:
        # Fetch HTML
        logger.info(f"Fetching {url[:80]}...")
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=20)
        if resp.status_code != 200:
            logger.warning(f"HTTP {resp.status_code} for {url[:80]}")
            return False

        soup = BeautifulSoup(resp.text, 'html.parser')
        [x.decompose() for x in soup(['script', 'style', 'nav', 'header', 'footer'])]
        text = soup.get_text(separator=' ', strip=True)[:1200]

        if len(text) < 50:
            logger.warning(f"Too little content ({len(text)} chars) for {url[:80]}")
            return False

        # Run enrichment
        enriched = worker._call_llm_for_pillars(name, text)
        if not enriched:
            logger.warning(f"LLM returned None for {url[:80]}")
            return False

        enriched = apply_validations(enriched, name)

        # Build patch data
        patch_data = {
            'name': enriched.get('official_name'),
            'price_pen': enriched.get('total_cost_est'),
            'mode': enriched.get('modality'),
            'duration': enriched.get('duration_text'),
            'start_date_text': enriched.get('start_date'),
            'description_long': enriched.get('ai_summary'),
            'syllabus': json.dumps(enriched.get('curriculum_summary', {})),
            'objectives': enriched.get('graduate_profile'),
            'target_audience': enriched.get('graduate_profile'),
            'course_type': enriched.get('degree_type'),
            'requirements': list_to_str(enriched.get('requirements'))
        }
        patch_data = {k: v for k, v in patch_data.items() if v is not None and v != ''}

        # Patch course
        result = db.patch('courses', filters=f'id=eq.{course["id"]}', data=patch_data)
        if result and result.get('status') == 'success':
            logger.info(f"Enriched: {patch_data.get('name', name)} | mode={patch_data.get('mode')} | cost={patch_data.get('price_pen')} | start={patch_data.get('start_date_text')}")
            return True
        else:
            logger.warning(f"Patch failed for {course['id'][:8]}")
            return False

    except Exception as e:
        logger.warning(f"Error enriching {url[:80]}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Batch enrich courses from HTML pages")
    parser.add_argument("--limit", type=int, default=20, help="Max courses to process")
    parser.add_argument("--institution-id", type=str, default=None, help="Filter by institution_id")
    parser.add_argument("--null-name-only", action="store_true", help="Only process courses with NULL name")
    args = parser.parse_args()

    worker = EnrichmentWorker()
    db = get_db_client()

    # Build filter
    filters = []
    if args.institution_id:
        filters.append(f"institution_id=eq.{args.institution_id}")
    if args.null_name_only:
        filters.append("name=is.null")

    filter_str = "&".join(filters) if filters else None

    courses = db.select('courses', columns='id,name,url,institution_id', filters=filter_str, limit=args.limit)
    if not courses:
        logger.info("No courses found to enrich")
        return

    logger.info(f"Processing {len(courses)} courses...")
    enriched_count = 0
    for course in courses:
        if enrich_course(worker, db, course):
            enriched_count += 1
        time.sleep(1.5)  # Rate limit between LLM calls

    logger.info(f"Done. Enriched: {enriched_count}/{len(courses)}")


if __name__ == "__main__":
    main()
