"""Detail routes answer 404 for an id that is missing or malformed, never 500.

`common.lookups.get_scoped_or_404` replaced the `objects.get(pk=pk, org=...)`
shape that six `get_object` helpers shared. That spelling failed two ways a
caller can trigger by accident:

* a deleted record, or one belonging to another tenant, raised `DoesNotExist`,
  which nothing caught, so the view answered 500;
* `id` is a UUID column, so a non-UUID id raised `ValidationError` while the
  query was built. DRF does not translate that class either, so a stale
  bookmark or a hand-edited URL also answered 500.

A previous sweep closed this class at 154 call sites and missed this shape,
because the sweep looked at the ORM calls inside view methods and these live in
a one-line helper. That is why this file drives the routes rather than the
helper: a unit test of `get_scoped_or_404` would not have caught the six views
that were not using it.
"""

import uuid

import pytest

# (method, url template). Each of these went through a `get_object(self, pk)`
# helper that used `objects.get(pk=pk, org=...)`.
ROUTES = [
    ("put", "/api/leads/comment/{}/"),
    ("patch", "/api/leads/comment/{}/"),
    ("delete", "/api/leads/comment/{}/"),
    ("put", "/api/opportunities/comment/{}/"),
    ("patch", "/api/opportunities/comment/{}/"),
    ("delete", "/api/opportunities/comment/{}/"),
    ("put", "/api/accounts/comment/{}/"),
    ("delete", "/api/accounts/comment/{}/"),
    ("delete", "/api/leads/attachment/{}/"),
    ("delete", "/api/opportunities/attachment/{}/"),
    ("get", "/api/tags/{}/"),
    ("delete", "/api/tags/{}/"),
    ("get", "/api/teams/{}/"),
    ("delete", "/api/teams/{}/"),
]


@pytest.mark.django_db
@pytest.mark.parametrize("method,template", ROUTES)
def test_missing_id_is_404(admin_client, method, template):
    """A well-formed id for a record that does not exist."""
    resp = getattr(admin_client, method)(template.format(uuid.uuid4()), {})
    assert resp.status_code == 404, resp.content


@pytest.mark.django_db
@pytest.mark.parametrize("method,template", ROUTES)
def test_malformed_id_is_404(admin_client, method, template):
    """An id that is not a UUID at all. This used to reach the ORM and 500."""
    resp = getattr(admin_client, method)(template.format("not-a-uuid"), {})
    assert resp.status_code == 404, resp.content
