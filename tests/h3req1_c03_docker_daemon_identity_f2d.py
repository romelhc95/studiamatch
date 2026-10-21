#!/usr/bin/env python3
"""Prove a local Docker socket's direct peer through Linux SO_PEERCRED."""

from __future__ import annotations

import os
import re
import socket
import stat
import struct
import sys
from pathlib import Path


PROC = Path("/proc")
SOCKET_PATH_PATTERN = re.compile(r"^/[A-Za-z0-9_./+-]{1,240}$")


def fail(reason: str) -> int:
    print(f"daemon-proof=NO-GO|reason={reason}")
    return 1


def process_start_ticks(pid: int) -> str:
    contents = (PROC / str(pid) / "stat").read_text(encoding="ascii")
    close_paren = contents.rfind(")")
    if close_paren < 0:
        raise ValueError("invalid-process-stat")
    fields_after_comm = contents[close_paren + 1 :].split()
    if len(fields_after_comm) <= 19 or not fields_after_comm[19].isdigit():
        raise ValueError("invalid-process-start-time")
    return fields_after_comm[19]


def effective_uid(pid: int) -> int:
    for line in (PROC / str(pid) / "status").read_text(encoding="ascii").splitlines():
        if line.startswith("Uid:"):
            values = line.split()
            if len(values) >= 3 and values[2].isdigit():
                return int(values[2])
            break
    raise ValueError("effective-uid-unavailable")


def stat_socket(path: str) -> os.stat_result:
    metadata = os.stat(path, follow_symlinks=True)
    if not stat.S_ISSOCK(metadata.st_mode):
        raise ValueError("endpoint-is-not-socket")
    return metadata


def main() -> int:
    if (
        not sys.platform.startswith("linux")
        or not hasattr(socket, "SO_PEERCRED")
        or len(sys.argv) != 3
    ):
        return fail("peer-credential-interface-unavailable")

    canonical_path, selected_path = sys.argv[1:]
    if (
        not SOCKET_PATH_PATTERN.fullmatch(canonical_path)
        or os.path.realpath(canonical_path) != canonical_path
        or not SOCKET_PATH_PATTERN.fullmatch(selected_path)
    ):
        return fail("socket-path-schema-or-canonicality")
    if os.path.realpath(selected_path) != canonical_path:
        return fail("selected-and-canonical-socket-differ")

    try:
        canonical_before = stat_socket(canonical_path)
        selected_before = stat_socket(selected_path)
    except OSError:
        return fail("socket-stat-unavailable")
    except ValueError as error:
        return fail(str(error))

    if (canonical_before.st_dev, canonical_before.st_ino) != (
        selected_before.st_dev,
        selected_before.st_ino,
    ):
        return fail("selected-and-canonical-socket-differ")

    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
            connection.settimeout(3.0)
            connection.connect(canonical_path)
            raw_credentials = connection.getsockopt(
                socket.SOL_SOCKET,
                socket.SO_PEERCRED,
                struct.calcsize("3i"),
            )
        peer_pid, peer_uid, _peer_gid = struct.unpack("3i", raw_credentials)
    except (OSError, struct.error):
        return fail("direct-peer-credentials-unavailable")

    if peer_pid <= 1 or peer_uid < 0:
        return fail("direct-peer-credentials-invalid")

    try:
        started_before = process_start_ticks(peer_pid)
        comm = (PROC / str(peer_pid) / "comm").read_text(encoding="ascii").strip()
        executable_path = os.readlink(PROC / str(peer_pid) / "exe")
        executable = Path(executable_path)
        executable_metadata = os.stat(PROC / str(peer_pid) / "exe")
        process_uid = effective_uid(peer_pid)
        peer_pid_namespace = os.readlink(PROC / str(peer_pid) / "ns/pid")
        local_pid_namespace = os.readlink(PROC / "self/ns/pid")
        started_after = process_start_ticks(peer_pid)
        canonical_after = stat_socket(canonical_path)
        selected_after = stat_socket(selected_path)
    except (OSError, UnicodeError, ValueError):
        return fail("direct-peer-process-metadata-unavailable")

    if started_before != started_after:
        return fail("direct-peer-process-changed-during-read")
    if (canonical_before.st_dev, canonical_before.st_ino) != (
        canonical_after.st_dev,
        canonical_after.st_ino,
    ) or (selected_before.st_dev, selected_before.st_ino) != (
        selected_after.st_dev,
        selected_after.st_ino,
    ):
        return fail("socket-identity-changed-during-peer-proof")
    if (canonical_after.st_dev, canonical_after.st_ino) != (
        selected_after.st_dev,
        selected_after.st_ino,
    ):
        return fail("selected-and-canonical-socket-changed")
    if comm != "dockerd" or executable.name != "dockerd":
        return fail("direct-peer-is-not-dockerd")
    if peer_uid != process_uid:
        return fail("peer-credential-does-not-match-process")
    if peer_pid_namespace != local_pid_namespace:
        return fail("daemon-pid-namespace-is-not-local")
    if (
        not stat.S_ISREG(executable_metadata.st_mode)
        or executable_metadata.st_uid != 0
        or stat.S_IMODE(executable_metadata.st_mode) & 0o022
        or not stat.S_IMODE(executable_metadata.st_mode) & 0o111
    ):
        return fail("daemon-executable-ownership-or-mode")

    print(
        "daemon-proof=PASS"
        f"|pid={peer_pid}|process=dockerd|exe=dockerd|uid={process_uid}"
        "|pid-namespace=local|exe-owner=root|exe-group-world-writable=false"
        f"|socket-inode={canonical_after.st_ino}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
