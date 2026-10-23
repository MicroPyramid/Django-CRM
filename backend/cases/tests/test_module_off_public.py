"""Public, portal and inbound case entry points while a module is off.

People outside the org reach these, so an off module answers exactly what an
unknown link already gets, and the same request answers as before once the
module is back on.
"""

import uuid
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth.hashers import make_password
from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APIClient

from cases.models import Case, CsatSurvey, EmailMessage, InboundMailbox, Solution
from cases.tasks import csat_signer, hash_csat_token, send_csat_survey
from common.models import Comment, PortalLoginToken
from common.portal_auth import mint_portal_token
from common.portal_tokens import register_portal_token_hash
from common.testing import rls_org, set_modules_off
from contacts.models import Contact

SLUG = "acme-help"
SNS_TOPIC = "arn:aws:sns:us-east-1:123456789012:acme-inbound"
RAW_EMAIL = (
    "From: Customer <user@example.com>\r\n"
    "To: support@acme.com\r\n"
    "Subject: Help with login\r\n"
    "Date: Sat, 9 May 2026 12:00:00 +0000\r\n"
    "Message-ID: <m1@example.com>\r\n"
    "MIME-Version: 1.0\r\n"
    'Content-Type: text/plain; charset="utf-8"\r\n'
    "\r\n"
    "I cannot log in."
)


@pytest.fixture(autouse=True)
def _fresh_throttle():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def anon():
    return APIClient()


@pytest.fixture
def pat(org_a):
    return Contact.objects.create(
        org=org_a, first_name="Pat", last_name="Smith", email="pat@example.com"
    )


@pytest.fixture
def portal(pat):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {mint_portal_token(pat)}")
    return client


@pytest.fixture
def article(org_a):
    with rls_org(org_a):
        return Solution.objects.create(
            org=org_a,
            title="Resetting your password",
            description="Open settings, choose security, then reset.",
            status="approved",
            is_published=True,
        )


def _answer(response):
    return response.status_code, response.json()


def test_help_center_closes_with_the_knowledge_base(anon, org_a, article):
    org_a.help_center_slug = SLUG
    org_a.help_center_enabled = True
    org_a.save()
    urls = (
        f"/api/public/help/{SLUG}/",
        f"/api/public/help/{SLUG}/articles/{article.id}/",
    )
    unknown = _answer(anon.get("/api/public/help/no-such-help/"))
    assert unknown == (404, {"error": "Not found"})

    set_modules_off(org_a, "knowledge_base")
    for url in urls:
        assert _answer(anon.get(url)) == unknown

    set_modules_off(org_a)
    for url in urls:
        assert anon.get(url).status_code == 200


def test_csat_link_answers_its_expired_answer(client, org_a, pat):
    case = Case.objects.create(
        org=org_a,
        name="Login bug",
        status="Closed",
        priority="Normal",
        closed_on=timezone.localdate(),
        resolved_at=timezone.now(),
    )
    case.contacts.add(pat)
    send_csat_survey(str(case.id), str(org_a.id))
    survey = CsatSurvey.objects.get(case=case)
    token = csat_signer().sign(str(case.id))
    survey.token_hash = hash_csat_token(token)
    survey.save(update_fields=["token_hash"])
    register_portal_token_hash(survey.token_hash, org_a.id, "csat", survey.id)
    url = f"/api/public/csat/{token}/"
    unknown = _answer(client.get(f"/api/public/csat/{csat_signer().sign('ghost')}/"))
    assert unknown == (410, {"error": "Survey link is no longer valid."})

    set_modules_off(org_a, "tickets")
    assert _answer(client.get(url)) == unknown
    posted = client.post(url, {"rating": 5}, content_type="application/json")
    assert _answer(posted) == unknown
    survey.refresh_from_db()
    assert (survey.rating, survey.responded_at) == (None, None)

    set_modules_off(org_a)
    assert client.get(url).status_code == 200
    posted = client.post(url, {"rating": 5}, content_type="application/json")
    assert posted.status_code == 200
    survey.refresh_from_db()
    assert survey.rating == 5


def test_portal_cases_close_with_tickets(portal, org_a, pat):
    case = Case.objects.create(org=org_a, name="Login broken", status="New")
    case.contacts.add(pat)
    detail = f"/api/portal/cases/{case.id}/"
    comment = f"{detail}comment/"
    unknown = _answer(portal.get(f"/api/portal/cases/{uuid.uuid4()}/"))
    assert unknown == (404, {"error": "Case not found"})

    set_modules_off(org_a, "tickets")
    assert _answer(portal.get("/api/portal/cases/")) == unknown
    created = portal.post("/api/portal/cases/", {"name": "New one"}, format="json")
    assert _answer(created) == unknown
    assert _answer(portal.get(detail)) == unknown
    assert _answer(portal.post(comment, {"comment": "Hi"}, format="json")) == unknown
    assert list(Case.objects.filter(org=org_a)) == [case]
    assert not Comment.objects.filter(object_id=case.id).exists()

    set_modules_off(org_a)
    assert portal.get("/api/portal/cases/").status_code == 200
    assert portal.get(detail).status_code == 200
    assert portal.post(comment, {"comment": "Hi"}, format="json").status_code == 201


def test_portal_articles_close_with_the_knowledge_base(portal, org_a, article):
    detail = f"/api/portal/articles/{article.id}/"
    suggest = "/api/portal/articles/suggest/?q=password"
    unknown = _answer(portal.get(f"/api/portal/articles/{uuid.uuid4()}/"))
    assert unknown == (404, {"error": "Article not found"})

    set_modules_off(org_a, "knowledge_base")
    assert _answer(portal.get("/api/portal/articles/")) == unknown
    assert _answer(portal.get(detail)) == unknown
    nothing = _answer(portal.get("/api/portal/articles/suggest/?q="))
    assert _answer(portal.get(suggest)) == nothing == (200, {"articles": []})

    set_modules_off(org_a)
    listed = portal.get("/api/portal/articles/").json()["articles"]
    assert [a["id"] for a in listed] == [str(article.id)]
    assert portal.get(detail).status_code == 200
    assert [a["id"] for a in portal.get(suggest).json()["articles"]] == [
        str(article.id)
    ]


def test_portal_sign_in_still_works_with_both_off(org_a, pat):
    """Pin: sign-in is core, so it passed before the module checks existed."""
    set_modules_off(org_a, "tickets", "knowledge_base")
    requested = APIClient().post(
        f"/api/portal/login/{org_a.id}/request/",
        {"email": "pat@example.com"},
        format="json",
    )
    assert requested.status_code == 200
    assert PortalLoginToken.objects.filter(contact=pat).count() == 1

    PortalLoginToken.objects.filter(contact=pat).update(
        code_hash=make_password("123456"),
        expires_at=timezone.now() + timedelta(minutes=10),
    )
    verified = APIClient().post(
        f"/api/portal/login/{org_a.id}/verify/",
        {"email": "pat@example.com", "code": "123456"},
        format="json",
    )
    assert verified.status_code == 200
    assert verified.json()["access_token"]


def test_inbound_email_answers_not_found_while_tickets_is_off(anon, org_a):
    with rls_org(org_a):
        mailbox = InboundMailbox.objects.create(
            org=org_a,
            address="support@acme.com",
            provider="ses",
            topic_arn=SNS_TOPIC,
            is_active=True,
        )
    notification = {
        "Type": "Notification",
        "Message": RAW_EMAIL,
        "Signature": "x",
        "SigningCertURL": "x",
        "SignatureVersion": "1",
        "TopicArn": SNS_TOPIC,
    }
    url = f"/api/cases/inbound/{mailbox.id}/"
    with patch("cases.inbound_views.verify_sns_message"):
        unknown = _answer(
            anon.post(
                f"/api/cases/inbound/{uuid.uuid4()}/", notification, format="json"
            )
        )
        assert unknown == (404, {"error": True, "errors": "Mailbox not found"})

        set_modules_off(org_a, "tickets")
        assert _answer(anon.post(url, notification, format="json")) == unknown
        assert not Case.objects.filter(org=org_a).exists()
        assert not EmailMessage.objects.filter(org=org_a).exists()

        set_modules_off(org_a)
        response = anon.post(url, notification, format="json")
    assert response.status_code == 200, response.content
    assert Case.objects.filter(org=org_a).count() == 1
