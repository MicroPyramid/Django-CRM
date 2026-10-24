"""Who may see and change an interaction.

An interaction is seen by whoever may open its home record, by that module's
own rule, and only while the home's module is on. Its other links only decide
which timelines also list it, so a second link never shows a record to
someone who cannot open it.
"""

from django.db.models import Q

from accounts.access import visible_accounts_qs
from cases.access import visible_cases_qs
from common.modules import available_modules
from common.permissions import is_org_admin
from common.scopes import check_request
from contacts.access import visible_contacts_qs
from interactions.models import Interaction
from leads.access import visible_leads_qs
from opportunity.access import visible_deals_qs

# home -> (the module it needs, None for core; the module's read rule; the API
# resource whose token scope its own routes, comments included, need)
HOME_RULES = {
    "lead": ("leads", visible_leads_qs, "leads"),
    "contact": (None, visible_contacts_qs, "contacts"),
    "account": (None, visible_accounts_qs, "accounts"),
    "opportunity": ("deals", visible_deals_qs, "opportunities"),
    "case": ("tickets", visible_cases_qs, "cases"),
}

# What a person logs. Anything else was written by intake or a connector.
PERSON_ORIGINS = ("manual", "phone_tap")


def home_module(home):
    return HOME_RULES[home][0]


def visible_records(profile, home):
    """The records of kind `home` that `profile` may open."""
    return HOME_RULES[home][1](profile)


def scope_denial(scopes, method, home):
    """Why a token holding `scopes` may not make a `method` request on an
    interaction homed on a `home` record, or None. The home's own scope is
    needed besides `interactions:*`, as it is for that record's comments.
    `scopes` is None for a signed-in session, which no scope limits."""
    if scopes is None:
        return None
    return check_request(scopes, method, f"/api/{HOME_RULES[home][2]}/")


def visible_interactions_qs(profile):
    available = available_modules(profile.org)
    homes = Q()
    for home, (module, visible, _) in HOME_RULES.items():
        if module is None or module in available:
            homes |= Q(home=home, **{f"{home}__in": visible(profile).values("pk")})
    return Interaction.objects.filter(org=profile.org).filter(homes)


def is_read_only(interaction):
    """Enquiries and what intake or a connector wrote belong to the system."""
    return interaction.kind == "enquiry" or interaction.origin not in PERSON_ORIGINS


def may_change_interaction(profile, interaction):
    """Whoever logged it, or an org admin; nobody for a system row. The caller
    has already found it through `visible_interactions_qs`."""
    if is_read_only(interaction):
        return False
    return is_org_admin(profile) or interaction.logged_by_id == profile.id
