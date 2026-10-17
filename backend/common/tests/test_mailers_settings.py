"""``MAILERS`` is built from the ``EMAIL_*`` environment variables.

Django 6.1 deprecates the flat ``EMAIL_BACKEND`` / ``EMAIL_HOST`` / ... settings,
so ``crm/settings.py`` reads the same variable names into ``MAILERS["default"]``
instead. Connection ``OPTIONS`` exist only for the SMTP backend: a mailer
configured through ``MAILERS`` rejects options its backend does not take, so a
stray ``EMAIL_HOST`` next to the console or SES backend would stop every send.
The tests below pin that, the ``localhost`` fallback for an unset or empty
``EMAIL_HOST``, and the two options left out when empty (``EMAIL_PORT``,
``EMAIL_TIMEOUT``) so Django picks the port from ``EMAIL_USE_TLS`` /
``EMAIL_USE_SSL`` instead of being handed 0.
"""

import importlib

import pytest

SMTP = "django.core.mail.backends.smtp.EmailBackend"
CONSOLE = "django.core.mail.backends.console.EmailBackend"

EMAIL_VARS = (
    "EMAIL_BACKEND",
    "EMAIL_HOST",
    "EMAIL_PORT",
    "EMAIL_HOST_USER",
    "EMAIL_HOST_PASSWORD",
    "EMAIL_USE_TLS",
    "EMAIL_USE_SSL",
    "EMAIL_TIMEOUT",
)


@pytest.fixture
def reloaded_settings(monkeypatch):
    """Re-execute ``crm.settings`` with exactly the given ``EMAIL_*`` variables.

    Every other ``EMAIL_*`` variable is removed, and ``load_dotenv`` is stubbed
    out so a developer's own ``.env`` cannot fill them back in. Reloading is safe
    for the same reason as in ``test_hsts_behind_proxy.py``: ``django.conf.settings``
    copied its values at setup and does not track the module object. The module
    is reloaded once more on teardown so its attributes match the ambient
    environment again.
    """
    import dotenv

    import crm.settings

    def _reload(**env):
        monkeypatch.setattr(dotenv, "load_dotenv", lambda *args, **kwargs: None)
        for name in EMAIL_VARS:
            monkeypatch.delenv(name, raising=False)
        for name, value in env.items():
            monkeypatch.setenv(name, value)
        return importlib.reload(crm.settings)

    yield _reload
    monkeypatch.undo()
    importlib.reload(crm.settings)


class TestNonSmtpBackends:
    def test_unset_backend_is_console_with_no_options(self, reloaded_settings):
        module = reloaded_settings()
        assert module.MAILERS == {"default": {"BACKEND": CONSOLE}}

    @pytest.mark.parametrize("backend", [CONSOLE, "django_ses.SESBackend"])
    def test_smtp_variables_are_ignored_for_other_backends(
        self, reloaded_settings, backend
    ):
        """A leftover SMTP host must not reach a backend that rejects it."""
        module = reloaded_settings(
            EMAIL_BACKEND=backend,
            EMAIL_HOST="sandbox.smtp.mailtrap.io",
            EMAIL_PORT="2525",
        )
        assert module.MAILERS == {"default": {"BACKEND": backend}}


class TestSmtpOptions:
    def test_every_variable_lands_in_options(self, reloaded_settings):
        module = reloaded_settings(
            EMAIL_BACKEND=SMTP,
            EMAIL_HOST="sandbox.smtp.mailtrap.io",
            EMAIL_PORT="2525",
            EMAIL_HOST_USER="user",
            EMAIL_HOST_PASSWORD="pass",
            EMAIL_USE_TLS="True",
            EMAIL_USE_SSL="False",
            EMAIL_TIMEOUT="10",
        )
        assert module.MAILERS == {
            "default": {
                "BACKEND": SMTP,
                "OPTIONS": {
                    "host": "sandbox.smtp.mailtrap.io",
                    "username": "user",
                    "password": "pass",
                    "use_tls": True,
                    "use_ssl": False,
                    "port": 2525,
                    "timeout": 10,
                },
            }
        }

    @pytest.mark.parametrize("value", [None, ""])
    def test_empty_port_and_timeout_are_left_out(self, reloaded_settings, value):
        """``.env.example`` ships ``EMAIL_PORT=`` empty; that must mean unset."""
        env = {"EMAIL_BACKEND": SMTP, "EMAIL_HOST": "smtp.example.com"}
        if value is not None:
            env.update(EMAIL_PORT=value, EMAIL_TIMEOUT=value)
        options = reloaded_settings(**env).MAILERS["default"]["OPTIONS"]
        assert "port" not in options
        assert "timeout" not in options

    @pytest.mark.parametrize("value", [None, ""])
    def test_unset_or_empty_host_falls_back_to_localhost(
        self, reloaded_settings, value
    ):
        """Without a host every send would fail with InvalidMailer."""
        env = {"EMAIL_BACKEND": SMTP}
        if value is not None:
            env["EMAIL_HOST"] = value
        options = reloaded_settings(**env).MAILERS["default"]["OPTIONS"]
        assert options["host"] == "localhost"

    @pytest.mark.parametrize("value", ["False", "false", "0", "no", ""])
    def test_tls_and_ssl_stay_off_unless_the_word_is_true(
        self, reloaded_settings, value
    ):
        module = reloaded_settings(
            EMAIL_BACKEND=SMTP, EMAIL_USE_TLS=value, EMAIL_USE_SSL=value
        )
        options = module.MAILERS["default"]["OPTIONS"]
        assert options["use_tls"] is False
        assert options["use_ssl"] is False

    @pytest.mark.parametrize("value", ["True", "true", "TRUE"])
    def test_tls_accepts_true_in_any_casing(self, reloaded_settings, value):
        module = reloaded_settings(EMAIL_BACKEND=SMTP, EMAIL_USE_TLS=value)
        assert module.MAILERS["default"]["OPTIONS"]["use_tls"] is True
