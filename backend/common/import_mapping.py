"""Column matching for spreadsheet imports.

Maps the headers of an uploaded table onto importable fields, either by
guessing from synonyms or from a client-supplied JSON choice. The JSON is
untrusted: every key and value is type-checked here.
"""

import json
import re
from collections import Counter
from collections.abc import Collection, Sequence
from dataclasses import dataclass, field

from common.spreadsheet import Table, read_upload
from common.utils import split_full_name

FULL_NAME = "full_name"
MULTI_VALUE_SEPARATOR = " ::: "

_UNREADABLE = "The column choices could not be read."
_BAD_INDEX = "The column choices name a column the file does not have."
_BAD_FIELD = "The column choices include a field that cannot be imported."
_SEPARATORS = re.compile(r"[-_./()\s]+")
_MAX_INDEX_DIGITS = 6


class MappingError(Exception):
    """Raised for a column choice the server refuses; str() is user-facing."""


def normalize_header(header: str) -> str:
    return _SEPARATORS.sub(" ", header.lower()).strip()


def guess_mapping(
    headers: list[str], synonyms: dict[str, tuple[str, ...]]
) -> list[str | None]:
    """Guess each header's field; a header nothing matches gets None.

    When several headers match one field, the best-ranked match takes it and
    the others get None. A synonym outranks the field's bare own name, so
    Outlook's "Job Title" beats its honorific "Title", and an earlier synonym
    in the tuple outranks a later one. Equal ranks go to the first header.
    Each header names at most one field, and each field takes one header.
    """
    lookup: dict[str, tuple[str, int]] = {}
    for name, names in synonyms.items():
        for rank, alias in enumerate(names):
            lookup.setdefault(normalize_header(alias), (name, rank))
        lookup.setdefault(normalize_header(name), (name, len(names)))
    best: dict[str, tuple[int, int]] = {}  # field -> (rank, header index)
    for index, header in enumerate(headers):
        match = lookup.get(normalize_header(header))
        if match is None:
            continue
        name, rank = match
        if name not in best or rank < best[name][0]:
            best[name] = (rank, index)
    result: list[str | None] = [None] * len(headers)
    for name, (_rank, index) in best.items():
        result[index] = name
    return result


def resolve_mapping(
    raw: str,
    table: Table,
    synonyms: dict[str, tuple[str, ...]],
    allowed: Collection[str],
) -> list[str | None]:
    if raw == "auto":
        return guess_mapping(table.headers, synonyms)
    try:
        data = json.loads(raw)
    except (TypeError, ValueError, RecursionError):
        raise MappingError(_UNREADABLE) from None
    if not isinstance(data, dict):
        raise MappingError(_UNREADABLE)

    chosen: list[tuple[int, str | None]] = []
    for key, value in data.items():
        match = re.fullmatch(r"-?[0-9]+", key)
        if match is None or len(key) > _MAX_INDEX_DIGITS + 1:
            raise MappingError(_UNREADABLE)
        if value is not None and not isinstance(value, str):
            raise MappingError(_UNREADABLE)
        chosen.append((int(key), value))

    result: list[str | None] = [None] * len(table.headers)
    for index, value in chosen:
        if index < 0 or index >= len(table.headers):
            raise MappingError(_BAD_INDEX)
        if value is not None and value not in allowed:
            raise MappingError(_BAD_FIELD)
        result[index] = value

    seen: set[str] = set()
    for value in result:
        if value is None:
            continue
        if value in seen:
            raise MappingError(f"Two columns are set to {value}; choose one.")
        seen.add(value)
    return result


def read_mapped_upload(
    request,
    max_rows: int,
    synonyms: dict[str, tuple[str, ...]],
    allowed: Collection[str],
) -> tuple[Table, list[str | None]]:
    """Read the uploaded file, then resolve the request's `mapping` field.

    Raises SpreadsheetError or MappingError, whose str() is user-facing.
    """
    table = read_upload(request, max_rows)
    return table, resolve_mapping(request.data["mapping"], table, synonyms, allowed)


def first_value(cell: str) -> str:
    return cell.split(MULTI_VALUE_SEPARATOR, 1)[0].strip()


def mapped_records(
    table: Table, mapping: list[str | None]
) -> list[tuple[int, dict[str, str], list[str]]]:
    records = []
    for number, cells in enumerate(table.rows, start=1):
        record: dict[str, str] = {}
        for index, target in enumerate(mapping):
            if target is None or index >= len(cells):
                continue
            value = first_value(cells[index])
            if value:
                record[target] = value
        full_name = record.pop(FULL_NAME, "")
        if full_name:
            first, last = split_full_name(full_name)
            if first and "first_name" not in record:
                record["first_name"] = first
            if last and "last_name" not in record:
                record["last_name"] = last
        records.append((number, record, list(cells)))
    return records


def describe_columns(table: Table, mapping: list[str | None]) -> list[dict]:
    columns = []
    for index, header in enumerate(table.headers):
        samples = []
        for cells in table.rows:
            if len(samples) == 3:
                break
            if index < len(cells):
                value = first_value(cells[index])
                if value:
                    samples.append(value)
        columns.append(
            {
                "index": index,
                "header": header,
                "field": mapping[index],
                "samples": samples,
            }
        )
    return columns


def describe_fields(fields: Sequence[tuple[str, str, bool]]) -> list[dict]:
    return [
        {"name": name, "label": label, "required": required}
        for name, label, required in fields
    ]


SKIP_DUPLICATE = "duplicate"
SKIP_ROW = "row"


@dataclass
class SkippedRow:
    """A row left out of a mapped import, with its original cells.

    `kind` is SKIP_DUPLICATE when the record already exists (in the org or
    earlier in the file) and SKIP_ROW when the row cannot become a record.
    Clients read it rather than the message, which is for people.
    """

    row: int
    field: str
    message: str
    cells: list[str]
    kind: str

    def to_dict(self) -> dict:
        return {
            "row": self.row,
            "field": self.field,
            "message": self.message,
            "cells": self.cells,
            "kind": self.kind,
        }


@dataclass
class MappedPreview:
    columns: list[dict]
    fields: list[dict]
    valid: list
    skipped: list[SkippedRow]
    dropped: Counter = field(default_factory=Counter)

    def to_dict(self) -> dict:
        return {
            "columns": self.columns,
            "fields": self.fields,
            "valid": [v.to_dict() for v in self.valid],
            "skipped": [s.to_dict() for s in self.skipped],
            "dropped": [
                {"field": name, "count": count}
                for name, count in sorted(self.dropped.items())
            ],
            "summary": {
                "total": len(self.valid) + len(self.skipped),
                "valid": len(self.valid),
                "skipped": len(self.skipped),
            },
        }
