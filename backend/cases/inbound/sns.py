"""SNS message verification.

AWS SNS posts JSON like:

  {
    "Type": "Notification",            // or "SubscriptionConfirmation"
    "MessageId": "...",
    "TopicArn": "arn:aws:sns:...:...:...",
    "Subject": "Amazon SES Email Receipt",
    "Message": "<raw-email-or-json>",
    "Timestamp": "2026-05-09T12:00:00.000Z",
    "SignatureVersion": "1",           // or "2" for SHA-256
    "Signature": "<base64>",
    "SigningCertURL": "https://sns.<region>.amazonaws.com/SimpleNotificationService-XXXX.pem",
    "SubscribeURL": "https://sns...",  // SubscriptionConfirmation only
    "Token": "..."                     // SubscriptionConfirmation only
  }

We verify the signature against the AWS-published certificate so that an
attacker can't post arbitrary JSON to our public webhook URL. The cert URL
is pinned to the `sns.<region>.amazonaws.com` host family.

Reference: https://docs.aws.amazon.com/sns/latest/dg/sns-verify-signature-of-message.html
"""

from __future__ import annotations

import base64
import logging
import re
from typing import Iterable
from urllib.parse import urlparse
from urllib.request import urlopen

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.x509 import load_pem_x509_certificate

logger = logging.getLogger(__name__)

# AWS regional SNS hosts; we accept any of these but reject any other host as
# a defense against a forged SigningCertURL pointing at attacker-controlled storage.
_SIGNING_HOST_RE = re.compile(
    r"^sns(?:\.[a-z0-9-]+)?\.amazonaws\.com(?:\.cn)?$"
)


# Headers required for the canonical signing string for each message type.
# See AWS docs link above.
_NOTIFICATION_KEYS = (
    "Message",
    "MessageId",
    "Subject",
    "Timestamp",
    "TopicArn",
    "Type",
)
_SUBSCRIPTION_KEYS = (
    "Message",
    "MessageId",
    "SubscribeURL",
    "Timestamp",
    "Token",
    "TopicArn",
    "Type",
)


class SNSVerificationError(Exception):
    """Raised when an SNS message fails signature verification."""


def _build_string_to_sign(payload: dict, keys: Iterable[str]) -> bytes:
    """Build the AWS-defined canonical string for signing.

    Format: for each key in `keys` (alphabetical order), if the key is present
    in the payload, append "<key>\\n<value>\\n".
    """
    pieces: list[str] = []
    for key in keys:
        if key in payload and payload[key] is not None:
            pieces.append(key)
            pieces.append("\n")
            pieces.append(str(payload[key]))
            pieces.append("\n")
    return "".join(pieces).encode("utf-8")


def _fetch_signing_cert(url: str, *, timeout: float = 5.0) -> bytes:
    """Fetch the SNS signing certificate, with hostname pinning."""
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise SNSVerificationError(f"SigningCertURL must be https: {url!r}")
    if not _SIGNING_HOST_RE.match(parsed.hostname or ""):
        raise SNSVerificationError(
            f"SigningCertURL host {parsed.hostname!r} not in the AWS SNS family"
        )
    if not parsed.path.endswith(".pem"):
        raise SNSVerificationError(f"SigningCertURL must end in .pem: {url!r}")
    with urlopen(url, timeout=timeout) as response:  # noqa: S310 — host pinned above
        return response.read()


def _hash_alg_for_version(version: str) -> hashes.HashAlgorithm:
    if version == "1":
        return hashes.SHA1()
    if version == "2":
        return hashes.SHA256()
    raise SNSVerificationError(f"Unsupported SignatureVersion: {version!r}")


def verify_sns_message(
    payload: dict,
    *,
    fetch_cert=_fetch_signing_cert,
) -> None:
    """Verify the signature on an SNS payload.

    Raises `SNSVerificationError` if anything looks wrong. The `fetch_cert`
    seam exists so tests can substitute a deterministic cert without going to
    the network.
    """
    msg_type = payload.get("Type")
    if msg_type not in {"Notification", "SubscriptionConfirmation", "UnsubscribeConfirmation"}:
        raise SNSVerificationError(f"Unknown SNS Type: {msg_type!r}")

    signature_b64 = payload.get("Signature")
    cert_url = payload.get("SigningCertURL")
    sig_version = str(payload.get("SignatureVersion", ""))
    if not signature_b64 or not cert_url or not sig_version:
        raise SNSVerificationError("Missing signature fields")

    try:
        signature = base64.b64decode(signature_b64)
    except (ValueError, TypeError) as exc:
        raise SNSVerificationError(f"Bad base64 signature: {exc}") from exc

    cert_bytes = fetch_cert(cert_url)
    cert = load_pem_x509_certificate(cert_bytes)
    public_key = cert.public_key()

    keys = _NOTIFICATION_KEYS if msg_type == "Notification" else _SUBSCRIPTION_KEYS
    string_to_sign = _build_string_to_sign(payload, keys)
    hash_alg = _hash_alg_for_version(sig_version)

    try:
        # SNS signs with PKCS#1 v1.5 RSA.
        public_key.verify(
            signature,
            string_to_sign,
            padding.PKCS1v15(),
            hash_alg,
        )
    except InvalidSignature as exc:
        raise SNSVerificationError("Signature does not match") from exc
    except Exception as exc:  # pragma: no cover — non-RSA cert is impossible in practice
        raise SNSVerificationError(f"Verification failed: {exc}") from exc


def confirm_subscription(payload: dict, *, fetch=urlopen, timeout: float = 5.0) -> None:
    """If the payload is a SubscriptionConfirmation, hit the SubscribeURL once.

    SNS will GET this URL itself when the topic is wired through the AWS console;
    confirming programmatically is convenient when an admin pastes the webhook
    URL directly into the SES Receipt Rule and lets SNS auto-subscribe.
    """
    if payload.get("Type") != "SubscriptionConfirmation":
        return
    url = payload.get("SubscribeURL")
    if not url:
        raise SNSVerificationError("SubscriptionConfirmation missing SubscribeURL")
    parsed = urlparse(url)
    if parsed.scheme != "https" or not _SIGNING_HOST_RE.match(parsed.hostname or ""):
        raise SNSVerificationError(f"SubscribeURL not on AWS SNS host: {url!r}")
    try:
        with fetch(url, timeout=timeout) as response:  # noqa: S310 — host pinned
            response.read()
    except Exception:
        logger.exception("Failed to confirm SNS subscription at %s", url)
        raise
