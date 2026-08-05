"""The HSTS settings only do anything when Django can tell the request was HTTPS.

``crm/settings.py`` has set ``SECURE_HSTS_SECONDS = 31536000`` with
``INCLUDE_SUBDOMAINS`` and ``PRELOAD`` for a long time, and every one of them was
inert in production. ``SecurityMiddleware`` emits the header only when
``request.is_secure()`` is true, and behind a TLS-terminating proxy the request
reaches Django over plain HTTP, so ``is_secure()`` was false on every request and
no ``Strict-Transport-Security`` header was ever sent.

``SECURE_PROXY_SSL_HEADER`` is what closes that, and it is opt-in via
``TRUST_PROXY_SSL_HEADER`` because it makes Django believe a request header. The
tests below pin both directions: the header appears once the setting is on, and
turning it on does not make Django trust plain HTTP or emit the header
unconditionally.
"""

import importlib

import pytest
from django.http import HttpResponse
from django.middleware.security import SecurityMiddleware
from django.test import RequestFactory, override_settings

PROXY_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")


def _response_for(**extra):
    """Run one GET through a freshly built ``SecurityMiddleware``.

    Built inside the call because ``SecurityMiddleware.__init__`` snapshots the
    security settings, so an instance created before ``override_settings`` would
    carry the wrong ``sts_seconds``.
    """
    middleware = SecurityMiddleware(lambda request: HttpResponse("ok"))
    return middleware(RequestFactory().get("/", **extra))


class TestHSTSHeaderBehindAProxy:
    @override_settings(SECURE_PROXY_SSL_HEADER=None)
    def test_no_hsts_header_when_the_proxy_setting_is_absent(self):
        """The defect. A proxy says HTTPS and Django sends nothing."""
        response = _response_for(HTTP_X_FORWARDED_PROTO="https")
        assert "Strict-Transport-Security" not in response

    @override_settings(SECURE_PROXY_SSL_HEADER=PROXY_HEADER)
    def test_hsts_header_present_when_the_proxy_setting_is_set(self):
        response = _response_for(HTTP_X_FORWARDED_PROTO="https")
        header = response["Strict-Transport-Security"]
        assert "max-age=31536000" in header
        assert "includeSubDomains" in header
        assert "preload" in header

    @override_settings(SECURE_PROXY_SSL_HEADER=PROXY_HEADER)
    def test_no_hsts_header_when_the_proxy_reports_plain_http(self):
        """Trusting the header is not the same as assuming HTTPS."""
        response = _response_for(HTTP_X_FORWARDED_PROTO="http")
        assert "Strict-Transport-Security" not in response

    @override_settings(SECURE_PROXY_SSL_HEADER=PROXY_HEADER)
    def test_no_hsts_header_when_no_proxy_header_is_sent_at_all(self):
        response = _response_for()
        assert "Strict-Transport-Security" not in response


class TestIsSecureReflectsTheSetting:
    """``request.is_secure()`` is the fact the whole thing turns on.

    Anything else that branches on it (a redirect, a cookie flag, a link
    scheme) inherits the same behaviour, which is why it is asserted directly.
    """

    @override_settings(SECURE_PROXY_SSL_HEADER=None)
    def test_forwarded_proto_is_ignored_when_untrusted(self):
        request = RequestFactory().get("/", HTTP_X_FORWARDED_PROTO="https")
        assert request.is_secure() is False

    @override_settings(SECURE_PROXY_SSL_HEADER=PROXY_HEADER)
    def test_forwarded_proto_is_honoured_when_trusted(self):
        request = RequestFactory().get("/", HTTP_X_FORWARDED_PROTO="https")
        assert request.is_secure() is True


@pytest.fixture
def reloaded_settings(monkeypatch):
    """Re-execute ``crm.settings`` under a chosen ``TRUST_PROXY_SSL_HEADER``.

    Reloading is safe here: ``django.conf.settings`` copied its values at setup
    and does not track the module object, so nothing the rest of the suite reads
    changes. The module is reloaded once more on teardown so its own attributes
    match the ambient environment again.
    """
    import crm.settings

    def _reload(value):
        if value is None:
            monkeypatch.delenv("TRUST_PROXY_SSL_HEADER", raising=False)
        else:
            monkeypatch.setenv("TRUST_PROXY_SSL_HEADER", value)
        return importlib.reload(crm.settings)

    yield _reload
    monkeypatch.undo()
    importlib.reload(crm.settings)


class TestTheEnvironmentGate:
    def test_absent_variable_leaves_the_setting_undefined(self, reloaded_settings):
        module = reloaded_settings(None)
        assert not hasattr(module, "SECURE_PROXY_SSL_HEADER")

    @pytest.mark.parametrize("value", ["False", "false", "0", "no", ""])
    def test_falsy_values_leave_the_setting_undefined(self, reloaded_settings, value):
        """Only the literal word "true" turns it on.

        The gate compares against ``"true"`` rather than testing truthiness of
        the string, so "0" and "no" stay off instead of reading as non-empty.
        """
        module = reloaded_settings(value)
        assert not hasattr(module, "SECURE_PROXY_SSL_HEADER")

    @pytest.mark.parametrize("value", ["True", "true", "TRUE"])
    def test_true_in_any_casing_sets_the_header_tuple(self, reloaded_settings, value):
        module = reloaded_settings(value)
        assert module.SECURE_PROXY_SSL_HEADER == PROXY_HEADER
