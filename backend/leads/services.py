"""
Lead conversion service functions
"""

from django.contrib.contenttypes.models import ContentType

from accounts.models import Account
from common.models import Attachments, Comment
from contacts.models import Contact
from opportunity.models import Opportunity


def convert_lead_to_account(lead_obj, request, create_opportunity=True):
    """
    Convert a Lead to Account, Contact, and optionally Opportunity.

    This function:
    1. Creates an Account from lead data
    2. Creates a Contact from lead data (if lead has email)
    3. Optionally creates an Opportunity (if create_opportunity=True and lead has opportunity_amount)
    4. Copies tags, assigned_to, teams
    5. Migrates Comments and Attachments
    6. Auto-links existing Lead.contacts to the new Account
    7. Sets lead status to "converted"

    Args:
        lead_obj: The Lead instance to convert
        request: The HTTP request (for user/org context)
        create_opportunity: Whether to create an Opportunity (default: True)

    Returns:
        tuple: (account, contact, opportunity) - the created entities (Contact/Opportunity may be None)
    """
    # Create Account
    account = Account.objects.create(
        created_by=request.profile.user,
        name=(
            lead_obj.company_name
            if lead_obj.company_name
            else f"{lead_obj.first_name} {lead_obj.last_name}"
        ),
        email=lead_obj.email,
        phone=lead_obj.phone,
        description=lead_obj.description,
        website=lead_obj.website,
        org=request.profile.org,
        is_active=True,
        # Use correct address fields
        address_line=lead_obj.address_line,
        city=lead_obj.city,
        state=lead_obj.state,
        postcode=lead_obj.postcode,
        country=lead_obj.country,
    )

    # Copy tags
    for tag in lead_obj.tags.all():
        account.tags.add(tag)

    # Copy assigned users
    for profile in lead_obj.assigned_to.all():
        account.assigned_to.add(profile)

    # Copy teams
    for team in lead_obj.teams.all():
        account.teams.add(team)

    # Move comments from Lead to Account
    lead_ct = ContentType.objects.get_for_model(lead_obj.__class__)
    account_ct = ContentType.objects.get_for_model(Account)
    Comment.objects.filter(
        content_type=lead_ct,
        object_id=lead_obj.id,
        org=request.profile.org,
    ).update(content_type=account_ct, object_id=account.id)

    # Move attachments from Lead to Account
    Attachments.objects.filter(
        content_type=lead_ct,
        object_id=lead_obj.id,
        org=request.profile.org,
    ).update(content_type=account_ct, object_id=account.id)

    # Create Contact from Lead data (if lead has email)
    contact = None
    if lead_obj.email:
        contact = Contact.objects.create(
            first_name=lead_obj.first_name or "",
            last_name=lead_obj.last_name or "",
            email=lead_obj.email,
            phone=lead_obj.phone,
            organization=lead_obj.company_name or "",
            title=lead_obj.job_title,
            description=lead_obj.description,
            address_line=lead_obj.address_line,
            city=lead_obj.city,
            state=lead_obj.state,
            postcode=lead_obj.postcode,
            country=lead_obj.country,
            created_by=request.profile.user,
            org=request.profile.org,
            account=account,  # Set the primary account relationship
        )
        contact.assigned_to.set(lead_obj.assigned_to.all())

        # Also link contact to account via M2M (for backwards compatibility)
        account.contacts.add(contact)

    # Auto-link any existing contacts from Lead to the new Account
    for existing_contact in lead_obj.contacts.all():
        account.contacts.add(existing_contact)

    # Create Opportunity if requested and lead has opportunity data
    opportunity = None
    if create_opportunity and (
        lead_obj.opportunity_amount or lead_obj.first_name or lead_obj.company_name
    ):
        # Construct opportunity name from available lead data
        opp_name_parts = []
        if lead_obj.company_name:
            opp_name_parts.append(lead_obj.company_name)
        if lead_obj.first_name or lead_obj.last_name:
            name = " ".join(filter(None, [lead_obj.first_name, lead_obj.last_name]))
            opp_name_parts.append(name)
        opp_name = (
            " - ".join(opp_name_parts)
            if opp_name_parts
            else f"Opportunity {lead_obj.id}"
        )

        opportunity = Opportunity.objects.create(
            name=opp_name,
            account=account,
            amount=lead_obj.opportunity_amount,
            probability=lead_obj.probability or 0,
            closed_on=lead_obj.close_date,
            lead_source=lead_obj.source,
            description=lead_obj.description,
            stage="QUALIFICATION",  # Initial stage after lead conversion
            created_by=request.profile.user,
            org=request.profile.org,
        )
        # Copy assigned users to opportunity
        opportunity.assigned_to.set(lead_obj.assigned_to.all())
        opportunity.teams.set(lead_obj.teams.all())
        opportunity.tags.set(lead_obj.tags.all())
        # Link contact to opportunity
        if contact:
            opportunity.contacts.add(contact)

    # Update lead status to converted
    lead_obj.status = "converted"
    lead_obj.save()

    return account, contact, opportunity
