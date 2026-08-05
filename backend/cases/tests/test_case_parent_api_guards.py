"""The parent/child guards, exercised through the API rather than the model.

``cases/tests/test_parent_child.py`` covers the same rules by calling
``case.clean()`` directly. That proves the model method works; it proves
nothing about the endpoints, because ``Case.save()`` does not call
``full_clean()`` and DRF never calls ``Model.clean()``. Every test here goes
through ``PATCH /api/cases/<id>/``, which is the door a client actually uses.

The rules under test, all declared in ``Case.clean()``:

* a case cannot be its own parent
* linking must not create a cycle in the case tree
* the tree is limited to ``Case.PARENT_MAX_DEPTH`` levels
* a merged (``Duplicate``) case may be neither the parent nor the child

The dedicated ``POST /api/cases/<id>/link/`` endpoint enforced all four. The
generic serializer enforced only the first and the parent half of the last,
which is why the cycle test below hangs the link endpoint when run against
the unfixed serializer.
"""

from __future__ import annotations

import pytest
from crum import impersonate
from rest_framework import status

from cases.models import Case


def _detail_url(pk):
    return f"/api/cases/{pk}/"


def _link_url(pk):
    return f"/api/cases/{pk}/link/"


def _make_case(org, creator, *, name, parent=None, status_value="New"):
    with impersonate(creator):
        return Case.objects.create(
            name=name,
            status=status_value,
            priority="Normal",
            org=org,
            parent=parent,
        )


@pytest.mark.django_db
class TestTheSerializerRefusesACycle:
    """The reason this matters is not tidiness of the tree.

    ``CaseLinkParentView`` walks the ancestor chain with a bare
    ``while cursor is not None``. A cycle stored by any other write path makes
    that walk run forever, one database query per step, on a request any
    authenticated member of the org can send.
    """

    def test_two_case_cycle_is_refused(self, admin_client, admin_user, org_a):
        a = _make_case(org_a, admin_user, name="A")
        b = _make_case(org_a, admin_user, name="B")

        first = admin_client.patch(
            _detail_url(a.pk), {"parent": str(b.pk)}, format="json"
        )
        assert first.status_code == status.HTTP_200_OK

        closing = admin_client.patch(
            _detail_url(b.pk), {"parent": str(a.pk)}, format="json"
        )
        assert closing.status_code == status.HTTP_400_BAD_REQUEST
        # `CaseDetailView` wraps serializer errors as `{error, errors}`, so the
        # field name the client reads is one level in.
        assert "parent" in closing.data["errors"]

        b.refresh_from_db()
        assert b.parent_id is None

    def test_three_case_cycle_is_refused(self, admin_client, admin_user, org_a):
        """A cycle does not have to be two cases long.

        A guard that only compares the incoming parent against the record
        itself catches A -> B -> A and misses A -> B -> C -> A, so the chain
        has to be walked.
        """
        a = _make_case(org_a, admin_user, name="A")
        b = _make_case(org_a, admin_user, name="B", parent=a)
        c = _make_case(org_a, admin_user, name="C", parent=b)

        response = admin_client.patch(
            _detail_url(a.pk), {"parent": str(c.pk)}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        a.refresh_from_db()
        assert a.parent_id is None

    def test_self_parent_is_refused(self, admin_client, admin_user, org_a):
        a = _make_case(org_a, admin_user, name="A")
        response = admin_client.patch(
            _detail_url(a.pk), {"parent": str(a.pk)}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestTheSerializerEnforcesTheDepthLimit:
    def test_a_tree_at_the_limit_is_accepted(self, admin_client, admin_user, org_a):
        root = _make_case(org_a, admin_user, name="L1")
        mid = _make_case(org_a, admin_user, name="L2", parent=root)
        leaf = _make_case(org_a, admin_user, name="L3")

        response = admin_client.patch(
            _detail_url(leaf.pk), {"parent": str(mid.pk)}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK

        leaf.refresh_from_db()
        assert leaf.parent_id == mid.pk

    def test_one_level_past_the_limit_is_refused(self, admin_client, admin_user, org_a):
        assert Case.PARENT_MAX_DEPTH == 3
        l1 = _make_case(org_a, admin_user, name="L1")
        l2 = _make_case(org_a, admin_user, name="L2", parent=l1)
        l3 = _make_case(org_a, admin_user, name="L3", parent=l2)
        l4 = _make_case(org_a, admin_user, name="L4")

        response = admin_client.patch(
            _detail_url(l4.pk), {"parent": str(l3.pk)}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        l4.refresh_from_db()
        assert l4.parent_id is None

    def test_depth_counts_the_children_the_case_already_carries(
        self, admin_client, admin_user, org_a
    ):
        """Re-parenting moves a whole subtree, so the subtree's own depth counts.

        A leaf may hang off a two-level tree; the root of a two-level subtree
        may not, because the result is four levels. ``CaseLinkParentView``
        already reasoned this way (``parent_depth + 1 + child_subtree_depth``)
        and the serializer did not.
        """
        l1 = _make_case(org_a, admin_user, name="L1")
        l2 = _make_case(org_a, admin_user, name="L2", parent=l1)

        subtree_root = _make_case(org_a, admin_user, name="Sub root")
        _make_case(org_a, admin_user, name="Sub child", parent=subtree_root)

        response = admin_client.patch(
            _detail_url(subtree_root.pk), {"parent": str(l2.pk)}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        subtree_root.refresh_from_db()
        assert subtree_root.parent_id is None


@pytest.mark.django_db
class TestMergedCasesCannotBeLinked:
    def test_a_merged_case_is_refused_as_a_parent(
        self, admin_client, admin_user, org_a
    ):
        merged = _make_case(org_a, admin_user, name="Merged", status_value="Duplicate")
        child = _make_case(org_a, admin_user, name="Child")

        response = admin_client.patch(
            _detail_url(child.pk), {"parent": str(merged.pk)}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_a_merged_case_is_refused_as_a_child(self, admin_client, admin_user, org_a):
        """The half the serializer missed.

        ``validate_parent`` is a field validator and sees only the incoming
        parent, so "the case being linked is itself merged" cannot be checked
        there. ``CaseLinkParentView`` rejects both directions in one condition.
        """
        merged = _make_case(org_a, admin_user, name="Merged", status_value="Duplicate")
        parent = _make_case(org_a, admin_user, name="Parent")

        response = admin_client.patch(
            _detail_url(merged.pk), {"parent": str(parent.pk)}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        merged.refresh_from_db()
        assert merged.parent_id is None


@pytest.mark.django_db
class TestOrdinaryLinkingStillWorks:
    """The guards have to be able to answer yes, or they are just an outage."""

    def test_linking_a_loose_case_under_a_parent_is_accepted(
        self, admin_client, admin_user, org_a
    ):
        parent = _make_case(org_a, admin_user, name="Parent")
        child = _make_case(org_a, admin_user, name="Child")

        response = admin_client.patch(
            _detail_url(child.pk), {"parent": str(parent.pk)}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK

        child.refresh_from_db()
        assert child.parent_id == parent.pk

    def test_clearing_a_parent_is_accepted(self, admin_client, admin_user, org_a):
        parent = _make_case(org_a, admin_user, name="Parent")
        child = _make_case(org_a, admin_user, name="Child", parent=parent)

        response = admin_client.patch(
            _detail_url(child.pk), {"parent": None}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK

        child.refresh_from_db()
        assert child.parent_id is None

    def test_an_edit_that_does_not_touch_parent_is_unaffected(
        self, admin_client, admin_user, org_a
    ):
        """The guard must not fire on a record that already has a parent.

        A field validator that ran the cycle walk against the stored parent on
        every save would reject every ordinary rename of a child case.
        """
        parent = _make_case(org_a, admin_user, name="Parent")
        child = _make_case(org_a, admin_user, name="Child", parent=parent)

        response = admin_client.patch(
            _detail_url(child.pk), {"name": "Renamed child"}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK

        child.refresh_from_db()
        assert child.name == "Renamed child"
        assert child.parent_id == parent.pk


@pytest.mark.django_db
class TestTheLinkEndpointSurvivesAStoredCycle:
    """Defence in depth for cycles written before the serializer was fixed.

    The serializer guard stops new ones. A database that already contains a
    cycle, from this bug or from a direct write, still has to be survivable:
    the ancestor walk must terminate rather than pin a worker.
    """

    def test_walking_into_a_pre_existing_cycle_terminates(
        self, admin_client, admin_user, org_a
    ):
        a = _make_case(org_a, admin_user, name="A")
        b = _make_case(org_a, admin_user, name="B", parent=a)
        # Written straight to the column, bypassing every application guard,
        # which is the only way to produce this state once the fix is in.
        Case.objects.filter(pk=a.pk).update(parent=b)

        loose = _make_case(org_a, admin_user, name="Loose")
        response = admin_client.post(
            _link_url(loose.pk), {"parent_id": str(a.pk)}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        loose.refresh_from_db()
        assert loose.parent_id is None
