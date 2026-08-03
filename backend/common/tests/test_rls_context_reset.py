"""The RLS context reset must survive an exception in the view.

`app.current_org` is set with ``set_config(..., false)``, i.e. SESSION scope.
It outlives the statement, the transaction, and the failed request. The only
thing that clears it is the middleware's own reset call.

Before pooling, `CONN_MAX_AGE=0` closed the connection at the end of every
request, so a skipped reset was invisible. Once connections are reused (a
psycopg pool, persistent connections, or a session-mode external pooler), a
skipped reset hands the next borrower a connection still scoped to the
previous tenant, and RLS happily serves them that tenant's rows.

These tests run on SQLite because they assert the *control flow*, that reset is
called on the exception path, not the SQL. The end-to-end proof that a returned
connection carries no context lives in ``test_pool_rls_isolation.py`` and needs
a real PostgreSQL with a non-superuser role.
"""

import pytest

from common.middleware.rls_context import RequireOrgContext, SetOrgContext


class _Boom(Exception):
    pass


class _FakeOrg:
    id = "11111111-1111-1111-1111-111111111111"


class _FakeRequest:
    def __init__(self, path="/api/leads/"):
        self.path = path
        self.org = _FakeOrg()


def _instrument(middleware_cls, get_response):
    """Build the middleware with set/reset replaced by call recorders."""
    calls = []
    mw = middleware_cls(get_response)
    mw._set_org_context = lambda request: calls.append("set")
    mw._reset_org_context = lambda: calls.append("reset")
    return mw, calls


@pytest.mark.parametrize("middleware_cls", [SetOrgContext, RequireOrgContext])
def test_reset_runs_on_the_happy_path(middleware_cls):
    mw, calls = _instrument(middleware_cls, lambda request: "response")

    assert mw(_FakeRequest()) == "response"
    assert calls == ["set", "reset"]


@pytest.mark.parametrize("middleware_cls", [SetOrgContext, RequireOrgContext])
def test_reset_runs_when_the_view_raises(middleware_cls):
    """The regression this file exists for.

    Without the try/finally the middleware returned early on the exception and
    `app.current_org` stayed set on the connection.
    """

    def boom(request):
        raise _Boom("view exploded")

    mw, calls = _instrument(middleware_cls, boom)

    with pytest.raises(_Boom):
        mw(_FakeRequest())

    assert calls == ["set", "reset"], (
        "org context was not cleared after the view raised: the connection "
        "goes back to the pool still scoped to this tenant"
    )


@pytest.mark.parametrize("middleware_cls", [SetOrgContext, RequireOrgContext])
def test_the_exception_still_propagates(middleware_cls):
    """The finally must not swallow the error into a silent 200."""

    def boom(request):
        raise _Boom("view exploded")

    mw, _ = _instrument(middleware_cls, boom)

    with pytest.raises(_Boom, match="view exploded"):
        mw(_FakeRequest())


def test_require_org_context_resets_after_an_exempt_path_raises():
    """Exempt paths skip the 403 check but still run set/reset around the view.

    `/api/public/invoice/` is anonymous, so `_set_org_context` returns early
    and leaves the context empty. The reset still has to run: an exempt request
    can be handled on a connection a previous tenant's request left dirty, and
    clearing on the way out is what stops that spreading further.
    """

    def boom(request):
        raise _Boom("public view exploded")

    mw, calls = _instrument(RequireOrgContext, boom)
    request = _FakeRequest(path="/api/public/invoice/abc123/")

    with pytest.raises(_Boom):
        mw(request)

    assert calls == ["set", "reset"]
