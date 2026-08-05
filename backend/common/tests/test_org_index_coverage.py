"""Every ``BaseOrgModel`` subclass keeps the per-org index its base promises.

``BaseOrgModel.Meta`` declares ``indexes = [Index(fields=["org", "-created_at"])]``
and its docstring sells "per-org indexes for performance" as one of the three
reasons to inherit from it. Django does not merge ``Meta`` classes: a subclass
that declares a plain ``class Meta:`` replaces the parent's outright, silently
losing ``indexes``.

``orders.Order`` and ``orders.OrderLineItem`` did exactly that, and the
evidence is a real migration in the tree,
``orders/0003_remove_order_orders_org_id_9026a7_idx_and_more``, which dropped
both indexes because ``makemigrations`` correctly read them as gone. Nothing
warned; the base class went on advertising the index in its docstring.

This is the kind of thing to guard from the model registry rather than from a
list written out here, for the same reason ``_TAGGABLE`` is: a hand-maintained
list of "models to check" has the identical failure mode as the thing it is
checking.
"""

from __future__ import annotations

from django.apps import apps

from common.base import BaseOrgModel

EXPECTED_FIELDS = ["org", "-created_at"]


def _org_scoped_models():
    return [
        model
        for model in apps.get_models()
        if issubclass(model, BaseOrgModel) and not model._meta.abstract
    ]


def test_the_sweep_actually_finds_models():
    """A guard that silently matches nothing passes forever."""
    assert len(_org_scoped_models()) >= 4


def test_every_org_scoped_model_has_the_org_created_at_index():
    missing = []
    for model in _org_scoped_models():
        if not any(index.fields == EXPECTED_FIELDS for index in model._meta.indexes):
            missing.append(model._meta.label)

    assert missing == [], (
        "These models inherit BaseOrgModel but do not carry its "
        f"{EXPECTED_FIELDS} index. A subclass declaring its own `class Meta:` "
        "replaces the parent's instead of extending it, so the index has to be "
        "restated (see orders/models.py): " + ", ".join(missing)
    )
