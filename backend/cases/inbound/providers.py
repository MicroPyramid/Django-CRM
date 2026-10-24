"""Postmark and Mailgun inbound deliveries: who sent them, and what they say.

Both post to a mailbox's own webhook URL, and the mailbox's `webhook_secret`
proves the post came from the provider. A mailbox with no secret accepts
nothing.

- Postmark posts JSON and is set up with the secret as the basic-auth password
  in the webhook URL (`https://postmark:<secret>@<host>/...`). Postmark retries
  any answer but 200 and stops at 403, so a wrong password answers 401 and the
  messages are retried while an admin fixes it.
  https://postmarkapp.com/developer/webhooks/inbound-webhook
- Mailgun posts form fields from a route's `forward()` action, signed with the
  account's HTTP webhook signing key: HMAC-SHA256 of `timestamp + token`, hex,
  in `signature` (`parent-signature` for a subaccount, keyed by the parent).
  The signature covers only those two, so the timestamp must be recent and a
  token is accepted once per mailbox.
  https://documentation.mailgun.com/docs/mailgun/user-manual/receive-forward-store/receive-http
  https://documentation.mailgun.com/docs/mailgun/user-manual/webhooks/securing-webhooks
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import re
import time

from django.core.cache import cache

from .parser import ParsedAttachment, ParsedEmail, parse_parts, parse_raw_email

# More attachments than this on one email are not read.
ATTACHMENTS_MAX = 50
# Mailgun retries a failed post for 8 hours; 5 minutes covers clock skew.
MAILGUN_MAX_AGE = 8 * 3600 + 5 * 60
MAILGUN_MAX_AHEAD = 5 * 60


def _field(data, name) -> str:
    """One string field from a dict or a QueryDict, else ""."""
    value = data.get(name) if hasattr(data, "get") else None
    if isinstance(value, list):
        value = value[0] if value else None
    return value if isinstance(value, str) else ""


def _header_value(parsed: ParsedEmail, name: str) -> str:
    wanted = name.lower()
    for key, value in parsed.raw_headers.items():
        if key.lower() == wanted:
            return str(value)
    return ""


# ---------------------------------------------------------------------------
# Postmark
# ---------------------------------------------------------------------------


def postmark_authorized(authorization, secret) -> bool:
    """Whether a basic-auth `Authorization` header carries `secret` as its
    password. Any user name; compared in constant time."""
    if not secret or not isinstance(authorization, str):
        return False
    scheme, _, encoded = authorization.strip().partition(" ")
    if scheme.lower() != "basic":
        return False
    try:
        decoded = base64.b64decode(encoded.strip(), validate=True)
    except (binascii.Error, ValueError):
        return False
    _, colon, password = decoded.partition(b":")
    return bool(colon) and hmac.compare_digest(password, secret.encode("utf-8"))


def _named_address(entry) -> str:
    if not isinstance(entry, dict):
        return ""
    address = entry.get("Email") if isinstance(entry.get("Email"), str) else ""
    name = entry.get("Name") if isinstance(entry.get("Name"), str) else ""
    if not address:
        return ""
    if not name:
        return address
    quoted = name.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{quoted}" <{address}>'


def _address_list(entries) -> str:
    if not isinstance(entries, list):
        return ""
    return ", ".join(a for a in (_named_address(e) for e in entries) if a)


def _postmark_files(entries) -> list[ParsedAttachment]:
    files = []
    for entry in (entries if isinstance(entries, list) else [])[:ATTACHMENTS_MAX]:
        if not isinstance(entry, dict) or not isinstance(entry.get("Content"), str):
            continue
        try:
            payload = base64.b64decode("".join(entry["Content"].split()), validate=True)
        except (binascii.Error, ValueError):
            continue
        name = entry.get("Name") if isinstance(entry.get("Name"), str) else ""
        kind = (
            entry.get("ContentType")
            if isinstance(entry.get("ContentType"), str)
            else ""
        )
        files.append(
            ParsedAttachment(
                filename=name or "attachment",
                content_type=(kind or "application/octet-stream").lower(),
                payload=payload,
            )
        )
    return files


def parse_postmark(payload: dict) -> ParsedEmail:
    """A Postmark inbound webhook's JSON. Its `RawEmail` (sent when the server
    has "Include raw email content" on) is the most faithful source; without it
    the parsed fields are used, with the real Message-ID read from `Headers`
    and Postmark's own `MessageID` as the fallback."""
    raw = payload.get("RawEmail")
    if isinstance(raw, str) and raw.strip():
        parsed = parse_raw_email(raw)
    else:
        headers = [
            (h.get("Name"), h.get("Value"))
            for h in payload.get("Headers") or []
            if isinstance(h, dict)
        ]
        sender = _named_address(payload.get("FromFull")) or _field(payload, "From")
        top = [
            ("From", sender),
            ("To", _address_list(payload.get("ToFull")) or _field(payload, "To")),
            ("Cc", _address_list(payload.get("CcFull")) or _field(payload, "Cc")),
            ("Subject", _field(payload, "Subject")),
            ("Date", _field(payload, "Date")),
            ("Reply-To", _field(payload, "ReplyTo")),
            ("X-Original-To", _field(payload, "OriginalRecipient")),
        ]
        headers += [(name, value) for name, value in top if value]
        own_id = _field(payload, "MessageID")
        parsed = parse_parts(
            headers,
            text=_field(payload, "TextBody"),
            html=_field(payload, "HtmlBody"),
            attachments=_postmark_files(payload.get("Attachments")),
            fallback_message_id=f"{own_id}@postmark" if own_id else "",
        )
    if _header_value(parsed, "X-Spam-Status").strip().lower().startswith("yes"):
        parsed.spam_verdict = "spam"
    return parsed


# ---------------------------------------------------------------------------
# Mailgun
# ---------------------------------------------------------------------------


def mailgun_signed(data, signing_key, now=None) -> bool:
    """Whether a Mailgun post's `signature` (or `parent-signature`) is the
    HMAC-SHA256 of `timestamp + token` under `signing_key`, with a timestamp
    no older than MAILGUN_MAX_AGE and no more than MAILGUN_MAX_AHEAD ahead."""
    timestamp, token = _field(data, "timestamp"), _field(data, "token")
    if not signing_key or not token:
        return False
    if not (timestamp.isascii() and timestamp.isdigit() and len(timestamp) <= 12):
        return False
    now = time.time() if now is None else now
    if not now - MAILGUN_MAX_AGE <= int(timestamp) <= now + MAILGUN_MAX_AHEAD:
        return False
    expected = hmac.new(
        signing_key.encode("utf-8"),
        (timestamp + token).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return any(
        hmac.compare_digest(_field(data, name).encode("utf-8"), expected.encode())
        for name in ("signature", "parent-signature")
        if _field(data, name)
    )


def _token_key(mailbox, data) -> str:
    token = hashlib.sha256(_field(data, "token").encode("utf-8")).hexdigest()
    return f"inbound:mailgun-token:{mailbox.id}:{token}"


def claim_mailgun_token(mailbox, data) -> bool:
    """Claim this post's token for `mailbox`, for as long as its timestamp is
    valid. False when it is already claimed, so of two concurrent posts with
    one token only the first is delivered."""
    return cache.add(_token_key(mailbox, data), 1, MAILGUN_MAX_AGE + MAILGUN_MAX_AHEAD)


def release_mailgun_token(mailbox, data) -> None:
    """Give a claimed token back after a failed delivery, so Mailgun's retry
    of the same post is accepted."""
    cache.delete(_token_key(mailbox, data))


def _mailgun_headers(value) -> list[tuple[str, str]]:
    try:
        pairs = json.loads(value) if value else []
    except ValueError:
        return []
    if not isinstance(pairs, list):
        return []
    return [
        (pair[0], pair[1])
        for pair in pairs
        if isinstance(pair, list) and len(pair) == 2
    ]


def _mailgun_files(files) -> list[ParsedAttachment]:
    names = sorted(
        (n for n in files if re.fullmatch(r"attachment-\d{1,3}", n)),
        key=lambda n: int(n.rsplit("-", 1)[1]),
    )
    attachments = []
    for name in names[:ATTACHMENTS_MAX]:
        upload = files[name]
        attachments.append(
            ParsedAttachment(
                filename=getattr(upload, "name", "") or "attachment",
                content_type=(
                    getattr(upload, "content_type", "") or "application/octet-stream"
                ).lower(),
                payload=upload.read(),
            )
        )
    return attachments


def parse_mailgun(data, files) -> ParsedEmail:
    """A Mailgun route's forwarded post. `body-mime` (a forward URL ending in
    `mime`) is the raw message; otherwise `message-headers` carries every
    header, `body-plain` and `body-html` the bodies and `attachment-<n>` the
    files. `stripped-text` is never used: it drops a forwarded original."""
    mime = _field(data, "body-mime")
    if mime:
        parsed = parse_raw_email(mime)
    else:
        headers = _mailgun_headers(_field(data, "message-headers"))
        top = [("From", _field(data, "from")), ("Subject", _field(data, "subject"))]
        headers += [(name, value) for name, value in top if value]
        html_parts = data.getlist("body-html") if hasattr(data, "getlist") else []
        html = "\n".join(p for p in html_parts if isinstance(p, str)) or _field(
            data, "body-html"
        )
        parsed = parse_parts(
            headers,
            text=_field(data, "body-plain"),
            html=html,
            attachments=_mailgun_files(files or {}),
        )
    if _header_value(parsed, "X-Mailgun-Sflag").strip().lower() == "yes":
        parsed.spam_verdict = "spam"
    return parsed
