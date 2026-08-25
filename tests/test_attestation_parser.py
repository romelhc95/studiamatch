from scripts.security.attestation_parser import parse_attestation_section


FIELDS = ("Base-SHA", "Candidate-SHA", "Approval-Level", "Approval-Expiry")


def test_exact_section_ignores_empty_other_section_duplicates() -> None:
    body = """## Governance Attestation
Base-SHA: a
Candidate-SHA: b
Approval-Level: R2
Approval-Expiry: 2026-09-04T23:59:59Z

## Promotion Attestation
Base-SHA:
Candidate-SHA:
Approval-Level:
Approval-Expiry:
"""
    section = parse_attestation_section(body, "Governance Attestation", FIELDS)
    assert section.present is True
    assert section.duplicate_section is False
    assert section.duplicates == ()
    assert section.fields["Base-SHA"] == "a"


def test_duplicate_within_applicable_section_is_reported() -> None:
    body = """## Promotion Attestation
Base-SHA: a
Base-SHA: b
"""
    section = parse_attestation_section(body, "Promotion Attestation", FIELDS)
    assert section.duplicates == ("Base-SHA",)
    assert section.fields["Base-SHA"] == "b"


def test_missing_or_malformed_heading_does_not_fallback_to_body() -> None:
    body = """### Promotion Attestation
Base-SHA: a
Candidate-SHA: b
"""
    section = parse_attestation_section(body, "Promotion Attestation", FIELDS)
    assert section.present is False
    assert section.fields == {}


def test_repeated_section_heading_is_ambiguous() -> None:
    body = """## Promotion Attestation
Base-SHA: a

## Promotion Attestation
Candidate-SHA: b
"""
    section = parse_attestation_section(body, "Promotion Attestation", FIELDS)
    assert section.duplicate_section is True


def test_fenced_block_fields_are_ignored() -> None:
    body = """## Promotion Attestation
```
Base-SHA: a
```
Candidate-SHA: b
"""
    section = parse_attestation_section(body, "Promotion Attestation", FIELDS)
    assert "Base-SHA" not in section.fields
    assert section.fields["Candidate-SHA"] == "b"


def test_unknown_key_value_lines_are_preserved_for_inactive_section_checks() -> None:
    body = """## Promotion Attestation
Unexpected-Key: populated
"""
    section = parse_attestation_section(body, "Promotion Attestation", FIELDS)
    assert section.unknown_fields == {"Unexpected-Key": "populated"}
    assert section.nonempty_fields()["Unexpected-Key"] == "populated"
