"""A malformed id in a filter must answer 400, never 500.

Every list endpoint accepts id-valued filters straight off the query string.
Django parses them with ``uuid.UUID`` while building the query and raises
``django.core.exceptions.ValidationError``, which DRF's exception handler does
not translate, so the response was a 500. A stale bookmark, a hand-edited URL,
or any client sending a placeholder id took the endpoint down.

The frontend now strips non-UUID values before it builds a request, but the
frontend is not the trust boundary: these endpoints serve the mobile app, API
tokens and curl as well. These tests exercise the API directly for that reason.

Both directions matter. A well-formed id must still filter, so each endpoint is
asserted twice: 400 for junk, 200 for a real id.
"""

import pytest
from rest_framework import status

# Shapes that reached production URLs. `p1`, `acc-1` and `profile-1` are
# placeholder ids that older frontend fixtures emitted verbatim.
MALFORMED = ["notauuid", "p1", "acc-1", "profile-1", "abc-123", "0"]

WELL_FORMED = "3f2504e0-4f89-41d3-9a0c-0305e82c3301"

# (label, url, param). One row per endpoint-and-filter that takes an id.
ID_FILTERS = [
    ("leads.tags", "/api/leads/", "tags"),
    ("leads.assigned_to", "/api/leads/", "assigned_to"),
    ("accounts.tags", "/api/accounts/", "tags"),
    ("accounts.assigned_to", "/api/accounts/", "assigned_to"),
    ("contacts.tags", "/api/contacts/", "tags"),
    ("contacts.assigned_to", "/api/contacts/", "assigned_to"),
    ("cases.tags", "/api/cases/", "tags"),
    ("cases.assigned_to", "/api/cases/", "assigned_to"),
    ("cases.account", "/api/cases/", "account"),
    ("tasks.tags", "/api/tasks/", "tags"),
    ("tasks.assigned_to", "/api/tasks/", "assigned_to"),
    ("tasks.account", "/api/tasks/", "account"),
    ("opportunities.tags", "/api/opportunities/", "tags"),
    ("opportunities.assigned_to", "/api/opportunities/", "assigned_to"),
    ("opportunities.account", "/api/opportunities/", "account"),
    ("invoices.account", "/api/invoices/", "account"),
    ("invoices.assigned_to", "/api/invoices/", "assigned_to"),
    ("invoices.created_by", "/api/invoices/", "created_by"),
    ("documents.shared_to", "/api/documents/", "shared_to"),
    ("teams.assigned_users", "/api/teams/", "assigned_users"),
    ("teams.created_by", "/api/teams/", "created_by"),
]

IDS = [row[0] for row in ID_FILTERS]


@pytest.mark.django_db
@pytest.mark.parametrize("label,url,param", ID_FILTERS, ids=IDS)
class TestMalformedIdIsRejected:
    def test_malformed_id_answers_400(self, admin_client, label, url, param):
        for bad in MALFORMED:
            response = admin_client.get(f"{url}?{param}={bad}")
            assert response.status_code == status.HTTP_400_BAD_REQUEST, (
                f"{label} answered {response.status_code} for {param}={bad!r}; "
                "a malformed id must be a 400, not a crash"
            )

    def test_well_formed_id_is_still_accepted(self, admin_client, label, url, param):
        """The guard must not have turned a working filter into a 400.

        The id matches nothing, so this asserts the request is served, not that
        rows come back.
        """
        response = admin_client.get(f"{url}?{param}={WELL_FORMED}")
        assert response.status_code == status.HTTP_200_OK, (
            f"{label} answered {response.status_code} for a well-formed id"
        )

    def test_a_blank_value_means_no_filter(self, admin_client, label, url, param):
        """``?tags=`` is what a select with a blank first option submits.

        It has to mean "no filter", not "malformed id".
        """
        response = admin_client.get(f"{url}?{param}=")
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestKanbanBoardsRejectMalformedIds:
    """The board endpoints read a narrower param set than their list twins."""

    BOARDS = [
        ("/api/tasks/kanban/", "assigned_to"),
        ("/api/tasks/kanban/", "pipeline_id"),
        ("/api/cases/kanban/", "assigned_to"),
        ("/api/cases/kanban/", "account"),
        ("/api/opportunities/kanban/", "assigned_to"),
        ("/api/opportunities/kanban/", "tags"),
    ]

    @pytest.mark.parametrize("url,param", BOARDS)
    def test_malformed_id_answers_400(self, admin_client, url, param):
        response = admin_client.get(f"{url}?{param}=notauuid")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.parametrize("url,param", BOARDS)
    def test_well_formed_id_is_still_accepted(self, admin_client, url, param):
        response = admin_client.get(f"{url}?{param}={WELL_FORMED}")
        # `pipeline_id` names a record that has to exist, so 404 is a correct
        # answer there. What matters is that it parsed rather than crashed.
        assert response.status_code in (
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
        )


@pytest.mark.django_db
class TestSharedToAcceptsABareId:
    """``?shared_to=<id>`` used to be a 500 because only JSON text parsed."""

    def test_bare_id_is_accepted(self, admin_client):
        response = admin_client.get(f"/api/documents/?shared_to={WELL_FORMED}")
        assert response.status_code == status.HTTP_200_OK

    def test_json_array_is_still_accepted(self, admin_client):
        response = admin_client.get(f'/api/documents/?shared_to=["{WELL_FORMED}"]')
        assert response.status_code == status.HTTP_200_OK
