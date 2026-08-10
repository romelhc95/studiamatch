import os
import sys
import time
from datetime import datetime

from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.db_client import get_db_client
from shared.f10_9_fg3_atomic import run_fg3_atomic
from shared.safe_http import DEFAULT_POLICY, UnsafeURL, _validate_target, safe_get, safe_head
from shared.utils import TimeGuard, setup_lima_logging


load_dotenv()
logger = setup_lima_logging("IntegrityPing")


def is_safe_public_url(url):
    """Compatibility validator for sync without issuing an HTTP request."""
    try:
        _validate_target(str(url or ""), time.monotonic() + DEFAULT_POLICY.total_timeout_seconds)
    except (UnsafeURL, TypeError, ValueError):
        return False
    return True


def run_integrity_ping(
    institution_id=None,
    limit=None,
    *,
    db=None,
    head=safe_head,
    get=safe_get,
    sleeper=time.sleep,
    now: datetime | None = None,
    guard=None,
    policy=DEFAULT_POLICY,
):
    """Run FG3 with all decisions complete before the first conditional write."""
    client = db or get_db_client()
    time_guard = guard or TimeGuard(max_seconds=3600, logger=logger)

    # Historical limit semantics remain represented for compatibility with the
    # certification contract; expiration is now aggregated, never written early.
    expired_count = 0
    active_limit = None if limit is None else max(limit - expired_count, 0)
    result = run_fg3_atomic(
        client,
        institution_id=institution_id,
        limit=active_limit,
        head=head,
        get=get,
        sleeper=sleeper,
        now=now,
        guard=time_guard,
        policy=policy,
    )
    summary = result.manifest
    logger.info(
        "FG3_RESULT result=%s rows=%s planned=%s applied=%s verified=%s",
        result.result,
        summary["collection"]["rows"],
        summary["aggregate"]["planned"],
        summary["apply"]["outcomes"].get("APPLIED", 0),
        summary["verify"]["desired_states_verified"],
    )
    return result.exit_code


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run FG3 integrity ping")
    parser.add_argument(
        "--institution-id",
        help="Optional exact institution UUID for a cohort-limited run",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum active courses to ping",
    )
    args = parser.parse_args()
    sys.exit(run_integrity_ping(institution_id=args.institution_id, limit=args.limit))
