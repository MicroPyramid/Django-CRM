"""No route may answer 500 because an id in the path was not a UUID.

Every model here has a UUID primary key, and the routes used to capture those
ids with ``<str:pk>``. The raw string reached the view and went into an ``id``
lookup, where Django parses it while building the query and raises
``django.core.exceptions.ValidationError``. DRF does not translate that class,
so the request answered 500: 114 route/method combinations across roughly 50
views, reachable by anything as ordinary as a stale bookmark or a crawler
following ``/api/leads/undefined/``.

The fix is the ``uid`` path converter (``common/converters.py``), so this is a
sweep rather than a list: it walks the live URLconf, so a route added later
with ``<str:pk>`` fails here instead of shipping the old bug back. That is the
point of driving it from the resolver and not from a fixed list of paths.

``pack_id`` and the public ``token`` are deliberately still ``<str:...>``: one
is a registry key and the other a ``secrets.token_urlsafe`` string. Neither is
a UUID, and neither reaches a UUID column.
"""

import re

import pytest
from django.urls import get_resolver

MALFORMED = "not-a-uuid"

# Path params that are legitimately not UUIDs. Anything else must be `<uid:>`.
NON_UUID_PARAMS = {"token", "pack_id"}


def _routes():
    """Every leaf route in the live URLconf, with its full pattern and view."""
    found = []

    def walk(patterns, prefix=""):
        for entry in patterns:
            if hasattr(entry, "url_patterns"):
                walk(entry.url_patterns, prefix + str(entry.pattern))
            else:
                found.append((prefix + str(entry.pattern), entry.callback))

    walk(get_resolver().url_patterns)
    return found


def _id_routes():
    """Routes carrying at least one id segment, excluding the public portal."""
    out = []
    for route, callback in _routes():
        if "api/public/" in route:
            continue
        if "<uid:" not in route and "<str:" not in route:
            continue
        out.append((route, callback))
    return out


def test_no_id_param_is_still_captured_as_a_bare_string():
    """The converter is only a fix while every id route actually uses it."""
    offenders = [
        (route, name)
        for route, _ in _id_routes()
        for name in re.findall(r"<str:(\w+)>", route)
        if name not in NON_UUID_PARAMS
    ]
    assert offenders == [], (
        "these routes capture an id as a bare string, so a malformed id "
        f"reaches the ORM and answers 500: {offenders}"
    )


@pytest.mark.django_db
def test_no_route_answers_500_for_a_malformed_id(admin_client):
    """Drive every id-bearing route with an unparseable id."""
    failures = []
    for route, callback in _id_routes():
        url = "/" + re.sub(r"<\w+:(\w+)>", MALFORMED, route)
        view = getattr(callback, "cls", None)
        if view is None:
            continue
        for method in ("get", "post", "put", "patch", "delete"):
            if not hasattr(view, method):
                continue
            try:
                code = getattr(admin_client, method)(url, {}, format="json").status_code
            except Exception as exc:  # noqa: BLE001
                failures.append(
                    f"{method.upper()} {url} raised {type(exc).__name__}: {exc}"
                )
                continue
            if code >= 500:
                failures.append(f"{method.upper()} {url} answered {code}")
    assert failures == [], "routes that fail on a malformed id:\n" + "\n".join(failures)


@pytest.mark.django_db
class TestTheConverterAcceptsEveryFormTheORMAccepts:
    """A guard that rejects too much is the same defect facing the other way.

    ``uuid.UUID`` accepts bare hex, braced and URN forms and any case, and so
    does the ORM. Django's built-in ``uuid`` converter accepts only canonical
    lowercase, which is why it is not used here. A 404 in these cases would
    mean the fix broke requests that used to work.
    """

    @pytest.fixture
    def account(self, org_a):
        from accounts.models import Account

        return Account.objects.create(name="Converter Account", org=org_a)

    @pytest.mark.parametrize(
        "form",
        [
            "canonical",
            "uppercase",
            "bare_hex",
            "braced",
            "urn",
        ],
    )
    def test_form_resolves(self, admin_client, account, form):
        raw = account.id
        rendered = {
            "canonical": str(raw),
            "uppercase": str(raw).upper(),
            "bare_hex": raw.hex,
            "braced": f"{{{raw}}}",
            "urn": raw.urn,
        }[form]
        response = admin_client.get(f"/api/accounts/{rendered}/")
        assert response.status_code != 404, (
            f"the {form} form of a real id no longer resolves; the converter "
            "is stricter than the ORM"
        )


@pytest.mark.django_db
class TestWrongVerbOnTheCaseSolutionRoutes:
    """One view class, two routes, different captured kwargs.

    Django passes a route's kwargs to whichever method it dispatches, so
    ``DELETE`` on the collection route arrived missing ``solution_pk`` and
    ``POST`` on the member route arrived with one. Both were an uncaught
    ``TypeError``, so a client using the wrong verb got a 500 instead of a 405.
    A malformed id now 404s before reaching either, which would have hidden
    this: these use a well-formed id on purpose.
    """

    @pytest.fixture
    def case(self, org_a):
        from cases.models import Case

        return Case.objects.create(name="Converter Case", status="New", org=org_a)

    def test_delete_on_the_collection_route(self, admin_client, case):
        response = admin_client.delete(f"/api/cases/{case.id}/solutions/")
        assert response.status_code == 405, response.status_code

    def test_post_on_the_member_route(self, admin_client, case):
        response = admin_client.post(
            f"/api/cases/{case.id}/solutions/{case.id}/", {}, format="json"
        )
        assert response.status_code == 405, response.status_code
