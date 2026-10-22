"""Deciding whether a rule's trigger fires and its conditions hold.

Pure functions over a captured `Change` and record values read by an adapter.
The comparison is chosen from the runtime type of the record's value, since
no field types reach here: a list is people, a bool is boolean, a number is
compared as `Decimal`, anything else as text. There is deliberately no
pattern operator; tenant text is only ever compared, never evaluated.
"""

import logging
from decimal import Decimal

from automation.capture import CREATED, UPDATED, Change

logger = logging.getLogger(__name__)

OPERATORS = {
    "text": ("eq", "neq", "contains", "not_contains", "empty", "not_empty"),
    "number": ("eq", "neq", "gt", "lt", "empty", "not_empty"),
    "date": ("eq", "neq", "gt", "lt", "empty", "not_empty"),
    "choice": ("eq", "neq", "in", "not_in", "empty", "not_empty"),
    "boolean": ("true", "false"),
    "person": ("eq", "includes", "excludes", "empty", "not_empty"),
    "people": ("eq", "includes", "excludes", "empty", "not_empty"),
}
UPDATE_ONLY = ("was", "was_not")


def _is_empty(v):
    return v is None or v == "" or v == []


def _is_number(v):
    return isinstance(v, (int, float, Decimal)) and not isinstance(v, bool)


def _dec(v):
    if isinstance(v, bool):
        raise ValueError("not a number")
    return Decimal(str(v))


def _ids(v):
    if v is None or v == "":
        return []
    items = v if isinstance(v, (list, tuple)) else [v]
    return sorted(str(i) for i in items)


def _equal(actual, value):
    if isinstance(actual, list):
        return _ids(actual) == _ids(value)
    if _is_empty(actual):
        return _is_empty(value)
    if isinstance(actual, bool):
        return isinstance(value, bool) and actual == value
    if _is_number(actual):
        return _dec(actual) == _dec(value)
    return not _is_empty(value) and str(actual) == str(value)


def _order(actual, value):
    """-1, 0 or 1 comparing the record value to the condition value."""
    if _is_number(actual):
        a, b = _dec(actual), _dec(value)
    else:
        a, b = str(actual), str(value)
    return (a > b) - (a < b)


def _contains(actual, value):
    return str(value).lower() in str(actual).lower()


def _in(actual, value):
    if not isinstance(value, (list, tuple)):
        return False
    return any(_equal(actual, v) for v in value)


def _unset_as_false(a, b):
    """Two values compared, an unset checkbox reading false as `"false"` does."""
    if isinstance(a, bool) or isinstance(b, bool):
        return a is True, b is True
    return a, b


def _evaluate(op, field, value, values, previous):
    if op in UPDATE_ONLY:
        before = previous[field] if field in previous else values.get(field)
        return _equal(*_unset_as_false(before, value)) == (op == "was")
    actual = values.get(field)
    empty = _is_empty(actual)
    if op == "empty":
        return empty
    if op == "not_empty":
        return not empty
    if op == "true":
        return actual is True
    if op == "false":
        return actual is False or actual is None
    if op == "eq":
        return _equal(actual, value)
    if op == "neq":
        return not _equal(actual, value)
    if op == "in":
        return _in(actual, value)
    if op == "not_in":
        return isinstance(value, (list, tuple)) and not _in(actual, value)
    if op == "includes":
        return not empty and str(value) in _ids(actual)
    if op == "excludes":
        return empty or str(value) not in _ids(actual)
    if op == "contains":
        return not empty and _contains(actual, value)
    if op == "not_contains":
        return empty or not _contains(actual, value)
    if op == "gt":
        return not empty and _order(actual, value) > 0
    if op == "lt":
        return not empty and _order(actual, value) < 0
    return False


def _moved(old, new):
    old, new = _unset_as_false(old, new)
    return old != new


def trigger_matches(trigger: dict, change: Change) -> bool:
    event = trigger.get("event")
    if event == CREATED:
        return change.event == CREATED
    if event != UPDATED or change.event != UPDATED:
        return False
    field = trigger.get("field")
    if not field:
        return any(_moved(old, new) for old, new in change.changes.values())
    if field not in change.changes or not _moved(*change.changes[field]):
        return False
    to = trigger.get("to")
    if to is None:
        return True
    old, new = _unset_as_false(*change.changes[field])
    try:
        return _equal(new, to) and not _equal(old, to)
    except Exception:
        return False


def conditions_match(
    match: str, conditions: list[dict], values: dict, previous: dict
) -> bool:
    if not conditions:
        return True
    results = (_condition_holds(c, values, previous) for c in conditions)
    return any(results) if match == "any" else all(results)


def _condition_holds(condition: dict, values: dict, previous: dict) -> bool:
    op, field = condition.get("op"), condition.get("field")
    try:
        return _evaluate(op, field, condition.get("value"), values, previous)
    except Exception as exc:
        logger.warning(
            "Automation condition failed: op=%s field=%s error=%s",
            op,
            field,
            type(exc).__name__,
        )
        return False
