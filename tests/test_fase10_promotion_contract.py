from __future__ import annotations

import copy
import contextlib
import hashlib
import inspect
import json
import os
import socket
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import dotenv
import pytest
import requests

from scripts.maintenance import check_db_parity, migration_manifest
from scripts.maintenance.migration_manifest import (
    ALLOWED_TARGETS,
    F10_EXCLUSIONS,
    F10_PAYLOAD_ENTRIES,
    F10_SOURCE_MANIFEST_SHA256,
    F10_STATES,
    F10_TRANSITIONS,
    MANIFEST_CONTRACTS,
    ManifestError,
    canonical_json_bytes,
    canonical_json_sha256,
    canonical_sql_sha256,
    derive_target_fingerprint,
    derive_effective_state,
    load_attestation_inventory,
    load_manifest,
    load_promotion_contract,
    reject_v1_circular_prerequisites,
    require_schema_apply_allowed,
    schema_apply_is_blocked,
    strict_json_loads,
    target_fingerprints_match,
    validate_attestation,
    validate_attestation_inventory_structure,
    validate_inventory_git_content,
    validate_local_git_binding,
    validate_promotion_descriptor,
)


ROOT = Path(__file__).resolve().parents[1]
DESCRIPTOR_PATH = ROOT / "db/manifests/fase10_promotion_contract.json"
F8_MANIFEST = ROOT / "db/manifests/fase08_candidate.json"
FIXED_CLOCK = datetime(2026, 7, 25, 18, 0, 0, tzinfo=timezone.utc)
SYNTHETIC_ORIGIN = "https://" + ("a" * 20) + ".supabase.co"
SYNTHETIC_KEY = "sb_" + "publishable_" + "synthetic_f10_key"
EXPECTED_TARGET_FINGERPRINT = derive_target_fingerprint(
    SYNTHETIC_ORIGIN, SYNTHETIC_KEY
)
_GIT_CONTEXT: dict[str, object] = {}


def _run_fixture_git(repo: Path, *argv: str) -> subprocess.CompletedProcess[str]:
    environment = {
        "HOME": "/tmp",
        "PATH": os.environ["PATH"],
        "LANG": "C",
        "LC_ALL": "C",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_TERMINAL_PROMPT": "0",
    }
    return subprocess.run(
        ["git", *argv],
        cwd=repo,
        env=environment,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=10,
        check=True,
        shell=False,
    )


@pytest.fixture(scope="session", autouse=True)
def _real_git_repository(tmp_path_factory: pytest.TempPathFactory):
    repo = tmp_path_factory.mktemp("f10-git")
    _run_fixture_git(repo, "init", "--quiet")
    commits: list[tuple[str, str]] = []
    tracked = repo / "candidate.txt"
    for index in range(1, 6):
        tracked.write_text(f"candidate-{index}\n", encoding="utf-8")
        _run_fixture_git(repo, "add", "candidate.txt")
        _run_fixture_git(
            repo,
            "-c",
            "user.name=F10 Synthetic",
            "-c",
            "user.email=f10-synthetic@example.invalid",
            "commit",
            "--quiet",
            "-m",
            f"synthetic-{index}",
        )
        commit = _run_fixture_git(repo, "rev-parse", "HEAD").stdout.strip()
        tree = _run_fixture_git(repo, "rev-parse", "HEAD^{tree}").stdout.strip()
        commits.append((commit, tree))
    _run_fixture_git(repo, "checkout", "--quiet", "--orphan", "unrelated")
    _run_fixture_git(repo, "rm", "--quiet", "--force", "candidate.txt")
    (repo / "unrelated.txt").write_text("unrelated\n", encoding="utf-8")
    _run_fixture_git(repo, "add", "unrelated.txt")
    _run_fixture_git(
        repo,
        "-c",
        "user.name=F10 Synthetic",
        "-c",
        "user.email=f10-synthetic@example.invalid",
        "commit",
        "--quiet",
        "-m",
        "synthetic-unrelated",
    )
    unrelated_commit = _run_fixture_git(repo, "rev-parse", "HEAD").stdout.strip()
    _run_fixture_git(repo, "checkout", "--quiet", "--detach", commits[4][0])
    _GIT_CONTEXT.update(
        repo=repo,
        candidates=tuple(commits[:4]),
        base_commit_sha=commits[4][0],
        unrelated_commit_sha=unrelated_commit,
        inventory_counter=0,
    )
    yield
    _GIT_CONTEXT.clear()


@pytest.fixture(autouse=True)
def _block_environment_loaders_and_transport(monkeypatch: pytest.MonkeyPatch):
    def unexpected(*_args, **_kwargs):
        raise AssertionError("F10 local contract attempted environment or transport")

    monkeypatch.setattr(dotenv, "load_dotenv", unexpected)
    monkeypatch.setattr(dotenv, "dotenv_values", unexpected)
    monkeypatch.setattr(socket, "socket", unexpected)
    monkeypatch.setattr(socket, "create_connection", unexpected)
    monkeypatch.setattr(requests.sessions.Session, "request", unexpected)


@pytest.fixture
def descriptor() -> dict:
    return load_promotion_contract(DESCRIPTOR_PATH)


def _digest(value: int) -> str:
    return f"{value:064x}"


def _git_sha(value: int) -> str:
    return f"{value:040x}"


def _chain(descriptor: dict, length: int = 4) -> list[dict]:
    descriptor_hash = canonical_json_sha256(descriptor)
    source_hash = descriptor["source_manifest"]["canonical_json_sha256"]
    previous_hash = None
    chain: list[dict] = []
    for index, transition in enumerate(descriptor["transitions"][:length], start=1):
        commit_sha, tree_sha = _GIT_CONTEXT["candidates"][index - 1]
        created = datetime(2026, 7, 25, 12 + index, tzinfo=timezone.utc)
        created_text = created.strftime("%Y-%m-%dT%H:%M:%SZ")
        evidence = []
        for evidence_index, evidence_type in enumerate(
            transition["evidence_types"], start=1
        ):
            evidence.append(
                {
                    "type": evidence_type,
                    "sha256": _digest(index * 100 + evidence_index),
                    "observed_at": (created - timedelta(minutes=5)).strftime(
                        "%Y-%m-%dT%H:%M:%SZ"
                    ),
                    "expires_at": (created + timedelta(hours=1)).strftime(
                        "%Y-%m-%dT%H:%M:%SZ"
                    ),
                }
            )
        attestation = {
            "schema_version": 1,
            "attestation_id": (
                f"ATT-{transition['id']}-{created.strftime('%Y%m%dT%H%M%SZ')}-"
                f"{index:012x}"
            ),
            "transition_id": transition["id"],
            "from_state": transition["from"],
            "to_state": transition["to"],
            "target_environment": "free",
            "target_fingerprint_sha256": EXPECTED_TARGET_FINGERPRINT,
            "package_id": descriptor["package_id"],
            "descriptor_sha256": descriptor_hash,
            "source_manifest_sha256": source_hash,
            "commit_sha": commit_sha,
            "tree_sha": tree_sha,
            "operation_owner": descriptor["approval_policy"]["owner"],
            "previous_attestation_sha256": previous_hash,
            "created_at": created_text,
            "result": "PASS",
            "approval": {
                "github_login": descriptor["approval_policy"]["reviewer"],
                "review_id": index,
                "reviewed_commit_sha": commit_sha,
                "decision": "APPROVED",
            },
            "evidence": evidence,
        }
        chain.append(attestation)
        previous_hash = canonical_json_sha256(attestation)
    return chain


def _mutated(value):
    return copy.deepcopy(value)


@contextlib.contextmanager
def _inventory(chain: list[dict]):
    root = _GIT_CONTEXT["repo"]
    base_commit = _GIT_CONTEXT["base_commit_sha"]
    _run_fixture_git(root, "reset", "--quiet", "--hard", base_commit)
    _run_fixture_git(root, "clean", "-fd", "--", "db")
    try:
        directory = root / "db/attestations/hito1"
        directory.mkdir(parents=True)
        for index, attestation in enumerate(chain):
            path = directory / f"{attestation['attestation_id']}.json"
            if path.exists():
                path = directory / f"duplicate-{index}.json"
            path.write_bytes(canonical_json_bytes(attestation))
        inventory = load_attestation_inventory(root=root)
        descriptor_path = root / "db/manifests/fase10_promotion_contract.json"
        descriptor_path.parent.mkdir(parents=True, exist_ok=True)
        descriptor_path.write_bytes(DESCRIPTOR_PATH.read_bytes())
        _run_fixture_git(root, "add", "--", "db")
        counter = int(_GIT_CONTEXT["inventory_counter"]) + 1
        _GIT_CONTEXT["inventory_counter"] = counter
        _run_fixture_git(
            root,
            "-c",
            "user.name=F10 Synthetic",
            "-c",
            "user.email=f10-synthetic@example.invalid",
            "commit",
            "--quiet",
            "-m",
            f"synthetic-inventory-{counter}",
        )
        attestation_commit = _run_fixture_git(
            root, "rev-parse", "HEAD"
        ).stdout.strip()
        yield inventory, attestation_commit
    finally:
        _run_fixture_git(root, "reset", "--quiet", "--hard", base_commit)
        _run_fixture_git(root, "clean", "-fd", "--", "db")


def _derive(descriptor: dict, attestations: list[dict], **kwargs) -> str:
    with _inventory(attestations) as (inventory, attestation_commit):
        validate_attestation_inventory_structure(
            descriptor,
            inventory,
            expected_target_fingerprint=EXPECTED_TARGET_FINGERPRINT,
            repo_root=_GIT_CONTEXT["repo"],
            attestation_commit_sha=attestation_commit,
            **kwargs,
        )
        if not attestations:
            return descriptor["initial_state"]
        return descriptor["transitions"][len(attestations) - 1]["to"]


def _copy_contract_tree(root: Path) -> Path:
    (root / "db/manifests").mkdir(parents=True)
    (root / "db/migrations").mkdir(parents=True)
    descriptor_target = root / "db/manifests/fase10_promotion_contract.json"
    descriptor_target.write_bytes(DESCRIPTOR_PATH.read_bytes())
    (root / "db/manifests/fase08_candidate.json").write_bytes(
        F8_MANIFEST.read_bytes()
    )
    descriptor = strict_json_loads(DESCRIPTOR_PATH.read_bytes())
    for entry in descriptor["payload_entries"]:
        target = root / entry["path"]
        target.write_bytes((ROOT / entry["path"]).read_bytes())
    return descriptor_target


def test_p01_exact_descriptor_starts_blocked_without_attestations(descriptor: dict):
    assert "current_status" not in descriptor
    assert derive_effective_state(descriptor, []) == "reconciled_not_certified"
    assert schema_apply_is_blocked(descriptor, "reconciled_not_certified", "free")
    assert schema_apply_is_blocked(descriptor, "reconciled_not_certified", "pro")
    with pytest.raises(ManifestError, match="blocked"):
        require_schema_apply_allowed(
            descriptor, "reconciled_not_certified", "free"
        )


@pytest.mark.parametrize(
    ("length", "state"),
    [
        (1, "ready_for_free"),
        (2, "free_schema_certified"),
        (3, "free_backfill_certified"),
        (4, "free_certified"),
    ],
)
def test_p02_to_p05_full_synthetic_chains_use_exact_mapping(
    descriptor: dict, length: int, state: str
):
    chain = _chain(descriptor, length)
    assert _derive(descriptor, chain, clock=FIXED_CLOCK) == state


def test_p06_payload_hashes_and_json_identity_are_cross_platform(descriptor: dict):
    source_bytes = F8_MANIFEST.read_bytes()
    source = strict_json_loads(source_bytes)
    crlf_source = strict_json_loads(source_bytes.replace(b"\n", b"\r\n"))
    assert canonical_json_bytes(source) == canonical_json_bytes(crlf_source)
    assert canonical_json_sha256(source) == F10_SOURCE_MANIFEST_SHA256
    assert descriptor["payload_entries"] == source["entries"]
    for entry in descriptor["payload_entries"]:
        assert canonical_sql_sha256(ROOT / entry["path"]) == entry["sha256"]


def test_target_fingerprint_derivation_is_exact_and_deterministic():
    origin = "https://" + ("a" * 20) + ".supabase.co"
    key = "sb_" + "publishable_" + "synthetic_f10_key"
    key_hash = hashlib.sha256(key.encode("utf-8")).hexdigest()
    expected = hashlib.sha256(
        (
            "studiamatch-target-v1\0free\0"
            f"{origin}\0{key_hash}"
        ).encode("utf-8")
    ).hexdigest()

    assert derive_target_fingerprint(origin, key) == expected
    assert derive_target_fingerprint(origin, key) == expected
    assert target_fingerprints_match(expected, expected)
    assert not target_fingerprints_match(expected, "0" * 64)


@pytest.mark.parametrize(
    "origin",
    [
        "not-an-origin",
        "http://" + ("a" * 20) + ".supabase.co",
        "https://" + ("a" * 20) + ".supabase.co/",
        "https://" + ("a" * 20) + ".supabase.co/path",
        "https://" + ("a" * 20) + ".supabase.co:443",
        "https://" + ("a" * 20) + ".supabase.co?mode=test",
        "https://" + ("a" * 20) + ".supabase.co#fragment",
        "https://user@" + ("a" * 20) + ".supabase.co",
        "https://" + ("a" * 19) + ".supabase.co",
        "https://" + ("a" * 19) + "-" + ".supabase.co",
        "https://" + ("A" * 20) + ".supabase.co",
        "https://pro.supabase.co",
    ],
)
def test_target_fingerprint_rejects_noncanonical_origins(origin: str):
    key = "sb_" + "publishable_" + "synthetic_f10_key"
    with pytest.raises(ManifestError, match="origin"):
        derive_target_fingerprint(origin, key)


@pytest.mark.parametrize(
    "key",
    [
        "",
        "synthetic",
        "sb_" + "publishable_",
        "sb_" + "publishable_" + "contains space",
        "sb_" + "secret_" + "synthetic_f10_key",
        "SB_" + "PUBLISHABLE_" + "synthetic_f10_key",
    ],
)
def test_target_fingerprint_rejects_invalid_keys_without_reflecting_them(key: str):
    origin = "https://" + ("a" * 20) + ".supabase.co"
    with pytest.raises(ManifestError, match="modern format") as exc_info:
        derive_target_fingerprint(origin, key)
    if key:
        assert key not in str(exc_info.value)


@pytest.mark.parametrize("value", ["invalid", "A" * 64, "0" * 63, None])
def test_target_fingerprint_comparison_rejects_malformed_values(value):
    with pytest.raises(ManifestError, match="lowercase SHA-256"):
        target_fingerprints_match("0" * 64, value)


@pytest.mark.parametrize(
    "raw",
    [
        '{"a":1,"a":2}',
        '{"value":1.5}',
        '{"value":NaN}',
        '{"value":Infinity}',
        '{"value":"e\u0301"}',
        '{"e\u0301":true}',
    ],
)
def test_n01_strict_project_jcs_rejects_ambiguous_json(raw: str):
    with pytest.raises(ManifestError):
        strict_json_loads(raw)


@pytest.mark.parametrize(
    "value",
    [{1: "non-string-key"}, {"value": 1.0}, {"value": (1, 2)}, {"value": b"x"}],
)
def test_n01_canonicalizer_rejects_unsupported_python_types(value):
    with pytest.raises(ManifestError):
        canonical_json_bytes(value)


def test_n01_descriptor_schema_is_closed_and_hashes_are_lowercase(descriptor: dict):
    extra = _mutated(descriptor)
    extra["unknown"] = True
    with pytest.raises(ManifestError, match="closed"):
        validate_promotion_descriptor(extra)
    missing = _mutated(descriptor)
    del missing["phase"]
    with pytest.raises(ManifestError, match="closed"):
        validate_promotion_descriptor(missing)
    malformed = _mutated(descriptor)
    malformed["source_manifest"]["canonical_json_sha256"] = "A" * 64
    with pytest.raises(ManifestError, match="lowercase"):
        validate_promotion_descriptor(malformed)

    attestation = _chain(descriptor, 1)[0]
    attestation["unknown"] = True
    with pytest.raises(ManifestError, match="closed"):
        _derive(descriptor, [attestation])
    del attestation["unknown"]
    del attestation["tree_sha"]
    with pytest.raises(ManifestError, match="closed"):
        _derive(descriptor, [attestation])


def test_n01_bool_is_never_accepted_as_schema_or_review_integer(descriptor: dict):
    bool_schema = _mutated(descriptor)
    bool_schema["schema_version"] = True
    with pytest.raises(ManifestError, match="schema"):
        validate_promotion_descriptor(bool_schema)

    attestation_schema = _chain(descriptor, 1)
    attestation_schema[0]["schema_version"] = True
    with pytest.raises(ManifestError, match="schema_version"):
        _derive(descriptor, attestation_schema)

    bool_review = _chain(descriptor, 1)
    bool_review[0]["approval"]["review_id"] = True
    with pytest.raises(ManifestError, match="approval"):
        _derive(descriptor, bool_review)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value["source_manifest"].__setitem__("package_id", "drift"),
        lambda value: value["payload_entries"][0].__setitem__("id", "drift"),
        lambda value: value["payload_entries"].reverse(),
        lambda value: value["payload_entries"][0].__setitem__("sha256", "0" * 64),
        lambda value: value["payload_entries"][0].__setitem__("provenance", "drift"),
        lambda value: value["payload_entries"][0].__setitem__("targets", ["free"]),
        lambda value: value["excluded"].__setitem__("canary", "drift"),
    ],
)
def test_n02_source_payload_order_hash_provenance_target_and_exclusion_drift_fail(
    descriptor: dict, mutation
):
    changed = _mutated(descriptor)
    mutation(changed)
    with pytest.raises(ManifestError):
        validate_promotion_descriptor(changed)


def test_n02_live_source_payload_drift_is_detected(tmp_path: Path, descriptor: dict):
    (tmp_path / "db/manifests").mkdir(parents=True)
    (tmp_path / "db/migrations").mkdir(parents=True)
    changed_source = strict_json_loads(F8_MANIFEST.read_bytes())
    changed_source["entries"][0]["id"] = "drift"
    (tmp_path / "db/manifests/fase08_candidate.json").write_text(
        json.dumps(changed_source), encoding="utf-8"
    )
    with pytest.raises(ManifestError, match="source .*identity"):
        validate_promotion_descriptor(descriptor, root=tmp_path)


def test_source_raw_identity_rejects_semantically_equal_reformatting(
    tmp_path: Path, descriptor: dict
):
    _copy_contract_tree(tmp_path)
    source_path = tmp_path / "db/manifests/fase08_candidate.json"
    source = strict_json_loads(source_path.read_bytes())
    source_path.write_text(json.dumps(source, sort_keys=True), encoding="utf-8")
    with pytest.raises(ManifestError, match="raw LF identity"):
        validate_promotion_descriptor(descriptor, root=tmp_path)


def test_source_raw_identity_accepts_windows_crlf_normalization(
    tmp_path: Path, descriptor: dict
):
    descriptor_path = _copy_contract_tree(tmp_path)
    source_path = tmp_path / "db/manifests/fase08_candidate.json"
    source_path.write_bytes(
        source_path.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    )
    loaded = load_promotion_contract(descriptor_path, root=tmp_path)
    assert loaded["package_id"] == descriptor["package_id"]


def test_descriptor_source_and_migrations_reject_symlinks_and_wrong_paths(
    tmp_path: Path,
):
    descriptor_path = _copy_contract_tree(tmp_path)
    alternate = tmp_path / "alternate.json"
    alternate.write_bytes(descriptor_path.read_bytes())
    with pytest.raises(ManifestError, match="path is not canonical"):
        load_promotion_contract(alternate, root=tmp_path)

    descriptor_bytes = descriptor_path.read_bytes()
    descriptor_path.unlink()
    descriptor_real = tmp_path / "descriptor-real.json"
    descriptor_real.write_bytes(descriptor_bytes)
    try:
        descriptor_path.symlink_to(descriptor_real)
    except OSError:
        pytest.skip("symlinks are unavailable on this platform")
    with pytest.raises(ManifestError, match="symlink"):
        load_promotion_contract(descriptor_path, root=tmp_path)

    descriptor_path.unlink()
    descriptor_path.write_bytes(descriptor_bytes)
    source = tmp_path / "db/manifests/fase08_candidate.json"
    source_bytes = source.read_bytes()
    source.unlink()
    source_real = tmp_path / "source-real.json"
    source_real.write_bytes(source_bytes)
    source.symlink_to(source_real)
    with pytest.raises(ManifestError, match="symlink"):
        load_promotion_contract(descriptor_path, root=tmp_path)

    source.unlink()
    source.write_bytes(source_bytes)
    manifest = strict_json_loads(descriptor_bytes)
    migration = tmp_path / manifest["payload_entries"][0]["path"]
    migration_bytes = migration.read_bytes()
    migration.unlink()
    migration_real = tmp_path / "migration-real.sql"
    migration_real.write_bytes(migration_bytes)
    migration.symlink_to(migration_real)
    with pytest.raises(ManifestError, match="symlink"):
        load_promotion_contract(descriptor_path, root=tmp_path)


def test_n03_transition_drift_skip_reverse_fork_and_duplicate_fail(descriptor: dict):
    changed = _mutated(descriptor)
    changed["transitions"][0]["to"] = "free_schema_certified"
    with pytest.raises(ManifestError):
        validate_promotion_descriptor(changed)

    chain = _chain(descriptor, 2)
    for field, value in (
        ("transition_id", "T03_FREE_BACKFILL"),
        ("from_state", "free_schema_certified"),
        ("to_state", "reconciled_not_certified"),
    ):
        invalid = _mutated(chain)
        invalid[1][field] = value
        with pytest.raises(ManifestError, match="gap|consecutive"):
            _derive(descriptor, invalid)
    with pytest.raises(ManifestError):
        _derive(descriptor, [chain[0], chain[0]])


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value["states"]["reconciled_not_certified"].__setitem__(
            "schema_apply_blocked_targets", ["pro"]
        ),
        lambda value: value["states"]["reconciled_not_certified"].__setitem__(
            "next_capabilities", ["ACCEPT_FREE_READINESS", "REMOTE_READ_FREE"]
        ),
        lambda value: value["transitions"][0].__setitem__(
            "acceptance_capability", "REMOTE_READ_FREE"
        ),
    ],
)
def test_n04_blocked_targets_capability_order_and_acceptance_are_exact(
    descriptor: dict, mutation
):
    changed = _mutated(descriptor)
    mutation(changed)
    with pytest.raises(ManifestError):
        validate_promotion_descriptor(changed)


@pytest.mark.parametrize("kind", ["missing", "extra", "duplicate", "digest", "result"])
def test_n05_evidence_cardinality_digest_and_result_fail(descriptor: dict, kind: str):
    chain = _chain(descriptor, 1)
    attestation = chain[0]
    if kind == "missing":
        attestation["evidence"].pop()
    elif kind == "extra":
        attestation["evidence"].append(
            dict(attestation["evidence"][0], type="unexpected")
        )
    elif kind == "duplicate":
        attestation["evidence"][1]["type"] = attestation["evidence"][0]["type"]
    elif kind == "digest":
        attestation["evidence"][0]["sha256"] = "invalid"
    else:
        attestation["result"] = "FAIL"
    with pytest.raises(ManifestError):
        _derive(descriptor, chain)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("target_fingerprint_sha256", "b" * 64),
        ("package_id", "drift"),
        ("descriptor_sha256", "0" * 64),
        ("source_manifest_sha256", "0" * 64),
        ("commit_sha", "invalid"),
        ("tree_sha", "invalid"),
        ("operation_owner", "other"),
    ],
)
def test_n06_stable_target_and_identity_bindings_fail(
    descriptor: dict, field: str, value
):
    chain = _chain(descriptor, 2)
    chain[1][field] = value
    if field == "commit_sha":
        chain[1]["approval"]["reviewed_commit_sha"] = value
    with pytest.raises(ManifestError):
        _derive(descriptor, chain)


def test_n06_reviewer_commit_and_unique_review_evidence_bindings_fail(descriptor: dict):
    chain = _chain(descriptor, 2)
    cases = []
    reviewer = _mutated(chain)
    reviewer[1]["approval"]["github_login"] = "other"
    cases.append(reviewer)
    reviewed_commit = _mutated(chain)
    reviewed_commit[1]["approval"]["reviewed_commit_sha"] = _git_sha(999)
    cases.append(reviewed_commit)
    review_reuse = _mutated(chain)
    review_reuse[1]["approval"]["review_id"] = review_reuse[0]["approval"]["review_id"]
    cases.append(review_reuse)
    evidence_reuse = _mutated(chain)
    evidence_reuse[1]["evidence"][0]["sha256"] = evidence_reuse[0]["evidence"][0]["sha256"]
    cases.append(evidence_reuse)
    for invalid in cases:
        with pytest.raises(ManifestError):
            _derive(descriptor, invalid)


def test_n06_nonempty_chain_requires_inventory_fingerprint_and_git_binding(
    descriptor: dict,
):
    chain = _chain(descriptor, 1)

    with pytest.raises(ManifestError, match="complete loaded attestation inventory"):
        derive_effective_state(descriptor, chain)
    with _inventory(chain) as (inventory, attestation_commit):
        with pytest.raises(ManifestError, match="expected target fingerprint"):
            derive_effective_state(descriptor, inventory)
        with pytest.raises(ManifestError, match="does not match expected"):
            derive_effective_state(
                descriptor,
                inventory,
                expected_target_fingerprint="0" * 64,
                repo_root=_GIT_CONTEXT["repo"],
                attestation_commit_sha=attestation_commit,
            )
        with pytest.raises(ManifestError, match="repository and attestation commit"):
            derive_effective_state(
                descriptor,
                inventory,
                expected_target_fingerprint=EXPECTED_TARGET_FINGERPRINT,
            )

    arbitrary = _chain(descriptor, 1)
    arbitrary[0]["target_fingerprint_sha256"] = "a" * 64
    with pytest.raises(ManifestError, match="does not match expected"):
        _derive(descriptor, arbitrary)


def test_n06_new_attestation_requires_clock_and_git_validator(descriptor: dict):
    attestation = _chain(descriptor, 1)[0]
    with _inventory([attestation]) as (inventory, attestation_commit):
        with pytest.raises(ManifestError, match="injected UTC clock"):
            validate_attestation(
                descriptor,
                attestation,
                inventory=inventory,
                expected_target_fingerprint=EXPECTED_TARGET_FINGERPRINT,
                repo_root=_GIT_CONTEXT["repo"],
                attestation_commit_sha=attestation_commit,
            )
        with pytest.raises(ManifestError, match="repository and attestation commit"):
            validate_attestation(
                descriptor,
                attestation,
                inventory=inventory,
                clock=FIXED_CLOCK,
                expected_target_fingerprint=EXPECTED_TARGET_FINGERPRINT,
            )


def test_public_nonempty_apis_defer_github_review_authenticity(descriptor: dict):
    chain = _chain(descriptor, 1)
    with _inventory(chain) as (inventory, attestation_commit):
        arguments = {
            "clock": FIXED_CLOCK,
            "expected_target_fingerprint": EXPECTED_TARGET_FINGERPRINT,
            "repo_root": _GIT_CONTEXT["repo"],
            "attestation_commit_sha": attestation_commit,
        }
        assert (
            validate_attestation_inventory_structure(
                descriptor, inventory, **arguments
            )
            is None
        )
        with pytest.raises(
            ManifestError,
            match="ACCEPT_FREE_READINESS/future acceptance gate must verify GitHub review authenticity",
        ):
            derive_effective_state(descriptor, inventory, **arguments)
        with pytest.raises(
            ManifestError,
            match="ACCEPT_FREE_READINESS/future acceptance gate must verify GitHub review authenticity",
        ):
            validate_attestation(
                descriptor,
                chain[-1],
                inventory=inventory,
                **arguments,
            )


def test_local_git_binding_proves_real_objects_tree_review_and_ancestry(
    descriptor: dict,
):
    attestation = _chain(descriptor, 1)[0]
    assert validate_local_git_binding(
        attestation,
        repo_root=_GIT_CONTEXT["repo"],
        attestation_commit_sha=_GIT_CONTEXT["base_commit_sha"],
    )

    fake_tree = _mutated(attestation)
    fake_tree["tree_sha"] = "0" * 40
    with pytest.raises(ManifestError, match="tree"):
        validate_local_git_binding(
            fake_tree,
            repo_root=_GIT_CONTEXT["repo"],
            attestation_commit_sha=_GIT_CONTEXT["base_commit_sha"],
        )

    missing = _mutated(attestation)
    missing["commit_sha"] = "0" * 40
    missing["approval"]["reviewed_commit_sha"] = "0" * 40
    with pytest.raises(ManifestError, match="missing"):
        validate_local_git_binding(
            missing,
            repo_root=_GIT_CONTEXT["repo"],
            attestation_commit_sha=_GIT_CONTEXT["base_commit_sha"],
        )

    with pytest.raises(ManifestError, match="ancestry"):
        validate_local_git_binding(
            attestation,
            repo_root=_GIT_CONTEXT["repo"],
            attestation_commit_sha=_GIT_CONTEXT["unrelated_commit_sha"],
        )

    with pytest.raises(ManifestError, match="missing"):
        validate_local_git_binding(
            attestation,
            repo_root=_GIT_CONTEXT["repo"],
            attestation_commit_sha="f" * 40,
        )


def test_inventory_and_descriptor_are_bound_to_exact_attestation_commit(
    descriptor: dict, tmp_path: Path
):
    chain = _chain(descriptor, 1)
    with _inventory(chain) as (inventory, exact_commit):
        repo = _GIT_CONTEXT["repo"]
        assert validate_inventory_git_content(
            inventory,
            descriptor,
            repo_root=repo,
            attestation_commit_sha=exact_commit,
        )

        descriptor_path = repo / "db/manifests/fase10_promotion_contract.json"
        _run_fixture_git(repo, "reset", "--quiet", "--hard", exact_commit)
        descriptor_path.write_bytes(
            canonical_json_bytes(strict_json_loads(descriptor_path.read_bytes()))
        )
        _run_fixture_git(repo, "add", "--", str(descriptor_path.relative_to(repo)))
        _run_fixture_git(
            repo,
            "-c",
            "user.name=F10 Synthetic",
            "-c",
            "user.email=f10-synthetic@example.invalid",
            "commit",
            "--quiet",
            "-m",
            "reformat-descriptor",
        )
        reformatted_commit = _run_fixture_git(
            repo, "rev-parse", "HEAD"
        ).stdout.strip()
        descriptor_path.write_bytes(DESCRIPTOR_PATH.read_bytes())
        with pytest.raises(ManifestError, match="raw F10 descriptor bytes drift"):
            validate_inventory_git_content(
                inventory,
                descriptor,
                repo_root=repo,
                attestation_commit_sha=reformatted_commit,
            )

        other_repo = tmp_path / "other-repo"
        other_repo.mkdir()
        _run_fixture_git(other_repo, "init", "--quiet")
        with pytest.raises(ManifestError, match="not rooted"):
            validate_inventory_git_content(
                inventory,
                descriptor,
                repo_root=other_repo,
                attestation_commit_sha=exact_commit,
            )

        descendant = repo / "arbitrary-descendant"
        descendant.mkdir()
        with pytest.raises(ManifestError, match="not rooted|root"):
            validate_inventory_git_content(
                inventory,
                descriptor,
                repo_root=descendant,
                attestation_commit_sha=exact_commit,
            )

        inventory_path = repo / "db/attestations/hito1" / inventory.file_names[0]
        _run_fixture_git(repo, "reset", "--quiet", "--hard", exact_commit)
        _run_fixture_git(repo, "rm", "--quiet", "--", str(inventory_path.relative_to(repo)))
        _run_fixture_git(
            repo,
            "-c",
            "user.name=F10 Synthetic",
            "-c",
            "user.email=f10-synthetic@example.invalid",
            "commit",
            "--quiet",
            "-m",
            "missing-inventory",
        )
        missing_commit = _run_fixture_git(repo, "rev-parse", "HEAD").stdout.strip()
        with pytest.raises(ManifestError, match="incomplete or has extras"):
            validate_inventory_git_content(
                inventory,
                descriptor,
                repo_root=repo,
                attestation_commit_sha=missing_commit,
            )

        _run_fixture_git(repo, "reset", "--quiet", "--hard", exact_commit)
        inventory_path.write_bytes(inventory_path.read_bytes() + b"\n")
        _run_fixture_git(repo, "add", "--", str(inventory_path.relative_to(repo)))
        _run_fixture_git(
            repo,
            "-c",
            "user.name=F10 Synthetic",
            "-c",
            "user.email=f10-synthetic@example.invalid",
            "commit",
            "--quiet",
            "-m",
            "drift-inventory",
        )
        drift_commit = _run_fixture_git(repo, "rev-parse", "HEAD").stdout.strip()
        with pytest.raises(ManifestError, match="object drift"):
            validate_inventory_git_content(
                inventory,
                descriptor,
                repo_root=repo,
                attestation_commit_sha=drift_commit,
            )

        _run_fixture_git(repo, "reset", "--quiet", "--hard", exact_commit)
        extra = repo / "db/attestations/hito1" / (
            "ATT-T02_FREE_SCHEMA-20260725T150000Z-eeeeeeeeeeee.json"
        )
        extra.write_bytes(canonical_json_bytes({"synthetic": True}))
        _run_fixture_git(repo, "add", "--", str(extra.relative_to(repo)))
        _run_fixture_git(
            repo,
            "-c",
            "user.name=F10 Synthetic",
            "-c",
            "user.email=f10-synthetic@example.invalid",
            "commit",
            "--quiet",
            "-m",
            "extra-inventory",
        )
        extra_commit = _run_fixture_git(repo, "rev-parse", "HEAD").stdout.strip()
        with pytest.raises(ManifestError, match="incomplete or has extras"):
            validate_inventory_git_content(
                inventory,
                descriptor,
                repo_root=repo,
                attestation_commit_sha=extra_commit,
            )

        _run_fixture_git(repo, "reset", "--quiet", "--hard", exact_commit)
        changed_descriptor = strict_json_loads(descriptor_path.read_bytes())
        changed_descriptor["package_id"] = "synthetic-drift"
        descriptor_path.write_bytes(canonical_json_bytes(changed_descriptor))
        _run_fixture_git(repo, "add", "--", str(descriptor_path.relative_to(repo)))
        _run_fixture_git(
            repo,
            "-c",
            "user.name=F10 Synthetic",
            "-c",
            "user.email=f10-synthetic@example.invalid",
            "commit",
            "--quiet",
            "-m",
            "drift-descriptor",
        )
        descriptor_drift_commit = _run_fixture_git(
            repo, "rev-parse", "HEAD"
        ).stdout.strip()
        descriptor_path.write_bytes(DESCRIPTOR_PATH.read_bytes())
        with pytest.raises(ManifestError, match="descriptor|contract"):
            validate_inventory_git_content(
                inventory,
                descriptor,
                repo_root=repo,
                attestation_commit_sha=descriptor_drift_commit,
            )


def test_local_git_proof_disables_replacement_objects(descriptor: dict):
    attestation = _chain(descriptor, 1)[0]
    repo = _GIT_CONTEXT["repo"]
    _run_fixture_git(
        repo,
        "replace",
        attestation["commit_sha"],
        _GIT_CONTEXT["unrelated_commit_sha"],
    )
    try:
        assert validate_local_git_binding(
            attestation,
            repo_root=repo,
            attestation_commit_sha=_GIT_CONTEXT["base_commit_sha"],
        )
    finally:
        _run_fixture_git(repo, "replace", "-d", attestation["commit_sha"])


def test_local_git_runner_disables_replacements_and_lazy_fetch():
    source = inspect.getsource(migration_manifest._run_local_git)
    content_source = inspect.getsource(validate_inventory_git_content)
    assert '"GIT_NO_REPLACE_OBJECTS": "1"' in source
    assert '"GIT_NO_LAZY_FETCH": "1"' in source
    assert "os.environ" not in source
    assert "shell=False" in source
    assert "timeout=5" in source
    assert '"show"' in content_source
    assert "_git_tree_entries" in content_source


def test_n07_predecessor_null_missing_wrong_and_replay_fail(descriptor: dict):
    chain = _chain(descriptor, 2)
    first_non_null = _mutated(chain)
    first_non_null[0]["previous_attestation_sha256"] = "0" * 64
    wrong = _mutated(chain)
    wrong[1]["previous_attestation_sha256"] = "0" * 64
    missing = _mutated(chain)
    del missing[1]["previous_attestation_sha256"]
    replay = [chain[0], _mutated(chain[0])]
    for invalid in (first_non_null, wrong, missing, replay):
        with pytest.raises(ManifestError):
            _derive(descriptor, invalid)


def test_inventory_rejects_global_sibling_fork_even_if_each_branch_is_valid(
    descriptor: dict,
):
    primary = _chain(descriptor, 2)
    sibling = _mutated(primary[1])
    sibling["attestation_id"] = sibling["attestation_id"][:-12] + "f" * 12
    sibling["approval"]["review_id"] = 2002
    for index, evidence in enumerate(sibling["evidence"], start=1):
        evidence["sha256"] = _digest(900 + index)

    assert _derive(descriptor, primary) == "free_schema_certified"
    assert _derive(descriptor, [primary[0], sibling]) == "free_schema_certified"
    with pytest.raises(ManifestError, match="sibling fork"):
        with _inventory([primary[0], primary[1], sibling]):
            pass


def test_inventory_rejects_unexpected_files_and_symlinks(tmp_path: Path):
    directory = tmp_path / "db/attestations/hito1"
    directory.mkdir(parents=True)
    (directory / "unexpected.txt").write_text("unexpected", encoding="utf-8")
    with pytest.raises(ManifestError, match="unexpected"):
        load_attestation_inventory(root=tmp_path)

    (directory / "unexpected.txt").unlink()
    target = tmp_path / "outside.json"
    target.write_text("{}", encoding="utf-8")
    link = directory / "linked.json"
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("symlinks are unavailable on this platform")
    with pytest.raises(ManifestError, match="non-regular"):
        load_attestation_inventory(root=tmp_path)


@pytest.mark.parametrize("kind", ["unordered", "outside", "negative", "long", "future"])
def test_n08_time_order_intervals_and_creation_clock_fail(
    descriptor: dict, kind: str
):
    chain = _chain(descriptor, 2 if kind == "unordered" else 1)
    if kind == "unordered":
        chain[1]["created_at"] = chain[0]["created_at"]
        chain[1]["attestation_id"] = chain[1]["attestation_id"].replace(
            "20260725T140000Z", "20260725T130000Z"
        )
    elif kind == "outside":
        chain[0]["evidence"][0]["expires_at"] = "2026-07-25T12:59:59Z"
    elif kind == "negative":
        chain[0]["evidence"][0]["expires_at"] = "2026-07-25T12:54:00Z"
    elif kind == "long":
        chain[0]["evidence"][0]["expires_at"] = "2026-07-26T13:00:01Z"
    else:
        with pytest.raises(ManifestError, match="future"):
            _derive(
                descriptor,
                chain,
                clock=datetime(2026, 7, 25, 12, tzinfo=timezone.utc),
            )
        return
    with pytest.raises(ManifestError):
        _derive(descriptor, chain)


def test_n08_historical_replay_ignores_current_expiry(descriptor: dict):
    chain = _chain(descriptor, 4)
    far_future_clock = datetime(2040, 1, 1, tzinfo=timezone.utc)
    assert _derive(descriptor, chain, clock=far_future_clock) == (
        "free_certified"
    )
    with pytest.raises(ManifestError, match="injected UTC clock"):
        validate_attestation(descriptor, chain[0])


def test_n09_derivation_is_pure_and_ignores_no_editable_status(descriptor: dict):
    descriptor_before = canonical_json_bytes(descriptor)
    chain = _chain(descriptor, 4)
    chain_before = canonical_json_bytes(chain)
    assert _derive(descriptor, chain) == "free_certified"
    assert canonical_json_bytes(descriptor) == descriptor_before
    assert canonical_json_bytes(chain) == chain_before
    changed = _mutated(descriptor)
    changed["current_status"] = "free_certified"
    with pytest.raises(ManifestError, match="closed"):
        derive_effective_state(changed, [])


def test_n10_pro_target_and_premature_schema_application_fail(descriptor: dict):
    chain = _chain(descriptor, 1)
    chain[0]["target_environment"] = "pro"
    with pytest.raises(ManifestError):
        _derive(descriptor, chain)
    with pytest.raises(ManifestError, match="blocked"):
        require_schema_apply_allowed(descriptor, "reconciled_not_certified", "free")
    for state in descriptor["state_order"][:-1]:
        with pytest.raises(ManifestError, match="blocked"):
            require_schema_apply_allowed(descriptor, state, "pro")
    require_schema_apply_allowed(descriptor, "free_certified", "pro")


def test_n11_h00_canary_and_snapshots_are_excluded_exactly(descriptor: dict):
    assert descriptor["excluded"] == {
        "H-00": "historical_free_only",
        "canary": "observed_effective_unledgered",
        "historical_snapshots": "superseded",
    }
    for key in descriptor["excluded"]:
        changed = _mutated(descriptor)
        del changed["excluded"][key]
        with pytest.raises(ManifestError):
            validate_promotion_descriptor(changed)


def _clean_cli_environment() -> dict[str, str]:
    provider_name = "SUPA" + "BASE"
    return {
        key: value
        for key, value in {
            "HOME": "/tmp",
            "PATH": os.environ["PATH"],
            "PYTHONPATH": str(ROOT),
        }.items()
        if provider_name not in key.upper()
    }


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/maintenance/db_migrate.py", *args],
        cwd=ROOT,
        env=_clean_cli_environment(),
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def test_n12_local_cli_prints_only_sanitized_aggregate_and_never_connects():
    result = _run_cli(
        "--env",
        "free",
        "--promotion-contract",
        "db/manifests/fase10_promotion_contract.json",
        "--validate-only",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    lines = result.stdout.strip().splitlines()
    assert lines == [
        "PROMOTION_CONTRACT status=PASS state=reconciled_not_certified "
        "attestations=0 schema_apply_free=BLOCKED schema_apply_pro=BLOCKED"
    ]
    forbidden = ["http", ".env", "secret", "project-ref", "api" + "key"]
    assert not any(marker in result.stdout.lower() for marker in forbidden)


@pytest.mark.parametrize(
    "extra",
    [
        (),
        ("--dry-run",),
        ("--manifest", "db/manifests/fase08_candidate.json"),
        ("--only", "synthetic"),
        ("--all",),
    ],
)
def test_n12_promotion_cli_rejects_apply_and_conflicting_modes(extra: tuple[str, ...]):
    args = [
        "--env",
        "free",
        "--promotion-contract",
        "db/manifests/fase10_promotion_contract.json",
    ]
    if extra:
        args.append("--validate-only")
        args.extend(extra)
    result = _run_cli(*args)
    assert result.returncode == 2


@pytest.mark.parametrize(
    "args",
    [
        (
            "--promotion-contract",
            "db/manifests/fase10_promotion_contract.json",
            "--validate-only",
        ),
        (
            "--env",
            "pro",
            "--promotion-contract",
            "db/manifests/fase10_promotion_contract.json",
            "--validate-only",
        ),
        (
            "--env",
            "free",
            "--env",
            "free",
            "--promotion-contract",
            "db/manifests/fase10_promotion_contract.json",
            "--validate-only",
        ),
        (
            "--env",
            "free",
            "--promotion-contract",
            "db/manifests/fase10_promotion_contract.json",
            "--promotion-contract",
            "db/manifests/fase10_promotion_contract.json",
            "--validate-only",
        ),
        (
            "--env",
            "free",
            "--promotion-contract",
            "db/manifests/fase08_candidate.json",
            "--validate-only",
        ),
    ],
)
def test_promotion_cli_requires_one_free_env_and_one_canonical_contract(args):
    result = _run_cli(*args)
    assert result.returncode == 2


def test_n12_only_local_operation_mode_is_executable():
    expected = {
        "local_contract": ("LOCAL_PROMOTION_CONTRACT", False, True),
        "free_readiness": ("REMOTE_READ_FREE", True, False),
        "free_schema_acceptance": ("ACCEPT_FREE_SCHEMA", True, False),
        "free_backfill_acceptance": ("ACCEPT_FREE_BACKFILL", True, False),
        "free_final_certification": ("ACCEPT_FREE_FINAL", True, False),
        "pro_parity": ("PRO_PARITY", True, False),
    }
    assert set(check_db_parity.PROMOTION_OPERATION_MODES) == set(expected)
    for name, properties in expected.items():
        classified = check_db_parity.classify_promotion_operation_mode(name)
        assert (
            classified.capability,
            classified.remote,
            classified.executable_in_f10,
        ) == properties
        if name == "local_contract":
            assert check_db_parity.select_promotion_operation_mode(name) == classified
        else:
            with pytest.raises(RuntimeError, match="blocked"):
                check_db_parity.select_promotion_operation_mode(name)


def test_policy_and_mode_registries_are_deeply_immutable(
    descriptor: dict, monkeypatch: pytest.MonkeyPatch
):
    with pytest.raises(AttributeError):
        ALLOWED_TARGETS.add("other")  # type: ignore[attr-defined]
    with pytest.raises(TypeError):
        MANIFEST_CONTRACTS[(9, "unsafe", "unsafe")] = {}  # type: ignore[index]
    with pytest.raises(TypeError):
        next(iter(MANIFEST_CONTRACTS.values()))["component_order"] = ()  # type: ignore[index]
    with pytest.raises(TypeError):
        F10_STATES["new_state"] = {}  # type: ignore[index]
    with pytest.raises(TypeError):
        F10_STATES["reconciled_not_certified"][
            "schema_apply_blocked_targets"
        ] = ()  # type: ignore[index]
    with pytest.raises(AttributeError):
        F10_TRANSITIONS.append({})  # type: ignore[attr-defined]
    with pytest.raises(TypeError):
        F10_PAYLOAD_ENTRIES[0]["targets"] = ("pro",)  # type: ignore[index]
    with pytest.raises(TypeError):
        F10_EXCLUSIONS["H-00"] = "promotable"  # type: ignore[index]
    with pytest.raises(TypeError):
        check_db_parity.PROMOTION_OPERATION_MODES["unsafe"] = (  # type: ignore[index]
            "unsafe"
        )

    monkeypatch.setattr(migration_manifest, "F10_TRANSITIONS", ())
    monkeypatch.setattr(migration_manifest, "ALLOWED_TARGETS", frozenset({"other"}))
    monkeypatch.setattr(check_db_parity, "PROMOTION_OPERATION_MODES", {})
    assert derive_effective_state(descriptor, []) == "reconciled_not_certified"
    assert schema_apply_is_blocked(descriptor, "reconciled_not_certified", "free")
    assert check_db_parity.select_promotion_operation_mode("local_contract").name == (
        "local_contract"
    )


def test_n12_assigned_runtime_imports_are_lazy_and_offline_safe():
    migrate = (ROOT / "scripts/maintenance/db_migrate.py").read_text(encoding="utf-8")
    parity = (ROOT / "scripts/maintenance/check_db_parity.py").read_text(
        encoding="utf-8"
    )
    migrate_prefix = migrate.split("def load_environment", 1)[0]
    parity_prefix = parity.split("def load_environment", 1)[0]
    assert "from dotenv import" not in migrate_prefix
    assert "from dotenv import" not in parity_prefix
    assert "import requests\n" not in migrate_prefix
    assert "import requests\n" not in parity_prefix
    assert "subprocess" not in migrate
    assert "subprocess" not in parity


def test_n12_production_cli_has_only_zero_attestation_f10_execution():
    migrate = (ROOT / "scripts/maintenance/db_migrate.py").read_text(encoding="utf-8")
    manifest_source = (ROOT / "scripts/maintenance/migration_manifest.py").read_text(
        encoding="utf-8"
    )
    promotion_branch = migrate.split("if promotion_contract_flags:", 1)[1].split(
        "if args.all:", 1
    )[0]

    assert migrate.count("derive_effective_state(descriptor, [])") == 1
    assert "--attestation" not in migrate
    assert "derive_target_fingerprint" not in migrate
    synthetic_name = "derive_synthetic_" + "state_for_tests"
    assert synthetic_name not in migrate
    assert synthetic_name not in manifest_source
    assert not hasattr(migration_manifest, synthetic_name)
    assert "if not args.validate_only:" in promotion_branch
    assert "load_environment" not in promotion_branch
    assert ("get_db_" + "client") not in promotion_branch
    assert "requests." not in promotion_branch
    assert "attestations=0" in promotion_branch

    parity_main = inspect.getsource(check_db_parity.main)
    assert "PROMOTION_OPERATION_MODES" not in parity_main
    assert "select_promotion_operation_mode" not in parity_main
    parity_source = (ROOT / "scripts/maintenance/check_db_parity.py").read_text(
        encoding="utf-8"
    )
    assert synthetic_name not in parity_source


def test_target_fingerprint_api_has_no_generic_or_pro_target_input():
    parameters = inspect.signature(derive_target_fingerprint).parameters
    source = inspect.getsource(derive_target_fingerprint)

    assert list(parameters) == ["canonical_origin", "publishable_key"]
    assert "studiamatch-target-v1\\0free\\0" in source
    assert "os.environ" not in source
    assert "load_dotenv" not in source
    assert "target=" not in source
    assert "environment" not in parameters
    derive_parameters = inspect.signature(derive_effective_state).parameters
    validate_parameters = inspect.signature(validate_attestation).parameters
    assert "git_binding_validator" not in derive_parameters
    assert "git_binding_validator" not in validate_parameters
    for required in (
        "expected_target_fingerprint",
        "repo_root",
        "attestation_commit_sha",
    ):
        assert required in derive_parameters
        assert required in validate_parameters


def test_v1_cycle_is_reproduced_rejected_for_future_but_historical_loader_works():
    historical = strict_json_loads(F8_MANIFEST.read_bytes())
    assert {
        "editorial_backfill_certified",
        "free_postconditions_certified",
    } < set(historical["prerequisites"])
    with pytest.raises(ManifestError, match="circular"):
        reject_v1_circular_prerequisites(historical)
    assert len(load_manifest(F8_MANIFEST, "free")) == 4


def test_source_artifacts_remain_exact_and_descriptor_has_no_attestations():
    descriptor = load_promotion_contract(DESCRIPTOR_PATH)
    assert canonical_json_sha256(strict_json_loads(F8_MANIFEST.read_bytes())) == (
        F10_SOURCE_MANIFEST_SHA256
    )
    assert "attestations" not in descriptor
    attestation_dir = ROOT / "db/attestations/hito1"
    if attestation_dir.exists():
        assert list(attestation_dir.glob("*.json")) == []


def test_fase10_ci_cleanup_does_not_query_a_deleted_chain_target():
    workflow = (ROOT / ".github/workflows/security-audit.yml").read_text(
        encoding="utf-8"
    )
    job = workflow.split("  fase10-promotion-contract:", 1)[1].split(
        "  security-audit:", 1
    )[0]

    assert job.count("iptables -w 10 -C OUTPUT -j FASE10_EGRESS") == 1
    assert job.count("ip6tables -w 10 -C OUTPUT -j FASE10_EGRESS") == 1
    assert "iptables -w 10 -X FASE10_EGRESS" in job
    assert "ip6tables -w 10 -X FASE10_EGRESS" in job
    assert "Unable to verify IPv4 chain absence" in job
    assert "Unable to verify IPv6 chain absence" in job
