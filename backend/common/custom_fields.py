"""Custom-field metadata + validation.

The CustomFieldDefinition model in common/models.py stores schema rows; this
module is the cross-cutting validator everyone uses to coerce/check values
before persisting them on an entity's `custom_fields` JSONField.

See docs/cases/tier1/custom-fields.md and docs/cases/COORDINATION_DECISIONS.md.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

from rest_framework import serializers as drf_serializers

logger = logging.getLogger(__name__)

# Targets whose entity model has a `custom_fields` JSONField column. Adding a
# new entity? Drop a column on it (one migration), then add it here.
SUPPORTED_TARGETS: set[str] = {
    "Account",
    "Case",
    "Contact",
    "Estimate",
    "Invoice",
    "Lead",
    "Opportunity",
    "RecurringInvoice",
    "Task",
}


def is_supported_target(target_model: str) -> bool:
    return target_model in SUPPORTED_TARGETS


def validate_definition_options(field_type: str, options: Any) -> None:
    """Raise serializers.ValidationError for malformed dropdown options."""
    if field_type != "dropdown":
        if options not in (None, [], {}):
            raise drf_serializers.ValidationError(
                {"options": "options is only valid for dropdown fields"}
            )
        return

    if not isinstance(options, list) or not options:
        raise drf_serializers.ValidationError(
            {"options": "Dropdown fields require a non-empty list of {value, label} pairs"}
        )

    seen: set[str] = set()
    for idx, entry in enumerate(options):
        if not isinstance(entry, dict):
            raise drf_serializers.ValidationError(
                {"options": f"Entry {idx} must be an object with value and label"}
            )
        value = entry.get("value")
        label = entry.get("label")
        if not isinstance(value, str) or not value:
            raise drf_serializers.ValidationError(
                {"options": f"Entry {idx} is missing a non-empty string value"}
            )
        if not isinstance(label, str) or not label:
            raise drf_serializers.ValidationError(
                {"options": f"Entry {idx} is missing a non-empty string label"}
            )
        if value in seen:
            raise drf_serializers.ValidationError(
                {"options": f"Duplicate dropdown value: {value!r}"}
            )
        seen.add(value)


def _coerce_value(field_type: str, raw: Any):
    """Coerce a raw input to the expected python/JSON type. Returns (value, error_or_None)."""
    if raw is None or raw == "":
        return None, None

    if field_type in ("text", "textarea"):
        return str(raw), None

    if field_type == "number":
        try:
            if isinstance(raw, bool):
                raise ValueError
            if isinstance(raw, (int, float)):
                return float(raw), None
            return float(str(raw)), None
        except (TypeError, ValueError):
            return None, "must be a number"

    if field_type == "checkbox":
        if isinstance(raw, bool):
            return raw, None
        if isinstance(raw, str):
            lowered = raw.strip().lower()
            if lowered in ("true", "1", "yes", "on"):
                return True, None
            if lowered in ("false", "0", "no", "off"):
                return False, None
        return None, "must be a boolean"

    if field_type == "date":
        if isinstance(raw, date):
            return raw.isoformat(), None
        if isinstance(raw, str):
            try:
                return date.fromisoformat(raw).isoformat(), None
            except ValueError:
                return None, "must be a YYYY-MM-DD date"
        return None, "must be a YYYY-MM-DD date"

    if field_type == "dropdown":
        return str(raw), None

    return None, f"unsupported field_type {field_type!r}"


def validate_payload(
    target_model: str,
    value_dict: Any,
    org,
    *,
    existing: dict | None = None,
) -> tuple[dict, dict]:
    """Validate and coerce a custom_fields payload for an entity.

    Returns (cleaned_dict, errors_dict). Non-empty errors -> caller should 400.
    Unknown keys are dropped silently and logged. `existing` is the value
    currently stored on the entity — required fields already set on the entity
    are preserved across PATCHes that omit them.

    Values tied to soft-deleted (is_active=False) definitions are carried
    forward on save so admins can soft-delete a field without losing history,
    but new writes against an inactive key are rejected as unknown.
    """
    from common.models import CustomFieldDefinition  # avoid import cycle

    if value_dict is None:
        value_dict = {}
    if not isinstance(value_dict, dict):
        return {}, {"custom_fields": "must be an object"}

    existing = existing or {}

    all_definitions = list(
        CustomFieldDefinition.objects.filter(org=org, target_model=target_model)
    )
    all_keys = {d.key for d in all_definitions}
    active_by_key = {d.key: d for d in all_definitions if d.is_active}

    cleaned: dict = {}
    errors: dict = {}

    # Carry forward existing recognized values (active OR soft-deleted) that
    # the caller didn't touch. Values whose definition was hard-deleted are
    # dropped — the schema is gone.
    for key, value in existing.items():
        if key in all_keys and key not in value_dict:
            cleaned[key] = value

    for key, raw in value_dict.items():
        defn = active_by_key.get(key)
        if defn is None:
            logger.info(
                "custom_fields: dropping unknown key %r on %s for org %s",
                key,
                target_model,
                getattr(org, "id", org),
            )
            continue
        coerced, error = _coerce_value(defn.field_type, raw)
        if error:
            errors[key] = error
            continue
        if coerced is None or coerced == "":
            cleaned.pop(key, None)
            continue
        if defn.field_type == "dropdown":
            allowed = {opt.get("value") for opt in (defn.options or [])}
            if coerced not in allowed:
                errors[key] = f"must be one of {sorted(allowed)}"
                continue
        cleaned[key] = coerced

    # Required fields: error if neither a new value nor an existing one is set.
    for defn in active_by_key.values():
        if not defn.is_required:
            continue
        present = cleaned.get(defn.key) not in (None, "")
        if not present:
            errors.setdefault(defn.key, "is required")

    return cleaned, errors
