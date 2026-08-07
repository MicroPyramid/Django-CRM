"""Accepting an estimate is a transition, not a field edit.

``PublicEstimateAcceptView`` treats it as one: the estimate must be in ``Sent``
or ``Viewed``, must not have expired, and the acceptor must give a name and a
valid email, which are recorded along with their IP and user agent. Accepting a
quote authorises its price, so those checks are the point of the endpoint.

``EstimateCreateSerializer`` also backs ``PUT /api/invoices/estimates/<id>/``
with ``partial=True``, and it left ``status`` writable. Any member with access
to the estimate could therefore send ``{"status": "Accepted"}`` and skip every
one of those checks, landing an Accepted estimate with no ``accepted_at``, no
acceptor and no invoice behind it. ``InvoiceCreateSerializer`` has always
marked ``status`` read-only; estimates were the asymmetry.

Both directions are covered: the transition is refused through the generic
edit, and still works through the endpoint that guards it.
"""

import datetime

import pytest
from django.utils import timezone
from rest_framework import status

from invoices.models import Estimate


def _estimate(org, **kwargs):
    defaults = {
        "title": "Quote for services",
        "status": "Sent",
        "currency": "USD",
        "issue_date": timezone.localdate(),
        "expiry_date": timezone.localdate() + datetime.timedelta(days=30),
        "public_link_enabled": True,
        "org": org,
    }
    defaults.update(kwargs)
    return Estimate.objects.create(**defaults)


@pytest.fixture
def estimate(org_a):
    return _estimate(org_a)


@pytest.mark.django_db
class TestStatusIsNotWritableThroughTheGenericEdit:
    def test_put_cannot_accept_an_estimate(self, admin_client, estimate):
        response = admin_client.put(
            f"/api/invoices/estimates/{estimate.id}/",
            {"status": "Accepted"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        estimate.refresh_from_db()
        assert estimate.status == "Sent", (
            "an estimate was accepted through the generic edit, skipping the "
            "expiry check and the acceptor record"
        )
        assert estimate.accepted_at is None

    def test_put_cannot_accept_a_draft(self, admin_client, org_a):
        """The public path refuses Draft as a source state. So must this one."""
        draft = _estimate(org_a, status="Draft", title="Not yet sent")
        admin_client.put(
            f"/api/invoices/estimates/{draft.id}/",
            {"status": "Accepted"},
            format="json",
        )
        draft.refresh_from_db()
        assert draft.status == "Draft"

    def test_put_cannot_accept_an_expired_estimate(self, admin_client, org_a):
        expired = _estimate(
            org_a,
            title="Stale quote",
            expiry_date=timezone.localdate() - datetime.timedelta(days=1),
        )
        admin_client.put(
            f"/api/invoices/estimates/{expired.id}/",
            {"status": "Accepted"},
            format="json",
        )
        expired.refresh_from_db()
        assert expired.status == "Sent"

    def test_ordinary_edits_through_the_same_put_still_work(
        self, admin_client, estimate
    ):
        """The True direction: the guard must not have frozen the whole record."""
        response = admin_client.put(
            f"/api/invoices/estimates/{estimate.id}/",
            {"title": "Revised quote", "notes": "Second draft"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        estimate.refresh_from_db()
        assert estimate.title == "Revised quote"
        assert estimate.notes == "Second draft"

    def test_a_status_sent_alongside_a_real_edit_is_dropped(
        self, admin_client, estimate
    ):
        """The edit lands; only the status rides along and is discarded."""
        admin_client.put(
            f"/api/invoices/estimates/{estimate.id}/",
            {"title": "Revised quote", "status": "Accepted"},
            format="json",
        )
        estimate.refresh_from_db()
        assert estimate.title == "Revised quote"
        assert estimate.status == "Sent"


@pytest.mark.django_db
class TestTheGuardedPathStillAccepts:
    """The endpoint that does enforce the rules is untouched."""

    def test_public_accept_still_works(self, estimate):
        from rest_framework.test import APIClient

        response = APIClient().post(
            f"/api/public/estimate/{estimate.public_token}/accept/",
            {"name": "Dana Client", "email": "dana@example.com"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        estimate.refresh_from_db()
        assert estimate.status == "Accepted"
        assert estimate.accepted_at is not None
        assert estimate.accepted_by_email == "dana@example.com"

    def test_public_accept_still_refuses_an_expired_estimate(self, org_a):
        from rest_framework.test import APIClient

        expired = _estimate(
            org_a,
            title="Stale quote",
            expiry_date=timezone.localdate() - datetime.timedelta(days=1),
        )
        response = APIClient().post(
            f"/api/public/estimate/{expired.public_token}/accept/",
            {"name": "Dana Client", "email": "dana@example.com"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        expired.refresh_from_db()
        assert expired.status == "Sent"
