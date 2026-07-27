import os
import re
import sys
from collections import Counter

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.db_client import get_db_client


STOPWORDS = {
    "curso", "cursos", "taller", "programa", "programas", "diplomado",
    "especializacion", "especialización", "maestria", "maestría", "doctorado",
    "de", "del", "la", "las", "los", "el", "en", "y", "para", "con",
    "por", "nivel", "basico", "básico", "avanzado", "online", "virtual",
}

PUBLIC_COURSE_FILTERS = (
    "is_active=eq.true&is_verified=eq.true&publication_status=eq.publicado"
)


def _load_public_visible_courses(database):
    profiles = database.select_all_service(
        "institution_site_profiles",
        filters="production_enabled=eq.true",
        columns="institution_id",
        batch_size=1000,
    )
    production_institution_ids = {
        str(profile.get("institution_id"))
        for profile in profiles
        if profile.get("institution_id")
    }
    courses = database.select_all_service(
        "courses",
        filters=PUBLIC_COURSE_FILTERS,
        columns="id,name,institution_id,category_confirmed",
        batch_size=1000,
    )
    return [
        course
        for course in courses
        if str(course.get("institution_id")) in production_institution_ids
    ]


def tokenize(text):
    return [
        token.lower()
        for token in re.findall(r"[A-Za-zÁÉÍÓÚáéíóúÑñ0-9]{3,}", text or "")
        if token.lower() not in STOPWORDS
    ]


def audit():
    db = get_db_client()
    courses = _load_public_visible_courses(db)
    total = len(courses)
    uncategorized = [course for course in courses if course.get("category_confirmed") is not True]
    categorized = total - len(uncategorized)
    coverage = (categorized / total * 100) if total else 100.0

    print(f"Category coverage: {coverage:.1f}% ({categorized}/{total})")

    if uncategorized:
        print("\nUncategorized active courses:")
        for course in uncategorized[:20]:
            print(f"  - {course.get('name')}")

        known_rules = db.select_all_service(
            "category_rules", columns="keyword", batch_size=1000
        )
        known_keywords = {str(row.get("keyword", "")).lower() for row in known_rules}
        token_counts = Counter(
            token
            for course in uncategorized
            for token in tokenize(course.get("name"))
            if token not in known_keywords
        )
        if token_counts:
            print("\nCandidate missing keywords:")
            for token, count in token_counts.most_common(20):
                print(f"  - {token}: {count}")

    if coverage < 80:
        return 2
    if coverage < 90:
        print("\nWARNING: category coverage is below 90%.")
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(audit())
