from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.maintenance.pro_h3_migration_manifest import (
    H3_PRO_MIGRATION_PRECEDENCE,
    H3_PRO_MIGRATION_SHA256,
    H3_PRO_MIGRATIONS,
    validate_h2_cohort_inputs,
    validate_h3_manifest_names,
    validate_h3_manifest_tree,
)
from scripts.maintenance.db_migrate import PRO_MIGRATION_MANIFESTS, resolve_requested_migrations


ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "db/migrations"


def test_h3_manifest_has_exact_ordered_inventory_and_matching_sha_pins() -> None:
    assert len(H3_PRO_MIGRATIONS) == 31
    assert len(set(H3_PRO_MIGRATIONS)) == len(H3_PRO_MIGRATIONS)
    assert set(H3_PRO_MIGRATION_SHA256) == set(H3_PRO_MIGRATIONS)
    assert validate_h3_manifest_tree(MIGRATIONS) == H3_PRO_MIGRATION_SHA256


def test_h3_manifest_rejects_unknown_missing_duplicate_and_reordered_selection() -> None:
    with pytest.raises(ValueError, match="pinned ordered inventory"):
        validate_h3_manifest_names((*H3_PRO_MIGRATIONS, "20269999_unapproved"))
    with pytest.raises(ValueError, match="pinned ordered inventory"):
        validate_h3_manifest_names(H3_PRO_MIGRATIONS[:-1])
    with pytest.raises(ValueError, match="pinned ordered inventory"):
        validate_h3_manifest_names((H3_PRO_MIGRATIONS[1], H3_PRO_MIGRATIONS[0], *H3_PRO_MIGRATIONS[2:]))
    with pytest.raises(ValueError, match="pinned ordered inventory"):
        validate_h3_manifest_names((*H3_PRO_MIGRATIONS, H3_PRO_MIGRATIONS[0]))


def test_pro_migrator_resolves_only_the_exact_h3_manifest_and_rejects_invalid_inputs() -> None:
    parser = argparse.ArgumentParser()
    h3_args = SimpleNamespace(env="pro", manifest="h3-editorial-expand", only=[])
    assert PRO_MIGRATION_MANIFESTS["h3-editorial-expand"] == H3_PRO_MIGRATIONS
    assert resolve_requested_migrations(h3_args, parser) == H3_PRO_MIGRATIONS

    invalid_args = (
        SimpleNamespace(env="pro", manifest="../all", only=[]),
        SimpleNamespace(env="pro", manifest=None, only=[]),
        SimpleNamespace(env="pro", manifest="h3-editorial-expand", only=["20261028_h3_editorial_publication_snapshot"]),
        SimpleNamespace(env="free", manifest="h3-editorial-expand", only=[]),
    )
    for args in invalid_args:
        with pytest.raises(SystemExit):
            resolve_requested_migrations(args, parser)


def test_h3_manifest_declares_and_obeys_non_lexical_dependency_edges() -> None:
    positions = {name: index for index, name in enumerate(H3_PRO_MIGRATIONS)}
    assert len(H3_PRO_MIGRATION_PRECEDENCE) == 5
    for prerequisite, dependent in H3_PRO_MIGRATION_PRECEDENCE:
        assert positions[prerequisite] < positions[dependent]


def test_h3_manifest_rejects_missing_or_changed_sql_bytes(tmp_path: Path) -> None:
    for name in H3_PRO_MIGRATIONS:
        shutil.copyfile(MIGRATIONS / f"{name}.sql", tmp_path / f"{name}.sql")
    validate_h3_manifest_tree(tmp_path)

    target = tmp_path / f"{H3_PRO_MIGRATIONS[0]}.sql"
    target.write_bytes(target.read_bytes() + b"\n-- drift\n")
    with pytest.raises(ValueError, match="hash mismatch"):
        validate_h3_manifest_tree(tmp_path)

    target.unlink()
    with pytest.raises(ValueError, match="missing from pinned manifest"):
        validate_h3_manifest_tree(tmp_path)


def test_h3_h2_compatibility_inputs_accept_aggregates_and_reject_invalid_values() -> None:
    digest = "sha256:" + "a" * 64
    assert validate_h2_cohort_inputs("224", digest) == (224, digest)
    for count, candidate_digest in (
        ("", digest),
        ("0", digest),
        ("-1", digest),
        ("224", "sha256:" + "A" * 64),
        ("224", "sha256:short"),
    ):
        with pytest.raises(ValueError):
            validate_h2_cohort_inputs(count, candidate_digest)
