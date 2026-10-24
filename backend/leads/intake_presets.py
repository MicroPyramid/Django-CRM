"""How a post to a lead webhook is read.

Each preset is a starting mapping plus where its sender puts its own lead id,
test flag, timestamp and key. A mapping row is ``{"from": <dot path>, "to":
<target>}``; a target is a lead column by the web forms' whitelist name, or
``custom_fields.<key>``. A dot path walks the posted body. At a list, a segment
picks the first item whose ``column_id``, ``key``, ``label``, ``name`` or
``type`` equals it (any case) and reads the item's ``string_value`` or
``value``, which is how Google Ads and Tally list their answers. A key that
itself holds dots (``1.3``, a Gravity Forms input) is matched whole first.

Top-level keys named like a lead column (``email``, ``first_name``) fill that
column when no row already did, so a sender that uses our names needs no
mapping. Whatever the mapping does not use is written into the enquiry text,
so nothing the person typed is lost. Payload formats are documented in
``docs/features/lead-capture.md``.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime

from django.utils.dateparse import parse_datetime
from rest_framework import serializers

from common.custom_fields import validate_payload
from common.models import CustomFieldDefinition
from common.validators import flexible_phone_validator
from leads.sources import source_keys
from webforms.constants import (
    LEAD_FIELD_CHOICE_SOURCES,
    LEAD_FIELD_CHOICES,
    LEAD_FIELD_MAX_LENGTHS,
    LEAD_FIELD_VALUES,
)

CUSTOM_PREFIX = "custom_fields."
MAPPING_MAX_ROWS = 50
PATH_MAX_LENGTH = 255
CUSTOM_VALUE_MAX = 1000
ENQUIRY_MAX = 20_000
_ITEM_NAMES = ("column_id", "key", "label", "name", "type")
COLUMN_LABELS = dict(LEAD_FIELD_CHOICES)


@dataclass(frozen=True)
class Preset:
    mapping: tuple = ()
    default_source: str = "web form"
    external_id: str | None = None
    occurred_at: str | None = None
    is_test: str | None = None
    source_ref: str | None = None
    # Where the key may travel besides `Authorization: Bearer` and `?key=`.
    key_field: str | None = None
    signature_header: str | None = None
    # The list holding the person's answers; None reads the whole body.
    answers: str | None = None
    # Top-level keys that describe the post, never what the person typed.
    metadata: frozenset = frozenset()


def _rows(*pairs):
    return tuple({"from": source, "to": target} for source, target in pairs)


# Google Ads lead form webhooks. FIRST_NAME before FULL_NAME, EMAIL before
# WORK_EMAIL: the first row that finds a value fills the column.
GOOGLE_ADS = Preset(
    mapping=_rows(
        ("user_column_data.FIRST_NAME", "first_name"),
        ("user_column_data.FULL_NAME", "first_name"),
        ("user_column_data.LAST_NAME", "last_name"),
        ("user_column_data.EMAIL", "email"),
        ("user_column_data.WORK_EMAIL", "email"),
        ("user_column_data.PHONE_NUMBER", "phone"),
        ("user_column_data.WORK_PHONE", "phone"),
        ("user_column_data.COMPANY_NAME", "company_name"),
        ("user_column_data.JOB_TITLE", "job_title"),
        ("user_column_data.CITY", "city"),
        ("user_column_data.REGION", "state"),
        ("user_column_data.POSTAL_CODE", "postcode"),
    ),
    default_source="google ads",
    external_id="lead_id",
    occurred_at="lead_submit_time",
    is_test="is_test",
    source_ref="campaign_id",
    key_field="google_key",
    answers="user_column_data",
)

# Tally `FORM_RESPONSE` events. Questions have form-specific keys, so the
# preset matches the email and phone question types and the usual labels.
TALLY = Preset(
    mapping=_rows(
        ("data.fields.INPUT_EMAIL", "email"),
        ("data.fields.INPUT_PHONE_NUMBER", "phone"),
        ("data.fields.First name", "first_name"),
        ("data.fields.Last name", "last_name"),
        ("data.fields.Full name", "first_name"),
        ("data.fields.Name", "first_name"),
        ("data.fields.Company", "company_name"),
        ("data.fields.Message", "description"),
    ),
    external_id="data.responseId",
    occurred_at="data.createdAt",
    source_ref="data.formId",
    signature_header="Tally-Signature",
    answers="data.fields",
)

# Gravity Forms webhooks sending all fields: inputs are keyed by field id,
# and a Name field's first and last inputs are `<id>.3` and `<id>.6`.
GRAVITY_FORMS = Preset(
    mapping=_rows(("1.2", "salutation"), ("1.3", "first_name"), ("1.6", "last_name")),
    external_id="id",
    occurred_at="date_created",
    source_ref="form_id",
    metadata=frozenset(
        {
            "id",
            "form_id",
            "post_id",
            "date_created",
            "date_updated",
            "is_starred",
            "is_read",
            "ip",
            "source_url",
            "user_agent",
            "currency",
            "payment_status",
            "payment_date",
            "payment_amount",
            "payment_method",
            "transaction_id",
            "is_fulfilled",
            "created_by",
            "transaction_type",
            "status",
        }
    ),
)

GENERIC = Preset(
    external_id="external_id",
    occurred_at="occurred_at",
    metadata=frozenset({"external_id", "occurred_at"}),
)

PRESETS = {
    "generic": GENERIC,
    "google_ads": GOOGLE_ADS,
    "tally": TALLY,
    "gravity_forms": GRAVITY_FORMS,
}


def preset_for(key) -> Preset:
    return PRESETS.get(key, GENERIC)


def default_mapping(preset_key) -> list[dict]:
    return [dict(row) for row in preset_for(preset_key).mapping]


def default_source(preset_key, org) -> str:
    """The preset's usual source while the org has it switched on, else none."""
    key = preset_for(preset_key).default_source
    return key if key in source_keys(org) else ""


def clean_mapping(rows, org, stored=None) -> list[dict]:
    """The mapping as stored, or a `ValidationError` naming the first bad row.

    A custom field target already stored passes after its field is switched
    off, because both clients resend the whole mapping on every save.
    """
    if not isinstance(rows, list):
        raise serializers.ValidationError("Send a list of {from, to} rows.")
    if len(rows) > MAPPING_MAX_ROWS:
        raise serializers.ValidationError(f"Use at most {MAPPING_MAX_ROWS} rows.")
    custom = set(
        CustomFieldDefinition.objects.filter(
            org=org, target_model="Lead", is_active=True
        ).values_list("key", flat=True)
    )
    custom |= {
        row["to"][len(CUSTOM_PREFIX) :]
        for row in stored or []
        if isinstance(row, dict)
        and isinstance(row.get("to"), str)
        and row["to"].startswith(CUSTOM_PREFIX)
    }
    cleaned = []
    for number, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise serializers.ValidationError(f"Row {number} is not a from, to pair.")
        source, target = row.get("from"), row.get("to")
        if (
            not isinstance(source, str)
            or not source.strip()
            or len(source) > PATH_MAX_LENGTH
        ):
            raise serializers.ValidationError(
                f"Row {number}: name the field in the post, up to "
                f"{PATH_MAX_LENGTH} characters."
            )
        if not isinstance(target, str) or not (
            target in LEAD_FIELD_VALUES
            or (
                target.startswith(CUSTOM_PREFIX)
                and target[len(CUSTOM_PREFIX) :] in custom
            )
        ):
            raise serializers.ValidationError(
                f"Row {number}: choose a lead field or one of your lead custom fields."
            )
        cleaned.append({"from": source.strip(), "to": target})
    return cleaned


@dataclass
class Reading:
    """One post, read through an intake's mapping and preset."""

    values: dict = field(default_factory=dict)
    custom_fields: dict = field(default_factory=dict)
    enquiry_text: str = ""
    external_id: str = ""
    occurred_at: datetime | None = None
    is_test: bool = False
    source_ref: str = ""
    errors: dict = field(default_factory=dict)


def read_post(intake, body) -> Reading:
    preset = preset_for(intake.preset)
    reading = Reading()
    columns, custom, used = {}, {}, []
    # The key a preset carries in the body never reaches a lead, whatever the
    # mapping says: members can read leads, and only admins may see the key.
    secret = (preset.key_field,) if preset.key_field else None

    for row in intake.mapping or []:
        if not isinstance(row, dict):
            continue
        target, path = row.get("to"), row.get("from")
        if not isinstance(target, str) or not isinstance(path, str):
            continue
        if target in LEAD_FIELD_VALUES:
            bucket, name = columns, target
        elif target.startswith(CUSTOM_PREFIX):
            bucket, name = custom, target[len(CUSTOM_PREFIX) :]
        else:
            continue
        if name in bucket:
            continue
        found = resolve(body, path)
        if found is None or _blank(found[0]) or isinstance(found[0], dict):
            continue
        if secret and found[1][:1] == secret:
            continue
        bucket[name] = found[0]
        used.append(found[1])

    for key, value in body.items():
        name = key.strip().lower().replace(" ", "_").replace("-", "_")
        if name in LEAD_FIELD_VALUES and name not in columns and not _blank(value):
            if not isinstance(value, dict):
                columns[name] = value
                used.append((key,))

    # Every lead gets in: a value too long for its column is cut to fit, and
    # kept whole in the enquiry text. A cut address or number would be wrong,
    # so those are left out of their column instead.
    kept_whole = []
    for name, value in columns.items():
        text = _choice(name, _as_text(value))
        limit = _limit(name)
        if len(text) > limit and name not in LEAD_FIELD_CHOICE_SOURCES:
            if name != "description":
                kept_whole.append(f"{COLUMN_LABELS[name]}: {text}")
            if name in ("email", "phone"):
                continue
            text = text[:limit]
        try:
            reading.values[name] = _column(name).run_validation(text)
        except serializers.ValidationError as exc:
            reading.errors[name] = exc.detail
    kept_whole += _read_custom(intake.org, custom, reading)

    reading.external_id = _as_text(_value_at(body, preset.external_id))[:255]
    reading.source_ref = _as_text(_value_at(body, preset.source_ref))[:255]
    reading.occurred_at = _when(_value_at(body, preset.occurred_at))
    flag = _value_at(body, preset.is_test)
    reading.is_test = flag is True or (
        isinstance(flag, str) and flag.strip().lower() == "true"
    )

    skip = preset.metadata | ({preset.key_field} if preset.key_field else set())
    extras = "\n".join(
        kept_whole
        + [
            f"{label}: {text}"
            for where, label, value in _answers(preset, body, skip)
            if not any(_overlaps(where, taken) for taken in used)
            and (text := _as_text(value))
        ]
    )
    message = reading.values.get("description", "")
    if message and extras:
        reading.values["description"] = f"{message}\n\n{extras}"[:ENQUIRY_MAX]
    reading.enquiry_text = (reading.values.get("description") or extras)[:ENQUIRY_MAX]
    return reading


def resolve(body, path):
    """``(value, location)`` for ``path`` in ``body``, or None. The location
    is the tuple of keys and indexes the walk took."""
    segments = path.split(".")
    node, where, i = body, (), 0
    while i < len(segments):
        if isinstance(node, dict):
            for end in range(len(segments), i, -1):
                key = ".".join(segments[i:end])
                if key in node:
                    node, where, i = node[key], (*where, key), end
                    break
            else:
                return None
        elif isinstance(node, list):
            segment = segments[i]
            if segment.isascii() and segment.isdigit():
                index = int(segment)
                if index >= len(node):
                    return None
                node, where = node[index], (*where, index)
            else:
                index = _item_named(node, segment)
                if index is None:
                    return None
                node, where = node[index], (*where, index)
                if i == len(segments) - 1:
                    node = _item_value(node)
            i += 1
        else:
            return None
    return node, where


def _item_named(items, segment):
    wanted = segment.strip().casefold()
    for index, item in enumerate(items):
        if isinstance(item, dict) and any(
            isinstance(item.get(name), str) and item[name].strip().casefold() == wanted
            for name in _ITEM_NAMES
        ):
            return index
    return None


def _item_value(item):
    value = item["string_value"] if "string_value" in item else item.get("value")
    options = item.get("options")
    if isinstance(options, list) and value is not None:
        texts = {
            str(option["id"]): option.get("text")
            for option in options
            if isinstance(option, dict) and "id" in option
        }
        if isinstance(value, list):
            value = [texts.get(str(v), v) for v in value]
        else:
            value = texts.get(str(value), value)
    return value


def _item_label(item):
    for name in ("column_name", "label", "name", "key", "column_id"):
        label = item.get(name)
        if isinstance(label, str) and label.strip():
            label = label.strip()
            if label.isupper() and " " not in label:
                label = label.replace("_", " ").capitalize()
            return label
    return "Answer"


def _answers(preset, body, skip):
    """``(location, label, value)`` for each thing the person answered."""
    if preset.answers:
        found = resolve(body, preset.answers)
        if found is None or not isinstance(found[0], list):
            return
        items, base = found
        for index, item in enumerate(items):
            if isinstance(item, dict):
                yield (*base, index), _item_label(item), _item_value(item)
        return
    yield from _leaves(body, (), skip)


def _leaves(node, where, skip):
    if isinstance(node, dict):
        for key, value in node.items():
            if not where and key in skip:
                continue
            yield from _leaves(value, (*where, key), skip)
    elif isinstance(node, list) and any(isinstance(v, dict | list) for v in node):
        for index, value in enumerate(node):
            yield from _leaves(value, (*where, index), skip)
    else:
        yield where, ".".join(str(part) for part in where), node


def _overlaps(a, b):
    shorter = min(len(a), len(b))
    return a[:shorter] == b[:shorter]


def _value_at(body, path):
    if not path:
        return None
    found = resolve(body, path)
    return None if found is None else found[0]


def _read_custom(org, custom, reading):
    """Validate the custom field half into `reading`; returns the
    `key: value` lines for values cut to fit."""
    submitted, kept_whole = {}, []
    for key, value in custom.items():
        value = value if isinstance(value, bool | int | float) else _as_text(value)
        if isinstance(value, str) and len(value) > CUSTOM_VALUE_MAX:
            kept_whole.append(f"{key}: {value}")
            value = value[:CUSTOM_VALUE_MAX]
        submitted[key] = value
    if not submitted:
        return kept_whole
    cleaned, errors = validate_payload("Lead", submitted, org)
    for key, message in errors.items():
        if key in submitted:
            reading.errors[CUSTOM_PREFIX + key] = [message]
    reading.custom_fields = {
        key: value
        for key, value in cleaned.items()
        if key in submitted and key not in errors
    }
    return kept_whole


def _limit(name):
    # The notes column has no limit of its own; the enquiry text's cap applies.
    if name == "description":
        return ENQUIRY_MAX
    return LEAD_FIELD_MAX_LENGTHS.get(name, 255)


def _column(name):
    if name == "email":
        return serializers.EmailField(max_length=LEAD_FIELD_MAX_LENGTHS["email"])
    if name == "phone":
        return serializers.CharField(
            max_length=LEAD_FIELD_MAX_LENGTHS["phone"],
            validators=[flexible_phone_validator],
        )
    choices = LEAD_FIELD_CHOICE_SOURCES.get(name)
    if choices is not None:
        return serializers.ChoiceField(choices=choices)
    return serializers.CharField(max_length=_limit(name))


def _choice(name, text):
    """A choice column takes its code or its label, in any case."""
    choices = LEAD_FIELD_CHOICE_SOURCES.get(name)
    if choices is None:
        return text
    folded = text.casefold()
    for code, label in choices:
        if folded in (str(code).casefold(), str(label).casefold()):
            return code
    return text


def _as_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, int | float):
        return str(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return ", ".join(text for text in map(_as_text, value) if text)
    if isinstance(value, dict):
        for name in ("name", "text", "url", "value"):
            if isinstance(value.get(name), str | int | float):
                return _as_text(value[name])
        return json.dumps(value, ensure_ascii=False)[:500]
    return str(value)


def _blank(value):
    return value is None or (isinstance(value, str | list) and not value)


def _when(value):
    if not isinstance(value, str):
        return None
    try:
        return parse_datetime(value.strip())
    except ValueError:
        return None
