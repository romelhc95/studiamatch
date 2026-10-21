from __future__ import annotations

import importlib.util
import os
import socket
import stat
import struct
import sys
from pathlib import Path

import pytest


REAL_SOCKET = socket.socket
HELPER_PATH = Path(__file__).with_name("h3req1_c03_docker_daemon_identity_f2d.py")
SPEC = importlib.util.spec_from_file_location("h3req1_docker_peer_f2d", HELPER_PATH)
assert SPEC is not None and SPEC.loader is not None
peer_helper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(peer_helper)


@pytest.fixture
def synthetic_peer(tmp_path, monkeypatch):
    """Supply a socket inode and proc metadata without a Docker API or live /proc reads."""
    peer_pid = 43210
    socket_path = tmp_path / "fixture.sock"
    listener = REAL_SOCKET(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(socket_path))
    listener.listen(1)

    proc_root = tmp_path / "proc-fixture"
    peer_dir = proc_root / str(peer_pid)
    (peer_dir / "ns").mkdir(parents=True)
    stat_fields = ["S", *(["0"] * 18), "123456"]
    (peer_dir / "stat").write_text(
        f"{peer_pid} (dockerd) {' '.join(stat_fields)}\n", encoding="ascii"
    )
    (peer_dir / "comm").write_text("dockerd\n", encoding="ascii")
    (peer_dir / "status").write_text("Name:\tdockerd\nUid:\t0\t0\t0\t0\n", encoding="ascii")

    peer_state = {
        "pid": peer_pid,
        "peer_uid": 0,
        "process_uid": 0,
        "peer_namespace": "pid:[fixture-namespace]",
        "local_namespace": "pid:[fixture-namespace]",
        "executable_mode": 0o755,
        "operations": [],
    }

    class SyntheticSocket:
        def __init__(self, *_args, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def settimeout(self, _timeout):
            pass

        def connect(self, path):
            peer_state["operations"].append(("connect", path))

        def getsockopt(self, level, option, _length):
            assert level == socket.SOL_SOCKET
            assert option == socket.SO_PEERCRED
            peer_state["operations"].append(("getsockopt", option))
            return struct.pack("3i", peer_state["pid"], peer_state["peer_uid"], 0)

    original_stat = os.stat
    original_readlink = os.readlink
    executable_entry = peer_dir / "exe"
    pid_namespace_entry = peer_dir / "ns" / "pid"
    local_namespace_entry = proc_root / "self" / "ns" / "pid"

    def fixture_stat(path, *args, **kwargs):
        if os.fspath(path) == os.fspath(executable_entry):
            return os.stat_result(
                (
                    stat.S_IFREG | peer_state["executable_mode"],
                    0,
                    0,
                    1,
                    0,
                    0,
                    4096,
                    0,
                    0,
                    0,
                )
            )
        return original_stat(path, *args, **kwargs)

    def fixture_readlink(path, *args, **kwargs):
        path_value = os.fspath(path)
        if path_value == os.fspath(executable_entry):
            return "/usr/sbin/dockerd"
        if path_value == os.fspath(pid_namespace_entry):
            return peer_state["peer_namespace"]
        if path_value == os.fspath(local_namespace_entry):
            return peer_state["local_namespace"]
        return original_readlink(path, *args, **kwargs)

    monkeypatch.setattr(peer_helper, "PROC", proc_root)
    monkeypatch.setattr(peer_helper.socket, "socket", SyntheticSocket)
    monkeypatch.setattr(peer_helper.os, "stat", fixture_stat)
    monkeypatch.setattr(peer_helper.os, "readlink", fixture_readlink)
    monkeypatch.setattr(
        sys,
        "argv",
        [str(HELPER_PATH), str(socket_path), str(socket_path)],
    )

    yield peer_state, socket_path
    listener.close()


def test_proves_only_synthetic_peer_and_sends_no_application_bytes(
    synthetic_peer, capsys
):
    peer_state, _socket_path = synthetic_peer

    assert peer_helper.main() == 0

    output = capsys.readouterr().out
    assert output.startswith("daemon-proof=PASS|pid=43210|process=dockerd")
    assert peer_state["operations"] == [
        ("connect", str(_socket_path)),
        ("getsockopt", socket.SO_PEERCRED),
    ]


@pytest.mark.parametrize(
    ("field", "value", "expected_reason"),
    [
        ("comm", "containerd-shim", "direct-peer-is-not-dockerd"),
        ("peer_uid", 1001, "peer-credential-does-not-match-process"),
        ("peer_namespace", "pid:[other-namespace]", "daemon-pid-namespace-is-not-local"),
        ("executable_mode", 0o777, "daemon-executable-ownership-or-mode"),
    ],
)
def test_rejects_peer_identity_or_executable_mismatches(
    synthetic_peer, capsys, field, value, expected_reason
):
    peer_state, _socket_path = synthetic_peer
    if field == "comm":
        (Path(peer_helper.PROC) / str(peer_state["pid"]) / "comm").write_text(
            value + "\n", encoding="ascii"
        )
    else:
        peer_state[field] = value

    assert peer_helper.main() == 1
    assert capsys.readouterr().out.strip() == f"daemon-proof=NO-GO|reason={expected_reason}"


def test_rejects_distinct_selected_socket_before_reading_peer(
    synthetic_peer, tmp_path, capsys, monkeypatch
):
    peer_state, canonical_socket = synthetic_peer
    second_socket = REAL_SOCKET(socket.AF_UNIX, socket.SOCK_STREAM)
    second_path = tmp_path / "different.sock"
    second_socket.bind(str(second_path))
    try:
        monkeypatch.setattr(
            sys,
            "argv",
            [str(HELPER_PATH), str(canonical_socket), str(second_path)],
        )

        assert peer_helper.main() == 1
        assert capsys.readouterr().out.strip() == (
            "daemon-proof=NO-GO|reason=selected-and-canonical-socket-differ"
        )
        assert peer_state["operations"] == []
    finally:
        second_socket.close()
