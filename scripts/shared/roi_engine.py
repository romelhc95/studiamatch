SENIORITY_RULES = {
    "Doctorado": ((0, float("inf"), "Senior"),),
    "Maestria": ((500, float("inf"), "Senior"), (0, 500, "Mid")),
    "Especializacion": ((200, float("inf"), "Mid"), (0, 200, "Junior")),
    "Diplomado": ((100, float("inf"), "Mid"), (0, 100, "Junior")),
    "Certificacion": ((80, float("inf"), "Mid"), (0, 80, "Junior")),
    "Curso": ((0, float("inf"), "Junior"),),
    "Taller": ((0, float("inf"), "Junior"),),
    "Pregrado": ((0, float("inf"), "Junior"),),
}

SALARY_FACTORS = {
    "Doctorado": 1.2,
    "Maestria": 1.0,
    "Pregrado": 0.9,
    "Especializacion": 0.7,
    "Diplomado": 0.5,
    "Certificacion": 0.4,
    "Curso": 0.3,
    "Taller": 0.15,
}

SENIORITY_COLUMNS = {
    "Junior": "salary_junior",
    "Mid": "salary_average",
    "Senior": "salary_senior",
}


def normalize_course_type(course_type):
    value = str(course_type or "").strip()
    replacements = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "Á": "A",
        "É": "E",
        "Í": "I",
        "Ó": "O",
        "Ú": "U",
    }
    for source, target in replacements.items():
        value = value.replace(source, target)
    return value


def coerce_float(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def infer_seniority(course_type, duration_hours=None):
    normalized_type = normalize_course_type(course_type)
    hours = coerce_float(duration_hours)

    if hours is not None:
        for min_hours, max_hours, seniority in SENIORITY_RULES.get(normalized_type, ()):  # noqa: B007
            if min_hours <= hours <= max_hours:
                return seniority

    if normalized_type in ("Doctorado", "Maestria"):
        return "Senior"
    if normalized_type in ("Especializacion", "Diplomado", "Certificacion"):
        return "Mid"
    return "Junior"


def duration_months_to_hours(duration_months):
    months = coerce_float(duration_months)
    if months is None or months <= 0:
        return None
    return months * 160


def lookup_market_salary(db, category_id, seniority_level):
    if not category_id:
        return None

    column = SENIORITY_COLUMNS.get(seniority_level)
    if not column:
        return None

    rows = db.select(
        "market_salaries",
        filters=f"category_id=eq.{category_id}",
        columns=f"category_name,{column}",
        limit=1,
    )
    if not rows:
        return None
    return coerce_float(rows[0].get(column))


def adjust_salary_for_course_type(salary_base, course_type):
    salary = coerce_float(salary_base)
    if salary is None or salary <= 0:
        return None
    factor = SALARY_FACTORS.get(normalize_course_type(course_type), 0.3)
    return round(salary * factor, 2)


def compute_roi(price_pen, salary_base, course_type):
    price = coerce_float(price_pen)
    effective_salary = adjust_salary_for_course_type(salary_base, course_type)
    if effective_salary is None or effective_salary <= 0:
        return None, None
    if price is None or price <= 0:
        return effective_salary, None
    return effective_salary, round(price / effective_salary, 1)
