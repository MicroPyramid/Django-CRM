"""Match an inbound email to an existing Case if possible."""

from __future__ import annotations

import re
import uuid
from typing import Optional

from django.db import connection

from cases.models import Case, EmailMessage
from .parser import ParsedEmail

# Subject-line fallback: `[Case #<short-id>]` where short-id is the first
# 8 hex chars of the case UUID. Used only when RFC headers can't thread.
_SUBJECT_FALLBACK_RE = re.compile(r"\[Case #([0-9a-f]{8})(?:[0-9a-f-]*)?\]", re.I)


def _follow_merge(case: Optional[Case]) -> Optional[Case]:
    """If `case` was merged into another, return the primary; else return as-is.

    Merge chains are forbidden at the API (see CaseMergeView), so a single hop
    is sufficient.
    """
    if case is None:
        return None
    if case.merged_into_id:
        return case.merged_into or case
    return case


def find_existing_case(parsed: ParsedEmail, org) -> Optional[Case]:
    """Return the Case this email belongs to, or None to create a new one.

    Matching priority (highest first):
      1. `In-Reply-To` matches an `EmailMessage.message_id` for this org.
      2. Any id in `References` matches an `EmailMessage.message_id`.
      3. Any id in `References` (or In-Reply-To) matches a `Case.external_thread_id`
         OR `Case.alt_thread_ids` (inherited from a merged duplicate).
      4. Subject line contains `[Case #<short-id>]` and a Case with that
         id-prefix exists in this org.

    In every branch, if the matched case has been merged into a primary,
    the primary is returned instead.
    """
    candidate_ids: list[str] = []
    if parsed.in_reply_to:
        candidate_ids.append(parsed.in_reply_to)
    candidate_ids.extend(parsed.references)
    # de-dupe while preserving order
    seen: set[str] = set()
    candidate_ids = [c for c in candidate_ids if not (c in seen or seen.add(c))]

    if candidate_ids:
        match = (
            EmailMessage.objects.filter(org=org, message_id__in=candidate_ids)
            .select_related("case", "case__merged_into")
            .order_by("-received_at")
            .first()
        )
        if match and match.case_id:
            return _follow_merge(match.case)

        case_via_thread = (
            Case.objects.select_related("merged_into")
            .filter(org=org, external_thread_id__in=candidate_ids)
            .first()
        )
        if case_via_thread:
            return _follow_merge(case_via_thread)

        # alt_thread_ids on a primary inherits merged duplicates' thread ids.
        # JSONField `__contains` is Postgres-only; SQLite tests fall back to a
        # narrow Python scan over cases that actually have a non-empty array.
        if connection.vendor == "postgresql":
            for cid in candidate_ids:
                case_via_alt = (
                    Case.objects.select_related("merged_into")
                    .filter(org=org, alt_thread_ids__contains=cid)
                    .first()
                )
                if case_via_alt:
                    return _follow_merge(case_via_alt)
        else:
            candidate_set = set(candidate_ids)
            for case in (
                Case.objects.select_related("merged_into")
                .filter(org=org)
                .exclude(alt_thread_ids=[])
                .only("id", "alt_thread_ids", "merged_into")
            ):
                if any(tid in candidate_set for tid in (case.alt_thread_ids or [])):
                    return _follow_merge(case)

    # Subject-line fallback. We need a real prefix because Case.id is a UUID.
    subject_match = _SUBJECT_FALLBACK_RE.search(parsed.subject or "")
    if subject_match:
        prefix = subject_match.group(1).lower()
        # Reconstruct enough of a UUID to use a startswith filter on the str cast.
        # SQLite can't index a UUIDField for prefix lookups; in production
        # Postgres this is still cheap because the candidate set is small per org.
        for case in Case.objects.filter(org=org).only("id", "merged_into")[:200]:
            if str(case.id).replace("-", "").lower().startswith(prefix):
                return _follow_merge(case)

    return None


# A tiny helper used by the pipeline when a brand-new Case is created — the
# Case.external_thread_id should be the Message-ID of the email that birthed it.
def short_case_id(case: Case) -> str:
    """8-char prefix used in subject-line fallback threading."""
    return str(case.id).replace("-", "")[:8]


__all__ = ["find_existing_case", "short_case_id"]
