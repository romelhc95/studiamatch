#!/usr/bin/env python3
"""Read one tracked worktree path without following symlink components."""

from __future__ import annotations

import errno
import os
import stat
import sys


def _error() -> int:
    sys.stderr.write("worktree-read=UNSAFE_OR_UNAVAILABLE\n")
    return 2


def _write_all(data: bytes) -> bool:
    view = memoryview(data)
    while view:
        written = os.write(sys.stdout.fileno(), view)
        if written <= 0:
            return False
        view = view[written:]
    return True


def main() -> int:
    if len(sys.argv) != 3:
        return _error()

    root, relative_path = sys.argv[1:]
    if not relative_path or os.path.isabs(relative_path):
        return _error()

    parts = relative_path.split(os.sep)
    if any(part in ("", ".", "..") for part in parts):
        return _error()

    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    file_flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    opened: list[int] = []

    try:
        current_fd = os.open(root, directory_flags)
        opened.append(current_fd)

        for part in parts[:-1]:
            try:
                current_fd = os.open(part, directory_flags, dir_fd=current_fd)
            except FileNotFoundError:
                return 0
            opened.append(current_fd)

        final_name = parts[-1]
        try:
            file_fd = os.open(final_name, file_flags, dir_fd=current_fd)
        except FileNotFoundError:
            return 0
        except OSError as error:
            if error.errno != errno.ELOOP:
                return _error()
            try:
                link_text = os.readlink(final_name, dir_fd=current_fd)
            except OSError:
                return _error()
            return 0 if _write_all(os.fsencode(link_text)) else _error()

        opened.append(file_fd)
        if not stat.S_ISREG(os.fstat(file_fd).st_mode):
            return _error()

        while True:
            chunk = os.read(file_fd, 65536)
            if not chunk:
                break
            if not _write_all(chunk):
                return _error()
        return 0
    except OSError:
        return _error()
    finally:
        for fd in reversed(opened):
            try:
                os.close(fd)
            except OSError:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
