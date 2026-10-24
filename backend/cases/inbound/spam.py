"""Header-based filters for autoresponders, mailing-list traffic, and bounces.

Provider-side spam scoring (Mailgun's X-Mailgun-Sflag, SES SNS verdicts) is
deferred to a follow-up; for now we drop the obvious self-replying noise so
auto-replies don't spawn empty Cases that immediately need closing.
"""

from __future__ import annotations

from .parser import ParsedEmail

# Set as a constant so the test suite can introspect the policy.
DROP_PRECEDENCE_VALUES = {"bulk", "list", "junk"}


def should_drop(parsed: ParsedEmail) -> tuple[bool, str]:
    """Return `(drop, reason)`. `reason` is one of:
    `bounce`, `auto_submitted`, `precedence_bulk`, `x_autoreply`, or "" when
    the message should be processed.
    """
    headers_lower = {k.lower(): v for k, v in parsed.raw_headers.items()}

    if parsed.is_bounce:
        return True, "bounce"

    auto_submitted = headers_lower.get("auto-submitted", "").strip().lower()
    if auto_submitted and auto_submitted != "no":
        return True, "auto_submitted"

    precedence = headers_lower.get("precedence", "").strip().lower()
    if precedence in DROP_PRECEDENCE_VALUES:
        return True, "precedence_bulk"

    x_autoreply = headers_lower.get("x-autoreply", "").strip().lower()
    if x_autoreply == "yes":
        return True, "x_autoreply"

    # `List-Unsubscribe` plus `List-Id` is the canonical mailing-list signature;
    # one alone (e.g. List-Unsubscribe in transactional mail) isn't enough.
    if "list-id" in headers_lower and "list-unsubscribe" in headers_lower:
        return True, "mailing_list"

    return False, ""


def lead_drop_reason(parsed: ParsedEmail, own_addresses) -> str:
    """Why a lead address ignores this email (`bounce`, `own_address`, `spam`,
    `virus`), or "". `own_addresses` are the org's inbound addresses, lowercased.

    Unlike `should_drop`, Auto-Submitted, Precedence, X-Autoreply and list mail
    are kept: portal notifications carry those headers, and a lead address
    never replies, so there is no mail loop to guard against.
    """
    if parsed.is_bounce:
        return "bounce"
    if parsed.from_address and parsed.from_address in own_addresses:
        return "own_address"
    return parsed.spam_verdict
