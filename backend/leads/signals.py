"""A lead webhook's URL id -> org lookup, for the anonymous public endpoint.

A post to `/api/public/leads/<intake id>/` carries no org, and under RLS an
empty context hides the `lead_intake` row that would name one. The view
resolves the org from the unscoped `PortalAccessToken` row kept here (keyed on
the SHA-256 of the id), sets the context, and only then reads the intake, as
the inbound mailbox webhook does (`cases/signals.py`). Registered once on
create, since the id never changes, and removed on delete.
"""

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from common.models import PortalAccessToken
from common.portal_tokens import register_portal_token
from leads.models import LeadIntake


@receiver(post_save, sender=LeadIntake)
def lead_intake_register_lookup(sender, instance, created, raw=False, **kwargs):
    if created and not raw:
        register_portal_token(
            str(instance.pk),
            instance.org_id,
            PortalAccessToken.LEAD_INTAKE,
            instance.pk,
        )


@receiver(post_delete, sender=LeadIntake)
def lead_intake_remove_lookup(sender, instance, **kwargs):
    PortalAccessToken.objects.filter(
        resource_type=PortalAccessToken.LEAD_INTAKE, resource_id=instance.pk
    ).delete()
