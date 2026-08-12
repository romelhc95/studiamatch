import json
import os
from pathlib import Path
import subprocess
import stat
import sys
import uuid

import pytest

from scripts.maintenance.f10_10_m3_apply_projection import (
    ProjectionError,
    _publish_private_pair,
    _write_private,
    project_apply_migration_query,
    provisioner_fingerprint,
)


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "db/free_only_migrations/20260811_fase10_10_m3_free_reader.sql"
PACKAGE_DIGEST = "sha256:d68d44c6ae61bac120f460955f86547082c0e42b70868a35a330fda8fb7883aa"
ROLE = "synthetic_m3_provisioner"
FINGERPRINT = provisioner_fingerprint(ROLE)
SCRIPT = ROOT / "scripts/maintenance/f10_10_m3_apply_projection.py"
PRIVATE_ROOT = ROOT / "local/f10_10/m3"


def project(source: bytes | None = None):
    return project_apply_migration_query(
        MIGRATION.read_bytes() if source is None else source,
        expected_source_package_digest=PACKAGE_DIGEST if source is None else (
            "sha256:" + __import__("hashlib").sha256(source.replace(b"\r\n", b"\n")).hexdigest()
        ),
        provisioner=ROLE,
        expected_provisioner_fingerprint=FINGERPRINT,
    )


def test_projects_exact_package_without_outer_transaction_or_private_name() -> None:
    result = project()

    assert result.source_package_digest == PACKAGE_DIGEST
    assert result.applied_query.startswith(b"DO $f1010_executor_binding$")
    assert b"-- F10.10/M3" in result.applied_query
    assert b"SET LOCAL search_path = pg_catalog;" in result.applied_query
    assert not result.applied_query.rstrip().endswith(b"COMMIT;")
    assert ROLE.encode() not in result.applied_query
    assert result.applied_query_digest == "sha256:75bc9211fd7a620ee11198db7728183bb75edf5d2c3b89f24a753b70139a233d"
    normalized = MIGRATION.read_bytes().replace(b"\r\n", b"\n")
    expected_body = normalized.replace(b"BEGIN;", b"", 1)
    commit = expected_body.rfind(b"COMMIT;")
    expected_body = expected_body[:commit] + expected_body[commit + len(b"COMMIT;"):]
    guard_end = result.applied_query.index(b"$f1010_executor_binding$;\n\n") + len(
        b"$f1010_executor_binding$;\n\n"
    )
    assert result.applied_query[guard_end:] == expected_body


def test_preserves_transaction_words_in_comments_strings_and_dollar_bodies() -> None:
    source = b"""-- BEGIN;\nBEGIN;\nDO $body$ BEGIN RAISE NOTICE 'COMMIT;'; END $body$;\n-- COMMIT;\nCOMMIT;\n"""
    result = project(source)

    assert b"DO $body$ BEGIN RAISE NOTICE 'COMMIT;'; END $body$;" in result.applied_query
    assert b"-- COMMIT;" in result.applied_query


@pytest.mark.parametrize(
    "source",
    [
        b"SELECT 1; COMMIT;\n",
        b"BEGIN; SELECT 1;\n",
        b"BEGIN; COMMIT; SELECT 1;\n",
        b"BEGIN; ROLLBACK; COMMIT;\n",
        b"BEGIN; SAVEPOINT nested; COMMIT;\n",
        b"BEGIN; ABORT AND NO CHAIN; COMMIT;\n",
        b"BEGIN; BEGIN WORK; COMMIT;\n",
        b"BEGIN; END AND CHAIN; COMMIT;\n",
        b"BEGIN; START TRANSACTION; COMMIT;\n",
        b"BEGIN; ROLLBACK TO SAVEPOINT nested; COMMIT;\n",
        b"BEGIN; RELEASE SAVEPOINT nested; COMMIT;\n",
        b"BEGIN; COMMIT AND CHAIN; COMMIT;\n",
        b"BEGIN; PREPARE TRANSACTION 'gid'; COMMIT;\n",
        b"BEGIN; SET TRANSACTION READ ONLY; COMMIT;\n",
        b"BEGIN; SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY; COMMIT;\n",
        b"BEGIN; SELECT 'unterminated; COMMIT;\n",
    ],
)
def test_rejects_invalid_or_nested_transaction_envelopes(source: bytes) -> None:
    with pytest.raises(ProjectionError, match="STOP_"):
        project(source)


def test_rejects_package_and_provisioner_digest_mismatch() -> None:
    with pytest.raises(ProjectionError, match="STOP_PACKAGE_DIGEST_MISMATCH"):
        project_apply_migration_query(
            MIGRATION.read_bytes(),
            expected_source_package_digest="sha256:" + "0" * 64,
            provisioner=ROLE,
            expected_provisioner_fingerprint=FINGERPRINT,
        )
    with pytest.raises(ProjectionError, match="STOP_PROVISIONER_BINDING_MISMATCH"):
        project_apply_migration_query(
            MIGRATION.read_bytes(),
            expected_source_package_digest=PACKAGE_DIGEST,
            provisioner=ROLE,
            expected_provisioner_fingerprint="sha256:" + "0" * 64,
        )


def test_crlf_normalizes_to_approved_package_and_projection() -> None:
    lf = MIGRATION.read_bytes().replace(b"\r\n", b"\n")
    crlf = lf.replace(b"\n", b"\r\n")

    assert project_apply_migration_query(
        lf,
        expected_source_package_digest=PACKAGE_DIGEST,
        provisioner=ROLE,
        expected_provisioner_fingerprint=FINGERPRINT,
    ).applied_query == project_apply_migration_query(
        crlf,
        expected_source_package_digest=PACKAGE_DIGEST,
        provisioner=ROLE,
        expected_provisioner_fingerprint=FINGERPRINT,
    ).applied_query


@pytest.mark.parametrize(
    "source",
    [
        b"\xef\xbb\xbfBEGIN; SELECT 1; COMMIT;\n",
        b"BEGIN; SELECT '\x00'; COMMIT;\n",
        b"BEGIN;\rSELECT 1;\rCOMMIT;\r",
    ],
)
def test_rejects_bom_nul_and_bare_cr(source: bytes) -> None:
    with pytest.raises(ProjectionError, match="STOP_SOURCE_INVALID"):
        project(source)


def test_private_writer_is_0600_and_rejects_existing_or_symlink(tmp_path: Path) -> None:
    output = tmp_path / "projection.sql"
    _write_private(output, b"SELECT 1;\n")

    assert output.read_bytes() == b"SELECT 1;\n"
    assert os.stat(output).st_mode & 0o777 == 0o600
    with pytest.raises(FileExistsError):
        _write_private(output, b"changed")

    link = tmp_path / "projection-link.sql"
    try:
        link.symlink_to(output)
    except OSError:
        pytest.skip("symlinks unavailable")
    with pytest.raises(OSError):
        _write_private(link, b"changed")


def test_private_writer_completes_short_writes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    output = tmp_path / "projection.sql"
    real_write = os.write

    def short_write(fd: int, contents: bytes | memoryview) -> int:
        return real_write(fd, contents[:1])

    monkeypatch.setattr(os, "write", short_write)
    _write_private(output, b"abcdef")

    assert output.read_bytes() == b"abcdef"


def test_private_writer_removes_partial_file_on_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "projection.sql"
    real_write = os.write
    calls = 0

    def failing_write(fd: int, contents: bytes | memoryview) -> int:
        nonlocal calls
        calls += 1
        if calls == 1:
            return real_write(fd, contents[:1])
        raise OSError("synthetic write failure")

    monkeypatch.setattr(os, "write", failing_write)
    with pytest.raises(OSError, match="synthetic write failure"):
        _write_private(output, b"abcdef")

    assert not output.exists()


def test_private_pair_removes_both_files_if_commit_fsync_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    sql = tmp_path / "projection.sql"
    manifest = tmp_path / "manifest.json"
    real_fsync = os.fsync

    def failing_directory_fsync(fd: int) -> None:
        if stat.S_ISDIR(os.fstat(fd).st_mode):
            raise OSError("synthetic directory fsync failure")
        real_fsync(fd)

    monkeypatch.setattr(os, "fsync", failing_directory_fsync)
    with pytest.raises(OSError, match="synthetic directory fsync failure"):
        _publish_private_pair(
            tmp_path,
            sql.name,
            b"SELECT 1;\n",
            manifest.name,
            b"{}\n",
        )

    assert not sql.exists()
    assert not manifest.exists()


def run_cli(
    *,
    sql: Path,
    manifest: Path,
    role: str = ROLE,
    package_digest: str = PACKAGE_DIGEST,
    fingerprint: str = FINGERPRINT,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["F10_10_M3_PROVISIONER"] = role
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--expected-package-digest",
            package_digest,
            "--expected-provisioner-fingerprint",
            fingerprint,
            "--output-sql",
            str(sql),
            "--output-manifest",
            str(manifest),
        ],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


@pytest.fixture
def private_outputs() -> tuple[Path, Path]:
    PRIVATE_ROOT.mkdir(parents=True, exist_ok=True, mode=0o700)
    token = uuid.uuid4().hex
    sql = PRIVATE_ROOT / f"projection-{token}.sql"
    manifest = PRIVATE_ROOT / f"projection-{token}.json"
    yield sql, manifest
    sql.unlink(missing_ok=True)
    manifest.unlink(missing_ok=True)


def test_cli_publishes_private_pair_and_sanitized_stdout(
    private_outputs: tuple[Path, Path],
) -> None:
    sql, manifest = private_outputs
    result = run_cli(sql=sql, manifest=manifest)

    assert result.returncode == 0
    status = json.loads(result.stdout)
    manifest_data = json.loads(manifest.read_text(encoding="ascii"))
    assert status == {
        "status": "PASS",
        "schema": "f10.10-m3-apply-projection-v1",
        "applied_query_digest": manifest_data["applied_query_digest"],
    }
    assert ROLE not in result.stdout
    assert ROLE not in manifest.read_text(encoding="ascii")
    assert ROLE.encode("ascii") not in sql.read_bytes()
    assert os.stat(sql).st_mode & 0o777 == 0o600
    assert os.stat(manifest).st_mode & 0o777 == 0o600
    assert "sha256:" + __import__("hashlib").sha256(sql.read_bytes()).hexdigest() == (
        manifest_data["applied_query_digest"]
    )


@pytest.mark.parametrize(
    ("role", "package_digest", "fingerprint", "reason"),
    [
        ("", PACKAGE_DIGEST, FINGERPRINT, "STOP_CONFIG_INVALID"),
        ("Invalid-Role", PACKAGE_DIGEST, FINGERPRINT, "STOP_CONFIG_INVALID"),
        (ROLE, "sha256:invalid", FINGERPRINT, "STOP_CONFIG_INVALID"),
        (ROLE, PACKAGE_DIGEST, "sha256:invalid", "STOP_CONFIG_INVALID"),
        (ROLE, "sha256:" + "0" * 64, FINGERPRINT, "STOP_PACKAGE_DIGEST_MISMATCH"),
    ],
)
def test_cli_rejects_invalid_configuration(
    private_outputs: tuple[Path, Path],
    role: str,
    package_digest: str,
    fingerprint: str,
    reason: str,
) -> None:
    sql, manifest = private_outputs
    result = run_cli(
        sql=sql,
        manifest=manifest,
        role=role,
        package_digest=package_digest,
        fingerprint=fingerprint,
    )

    assert result.returncode == 2
    assert json.loads(result.stdout) == {"status": "STOP", "reason": reason}
    assert ROLE not in result.stdout
    assert not sql.exists()
    assert not manifest.exists()


def test_cli_rejects_output_outside_private_root(tmp_path: Path) -> None:
    result = run_cli(sql=tmp_path / "projection.sql", manifest=tmp_path / "manifest.json")

    assert result.returncode == 2
    assert json.loads(result.stdout)["reason"] == "STOP_OUTPUT_PATH_INVALID"
    assert not (tmp_path / "projection.sql").exists()
    assert not (tmp_path / "manifest.json").exists()


def test_cli_missing_required_configuration_exits_two() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=ROOT,
        env={**os.environ, "F10_10_M3_PROVISIONER": ROLE},
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert ROLE not in result.stdout + result.stderr


def test_cli_rejects_same_output_path(private_outputs: tuple[Path, Path]) -> None:
    sql, _manifest = private_outputs
    result = run_cli(sql=sql, manifest=sql)

    assert result.returncode == 2
    assert json.loads(result.stdout)["reason"] == "STOP_OUTPUT_PATH_INVALID"
    assert not sql.exists()


def test_cli_existing_manifest_removes_new_sql(
    private_outputs: tuple[Path, Path],
) -> None:
    sql, manifest = private_outputs
    manifest.write_text("existing\n", encoding="ascii")
    manifest.chmod(0o600)

    result = run_cli(sql=sql, manifest=manifest)

    assert result.returncode == 2
    assert json.loads(result.stdout)["reason"] == "STOP_LOCAL_IO"
    assert not sql.exists()
    assert manifest.read_text(encoding="ascii") == "existing\n"


def test_cli_rejects_existing_sql_without_touching_it(
    private_outputs: tuple[Path, Path],
) -> None:
    sql, manifest = private_outputs
    sql.write_text("existing\n", encoding="ascii")
    sql.chmod(0o600)

    result = run_cli(sql=sql, manifest=manifest)

    assert result.returncode == 2
    assert sql.read_text(encoding="ascii") == "existing\n"
    assert not manifest.exists()


def test_cli_rejects_symlink_output(
    private_outputs: tuple[Path, Path], tmp_path: Path,
) -> None:
    sql, manifest = private_outputs
    target = tmp_path / "target.sql"
    target.write_text("unchanged\n", encoding="ascii")
    try:
        sql.symlink_to(target)
    except OSError:
        pytest.skip("symlinks unavailable")

    result = run_cli(sql=sql, manifest=manifest)

    assert result.returncode == 2
    assert target.read_text(encoding="ascii") == "unchanged\n"
    assert not manifest.exists()
