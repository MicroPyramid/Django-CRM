"""Two routes the middleware cannot gate: the anonymous calendar feed, which
answers its unknown-link 404 while Tasks is off, and the knowledge base's
settings under the exempt ``/api/org/`` prefix, which answers the signed-in
module 404 on every method."""

from urllib.parse import urlparse

import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from common.models import CalendarFeedToken
from common.modules import module_off_body
from common.testing import set_modules_off

HELP_CENTER = "/api/org/help-center/"
SLUG_CHANGE = {"help_center_enabled": True, "help_center_slug": "acme"}
METHODS = ("get", "head", "options", "post", "put", "patch", "delete")


@pytest.fixture(autouse=True)
def _fresh_throttle():
    cache.clear()
    yield
    cache.clear()


def test_calendar_feed_closes_with_tasks(user_client, org_a):
    created = user_client.post("/api/profile/calendar-feed/")
    assert created.status_code == 201
    feed = urlparse(created.json()["url"]).path
    anon = APIClient()
    assert anon.get(feed).status_code == 200
    CalendarFeedToken.objects.update(last_used_at=None)
    unknown = anon.get("/api/public/calendar/nope.ics")
    assert (unknown.status_code, unknown.json()) == (404, {"error": "Not found"})

    set_modules_off(org_a, "tasks")
    response = anon.get(feed)
    assert (response.status_code, response.content) == (404, unknown.content)
    assert CalendarFeedToken.objects.get().last_used_at is None

    set_modules_off(org_a)
    assert anon.get(feed).status_code == 200


def _help_center_unchanged(org):
    org.refresh_from_db()
    return (org.help_center_enabled, org.help_center_slug) == (False, None)


def test_help_center_settings_answer_module_off(
    admin_client, user_client, unauthenticated_client, org_a
):
    assert admin_client.get(HELP_CENTER).status_code == 200
    assert user_client.get(HELP_CENTER).status_code == 200
    refused = user_client.patch(HELP_CENTER, SLUG_CHANGE, format="json")
    assert refused.status_code == 403

    set_modules_off(org_a, "knowledge_base")
    off = (404, module_off_body(org_a, "knowledge_base"))
    for client in (admin_client, user_client):
        response = client.get(HELP_CENTER)
        assert (response.status_code, response.json()) == off
        response = client.patch(HELP_CENTER, SLUG_CHANGE, format="json")
        assert (response.status_code, response.json()) == off
    assert _help_center_unchanged(org_a)
    assert unauthenticated_client.get(HELP_CENTER).status_code == 403

    set_modules_off(org_a)
    assert user_client.get(HELP_CENTER).status_code == 200
    saved = admin_client.patch(HELP_CENTER, SLUG_CHANGE, format="json")
    assert saved.status_code == 200


@pytest.mark.parametrize("method", METHODS)
def test_help_center_settings_answer_one_404_for_every_method(
    admin_client, org_a, method
):
    set_modules_off(org_a, "knowledge_base")
    send = getattr(admin_client, method)
    if method in ("get", "head"):
        response = send(HELP_CENTER)
    else:
        response = send(HELP_CENTER, SLUG_CHANGE, format="json")
    assert response.status_code == 404
    if method == "head":
        assert response.content == b""
    else:
        assert response.json() == module_off_body(org_a, "knowledge_base")
    assert _help_center_unchanged(org_a)
