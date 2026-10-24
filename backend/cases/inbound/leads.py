"""Email to a lead address (`InboundMailbox.creates == "leads"`) becomes a lead.

`lead_from_email` decides who the enquirer is; `ingest_lead` applies the drops
and the daily limit, records the email once, and hands the rest to
`leads.intake.receive_lead`, the one way a lead arrives from outside.

Who the enquirer is (docs/features/lead-capture.md, "Lead addresses"):

- A hand-forwarded email is read for the original message inside it.
- A person's email: the `Reply-To` when it differs from `From`, else `From`.
- An automated sender (a no-reply style local part, or `Auto-Submitted`,
  `Precedence: bulk`) is never the lead: the enquirer is its `Reply-To` or the
  first address in the body that is not the sender's, ours or a member's.
- A member of the org is never made a lead, and their own mail is dropped.
"""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass, field
from datetime import timedelta
from itertools import islice

import phonenumbers
from django.core.exceptions import SuspiciousFileOperation, ValidationError
from django.core.files.base import ContentFile
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.text import get_valid_filename
from rest_framework.exceptions import ValidationError as DRFValidationError

from cases.models import EmailMessage, InboundMailbox
from common.models import Attachments, Profile
from common.phones import to_e164
from common.utils import fit_attachment_file_name, split_full_name, validate_attachment
from leads.intake import IncomingLead, receive_lead
from leads.models import Lead

from .generated import address_domain, on_generated_domain
from .parser import ParsedEmail
from .spam import lead_drop_reason
from .text import (
    ADDRESS,
    html_to_text,
    innermost_forward,
    split_address,
    strip_forward_prefix,
    strip_quoted_history,
    tidy,
)

logger = logging.getLogger(__name__)

AUTOMATED_LOCAL_PARTS = frozenset(
    {
        "noreply",
        "no-reply",
        "donotreply",
        "do-not-reply",
        "notifications",
        "notification",
        "alerts",
        "mailer",
    }
)
_MACHINE_PRECEDENCE = {"bulk", "list", "junk"}
DAILY_LEAD_LIMIT = 500
ENQUIRY_MAX = 20_000
# Read at most this much of a body; the enquiry keeps the first ENQUIRY_MAX.
TEXT_MAX = 100_000
NO_CONTACT_NOTE = "No email address or phone number was found in this email."
ROW_PREFIX = "lead:"
# Drops that depend on the mailbox, recorded against it rather than the org.
MAILBOX_DROPS = {"member_sender"}
# An enquirer's address comes early; a body is never searched past this many.
ADDRESSES_MAX = 200
# The phone matcher is slow on a line of nothing but digits, so it reads only
# the start of a body and stops after this many candidate numbers.
PHONE_LINES_MAX = 200
PHONE_CHARS_MAX = 20_000
PHONE_CANDIDATES_MAX = 20
PHONE_TRIES_PER_LINE = 10

_EMAIL_LABEL = re.compile(r"\b(?:e-?mail|reply|contact)\b", re.IGNORECASE)
_PHONE_LABEL = re.compile(
    r"\b(?:phone|tel|telephone|mobile|cell|cellphone|whatsapp|contact number)\b",
    re.IGNORECASE,
)
_NAME_LINE = re.compile(
    r"(?:full\s+|contact\s+|your\s+|customer\s+|lead\s+)?name\s*:\s*(.+)",
    re.IGNORECASE,
)
_FIRST_LINE = re.compile(r"first\s*name\s*:\s*(.+)", re.IGNORECASE)
_LAST_LINE = re.compile(r"(?:last\s*name|surname)\s*:\s*(.+)", re.IGNORECASE)
# A portal's own number (toll free, premium) is never the enquirer's.
_SERVICE_NUMBERS = {
    phonenumbers.PhoneNumberType.TOLL_FREE,
    phonenumbers.PhoneNumberType.PREMIUM_RATE,
    phonenumbers.PhoneNumberType.SHARED_COST,
    phonenumbers.PhoneNumberType.UAN,
    phonenumbers.PhoneNumberType.VOICEMAIL,
}
_PHONE_MAX = Lead._meta.get_field("phone").max_length
_TITLE_MAX = Lead._meta.get_field("title").max_length
_NAME_MAX = Lead._meta.get_field("first_name").max_length


@dataclass
class LeadIngestResult:
    result: str = ""  # created, merged or duplicate; "" when dropped
    lead: Lead | None = None
    dropped: bool = False
    drop_reason: str = ""


@dataclass
class EmailReading:
    """What an email says, whichever mailbox it reached. Read once per email,
    so the catch-all's recipients in several orgs share one reading."""

    sender_name: str
    sender: str
    reply_name: str
    reply_to: str
    subject: str
    text: str  # the original's body, quoted history removed
    forwarded: bool
    machine_headers: bool
    addresses: list[str]  # body addresses, labelled lines first
    name: str  # from a "Name:" line, or ""
    identity: str
    _phones: dict = field(default_factory=dict, repr=False)

    def phone(self, region) -> str:
        region = str(region or "").upper() or None
        if region not in self._phones:
            self._phones[region] = _first_phone(self.text, region)
        return self._phones[region]


def read_email(parsed: ParsedEmail) -> EmailReading:
    text = _plain_text(parsed)
    subject = parsed.subject or ""
    sender_name, sender = parsed.from_display_name, parsed.from_address
    reply_name, reply_to = split_address(_header(parsed, "Reply-To"))
    machine_headers = _machine_headers(parsed)
    forward = innermost_forward(text, subject)
    if forward is not None:
        sender_name, sender = forward.name, forward.address
        reply_name, reply_to = forward.reply_to_name, forward.reply_to
        subject = forward.subject or strip_forward_prefix(subject)
        text = forward.body
        # The outer headers describe the forwarder's mail, not the original.
        machine_headers = False
    text = strip_quoted_history(text)
    return EmailReading(
        sender_name=sender_name,
        sender=sender,
        reply_name=reply_name,
        reply_to=reply_to,
        subject=subject,
        text=text,
        forwarded=forward is not None,
        machine_headers=machine_headers,
        addresses=_body_addresses(text),
        name=_name_in(text),
        identity=_identity(parsed),
    )


def ingest_lead(
    parsed: ParsedEmail, mailbox: InboundMailbox, reading: EmailReading | None = None
) -> LeadIngestResult:
    """Run one email through a lead address.

    An email is recorded as an `EmailMessage` row keyed on
    `lead:<sha256 of its Message-ID>`, once per org, so a provider's repeat
    delivery is `already_received` and never merges twice, and one email to two
    of the org's lead addresses arrives once. A drop that depends on the
    mailbox is keyed to that mailbox instead, so the email can still land at
    the org's other lead addresses. Past the daily cap nothing is written and
    the body is not parsed. The key differs from a ticket mailbox's (the raw
    Message-ID), so the same email reaches a lead and a ticket address of one
    org. A row keeps no sender, subject or body: the lead holds those, and
    deleting the lead must not leave a copy behind.
    """
    org = mailbox.org
    identity = reading.identity if reading is not None else _identity(parsed)
    digest = hashlib.sha256(identity.encode()).hexdigest()
    org_key = ROW_PREFIX + digest
    mailbox_key = f"{ROW_PREFIX}{mailbox.id}:{digest}"
    seen = EmailMessage.objects.filter(org=org, message_id__in=[org_key, mailbox_key])
    if seen.exists():
        return LeadIngestResult(dropped=True, drop_reason="already_received")
    if _received_today(mailbox) >= DAILY_LEAD_LIMIT:
        logger.info("Lead email over the daily limit on mailbox=%s", mailbox.id)
        return LeadIngestResult(dropped=True, drop_reason="daily_limit")

    reading = reading or read_email(parsed)
    reason = lead_drop_reason(parsed, _own_addresses(org))
    incoming = None
    if not reason:
        incoming = lead_from_email(parsed, mailbox, reading)
        if incoming is None:
            reason = "member_sender"

    with transaction.atomic():
        key = mailbox_key if reason in MAILBOX_DROPS else org_key
        try:
            # Claimed before the lead is made: a concurrent delivery of the
            # same email waits on this row's unique key, then lands here.
            with transaction.atomic():
                EmailMessage.objects.create(
                    org=org,
                    mailbox=mailbox,
                    direction="inbound",
                    message_id=key,
                    from_address="",
                    received_at=timezone.now(),
                    drop_reason=reason,
                )
        except IntegrityError:
            return LeadIngestResult(dropped=True, drop_reason="already_received")
        if reason:
            logger.info("Dropped lead email on mailbox=%s: %s", mailbox.id, reason)
            return LeadIngestResult(dropped=True, drop_reason=reason)
        outcome = receive_lead(org, incoming)
        if outcome.result != "duplicate":
            _store_attachments(parsed, outcome.contact or outcome.lead)
    return LeadIngestResult(result=outcome.result, lead=outcome.lead)


def lead_from_email(
    parsed: ParsedEmail, mailbox: InboundMailbox, reading: EmailReading | None = None
) -> IncomingLead | None:
    """The lead this email describes, or None when it must be dropped (the
    sender, or the address it names, is a member of the org)."""
    reading = reading or read_email(parsed)
    org = mailbox.org
    members = _member_emails(org)
    sender = reading.sender
    if not reading.forwarded and sender in members:
        return None

    if reading.machine_headers or _automated(sender):
        not_enquirer = _not_enquirer(parsed, mailbox, sender, members)
        email = _enquirer_address(reading, not_enquirer)
        name = reading.name or (
            reading.reply_name if email and email == reading.reply_to else ""
        )
        detail = address_domain(sender)
    else:
        if _usable_reply_to(reading.reply_to, sender, mailbox):
            name, email = reading.reply_name, reading.reply_to
        else:
            name, email = reading.sender_name, sender
        if sender in members or email in members:
            return None
        email = email if _valid_email(email) else ""
        detail = mailbox.lead_source_detail
        name = name or reading.name

    phone = reading.phone(org.default_country)
    values = {
        "email": email,
        "phone": phone,
        "title": reading.subject.strip()[:_TITLE_MAX],
    }
    first, last = _split_name(name)
    values.update(first_name=first, last_name=last)

    enquiry = reading.text
    if not email and not phone:
        enquiry = f"{NO_CONTACT_NOTE}\n\n{reading.text}".strip()
    identity = reading.identity
    return IncomingLead(
        values={k: v for k, v in values.items() if v},
        custom_fields={},
        source=mailbox.lead_source,
        source_detail=(detail or "")[:100],
        external_source=f"email:{mailbox.id}",
        external_id=identity
        if len(identity) <= 255
        else "sha256:" + hashlib.sha256(identity.encode()).hexdigest(),
        assignee=mailbox.default_assignee,
        enquiry_text=enquiry[:ENQUIRY_MAX],
        channel_label=f"email to {mailbox.address}",
    )


# ---------------------------------------------------------------------------
# Reading the email
# ---------------------------------------------------------------------------


def _plain_text(parsed):
    text = parsed.body_text if parsed.body_text.strip() else ""
    if not text and parsed.body_html:
        text = html_to_text(parsed.body_html)
    return tidy(text[:TEXT_MAX])


def _header(parsed, name):
    wanted = name.lower()
    for key, value in parsed.raw_headers.items():
        if key.lower() == wanted:
            return str(value)
    return ""


def _machine_headers(parsed):
    auto = _header(parsed, "Auto-Submitted").strip().lower()
    precedence = _header(parsed, "Precedence").strip().lower()
    return bool(auto and auto != "no") or precedence in _MACHINE_PRECEDENCE


def _usable_reply_to(reply_to, sender, mailbox):
    """A person's Reply-To names the enquirer unless it is the sender again, a
    no-reply style address, or one of our own."""
    return bool(
        reply_to
        and reply_to != sender
        and not _automated(reply_to)
        and reply_to != mailbox.address.strip().lower()
        and not on_generated_domain(reply_to)
    )


def _automated(address):
    local = (address or "").split("@", 1)[0].split("+", 1)[0].lower()
    return local in AUTOMATED_LOCAL_PARTS


def _identity(parsed):
    """The email's Message-ID, or, with none, a hash of what it says, so a
    repeat delivery of it is still recognised."""
    if parsed.message_id:
        return parsed.message_id
    seen = "\n".join(
        [
            parsed.from_address,
            ",".join(parsed.to_addresses),
            parsed.subject or "",
            _header(parsed, "Date"),
            parsed.body_text or "",
            parsed.body_html or "",
        ]
    )
    return "sha256:" + hashlib.sha256(seen.encode("utf-8", "replace")).hexdigest()


def _member_emails(org):
    return {
        email.strip().lower()
        for email in Profile.objects.filter(org=org).values_list(
            "user__email", flat=True
        )
        if email
    }


def _own_addresses(org):
    return {
        address.strip().lower()
        for address in InboundMailbox.objects.filter(org=org).values_list(
            "address", flat=True
        )
    }


def _not_enquirer(parsed, mailbox, sender, members):
    """Addresses that can never be an automated email's enquirer."""
    return {
        "sender": sender,
        "domain": address_domain(sender) if sender else "",
        "addresses": members
        | _own_addresses(mailbox.org)
        | {sender, mailbox.address.lower()}
        | set(parsed.to_addresses)
        | set(parsed.cc_addresses)
        | set(parsed.delivered_to),
    }


def _acceptable(address, not_enquirer):
    address = (address or "").strip().lower().rstrip(".")
    if (
        not address
        or address in not_enquirer["addresses"]
        or _automated(address)
        or address_domain(address) == not_enquirer["domain"]
        or on_generated_domain(address)
        or not _valid_email(address)
    ):
        return ""
    return address


def _body_addresses(text):
    """Addresses in the body, those on a line labelled as an email first,
    without repeats; at most ADDRESSES_MAX."""
    found: dict[str, None] = {}
    lines = text.splitlines()
    for wanted_label in (True, False):
        for line in lines:
            if wanted_label and not _EMAIL_LABEL.search(line):
                continue
            for match in ADDRESS.finditer(line):
                found.setdefault(match.group(0).lower().rstrip("."))
                if len(found) >= ADDRESSES_MAX:
                    return list(found)
    return list(found)


def _enquirer_address(reading, not_enquirer):
    """The Reply-To, else the first acceptable address in the body."""
    for candidate in (reading.reply_to, *reading.addresses):
        found = _acceptable(candidate, not_enquirer)
        if found:
            return found
    return ""


def _name_in(text):
    """A name from the body's "Name:" line, or its first and last name lines."""
    first = last = ""
    for line in text.splitlines():
        line = line.strip(" *\t")
        if not first and (match := _FIRST_LINE.fullmatch(line)):
            first = match.group(1)
        elif not last and (match := _LAST_LINE.fullmatch(line)):
            last = match.group(1)
        elif match := _NAME_LINE.fullmatch(line):
            name = _clean_name(match.group(1))
            if name:
                return name
    return _clean_name(f"{first} {last}")


def _clean_name(value):
    value = " ".join((value or "").strip(" *\t").split())
    if not value or "@" in value or len(value) > 100 or any(c.isdigit() for c in value):
        return ""
    return value


def _split_name(name):
    name = _clean_name(name)
    if "," in name:
        # "Doe, Jane" as Outlook writes it.
        last, _, first = name.partition(",")
        name = f"{first.strip()} {last.strip()}".strip()
    first, last = split_full_name(name)
    return first[:_NAME_MAX], last[:_NAME_MAX]


def _first_phone(text, region):
    """The first phone number on a line labelled as one, else the first in the
    body, that parses for the org's country and is not a service number."""
    region = str(region or "").upper() or None
    lines = text[:PHONE_CHARS_MAX].splitlines()[:PHONE_LINES_MAX]
    labelled = [bool(_PHONE_LABEL.search(line)) for line in lines]
    ordered = [line for line, label in zip(lines, labelled) if label]
    ordered += [line for line, label in zip(lines, labelled) if not label]
    for match in islice(_phone_matches(ordered, region), PHONE_CANDIDATES_MAX):
        if phonenumbers.number_type(match.number) in _SERVICE_NUMBERS:
            continue
        e164 = to_e164(match.raw_string, region)
        if e164:
            raw = match.raw_string.strip()
            return raw if len(raw) <= _PHONE_MAX else e164
    return ""


def _phone_matches(lines, region):
    for line in lines:
        try:
            yield from phonenumbers.PhoneNumberMatcher(
                line,
                region,
                leniency=phonenumbers.Leniency.POSSIBLE,
                max_tries=PHONE_TRIES_PER_LINE,
            )
        except Exception:  # never fail an email over its text
            continue


def _valid_email(address):
    if not address or len(address) > 254:
        return False
    try:
        validate_email(address)
    except ValidationError:
        return False
    return True


# ---------------------------------------------------------------------------
# Limits and files
# ---------------------------------------------------------------------------


def _received_today(mailbox):
    """Emails this address turned into a lead (or a merge) in the last 24 hours."""
    return EmailMessage.objects.filter(
        org=mailbox.org,
        mailbox=mailbox,
        drop_reason="",
        created_at__gte=timezone.now() - timedelta(hours=24),
    ).count()


def _store_attachments(parsed, record):
    """The email's files on the lead (or the contact a converted lead became),
    each through `validate_attachment`; a refused file is skipped, not fatal."""
    if record is None:
        return
    label_length = Attachments._meta.get_field("file_name").max_length
    for parsed_file in parsed.attachments:
        label = fit_attachment_file_name(parsed_file.filename, label_length)
        try:
            storage_name = get_valid_filename(label)
        except SuspiciousFileOperation:
            storage_name = "attachment"
        upload = ContentFile(parsed_file.payload, name=storage_name)
        try:
            validate_attachment(upload)
        except DRFValidationError:
            logger.warning(
                "Skipped an inbound attachment of %d bytes on %s %s",
                upload.size,
                type(record).__name__,
                record.id,
            )
            continue
        Attachments.objects.create(
            content_object=record, org=record.org, file_name=label, attachment=upload
        )
