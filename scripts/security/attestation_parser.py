#!/usr/bin/env python3
"""Section-aware PR attestation parsing helpers."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class AttestationSection:
    present: bool
    duplicate_section: bool = False
    fields: dict[str, str] = field(default_factory=dict)
    unknown_fields: dict[str, str] = field(default_factory=dict)
    duplicates: tuple[str, ...] = ()

    def nonempty_fields(self) -> dict[str, str]:
        values = {key: value for key, value in self.fields.items() if value.strip()}
        values.update({key: value for key, value in self.unknown_fields.items() if value.strip()})
        return values


def parse_attestation_section(body: str, heading: str, allowed_fields: tuple[str, ...]) -> AttestationSection:
    """Parse only the exact H2 attestation section and fail closed on ambiguity."""
    section_heading = f"## {heading}"
    in_section = False
    found = 0
    fields: dict[str, str] = {}
    unknown_fields: dict[str, str] = {}
    duplicates: list[str] = []
    in_fence = False

    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            if in_section:
                continue
        if in_fence:
            continue
        if stripped.startswith("## "):
            if stripped == section_heading:
                found += 1
                in_section = True
                continue
            if in_section:
                in_section = False
        if not in_section or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        if key not in allowed_fields:
            unknown_fields[key] = value.strip()
            continue
        if key in fields and key not in duplicates:
            duplicates.append(key)
        fields[key] = value.strip()

    return AttestationSection(
        present=found > 0,
        duplicate_section=found > 1,
        fields=fields,
        unknown_fields=unknown_fields,
        duplicates=tuple(duplicates),
    )
