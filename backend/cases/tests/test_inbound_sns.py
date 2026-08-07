"""SNS signature-verification hardening tests.

Covers the three controls added after CodeQL alerts #27/#28 (`py/full-ssrf`)
on `cases/inbound/sns.py`:

1. Neither outbound fetch (SigningCertURL, SubscribeURL) follows redirects.
   The host allow-list is applied to the URL we are *about* to fetch, so a 3xx
   would otherwise land us on an unvalidated host.
2. The signing certificate is validated (validity window + subject CN pinned
   to the AWS SNS host family) instead of being trusted blindly.
3. The cert fetch uses an explicit, strict TLS context so transport trust
   can't silently degrade.

The TopicArn pin lives in `test_inbound_email.py` with the other webhook tests.
"""

from __future__ import annotations

import http.server
import threading
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.x509.oid import NameOID

from cases.inbound import sns
from cases.inbound.sns import SNSVerificationError, verify_sns_message

# ---------------------------------------------------------------------------
# Certificate helpers
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def signing_key():
    """One RSA key for the whole module. Keygen is the slow part."""
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _make_cert(key, *, cn="sns.amazonaws.com", not_before=None, not_after=None):
    """Self-signed cert with a controllable CN and validity window."""
    now = datetime.now(timezone.utc)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, cn)])
    return (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(not_before or now - timedelta(days=1))
        .not_valid_after(not_after or now + timedelta(days=1))
        .sign(key, hashes.SHA256())
    )


def _pem(cert) -> bytes:
    return cert.public_bytes(serialization.Encoding.PEM)


def _signed_payload(key, *, topic_arn="arn:aws:sns:us-east-1:1:t", **overrides):
    """A Notification payload carrying a signature that actually verifies."""
    payload = {
        "Type": "Notification",
        "MessageId": "m-1",
        "Subject": "Amazon SES Email Receipt",
        "Message": "raw email here",
        "Timestamp": "2026-05-09T12:00:00.000Z",
        "TopicArn": topic_arn,
        "SignatureVersion": "1",
        "SigningCertURL": (
            "https://sns.us-east-1.amazonaws.com/SimpleNotificationService-x.pem"
        ),
    }
    payload.update(overrides)
    string_to_sign = sns._build_string_to_sign(payload, sns._NOTIFICATION_KEYS)
    payload["Signature"] = (
        __import__("base64")
        .b64encode(key.sign(string_to_sign, padding.PKCS1v15(), hashes.SHA1()))
        .decode()
    )
    return payload


# ---------------------------------------------------------------------------
# Certificate validation
# ---------------------------------------------------------------------------


class TestSigningCertValidation:
    def test_valid_cert_and_signature_verifies(self, signing_key):
        """Happy path. Proves the new checks can return True, not just False."""
        cert = _make_cert(signing_key)
        payload = _signed_payload(signing_key)

        verify_sns_message(payload, fetch_cert=lambda url: _pem(cert))

    def test_expired_signing_cert_is_rejected(self, signing_key):
        now = datetime.now(timezone.utc)
        cert = _make_cert(
            signing_key,
            not_before=now - timedelta(days=30),
            not_after=now - timedelta(days=1),
        )
        payload = _signed_payload(signing_key)

        with pytest.raises(SNSVerificationError, match="not currently valid"):
            verify_sns_message(payload, fetch_cert=lambda url: _pem(cert))

    def test_not_yet_valid_signing_cert_is_rejected(self, signing_key):
        now = datetime.now(timezone.utc)
        cert = _make_cert(
            signing_key,
            not_before=now + timedelta(days=1),
            not_after=now + timedelta(days=30),
        )
        payload = _signed_payload(signing_key)

        with pytest.raises(SNSVerificationError, match="not currently valid"):
            verify_sns_message(payload, fetch_cert=lambda url: _pem(cert))

    def test_cert_with_foreign_common_name_is_rejected(self, signing_key):
        """A cert served from an SNS URL but issued to someone else must not be
        accepted just because the signature it carries checks out."""
        cert = _make_cert(signing_key, cn="evil.example.com")
        payload = _signed_payload(signing_key)

        with pytest.raises(SNSVerificationError, match="common name"):
            verify_sns_message(payload, fetch_cert=lambda url: _pem(cert))

    def test_regional_and_cn_partition_common_names_are_accepted(self, signing_key):
        for cn in ("sns.amazonaws.com", "sns.eu-west-1.amazonaws.com"):
            cert = _make_cert(signing_key, cn=cn)
            payload = _signed_payload(signing_key)

            verify_sns_message(payload, fetch_cert=lambda url: _pem(cert))

    def test_cert_without_common_name_is_rejected(self, signing_key):
        now = datetime.now(timezone.utc)
        name = x509.Name(
            [x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Amazon Web Services")]
        )
        cert = (
            x509.CertificateBuilder()
            .subject_name(name)
            .issuer_name(name)
            .public_key(signing_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(days=1))
            .not_valid_after(now + timedelta(days=1))
            .sign(signing_key, hashes.SHA256())
        )
        payload = _signed_payload(signing_key)

        with pytest.raises(SNSVerificationError, match="common name"):
            verify_sns_message(payload, fetch_cert=lambda url: _pem(cert))

    def test_common_name_with_trailing_newline_is_rejected(self, signing_key):
        """`$` also matches just before a trailing newline, so `match()` would
        accept "sns.amazonaws.com\\n". Only `fullmatch()` anchors to the true
        end of the string."""
        cert = _make_cert(signing_key, cn="sns.amazonaws.com\n")
        payload = _signed_payload(signing_key)

        with pytest.raises(SNSVerificationError, match="common name"):
            verify_sns_message(payload, fetch_cert=lambda url: _pem(cert))

    def test_wrong_key_still_fails_signature_check(self, signing_key):
        """Cert validation must not have displaced the signature check."""
        other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cert = _make_cert(other_key)
        payload = _signed_payload(signing_key)

        with pytest.raises(SNSVerificationError, match="Signature does not match"):
            verify_sns_message(payload, fetch_cert=lambda url: _pem(cert))


# ---------------------------------------------------------------------------
# Redirect refusal
# ---------------------------------------------------------------------------


class _RedirectHandler(http.server.BaseHTTPRequestHandler):
    """302s /start to /secret and records every path it is asked for."""

    paths_seen: list = []

    def do_GET(self):  # noqa: N802  # BaseHTTPRequestHandler API
        type(self).paths_seen.append(self.path)
        if self.path == "/start":
            self.send_response(302)
            self.send_header("Location", "/secret")
            self.end_headers()
            return
        body = b"redirect target reached"
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):  # silence the test run
        pass


@pytest.fixture
def redirecting_server():
    _RedirectHandler.paths_seen = []
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _RedirectHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server, _RedirectHandler.paths_seen
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


class TestRedirectRefusal:
    def test_opener_does_not_follow_redirects(self, redirecting_server):
        """The shared opener must surface the 3xx instead of chasing it."""
        server, paths_seen = redirecting_server
        host, port = server.server_address[:2]

        with pytest.raises(HTTPError) as exc:
            sns._OPENER.open(f"http://{host}:{port}/start", timeout=5)

        assert exc.value.code == 302
        assert paths_seen == ["/start"], "redirect target must not be fetched"

    def test_opener_still_returns_non_redirect_responses(self, redirecting_server):
        server, _ = redirecting_server
        host, port = server.server_address[:2]

        with sns._OPENER.open(f"http://{host}:{port}/plain", timeout=5) as response:
            assert response.read() == b"redirect target reached"

    def test_fetch_signing_cert_routes_through_the_no_redirect_opener(
        self, monkeypatch
    ):
        calls = []

        class _FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def read(self):
                return b"pem-bytes"

        monkeypatch.setattr(
            sns._OPENER,
            "open",
            lambda url, timeout=None: calls.append(url) or _FakeResponse(),
        )

        url = "https://sns.us-east-1.amazonaws.com/SimpleNotificationService-a.pem"
        assert sns._fetch_signing_cert(url) == b"pem-bytes"
        assert calls == [url]

    def test_confirm_subscription_routes_through_the_no_redirect_opener(
        self, monkeypatch
    ):
        calls = []

        class _FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def read(self):
                return b""

        monkeypatch.setattr(
            sns._OPENER,
            "open",
            lambda url, timeout=None: calls.append(url) or _FakeResponse(),
        )

        url = "https://sns.us-east-1.amazonaws.com/?Action=ConfirmSubscription"
        sns.confirm_subscription(
            {"Type": "SubscriptionConfirmation", "SubscribeURL": url}
        )
        assert calls == [url]


# ---------------------------------------------------------------------------
# URL pinning (pre-existing behaviour, previously untested)
# ---------------------------------------------------------------------------


class TestUrlPinning:
    @pytest.mark.parametrize(
        "url",
        [
            "http://sns.us-east-1.amazonaws.com/a.pem",
            "file:///etc/passwd",
        ],
    )
    def test_cert_url_must_be_https(self, url):
        with pytest.raises(SNSVerificationError, match="must be https"):
            sns._fetch_signing_cert(url)

    @pytest.mark.parametrize(
        "url",
        [
            "https://evil.example.com/a.pem",
            "https://sns.evil.attacker.amazonaws.com/a.pem",
            "https://notsns.amazonaws.com/a.pem",
            "https://sns.amazonaws.com.evil.com/a.pem",
        ],
    )
    def test_cert_url_host_must_be_in_the_sns_family(self, url):
        with pytest.raises(SNSVerificationError, match="not in the AWS SNS family"):
            sns._fetch_signing_cert(url)

    def test_cert_url_must_end_in_pem(self):
        with pytest.raises(SNSVerificationError, match="must end in .pem"):
            sns._fetch_signing_cert("https://sns.us-east-1.amazonaws.com/payload.txt")

    @pytest.mark.parametrize(
        "url",
        [
            "https://evil.example.com/confirm",
            "http://sns.us-east-1.amazonaws.com/confirm",
        ],
    )
    def test_subscribe_url_must_be_https_on_an_sns_host(self, url):
        with pytest.raises(SNSVerificationError, match="not on AWS SNS host"):
            sns.confirm_subscription(
                {"Type": "SubscriptionConfirmation", "SubscribeURL": url}
            )
