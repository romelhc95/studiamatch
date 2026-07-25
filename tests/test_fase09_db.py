from __future__ import annotations

import builtins
import os
import re
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any

import dotenv
import pytest
import requests

from scripts.maintenance import check_db_parity, db_migrate
from scripts.maintenance.migration_manifest import (
    canonical_sql_sha256,
    load_manifest,
)


ROOT = Path(__file__).resolve().parents[1]
F8_MANIFEST = ROOT / "db/manifests/fase08_candidate.json"
EXPECTED_MARKERS = {
    "20260724_fase06_g1b_reconciliation": (
        "sha256:d239f7080c709cdccf7227523ff2b89b48f99a57ace376a18bbdaa4d1a4d75df"
    ),
    "20260724_fase06_hito1_editorial_contract": (
        "sha256:b8badde99ada9de16aae126497304cfa7d02f9f6df89f3e22604965446c1af8a"
    ),
    "20260725_fase07_g1b_closure": (
        "sha256:9b83b36e0d90be048ccdfdea8fc1c175b8c7d7ac1fe25d7589d4c653f6a1c120"
    ),
    "20260725_fase08_hito1_functional_closure": (
        "sha256:7e392473e464df07edbcfcd7b8597ead8d7e10a47d990eedcfe6ed6cee70b527"
    ),
}


def _is_env_path(value: Any) -> bool:
    try:
        return Path(value).name.startswith(".env")
    except (TypeError, ValueError):
        return False


@pytest.fixture(autouse=True)
def _forbid_env_files_and_egress(monkeypatch: pytest.MonkeyPatch):
    def unexpected(*_args, **_kwargs):
        raise AssertionError("unexpected environment load or network transport")

    monkeypatch.setattr(dotenv, "load_dotenv", unexpected)
    monkeypatch.setattr(dotenv, "dotenv_values", unexpected)
    monkeypatch.setattr(socket, "socket", unexpected)
    monkeypatch.setattr(socket, "create_connection", unexpected)
    monkeypatch.setattr(requests.sessions.Session, "request", unexpected)
    monkeypatch.setattr(check_db_parity.requests, "get", unexpected)

    original_open = builtins.open
    original_path_open = Path.open
    original_read_text = Path.read_text

    def guarded_open(file, *args, **kwargs):
        if _is_env_path(file):
            raise AssertionError("unexpected .env file access")
        return original_open(file, *args, **kwargs)

    def guarded_path_open(path: Path, *args, **kwargs):
        if _is_env_path(path):
            raise AssertionError("unexpected .env file access")
        return original_path_open(path, *args, **kwargs)

    def guarded_read_text(path: Path, *args, **kwargs):
        if _is_env_path(path):
            raise AssertionError("unexpected .env file access")
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", guarded_open)
    monkeypatch.setattr(Path, "open", guarded_path_open)
    monkeypatch.setattr(Path, "read_text", guarded_read_text)


def _row(index: int, *, name: str | None = None) -> dict[str, str]:
    return {
        "name": name or f"20260725_fixture_{index:04d}",
        "statements": f"sha256:{index:064x}",
    }


def test_pure_ledger_reader_fetches_more_than_one_thousand_rows():
    rows = [_row(index) for index in range(1001)]
    calls: list[tuple[int, int]] = []

    def fetch(limit: int, offset: int) -> check_db_parity.LedgerPage:
        calls.append((limit, offset))
        return check_db_parity.LedgerPage(
            rows=rows[offset : offset + limit],
            total=len(rows),
            start=offset,
            end=min(offset + limit, len(rows)) - 1,
        )

    ledger = check_db_parity.read_paginated_migration_ledger(fetch)

    assert len(ledger) == 1001
    assert calls == [(1000, 0), (1000, 1000)]
    assert ledger[rows[-1]["name"]] == rows[-1]["statements"]


def test_pure_ledger_reader_fails_closed_on_transport_error():
    def fail(_limit: int, _offset: int) -> check_db_parity.LedgerPage:
        raise requests.ConnectionError("synthetic transport failure")

    with pytest.raises(RuntimeError, match="ledger page read failed"):
        check_db_parity.read_paginated_migration_ledger(fail)


@pytest.mark.parametrize(
    ("page", "message"),
    [
        ("invalid", "invalid representation"),
        (
            check_db_parity.LedgerPage(
                rows="invalid", total=0, start=None, end=None
            ),
            "not a list",
        ),
        (
            check_db_parity.LedgerPage(
                rows=["invalid"], total=1, start=0, end=0
            ),
            "malformed",
        ),
        (
            check_db_parity.LedgerPage(
                rows=[{"statements": "sha256:synthetic"}],
                total=1,
                start=0,
                end=0,
            ),
            "invalid migration name",
        ),
        (
            check_db_parity.LedgerPage(
                rows=[{"name": "migration", "statements": None}],
                total=1,
                start=0,
                end=0,
            ),
            "invalid statements",
        ),
    ],
)
def test_pure_ledger_reader_rejects_malformed_representations(page, message):
    with pytest.raises(RuntimeError, match=message):
        check_db_parity.read_paginated_migration_ledger(
            lambda _limit, _offset: page
        )


def test_pure_ledger_reader_rejects_incomplete_page():
    page = check_db_parity.LedgerPage(
        rows=[_row(index) for index in range(999)],
        total=1001,
        start=0,
        end=998,
    )
    with pytest.raises(RuntimeError, match="incomplete"):
        check_db_parity.read_paginated_migration_ledger(
            lambda _limit, _offset: page
        )


def test_pure_ledger_reader_rejects_duplicates_across_pages():
    pages = {
        0: check_db_parity.LedgerPage(
            rows=[_row(0, name="first"), _row(1, name="duplicate")],
            total=3,
            start=0,
            end=1,
        ),
        2: check_db_parity.LedgerPage(
            rows=[_row(2, name="duplicate")], total=3, start=2, end=2
        ),
    }
    with pytest.raises(RuntimeError, match="duplicate migration name"):
        check_db_parity.read_paginated_migration_ledger(
            lambda _limit, offset: pages[offset], page_size=2
        )


class _Response:
    status_code = 200
    text = "synthetic"
    headers = {"Content-Range": "*/0"}

    @staticmethod
    def json():
        raise ValueError("synthetic invalid JSON")


class _Database:
    supabase_url = "https://fixture.invalid"

    @staticmethod
    def _get_headers(**_kwargs):
        return {"api" + "key": "synthetic"}


def test_service_select_fails_closed_on_invalid_json(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(check_db_parity.requests, "get", lambda *_a, **_k: _Response())
    with pytest.raises(RuntimeError, match="invalid JSON"):
        check_db_parity.service_select(
            _Database(),
            "supabase_migrations",
            "name,statements",
            exact_count=True,
        )


def test_service_select_fails_closed_on_http_and_transport(monkeypatch):
    class FailedResponse:
        status_code = 503
        text = "must-not-be-reflected"
        headers: dict[str, str] = {}

    monkeypatch.setattr(
        check_db_parity.requests, "get", lambda *_a, **_k: FailedResponse()
    )
    with pytest.raises(RuntimeError, match="HTTP 503") as exc_info:
        check_db_parity.service_select(
            _Database(), "supabase_migrations", "name,statements"
        )
    assert "must-not-be-reflected" not in str(exc_info.value)

    def transport(*_args, **_kwargs):
        raise requests.ConnectionError("synthetic")

    monkeypatch.setattr(check_db_parity.requests, "get", transport)
    with pytest.raises(RuntimeError, match="transport failed"):
        check_db_parity.service_select(
            _Database(), "supabase_migrations", "name,statements"
        )


def test_service_select_validates_content_range_boundaries(monkeypatch):
    class Response:
        status_code = 206
        text = ""
        headers = {"Content-Range": "1000-1000/1001"}

        @staticmethod
        def json():
            return [_row(1000)]

    monkeypatch.setattr(
        check_db_parity.requests, "get", lambda *_a, **_k: Response()
    )
    page = check_db_parity.service_select(
        _Database(),
        "supabase_migrations",
        "name,statements",
        limit=1000,
        offset=1000,
        order="name.asc",
        exact_count=True,
    )

    assert page == check_db_parity.LedgerPage(
        rows=[_row(1000)], total=1001, start=1000, end=1000
    )


def test_pure_ledger_reader_rejects_wrong_page_boundaries():
    page = check_db_parity.LedgerPage(
        rows=[_row(0)], total=1, start=1, end=1
    )
    with pytest.raises(RuntimeError, match="boundaries"):
        check_db_parity.read_paginated_migration_ledger(
            lambda _limit, _offset: page
        )


def test_second_manifest_plan_has_zero_pending_and_sends_no_sql(monkeypatch):
    paths = load_manifest(F8_MANIFEST, "free")
    applied = {
        path.stem: f"sha256:{canonical_sql_sha256(path)}" for path in paths
    }
    sql_calls: list[str] = []

    class LocalAdapter:
        @staticmethod
        def rpc_raise(_name, _params):
            return True

    def capture_sql(_db, sql, max_retries=2):
        sql_calls.append(sql)
        return {"status": "unexpected"}

    monkeypatch.setattr(db_migrate, "_exec_sql_with_retry", capture_sql)
    pending = db_migrate.validate_manifest_ledger_state(
        LocalAdapter(), paths, applied
    )
    if pending:
        db_migrate.apply_manifest_package(LocalAdapter(), pending)

    assert pending == []
    assert sql_calls == []


def test_package_preflight_revalidates_applied_prefix_under_lock():
    paths = load_manifest(F8_MANIFEST, "free")
    prefix = {
        paths[0].stem: f"sha256:{canonical_sql_sha256(paths[0])}"
    }
    package = db_migrate.build_manifest_package_sql(
        paths[1:], version=20260725090000, expected_prefix=prefix
    )

    assert "LOCK TABLE public.supabase_migrations" in package
    assert "NOT EXISTS (SELECT 1 FROM public.supabase_migrations" in package
    assert paths[0].stem in package
    assert prefix[paths[0].stem] in package


def test_manifest_payload_and_test_only_exec_sql_contract_are_exact():
    paths = load_manifest(F8_MANIFEST, "free")
    package = db_migrate.build_manifest_package_sql(
        paths, version=20260725090000
    )
    fixture = (ROOT / "tests/sql/fase09_exec_sql_fixture.sql").read_text(
        encoding="utf-8"
    )
    runner = (ROOT / "tests/sql/run_fase09_postgres.sh").read_text(
        encoding="utf-8"
    )

    assert package.count("-- manifest-entry") == 4
    assert package.count("INSERT INTO public.supabase_migrations") == 4
    assert package.count("-- final-package-postconditions") == 1
    assert package.count("-- manifest-ledger-registration") == 1
    assert package.rindex("-- manifest-entry") < package.index(
        "-- final-package-postconditions"
    )
    assert package.index("-- final-package-postconditions") < package.index(
        "-- manifest-ledger-registration"
    )
    assert "build_manifest_package_sql" in runner
    assert runner.count('--file "$package_wrapper"') == 2
    assert '--file "$migration"' not in runner
    assert "SELECT public.exec_sql({delimiter}{payload}{delimiter})" in runner

    assert "RETURNS jsonb" in fixture
    assert "SECURITY DEFINER" in fixture
    assert "SET search_path = ''" in fixture
    assert "OWNER TO postgres" in fixture
    assert "FROM PUBLIC, anon, authenticated, service_role CASCADE" in fixture
    assert "TO service_role" in fixture

    definitions = []
    pattern = re.compile(
        r"\bCREATE\s+(?:OR\s+REPLACE\s+)?FUNCTION\s+"
        r"(?:public\s*\.\s*)?exec_sql\s*\(",
        re.IGNORECASE | re.MULTILINE,
    )
    sql_paths = list((ROOT / "db/migrations").glob("*.sql"))
    sql_paths.extend((ROOT / "tests/sql").glob("*.sql"))
    for sql_path in sql_paths:
        text = sql_path.read_text(encoding="utf-8")
        if pattern.search(text):
            definitions.append(sql_path.relative_to(ROOT).as_posix())
    assert sorted(definitions) == [
        "db/migrations/20260510_pro_schema_sync.sql",
        "tests/sql/fase09_exec_sql_fixture.sql",
    ]


def test_postgres_runner_is_fail_closed_and_counts_only():
    runner = (ROOT / "tests/sql/run_fase09_postgres.sh").read_text(
        encoding="utf-8"
    )
    functional = (ROOT / "tests/sql/fase09_functional_test.sql").read_text(
        encoding="utf-8"
    )

    assert "^postgresql://postgres:postgres@" in runner
    for host in ("127\\.0\\.0\\.1", "localhost", "studiamatch-f9-postgres"):
        assert host in runner
    secret_guard = "SUPA" + "BASE*|NEXT_" + "SUPABASE*|NEXT_PUBLIC_" + "SUPABASE*"
    assert secret_guard in runner
    assert "trap finish EXIT" in runner
    assert "DROP FUNCTION IF EXISTS public.exec_sql(text)" in runner
    assert "fase09_final_verifier_fault" in runner
    assert "validate_manifest_ledger_state" in runner
    assert "second plan contains pending migrations" in runner
    assert "schema_fingerprint" in runner
    assert "ON_ERROR_STOP=1 --tuples-only --no-align" in runner
    assert '[[ "$before_fingerprint" =~ ^[0-9a-f]{32}$ ]]' in runner
    assert '[[ "$after_fingerprint" =~ ^[0-9a-f]{32}$ ]]' in runner
    assert '[[ "$before_fingerprint" == "$after_fingerprint" ]]' in runner
    assert "if psql" in runner
    assert (
        "Postcondicion fallida: 20260725_fase08_hito1_functional_closure"
        in runner
    )
    assert "package contract: PASS" in runner
    assert "package contract: FAIL" in runner
    assert "sha256:" in functional
    assert "NOT EXISTS (SELECT 1 FROM public.supabase_migrations)" in functional
    assert "publication_status" in functional


def test_local_wrapper_is_docker_only_with_unconditional_cleanup():
    wrapper = (ROOT / "tests/run_fase09_local.ps1").read_text(
        encoding="utf-8"
    )

    assert "postgres:17-alpine@sha256:" in wrapper
    assert 'docker image inspect $Image' in wrapper
    assert '"--pull=never"' in wrapper
    assert '"network", "create", "--internal"' in wrapper
    assert '"network", "connect"' in wrapper
    assert '"env", "-i"' in wrapper
    assert "TEST_DATABASE_URL=$TestDatabaseUrl" in wrapper
    assert "FASE09_ROOT=/app" in wrapper
    assert "tr -d ''\\r''" in wrapper
    assert "mktemp -d /tmp/fase09-runner.XXXXXX" in wrapper
    assert "chmod 700" in wrapper
    assert "rm -rf --" in wrapper
    assert "> \"$normalized\" && bash \"$normalized\"" in wrapper
    assert "/tmp/fase09-postgres-runner.sh" not in wrapper
    assert "finally" in wrapper
    assert '"network", "disconnect", "--force"' in wrapper
    assert "originalNetworks" in wrapper
    assert "tests/test_fase09_db.py" in wrapper
    assert "docker rm --force" in wrapper
    assert "docker network disconnect --force" in wrapper
    assert "docker network rm" in wrapper
    assert "Set-Location" not in wrapper
    assert "Push-Location" not in wrapper
    assert "docker pull" not in wrapper


def test_fase09_ci_is_blocking_secretless_and_egress_restricted():
    workflow = (ROOT / ".github/workflows/security-audit.yml").read_text(
        encoding="utf-8"
    )
    job = workflow.split("  fase09-pre-free:", 1)[1].split(
        "  security-audit:", 1
    )[0]

    assert "name: FASE-09 Pre-Free Local Contract" in job
    assert "environment:" not in job
    assert "secrets." not in job
    assert "POSTGRES_CONTAINER: ${{ job.services.postgres.id }}" in job
    assert "-d \"$POSTGRES_IP\" --dport 5432 -j RETURN" in job
    assert "iptables -I OUTPUT 1 -j FASE09_EGRESS" in job
    assert "ip6tables -I OUTPUT 1 -j FASE09_EGRESS" in job
    assert "name: Restore runner network" in job
    assert "if: always()" in job
    assert "iptables -D OUTPUT -j FASE09_EGRESS" in job
    assert "tests/test_fase09_db.py tests/test_fase09_workers.py" in job
    assert "bash tests/sql/run_fase09_postgres.sh" in job
    assert "fase09-pre-free" in workflow.split("needs:", 1)[-1]
    assert "F9: ${{ needs.fase09-pre-free.result }}" in workflow


def test_fase09_imports_do_not_load_dotenv_or_start_transport():
    guard = r'''
import builtins
import socket
from pathlib import Path

import dotenv
import requests

def unexpected(*args, **kwargs):
    raise AssertionError("unexpected environment load or transport")

def is_env_path(value):
    try:
        return Path(value).name.startswith(".env")
    except (TypeError, ValueError):
        return False

original_open = builtins.open
original_path_open = Path.open
original_read_text = Path.read_text

def guarded_open(file, *args, **kwargs):
    if is_env_path(file):
        raise AssertionError("unexpected .env access")
    return original_open(file, *args, **kwargs)

def guarded_path_open(path, *args, **kwargs):
    if is_env_path(path):
        raise AssertionError("unexpected .env access")
    return original_path_open(path, *args, **kwargs)

def guarded_read_text(path, *args, **kwargs):
    if is_env_path(path):
        raise AssertionError("unexpected .env access")
    return original_read_text(path, *args, **kwargs)

dotenv.load_dotenv = unexpected
dotenv.dotenv_values = unexpected
socket.socket = unexpected
socket.create_connection = unexpected
requests.sessions.Session.request = unexpected
builtins.open = guarded_open
Path.open = guarded_path_open
Path.read_text = guarded_read_text

import scripts.maintenance.db_migrate
import scripts.maintenance.check_db_parity
'''
    clean_env = {
        "HOME": "/tmp",
        "PATH": os.environ["PATH"],
        "PYTHONPATH": str(ROOT),
    }
    result = subprocess.run(
        [sys.executable, "-c", guard],
        cwd=ROOT,
        env=clean_env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_f8_manifest_and_migrations_keep_exact_checksums():
    paths = load_manifest(F8_MANIFEST, "free")
    assert {
        path.stem: f"sha256:{canonical_sql_sha256(path)}" for path in paths
    } == EXPECTED_MARKERS
