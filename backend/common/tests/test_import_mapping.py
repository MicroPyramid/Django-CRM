import json
from types import SimpleNamespace

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from cases.inbound.contacts import _split_display_name
from common.import_mapping import (
    MappingError,
    guess_mapping,
    mapped_records,
    normalize_header,
    read_mapped_upload,
    resolve_mapping,
)
from common.spreadsheet import SpreadsheetError, Table
from common.utils import split_full_name

SYN = {"phone": ("mobile", "phone number"), "email": ("email address",)}


def test_normalize_header():
    assert normalize_header("E-mail 1 - Value") == "e mail 1 value"
    assert normalize_header(" Phone_Number ") == "phone number"
    assert normalize_header("State/Region") == "state region"


def test_guess_mapping_first_wins_unknown_none():
    headers = ["Mobile", "Phone Number", "Shoe size", "email"]
    assert guess_mapping(headers, SYN) == ["phone", None, None, "email"]


def test_guess_mapping_synonym_beats_self_name():
    headers = ["Title", "Job Title"]
    assert guess_mapping(headers, {"title": ("job title",)}) == [None, "title"]


def test_guess_mapping_synonym_order_is_preference():
    headers = ["Business Phone", "Mobile Phone"]
    synonyms = {"phone": ("mobile phone", "business phone")}
    assert guess_mapping(headers, synonyms) == [None, "phone"]


def test_guess_mapping_equal_rank_first_column_wins():
    assert guess_mapping(["Mobile", "mobile"], SYN) == ["phone", None]
    assert guess_mapping(["phone", "Phone"], {"phone": ()}) == ["phone", None]


def test_guess_mapping_normalizes_synonyms():
    assert guess_mapping(["Cell-Phone"], {"phone": ("CELL_PHONE",)}) == ["phone"]


def test_resolve_mapping_auto():
    table = Table(["Mobile", "x"], [])
    allowed = {"phone", "email"}
    assert resolve_mapping("auto", table, SYN, allowed) == guess_mapping(
        table.headers, SYN
    )


TABLE = Table(["a", "b"], [])
ALLOWED = {"email", "phone", "first_name"}


def _resolve(raw):
    return resolve_mapping(raw, TABLE, SYN, ALLOWED)


def test_resolve_mapping_valid():
    assert _resolve(json.dumps({"1": "email", "0": None})) == [None, "email"]
    assert _resolve("{}") == [None, None]


@pytest.mark.parametrize(
    "raw",
    [
        "not json",
        "[1]",
        '{"x": "email"}',
        '{"0": 5}',
        '{"0": ["email"]}',
        '{"0": true}',
        '{"1.5": "email"}',
    ],
)
def test_resolve_mapping_unreadable(raw):
    with pytest.raises(MappingError) as exc:
        _resolve(raw)
    assert str(exc.value) == "The column choices could not be read."


def test_resolve_mapping_bad_index():
    with pytest.raises(MappingError) as exc:
        _resolve('{"9": "email"}')
    assert str(exc.value) == (
        "The column choices name a column the file does not have."
    )


def test_resolve_mapping_negative_index():
    with pytest.raises(MappingError) as exc:
        _resolve('{"-1": "email"}')
    assert str(exc.value) == (
        "The column choices name a column the file does not have."
    )


def test_resolve_mapping_forbidden_field():
    with pytest.raises(MappingError) as exc:
        _resolve('{"0": "org"}')
    assert str(exc.value) == (
        "The column choices include a field that cannot be imported."
    )
    assert "org" not in str(exc.value)


def test_resolve_mapping_duplicate_target():
    with pytest.raises(MappingError) as exc:
        _resolve('{"0": "email", "1": "email"}')
    assert str(exc.value) == "Two columns are set to email; choose one."


def test_mapped_records_full_name_and_multivalue():
    table = Table(["Name", "E-mail 1 - Value"], [["Ada Byte", "a@x.com ::: b@x.com"]])
    assert mapped_records(table, ["full_name", "email"]) == [
        (
            1,
            {"first_name": "Ada", "last_name": "Byte", "email": "a@x.com"},
            ["Ada Byte", "a@x.com ::: b@x.com"],
        )
    ]


def test_mapped_records_full_name_does_not_overwrite():
    table = Table(["Name", "First"], [["Ada Byte", "Grace"]])
    [(_, record, _)] = mapped_records(table, ["full_name", "first_name"])
    assert record == {"first_name": "Grace", "last_name": "Byte"}


def test_mapped_records_ragged():
    table = Table(["a", "b"], [["x"], ["y", "z", "extra"], ["", "q"]])
    records = mapped_records(table, ["first_name", "email"])
    assert records == [
        (1, {"first_name": "x"}, ["x"]),
        (2, {"first_name": "y", "email": "z"}, ["y", "z", "extra"]),
        (3, {"email": "q"}, ["", "q"]),
    ]


def test_split_full_name():
    assert split_full_name("Ravi Kumar Sharma") == ("Ravi", "Kumar Sharma")
    assert split_full_name("Ramesh") == ("Ramesh", "")
    assert split_full_name("  ") == ("", "")


def test_inbound_split_display_name_unchanged():
    assert _split_display_name("Ada Byte", "a@x.com") == ("Ada", "Byte")
    assert _split_display_name("", "ada@x.com") == ("ada", "")
    assert _split_display_name("", "") == ("Unknown", "")


def test_preview_to_dict_and_describe():
    from collections import Counter

    from common.import_mapping import (
        MappedPreview,
        SkippedRow,
        describe_columns,
        describe_fields,
    )

    table = Table(["Name", "Email"], [["Ada", "a@x.com ::: b"], ["", ""], ["B", "c"]])
    cols = describe_columns(table, ["full_name", "email"])
    assert cols[1] == {
        "index": 1,
        "header": "Email",
        "field": "email",
        "samples": ["a@x.com", "c"],
    }
    assert describe_fields([("email", "Email", True)]) == [
        {"name": "email", "label": "Email", "required": True}
    ]

    class V:
        def to_dict(self):
            return {"ok": 1}

    preview = MappedPreview(
        columns=cols,
        fields=[],
        valid=[V()],
        skipped=[SkippedRow(2, "email", "Missing", ["", ""], "row")],
        dropped=Counter({"b": 2, "a": 1}),
    )
    out = preview.to_dict()
    assert out["dropped"] == [
        {"field": "a", "count": 1},
        {"field": "b", "count": 2},
    ]
    assert out["summary"] == {"total": 2, "valid": 1, "skipped": 1}
    assert out["skipped"] == [
        {
            "row": 2,
            "field": "email",
            "message": "Missing",
            "cells": ["", ""],
            "kind": "row",
        }
    ]


@pytest.mark.parametrize("raw", ["[" * 100000, '{"0":' * 100000])
def test_resolve_mapping_deeply_nested_json(raw):
    with pytest.raises(MappingError) as exc:
        _resolve(raw)
    assert str(exc.value) == "The column choices could not be read."


def _upload_request(name, data, mapping):
    return SimpleNamespace(
        FILES={"file": SimpleUploadedFile(name, data)}, data={"mapping": mapping}
    )


def test_read_mapped_upload_reads_then_resolves():
    request = _upload_request("people.csv", b"Mobile,Shoe size\n123,9\n", "auto")
    table, mapping = read_mapped_upload(request, 10, SYN, {"phone"})
    assert table == Table(["Mobile", "Shoe size"], [["123", "9"]])
    assert mapping == ["phone", None]


def test_read_mapped_upload_raises_unchanged():
    with pytest.raises(SpreadsheetError) as exc:
        read_mapped_upload(_upload_request("p.xls", b"x", "auto"), 10, SYN, {"phone"})
    assert str(exc.value) == "Save it as .xlsx or .csv and try again."

    # max_rows reaches the reader.
    with pytest.raises(SpreadsheetError) as exc:
        read_mapped_upload(_upload_request("p.csv", b"a\n1\n2\n", "auto"), 1, SYN, {})
    assert str(exc.value) == "Too many rows (2); the limit is 1."

    # `allowed` reaches the resolver: email has synonyms but is not allowed here.
    request = _upload_request("p.csv", b"Mobile\n1\n", json.dumps({"0": "email"}))
    with pytest.raises(MappingError) as exc:
        read_mapped_upload(request, 10, SYN, {"phone"})
    assert (
        str(exc.value) == "The column choices include a field that cannot be imported."
    )
