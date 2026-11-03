import os
import tempfile
import unittest
from pathlib import Path

from scripts.maintenance.taxonomy_roi_audit import run_taxonomy_roi_audit


class FakeDatabase:
    def __init__(self, salaries, courses):
        self.salaries = salaries
        self.courses = courses

    def select_all(self, table, **kwargs):
        if table == "market_salaries":
            return self.salaries
        if table == "courses":
            return self.courses
        raise AssertionError(f"Unexpected table: {table}")


class TaxonomyRoiAuditPrivacyTests(unittest.TestCase):
    def test_audit_report_persists_only_aggregate_findings(self):
        database = FakeDatabase(
            salaries=[{
                "category_id": "fixture-category-id",
                "category_name": "Fixture Market Category",
                "salary_average": 5000,
                "salary_junior": 3000,
                "salary_senior": 7000,
            }],
            courses=[{
                "name": "FIXTURE PRIVATE COURSE TITLE",
                "category": "FIXTURE WRONG CATEGORY",
                "category_id": "fixture-category-id",
                "expected_monthly_salary": 1,
                "roi_months": 49,
                "seniority_level": "Junior",
                "course_type": None,
                "price_pen": 123456,
            }],
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            previous_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                run_taxonomy_roi_audit(database)
                report = Path("docs/qa-engineer/reporte_coherencia_taxonomica_v1.md").read_text()
            finally:
                os.chdir(previous_cwd)

        self.assertIn("Total Cursos Auditados:** 1", report)
        self.assertIn("Conflictos Detectados:** 1", report)
        self.assertIn("Desconexiones de categoría:** 1", report)
        self.assertIn("Salarios inconsistentes:** 1", report)
        self.assertIn("ROI atípicos:** 1", report)
        for private_marker in (
            "FIXTURE PRIVATE COURSE TITLE",
            "FIXTURE WRONG CATEGORY",
            "fixture-category-id",
            "123456",
            "S/ 1",
        ):
            self.assertNotIn(private_marker, report)


    def test_audit_report_keeps_zero_conflict_summary(self):
        database = FakeDatabase(
            salaries=[],
            courses=[{"category_id": "unknown", "category": "Unknown", "roi_months": 12}],
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            previous_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                run_taxonomy_roi_audit(database)
                report = Path("docs/qa-engineer/reporte_coherencia_taxonomica_v1.md").read_text()
            finally:
                os.chdir(previous_cwd)

        self.assertIn("Total Cursos Auditados:** 1", report)
        self.assertIn("Conflictos Detectados:** 0", report)
        for label in (
            "Desconexiones de categoría",
            "Salarios inconsistentes",
            "ROI atípicos",
        ):
            self.assertIn(f"{label}:** 0", report)


if __name__ == "__main__":
    unittest.main()
