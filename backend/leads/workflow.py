"""
Lead workflow rules.

This module used to be reference-only. It declared `TERMINAL_STATUSES` and
nothing imported it, so the rule existed as a comment while the API happily
allowed the transitions it described. It is now imported by
`leads.serializer.LeadCreateSerializer`, which is the only place that can
enforce it: the frontend is not a trust boundary, and `PUT /api/leads/<pk>/`
is reachable from curl, the mobile client and a stale build.

Two different ideas were previously conflated under one name, so they are now
separate:

`IRREVERSIBLE_STATUSES`: statuses a lead can never leave, and can never be
    re-entered. "converted" is the only one. `leads.services.convert_lead_to_account`
    creates an Account, a Contact and an Opportunity, migrates comments and
    attachments, and then sets the status; none of that is undone by editing
    the status back. And `LeadDetailView.put` calls the conversion whenever the
    incoming status is "converted", with no check that it has already happened,
    so re-sending it produces a *second* Opportunity against the same Account.
    Both directions have to be refused.

`CLOSING_STATUSES`: the statuses that take a lead out of the working list.
    Deliberately NOT irreversible: reopening a closed lead is ordinary work,
    and "recycled" exists precisely so a lead can come back. These are listed
    for the list/kanban split, not for validation.

`EMAIL_REQUIRED_STATUSES`: statuses that cannot be set without an email
    address, because conversion has to create a Contact somebody can reach.
    Also enforced in `Lead.clean()`.
"""

# Cannot be entered twice, and cannot be left.
IRREVERSIBLE_STATUSES = {"converted"}

# Out of the working list, but reversible.
CLOSING_STATUSES = {"closed"}

# Status that requires email
EMAIL_REQUIRED_STATUSES = {"converted"}
