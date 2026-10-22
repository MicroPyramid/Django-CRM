"""Pausing automation rules whose owner can no longer answer for them.

A rule acts with its owner's admin reach, so when the owner stops being an org
admin, is deactivated, leaves the org or is deleted, their active rules are
turned off with a short code in `paused_reason` and the other admins are told
why. Switching a rule on again through the API makes that admin its owner.

The signal sources, reasons and the `_problem` test are those of
`webhooks.ownership`; see there for why each receiver works under the
profile's own org.
"""

from django.db.models.signals import post_save, pre_delete

from automation.models import AutomationRule
from common import notifications
from common.models import Org, Profile, User
from common.permissions import is_org_admin
from webhooks.ownership import (
    DEACTIVATED,
    DELETED_USER,
    LEFT,
    NOT_ADMIN,
    NOT_MEMBER,
    _as_org,
    _deleting,
    _problem,
)

PAUSED_VERB = "automation.paused"
SETTINGS_PATH = "/settings/automation"
CODES = {
    NOT_ADMIN: "not_admin",
    DEACTIVATED: "deactivated",
    LEFT: "left",
    NOT_MEMBER: "not_member",
    DELETED_USER: "deleted_user",
}
SENTENCES = {
    "not_admin": "Paused because the admin who switched it on is no longer an admin.",
    "deactivated": "Paused because the admin who switched it on was deactivated.",
    "left": "Paused because the admin who switched it on left the organization.",
    "not_member": (
        "Paused because the person who switched it on is not a member of this organization."
    ),
    "deleted_user": "Paused because the user who switched it on was deleted.",
}


def owner_problem(rule):
    """The `SENTENCES` code for why the rule's owner cannot run it, or None
    when nothing is wrong or the owner is gone without a trace."""
    owner = rule.owner
    if owner is None:
        return None
    member = owner if owner.org_id == rule.org_id else None
    return CODES.get(_problem(owner.user, member))


def pause(rules, reason) -> int:
    """Turn each still-active rule off with `reason` (one of the webhook constants
    imported above) and tell the org's other admins. Returns how many were paused.

    The conditional update means two paths pausing one rule count it once.
    """
    paused = []
    for rule in rules:
        changed = AutomationRule.objects.filter(
            org_id=rule.org_id, pk=rule.pk, owner_id=rule.owner_id, is_active=True
        ).update(is_active=False, paused_reason=CODES[reason])
        if changed:
            paused.append(rule)
    if paused:
        _tell_admins(paused, CODES[reason])
    return len(paused)


def _tell_admins(rules, code):
    org_id = rules[0].org_id
    owner_ids = {r.owner_id for r in rules}
    names = [r.name for r in rules]
    admins = Profile.objects.filter(
        org_id=org_id, is_active=True, user__is_active=True
    ).select_related("user", "org")
    for admin in admins:
        if admin.pk in owner_ids or not is_org_admin(admin):
            continue
        notifications.create(
            admin,
            PAUSED_VERB,
            entity_name=names[0][:255],
            link=SETTINGS_PATH,
            data={"rules": names, "reason": SENTENCES[code]},
        )


def _pause_owned_by(profile_id, org_id, reason):
    with _as_org(org_id):
        rules = list(
            AutomationRule.objects.filter(
                org_id=org_id, owner_id=profile_id, is_active=True
            )
        )
        pause(rules, reason)


def profile_saved(sender, instance, created, raw=False, **kwargs):
    """A role change or a deactivation, from any view, serializer or script."""
    if raw or created:
        return
    reason = _problem(instance.user, instance)
    if reason:
        _pause_owned_by(instance.pk, instance.org_id, reason)


def profile_deleting(sender, instance, **kwargs):
    """Before the delete: SET_NULL would empty `owner` and hide the rules.

    Deleting the org deletes its rules too, so there is nothing to pause.
    """
    if _deleting(kwargs.get("origin"), Org):
        return
    user_deleted = _deleting(kwargs.get("origin"), User)
    _pause_owned_by(
        instance.pk, instance.org_id, DELETED_USER if user_deleted else LEFT
    )


def user_saved(sender, instance, created, raw=False, update_fields=None, **kwargs):
    """A user deactivated, or stripped of superuser, in every org at once."""
    if raw or created:
        return
    if update_fields is not None and not {"is_active", "is_superuser"} & set(
        update_fields
    ):
        return
    for profile in Profile.objects.filter(user=instance):
        profile.user = instance
        reason = _problem(instance, profile)
        if reason:
            _pause_owned_by(profile.pk, profile.org_id, reason)


def connect():
    post_save.connect(
        profile_saved, sender="common.Profile", dispatch_uid="automation_profile_saved"
    )
    pre_delete.connect(
        profile_deleting,
        sender="common.Profile",
        dispatch_uid="automation_profile_deleting",
    )
    post_save.connect(
        user_saved, sender="common.User", dispatch_uid="automation_user_saved"
    )
