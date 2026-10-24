"""The rule for a `source` value on a lead, contact or deal.

A source is a key from the org's list (`leads.sources`). Three cases pass
without being an active key: nothing at all, the value the record already
holds (retired or not, because both clients resend it on every save), and,
for phone builds that predate editable sources, what those builds can send.
"""

from leads.sources import source_keys

# Exactly the keys the old phone builds read back (mobile/lib/data/models at
# 1.12). The lead picker knew `compaign`, not `campaign`; the deal picker
# matched `CAMPAIGN` case-insensitively but had no `web form`. A stored key
# outside the set reads as Other (leads) or None (deals), and the build saves
# that in its place.
LEAD_PICKER_KEYS = frozenset(
    {
        "call",
        "email",
        "existing customer",
        "partner",
        "public relations",
        "other",
    }
)
DEAL_PICKER_KEYS = LEAD_PICKER_KEYS | {"campaign"}

# What old builds send for the keys that were renamed or uppercase.
LEGACY_PHONE_ALIASES = {
    "compaign": "campaign",
    "NONE": "",
    "CALL": "call",
    "EMAIL": "email",
    "EXISTING CUSTOMER": "existing customer",
    "PARTNER": "partner",
    "PUBLIC RELATIONS": "public relations",
    "CAMPAIGN": "campaign",
    "WEBSITE": "web form",
    "OTHER": "other",
}

NOT_A_SOURCE = "Choose one of your lead sources."


def check_source(value, org, stored, legacy_phone=False, picker_keys=LEAD_PICKER_KEYS):
    """Return the value to store, or raise ValueError(NOT_A_SOURCE).

    `stored` is the record's current value (None on create); `org` may be None
    only where there is nothing to check against, which refuses any key.
    """
    if legacy_phone:
        if value in LEGACY_PHONE_ALIASES:
            value = LEGACY_PHONE_ALIASES[value]
        # An old build that cannot show a newer key sends blank or "other"
        # for it. Keeping the stored key is the only reading that loses nothing.
        if stored and stored not in picker_keys and value in (None, "", "other"):
            return stored
    if value in (None, ""):
        return value
    if value == stored:
        return value
    if org is None or value not in source_keys(org):
        raise ValueError(NOT_A_SOURCE)
    return value
