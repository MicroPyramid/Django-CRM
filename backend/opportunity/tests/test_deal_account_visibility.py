"""A deal links only to an account its editor can open, as contacts and tickets do.

`OpportunityCreateSerializer.validate_account` asks `has_account_access` on
create, PUT and PATCH. An unknown id, another org's account and a hidden one
read the same, and the account a deal already has is kept whoever saves, since
the phone form sends it back on every edit.
"""

import uuid

import pytest

from accounts.models import Account
from conftest import rls_org
from opportunity.models import Opportunity

DEALS_URL = "/api/opportunities/"

pytestmark = pytest.mark.django_db


def _account(org, name, created_by=None):
    account = Account.objects.create(name=name, org=org)
    Account.objects.filter(pk=account.pk).update(created_by=created_by)
    return account


def _deal(org, name, created_by, account=None):
    deal = Opportunity.objects.create(name=name, org=org, account=account)
    Opportunity.objects.filter(pk=deal.pk).update(created_by=created_by)
    return deal


@pytest.fixture
def hidden(org_a, admin_user):
    return _account(org_a, "Hidden Holdings", created_by=admin_user)


@pytest.fixture
def assigned(org_a, admin_user, user_profile):
    account = _account(org_a, "Assigned Industries", created_by=admin_user)
    account.assigned_to.add(user_profile)
    return account


@pytest.fixture
def foreign(org_b, user_b):
    with rls_org(org_b):
        return _account(org_b, "Other Org Ltd", created_by=user_b)


@pytest.fixture
def superuser(regular_user):
    """The `user_client` caller, with a plain USER profile, made superuser."""
    regular_user.is_superuser = True
    regular_user.save(update_fields=["is_superuser"])
    return regular_user


@pytest.fixture
def mine(org_a, regular_user):
    return _deal(org_a, "Mine", regular_user)


@pytest.fixture
def mine_at_hidden(org_a, regular_user, hidden):
    """The member's own deal, linked by an admin to an account they cannot open."""
    return _deal(org_a, "Linked", regular_user, account=hidden)


def _create(client, name, account_id):
    return client.post(
        DEALS_URL, {"name": name, "account": str(account_id)}, format="json"
    )


def _refusal_errors(response):
    assert response.status_code == 400, response.content
    return response.json()["errors"]


def _refusal(response):
    return _refusal_errors(response)["account"]


class TestDealAccountLinkOnCreate:
    def test_member_may_link_an_account_they_are_assigned_to(
        self, user_client, assigned
    ):
        response = _create(user_client, "Assigned", assigned.id)
        assert response.status_code == 200, response.content
        assert Opportunity.objects.get(name="Assigned").account_id == assigned.id

    def test_member_may_link_an_account_they_created(
        self, user_client, org_a, regular_user
    ):
        own = _account(org_a, "Own Co", created_by=regular_user)
        response = _create(user_client, "Own", own.id)
        assert response.status_code == 200, response.content
        assert Opportunity.objects.get(name="Own").account_id == own.id

    def test_hidden_account_reads_like_an_unknown_id(self, user_client, hidden):
        hidden_refusal = _refusal(_create(user_client, "Hidden", hidden.id))
        unknown_refusal = _refusal(_create(user_client, "Unknown", uuid.uuid4()))
        assert hidden_refusal == unknown_refusal == ["No such account."]
        assert not Opportunity.objects.filter(name__in=["Hidden", "Unknown"]).exists()

    def test_malformed_account_id_is_a_400(self, user_client):
        response = user_client.post(
            DEALS_URL, {"name": "Garbled", "account": "not-a-uuid"}, format="json"
        )
        assert "account" in _refusal_errors(response)
        assert not Opportunity.objects.filter(name="Garbled").exists()

    def test_admin_may_link_any_account_in_the_org(self, admin_client, hidden):
        response = _create(admin_client, "Admin", hidden.id)
        assert response.status_code == 200, response.content
        assert Opportunity.objects.get(name="Admin").account_id == hidden.id

    def test_superuser_may_link_any_account_in_the_org(
        self, superuser, user_client, hidden
    ):
        response = _create(user_client, "Superuser", hidden.id)
        assert response.status_code == 200, response.content
        assert Opportunity.objects.get(name="Superuser").account_id == hidden.id

    @pytest.mark.parametrize("caller", ["member", "admin", "superuser"])
    def test_other_org_account_is_refused_for_everyone(
        self, caller, request, user_client, admin_client, foreign
    ):
        if caller == "superuser":
            request.getfixturevalue("superuser")
        client = admin_client if caller == "admin" else user_client
        assert _refusal(_create(client, "Foreign", foreign.id)) == ["No such account."]
        assert not Opportunity.objects.filter(name="Foreign").exists()


class TestDealAccountLinkOnEdit:
    def test_patch_may_not_move_a_deal_to_a_hidden_account(
        self, user_client, mine, hidden
    ):
        response = user_client.patch(
            f"{DEALS_URL}{mine.id}/", {"account": str(hidden.id)}, format="json"
        )
        assert _refusal(response) == ["No such account."]
        mine.refresh_from_db()
        assert mine.account_id is None

    def test_put_may_not_move_a_deal_to_a_hidden_account(
        self, user_client, mine, hidden
    ):
        response = user_client.put(
            f"{DEALS_URL}{mine.id}/",
            {"name": "Mine", "account": str(hidden.id)},
            format="json",
        )
        assert _refusal(response) == ["No such account."]
        mine.refresh_from_db()
        assert mine.account_id is None

    def test_patch_may_move_a_deal_to_an_account_the_member_can_open(
        self, user_client, mine, assigned
    ):
        response = user_client.patch(
            f"{DEALS_URL}{mine.id}/", {"account": str(assigned.id)}, format="json"
        )
        assert response.status_code == 200, response.content
        mine.refresh_from_db()
        assert mine.account_id == assigned.id

    def test_patch_may_not_move_a_deal_to_another_org_account_even_as_admin(
        self, admin_client, mine, foreign
    ):
        response = admin_client.patch(
            f"{DEALS_URL}{mine.id}/", {"account": str(foreign.id)}, format="json"
        )
        assert _refusal(response) == ["No such account."]
        mine.refresh_from_db()
        assert mine.account_id is None

    def test_patch_resending_a_stored_hidden_account_keeps_it(
        self, user_client, hidden, mine_at_hidden
    ):
        # What the phone form does: it sends `account` on every save.
        response = user_client.patch(
            f"{DEALS_URL}{mine_at_hidden.id}/",
            {"description": "Renewal", "account": str(hidden.id)},
            format="json",
        )
        assert response.status_code == 200, response.content
        mine_at_hidden.refresh_from_db()
        assert mine_at_hidden.description == "Renewal"
        assert mine_at_hidden.account_id == hidden.id

    def test_put_resending_a_stored_hidden_account_keeps_it(
        self, user_client, hidden, mine_at_hidden
    ):
        response = user_client.put(
            f"{DEALS_URL}{mine_at_hidden.id}/",
            {"name": "Linked", "description": "Renewal", "account": str(hidden.id)},
            format="json",
        )
        assert response.status_code == 200, response.content
        mine_at_hidden.refresh_from_db()
        assert mine_at_hidden.account_id == hidden.id

    def test_patch_may_clear_the_account(self, user_client, mine_at_hidden):
        response = user_client.patch(
            f"{DEALS_URL}{mine_at_hidden.id}/", {"account": None}, format="json"
        )
        assert response.status_code == 200, response.content
        mine_at_hidden.refresh_from_db()
        assert mine_at_hidden.account_id is None

    def test_picker_offers_exactly_what_the_save_path_accepts(
        self, user_client, assigned, hidden
    ):
        # The web deal form builds its account picker from this list.
        body = user_client.get(f"{DEALS_URL}?limit=1").json()
        offered = {row["id"] for row in body["accounts_list"]}
        assert str(assigned.id) in offered
        assert str(hidden.id) not in offered
