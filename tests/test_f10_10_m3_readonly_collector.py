from __future__ import annotations

import ast
import hashlib
import importlib
import json
import os
import stat
import sys
import uuid
from copy import deepcopy
from pathlib import Path

import pytest

from scripts.maintenance import f10_10_m3_readonly_collector as m3


VALID_UNTIL = "2099-12-31T23:59:59Z"
VALID_UNTIL_EPOCH = 4_102_444_799
PROVISIONER = "m3_provisioner"


def uid(number: int) -> uuid.UUID:
    return uuid.UUID(int=number)


def rows(count: int, *, missing: bool = False) -> list[tuple[object, ...]]:
    return [
        (uid(index + 1), True, None if missing and index == 0 else "Syllabus", "Objectives")
        for index in range(count)
    ]


def valid_q0() -> tuple[object, ...]:
    return (
        "m3_reader", "m3_reader", "postgres", "on", "on", "pg_catalog", "UTF8",
        False, True, False, False, True, False, False, 1,
        VALID_UNTIL_EPOCH, True, False, 1, PROVISIONER, True, False, False,
        False, False, False,
        True, True, True, True, False,
        False, False, False, False, False, False, False, False,
    )


SCHEMA = [
    ("id", "uuid", True, None),
    ("is_active", "boolean", False, "true"),
    ("syllabus", "text", False, None),
    ("objectives", "text", False, None),
]
CONSTRAINTS = [("courses_pkey", "p", "PRIMARY KEY (id)", 1, "id")]


class FakeInfo:
    ssl_in_use = True
    server_version = 170004
    host = "db.abc-project.supabase.co"
    port = 5432
    dbname = "postgres"
    user = "m3_reader"

    def ssl_attribute(self, name: str) -> str | None:
        return {
            "protocol": "TLSv1.3",
            "cipher": "TLS_AES_256_GCM_SHA384",
            "library": "OpenSSL",
        }.get(name)


class FakeCursor:
    def __init__(self, connection: "FakeConnection", name: str | None = None) -> None:
        self.connection = connection
        self.name = name
        self.result: list[tuple[object, ...]] = []
        self.fetch_offset = 0
        self.transaction = 0
        self.page_offset = 0
        self.itersize: int | None = None
        self.closed = False

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()
        return None

    def execute(self, sql: str, params: tuple[object, ...] | None = None) -> None:
        self.connection.transcript.append((sql, params))
        self.connection.cursor_transcript.append((sql, self.name))
        self.fetch_offset = 0
        if sql == m3.BEGIN_SQL:
            self.transaction += 1
            self.page_offset = 0
            self.result = []
        elif sql == m3.Q0_SQL:
            self.result = [self.connection.q0]
        elif sql == m3.Q1_SQL:
            self.result = self.connection.schema
        elif sql == m3.Q2_SQL:
            self.result = self.connection.constraints
        elif sql == m3.Q3_SQL:
            self.result = self.connection.triggers
        elif sql in {
            m3.Q3_ROUTINES_SQL, m3.Q3_EXTENSIONS_SQL, m3.Q3_AGGREGATES_SQL,
            m3.Q3_EXTENSION_MEMBERS_SQL,
        }:
            self.result = []
        elif sql in {m3.Q4_FIRST_SQL, m3.Q4_NEXT_SQL}:
            snapshot = self.connection.snapshots[self.transaction - 2]
            start = self.page_offset
            self.result = snapshot[start : start + m3.PAGE_SIZE]
            self.page_offset += len(self.result)
        elif sql == m3.COMMIT_SQL:
            self.result = []
        else:  # pragma: no cover - the collector should reject before this point
            raise AssertionError("unexpected SQL")

    def fetchall(self) -> list[tuple[object, ...]]:
        return self.result

    def fetchmany(self, size: int) -> list[tuple[object, ...]]:
        start = self.fetch_offset
        batch = self.result[start : start + size]
        self.fetch_offset += len(batch)
        return batch

    def close(self) -> None:
        self.closed = True


class FakeConnection:
    def __init__(
        self,
        snapshot_rows: list[tuple[object, ...]] | None = None,
        *,
        second_rows: list[tuple[object, ...]] | None = None,
    ) -> None:
        first = rows(2, missing=True) if snapshot_rows is None else snapshot_rows
        self.snapshots = [first, deepcopy(first) if second_rows is None else second_rows]
        self.q0 = valid_q0()
        self.schema = deepcopy(SCHEMA)
        self.constraints = deepcopy(CONSTRAINTS)
        self.triggers: list[tuple[object, ...]] = []
        self.transcript: list[tuple[str, tuple[object, ...] | None]] = []
        self.cursor_transcript: list[tuple[str, str | None]] = []
        self.info = FakeInfo()
        self.closed = False
        self.rolled_back = False
        self.named_cursors: list[FakeCursor] = []

    def cursor(self, name: str | None = None) -> FakeCursor:
        cursor = FakeCursor(self, name)
        if name is not None:
            self.named_cursors.append(cursor)
        return cursor

    def rollback(self) -> None:
        self.rolled_back = True

    def close(self) -> None:
        self.closed = True


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    for relative in m3.QUERY_SET_FILES:
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        source = Path(__file__).parents[1] / relative
        destination.write_bytes(source.read_bytes())
    return tmp_path


@pytest.fixture
def config(tmp_path: Path) -> m3.Config:
    ca = tmp_path / "approved-ca.pem"
    ca.write_bytes(b"approved test ca\n")
    return m3.Config(
        target_alias="FREE_DB",
        approval_id="M3-APPROVAL-000001",
        api_url="https://abc-project.supabase.co",
        project_ref="abc-project",
        sql_host="db.abc-project.supabase.co",
        sql_port=5432,
        database="postgres",
        user="m3_reader",
        password="hostile-password-value",
        ca_file=ca,
        ca_sha256="sha256:" + hashlib.sha256(ca.read_bytes()).hexdigest(),
        valid_until_epoch=VALID_UNTIL_EPOCH,
        provisioner=PROVISIONER,
    )


def env_for(config: m3.Config) -> dict[str, str]:
    return {
        "F10_10_M3_API_URL": config.api_url,
        "F10_10_M3_PROJECT_REF": config.project_ref,
        "F10_10_M3_SQL_HOST": config.sql_host,
        "F10_10_M3_SQL_PORT": str(config.sql_port),
        "F10_10_M3_DATABASE": config.database,
        "F10_10_M3_USER": config.user,
        "F10_10_M3_PASSWORD": config.password,
        "F10_10_M3_CA_FILE": str(config.ca_file),
        "F10_10_M3_CA_SHA256": config.ca_sha256,
        "F10_10_M3_VALID_UNTIL": VALID_UNTIL,
        "F10_10_M3_PROVISIONER": PROVISIONER,
    }


def collect_fake(
    config: m3.Config, workspace: Path, connection: FakeConnection,
) -> m3.CollectionResult:
    with m3.open_pinned_ca(config) as pinned_ca:
        return m3.collect(
            config, lambda _config, _ca: connection,
            m3.query_set_digest(workspace), "sha256:" + "1" * 64, pinned_ca,
        )


def configured_binding(config: m3.Config) -> str:
    with m3.open_pinned_ca(config) as pinned_ca:
        return m3.target_binding(config, pinned_ca.digest)[1]


def test_exact_transcript_has_three_q0_first_read_only_transactions(
    workspace: Path, config: m3.Config,
) -> None:
    connection = FakeConnection()
    result = collect_fake(config, workspace, connection)

    assert result.manifest["decision"] == "PASS"
    assert result.manifest["schema"] == "f10.10-m3-sanitized-manifest-v2"
    assert result.manifest["collector_version"].endswith("collector-v2")
    assert result.manifest["canonical_version"].endswith("canonical-v2")
    assert result.manifest["target_binding_version"] == m3.TARGET_BINDING_VERSION
    assert result.manifest["summary"]["incomplete_active_courses"] == 1
    expected = [
        (m3.BEGIN_SQL, None), (m3.Q0_SQL, None),
        *[(sql, None) for _, sql in m3.CATALOG_QUERIES],
        (m3.COMMIT_SQL, None),
        (m3.BEGIN_SQL, None), (m3.Q0_SQL, None), (m3.Q4_FIRST_SQL, None),
        (m3.COMMIT_SQL, None),
        (m3.BEGIN_SQL, None), (m3.Q0_SQL, None), (m3.Q4_FIRST_SQL, None),
        (m3.COMMIT_SQL, None),
    ]
    assert connection.transcript == expected
    begins = [index for index, item in enumerate(connection.transcript) if item[0] == m3.BEGIN_SQL]
    assert len(begins) == 3
    assert all(connection.transcript[index + 1] == (m3.Q0_SQL, None) for index in begins)
    assert sum(sql == m3.COMMIT_SQL for sql, _ in connection.transcript) == 3
    assert connection.closed is True
    assert all(sql in m3.STATIC_SQL for sql, _ in connection.transcript)
    assert [cursor.name for cursor in connection.named_cursors] == [
        f"f10_10_m3_{name}" for name, _ in m3.CATALOG_QUERIES
    ]
    assert all(
        cursor.closed and cursor.itersize == m3.CATALOG_FETCH_SIZE
        for cursor in connection.named_cursors
    )
    catalog_sql = {sql for _, sql in m3.CATALOG_QUERIES}
    assert all(
        name is not None if sql in catalog_sql else name is None
        for sql, name in connection.cursor_transcript
    )


@pytest.mark.parametrize(
    ("mutate", "reason"),
    [
        (lambda connection: connection.schema.__setitem__(0, ("id", "text", True, None)), "STOP_SCHEMA_DRIFT"),
        (lambda connection: connection.schema.__setitem__(1, ("is_active", "boolean", True, "true")), "STOP_SCHEMA_DRIFT"),
        (lambda connection: connection.schema.__setitem__(2, ("syllabus", "text", True, None)), "STOP_SCHEMA_DRIFT"),
        (lambda connection: connection.constraints.__setitem__(0, ("pk", "p", "PRIMARY KEY", 1, "is_active")), "STOP_UNSTABLE_KEYSET"),
        (lambda connection: setattr(connection, "constraints", []), "STOP_UNSTABLE_KEYSET"),
        (lambda connection: setattr(connection, "q0", valid_q0()[:25] + (True,) + valid_q0()[26:]), "STOP_NEEDS_READONLY_CHANNEL"),
    ],
)
def test_schema_pk_and_q0_fail_closed(workspace: Path, config: m3.Config, mutate, reason: str) -> None:
    connection = FakeConnection()
    mutate(connection)
    with pytest.raises(m3.CollectorError) as caught:
        collect_fake(config, workspace, connection)
    assert caught.value.reason_code == reason
    assert connection.rolled_back is True


@pytest.mark.parametrize(
    ("index", "value"),
    [
        (3, "off"), (4, "off"), (5, "public"), (6, "LATIN1"),
        (7, True), (8, False), (10, True), (11, False), (12, True), (13, True),
        (14, -1), (14, True), (15, VALID_UNTIL_EPOCH + 1), (15, True),
        (16, False), (17, True), (18, 0), (18, 2), (18, True),
        (19, "other_provisioner"), (19, None), (20, False), (21, True),
        (22, True), (25, True), (26, False), (27, False), (28, False),
        (29, False), (30, True), (31, True), (32, True), (33, True),
        (34, True), (35, True), (36, True), (37, True), (38, True),
    ],
)
def test_major_q0_contract_failures_stop(
    workspace: Path, config: m3.Config, index: int, value: object,
) -> None:
    connection = FakeConnection()
    changed = list(connection.q0)
    changed[index] = value
    connection.q0 = tuple(changed)
    with pytest.raises(m3.CollectorError, match="STOP_NEEDS_READONLY_CHANNEL"):
        collect_fake(config, workspace, connection)


@pytest.mark.parametrize(
    ("count", "expected_pages", "reason"),
    [(0, 1, None), (499, 1, None), (500, 2, None), (10_000, 21, None), (10_001, None, "STOP_POPULATION_LIMIT")],
)
def test_keyset_boundaries(
    workspace: Path, config: m3.Config, count: int, expected_pages: int | None, reason: str | None,
) -> None:
    connection = FakeConnection(rows(count))
    if reason:
        with pytest.raises(m3.CollectorError) as caught:
            collect_fake(config, workspace, connection)
        assert caught.value.reason_code == reason
    else:
        result = collect_fake(config, workspace, connection)
        assert result.manifest["summary"]["total_count"] == count
        assert result.manifest["summary"]["page_count"] == expected_pages


def test_q4_uses_parameter_placeholder_and_private_uuid(workspace: Path, config: m3.Config) -> None:
    connection = FakeConnection(rows(501))
    collect_fake(config, workspace, connection)
    calls = [(sql, params) for sql, params in connection.transcript if sql == m3.Q4_NEXT_SQL]
    assert "%s" in m3.Q4_NEXT_SQL and ":last_private_id" not in m3.Q4_NEXT_SQL
    assert calls[0][1] == (str(uid(500)),)


def test_duplicate_order_and_snapshot_drift_stop(workspace: Path, config: m3.Config) -> None:
    duplicate = rows(2)
    duplicate[1] = duplicate[0]
    with pytest.raises(m3.CollectorError, match="STOP_UNSTABLE_KEYSET"):
        collect_fake(config, workspace, FakeConnection(duplicate))

    reversed_rows = list(reversed(rows(2)))
    with pytest.raises(m3.CollectorError, match="STOP_UNSTABLE_KEYSET"):
        collect_fake(config, workspace, FakeConnection(reversed_rows))

    changed = rows(2)
    changed[0] = (changed[0][0], True, "changed", "Objectives")
    with pytest.raises(m3.CollectorError, match="STOP_SNAPSHOT_DRIFT"):
        collect_fake(config, workspace, FakeConnection(rows(2), second_rows=changed))


def test_q0_drift_between_transactions_stops(workspace: Path, config: m3.Config) -> None:
    connection = FakeConnection()

    class DriftingCursor(FakeCursor):
        def execute(self, sql: str, params: tuple[object, ...] | None = None) -> None:
            super().execute(sql, params)
            if sql == m3.Q0_SQL and self.transaction == 3:
                changed = list(self.connection.q0)
                changed[24] = True
                self.result = [tuple(changed)]

    def cursor_factory(name: str | None = None) -> FakeCursor:
        if name is None:
            return DriftingCursor(connection)
        cursor = FakeCursor(connection, name)
        connection.named_cursors.append(cursor)
        return cursor

    connection.cursor = cursor_factory  # type: ignore[method-assign]
    with pytest.raises(m3.CollectorError, match="STOP_CHANNEL_DRIFT"):
        collect_fake(config, workspace, connection)


def test_canonical_golden_vectors_and_uuid_contract() -> None:
    assert m3.canonical_json({"z": m3.tagged(None), "a": m3.tagged(7)}) == (
        b'{"a":["integer","7"],"z":["null"]}'
    )
    payload = [[m3.typed_uuid("00000000-0000-0000-0000-000000000001")]]
    assert m3.envelope_digest("total-ids-v1", payload) == (
        "sha256:4fa18cd8fc3fb1ccbd85fdb960e945595f2ef3d98b9e114ddcecec36ea552019"
    )
    assert m3.normalized_tag("\u200b POR\u00a0DEFINIR ") == ["null"]
    with pytest.raises(m3.CollectorError, match="STOP_SCHEMA_DRIFT"):
        m3.typed_uuid("00000000-0000-0000-0000-000000000001 ")


def test_collector_id_digest_uses_nested_typed_ids(workspace: Path, config: m3.Config) -> None:
    result = collect_fake(config, workspace, FakeConnection(rows(1)))
    expected = m3.envelope_digest("total-ids-v1", [[m3.typed_uuid(uid(1))]])
    assert result.manifest["summary"]["total_ids_digest"] == expected
    assert result.manifest["summary"]["active_ids_digest"] == m3.envelope_digest(
        "active-ids-v1", [[m3.typed_uuid(uid(1))]],
    )


def test_config_and_target_binding_v2_are_pre_transport(
    workspace: Path, config: m3.Config,
) -> None:
    loaded = m3.load_config(env_for(config), "FREE_DB", "M3-APPROVAL-000001")
    assert loaded.valid_until_epoch == VALID_UNTIL_EPOCH
    assert loaded.provisioner == PROVISIONER
    assert not hasattr(loaded, "server_version_num")
    assert not hasattr(loaded, "tls_protocol")
    assert not hasattr(loaded, "tls_cipher")
    assert not hasattr(loaded, "tls_library")
    source = Path(m3.__file__).read_text(encoding="utf-8")
    for removed_name in (
        "F10_10_M3_SERVER_VERSION_NUM", "F10_10_M3_TLS_PROTOCOL",
        "F10_10_M3_TLS_CIPHER", "F10_10_M3_TLS_LIBRARY",
    ):
        assert removed_name not in source

    bad_port = env_for(config) | {"F10_10_M3_SQL_PORT": "6543"}
    with pytest.raises(m3.CollectorError, match="STOP_CONFIG_INVALID"):
        m3.load_config(bad_port, "FREE_DB", "M3-APPROVAL-000001")

    bad_api = env_for(config) | {"F10_10_M3_API_URL": "https://other.supabase.co"}
    with pytest.raises(m3.CollectorError, match="STOP_TARGET_MISMATCH"):
        m3.load_config(bad_api, "FREE_DB", "M3-APPROVAL-000001")

    pooler = env_for(config) | {"F10_10_M3_SQL_HOST": "aws-0-us-east-1.pooler.supabase.com"}
    with pytest.raises(m3.CollectorError, match="STOP_TARGET_MISMATCH"):
        m3.load_config(pooler, "FREE_DB", "M3-APPROVAL-000001")

    wrong_pin = deepcopy(config)
    object.__setattr__(wrong_pin, "ca_sha256", "sha256:" + "0" * 64)
    with pytest.raises(m3.CollectorError, match="STOP_TLS_CONTRACT"):
        collect_fake(wrong_pin, workspace, FakeConnection())

    with m3.open_pinned_ca(config) as pinned:
        binding, digest = m3.target_binding(config, pinned.digest)
    serialized = json.dumps(binding)
    assert binding["schema"] == m3.TARGET_BINDING_VERSION
    assert binding["alias"] == config.target_alias
    assert binding["api"][0] == m3.HOST_NORMALIZATION_VERSION
    assert all(value.startswith("sha256:") for value in binding["api"][1:])
    assert binding["sql"][0] == m3.SQL_HOST_NORMALIZATION_VERSION
    assert binding["sql"][2] == 5432
    assert all(
        binding["sql"][index].startswith("sha256:") for index in (1, 3, 4, 5)
    )
    assert binding["sql"][6] == VALID_UNTIL_EPOCH
    assert binding["sql"][-2:] == ["verify-full", config.ca_sha256]
    assert config.user not in serialized
    assert config.provisioner not in serialized
    assert config.password not in serialized
    assert "TLSv1" not in serialized and "OpenSSL" not in serialized
    assert digest.startswith("sha256:")
    other_user = deepcopy(config)
    object.__setattr__(other_user, "user", "different_reader")
    with m3.open_pinned_ca(other_user) as pinned:
        assert m3.target_binding(other_user, pinned.digest)[1] != digest
    other_provisioner = deepcopy(config)
    object.__setattr__(other_provisioner, "provisioner", "other_provisioner")
    with m3.open_pinned_ca(other_provisioner) as pinned:
        assert m3.target_binding(other_provisioner, pinned.digest)[1] != digest


def test_v2_rebaseline_rejects_pro_deterministically_without_connection(
    workspace: Path, config: m3.Config,
) -> None:
    with pytest.raises(m3.CollectorError, match="STOP_CONFIG_INVALID"):
        m3.load_config(env_for(config), "PRO_DB", config.approval_id)

    called = False

    def factory(*_args):
        nonlocal called
        called = True
        raise AssertionError("PRO must stop before connection")

    code, manifest = m3.run_cli(
        [
            "--mode", "target-binding-digest", "--target-alias", "PRO_DB",
            "--approval-id", config.approval_id,
        ],
        env=env_for(config), workspace=workspace, connection_factory=factory,
    )
    assert code == 2
    assert manifest["reason_codes"] == ["STOP_CONFIG_INVALID"]
    assert called is False


@pytest.mark.parametrize(
    "value",
    [
        "", "2099-12-31T23:59:59+00:00", "2099-12-31t23:59:59Z",
        "2099-12-31T23:59:59.000Z", "2099-02-29T00:00:00Z",
        "1969-12-31T23:59:59Z", "9999-12-31T23:59:60Z",
        " 2099-12-31T23:59:59Z", "2099-12-31T23:59:59Z\n",
    ],
)
def test_valid_until_rejects_missing_malformed_noncanonical_and_out_of_range(
    config: m3.Config, value: str,
) -> None:
    env = env_for(config)
    if value == "":
        del env["F10_10_M3_VALID_UNTIL"]
    else:
        env["F10_10_M3_VALID_UNTIL"] = value
    with pytest.raises(m3.CollectorError, match="STOP_CONFIG_INVALID"):
        m3.load_config(env, "FREE_DB", "M3-APPROVAL-000001")


@pytest.mark.parametrize(
    "value",
    [
        "", "Provisioner", "1provisioner", "provisioner-role",
        "provisioner.role", '"provisioner"', "provisioner role",
        "a" * 64, "provisión",
    ],
)
def test_provisioner_rejects_missing_or_unsafe_postgresql_names(
    config: m3.Config, value: str,
) -> None:
    env = env_for(config)
    if value == "":
        del env["F10_10_M3_PROVISIONER"]
    else:
        env["F10_10_M3_PROVISIONER"] = value
    with pytest.raises(m3.CollectorError, match="STOP_CONFIG_INVALID"):
        m3.load_config(env, "FREE_DB", "M3-APPROVAL-000001")


def test_past_canonical_valid_until_is_allowed_for_offline_binding_only(
    workspace: Path, config: m3.Config,
) -> None:
    env = env_for(config) | {"F10_10_M3_VALID_UNTIL": "1970-01-01T00:00:00Z"}
    called = False

    def factory(*_args):
        nonlocal called
        called = True
        raise AssertionError("offline mode must not connect")

    code, binding = m3.run_cli(
        [
            "--mode", "target-binding-digest", "--target-alias", "FREE_DB",
            "--approval-id", config.approval_id,
        ],
        env=env, workspace=workspace, connection_factory=factory,
    )
    assert code == 0
    assert binding["target_binding_digest"].startswith("sha256:")
    assert called is False


def test_target_binding_digest_requires_no_password(
    workspace: Path, config: m3.Config,
) -> None:
    env = env_for(config)
    del env["F10_10_M3_PASSWORD"]

    code, binding = m3.run_cli(
        [
            "--mode", "target-binding-digest", "--target-alias", "FREE_DB",
            "--approval-id", config.approval_id,
        ],
        env=env,
        workspace=workspace,
        connection_factory=lambda *_args: pytest.fail("offline mode must not connect"),
    )

    assert code == 0
    assert binding["target_binding_digest"] == configured_binding(config)


@pytest.mark.parametrize("mode", ["q0-only", "collect"])
def test_connected_modes_require_password_before_connection(
    workspace: Path, config: m3.Config, mode: str,
) -> None:
    env = env_for(config)
    del env["F10_10_M3_PASSWORD"]
    called = False

    def factory(*_args):
        nonlocal called
        called = True
        raise AssertionError("missing password must stop before connection")

    code, manifest = m3.run_cli(
        [
            "--mode", mode, "--target-alias", "FREE_DB",
            "--approval-id", config.approval_id,
        ],
        env=env, workspace=workspace, connection_factory=factory,
    )

    assert code == 2
    assert manifest["reason_codes"] == ["STOP_CONFIG_INVALID"]
    assert called is False


def test_default_connection_factory_rejects_missing_password_before_driver_import(
    config: m3.Config, monkeypatch: pytest.MonkeyPatch,
) -> None:
    passwordless = deepcopy(config)
    object.__setattr__(passwordless, "password", None)
    monkeypatch.setitem(sys.modules, "psycopg2", None)

    with pytest.raises(m3.CollectorError, match="STOP_CONFIG_INVALID"):
        m3.default_connection_factory(passwordless, None)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("mutate", "reason"),
    [
        (lambda info: setattr(info, "ssl_in_use", False), "STOP_TLS_CONTRACT"),
        (lambda info: setattr(info, "server_version", 0), "STOP_TLS_CONTRACT"),
        (
            lambda info: setattr(
                info, "ssl_attribute",
                lambda name: "TLSv1.1" if name == "protocol" else FakeInfo().ssl_attribute(name),
            ),
            "STOP_TLS_CONTRACT",
        ),
        (
            lambda info: setattr(
                info, "ssl_attribute",
                lambda name: None if name == "cipher" else FakeInfo().ssl_attribute(name),
            ),
            "STOP_TLS_CONTRACT",
        ),
        (
            lambda info: setattr(
                info, "ssl_attribute",
                lambda name: "" if name == "library" else FakeInfo().ssl_attribute(name),
            ),
            "STOP_TLS_CONTRACT",
        ),
        (
            lambda info: setattr(
                info, "ssl_attribute",
                lambda name: "x" * 257 if name == "cipher" else FakeInfo().ssl_attribute(name),
            ),
            "STOP_TLS_CONTRACT",
        ),
        (lambda info: setattr(info, "host", "aws-0-us-east-1.pooler.supabase.com"), "STOP_TARGET_MISMATCH"),
        (lambda info: setattr(info, "port", 6543), "STOP_TARGET_MISMATCH"),
        (lambda info: setattr(info, "dbname", "other"), "STOP_TARGET_MISMATCH"),
        (lambda info: setattr(info, "user", "other"), "STOP_TARGET_MISMATCH"),
    ],
)
def test_observed_transport_attestation_fails_closed(
    workspace: Path, config: m3.Config, mutate, reason: str,
) -> None:
    connection = FakeConnection()
    mutate(connection.info)
    with pytest.raises(m3.CollectorError, match=reason):
        collect_fake(config, workspace, connection)


def test_observed_transport_accepts_allowlisted_tls_and_has_separate_digest(
    workspace: Path, config: m3.Config,
) -> None:
    connection = FakeConnection()
    connection.info.server_version = 160000
    connection.info.ssl_attribute = lambda name: (
        "TLSv1.2" if name == "protocol" else FakeInfo().ssl_attribute(name)
    )
    result = collect_fake(config, workspace, connection)
    observed = result.private["observed_transport"]
    assert observed["protocol"] == "TLSv1.2"
    assert observed["server_version_num"] == 160000
    assert result.manifest["observed_transport_digest"].startswith("sha256:")
    assert (
        result.manifest["observed_transport_digest"]
        != result.manifest["target_binding_digest"]
    )


@pytest.mark.parametrize("mode", ["q0-only", "collect"])
def test_runtime_digest_domain_collision_stops_before_any_sql(
    workspace: Path, config: m3.Config, monkeypatch: pytest.MonkeyPatch,
    mode: str,
) -> None:
    collision = configured_binding(config)
    monkeypatch.setattr(
        m3, "observed_transport_attestation",
        lambda _connection, _config: ({"private": "transport"}, collision),
    )
    connection = FakeConnection()
    with m3.open_pinned_ca(config) as pinned_ca:
        with pytest.raises(m3.CollectorError) as raised:
            if mode == "collect":
                m3.collect(
                    config, lambda _config, _ca: connection,
                    m3.query_set_digest(workspace), "sha256:" + "1" * 64,
                    pinned_ca,
                )
            else:
                m3.collect_q0_only(
                    config, lambda _config, _ca: connection,
                    m3.query_set_digest(workspace), pinned_ca,
                )
    assert raised.value.reason_code == "STOP_DIGEST_DOMAIN_COLLISION"
    assert connection.transcript == []
    assert connection.closed is True


def test_q0_sql_and_validation_cover_exact_reader_capabilities(
    workspace: Path, config: m3.Config,
) -> None:
    lowered = m3.Q0_SQL.lower()
    for role_attribute in (
        "rolcanlogin", "rolinherit", "rolreplication", "rolconnlimit",
        "rolvaliduntil",
    ):
        assert role_attribute in lowered
    assert "m.member = r.oid" in lowered
    assert "m.roleid = r.oid" in lowered
    assert "role_member_count" in lowered
    assert "member_role_name" in lowered
    assert "m.admin_option" in lowered
    assert "m.inherit_option" in lowered
    assert "m.set_option" in lowered
    assert "a.attname not in ('id', 'is_active', 'syllabus', 'objectives')" in lowered
    assert "has_function_privilege" in lowered
    assert "p.prosecdef" in lowered
    assert "extract(epoch from r.rolvaliduntil)::bigint" in lowered
    assert "rolvaliduntil_is_future" in lowered

    connection = FakeConnection()
    changed = list(connection.q0)
    changed[8] = True
    changed[23] = True
    connection.q0 = tuple(changed)
    assert collect_fake(config, workspace, connection).manifest["decision"] == "PASS"


def test_ca_pin_rejects_symlink_nonregular_oversize_and_unsupported(
    config: m3.Config, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    link = tmp_path / "ca-link.pem"
    link.symlink_to(config.ca_file)
    linked = deepcopy(config)
    object.__setattr__(linked, "ca_file", link)
    with pytest.raises(m3.CollectorError, match="STOP_TLS_CONTRACT"):
        with m3.open_pinned_ca(linked):
            pass

    directory = deepcopy(config)
    object.__setattr__(directory, "ca_file", tmp_path)
    with pytest.raises(m3.CollectorError, match="STOP_TLS_CONTRACT"):
        with m3.open_pinned_ca(directory):
            pass

    monkeypatch.setattr(m3, "MAX_CA_BYTES", 2)
    with pytest.raises(m3.CollectorError, match="STOP_TLS_CONTRACT"):
        with m3.open_pinned_ca(config):
            pass

    monkeypatch.setattr(m3.sys, "platform", "win32")
    with pytest.raises(m3.CollectorError, match="STOP_UNSUPPORTED_PLATFORM"):
        with m3.open_pinned_ca(config):
            pass


def test_pinned_ca_is_sealed_memfd_and_source_mutation_cannot_change_it(
    config: m3.Config,
) -> None:
    original = config.ca_file.read_bytes()
    with m3.open_pinned_ca(config) as pinned:
        import fcntl

        required = (
            fcntl.F_SEAL_WRITE | fcntl.F_SEAL_GROW | fcntl.F_SEAL_SHRINK
            | fcntl.F_SEAL_SEAL
        )
        assert fcntl.fcntl(pinned.fd, fcntl.F_GET_SEALS) & required == required
        assert Path(pinned.proc_path).read_bytes() == original
        config.ca_file.write_bytes(b"mutated source ca\n")
        m3.verify_pinned_ca(pinned)
        assert Path(pinned.proc_path).read_bytes() == original
        config.ca_file.write_bytes(original)
        m3.verify_pinned_ca(pinned)
        with pytest.raises(OSError):
            os.write(pinned.fd, b"x")
        with pytest.raises(OSError):
            os.ftruncate(pinned.fd, len(original) + 1)


def test_ca_mutation_during_connection_uses_sealed_copy_and_passes(
    workspace: Path, config: m3.Config,
) -> None:
    expected = configured_binding(config)

    def mutating_factory(_config: m3.Config, _ca: m3.PinnedCA) -> FakeConnection:
        config.ca_file.write_bytes(b"mutated ca bytes\n")
        return FakeConnection()

    code, manifest = m3.run_cli(
        cli_args(workspace, config, expected_binding=expected),
        env=env_for(config), workspace=workspace, connection_factory=mutating_factory,
    )
    assert code == 0
    assert manifest["decision"] == "PASS"

def test_catalog_string_artifact_and_opaque_surface_limits(
    workspace: Path, config: m3.Config, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert m3.MAX_STRING_CHARS == 32_768
    monkeypatch.setattr(m3, "MAX_CATALOG_ROWS", 1)
    too_many = FakeConnection()
    too_many.triggers = [
        (1, "a", "definition", 2, "function_a", "function definition"),
        (3, "b", "definition", 4, "function_b", "function definition"),
    ]
    with pytest.raises(m3.CollectorError, match="STOP_CATALOG_LIMIT"):
        collect_fake(config, workspace, too_many)

    monkeypatch.setattr(m3, "MAX_CATALOG_ROWS", 50_000)
    opaque = FakeConnection()
    opaque.triggers = [(1, "a", None, 2, "function_a", "function definition")]
    with pytest.raises(m3.CollectorError, match="STOP_OPAQUE_ROUTINE_SURFACE"):
        collect_fake(config, workspace, opaque)

    monkeypatch.setattr(m3, "MAX_STRING_CHARS", 3)
    with pytest.raises(m3.CollectorError, match="STOP_UNTRUSTED_REMOTE_CONTENT"):
        collect_fake(config, workspace, FakeConnection([(uid(1), True, "long", None)]))

    monkeypatch.setattr(m3, "MAX_ARTIFACT_BYTES", 2)
    with m3.ArtifactDirectory(tmp_path) as artifacts:
        with pytest.raises(m3.CollectorError, match="STOP_ARTIFACT_LIMIT"):
            artifacts.publish("too-large.json", b"123")


def test_cumulative_remote_utf8_budget_exact_boundary_and_normalized_expansion(
    workspace: Path, config: m3.Config, monkeypatch: pytest.MonkeyPatch,
) -> None:
    baseline = collect_fake(config, workspace, FakeConnection(rows(1)))
    exact = baseline.private["remote_utf8_bytes"]
    monkeypatch.setattr(m3, "MAX_REMOTE_UTF8_BYTES", exact)
    assert collect_fake(config, workspace, FakeConnection(rows(1))).private[
        "remote_utf8_bytes"
    ] == exact
    monkeypatch.setattr(m3, "MAX_REMOTE_UTF8_BYTES", exact - 1)
    with pytest.raises(m3.CollectorError, match="STOP_REMOTE_BYTE_LIMIT"):
        collect_fake(config, workspace, FakeConnection(rows(1)))

    budget = m3.RemoteBudget(limit=4)
    budget.consume("éé")
    assert budget.used == 4
    with pytest.raises(m3.CollectorError, match="STOP_REMOTE_BYTE_LIMIT"):
        budget.consume("x")


def test_catalog_streaming_applies_budget_before_full_materialization() -> None:
    class StreamingCursor:
        def __init__(self) -> None:
            self.calls: list[int] = []

        def fetchmany(self, size: int) -> list[tuple[str]]:
            self.calls.append(size)
            return [("x" * 51,)]

    cursor = StreamingCursor()
    with pytest.raises(m3.CollectorError, match="STOP_REMOTE_BYTE_LIMIT"):
        m3._fetch_catalog(cursor, m3.RemoteBudget(limit=50))
    assert cursor.calls == [m3.CATALOG_FETCH_SIZE]


def test_path_safety_symlink_traversal_and_atomic_no_overwrite(tmp_path: Path) -> None:
    with pytest.raises(m3.CollectorError, match="STOP_PATH_UNSAFE"):
        m3._artifact_filename("local/f10_10/m3/../escape.json")
    with pytest.raises(m3.CollectorError, match="STOP_PATH_UNSAFE"):
        m3._artifact_filename("outside.json")

    with m3.ArtifactDirectory(tmp_path) as artifacts:
        artifacts.publish("artifact.json", b"{}\n")
        with pytest.raises(m3.CollectorError, match="STOP_ARTIFACT_EXISTS"):
            artifacts.publish("artifact.json", b"changed")
    path = tmp_path / m3.ARTIFACT_ROOT_RELATIVE / "artifact.json"
    assert path.read_bytes() == b"{}\n"
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert path.read_bytes() == b"{}\n"

    hostile = tmp_path / "hostile"
    hostile.mkdir()
    symlink_workspace = tmp_path / "symlink-workspace"
    symlink_workspace.mkdir()
    (symlink_workspace / "local").symlink_to(hostile, target_is_directory=True)
    with pytest.raises(m3.CollectorError, match="STOP_PATH_UNSAFE"):
        with m3.ArtifactDirectory(symlink_workspace):
            pass

    unsafe_permissions = tmp_path / "unsafe-permissions"
    unsafe_permissions.mkdir(mode=0o700)
    unsafe_permissions.chmod(0o720)
    try:
        with pytest.raises(m3.CollectorError, match="STOP_PATH_UNSAFE"):
            with m3.ArtifactDirectory(unsafe_permissions):
                pass
    finally:
        unsafe_permissions.chmod(0o700)


def test_manifest_fsync_failure_removes_commit_marker_but_keeps_private_orphan(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Precreate/verify the hierarchy before fault injection.
    with m3.ArtifactDirectory(tmp_path):
        pass
    with m3.ArtifactDirectory(tmp_path) as artifacts:
        artifacts.publish("private.json", b"private\n")
        original_fsync = m3.os.fsync

        def fail_directory_fsync(fd: int) -> None:
            if fd == artifacts.fd:
                raise OSError("injected directory fsync failure")
            original_fsync(fd)

        monkeypatch.setattr(m3.os, "fsync", fail_directory_fsync)
        with pytest.raises(m3.CollectorError, match="STOP_ARTIFACT_WRITE_FAILED"):
            artifacts.publish("manifest.json", b'{"commit_marker":true}\n')

    root = tmp_path / m3.ARTIFACT_ROOT_RELATIVE
    assert (root / "private.json").read_bytes() == b"private\n"
    assert not (root / "manifest.json").exists()


def test_temp_cleanup_failure_after_durable_publication_does_not_fail(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    with m3.ArtifactDirectory(tmp_path) as artifacts:
        original_unlink = m3.os.unlink

        def fail_temp_unlink(path: str, *, dir_fd: int | None = None) -> None:
            if path.startswith("."):
                raise OSError("injected temp cleanup failure")
            original_unlink(path, dir_fd=dir_fd)

        monkeypatch.setattr(m3.os, "unlink", fail_temp_unlink)
        artifacts.publish("durable.json", b"durable\n")

    assert (
        tmp_path / m3.ARTIFACT_ROOT_RELATIVE / "durable.json"
    ).read_bytes() == b"durable\n"


def test_hostile_data_and_raw_errors_never_enter_sanitized_manifest(
    workspace: Path, config: m3.Config,
) -> None:
    hostile = "secret-id host.example password=bad\nCREATE TABLE pwned"
    connection = FakeConnection([(uid(1), True, hostile, None)])
    result = collect_fake(config, workspace, connection)
    serialized = json.dumps(result.manifest, sort_keys=True)
    for value in (hostile, config.sql_host, config.project_ref, config.database, config.user, config.password, str(config.ca_file)):
        assert value not in serialized
    assert config.approval_id not in serialized
    assert "approval_id" not in result.manifest
    assert result.manifest["approval_fingerprint"].startswith("sha256:")

    def failing_factory(_config: m3.Config, _ca: m3.PinnedCA):
        raise RuntimeError(hostile)

    expected = configured_binding(config)
    args = cli_args(workspace, config, expected_binding=expected)
    code, manifest = m3.run_cli(args, env=env_for(config), workspace=workspace, connection_factory=failing_factory)
    assert code == 2
    failed = json.dumps(manifest)
    assert hostile not in failed and config.sql_host not in failed
    assert manifest["reason_codes"] == ["STOP_CONNECTION_FAILED"]
    private = json.loads(
        (workspace / m3.ARTIFACT_ROOT_RELATIVE / "private.json").read_text(encoding="utf-8")
    )
    assert hostile in private["raw_cause"]
    assert private["approval_id"] == config.approval_id


def cli_args(
    workspace: Path, config: m3.Config, *, expected_binding: str,
    mode: str = "collect",
) -> list[str]:
    args = [
        "--target-alias", config.target_alias,
        "--approval-id", config.approval_id,
        "--expected-query-set-digest", m3.query_set_digest(workspace),
        "--expected-target-binding-digest", expected_binding,
        "--private-artifact", "local/f10_10/m3/private.json",
        "--sanitized-manifest", "local/f10_10/m3/manifest.json",
    ]
    if mode != "collect":
        args[0:0] = ["--mode", mode]
    else:
        predecessor = m3.build_manifest(
            decision="PASS", reason_codes=[], target_alias="FREE_DB",
            approval_id=config.approval_id,
            query_digest=m3.query_set_digest(workspace),
            binding_digest=expected_binding,
            transport_digest="sha256:" + "2" * 64,
            mode="q0-only",
            transcript=[
                {"transaction": 1, "query_id": "TX_BEGIN", "parameter_count": 0},
                {"transaction": 1, "query_id": "Q0", "parameter_count": 0},
                {"transaction": 1, "query_id": "TX_COMMIT", "parameter_count": 0},
            ],
            summary={"rows_collected": 0, "content_bytes": 0},
        )
        predecessor_path = workspace / m3.ARTIFACT_ROOT_RELATIVE / "q0-pass.json"
        predecessor_path.parent.mkdir(parents=True, exist_ok=True)
        predecessor_bytes = m3.canonical_json(predecessor) + b"\n"
        predecessor_path.write_bytes(predecessor_bytes)
        predecessor_path.chmod(0o600)
        args.extend([
            "--q0-predecessor-manifest", "local/f10_10/m3/q0-pass.json",
            "--expected-q0-predecessor-digest",
            "sha256:" + hashlib.sha256(predecessor_bytes).hexdigest(),
        ])
    return args


def rewrite_predecessor(
    args: list[str], workspace: Path, mutate,
) -> None:
    path = workspace / m3.ARTIFACT_ROOT_RELATIVE / "q0-pass.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    mutate(payload)
    raw = m3.canonical_json(payload) + b"\n"
    path.write_bytes(raw)
    path.chmod(0o600)
    digest_index = args.index("--expected-q0-predecessor-digest") + 1
    args[digest_index] = "sha256:" + hashlib.sha256(raw).hexdigest()


def test_collect_requires_q0_predecessor_arguments_before_connection(
    workspace: Path, config: m3.Config,
) -> None:
    called = False
    args = cli_args(workspace, config, expected_binding=configured_binding(config))
    for flag in ("--q0-predecessor-manifest", "--expected-q0-predecessor-digest"):
        index = args.index(flag)
        del args[index:index + 2]

    def factory(*_args):
        nonlocal called
        called = True
        return FakeConnection()

    code, manifest = m3.run_cli(
        args, env=env_for(config), workspace=workspace, connection_factory=factory,
    )
    assert code == 2
    assert manifest["reason_codes"] == ["STOP_CLI_INVALID"]
    assert called is False


def test_collect_missing_or_tampered_predecessor_stops_before_connection(
    workspace: Path, config: m3.Config,
) -> None:
    called = False
    args = cli_args(workspace, config, expected_binding=configured_binding(config))
    predecessor = workspace / m3.ARTIFACT_ROOT_RELATIVE / "q0-pass.json"
    predecessor.unlink()

    def factory(*_args):
        nonlocal called
        called = True
        return FakeConnection()

    code, manifest = m3.run_cli(
        args, env=env_for(config), workspace=workspace, connection_factory=factory,
    )
    assert code == 2
    assert manifest["reason_codes"] == ["STOP_Q0_PREDECESSOR_INVALID"]
    assert called is False


@pytest.mark.parametrize(
    "mutate",
    [
        pytest.param(
            lambda payload: payload.__setitem__("target_binding_digest", "sha256:" + "0" * 64),
            id="wrong-binding",
        ),
        pytest.param(
            lambda payload: payload.__setitem__("query_set_digest", "sha256:" + "0" * 64),
            id="wrong-query",
        ),
        pytest.param(
            lambda payload: payload.__setitem__("writer_calls", 1),
            id="nonzero-writer",
        ),
        pytest.param(
            lambda payload: payload.__setitem__(
                "observed_transport_digest", payload["target_binding_digest"],
            ),
            id="digest-domain-collision",
        ),
        pytest.param(
            lambda payload: payload["transcript"].pop(),
            id="incomplete-transcript",
        ),
    ],
)
def test_collect_rejects_semantically_invalid_canonical_predecessor(
    workspace: Path, config: m3.Config, mutate,
) -> None:
    called = False
    args = cli_args(workspace, config, expected_binding=configured_binding(config))
    rewrite_predecessor(args, workspace, mutate)

    def factory(*_args):
        nonlocal called
        called = True
        return FakeConnection()

    code, manifest = m3.run_cli(
        args, env=env_for(config), workspace=workspace, connection_factory=factory,
    )
    assert code == 2
    assert manifest["reason_codes"] == ["STOP_Q0_PREDECESSOR_INVALID"]
    assert called is False


def test_collect_rejects_tampered_bytes_unsafe_path_and_symlink_predecessor(
    workspace: Path, config: m3.Config,
) -> None:
    expected = configured_binding(config)
    args = cli_args(workspace, config, expected_binding=expected)
    predecessor = workspace / m3.ARTIFACT_ROOT_RELATIVE / "q0-pass.json"
    predecessor.write_bytes(predecessor.read_bytes() + b" ")
    predecessor.chmod(0o600)
    code, manifest = m3.run_cli(args, env=env_for(config), workspace=workspace)
    assert code == 2
    assert manifest["reason_codes"] == ["STOP_Q0_PREDECESSOR_INVALID"]

    # A fresh workspace is not available inside one test after STOP artifacts,
    # so path validation is exercised before artifact publication.
    unsafe_workspace = workspace / "unsafe-case"
    unsafe_workspace.mkdir(mode=0o700)
    for relative in m3.QUERY_SET_FILES:
        destination = unsafe_workspace / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((workspace / relative).read_bytes())
    unsafe_args = cli_args(
        unsafe_workspace, config, expected_binding=configured_binding(config),
    )
    unsafe_args[unsafe_args.index("--q0-predecessor-manifest") + 1] = (
        "local/f10_10/m3/../q0-pass.json"
    )
    code, manifest = m3.run_cli(
        unsafe_args, env=env_for(config), workspace=unsafe_workspace,
    )
    assert code == 2
    assert manifest["reason_codes"] == ["STOP_PATH_UNSAFE"]

    symlink_workspace = workspace / "symlink-case"
    symlink_workspace.mkdir(mode=0o700)
    for relative in m3.QUERY_SET_FILES:
        destination = symlink_workspace / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((workspace / relative).read_bytes())
    symlink_args = cli_args(
        symlink_workspace, config, expected_binding=configured_binding(config),
    )
    symlink_path = symlink_workspace / m3.ARTIFACT_ROOT_RELATIVE / "q0-pass.json"
    target = symlink_path.with_name("q0-target.json")
    symlink_path.replace(target)
    symlink_path.symlink_to(target.name)
    code, manifest = m3.run_cli(
        symlink_args, env=env_for(config), workspace=symlink_workspace,
    )
    assert code == 2
    assert manifest["reason_codes"] == ["STOP_Q0_PREDECESSOR_INVALID"]


def test_cli_success_writes_only_two_0600_files(workspace: Path, config: m3.Config) -> None:
    expected_binding = configured_binding(config)
    code, manifest = m3.run_cli(
        cli_args(workspace, config, expected_binding=expected_binding),
        env=env_for(config), workspace=workspace,
        connection_factory=lambda _config, _ca: FakeConnection(),
    )
    assert code == 0 and manifest["decision"] == "PASS"
    outputs = sorted((workspace / m3.ARTIFACT_ROOT_RELATIVE).iterdir())
    assert [path.name for path in outputs] == [
        "manifest.json", "private.json", "q0-pass.json",
    ]
    assert json.loads(outputs[0].read_text(encoding="utf-8")) == manifest
    predecessor_digest = "sha256:" + hashlib.sha256(outputs[2].read_bytes()).hexdigest()
    assert manifest["q0_predecessor_digest"] == predecessor_digest
    private = json.loads(outputs[1].read_text(encoding="utf-8"))
    assert private["q0_predecessor_digest"] == predecessor_digest


def test_q0_only_has_exact_transcript_and_never_runs_q1_through_q4(
    workspace: Path, config: m3.Config,
) -> None:
    connection = FakeConnection()
    code, manifest = m3.run_cli(
        cli_args(
            workspace, config, expected_binding=configured_binding(config),
            mode="q0-only",
        ),
        env=env_for(config), workspace=workspace,
        connection_factory=lambda _config, _ca: connection,
    )

    assert code == 0
    assert connection.transcript == [
        (m3.BEGIN_SQL, None), (m3.Q0_SQL, None), (m3.COMMIT_SQL, None),
    ]
    assert manifest["mode"] == "q0-only"
    assert manifest["summary"] == {"rows_collected": 0, "content_bytes": 0}
    assert manifest["observed_transport_digest"].startswith("sha256:")
    assert manifest["snapshots_equal"] is False
    assert [item["query_id"] for item in manifest["transcript"]] == [
        "TX_BEGIN", "Q0", "TX_COMMIT",
    ]
    assert all(sql not in {query for _, query in m3.CATALOG_QUERIES} for sql, _ in connection.transcript)
    assert all(sql not in {m3.Q4_FIRST_SQL, m3.Q4_NEXT_SQL} for sql, _ in connection.transcript)
    serialized = json.dumps(manifest, sort_keys=True)
    for private_value in (
        config.api_url, config.project_ref, config.sql_host, config.database,
        config.user, config.provisioner, config.password, str(config.ca_file),
        config.approval_id,
    ):
        assert private_value not in serialized

    private = json.loads(
        (workspace / m3.ARTIFACT_ROOT_RELATIVE / "private.json").read_text(
            encoding="utf-8"
        )
    )
    assert private["catalog"] == {}
    assert private["snapshots"] == []
    assert private["page_boundaries"] == []
    assert PROVISIONER in json.dumps(private, sort_keys=True)


@pytest.mark.parametrize(
    ("index", "value"),
    [
        pytest.param(15, VALID_UNTIL_EPOCH + 1, id="expiry-mismatch"),
        pytest.param(16, False, id="expiry-not-future"),
        pytest.param(18, 0, id="missing-provisioner-edge"),
        pytest.param(19, "other_provisioner", id="wrong-provisioner"),
        pytest.param(20, False, id="provisioner-no-admin"),
        pytest.param(21, True, id="provisioner-inherits"),
        pytest.param(22, True, id="provisioner-can-set"),
        pytest.param(38, True, id="security-definer-execute"),
    ],
)
def test_q0_only_invalid_reader_stops_without_catalog_or_content_queries(
    workspace: Path, config: m3.Config, index: int, value: object,
) -> None:
    connection = FakeConnection()
    changed = list(connection.q0)
    changed[index] = value
    connection.q0 = tuple(changed)
    code, manifest = m3.run_cli(
        cli_args(
            workspace, config, expected_binding=configured_binding(config),
            mode="q0-only",
        ),
        env=env_for(config), workspace=workspace,
        connection_factory=lambda _config, _ca: connection,
    )

    assert code == 2
    assert manifest["reason_codes"] == ["STOP_NEEDS_READONLY_CHANNEL"]
    assert manifest["summary"] == {"rows_collected": 0, "content_bytes": 0}
    assert manifest["observed_transport_digest"].startswith("sha256:")
    assert [item["query_id"] for item in manifest["transcript"]] == [
        "TX_BEGIN", "Q0",
    ]
    assert connection.transcript == [(m3.BEGIN_SQL, None), (m3.Q0_SQL, None)]
    assert connection.rolled_back is True


def test_cli_failure_persists_sanitized_stop_evidence(workspace: Path, config: m3.Config) -> None:
    expected_binding = configured_binding(config)
    connection = FakeConnection()
    connection.schema[0] = ("id", "text", True, None)
    code, manifest = m3.run_cli(
        cli_args(workspace, config, expected_binding=expected_binding),
        env=env_for(config), workspace=workspace,
        connection_factory=lambda _config, _ca: connection,
    )
    assert code == 2
    assert manifest["reason_codes"] == ["STOP_SCHEMA_DRIFT"]
    root = workspace / m3.ARTIFACT_ROOT_RELATIVE
    private = json.loads((root / "private.json").read_text(encoding="utf-8"))
    public = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    assert private["reason_code"] == "STOP_SCHEMA_DRIFT"
    assert [item["query_id"] for item in private["transcript"]][:3] == [
        "TX_BEGIN", "Q0", "Q1",
    ]
    assert all("select" not in json.dumps(item).lower() for item in private["transcript"])
    assert public == manifest


def test_success_private_evidence_has_redacted_query_ids_and_page_boundaries(
    workspace: Path, config: m3.Config,
) -> None:
    result = collect_fake(config, workspace, FakeConnection(rows(501)))
    query_ids = [item["query_id"] for item in result.private["transcript"]]
    assert query_ids.count("Q0") == 3
    assert "Q4_NEXT" in query_ids
    boundaries = result.private["page_boundaries"]
    assert [(item["snapshot"], item["page"], item["row_count"]) for item in boundaries] == [
        (1, 1, 500), (1, 2, 1), (2, 1, 500), (2, 2, 1),
    ]
    assert boundaries[0]["last_id"] == str(uid(500))


def test_default_connection_factory_enforces_verify_full_and_timeouts(
    config: m3.Config, monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class DriverConnection:
        autocommit = False

    class Driver:
        __version__ = "2.9.12 (dt dec pq3 ext lo64)"

        @staticmethod
        def connect(**kwargs: object) -> DriverConnection:
            captured.update(kwargs)
            return DriverConnection()

    monkeypatch.setitem(sys.modules, "psycopg2", Driver())
    with m3.open_pinned_ca(config) as pinned_ca:
        connection = m3.default_connection_factory(config, pinned_ca)
        assert captured["sslrootcert"] == pinned_ca.proc_path
    assert connection.autocommit is True
    assert captured["sslmode"] == "verify-full"
    assert captured["connect_timeout"] == 10
    options = str(captured["options"])
    assert "search_path=pg_catalog" in options
    assert "client_encoding=UTF8" in options
    assert options.count("60000") == 3

    monkeypatch.setitem(sys.modules, "psycopg2", type("OldDriver", (), {"__version__": "2.9.11"})())
    with m3.open_pinned_ca(config) as pinned_ca:
        with pytest.raises(m3.CollectorError, match="STOP_DRIVER_VERSION"):
            m3.default_connection_factory(config, pinned_ca)


def test_binding_and_unsafe_paths_stop_before_connection(workspace: Path, config: m3.Config) -> None:
    called = False

    def factory(_config: m3.Config, _ca: m3.PinnedCA) -> FakeConnection:
        nonlocal called
        called = True
        return FakeConnection()

    wrong = cli_args(workspace, config, expected_binding="sha256:" + "0" * 64)
    code, manifest = m3.run_cli(
        wrong, env=env_for(config), workspace=workspace, connection_factory=factory,
    )
    assert (code, manifest["reason_codes"], called) == (2, ["STOP_TARGET_MISMATCH"], False)

    root = workspace / m3.ARTIFACT_ROOT_RELATIVE
    (root / "private.json").unlink()
    (root / "manifest.json").unlink()

    expected = configured_binding(config)
    unsafe = cli_args(workspace, config, expected_binding=expected)
    unsafe[unsafe.index("--private-artifact") + 1] = "outside.json"
    code, manifest = m3.run_cli(
        unsafe, env=env_for(config), workspace=workspace, connection_factory=factory,
    )
    assert (code, manifest["reason_codes"], called) == (2, ["STOP_PATH_UNSAFE"], False)


def test_query_set_is_captured_once_and_collect_never_rereads(
    workspace: Path, config: m3.Config, monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = configured_binding(config)
    args = cli_args(workspace, config, expected_binding=expected)
    original = m3.query_set_payload
    calls = 0

    def counted(root: Path) -> dict[str, object]:
        nonlocal calls
        calls += 1
        return original(root)

    monkeypatch.setattr(m3, "query_set_payload", counted)
    code, _ = m3.run_cli(
        args, env=env_for(config), workspace=workspace,
        connection_factory=lambda _config, _ca: FakeConnection(),
    )
    assert code == 0 and calls == 1


def test_approval_format_and_public_fingerprint_only(config: m3.Config) -> None:
    hostile = env_for(config)
    with pytest.raises(m3.CollectorError, match="STOP_CONFIG_INVALID"):
        m3.load_config(hostile, "FREE_DB", "M3-approval/password-123")
    manifest = m3.build_manifest(
        decision="STOP", reason_codes=["STOP_TEST"], target_alias="FREE_DB",
        approval_id=config.approval_id,
    )
    assert config.approval_id not in json.dumps(manifest)
    assert set(key for key in manifest if "approval" in key) == {"approval_fingerprint"}


def test_pass_hold_stop_manifest_semantics() -> None:
    for decision, reasons in (("PASS", []), ("HOLD", ["HOLD_METADATA_REVIEW"]), ("STOP", ["STOP_TEST"])):
        manifest = m3.build_manifest(
            decision=decision, reason_codes=reasons, target_alias="FREE_DB", approval_id="M3-APPROVAL-000001",
        )
        assert manifest["decision"] == decision
        assert manifest["reason_codes"] == reasons
    with pytest.raises(m3.CollectorError, match="STOP_INTERNAL_CONTRACT"):
        m3.build_manifest(
            decision="UNKNOWN", reason_codes=[], target_alias="FREE_DB", approval_id="M3-APPROVAL-000001",
        )


def test_cli_has_no_dsn_host_password_sql_or_mutating_flags() -> None:
    parser = m3.build_parser()
    flags = {option for action in parser._actions for option in action.option_strings}
    assert flags == {
        "-h", "--help", "--mode", "--target-alias", "--approval-id",
        "--expected-query-set-digest", "--expected-target-binding-digest",
        "--q0-predecessor-manifest", "--expected-q0-predecessor-digest",
        "--private-artifact", "--sanitized-manifest",
    }
    assert not any(token in " ".join(flags) for token in ("dsn", "password", "host", "sql", "execute"))
    assert "--query" not in flags

    code, manifest = m3.run_cli(["--password", "must-not-echo"])
    assert code == 2
    assert manifest["reason_codes"] == ["STOP_CLI_INVALID"]
    assert "must-not-echo" not in json.dumps(manifest)


def test_offline_digest_modes_do_not_connect_or_import_driver(
    workspace: Path, config: m3.Config, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(sys.modules, "psycopg2", None)
    code, query = m3.run_cli(["--mode", "query-set-digest"], workspace=workspace)
    assert code == 0 and query["query_set_digest"] == m3.query_set_digest(workspace)

    code, binding = m3.run_cli(
        [
            "--mode", "target-binding-digest", "--target-alias", "FREE_DB",
            "--approval-id", config.approval_id,
        ],
        env=env_for(config), workspace=workspace,
        connection_factory=lambda *_args: pytest.fail("must not connect"),
    )
    assert code == 0 and binding["target_binding_digest"] == configured_binding(config)
    assert binding["target_binding_version"] == m3.TARGET_BINDING_VERSION


def test_unexpected_internal_exception_returns_stable_result_without_raw_text(
    workspace: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    hostile = "unexpected secret traceback text"

    def explode(_root: Path):
        raise RuntimeError(hostile)

    monkeypatch.setattr(m3, "query_set_payload", explode)
    code, manifest = m3.run_cli(["--mode", "query-set-digest"], workspace=workspace)
    assert code == 2
    assert manifest["reason_codes"] == ["STOP_INTERNAL_FAILURE"]
    assert hostile not in json.dumps(manifest)


def test_ast_capability_surface_is_read_only_and_psycopg2_is_lazy() -> None:
    source_path = Path(m3.__file__)
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {
        alias.name.split(".")[0]
        for node in ast.walk(tree) if isinstance(node, ast.Import)
        for alias in node.names
    }
    imports.update(
        node.module.split(".")[0]
        for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module
    )
    assert not imports.intersection({"requests", "httpx", "socket", "subprocess", "urllib3"})
    top_level_imports = [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]
    assert "psycopg2" not in ast.unparse(ast.Module(body=top_level_imports, type_ignores=[]))
    lowered = "\n".join(m3.STATIC_SQL).lower()
    for forbidden in (" insert ", " update ", " delete ", " truncate ", " alter ", " create ", " drop ", " call "):
        assert forbidden not in f" {lowered} "
    assert "offset" not in lowered and "select *" not in lowered


def test_query_set_digest_normalizes_newlines_rejects_bom_and_binds_both_files(
    workspace: Path,
) -> None:
    baseline = m3.query_set_digest(workspace)
    test_path = workspace / m3.QUERY_SET_FILES[1]
    normalized = test_path.read_text(encoding="utf-8").replace("\n", "\r\n").encode("utf-8")
    test_path.write_bytes(normalized)
    assert m3.query_set_digest(workspace) == baseline
    test_path.write_bytes(b"\xef\xbb\xbf" + normalized)
    with pytest.raises(m3.CollectorError, match="STOP_QUERY_SET_INVALID"):
        m3.query_set_digest(workspace)


def test_import_does_not_require_psycopg2(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "psycopg2", None)
    assert importlib.reload(m3).COLLECTOR_VERSION == "f10.10-m3-readonly-collector-v2"


def test_protected_f97_workflow_runs_m3_zero_write_suite() -> None:
    workflow = (
        Path(__file__).parents[1] / ".github/workflows/f9-7-contract.yml"
    ).read_text(encoding="utf-8")
    assert "scripts/maintenance/f10_10_m3_readonly_collector.py" in workflow
    assert workflow.count("tests/test_f10_10_m3_readonly_collector.py") >= 2
