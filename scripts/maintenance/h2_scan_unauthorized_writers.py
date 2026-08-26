import argparse
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ACTIVE_PATHS = (ROOT / "web/src", ROOT / "scripts/core")
ALLOWED_COURSE_WRITERS = {
    "scripts/core/sync_vector_worker.py",
    "scripts/core/integrity_ping.py",
}

LEAD_EGRESS_PATTERNS = (
    re.compile(r"rest/v1/leads", re.IGNORECASE),
    re.compile(r"/leads[`'\"]", re.IGNORECASE),
)
POST_PATTERN = re.compile(r"method\s*:\s*[`'\"]POST[`'\"]", re.IGNORECASE)
COURSE_WRITE_PATTERN = re.compile(
    r"\.\s*(?:upsert|patch|patch_raise|patch_exact_one_raise|delete)\s*\(\s*[`'\"]courses[`'\"]"
)


def scan(root: Path = ROOT) -> list[str]:
    findings: list[str] = []
    for base in ACTIVE_PATHS:
        target = root / base.relative_to(ROOT)
        if not target.exists():
            continue
        for path in sorted(target.rglob("*")):
            if path.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx"}:
                continue
            rel = path.relative_to(root).as_posix()
            text = path.read_text(encoding="utf-8-sig")
            if any(pattern.search(text) for pattern in LEAD_EGRESS_PATTERNS) and POST_PATTERN.search(text):
                findings.append(f"{rel}: public lead egress is forbidden")
            if COURSE_WRITE_PATTERN.search(text) and rel not in ALLOWED_COURSE_WRITERS:
                findings.append(f"{rel}: unauthorized courses writer")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan active H2 surfaces for forbidden writers")
    parser.parse_args()
    findings = scan()
    if findings:
        for finding in findings:
            print(finding)
        return 1
    print("h2 writer scan passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
