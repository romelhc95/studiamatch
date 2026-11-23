"""Restore one serialized Actions-style manifest, then execute a real CLI."""

from __future__ import annotations

import base64
import hashlib
import os
import runpy
import sys
from pathlib import Path


def restore_manifest() -> None:
    encoded = os.environ.get("FG2_FIXTURE_MANIFEST_B64")
    expected = os.environ.get("FG2_FIXTURE_MANIFEST_SHA256")
    if not encoded and not expected:
        return
    if not encoded or not expected:
        raise SystemExit("phase=manifest_restore|result=FAIL|code=missing_binding")
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (ValueError, TypeError):
        raise SystemExit("phase=manifest_restore|result=FAIL|code=invalid_base64") from None
    actual = hashlib.sha256(raw).hexdigest()
    if actual != expected.lower():
        raise SystemExit("phase=manifest_restore|result=FAIL|code=digest_mismatch")
    target = Path(os.environ.get("FG2_FIXTURE_RESTORED_MANIFEST", "/tmp/fg2-cohort-manifest.json"))
    target.write_bytes(raw)
    print(f"phase=manifest_restore|result=PASS|sha256={actual}")


def export_manifest_for_host() -> None:
    target = os.environ.get("FG2_FIXTURE_EXPORT_MANIFEST")
    if not target:
        return
    if target != "/run/fg2-cohort-manifest.json":
        raise SystemExit("phase=manifest_export|result=FAIL|code=unexpected_path")
    try:
        os.chmod(target, 0o644)
    except OSError:
        raise SystemExit("phase=manifest_export|result=FAIL|code=chmod_failed") from None
    print("phase=manifest_export|result=PASS|mode=0644")


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("phase=entrypoint|result=FAIL|code=missing_target")
    restore_manifest()
    script = sys.argv[1]
    args = sys.argv[2:]
    # Match ``python /path/to/script.py`` semantics used by Actions: Python
    # adds the entrypoint directory to sys.path. ``runpy.run_path`` does not.
    script_path = Path(script).resolve()
    if str(script_path.parent) not in sys.path:
        sys.path.insert(0, str(script_path.parent))
    sys.argv = [script, *args]
    try:
        if (
            script_path.name == "sync_vector_worker.py"
            and os.environ.get("FG2_FIXTURE_PROVIDER_ADAPTER") == "1"
        ):
            # The fixture must exercise the candidate's real CLI and main()
            # while allowing its explicitly synthetic provider result to pass
            # the production provenance guard. runpy's __main__ namespace is
            # distinct from the module patched by sitecustomize, so load the
            # same entrypoint without auto-running it, set the fixture-only
            # class attribute in that namespace, then invoke its real main().
            namespace = runpy.run_path(str(script_path), run_name="fg2_fixture_entrypoint")
            worker_class = namespace.get("SyncVectorWorker")
            entrypoint_main = namespace.get("main")
            if worker_class is None or not callable(entrypoint_main):
                raise SystemExit("phase=entrypoint|result=FAIL|code=sync_fixture_entrypoint_unavailable")
            worker_class._fg2_fixture_provider_allowed = True
            entrypoint_main()
        else:
            runpy.run_path(str(script_path), run_name="__main__")
    except SystemExit as exc:
        if exc.code not in (None, 0):
            raise
        export_manifest_for_host()
        raise
    else:
        export_manifest_for_host()


if __name__ == "__main__":
    main()
