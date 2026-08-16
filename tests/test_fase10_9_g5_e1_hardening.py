from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path


WORKER_DIR = Path("workers/g5-trust-broker")
WRANGLER_CONFIG = WORKER_DIR / "wrangler.repository-only.jsonc"
PACKAGE_JSON = WORKER_DIR / "package.json"
PACKAGE_LOCK = WORKER_DIR / "package-lock.json"
WRANGLER_BIN = WORKER_DIR / "node_modules" / ".bin" / "wrangler"
EGRESS_GUARD = WORKER_DIR / "test" / "block-egress.mjs"
DRY_RUN_OUTDIR = Path("/tmp/studiamatch-g5-e1-dry-run")
DRY_RUN_WORKER_DIR = Path("/tmp/studiamatch-g5-worker-dry-run")
WRANGLER_CACHE = WORKER_DIR / ".wrangler"
MANIFEST = Path(".context/operaciones/g5_operational_activation_manifest_2026_08_15.json")
RUNBOOK = Path(".context/operaciones/g5_operational_activation_runbook_2026_08_15.md")
ADR16 = Path(".context/decisiones/ADR-0016_g5_operational_activation_gates.md")
ADR17 = Path(".context/decisiones/ADR-0017_g5_e1_cloudflare_deployment_hardening.md")

WRANGLER_VERSION = "4.44.0"
DEPLOY_COMMAND = "wrangler deploy --strict --config wrangler.repository-only.jsonc"
DRY_RUN_COMMAND = (
    "wrangler deploy --strict --config wrangler.repository-only.jsonc "
    "--dry-run --outdir /tmp/studiamatch-g5-e1-dry-run"
)
FORBIDDEN_DEPLOY_FLAGS = (
    "--temporary",
    "--route",
    "--routes",
    "--domain",
    "--triggers",
    "--schedule",
    "--schedules",
    "--env-file",
    "--secrets-file",
    "--keep-vars",
)
SENSITIVE_PATTERNS = (
    r"sb_secret_[A-Za-z0-9_-]+",
    r"sb_publishable_[A-Za-z0-9_-]+",
    r"sbp_[A-Za-z0-9_-]+",
    r"eyJhbG[A-Za-z0-9_-]+",
    r"ghp_[A-Za-z0-9]+",
    r"gho_[A-Za-z0-9]+",
    r"ghs_[A-Za-z0-9]+",
    r"github_pat_[A-Za-z0-9_-]+",
    r"-----BEGIN [A-Z ]+PRIVATE KEY-----",
)


def _json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _clean_env(*, block_egress: bool = False) -> dict[str, str]:
    env = {
        "CI": "true",
        "HOME": "/tmp",
        "NO_COLOR": "1",
        "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
        "WRANGLER_SEND_METRICS": "false",
    }
    if block_egress:
        env["NODE_OPTIONS"] = f"--import={EGRESS_GUARD.resolve().as_uri()}"
    assert not any(key.startswith(("CLOUDFLARE_", "CF_")) for key in env)
    return env


def _repo_cache_files() -> list[Path]:
    if not WRANGLER_CACHE.exists():
        return []
    return sorted(
        path.relative_to(WRANGLER_CACHE)
        for path in WRANGLER_CACHE.rglob("*")
        if path.is_file()
    )


def _prepare_writable_dry_run_worker() -> Path:
    shutil.rmtree(DRY_RUN_WORKER_DIR, ignore_errors=True)
    DRY_RUN_WORKER_DIR.mkdir(parents=True)
    for source in (PACKAGE_JSON, PACKAGE_LOCK, WRANGLER_CONFIG):
        shutil.copy2(source, DRY_RUN_WORKER_DIR / source.name)
    shutil.copytree(WORKER_DIR / "src", DRY_RUN_WORKER_DIR / "src", symlinks=True)
    node_modules = WORKER_DIR / "node_modules"
    assert node_modules.exists(), "run npm ci --ignore-scripts in workers/g5-trust-broker first"
    try:
        os.symlink(
            node_modules.resolve(),
            DRY_RUN_WORKER_DIR / "node_modules",
            target_is_directory=True,
        )
    except (NotImplementedError, OSError):
        shutil.copytree(node_modules, DRY_RUN_WORKER_DIR / "node_modules", symlinks=True)
    return DRY_RUN_WORKER_DIR


def test_wrangler_version_is_exact_and_lockfile_is_versioned() -> None:
    package = _json(PACKAGE_JSON)
    lock = _json(PACKAGE_LOCK)
    assert package["private"] is True
    assert package["devDependencies"] == {"wrangler": WRANGLER_VERSION}
    assert re.fullmatch(r"\d+\.\d+\.\d+", WRANGLER_VERSION)
    assert lock["lockfileVersion"] == 3
    assert lock["packages"][""]["devDependencies"] == {"wrangler": WRANGLER_VERSION}
    assert lock["packages"]["node_modules/wrangler"]["version"] == WRANGLER_VERSION


def test_lockfile_uses_registry_only_and_has_no_unexpected_root_dependency() -> None:
    lock = _json(PACKAGE_LOCK)
    assert set(lock["packages"][""]["devDependencies"]) == {"wrangler"}
    for name, package in lock["packages"].items():
        if not name:
            continue
        resolved = package.get("resolved")
        if resolved is not None:
            assert str(resolved).startswith("https://registry.npmjs.org/")
        assert "scripts" not in package


def test_wrangler_cli_version_and_strict_support_are_executable() -> None:
    assert WRANGLER_BIN.exists(), "run npm ci --ignore-scripts in workers/g5-trust-broker first"
    version = subprocess.run(
        [str(WRANGLER_BIN.resolve()), "--version"],
        cwd=WORKER_DIR,
        env=_clean_env(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    version_match = re.search(r"\b\d+\.\d+\.\d+\b", version.stdout)
    assert version_match and version_match.group(0) == WRANGLER_VERSION

    help_result = subprocess.run(
        [str(WRANGLER_BIN.resolve()), "deploy", "--help"],
        cwd=WORKER_DIR,
        env=_clean_env(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    assert "--strict" in help_result.stdout


def test_e1_dry_run_executes_without_cloudflare_credentials_or_external_egress() -> None:
    assert EGRESS_GUARD.exists()
    shutil.rmtree(DRY_RUN_OUTDIR, ignore_errors=True)
    repo_cache_before = _repo_cache_files()
    dry_run_worker = _prepare_writable_dry_run_worker()
    dry_run_cache = dry_run_worker / ".wrangler"
    env = _clean_env(block_egress=True)
    for name in ("CLOUDFLARE_API_TOKEN", "CLOUDFLARE_ACCOUNT_ID"):
        assert name not in env
    try:
        result = subprocess.run(
            ["npm", "run", "e1:dry-run"],
            cwd=dry_run_worker,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=120,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert DRY_RUN_OUTDIR.exists()
        generated = [path for path in DRY_RUN_OUTDIR.rglob("*") if path.is_file()]
        assert generated, "dry-run did not materialize a bundle"
        for path in generated:
            assert path.resolve().is_relative_to(DRY_RUN_OUTDIR.resolve())
        assert _repo_cache_files() == repo_cache_before
        assert not any(path.is_file() for path in dry_run_cache.rglob("*"))
        assert not (WORKER_DIR / "dist").exists()
    finally:
        shutil.rmtree(DRY_RUN_OUTDIR, ignore_errors=True)
        shutil.rmtree(DRY_RUN_WORKER_DIR, ignore_errors=True)


def test_wrangler_config_is_isolated_and_explicitly_non_public() -> None:
    config = _json(WRANGLER_CONFIG)
    assert set(config) == {
        "name",
        "main",
        "compatibility_date",
        "workers_dev",
        "preview_urls",
        "durable_objects",
        "migrations",
    }
    assert config["name"] == "g5-trust-broker-repository-only"
    assert config["main"] == "src/index.mjs"
    assert config["compatibility_date"] == "2026-08-15"
    assert config["workers_dev"] is False
    assert config["preview_urls"] is False
    for forbidden in ("route", "routes", "domain", "domains", "custom_domain", "custom_domains", "triggers"):
        assert forbidden not in config
    assert config["durable_objects"] == {
        "bindings": [
            {"name": "G5_ATOMIC_LEDGER", "class_name": "G5AtomicLedgerDurableObject"}
        ]
    }
    assert config["migrations"] == [
        {"tag": "repository-only-v1", "new_sqlite_classes": ["G5AtomicLedgerDurableObject"]}
    ]


def test_package_scripts_require_dry_run_before_exact_deploy_command() -> None:
    scripts = _json(PACKAGE_JSON)["scripts"]
    assert list(scripts) == ["e1:dry-run", "e1:deploy"]
    assert scripts["e1:dry-run"] == DRY_RUN_COMMAND
    assert scripts["e1:deploy"] == DEPLOY_COMMAND
    assert "--dry-run" in scripts["e1:dry-run"]
    assert "--outdir /tmp/studiamatch-g5-e1-dry-run" in scripts["e1:dry-run"]
    for command in scripts.values():
        assert "--strict" in command
        assert "--config wrangler.repository-only.jsonc" in command
        for flag in FORBIDDEN_DEPLOY_FLAGS:
            assert flag not in command


def test_cloudflare_credential_names_are_standard_for_e1_only() -> None:
    combined = ADR17.read_text(encoding="utf-8") + RUNBOOK.read_text(encoding="utf-8")
    assert "CLOUDFLARE_API_TOKEN" in combined
    assert "CLOUDFLARE_ACCOUNT_ID" in combined
    assert "CF_API_TOKEN" in combined
    assert "CF_ACCOUNT_ID" in combined
    package_and_config = PACKAGE_JSON.read_text(encoding="utf-8") + WRANGLER_CONFIG.read_text(encoding="utf-8")
    assert "CF_API_TOKEN" not in package_and_config
    assert "CF_ACCOUNT_ID" not in package_and_config
    assert "CLOUDFLARE_API_TOKEN" not in package_and_config
    assert "CLOUDFLARE_ACCOUNT_ID" not in package_and_config


def test_e4b_endpoint_gate_is_separate_and_blocks_e5() -> None:
    manifest = _json(MANIFEST)
    gates = {gate["id"]: gate for gate in manifest["gates"]}
    assert list(gates) == ["E1", "E2", "E3", "E4", "E4A", "E4B", "E5", "E6"]
    assert gates["E4B"]["domain"] == "trust_broker_endpoint_exposure_decision"
    assert any("E4B" in item for item in gates["E5"]["preconditions"])
    assert any("E4B" in item for item in gates["E5"]["stop_conditions"])
    docs = ADR16.read_text(encoding="utf-8") + ADR17.read_text(encoding="utf-8") + RUNBOOK.read_text(encoding="utf-8")
    assert "E4B" in docs
    assert "DEFINED_NOT_EXECUTED" in docs
    assert "endpoint" in docs
    assert "E5" in docs


def test_e1_hardening_docs_preserve_stops_and_no_sensitive_values() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (PACKAGE_JSON, PACKAGE_LOCK, WRANGLER_CONFIG, ADR17, RUNBOOK, MANIFEST)
    )
    for marker in (
        "MERGED_POST_MERGE_VERIFIED",
        "E1_ACCOUNT_READINESS_GO",
        "E1_DEPLOYMENT_STOP_WRANGLER_FLAG_INCOMPATIBLE",
        "NOT_EXECUTED",
        "E1_DEPLOYMENT_PASS",
        "NOT_CREATED_NOT_APPROVED_NOT_CONSUMED",
        "STOP_G5_TRUST_VERIFICATION_NOT_IMPLEMENTED",
        "IMPLEMENTED_DISABLED_NOT_CONFIGURED",
        "G5_TRUST_RUNTIME_ENABLED",
    ):
        assert marker in combined
    for pattern in SENSITIVE_PATTERNS:
        assert not re.search(pattern, combined)
