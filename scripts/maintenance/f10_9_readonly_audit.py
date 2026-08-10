from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.shared.f10_9_readonly_planner import (  # noqa: E402
    PlannerInputError,
    build_readonly_manifest,
    canonical_json,
    load_snapshot,
)


DEFAULT_FIXTURE = ROOT / "tests" / "fixtures" / "f10_9_p2_synthetic.json"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the local offline F10.9 G1/P2 read-only audit.")
    parser.add_argument("--input", type=Path, help="Explicit local JSON fixture path with enforced expiry.")
    parser.add_argument("--page-size", type=int, help="Deterministic local page size (1-1000).")
    parser.add_argument("--compact", action="store_true", help="Emit canonical one-line JSON.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    input_path = args.input or DEFAULT_FIXTURE
    if "://" in str(input_path):
        print("P2_INPUT_FILE_UNAVAILABLE", file=sys.stderr)
        return 2
    try:
        snapshot = load_snapshot(
            input_path,
            now=datetime.now(timezone.utc) if args.input is not None else None,
        )
        manifest = build_readonly_manifest(snapshot, page_size=args.page_size)
    except PlannerInputError as exc:
        print(exc.code, file=sys.stderr)
        return 2
    except Exception:
        print("F10_9_P2_AUDIT_FAILED", file=sys.stderr)
        return 1

    if args.compact:
        print(canonical_json(manifest))
    else:
        print(json.dumps(manifest, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
