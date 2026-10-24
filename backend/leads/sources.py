"""Each org's list of lead sources, and the defaults every org starts with."""

from leads.models import LeadSource

DEFAULT_SOURCES = [
    ("call", "Call"),
    ("email", "Email"),
    ("existing customer", "Existing customer"),
    ("partner", "Partner"),
    ("public relations", "Public relations"),
    ("campaign", "Campaign"),
    ("other", "Other"),
    ("web form", "Web form"),
    ("meta ads", "Meta ads"),
    ("google ads", "Google ads"),
    ("linkedin ads", "LinkedIn ads"),
    ("directory or marketplace", "Directory or marketplace"),
    ("whatsapp", "WhatsApp"),
    ("referral", "Referral"),
    ("walk-in", "Walk-in"),
]


def derive_key(label: str) -> str:
    """A source's key: its label lowercased, with single spaces."""
    return " ".join(label.lower().split())


def org_sources(org, create=True) -> list[LeadSource]:
    """The org's sources by `order`, retired ones included, with every default.

    `create` saves any default the org lacks first. Sources cannot be deleted,
    so that is only ever the first use, or the first after a pack added its
    own, and `ignore_conflicts` lets two first requests race safely. With
    `create=False` nothing is written and missing defaults come back unsaved,
    for a caller that only reads keys and labels.
    """
    sources = list(LeadSource.objects.filter(org=org))
    present = {source.key for source in sources}
    missing = [
        LeadSource(org=org, key=key, label=label, order=order)
        for order, (key, label) in enumerate(DEFAULT_SOURCES)
        if key not in present
    ]
    if not missing:
        return sources
    if not create:
        return sorted(sources + missing, key=lambda s: (s.order, s.label))
    LeadSource.objects.bulk_create(missing, ignore_conflicts=True)
    return list(LeadSource.objects.filter(org=org))


def source_keys(org, active_only=True) -> set[str]:
    return {
        s.key for s in org_sources(org, create=False) if s.is_active or not active_only
    }


def source_labels(org) -> dict[str, str]:
    return {s.key: s.label for s in org_sources(org, create=False)}
