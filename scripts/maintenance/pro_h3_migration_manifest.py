"""Pinned, closed H3 Pro migration selection used by the existing DB Sync flow.

StudIAMatch-Docs: .context/componentes/database_migrations.md#h3-pro-promotion-manifest
"""

from __future__ import annotations

import hashlib
from pathlib import Path


H3_PRO_MANIFEST_NAME = "h3-editorial-expand"

H3_PRO_MIGRATIONS = (
    "20260828_h3_admin_auth",
    "20260828_h3_admin_course_queue_view",
    "20260828_h3_admin_editorial_reader_rpc",
    "20260828_h3_admin_editorial_rpc",
    "20260828_h3_admin_queue_rpc",
    "20260829_h3_rbac_users",
    "20260830_h3_expanded_contract",
    "20260902_h3_pr_contract",
    "20260903_h3_rbac_contract_fix",
    "20260918_h3_invitation_flow_persistence",
    "20260919_h3_invitation_auth_token_delta",
    "20260920_h3_invitation_edge_runtime",
    "20260921_h3_invitation_onboarding_rpc",
    "20260924_h3_onboarding_rbac_hardening",
    "20260924_h3_onboarding_rbac_hardening_fix",
    "20260925_h3_admin_members_onboarding_reader",
    "20260925_h3_legacy_member_creation_guard",
    "20260927_h3_admin_queue_facets_filter",
    "20260927_h3_publication_visibility_contract",
    "20260928_h3_invitation_accept_email_regex_fix",
    "20261001_h3_course_editorial_audit_availability",
    "20261001_h3_invitation_reservation_compensation",
    "20261002_h3_admin_quota_expand",
    "20261002_h3_admin_quotas",
    "20261004_h3_admin_queue_first_null_guard",
    "20261004_h3_admin_rpc_signed_gateway_expand",
    "20261004_h3_admin_rpc_signed_gateway_payload_bound_wrapper",
    "20261010_h3_admin_members_service_select",
    "20261025_h3_admin_members_onboarding_forbidden_status",
    "20261028_h3_editorial_publication_snapshot",
    "20261028_h3_public_price_projection_empty_price_guard",
    "20261102_h3_legacy_public_withdrawal_guard",
    "20261105_h3_first_admin_auth_bootstrap",
)

H3_PRO_MIGRATION_SHA256 = {
    "20260828_h3_admin_auth": "9a962d01cb3969f6442cac44e3947e7591e93015c4383d245fb3d1f9a1beb314",
    "20260828_h3_admin_course_queue_view": "96f2ffffdbae1ea3f85ff32ade1a2987821c9e837dd771e1a188165cf377caf9",
    "20260828_h3_admin_editorial_reader_rpc": "2783ad358c035db03456b8934e2fa598a4af8272d3715404a8d3c00189e3b63b",
    "20260828_h3_admin_editorial_rpc": "ee8d5b1458da1291ec8b1e4f943728af82cd3cef42a5aee36d490ef8cbda9726",
    "20260828_h3_admin_queue_rpc": "e4fd2ff6733667520916d136eb5d657778c27e5f291e74613a02a595c4bbfb0c",
    "20260829_h3_rbac_users": "b1f96c366f506d52ce11fcf6ef64759ba543af63304da124af0dc10b21fd24c7",
    "20260830_h3_expanded_contract": "387c6247976e92dcbaeff3b53ffa59a9f3f989dd8a50ded1ff61df4721769e27",
    "20260902_h3_pr_contract": "6c22319a66c10e323a6fa4ed1fdbd612a609f8057c6e952a8601cb17c46a4e74",
    "20260903_h3_rbac_contract_fix": "4274e114882fae1deb3039036c612bdc682d59921833c297ed691e87c0440797",
    "20260918_h3_invitation_flow_persistence": "0837d448d8552feb62bb3ab63701123e2449a00ffdcc84dc776849e879030f77",
    "20260919_h3_invitation_auth_token_delta": "701f5c74ff923765fb39efa1605600cb58c93c8caa820b7d49a17fba73e8275d",
    "20260920_h3_invitation_edge_runtime": "46f7d24ac9c8af033ebd84b9ede44c27241382b9cba3fe179ec745b9a25f9188",
    "20260921_h3_invitation_onboarding_rpc": "138e2d3690ec880c51f3834e42fa33ebce0080c6ad9e08b5fe34b8df76de84f2",
    "20260924_h3_onboarding_rbac_hardening": "e466bf1f7968d71ce715724779cc4bd37818f6462021724d01ad48a9bfb1a857",
    "20260924_h3_onboarding_rbac_hardening_fix": "9a5c5d46bca6b4dec438bc6ae63036641423fee95b73e188237ef8ba230b2978",
    "20260925_h3_admin_members_onboarding_reader": "0a9a0b5b694b9caef66da5f6e0d5a45d77bff9029e31b0ede54a5026c14a9d0d",
    "20260925_h3_legacy_member_creation_guard": "bf7b240d76452105753883523428f6cfa4448bdb96c880b2f4aca467db0fe678",
    "20260927_h3_admin_queue_facets_filter": "efabbb35e5fc8b9dc28ce3159ed3ed2328f20c74e4d8e02d2a1a222e8351600b",
    "20260927_h3_publication_visibility_contract": "2b02df3f9ab5736da292d5b8653ca567111cd82705ada182b5baa8085b21e1aa",
    "20260928_h3_invitation_accept_email_regex_fix": "a1b9eaa799d7cc760c84e1df2f66b362ebf1b0556a9f446222f2f9cbea99cd44",
    "20261001_h3_course_editorial_audit_availability": "14e47f4ab4a50382bbea8453b84295bcb2f707e760c8c0a9ae5da4c1f71c3097",
    "20261001_h3_invitation_reservation_compensation": "1001c059b951eaa907016e31be08bef9f3e0a7835f30ea2cac5227a123927270",
    "20261002_h3_admin_quota_expand": "68016d250bfc9ab6fc83cd2c2123a4fcefbbad87732eb1807364b5129facbfad",
    "20261002_h3_admin_quotas": "99cf11b5cac339f5382a5c49d4fd2a5d0439700938a4d78308f57a1a8f8f523e",
    "20261004_h3_admin_queue_first_null_guard": "912b28d476b8bef3246c88c895ed275b85477f57ba15efa47b435c344c778175",
    "20261004_h3_admin_rpc_signed_gateway_expand": "0d20f15140014dd9fe887b95003d4e00b153abad044d5823ec212e24d83ea16e",
    "20261004_h3_admin_rpc_signed_gateway_payload_bound_wrapper": "d708e9de4c3c9c53a72b3f3c189aded683ba3013cb1f63dc6564a7fa6e19f8cc",
    "20261010_h3_admin_members_service_select": "6a4d4476e5143537b51390becfe995ca5cb9340ed891c1232e7af2cb1cb9e49c",
    "20261025_h3_admin_members_onboarding_forbidden_status": "37c14b6d5bc2ca39bbc0487c9c34fca794ab34e5ee024a94df5236e70bd70a7e",
    "20261028_h3_editorial_publication_snapshot": "2c2bd2238f03a1b5bec2d47fb4bc8a9f0fe1650501378a8ff2dde8746b2a0fef",
    "20261028_h3_public_price_projection_empty_price_guard": "82b8eb0655779f0e82b979cb65a051f2b244b5c4bffb199c5e13c9473132987b",
    "20261102_h3_legacy_public_withdrawal_guard": "a719310811dd9b5a992f4a0002931b4a6c9f6a84aac2f84cdd217daead97a7b6",
    "20261105_h3_first_admin_auth_bootstrap": "67045f02b2eb2c846295207b249b5b9014fe50610e162fe7fac4b40c8b7d62d6",
}

# Explicit non-lexical dependencies. The complete ordered list is also pinned above.
H3_PRO_MIGRATION_PRECEDENCE = (
    ("20260828_h3_admin_auth", "20260829_h3_rbac_users"),
    ("20260829_h3_rbac_users", "20260830_h3_expanded_contract"),
    ("20261002_h3_admin_quota_expand", "20261002_h3_admin_quotas"),
    (
        "20261004_h3_admin_rpc_signed_gateway_expand",
        "20261004_h3_admin_rpc_signed_gateway_payload_bound_wrapper",
    ),
    (
        "20261028_h3_editorial_publication_snapshot",
        "20261028_h3_public_price_projection_empty_price_guard",
    ),
    (
        "20261028_h3_public_price_projection_empty_price_guard",
        "20261102_h3_legacy_public_withdrawal_guard",
    ),
    (
        "20261001_h3_invitation_reservation_compensation",
        "20261105_h3_first_admin_auth_bootstrap",
    ),
)

H3_PRO_EXTERNAL_PREREQUISITE = (
    "H2 expand/compatibility reader independently verified against the exact Pro cohort; "
    "H2 migrations are intentionally not included in this manifest."
)


# Shared by the runtime migrator and the dependency-free workflow preflight.
# Importing this registry never loads database clients, environment files or keys.
PRO_MIGRATION_MANIFESTS = {
    "f10-8-atomic-cleansing-provenance": (
        "20260808_fase10_8_atomic_cleansing_provenance",
    ),
    "h2-expand-compat": (
        "20260827_h2_pro_expand_schema_compat",
        "20260827_h2_pro_seed_editorial_field_definitions",
        "20260827_h2_pro_backfill_editorial_state",
        "20260827_h2_pro_capture_legacy_cohort",
        "20260827_h2_pro_enable_legacy_cohort_rls",
    ),
    "h2-contract-public-reader": (
        "20260827_h2_pro_contract_public_reader",
    ),
    "h2-contract-legacy-cohort": (
        "20260827_h2_pro_contract_legacy_cohort",
    ),
    "h2-rollback-public-reader-contract": (
        "20260827_h2_pro_rollback_public_reader_contract",
    ),
    H3_PRO_MANIFEST_NAME: H3_PRO_MIGRATIONS,
}


def validate_h3_manifest_names(names: tuple[str, ...] | list[str]) -> None:
    selected = tuple(names)
    if selected != H3_PRO_MIGRATIONS:
        raise ValueError("H3 Pro manifest selection differs from its pinned ordered inventory")
    if set(H3_PRO_MIGRATION_SHA256) != set(H3_PRO_MIGRATIONS):
        raise ValueError("H3 Pro migration SHA inventory does not match the manifest")
    positions = {name: index for index, name in enumerate(selected)}
    for prerequisite, dependent in H3_PRO_MIGRATION_PRECEDENCE:
        if prerequisite not in positions or dependent not in positions:
            raise ValueError("H3 Pro migration dependency is outside the pinned manifest")
        if positions[prerequisite] >= positions[dependent]:
            raise ValueError(f"H3 Pro migration dependency order invalid: {prerequisite} before {dependent}")


def validate_h3_manifest_tree(migrations_dir: str | Path) -> dict[str, str]:
    """Fail closed unless every pinned SQL file exists byte-identically."""
    validate_h3_manifest_names(H3_PRO_MIGRATIONS)
    root = Path(migrations_dir)
    actual: dict[str, str] = {}
    for name in H3_PRO_MIGRATIONS:
        path = root / f"{name}.sql"
        if not path.is_file():
            raise ValueError(f"H3 Pro migration missing from pinned manifest: {name}")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != H3_PRO_MIGRATION_SHA256[name]:
            raise ValueError(f"H3 Pro migration hash mismatch: {name}")
        actual[name] = digest
    return actual


def validate_h2_cohort_inputs(expected_count: str, expected_digest: str) -> tuple[int, str]:
    """Validate aggregate-only H2 compatibility inputs consumed by H3 preflight."""
    import re

    if not expected_count.isdigit() or int(expected_count) <= 0:
        raise ValueError("H2 expected cohort count must be a positive integer")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", expected_digest):
        raise ValueError("H2 expected cohort digest must use sha256:<64 lowercase hex chars>")
    return int(expected_count), expected_digest
