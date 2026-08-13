import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess

import pytest

from scripts.maintenance.f10_10_m3_public_db_acl_preflight import (
    COLLECTOR_SQL,
    EXECUTE_SQL_FALLBACK_ALLOWED,
    MANIFEST_SCHEMA,
    PRIVATE_ROOT,
    PreflightError,
    ValidatedSnapshot,
    APPLY_MIGRATION_ONLY,
    build_target_attestation,
    bind_private_attestations,
    generate_candidate_sql,
    project_apply_migration_candidate,
    run,
    validate_private_result,
    write_private_artifact,
)


def owner_fingerprint(oid: int, name: str) -> str:
    return hashlib.sha256(f"database-owner-v1\0{oid}\0{name}".encode()).hexdigest()


def acl(grantee_oid: int, grantee_name: str, privilege: str, *, grantable: bool = False):
    return {
        "grantee_oid": grantee_oid,
        "grantee_name": grantee_name,
        "grantor_oid": 10,
        "grantor_name": "synthetic_owner",
        "privilege": privilege,
        "is_grantable": grantable,
        "grantor_managed": True,
    }


def database(name: str, oid: int, allowconn: bool, privileges: tuple[str, ...]):
    rows = [acl(0, "PUBLIC", privilege) for privilege in privileges]
    rows.append(acl(20, "synthetic_application", "CONNECT"))
    return {
        "name": name,
        "oid": oid,
        "allowconn": allowconn,
        "istemplate": name.startswith("template"),
        "owner_oid": 10,
        "owner_name": "synthetic_owner",
        "owner_domain_fingerprint": owner_fingerprint(10, "synthetic_owner"),
        "owner_managed": True,
        "datacl_is_null": False,
        "datacl_text": "{synthetic-acl}",
        "effective_acl": rows,
    }


def valid_result():
    value = {
        "schema": "f10.10-m3-public-db-acl-private-result-v1",
        "target_alias": "FREE_DB",
        "postgres_version_num": 170006,
        "current_database": "postgres",
        "current_user": "synthetic_executor",
        "session_user": "synthetic_executor",
        "in_recovery": False,
        "transaction_read_only": "on",
        "transaction_isolation": "repeatable read",
        "reader_present": False,
        "target_binding": build_target_attestation("sha256:" + "1" * 64, "sha256:" + "2" * 64),
        "executor": {
            "oid": 10, "name": "synthetic_executor",
            "domain_fingerprint": hashlib.sha256(
                b"database-executor-v1\0" + b"10\0synthetic_executor"
            ).hexdigest(),
            "is_superuser": True, "can_revoke_all_observed": True,
        },
        "databases": [
            database("postgres", 5, True, ("CONNECT", "TEMPORARY", "CREATE")),
            database("synthetic_other", 6, True, ("CONNECT", "TEMPORARY", "CREATE")),
            database("template0", 4, False, ("CONNECT",)),
        ],
        "sessions": [{"database_oid": 5, "role_oid": 20, "count": 1}],
        "login_public_dependencies": [],
        "managed_service_evaluation": {
            "schema": "f10.10-m3-managed-dependency-attestation-v1", "entries": [],
        },
        "topology_digest_before": "a" * 64,
        "topology_digest_after": "a" * 64,
    }
    return value


def expected_binding(value: dict) -> str:
    return value["target_binding"]["binding_digest"]


def validate(value: dict):
    return validate_private_result(value, expected_binding(value))


def mutate(path: tuple[str | int, ...], value):
    result = valid_result()
    current = result
    for key in path[:-1]:
        current = current[key]
    current[path[-1]] = value
    return result


def test_collector_is_pg17_readonly_catalog_only_and_no_query_text() -> None:
    upper = COLLECTOR_SQL.upper()
    assert COLLECTOR_SQL.startswith("BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY;")
    assert COLLECTOR_SQL.endswith("COMMIT;")
    assert "pg_catalog.pg_database" in COLLECTOR_SQL
    assert "pg_catalog.pg_stat_activity" in COLLECTOR_SQL
    assert "GROUP BY a.datid, a.usesysid" in COLLECTOR_SQL
    assert "('CREATE'::text)" in COLLECTOR_SQL
    assert "'target_binding', NULL" in COLLECTOR_SQL
    assert "'managed_service_evaluation', NULL" in COLLECTOR_SQL
    assert not __import__("re").search(r"\ba\.query\b|query_start|backend_start", COLLECTOR_SQL)
    assert "public." not in COLLECTOR_SQL
    assert not any(token in upper for token in (" INSERT ", " UPDATE ", " DELETE ", " REVOKE ", " GRANT "))


def test_postgres17_runner_reports_early_failure_and_cleans_workdir(tmp_path: Path) -> None:
    runner = Path(__file__).resolve().parent / "sql/run_f10_10_m3_public_db_acl_preflight_postgres17.sh"
    fake_bin = tmp_path / "bin"
    work_root = tmp_path / "work"
    fake_bin.mkdir()
    work_root.mkdir()
    fake_docker = fake_bin / "docker"
    fake_docker.write_text("#!/usr/bin/env bash\nexit 2\n", encoding="utf-8", newline="\n")
    fake_docker.chmod(0o755)

    result = subprocess.run(
        ["bash", str(runner)],
        cwd=Path(__file__).resolve().parents[1],
        env={**os.environ, "PATH": f"{fake_bin}:{os.environ['PATH']}", "TMPDIR": str(work_root)},
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert "stage=work-created" in result.stderr
    assert "status=2" in result.stderr
    assert list(work_root.iterdir()) == []


@pytest.mark.parametrize(
    ("path", "value", "reason"),
    [
        (("postgres_version_num",), 160000, "STOP_POSTGRES_VERSION"),
        (("target_alias",), "PRO_DB", "STOP_TARGET_BINDING"),
        (("current_database",), "other", "STOP_TARGET_BINDING"),
        (("databases", 0, "allowconn"), False, "STOP_TARGET_CONNECT"),
        (("reader_present",), True, "STOP_READER_PRESENT"),
        (("executor", "can_revoke_all_observed"), False, "STOP_EXECUTOR_AUTHORITY"),
        (("topology_digest_after",), "b" * 64, "STOP_TOPOLOGY_DRIFT"),
    ],
)
def test_fail_closed_environment_and_topology(path, value, reason) -> None:
    with pytest.raises(PreflightError, match=reason):
        validate(mutate(path, value))


def test_requires_exactly_one_target() -> None:
    result = valid_result()
    result["databases"].append(database("postgres", 99, True, ("CONNECT",)))
    with pytest.raises(PreflightError, match="STOP_TOPOLOGY|STOP_TARGET_COUNT"):
        validate(result)


def test_rejects_owner_or_grantor_ambiguity_and_grant_option() -> None:
    result = valid_result()
    result["databases"][0]["owner_domain_fingerprint"] = "0" * 64
    with pytest.raises(PreflightError, match="STOP_OWNER_GRANTOR_AMBIGUITY"):
        validate(result)

    result = valid_result()
    result["databases"][0]["effective_acl"][0]["is_grantable"] = True
    with pytest.raises(PreflightError, match="STOP_GRANT_OPTION"):
        validate(result)


def test_rejects_unmanaged_dependency_and_nonconnectable_mutation() -> None:
    result = valid_result()
    result["login_public_dependencies"] = [{"database_oid": 5, "role_oid": 30, "privilege": "CONNECT"}]
    with pytest.raises(PreflightError, match="STOP_UNRESOLVED_MANAGED_DEPENDENCY"):
        validate(result)

    for privilege in ("TEMPORARY", "CREATE"):
        result = valid_result()
        result["databases"][2]["effective_acl"].append(acl(0, "PUBLIC", privilege))
        with pytest.raises(PreflightError, match="STOP_NONCONNECTABLE_MUTATION"):
            validate(result)


def test_managed_dependency_requires_exact_explicit_surviving_source() -> None:
    result = valid_result()
    result["login_public_dependencies"] = [{"database_oid": 5, "role_oid": 20, "privilege": "CONNECT"}]
    result["managed_service_evaluation"]["entries"] = [{
        "database_oid": 5, "role_oid": 20, "privilege": "CONNECT", "service": "postgrest",
        "source_grantee_oid": 20, "source_grantor_oid": 10,
        "source_is_grantable": False, "membership": "USAGE",
    }]
    validated = validate(result)
    sql = generate_candidate_sql(validated)
    assert "x.grantee = 20 AND x.grantor = 10" in sql
    assert "has_database_privilege" in sql

    result["managed_service_evaluation"]["entries"][0]["source_grantee_oid"] = 0
    with pytest.raises(PreflightError, match="STOP_MANAGED_SERVICE_EVALUATION"):
        validate(result)


def test_validation_requires_independent_expected_target_binding() -> None:
    result = valid_result()
    expected = expected_binding(result)
    validated = validate_private_result(result, expected)
    assert validated.expected_target_binding_digest == expected
    assert validated.manifest["digests"]["target_binding"] == expected

    with pytest.raises(PreflightError, match="STOP_EXPECTED_TARGET_BINDING_REQUIRED"):
        validate_private_result(result, "")
    with pytest.raises(PreflightError, match="STOP_TARGET_BINDING"):
        validate_private_result(result, "sha256:" + "9" * 64)


def test_generation_requires_valid_private_free_target_binding() -> None:
    result = valid_result()
    result["target_binding"]["environment"] = "pro"
    with pytest.raises(PreflightError, match="STOP_TARGET_BINDING"):
        validate(result)
    with pytest.raises(PreflightError, match="STOP_SNAPSHOT_BINDING"):
        project_apply_migration_candidate("BEGIN;\nCOMMIT;\n")  # type: ignore[arg-type]


def test_free_only_paths_are_mechanically_outside_pro_migration_glob() -> None:
    root = Path(__file__).resolve().parents[1]
    free_only = root / "db/free_only_migrations/20260811_fase10_10_m3_free_reader.sql"
    rollback = root / "db/rollbacks/20260811_fase10_10_m3_free_reader_compensating.sql"
    pro_candidates = set((root / "db/migrations").glob("*.sql"))
    assert free_only.exists() and rollback.exists()
    assert free_only not in pro_candidates and rollback not in pro_candidates
    assert "free_only_migrations" not in str(pro_candidates)


def test_candidate_is_minimal_bound_and_apply_projection_removes_only_envelope() -> None:
    validated = validate(valid_result())
    sql = generate_candidate_sql(validated)

    assert validated.snapshot_digest in sql
    assert 'REVOKE CREATE, TEMPORARY ON DATABASE "postgres" FROM PUBLIC RESTRICT;' in sql
    assert 'REVOKE CONNECT, CREATE, TEMPORARY ON DATABASE "synthetic_other" FROM PUBLIC RESTRICT;' in sql
    assert 'REVOKE' not in "\n".join(line for line in sql.splitlines() if '"template0"' in line)
    assert "d.datname = 'postgres'" in sql
    assert "x.grantee = 0" in sql
    assert "x.grantee <> 0" in sql
    assert "x.grantee = 0" in sql
    assert "datacl IS NOT DISTINCT FROM" in sql
    assert "pg_catalog.pg_stat_activity" not in sql
    assert "pg_advisory_xact_lock(101010, 300312)" in sql
    projected = project_apply_migration_candidate(validated)
    assert not projected.startswith("BEGIN;")
    assert not projected.endswith("COMMIT;\n")
    assert projected == sql.removeprefix("BEGIN;\n").removesuffix("COMMIT;\n")
    assert EXECUTE_SQL_FALLBACK_ALLOWED is False


@pytest.mark.parametrize(
    "token",
    [
        "REVOKE ALL ON DATABASE x FROM PUBLIC RESTRICT;", "GRANT CONNECT ON DATABASE x TO y;",
        "REVOKE CONNECT ON DATABASE x FROM PUBLIC CASCADE;", "ALTER DATABASE x OWNER TO y;",
        "CREATE ROLE y;", "DROP SCHEMA public;", "UPDATE public.t SET x=1;",
        'REVOKE CONNECT ON DATABASE "postgres" FROM PUBLIC RESTRICT;',
    ],
)
def test_mechanical_forbidden_sql_tokens(token: str) -> None:
    with pytest.raises(PreflightError, match="STOP_FORBIDDEN_SQL|STOP_SQL_SURFACE"):
        from scripts.maintenance.f10_10_m3_public_db_acl_preflight import assert_candidate_sql_contract
        assert_candidate_sql_contract(f"BEGIN;\n{token}\nCOMMIT;\n")


def test_mutated_validated_snapshot_cannot_generate() -> None:
    validated = validate(valid_result())
    forged = ValidatedSnapshot(
        validated.private, validated.manifest, "sha256:" + "0" * 64,
        validated.expected_target_binding_digest,
    )
    with pytest.raises(PreflightError, match="STOP_SNAPSHOT_BINDING"):
        generate_candidate_sql(forged)


def test_acl_drift_after_validation_cannot_generate() -> None:
    validated = validate(valid_result())
    validated.private["result"]["databases"][0]["effective_acl"].pop()
    with pytest.raises(PreflightError, match="STOP_SNAPSHOT_BINDING"):
        generate_candidate_sql(validated)


def test_manifest_digest_domains_are_distinct() -> None:
    digests = validate(valid_result()).manifest["digests"]
    assert set(digests) == {"target_binding", "executor", "collector_sql"}
    assert len(set(digests.values())) == len(digests)


def test_manifest_is_strictly_sanitized() -> None:
    validated = validate(valid_result())
    rendered = json.dumps(validated.manifest, sort_keys=True)
    assert validated.manifest["schema"] == MANIFEST_SCHEMA
    assert validated.manifest["flags"]["execute_sql_fallback_allowed"] is False
    assert validated.manifest["flags"]["apply_migration_only"] is True
    assert APPLY_MIGRATION_ONLY is True
    for private in ("postgres", "synthetic_other", "synthetic_executor", "synthetic_owner", "synthetic_application"):
        assert private not in rendered
    forbidden_keys = {
        "datacl_text", "effective_acl", "owner_oid", "project_ref", "host",
        "database_class_counts", "public_acl_row_counts", "session_group_count",
        "login_public_dependency_count", "snapshot", "topology", "owners", "non_public_acl",
    }
    assert forbidden_keys.isdisjoint(validated.manifest)
    assert forbidden_keys.isdisjoint(validated.manifest["digests"])


def test_cli_has_no_candidate_or_payload_mode(tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        run(["--mode", "candidate"])
    code, output = run(["--mode", "sql"])
    assert code == 0 and output["sql"] == COLLECTOR_SQL
    assert "candidate" not in json.dumps(output).lower()


def test_private_writer_0600_exclusive_regular_nlink_one_and_symlink_rejected(tmp_path: Path) -> None:
    PRIVATE_ROOT.mkdir(parents=True, exist_ok=True, mode=0o700)
    PRIVATE_ROOT.chmod(0o700)
    output = PRIVATE_ROOT / f"pytest-{os.getpid()}-{id(tmp_path)}.json"
    link = PRIVATE_ROOT / f"pytest-link-{os.getpid()}-{id(tmp_path)}.json"
    try:
        write_private_artifact(output, b"{}\n")
        metadata = os.stat(output)
        assert stat_mode(metadata.st_mode) == 0o600
        assert metadata.st_nlink == 1 and output.is_file()
        with pytest.raises(FileExistsError):
            write_private_artifact(output, b"changed")
        try:
            link.symlink_to(output)
        except OSError:
            pytest.skip("symlinks unavailable")
        with pytest.raises((FileExistsError, OSError)):
            write_private_artifact(link, b"changed")
    finally:
        output.unlink(missing_ok=True)
        link.unlink(missing_ok=True)


def stat_mode(mode: int) -> int:
    return mode & 0o777


def test_private_writer_rejects_path_outside_gitignored_root(tmp_path: Path) -> None:
    with pytest.raises(PreflightError, match="STOP_OUTPUT_PATH"):
        write_private_artifact(tmp_path / "artifact.json", b"{}\n")


def test_private_reader_rejects_permissive_root_input_and_hardlink(tmp_path: Path) -> None:
    from scripts.maintenance.f10_10_m3_public_db_acl_preflight import _read_private

    PRIVATE_ROOT.mkdir(parents=True, exist_ok=True, mode=0o700)
    source = PRIVATE_ROOT / f"pytest-mode-{os.getpid()}-{id(tmp_path)}.json"
    source.write_text("{}", encoding="ascii")
    source.chmod(0o600)
    try:
        PRIVATE_ROOT.chmod(0o755)
        with pytest.raises(PreflightError, match="STOP_PRIVATE_ROOT"):
            _read_private(source)
        PRIVATE_ROOT.chmod(0o700)
        source.chmod(0o644)
        with pytest.raises(PreflightError, match="STOP_PRIVATE_INPUT"):
            _read_private(source)
        source.chmod(0o600)
        link = PRIVATE_ROOT / f"pytest-hardlink-{os.getpid()}-{id(tmp_path)}.json"
        os.link(source, link)
        with pytest.raises(PreflightError, match="STOP_PRIVATE_INPUT"):
            _read_private(source)
        link.unlink()
        symlink = PRIVATE_ROOT / f"pytest-symlink-input-{os.getpid()}-{id(tmp_path)}.json"
        try:
            symlink.symlink_to(source)
        except OSError:
            pytest.skip("symlinks unavailable")
        with pytest.raises(PreflightError, match="STOP_PRIVATE_INPUT"):
            _read_private(symlink)
        symlink.unlink()
    finally:
        PRIVATE_ROOT.chmod(0o700)
        source.unlink(missing_ok=True)


def test_validation_cli_writes_private_artifact_but_returns_only_manifest(tmp_path: Path) -> None:
    PRIVATE_ROOT.mkdir(parents=True, exist_ok=True, mode=0o700)
    PRIVATE_ROOT.chmod(0o700)
    collected = valid_result()
    target = collected.pop("target_binding")
    dependency = collected.pop("managed_service_evaluation")
    source = PRIVATE_ROOT / f"pytest-source-{os.getpid()}-{id(tmp_path)}.json"
    target_path = PRIVATE_ROOT / f"pytest-target-{os.getpid()}-{id(tmp_path)}.json"
    dependency_path = PRIVATE_ROOT / f"pytest-dependency-{os.getpid()}-{id(tmp_path)}.json"
    for path, value in ((source, collected), (target_path, target), (dependency_path, dependency)):
        path.write_text(json.dumps(value), encoding="ascii")
        path.chmod(0o600)
    output = PRIVATE_ROOT / f"pytest-cli-{os.getpid()}-{id(tmp_path)}.json"
    try:
        with pytest.raises(PreflightError, match="STOP_CLI_INVALID"):
            run([
                "--mode", "validate", "--input", str(source),
                "--target-attestation", str(target_path),
                "--dependency-attestation", str(dependency_path),
                "--private-output", str(output),
            ])
        with pytest.raises(PreflightError, match="STOP_TARGET_BINDING"):
            run([
                "--mode", "validate", "--input", str(source),
                "--target-attestation", str(target_path),
                "--dependency-attestation", str(dependency_path),
                "--expected-target-binding-digest", "sha256:" + "9" * 64,
                "--private-output", str(output),
            ])
        code, manifest = run([
            "--mode", "validate", "--input", str(source),
            "--target-attestation", str(target_path),
            "--dependency-attestation", str(dependency_path),
            "--expected-target-binding-digest", target["binding_digest"],
            "--private-output", str(output),
        ])
        assert code == 0
        assert manifest["decision"] == "PASS_OFFLINE_CANDIDATE_ELIGIBLE"
        private = json.loads(output.read_text(encoding="ascii"))
        assert private["result"]["current_database"] == "postgres"
        assert "postgres" not in json.dumps(manifest)
    finally:
        output.unlink(missing_ok=True)
        source.unlink(missing_ok=True)
        target_path.unlink(missing_ok=True)
        dependency_path.unlink(missing_ok=True)
