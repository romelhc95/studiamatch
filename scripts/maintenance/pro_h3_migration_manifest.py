"""Pinned, closed H3 Pro migration selection used by the existing DB Sync flow."""

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
    "20261002_h3_admin_quota_expand": "d839f7f760bdb12025297a24e09b547cf4f0b5989d3c0142835978083be9bb67",
    "20261002_h3_admin_quotas": "7ea746ca73f2acee31956e59d490083c4fbfcaebf51941d4c6cb52618c906619",
    "20261004_h3_admin_queue_first_null_guard": "012f994af8b44353e385e68b22dc1b15535e31f47f8f990716cbd726f1908711",
    "20261004_h3_admin_rpc_signed_gateway_expand": "e80e236348c2eefe79035c6f6ea5e22bc5dea194555d07a1f1b5a8b41a02876c",
    "20261004_h3_admin_rpc_signed_gateway_payload_bound_wrapper": "c8a69e06e2d1d3a7f5e2245f6fb68ac6220deac3fd0b273edb5bcedafdba81a5",
    "20261010_h3_admin_members_service_select": "6a4d4476e5143537b51390becfe995ca5cb9340ed891c1232e7af2cb1cb9e49c",
    "20261025_h3_admin_members_onboarding_forbidden_status": "11c46cebb640cc6e015926ac7ab6120ca9f0180e43e451909a94ea316960502d",
    "20261028_h3_editorial_publication_snapshot": "2c2bd2238f03a1b5bec2d47fb4bc8a9f0fe1650501378a8ff2dde8746b2a0fef",
    "20261028_h3_public_price_projection_empty_price_guard": "82b8eb0655779f0e82b979cb65a051f2b244b5c4bffb199c5e13c9473132987b",
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
