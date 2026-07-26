from __future__ import annotations

import ast
import copy
import hashlib
import inspect
import os
import re
import shutil
import socket
import subprocess
import sys
from pathlib import Path

import dotenv
import pytest
import requests

from scripts.maintenance import free_preflight
from scripts.maintenance.free_preflight import (
    CONTRACT_PATH,
    GitBindingProof,
    LocalFileProof,
    PreflightContractError,
    TargetValidation,
    build_target_validation,
    canonical_json_bytes,
    canonical_json_sha256,
    catalog_adapter_commands,
    load_contract,
    prepare_catalog_query,
    run_synthetic_self_test,
    strict_json_loads,
    validate_contract_files,
    validate_contract_shape,
    validate_evidence_structure,
    validate_git_binding,
    validate_http_observation,
    validate_http_trace_structure,
    validate_local_capability,
    validate_query_replay,
    validate_sql_trace_structure,
    validate_tool_observation,
    validate_tool_trace_structure,
)


ROOT = Path(__file__).resolve().parents[1]
DESCRIPTOR = ROOT / CONTRACT_PATH
_PROVIDER = "SUPA" + "BASE"
_NEXT_PUBLISHABLE = "NEXT_" + _PROVIDER + "_PUBLISHABLE_KEY"
_FREE_ORIGIN_NAME = "FREE_" + _PROVIDER + "_URL"
_FREE_KEY_NAME = "FREE_" + _NEXT_PUBLISHABLE
_PRO_ORIGIN_NAME = "PRO_" + _PROVIDER + "_URL"
_PRO_KEY_NAME = "PRO_" + _NEXT_PUBLISHABLE
_REST_V1 = "/" + "rest" + "/v1"
_API_KEY_HEADER = "api" + "key"


@pytest.fixture(autouse=True)
def _block_runtime_capabilities(monkeypatch: pytest.MonkeyPatch):
    def unexpected(*_args, **_kwargs):
        raise AssertionError("F9.3 runner attempted a prohibited capability")

    monkeypatch.setattr(dotenv, "load_dotenv", unexpected)
    monkeypatch.setattr(dotenv, "dotenv_values", unexpected)
    monkeypatch.setattr(socket, "socket", unexpected)
    monkeypatch.setattr(socket, "create_connection", unexpected)
    monkeypatch.setattr(requests.sessions.Session, "request", unexpected)


@pytest.fixture
def contract() -> dict:
    return load_contract(DESCRIPTOR)


def _git(repo: Path, *args: str) -> str:
    environment = {
        "HOME": "/tmp",
        "PATH": os.environ["PATH"],
        "LANG": "C",
        "LC_ALL": "C",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_NO_LAZY_FETCH": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
    }
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        env=environment,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=15,
        check=True,
    )
    return result.stdout.strip()


def _git_bytes(repo: Path, *args: str) -> bytes:
    environment = {
        "HOME": "/tmp", "PATH": os.environ["PATH"], "LANG": "C", "LC_ALL": "C",
        "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_TERMINAL_PROMPT": "0", "GIT_NO_LAZY_FETCH": "1", "GIT_NO_REPLACE_OBJECTS": "1",
    }
    return subprocess.run(
        ["git", *args], cwd=repo, env=environment, stdin=subprocess.DEVNULL,
        capture_output=True, timeout=15, check=True,
    ).stdout


def _complete_tree_entries(repo: Path, commit: str) -> list[dict[str, str]]:
    records = _git_bytes(repo, "ls-tree", "-rz", "--full-tree", "-r", commit).split(b"\0")
    entries = []
    for record in records:
        if not record:
            continue
        metadata, raw_path = record.split(b"\t", 1)
        mode, object_type, object_sha = metadata.decode("ascii").split(" ")
        entries.append({
            "path": raw_path.decode("utf-8"), "mode": mode,
            "object_type": object_type, "object_sha1": object_sha,
        })
    return entries


def _actual_git_proof(contract: dict, tmp_path: Path) -> tuple[dict, Path]:
    source_commit = contract["source_binding"]["commit_sha"]
    assert _git(ROOT, "cat-file", "-t", source_commit) == "commit"
    source_tree = _git(ROOT, "rev-parse", f"{source_commit}^{{tree}}")
    assert source_tree == contract["source_binding"]["tree_sha"]
    source_entries = _complete_tree_entries(ROOT, source_commit)
    source_by_path = {entry["path"]: entry for entry in source_entries}
    for expected in contract["source_binding"]["entries"]:
        assert source_by_path[expected["path"]]["object_sha1"] == expected["git_blob_sha1"]

    candidate = tmp_path / "candidate-git"
    candidate.mkdir()
    for relative in contract["implementation_binding"]["candidate_git_required_paths"]:
        destination = candidate / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(free_preflight._lf((ROOT / relative).read_bytes()))
    _git(candidate, "init", "--quiet")
    _git(candidate, "add", "--all")
    _git(
        candidate,
        "-c",
        "user.name=F9.3 Actual Git Gate",
        "-c",
        "user.email=f93-gate@example.invalid",
        "commit",
        "--quiet",
        "-m",
        "f93 candidate proof",
    )
    candidate_commit = _git(candidate, "rev-parse", "HEAD")
    assert _git(candidate, "cat-file", "-t", candidate_commit) == "commit"
    candidate_tree = _git(candidate, "rev-parse", f"{candidate_commit}^{{tree}}")
    assert _git(candidate, "cat-file", "-t", candidate_tree) == "tree"
    candidate_entries = _complete_tree_entries(candidate, candidate_commit)
    proof = {
        "schema_version": 2,
        "provenance": "raw_git_objects_complete_tree_v1",
        "source": {
            "commit_sha": source_commit,
            "raw_commit_hex": _git_bytes(ROOT, "cat-file", "commit", source_commit).hex(),
            "tree_sha": source_tree,
            "entries": source_entries,
        },
        "candidate": {
            "commit_sha": candidate_commit,
            "raw_commit_hex": _git_bytes(candidate, "cat-file", "commit", candidate_commit).hex(),
            "tree_sha": candidate_tree,
            "entries": candidate_entries,
        },
    }
    return proof, candidate


@pytest.fixture
def git_binding(contract: dict, tmp_path: Path) -> GitBindingProof:
    proof, candidate = _actual_git_proof(contract, tmp_path)
    return validate_git_binding(contract, proof, root=candidate)


def _target_configuration() -> dict[str, str]:
    return {
        _FREE_ORIGIN_NAME: "https://" + ("f" * 20) + ".supabase.co",
        _FREE_KEY_NAME: "sb_" + "publishable_" + "synthetic_free",
        _PRO_ORIGIN_NAME: "https://" + ("p" * 20) + ".supabase.co",
        _PRO_KEY_NAME: "sb_" + "publishable_" + "synthetic_pro",
    }


def _target_artifact(configuration: dict[str, str]) -> dict[str, object]:
    artifact: dict[str, object] = {
        "schema_version": 1,
        "source_document_path": ".context/sistema_db_supabase.md",
        "source_document_blob_sha1": "37c5a7c7acf5fb5ee6a55d57a161698f6115b1e5",
        "free_origin_sha256": hashlib.sha256(configuration[_FREE_ORIGIN_NAME].encode()).hexdigest(),
        "pro_origin_sha256": hashlib.sha256(configuration[_PRO_ORIGIN_NAME].encode()).hexdigest(),
    }
    artifact["artifact_sha256"] = canonical_json_sha256(artifact)
    return artifact


def _query(contract: dict, query_id: str) -> dict:
    return next(item for item in contract["query_catalog"] if item["id"] == query_id)


def _safe_row(contract: dict, query: dict, index: int = 0) -> dict:
    if query["id"] == "migration_ledger":
        if index < 4:
            entry = contract["package_binding"]["entries"][index]
            return {
                "migration_name": entry["migration_name"],
                "checksum_marker": "sha256:" + entry["sha256"],
            }
        return {
            "migration_name": f"20990101_synthetic_{index:06d}",
            "checksum_marker": "sha256:" + f"{index:064x}",
        }
    row = free_preflight._synthetic_row(query, index)
    return row


def _pages(operation: dict, rows: list[dict]) -> list[dict]:
    page_size = operation["pagination"]["page_size"]
    chunks = [rows[index : index + page_size] for index in range(0, len(rows), page_size)]
    if not chunks:
        chunks = [[]]
    elif len(rows) % page_size == 0:
        chunks.append([])
    pages = []
    cursor = None
    for page_index, chunk in enumerate(chunks):
        offset = page_index * page_size
        page = {
            "operation_id": operation["id"],
            "page_index": page_index,
            "request_cursor": cursor if operation["pagination"]["mode"] == "keyset" else None,
            "request_offset": offset if operation["pagination"]["mode"] == "offset" else None,
            "total_count": len(rows),
            "start_index": offset if chunk else None,
            "end_index": offset + len(chunk) - 1 if chunk else None,
            "server_timeout_ms": operation["timeout_ms"],
            "timeout_enforced": True,
            "rows": copy.deepcopy(chunk),
        }
        pages.append(page)
        if operation["pagination"]["mode"] == "keyset" and chunk:
            cursor = chunk[-1][operation["pagination"]["order_columns"][0]]
    return pages


def _all_summaries(contract: dict):
    queries = []
    for query in contract["query_catalog"]:
        rows = [] if query["id"] == "catalog_sequence_grants" else [_safe_row(contract, query)]
        queries.append(validate_query_replay(contract, query["id"], _pages(query, rows)))
    http = contract["http_catalog"][0]
    schema_row = {"openapi_version": "3.0.0", "path_count": 1, "definition_count": 1}
    http_summaries = [validate_http_observation(contract, http["id"], _pages(http, [schema_row]))]
    tool_summaries = [
        validate_tool_observation(
            contract,
            {"tool_id": tool["id"], "item_count": 0, "levels_sha256": "1" * 64, "payload_sha256": "2" * 64},
        )
        for tool in contract["tool_catalog"]
    ]
    local_summaries = [
        validate_local_capability(contract, item["id"], item["required_classification"])
        for item in contract["local_capability_catalog"]
    ]
    return queries, http_summaries, tool_summaries, local_summaries


def _copy_local_tree(contract: dict, root: Path) -> Path:
    paths = {CONTRACT_PATH, "scripts/maintenance/free_preflight.py"}
    paths.update(item["path"] for item in contract["source_binding"]["entries"])
    for relative in paths:
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((ROOT / relative).read_bytes())
    return root / CONTRACT_PATH


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/maintenance/free_preflight.py", *args],
        cwd=ROOT,
        env={"HOME": "/tmp", "PATH": os.environ["PATH"]},
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def test_contract_shape_files_and_non_circular_implementation_binding(contract: dict):
    assert contract["schema_version"] == 2
    assert validate_contract_shape(contract) is contract
    local = validate_contract_files(contract)
    assert isinstance(local, LocalFileProof)
    assert local.contract_sha256 == canonical_json_sha256(contract)
    validator = contract["implementation_binding"]["runtime_validators"]
    assert len(validator) == 1
    assert validator[0]["raw_lf_sha256"] == local.implementation_sha256
    assert contract["implementation_binding"]["transitive_project_modules"] == []
    assert CONTRACT_PATH not in {item["path"] for item in validator}


@pytest.mark.parametrize(
    "raw",
    [
        '{"a":1,"a":2}',
        '{"value":1.5}',
        '{"value":NaN}',
        '{"value":"e\u0301"}',
    ],
)
def test_strict_json_rejects_duplicates_float_nonfinite_and_non_nfc(raw: str):
    with pytest.raises(PreflightContractError):
        strict_json_loads(raw)


def test_contract_rejects_unknown_bool_integer_query_and_validator_drift(contract: dict):
    mutations = []
    extra = copy.deepcopy(contract)
    extra["unknown"] = True
    mutations.append(extra)
    boolean = copy.deepcopy(contract)
    boolean["schema_version"] = True
    mutations.append(boolean)
    query = copy.deepcopy(contract)
    query["query_catalog"][0]["sql"] = "SELECT 1"
    query["query_catalog"][0]["sql_sha256"] = hashlib.sha256(b"SELECT 1").hexdigest()
    mutations.append(query)
    validator = copy.deepcopy(contract)
    validator["implementation_binding"]["runtime_validators"][0]["raw_lf_sha256"] = "0" * 64
    for changed in mutations:
        with pytest.raises(PreflightContractError):
            validate_contract_shape(changed)
    with pytest.raises(PreflightContractError, match="implementation"):
        validate_contract_files(validator)


def test_loader_rejects_wrong_path_symlink_and_file_drift(contract: dict, tmp_path: Path):
    descriptor = _copy_local_tree(contract, tmp_path)
    assert load_contract(descriptor, root=tmp_path)["contract_id"] == contract["contract_id"]
    with pytest.raises(PreflightContractError, match="path"):
        load_contract("db/manifests/../manifests/f9_3_free_preflight_contract.json", root=tmp_path)
    runner = tmp_path / "scripts/maintenance/free_preflight.py"
    runner.write_bytes(runner.read_bytes() + b"\n")
    with pytest.raises(PreflightContractError, match="implementation"):
        validate_contract_files(load_contract(descriptor, root=tmp_path), root=tmp_path)
    runner.write_bytes((ROOT / "scripts/maintenance/free_preflight.py").read_bytes())
    source = tmp_path / contract["source_binding"]["entries"][0]["path"]
    source_bytes = source.read_bytes()
    source.unlink()
    target = tmp_path / "source-target"
    target.write_bytes(source_bytes)
    try:
        source.symlink_to(target)
    except OSError:
        pytest.skip("symlinks unavailable")
    with pytest.raises(PreflightContractError, match="symlink"):
        validate_contract_files(load_contract(descriptor, root=tmp_path), root=tmp_path)


def test_actual_git_gate_verifies_commit_tree_modes_and_blob_ids(contract: dict, tmp_path: Path):
    proof, candidate = _actual_git_proof(contract, tmp_path)
    validated = validate_git_binding(contract, proof, root=candidate)
    assert isinstance(validated, GitBindingProof)
    assert validated.source_commit_sha == contract["source_binding"]["commit_sha"]
    assert validated.source_tree_sha == contract["source_binding"]["tree_sha"]
    assert re.fullmatch(r"[0-9a-f]{64}", validated.proof_sha256)

    checkout_path = candidate / CONTRACT_PATH
    checkout_path.write_bytes(checkout_path.read_bytes().replace(b"\n", b"\r\n"))
    assert validate_git_binding(contract, proof, root=candidate) == validated

    wrong_tree = copy.deepcopy(proof)
    wrong_tree["source"]["tree_sha"] = "0" * 40
    with pytest.raises(PreflightContractError):
        validate_git_binding(contract, wrong_tree, root=candidate)
    wrong_mode = copy.deepcopy(proof)
    wrong_mode["candidate"]["entries"][0]["mode"] = "100755"
    with pytest.raises(PreflightContractError):
        validate_git_binding(contract, wrong_mode, root=candidate)
    wrong_blob = copy.deepcopy(proof)
    wrong_blob["candidate"]["entries"][0]["object_sha1"] = "0" * 40
    with pytest.raises(PreflightContractError):
        validate_git_binding(contract, wrong_blob, root=candidate)

    wrong_raw_commit = copy.deepcopy(proof)
    wrong_raw_commit["candidate"]["raw_commit_hex"] = (b"tree " + candidate.name.encode()).hex()
    with pytest.raises(PreflightContractError, match="commit"):
        validate_git_binding(contract, wrong_raw_commit, root=candidate)
    incomplete_tree = copy.deepcopy(proof)
    incomplete_tree["candidate"]["entries"].pop()
    with pytest.raises(PreflightContractError, match="tree"):
        validate_git_binding(contract, incomplete_tree, root=candidate)


def test_copied_non_git_tree_only_receives_local_file_validation(contract: dict, tmp_path: Path):
    _copy_local_tree(contract, tmp_path)
    local = validate_contract_files(load_contract(tmp_path / CONTRACT_PATH, root=tmp_path), root=tmp_path)
    assert isinstance(local, LocalFileProof)
    assert not isinstance(local, GitBindingProof)
    assert not hasattr(free_preflight, "build_evidence")


def test_target_validation_requires_reviewed_artifact_and_exact_named_pairs(contract: dict):
    configuration = _target_configuration()
    artifact = _target_artifact(configuration)
    validation = build_target_validation(contract, configuration, artifact)
    assert isinstance(validation, TargetValidation)
    assert validation.free_fingerprint_sha256 != validation.pro_fingerprint_sha256
    assert validation == build_target_validation(contract, configuration, artifact)
    assert re.fullmatch(r"[0-9a-f]{64}", validation.validation_sha256)
    signature = inspect.signature(build_target_validation)
    assert list(signature.parameters) == ["contract", "named_configuration", "reviewed_identity_artifact"]


@pytest.mark.parametrize("kind", ["missing", "extra", "generic", "same_origin", "same_key", "pro_as_free", "bad_key", "bad_origin"])
def test_target_validation_rejects_ambiguous_reused_and_wrong_provenance(contract: dict, kind: str):
    values = _target_configuration()
    artifact = _target_artifact(values)
    if kind == "missing":
        values.pop(_PRO_KEY_NAME)
    elif kind == "extra":
        values[_PROVIDER + "_URL"] = "synthetic"
    elif kind == "generic":
        values = {_PROVIDER + "_URL": values[_FREE_ORIGIN_NAME], _NEXT_PUBLISHABLE: values[_FREE_KEY_NAME]}
    elif kind == "same_origin":
        values[_PRO_ORIGIN_NAME] = values[_FREE_ORIGIN_NAME]
    elif kind == "same_key":
        values[_PRO_KEY_NAME] = values[_FREE_KEY_NAME]
    elif kind == "pro_as_free":
        values[_FREE_ORIGIN_NAME], values[_PRO_ORIGIN_NAME] = values[_PRO_ORIGIN_NAME], values[_FREE_ORIGIN_NAME]
        values[_FREE_KEY_NAME], values[_PRO_KEY_NAME] = values[_PRO_KEY_NAME], values[_FREE_KEY_NAME]
    elif kind == "bad_key":
        values[_FREE_KEY_NAME] = "sb_" + "secret_" + "synthetic"
    else:
        values[_FREE_ORIGIN_NAME] += "/path"
    with pytest.raises(PreflightContractError):
        build_target_validation(contract, values, artifact)


def test_catalog_is_expanded_semantic_exact_and_has_no_generic_primitive(contract: dict):
    ids = [item["id"] for item in contract["query_catalog"]]
    assert ids == [item["id"] for item in free_preflight._QUERY_DEFINITIONS]
    assert {
        "catalog_schema_acl", "catalog_table_grants", "catalog_column_grants",
        "catalog_sequence_grants", "catalog_routines", "catalog_routine_grants", "catalog_views",
    } < set(ids)
    routines = _query(contract, "catalog_routines")
    for field in ("identity_arguments", "result_type", "language_name", "security_definer", "runtime_settings", "owner_name"):
        assert field in {item["name"] for item in routines["result_shape"]}
    assert "owner_name" in {
        item["name"] for item in _query(contract, "catalog_schema_acl")["result_shape"]
    }
    for query in contract["query_catalog"]:
        assert query["acceptance"]["predicate"] != "collect_only"
        assert hashlib.sha256(query["sql"].encode()).hexdigest() == query["sql_sha256"]
        assert query["sql"].startswith("SELECT ")
        assert ";" not in query["sql"]
    assert not hasattr(free_preflight, "execute_sql")
    assert not hasattr(free_preflight, "rpc")
    assert not hasattr(free_preflight, "transport")


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT value INTO temporary_table FROM pg_catalog.pg_class",
        "WITH x AS (SELECT 1) SELECT 1",
        "SELECT pg_catalog.pg_sleep(10)",
        "SELECT pg_catalog.set_config('x','y',false)",
        "SELECT 1; DELETE FROM public.synthetic",
    ],
)
def test_exact_sql_binding_rejects_select_into_cte_side_effects_and_escape(contract: dict, sql: str):
    changed = copy.deepcopy(contract)
    changed["query_catalog"][0]["sql"] = sql
    changed["query_catalog"][0]["sql_sha256"] = hashlib.sha256(sql.encode()).hexdigest()
    changed["query_catalog"][0]["allowed_catalog_functions"] = []
    with pytest.raises(PreflightContractError):
        validate_contract_shape(changed)


def test_prepared_query_is_only_exact_catalog_resolution(contract: dict):
    prepared = prepare_catalog_query(contract, "migration_ledger", {"after_name": None, "page_size": 100})
    assert prepared.sql == _query(contract, "migration_ledger")["sql"]
    assert prepared.sql_sha256 == _query(contract, "migration_ledger")["sql_sha256"]
    assert prepared.parameters == (None, 100)
    with pytest.raises(PreflightContractError):
        prepare_catalog_query(contract, "unknown", {})
    with pytest.raises(PreflightContractError):
        prepare_catalog_query(contract, "catalog_relations", {"page_size": 100, "offset": True})
    with pytest.raises(PreflightContractError):
        prepare_catalog_query(contract, "migration_ledger", {"after_name": "unsafe value", "page_size": 100})


def test_transaction_adapter_sequence_is_exact_server_enforced_and_rollback_only(contract: dict):
    commands = catalog_adapter_commands(contract)
    assert [item.sequence for item in commands] == [1, 2, 3, 4, 5, 6]
    assert commands[0].value == "BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY"
    assert commands[1].value == "SET LOCAL statement_timeout = '5000ms'"
    assert commands[2].value == "SET LOCAL lock_timeout = '1000ms'"
    assert commands[3].value == "SET LOCAL idle_in_transaction_session_timeout = '10000ms'"
    assert commands[-1].value == "ROLLBACK"
    assert contract["transaction_policy"]["generic_sql_allowed"] is False
    changed = copy.deepcopy(contract)
    changed["transaction_policy"]["adapter_command_sequence"][-1]["value"] = "COMMIT"
    with pytest.raises(PreflightContractError):
        validate_contract_shape(changed)


def test_every_query_shape_has_a_nonempty_positive(contract: dict):
    for query in contract["query_catalog"]:
        rows = [] if query["id"] == "catalog_sequence_grants" else [_safe_row(contract, query)]
        summary = validate_query_replay(contract, query["id"], _pages(query, rows))
        assert summary.query_id == query["id"]
        assert summary.row_count == len(rows)
        assert summary.timeout_policy_sha256 == canonical_json_sha256(contract["transaction_policy"]["adapter_command_sequence"])


@pytest.mark.parametrize("count", [100, 150, 200])
def test_keyset_pagination_requires_terminal_short_page_for_exact_multiples(contract: dict, count: int):
    query = _query(contract, "migration_ledger")
    rows = [
        {"migration_name": f"20200101_fixture_{index:06d}", "checksum_marker": "sha256:" + f"{index:064x}"}
        for index in range(count)
    ]
    pages = _pages(query, rows)
    summary = validate_query_replay(contract, query["id"], pages)
    assert summary.row_count == count
    assert len(pages) == (count // 100 + 1)
    assert len(pages[-1]["rows"]) == count % 100


@pytest.mark.parametrize("count", [100, 200])
def test_offset_pagination_requires_empty_sentinel_for_exact_multiples(contract: dict, count: int):
    query = _query(contract, "catalog_relations")
    rows = [_safe_row(contract, query, index) for index in range(count)]
    pages = _pages(query, rows)
    summary = validate_query_replay(contract, query["id"], pages)
    assert summary.row_count == count
    assert pages[-1]["rows"] == []


@pytest.mark.parametrize("kind", ["truncated", "cursor", "offset", "total", "timeout_flag", "timeout_value", "shape", "duplicate", "short_nonterminal"])
def test_pagination_shape_and_server_timeout_negatives(contract: dict, kind: str):
    query = _query(contract, "migration_ledger")
    rows = [{"migration_name": f"20200101_fixture_{index:06d}", "checksum_marker": "sha256:" + f"{index:064x}"} for index in range(100)]
    pages = _pages(query, rows)
    if kind == "truncated":
        pages.pop()
    elif kind == "cursor":
        pages[-1]["request_cursor"] = "20200101_wrong_000000"
    elif kind == "offset":
        pages[0]["request_offset"] = 0
    elif kind == "total":
        pages[-1]["total_count"] = 99
    elif kind == "timeout_flag":
        pages[0]["timeout_enforced"] = False
    elif kind == "timeout_value":
        pages[0]["server_timeout_ms"] = 4999
    elif kind == "shape":
        pages[0]["rows"][0]["extra"] = "x"
    elif kind == "duplicate":
        pages[0]["rows"][1] = copy.deepcopy(pages[0]["rows"][0])
    else:
        pages[0]["rows"].pop()
        pages[0]["end_index"] -= 1
    with pytest.raises(PreflightContractError):
        validate_query_replay(contract, query["id"], pages)


def test_semantic_acceptance_rejects_acl_view_constraint_and_exec_sql_hazards(contract: dict):
    cases = []
    schema = _query(contract, "catalog_schema_acl")
    row = _safe_row(contract, schema)
    row.update(grantee="PUBLIC", privilege_type="CREATE")
    cases.append((schema, row))
    grants = _query(contract, "catalog_table_grants")
    row = _safe_row(contract, grants)
    row.update(grantee="anon", privilege_type="UPDATE")
    cases.append((grants, row))
    views = _query(contract, "catalog_views")
    row = _safe_row(contract, views)
    row.update(schema_name="public", security_options="")
    cases.append((views, row))
    constraints = _query(contract, "catalog_constraints")
    row = _safe_row(contract, constraints)
    row["validated"] = False
    cases.append((constraints, row))
    routines = _query(contract, "catalog_routines")
    row = _safe_row(contract, routines)
    row.update(routine_name="exec_sql", security_definer=True, language_name="plpgsql", runtime_settings="search_path=\"\"", identity_arguments="text", result_type="jsonb", owner_name="postgres")
    cases.append((routines, row))
    for query, unsafe_row in cases:
        with pytest.raises(PreflightContractError):
            validate_query_replay(contract, query["id"], _pages(query, [unsafe_row]))


def test_package_acl_allowlists_reject_grantable_unknown_columns_and_sequences(contract: dict):
    table = _query(contract, "catalog_table_grants")
    allowed_table = _safe_row(contract, table)
    assert validate_query_replay(contract, table["id"], _pages(table, [allowed_table])).row_count == 1
    grantable = copy.deepcopy(allowed_table)
    grantable["is_grantable"] = True
    with pytest.raises(PreflightContractError, match="allowlist"):
        validate_query_replay(contract, table["id"], _pages(table, [grantable]))

    column = _query(contract, "catalog_column_grants")
    forbidden_column = _safe_row(contract, column)
    forbidden_column["column_name"] = "view_count"
    with pytest.raises(PreflightContractError, match="allowlist"):
        validate_query_replay(contract, column["id"], _pages(column, [forbidden_column]))

    sequence = _query(contract, "catalog_sequence_grants")
    sequence_row = _safe_row(contract, sequence)
    with pytest.raises(PreflightContractError, match="sequence"):
        validate_query_replay(contract, sequence["id"], _pages(sequence, [sequence_row]))


def test_exec_sql_exact_signature_owner_search_path_uniqueness_and_normalized_acl(contract: dict):
    routines = _query(contract, "catalog_routines")
    metadata = _safe_row(contract, routines)
    metadata.update(
        schema_name="public", routine_name="exec_sql", identity_arguments="sql_text text",
        language_name="plpgsql", security_definer=True, runtime_settings='search_path=""',
        owner_name="postgres", result_type="jsonb",
    )
    assert validate_query_replay(contract, routines["id"], _pages(routines, [metadata])).row_count == 1
    for field, value in (
        ("identity_arguments", "text"), ("owner_name", "other"), ("runtime_settings", "search_path=public"),
        ("result_type", "text"), ("security_definer", False),
    ):
        changed = copy.deepcopy(metadata)
        changed[field] = value
        with pytest.raises(PreflightContractError, match="exec_sql"):
            validate_query_replay(contract, routines["id"], _pages(routines, [changed]))

    duplicate = copy.deepcopy(metadata)
    duplicate["identity_arguments"] = "sql_text text, unsafe boolean"
    with pytest.raises(PreflightContractError, match="unique"):
        validate_query_replay(contract, routines["id"], _pages(routines, [metadata, duplicate]))

    grants = _query(contract, "catalog_routine_grants")
    acl = _safe_row(contract, grants)
    acl.update(
        schema_name="public", routine_name="exec_sql", identity_arguments="sql_text text",
        grantee="service_role", privilege_type="EXECUTE", is_grantable=False,
    )
    assert validate_query_replay(contract, grants["id"], _pages(grants, [acl])).row_count == 1
    for field, value in (("grantee", "anon"), ("identity_arguments", "text"), ("is_grantable", True)):
        changed = copy.deepcopy(acl)
        changed[field] = value
        with pytest.raises(PreflightContractError, match="ACL"):
            validate_query_replay(contract, grants["id"], _pages(grants, [changed]))


def test_http_catalog_is_one_precise_public_schema_probe_and_capabilities_are_local(contract: dict):
    assert len(contract["http_catalog"]) == 1
    operation = contract["http_catalog"][0]
    assert operation["id"] == "postgrest_public_schema_probe"
    assert operation["path_template"] == _REST_V1 + "/"
    assert operation["method"] == "GET"
    assert operation["auth_class"] == "supabase_publishable_apikey_only"
    assert operation["header_names"] == ["Accept", _API_KEY_HEADER]
    assert operation["query_parameters"] == []
    assert operation["response_content_type"] == "application/openapi+json"
    assert {item["id"] for item in contract["local_capability_catalog"]} == {
        "backup_capability", "writer_pause_capability", "rollback_capability"
    }
    assert not {"backup_capability", "writer_pause_capability", "rollback_capability"}.intersection({item["id"] for item in contract["http_catalog"]})


def test_http_nonempty_schema_pagination_and_negatives(contract: dict):
    operation = contract["http_catalog"][0]
    rows = [{"openapi_version": "3.0.0", "path_count": 10, "definition_count": 5}]
    pages = _pages(operation, rows)
    summary = validate_http_observation(contract, operation["id"], pages)
    assert summary.item_count == 1
    for mutation in ("wrong_offset", "extra_field", "bad_type", "bad_timeout"):
        changed = copy.deepcopy(pages)
        if mutation == "wrong_offset":
            changed[-1]["request_offset"] = 2
        elif mutation == "extra_field":
            changed[0]["rows"][0]["url"] = "synthetic"
        elif mutation == "bad_type":
            changed[0]["rows"][0]["openapi_version"] = 1
        else:
            changed[0]["timeout_enforced"] = False
        with pytest.raises(PreflightContractError):
            validate_http_observation(contract, operation["id"], changed)


def test_advisor_tool_catalog_is_precise_and_non_executable(contract: dict):
    assert contract["tool_catalog"] == [
        {"id": "security_advisors", "adapter_identity": "supabase-free.get_advisors", "arguments": {"type": "security"}, "project_binding": "FREE_SUPABASE_PROJECT_REF", "timeout_ms": 5000, "executable_in_f9_3": False, "response_projection": ["advisory_count", "levels_sha256", "payload_sha256"]},
        {"id": "performance_advisors", "adapter_identity": "supabase-free.get_advisors", "arguments": {"type": "performance"}, "project_binding": "FREE_SUPABASE_PROJECT_REF", "timeout_ms": 5000, "executable_in_f9_3": False, "response_projection": ["advisory_count", "levels_sha256", "payload_sha256"]},
    ]
    for tool in contract["tool_catalog"]:
        summary = validate_tool_observation(contract, {"tool_id": tool["id"], "item_count": 1, "levels_sha256": "1" * 64, "payload_sha256": "2" * 64})
        assert summary.tool_id == tool["id"]
    with pytest.raises(PreflightContractError):
        validate_tool_observation(contract, {"tool_id": "unknown", "item_count": 0, "levels_sha256": "1" * 64, "payload_sha256": "2" * 64})


def test_evidence_api_only_validates_neutral_future_f94_envelopes(contract: dict):
    schema = contract["evidence_schema"]
    evidence = {field: "1" * 64 for field in schema["digest_fields"]}
    evidence.update({field: 0 for field in schema["count_fields"]})
    evidence.update(schema_version=3, status="PASS")
    assert set(evidence) == set(schema["pass_fields"])
    assert validate_evidence_structure(contract, evidence) is None
    assert not hasattr(free_preflight, "build_evidence")
    assert not hasattr(free_preflight, "evidence_payload")

    failed = dict(evidence)
    failed.update(status="FAIL", failure_code="TRANSPORT_ERROR", failed_operation_id_sha256="2" * 64)
    assert set(failed) == set(schema["fail_fields"])
    assert validate_evidence_structure(contract, failed) is None
    for mutation in ("extra", "raw", "bad_failure"):
        changed = copy.deepcopy(failed)
        if mutation == "extra":
            changed["details"] = "not allowed"
        elif mutation == "raw":
            changed["rows"] = []
        else:
            changed["failure_code"] = "ARBITRARY"
        with pytest.raises(PreflightContractError):
            validate_evidence_structure(contract, changed)


def test_sql_http_and_tool_raw_trace_schemas_are_closed_and_neutral(contract: dict):
    digest = "3" * 64
    sql_trace = {
        "schema_version": 1, "target_identity_sha256": digest, "session_id_sha256": digest,
        "command_sequence_sha256": canonical_json_sha256(contract["transaction_policy"]["adapter_command_sequence"]),
        "query_ids": [item["id"] for item in contract["query_catalog"]],
        "query_page_digests": [
            {"query_id": item["id"], "page_count": 1, "pages_sha256": digest}
            for item in contract["query_catalog"]
        ],
        "timeout_settings": {"statement_timeout_ms": 5000, "lock_timeout_ms": 1000, "idle_in_transaction_timeout_ms": 10000},
        "rollback_completed": True,
    }
    assert validate_sql_trace_structure(contract, sql_trace) is None
    operation = contract["http_catalog"][0]
    http_trace = {
        "schema_version": 1, "target_identity_sha256": digest, "operation_id": operation["id"],
        "method": "GET", "origin_binding": "FREE_SUPABASE_URL", "path": _REST_V1 + "/",
        "query_parameter_names": [], "header_names": ["Accept", _API_KEY_HEADER],
        "auth_class": "supabase_publishable_apikey_only", "status_code": 200, "redirected": False,
        "request_body_present": False, "content_type": "application/openapi+json",
        "response_size_bytes": 123, "page_count": 1, "pages_sha256": digest,
    }
    assert validate_http_trace_structure(contract, http_trace) is None
    tool = contract["tool_catalog"][0]
    tool_trace = {
        "schema_version": 1, "target_identity_sha256": digest, "tool_id": tool["id"],
        "adapter_identity": tool["adapter_identity"], "arguments": tool["arguments"],
        "project_binding": tool["project_binding"], "project_identity_sha256": digest,
        "timeout_ms": 5000, "response_projection": tool["response_projection"],
        "response_sha256": digest, "item_count": 0,
    }
    assert validate_tool_trace_structure(contract, tool_trace) is None
    for validator, trace in (
        (validate_sql_trace_structure, sql_trace),
        (validate_http_trace_structure, http_trace),
        (validate_tool_trace_structure, tool_trace),
    ):
        changed = copy.deepcopy(trace)
        changed["raw_payload"] = "forbidden"
        with pytest.raises(PreflightContractError):
            validator(contract, changed)
        for mutation in ("missing", "boolean", "integer", "string", "extra"):
            changed = copy.deepcopy(trace)
            if mutation == "missing":
                changed.pop("schema_version")
            elif mutation == "boolean":
                changed["schema_version"] = False
            elif mutation == "integer":
                changed["schema_version"] = 2
            elif mutation == "string":
                changed["schema_version"] = "1"
            else:
                changed["schema_versions"] = [1]
            with pytest.raises(PreflightContractError):
                validator(contract, changed)


def test_synthetic_self_test_is_deterministic_but_never_claims_remote_evidence(contract: dict):
    first = run_synthetic_self_test(contract)
    second = run_synthetic_self_test(contract)
    assert first == second
    assert first[0] == 22
    assert re.fullmatch(r"[0-9a-f]{64}", first[1])


def test_standalone_cli_needs_no_pythonpath_and_exposes_only_two_local_modes():
    validate = _run_cli("--contract", CONTRACT_PATH, "--validate-only")
    assert validate.returncode == 0, validate.stdout + validate.stderr
    assert "status=LOCAL_VALID" in validate.stdout
    assert "git_proof=EXTERNAL_REQUIRED" in validate.stdout
    assert "PASS" not in validate.stdout and "FAIL" not in validate.stdout
    synthetic = _run_cli("--contract", CONTRACT_PATH, "--synthetic-self-test")
    assert synthetic.returncode == 0, synthetic.stdout + synthetic.stderr
    assert "status=LOCAL_VALID" in synthetic.stdout
    assert "PYTHONPATH" not in synthetic.stdout
    assert "PASS" not in synthetic.stdout and "FAIL" not in synthetic.stdout
    for args in (
        (),
        ("--contract", CONTRACT_PATH),
        ("--contract", CONTRACT_PATH, "--remote"),
        ("--contract", CONTRACT_PATH, "--apply"),
        ("--contract", CONTRACT_PATH, "--validate-only", "--remote"),
        ("--contract", CONTRACT_PATH, "--validate-only", "--synthetic-self-test"),
        ("--validate-only", "--contract", CONTRACT_PATH),
    ):
        result = _run_cli(*args)
        assert result.returncode != 0
        assert result.stdout == ""
        assert result.stderr.strip() == "F9_3_CONTRACT git_proof=EXTERNAL_REQUIRED"
        assert "PASS" not in result.stderr and "FAIL" not in result.stderr


def test_runner_has_no_project_subprocess_os_env_dotenv_or_network_dependency(contract: dict):
    source = (ROOT / "scripts/maintenance/free_preflight.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imports.update(
        node.module.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    )
    assert imports.isdisjoint({"os", "subprocess", "socket", "requests", "httpx", "urllib", "http", "dotenv", "scripts"})
    assert "migration_manifest" not in source
    assert "os.environ" not in source
    assert "getenv" not in source
    assert "load_dotenv" not in source
    assert "subprocess." not in source
    assert "socket." not in source
    assert "requests." not in source
    assert contract["implementation_binding"]["transitive_project_modules"] == []


def test_fresh_import_and_validation_survive_capability_traps():
    guard = r'''
import os
import socket
import subprocess
import dotenv
import requests

def unexpected(*args, **kwargs):
    raise AssertionError("unexpected capability")

os.getenv = unexpected
socket.socket = unexpected
socket.create_connection = unexpected
subprocess.run = unexpected
dotenv.load_dotenv = unexpected
dotenv.dotenv_values = unexpected
requests.sessions.Session.request = unexpected

from scripts.maintenance.free_preflight import load_contract, validate_contract_files, run_synthetic_self_test
c = load_contract("db/manifests/f9_3_free_preflight_contract.json")
validate_contract_files(c)
assert run_synthetic_self_test(c)[0] > 0
'''
    result = subprocess.run(
        [sys.executable, "-c", guard],
        cwd=ROOT,
        env={"HOME": "/tmp", "PATH": os.environ["PATH"]},
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_ci_uses_network_namespace_none_boundary_and_preserves_cleanup():
    workflow = (ROOT / ".github/workflows/security-audit.yml").read_text(encoding="utf-8")
    job = workflow.split("  fase09-free-preflight-contract:", 1)[1].split("  fase10-promotion-contract:", 1)[0]
    assert "environment:" not in job
    assert "secrets." not in job
    assert "services:" not in job
    assert "fetch-depth: 0" in job
    assert job.index("Install test dependencies") < job.index("Block all egress")
    assert job.count("sudo unshare --net") >= 3
    assert job.count("ip link set lo down") >= 3
    assert job.count("set -euo pipefail") >= 3
    assert job.count("--bounding-set=-all") >= 3
    assert job.count("--no-new-privs") >= 3
    assert job.count("--reuid=") >= 3
    assert "PYTHONPATH" not in job
    assert "tests/test_fase09_free_preflight.py" in job
    assert "--validate-only" in job and "--synthetic-self-test" in job
    assert "name: Restore runner network" in job
    cleanup = job.split("name: Restore runner network", 1)[1]
    assert "ipv4-owned" in cleanup and "ipv6-owned" in cleanup
    assert "-C OUTPUT -j FASE093_EGRESS" in cleanup
    assert "-D OUTPUT -j FASE093_EGRESS" in cleanup
    assert "|| true" not in cleanup
    assert "exit \"$cleanup_failed\"" in cleanup


def test_f6_f10_package_hashes_and_blocked_state_are_unchanged(contract: dict):
    assert contract["package_binding"]["manifest"]["canonical_json_sha256"] == free_preflight.F8_MANIFEST_SHA256
    assert contract["package_binding"]["promotion_contract"]["canonical_json_sha256"] == free_preflight.F10_DESCRIPTOR_SHA256
    assert contract["package_binding"]["status"] == "reconciled_not_certified"
    assert contract["package_binding"]["blocked_targets"] == ["free", "pro"]
    assert "attestations" not in contract
