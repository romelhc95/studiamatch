"""Shared local truth table for F9.7 notify trigger retirement v3."""

from __future__ import annotations

from dataclasses import dataclass


PROJECT_REF_LENGTH = 20
PROJECT_REF_GRAMMAR = rf"[a-z0-9]{{{PROJECT_REF_LENGTH}}}"
PROJECT_REF_URL_PATTERN = (
    rf"https://{PROJECT_REF_GRAMMAR}[.]"
    rf"supabase[.]co/functions/v1/send-lead-emails"
)
PROJECT_REF_URL_REDACTION = "https://<project-ref>.supabase.co/functions/v1/send-lead-emails"


@dataclass(frozen=True)
class NotifyVariant:
    name: str
    prosrc_lf_octets: int
    definition_lf_octets: int | None
    prosrc_lf_sha256: str | None = None
    prosrc_normalized_sha256: str | None = None
    definition_lf_sha256: str | None = None
    definition_normalized_sha256: str | None = None
    prosrc_redacted_sha256: str | None = None
    prosrc_normalized_redacted_sha256: str | None = None
    definition_redacted_sha256: str | None = None
    definition_normalized_redacted_sha256: str | None = None


NOTIFY_VARIANTS: tuple[NotifyVariant, ...] = (
    NotifyVariant(
        name="secure_trigger_exact",
        prosrc_lf_octets=1251,
        definition_lf_octets=1423,
        prosrc_lf_sha256="5fa712326d4c331c074caabafc8957dc4edd3e85404ad31ad0f5f7304fc6b32e",
        prosrc_normalized_sha256="42dab6c9e511e61ad04f8dbd8bccf070e23b598d6877de1dd27865b4b2734ccc",
        definition_lf_sha256="c05c403dc06c7a03379591de7bc729f6aa15366566aa5dcf6a00de2e7f3e0d12",
        definition_normalized_sha256="7844c0c19a151091d05ba33800013edc4709125725221bd313e59363f647d020",
    ),
    NotifyVariant(
        name="secure_trigger_project_ref_redacted",
        prosrc_lf_octets=1251,
        definition_lf_octets=None,
        prosrc_redacted_sha256="b0b03f57d6d6416f71cebc3fded4e715fbb34867c35c5616d9c6cb561e0ecd8c",
        prosrc_normalized_redacted_sha256="57b2644f3c023f18d10f696459704195d24a0c2cca2b3b5bdb9895b21d4a829c",
        definition_redacted_sha256="1f81d3a05c5b01dc459bb59a92ece636d34c490c681db3a82ce8ba67c6e99774",
        definition_normalized_redacted_sha256="d1b5dba4a69b44926db4906401099603d0a511858f0d599d41ad18ceb683de56",
    ),
    NotifyVariant(
        name="email_infrastructure_exact",
        prosrc_lf_octets=954,
        definition_lf_octets=1126,
        prosrc_lf_sha256="e802821baeabb39968b37529d14d889296b65bf34bdfce41dc0639f57f75bcf9",
        prosrc_normalized_sha256="79ac9190efc739367216aec867aa2119afa3085892aa2a9092fb080d83b9b753",
        definition_lf_sha256="e23bf811d4c0f288a8e6d58fb1edcf8571c0348c8cc8697cbe4458dc76642164",
        definition_normalized_sha256="04ef62b7aaea62d2653b8971114624829ba08a13c09eb3e4f4340b09e094ddc4",
    ),
)

NOTIFY_VARIANTS_BY_NAME = {variant.name: variant for variant in NOTIFY_VARIANTS}
