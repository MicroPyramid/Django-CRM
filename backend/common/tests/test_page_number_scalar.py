"""`page_number` is a number in every list response.

`page_number = (int(self.offset / 10) + 1,)` at five sites. The trailing comma
makes it a one-element tuple, so every one of these endpoints answered
`"page_number": [1]` while four of the five declared `IntegerField` in their
own OpenAPI schema. The fifth had been changed to `ListField` to agree with the
bug, which is how a defect becomes a documented contract.

Driven through the endpoints rather than asserted on the expression, because the
thing that was wrong is what clients received.
"""

import pytest

LIST_ENDPOINTS = [
    "/api/leads/",
    "/api/contacts/",
    "/api/opportunities/",
    "/api/accounts/",
    "/api/teams/",
]


@pytest.mark.django_db
@pytest.mark.parametrize("url", LIST_ENDPOINTS)
def test_page_number_is_an_integer(admin_client, url):
    resp = admin_client.get(url)
    assert resp.status_code == 200, resp.content
    body = resp.json()
    assert "page_number" in body, sorted(body)
    assert isinstance(body["page_number"], int), body["page_number"]
    assert body["page_number"] == 1
