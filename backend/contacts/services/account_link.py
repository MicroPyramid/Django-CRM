"""Keeping a contact's primary account and its account membership in step."""


def link_primary_account(contact):
    """Make `contact.account` show up on that account's people list.

    A Contact is joined to an Account two ways: the `account` FK, documented on
    the model as "Primary account this contact belongs to", and membership of
    `Account.contacts`. Nothing kept them in step, and the whole seeded org
    demonstrated the result: not one contact had the FK set, while twelve of
    fifteen were in the M2M. So the account field on a contact form wrote to a
    column the account page does not read, and the person never appeared where
    they work.

    Setting the primary account now also records the membership. The reverse is
    deliberately not true: clearing the FK leaves the membership alone, because
    membership can be granted from the account side and losing "primary" is not
    a statement that the person left the company.

    This lives here rather than in `contacts.views` (where it started) so the
    CSV importer can call it without a service module importing a views module.
    The importer set the FK and skipped this, so every imported contact was
    invisible on the account it was imported against.
    """
    if contact.account_id:
        contact.account.contacts.add(contact)
