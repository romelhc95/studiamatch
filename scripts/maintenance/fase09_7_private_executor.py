"""Local-only planner for the F9.7 private executor successor."""

from __future__ import annotations

import hashlib
import hmac
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ID = "PR-O-F9.7-PRIVATE-EXECUTOR-002"
MANIFEST_PATH = ROOT / "db/manifests/fase09_7_private_executor.json"
RUNBOOK_PATH = ROOT / "db/runbooks/fase09_7_private_executor.json"
BOUNDARY7_SQL_PATH = ROOT / "tests/sql/fase09_7_private_executor_boundary7.sql"

MANIFEST_SHA256 = "115f5b52bf9e975b050fe20668d4b05538eeb9a539eb04d95c0bd83e2d8a1c7a"
RUNBOOK_SHA256 = "8246675f588afc85f360c9b18dac667069615885a104ab41624da35c0e177cda"
BOUNDARY7_SQL_SHA256 = "2c551c592c0969c89b8fa3dab8c2eb864a36b42a403e260acf468fd6edf91b14"
PAYLOAD_SHA256 = "d500177945155aced1a997ab1add947b5c7bd575d9d4dfbaa4b5e2761853f0b5"
SYNTHETIC_FREE_FINGERPRINT_SHA256 = (
    "6a63086f1c20745985f3d76699e36a3d49bf7f16fd45aa6fdc531d33c6651153"
)
V3_MANIFEST_SHA256 = "835b9103f10a8c03b930d4474f9007d99a8715b9bcbc438f144c5bd14d80ea07"

APPLICATION_ROLES = ("PUBLIC", "anon", "authenticated", "authenticator", "service_role")
TERMINAL_RESULTS = ("success", "failure", "timeout", "ambiguous_response")
ATOMIC_SEQUENCE = (
    "pending v3",
    "postcondiciones v3",
    "ledger v3",
    "hold sucesor",
    "verificador terminal",
    "ledger hold",
    "verificacion final",
    "commit unico",
)
DRIFT_GUARDS = frozenset(
    {
        "schema",
        "ledger",
        "acl",
        "rls",
        "grants",
        "policies",
        "owner",
        "routines",
        "triggers",
        "views",
        "rules",
        "publications",
        "extensions",
        "payload",
    }
)

_HEX40 = re.compile(r"\A[0-9a-f]{40}\Z")
_HEX64 = re.compile(r"\A[0-9a-f]{64}\Z")
_STRING_LITERAL = re.compile(r"'(?:''|[^'])*'")
_BOUNDARY7_FORBIDDEN = re.compile(
    r"\b(?:ALTER|CALL|COPY|CREATE|DELETE|DO|DROP|GRANT|INSERT|LOCK|MERGE|"
    r"REASSIGN|RESET|REVOKE|SET|TRUNCATE|UPDATE|VACUUM)\b|"
    r"\bFOR\s+UPDATE\b|\bpg_advisory_(?:lock|xact_lock)\b|"
    r"\b(?:leads|email_log)\b",
    re.IGNORECASE,
)
_EVIDENCE_FORBIDDEN = re.compile(
    r"https?://|\bsb_(?:publishable|secret|p)_|\beyJhbG|"
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|"
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    re.IGNORECASE,
)


class PrivateExecutorError(ValueError):
    pass


@dataclass(frozen=True)
class PrivateExecutorContract:
    manifest: Mapping[str, object]
    runbook: Mapping[str, object]
    boundary7_sql: str
    manifest_sha256: str
    runbook_sha256: str
    boundary7_sql_sha256: str
    payload_sha256: str


@dataclass(frozen=True)
class ApprovalState:
    nonce_digest: str
    not_before: datetime
    expires_at: datetime
    consumed: bool = False
    terminal_result: str | None = None


def _reject_duplicates(pairs: Sequence[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise PrivateExecutorError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicates)


def canonical_json_sha256(value: object) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def canonical_text_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected_payload(manifest: Mapping[str, object]) -> dict[str, object]:
    bindings = _mapping(manifest, "bindings")
    depends_on = _mapping(manifest, "depends_on")
    target_binding = _mapping(manifest, "target_binding")
    return {
        "package_id": PACKAGE_ID,
        "target": manifest.get("target"),
        "v3_manifest_sha256": depends_on.get("manifest_sha256"),
        "synthetic_target_fingerprint_sha256": target_binding.get(
            "synthetic_target_fingerprint_sha256"
        ),
        "atomic_sequence": list(ATOMIC_SEQUENCE),
        "boundary7_sql_sha256": _mapping(bindings, "boundary7_sql").get("sha256"),
        "runbook_sha256": _mapping(bindings, "runbook").get("sha256"),
        "final_expected_state": "private_executor_without_exec_sql",
    }


def _mapping(value: Mapping[str, object], key: str) -> Mapping[str, object]:
    item = value.get(key)
    if not isinstance(item, dict):
        raise PrivateExecutorError(f"{key} block is required")
    return item


def _assert_sha(value: object, label: str) -> str:
    if not isinstance(value, str) or not _HEX64.fullmatch(value):
        raise PrivateExecutorError(f"{label} must be a sha256 hex digest")
    return value


def _assert_path_under_root(root: Path, relative_path: object) -> Path:
    if not isinstance(relative_path, str) or relative_path.startswith(("/", "..")):
        raise PrivateExecutorError("artifact path must be repository-relative")
    path = (root / relative_path).resolve()
    if root.resolve() not in path.parents:
        raise PrivateExecutorError("artifact path escapes repository root")
    return path


def validate_boundary7_sql(sql: str) -> None:
    without_literals = _STRING_LITERAL.sub("''", sql)
    if sql.count(";") != 1 or not sql.rstrip().endswith(";"):
        raise PrivateExecutorError("boundary 7 SQL must be a single statement")
    if _BOUNDARY7_FORBIDDEN.search(without_literals):
        raise PrivateExecutorError("boundary 7 SQL is not strictly read-only")
    if "SELECT" not in without_literals.upper():
        raise PrivateExecutorError("boundary 7 SQL must express a read-only verifier")


def validate_private_surface(manifest: Mapping[str, object]) -> None:
    executor = _mapping(manifest, "executor")
    if executor.get("schema") == "public":
        raise PrivateExecutorError("executor must not live in public")
    for key in (
        "schema_exposed_by_data_api",
        "postgrest_rpc_endpoint",
        "accepts_arbitrary_sql",
        "accepts_text_sql",
    ):
        if executor.get(key) is not False:
            raise PrivateExecutorError(f"executor surface must keep {key}=false")
    if executor.get("descriptor_only") is not True:
        raise PrivateExecutorError("executor must be descriptor-only")
    if executor.get("final_state_excludes") != ["public.exec_sql(text)"]:
        raise PrivateExecutorError("final state must exclude public.exec_sql(text)")
    grants = _mapping(executor, "execute_grants")
    for role in APPLICATION_ROLES:
        if grants.get(role) is not False:
            raise PrivateExecutorError(f"executor grant must deny {role}")


def load_contract(root: Path = ROOT) -> PrivateExecutorContract:
    manifest_path = root / "db/manifests/fase09_7_private_executor.json"
    runbook_path = root / "db/runbooks/fase09_7_private_executor.json"
    boundary_path = root / "tests/sql/fase09_7_private_executor_boundary7.sql"

    manifest = _load_json(manifest_path)
    runbook = _load_json(runbook_path)
    boundary_sql = boundary_path.read_text(encoding="utf-8")
    manifest_sha256 = canonical_text_sha256(manifest_path)
    runbook_sha256 = canonical_text_sha256(runbook_path)
    boundary_sql_sha256 = canonical_text_sha256(boundary_path)
    bindings = _mapping(manifest, "bindings")

    if MANIFEST_SHA256 != "TO_BE_FILLED" and not hmac.compare_digest(
        manifest_sha256, MANIFEST_SHA256
    ):
        raise PrivateExecutorError("private executor manifest digest drift")
    if RUNBOOK_SHA256 != "TO_BE_FILLED" and not hmac.compare_digest(
        runbook_sha256, RUNBOOK_SHA256
    ):
        raise PrivateExecutorError("private executor runbook digest drift")
    if BOUNDARY7_SQL_SHA256 != "TO_BE_FILLED" and not hmac.compare_digest(
        boundary_sql_sha256, BOUNDARY7_SQL_SHA256
    ):
        raise PrivateExecutorError("private executor boundary SQL digest drift")

    if manifest.get("package_id") != PACKAGE_ID or runbook.get("package_id") != PACKAGE_ID:
        raise PrivateExecutorError("private executor package id drift")
    if manifest.get("status") != "GO_WP_LOCAL" or runbook.get("status") != "GO_WP_LOCAL":
        raise PrivateExecutorError("private executor status drift")
    if manifest.get("application_authorized") is not False:
        raise PrivateExecutorError("private executor application must remain unauthorized")
    if manifest.get("capabilities") != [] or runbook.get("capabilities") != []:
        raise PrivateExecutorError("private executor capabilities must be empty")
    if manifest.get("target") != "free":
        raise PrivateExecutorError("private executor target must be Free")
    if manifest.get("blocked_targets") != ["pro", "production", "certification"]:
        raise PrivateExecutorError("private executor blocked targets drift")

    depends_on = _mapping(manifest, "depends_on")
    if depends_on.get("manifest_sha256") != V3_MANIFEST_SHA256:
        raise PrivateExecutorError("private executor v3 manifest digest drift")
    v3_manifest_path = _assert_path_under_root(root, depends_on.get("manifest"))
    if not hmac.compare_digest(canonical_text_sha256(v3_manifest_path), V3_MANIFEST_SHA256):
        raise PrivateExecutorError("private executor v3 manifest file digest drift")
    if len(depends_on.get("entries", [])) != 6:
        raise PrivateExecutorError("private executor requires exact six-entry v3 prefix")
    for entry in depends_on.get("entries", []):
        if not isinstance(entry, dict):
            raise PrivateExecutorError("v3 entry must be an object")
        path = _assert_path_under_root(root, entry.get("path"))
        expected_sha = _assert_sha(entry.get("sha256"), "v3 entry")
        if not hmac.compare_digest(canonical_text_sha256(path), expected_sha):
            raise PrivateExecutorError("v3 entry digest drift")

    runbook_binding = _mapping(bindings, "runbook")
    runbook_binding_path = _assert_path_under_root(root, runbook_binding.get("path"))
    if runbook_binding_path != runbook_path.resolve():
        raise PrivateExecutorError("private executor runbook path drift")
    if not hmac.compare_digest(runbook_sha256, _assert_sha(runbook_binding.get("sha256"), "runbook")):
        raise PrivateExecutorError("private executor runbook binding drift")

    sql_binding = _mapping(bindings, "boundary7_sql")
    sql_binding_path = _assert_path_under_root(root, sql_binding.get("path"))
    if sql_binding_path != boundary_path.resolve():
        raise PrivateExecutorError("private executor SQL path drift")
    if not hmac.compare_digest(boundary_sql_sha256, _assert_sha(sql_binding.get("sha256"), "boundary7 SQL")):
        raise PrivateExecutorError("private executor SQL binding drift")

    validate_private_surface(manifest)
    validate_boundary7_sql(boundary_sql)
    validate_target_binding(manifest, "free", SYNTHETIC_FREE_FINGERPRINT_SHA256)

    payload_sha256 = canonical_json_sha256(expected_payload(manifest))
    payload_binding = _mapping(bindings, "payload")
    if not hmac.compare_digest(payload_sha256, _assert_sha(payload_binding.get("sha256"), "payload")):
        raise PrivateExecutorError("private executor payload binding drift")
    if PAYLOAD_SHA256 != "TO_BE_FILLED" and not hmac.compare_digest(
        payload_sha256, PAYLOAD_SHA256
    ):
        raise PrivateExecutorError("private executor payload digest drift")

    return PrivateExecutorContract(
        manifest=manifest,
        runbook=runbook,
        boundary7_sql=boundary_sql,
        manifest_sha256=manifest_sha256,
        runbook_sha256=runbook_sha256,
        boundary7_sql_sha256=boundary_sql_sha256,
        payload_sha256=payload_sha256,
    )


def validate_target_binding(
    manifest: Mapping[str, object],
    target: str,
    target_fingerprint_sha256: str,
) -> None:
    target_binding = _mapping(manifest, "target_binding")
    if target != target_binding.get("required_target"):
        raise PrivateExecutorError("private executor target binding rejected")
    expected = _assert_sha(
        target_binding.get("synthetic_target_fingerprint_sha256"),
        "target fingerprint",
    )
    if not hmac.compare_digest(target_fingerprint_sha256, expected):
        raise PrivateExecutorError("private executor target fingerprint mismatch")


def build_descriptor(
    contract: PrivateExecutorContract,
    *,
    candidate_commit: str,
    candidate_tree: str,
    payload: Mapping[str, object] | None = None,
) -> dict[str, object]:
    if not _HEX40.fullmatch(candidate_commit) or not _HEX40.fullmatch(candidate_tree):
        raise PrivateExecutorError("candidate commit and tree must be 40 hex characters")
    payload = payload or expected_payload(contract.manifest)
    return {
        "package_id": PACKAGE_ID,
        "candidate_commit": candidate_commit,
        "candidate_tree": candidate_tree,
        "manifest_sha256": contract.manifest_sha256,
        "runbook_sha256": contract.runbook_sha256,
        "boundary7_sql_sha256": contract.boundary7_sql_sha256,
        "payload_sha256": canonical_json_sha256(payload),
        "target": "free",
        "target_fingerprint_sha256": SYNTHETIC_FREE_FINGERPRINT_SHA256,
    }


def validate_descriptor(
    contract: PrivateExecutorContract,
    descriptor: Mapping[str, object],
    *,
    expected_candidate_commit: str,
    expected_candidate_tree: str,
    expected_payload_value: Mapping[str, object] | None = None,
) -> None:
    expected_payload_value = expected_payload_value or expected_payload(contract.manifest)
    expected = build_descriptor(
        contract,
        candidate_commit=expected_candidate_commit,
        candidate_tree=expected_candidate_tree,
        payload=expected_payload_value,
    )
    if set(descriptor) != set(expected):
        raise PrivateExecutorError("private executor descriptor has unexpected keys")
    for key, value in expected.items():
        actual = descriptor.get(key)
        if isinstance(value, str):
            if not isinstance(actual, str) or not hmac.compare_digest(actual, value):
                raise PrivateExecutorError(f"private executor descriptor {key} mismatch")
        elif actual != value:
            raise PrivateExecutorError(f"private executor descriptor {key} mismatch")


def validate_no_drift(snapshot: Mapping[str, object]) -> None:
    missing = DRIFT_GUARDS.difference(snapshot)
    if missing:
        raise PrivateExecutorError("private executor drift snapshot incomplete")
    dirty = sorted(key for key in DRIFT_GUARDS if snapshot.get(key) not in (False, 0, "clean"))
    if dirty:
        raise PrivateExecutorError("private executor drift detected: " + ", ".join(dirty))


def reject_arbitrary_sql(contract: PrivateExecutorContract, sql_text: str) -> None:
    candidate_sha = hashlib.sha256(sql_text.encode("utf-8")).hexdigest()
    if not hmac.compare_digest(candidate_sha, contract.boundary7_sql_sha256):
        raise PrivateExecutorError("private executor rejects arbitrary SQL")
    validate_boundary7_sql(sql_text)


def create_approval(
    *,
    nonce: str,
    not_before: datetime,
    expires_at: datetime,
    now: datetime,
) -> ApprovalState:
    if not nonce:
        raise PrivateExecutorError("private executor nonce is required")
    if not_before.tzinfo is None or expires_at.tzinfo is None or now.tzinfo is None:
        raise PrivateExecutorError("private executor approval times must be timezone-aware")
    if expires_at <= not_before:
        raise PrivateExecutorError("private executor approval window is invalid")
    if now < not_before or now >= expires_at:
        raise PrivateExecutorError("private executor approval window closed")
    return ApprovalState(
        nonce_digest=hashlib.sha256(nonce.encode("utf-8")).hexdigest(),
        not_before=not_before.astimezone(timezone.utc),
        expires_at=expires_at.astimezone(timezone.utc),
    )


def consume_approval(state: ApprovalState, terminal_result: str) -> ApprovalState:
    if state.consumed:
        raise PrivateExecutorError("private executor approval already consumed")
    if terminal_result not in TERMINAL_RESULTS:
        raise PrivateExecutorError("private executor response is ambiguous")
    return ApprovalState(
        nonce_digest=state.nonce_digest,
        not_before=state.not_before,
        expires_at=state.expires_at,
        consumed=True,
        terminal_result=terminal_result,
    )


def public_evidence(contract: PrivateExecutorContract, *, verdict: str, timestamp: str) -> dict[str, object]:
    evidence = {
        "aggregate_state": contract.manifest.get("status"),
        "timestamp": timestamp,
        "artifact_digest": {
            "manifest": contract.manifest_sha256,
            "runbook": contract.runbook_sha256,
            "boundary7_sql": contract.boundary7_sql_sha256,
            "payload": contract.payload_sha256,
        },
        "verdict": verdict,
    }
    assert_public_evidence_sanitized(evidence)
    return evidence


def assert_public_evidence_sanitized(evidence: Mapping[str, object]) -> None:
    if set(evidence) != {"aggregate_state", "timestamp", "artifact_digest", "verdict"}:
        raise PrivateExecutorError("private executor evidence has non-public keys")
    serialized = json.dumps(evidence, sort_keys=True, separators=(",", ":"))
    if _EVIDENCE_FORBIDDEN.search(serialized):
        raise PrivateExecutorError("private executor evidence is not sanitized")
