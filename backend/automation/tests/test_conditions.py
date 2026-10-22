"""Triggers and conditions: pure decisions, no database."""

import logging
from decimal import Decimal

import pytest

from automation.capture import Change
from automation.conditions import (
    OPERATORS,
    UPDATE_ONLY,
    conditions_match,
    trigger_matches,
)


def _updated(**changes):
    return Change("org", "deal", "r1", "updated", changes)


def _created():
    return Change("org", "deal", "r1", "created", {})


def _one(op, actual, value=None, field="f"):
    return conditions_match(
        "all", [{"field": field, "op": op, "value": value}], {field: actual}, {}
    )


ROWS = [
    # text
    ("eq", "Acme", "Acme", True),
    ("eq", "Acme", "acme", False),
    ("neq", "Acme", "Acme", False),
    ("neq", "Acme", "Other", True),
    ("neq", None, "Other", True),
    ("contains", "Acme Corp", "acme", True),
    ("contains", "Acme Corp", "zzz", False),
    ("contains", None, "a", False),
    ("contains", "", "a", False),
    ("not_contains", "Acme Corp", "acme", False),
    ("not_contains", "Acme Corp", "zzz", True),
    ("not_contains", None, "a", True),
    ("empty", None, None, True),
    ("empty", "", None, True),
    ("empty", [], None, True),
    ("empty", "x", None, False),
    ("not_empty", "x", None, True),
    ("not_empty", None, None, False),
    ("not_empty", ["p1"], None, True),
    # number
    ("eq", Decimal("9.5"), 9.5, True),
    ("eq", Decimal("9.5"), "9.50", True),
    ("eq", 10, "11", False),
    ("neq", 10, 11, True),
    ("neq", 10, 10, False),
    ("gt", Decimal("9.5"), 9, True),
    ("gt", Decimal("9.5"), 10, False),
    ("gt", None, 1, False),
    ("lt", 3, "4", True),
    ("lt", 5, 4, False),
    ("lt", None, 1, False),
    # date (ISO strings)
    ("gt", "2026-10-22", "2026-10-01", True),
    ("gt", "2026-09-22", "2026-10-01", False),
    ("lt", "2026-09-22", "2026-10-01", True),
    ("lt", "2026-10-22", "2026-10-01", False),
    ("eq", "2026-10-01", "2026-10-01", True),
    ("neq", "2026-10-01", "2026-10-01", False),
    # choice
    ("in", "won", ["won", "lost"], True),
    ("in", "open", ["won", "lost"], False),
    ("in", None, ["won"], False),
    ("not_in", "open", ["won", "lost"], True),
    ("not_in", "won", ["won", "lost"], False),
    ("not_in", None, ["won"], True),
    ("in", "won", "won", False),
    # boolean
    ("true", True, None, True),
    ("true", False, None, False),
    ("false", False, None, True),
    ("false", True, None, False),
    ("false", None, None, True),
    ("true", None, None, False),
    ("eq", True, True, True),
    ("eq", True, False, False),
    # people
    ("eq", ["a", "b"], ["b", "a"], True),
    ("eq", ["a", "b"], ["a"], False),
    ("eq", ["a"], "a", True),
    ("eq", [], [], True),
    ("includes", ["a", "b"], "a", True),
    ("includes", ["a", "b"], "c", False),
    ("includes", [], "a", False),
    ("excludes", ["a", "b"], "c", True),
    ("excludes", ["a", "b"], "a", False),
    ("excludes", [], "a", True),
    ("neq", ["a"], ["b"], True),
]


@pytest.mark.parametrize("op,actual,value,expected", ROWS)
def test_operator_table(op, actual, value, expected):
    assert _one(op, actual, value) is expected


def test_operator_catalogue_names():
    assert OPERATORS["boolean"] == ("true", "false")
    assert OPERATORS["people"] == ("eq", "includes", "excludes", "empty", "not_empty")
    assert UPDATE_ONLY == ("was", "was_not")


def test_unknown_operator_and_regex_do_not_match():
    assert _one("regex", "abc", "a.c") is False
    assert _one("matches", "abc", "abc") is False


def test_number_strings_compare_as_numbers():
    assert _one("gt", Decimal("9.5"), "10") is False
    assert _one("lt", Decimal("9.5"), "10") is True


def test_changes_to_fires_only_on_the_move_into_the_value():
    trig = {"event": "updated", "field": "stage", "to": "Won"}
    assert trigger_matches(trig, _updated(stage=("Proposal", "Won"))) is True
    assert trigger_matches(trig, _updated(stage=("Won", "Won"))) is False
    assert (
        trigger_matches({**trig, "to": "won"}, _updated(stage=("Won", "Lost"))) is False
    )


def test_trigger_event_and_field_rules():
    assert trigger_matches({"event": "created"}, _created()) is True
    assert trigger_matches({"event": "created"}, _updated(a=(1, 2))) is False
    assert trigger_matches({"event": "updated"}, _created()) is False
    assert trigger_matches({"event": "updated"}, _updated()) is False
    assert trigger_matches({"event": "updated"}, _updated(a=(1, 2))) is True
    assert (
        trigger_matches({"event": "updated", "field": "a"}, _updated(b=(1, 2))) is False
    )
    assert (
        trigger_matches({"event": "updated", "field": "a"}, _updated(a=(1, 2))) is True
    )


def test_trigger_to_normalises_like_eq():
    trig = {"event": "updated", "field": "amount", "to": "10"}
    assert (
        trigger_matches(trig, _updated(amount=(Decimal("5"), Decimal("10.0")))) is True
    )
    people = {"event": "updated", "field": "owners", "to": ["b", "a"]}
    assert trigger_matches(people, _updated(owners=(["a"], ["a", "b"]))) is True


def test_a_checkbox_saved_unchecked_for_the_first_time_does_not_change():
    to_false = {"event": "updated", "field": "vip", "to": False}
    to_true = {**to_false, "to": True}
    assert trigger_matches(to_false, _updated(vip=(None, False))) is False
    assert trigger_matches(to_false, _updated(vip=(True, False))) is True
    assert trigger_matches(to_true, _updated(vip=(None, True))) is True
    assert (
        trigger_matches({**to_false, "to": None}, _updated(vip=(None, False))) is False
    )
    assert trigger_matches({"event": "updated"}, _updated(vip=(None, False))) is False
    assert trigger_matches({"event": "updated"}, _updated(vip=(False, True))) is True


def test_trigger_unknown_event_or_bad_to_does_not_match():
    assert trigger_matches({"event": "deleted"}, _created()) is False
    trig = {"event": "updated", "field": "amount", "to": "abc"}
    assert trigger_matches(trig, _updated(amount=(1, 2))) is False


def test_any_and_all():
    conds = [
        {"field": "a", "op": "eq", "value": "x"},
        {"field": "b", "op": "eq", "value": "y"},
    ]
    both, one, none = {"a": "x", "b": "y"}, {"a": "x", "b": "n"}, {"a": "n", "b": "n"}
    assert conditions_match("all", conds, both, {}) is True
    assert conditions_match("all", conds, one, {}) is False
    assert conditions_match("any", conds, one, {}) is True
    assert conditions_match("any", conds, none, {}) is False


def test_an_empty_condition_list_matches():
    assert conditions_match("all", [], {}, {}) is True
    assert conditions_match("any", [], {}, {}) is True


def test_a_broken_condition_does_not_match(caplog):
    secret = "s3cret-value"
    conds = [{"field": "n", "op": "gt", "value": secret}]
    with caplog.at_level(logging.WARNING):
        assert conditions_match("all", conds, {"n": Decimal("5")}, {}) is False
    assert "gt" in caplog.text and "n" in caplog.text
    assert secret not in caplog.text and "5" not in caplog.text.split("n")[-1]
    # a broken condition in an "any" list does not stop a good one
    good = {"field": "n", "op": "not_empty"}
    assert conditions_match("any", [conds[0], good], {"n": Decimal("5")}, {}) is True


def test_was_reads_the_old_value():
    conds = [{"field": "stage", "op": "was", "value": "Proposal"}]
    assert (
        conditions_match("all", conds, {"stage": "Won"}, {"stage": "Proposal"}) is True
    )
    assert conditions_match("all", conds, {"stage": "Won"}, {"stage": "Other"}) is False
    not_conds = [{"field": "stage", "op": "was_not", "value": "Proposal"}]
    assert (
        conditions_match("all", not_conds, {"stage": "Won"}, {"stage": "Other"}) is True
    )
    assert (
        conditions_match("all", not_conds, {"stage": "Won"}, {"stage": "Proposal"})
        is False
    )


def test_was_on_an_unchanged_field_reads_the_current_value():
    values = {"status": "New", "amount": 5}
    previous = {"amount": 3}
    was = [{"field": "status", "op": "was", "value": "New"}]
    was_other = [{"field": "status", "op": "was", "value": "Won"}]
    was_not = [{"field": "status", "op": "was_not", "value": "New"}]
    assert conditions_match("all", was, values, previous) is True
    assert conditions_match("all", was_other, values, previous) is False
    assert conditions_match("all", was_not, values, previous) is False


def test_an_unset_old_checkbox_was_false():
    def holds(op, value, old):
        condition = [{"field": "vip", "op": op, "value": value}]
        return conditions_match("all", condition, {"vip": True}, {"vip": old})

    assert holds("was", False, None) is True
    assert holds("was", False, False) is True
    assert holds("was", False, True) is False
    assert holds("was", True, None) is False
    assert holds("was_not", False, None) is False
    assert holds("was_not", True, None) is True
