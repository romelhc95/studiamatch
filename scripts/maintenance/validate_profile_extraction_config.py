"""
Fase 121 — valida configuracion JSONB de extraccion por perfil.

No ejecuta selectores contra sitios externos. Solo valida estructura, allowlist de
transforms y limites defensivos para evitar payloads peligrosos.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.shared.db_client import get_db_client


ALLOWED_TRANSFORMS = {
    "text",
    "html_to_text",
    "absolute_url",
    "normalize_mode",
    "price_to_float",
    "accordion_to_bullets",
    "derive_from_duration_text",
}

MAX_SELECTOR_LEN = 500
MAX_RULES = 50


def _as_dict(value):
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def _as_list(value):
    if isinstance(value, list):
        return value
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            return []
    return []


def _validate_selector_spec(spec, path, errors):
    if isinstance(spec, str):
        selector = spec
        transform = "text"
    elif isinstance(spec, dict):
        selector = spec.get("selector") or spec.get("container")
        transform = spec.get("transform", "text")
        value_selector = spec.get("value_selector")
        if value_selector and (not isinstance(value_selector, str) or len(value_selector) > MAX_SELECTOR_LEN):
            errors.append(f"{path}.value_selector invalido o demasiado largo")
    else:
        errors.append(f"{path} debe ser string u objeto")
        return
    if selector is not None and (not isinstance(selector, str) or len(selector) > MAX_SELECTOR_LEN):
        errors.append(f"{path}.selector/container invalido o demasiado largo")
    if isinstance(selector, str):
        normalized = selector.strip().replace(" ", "")
        if normalized == "*" or normalized.startswith("*,") or ",*" in normalized:
            errors.append(f"{path}.selector demasiado amplio: {selector}")
        if selector.count(",") > 5:
            errors.append(f"{path}.selector tiene demasiados selectores combinados")
        if any(token in selector.lower() for token in (":contains", ":has(", ":not(", ">>")):
            errors.append(f"{path}.selector usa pseudo-selector no permitido: {selector}")
    if transform not in ALLOWED_TRANSFORMS:
        errors.append(f"{path}.transform no permitido: {transform}")


def validate_profile(profile):
    errors = []
    field_selectors = _as_dict(profile.get("field_selectors"))
    label_selectors = _as_dict(profile.get("label_selectors"))
    url_type_rules = _as_list(profile.get("url_type_rules"))
    extraction_transforms = _as_dict(profile.get("extraction_transforms"))

    if len(field_selectors) > MAX_RULES:
        errors.append("field_selectors excede limite de reglas")
    if len(label_selectors) > MAX_RULES:
        errors.append("label_selectors excede limite de reglas")
    if len(url_type_rules) > MAX_RULES:
        errors.append("url_type_rules excede limite de reglas")

    for field, spec in field_selectors.items():
        _validate_selector_spec(spec, f"field_selectors.{field}", errors)
    for label, spec in label_selectors.items():
        if not isinstance(spec, dict):
            errors.append(f"label_selectors.{label} debe ser objeto")
            continue
        if not spec.get("field"):
            errors.append(f"label_selectors.{label}.field requerido")
        _validate_selector_spec(spec, f"label_selectors.{label}", errors)

    for idx, rule in enumerate(url_type_rules):
        if not isinstance(rule, dict):
            errors.append(f"url_type_rules[{idx}] debe ser objeto")
            continue
        match = rule.get("match")
        if not isinstance(match, str) or not match.strip() or len(match) > MAX_SELECTOR_LEN:
            errors.append(f"url_type_rules[{idx}].match requerido o demasiado largo")
        if isinstance(match, str) and match.startswith("re:"):
            errors.append(f"url_type_rules[{idx}].match no permite regex dinamico")
        for field, spec in _as_dict(rule.get("field_overrides")).items():
            _validate_selector_spec(spec, f"url_type_rules[{idx}].field_overrides.{field}", errors)
        for label, spec in _as_dict(rule.get("label_overrides")).items():
            if not isinstance(spec, dict):
                errors.append(f"url_type_rules[{idx}].label_overrides.{label} debe ser objeto")
                continue
            _validate_selector_spec(spec, f"url_type_rules[{idx}].label_overrides.{label}", errors)

    for field, transform in extraction_transforms.items():
        if transform not in ALLOWED_TRANSFORMS:
            errors.append(f"extraction_transforms.{field} no permitido: {transform}")

    return errors


def main():
    db = get_db_client()
    profiles = db.select_pipeline(
        "institution_site_profiles",
        columns="institution_id,field_selectors,label_selectors,url_type_rules,extraction_transforms,extraction_confidence",
    ) or []
    failures = 0
    for profile in profiles:
        errors = validate_profile(profile)
        if errors:
            failures += 1
            print(f"Perfil {profile.get('institution_id')} invalido:")
            for error in errors:
                print(f"  - {error}")
    if failures:
        sys.exit(1)
    print(f"OK: {len(profiles)} perfiles validos")


if __name__ == "__main__":
    main()
