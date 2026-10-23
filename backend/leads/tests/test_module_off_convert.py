"""Converting a lead while Deals is off: the account and contact are made, no
deal is, and every entry point answers with no deal id."""

from unittest.mock import patch

import pytest

from accounts.models import Account
from common.testing import set_modules_off
from contacts.models import Contact
from leads.models import Lead
from opportunity.models import Opportunity

pytestmark = pytest.mark.django_db

URL = "/api/leads/"
EMAIL = "lee@convert.test"
BODY = {
    "first_name": "Lee",
    "last_name": "Ad",
    "email": EMAIL,
    "company_name": "Convert Co",
}


@pytest.fixture(autouse=True)
def _no_mail():
    with patch("leads.views.lead_views.send_email_to_assigned_user.delay"):
        yield


@pytest.fixture
def lead(org_a):
    return Lead.objects.create(org=org_a, status="in process", **BODY)


def _convert(client, how, lead):
    if how == "create":
        return client.post(
            URL,
            {
                **BODY,
                "email": "new@convert.test",
                "title": "Fresh",
                "status": "converted",
            },
            format="json",
        )
    if how == "put":
        return client.put(
            f"{URL}{lead.id}/",
            {**BODY, "title": "Converted", "status": "converted"},
            format="json",
        )
    return client.patch(f"{URL}{lead.id}/", {"status": "converted"}, format="json")


@pytest.mark.parametrize("how", ["create", "put", "patch"])
def test_converting_with_deals_off_creates_no_deal(admin_client, org_a, lead, how):
    set_modules_off(org_a, "deals")

    response = _convert(admin_client, how, lead)

    assert response.status_code == 200, response.content
    body = response.json()
    assert body["opportunity_id"] is None
    assert Account.objects.filter(id=body["account_id"], org=org_a).exists()
    assert Contact.objects.filter(id=body["contact_id"], org=org_a).exists()
    assert not Opportunity.objects.filter(org=org_a).exists()


@pytest.mark.parametrize("how", ["create", "put", "patch"])
def test_converting_with_deals_on_creates_a_deal_as_before(
    admin_client, org_a, lead, how
):
    response = _convert(admin_client, how, lead)

    assert response.status_code == 200, response.content
    deal = Opportunity.objects.get(org=org_a)
    assert response.json()["opportunity_id"] == str(deal.id)
