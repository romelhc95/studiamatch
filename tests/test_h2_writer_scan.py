import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.maintenance.h2_scan_unauthorized_writers import scan


def test_current_active_surfaces_have_no_forbidden_lead_egress_or_writers() -> None:
    assert scan() == []


def test_scan_detects_public_lead_post(tmp_path: Path) -> None:
    target = tmp_path / "web/src/app"
    target.mkdir(parents=True)
    (target / "page.tsx").write_text(
        "fetch(`${SUPABASE_URL}/rest/v1/leads`, { method: 'POST' })",
        encoding="utf-8",
    )

    assert scan(tmp_path) == ["web/src/app/page.tsx: public lead egress is forbidden"]


def test_scan_detects_unapproved_courses_writer(tmp_path: Path) -> None:
    target = tmp_path / "scripts/core"
    target.mkdir(parents=True)
    (target / "rogue.py").write_text("db.patch('courses', 'id=eq.1', {})", encoding="utf-8")

    assert scan(tmp_path) == ["scripts/core/rogue.py: unauthorized courses writer"]
