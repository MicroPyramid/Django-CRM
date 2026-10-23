"""What a rule can see and change on each object, reached through the registry.

An entry offers rules an `Adapter` through `automation_adapter()`. Built-in
entries name theirs by dotted path in `ObjectEntry.automation`; an entry a
registry hook adds may be any object with that method. The field catalogue is
an allowlist in the style of `webhooks/events.py`: a field reaches rules only
by being listed, and a settable one is one its module's edit form writes.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework.exceptions import ValidationError

from common.models import CustomFieldDefinition, Profile
from common.modules import module_is_available
from common.object_registry import all_objects, object_for_key, object_module

FIELD_TYPES = ("text", "number", "date", "choice", "person", "people", "boolean")

CUSTOM_PREFIX = "custom_fields."

_CUSTOM_TYPES = {
    "text": "text",
    "textarea": "text",
    "number": "number",
    "date": "date",
    "dropdown": "choice",
    "checkbox": "boolean",
}


@dataclass(frozen=True)
class Choice:
    value: str
    label: str
    group: str = ""
    settable: bool = True


@dataclass(frozen=True)
class FieldSpec:
    key: str
    label: str
    type: str
    choices: tuple[Choice, ...] = ()
    settable: bool = True


def model_choices(model, field, *, unsettable=()):
    """The model field's choices; `unsettable` values are offered but not set."""
    return tuple(
        Choice(str(value), str(label).strip(), settable=value not in unsettable)
        for value, label in model._meta.get_field(field).flatchoices
    )


def custom_field_specs(org, target):
    specs = []
    for definition in CustomFieldDefinition.objects.filter(
        org=org, target_model=target, is_active=True
    ):
        kind = _CUSTOM_TYPES.get(definition.field_type)
        if kind is None:
            continue
        choices = ()
        if kind == "choice":
            choices = tuple(
                Choice(str(option["value"]), str(option["label"]))
                for option in definition.options or ()
            )
        specs.append(
            FieldSpec(CUSTOM_PREFIX + definition.key, definition.label, kind, choices)
        )
    return specs


def _plain(value):
    """A stored value in the shape rules compare: see `Adapter.read`."""
    if value is None or value == "":
        return None
    if isinstance(value, (bool, int, Decimal)):
        return value
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


class Adapter:
    """How rules read and write one object's records.

    Subclasses set `route` and `FIELDS`, or override `own_fields` when the
    catalogue varies by org, and implement `update` over the module's own
    update service. `parent_key` is the object a record's parent always is,
    or None when there is none or it varies.
    """

    parent_key: str | None = None
    route: str | None = None
    FIELDS: tuple[FieldSpec, ...] = ()

    def __init__(self, entry):
        self.entry = entry
        self._catalogues = {}

    def own_fields(self, org) -> list[FieldSpec]:
        return list(self.FIELDS)

    def fields(self, org) -> list[FieldSpec]:
        return [
            *self.own_fields(org),
            *custom_field_specs(org, self.entry.custom_field_target),
        ]

    def _catalogue(self, record) -> dict[str, FieldSpec]:
        """`fields` of the record's org by key, built once per adapter.

        `automation_adapter()` makes a new adapter per use, so this is never
        older than the caller's own work, and reads after the first are free.
        """
        if record.org_id not in self._catalogues:
            fields = self.fields(record.org)
            self._catalogues[record.org_id] = {spec.key: spec for spec in fields}
        return self._catalogues[record.org_id]

    def read(self, record, key) -> Any:
        """The value of `key` on `record`, `None` when empty.

        Text and choices are `str`, numbers `Decimal` or `int`, dates ISO
        `YYYY-MM-DD`, booleans `bool`, and a `people` field the sorted ids of
        its active profiles in the record's org. A custom key whose definition
        is gone reads `None`; any other key outside the catalogue raises.
        """
        if key.startswith(CUSTOM_PREFIX):
            stored = record.custom_fields or {}
            return _plain(stored.get(key[len(CUSTOM_PREFIX) :]))
        spec = self._catalogue(record).get(key)
        if spec is None:
            raise KeyError(key)
        if spec.type == "people":
            people = getattr(record, key).filter(org_id=record.org_id, is_active=True)
            return sorted(str(pk) for pk in people.values_list("pk", flat=True))
        return _plain(getattr(record, key))

    def snapshot(self, record) -> dict[str, Any]:
        return {
            key: self.read(record, key)
            for key, spec in self._catalogue(record).items()
            if spec.type != "people"
        }

    def load(self, org, pk):
        try:
            return self.entry.records(org).filter(pk=pk).first()
        except (DjangoValidationError, ValueError):
            return None

    def name(self, record) -> str:
        return str(record)

    def path(self, record) -> str:
        if self.route is None:
            raise NotImplementedError
        return self.route.format(id=record.pk)

    def parent(self, record):
        return None

    def parent_label(self, record) -> str:
        """What the record's parent is called: "account", or "parent" if it varies."""
        parent = self.parent(record)
        key = parent[0] if parent is not None else self.parent_key
        entry = object_for_key(record.org, key) if key is not None else None
        return entry.label.lower() if entry is not None else "parent"

    def people(self, record, who: str) -> list:
        if who == "assignees":
            return list(record.assigned_to.filter(org_id=record.org_id, is_active=True))
        if who == "creator":
            if record.created_by_id is None:
                return []
            return list(
                Profile.objects.filter(
                    user_id=record.created_by_id,
                    org_id=record.org_id,
                    is_active=True,
                )[:1]
            )
        raise ValueError(f"Unknown people: {who!r}")

    def task_parent(self, record) -> dict:
        return {}

    def webhook_data(self, record) -> dict | None:
        return None

    def update(self, request, record, data) -> dict | None:
        raise NotImplementedError

    def write(self, record, changes: dict, actor) -> dict | None:
        """Apply catalogue `changes` to `record` as `actor`, through `update`.

        `None` once saved, else the error dict a 400 would carry. The update
        services trust their caller's lookup, so the actor's org, standing and
        edit rule are checked here, and only settable catalogue keys pass.
        `update` gets the record re-read under a lock and only the custom
        field keys asked for, which it merges over that row, so a value
        changed since `record` was loaded stands.
        """
        cannot_edit = {"detail": [f"Cannot edit this {self.entry.label.lower()}."]}
        if (
            not actor.is_active
            or record.org_id != actor.org_id
            or not self.entry.editable(actor).filter(pk=record.pk).exists()
        ):
            return cannot_edit
        settable = {k for k, s in self._catalogue(record).items() if s.settable}
        refused = [key for key in changes if key not in settable]
        if refused:
            return {key: ["A rule cannot set this field."] for key in refused}

        data, custom = {}, {}
        for key, value in changes.items():
            if key.startswith(CUSTOM_PREFIX):
                custom[key[len(CUSTOM_PREFIX) :]] = value
            else:
                data[key] = value
        if custom:
            data["custom_fields"] = custom
        try:
            with transaction.atomic():
                locked = (
                    self.entry.records(record.org)
                    .select_for_update(no_key=True)
                    .filter(pk=record.pk)
                    .first()
                )
                if locked is None:
                    return cannot_edit
                return self.update(SimpleNamespace(profile=actor), locked, data)
        except ValidationError as exc:
            detail = exc.detail
            return dict(detail) if isinstance(detail, dict) else {"detail": detail}


def _adapter_of(entry):
    offer = getattr(entry, "automation_adapter", None)
    return offer() if offer is not None else None


def adapter_for(org, key) -> Adapter | None:
    entry = object_for_key(org, key)
    return _adapter_of(entry) if entry is not None else None


def switched_off_module(org, key) -> str | None:
    """The module of the built-in object `key` when it is off for `org`."""
    module = object_module(key)
    if module is None or module_is_available(org, module):
        return None
    return module


def automatable(org) -> list[tuple[Any, Adapter]]:
    pairs = ((entry, _adapter_of(entry)) for entry in all_objects(org))
    return [(entry, adapter) for entry, adapter in pairs if adapter is not None]
